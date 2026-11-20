"""The researchbox482 recipe (Hu, Gaertig and Dietvorst, time estimates) and its key.

The generator reads Study S3's three screens per app from the .qsf through its display
logic, pipes in each arm's estimate, and codes the deposit with the authors' exclusions.
These tests stop a hand edit drifting from it, and check the facts the rows rest on:

- the recipe and the coded file are what the generator writes; only S3 has a recipe, and
  every other study is in NOT_BUILT;
- every .qsf's pictures are where PICTURES says, S3 has none, and a planted one is seen;
- the sequence studies really randomise their pages and record no order;
- the response page's grey repeat of the scenario is the scenario (a changed one fails);
- the matrix columns are the bins in order (the "Yes" share peaks at the bin holding 43);
- the authors' exclusions give their N (188 of 198);
- recomputed from the BUILT rows, the authors' model (count of "Yes" on the range contrast
  with an app fixed effect) and the cell means equal the deposit's, to 1e-9, and the
  supplement's numbers; a swapped estimate level breaks it.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_researchbox482.py"
PROCESSED = REPO / "data" / "processed"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_researchbox482", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_researchbox482"] = mod  # dataclasses look their module up here
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.BOX.exists(), reason="researchbox482 deposit not fetched")


def built() -> pd.DataFrame:
    path = PROCESSED / "researchbox482_s3.parquet"
    if not path.exists():
        pytest.skip("researchbox482_s3 not built")
    return pd.read_parquet(path)


@needs_raw
def test_recipe_is_what_the_generator_writes() -> None:
    e = gen.experiment()
    assert gen.recipe_path(e).read_text() == gen.render(e)
    r = load(gen.recipe_path(e))
    assert len(r.condition.arms) == 4 and len(r.outcomes) == 11


def test_the_recipes_and_what_is_not_built() -> None:
    want = ["researchbox482_s3"] + [
        f"researchbox482_{st.name}_{b}" for st in gen.SEQ_STUDIES for b in st.blocks
    ]
    assert sorted(p.stem for p in (REPO / "recipes").glob("researchbox482_*.yaml")) == sorted(want)
    assert set(gen.NOT_BUILT) == {"study4", "s1", "s2"}


@needs_raw
def test_coded_file_is_what_the_generator_writes() -> None:
    assert (gen.RAW / gen.data_file()).read_text() == gen.prep().to_csv(index=False)


@needs_raw
def test_codebook_pictures_and_sequences() -> None:
    gen.check_codebook()
    gen.check_pictures()
    gen.check_sequences()
    assert "Graphic" not in gen.Survey(gen.QSF).raw


def test_a_planted_picture_is_seen() -> None:
    assert gen.graphics_in('{"QuestionText":"<p>x</p>"}') == (0, set())
    assert gen.graphics_in('{"QuestionText":"<img src=x>"}')[0] == 1
    assert gen.graphics_in('"Graphic.php?IM=IM_abc123"')[1] == {"IM_abc123"}


@needs_raw
def test_arm_texts() -> None:
    e = gen.experiment()
    words = {"gps": ("arrival time", "drive"), "food": ("delivery time", "food")}
    for a in e.arms:
        other = "33-53 minutes" if a.estimate == "43 minutes" else "43 minutes"
        assert a.text.count(f"{a.estimate}") == 3 and other not in a.text
        assert all(w in a.text for w in words[a.app])
        no = "food delivery app" if a.app == "gps" else "navigation app"
        assert no not in a.text
        assert a.text.count("Imagine that you decide") == 1  # the grey repeat written once
        assert a.text.startswith("Instructions:\n\nIn this study, you will imagine")
        assert "${" not in a.text and "<" not in a.text
    assert [a.factors for a in e.arms] == [
        {"app": "navigation", "estimate": "point"},
        {"app": "navigation", "estimate": "range"},
        {"app": "food_delivery", "estimate": "point"},
        {"app": "food_delivery", "estimate": "range"},
    ]


@needs_raw
def test_a_changed_repeat_fails() -> None:
    pages = gen.screens(gen.Survey(gen.QSF))["food"]
    gen.arm_text(pages, "43 minutes")
    bad = [pages[0], pages[1], pages[2].replace("dinner", "lunch"), pages[3]]
    with pytest.raises(AssertionError):
        gen.arm_text(bad, "43 minutes")


@needs_raw
def test_bins_are_the_columns_in_order() -> None:
    df = gen.kept()
    yes = [(df[f"binary_{k}"] == 1).mean() for k in range(1, 12)]
    assert int(np.argmax(yes)) == gen.BINS.index("41-45 min")
    # and the extremes are almost never "consistent"
    assert yes[0] < 0.1 and yes[-1] < 0.05


@needs_raw
def test_exclusions_step_by_step() -> None:
    df = gen.read_deposit()
    assert len(df) == 198
    df = df[df["ExcludeDuplicateIP"] != 1]
    assert len(df) == 188
    df = df[df["ExcludeDuplicateID"] != 1]
    assert len(df) == 188 == len(gen.kept()) == gen.N
    assert gen.kept()["Consent"].isna().sum() == 1  # kept, as the authors keep them


# ---------------------------------------------------------------------------
# The answer key: Study S3.do's model and cell means
# ---------------------------------------------------------------------------


def _fit(total: np.ndarray, food: np.ndarray, rng: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """OLS of the count on an app dummy and the range contrast; (b, se)."""
    x = np.column_stack([np.ones(len(total)), food, rng])
    b, *_ = np.linalg.lstsq(x, total, rcond=None)
    e = total - x @ b
    s2 = e @ e / (len(total) - x.shape[1])
    return b, np.sqrt(np.diag(s2 * np.linalg.inv(x.T @ x)))


def _deposit() -> pd.DataFrame:
    """The do file: recode 2 -> 0, rowtotal, range = +-0.5."""
    df = gen.kept()
    yes = df[[f"binary_{k}" for k in range(1, 12)]].replace(2, 0)
    return pd.DataFrame(
        {
            "who": df["Id"].astype(str).values,
            "total": yes.sum(axis=1).astype(float).values,
            "food": (df["app"] == 2).astype(float).values,
            "range": np.where(df["Condition"] == 2, 0.5, -0.5),
        }
    ).sort_values("who", ignore_index=True)


def _built(swap: bool = False) -> pd.DataFrame:
    d = built()
    f = d["factors"].map(lambda x: x if isinstance(x, dict) else json.loads(x))
    est = f.map(lambda x: x["estimate"])
    if swap:
        est = est.map({"point": "range", "range": "point"})
    d = d.assign(
        yes=(d["response_num"] == 1).astype(float),
        food=f.map(lambda x: float(x["app"] == "food_delivery")),
        range=np.where(est == "range", 0.5, -0.5),
        who=d["participant_id"].str.replace(r"^.*s3_", "", regex=True),
    )
    g = d.groupby("who").agg(total=("yes", "sum"), food=("food", "first"), range=("range", "first"))
    return g.reset_index().sort_values("who", ignore_index=True)


@needs_raw
def test_built_rows_reproduce_the_authors_model() -> None:
    d = built()
    assert len(d) == 2068 and d["participant_id"].nunique() == 188
    assert d.groupby("participant_id").size().eq(11).all()
    dep, ours = _deposit(), _built()
    assert dep["who"].tolist() == ours["who"].tolist()
    assert np.allclose(dep["total"], ours["total"], atol=1e-9, rtol=0)
    bd, sd = _fit(dep["total"].to_numpy(), dep["food"].to_numpy(), dep["range"].to_numpy())
    bo, so = _fit(ours["total"].to_numpy(), ours["food"].to_numpy(), ours["range"].to_numpy())
    assert np.allclose(bd, bo, atol=1e-9, rtol=0) and np.allclose(sd, so, atol=1e-9, rtol=0)
    # Supplement 6: b = 1.88, SE = .22; point M = 3.39 (1.58), range M = 5.11 (1.53)
    assert round(bd[2], 2) == 1.88 and round(sd[2], 2) == 0.22
    cells = ours.groupby("range")["total"].agg(["mean", "std", "count"])
    assert np.round(cells["mean"].to_numpy(), 2).tolist() == [3.39, 5.11]
    assert np.round(cells["std"].to_numpy(), 2).tolist() == [1.58, 1.53]
    assert cells["count"].tolist() == [92, 96]
    sw = _built(swap=True)
    bs, _ = _fit(sw["total"].to_numpy(), sw["food"].to_numpy(), sw["range"].to_numpy())
    assert not np.allclose(bd, bs, atol=1e-6, rtol=0)


@needs_raw
def test_rows_carry_only_the_instruments_words() -> None:
    d = built()
    q = d["outcome"].str.split(" Only return").str[0]
    for est, people in (("43 minutes", 92), ("33-53 minutes", 96)):
        stem = (
            "Do you think each of the outcomes below is consistent or inconsistent with "
            f'the estimate of "{est}?"'
        )
        sub = d[d["condition"].str.contains(f'estimate of "{est}."', regex=False)]
        assert len(sub) == people * 11
        assert (q[sub.index].str.startswith(stem)).all()
    assert set(q.str.rsplit('?" ', n=1).str[1]) == set(gen.BINS)
    assert d["condition"].nunique() == 4
    assert not d["condition"].str.contains("apple|consent|Prolific", case=False).any()


# ---------------------------------------------------------------------------
# The sequence studies (rich, 20 Nov 2026: listed in the data file's order, with a clause)
# ---------------------------------------------------------------------------

SEQ_KEYS = [st.key for st in gen.SEQ_STUDIES]


@needs_raw
def test_sequence_recipes_and_coded_files_are_the_generators() -> None:
    for st in gen.SEQ_STUDIES:
        coded = gen.RAW / gen.seq_data_file(st)
        assert coded.read_text() == gen.seq_prep(st).to_csv(index=False), st.key
        for b in st.blocks:
            assert gen.seq_recipe_path(st, b).read_text() == gen.seq_render(st, b), (st.key, b)


def test_a_reordered_or_foreign_draw_is_not_a_subsequence() -> None:
    values = ["59", "38", "49", "60", "49"]
    assert gen.subsequence([59, 49, 49], values) == ["59", "49", "49"]
    with pytest.raises(AssertionError):  # out of loop order
        gen.subsequence([49, 59], values)
    with pytest.raises(AssertionError):  # a time the loop never held
        gen.subsequence([59, 41], values)
    assert gen.minutes("2 hours and 12 minutes") == 132 and gen.minutes("48 minutes") == 48


def seq_built(st: Any, block: str) -> pd.DataFrame:
    path = PROCESSED / f"researchbox482_{st.name}_{block}.parquet"
    if not path.exists():
        pytest.skip(f"{path.name} not built")
    return pd.read_parquet(path)


def _factors(d: pd.DataFrame) -> pd.Series:
    return d["factors"].map(lambda x: x if isinstance(x, dict) else json.loads(x))


def _design(key: str, length: np.ndarray, cond: np.ndarray) -> np.ndarray:
    """The do file's main model for each study (Study N.do, 2.2 Main Analyses)."""
    one = np.ones(len(cond))
    if key in ("1", "2"):
        return np.column_stack([one, cond == 2, cond == 3]).astype(float)
    if key in ("3", "5"):
        return np.column_stack([one, np.where(cond == 2, 0.5, -0.5)])
    if key == "6":
        return np.column_stack([one, cond == 2, cond == 3, cond == 4]).astype(float)
    if key == "7":
        pt = np.where(np.isin(cond, [1, 2]), 0.5, -0.5)
        acr = np.where(np.isin(cond, [1, 3]), 0.5, -0.5)
        return np.column_stack([one, pt, acr, pt * acr])
    assert key == "8"
    return np.column_stack([one, length == 2, cond == 2, cond == 3]).astype(float)


