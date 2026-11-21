"""Human approval gate for generated project plans."""

import json
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.plan_validation import validate_plan


def review_plan(
    plan_path: Path | str | None = None,
    input_fn: Callable[[str], str] = input,
) -> bool:
    """Display a validated plan and ask a human to approve it.

    Invalid, missing, or unreadable plans are rejected without prompting.
    """
    path = Path(plan_path) if plan_path is not None else ROOT / "project_plan.json"

    try:
        with path.open("r", encoding="utf-8") as file:
            plan = json.load(file)
    except FileNotFoundError:
        print(f"No project plan found at: {path}")
        return False
    except (OSError, json.JSONDecodeError) as error:
        print(f"Could not read project plan: {error}")
        return False

    errors = validate_plan(plan)
    if errors:
        print("\nProject plan is invalid:")
        for error in errors:
            print(f"- {error}")
        return False

    print("\n=== PROJECT APPROVAL ===")
    print(f"Project: {plan['project']}")

    for task in plan["tasks"]:
        print(f"\nTask {task['id']}: {task['task']}")
        print(f"Agent: {task['agent']}")
        print(f"Expected: {task['expected_outcome']}")

    choice = input_fn("\nDo you approve this plan? (yes/no): ").strip().lower()
    if choice == "yes":
        print("\nPlan approved!")
        return True

    print("\nPlan rejected. Execution cancelled.")
    return False


if __name__ == "__main__":
    review_plan()
