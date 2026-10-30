# CLAUDE.md — mad-science

Rules for agents working **in this official data science skills repository**.
Read before changing anything under `skills/`.

## Repository purpose

Manage and improve the hypothesis-driven experiment skills (`skills/*`), packaged
as a multi-agent plugin (Claude Code, Codex, Copilot, Cursor, skills.sh). Every
change to the skill ecosystem happens here.

## Mandatory rules

1. **Pull Request required**: every change goes in through a Pull Request (PR)
   that describes the proposed change. Never commit directly to `main`.
   - Branches: `type/description` in kebab-case (`feat/new-skill`, `fix/typo-what-i-do`).
   - Commits: Conventional Commits, subject ≤ 72 characters.
2. **Catalogue in `what-i-do`**: every skill must be catalogued in
   `skills/what-i-do/SKILL.md` **before it is final**.
   - **If the skill changes the experiment flow**, update `what-i-do`
     (*Main Flow* and/or *Flow Checks* sections) to reflect the new flow, and
     describe the flow change for the reviewer in the PR.
   - `what-i-do` is the **source of truth** for the catalogue; `README.md` mirrors it.

## Checklist before opening a PR

- [ ] Created a `type/description` branch and described the change in the PR.
- [ ] The skill is catalogued in `what-i-do` (with a descriptive role per skill).
- [ ] If the flow changed: `what-i-do` updated (Main Flow / Flow Checks / Standalone).
- [ ] Conventional Commits; no secrets or `.env` in the diff.
- [ ] Tests/validations run (e.g. `scripts/tests` of skills that have them).
- [ ] `python3 scripts/validate_plugin.py` passes (frontmatter, catalogue, manifests).
- [ ] New skill? It is also added to the `README.md` table.
- [ ] Release? `version` is the same in all three manifests (`.claude-plugin/plugin.json`,
      `.cursor-plugin/plugin.json`, `plugin.json`).

## Packaging (plugin)

- Skills live in `skills/<name>/SKILL.md`; the frontmatter `name` equals the folder name.
- Skill scripts never assume they live inside the user's repo: reference them as
  `<skill-dir>/scripts/...` and resolve project files from the working directory
  (the plugin is installed outside the project).
- `.claude-plugin/marketplace.json` serves Claude Code, Codex and Copilot CLI;
  `.cursor-plugin/plugin.json` serves Cursor; skills.sh discovers `skills/` on its own.
- All content (skills, docs, UI strings) is written in English.
- Local test: `claude --plugin-dir .` and `claude plugin validate .`.

## Skill catalogue

Source: `skills/what-i-do/SKILL.md` (wins over this file on divergence).

| Skill | Role | When to use |
|---|---|---|
| `/hypothesys` | Sharpens the hypothesis and premises through an interview. | First step of the flow. |
| `/to-doc` | Consolidates the discussion into an experiment doc and publishes it to the issue tracker. | Experiment contract. |
| `/experiment-pipeline` | Builds a sliced pipeline and tracks the rounds. | Execution in slices. |
| `/let-it-rip` | Implements the experiment in the notebook (expectation-driven). | Time to implement. |
| `/exp-review` | Reviews the experiment code (standards + quality) in parallel. | Gate before moving on. |
| `/expectation-driven-science` | Scientific discipline (hypothesis → prediction → verification). | Rigor reference. |
| `/developing-data-science-notebooks` | Production-grade notebook practices. | Creating/refactoring notebooks. |
| `/literature-research` | Research on primary sources, findings saved as Markdown. | State of the art. |
| `/to-article` | Generates/structures/reviews a scientific-technical article. | Results become a paper. |
| `/mad-science-setup` | Configures the repo layout and documents. | Once, before using the others. |
| `/notify-gchat-human-wait` | Sends a Google Chat card when the agent waits for a human. | Operations/automation. |
| `/critic-review` | Reviews the whole project (docs, experiments, results) against the state of the art; flags gaps and weak evidence. | End of project or a critical second opinion. |
| `/experiment-graph` | Read-only interactive graph of the pipeline doc (status, dependencies, critical path). | Visual overview of experiment state. |
| `/what-i-do` | Orientation map and canonical catalogue. | Unsure which skill to use. |

## Engineering standards

- Global governance files (`~/.claude/CLAUDE.md`, rules in `.agents/`) apply unless
  this file says otherwise.
- Prefer small, incremental changes; code size limits and quality standards
  (coverage, tests in `scripts/`) follow the global rules.
