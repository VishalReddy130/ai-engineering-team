class ProjectManagerAgent:
    def __init__(self):
        self.name = "Project Manager"

    def create_plan(self, request):
        return {
            "request": request,
            "tasks": [
                {
                    "agent": "Coding Agent",
                    "task": f"Implement: {request}"
                },
                {
                    "agent": "Testing Agent",
                    "task": f"Test: {request}"
                },
                {
                    "agent": "Security Agent",
                    "task": f"Audit: {request}"
                },
                {
                    "agent": "Review Agent",
                    "task": f"Review changes for: {request}"
                }
            ]
        }


if __name__ == "__main__":
    manager = ProjectManagerAgent()

    plan = manager.create_plan(
        "Build a multi agentic AI system"
    )

    print(f"Agent: {manager.name}")
    print(f"Request: {plan['request']}")

    for number, task in enumerate(plan["tasks"], start=1):
        print(f"{number}. {task['agent']}: {task['task']}")