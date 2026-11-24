"""The g2jcy recipe (TESS 142, Elliott: a hybrid-work request) and its answer keys.

The generator reads every arm and every outcome wording out of the fielded
questionnaire, in both its simple and its programming copy, and resolves each name
and pronoun fill the way that arm's screen did. These tests stop a hand edit drifting
from it, and check the facts the rows rest on:

- eight arms, raw code = condition_num + 1, each vignette naming the character, the job
  and the disclosure its value label names, and every minimal pair differing in text;
- every outcome an arm carries names that arm's character and no other;
- the built rows reproduce every (arm, outcome) count and mean computed from the
  deposit's CSV export, a file the build never reads;
- the persona of the built rows reproduces the unweighted percentages in NORC's
  methods report (Benchmark Comparisons) to the 0.1 printed.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_g2jcy.py"
RECIPE = REPO / "recipes" / "g2jcy.yaml"
RAW = REPO / "data" / "raw" / "g2jcy"
CSV = RAW / "TESS 142 Elliott_Final Data.csv"
BUILT = REPO / "data" / "processed" / "g2jcy.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_g2jcy", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not CSV.exists(), reason="g2jcy deposit not fetched")
needs_built = pytest.mark.skipif(not (BUILT.exists() and CSV.exists()), reason="g2jcy not built")

OUTCOMES = gen.OUTCOME_VARS


@needs_raw
def test_recipe_is_what_the_generator_writes() -> None:
    assert RECIPE.read_text() == gen.render()


def test_fills_resolve_by_code() -> None:
    pg = "[IF P_EXP_ELLIOTT=1,2,3,4: Michael's, IF P_EXP_ELLIOTT=5,6,7,8: Michelle's] job"
    q = "[Michael's / Michelle's] job"
    for code in range(1, 9):
        want = "Michael's job" if code <= 4 else "Michelle's job"
        assert gen.resolve(pg, code, gen.PG_FILL) == want
        assert gen.resolve(q, code, gen.Q_FILL) == want
    with pytest.raises(SystemExit):
        gen.resolve("[IF P_EXP_ELLIOTT=1,2: Michael]", 1, gen.PG_FILL)


def test_arms_say_what_their_labels_say() -> None:
    rec = load(RECIPE)
    arms = sorted(rec.condition.arms, key=lambda a: a.condition_num)
    assert [a.condition_num for a in arms] == list(range(8))
    assert [a.raw for a in arms] == list(range(1, 9))
    assert rec.condition.shared_context is None
    assert len({a.text for a in arms}) == 8
    for a in arms:
        f = a.factors
        name = "Michael" if f["character"] == "michael" else "Michelle"
        job = "a data entry clerk" if f["occupation"] == "data_entry_clerk" else "a lawyer"
        assert a.text.startswith(f"{name} is {job} who works in-person in a law firm.")
        assert ("has Bipolar disorder" in a.text) == (f["disclosure"] == "bipolar")
        assert f == gen.factors_of(a.raw)
    # Each factor's minimal pairs differ in text, and in nothing else's label.
    by = {tuple(a.factors.values()): a.text for a in arms}
    for key, text in by.items():
        for i in range(3):
            for other, other_text in by.items():
                if sum(x != y for x, y in zip(key, other, strict=True)) == 1 and key[i] != other[i]:
                    assert text != other_text


def test_every_outcome_names_its_arms_character_only() -> None:
    rec = load(RECIPE)
    for a in rec.condition.arms:
        michael = a.factors["character"] == "michael"
        name, other = ("Michael", "Michelle") if michael else ("Michelle", "Michael")
        pron = {" his ", " he "} if name == "Michael" else {" her ", " she "}
        wrong = {" her ", " she "} if name == "Michael" else {" his ", " he "}
        assert sorted(a.items) == list(range(10))
        for t, item in a.items.items():
            words = f" {item.outcome_question} "
            assert name in words and other not in words, (a.raw, t)
            assert not any(w in words for w in wrong), (a.raw, t)
            assert "[" not in words and "]" not in words
        assert other not in a.text and name in a.text
        assert any(p in f" {a.text} " for p in pron)


def test_no_row_carries_survey_mechanics() -> None:
    rec = load(RECIPE)
    for a in rec.condition.arms:
        text = rec.condition.render(a).lower()
        assert "next screen" not in text and "read it carefully" not in text
        assert "different topic" not in text


def test_scales_are_the_questionnaires() -> None:
    rec = load(RECIPE)
    ends = [("Strongly disagree", "Strongly agree")] * 4 + [("Very unlikely", "Very likely")] * 4
    ends += [("Very unreasonable", "Very reasonable"), ("Definitely yes", "Definitely not")]
    assert [o.var for o in rec.outcomes] == OUTCOMES
    for o, (lo, hi) in zip(rec.outcomes, ends, strict=True):
        assert (o.scale.min, o.scale.max, o.scale.min_label, o.scale.max_label) == (1, 6, lo, hi)
    assert rec.missing_codes == [77, 98, 99]


def _csv() -> pd.DataFrame:
    return pd.read_csv(CSV)


def _built() -> pd.DataFrame:
    return pd.read_parquet(BUILT)


@needs_built
def test_every_cell_reproduces_the_csv() -> None:
    """Count and mean of every (arm, outcome) cell, from the CSV the build never reads."""
    raw = _csv()
    long = raw.melt(id_vars=["P_EXP_ELLIOTT"], value_vars=OUTCOMES, var_name="var", value_name="r")
    long = long[long["r"].between(1, 6)]
    long["condition_num"] = long["P_EXP_ELLIOTT"] - 1
    long["task_num"] = long["var"].map({v: i for i, v in enumerate(OUTCOMES)})
    want = long.groupby(["condition_num", "task_num"])["r"].agg(["count", "mean"])

    built = _built()
    got = built.groupby(["condition_num", "task_num"])["response_num"].agg(["count", "mean"])
    assert len(built) == 16_549 == int(want["count"].sum())
    assert len(got) == 80
    pd.testing.assert_frame_equal(got, want, check_dtype=False, check_names=False)
    # One respondent skipped all ten; everyone else is in the rows.
    assert built["participant_id"].nunique() == 1_667


# NORC methods report, Benchmark Comparisons, "Unweighted (%)", N = 1,668.
REPORT_AGE = [9.3, 7.7, 21.3, 17.3, 14.6, 10.0, 19.8]  # 18-24 25-29 30-39 40-49 50-59 60-64 65+
AGE_EDGES = [17, 24, 29, 39, 49, 59, 64, 200]
REPORT_ETHNICITY = {"White": 63.8, "Black": 10.9, "Hispanic": 17.1, "All others": 8.2}
REPORT_EDUCATION = {
    "Less than high school": 6.9,
    "High school": 16.5,
    "Some college to associate": 39.5,
    "Bachelors to postgraduate": 37.1,
}
REPORT_SEX = {"Male": 50.7, "Female": 49.3}


def _pct(s: pd.Series, n: int) -> dict[Any, float]:
    return {k: round(100 * v / n, 1) for k, v in s.value_counts().items()}


@needs_built
def test_persona_reproduces_the_methods_report() -> None:
    """The built persona of the 1,667 who answered, plus the deposit's record of the one
    who answered nothing, gives the report's 1,668 percentages exactly."""
    raw = _csv()
    skipped_all = raw[(raw[OUTCOMES] > 6).all(axis=1)]
    assert len(skipped_all) == 1
    gone = skipped_all.iloc[0]

    built = _built().drop_duplicates("participant_id")
    people = pd.DataFrame([json.loads(p) for p in built["persona"]])
    assert len(people) == 1_667
    n = 1_668

    eth_of = {1: "White", 2: "Black", 4: "Hispanic"}
    eth = people["ethnicity"].map(
        lambda e: e if e in {"White", "Black", "Hispanic"} else "All others"
    )
    eth = pd.concat([eth, pd.Series([eth_of.get(int(gone["RACETHNICITY"]), "All others")])])
    assert _pct(eth, n) == REPORT_ETHNICITY

    edu_of = {
        1: "Less than high school",
        2: "High school",
        3: "Some college to associate",
        4: "Bachelors to postgraduate",
        5: "Bachelors to postgraduate",
    }
    edu = pd.concat([people["education"], pd.Series([edu_of[int(gone["EDUC5"])]])])
    assert _pct(edu, n) == REPORT_EDUCATION

    sex = pd.concat([people["gender"], pd.Series([{1: "Male", 2: "Female"}[int(gone["GENDER"])]])])
    assert _pct(sex, n) == REPORT_SEX

    ages = pd.concat([people["age"], pd.Series([int(gone["AGE"])])])
    bands = pd.cut(ages, AGE_EDGES).value_counts(sort=False)
    assert [round(100 * v / n, 1) for v in bands] == REPORT_AGE
