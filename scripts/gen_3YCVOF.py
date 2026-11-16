#!/usr/bin/env python3
"""Derive 3YCVOF's Study 2 conjoint (MP dissent) arms from the data.

3YCVOF is Campbell, Cowley, Vivyan & Wagner, "Legislator dissent as a valence
signal", British Journal of Political Science 49(1) (2019), first online 2016.
Harvard Dataverse doi:10.7910/DVN/3YCVOF, CC0 1.0. The deposit holds four
studies as R `.rds` files plus R code; it holds NO questionnaire.

WHAT IS BUILT, AND WHAT IS NOT
------------------------------
* Study 2 (`study2data.rds`): YouGov, 5-6 December 2012, 1,899 British adults,
  five forced choices each between two hypothetical MPs. BUILT here.
* Study 3 (`study3data.rds`): same format, different attributes (motivation and
  type of dissent). NOT built: the paper quotes only fragments of its level
  wording ("nevertheless tends not to speak out", "when considering policy
  matters") and prints no screen, so the sentences respondents read cannot be
  recovered.
* Appendix A (`appendixAdata.rds`): a split-sample vignette whose full wording
  IS printed in the online appendix, but the file holds only `id`, `w8` and the
  answer. No persona at all, so not built (the X08IVC precedent).
* Study 1 is observational.

WHERE THE WORDING COMES FROM
----------------------------
Figure 1 of the author-accepted manuscript (Birkbeck BIROn,
https://eprints.bbk.ac.uk/id/eprint/14786/3/14786.pdf, p.38) is two screenshots
of the fielded YouGov screens: the introduction, and one rendered comparison.
Every word of `SHARED_CONTEXT` and of the profile template below is read off
that figure. The levels the screenshot does not happen to show are the paper's
own list of values for each attribute (pp.19-20): party Labour/Conservative;
1/2/3/4 constituency days, "with the remainder spent reviewing and working on
national policies in Parliament"; tenure 3, 10 and 21 years; male or female;
dissent never/rarely/sometimes/often. They slot into the screenshot's sentence
exactly where the shown level sits; "1 day" and "4 days" both appear in it, so
the singular/plural rule is the screenshot's own.
The levels "never" and "often" (7,161 rows), "3 years" (5,350 rows) and "2
days" and "3 days" (7,136 rows) were slot-filled from the paper's own lists
into the frame the screenshot shows; their wording was not seen word-for-word
on Figure 1.

Footnote 72 says the dissent line was "the last bullet point" in Study 2: the
attribute order was fixed, so the layout below is the one respondents saw.

Dropped as survey mechanics or sequence signposting (CONVENTIONS): "You will be
asked to make a total of five comparisons." and the "Comparison 1" heading.

WHICH PROFILE WAS "MP 1": RANDOMISED, NOT RECORDED
-------------------------------------------------
The paper (p.20): "MP attribute values were assigned via completely independent
randomization, such that all possible combinations of attribute values were
equally likely in expectation", so which profile sat in the MP 1 slot was
random per task. Nothing in the deposit records it: the file is one row per
profile (18,990 = 1,899 x 5 x 2), its 27 columns hold no side or position
variable, the two profiles of a task are not adjacent, and neither half of the
file holds one side.

So the CONVENTIONS ruling "Choice sets whose on-screen order was randomised and
not recorded" (rich, 16 Nov 2026) applies. The two profiles are listed by a
fixed rule, the one occurring first in the file first, under the instrument's
own labels MP 1 and MP 2 (Figure 1). The ruling's clause "(the options were
shown in a random order)" ends the shared context, so the row never presents
the list as the screen order, and the answer is coded to the list. Every
attribute of both profiles is kept as a structured factor (`party_1` ...
`rebellion_2`) so training can re-order and remap.

CONVERSION
----------
No reader for `.rds` exists in this project, so `export_dta()` asks R
(`haven::write_dta`) to write the file out as Stata: factors become labelled
integers, so no label is lost, dots in names become underscores, and stray
whitespace around labels ("Female\\n") is trimmed. A `row_in_file` column keeps
the deposit's own row order, which is what decides MP 1 above.

    uv run python scripts/gen_3YCVOF.py --check
    uv run python scripts/gen_3YCVOF.py --write
"""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from micromotives_datasets.sources import spss

REPO = Path(__file__).resolve().parents[1]
RECIPE = REPO / "recipes" / "3YCVOF.yaml"
RAW_DIR = REPO / "data" / "raw" / "3YCVOF"
RDS = RAW_DIR / "study2data.rds"
DTA = RAW_DIR / "study2data.dta"  # derived, for scripts/recipe_prep.py
WIDE = RAW_DIR / "study2_wide.csv"

N_RESPONDENTS = 1_899
N_TASKS = 5

_R_EXPORT = r"""
args <- commandArgs(trailingOnly = TRUE)
d <- readRDS(args[1])
names(d) <- gsub(".", "_", names(d), fixed = TRUE)
for (n in names(d)) if (is.factor(d[[n]])) levels(d[[n]]) <- trimws(levels(d[[n]]))
d$row_in_file <- seq_len(nrow(d))
haven::write_dta(d, args[2])
"""

