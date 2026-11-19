"""The researchbox3299 recipes (Gaertig & Simmons, uncertain price promotions) and their answer key.

The generator reads every word from the .qsf (asserting each transcribed sentence and every
piped value is in it), the hotel listings from Qualtrics graphics pinned by sha256, and the
answers from the deposit's spreadsheets. These tests stop a hand edit drifting from it, and
check the facts the rows rest on:

- each recipe and coded file is what the generator writes;
- each row's options are rendered in that respondent's recorded order, and the answer code
  points at the option the row shows in that place;
- recomputed from the BUILT rows by each do file's own logic, every per-cell statistic the
  do files tabulate equals the same statistic computed straight from the deposit, and N
  equals the N each do file states;
- swapping the order factor breaks the Study 4 means.

Studies 1, 2, S1a, S1b, S1c and S2 are not built (their prices exist only in screenshots;
rich, 19 Nov 2026), so neither are their tests, including the check against the authors'
2019 talk, which covered S2.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_researchbox3299.py"
PROCESSED = REPO / "data" / "processed"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_researchbox3299", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_researchbox3299"] = mod  # dataclasses look their module up here
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.RAW.exists(), reason="researchbox3299 deposit not fetched")
NAMES = [
    "study3",
    "study3_wealth",
    "study4",
    "study4_pretest",
    "study5",
    "study5_size",
    "s3",
    "s4",
]


def built(name: str) -> pd.DataFrame:
    path = PROCESSED / f"researchbox3299_{name}.parquet"
    if not path.exists():
        pytest.skip(f"researchbox3299_{name} not built")
    df = pd.read_parquet(path)
    return pd.concat([df.reset_index(drop=True), pd.json_normalize(df["factors"])], axis=1)


def deposit(tag: str) -> pd.DataFrame:
    """The deposit after the do file's exclusions, read here, not through the generator."""
    df = pd.read_excel(gen.DATA_DIR / gen.DATA_FILES[tag])
    for flag in gen.EXCLUDE[tag][0]:
        df = df[df[flag] != 1]
    if tag in gen.ANSWERED:
        df = df[df[gen.ANSWERED[tag]].notna()]
    return df


@needs_raw
@pytest.mark.parametrize("exp", gen.experiments(), ids=lambda e: e.name)
def test_recipe_is_what_the_generator_writes(exp: Any) -> None:
    assert gen.recipe_path(exp).read_text() == gen.render(exp)
    load(gen.recipe_path(exp))


def test_every_experiment_has_a_recipe() -> None:
    assert sorted(p.stem for p in (REPO / "recipes").glob("researchbox3299_*.yaml")) == sorted(
        f"researchbox3299_{n}" for n in NAMES
    )


@needs_raw
@pytest.mark.parametrize("tag", list(gen.CODED))
def test_coded_file_is_what_the_generator_writes(tag: str) -> None:
    assert (gen.RAW / gen.data_file(tag)).read_text() == gen.prep(tag).to_csv(index=False)


@needs_raw
@pytest.mark.parametrize("tag", list(gen.EXCLUDE))
def test_n_is_the_do_files_n(tag: str) -> None:
    assert len(deposit(tag)) == gen.EXCLUDE[tag][1]


@needs_raw
def test_the_two_questionnaire_exports_agree() -> None:
    for tag in gen.CODED:
        gen.check_qsf_pair(tag)


def test_two_option_rows_list_options_in_the_recorded_order() -> None:
    for name in ("study4", "study5", "s3"):
        df = built(name)
        for _, r in df.drop_duplicates("condition_num").iterrows():
            first = r["condition"].split("Promotion A: ")[1].split("\n")[0]
            is_sure = " off of the " in first.split(" & ")[-1]
            assert is_sure == (r["order"] == "sure_first"), (name, first)


def _recoded(df: pd.DataFrame) -> pd.Series:
    return df["response_num"].where(df["order"] == "sure_first", 7 - df["response_num"])


def _dep_recoded(d: pd.DataFrame, col: str = "Rating") -> pd.Series:
    return d[col].where(d["SureDiscountFirst"] == 1, 7 - d[col])


@needs_raw
def test_built_rows_reproduce_the_do_files_tables() -> None:
    def same(ours: pd.Series, theirs: pd.Series) -> None:
        a, b = ours.sort_index(), theirs.sort_index()
        assert list(a.round(10)) == list(b.round(10)), (a, b)

    # Rating studies: mean of the order-reversed rating, by Condition.
    for name, tag, col, keys in (
        ("study3", "3", "Rating", ["context_price"]),
        ("study4", "4", "Rating", ["price", "framing"]),
        ("study5", "5", "Rating", ["framing"]),
        ("s3", "S3", "Rating", ["context_price"]),
    ):
        df, d = built(name), deposit(tag)
        ours = _recoded(df).groupby([df[k] for k in keys]).mean()
        theirs = _dep_recoded(d, col).groupby(d["Condition"]).mean()
        assert sorted(ours.round(10)) == sorted(theirs.round(10)), name

    s4, d = built("s4"), deposit("S4")
    for task, col in ((0, "ContextRating"), (1, "Rating")):
        t = s4[s4["task_num"] == task]
        same(
            _recoded(t).groupby(t["context_price"].map({"low": 1, "high": 2})).mean(),
            _dep_recoded(d, col).groupby(d["Condition"]).mean(),
        )

    # Unrecoded 7-point measures.
    for name, tag, col, key, codes in (
        ("study3_wealth", "3", "Wealthy", "context_price", {"low": 1, "high": 2}),
        ("study5_size", "5", "Size", "framing", {"percent": 1, "dollar": 2}),
    ):
        df, d = built(name), deposit(tag)
        same(
            df["response_num"].groupby(df[key].map(codes)).mean(),
            d[col].groupby(d["Condition"]).mean(),
        )
    pre, d = built("study4_pretest"), deposit("4_Pretest")
    same(
        pre["response_num"].groupby(pre["condition_num"] + 1).mean(),
        d["Rating"].groupby(d["Condition"]).mean(),
    )


def test_swapping_the_order_factor_breaks_study4() -> None:
    df = built("study4")
    right = _recoded(df).groupby([df["price"], df["framing"]]).mean()
    swapped = df.assign(
        order=df["order"].map({"sure_first": "uncertain_first", "uncertain_first": "sure_first"})
    )
    wrong = _recoded(swapped).groupby([df["price"], df["framing"]]).mean()
    assert (abs(right - wrong) > 0.05).any()
