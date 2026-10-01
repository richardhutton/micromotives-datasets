# SocSci-UK — Master Reference

*Single consolidated doc for the UK behavioural-prediction dataset project.*
*Merged 2026-09-24 from the earlier scattered notes (now in `archive/`).*
*Study-level detail lives in the one CSV: `tess_uk_foundation_sources.csv`.*

---

## 0. What this project is (the overview)

**Goal:** build **SocSci-UK** — a UK dataset for training LLMs to predict human
behaviour, in the shape of Stanford's **SocSci210** (paper: *Finetuning LLMs for
Human Behavior Prediction in Social Science Experiments*, arXiv:2509.05830).

**Two data streams feed it:**

1. **US-transfer layer** — TESS/SocSci210 studies whose *topic is universal* so
   they transfer to a UK population (the "foundation layer", §4).
2. **UK-native layer** — real UK experiments and panels (Dataverse sets, BES,
   DEL) that make the dataset genuinely British, not just US-transferred (§5).

**The task the model learns:** given a **persona** (demographics) + a
**stimulus** (an experimental scenario + question), predict the **response** (a
single integer). The UK-native BES layer adds a **time** axis SocSci210 lacks:
predict how a real person's attitude *moves over 12 years*.

**The whole workflow at a glance:**

```
  DATA SOURCES            BUILD PIPELINE (§8)        DATASET        TRAIN (§9)       USE
 ┌─────────────┐         ┌──────────────────┐      ┌──────────┐   ┌──────────┐   ┌───────────┐
 │ SocSci210   │─ pull ─▶│                  │      │          │   │  QLoRA   │   │  simulate │
 │ TESS / OSF  │─ build ▶│ agent + judgment │─rows▶│ (P,c,o,r)│SFT│ Qwen3-8B │──▶│ persona → │
 │ UK Dataverse│─ build ▶│  (Jev) + human   │      │  rows    │   │  (dense) │   │ response  │
 │ UKDS/IP, BES│─ build ▶│                  │      │          │   │          │   │ (+ quote) │
 └─────────────┘         └──────────────────┘      └──────────┘   └──────────┘   └───────────┘
   §3–§5                       §8                                      §9            §9
```

---

## 1. The prediction schema (what every row is)

One canonical row, same shape as SocSci210 — the tuple **(P, c, o, r)**:

| Part | What it is | SocSci210 column |
|---|---|---|
| **Persona (P)** | the demographic block, rendered as text | `demographic` (16-field struct) |
| **Condition (c)** | the treatment/arm — *rendered as the stimulus text they read* | `stimuli` (text) + `condition_num` (index) |
| **Outcome question (o)** | what they were asked | `stimuli` (text) + `task_num` (index) |
| **Response (r)** | the answer as ONE integer (single token) | `response` (int) |

**Key clarifications (learned the hard way):**
- The **condition *is* the stimulus** — the arm is realised as the text the
  person reads, not a separate field. In SocSci210 both the condition and the
  outcome question are rendered into the single `stimuli` string, each with an
  integer index (`condition_num`, `task_num`) used to build the unseen-condition
  / unseen-outcome generalisation splits.
- **Persona and outcome are distinct parts** — Figures 1 & 3 of the paper label
  all four (Persona · Condition · Outcome · Response). Don't collapse them.

**Why the condition is the whole point — this is not just a survey.** Strip the
condition and you have a poll: *"people like this answer X."* Keep it and you
have something a decision-maker can act on: *"people like this answer X when
shown A, and Y when shown B."* **The gap between A and B, for the same persona,
is the treatment effect** — the thing anyone deciding whether to act actually
wants to know. A poll tells you where opinion sits; the condition tells you how
it *moves* when you change what people are shown.

**Two build rules:**
1. **Response is always one integer = one token.** Forced choice → 1/2; rating →
   scale value (1–7, 0–100); MaxDiff → 1/2. The stimulus text can be any length;
   the target must stay one token (SFT loss lands on a single answer token).
2. **Conjoint rows keep their attributes as structured metadata**, not just in
   the prompt — otherwise you can't score how much each attribute moved the
   choice in a held-out study (that score *is* the treatment-effect result).

---

## 2. Data sources — the map

| Source | Layer | Unit | What it contributes | Section |
|---|---|---|---|---|
| **SocSci210** | US reference | individual | 210 US TESS studies, 2.9M ready-made rows | §3 |
| **TESS foundation** | US-transfer | individual | 202 UK-appropriate studies (75 pull / 120 build) | §4 |
| **UK Dataverse sets** | UK-native | individual | Brexit, immigration, persuasion conjoints/vignettes | §5a |
| **BES Internet Panel** | UK-native | individual × wave | longitudinal: attitude trajectories over 31 waves / 12 yrs | §5b |
| **DEL** | UK-native | individual × wave | aid/climate/humanitarian; panels give stimulus + time | §5c |

The **US-transfer** layer is broad-but-shallow (many topics, one-shot). The
**UK-native** layer is the differentiator: real UK politics, and the *time* axis.

---

## 3. SocSci210 — the US reference dataset

**2,901,390 rows** across **210 studies** (`socratesft/SocSci210` on HF). **One
row = one respondent answering one question** (so a person who answered 3
questions appears in 3 rows).

**The 10 columns, in plain English:**