# Attribute -> deposit column. Order is the screenshot's: the heading line
# carries party and tenure, then three bullets (national days, constituency
# days, dissent). Sex is carried by the pronoun.
ATTR_COLS = {
    "party": "mp_party",
    "tenure": "mp_tenure",
    "sex": "mp_sex",
    "const": "mp_const",
    "rebellion": "mp_rebellion",
}
ATTRS = list(ATTR_COLS)

SHARED_CONTEXT = (
    "People have different opinions about what their Member of Parliament should do.\n\n"
    "In the next few questions, we will ask you to compare two example MPs. We will call them "
    "MP 1 and MP 2. For each pair of MPs, please say which one you would personally prefer to "
    "have as your MP in the House of Commons.\n\n"
    "Please remember there are no right or wrong answers.\n\n"
    "Please read the descriptions of these two MPs carefully.\n\n"
    "(the options were shown in a random order)"
)

QUESTION = (
    "Based on this information, which ONE of these two MPs would you prefer to have as your MP "
    'in the House of Commons? 1 means "MP 1"; 2 means "MP 2".'
)

# Persona columns (deposit names after export) -> how they are carried in the
# wide CSV. The recipe's persona_map points at these wide-CSV names.
PERSONA_COLS = [
    "age_group3",
    "profile_gender",
    "social_grade",
    "educ",
    "income",
    "lr_self_group3",
    "follow_pol",
]


def export_dta(out: Path) -> None:
    subprocess.run(
        ["Rscript", "-e", _R_EXPORT, str(RDS), str(out)],
        check=True,
        capture_output=True,
    )


def load() -> spss.Dataset:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "study2data.dta"
        export_dta(out)
        ds = spss.read(out)
    df = ds.df
    if len(df) != N_RESPONDENTS * N_TASKS * 2:
        raise ValueError(f"{len(df)} rows, expected {N_RESPONDENTS * N_TASKS * 2}")
    if df["id"].nunique() != N_RESPONDENTS:
        raise ValueError(f"{df['id'].nunique()} respondents, expected {N_RESPONDENTS}")
    per_task = df.groupby(["id", "choicetask"])
    if not (per_task.size() == 2).all():
        raise ValueError("not every (id, task) has exactly two profiles")
    if not (per_task["mp_preferred"].sum() == 1).all():
        raise ValueError("not every (id, task) has exactly one preferred profile")
    for col in [*ATTR_COLS.values(), "mp_preferred"]:
        if df[col].isna().any():
            raise ValueError(f"{col} has missing values")
    # Pin every attribute's level set, so a changed deposit fails loudly.
    expect = {
        "mp_party": {"Conservative", "Labour"},
        "mp_sex": {"female", "male"},
        "mp_rebellion": {"never", "rarely", "sometimes", "often"},
        "choicetask": {f"Choice task {k}" for k in range(1, N_TASKS + 1)},
    }
    for col, want in expect.items():
        got = {ds.label(col, v) for v in df[col].unique()}
        if got != want:
            raise ValueError(f"{col}: levels {got} != {want}")
    if set(df["mp_tenure"].unique()) != {3, 10, 21}:
        raise ValueError("mp_tenure levels drifted")
    if set(df["mp_const"].unique()) != {1, 2, 3, 4}:
        raise ValueError("mp_const levels drifted")
    for col in PERSONA_COLS:
        if df.groupby("id")[col].nunique(dropna=False).max() != 1:
            raise ValueError(f"{col} is not constant within respondent")
    return ds


def build_wide(ds: spss.Dataset) -> pd.DataFrame:
    """One row per respondent; the listed first profile is the first in file order.

    That is a listing rule, not the screen order, which nothing records (see the
    module docstring and the clause ending SHARED_CONTEXT).
    """
    df = ds.df.sort_values("row_in_file")
    records: list[dict[str, Any]] = []
    for resp_id, grp in df.groupby("id", sort=True):
        first = grp.iloc[0]
        rec: dict[str, Any] = {"id": int(resp_id)}
        for col in PERSONA_COLS:
            raw = first[col]
            # `income` is renamed: the corpus reads a column called `income` as
            # household income (tests/test_income_fields.py), and these are the
            # authors' own Low/Medium/High groups, which say neither.
            out = "income_group" if col == "income" else col
            rec[out] = None if pd.isna(raw) else ds.label(col, raw)
        for t in range(1, N_TASKS + 1):
            label = f"Choice task {t}"
            pair = grp[grp["choicetask"].map(lambda v: ds.label("choicetask", v)) == label]
            if len(pair) != 2:
                raise ValueError(f"{resp_id} task {t}: {len(pair)} profiles")
            for side, (_, prof) in enumerate(pair.iterrows(), start=1):
                for attr, col in ATTR_COLS.items():
                    rec[f"{attr}_{side}_t{t}"] = int(prof[col])
            chosen = [s for s, (_, p) in enumerate(pair.iterrows(), 1) if p["mp_preferred"] == 1]
            rec[f"choice_t{t}"] = chosen[0]
        records.append(rec)
    wide = pd.DataFrame.from_records(records)
    assert len(wide) == N_RESPONDENTS
    return wide


