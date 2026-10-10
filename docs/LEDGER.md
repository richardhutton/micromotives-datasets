# Failure ledger

Project-wide rulings live in **`docs/CONVENTIONS.md`** — characters, source
authority, arm-text principle, scope. This file records what went *wrong*; that
one records what we *decided*.

One line per problem found, and what we did about it. The point is to separate
**one-off fixes** (patch this study) from **method fixes** (a rule that protects
every future study). Only the second kind compounds — if the pass rate isn't
climbing batch over batch, we're fixing symptoms.

When a method fix is added, **re-run it against every batch already done**. It's
automated, so it costs nothing and retroactively audits earlier work.

---

## Phase 0 — hand-built studies

### Audit of SocSci210 (4 studies, sampled from our own 202)

Done before building, to decide whether the "PULL 75 studies free" path was safe.

| Study | Numbers | Condition text | What was wrong |
|---|---|---|---|
| `7jt2f` | ✅ | ❌ | Biography factor **inverted** (arms 1–4 got the self-introduction; described as "only by the label"); labels for arms 2 and 3 **swapped** |
| `sd7cf` | ✅ | ⚠️ | Framing correct, but the distractor-position factor **dropped** — 12 conditions collapsed to 3 distinct strings |
| `zrwjp` | ✅ | ✅ | Clean. Minor: describes the wage as self-computed when it was auto-displayed |
| `c5r2f` | ✅ | ❌ | **All 12 arms given the wrong scenario** (one-block domain rotation) + a fabricated figure ("3%" vs the study's 5%) |
| `rpw4u` | ✅ | ❌ | ~15 experiments reduced to 2 conditions, each **merging all arms** and described only as "with wording varied" — the treatment is unstated |

**Numbers correct 5/5** (including a subtle option-order reversal in `rpw4u`, which
they got right). **Text materially wrong in 4/5.**

→ **Method decision:** do not reuse their stimulus text. Build every study from
source; use SocSci210 as a *numeric* answer key only. `crosscheck` therefore
asserts on numbers and reports text as informational.

→ **Caveat:** 5 studies, chosen for ease of checking, not at random. Enough to
justify "don't trust the text unchecked"; not enough to state a rate.

---

### Study 1 — `7jt2f` (2 × 4 vignette)

| # | Finding | Kind | Action |
|---|---|---|---|
| 1 | SocSci210's condition text is inverted for this study | one-off | Recipe follows the questionnaire; `notes` records the disagreement |
| 2 | Two conditions could render identical text and nothing would notice | **method** | QC rule: *distinct conditions must render distinct text* (`qc.py` rule 1) |
| 3 | A declared factor could be absent from the text entirely | **method** | QC rule: *each factor must vary the arm text* (`qc.py` rule 5) |
| 4 | Flat arm lists invite losing a second factor | **method** | `factors` are first-class on every arm and validated |

Outcome: **crosscheck PASS** — 3,053 rows, 8 cells, 7-bin distribution all exact.

---

### Study 2 — `rpw4u` (split-ballot / question-wording)

Chosen deliberately for a different shape. It broke the recipe format three ways.

| # | Finding | Kind | Action |
|---|---|---|---|
| 5 | One deposit holds **~15 independent experiments** (one per `DOV_*_Assign`) | **method** | One recipe file per sub-experiment; `experiment` field names it |
| 6 | Each arm is asked a **different variable** (`RO1a`..`RO1d`) — the question *is* the treatment | **method** | `Arm.outcome_var`; `Outcome.var` now optional |
| 7 | Response options are **reversed** in some arms — raw code `1` means opposite things | **method** | `Arm.response_recode` overrides the study map. Silently inverts half the answers if missed |
| 8 | SocSci210 reconstructed a *different scope* (2 merged conditions), so a numeric crosscheck is meaningless — neither side is buggy | **method** | `comparable_to_socsci210: false`; crosscheck reports SKIPPED rather than a false FAIL |

Outcome: **QC PASS**, 1,023 rows, 4 distinct conditions preserved. Merged response
distribution `{1: 778, 2: 245}` matches the correctly order-flipped merge.

**Consequence for the plan:** some of the 75 "verifiable" studies are not actually
verifiable, because SocSci210 built a narrower or merged version. We find out per
study; those drop to the same footing as the blind 120.

---

### Study 3 — `zrwjp` (2-arm, banded quantity outcomes)

Chosen as a simple 2-arm design. The design was simple; the **outcome coding** was not.

| # | Finding | Kind | Action |
|---|---|---|---|
| 9 | A study's outcomes can sit on **different scales** (banded dollars vs banded time) | **method** | `Outcome.response_recode`; resolution order is arm → outcome → study |
| 10 | QC rule 4 validated responses against the study-level recode only, so per-outcome recodes false-failed | **method** (bug in our code) | Rule 4 now unions study + outcome + arm recodes |
| 11 | **A study can span more than one parquet shard**; `find_shard` returned only the largest, silently truncating the reference data (915 of 1,263 rows) | **method** (bug in our code) | `find_shards` returns all; `fetch_socsci210` reads them all. `7jt2f` was single-shard, so its earlier PASS was genuine |
| 12 | Condition mapping is **reversed** here (condition_num 0 = Control = raw 2), and arm sizes 635/640 are too close for counts to settle it | one-off | Declared explicitly; fixed by content, not by counts. Reinforces finding #7 |

**Three numeric defects found in SocSci210 for this study** — each verified by
reproducing their distribution exactly:

| | Defect | Proof |
|---|---|---|
| a | **Wrong variable**: task 0 answers come from `Q10` ("how much do you *spend*") while the stimulus quotes `Q5` ("how much would it *cost*") | `Q10`'s `$0` band n=986 = their zero count exactly |
| b | **Comma-parsing bug**: `"$1,001-$2,500"` → `1`, not `1001` | their distribution reproduces only with band 16 → 1 |
| c | **Minutes conflated with hours**: `"1-4 minutes"` and `"1-3 hours"` both → `1`, under a stimulus reading "monthly hours saved" | exact match under the conflated map |

Outcome: **QC PASS**, 2,532 rows. Marked `comparable_to_socsci210: false` — we
deliberately disagree on both outcomes.

→ **Revises an earlier conclusion.** "Numbers correct 5/5" was wrong. The accurate
statement: SocSci210's **arm assignment and row structure** have been correct in every
study checked, but **response values are unreliable wherever a band→quantity
conversion is involved**. Plain ordinals and option-order flips were handled
correctly; all three conversions in this study were not.

→ **Consequence:** a crosscheck failure is a signal to *investigate*, not evidence
that we are wrong. Agreement is strong evidence both sides are right; disagreement
must be adjudicated against the questionnaire.

---

### Study 4 — `c5r2f` (3 × 2 × 2 factorial, 12 cells)

The most complex design so far, and the **first study that needed no new format
features** — the split-ballot support added for `rpw4u` covered it unchanged.

| # | Finding | Kind | Action |
|---|---|---|---|
| 13 | 12 cells, each with its own outcome variable `Cond_1..Cond_12` | — | Already handled by `Arm.outcome_var` |
| 14 | Three factors (domain × default × process) | — | Already handled by first-class `factors` |
| 15 | Our scope is narrower than theirs (primary DV only; they also built two blocks of follow-up items, 3 tasks / 4,375 rows) | one-off | `comparable_to_socsci210: false`, with the per-condition check done manually |

Outcome: **QC PASS**, 1,091 rows, 12 conditions. Per-condition counts on the primary
measure match SocSci210 **exactly, 12 for 12** — so their arm assignment is right and
our parse agrees with it.

Confirms the earlier audit: their stimulus text rotates the domains by one block (every
arm gets the wrong scenario), and their retirement text's "3% of earnings" appears
nowhere in the source — the questionnaire says **5% of net monthly salary**. Verified
by reading the `[SP; XTESS084 = n]` blocks directly.

**First signal on cost:** this study took materially less work than studies 2 and 3
despite being the most complex design, because the format already fitted. That is the
batching bet paying off — method fixes compounding.

---

### Study 5 — `QQM5MC` (Harvard Dataverse, UK YouGov sample) — **NOT BUILDABLE**

Chosen to test a different source (Dataverse rather than TESS/OSF), a different file
format (`.tab`), and to get our first genuinely **UK sample**. It produced the most
consequential finding of Phase 0 — by failing.

Sorace & Hobolt, "A Tale of Two Peoples: Motivated Reasoning after the Brexit
Referendum". CC0. 3,267 UK respondents, 4 arms (Control / Prime only / Info only /
Prime & Info).

| # | Finding | Kind | Action |
|---|---|---|---|
| 16 | **The deposit contains no questionnaire and no treatment text** — only Stata code, a log, and a de-labelled `.tab`. We know which arm each respondent was in, but not what they read | **method** | Study is blocked pending the paper. See the source-family note below |
| 17 | `.tab` files carry **no value labels**; labels live in the `.do` file (`lab define expgroup 1 "Prime only" ...`) | **method** | A delimited reader will need labels declared in the recipe, not read from the file |
| 18 | The arm indicator is **not a column** — it is implied by which suffixed variable is populated (`Q2A`/`Q2B`/`Q2C`/`Q2D`), recovered in Stata by `reshape long` | **method** | Needs a "derive the arm from which outcome variable is present" mode |

**The structural point, which changes sourcing strategy:**

| Source family | Contains | Arm text recoverable? |
|---|---|---|
| TESS / OSF (202 studies) | data + questionnaire + methodology report | **Yes** — demonstrated on 4 studies |
| Dataverse replication archives | analysis code, logs, de-labelled data | **Often not** — built to replicate the *analysis*, not the *instrument* |

The UK-native layer (master doc §5a) leans on Dataverse. This says that layer is
**more expensive per study than the TESS layer, not less** — the opposite of the
working assumption — because the instrument has to be recovered from the paper, or
the study dropped. Worth confirming across the other three confirmed UK Dataverse
studies before committing.

It also argues for preferring sources that deposit **instruments** — UKDS (which
supplies questionnaires) and the Innovation Panel — over replication archives.

Outcome: **no rows built.** Recorded as blocked rather than forced; writing arm text
we cannot evidence is exactly the failure we are trying not to repeat.

---

## Batch 1 — first pass with Jev

Five TESS studies fetched (`bf8p2`, `h6zk9`, `dh3nj`, `sd7cf`, `savkp`), all with data
and a questionnaire. Jev ran first-pass assignment-variable identification before any
recipe was written — the honest test, since these had not been built by hand.

| # | Finding | Kind | Action |
|---|---|---|---|
| 19 | macOS zips carry AppleDouble sidecars (`._name`, `__MACOSX/`) which were being classified as data and documentation, doubling the apparent file count | **method** | `_is_macos_sidecar` filter in `osf.py` |
| 20 | **A `Choice` is only as good as its option list.** A keyword allowlist excluded `CALARCO_VIGNETTE` (its label says "vignette", which was not a hint word), and Jev then picked a question-order variable **at 0.99** — a confident-wrong answer created entirely by the caller | **method** | Denylist, not allowlist; plus an explicit `NONE_OF_THESE` option so it can decline |
| 21 | The same mistake again, subtler: ranking candidates by fewest distinct values filled the list with low-cardinality **demographics** and pushed the 12-arm manipulation out | **method** | Offer every plausible variable (cap 60). Narrowing the options is the caller quietly making the decision it is asking the model to make |
| 22 | **Narrow option lists inflate confidence.** `h6zk9` scored 0.79 against ~10 options and **0.59** against ~44. Same question, same model | **method** | The calibration in `jev_calibration.py` used shortlists and is therefore optimistic. Re-measure with realistic option sets before setting a routing threshold |

After the fixes, `dh3nj` returns the correct `CALARCO_VIGNETTE` at 0.80 (flagged, not
auto-accepted) and `NONE_OF_THESE` is available as a real answer.

**Revises the Jev conclusion.** The earlier "13 of 19 auto-accept at 0.85 with zero
errors" was measured under artificially narrow choices. With honest option sets,
confidence drops and fewer answers clear the threshold. The realistic value looks less
like *auto-accept* and more like *a ranked shortlist that puts the right answer first* —
still worth having, since ranking 44 variables is the tedious part, but it does not
remove the human.

---


### Batch 1 results — 3 of 5 built

