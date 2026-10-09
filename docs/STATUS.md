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

**751,067 rows across 63 experiments**, all QC-passed and on disk at
`data/processed/`.

| | experiments | rows |
|---|---|---|
| US (TESS deposits) | 28 | 283,935 |
| UK-native | 35 | 467,132 |
| **total** | **63** | **751,067** |

Ten largest: `EFXNLX` 49,395 · `evnyh` 33,932 · `es4xw` 32,228 · `9xw67_conjoint`
20,373 · `b87sm` 19,282 · `8ctbk` 17,464 · `cug34` 15,091 · `z358z` 14,702 ·
`POMIFD` 13,268 · `ye2ej` 12,971.

### The licence position, which shapes everything

| source | licence | can it be published? |
|---|---|---|
| 24 TESS deposits | none stated | **No** |
| 4 Harvard UK deposits | CC0 1.0 | **Yes** |
| `POMIFD` | no licence, but **the author gave written permission to use it** (Jack Blumenau, 6 Oct 2026) | No — see below |
| UKDS SN 6849 (Innovation Panel) | UKDS End User Licence | **No** |
| BES Internet Panel | BES own terms — grants distribution, share-alike | **Yes, conditionally** |

Most of the corpus cannot be redistributed. That is not a blocker for building or
for research use; it is a blocker for release.

**On `POMIFD`, because the table cannot hold it.** The deposit states no licence
— `license` is literally null on Dataverse, re-checked live. Its terms say "You
may wish to communicate with the Contact(s) specified before use", so rich
emailed Jack Blumenau at UCL on 5 Oct 2026, before fetching anything, describing
the project and stating plainly that nothing would be redistributed. He replied
the next day: *"Of course, very happy for you to use that data. Do let me know
how your study turns out!"*

So the basis for using it is **explicit consent from the author**, not an
unanswered courtesy notice, and the delete-if-they-object commitment is
discharged. What that consent is not: he agreed to USE, having been told nothing
would be redistributed, so it is not a licence to publish and `redistributable`
stays false. He also asked to hear how the study turns out, which is worth
honouring.

---

## 3. The Innovation Panel — the main remaining source

UKDS SN 6849. 93 experiments across 17 waves, all screened in
`data/catalog/innovation_panel_experiments.json` and rendered to
`docs/UKDS_UNBUILT.md`.

| verdict | count |
|---|---|
| **build** | 40 |
| marginal | 9 |
| drop | 44 |

**13 of the 40 are built**, 324,392 rows in all. 9.10, the housework scenarios: 9,631
rows across waves 5 and 6. 9.18, successful ageing: 12,567 rows across waves 9 and
17. 9.39, flexibility stigma: 17,656 rows, wave 16. 9.36, alcohol in units or drinks: 4,208 rows, wave 15. 9.24, EQ-5D forms: 21,901 rows, wave 11. 9.4, occupation or profession: 1,746 rows, wave 2. 9.17, sexual identity by item counts: 24,992 rows, waves 8 and 9. 9.31, ReQoL-10 / EQ-5D / GHQ-12 order: 84,995 rows, wave 14. 9.42, compound growth as money or sea level: 9,240 rows, wave 16. 9.20, satisfaction layouts: 8,025 rows, wave 9. 9.13, time and risk choices: 109,770 rows, waves 6 and 7. 9.9, fertility after friends: 939 rows, waves 4 and 5. 9.47, two ways of asking about caring: 18,722 rows, wave 17. **27 remain.** (9.43, 9.48, 9.12 and 9.11 were moved from build to
drop on 9 Oct; see the plan below.)

`docs/EXPERIMENTS.md` is the generated list of everything built. Each Innovation
Panel wave counts as its own experiment there, so these thirteen studies are twenty-two
entries.

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

## 4. The plan: 16 experiments, all triaged

**Triage done 9 October. All 16 are buildable. Nothing dropped out.**

We expected to lose some. A check like this can only disqualify an experiment,
never qualify a new one, so sixteen was the ceiling and the real question was how
far below it we would land. The answer is: not at all. The User Guide names an
allocation variable, says which file it is in, and writes out what each arm
means, for every one of the sixteen.

