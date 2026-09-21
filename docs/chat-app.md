# The chat app

A local chat window for people who don't want to use a terminal or write code. It wraps the
same analysis engine as the CLI and API in a guided conversation.

## For users

Open the app, and a chat appears in your web browser. You can:

- Paste project updates (status reports, emails, meeting notes, chat messages).
- Drag a file into the window, or use **Attach file**: `.txt`, `.md`, `.csv`, `.json`, `.eml`.
  For Word or PDF documents, copy the text and paste it.
- Ask follow-ups with the suggested buttons or by typing: "What decisions are needed?",
  "What is blocked or waiting?", "What should I do next?", "What changed since last time?",
  "What did you read?", "Show everything", "Start over".
- Download a report (a single `.html` file that opens in any browser and can be printed or
  saved as a PDF), or copy it as text.

Notes on how it reads what you share:

- Blank lines separate updates. Bulleted or numbered lines become one update each. Lines
  wrapped mid-sentence are rejoined.
- Updates you have already shared are recognized, so pasting the same text twice doesn't
  double count it. Adding newer updates re-analyzes everything together and reports what
  changed since the previous look (in this session only).
- Emails (`.eml`) and JSON files with a `timestamp` keep their dates, so old information is
  flagged as old.
- A message is treated as a *question* only if it ends with `?` or is a short command such as
  "Show everything". Anything longer is read as an update.

### What it can't do (yet)

- It uses the deterministic, rule-based engine. It looks for common warning language, so it
  can miss things phrased in unusual ways. Findings quote their evidence so you can check them.
- Nothing is saved between sessions. Longitudinal tracking across days uses the CLI's
  `--state` option today.
- No live connectors (Jira, Slack) in the chat yet; export or copy the content instead.

## Privacy and security

The chat handles sensitive project information, so it is deliberately locked down:

- It listens on `127.0.0.1` only, never on the network. Requests with any other `Host`
  header are refused, which blocks DNS-rebinding attacks from other websites.
- Each launch creates a new random session token that every request must present, so other
  websites open in your browser cannot use it. The link printed at startup contains it.
- The page is served with a strict Content-Security-Policy (per-response nonce,
  `default-src 'none'`, no external requests) and never inserts pasted text as HTML.
- Conversations live in memory only. Quitting discards them. Nothing is written to disk and
  there is no telemetry.
- With the default engine nothing leaves your computer. If a technical user launches it with
  `--provider openai`, the page says so prominently, because pasted text is then sent to
  that service.

## For technical users

```bash
pip install "project-risk-agent[chat]"
project-risk-agent-chat                # opens your browser
project-risk-agent-chat --no-browser   # just print the link
project-risk-agent-chat --port 8080
project-risk-agent-chat --provider openai --model YOUR_MODEL_ID   # needs the openai extra
```

Code layout:

| File | Role |
|---|---|
| `chat_input.py` | Turns pasted text and uploaded files into updates |
| `chat.py` | The conversation: intent handling and plain-language replies |
| `chat_report.py` | Renders the shareable report (text and HTML) |
| `webapp.py` | The local server, security controls, and the launcher |
| `web/index.html` | The single-file chat page (no external requests) |

## Building the downloadable apps

`.github/workflows/build-apps.yml` builds a Windows `.exe` and a macOS `.app` with
PyInstaller whenever a release is published and attaches them to it. You can also run it by
hand from the Actions tab to try a build without releasing. Each build runs the app's
`--self-test` (start the server, load the page, analyze the example) before it is uploaded.

To build locally:

```bash
pip install ".[chat]" pyinstaller
pyinstaller --noconfirm packaging/project-risk-agent.spec
dist/ProjectRiskAgent --self-test    # Windows: dist\ProjectRiskAgent.exe
```

The builds are not code-signed, so Windows SmartScreen and macOS Gatekeeper show a warning on
first launch (the README explains how to proceed). Removing that warning requires a Windows
code-signing certificate and an Apple Developer ID with notarization. Some antivirus tools
also distrust unsigned single-file PyInstaller programs; if that becomes a problem, the
alternative is an installer.
