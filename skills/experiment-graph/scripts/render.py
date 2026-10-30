#!/usr/bin/env python3
"""Render the experiment graph artifacts from a pipeline doc.

    python3 render.py <pipeline-doc.md> [--html PATH] [--mmd PATH] [--template PATH]

Writes an interactive standalone HTML next to the doc (same base name) plus a
Mermaid block. Read-only: never touches the doc.

The same doc always yields byte-identical output — the template is static and
only the `%%GRAPH_DATA%%` payload varies.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import model  # noqa: E402  (path setup must precede the import)

PLACEHOLDER = "%%GRAPH_DATA%%"
DEFAULT_TEMPLATE = pathlib.Path(__file__).resolve().parent / "graph-template.html"


def encode_payload(payload: dict) -> str:
    """Serialise for embedding in a <script> block without breaking out of it."""
    return json.dumps(payload, ensure_ascii=False, indent=1).replace("<", "\\u003c")


def render_html(template: str, payload: dict) -> str:
    if PLACEHOLDER not in template:
        raise SystemExit(f"template is missing the {PLACEHOLDER} placeholder")
    return template.replace(PLACEHOLDER, encode_payload(payload))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render experiment graph artifacts.")
    parser.add_argument("doc", help="pipeline doc (docs/experiments-pipeline/<name>.md)")
    parser.add_argument("--html", help="output HTML (default: alongside the doc)")
    parser.add_argument("--mmd", help="output Mermaid (default: alongside the doc)")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE),
                        help="HTML template to fill")
    args = parser.parse_args(argv)

    doc_path = pathlib.Path(args.doc)
    if not doc_path.is_file():
        raise SystemExit(f"pipeline doc not found: {doc_path}")

    graph = model.build(str(doc_path))
    if not graph.experiments:
        raise SystemExit(f"no `#### Experiment N` blocks found in {doc_path}")

    payload = model.to_payload(graph, source=str(doc_path))
    template = pathlib.Path(args.template).read_text(encoding="utf-8")

    html_path = pathlib.Path(args.html) if args.html else doc_path.with_suffix(".html")
    mmd_path = pathlib.Path(args.mmd) if args.mmd else doc_path.with_suffix(".mmd")
    html_path.write_text(render_html(template, payload), encoding="utf-8")
    mmd_path.write_text(model.to_mermaid(graph), encoding="utf-8")

    # Verification summary — the checklist from SKILL.md, in one place.
    derived = payload["derived"]
    print(f"nodes={len(payload['nodes'])} edges={len(payload['edges'])} "
          f"layers={derived['layerCount']} critPaths={derived['critPaths']} "
          f"runnable={len(derived['runnable'])} anomalies={len(derived['anomalies'])}")
    print(f"wrote {html_path}")
    print(f"wrote {mmd_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())