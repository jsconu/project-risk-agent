"""A conversational front end over the risk engine, written for non-technical users."""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime, timedelta
from hashlib import sha256

from project_risk_agent.analyzer import RiskAnalyzer
from project_risk_agent.chat_input import IncomingUpdate, parse_upload, split_updates
from project_risk_agent.chat_report import render_html, render_text
from project_risk_agent.models import Finding, FindingType, ProjectSignal
from project_risk_agent.prioritizer import attention_score, prioritize
from project_risk_agent.providers import DeterministicProvider, ModelProvider
from project_risk_agent.service import AnalysisResult, RiskAnalysisService
from project_risk_agent.state import ProjectSnapshot

logger = logging.getLogger(__name__)

MAX_UPDATES = 1000
TOP_FINDINGS = 5
PREVIEW_CHARS = 600

LOCAL_PRIVACY_NOTE = (
    "Everything stays on this computer. Nothing you paste is sent anywhere, "
    "and nothing is saved when you close the app."
)

EXAMPLE_UPDATES = """\
Status update (Monday): The API delivery from the vendor moved from Tuesday to Friday. \
This is the second delivery-date change this month.

Testing team: UAT cannot start until the API is available, so the test plan is now blocked.

Engineering lead: We are still on track for the overall launch, but the test environment \
has been unstable and we need a decision on whether to add another engineer. \
The sponsor should approve by Friday.

Finance: The vendor invoice is 15% over budget and we are waiting for a change request approval.
"""

_TYPE_LABELS = {
    FindingType.RISK: "Risk",
    FindingType.ISSUE: "Issue",
    FindingType.DEPENDENCY: "Dependency",
    FindingType.DECISION: "Decision",
}
_TYPE_HELP = {
    FindingType.RISK: "Something that might go wrong",
    FindingType.ISSUE: "Something that is already going wrong",
    FindingType.DEPENDENCY: "Work that is waiting on something else",
    FindingType.DECISION: "Someone needs to make a call",
}
_READINESS = {
    "ready": ("Ready to decide", "ok"),
    "missing_owner": ("Needs an owner", "warn"),
    "missing_deadline": ("Needs a deadline", "warn"),
    "missing_owner_and_deadline": ("Needs an owner and a deadline", "warn"),
}
_DEPENDENCY_STATUS = {"blocked": ("Blocked", "bad"), "waiting": ("Waiting", "warn"), "at_risk": ("At risk", "warn")}
_TRAJECTORY_LABELS = {
    "new": "New since last time",
    "deteriorating": "Getting worse",
    "improving": "Improving",
    "persistent": "Still open",
    "stale": "Based on old information",
}

CHIP_HELP = "How does this work?"
CHIP_EXAMPLE = "Try an example"
CHIP_PASTE = "What can I paste?"
CHIP_DECISIONS = "What decisions are needed?"
CHIP_DEPENDENCIES = "What is blocked or waiting?"
CHIP_ACTIONS = "What should I do next?"
CHIP_REPORT = "Give me a report I can share"
CHIP_ADD = "Add more updates"
CHIP_CHANGES = "What changed since last time?"
CHIP_READ = "What did you read?"
CHIP_ALL = "Show everything"
CHIP_RESET = "Start over"

