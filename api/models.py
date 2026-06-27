"""
api/models.py

Pydantic request/response models for the FastAPI layer.
Separate from agents/state.py — these are API contracts,
not internal graph state.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StartConversationRequest(BaseModel):
    message: str


class StartConversationResponse(BaseModel):
    trace_id:       str
    response:       str
    agent:          str
    awaiting_human: bool


class SendMessageRequest(BaseModel):
    message: str


class SendMessageResponse(BaseModel):
    trace_id:       str
    response:       str
    agent:          str
    awaiting_human: bool
    kb_sources:     list[str]


class MessageRecord(BaseModel):
    role:      str
    content:   str
    agent:     Optional[str]
    timestamp: str


class ConversationHistoryResponse(BaseModel):
    trace_id:       str
    messages:       list[MessageRecord]
    handover_count: int
    awaiting_human: bool


class ErrorResponse(BaseModel):
    error:   str
    detail:  str
    trace_id: Optional[str] = None
