# Changelog

All notable changes to this project are documented here.

The project is in early development and does not yet guarantee API stability.

## [Unreleased]

## [0.3.0]

- Chat app for non-technical users: a local, guided chat window (`project-risk-agent-chat`, new `chat` extra) where people paste updates or drop `.txt`/`.md`/`.csv`/`.json`/`.eml` files, get plain-language findings with quoted evidence, ask follow-up questions, and download a shareable report. Runs entirely on the user's computer with a localhost-only, token-protected server and a strict CSP.
- Double-click desktop builds (Windows `.exe`, macOS `.app`) built with PyInstaller and attached to releases by a new workflow, each verified with an in-app self-test.
- Fix the static demo page, which sent signals without the required `timestamp` and was rejected by the API.

## [0.2.0]

- Apache-2.0 `LICENSE`, Code of Conduct, and GitHub issue/PR templates for open-source release.
- Packaging metadata (license, classifiers, keywords, project URLs) and a PyPI publish workflow using Trusted Publishing.

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
