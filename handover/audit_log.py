"""
handover/audit_log.py

Writes every handover event to a structured JSON audit log.
Each line is a valid JSON object (JSON Lines format).

This satisfies the assessment requirement:
"Log every handover event with: timestamp, source agent,
target agent, reason, and context snapshot."
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from agents.state import HandoverEvent

LOGS_DIR  = Path(__file__).parent.parent / "logs"
AUDIT_FILE = LOGS_DIR / "handover_audit.jsonl"


def log_handover(
    trace_id: str,
    event: HandoverEvent,
) -> None:
    """
    Appends a handover event to the audit log.
    Creates the log file and directory if they don't exist.
    """
    os.makedirs(LOGS_DIR, exist_ok=True)

    record = {
        "trace_id":      trace_id,
        "timestamp":     event.timestamp,
        "source_agent":  event.source_agent.value,
        "target_agent":  event.target_agent.value,
        "reason":        event.reason,
        "success":       event.success,
        "entity_snapshot": event.entity_snapshot,
    }

    with open(AUDIT_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")
