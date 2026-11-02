"""The gybnm recipe (IMG44, political advert disclaimers) and its answer key.

The generator codes every answer from the Qualtrics export by label and quotes the
words printed on each advert; these tests stop a hand edit drifting from it, and
check the facts the rows rest on:

- each arm shows the four adverts of its own column, plain or with the disclaimer,
  and quotes the catalogue's transcription of each;
- every outcome's wording is the export's own question text;
- the built rows reproduce the paper (Gordon, Stafford & Dommett 2024, CogSci):
  611 per arm after the authors' exclusions, Table 1's means, SDs and ranges, and
  the three OLS coefficients for the disclaimer and the agreement covariate.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_gybnm.py"
RECIPE = REPO / "recipes" / "images" / "gybnm.yaml"
RAW = REPO / "data" / "raw" / "gybnm"
CSV = RAW / "final_responses.csv"
BUILT = REPO / "data" / "processed" / "images" / "gybnm.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_gybnm", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not CSV.exists(), reason="gybnm deposit not fetched")
needs_built = pytest.mark.skipif(not (BUILT.exists() and CSV.exists()), reason="gybnm not built")


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


def test_each_arm_quotes_and_shows_its_own_four_adverts() -> None:
    rec = load(RECIPE)
    cat = images_mod.load()
    assert [a.raw for a in rec.condition.arms] == [0, 1]
    for arm in rec.condition.arms:
        disclaimer = arm.raw == 1
        assert arm.images == [gen.image_id(k, disclaimer) for k in range(4)]
        assert arm.text.count(images_mod.IMAGE_MARKER) == 4
        for image_id in arm.images:
            img = cat[image_id]
            assert f'"{img.text_in_image}" {images_mod.IMAGE_MARKER}' in arm.text
            assert (
                img.file.endswith("_transparent.jpg" if disclaimer else ".jpg")
                and ("material" in img.file) == disclaimer
            )
            assert ("Paid for by The Reconnect Party." in (img.text_in_image or "")) == disclaimer
            assert ("Political ad." in (img.text_in_image or "")) == disclaimer


def test_the_disclaimer_is_the_only_words_that_differ_between_arms() -> None:
    for k in range(4):
        plain = gen.ad_words(k, False).split(" / ")
        shown = gen.ad_words(k, True).split(" / ")
        extra = [b for b in shown if b not in plain]
        assert [b for b in shown if b in plain] == plain
        assert extra[0] == "Political ad." and extra[1].startswith("Paid for by")
        assert len(extra) == 2


@needs_raw
def test_outcome_wording_is_the_exports_question_text() -> None:
    texts = gen.question_texts()
    rec = load(RECIPE)
    for outcome in rec.outcomes:
        assert outcome.var is not None
        stem, statement = gen._split(texts[outcome.var])
        assert outcome.question.endswith(f'"{statement}"' if statement else stem)
        assert "Thank you" not in outcome.question
    built = {o.var for o in rec.outcomes}
    assert not built & {"MEM_PAID", "MEM_TAR", "AD_TRUST_3", "MISTRUST_EX_4", "PERC_ID"}


def _analytic() -> pd.DataFrame:
    """Built rows, one column per item, under the authors' exclusions."""
    raw = pd.read_csv(CSV, skiprows=[1, 2])
    raw["pid"] = range(1, len(raw) + 1)
    keep = set(raw.loc[(raw["Duration (in seconds)"] > 270) & (raw["AGE"] > 17), "pid"])
    rows = pd.read_parquet(BUILT)
    rows["pid"] = rows["participant_id"].str.removeprefix("gybnm:").astype(int)
    rows = rows[rows["pid"].isin(keep)]
    var = {o.task_num: o.var for o in load(RECIPE).outcomes}
    wide = rows.pivot(index="pid", columns="task_num", values="response_num").rename(columns=var)
    arm = rows.groupby("pid")["condition_num"].first()
    wide["arm"] = arm
    return wide


TRUST = ["COMP_1", "COMP_4", "INTEG_1", "INTEG_4", "BENEV_2", "BENEV_4"]
DISTRUST = ["COMP_2", "COMP_3", "INTEG_2", "INTEG_3", "BENEV_1", "BENEV_3"]


@needs_built
def test_paper_sample_and_table_1() -> None:
    w = _analytic()
    assert len(w) == 1222
    assert w["arm"].value_counts().to_dict() == {0: 611, 1: 611}
    w["trust"] = w[TRUST].mean(axis=1)
    w["distrust"] = w[DISTRUST].mean(axis=1)
    w["manip"] = w["AD_TRUST_2"]
    # Table 1: (mean, SD, min, max) per arm.
    table = {
        0: {
            "trust": (4.94, 0.93, 1.17, 7.0),
            "distrust": (3.17, 1.00, 1.0, 6.67),
            "manip": (3.33, 1.38, 1.0, 7.0),
        },
        1: {
            "trust": (4.94, 0.86, 1.0, 7.0),
            "distrust": (3.20, 0.95, 1.0, 6.67),
            "manip": (3.42, 1.33, 1.0, 7.0),
        },
    }
    for arm, measures in table.items():
        g = w[w["arm"] == arm]
        for m, (mean, sd, lo, hi) in measures.items():
            got = (g[m].mean(), g[m].std(), g[m].min(), g[m].max())
            # One printed SD is truncated, not rounded: control manipulativeness is
            # 1.3862 here (1.3851 with ddof=0) and printed 1.38. Every other cell
            # agrees to the printed two decimals.
            tol = 0.0065 if (arm, m) == (0, "manip") else 0.005
            assert np.allclose(got, (mean, sd, lo, hi), atol=tol), (arm, m, got)


@needs_built
def test_paper_regressions() -> None:
    w = _analytic()
    w["trust"] = w[TRUST].mean(axis=1)
    w["distrust"] = w[DISTRUST].mean(axis=1)
    x = np.column_stack([np.ones(len(w)), w["arm"], w["AGREE"]])
    n = len(w)
    # (outcome, |B| disclaimer, B agreement, F(2, 1219), adjusted R2), as printed.
    # The paper gives the disclaimer's B without sign ("B = 0.01, p = .71" for
    # trustworthiness; it is -0.014 here, t = -0.37, p = .71) and the agreement
    # effects as "increase"/"decrease"; signed here.
    printed = (
        ("trust", 0.01, 0.76, 459.9, 0.43),
        ("distrust", 0.04, -0.75, 330.3, 0.35),
        ("AD_TRUST_2", 0.10, -0.70, 114.0, 0.16),
    )
    for col, b_arm, b_agree, f_stat, adj_r2 in printed:
        y = w[col].to_numpy(dtype=float)
        coef, *_ = np.linalg.lstsq(x, y, rcond=None)
        resid = y - x @ coef
        r2 = 1 - (resid @ resid) / ((y - y.mean()) @ (y - y.mean()))
        assert round(abs(coef[1]), 2) == b_arm, (col, coef)
        assert round(coef[2], 2) == b_agree, (col, coef)
        assert round((r2 / 2) / ((1 - r2) / (n - 3)), 1) == f_stat, col
        assert round(1 - (1 - r2) * (n - 1) / (n - 3), 2) == adj_r2, col
