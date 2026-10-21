#!/usr/bin/env python3
"""Derive the BBC half of 35M5CV's conjoint arms from the data.

`recipes/35M5CV_bbc.yaml` declares one arm per distinct (respondent, pair)
PAIR actually drawn. Same design and same traps as the Lodger conjoint
(`gen_35M5CV_lodger.py`), checked independently against this study's own
files rather than assumed to carry over — see that file's module docstring
for the general argument each point below restates briefly.

Hobolt, Leeper & Tilley, "Divided by the Vote: Affective Polarization in the
Wake of the Brexit Referendum" (BJPS 51(4):1476-1493), Harvard Dataverse
doi:10.7910/DVN/35M5CV, CC0 1.0. `bbc-data-raw.sav` (1,635 respondents),
`bbc-script.docx` (fielded instrument).

THE DESIGN — 7-ATTRIBUTE FORCED-CHOICE CONJOINT, 5 RANDOMISED PAIRS PER PERSON

Each respondent imagines appointing the next BBC Director General and is
shown 5 pairs of hypothetical applicants, each built from 7 independently-
randomised attributes per profile:

    name (11 levels, drawn once per respondent, no repeats across all 10
          profile slots -- confirmed by direct count: 0 of 1,635 respondents
          have a duplicate name across their 10 slots)
    age (7)   experience (4)   degree (4)   politics (3)   eu (3)
    occupation (5)
                                        = 37 levels, matches
                                          answer_key_35M5CV_bbc.csv

CONFIRMED TRAPS, checked directly against THIS study's own files:

  1. ATTRIBUTE ROW ORDER IS RANDOMISED PER RESPONDENT. `list_table =
     random_shuffle([1,2,3,4,5,6])` (script line 163) is drawn once before
     Pair 1 and reused unchanged for Pairs 2-5 (lines 367-368, 571-572,
     775-776, 979-980 are all `#list_table = ...`, commented out). Confirmed
     in the .sav: non-null for all 1,635 respondents, 647 distinct values,
     and only 3 of 1,635 draw the canonical [1,2,3,4,5,6] order. `col_1` here
     is ["Age","Experience","Degree","Politics","EU","Occupation"] -- a
     DIFFERENT order from the Lodger study's ["Age","Occupation",
     "Volunteering","Politics","EU","Hobby"], so `SHUFFLED_ATTRS` below is
     this study's own, not copied from the Lodger generator.
  2. NO ATTRIBUTE LABEL IS EVER SHOWN -- `<!--th>$row1_1</th-->` etc, all six
     rows, all five pairs, confirmed in this file too.
  3. THE OUTCOME IS CODED BY NAME. `QPAIR1..5` stores which of the 11 names
     was picked; confirmed exhaustively that it equals `name_seen1_t{t}` or
     `name_seen2_t{t}` and nothing else across all 8,175 pair instances.
     Resolved via a PER-ARM `response_recode`, same as the Lodger study.
  4. THE `politics` VARIABLE'S LABELS ARE SWAPPED here too:
     `politics_seen1_t1`'s column label is "Politics 2 - Pair 1" and
     `politics_seen2_t1`'s is "Politics 1 - Pair 1" -- checked directly in
     this .sav's metadata, independently of the Lodger file. Read by
     variable NAME throughout, never by label.
  5. `work_type` IS EXCLUDED FROM PERSONA. Four of its nine value labels are
     severed at exactly 120 characters in this file too (checked directly,
     not assumed identical to the Lodger file, though the labels are in
     fact byte-identical). Never asked by `bbc-script.docx` (grepped: zero
     hits).
  6. `Region_2GOR` code 12 ("Northern Ireland") has ZERO respondents in this
     file too (confirmed by direct count) and is NOT declared missing. Note
     this deposit's two files order Region_1/Region_2GOR DIFFERENTLY in the
     column list (Lodger: Region_2GOR, Region_1; BBC: Region_1,
     Region_2GOR) -- immaterial since both are looked up by name, but worth
     recording so a future reader does not mistake it for two schemes.
  7. NO RESPONDENT-LEVEL PARTY/BREXIT VARIABLE IS IN THE PERSONA, for the
     same reason as the Lodger study: the profile carries `politics` (party
     support) and `eu` (referendum side) as attributes of the applicant
     being judged.
  8. INCOME EXISTS (`Income_GrossPersonal`, 16 bands) -- included, same
     correction to the brief as the Lodger recipe.

ROW SHAPE — PAIR-LEVEL ONLY, 5 OUTCOMES (see `gen_35M5CV_lodger.py`'s
docstring for the full argument: `QPAIRt` is the only question asked per
pair, so there is no second, genuinely per-profile outcome to build a
profile-level row from). 8,175 = 1,635 x 5. Checked: 0 "Skipped"/"Not Asked"
on QPAIRt or any attribute column in this file.

Usage:
    uv run python scripts/gen_35M5CV_bbc.py --check
    uv run python scripts/gen_35M5CV_bbc.py --write
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import Any

import yaml

from micromotives_datasets.sources import spss

REPO = Path(__file__).resolve().parents[1]
RECIPE = REPO / "recipes" / "35M5CV_bbc.yaml"
DATA = REPO / "data" / "raw" / "35M5CV" / "bbc-data-raw.sav"

# `name` is the table header and is NOT part of the on-screen row shuffle.
# The other six ARE shuffled, in `list_table`'s own `col_1` order (script
# line 169): ["Age","Experience","Degree","Politics","EU","Occupation"].
SHUFFLED_ATTRS = ["age", "experience", "degree", "politics", "eu", "occupation"]
ATTRS = ["name", *SHUFFLED_ATTRS]

SENTINELS: dict[str, set[int]] = {"name": {98, 99}} | {a: {8, 9} for a in SHUFFLED_ATTRS}

KEY_VARS = [f"{a}_seen1_t1" for a in ATTRS] + [f"{a}_seen2_t1" for a in ATTRS]

PREAMBLE = (
    "Imagine that you are deciding who to appoint as the next Director General "
    "of the BBC. You have received the following information about two "
    "applicants and need to make a decision between them.\n\nPlease read this "
    "information carefully:"
)
_CHOICE_Q = (
    "Which of the two applicants would you prefer as the next Director General "
    "of the BBC? 1 means the applicant listed first above; 2 means the "
    "applicant listed second above."
)


def _condition_vars(t: int) -> list[str]:
    return [f"{a}_seen1_t{t}" for a in ATTRS] + [f"{a}_seen2_t{t}" for a in ATTRS]


def _attribute_order(raw: Any) -> list[int]:
    """This respondent's own on-screen order for the 6 shuffled attribute rows."""
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
51(4):1476-1493, doi:10.1017/S0007123420000125 (paper; the DEPOSIT's own
licence, which governs this build, is CC0 1.0 as above). Harvard Dataverse
doi:10.7910/DVN/35M5CV. One of six datasets in this deposit (README.md);
this recipe covers the "BBC" conjoint only (the "Lodger" conjoint is
`recipes/35M5CV_lodger.yaml`). Fielded by YouGov UK, 30-31 October 2017 (the
.sav's own `respdate`, min/max). 1,635 respondents.

Deposit contents used: `bbc-data-raw.sav` (SPSS, value labels intact),
`bbc-script.docx` (fielded instrument, converted with
`textutil -convert txt` to read it), `bbc-analysis-cleaning.R` (the
depositors' own reshape, whose two `stopifnot`s this generator's row counts
agree with), `bbc-analysis.Rmd` (SI source).

See `scripts/gen_35M5CV_bbc.py`'s module docstring for the full account of
every trap checked, independently against this study's own files (attribute-
row order randomisation, the hidden-label table, the name-coded outcome, the
swapped politics labels, work_type, Region_2GOR's NI code, and the
respondent-level party/Brexit exclusion). Row shape: PAIR-level only
(8,175 = 1,635 x 5) -- `QPAIRt` is the only question asked per pair.