`scripts/ip_triage.py` did the data-existence check and `scripts/ip_wording.py`
the questionnaire check; the rest was read by hand, for reasons given below.

**The wording exists for all sixteen, verified 9 Oct against the actual PDFs.**
This is the check that decides whether a build renders real stimulus text or an
invention, and it is separate from the triage: 14 were located automatically, and
the two that were not — EQ-5D variants and Measuring identity — were read by hand
and both carry their full wording and response options.

**Wave 2's questionnaire has a different layout from waves 5 onward**, and
Measuring identity is the one experiment here that uses it: asterisk-delimited
headings (`*EthExp_A*`), inline universe conditions (`*Universe* IF
ff_identityw2 = 1`), and no `Text` marker at all. Whatever parses the later waves
will not parse it.

### Build order

Reordered from section 3 on one triage finding: **"What do the general
population regard as 'successful ageing'?"** was listed as a measurement study
and is in fact a **2⁶ factorial of scenarios across two waves**, with randomised
names — the same shape as the housework scenarios already built, and covered by
the existing `Condition.template` machinery. It moves to the front.

| # | id | experiment | category | wave | allocation variable |
|---|---|---|---|---|---|
| 1 | 9.18 | What do the general population regard as "successful ageing"? **BUILT 9 Oct** | wellbeing | 9, 17 | 2⁶ factorial, allocated in the questionnaire |
| 2 | 9.39 | Vignettes: measuring flexibility stigma — double whammy or femininity stigma **BUILT 9 Oct** | family-care | 16 | `fsvigname1-3`, `fsvigparent1-3`, `fsvighybrid1-3`, `fsvigorguse1-3`, `fsvigorgpol1-3` |
| 3 | 9.43 | Mental health questions comparisons **DROPPED 9 Oct — see below** | health | 16 | `ff_mhealthexpw16` in `p_hhsamp_ip` |
| 4 | 9.36 | Alcohol consumption **BUILT 9 Oct** | health | 15 | located in `o_hhsamp_ip` |
| 5 | 9.24 | Variations of the EQ-5D questions **BUILT 9 Oct** | health | 11 | `eq5dcond` in `k_indresp_ip` |
| 6 | 9.4 | Measuring identity **BUILT 9 Oct** | attitudes | 2 | located in the wave 2 files |
| 7 | 9.48 | Labour market expectations **DROPPED 9 Oct — see below** | work-money | 17 | 7 variables located |
| 8 | 9.17 | Measuring sexual identity using direct and indirect questioning **BUILT 9 Oct (item counts)** | sensitive | 8, 9 | 2 variables located |
| 9 | 9.31 | Comparison of ReQoL-10 to other scales **BUILT 9 Oct** | health | 14 | 4 variables located |
| 10 | 9.12 | Measuring change in self-assessed disability **DROPPED 9 Oct — see below** | health | 6, 7 | dependent interviewing |
| 11 | 9.42 | Understanding of the long-term future **BUILT 9 Oct** | attitudes | 16 | 4 variables located |
| 12 | 9.20 | Presentation of response options in satisfaction questions **BUILT 9 Oct** | wellbeing | 9 | 1 variable located |
| 13 | 9.13 | Associated Study: measuring time and risk preferences **BUILT 9 Oct (one condition)** | work-money | 6, 7 | 13 variables located |
| 14 | 9.11 | Subjective expectations about the returns to higher education **DROPPED 9 Oct — see below** | work-money | 5, 8, 9 | 2 variables located |
| 15 | 9.9 | Context effects in fertility decisions **BUILT 9 Oct** | family-care | 4, 5 | `d_ff_fertw4` in `d_hhsamp_ip`, Group 1 / Group 2 |
| 16 | 9.47 | Identification of informal caregiving **BUILT 9 Oct** | family-care | 17 | 3 variables located |

### Experiment 1, successful ageing — BUILT 9 Oct

