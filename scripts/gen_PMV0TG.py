#!/usr/bin/env python3
"""Derive PMV0TG's UK conjoint arms from the data, rather than hand-typing them.

PMV0TG (CANDOUR, Duch et al., 13-country COVID-19 vaccine-allocation conjoint)
ships ONE file, `nbh_clean_conjoint_global.tab`: 248,576 rows, tab-delimited,
codes already resolved to text (no `.sav`/`.dta`, so `value_labels` is empty —
see `sources/delimited.py`). Filtered to `country == "UK"` this is 18,640 rows,
1,165 respondents, exactly 16 rows each (8 rounds x 2 candidate profiles).

That file is LONG at the PROFILE level (one row per candidate, two rows per
round) and the pipeline's melt (`pipeline.build.build_rows`) needs, for an
8-attribute forced choice between two profiles, a row that holds BOTH
profiles' attributes at once (`condition.source_vars` is looked up by column
name on a single `ds.df` row). So this script does two things, not one:

  1. RESHAPE: pivot the 18,640 UK profile-rows into ONE ROW PER RESPONDENT
     (1,165 rows), with one block of 11 columns per round (r=1..8):
     `{attr}_A_r{r}`, `{attr}_B_r{r}` (5 attributes x 2 sides = 10 numeric
     codes) and `ans_code_r{r}` (1=Person A, 2=Person B). This is the SAME
     shape as `b87sm`'s within-subject vignette design, not `EFXNLX`'s (there
     the deposit was already wide per respondent; here it is not). Persona
     fields and `weights` are constant within respondent (verified) and so
     appear once. Written to
     `data/raw/PMV0TG/nbh_clean_conjoint_UK_wide.csv` — a DERIVED file, not a
     second copy of the deposit — which becomes the recipe's `data_file`.
     One row of this file = one respondent, so the pipeline's
     `participant_id = f"{study_id}:{idx}"` is correct: all 8 rounds of one
     person share one participant_id. Pivoting to one-row-per-ROUND instead
     would have given each of a respondent's 8 rounds a DIFFERENT idx and
     hence a different synthetic participant_id, silently breaking
     held-out-split integrity for no reason visible in QC.

  2. DERIVE ARMS: every distinct 10-attribute (Person A x Person B) profile
     pair actually drawn, deduplicated across all 8 rounds x 1,165
     respondents = 9,320 round-instances (9,272 distinct; 48 "coincidental"
     repeats — see the recipe's own notes for why that is safe here, unlike
     `EFXNLX` where a repeat would have risked the wrong position-dependent
     preamble: this design has no position-dependent text at all, every
     round renders identically bar the attribute values).

Attribute CODES are manufactured here, 1-based, in `codebook.pdf`'s own table
order (reference level first, asterisked) — the delimited file carries no
codes of its own, only the resolved text. Verified before writing this file:
the UK data's set of distinct strings for each of the 5 attributes equals
EXACTLY `ATTR_LEVELS` below, so the numbering is total and uncontested.

    uv run python scripts/gen_PMV0TG.py --check   # agree with the recipe?
    uv run python scripts/gen_PMV0TG.py --write   # regenerate wide CSV + arms/outcomes
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
RECIPE = REPO / "recipes" / "PMV0TG.yaml"
RAW = REPO / "data" / "raw" / "PMV0TG" / "nbh_clean_conjoint_global.tab"
WIDE = REPO / "data" / "raw" / "PMV0TG" / "nbh_clean_conjoint_UK_wide.csv"

N_ROUNDS = 8

# The 5 attributes, in the instrument's own on-screen table order (uk_survey.txt
# Q5.2 / the PDF preview, both blank but with this exact row-label order; it
# matches the data file's own column order too). ROW LABEL is the instrument's
# left-column text verbatim (uk_survey.txt lines 271-284 / PDF page 7).
ATTRS: list[tuple[str, str]] = [
    ("vulnerability", "Risk of COVID-19 related death"),
    ("transmission", "Risk of catching and transmitting the COVID-19 virus"),
    ("income", "Income level"),
    ("occupation", "Occupation status"),
    ("age_category", "Age category"),
]

# Level text verbatim from codebook.pdf's own attribute tables, in the order it
# prints them (reference level, asterisked, FIRST in every case). This is the
# authority for the baseline, per the brief: the answer key's own .tex states
# no baselines, only codebook.pdf does.
ATTR_LEVELS: dict[str, list[str]] = {
    "vulnerability": [
        "Average risk of COVID-19 death",
        "Moderate (Twice the average risk of COVID-19 death)",
        "High (Five times the average risk of COVID-19 death)",
    ],
    "transmission": [
        "Average risk of catching and transmitting the COVID-19 virus",
        "Moderate risk (Twice the average risk of catching and transmitting the COVID-19 virus)",
        "High risk (Five times the average risk of catching and transmitting the COVID-19 virus)",
    ],
    "income": [
        "Lowest 20% income level",
        "Average income level",
        "Highest 20% income level",
    ],
    "occupation": [
        "Not working",
        "Non-Key worker: Can work at home",
        "Non-Key worker: Cannot work at home",
        "Key worker: Education and childcare",
        "Key worker: Factory worker",
        "Key worker: Water and electricity service",
        "Key worker: Police and fire-fighting",
        "Key worker: Health and social care",
    ],
    "age_category": ["25 years old", "40 years old", "65 years old", "79 years old"],
}
CODE_OF: dict[str, dict[str, int]] = {
    attr: {level: i + 1 for i, level in enumerate(levels)} for attr, levels in ATTR_LEVELS.items()
}

PERSONA_COLS = ["age", "gender", "ideology", "ind_inc", "education"]

# Canonical column names: round 1's own, used as the generic `raw_values` /
# `condition.source_vars` keys regardless of which round's content an arm was
# first observed at — exactly EFXNLX's KEY_VARS pattern.
KEY_VARS = [f"{a}_A_r1" for a, _ in ATTRS] + [f"{a}_B_r1" for a, _ in ATTRS]


def _round_cols(r: int) -> list[str]:
    return [f"{a}_A_r{r}" for a, _ in ATTRS] + [f"{a}_B_r{r}" for a, _ in ATTRS]


def load_uk() -> pd.DataFrame:
    df = pd.read_csv(RAW, sep="\t", low_memory=False)
    uk = df[df["country"] == "UK"].copy()
    if len(uk) != 18_640 or uk["id"].nunique() != 1_165:
        raise ValueError(
            f"UK filter drifted: {len(uk)} rows, {uk['id'].nunique()} ids "
            "(expected 18,640 / 1,165) — re-read the deposit before building"
        )
    counts = uk.groupby("id").size()
    if not (counts == 16).all():
        raise ValueError("not every UK respondent has exactly 16 rows (8 rounds x 2 candidates)")
    if not (uk["select"] == (uk["candidate"] == uk["ans"]).astype(int)).all():
        raise ValueError("select != (candidate == ans) somewhere — the forced-choice key is off")
    for attr, levels in ATTR_LEVELS.items():
        actual = set(uk[attr].unique())
        if actual != set(levels):
            raise ValueError(f"{attr}: data levels {actual} != codebook levels {set(levels)}")
    return uk


def build_wide(uk: pd.DataFrame) -> pd.DataFrame:
    """One row per respondent, 8 rounds' worth of columns each."""
    records: list[dict[str, Any]] = []
    for resp_id, grp in uk.groupby("id", sort=False):
        rounds = sorted(grp["person"].unique(), key=lambda p: int(p.replace("person", "")))
        if rounds != [f"person{r}" for r in range(1, N_ROUNDS + 1)]:
            raise ValueError(f"{resp_id}: rounds are not exactly person1..person{N_ROUNDS}")
        # Persona fields and weights are constant within respondent — verified
        # directly (see maker's report), asserted again here so a future
        # re-fetch that breaks it fails loudly rather than silently averaging.
        persona_vals = grp[PERSONA_COLS].drop_duplicates()
        if len(persona_vals) != 1:
            raise ValueError(f"{resp_id}: persona fields are not constant across rounds")
        rec: dict[str, Any] = {"id": resp_id, **persona_vals.iloc[0].to_dict()}

        for r in range(1, N_ROUNDS + 1):
            round_rows = grp[grp["person"] == f"person{r}"]
            a_row = round_rows[round_rows["candidate"] == "A"]
            b_row = round_rows[round_rows["candidate"] == "B"]
            if len(a_row) != 1 or len(b_row) != 1:
                raise ValueError(f"{resp_id} round {r}: not exactly one A and one B row")
            a_row, b_row = a_row.iloc[0], b_row.iloc[0]
            if a_row["ans"] != b_row["ans"]:
                raise ValueError(f"{resp_id} round {r}: A/B rows disagree on `ans`")
            for attr, _ in ATTRS:
                rec[f"{attr}_A_r{r}"] = CODE_OF[attr][a_row[attr]]
                rec[f"{attr}_B_r{r}"] = CODE_OF[attr][b_row[attr]]
            rec[f"ans_code_r{r}"] = 1 if a_row["ans"] == "A" else 2
        records.append(rec)

    wide = pd.DataFrame.from_records(records)
    expected_cols = 1 + len(PERSONA_COLS) + N_ROUNDS * (2 * len(ATTRS) + 1)
    assert wide.shape == (1_165, expected_cols), wide.shape
    return wide


