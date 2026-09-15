# Security

Project Risk Agent is intended to process potentially sensitive organizational information.

## Principles

- Never commit credentials, tokens, secrets, or real customer data.
- Prefer least-privilege OAuth/API scopes for integrations.
- Keep provider credentials outside the repository and source tree.
- Do not add telemetry or data collection without explicit user configuration.
- Preserve provenance so users can inspect why a finding was produced.
- Clearly distinguish source evidence from model inference.
- Treat meeting transcripts, email, chat, and project data as sensitive by default.
- The agent should recommend actions but should not autonomously make consequential business decisions.

## Reporting a vulnerability

Please do not publish credentials or exploit details in a public issue. Use GitHub's private vulnerability-reporting mechanism when available, or contact the repository maintainer privately through GitHub.
