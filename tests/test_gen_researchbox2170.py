"""The researchbox2170 recipes (Maesen & Ang, buy now pay later) and their answer key.

The generator decodes the authors' jamovi .omv files, reads each stimulus screen and
question from the fielded .qsf, and narrates the earlier pages into each later row's
condition. These tests stop a hand edit drifting from it, and check the facts the rows rest
on:

- each recipe and coded file is what the generator writes;
- the fielded and submission .qsf exports agree on every question shown;
- N, and N by arm, equal the authors' jamovi outputs (598: 200 / 197 / 201; 597: 297 / 300);
- every scale runs from the first answer shown to the last, and the check that says so
  fails on a reversed scale;
- the follow-up rows carry the earlier pages in the order the deposit records;
- recomputed from the BUILT rows, the jamovi outputs come out: Study 3's financial
  constraint by arm (means, SDs, F = 12.2) and its misled / benefit / price-attractiveness
  means and F tests, and Supplementary Study 2's three t tests;
- swapping the payment factor breaks them.

Studies 2 and 4 and Supplementary Studies 1a, 1b and 3 are not built; the generator's
docstring says why. Tests needing the gitignored deposit or build skip on a fresh clone.
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
GEN = REPO / "scripts" / "gen_researchbox2170.py"
PROCESSED = REPO / "data" / "processed"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_researchbox2170", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_researchbox2170"] = mod  # dataclasses look their module up here
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.RAW.exists(), reason="researchbox2170 deposit not fetched")
NAMES = ["study3", "study3_followup", "ss2"]


def built(name: str) -> pd.DataFrame:
    path = PROCESSED / f"researchbox2170_{name}.parquet"
    if not path.exists():
        pytest.skip(f"researchbox2170_{name} not built")
    df = pd.read_parquet(path)
    return pd.concat([df.reset_index(drop=True), pd.json_normalize(df["factors"])], axis=1)


def wide(df: pd.DataFrame) -> pd.DataFrame:
    return df.pivot(index="participant_id", columns="task_num", values="response_num")


def per_person(df: pd.DataFrame, col: str) -> pd.Series:
    return df.drop_duplicates("participant_id").set_index("participant_id")[col]


def f_stat(score: pd.Series, group: pd.Series) -> float:
    """One-way ANOVA F (Fisher's), as jamovi's anovaOneW reports it."""
    grand = score.mean()
    parts = [score[group == g] for g in sorted(group.unique())]
    between = sum(len(p) * (p.mean() - grand) ** 2 for p in parts) / (len(parts) - 1)
    within = sum(((p - p.mean()) ** 2).sum() for p in parts) / (len(score) - len(parts))
    return float(between / within)


def t_stat(a: pd.Series, b: pd.Series) -> float:
    """Student's t, pooled variance, as jamovi's ttestIS reports it."""
    na, nb = len(a), len(b)
    pooled = ((na - 1) * a.var() + (nb - 1) * b.var()) / (na + nb - 2)
    return float((a.mean() - b.mean()) / (pooled * (1 / na + 1 / nb)) ** 0.5)


@needs_raw
@pytest.mark.parametrize("exp", gen.experiments(), ids=lambda e: e.name)
def test_recipe_is_what_the_generator_writes(exp: Any) -> None:
    assert gen.recipe_path(exp).read_text() == gen.render(exp)
    load(gen.recipe_path(exp))


def test_every_experiment_has_a_recipe() -> None:
    assert sorted(p.stem for p in (REPO / "recipes").glob("researchbox2170_*.yaml")) == sorted(
        f"researchbox2170_{n}" for n in NAMES
    )


@needs_raw
@pytest.mark.parametrize("tag", list(gen.QSF))
def test_coded_file_is_what_the_generator_writes(tag: str) -> None:
    assert (gen.RAW / gen.data_file(tag)).read_text() == gen.prep(tag).to_csv(index=False)


@needs_raw
@pytest.mark.parametrize("tag", list(gen.QSF))
def test_the_two_exports_agree(tag: str) -> None:
    gen.check_qsf_pair(tag)


@needs_raw
def test_n_is_the_jamovi_n() -> None:
    # jamovi Group Descriptives: Upfront LS 200, Defer LS 197, BNPL 201 (Study 3);
    # Defer LS 297, BNPL (2) 300 (Supplementary Study 2).
    assert gen.deposit("study3")["BNPL"].value_counts().to_dict() == {0: 200, 1: 197, 2: 201}
    assert gen.deposit("ss2")["BNPL"].value_counts().to_dict() == {1: 297, 2: 300}


@needs_raw
def test_every_scale_runs_first_answer_to_last() -> None:
    for tag in gen.QSF:
        sv = gen.Survey(gen.QSF[tag][0])
        for qid in ("QID80",):
            q = sv.qs[qid]
            first = gen.norm(q["Answers"][str(q["AnswerOrder"][0])]["Display"])
            assert gen.scale_of(q) == (1, 9, first, "Very much") and first == "Not at all"


@needs_raw
def test_the_scale_check_catches_a_reversed_scale() -> None:
    q = dict(gen.Survey(gen.QSF["study3"][0]).qs["QID80"])
    q["AnswerOrder"] = list(reversed(q["AnswerOrder"]))
    with pytest.raises(AssertionError):
        gen.scale_of(q)


@needs_raw
def test_screens_are_the_qsf_words() -> None:
    for e in gen.experiments():
        sv = gen.Survey(gen.QSF[e.tag][0])
        shown = {gen.lines(q["QuestionText"]) for q in sv.qs.values() if q["QuestionType"] == "DB"}
        for a in e.arms:
            assert a.screen in shown
            assert "<" not in a.screen and "${" not in a.screen


def test_followup_rows_follow_the_recorded_block_order() -> None:
    df = built("study3_followup")
    amt = '"What is the price of the T-shirt?"'
    pleasure = '"I would get a lot of pleasure from this purchase."'
    for _, r in df.iterrows():
        price_first = r["block_order"] == "price_first"
        if r["task_num"] <= 4:  # the price page itself
            assert amt in r["condition"]
            assert (pleasure in r["condition"]) is not price_first
        elif r["task_num"] <= 8:  # benefit statements
            assert (amt in r["condition"]) is price_first
            assert pleasure not in r["condition"]
        else:  # price attractiveness, the benefits block's second page
            assert (amt in r["condition"]) is price_first
            assert pleasure in r["condition"]


@needs_raw
def test_block_order_is_the_deposits() -> None:
    df = built("study3_followup")
    order = per_person(df, "block_order")
    dep = gen.deposit("study3").set_index("ResponseId")["FL_33_DO"]
    want = dep.map({gen.PRICE_FIRST: "price_first", gen.BENEFITS_FIRST: "benefits_first"})
    got = order.rename(lambda p: p.removeprefix("researchbox2170:study3_"))
    assert got.sort_index().to_dict() == want.sort_index().to_dict()


def _study3_fc(payment: pd.Series, df: pd.DataFrame) -> pd.DataFrame:
    fc = (10 - wide(df)[[0, 1, 2, 3]]).mean(axis=1)  # jamovi: FC = MEAN of reversed items
    return fc.groupby(payment).agg(["count", "mean", "std"]).round(2)


def test_built_rows_reproduce_study3_financial_constraint() -> None:
    # jamovi, One-Way ANOVA - Perceived Financial Constraints: F(2, 595) = 12.2; Upfront LS
    # 6.51 (1.71), Defer LS 6.05 (2.23), BNPL 5.48 (2.29).
    df = built("study3")
    pay = per_person(df, "payment")
    got = _study3_fc(pay, df)
    assert {k: tuple(v) for k, v in got.iterrows()} == {
        "pay_now": (200, 6.51, 1.71),
        "pay_in_30_days": (197, 6.05, 2.23),
        "three_instalments": (201, 5.48, 2.29),
    }
    fc = (10 - wide(df)[[0, 1, 2, 3]]).mean(axis=1)
    assert round(f_stat(fc, pay), 1) == 12.2


def test_built_rows_reproduce_study3_alternative_mechanisms() -> None:
    # jamovi, One-Way ANOVA - Alternative Mechanisms: M F = 2.35, PB 1.50, Att 2.83, and the
    # group means; Welch ANOVA table's group means for M1_1..M5_1.
    df = built("study3_followup")
    w, pay = wide(df), per_person(df, "payment")
    scores = {
        "M": w[[0, 1, 2, 3, 4]].mean(axis=1),
        "PB": pd.concat([w[[5, 6, 7]], 10 - w[[8]]], axis=1).mean(axis=1),
        "Att": w[[9, 10, 11]].mean(axis=1),
    }
    want = {
        "M": ((2.07, 2.30, 2.32), 2.35),
        "PB": ((4.18, 3.96, 4.21), 1.50),
        "Att": ((4.56, 4.71, 5.01), 2.83),
    }
    order = ["pay_now", "pay_in_30_days", "three_instalments"]
    for name, s in scores.items():
        means = s.groupby(pay).mean().round(2)
        assert tuple(means[o] for o in order) == want[name][0], name
        assert round(f_stat(s, pay), 2) == want[name][1], name
    items = {
        0: (1.72, 2.02, 2.07),
        1: (1.76, 1.81, 2.08),
        2: (1.51, 1.93, 1.94),
        3: (3.50, 3.29, 3.25),
        4: (1.84, 2.46, 2.27),
    }
    for t, m in items.items():
        means = w[t].groupby(pay).mean().round(2)
        assert tuple(means[o] for o in order) == m, t


def test_built_rows_reproduce_ss2_t_tests() -> None:
    # jamovi, Independent Samples T-Tests (Defer LS v BNPL (2)): FC 6.12 (2.20) v 5.77
    # (2.14), t = 1.98; PC 3.62 (2.10) v 4.27 (2.17), t = -3.69; BC 4.30 (2.50) v 4.92
    # (2.41), t = -3.12; N 297 v 300.
    df = built("ss2")
    w, pay = wide(df), per_person(df, "payment")
    for cols, reverse, want in (
        ([0, 1, 2, 3], True, ((6.12, 2.20), (5.77, 2.14), 1.98)),
        ([4, 5, 6, 7], False, ((3.62, 2.10), (4.27, 2.17), -3.69)),
        ([8, 9, 10, 11], False, ((4.30, 2.50), (4.92, 2.41), -3.12)),
    ):
        s = w[cols].mean(axis=1)
        s = 10 - s if reverse else s
        a, b = s[pay == "pay_in_21_days"], s[pay == "three_instalments"]
        assert (len(a), len(b)) == (297, 300)
        assert (round(a.mean(), 2), round(a.std(), 2)) == want[0]
        assert (round(b.mean(), 2), round(b.std(), 2)) == want[1]
        assert round(t_stat(a, b), 2) == want[2]


def test_swapping_the_payment_factor_breaks_the_reproduction() -> None:
    df = built("study3")
    pay = (
        per_person(df, "payment")
        .map({"pay_now": "three_instalments", "three_instalments": "pay_now"})
        .fillna("pay_in_30_days")
    )
    assert _study3_fc(pay, df).loc["pay_now", "mean"] != 6.51
    df = built("ss2")
    w = wide(df)
    pay = per_person(df, "payment")
    swapped = pay.map(
        {"pay_in_21_days": "three_instalments", "three_instalments": "pay_in_21_days"}
    )
    fc = 10 - w[[0, 1, 2, 3]].mean(axis=1)
    assert round(fc[swapped == "pay_in_21_days"].mean(), 2) != 6.12


def _alpha(items: pd.DataFrame) -> float:
    k = items.shape[1]
    return float(k / (k - 1) * (1 - items.var().sum() / items.sum(axis=1).var()))


def test_built_rows_reproduce_ss2_item_reliability() -> None:
    # jamovi, Item Reliability Statistics, Cronbach's alpha if item dropped: FC1_1..FC1_4
    # .852 .887 .836 .814; PC1..PC4 .849 .854 .859 .840; BC1..BC4 .967 .973 .965 .966.
    # Each item's figure differs, so this ties every task_num to its deposit column.
    w = wide(built("ss2"))
    for cols, want in (
        ([0, 1, 2, 3], (0.852, 0.887, 0.836, 0.814)),
        ([4, 5, 6, 7], (0.849, 0.854, 0.859, 0.840)),
        ([8, 9, 10, 11], (0.967, 0.973, 0.965, 0.966)),
    ):
        got = tuple(round(_alpha(w[[c for c in cols if c != d]]), 3) for d in cols)
        assert got == want, cols
