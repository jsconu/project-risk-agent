from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime

from pydantic import BaseModel

from project_risk_agent.analyzer import RiskAnalyzer
from project_risk_agent.brief import management_brief
from project_risk_agent.models import ProjectSignal
from project_risk_agent.providers import DeterministicProvider
from project_risk_agent.service import AnalysisResult, RiskAnalysisService


class AnalyzeRequest(BaseModel):
    signals: list[ProjectSignal]


def _changes(result: AnalysisResult) -> list[dict[str, object]]:
    return [
        asdict(change) | {"attention_direction": change.attention_direction}
        for change in result.changed_findings
    ]


def create_app():
    try:
        from fastapi import FastAPI
    except ImportError as exc:  # pragma: no cover - exercised only without API extra
        raise RuntimeError("Install the 'api' extra to run the HTTP API") from exc

    app = FastAPI(title="Project Risk Agent", version="0.1.0")
    service = RiskAnalysisService(DeterministicProvider(RiskAnalyzer()))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/analyze")
    def analyze(request: AnalyzeRequest) -> dict[str, object]:
        result = service.analyze(request.signals)
        return {
            "analyzed_at": datetime.now(UTC),
            "signals_analyzed": result.signals_analyzed,
            "findings": result.management_attention,
            "changed_findings": _changes(result),
        }

    @app.post("/brief")
    def brief(request: AnalyzeRequest) -> dict[str, object]:
        result = service.analyze(request.signals)
        return {
            "generated_at": datetime.now(UTC),
            "signals_analyzed": result.signals_analyzed,
            "findings": result.management_attention,
            "changed_findings": _changes(result),
            "markdown": management_brief(result.management_attention),
        }

    return app


app = create_app()
