# Anti-slop audit for scientific prose

Sources: stop-slop (hardikpandya), Stop Slop v3 (Julz7727), avoid-ai-writing
(conorbronsdon), Wikipedia "Signs of AI writing".

## Why it works

LLMs pick the most statistically likely continuation for the widest audience —
the "slop basin". Negative lists prime the failures they ban. So: write to a
positive register (derivation), audit afterwards with these presence tests. The
audit is the ONLY place AI-failure patterns may be loaded into context, and only
on a finished draft.

## Presence-test checklist (each item = a pass/fail to apply sentence-by-sentence)

1. **Human subject** — every sentence has a named/specific human acting ("we filtered", "the evaluator measured"). Inanimate actors fail ("the decision emerges", "the pipeline shows").
2. **Material anchor** — every paragraph has ≥1 concrete noun (number, duration, name, object, dataset). "The implications are significant" fails; "9 semanas e US$14k em horas extras" passes.
3. **Single-pass assertion** — first sentence of each paragraph is the claim; the rest is evidence/consequence. No "not X, but Y", no preview ("In this section we will explore…").
4. **Rhythm variation** — no 3 consecutive sentences within ~5 words of each other. No em-dashes. Paragraphs don't end on their shortest sentence. Two items, not three.
5. **Earned emphasis** — no sentence announces its own importance ("this matters", "importantly", "a key contribution"). Consequence in the same paragraph justifies it.
6. **Specificity** — no vague adverbs/superlatives ("significantly", "every", "always"), no synonym-cycling (sistema↔plataforma↔stack), no throat-clearing ("here's what", "in order to", "it's about").
7. **Trust** — facts stated directly; no justification, hand-holding, or parenthetical hedging ("tools (like X and Y)").
8. **No pull-quotes** — if a clause reads like a keynote line, rewrite it.

## Quick checks before delivery (presence, not absence)

- Every sentence has a human subject? Find the actor in each.
- ≥1 concrete noun per paragraph?
- First sentence of each paragraph states the point?
- Sentence lengths vary across every 3-sentence window?
- Stays inside the register from derivation?
- Is every claim of importance backed by a specific consequence in the same paragraph?
- Could a reader identify the target register without being told? (If register-neutral, the derivation failed.)