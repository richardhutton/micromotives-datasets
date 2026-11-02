"""The pr8zu Study 2 recipe (IMG03, alcohol) must stay exactly what its generator derives.

The deposit has no codebook, so the generator ties its condition codes to arms
by the paper's counts and refuses a deposit whose control group is not the one
re-randomised for acceptability. This test stops a hand edit drifting from the
generator, and checks what the arms rest on: 4 label types x beer/wine, the
three labels' pictures cited only in the image-and-text arm, their words quoted
in the text-only arm, neither words nor pictures in the image-only arm, and the
response only ever "alcoholic or not", which is all the deposit records.

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
GEN = REPO / "scripts" / "gen_pr8zu_study2.py"
RECIPE = REPO / "recipes" / "images" / "pr8zu_study2.yaml"
DATA = REPO / "data" / "raw" / "pr8zu" / "Study 2" / "Alcohol study 2 full dataset.xlsx"

needs_data = pytest.mark.skipif(not DATA.exists(), reason="pr8zu deposit not fetched")


def _gen() -> ModuleType:
    spec = importlib.util.spec_from_file_location("gen_pr8zu_study2", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@needs_data
def test_recipe_is_what_the_generator_writes() -> None:
    assert RECIPE.read_text() == _gen().render()


@needs_data
def test_generator_refuses_a_control_that_was_not_re_randomised() -> None:
    mod = _gen()
    mod.CONTROL_CODE = 4  # the protocol's numbering, which the deposit does not use
    with pytest.raises(SystemExit, match="control group"):
        mod.recipe()


def test_labels_appear_only_in_the_form_each_arm_saw() -> None:
    rec = load(RECIPE)
    cat = images_mod.load()
    arms = rec.condition.arms
    assert len(arms) == 8
    assert {(a.factors["label"], a.factors["drink"]) for a in arms} == {
        (lab, d)
        for lab in ("none", "text only", "image only", "image and text")
        for d in ("beer", "wine")
    }
    hwl_ids = {i for a in arms if a.factors["label"] == "image and text" for i in a.images}
    assert len(hwl_ids) == 3
    words = [cat[i].text_in_image for i in sorted(hwl_ids)]
    assert all(words)
    for arm in arms:
        # Only the image-and-text arm saw the labels as pictures with words.
        # Image-only, text-only and control must cite no catalogued label.
        if arm.factors["label"] != "image and text":
            assert not set(arm.images) & hwl_ids, (arm.factors, arm.images)
            assert not any(cat[i].text_in_image in words for i in arm.images if i in cat)
        label = arm.factors["label"]
        assert f"The drinks are {arm.factors['drink']}." in arm.text
        if label == "image and text":
            assert arm.text.count(images_mod.IMAGE_MARKER) == 3
            assert all(f'"{w}" <image>' in arm.text for w in words)
        else:
            assert arm.images == [] and images_mod.IMAGE_MARKER not in arm.text
        if label == "text only":
            assert all(f'"{w}"' in arm.text for w in words)
        if label in ("image only", "none"):
            assert not any(w in arm.text for w in words)


def test_response_is_only_alcoholic_or_not() -> None:
    (outcome,) = load(RECIPE).outcomes
    assert outcome.scale.nominal and (outcome.scale.min, outcome.scale.max) == (0, 1)
    assert "Only whether the drink you choose is alcoholic is recorded" in outcome.question
