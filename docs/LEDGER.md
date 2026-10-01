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
QC-clean recipes with verbatim-checked arm text, explicit uncertainty lists, and numeric
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
| 38 | `z358z` rebuilt to 4 arms on the extended schema: crosscheck **PASS on all four condition indices** (2426/2728/2697/2594, exact and in order) plus `n_rows`, participants and the full response distribution. The `DOV_OPTION` paragraph the maker had omitted **did exist** in the questionnaire and is restored verbatim | one-off, resolved | `recipes/z358z.yaml`; first study to exercise `source_vars`/`raw_values` end to end |

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