def build_arms(wide: pd.DataFrame) -> list[dict[str, Any]]:
    """Every distinct 10-attribute (Person A, Person B) pair actually drawn.

    Round-major, respondent-major within each round — same declared scan
    order as `gen_EFXNLX.py`, for the same reason: prose cannot pin an
    ordering, only a loop can.
    """
    arms: list[dict[str, Any]] = []
    seen: dict[tuple[int, ...], int] = {}

    for r in range(1, N_ROUNDS + 1):
        cols = _round_cols(r)
        for _, row in wide.iterrows():
            codes = [int(row[c]) for c in cols]
            key = tuple(codes)
            if key in seen:
                continue
            seen[key] = len(arms)
            codes_a, codes_b = codes[:5], codes[5:]

            def block(label: str, side_codes: list[int]) -> str:
                lines = [label]
                for (attr, row_label), code in zip(ATTRS, side_codes, strict=True):
                    text = ATTR_LEVELS[attr][code - 1]
                    lines.append(f"- {row_label}: {text}")
                return "\n".join(lines)

            factors = {}
            for (attr, _), code in zip(ATTRS, codes_a, strict=True):
                factors[f"{attr}_A"] = ATTR_LEVELS[attr][code - 1]
            for (attr, _), code in zip(ATTRS, codes_b, strict=True):
                factors[f"{attr}_B"] = ATTR_LEVELS[attr][code - 1]

            text = f"{block('Person A', codes_a)}\n\n{block('Person B', codes_b)}"
            arms.append(
                {
                    "raw_values": dict(zip(KEY_VARS, codes, strict=True)),
                    "condition_num": len(arms),
                    "factors": factors,
                    "text": text,
                }
            )
    return arms


