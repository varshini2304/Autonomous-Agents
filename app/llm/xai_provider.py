import httpx
from app.core.config import Settings
from app.llm.errors import safe_network_error, safe_provider_error

class XAIProvider:
    """xAI Responses API adapter; no SDK dependency required."""
    base_url = "https://api.x.ai/v1"

    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings
        self.transport = transport
        self.active = False

    @property
    def mode(self) -> str:
        return "xai"

    async def complete_json(self, system_prompt: str, user_content: str) -> str:
        headers = {"Authorization": f"Bearer {self.settings.xai_api_key}"}
        payload = {
            "model": self.settings.xai_model,
            "store": False,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "input_text", "text": user_content}]},
            ],
            "text": {"format": {"type": "json_schema", "name": "agent_output", "schema": {"type": "object", "additionalProperties": True}, "strict": True}},
        }
        try:
            async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds, transport=self.transport) as client:
                response = await client.post(f"{self.base_url}/responses", headers=headers, json=payload)
            if response.is_error:
                self.active = False
                raise safe_provider_error(response, self.settings.xai_api_key or "")
            data = response.json()
            output = "".join(
                part.get("text", "")
                for item in data.get("output", [])
                for part in item.get("content", [])
                if part.get("type") == "output_text"
            )
            if not output:
                self.active = False
                raise ValueError("xAI returned no text output")
            self.active = True
            return output
        except httpx.RequestError as exc:
            self.active = False
            raise safe_network_error(exc, self.settings.xai_api_key or "", "xAI") from exc

    async def check_connectivity(self) -> dict[str, str]:
        """Verify key access and model availability via the non-generation models endpoint."""
        headers = {"Authorization": f"Bearer {self.settings.xai_api_key}"}
        try:
            async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds, transport=self.transport) as client:
                response = await client.get(f"{self.base_url}/models", headers=headers)
            if response.is_error:
                self.active = False
                raise safe_provider_error(response, self.settings.xai_api_key or "")
            data = response.json()
            models = data.get("data", []) if isinstance(data, dict) else []
            if not any(item.get("id") == self.settings.xai_model for item in models if isinstance(item, dict)):
                self.active = False
                raise RuntimeError(f"xAI API connected, but model '{self.settings.xai_model}' is unavailable to this key")
            self.active = True
            return {"provider": "xai", "model": self.settings.xai_model, "status": "connected"}
        except httpx.RequestError as exc:
            self.active = False
            raise safe_network_error(exc, self.settings.xai_api_key or "", "xAI") from exc

