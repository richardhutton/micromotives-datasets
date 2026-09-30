# Failure ledger

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

## Open items

- Only `RO1` of `rpw4u`'s ~15 experiments is built. The rest are mechanical repeats.
- Persona categories are still passed through raw (`Education: Bachelor's degree or
  higher`). The crosswalk to one shared vocabulary (master doc §6) is unbuilt — this
  is the intended first Jev task.
- `.doc` conversion uses macOS `textutil`; needs `antiword`/LibreOffice elsewhere.
  Arm text is committed into the recipe, so the melt and its tests stay unaffected.
