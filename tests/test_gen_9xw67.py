"""The 9xw67 conjoint recipe must stay exactly what its generator derives.

`recipes/9xw67_conjoint.yaml` is 455,919 lines of generated arms -- 95% of all
recipe text here. Its own notes said it came from "scripts/gen_conjoint_full.py-
equivalent code, not hand-typed", and that script was never kept, so the
judgement behind 11,991 arms survived only as prose describing code nobody could
run. `scripts/gen_9xw67_conjoint.py` is now that judgement, and this test is what
stops the two drifting apart silently.

Writing the generator immediately found two things the prose had hidden:

  * SIX value labels in the .dta are severed at Stata's 80-character ceiling,
    five of them the CLASS attribute -- the race-disparity manipulation the
    study is about. A generator reading the .dta naively puts "...are equally
    classifie" into the stimulus. The maker had recovered all six from the
    questionnaire; nothing recorded that it had, so the next person would have
    reintroduced it.

  * The scan order was ambiguous. "Scanning (pair, side) = (V1,A), (V1,B), ...
    across all 2,048 respondents in file order" reads equally well as
    respondent-major, and that assignment is completely different. Prose cannot
    pin an ordering.

The test needs the deposit, which is gitignored, so it skips when the data is
absent rather than failing on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_9xw67_conjoint.py"
RECIPE = REPO / "recipes" / "9xw67_conjoint.yaml"
DATA = REPO / "data" / "raw" / "9xw67" / "TESS 091B Ozer" / "s2078_surveyB_final_20211021.dta"


def _generator():
    spec = importlib.util.spec_from_file_location("gen_9xw67", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_9xw67"] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.skipif(not DATA.exists(), reason="9xw67 deposit not fetched (data/raw is gitignored)")
def test_the_recipe_is_exactly_what_the_generator_derives() -> None:
    generated = _generator().build_arms()
    recipe = yaml.safe_load(RECIPE.read_text())
    assert generated == recipe["condition"]["arms"], (
        "the recipe and its generator have diverged — regenerate with "
        "`uv run python scripts/gen_9xw67_conjoint.py --write`, and read the diff "
        "before accepting it"
    )


@pytest.mark.skipif(not DATA.exists(), reason="9xw67 deposit not fetched")
def test_no_arm_carries_a_truncated_attribute_label() -> None:
    """The six 80-character severances, pinned so they cannot creep back.

    Stata truncated them in the deposit; the questionnaire has them whole. This
    is the religion-label fault in stimulus text rather than persona text, and
    QC rule 18 cannot see it -- the cut lands mid-word, with no unclosed bracket
    to notice.
    """
    arms = _generator().build_arms()
    severed = [
        line
        for arm in arms
        for line in arm["text"].split("\n")
        if line.endswith(("classifie", "than white de", "recommendation that"))
    ]
    assert not severed, f"{len(severed)} lines still carry a truncated label: {severed[:2]}"

    full = "classified as high risk."
    assert any(full in arm["text"] for arm in arms), "the recovered wording is missing entirely"
