from __future__ import annotations

import argparse
import json
from pathlib import Path

from project_risk_agent.analyzer import RiskAnalyzer
from project_risk_agent.brief import management_brief
from project_risk_agent.connectors.file import FileConnector
from project_risk_agent.prioritizer import prioritize
from project_risk_agent.providers import DeterministicProvider, openai_provider_from_environment
from project_risk_agent.service import RiskAnalysisService
from project_risk_agent.state import JsonProjectStateStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze project information for management risks.")
    parser.add_argument("path", type=Path, help="Text or JSON file containing project signals")
    parser.add_argument("--brief", action="store_true", help="Print a concise management brief")
    parser.add_argument("--all", action="store_true", help="Include all findings instead of prioritized findings")
    parser.add_argument(
        "--provider",
        choices=("deterministic", "openai"),
        default="deterministic",
        help="Reasoning provider (default: deterministic)",
    )
    parser.add_argument(
        "--model",
        help="OpenAI model ID; required with --provider openai unless configured in the environment",
    )
    parser.add_argument(
        "--state",
        type=Path,
        help="Persist project intelligence at this path and report changes from the prior run",
    )
    args = parser.parse_args()

    signals = FileConnector().load(args.path)
    provider = (
        openai_provider_from_environment(args.model)
        if args.provider == "openai"
        else DeterministicProvider(RiskAnalyzer())
    )
    service = RiskAnalysisService(provider)
    result = service.analyze_with_state(signals, JsonProjectStateStore(args.state)) if args.state else service.analyze(signals)
    findings = result.findings if args.all else prioritize(result.findings)

    if args.brief:
        print(management_brief(findings, result.decision_requests))
        print(f"\nTrajectory: {result.trend}")
        for trajectory in result.trajectories:
            print(f"- {trajectory.finding_id}: {trajectory.state} ({trajectory.freshness})")
        if result.changed_findings:
            print("\nChanged findings:")
            for change in result.changed_findings:
                fields = ", ".join(change.changed_fields)
                print(f"- {change.finding_id}: {change.attention_direction} ({fields})")
        return

    payload = {
        "analyzed_at": result.analyzed_at,
        "signals_analyzed": result.signals_analyzed,
        "trend": result.trend,
        "findings": [finding.model_dump(mode="json") for finding in findings],
        "trajectories": [
            {
                "finding_id": item.finding_id,
                "state": item.state,
                "attention_direction": item.attention_direction,
                "freshness": item.freshness,
            }
            for item in result.trajectories
        ],
        "freshness": [
            {
                "finding_id": item.finding_id,
                "age_days": item.age_days,
                "status": item.status,
            }
            for item in result.freshness or []
        ],
        "decision_requests": [
            {
                "signal_id": item.signal_id,
                "description": item.description,
                "owner": item.owner,
                "deadline": item.deadline,
                "readiness": item.readiness,
            }
            for item in result.decision_requests or []
        ],
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
