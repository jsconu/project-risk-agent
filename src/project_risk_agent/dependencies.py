from __future__ import annotations

from dataclasses import dataclass

from project_risk_agent.models import Finding, FindingType


@dataclass(frozen=True)
class DependencyItem:
    """A separately reviewable dependency derived from an evidence-backed finding."""

    finding_id: str
    title: str
    status: str
    evidence_signal_ids: list[str]
    owner: str | None
    required_by: str | None


def dependency_items(findings: list[Finding]) -> list[DependencyItem]:
    """Extract dependency status without changing the core Finding contract."""
    return [
        DependencyItem(
            finding_id=finding.id,
            title=finding.title,
            status=_status(finding),
            evidence_signal_ids=[evidence.signal_id for evidence in finding.evidence],
            owner=finding.owner,
            required_by=finding.decision_deadline,
        )
        for finding in findings
        if finding.type == FindingType.DEPENDENCY
    ]


def _status(finding: Finding) -> str:
    text = f"{finding.title} {finding.description}".lower()
    if any(phrase in text for phrase in ("blocked", "cannot start", "can't start", "unavailable")):
        return "blocked"
    if any(phrase in text for phrase in ("waiting", "depends on", "until ")):
        return "waiting"
    return "at_risk"
