from fastapi import APIRouter
from backend.schemas.models import RunRequest, RunResponse, ConfirmRequest, ConfirmResponse
from backend.agents.team import run_leave_request, confirm_leave_request

router = APIRouter()


@router.post("/run", response_model=RunResponse)
def run_agent(request: RunRequest):
    result = run_leave_request(
        prompt=request.prompt,
        session_id=request.session_id,
    )
    return RunResponse(
        status=result["status"],
        session_id=result["session_id"],
        message=result["message"],
        pending_action=result.get("pending_action"),
        agents_involved=result.get("agents_involved"),
    )


@router.post("/confirm", response_model=ConfirmResponse)
def confirm_action(request: ConfirmRequest):
    result = confirm_leave_request(
        session_id=request.session_id,
        confirmed=request.confirmed,
    )
    return ConfirmResponse(
        status=result["status"],
        message=result["message"],
        leave_application_id=result.get("leave_application_id"),
    )