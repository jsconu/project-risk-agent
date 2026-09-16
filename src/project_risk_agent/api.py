from __future__ import annotations

from dataclasses import asdict
from pydantic import BaseModel

from project_risk_agent.analyzer import RiskAnalyzer
from project_risk_agent.brief import management_brief
from project_risk_agent.models import ProjectSignal
from project_risk_agent.providers import DeterministicProvider, ModelProvider
from project_risk_agent.service import AnalysisResult, RiskAnalysisService


class AnalyzeRequest(BaseModel):
    signals: list[ProjectSignal]


def _changes(result: AnalysisResult) -> list[dict[str, object]]:
    return [asdict(change) | {"attention_direction": change.attention_direction} for change in result.changed_findings]


def _trajectories(result: AnalysisResult) -> list[dict[str, object]]:
    return [asdict(item) for item in result.trajectories]


def _freshness(result: AnalysisResult) -> list[dict[str, object]]:
    return [asdict(item) for item in result.freshness or []]


def _decisions(result: AnalysisResult) -> list[dict[str, object]]:
    return [asdict(item) for item in result.decision_requests or []]


def create_app(provider: ModelProvider | None = None):
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
    except ImportError as exc:  # pragma: no cover - exercised only without API extra
        raise RuntimeError("Install the 'api' extra to run the HTTP API") from exc

    app = FastAPI(title="Project Risk Agent", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:8001", "http://localhost:8001"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    service = RiskAnalysisService(provider or DeterministicProvider(RiskAnalyzer()))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    def response(result: AnalysisResult) -> dict[str, object]:
        return {
            "analyzed_at": result.analyzed_at,
            "signals_analyzed": result.signals_analyzed,
            "trend": result.trend,
            "findings": result.management_attention,
            "changed_findings": _changes(result),
            "trajectories": _trajectories(result),
            "freshness": _freshness(result),
            "decision_requests": _decisions(result),
        }

    @app.post("/analyze")
    def analyze(request: AnalyzeRequest) -> dict[str, object]:
        return response(service.analyze(request.signals))

    @app.post("/brief")
    def brief(request: AnalyzeRequest) -> dict[str, object]:
        result = service.analyze(request.signals)
        return response(result) | {
            "markdown": management_brief(result.management_attention, result.decision_requests)
        }

    return app


app = create_app()
