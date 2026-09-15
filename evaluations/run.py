from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

from project_risk_agent.analysis import SignalReasoner
from project_risk_agent.models import ProjectSignal


def run_case(case: dict) -> dict:
    signals = [
        ProjectSignal(
            id=item["id"],
            source=item["source"],
            source_type=item["source_type"],
            content=item["content"],
            timestamp=datetime.now(UTC),
        )
        for item in case["signals"]
    ]
    findings = SignalReasoner().analyze(signals)
    expected = case["expected"]
    actual_types = {finding.type.value for finding in findings}
    actual_categories = {finding.category.value for finding in findings}
    evidence_grounded = all(finding.evidence for finding in findings)
    expected_types = set(expected.get("finding_types", []))
    expected_categories = set(expected.get("categories", []))
    type_ok = expected_types <= actual_types if expected_types else not actual_types
    category_ok = expected_categories <= actual_categories
    evidence_ok = not expected.get("requires_evidence", False) or evidence_grounded
    return {
        "id": case["id"],
        "pass": type_ok and category_ok and evidence_ok,
        "finding_types": sorted(actual_types),
        "categories": sorted(actual_categories),
        "finding_count": len(findings),
        "evidence_grounded": evidence_grounded,
    }


def main() -> int:
    cases = json.loads(Path(__file__).with_name("cases.json").read_text(encoding="utf-8"))
    results = [run_case(case) for case in cases]
    for result in results:
        print(f"{'PASS' if result['pass'] else 'FAIL'} {result['id']}: {result['finding_count']} finding(s)")
    return 0 if all(result["pass"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
