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

## Local chat app

The chat app (`project-risk-agent-chat` and the desktop downloads) serves a page on
`127.0.0.1` only, requires a per-launch random session token on every request, rejects
requests whose `Host` header is not localhost, sends a strict Content-Security-Policy, keeps
conversations in memory only, and never renders pasted text as HTML. See
[docs/chat-app.md](docs/chat-app.md). Changes to it should preserve these properties; the
tests in `tests/test_webapp.py` cover them.

## Reporting a vulnerability

Please do not publish credentials or exploit details in a public issue. Use GitHub's private vulnerability-reporting mechanism when available, or contact the repository maintainer privately through GitHub.
