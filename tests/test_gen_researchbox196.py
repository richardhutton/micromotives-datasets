"""The researchbox196 recipes (Mehr & Simmons 2024, rating specific features) and key.

The generator reads every scenario and rating question from the blocks each .qsf's flow
reaches, keeps the people the authors' R scripts keep, and takes the assignment from the
randomiser's embedded fields. These tests stop a hand edit drifting from it, and check the
facts the rows rest on:

- each recipe and coded file is what the generator writes; the codebooks list the data
  files' columns, and Study 9's codebook attribute labels are its .qsf's rating rows;
- the <img> tags sit where the docstring says (no built study shows one in displayed text),
  and the picture check fails if one moves;
- the answer key: each R script's preregistered comparison, computed straight from the
  deposit with the script's own exclusions and variables, equals the same computed from the
  BUILT rows (N, cell means, pooled-variance t): Studies 10, S3, S4, S5 and S7 (per scenario
  and pooled), and Study 9's first-domain cells (bookcase excluded);
- swapping a factor breaks the reproduction;
- Study 9's bookcase-first people are dropped (by ruling) and counted;
- the not-built studies are listed, with the image-list ones named.

The paper is paywalled and was not read, so the reference is the authors' scripts, not
their printed numbers. Tests needing the gitignored deposit or build skip on a fresh clone.
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
GEN = REPO / "scripts" / "gen_researchbox196.py"
PROCESSED = REPO / "data" / "processed"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_researchbox196", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_researchbox196"] = mod  # dataclasses look their module up here
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.RAW.exists(), reason="researchbox196 deposit not fetched")
NAMES = ["study9", "study10", "s3", "s4", "s5", "s7"]


def built(name: str) -> pd.DataFrame:
    path = PROCESSED / f"researchbox196_{name}.parquet"
    if not path.exists():
        pytest.skip(f"researchbox196_{name} not built")
    df = pd.read_parquet(path)
    return pd.concat([df.reset_index(drop=True), pd.json_normalize(df["factors"])], axis=1)


def deposit(tag: str) -> pd.DataFrame:
    return pd.read_csv(gen.DATA / gen.SOURCES[tag][1])


def ttest(a: pd.Series, b: pd.Series) -> tuple[int, int, float, float, float]:
    """R's t.test(var.equal = TRUE): the two Ns, the two means, and t."""
    t = float(stats.ttest_ind(a, b, equal_var=True).statistic)
    return len(a), len(b), round(float(a.mean()), 10), round(float(b.mean()), 10), round(t, 10)


def r_keep(df: pd.DataFrame, *tests: pd.Series) -> pd.DataFrame:
    """R's `deletes <- ifelse(a | b | ...)` then `which(deletes == 0)`: NA in any test drops."""
    bad = pd.Series(False, index=df.index)
    unknown = pd.Series(False, index=df.index)
    for t in tests:
        bad |= t.fillna(False).astype(bool)
        unknown |= t.isna()
    return df[~bad & ~unknown]


def eq(s: pd.Series, v: Any) -> pd.Series:
    """R's `s == v`, NA where s is NA."""
    return s.eq(v).astype("boolean").mask(s.isna())


def ne(s: pd.Series, v: Any) -> pd.Series:
    return s.ne(v).astype("boolean").mask(s.isna())


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
    assert sorted(p.stem for p in (REPO / "recipes").glob("researchbox196_*.yaml")) == sorted(
        f"researchbox196_{n}" for n in NAMES
    )
    assert set(gen.NOT_BUILT) == {
        "study1",
        "study2",
        "study3",
        "study4",
        "study4_pretest",
        "study5",
        "study6",
        "study7",
        "study8",
        "s1",
        "s2",
        "s6",
        "s7_pretest",
    }
    assert not set(gen.NOT_BUILT) & set(gen.SOURCES)
    assert set(gen.IMAGE_LIST) <= set(gen.NOT_BUILT)
    assert all("image list" in gen.NOT_BUILT[k] for k in gen.IMAGE_LIST)


@needs_raw
@pytest.mark.parametrize("tag", NAMES)
def test_coded_file_is_what_the_generator_writes(tag: str) -> None:
    assert (gen.RAW / gen.data_file(tag)).read_text() == gen.prep(tag).to_csv(index=False)


@needs_raw
@pytest.mark.parametrize("tag", NAMES)
def test_codebook_lists_the_columns(tag: str) -> None:
    gen.check_codebook(tag)


