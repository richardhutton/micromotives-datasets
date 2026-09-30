# scripts/

Ad-hoc **inspection** tools — how we look at a source dataset *before* writing a
proper `sources/` adapter for it. They only read and print; they don't write to
`data/`. Run everything through uv from the repo root:

```sh
uv run python scripts/<script>.py <command> [options]
```

Two scripts today:

| Script            | Inspects                              | Needs                         |
|-------------------|---------------------------------------|-------------------------------|
| `explore.py`      | **SocSci210** (any HF dataset)        | network only — no download    |
| `bes_inspect.py`  | **British Election Study** panel `.dta` | the `.dta` file on disk        |

---

## `explore.py` — query SocSci210

Leans on the Hugging Face **datasets-server** REST API, so it inspects the
schema, browses rows, and reads column stats **without downloading the 9.4 GB
dataset**. Only `mappings` pulls small JSON files down. Defaults target
`socratesft/SocSci210` (`--dataset` / `--config` / `--split` override).

Transient `429` (rate-limit) and `500 "index loading"` responses are retried
with backoff automatically — they're not permissions errors; wait and retry.

| Command    | What it shows |
|------------|---------------|
| `org`      | All datasets & models published by an org (default `socratesft`). |
| `info`     | Configs, splits, row counts, and the full (nested) column schema + size. |
| `sample`   | A few rows, each field truncated to one line — a quick look inside. |
| `read`     | The **full** text of one row's fields (great for reading `prompt` / `reasoning`). |
| `stats`    | Per-column statistics: value counts, histograms, null rates. |
| `dpo`      | Reconstructs DPO preference pairs `{prompt, chosen, rejected}` from the rows (they aren't stored on HF — see the paper §4/§5.5). |
| `mappings` | Downloads & summarises the `metadata/*.json` split files (train/eval logic). |

**Examples**

```sh
# What's the schema, how many rows, how big?
uv run python scripts/explore.py info

# Peek at 3 rows
uv run python scripts/explore.py sample -n 3

# Read one row's full prompt + reasoning + stimulus + response
uv run python scripts/explore.py read --row 0 --fields prompt,reasoning,stimuli,response

# Column-level distributions (top 10 values each)
uv run python scripts/explore.py stats --top 10

# See how a DPO pair is built (scan 300 rows for a contested cell)
uv run python scripts/explore.py dpo --scan 300 --pairs 3

# What else has the org published?
uv run python scripts/explore.py org
```

The `(P,c,o,r)` fields map to these SocSci210 columns: `demographic` →
**persona**, `stimuli`/`condition_num` → **condition**, `prompt` frames the
**outcome** question, `response` → **response**. `study_id` is the OSF 5-char
code; `task_num` indexes multiple items per respondent. Use `read` to see them
in full on a real row.

---

## `bes_inspect.py` — inspect the BES panel `.dta`

Same idea for the **British Election Study** Internet Panel — a *wide* panel
(~127k respondents × ~13k columns) where most measures repeat per wave with a
`W<n>` suffix. Reads metadata (names + labels + value labels) in under a second
without loading the 3.6 GB of data; only `values` and `sample` touch the data.

Point it at your local file with `--dta` (default is hard-coded to
`~/bes-data/BES2024_W31_Panel_v31.05.dta` — override it):

| Command        | What it shows |
|----------------|---------------|
| `overview`     | Dimensions, waves, measure count, label coverage. |
| `catalog`      | Dump **all** variables + labels + wave to a CSV. |
| `measures`     | Distinct measures (suffix stripped) + which waves they span. |
| `search TERM`  | Variables whose name/label matches a keyword. |
| `demographics` | Auto-detected demographic variables (the persona fields). |
| `experiments`  | Auto-flagged experiment / randomisation variables (the conditions). |
| `values VAR`   | Value labels + distribution for one variable. |
| `sample`       | A few respondents across chosen variables. |

**Examples**

```sh
uv run python scripts/bes_inspect.py overview
uv run python scripts/bes_inspect.py search immigration
uv run python scripts/bes_inspect.py experiments          # find the randomised items
uv run python scripts/bes_inspect.py values partyIdW31
uv run python scripts/bes_inspect.py sample --vars ageW1,gender,partyIdW31 -n 5
```

> BES data is licensed — keep the `.dta` under `data/raw/` (gitignored) or
> outside the repo entirely. Never commit it.

---

## From inspection → adapter

These scripts are the reconnaissance step. Once we understand a source's shape,
the reusable logic moves into `src/micromotives_datasets/sources/` (e.g.
`socsci210.py`, `bes.py`) which yields validated `Row` objects the pipeline can
melt to Parquet. The scripts stay as ad-hoc explorers.