**12,567 rows: wave 9 5,967, wave 17 6,600.** Both QC PASS with no warnings.
Recipes `recipes/ukds_6849_vig_ageing_w{9,17}.yaml`, generator
`scripts/gen_ip_vig_ageing.py` (`--check` verifies every derived name against the
archive), tests `tests/test_ip_vig_ageing.py`. Verified by a separate checker
agent that re-transcribed both questionnaires and re-rendered all 12,567 rows from
the raw files: 0 condition, 0 outcome, 0 name and 0 code disagreements. No
publication to check against; the User Guide cites none.

What the build settled, beyond the groundwork recorded before it:

- **Wave 17's randomisation partly failed (ledger 125).** 354 web respondents,
  mostly in December 2024, share one identical allocation; 933 in all share
  theirs with someone. Wave 9 is clean: 2,010 distinct allocations out of 2,010.
  The rows are real (the stored codes are what filled the text), but wave 17 is
  not a balanced factorial. Use wave 9 to estimate a dimension's effect, or drop
  or down-weight the 354.
- **The two waves get separate templates, not one.** Wave 17's extra comma is
  kept: word-for-word, and each wave has its own recipe anyway.
- **The question names the person**, so it is the outcome, rendered per cell
  through the new `ConditionTemplate.outcome_questions`. It is not folded into
  the condition.
- **The schema addition grew by one field.** `Level.parts` as planned, plus
  `outcome_questions` (one question template per task), plus a guard that no rendered text or
  question may contain a brace. All 43 earlier experiments rebuild to
  row-identical output, personas included.
- **Wave 17 has 681 rows (10%) with no age and no sex.** These were coded -8 in
  the deposit, and the rows ship without age and sex rather than a guess.
- **Neither wave documents a constraint on repeated profiles.** Wave 9 never
  repeats description 1's six life codes in description 2; wave 17 never repeats
  them in any pair.

### Experiment 2, flexibility stigma — BUILT 9 Oct

**17,656 rows, wave 16 (2023).** QC PASS with no warnings. Recipe
`recipes/ukds_6849_vig_flexstigma_w16.yaml`, generator
`scripts/gen_ip_vig_flexstigma.py`, tests `tests/test_ip_vig_flexstigma.py`.
Working respondents aged 18-65 play an HR manager and rate three job candidates on
four 0-10 questions (recommend, commitment, productivity, team player). Gender (by
name), parenthood, own home working, company prevalence and company policy vary;
576 arms, 192 per slot. The allocation is clean: 1,616 distinct among 1,616.

- **Independent checker: PASS, no defect in the rows.** It transcribed the
  questionnaire itself and re-rendered all 17,656 rows from the raw file with 0
  condition, outcome, response, name or pronoun disagreements. It found one latent
  schema gap: a task left out of `outcome_questions` shipped its bracketed fallback
  with QC silent. Now refused at load (ledger 131).
- **A published reference exists and has not been checked:** Chung & Wang (2024),
  ISER working paper 2024-11, pp. 105-123. The PDF sits behind a browser check this
  machine cannot pass; download it by hand to `data/raw/ukds_6849/` to compare.
- **"Candidate 1:" is dropped from the text**, because a row cannot cite its own
  position. The four questions each name or pronoun the candidate, so each is
  rendered per cell. That needed `ConditionTemplate.outcome_questions` (one
  question per task), which replaced 9.18's single-question field the same day.
- `fsvrecall`, the end-of-module recall check, is not built: it asks about all three
  candidates at once and has no single condition.

### Experiment 3, mental health questions — DROPPED 9 Oct

Decided by rich after reading the questionnaire. The three versions are "code all
that apply" lists that differ between versions:

- **A:** one 20-item list with "Clinical depression".
- **B:** a list with "An emotional, nervous or psychiatric problem", then a
  follow-up asking which type.
- **C:** a separate 18-item mental-health list before the physical one.

A row is one question and one answer. Every way to build it either turned a tick
list into yes/no answers nobody gave, or pooled differently worded questions as
one outcome. Recorded as `drop` in the catalogue with that reason. **The triage's
PASS was about the data existing, not the outcome's shape** (ledger 132).

### Experiment 4, alcohol in units or drinks — BUILT 9 Oct

