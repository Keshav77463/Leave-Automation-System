import json
from agno.tools import tool
from backend.services.erpnext_client import erpnext_client
from backend.config import settings


@tool
def get_employee(employee_id: str) -> str:
    """Fetch employee details from ERPNext by employee ID."""
    try:
        response = erpnext_client.get(f"api/resource/Employee/{employee_id}")
        emp = response.get("data", {})
        return json.dumps({
            "employee_id": emp.get("name"),
            "employee_name": emp.get("employee_name"),
            "department": emp.get("department"),
            "company": emp.get("company"),
            "status": emp.get("status"),
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_leave_balance(employee_id: str, leave_type: str) -> str:
    """Get available leave balance for an employee and leave type."""
    try:
        # Get allocation
        response = erpnext_client.get(
            "api/resource/Leave Allocation",
            params={
                "filters": json.dumps([
                    ["employee", "=", employee_id],
                    ["leave_type", "=", leave_type],
                    ["docstatus", "=", 1],
                ]),
                "fields": json.dumps([
                    "employee", "leave_type", "total_leaves_allocated",#you can get this much holidays from to date
                    "from_date", "to_date"
                ]),
            }
        )
        allocations = response.get("data", [])
        if not allocations:
            return json.dumps({"error": f"No allocation found for {leave_type}"})

        alloc = allocations[0]
        total = alloc.get("total_leaves_allocated", 0)
        from_date = alloc.get("from_date")
        to_date = alloc.get("to_date")

        # Get actual leaves taken from all non-cancelled applications
        taken_response = erpnext_client.get(
            "api/resource/Leave Application",
            params={
                "filters": json.dumps([
                    ["employee", "=", employee_id],
                    ["leave_type", "=", leave_type],
                    ["from_date", ">=", from_date],
                    ["to_date", "<=", to_date],
                    ["docstatus", "!=", 2],
                ]),
                "fields": json.dumps(["total_leave_days"]),
            }
        )
        taken_apps = taken_response.get("data", [])
        taken = sum(app.get("total_leave_days", 0) for app in taken_apps)
        available = total - taken

        return json.dumps({
            "employee_id": employee_id,
            "leave_type": leave_type,
            "total_allocated": total,
            "leaves_taken": taken,
            "available_balance": available,
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_team_leaves(department: str, from_date: str, to_date: str) -> str:
    """Get approved leave applications for a department in a date range."""
    try:
        response = erpnext_client.get(
            "api/resource/Leave Application",
            params={
                "filters": json.dumps([
                    ["department", "=", department],
                    ["from_date", "<=", to_date],
                    ["to_date", ">=", from_date],
                    ["docstatus", "=", 1],
                ]),
                "fields": json.dumps([
                    "employee", "employee_name", "leave_type",
                    "from_date", "to_date", "total_leave_days", "status"
                ]),
            }
        )
        leaves = response.get("data", [])
        return json.dumps({
            "department": department,
            "date_range": f"{from_date} to {to_date}",
            "colleagues_on_leave": len(leaves),
            "details": leaves,
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_leave_types() -> str:
    """Fetch all available leave types from ERPNext."""
    try:
        response = erpnext_client.get(
            "api/resource/Leave Type",
            params={"fields": json.dumps(["name", "max_days_allowed"])}
        )
        leave_types = response.get("data", [])
        return json.dumps({"leave_types": [lt["name"] for lt in leave_types]})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def create_leave_application(
    employee_id: str,
    leave_type: str,
    from_date: str,
    to_date: str,
    total_days: int,
    reason: str = "Leave request via AI assistant"
) -> str:
    """Create a Leave Application in ERPNext."""
    try:
        data = {
            "employee": employee_id,
            "leave_type": leave_type,
            "from_date": from_date,
            "to_date": to_date,
            "total_leave_days": total_days,
            "description": reason,
            "status": "Open",
            "docstatus": 0,
        }
        response = erpnext_client.post("api/resource/Leave Application", data)
        doc = response.get("data", {})
        return json.dumps({
            "success": True,
            "leave_application_id": doc.get("name"),
            "status": doc.get("status"),
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})