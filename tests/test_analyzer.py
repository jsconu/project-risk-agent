from datetime import UTC, datetime

from project_risk_agent.analyzer import RiskAnalyzer
from project_risk_agent.models import FindingType, ProjectSignal


def signal(content: str, signal_id: str = "s1") -> ProjectSignal:
    return ProjectSignal(
        id=signal_id,
        source="test",
        source_type="text",
        timestamp=datetime.now(UTC),
        content=content,
    )


def test_explicit_schedule_risk_produces_evidence_backed_finding():
    findings = RiskAnalyzer().analyze(
        [signal("Integration testing is at risk because the API is delayed.")]
    )

    assert len(findings) == 1
    assert findings[0].type == FindingType.RISK
    assert findings[0].evidence[0].signal_id == "s1"
    assert "delayed" in findings[0].evidence[0].excerpt.lower()


def test_normal_update_does_not_create_risk():
    findings = RiskAnalyzer().analyze(
        [signal("The team completed the design review on Tuesday.")]
    )
    assert findings == []