_COMMAND_WORDS = re.compile(
    r"^(what|which|who|when|where|why|how|show|list|give|tell|explain|help|reset|start|clear|"
    r"download|copy|export|try|add|are there|is there|do you|can you|could you|please|"
    r"thanks|thank you|thx|hi|hello|hey)\b",
    re.IGNORECASE,
)
_INTENTS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (name, re.compile(pattern, re.IGNORECASE))
    for name, pattern in (
        ("reset", r"\b(start over|start again|reset|clear (?:everything|all|it)|new project|begin again)\b"),
        ("example", r"\b(example|sample|demo)\b"),
        ("read", r"\bwhat (?:did|have) you read\b|\bshow (?:me )?(?:my |the )?updates\b"),
        ("add", r"^\s*(?:add|paste|upload|attach)\s+(?:some\s+)?(?:more|another|new)?\s*(?:updates?|files?|notes?)\b"),
        ("help", r"\b(help|how does (?:this|it) work|how do i|what can (?:i|you)|what do you do|get started|how to)\b"),
        ("report", r"\b(report|brief|export|download|copy|share)\b"),
        ("decisions", r"\b(decisions?|decide|sign[- ]?off|approvals?|approve)\b"),
        ("dependencies", r"\b(depend\w*|blocked|blockers?|blocking|waiting)\b"),
        ("changes", r"\b(what changed|changes|new since|since last|trend|getting worse|improv\w*)\b"),
        ("actions", r"\b(next steps?|what should i do|what do i do|actions?|recommend\w*|to do)\b"),
        ("all", r"\b(everything|show all|full list|all (?:the )?(?:findings|risks|issues))\b"),
        ("evidence", r"\b(evidence|proof|why|sources?)\b"),
        ("top", r"\b(top|biggest|most important|priorit\w*|urgent|worr\w*|summary|overview|risks|issues|concerns|attention)\b"),
        ("greeting", r"^\s*(?:hi|hello|hey|thanks|thank you|thx)\b"),
    )
)


class InMemoryProjectStateStore:
    """Holds the previous analysis for this conversation only; nothing touches the disk."""

    def __init__(self) -> None:
        self._snapshot: ProjectSnapshot | None = None

    def load(self) -> ProjectSnapshot | None:
        return self._snapshot

    def save(self, snapshot: ProjectSnapshot) -> None:
        self._snapshot = snapshot


def _plural(count: int, word: str, plural: str | None = None) -> str:
    return f"{count} {word if count == 1 else (plural or word + 's')}"


def _signal_id(text: str) -> str:
    normalized = " ".join(text.lower().split())
    return "update-" + sha256(normalized.encode("utf-8")).hexdigest()[:10]


def _text(text: str, style: str = "plain") -> dict[str, object]:
    return {"type": "text", "text": text, "style": style}


def _message(blocks: list[dict[str, object]], suggestions: list[str]) -> dict[str, object]:
    return {"role": "assistant", "blocks": blocks, "suggestions": suggestions}


def _looks_like_command(text: str) -> bool:
    """Questions and short imperatives are commands; anything longer is an update to read."""
    stripped = text.strip()
    words = len(stripped.split())
    if "\n" in stripped or words > 20:
        return False
    if stripped.endswith("?"):
        return True
    return words <= 8 and bool(_COMMAND_WORDS.match(stripped))


def _confidence_label(confidence: float) -> str:
    return "High" if confidence >= 0.8 else "Medium" if confidence >= 0.6 else "Low"


def _plain_title(finding: Finding) -> str:
    """Describe a finding in everyday words; the engine's own titles read awkwardly in a chat."""
    area = "General" if finding.category.value == "other" else finding.category.value.capitalize()
    if finding.type == FindingType.RISK:
        return f"{area} risk"
    if finding.type == FindingType.ISSUE:
        return f"{area} problem"
    if finding.type == FindingType.DEPENDENCY:
        return "Work is waiting on something else"
    return "A decision is needed"