| Study | Design | Rows | Result |
|---|---|---|---|
| `sd7cf` | 3 x 4 framing x distractor position | 4,124 | ✅ crosscheck exact |
| `bf8p2` | 2 x 2 valence x social comparison | 1,998 | ✅ crosscheck exact |
| `dh3nj` | 2 x 3 x 2 vignette (status x drinking x warning) | 4,001 | ✅ crosscheck pass (permuted index) |
| `savkp` | 3 x 2 emotion x information (video stimuli) | — | ⚠️ their numbers do not reconcile |
| `h6zk9` | 2-arm income-feedback + economic games | — | ⚠️ needs per-respondent stimulus |

**First-pass build rate: 3/5 (60%).** Both non-builds are recorded rather than forced.

| # | Finding | Kind | Action |
|---|---|---|---|
| 23 | Arms can be asked **different questions on different scales** — `bf8p2`'s loss arms ask how DISAPPOINTED, its gain arms how SATISFIED | **method** | `Arm.outcome_question` and `Arm.scale`, completing the per-arm override set |
| 24 | Zips extract into a subfolder, so a recipe's `data_file` is often not at the study root | **method** | `mmds build` resolves the filename anywhere under `data/raw/<study_id>/` |
| 25 | **`condition_num` ordering is a convention, not a fact.** `dh3nj`'s per-condition counts are a *permutation* of SocSci210's — same cells, different numbering | **method** | Crosscheck now reports a permutation as a note rather than failing. A real disagreement changes the multiset of counts; a relabelling does not |
| 26 | `savkp`: SocSci210's responses span only **2-6** on items that are genuinely **1-7** in the source. With 4,564 responses, missing both endpoints is impossible — they applied some undocumented transformation | open | Flagged. Not built; would need their transform reverse-engineered, or build ours and mark not comparable |
| 27 | `h6zk9`: the stimulus is **personalised** — the feedback text depends on a computed per-respondent value ("you *overestimated* your position"), not just the randomised arm | open | Needs a per-respondent stimulus template; no format support yet |

**Cost signal.** `sd7cf`, `bf8p2` and `dh3nj` were each markedly quicker than the Phase 0
studies — the format now fits most designs, and `dh3nj`'s twelve arms were composed from
the questionnaire's own templated fragments rather than transcribed one by one. The two
that failed both failed for *source* reasons, not pipeline reasons.

---


## UK-transferability — two axes, not one

Prompted by a check on whether we are building studies that are actually useful
as a basis for UK work.

**A prior judgement already exists and is good.** `docs/archive/SocSci210_uk_filter.csv`
carries `uk_applicable`, `conf` and `note` per study, and the criterion was sound: the
drops are overwhelmingly US race and partisan politics (partisan stereotypes, Latino
policy attitudes, affective polarization, Congress, the 2020 election), and 17 studies
carry real reasoning — *"mechanism universal; US racial frame, borderline"*, *"name is
US, mechanism universal"*, *"dollar prices; convertible"*, *"has race dimension; keep
non-race arms"*.

| # | Finding | Kind | Action |
|---|---|---|---|
| 28 | That judgement **was not reaching the working catalog at all** — it sat in `archive/`, so nothing in the build process could see it | **method** | `uk_applicable`, `uk_conf`, `uk_note` merged into `data/catalog/tess_uk_foundation_sources.csv` (75 of 202 have one) |
| 29 | The judgement was made from **titles**, so it cannot catch a study whose title reads universal but whose *content* is US-specific. `sd7cf` — "Framing in Noisy Informational Environments" — scored `conf=1.0` with no note; its stimulus is the **Patriot Act** and its outcome is *support for the Patriot Act*, which a UK respondent cannot hold a view on | **method** | New `uk_content` axis, recorded when we open a study to write its recipe — which is free, because we are reading the questionnaire anyway |

**Two distinct axes, both needed:**

| Axis | Question | Source |
|---|---|---|
| `uk_applicable` | Could this design be run in the UK at all? | title-level, pre-existing |
| `uk_content` | Does the stimulus or outcome require US-specific knowledge? | content-level, recorded at build time |

`full` = no country-specific institutions. `mechanism-only` = the effect transfers but
the stimulus or outcome is US-specific.

Of the 9 studies opened so far: **7 `full`, 2 `mechanism-only`** (`sd7cf` Patriot Act,
`rpw4u` US oil/courts items). 193 still unassessed at content level.

**Not dropping the `mechanism-only` ones.** The paper's own finding is that training on
more studies improves generalisation to unseen ones, so a framing effect learned on the
Patriot Act may still teach the model how framing works. Tagging them means we can hold
them out and *measure* whether they help, instead of guessing either way.

Also worth noting: a US **sample** is unavoidable across all 202 and is a separate
concern from US **content**. Only the latter varies.

---


## Maker/checker trial — and a hard limit on data-only screening

First maker agent drafted a recipe for `a5v96` (McLaughlin, clinical decision support),
a study nobody had built, so there was nothing to copy.

| # | Finding | Kind | Action |
|---|---|---|---|
| 30 | **A variable labelled "Experimental condition" can be presentation order.** `a5v96`'s `XTESS193` is labelled exactly that; its values are *"Vignette1 followed by Vignette2"*. The real manipulations (`Vignette1`, 10 arms; `Vignette2`, 12 arms) are labelled merely *"Data Only Variable"* with opaque values *"Vignette 1-1"…* | **method** | The label heuristic is not safe. Only the questionnaire resolves it |
| 31 | **Jev picked the order variable at confidence 1.00** — a confident-wrong answer on a fresh study. Adding value labels to the prompt did **not** fix it, because the true manipulation's value labels are meaningless codes while the order variable's read like a real design | **limit, not a bug** | `jev_firstpass` is demoted to a hint, not a gate. Data-only screening has a ceiling |
| 32 | The maker agent got it right, because it read the questionnaire and found the randomisation note | — | Confirms the architecture: extraction needs an agent, not a typed judgment |

**This revises the Jev assessment for the third time, and each revision has been in the
same direction: its value is narrower than it first appears, and the wrapper matters
more than the model.**

- Measured 84% with narrow option lists → optimistic, because narrow choices inflate confidence.
- Widened options → confidence fell, accuracy held.
- Fresh study with a misleading label → **wrong at 1.00**, and unfixable by sending more metadata.

Standing conclusion: use it to **rank and flag**, never to decide. The three times it
looked wrong, twice it was our option list and once it was a genuine limit of the input
we can give it.

### What the maker produced

`a5v96`: QC PASS, 3,621 rows, 10 conditions, 3 outcomes. It also:
- spotted the deposit holds **two independent experiments** (10-arm and 12-arm vignettes,
  separately randomised) and built one, flagging the other as owed;
- verified its own arm text **byte-for-byte** against the questionnaire, keeping a
  source typo ("make sure that that he is right") rather than tidying it;
- marked the study not-comparable and then **proved** the difference rather than
  asserting it — reproducing SocSci210's merge exactly, all 7 conditions and the full
  response distribution digit-for-digit, showing they merged both experiments and
  dropped two of the three factors;
- listed six specific uncertainties for the checker.

---


### Maker #2 — `z358z`, and a schema gap it could not work around

| # | Finding | Kind | Action |
|---|---|---|---|
| 33 | **A factorial design can be randomised through one variable per factor**, with no combined assignment code anywhere in the file. `z358z` holds scenario in `XTESS175` and consent alternative in `DOV_OPTION`, fully crossed (503/558/546/523). `Condition` assumed a single `source_var`, so the consent factor could not be expressed at all | **method** | `Condition.source_vars` (several variables that jointly define the arm) + `Arm.raw_values`. Single-variable recipes are unchanged; all seven existing ones still build |

The maker handled the gap the right way: it built the factor it could express, **documented
the loss at length rather than hiding it**, and — crucially — **omitted the paragraph that
varies by the factor it could not express**, rather than guessing at it. It also kept
`comparable_to_socsci210: true` deliberately so the disagreement stayed visible, accepting
a FAIL over a silent skip.

Its numbers independently confirm the build: `n_rows` 10,445, participants 2,096 and the
full response distribution all match SocSci210 **exactly**; only the condition index
differs, and it decomposes precisely (their 0+1 = our 0, their 2+3 = our 1).

It also found that **SocSci210's four conditions render only two distinct stimulus
strings** — they kept the four-way index but dropped the consent factor from the text.
Our QC rule 1 would fail that. Same defect class as `sd7cf`.

**Maker/checker verdict so far:** two agents, two studies nobody had built, both producing
QC-clean recipes with word-for-word-checked arm text, explicit uncertainty lists, and numeric
evidence for every claim of disagreement. One caught a mislabelled order variable that
fooled Jev at confidence 1.00; the other found a schema limitation and refused to fabricate
around it. This is the strongest argument yet that the ~188 remaining studies are tractable.

---

### Checkers — the maker/checker loop closed

Both drafts were then reviewed by a second agent, working from source and told to assume
at least one error. Verdicts: `z358z` **accept, superseded by the 4-arm rebuild**;
`a5v96` **accept with fixes** (all in the audit trail, none in the data).

| # | Finding | Kind | Action |
|---|---|---|---|
| 34 | **QC rule 5 never tested anything.** Meant to enforce "each declared factor must vary the arm text", its final test failed only when *every* arm rendered identically — which rule 1 already catches. Proved by injecting a factor (`doctor_hair_colour`) present in no arm text at all: **PASS**. Vacuous on all eight studies built to date | **method** (bug in our code) | Replaced with a **minimal-pair** test: for each factor, arms differing in that factor *and nothing else* must render different text. A factor with no minimal pair is **nested, not crossed** (heed-vs-defy is undefined with no computer) and now warns "could not be tested" rather than passing silently or failing wrongly. Re-run against all 10 recipes: **all PASS** — the vacuous rule was not hiding a real defect; we simply had not been checking |
| 35 | **A TESS deposit's proposal PDF and its fielded questionnaire are different instruments.** SocSci210's `z358z` stimulus uses the proposal's `CTD`/`HCTZ` wording; `hydrochlorothiazide` appears **0 times** in the fielded questionnaire, which says "CTD and TRT (we have changed the names but they refer to real drugs)". No respondent saw their text | **method** | **Arm text comes from the questionnaire, never from the proposal or paper appendix**, even when the appendix reprints what looks like the stimulus. The PDF remains a legitimate second authority on *arm ordering* — it resolved the `Xtess193=1.3` typo in `a5v96` decisively |
| 36 | `_write_parquet` keyed output on `study_id` alone, ignoring `experiment`, so a second sub-experiment of one deposit would **silently overwrite the first**. Latent until `a5v96` became the first deposit with two experiments both meant to be built | **method** (bug in our code) | Output stem is now `<study_id>_<experiment>` when `experiment` is set |
| 37 | `mmds crosscheck` ignored `comparable_to_socsci210` while `mmds build --crosscheck` honoured it, so a study deliberately marked not-comparable reported a **false FAIL** and exited 1 | **method** (bug in our code) | Both paths now skip and exit 0 |
| 38 | `z358z` rebuilt to 4 arms on the extended schema: crosscheck **PASS on all four condition indices** (2426/2728/2697/2594, exact and in order) plus `n_rows`, participants and the full response distribution. The `DOV_OPTION` paragraph the maker had omitted **did exist** in the questionnaire and is restored word-for-word | one-off, resolved | `recipes/z358z.yaml`; first study to exercise `source_vars`/`raw_values` end to end |

| 39 | **Rule 9 — "is there a second randomisation you didn't declare?"** Built, in `pipeline/screen.py`, called from `cmd_build`; it warns and never blocks. Anchored on the recipe's own declared assignment variable, it flags any other column that looks randomised (name/label pattern), is ≥95% non-null, has 2–12 balanced levels, and crosses the declared key with no empty cell and balanced cells | **method** | Measured on the real recipes: **0 suspects on all 9**, and on `z358z` rolled back to its pre-discovery single-variable state, **exactly 1, naming exactly `DOV_OPTION`**. `rpw4u_RO1`'s 6 hits are true positives of a different class (its other sub-experiments) and are now silenced by `condition.considered_and_rejected`, which records the reason rather than leaving the judgment implicit. Makes finding #33 mechanical instead of dependent on an agent noticing |

The anchoring is what makes it usable. An unanchored sweep for randomisation-looking
variables across the corpus returns over a thousand hits, dominated by item-order
variables; requiring full, balanced crossing against the *declared* key cuts that to zero
on a correct recipe.

---

