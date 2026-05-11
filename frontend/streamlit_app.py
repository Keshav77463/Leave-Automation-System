import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="Leave Request Assistant", page_icon="🏖️", layout="wide")
st.title("🏖️ Leave Request Automation System")
st.caption("Powered by Agno Multi-Agent AI + ERPNext")

# ── Session State ────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "pending_action" not in st.session_state:
    st.session_state.pending_action = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    st.header("ℹ️ How to use")
    st.markdown("""
    Type a leave request like:
    > *I want casual leave from December 24 to December 27, that's 4 days*

    The system will:
    1. Check your leave balance
    2. Check team coverage
    3. Ask for your confirmation
    4. Create the leave application
    """)

    st.divider()
    st.header("🤖 Agents")
    st.markdown("""
    - 👤 **Employee & Balance Agent**
    - 👥 **Team Coverage Agent**  
    - ✅ **Decision & Action Agent**
    """)

    st.divider()
    if st.button("🔍 Check Health"):
        try:
            resp = requests.get(f"{BACKEND_URL}/api/v1/health")
            data = resp.json()
            st.success(f"✅ {data['service']} v{data['version']} — {data['status']}")
        except Exception as e:
            st.error(f"Backend not reachable: {e}")

# ── Chat History ─────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── HITL Confirmation Card ───────────────────────────────────────
if st.session_state.pending_action:
    pa = st.session_state.pending_action
    st.divider()
    st.subheader("⚠️ Confirmation Required")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📋 Leave Details")
        st.table({
            "Field": ["Employee", "Leave Type", "From Date", "To Date", "Total Days"],
            "Value": [
                pa["employee_name"],
                pa["leave_type"],
                pa["from_date"],
                pa["to_date"],
                pa["total_days"],
            ]
        })

    with col2:
        st.markdown("### 📊 Balance & Coverage")
        st.table({
            "Field": ["Current Balance", "Balance After Approval", "Colleagues on Leave", "Coverage Risk"],
            "Value": [
                pa["current_balance"],
                pa["balance_after"],
                pa["colleagues_on_leave"],
                "⚠️ YES" if pa["coverage_risk"] else "✅ NO",
            ]
        })

    if pa["coverage_risk"]:
        st.warning(f"⚠️ Coverage Risk: {pa['colleagues_on_leave']} colleague(s) already on leave during this period!")

    st.markdown(f"**{pa['confirmation_prompt']}**")

    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("✅ Confirm", type="primary", use_container_width=True):
            try:
                resp = requests.post(f"{BACKEND_URL}/api/v1/confirm", json={
                    "session_id": st.session_state.session_id,
                    "confirmed": True,
                })
                data = resp.json()
                msg = data["message"]
                if data.get("leave_application_id"):
                    msg += f"\n\n✅ **Leave Application ID: {data['leave_application_id']}**"
                st.session_state.messages.append({"role": "assistant", "content": msg})
                st.session_state.pending_action = None
                st.session_state.session_id = None
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    with col_no:
        if st.button("❌ Cancel", type="secondary", use_container_width=True):
            try:
                resp = requests.post(f"{BACKEND_URL}/api/v1/confirm", json={
                    "session_id": st.session_state.session_id,
                    "confirmed": False,
                })
                data = resp.json()
                st.session_state.messages.append({"role": "assistant", "content": data["message"]})
                st.session_state.pending_action = None
                st.session_state.session_id = None
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# ── Chat Input ───────────────────────────────────────────────────
if not st.session_state.pending_action:
    prompt = st.chat_input("Type your leave request here...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Processing your request..."):
                try:
                    resp = requests.post(f"{BACKEND_URL}/api/v1/run", json={
                        "prompt": prompt,
                    })
                    data = resp.json()

                    if data["status"] == "awaiting_confirmation":
                        st.session_state.session_id = data["session_id"]
                        st.session_state.pending_action = data["pending_action"]
                        msg = "✋ **Action Required:** I've validated your leave request. Please review the details below and confirm."
                        st.markdown(msg)
                        st.session_state.messages.append({"role": "assistant", "content": msg})
                        st.rerun()
                    else:
                        msg = data["message"]
                        st.markdown(msg)
                        st.session_state.messages.append({"role": "assistant", "content": msg})

                    if data.get("agents_involved"):
                        st.caption(f"🤖 Agents involved: {', '.join(data['agents_involved'])}")

                except Exception as e:
                    st.error(f"Backend error: {e}")