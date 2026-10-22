import asyncio
import httpx
from app.core.config import Settings
from app.llm.xai_provider import XAIProvider

def test_xai_responses_api_uses_official_endpoint_and_parses_output():
    seen = {}
    def handler(request):
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("authorization")
        seen["json"] = __import__("json").loads(request.content)
        return httpx.Response(200, json={"output":[{"type":"message","content":[{"type":"output_text","text":'{"ok":true}'}]}]})
    provider = XAIProvider(Settings(xai_api_key="xai-secret-test", xai_model="grok-4.7"), httpx.MockTransport(handler))
    result = asyncio.run(provider.complete_json("system","untrusted user request"))
    assert result == '{"ok":true}'
    assert seen["url"] == "https://api.x.ai/v1/responses"
    assert seen["auth"] == "Bearer xai-secret-test"
    assert seen["json"]["model"] == "grok-4.7"
    assert seen["json"]["store"] is False
    assert provider.active

def test_xai_provider_redacts_auth_error_and_deactivates():
    key = "xai-secret-test"
    transport = httpx.MockTransport(lambda request: httpx.Response(401, json={"error":f"Invalid key {key}"}))
    provider = XAIProvider(Settings(xai_api_key=key), transport)
    try:
        asyncio.run(provider.complete_json("system", "user"))
        assert False, "Expected provider error"
    except Exception as exc:
        assert "401" in str(exc)
        assert key not in str(exc)
        assert "[REDACTED]" in str(exc)
    assert not provider.active

def test_safe_connectivity_check_does_not_need_generation():
    seen = {}
    def handler(request):
        seen["path"] = request.url.path
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"data":[{"id":"grok-4.7"}]})
    key = "xai-secret-test"
    provider = XAIProvider(Settings(xai_api_key=key), httpx.MockTransport(handler))
    result = asyncio.run(provider.check_connectivity())
    assert result == {"provider":"xai", "model":"grok-4.7", "status":"connected"}
    assert seen == {"path":"/v1/models", "auth":f"Bearer {key}"}
    assert provider.active

def test_authentication_error_is_reported_and_planner_falls_back():
    from app.agents.planner import Planner
    key = "xai-secret-test"
    transport = httpx.MockTransport(lambda request: httpx.Response(401, json={"error":"Invalid API key"}))
    provider = XAIProvider(Settings(xai_api_key=key), transport)
    planner = Planner(provider, 8)
    plan = asyncio.run(planner.create_plan("Create a proposal"))
    assert plan.tasks
    assert planner.fallback_reason and "HTTP 401" in planner.fallback_reason
    assert key not in planner.fallback_reason
    assert not provider.active
