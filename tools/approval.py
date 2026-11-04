
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def review_plan():

    plan_path = ROOT / "project_plan.json"

    if not plan_path.exists():
        print("No project plan found.")
        return False

    with open(plan_path, "r", encoding="utf-8") as file:
        plan = json.load(file)

    print("\n=== PROJECT APPROVAL ===")
    print(f"Project: {plan['project']}")

    for task in plan["tasks"]:
        print(f"\nTask {task['id']}: {task['task']}")
        print(f"Agent: {task['agent']}")
        print(f"Expected: {task['expected_outcome']}")

    choice = input(
        "\nDo you approve this plan? (yes/no): "
    ).strip().lower()

    if choice == "yes":
        print("\nPlan approved!")
        return True

    print("\nPlan rejected. Execution cancelled.")
    return False


if __name__ == "__main__":
    review_plan()
