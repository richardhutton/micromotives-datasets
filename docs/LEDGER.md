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

## Open items

- Only `RO1` of `rpw4u`'s ~15 experiments is built. The rest are mechanical repeats.
- Persona categories are still passed through raw (`Education: Bachelor's degree or
  higher`). The crosswalk to one shared vocabulary (master doc §6) is unbuilt — this
  is the intended first Jev task.
- `.doc` conversion uses macOS `textutil`; needs `antiword`/LibreOffice elsewhere.
  Arm text is committed into the recipe, so the melt and its tests stay unaffected.
