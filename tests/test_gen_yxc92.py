"""The yxc92 recipe (IMG75, Join This Group vs Tetris, UK) and its answer key.

The generator quotes the fielded Qualtrics surveys and pairs each export tag with
its picture; these tests stop a hand edit drifting from it, and check the facts
the rows rest on:

- every quoted passage is on screen in the .qsf, and the randomiser's own
  embedded-data field `Tetris` is the arm;
- each tag's picture is its PNG (printouts by pixels, display size), which
  contradicts the deposit's codebook for the four `Real` items;
- the pretest is one condition for both arms; post and follow-up rows exist only
  for the people the notes say;
- the built rows, under the authors' own exclusions, give their 425 Tetris and 345
  game players and every F statistic in their results tables (Script 3, one-way
  ANOVA on the change from pretest), to the printed third decimal.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_yxc92.py"
RECIPE = REPO / "recipes" / "images" / "yxc92.yaml"
BUILT = REPO / "data" / "processed" / "images" / "yxc92.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_yxc92", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.RAW_CSV.exists(), reason="yxc92 deposit not fetched")
needs_built = pytest.mark.skipif(
    not (BUILT.exists() and gen.RAW_CSV.exists()), reason="yxc92 not built"
)
needs_tools = pytest.mark.skipif(
    not (shutil.which("pdfimages") and shutil.which("sips")), reason="needs pdfimages and sips"
)


@needs_raw
def test_recipe_is_what_the_generator_writes() -> None:
    assert RECIPE.read_text() == gen.render()


@needs_raw
def test_the_coded_spreadsheet_is_what_prep_derives() -> None:
    coded = pd.read_excel(gen.DATA)
    pd.testing.assert_frame_equal(gen.prep(), coded, check_dtype=False)


@needs_raw
def test_catalogue_entries_are_what_the_generator_derives() -> None:
    cat = images_mod.load()
    for image_id, entry in gen.catalogue_entries().items():
        assert cat[image_id].model_dump() == entry, image_id


@needs_raw
def test_quotes_are_on_screen_and_the_randomiser_sets_tetris() -> None:
    gen.check_instrument()
    gen.check_flow()


@needs_raw
@needs_tools
def test_each_tag_shows_its_own_picture() -> None:
    gen.check_pictures()


@needs_raw
def test_display_sizes_overrule_the_codebook_for_the_real_items() -> None:
    """Each Real question displays its graphic at its PNG's own pixel size (Real2's
    scaled to width 211, same proportions); the codebook's pairing fits none."""
    live = gen.live_items()
    for tag, f in gen.CODEBOOK_REAL.items():
        sw, sh = live[(1, tag)]["size"]
        ow, oh = gen._png_size(gen.STIMULI / dict(gen.ITEMS)[tag])
        tw, th = gen._png_size(gen.STIMULI / f)
        if tag == "Real2":
            assert (ow, oh) != (sw, sh) and abs(sw / sh - ow / oh) < 0.01
        else:
            assert (ow, oh) == (sw, sh), tag
        assert abs(sw / sh - tw / th) > 0.03 * (tw / th), tag
        assert (tw, th) != (sw, sh), tag


@needs_raw
def test_party_none_is_an_answer_not_missing() -> None:
    """147 people chose "None"; the .xlsx reader would have blanked the text."""
    raw = gen.read_raw()
    coded = pd.read_excel(gen.DATA)
    codes = gen.party_codes()
    assert int((raw["PolParty"] == "None").sum()) == 147
    assert int((coded["PolParty"] == codes["None"]).sum()) == 147
    rec = load(RECIPE)
    assert rec.persona_label_rewrite["PolParty"][codes["None"]] == "None"
    assert rec.persona_missing["PolParty"] == [codes["Refuse to say"]]


def test_arms_quote_their_own_game_and_cite_one_picture() -> None:
    rec = load(RECIPE)
    assert len(rec.condition.arms) == 16 * 5
    for arm in rec.condition.arms:
        tag = arm.factors["message"]
        assert arm.images == [gen.image_id(tag)]
        assert arm.text.count(images_mod.IMAGE_MARKER) == 1
        assert arm.text.endswith(images_mod.IMAGE_MARKER)
        game = arm.factors["game"]
        assert ("Tetris" in arm.text) == (game == "Tetris" or arm.factors["moment"] == "follow-up")
        assert ("secret password" in arm.text) == (game == "Join This Group")
        if arm.factors["moment"] == "before the game":
            assert game == "not yet played" and arm.text == gen.pre_text()
        if arm.factors["moment"] == "follow-up":
            assert f'"{gen.DEBRIEF} ..."' in arm.text
        else:
            # The debrief came last in the first survey: nothing from it before then,
            # least of all its list of the four techniques the outcomes are about.
            for words in ("randomly assigned", "educational game", "four scenarios", "fake expert"):
                assert words not in arm.text, (arm.condition_num, words)
        if game == "Tetris":
            assert f'"{gen.TETRIS} ..."' in arm.text
        if game == "Join This Group":
            assert f'"{gen.JTG}" {gen.PASSWORD}' in arm.text


