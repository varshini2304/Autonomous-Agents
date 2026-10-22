import asyncio
import httpx
from app.core.config import Settings
from app.llm.groq_provider import GroqProvider

def test_groq_provider_uses_official_endpoint_and_model():
    seen = {}
    def handler(request):
        seen["url"] = str(request.url)
        seen["authorization"] = request.headers.get("authorization")
        seen["payload"] = __import__("json").loads(request.content)
        return httpx.Response(200, json={"choices":[{"message":{"content":'{"ok":true}'}}]})
    key = "gsk-secret-test"
    provider = GroqProvider(Settings(groq_api_key=key, groq_model="llama-3.3-70b-versatile"), httpx.MockTransport(handler))
    assert asyncio.run(provider.complete_json("system", "request")) == '{"ok":true}'
    assert seen["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert seen["authorization"] == f"Bearer {key}"
    assert seen["payload"]["model"] == "llama-3.3-70b-versatile"
    assert provider.active

def test_groq_auth_error_is_reported_without_secret():
    key = "gsk-secret-test"
    transport = httpx.MockTransport(lambda request: httpx.Response(401, json={"error":{"message":f"Invalid key {key}"}}))
    provider = GroqProvider(Settings(groq_api_key=key), transport)
    try:
        asyncio.run(provider.complete_json("system", "request"))
        assert False, "Expected safe provider error"
    except Exception as exc:
        assert "Groq API HTTP 401" in str(exc)
        assert key not in str(exc)
        assert "[REDACTED]" in str(exc)
    assert not provider.active

def test_groq_network_error_is_reported_without_secret():
    key = "gsk-secret-test"
    def handler(request):
        raise httpx.ConnectError(f"failed while using Bearer {key}", request=request)
    provider = GroqProvider(Settings(groq_api_key=key), httpx.MockTransport(handler))
    try:
        asyncio.run(provider.complete_json("system", "request"))
        assert False, "Expected safe network error"
    except Exception as exc:
        assert "Groq API network error" in str(exc)
        assert key not in str(exc)
    assert not provider.active

def test_groq_authentication_failure_preserves_planner_fallback():
    from app.agents.planner import Planner
    key = "gsk-secret-test"
    transport = httpx.MockTransport(lambda request: httpx.Response(401, json={"error":{"message":"Invalid API Key"}}))
    provider = GroqProvider(Settings(groq_api_key=key), transport)
    planner = Planner(provider, 8)
    plan = asyncio.run(planner.create_plan("Create a proposal for an online booking system"))
    assert plan.tasks
    assert planner.fallback_reason and "Groq API HTTP 401" in planner.fallback_reason
    assert key not in planner.fallback_reason
    assert not provider.active
