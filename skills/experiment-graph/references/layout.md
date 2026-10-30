# Derivation — the graph facts

Read this before changing the derivation in `scripts/model.py`. Every rule here
exists because the naive version got it wrong at least once.

## Edges

`Blocked by: A, B` on experiment `N` produces `A → N` and `B → N`. Direction is
always **blocker → blocked**. Duplicates and self-references are dropped.

## Layers — derive, never trust the summary table

`layer(n) = longest source-to-node path`, computed over the edges. This is the real
DAG depth. The doc's own summary table has been wrong (it once put E18/E21 at layer 7
and E22 at layer 9; the real depth is 6 and 8). Cross-check the table against the
derived depth and surface a visible note when they differ — never silently follow
the table, never silently ignore it either.

Layers render top → bottom: layer 0 at the top, deepest at the bottom, so the
pipeline reads like a flow. The `L1…Ln` ruler on the left makes depth readable
without hovering.

## Critical path — all of them

Compute **every** longest source-to-sink path, not one.

An edge lies on *some* maximal path iff `depth(f) + 1 + height(t) == longest`, where
`depth` is the longest path from a source and `height` the longest path to a sink.
Highlight the union of those edges and nodes.

The doc may state a single path. If the stated path is not maximal, say so and show
the union anyway. Report how many maximal paths exist.

## Runnable now

A `not-implemented` node whose **direct** blockers are all `completed`. Mark it with
`▶` on the node and list it in the "Runnable now" panel.

"Direct" matters: a node whose blockers are satisfied but whose *grandparents* are
not is still not runnable in the practical sense — that case is covered by *blocked*.

## Blocked now

A node with **any transitive ancestor** that is not `completed`. Cycle-safe (a node
revisiting itself in the walk is not blocked by the cycle).

This is a *lens*, not a permanent channel: in a healthy doc most nodes are blocked at
some point, so painting it always would encode nothing. It is off by default.

## Status anomalies — reflect, never correct

Recorded and shown in the "Anomalias de status" panel, and flagged with `⚠` on the
node:

| Kind | Meaning |
|---|---|
| `status` | An unrecognized status value, treated as `not-implemented`. |
| `blocked-completed` | A node marked `completed` whose direct blocker is not `completed`. |
| `cycle` | Dependency cycle; back-edges are ignored for layering. |

The rule is absolute: **the graph reflects the doc**. If the doc says an experiment
closed before its blocker, the graph shows `completed` *and* flags it. Silently
"fixing" it would hide the very inconsistency the view exists to reveal.

## Status → visual channel

Status is encoded redundantly so it survives color-blindness and grayscale:

| Status | Fill | Border form | Label |
|---|---|---|---|
| `completed` | green | solid | completed |
| `running` | blue | solid | running |
| `waiting-to-run` | amber | dashed | waiting to run |
| `not-implemented` | gray | dotted | not implemented |

Fill is a low-alpha wash of the status color; the border carries the status color at
full strength. Text labels are always present.

## Cross-checks

- **Layers**: derived depth vs the doc's table → note in the "Layers" panel.
- **Critical path**: stated path length vs the longest → note in the "Critical
  path" panel.

Both notes are visible in the output, never only in a log.