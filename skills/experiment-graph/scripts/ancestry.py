"""Reachability chains: what leads to a node, and what it unblocks.

Supports the selection interaction — clicking an experiment highlights the whole
reasoning chain behind it, not just its immediate parents.

Determinism note: the walks return sets, and Python randomises string hashing per
process, so every list emitted here is sorted numerically. Emitting set order
would make the artifact differ between runs and break the byte-identical
guarantee the skill depends on.
"""

from __future__ import annotations


def _by_number(node: str) -> int:
    return int(node[1:])


def _edge_key(edge: str) -> tuple[int, int]:
    source, target = edge.split(">")
    return int(source[1:]), int(target[1:])


def _walk(node: str, adjacency: dict[str, list[str]], seen: set[str]) -> set[str]:
    """Every node reachable from `node` following `adjacency`, excluding itself."""
    for step in adjacency[node]:
        if step not in seen:
            seen.add(step)
            _walk(step, adjacency, seen)
    return seen


def ancestry_of(ids: list[str], parents: dict[str, list[str]],
                children: dict[str, list[str]]) -> dict[str, dict]:
    """Per node: its ancestors, its descendants, and the edges inside each chain.

    `edges` holds only edges whose *both* ends belong to the chain, so an
    unrelated branch is never highlighted along with it.
    """
    result: dict[str, dict] = {}
    for node in ids:
        up = _walk(node, parents, set())
        down = _walk(node, children, set())
        up_edges = sorted(
            (f"{p}>{n}" for n in up | {node} for p in parents[n] if p in up),
            key=_edge_key,
        )
        down_edges = sorted(
            (f"{n}>{c}" for n in down | {node} for c in children[n] if c in down),
            key=_edge_key,
        )
        result[node] = {
            "anc": sorted(up, key=_by_number),
            "desc": sorted(down, key=_by_number),
            "edges": up_edges + down_edges,
        }
    return result