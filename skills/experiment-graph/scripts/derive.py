"""Turn parsed experiments into the derived graph facts.

Layers, critical path, runnable-now, blocked-now and status anomalies. Pure graph
logic over the edges — no parsing, no rendering, no HTML.

Contract: this module never "corrects" a status it disagrees with. It reflects the
doc and reports the inconsistency as an anomaly.
"""

from __future__ import annotations

import re
from html import escape

from docparse import KNOWN_STATUSES, Experiment

# A node counts as human work when its TITLE says so. Result prose is narrative and
# yields false positives ("annotated pool", "human anchors" inside another result).
# Portuguese stems are kept so pipeline docs written in Portuguese still work.
# An explicit `**Human**: true|false` overrides this either way.
_HUMAN_RE = re.compile(
    r"annotation|annotate|human|anchor|judg(e)?ment|anota|âncora|ancora|humano|humana|julgamento",
    re.IGNORECASE,
)


def is_human(experiment: Experiment) -> bool:
    """Whether the experiment is human work (annotations, manual judgement)."""
    if experiment.human is not None:
        return experiment.human
    return bool(_HUMAN_RE.search(experiment.title))


def status_of(experiment: Experiment) -> str:
    """The literal status, with an unrecognised value falling back to the default."""
    return experiment.status if experiment.status in KNOWN_STATUSES else "not-implemented"


def edges_of(experiments: list[Experiment]) -> list[tuple[str, str]]:
    """`Blocked by: A, B` on N becomes A→N, B→N. Unknown ids and self-refs dropped."""
    known = {e.id for e in experiments}
    edges: set[tuple[str, str]] = set()
    for experiment in experiments:
        for source in experiment.blocked_by:
            if source in known and source != experiment.id:
                edges.add((source, experiment.id))
    return sorted(edges, key=lambda e: (int(e[0][1:]), int(e[1][1:])))


def adjacency(ids: list[str], edges: list[tuple[str, str]]) -> tuple[dict, dict]:
    """Return `(parents, children)` maps over the given ids."""
    parents = {i: [] for i in ids}
    children = {i: [] for i in ids}
    for source, target in edges:
        parents[target].append(source)
        children[source].append(target)
    return parents, children


def layers_of(experiments: list[Experiment], edges: list[tuple[str, str]]) -> tuple[dict[str, int], list[str]]:
    """Longest-path layering = real DAG depth. Cycles are broken, then reported."""
    ids = [e.id for e in experiments]
    parents, children = adjacency(ids, edges)

    indegree = {i: len(parents[i]) for i in ids}
    queue = [i for i in ids if indegree[i] == 0]
    order: list[str] = []
    seen: set[str] = set()
    while queue:
        node = queue.pop(0)
        if node in seen:
            continue
        seen.add(node)
        order.append(node)
        for child in children[node]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)

    cyclic = [i for i in ids if i not in seen]
    order.extend(cyclic)  # keep going with what we have; the caller reports it

    layer: dict[str, int] = {}
    for node in order:
        known = [layer[p] for p in parents[node] if p in layer]
        layer[node] = max(known) + 1 if known else 0
    for node in ids:
        layer.setdefault(node, 0)
    return layer, cyclic


def critical_of(experiments: list[Experiment], edges: list[tuple[str, str]],
                layer: dict[str, int]) -> tuple[set[tuple[str, str]], set[str], int, int]:
    """Every edge/node on some longest source-to-sink path, plus its length.

    An edge is on a maximal path iff `depth(f) + 1 + height(t) == longest`, where
    depth is the longest path from a source and height the longest path to a sink.
    Returns the union across ALL maximal paths, and how many there are.
    """
    ids = [e.id for e in experiments]
    parents, children = adjacency(ids, edges)
    order = sorted(ids, key=lambda i: (layer[i], int(i[1:])))

    depth: dict[str, int] = {}
    for node in order:
        known = [depth[p] for p in parents[node] if p in depth]
        depth[node] = max(known) + 1 if known else 0

    height: dict[str, int] = {}
    for node in reversed(order):
        known = [height[c] for c in children[node] if c in height]
        height[node] = max(known) + 1 if known else 0

    longest = max(depth.values(), default=0)
    crit_edges = {
        (s, t) for s, t in edges if depth.get(s, 0) + 1 + height.get(t, 0) == longest
    }
    crit_nodes = {i for i in ids if depth.get(i, 0) + height.get(i, 0) == longest}

    crit_children = {i: [] for i in ids}
    for source, target in crit_edges:
        crit_children[source].append(target)
    memo: dict[str, int] = {}

    def count_from(node: str) -> int:
        if node in memo:
            return memo[node]
        if not crit_children[node]:
            memo[node] = 1 if depth.get(node) == longest else 0
        else:
            memo[node] = sum(count_from(c) for c in crit_children[node])
        return memo[node]

    paths = sum(count_from(i) for i in ids if depth.get(i, 0) == 0)
    return crit_edges, crit_nodes, longest, paths


def runnable_of(experiments: list[Experiment], parents: dict[str, list[str]],
                status: dict[str, str]) -> set[str]:
    """`not-implemented` nodes whose DIRECT blockers are all `completed`."""
    return {
        e.id for e in experiments
        if status[e.id] == "not-implemented"
        and all(status[p] == "completed" for p in parents[e.id])
    }


def blocked_of(ids: list[str], parents: dict[str, list[str]],
               status: dict[str, str]) -> set[str]:
    """Nodes with any transitive ancestor that is not `completed`. Cycle-safe."""
    memo: dict[str, bool] = {}

    def blocked_by_ancestor(node: str, stack: set[str]) -> bool:
        if node in memo:
            return memo[node]
        if node in stack:
            return False
        stack.add(node)
        result = any(
            status[p] != "completed" or blocked_by_ancestor(p, stack) for p in parents[node]
        )
        stack.discard(node)
        memo[node] = result
        return result

    return {i for i in ids if blocked_by_ancestor(i, set())}


def anomaly(kind: str, ids: list[str], detail: str) -> dict:
    """One reflected inconsistency: its kind, the nodes it touches, its text."""
    return {"kind": kind, "ids": ids, "text": detail}


def status_anomalies(experiments: list[Experiment], parents: dict[str, list[str]],
                     status: dict[str, str]) -> list[dict]:
    """Status errors the doc contains: unknown values, and closed-before-blocker."""
    found: list[dict] = []
    for experiment in experiments:
        if experiment.status not in KNOWN_STATUSES:
            found.append(anomaly(
                "status", [experiment.id],
                f"<b>{escape(experiment.id)}</b>: unknown status "
                f"<code>{escape(experiment.status or '(empty)')}</code> — treated as "
                f"<code>not-implemented</code>.",
            ))
        if status[experiment.id] != "completed":
            continue
        unfinished = [p for p in parents[experiment.id] if status[p] != "completed"]
        if unfinished:
            detail = ", ".join(
                f"<b>{escape(p)}</b> (<code>{escape(status[p])}</code>)" for p in unfinished
            )
            found.append(anomaly(
                "blocked-completed", [experiment.id, *unfinished],
                f"<b>{escape(experiment.id)}</b> is <code>completed</code> but blocked "
                f"by {detail} — it should not have closed.",
            ))
    return found


def cycle_anomaly(cyclic: list[str]) -> list[dict]:
    """Report a dependency cycle; its back-edges were ignored for layering."""
    if not cyclic:
        return []
    ordered = sorted(cyclic)
    return [anomaly(
        "cycle", ordered,
        f"Dependency cycle involving <b>{escape(', '.join(ordered))}</b> — "
        f"back-edges were ignored when computing layers.",
    )]