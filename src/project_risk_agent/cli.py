from __future__ import annotations

import argparse
import json
from pathlib import Path

from project_risk_agent.analyzer import RiskAnalyzer
from project_risk_agent.brief import management_brief
from project_risk_agent.connectors.file import FileConnector
from project_risk_agent.prioritizer import prioritize
from project_risk_agent.providers import DeterministicProvider
from project_risk_agent.service import RiskAnalysisService
from project_risk_agent.state import JsonProjectStateStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze project information for management risks.")
    parser.add_argument("path", type=Path, help="Text or JSON file containing project signals")
    parser.add_argument("--brief", action="store_true", help="Print a concise management brief")
    parser.add_argument("--all", action="store_true", help="Include all findings instead of prioritized findings")
    parser.add_argument(
        "--state",
        type=Path,
        help="Persist project intelligence at this path and report changes from the prior run",
    )
    args = parser.parse_args()

    signals = FileConnector().load(args.path)
    service = RiskAnalysisService(DeterministicProvider(RiskAnalyzer()))
    result = service.analyze_with_state(signals, JsonProjectStateStore(args.state)) if args.state else service.analyze(signals)
    findings = result.findings if args.all else prioritize(result.findings)

    if args.brief:
        print(management_brief(findings))
        if result.changed_findings:
            print("\nChanged findings:")
            for change in result.changed_findings:
                fields = ", ".join(change.changed_fields)
                print(f"- {change.finding_id}: {change.attention_direction} ({fields})")
        return

    payload = {
        "signals_analyzed": result.signals_analyzed,
        "findings": [finding.model_dump(mode="json") for finding in findings],
        "changed_findings": [
            {
                "finding_id": change.finding_id,
                "changed_fields": change.changed_fields,
                "previous_attention": change.previous_attention,
                "current_attention": change.current_attention,
                "attention_direction": change.attention_direction,
            }
            for change in result.changed_findings
        ],
    }
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
