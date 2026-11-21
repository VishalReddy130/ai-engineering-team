import json
import tempfile
import unittest
from pathlib import Path

from tools.approval import review_plan


class ReviewPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.plan_path = Path(self.temp_dir.name) / "project_plan.json"
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

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_plan(self, content=None):
        self.plan_path.write_text(
            json.dumps(self.valid_plan if content is None else content),
            encoding="utf-8",
        )

    def test_approves_only_explicit_yes(self):
        self.write_plan()
        self.assertTrue(review_plan(self.plan_path, lambda _: " YES "))

    def test_rejects_no(self):
        self.write_plan()
        self.assertFalse(review_plan(self.plan_path, lambda _: "no"))

    def test_missing_file_is_rejected_without_prompt(self):
        self.assertFalse(
            review_plan(self.plan_path, lambda _: self.fail("Should not prompt"))
        )

    def test_malformed_json_is_rejected_without_prompt(self):
        self.plan_path.write_text("{invalid", encoding="utf-8")
        self.assertFalse(
            review_plan(self.plan_path, lambda _: self.fail("Should not prompt"))
        )

    def test_invalid_plan_is_rejected_without_prompt(self):
        self.write_plan({"project": "", "tasks": []})
        self.assertFalse(
            review_plan(self.plan_path, lambda _: self.fail("Should not prompt"))
        )


if __name__ == "__main__":
    unittest.main()
