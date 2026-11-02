"""The be8a2 recipe (IMG54, digital imprints on campaigners' posts) and its answer key.

The generator reshapes the export to one row per person per post, codes every answer
by label and quotes the words on each post; these tests stop a hand edit drifting
from it, and check the facts the rows rest on:

- each of the 16 arms shows ONE post, in its own version, after its own group's
  text, and quotes the catalogue's transcription of that picture;
- the imprint is the only words that differ between a post's two versions, and
  the education text the only words that differ between the two groups;
- every person's four rows are four different conditions, two with an imprint;
- the built rows reproduce the authors' processed file (mixedeffect_df.csv) answer
  for answer, their exclusions, and the knitted analysis's descriptives table.

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
GEN = REPO / "scripts" / "gen_be8a2.py"
RECIPE = REPO / "recipes" / "images" / "be8a2.yaml"
RAW = REPO / "data" / "raw" / "be8a2"
CSV = RAW / "Data wrangle" / "main_data.csv"
AUTHORS = RAW / "Processed data" / "mixedeffect_df.csv"
BUILT = REPO / "data" / "processed" / "images" / "be8a2.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_be8a2", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not CSV.exists(), reason="be8a2 deposit not fetched")
needs_built = pytest.mark.skipif(not (BUILT.exists() and CSV.exists()), reason="be8a2 not built")


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


def test_each_arm_quotes_and_shows_its_own_post() -> None:
    rec = load(RECIPE)
    cat = images_mod.load()
    assert len(rec.condition.arms) == 16
    assert sorted(a.condition_num for a in rec.condition.arms) == list(range(16))
    for arm in rec.condition.arms:
        assert arm.raw_values is not None
        training = arm.raw_values["training"]
        k = arm.raw_values["post"] - 1
        imprint = bool(arm.raw_values["imprint"])
        assert arm.condition_num == gen.condition_num(training, k, int(imprint))
        assert arm.images == [gen.image_id(k, imprint)]
        assert arm.text.count(images_mod.IMAGE_MARKER) == 1
        img = cat[arm.images[0]]
        assert arm.text.startswith(gen.INTRO[training])
        assert arm.text.endswith(f'"{img.text_in_image}" {images_mod.IMAGE_MARKER}')
        assert ("Promoted by:" in (img.text_in_image or "")) == imprint
        assert gen.POSTS[k]["name"] in (img.text_in_image or "")
        assert arm.factors["post"] == gen.POSTS[k]["name"]
        # The education text names the law; the plain intro must not.
        assert ("transparency law" in arm.text) == (training == 1)


def test_the_imprint_is_the_only_words_that_differ_between_versions() -> None:
    for k, post in enumerate(gen.POSTS):
        plain = gen.post_words(k, False).split(" / ")
        shown = gen.post_words(k, True).split(" / ")
        assert [b for b in shown if b != post["imprint"]] == plain
        assert shown.count(post["imprint"]) == 1
        assert post["imprint"].startswith(f"Promoted by: {post['name']}, ")
        assert post["imprint"] not in plain


def test_the_education_text_is_the_only_words_that_differ_between_groups() -> None:
    for k in range(4):
        for imprint in (False, True):
            a, b = gen.arm_text(0, k, imprint), gen.arm_text(1, k, imprint)
            assert a.removeprefix(gen.INTRO[0]) == b.removeprefix(gen.INTRO[1])


def test_no_row_cites_its_position_in_the_sequence() -> None:
    for arm in load(RECIPE).condition.arms:
        for word in ("first", "second", "third", "fourth", "next", "previous", "Advert "):
            assert word not in arm.text, (arm.condition_num, word)


@needs_raw
def test_outcomes_are_the_codebook_wording() -> None:
    codebook = (RAW / "codebook.md").read_text().replace("\u2019", "'").replace("\u2013", "-")
    rec = load(RECIPE)
    assert len(rec.outcomes) == 13
    for outcome, (_, _, question, options) in zip(rec.outcomes, gen.OUTCOMES, strict=True):
        assert outcome.question == question
        if isinstance(options, tuple):  # a word pair: the stem, then the pair
            assert question == f'{gen.PAIR_STEM} "{options[0]}" - "{options[1]}"'
            assert f"{options[0]} (1) - {options[1]} (7)" in codebook, options
            assert gen.PAIR_STEM in codebook
        elif question.endswith('"'):  # a grid item: its screen's stem, then the statement
            stem, statement = question[:-1].split(' "')
            assert statement in codebook and stem in codebook, question
        else:
            assert question in codebook
    # The pre-fielding wording the authors say was replaced is not used.
    assert not any("do not feel able" in o.question for o in rec.outcomes)


@needs_raw
def test_prep_refuses_an_answer_in_the_unshown_version(monkeypatch: pytest.MonkeyPatch) -> None:
    wide = pd.read_csv(CSV, low_memory=False)
    first = wide.index[wide["Training.condition"].notna()][0]
    shown = bool(wide.loc[first, "Advert.1"])
    wide.loc[first, gen.raw_column("agree_{k}{v}", 1, not shown)] = "Agree"
    monkeypatch.setattr(pd, "read_csv", lambda *a, **k: wide.copy())
    with pytest.raises(SystemExit, match="unshown version"):
        gen.prep()


def _built() -> pd.DataFrame:
    rows = pd.read_parquet(BUILT)
    rows["pid"] = rows["participant_id"].str.removeprefix("be8a2:").astype(int)
    rows["training"] = rows["condition_num"] // 8
    rows["post"] = rows["condition_num"] % 8 // 2 + 1
    rows["version"] = rows["condition_num"] % 2
    return rows


@needs_built
def test_four_posts_per_person_two_with_imprint() -> None:
    rows = _built()
    per = rows.groupby("pid").agg(
        conds=("condition_num", "nunique"),
        posts=("post", "nunique"),
        training=("training", "nunique"),
    )
    assert len(per) == 1357
    assert (per["conds"] == 4).all() and (per["posts"] == 4).all() and (per["training"] == 1).all()
    imprints = rows.groupby("pid")["condition_num"].unique().map(lambda c: sum(x % 2 for x in c))
    assert (imprints == 2).all()


ITEMS = {
    0: "PK1_value",
    1: "PK2_value",
    2: "PK3_value",
    3: "PK4_value",
    4: "agree_value",
    5: "PG_value",
    6: "informed2_value",
    7: "informed3_value",
    8: "informed4_value",
    9: "accurate_value",
    10: "trustworthy_value",
    11: "believable_value",
    12: "factual_value",
}


def _wide(rows: pd.DataFrame) -> pd.DataFrame:
    return rows.pivot_table(
        index=["pid", "training", "post", "version"], columns="task_num", values="response_num"
    ).reset_index()


def _authors_sample() -> set[int]:
    """main_datawrangle.Rmd's exclusions, applied independently of its output."""
    raw = pd.read_csv(CSV, low_memory=False)
    raw["id"] = range(1, len(raw) + 1)
    raw = raw[~raw["EPE_5"].fillna("").str.match(r"^\s*$")].reset_index(drop=True)
    raw = raw[~(raw.index + 1).isin([420, 948, 1288, 1315])]
    return set(raw.loc[raw["Duration..in.seconds."] >= 360, "id"])


