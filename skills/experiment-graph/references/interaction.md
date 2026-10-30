# Interaction contract & verification

Read this before changing the JS in `scripts/graph-template.html`.

## Layout

```
┌──────────────────────────────────────────────────────────┬──────────────┐
│ title · source doc · counts                              │ DETAIL       │
├──────────────────────────────────────────────────────────┤ (selected    │
│ search │ status chips │ lens chips │            clear    │  node or     │
├──────────────────────────────────────────────────────────┤  empty)      │
│  ┌ selection bar (only when selected) ┐          +       │              │
│  │                                    │          -       │ LEGEND       │
│  L1 ▸ layer 1 nodes                             ⤢        │              │
│  L2 ▸ layer 2 nodes                         ┌─────┐      │ RUNNABLE     │
│  ...                                        │mini │      │ CRITICAL     │
│  L9 ▸ layer 9 nodes                         └─────┘      │ LAYERS       │
│                                                          │ ANOMALIES    │
└──────────────────────────────────────────────────────────┴──────────────┘
```

Geometry constants (top of the geometry section): node `134×56`, horizontal gap 22,
vertical gap 34, padding 46. The vertical gap was raised from 18 — at 9 layers the
rows were crowding each other. Layer order is set by four alternating barycenter
sweeps keyed on neighbours' **real x**; keying on slot index instead compares parents
in layers of different widths and strands nodes far from their parents.

## Selection — the whole point

| Action | Result |
|---|---|
| Click a node | Highlight the **whole chain**: every ancestor that leads to it and everything it unblocks (transitive). Dim everything else to ~12%. Direct incoming edges take the "in" color, direct outgoing the "out" color, the rest of the chain a quieter "anc" tone. |
| Click it again | Toggle the selection off. |
| Click the graph background | Clear. |
| `Esc` | Clear. |
| The `✕` in the selection bar | Clear. |
| Click an `E<n>` chip in the side panel | Select that node. |

Selecting highlights the *reasoning path*, not just the neighbourhood: clicking E11
lights E1→E2→E3→E4→{E5,E6,E7}→E8 and E10→E11, plus E11→E22. Direct-only highlighting
was too narrow to answer "why does this experiment exist".

The chain is computed in `ancestry.py` and shipped in the payload — the template
never re-derives graph facts. `anc` and `desc` are emitted **sorted numerically**:
the walks return sets and Python randomises string hashing per process, so set order
would break the byte-identical guarantee.

The selection bar (top-left) always states `E<n> — title · cadeia completa · N acima
· M abaixo`. The **detail panel** on the right holds Goals, Result and the connection
chips — never a modal, which would cover the very highlight the selection produced.

**Follow selection is OFF by default.** Clicking a node must never move the viewport
out from under the cursor — you clicked *there*, so the graph stays *there*. The
highlight alone is enough to read the chain.

The header toggle (`s`) opts in to framing the chain on click. Even then it only ever
zooms *in*, never out, and never fights a deliberate manual zoom.

### Why the background click is a real element

The selection clears on a background click only because the SVG contains a real
`<rect id="bg">` with `pointer-events: all`. A bare `<g>` has no fill and therefore
no hit target, so the click lands on the `<svg>` and a handler bound to the `<g>`
never fires — that was the original "I can't clear the selection" bug.

## Navigation

| Input | Action |
|---|---|
| Drag | Pan |
| Wheel / pinch | Zoom about the pointer |
| Double-click | Fit to view |
| `＋` `－` `⤢` | Zoom in, out, fit |
| `f` | Fit |
| `s` | Toggle follow-selection (off by default) |
| `r` | Reset view **and** clear selection |
| `/` | Focus the search box |
| Search + Enter | Jump to the first match |
| Arrow keys on a focused node | Move focus to the nearest node in that direction |
| `Enter` / `Space` on a focused node | Select |
| Minimap click / drag | Jump the viewport |
| `clear` | Clear selection, search and all lenses |

Nodes are focusable (`tabindex="0"`, `role="button"`) with a visible focus ring, so
the graph is usable from the keyboard. `prefers-reduced-motion` disables transitions.

## Lenses

A lens **fades** non-matching elements; it never reflows the layout. Multiple active
lenses combine as a **union** (one predictable rule).

- Status chips: `completed`, `running`, `waiting-to-run`, `not-implemented`
- `▶ runnable` — nodes runnable now
- `critical path` — nodes on any maximal path
- `👤 human` — human work
- `blocked` — nodes blocked now (also switches on the diagonal hatch overlay)

## Offline requirement

The HTML is a single standalone file: inline CSS, inline JS, inline SVG, inline JSON.
**No CDN, no external font, no `fetch`.** It must open from `file://` behind the
corporate proxy. The only `http://` string in the output is the SVG XML namespace,
which is an identifier, not a request.

## Verification checklist

Automated (run after any `model.py` change):

```bash
python3 <skill-dir>/scripts/test_model.py
```

Manual (run after any `graph-template.html` change):

- [ ] Node count == experiment count in the doc
- [ ] Edges match every `Blocked by` (direction blocker → blocked)
- [ ] Layers equal real DAG depth; if the summary table differs, the note is visible
- [ ] All maximal critical paths highlighted; a non-maximal doc claim is flagged
- [ ] Statuses literal from the doc; anomalies listed **and** flagged on the node
- [ ] Human work marked `👤` — and only the genuine ones (check `Result` prose is
      not being scanned)
- [ ] Runnable-now and blocked-now sets are correct
- [ ] Clicking a node highlights its whole chain (ancestors + descendants); an
      unrelated branch stays dim. Background click, `Esc`, `✕` and re-click all clear
- [ ] Lenses fade without reflowing; multiple lenses union correctly
- [ ] `<name>.html` opens standalone (no server, no internet)
- [ ] Two consecutive runs produce a byte-identical HTML (`diff`)
- [ ] No JS errors in the console

### Headless smoke test

```bash
google-chrome --headless --disable-gpu --no-sandbox --virtual-time-budget=4000 \
  --window-size=1920,1000 --screenshot=/tmp/graph.png \
  "file://$PWD/docs/experiments-pipeline/<name>.html"
```

To assert on the DOM instead of looking at it, append a probe script before
`</body>` that writes `document.querySelectorAll('.node').length` into a div, then
use `--dump-dom` and grep for it. `errors=0 nodes=22 edges=26` is the healthy output
for the current doc.