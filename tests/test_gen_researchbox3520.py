"""The researchbox3520 recipe (Edenbrandt & Häsler, UK beef mince choices, text arms).

The generator builds every card from the survey PDF, ties each screen to its design choice
set by the cards' attribute levels, and re-derives the authors' analysis sample from the raw
export. These tests hold the recipe and coded file to the generator, and check the facts the
rows rest on:

- the recipe and coded file are what the generator writes; the sample is the do-file's;
- the screen-to-set tie is unique, and fails when a card's level is altered;
- the cards keep the PDF's words, typo included; affirmative cards never say "Not";
- N by arm is the analysis file's (497 T-C, 503 T-A);
- the answer key: the authors' MNL in WTP space (Code/wMNL_TC.R, wMNL_TA.R), estimated on
  the BUILT rows from their factors and responses, equals the same model on
  Beef_CE_Survey.txt read by the authors' column names; and the opt-out count per person
  (the do-file's `all_SQ`) by arm equals theirs;
- swapping the two products' answers, or the label_display factor, breaks it.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import minimize

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_researchbox3520.py"
PROCESSED = REPO / "data" / "processed"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_researchbox3520", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_researchbox3520"] = mod
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(
    not gen.BOX.exists() or shutil.which("pdftotext") is None,
    reason="researchbox3520 deposit not fetched, or poppler not installed",
)
BUILT = PROCESSED / "researchbox3520_text.parquet"
needs_build = pytest.mark.skipif(not BUILT.exists(), reason="researchbox3520 not built")


@needs_raw
def test_recipe_is_what_the_generator_writes() -> None:
    assert gen.RECIPE.read_text() == gen.render()
    load(gen.RECIPE)


@needs_raw
def test_coded_file_is_what_the_generator_writes() -> None:
    assert (gen.RAW / gen.DATA_FILE).read_text() == gen.prep().to_csv(index=False)


@needs_raw
def test_sample_is_the_do_files() -> None:
    gen.check_sample()


@needs_raw
def test_every_set_is_tied_once_per_arm_and_typos_are_kept() -> None:
    typo = 0
    for prefix in gen.ARMS:
        sets = gen.choice_sets(prefix)
        assert sorted(sets) == list(range(1, 25))
        for s, (c1, c2) in sets.items():
            assert c1.levels == gen.alt(s, 1) and c2.levels == gen.alt(s, 2)
            for c in (c1, c2):
                typo += "'RSPCA Assued'" in c.text
                if prefix == "tl":
                    assert "Not " not in c.text
                else:
                    assert len(c.lines) == 7
    assert typo == 36


@needs_raw
def test_the_tie_fails_when_a_level_is_altered(monkeypatch: Any) -> None:
    real = gen.alt

    def wrong(s: int, k: int) -> tuple[float, ...]:
        v = real(s, k)
        return (v[0], v[1] + 5, *v[2:]) if (s, k) == (2, 1) else v

    gen.choice_sets.cache_clear()
    monkeypatch.setattr(gen, "alt", wrong)
    with pytest.raises(AssertionError):
        gen.choice_sets("tc")
    monkeypatch.setattr(gen, "alt", real)
    gen.choice_sets.cache_clear()


# ---------------------------------------------------------------------------
# The answer key
# ---------------------------------------------------------------------------

ATTRS = ["rspca", "fat", "ftn", "quality", "cl"]


def wmnl(x1: np.ndarray, p1: np.ndarray, x2: np.ndarray, p2: np.ndarray, y: np.ndarray) -> Any:
    """Code/wMNL_T?.R: V_k = -mu_price * (w . x_k - price_k), V_3 = mu_sq."""

    def nll(b: np.ndarray) -> float:
        w, mu_price, mu_sq = b[:5], b[5], b[6]
        v = np.c_[-mu_price * (x1 @ w - p1), -mu_price * (x2 @ w - p2), np.full(len(y), mu_sq)]
        v -= v.max(axis=1, keepdims=True)
        lp = v - np.log(np.exp(v).sum(axis=1, keepdims=True))
        return float(-lp[np.arange(len(y)), y - 1].sum())

    start = np.array([0.96, -0.14, 0.58, 0.64, 0.30, -0.43, -3.57])  # the scripts' own
    return minimize(nll, start, method="BFGS", options={"gtol": 1e-8}).x


def from_authors(group: str) -> np.ndarray:
    ce = pd.read_csv(gen.CE, sep="\t")
    ce = ce[ce[group] == 1]
    return np.asarray(
        wmnl(
            ce[[f"{a}1" for a in ATTRS]].to_numpy(float),
            ce["price1"].to_numpy(float),
            ce[[f"{a}2" for a in ATTRS]].to_numpy(float),
            ce["price2"].to_numpy(float),
            ce["choice"].to_numpy(int),
        )
    )


FNAME = {
    "rspca": "rspca",
    "fat": "fat",
    "ftn": "fair_to_nature",
    "quality": "premium_quality_angus",
    "cl": "low_climate_impact",
}


def _level(v: str) -> float:
    if v in ("yes", "no"):
        return 1.0 if v == "yes" else 0.0
    return float(re.sub(r"[£%]", "", v))


def from_rows(rows: pd.DataFrame, level: str) -> np.ndarray:
    rows = rows[rows.factors.map(lambda f: f["label_display"]) == level]
    f = rows.factors

    def x(k: int) -> np.ndarray:
        return np.array([[_level(d[f"option_{k}_{FNAME[a]}"]) for a in ATTRS] for d in f])

    def p(k: int) -> np.ndarray:
        return np.array([_level(d[f"option_{k}_price"]) for d in f])

    return np.asarray(wmnl(x(1), p(1), x(2), p(2), rows.response_num.to_numpy(int)))


@pytest.fixture(scope="module")
def rows() -> pd.DataFrame:
    return pd.read_parquet(BUILT, columns=["participant_id", "factors", "response_num"])


@needs_raw
@needs_build
def test_n_by_arm_is_the_analysis_files(rows: pd.DataFrame) -> None:
    per = rows.groupby("participant_id").factors.first().map(lambda f: f["label_display"])
    assert len(rows) == 8000 and per.value_counts().to_dict() == {
        "affirmative": 503,
        "comprehensive": 497,
    }


@needs_raw
@needs_build
@pytest.mark.parametrize(
    ("level", "group"), [("comprehensive", "Group_TC"), ("affirmative", "Group_TA")]
)
def test_built_rows_reproduce_the_authors_wtp_mnl(
    rows: pd.DataFrame, level: str, group: str
) -> None:
    ours, theirs = from_rows(rows, level), from_authors(group)
    assert np.allclose(ours, theirs, atol=1e-5), (ours, theirs)
    w = dict(zip(ATTRS, ours[:5], strict=True))
    # The published MXL means' signs: every label worth paying for, fat a cost.
    assert w["fat"] < 0 and min(w["rspca"], w["ftn"], w["quality"], w["cl"]) > 0


@needs_raw
@needs_build
def test_comprehensive_values_every_label_more_as_published(rows: pd.DataFrame) -> None:
    # wMLec_b_estimates_short.xlsx: T-C's mean WTP exceeds T-A's for all four labels.
    tc, ta = from_rows(rows, "comprehensive"), from_rows(rows, "affirmative")
    for i in (0, 2, 3, 4):
        assert tc[i] > ta[i]


@needs_raw
@needs_build
def test_opt_outs_per_person_by_arm_are_the_do_files(rows: pd.DataFrame) -> None:
    ce = pd.read_csv(gen.CE, sep="\t").groupby("id").first()
    theirs = ce.groupby("treatment").all_SQ.mean()
    per = rows.assign(
        sq=rows.response_num == 3, arm=rows.factors.map(lambda f: f["label_display"])
    ).groupby("participant_id")
    ours = per.agg(sq=("sq", "sum"), arm=("arm", "first")).groupby("arm").sq.mean()
    assert ours["comprehensive"] == pytest.approx(theirs[3], abs=1e-12)
    assert ours["affirmative"] == pytest.approx(theirs[4], abs=1e-12)


@needs_raw
@needs_build
def test_swapping_the_products_or_the_arm_breaks_the_reproduction(rows: pd.DataFrame) -> None:
    swapped = rows.assign(response_num=rows.response_num.replace({1: 2, 2: 1}))
    assert not np.allclose(from_rows(swapped, "comprehensive"), from_authors("Group_TC"), atol=1e-3)
    flip = {"comprehensive": "affirmative", "affirmative": "comprehensive"}
    relabelled = rows.assign(
        factors=rows.factors.map(lambda f: {**f, "label_display": flip[f["label_display"]]})
    )
    assert not np.allclose(
        from_rows(relabelled, "comprehensive"), from_authors("Group_TC"), atol=1e-3
    )