@needs_raw
@pytest.mark.parametrize("tag", NAMES)
def test_data_assignment_values_are_the_qsf_ones(tag: str) -> None:
    gen.check_assignment(tag)


@needs_raw
def test_assignment_check_catches_the_wrong_qsf() -> None:
    saved = gen.SOURCES["s5"]
    try:
        gen.SOURCES["s5"] = (gen.SOURCES["s7"][0], *saved[1:])
        gen.survey.cache_clear()
        with pytest.raises((AssertionError, KeyError)):
            gen.check_assignment("s5")
    finally:
        gen.SOURCES["s5"] = saved
        gen.survey.cache_clear()
    gen.check_assignment("s5")


@needs_raw
def test_study9_codebook_attributes_are_the_qsf_rows() -> None:
    gen.study9_check_codebook()


@needs_raw
def test_study9_codebook_check_catches_a_swapped_cell() -> None:
    saved = gen.FORMATS.copy()
    try:
        gen.FORMATS["positive"], gen.FORMATS["negative"] = saved["negative"], saved["positive"]
        with pytest.raises(AssertionError):
            gen.study9_check_codebook()
    finally:
        gen.FORMATS.clear()
        gen.FORMATS.update(saved)
    gen.study9_check_codebook()


@needs_raw
def test_pictures_are_where_the_docstring_says() -> None:
    gen.check_pictures()


@needs_raw
def test_the_picture_check_catches_a_moved_picture() -> None:
    name = "Study 10.(file id 194).qsf"
    saved = gen.PICTURES[name]
    try:
        gen.PICTURES[name] = (2, 0)  # "the scenario shows the screenshot": false
        with pytest.raises(AssertionError):
            gen.check_pictures()
    finally:
        gen.PICTURES[name] = saved
    gen.check_pictures()


@needs_raw
def test_no_condition_names_a_page_or_a_scenario_number() -> None:
    for name in NAMES:
        for a in gen.experiment(name).arms:
            texts = [a.text] + [i["condition_text"] for i in a.items.values()]
            for t in texts:
                assert "page" not in t and "Scenario" not in t, (name, t[:80])


@needs_raw
def test_s4_has_one_kept_person_without_a_company() -> None:
    # why the piped "Why were you calling <company>?" is not narrated
    name = gen.kept("s4")["nameCompany"].astype("string").str.strip()
    assert int((name.isna() | (name == "")).sum()) == 1


# --------------------------------------------------------------------------------------
# The authors' R scripts, deposit vs built rows
# --------------------------------------------------------------------------------------


def r_study10() -> pd.DataFrame:
    d = deposit("study10")
    d["overall"] = d["overallSingle"].fillna(d["overallMultiple"])
    d["oAndA"] = d["overallSingle"].notna().map({True: 0, False: 1}).where(d["overall"].notna())
    d["prefQs"] = (d["prefQ1"] + d["prefQ2"]) / 2
    return r_keep(
        d,
        d["overall"].isna(),
        eq(d["duplicateIP"], 1),
        eq(d["duplicateID"], 1),
        ne(d["attnCheck"], 1),
        eq(d["approvedID"], 0),
    )


@needs_raw
def test_study10_preregistered_t_tests() -> None:
    d = r_study10()
    b = built("study10")
    wide = b.pivot_table(
        index=["participant_id", "rating_rows"], columns="task_num", values="response_num"
    ).reset_index()
    wide["prefQs"] = (wide[1] + wide[2]) / 2
    single, multi = (
        wide[wide["rating_rows"] == "overall_only"],
        wide[wide["rating_rows"] == "overall_and_attributes"],
    )
    assert len(d) == len(wide) == 1991
    assert ttest(single[0], multi[0]) == ttest(
        d.loc[d["oAndA"] == 0, "overall"], d.loc[d["oAndA"] == 1, "overall"]
    )
    dp = d.dropna(subset=["prefQs"])
    assert ttest(single["prefQs"].dropna(), multi["prefQs"].dropna()) == ttest(
        dp.loc[dp["oAndA"] == 0, "prefQs"], dp.loc[dp["oAndA"] == 1, "prefQs"]
    )
    assert single[0].mean() < multi[0].mean()  # the paper's direction


