# 🏖️ Leave Request Automation System
### Fyntwin Intern Assignment — Module: HR Leave Management

> An intelligent ERP automation assistant that understands natural language leave requests and processes them against a live ERPNext instance using a multi-agent AI team.

---

## 📌 What This System Does

This system automates the HR leave approval workflow using a team of specialized AI agents. An employee (or HR executive) types a natural language request like:

> *"I want casual leave from December 24 to December 27, that's 4 days."*

The system then:
1. **Identifies the employee** record in ERPNext using a configurable employee ID
2. **Checks the leave balance** — fetches the employee's leave allocation and calculates how many days have already been consumed
3. **Checks team coverage** — queries approved leaves for the same department in the requested date range
4. **Pauses for HITL confirmation** before creating anything — showing a full summary including balance impact and coverage risk
5. **Creates the Leave Application** in ERPNext on confirmation, or aborts cleanly on cancellation

**ERPNext Module Covered:** HR → Leave Management (`Leave Type`, `Leave Allocation`, `Leave Application`)

---

## 🤖 Agno Team Mode Justification

This system uses **`coordinate` mode** for the Agno Team.

The coordinate mode was chosen because the leave validation process has two completely independent sub-tasks — checking the employee's leave balance and checking team coverage — that neither depend on each other's results. In coordinate mode, the coordinator agent can dispatch both the Employee & Balance Agent and the Team Coverage Agent concurrently (or in parallel), then collect both results and forward them to the Decision Agent. This mirrors the real-world HR process where a manager checks both conditions simultaneously rather than sequentially. A `route` mode would force serial execution (one agent at a time), which is wasteful; `collaborate` mode would have agents talk to each other rather than a clear coordinator, which introduces ambiguity for this structured workflow.

---

## 🔄 Human-in-the-Loop (HITL) Flow

### What Triggers the Pause
After the agent team validates the leave request (balance check + coverage check), **before any write operation is performed on ERPNext**, the system pauses and stores the pending action in an in-memory session store keyed by a unique `session_id`.

### What the User Sees
The Streamlit UI detects the `awaiting_confirmation` status in the API response and renders a confirmation card showing:

| Field | Details |
|---|---|
| Employee name & ID | Identifies who the leave is for |
| Leave type | e.g., Casual Leave |
| From / To dates | Requested date range |
| Total days | Count of leave days |
| Current balance | Days available before this request |
| Balance after approval | Days remaining if approved |
| Colleagues on leave | Number of teammates already absent |
| Coverage risk flag | ⚠️ YES / ✅ NO |

A prominent confirmation prompt is shown: *"Create Leave Application for [employee name] from [date] to [date] ([n] days)?"*

### How Confirmation Resumes the Agent
- **Confirm →** `POST /api/v1/confirm { "session_id": "...", "confirmed": true }` — the backend retrieves the pending action from the session store and calls the ERPNext API to create the Leave Application, then returns the Application ID.
- **Cancel →** `POST /api/v1/confirm { "session_id": "...", "confirmed": false }` — the session is deleted and a clean *"No changes made"* message is returned.

```
User Prompt → POST /api/v1/run
     ↓
Agent Team processes (balance check ∥ coverage check)
     ↓
status: "awaiting_confirmation" + pending_action + session_id
     ↓
UI shows confirmation card
     ↓
User clicks Confirm → POST /api/v1/confirm {"confirmed": true}
                 ↓
        ERPNext Leave Application created
        Returns Leave Application ID ✅

User clicks Cancel → POST /api/v1/confirm {"confirmed": false}
                 ↓
        Session deleted, no changes made ❌
```

---

## 🏗️ Project Structure

