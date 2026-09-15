from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import re

from project_risk_agent.models import Evidence, Finding, FindingType, ProjectSignal, RiskCategory


RISK_PATTERNS: tuple[tuple[str, RiskCategory], ...] = (
    (r"\b(delayed?|slipp(?:ed|ing)|miss(?:ed|ing)|behind|blocked|cannot start|can't start)\b", RiskCategory.SCHEDULE),
    (r"\b(depend(?:ency|encies)|depends on|waiting for|blocked by)\b", RiskCategory.DEPENDENCY),
    (r"\b(understaffed|no capacity|capacity|resource constraint|vacancy)\b", RiskCategory.RESOURCE),
    (r"\b(scope creep|out of scope|requirements changed|change request)\b", RiskCategory.SCOPE),
    (r"\b(defect|bug|failed test|quality issue|regression)\b", RiskCategory.QUALITY),
    (r"\b(vendor|supplier|third party)\b", RiskCategory.VENDOR),
    (r"\b(budget|cost overrun|funding|financial)\b", RiskCategory.FINANCIAL),
)


def _category(text: str) -> RiskCategory:
    lowered = text.lower()
    for pattern, category in RISK_PATTERNS:
        if re.search(pattern, lowered):
            return category
    return RiskCategory.OTHER


def _finding_id(signals: list[ProjectSignal]) -> str:
    raw = ":".join(sorted(s.id for s in signals))
    return "finding-" + sha256(raw.encode()).hexdigest()[:12]


class SignalReasoner:
    """Evidence-first reasoning over a set of normalized project signals."""

    def analyze(self, signals: list[ProjectSignal]) -> list[Finding]:
        if not signals:
            return []

        findings: list[Finding] = []
        for signal in signals:
            if not self._is_actionable(signal.content):
                continue
            category = _category(signal.content)
            findings.append(
                Finding(
                    id=_finding_id([signal]),
                    type=self._finding_type(signal.content),
                    category=category,
                    title=self._title(signal.content, category),
                    description=signal.content[:500],
                    likelihood=self._likelihood(signal.content),
                    impact=self._impact(signal.content),
                    urgency=self._urgency(signal.content),
                    confidence=0.68,
                    evidence=[Evidence(signal_id=signal.id, excerpt=signal.content[:500])],
                )
            )

        # Repeated or corroborated signals increase confidence without inventing evidence.
        groups: dict[tuple[RiskCategory, FindingType], list[Finding]] = defaultdict(list)
        for finding in findings:
            groups[(finding.category, finding.type)].append(finding)
        for group in groups.values():
            if len(group) < 2:
                continue
            primary = group[0]
            primary.evidence = [e for f in group for e in f.evidence]
            primary.confidence = min(0.95, primary.confidence + 0.08 * (len(group) - 1))
            primary.description = "Multiple project signals support this finding."
            primary.title = primary.title.replace("Potential", "Corroborated")
            findings = [f for f in findings if f is primary or f not in group]

        return findings

    @staticmethod
    def _is_actionable(text: str) -> bool:
        lowered = text.lower()
        return any(re.search(pattern, lowered) for pattern, _ in RISK_PATTERNS) or "decision" in lowered

    @staticmethod
    def _finding_type(text: str) -> FindingType:
        lowered = text.lower()
        if "decision" in lowered or "approve" in lowered or "approval" in lowered:
            return FindingType.DECISION
        if any(word in lowered for word in ("blocked", "failed", "already", "is delayed")):
            return FindingType.ISSUE
        if any(word in lowered for word in ("depends on", "dependency", "waiting for", "blocked by")):
            return FindingType.DEPENDENCY
        return FindingType.RISK

    @staticmethod
    def _title(text: str, category: RiskCategory) -> str:
        prefix = "Management decision needed" if "decision" in text.lower() else "Potential"
        return f"{prefix} {category.value} concern"

    @staticmethod
    def _likelihood(text: str) -> str:
        lowered = text.lower()
        return "high" if any(x in lowered for x in ("blocked", "cannot", "miss", "critical")) else "medium"

    @staticmethod
    def _impact(text: str) -> str:
        lowered = text.lower()
        return "high" if any(x in lowered for x in ("launch", "deadline", "critical", "customer")) else "medium"

    @staticmethod
    def _urgency(text: str) -> str:
        lowered = text.lower()
        return "high" if any(x in lowered for x in ("today", "tomorrow", "blocked", "critical")) else "medium"