def _ols(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    b, *_ = np.linalg.lstsq(x, y, rcond=None)
    return np.asarray(b)


DVS = {"satisfaction": ["sb"], "accuracy": gen.OB, "lateness": ["late"]}


def _deposit_seq(st: Any, block: str) -> pd.DataFrame:
    df = gen.seq_kept(st)
    out = pd.DataFrame({"who": [f"{st.name}_{i}" for i in df["Id"]]})
    out["length"] = df["Length"].values if "Length" in df else 0
    out["cond"] = df["Condition"].values
    if block == "satisfaction":
        out["sb"] = df[gen.SB].mean(axis=1).values  # egen sb = rowmean(...)
    for v in DVS[block]:
        if v != "sb":
            out[v] = df[v].astype(float).values
    return out.sort_values("who", ignore_index=True)


def _built_seq(st: Any, block: str, swap: bool = False) -> pd.DataFrame:
    d = seq_built(st, block)
    f = _factors(d)
    back = {tuple(lv[k] for k in st.factors): key for key, (_, lv) in st.cells.items()}
    keys = f.map(lambda x: back[tuple(x[k] for k in st.factors)])
    d = d.assign(length=keys.map(lambda k: k[0]), cond=keys.map(lambda k: k[1]))
    if swap:  # move every row of the first arm to the second
        first, second = sorted(st.cells)[:2]
        d.loc[keys == first, "cond"] = second[1]
    items = gen.SB if block == "satisfaction" else DVS[block]
    var = d["outcome"].str.split(" Only return").str[0]
    qs = {it.question: it.var for it in gen.seq_design(st).dvs[block].items}
    d["var"] = var.map(qs)
    assert d["var"].notna().all() and set(d["var"]) == set(items)
    y = d["response_num"].astype(float)
    y = y.where(~d["var"].isin(["ob_accurate", "ob_inaccurate"]), y * 10)  # back to percent
    d = d.assign(y=y)
    wide = d.pivot_table(index="participant_id", columns="var", values="y", aggfunc="first")
    meta = d.groupby("participant_id")[["length", "cond"]].first()
    out = meta.join(wide).reset_index()
    out["who"] = out["participant_id"].str.replace(r"^.*?(study\d_)", r"\1", regex=True)
    if block == "satisfaction":
        out["sb"] = out[gen.SB].mean(axis=1)
    return out.sort_values("who", ignore_index=True)


@needs_raw
@pytest.mark.parametrize("key", SEQ_KEYS)
def test_built_rows_reproduce_the_authors_models(key: str) -> None:
    st = gen.SEQ[key]
    for block in st.blocks:
        dep, ours = _deposit_seq(st, block), _built_seq(st, block)
        assert len(dep) == st.n and dep["who"].tolist() == ours["who"].tolist()
        assert (dep["cond"].to_numpy() == ours["cond"].to_numpy()).all()
        assert (dep["length"].to_numpy() == ours["length"].to_numpy()).all()
        x = _design(key, dep["length"].to_numpy(), dep["cond"].to_numpy())
        for v in DVS[block]:
            bd = _ols(x, dep[v].to_numpy(float))
            bo = _ols(x, ours[v].to_numpy(float))
            assert np.allclose(bd, bo, atol=1e-9, rtol=0), (key, block, v)
        sw = _built_seq(st, block, swap=True)
        xs = _design(key, sw["length"].to_numpy(), sw["cond"].to_numpy())
        v = DVS[block][0]
        assert not np.allclose(_ols(x, dep[v].to_numpy(float)), _ols(xs, sw[v].to_numpy(float)))


@needs_raw
@pytest.mark.parametrize("key", SEQ_KEYS)
def test_each_row_lists_the_twenty_pages_it_carries(key: str) -> None:
    st = gen.SEQ[key]
    df = gen.seq_kept(st)
    if key == "3":
        drawn = df[[f"draw{k}" for k in range(36, 56)]].astype(int).values.tolist()
    else:
        drawn = [[int(t) for t in str(o).split(",")] for o in df["outcomes"]]
    want = dict(zip([f"{st.name}_{i}" for i in df["Id"]], drawn, strict=True))
    for block in st.blocks:
        d = seq_built(st, block)
        f = _factors(d)
        for pid, fx, cond in zip(d["participant_id"], f, d["condition"], strict=True):
            who = pid[pid.index(st.name) :]
            times = [int(fx[f"time_{j:02d}"]) for j in range(1, 21)]
            assert times == want[who], (key, who)
            body = cond.split(gen.UNORDERED + "\n", 1)[1].split("\n\n", 1)[0]
            lines = body.split("\n")
            assert len(lines) == 20 and all(ln.startswith("- The app presented") for ln in lines)
            pat = r"took the driver (.+)\.$" if key == "8" else r"took (\d+) minutes\.$"
            took = [gen.minutes(m.group(1)) for m in (re.search(pat, ln) for ln in lines) if m]
            assert took == times, (key, who)
            assert "Order " not in cond and "Please click >> to view the next" not in cond
            assert cond.count(gen.UNORDERED) == 1


@needs_raw
@pytest.mark.parametrize("key", SEQ_KEYS)
def test_the_second_block_narrates_the_first(key: str) -> None:
    st = gen.SEQ[key]
    for block in st.blocks:
        d = seq_built(st, block)
        f = _factors(d)
        asked = d["condition"].str.contains("\nYou were asked", regex=False)
        if st.counterbalanced:
            first = f.map(lambda x: x["dv_order"]) == f"{block}_first"
        else:
            first = pd.Series(block == "satisfaction", index=d.index)
        assert (asked == ~first).all(), (key, block)
        assert d["condition"].str.contains("You will now be asked to evaluate").all()
