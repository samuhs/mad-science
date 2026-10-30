"""Compose the experiment graph model and serialise it for the template.

Public entry point: `build(path)` -> `Graph`, and `to_payload` / `to_mermaid`.

    docparse.py   doc  -> experiments, stages, stated claims
    derive.py     edges -> layers, critical path, runnable, blocked, anomalies
    model.py      compose the above, cross-check the doc's claims, serialise

`render.py` only writes the artifacts; the HTML template only draws them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape

import ancestry
import derive
import docparse
from docparse import KNOWN_STATUSES, DocClaims, Experiment


@dataclass
class Graph:
    """The parsed doc plus everything derived from its edges."""

    title: str
    stages: list[dict]
    experiments: list[Experiment]
    claims: DocClaims
    edges: list[tuple[str, str]] = field(default_factory=list)
    layer: dict[str, int] = field(default_factory=dict)
    crit_edges: set[tuple[str, str]] = field(default_factory=set)
    crit_nodes: set[str] = field(default_factory=set)
    crit_depth: int = 0
    crit_paths: int = 0
    runnable: set[str] = field(default_factory=set)
    blocked: set[str] = field(default_factory=set)
    status: dict[str, str] = field(default_factory=dict)
    ancestry: dict[str, dict] = field(default_factory=dict)
    anomalies: list[dict] = field(default_factory=list)
    notes: dict[str, str] = field(default_factory=dict)

    @property
    def layer_count(self) -> int:
        return max(self.layer.values(), default=0) + 1

    def by_id(self, exp_id: str) -> Experiment | None:
        return next((e for e in self.experiments if e.id == exp_id), None)


def _cross_check_claims(graph: Graph) -> dict[str, str]:
    """Compare the doc's summary table / stated path against the derived DAG."""
    notes: dict[str, str] = {}

    if graph.claims.layers:
        diverging = [
            f"{exp_id}: doc L{stated} → real L{graph.layer[exp_id] + 1}"
            for stated, ids in sorted(graph.claims.layers.items())
            for exp_id in ids
            if exp_id in graph.layer and graph.layer[exp_id] + 1 != stated
        ]
        notes["layers"] = (
            f"The doc's summary table disagrees with the real DAG depth on "
            f"{len(diverging)} node(s): {' · '.join(diverging[:4])}. "
            f"The layer shown is the one derived from the edges."
            if diverging else
            f"The doc's summary table agrees with the real DAG depth "
            f"({graph.layer_count} layers)."
        )

    if graph.claims.critical_path:
        stated = " → ".join(graph.claims.critical_path)
        stated_len = len(graph.claims.critical_path) - 1
        if stated_len == graph.crit_depth:
            notes["critical"] = (
                f"The doc lists <b>1</b> critical path (<code>{escape(stated)}</code>) "
                f"out of <b>{graph.crit_paths}</b> existing maximal paths. "
                f"Highlight = union of all of them."
            )
        else:
            notes["critical"] = (
                f"The doc lists a path of {stated_len} edges "
                f"(<code>{escape(stated)}</code>), but the real maximum has "
                f"{graph.crit_depth} edges — <b>the doc's path is not maximal</b>. "
                f"Highlight = union of the <b>{graph.crit_paths}</b> maximal paths."
            )

    return notes


def build(path: str) -> Graph:
    """Parse the doc at `path` and derive the full graph model."""
    title, stages, experiments, claims = docparse.parse(path)
    graph = Graph(title=title, stages=stages, experiments=experiments, claims=claims)

    ids = [e.id for e in experiments]
    graph.edges = derive.edges_of(experiments)
    graph.layer, cyclic = derive.layers_of(experiments, graph.edges)
    (graph.crit_edges, graph.crit_nodes,
     graph.crit_depth, graph.crit_paths) = derive.critical_of(experiments, graph.edges, graph.layer)

    graph.status = {e.id: derive.status_of(e) for e in experiments}
    parents, children = derive.adjacency(ids, graph.edges)

    graph.runnable = derive.runnable_of(experiments, parents, graph.status)
    graph.blocked = derive.blocked_of(ids, parents, graph.status)
    graph.ancestry = ancestry.ancestry_of(ids, parents, children)
    graph.anomalies = (
        derive.status_anomalies(experiments, parents, graph.status)
        + derive.cycle_anomaly(cyclic)
    )
    graph.notes = _cross_check_claims(graph)
    return graph


def to_payload(graph: Graph, source: str) -> dict:
    """Serialise the model into the JSON shape the template expects."""
    edges = [
        {"f": source_id, "t": target_id, "crit": (source_id, target_id) in graph.crit_edges}
        for source_id, target_id in graph.edges
    ]
    nodes = []
    for experiment in sorted(graph.experiments, key=lambda e: e.num):
        nodes.append({
            "id": experiment.id,
            "num": experiment.num,
            "title": experiment.title,
            "goals": experiment.goals,
            "result": experiment.result,
            "status": graph.status[experiment.id],
            "rawStatus": experiment.status,
            "stage": experiment.stage,
            "layer": graph.layer.get(experiment.id, 0),
            "human": derive.is_human(experiment),
        })
    return {
        "title": graph.title,
        "source": source,
        "stages": graph.stages,
        "nodes": nodes,
        "edges": edges,
        "derived": {
            "layerCount": graph.layer_count,
            "critNodes": sorted(graph.crit_nodes,
                                key=lambda i: (graph.layer[i], int(i[1:]))),
            "critDepth": graph.crit_depth,
            "critPaths": graph.crit_paths,
            "runnable": sorted(graph.runnable, key=lambda i: int(i[1:])),
            "blocked": sorted(graph.blocked, key=lambda i: int(i[1:])),
            "ancestry": graph.ancestry,
            "anomalies": graph.anomalies,
            "notes": graph.notes,
        },
    }


_STATUS_FILL = {
    "completed": "#2f9e63",
    "running": "#2b7fe0",
    "waiting-to-run": "#c2760c",
    "not-implemented": "#6e7b8b",
}


def to_mermaid(graph: Graph) -> str:
    """Emit a `flowchart LR` block: one subgraph per stage, classDef per status."""
    lines = ["flowchart LR", ""]
    for status in KNOWN_STATUSES:
        lines.append(
            f"classDef {status} fill:{_STATUS_FILL[status]},stroke:#0b1220,"
            f"color:#fff,font-weight:600"
        )
    lines.append("")

    for stage in graph.stages:
        members = [e for e in graph.experiments if e.stage == stage["n"]]
        if not members:
            continue
        lines.append(f'subgraph S{stage["n"]}["Stage {stage["n"]} — {stage["name"]}"]')
        for experiment in members:
            marks = "👤 " if derive.is_human(experiment) else ""
            label = f"{marks}{experiment.id} {experiment.title}".replace('"', "'")
            lines.append(f'    {experiment.id}["{label}"]')
        lines.append("end")
        lines.append("")

    lines.extend(f"{source} --> {target}" for source, target in graph.edges)
    lines.append("")

    for status in KNOWN_STATUSES:
        ids = [e.id for e in graph.experiments if graph.status[e.id] == status]
        if ids:
            lines.append(f"class {','.join(ids)} {status}")
    return "\n".join(lines).rstrip() + "\n"