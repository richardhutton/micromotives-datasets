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

### The 43, ranked by what fills the gaps in the UK layer

**`gap` is how far an experiment sits from the nearest UK study already built,
in topic space.** Every study's title is embedded and projected to a map by
`scripts/coverage_map.py`; the gap is the distance to the closest UK point on it.
Two UK studies already built sit **3.28** apart on average, so:

| gap | means |
|---|---|
| ~2.2 | new territory — nothing like it in the dataset |
| ~1.0 | partly new |
| under 0.5 | a near-duplicate of something already built |

**Why this measure and not category counts.** SocSci210's own paper
(arXiv:2509.05830) treats diversity as spread in embedding space — its Figure 2
is a projection of question embeddings against SubPop and Psych101 — not as
counts per bucket. `coverage_map.py` says the same in its docstring: six
categories "cannot show that two 'moral/social/cognition' studies are about
completely different things, and the holes worth seeing are finer than a bucket".

**And the comparison is against the UK layer only.** Measured against the whole
corpus, the best picks come out as US social-psychology studies — true, and
useless, because the point is UK representation. TESS supplies experiment
designs that transfer; it cannot supply UK respondents.

`wv` is how many waves it ran in. More waves, more rows.

#### Tier A — build first (7)

| gap | id | category | wv | title |
|---|---|---|---|---|
| 2.22 | 9.4 | attitudes | 1 | Measuring identity |
| 1.62 | 9.43 | health | 1 | Mental health questions comparisons |
| 1.41 | 9.48 | work-money | 1 | Labour market expectations |
| 1.39 | 9.17 | sensitive | 2 | Measuring sexual identity using direct and indirect questioning |
| 1.33 | 9.24 | health | 1 | Variations of the EQ-5D questions |
| 1.26 | 9.18 | wellbeing | 2 | What do the general population regard as "successful ageing"? |
| 1.23 | 9.36 | health | 1 | Alcohol consumption |

#### Tier B — build next (5)

| gap | id | category | wv | title |
|---|---|---|---|---|
| 1.20 | 9.20 | wellbeing | 1 | Presentation of response options in satisfaction questions |
| 1.13 | 9.31 | health | 1 | Comparison of ReQoL-10 to other scales |
| 1.11 | 9.12 | health | 2 | Measuring change in self-assessed disability |
| 1.10 | 9.42 | attitudes | 1 | Understanding of the long-term future |
| 1.09 | 9.39 | family-care | 1 | Vignettes: measuring flexibility stigma — double whammy or femininity stigma |

#### Tier C — good value, and multi-wave so the rows multiply (4)

| gap | id | category | wv | title |
|---|---|---|---|---|
| 1.07 | 9.13 | work-money | 2 | Associated Study: measuring time and risk preferences |
| 1.02 | 9.11 | work-money | 3 | Subjective expectations about the returns to higher education and decisions to attend university |
| 0.94 | 9.9 | family-care | 2 | Context effects in fertility decisions |
| 0.88 | 9.47 | family-care | 1 | Identification of informal caregiving |

#### Not selected, and why

Everything below a gap of about 0.85 duplicates ground the UK layer already
covers. The lowest are **9.40** (cognitive reflection and politically motivated
reasoning) and **9.38** (national identity) at 0.09, then **9.49**, **9.30**,
**9.25**, **9.16** — all under 0.2. The UK layer is currently Brexit, immigration
and party politics almost end to end, so another politics experiment adds the
least of anything available.

The 8 consent and 7 question-form experiments mostly sit low for the same
reason, with four exceptions kept in view: **8.14**, **8.3**, **8.11** and
**8.5** all score 1.24-1.41. They are survey-methodology experiments, so the
condition is a question format rather than a situation, but they genuinely
occupy empty space.

#### A correction worth keeping

An earlier version of this section ranked the 44 by how interesting the
condition text looked, and put 9.40, 9.38, 9.16, 9.30 and 9.26 in the top tier.
Measured against the UK layer, those are **five of the weakest in the whole
list**. Ranking by "which experiment is more interesting" and ranking by "what is
missing" give nearly opposite answers, and only the second one serves a dataset
whose purpose is UK coverage.

#### What this selection buys

| | now | after the 16 |
|---|---|---|
| health experiments in the UK layer | 0 | 5 |
| wellbeing | 0 | 2 |
| UK share of corpus rows | 35% | ~40% |

Health and wellbeing are the categories TESS cannot fill: norms around illness,
drinking, ageing and mental health do not transfer across countries the way an
attitude-framing experiment does.

## 4. The plan: 16 more experiments

**Tier A (7) + Tier B (5) + Tier C (4) = 16**, in that order.

### Step 1 — triage, half a session

Check all 16 against their wave questionnaire PDFs for whether the condition
wording actually exists. **Nobody has done this for any experiment except 9.10.**
`SocSci-UK_MASTER.md` flags it as "the largest unknown left, and resolving it can
only move the count down". For 9.10 the wording was there word-for-word; for the
rest it is unverified, and anything that fails drops out and is replaced from the
next band down.

Output: a buildable list, so the 16 are picked from fact rather than hope.

### Step 2 — build, 2–4 sessions

Estimated **1–2 hours per experiment** where the wording exists. That is
extrapolated from a single build, so treat it as a range. 9.10 took a full
session, but most of that was one-off machinery now reusable:

- `Condition.template` — a factorial declared as a template plus dimensions,
  expanded on load. 480 arms from ~40 reviewable lines of YAML.
- `Recipe.participant_id_var` — one person keeps one id across waves.

Both are inert for every existing study (all 41 rebuilt, zero row-count changes).
The three remaining scenario studies need no new machinery at all.

**Batch by wave where it helps.** The 16 are spread across waves, so the
per-wave saving is smaller than it would be for a cheapest-first selection — that
is the cost of choosing on coverage instead of convenience, and it is worth
paying. The clusters that do exist: waves 8-9 carry 9.17 and 9.18, waves 6-7
carry 9.12 and 9.13, wave 16 carries 9.39, 9.42 and 9.43.

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
