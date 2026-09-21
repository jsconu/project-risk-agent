import pytest

from project_risk_agent import chat
from project_risk_agent.chat import (
    CHIP_ACTIONS,
    CHIP_CHANGES,
    CHIP_DECISIONS,
    CHIP_DEPENDENCIES,
    CHIP_EXAMPLE,
    CHIP_READ,
    CHIP_REPORT,
    ChatSession,
)
from project_risk_agent.models import Finding, ProjectSignal


def blocks(message, kind):
    return [block for block in message["blocks"] if block["type"] == kind]


def all_text(message):
    return " ".join(block["text"] for block in blocks(message, "text"))


@pytest.fixture
def session():
    return ChatSession()


@pytest.fixture
def loaded(session):
    session.send(CHIP_EXAMPLE)
    return session


def test_new_session_greets_and_offers_starting_points(session):
    assert session.transcript[0]["role"] == "assistant"
    assert "Project Risk Agent" in all_text(session.transcript[0])
    assert CHIP_EXAMPLE in session.suggestions


def test_example_produces_plain_language_findings_with_quotes(session):
    reply = session.send(CHIP_EXAMPLE)
    cards = blocks(reply, "finding")
    assert len(cards) >= 3
    assert cards[0]["rank"] == 1 and cards[0]["tone"] in {"high", "medium", "low"}
    assert all(card["quotes"] for card in cards)
    titles = {card["title"] for card in cards}
    assert "Schedule risk" in titles
    assert not any("dependency dependency" in title.lower() for title in titles)
    assert "made-up example" in all_text(reply)


def test_pasted_text_is_read_as_updates_not_as_a_command(session):
    reply = session.send("The vendor is blocked and the launch date has slipped again.")
    assert blocks(reply, "finding")
    assert "I read 1 update" in all_text(reply)


def test_update_that_starts_with_a_command_word_but_has_no_question_is_still_an_update(session):
    reply = session.send("Add another engineer to the team, the testing is behind and blocked.")
    assert blocks(reply, "finding")


def test_short_greeting_is_answered_without_being_ingested(session):
    reply = session.send("hello")
    assert not blocks(reply, "finding")
    assert "Hello" in all_text(reply)
    assert session._signals == []


def test_one_or_two_word_messages_ask_for_more_detail(session):
    reply = session.send("test")
    assert "tell me a bit more" in all_text(reply)
    assert session._signals == []


def test_unknown_question_gets_a_helpful_fallback(session):
    reply = session.send("Is the moon made of cheese?")
    assert "not sure how to answer" in all_text(reply)


def test_follow_up_questions_before_any_updates_point_to_the_example(session):
    reply = session.send(CHIP_DECISIONS)
    assert "haven't read any updates" in all_text(reply)
    assert CHIP_EXAMPLE in reply["suggestions"]


def test_decisions_show_readiness_and_missing_owner_or_deadline(loaded):
    reply = loaded.send(CHIP_DECISIONS)
    items = blocks(reply, "items")[0]["items"]
    labels = {item["label"] for item in items}
    assert "Ready to decide" in labels
    assert "Needs an owner and a deadline" in labels
    ready = next(item for item in items if item["label"] == "Ready to decide")
    assert "Owner: sponsor" in ready["detail"] and "Deadline: Friday" in ready["detail"]


def test_dependencies_are_listed_with_status_and_source(loaded):
    reply = loaded.send(CHIP_DEPENDENCIES)
    items = blocks(reply, "items")[0]["items"]
    assert items[0]["label"] == "Blocked"
    assert "Update 2" in items[0]["detail"]


def test_next_steps_are_deduplicated_and_framed_as_suggestions(loaded):
    reply = loaded.send(CHIP_ACTIONS)
    actions = [item["text"] for item in blocks(reply, "items")[0]["items"]]
    assert actions and len(actions) == len(set(actions))
    assert "not instructions" in all_text(reply)


def test_report_is_plain_text_plus_a_downloadable_html_file_with_friendly_labels(loaded):
    reply = loaded.send(CHIP_REPORT)
    document = blocks(reply, "document")[0]
    assert document["filename"].startswith("project-risk-report-") and document["filename"].endswith(".html")
    for version in (document["text"], document["html"]):
        assert "update-" not in version
        assert "Schedule risk" in version and "Update 1" in version
        assert "dependency dependency" not in version.lower()
    assert "**" not in document["text"] and "#" not in document["text"]
    assert document["html"].startswith("<!doctype html>")
    assert "Ready to decide" in document["text"] and "Blocked" in document["text"]


def test_report_html_escapes_pasted_content(session):
    session.send("<script>alert(1)</script> the vendor delivery is delayed and blocked.")
    document = blocks(session.send(CHIP_REPORT), "document")[0]
    assert "<script>" not in document["html"]
    assert "&lt;script&gt;" in document["html"]


def test_what_did_you_read_lists_each_update(loaded):
    reply = loaded.send(CHIP_READ)
    assert len(blocks(reply, "items")[0]["items"]) == 4


def test_changes_before_a_second_analysis_explains_nothing_to_compare(loaded):
    reply = loaded.send(CHIP_CHANGES)
    assert "nothing to compare yet" in all_text(reply)


