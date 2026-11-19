"""The researchbox108 recipes (Barnes and Shavitt 2024, top rated or best seller) and their key.

The generator reads every condition and outcome from the .qsf through its survey flow and
codes the deposit. These tests stop a hand edit drifting from it, and check the facts the
rows rest on:

- each recipe and coded file is what the generator writes; the codebooks give the codes
  the coding assumes;
- the box's 57 pictures are where the generator says, and the built studies' in-flow
  pictures are exactly the ones judged decorative; a picture added to a built study's
  flow fails;
- the in-flow lookup matters: the Study 4 .qsf holds out-of-flow copies of both questions
  with the ends reversed, and reading by export tag alone would pick up the wrong ones;
- N and N by arm are the deposit's;
- recomputed from the BUILT rows, the answer key (Table A1 of "Items means and sds for
  Studies 1-6.pdf") reproduces to its printed precision: Study 1 WTP 320.67 (162.45) USD and
  20106.39 (12252.44) INR, Study 4 relative cue diagnosticity 2.88 (1.75); and every Study 1
  cell mean equals the deposit's, which a swapped arm breaks.

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
GEN = REPO / "scripts" / "gen_researchbox108.py"
PROCESSED = REPO / "data" / "processed"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_researchbox108", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_researchbox108"] = mod  # dataclasses look their module up here
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.RAW.exists(), reason="researchbox108 deposit not fetched")
NAMES = ["study1_us", "study1_india", "study4"]


def built(name: str) -> pd.DataFrame:
    path = PROCESSED / f"researchbox108_{name}.parquet"
    if not path.exists():
        pytest.skip(f"researchbox108_{name} not built")
    return pd.read_parquet(path)


@needs_raw
@pytest.mark.parametrize("exp", gen.experiments(), ids=lambda e: e.name)
def test_recipe_is_what_the_generator_writes(exp: Any) -> None:
    assert gen.recipe_path(exp).read_text() == gen.render(exp)
    load(gen.recipe_path(exp))


def test_every_experiment_has_a_recipe_and_nothing_else() -> None:
    assert sorted(p.stem for p in (REPO / "recipes").glob("researchbox108_*.yaml")) == sorted(
        f"researchbox108_{n}" for n in NAMES
    )
    assert not set(gen.NOT_BUILT) & set(NAMES)


@needs_raw
@pytest.mark.parametrize("tag", NAMES)
def test_coded_file_is_what_the_generator_writes(tag: str) -> None:
    assert (gen.RAW / gen.data_file(tag)).read_text() == gen.prep(tag).to_csv(index=False)


@needs_raw
def test_codebooks_and_pictures() -> None:
    gen.check_codebook()
    gen.check_pictures()


@needs_raw
def test_a_picture_in_a_built_flow_fails() -> None:
    sv = gen.Survey(gen.QSF["study1_us"])
    love = sv.q("love")
    love["QuestionText"] += '<img src="https://x/CP/Graphic.php?IM=IM_planted">'
    assert ("love", "IM_planted") in sv.pictures_in_flow()
    assert sv.pictures_in_flow() != gen.DECORATIVE["study1_us"]


@needs_raw
def test_study4_reads_the_in_flow_questions_not_the_reversed_copies() -> None:
    sv = gen.Survey(gen.QSF["study4"])
    for tag, top in (("impt", 'Definitely "Top Rated"'), ("relv", "Definitely that they are")):
        copies = [p for p in sv.all if p["DataExportTag"] == tag]
        assert len(copies) == 2  # one in the flow, one outside it, ends reversed
        firsts = {gen.norm(p["Choices"]["1"]["Display"]) for p in copies}
        assert any("Best Seller" in f for f in firsts) and any("Top Rated" in f for f in firsts)
        assert gen.six_point(sv, tag)["min_label"].startswith(top)
        assert "Top Rated" in gen.six_point(sv, tag)["min_label"]


@needs_raw
def test_the_scale_check_catches_a_reversed_scale() -> None:
    sv = gen.Survey(gen.QSF["study4"])
    q = sv.q("impt")
    q["ChoiceOrder"] = list(reversed(q["ChoiceOrder"]))
    with pytest.raises(AssertionError):
        gen.six_point(sv, "impt")


@needs_raw
def test_india_survey_is_in_english() -> None:
    sv = gen.Survey(gen.QSF["study1_india"])
    assert sv.entry["SurveyLanguage"] == "EN"
    assert not any(p.get("Language") for p in sv.all)


@needs_raw
def test_n_and_arms_are_the_deposits() -> None:
    assert gen.prep("study1_us")["arm"].value_counts().to_dict() == {1: 52, 2: 49}
    assert gen.prep("study1_india")["arm"].value_counts().to_dict() == {1: 50, 2: 49}
    assert len(gen.read_deposit("study4")) == 153 and len(gen.prep("study4")) == 148


def _mean_sd(s: pd.Series) -> tuple[float, float]:
    return round(float(s.mean()), 2), round(float(s.std()), 2)


@needs_raw
def test_built_rows_reproduce_table_a1_study1() -> None:
    assert _mean_sd(built("study1_us")["response_num"]) == (320.67, 162.45)
    assert _mean_sd(built("study1_india")["response_num"]) == (20106.39, 12252.44)


@needs_raw
def test_built_rows_reproduce_table_a1_study4() -> None:
    df = built("study4")
    wide = df.pivot(index="participant_id", columns="task_num", values="response_num")
    assert len(wide) == 148
    assert _mean_sd((wide[0] + wide[1]) / 2) == (2.88, 1.75)


def _cell_means(name: str, swap: bool = False) -> dict[str, float]:
    df = built(name)
    cue = df["factors"].map(lambda f: (f if isinstance(f, dict) else json.loads(f))["cue"])
    if swap:
        cue = cue.map({"attitudinal": "behavioural", "behavioural": "attitudinal"})
    return {k: round(v, 6) for k, v in df.groupby(cue.values)["response_num"].mean().items()}


def _deposit_cells(india: int) -> dict[str, float]:
    d = gen.read_deposit("study1_us")
    d = d[d["INDIA"] == india]
    m = d.groupby("AttCue")["WTP_raw"].mean()
    return {"attitudinal": round(m[1], 6), "behavioural": round(m[0], 6)}


@needs_raw
@pytest.mark.parametrize(("name", "india"), [("study1_us", 0), ("study1_india", 1)])
def test_built_cell_means_are_the_deposits(name: str, india: int) -> None:
    assert _cell_means(name) == _deposit_cells(india)
    assert _cell_means(name, swap=True) != _deposit_cells(india)


@needs_raw
def test_rows_carry_only_the_words_the_notes_declare_as_ours() -> None:
    us = built("study1_us")
    assert set(us["outcome"].str.split(" Only return").str[0]) == {
        'How much would be willing to pay for a Laplet? Answer on the slider labelled "USD".'
    }
    s4 = built("study4")
    second = s4[s4["task_num"] == 1]["condition"].unique()
    assert len(second) == 1 and second[0].endswith(
        'You were asked "Which of these criteria do you think is more important to consider?"'
    )
