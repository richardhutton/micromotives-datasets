"""The researchbox348 recipe (Chin, Zimmerman, Johnson and Shu 2022, overdraft) and its key.

The generator reads Study 1's ten scenarios from the .qsf through its survey flow, parses
every attribute back out of each scenario's words, and codes the deposit with the authors'
exclusions. These tests stop a hand edit drifting from it, and check the facts the rows
rest on:

- the recipe and the coded file are what the generator writes; the codebook lists the data
  file's columns, and its wrong "number of fees (1=4, 0=1)" is still what it says;
- Study 1's .qsf has no picture at all, and the form pictures of Studies 2 and 3 are where
  the generator says; a planted picture is seen;
- the ten profiles' words agree with their export tags, and the template filled from each
  profile's codes reproduces its lists exactly; a swapped clause or a mislabelled fee fails;
- the order really is unrecorded (no _DO column) and randomised as the generator says;
- the authors' exclusions, step by step, give their wave-1 N (869 of 1,016);
- recomputed from the BUILT rows, the authors' Table 3 model (OLS with person fixed effects)
  gives the same six coefficients as the deposit run through their own reshape, to 1e-9,
  and every profile's mean rating is the deposit's column mean; a swapped level breaks both;
- the rows carry only the words the notes declare as ours.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_researchbox348.py"
PROCESSED = REPO / "data" / "processed"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_researchbox348", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_researchbox348"] = mod  # dataclasses look their module up here
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.RAW.exists(), reason="researchbox348 deposit not fetched")
ATTRS = ["fee_amount", "number_of_fees", "slack", "purchase_purpose", "alt_payment", "bank_type"]


def built() -> pd.DataFrame:
    path = PROCESSED / "researchbox348_study1.parquet"
    if not path.exists():
        pytest.skip("researchbox348_study1 not built")
    return pd.read_parquet(path)


@needs_raw
def test_recipe_is_what_the_generator_writes() -> None:
    e = gen.experiment()
    assert gen.recipe_path(e).read_text() == gen.render(e)
    r = load(gen.recipe_path(e))
    assert len(r.condition.arms) == 10


def test_only_study1_has_a_recipe() -> None:
    assert sorted(p.stem for p in (REPO / "recipes").glob("researchbox348_*.yaml")) == [
        "researchbox348_study1"
    ]
    assert set(gen.NOT_BUILT) == {"study2", "study3", "study1_pilot", "study3_pilot"}


@needs_raw
def test_coded_file_is_what_the_generator_writes() -> None:
    assert (gen.RAW / gen.data_file()).read_text() == gen.prep().to_csv(index=False)


@needs_raw
def test_codebook_pictures_and_order() -> None:
    gen.check_codebook()
    gen.check_pictures()
    gen.check_order(gen.Survey(gen.QSF))


def test_a_planted_picture_is_seen() -> None:
    assert gen.graphics_in('{"QuestionText":"<p>x</p>"}') == (0, set())
    assert gen.graphics_in('{"QuestionText":"<img src=x>"}')[0] == 1
    assert gen.graphics_in('{"GraphicID":"IM_abc123","Regions":[]}')[1] == {"IM_abc123"}


@needs_raw
def test_profiles_match_their_tags_and_the_template() -> None:
    _, scen = gen.scenarios()
    assert [s.tag for s in scen] == [
        "a1_n0_s0_p0_l1_b1",
        "a0_n1_s1_p0_l0_b0",
        "a0_n0_s1_p1_l0_b1",
        "a0_n0_s0_p0_l1_b0",
        "a0_n1_s0_p1_l1_b0",
        "a0_n1_s0_p0_l0_b1",
        "a1_n0_s1_p0_l0_b0",
        "a1_n1_s1_p1_l1_b1",
        "a1_n0_s0_p1_l0_b0",
        "a0_n1_s1_p0_l0_b1",
    ]
    # the tenth is the profile the authors added from the pilot
    assert scen[-1].tag == "a0_n1_s1_p0_l0_b1"
    caps = {s.tag: s.cell["daily_cap"] for s in scen}
    assert caps["a1_n1_s1_p1_l1_b1"] == 210 and caps["a0_n0_s1_p1_l0_b1"] == 75


@needs_raw
def test_a_swapped_clause_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    slack = gen.CLAUSES["slack"]
    monkeypatch.setitem(gen.CLAUSES, "slack", (slack[1], slack[0]))
    with pytest.raises(AssertionError):
        gen.scenarios()


def test_parse_reads_the_fee_and_rejects_a_wrong_cap() -> None:
    bg = [
        "This person enters a bank.",
        gen.CLAUSES["slack"][0],
        gen.CLAUSES["purchase_purpose"][1],
        gen.CLAUSES["alt_payment"][0],
    ]
    prog = [
        "The bank's overdraft fee is $35 per transaction.",
        "The maximum number of overdraft fees is 6 each day, or $210.",
    ]
    assert gen.parse_bits(bg, prog) == (1, 1, 0, 1, 0, 1)
    with pytest.raises(AssertionError):  # cap is not fee x number
        gen.parse_bits(
            bg, [prog[0], "The maximum number of overdraft fees is 6 each day, or $150."]
        )
    with pytest.raises(KeyError):  # a place sentence no profile has
        gen.parse_bits(["This person enters a credit unions.", *bg[1:]], prog)
    with pytest.raises(AssertionError):  # a bank's person, the credit union's fee
        gen.parse_bits(bg, ["The credit union's overdraft fee is $35 per transaction.", prog[1]])


@needs_raw
def test_exclusions_step_by_step() -> None:
    df = gen.read_deposit()
    assert len(df) == 1016
    df = df[df["old_enough"].notna()]
    assert len(df) == 984
    df = df[(df["old_enough"] == "Yes") & (df["agree_participate"] == "Yes")]
    assert len(df) == 978
    ok = gen.CORRECT_DEFINITION
    df = df[(df["ob_od_cover"] == ok) | (df["ob_od_cover_2"] == ok)]
    assert len(df) == 903
    df = df[df["edu_lvl"].notna()]
    assert len(df) == 879
    assert len(df[df["timing_s1"] > 180]) == 869 == len(gen.kept()) == gen.N
    assert gen.kept()["workerId"].is_unique


@needs_raw
def test_merged_gender_is_left_blank() -> None:
    out = gen.prep()
    assert out["gender"].isna().sum() == 3
    assert (gen.kept()["gender"] == gen.MERGED_GENDER).sum() == 3


# ---------------------------------------------------------------------------
# The answer key: the authors' Table 3 model and the profile means
# ---------------------------------------------------------------------------

X = ["amount_fee", "num_fees_high", "no_fin_slack", "purpose_card", "alternative_payments"]
X += ["credit_union"]


def _fe(d: pd.DataFrame, who: str) -> np.ndarray:
    """OLS of rating on X with person fixed effects (within transformation; balanced)."""
    cols = [*X, "rating"]
    dm = d[cols] - d.groupby(who)[cols].transform("mean")
    b, *_ = np.linalg.lstsq(dm[X].to_numpy(float), dm["rating"].to_numpy(float), rcond=None)
    return np.asarray(b)


def _deposit_long() -> pd.DataFrame:
    """The authors' reshape (manuscript_cleaning.Rmd): the tag's digits are the codes."""
    df = gen.kept()
    cols = [c for c in df.columns if gen.TAG.match(c[:-2])]
    long = df[["workerId", *cols]].melt(
        id_vars="workerId", var_name="scenario", value_name="rating"
    )
    bits = long["scenario"].str.extract(r"^a([01])_n([01])_s([01])_p([01])_l([01])_b([01])_1$")
    bits = bits.astype(int)
    bits.columns = [
        "amount_fee",
        "number_fees",
        "fin_slack",
        "purpose_card",
        "alternative_payments",
        "bank_type",
    ]
    long = pd.concat([long, bits], axis=1)
    long["num_fees_high"] = (long["number_fees"] == 0).astype(int)  # as the authors code it
    long["no_fin_slack"] = (long["fin_slack"] == 0).astype(int)
    long["credit_union"] = (long["bank_type"] == 0).astype(int)
    return long


def _built_long(swap: str | None = None) -> pd.DataFrame:
    d = built()
    f = d["factors"].map(lambda x: x if isinstance(x, dict) else json.loads(x))
    if swap:
        lv = gen.LEVELS[swap]
        f = f.map(lambda x: x | {swap: {lv[0]: lv[1], lv[1]: lv[0]}[x[swap]]})

    def is_(attr: str, level: str) -> pd.Series:
        return f.map(lambda x: int(x[attr] == level))

    return pd.DataFrame(
        {
            "who": d["participant_id"].values,
            "rating": d["response_num"].values,
            "amount_fee": is_("fee_amount", "$35").values,
            "num_fees_high": is_("number_of_fees", "3_per_day").values,
            "no_fin_slack": is_("slack", "month_to_month").values,
            "purpose_card": is_("purchase_purpose", "critical").values,
            "alternative_payments": is_("alt_payment", "yes").values,
            "credit_union": is_("bank_type", "credit_union").values,
        }
    )


@needs_raw
def test_built_rows_reproduce_the_authors_model() -> None:
    d = built()
    assert len(d) == 8690 and d["participant_id"].nunique() == 869
    assert d.groupby("participant_id").size().eq(10).all()
    dep = _fe(_deposit_long(), "workerId")
    ours = _fe(_built_long(), "who")
    assert np.allclose(dep, ours, atol=1e-9, rtol=0)
    # the values the authors' code gives on this deposit, for the record
    assert np.round(dep, 3).tolist() == [-2.265, 1.603, 3.95, 7.375, -11.113, -0.588]
    for attr in ATTRS:  # a swapped level in any attribute moves a coefficient
        assert not np.allclose(dep, _fe(_built_long(swap=attr), "who"), atol=1e-6, rtol=0)


@needs_raw
def test_profile_means_are_the_deposits() -> None:
    d = built()
    df = gen.kept()
    _, scen = gen.scenarios()
    tag_of = {s.code - 1: s.tag for s in scen}
    ours = d.groupby("task_num")["response_num"].mean()
    for t, tag in tag_of.items():
        assert ours[t] == pytest.approx(df[f"{tag}_1"].mean(), abs=1e-9)
    # each task's rows carry its own profile
    for t, tag in tag_of.items():
        fs = d.loc[d["task_num"] == t, "factors"].map(
            lambda x: x if isinstance(x, dict) else json.loads(x)
        )
        (s,) = [s for s in scen if s.tag == tag]
        assert all({k: v for k, v in f.items() if k in ATTRS} == s.factors for f in fs)


@needs_raw
def test_rows_carry_only_the_words_the_notes_declare_as_ours() -> None:
    d = built()
    q = {o.split(" Only return")[0] for o in d["outcome"]}
    assert q == {f"{gen.QUESTION} {gen.SLIDER_SENTENCE}"}
    assert gen.SLIDER_SENTENCE in load(gen.recipe_path(gen.experiment())).notes
    cond = d["condition"]
    assert cond.str.startswith("In this study, we will ask you for your thoughts").all()
    assert not cond.str.contains("In the next part of the study").any()
    assert not cond.str.contains("some may be similar").any()
    assert not cond.str.contains("incorrect response").any()
    assert d["condition"].nunique() == 10
