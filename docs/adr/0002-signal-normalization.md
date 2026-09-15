# ADR 0002: Normalize external information into ProjectSignal

## Status

Accepted

## Context

Project information arrives from systems with very different APIs and data models. Risk reasoning should operate on project meaning rather than provider-specific payloads.

## Decision

Every connector converts source records into the common `ProjectSignal` model. A signal carries source identity, source type, timestamp, project context, content, metadata, and provenance.

Connectors are responsible for authentication, retrieval, pagination/rate-limit handling, and source-specific parsing. The reasoning layer is responsible for interpreting normalized signals.

## Consequences

- New integrations can be added without changing the reasoning engine.
- Evidence can point back to stable signal IDs.
- Provenance remains available for auditing and debugging.
- Provider-specific fields may remain in `metadata`, but core reasoning must not depend on them.
- Native connectors and generic webhook/file ingestion can coexist behind the same contract.
