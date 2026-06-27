"""
retrieval/guardrails.py

Input and output guardrails.

Input guardrail  — blocks prompt injection and off-topic queries
Output guardrail — checks agent responses are grounded in KB
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

SETTINGS_PATH = Path(__file__).parent.parent / "config" / "settings.yaml"
with open(SETTINGS_PATH) as f:
    _settings = yaml.safe_load(f)

INJECTION_PATTERNS: list[str] = _settings["guardrails"]["injection_patterns"]
MAX_INPUT_LENGTH:   int       = _settings["guardrails"]["max_input_length"]

# Off-topic signals — queries with no CloudDash relevance
OFF_TOPIC_PATTERNS = [
    r"\b(weather|sports|recipe|movie|music|song|celebrity)\b",
    r"\b(stock price|bitcoin|crypto|forex)\b",
    r"\b(write me a (poem|story|essay|joke))\b",
]


def check_input(message: str) -> dict:
    """
    Input guardrail. Returns:
        {"allowed": True}
        {"allowed": False, "reason": "..."}
    """
    # 1. Length check
    if len(message) > MAX_INPUT_LENGTH:
        return {
            "allowed": False,
            "reason":  f"Message too long ({len(message)} chars). Maximum is {MAX_INPUT_LENGTH}.",
        }

    msg_lower = message.lower()

    # 2. Prompt injection detection
    for pattern in INJECTION_PATTERNS:
        if pattern.lower() in msg_lower:
            return {
                "allowed": False,
                "reason":  "Message contains content that cannot be processed.",
            }

    # 3. Off-topic detection
    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, msg_lower):
            return {
                "allowed": False,
                "reason":  (
                    "I can only help with CloudDash-related questions — "
                    "technical issues, billing, account management, or "
                    "general product questions."
                ),
            }

    return {"allowed": True}


def check_output_grounded(
    response: str,
    chunks: list,
) -> dict:
    """
    Output guardrail. Checks whether the response is grounded
    in the retrieved KB chunks.

    If no chunks were retrieved but the response makes specific
    claims about CloudDash features, flag it.

    Returns:
        {"grounded": True}
        {"grounded": False, "reason": "..."}
    """
    if not chunks:
        # No KB context — check if response makes specific feature claims
        specific_claim_patterns = [
            r"\$\d+",           # price mentions
            r"settings\s*>",    # navigation paths
            r"api\.clouddash",  # specific URLs
        ]
        for pattern in specific_claim_patterns:
            if re.search(pattern, response.lower()):
                return {
                    "grounded": False,
                    "reason":   "Response makes specific claims without KB support.",
                }

    return {"grounded": True}
