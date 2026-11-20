"""The researchbox809 recipes (periodic corporate donations, 11 studies) and their key.

The generator simulates each .qsf's survey flow for every assignment, renders the screens a
respondent read, and codes the deposit with the authors' exclusions. These tests stop a hand
edit drifting from it, and check the facts the rows rest on:

- the recipes and the coded files are what the generator writes; only the eleven recipes
  exist, and the field studies are NOT_BUILT;
- every kept row's recorded fills (price, cause, company, ...) are what its .qsf sets for its
  assignment, and a tampered fill fails;
- the two "5b" questionnaires are two studies: neither data file could have come from the
  other's .qsf;
- the only picture in any built .qsf is 5b's pre-consent screener, which no row carries; a
  planted picture is seen;
- no data file records a display order;
- the authors' exclusions give their N, and the PROCESS outputs' N where there is one;
- recomputed from the BUILT rows, each study's pre-registered model (from its .rmd) gives the
  same coefficients as the deposit, to 1e-9; swapping the schedule levels breaks it;
- the rows carry no screen the docstring drops.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_researchbox809.py"
PROCESSED = REPO / "data" / "processed"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_researchbox809", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_researchbox809"] = mod  # dataclasses look their module up here
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.RAW.exists(), reason="researchbox809 deposit not fetched")
NAMES = [s.name for s in gen.SPECS]


def built(name: str) -> pd.DataFrame:
    path = PROCESSED / f"researchbox809_{name}.parquet"
    if not path.exists():
        pytest.skip(f"researchbox809_{name} not built")
    return pd.read_parquet(path)


def test_only_these_recipes() -> None:
    assert sorted(p.stem for p in (REPO / "recipes").glob("researchbox809_*.yaml")) == sorted(
        f"researchbox809_{n}" for n in NAMES
    )
    assert set(gen.NOT_BUILT) == {"study1a", "study1b", "study5b_2024"}
    assert "study5b_2024" in gen.BY_NAME and "study5b_2024" not in NAMES


@needs_raw
@pytest.mark.parametrize("name", NAMES)
def test_recipe_and_coded_file_are_what_the_generator_writes(name: str) -> None:
    spec = gen.BY_NAME[name]
    assert gen.recipe_path(spec).read_text() == gen.render(spec)
    r = load(gen.recipe_path(spec))
    assert len(r.condition.arms) == len(gen.arms(spec))
    assert (gen.RAW / gen.data_file(spec)).read_text() == gen.prep(spec).to_csv(index=False)


@needs_raw
def test_a_tampered_fill_fails() -> None:
    spec = gen.BY_NAME["study3"]
    df = gen.kept(spec).copy()
    gen.check_data_matches_qsf(spec, df)
    df.iloc[0, df.columns.get_loc("price")] = "donate $50 every month in 2024"
    with pytest.raises(AssertionError):
        gen.check_data_matches_qsf(spec, df)


@needs_raw
def test_the_two_5b_questionnaires_are_two_studies() -> None:
    new, old = gen.BY_NAME["study5b"], gen.BY_NAME["study5b_2024"]
    assert new.qsf != old.qsf and new.data != old.data
    for this, other in ((new, old), (old, new)):
        prices = {gen._norm(p) for p in gen.read_deposit(this)["price"].dropna()}
        theirs = {gen._norm(a.ed["price"]) for a in gen.arms(other)}
        assert prices == {gen._norm(a.ed["price"]) for a in gen.arms(this)}
        assert not prices & theirs
    assert {"engage", "filter", "amount"} <= set(gen.read_deposit(new).columns)
    assert not {"engage", "filter"} & set(gen.read_deposit(old).columns)
    assert {"impact_1", "commit_1", "money", "brand"} <= set(gen.read_deposit(old).columns)


@needs_raw
@pytest.mark.parametrize("name", NAMES)
def test_pictures_and_order(name: str) -> None:
    gen.check_pictures(gen.BY_NAME[name])
    gen.check_order_unrecorded(gen.BY_NAME[name])


def test_a_planted_picture_is_seen() -> None:
    payload: dict[str, str] = {"QuestionID": "QID9"}
    doc = {"SurveyElements": [{"Element": "SQ", "Payload": payload}]}
    assert gen.graphics_in(json.dumps(doc)) == (set(), set())
    payload["QuestionText"] = '<img src="x?IM=IM_abc">'
    assert gen.graphics_in(json.dumps(doc)) == ({"QID9"}, {"IM_abc"})


@needs_raw
def test_authors_ns_and_the_process_outputs() -> None:
    for s in gen.SPECS:
        assert len(gen.kept(s)) == s.n_kept
    # the analysed N in the authors' PROCESS outputs (Other/*.pdf)
    pdf = {"study3": 556, "w4": 429, "w5": 1643, "study5b_2024": 759}  # last: not built
    for name, n in pdf.items():
        assert gen.BY_NAME[name].n_kept == n
    for s in gen.SPECS:
        d = built(s.name)
        assert d["participant_id"].nunique() == s.n_kept


# ---------------------------------------------------------------------------
# The answer key: each study's pre-registered model, deposit vs built rows
# ---------------------------------------------------------------------------


def built_frame(name: str, swap: bool = False) -> pd.DataFrame:
    spec = gen.BY_NAME[name]
    d = built(name)
    f = d["factors"].map(lambda x: x if isinstance(x, dict) else json.loads(x))
    rows = pd.DataFrame(list(f.values), index=d.index)
    rows["pid"] = d["participant_id"].values
    rows["var"] = [spec.outcomes[t] for t in d["task_num"]]
    rows["y"] = d["response_num"].astype(float).values
    facs = list(spec.assign.values())
    wide = rows.pivot_table(index=["pid", *facs], columns="var", values="y").reset_index()
    if swap:  # the schedule's first two levels exchanged
        a, b = sorted(wide["schedule"].unique())[:2]
        wide["schedule"] = wide["schedule"].map(lambda v: {a: b, b: a}.get(v, v))
    return wide


KEY = {  # the schedule effect each .rmd's model gives on this deposit, for the record
    "study2": {"scheduleperiodic": 0.1705},
    "study3": {"scheduleperiodic": 0.4002},
    "study4": {"scheduleC": 0.2823, "scheduleC:followerC": -0.3691},
    "study5a": {"scheduleC": 0.0311, "scheduleC:moneyC": 0.4731},
    "study5b": {"scheduleperiodic": -0.1431, "scheduleperiodic:amounthigh": 0.2345},
    "w1": {"scheduleperiodic": 0.3127},
    "w2": {"scheduleperiodic": 0.382, "scheduleperiodic-sum": 0.3392},
    "w3": {"scheduleperiodic": 0.2721},
    "w4": {"scheduleperiodic": 0.4144},
    "w5": {"scheduleC": 0.2988, "scheduleC:reputationC": -0.242},
}


@needs_raw
@pytest.mark.parametrize("name", NAMES)
def test_built_rows_reproduce_the_authors_model(name: str) -> None:
    spec = gen.BY_NAME[name]
    dep, ours = gen.deposit_frame(spec), built_frame(name)
    for formula in spec.key:
        a = gen.key_terms(spec, formula, dep)
        b = gen.key_terms(spec, formula, ours)
        assert a.keys() == b.keys()
        assert all(abs(a[k] - b[k]) < 1e-9 for k in a), (formula, a, b)
        assert a["n"] == spec.n_kept
        if formula == spec.key[0]:
            for k, v in KEY[name].items():
                assert round(a[k], 4) == v, (k, a[k])
        broken = gen.key_terms(spec, formula, built_frame(name, swap=True))
        assert any(abs(a[k] - broken[k]) > 1e-6 for k in a if k != "n")


@needs_raw
@pytest.mark.parametrize("name", NAMES)
def test_rows_carry_only_the_screens_the_docstring_keeps(name: str) -> None:
    d = built(name)
    cond = d["condition"]
    for dropped in ("Welcome to the survey", "On the following pages", "Below are the instruc"):
        assert not cond.str.contains(dropped, regex=False).any()
    assert not cond.str.contains("${", regex=False).any()
    assert not d["outcome"].str.contains("${", regex=False).any()
    assert cond.str.contains("Reminder:", regex=False).all()
    assert d["condition"].nunique() == len(gen.arms(gen.BY_NAME[name]))
