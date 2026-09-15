from datetime import UTC, datetime, timedelta

from project_risk_agent.models import ProjectSignal
from project_risk_agent.temporal import (
    age_days,
    extract_date_move,
    has_repeated_change,
    signal_sequence,
)


def signal(content: str, signal_id: str, days_ago: int = 0) -> ProjectSignal:
    return ProjectSignal(
        id=signal_id,
        source="test",
        source_type="text",
        timestamp=datetime.now(UTC) - timedelta(days=days_ago),
        content=content,
    )


def test_sequence_is_chronological():
    result = signal_sequence([signal("later", "2", 1), signal("earlier", "1", 3)])
    assert [item.id for item in result] == ["1", "2"]


def test_repeated_change_is_detected():
    signals = [signal("Date moved to Friday.", "1"), signal("Launch slipped again.", "2")]
    assert has_repeated_change(signals)


def test_date_move_is_best_effort():
    result = extract_date_move(signal("The delivery moved from Tuesday to Friday.", "1"))
    assert result == ("Tuesday", "Friday")


def test_age_days_is_non_negative():
    assert age_days(signal("old", "1", 4), datetime.now(UTC)) >= 4