### Makers, batch of five — findings so far

All five reported. Every draft builds QC-clean; the numbers below were re-derived here
rather than taken from the agents' reports.

| # | Finding | Kind | Action |
|---|---|---|---|
| 40 | **Rule 10 — every arm must be measured about as thoroughly as its peers.** Found on `9263n`, where six of seven items are asked with a different variable per branch (`Q3A` for the experiential arms, `Q3B` for the material ones). Declaring only the A variants halves the corpus and leaves arms 2 and 3 with **one item out of seven** — and QC passed with no warnings. Confirmed by building it that way: 6,328 rows to 3,188, arms 2 and 3 down to 189 and 219 rows, verdict PASS | **method** | Counting per OUTCOME would warn on every legitimately branched item (12 of 14 here) and train us to ignore the column, so the rule counts per ARM: silent when branching is symmetric, loud when it is not. Verified on both builds — no warning on the correct one, naming exactly arms 2 and 3 on the broken one |
| 41 | **A within-subject repeated-measures design randomises the arm PER ITEM, not per respondent.** `b87sm`: each respondent read **eight** vignettes drawn without replacement from a 72-cell universe, slot k assigned by `P_S{k}`. `Condition` resolves one arm per respondent row, so 7/8 of the study's vignette observations are unreachable. A new shape, distinct from #5 (several independent experiments) and #33 (factorial split across variables) | **method**, open | Needs either per-(arm, outcome) assignment — the same gap open for `z358z` Q1/Q2 — or a "long" mode where one respondent row yields several rows with different arms. Slot 1 built (5,769 rows); slots 2–8 owed |
| 42 | **Rule 9 is structurally blind to that shape**, verified empirically: it returns nothing for `P_S2..P_S8` for three independent reasons — names do not match its pattern, labels ("PRELOAD VARIABLE: P_S2") carry no keyword, and 72 levels exceeds `MAX_LEVELS`; and past all three, a 72-level anchor guarantees an empty crosstab cell | **method** | **Rule 11 — numbered siblings of the declared assignment variable.** `P_S1` -> `P_S2..P_S8`, `Vignette1` -> `Vignette2`. Needs no balance, crossing or level-count machinery. Measured across all 13 recipes and drafts: **zero false positives**, true positives on exactly the two studies with observations left on the table |
| 43 | **A deposit's stimulus text can live in a spreadsheet, not the questionnaire.** `b87sm`'s questionnaire contains no arm text at all — only `[INSERT P_S1]` and "(See excel table for look up)". The 72 vignettes are in `Independent Variables Map.xlsx`, referenced by the instrument and therefore part of it | **method** | Source triage must check for a lookup/map spreadsheet the questionnaire points to. A step that reads only `.txt`/`.docx` would conclude the text is unrecoverable |
| 44 | **Third instance of #35**, with a mechanical fingerprint: SocSci210's `b87sm` text contains "you should leave the research app installed", which occurs in the proposal and **0 times** in the fielded instrument (which reads "you would be asked to leave"). Their 8 conditions render **2 distinct strings**, so 71 of 72 arms are described wrongly, and they kept code 98 "SKIPPED ON WEB" as a response value | one-off + **method** | A phrase present in the proposal and absent from the questionnaire is a cheap, automatable provenance check |
| 45 | **`task_num` in SocSci210 is not a question key.** Their `9263n` task 6 holds two genuinely different questions (bad–good and sad–happy mood) under one index | **method** | When reconciling scope, read their `prompt` per `task_num` rather than subset-summing row counts — the maker reports that subset-sum returned **342** candidate subsets for one row total, while one `min(prompt) GROUP BY task_num` query identified all seven items at once |
| 46 | First audited study where SocSci210's stimulus text is substantively **correct** — `9263n` is faithful, all arms distinct, no factor dropped (abridged, and one tense changed from "is" to "was") | context | Their text failures are frequent, not universal. Worth recording so the sample stays honest |

| 47 | **"Reversed on screen" is not "reversed in the data" — and `rpw4u` is not the general case.** `evnyh` manipulates response-scale direction; the options were displayed in reverse sequence but the stored codes stayed **label-anchored**, so applying an `Arm.response_recode` would have silently inverted half the answers. The same failure as #7, from the opposite action | **method** | Discriminating test, cheap and mechanical: **if one data column serves several arms of the order factor and carries one value-label set, the coding is label-anchored.** `Q1A_1` is labelled "(Groups 4 + 10)" — one column, both directions, one label set. Proven four ways, including correlating each item against its unmanipulated day-count counterpart: r ≈ −0.77 in *both* direction arms, where a positional coding would flip the sign |
| 48 | SocSci210 **introduced a reversal that was not there, and attached it to the wrong factor.** Their `evnyh` direction wording tracks *alignment* (vertical/horizontal), which is orthogonal to direction. Their 12 conditions render only **7 distinct strings**, so the direction factor is absent from the text. Two of their six cell maps collapse five ordinal levels to three, and one emits `0` against their own declared 1–5 scale | one-off | Our rule 1 fails the identical-text shape, rule 8 the collapse, rule 4 the out-of-scale value. Recovered by matching their counts against raw distributions, consistent across all ten items |
| 49 | **A deposit's proposal can describe a SMALLER DESIGN than the one fielded**, so SocSci210's *condition count* can be wrong — not just its text. `cug34`'s proposal says "12 (2 x 2 x 3)" and holds duration constant; the fielded instrument randomised a **fourth** factor (`DOV_RELDUR`, 2,014 / 2,006) and has **24** blocks. Their 12 stimulus strings all say "for three years", which is false for the 2,006 respondents who read "7 years" | **method** | Extends #35 and #49 is the sharper form: the proposal is unreliable even on arm *count*. Mechanically checkable — reconcile the answer key's condition count against the assignment variable's cardinality. Here `XTESS217` has 24 values and the key said 12; that gap is the tell |
| 50 | **The `outcome.var or arm.outcome_var` resolution is a SUM, not a PRODUCT.** One variable per outcome, or one per arm — never one per (arm, outcome) pair. Now the single largest source of unbuilt rows: it costs `evnyh` **nine of ten** experimental items (~15,400 rows), `cug34`'s B02/B03 and its four insert-bearing items, and `z358z`'s two primary outcomes | **method**, open | Proposed `Arm.outcome_vars: {task_num: var}`, resolved before `outcome.var`. No change to any existing recipe |
| 51 | **The questionnaire can specify a vignette combinatorially rather than as written blocks.** `zaqkm`'s 40 arms are 5 first paragraphs × 8 second-paragraph blocks, each branching again on `[SHOW IF DOV_MENTALHEALTH=2: alcohol use disorder ...]`. Three of the last four studies (`dh3nj`, `z358z`, `zaqkm`) assembled arms from templated fragments, and each agent wrote its own throwaway parser | **method**, open | A shared `sources/quex.py` resolving `[SHOW IF VAR=n: ...]` / `[ALL ELSE ...]` / inline switches would make arm text **derived** rather than transcribed, and turn the hardest study in the batch into a routine one |
| 52 | **Cross-file agreement is a free, strong verification primitive.** TESS deposits ship *simple* and *prog* questionnaires. `zaqkm`'s maker derived all 40 arms from **both** independently and asserted equality — which caught two real bugs in its own parser (an unbounded last block; a `</i>`-before-full-stop divergence) before either reached the YAML | **method** | Standard step wherever both files exist |
| 53 | **Continuous / quantity outcomes are inexpressible.** `response_recode` is a finite explicit map and rules 7–8 assume bands, so `cug34`'s dollar boxes (0–2,800) would need ~2,800 entries. SocSci210 built exactly those 7,138 answers, so this is real training signal we cannot currently emit | **method**, open | Proposed `Outcome.numeric: {min, max}` passthrough |
| 54 | **`persona_map` has no missing-code handling.** Panel sentinels (`XIDEO=9 "MISSING"`, `XREL1=14 "MISSING"`) resolve to the literal word "MISSING" in persona text, and a recipe author's only mitigation is to drop the field. `evnyh` dropped ideology and religion to protect 37 rows | **method**, open | Proposed `persona_missing: {VAR: [codes]}`, or a global drop-list of sentinel labels. Raises coverage on every KnowledgePanel study — see the persona-coverage section |
| 55 | **Proposed, not built: "arm text must not come from the proposal."** Warn when a long n-gram of a recipe's arm text appears in the deposit's proposal PDF but **not** in the questionnaire. Independently proposed by three of the five makers | **method**, open | Mechanises #35/#44. Would have auto-caught SocSci210 on `z358z`, `zaqkm` and `b87sm`. `zaqkm`'s maker already ran it by hand as five assertions, all passing |
| 56 | **Proposed, not built: factorial completeness.** Assert `len(arms) == product(level counts)` and that every cell is non-empty in the data. At 40 arms a dropped or duplicated cell is invisible by eye | **method**, open | One line; `zaqkm` (5×4×2 = 40) is the case that motivates it |

Both `9263n` and `zaqkm` reproduce SocSci210 exactly: `9263n` **PASS on all four numeric
fields** (6,328 rows, conditions 1685/1447/1479/1717 in their order, the whole 10-bin
distribution), independently re-derived here. `b87sm` is not comparable — their 8
"conditions" are the eight presentation *slots*, not the manipulation — but the maker
reproduced their full response distribution digit-for-digit under that reading, including
the 198 retained code-98 non-responses.

---

### Testing the tests

Rule 5 was dead for eight studies and we found it **by luck** — a checker probing an
unrelated uncertainty. Nothing in the suite would have told us. That is a worse problem
than the rule itself: it means "QC PASS" was a weaker claim than we had been making, and
we had no way to know which other rules were hollow.

So every rule now has a **mutation test**: a minimal break of an otherwise-clean study,
asserting that rule's *own* message. Asserting only `not rep.passed` is exactly what let
rule 5 hide — the crude mutation tripped rule 1 as well, so the suite stayed green while
rule 5 checked nothing.

Verified by restoring the vacuous rule 5 and re-running: **3 tests go red.** The suite now
catches the bug we actually shipped.

Also pinned, because each was a live trap:
- a clean study must raise **no warnings either**, not merely pass — a rule that cries
  wolf trains us to ignore the warning column;
- rule 7 must **not** fire on a legitimately reverse-coded scale, only on a mixed
  direction;
- rule 5 must catch an unexpressed factor in an arm with **no rows**, where rule 1 is
  structurally blind (it reads built rows; rule 5 reads the recipe). That case is the one
  that justifies keeping both rules.

63 tests.

**What the checkers cost:** ~10 minutes of review each. Between them: one method-level
defect in our own QC, two latent pipeline bugs, a rule about which source document to
trust, and a four-way crosscheck PASS the maker alone could not reach. Maker-only would
have shipped two good recipes and left rule 5 vacuous indefinitely.

---

### SocSci210's persona coverage — measured, not assumed

Their `demographic` field is a fixed 16-key dict, harmonised across TESS's **two** panel
families (KnowledgePanel `PP*`, 44 of our 73 fetched studies; AmeriSpeak
`AGE`/`EDUC`/`RACETHNICITY`, 29). So the crosswalk problem is real but small — two lookup
tables, not one per study.

They did not finish it. Fill rates over whole studies, not samples:

| Studies | Family | Fields populated (of 16) |
|---|---|---|
| `7jt2f`, `zrwjp`, `c5r2f`, `sd7cf` | KnowledgePanel | **6 / 16** |
| `dh3nj`, `m52pd`, `xweq8` | AmeriSpeak | 14–15 / 16 |
| `bf8p2` | AmeriSpeak | **1 / 16** |

The KnowledgePanel studies are null on `gender`, `employment`, `location`, `ideology`,
`party_id`, `housing_ownership`, `housing_type`, `internet_access`, `metro_status` and
`phone_service` — and all seven of those checked **exist in the source `.sav`**
(`PPGENDER`, `PPWORK`, `PPSTATEN`, `PPRENT`, `PPHOUSE`, `PPNET`, `PPMSACAT`). Gender is
null on every KnowledgePanel study.

→ Same shape as the stimulus-text finding: their **structure** is sound, their
**filling-in** is not. Our crosswalk (§6) should aim to beat their coverage, not match it.

---

### The persona crosswalk — findings 57-63

Built after the five-study batch, to make the corpus mergeable. The corpus is
now harmonised on four fields: income 17 bands (was 19 vs 18), education 4
levels (4 vs 5), ethnicity 5 categories (5 vs 6), employment 7 (7 vs 9 vs 2).

