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

### 5a. Harvard Dataverse UK experiments — CC0 except where the table says otherwise

The core UK experiments, in (persona · stimulus · condition · response) shape.
Persona = the YouGov profile block. Stimulus form varies per study.

**Resolved against the live Dataverse API on 2 October 2026.** Every row below
had sat here unverified since early planning, and the check found the heading
itself was wrong: **`POMIFD` is NOT CC0.** The audit is ledger 106-113; the short
version is that titles were reliable, licences were not, and the design column
was wrong on BOTH entries anyone checked against actual data.

**The heading above was corrected on 5 October 2026, three days after the audit
that found it wrong** — the 2 October check recorded the error in this paragraph
and left the heading itself saying "(all CC0)". Worth stating as its own lesson:
a licence claim in a HEADING is the most dangerous place for one to be wrong,
because a heading is what someone reads when skimming for what may be published,
and the correction sat four lines below it unread. The `licence` column in the
table is the authority; the heading is now written so it cannot contradict it.

`Rows` is now labelled for what it is. **Every number in the old table was a
RESPONDENT count**, not a row count — `6MRVOM`'s 3,636 and `POMIFD`'s 3,317 are
both respondents, and `EFXNLX`'s 3,293 respondents are 16,465 pair-level or
32,930 profile-level observations. A claimed row count read as a row count
overstates nothing and understates a conjoint by an order of magnitude.

| DOI (`10.7910/DVN/…`) | Dataset | Licence | Design, as VERIFIED | Respondents | Instrument ships? |
|---|---|---|---|---|---|
| EFXNLX | Brexit negotiations conjoint (Hobolt, Tilley, Leeper) | CC0 1.0 | 8-attribute conjoint, 6 pairs, forced choice + per-profile acceptability | 3,293 → 16,465 pair / 32,930 profile | **yes**, and data levels match it word for word |
| 6MRVOM | Pricing Immigration (Hix, Kaufmann, Leeper) | CC0 1.0 | **NOT a conjoint** — THREE independent randomisations. BUILT: `ExpSplitQ5` (information anchor, 0-100 share outcome, 2,397 rows) and `ExpSplitQ67` (post-Brexit scenario, party choice + satisfaction, 6,526 rows — 2,890 party-choice + 3,636 satisfaction, after a 2026-10-05 ruling dropped code 12 "Don't know" from party choice; originally built at 7,272 with code 12 kept). UNBUILT: the paper's own main 2×2×2×2 cost-framing experiment, a genuine 0-165,000 net-migration slider, pending an owner decision | 3,636 | **yes**, carries the template the condition fills |
| 35M5CV | Divided by the Vote (Hobolt, Leeper, Tilley) | CC0 1.0 | **SIX bundled sub-studies**, not one | unverified | 2 of 6 only (lodger, bbc) |
| PMV0TG | Vaccine allocation, 13 countries (Duch et al.) | CC0 1.0 | conjoint | unverified | **yes**, a UK-specific Qualtrics instrument |
| ZZYSIZ | Anti-immigrant, 22 countries (Wimmer et al.) | CC0 1.0 | conjoint, forced choice | unverified; **UK presence NOT confirmed** | an "example" only, not full wording |
| PZB01G | For/Against Brexit (Goodwin, Hix, Pickup) | CC0 1.0 | **2×2×2 factorial** + control, six vignette frames | **5,333** in the vignette wave (Wave 1: 6,074) | not in the deposit — but all six frames are word-for-word in the paper's **open-access CC-BY** appendix |
| RJTVG8 | i-voting (Turnbull-Dugarte, Devine) | CC0 1.0 | 10-attribute conjoint, 5 tasks | **1,200 UK → 6,000 pairs**, UK confirmed | not in the deposit — Table A.3 of the open author manuscript prints all ten attributes word-for-word |
| SACJHE | Cyber Terrorism (Shandler et al.) | CC0 1.0 | TV news **video**, retaliation scale | **597 UK** of 1,848 (2,028 included an undeposited 180-person pilot) | script is word-for-word in the open appendix — **DROPPED anyway on the video-stimulus ruling, below** |
| POMIFD | Variable Persuasiveness of Political Rhetoric (Blumenau, Lauderdale) | **NOT CC0 — `license` is null** | pairwise comparison, 336 arguments | 3,317 → 13,268 | yes, prompts ship as data. **Usable but never publishable** — see `use_basis` in the provenance catalogue |
| (OSF) | Many Labs 1/2, PSA | various | various | — | — |

