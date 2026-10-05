#!/usr/bin/env python3
"""Derive the LODGER half of 35M5CV's conjoint arms from the data.

`recipes/35M5CV_lodger.yaml` declares one arm per distinct (respondent, pair)
PAIR actually drawn, same shape as `EFXNLX` (see `gen_EFXNLX.py`'s docstring
for the general pattern this copies). This file writes the WHOLE recipe, not
just `condition.arms`/`outcomes` — there was no hand-authored draft to extend,
so the generator is the sole authority for every generated field and the
constants below (persona map, notes, licence...) are the authority for
everything else.

Hobolt, Leeper & Tilley, "Divided by the Vote: Affective Polarization in the
Wake of the Brexit Referendum" (BJPS 51(4):1476-1493), Harvard Dataverse
doi:10.7910/DVN/35M5CV, CC0 1.0. `lodger-data-raw.sav` (1,669 respondents),
`lodger-script.docx` (fielded instrument).

THE DESIGN — 7-ATTRIBUTE FORCED-CHOICE CONJOINT, 5 RANDOMISED PAIRS PER PERSON

Each respondent imagines renting a spare room and is shown 5 pairs of
hypothetical lodgers ("Pair 1".."Pair 5", each its own `{page IntroN}`), each
built from 7 independently-randomised attributes per profile:

    name (11 levels, drawn once per respondent, no repeats across all 10
          profile slots -- script line 39's own check comment)
    age (7)   occupation (4)   volunteer (5)   politics (3)   eu (3)
    hobby (5)
                                        = 38 levels, matches
                                          answer_key_35M5CV_lodger.csv

CONFIRMED TRAPS (all checked directly against `lodger-script.docx` and the
.sav, not assumed from the EFXNLX precedent that flagged them):

  1. ATTRIBUTE ROW ORDER IS RANDOMISED PER RESPONDENT, exactly like EFXNLX.
     `list_table = random_shuffle([1,2,3,4,5,6])` (script line 164) is drawn
     ONCE before Pair 1 and reused unchanged for Pairs 2-5 (lines 377-378,
     586-587, 797-798, 1005-1006 are all `#list_table = ...`, commented out --
     i.e. NOT redrawn). `list_table` is a column in the .sav: non-null for all
     1,669 respondents, a string-encoded permutation of 1..6, 641 distinct
     values, and only 4 of 1,669 respondents happen to draw the canonical
     [1,2,3,4,5,6] order (binomial-plausible: 1669/720 ~= 2.3). The table's
     NAME column (`name_seen1/2_tN`) is NOT part of this shuffle -- it is
     always the header, drawn and assigned separately (lines 120-130) -- so
     only the 6 attributes in `SHUFFLED_ATTRS` below are reordered.
  2. NO ATTRIBUTE LABEL IS EVER SHOWN. The table's left-hand label column
     (`row{n}_1`, e.g. "Age") is wrapped in an HTML comment in EVERY pair's
     markup (`<!--th>$row1_1</th-->`, lines 272, 283, ... all six, all five
     pairs, both this file and `bbc-script.docx`) -- the respondent saw two
     bare columns of value text under the two candidates' names, nothing
     else. This is NOT the EFXNLX shape (which DOES render a label prefix);
     rendering one here would be stimulus text no respondent read.
  3. THE OUTCOME IS CODED BY NAME, NOT BY SCREEN POSITION. `QPAIR1..5` stores
     which of the 11 names was picked (value-labelled 1..11 = James..Jenny,
     98/99 = Skipped/Not Asked) -- confirmed directly: for every respondent
     and pair, `QPAIRt` equals either `name_seen1_t{t}` or `name_seen2_t{t}`
     and never anything else (checked exhaustively, 0 mismatches across all
     8,345 pair instances). `lodger-analysis-cleaning.R` recovers the 0/1
     "was this profile picked" indicator the same way
     (`outcomeA <- as.integer(outcome == nameA)`). Resolved here via a
     PER-ARM `response_recode` (see `build_arms`), because the raw code's
     MEANING (which of the two profiles it names) depends on which two names
     this specific arm drew -- a study-level or outcome-level map cannot
     express that, an arm-level one can (`recipe.py`'s `recode_for`:
     item -> arm -> outcome -> study, and every arm here sets its own).
  4. THE `politics` VARIABLE'S LABELS ARE SWAPPED. `politics_seen1_t1`'s
     *column label* is "Politics 2 - Pair 1" and `politics_seen2_t1`'s is
     "Politics 1 - Pair 1" -- checked directly in the .sav metadata, the
     opposite of every other attribute (`age_seen1_t1` -> "Age 1 - Pair 1",
     etc). The RENDER is unaffected: the table always shows `_seen1` under
     the first name and `_seen2` under the second, by variable NAME, and
     this generator reads columns by name throughout. Only reading the
     LABEL to decide which side a value belongs to would invert politics.
  5. `work_type` IS EXCLUDED FROM PERSONA (ledger #111). Four of its nine
     value labels are severed at exactly 120 characters -- confirmed by
     direct length check -- and it is a YouGov standing-panel profile
     variable; `lodger-script.docx` never asks it (grepped the full
     converted text for "work_type", "occupation" outside the conjoint
     block, and NRS-style wording: zero hits).
  6. `Region_2GOR` code 12 ("Northern Ireland") has ZERO respondents in this
     file (confirmed by direct count: codes 1-11 sum to 1,669 minus
     sentinels) -- a REAL region with no rows, so it is NOT declared a
     missing code (ledger #101's fix). Code 13 ("Non UK & Invalid") IS a
     non-answer by its own label and is declared missing.
  7. NO RESPONDENT-LEVEL PARTY/BREXIT VARIABLE IS IN THE PERSONA. The profile
     itself carries `politics` (2017 party support) and `eu` (EU referendum
     side) as attributes of the CANDIDATE being judged, so a persona field
     naming the RESPONDENT's own `partyid_2017`/`Vote2017`/`VoteEURef`/
     `rl2`/`rl3`/`rl4` would sit in the exact domain of two of the outcome's
     own attributes -- the same ruling that removed `eu_referendum_vote`
     from `EFXNLX`, applied here more directly because the profile literally
     varies party support and EU-referendum side, not merely EU policy
     terms. Excluded.
  8. INCOME EXISTS, contrary to the brief's "no income" claim: `Income_
     GrossPersonal`, 16 bands, system-missing on 200 of 1,669 (no code),
     98/99 sentinels not observed in this field (0 occurrences). Included.
     No ethnicity/marital status/religion/household size column exists
     anywhere in the 170-column file (grepped for all four) -- the brief
     was right about those four, just not income.

ROW SHAPE — PAIR-LEVEL ONLY, 5 OUTCOMES, NO PROFILE-LEVEL ROWS

Unlike `EFXNLX` (which has a genuine per-profile acceptability item riding
alongside the pair-level choice), this study asks exactly ONE question per
pair (`QPAIRt`). There is no second, per-profile outcome variable to build a
profile-level row from -- the depositors' own profile-level reshape exists
only to feed `cj()`, which needs one row per (pair, side) to estimate an
AMCE; it answers no question a respondent was actually asked. So this
recipe's row count is the PAIR-level target (8,345 = 1,669 x 5), not the
profile-level one (16,690) the brief also quotes -- that second number
describes the depositors' intermediate reshape, not a row this project
builds. Checked: 0 "Skipped"/"Not Asked" on QPAIRt or any attribute column.

Usage:
    uv run python scripts/gen_35M5CV_lodger.py --check
    uv run python scripts/gen_35M5CV_lodger.py --write
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import Any

import yaml

from micromotives_datasets.sources import spss

REPO = Path(__file__).resolve().parents[1]
RECIPE = REPO / "recipes" / "35M5CV_lodger.yaml"
DATA = REPO / "data" / "raw" / "35M5CV" / "lodger-data-raw.sav"

# `name` is the table header, drawn once per respondent and NOT part of the
# on-screen row shuffle. The other six ARE shuffled, in `list_table`'s own
# `col_1` order (script line 170): ["Age","Occupation","Volunteering",
# "Politics","EU","Hobby"].
SHUFFLED_ATTRS = ["age", "occupation", "volunteer", "politics", "eu", "hobby"]
ATTRS = ["name", *SHUFFLED_ATTRS]

# Sentinel codes, by attribute: name/QPAIR use two-digit sentinels (11 real
# levels), every other attribute uses single-digit ones. Confirmed by direct
# count: zero occurrences of any of these in this deposit, but the generator
# guards against them anyway rather than assuming a re-fetched deposit stays
# as clean.
SENTINELS: dict[str, set[int]] = {"name": {98, 99}} | {a: {8, 9} for a in SHUFFLED_ATTRS}

KEY_VARS = [f"{a}_seen1_t1" for a in ATTRS] + [f"{a}_seen2_t1" for a in ATTRS]

PREAMBLE = (
    "Imagine that you have a spare room that you want to rent out to a lodger. "
    "You have received the following information about two possible lodgers "
    "and need to make a decision between them.\n\nPlease read this information "
    "carefully:"
)
_CHOICE_Q = (
    "Which of the two lodgers would you prefer? 1 means the lodger listed "
    "first above; 2 means the lodger listed second above."
)


def _condition_vars(t: int) -> list[str]:
    return [f"{a}_seen1_t{t}" for a in ATTRS] + [f"{a}_seen2_t{t}" for a in ATTRS]


def _attribute_order(raw: Any) -> list[int]:
    """This respondent's own on-screen order for the 6 shuffled attribute rows.

    See `gen_EFXNLX.py`'s `_attribute_order` for the general argument for why
    this is resolved here (at generation time, one arm = one (respondent,
    pair) instance) rather than via `condition.line_order_vars` (which exists
    for several respondents sharing one declared arm).
    """
    order = ast.literal_eval(raw)
    if sorted(order) != list(range(1, 7)):
        raise ValueError(f"list_table is not a permutation of 1..6: {raw!r}")
    return [int(x) for x in order]


def build_arms() -> list[dict[str, Any]]:
    """Every distinct (respondent, pair) 14-attribute PAIR actually shown."""
    ds = spss.read(DATA)
    value_labels = {a: dict(ds.value_labels.get(f"{a}_seen1_t1") or {}) for a in ATTRS}

    arms: list[dict[str, Any]] = []
    seen: dict[tuple[int, ...], int] = {}

    for t in range(1, 6):
        cols = _condition_vars(t)
        for _, row in ds.df.iterrows():
            codes = []
            bad = False
            for col, a in zip(cols, ATTRS + ATTRS, strict=True):
                value = row[col]
                if value is None or value != value:  # NaN
                    bad = True
                    break
                code = int(float(value))
                if code in SENTINELS[a]:
                    bad = True
                    break
                codes.append(code)
            if bad:
                continue
            key = tuple(codes)
            if key in seen:
                continue
            seen[key] = len(arms)
            codes_a, codes_b = codes[: len(ATTRS)], codes[len(ATTRS) :]
            order = _attribute_order(row["list_table"])

            def block(side_codes: list[int], order: list[int] = order) -> str:
                name = value_labels["name"][side_codes[0]]
                lines = [name]
                # side_codes[0] is name; side_codes[1:] are SHUFFLED_ATTRS in
                # declared order. Screen slot p shows SHUFFLED_ATTRS[order[p-1]-1].
                for slot in order:
                    a = SHUFFLED_ATTRS[slot - 1]
                    idx = 1 + SHUFFLED_ATTRS.index(a)
                    lines.append(f"- {value_labels[a][side_codes[idx]]}")
                return "\n".join(lines)

            factors = {}
            for a, code in zip(ATTRS, codes_a, strict=True):
                factors[f"{a}_A"] = value_labels[a][code]
            for a, code in zip(ATTRS, codes_b, strict=True):
                factors[f"{a}_B"] = value_labels[a][code]

            text = f"{PREAMBLE}\n\n{block(codes_a)}\n\n{block(codes_b)}"
            name_a_code, name_b_code = codes_a[0], codes_b[0]
            arms.append(
                {
                    "raw_values": dict(zip(KEY_VARS, codes, strict=True)),
                    "condition_num": len(arms),
                    "factors": factors,
                    "text": text,
                    # Per-arm, because the raw QPAIRt code names a PERSON, and
                    # which side that name sits on is a property of this one
                    # (respondent, pair) draw -- see trap #3 above.
                    "response_recode": {name_a_code: 1, name_b_code: 2},
                }
            )
    return arms


def build_outcomes() -> list[dict[str, Any]]:
    outcomes: list[dict[str, Any]] = []
    for t in range(1, 6):
        outcomes.append(
            {
                "var": f"QPAIR{t}",
                "task_num": t - 1,
                "question": _CHOICE_Q,
                "scale": {"min": 1, "max": 2, "nominal": True},
                "condition_vars": _condition_vars(t),
            }
        )
    return outcomes


NOTES = """\
Hobolt, Leeper & Tilley, "Divided by the Vote: Affective Polarization in the
Wake of the Brexit Referendum", British Journal of Political Science
51(4):1476-1493, doi:10.1017/S0007123420000125 (paper, CC BY where stated;
the DEPOSIT's own licence, which governs this build, is CC0 1.0 as above).
Harvard Dataverse doi:10.7910/DVN/35M5CV. One of six datasets in this
deposit (README.md); this recipe covers the "Lodger" conjoint only (the
"BBC" conjoint is `recipes/35M5CV_bbc.yaml`; BES/Tracker/YouGov/Sky are out
of scope -- none is a conjoint). Fielded by YouGov UK, 24-25 October 2017
(the .sav's own `respdate`, min/max). 1,669 respondents.

Deposit contents used: `lodger-data-raw.sav` (SPSS, value labels intact),
`lodger-script.docx` (fielded instrument, converted with
`textutil -convert txt` to read it), `lodger-analysis-cleaning.R` (the
depositors' own reshape, whose two `stopifnot`s this generator's row counts
agree with), `lodger-analysis.Rmd` (SI source).

See `scripts/gen_35M5CV_lodger.py`'s module docstring for the full account
of every trap checked (attribute-row order randomisation, the hidden-label
table, the name-coded outcome, the swapped politics labels, work_type,
Region_2GOR's NI code, and the respondent-level party/Brexit exclusion) --
not repeated here to avoid the two drifting apart. Row shape: PAIR-level
only (8,345 = 1,669 x 5), because `QPAIRt` is the only question asked per
pair; there is no second, genuinely per-profile outcome variable the way
EFXNLX's QB2gridA/B are.

PERSONA

age <- Age (raw years; -9 "Not Asked"/-8 "Skipped" sentinels, matching
EFXNLX's age field exactly). gender <- Gender (1 Male/2 Female; 8/9
sentinels). region <- Region_2GOR (11 populated GB regions, 1-11; code 12
"Northern Ireland" has ZERO respondents here -- confirmed by direct count
-- and is NOT declared missing, per ledger #101; code 13 "Non UK & Invalid"
IS declared missing on semantic grounds). Region_1 (5 coarse bands, no NI
possible by construction) was considered and rejected in favour of the
richer GOR scheme, matching the EFXNLX/QQM5MC precedent. social_grade <-
SocialGrade (6-level A/B/C1/C2/D/E; codes 7 "Refused"/8 "Unknown" plus 98/99
declared missing). Checked this is not the QQM5MC personal-vs-chief-income-
earner trap: SocialGrade and the coarser SocialGrade_2 (2-level ABC1/C2DE)
cross-tabulate with ZERO off-diagonal cells, so they are the same grading at
two grains and the finer one is simply used. education <- Education_Level
(18-level UK ladder; 19 "Don't know"/20 "Prefer not to say"/98/99 declared
missing) -- preferred over the coarser, non-standard Education_Level_Grouped.
income <- Income_GrossPersonal (16 bands; 15 "Don't know"/16 "Prefer not to
answer"/98/99 declared missing, plus 200 rows of plain system-missing with
no code, handled automatically). employment <- Work_status (8 levels
including a genuine "Other"; 98/99 declared missing).

work_type IS EXCLUDED (see generator docstring trap #5): four of nine value
labels severed at 120 characters, and it is a YouGov standing-panel profile
variable this instrument never asks (grepped the full converted
questionnaire for every distinctive phrase and for "work_type"/
"occupation"/NRS-style wording outside the conjoint block: zero hits).

NO RESPONDENT-LEVEL PARTY OR BREXIT VARIABLE IS IN THE PERSONA (see trap #7):
Voted2015, Vote2015R, VoteEURef, Voted2017, Vote2017, VotingIntention,
partyid_2017, rl2, rl3, rl4 are all excluded. The profile itself carries
`politics` (2017 party support) and `eu` (EU referendum side) as attributes
of the candidate being judged, so telling the model the RESPONDENT's own
party/Brexit position would hand it the outcome's own domain -- the same
ruling (2026-10-02) that removed `eu_referendum_vote` from EFXNLX, and a
more direct case here because the profile varies party support and EU side
literally, not just EU-negotiation terms.

No ethnicity, marital status, religion or household size exists in this
file (grepped all 170 column names for every synonym: zero hits). Income
DOES exist, contrary to the brief's blanket claim -- corrected above rather
than silently matching the brief.

WORDS WE ADDED, AND WHY

`shared_context` below ("You are taking part in an online survey run by
YouGov UK on 24-25 October 2017.") is composed from the .sav's own
`respdate` field (min 2017-10-24, max 2017-10-25), not transcribed from the
instrument, which has no top-level welcome text before the conjoint block.
It is true for every respondent regardless of arm, carries no sequence
position, and is deliberately minimal -- we do not know from this deposit
alone whether this was an "Omnibus" panel wave or something else, so the
sentence does not claim it.

Each outcome's `question` keeps the fielded stem verbatim ("Which of the two
lodgers would you prefer?") and adds one clause -- "1 means the lodger listed
first above; 2 means the lodger listed second above." -- because a `nominal`
Scale must not carry endpoint labels (`recipe.py`'s own validator), and the
two option labels the respondent actually saw were the two candidates' own
NAMES, which differ by arm and so cannot sit in one fixed Outcome.question.
Describing them by screen POSITION (first/second) is accurate for every arm
alike: the table always renders `name_seen1_tN` first (left) and
`name_seen2_tN` second (right), by construction (`row_1`/`row_2` wiring, not
by any declared order), and the per-arm `response_recode` maps response 1 to
whichever name sat in `name_seen1_tN` for that specific arm.

JUDGEMENT CALLS AND OPEN UNCERTAINTIES

  1. Attribute-row order (list_table) is reproduced per (respondent, pair)
     from the start, having read the EFXNLX post-mortem before writing a
     line of this generator. Checked, not assumed: `list_table` exists in
     this .sav, is non-null for all 1,669 respondents, and only 4 of them
     drew the canonical order.
  2. Row shape is pair-level only (see above) -- the profile-level number
     the brief quotes (16,690) is the depositors' cj()-feeding reshape, not
     a row this project builds, because there is no second, genuinely
     per-profile question.
  3. QC rule 5 (minimal pairs) is expected to WARN "nested, not crossed" on
     most or all of the 14 declared factors, same shape as EFXNLX and for
     the same reason: the attribute space (11x7x4x5x3x3x5 per side) is far
     larger than the 8,345 pairs actually drawn, so two pairs agreeing on 13
     of 14 dimensions by chance is not expected. Reported, not suppressed.
  4. The persona-vocabulary crosswalk does not yet exist for this UK corpus
     (per the brief), so QC rule 14 is expected to warn that persona labels
     (e.g. "Working full time (30 or more hours per week)") are unmapped --
     expected, not a defect in this recipe.
"""


def build_recipe() -> dict[str, Any]:
    return {
        "study_id": "35M5CV",
        "experiment": "lodger",
        "source": "dataverse",
        "title": "Divided by the Vote: Affective Polarization in the Wake of the Brexit "
        "Referendum (Lodger conjoint)",
        "data_file": "lodger-data-raw.sav",
        "licence": "CC0 1.0 Universal, stated on the Harvard Dataverse deposit for "
        "doi:10.7910/DVN/35M5CV.",
        "comparable_to_socsci210": False,
        "notes": NOTES,
        "condition": {
            "source_vars": KEY_VARS,
            "factors": [f"{a}_A" for a in ATTRS] + [f"{a}_B" for a in ATTRS],
            "considered_and_rejected": {},
            "shared_context": "You are taking part in an online survey run by YouGov UK "
            "on 24-25 October 2017.",
            "arms": build_arms(),
        },
        "outcomes": build_outcomes(),
        # Never exercised: every arm sets its own response_recode (see trap #3
        # above), which `recipe.py`'s `recode_for` prefers unconditionally.
        # Required by the schema regardless.
        "response_recode": {1: 1, 2: 2},
        "missing_codes": [98, 99],
        "persona_map": {
            "age": "Age",
            "gender": "Gender",
            "region": "Region_2GOR",
            "social_grade": "SocialGrade",
            "education": "Education_Level",
            "income": "Income_GrossPersonal",
            "employment": "Work_status",
        },
        "persona_missing": {
            "Age": [-9, -8],
            "Gender": [8, 9],
            "Region_2GOR": [13, 98, 99],
            "SocialGrade": [7, 8, 98, 99],
            "Education_Level": [19, 20, 98, 99],
            "Income_GrossPersonal": [15, 16, 98, 99],
            "Work_status": [98, 99],
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="compare against the recipe")
    ap.add_argument("--write", action="store_true", help="(re)write the whole recipe")
    args = ap.parse_args()

    generated_arms = build_arms()
    generated_outcomes = build_outcomes()
    print(f"generated {len(generated_arms):,} arms, {len(generated_outcomes)} outcomes")

    if args.write:
        recipe = build_recipe()
        RECIPE.write_text(yaml.safe_dump(recipe, sort_keys=False, allow_unicode=True, width=100))
        print(f"wrote {RECIPE.relative_to(REPO)}")
        return 0

    if not RECIPE.exists():
        print(f"{RECIPE} does not exist yet -- run with --write")
        return 1
    recipe = yaml.safe_load(RECIPE.read_text())
    ok = True
    current_arms = recipe["condition"]["arms"]
    current_outcomes = recipe["outcomes"]
    if generated_arms != current_arms:
        ok = False
        print("ARMS DIFFER")
        for i, (g, c) in enumerate(zip(generated_arms, current_arms, strict=False)):
            if g != c:
                print(f"  first difference at arm {i}:\n    generated {g}\n    recipe    {c}")
                break
    if generated_outcomes != current_outcomes:
        ok = False
        print("OUTCOMES DIFFER")
    if ok:
        print("IDENTICAL — the recipe is exactly what this file derives")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
