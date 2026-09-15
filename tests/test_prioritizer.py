from project_risk_agent.models import Finding, FindingType, RiskCategory
from project_risk_agent.prioritizer import attention_score, prioritize


def finding(name: str, urgency: str, confidence: float) -> Finding:
    return Finding(
        id=name,
        type=FindingType.RISK,
        category=RiskCategory.SCHEDULE,
        title=name,
        description="test",
        likelihood="high",
        impact="high",
        urgency=urgency,
        confidence=confidence,
    )


def test_attention_score_is_transparent_and_bounded():
    score = attention_score(finding("f1", "high", 0.9))
    assert 0 <= score <= 100
    assert score == 90.0


def test_prioritize_orders_high_attention_first():
    low = finding("low", "low", 0.9)
    high = finding("high", "high", 0.9)
    assert [item.id for item in prioritize([low, high])] == ["high", "low"]