**`POMIFD` is the best material of all nine and is blocked on licence alone.** 336
argument strings ship word-for-word as data, every pair a respondent saw is recoverable
by a join, demographics are the richest of any UK deposit, and the numbers behind
the main figure ship as R data. Its `termsOfUse` says *"You may wish to
communicate with the Contact(s) specified before use"* — an invitation to ask, not
a prohibition. **One email to UCL could unblock it.** If the licence ever clears,
it goes straight to the top of the queue.

**`PZB01G`, `RJTVG8` and `SACJHE` have no status, and that is the gap, not their
quality (2026-10-05).** All three are CC0. All three are marked "no instrument"
in the table above, and all three are **absent from
`data/catalog/uk_dataverse_provenance.json` entirely** — so they were never
dropped, never queued, and no test covers them. "No instrument in the deposit"
decides nothing on its own: the appendix ruling makes an author-written table or
appendix an acceptable primary source, which is how `LOGVPZ` is built (its
paper's Table 4) and how `X08IVC` will be. The test that actually decides is
**whether the authors' own wording is reachable in an accessible paper**, and
`TLT65Z` was dropped on precisely that test when its AJPS paper proved paywalled.
**The test was run on 5 October 2026, and §5a was wrong about all three.** Two
are buildable and the third's objections were factually mistaken:

| Deposit | Verdict | Why §5a's note did not decide it |
|---|---|---|
| `PZB01G` | **BUILDABLE** — 5,333 respondents, 2×2×2 + control | Paper is **open access CC-BY** in BJPolS; supplementary appendix is headed *"I. Text of the vignettes:"* and prints all six frame paragraphs word-for-word |
| `RJTVG8` | **BUILDABLE** — 1,200 UK respondents, 6,000 pairs | **UK sample confirmed** from the paper's own text and the data; author-accepted manuscript open at Southampton ePrints, Table A.3 prints all ten attributes with full level text |
| `SACJHE` | **DROPPED** — rich's scope ruling, 5 Oct 2026 | §5a's two objections were both wrong, but it was dropped for different reasons; see below |

#### The video-stimulus ruling (`SACJHE`, 5 October 2026)

**A word-for-word author-written SCRIPT of a produced audiovisual stimulus does not
count as condition text.** This is a standing ruling rather than a one-off: the
next study with a video, an audio clip or an image is decided the same way unless
someone revisits it deliberately.

The appendix-ruling precedents — `LOGVPZ`, `X08IVC`, `PZB01G` — are all studies
where respondents **read** text, so an appendix reprinting that text reprints the
actual stimulus. `SACJHE`'s respondents watched a produced, acted, scored news
segment; the script is the words spoken in it, without imagery, tone, pacing or
the on-screen chyron.

What was NOT wrong with it, so nobody re-litigates the easy parts: the deposit is
CC0, the UK sample is separable and clean at **n=597** (120/119/118/120/120,
matching the paper's published Table 3 cell for cell), and a word-for-word script
genuinely does exist in the open-access Online Appendix B. The ruling was close,
and these are the three reasons, recorded because the question will come back:

1. **The control arm saw no video at all** — 120 of 597. The contrast the design
   rests on is *watched a dramatic bulletin about a terror attack* versus
   *nothing*, and no text represents that. Composing a no-stimulus arm is
   precedented (`LOGVPZ`), but there the treatment arm was also text the
   respondent READ.
2. **The outcome is an absolute 1-6 rating, not a contrast.** The
   cyber/conventional and fatal/non-fatal manipulations ARE purely linguistic and
   survive in text perfectly well — but a produced segment moves an absolute
   rating differently from a paragraph, so a model would be asked to predict a
   number produced by an experience we cannot give it.
3. **The UK substitute for the US city name "Cambridge" is unrecoverable** —
   checked against the appendix text, all seven embedded images at native
   resolution, the paper's own Table 1 screenshots, the codebook, every `.sav`
   label and the SPSS output file. It appears only in the FATAL script, so either
   two of four treatment arms assert that UK respondents saw a US city, or the
   sentence carrying the casualty detail is left incomplete, or both Fatal arms go
   and 359 respondents remain from a 2×2 with half its cells missing — which is
   no longer the experiment. (`Amtrak` → `National Rail` IS confirmed, from two
   independent sources.)

**If it is ever revisited**, the middle option is to build only the four TREATMENT
arms and drop the control, measuring within-treatment contrasts rather than
treatment-versus-nothing. That answers reason 1 completely and reasons 2 and 3
not at all.

Two findings worth keeping whatever the ruling. `ManiCheck1`/`ManiCheck2` hold an
**undeclared `0`** meaning "Control, never shown a video" rather than a failed
attention check — the authors' own filter carries a third clause specifically to
pass Control through, so coding it naively would flag every control respondent as
a failure. And the authors' headline measure is `MEAN(Retaliation_1,_3,_5,_6)`,
which must never ship as a `response`, because no respondent produced it.

Two corrections to the record while we are here. §5a said `SACJHE`'s 2,028 was a
three-country total; the deposited file actually holds the **1,848**-respondent
main experiment, and 2,028 adds a 180-person pilot whose raw data was never
deposited — so the figure in the table was wrong about *which* study it counted,
not merely about its scope. And §5a said the deposit ships "no transcript", which
is true of the deposit and irrelevant to the decision, since the transcript is in
the paper.

All three now hold rows in `uk_dataverse_provenance.json` with a `status` and a
`status_reason`. `tests/test_uk_provenance.py` requires both, and — the point of
the new completeness test — requires a row to exist at all for every deposit code
§5a names, because the other tests iterate the catalogue and a catalogue cannot
report what it omits.

**`35M5CV` is six studies, and we have built two (2026-10-05).** The table row
above says "SIX bundled sub-studies" and the deposit was then marked built once
`lodger` and `bbc` were done. A screen of the other four:

| Sub-study | File | Rows | Verdict |
|---|---|---|---|
| `lodger` | `lodger-data-raw.sav` | 1,669 resp → 8,345 | **built** |
| `bbc` | `bbc-data-raw.sav` | 1,635 resp → 8,175 | **built** |
| `sky` | `sky-data.sav` | **3,481** | **BUILDABLE — split ballot, see below** |
| `tracker` | `tracker-data.sav` | 15,341 | no assignment column found; likely the tracker series, not an experiment |
| `yougov-brexit-id` | `yougov-data-brexit-id.sav` | 1,678 | no assignment column; looks like `sky`'s two halves fielded as separate surveys, which is not random assignment |
| `yougov-party-id` | `yougov-data-party-id.sav` | 1,648 | as above |

`sky` is a genuine split ballot: `Split` divides 1,779 / 1,702 and partitions
every row exactly once, and **36 columns are answered by one split and zero by
the other**. Both halves ask the identical social-distance items — *"Happy if
child married a …"*, *"Happy to talk politics with …"* — about **Brexit identity**
(Remainer / Leaver) for Split 1 and **party identity** (Labour / Conservative)
for Split 2. That is the paper's own central comparison, randomised, and the
schema already exists: `witness_var` + `not_asked_code`, built for `QQM5MC`,
which is the same shape. The one gap is that **no questionnaire ships for `sky`**
(only `bbc-script.docx` and `lodger-script.docx`), so the condition text needs
the paper under the appendix ruling — the access test has not been run yet.

**Great Britain, not the UK.** All three YouGov-fielded deposits checked against
data (`QQM5MC`, `6MRVOM`, `EFXNLX`) have respondents only in regions 1-11 — zero
in Northern Ireland, which is a declared level with no rows in every one of them.
Ruled fine (rich, 2 Oct); recorded as a property of the YouGov studies, not a
defect. It is also ledger 101's shape three times over, so never trust a region
drop-list on these deposits without checking occurrences.

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

**Downloaded and screened, 5 Oct 2026.** SN **6849** (the EUL version; 7083 is the
special licence, which we do not hold and do not need) is in `data/raw/ukds_6849/`
— 17 waves, 279 files, 1 GB. The User Guide catalogues **93 experiments**, and all
93 are now screened in `data/catalog/innovation_panel_experiments.json`, rendered
to **`docs/UKDS_UNBUILT.md`**:

| Verdict | | |
|---|---|---|
| `build` | 44 experiments, 63 experiment-waves | 4 are vignette studies |
| `marginal` | 9 | need a ruling; `9.3` first |
| `drop` | 40 | 28 procedural, 5 physical/app, 7 visual or mode |

Three corrections to what this section claimed before the download:

- **The allocation variables are in `{w}_hhsamp_ip`, not `{w}_indresp_ip`.**
  Randomisation is mostly per household, so every build joins two files on
  `{w}_hidp` — unlike all 13 Harvard studies, where the condition sits in the
  same file as the answer. ~293 person-level allocations also exist.
- **"Retains the allocation variables" is true but not sufficient.** The data
  gives a group *number*; the condition *wording* exists only in the wave
  questionnaire PDFs. Whether each of the 44 has usable wording there is the
  largest unknown left, and resolving it can only move the count down.
- **Only ~30 of the 93 are substantive.** 43 are about survey methodology,
  because that is the panel's purpose. TESS remains the broader source on topic;
  the Innovation Panel's edge is the time axis (8,078 people, mean 5.09 waves
  each, 216 in all 17) and persona depth.

**FIRST BUILD, 7 Oct 2026: experiment 9.10, waves 5 and 6 — 9,631 rows.**
`recipes/ukds_6849_vig_housework_w{5,6}.yaml`, both QC PASS. The made-up-scenario
study on satisfaction with the sharing of housework: five randomised dimensions,
4 × 3 × 4 × 5 × 2 = 480 cells, all 480 occurring, three scenarios per person drawn
without replacement. It answers the largest unknown above in the affirmative for
this experiment — the questionnaire specification (`Scavignettes_ip5`) carries
every clause word-for-word, and the archived value labels turned out to be not
merely truncated but WRONG in three places (ledger 119), so building from the PDF
was not a preference but the only correct route.

Two things the build settled that the desk screen could not:

- **The screen's stated reason was wrong.** It said "respondents rate a described
  couple, not themselves"; the fielded wording is "Imagine that **you** are
  married or cohabiting", so the outcome is imagined own satisfaction. Corrected
  in the catalogue (ledger 120).
- **Household allocation is an asset, not an obstacle.** Both partners in a couple
  saw the IDENTICAL three scenarios, so the corpus now holds pairs of rows with
  the same condition and different answers — the cleanest test there is of whether
  persona is doing any work, and nothing else in this corpus offers it (ledger 123).

**AND IT MEASURES ITS OWN CEILING — 27.7% (ledger 124).** The User Guide says "the
exact allocation at Wave 5 was replicated at Wave 6" and it is true: 27,696 of
27,705 allocation cells are identical for the 1,849 people in both waves, so a
returning respondent rated the **same three arrangements a year apart**. Across
those 3,621 pairs the answer is identical only **27.7%** of the time (within one
point 57.5%, mean absolute change 1.59 on a 1–7 scale, r = 0.329), against chance
of 14.8% and a modal-class baseline of 19.4%.

**So the usable band on exact match is about 19% to 28%, and the top of it is set
by people disagreeing with themselves.** Any accuracy figure reported on this
outcome is uninterpretable without that ceiling printed next to it, and anything
above ~28% is a bug, not a result. This is the first ceiling in the project
measured from data rather than borrowed from Park's 0.86, and it is the reason
this study was worth building first.

Two practical consequences:

- **The two waves are not independent rows.** Pooled they are 9,631 rows but only
  6,010 distinct (person, cell) pairs. They are built as separate experiments, and
  anything concatenating them must keep one wave or treat the pair as repeated
  measures.
- **No published answer key exists.** The User Guide cites no paper for 9.10, so
  `verified_against` in the manifest records the design verification it actually
  has — the replication claim, the household join against wave 5's duplicate copy,
  cell coverage, marginal balance and two independent row counts — and claims no
  agreement with any published table.

Two reusable additions came out of it, so the remaining three scenario studies
(`9.26`, `9.30`, `9.39`) need no new machinery:

- **`Condition.template`** — a factorial declared as a template plus its
  dimensions, expanded on load. 480 arms from ~40 reviewable lines of YAML,
  instead of the `9xw67` outcome of 455,919 generated lines nobody reads.
- **`Recipe.participant_id_var`** — the respondent's own identifier in place of
  the row index, so one person keeps one id across waves. Without it a panel wave
  is a separate population and the time axis, the whole reason this source is
  worth the licence, is unusable.

**SECOND BUILD, 9 Oct 2026: experiment 9.18, waves 9 and 17 — 12,567 rows.**
`recipes/ukds_6849_vig_ageing_w{9,17}.yaml`, both QC PASS with no warnings. Three
descriptions of an imaginary 75-year-old per respondent, each rated 0-10 on how
successfully they are ageing. Six life dimensions plus a name (4 × 2⁶ = 256 cells,
all occurring), the name setting the pronouns and appearing in the question. Built
from the questionnaires (`Scavignettes_ip9`, `scasuccessageing_ip17`); the archived
labels contradict themselves again ("rarely sees family and friends regularly").
An independent checker re-rendered all 12,567 rows from the raw files with zero
disagreements. No publication exists to check against.

- **Wave 17's randomisation partly failed (ledger 125).** 354 respondents share one
  identical allocation, and 933 share theirs with someone. Wave 9 is clean. The rows
  are real, but the wave is not a balanced factorial.
- **Schema:** `Level.parts` (fragments that agree with a level, such as pronouns)
  and `ConditionTemplate.outcome_questions` (per-task questions that vary with the cell,
  attached as item overrides). Inert: all 43 earlier experiments rebuild
  row-identical.

**THIRD BUILD, 9 Oct 2026: experiment 9.39, wave 16 — 17,656 rows.**
`recipes/ukds_6849_vig_flexstigma_w16.yaml`, QC PASS with no warnings. HR-manager
vignettes: three job candidates rated on recommendation, commitment, productivity and
team-playing; gender, parenthood, home working, company prevalence and policy
randomised (576 arms). Clean allocation. Chung & Wang (2024) published initial
findings, not yet compared (the PDF could not be fetched from this machine). With it
the Innovation Panel layer is 5 experiments and 39,854 rows; the corpus is 46
experiments and 466,529 rows.

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

**Harvest finding (2026-09-25), SUPERSEDED — see the correction below.** The
claim was: the open Harvard Dataverse pool is **~tapped** for UK experiments
(~13 total: §5a's 9 + 4 new in `uk_dataverse_candidates.csv`). Topic-only search
drowns in the US-dominated corpus (no country filter); UK experiments cluster in
the UK poli-sci community, already swept by author. Open *volume* would need
OSF-beyond-TESS (not API-searchable) or journal supplements. The real volume is
the **safeguarded UKDS** sources above — start with the Innovation Panel.

**Correction (2026-10-05).** The "~tapped" claim above contradicted §5a's own
closing line, written nine days later: *"Search was **not exhaustive** — more
remain on both Dataverse and UKDS."* Two statements in one document, pointing
opposite ways, and the older and more comfortable one is the one that got quoted
in planning. **§5a is the authority: the pool is not tapped.**

Two concrete reasons it is not, both found on 5 October:

1. **"Tapped" was measured at DEPOSIT level, never at EXPERIMENT level.**
   `35M5CV` was marked built after two of its **six** bundled sub-studies were
   done. A screen of the remaining four found `sky-data.sav` — 3,481
   respondents, a clean 1,779/1,702 `Split`, and 36 split-exclusive columns
   asking the same social-distance items about **Brexit identity** (Split 1) or
   **party identity** (Split 2). That is a genuine split-ballot experiment, it
   is the paper's own central comparison, and the schema for it already exists
   (`witness_var` + `not_asked_code`, built for `QQM5MC`). Nobody looked for a
   seventh experiment inside a deposit already marked finished.
2. **Three CC0 deposits were marked "no instrument" and then nothing happened.**
   `PZB01G`, `RJTVG8` and `SACJHE` sat in §5a's table with no status, absent
   from `uk_dataverse_provenance.json` entirely. "No instrument in the deposit"
   is not a reason to drop anything — the appendix ruling makes an author-written
   table or appendix an acceptable primary source, which is why `LOGVPZ` is
   built from its paper's Table 4. The real test is whether the authors' own
   wording is REACHABLE, and `TLT65Z` was dropped on exactly that test (AJPS
   paywall). That test was never applied to these three.

**The generalisable lesson**, since this is the second time a planning table has
aged into an assumption (the first is ledger 106-113): a harvest finding should
record *what was searched* and *at what grain*, not just its conclusion. "Tapped"
with no stated grain cannot be checked, and so it survives being wrong.

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

We may want a **word-for-word-style quote** (justification in the persona's voice), not
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

## 10. Where we actually are (2 October 2026)

**29 experiments from 25 studies. 290,280 rows. 12.4% of the 202-study
catalogue.** All 29 build through the CLI and pass QC. Two warnings in the whole
corpus, both deliberate: `9xw67_conjoint`'s 31 declared profiles whose single
occurrence in 20,480 draws is a refusal, which is precisely what rule 2 exists to
surface; and `QQM5MC`'s unmapped UK persona values, which rule 14 is reporting
exactly as designed and which are the input to the UK vocabulary work. 261 tests.
Licence recorded for all 29.

**`QQM5MC` is BUILT BUT NOT DONE**, by the definition of done in CLAUDE.md. It
has an independent reference (the strongest in the corpus), tests, licence and
provenance — and it still ships that rule 14 warning, which item 2 does not have
an exception for. The warning is true: 6,345 rows carry unharmonised UK persona
values. The UK crosswalk is what closes it. Recorded as a debt with a number on
it rather than waved through, because a documented debt stops being visible the
moment it is documented.

**What the 2 October pass added, none of it new rows:**

- A **checker** on `QQM5MC`, which CLAUDE.md requires and the build had skipped.
  It found five defects — one real answer in a sentinel list, a truncation length
  recalled rather than measured, a wrong journal, an exclusion with a false
  reason, and composed narration never declared. Zero numeric defects, all five
  in the condition-and-notes layer. Fixed.
- `scripts/persona_missing_audit.py` — resolves all 124 declared missing-codes
  against their own value labels. **55 of 124 have never been exercised by their
  own deposit**, so they have never been tested; the `Region_GOR` defect was one.
  It found 618 respondents across `b87sm`, `bf8p2` and `zaqkm` rendering
  "Ideology: Unknown" into their persona text. Fixed.
- `scripts/recipe_prep.py` was filtering Jev's answers through the keyword regex
  Jev exists to beat, so the judgement could only confirm it, and silently skipped
  any variable with over 20 labels — which excluded the 22-level UK education
  ladder. Both fixed; its first unfiltered run found a regex blind spot.
- `qc.reads_as_a_non_answer` is now one definition used by rule 12, the audit and
  the tests, instead of four keyword lists drifting apart.

Up from 14 studies / 80,010 rows at the start of the day. The first jump came
from four studies ALREADY built whose rows the schema could not reach (40,296);
the second from wave 2's five studies (96,630).

Experiments (28) exceed studies (24) because three deposits each hold several:
`yv2ta` two, `9xw67` two (a vignette and a conjoint, and SocSci210 built only
the vignette), `py9q3` three. Expect that gap to widen — `py9q3`'s Parts 2 and
3, `a5v96`'s second vignette, `evnyh`'s Q3-Q16 and `b87sm`'s other items are all
owed, and would add rows without moving the study count. **Mining a deposit we
already hold is far cheaper per row than a new study, but it does not move the
20% figure, which counts studies.**

**The UK layer has begun.** All four Harvard Dataverse UK experiments are
fetched — `QQM5MC`, `TLT65Z`, `X08IVC`, `LOGVPZ` — in their ORIGINAL format,
with licences read from the Dataverse API rather than asserted: **CC0 1.0, all
four.** That matters more than the row count: no TESS deposit grants
redistribution, so these are the first material here that could be published.

**`QQM5MC` is built: 6,345 rows, and the first CC0 rows in the corpus.** Sorace &
Hobolt (2021), YouGov, 24-26 July 2018, a fully crossed 2x2 — a Leaver/Remainer
identity prime crossed with an ONS statement on UK GDP growth — with two outcomes,
a 1-34 ranking of the UK against the OECD and the five-point "is the economy
getting better". 3,266 of 3,267 respondents; the one exclusion is explained below.

It is also the first study whose numbers were **verified against the published
paper before the recipe was written**, and the first with no assignment column at
all. Three things came out of it:

- **A numeric answer key without SocSci210.** UK studies are not in the 210, so
  `comparable_to_socsci210` is false and `mmds crosscheck` has nothing to compare.
  The published regression table is the answer key instead. Both of Table 1's
  models are saturated, so the printed coefficients ARE the eight cell means;
  `scripts/verify_QQM5MC.py` reads the BUILT parquet and reproduces all eight,
  plus both Ns. Expect to need this for every UK study.
- **The witness design.** `Arm.witness_var` + `Condition.not_asked_code`, for an
  instrument that routes respondents to separate blocks of variables and records
  no assignment column — here the only record of who saw what is that the other
  blocks read "Not Asked". Inert for the 28 existing recipes, which rebuild to
  283,935 rows unchanged.
- **One respondent routed to two conditions.** `ID 2158` was asked both the Prime
  only and the Info only blocks. The authors' own reshape keeps that person in
  both groups, so the paper's N of 2,762 counts them twice. A respondent with two
  conditions has none, so the melt drops them and `ambiguous_routing: 1` declares
  it — and the melt FAILS if a re-fetched deposit ever holds a second.

Three UK studies remain unbuilt. The persona vocabulary is the next piece, and is
deliberately being designed after all four deposits are read rather than from this
one — see "Two things that are not done".

### The plan

Not 100% of the catalogue. **20% (~40 studies) chosen for UK value**, so 21
more. `data/catalog/uk_shortlist.json` holds the queue;
`scripts/uk_priority.py --reuse --balance N` regenerates it. Both open
decisions from this morning are settled: the ranking was re-asked as a `Score`
rather than a `Noul` (see below) and survey-methodology studies fell out at two
on merit; `full`-transfer studies are being built first, and wave 1 and 2 are
all `full`.

### Waves

**Wave 1, built and checked:** `a2nbf` 6,211, `5hqan` 6,411, `a42yg` 8,022,
`8ctbk` 17,464 (the first CONJOINT — 1,146 profiles), `yv2ta` 12,139 + 12,131.
Three checkers: `8ctbk` and `5hqan` clean on every point, the other three each
with one real defect, all in the condition-and-notes layer, none touching a
response or a persona value. Zero numeric defects across all five.

**Wave 2, built:** `9xw67` 5,816 + 20,373, `es4xw` 32,228, `sh4px` 6,911,
`ye2ej` 12,971, `py9q3` 6,667 + 5,005 + 6,659. Seven experiments from five
studies, **96,630 rows** — against the ~58,650 SocSci210 records for the same
five, because four of the five were built narrower than what was fielded and the
fifth was built from the wrong document.

**SocSci210 was wrong about all five, each differently.** `9xw67`: vignette
only, control arm dropped, conjoint never attempted. `es4xw`: built from the
proposal's PILOT — eight headshots, a design never fielded. `sh4px`: its two
"conditions" are our two outcome clusters, so the real 10-arm randomisation is
absent. `ye2ej`: an arm dropped, and a banded salary coded as band numbers 1-5
pooled onto a Likert axis. `py9q3`: vignette-3 items under vignette-2 labels,
plus items from a different sub-experiment. Every difference was reconciled
arithmetically rather than asserted. The paper explains the pattern: the 210
were reconstructed by an automated agent.

That makes the base rate 9 of 9 on studies audited closely. **Treat SocSci210 as
a numeric answer key and a lower bound on the design, never as a description of
one.**

### What changed today, beyond the studies

- **The per-(arm, outcome) schema gap is closed**, in both directions:
  `Arm.items` for arms crossed with items, `Outcome.condition_var` for items
  carrying their own assignment. That is what unblocked the 40,296 rows.
- **`sources/quex.py`** — the shared questionnaire-directive resolver. Parses
  89.7% of the 1,853 conditional directives in the corpus and REFUSES the rest
  rather than guessing. Written to a census of all 127 questionnaires, because
  the grammar three worked examples suggested covered only 733 of them.
- **`respondent_vars`** — stimulus wording that varies by respondent rather
  than by arm, resolved per row through `quex`. Fixed 3,117 rows of `a2nbf`
  that had been shipping unresolved template notation no respondent read.
- **`Scale.mid_label`**, after a maker had to write a labelled midpoint into
  free text and invented a word doing it.
- **`Row.factors`** — the row contract requires within-condition structure as
  metadata; 50 distinct factor names now reach the parquet instead of being
  discarded.
- **QC rules 15 and 16** (sequence signposting; licence recorded), and rule 10
  now DECLINES on within-subject designs rather than guessing, via a new
  `notes` channel on the report.
- **`src/micromotives_datasets/jev.py` and `scripts/recipe_prep.py`** — the
  LLM judge now has one home and one door, run before authoring a recipe.
  `tests/test_architecture.py` enforces that the pipeline never imports it:
  builds must stay offline and reproducible.
- **The study ranking was re-asked as `Score`, not `Noul`.** The docs are
  explicit that a `Noul` is a yes/no probability, not a magnitude, and we had
  been ranking 59 studies by `relevance + 0.15 * evergreen`. The `Score`
  version visibly discriminates: evergreen spreads 0.39-3.82 where the `Noul`
  clustered high.
- **`docs/SKIPPED.md`** — every source not built and why: 7 no access, 56 with
  no fielded questionnaire, 2 whose outcome needs US knowledge, 118 not yet
  reached.

### Repairs after the wave-2 audit

The condition screen and the task-dimension crosscheck turned up defects in work
already built and checked. All are fixed; each is in the ledger.

| study | what it asserted | rows |
|---|---|---|
| `8ctbk` | one fixed attribute order; exactly 1 of 1,794 respondents saw it | 17,464 |
| 7 studies | religion severed at the SPSS label ceiling ("…Presbyterian, Pent") | ~27,900 |
| `a2nbf` | a wording variant at Q1/Q2, asked before it appeared | 3,094 |
| `a2nbf` | an open-ended probe administered after every scored outcome | 6,211 |
| `sh4px` | four outcomes DROPPED rather than assert a treatment not yet given | 6,911 → 11,532 |
| `5hqan` | "…in the same position regardless of condition" | 6,411 |

Three schema additions came out of it, each unblocking a recipe that had
documented its own blocker and been refused on grounds that no longer held:
`Arm.raws` (several source codes denoting one condition),
`ItemOverride.condition_text` (a condition can differ by outcome, not only by
condition) and `Condition.line_order_vars` (the instrument randomised which
order its lines appeared in). QC rule 1 now compares per outcome.

### Three things that are not done

**Publication is not cleared for the TESS corpus.** All 24 OSF deposits state NO
licence — `node_license` null, no licence relationship, checked via the OSF API —
and TESS's own site states no reuse terms and has suspended operations. There is
no explicit grant of redistribution rights for any of it. Recorded in every
recipe. It does not block building; it blocks publishing. The four UK Dataverse
studies are the exception and the reason to prioritise them: **CC0 1.0**, stated
by the API, recorded in `data/catalog/uk_dataverse_provenance.json`. The
publishable part of this dataset now has 283,935 rows we cannot ship and **6,345
we can** — `QQM5MC`, built.

**The persona crosswalk is US-anchored, and the UK rows are not yet harmonised.**
Canonical education runs "Less than high school / High school / Some college to
associate / Bachelors to postgraduate"; canonical ethnicity includes "Hispanic".
`QQM5MC` has `education_level` = "No formal qualifications" / "Youth training
certificate/skillseekers" / "Recognised trade apprenticeship completed", and
carries `education_age` ("15 or under", "16", "17-18"), the standard BES measure
with no US analogue at all. A trade apprenticeship has no US rung, and UK
ethnicity is a different classification rather than a relabelling.

**The decision is made: two vocabularies with an explicit mapping, each row tagged
by which it uses** — not one shared ladder that is lossy in both directions. It is
more faithful to "absent stays absent, merged stays merged" and costs more in the
persona layer. It is not yet built. `QQM5MC`'s UK labels pass through unchanged
and QC rule 14 reports them, which is the crosswalk's designed behaviour ("a label
with no mapping is left ALONE") and is the input to this work.

**Build it from all four UK deposits, not from `QQM5MC`.** The four do not even
ask the same education question: highest qualification (`QQM5MC`, 20 levels), age
left full-time education (`TLT65Z` q112, and `QQM5MC`'s own `education_age`), and
ever attended university (`LOGVPZ` `anyUniW19`, 5 levels). No single UK ladder
carries all three. Income is the same story — `QQM5MC` bands gross PERSONAL income
in 14 steps, `TLT65Z` bands annual HOUSEHOLD income in 9 — and only `TLT65Z`
carries ethnicity at all. Designing the vocabulary from the one file we have built
would be the "fixed locally, never swept" shape a sixth time.

**Evaluation is barely exercised.** `scripts/condition_probe.py` is the first
eval this project has had: it scores the condition screen against the five
defects actually shipped, catching 4 of 5 and naming 4 of 5 correctly, with its
one apparent false positive being a true positive on a control written by hand.
Nothing else is measured. Every identifier a real eval needs is present.

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
- `docs/UKDS_UNBUILT.md` — **generated.** All 93 Innovation Panel experiments with
  id, title, description, category, waves and a verdict. Source of truth is
  `data/catalog/innovation_panel_experiments.json`, built by
  `scripts/innovation_panel_catalogue.py` (parses the User Guide; needs the local
  licensed bundle) and rendered by `scripts/innovation_panel_table.py --write`.
  `--check` fails when the doc is stale, and a test runs it.
- `docs/TESS_UNBUILT.md` — the 178 screened, suitable, unbuilt TESS studies.
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