_CHOICE_Q = (
    "Which of the Persons do you think should get the vaccine immediately? Select one of them. "
    '1 means "Person A"; 2 means "Person B".'
)


def build_outcomes() -> list[dict[str, Any]]:
    outcomes: list[dict[str, Any]] = []
    for r in range(1, N_ROUNDS + 1):
        outcomes.append(
            {
                "var": f"ans_code_r{r}",
                "task_num": r - 1,
                "question": _CHOICE_Q,
                "scale": {"min": 1, "max": 2, "nominal": True},
                "response_recode": {1: 1, 2: 2},
                "condition_vars": _round_cols(r),
            }
        )
    return outcomes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="compare against the recipe + wide CSV")
    ap.add_argument("--write", action="store_true", help="regenerate the wide CSV and the recipe")
    args = ap.parse_args()

    uk = load_uk()
    wide = build_wide(uk)
    generated_arms = build_arms(wide)
    generated_outcomes = build_outcomes()

    recipe = yaml.safe_load(RECIPE.read_text()) if RECIPE.exists() else {}
    current_arms = recipe.get("condition", {}).get("arms", [])
    current_outcomes = recipe.get("outcomes", [])
    print(f"generated {len(generated_arms):,} arms; recipe holds {len(current_arms):,}")
    print(f"generated {len(generated_outcomes)} outcomes; recipe holds {len(current_outcomes)}")

    if args.write:
        WIDE.parent.mkdir(parents=True, exist_ok=True)
        wide.to_csv(WIDE, index=False)
        print(f"wrote {WIDE.relative_to(REPO)} ({wide.shape[0]} x {wide.shape[1]})")
        recipe["condition"]["arms"] = generated_arms
        recipe["outcomes"] = generated_outcomes
        RECIPE.write_text(yaml.safe_dump(recipe, sort_keys=False, allow_unicode=True, width=100))
        print(f"wrote {RECIPE.relative_to(REPO)}")
        return 0

    ok = True
    if not WIDE.exists():
        print("wide CSV missing — run --write")
        ok = False
    else:
        on_disk = pd.read_csv(WIDE)
        if not on_disk.equals(wide):
            print("WIDE CSV DIFFERS from what this script derives")
            ok = False
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
        print("IDENTICAL — the recipe and wide CSV are exactly what this file derives")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