| column&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | type | what it actually is |
|:------------------------|------|---------------------|
| `study_id`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | string | which experiment this row came from — the OSF 5-char code (e.g. `egmxd`). **The join key.** 210 distinct values. |
| `participant`&nbsp;&nbsp; | int | which respondent — a person id. The same person recurs across the rows for each question they answered. |
| `demographic`&nbsp;&nbsp; | struct (16) | **the persona (P)** — that respondent's attributes: age, gender, education, income, party_id, ideology, ethnicity, marital_status, employment, location, household_size, housing_*, metro_status, internet_access, phone_service. |
| `condition_num` | int | **which experimental arm the respondent was put in (c).** A study has several conditions (e.g. arm 0 = saw message A, arm 1 = saw message B). This number says which one this person got. It's the treatment. |
| `task_num`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | int | **which outcome question within the study (o).** A study asks several questions; `task_num` indexes them (0, 1, 2 …). So "study `egmxd`, task_num 2" = the 3rd question that study asked. *This is the one that's easy to miss.* |
| `stimuli`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | string | the actual text the respondent read — the condition's scenario **and** the outcome question, rendered together. (`condition_num`/`task_num` are the *indices*; `stimuli` is the *words* those indices point to.) |
| `prompt`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | string | the full LLM input: the persona written out as text + the `stimuli` + answer instructions. What the model is actually fed. |
| `reasoning`&nbsp;&nbsp;&nbsp;&nbsp; | string | a model-written rationale for the answer — the chain-of-thought training target (only used by the reasoning-augmented variant). |
| `response`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | int | **the answer, as one integer (r)** — e.g. a 1–7 Likert rating or a 1/2 forced choice. **The label the model predicts.** |
| `sample_id`&nbsp;&nbsp;&nbsp;&nbsp; | int | a unique id for this one (respondent × question) row. Just a row key. |

**How the indices fit together:** `(study_id, condition_num, task_num)` pins down
one **cell** — a specific study, arm, and question. Many participants share a
cell (they got the same arm and answered the same question) but give different
`response` values — and *that spread of answers within a cell is the response
distribution* the model is trying to match. `condition_num` and `task_num` also
exist so you can build the held-out splits below (hide some arms, or some
questions, and test if the model generalises).

**Three generalisation splits** (in `metadata/*.json`):
`participant_mapping` (170 seen + 40 unseen studies), `task_mapping` (75/25 by
question, 73 studies), `condition_mapping` (75/25 by condition, 129 studies).

**Models & objectives** (4 released: Llama-3-8B, Qwen2.5-14B × SFT, DPO):
- **DPO** wins *individual accuracy* (its demographic contrastive pairs sharpen
  per-person prediction) but is *worse* on distribution alignment.
- **SFT** wins *distribution alignment*; reasoning-augmented SFT only helps
  distribution *within* a known study.
- No separate DPO dataset — preference pairs are built on the fly: focal persona's
  real answer = chosen, another persona's different answer to the same (c,o) = rejected.

Inspect with `explore.py` (org / info / sample / read / stats / mappings / dpo) —
works off the HF datasets-server API, no full download.

---

## 4. TESS foundation layer — UK-appropriate US studies  ⭐ (the working set)

Blank-slate crawl of tessexperiments.org/paststudies (**517 studies**, 2003–2024),
classified by the test: *does the stimulus/outcome depend on US institutions,
parties, racial categories, prices or events?* KEEP if no.

**202 are UK-appropriate (KEEP).** Of those:

| path | studies | detail |
|---|---|---|
| **pull from SocSci210** | 75 | rows already built (~1.06M); use `study_id` |
| **reconstruct from OSF** | 120 | data confirmed downloadable (`data_download` in CSV) |
| **no access** | 7 | private / withdrawn / empty |
| **usable now** | **195 / 202** | |

**Topic distribution (202 KEEP):**

| topic | studies | pull | build |
|---|---|---|---|
| moral / social / cognition | 68 | 18 | 48 |
| economics / behavioural | 34 | 11 | 21 |
| work / family / gender | 32 | 13 | 19 |
| health communication | 30 | 15 | 13 |
| survey methodology | 29 | 14 | 14 |
| cross-national | 9 | 4 | 5 |

**Two myths busted along the way:**
- SocSci210 skipped 127 UK-appropriate studies *not* because data was missing —
  its auto-parser hit attrition (SPSS `.sav` + Word `.doc` questionnaires).
- The "no OSF / pre-deposit era" worry was a scraping artifact: OSF codes sit as
  **plain text** on TESS pages (not links), and ~half are OSF **registrations**
  not nodes. All 202 have OSF deposits; even 2006 studies do.

**Access recipe for the 120:** `osf_code` → resolve via `api.osf.io/v2/guids/<code>/`
→ follow the files link (works for node *or* registration) → the "Data and
Materials" child component holds a `.sav`/`.csv` (or a zip of it) + questionnaire.
The verified download URL is already in the CSV's `data_download` column.

→ **All 202 studies with year, title, category, both IDs, buildable flag, URLs,
and download links are in `tess_uk_foundation_sources.csv`.**

---

## 5. UK-native datasets

### 5a. Harvard Dataverse UK experiments (all CC0)

The core UK experiments, in (persona · stimulus · condition · response) shape.
Persona = the YouGov profile block. Stimulus form varies per study.

