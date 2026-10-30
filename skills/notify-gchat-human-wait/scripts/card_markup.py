"""The Google Chat card markup contract: sanitize, escape and clamp text.

Google Chat renders a small **subset of HTML tags** inside cards, documented at
https://developers.google.com/workspace/chat/format-messages ("Format text that
appears in cards"). It is not HTML: entities are not decoded, and anything
outside the subset is displayed literally.

That shape drives the three rules in this module:

* The message body is written by the caller *in card markup*, so it must be
  **sanitized** (``sanitize_markup``) rather than escaped — escaping it turns
  ``<b>`` into a literal ``&lt;b&gt;`` on screen, which is the bug this module
  exists to prevent.
* Fields the caller does not control — the project name, the timestamp — are
  **data**, so they go through ``escape``.
* ``clamp`` truncates to the card's length limit without cutting a tag in half.
"""

from __future__ import annotations

import re

FONT_COLOR = re.compile(r"\A#[0-9A-Fa-f]{6}\Z")
DEFAULT_FONT_COLOR = "#5f6368"

# An HTML comment (`<!-- ... -->`) renders as *nothing* in Google Chat, so it is
# the neutral sink for markup that must not reach the card. The space after
# `<!--` is load bearing: it keeps a stray `-->` from a malicious payload from
# closing the comment early, which would make the rest of that payload render.
COMMENT_OPEN = "<!-- "
COMMENT_CLOSE = " -->"

# Tags Google Chat supports verbatim; `<br>` variants collapse to one form.
PASSTHROUGH = {"<b>", "</b>", "<i>", "</i>", "<u>", "</u>", "<s>", "</s>",
               "<code>", "</code>", "<pre>", "</pre>", "</a>", "</font>"}
BREAKS = {"<br>", "<br/>", "<br />"}


def escape(text: str) -> str:
    """Neutralize text that must never be interpreted as card markup.

    Args:
        text: Raw data, such as the project name or a timestamp.

    Returns:
        Text with ``<`` and ``>`` replaced by full-width lookalikes, which
        Google Chat renders as the intended glyph but never parses as a tag.
        ``&`` is left alone: cards do not decode entities, so escaping it would
        mangle ordinary text such as ``R&D``.
    """
    return text.replace("<", "＜").replace(">", "＞")


def _neutral() -> str:
    """Return the markup sink that renders as nothing.

    Returns:
        An empty HTML comment.
    """
    return COMMENT_OPEN + COMMENT_CLOSE


def _normalize_font(tag: str) -> str:
    """Normalize a ``<font>`` tag, or neutralize it.

    Args:
        tag: A ``<font ...>`` token.

    Returns:
        A canonical ``<font color="#RRGGBB">`` when the color is valid,
        otherwise the neutral sink.
    """
    match = re.search(r'color\s*=\s*"?([^"\s>]*)"?', tag)
    if match and FONT_COLOR.match(match.group(1)):
        return f'<font color="{match.group(1)}">'
    return _neutral()


def _normalize_link(tag: str) -> str:
    """Normalize an ``<a>`` tag, or neutralize it.

    Args:
        tag: An ``<a ...>`` token.

    Returns:
        A canonical ``<a href="...">`` for ``http``/``https`` targets,
        otherwise the neutral sink.
    """
    match = re.search(r'href\s*=\s*"?(https?://[^"\s>]+)"?', tag)
    if match:
        return f'<a href="{match.group(1)}">'
    return _neutral()


def _sanitize_tag(tag: str) -> str:
    """Normalize one supported tag, or neutralize it.

    Args:
        tag: A single ``<...>`` token, verbatim from the caller's text.

    Returns:
        The normalized tag when Google Chat supports it, otherwise an empty
        HTML comment (which renders as nothing).
    """
    lowered = tag.lower()
    if lowered in BREAKS:
        return "<br>"
    if lowered in PASSTHROUGH:
        return lowered
    if lowered == "<font>":
        return f'<font color="{DEFAULT_FONT_COLOR}">'
    if lowered.startswith("<font "):
        return _normalize_font(tag)
    if lowered.startswith("<a "):
        return _normalize_link(tag)
    return _neutral()


def _split_tags(text: str) -> list[tuple[str, str]]:
    """Split text into alternating ``(tag, following_text)`` pairs.

    Args:
        text: Raw text that may contain ``<...>`` tokens.

    Returns:
        One ``(tag, text)`` pair per tag, where ``tag`` is ``""`` for the run
        before the first tag.
    """
    parts = re.split(r"(<[^>]*>)", text)
    if len(parts) == 1:
        return [("", parts[0])]
    pairs: list[tuple[str, str]] = []
    if parts[0]:
        pairs.append(("", parts[0]))
    for index in range(1, len(parts), 2):
        following = parts[index + 1] if index + 1 < len(parts) else ""
        pairs.append((parts[index], following))
    return pairs


def sanitize_markup(text: str) -> str:
    """Keep the supported card tags, neutralize everything else.

    Each ``<...>`` token is normalized against the supported subset: allowed
    tags survive (and are canonicalized, e.g. ``<FONT COLOR=#fff>`` becomes a
    valid ``<font color>``), while unsupported or malformed markup becomes an
    empty HTML comment. Text between tags is escaped and newlines become
    ``<br>``.

    Args:
        text: Raw message body, possibly containing card markup.

    Returns:
        Card markup safe to place in a ``textParagraph``.
    """
    safe = "".join(
        (_sanitize_tag(tag) if tag else "") + escape(part)
        for tag, part in _split_tags(text)
    )
    return safe.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


def clamp(text: str, limit: int) -> str:
    """Truncate card markup to ``limit`` characters without cutting a tag.

    Args:
        text: Sanitized card markup.
        limit: Maximum raw length, matching the Google Chat card field limit.

    Returns:
        ``text`` unchanged when it fits, otherwise the longest prefix that ends
        outside of a tag.
    """
    if len(text) <= limit:
        return text
    cut = text[:limit]
    if cut.rfind("<") > cut.rfind(">"):
        cut = cut[: cut.rfind("<")]
    return cut