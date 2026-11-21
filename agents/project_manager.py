"""LLM-backed project planning agent with deterministic validation."""

import json
import os
import time
from pathlib import Path
from typing import Any, Callable

from tools.plan_validation import validate_plan

ROOT = Path(__file__).resolve().parent.parent

PLAN_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "project": {"type": "STRING"},
        "tasks": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "INTEGER"},
                    "agent": {"type": "STRING"},
                    "task": {"type": "STRING"},
                    "expected_outcome": {"type": "STRING"},
                },
                "required": ["id", "agent", "task", "expected_outcome"],
            },
        },
    },
    "required": ["project", "tasks"],
}


class ProjectManagerAgent:
    """Create validated project plans without initializing an API at import time."""

    def __init__(
        self,
        client: Any = None,
        model: str | None = None,
        plan_path: Path | str | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        config_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.client = client
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        self.plan_path = Path(plan_path) if plan_path else ROOT / "project_plan.json"
        self.sleep_fn = sleep_fn
        self.config_factory = config_factory

    def _get_client(self) -> Any:
        if self.client is not None:
            return self.client

        from dotenv import load_dotenv
        from google import genai

        load_dotenv(ROOT / ".env")
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is missing from the repository .env file.")

        self.client = genai.Client(api_key=api_key)
        return self.client

    def _get_config(self) -> Any:
        if self.config_factory is not None:
            return self.config_factory(
                response_mime_type="application/json",
                response_schema=PLAN_SCHEMA,
            )

        from google.genai import types

        return types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PLAN_SCHEMA,
        )

    def _save_plan(self, plan: dict[str, Any]) -> None:
        self.plan_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.plan_path.with_name(self.plan_path.name + ".tmp")
        try:
            temporary_path.write_text(
                json.dumps(plan, indent=4) + "\n",
                encoding="utf-8",
            )
            temporary_path.replace(self.plan_path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    def create_plan(self, request: str) -> dict[str, Any] | None:
        """Generate, validate, and atomically save a project plan."""
        if not isinstance(request, str) or not request.strip():
            print("Please provide a non-empty project request.")
            return None

        prompt = f"""
You are the Project Manager of a software engineering team.

Create a development plan for:
{request.strip()}

Assign tasks to:
- Coding Agent
- Testing Agent
- Security Agent
- Review Agent

Each task must contain:
- id (positive integer, unique within the plan)
- agent (non-empty string)
- task (non-empty string)
- expected_outcome (non-empty string)

Put tasks in logical order.
Do not claim anything has already been implemented.
Return a non-empty project name and at least one task.
"""

        for attempt in range(1, 4):
            try:
                print(f"\nGenerating plan ({attempt}/3)...")
                response = self._get_client().models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=self._get_config(),
                )

                if not getattr(response, "text", None):
                    raise ValueError("Gemini returned an empty response.")

                plan = json.loads(response.text)
                errors = validate_plan(plan)
                if errors:
                    details = "; ".join(errors)
                    raise ValueError(f"Gemini returned an invalid plan: {details}")

                self._save_plan(plan)
                print(f"\nPlan saved: {self.plan_path}")
                return plan

            except Exception as error:
                message = str(error)
                temporary_error = any(
                    code in message for code in ("429", "503", "504")
                )
                if temporary_error and attempt < 3:
                    wait_seconds = attempt * 5
                    print(f"Temporary API error. Retrying in {wait_seconds}s...")
                    self.sleep_fn(wait_seconds)
                    continue

                print(f"\nError generating plan: {error}")
                return None

        return None


if __name__ == "__main__":
    import sys

    from tools.approval import review_plan

    manager = ProjectManagerAgent()
    request = input("\nWhat should the AI team build? ").strip()

    if not request:
        sys.exit("Please enter a project request.")

    plan = manager.create_plan(request)
    if plan:
        print("\n=== GENERATED PROJECT PLAN ===")
        print(json.dumps(plan, indent=4))
        print("\nMoving to approval...")
        if review_plan(manager.plan_path):
            print("\nPlan approved. Ready for execution!")
        else:
            print("\nExecution cancelled.")
