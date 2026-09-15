from __future__ import annotations

import re
from datetime import datetime

from project_risk_agent.models import ProjectSignal


DATE_MOVE = re.compile(
    r"\b(?:moved|shifted|pushed|slipped)\b.*?\b(?:from\s+)?(.+?)\s+to\s+(.+?)(?:[.!?]|$)",
    re.IGNORECASE,
)
CHANGE_WORDS = re.compile(
    r"\b(?:delayed|slipped|pushed|moved|shifted|changed|second|another|again|still)\b",
    re.IGNORECASE,
)


def signal_sequence(signals: list[ProjectSignal]) -> list[ProjectSignal]:
    """Return signals in chronological order without mutating the caller's list."""
    return sorted(signals, key=lambda signal: signal.timestamp)


def change_count(signals: list[ProjectSignal]) -> int:
    """Count signals that describe a schedule/status change."""
    return sum(bool(CHANGE_WORDS.search(signal.content)) for signal in signals)


def has_repeated_change(signals: list[ProjectSignal]) -> bool:
    """Detect repeated change language across a project history."""
    return change_count(signals) >= 2


def extract_date_move(signal: ProjectSignal) -> tuple[str, str] | None:
    """Extract a best-effort textual from/to pair from a schedule update."""
    match = DATE_MOVE.search(signal.content)
    if not match:
        return None
    start = re.sub(r"^from\s+", "", match.group(1).strip(), flags=re.IGNORECASE)
    return start, match.group(2).strip()


def age_days(signal: ProjectSignal, now: datetime) -> int:
    """Return whole days since a signal was observed."""
    return max(0, (now - signal.timestamp).days)
