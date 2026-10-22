import json
import pytest
from docx import Document
from tests.conftest import configured
from app.agents.planner import Planner
from app.agents.executor import TaskExecutor
from app.core.config import Settings
from app.services.agent_service import AgentService
from app.tools.document_tools import DocumentTools
from app.tools.registry import ToolRegistry

APPOINTMENT_REQUEST = (
    "Create a project proposal for a small business launching an online appointment booking system. Include the business "
    "objectives, target users, project scope, key features, technology considerations, a four-week implementation timeline, "
    "risks, estimated resource requirements, and measurable success criteria. Clearly label assumptions and do not invent "
    "actual company data."
)
RECOVERY_REQUEST = (
    "Prepare a recovery plan for a customer support chatbot scheduled to launch in two weeks. Testing is incomplete, the "
    "budget is limited, and the team has not agreed on the launch scope. Identify missing information, state reasonable "
    "assumptions, prioritize critical work, propose a revised two-week schedule, include risks and go/no-go criteria, and "
    "do not invent actual company data."
)
REQUIRED_APPOINTMENT_SECTIONS = [
    "Executive summary", "Business objectives", "Target users", "Scope and exclusions", "Key features",
    "Technology considerations", "Four-week implementation timeline", "Risks and mitigations",
    "Estimated roles and effort", "Measurable success criteria", "Assumptions and next steps",
]

def _document_text(path):
    document = Document(path)
    return "\n".join(paragraph.text for paragraph in document.paragraphs)

def test_exact_appointment_request_fallback_is_request_aware_and_four_weeks(configured):
    client, _, store = configured
    response = client.post("/agent", json={"request": APPOINTMENT_REQUEST})
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "succeeded"
    assert result["provider_mode"] == "fallback"
    assert result["planner_status"] == "fallback"
    assert "recovery" not in result["plan"]["title"].lower()
    assert result["plan"]["title"] == "Project Proposal: Online Appointment Booking System"
    assert "appointment booking system" in result["plan"]["objective"].lower()
    assert APPOINTMENT_REQUEST not in result["plan"]["objective"]
    assert not any("two-week" in assumption.lower() or "2-week" in assumption.lower() for assumption in result["assumptions"])

    validate_step = next(step for step in result["steps"] if step["tool"] == "validate_document_content")
    assert validate_step["status"] == "succeeded"
    assert validate_step["output"]["valid"] is True
    path = store.get(result["document_id"])
    assert path
    text = _document_text(path)
    for heading in REQUIRED_APPOINTMENT_SECTIONS:
        assert heading in text
    timeline = text.split("Four-week implementation timeline", 1)[1].split("Risks and mitigations", 1)[0]
    for week in range(1, 5):
        assert f"Week {week}" in timeline
    assert "eight-week" not in text.lower() and "8-week" not in text.lower()
    assert "illustrative estimate" in text.lower()
    assert "proposed target" in text.lower()

class QueueProvider:
    mode = "xai"
    def __init__(self, outputs): self.outputs, self.calls = list(outputs), 0
    async def complete_json(self, system_prompt, user_content):
        self.calls += 1
        return json.dumps(self.outputs.pop(0))

def test_mocked_llm_incomplete_draft_is_repaired_and_document_validated(configured):
    client, fallback_service, store = configured
    tasks = [
        {"id":"requirements", "description":"Extract requirements", "tool":"extract_requirements", "expected_output":"Requirements"},
        {"id":"draft", "description":"Draft requested proposal", "tool":"draft_document_section", "expected_output":"Requested sections"},
        {"id":"validate", "description":"Validate and repair content", "tool":"validate_document_content", "expected_output":"Valid sections"},
        {"id":"generate", "description":"Generate Word document", "tool":"generate_docx", "expected_output":"DOCX"},
    ]
    provider = QueueProvider([
        {"document_type":"Project Proposal", "title":"Project Proposal: Online Appointment Booking System", "objective":"Deliver a useful online booking proposal", "assumptions":[], "tasks":tasks},
        {"sections":{"Executive summary":"Proposal overview", "Timeline":["Eight-week schedule: Weeks 1–8"]}},
    ])
    settings: Settings = fallback_service.settings
    tools = DocumentTools(settings, store, provider)
    service = AgentService(settings, Planner(provider, settings.max_plan_steps), TaskExecutor(ToolRegistry(tools)), store, "xai", tools)
    from app.api.routes import router
    router.agent_service = service
    router.document_store = store

    response = client.post("/agent", json={"request":APPOINTMENT_REQUEST})
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "succeeded"
    assert provider.calls == 2
    validation = next(step for step in result["steps"] if step["tool"] == "validate_document_content")
    assert validation["status"] == "succeeded"
    assert validation["output"]["repair_attempted"] is True
    assert validation["output"]["valid"] is True
    text = _document_text(store.get(result["document_id"]))
    assert "Eight-week" not in text and "Weeks 1–8" not in text
    assert all(section in text for section in REQUIRED_APPOINTMENT_SECTIONS)

