# Extraction — doc → model

Read this before changing `scripts/model.py`.

## What the doc looks like

The pipeline doc is written by `experiment-pipeline`. Only these structures are parsed:

```markdown
### Experiment Stage <n> — <name>        # subgraph boundary + stage color stripe

#### Fase <n> — <name>                   # ignored (organisational only)

#### Experiment <n>                      # one node, id = "E<n>"
**title**: short name                   # node label + human-work signal
**Goals**: what it measures             # tooltip + detail panel
**Status**: one of the four literals    # fill + border form
**Blocked by**: E1, E2 | —              # incoming edges (blocker → blocked)
**Result**: prose when completed        # tooltip + detail panel
```

Optional, per experiment:

```markdown
**Human**: true | false                 # overrides the title heuristic
```

## Field rules

| Field | Rule |
|---|---|
| `title` | Markdown emphasis and backticks stripped. Used verbatim in the label. |
| `Goals` / `Result` | Emptiness markers (`—`, `-`, `--`) normalise to `""`. `Result` may span several lines; continuations are folded into one string. |
| `Status` | Lowercased, matched against the four literals. Anything else → `not-implemented` **and** an anomaly is recorded. |
| `Blocked by` | `E<n>` tokens extracted by regex; sorted by number. Self-references and unknown ids are dropped (an unknown blocker is silently ignored — it cannot be an edge). |
| `Human` | Present → parsed as `true`/`yes` (or Portuguese `sim`). Absent → the title heuristic applies. |

## Human work detection

Human work is a property of the **title**, never of `Result` prose. Result text is
narrative and false-positives on phrases like *"annotated pool"* (E8) and *"human
anchors"* inside another experiment's result.

Signal: `annotation|annotate|human|anchor|judg(e)?ment` plus the Portuguese stems
`anota|âncora|ancora|humano|humana|julgamento` (case-insensitive) against `title` only. Override with `**Human**: false` when the
heuristic is wrong for a given experiment.

## Claims to check, not facts

Two parts of the doc are extracted only to be cross-checked:

- **Layer table** — `| <layer> | **E1**, **E2** | ... |` rows. Compared against the
  derived DAG depth; divergence is reported in the "Layers" panel.
- **Stated critical path** — `**Critical path:** E1 → E2 → ...` (the Portuguese
  label `**Caminho crítico:**` is also accepted). Compared against
  the longest path length; a non-maximal claim is reported in the "Critical path"
  panel.

Neither is ever used to draw the graph. See `layout.md`.

## Contract

`model.parse()` is pure and total: it never raises on a malformed doc and never
corrects what it reads. A doc with no `#### Experiment` blocks yields an empty graph,
which `render.py` rejects with a clear message rather than writing an empty artifact.