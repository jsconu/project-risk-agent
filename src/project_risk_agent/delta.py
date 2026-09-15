from __future__ import annotations

from dataclasses import dataclass

from project_risk_agent.models import Finding


@dataclass(frozen=True)
class FindingDelta:
    """Changes between two analysis snapshots."""

    new: list[Finding]
    continuing: list[Finding]
    resolved: list[Finding]


def compare_findings(previous: list[Finding], current: list[Finding]) -> FindingDelta:
    """Compare findings using their stable IDs.

    A finding is considered continuing when the same evidence-backed finding ID
    appears in both snapshots. Resolved findings are those that disappear from
    the latest analysis; callers can decide how long to retain them.
    """
    previous_by_id = {finding.id: finding for finding in previous}
    current_by_id = {finding.id: finding for finding in current}

    return FindingDelta(
        new=[finding for finding in current if finding.id not in previous_by_id],
        continuing=[finding for finding in current if finding.id in previous_by_id],
        resolved=[finding for finding in previous if finding.id not in current_by_id],
    )
