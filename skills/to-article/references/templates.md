# Article templates

Detect the destination, then apply that template's rules. When the venue is
unknown and evidence is ambiguous, predicate default = target language:
pt-BR → SBC; English + acmart/arXiv → ACM; IEEEtran → IEEE.

## SBC (Brazilian conferences — SBES, SBPC, SBSeg, etc.)
- Source: SBC Publications Manual (*Manual de Publicações da SBC*) + publication templates (*Modelos para Publicações*).
- Submission via JEMS (jems3.sbc.org.br). Metadata required: title, abstract,
  keywords, language, authors (name/affiliation/ORCID), references.
- Article types: full paper (12–16 pages), short paper (≤4 pages), poster.
- Structure: title, abstract (≤500 words), keywords, body, references.
- Language: usually pt-BR (content language matches the venue CFP).
- Official inputs: https://www.sbc.org.br/documentosinstitucionais/#publicacoes,
  SBC Publications Manual PDF (2024).

## ACM (sigconf / acmart)
- Source: ACM Author Submissions + acmart template.
- Required elements for articles > 2 pages: Abstract, CSS Concepts (from the ACM
  Computing Classification System), user-defined keywords, ACM Reference Format.
- Body: Introduction, Related Work, Method, Evaluation/Results, Discussion,
  Conclusion, References. Use \documentclass[sigconf]{acmart}.
- Author metadata: ORCID, affiliation, anonymized mode for review
  (\documentclass[manuscript,review,anonymous]{acmart}).

## IEEE (conference / journal)
- Source: IEEE Author Center — Structure Your Article; IEEEtran template.
- Required: Title (no "novel/new"), Abstract (single paragraph ≤250 words,
  self-contained, no refs/equations/abbrs), Index Terms (IEEE Thesaurus), Authors
  (IEEE authorship rules), First Footnote, Body, References (IEEE numeric style).
- Section guidance (from IEEE, verbatim intent): Intro = position in literature +
  research question + why it matters; Methodology = reproducible; Results = figures
  (trends) + tables (exact values), no interpretation; Discussion = what results
  mean + contribution; Conclusion = implications + future work, don't inflate;
  References = only what supports the work (inflated citations = ethics breach).

## Format checklist (all templates)
- [ ] Abstract self-contained, written last, within the venue's word limit
- [ ] Keywords / index terms / CCS Concepts present and venue-correct
- [ ] Reference style matches template; every citation supports a claim
- [ ] Figures have captions and are referenced from the text
- [ ] Page/size limits respected
- [ ] Metadata (authors, ORCID, affiliation) filled