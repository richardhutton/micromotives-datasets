"""The researchbox231 recipes (De La Rosa & Tully, payment frequency) and their answer key.

The generator replays each Qualtrics survey flow for each arm (embedded-data arithmetic,
branches, display logic, loop-and-merge) to get the screens a respondent saw, and reads
the answers from the deposit's CSVs. These tests stop a hand edit drifting from it, and
check the facts the rows rest on:

- each recipe and coded file is what the generator writes;
- N equals the N the paper (Studies 2-5) or the pre-registration (S1, S3) gives;
- every balance a condition shows is the previous balance plus that screen's income or
  expense, so the replayed arithmetic is self-consistent from the opening balance;
- each decision row lists the options in the .qsf's order, and its answer code points at
  the option whose dollar amount the deposit records;
- recomputed from the BUILT rows, the paper's Study 3 means and SDs and Study 4 simple
  effects come out to the published figures; the paper's Study 2 and Study 5 totals come
  out from the deposit under the same exclusions (which checks N and the arm labels);
- swapping the pay factor breaks the Study 3 means.

Study 6 (Instant Pay), Supplemental Study 4 (expense listing) and every decision after the
first are not built; the generator's docstring says why.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_researchbox231.py"
PROCESSED = REPO / "data" / "processed"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_researchbox231", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_researchbox231"] = mod  # dataclasses look their module up here
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.RAW.exists(), reason="researchbox231 deposit not fetched")
NAMES = [
    "study2",
    "study3",
    "study3_ease",
    "study4",
    "study4_ease",
    "study5",
    "s1",
    "s2",
]
DECISIONS = {"study2": "2", "study5": "5", "s1": "S1", "s2": "S2"}


def built(name: str) -> pd.DataFrame:
    path = PROCESSED / f"researchbox231_{name}.parquet"
    if not path.exists():
        pytest.skip(f"researchbox231_{name} not built")
    df = pd.read_parquet(path)
    return pd.concat([df.reset_index(drop=True), pd.json_normalize(df["factors"])], axis=1)


def deposit(tag: str) -> pd.DataFrame:
    """The deposit after the exclusions, read here, not through the generator."""
    df = pd.read_csv(gen.DATA_DIR / gen.DATA_FILES[tag], encoding="utf-8-sig")
    for prefix, bad in gen.EXCLUDE[tag][0]:
        c = next(c for c in df.columns if c.strip().startswith(prefix))
        df = df[df[c] != bad]
    return df


@needs_raw
@pytest.mark.parametrize("exp", gen.experiments(), ids=lambda e: e.name)
def test_recipe_is_what_the_generator_writes(exp: Any) -> None:
    assert gen.recipe_path(exp).read_text() == gen.render(exp)
    load(gen.recipe_path(exp))


def test_every_experiment_has_a_recipe() -> None:
    assert sorted(p.stem for p in (REPO / "recipes").glob("researchbox231_*.yaml")) == sorted(
        f"researchbox231_{n}" for n in NAMES
    )


@needs_raw
@pytest.mark.parametrize("tag", list(gen.CODED))
def test_coded_file_is_what_the_generator_writes(tag: str) -> None:
    assert (gen.RAW / gen.data_file(tag)).read_text() == gen.prep(tag).to_csv(index=False)


@needs_raw
@pytest.mark.parametrize("tag", list(gen.EXCLUDE))
def test_n_is_the_published_n(tag: str) -> None:
    published = {"2": 401, "3": 112, "4": 528, "5": 1120, "S1": 146, "S2": 402, "S3": 404}
    assert len(deposit(tag)) == gen.EXCLUDE[tag][1] == published[tag]


_MONEY = re.compile(
    r"^(Income|Expense|Expenses|Checking Account Balance|Current Checking "
    r"Account Balance|Overdraft Fee): \$ ?(-?[\d,]+)$"
)


def _ledger(text: str) -> list[tuple[str, int]]:
    out = []
    for line in text.split("\n"):
        m = _MONEY.match(line.strip())
        if m:
            out.append((m.group(1), int(m.group(2).replace(",", ""))))
    return out


def _check_ledger(text: str) -> int:
    """Every balance shown equals the last balance plus what moved since; returns checks."""
    balance: int | None = None
    moved = seen = 0
    for kind, amount in _ledger(text):
        if kind in ("Income", "Expense", "Expenses", "Overdraft Fee"):
            moved += amount
        elif balance is None:  # S2 shows no opening balance; start at the first shown
            balance, moved = amount, 0
        else:
            assert amount == balance + moved, (kind, amount, balance, moved)
            balance, moved = amount, 0
            seen += 1
    return seen


@needs_raw
@pytest.mark.parametrize("exp", gen.experiments(), ids=lambda e: e.name)
def test_every_balance_follows_from_the_last(exp: Any) -> None:
    for arm in exp.arms:
        assert _check_ledger(arm.text) >= 2, (exp.name, arm.factors)


def test_the_ledger_check_catches_a_wrong_balance() -> None:
    good = (
        "Checking Account Balance: $ 850\nExpense: $ -650\nCurrent Checking Account Balance: $ 200"
        "\nIncome: $ 140\nCurrent Checking Account Balance: $ 340"
    )
    assert _check_ledger(good) == 2
    with pytest.raises(AssertionError):
        _check_ledger(good.replace("$ 340", "$ 341"))


@pytest.mark.parametrize("name", list(DECISIONS))
def test_decision_rows_follow_the_qsf_and_the_deposit(name: str) -> None:
    tag = DECISIONS[name]
    df = built(name)
    exp = next(e for e in gen.experiments() if e.name == name)
    target = gen.Survey(tag).qs[exp.outcomes[0].qid]
    opts = gen.decision_options(target)
    listed = "; ".join(f'{i} means "{lab}"' for i, (_, _, lab) in enumerate(opts, 1))
    assert all(listed in o for o in df["outcome"])
    dollars = {i: d for i, (_, d, _) in enumerate(opts, 1)}
    d = deposit(tag)
    pid = d["ResponseId" if "ResponseId" in d.columns else "Response ID"]
    want = dict(zip(f"{gen.CODED[tag]}_" + pid, d["Decision 1"].astype(int), strict=True))
    got = {
        p.removeprefix(f"{gen.STUDY_ID}:"): dollars[int(r)]
        for p, r in zip(df["participant_id"], df["response_num"], strict=True)
    }
    assert got == want
    shares = df.groupby("pay_frequency")["response_num"].apply(lambda s: (s == 1).mean())
    cond = d["Condition"].map(_LEVELS[tag])
    theirs = (d["Decision 1"] == opts[0][1]).groupby(cond).mean()
    assert shares.round(12).to_dict() == theirs.round(12).to_dict()


_LEVELS = {
    "2": {"day": "daily", "week": "weekly"},
    "5": {"Daily": "daily", "Bi-Weekly": "biweekly"},
    "S1": {"day": "daily", "week": "weekly"},
    "S2": {"day": "daily", "week": "weekly"},
    "S3": {"day": "daily", "bi-week": "biweekly"},
}


def _index(df: pd.DataFrame, positive: list[int], negative: list[int]) -> pd.Series:
    wide = df.pivot(index="participant_id", columns="task_num", values="response_num")
    return (wide[positive].sum(axis=1) + (100 - wide[negative]).sum(axis=1)) / (
        len(positive) + len(negative)
    )


def _cells(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    return df.drop_duplicates("participant_id").set_index("participant_id")[keys]


def test_built_rows_reproduce_the_papers_study3() -> None:
    # Paper, Study 3: subjective wealth 44.40 (25.55) daily v 34.57 (24.17) weekly;
    # prediction uncertainty 35.29 (23.16) v 50.34 (28.63).
    for name, pos, neg, want in (
        ("study3", [0, 1, 2], [3, 4, 5], {"daily": (44.40, 25.55), "weekly": (34.57, 24.17)}),
        ("study3_ease", [2, 3], [0, 1], {"daily": (35.29, 23.16), "weekly": (50.34, 28.63)}),
    ):
        df = built(name)
        idx = _index(df, pos, neg)
        pay = _cells(df, ["pay_frequency"])["pay_frequency"]
        got = idx.groupby(pay).agg(["mean", "std"]).round(2)
        assert {k: tuple(v) for k, v in got.iterrows()} == want, name


def test_built_rows_reproduce_the_papers_study4_simple_effects() -> None:
    # Paper, Study 4: daily-minus-weekly pay, within daily expenses and within weekly
    # expenses: wealth b = 19.32 and 2.94; uncertainty b = -16.87 and 4.24.
    for name, pos, neg, want in (
        ("study4", [0, 1, 2], [3, 4, 5], {"daily": 19.32, "weekly": 2.94}),
        ("study4_ease", [2, 3], [0, 1], {"daily": -16.87, "weekly": 4.24}),
    ):
        df = built(name)
        idx = _index(df, pos, neg)
        cells = _cells(df, ["pay_frequency", "expense_frequency"])
        means = idx.groupby([cells["expense_frequency"], cells["pay_frequency"]]).mean()
        for exp_level, b in want.items():
            assert round(means[(exp_level, "daily")] - means[(exp_level, "weekly")], 2) == b


@needs_raw
def test_deposit_reproduces_the_papers_study2_and_study5_totals() -> None:
    # Paper: Study 2 high-cost decisions 6.17 (2.55) v 5.16 (2.09), spending $404.35 v
    # $363.55; Study 5 17.00 (3.63) v 15.21 (3.30), $2,919.58 v $2,816.52.
    d = deposit("2")
    g = d.groupby("Condition")
    assert g["Total Number of Expensive Decisions"].mean().round(2).to_dict() == {
        "day": 6.17,
        "week": 5.16,
    }
    assert g["Total Spending "].mean().round(2).to_dict() == {"day": 404.35, "week": 363.55}
    d = deposit("5")
    g = d.groupby("Condition")
    assert g["Number of Expensive Decisions"].mean().round(2).to_dict() == {
        "Daily": 17.00,
        "Bi-Weekly": 15.21,
    }
    assert g["Total Spending "].mean().round(2).to_dict() == {
        "Daily": 2919.58,
        "Bi-Weekly": 2816.52,
    }


def test_swapping_the_pay_factor_breaks_study3() -> None:
    df = built("study3")
    idx = _index(df, [0, 1, 2], [3, 4, 5])
    pay = _cells(df, ["pay_frequency"])["pay_frequency"]
    swapped = pay.map({"daily": "weekly", "weekly": "daily"})
    assert round(idx.groupby(swapped).mean()["daily"], 2) != 44.40
