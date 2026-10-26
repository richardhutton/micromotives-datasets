"""The k7tw5 Study 1 recipe (IMG02) must stay exactly what its generator derives.

The generator looks every arm's code up by its label in the deposit and ties each
arm to its catalogued picture; this stops a hand edit drifting from that. It also
checks the two facts the arms rest on: 18 arms, each citing one catalogued image
whose printed words the arm's text quotes word-for-word.

Needs the deposit, which is gitignored, so it skips on a fresh clone.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_k7tw5_study1.py"
RECIPE = REPO / "recipes" / "images" / "k7tw5_study1.yaml"
DATA = REPO / "data" / "raw" / "k7tw5" / "Study1" / "Food labelling study 1 final dataset.xlsx"

needs_data = pytest.mark.skipif(not DATA.exists(), reason="k7tw5 deposit not fetched")


@needs_data
def test_recipe_is_what_the_generator_writes() -> None:
    spec = importlib.util.spec_from_file_location("gen_k7tw5_study1", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert RECIPE.read_text() == mod.render()


def test_every_arm_quotes_the_words_printed_on_its_picture() -> None:
    rec = load(RECIPE)
    cat = images_mod.load()
    assert len(rec.condition.arms) == 18
    for arm in rec.condition.arms:
        assert len(arm.images) == 1
        img = cat[arm.images[0]]
        assert img.text_in_image, arm.images[0]
        assert f'"{img.text_in_image}"' in arm.text, arm.images[0]
        assert arm.text.count(images_mod.IMAGE_MARKER) == 1
