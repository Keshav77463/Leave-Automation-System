import uuid
import json
from agno.team import Team
from agno.models.groq import Groq
from backend.config import settings
from backend.agents.agents_1 import employee_agent
from backend.agents.agents_2 import coverage_agent
from backend.agents.agents_3 import decision_agent
from backend.schemas.models import PendingAction

# In-memory session store for HITL
session_store: dict = {}


def run_leave_request(prompt: str, session_id: str = None) -> dict:
    """
    Process a leave request prompt.
    Returns either a completed result or awaiting_confirmation with pending action.
    """

    team = Team(
        name="Leave Request Team",
        mode="coordinate",
        model=Groq(id="llama-3.1-8b-instant", api_key=settings.groq_api_key),
        members=[employee_agent, coverage_agent, decision_agent],
        instructions=[
            "You are coordinating a leave request processing team.",
            "When a leave request comes in:",
            "1. Send the employee ID, leave type and requested days to the Employee & Balance Agent",
            "2. Send the department and date range to the Team Coverage Agent",
            "3. Both agents can run independently — they don't depend on each other",
            "4. Send both results to the Decision & Action Agent for final decision",
            f"The default employee ID is: {settings.employee_id}",
            f"The default department is: {settings.department}",
            "Extract leave type, from_date, to_date, and total_days from the user prompt.",
            "Dates should be in YYYY-MM-DD format.",
        ],
        debug_mode=True,
    )

    # Run the team
    response = team.run(prompt)
    result_text = response.content if hasattr(response, "content") else str(response)

    # Generate session ID
    sid = session_id or str(uuid.uuid4())

    # Try to extract structured data from agent responses
    # Check if balance is insufficient
    if "insufficient" in result_text.lower() or "not enough" in result_text.lower():
        return {
            "status": "completed",
            "session_id": sid,
            "message": result_text,
            "pending_action": None,
            "agents_involved": ["Employee & Balance Agent", "Team Coverage Agent", "Decision & Action Agent"],
        }

    # Try to parse pending action for HITL
    try:
        pending = _extract_pending_action(result_text, prompt)
        if pending:
            session_store[sid] = {
                "pending_action": pending,
                "prompt": prompt,
            }
            return {
                "status": "awaiting_confirmation",
                "session_id": sid,
                "message": "Leave request validated. Awaiting your confirmation.",
                "pending_action": pending,
                "agents_involved": ["Employee & Balance Agent", "Team Coverage Agent", "Decision & Action Agent"],
            }
    except Exception:
        pass

    return {
        "status": "completed",
        "session_id": sid,
        "message": result_text,
        "pending_action": None,
        "agents_involved": ["Employee & Balance Agent", "Team Coverage Agent", "Decision & Action Agent"],
    }


def confirm_leave_request(session_id: str, confirmed: bool) -> dict:
    session = session_store.get(session_id)
    if not session:
        return {
            "status": "error",
            "message": "Session not found or already completed.",
            "leave_application_id": None,
        }

    pending: PendingAction = session["pending_action"]

    if not confirmed:
        del session_store[session_id]
        return {
            "status": "cancelled",
            "message": "Leave Application not created. No changes made.",
            "leave_application_id": None,
        }

    # Directly create leave application via ERPNext client — no Groq needed
    try:
        from backend.services.erpnext_client import erpnext_client
        data = {
            "employee": pending.employee_id,
            "leave_type": pending.leave_type,
            "from_date": pending.from_date,
            "to_date": pending.to_date,
            "total_leave_days": pending.total_days,
            "description": "Leave request via AI assistant",
            "status": "Open",
            "docstatus": 0,
        }
        response = erpnext_client.post("api/resource/Leave Application", data)
        doc = response.get("data", {})
        leave_app_id = doc.get("name")

        del session_store[session_id]

        return {
            "status": "completed",
            "message": f"Leave application created successfully for {pending.employee_name} from {pending.from_date} to {pending.to_date}. Application ID: {leave_app_id}",
            "leave_application_id": leave_app_id,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create leave application: {str(e)}",
            "leave_application_id": None,
        }


