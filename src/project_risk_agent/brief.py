from __future__ import annotations

from project_risk_agent.models import Finding


def management_brief(findings: list[Finding]) -> str:
    """Render findings as a concise, human-reviewable management brief."""
    if not findings:
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
    return "\n".join(lines)
