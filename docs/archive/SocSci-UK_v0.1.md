# SocSci-UK — Dataset Summary (v0.1 draft)

> **Working name:** **SocSci-UK** (signals the lineage to SocSci210).
> Alternatives considered: *BritTrack*, *PanelUK*, *Albion*. Name is provisional.
>
> **One-liner:** A UK counterpart to SocSci210 — but where SocSci210 is a
> cross-sectional *snapshot*, SocSci-UK is **longitudinal**: the same real
> individuals' attitudes and behaviour tracked over 12 years, for training
> models to **predict how a person's politics change over time**.

*Record created from our analysis session. Everything below is measured from
the actual file unless flagged as an estimate.*

---

## 1. Provenance

| | |
|---|---|
| **Source** | British Election Study (BES) Internet Panel, Combined Wave 1–31 |
| **File** | `BES2024_W31_Panel_v31.05.dta` (3.6 GB uncompressed) |
| **Citation** | Fieldhouse, E., J. Green, G. Evans, J. Mellon, C. Prosser, J. Bailey, R. de Geus, H. Schmitt, C. van der Eijk, J. Griffiths & S. Perrett (2026). *British Election Study Internet Panel Waves 1–31.* DOI: 10.5255/UKDA-SN-8202-4 |
| **Access** | Free registration on britishelectionstudy.com; also UK Data Service |
| **Licence status** | Fine for **private, non-commercial** use (current use). **Redistribution / commercial release NOT permitted** without checking BES's own terms / seeking permission. Do **not** re-host the raw file. |

---

## 2. Scale & dimensions

| | |
|---|---|
| **Respondents (rows)** | **126,840** |
| **Variables (columns)** | **13,381** |
| **Distinct measures** | **3,407** (after stripping the `W<n>` wave suffix) |
| **Waves** | **31**, Feb 2014 – Jun 2026 (~12 years) |
| **Labelled variables** | 12,953 have value labels (coded → readable) |
| **Format** | **Wide panel** — 1 row per respondent; each measure repeated per wave (`partyIdW1 … partyIdW31`) |

**Participation (attrition is heavy — plan around it):**

| | |
|---|---|
| Did only 1 wave | 28,519 people |
| **Median waves per person** | **5** of 31 |
| Did ≥10 waves | **39,864 (31%)** ← the usable sequence-modelling core |
| Did all 31 | 108 |
| Tracked across full span (partyId at W1 **and** W31) | 7,027 |

---

## 3. Attributes per person (the persona)

Clean, rich demographic layer — mostly the `p_*` YouGov profile block. Maps
directly onto SocSci210's `demographic` struct, and is **more granular**:

| Attribute | Variable | Categories |
|---|---|---|
| Age | `age` (exact int) + `ageGroup` | 7 bands |
| Gender | `gender` | 2 |
| Education | `p_education` / `p_edlevel` | **20** / 6 |
| Employment | `p_work_stat` + `p_job_sector` | 8 + 5 |
| Ethnicity | `p_ethnicity2` | **19** |
| Household size / children | `p_hh_size` / `p_hh_children` | 10 / 9 |
| Housing tenure | `p_housing` | 9 |
| Income (household + personal) | `p_gross_household` / `p_gross_personal` | 17 / 16 |
| Marital status | `p_marital` | 8 |
| Social grade (NRS) | `p_socgrade` | 8 (A–E) |
| Religion | `p_religion` | 19 |
| Country of birth | `p_country_birth` | 15 |
| Sexuality | `p_sexuality` | 5 |
| Disability | `p_disability` | 3 |
| Geography | `country`, `gor` (region), **`new_pcon` (constituency)**, `oslaua` (local authority) | — |
| Party ID | `partyId` | 13 |
| Ideology | `leftRight` (0–10), `al_scale` (lib–auth 0–10) | scales |
| Media diet | `p_paper_read` | 16 |
| Vote history | `p_past_vote_2005 … 2024`, `p_eurefvote` (Brexit) | — |
| Personality | `big_five_*` (mini-IPIP trait scores) | continuous |

**Verdict vs SocSci210:** matches or beats it on 13 of 16 shared fields, adds
~8 fields SocSci210 lacks (religion, media diet, vote history, personality,
social grade, sexuality, disability), and geography goes down to **constituency**
vs US "state". Only real gap: no dwelling-*type* field.

