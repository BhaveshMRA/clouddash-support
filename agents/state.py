from __future__ import annotations
from datetime import datetime
from enum import Enum
from operator import add
from typing import Annotated, Optional, TypedDict
from pydantic import BaseModel, Field

class AgentRole(str, Enum):
    TRIAGE     = "triage"
    TECHNICAL  = "technical"
    BILLING    = "billing"
    ESCALATION = "escalation"

class Intent(str, Enum):
    TECHNICAL = "technical"
    BILLING   = "billing"
    ACCOUNT   = "account"
    GENERAL   = "general"
    ESCALATE  = "escalate"
    RESOLVED  = "resolved"
    UNKNOWN   = "unknown"

class Sentiment(str, Enum):
    NEUTRAL    = "neutral"
    FRUSTRATED = "frustrated"
    URGENT     = "urgent"

class Priority(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"

class Message(BaseModel):
    role: str
    content: str
    agent: Optional[AgentRole] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ExtractedEntities(BaseModel):
    customer_id: Optional[str]    = None
    intent: Intent                = Intent.UNKNOWN
    product_references: list[str] = Field(default_factory=list)
    sentiment: Sentiment          = Sentiment.NEUTRAL
    plan_type: Optional[str]      = None
    raw_issue: Optional[str]      = None

class RetrievedChunk(BaseModel):
    kb_id: str
    title: str
    content: str
    score: float
    category: str

class HandoverEvent(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    source_agent: AgentRole
    target_agent: AgentRole
    reason: str
    entity_snapshot: dict
    success: bool = True

class HumanEscalationPayload(BaseModel):
    trace_id: str
    customer_id: Optional[str]
    priority: Priority
    sentiment: Sentiment
    issue_summary: str
    conversation_summary: str
    recommended_action: str
    full_history_ref: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class SupportState(TypedDict):
    trace_id:             str
    conversation_history: Annotated[list[Message], add]
    extracted_entities:   ExtractedEntities
    current_agent:        AgentRole
    handover_log:         Annotated[list[HandoverEvent], add]
    retrieved_chunks:     list[RetrievedChunk]
    awaiting_human:       bool
    routing_decision:     Optional[str]
    error_count:          int
    escalation_payload:   Optional[HumanEscalationPayload]
