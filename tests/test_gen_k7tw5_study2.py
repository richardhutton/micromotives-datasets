"""The k7tw5 Study 2 recipe (IMG03, snacks) must stay exactly what its generator derives.

The generator ties each arm to the deposit's Legend codes and refuses a deposit
whose energy-dense codes differ from the six it names; this stops a hand edit
drifting from that. It also checks what the arms rest on: six arms, the three
pictorial labels cited (and quoted) only where the picture was shown, the same
three quoted without pictures in the text-only arms, and no row claiming which
snack carried which label.

The recipe-equality and guard tests need the deposit, which is gitignored, so
they skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_k7tw5_study2.py"
RECIPE = REPO / "recipes" / "images" / "k7tw5_study2.yaml"
DATA = REPO / "data" / "raw" / "k7tw5" / "Study2" / "FoodLabellingOnline2Dataset.xlsx"

needs_data = pytest.mark.skipif(not DATA.exists(), reason="k7tw5 deposit not fetched")


def _gen() -> ModuleType:
    spec = importlib.util.spec_from_file_location("gen_k7tw5_study2", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@needs_data
def test_recipe_is_what_the_generator_writes() -> None:
    assert RECIPE.read_text() == _gen().render()


@needs_data
def test_generator_refuses_a_wrong_energy_dense_set() -> None:
    mod = _gen()
    mod.ENERGY_DENSE = [1, 2, 6, 8, 9, 11]  # carrot crisps in place of Galaxy
    with pytest.raises(SystemExit, match="energy-dense"):
        mod.recipe()


def test_pictures_only_where_shown_and_words_quoted_word_for_word() -> None:
    rec = load(RECIPE)
    cat = images_mod.load()
    arms = rec.condition.arms
    assert len(arms) == 6
    words = None
    for arm in arms:
        hwl = arm.factors["hwl"]
        if hwl == "image and text":
            assert len(arm.images) == 3
            assert arm.text.count(images_mod.IMAGE_MARKER) == 3
            quoted = [cat[i].text_in_image for i in arm.images]
            for w in quoted:
                assert f'"{w}" <image>' in arm.text
            words = words or quoted
        else:
            assert arm.images == []
            assert images_mod.IMAGE_MARKER not in arm.text
    assert words is not None
    for arm in arms:
        hwl = arm.factors["hwl"]
        if hwl == "text only":
            assert all(f'"{w}"' in arm.text for w in words)
        if hwl == "none":
            assert not any(w in arm.text for w in words)


def test_no_row_pairs_a_label_with_a_snack() -> None:
    # Which label sat on which snack is not in the source; the text may say the
    # six carry "one of these three", never "Doritos carries ...".
    for arm in load(RECIPE).condition.arms:
        assert "each on two of the six" in arm.text or arm.factors["hwl"] == "none"


def test_question_enumerates_the_twelve_snacks() -> None:
    rec = load(RECIPE)
    (outcome,) = rec.outcomes
    assert outcome.scale.nominal
    for n in range(1, 13):
        assert f" {n} " in outcome.question
    assert "Imagine you are at a vending machine." in outcome.question
