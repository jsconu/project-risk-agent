from datetime import UTC

from project_risk_agent.connectors.webhook import WebhookConnector


def test_webhook_generated_id_is_deterministic():
    connector = WebhookConnector()
    first = connector.normalize({"content": "A delivery date moved."})
    second = connector.normalize({"content": "A delivery date moved."})
    assert first.id == second.id
    assert first.provenance["connector"] == "webhook"


def test_webhook_normalizes_zulu_timestamp():
    signal = WebhookConnector().normalize({
        "id": "event-1",
        "content": "Update",
        "timestamp": "2026-09-15T12:00:00Z",
    })
    assert signal.timestamp.tzinfo == UTC
