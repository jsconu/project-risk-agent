from datetime import UTC, datetime, timedelta

from project_risk_agent.analysis import SignalReasoner
from project_risk_agent.models import ProjectSignal, RiskCategory


def signal(content: str, signal_id: str, days_ago: int) -> ProjectSignal:
    return ProjectSignal(
        id=signal_id,
        source="test",
        source_type="status",
        timestamp=datetime.now(UTC) - timedelta(days=days_ago),
        content=content,
    )


def test_recurring_concern_increases_confidence_and_likelihood():
    signals = [
        signal("The vendor delivery is delayed.", "s1", 6),
        signal("The vendor delivery is still delayed.", "s2", 4),
        signal("The vendor delivery slipped again.", "s3", 1),
    ]

    findings = SignalReasoner().analyze(signals)
    vendor = next(f for f in findings if f.category == RiskCategory.SCHEDULE)

    assert vendor.likelihood == "high"
    assert vendor.confidence >= 0.9
    assert len(vendor.evidence) == 3
    assert "Recurring across 3 project signals" in vendor.description
    assert any("underlying cause" in action for action in vendor.recommended_actions)