def test_mocked_llm_targeted_repair_fills_missing_general_section(configured):
    import asyncio
    from app.schemas.agent import AgentPlan
    _, service, store = configured
    provider = QueueProvider([{"sections":{"Objectives":"Improve support operations by making response handling consistent and measurable across the agreed service workflow."}}])
    tools = DocumentTools(service.settings, store, provider)
    plan = AgentPlan(document_type="Business Document", title="Support Operations", objective="Improve the requested support operations", tasks=[
        {"id":"requirements", "description":"Extract requirements", "tool":"extract_requirements", "expected_output":"Requirements"},
    ])
    content = {"Executive summary":"This brief describes a consistent approach to improving support operations and the work required to put it into practice."}
    result = asyncio.run(tools.validate_document_content("Create a business document about support operations including objectives.", plan, content))
    assert result["repair_attempted"] is True
    assert result["valid"] is True
    assert provider.calls == 1

def test_chatbot_recovery_fallback_preserves_two_week_constraint(configured):
    client, _, store = configured
    response = client.post("/agent", json={"request":RECOVERY_REQUEST})
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "succeeded"
    assert result["plan"]["document_type"] == "Project Recovery Plan"
    assert "recovery" in result["plan"]["title"].lower()
    assert any("two weeks" in item.lower() or "2-week" in item.lower() for item in result["assumptions"])
    text = _document_text(store.get(result["document_id"]))
    assert "Revised two-week schedule" in text
    assert "Week 1" in text and "Week 2" in text
    assert "four-week" not in text.lower() and "eight-week" not in text.lower()
    validation = next(step for step in result["steps"] if step["tool"] == "validate_document_content")
    assert validation["status"] == "succeeded" and validation["output"]["valid"] is True

def test_validator_rejects_missing_sections_and_wrong_duration():
    from app.documents.content_validator import validate_content
    report = validate_content(
        APPOINTMENT_REQUEST,
        "Project Proposal: Online Appointment Booking System",
        "Project Proposal",
        "Propose a four-week implementation for online appointment booking.",
        ["The requested four-week period is the full planning horizon."],
        {"Executive summary": "This proposal describes an eight-week booking system implementation plan."},
    )
    assert report["valid"] is False
    assert any("Missing required sections" in issue for issue in report["issues"])
    assert any("contradict" in issue.lower() for issue in report["issues"])

def test_appointment_output_validator_rejects_unrelated_recovery_title():
    from app.agents.fallback_drafter import draft_fallback
    from app.agents.planner import deterministic_plan
    from app.documents.content_validator import validate_content
    plan = deterministic_plan(APPOINTMENT_REQUEST)
    content = draft_fallback(APPOINTMENT_REQUEST, plan)
    report = validate_content(
        APPOINTMENT_REQUEST,
        "PROJECT RECOVERY PLAN",
        "Project Recovery Plan",
        plan.objective,
        plan.assumptions,
        content,
    )
    assert report["valid"] is False
    assert any("Title is not relevant" in issue for issue in report["issues"])
    assert any("Document type contradicts" in issue for issue in report["issues"])

def test_docx_generation_refuses_unrelated_appointment_title(configured):
    import asyncio
    from app.agents.fallback_drafter import draft_fallback
    from app.agents.planner import deterministic_plan
    _, service, store = configured
    plan = deterministic_plan(APPOINTMENT_REQUEST)
    content = draft_fallback(APPOINTMENT_REQUEST, plan)
    plan.title = "PROJECT RECOVERY PLAN"
    plan.document_type = "Project Recovery Plan"
    with pytest.raises(ValueError, match="failed validation"):
        asyncio.run(service.tools.generate_docx(APPOINTMENT_REQUEST, plan, content, []))
    assert list(store.output_dir.glob("*.docx")) == []

def test_each_request_gets_fresh_plan_and_drafting_context(configured):
    client, _, _ = configured
    recovery = client.post("/agent", json={"request":RECOVERY_REQUEST}).json()
    proposal = client.post("/agent", json={"request":APPOINTMENT_REQUEST}).json()
    assert "recovery" in recovery["plan"]["title"].lower()
    assert "appointment booking" in proposal["plan"]["title"].lower()
    assert all("two-week" not in assumption.lower() for assumption in proposal["assumptions"])
    proposal_validation = next(step for step in proposal["steps"] if step["tool"] == "validate_document_content")
    assert proposal_validation["status"] == "succeeded"
    assert proposal_validation["output"]["valid"] is True