```
Fyntwin-assignment/
├── backend/
│   ├── main.py                    # FastAPI app entry point, CORS, router registration
│   ├── config.py                  # pydantic-settings — loads all config from .env
│   ├── routes/
│   │   ├── agent.py               # POST /api/v1/run  |  POST /api/v1/confirm
│   │   └── health.py              # GET /api/v1/health  |  GET /api/v1/history
│   ├── agents/
│   │   ├── team.py                # Agno Team ("coordinate" mode) + HITL session store
│   │   ├── agents_1.py            # Employee & Balance Agent — fetches employee + leave balance
│   │   ├── agents_2.py            # Team Coverage Agent — checks overlapping approved leaves
│   │   └── agents_3.py            # Decision & Action Agent — synthesises results, flags conflicts
│   ├── tools/
│   │   └── erpnext_tools.py       # @tool-decorated ERPNext functions (5 tools)
│   ├── schemas/
│   │   └── models.py              # All Pydantic request/response models
│   └── services/
│       └── erpnext_client.py      # Reusable ERPNext HTTP client (auth, error handling)
├── frontend/
│   └── streamlit_app.py           # Streamlit UI — chat interface + HITL confirmation card
├── .env.example                   # Environment variable template (no secrets)
├── requirements.txt               # Pinned dependencies (uv pip compile)
├── pyproject.toml
└── README.md
```

### Agent Roles (non-overlapping)

| Agent | File | Responsibility |
|---|---|---|
| Employee & Balance Agent | `agents_1.py` | Fetch employee record, available leave types, compute leave balance |
| Team Coverage Agent | `agents_2.py` | Query approved leaves for department in the requested date range |
| Decision & Action Agent | `agents_3.py` | Receive both reports, determine outcome (approve / reject), flag conflicts |

### ERPNext Tools (5 total)

| Tool | Purpose |
|---|---|
| `get_employee` | Fetch employee details by ID |
| `get_leave_balance` | Fetch allocation & compute available balance |
| `get_team_leaves` | Query approved leaves for a department + date range |
| `get_leave_types` | List all configured leave types in ERPNext |
| `create_leave_application` | Create a Leave Application document (called only after HITL confirm) |

---

## ⚙️ Setup & Run (Under 5 Minutes)

