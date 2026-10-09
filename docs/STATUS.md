# SocSci-UK — where the project is

Last updated 9 October 2026. One page, read top to bottom. `SocSci-UK_MASTER.md`
is the full reference and has accreted over months; this is the current picture.

---

## 1. The goal

Build a UK behavioural-prediction dataset comparable to **SocSci210**
(arXiv:2509.05830). Every row is four things:

| part | what it is |
|---|---|
| **persona** | who the respondent is — age, sex, region, education, employment |
| **condition** | the randomised stimulus text they actually read |
| **outcome** | the question they were asked |
| **response** | what they answered |

The point is a model that predicts how a described person answers a described
question under a described condition. SocSci210 did this for the US. Nobody has
done it for the UK.

---

## 2. Where it stands

**436,306 rows across 43 experiments**, all QC-passed and on disk at
`data/processed/`.

| | experiments | rows |
|---|---|---|
| US (TESS deposits) | 28 | 283,935 |
| UK-native | 15 | 152,371 |
| **total** | **43** | **436,306** |

Ten largest: `EFXNLX` 49,395 · `evnyh` 33,932 · `es4xw` 32,228 · `9xw67_conjoint`
20,373 · `b87sm` 19,282 · `8ctbk` 17,464 · `cug34` 15,091 · `z358z` 14,702 ·
`POMIFD` 13,268 · `ye2ej` 12,971.

### The licence position, which shapes everything

| source | licence | can it be published? |
|---|---|---|
| 24 TESS deposits | none stated | **No** |
| 4 Harvard UK deposits | CC0 1.0 | **Yes** |
| `POMIFD` | none, but author gave written permission to use | No |
| UKDS SN 6849 (Innovation Panel) | UKDS End User Licence | **No** |
| BES Internet Panel | BES own terms — grants distribution, share-alike | **Yes, conditionally** |

Most of the corpus cannot be redistributed. That is not a blocker for building or
for research use; it is a blocker for release.

---

## 3. The Innovation Panel — the main remaining source

UKDS SN 6849. 93 experiments across 17 waves, all screened in
`data/catalog/innovation_panel_experiments.json` and rendered to
`docs/UKDS_UNBUILT.md`.

| verdict | count |
|---|---|
| **build** | 44 |
| marginal | 9 |
| drop | 40 |

**1 of the 44 is built** — 9.10, the housework scenarios, 9,631 rows across waves
5 and 6. **43 remain.**

### The 43, ranked by what they are worth

**Tier 1 — made-up scenarios (3 left).** A described situation, then a judgement.
The richest condition text available and the closest thing to SocSci210's
conjoints.

| id | category | wave | what |
|---|---|---|---|
| 9.39 | family-care | 16 | Homeworking and flexibility stigma — same CV, name changed from Charlotte Davies to Paul Taylor |
| 9.26 | attitudes | 11 | Immigration residency rights under competition for public services |
| 9.30 | technology | 14 | Automation threat × timeframe, 2×2 |

**Tier 2 — substantive attitudes under a real randomisation (11).**

| id | category | wave | what |
|---|---|---|---|
| 9.40 | attitudes | 16 | Cognitive reflection × politically motivated reasoning |
| 9.41 | attitudes | 16 | Climate worry, "you" vs "future generations" |
| 9.42 | attitudes | 16 | Understanding of the long-term future |
| 9.38 | attitudes | 15 | National identity |
| 9.14 | attitudes | 7 | Willingness to pay environmental taxes |
| 9.16 | attitudes | 8, 9 | Immigration attitudes via list experiment |
| 9.34 | work-money | 15 | Marginal propensity to consume |
| 9.22 | work-money | 10 | Financial management within couples |
| 9.17 | sensitive | 8, 9 | Sexual identity, direct vs indirect questioning |
| 9.9 | family-care | 4, 5 | Fertility intentions under priming |
| 9.18 | wellbeing | 9, 17 | What counts as "successful ageing" |

**Tier 3 — measurement variants on substantive topics (14).** Valid rows; the
condition is a question format rather than a situation. 9.11 (returns to higher
education) and 9.13 (time and risk preferences) are the strongest, because both
carry a real decision.

9.11 · 9.13 · 9.5 · 9.48 · 9.43 · 9.36 · 9.24 · 9.31 · 9.12 · 9.35 · 9.47 ·
9.23 · 9.4 · 9.20

**Tier 4 — weakest for this dataset (15).**

- **consent** (8): 9.6, 9.21, 9.25, 9.29, 9.33, 9.46, 9.49, 9.50. Outcome is
  whether the person agreed to data linkage. A real decision under randomised
  wording, so legitimate, but narrow and repetitive.
- **question-form** (7): 8.3, 8.4, 8.5, 8.8, 8.10, 8.11, 8.14. Outcome is
  response style. This is the panel's own survey-methodology work.

