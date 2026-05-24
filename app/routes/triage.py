from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.triage import TriageRequest, TriageResponse
from app.services import triage_service

router = APIRouter(prefix="/triage", tags=["triage"])


@router.post("", response_model=TriageResponse)
async def triage_endpoint(
    request: TriageRequest,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    return await triage_service.classify(db, request, actor)
