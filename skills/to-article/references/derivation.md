# Derivation — complete before writing any prose

Doing this silently commits generation to a specific human register instead of
the default (AI) basin. If you skip it, you produce slop.

| Field | What to fill | Example (SBC paper; the real fields are written in the paper's language) |
|---|---|---|
| readerProfile | One specific reviewer: what they already know, what they must be able to do after reading. | "SBSE reviewer: knows Software Testing, does not know our pipeline; must be able to rerun the experiment." |
| registerTarget | Named venue/template whose register the prose must match. | "SBC full paper, pt-BR, technical-conference register." |
| sceneAnchor | Where/when the reader meets the text. | "Read as a PDF in EOL, two-column layout, reader looks for the abstract first." |
| textureConstraint | Concrete vocabulary from the repo (method, metrics, dataset, file names). | "ToSC, mutation score, EvoSuite suite, run_2024.csv, SMART-MUT method." |
| antiPattern (optional) | One positive redirection for a known prior failure. | "Use a human subject ('we classify'), never inanimate agents ('the pipeline shows')." |

Voice sample: if the author provided a sample of their own writing, read it
before deriving and add voiceSample with observed rhythm/word register. The
sample replaces the generic register target.