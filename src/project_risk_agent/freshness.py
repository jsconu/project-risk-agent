from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from project_risk_agent.models import Finding, ProjectSignal


@dataclass(frozen=True)
class FindingFreshness:
    """Current age of the evidence supporting a finding."""

    finding_id: str
    age_days: float | None
    status: str


def latest_evidence_timestamp(finding: Finding, signals: list[ProjectSignal]) -> datetime | None:
    """Return the newest timestamp among signals cited by the finding."""
    by_id = {signal.id: signal for signal in signals}
    timestamps = [by_id[item.signal_id].timestamp for item in finding.evidence if item.signal_id in by_id]
    return max(timestamps) if timestamps else None


def finding_freshness(
    finding: Finding,
    signals: list[ProjectSignal],
    *,
    now: datetime | None = None,
    aging_after_days: float = 3,
    stale_after_days: float = 7,
) -> FindingFreshness:
    """Classify evidence as fresh, aging, or stale without changing the finding itself."""
    now = now or datetime.now(UTC)
    timestamp = latest_evidence_timestamp(finding, signals)
    if timestamp is None:
        return FindingFreshness(finding_id=finding.id, age_days=None, status="unknown")
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    age_days = max(0.0, (now - timestamp).total_seconds() / 86400)
    if age_days >= stale_after_days:
        status = "stale"
    elif age_days >= aging_after_days:
        status = "aging"
    else:
        status = "fresh"
    return FindingFreshness(finding_id=finding.id, age_days=age_days, status=status)


def freshness_for_findings(
    findings: list[Finding],
    signals: list[ProjectSignal],
    *,
    now: datetime | None = None,
    aging_after_days: float = 3,
    stale_after_days: float = 7,
) -> list[FindingFreshness]:
    return [
        finding_freshness(
            finding,
            signals,
            now=now,
            aging_after_days=aging_after_days,
            stale_after_days=stale_after_days,
        )
        for finding in findings
    ]