@needs_raw
def test_education_scheme_covers_every_label() -> None:
    raw = gen.read_raw()
    scheme = json.loads(
        (REPO / "data" / "catalog" / "persona_crosswalk_education.json").read_text()
    )["schemes"]["uk_yxc92_osf"]
    assert set(raw["Education"].dropna()) == set(scheme)


def _built() -> pd.DataFrame:
    rows = pd.read_parquet(BUILT)
    rows["pid"] = rows["participant_id"].str.removeprefix("yxc92:").astype(int)
    return rows


def _arm_of(cn: int) -> int:
    return ((cn - 16) // 16) % 2


@needs_built
def test_who_has_rows_at_each_moment() -> None:
    raw = gen.read_raw().set_index("pid")
    rows = _built()
    moment = rows["condition_num"].map(lambda c: 1 if c < 16 else 2 if c < 48 else 3)
    people = {m: set(rows.loc[moment == m, "pid"]) for m in (1, 2, 3)}
    assert len(people[1]) == 978  # everyone who started the first survey
    post = rows[moment == 2].groupby("pid")["condition_num"].first().map(_arm_of)
    assert post.value_counts().to_dict() == {0: 505, 1: 417}
    assert (raw.loc[post.index[post == 0], "Tetris"] == "1").all()
    assert raw.loc[post.index[post == 1], "JoinThisGroup"].isin(gen.VALID_PW).all()
    assert people[3] <= people[2]
    assert (raw.loc[list(people[3]), "Finished.T0"] == "True").all()
    assert raw.loc[list(people[3]), "StartDate.T10"].notna().all()
    # each person meets one arm only
    assert (
        rows[moment > 1].groupby("pid")["condition_num"].agg(lambda c: len(set(map(_arm_of, c))))
        == 1
    ).all()


# Results_Tables.xlsx (Main_Hypotheses and Exploratory), F(1, 768), change from
# pretest, Control vs Inoc: (score, items, measure, moment) -> F as printed.
PRINTED_F = {
    ("All", 1, 2): 82.748,
    ("All", 1, 3): 29.378,
    ("Craft", 1, 2): 85.065,
    ("Natur", 1, 2): 15.297,
    ("Craft", 1, 3): 29.903,
    ("Natur", 1, 3): 9.091,
    ("All", 2, 2): 47.279,
    ("All", 2, 3): 21.984,
    ("All", 3, 2): 15.962,
    ("All", 3, 3): 6.072,
    ("Craft", 2, 2): 56.106,
    ("Natur", 2, 2): 8.414,
    ("Craft", 2, 3): 23.379,
    ("Natur", 2, 3): 10.085,
    ("Craft", 3, 2): 13.123,
    ("Natur", 3, 2): 8.289,
}


@needs_built
def test_paper_sample_and_f_statistics() -> None:
    raw = gen.read_raw()
    days = (
        pd.to_datetime(raw["StartDate.T10"]) - pd.to_datetime(raw["EndDate.T0"])
    ).dt.total_seconds() / 86400
    keep = set(
        raw.loc[
            (raw["Finished.T0"] == "True") & (raw["Finished.T10"] == "True") & days.between(7, 14),
            "pid",
        ]
    )
    rows = _built()
    rows = rows[rows["pid"].isin(keep)]
    arm = rows[rows["condition_num"] >= 16].groupby("pid")["condition_num"].first().map(_arm_of)
    assert arm.value_counts().to_dict() == {0: 425, 1: 345}
    rows = rows[rows["pid"].isin(arm.index)]
    var = {o.task_num: o.var for o in load(RECIPE).outcomes}
    wide = rows.pivot(index="pid", columns="task_num", values="response_num").rename(columns=var)
    a = arm.reindex(wide.index)
    items = {"All": gen.TAGS, "Craft": gen.TAGS[:12], "Natur": gen.TAGS[12:]}

    def score(m: int, k: int, tags: list[str]) -> pd.Series:
        return wide[[f"{t}.{m}_{k}" for t in tags]].mean(axis=1)

    for (name, k, m), printed in PRINTED_F.items():
        y = score(m, k, items[name]) - score(1, k, items[name])
        groups = [y[a == i] for i in (0, 1)]
        between = sum(len(g) * (g.mean() - y.mean()) ** 2 for g in groups)
        within = sum(((g - g.mean()) ** 2).sum() for g in groups) / (len(y) - 2)
        assert round(between / within, 3) == printed, (name, k, m)


@needs_built
def test_built_parquet_is_current(tmp_path: Path) -> None:
    """The answer-key tests read the parquet on disk, so a stale build would let a
    generator change pass them unseen. Rebuild in memory and require the same rows."""
    from micromotives_datasets import cli

    rec, rows, _ = cli._load_and_build(RECIPE)
    fresh = pd.read_parquet(cli._write_parquet(rows, tmp_path, rec))
    on_disk = pd.read_parquet(BUILT)
    assert fresh.equals(on_disk), "yxc92.parquet is stale: rebuild with mmds build"
