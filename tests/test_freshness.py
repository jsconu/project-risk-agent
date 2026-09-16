from datetime import UTC, datetime, timedelta

from project_risk_agent.freshness import finding_freshness
from project_risk_agent.models import Evidence, Finding, FindingType, ProjectSignal, RiskCategory


NOW = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)


def make_finding() -> Finding:
    return Finding(
        id="f1",
        type=FindingType.RISK,
        category=RiskCategory.SCHEDULE,
        title="Schedule concern",
        description="A schedule concern",
        evidence=[Evidence(signal_id="s1", excerpt="Delayed", rationale="Test")],
    )


def test_freshness_uses_latest_supporting_signal():
    finding = make_finding()
    signals = [
        ProjectSignal(id="s1", source="test", source_type="status", timestamp=NOW - timedelta(days=6), content="Delayed"),
    ]

    result = finding_freshness(finding, signals, now=NOW)

    assert result.age_days == 6
    assert result.status == "aging"


def test_freshness_marks_old_evidence_stale():
    finding = make_finding()
    signals = [
        ProjectSignal(id="s1", source="test", source_type="status", timestamp=NOW - timedelta(days=8), content="Delayed"),
    ]

    result = finding_freshness(finding, signals, now=NOW)

    assert result.status == "stale"


def test_freshness_is_unknown_when_evidence_signal_is_missing():
    result = finding_freshness(make_finding(), [], now=NOW)

    assert result.age_days is None
    assert result.status == "unknown"
