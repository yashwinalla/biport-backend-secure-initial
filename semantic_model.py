from fastapi import APIRouter, Depends
from uuid import UUID

from app.models.users import User
from app.core.dependencies import get_current_user
from app.services.migrate.PowerBI.semantic_model.semantic_processor import SemanticProcessor

semantic_model_router = APIRouter()

@semantic_model_router.post("/semantic_model/{report_id}")
async def generate_semantic_model(report_id: UUID, user: User = Depends(get_current_user)):
    """
    Triggers semantic model generation or returns pre-signed URL if already processed.
    """
    response = await SemanticProcessor.semantic_processor(report_id, user)
    return {"message": response.data.get("message", "Success"),"data": response.data}