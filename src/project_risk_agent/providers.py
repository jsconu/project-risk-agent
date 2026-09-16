from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Protocol

from pydantic import TypeAdapter, ValidationError

from project_risk_agent.models import Finding, ProjectSignal


class ModelProvider(Protocol):
    """Provider boundary for optional model-backed semantic reasoning."""

    def analyze(self, signals: list[ProjectSignal]) -> list[Finding]:
        ...


@dataclass
class DeterministicProvider:
    """No-key provider useful for local development, tests, and demos."""

    reasoner: object

    def analyze(self, signals: list[ProjectSignal]) -> list[Finding]:
        return self.reasoner.analyze(signals)


class StructuredModelProvider(Protocol):
    """Minimal boundary for an external model that can return structured JSON."""

    def complete_json(self, *, system: str, user: str) -> object:
        ...


_FINDING_LIST = TypeAdapter(list[Finding])


def parse_model_findings(payload: object) -> list[Finding]:
    """Validate model output before it enters the application domain."""
    candidate = payload["findings"] if isinstance(payload, dict) and "findings" in payload else payload
    try:
        return _FINDING_LIST.validate_python(candidate)
    except ValidationError as exc:
        raise ValueError("Model output does not match the Finding schema") from exc


def build_reasoning_prompt(signals: list[ProjectSignal]) -> str:
    """Create a vendor-neutral prompt while preserving signal provenance."""
    lines = [
        "Analyze these project signals for management-relevant risks, issues, dependencies, and decisions.",
        "Do not invent evidence. Distinguish observed evidence from inference.",
        "Every finding must cite one or more provided signal IDs as evidence.",
        "Return structured findings using the project's Finding schema.",
        "Signals:",
    ]
    for signal in signals:
        lines.append(f"[{signal.id}] ({signal.source_type}) {signal.content}")
    return "\n".join(lines)


_OPENAI_SYSTEM_PROMPT = """You are a cautious project-risk analyst. Return only evidence-backed findings.
Use only the supplied signals. Every evidence.signal_id must exactly match a supplied signal ID.
Do not treat an absence of information as evidence that a risk is resolved."""


def _finding_response_schema() -> dict[str, object]:
    """Return the Responses API schema for the existing Finding contract."""
    return {
        "type": "object",
        "properties": {"findings": _FINDING_LIST.json_schema()},
        "required": ["findings"],
        "additionalProperties": False,
    }


@dataclass
class OpenAIResponsesProvider:
    """Model-backed provider using the OpenAI Responses API structured-output path."""

    client: object
    model: str

    def analyze(self, signals: list[ProjectSignal]) -> list[Finding]:
        response = self.client.responses.create(
            model=self.model,
            instructions=_OPENAI_SYSTEM_PROMPT,
            input=build_reasoning_prompt(signals),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "project_risk_findings",
                    "schema": _finding_response_schema(),
                    "strict": True,
                }
            },
        )
        output_text = getattr(response, "output_text", None)
        if not isinstance(output_text, str):
            raise ValueError("OpenAI response did not include structured output text")
        try:
            findings = parse_model_findings(json.loads(output_text))
        except json.JSONDecodeError as exc:
            raise ValueError("OpenAI response was not valid JSON") from exc
        signal_ids = {signal.id for signal in signals}
        invalid_evidence = [
            evidence.signal_id
            for finding in findings
            for evidence in finding.evidence
            if evidence.signal_id not in signal_ids
        ]
        if invalid_evidence:
            raise ValueError("OpenAI response cited signal IDs that were not supplied")
        return findings


def openai_provider_from_environment(model: str | None = None) -> OpenAIResponsesProvider:
    """Create an opt-in OpenAI provider without putting credentials in application code."""
    selected_model = model or os.environ.get("PROJECT_RISK_AGENT_OPENAI_MODEL")
    if not selected_model:
        raise ValueError(
            "Set PROJECT_RISK_AGENT_OPENAI_MODEL or pass --model when using the OpenAI provider"
        )
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - depends on optional installation
        raise RuntimeError("Install the 'openai' extra to use the OpenAI provider") from exc
    return OpenAIResponsesProvider(client=OpenAI(), model=selected_model)
