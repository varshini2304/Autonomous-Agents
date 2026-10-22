import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.storage.document_store import DocumentStore
from app.tools.document_tools import DocumentTools
from app.tools.registry import ToolRegistry
from app.agents.planner import Planner
from app.agents.executor import TaskExecutor
from app.services.agent_service import AgentService
from app.main import app

@pytest.fixture
def configured(tmp_path):
    settings = Settings(output_dir=tmp_path, max_plan_steps=8)
    store = DocumentStore(tmp_path)
    tools = DocumentTools(settings, store, None)
    planner = Planner(None, settings.max_plan_steps)
    service = AgentService(settings, planner, TaskExecutor(ToolRegistry(tools)), store, "fallback", tools)
    app.state.agent_service = service
    app.state.document_store = store
    # Route dependencies read this module-level router; replace references for isolated tests.
    from app.api.routes import router
    router.agent_service = service
    router.document_store = store
    return TestClient(app), service, store
