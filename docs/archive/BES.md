# BES Internet Panel — inspection (`bes_inspect.py`)

Tooling to understand the **British Election Study Internet Panel** raw file,
the UK candidate for a SocSci210-style dataset. This is the *inspection* stage —
no prompts/reasoning, just understanding the format.

## Setup

```bash
# already installed into .venv: pyreadstat + pandas
./.venv/bin/python bes_inspect.py overview
```

Point `--dta` at the file if it moves (default is `~/bes-data/BES2024_W31_Panel_v31.05.dta`).

## Commands

```bash
python bes_inspect.py overview            # dimensions, waves, measure count
python bes_inspect.py catalog             # dump ALL 13k vars + labels → CSV
python bes_inspect.py measures --limit 60 # distinct topics (suffix stripped)
python bes_inspect.py search immigration  # find variables by keyword
python bes_inspect.py demographics        # persona fields (the p_* profile block)
python bes_inspect.py experiments         # ⭐ auto-flag randomised items
python bes_inspect.py values partyId      # value labels + distribution
python bes_inspect.py sample --vars age,gender,partyId -n 5
```

Metadata (names/labels) reads in <1s without loading the 3.6 GB; only `values`
and `sample` touch data, reading just the columns you ask for.

## What the file actually is

| | |
|---|---|
| **Rows** | 126,840 — one per **respondent** |
| **Columns** | 13,381 variables |
| **Waves** | 31 (W1–W31), Feb 2014 – Jun 2026 |
| **Measures** | 3,407 distinct topics (after stripping `W<n>` suffix) |
| **Format** | **wide panel** — 1 row/person, each measure repeated per wave |

**Key structural facts (different from SocSci210):**

1. **Wide, not long.** SocSci210 is one row per (person × question). BES is one
   row per person, with `measureW1 … measureW31` columns. To get SocSci210 shape
   you **melt wide → long**.
2. **Wave suffix = time.** `partyIdW31` is party ID at wave 31. Strip `W<n>` to
   get the measure (`partyId`). A measure spanning 31 waves = a persistent topic.
3. **NaN = didn't take that wave.** A respondent only has values for the waves
   they participated in. Keep non-NaN person-wave observations when reshaping.
4. **Everything is coded + labelled.** 12,953 vars have value labels
   (`1 = Conservative`), which `values` and `sample` decode for you.

## Topic coverage (from `measures` / `search`)

Rich political + attitudinal content, e.g.: vote intention (`generalElectionVote`,
31w), most important issue (`mii`), party like/dislike (`likeCon`…`likeSNP`),
immigration (204 vars), EU/Brexit, economy, and a full demographic block.

## The persona fields (from `demographics`)

The `p_*` profile block is the clean persona layer — maps directly to
SocSci210's `demographic` struct: `p_education`, `p_socgrade`,
`p_gross_household`, `p_hh_size`, `p_ethnicity2`, `p_marital`, `p_housing`,
`p_job_sector`, plus `age`, `gender`, `country`, `gor` (region), `partyId`.

## The experiments (from `experiments`) — the SocSci210 gold

Keyword-flagged randomised items, e.g. the **Scottish independence question-
wording experiment**:

- `scotWordingBasic` — "Should Scotland be an independent country?"
- `scotWordingAgree` — "Do you agree that Scotland should be an independent…?"
- `scotWordingRemain` — "Should Scotland remain in the UK or leave?"

Each respondent saw **one** randomly-assigned wording (confirmed: `values`
shows ~440 non-null of 40k rows — a random subset). That's exactly a
`{condition → outcome}` experiment: the wording is `condition_num`, the answer
is `response`, the `p_*` block is the persona.

⚠️ **Caveat:** keyword flagging only catches items whose *label* says
experiment/random/wording. BES has more experiments where the randomisation
lives in a separate allocation variable and the items look like normal
questions. **The questionnaire PDF (`bes-questions.pdf`) is the authoritative
source** — use `experiments`/`search` to find candidates, then confirm the
manipulation in the PDF.

## Next step toward a UK dataset

1. Pick an experiment (start with `scotWording*`).
2. Confirm the design in the questionnaire PDF.
3. Melt the relevant columns wide → long: one row per (respondent × item), with
   the randomised wording as `condition`, the answer as `response`, and the
   `p_*` fields as the persona — i.e. the SocSci210 schema.
