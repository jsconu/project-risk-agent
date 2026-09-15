from project_risk_agent.evidence import deduplicate_evidence, evidence_for_signals
from project_risk_agent.models import Evidence, ProjectSignal


def test_deduplicate_evidence_preserves_order():
    items = [Evidence(signal_id="s1", excerpt="same"), Evidence(signal_id="s1", excerpt="same")]
    assert len(deduplicate_evidence(items)) == 1


def test_evidence_for_signals_uses_matching_signals():
    signal = ProjectSignal(id="s1", source="test", source_type="text", timestamp="2026-01-01T00:00:00Z", content="blocked")
    result = evidence_for_signals([signal], lambda s: "blocked" in s.content, "support")
    assert result[0].signal_id == "s1"
    assert result[0].rationale == "support"
