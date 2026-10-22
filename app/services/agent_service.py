from app.core.config import Settings
from app.schemas.agent import AgentPlan, AgentRequest, AgentResponse
from app.agents.planner import Planner
from app.agents.executor import TaskExecutor
from app.storage.document_store import DocumentStore
from app.tools.document_tools import DocumentTools
from app.tools.registry import ToolRegistry

class AgentService:
    def __init__(self, settings: Settings, planner: Planner, executor: TaskExecutor, store: DocumentStore, provider_mode: str, tools=None):
        self.settings, self.planner, self.executor, self.store, self.provider_mode, self.tools = settings, planner, executor, store, provider_mode, tools
    async def run(self, incoming: AgentRequest) -> AgentResponse:
        if len(incoming.request) > self.settings.max_request_length: raise ValueError(f"Request exceeds {self.settings.max_request_length} characters")
        base_tools = self.tools or self.executor.registry.tools
        request_tools = DocumentTools(base_tools.settings, base_tools.store, base_tools.provider)
        request_planner = Planner(self.planner.provider, self.planner.max_steps)
        request_executor = TaskExecutor(ToolRegistry(request_tools))
        plan = await request_planner.create_plan(incoming.request)
        steps, document = await request_executor.execute(incoming.request, plan)
        fallback_reason = request_planner.fallback_reason or request_tools.fallback_reason
        mode = "fallback" if self.provider_mode in {"xai", "groq"} and fallback_reason else self.provider_mode
        succeeded = sum(step.status == "succeeded" for step in steps); failed = sum(step.status == "failed" for step in steps)
        doc_id = document.get("document_id")
        skipped = sum(step.status == "skipped" for step in steps)
        status = "succeeded" if doc_id and failed == 0 and skipped == 0 else ("partial" if succeeded or doc_id else "failed")
        verb = "Prepared" if status == "succeeded" else ("Partially prepared" if status == "partial" else "Could not prepare")
        return AgentResponse(summary=f"{verb} {plan.document_type.lower()} '{plan.title}' with {succeeded} successful and {failed} failed execution steps.", plan=plan, assumptions=plan.assumptions, steps=steps, document_id=doc_id, download_url=f"/documents/{doc_id}" if doc_id else None, status=status, provider_mode=mode, planner_status=request_planner.status, fallback_reason=fallback_reason)
