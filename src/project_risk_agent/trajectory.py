from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from project_risk_agent.delta import FindingDelta
from project_risk_agent.freshness import FindingFreshness
from project_risk_agent.models import Finding, ProjectSignal


@dataclass(frozen=True)
class FindingTrajectory:
    """Longitudinal state of a finding across analysis runs."""

    finding_id: str
    state: str
    attention_direction: str
    freshness: str


def _state(
    finding: Finding,
    delta: FindingDelta,
    freshness: FindingFreshness | None,
) -> str:
    if freshness and freshness.status == "stale":
        return "stale"
    if finding.id in {item.id for item in delta.new}:
        return "new"
    change = next((item for item in delta.changed if item.finding_id == finding.id), None)
    if change:
        if change.attention_direction == "increased":
            return "deteriorating"
        if change.attention_direction == "decreased":
            return "improving"
    return "persistent"


def _confirms_resolution(signal: ProjectSignal, finding: Finding) -> bool:
    """Return whether a current signal explicitly confirms this finding is resolved.

    An omitted finding can mean that source coverage changed rather than that the
    underlying risk disappeared.  Resolution therefore requires a direct link to
    the old finding plus a clear completion/resolution statement.
    """
    linked_ids = signal.metadata.get("resolves_finding_ids", [])
    if isinstance(linked_ids, str):
        linked_ids = [linked_ids]
    explicitly_linked = finding.id in linked_ids or finding.id.lower() in signal.content.lower()
    resolution_words = ("resolved", "closed", "completed", "unblocked", "mitigated")
    return explicitly_linked and any(word in signal.content.lower() for word in resolution_words)


def _resolved_trajectories(
    delta: FindingDelta,
    signals: list[ProjectSignal] | None,
    *,
    now: datetime | None,
) -> list[FindingTrajectory]:
    current_signals = signals or []
    resolved: list[FindingTrajectory] = []
    for finding in delta.resolved:
        confirmations = [signal for signal in current_signals if _confirms_resolution(signal, finding)]
        if not confirmations:
            continue
        freshness = _resolution_freshness(finding.id, confirmations, now=now)
        # A resolution statement that is itself stale is not enough to close a
        # finding in the current analysis.
        if freshness.status == "stale":
            continue
        resolved.append(
            FindingTrajectory(
                finding_id=finding.id,
                state="resolved",
                attention_direction="decreased",
                freshness=freshness.status,
            )
        )
    return resolved


def _resolution_freshness(
    finding_id: str,
    signals: list[ProjectSignal],
    *,
    now: datetime | None,
) -> FindingFreshness:
    """Classify the age of direct resolution evidence."""
    reference = now or datetime.now(UTC)
    latest = max(signal.timestamp for signal in signals)
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=UTC)
    age_days = max(0.0, (reference - latest).total_seconds() / 86400)
    status = "stale" if age_days >= 7 else "aging" if age_days >= 3 else "fresh"
    return FindingFreshness(finding_id=finding_id, age_days=age_days, status=status)


def trajectories(
    findings: list[Finding],
    delta: FindingDelta | None,
    freshness: list[FindingFreshness] | None,
    signals: list[ProjectSignal] | None = None,
    *,
    now: datetime | None = None,
) -> list[FindingTrajectory]:
    """Classify current findings using longitudinal deltas and evidence freshness."""
    effective_delta = delta or FindingDelta(new=findings, continuing=[], resolved=[], changed=[])
    freshness_by_id = {item.finding_id: item for item in freshness or []}
    active = [
        FindingTrajectory(
            finding_id=finding.id,
            state=_state(finding, effective_delta, freshness_by_id.get(finding.id)),
            attention_direction=next(
                (
                    change.attention_direction
                    for change in effective_delta.changed
                    if change.finding_id == finding.id
                ),
                "unchanged",
            ),
            freshness=freshness_by_id.get(finding.id).status if finding.id in freshness_by_id else "unknown",
        )
        for finding in findings
    ]
    return active + _resolved_trajectories(effective_delta, signals, now=now)