def _days(n: int) -> str:
    return f"{n} day" if n == 1 else f"{n} days"


def render_profile(side: int, lv: dict[str, str]) -> str:
    he, his = ("He", "his") if lv["sex"] == "male" else ("She", "her")
    const = int(lv["const"])
    return "\n".join(
        [
            f"MP {side} has been a {lv['party']} MP for {lv['tenure']} years",
            f"- {he} spends on average {_days(5 - const)} of a 5-day week reviewing and "
            "working on national policies in Parliament, and",
            f"- The remaining {_days(const)} working on local constituency issues.",
            f"- {he} {lv['rebellion']} speaks out or votes against {his} party leadership.",
        ]
    )


def _task_cols(t: int) -> list[str]:
    return [f"{a}_{s}_t{t}" for s in (1, 2) for a in ATTRS]


KEY_VARS = _task_cols(1)


def build_arms(wide: pd.DataFrame, ds: spss.Dataset) -> list[dict[str, Any]]:
    """Every distinct (MP 1, MP 2) pair drawn, task-major then respondent order.

    Dedup across tasks is safe: the shared context and the question are
    identical for all five tasks, so a repeated pair is the same screen.
    """
    arms: list[dict[str, Any]] = []
    seen: set[tuple[int, ...]] = set()
    n = len(ATTRS)
    for t in range(1, N_TASKS + 1):
        cols = _task_cols(t)
        for _, row in wide.iterrows():
            vals = tuple(int(row[c]) for c in cols)
            if vals in seen:
                continue
            seen.add(vals)
            text = [ds.label(ATTR_COLS[a], v) for a, v in zip(ATTRS * 2, vals, strict=True)]
            side1 = dict(zip(ATTRS, text[:n], strict=True))
            side2 = dict(zip(ATTRS, text[n:], strict=True))
            factors = {f"{a}_1": side1[a] for a in ATTRS} | {f"{a}_2": side2[a] for a in ATTRS}
            arms.append(
                {
                    "raw_values": dict(zip(KEY_VARS, vals, strict=True)),
                    "condition_num": len(arms),
                    "factors": factors,
                    "text": f"{render_profile(1, side1)}\n\n{render_profile(2, side2)}",
                }
            )
    return arms


def build_outcomes() -> list[dict[str, Any]]:
    return [
        {
            "var": f"choice_t{t}",
            "task_num": t - 1,
            "question": QUESTION,
            "scale": {"min": 1, "max": 2, "nominal": True},
            "response_recode": {1: 1, 2: 2},
            "condition_vars": _task_cols(t),
        }
        for t in range(1, N_TASKS + 1)
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    ds = load()
    wide = build_wide(ds)
    arms = build_arms(wide, ds)
    outcomes = build_outcomes()

    recipe = yaml.safe_load(RECIPE.read_text()) if RECIPE.exists() else {}
    current_arms = recipe.get("condition", {}).get("arms", [])
    print(f"generated {len(arms):,} arms; recipe holds {len(current_arms):,}")

    if args.write:
        export_dta(DTA)
        wide.to_csv(WIDE, index=False)
        print(f"wrote {WIDE.relative_to(REPO)} ({wide.shape[0]} x {wide.shape[1]})")
        cond = recipe.setdefault("condition", {})
        cond["source_vars"] = KEY_VARS
        cond["shared_context"] = SHARED_CONTEXT
        cond["arms"] = arms
        recipe["outcomes"] = outcomes
        RECIPE.write_text(yaml.safe_dump(recipe, sort_keys=False, allow_unicode=True, width=100))
        print(f"wrote {RECIPE.relative_to(REPO)}")
        return 0

    ok = True
    if not WIDE.exists() or not pd.read_csv(WIDE).equals(pd.read_csv(_roundtrip(wide))):
        print("WIDE CSV DIFFERS from what this script derives")
        ok = False
    cond = recipe.get("condition", {})
    if cond.get("source_vars") != KEY_VARS or cond.get("shared_context") != SHARED_CONTEXT:
        print("SOURCE_VARS OR SHARED_CONTEXT DIFFER")
        ok = False
    if arms != current_arms:
        print("ARMS DIFFER")
        ok = False
    if outcomes != recipe.get("outcomes"):
        print("OUTCOMES DIFFER")
        ok = False
    if ok:
        print("IDENTICAL")
        return 0
    return 1


def _roundtrip(wide: pd.DataFrame) -> Path:
    tmp = Path(tempfile.mkdtemp()) / "wide.csv"
    wide.to_csv(tmp, index=False)
    return tmp


if __name__ == "__main__":
    raise SystemExit(main())
