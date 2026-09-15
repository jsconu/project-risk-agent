from datetime import UTC, datetime

from project_risk_agent.models import Finding, FindingType, ProjectSignal, RiskCategory
from project_risk_agent.state import JsonProjectStateStore, ProjectSnapshot


def test_json_state_round_trip(tmp_path):
    store = JsonProjectStateStore(tmp_path / "state.json")
    signal = ProjectSignal(
        id="s1",
        source="test",
        source_type="text",
        timestamp=datetime(2026, 9, 15, tzinfo=UTC),
        content="The launch date moved.",
    )
    finding = Finding(
        id="f1",
        type=FindingType.RISK,
        category=RiskCategory.SCHEDULE,
        title="Schedule movement",
        description="The launch date moved.",
        confidence=0.8,
    )

    store.save(ProjectSnapshot(signals=[signal], findings=[finding]))
    restored = store.load()

    assert restored is not None
    assert restored.signals[0] == signal
    assert restored.findings[0] == finding


def test_missing_state_returns_none(tmp_path):
    assert JsonProjectStateStore(tmp_path / "missing.json").load() is None
