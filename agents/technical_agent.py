"""
agents/technical_agent.py

Resolves technical issues using KB retrieval.
Always cites sources in responses.
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import BaseAgent
from agents.state import AgentRole, Message, SupportState
from retrieval.retriever import format_citations, format_context, retrieve


class TechnicalSupportAgent(BaseAgent):

    def __init__(self):
        super().__init__("technical")

    def run(self, state: SupportState) -> dict:
        """
        LangGraph node entry point.

        Reads:  conversation_history, extracted_entities, retrieved_chunks
        Writes: conversation_history, retrieved_chunks, routing_decision,
                current_agent
        """
        try:
            history  = state.get("conversation_history", [])
            entities = state.get("extracted_entities")

            # Get the customer's latest message
            user_messages = [m for m in history if m.role == "user"]
            if not user_messages:
                return {"current_agent": AgentRole.TECHNICAL}

            latest_query = user_messages[-1].content

            # Build history dict for query rewriter
            history_dicts = [
                {"role": m.role, "content": m.content} for m in history[-6:]
            ]

            # Retrieve relevant KB chunks
            # Technical agent searches troubleshooting + api + faq categories
            chunks, rewritten_query = retrieve(
                query    = latest_query,
                history  = history_dicts,
            )

            # Format KB context for the prompt
            kb_context = format_context(chunks)
            citations  = format_citations(chunks)

            # Build the full prompt
            user_prompt = f"""Customer issue: {latest_query}

Knowledge Base Context:
{kb_context}

Please provide a clear, step-by-step resolution. 
Cite sources using [KB-XXX] format inline.
If the knowledge base does not contain enough information, say so clearly."""

            if entities and entities.raw_issue:
                user_prompt = f"Issue summary: {entities.raw_issue}\n\n" + user_prompt

            response = self.llm.invoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_prompt),
            ])

            response_text = response.content.strip()

            # Append citation line if not already included
            if citations and "[KB-" not in response_text:
                response_text += f"\n\n{citations}"

            # Check if agent wants to escalate (no KB content found)
            routing = "end"
            if not chunks:
                routing = "escalation"
                response_text += (
                    "\n\nI wasn't able to find specific information about this "
                    "in our knowledge base. Let me escalate this to a specialist "
                    "who can help further."
                )

            assistant_msg = Message(
                role    = "assistant",
                content = response_text,
                agent   = AgentRole.TECHNICAL,
            )

            return {
                "conversation_history": [assistant_msg],
                "retrieved_chunks":     chunks,
                "routing_decision":     routing,
                "current_agent":        AgentRole.TECHNICAL,
            }

        except Exception as e:
            error_msg = Message(
                role    = "assistant",
                content = "I encountered an issue processing your request. Let me escalate this to ensure you get the help you need.",
                agent   = AgentRole.TECHNICAL,
            )
            return {
                "conversation_history": [error_msg],
                "routing_decision":     "escalation",
                "current_agent":        AgentRole.TECHNICAL,
                "error_count":          state.get("error_count", 0) + 1,
            }
