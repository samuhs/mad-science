# What each section must contain

Per IEEE/acmart guidance, in Computer Science the structure is problem → solution
→ evaluation. IMRaD is a base, but Related Work and Evaluation are their own
sections (empirical mapping: "Sections to IMRaD", 329 CS papers).

| Section | Must contain | Anti-pattern |
|---|---|---|
| Title | Specific, concise; no "novel/new"; no math symbols | Vague, clickbaity, meta |
| Abstract | Single paragraph, ≤ venue limit, self-contained (no refs/abbr/eqs), states done + conclusions + implication, highlights novelty. Write LAST. | Generic, cites refs, lists sections |
| Keywords / CCS | Venue-correct (SBC: palavras-chave; ACM: CCS Concepts + keywords; IEEE: Index Terms) | Missing or wrong taxonomy |
| Introduction | Funnel: world → field → gap → contribution → article roadmap. States research question + why it matters. | Catalogue of citations; no gap |
| Related Work | Positions THIS work vs prior, names the gap you fill | Just a summary list |
| Method | Reproducible: dataset, split, setup, params, metrics, running steps; enough detail for others to rebuild | Black box; missing params |
| Results | Reports outcomes: figures for trends, tables for exact values. No interpretation here. | Interpretation/claims inside Results |
| Discussion | What results mean; why contribution matters; compare vs Related Work; threats to validity for empirical work | Mere restatement of results |
| Conclusion | Implications + limits + future work; do not inflate (IEEE) | New results, overclaiming |
| References | Only work that supports claims; IEEE explicitly warns inflated citations = ethics breach | Padding, unreferenced sweep |

## Shape by article type

- Empirical → Method+Results+Discussion+Threats dominate (often 40–60% of the page budget).
- Systems/position → Approach/Method dominates, lighter evaluation, more motivation.
- Survey/SLR → no IMRaD: Introduction, review methodology (search/selection protocol), thematic synthesis, gaps, conclusion.