**4,208 rows, wave 15 (2022).** QC PASS with no warnings. Recipe
`recipes/ukds_6849_alcohol_w15.yaml`, generator `scripts/gen_ip_alcohol.py`, tests
`tests/test_ip_alcohol.py`. The first question-wording build in the Innovation
Panel layer: AUDIT-C items 4 and 5 asked in units (NHS wording) or in drinks, split
by household.

- **The condition is narrated** — `You were asked: "<question>"` — by the `rpw4u`
  precedent, because the question is the only stimulus. The added words are
  recorded in the notes.
- **The binge threshold follows the respondent's sex** (6 for women, 8 for men).
  It is resolved per row through `respondent_vars` and is not an arm.
- **Not rendered:** version A's Help definition of a unit. It sits behind a help
  link, so nobody knows who read it.
- **Independent checker: PASS, no defect in the rows.** It re-rendered all 4,208
  rows from the raw files with 0 mismatches and confirmed the sex fill. It corrected
  three statements in the notes: phone respondents heard the unit definition, the
  allocation counts were respondents rather than households, and 8 answerers had
  been routed out of self-completion. All three are now recorded in the recipe.
- **Endpoint labels only.** The answer instruction names 1 and 5 ("1-2"/"10+",
  "Never"/"Daily or almost daily"), not the uneven bands between (ledger 133).

### Experiment 5, EQ-5D 3-level and 5-level forms — BUILT 9 Oct

**21,901 rows across two experiments, wave 11 (2018).** 5-level answers 13,203,
3-level answers 8,698, both QC PASS with no warnings. Recipes
`recipes/ukds_6849_eq5d{5l,3l}_w11.yaml`, generator `scripts/gen_ip_eq5d.py`, tests
`tests/test_ip_eq5d.py`.

