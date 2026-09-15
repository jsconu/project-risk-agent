from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class FindingType(str, Enum):
    RISK = "risk"
    ISSUE = "issue"
    DEPENDENCY = "dependency"
    DECISION = "decision"


class RiskCategory(str, Enum):
    SCHEDULE = "schedule"
    DEPENDENCY = "dependency"
    RESOURCE = "resource"
    SCOPE = "scope"
    QUALITY = "quality"
    STAKEHOLDER = "stakeholder"
    TECHNICAL = "technical"
    VENDOR = "vendor"
    FINANCIAL = "financial"
    OTHER = "other"


class ProjectSignal(BaseModel):
    """A normalized piece of project information from any source."""

    id: str
    source: str
    source_type: str
    timestamp: datetime
    project_id: str | None = None
    author: str | None = None
    content: str
    metadata: dict[str, object] = Field(default_factory=dict)
    provenance: dict[str, object] = Field(default_factory=dict)


class Evidence(BaseModel):
    signal_id: str
    excerpt: str
    rationale: str | None = None


class Finding(BaseModel):
    """An evidence-backed management finding."""

    id: str
    type: FindingType
    category: RiskCategory
    title: str
    description: str
    likelihood: str | None = None
    impact: str | None = None
    urgency: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)
    owner: str | None = None
    decision_required: bool = False
    decision_owner: str | None = None
    recommended_actions: list[str] = Field(default_factory=list)
