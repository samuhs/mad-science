#!/usr/bin/env python3
"""Send a formatted Google Chat card when a flow skill is waiting for a human.

The bash wrapper (``notify-gchat.sh``) only locates ``.env``, exports
``GCHAT_WEBHOOK_URL`` and delegates here; the payload formatting lives in this
file. Plain ``text`` payloads are rendered by Google Chat as one unformatted
blob, so this script builds a ``cardsV2`` card instead: a header, one widget per
message line, and a context footer.

The message body is written in Google Chat's *card markup*, not HTML — see
``card_markup`` for the supported subset and the sanitizing rules.

Fail-silent by contract: any failure is a warning on stderr and the process
still exits 0, so a notification can never block the workflow.

Usage:
    echo "open question" | notify_gchat.py --project iris_dataset
    notify_gchat.py --project iris_dataset --message "..." --details path.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime

from card_markup import DEFAULT_FONT_COLOR, clamp, escape, sanitize_markup

MAX_CARD_CHARS = 4000
HTTP_TIMEOUT_S = 15
TITLES = {
    "waiting": "🤖 Claude needs your answer",
    "done": "✅ Stage completed",
}


def text_widget(text: str) -> dict:
    """Build a textParagraph widget.

    Args:
        text: Card-markup text (already sanitized).

    Returns:
        A Google Chat widget dict.
    """
    return {"textParagraph": {"text": text}}


def read_message(args: argparse.Namespace) -> str:
    """Resolve the notification body from ``--message`` or stdin.

    Args:
        args: Parsed command-line arguments.

    Returns:
        The message body, or a placeholder when both sources are empty.
    """
    if args.message:
        return args.message
    piped = sys.stdin.read() if not sys.stdin.isatty() else ""
    return piped.strip() or "(sem detalhes fornecidos)"


def read_details(path: str | None) -> list[str]:
    """Read optional extra lines rendered as a bullet list.

    Args:
        path: Path to a plain-text file, or ``None``.

    Returns:
        Non-empty, non-comment lines from the file; empty list when absent.
    """
    if not path:
        return []
    try:
        with open(path, encoding="utf-8") as handle:
            lines = [line.strip() for line in handle]
    except OSError as error:
        print(f"⚠️ notify-gchat: details unreadable ({error})", file=sys.stderr)
        return []
    return [line for line in lines if line and not line.startswith("#")]


def build_card(project: str, kind: str, message: str, details: list[str]) -> dict:
    """Assemble the cardsV2 payload.

    Args:
        project: Project name shown in the card subtitle.
        kind: ``waiting`` or ``done`` — selects the header title.
        message: Main body text, in card markup.
        details: Extra lines rendered as bullets (card markup).

    Returns:
        The payload dict ready to be serialized as JSON.
    """
    widgets = [text_widget(sanitize_markup(message))]
    if details:
        bullets = "<br>".join(f"• {sanitize_markup(line)}" for line in details)
        widgets.append(text_widget(bullets))
    widgets.append(text_widget(footer(project)))
    card = {
        "header": {"title": TITLES.get(kind, TITLES["waiting"]), "subtitle": escape(project)},
        "sections": [{"widgets": widgets}],
    }
    return {"cardsV2": [{"cardId": f"notify-{kind}", "card": card}]}


def footer(project: str) -> str:
    """Build the muted context line at the bottom of the card.

    Args:
        project: Project name (data, never markup).

    Returns:
        The footer widget text, with the project name escaped.
    """
    stamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    text = escape(f"📎 {project} · {stamp}")
    return f'<font color="{DEFAULT_FONT_COLOR}">{text}</font>'


def send(webhook: str, payload: dict) -> None:
    """POST the payload to the webhook, warning (never raising) on failure.

    Args:
        webhook: Google Chat webhook URL.
        payload: Card payload to serialize.
    """
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        webhook, data=body, headers={"Content-Type": "application/json; charset=UTF-8"}
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_S) as response:
            if not 200 <= response.status < 300:
                print(f"⚠️ notify-gchat: HTTP {response.status}", file=sys.stderr)
    except (urllib.error.URLError, OSError) as error:
        print(f"⚠️ notify-gchat: failed to notify ({error})", file=sys.stderr)


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list without the program name.

    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Send a formatted Google Chat card.")
    parser.add_argument("--project", default=os.path.basename(os.getcwd()))
    parser.add_argument("--message", default="")
    parser.add_argument("--details", default=None)
    parser.add_argument("--kind", choices=sorted(TITLES), default="waiting")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    """Entry point. Always returns 0 — notifications must not break the flow.

    Args:
        argv: Argument list without the program name.

    Returns:
        Exit code (always 0).
    """
    args = parse_args(argv)
    webhook = os.environ.get("GCHAT_WEBHOOK_URL", "")
    if not webhook:
        print("⚠️ notify-gchat: GCHAT_WEBHOOK_URL not configured (see .env)", file=sys.stderr)
        return 0
    message = clamp(read_message(args), MAX_CARD_CHARS)
    send(webhook, build_card(args.project, args.kind, message, read_details(args.details)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))