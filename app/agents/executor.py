import logging
from app.schemas.agent import AgentPlan, StepResult
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)
class TaskExecutor:
    def __init__(self, registry: ToolRegistry): self.registry = registry
    async def execute(self, request: str, plan: AgentPlan) -> tuple[list[StepResult], dict]:
        results: list[StepResult] = []; content: dict = {}
        for index, step in enumerate(plan.tasks):
            try:
                output = await self.registry.execute(step.tool, request=request, plan=plan, results=[r.model_dump() for r in results], content=content)
                if step.tool == "draft_document_section": content = output
                if step.tool == "validate_document_content":
                    if isinstance(output.get("content"), dict):
                        content = output["content"]
                    if not output.get("valid"):
                        raise ValueError("; ".join(output.get("issues", [])))
                results.append(StepResult(step_id=step.id, description=step.description, tool=step.tool, status="succeeded", output=output))
            except Exception as exc:
                logger.exception("Execution step %s failed", step.id)
                results.append(StepResult(step_id=step.id, description=step.description, tool=step.tool, status="failed", error=f"{type(exc).__name__}: {exc}"))
                for remaining in plan.tasks[index + 1:]: results.append(StepResult(step_id=remaining.id, description=remaining.description, tool=remaining.tool, status="skipped", error="A prior execution step failed"))
                break
        document = next((r.output for r in results if r.tool == "generate_docx" and r.status == "succeeded"), {})
        return results, document
