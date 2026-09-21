"""Turn whatever a non-technical user pastes or uploads into plain updates."""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from email import message_from_string
from email.policy import default as default_policy
from email.utils import parsedate_to_datetime

SUPPORTED_EXTENSIONS = (".txt", ".md", ".csv", ".json", ".eml")

_BULLET = re.compile(r"^\s*(?:[-*•‣▪]|\d{1,3}[.)])\s+")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_TAGS = re.compile(r"<[^>]+>")
_MAX_CHUNK = 600
_TARGET_CHUNK = 400
_MAX_ROWS = 1000
_TEXT_COLUMNS = (
    "update", "content", "text", "message", "description", "summary",
    "comment", "comments", "notes", "note", "status",
)


@dataclass(frozen=True)
class IncomingUpdate:
    """One piece of project information, ready to become a ProjectSignal."""

    text: str
    source_type: str = "text"
    author: str | None = None
    timestamp: datetime | None = None
    filename: str | None = None


def _chunk(piece: str) -> list[str]:
    """Keep updates short enough that evidence quotes stay readable."""
    if len(piece) <= _MAX_CHUNK:
        return [piece]
    chunks: list[str] = []
    current = ""
    for sentence in _SENTENCE_END.split(piece):
        if current and len(current) + len(sentence) + 1 > _TARGET_CHUNK:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def split_updates(text: str) -> list[str]:
    """Split pasted text into individual updates.

    Blank lines separate updates. Bulleted or numbered lines become one update each.
    Hard-wrapped lines inside a paragraph are rejoined into a single update.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    updates: list[str] = []
    for block in re.split(r"\n\s*\n", normalized):
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue
        if len(lines) > 1 and any(_BULLET.match(line) for line in lines):
            pieces = [_BULLET.sub("", line) for line in lines if not line.endswith(":")]
        else:
            pieces = [" ".join(lines)]
        for piece in pieces:
            updates.extend(_chunk(piece.strip()))
    return [update for update in updates if update]


def _parse_time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _from_json(text: str, filename: str) -> list[IncomingUpdate]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("That file isn't valid JSON, so I couldn't read it.") from exc
    if isinstance(data, dict) and isinstance(data.get("signals"), list):
        items = data["signals"]
    elif isinstance(data, list):
        items = data
    else:
        items = [data]
    updates: list[IncomingUpdate] = []
    for item in items:
        author: str | None = None
        timestamp: datetime | None = None
        if isinstance(item, str):
            content = item
        elif isinstance(item, dict):
            content = str(item.get("content") or item.get("text") or item.get("message") or "")
            raw_author = item.get("author")
            author = str(raw_author) if raw_author else None
            timestamp = _parse_time(item.get("timestamp"))
        else:
            continue
        updates.extend(
            IncomingUpdate(piece, "json", author, timestamp, filename) for piece in split_updates(content)
        )
    return updates


def _looks_like_header(row: list[str]) -> bool:
    cells = [cell.strip() for cell in row]
    return bool(cells) and all(cells) and not any(cell.replace(".", "", 1).isdigit() for cell in cells)


def _from_csv(text: str, filename: str) -> list[IncomingUpdate]:
    rows = [row for row in csv.reader(io.StringIO(text)) if any(cell.strip() for cell in row)]
    if not rows:
        raise ValueError("That spreadsheet looks empty.")
    rows = rows[: _MAX_ROWS + 1]
    header = [cell.strip().lower() for cell in rows[0]]
    has_header = len(rows) > 1 and _looks_like_header(rows[0])
    text_column = next((header.index(name) for name in _TEXT_COLUMNS if name in header), None)
    pieces: list[str] = []
    if has_header and text_column is not None:
        pieces = [row[text_column].strip() for row in rows[1:] if text_column < len(row)]
    elif has_header:
        labels = [cell.strip() for cell in rows[0]]
        for row in rows[1:]:
            fields = [f"{label}: {cell.strip()}" for label, cell in zip(labels, row) if cell.strip()]
            pieces.append("; ".join(fields))
    else:
        pieces = [" - ".join(cell.strip() for cell in row if cell.strip()) for row in rows]
    return [
        IncomingUpdate(chunk, "spreadsheet", None, None, filename)
        for piece in pieces
        for chunk in _chunk(piece)
        if chunk
    ]


def _email_body(message) -> str:
    body = message.get_body(preferencelist=("plain", "html"))
    if body is None:
        return ""
    content = body.get_content()
    if body.get_content_type() == "text/html":
        content = _TAGS.sub(" ", content)
    return "\n".join(line for line in content.splitlines() if not line.lstrip().startswith(">"))


def _from_email(text: str, filename: str) -> list[IncomingUpdate]:
    message = message_from_string(text, policy=default_policy)
    subject = str(message["subject"] or "").strip()
    sender = str(message["from"] or "").strip()
    if not subject and not sender:
        return [IncomingUpdate(piece, "text", None, None, filename) for piece in split_updates(text)]
    timestamp: datetime | None = None
    if message["date"]:
        try:
            timestamp = parsedate_to_datetime(str(message["date"]))
        except (TypeError, ValueError):
            timestamp = None
        if timestamp is not None and timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
    body = _email_body(message)
    if not body.strip():
        raise ValueError("I couldn't find any readable text in that email.")
    combined = f"{subject}\n\n{body}" if subject else body
    return [
        IncomingUpdate(piece, "email", sender or None, timestamp, filename)
        for piece in split_updates(combined)
    ]


def parse_upload(filename: str, text: str) -> list[IncomingUpdate]:
    """Read an uploaded file's text into updates. Raises ValueError with a friendly message."""
    lowered = filename.lower()
    if lowered.endswith(".json"):
        return _from_json(text, filename)
    if lowered.endswith(".csv"):
        return _from_csv(text, filename)
    if lowered.endswith(".eml"):
        return _from_email(text, filename)
    if not lowered.endswith(SUPPORTED_EXTENSIONS):
        raise ValueError(
            "I can read .txt, .md, .csv, .json and .eml files. "
            "For Word or PDF documents, copy the text and paste it here."
        )
    return [IncomingUpdate(piece, "document", None, None, filename) for piece in split_updates(text)]
