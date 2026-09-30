# micromotives-datasets

Dataset-building pipeline for **Micromotives** (the behavioural-simulation stack).
Produces UK behavioural-prediction datasets in
`(persona, condition, outcome, response)` form, modelled on the **SocSci210**
paper (arXiv:2509.05830), for fine-tuning open-weight LLMs to predict human
behaviour in social-science experiments.

The design, sources, and decisions live in
[`docs/SocSci-UK_MASTER.md`](docs/SocSci-UK_MASTER.md) — the single source of
truth. Start there.

## What this produces

Rows shaped `(P, c, o, r)`:

- **persona** — respondent demographics rendered to text.
- **condition** — the randomised stimulus arm the respondent saw.
- **outcome** — the question they were asked.
- **response** — what they answered.

Two assembly paths (see master doc §8):

- **PULL** — studies already reconstructed in SocSci210 → melt straight through.
- **BUILD** — studies SocSci210 missed + all UK-native sources (TESS, Harvard
  Dataverse, BES, the Understanding Society Innovation Panel) → reconstruct from
  raw deposits via the build pipeline.

## Setup (once)

```sh
uv sync
```

Package manager is [`uv`](https://github.com/astral-sh/uv) — do not use `pip` or
`poetry` (lockfile is `uv.lock`).

## Layout

```
src/micromotives_datasets/   package
  schema.py                  the (P,c,o,r) row model
  config.py                  settings / paths
  persona.py                 demographics → persona text
  sources/                   one adapter per data source
    socsci210.py  tess.py  dataverse.py  innovation_panel.py
  pipeline/                  parse → reconstruct → QC → emit
docs/                        SocSci-UK_MASTER.md + checklists + archive/
data/
  catalog/                   study lists, IDs, URLs (committed)
  raw/                       source downloads (LOCAL ONLY — gitignored)
  processed/                 built (P,c,o,r) rows (gitignored)
scripts/                     explore.py, bes_inspect.py — ad-hoc inspection
tests/
```

## Data licensing — read before committing anything under `data/`

`data/raw/` and built rows are **gitignored**. Several sources are
redistribution-restricted:

- **UKDS safeguarded** (Innovation Panel SN 6849, restricted BES files) — EUL,
  **no redistribution**. Keep local; never commit; never send to an external
  service without checking the EUL.
- Only the **catalog** (`data/catalog/`) and rows we are licensed to hold are
  tracked.

Synthetic quotes generated for the quote model are **always labelled synthetic**
— never presented as real respondent words.

## Commands

- `uv sync` — install deps.
- `uv run pytest` — tests.
- `uv run ruff check src tests scripts` — lint.
- `uv run ruff format src tests scripts` — format.
- `uv run mypy src` — type check.
- `uv run python scripts/explore.py` — inspect the SocSci210 dataset.
