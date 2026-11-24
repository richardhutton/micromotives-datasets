"""The 4zscf recipe (TESS3 192, Mize), checked on the recipe alone.

Four stories, 2 x 2: Michael or Emily, past relationships all with women or all
with men, then a casual encounter with someone of the other kind. One screen of
three number boxes (heterosexual / straight, gay or gay/lesbian, bisexual, each
0-100) follows the story, asked as Q1 about Michael and Q2 about Emily. So the
three outcomes are crossed with the arms, and the variable and wording are set per
(arm, task). These tests pin that crossing, so a hand edit cannot put Michael's
question under Emily's story, swap two boxes, or let one box's sentence name
another. The words themselves are checked against the questionnaire, and the rows
against the deposit, in `test_4zscf_answer_key.py`.
"""

from __future__ import annotations

import itertools
from pathlib import Path

import pytest

from micromotives_datasets.recipe import Recipe, load

RECIPE = Path(__file__).resolve().parents[1] / "recipes" / "4zscf.yaml"

LABELS = {
    "Michael": ("Heterosexual / Straight", "Gay", "Bisexual"),
    "Emily": ("Heterosexual / Straight", "Gay/Lesbian", "Bisexual"),
}
TARGET = {1: "Michael", 2: "Michael", 3: "Emily", 4: "Emily"}
FACTORS = {
    1: {"target_gender": "man", "sexual_history": "heterosexual"},
    2: {"target_gender": "man", "sexual_history": "same-sex"},
    3: {"target_gender": "woman", "sexual_history": "heterosexual"},
    4: {"target_gender": "woman", "sexual_history": "same-sex"},
}


@pytest.fixture(scope="module")
def rec() -> Recipe:
    return load(RECIPE)


def cell(rec: Recipe, raw: int, task: int) -> tuple[str, str]:
    arm = next(a for a in rec.condition.arms if a.raw == raw)
    out = next(o for o in rec.outcomes if o.task_num == task)
    item = arm.items.get(task)
    var = (item.outcome_var if item and item.outcome_var else None) or out.var
    q = (item.outcome_question if item and item.outcome_question else None) or out.question
    assert var is not None
    return var, q


def test_assignment_and_arm_numbering(rec: Recipe) -> None:
    assert rec.condition.source_var == "DOV_TESS192"
    # raw n -> n - 1, which is also SocSci210's numbering
    assert sorted((a.raw, a.condition_num) for a in rec.condition.arms) == [
        (1, 0),
        (2, 1),
        (3, 2),
        (4, 3),
    ]
    assert rec.comparable_to_socsci210 is True
    for name in ("DOV_Order1", "DOV_Order2", "DOV_Order3"):
        assert name in rec.condition.considered_and_rejected


def test_factors_are_a_full_two_by_two_matching_the_stories(rec: Recipe) -> None:
    assert rec.condition.factors == ["target_gender", "sexual_history"]
    seen = set()
    for arm in rec.condition.arms:
        assert arm.raw is not None
        assert arm.factors == FACTORS[arm.raw]
        seen.add((arm.factors["target_gender"], arm.factors["sexual_history"]))
        name = TARGET[arm.raw]
        assert arm.text.startswith(f"{name} is currently single")
        # history: same-sex means past partners of the target's own sex
        own, other = ("men", "women") if name == "Michael" else ("women", "men")
        past = own if arm.factors["sexual_history"] == "same-sex" else other
        assert f"multiple happy relationships with {past} in the past" in arm.text
        assert f"has only dated {past}" in arm.text
    assert seen == set(itertools.product(("man", "woman"), ("heterosexual", "same-sex")))


@pytest.mark.parametrize("raw", [1, 2, 3, 4])
def test_each_cell_asks_about_its_own_target_from_its_own_box(rec: Recipe, raw: int) -> None:
    name = TARGET[raw]
    q = "Q1" if name == "Michael" else "Q2"
    for task, box in enumerate("ABC"):
        var, question = cell(rec, raw, task)
        assert var == f"{q}_{box}"
        lines = question.split("\n")
        assert lines[0] == f"How likely to do you think {name} is:"
        assert f"completely certain {name} is that orientation" in lines[1]
        assert tuple(lines[2:5]) == LABELS[name]
        assert lines[5] == f'Report only the percentage for "{LABELS[name][task]}".'
        # the other target's name never appears
        other = "Emily" if name == "Michael" else "Michael"
        assert other not in question


def test_scale_recode_and_missing(rec: Recipe) -> None:
    for o in rec.outcomes:
        assert (o.scale.min, o.scale.max) == (0, 100)
        assert o.scale.min_label is None and o.scale.max_label is None
    assert rec.response_recode == {v: v for v in range(101)}
    assert rec.missing_codes == [-1]


def test_persona_leaves_out_the_outcomes_own_domain(rec: Recipe) -> None:
    mapped = {v.upper() for v in rec.persona_map.values()}
    assert "PPP20063" in mapped  # the respondent's own orientation: a fact about them
    assert not mapped & {"PPP20064", "PPP10212"}  # LGBT contact and activism: left out
    assert not mapped & {"Q1_A", "Q1_B", "Q1_C", "Q2_A", "Q2_B", "Q2_C", "DOV_TESS192"}
