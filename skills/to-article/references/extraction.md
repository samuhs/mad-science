# Extract evidence from the repo

Goal: build an evidence map {topic → files → key numbers} WITHOUT pulling raw bytes
into context. Use processor/parse tools (e.g. invoke a sandbox/processor over the
files and print only summaries), keep citations as `path:line`.

## 1. Theoretical basis

- Find: README*, docs/, *.md, design/ADR docs, cited papers.
- Extract: problem statement, scope, related work names, hypotheses, method names.
- Cite each claim to a `path` (the file that states it).

## 2. Experiment code

- Find: entrypoints, configs (.yaml/.json), train/eval scripts, notebooks,
  Makefile/pyproject setup.
- Extract: exact experimental procedure (dataset, split, hyperparameters, metrics
  collected, running steps) so the Method/Results sections are reproducible.
- Never reverse-engineer a result from code you haven't run; report what IS stated.

## 3. Results

- Find: CSV/JSON/TSV outputs, metric logs, plots, saved artifacts, tables in docs.
- Extract: every concrete number (metric → value → path:line). Record units.
- If a number is absent, mark `[EVIDENCE: metric X — which file?]` and ask the
  author. DO NOT invent.

## 4. Evidence map

Produce a compact table, e.g.:

| Section | Claim | Source (path:line) |
|---|---|---|
| Method | 12 LLM queries, 5 seeds | src/eval.py:87 |
| Results | mutation score 0.43 ± 0.05 | results/run_2024.csv:9 |
| Related work | ToSC name + year | docs/related.md:2 |

Keep it small enough to remain in context for drafting.