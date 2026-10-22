from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.storage.document_store import DocumentStore
from app.tools.document_tools import DocumentTools
from app.tools.registry import ToolRegistry
from app.agents.planner import Planner
from app.agents.executor import TaskExecutor
from app.services.agent_service import AgentService
from app.llm.groq_provider import GroqProvider
from app.llm.xai_provider import XAIProvider

configure_logging()
settings = get_settings()
store = DocumentStore(settings.output_dir)
provider = XAIProvider(settings) if settings.xai_api_key else (GroqProvider(settings) if settings.groq_api_key else None)
doc_tools = DocumentTools(settings, store, provider)
planner = Planner(provider, settings.max_plan_steps)
service = AgentService(settings, planner, TaskExecutor(ToolRegistry(doc_tools)), store, provider.mode if provider else "fallback", doc_tools)
router.agent_service = service
router.document_store = store
app = FastAPI(title="Autonomous AI Document Agent", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
app.include_router(router)
app.state.model_provider = provider

@app.get("/health")
async def health():
    active_provider = app.state.model_provider
    is_live = bool(active_provider and getattr(active_provider, "active", False))
    return {
        "status": "ok",
        "provider_mode": "live_llm" if is_live else "fallback",
        "provider": active_provider.mode if active_provider else None,
        "configured": bool(active_provider),
    }
