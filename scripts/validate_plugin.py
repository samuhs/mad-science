#!/usr/bin/env python3
"""Validate the plugin packaging before a release.

    python3 scripts/validate_plugin.py

Checks that every skill under ``skills/`` has frontmatter whose ``name`` matches
its directory and a non-empty ``description``; that every skill is catalogued
in ``what-i-do`` and in the README; and that all plugin manifests parse and
agree on name and version. Stdlib only. Exits non-zero on the first run with
any failure.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
CATALOG = SKILLS / "what-i-do" / "SKILL.md"
README = ROOT / "README.md"
MANIFESTS = [
    ROOT / ".claude-plugin" / "plugin.json",
    ROOT / ".cursor-plugin" / "plugin.json",
    ROOT / "plugin.json",
]
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def frontmatter(text: str) -> dict[str, str]:
    """Top-level keys of a YAML frontmatter block, folding indented continuations."""
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return {}
    fields: dict[str, str] = {}
    key = None
    for line in match.group(1).splitlines():
        if line[:1].isspace() and key:
            fields[key] = (fields[key] + " " + line.strip()).strip()
        elif ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            fields[key] = value.strip().strip('"')
    return fields


def check_skills(errors: list[str]) -> list[str]:
    names = []
    for skill_md in sorted(SKILLS.glob("*/SKILL.md")):
        directory = skill_md.parent.name
        fields = frontmatter(skill_md.read_text(encoding="utf-8"))
        name = fields.get("name", "")
        if name != directory:
            errors.append(f"{skill_md}: name '{name}' != directory '{directory}'")
        if not NAME_RE.match(name):
            errors.append(f"{skill_md}: name '{name}' is not kebab-case")
        if len(fields.get("description", "")) < 20:
            errors.append(f"{skill_md}: description missing or too short")
        names.append(directory)
    if not names:
        errors.append(f"no skills found under {SKILLS}")
    return names


def check_catalogs(names: list[str], errors: list[str]) -> None:
    for doc in (CATALOG, README):
        text = doc.read_text(encoding="utf-8")
        for name in names:
            if f"`/{name}`" not in text:
                errors.append(f"{doc.relative_to(ROOT)}: skill '/{name}' not catalogued")
        if re.search(r"^(<<<<<<<|=======|>>>>>>>)", text, re.MULTILINE):
            errors.append(f"{doc.relative_to(ROOT)}: leftover merge conflict marker")


def check_manifests(errors: list[str]) -> None:
    seen: set[tuple[str, str]] = set()
    for path in MANIFESTS:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        seen.add((data.get("name", ""), data.get("version", "")))
    if len(seen) > 1:
        errors.append(f"manifests disagree on (name, version): {sorted(seen)}")
    try:
        market = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{MARKETPLACE.relative_to(ROOT)}: {exc}")
        return
    plugin_names = {p.get("name") for p in market.get("plugins", [])}
    if seen and next(iter(seen))[0] not in plugin_names:
        errors.append("marketplace.json does not list the plugin by its manifest name")


def main() -> int:
    errors: list[str] = []
    names = check_skills(errors)
    check_catalogs(names, errors)
    check_manifests(errors)
    for error in errors:
        print(f"FAIL {error}")
    if errors:
        return 1
    print(f"ok: {len(names)} skills, manifests consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