PERSONA

age <- Age (raw years; -9/-8 sentinels). gender <- Gender (1 Male/2 Female;
8/9). region <- Region_2GOR (11 populated GB regions, 1-11; code 12
"Northern Ireland" has ZERO respondents here too and is NOT declared
missing, per ledger #101; code 13 "Non UK & Invalid" IS declared missing).
social_grade <- SocialGrade (6-level A/B/C1/C2/D/E; 7 "Refused"/8
"Unknown"/98/99 declared missing) -- checked independently in this file
that SocialGrade and the coarser SocialGrade_2 cross-tabulate with ZERO
off-diagonal cells, so this is not the QQM5MC personal-vs-chief-income-
earner trap. education <- Education_Level (18-level UK ladder; 19/20/98/99
declared missing). income <- Income_GrossPersonal (16 bands; 15/16/98/99
declared missing). employment <- Work_status (8 levels; 98/99 declared
missing).

work_type IS EXCLUDED: four of nine value labels severed at 120 characters
in this file (checked directly), and it is a YouGov standing-panel profile
variable `bbc-script.docx` never asks (grepped: zero hits).

NO RESPONDENT-LEVEL PARTY OR BREXIT VARIABLE IS IN THE PERSONA: Voted2015,
Vote2015R, VoteEURef, Voted2017, Vote2017, VotingIntention, partyid_2017,
rl2, rl3, rl4 are all excluded -- the profile itself carries `politics` and
`eu` as attributes of the applicant being judged, so the respondent's own
party/Brexit position would sit in the outcome's own domain. Same ruling as
the Lodger recipe and as EFXNLX's `eu_referendum_vote` removal
(2026-10-02).

No ethnicity, marital status, religion or household size exists in this
file (grepped all 167 column names). Income DOES exist, contrary to the
brief's blanket claim, same correction as the Lodger recipe.

WORDS WE ADDED, AND WHY

`shared_context` ("You are taking part in an online survey run by YouGov UK
on 30-31 October 2017.") is composed from this file's own `respdate` (min
2017-10-30, max 2017-10-31) -- a different fielding window from the Lodger
study, confirmed independently rather than copied.

Each outcome's `question` keeps the fielded stem verbatim ("Which of the two
applicants would you prefer as the next Director General of the BBC?") and
adds the same first/second-listed disambiguation clause as the Lodger
recipe, for the same reason (a nominal Scale cannot carry per-arm-varying
option labels; the two names differ by arm, screen position does not).

JUDGEMENT CALLS AND OPEN UNCERTAINTIES

  1. Attribute-row order (list_table) reproduced per (respondent, pair) from
     the start. Checked, not assumed: non-null for all 1,635 respondents,
     only 3 draw the canonical order.
  2. Row shape is pair-level only, same argument as the Lodger recipe.
  3. QC rule 5 is expected to WARN "nested, not crossed" on most or all of
     the 14 declared factors, same shape as EFXNLX and the Lodger recipe.
  4. The persona-vocabulary crosswalk does not yet exist for this UK corpus,
     so QC rule 14 is expected to warn on unmapped persona labels.
"""


def build_recipe() -> dict[str, Any]:
    return {
        "study_id": "35M5CV",
        "experiment": "bbc",
        "source": "dataverse",
        "title": "Divided by the Vote: Affective Polarization in the Wake of the Brexit "
        "Referendum (BBC conjoint)",
        "data_file": "bbc-data-raw.sav",
        "licence": "CC0 1.0 Universal, stated on the Harvard Dataverse deposit for "
        "doi:10.7910/DVN/35M5CV.",
        "comparable_to_socsci210": False,
        "notes": NOTES,
        "condition": {
            "source_vars": KEY_VARS,
            "factors": [f"{a}_A" for a in ATTRS] + [f"{a}_B" for a in ATTRS],
            "considered_and_rejected": {},
            "shared_context": "You are taking part in an online survey run by YouGov UK "
            "on 30-31 October 2017.",
            "arms": build_arms(),
        },
        "outcomes": build_outcomes(),
        "response_recode": {1: 1, 2: 2},
        "missing_codes": [98, 99],
        "persona_map": {
            "age": "Age",
            "gender": "Gender",
            "region": "Region_2GOR",
            "social_grade": "SocialGrade",
            "education": "Education_Level",
            "income_personal": "Income_GrossPersonal",
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
