#!/usr/bin/env python3
"""Derive 9xw67's conjoint arms from the data, instead of storing 456,000 lines.

`recipes/9xw67_conjoint.yaml` declares 11,991 arms and runs to 455,919 lines --
95% of all recipe text in this repo. It was machine-generated, and its own notes
said so: "generated once by scripts/gen_conjoint_full.py-equivalent code, not
hand-typed". That script was never kept. So the only surviving artefact was the
expansion, and the *judgement* -- which profiles count as observed, how
condition_num is ordered, how an attribute row is rendered -- existed only as
prose describing code nobody could run.

That inverts what a recipe is for. The convention is that every judgement lives
in a file a human reviews; nobody reviews 456,000 lines, and nobody could
regenerate them after a fix. This file is the judgement, at ~90 lines. The YAML
is its output.

    uv run python scripts/gen_9xw67_conjoint.py --check   # agree with the recipe?
    uv run python scripts/gen_9xw67_conjoint.py --write   # regenerate the arms

`--check` runs in CI via tests/test_gen_9xw67.py, so the recipe and this file
cannot drift apart silently.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from micromotives_datasets.sources import spss

REPO = Path(__file__).resolve().parents[1]
RECIPE = REPO / "recipes" / "9xw67_conjoint.yaml"
DATA = REPO / "data" / "raw" / "9xw67" / "TESS 091B Ozer" / "s2078_surveyB_final_20211021.dta"

# The ten profile slots, in the order a respondent met them: five pairs, two
# sides each. condition_num is assigned in first-encounter order scanning these
# slots across respondents in file order, which is arbitrary but DECLARED and
# reproducible — CONVENTIONS only asks that the raw->condition_num map be
# declared, not that it carry meaning. See build_arms for which way round the
# scan goes; it is not what the recipe's prose first suggests.
SLOTS = [f"V{pair}_{side}" for pair in range(1, 6) for side in ("A", "B")]

# The nine attributes: the variable stem, the row label the on-screen table put
# in its left column, and the factor name QC rule 5 checks is expressed.
#
# The VALUE text is not here — it comes from the .dta's own value labels, so the
# words a respondent read are never retyped. Only the row labels and the short
# factor level names are judgement, and both are below where they can be read.
ATTRIBUTES: list[tuple[str, str, str]] = [
    ("TRANS", "Transparency of the algorithm", "transparency"),
    ("CASES", "Number of cases used to create the algorithm", "num_cases"),
    ("DEV", "Who developed the algorithm", "developer"),
    ("LOC", "Location from which data to create the algorithm was collected", "data_location"),
    (
        "ACC",
        "Estimated accuracy of the algorithm based on the cases used to create it",
        "accuracy",
    ),
    ("CLASS", "Differences in classification by race", "race_gap"),
    ("HUM", "Human involvement in final estimate (if any)", "human_involvement"),
    ("RACE", "Is race used to predict risk", "race_used"),
    ("FACTOR", "Number of factors the algorithm uses to make a recommendation", "num_factors"),
]

# Short names for each level, used only in `factors` so a consumer can select
# rows without parsing the condition text. The full wording is in the text.
LEVELS: dict[str, dict[int, str]] = {
    "TRANS": {
        1: "data+algo private",
        2: "algo public, data private",
        3: "data public, algo private",
        4: "both public",
    },
    "CASES": {1: "10k cases", 2: "100k cases", 3: "500k cases", 4: "1m cases"},
    "DEV": {1: "Harvard", 2: "DOJ", 3: "private firm"},
    "LOC": {1: "own state only", 2: "all 50 states"},
    "ACC": {1: "65% accurate", 2: "52% accurate", 3: "76% accurate"},
    "CLASS": {
        1: "no race gap",
        2: "+45% Black",
        3: "+25% Black",
        4: "+62% Black",
        5: "+77% Black",
    },
    "HUM": {1: "human+algo (50/50)", 2: "algo only, no human"},
    "RACE": {1: "race used", 2: "race not used"},
    "FACTOR": {1: "137 factors", 2: "58 factors", 3: "5 factors"},
}

# SIX value labels in this .dta are severed at Stata's 80-character ceiling, and
# five of them are the CLASS attribute -- the race-disparity manipulation, which
# is what the study is about. Building from the .dta alone would put
# "...are equally classifie" and "...than white de" into the stimulus text of
# thousands of rows. Recovered verbatim from the fielded questionnaire
# ([8041.091] TESS Ozer SurveyB_vFINALsimple.txt), where each appears once per
# slot, ten times in all; every string below was grep-confirmed against it.
#
# This is the same fault as the truncated religion labels across seven studies,
# except here it is in the STIMULUS rather than the persona, and no unclosed
# bracket marks it -- the cut lands mid-word with nothing to detect. QC rule 18
# would not catch this one.
RECOVERED: dict[str, dict[int, str]] = {
    "CLASS": {
        1: (
            "Black and white defendants with similar criminal histories are equally "
            "classified as high risk."
        ),
        2: (
            "Black defendants are 45% more likely to be classified as high risk than "
            "white defendants with similar criminal histories."
        ),
        3: (
            "Black defendants are 25% more likely to be classified as high risk than "
            "white defendants with similar criminal histories."
        ),
        4: (
            "Black defendants are 62% more likely to be classified as high risk than "
            "white defendants with similar criminal histories."
        ),
        5: (
            "Black defendants are 77% more likely to be classified as high risk than "
            "white defendants with similar criminal histories."
        ),
    },
    "HUM": {
        1: (
            "A trained assessment officer reviews the case and provides a "
            "recommendation that makes up 50% of the final score."
        ),
    },
}

# The arm lookup is keyed by the ORDERED CODE TUPLE, so every arm's raw_values
# is written against slot V1_A's column names whichever slot it was drawn into.
KEY_VARS = [f"{stem}_V1_A" for stem, _, _ in ATTRIBUTES]


def build_arms() -> list[dict[str, Any]]:
    """Every distinct 9-attribute profile that any respondent actually saw.

    Only observed profiles are declared. The full theoretical universe is
    4*4*3*2*3*5*2*2*3 = 17,280 cells, and declaring it would raise thousands of
    rule 2 warnings for combinations this finite sample never drew — noise that
    buries the warnings rule 2 exists to give.
    """
    ds = spss.read(DATA)
    value_labels = {}
    for stem, _, _ in ATTRIBUTES:
        labels = dict(ds.value_labels.get(f"{stem}_V1_A") or {})
        labels.update(RECOVERED.get(stem, {}))
        value_labels[stem] = labels
    arms: list[dict[str, Any]] = []
    seen: dict[tuple[int, ...], int] = {}

    # SLOT-MAJOR: every respondent's V1_A, then every respondent's V1_B, and so
    # on. The recipe's own note said "scanning (pair, side) = (V1,A), (V1,B),
    # ... across all 2,048 respondents in file order", which reads equally well
    # as respondent-major and produces a completely different condition_num
    # assignment. Prose cannot pin an ordering; this loop can.
    for slot in SLOTS:
        for _, row in ds.df.iterrows():
            codes = []
            for stem, _, _ in ATTRIBUTES:
                value = row[f"{stem}_{slot}"]
                if value is None or value != value:  # NaN
                    codes = []
                    break
                codes.append(int(float(value)))
            if not codes:
                continue
            key = tuple(codes)
            if key in seen:
                continue
            seen[key] = len(arms)
            lines, factors = [], {}
            for (stem, label, factor), code in zip(ATTRIBUTES, codes, strict=True):
                # The label's own trailing period is stripped so the rendered
                # line is "label: value", not "label.: value".
                lines.append(f"{label.rstrip('.')}: {value_labels[stem][code]}")
                factors[factor] = LEVELS[stem][code]
            arms.append(
                {
                    "raw_values": dict(zip(KEY_VARS, codes, strict=True)),
                    "condition_num": len(arms),
                    "factors": factors,
                    "text": "\n".join(lines),
                }
            )
    return arms


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="compare against the recipe")
    ap.add_argument("--write", action="store_true", help="rewrite the recipe's arms")
    args = ap.parse_args()

    generated = build_arms()
    recipe = yaml.safe_load(RECIPE.read_text())
    current = recipe["condition"]["arms"]
    print(f"generated {len(generated):,} arms; recipe holds {len(current):,}")

    if args.write:
        recipe["condition"]["arms"] = generated
        RECIPE.write_text(yaml.safe_dump(recipe, sort_keys=False, allow_unicode=True, width=100))
        print(f"wrote {RECIPE.relative_to(REPO)}")
        return 0

    if generated == current:
        print("IDENTICAL — the recipe is exactly what this file derives")
        return 0
    print("DIFFER")
    for i, (g, c) in enumerate(zip(generated, current, strict=False)):
        if g != c:
            print(f"  first difference at arm {i}:\n    generated {g}\n    recipe    {c}")
            break
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
