"""The researchbox755 recipes (Hu, Moon & VanEpps 2026, choice set size neglect) and key.

The generator reads every scenario and question from the blocks each .qsf's flow reaches,
fills each person's pipes from their recorded fields, applies the authors' exclusions and
codes each person's drawn cell as an arm. These tests stop a hand edit drifting from it, and
check the facts the rows rest on:

- each recipe and coded file is what the generator writes; the codebooks list the data
  files' columns;
- the <img> tags sit where the docstring says (Studies 1, 2 and 5 show dish photographs and
  are not built; Study 4's one graphic is a spinner), and the picture check fails if one moves;
- N is the .do files' final sample;
- recomputed from the BUILT rows, the authors' .do-file analyses come out exactly as they do
  from the deposit: Study 3's dv by evaluation x choice set and its OLS with reason fixed
  effects; Study 4's liking by scenario x condition and each scenario's regression;
- mislabelling which set Avery chose from breaks the Study 3 reproduction.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_researchbox755.py"
PROCESSED = REPO / "data" / "processed"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_researchbox755", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_researchbox755"] = mod  # dataclasses look their module up here
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.RAW.exists(), reason="researchbox755 deposit not fetched")
NAMES = ["study3", "study4_food", "study4_election"]


def built(name: str) -> pd.DataFrame:
    path = PROCESSED / f"researchbox755_{name}.parquet"
    if not path.exists():
        pytest.skip(f"researchbox755_{name} not built")
    df = pd.read_parquet(path)
    return pd.concat([df.reset_index(drop=True), pd.json_normalize(df["factors"])], axis=1)


def cells(
    df: pd.DataFrame, by: list[str], col: str
) -> dict[tuple[Any, ...], tuple[int, float, float]]:
    out = {}
    for k, g in df.groupby(by):
        out[k if isinstance(k, tuple) else (k,)] = (
            len(g),
            round(float(g[col].mean()), 10),
            round(float(g[col].std()), 10),
        )
    return out


def ols(y: pd.Series, x: pd.DataFrame) -> np.ndarray:
    a = np.column_stack([np.ones(len(x)), x.to_numpy(dtype=float)])
    beta, *_ = np.linalg.lstsq(a, y.to_numpy(dtype=float), rcond=None)
    return np.asarray(beta)


def deposit(name: str) -> pd.DataFrame:
    return pd.read_excel(gen.DATA / name)


# --------------------------------------------------------------------------------------
# The generator
# --------------------------------------------------------------------------------------


@needs_raw
@pytest.mark.slow
@pytest.mark.parametrize("name", NAMES)
def test_recipe_is_what_the_generator_writes(name: str) -> None:
    e = gen.experiment(name)
    assert gen.recipe_path(e).read_text() == gen.render(e)
    load(gen.recipe_path(e))


def test_every_built_study_has_a_recipe_and_the_rest_are_not_built() -> None:
    assert sorted(p.stem for p in (REPO / "recipes").glob("researchbox755_*.yaml")) == sorted(
        f"researchbox755_{n}" for n in NAMES
    )
    assert set(gen.NOT_BUILT) == {"study1", "study2", "study5", "study6_self", "study6_other"}
    assert not set(gen.NOT_BUILT) & set(gen.SOURCES)


@needs_raw
@pytest.mark.slow
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
    saved = gen.PICTURES["Study 3.qsf"]
    try:
        gen.PICTURES["Study 3.qsf"] = (1, 0)  # "Study 3 shows a picture": false
        with pytest.raises(AssertionError):
            gen.check_pictures()
    finally:
        gen.PICTURES["Study 3.qsf"] = saved
    gen.check_pictures()


def test_text_rendering_keeps_words_and_lays_out_tables() -> None:
    raw = (
        "Hello&nbsp;<b>there</b>.<br><br><table><tr><td>&nbsp;</td><td>Issue 1</td></tr>"
        '<tr><td>Ranked #1</td><td>A</td></tr></table><img src="x"><ul><li>one</li></ul>'
    )
    assert gen.to_text(raw) == "Hello there.\n\nIssue 1\nRanked #1 | A\n\n- one"
    assert gen.demojibake("Saut√©ed") == "Sautéed"
    with pytest.raises(AssertionError):
        gen.fill("a ${e://Field/x}", {"x": "${e://Field/y}"})


@needs_raw
def test_n() -> None:
    for tag, n in gen.N.items():
        assert len(gen.kept(tag)) == n


# --------------------------------------------------------------------------------------
# Answer key: the authors' .do files, on the deposit and on the built rows
# --------------------------------------------------------------------------------------


def study3_deposit() -> pd.DataFrame:
    """Study 3.do: exclusions, then like_2/like_6 from twofirst, reshape long, dv."""
    d = deposit("Study 3.xlsx")
    d = d[d["attnchk"].notna()]
    d = d[(d["ExcludeDuplicateIP"] != 1) & (d["ExcludeDuplicateID"] != 1) & (d["attnchk"] == 1)]
    rows = []
    for _, r in d.iterrows():
        if r["Condition"] in (1, 2):
            rows.append((r["Id"], 1, 2 if r["Condition"] == 1 else 6, r["reason"], r["like_SE"]))
        else:
            two, six = (
                (r["like_a"], r["like_b"]) if r["twofirst"] == 1 else (r["like_b"], r["like_a"])
            )
            rows.append((r["Id"], 2, 2, r["reason"], two))
            rows.append((r["Id"], 2, 6, r["reason"], six))
    return pd.DataFrame(rows, columns=["id", "evaluation", "choice_set", "reason", "dv"])


def study3_built(swap: bool = False) -> pd.DataFrame:
    b = built("study3")
    ev = b["design"].str.startswith("joint").map({False: 1, True: 2})
    avery_two = b["design"].isin(["separate_2", "joint_2_first"])
    if swap:  # the mutation: read joint_2_first as Avery choosing from six
        avery_two = b["design"].isin(["separate_2", "joint_6_first"])
    is_avery = b["task_num"].isin([0, 1])
    two = np.where(is_avery, avery_two, ~avery_two)
    reason = b["reason"].map({v: k for k, v in gen.REASON.items()})
    return pd.DataFrame(
        {
            "id": b["participant_id"],
            "evaluation": ev,
            "choice_set": np.where(two, 2, 6),
            "reason": reason,
            "dv": b["response_num"],
        }
    )


def study3_ols(df: pd.DataFrame) -> np.ndarray:
    twoop = (df["choice_set"] == 2) - 0.5
    je = (df["evaluation"] == 2) - 0.5
    x = pd.DataFrame({"twoop": twoop, "je": je, "int": twoop * je})
    for r in (2, 3):
        x[f"r{r}"] = (df["reason"] == r).astype(float)
    return ols(df["dv"], x)


@needs_raw
def test_study3_reproduces_the_do_file() -> None:
    dep, b = study3_deposit(), study3_built()
    assert len(dep) == len(b) == 785
    assert cells(b, ["evaluation", "choice_set"], "dv") == cells(
        dep, ["evaluation", "choice_set"], "dv"
    )
    assert {k: v[0] for k, v in cells(b, ["evaluation", "choice_set"], "dv").items()} == {
        (1, 2): 193,
        (1, 6): 196,
        (2, 2): 198,
        (2, 6): 198,
    }
    np.testing.assert_allclose(study3_ols(b), study3_ols(dep), atol=1e-10)


@needs_raw
def test_study3_reproduction_catches_a_swapped_order() -> None:
    dep, b = study3_deposit(), study3_built(swap=True)
    assert cells(b, ["evaluation", "choice_set"], "dv") != cells(
        dep, ["evaluation", "choice_set"], "dv"
    )


def study4_deposit() -> pd.DataFrame:
    d = deposit("Study 4.xlsx")
    d = d[d["age"].notna()]
    d = d[(d["ExcludeDuplicateIP"] != 1) & (d["ExcludeDuplicateID"] != 1) & (d["attnchk"] == 1)]
    d = d.assign(Condition=(d["Choice"] == 6) * 2 + d["Frame"])
    long = []
    for s in (1, 2):
        like = d[[f"like{s}_{k}" for k in range(1, 5)]].sum(axis=1, min_count=1)
        long.append(pd.DataFrame({"scenario": s, "condition": d["Condition"], "like": like}))
    return pd.concat(long, ignore_index=True)


def study4_built() -> pd.DataFrame:
    parts = []
    for s, name in ((1, "study4_food"), (2, "study4_election")):
        b = built(name)
        parts.append(
            pd.DataFrame(
                {
                    "scenario": s,
                    "condition": b["design"].map(gen.CONDITION4),
                    "like": b["response_num"],
                }
            )
        )
    return pd.concat(parts, ignore_index=True)


def study4_ols(df: pd.DataFrame) -> np.ndarray:
    twoop = df["condition"].isin([1, 2]) - 0.5
    choose = df["condition"].isin([1, 3]) - 0.5
    return ols(df["like"], pd.DataFrame({"twoop": twoop, "choose": choose, "int": twoop * choose}))


@needs_raw
def test_study4_reproduces_the_do_file() -> None:
    dep, b = study4_deposit(), study4_built()
    assert len(dep) == len(b) == 2 * 1578
    assert cells(b, ["scenario", "condition"], "like") == cells(
        dep, ["scenario", "condition"], "like"
    )
    for s in (1, 2):
        np.testing.assert_allclose(
            study4_ols(b[b["scenario"] == s]), study4_ols(dep[dep["scenario"] == s]), atol=1e-10
        )
