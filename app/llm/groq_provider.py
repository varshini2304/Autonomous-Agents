import httpx
from app.core.config import Settings
from app.llm.errors import safe_network_error, safe_provider_error

class GroqProvider:
    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings
        self.transport = transport
        self.active = False
    @property
    def mode(self) -> str:
        return "groq"
    async def complete_json(self, system_prompt: str, user_content: str) -> str:
        headers = {"Authorization": f"Bearer {self.settings.groq_api_key}"}
        payload = {"model": self.settings.groq_model, "temperature": 0.2, "response_format": {"type": "json_object"}, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}]}
        try:
            async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds, transport=self.transport) as client:
                response = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                if response.is_error:
                    self.active = False
                    raise safe_provider_error(response, self.settings.groq_api_key or "", "Groq")
                content = response.json()["choices"][0]["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    raise ValueError("Groq API returned an empty message")
                self.active = True
                return content
        except httpx.RequestError as exc:
            self.active = False
            raise safe_network_error(exc, self.settings.groq_api_key or "", "Groq") from exc
        except Exception:
            self.active = False
            raise
