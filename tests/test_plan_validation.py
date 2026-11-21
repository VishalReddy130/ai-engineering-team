import unittest

from tools.plan_validation import validate_plan


class ValidatePlanTests(unittest.TestCase):
    def setUp(self):
        self.valid_plan = {
            "project": "Inventory API",
            "tasks": [
                {
                    "id": 1,
                    "agent": "Developer",
                    "task": "Create stock endpoint",
                    "expected_outcome": "Endpoint returns stock levels",
                }
            ],
        }

    def test_accepts_valid_plan(self):
        self.assertEqual(validate_plan(self.valid_plan), [])

    def test_rejects_non_object_plan(self):
        self.assertEqual(
            validate_plan(["not", "an", "object"]),
            ["Plan must be a JSON object."],
        )

    def test_rejects_missing_project_name(self):
        plan = {**self.valid_plan, "project": "   "}
        self.assertIn(
            "'project' must be a non-empty string.",
            validate_plan(plan),
        )

    def test_rejects_empty_task_list(self):
        plan = {**self.valid_plan, "tasks": []}
        self.assertIn("'tasks' must be a non-empty list.", validate_plan(plan))

    def test_rejects_duplicate_task_ids(self):
        duplicate = dict(self.valid_plan["tasks"][0])
        plan = {**self.valid_plan, "tasks": [self.valid_plan["tasks"][0], duplicate]}
        self.assertIn("Task 2: duplicate task id 1.", validate_plan(plan))

    def test_rejects_boolean_task_id(self):
        task = {**self.valid_plan["tasks"][0], "id": True}
        plan = {**self.valid_plan, "tasks": [task]}
        self.assertIn(
            "Task 1: 'id' must be a positive integer.",
            validate_plan(plan),
        )

    def test_rejects_blank_task_fields(self):
        task = {**self.valid_plan["tasks"][0], "agent": " "}
        plan = {**self.valid_plan, "tasks": [task]}
        self.assertIn(
            "Task 1: 'agent' must be a non-empty string.",
            validate_plan(plan),
        )

    def test_rejects_non_object_task(self):
        plan = {**self.valid_plan, "tasks": ["not a task"]}
        self.assertIn("Task 1 must be a JSON object.", validate_plan(plan))


if __name__ == "__main__":
    unittest.main()
