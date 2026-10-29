"""The wsqyn recipe (IMG34) and its derived data must stay what the generator writes.

The generator pairs each photograph's three rating pages by their place in the
set's randomisers, reads every answer by its Qualtrics ImportId, and refuses to
write anything unless every cell agrees with the authors' own primary-analysis
file. These tests pin the facts the rows rest on: each arm cites one catalogued
image and quotes its page's heading; the one page whose grid asks "Vitamins &
minerals" instead of "Salt" says so, and no other does; and the agreement check
really fails when a single answer is wrong.

The recipe-equality test needs the deposit, which is gitignored, so it skips on
a fresh clone.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from types import ModuleType

import pytest

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_wsqyn.py"
RECIPE = REPO / "recipes" / "images" / "wsqyn.yaml"
QSF = REPO / "data" / "raw" / "wsqyn" / "Qualtrics survey" / "VSM_Validation_Study.qsf"

needs_data = pytest.mark.skipif(not QSF.exists(), reason="wsqyn deposit not fetched")


def _gen() -> ModuleType:
    spec = importlib.util.spec_from_file_location("gen_wsqyn", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@needs_data
def test_recipe_and_data_are_what_the_generator_writes() -> None:
    gen = _gen()
    long_rows, arms, meta = gen.derive()
    assert RECIPE.read_text(encoding="utf-8") == gen.render(arms, meta)
    assert gen.LONG.read_text(encoding="utf-8") == gen.long_csv(long_rows)
    assert gen.GROUPS.read_text(encoding="utf-8") == gen.food_groups(arms)


def test_every_arm_has_a_food_group_and_every_food_is_covered() -> None:
    groups = json.loads((REPO / "data" / "catalog" / "wsqyn_food_groups.json").read_text())
    arms = {str(a.condition_num) for a in load(RECIPE).condition.arms}
    assert set(groups["arms"]) == arms
    foods = {f["set_item"] for fs in groups["arms"].values() for f in fs}
    assert len(foods) == 520


def test_every_arm_cites_one_catalogued_image_under_its_own_heading() -> None:
    rec = load(RECIPE)
    cat = images_mod.load()
    assert len(rec.condition.arms) == 853
    seen = set()
    for arm in rec.condition.arms:
        assert len(arm.images) == 1
        img = cat[arm.images[0]]
        assert arm.factors["photo"] == arm.images[0]
        assert img.file.endswith(arm.images[0].removeprefix("wsqyn_") + Path(img.file).suffix)
        heading = arm.factors["heading"]
        assert f'under the heading "{heading}": <image>' in arm.text
        assert not re.search(r"<(?!image>)|&\w+;|\xa0", heading), heading
        seen.add((heading, arm.images[0]))
    assert len(seen) == 853, "an arm is one (heading, image) pair"


def test_only_the_vitamins_page_departs_from_the_salt_row() -> None:
    rec = load(RECIPE)
    salt = next(o for o in rec.outcomes if o.question.endswith('"Salt".'))
    overridden = [a for a in rec.condition.arms if a.items]
    assert len(overridden) == 1
    arm = overridden[0]
    assert arm.factors["heading"] == "Vegetable Thai Red Curry"
    assert set(arm.items) == {salt.task_num}
    assert arm.items[salt.task_num].outcome_question.endswith('"Vitamins & minerals".')


def test_every_grid_row_is_its_own_outcome_quoting_the_row_label() -> None:
    rec = load(RECIPE)
    rows = [o for o in rec.outcomes if o.var and o.var.startswith("grid_")]
    labels = [re.search(r'"([^"]+)"\.$', o.question).group(1) for o in rows]  # type: ignore[union-attr]
    assert labels == ["Calories", "Fat", "Saturated fat", "Sugar", "Salt"]
    assert all(o.condition_var == "arm_B" for o in rows)


def test_clean_resolves_markup_without_touching_words() -> None:
    gen = _gen()
    assert gen.clean('<h1 style="x">Pink Wafer&nbsp;</h1>') == "Pink Wafer"
    assert gen.clean("Sausage &amp; Mash<br>") == "Sausage & Mash"
    assert gen.clean("<span>&nbsp;Cheese scone</span>") == "Cheese scone"
    assert gen.clean("Spinache") == "Spinache"


def _one_row() -> tuple[list[dict], list[dict], dict]:
    codes = {
        "diet": {"Eat More": 1, "Eat Less": 2},
        "freq": {"None": 1, "1-2 times": 2},
        "grid": {"Low": 1, "Medium": 2, "High": 3},
        "grid_rows": {},
        "recognise": {"Yes": 1, "No": 2},
        "quality": {"Good": 1, "Okay": 2, "Bad": 3},
    }
    mine = {
        "_prolific": "p1", "set": 1, "item": 1, "taste": "50", "craving": "0",
        "healthy": "90", "positive": "70", "diet": 1, "freq": 1, "grid_1": 1,
        "grid_2": 1, "grid_3": 1, "grid_4": 2, "grid_5": 1, "recognise": 1,
        "quality": 1, "age": 30, "hunger": 20, "_bmi_authors": 22.5,
    }  # fmt: skip
    theirs = {
        "ProlificID": "p1", "Set": "1", "Item": "1", "Taste": "50", "Cravings": "0",
        "Healthiness": "90", "Positivity": "70", "HealthyDiet": "Eat More",
        "FreqofConsumption": "None", "CalorieEstimate": "Low", "FatEstimate": "Low",
        "SaturatedFatEstimate": "Low", "SugarEstimate": "Medium",
        "VitaminsMineralsEstimate": "Low", "Recognisability": "Yes",
        "QualityofImage": "Good", "Age": "30", "Hunger": "20", "BMI": "22.5",
    }  # fmt: skip
    return [mine], [theirs], codes


def test_agreement_check_passes_identical_cells() -> None:
    gen = _gen()
    mine, theirs, codes = _one_row()
    gen._check_against_primary(mine, theirs, codes)


@pytest.mark.parametrize(
    ("field", "value"),
    [("taste", "51"), ("freq", 2), ("grid_4", 3), ("hunger", 30), ("_bmi_authors", 23.0)],
)
def test_agreement_check_fails_on_one_wrong_cell(field: str, value: object) -> None:
    gen = _gen()
    mine, theirs, codes = _one_row()
    mine[0][field] = value
    with pytest.raises(SystemExit):
        gen._check_against_primary(mine, theirs, codes)
