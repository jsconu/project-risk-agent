# Changelog

All notable changes to this project are documented here.

The project is in early development and does not yet guarantee API stability.

## [Unreleased]

- Longitudinal finding trajectories: new, persistent, improving, deteriorating, stale, and explicitly confirmed resolved.
- Resolution guard: a finding absent from a later run is not declared resolved without fresh, linked resolution evidence.
- Optional OpenAI Responses API provider with strict structured-output, domain-schema, and supplied-evidence validation.
- Decision queue with explicit ownership/deadline readiness checks in the service, API, CLI, and management brief.
- Dependency queue with evidence-linked blocked, waiting, and at-risk statuses.
- Evidence freshness classification based on the timestamps of supporting signals.
- API and CLI exposure of finding trajectories, freshness, and analysis trend.
- Persistent local project state with new/continuing/resolved finding deltas.
- Material-change tracking with management-attention direction across analysis runs.
- Evidence-backed contradiction detection across project signals.
- Cross-signal temporal reasoning for repeated schedule movement and downstream dependencies.
- FastAPI analysis and management-brief endpoints with local demo CORS support.
- Jira Cloud and Slack read connectors.
- Generic webhook and file ingestion paths.
- Connector implementation template and normalization/security guidance.
- Expanded synthetic evaluation coverage and automated CI checks.

## [0.1.0]

- Initial public foundation for source-agnostic project risk intelligence.
- Common signal and finding schemas.
- Deterministic analysis provider behind a model-provider boundary.
- File ingestion, evidence handling, prioritization, and decision extraction.
- Synthetic evaluation suite covering common project-risk patterns.
