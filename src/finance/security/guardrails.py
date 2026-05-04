"""Input and output guardrails for the finance agent."""

from __future__ import annotations

import re

BLOCKED_PATTERNS = [
    re.compile(r"ignore (all )?(previous|prior) instructions", re.IGNORECASE),
    re.compile(r"reveal .*secret", re.IGNORECASE),
    re.compile(r"api[_ -]?key|token|password", re.IGNORECASE),
]


def validate_agent_input(text: str) -> None:
    """Reject empty, oversized, or clearly malicious agent inputs."""
    if not text.strip():
        raise ValueError("question must not be empty")
    if len(text) > 2_000:
        raise ValueError("question is too long")
    for pattern in BLOCKED_PATTERNS:
        if pattern.search(text):
            raise ValueError("question rejected by security guardrails")


def validate_agent_output(text: str) -> None:
    """Block accidental leakage patterns in generated answers."""
    for pattern in BLOCKED_PATTERNS:
        if pattern.search(text):
            raise ValueError("answer rejected by security guardrails")
