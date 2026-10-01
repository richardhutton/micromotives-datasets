# SocSci210 — dataset inspector

A tiny CLI for poking around the datasets published by the
[`socratesft`](https://huggingface.co/socratesft) org on Hugging Face —
what's inside, what the schema looks like, and how the data is split for
training.

It works **without downloading the 9.4 GB dataset**: schema, rows, and
statistics come from the Hugging Face *datasets-server* REST API. Only the
small `metadata/*.json` split files are pulled down (by the `mappings` command).

## Setup

```bash
pip install -r requirements.txt
```

Needs only `requests` + `huggingface_hub` (both light). Python 3.9+.

## Commands

```bash
python explore.py org                 # list the org's datasets & models
python explore.py info                # configs, splits, row counts, schema
python explore.py sample -n 3         # a few rows, each field on one line
python explore.py read --row 0 \
       --fields prompt,reasoning      # full untruncated text of chosen fields
python explore.py stats               # per-column stats (value counts, ranges)
python explore.py mappings            # summarize the train/eval split files
python explore.py dpo                 # reconstruct DPO {prompt,chosen,rejected} pairs
```

Every command takes `--dataset`, `--config`, `--split` so you can point it at
any public dataset, not just SocSci210. Run `python explore.py <cmd> -h` for
per-command options.

---

## What's in the `socratesft` org

- **1 dataset:** `socratesft/SocSci210` — the training data below.
- **4 models**, fine-tuned on it: Llama-3-8B and Qwen2.5-14B, each in an
  **SFT** (supervised fine-tune) and a **DPO** (direct preference optimization)
  variant. `socrates-*-sft` → `socrates-*-dpo`.

Paper: *Finetuning LLMs for Human Behavior Prediction in Social Science
Experiments* ([arXiv:2509.05830](https://arxiv.org/abs/2509.05830)).

## What SocSci210 actually is

**2,901,390 rows.** Each row is one simulated survey answer: given a
**persona** (real survey respondent demographics) and a **stimulus** (an
experimental scenario + question), what numeric **response** would that person
give — and the model's **reasoning** for it.

The name = the **210 studies** it's built from (see `mappings` below).

### Schema (`python explore.py info`)

| column | type | what it is |
|---|---|---|
| `sample_id` | int64 | id of the (participant × question) task |
| `participant` | int64 | id of the survey respondent |
| `demographic` | **struct (16 fields)** | the persona: `age`, `gender`, `education`, `employment`, `ethnicity`, `income`, `party_id`, `ideology`, `location`, `marital_status`, `household_size`, `housing_*`, `metro_status`, `internet_access`, `phone_service` |
| `stimuli` | string | the scenario the respondent read + the question asked |
| `prompt` | string | the **full LLM prompt** — persona rendered as text + question + answer instructions |
| `reasoning` | string | model-written rationale for the answer (the chain-of-thought target) |
| `response` | int64 | the numeric answer (e.g. a 1–7 Likert rating) — the **label** |
| `condition_num` | int64 | which experimental condition the respondent was in |
| `task_num` | int64 | which question within the study |
| `study_id` | string | 5-char id of the source study (e.g. `9nphm`) |

### How a training example is built

The `prompt` column is the model input and it's assembled from the structured
fields. Roughly:

```
demographic{...}  ──►  "You are a survey respondent with the following
                        demographic profile: Age: 34, Gender: Female, ..."
stimuli           ──►  "You read 'Jaime is 20 years old...'  How likely is it
                        that Jaime will still identify as non-binary in 5 years?"
                  ──►  answer instructions (e.g. "answer 1–7")
```

The training targets are `reasoning` (the rationale text) then `response` (the
number). So the model learns: **persona + scenario → reasoning → predicted
human answer.** See it for real:

```bash
python explore.py read --row 0 --fields prompt,reasoning,response
```

### How the data is split for training (`python explore.py mappings`)

Three JSON files in `metadata/` define three *different* ways to split, so you
can test generalization along three axes:

| file | shape | meaning |
|---|---|---|
| `participant_mapping.json` | `{seen: [170 studies], unseen: [40 studies]}` | **study-level** hold-out — 170 + 40 = **210** studies. Can the model generalize to entirely unseen studies? |
| `task_mapping.json` | `{study_id: {train:[...], eval:[...]}}` for 73 studies | **75/25 split by task** — hold out some questions within a seen study. |
| `condition_mapping.json` | `{study_id: {train:[...], eval:[...]}}` for 129 studies | **75/25 split by experimental condition** — hold out some conditions within a seen study. |

To reproduce a split you filter the dataset by `study_id` / `task_num` /
`condition_num` against the relevant mapping.

## The DPO data — it isn't a separate file

The org publishes **one** dataset (SocSci210) and four models. There is **no
separate DPO dataset** — the preference pairs used to train the `-dpo` models
are *constructed on the fly* from the same rows (paper §4 + §5.5).

**How a pair is built (demographic contrastive pairs):**

1. Pick a **focal persona** `p_pos` who answered question `o` under condition
   `c` with response `r_pos`. → the prompt + the **chosen** answer.
2. Find another participant `p_neg` who answered the **same** `o` under the
   **same** `c` but gave a **different** number `r_neg`. → the **rejected** answer.
3. The training pair: given `p_pos`'s prompt, **prefer `r_pos` over `r_neg`**.
   Only the *number* `r_neg` is borrowed — the prompt keeps `p_pos`'s persona.

So a "cell" = `(study_id, condition_num, task_num)`. Any cell where personas
disagreed yields a chosen/rejected contrast. Inspect them with:

```bash
python explore.py dpo                 # scans 300 rows, shows contrast cells
python explore.py dpo --scan 500 --pairs 5 --full
```

Example output (one cell): 14 personas answered the same question; the focal
persona's real answer `5` becomes **chosen**, while `7`, `6`, `4` from other
personas become **rejected** alternatives. The DPO loss (eq. 2) then pushes the
model to rank the focal person's actual answer above the others.

### What DPO buys you (from the paper's results)

| metric | best method | note |
|---|---|---|
| **individual accuracy** ↑ | **DPO** (72.6 / 74.0) | its demographic contrastive pairs sharpen per-person prediction |
| **distribution alignment** ↓ | **SFT** (and SFT+Reasoning within-study) | DPO is *worse* than SFT on matching the response distribution |

DPO wins individual accuracy but trades away distributional alignment; plain
SFT is the opposite. Reasoning-augmented SFT only helps distribution *within* a
known study. Pick the objective for the metric you care about.

---

## Going deeper (optional, needs `datasets`)

The REST API caps rows per request. To scan or download the full thing:

```python
# pip install datasets
from datasets import load_dataset
from huggingface_hub import hf_hub_download
import json

# stream — no full download
ds = load_dataset("socratesft/SocSci210", split="train", streaming=True)
print(next(iter(ds)))

# reproduce the "unseen studies" test split
mp = json.load(
    open(
        hf_hub_download(
            "socratesft/SocSci210", "metadata/participant_mapping.json", repo_type="dataset"
        )
    )
)
unseen = set(mp["unseen"])
full = load_dataset("socratesft/SocSci210", split="train")
test = full.filter(lambda r: r["study_id"] in unseen)
```
