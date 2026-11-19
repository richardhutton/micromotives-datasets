"""The researchbox1032 recipes (Evangelidis 2024, shrinkflation aversion) and their answer key.

The generator reads each scenario from the study's .qsf and derives each person's arm from
which of the deposit's per-arm columns is filled. These tests stop a hand edit drifting from
it, and check the facts the rows rest on:

- each recipe and coded file is what the generator writes, and the codebooks agree with the
  .qsf question by question;
- N, and N by arm, are the deposit's (no exclusions were pre-registered; Study 3 loses one
  row that is blank throughout);
- the scale check fails on a reversed scale;
- recomputed from the BUILT rows, every R script's Model1 (a logit of unfair on the
  study's dummies) comes out coefficient for coefficient and standard error for standard
  error (to 1e-9 and 1e-6: glm stops its iterations a hair from the exact MLE, which
  moves its SEs in the seventh place), against the figures base R prints for the
  authors' own code run on the deposit (19 Nov 2026; tidyverse and epiDisplay are only
  for printing, so the models were re-run in base R with haven, line for line). Study 3's
  figures differ, as asserted, because the R script counts the blank row as a
  price-increase respondent who said fair; adding that row back to the built rows
  reproduces R exactly;
- Study 3's three process items (the mediators) have the deposit's means by arm;
- swapping the action factor breaks the reproduction.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_researchbox1032.py"
PROCESSED = REPO / "data" / "processed"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_researchbox1032", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_researchbox1032"] = mod  # dataclasses look their module up here
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.RAW.exists(), reason="researchbox1032 deposit not fetched")
NAMES = ["study1", "study2", "study3", "study4", "study5", "s1", "s2"]


def built(name: str) -> pd.DataFrame:
    path = PROCESSED / f"researchbox1032_{name}.parquet"
    if not path.exists():
        pytest.skip(f"researchbox1032_{name} not built")
    df = pd.read_parquet(path)
    return pd.concat([df.reset_index(drop=True), pd.json_normalize(df["factors"])], axis=1)


@needs_raw
@pytest.mark.parametrize("exp", gen.experiments(), ids=lambda e: e.name)
def test_recipe_is_what_the_generator_writes(exp: Any) -> None:
    assert gen.recipe_path(exp).read_text() == gen.render(exp)
    load(gen.recipe_path(exp))


def test_every_experiment_has_a_recipe() -> None:
    assert sorted(p.stem for p in (REPO / "recipes").glob("researchbox1032_*.yaml")) == sorted(
        f"researchbox1032_{n}" for n in NAMES
    )


@needs_raw
@pytest.mark.parametrize("tag", NAMES)
def test_coded_file_is_what_the_generator_writes(tag: str) -> None:
    assert (gen.RAW / gen.data_file(tag)).read_text() == gen.prep(tag).to_csv(index=False)


@needs_raw
@pytest.mark.parametrize("tag", NAMES)
def test_codebook_matches_the_qsf(tag: str) -> None:
    gen.check_codebook(tag)


@needs_raw
def test_n_and_arms_are_the_deposits() -> None:
    want = {
        "study2": {1: 152, 2: 149},
        "study3": {1: 500, 2: 500},
        "study4": {1: 1004, 2: 1004, 3: 1000, 4: 1002},
        "study5": {1: 301, 2: 300, 3: 301, 4: 300},
        "s2": {1: 998, 2: 999, 3: 1005, 4: 1003},
    }
    for tag, arms in want.items():
        assert gen.prep(tag)["arm"].value_counts().to_dict() == arms, tag
    s1 = gen.prep("study1")
    assert s1["arm_chocolate"].value_counts().to_dict() == {1: 251, 2: 250}
    assert s1["arm_orange_juice"].value_counts().to_dict() == {3: 251, 4: 250}
    assert len(gen.prep("s1")) == 200
    assert len(gen.read_deposit("study3")) == 1001 and len(gen.deposit("study3")) == 1000


@needs_raw
def test_the_scale_check_catches_a_reversed_scale() -> None:
    sv = gen.Survey("study5")
    q = dict(sv.qs["CostIncPrice"])
    assert gen.binary_scale(sv, "CostIncPrice") == (1, 2, "fair", "unfair")
    q["ChoiceOrder"] = list(reversed(q["ChoiceOrder"]))
    sv.qs["CostIncPrice"] = q
    with pytest.raises(AssertionError):
        gen.binary_scale(sv, "CostIncPrice")


@needs_raw
def test_conditions_are_the_qsf_words_up_to_this_is() -> None:
    for e in gen.experiments():
        sv = gen.Survey(e.name)
        for a in e.arms:
            assert sv.text(a.column) == f"{a.text} This is"
            assert "<" not in a.text and "&" not in a.text


# --------------------------------------------------------------------------------------
# The R scripts' Model1, from the built rows
# --------------------------------------------------------------------------------------

# summary(Model1)$coefficients, base R 4.x, the authors' code on the deposit.
R_MODEL1: dict[str, dict[str, tuple[float, float]]] = {
    "study1_chocolate": {
        "(Intercept)": (-0.815249877360, 0.136872656131),
        "ChoSizeDummy": (0.590306145542, 0.186915429025),
    },
    "study1_orange": {
        "(Intercept)": (-1.010243138215, 0.142688902120),
        "OraSizeDummy": (0.849900488140, 0.190953351291),
    },
    "study2": {
        "(Intercept)": (-0.372675285285, 0.165045882125),
        "SizeDu": (0.766967092795, 0.234824966044),
    },
    "study3": {  # N = 1001: the R script keeps the blank row
        "(Intercept)": (-0.00399202126954, 0.08935358831642),
        "SizeDu": (0.60549461191832, 0.12934355451217),
    },
    "study4": {
        "(Intercept)": (0.1196645037561, 0.0632324546093),
        "SizeDu": (0.6955853736039, 0.0931765759994),
        "HightrDu": (-0.7211670944049, 0.0914942019492),
        "SizeDu:HightrDu": (-0.6294691714637, 0.1316802978732),
    },
    "study5": {
        "(Intercept)": (-0.523248143765, 0.119245862791),
        "SizeDu": (1.055464957512, 0.168877437952),
        "CostSameDu": (1.852384091044, 0.185187083911),
        "SizeDu:CostSameDu": (-0.569310938153, 0.276187883786),
    },
    "s1": {  # glm SE; the script reports HC3 cluster-robust SEs (0.192296 for SizeDu)
        "(Intercept)": (-0.871222446471, 0.155052653083),
        "SizeDu": (1.297565139601, 0.212047201243),
    },
    "s2": {
        "(Intercept)": (-0.3111023466599, 0.0640763556326),
        "SizeDu": (0.9242068195462, 0.0921845501557),
        "MatDecDu": (0.3688298153152, 0.0899399558362),
        "SizeDu:MatDecDu": (0.1206700217332, 0.1334519376839),
    },
}


def _cell(df: pd.DataFrame) -> tuple[float, float]:
    """Log-odds of unfair (response 2) in a cell, and its variance."""
    u, f = int((df["response_num"] == 2).sum()), int((df["response_num"] == 1).sum())
    return math.log(u / f), 1 / u + 1 / f


def saturated_logit(df: pd.DataFrame, x: str, w: str | None) -> list[tuple[float, float]]:
    """Coefficients and SEs of a saturated logit of unfair on dummies x (and w, x*w).

    With every cell its own parameter, the MLE is each cell's log-odds and glm's Wald SE is
    the square root of the summed 1/count terms, so this is what R's glm reports, exactly.
    """
    if w is None:
        (l0, v0), (l1, v1) = _cell(df[df[x] == 0]), _cell(df[df[x] == 1])
        return [(l0, v0**0.5), (l1 - l0, (v0 + v1) ** 0.5)]
    c = {(i, j): _cell(df[(df[x] == i) & (df[w] == j)]) for i in (0, 1) for j in (0, 1)}
    (l00, v00), (l10, v10), (l01, v01), (l11, v11) = c[0, 0], c[1, 0], c[0, 1], c[1, 1]
    return [
        (l00, v00**0.5),
        (l10 - l00, (v00 + v10) ** 0.5),
        (l01 - l00, (v00 + v01) ** 0.5),
        (l11 - l10 - l01 + l00, (v00 + v10 + v01 + v11) ** 0.5),
    ]


def _fairness_rows(name: str) -> pd.DataFrame:
    df = built(name)
    df = df[df["scale_max"] == 2].copy()  # the fairness question(s)
    df["SizeDu"] = (df["action"] == "size_decrease").astype(int)
    return df


def _same(got: list[tuple[float, float]], want: dict[str, tuple[float, float]]) -> bool:
    return all(
        abs(g[0] - w[0]) < 1e-9 and abs(g[1] - w[1]) < 1e-6
        for g, w in zip(got, want.values(), strict=True)
    )


def test_built_rows_reproduce_r_model1_study1() -> None:
    df = _fairness_rows("study1")
    for product, key in (("chocolate", "study1_chocolate"), ("orange_juice", "study1_orange")):
        rows = df[df["product"] == product]
        assert len(rows) == 501 and rows["participant_id"].is_unique
        assert _same(saturated_logit(rows, "SizeDu", None), R_MODEL1[key]), key


@pytest.mark.parametrize("name", ["study2", "s1"])
def test_built_rows_reproduce_r_model1_one_factor(name: str) -> None:
    assert _same(saturated_logit(_fairness_rows(name), "SizeDu", None), R_MODEL1[name])


@pytest.mark.parametrize(
    "name,factor,level,dummy",
    [
        ("study4", "transparency", "high", "HightrDu"),
        ("study5", "costs", "not_increased", "CostSameDu"),
        ("s2", "reason", "materials_decreased", "MatDecDu"),
    ],
)
def test_built_rows_reproduce_r_model1_two_by_two(
    name: str, factor: str, level: str, dummy: str
) -> None:
    df = _fairness_rows(name)
    df[dummy] = (df[factor] == level).astype(int)
    assert _same(saturated_logit(df, "SizeDu", dummy), R_MODEL1[name])


def test_built_rows_reproduce_r_model1_study3_with_its_blank_row() -> None:
    df = _fairness_rows("study3")
    assert len(df) == 1000
    # Our 1,000 rows differ from R's 1,001 ...
    assert not _same(saturated_logit(df, "SizeDu", None), R_MODEL1["study3"])
    # ... and the R script's blank row, recoded as it recodes it (SizeDu 0, Unfair 0),
    # is exactly the difference.
    blank = pd.DataFrame({"SizeDu": [0], "response_num": [1.0]})
    with_blank = pd.concat([df[["SizeDu", "response_num"]], blank], ignore_index=True)
    assert _same(saturated_logit(with_blank, "SizeDu", None), R_MODEL1["study3"])


def test_built_rows_reproduce_study3_process_means() -> None:
    # Means of Process_1..3 by arm on the deposit (the PROCESS mediators): price 2.916,
    # 2.344, 4.884; size 5.234, 5.532, 4.812 (500 each).
    df = built("study3")
    items = df[df["task_num"] > 0]
    got = items.groupby(["task_num", "action"])["response_num"].agg(["mean", "size"])
    want = {
        (1, "price_increase"): 2.916,
        (2, "price_increase"): 2.344,
        (3, "price_increase"): 4.884,
        (1, "size_decrease"): 5.234,
        (2, "size_decrease"): 5.532,
        (3, "size_decrease"): 4.812,
    }
    assert {k: round(v, 3) for k, v in got["mean"].items()} == want
    assert set(got["size"]) == {500}


def test_swapping_the_action_factor_breaks_the_reproduction() -> None:
    df = _fairness_rows("study2")
    df["SizeDu"] = 1 - df["SizeDu"]
    assert not _same(saturated_logit(df, "SizeDu", None), R_MODEL1["study2"])
    df = _fairness_rows("study4")
    df["HightrDu"] = (df["transparency"] == "low").astype(int)
    assert not _same(saturated_logit(df, "SizeDu", "HightrDu"), R_MODEL1["study4"])


def test_within_person_rows_carry_their_own_scenario_only() -> None:
    for name in ("study1", "s1"):
        df = built(name)
        assert df.groupby("participant_id").size().eq(2).all(), name
        assert df.groupby("participant_id")["task_num"].nunique().eq(2).all(), name
        for _, r in df.iterrows():
            assert r["condition"].count("Production costs") == 1, name
