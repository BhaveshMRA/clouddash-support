"""
api/main.py

FastAPI application with three endpoints:
  POST /conversation              - start a new conversation
  POST /conversation/{id}/message - send a message, get agent response
  GET  /conversation/{id}/history - retrieve full conversation history
"""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agents.orchestrator import (
    create_initial_state,
    run_conversation_turn,
    support_graph,
)
from agents.state import AgentRole, ExtractedEntities, Message, SupportState
from api.models import (
    ConversationHistoryResponse,
    ErrorResponse,
    MessageRecord,
    SendMessageRequest,
    SendMessageResponse,
    StartConversationRequest,
    StartConversationResponse,
)
from retrieval.guardrails import check_input

# ── Logging ───────────────────────────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
log = structlog.get_logger()

# ── In-memory conversation store ──────────────────────────────────────────────
# Maps trace_id → SupportState
# Production: replace with Redis or a database
conversations: dict[str, SupportState] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("clouddash_support_starting")
    yield
    log.info("clouddash_support_stopping")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "CloudDash Support System",
    description = "Multi-agent AI customer support for CloudDash",
    version     = "0.1.0",
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_last_assistant_response(state: SupportState) -> tuple[str, str]:
    """Returns (response_text, agent_name) from the latest assistant message."""
    assistant_msgs = [
        m for m in state["conversation_history"]
        if m.role == "assistant"
    ]
    if not assistant_msgs:
        return "I'm here to help. What can I assist you with?", "triage"

    last = assistant_msgs[-1]
    agent_name = last.agent.value if last.agent else "system"
    return last.content, agent_name


def get_kb_sources(state: SupportState) -> list[str]:
    """Returns unique KB IDs from retrieved chunks."""
    seen = {}
    for chunk in state.get("retrieved_chunks", []):
        if chunk.kb_id not in seen:
            seen[chunk.kb_id] = chunk.title
    return [f"[{k}] {v}" for k, v in seen.items()]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post(
    "/conversation",
    response_model = StartConversationResponse,
    summary        = "Start a new support conversation",
)
async def start_conversation(request: StartConversationRequest):
    """
    Creates a new conversation and processes the first message.
    Returns a trace_id used for all subsequent messages.
    """
    # Input guardrail
    guardrail_result = check_input(request.message)
    if not guardrail_result["allowed"]:
        raise HTTPException(
            status_code = 400,
            detail      = guardrail_result["reason"],
        )

    log.info(
        "conversation_started",
        message_preview = request.message[:100],
    )

    try:
        state  = create_initial_state(request.message)
        result = support_graph.invoke(state)

        trace_id = result["trace_id"]
        conversations[trace_id] = result

        response_text, agent_name = get_last_assistant_response(result)

        log.info(
            "conversation_processed",
            trace_id       = trace_id,
            final_agent    = agent_name,
            awaiting_human = result["awaiting_human"],
        )

        return StartConversationResponse(
            trace_id       = trace_id,
            response       = response_text,
            agent          = agent_name,
            awaiting_human = result["awaiting_human"],
        )

    except Exception as e:
        log.error("conversation_start_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/conversation/{trace_id}/message",
    response_model = SendMessageResponse,
    summary        = "Send a message in an existing conversation",
)
async def send_message(trace_id: str, request: SendMessageRequest):
    """
    Adds a message to an existing conversation and runs it
    through the agent graph. Returns the agent's response.
    """
    if trace_id not in conversations:
        raise HTTPException(
            status_code = 404,
            detail      = f"Conversation {trace_id} not found.",
        )

    # Input guardrail
    guardrail_result = check_input(request.message)
    if not guardrail_result["allowed"]:
        raise HTTPException(
            status_code = 400,
            detail      = guardrail_result["reason"],
        )

    state = conversations[trace_id]

    if state.get("awaiting_human"):
        raise HTTPException(
            status_code = 400,
            detail      = "This conversation has been escalated to a human agent.",
        )

    log.info(
        "message_received",
        trace_id        = trace_id,
        message_preview = request.message[:100],
    )

    try:
        result = run_conversation_turn(state, request.message)
        conversations[trace_id] = result

        response_text, agent_name = get_last_assistant_response(result)
        kb_sources = get_kb_sources(result)

        log.info(
            "message_processed",
            trace_id       = trace_id,
            agent          = agent_name,
            kb_sources     = kb_sources,
            awaiting_human = result["awaiting_human"],
        )

        return SendMessageResponse(
            trace_id       = trace_id,
            response       = response_text,
            agent          = agent_name,
            awaiting_human = result["awaiting_human"],
            kb_sources     = kb_sources,
        )

    except Exception as e:
        log.error("message_processing_failed", trace_id=trace_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/conversation/{trace_id}/history",
    response_model = ConversationHistoryResponse,
    summary        = "Retrieve full conversation history",
)
async def get_history(trace_id: str):
    """Returns the complete message history for a conversation."""
    if trace_id not in conversations:
        raise HTTPException(
            status_code = 404,
            detail      = f"Conversation {trace_id} not found.",
        )

    state = conversations[trace_id]

    messages = [
        MessageRecord(
            role      = m.role,
            content   = m.content,
            agent     = m.agent.value if m.agent else None,
            timestamp = m.timestamp,
        )
        for m in state["conversation_history"]
    ]

    return ConversationHistoryResponse(
        trace_id       = trace_id,
        messages       = messages,
        handover_count = len(state.get("handover_log", [])),
        awaiting_human = state.get("awaiting_human", False),
    )


@app.get("/health", summary="Health check")
async def health():
    return {
        "status":        "ok",
        "conversations": len(conversations),
        "version":       "0.1.0",
    }
