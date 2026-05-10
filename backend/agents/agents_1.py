from agno.agent import Agent
from agno.models.groq import Groq
from backend.config import settings
from backend.tools.erpnext_tools import get_employee, get_leave_balance, get_leave_types

employee_agent = Agent(
    name="Employee & Balance Agent",
    role="Check employee details and leave balance",
    model=Groq(id="llama-3.1-8b-instant", api_key=settings.groq_api_key),
    tools=[get_employee, get_leave_balance, get_leave_types],
    instructions=[
        "You are an HR assistant that checks employee details and leave balances.",
        "When given an employee ID and leave request, you must:",
        "1. Fetch the employee record using get_employee",
        "2. Fetch available leave types using get_leave_types",
        "3. Check the leave balance using get_leave_balance",
        "4. Determine if the employee has sufficient balance for the requested days",
        "5. Return a clear summary with: employee name, leave type, available balance, requested days, and whether balance is sufficient",
        "Always return structured information that can be used by the decision agent.",
    ],
)