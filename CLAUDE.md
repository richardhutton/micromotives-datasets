# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project Overview

**micromotives-datasets** — Python 3.12+ pipeline that builds UK
behavioural-prediction datasets in `(persona, condition, outcome, response)`
form, modelled on the SocSci210 paper (arXiv:2509.05830). Output is training
data for fine-tuning open-weight LLMs to predict human behaviour in
social-science experiments. Part of the **Micromotives** simulation stack
(sibling: `../melange-sim`).

**The single source of truth is [`docs/SocSci-UK_MASTER.md`](docs/SocSci-UK_MASTER.md)**
(sections 0–11: schema, sources, the SocSci210 foundation, the TESS/UK-native
layers, persona crosswalk, prompt format, the build pipeline, training setup,
status). Read it before doing anything substantive. Everything below is a
pointer into it.

## Commands

- `uv sync` — install deps (once).
- `uv run pytest` — run all tests.
- `uv run ruff check src tests scripts` — lint.
- `uv run ruff format src tests scripts` — format.
- `uv run mypy src` — type check.

Package manager is **uv** (https://github.com/astral-sh/uv). Do not use pip or
poetry — the lockfile is `uv.lock`.

## Architecture

Two assembly paths (master doc §8):

- **PULL** — melt studies already reconstructed in SocSci210.
- **BUILD** — reconstruct studies SocSci210 missed + all UK-native sources.

Package layout:

- `schema.py` — the `(P,c,o,r)` row model (Pydantic). One row = one respondent
  × one experiment.
- `config.py` — settings and data paths.
- `persona.py` — demographics struct → persona text.
- `sources/` — one adapter per source: `socsci210.py`, `tess.py`,
  `dataverse.py`, `innovation_panel.py`. Each yields `(P,c,o,r)` rows.
- `pipeline/` — parse → reconstruct → QC → emit Parquet.

Study-level catalog: `data/catalog/tess_uk_foundation_sources.csv` (202
UK-appropriate TESS studies with both IDs, buildability, URLs) and
`uk_dataverse_candidates.csv`. Reconstruction recipe for the Innovation Panel:
`docs/innovation_panel_checklist.md`.

## Hard rules

- **Data licensing.** `data/raw/` and built rows are gitignored. **UKDS
  safeguarded** data (Innovation Panel SN 6849, restricted BES) is EUL —
  **never redistribute, never commit, never send to an external service**
  (including any LLM/judge API) without checking the EUL first. Only the
  `data/catalog/` files and rows we are licensed to hold are tracked.
- **Synthetic quotes are always labelled synthetic** — never presented as real
  respondent words.
- **Missing-value codes** in survey microdata are negative (UKHLS: `-1`, `-2`,
  `-7`, `-8`, `-9`…) or `9999` (BES). Strip before making integer responses.
- The `(P,c,o,r)` tuple has **four** distinct parts (paper Figure 1). Do not
  collapse outcome into condition.

## Git

Sibling projects are git repos. Commit or push only when the user asks. When
committing, end the message with:

```
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```
