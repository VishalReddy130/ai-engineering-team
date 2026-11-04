
import os
import sys
import json
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Locate the main project folder
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.approval import review_plan

load_dotenv(ROOT / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=API_KEY)


class ProjectManagerAgent:

    def create_plan(self, request):

        prompt = f"""
You are the Project Manager of a software engineering team.

Create a development plan for:
{request}

Assign tasks to:
- Coding Agent
- Testing Agent
- Security Agent
- Review Agent

Each task must contain:
- id
- agent
- task
- expected_outcome

Put tasks in logical order.
Do not claim anything has already been implemented.
"""

        for attempt in range(1, 4):
            try:
                print(f"\nGenerating plan ({attempt}/3)...")

                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema={
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
                                            "expected_outcome": {
                                                "type": "STRING"
                                            }
                                        },
                                        "required": [
                                            "id",
                                            "agent",
                                            "task",
                                            "expected_outcome"
                                        ]
                                    }
                                }
                            },
                            "required": ["project", "tasks"]
                        }
                    )
                )

                if not response.text:
                    raise ValueError("Gemini returned an empty response")

                plan = json.loads(response.text)

                if not isinstance(plan.get("tasks"), list):
                    raise ValueError("Invalid plan structure")

                # Save the generated plan
                plan_path = ROOT / "project_plan.json"

                with open(plan_path, "w", encoding="utf-8") as file:
                    json.dump(plan, file, indent=4)

                print(f"\nPlan saved: {plan_path}")
                return plan

            except Exception as error:
                message = str(error)

                temporary_error = (
                    "503" in message or "504" in message
                )

                if temporary_error and attempt < 3:
                    wait = attempt * 5
                    print(f"Temporary error. Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"\nError generating plan: {error}")
                    return None

        return None


if __name__ == "__main__":

    manager = ProjectManagerAgent()

    request = input("\nWhat should the AI team build? ").strip()

    if not request:
        print("Please enter a project request.")
        sys.exit()

    plan = manager.create_plan(request)

    if plan:
        print("\n=== GENERATED PROJECT PLAN ===")
        print(json.dumps(plan, indent=4))

        print("\nMoving to approval...")

        approved = review_plan()

        if approved:
            print("\nPlan approved. Ready for execution!")
        else:
            print("\nExecution cancelled.")
