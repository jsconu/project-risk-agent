from __future__ import annotations

import argparse
import json
from pathlib import Path

from project_risk_agent.analyzer import RiskAnalyzer
from project_risk_agent.connectors.file import FileConnector
from project_risk_agent.providers import DeterministicProvider
from project_risk_agent.service import RiskAnalysisService


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze project information for management risks.")
    parser.add_argument("path", type=Path, help="Text or JSON file containing project signals")
    args = parser.parse_args()

    signals = FileConnector().load(args.path)
    result = RiskAnalysisService(DeterministicProvider(RiskAnalyzer())).analyze(signals)
    payload = {
        "signals_analyzed": result.signals_analyzed,
        "findings": [finding.model_dump(mode="json") for finding in result.findings],
    }
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
