#!/usr/bin/env python3
"""Regression tests for the experiment-graph model.

    python3 test_model.py [path/to/pipeline-doc.md]

The synthetic contract always runs. The real-doc regression runs only when a doc
path is given: its expected counts belong to that specific doc.

No test framework required — the repo has none, and this skill ships
self-contained. Exits non-zero on the first failed expectation.
"""

from __future__ import annotations

import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import model  # noqa: E402  (path setup must precede the import)

_failures: list[str] = []


def check(label: str, actual, expected) -> None:
    if actual == expected:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}\n         expected: {expected!r}\n         actual:   {actual!r}")
        _failures.append(label)


def test_real_doc(path: pathlib.Path) -> None:
    """The graph must reflect this doc exactly — statuses, layers, edges."""
    print(f"\n== real doc: {path.name} ==")
    graph = model.build(str(path))
    payload = model.to_payload(graph, source=str(path))
    derived = payload["derived"]

    check("22 experiments", len(payload["nodes"]), 22)
    check("26 dependencies", len(payload["edges"]), 26)
    check("9 derived layers", derived["layerCount"], 9)
    check("critical path depth", derived["critDepth"], 8)
    check("6 maximal paths", derived["critPaths"], 6)
    check("runnable now", derived["runnable"],
          ["E5", "E12", "E13", "E14", "E15", "E16", "E18", "E19", "E21"])

    # Statuses are read literally: the doc has 7 completed / 3 running / 12 not.
    counts: dict[str, int] = {}
    for node in payload["nodes"]:
        counts[node["status"]] = counts.get(node["status"], 0) + 1
    check("status counts", counts, {"completed": 7, "running": 3, "not-implemented": 12})

    # Human work is a property of the TITLE, never of the Result prose: E3 and
    # E8 mention an annotated pool in their result and are not human work.
    check("human work", sorted(n["id"] for n in payload["nodes"] if n["human"]),
          ["E10", "E11"])

    # Both inconsistencies in the doc must be reflected, never corrected.
    kinds = sorted(a["kind"] for a in derived["anomalies"])
    check("anomalies reflected", kinds, ["blocked-completed", "blocked-completed"])
    flagged = sorted({i for a in derived["anomalies"] for i in a["ids"]})
    check("anomaly nodes", flagged, ["E2", "E3", "E5", "E8"])

    # The doc's summary table disagrees with the real DAG depth; say so.
    check("layers note present", bool(derived["notes"].get("layers")), True)
    check("critical path note present", bool(derived["notes"].get("critical")), True)
    check("E18 derived at layer 6 (doc says 7)", graph.layer["E18"], 5)
    check("E22 derived at layer 8 (doc says 9)", graph.layer["E22"], 7)

    # Edges always point blocker -> blocked.
    check("E1 -> E2 exists", ("E1", "E2") in set(graph.edges), True)
    check("E3 -> E1 does not exist", ("E3", "E1") in set(graph.edges), False)


SYNTHETIC = """# Pipeline — Test

### Experiment Stage 1 — One
#### Experiment 1
**title**: Base thing
**Goals**: goal
**Status**: completed
**Blocked by**: —
**Result**: done

#### Experiment 2
**title**: Manual annotation work
**Goals**: label by hand
**Status**: completed
**Blocked by**: E1
**Result**: 12 labelled anchors

#### Experiment 3
**title**: Depends on pending thing
**Goals**: measure
**Status**: banana
**Blocked by**: E1, E2
**Result**: —

#### Experiment 4
**title**: Explicit flag
**Goals**: nothing here hints at manual work
**Status**: not-implemented
**Blocked by**: E3
**Human**: true
**Result**: —
"""


def test_contract_edges() -> None:
    """Unknown status, human override, and blocked/runnable semantics."""
    print("\n== synthetic doc: contract ==")
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False,
                                     encoding="utf-8") as handle:
        handle.write(SYNTHETIC)
        tmp = pathlib.Path(handle.name)
    try:
        graph = model.build(str(tmp))
        payload = model.to_payload(graph, source=str(tmp))
        derived = payload["derived"]
        nodes = {n["id"]: n for n in payload["nodes"]}

        # An unrecognised status is treated as not-implemented AND flagged.
        check("unknown status becomes not-implemented", nodes["E3"]["status"], "not-implemented")
        check("unknown status is flagged",
              any(a["kind"] == "status" and "E3" in a["ids"] for a in derived["anomalies"]), True)

        # Human detection: title only, plus the explicit override.
        check("E2 title marks human work", nodes["E2"]["human"], True)
        check("E1 title does not mark", nodes["E1"]["human"], False)
        check("explicit override marks E4", nodes["E4"]["human"], True)

        # completed despite an unfinished blocker is reflected, not corrected.
        check("E2 completed with completed blocker is not an anomaly",
              any(a["kind"] == "blocked-completed" and "E2" in a["ids"]
                  for a in derived["anomalies"]), False)
        check("runnable: E4 with unfinished blocker",
              "E4" in derived["runnable"], False)
        check("blocked: E4 transitively blocked",
              "E4" in derived["blocked"], True)

        # Layers follow longest path: 1 -> 2 -> 3 -> 4.
        check("layers E1..E4", [graph.layer[f"E{i}"] for i in (1, 2, 3, 4)], [0, 1, 2, 3])
        check("one maximal path", derived["critPaths"], 1)

        # Selecting E4 highlights the whole chain that leads to it (E1,E2,E3),
        # not only its direct parent (E3) — and nothing below it.
        anc = derived["ancestry"]
        check("E4 chain above", anc["E4"]["anc"], ["E1", "E2", "E3"])
        check("E4 chain below", anc["E4"]["desc"], [])
        check("E4 chain edges", sorted(anc["E4"]["edges"]),
              ["E1>E2", "E1>E3", "E2>E3", "E3>E4"])
        check("E1 has no ancestors", anc["E1"]["anc"], [])
        check("E1 has all below", anc["E1"]["desc"], ["E2", "E3", "E4"])
        # An excluded branch must not leak into the chain.
        check("edge outside the chain absent", "E2>E4" in anc["E4"]["edges"], False)

        # Determinism invariant: the walks return sets, and Python randomises
        # string hashing per process, so every emitted list must be sorted
        # numerically. Unsorted output would differ between runs.
        def num(x):
            return int(x[1:])

        def edge_num(e):
            return (int(e.split(">")[0][1:]), int(e.split(">")[1][1:]))

        unsorted = [
            f"{nid}.{k}" for nid, entry in anc.items() for k in ("anc", "desc")
            if entry[k] != sorted(entry[k], key=num)
        ] + [
            f"{nid}.edges" for nid, entry in anc.items()
            if entry["edges"] != sorted(entry["edges"], key=edge_num)
        ]
        check("ancestry lists sorted", unsorted, [])
    finally:
        tmp.unlink(missing_ok=True)


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        doc = pathlib.Path(argv[1])
        if not doc.is_file():
            print(f"doc not found: {doc}")
            return 1
        test_real_doc(doc)
    test_contract_edges()

    print()
    if _failures:
        print(f"{len(_failures)} check(s) failed: {', '.join(_failures)}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))