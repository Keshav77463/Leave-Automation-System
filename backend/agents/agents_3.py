from agno.agent import Agent
from agno.models.groq import Groq
from backend.config import settings
from backend.tools.erpnext_tools import create_leave_application

decision_agent = Agent(
    name="Decision & Action Agent",
    role="Make final decision and create leave application after confirmation",
    model=Groq(id="llama-3.1-8b-instant", api_key=settings.groq_api_key),
    tools=[create_leave_application],
    instructions=[
        "You are an HR decision agent that processes leave requests.",
        "You will receive results from the Employee Balance Agent and Team Coverage Agent.",
        "Your job is to:",
        "1. If balance is insufficient: return a clear message with current balance and maximum available days. Do NOT create any application.",
        "2. If balance is sufficient: prepare a confirmation summary with all details for human review.",
        "3. When explicitly told to CREATE the leave application (after human confirmation): call create_leave_application with the correct parameters.",
        "4. When explicitly told the request was CANCELLED: return a cancellation message without creating anything.",
        "Always be clear and concise in your responses.",
        "Date format for ERPNext must be YYYY-MM-DD.",
    ],
)