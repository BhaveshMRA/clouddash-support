"""
app.py — Streamlit chat UI for CloudDash Support System
Talks to the deployed FastAPI backend via REST.
"""
import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "https://web-production-4096b.up.railway.app")

st.set_page_config(
    page_title="CloudDash Support",
    page_icon="☁️",
    layout="centered"
)

st.title("☁️ CloudDash Support")
st.caption("AI-powered customer support — Technical, Billing, and Account help")

# Session state
if "trace_id" not in st.session_state:
    st.session_state.trace_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "awaiting_human" not in st.session_state:
    st.session_state.awaiting_human = False

# Sidebar
with st.sidebar:
    st.header("Session Info")
    if st.session_state.trace_id:
        st.code(f"Trace ID:\n{st.session_state.trace_id}")
    else:
        st.info("Start a conversation to see your trace ID")

    if st.button("New Conversation", use_container_width=True):
        st.session_state.trace_id = None
        st.session_state.messages = []
        st.session_state.awaiting_human = False
        st.rerun()

    st.divider()
    st.markdown("**Try these:**")
    examples = [
        "My alerts stopped firing after I updated my AWS credentials",
        "I was charged twice for April and want a refund",
        "How do I set up SSO with Okta?",
        "Does CloudDash support Datadog integration?",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True, key=ex):
            st.session_state["prefill"] = ex

# Display chat history
for msg in st.session_state.messages:
    role = msg["role"]
    with st.chat_message(role):
        st.markdown(msg["content"])
        if msg.get("agent"):
            st.caption(f"Agent: {msg['agent']}")
        if msg.get("kb_sources"):
            with st.expander("KB Sources"):
                for src in msg["kb_sources"]:
                    st.markdown(f"- {src}")

# Escalation banner
if st.session_state.awaiting_human:
    st.warning("This conversation has been escalated to a human agent. Our team will follow up with you shortly.")

# Chat input
prefill = st.session_state.pop("prefill", None)
user_input = st.chat_input(
    "Ask about technical issues, billing, or account management...",
    disabled=st.session_state.awaiting_human
)

if prefill:
    user_input = prefill

if user_input:
    # Add user message to display
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                if st.session_state.trace_id is None:
                    # Start new conversation
                    resp = requests.post(
                        f"{API_URL}/conversation",
                        json={"message": user_input},
                        timeout=90,
                    )
                else:
                    # Continue existing conversation
                    resp = requests.post(
                        f"{API_URL}/conversation/{st.session_state.trace_id}/message",
                        json={"message": user_input},
                        timeout=90,
                    )

                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.trace_id      = data["trace_id"]
                    st.session_state.awaiting_human = data.get("awaiting_human", False)

                    response_text = data["response"]
                    agent_name    = data.get("agent", "system")
                    kb_sources    = data.get("kb_sources", [])

                    st.markdown(response_text)
                    st.caption(f"Agent: {agent_name}")
                    if kb_sources:
                        with st.expander("KB Sources"):
                            for src in kb_sources:
                                st.markdown(f"- {src}")

                    st.session_state.messages.append({
                        "role":       "assistant",
                        "content":    response_text,
                        "agent":      agent_name,
                        "kb_sources": kb_sources,
                    })

                    if st.session_state.awaiting_human:
                        st.rerun()

                elif resp.status_code == 400:
                    err = resp.json().get("detail", "Request not allowed.")
                    st.error(err)
                else:
                    st.error(f"Error {resp.status_code}: {resp.text[:200]}")

            except requests.exceptions.Timeout:
                st.error("Request timed out — the server may be cold starting. Please try again in 30 seconds.")
            except Exception as e:
                st.error(f"Connection error: {str(e)}")
