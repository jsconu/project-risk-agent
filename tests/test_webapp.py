import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from project_risk_agent.webapp import MAX_MESSAGE_CHARS, create_chat_app  # noqa: E402

TOKEN = "test-token-value"
AUTH = {"X-Session-Token": TOKEN}


@pytest.fixture
def client():
    return TestClient(create_chat_app(token=TOKEN), base_url="http://127.0.0.1:8123")


def test_page_requires_the_session_token(client):
    assert client.get("/").status_code == 403
    assert client.get("/", params={"t": "wrong"}).status_code == 403
    page = client.get("/", params={"t": TOKEN})
    assert page.status_code == 200
    assert "Project Risk Agent" in page.text


def test_expired_link_page_explains_what_to_do(client):
    page = client.get("/")
    assert "isn't valid any more" in page.text


def test_page_is_served_with_a_strict_nonce_based_csp_and_no_external_requests(client):
    response = client.get("/", params={"t": TOKEN})
    policy = response.headers["content-security-policy"]
    nonce = policy.split("script-src 'nonce-")[1].split("'")[0]
    assert f'nonce="{nonce}"' in response.text
    assert "__NONCE__" not in response.text
    assert "default-src 'none'" in policy and "frame-ancestors 'none'" in policy
    assert "http://" not in response.text and "https://" not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-frame-options"] == "DENY"


def test_each_page_load_gets_a_fresh_nonce(client):
    first = client.get("/", params={"t": TOKEN}).headers["content-security-policy"]
    second = client.get("/", params={"t": TOKEN}).headers["content-security-policy"]
    assert first != second


@pytest.mark.parametrize(
    ("method", "path"),
    [("get", "/api/session"), ("post", "/api/message"), ("post", "/api/reset"), ("post", "/api/quit")],
)
def test_api_rejects_missing_or_wrong_token(client, method, path):
    kwargs = {"json": {"text": "hi"}} if path == "/api/message" else {}
    assert getattr(client, method)(path, **kwargs).status_code == 403
    assert getattr(client, method)(path, headers={"X-Session-Token": "nope"}, **kwargs).status_code == 403


def test_requests_with_a_foreign_host_header_are_refused():
    app = create_chat_app(token=TOKEN)
    rebound = TestClient(app, base_url="http://evil.example.com")
    assert rebound.get("/", params={"t": TOKEN}).status_code == 400
    assert rebound.get("/api/session", headers=AUTH).status_code == 400


def test_localhost_hostname_is_allowed():
    client = TestClient(create_chat_app(token=TOKEN), base_url="http://localhost:8123")
    assert client.get("/api/session", headers=AUTH).status_code == 200


def test_no_cross_origin_access_is_granted(client):
    response = client.options(
        "/api/message",
        headers={"Origin": "https://evil.example.com", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in response.headers


def test_api_docs_are_not_exposed(client):
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path, headers=AUTH).status_code == 404


def test_session_starts_with_a_welcome_and_privacy_note(client):
    body = client.get("/api/session", headers=AUTH).json()
    assert body["transcript"][0]["role"] == "assistant"
    assert "stays on this computer" in body["privacy"]
    assert "Try an example" in body["suggestions"]
    assert body["max_chars"] == MAX_MESSAGE_CHARS


def test_message_round_trip_returns_findings_and_persists_the_transcript(client):
    reply = client.post("/api/message", headers=AUTH, json={"text": "Try an example"})
    assert reply.status_code == 200
    message = reply.json()["message"]
    assert any(block["type"] == "finding" for block in message["blocks"])
    transcript = client.get("/api/session", headers=AUTH).json()["transcript"]
    assert [m["role"] for m in transcript] == ["assistant", "user", "assistant"]


def test_file_upload_is_read_through_the_same_endpoint(client):
    reply = client.post(
        "/api/message",
        headers=AUTH,
        json={"text": "The API is delayed.\n\nUAT is blocked.", "filename": "notes.txt"},
    )
    text = " ".join(b["text"] for b in reply.json()["message"]["blocks"] if b["type"] == "text")
    assert "notes.txt" in text


def test_oversized_messages_are_rejected(client):
    reply = client.post("/api/message", headers=AUTH, json={"text": "x" * (MAX_MESSAGE_CHARS + 1)})
    assert reply.status_code == 422


def test_reset_starts_a_fresh_conversation(client):
    client.post("/api/message", headers=AUTH, json={"text": "Try an example"})
    state = client.post("/api/reset", headers=AUTH).json()
    assert len(state["transcript"]) == 1
    again = client.post("/api/message", headers=AUTH, json={"text": "What decisions are needed?"})
    text = " ".join(b["text"] for b in again.json()["message"]["blocks"] if b["type"] == "text")
    assert "haven't read any updates" in text


def test_quit_calls_the_shutdown_hook():
    import threading

    stopped = threading.Event()
    client = TestClient(
        create_chat_app(token=TOKEN, on_quit=stopped.set), base_url="http://127.0.0.1:8123"
    )
    assert client.post("/api/quit", headers=AUTH).json() == {"status": "stopping"}
    assert stopped.wait(timeout=3)
