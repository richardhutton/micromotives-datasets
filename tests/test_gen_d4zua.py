"""The d4zua recipe (TESS 076, Munsch: an e-mailed job reference) and its answer key.

The generator reads the condition and the four question wordings out of the fielded
questionnaire and writes them as a template over the three preloads. These tests stop a
hand edit drifting from it, and check the facts the rows rest on:

- the [SHOW] resolver evaluates each clause by code and refuses what it cannot read;
- 32 arms, condition_num the odometer over (hours, gender, performance), each arm's text
  saying what its three value labels say, and every minimal pair differing in text;
- every question an arm carries names that arm's applicant and no other;
- the dropped salary question leaves no dollar amount in any row;
- the built rows reproduce every (cell, outcome) count and mean computed from the STATA
  copy of the data, a file the build never reads, and fail to when a factor is flipped.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import re
from itertools import product
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_d4zua.py"
RECIPE = REPO / "recipes" / "d4zua.yaml"
RAW = REPO / "data" / "raw" / "d4zua"
DTA = RAW / "TESS076_Munsch_STATA.dta"
BUILT = REPO / "data" / "processed" / "d4zua.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_d4zua", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not DTA.exists(), reason="d4zua deposit not fetched")
needs_built = pytest.mark.skipif(not (BUILT.exists() and DTA.exists()), reason="d4zua not built")

OUTCOMES = gen.OUTCOME_VARS
DESIGN = gen.DESIGN_VARS
WOMAN = {"Ms.", "Amy", "her", "she"}
MAN = {"Mr.", "Jason", "his", "he"}


def _words(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z]+\.?", text)) | set(re.findall(r"[A-Za-z]+", text))


@needs_raw
def test_recipe_is_what_the_generator_writes() -> None:
    assert RECIPE.read_text() == gen.render()


def test_resolver_evaluates_each_clause() -> None:
    d = (
        "[SHOW “Ms.” IF P_MUNSCHEXP2=1 and P_MUNSCHEXP1=2; "
        "SHOW “Mr.” if P_MUNSCHEXP2=2 and P_MUNSCHEXP1=2]"
    )
    cell = {gen.HOURS: 2, gen.GENDER: 1, gen.PERF: 3}
    assert gen.resolve(d, cell) == "Ms."
    assert gen.resolve(d, cell | {gen.GENDER: 2}) == "Mr."
    assert gen.resolve(d, cell | {gen.HOURS: 1}) == ""
    assert gen.resolve("top [P_MUNSCHEXP3] of", cell) == "top 10% of"
    with pytest.raises(SystemExit):
        gen.resolve("[SHOW “x” WHEN P_MUNSCHEXP2=1]", cell)
    with pytest.raises(SystemExit):
        gen.resolve("[SHOW “x” IF P_MUNSCHEXP2>1]", cell)


def test_arms_say_what_their_labels_say() -> None:
    rec = load(RECIPE)
    arms = sorted(rec.condition.arms, key=lambda a: a.condition_num)
    assert [a.condition_num for a in arms] == list(range(32))
    assert rec.condition.source_vars == DESIGN
    for (h, g, p), a in zip(product((1, 2), (1, 2), range(1, 9)), arms, strict=True):
        assert a.raw_values == {gen.HOURS: h, gen.GENDER: g, gen.PERF: p}
        text = rec.condition.render(a)
        words = _words(text)
        mine, other = (WOMAN, MAN) if g == 1 else (MAN, WOMAN)
        assert mine <= words, a.raw_values
        assert not (other - {"Mr."}) & words, a.raw_values  # "Dear Mr. Welch" is fixed
        assert text.count("Mr.") == (1 if g == 1 else 4)
        assert ("standard business hours" in text) == (h == 1)
        assert ("50 or 60 hours/week" in text) == (h == 2)
        assert f"in the top {gen.PERF_LABELS[p]} of employees" in text
        assert "{" not in text and "[" not in text and "$" not in text
    # Each factor's minimal pairs differ in text.
    by = {tuple(a.raw_values.values()): rec.condition.render(a) for a in arms}
    for key, text in by.items():
        for other_key, other_text in by.items():
            if sum(x != y for x, y in zip(key, other_key, strict=True)) == 1:
                assert text != other_text


def test_every_question_names_its_arms_applicant_only() -> None:
    rec = load(RECIPE)
    assert [o.var for o in rec.outcomes] == OUTCOMES
    for a in rec.condition.arms:
        woman = a.factors["gender"] == "woman"
        assert sorted(a.items) == [0, 1, 2, 3]
        for t, item in a.items.items():
            q = item.outcome_question or ""
            assert ("Ms. Morgan" in q) == woman and ("Mr. Morgan" in q) != woman, (a.label, t)
            assert "/" not in q and "[" not in q and "$" not in q
        assert ("her work?" in a.items[0].outcome_question) == woman  # type: ignore[operator]


def test_scales_and_the_dropped_question() -> None:
    rec = load(RECIPE)
    ends = [
        ("not at all " + w, "extremely " + w)
        for w in ("committed", "competent", "likeable", "reliable")
    ]
    for o, (lo, hi) in zip(rec.outcomes, ends, strict=True):
        assert (o.scale.min, o.scale.max, o.scale.min_label, o.scale.max_label) == (1, 7, lo, hi)
    assert rec.missing_codes == [77, 98, 99]
    assert gen.NOT_BUILT not in [o.var for o in rec.outcomes]
    assert "Q5_MUNSCH" in rec.notes and "DROPPED (US dollar salary)" in rec.notes


def _long(frame: pd.DataFrame) -> pd.DataFrame:
    long = frame.melt(id_vars=DESIGN, value_vars=OUTCOMES, var_name="var", value_name="r")
    long = long[long["r"].between(1, 7)].copy()
    long["condition_num"] = (
        (long[gen.HOURS] - 1) * 16 + (long[gen.GENDER] - 1) * 8 + (long[gen.PERF] - 1)
    ).astype(int)
    long["task_num"] = long["var"].map({v: i for i, v in enumerate(OUTCOMES)})
    return long


@needs_built
def test_every_cell_reproduces_the_stata_copy() -> None:
    """Count and mean of every (cell, outcome), from the .dta the build never reads; and
    the same comparison with the gender codes swapped must fail, so it can."""
    raw = pd.read_stata(DTA, convert_categoricals=False)
    assert len(raw) == 2_116
    want = _long(raw).groupby(["condition_num", "task_num"])["r"].agg(["count", "mean"])

    built = pd.read_parquet(BUILT)
    got = built.groupby(["condition_num", "task_num"])["response_num"].agg(["count", "mean"])
    assert len(built) == 8_408 == int(want["count"].sum())
    assert built["participant_id"].nunique() == 2_114
    assert len(got) == 128
    pd.testing.assert_frame_equal(got, want, check_dtype=False, check_names=False)

    # Per factor, as an analyst would read it: overall means by hours, gender, performance.
    b = built.assign(**{k: built["factors"].map(lambda f, k=k: f[k]) for k in gen.DIMENSIONS})
    r = _long(raw)
    level = {
        n: {c: lv["level"] for c, lv in d["levels"].items()} for n, d in gen.DIMENSIONS.items()
    }
    for name, var in zip(gen.DIMENSIONS, DESIGN, strict=True):
        w = r.assign(lv=r[var].map(level[name])).groupby(["lv", "task_num"])["r"].mean()
        g = b.groupby([name, "task_num"])["response_num"].mean()
        pd.testing.assert_series_equal(g, w, check_names=False, check_index_type=False)

    flipped = raw.assign(**{gen.GENDER: 3 - raw[gen.GENDER]})
    wrong = _long(flipped).groupby(["condition_num", "task_num"])["r"].agg(["count", "mean"])
    with pytest.raises(AssertionError):
        pd.testing.assert_frame_equal(got, wrong, check_dtype=False, check_names=False)
