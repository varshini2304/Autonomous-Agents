import asyncio
import json
import pytest
from app.agents.planner import Planner
from app.agents.request_analysis import analyze_request
from app.schemas.agent import AgentPlan

REQUEST = "Create a plan for a small service launch."
TOOLS = ["extract_requirements", "draft_document_section", "validate_document_content", "generate_docx"]

def valid_payload():
    analysis = analyze_request(REQUEST)
    return {
        "document_type": analysis.document_type,
        "title": analysis.title,
        "objective": analysis.objective,
        "assumptions": [],
        "tasks": [
            {"id": "requirements", "description": "Extract launch requirements", "tool": TOOLS[0], "expected_output": "Requirements and constraints"},
            {"id": "draft", "description": "Draft requested launch sections", "tool": TOOLS[1], "expected_output": "Substantive requested sections"},
            {"id": "validate", "description": "Validate sections and constraints", "tool": TOOLS[2], "expected_output": "Validation report"},
            {"id": "generate", "description": "Generate and verify DOCX", "tool": TOOLS[3], "expected_output": "Stored DOCX document"},
        ],
    }

class QueueProvider:
    mode = "groq"
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []
    async def complete_json(self, system_prompt, user_content):
        self.calls.append((system_prompt, user_content))
        output = self.outputs.pop(0)
        if isinstance(output, Exception):
            raise output
        return output if isinstance(output, str) else json.dumps(output)

def test_valid_llm_plan_and_markdown_fence_are_accepted():
    raw = "```json\n" + json.dumps(valid_payload()) + "\n```"
    provider = QueueProvider([raw])
    planner = Planner(provider, 8)
    plan = asyncio.run(planner.create_plan(REQUEST))
    assert [task.tool for task in plan.tasks] == TOOLS
    assert planner.status == "succeeded"
    assert planner.fallback_reason is None
    assert provider.calls[0][0].find('"required"') >= 0

@pytest.mark.parametrize(("invalid", "expected_feedback"), [
    ("malformed-json", "Malformed JSON"),
    ("missing-fields", "objective"),
    ("invalid-step-id", "tasks.1.id"),
    ("invalid-tool", "unknown tool 'shell'"),
    ("missing-required-tool", "missing required workflow tools"),
    ("workflow-order", "incorrect workflow order"),
])
def test_one_targeted_correction_uses_specific_validation_feedback(invalid, expected_feedback):
    bad = valid_payload()
    if invalid == "malformed-json":
        first = '{"document_type":'
    else:
        first = bad
        if invalid == "missing-fields":
            first.pop("objective")
        elif invalid == "invalid-step-id":
            first["tasks"][1]["id"] = "Bad ID"
        elif invalid == "invalid-tool":
            first["tasks"][1]["tool"] = "shell"
        elif invalid == "missing-required-tool":
            first["tasks"] = [task for task in first["tasks"] if task["tool"] != "validate_document_content"]
        elif invalid == "workflow-order":
            first["tasks"][2], first["tasks"][3] = first["tasks"][3], first["tasks"][2]
    provider = QueueProvider([first, valid_payload()])
    planner = Planner(provider, 8)
    plan = asyncio.run(planner.create_plan(REQUEST))
    assert planner.status == "succeeded"
    assert planner.fallback_reason is None
    assert len(plan.tasks) == 4
    feedback_payload = json.loads(provider.calls[1][1])
    assert expected_feedback.lower() in feedback_payload["validation_feedback"].lower()
    assert "valid_workflow_reference" in feedback_payload

def test_invalid_plan_after_correction_reports_error_and_uses_fallback():
    bad = valid_payload()
    bad["tasks"][1]["id"] = "Bad ID"
    provider = QueueProvider([bad, bad])
    planner = Planner(provider, 8)
    plan = asyncio.run(planner.create_plan(REQUEST))
    assert planner.status == "fallback"
    assert len(provider.calls) == 2
    assert planner.fallback_reason and "tasks.1.id" in planner.fallback_reason
    assert "step id 'Bad ID'" in planner.fallback_reason
    assert [task.tool for task in plan.tasks] == TOOLS

def test_provider_failure_uses_fallback_without_blind_retry():
    provider = QueueProvider([RuntimeError("temporary provider failure")])
    planner = Planner(provider, 8)
    plan = asyncio.run(planner.create_plan(REQUEST))
    assert plan.tasks and planner.status == "fallback"
    assert len(provider.calls) == 1
    assert planner.fallback_reason and "temporary provider failure" in planner.fallback_reason

def test_step_limit_enforced():
    planner = Planner(None, 3)
    plan = AgentPlan(document_type="Test plan", title="Test", objective="Create a valid test plan", tasks=[{"id":f"step{i}","description":"A valid test step","tool":"extract_requirements","expected_output":"Requirements"} for i in range(4)])
    with pytest.raises(ValueError, match="maximum"):
        planner._validate(plan)
