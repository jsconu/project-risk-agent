from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel

from project_risk_agent.analyzer import RiskAnalyzer
from project_risk_agent.models import ProjectSignal
from project_risk_agent.providers import DeterministicProvider
from project_risk_agent.service import RiskAnalysisService


class AnalyzeRequest(BaseModel):
    signals: list[ProjectSignal]


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
            "findings": result.findings,
        }

    return app


app = create_app()
