from datetime import UTC

from project_risk_agent.connectors.slack import SlackConnector


def test_normalize_slack_message_preserves_provenance():
    signal = SlackConnector.normalize(
        {"ts": "1767225600.000100", "user": "U123", "text": "API is delayed", "thread_ts": "1.0"},
        "C123",
    )
    assert signal.source == "slack"
    assert signal.project_id == "C123"
    assert signal.author == "U123"
    assert signal.content == "API is delayed"
    assert signal.provenance["conversation_id"] == "C123"
    assert signal.timestamp.tzinfo == UTC