def _extract_pending_action(result_text: str, prompt: str) -> PendingAction:
    import re

    # Only proceed if prompt looks like a leave request with dates
    prompt_lower = prompt.lower()
    has_leave_intent = any(word in prompt_lower for word in ["leave", "casual", "sick", "off"])
    has_date_intent = any(word in prompt_lower for word in ["january","february","march","april","may","june","july","august","september","october","november","december","from","to","date"])

    if not has_leave_intent or not has_date_intent:
        return None

    months = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12"
    }

    from_date = None
    to_date = None
    total_days = 4

    # Pattern 1: "from 24 december to 27 december"
    match = re.search(r"from\s+(\d+)\w*\s+(\w+)\s+to\s+(\d+)\w*\s+(\w+)", prompt_lower)
    if match:
        from_day = match.group(1).zfill(2)
        from_month = months.get(match.group(2), "12")
        to_day = match.group(3).zfill(2)
        to_month = months.get(match.group(4), "12")
        from_date = f"2026-{from_month}-{from_day}"
        to_date = f"2026-{to_month}-{to_day}"

    # Pattern 2: "from december 24 to december 27"
    if not from_date:
        match = re.search(r"from\s+(\w+)\s+(\d+)\w*\s+to\s+(\w+)\s+(\d+)\w*", prompt_lower)
        if match:
            from_month = months.get(match.group(1), "12")
            from_day = match.group(2).zfill(2)
            to_month = months.get(match.group(3), "12")
            to_day = match.group(4).zfill(2)
            from_date = f"2026-{from_month}-{from_day}"
            to_date = f"2026-{to_month}-{to_day}"

    # Pattern 3: "19th to 21st may"
    if not from_date:
        match = re.search(r"(\d+)\w*\s+to\s+(\d+)\w*\s+(\w+)", prompt_lower)
        if match:
            from_day = match.group(1).zfill(2)
            to_day = match.group(2).zfill(2)
            month = months.get(match.group(3), "12")
            from_date = f"2026-{month}-{from_day}"
            to_date = f"2026-{month}-{to_day}"

    # If no dates found, return None — not a valid leave request
    if not from_date:
        return None

    # Extract days from prompt
    days_match = re.search(r"(\d+)\s*day", prompt_lower)
    if days_match:
        total_days = int(days_match.group(1))
    else:
        try:
            from datetime import datetime
            d1 = datetime.strptime(from_date, "%Y-%m-%d")
            d2 = datetime.strptime(to_date, "%Y-%m-%d")
            total_days = (d2 - d1).days + 1
        except Exception:
            total_days = 4

    # Get real balance directly from ERPNext
    current_balance = 15.0
    try:
        from backend.services.erpnext_client import erpnext_client as _client
        alloc_resp = _client.get(
            "api/resource/Leave Allocation",
            params={
                "filters": json.dumps([
                    ["employee", "=", settings.employee_id],
                    ["leave_type", "=", "Casual Leave"],
                    ["docstatus", "=", 1],
                ]),
                "fields": json.dumps(["total_leaves_allocated", "from_date", "to_date"]),
            }
        )
        allocs = alloc_resp.get("data", [])
        if allocs:
            total = allocs[0].get("total_leaves_allocated", 15)
            taken_resp = _client.get(
                "api/resource/Leave Application",
                params={
                    "filters": json.dumps([
                        ["employee", "=", settings.employee_id],
                        ["leave_type", "=", "Casual Leave"],
                        ["docstatus", "!=", 2],
                    ]),
                    "fields": json.dumps(["total_leave_days"]),
                }
            )
            taken = sum(a.get("total_leave_days", 0) for a in taken_resp.get("data", []))
            current_balance = total - taken
    except Exception:
        pass

    # Get colleagues directly from ERPNext
    colleagues = 0
    try:
        from backend.services.erpnext_client import erpnext_client as _client2
        coverage_response = _client2.get(
            "api/resource/Leave Application",
            params={
                "filters": json.dumps([
                    ["department", "=", settings.department],
                    ["from_date", "<=", to_date],
                    ["to_date", ">=", from_date],
                    ["docstatus", "=", 1],
                ]),
                "fields": json.dumps(["employee", "employee_name", "from_date", "to_date"]),
            }
        )
        details = coverage_response.get("data", [])
        colleagues = len([d for d in details if d.get("employee") != settings.employee_id])
    except Exception:
        pass

    coverage_risk = colleagues > 0

    return PendingAction(
        employee_id=settings.employee_id,
        employee_name="Test Employee",
        leave_type="Casual Leave",
        from_date=from_date,
        to_date=to_date,
        total_days=total_days,
        current_balance=current_balance,
        balance_after=current_balance - total_days,
        colleagues_on_leave=colleagues,
        coverage_risk=coverage_risk,
        confirmation_prompt=f"Create Leave Application for Test Employee from {from_date} to {to_date} ({total_days} days)?",
    )