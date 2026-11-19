"""The researchbox3251 recipes (Cheng & Stadler Blank 2025, conditional promotions) and key.

The generator reads every scenario and question from the blocks each .qsf's flow reaches,
keeps the Finished = 1 rows the authors analyse, and takes the assignment from the
randomiser's embedded field. These tests stop a hand edit drifting from it, and check the
facts the rows rest on:

- each recipe and coded file is what the generator writes; the codebooks list the data
  files' columns;
- the 25 <img> tags sit where the docstring says (only WA-A3's scenario shows one to a
  respondent, and WA-A3 is not built), and the picture check fails if one moves;
- N and N by arm are the paper's;
- recomputed from the BUILT rows, the paper's own numbers come out to the printed
  precision: Study 2's five cell means and SDs and its one-way F; Study 3's Table 4, all 40
  counts; Web Appendix B2's discount means
  (with the authors' one exclusion applied, and not without it); B3's eight means and SDs
  and three F tests; B4's twelve Figure W1 means;
- swapping a factor breaks the reproduction;
- Study 4 is not built (its arms are defined by the respondent's own first answer).

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from scipy import stats

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_researchbox3251.py"
PROCESSED = REPO / "data" / "processed"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_researchbox3251", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_researchbox3251"] = mod  # dataclasses look their module up here
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.RAW.exists(), reason="researchbox3251 deposit not fetched")
NAMES = ["study2", "study3", "wa_b2", "wa_b3", "wa_b4"]


def built(name: str) -> pd.DataFrame:
    path = PROCESSED / f"researchbox3251_{name}.parquet"
    if not path.exists():
        pytest.skip(f"researchbox3251_{name} not built")
    df = pd.read_parquet(path)
    return pd.concat([df.reset_index(drop=True), pd.json_normalize(df["factors"])], axis=1)


def wide(name: str, by: str) -> pd.DataFrame:
    """One row per person: the factor `by` and each task's answer as a column."""
    df = built(name)
    return df.pivot_table(
        index=["participant_id", by], columns="task_num", values="response_num"
    ).reset_index()


def stat(s: pd.Series) -> tuple[float, float]:
    return round(float(s.mean()), 2), round(float(s.std()), 2)


def oneway(df: pd.DataFrame, by: str, col: Any) -> float:
    return float(stats.f_oneway(*[g[col].dropna() for _, g in df.groupby(by)]).statistic)


# --------------------------------------------------------------------------------------
# The generator
# --------------------------------------------------------------------------------------


@needs_raw
@pytest.mark.parametrize("name", NAMES)
def test_recipe_is_what_the_generator_writes(name: str) -> None:
    e = gen.experiment(name)
    assert gen.recipe_path(e).read_text() == gen.render(e)
    load(gen.recipe_path(e))


def test_every_built_study_has_a_recipe_and_the_rest_are_not_built() -> None:
    assert sorted(p.stem for p in (REPO / "recipes").glob("researchbox3251_*.yaml")) == sorted(
        f"researchbox3251_{n}" for n in NAMES
    )
    assert set(gen.NOT_BUILT) == {
        "pilot",
        "study1",
        "study4",
        "wa_a3",
        "wa_b1_mturk",
        "wa_b1_student",
    }
    assert not set(gen.NOT_BUILT) & set(gen.SOURCES)


@needs_raw
@pytest.mark.parametrize("tag", NAMES)
def test_coded_file_is_what_the_generator_writes(tag: str) -> None:
    assert (gen.RAW / gen.data_file(tag)).read_text() == gen.prep(tag).to_csv(index=False)


@needs_raw
@pytest.mark.parametrize("tag", NAMES)
def test_codebook_lists_the_columns(tag: str) -> None:
    gen.check_codebook(tag)


@needs_raw
def test_pictures_are_where_the_docstring_says() -> None:
    gen.check_pictures()


