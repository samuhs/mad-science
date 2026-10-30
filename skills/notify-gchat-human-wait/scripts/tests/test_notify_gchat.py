"""Tests for the Google Chat card builder (notify_gchat.py).

The regression this suite guards: the message body used to be HTML-escaped, so
the supported card tags arrived at Google Chat as ``&lt;b&gt;`` and were shown
literally instead of rendering. Markup must pass through; anything outside the
documented subset must not.

Run: python3 -m pytest skills/notify-gchat-human-wait/scripts/tests -q
"""

from __future__ import annotations

import json
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from card_markup import clamp, escape, sanitize_markup  # noqa: E402
from notify_gchat import build_card  # noqa: E402


def body_of(payload: dict) -> str:
    """Return the text of the first widget of the card."""
    widgets = payload["cardsV2"][0]["card"]["sections"][0]["widgets"]
    return widgets[0]["textParagraph"]["text"]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("<b>F1-macro:</b> 0.32", "<b>F1-macro:</b> 0.32"),
        ("<i>a</i><u>b</u><s>c</s>", "<i>a</i><u>b</u><s>c</s>"),
        ("<code>x</code>", "<code>x</code>"),
        ("line1\nline2", "line1<br>line2"),
        ("<BR>", "<br>"),
        ('<font color="#FF0000">red</font>', '<font color="#FF0000">red</font>'),
        ('<font color=#FF0000>red</font>', '<font color="#FF0000">red</font>'),
        ('<a href="https://example.com">link</a>',
         '<a href="https://example.com">link</a>'),
    ],
)
def test_should_keep_supported_card_tags_intact(raw: str, expected: str) -> None:
    """Every tag Google Chat renders must survive sanitization unchanged."""
    assert sanitize_markup(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "<b>bold</b>",                     # the exact payload that used to break
        "<font color=\"#5f6368\">f</font>",
    ],
)
def test_should_not_escape_supported_markup_into_entities(raw: str) -> None:
    """Regression: escaping turned tags into `&lt;b&gt;`, rendered literally."""
    assert "&lt;" not in sanitize_markup(raw)
    assert "&gt;" not in sanitize_markup(raw)


@pytest.mark.parametrize(
    "raw",
    [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "<h1>title</h1>",
        '<a href="javascript:alert(1)">x</a>',
        '<font color="url(javascript:alert(1))">x</font>',
        '<a href="https://x" onmouseover="alert(1)">x</a>',
        '<a href="https://x>"><b>escaped</b>',
    ],
)
def test_should_neutralize_unsupported_or_unsafe_markup(raw: str) -> None:
    """Anything outside the subset must not reach the card as active markup."""
    result = sanitize_markup(raw)
    for forbidden in ("<script", "<img", "<h1", "javascript:", "onerror", "onmouseover"):
        assert forbidden not in result


@pytest.mark.parametrize(("raw", "expected"), [("<", "＜"), (">", "＞")])
def test_should_replace_bare_angle_brackets_with_lookalikes(raw: str, expected: str) -> None:
    """Unbalanced angle brackets must render as glyphs, not start a tag."""
    assert sanitize_markup(raw) == expected


def test_should_leave_ampersand_untouched_for_plain_text() -> None:
    """Google Chat does not decode entities, so `R&D` must stay `R&D`."""
    assert sanitize_markup("R&D <b>budget</b>") == "R&D <b>budget</b>"


def test_should_render_each_line_of_a_multiline_body_as_a_break() -> None:
    """A multi-paragraph question keeps its structure in the card."""
    assert sanitize_markup("Stage 1 done.\n\n<b>F1:</b> 0.32") == (
        "Stage 1 done.<br><br><b>F1:</b> 0.32"
    )


def test_should_render_details_as_bullets_with_markup_support() -> None:
    """Details lines are prefixed with a bullet and keep their markup."""
    payload = build_card("iris", "waiting", "q", ["<b>a</b>", "b"])
    bullets = payload["cardsV2"][0]["card"]["sections"][0]["widgets"][1]
    assert bullets["textParagraph"]["text"] == "• <b>a</b><br>• b"


def test_should_escape_angle_brackets_in_the_project_name() -> None:
    """The project name is data, never markup, in header and footer."""
    payload = build_card("a<b>c", "done", "q", [])
    card = payload["cardsV2"][0]["card"]
    assert card["header"]["subtitle"] == "a＜b＞c"
    footer = card["sections"][0]["widgets"][-1]["textParagraph"]["text"]
    assert "a＜b＞c" in footer


@pytest.mark.parametrize(("kind", "title"), [("waiting", "🤖"), ("done", "✅")])
def test_should_pick_the_header_title_from_the_kind(kind: str, title: str) -> None:
    """`waiting` and `done` render distinct headers."""
    payload = build_card("iris", kind, "q", [])
    assert payload["cardsV2"][0]["card"]["header"]["title"].startswith(title)
    assert payload["cardsV2"][0]["cardId"] == f"notify-{kind}"


def test_should_serialize_payload_as_valid_json_without_ascii_escapes() -> None:
    """Emoji and accents must travel as UTF-8, not as \\uXXXX escapes."""
    serialized = json.dumps(build_card("iris", "done", "naïve café ✅", []), ensure_ascii=False)
    assert "naïve café ✅" in serialized
    assert json.loads(serialized)["cardsV2"][0]["card"]["header"]["title"] == "✅ Stage completed"


def test_should_truncate_long_bodies_without_cutting_a_tag() -> None:
    """A body over the limit is trimmed at a tag boundary, never mid-tag."""
    truncated = clamp("<b>" + "x" * 100 + "</b>", 50)
    assert len(truncated) <= 50
    assert re.search(r"<[^>]*$", truncated) is None
    assert truncated.startswith("<b>")


def test_should_drop_a_trailing_partial_tag_when_clamping() -> None:
    """Truncating inside a tag removes the fragment instead of leaking it."""
    truncated = clamp("x" * 20 + "<font color=\"#5f6368\">y</font>", 25)
    assert truncated == "x" * 20


def test_should_return_short_bodies_unchanged_when_clamping() -> None:
    """Clamping is a no-op below the limit."""
    assert clamp("<b>ok</b>", 4000) == "<b>ok</b>"


def test_escape_should_neutralize_tag_delimiters_but_keep_ampersand() -> None:
    """`escape` is for data fields, not for the hand-written body."""
    assert escape("a<b>&c") == "a＜b＞&c"