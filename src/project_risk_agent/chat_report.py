"""Render the chat's findings as a shareable report: plain text to copy, HTML to download."""

from __future__ import annotations

from html import escape

_ABOUT = (
    "This report was produced by Project Risk Agent from the updates listed above. It looks for "
    "common warning language, can miss things, and doesn't know your project's context. Treat it as "
    "a starting point for a conversation. Check the quotes against the original sources before "
    "acting. It suggests actions but never makes decisions."
)
_STYLE = (
    "body{font:16px/1.55 system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;color:#1d2330;"
    "max-width:780px;margin:32px auto;padding:0 20px}"
    "h1{font-size:1.6rem;margin:0 0 4px}h2{font-size:1.15rem;margin:28px 0 10px;border-bottom:1px solid #dde1e8;"
    "padding-bottom:6px}h3{font-size:1.05rem;margin:0}.muted{color:#5b6473;font-size:.9rem}"
    ".card{border:1px solid #dde1e8;border-left:6px solid #475467;border-radius:10px;padding:12px 16px;margin:0 0 14px;"
    "break-inside:avoid}.high{border-left-color:#b42318}.medium{border-left-color:#b7791f}"
    ".tag{display:inline-block;font-size:.8rem;font-weight:700;background:#f2f4f7;border-radius:999px;padding:1px 10px;"
    "margin-right:6px}blockquote{margin:6px 0;padding:4px 12px;background:#f2f4f7;border-radius:6px}"
    "blockquote b{display:block;font-size:.8rem;color:#5b6473}ul{margin:4px 0 0;padding-left:20px}"
    "li{margin:0 0 8px}.note{margin-top:32px;padding-top:12px;border-top:1px solid #dde1e8}"
    "@media print{body{margin:0}}"
)
_PRIORITY = {"high": "Act soon", "medium": "Keep an eye on", "low": "Lower priority"}


def _levels(card: dict) -> str:
    parts = [f"{level['name']}: {level['value']}" for level in card["levels"]]
    parts.append(f"How sure I am: {card['confidence']}")
    return " | ".join(parts)


def render_text(report: dict) -> str:
    lines = [report["title"].upper(), f"Prepared {report['date']} from {report['update_count']}.", ""]
    if report["findings"]:
        lines += ["WHAT MAY NEED ATTENTION", ""]
    for card in report["findings"]:
        lines.append(f"{card['rank']}. {card['title']} ({_PRIORITY[card['tone']]})")
        lines.append(f"   {card['kind']}: {card['kind_help'].lower()}. Area: {card['category']}.")
        if card["decision_required"]:
            lines.append("   A decision is needed.")
        if card["summary"]:
            lines.append(f"   Why this matters: {card['summary']}")
        for quote in card["quotes"]:
            lines.append(f'   - {quote["source"]}: "{quote["quote"]}"')
        if card["more_quotes"]:
            lines.append(f"   - ...and {card['more_quotes']} more")
        if card["actions"]:
            lines.append("   Suggested next steps:")
            lines += [f"   * {action}" for action in card["actions"]]
        lines += [f"   {_levels(card)}", ""]
    for heading, items in (("DECISIONS WAITING", report["decisions"]), ("BLOCKED OR WAITING", report["dependencies"])):
        if items:
            lines += [heading, ""]
            for item in items:
                lines.append(f"- [{item['label']}] {item['text']}")
                if item["detail"]:
                    lines.append(f"  {item['detail']}")
            lines.append("")
    lines += ["ABOUT THIS REPORT", _ABOUT]
    return "\n".join(lines)


def _item_html(items: list[dict]) -> str:
    rows = "".join(
        f"<li><span class='tag'>{escape(item['label'])}</span>{escape(item['text'])}"
        + (f"<br><span class='muted'>{escape(item['detail'])}</span>" if item["detail"] else "")
        + "</li>"
        for item in items
    )
    return f"<ul>{rows}</ul>"


def render_html(report: dict) -> str:
    body = [
        f"<h1>{escape(report['title'])}</h1>",
        f"<p class='muted'>Prepared {escape(report['date'])} from {escape(report['update_count'])}.</p>",
    ]
    if report["findings"]:
        body.append("<h2>What may need attention</h2>")
    for card in report["findings"]:
        quotes = "".join(
            f"<blockquote><b>{escape(q['source'])}</b>{escape(q['quote'])}</blockquote>" for q in card["quotes"]
        )
        more = f"<p class='muted'>...and {card['more_quotes']} more.</p>" if card["more_quotes"] else ""
        actions = (
            "<p><b>Suggested next steps</b></p><ul>"
            + "".join(f"<li>{escape(action)}</li>" for action in card["actions"])
            + "</ul>"
            if card["actions"]
            else ""
        )
        decision = "<span class='tag'>Decision needed</span>" if card["decision_required"] else ""
        summary = f"<p><b>Why this matters:</b> {escape(card['summary'])}</p>" if card["summary"] else ""
        body.append(
            f"<div class='card {escape(card['tone'])}'>"
            f"<h3>{card['rank']}. {escape(card['title'])}</h3>"
            f"<p class='muted'><span class='tag'>{escape(_PRIORITY[card['tone']])}</span>{decision}"
            f"{escape(card['kind'])}: {escape(card['kind_help'].lower())}. Area: {escape(card['category'])}.</p>"
            f"{summary}{quotes}{more}{actions}"
            f"<p class='muted'>{escape(_levels(card))}</p></div>"
        )
    for heading, items in (("Decisions waiting", report["decisions"]), ("Blocked or waiting", report["dependencies"])):
        if items:
            body += [f"<h2>{heading}</h2>", _item_html(items)]
    body.append(f"<div class='note muted'><b>About this report.</b> {escape(_ABOUT)}</div>")
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{escape(report['title'])}</title><style>{_STYLE}</style></head><body>"
        + "".join(body)
        + "</body></html>"
    )
