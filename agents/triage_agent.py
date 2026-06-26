"""
agents/triage_agent.py

First point of contact. Classifies intent, extracts entities,
sets routing_decision so the LangGraph router knows where to send next.
"""
from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import BaseAgent
from agents.state import (
    AgentRole, ExtractedEntities, Intent,
    Message, Priority, Sentiment, SupportState
)

EXTRACTION_PROMPT = """Analyze the customer message and conversation history.
Return a JSON object with exactly these fields:

{
  "intent": "technical" | "billing" | "account" | "general" | "escalate" | "unknown",
  "customer_id": "CUST-XXXX or null",
  "plan_type": "Free" | "Pro" | "Enterprise" | null,
  "sentiment": "neutral" | "frustrated" | "urgent",
  "raw_issue": "one sentence describing the core problem",
  "product_references": ["list", "of", "products", "mentioned"]
}

Return ONLY the JSON object. No explanation, no markdown, no preamble."""


class TriageAgent(BaseAgent):

    def __init__(self):
        super().__init__("triage")

    def _extract_entities(
        self,
        message: str,
        history: list[Message]
    ) -> ExtractedEntities:
        """
        Uses LLM to extract structured entities from the customer message.
        Falls back to UNKNOWN intent if parsing fails.
        """
        history_text = ""
        if history:
            recent = history[-4:]
            history_text = "\n".join(
                f"{m.role.upper()}: {m.content}" for m in recent
            )

        prompt = f"{EXTRACTION_PROMPT}\n\nConversation history:\n{history_text}\n\nCustomer message: {message}"

        response = self.llm.invoke([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt),
        ])

        try:
            # Strip markdown fences if model adds them
            raw = response.content.strip()
            raw = re.sub(r"```json\s*|\s*```", "", raw).strip()
            data = json.loads(raw)

            return ExtractedEntities(
                customer_id       = data.get("customer_id"),
                intent            = Intent(data.get("intent", "unknown")),
                sentiment         = Sentiment(data.get("sentiment", "neutral")),
                plan_type         = data.get("plan_type"),
                raw_issue         = data.get("raw_issue"),
                product_references= data.get("product_references", []),
            )
        except Exception:
            return ExtractedEntities(intent=Intent.UNKNOWN)

    def _generate_response(
        self,
        message: str,
        entities: ExtractedEntities,
        history: list[Message],
    ) -> str:
        """Generate a brief acknowledgement while routing."""
        is_first_message = len(history) == 0

        if is_first_message:
            greeting = "Hi there! Thanks for reaching out to CloudDash support. "
        else:
            greeting = ""

        if entities.intent == Intent.TECHNICAL:
            return (f"{greeting}I can see you're having a technical issue — "
                    f"let me connect you with our Technical Support team right away.")
        elif entities.intent == Intent.BILLING:
            return (f"{greeting}I understand you have a billing question. "
                    f"I'll transfer you to our Billing team who can help.")
        elif entities.intent == Intent.ESCALATE:
            return (f"{greeting}I understand you'd like to speak with someone "
                    f"directly. Let me escalate this to our support team now.")
        elif entities.intent == Intent.ACCOUNT:
            return (f"{greeting}I can see this is an account access issue. "
                    f"Our Technical team handles SSO and access management.")
        else:
            return (f"{greeting}Thanks for your message. Let me look into "
                    f"that for you.")

    def run(self, state: SupportState) -> dict:
        """
        LangGraph node entry point.

        Reads: conversation_history (last message is the customer's input)
        Writes: extracted_entities, routing_decision, conversation_history,
                current_agent, error_count
        """
        try:
            history  = state.get("conversation_history", [])
            last_msg = history[-1] if history else None

            if not last_msg or last_msg.role != "user":
                return {
                    "routing_decision": "triage",
                    "current_agent":    AgentRole.TRIAGE,
                }

            # Extract intent and entities
            entities = self._extract_entities(last_msg.content, history[:-1])

            # Map intent to routing decision
            routing_map = {
                Intent.TECHNICAL: "technical",
                Intent.BILLING:   "billing",
                Intent.ACCOUNT:   "technical",   # Tech handles account issues
                Intent.GENERAL:   "technical",   # Tech handles general questions
                Intent.ESCALATE:  "escalation",
                Intent.UNKNOWN:   "triage",      # Stay in triage, ask for clarity
            }
            routing = routing_map.get(entities.intent, "triage")

            # Generate triage acknowledgement
            response_text = self._generate_response(
                last_msg.content, entities, history[:-1]
            )

            assistant_msg = Message(
                role    = "assistant",
                content = response_text,
                agent   = AgentRole.TRIAGE,
            )

            return {
                "extracted_entities":  entities,
                "routing_decision":    routing,
                "current_agent":       AgentRole.TRIAGE,
                "conversation_history":[assistant_msg],
            }

        except Exception as e:
            return {
                "routing_decision": "escalation",
                "current_agent":    AgentRole.TRIAGE,
                "error_count":      state.get("error_count", 0) + 1,
            }