### Where the value sits

| category | count | Tier 1–2 |
|---|---|---|
| attitudes | 8 | 7 |
| consent | 8 | 0 |
| question-form | 7 | 0 |
| work-money | 6 | 2 |
| family-care | 6 | 3 |
| health | 5 | 0 |
| wellbeing | 2 | 1 |
| technology | 1 | 1 |
| sensitive | 1 | 1 |

`attitudes` is where the value concentrates. `health` is five instrument
comparisons — volume, not variety. `consent` and `question-form` are 15 of 44
and bottom-tier.

---

## 4. The plan: 17 more experiments

**Tier 1 (3) + Tier 2 (11) + 9.11 and 9.13 from Tier 3 = 16.** Plus one more
from Tier 3 by wave convenience = **17**.

### Step 1 — triage, half a session

Check all 43 against their wave questionnaire PDFs for whether the condition
wording actually exists. **Nobody has done this.** `SocSci-UK_MASTER.md` flags it
as "the largest unknown left, and resolving it can only move the count down". For
9.10 the wording was there word-for-word; for the other 43 it is unverified.

Output: a buildable list, so the 17 are picked from fact rather than hope.

### Step 2 — build, 2–4 sessions

Estimated **1–2 hours per experiment** where the wording exists. That is
extrapolated from a single build, so treat it as a range. 9.10 took a full
session, but most of that was one-off machinery now reusable:

- `Condition.template` — a factorial declared as a template plus dimensions,
  expanded on load. 480 arms from ~40 reviewable lines of YAML.
- `Recipe.participant_id_var` — one person keeps one id across waves.

Both are inert for every existing study (all 41 rebuilt, zero row-count changes).
The three remaining scenario studies need no new machinery at all.

**Batch by wave.** Wave 16 is the strongest single batch in the panel — 9.39,
9.40, 9.41, 9.42, 9.43 — one questionnaire, four Tier 1–2 experiments.

---

## 5. What is parked, and why

Work done on 7–9 October that is **not** the dataset. All committed, all
documented, all resumable. It came out of asking whether the dataset's rows
actually predict anything, which is a fair question and not the goal.

| what | where | state |
|---|---|---|
| Person profiles from the Innovation Panel | `scripts/build_profiles.py` | 100 built, gitignored |
| The holdout test (3 modes) | `scripts/holdout3.py` | works; 100-question result banked |
| **The ceiling method** | `scripts/ceiling.py` | **keep this one** — see below |
| Per-topic scoreboard | `scripts/scoreboard.py` | works |
| Synthetic probe (big vs local model) | `scripts/synthetic_probe.py` | works |
| BES panel | `data/raw/bes_panel/` | downloaded, inspected, not built |

### The one finding worth carrying forward

**Never quote an accuracy without its ceiling beside it.**

People do not reproduce their own survey answers. Measured two ways here:

- IP 9.10 shows the same person the identical scenario a year apart — they give
  the same answer **27.7%** of the time, against 19.3% for random guessing.
- Across the profiles, a person's latest answer matches their own previous
  answer **60.8%** of the time, against 25.3% chance.

So a prediction scored at 39% is not "39% right" — it is about a third of the
range that was ever available. **Park's own headline numbers were already
normalised this way** (arXiv:2411.10109 reports 82% *of participants' two-week
test-retest consistency*, not 82% correct), which was discovered after arriving
at the same method independently.

### The constraint that parked the rest

UKDS data cannot leave the machine, so the prediction work ran on local
`qwen3:8b`. On synthetic data built so that a learnable pattern provably exists,
that model scores **20.0% against 19.3% for random guessing — it is at chance**,
while a hosted frontier model on identical input reaches **44%** of the maximum.
The local route is a dead end for prompted prediction; fine-tuning is a different
question and remains open.

Two emails address it:

| to | asking | status |
|---|---|---|
| BES | does their Licensed Use cover sending panel responses to a hosted model | **sent 9 Oct** |
| UKDS | permission under EUL clause 5.5 for SN 6849 | drafted, not sent |

Neither blocks anything. Downloading, building, local models and local
fine-tuning are all permitted today on both sources.

---

## 6. Standing constraints

- **Raw and processed data never enter git.** `data/raw/`, `data/profiles/` and
  `data/processed/*.parquet` are gitignored. `data/catalog/` is tracked.
- **Nothing UKDS-derived has left this machine.** `jev.RESTRICTED` refuses
  `source="ukds"`.
- **The repo has never been pushed.** 80+ commits ahead of `origin/main`. The
  recipes contain questionnaire wording, which the EUL counts as part of the Data
  Collection, so a push would be a disclosure. Decide deliberately before pushing.
- **The questionnaire is the authority on stimulus wording**, not the data file's
  labels. In 9.10 the archived labels were not merely truncated but wrong — two
  opposite housework splits shared one label string.
