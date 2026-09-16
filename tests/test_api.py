from datetime import UTC, datetime

from project_risk_agent.api import create_app
from project_risk_agent.models import ProjectSignal


def test_api_exposes_health_and_brief():
    from fastapi.testclient import TestClient

    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    payload = {
        "signals": [
            ProjectSignal(
                id="s1",
                source="test",
                source_type="text",
                timestamp=datetime.now(UTC).isoformat(),
                content="The launch is delayed by two days.",
            ).model_dump(mode="json")
        ]
    }
    response = client.post("/brief", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["signals_analyzed"] == 1
    assert "# Project Risk Brief" in body["markdown"]
    assert body["findings"][0]["category"] == "schedule"


def test_api_allows_local_demo_origin():
    from fastapi.testclient import TestClient

    client = TestClient(create_app())
    response = client.options(
        "/analyze",
        headers={
            "Origin": "http://127.0.0.1:8001",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:8001"
