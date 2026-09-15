from __future__ import annotations

from project_risk_agent.models import Finding


_LEVEL = {"low": 1, "medium": 2, "high": 3}


def attention_score(finding: Finding) -> float:
    """Return a transparent 0-100 management-attention score."""
    likelihood = _LEVEL.get((finding.likelihood or "medium").lower(), 2)
    impact = _LEVEL.get((finding.impact or "medium").lower(), 2)
    urgency = _LEVEL.get((finding.urgency or "medium").lower(), 2)
    severity = (likelihood + impact + urgency) / 9
    return round(severity * finding.confidence * 100, 1)


def prioritize(findings: list[Finding]) -> list[Finding]:
    """Sort findings by transparent management-attention score."""
    return sorted(findings, key=attention_score, reverse=True)
