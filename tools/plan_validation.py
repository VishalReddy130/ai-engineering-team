"""Validation helpers for AI-generated project plans.

These checks are deliberately deterministic and do not require an LLM.
"""

from typing import Any


def validate_plan(plan: Any) -> list[str]:
    """Return human-readable validation errors for a project plan."""
    errors: list[str] = []

    if not isinstance(plan, dict):
        return ["Plan must be a JSON object."]

    project = plan.get("project")
    if not isinstance(project, str) or not project.strip():
        errors.append("'project' must be a non-empty string.")

    tasks = plan.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append("'tasks' must be a non-empty list.")
        return errors

    seen_ids: set[int] = set()
    required_fields = ("id", "agent", "task", "expected_outcome")

    for index, task in enumerate(tasks, start=1):
        prefix = f"Task {index}"

        if not isinstance(task, dict):
            errors.append(f"{prefix} must be a JSON object.")
            continue

        for field in required_fields:
            value = task.get(field)
            if field == "id":
                if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                    errors.append(f"{prefix}: 'id' must be a positive integer.")
                elif value in seen_ids:
                    errors.append(f"{prefix}: duplicate task id {value}.")
                else:
                    seen_ids.add(value)
            elif not isinstance(value, str) or not value.strip():
                errors.append(f"{prefix}: '{field}' must be a non-empty string.")

    return errors
