"""The pr8zu Study 1 recipe (IMG01) must stay exactly what its generator derives.

The generator looks every arm's codes up by their labels in the deposit and ties
each arm to its catalogued picture; this stops a hand edit drifting from that. It
also checks the facts the arms rest on: 42 arms (21 labels x beer/wine), each
citing one catalogued image whose printed words the arm's text quotes
word-for-word, each naming the drink it was shown on, and no outcome built from
the desire-to-drink item, whose codes (1-5, 8, 9) the source cannot order.

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
GEN = REPO / "scripts" / "gen_pr8zu_study1.py"
RECIPE = REPO / "recipes" / "images" / "pr8zu_study1.yaml"
DATA = REPO / "data" / "raw" / "pr8zu" / "Study 1" / "Full dataset alcohol labelling study 1.xlsx"

needs_data = pytest.mark.skipif(not DATA.exists(), reason="pr8zu deposit not fetched")


@needs_data
def test_recipe_is_what_the_generator_writes() -> None:
    spec = importlib.util.spec_from_file_location("gen_pr8zu_study1", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert RECIPE.read_text() == mod.render()


def test_every_arm_quotes_the_words_printed_on_its_picture() -> None:
    rec = load(RECIPE)
    cat = images_mod.load()
    assert len(rec.condition.arms) == 42
    for arm in rec.condition.arms:
        assert len(arm.images) == 1
        img = cat[arm.images[0]]
        assert img.text_in_image, arm.images[0]
        assert f'"{img.text_in_image}"' in arm.text, arm.images[0]
        assert arm.text.count(images_mod.IMAGE_MARKER) == 1


def test_every_arm_names_the_drink_it_was_shown_on() -> None:
    rec = load(RECIPE)
    seen = set()
    for arm in rec.condition.arms:
        drink = arm.factors["drink"]
        assert f"The drink is {drink}." in arm.text
        other = {"beer": "wine", "wine": "beer"}[drink]
        assert other not in arm.text
        seen.add((arm.images[0], drink))
    assert len(seen) == 42, "each label appears once on beer and once on wine"


def test_desire_to_drink_is_not_built() -> None:
    rec = load(RECIPE)
    assert all("Desirability" not in (o.var or "") for o in rec.outcomes)