- **An order experiment, built on prior exposure** (rich's ruling). The condition
  is whether the other form had been asked earlier, quoting its items
  word-for-word, or that it had not. Arms that differ only by position share a
  condition, because a row cannot say where it sat.
- **Exposure is what happened, not what was allocated.** 70 and 69 respondents
  whose arm put the other form first, but who skipped the early module, are
  excluded rather than told something false.
- **Each question lists its options**, because the middle levels are the
  difference between the forms (ledger 133).
- **Independent checker: PASS, no defect in the rows.** It rebuilt both
  experiments from the raw file with 0 mismatches across 21,901 rows. It sharpened
  the exclusion: only 6 and 7 of those people answered this form, so 30 and 34 rows
  were lost. It also showed the exclusion is a small selection after allocation
  (face-to-face early-module refusers); both points are now in the notes.

### Experiment 6, occupation or profession — BUILT 9 Oct

**1,746 rows, wave 2 (2009).** QC PASS with no warnings. Recipe
`recipes/ukds_6849_identity_w2.yaml`, generator `scripts/gen_ip_identity.py`, tests
`tests/test_ip_identity.py`. A one-word split ballot. The first item of an identity
battery asks how important "Your occupation?" or "Your profession?" is to your sense
of who you are, split by household. Only that item is built; the other twelve are
identical in both versions. The older asterisk layout of the wave 2 questionnaire
needed no parser, because it was read by hand. The household join checks against
indresp's own copy with 0 disagreements in 1,788 comparisons.

- **Independent checker: PASS, no defect in the rows.** It re-rendered all 1,746 rows
  from raw with its own join: 0 condition, outcome or response mismatches. It found
  one test checking a row against itself rather than against the raw allocation;
  fixed.

### Experiment 7, labour market expectations — DROPPED 9 Oct

Decided by rich. The randomised part asks for a percentage chance over six earnings
buckets. Each bucket's £ bounds were computed on screen from the respondent's own
wage, or from their estimate of the market wage ("£ [0.85 x LMEANCHOR]"). The
deposit stores the anchor but not the bounds shown, and the questionnaire does not
say how they were rounded or formatted. So the exact stimulus cannot be recovered,
and every row would carry the respondent's own earnings as stimulus. Recorded as
`drop` in the catalogue.

### Experiment 8, sexual identity by item counts — BUILT 9 Oct

**24,992 rows: wave 8 12,672, wave 9 12,320.** Both QC PASS with no warnings.
Recipes `recipes/ukds_6849_itemcount_w{8,9}.yaml`, generator
`scripts/gen_ip_itemcount.py`, tests `tests/test_ip_itemcount.py`. Six lists per
respondent per wave, each answered with a count; three carry a sensitive statement,
which three depending on group, and that assignment flips between the waves.

- **A schema addition: `ItemOverride.line_order_vars`.** Statements were shuffled
  per respondent, with one order variable per list, so each (arm, list) cell names
  its own. Bullets stay bullets and the stem stays put. A row with no recorded
  order is skipped rather than rendered in a guessed order. Inert for every other
  study (full rebuild).
- **Built: only the item-count lists.** The direct-question split (ONS against
  UKHLS wording) is not built: the ONS version is answered by reading a code off a
  showcard.
- **Independent checker: PASS, no defect in the rows.** It extracted both
  questionnaires itself and re-rendered all 24,992 rows from the raw files: 0
  condition and 0 response mismatches. **The order code's reading is unverifiable**
  (ledger 135). "3124 = statement 3 shown first" is the natural reading, but no
  document or data pattern settles it, and about two-thirds of rows depend on it.
  The statements shown and the responses are right either way. The checker also
  showed that a row answered without a recorded order would have been dropped
  silently; it now stops the build.

### Experiment 9, ReQoL-10, EQ-5D and GHQ-12 in order — BUILT 9 Oct

**84,995 rows across two experiments, wave 14 (2021).** ReQoL-10 and EQ-5D answers
48,548, GHQ-12 answers 36,447, both QC PASS with no warnings. Recipes
`recipes/ukds_6849_{reqol,ghq}_w14.yaml`, generator `scripts/gen_ip_reqol.py`,
tests `tests/test_ip_reqol.py`. Your 9.24 ruling applied to the same design: each
block is conditioned on whether the other had been asked earlier.

- **The allocation variable is wrong for half the sample** (ledger 134). For the
  refreshment households, `n_req10cond` holds a value that has nothing to do with
  what they were asked; their arm is in `n_ff_req10cond`. Taken from the right
  place, 0 answers sit in a module the arm did not use.
- **Wording follows mode.** Telephone respondents heard different ReQoL and EQ-5D
  wording, resolved per row. "First, " and "Next, " are dropped from the
  telephone EQ-5D, because they cite position.
- **Independent checker: FAIL, then fixed.** It found a real wording defect.
  Telephone respondents heard the EQ-5D options in the second person ("You have no
  problems in walking about."), but my extractor never read the telephone options
  block, so 1,326 telephone EQ-5D rows and 1,786 GHQ conditions carried the
  self-completion wording ("I have …"). It also found a "Finally, " the sequence
  rule should have dropped. Both are fixed, with a test that kills the old
  behaviour (ledger 137). Its other checks passed: allocation, responses and row
  counts, with 0 mismatches.

### Experiment 10, self-assessed disability — DROPPED 9 Oct

Dropped by the 9.43 ruling. The long-standing-illness question is word-for-word
the same in groups 1 and 3 (group 2 is not asked it), and the
dependent-interviewing check fires only after the answer, and only if it
contradicts last year's. So nothing differs at the moment of answering. The other
outcomes, the difficulties list and the follow-up asking why things changed, are
"code all that apply" lists.

### Experiment 11, compound growth as money or sea level — BUILT 9 Oct

**9,240 rows across two experiments, wave 16 (2023).** Environmental answers 4,638,
financial 4,602, both QC PASS with no warnings. Recipes
`recipes/ukds_6849_numeracy_{env,fin}_w16.yaml`, generator
`scripts/gen_ip_numeracy.py`, tests `tests/test_ip_numeracy.py`. The same
arithmetic, compounding at 1% a year, framed as savings or as sea level. Built on
prior exposure: the condition is whether the other frame was asked earlier.

- **The archive's labels for the order are reversed** (ledger 138). They say 1 =
  environmental first; the questionnaire and the data say 2. The build follows the
  routing, and 0 answers fall outside it.
- **Independent checker: PASS.** It rebuilt every row from raw (0 condition,
  response or arm mismatches across 9,240) and confirmed the label reversal
  independently. A flipped allocation makes `--check` report 3,132 misrouted
  answers.

### Experiment 12, satisfaction layouts — BUILT 9 Oct

**8,025 rows, wave 9 (2016).** QC PASS with no warnings. Recipe
`recipes/ukds_6849_satisfaction_w9.yaml`, generator
`scripts/gen_ip_satisfaction.py`, tests `tests/test_ip_satisfaction.py`. The same
four satisfaction questions in a grid, or one per screen with vertical or
horizontal options. No word differs, so each condition is one sentence of
description. That is CONVENTIONS' layout exception, as evnyh used it, and the
sentence is built from the questionnaire's own scripting note. Respondents who
heard the questions are excluded, because no layout was shown to them: 30 by
telephone, and 75 whose interviewer read it out.

- **Independent checker: FAIL, then fixed.** It rebuilt every row from raw with 0
  mismatches, but found the 75 read-out respondents (`scac` = 2, 299 rows) carrying a
  screen layout they never saw. They are now excluded, the same rule as telephone,
  with a test that kills the old behaviour.

### Experiment 13, time and risk preference choices — BUILT 9 Oct

**109,770 rows: wave 6 63,487, wave 7 46,283.** Both QC PASS with no warnings.
Recipes `recipes/ukds_6849_timerisk_w{6,7}.yaml`, generated with the data by
`scripts/gen_ip_timerisk.py` from the questionnaire PDFs. Tests
`tests/test_ip_timerisk.py`.

- **One condition, not an experiment** (your ruling). Everyone saw the same
  preamble and the same 91 choices (72 money-over-time, 19 lotteries). The only
  randomisation, who was paid for real, came after the answers. Built because
  these are genuine incentivised choices.
- **Two small shared-code changes, both first exercised here.** A study with no
  factors writes its factors column as null (Parquet cannot store an empty
  struct). Resolved fills are trimmed of trailing whitespace. Every other study
  using fills rebuilds identically.
- **Independent checker: PASS.** It re-derived all 109,770 rows from raw with 0
  condition, outcome or response mismatches. On its advice the second appeal's
  closing instruction ("…enter 1 or else just return the laptop") is dropped as
  survey mechanics, because "1" is also an answer code in those rows. The trim
  change now has its own mutation-tested unit test.

### Experiment 14, returns to higher education — DROPPED 9 Oct

The information treatment is a graph ("Display Earnings graph on screen", a page
handed to face-to-face respondents). The questionnaire carries only one framing
sentence. The earnings figures exist only in the image, and the wave 8 graph is
not reproduced anywhere in the documentation. A condition without the numbers
leaves out the treatment, and one with them would invent it. Dropped under the
catalogue's visual-stimulus ruling.

### Experiment 15, fertility asked before or after friends — BUILT 9 Oct

**939 rows: wave 4 532, wave 5 407.** Both QC PASS with no warnings. Recipes
`recipes/ukds_6849_fertility_w{4,5}.yaml`, generated with the data by
`scripts/gen_ip_fertility.py`. Tests `tests/test_ip_fertility.py`. A priming order
experiment: the expected-fertility questions came before or after a block about
the respondent's close friends. Built on prior exposure. The friends block is a
loop that can't be quoted whole, so its opening question (and, for those with a
close friend, the loop's own opening) is quoted behind a narrating clause.
Small: self-completing continuing respondents of childbearing age.

- **Independent checker: PASS.** 0 condition and 0 response mismatches in both
  waves, and the module order confirmed in both questionnaires. On its findings,
  wave 4's Version B carries its printed wording ("will have **and** (more)
  children?", almost certainly a typo but the source's), and web respondents'
  friends question omits "Enter number", which is only a box label there.

### Experiment 16, two ways of asking about caring — BUILT 9 Oct

**18,722 rows across two experiments, wave 17 (2024).** Activity-hours answers
13,875, existing caring questions 4,847, both QC PASS with no warnings. Recipes
`recipes/ukds_6849_caring_{activity,existing}_w17.yaml`, generated with the data by
`scripts/gen_ip_caring.py`. Tests `tests/test_ip_caring.py`. Everyone was asked both
sets, one early and one late. Built on prior exposure, with wording by mode. The
name-filled "who do you look after" checklist and the computed total are not built.

- **Independent checker: PASS.** It rebuilt every row from raw with 0 mismatches.
  On its points: "How many people do you care for?" is dropped, because it counts
  only people outside the household and its row couldn't say so. The "not asked"
  condition now quotes whichever question opens the respondent's own set. Two
  in-universe respondents coded −9 now count as asked.

**PLAN COMPLETE: 12 built, 4 dropped (9.43, 9.48, 9.12, 9.11), 0 to go.**

### What the waves are and are not doing for us

The waves are not a time dimension in these rows. An experiment that ran in two
waves simply yields twice the rows; `(persona, condition, outcome, response)`
says nothing about when, beyond the fieldwork year sitting in the persona. We are
mining the Innovation Panel for **experiments**, not for trajectories.

**One thing does carry across, and it should not be lost.**
`Recipe.participant_id_var` keeps one person's identifier stable across every
wave and every experiment, and the id is a hash of `pidp` matching
`scripts/build_profiles.py`. So once these sixteen are built, the same person
appears in several different experiments, years apart, under one id.

Why that is worth protecting:

- **SocSci210 structurally cannot do it.** Each of its 210 studies is a separate
  sample of different people. The Innovation Panel is roughly the same 2,500
  people answering experiment after experiment from 2008 to 2024, so this corpus
  can ask whether a person's behaviour in one experiment predicts their behaviour
  in another — a question the US reference dataset cannot pose at all.
- **It is the bridge back to the parked profile work** (§5). The same hashed id
  joins a row here to that person's profile there. Building the experiments now
  costs nothing extra and leaves the profile layer able to plug in later without
  rework.
- **It is free, and easy to lose.** The default is the row index, which makes the
  same person in two waves two unrelated participants. Every Innovation Panel
  recipe must set `participant_id_var: person`, and the generator must write the
  hash rather than `pidp`.

### What the triage script is and is not good for

It reported 9 PASS, 5 CHECK, 2 FAIL. **The passes are grounded and the failures
are worthless**, and that distinction is written into the script itself so nobody
later reads a FAIL as a finding.

A PASS means a named variable was located in a real data file — a positive fact.
A FAIL meant the script's own pattern-matching gave up, and it did that **six
times for six different reasons**, every one of them its fault rather than the
data's:

1. `\bff_` never matches inside `d_ff_fertw4`, because `_` is a word character.
2. Not every allocation variable is `ff_` prefixed — the flexibility-stigma ones
   are `fsvigname1`, `fsvigparent1` and so on.
3. Not every arm is written `1 = x`. Fertility context effects writes
   `Group 1  Version A (before friendship questions)`.
4. Taking the longest block under a heading picked a contents-table fragment
   instead of the real section.
5. `eq5dcond on record k_indresp_ip:` is the guide's other way of naming the
   controlling variable and was not matched.
6. `pdftotext` keeps the page margin, so the real heading is
   `" 9.24 Variations of the EQ-5D questions"` with a leading space, and `^`
   missed it.

The EQ-5D experiment still reports FAIL after all six fixes, and is completely
specified when read. **With sixteen short sections, reading them is more reliable
than another regex**, and that is how the table above was finished.

### Estimated effort

**1–2 hours per experiment** where the wording exists, extrapolated from one
build, so treat it as a range. The housework scenarios took a full session, but
most of that was one-off machinery now reusable:

- `Condition.template` — a factorial declared as a template plus dimensions,
  expanded on load. 480 arms from ~40 reviewable lines of YAML.
- `Recipe.participant_id_var` — one person keeps one id across waves.

Both are inert for every existing study (all 41 rebuilt, zero row-count
changes). The scenario studies at positions 1 and 2 need no new machinery.

**Batching.** The 16 are spread across waves, so the per-wave saving is smaller
than a cheapest-first list would have given — the cost of choosing on coverage
rather than convenience, and worth paying. The clusters that do exist: waves 8–9
carry sexual-identity measurement and successful ageing; waves 6–7 carry
self-assessed disability and time/risk preferences; wave 16 carries flexibility
stigma, mental health and the long-term future.

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

## 6. Groundwork already done — do not redo it

Everything here is finished and tested. It is listed because each one looks like
an open question until you check.

**The persona crosswalk is complete: nine fields, zero unmapped.**
`education` · `employment` · `region` · `social_grade` · `income` · `ethnicity` ·
`marital_status` · `housing_ownership` · `religion`. QC rule 14 reports no
persona-vocabulary warning anywhere in the corpus. The Innovation Panel's own 58
labels were added 9 Oct by `scripts/persona_ukhls.py`, which also cleared the
warning for `QQM5MC`, `EFXNLX` and both `35M5CV` builds — they had been carrying
it too.

Four decisions inside it that should not be reopened:

- **UK and US do not share a canonical for income or ethnicity.** Currency
  conversion was rejected on four grounds, decisively that converted bands do not
  nest — £10,000-£14,999 becomes roughly $13,000-$19,500 and straddles two US
  boundaries, so it cannot be a union of source categories.
- **Education follows the YouGov ladder seven UK studies already use.** A-levels
  and GCSEs both land on `High school`, degrees on `Bachelors to postgraduate`.
  Choosing differently for UKHLS would make its rows incomparable with what is
  already built.
- **`Northern Ireland` was added as a canonical region.** No earlier study
  sampled there; the Innovation Panel does.
- **Two coarsenings are deliberate**: civil-partnership dissolution states
  collapse to one value, and "Looking after family or home" goes to the residual
  `Other`. The raw `.sav` still holds both.

**QC rule 19 enforces the panel link.** A recipe whose `source` is
`innovation_panel` must declare `participant_id_var`, and it FAILS rather than
warns, because the loss is silent — row counts right, conditions right, every
other rule passing, and the wave-on-wave link simply gone.

**Jev is refused for UKDS and is not needed.** `jev.RESTRICTED` quotes EUL clause
4 and ends "Map UKDS allocation variables by hand", which is what was done. Jev's
real job is semantic — deciding that `2+ Races, Non-Hispanic` and `Multiracial`
are one concept — and the UKHLS labels are self-describing, carrying their own
census grouping in brackets. It remains the right tool on TESS and Harvard.

**The reusable machinery from the housework build:** `Condition.template` (a
factorial declared as a template plus its dimensions, expanded on load) and
`Recipe.participant_id_var`. Both verified inert for every existing study — all
41 rebuilt with zero row-count changes.

---

## 7. Standing constraints

- **Raw and processed data never enter git.** `data/raw/`, `data/profiles/` and
  `data/processed/*.parquet` are gitignored. `data/catalog/` is tracked.
- **Nothing UKDS-derived has left this machine.** `jev.RESTRICTED` refuses
  `source="ukds"`.
- **The repo has never been pushed.** 80+ commits ahead of `origin/main`.
  **The reason originally given here was wrong and is corrected.** It said the
  recipes carry questionnaire wording, which the EUL counts as part of the Data
  Collection, so a push would be a disclosure. Checking rather than assuming
  found that UKDS publish the Innovation Panel's User Guide AND its
  questionnaires themselves, at `doc.ukdataservice.ac.uk`, downloadable with no
  authentication (verified 9 Oct 2026 — User Guide 200/3.5 MB, wave 5 and 16
  questionnaires 200). Condition text transcribed from those PDFs is therefore
  already public, published by the rights holder by their own choice.

  What has NOT changed is the only thing that mattered: **no microdata is in
  git**, and none may ever be. `data/raw/`, `data/profiles/` and
  `data/processed/*.parquet` are gitignored, so a push would carry recipes,
  scripts and docs and no respondent's answers.

  So pushing is a decision about the TESS and Harvard material — most of which
  states no licence — and about whether this work should be public at all, not
  about the UKDS documentation. Still worth deciding deliberately; just not for
  the reason given before.
- **The questionnaire is the authority on stimulus wording**, not the data file's
  labels. In 9.10 the archived labels were not merely truncated but wrong — two
  opposite housework splits shared one label string.
