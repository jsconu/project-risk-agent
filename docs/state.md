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

for change in result.changed_findings:
    print("CHANGED:", change.finding_id, change.attention_direction)
```

The local JSON store is intentionally simple. It is suitable for experiments and single-process deployments, not as a multi-user database.

## Longitudinal signals

When a finding remains present across runs, the delta layer compares material attributes such as likelihood, impact, urgency, confidence, ownership, decision state, and recommended actions. Each change includes the prior and current management-attention scores plus a direction (`increased`, `decreased`, or `unchanged`).

This makes the agent useful for questions such as:

- What changed since the last review?
- Which risks are new?
- Which continuing risks are getting more serious?
- Which findings are resolved?
- Which findings need renewed human attention?

The comparison uses stable finding IDs. Future state backends can add richer history, trend detection, configurable retention, and database-backed concurrency without changing the analysis interface.

## Trajectories and resolution

Each current finding is classified as `new`, `persistent`, `improving`, `deteriorating`, or `stale`. A `resolved` trajectory is emitted only when a current, fresh signal explicitly links to the prior finding (by finding ID or `resolves_finding_ids` metadata) and states that it was resolved, closed, completed, unblocked, or mitigated. A finding merely disappearing from a later analysis remains an unconfirmed delta, not a resolution. This prevents gaps in source coverage from creating false resolution claims.

## Privacy

State can contain sensitive project information. Keep the state path out of source control and apply the same access, retention, and redaction controls as the underlying project data.