@needs_built
def test_reproduces_the_authors_processed_file() -> None:
    keep = _authors_sample()
    authors = pd.read_csv(AUTHORS)
    assert len(keep) == 1322 and keep == set(authors["id"])
    w = _wide(_built())
    authors["post"] = authors["advert"].str.removeprefix("advert.").astype(int)
    m = authors.merge(w, left_on=["id", "post"], right_on=["pid", "post"], suffixes=("_a", ""))
    assert len(m) == len(authors) == 5288
    assert (m["version_a"] == m["version"]).all()
    assert (m["Training.condition"] == m["training"]).all()
    for t, col in ITEMS.items():
        mine = m[t]
        if col == "informed3_value":  # the authors reverse-score it; we do not
            mine = 8 - mine
        assert (m[col] == mine).all(), col


@needs_built
def test_reproduces_the_knitted_descriptives_table() -> None:
    rows = _built()
    w = _wide(rows[rows["pid"].isin(_authors_sample())])
    w["informed"] = (w[6] + (8 - w[7]) + w[8]) / 3
    w["PK"] = w[[0, 1, 2, 3]].mean(axis=1)
    w["cred"] = w[[9, 10, 11, 12]].mean(axis=1)
    # knitted_analysis_script.pdf, 0.6 Group descriptives: (mean, SD) by
    # (training, version) for informed, PK and credibility.
    table = {
        (0, 0): (4.08, 1.56, 4.72, 1.05, 3.90, 1.42),
        (0, 1): (4.29, 1.54, 4.84, 1.06, 3.94, 1.36),
        (1, 0): (4.01, 1.60, 4.89, 1.05, 3.88, 1.38),
        (1, 1): (4.44, 1.54, 4.97, 1.09, 3.93, 1.39),
    }
    for (training, version), printed in table.items():
        g = w[(w["training"] == training) & (w["version"] == version)]
        got = []
        for col in ("informed", "PK", "cred"):
            got += [g[col].mean(), g[col].std()]
        assert np.allclose(got, printed, atol=0.005), (training, version, got)


@needs_built
def test_imprint_raises_enough_information_for_every_post() -> None:
    """A sign check per post: with its imprint, more people say the post said who placed it."""
    w = _wide(_built())
    means = w.groupby(["post", "version"])[6].mean().unstack()
    assert (means[1] > means[0]).all(), means
