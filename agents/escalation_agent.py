"""
agents/escalation_agent.py

Packages conversation context for human handover.
Classifies priority and sentiment, creates HumanEscalationPayload.
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import BaseAgent
from agents.state import (
    AgentRole, HumanEscalationPayload, Message,
    Priority, Sentiment, SupportState
)


class EscalationAgent(BaseAgent):

    def __init__(self):
        super().__init__("escalation")

    def _classify_priority(
        self,
        entities,
        history: list[Message]
    ) -> Priority:
        """
        Rule-based priority classification.
        Keeps this deterministic — no LLM needed for a yes/no decision.
        """
        all_text = " ".join(m.content.lower() for m in history)

        if any(w in all_text for w in ["outage", "down", "data loss", "security", "breach"]):
            return Priority.CRITICAL

        if entities and entities.sentiment in [Sentiment.FRUSTRATED, Sentiment.URGENT]:
            return Priority.HIGH

        if any(w in all_text for w in ["charged twice", "duplicate", "refund", "manager"]):
            return Priority.HIGH

        if any(w in all_text for w in ["sso", "cannot login", "access denied", "locked out"]):
            return Priority.MEDIUM

        return Priority.MEDIUM

    def _summarize_conversation(self, history: list[Message]) -> str:
        """Uses LLM to generate a concise summary for the human agent."""
        if not history:
            return "No conversation history available."

        history_text = "\n".join(
            f"{m.role.upper()} [{m.agent or 'system'}]: {m.content}"
            for m in history
        )

        response = self.llm.invoke([
            SystemMessage(content=(
                "You are summarizing a customer support conversation for a human agent. "
                "Write a concise 3-5 sentence summary covering: "
                "1) What the customer's issue is, "
                "2) What was already attempted, "
                "3) Why escalation was needed. "
                "Be factual and specific."
            )),
            HumanMessage(content=f"Conversation:\n{history_text}\n\nSummary:"),
        ])
        return response.content.strip()

    def run(self, state: SupportState) -> dict:
        """
        LangGraph node entry point.

        Reads:  conversation_history, extracted_entities, trace_id
        Writes: conversation_history, escalation_payload,
                awaiting_human, current_agent, routing_decision
        """
        try:
            history  = state.get("conversation_history", [])
            entities = state.get("extracted_entities")
            trace_id = state.get("trace_id", "unknown")

            priority = self._classify_priority(entities, history)
            summary  = self._summarize_conversation(history)

            # Time estimate based on priority
            time_map = {
                Priority.CRITICAL: "1 hour",
                Priority.HIGH:     "4 hours",
                Priority.MEDIUM:   "1 business day",
                Priority.LOW:      "2 business days",
            }
            eta = time_map.get(priority, "1 business day")

            # Create the human handover payload
            sentiment = entities.sentiment if entities else Sentiment.NEUTRAL
            payload   = HumanEscalationPayload(
                trace_id             = trace_id,
                customer_id          = entities.customer_id if entities else None,
                priority             = priority,
                sentiment            = sentiment,
                issue_summary        = entities.raw_issue if entities and entities.raw_issue else "See conversation summary",
                conversation_summary = summary,
                recommended_action   = f"Review conversation {trace_id} and follow up with customer within {eta}.",
                full_history_ref     = f"Trace ID: {trace_id} — retrieve from audit logs",
            )

            # Generate the customer-facing escalation message
            response = self.llm.invoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=(
                    f"The customer needs human support. Priority: {priority.value}. "
                    f"Issue: {payload.issue_summary}. "
                    f"Expected response time: {eta}. "
                    f"Generate a warm, reassuring message to the customer."
                )),
            ])

            response_text = response.content.strip()

            assistant_msg = Message(
                role    = "assistant",
                content = response_text,
                agent   = AgentRole.ESCALATION,
            )

            return {
                "conversation_history": [assistant_msg],
                "escalation_payload":   payload,
                "awaiting_human":       True,
                "routing_decision":     "end",
                "current_agent":        AgentRole.ESCALATION,
            }

        except Exception as e:
            fallback_msg = Message(
                role    = "assistant",
                content = (
                    "I'm escalating your case to our human support team right away. "
                    "You will hear from us shortly. We apologize for any inconvenience."
                ),
                agent   = AgentRole.ESCALATION,
            )
            return {
                "conversation_history": [fallback_msg],
                "awaiting_human":       True,
                "routing_decision":     "end",
                "current_agent":        AgentRole.ESCALATION,
                "error_count":          state.get("error_count", 0) + 1,
            }
