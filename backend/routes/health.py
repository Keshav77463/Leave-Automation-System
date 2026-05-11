from fastapi import APIRouter
from backend.schemas.models import HealthResponse, HistoryResponse, HistoryItem
from backend.config import settings
from backend.agents.team import session_store

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        service=settings.app_name,
        version=settings.app_version,
        status="ok",
    )


@router.get("/history", response_model=HistoryResponse)
def get_history():
    sessions = []
    for sid, data in session_store.items():
        sessions.append(HistoryItem(
            session_id=sid,
            prompt=data.get("prompt", ""),
            status="awaiting_confirmation",
            result=data.get("pending_action"),
        ))
    return HistoryResponse(sessions=sessions)