@needs_raw
def test_the_picture_check_catches_a_moved_picture() -> None:
    saved = gen.PICTURES["WA-A3_Qualtrics survey.qsf"]
    try:
        gen.PICTURES["WA-A3_Qualtrics survey.qsf"] = (0, 3)  # "none fielded": false
        with pytest.raises(AssertionError):
            gen.check_pictures()
    finally:
        gen.PICTURES["WA-A3_Qualtrics survey.qsf"] = saved
    gen.check_pictures()


@needs_raw
def test_n_and_arms() -> None:
    assert gen.prep("study2")["qp"].value_counts().sort_index().to_dict() == {
        1: 98,
        2: 100,
        3: 101,
        4: 101,
        5: 101,
    }
    assert gen.prep("study3")["arm_0"].value_counts().to_dict() == {1: 174, 2: 173}
    assert gen.prep("wa_b2")["cond"].value_counts().sort_index().to_dict() == {
        1: 97,
        2: 103,
        3: 99,
        4: 101,
    }
    assert gen.prep("wa_b3")["cond"].value_counts().sort_index().to_dict() == {1: 99, 2: 101}
    b4 = gen.prep("wa_b4")
    assert len(b4) == 210 and b4["age"].isna().sum() == 16  # "22 or older"
    assert set(b4["sex"]) == {"Male", "Female"}


@needs_raw
def test_identity_not_listed_loses_its_write_in_prompt_and_refusals_are_blank() -> None:
    g = gen.gender_labels(gen.survey("study2").qs["gender"])
    assert g == {
        1: "Man",
        2: "Woman",
        3: "Non-binary/non-conforming",
        4: "Identity not listed",
        5: None,
    }
    g3 = gen.gender_labels(gen.survey("study3").qs["gender"])
    assert g3[5] == "Identity not listed" and g3[6] is None and g3[3] == "Transgender"


# --------------------------------------------------------------------------------------
# The paper's numbers, from the built rows
# --------------------------------------------------------------------------------------


def test_study2_cell_means_and_f() -> None:
    df = built("study2")
    df["rev"] = 8 - df["response_num"]  # the paper reverse-codes: higher = Saks
    want = {
        ("low", "high"): (5.38, 1.82),
        ("low", "low"): (4.46, 1.79),
        ("high", "high"): (3.28, 1.59),
        ("high", "low"): (3.79, 1.74),
        ("none", "none"): (4.86, 1.72),
    }
    for (q, p), ms in want.items():
        cell = df[(df["precondition_cost"] == q) & (df["discount"] == p)]
        assert stat(cell["rev"]) == ms, (q, p)
    df["cell"] = df["precondition_cost"] + df["discount"]
    assert len(df) == 501
    assert round(oneway(df, "cell", "rev"), 2) == 23.34  # F(4, 496)


def test_study2_swapping_the_discount_breaks_it() -> None:
    df = built("study2")
    df["discount"] = df["discount"].map({"high": "low", "low": "high", "none": "none"})
    cell = df[(df["precondition_cost"] == "low") & (df["discount"] == "high")]
    assert stat(8 - cell["response_num"]) != (5.38, 1.82)


TABLE4 = {  # Table 4: distance -> (no promotion, promotion), counts of options 1-5
    "0_miles": ((24, 123, 3, 11, 13), (4, 159, 6, 3, 1)),
    "30_miles": ((104, 21, 20, 4, 25), (16, 125, 21, 1, 10)),
    "60_miles": ((127, 3, 17, 2, 25), (35, 72, 43, 1, 22)),
    "90_miles": ((115, 3, 31, 1, 24), (46, 39, 56, 1, 31)),
}


def table4(df: pd.DataFrame) -> dict[str, tuple[tuple[int, ...], ...]]:
    out = {}
    for d in TABLE4:
        rows = []
        for promo in ("none", "conditional"):
            r = df[(df["distance"] == d) & (df["promotion"] == promo)]["response_num"]
            rows.append(tuple(int((r == k).sum()) for k in range(1, 6)))
        out[d] = tuple(rows)
    return out


