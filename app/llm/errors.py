import re
from typing import Any
import httpx

class ProviderError(RuntimeError):
    """Safe, user-reportable provider error with credentials removed."""

def redact_sensitive_text(text: str, api_key: str = "") -> str:
    if api_key:
        text = text.replace(api_key, "[REDACTED]")
    text = re.sub(r"(?i)bearer\s+\S+", "Bearer [REDACTED]", text)
    return re.sub(r"\b(?:xai-[A-Za-z0-9_-]{8,}|gsk_[A-Za-z0-9_-]{8,}|sk-[A-Za-z0-9_-]{8,})\b", "[REDACTED]", text)

def safe_provider_error(response: httpx.Response, api_key: str, provider: str = "xAI") -> ProviderError:
    try:
        data: Any = response.json()
        if isinstance(data, dict):
            detail = data.get("error", data.get("message", data.get("detail", "")))
            if isinstance(detail, dict):
                detail = detail.get("message") or detail.get("code") or "provider returned an error"
            if not isinstance(detail, str):
                detail = str(detail)
        else:
            detail = "provider returned an error"
    except ValueError:
        detail = "provider returned a non-JSON error response"
    detail = detail[:500]
    detail = redact_sensitive_text(detail, api_key)
    return ProviderError(f"{provider} API HTTP {response.status_code}: {detail}")

def safe_network_error(exc: Exception, api_key: str = "", provider: str = "xAI") -> ProviderError:
    message = str(exc).replace("\n", " ")[:300]
    message = redact_sensitive_text(message, api_key)
    return ProviderError(f"{provider} API network error ({type(exc).__name__}): {message or 'request failed'}")
