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

## Open items

- Only `RO1` of `rpw4u`'s ~15 experiments is built. The rest are mechanical repeats.
- Persona categories are still passed through raw (`Education: Bachelor's degree or
  higher`). The crosswalk to one shared vocabulary (master doc §6) is unbuilt — this
  is the intended first Jev task.
- `.doc` conversion uses macOS `textutil`; needs `antiword`/LibreOffice elsewhere.
  Arm text is committed into the recipe, so the melt and its tests stay unaffected.
