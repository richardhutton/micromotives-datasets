"""The k369t recipe (IMG27) must stay exactly what its generator derives.

The generator looks every arm's codes up by label and builds each arm's answer
recode from its own dish's photographs; this stops a hand edit drifting from
that. It also checks the facts the arms rest on: 72 arms (4 labelling groups x
18 dishes), each citing its dish's catalogued picture and quoting the caption
printed on it; the no-label group told nothing about calories or walking; each
labelled group told exactly its own label and recommendation; and a photograph
code counting as an answer only in its own dish's arms, which is what drops the
one "Biryani" trial recorded with a tortellini photograph.

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
GEN = REPO / "scripts" / "gen_k369t.py"
RECIPE = REPO / "recipes" / "images" / "k369t.yaml"
DATA = REPO / "data" / "raw" / "k369t" / "kcal_pace_data_OSF_final.xlsx"

needs_data = pytest.mark.skipif(not DATA.exists(), reason="k369t deposit not fetched")

KCAL = "On average women need 2,000 kcal per day"
PACE = "adults should aim to take part in at least 150 minutes"


@needs_data
def test_recipe_is_what_the_generator_writes() -> None:
    spec = importlib.util.spec_from_file_location("gen_k369t", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert RECIPE.read_text() == mod.render()


def test_every_arm_quotes_the_caption_printed_on_its_picture() -> None:
    rec = load(RECIPE)
    cat = images_mod.load()
    assert len(rec.condition.arms) == 72
    seen = set()
    for arm in rec.condition.arms:
        assert len(arm.images) == 1
        img = cat[arm.images[0]]
        assert img.text_in_image == arm.factors["dish"], arm.images[0]
        assert f'captioned "{img.text_in_image}"' in arm.text, arm.images[0]
        assert arm.text.count(images_mod.IMAGE_MARKER) == 1
        seen.add((arm.factors["label"], arm.images[0]))
    assert len(seen) == 72, "each dish's picture appears once per labelling group"


def test_each_group_is_told_its_own_label_and_nothing_else() -> None:
    rec = load(RECIPE)
    for arm in rec.condition.arms:
        label = arm.factors["label"]
        has_kcal = label in ("kcal", "kcal and PACE")
        has_pace = label in ("PACE", "kcal and PACE")
        assert ("kcal" in arm.text) == has_kcal, arm.condition_num
        assert ("walking" in arm.text) == has_pace, arm.condition_num
        assert (KCAL in arm.text) == has_kcal, arm.condition_num
        assert (PACE in arm.text) == has_pace, arm.condition_num
        assert ('"600 kcal"' in arm.text) == has_kcal, arm.condition_num
        assert ('"120 min"' in arm.text) == has_pace, arm.condition_num


def test_a_photograph_counts_only_in_its_own_dishs_arms() -> None:
    rec = load(RECIPE)
    by_dish: dict[str, dict[int, int]] = {}
    for arm in rec.condition.arms:
        recode = arm.response_recode
        assert recode, arm.condition_num
        assert set(recode.values()) <= set(range(1, 51)), arm.condition_num
        dish = arm.factors["dish"]
        # The same dish gets the same recode in every labelling group.
        assert by_dish.setdefault(dish, recode) == recode, arm.condition_num
    codes = [set(r) for r in by_dish.values()]
    assert len(codes) == 18
    assert sum(len(c) for c in codes) == len(set().union(*codes)), "a code in two dishes"
