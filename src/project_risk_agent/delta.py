from __future__ import annotations

from dataclasses import dataclass

from project_risk_agent.models import Finding
from project_risk_agent.prioritizer import attention_score


@dataclass(frozen=True)
class FindingChange:
    """A material change to a finding that persists across analysis runs."""

    finding_id: str
    changed_fields: tuple[str, ...]
    previous_attention: float
    current_attention: float

    @property
    def attention_direction(self) -> str:
        if self.current_attention > self.previous_attention:
            return "increased"
        if self.current_attention < self.previous_attention:
            return "decreased"
        return "unchanged"


@dataclass(frozen=True)
class FindingDelta:
    """Changes between two analysis snapshots."""

    new: list[Finding]
    continuing: list[Finding]
    resolved: list[Finding]
    changed: list[FindingChange]


def _changed_fields(previous: Finding, current: Finding) -> tuple[str, ...]:
    fields = (
        "title",
        "description",
        "likelihood",
        "impact",
        "urgency",
        "confidence",
        "owner",
        "decision_required",
        "decision_owner",
        "recommended_actions",
    )
    return tuple(field for field in fields if getattr(previous, field) != getattr(current, field))


def compare_findings(previous: list[Finding], current: list[Finding]) -> FindingDelta:
    """Compare findings using stable IDs and detect material changes."""
    previous_by_id = {finding.id: finding for finding in previous}
    current_by_id = {finding.id: finding for finding in current}

    changed = []
    for finding in current:
        prior = previous_by_id.get(finding.id)
        if prior is None:
            continue
        fields = _changed_fields(prior, finding)
        if fields:
            changed.append(
                FindingChange(
                    finding_id=finding.id,
                    changed_fields=fields,
                    previous_attention=attention_score(prior),
                    current_attention=attention_score(finding),
                )
            )

    return FindingDelta(
        new=[finding for finding in current if finding.id not in previous_by_id],
        continuing=[finding for finding in current if finding.id in previous_by_id],
        resolved=[finding for finding in previous if finding.id not in current_by_id],
        changed=changed,
    )