| # | Finding | Kind | Action |
|---|---|---|---|
| 57 | **Recording a numbered sibling in `considered_and_rejected` un-silenced rule 9 on its component columns**, because rule 9 took its suppression list from `find_numbered_siblings`, which strips rejected variables. Doing the right thing took `b87sm` from 5 warnings to 40 | **method** (bug in our code) | Rule 9 suppresses on the sibling FAMILY via `_sibling_family`. General form: *a suppression mechanism must not be derived from a reporting mechanism that the suppression itself feeds* |
| 58 | **`Arm.scale` leaked onto outcomes that name their own `var`.** `evnyh` rendered "return an integer from 1 to 5" on 16,824 rows whose responses ran 0-7, direction inverted — **8,774 rows, 47.3% of that study**, carrying an instruction their own response contradicts. QC passed with ZERO warnings. Cause was our own inconsistency: `outcome_var_for` prefers the outcome, `outcome_text_for` preferred the arm | **method** (bug in our code) | `Recipe.scale_for`, shared by the melt and rule 13 so they cannot drift. `evnyh` was the only recipe triggering it; 0 offending rows across all 14 |
| 59 | **Rule 13** — a response must lie inside the scale its OWN rendered text states. Rule 4 checks the union of declared recodes and is structurally blind, since every one of those 0-7 values IS in some declared recode | **method** | Proved by restoring the buggy precedence: rule 13 fails, naming the (condition, task) pairs |
| 60 | **Rule 12** — no persona field may render a non-answer label. 6 of 14 recipes were putting panel boilerplate into personas, 930 rows; `b87sm` shipped 93 rows of `religion: "SKIPPED ON WEB"` under a 335-line notes block that never mentioned persona | **method** | Two escape hatches for two causes: `persona_missing` drops sentinels carrying no answer; `persona_label_rewrite` cleans `cug34`'s 685 rows of "Other Christian religion, please specify" — a real answer wearing an interviewer instruction, which dropping would discard |
| 61 | **Three studies had NO persona at all** — `rpw4u`, `sd7cf`, `zrwjp`, 33 mapped fields, 7,679 rows — because the recipes said `ppincimp` and the files say `PPINCIMP`, and the lookup was case-sensitive and skipped in silence. Persona is one of the four parts of the tuple. Three of our own early recipes, wrong since written | **method** (bug in our code) | Case-insensitive resolution (SPSS names *are* case-insensitive), and a mapped variable absent from the data is now a HARD ERROR. Coverage on the ten core fields went 90.4% -> 100% |
| 62 | **`participant_id` was a per-study row index**, so on merge 23,464 respondents collapsed into 4,010 ids and "person 0" existed in all 14 studies as 14 different people | **method** (bug in our code) | Namespaced `<study_id>:<idx>`; `experiment` added to `Row` and `anchor()` too, because a deposit's sub-experiments are answered by the SAME people |
| 63 | **Rule 14** — persona values must be in the canonical vocabulary. An unmapped label passes through UNCHANGED rather than being blanked, because silently thinning the corpus as new schemes arrive is the failure this layer exists to prevent | **method** | Caught finding #64 within minutes of existing |

**The pattern across 57-63:** every one was invisible per study — each recipe
built, passed QC and crosschecked — and obvious the moment the corpus was
merged and *looked at*. Building the artifact found in minutes what fourteen
clean builds had not.

### Crosswalk design: three wrong sources before the right one

| # | Finding | Kind |
|---|---|---|
| 64 | Derived the crosswalk from the variable **Jev picked**. But a recipe renders whatever variable IT declared, which can be a coarser sibling: the classifier prefers fine-grained `PPEDUC` while the recipes map 4-level `PPEDUCAT`, so education's crosswalk covered labels the corpus never contains | **method** (our error) |
| 65 | Then derived it from the **built corpus**, which looks right and is worse — circular. Once applied, the corpus holds harmonised labels, so the second run reads its own output back as input | **method** (our error) |
| 66 | Then filtered to value labels **observed in each sample**. `zrwjp`'s respondents are all in work, so it looked like a 2-category employment scheme, which forced every other study's retired/disabled/unemployed distinctions to collapse — 7 categories down to 3. **A scheme's categories are what the questionnaire OFFERED; absence in a sample is not absence from the scheme** | **method** (our error) |

Correct source: the variable each **recipe declares**, read raw from the `.sav`.

**Education needed the ORDINAL path, not the categorical one.** "Bachelor's degree
or higher" is not a concept some schemes lack, it is a merge of adjacent rungs —
so it routes through the band arithmetic. Pointing `categories.py` at it made the
field unreconcilable, which was our error and not a fact about the data.

**The granularity tiebreak misfired three times**, always by preferring a
*different construct* that happened to be finer: `zrwjp`'s personal earnings over
household income, and `ppcm0160` "Occupation (detailed)" over `PPWORK` "Current
Employment Status" on two studies. Window narrowed from 0.10 to 0.03 (0.05 is the
widest that still resolves every known answer), and picks decided by the tiebreak
rather than by the score are now flagged for review. The real fix — asking Jev
whether two candidates measure the same construct — is not built.

### What Jev is for, settled

rich pushed back on hand-coding the crosswalk with regex plus arithmetic, on the
grounds that there would be a lot of edge cases. Measuring it settled it against
us twice: there are **8** income band schemes across the fetched studies, not the
2 visible in the built ones; and our own regex offered six **vignette** variables
about a fictional character ("her family depends on her income") as income
columns. The pattern could not even identify the right variable.

So the division is: **Jev answers "what is this variable" and "what does this
label mean"; code answers "do these bands tile".** Measured — 785 candidate
columns across four fields, **327 rejected** by Jev; 14/14 on the studies whose
income variable we already knew; and all six `py9q3` vignette variables scored
0.02 against 0.85 for the real one.

---

## Where the batch leaves us

14 recipes (9 committed, 5 drafts awaiting checkers), **80,010 rows**, all QC PASS.

**Verification state, stated plainly:**

| | Count |
|---|---|
| Numeric answer key from SocSci210, passing | 7 — `7jt2f`, `bf8p2`, `dh3nj`, `sd7cf`, `z358z`, `9263n`, `zaqkm` |
| No usable key (they built a different scope) | 7 |
| Independent read of the questionnaire by a second party | 2 — `a5v96`, `z358z` |

So the five new drafts are maker-verified but not yet checked. On the two studies
that have been through the full loop, the checkers found one method-level defect in
our own QC, two latent pipeline bugs, and a four-way crosscheck PASS the maker alone
could not reach — so the remaining five checker runs are the next real step, and
they give the n=7 defect-rate measurement that would license scaling.

**What the batch cost:** five agents, roughly 15 minutes of wall-clock each in
parallel, ~10 minutes of review each. Against the 30–60 min/study hand estimate, and
with materially better evidence than hand-building produced.

**What the batch bought, beyond five studies:** rules 10 and 11, two measured fixes
to rule 9, and nine method-level findings. The pattern to note is that every rule in
this ledger was found by a study breaking it — not by design. Rules 9 and 11 both
came from a study the previous rule was blind to, one batch apart.

---

## Open items

- Only `RO1` of `rpw4u`'s ~15 experiments is built. The rest are mechanical repeats.
- `a5v96` vignette 2 (12-arm combat-medic triage) is owed — the deposit's second
  experiment, deliberately out of scope for `a5v96_vignette1.yaml`.
- `z358z` Q1/Q2, the study's **primary** outcomes (4-point written-consent-vs-alternative).
  SocSci210 did not build them either. Now expressible, but `Arm.outcome_var` holds one
  variable per arm and these are two items per arm — needs a per-(arm, outcome) override
  or a second recipe.
- Rule 9's thresholds (12 levels, 95% coverage, 0.70 balance) and rule 10's 0.5 ratio
  are set from a handful of recipes. Expect to revisit once a batch has run through them.
