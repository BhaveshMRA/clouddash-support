"""
agents/orchestrator.py

LangGraph StateGraph that wires all agents together.

Graph structure:
    START
      ↓
   Triage  ←─────────────────┐
    ↙  ↓  ↘                  │ (unknown intent loop)
Tech Billing Escalation       │
  ↘    ↓    ↙
  Escalation (if needed)
      ↓
     END
"""
from __future__ import annotations

import uuid

from langgraph.graph import END, START, StateGraph

from agents.billing_agent import BillingAgent
from agents.escalation_agent import EscalationAgent
from agents.state import AgentRole, Message, SupportState
from agents.technical_agent import TechnicalSupportAgent
from agents.triage_agent import TriageAgent
from handover.audit_log import log_handover
from handover.protocol import create_handover_event

# ── Instantiate agents once (singletons) ──────────────────────────────────────
_triage     = TriageAgent()
_technical  = TechnicalSupportAgent()
_billing    = BillingAgent()
_escalation = EscalationAgent()


# ── Node wrappers ──────────────────────────────────────────────────────────────
# Each wrapper calls the agent's run() and logs handover events

def triage_node(state: SupportState) -> dict:
    result       = _triage.run(state)
    prev_agent   = state.get("current_agent")
    next_routing = result.get("routing_decision", "triage")

    # Log handover if we're coming from another agent
    if prev_agent and prev_agent != AgentRole.TRIAGE:
        event = create_handover_event(
            source_agent = prev_agent,
            target_agent = AgentRole.TRIAGE,
            reason       = "Fallback to triage — intent unclear",
            entities     = state.get("extracted_entities"),
        )
        log_handover(state.get("trace_id", "unknown"), event)
        result["handover_log"] = [event]

    return result


def technical_node(state: SupportState) -> dict:
    prev_agent = state.get("current_agent")
    result     = _technical.run(state)

    if prev_agent and prev_agent != AgentRole.TECHNICAL:
        event = create_handover_event(
            source_agent = prev_agent,
            target_agent = AgentRole.TECHNICAL,
            reason       = f"Routed from {prev_agent.value} — technical issue",
            entities     = state.get("extracted_entities"),
        )
        log_handover(state.get("trace_id", "unknown"), event)
        result["handover_log"] = [event]

    return result


def billing_node(state: SupportState) -> dict:
    prev_agent = state.get("current_agent")
    result     = _billing.run(state)

    if prev_agent and prev_agent != AgentRole.BILLING:
        event = create_handover_event(
            source_agent = prev_agent,
            target_agent = AgentRole.BILLING,
            reason       = f"Routed from {prev_agent.value} — billing issue",
            entities     = state.get("extracted_entities"),
        )
        log_handover(state.get("trace_id", "unknown"), event)
        result["handover_log"] = [event]

    return result


def escalation_node(state: SupportState) -> dict:
    prev_agent = state.get("current_agent")
    result     = _escalation.run(state)

    if prev_agent and prev_agent != AgentRole.ESCALATION:
        entities = state.get("extracted_entities")
        reason   = "Escalated to human support"
        if entities and entities.raw_issue:
            reason = f"Escalated: {entities.raw_issue}"

        event = create_handover_event(
            source_agent = prev_agent or AgentRole.TRIAGE,
            target_agent = AgentRole.ESCALATION,
            reason       = reason,
            entities     = entities,
        )
        log_handover(state.get("trace_id", "unknown"), event)
        result["handover_log"] = [event]

    return result


# ── Routing functions ──────────────────────────────────────────────────────────

def route_from_triage(state: SupportState) -> str:
    """
    Reads routing_decision set by TriageAgent and returns
    the name of the next node.
    """
    decision    = state.get("routing_decision", "triage")
    error_count = state.get("error_count", 0)

    # Force escalation if too many errors
    if error_count >= 2:
        return "escalation"

    # Force escalation if too many handovers
    handover_log = state.get("handover_log", [])
    if len(handover_log) >= 3:
        return "escalation"

    route_map = {
        "technical":  "technical",
        "billing":    "billing",
        "escalation": "escalation",
        "triage":     "escalation",  # unknown intent → escalate, never loop
        "end":        END,
    }
    return route_map.get(decision, "triage")


def route_from_specialist(state: SupportState) -> str:
    """
    Routing after Technical or Billing agent completes.
    They can either end the conversation or escalate.
    """
    decision    = state.get("routing_decision", "end")
    error_count = state.get("error_count", 0)

    if error_count >= 2:
        return "escalation"

    if state.get("awaiting_human"):
        return "escalation"

    route_map = {
        "escalation": "escalation",
        "technical":  "technical",
        "billing":    "billing",
        "end":        END,
    }
    return route_map.get(decision, END)


# ── Build the graph ────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(SupportState)

    # Add nodes
    graph.add_node("triage",     triage_node)
    graph.add_node("technical",  technical_node)
    graph.add_node("billing",    billing_node)
    graph.add_node("escalation", escalation_node)

    # Entry point
    graph.add_edge(START, "triage")

    # Triage routes to specialist agents
    graph.add_conditional_edges(
        "triage",
        route_from_triage,
        {
            "technical":  "technical",
            "billing":    "billing",
            "escalation": "escalation",
            "triage":     "escalation",  # unknown intent → escalate, never loop
            END:          END,
        },
    )

    # Technical and Billing can escalate or end
    graph.add_conditional_edges(
        "technical",
        route_from_specialist,
        {
            "escalation": "escalation",
            "technical":  "technical",
            "billing":    "billing",
            END:          END,
        },
    )

    graph.add_conditional_edges(
        "billing",
        route_from_specialist,
        {
            "escalation": "escalation",
            "technical":  "technical",
            "billing":    "billing",
            END:          END,
        },
    )

    # Escalation always ends
    graph.add_edge("escalation", END)

    return graph.compile()


# ── Public interface ───────────────────────────────────────────────────────────

# Compiled graph — import this in the API layer
support_graph = build_graph()


def create_initial_state(user_message: str) -> SupportState:
    """Creates a fresh SupportState for a new conversation."""
    from agents.state import (
        AgentRole, ExtractedEntities, Intent, Sentiment
    )

    return {
        "trace_id":             str(uuid.uuid4()),
        "conversation_history": [
            Message(role="user", content=user_message)
        ],
        "extracted_entities":   ExtractedEntities(),
        "current_agent":        AgentRole.TRIAGE,
        "handover_log":         [],
        "retrieved_chunks":     [],
        "awaiting_human":       False,
        "routing_decision":     None,
        "error_count":          0,
        "escalation_payload":   None,
    }


def run_conversation_turn(
    state: SupportState,
    user_message: str,
) -> SupportState:
    """
    Adds a new user message to state and runs one full graph pass.
    Returns the updated state after all agents have completed.
    """
    new_msg = Message(role="user", content=user_message)

    updated_state = {
        **state,
        "conversation_history": state["conversation_history"] + [new_msg],
        "routing_decision":     None,
        "retrieved_chunks":     [],
    }

    result = support_graph.invoke(updated_state, config={"recursion_limit": 25})
    return result