### Prerequisites
- Python 3.11+
- A live ERPNext instance (cloud or self-hosted)
- A Groq API key ([console.groq.com](https://console.groq.com))

### Step 1 — Clone the repository

```bash
git clone https://github.com/<your-username>/Fyntwin-assignment.git
cd Fyntwin-assignment
```

### Step 2 — Create and activate a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure environment variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

Open `.env` and set:

```env
# ERPNext instance URL (no trailing slash)
ERPNEXT_URL=https://your-instance.erpnext.com

# ERPNext API credentials
# Generate from: ERPNext → Avatar (top-right) → API Access → Generate Keys
ERPNEXT_API_KEY=your_api_key_here
ERPNEXT_API_SECRET=your_api_secret_here

# Test employee — must have a Leave Allocation in ERPNext for the current year
EMPLOYEE_ID=EMP-0001

# Department of the test employee (used for team coverage checks)
DEPARTMENT=All Departments

# Groq API key for LLM inference
GROQ_API_KEY=your_groq_api_key_here

# App metadata (optional)
APP_NAME=Leave Request Automation
APP_VERSION=1.0.0
```

> **ERPNext Data Setup:** Go to **HR → Leave Allocation → New**, select your employee, choose leave type (e.g., `Casual Leave`), set allocated days (e.g., `15`), and save with **Submit** (docstatus = 1). The `EMPLOYEE_ID` in `.env` must match this employee.

### Step 5 — Start the FastAPI backend

```bash
# From the project root
uvicorn backend.main:app --reload --port 8000
```

The API will be live at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### Step 6 — Start the Streamlit frontend

Open a **second terminal** (same virtualenv):

```bash
streamlit run frontend/streamlit_app.py
```

The UI opens at `http://localhost:8501`.

### Step 7 — Test the system

Type a leave request in the chat box, for example:

```
I want casual leave from December 24 to December 27, that's 4 days
```

The system will validate the request, pause for confirmation, and — after you click **Confirm** — create the Leave Application in ERPNext and return the Application ID.

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Service health check |
| `POST` | `/api/v1/run` | Submit a leave request prompt |
| `POST` | `/api/v1/confirm` | Confirm or cancel a pending leave action |
| `GET` | `/api/v1/history` | List active pending sessions |

### POST `/api/v1/run` — Example Request

```json
{
  "prompt": "I want casual leave from December 24 to December 27, that's 4 days"
}
```

### POST `/api/v1/run` — Example Response (awaiting confirmation)

```json
{
  "status": "awaiting_confirmation",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Leave request validated. Awaiting your confirmation.",
  "pending_action": {
    "employee_id": "EMP-0001",
    "employee_name": "Test Employee",
    "leave_type": "Casual Leave",
    "from_date": "2026-12-24",
    "to_date": "2026-12-27",
    "total_days": 4,
    "current_balance": 15.0,
    "balance_after": 11.0,
    "colleagues_on_leave": 1,
    "coverage_risk": true,
    "confirmation_prompt": "Create Leave Application for Test Employee from 2026-12-24 to 2026-12-27 (4 days)?"
  },
  "agents_involved": [
    "Employee & Balance Agent",
    "Team Coverage Agent",
    "Decision & Action Agent"
  ]
}
```

### POST `/api/v1/confirm` — Example Request

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "confirmed": true
}
```

### POST `/api/v1/confirm` — Example Response

```json
{
  "status": "completed",
  "message": "Leave application created successfully for Test Employee from 2026-12-24 to 2026-12-27. Application ID: HR-LAP-2026-00042",
  "leave_application_id": "HR-LAP-2026-00042"
}
```

---

## 🛡️ Conditional Workflow (Branching Logic)

The system implements a clear conditional branch in `team.py`:

```
Balance Check Result
        │
        ├── INSUFFICIENT BALANCE
        │       └── Return immediately with current balance + max available days suggestion
        │           (No HITL, no ERPNext write)
        │
        └── SUFFICIENT BALANCE
                │
                ├── Coverage check result included in pending_action
                │   (coverage_risk flag is set, still allowed to proceed)
                │
                └── PAUSE → awaiting_confirmation
                        │
                        ├── User CONFIRMS → Create Leave Application in ERPNext
                        └── User CANCELS  → No changes made
```

---

## 📦 Key Dependencies

| Package | Version | Purpose |
|---|---|---|
| `agno` | 2.6.5 | Multi-agent orchestration framework |
| `fastapi` | 0.136.1 | Backend REST API |
| `uvicorn` | 0.46.0 | ASGI server |
| `pydantic` | 2.13.4 | Data validation |
| `pydantic-settings` | 2.14.1 | `.env` config loading |
| `httpx` | 0.28.1 | Async HTTP client for ERPNext |
| `streamlit` | 1.57.0 | Frontend UI |
| `groq` (via agno) | — | LLM inference (llama-3.1-8b-instant) |

---

## 🔒 Security Notes

- **`.env` is git-ignored** — never committed. Only `.env.example` (with empty values) is in the repository.
- All ERPNext authentication uses token-based headers (`Authorization: token <key>:<secret>`).
- Zero hardcoded credentials anywhere in source code — everything flows through `config.py` → `pydantic-settings` → `.env`.

---

## 🐛 Troubleshooting

| Issue | Fix |
|---|---|
| `ERPNext GET error 403` | Check API key/secret in `.env`; ensure the ERPNext user has HR module permissions |
| `No allocation found for Casual Leave` | Create a Leave Allocation for the employee in ERPNext (must be submitted, docstatus=1) |
| `Backend not reachable` in UI | Ensure FastAPI is running on port 8000 before starting Streamlit |
| `Team.__init__() unexpected keyword` | Upgrade agno: `pip install --upgrade agno` |
| Agent returns no HITL card | The prompt must contain a leave type keyword + date range for `_extract_pending_action` to trigger |

---

*Built for Fyntwin Intern Assignment #06 — HR Leave Management Module*
