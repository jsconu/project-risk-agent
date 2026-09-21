"""Local chat app: a small web server plus the page a non-technical user talks to.

The server only listens on 127.0.0.1. Every launch generates a random session token that
must accompany each request, and requests whose Host header is not localhost are refused,
so other websites open in the same browser cannot talk to it.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from collections.abc import Callable
from importlib import resources

from pydantic import BaseModel, Field

from project_risk_agent import __version__
from project_risk_agent.chat import LOCAL_PRIVACY_NOTE, ChatSession
from project_risk_agent.providers import ModelProvider

MAX_MESSAGE_CHARS = 1_000_000
_SECURITY_HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
}
_EXPIRED_PAGE = (
    "<!doctype html><meta charset='utf-8'><title>Project Risk Agent</title>"
    "<body style='font-family:system-ui,sans-serif;max-width:32rem;margin:4rem auto;padding:0 1rem'>"
    "<h1>This link isn't valid any more</h1>"
    "<p>Project Risk Agent creates a new private link each time it starts. "
    "Close this tab and open the app again.</p></body>"
)


class MessageRequest(BaseModel):
    text: str = Field(max_length=MAX_MESSAGE_CHARS)
    filename: str | None = Field(default=None, max_length=255)


def _index_html() -> str:
    return resources.files("project_risk_agent").joinpath("web", "index.html").read_text(encoding="utf-8")


def create_chat_app(
    provider: ModelProvider | None = None,
    *,
    token: str | None = None,
    on_quit: Callable[[], None] | None = None,
    privacy_note: str | None = None,
):
    try:
        from fastapi import Depends, FastAPI, Header, HTTPException
        from fastapi.responses import HTMLResponse
        from starlette.middleware.trustedhost import TrustedHostMiddleware
    except ImportError as exc:  # pragma: no cover - exercised only without the chat extra
        raise RuntimeError("Install the 'chat' extra to run the chat app") from exc

    session_token = token or secrets.token_urlsafe(24)
    session = ChatSession(provider, privacy_note=privacy_note)
    lock = threading.Lock()
    page = _index_html()

    app = FastAPI(
        title="Project Risk Agent chat",
        version=__version__,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])

    def authorized(supplied: str | None) -> bool:
        return supplied is not None and secrets.compare_digest(supplied, session_token)

    def require_token(x_session_token: str | None = Header(default=None)) -> None:
        if not authorized(x_session_token):
            raise HTTPException(status_code=403, detail="Missing or invalid session token")

    @app.get("/", response_class=HTMLResponse)
    def index(t: str | None = None) -> HTMLResponse:
        if not authorized(t):
            return HTMLResponse(_EXPIRED_PAGE, status_code=403, headers=_SECURITY_HEADERS)
        nonce = secrets.token_urlsafe(16)
        policy = (
            f"default-src 'none'; script-src 'nonce-{nonce}'; style-src 'nonce-{nonce}'; "
            "connect-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'; "
            "frame-ancestors 'none'"
        )
        headers = _SECURITY_HEADERS | {"Content-Security-Policy": policy}
        return HTMLResponse(page.replace("__NONCE__", nonce), headers=headers)

    @app.get("/api/session", dependencies=[Depends(require_token)])
    def get_session() -> dict[str, object]:
        with lock:
            return {
                "version": __version__,
                "privacy": session.privacy_note,
                "transcript": session.transcript,
                "suggestions": session.suggestions,
                "max_chars": MAX_MESSAGE_CHARS,
            }

    @app.post("/api/message", dependencies=[Depends(require_token)])
    def post_message(request: MessageRequest) -> dict[str, object]:
        with lock:
            return {"message": session.send(request.text, request.filename)}

    @app.post("/api/reset", dependencies=[Depends(require_token)])
    def reset() -> dict[str, object]:
        nonlocal session
        with lock:
            session = ChatSession(provider, privacy_note=privacy_note)
            return {"transcript": session.transcript, "suggestions": session.suggestions}

    @app.post("/api/quit", dependencies=[Depends(require_token)])
    def quit_app() -> dict[str, str]:
        if on_quit is not None:
            threading.Timer(0.4, on_quit).start()
        return {"status": "stopping"}

    app.state.token = session_token
    return app


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _ensure_standard_streams() -> None:
    """Windowed builds have no console, so stdout/stderr can be None."""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115


def _open_when_ready(server, url: str, open_browser: bool) -> None:
    deadline = time.monotonic() + 30
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.1)
    if server.started and open_browser:
        webbrowser.open(url)


def _self_test(url: str, token: str) -> bool:
    """Exercise the running server the way a browser would; used to verify packaged builds."""
    headers = {"X-Session-Token": token, "Content-Type": "application/json"}
    with urllib.request.urlopen(url, timeout=10) as page:
        if page.status != 200 or b"Project Risk Agent" not in page.read():
            return False
    payload = json.dumps({"text": "Try an example"}).encode("utf-8")
    request = urllib.request.Request(url.split("?")[0] + "api/message", payload, headers)
    with urllib.request.urlopen(request, timeout=10) as reply:
        message = json.load(reply)["message"]
    return any(block["type"] == "finding" for block in message["blocks"])


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="project-risk-agent-chat",
        description="Open the Project Risk Agent chat in your web browser.",
    )
    parser.add_argument("--port", type=int, default=0, help="Port to listen on (default: any free port)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open the browser automatically")
    parser.add_argument("--provider", choices=("deterministic", "openai"), default="deterministic")
    parser.add_argument("--model", help="OpenAI model ID; required with --provider openai")
    parser.add_argument("--self-test", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    _ensure_standard_streams()

    try:
        import uvicorn
    except ImportError:
        print("The chat app needs extra components. Install them with:\n"
              '  pip install "project-risk-agent[chat]"')
        sys.exit(1)

    provider: ModelProvider | None = None
    privacy_note: str | None = None
    if args.provider == "openai":
        from project_risk_agent.providers import openai_provider_from_environment

        provider = openai_provider_from_environment(args.model)
        privacy_note = (
            "Warning: this copy is set up to use an online AI model. Anything you paste is sent to "
            "that service for analysis. Nothing is saved on this computer when you close the app."
        )

    port = args.port or _free_port()
    token = secrets.token_urlsafe(24)
    server_holder: dict[str, object] = {}
    app = create_chat_app(
        provider,
        token=token,
        on_quit=lambda: setattr(server_holder["server"], "should_exit", True),
        privacy_note=privacy_note or LOCAL_PRIVACY_NOTE,
    )
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", log_config=None)
    server = uvicorn.Server(config)
    server_holder["server"] = server
    url = f"http://127.0.0.1:{port}/?t={token}"

    if args.self_test:
        results: list[bool] = []

        def check() -> None:
            while not server.started:
                time.sleep(0.1)
            try:
                results.append(_self_test(url, token))
            except Exception as exc:  # report any failure as a failed self-test
                print(f"Self-test error: {exc!r}")
                results.append(False)
            server.should_exit = True

        threading.Thread(target=check, daemon=True).start()
        server.run()
        print("Self-test passed." if results and results[0] else "Self-test FAILED.")
        sys.exit(0 if results and results[0] else 1)

    print("Project Risk Agent is running.")
    if args.no_browser:
        print("Open this link in your web browser:")
    else:
        print("Your web browser should open in a moment. If it doesn't, open this link:")
    print(f"  {url}")
    print("\nKeep this window open while you use the app. Close it (or press Ctrl+C) to quit.", flush=True)
    threading.Thread(target=_open_when_ready, args=(server, url, not args.no_browser), daemon=True).start()
    try:
        server.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
