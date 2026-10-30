# mad-science

[![skills.sh](https://skills.sh/b/samuhs/mad-science)](https://skills.sh/samuhs/mad-science)
[![validate](https://github.com/samuhs/mad-science/actions/workflows/validate.yml/badge.svg)](https://github.com/samuhs/mad-science/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> **Hypothesis-driven data science** skills for coding agents (Claude Code, Codex,
> GitHub Copilot, Cursor, Gemini CLI and more). They take a raw idea all the way to
> a validated, reviewed notebook and, when it earns it, to a paper.

**mad-science** is a set of 14 [Agent Skills](https://skills.sh/samuhs/mad-science)
that teach a coding agent to run machine learning and data science experiments the
way a careful scientist would: state a falsifiable hypothesis, write down the
expected result before looking at the data, implement the experiment in a Jupyter
notebook, and review it for reproducibility, data leakage and weak evidence before
trusting the numbers.

## Why

Coding agents are fast at writing notebooks and bad at doubting them. Left alone,
they tune until a metric looks good and report it. mad-science adds the missing
discipline:

- **Hypothesis first.** `/hypothesys` interviews you until the idea has premises,
  a baseline and a success metric you can fail.
- **Expectations before results.** `/expectation-driven-science` applies the TDD
  idea to analysis: predict, then verify.
- **Small, tracked slices.** `/experiment-pipeline` splits the work into
  experiments with status and dependencies, so nothing runs out of order.
- **A review gate.** `/exp-review` checks every notebook for reproducibility
  (fixed seeds, pinned dependencies), security, data leakage and code quality.
- **Paper-ready output.** `/to-article` turns the results into a structured
  scientific article.

## What a session looks like

```text
you   > /hypothesys Adding weather features will improve next-day demand forecasts.

agent > ❓ Q1 - Baseline: what does the current forecast use, and what is its
        error today?
        ➡️ Recommended: the production model's MAPE over the last 90 days.

        ❓ Q2 - Success metric: how much better counts as "improve"?
        ➡️ Recommended: at least 2 points lower MAPE on a time-based holdout.
        ...
```

When the interview ends, `/to-doc` writes the experiment contract,
`/experiment-pipeline` slices it, and `/let-it-rip` implements each slice in a
notebook that `/exp-review` must pass.

## Installation

A plugin updates itself. [skills.sh](https://skills.sh/samuhs/mad-science) copies
editable files into your project, and you update them by hand. Pick **one** per
agent: installing both gives you every skill twice.

### 1. Get the skills

**Claude Code**

```bash
claude plugin marketplace add samuhs/mad-science
claude plugin install mad-science@samuhs
```

Or inside a session: `/plugin marketplace add samuhs/mad-science` and
`/plugin install mad-science@samuhs`. Claude Code leaves auto-update off for
third-party marketplaces. Update with `claude plugin update mad-science@samuhs`,
or turn auto-update on under `/plugin` → *Marketplaces*.

**Codex**

```bash
codex plugin marketplace add samuhs/mad-science
codex plugin add mad-science@samuhs
```

**GitHub Copilot** (CLI and VS Code)

```bash
copilot plugin marketplace add samuhs/mad-science
copilot plugin install mad-science@samuhs
```

In VS Code: **Chat: Install Plugin From Source** → `https://github.com/samuhs/mad-science`.

**Cursor**

Load the repo as a local plugin, or use skills.sh (below) with `-a cursor`.

**Gemini CLI** (manual updates)

```bash
gemini skills install https://github.com/samuhs/mad-science.git --path skills
```

**Any other agent, or editable files** ([skills.sh](https://skills.sh/samuhs/mad-science))

```bash
npx skills@latest add samuhs/mad-science            # interactive: pick agents and skills
npx skills@latest add samuhs/mad-science -a codex   # cursor, opencode, windsurf, amp, ...
npx skills@latest add samuhs/mad-science --skill hypothesys --skill to-doc
```

When the installer asks which skills to take, include `mad-science-setup` and
`what-i-do`. To update, run `npx skills@latest update`.

### 2. Run `/mad-science-setup`

Once per repository. It creates the layout and documents (`docs/`, coding
standards, `.env.example`) the other skills expect.

### 3. Done

Start with `/hypothesys`. When you don't know the next step, ask `/what-i-do`.

## The flow

```
/hypothesys → /to-doc → /experiment-pipeline → /let-it-rip → /exp-review
    idea      contract      slices/rounds         notebook       gate
```

Each step produces an artifact the next one consumes. The hypothesis becomes a
contract, the contract becomes slices, each slice becomes a notebook, and each
notebook is reviewed before moving on. The discipline underneath is
`/expectation-driven-science`: write the expectation before trusting the data, the
way TDD does for code.

## Skill catalogue

> **Source of truth:** [`skills/what-i-do/SKILL.md`](skills/what-i-do/SKILL.md).
> If this README disagrees with it, `what-i-do` wins.

### Main flow: Hypothesis → Notebook

| Skill | What it does | When to use |
|---|---|---|
| `/hypothesys` | Interview ("grill") that sharpens the hypothesis and its premises. | First step: make the idea clear and falsifiable. |
| `/to-doc` | Consolidates what has been discussed into an experiment doc and publishes it to the issue tracker. | After sharpening the hypothesis; fixes the experiment contract. |
| `/experiment-pipeline` | Turns the doc into a pipeline, slicing the work and tracking the rounds. | When the contract is settled and you want to run in slices. |
| `/let-it-rip` | Implements the experiment in the notebook following the *expectation-driven* rules. | Time to get your hands dirty. |
| `/exp-review` | Reviews the experiment code (standards + quality) in parallel sub-agents. | Gate after each implementation, before moving on. |

### Scientific discipline / reference

| Skill | What it does | When to use |
|---|---|---|
| `/expectation-driven-science` | The *hypothesis → prediction → verification* discipline (TDD for science). | Guiding any analysis/model driven by explicit expectations. |
| `/developing-data-science-notebooks` | Production-grade notebook practices (structure, modularization, reproducibility). | Creating, refactoring or reviewing notebooks. |
| `/literature-research` | Researches high-trust primary sources and saves the findings as Markdown in the repo. | Before or alongside the hypothesis, to anchor it in the state of the art. |
| `/to-article` | Generates, structures or reviews a scientific-technical article from results and docs. | When experiment results are ready to become a paper. |

### Utilities / operations

| Skill | What it does | When to use |
|---|---|---|
| `/mad-science-setup` | Configures the repository layout and documents. | Once, before using the other skills. |
| `/notify-gchat-human-wait` | Sends a Google Chat card when the agent is waiting for a human answer. | Notification automation (outside the science flow). |
| `/critic-review` | Critical review of the whole project (docs, experiments, results) against the state of the art; flags gaps, weak evidence and wrong assumptions. | At the end of the project, or when you want a critical second look. |
| `/experiment-graph` | Renders a *read-only* interactive graph of the pipeline doc: status, dependencies and critical path. | Whenever you need a visual overview of `docs/experiments-pipeline/*.md`. |
| `/what-i-do` | Orientation map and **canonical catalogue** of the skills. | Whenever you don't know which skill to invoke. |

## Quick guide: which skill?

| Situation | Skill |
|---|---|
| I don't know where to start / which skill to use | `/what-i-do` |
| I have an idea and want to test it | `/hypothesys` → `/to-doc` → `/experiment-pipeline` → `/let-it-rip` → `/exp-review` |
| My hypothesis is weak or I want to stress-test the logic | `/hypothesys` |
| I want to check the state of the art | `/literature-research` |
| I want a closed experiment contract/scope | `/to-doc` |
| I want to move to execution | `/experiment-pipeline` → `/let-it-rip` |
| I finished an experiment and want a review | `/exp-review` |
| I want to turn the results into a paper | `/to-article` |

## FAQ

**What are Agent Skills?**
Folders with a `SKILL.md` file that a coding agent loads on demand. Each skill
describes when to use it and how to do one job. Claude Code, Codex, GitHub
Copilot, Cursor and Gemini CLI all read the same format.

**Which agents does mad-science work with?**
Claude Code, Codex and GitHub Copilot through the plugin marketplace, Cursor as a
plugin, Gemini CLI through `gemini skills install`, and any other agent supported
by [skills.sh](https://skills.sh/samuhs/mad-science) (OpenCode, Windsurf, Amp, ...).

**How do I make a coding agent run reproducible ML experiments?**
Install the skills, run `/mad-science-setup` once, then start with `/hypothesys`.
The flow forces fixed seeds, pinned dependencies and a written expectation before
each result, and `/exp-review` blocks notebooks that fail those checks.

**Do I need Jupyter?**
The implementation skills (`/let-it-rip`, `/developing-data-science-notebooks`,
`/exp-review`) target Jupyter notebooks. The planning skills (`/hypothesys`,
`/to-doc`, `/experiment-pipeline`, `/literature-research`) work in any repo.

**Plugin or skills.sh?**
The plugin updates itself; skills.sh copies editable files into your project.
Pick one per agent, not both.

## Special thanks

The mad-science flow **did not start from scratch**. It adapts the work of two
people to data science, and their results are the foundation of everything here:

- **[Matt Pocock](https://github.com/mattpocock)**, with [`mattpocock/skills`](https://github.com/mattpocock/skills).
  The interview → doc → slices → implementation → review cycle, the idea of
  "grilling" to sharpen your thinking, and the very shape of this repository as a
  multi-agent plugin all come from there. `/hypothesys`, `/to-doc`,
  `/experiment-pipeline`, `/exp-review` and `/literature-research` are direct
  adaptations of his skills.
- **[Lauren Tan](https://github.com/poteto)** (a.k.a. *potato*), with
  [`pstack`](https://github.com/cursor/plugins/tree/main/pstack). The philosophy of
  going deep before going fast, writing less but higher-quality code, and running
  rigorous agent workflows you can parallelize with confidence shaped the
  *expectation-driven* discipline and the review gates of this flow.

Thank you both for sharing this work openly. 🙏

## Layout

```
.claude-plugin/
├── plugin.json          # plugin manifest (Claude Code, Copilot, Codex)
└── marketplace.json     # "samuhs" marketplace listing the "mad-science" plugin
.cursor-plugin/
└── plugin.json          # plugin manifest for Cursor
plugin.json              # portable manifest (agent-plugins.org) for Codex
llms.txt                 # LLM-readable summary of the repo (llmstxt.org)
assets/
└── social-preview.*     # repository social preview image (1280×640)
skills/
└── <skill-name>/
    ├── SKILL.md         # skill definition (frontmatter + instructions)
    ├── references/      # supporting material (optional)
    └── scripts/         # executable support + tests (optional)
scripts/
└── validate_plugin.py   # validates skills, catalogue and manifests
```

## Contributing (governance)

1. **Every change goes in through a Pull Request** describing the proposed change.
   Never commit directly to `main`. Explain what changed, why, and the impact on
   the flow (if any).
2. **Branches:** `type/description` in kebab-case, e.g. `feat/new-skill`,
   `docs/update-readme`, `fix/typo-what-i-do`.
3. **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`), subject ≤ 72 characters.
4. **Before finishing the PR, update the catalogue in `skills/what-i-do/SKILL.md`:**
   - new skills go into the full catalogue (and into this README);
   - **if the skill changes the flow**, `what-i-do` must reflect the new flow (*Main Flow* and *Flow Checks* sections);
   - the PR must spell out the flow change for the reviewer.
5. **Validate before opening the PR:**

   ```bash
   python3 scripts/validate_plugin.py
   ```

6. **Release:** bump `version` in all three manifests (`.claude-plugin/plugin.json`,
   `.cursor-plugin/plugin.json`, `plugin.json`). The validator fails if they diverge.

### Local development

```bash
claude --plugin-dir .                 # load the plugin straight from the checkout
claude plugin validate .              # validate manifest + marketplace
```

## License

[MIT](LICENSE)
