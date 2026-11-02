"""The rhfd6 recipe (IMG55, safer gambling adverts and stigma) and its answer key.

The generator reads the outcome wording and the page before the adverts out of the
fielded .qsf, reshapes the export to one row per person per advert, and quotes the
words on each advert; these tests stop a hand edit drifting from it, and check the
facts the rows rest on:

- each of the five arms shows ONE advert, quotes the catalogue's transcription of it,
  and cites the OSF file its .qsf block displayed;
- the three statements are the .qsf's, identical in all five blocks;
- every person's fifteen rows are five adverts x three statements, never one advert
  twice;
- the built rows reproduce the authors' knitted analysis (Stigma.html, 24 Sep 2025)
  and preprint (Palmer et al. 2025, OSF h8vxz v1): N, age, sex, PGSI mean, SD and
  risk categories, the item frequency table, Cronbach's alpha, the five advert means
  and all ten pairwise differences to the four decimals printed.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_rhfd6.py"
RECIPE = REPO / "recipes" / "images" / "rhfd6.yaml"
RAW = REPO / "data" / "raw" / "rhfd6"
CSV = RAW / "Data" / "stigma_data.csv"
BUILT = REPO / "data" / "processed" / "images" / "rhfd6.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_rhfd6", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not CSV.exists(), reason="rhfd6 deposit not fetched")
needs_built = pytest.mark.skipif(not (BUILT.exists() and CSV.exists()), reason="rhfd6 not built")

DEPOSIT, STIGMA, CHASING, ODDS, BET_RESP = range(5)


@needs_raw
def test_recipe_is_what_the_generator_writes() -> None:
    assert RECIPE.read_text() == gen.render()


@needs_raw
def test_the_coded_spreadsheet_is_what_prep_derives() -> None:
    coded = pd.read_excel(RAW / gen.DATA_FILE)
    pd.testing.assert_frame_equal(gen.prep(), coded, check_dtype=False)


@needs_raw
def test_catalogue_entries_are_what_the_generator_derives() -> None:
    cat = images_mod.load()
    for image_id, entry in gen.catalogue_entries().items():
        assert cat[image_id].model_dump() == entry, image_id
        assert not images_mod.problems(image_id, cat), image_id


def test_each_arm_quotes_and_shows_its_own_advert() -> None:
    rec = load(RECIPE)
    cat = images_mod.load()
    assert sorted(a.condition_num for a in rec.condition.arms) == list(range(5))
    assert len({a.text for a in rec.condition.arms}) == 5
    for arm in rec.condition.arms:
        key = gen.ADVERTS[arm.condition_num][0]
        assert arm.raw == arm.condition_num + 1
        assert arm.images == [f"rhfd6_{key}"]
        assert arm.text.count(images_mod.IMAGE_MARKER) == 1
        words = cat[arm.images[0]].text_in_image
        assert words and words in arm.text
        assert arm.text.startswith("One of the adverts: ")
    assert rec.condition.shared_context == (
        "You will now be presented with various safer gambling adverts. Please rate each "
        "message using the scales provided."
    )


def test_no_row_says_where_its_advert_sat() -> None:
    rec = load(RECIPE)
    position = ("first", "second", "third", "fourth", "fifth", "next", "previous", "last")
    for arm in rec.condition.arms:
        text = rec.condition.render(arm)
        assert not any(f" {w} " in f" {text.lower()} " for w in position), arm.text


def test_the_outcomes_are_the_three_statements() -> None:
    rec = load(RECIPE)
    assert [o.question for o in rec.outcomes] == [
        "This advertisement makes me think that people who gamble heavily are at fault for "
        "whatever may happen to them.",
        "This advertisement makes me think that people wouldn't gamble heavily if they had "
        "more will-power.",
        "This advertisement makes me think that people who gamble heavily are worse than "
        "those who can control their gambling.",
    ]
    for o in rec.outcomes:
        assert (o.scale.min, o.scale.max) == (1, 7)
        assert (o.scale.min_label, o.scale.mid_label, o.scale.max_label) == (
            "Strongly disagree",
            "Neither agree nor disagree",
            "Strongly agree",
        )


@needs_raw
def test_the_five_blocks_ask_the_same_statements() -> None:
    first = gen.statements(gen.ADVERTS[0][2])
    for advert in gen.ADVERTS:
        assert gen.statements(advert[2]) == first
        assert gen.graphics_in(gen.grid(advert[2])) == [advert[3]]


@needs_raw
def test_the_two_discards_are_dropped_and_nobody_else() -> None:
    raw = pd.read_csv(CSV)
    coded = pd.read_excel(RAW / gen.DATA_FILE)
    assert len(raw) == 500 and (raw["Honesty"] == 1).sum() == 2
    assert coded[gen.ID_VAR].nunique() == 498
    assert len(coded) == 498 * 5


def _wide() -> pd.DataFrame:
    rows = pd.read_parquet(BUILT)
    w = rows.pivot_table(
        index=["participant_id", "condition_num"], columns="task_num", values="response_num"
    ).reset_index()
    w["stigma"] = w[[0, 1, 2]].mean(axis=1)
    return w


@needs_built
def test_every_person_rates_every_advert_once() -> None:
    rows = pd.read_parquet(BUILT)
    assert len(rows) == 498 * 5 * 3
    per = rows.groupby("participant_id").apply(
        lambda g: sorted(zip(g["condition_num"], g["task_num"], strict=True))
    )
    assert all(p == [(c, t) for c in range(5) for t in range(3)] for p in per)


@needs_built
def test_sample_matches_the_knitted_analysis() -> None:
    rows = pd.read_parquet(BUILT)
    people = rows.groupby("participant_id")["persona"].first().map(json.loads)
    assert len(people) == 498
    ages = np.array([p["age"] for p in people])
    assert round(ages.mean(), 2) == 38.01 and round(ages.std(ddof=1), 2) == 11.68
    assert np.median(ages) == 36
    sexes = pd.Series([p["sex"] for p in people]).value_counts(dropna=False).to_dict()
    assert sexes["Female"] == 186 and sexes["Male"] == 311  # and 1 Prefer not to say, absent
    code = {"Never": 0, "Sometimes": 1, "Most of the time": 2, "Almost always": 3}
    pgsi = np.array(
        [
            sum(code[v] for k, v in p["extra"].items() if k.startswith(gen.PGSI_STEM_KEY))
            for p in people
        ]
    )
    assert round(pgsi.mean(), 2) == 3.37 and round(pgsi.std(ddof=1), 1) == 4.8
    cats = [(pgsi == 0).sum(), ((pgsi >= 1) & (pgsi < 3)).sum()]
    cats += [((pgsi >= 3) & (pgsi < 8)).sum(), (pgsi >= 8).sum()]
    assert cats == [170, 137, 122, 69]


@needs_built
def test_item_table_and_alpha() -> None:
    rows = pd.read_parquet(BUILT)
    # Stigma.html, psych::alpha: item means 3.6 (Fault), 3.9 (Willpower), 3.5 (Worse)
    means = rows.groupby("task_num")["response_num"].mean().round(1).to_dict()
    assert means == {0: 3.6, 1: 3.9, 2: 3.5}
    freq = rows.groupby("task_num")["response_num"].value_counts(normalize=True).round(2)
    printed = {
        0: [0.13, 0.22, 0.16, 0.14, 0.19, 0.11, 0.05],
        1: [0.09, 0.19, 0.14, 0.15, 0.23, 0.14, 0.05],
        2: [0.13, 0.23, 0.15, 0.16, 0.18, 0.11, 0.04],
    }
    for task, shares in printed.items():
        assert [freq[(task, float(v))] for v in range(1, 8)] == shares, task
    w = _wide()
    x = w[[0, 1, 2]]
    alpha = 3 / 2 * (1 - x.var().sum() / x.sum(axis=1).var())
    assert round(alpha, 2) == 0.84
    assert round(w["stigma"].mean(), 2) == 3.65 and round(w["stigma"].std(), 2) == 1.52
    assert round(w["stigma"].median(), 2) == 3.67


@needs_built
def test_advert_means_and_pairwise_differences() -> None:
    m = _wide().groupby("condition_num")["stigma"].mean()
    # emmeans; with every person rating every advert, these are the cell means.
    printed_means = {CHASING: 4.38, BET_RESP: 3.63, DEPOSIT: 3.46, STIGMA: 3.44, ODDS: 3.32}
    assert {k: round(v, 2) for k, v in m.items()} == printed_means
    printed_pairs = [
        (BET_RESP, CHASING, -0.7584),
        (BET_RESP, DEPOSIT, 0.1647),
        (BET_RESP, ODDS, 0.3046),
        (BET_RESP, STIGMA, 0.1874),
        (CHASING, DEPOSIT, 0.9230),
        (CHASING, ODDS, 1.0629),
        (CHASING, STIGMA, 0.9458),
        (DEPOSIT, ODDS, 0.1399),
        (DEPOSIT, STIGMA, 0.0228),
        (ODDS, STIGMA, -0.1171),
    ]
    for a, b, est in printed_pairs:
        assert round(m[a] - m[b], 4) == est, (a, b)


@needs_raw
def test_pgsi_order_did_not_move_pgsi() -> None:
    """Half answered the PGSI after the adverts. The authors' negative-binomial test of
    PGSI on that order was not significant; a t-test on the deposit agrees."""
    raw = pd.read_csv(CSV)
    raw = raw[raw["Honesty"] != 1]
    a = raw.loc[raw["counterbalance"] == 0, "PGSI"]
    b = raw.loc[raw["counterbalance"] == 1, "PGSI"]
    assert (len(a), len(b)) == (250, 248)
    assert stats.ttest_ind(a, b, equal_var=False).pvalue > 0.05


@needs_built
def test_built_parquet_is_current(tmp_path: Path) -> None:
    """The answer-key tests read the parquet on disk, so a stale build would let a
    generator change (e.g. two adverts' column prefixes swapped) pass them unseen.
    Rebuild from the current recipe in memory and require the same rows."""
    from micromotives_datasets import cli

    rec, rows, _ = cli._load_and_build(RECIPE)
    fresh = pd.read_parquet(cli._write_parquet(rows, tmp_path, rec))
    on_disk = pd.read_parquet(BUILT)
    assert fresh.equals(on_disk), "rhfd6.parquet is stale: rebuild with mmds build"
