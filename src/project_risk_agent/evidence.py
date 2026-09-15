from __future__ import annotations

from collections.abc import Callable

from project_risk_agent.models import Evidence, ProjectSignal


def deduplicate_evidence(evidence: list[Evidence]) -> list[Evidence]:
    """Remove duplicate signal/excerpt pairs while preserving order."""
    seen: set[tuple[str, str]] = set()
    result: list[Evidence] = []
    for item in evidence:
        key = (item.signal_id, item.excerpt)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def evidence_for_signals(
    signals: list[ProjectSignal],
    predicate: Callable[[ProjectSignal], bool],
    rationale: str,
    excerpt_limit: int = 500,
) -> list[Evidence]:
    """Build grounded evidence from signals matching a supplied predicate."""
    return deduplicate_evidence(
        [
            Evidence(
                signal_id=signal.id,
                excerpt=signal.content.strip()[:excerpt_limit],
                rationale=rationale,
            )
            for signal in signals
            if predicate(signal)
        ]
    )
