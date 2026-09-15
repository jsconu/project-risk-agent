from project_risk_agent.decisions import extract_decision_requests
from project_risk_agent.models import ProjectSignal


def test_extract_decision_request_owner_and_deadline():
    signal = ProjectSignal(
        id="s1",
        source="meeting",
        source_type="transcript",
        timestamp="2026-01-01T00:00:00Z",
        content="We need the sponsor to decide whether to move launch by Friday.",
    )
    result = extract_decision_requests([signal])
    assert result[0].owner == "sponsor"
    assert result[0].deadline == "Friday"


def test_non_decision_signal_is_ignored():
    signal = ProjectSignal(
        id="s1",
        source="meeting",
        source_type="transcript",
        timestamp="2026-01-01T00:00:00Z",
        content="The team completed testing.",
    )
    assert extract_decision_requests([signal]) == []
