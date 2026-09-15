from project_risk_agent.delta import compare_findings
from project_risk_agent.models import Finding, FindingType, RiskCategory


def finding(identifier: str, *, impact: str = "medium") -> Finding:
    return Finding(
        id=identifier,
        type=FindingType.RISK,
        category=RiskCategory.SCHEDULE,
        title=identifier,
        description=identifier,
        impact=impact,
        confidence=0.8,
    )


def test_compare_findings_tracks_new_continuing_and_resolved():
    delta = compare_findings([finding("old"), finding("same")], [finding("same"), finding("new")])

    assert [item.id for item in delta.new] == ["new"]
    assert [item.id for item in delta.continuing] == ["same"]
    assert [item.id for item in delta.resolved] == ["old"]
    assert delta.changed == []


def test_compare_findings_tracks_material_changes_and_attention_direction():
    delta = compare_findings([finding("same")], [finding("same", impact="high")])

    assert len(delta.changed) == 1
    change = delta.changed[0]
    assert change.finding_id == "same"
    assert "impact" in change.changed_fields
    assert change.previous_attention < change.current_attention
    assert change.attention_direction == "increased"
