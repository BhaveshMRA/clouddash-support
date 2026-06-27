"""
handover/protocol.py

Handles context packaging when control passes between agents.
Ensures the receiving agent has full context without the customer
needing to repeat themselves.
"""
from __future__ import annotations

from agents.state import (
    AgentRole, ExtractedEntities, HandoverEvent, SupportState
)


def create_handover_event(
    source_agent: AgentRole,
    target_agent: AgentRole,
    reason: str,
    entities: ExtractedEntities | None,
) -> HandoverEvent:
    """
    Creates a structured HandoverEvent for the audit log.
    Called every time routing changes between agents.
    """
    snapshot = {}
    if entities:
        snapshot = {
            "customer_id":        entities.customer_id,
            "intent":             entities.intent.value,
            "sentiment":          entities.sentiment.value,
            "plan_type":          entities.plan_type,
            "raw_issue":          entities.raw_issue,
            "product_references": entities.product_references,
        }

    return HandoverEvent(
        source_agent    = source_agent,
        target_agent    = target_agent,
        reason          = reason,
        entity_snapshot = snapshot,
        success         = True,
    )


def build_handover_context(state: SupportState) -> str:
    """
    Builds a context summary string injected into the receiving
    agent's prompt so it has full conversation context.
    """
    entities = state.get("extracted_entities")
    history  = state.get("conversation_history", [])
    log      = state.get("handover_log", [])

    lines = ["=== HANDOVER CONTEXT ==="]

    if entities:
        lines.append(f"Customer ID  : {entities.customer_id or 'not provided'}")
        lines.append(f"Intent       : {entities.intent.value}")
        lines.append(f"Sentiment    : {entities.sentiment.value}")
        lines.append(f"Plan         : {entities.plan_type or 'unknown'}")
        lines.append(f"Issue        : {entities.raw_issue or 'see history'}")

    if log:
        last = log[-1]
        lines.append(f"Handed off from: {last.source_agent.value} → reason: {last.reason}")

    lines.append(f"Conversation turns: {len(history)}")
    lines.append("========================")

    return "\n".join(lines)
