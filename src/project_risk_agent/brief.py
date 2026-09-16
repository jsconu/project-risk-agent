from __future__ import annotations

from project_risk_agent.decisions import DecisionRequest
from project_risk_agent.models import Finding


def management_brief(
    findings: list[Finding], decision_requests: list[DecisionRequest] | None = None
) -> str:
    """Render findings as a concise, human-reviewable management brief."""
    if not findings and not decision_requests:
        return "No management-relevant findings detected."

    lines = ["# Project Risk Brief", ""]
    for index, finding in enumerate(findings, start=1):
        lines.extend([
            f"## {index}. {finding.title}",
            f"**Type:** {finding.type.value}  **Category:** {finding.category.value}",
            f"**Confidence:** {finding.confidence:.0%}",
            "",
            finding.description,
            "",
            "### Evidence",
        ])
        for evidence in finding.evidence:
            lines.append(f"- `{evidence.signal_id}` — {evidence.excerpt}")
        if finding.recommended_actions:
            lines.extend(["", "### Suggested next actions"])
            lines.extend(f"- {action}" for action in finding.recommended_actions)
        if finding.decision_required:
            lines.extend(["", "**Management decision required:** Yes"])
        lines.append("")
    if decision_requests:
        lines.extend(["## Decision queue", ""])
        for request in decision_requests:
            details = [f"**Readiness:** {request.readiness.replace('_', ' ')}"]
            if request.owner:
                details.append(f"**Owner:** {request.owner}")
            if request.deadline:
                details.append(f"**Deadline:** {request.deadline}")
            lines.extend([f"- `{request.signal_id}` — {request.description}", "  " + "  ".join(details)])
        lines.append("")
    return "\n".join(lines)