def test_study3_table4_every_count() -> None:
    assert table4(built("study3")) == TABLE4


def test_study3_swapping_the_promotion_breaks_it() -> None:
    df = built("study3")
    df["promotion"] = df["promotion"].map({"none": "conditional", "conditional": "none"})
    assert table4(df) != TABLE4


def test_study3_options_carry_each_arms_price() -> None:
    df = built("study3")
    for promo, price in (("none", "$90"), ("conditional", "$45")):
        r = df[df["promotion"] == promo]
        assert r["outcome"].str.contains(f'instore for {price}"; 3 means', regex=False).all()


def test_wa_b2_discount_means_after_the_authors_exclusion() -> None:
    w = wide("wa_b2", "discount")
    assert len(w) == 400
    kept = w[w[1] <= 2435.88]  # the authors' 3 SD rule drops exactly one person, kept here
    assert len(kept) == 399 and int(w[1].max()) == 10000
    idx = (kept[0] + kept[1]) / 2
    assert stat(idx[kept["discount"] == "70_percent"]) == (731.93, 216.47)
    assert stat(idx[kept["discount"] == "10_percent"]) == (818.19, 195.30)
    every = (w[0] + w[1]) / 2  # with that person: the rows we build do not match the paper
    assert stat(every[w["discount"] == "70_percent"]) != (731.93, 216.47) or stat(
        every[w["discount"] == "10_percent"]
    ) != (818.19, 195.30)


WA_B3 = {  # task -> {arm: (M, SD)}
    0: {"cash_only": (4.74, 1.86), "none": (5.59, 1.45)},  # purchase intention
    2: {"cash_only": (7.16, 5.83), "none": (10.16, 5.49)},  # gallons
    1: {"cash_only": (3.08, 1.64), "none": (3.93, 1.80)},  # transaction utility
    7: {"cash_only": (2.46, 1.61), "none": (2.45, 1.48)},  # regret
    6: {"cash_only": (3.67, 1.56), "none": (3.93, 1.54)},  # fairness
}
WA_B3_F = {0: 12.77, 2: 14.04, 1: 12.21}  # F(1, 198)


def test_wa_b3_means_and_f() -> None:
    w = wide("wa_b3", "promotion")
    assert len(w) == 200
    w["react"] = w[[3, 4, 5]].mean(axis=1)
    for t, want in WA_B3.items():
        for arm, ms in want.items():
            assert stat(w[w["promotion"] == arm][t]) == ms, (t, arm)
    for arm, ms in {"cash_only": (2.85, 1.41), "none": (2.53, 1.44)}.items():
        assert stat(w[w["promotion"] == arm]["react"]) == ms
    for t, f in WA_B3_F.items():
        assert round(oneway(w, "promotion", t), 2) == f, t


FIGURE_W1 = {
    "veteran": 1.70,
    "senior_citizen": 1.76,
    "mother": 1.83,
    "loyalty": 3.42,
    "additional_purchase": 3.79,
    "minimum_dollar": 3.82,
    "minimum_quantity": 4.18,
    "geography": 4.62,
    "referral": 4.68,
    "happy_hour": 4.86,
    "flash_sale": 4.87,
    "student": 6.47,
}


def test_wa_b4_figure_w1_means() -> None:
    df = built("wa_b4")
    assert df["participant_id"].nunique() == 210
    per = df.groupby(["participant_id", "precondition"])["response_num"].mean()
    got = per.groupby("precondition").mean().round(2).to_dict()
    assert got == FIGURE_W1


def test_wa_b4_each_row_names_its_own_promotion_only() -> None:
    df = built("wa_b4")
    assert (df.groupby("participant_id")["condition_num"].nunique() == 12).all()
    assert not df["condition"].str.contains("12 different").any()
    for c, rows in df.groupby("condition_num"):
        assert rows["condition"].nunique() == 1, c
        assert rows["condition"].str.count("Currently, Firm A").eq(1).all(), c
