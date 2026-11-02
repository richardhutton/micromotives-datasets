"""The xsfev Study 2 recipe (IMG40) must stay exactly what its generator derives.

The generator checks the deposit's condition codes and outcome columns and ties
each labelled arm to its three catalogued labels; this stops a hand edit drifting
from that. It also pins the facts the build rests on: three arms, the two label
arms citing three images each whose printed words they quote word-for-word, the
no-label arm citing none; no row claiming which label sat on which bar; and no
outcome built from the pre-treatment baseline ratings or the repeated second
snack choice.

The recipe-equality test needs the deposit, which is gitignored, so it skips on
a fresh clone.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_xsfev_study2.py"
RECIPE = REPO / "recipes" / "images" / "xsfev_study2.yaml"
DATA = REPO / "data" / "raw" / "xsfev" / "data" / "Study2_AvoidApproach_Data_20201019.xlsx"

needs_data = pytest.mark.skipif(not DATA.exists(), reason="xsfev deposit not fetched")


@needs_data
def test_recipe_is_what_the_generator_writes() -> None:
    spec = importlib.util.spec_from_file_location("gen_xsfev_study2", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert RECIPE.read_text() == mod.render()


def test_label_arms_quote_the_words_printed_on_their_pictures() -> None:
    rec = load(RECIPE)
    cat = images_mod.load()
    by_level = {a.factors["label"]: a for a in rec.condition.arms}
    assert set(by_level) == {"health warning", "irrelevant aversive", "none"}
    for level in ("health warning", "irrelevant aversive"):
        arm = by_level[level]
        assert len(arm.images) == 3
        assert arm.text.count(images_mod.IMAGE_MARKER) == 3
        for image_id in arm.images:
            words = cat[image_id].text_in_image
            assert words, image_id
            assert f'"{words}" {images_mod.IMAGE_MARKER}' in arm.text, image_id
    assert by_level["none"].images == []
    assert images_mod.IMAGE_MARKER not in by_level["none"].text


def test_no_row_says_which_label_was_on_which_bar() -> None:
    # The deposit's own pictures disagree about the pairing, so nothing may assert one.
    rec = load(RECIPE)
    for arm in rec.condition.arms:
        for bar in ("Dairy Milk", "Mars", "Snickers", "Galaxy"):
            assert f"{bar}'s" not in arm.text and f"{bar} carries" not in arm.text


def test_baseline_and_second_choice_are_not_built() -> None:
    rec = load(RECIPE)
    vars_ = [o.var or "" for o in rec.outcomes]
    assert not any(v.startswith("Baseline") for v in vars_)
    assert not any(v.startswith("2nd Snack") for v in vars_)
    # Stationery columns are "Post-IM task-pen-like" etc.; the bars' carry "(labelled ...)".
    assert not any(v.startswith("Post-IM task-") for v in vars_)
    assert len(rec.outcomes) == 10


def test_labelled_choice_names_what_each_arm_saw_on_the_bars() -> None:
    rec = load(RECIPE)
    for arm in rec.condition.arms:
        q = arm.items[9].outcome_question or ""
        if arm.factors["label"] == "none":
            # The same screen as task 8: dropped (empty recode), not asked twice.
            assert arm.items[9].response_recode == {} and not q
        else:
            assert "each carrying one of the" in q and "without any label" not in q
