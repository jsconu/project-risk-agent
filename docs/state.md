# Persistent Project Intelligence

The agent can persist the latest normalized signals and findings so a later run can reason about change rather than treating every analysis as a blank slate.

## Local usage

```python
from project_risk_agent.providers import DeterministicProvider
from project_risk_agent.analyzer import RiskAnalyzer
from project_risk_agent.service import RiskAnalysisService
from project_risk_agent.state import JsonProjectStateStore

service = RiskAnalysisService(DeterministicProvider(RiskAnalyzer()))
store = JsonProjectStateStore(".project-risk/state.json")
result = service.analyze_with_state(signals, store)

for finding in result.delta.new:
    print("NEW:", finding.title)

for finding in result.delta.resolved:
    print("RESOLVED:", finding.title)
```

The local JSON store is intentionally simple. It is suitable for experiments and single-process deployments, not as a multi-user database.

## Why this matters

A useful project agent should accumulate context and answer questions such as:

- What changed since the last review?
- Which risks are new?
- Which findings are continuing?
- Which previously observed findings disappeared?

The current implementation compares stable finding IDs. Future state backends can add richer history, trend detection, configurable retention, and database-backed concurrency without changing the analysis interface.

## Privacy

State can contain sensitive project information. Keep the state path out of source control and apply the same access, retention, and redaction controls as the underlying project data.