def test_adding_updates_combines_them_and_reports_what_changed(loaded):
    reply = loaded.send("QA: a critical defect was found and we are behind schedule on fixes.")
    assert "5 in total" in all_text(reply)
    assert "Compared with the last time I looked" in all_text(reply)
    assert CHIP_CHANGES in reply["suggestions"]
    changes = loaded.send(CHIP_CHANGES)
    assert blocks(changes, "items")[0]["items"]


def test_pasting_the_same_text_twice_does_not_duplicate_updates(loaded):
    loaded.send("Finance: The vendor invoice is 15% over budget and we are waiting for a change request approval.")
    assert len(loaded._signals) == 4


def test_pasting_only_known_updates_says_so(loaded):
    reply = loaded.send("Testing team: UAT cannot start until the API is available, so the test plan is now blocked.")
    assert "already read all of that" in all_text(reply)


def test_start_over_clears_updates_and_comparison_history(loaded):
    reply = loaded.send("Start over")
    assert "cleared everything" in all_text(reply)
    assert loaded._signals == [] and loaded._result is None
    again = loaded.send(CHIP_EXAMPLE)
    assert "in total" not in all_text(again)


def test_no_findings_reply_is_honest_about_limits(session):
    reply = session.send("The team had lunch together and everyone enjoyed the sunny weather today.")
    assert not blocks(reply, "finding")
    assert "doesn't mean everything is fine" in all_text(reply)


def test_only_top_findings_shown_with_option_to_see_everything(session):
    many = "\n\n".join(
        f"Item {i}: the vendor {category} is delayed and blocked."
        for i, category in enumerate(["alpha", "beta", "gamma"])
    )
    session.send(many)
    text = "\n\n".join([
        "The budget is over and we need approval to fund it.",
        "The team is understaffed and has no capacity.",
        "There is a critical defect and a failed test.",
        "Scope creep: requirements changed again.",
        "The customer escalation needs a decision by Monday.",
        "There was an outage in production.",
    ])
    reply = session.send(text)
    cards = blocks(reply, "finding")
    assert len(cards) <= chat.TOP_FINDINGS
    if len(session._result.findings) > chat.TOP_FINDINGS:
        assert "Show everything" in reply["suggestions"]
        everything = session.send("Show everything")
        assert len(blocks(everything, "finding")) == len(session._result.findings)


def test_file_upload_reports_the_file_name_and_reads_updates(session):
    reply = session.send("The API delivery is delayed.\n\nUAT is blocked.", filename="notes.txt")
    assert "I read notes.txt and found 2 updates" in all_text(reply)
    assert session.transcript[-2]["filename"] == "notes.txt"
    assert session.transcript[-2]["text"] == ""


def test_unsupported_upload_explains_what_to_do(session):
    reply = session.send("binary", filename="plan.docx")
    assert "copy the text and paste it" in all_text(reply)


def test_user_messages_keep_only_a_preview_in_the_transcript(session):
    session.send("The vendor is delayed. " * 200)
    user = next(m for m in session.transcript if m["role"] == "user")
    assert len(user["text"]) == chat.PREVIEW_CHARS
    assert user["chars"] > chat.PREVIEW_CHARS


def test_old_evidence_is_flagged_as_old(session):
    payload = '[{"content": "The vendor delivery is delayed and blocked.", "timestamp": "2020-01-01T00:00:00Z"}]'
    reply = session.send(payload, filename="old.json")
    card = blocks(reply, "finding")[0]
    assert "days old" in card["freshness_note"]


class FailingProvider:
    def analyze(self, signals):
        raise RuntimeError("model unavailable")


def test_provider_failures_are_reported_kindly_and_do_not_lose_earlier_updates():
    session = ChatSession()
    session.send(CHIP_EXAMPLE)
    session._service.provider = FailingProvider()
    reply = session.send("A brand new delayed and blocked update arrived today.")
    assert "Something went wrong" in all_text(reply)
    assert "RuntimeError" in all_text(reply)
    assert "model unavailable" not in all_text(reply)
    assert len(session._signals) == 4


class RecordingProvider:
    def __init__(self):
        self.seen = []

    def analyze(self, signals):
        self.seen.append([signal.id for signal in signals])
        return [
            Finding(
                id="f1", type="risk", category="vendor", title="t", description="d",
                confidence=0.9,
                evidence=[{"signal_id": signals[0].id, "excerpt": signals[0].content}],
            )
        ]


def test_a_custom_provider_is_used_and_privacy_note_can_be_overridden():
    provider = RecordingProvider()
    session = ChatSession(provider, privacy_note="Sent to a remote service.")
    session.send("Anything about the project goes here, it is fine.")
    assert provider.seen and session.privacy_note == "Sent to a remote service."


def test_signal_ids_are_stable_across_sessions():
    first, second = ChatSession(), ChatSession()
    first.send("The vendor delivery is delayed again this week.")
    second.send("The vendor  delivery is delayed AGAIN this week.")
    assert [s.id for s in first._signals] == [s.id for s in second._signals]
    assert isinstance(first._signals[0], ProjectSignal)
