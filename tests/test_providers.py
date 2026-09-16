import pytest

from datetime import UTC, datetime

from project_risk_agent.models import FindingType, ProjectSignal, RiskCategory
from project_risk_agent.providers import OpenAIResponsesProvider, build_reasoning_prompt, parse_model_findings


def valid_payload():
    return [{
        "id": "f1",
        "type": "risk",
        "category": "schedule",
        "title": "Schedule concern",
        "description": "A delivery date moved.",
        "confidence": 0.8,
        "evidence": [{"signal_id": "s1", "excerpt": "Date moved"}],
    }]


def test_parse_model_findings_validates_domain_schema():
    result = parse_model_findings(valid_payload())
    assert result[0].type == FindingType.RISK
    assert result[0].category == RiskCategory.SCHEDULE


def test_parse_model_findings_accepts_findings_wrapper():
    result = parse_model_findings({"findings": valid_payload()})
    assert result[0].id == "f1"


def test_parse_model_findings_rejects_malformed_output():
    with pytest.raises(ValueError):
        parse_model_findings({"findings": [{"id": "missing-required-fields"}]})


def test_prompt_preserves_signal_ids():
    signal = ProjectSignal(id="s42", source="test", source_type="text", timestamp="2026-01-01T00:00:00Z", content="API is late")
    prompt = build_reasoning_prompt([signal])
    assert "[s42]" in prompt


class FakeResponses:
    def __init__(self, output_text):
        self.output_text = output_text
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return type("Response", (), {"output_text": self.output_text})()


class FakeClient:
    def __init__(self, output_text):
        self.responses = FakeResponses(output_text)


def signal(identifier="s1"):
    return ProjectSignal(
        id=identifier,
        source="test",
        source_type="text",
        timestamp=datetime.now(UTC),
        content="The delivery date moved.",
    )


def test_openai_provider_uses_structured_output_and_validates_evidence():
    import json

    client = FakeClient(json.dumps({"findings": valid_payload()}))
    result = OpenAIResponsesProvider(client=client, model="test-model").analyze([signal()])

    assert result[0].id == "f1"
    request = client.responses.calls[0]
    assert request["model"] == "test-model"
    assert request["text"]["format"]["type"] == "json_schema"
    assert request["text"]["format"]["strict"] is True


def test_openai_provider_rejects_unknown_evidence_ids():
    import json

    payload = valid_payload()
    payload[0]["evidence"][0]["signal_id"] = "not-provided"
    provider = OpenAIResponsesProvider(client=FakeClient(json.dumps({"findings": payload})), model="test-model")

    with pytest.raises(ValueError, match="not supplied"):
        provider.analyze([signal()])
