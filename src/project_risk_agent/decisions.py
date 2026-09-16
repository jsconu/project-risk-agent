from __future__ import annotations

import re
from dataclasses import dataclass

from project_risk_agent.models import ProjectSignal


@dataclass(frozen=True)
class DecisionRequest:
    """A human decision request extracted from project signals."""

    signal_id: str
    description: str
    owner: str | None = None
    deadline: str | None = None
    readiness: str = "missing_owner_and_deadline"


OWNER_PATTERN = re.compile(r"\b(?:sponsor|owner|leadership|leader|manager|team)\b", re.IGNORECASE)
DEADLINE_PATTERN = re.compile(
    r"\b(?:by|before|no later than)\s+((?:today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)|\w+\s+\d{1,2})\b",
    re.IGNORECASE,
)
DECISION_PATTERN = re.compile(r"\b(?:decision|decide|approval|approve|choose|sign[- ]off)\b", re.IGNORECASE)


def extract_decision_requests(signals: list[ProjectSignal]) -> list[DecisionRequest]:
    """Extract explicit decision requests while preserving source provenance."""
    requests: list[DecisionRequest] = []
    for signal in signals:
        if not DECISION_PATTERN.search(signal.content):
            continue
        owner_match = OWNER_PATTERN.search(signal.content)
        deadline_match = DEADLINE_PATTERN.search(signal.content)
        owner = owner_match.group(0) if owner_match else None
        deadline = deadline_match.group(1) if deadline_match else None
        requests.append(
            DecisionRequest(
                signal_id=signal.id,
                description=signal.content.strip()[:500],
                owner=owner,
                deadline=deadline,
                readiness=_readiness(owner, deadline),
            )
        )
    return requests


def _readiness(owner: str | None, deadline: str | None) -> str:
    """Describe whether an explicit decision request is actionable."""
    if owner and deadline:
        return "ready"
    if owner:
        return "missing_deadline"
    if deadline:
        return "missing_owner"
    return "missing_owner_and_deadline"
