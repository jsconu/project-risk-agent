from __future__ import annotations

from dataclasses import dataclass

from project_risk_agent.delta import FindingDelta
from project_risk_agent.freshness import FindingFreshness
from project_risk_agent.models import Finding


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
    if finding.id in {item.id for item in delta.new}:
        return "new"
    if freshness and freshness.status == "stale":
        return "stale"
    change = next((item for item in delta.changed if item.finding_id == finding.id), None)
    if change:
        if change.attention_direction == "increased":
            return "deteriorating"
        if change.attention_direction == "decreased":
            return "improving"
    return "persistent"


def trajectories(
    findings: list[Finding],
    delta: FindingDelta | None,
    freshness: list[FindingFreshness] | None,
) -> list[FindingTrajectory]:
    """Classify current findings using longitudinal deltas and evidence freshness."""
    effective_delta = delta or FindingDelta(new=findings, continuing=[], resolved=[], changed=[])
    freshness_by_id = {item.finding_id: item for item in freshness or []}
    return [
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
