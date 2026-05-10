from pydantic import BaseModel
from typing import Optional, Any


# ── Request Models ──────────────────────────────────────────────

class RunRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None


class ConfirmRequest(BaseModel):
    session_id: str
    confirmed: bool


# ── Response Models ─────────────────────────────────────────────

class HealthResponse(BaseModel):
    service: str
    version: str
    status: str


class PendingAction(BaseModel):
    employee_id: str
    employee_name: str
    leave_type: str
    from_date: str
    to_date: str
    total_days: int
    current_balance: float
    balance_after: float
    colleagues_on_leave: int
    coverage_risk: bool
    confirmation_prompt: str


class RunResponse(BaseModel):
    status: str  # "completed" or "awaiting_confirmation"
    session_id: str
    message: str
    pending_action: Optional[PendingAction] = None
    agents_involved: Optional[list[str]] = None


class ConfirmResponse(BaseModel):
    status: str
    message: str
    leave_application_id: Optional[str] = None


class HistoryItem(BaseModel):
    session_id: str
    prompt: str
    status: str
    result: Optional[Any] = None


class HistoryResponse(BaseModel):
    sessions: list[HistoryItem]