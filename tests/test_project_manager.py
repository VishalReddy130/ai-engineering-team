import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from agents.project_manager import ProjectManagerAgent


VALID_PLAN = {
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


class FakeModels:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(text=outcome)


class ProjectManagerAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.plan_path = Path(self.temp_dir.name) / "nested" / "plan.json"
        self.sleep_calls = []
        self.config_calls = []

    def tearDown(self):
        self.temp_dir.cleanup()

    def build_agent(self, outcomes):
        models = FakeModels(outcomes)
        client = SimpleNamespace(models=models)

        def config_factory(**kwargs):
            self.config_calls.append(kwargs)
            return kwargs

        agent = ProjectManagerAgent(
            client=client,
            model="test-model",
            plan_path=self.plan_path,
            sleep_fn=self.sleep_calls.append,
            config_factory=config_factory,
        )
        return agent, models

    def test_generates_and_saves_valid_plan(self):
        agent, models = self.build_agent([json.dumps(VALID_PLAN)])

        result = agent.create_plan("Build an inventory API")

        self.assertEqual(result, VALID_PLAN)
        self.assertEqual(json.loads(self.plan_path.read_text()), VALID_PLAN)
        self.assertEqual(len(models.calls), 1)
        self.assertEqual(models.calls[0]["model"], "test-model")
        self.assertEqual(len(self.config_calls), 1)
        self.assertFalse(self.plan_path.with_name("plan.json.tmp").exists())

    def test_rejects_blank_request_without_calling_model(self):
        agent, models = self.build_agent([json.dumps(VALID_PLAN)])

        self.assertIsNone(agent.create_plan("   "))
        self.assertEqual(models.calls, [])
        self.assertFalse(self.plan_path.exists())

    def test_rejects_invalid_model_output_without_saving(self):
        invalid_plan = {"project": " ", "tasks": []}
        agent, models = self.build_agent([json.dumps(invalid_plan)])

        self.assertIsNone(agent.create_plan("Build something"))
        self.assertEqual(len(models.calls), 1)
        self.assertFalse(self.plan_path.exists())

    def test_retries_temporary_api_error(self):
        agent, models = self.build_agent(
            [RuntimeError("503 service unavailable"), json.dumps(VALID_PLAN)]
        )

        result = agent.create_plan("Build an inventory API")

        self.assertEqual(result, VALID_PLAN)
        self.assertEqual(len(models.calls), 2)
        self.assertEqual(self.sleep_calls, [5])

    def test_does_not_retry_non_temporary_error(self):
        agent, models = self.build_agent([RuntimeError("invalid API key")])

        self.assertIsNone(agent.create_plan("Build an inventory API"))
        self.assertEqual(len(models.calls), 1)
        self.assertEqual(self.sleep_calls, [])


if __name__ == "__main__":
    unittest.main()
