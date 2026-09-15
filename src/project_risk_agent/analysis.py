from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import re

from project_risk_agent.models import Evidence, Finding, FindingType, ProjectSignal, RiskCategory


PATTERNS: tuple[tuple[str, RiskCategory], ...] = (
    (r"\b(delayed?|slipp(?:ed|ing)|miss(?:ed|ing)|behind|cannot start|can't start)\b", RiskCategory.SCHEDULE),
    (r"\b(depend(?:ency|encies)|depends on|waiting for|blocked by)\b", RiskCategory.DEPENDENCY),
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
    """Deterministic, evidence-first baseline for normalized project signals.

    This is intentionally conservative: it only promotes a finding when the
    input contains recognizable signal language, and every finding carries
    source evidence. Model-backed inference can later sit behind this same
    output contract.
    """

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

            category = categories[0] if categories else RiskCategory.OTHER
            evidence = Evidence(
                signal_id=signal.id,
                excerpt=text[:500],
                rationale="Signal contains language associated with a management concern.",
            )
            findings.append(
                Finding(
                    id=_finding_id([signal], finding_type, category),
                    type=finding_type,
                    category=category,
                    title=self._title(text, finding_type, category),
                    description=text[:500],
                    likelihood=self._likelihood(text),
                    impact=self._impact(text),
                    urgency=self._urgency(text),
                    confidence=0.68,
                    evidence=[evidence],
                    decision_required=finding_type == FindingType.DECISION,
                    recommended_actions=self._actions(finding_type, category),
                )
            )

        return self._corroborate(findings)

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
                primary.description = (
                    f"Corroborated by {len(group)} project signals. " + primary.description
                )
            output.append(primary)
        return output

    @staticmethod
    def _finding_type(text: str) -> FindingType:
        lowered = text.lower()
        if re.search(r"\b(decision|approve|approval|choose|needs sign[- ]off)\b", lowered):
            return FindingType.DECISION
        if re.search(r"\b(blocked|failed|has failed|already missed|is delayed|outage)\b", lowered):
            return FindingType.ISSUE
        if re.search(r"\b(depends on|dependency|waiting for|blocked by)\b", lowered):
            return FindingType.DEPENDENCY
        return FindingType.RISK

    @staticmethod
    def _title(text: str, finding_type: FindingType, category: RiskCategory) -> str:
        prefix = {
            FindingType.RISK: "Potential",
            FindingType.ISSUE: "Active",
            FindingType.DEPENDENCY: "Dependency",
            FindingType.DECISION: "Decision needed for",
        }[finding_type]
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
