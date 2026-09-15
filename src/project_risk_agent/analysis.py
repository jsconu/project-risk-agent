from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import re

from project_risk_agent.models import Evidence, Finding, FindingType, ProjectSignal, RiskCategory


PATTERNS: tuple[tuple[str, RiskCategory], ...] = (
    (r"\b(delayed?|slipp(?:ed|ing)|miss(?:ed|ing)|behind|cannot start|can't start)\b", RiskCategory.SCHEDULE),
    (r"\b(moved from .+ to .+|date change|date changed|schedule changed|second date change|another date change)\b", RiskCategory.SCHEDULE),
    (r"\b(depend(?:ency|encies)|depends on|waiting for|blocked by|until .+ is available)\b", RiskCategory.DEPENDENCY),
    (r"\b(understaffed|no capacity|resource constraint|vacancy|bandwidth)\b", RiskCategory.RESOURCE),
    (r"\b(scope creep|out of scope|requirements changed|change request)\b", RiskCategory.SCOPE),
    (r"\b(defect|bug|failed test|quality issue|regression)\b", RiskCategory.QUALITY),
    (r"\b(vendor|supplier|third party)\b", RiskCategory.VENDOR),
    (r"\b(budget|cost overrun|funding|financial)\b", RiskCategory.FINANCIAL),
    (r"\b(customer escalation|stakeholder concern|sponsor concern)\b", RiskCategory.STAKEHOLDER),
    (r"\b(outage|integration failure|performance issue|technical debt)\b", RiskCategory.TECHNICAL),
)


def _matched_categories(text: str) -> list[RiskCategory]:
    lowered = text.lower()
    return [category for pattern, category in PATTERNS if re.search(pattern, lowered)]


def _finding_id(signals: list[ProjectSignal], finding_type: FindingType, category: RiskCategory) -> str:
    raw = ":".join(sorted(s.id for s in signals)) + f":{finding_type.value}:{category.value}"
    return "finding-" + sha256(raw.encode()).hexdigest()[:12]


