"""Unit tests for agent logic."""
import pytest
from agents.state import (
    AgentRole, ExtractedEntities, Intent,
    Message, Sentiment, SupportState
)
from agents.triage_agent import TriageAgent
from agents.billing_agent import BillingAgent
from agents.escalation_agent import EscalationAgent


def make_state(message: str) -> SupportState:
    return {
        "trace_id":             "test-trace-001",
        "conversation_history": [Message(role="user", content=message)],
        "extracted_entities":   ExtractedEntities(),
        "current_agent":        AgentRole.TRIAGE,
        "handover_log":         [],
        "retrieved_chunks":     [],
        "awaiting_human":       False,
        "routing_decision":     None,
        "error_count":          0,
        "escalation_payload":   None,
    }


# ── Triage tests ───────────────────────────────────────────────────────────────

def test_triage_routes_technical_issue():
    agent  = TriageAgent()
    state  = make_state("My AWS CloudWatch integration is failing")
    result = agent.run(state)
    assert result["routing_decision"] == "technical"


def test_triage_routes_billing_issue():
    agent  = TriageAgent()
    state  = make_state("I have a question about my invoice this month")
    result = agent.run(state)
    assert result["routing_decision"] == "billing"


def test_triage_routes_escalation_on_manager_request():
    agent  = TriageAgent()
    state  = make_state("I want to speak to a manager immediately")
    result = agent.run(state)
    assert result["routing_decision"] == "escalation"


def test_triage_sets_extracted_entities():
    agent  = TriageAgent()
    state  = make_state("My Pro plan alerts are broken")
    result = agent.run(state)
    assert result["extracted_entities"] is not None
    assert result["extracted_entities"].intent != Intent.UNKNOWN


# ── Billing tests ──────────────────────────────────────────────────────────────

def test_billing_escalates_on_duplicate_charge():
    agent = BillingAgent()
    state = make_state("I was charged twice for April")
    state["extracted_entities"] = ExtractedEntities(
        intent    = Intent.BILLING,
        sentiment = Sentiment.FRUSTRATED,
    )
    result = agent.run(state)
    assert result["routing_decision"] == "escalation"


def test_billing_escalates_on_manager_request():
    agent = BillingAgent()
    state = make_state("I need to speak to a manager about my bill")
    state["extracted_entities"] = ExtractedEntities(intent=Intent.BILLING)
    result = agent.run(state)
    assert result["routing_decision"] == "escalation"


def test_billing_looks_up_known_account():
    agent = BillingAgent()
    account = agent._lookup_account("CUST-1234")
    assert account is not None
    assert account["plan"] == "Pro"


def test_billing_returns_none_for_unknown_account():
    agent   = BillingAgent()
    account = agent._lookup_account("CUST-9999")
    assert account is None


# ── Escalation tests ───────────────────────────────────────────────────────────

def test_escalation_sets_awaiting_human():
    agent = EscalationAgent()
    state = make_state("I need help urgently")
    state["extracted_entities"] = ExtractedEntities(
        intent    = Intent.ESCALATE,
        sentiment = Sentiment.URGENT,
        raw_issue = "Customer needs urgent help",
    )
    result = agent.run(state)
    assert result["awaiting_human"] is True


def test_escalation_classifies_high_priority_for_frustrated_customer():
    agent    = EscalationAgent()
    entities = ExtractedEntities(
        sentiment = Sentiment.FRUSTRATED,
        raw_issue = "Duplicate charge on account",
    )
    history  = [
        Message(role="user",      content="I was charged twice and want a refund"),
        Message(role="assistant", content="Let me help with that"),
    ]
    priority = agent._classify_priority(entities, history)
    from agents.state import Priority
    assert priority == Priority.HIGH


def test_escalation_creates_payload_with_trace_id():
    agent = EscalationAgent()
    state = make_state("urgent issue")
    state["extracted_entities"] = ExtractedEntities(
        sentiment = Sentiment.URGENT,
        raw_issue = "Test issue",
    )
    result = agent.run(state)
    assert result["escalation_payload"] is not None
    assert result["escalation_payload"].trace_id == "test-trace-001"
