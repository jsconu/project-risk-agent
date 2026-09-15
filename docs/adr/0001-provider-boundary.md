# ADR 0001: Keep reasoning providers behind a stable boundary

## Status

Accepted

## Context

The project needs to support deterministic local evaluation as well as model-backed reasoning. Hard-coding a model vendor into the core analysis engine would make testing, self-hosting, and future provider changes unnecessarily difficult.

## Decision

The reasoning layer uses a small provider interface. The core service accepts a `ModelProvider` and does not depend on a specific model vendor or SDK.

The deterministic provider remains the default baseline. Model-backed providers may be added behind the same boundary and should return validated `Finding` objects rather than bypassing the evidence/provenance model.

## Consequences

- Contributors can improve reasoning without requiring API credentials.
- Evaluation results remain reproducible when using the deterministic provider.
- Model vendors can be changed without rewriting connectors or the service layer.
- Provider implementations must preserve evidence IDs and schema validation.
- Vendor-specific prompting belongs in the provider layer, not in the domain models.