---

## 4. Topics covered

~1,700 substantive measures spanning UK political & social attitudes:

| Theme | ~measures | Examples |
|---|---|---|
| Vote & elections | 516 | `generalElectionVote`, `turnoutUKGeneral` |
| EU / Brexit | 258 | `euRefVote`, `scotIndepJoinEU` |
| Economy | 178 | `econPersonalRetro`, `riskUnemployment` |
| Media & information | 155 | `infoSourcePaper`, `twitterUse` |
| Parties & leaders | 108 | `likeCon…likeSNP`, `bestPM` |
| Identity & values | 92 | `leftRight`, `al_scale`, `efficacy*` |
| Immigration | 89 | `changeImmig`, `immigEcon` |
| Welfare / inequality | 75 | `redistSelf`, `riskPoverty` |
| Health / NHS | 59 | `changeNHS`, `cutsTooFarNHS` |
| Environment | 49 | `enviroProtection` |
| Crime / justice | 44 | `changeCrime` |

---

## 5. Question → response format

Responses are **ordinal integers — the same shape as SocSci210's `response`**
(with `9999` = Don't know to strip). Examples:

| Question | Scale |
|---|---|
| `likeCon` — like/dislike Conservatives | 0–10 |
| `leftRight` — left/right self-placement | 0–10 |
| `redistSelf` — govt should equalise incomes | 0–10 |
| `immigEcon` — immigration bad/good for economy | 1–7 |
| `changeImmig` — immigration higher/lower | 1–5 |
| `econPersonalRetro` — household economy better/worse | 1–5 |
| `efficacyPolCare` — "politicians don't care" | 1–5 |
| `satDemUK` — satisfaction with UK democracy | 1–4 |

---

## 6. How the questions differ from SocSci210

Same **response format** (ordinal integers), but the questions are built on a
fundamentally different unit.

**Core difference:** SocSci210 questions come **with a stimulus** — a scenario
you read, then *react* to (they are experimental outcomes). BES questions are
mostly **bare, direct questions** about the real world (observational).

| | SocSci210 | BES |
|---|---|---|
| **Stimulus** | *"You read: 'Jaime is 20, was born a girl, now identifies as non-binary…'"* | *(none)* |
| **Question** | *"How likely is Jaime to still identify as non-binary in 5 years?"* | *"How much do you like the Conservative Party?"* |
| **Response** | 1–7 | 0–10 |
| **Asks the model to…** | *reason about a novel scenario* | *report a real, standing attitude* |

**The dimensions that differ:**

| Dimension | SocSci210 | BES |
|---|---|---|
| Stimulus present? | ✅ every question has a scenario | ❌ most questions are direct |
| Experimental? | ✅ outcome of a randomised condition | ❌ mostly observational |
| Referent | **fictional / hypothetical** (Jaime, a Hyundai Kona) | **real world** (actual parties, leaders, Brexit) |
| Topic breadth | **very broad** — 210 studies across psych/econ/sociology/comms/politics | **narrow & deep** — UK politics only |
| Time | one-shot (asked once) | **repeated** over 31 waves |
| Scales | heterogeneous per study (1–7, 0–100, binary) | standardised political scales (0–10, 1–5) |

**Why it matters (the axes are orthogonal):**

- **SocSci210's power is the *stimulus* axis** — "how does this persona react to
  a scenario it's never seen?" Its questions are rich *because of the attached
  scenario*.
- **BES's power is the *time* axis** — "how does this real person's attitude
  *move over 12 years*?" A single `likeCon = 5` is a thin datapoint; `likeCon`
  moving 8→5→2 across the Brexit years is a rich one.

**Design consequence:** don't force BES questions into SocSci210's
stimulus-reaction mould — most have no stimulus, so as isolated Q→A pairs they
are *weaker* than SocSci210's. Their value appears only when **sequenced over
time** — the dimension SocSci210 lacks. (Exception: the handful of BES
*experiments* like `scotWording` *do* carry a SocSci210-style manipulated
stimulus — see §7.)

---

## 7. Experiments (condition → outcome → response)

BES **embeds** experiments in the panel via `gets<Name>` random-allocation
flags and `$RV<n>` random fills. **Key finding: the released panel file keeps
the OUTCOMES but usually strips the CONDITION/randomisation variables.**

| Experiment | Type | Recoverable from this file? |
|---|---|---|
| `scotWording` (W21) — 3 randomised wordings of the Scottish independence question | wording manipulation | **✅ fully** (arms are separate vars; ~2,800 respondents, ~940/arm; shows an acquiescence effect) |
| `expectationManip` (W1) — devo-max priming | priming | ⚠️ outcome only, condition stripped |
| candidate-choice vignette (`getsBrandenburg`) — randomised name/gender/class/education/party | vignette | ❌ conditions (`$RV*`) not in file |
| `getsHuddy` / `getsTT` / `getsPTV` … | split-sample | ⚠️ outcome present, allocation flag not |

**Implication:** truly recoverable `condition→outcome` experiments in this file
are essentially **one** (`scotWording`) — far fewer than SocSci210's 210. To use
the richer vignette/priming experiments you'd need BES's supplementary
experiment files or to contact the BES team.

---

## 8. The real differentiator: observational + longitudinal

- **Observational** = plain questions (not manipulated) — measures real attitudes.
- **Longitudinal** = the *same people* over *31 waves / 12 years* → a per-person
  **time series**.

This is what SocSci210 structurally **cannot** do. Concrete example from the
file — respondent `10997`, all 31 waves:

> 2014 undecided → flirts with UKIP → Labour *identity* but votes Conservative
> from 2016 → identity becomes Conservative by 2018 → Reform UK by 2024–2026.

A textbook "red wall" realignment, visible wave by wave. Scale of this layer:
~1,700 measures × up to 31 waves × ~40k well-covered respondents = **tens of
millions of person-wave-item observations.**

**Enables the headline task:** *given a person's demographics + attitudes through
wave t, predict their behaviour/vote at wave t+k* — forecasting real individual
trajectories, not simulating a persona.

---

## 9. Prompt format & the two modes (with / without stimulus)

All sources share **one uniform prompt template**, so BES (no stimulus) and
stimulus-bearing sources (SocSci210, BES experiments) train the *same* model.
The stimulus is an always-present slot with an explicit sentinel — **not** a
cryptic `<blank>` token:

```
You are a UK survey respondent with this profile:
- Age: 61 · Gender: Male · Region: North East · Education: GCSE · Party ID: Labour
[optional history, longitudinal only:]
  2015: like Labour = 8 · 2017 = 6 · 2019 = 3
Scenario: none                       ← BES / standing-attitude mode
Question: "How much do you like the Labour Party?" (0–10)
Answer with the number only.
```

For a stimulus source, only the slot changes:

```
Scenario: "A new policy would cut immigration by 50%…"   ← reaction mode
```

**The sentinel is the mode switch — it does real work:**

| Slot | Model behaviour | Trained by |
|---|---|---|
| `Scenario: none` | give the person's **standing attitude** | BES observational (the bulk) |
| `Scenario: "<text>"` | **react** to the scenario | SocSci210 + BES experiments |

So the empty-stimulus BES rows aren't wasted — they teach the "no scenario →
standing view" mode, and the sentinel lets the model tell it apart from the
"react" mode. At application time you flip behaviour with a one-line edit.

**Rules that keep this valid:**
- **Use a natural sentinel** (`none`), consistent across every source — not a
  special token (brittle, tokenises badly).
- **Watch the mix ratio.** Both modes must be well represented; if the data is
  almost all `Scenario: none` (BES-heavy), the reaction mode barely trains and
  the model drifts toward ignoring the slot. Blend in enough filled-scenario
  examples.
- **Never fabricate a stimulus onto a BES answer** (see the iron rule): the BES
  response was given with *no* stimulus, so attaching an invented one teaches
  the model that stimuli don't matter. Filled-scenario data must come from real
  stimulus→response pairs (SocSci210, experiments, or new Prolific collection).

---

## 10. Training on time — variable-horizon forecasting

Because BES is longitudinal, we can train **one model to forecast at any time
distance** — short *and* long term — by building pairs of
`(history up to wave t) → (state at wave t+k)` where the horizon `k` varies.

**Prompt format** — the horizon is just another field (like scale / scenario):

```
[persona]
History (their past answers):
  2015-05: like Labour = 8
  2017-06: like Labour = 6
  2019-12: like Labour = 3
Scenario: none
Predict their answer as of: 2024-07        ← the horizon (real DATE, not "+4 waves")
Question: "How much do you like Labour?" (0–10)
```

**Three design rules:**

1. **Horizon must be in the prompt.** History→"predict" is ambiguous — 6 months
   vs 5 years give different answers. State the target date.
2. **Use real dates, not wave counts.** Waves are unevenly spaced (cluster around
   elections), so "+4 waves" isn't a fixed gap. Real dates also let the LLM use
   its world knowledge (2016 Brexit, 2019 election, 2020 COVID) to explain jumps
   — an advantage a classical time-series model doesn't have.
3. **Sliding windows → many pairs per person.** From one sequence
   `[W1,W3,W5,W10,W20,W31]` generate many `(history, horizon)` pairs spanning
   short + long. Multiplies training data from a modest number of people (helps
   the "~10% of data is enough" budget reality).

**What it learns per horizon:**

| Horizon | Signal |
|---|---|
| Short (1 wave) | mostly **persistence** + small drift |
| Long (many waves) | real **dynamics** — realignment, event shifts (respondent 10997's Labour→Reform arc) |

**Evaluation (a nice result in itself):**
- **Accuracy binned by horizon** → a decay curve (accuracy falls as you forecast
  further out).
- **Beat the persistence baseline** ("predict last observed value") — the model
  earns its keep at long horizons.
- **Out-of-time split** for honesty: train on waves ≤ W25, forecast W26–W31 (real
  future, not interpolation).

**Traps:** (a) **balance the horizons** — over-sampling 1-wave-ahead pairs makes
the model just copy the last value; deliberately weight in long horizons.
(b) **leakage / survivorship** — never leak target-wave info into history; split
**by person** (and by time); people present at far-future waves are survivors
(report the bias).

---

## 11. Known caveats / data-quality notes

1. **Stimulus gap (the core design limitation)** — BES is ~all stimulus-free
   survey data (§6). A BES-only model learns persona + trajectory but **cannot
   reliably react to a novel stimulus** in an application — the `Scenario:` slot
   would be untrained, so it either ignores the stimulus or reverts to base-model
   reasoning. Fix: train the reaction mode on **real** stimulus→response data
   (SocSci210, BES experiments, OSF vignettes, or new Prolific collection) and
   **never fabricate a stimulus onto a BES answer** (see §9). Validate any
   stimulus prediction on held-out experiments before trusting it.
2. **Condition variables stripped** — most experiments' randomisation isn't in
   this file (see §7).
3. **Attrition is non-random** — long-term stayers skew older / more engaged;
   the 7k full-span respondents are not representative.
4. **Waves aren't evenly spaced** — they cluster around elections (2015, 2016
   ref, 2017, 2019, 2024). Use `starttime`/`endtime` for real time gaps.
5. **Panel conditioning** — repeated interviewing can itself change respondents.
6. **Ragged coverage** — people skip waves then return; handle gaps.
7. **Text encoding** — `£` currently renders as `Â£`; read with the right
   encoding (`pyreadstat.read_dta(..., encoding=...)`) before shipping labels.
8. **`9999` = Don't know** across most items — strip/handle explicitly.

---

## 12. Tooling

Inspect with `bes_inspect.py` (see `BES.md`):

```bash
python bes_inspect.py overview        # dimensions & waves
python bes_inspect.py measures        # topic coverage
python bes_inspect.py search brexit   # find variables
python bes_inspect.py demographics    # persona fields
python bes_inspect.py experiments     # randomised items
python bes_inspect.py values partyId  # labels + distribution
python bes_inspect.py sample --vars age,gender,partyId
```

---

## 13. Status & next step

- ✅ Source acquired, format understood, persona + topics + response format mapped.
- ✅ Confirmed differentiator: individual longitudinal forecasting.
- **Next:** build the **wide → long converter** — turn the wide file into tidy
  `(person, wave, measure, value)` trajectories, the input every forecasting
  model needs.