- `b87sm` slots 2-8 owed (finding #41) — blocked on per-item arm assignment, the same
  schema gap as `z358z` Q1/Q2.
- Automate the proposal-vs-questionnaire phrase check (findings #44, #55).
- **Character sweep owed on `zaqkm`**: 114 curly apostrophes in arm text, against
  the ruling now in `docs/CONVENTIONS.md`. One file. The other 13 recipes already
  comply, having straightened quotes before anyone decided to. Held until its
  checker reports, to avoid editing a file under review.
- Persona categories are still passed through raw (`Education: Bachelor's degree or
  higher`). The crosswalk to one shared vocabulary (master doc §6) is unbuilt — two
  panel lookup tables plus UK re-anchoring, per the coverage finding above.
- `.doc` conversion uses macOS `textutil`; needs `antiword`/LibreOffice elsewhere.
  Arm text is committed into the recipe, so the melt and its tests stay unaffected.

---

## Round 7 — the per-(arm, outcome) schema gap, findings 67-70

| # | Finding | Kind |
|---|---|---|
| 67 | **Four studies already "built, checked and crosschecked" were each missing most of their rows**, all for one cause: the schema could describe arms that ARE items and arms crossed with nothing, but not arms crossed with items. 40,296 rows — a third of the eventual corpus — sat unreachable behind it, and every recipe said so in its own `notes`. **A documented debt stops being visible the moment it is documented.** The four recipes recorded the gap when written and it was still there studies later; the thing that moved it was counting the rows it cost | **method** |
| 68 | **A suppression derived from "things we have not dealt with yet" is removed by every way of dealing with them.** Ledger #52 was: recording `P_S2..P_S8` in `considered_and_rejected` emptied the sibling list and un-silenced their 40 component columns, 5 warnings to 40. This round: **declaring** them as per-item assignment emptied it the same way, for the same reason. The fix both times is the same shape — derive the suppression from the DECLARED set, which no act of declaring can empty. Found because a maker worked around it with 40 lines of recipe and said so | **method** (our error, twice) |
| 69 | **A row cannot cite its own position in a sequence.** `b87sm` carried "Please read Scenario #1 carefully." in `shared_context`, so 13,513 of 19,282 rows (70.1%) told the respondent they were reading scenario 1 while rating scenario 2-8. Nothing caught it: 72 arms still rendered 72 distinct strings (rules 1 and 5 satisfied), arm text matched the source byte-for-byte, row counts reconciled exactly, and an exhaustive independent recomputation of all 19,282 rows' arm assignment found zero errors. **A checker found it by reading one rendered row and asking what it said.** Now QC rule 15, numbered references only — "the following scenario" points inside the row and is correct | **method** |
| 70 | **"Presumably" in a verification note is a guess wearing a finding's clothes.** `cug34` explained 5 rows where Shared + Individual ≠ TOTAL as "presumably client-side rounding/validation slips". A checker identified all 5 exactly: each is a refusal (-1) with TOTAL still showing the cap. No arithmetic involved. Harmless here because TOTAL is not built — but the sentence read as checked when it was not. Related: `z358z`'s option-order proof was cited to the `.sav`, whose value labels are generic (`{1: 'Definitely', 2: 'Probably', ...}`) and cannot settle direction; the real authority is the questionnaire's grid column headers. A correct claim resting on an unstated source is one revision from looking like an assumption | **method** |

**What maker/checker is now worth, measured.** n=11 through the full loop. Defects
found in built data: **one** (#69), in 70% of one study's rows, by a checker
reading a row rather than running a check. Everything else the checkers found was
documentation. Two makers flagged their own riskiest judgement before being asked,
and one of those flags is what exposed #68.

---

## Round 8 — wave 1 of the 20% push, findings 71-75

| # | Finding | Kind |
|---|---|---|
| 71 | **Four of five studies in one wave had been built NARROWER by SocSci210 than what was fielded**, each differently: `a2nbf` collapsed a 2x2 to one factor (our 4 cells sum to their 2 exactly), `a42yg` dropped the self-affirmation factor from its stimulus text entirely (4 conditions rendering 2 strings — our own rule 1 would fail it), `yv2ta` merged two independent experiments into one condition index with four empty slots, `8ctbk` used pair POSITION as `condition_num` rather than profile identity. The ratio is no longer a surprise and should be treated as the base rate: **assume the reference reconstruction is a lower bound on the design** | **method** |
| 72 | **A `Noul` is not a magnitude, and we had been averaging two of them.** `uk_priority.py` asked `uk_relevance` and `evergreen` as `Noul`s and ranked 59 studies by `relevance + 0.15 * evergreen`. The primitive docs: *"A Noul value of 0.5 means the model gives yes and no equal probability. It does not mean the candidate has a medium skill level."* Re-asked as `Score` with five written-out levels, the values visibly discriminate where they had not: evergreen now spreads 0.39-3.88 against a tight high cluster, a 2002 smallpox-vaccine study correctly collapsing to 0.39. **The lesson is not "read the docs" but that a wrong primitive returns a number that looks perfectly usable** — nothing in the output said anything was wrong | **method** (our error) |
| 73 | **A rule that cannot distinguish design from defect on a class of design should decline, not guess.** The first conjoint (`8ctbk`, 1,146 profiles x 10 task slots) made rule 10 fire on nearly every arm: a profile drawn four times cannot span more than four of ten. Both obvious repairs fail — counting per (participant, arm) silences `8ctbk` but then fires on `b87sm`, where slot 1 legitimately carries 3 items and slots 2-8 carry 1; loosening the 0.5 threshold gives up the `9263n` defect the rule exists for. Rule 10 now skips within-subject designs and SAYS SO, via a new `notes` channel on the report — because an unexamined PASS must not read like a checked one | **method** |
| 74 | **The row contract was being violated in all 182,684 rows and nothing asked.** CLAUDE.md requires what varies within a condition to be structured metadata, not only prompt text. Every study declares factors — 50 distinct names across the corpus — and none reached the parquet, so no consumer could select the rows where the privacy wording was plain except by parsing the condition string. Found by auditing the contract line by line rather than by anything failing. The conjoint is what turned it from cosmetic to blocking | **method** (our error) |
| 75 | **Licence was recorded in 0 of 14 studies** while source and provenance were recorded richly from the first one — adapter, study id, line citations into the instrument. The definition of done asks for all three; nothing noticed the missing one because nothing asked. Now QC rule 16. **A checklist item that nothing executes is not a checklist item** — the other four items each had a rule or a test behind them, and were all satisfied | **method** (our error) |

---

## Round 9 — the wave-1 checkers, findings 76-79

| # | Finding | Kind |
|---|---|---|
| 76 | **A missing schema field makes information drift into free text, and then the audit trail lies about it.** `a42yg`'s Q7 labels its midpoint "Both are important"; `Scale` had nowhere to put that, so the maker wrote "(4 means both are **equally** important.)" into the question — inventing a word that asserts parity where the source asserts only that both matter — and recorded in `notes` that the clause was "sourced from the same column header rather than invented". Neither the slip nor the false provenance was deliberate. **The fix is the field, not the discipline:** `Scale.mid_label` now renders it word-for-word. Watch for the shape — when a maker explains in `notes` why information had to go somewhere unusual, that is a schema gap announcing itself | **method** |
| 77 | **Shipping a template that resolves to nothing a respondent read.** `a2nbf`'s Q3/Q4 carry `[IF PPGENDER=2 INSERT: you; IF PPGENDER=1 INSERT: your partner]`, which varies by RESPONDENT, not by arm. The maker rendered `{you/your partner}` literally on 3,117 rows — 50.2% of the study — reasoning that the schema could not express it and that the notation mirrored the `.sav`'s own. The checker's decisive point: **it was never unknowable.** `PPGENDER` was already in that recipe's own `persona_map`. A declared `respondent_vars` plus the directive resolver written earlier the same day now resolves it per row, verified both ways: men read "If your partner were pregnant, would you want her to have a test", women "If you were pregnant, would you want to have a test". Zero fabrication, zero rows lost. `8ctbk`'s fixed attribute order is the same gap, still open | **method** |
| 78 | **A stale note is worse than no note, and I wrote this one.** I removed `yv2ta`'s recall-check outcomes and recorded the removal in a YAML comment beside the outcomes block — while `notes`, the field the schema carries as the audit trail, went on describing them as built at task_num 6 and 7 with their refusal counts. A reader trusting `notes` would have concluded they were in the corpus. The inverse of finding #67: there, a documented debt stopped being visible; here, a paid debt went on looking unpaid | **method** (my error) |
| 79 | **A checker's most useful act is often to reject the maker's framing of the choice.** Three of this round's findings came not from re-deriving numbers — all of which checked out, exhaustively, including a row-by-row independent rebuild of all 17,464 conjoint rows with zero mismatches — but from refusing the premise: "the schema cannot express this" became "the data to express it is already in your recipe"; "both halves are the source's own words" became "the stem's own number was altered"; "this clause is sourced" became "that claim is false". **Brief checkers to audit the reasoning, not only the arithmetic** | **method** |
| 80 | **The judge was pointed at the wrong half of the problem for weeks.** Jev was spent entirely on variable selection, where it has a documented blind spot and where NO shipped defect has ever originated. Every serious defect this project has had was a CONDITION asserting something the participant could not have known — and the whole hand-written stimulus surface of a 279,314-row corpus is 308 distinct strings. `scripts/condition_screen.py` screens all of them for about nothing. First full pass flagged 150 of 1,002 pairs; triage found two real defects on 12,622 rows that four maker/checker rounds had missed | **method** |
| 81 | **A wrong primitive returns a number that looks perfectly usable — again, in code written by the person who wrote finding 72.** The condition screen's first version asked a second, redundant `Noul` as a cross-check: "everything asserted was knowable, AND it does not reveal the experiment, AND nothing had not yet happened". A three-clause conjunction has no single answer to be probable about. It returned 0.55–0.58 across every input, a spread of 0.03, and would have been averaged into a score. Removed, not patched | **method** (my error) |
| 82 | **The frame is not cosmetic: a wrong one inverted the measurement.** The screen first told Jev "a survey respondent was shown the following text". They were not shown it — it is second-person prose we compose afterwards — and calling it a survey hid that one CONDITION of a randomised experiment is what is being judged. Under that frame `sh4px`'s CORRECTED condition scored WORSE than its defective one (0.35 against 0.17), because any second-person narration of past events reads as suspect. Reframed as "a reconstruction of one condition of a randomised experiment, not a transcript", `b87sm` went from missed to correctly named and correct naming went 3/5 to 4/5 | **method** |
| 83 | **A threshold chosen by taste is a guess with a number on it.** I set `DEFECT_MASS_REVIEW` to 0.35 by feel. Measured against the five defects actually shipped and their corrections, the gap is 0.61–0.97 against 0.03–0.31 — so 0.35 sat 0.04 from firing on a correction. Set to 0.45 from the measurement. `scripts/condition_probe.py` is also this project's first eval; CLAUDE.md has had an evaluation section since it was written and nothing had exercised it | **method** |
| 84 | **Counting a pattern match is not finding a defect, and I did it twice in one day.** `8ctbk` renders a conjoint attribute as a bare "4. -" on 5,682 rows; I inferred a defect from the SPSS value label "BLANK" and shipped a QC rule asserting it. The questionnaire declares `c. [LEAVE BLANK]` as a real third level and the deposit's own .docx contains SCREENSHOTS of the fielded screen showing a literal hyphen. Separately I reported `5hqan`'s "this part of the survey" as a genuine rule-17 hit without reading the sentence; it names a section, not an arm. Both rules corrected. **A sweep that returns a hit tells you the pattern fired** | **method** (my error) |
| 85 | **Fixed locally, never swept — the fifth and sixth occurrences, both found the same day.** Truncated religion value labels shipped in SEVEN studies, ~27,900 rows, reading "Protestant (Baptist, Methodist, Non-denominational, Lutheran, Presbyterian, Pent". `a42yg`'s REL1 had the identical fault, fixed in that one recipe, corpus never swept. Separately, `jev.py` was written to end duplicated prompts and four stale copies of the assignment prompt survived in scripts — including in `jev_calibration.py`, the harness that MEASURES Jev, twice. The truncation lengths were 80, 119 and 120, so a length test would have missed two of the seven; an unclosed bracket is the signal | **corpus-wide** |
| 86 | **The harness that measures the judge was measuring something else.** `jev_calibration.py` asks the assignment question with the first sentence of the production instruction only (the anti-counterbalancing warning added after `a5v96` is absent), over `[:9]` candidates plus the true answer — 10 options, answer guaranteed present, and `MAX_OPTIONS` is 45, so PAGING IS NEVER EXERCISED. Production offers up to 80 across pages. Every calibration number we had answers "can it pick from 10 when the answer is definitely there", and the project's confidence in Jev-on-assignment came from that | **method** |
| 87 | **Paging destroys a split assignment, and file order guarantees it.** `py9q3`'s 80 candidates page into two; all 21 real `VIGNETTE*_Insert` manipulation variables land on page 1 and split their own vote, while `XTESS094` — a sample-split router whose label reads "Experimental Condition" and whose value labels are the strings '1' and '2' — has page 0 to itself. Only a winner and a runner-up leave each page, so the real answer cannot reach the run-off. Related variables are ADJACENT in a data file, so siblings reliably share a page: the more columns a factorial spreads across, the more certainly all of them are eliminated. Carrying more runners-up cannot fix it; the question ("which ONE variable") is wrong for a design with 21 assignment columns | **tooling** |
| 88 | **Dataverse serves you a file with the value labels stripped, by default.** It "ingests" an uploaded .dta or .sav and serves a derived `.tab`; the conversion drops value labels, which is what this project decodes personas, conditions and non-answers from. `data/raw/QQM5MC` already held exactly that: `YouGovExp.tab`, where the API reports `originalFileFormat: application/x-stata-14`. Always `?format=original`. Measured on the recovered original: 66 of 73 variables carry value labels; the .tab carried none. (Also: Harvard Dataverse 403s the default `Python-urllib` user agent while serving curl, which reads like an auth failure and is not) | **tooling** |
| 89 | **A generated recipe keeps the output and throws away the judgement.** `9xw67_conjoint.yaml` is 455,919 lines, 95% of all recipe text here, and its notes said the arms were "generated once by `scripts/gen_conjoint_full.py`-equivalent code". That script was never kept, so nobody could re-derive, verify or regenerate it. Writing the generator (110 lines, reproduces all 11,991 arms exactly) immediately found two things the prose had hidden: SIX value labels severed at Stata's 80-char ceiling, five of them the CLASS race-disparity attribute the study is ABOUT — truncated stimulus text that rule 18 cannot see, because the cut lands mid-word with no bracket — and an ordering the prose could not pin, "scanning (V1,A), (V1,B) ... across all 2,048 respondents" reading equally well as respondent-major when it is slot-major | **method** |
| 90 | **Nine for nine.** SocSci210 was wrong about every one of wave 2's five studies, each differently: `9xw67` built the vignette only and never touched the conjoint; `es4xw` was built from the proposal's PILOT, a design never fielded; `sh4px`'s two "conditions" are our two outcome clusters, so the real 10-arm randomisation is absent; `ye2ej` dropped an arm and coded a banded salary as band numbers on a Likert axis; `py9q3` has vignette-3 items under vignette-2 labels and items from a different sub-experiment. The paper states the method — the 210 were reconstructed by an automated agent — which is the explanation. **A numeric answer key and a lower bound on the design, never a description of one** | **reference** |
| 91 | **A recipe that documents its own blocker is a to-do list, and we had three.** `a2nbf` wrote "QC rule 1 fails hard if two different condition_nums render identical text", `sh4px` named the exact field it needed ("an `ItemOverride`-style per-(condition, outcome) override for the rendered CONDITION text"), `8ctbk` wrote "rendering the true per-respondent order... is not tractable". All three were accurate readings of the schema AS IT STOOD, and all three were fixed in an afternoon once read as a queue rather than as closed decisions. `Arm.raws`, `ItemOverride.condition_text`, `Condition.line_order_vars`. **Grep the corpus's notes for the word "cannot"** | **method** |
| 92 | **A fixed rendering of a randomised order was right for 1 row in 17,464.** `8ctbk` randomised its six attribute rows per respondent and the deposit records every position; 654 of 720 permutations occur, and exactly ONE of 1,794 respondents saw the canonical order the recipe rendered for everybody. Every count reconciled throughout. The blocking argument — that per-respondent order means crossing 1,146 conditions with 720 permutations — assumed order must be DECLARED as part of the condition. It is a property of the respondent, like a piped pronoun, so it is resolved when the row renders and the 1,146 stay 1,146 | **data** |
| 93 | **A helper that is never called looks exactly like a correct one.** The mutant that made the melt ignore `line_order_vars` entirely PASSED every test: unit tests proved `reorder_lines` worked, and nothing proved the build invoked it. Caught only because the mutation was run. A unit test on a pure function and a test that the pipeline reaches it are different tests, and the second is the one that fails silently when absent | **method** |
| 94 | **The crosscheck ignored SocSci210's `task_num` for 28 builds.** It compared rows, conditions and the response distribution — so two builds could agree on all of them while disagreeing about WHICH QUESTION a row answers. That is exactly how `sh4px` (their two "conditions" are our two outcome clusters) and `py9q3` (items from a different sub-experiment under one condition) hid, both found by hand. Now compared, and REPORTED rather than failed, because task numbering has no shared convention: on `9263n` we declare 14 tasks and they seven, each of theirs a pair of ours merged, and a crosstab shows our tasks 0-11 each occur in exactly 2 of 4 conditions — our split makes task_num partly a function of condition_num, so their merge is arguably righter, while tasks 12/13 are asked of everyone and they merged those too. Neither is simply wrong | **tooling** |
| 95 | **Recovering four excluded outcomes reproduced the reference count exactly.** `sh4px` went 6,911 -> 11,532 rows, and 11,532 is SocSci210's own figure for the study. Their numbers had predicted it: their two "conditions" decompose as Q2-Q5's valid responses (4,621) and Q8-Q14's (6,911). They had the right rows on the wrong axis, collapsing outcomes into conditions. An exact match with a build we believe is wrong is not reassurance — it means both builds saw the same data and only one of them modelled it | **reference** |

---

## Round 11 — the first UK study, findings 96-100

| # | Finding | Kind |
|---|---|---|
| 96 | **The first study verified BEFORE its recipe was written, and the method generalises.** UK studies are not in SocSci210, so `comparable_to_socsci210` is false and the usual numeric answer key does not exist — which looked like a loss and is not. `QQM5MC`'s paper is open access and both of its Table 1 regressions are SATURATED (four conditions fully crossed with a two-level moderator), so the printed coefficients ARE the eight cell means. Reconstructing the conditions from the do-file and summing those coefficients reproduced all eight, both Ns exactly, and the identity-prime split to 82.07/14.35/3.57 against the paper's 82.1/14.3/3.6 — all before a line of recipe existed. **A published saturated regression is a better answer key than SocSci210 has ever been**, because it is the authors' own numbers rather than a third party's reconstruction. `scripts/verify_QQM5MC.py` runs it against the BUILT parquet, not the deposit, so it tests the melt and not the paper | **method** |
| 97 | **A study can record its randomisation only as the absence of questions.** `QQM5MC` has NO assignment column — every other recipe here names a `condition.source_var`. Its four conditions are four blocks of variables, and the only record of who saw what is that the blocks a person was not routed to read 9999 "Not Asked". That is the instrument's own account of what it asked, not an inference from the answer, and the file keeps the two apart: 9998 is "Skipped". Now `Arm.witness_var` + `Condition.not_asked_code`. The routing is internally consistent — within each block Q1 and Q3 agree exactly on who was not asked — which is what makes it readable at all, and the 28 existing recipes rebuild to 283,935 rows unchanged | **data** |
| 98 | **A respondent routed to two conditions has none, and the published analysis counts them twice.** `ID 2158` was asked both the Prime only and the Info only blocks. The authors' `drop if Q1==. & Q2==. & Q3==.` keeps that person in both groups after the reshape, so Table 1's N of 2,762 includes a duplicate — and our two cell means furthest from the table are exactly the two cells they were counted in, moving in the direction their rank of 6 predicts. A melt taking the FIRST match would be identical on 3,266 of 3,267 respondents and silently wrong on the remaining one; run as a mutation, it killed three tests. The count is DECLARED (`ambiguous_routing: 1`) and the melt fails in EITHER direction, so a re-fetched deposit can neither grow the discard quietly nor leave a stale declaration standing | **method** |
| 99 | **Reading a figure by eye and calling the difference a failure.** The first verification script keyed on Figures 4 and 5, read off the plotted bars, and failed two cells — against a build that was correct. The paper prints the constant as 16.83; I had written 16.9 from the chart. **Where a table and a figure carry the same numbers, the table is the source**: a drawn bar resolves to about 0.1, and no tolerance tight enough to be useful survives that. Same shape as finding 84 — the measurement fired and the defect was in the reader. Found en route: four of `work_type`'s nine value labels are severed at Stata's 80-character ceiling mid-word, the 9xw67 fault in a second deposit, and this one has no questionnaire to recover them from. The variable is excluded and the exclusion is pinned by a test | **method** (my error) |
| 100 | **A module written to end duplicated prompts did not end them, and nothing was checking.** `jev.py`'s first paragraph has said since the day it was written that these questions used to be asked "in eight separate scripts, each with its own prompt... a lesson learned in one did not reach the others" — and FIVE scripts still owned prompts. Not a near-miss: `jev_show_wire.py`, whose whole job is to print what production sends, held a stale sixth copy of the transfer-screen wording and was reporting on a call nothing else made; `persona_harmonise.py` held both prompts the persona crosswalk is derived from; `persona_classify.py`, `uk_content_screen.py` and `uk_priority.py` each held one, and all four built `TypeSafeClient()` directly, bypassing the error message that explains the key lives in `~/.bash_profile`. Found by grepping for `system_one` across the repo rather than for the one file I had noticed. Five prompts moved; `jev_firstpass.py` deleted; `tests/test_architecture.py` now parses every script and FAILS on a `system_one` call outside `jev.py`, with the two eval harnesses as a named, existence-checked exception. **This is finding 85's shape a seventh time, and the reason it recurs is that "put it in one place" is a decision while "nothing may put it elsewhere" is a test** | **method** (my error) |

---

## Round 12 — the QQM5MC checker, and what a sweep found behind it, findings 101-105

| # | Finding | Kind |
|---|---|---|
| 101 | **An INERT wrong declaration is the shape that survives review.** `QQM5MC` declared `Region_GOR: [12, ...]` where 12 is "Northern Ireland" — a real region in a drop list. It deleted nothing, because this deposit has no respondent from Northern Ireland at all (observed 1-11), and that is exactly why a build, a QC pass, a maker's read-through and a published-table verification all left it standing. It would have deleted the region of every NI respondent the moment a refetch or another UK deposit had one. **A declaration with zero current occurrences has never been tested and could say anything** — a corpus-wide audit found 55 of 124 declared missing-codes are in that state, and this was one of them | **method** (my error) |
| 102 | **The checker rule earns its place even on a study verified against its own published table.** `QQM5MC` reproduced Sorace & Hobolt's Table 1 to three decimals, had 16 passing tests and two mutation-tested mechanisms — and a checker briefed to break it found FIVE defects, none of which any of that could see: a real answer in a sentinel list; a truncation length recalled from another study rather than measured (120, not 80, and ledger 85 had already recorded that this project's truncations run 80/119/120); a wrong journal, contradicted by the deposit's own `publicationCitation`; `socgrade` excluded as "redundant" when 991 of 3,267 respondents disagree because it is a DIFFERENT PERSON'S social grade (personal vs chief income earner); and composed narration never declared as composed. **Zero numeric defects, five in the condition-and-notes layer** — the same split as waves 1 and 2, in the one study where I had skipped the checker | **method** (my error) |
| 103 | **618 respondents were telling a model "Ideology: Unknown".** Panel code -1 "Unknown" was undeclared on the profile variables of `b87sm`, `bf8p2` and `zaqkm`, so it rendered into the persona text as a value. QC rule 12 was silent because its keyword list did not carry "unknown". Found by resolving every declared missing-code in the corpus against its own value labels, which is a thing no rule can do — by the time a row exists the code is gone, so the check has to run against the DEPOSIT, from a script | **corpus-wide** |
| 104 | **Never filter a judge's answers through the heuristic it exists to beat.** `recipe_prep.py` asked Jev about every value label on a variable and then printed only the ones a keyword list had already flagged, so the judgement could only ever CONFIRM the regex. Jev was asked about "Northern Ireland", answered, and the verdict was binned unread — the defect in 101 was knowable, paid for, and discarded. CLAUDE.md already warned about narrowing the OPTIONS; this is the same error applied to the ANSWERS, and it is harder to see because the call still looks right. The same function also skipped any variable with more than 20 labels, in silence, which took out the 22-level UK education ladder. Unfiltered, its first run produced the thing it structurally could not before: one disagreement, "Not applicable", which Jev called a non-answer and the regex missed | **tooling** (my error) |
| 105 | **A punctuation fix that nearly deleted real answers.** The audit's first run reported "Don't know" and "Can't remember" as suspect non-answers, because the file spells them with a CURLY apostrophe and every keyword list here used a straight one — including the pipeline's rule 12, which had therefore been silently missing them. Fixing it by stripping all punctuation made "na" a substring match, which swallows "National", "Finance" and "Native American": the exact failure the check exists to prevent, in the opposite direction, introduced by the fix. Caught before shipping by testing the fix against labels it must NOT match. **When widening a pattern, write the cases it must still reject first** | **method** (my error) |

---

**Wave 1 tally.** Five studies, three checkers. `8ctbk` and `5hqan` clean on every
point, each independently re-derived rather than re-read. `a42yg`, `a2nbf` and
`yv2ta` each had a real defect, all in the condition-and-notes layer that
CLAUDE.md names as the one error nothing downstream can detect, and none of them
touching a response or a persona value. Zero numeric defects across all five.

---

## Round 13 — the UK deposit read, and a planning table that had aged into an assumption, findings 106-113

| # | Finding | Kind |
|---|---|---|
| 106 | **A planning table nobody re-read asserted a licence that was false.** `docs/SocSci-UK_MASTER.md` §5a has listed nine Harvard Dataverse UK experiments under the heading "(all CC0)" since early planning. Resolved against the API, eight are CC0 and **`POMIFD` is not** — `latestVersion.license` is null and its terms read "This dataset is made available with limited information on how it can be used." Licence is the ENTIRE reason the UK layer is the only publishable material here, and the one row where it was wrong is the row with the best data in it. Worse than the error: all nine had sat unverified while every hour of UK work went to four studies found later by a separate sweep and listed in a second table directly below them. **Nothing in that table distinguished "verified" from "written down"**, so a planning note aged quietly into an assumption | **method** (my error) |
| 107 | **The design label was wrong on BOTH entries anyone checked against data.** `6MRVOM` was listed as "conjoint with prices / choice" and is a 2x2 factorial cost-framing experiment with a CONTINUOUS slider outcome — no profile table anywhere in the instrument or the file. `POMIFD` was listed as MaxDiff and is pairwise comparison, two arguments at a time. Two for two, on the only two rows anyone verified. Both titles were right and both respondent counts were right, which is exactly what made the design column credible. I repeated the conjoint claim to rich and built an argument on it before checking | **method** (my error) |
| 108 | **A set-match hid a swapped label, and only a second independent read found it.** `6MRVOM`'s published Table 1 prints four cell sizes that match the data as a SET — {897, 903, 914, 922} — but its High Cost and Low Cost rows are swapped against both the file's own value labels and the authors' own `analysis.log`. The first read matched the four numbers and reported exact agreement; a second agent, surveying the same deposit in parallel, checked which label owned which number. Table 2's coefficients are unaffected because its baseline is stated in prose, so **a build keyed on Table 1 would mislabel the conditions and every number would still reconcile** — the condition is the one error nothing downstream detects. **Aggregate agreement is not assignment agreement.** The duplicate survey was unplanned and paid for itself on its first finding | **method** |
| 109 | **An unlabelled missing code that is the MODAL response.** `6MRVOM` codes "Don't know" on its main outcome as 997 and gives it no value label at all; only 998 "Skipped" and 999 "Not Asked" are labelled. 997 is the single most frequent value in that variable — **1,105 of 3,636 respondents, 30.4%** — and on Q5 it is 33.9% of those asked. This project's standard missing-code handling would read it as a preferred net migration figure of 997 people, for a third of the sample, and nothing would look wrong. Recoverable only from line 28 of the authors' R script. Ledger 103 with the proportions inverted: there an undeclared code reached 618 personas, here it would corrupt the response for a third of a study | **data** |
| 110 | **Three of the four deposits worked do not contain their own condition text — and the better-documented ones were on the list the whole time.** `LOGVPZ`'s stimulus and both question stems exist only in the paper's Table 4; `X08IVC`'s is severed at 254 characters inside the `.sav` and completed only in an appendix; `TLT65Z` Study 2's seven message texts are nowhere at all. Meanwhile `EFXNLX` and `6MRVOM` ship fielded questionnaires, and `EFXNLX`'s eight attributes match its instrument WORD FOR WORD — the first UK deposit needing nothing recovered, reconstructed or inferred. Four of the nine ship an instrument; three of the four we built do not. The convention that the questionnaire is the only authority on stimulus wording is right, but it was written against SocSci210 RECONSTRUCTING text. **An author-written appendix is a primary source; an agent's reconstruction is not** — and treating them as the same thing silently blocked the three studies where the authors had published the wording themselves | **method** |
| 111 | **`work_type` truncated in a FIFTH deposit, and shipping a questionnaire does not rescue it.** Four of its nine value labels severed mid-word — at 80 characters in `QQM5MC`, at 120 in `EFXNLX` and in both `35M5CV` conjoints, the same variable and the same four of nine every time. **This entry first read "and this time the questionnaire rescues it", and that was wrong.** I wrote it on the reasoning that `QQM5MC` had no instrument to repair the labels from while `EFXNLX` ships one — and never checked. `EFXNLX`'s questionnaire does not ask `work_type` at all: it is a YouGov STANDING-PANEL variable, pulled from the profile library (`{pdl-update ...}`) rather than fielded in the instrument, so no study-specific questionnaire will ever carry it. Confirmed by searching both `EFXNLX`'s and `35M5CV`'s converted instruments for every distinctive phrase in the truncated labels: zero hits. Disposition is `QQM5MC`'s — excluded — in every deposit, and the standard NRS wording being well known from elsewhere is not a licence to write it in. **Check by NAME, and do not assume an instrument covers a panel-profile variable** | **data** (my error) |
| 112 | **A study can sit in a deposit of experiments and not be an experiment.** `TLT65Z` Study 3, both its British and German halves, regresses real-world vote choice on a continuous attitude scale that was simply asked of everyone. Nothing was assigned; there is no condition. Its driver variable `mcp01` reads like an assignment column by naming convention and is a PERSONA attribute. The German scope question dissolved with it — Germany appears only in Study 3, in its own separate file, so the ruling to exclude it (rich, 2 Oct) costs nothing and there was never a mixed file to filter | **data** |
| 113 | **The answer key can be CC0, in hand, and still unreadable.** `EFXNLX`'s published paper reports every result as an AMCE plot — no numeric table in the main text beyond one inline value — which this project has already ruled unusable (ledger 99). But the deposit itself ships the complete Supplementary Information as R Markdown SOURCE, which computes the AMCE tables to two decimals with standard errors, including the manual baseline releveling that sets every sign. The numbers are ours and are simply not rendered. Running that code once and transcribing the output is the `verify_QQM5MC.py` pattern; **reimplementing the estimator in Python would mean checking my code against my code**, which is not verification. Also confirmed here independently: the paper's prose PARAPHRASES its own fielded preamble, dropping words — the questionnaire-is-authority ruling, demonstrated rather than asserted | **method** |

---

## Round 14 — EFXNLX, and a study that passed every check while being wrong on every row, findings 114-118

| # | Finding | Kind |
|---|---|---|
| 114 | **A study can pass QC, verify against its authors' own estimator to thirteen decimal places, and be wrong on every single row.** `EFXNLX` rendered its 8 attribute rows in one fixed canonical order. The questionnaire randomises that order per respondent in `list_table` — column 166 of 422, non-null for all 3,293, 3,137 distinct permutations, and **ZERO respondents drew the canonical order**. So all 16,465 conditions stated a sequence nobody saw. The recipe's own notes asserted "no such column exists (checked)"; one command falsifies that. AMCE and marginal-mean estimators are INVARIANT TO DISPLAY ORDER, so `verify_EFXNLX.py` agreed to 1.6e-13 while the condition layer was wrong in every instance — and the depositors' own SI says they randomised row order precisely to mitigate ordering effects, so it is a design feature, not layout. **Numeric verification cannot see the condition. That is what a checker is for**, and it is the third time in one day one found what verification structurally could not | **method** (my error) |
| 115 | **A mutation left in place is a defect wearing the costume of its own test.** Fixing 114, the agent wrote the right test — pinned against `list_table` independently, so a bug shared with the generator could not hide it — then mutation-tested it by reverting the renderer to canonical order, confirmed the test died, and **left the mutation in**, marked `# MUTATION: back to canonical order` in otherwise finished code. The generator read `list_table`, validated it was a permutation of 1..8, documented the mechanism in twenty accurate lines, and ignored it. I regenerated the recipe from that before noticing. Mutation testing is right and this project depends on it; **a mutation is a temporary lie told to the code, and leaving one behind is worse than never testing, because the test now passes against the implementation it was written to catch** | **method** |
| 116 | **Three defences lined up and exactly one was load-bearing.** After the fix was written: QC passed, verification passed to machine precision, and one test failed. Only the test was right. The near-miss was closer still — the generator was fixed at 13:13, the recipe last written at 13:07, and a parquet built at 13:24 from the stale recipe. "Fix applied, build run, verification passed" would have read as complete. **Check that each step consumed the previous step's output; a timestamp is evidence and an assumption is not** | **method** (my error) |
| 117 | **A minimal pair is a GROUP BY, not a search.** QC rule 5 compared every pair of conditions per factor — `itertools.combinations` over 16,465 conditions × 16 factors, 562 of `EFXNLX`'s 564-second QC. Two conditions form a minimal pair on factor f exactly when they agree on every OTHER factor, so bucketing on the all-but-f key finds the same pairs at sum(m²) over buckets rather than n², and in a conjoint nearly every bucket is a singleton. Measured identical pair sets on all 30 recipes before swapping it in; the full build went 564s → 49.6s with the same 17 warnings. **A nine-minute check is a check people stop running**, and skipping QC is how the `QQM5MC` defects got in | **tooling** |
| 118 | **An empty report reads like a clean one — three times in one tool, stacked.** `recipe_prep.py` section 4 reported "every conditional directive in this deposit parses" having opened ZERO files: it globbed `*.txt` and every Dataverse deposit ships `.docx`. Fixed that, and it STILL passed — `quex` recognised none of the directives, because this instrument writes them as `[QA2A if ...]` (variable before the IF) and `{module ... if ...}` (braces), so nothing was offered to the parser and nothing was refused. Fixed that, and a THIRD version appeared on `35M5CV`: `questionnaires()` ignored `--file`, so one sub-study's instrument was reported against another's. Each layer produced a confident verdict about something it had not examined. **A tool must say what it actually looked at, not what it failed to find fault with** | **tooling** (my error) |

---

## Round 15 — IP 9.10 built, a ceiling measured, and two checks that were checking nothing, findings 119-124

| # | Finding | Kind |
|---|---|---|
| 119 | **An archived value label can be wrong in a way that silently collapses the dimension the study is about.** IP 9.10 randomises five dimensions; three of the five are mislabelled in the `.dta`. `ff_housework = 2` ("your partner does three quarters, you do one quarter") and `ff_housework = 4` ("your partner does one quarter, you do three quarters") carry **the same label**, "partner 1/4" — opposite arrangements, one string. `ff_children = 2` reads "one children age 6" where the questionnaire says "one child aged 6 **months**". `ff_paid_housework = 2` reads "o paid work", a truncation of "no paid work" that scans as its opposite. A builder reading labels renders two opposite housework splits identically and the one dimension the study exists to measure disappears, with every count and every QC rule still agreeing. The questionnaire specification (`Scavignettes_ip5`, VIG1-3) carries all five dimensions word-for-word. Ledger 110-111 said the questionnaire is the only authority on stimulus wording; this is the first case where the archive's alternative is not truncated but **wrong** | **data** |
| 120 | **The desk verdict on an experiment can be wrong about who is standing in the scenario, and only building it finds out.** `9.10`'s catalogue reason read "respondents rate a described couple, not themselves" — written from the User Guide's own one-line summary. The fielded wording is "Imagine that **you** are married or cohabiting". The respondent is inside the scenario, so the outcome is imagined own satisfaction, not third-party judgement, and that changes what the rows mean to anyone training on them. The verdict (build) was right for the wrong reason, which is the hardest kind of error to notice, because nothing downstream disagrees | **method** (my error) |
| 121 | **A check that reads the inputs cannot validate what the code did to them.** The first `--check` for 9.10 compared `e_indresp_ip`'s copy of the allocation against `e_hhsamp_ip`'s, reported 23,880 agreements, and never called `derive()`. It is structurally incapable of failing on a join defect: no change to the join can alter either file it reads. Rewritten to compare the **derived frame** against `indresp`'s copy row for row, and then mutation-tested by reversing `hhsamp`'s allocation block before the merge — 17,552 disagreements, test dies. Ledger 118 was tools reporting on files they had not opened; this is a check reporting on a step it did not run | **method** (my error) |
| 122 | **Asserting that two sets OVERLAP does not test that the members are the right members.** `participant_id_var` was added so a panel person keeps one id across waves, instead of the row index making them two unrelated participants. The test asserted that wave 5's and wave 6's id sets intersect in more than 1,000 people — and **passed under the mutation that ignores `participant_id_var` entirely**, because row-index ids collide across files: `ukds_6849:0` exists in both waves and names two different people. The mutation survived, which is the only reason this was caught. Replaced with two assertions a row index cannot satisfy: every id is that row's own `person` hash, and the id set is unchanged when the rows are shuffled | **method** (my error) |
| 123 | **Household-level allocation is the most useful structure in the study and reads at first like a defect.** Both people in a couple were shown the IDENTICAL three scenarios — allocation lives in `{w}_hhsamp_ip`, joined on `{w}_hidp`, one draw per household. In the first twenty rows a woman of 48 and a man of 58 in one household rate the same three arrangements and he is satisfied where she is not. Same condition, same household, different answer: persona has to do the work, and no between-subjects design in this corpus offers that. Two further facts a consumer needs: the fifth dimension (paid help) exists in **no** wave's `indresp`, so the household join is not optional; and 32% of respondents gave the same answer to all three scenarios, contributing no within-person variation | **data** |
| 124 | **The study measures its own ceiling, and the ceiling is 27.7%.** The User Guide says "the exact allocation at Wave 5 was replicated at Wave 6", which reads like a footnote about fieldwork and is the single most important fact about the data: of the 1,849 people in both waves, **27,696 of 27,705 allocation cells are identical**, so a returning respondent rated the SAME three arrangements a year apart. That makes 3,621 same-person same-scenario pairs, and across them the answer is identical only **27.7%** of the time — within one point 57.5%, mean absolute change 1.59 points on a 1-7 scale, correlation 0.329. Chance is 14.8% (matching the marginal) and 19.4% (always answering the modal "Neither"). **So the entire usable band on exact match is about 19% to 28%, and the top of it is people disagreeing with themselves.** Any predictor reported above ~28% on this outcome is not beating the respondents, and a number quoted without this ceiling beside it is uninterpretable. Second consequence, easy to miss: the two waves are **not independent rows** — pooled they are 9,631 rows but only 6,010 distinct (person, cell) pairs, so 3,621 of them repeat a person-and-scenario the other wave already holds. They are built as separate experiments for that reason. Found by testing a sentence in the documentation rather than reading past it | **data** |

---

## Round 16 — IP 9.18 built, a randomisation that failed in the field, and a checker that caught my numbers, findings 125-130

| # | Finding | Kind |
|---|---|---|
| 125 | **A documented randomisation can fail in the field, and the documentation will not say so.** The User Guide says wave 17 allocated each 9.18 dimension "1/2 to each condition" and each name sequence "1/6"; the technical report says "Vignettes were randomly assigned to respondents within the script". In the data, **354 of 2,220** respondents (all web, none before August, 244 in December) share ONE identical allocation, and **933** share theirs with someone (1,497 distinct), in groups that fall on a single start date across different households: a generator seeded from the date, or a fixed fallback. Wave 9, the same design, gives 2,010 distinct allocations to 2,010 people. The rows survive, because the stored codes filled the text (the block's mean ratings match what an additive model fitted on everyone else predicts). But the wave is not a balanced factorial, and anything estimating an effect from it inherits a confound with late web response. Found only by counting distinct allocations, which no per-row check does | **data** |
| 126 | **A test that pins the numbers the code printed pins the bug along with them.** `report_allocation` keyed on slot 1's name only, which merges name sequences 1-3 and 4-6, and reported 1,395 distinct / 1,060 shared for wave 17. The truth is 1,497 / 933. The test asserted 1,395 / 1,060, because that is what the code said, and the recipe notes, generator docstring and manifest quoted them, inconsistently, in three versions. The independent checker found it by computing the key itself. The fix now kills the old key as a mutation. "Write the test expecting to see it fail" applies to pinned numbers too: a pinned number has to come from a computation the test does not share | **method** (my error) |
| 127 | **QC's persona-vocabulary warning shows three labels and hides how many there are.** The wave 9 build warned about three `jbstat` labels; **13** were unmapped. UKHLS `jbstat` labels are spelled differently in different Innovation Panel waves: lower case and abbreviated in wave 9 ("lt sick or disabled"), title case in wave 17, full in waves 5-6. The crosswalk matches exactly, so every new IP wave needs its labels listed against the scheme, not just the warning read. `scripts/persona_ukhls.py` now carries all three spellings. One wave 17 label, "Temporarily laid off/short time working", straddles two canonical states and goes to `Other` | **data** |
| 128 | **`docs/EXPERIMENTS.md` filed every UKDS experiment as "TESS (OSF)", and had been stale since 9.10 landed.** The generator's layer split read `not is_uk`, and `is_uk` meant Dataverse, so a third source fell into the US layer silently. The doc still said 41 experiments when 43 were built: `--check` is not in anyone's commit path. Fixed: a UKDS layer, TESS selected by its own source string, an unknown source stops the render, and a test asserts each UKDS row's rendered layer | **method** |
| 129 | **"Read rows" and the UKDS licence pull in opposite directions, and I followed the wrong one.** Reading the built 9.18 rows, I printed eight full rows, personas and responses included, into the conversation, which sends UKDS microdata to an LLM API. CLAUDE.md forbids that until the EUL is cleared, and the clause 5.5 request is still unsent. For UKDS, reading rows has to mean the instrument side (condition and outcome text, transcribed from public questionnaires) plus aggregates computed locally. The checker was briefed that way and needed nothing more. Rule added to CLAUDE.md | **method** (my error) |
| 130 | **`sex` is not harmonised anywhere, and 9.18 wave 9 adds two more spellings.** 27,517 rows carry `sex` (most of the corpus uses `gender`), spelled `Female`/`Male`, `female`/`male` (wave 9, the archive's own lower case) and `Woman`/`Man`. So the same panel member is "female" in 2016 and "Female" in 2012 and 2024. Not fixed in this build: it needs a `sex` crosswalk, which is a shared-code change | **data** (debt) |

## Round 17 — IP 9.39 and 9.36 built, IP 9.43 dropped, findings 131-133

| # | Finding | Kind |
|---|---|---|
| 131 | **A per-task map with a fallback fails open.** `ConditionTemplate.outcome_questions` attaches a question per task; a task left out of the map silently keeps the outcome's own `question`. In 9.39 that fallback is the questionnaire's fill notation ("How do you see [her/him] ..."), so removing one key shipped 1,477 rows with brackets in the question — and **QC reported 0 failures and 0 warnings**. Only the study's own test caught it, and a fallback without brackets would have been caught by nothing. Found by the independent checker by mutating the recipe in memory. Now refused at load: a template that declares any question must declare one for every outcome | **method** |
| 132 | **A triage PASS says the data exists, not that the outcome fits a row.** 9.43 passed triage (allocation variable located, wording present) and was third in the build order. Reading the questionnaire found three "code all that apply" lists that differ between versions. A row needs one question and one answer, so any build would have restructured the instrument. Dropped by rich on 9 Oct. The remaining methodology experiments in the plan (EQ-5D variants, ReQoL-10, response-option presentation) should have their outcome shape read before their data | **method** |
| 133 | **A banded scale shown with only its endpoint labels hides its spacing.** The answer instruction names the two ends only ("1 means 1-2 and 5 means 10+"). For 9.36 the middle codes are "3-4", "5-6", "7-9" drinks and "Less than monthly", "Monthly", "Weekly": uneven intervals a model cannot infer from the ends. The same holds for every banded outcome in the corpus. Raised by the 9.36 checker. Not fixed: `Scale` has no field for middle labels, so fixing it is a pipeline change | **method** (debt) |

## Round 18 — IP 9.24, 9.4, 9.17 and 9.31 built, IP 9.48 dropped, findings 134-136

| # | Finding | Kind |
|---|---|---|
| 134 | **An allocation variable can hold a value for respondents it did not allocate.** In 9.31 (wave 14) the continuing sample was allocated in the script (`n_req10cond`) and the refreshment sample by household before fieldwork (`n_ff_req10cond` in `n_hhsamp_ip`). Refreshment respondents ALSO carry a value in `n_req10cond`, and it bears no relation to what they were asked: it splits 253/226 and 252/233 across the two blocks, where the household variable matches exactly. The User Guide names both variables, but nothing says the person-level one is noise for half the sample. A build trusting it would have put about 480 respondents under the wrong condition, with every count reconciling. Found by cross-tabulating each arm variable against which modules were actually answered — the same check that should run on every allocation | **data** |
| 135 | **A permutation code can be unreadable in a way no document settles.** 9.17 records the shuffled order of each list as an integer such as 3124. "Statement 3 was shown first" and "statement 1 sat in slot 3" are both consistent with the specification ("record the random ordering as an integer"), the variable labels, the User Guide and both technical reports; every permutation occurs about equally, so the data cannot decide either. Built on the first, natural reading and recorded as an assumption; about two-thirds of rows depend on it, though only for order. The independent checker established this; my own tests used the generator's reading and so could not have | **data** (unresolved) |
| 136 | **"Skip when unrecorded" is a silent drop until it is counted.** The new per-item bullet order skipped a row whose order was missing. That is right for a row nobody answered, and a silent loss for one somebody did. It dropped nothing in 9.17, so it had never been exercised. Now an answered row without an order stops the build; an unanswered one is still skipped. Found by the independent checker | **method** |
| 137 | **An extractor that reads one block of a question sees one mode's wording.** 9.31's items carry a self-completion block and a telephone block, each with its own text AND its own options. The extractor read the telephone text and handled it per mode, but never read the telephone options. So telephone respondents' EQ-5D answers were labelled "I have no problems in walking about." where they heard "You have no problems in walking about.": 1,326 rows, plus 1,786 conditions quoting the block. Tests passed because they checked the question text by mode and never the options. QC passed. The independent checker found it by transcribing the PDF itself. When a mode alternative exists, every field it can override (text, options, instructions) has to be read and compared, not just the field that was noticed first | **method** (my error) |
| 138 | **An allocation variable's own value labels can be reversed.** 9.42's `ff_numeracyw16` is labelled 1 = "Environmental questions early/financial questions late", and the User Guide says the same. The questionnaire routes the early environmental questions on 2, and the data agree with the questionnaire in every cell: the environmental-only households answered early under 2, the financial-only under 1. A build that trusted the label would have attached every order condition to the wrong half of the sample, and every count would have reconciled. Third occurrence of the same pattern in this round (134: a variable that is noise for half the sample; 9.18: labels that contradict themselves): **the allocation is whatever the routing did, and the routing is visible in which variables hold answers. Cross-tabulate before believing any label** | **data** |

## Round 19 — the plan finished: 9.42, 9.20, 9.13, 9.9 and 9.47 built, 9.12 and 9.11 dropped, findings 139-142

| # | Finding | Kind |
|---|---|---|
| 139 | **A convention that has never been exercised has never been tested.** CONVENTIONS prescribes `factors: {}` for a single-condition source, and no source had used it until 9.13. QC passed; writing the parquet then failed, because Parquet cannot store a struct with no fields. The writer now stores an all-empty factors column as null, with a test for both directions | **method** |
| 140 | **An instruction to operate the screen can collide with an answer code.** 9.13's second appeal ends "If you do now want to continue enter 1 …", rendered into rows whose answer codes include 1. Survey mechanics are already dropped as a rule; this one was quoted because it sat inside otherwise respondent-facing text. Found by the independent checker | **method** |
| 141 | **"Who heard the questions" is a layout condition's real boundary, not the mode variable.** 9.20 excluded telephone respondents from a screen-layout experiment, but 75 face-to-face respondents (299 rows) had the interviewer complete the self-completion for them (`scac` = 2), and they carried a layout they never saw. Found by the independent checker. Any condition about what was on a screen has to exclude everyone who did not look at it | **data** |
| 142 | **Four of the plan's sixteen did not survive their own questionnaire.** 9.43 (code-all-that-apply lists), 9.48 (on-screen computed bounds not in the deposit), 9.12 (the manipulation follows the answer), 9.11 (the treatment is a graph). All four had passed triage, which checks that the data exists. Each was found only by reading the outcome's shape in the instrument: ledger 132's lesson, three more times | **method** |
| 143 | **An assignment column can name one condition while the respondent met two.** DEL's Feb 2023 sandbox has one respondent assigned condition 1 who also answered condition 5's question, with page timings on both (a back-button re-assignment). The melt only checked ambiguity for witness designs, on the premise that "a coded assignment yields one arm by construction"; the premise was false. `Condition.routing_check` now reads each arm's OWN outcome variables and counts any code there as a second condition, against the declared `ambiguous_routing`. It is OPT-IN because deposits mark "not asked" differently: switched on everywhere, it read the Innovation Panel's negative not-asked codes as answers and flagged 1,870-2,719 respondents in four builds — the full rebuild caught that before it shipped. On only where "not asked" is blank | **schema** (opt-in; all 63 earlier builds unchanged) |
| 144 | **A numeric person id gained ".0".** SPSS reads `GUNQID` as a float, so ids came out "del:120615074968.0"; a file holding the same person as an integer would have given them a second id and silently broken DEL's cross-file person link. Whole-number ids are now written whole | **pipeline** (inert for the 22 earlier builds, whose ids are text) |
| 145 | **A persona age can be a code, and nothing noticed.** DEL's wave 3 panel stores `age` as a code with value labels (1 = "18" ... 77 = "94"); the Feb 2023 sandbox stores real ages, and reusing its persona map rendered the code: every row of both NGO conjoint builds 17 years too young, 1,735 adults shown as minors, every QC rule passing. Caught by the independent checker. The build now reads age through its label (an unlabelled value's label is itself, so 64 other builds are unchanged), and QC rule 20 FAILS any age outside 16-120. The ceiling is the human lifespan, not plausibility: four respondents in 35M5CV_lodger (115) and POMIFD (118, 119) carry ages YouGov recorded, which are the source's values rather than a decoding error, and are kept | **pipeline + QC** |
| 146 | **An arm-level outcome override can be dead and look live.** 9.34's first draft put each cell's filled question and scale on its arm while the outcome named its own `var`. The arm override applies only where the arm supplies the item (the evnyh guard, ledger entry on `scale_for`), so all 1,259 rows shipped the outcome's placeholder "[the two-part question, ...]" with QC passing. Caught by the maker's own bracket count, not by QC. The validator now refuses arm-level `outcome_var`/`outcome_question`/`scale` when every outcome names its `var`; per-cell wording there goes in `items`. The checker then showed a second route: deleting one arm's `items` override shipped 302 placeholder rows, QC silent. So QC rule 21 now FAILS any condition or outcome holding a "[...]" (measured first: none of the 72 built files has one). Both mutation-tested. All 70 recipes still validate | **pipeline** |
| 147 | **One question cannot be one outcome when its arms answer different things.** 9.34 crosses question format (spend more/same/less, 1-3) with amount and period; built as one outcome, a direction code and a £ amount shared an outcome id, so an outcome-held-out split or per-outcome score would mix them. Split into two experiments by format (the DEL NGO donate/petition precedent). **A design with two answer types is two experiments** | **method** |
| 148 | **An assignment can run over more cells than the script exported.** DEL wave 4's `connectstorysplit` assigns 5 groups; the exported questionnaire has 4 items and group 5 answered no story variable (all 403 columns compared). Group 5 is excluded, not rendered as a "no story" condition: nothing records what it saw. The same wave's donation amount is `assign_treatment(4, ...)` in the script yet takes 5 values, the fifth appearing from 4 Oct: the script changed mid-fieldwork and the deposit holds the older one. **The data, not the exported script, says what was fielded** | **data** |