@needs_raw
def test_study10_swapping_the_rows_breaks_it() -> None:
    d = r_study10()
    b = built("study10")
    b = b[b["task_num"] == 0]
    swapped = b["rating_rows"].map(
        {"overall_only": "overall_and_attributes", "overall_and_attributes": "overall_only"}
    )
    got = ttest(
        b.loc[swapped == "overall_only", "response_num"],
        b.loc[swapped == "overall_and_attributes", "response_num"],
    )
    assert got != ttest(d.loc[d["oAndA"] == 0, "overall"], d.loc[d["oAndA"] == 1, "overall"])


@needs_raw
@pytest.mark.parametrize("tag", ["s3", "s4"])
def test_recall_studies_t_test(tag: str) -> None:
    d = deposit(tag)
    d["rating"] = (
        d["overallSingle"]
        .where(d["condition"] == "single")
        .fillna(d["overallMultiple"].where(d["condition"] == "multiple"))
    )
    d = r_keep(
        d,
        d["rating"].isna(),
        eq(d["duplicateIP"], 1),
        eq(d["duplicateID"], 1),
        eq(d["unapprovedID"], 1),
    )
    b = built(tag)
    want = ttest(
        d.loc[d["condition"] == "single", "rating"], d.loc[d["condition"] == "multiple", "rating"]
    )
    got = ttest(
        b.loc[b["rating_rows"] == "overall_only", "response_num"],
        b.loc[b["rating_rows"] == "overall_and_attributes", "response_num"],
    )
    assert got == want
    assert len(b) == {"s3": 1514, "s4": 1537}[tag]


@needs_raw
def test_s5_cell_means() -> None:
    d = deposit("s5")
    col = {
        "overallOnly": "overallOO",
        "overallAttributes": "overallOF",
        "attributesOverall": "overallOS",
    }
    d["overall"] = float("nan")
    for c, v in col.items():
        d.loc[d["condition"] == c, "overall"] = d.loc[d["condition"] == c, v]
    d = r_keep(
        d,
        d["overall"].isna(),
        eq(d["duplicateIP"], 1),
        eq(d["duplicateID"], 1),
        ne(d["attnCheck"], 2),
        eq(d["approvedID"], 0),
    )
    b = built("s5")
    name = {
        "overallOnly": "overall_only",
        "overallAttributes": "overall_then_attributes",
        "attributesOverall": "attributes_then_overall",
    }
    assert len(b) == len(d) == 2341
    for c, lvl in name.items():
        for s in (1, 2):
            want = d.loc[(d["condition"] == c) & (d["scenario"] == s), "overall"]
            got = b.loc[(b["rating_layout"] == lvl) & (b["scenario"] == str(s)), "response_num"]
            assert (len(got), round(got.mean(), 10)) == (len(want), round(want.mean(), 10))
    # the preregistered contrast: overall only vs the two attribute layouts pooled
    only = b["rating_layout"] == "overall_only"
    assert ttest(b.loc[only, "response_num"], b.loc[~only, "response_num"]) == ttest(
        d.loc[d["condition"] == "overallOnly", "overall"],
        d.loc[d["condition"] != "overallOnly", "overall"],
    )


def r_s7_long() -> pd.DataFrame:
    d = deposit("s7")
    rows = []
    for slot in (1, 2):
        for s in range(1, 7):
            at = d[d[f"orderS{s}"] == slot]
            for f in ("single", "multiple"):
                part = at[at["condition"] == f]
                rows.append(
                    pd.DataFrame(
                        {
                            "id": part["id"],
                            "slot": slot,
                            "scenario": s,
                            "condition": f,
                            "rating": part[f"{f}S{s}"],
                            "duplicateIP": part["duplicateIP"],
                            "duplicateID": part["duplicateID"],
                        }
                    )
                )
    long = pd.concat(rows, ignore_index=True)
    return r_keep(
        long, long["rating"].isna(), eq(long["duplicateIP"], 1), eq(long["duplicateID"], 1)
    )