| Dataset | Rows | Stimulus form | Response | DOI (`10.7910/DVN/…`) |
|---|---|---|---|---|
| Persuasion (political rhetoric) | 3,317 | 336 text arguments | MaxDiff (which most persuasive) | POMIFD |
| Brexit conjoint | 3,293 | negotiation-outcome profiles | forced choice | EFXNLX |
| Divided by the Vote | 1,635 | lodger / BBC vignettes | affective-polarisation rating | 35M5CV |
| For/Against Brexit | 19,986 obs | pro/anti Brexit messages | attitude scale, 2 waves | PZB01G |
| Pricing Immigration | 3,636 | conjoint with prices | choice | 6MRVOM |
| i-voting | 1,200 | voting-system conjoint | forced choice | RJTVG8 |
| Cyber Terrorism | 2,028 | TV news report (video→needs text) | support-for-retaliation scale | SACJHE |
| Vaccine allocation (13-ctry) | — | conjoint | 8 forced choices | PMV0TG |
| Anti-immigrant (22-ctry) | 45,402 | conjoint | choice | ZZYSIZ |
| Many Labs 1/2, PSA | — | various (OSF) | various | (OSF) |

**Added 2026-09-25 (search sweep, verified experiments, CC0):**

| Dataset | topic | design | DOI (`10.7910/DVN/…`) |
|---|---|---|---|
| A Tale of Two Peoples: Motivated Reasoning after Brexit (Sorace, Hobolt) | political cognition | survey experiment | QQM5MC |
| The Better Angels of Our Nature: Anti-Prejudice Norm, GB+DE (Blinder, Ford, Ivarsflaten) | prejudice / immigration norms | survey experiment | TLT65Z |
| Brexit as an Identity (Tilley) | identity / policy attitudes | survey experiment | X08IVC |
| Mind the Gap: Wealthy Voters Support Brexit (Green, Pahontu) | economic risk / Brexit | survey experiment (BES-heavy) | LOGVPZ |

**Coverage vs SocSci210's political topics:** UK-native covers immigration
(strong), Brexit-partisanship, cross-national, and partially foreign-policy /
electoral. **Genuine gaps** (US topics with no UK analogue yet): US race/ethnicity,
media/misinformation, inequality/welfare, UK institutions, political gender/LGBT.

**UK Data Service (ReShare) candidates — verified UK, but SAFEGUARDED (not CC0).**
A ReShare sweep found UK experiments in topics the CC0 Dataverse set lacks —
**environment** and **health** — all discrete-choice/WTP (conjoint-family):
`858763` Willingness to Pay for Birdsong (environment); `857401` Sexual Health
Service preferences, 45+ (health); `858683` AMR/antibiotics (health policy, but
GP sample, not general public). **Licence caveat:** UKDS *safeguarded* = free
registration + End User Licence, **no redistribution** — usable for research, but
check the EUL per study; do not treat as CC0. Full list + rejects (with reasons)
in `uk_dataverse_candidates.csv`. Search was **not exhaustive** — more remain on
both Dataverse and UKDS.

### 5b. BES Internet Panel — the longitudinal differentiator

`BES2024_W31_Panel_v31.05.dta` (3.6 GB). **126,840 respondents × 13,381 vars**,
**31 waves Feb 2014 – Jun 2026** (~12 yrs). DOI `10.5255/UKDA-SN-8202-4`.
Free registration; **private non-commercial use only — do not re-host**.

- **Wide panel** — 1 row/person, each measure repeated per wave (`partyIdW1…W31`).
  Melt wide→long to get SocSci210 shape.
- **Attrition is heavy:** median 5 of 31 waves; **39,864 (31%) did ≥10 waves** =
  the usable sequence-modelling core; 7,027 tracked W1→W31.
- **Persona is richer than SocSci210** (the `p_*` YouGov block): adds religion,
  media diet, vote history, personality (big-5), social grade, sexuality,
  disability; geography down to **constituency**. Only gap: no dwelling-type.
- **~1,700 substantive measures** (vote, Brexit, economy, immigration, welfare,
  NHS…), responses ordinal integers (`9999` = Don't know, strip it).

**The differentiator SocSci210 can't do:** *given a person's history through wave
t, predict their answer at t+k* — real individual trajectories. Train one model
for variable-horizon forecasting (put the **real target date** in the prompt, not
"+4 waves"; slide windows for many pairs/person).

**Experiments in BES:** the released file keeps outcomes but usually **strips the
condition/randomisation vars**. Truly recoverable `condition→outcome`: essentially
**one** (`scotWording`, W21 — 3 randomised Scottish-independence wordings). Richer
vignette/priming experiments need BES's supplementary files.

**Two iron rules for mixing stimulus/no-stimulus data:**
- Use an explicit **`Scenario: none` sentinel** so the model learns "no scenario →
  standing attitude" vs "scenario → react". Consistent natural word, not a token.
- **Never fabricate a stimulus onto a BES answer** — it was given with no stimulus;
  attaching an invented one teaches the model that stimuli don't matter.

### 5c. DEL (Development Engagement Lab)

YouGov-fielded, France/Germany/GB/US, 2020–2025, aid/humanitarian/climate. All
Harvard Dataverse, **CC0**. GB is a separate file (no country filtering). **Same
YouGov persona block** — no new crosswalk. Data paper `s41597-025-05135-0`.

- **Trackers** = observational cross-sections. **Panels** = time + experiments
  (~8,000 GB/wave). **Sandboxes** = the experiment programme (split-ballots,
  conjoints, list experiments).
- Adds **non-party topics** (aid, ODA, climate, feminism) with money/donation
  outcomes. Questionnaire (`Survey.docx`) + codebook (`Codebook.xlsx`) in every
  deposit → exact stimulus wording per arm available.
- Open: conjoint/list-experiment check on the 0-split Sandboxes; find Panel 2025
  GB file; pull one experiment end-to-end.

---

## 5d. Conjoint sub-corpus — the high-control training set

Conjoints are worth pulling out as their own set because they give **the most
control over what the model learns**. Every attribute is randomised
*independently*, so each one carries a clean marginal signal: you're not just
teaching "this persona chose package A", you're teaching "holding everything
else fixed, moving *this attribute* x→y shifts the choice by this much" (AMCE-
style structure — exactly the treatment-effect signal the engine is for).

