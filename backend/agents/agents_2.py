from agno.agent import Agent
from agno.models.groq import Groq
from backend.config import settings
from backend.tools.erpnext_tools import get_team_leaves

coverage_agent = Agent(
    name="Team Coverage Agent",
    role="Check team availability and coverage conflicts",
    model=Groq(id="llama-3.1-8b-instant", api_key=settings.groq_api_key),
    tools=[get_team_leaves],
    instructions=[
        "You are an HR assistant that checks team coverage during leave periods.",
        "When given a department and date range, you must:",
        "1. Fetch all approved leaves for the department in that date range using get_team_leaves",
        "2. Count how many colleagues are already on leave",
        "3. Determine if there is a coverage risk (more than 1 colleague on leave = risk)",
        "4. Return a clear summary with: number of colleagues on leave, their names, dates, and whether there is a coverage risk",
        "Always return structured information that can be used by the decision agent.",
    ],
)