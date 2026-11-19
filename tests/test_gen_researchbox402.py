"""The researchbox402 recipes (Gunadi & Evangelidis 2022, historical prices) and their key.

The generator builds every scenario and question from the data files' variable labels (the
fielded screens, typos kept), takes the page structure and anything no label carries from
the materials PDF, and ties each data column to its PDF screen by the dollar amounts in the
column's label. These tests stop a
hand edit drifting from it, and check the facts the rows rest on:

- each recipe and coded file is what the generator writes; the codebooks are the labels;
  the PDF's pictures are all Study 5's; every built screen is its label's words, and every
  PDF/label difference is the enumerated one;
- the tie fails when a column's label names another arm's prices;
- N, and N by arm, are the deposit's (no exclusions);
- recomputed from the BUILT rows, each pre-registered analysis equals the same analysis on
  the deposit read column by column (the authors' names, not the generator's mapping): the
  saturated logit of deferral by cell (1a, 2, 3, 4), the number of deferrals per person by
  cell (1b's OLS on the 2 x 2), and the cell means of the price prediction and agreement
  item (2, 3, 4). No analysis script or published table is in the deposit;
- swapping the direction factor breaks the reproduction;
- which rows narrate the choice, and which do not.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import math
import shutil
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pyreadstat
import pytest

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_researchbox402.py"
PROCESSED = REPO / "data" / "processed"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_researchbox402", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_researchbox402"] = mod  # dataclasses look their module up here
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(
    not gen.RAW.exists() or shutil.which("pdftotext") is None,
    reason="researchbox402 deposit not fetched, or poppler not installed",
)
NAMES = ["study1a", "study1b", "study2", "study3", "study4"]


def built(name: str) -> pd.DataFrame:
    path = PROCESSED / f"researchbox402_{name}.parquet"
    if not path.exists():
        pytest.skip(f"researchbox402_{name} not built")
    df = pd.read_parquet(path)
    return pd.concat([df.reset_index(drop=True), pd.json_normalize(df["factors"])], axis=1)


def deposit(label: str) -> pd.DataFrame:
    df, _ = pyreadstat.read_sav(str(gen.DATA / f"Study {label} - Data.sav"))
    return df


# --------------------------------------------------------------------------------------
# The generator
# --------------------------------------------------------------------------------------


@needs_raw
@pytest.mark.parametrize("name", NAMES)
def test_recipe_is_what_the_generator_writes(name: str) -> None:
    (e,) = [x for x in gen.experiments() if x.name == name]
    assert gen.recipe_path(e).read_text() == gen.render(e)
    load(gen.recipe_path(e))


def test_every_built_study_has_a_recipe_and_study5_is_not_built() -> None:
    assert sorted(p.stem for p in (REPO / "recipes").glob("researchbox402_*.yaml")) == sorted(
        f"researchbox402_{n}" for n in NAMES
    )
    assert set(gen.NOT_BUILT) == {"study5"}


@needs_raw
@pytest.mark.parametrize("tag", NAMES)
def test_coded_file_is_what_the_generator_writes(tag: str) -> None:
    assert (gen.RAW / gen.data_file(tag)).read_text() == gen.prep(tag).to_csv(index=False)


@needs_raw
@pytest.mark.parametrize("tag", NAMES)
def test_codebook_is_the_labels(tag: str) -> None:
    gen.check_codebook(tag)


@needs_raw
def test_pictures_are_all_study5s_and_labels_differ_only_as_enumerated() -> None:
    if shutil.which("pdfimages") is None:
        pytest.skip("pdfimages not installed")
    gen.check_pictures()
    gen.check_labels()


@needs_raw
def test_the_label_check_catches_a_new_difference() -> None:
    saved = gen.LABEL_DIFFERENCES["study1a"]
    try:
        gen.LABEL_DIFFERENCES["study1a"] = {}
        with pytest.raises(AssertionError):
            gen.check_labels()
    finally:
        gen.LABEL_DIFFERENCES["study1a"] = saved
    gen.check_labels()


@needs_raw
def test_the_label_check_catches_pdf_words_in_a_built_screen(monkeypatch: Any) -> None:
    real = gen.study1a

    def pdf_worded() -> Any:  # "One week ago", the PDF's word, in place of the fielded one
        e = real()
        e.arms[0].text = e.arms[0].text.replace("One weeks ago", "One week ago")
        return e

    monkeypatch.setattr(gen, "study1a", pdf_worded)
    with pytest.raises(AssertionError):
        gen.check_labels()
    monkeypatch.undo()
    gen.check_labels()


@needs_raw
def test_fielded_words_are_built() -> None:
    a1 = gen.study1a().arms[0].text
    assert "One weeks ago" in a1 and "One week ago" not in a1
    assert gen.study3().outcomes[1].question == (
        "In a week from now, what do you think the price of the speaker will be? (in $)."
    )


@needs_raw
def test_the_tie_fails_on_another_arms_column() -> None:
    _, scr = gen.screens("study1a")
    assert gen.ties("study1a", "DecrHigh", scr) is scr[1]
    with pytest.raises(AssertionError):  # IncrLow's prices are no decrease screen's
        gen.ties("study1a", "IncrLow", scr[:2])
    _, scr = gen.screens("study1b")  # DL3's label is cut short and still unique
    assert gen.ties("study1b", "DL3", scr).header.startswith("[Single decrease - page 3")


@needs_raw
def test_n_and_arms_are_the_deposits() -> None:
    want = {
        "study1a": {1: 201, 2: 201, 3: 201, 4: 199},
        "study2": {1: 203, 2: 201, 3: 200, 4: 198},
        "study3": {1: 252, 2: 250, 3: 252, 4: 253, 5: 250, 6: 249},
        "study4": {1: 251, 2: 251, 3: 251, 4: 249, 5: 253, 6: 251},
    }
    for tag, arms in want.items():
        assert gen.prep(tag)["arm"].value_counts().to_dict() == arms, tag
    b = gen.prep("study1b")
    assert len(b) == 800 and (b["cond_day1"] == 1).all()
    assert [int(b[f"choice_day{k}"].notna().sum()) for k in range(1, 5)] == [800, 662, 541, 484]
    assert gen.prep("study4")["age"].isna().sum() == 2  # the 4 and the 17


# --------------------------------------------------------------------------------------
# The pre-registered analyses, from the built rows and from the deposit
# --------------------------------------------------------------------------------------

# cell -> the deposit's column for the choice (authors' names), and the prediction
DEPOSIT = {
    "study1a": {
        ("decrease", "low"): ("DecrLow", None),
        ("decrease", "high"): ("DecrHigh", None),
        ("increase", "low"): ("IncrLow", None),
        ("increase", "high"): ("IncrHigh", None),
    },
    "study2": {
        ("decrease", "low"): ("DecLow", "PredDecLow"),
        ("decrease", "high"): ("DecHigh", "PredDecHigh"),
        ("increase", "low"): ("IncLow", "PredIncLow"),
        ("increase", "high"): ("IncHigh", "PredIncHigh"),
    },
    "study3": {
        ("decrease", "single"): ("DecLow", "PredDecLow"),
        ("decrease", "monotonic"): ("DecHighMo", "PredDecHighMo"),
        ("decrease", "nonmonotonic"): ("DecHighNon", "PredDecHighNon"),
        ("increase", "single"): ("IncLow", "PredIncLow"),
        ("increase", "monotonic"): ("IncHighMo", "PredIncHigh"),
        ("increase", "nonmonotonic"): ("IncHighNon", "PredIncHighNon"),
    },
    "study4": {
        ("decrease", "single_late"): ("LowDeLa", "PredLowDeLa"),
        ("decrease", "single_early"): ("LowDeEa", "PredDeEa"),
        ("decrease", "multiple"): ("HighDe", "PredHighDe"),
        ("increase", "single_late"): ("LowInLa", "PredLowInLa"),
        ("increase", "single_early"): ("LowInEa", "PredInEa"),
        ("increase", "multiple"): ("HighIn", "PredHighIn"),
    },
}
SECOND = {"study1a": "frequency", "study2": "frequency", "study3": "pattern", "study4": "pattern"}


def log_odds(later: int, now: int) -> float:
    return math.log(later / now)


def saturated(cells: dict[tuple[str, str], tuple[int, int]]) -> dict[str, float]:
    """The saturated logit of deferral, dummy-coded against (decrease, first level):
    intercept, increase, each other level, and each interaction, from cell counts."""
    lo = {c: log_odds(*n) for c, n in cells.items()}
    levels = list(dict.fromkeys(c[1] for c in cells))
    base = lo["decrease", levels[0]]
    out = {"(Intercept)": base, "increase": lo["increase", levels[0]] - base}
    for lv in levels[1:]:
        out[lv] = lo["decrease", lv] - base
        out[f"increase:{lv}"] = lo["increase", lv] - lo["decrease", lv] - out["increase"]
    return out


def built_cells(name: str, swap: bool = False) -> dict[tuple[str, str], tuple[int, int]]:
    df = built(name)
    df = df[df["task_num"] == 0]
    if swap:
        df["direction"] = df["direction"].map({"decrease": "increase", "increase": "decrease"})
    out = {}
    for cell in DEPOSIT[name]:
        rows = df[(df["direction"] == cell[0]) & (df[SECOND[name]] == cell[1])]
        out[cell] = (int((rows["response_num"] == 2).sum()), int((rows["response_num"] == 1).sum()))
    return out


def deposit_cells(name: str) -> dict[tuple[str, str], tuple[int, int]]:
    df = deposit(gen.LABEL[name])
    return {
        cell: (int((df[c] == 2).sum()), int((df[c] == 1).sum()))
        for cell, (c, _) in DEPOSIT[name].items()
    }


@pytest.mark.parametrize("name", ["study1a", "study2", "study3", "study4"])
def test_built_rows_reproduce_the_deferral_logit(name: str) -> None:
    got, want = saturated(built_cells(name)), saturated(deposit_cells(name))
    assert got.keys() == want.keys()
    assert all(abs(got[k] - want[k]) < 1e-12 for k in got), (got, want)
    assert sum(sum(n) for n in built_cells(name).values()) == gen.N[name]


@pytest.mark.parametrize("name", ["study2", "study3", "study4"])
def test_built_rows_reproduce_the_prediction_means(name: str) -> None:
    df = built(name)
    df = df[df["task_num"] == 1]
    dep = deposit(gen.LABEL[name])
    for cell, (_, pred) in DEPOSIT[name].items():
        rows = df[(df["direction"] == cell[0]) & (df[SECOND[name]] == cell[1])]
        assert len(rows) == dep[pred].notna().sum(), (name, cell)
        assert abs(rows["response_num"].mean() - dep[pred].mean()) < 1e-12, (name, cell)


def test_built_rows_reproduce_study2_agreement_means() -> None:
    df = built("study2")
    df = df[df["task_num"] == 2]
    dep = deposit("2")
    for (direction, freq), (choice, _) in DEPOSIT["study2"].items():
        rows = df[(df["direction"] == direction) & (df["frequency"] == freq)]
        col = choice.replace("Dec", "TempDec").replace("Inc", "TempInc") + "_1"
        assert abs(rows["response_num"].mean() - dep[col].mean()) < 1e-12, col
        word = "decrease" if direction == "decrease" else "increase"
        assert rows["outcome"].str.contains(f"continue to {word} in the future").all()


def test_built_rows_reproduce_study1b_deferral_counts() -> None:
    df = built("study1b")
    dep = deposit("1b")
    groups = {
        "DL": ("decrease", "low"),
        "DH": ("decrease", "high"),
        "IL": ("increase", "low"),
        "IH": ("increase", "high"),
    }
    # the deposit: each person's arm and number of "later" answers, column by column
    arm = pd.Series(None, index=dep.index, dtype=object)
    count = pd.Series(0, index=dep.index)
    for g in groups:
        arm[dep[f"{g}1"].notna()] = g
        for k in range(1, 5):
            count += (dep[f"{g}{k}"] == 2).astype(int)
    assert arm.notna().all()
    # the built rows: the same count per person; the arm is not on a day-1 row (none was
    # shown yet), so it is read from the deposit by the row number in the id
    row = df["participant_id"].str.rsplit("_", n=1).str[1].astype(int) - 1
    later = (df["response_num"] == 2).groupby(row).sum()
    assert len(later) == 800
    assert (later.sort_index().values == count.values).all()
    for g, (direction, freq) in groups.items():
        mine = df[(df["direction"] == direction) & (df["frequency"] == freq)]
        assert set(arm[row[mine.index]]) == {g}  # days 2-4 rows sit in the deposit's arm
        mean_built = later[arm == g].mean()
        assert abs(mean_built - count[arm == g].mean()) < 1e-12
    # the pre-registered OLS on the 2 x 2 is saturated: its interaction is this contrast
    m = {g: count[arm == g].mean() for g in groups}
    inter = (m["IH"] - m["IL"]) - (m["DH"] - m["DL"])
    mb = {g: later[arm == g].mean() for g in groups}
    assert abs(((mb["IH"] - mb["IL"]) - (mb["DH"] - mb["DL"])) - inter) < 1e-12


def test_swapping_the_direction_factor_breaks_the_reproduction() -> None:
    for name in ("study2", "study4"):
        got = saturated(built_cells(name, swap=True))
        want = saturated(deposit_cells(name))
        assert not all(abs(got[k] - want[k]) < 1e-12 for k in got), name


# --------------------------------------------------------------------------------------
# What the rows narrate
# --------------------------------------------------------------------------------------


def test_only_fixed_order_rows_narrate_the_choice() -> None:
    asked = gen.ASKED
    for name, narrated in (("study2", {1, 2}), ("study3", {1}), ("study4", set())):
        df = built(name)
        for t, rows in df.groupby("task_num"):
            ends = rows["condition"].str.endswith(asked)
            assert ends.all() if t in narrated else not ends.any(), (name, t)
    for name in ("study1a", "study1b"):
        assert not built(name)["condition"].str.contains("You were asked").any()


def test_study1b_day1_is_one_condition_and_later_days_follow_later() -> None:
    df = built("study1b")
    day1 = df[df["task_num"] == 0]
    assert len(day1) == 800 and day1["condition_num"].nunique() == 1
    assert day1["condition"].str.endswith("Currently, the price of the TV is $1200.").all()
    for k in range(1, 4):
        nxt = df[df["task_num"] == k]
        prev = df[(df["task_num"] == k - 1) & (df["response_num"] == 2)]
        assert set(nxt["participant_id"]) == set(prev["participant_id"]), k
        assert nxt["condition"].str.contains(f"It is now January {16 + k}, 2021.").all()
