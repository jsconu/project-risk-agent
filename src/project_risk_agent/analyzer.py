from __future__ import annotations

from hashlib import sha256

from project_risk_agent.models import Evidence, Finding, FindingType, ProjectSignal, RiskCategory


class RiskAnalyzer:
    """Core reasoning boundary for the risk agent.

    The analyzer deliberately requires evidence to be attached to findings.
    A model-backed implementation can be added behind this interface without
    changing connectors or downstream consumers.
    """

    def analyze(self, signals: list[ProjectSignal]) -> list[Finding]:
        """Analyze normalized project signals.

        This deterministic starter implementation demonstrates the contract
        and catches explicit risk language. Future model-backed reasoning can
        add inferred risks while preserving the same evidence requirements.
        """
        findings: list[Finding] = []
        risk_terms = ("at risk", "blocked", "slip", "slipping", "delayed", "delay", "cannot start")

        for signal in signals:
            text = signal.content.strip()
            lowered = text.lower()
            if not any(term in lowered for term in risk_terms):
                continue

            evidence = Evidence(
                signal_id=signal.id,
                excerpt=text[:500],
                rationale="Signal contains explicit risk or delivery-risk language.",
            )
            finding_id = "risk-" + sha256(signal.id.encode()).hexdigest()[:12]
            findings.append(
                Finding(
                    id=finding_id,
                    type=FindingType.RISK,
                    category=RiskCategory.SCHEDULE,
                    title="Potential delivery risk detected",
                    description=text[:500],
                    confidence=0.65,
                    evidence=[evidence],
                )
            )

        return findings
