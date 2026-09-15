from __future__ import annotations

import re
from collections import defaultdict
from hashlib import sha256

from project_risk_agent.evidence import evidence_for_signals
from project_risk_agent.models import Evidence, Finding, FindingType, ProjectSignal, RiskCategory
from project_risk_agent.temporal import has_repeated_change, signal_sequence


PATTERNS: tuple[tuple[str, RiskCategory], ...] = ()