@needs_raw
def test_s7_per_scenario_t_tests_and_slots() -> None:
    d = r_s7_long()
    b = built("s7")
    assert len(b) == len(d) == 3111
    lvl = {"single": "overall_only", "multiple": "overall_and_attributes"}
    for s in range(1, 7):
        w = d[d["scenario"] == s]
        g = b[b["scenario"] == str(s)]
        assert ttest(
            g.loc[g["rating_rows"] == "overall_only", "response_num"],
            g.loc[g["rating_rows"] == "overall_and_attributes", "response_num"],
        ) == ttest(
            w.loc[w["condition"] == "single", "rating"],
            w.loc[w["condition"] == "multiple", "rating"],
        )
    # slot by slot, and the second slot's earlier scenario is the one the person saw first
    for slot in (1, 2):
        w = d[d["slot"] == slot]
        g = b[b["task_num"] == slot - 1]
        for f, name in lvl.items():
            a = w.loc[w["condition"] == f, "rating"]
            c = g.loc[g["rating_rows"] == name, "response_num"]
            assert (len(c), round(c.mean(), 10)) == (len(a), round(a.mean(), 10))
    dep = deposit("s7").set_index("id")
    second = b[b["task_num"] == 1]
    for pid, earlier in zip(second["participant_id"], second["earlier_scenario"], strict=True):
        i = int(str(pid).rsplit("_", 1)[1])
        assert dep.at[i, f"orderS{earlier}"] == 1


@needs_raw
def test_s7_swapping_the_scenario_breaks_it() -> None:
    d = r_s7_long()
    b = built("s7")
    w = d[d["scenario"] == 1]
    g = b[b["scenario"] == "2"]
    assert ttest(
        g.loc[g["rating_rows"] == "overall_only", "response_num"],
        g.loc[g["rating_rows"] == "overall_and_attributes", "response_num"],
    ) != ttest(
        w.loc[w["condition"] == "single", "rating"], w.loc[w["condition"] == "multiple", "rating"]
    )


def r_study9_long() -> pd.DataFrame:
    d = deposit("study9")
    rows = []
    for pre, (dom, _, scen) in gen.DOMAINS.items():
        for f, (letter, _) in gen.FORMATS.items():
            for s in scen:
                col = f"{pre}S{s}{letter}Overall"
                part = d[d[col].notna()]
                rows.append(
                    pd.DataFrame(
                        {
                            "id": part["id"],
                            "domain": dom,
                            "scenario": s,
                            "format": f,
                            "order": part[f"order{dom.capitalize()}"],
                            "rating": part[col],
                            "attnCheck": part["attnCheck"],
                            "duplicateIP": part["duplicateIP"],
                            "duplicateID": part["duplicateID"],
                            "unapprovedID": part["unapprovedID"],
                        }
                    )
                )
    long = pd.concat(rows, ignore_index=True)
    return r_keep(
        long,
        long["rating"].isna(),
        eq(long["duplicateIP"], 1),
        eq(long["duplicateID"], 1),
        ne(long["attnCheck"], 1),
        eq(long["unapprovedID"], 1),
    )


@needs_raw
def test_study9_first_domain_cells_and_the_rest_counted() -> None:
    d = r_study9_long()
    b = built("study9")
    first = d[d["order"] == 1]
    assert len(d) - len(first) == gen.study9_later()
    # the bookcase-first people are dropped by ruling (their columns tie to blocks by position)
    bookcase = first["domain"] == "bookcase"
    assert int(bookcase.sum()) == gen.study9_bookcase_first() == 337
    first = first[~bookcase]
    assert len(b) == len(first) == 1089
    assert not b["scenario"].str.startswith("bookcase").any()
    lvl = {f: v for f, (_, v) in gen.FORMATS.items()}
    cells = first.groupby(["domain", "scenario", "format"])
    assert cells.ngroups == b.groupby(["scenario", "rating_rows"]).ngroups == 48
    for (dom, s, f), w in cells:
        g = b[(b["scenario"] == f"{dom}_{s}") & (b["rating_rows"] == lvl[f])]
        assert (len(g), round(g["response_num"].mean(), 10)) == (
            len(w),
            round(w["rating"].mean(), 10),
        ), (dom, s, f)


@needs_raw
def test_study9_swapping_positive_and_negative_breaks_it() -> None:
    d = r_study9_long()
    first = d[d["order"] == 1]
    b = built("study9")
    swap = {
        "positive_attributes": "negative_attributes",
        "negative_attributes": "positive_attributes",
    }
    b["rating_rows"] = b["rating_rows"].replace(swap)
    w = first[(first["domain"] == "airplane") & (first["format"] == "positive")]
    g = b[(b["scenario"].str.startswith("airplane")) & (b["rating_rows"] == "positive_attributes")]
    assert round(g["response_num"].mean(), 10) != round(w["rating"].mean(), 10)
