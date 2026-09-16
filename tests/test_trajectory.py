from datetime import UTC, datetime, timedelta

from project_risk_agent.delta import compare_findings
from project_risk_agent.freshness import freshness_for_findings
from project_risk_agent.models import Evidence, Finding, FindingType, ProjectSignal, RiskCategory
from project_risk_agent.trajectory import trajectories


NOW = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)


def finding(identifier: str, *, impact: str = "medium") -> Finding:
    return Finding(
        id=identifier,
        type=FindingType.RISK,
        category=RiskCategory.SCHEDULE,
        title=identifier,
        description=identifier,
        impact=impact,
        confidence=0.8,
        evidence=[Evidence(signal_id="s1", excerpt="schedule", rationale="test")],
    )


def test_new_finding_is_new():
    current = [finding("a")]
    signal = ProjectSignal(id="s1", source="test", source_type="status", timestamp=NOW, content="schedule")
    delta = compare_findings([], current)
    freshness = freshness_for_findings(current, [signal], now=NOW)

    result = trajectories(current, delta, freshness)

    assert result[0].state == "new"
    assert result[0].freshness == "fresh"


def test_material_attention_increase_is_deteriorating():
    previous = [finding("a")]
    current = [finding("a", impact="high")]
    signal = ProjectSignal(id="s1", source="test", source_type="status", timestamp=NOW, content="schedule")

    delta = compare_findings(previous, current)
    freshness = freshness_for_findings(current, [signal], now=NOW)

    result = trajectories(current, delta, freshness)

    assert result[0].state == "deteriorating"
    assert result[0].attention_direction == "increased"


def test_material_attention_decrease_is_improving():
    previous = [finding("a", impact="high")]
    current = [finding("a")]
    signal = ProjectSignal(id="s1", source="test", source_type="status", timestamp=NOW, content="schedule")

    delta = compare_findings(previous, current)
    freshness = freshness_for_findings(current, [signal], now=NOW)

    result = trajectories(current, delta, freshness)

    assert result[0].state == "improving"
    assert result[0].attention_direction == "decreased"


def test_unchanged_fresh_finding_is_persistent():
    current = [finding("a")]
    signal = ProjectSignal(id="s1", source="test", source_type="status", timestamp=NOW, content="schedule")
    delta = compare_findings(current, current)
    freshness = freshness_for_findings(current, [signal], now=NOW)

    result = trajectories(current, delta, freshness)

    assert result[0].state == "persistent"


def test_old_persistent_finding_is_stale():
    current = [finding("a")]
    signal = ProjectSignal(
        id="s1", source="test", source_type="status", timestamp=NOW - timedelta(days=8), content="schedule"
    )
    delta = compare_findings(current, current)
    freshness = freshness_for_findings(current, [signal], now=NOW)

    result = trajectories(current, delta, freshness)

    assert result[0].state == "stale"
    assert result[0].freshness == "stale"


def test_absent_finding_is_not_resolved_without_explicit_confirmation():
    previous = [finding("a")]
    delta = compare_findings(previous, [])
    signal = ProjectSignal(id="s2", source="test", source_type="status", timestamp=NOW, content="Status update")

    result = trajectories([], delta, [], [signal], now=NOW)

    assert result == []


def test_explicit_fresh_resolution_is_reported():
    previous = [finding("a")]
    delta = compare_findings(previous, [])
    signal = ProjectSignal(
        id="s2",
        source="test",
        source_type="status",
        timestamp=NOW,
        content="Finding a is resolved and the schedule is unblocked.",
    )

    result = trajectories([], delta, [], [signal], now=NOW)

    assert [(item.finding_id, item.state, item.freshness) for item in result] == [("a", "resolved", "fresh")]


def test_stale_resolution_confirmation_does_not_close_finding():
    previous = [finding("a")]
    delta = compare_findings(previous, [])
    signal = ProjectSignal(
        id="s2",
        source="test",
        source_type="status",
        timestamp=NOW - timedelta(days=8),
        content="Finding a is resolved.",
    )

    result = trajectories([], delta, [], [signal], now=NOW)

    assert result == []