class SignalReasoner:
    """Conservative, evidence-first reasoning baseline."""

    def analyze(self, signals: list[ProjectSignal]) -> list[Finding]:
        findings: list[Finding] = []
        for signal in signals:
            text = signal.content.strip()
            if not text:
                continue
            categories = _matched_categories(text)
            finding_type = self._finding_type(text)
            if not categories and finding_type != FindingType.DECISION:
                continue
            category = self._category(categories, finding_type)
            findings.append(
                Finding(
                    id=_finding_id([signal], finding_type, category),
                    type=finding_type,
                    category=category,
                    title=self._title(finding_type, category),
                    description=text[:500],
                    likelihood=self._likelihood(text),
                    impact=self._impact(text),
                    urgency=self._urgency(text),
                    confidence=0.68,
                    evidence=[Evidence(signal_id=signal.id, excerpt=text[:500], rationale="Signal contains language associated with a management concern.")],
                    decision_required=finding_type == FindingType.DECISION,
                    recommended_actions=self._actions(finding_type, category),
                )
            )

        return self._infer_cross_signal_schedule_risk(signals, self._corroborate(findings))

    @staticmethod
    def _category(categories: list[RiskCategory], finding_type: FindingType) -> RiskCategory:
        if finding_type == FindingType.DEPENDENCY and RiskCategory.DEPENDENCY in categories:
            return RiskCategory.DEPENDENCY
        return categories[0] if categories else RiskCategory.OTHER

    @staticmethod
    def _corroborate(findings: list[Finding]) -> list[Finding]:
        groups: dict[tuple[FindingType, RiskCategory], list[Finding]] = defaultdict(list)
        for finding in findings:
            groups[(finding.type, finding.category)].append(finding)
        output: list[Finding] = []
        for group in groups.values():
            primary = group[0]
            if len(group) > 1:
                primary.evidence = [e for item in group for e in item.evidence]
                primary.confidence = min(0.95, primary.confidence + 0.08 * (len(group) - 1))
                primary.description = f"Corroborated by {len(group)} project signals. " + primary.description
            output.append(primary)
        return output

    def _infer_cross_signal_schedule_risk(self, signals: list[ProjectSignal], findings: list[Finding]) -> list[Finding]:
        lowered = [s.content.lower() for s in signals]
        has_schedule_movement = any(re.search(r"\b(moved from .+ to .+|date change|date changed|delayed?|slipp(?:ed|ing))\b", text) for text in lowered)
        has_downstream_dependency = any(re.search(r"\b(depends on|dependency|dependencies|waiting for|blocked by|cannot start|until .+ is available)\b", text) for text in lowered)
        if not (has_schedule_movement and has_downstream_dependency):
            return findings
        evidence = [
            Evidence(signal_id=signal.id, excerpt=signal.content[:500], rationale="Cross-signal evidence for schedule exposure.")
            for signal in signals
            if re.search(r"\b(moved from .+ to .+|date change|date changed|delayed?|slipp(?:ed|ing)|depends on|dependency|dependencies|waiting for|blocked by|cannot start|until .+ is available)\b", signal.content.lower())
        ]
        existing = next((f for f in findings if f.type == FindingType.RISK and f.category == RiskCategory.SCHEDULE), None)
        if existing:
            existing.evidence = evidence
            existing.confidence = min(0.95, max(existing.confidence, 0.82))
            existing.description = "Schedule movement and a downstream dependency are supported by multiple signals."
            existing.likelihood = "high"
            return findings
        findings.append(Finding(
            id=_finding_id(signals, FindingType.RISK, RiskCategory.SCHEDULE),
            type=FindingType.RISK,
            category=RiskCategory.SCHEDULE,
            title="Potential schedule concern",
            description="Schedule movement is coupled to a downstream dependency.",
            likelihood="high",
            impact="medium",
            urgency="medium",
            confidence=0.82,
            evidence=evidence,
            recommended_actions=["Validate the dependency date and downstream contingency with the owners."],
        ))
        return findings

    @staticmethod
    def _finding_type(text: str) -> FindingType:
        lowered = text.lower()
        # Explicit risk framing takes precedence over generic status words.
        if re.search(r"\b(decision|approve|approval|choose|needs sign[- ]off)\b", lowered):
            return FindingType.DECISION
        if re.search(r"\b(risk|at risk|may miss|might miss|could miss|potential)\b", lowered):
            return FindingType.RISK
        if re.search(r"\b(already missed|has failed|failed test|outage|currently blocked|currently unavailable)\b", lowered):
            return FindingType.ISSUE
        if re.search(r"\b(depends on|dependency|dependencies|waiting for|blocked by)\b", lowered):
            return FindingType.DEPENDENCY
        return FindingType.RISK

    @staticmethod
    def _title(finding_type: FindingType, category: RiskCategory) -> str:
        prefix = {FindingType.RISK: "Potential", FindingType.ISSUE: "Active", FindingType.DEPENDENCY: "Dependency", FindingType.DECISION: "Decision needed for"}[finding_type]
        return f"{prefix} {category.value} concern"

    @staticmethod
    def _likelihood(text: str) -> str:
        lowered = text.lower()
        return "high" if re.search(r"\b(blocked|cannot|critical|miss|failed)\b", lowered) else "medium"

    @staticmethod
    def _impact(text: str) -> str:
        lowered = text.lower()
        return "high" if re.search(r"\b(launch|deadline|critical|customer|revenue|production)\b", lowered) else "medium"

    @staticmethod
    def _urgency(text: str) -> str:
        lowered = text.lower()
        return "high" if re.search(r"\b(today|tomorrow|blocked|critical|production|outage)\b", lowered) else "medium"

    @staticmethod
    def _actions(finding_type: FindingType, category: RiskCategory) -> list[str]:
        if finding_type == FindingType.DECISION:
            return ["Confirm the decision owner and required decision date."]
        if finding_type == FindingType.DEPENDENCY:
            return ["Confirm the dependency owner, required-by date, and contingency."]
        if finding_type == FindingType.ISSUE:
            return ["Assign an owner, recovery action, and next checkpoint."]
        return [f"Validate the {category.value} concern with the responsible owner."]
