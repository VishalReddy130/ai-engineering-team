# AI Engineering Team

A Python prototype for coordinating AI-assisted software development through a project manager and a human approval gate.

## Current workflow

1. The Project Manager Agent receives a plain-language build request.
2. It asks the configured Gemini model to produce a structured JSON plan.
3. The plan is checked locally for required fields, valid task IDs, and non-empty task details.
4. The plan is saved to `project_plan.json`.
5. A human reviews the plan and explicitly approves or rejects it.

A generated plan is not an implementation. Coding, testing, security, and review agents are planned roles; they should only be described as implemented when executable agent workflows exist in the repository.

## Requirements

- Python 3.11 or later
- A Gemini API key

Install dependencies:

```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate

python -m pip install -r requirements.txt
```

Create a `.env` file in the repository root:

```dotenv
GEMINI_API_KEY=your_api_key_here
```

Do not commit `.env` or paste API keys into issues, logs, or prompts.

## Run

From the repository root:

```bash
python agents/project_manager.py
```

Enter a project request when prompted. Inspect the generated `project_plan.json` and approve it only if the task breakdown and expected outcomes are appropriate.

## Validate a plan manually

```bash
python -m tools.approval
```

The approval gate rejects missing, malformed, or structurally invalid plans before asking for human approval.

## Tests

The validation and approval modules use Python's standard library and can be tested without an API key:

```bash
python -m unittest discover -s tests -v
```

GitHub Actions runs Python compilation and the unit test suite on pushes and pull requests targeting `main`.

## Repository layout

```text
agents/
  project_manager.py       # LLM-backed project plan generation
tools/
  approval.py              # Human approval gate
  plan_validation.py       # Deterministic plan validation
tests/
  test_approval.py
  test_plan_validation.py
.github/workflows/
  ci.yml
```

## Current limitations

- The Project Manager currently generates plans; it does not execute coding tasks.
- Agent roles in a plan are assignments, not proof that those agents are implemented.
- API calls require a valid Gemini API key and an available model.
- Human approval is mandatory before any future execution stage should begin.
