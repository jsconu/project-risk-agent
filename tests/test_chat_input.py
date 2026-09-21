import json

import pytest

from project_risk_agent.chat_input import parse_upload, split_updates


def test_blank_lines_separate_updates_and_wrapped_lines_are_rejoined():
    text = "The API is late\nand still not ready.\n\n\nTesting is blocked."
    assert split_updates(text) == ["The API is late and still not ready.", "Testing is blocked."]


def test_bulleted_lines_become_separate_updates_and_headers_are_dropped():
    text = "Status:\n- Vendor is late\n* Budget is over\n1. Team is understaffed"
    assert split_updates(text) == ["Vendor is late", "Budget is over", "Team is understaffed"]


def test_windows_line_endings_are_handled():
    assert split_updates("One update.\r\n\r\nTwo update.") == ["One update.", "Two update."]


def test_long_paragraphs_are_split_at_sentence_boundaries():
    sentence = "The vendor has not confirmed the delivery date yet. "
    pieces = split_updates(sentence * 30)
    assert len(pieces) > 1
    assert all(len(piece) <= 600 for piece in pieces)
    assert all(piece.endswith(".") for piece in pieces)


def test_empty_text_yields_no_updates():
    assert split_updates("  \n\n  ") == []


def test_plain_text_upload_is_split_into_updates():
    updates = parse_upload("notes.txt", "First note.\n\nSecond note.")
    assert [u.text for u in updates] == ["First note.", "Second note."]
    assert {u.filename for u in updates} == {"notes.txt"}


def test_json_upload_accepts_signal_files_and_keeps_author_and_time():
    payload = {
        "signals": [
            {"content": "API moved to Friday.", "author": "Sam", "timestamp": "2026-01-05T10:00:00Z"},
            {"content": "UAT is blocked."},
        ]
    }
    updates = parse_upload("signals.json", json.dumps(payload))
    assert [u.text for u in updates] == ["API moved to Friday.", "UAT is blocked."]
    assert updates[0].author == "Sam"
    assert updates[0].timestamp is not None and updates[0].timestamp.year == 2026
    assert updates[1].timestamp is None


def test_json_upload_accepts_plain_list_of_strings():
    updates = parse_upload("list.json", json.dumps(["One.", "Two."]))
    assert [u.text for u in updates] == ["One.", "Two."]


def test_invalid_json_gives_a_friendly_error():
    with pytest.raises(ValueError, match="isn't valid JSON"):
        parse_upload("bad.json", "{not json")


def test_csv_with_a_text_column_uses_that_column():
    csv_text = "id,owner,status\n1,Sam,Vendor is late\n2,Ana,Budget is over\n"
    updates = parse_upload("export.csv", csv_text)
    assert [u.text for u in updates] == ["Vendor is late", "Budget is over"]


def test_csv_without_a_text_column_labels_each_field():
    csv_text = "Task,Owner,Blocker\nAPI,Sam,Waiting for vendor\n"
    updates = parse_upload("tasks.csv", csv_text)
    assert updates[0].text == "Task: API; Owner: Sam; Blocker: Waiting for vendor"


def test_empty_csv_gives_a_friendly_error():
    with pytest.raises(ValueError, match="looks empty"):
        parse_upload("empty.csv", "\n\n")


def test_email_upload_reads_subject_body_sender_and_date_and_skips_quoted_replies():
    eml = (
        "From: Sam <sam@example.com>\n"
        "Subject: API delivery slipped\n"
        "Date: Mon, 05 Jan 2026 10:00:00 +0000\n"
        "Content-Type: text/plain; charset=utf-8\n\n"
        "The vendor moved the API date again.\n\n"
        "> older quoted text that should be ignored\n"
    )
    updates = parse_upload("mail.eml", eml)
    texts = [u.text for u in updates]
    assert texts == ["API delivery slipped", "The vendor moved the API date again."]
    assert updates[0].author == "Sam <sam@example.com>"
    assert updates[0].timestamp is not None and updates[0].timestamp.year == 2026
    assert updates[0].source_type == "email"


def test_eml_without_headers_is_treated_as_plain_text():
    updates = parse_upload("notes.eml", "Just some notes about a delay.")
    assert [u.text for u in updates] == ["Just some notes about a delay."]


def test_unsupported_file_types_explain_what_to_do():
    with pytest.raises(ValueError, match="copy the text and paste it"):
        parse_upload("plan.docx", "binary")