**What it buys:** (1) attribute-level effects, not just outcomes — a grid of
manipulations per respondent, not one; (2) targeted held-out evals — hold out a
single *attribute level* and test if the model learned the dimension vs
memorised packages; (3) curated coverage — you choose which attributes/levels
appear. Unlocked by **Build Rule 2** (§1): keep the per-row attribute levels as
*structured metadata*, or you can't score how much each attribute moved the
choice in a held-out study.

**Keep two attribute sets separate:** the **respondent's persona** (`P` — who's
choosing) and the **profile attributes** (the thing being judged — part of the
stimulus/condition, *not* the persona). Separated, you can model persona ×
profile-attribute interactions ("does *this kind of person* weight *price* more?").
Conflated, the signal collapses.

**The conjoint sub-corpus (both layers):**

| study | layer | tier | profile attributes (what varies) | outcome |
|---|---|---|---|---|
| Brexit conjoint | UK-native | — | negotiation-outcome package attributes | forced choice |
| Pricing Immigration | UK-native | — | immigrant profile attributes **+ price** | choice |
| i-voting | UK-native | — | voting-system attributes | forced choice |
| Vaccine allocation (13-ctry) | UK-native | — | recipient profile attributes | 8 forced choices |
| Anti-immigrant (22-ctry) | UK-native | — | immigrant profile attributes | choice |
| DEL NGO-donation conjoint | UK-native | — | charity / appeal attributes | donation choice |
| `martin335` — privacy factorial vignette | TESS | KEEP | privacy-scenario attributes | privacy rating |
| `senS81` — ideal descriptive representation | TESS | JUDGEMENT | candidate attributes | evaluation |
| `hankinson707` — new housing development | TESS | JUDGEMENT | housing-development attributes | support |
| `hopkins365` — voting criteria (US federal) | TESS | JUDGEMENT | candidate / level attributes | choice |
| `simonovitsM17` — policy responsiveness | TESS | JUDGEMENT | policy attributes | choice |
| `claassen502` — candidate evaluation *(likely, verify)* | TESS | JUDGEMENT | candidate attributes | evaluation |

**Caveat — this is a lower bound.** The TESS side is identified by *title only*,
and conjoints are chronically under-titled, so the real count is higher. A
definitive list needs design-level inspection (open each OSF questionnaire/data
and look for multiple randomised profiles per respondent with attribute columns).
The `is_conjoint` column in `tess_uk_foundation_sources.csv` currently flags only
the title-confirmed KEEP one (`martin335`); the JUDGEMENT-tier conjoints above
live in `archive/tess_all_studies_classified.csv`.

### Why the UK layer leans conjoint (the strategy)

UK data is **scarce** relative to the abundant US data (SocSci210 = 2.9M rows).
That scarcity is a reason to *choose* the conjoint format, not a weakness —
conjoints give the most bang per respondent on two axes at once:

- **Data efficiency (more signal per person).** One respondent makes many
  choices over randomised profiles (5–10 tasks; Vaccine allocation = 8), so a
  3,600-person UK sample yields *tens of thousands* of rows, each a within-person
  contrast with clean marginal signal. A single-question survey gives one row per
  person. And the paper finds learning **saturates at ~10% of a study's data**
  (§5.5, Fig 4) — so you don't need US-scale N; a modest UK conjoint already hits
  the learnable ceiling.
- **Generalisation (transfers best).** SocSci210's strongest result is
  generalisation to **unseen conditions** (+71%, §5.4) — *"LLMs grasp the
  underlying effects of how condition manipulations influence responses."* A
  conjoint is pure condition manipulation, so it trains the axis the model
  transfers on: unseen attribute combinations (safe), unseen UK personas
  (plausible), and — the hopeful frontier — cross-domain decision structure.

**Upshot:** `US abundant → can afford shallow one-shot format; UK scarce → use
the format that maximises signal per respondent AND transfers best = conjoints.`
Both properties point the same way, so the UK conjoints (Pricing Immigration,
Brexit, i-voting, Vaccine allocation, Anti-immigrant, DEL donation) are the
highest-ROI part of the build — make one of them the **first end-to-end worked
example** and test held-out-attribute-level generalisation on real UK data.