class ChatSession:
    """One conversation: the updates shared so far, the latest analysis, and the transcript."""

    def __init__(self, provider: ModelProvider | None = None, privacy_note: str | None = None) -> None:
        self._service = RiskAnalysisService(provider or DeterministicProvider(RiskAnalyzer()))
        self.privacy_note = privacy_note or LOCAL_PRIVACY_NOTE
        self._store = InMemoryProjectStateStore()
        self._signals: list[ProjectSignal] = []
        self._labels: dict[str, int] = {}
        self._result: AnalysisResult | None = None
        self._analyses = 0
        self.transcript: list[dict[str, object]] = []
        self._add_assistant(self._welcome())

    @property
    def suggestions(self) -> list[str]:
        for message in reversed(self.transcript):
            if message["role"] == "assistant":
                return list(message["suggestions"])  # type: ignore[arg-type]
        return []

    def send(self, text: str, filename: str | None = None) -> dict[str, object]:
        """Handle one user turn and return the assistant's reply message."""
        text = text.strip()
        shown = "" if filename else text[:PREVIEW_CHARS]
        self.transcript.append(
            {"role": "user", "text": shown, "chars": len(text), "filename": filename}
        )
        reply = self._route(text, filename)
        self._add_assistant(reply)
        return reply

    def _add_assistant(self, message: dict[str, object]) -> None:
        self.transcript.append(message)

    def _welcome(self) -> dict[str, object]:
        return _message(
            [
                _text("Hi, I'm Project Risk Agent."),
                _text(
                    "I read your project updates and point out what may need a manager's attention: "
                    "risks, problems, work that is waiting on something, and decisions that are stuck."
                ),
                _text(
                    "To start, paste some updates below (status reports, emails, meeting notes, chat "
                    "messages) or drop a file into this window. I'll list what looks important and quote "
                    "the exact words I based it on. Then you can ask me follow-up questions."
                ),
                _text("Not sure where to begin? Try the example and see how it works.", "note"),
            ],
            [CHIP_EXAMPLE, CHIP_PASTE, CHIP_HELP],
        )

    def _route(self, text: str, filename: str | None) -> dict[str, object]:
        if filename:
            try:
                updates = parse_upload(filename, text)
            except ValueError as exc:
                return _message([_text(str(exc))], self._next_suggestions())
            return self._ingest(updates, source=filename)
        if not text:
            return _message([_text("I didn't get any text. Paste an update and I'll take a look.")], self._next_suggestions())
        intent = self._detect_intent(text)
        if intent:
            return self._handle_intent(intent)
        if text.endswith("?"):
            return self._unsure()
        if len(text.split()) <= 2:
            return _message(
                [_text("Could you tell me a bit more? Paste a status update, an email, or meeting notes and I'll read it.")],
                self._next_suggestions(),
            )
        return self._ingest([IncomingUpdate(piece, filename=None) for piece in split_updates(text)])

    @staticmethod
    def _detect_intent(text: str) -> str | None:
        if not _looks_like_command(text):
            return None
        return next((name for name, pattern in _INTENTS if pattern.search(text)), None)

    def _handle_intent(self, intent: str) -> dict[str, object]:
        if intent == "reset":
            return self._reset()
        if intent == "example":
            return self._ingest(
                [IncomingUpdate(piece, "example") for piece in split_updates(EXAMPLE_UPDATES)],
                intro="This is a made-up example.",
            )
        if intent == "help":
            return self._help()
        if intent == "greeting":
            return _message([_text("Hello! Paste some project updates and I'll take a look.")], self._next_suggestions())
        if intent == "add":
            return _message(
                [_text("Sure. Paste more updates below, or drop another file into this window. I'll combine them with what I've already read.")],
                self._next_suggestions(),
            )
        if self._result is None or not self._signals:
            return _message(
                [_text("I haven't read any updates yet. Paste some in, or try the example first.")],
                [CHIP_EXAMPLE, CHIP_PASTE, CHIP_HELP],
            )
        handlers = {
            "read": self._what_i_read,
            "report": self._report,
            "decisions": self._decisions,
            "dependencies": self._dependencies,
            "changes": self._changes,
            "actions": self._actions,
            "all": lambda: self._findings_reply(prioritize(self._result.findings), limit=None),
            "evidence": self._evidence,
            "top": lambda: self._findings_reply(prioritize(self._result.findings), limit=TOP_FINDINGS),
        }
        return handlers[intent]()

    def _reset(self) -> dict[str, object]:
        self._store = InMemoryProjectStateStore()
        self._signals = []
        self._labels = {}
        self._result = None
        self._analyses = 0
        return _message(
            [_text("Okay, I've cleared everything. Paste new updates whenever you're ready.")],
            [CHIP_EXAMPLE, CHIP_PASTE, CHIP_HELP],
        )

    def _help(self) -> dict[str, object]:
        return _message(
            [
                _text("Here's how this works."),
                _text(
                    "1. Paste updates (status reports, emails, meeting notes, chat messages) or drop a "
                    "file: .txt, .md, .csv, .json or .eml. For Word or PDF files, copy the text and paste it.\n"
                    "2. I list what may need attention, most important first, and quote the exact words "
                    "I based each item on.\n"
                    "3. Ask follow-ups such as \"What decisions are needed?\" or \"What is blocked?\". "
                    "You can keep adding updates and I'll combine them."
                ),
                _text(
                    "Good to know: I look for common warning language such as delays, blockers, missing "
                    "owners and pending approvals. I can miss things phrased in unusual ways, and I don't "
                    "know your project's context. Treat my list as a starting point for a conversation, "
                    "not a verdict. I never make decisions for you.",
                    "note",
                ),
                _text(self.privacy_note, "note"),
            ],
            self._next_suggestions(),
        )

    def _unsure(self) -> dict[str, object]:
        return _message(
            [
                _text(
                    "I'm not sure how to answer that one. I can tell you what needs attention, "
                    "which decisions are pending, what is blocked or waiting, and what to do next. "
                    "Or paste more updates and I'll read them."
                )
            ],
            self._next_suggestions(),
        )

    def _next_suggestions(self) -> list[str]:
        result = self._result
        if result is None or not self._signals:
            return [CHIP_EXAMPLE, CHIP_PASTE, CHIP_HELP]
        chips: list[str] = []
        if result.findings:
            wants_decision = result.decision_requests or any(f.decision_required for f in result.findings)
            if wants_decision:
                chips.append(CHIP_DECISIONS)
            if result.dependencies:
                chips.append(CHIP_DEPENDENCIES)
            chips.append(CHIP_ACTIONS)
            if len(result.findings) > TOP_FINDINGS:
                chips.append(CHIP_ALL)
            chips.append(CHIP_REPORT)
        if self._analyses >= 2:
            chips.append(CHIP_CHANGES)
        chips.extend([CHIP_ADD, CHIP_READ, CHIP_RESET])
        return chips[:6]

    def _label(self, signal_id: str) -> str:
        number = self._labels.get(signal_id)
        return f"Update {number}" if number else "Update"

    def _ingest(
        self,
        updates: list[IncomingUpdate],
        intro: str | None = None,
        source: str | None = None,
    ) -> dict[str, object]:
        if not updates:
            return _message(
                [_text("I couldn't find any text to read there. Try pasting the updates directly.")],
                self._next_suggestions(),
            )
        known = {signal.id for signal in self._signals}
        base = datetime.now(UTC)
        fresh: list[ProjectSignal] = []
        skipped = 0
        for offset, update in enumerate(updates):
            signal_id = _signal_id(update.text)
            if signal_id in known:
                skipped += 1
                continue
            known.add(signal_id)
            provenance: dict[str, object] = {"connector": "chat"}
            if update.filename:
                provenance["filename"] = update.filename
            fresh.append(
                ProjectSignal(
                    id=signal_id,
                    source="chat",
                    source_type=update.source_type,
                    timestamp=update.timestamp or base + timedelta(microseconds=offset),
                    author=update.author,
                    content=update.text,
                    provenance=provenance,
                )
            )
        if not fresh:
            return _message(
                [_text("I've already read all of that. Paste something new, or ask me a question about what I found.")],
                self._next_suggestions(),
            )
        if len(self._signals) + len(fresh) > MAX_UPDATES:
            return _message(
                [_text(f"That's more than I can hold at once (the limit is {MAX_UPDATES} updates). Start over, or share a smaller batch.")],
                self._next_suggestions(),
            )
        candidate = self._signals + fresh
        try:
            result = self._service.analyze_with_state(candidate, self._store)
        except Exception as exc:  # the provider may be a remote model
            logger.exception("Analysis failed")
            return _message(
                [_text(f"Something went wrong while I was analyzing that ({type(exc).__name__}). Your earlier updates are still here. Please try again.")],
                self._next_suggestions(),
            )
        self._signals = candidate
        self._result = result
        self._analyses += 1
        for signal in fresh:
            self._labels[signal.id] = len(self._labels) + 1

        blocks: list[dict[str, object]] = []
        noun = _plural(len(fresh), "new update" if self._analyses > 1 else "update")
        read = f"I read {source} and found {noun} in it" if source else f"I read {noun}"
        if skipped:
            read += f" ({skipped} I'd already seen)"
        read += f", {len(self._signals)} in total." if self._analyses > 1 else "."
        blocks.append(_text(f"{intro} {read}" if intro else read))
        blocks.extend(self._findings_blocks(prioritize(result.findings), TOP_FINDINGS))
        return _message(blocks, self._next_suggestions())

    def _summary_line(self, findings: list[Finding]) -> str:
        counts = {kind: sum(f.type == kind for f in findings) for kind in FindingType}
        parts = [
            _plural(counts[kind], _TYPE_LABELS[kind].lower())
            for kind in (FindingType.RISK, FindingType.ISSUE, FindingType.DEPENDENCY, FindingType.DECISION)
            if counts[kind]
        ]
        return ", ".join(parts)

    def _findings_blocks(self, findings: list[Finding], limit: int | None) -> list[dict[str, object]]:
        if not findings:
            return [
                _text(
                    "I didn't find anything that looks like a risk, problem, dependency or pending decision. "
                    "That doesn't mean everything is fine: I only look for common warning language, so "
                    "try adding more detailed updates."
                )
            ]
        shown = findings if limit is None else findings[:limit]
        blocks: list[dict[str, object]] = [
            _text(
                f"Here's what may need attention ({self._summary_line(findings)}), most important first."
            )
        ]
        if self._analyses >= 2 and self._result is not None:
            change = self._change_summary()
            if change:
                blocks.append(_text(change, "note"))
        blocks.extend(self._finding_card(rank, finding) for rank, finding in enumerate(shown, start=1))
        if len(shown) < len(findings):
            hidden = len(findings) - len(shown)
            blocks.append(_text(f"Showing the {len(shown)} most important. There are {_plural(hidden, 'more item')}. Ask me to \"show everything\" to see them all.", "note"))
        return blocks

    def _findings_reply(self, findings: list[Finding], limit: int | None) -> dict[str, object]:
        return _message(self._findings_blocks(findings, limit), self._next_suggestions())

    def _finding_card(self, rank: int, finding: Finding) -> dict[str, object]:
        result = self._result
        score = attention_score(finding)
        tone = "high" if score >= 55 else "medium" if score >= 40 else "low"
        quotes: list[dict[str, str]] = []
        seen: set[str] = set()
        for evidence in finding.evidence:
            key = " ".join(evidence.excerpt.split())
            if key in seen:
                continue
            seen.add(key)
            quotes.append({"source": self._label(evidence.signal_id), "quote": evidence.excerpt})
        only_quote = len(quotes) == 1 and " ".join(finding.description.split()) == " ".join(quotes[0]["quote"].split())
        levels = [
            {"name": name, "value": value.capitalize()}
            for name, value in (
                ("Likelihood", finding.likelihood),
                ("Impact", finding.impact),
                ("Urgency", finding.urgency),
            )
            if value
        ]
        status: str | None = None
        freshness_note: str | None = None
        if result is not None:
            if self._analyses >= 2:
                trajectory = result.trajectory_for(finding.id)
                status = _TRAJECTORY_LABELS.get(trajectory.state) if trajectory else None
            freshness = result.freshness_for(finding.id)
            if freshness and freshness.status in ("aging", "stale") and freshness.age_days is not None:
                freshness_note = f"The latest information behind this is about {int(freshness.age_days)} days old."
        return {
            "type": "finding",
            "rank": rank,
            "tone": tone,
            "kind": _TYPE_LABELS[finding.type],
            "kind_help": _TYPE_HELP[finding.type],
            "category": finding.category.value.capitalize(),
            "title": _plain_title(finding),
            "summary": None if only_quote else finding.description,
            "levels": levels,
            "confidence": _confidence_label(finding.confidence),
            "decision_required": finding.decision_required,
            "status": status,
            "freshness_note": freshness_note,
            "quotes": quotes[:4],
            "more_quotes": max(0, len(quotes) - 4),
            "actions": list(finding.recommended_actions),
        }

    def _change_summary(self) -> str | None:
        result = self._result
        if result is None:
            return None
        states = [t.state for t in result.trajectories if t.state in _TRAJECTORY_LABELS]
        if not states:
            return None
        counts = {state: states.count(state) for state in _TRAJECTORY_LABELS}
        parts = [
            f"{counts[state]} {label.lower()}"
            for state, label in _TRAJECTORY_LABELS.items()
            if counts[state]
        ]
        return "Compared with the last time I looked: " + ", ".join(parts) + "."

    def _what_i_read(self) -> dict[str, object]:
        items = [
            {
                "label": self._label(signal.id),
                "tone": "info",
                "text": signal.content if len(signal.content) <= 280 else signal.content[:277] + "...",
                "detail": str(signal.provenance.get("filename") or ""),
            }
            for signal in self._signals
        ]
        shown = items[:30]
        blocks: list[dict[str, object]] = [
            _text(f"I've read {_plural(len(self._signals), 'update')} so far. If this doesn't look right, tell me to start over and paste it again."),
            {"type": "items", "title": "Updates I've read", "items": shown},
        ]
        if len(items) > len(shown):
            blocks.append(_text(f"...and {len(items) - len(shown)} more.", "note"))
        return _message(blocks, self._next_suggestions())

    def _decision_items(self) -> list[dict[str, object]]:
        result = self._result
        assert result is not None
        return [
            {
                "label": _READINESS[request.readiness][0],
                "tone": _READINESS[request.readiness][1],
                "text": request.description,
                "detail": " | ".join(
                    part
                    for part in (
                        f"Owner: {request.owner}" if request.owner else "No owner named",
                        f"Deadline: {request.deadline}" if request.deadline else "No deadline named",
                        f"From {self._label(request.signal_id)}",
                    )
                ),
            }
            for request in result.decision_requests or []
        ]

    def _dependency_items(self) -> list[dict[str, object]]:
        result = self._result
        assert result is not None
        by_id = {finding.id: finding for finding in result.findings}
        items: list[dict[str, object]] = []
        for dependency in result.dependencies or []:
            finding = by_id.get(dependency.finding_id)
            label, tone = _DEPENDENCY_STATUS.get(dependency.status, ("At risk", "warn"))
            quote = finding.evidence[0].excerpt if finding and finding.evidence else dependency.title
            source = self._label(finding.evidence[0].signal_id) if finding and finding.evidence else ""
            items.append(
                {
                    "label": label,
                    "tone": tone,
                    "text": quote,
                    "detail": " | ".join(
                        part
                        for part in (
                            f"Owner: {dependency.owner}" if dependency.owner else "",
                            f"Needed by: {dependency.required_by}" if dependency.required_by else "",
                            f"From {source}" if source else "",
                        )
                        if part
                    ),
                }
            )
        return items

    def _decisions(self) -> dict[str, object]:
        items = self._decision_items()
        if not items:
            return _message(
                [_text("I didn't see anyone asking for a decision or approval in what I've read.")],
                self._next_suggestions(),
            )
        return _message(
            [
                _text(
                    f"{_plural(len(items), 'decision')} {'is' if len(items) == 1 else 'are'} waiting on someone. "
                    "A decision with no owner or deadline tends to stall, so those are flagged."
                ),
                {"type": "items", "title": "Decisions waiting", "items": items},
            ],
            self._next_suggestions(),
        )

    def _dependencies(self) -> dict[str, object]:
        items = self._dependency_items()
        if not items:
            return _message(
                [_text("I didn't see anything that is blocked or waiting on something else.")],
                self._next_suggestions(),
            )
        return _message(
            [
                _text(f"{_plural(len(items), 'piece')} of work {'looks' if len(items) == 1 else 'look'} blocked or waiting on something else."),
                {"type": "items", "title": "Blocked or waiting", "items": items},
            ],
            self._next_suggestions(),
        )

    def _changes(self) -> dict[str, object]:
        if self._analyses < 2:
            return _message(
                [_text("This is the first time I've looked at these updates, so there's nothing to compare yet. Add newer updates and I'll tell you what changed.")],
                self._next_suggestions(),
            )
        summary = self._change_summary() or "Nothing has changed since the last time I looked."
        result = self._result
        assert result is not None
        items = []
        for finding in prioritize(result.findings):
            trajectory = result.trajectory_for(finding.id)
            label = _TRAJECTORY_LABELS.get(trajectory.state, "Still open") if trajectory else "Still open"
            tone = {"Getting worse": "bad", "Improving": "ok", "New since last time": "warn"}.get(label, "info")
            about = finding.evidence[0].excerpt if finding.evidence else finding.description
            items.append({"label": label, "tone": tone, "text": _plain_title(finding), "detail": about[:160]})
        return _message(
            [_text(summary), {"type": "items", "title": "How each item has moved", "items": items}],
            self._next_suggestions(),
        )

    def _actions(self) -> dict[str, object]:
        result = self._result
        assert result is not None
        items: list[dict[str, object]] = []
        seen: set[str] = set()
        for finding in prioritize(result.findings)[:TOP_FINDINGS]:
            about = finding.evidence[0].excerpt if finding.evidence else finding.title
            about = about if len(about) <= 110 else about[:107] + "..."
            for action in finding.recommended_actions:
                if action in seen:
                    continue
                seen.add(action)
                items.append({"label": _TYPE_LABELS[finding.type], "tone": "info", "text": action, "detail": f"About: {about}"})
        if not items:
            return _message([_text("I don't have any suggested next steps yet.")], self._next_suggestions())
        return _message(
            [
                _text("Here are suggested next steps for the most important items. They are suggestions for you and your team to weigh, not instructions."),
                {"type": "items", "title": "Suggested next steps", "items": items},
            ],
            self._next_suggestions(),
        )

    def _evidence(self) -> dict[str, object]:
        result = self._result
        assert result is not None
        blocks: list[dict[str, object]] = [
            _text(
                "Every item quotes the exact words it is based on, and says which update they came from. "
                "\"How sure I am\" reflects how much supporting evidence there is: several updates saying "
                "similar things raise it. Nothing here is invented, but do check the quotes against the "
                "source before acting."
            )
        ]
        blocks.extend(self._findings_blocks(prioritize(result.findings), 3)[1:])
        return _message(blocks, self._next_suggestions())

    def _report(self) -> dict[str, object]:
        result = self._result
        assert result is not None
        findings = prioritize(result.findings)
        decisions = self._decision_items()
        dependencies = self._dependency_items()
        if not findings and not decisions and not dependencies:
            return _message([_text("There's nothing to put in a report yet.")], self._next_suggestions())
        today = datetime.now()
        report = {
            "title": "Project risk report",
            "date": today.strftime("%B %d, %Y").replace(" 0", " "),
            "update_count": _plural(len(self._signals), "update"),
            "findings": [self._finding_card(rank, finding) for rank, finding in enumerate(findings, start=1)],
            "decisions": decisions,
            "dependencies": dependencies,
        }
        return _message(
            [
                _text(
                    "Here's a report you can share. Download it to get a file that opens in any web "
                    "browser (and can be printed or saved as a PDF), or copy the text into an email."
                ),
                {
                    "type": "document",
                    "title": report["title"],
                    "filename": f"project-risk-report-{today.strftime('%Y-%m-%d')}.html",
                    "text": render_text(report),
                    "html": render_html(report),
                },
            ],
            self._next_suggestions(),
        )
