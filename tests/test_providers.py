import pytest

from project_risk_agent.models import FindingType, RiskCategory
from project_risk_agent.providers import build_reasoning_prompt, parse_model_findings


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
    from project_risk_agent.models import ProjectSignal
    signal = ProjectSignal(id="s42", source="test", source_type="text", timestamp="2026-01-01T00:00:00Z", content="API is late")
    prompt = build_reasoning_prompt([signal])
    assert "[s42]" in prompt
