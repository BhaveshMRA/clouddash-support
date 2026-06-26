"""
agents/billing_agent.py

Handles billing inquiries with mock account lookup.
Escalates automatically when refund authority is exceeded.
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import BaseAgent
from agents.state import AgentRole, Message, Sentiment, SupportState
from retrieval.retriever import format_citations, format_context, retrieve

# Escalation triggers — if any keyword found, escalate regardless of amount
ESCALATION_KEYWORDS = [
    "charged twice", "double charged", "duplicate charge",
    "charged twice", "fraud", "unauthorized", "speak to a manager",
    "manager", "legal", "lawyer", "refund immediately",
]


class BillingAgent(BaseAgent):

    def __init__(self):
        super().__init__("billing")
        self.mock_accounts: dict = self.config.get("mock_accounts", {})
        self.max_refund_limit: float = (
            self.config.get("guardrails", {})
                       .get("max_refund_without_escalation", 500)
        )

    def _lookup_account(self, customer_id: str | None) -> dict | None:
        """Simulates a database account lookup."""
        if not customer_id:
            return None
        return self.mock_accounts.get(customer_id)

    def _needs_escalation(self, message: str, sentiment: Sentiment) -> bool:
        """
        Determines if this billing issue exceeds agent authority.
        Two triggers:
        1. Message contains escalation keywords (duplicate charge, manager request)
        2. Customer sentiment is urgent AND message mentions refund
        """
        msg_lower = message.lower()

        for keyword in ESCALATION_KEYWORDS:
            if keyword in msg_lower:
                return True

        if sentiment == Sentiment.URGENT and "refund" in msg_lower:
            return True

        return False

    def run(self, state: SupportState) -> dict:
        """
        LangGraph node entry point.

        Reads:  conversation_history, extracted_entities
        Writes: conversation_history, retrieved_chunks,
                routing_decision, current_agent
        """
        try:
            history  = state.get("conversation_history", [])
            entities = state.get("extracted_entities")

            user_messages = [m for m in history if m.role == "user"]
            if not user_messages:
                return {"current_agent": AgentRole.BILLING}

            latest_query = user_messages[-1].content

            # Check if this needs immediate escalation
            sentiment = entities.sentiment if entities else Sentiment.NEUTRAL
            if self._needs_escalation(latest_query, sentiment):
                escalation_msg = Message(
                    role    = "assistant",
                    content = (
                        "I can see this is an urgent billing matter that requires "
                        "immediate attention from our billing team. I'm escalating "
                        "this right now with high priority so a specialist can "
                        "assist you directly."
                    ),
                    agent   = AgentRole.BILLING,
                )
                return {
                    "conversation_history": [escalation_msg],
                    "routing_decision":     "escalation",
                    "current_agent":        AgentRole.BILLING,
                }

            # Look up account if we have a customer ID
            account_info = self._lookup_account(
                entities.customer_id if entities else None
            )

            # Retrieve relevant billing KB articles
            history_dicts = [
                {"role": m.role, "content": m.content} for m in history[-6:]
            ]
            chunks, _ = retrieve(
                query           = latest_query,
                history         = history_dicts,
                category_filter = "billing",
            )

            kb_context = format_context(chunks)
            citations  = format_citations(chunks)

            # Build context block
            account_context = ""
            if account_info:
                account_context = f"""
Customer account information:
- Customer ID: {entities.customer_id}
- Current plan: {account_info['plan']}
- Billing cycle: {account_info['billing_cycle']}
- Next invoice date: {account_info['next_invoice_date']}
- Outstanding balance: ${account_info['outstanding_balance']}
"""

            user_prompt = f"""Customer billing inquiry: {latest_query}
{account_context}
Knowledge Base — Billing Policies:
{kb_context}

Provide a clear, helpful response. Cite policy sources using [KB-XXX] format.
If you cannot resolve this within your authority, say so and indicate escalation."""

            response = self.llm.invoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_prompt),
            ])

            response_text = response.content.strip()
            if citations and "[KB-" not in response_text:
                response_text += f"\n\nPolicy reference: {citations}"

            routing = "end"
            if not chunks:
                routing = "escalation"

            assistant_msg = Message(
                role    = "assistant",
                content = response_text,
                agent   = AgentRole.BILLING,
            )

            return {
                "conversation_history": [assistant_msg],
                "retrieved_chunks":     chunks,
                "routing_decision":     routing,
                "current_agent":        AgentRole.BILLING,
            }

        except Exception as e:
            error_msg = Message(
                role    = "assistant",
                content = "I encountered an issue with your billing inquiry. Let me escalate this to our billing team directly.",
                agent   = AgentRole.BILLING,
            )
            return {
                "conversation_history": [error_msg],
                "routing_decision":     "escalation",
                "current_agent":        AgentRole.BILLING,
                "error_count":          state.get("error_count", 0) + 1,
            }
