from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.schemas.agent import AgentRequest, AgentResponse
from app.services.agent_service import AgentService
from app.storage.document_store import DocumentStore

router = APIRouter()
def get_agent_service() -> AgentService: return router.agent_service
def get_document_store() -> DocumentStore: return router.document_store

@router.post("/agent", response_model=AgentResponse)
async def create_document(payload: AgentRequest, service: AgentService = Depends(get_agent_service)):
    try: result = await service.run(payload)
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
    if result.status == "failed": raise HTTPException(status_code=500, detail=result.model_dump())
    return result

@router.get("/documents/{document_id}")
async def download_document(document_id: str, store: DocumentStore = Depends(get_document_store)):
    path = store.get(document_id)
    if path is None: raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=f"{document_id}.docx")