**Two caveats (don't oversell):** (1) more rows per person ≠ that many
*independent* datapoints — within-person choices are correlated, so don't count
conjoint rows 1:1 against independent survey responses; (2) the target is
forced-choice (binary) — the gain is in attribute-effect learning, not in
matching a rich response *distribution*, which still wants enough people per cell.

---

## 5e. Other UK data sources to mine (source map)

Sources beyond §5a we have **not** fully harvested, by access tier.

**🏆 Understanding Society Innovation Panel** — the UK's de-facto TESS.
UKDS **study 7083** (Waves 1–17, 2008–2024, ~1,500 households, annual). A running
programme of **randomised experiments** on a longitudinal probability panel —
substantive (EQ-5D health, immigration vs public services, kids reporting parents'
occupation, mental-health question versions) *and* methodological (→ our
survey-methodology topic). **Purpose-built for experiments, so it RETAINS the
allocation/randomisation variables** (unlike BES, which stripped them) — that's
what makes reconstruction possible. Longitudinal → gives stimulus-reaction *and*
the time axis in one source. Docs: Innovation Panel User Guide (6849) +
per-wave "results from methodological experiments" working papers (name the
allocation vars). IP1–15 experiment-focused; IP16+ broadened. *Access:
safeguarded (UKDS registration + EUL).* Extraction: allocation flag → `condition`,
outcome item → `outcome`, UKHLS demographic block → `persona`, answer → `response`.
**→ full pull-and-reconstruct checklist: `innovation_panel_checklist.md`.**

**Other UK panels / cohorts (forecasting layer, safeguarded on UKDS):**
UKHLS main study (~40k households, richer than BES on non-political topics);
birth-cohort studies (NCDS, BCS70, Millennium Cohort, Next Steps); British Social
Attitudes (NatCen, annual — occasional split-ballot experiments).

**Open / CC0 pools (redistributable — highest priority for an open release):**
OSF beyond the TESS account (most UK Prolific-run survey experiments live here,
e.g. `osf.io/muctb`); journal replication Dataverses (Political Analysis, BJPolS,
JOP, AJPS — thousands of UK survey-experiment packages, many CC0); Zenodo.

**Specialist but conjoint-rich:** UK health-economics **DCEs** (NHS/service
preferences — our high-value format, large literature); Behavioural Insights Team
/ What Works Centres / Nesta RCTs (some open).

**Cross-national with UK slices:** ESS, ISSP, CSES, Eurobarometer, WVS/EVS (UK
samples, occasional experimental modules); GESIS Data Archive.

*Access tiers: **open/CC0** = free + redistribute · **safeguarded** = UKDS
registration + EUL, no redistribute · **controlled** (admin data, ADR UK) = not
usable here.*

**Harvest finding (2026-09-25):** the open Harvard Dataverse pool is **~tapped**
for UK experiments (~13 total: §5a's 9 + 4 new in `uk_dataverse_candidates.csv`).
Topic-only search drowns in the US-dominated corpus (no country filter); UK
experiments cluster in the UK poli-sci community, already swept by author. Open
*volume* would need OSF-beyond-TESS (not API-searchable) or journal supplements.
The real volume is the **safeguarded UKDS** sources above — start with the
Innovation Panel.

---

## 6. Persona — the merged UK schema & crosswalk

**Common spine** (richness varies by source):
`gender · education · income` everywhere; `age · social grade · party · EU vote`
across the politics sets. Field order per row:

> age · gender · ethnicity · region · education · social grade · income ·
> work status · marital · party · EU vote

**Crosswalk status** (four YouGov studies checked, 2026-09-21):
- **Match as-is:** gender (1=M,2=F), education, EU-ref vote (1=Remain,2=Leave,
  3=Didn't vote), region (3 of 4).
- **Need a fix:** social grade (grouped differently per study — map to common
  bands; can't split a pre-merged AB/DE), region in "Divided by the Vote" (remap
  to standard 12).
- **Open:** BES coding; thinner/non-UK studies not yet checked.

**Vs SocSci210:** matches or beats it on 13 of 16 shared fields; adds ~8 fields
SocSci210 lacks; main genuine gap is household size (BES/DEL have it though).

---

## 7. Prompt format & modes

One uniform template so stimulus and no-stimulus sources train the same model:

```
You are a UK survey respondent with this profile:
- Age: 61 · Gender: Male · Region: North East · Education: GCSE · Party ID: Labour
[optional history, longitudinal only:]
  2015: like Labour = 8 · 2017 = 6 · 2019 = 3
Scenario: none                       ← standing-attitude mode (BES observational)
Predict their answer as of: 2024-07  ← horizon, longitudinal only (real DATE)
Question: "How much do you like the Labour Party?" (0–10)
Answer with the number only.
```

- `Scenario: none` → give standing attitude; `Scenario: "<text>"` → react. The
  sentinel is the mode switch and does real work.
- **Watch the mix ratio** — if it's almost all `Scenario: none` (BES-heavy), the
  reaction mode barely trains. Blend in enough filled-scenario examples.

---

## 8. Dataset-building pipeline (the data agents)

**At a glance — two paths, one dataset.** The dataset is `(persona, condition,
outcome, response)` rows gathered study by study. Each study takes one route:

- **PULL** — already in SocSci210 → grab ready-made rows, no work. *(75 studies, ~1M rows, free.)*
- **BUILD** — not in SocSci210 (the 120 TESS it skipped + **all** UK-native: Brexit/immigration conjoints, BES, Innovation Panel) → run the pipeline below.

> One-liner: *pull what SocSci210 already built; run the pipeline only on the
> UK-native data and the studies it missed.* Then merge both → train.

---

The **BUILD** path: how a raw source deposit becomes canonical `(persona,
condition, outcome, response)` rows. Mirrors SocSci210's reconstruction agent
(paper App. A) plus a **judgment layer** and **human-in-the-loop**. Runs **per
study**.

```
  raw deposit (data files + docs)
        │
        ▼
  [1] parse & profile ................ agent
        │
        ▼
  [2] identify condition / outcome ... agent + Jev  (is-experiment? which var is which?)
        │
        ▼
  [3] map persona → schema (§6) ...... agent + Jev  (category crosswalk)
        │
        ▼
  [4] assemble stimulus (arm→text) ... agent  (+ human for video/image)
        │
        ▼
  [5] build rows (P, c, o, r) ........ agent  (strip missing codes; keep conjoint attrs)
        │
        ▼
  [6] validate / QC .................. Jev  (well-formed? stimulus ↔ condition consistent?)
        │  ├── fail ──▶ flag / human review ──┐
        │  └── pass                            │
        ▼                                      │
  [7] merge & version ──▶ DATASET  ◀───────────┘
```

Legend: **agent** = reconstruction agent (writes+runs parsing code) · **Jev** =
TypeSafe judgment call · **human** = review of low-confidence / hard cases.

### Stages

| # | stage | what happens | who | gate |
|---|---|---|---|---|
| 0 | **Acquire** | download deposit (Dataverse CC0 / OSF / UKDS safeguarded): data files (`.sav/.dta/.csv/.tab`) + docs (questionnaire, codebook, User Guide) | script | file present |
| 1 | **Parse & profile** | read data (`pyreadstat`), extract variables + labels + value codes; profile candidate persona/condition/outcome vars | agent | parses clean |
| 2 | **Identify experiment structure** | find the **allocation/condition** var(s), the **outcome** question(s) + scale, the **design type** (conjoint/vignette/framing/split-ballot) | agent + **judgment** | is it an experiment? which var is which? |
| 3 | **Map to schema (crosswalk)** | source persona vars → canonical spine (§6); harmonise category codes (income bands, education) | agent + **judgment** | fields mapped |
| 4 | **Assemble stimulus (arm→text)** | render each arm's wording — conjoints from attribute columns · text-argument studies from a companion file · vignettes from questionnaire · video → written description ("the work is part 2") | agent (+ human for video) | every condition has stimulus text |
| 5 | **Build rows** | per respondent × outcome → emit `(persona, stimulus, condition, outcome, response int)`; strip missing codes; keep conjoint attributes as structured metadata; expand conjoint tasks | agent | one-integer response in range |
| 6 | **Validate / QC** | row well-formed? stimulus ↔ condition consistent? persona harmonised? | **judgment** | reject/flag bad rows |
| 7 | **Quote layer** (optional) | if open-ended responses exist → extract as realism anchor (§9); else mark for synthetic-quote track | agent | — |
| 8 | **Merge & version** | unify into one schema; record source, licence, provenance | script | — |

### The three actors

- **Reconstruction agent** (per study, SocSci210-style): reads the full study
  context (paper, data files, codebook, stimuli) → writes and **executes parsing
  code** → self-corrects on errors (generate-and-test loop) → emits rows.
  **Success gates** (paper App. A): (1) find a stimulus description for *each*
  condition; (2) reconstruct binary/ordinal outcomes; (3) outcomes map to
  condition-specific stimuli — else **skip the study**. "Success" = code compiles,
  runs without errors, and produces non-empty row-by-row output. (SocSci210
  reconstructed 210 of 321 this way; ~111 failed these gates.)
- **Judgment layer** (atomic typed decisions — a good fit for **TypeSafe**, see
  below): study curation (KEEP/JUDGEMENT/DROP, topic, is-experiment?, is-UK?),
  category-mapping choices, row-level QC (well-formed?, stimulus↔condition
  consistent?), and later the **quote consistency** + **realism discriminator**
  judges (§9). Typed answer + probability + confidence beats ad-hoc LLM
  prompting for these.
- **Human-in-the-loop**: spot-check low-confidence judgments, resolve borderline
  crosswalk mappings, handle hard formats (video/image stimuli, messy files).

### TypeSafe (docs.typesafe.ai) — where it fits

A structured-decision API built on **Jev** — TypeSafe's flagship "System One"
model (fast, atomic, structured judgments code can consume directly, rather than
free text). You send state + typed questions; Jev returns typed answers via three
primitives — **Choice** (pick option), **Score** (rate vs rubric), **Noul** (truth
0–1) — each with a probability distribution + confidence, evaluated in parallel.
It maps cleanly onto our **judgment layer**:

- ✅ **Fits:** curation (KEEP/DROP = Choice, topic = Choice, is-experiment / is-UK
  = Noul), category harmonisation (Choice), row QC (Noul/Score), quote-consistency
  judge (Score/Noul), real-vs-synthetic discriminator (Noul). Calibrated confidence
  is a real upgrade over free-text judging.
- ❌ **Does NOT fit:** it is **not** an ETL/parsing tool (reconstruction stays
  in-house); and it **cannot be the behavioural predictor** — that must be a model
  *fine-tuned on the survey data*, and TypeSafe is proprietary + non-fine-tunable.
- ⚠️ **The trap:** its Choice returns a probability distribution = *the model's
  confidence*, **not the human population's response spread**. Never use it as a
  stand-in for real response distributions — that would silently defeat the
  distribution-matching goal. Keep it out of the prediction path.
- ⚠️ **Caveats:** hosted/proprietary → cost, external dependency, and a
  **data-privacy** question (don't send safeguarded UKDS data without checking the
  EUL; consider open-release implications). Niche/new — pilot on one task first.

---

## 9. Training setup — model choice

**Do we have enough data?** Yes — volume is not the bottleneck. A LoRA/QLoRA
fine-tune of an 8B model shows a real gain with ~10k–50k well-structured rows +
a held-out test set; the paper finds learning **saturates at ~10% of a study's
data**. We have far more: 75 SocSci210 studies = ~1.06M rows ready now, and *any
one* reconstructed UK conjoint (Pricing Immigration ~18–36k, Anti-immigrant ~45k)
already clears the bar. The real constraints are reconstruction effort (need 1–2
UK datasets), a held-out eval, and modest compute — **not** data.

**What the paper used** (Kolluri et al., §5.1 + App. C): base models
**LLaMA-3-8B-Instruct** and **Qwen2.5-14B-Instruct** → Socrates-Llama-8B /
Socrates-Qwen-14B. **Full fine-tune** (not LoRA), 8× A100 80 GB, batch 256, 1
epoch, LR 1e-5 (SFT) / 1e-6 (DPO). Proprietary only as baselines/tools: GPT-4o
(eval baseline), GPT-4o-mini (reasoning traces), o4-mini-high (reconstruction
agent).

**Our model shortlist (Sept 2026) — dense, permissive licence, single-GPU LoRA.**
Task = SFT for a single-token integer, so: *dense* (not MoE), Instruct
(non-thinking) base, mature LoRA/QLoRA tooling, and lineage to the paper for
comparability.

| # | model | size / arch | licence | role |
|---|---|---|---|---|
| 1 | **Qwen3-8B-Instruct** | 8B dense | Apache 2.0 | **PoC — start here.** Cheapest, best tooling, paper lineage; single 24 GB GPU. |
| 2 | **Qwen3.8-27B** | 27B dense | Apache 2.0 | **Headline scale-up.** Top small-dense scorer; same family = one recipe; 48–80 GB QLoRA. |
| 3 | **Gemma 4 12B** | 12B dense | Gemma (verify) | **Independent-lineage cross-check** (rules out a Qwen artefact). Swap **Phi-4 14B / MIT** for the cleanest licence, but it's synthetic-heavy → test pliability. |

**Deviation from the paper:** they full-FT'd on 8×A100; for a PoC we use **QLoRA
on a single GPU** (Instruct base, 1 epoch) — far cheaper, fine for proof. 8B
proves the approach; 27B is the best-available small-dense *headline*, not a
requirement.

**Avoid:** the hyped giant-MoE frontier models (Kimi K3, DeepSeek V4, GLM-5.3) —
wrong scale/shape for a narrow SFT, coding-leaderboard hype ≠ our task; **Exaone**
(non-commercial licence); MoE + "thinking" variants for now.

**Minimal PoC:** reconstruct one UK conjoint → QLoRA-tune Qwen3-8B → hold out
**unseen conditions** (attribute combos) + split by respondent → report base vs
fine-tuned on accuracy ↑ and Wasserstein ↓. That's a complete proof the approach
transfers to UK data. Caveats: conjoint rows are within-person correlated (don't
count 1:1); one conjoint proves the *format*, not topic breadth.

### Objective & checkpoint (for distribution matching)

The primary goal is **distribution alignment** (match the human response spread),
not just individual accuracy. What the paper showed:

- **SFT from an Instruct checkpoint already recovers human dispersion.** human
  σ=0.192, Socrates-Llama-8B (SFT from Instruct) σ=0.195, vs **GPT-4o σ=0.154**
  (collapsed — but that's because it was *prompted*, not fine-tuned). So the
  mode-collapse is a *prompting* artefact; **plain SFT fixes it**.
- **Prefer plain SFT over DPO, and no reasoning traces, if distribution is the
  goal.** DPO sharpens individual accuracy but *worsens* distribution;
  reasoning-augmented SFT underperformed plain SFT on both metrics.
- **Checkpoint:** mirror the paper — **Instruct + SFT** is the proven baseline.
  A raw **Base (pretrained, non-RLHF) checkpoint** is an *optional A/B* that may
  add a little dispersion, not a requirement. Newer/bigger or "thinking" models
  tend to under-disperse (assistant-consensus) — measure σ before trusting them.

### Quotes / open-ended output (two-stage, decoupled)

We may want a **verbatim-style quote** (justification in the persona's voice), not
just the number. Key fact: we have real **numbers** as ground truth but rarely
real **quotes** — so any quote is *synthetic* (this is exactly the paper's
`reasoning` field, which had no ground truth and hurt the number when trained
jointly). Therefore **keep them separate:**

```
  persona + stimulus
        │
        ├────────────────────────▶ [tuned SFT model] ──▶ RESPONSE NUMBER   (ground-truthed, 1 token)
        │                                                       │
        │                                                       ▼
        └──▶ persona + stimulus + number ──▶ [quote generator] ──▶ quote   (separate model; AFTER the number)
                                                                │
                                                                ▼
                                                    [Jev consistency judge] ──▶ keep  /  regenerate
                                                     (consistency, NOT truth)
```

- **Never joint-train number+quote** — the synthetic quote target degrades the
  ground-truthed number (paper's SFT-w/-Reasoning result). Two models, two losses,
  fully decoupled; the quote track never backprops into the number model.
- **Generate the quote *after* the number** (presentation layer). Quote-then-number
  is the reasoning path that lets rationalisation steer the answer — underperformed.
- **How the judge feeds training** (escalating): **L0 inference-time only** —
  best-of-N filter/rerank, no training (often enough); **L1 rejection-sampling
  SFT** — judge *curates* accepted quotes → SFT the generator on them (stable,
  the sweet spot); **L2 DPO / RLAIF** — judge → preference/reward → RL (powerful,
  unstable, risks reward-hacking).
- **The judge measures consistency, not truth** — optimising against it makes
  quotes self-consistent, *not* more real. Consistency is a floor.
- **Labelling (non-negotiable):** synthetic quotes are labelled synthetic — never
  presented as a real respondent's words.

**Making quotes *realistic* (not just consistent) — the recipe.** Realism can't
come from the judge; it has to be **anchored to real human open-ended text**:

1. **Harvest a realism anchor** = real open-ended responses (BES open-text, DEL,
   "why?" follow-ups), each tagged with its `(persona, stimulus, number)`. A few
   thousand is enough to learn the *voice*. **This is the gate — do it first.**
2. **SFT the quote generator on those real quotes** (conditioned on
   persona+stimulus+number). This step *is* the realism — it teaches authentic
   register (short, hedged, messy) instead of assistant-speak.
3. **Fill gaps** (rows with no real quote) with that now-realistic generator,
   optionally **few-shot on retrieved real exemplars** from similar personas.
4. **Validate realism** with things a consistency judge can't: style-distribution
   match (length, readability, hedging, sentiment spread vs real); a **real-vs-
   synthetic discriminator** (if it separates them easily, not realistic yet); a
   small human spot-check.
5. **Design against assistant-polish** — constrain length, don't over-clean,
   prefer a Base/lightly-tuned checkpoint. Real open-ends are terse and low-effort.

**Bottom line:** *with* real open-ends → genuinely realistic quotes are possible;
*without* them → only consistent-and-plausible, never verified-realistic (label as
synthetic). Highest-value move = **step 1: find which sources have open-text items.**

---

## 10. Where we actually are (1 October 2026)

**14 studies, 80,010 rows, 23,464 respondents.** All QC PASS with no warnings.
Persona harmonised across four fields. 109 tests. 7 of 14 pass an independent
SocSci210 numeric crosscheck exactly; the other 7 have no usable key because
SocSci210 built a different scope.

### The plan

Not 100% of the catalog. **20% (~40 studies) chosen for UK value** — 26 more
than exist today. `data/catalog/uk_priority.json` ranks the 59 buildable
candidates on UK relevance, whether the question is still live, and domain, and
`scripts/uk_priority.py --balance 26` produces a shortlist spread across 11
domains rather than piled into one topic.

Two decisions open: how many survey-methodology studies to include (11 of 59
candidates, one tops the ranking, but they are not UK questions), and whether to
build the 14 `full`-transfer studies before the 11 `mechanism-only` ones that
need their scenarios re-anchored.

### What is proven

Every design shape TESS throws: **2 to 72 arms**, 1 to 14 outcome items,
assignment via one variable / three variables jointly / combinatorial `[SHOW IF]`
templates / a lookup spreadsheet, split-ballot where the question IS the
treatment, per-arm recodes, nominal outcomes, banded quantities, and several
sub-experiments in one deposit.

Quality against SocSci210 is measured rather than asserted — see `docs/LEDGER.md`.
Their persona coverage is 6/16 fields on KnowledgePanel studies with the data
sitting in the source file; ours is 100% on ten core fields.

### What is not proven

**Scale.** 14 of 202 is 7%, and SocSci210 is 36x bigger. Throughput works at 5
parallel agents and is untested at 50. 125 studies are not fetched.

Two design shapes we met and could not fully build, blocking ~60,000 rows in
studies already verified: within-subject per-item assignment (`b87sm`, 1 of 8
vignettes) and per-(arm, outcome) variables (`evnyh`, 1 of 10 items).

### How it is built

Maker/checker agent pairs, n=7 through the full loop with **zero defects in built
data** — what the checkers found instead were bugs in our own pipeline. Jev
decides which column is which persona attribute and what each category label
means; arithmetic proves the band merges. Both are measured, both rank and flag
rather than deciding.

## 11. Files & tooling

**Project home:** `~/Workspace/products/micromotives-datasets` — a proper Python
project (uv, `src/` layout, ruff + mypy + pytest), mirroring sibling `melange-sim`.
GitHub: `richardhutton/micromotives-datasets` (private). Note the split: the repo
and folder use a **hyphen**, the importable package uses an **underscore**
(`micromotives_datasets`). "Micromotives" is the umbrella name for the whole
simulation stack.

**Layout:**
- `docs/SocSci-UK_MASTER.md` — this doc (source of truth).
- `docs/innovation_panel_checklist.md` — UKDS SN 6849 pull & reconstruct recipe.
- `data/catalog/tess_uk_foundation_sources.csv` — the 202 foundation studies (the
  work-list): `year, title, category, is_conjoint, tess_id, osf_code, study_id,
  in_socsci210, socsci210_rows, buildable, osf_type, data_kind, data_file,
  data_bytes, has_questionnaire, tess_url, osf_url, data_download, is_new`.
  (`is_conjoint` flags conjoint/factorial designs — see §5d.)
- `data/catalog/uk_dataverse_candidates.csv` — UK Dataverse finds + rejects.
- `src/micromotives_datasets/` — the package: `schema.py` (the `(P,c,o,r)` `Row`
  + `Persona`), `persona.py`, `config.py`, `recipe.py`, `sources/`, `pipeline/`.
- `scripts/` — `explore.py` (SocSci210 inspector), `bes_inspect.py` (BES);
  usage documented in `scripts/README.md`.
- `recipes/` — one hand-authored YAML per BUILD study (§8 stages 2–4).
- `data/raw/` and `data/processed/` — **gitignored**; source downloads and built
  rows never enter git (UKDS safeguarded = no redistribution).

**Archived (`docs/archive/`):** the source notes this doc merged (SocSci210_studies.md,
SocSci210_uk_suitability.md, SocSci-UK_v0.1.md, SocSci-UK_data-overview.md,
SocSci-UK_persona-crosswalk.md, SocSci-UK_DEL.md, BES.md, README.md) and the
intermediate CSV/JSON (SocSci210_uk_filter, tess_uk_keep_join, tess_uk_foundation,
tess_uk_foundation_topics, tess_all_studies_classified). Nothing deleted — the
full 517-study classification with JUDGEMENT/DROP tiers is in
`archive/tess_all_studies_classified.csv` if ever needed.
