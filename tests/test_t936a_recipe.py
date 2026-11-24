"""The two t936a recipes (TESS2 053, Schnettler), checked on the recipes alone.

Every respondent read two vignettes, each with its own eight-cell assignment
(XVIGN1, XVIGN2), so the deposit is two experiments. These tests pin the
structure a hand edit could break without any count moving: the arm numbering,
the 2 x 2 x 2 factors, the child named in each V1 question, the scales, and the
two scope decisions (recall checks not built, section order not a factor). The
words themselves are checked against the questionnaire, and the rows against the
deposit and SocSci210, in `test_t936a_answer_key.py`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from micromotives_datasets.recipe import Recipe, load

RECIPES = Path(__file__).resolve().parents[1] / "recipes"


@pytest.fixture(scope="module")
def feeding() -> Recipe:
    return load(RECIPES / "t936a_feeding.yaml")


@pytest.fixture(scope="module")
def time() -> Recipe:
    return load(RECIPES / "t936a_time.yaml")


def test_two_experiments_one_assignment_each(feeding: Recipe, time: Recipe) -> None:
    assert (feeding.experiment, feeding.condition.source_var) == ("feeding", "XVIGN1")
    assert (time.experiment, time.condition.source_var) == ("time", "XVIGN2")
    assert "XVIGN2" in feeding.condition.considered_and_rejected
    assert "XVIGN1" in time.condition.considered_and_rejected
    for rec in (feeding, time):
        assert [(a.raw, a.condition_num) for a in rec.condition.arms] == [
            (k, k - 1) for k in range(1, 9)
        ]
        # The section rotation is recorded as rejected, never smuggled in as a factor.
        assert "Order_V1V2_1st" in rec.condition.considered_and_rejected
        assert all("order" not in f for f in rec.condition.factors if "birth" not in f)


def test_birth_order_is_codes_1_to_4_against_5_to_8(feeding: Recipe, time: Recipe) -> None:
    for a in feeding.condition.arms:
        assert a.factors["nursed_child_birth_order"] == ("first" if a.raw <= 4 else "second")
    for a in time.condition.arms:
        want = "first-born" if a.raw <= 4 else "second-born"
        assert a.factors["low_weight_child_birth_order"] == want


def test_v1_questions_name_the_formula_fed_child(feeding: Recipe) -> None:
    name = {"daughter": "Caroline", "son": "Bob"}
    for a in feeding.condition.arms:
        child = name[a.factors["formula_fed_child"]]
        assert sorted(a.items) == [0, 1, 2]
        for item in a.items.values():
            assert item.outcome_question is not None
            assert item.outcome_question.endswith(f"formula-feed {child}?")
    # The outcome's own wording keeps the bracket, so a missing override fails QC.
    for o in feeding.outcomes[:3]:
        assert "[Caroline/Bob]" in o.question


def test_outcomes_scales_and_codes(feeding: Recipe, time: Recipe) -> None:
    assert [o.var for o in feeding.outcomes] == ["QV11", "QV12", "QV13", "QV15"]
    assert [o.var for o in time.outcomes] == ["QV21", "QV22", "QV23", "QV25"]
    for rec in (feeding, time):
        assert [o.task_num for o in rec.outcomes] == [0, 1, 2, 3]
        assert rec.response_recode == {c: c - 6 for c in range(1, 12)}
        assert rec.missing_codes == [-1]
        # Recall checks (QV14, QV24) are not outcomes.
        assert not {o.var for o in rec.outcomes} & {"QV14", "QV24"}
    qv25 = time.outcomes[3]
    assert (qv25.scale.min, qv25.scale.max) == (0, 10)
    assert qv25.response_recode == {c: c - 1 for c in range(1, 12)}
    assert feeding.outcomes[0].scale.max_label == "Very Favorable"  # as printed, Q 498
