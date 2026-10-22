import asyncio
import logging
from app.core.config import get_settings
from app.llm.xai_provider import XAIProvider

logger = logging.getLogger(__name__)

async def check_xai_connectivity() -> int:
    settings = get_settings()
    if not settings.xai_api_key:
        print("xAI connectivity unavailable: XAI_API_KEY is not configured.")
        return 2
    try:
        result = await XAIProvider(settings).check_connectivity()
        print(f"{result['provider']} connectivity OK; configured model {result['model']} is available.")
        return 0
    except Exception as exc:
        logger.warning("xAI connectivity check failed: %s", exc)
        print(f"xAI connectivity failed: {exc}")
        return 1

if __name__ == "__main__":
    raise SystemExit(asyncio.run(check_xai_connectivity()))
