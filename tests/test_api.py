from tests.conftest import configured

def test_health(configured):
    client, _, _ = configured
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["provider_mode"] in {"live_llm", "fallback"}
    assert isinstance(body["configured"], bool)

def test_cors_allows_vite_origin_but_not_arbitrary_origins(configured):
    client, _, _ = configured
    allowed = client.options("/agent", headers={
        "Origin":"http://localhost:5173",
        "Access-Control-Request-Method":"POST",
        "Access-Control-Request-Headers":"content-type",
    })
    assert allowed.status_code == 200
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"

    denied = client.options("/agent", headers={
        "Origin":"https://untrusted.invalid",
        "Access-Control-Request-Method":"POST",
        "Access-Control-Request-Headers":"content-type",
    })
    assert "access-control-allow-origin" not in denied.headers

def test_empty_request_rejected(configured):
    client, _, _ = configured
    assert client.post("/agent", json={"request":"  "}).status_code == 422
    assert client.post("/agent", json={"request":""}).status_code == 422

def test_standard_request_generates_and_downloads_docx(configured):
    client, _, _ = configured
    result = client.post("/agent", json={"request":"Create a project proposal for a small business launching an online appointment booking system. Include objectives, scope, features, timeline, risks, and success metrics."})
    assert result.status_code == 200
    body = result.json()
    assert body["status"] == "succeeded" and body["document_id"]
    assert body["plan"]["tasks"] and body["steps"]
    download = client.get(body["download_url"])
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    assert download.content[:2] == b"PK"

def test_complex_request_has_assumptions_and_multistep_plan(configured):
    client, _, _ = configured
    request = "Prepare a project recovery plan for a delayed customer support chatbot launch. The original deadline is in two weeks, the budget is limited, testing is incomplete, and the team has not agreed on the launch scope. Identify missing information, state reasonable assumptions, prioritize critical tasks, propose a revised two-week schedule, and include risks, decision points, and go/no-go criteria. Do not invent actual company data."
    response = client.post("/agent", json={"request":request})
    assert response.status_code == 200
    body = response.json()
    assert len(body["plan"]["tasks"]) >= 4 and len(body["assumptions"]) >= 2
    assert body["status"] == "succeeded"
    assert any("Go/no-go" in section for section in body["steps"][1]["output"])

def test_unknown_tool_rejected_by_registry(configured):
    import pytest
    from app.tools.registry import ToolRegistry
    from app.schemas.agent import AgentPlan
    _, service, _ = configured
    import asyncio
    plan = service.planner.create_plan
    bad = AgentPlan(document_type="test", title="test", objective="A valid objective", tasks=[{"id":"bad","description":"Run forbidden tool","tool":"shell","expected_output":"none"}])
    with pytest.raises(ValueError, match="Unknown tool"):
        service.planner._validate(bad)

def test_malformed_llm_uses_visible_fallback(configured):
    import asyncio
    from app.agents.planner import Planner
    class Broken:
        @property
        def mode(self): return "groq"
        async def complete_json(self, system_prompt, user_content): raise RuntimeError("offline")
    planner = Planner(Broken(), 8)
    result = asyncio.run(planner.create_plan("Create a project proposal"))
    assert result.tasks and planner.fallback_reason and "offline" in planner.fallback_reason
    assert planner.status == "fallback"
