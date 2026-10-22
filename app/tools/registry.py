from typing import Any
from app.schemas.agent import AgentPlan
from app.tools.document_tools import DocumentTools

class ToolRegistry:
    def __init__(self, tools: DocumentTools): self.tools = tools
    async def execute(self, name: str, *, request: str, plan: AgentPlan, results: list[dict[str, Any]], content: dict[str, Any] | None = None) -> Any:
        handlers = {
            "extract_requirements": lambda: self.tools.extract_requirements(request, results),
            "draft_document_section": lambda: self.tools.draft_document_section(request, plan, results),
            "validate_document_content": lambda: self.tools.validate_document_content(request, plan, content or {}),
            "generate_docx": lambda: self.tools.generate_docx(request, plan, content or {}, [f"{r['step_id']}: {r['status']}" for r in results]),
        }
        if name not in handlers: raise ValueError(f"Tool is not permitted: {name}")
        return await handlers[name]()

def allowed_tool_names() -> set[str]:
    return {"extract_requirements", "draft_document_section", "validate_document_content", "generate_docx"}
