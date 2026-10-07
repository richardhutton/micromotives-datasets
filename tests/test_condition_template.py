"""A templated factorial condition, and the panel-stable participant id.

`Condition.template` exists because IP `9.10` crosses 4 x 3 x 4 x 5 x 2 = 480
arms and `9xw67` already showed where writing that product into YAML leads:
455,919 lines nobody reviewed. The judgment in a factorial is the dimension list
and the clause wording; the product is arithmetic. So the tests here are about
the two things that can go wrong when arithmetic replaces a table -- the
expansion being wrong, and the expansion being SILENTLY wrong because something
else in the recipe contradicts it.

`Recipe.participant_id_var` exists because a panel wave is its own file, so the
row index makes the same person two unrelated participants and loses the
wave-on-wave link, which is the whole reason a panel is worth building.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from micromotives_datasets import recipe

REPO = Path(__file__).resolve().parents[1]

# A 2 x 3 toy: small enough to check every cell by hand, big enough that the
# odometer order is observable (a square would hide a transposition).
TOY: dict = {
    "text": "You {work} and {pay}",
    "dimensions": {
        "work": {
            "var": "ff_work",
            "levels": {1: {"level": "full", "text": "work full time"},
                       2: {"level": "part", "text": "work part time"}},
        },
        "pay": {
            "var": "ff_pay",
            "levels": {1: {"level": "low", "text": "are paid less"},
                       2: {"level": "same", "text": "are paid the same"},
                       3: {"level": "high", "text": "are paid more"}},
        },
    },
}


def _template(**over: object) -> recipe.ConditionTemplate:
    return recipe.ConditionTemplate.model_validate(TOY | over)


def _condition(**over: object) -> recipe.Condition:
    return recipe.Condition.model_validate({"template": TOY} | over)


# --- the expansion ----------------------------------------------------------


def test_the_product_is_every_cell_exactly_once() -> None:
    arms = _template().expand()
    assert len(arms) == 6
    keys = [tuple(sorted(a.raw_values.items())) for a in arms if a.raw_values]
    assert len(set(keys)) == 6


def test_condition_num_is_the_declared_odometer() -> None:
    """Dimensions in declared order, LAST one fastest. A transposition would
    still give 0..5, so the test pins which cell each number names."""
    arms = _template().expand()
    assert [a.condition_num for a in arms] == [0, 1, 2, 3, 4, 5]
    assert [a.raw_values for a in arms] == [
        {"ff_work": 1, "ff_pay": 1},
        {"ff_work": 1, "ff_pay": 2},
        {"ff_work": 1, "ff_pay": 3},
        {"ff_work": 2, "ff_pay": 1},
        {"ff_work": 2, "ff_pay": 2},
        {"ff_work": 2, "ff_pay": 3},
    ]


def test_each_arm_carries_its_level_names_and_its_rendered_text() -> None:
    arms = _template().expand()
    assert arms[2].factors == {"work": "full", "pay": "high"}
    assert arms[2].text == "You work full time and are paid more"
    assert arms[3].factors == {"work": "part", "pay": "low"}
    assert arms[3].text == "You work part time and are paid less"


def test_no_placeholder_survives_into_the_text() -> None:
    """Bracket notation reaching the corpus as stimulus text is the failure this
    whole mechanism has to avoid."""
    for arm in _template().expand():
        assert "{" not in arm.text and "}" not in arm.text


# --- what must be refused ---------------------------------------------------


def test_a_dimension_with_no_placeholder_is_refused() -> None:
    """It would be randomised but never shown: the rows would claim a factor the
    respondent could not have read."""
    with pytest.raises(ValidationError, match="do not match declared dimensions"):
        _template(text="You {work}")


def test_a_placeholder_with_no_dimension_is_refused() -> None:
    with pytest.raises(ValidationError, match="do not match declared dimensions"):
        _template(text="You {work} and {pay} and {help}")


def test_a_dimension_used_twice_is_refused() -> None:
    with pytest.raises(ValidationError, match="appears more than once"):
        _template(text="You {work} and {pay}, and {work}")


def test_two_dimensions_sharing_a_variable_are_refused() -> None:
    """Their levels would collide: one code cannot mean two things at once."""
    clash = {k: dict(v) for k, v in TOY["dimensions"].items()}
    clash["pay"]["var"] = "ff_work"
    with pytest.raises(ValidationError, match="share one variable"):
        _template(dimensions=clash)


def test_a_dimension_with_no_levels_is_refused() -> None:
    with pytest.raises(ValidationError, match="declares no levels"):
        _template(dimensions={"work": {"var": "ff_work", "levels": {}},
                              "pay": TOY["dimensions"]["pay"]})


def test_arms_and_a_template_together_are_refused() -> None:
    """The expansion would replace the written arms with no sign it had."""
    arm = {"raw": 1, "condition_num": 0, "text": "something"}
    with pytest.raises(ValidationError, match="both `arms` and `template`"):
        _condition(arms=[arm])


def test_neither_arms_nor_a_template_is_refused() -> None:
    with pytest.raises(ValidationError, match="neither `arms` nor `template`"):
        recipe.Condition.model_validate({"arms": []})


def test_source_vars_in_a_different_order_are_refused() -> None:
    """`by_raw` keys arms on this order, so a mismatch looks up the wrong cell
    and returns a real arm -- it does not fail. That is why it is refused here."""
    with pytest.raises(ValidationError, match="in the same order"):
        _condition(source_vars=["ff_pay", "ff_work"])


def test_a_single_source_var_with_a_template_is_refused() -> None:
    with pytest.raises(ValidationError, match="use `source_vars`"):
        _condition(source_var="ff_work")


def test_factors_in_a_different_order_are_refused() -> None:
    with pytest.raises(ValidationError, match="do not match the template's dimensions"):
        _condition(factors=["pay", "work"])


def test_the_template_fills_in_source_vars_and_factors() -> None:
    cond = _condition()
    assert cond.source_vars == ["ff_work", "ff_pay"]
    assert cond.factors == ["work", "pay"]
    assert cond.key_for({"ff_work": 2, "ff_pay": 3}) == (2, 3)
    assert cond.by_raw()[(2, 3)].condition_num == 5


# --- the schema addition must be inert for every study that does not use it --


def test_every_existing_recipe_still_loads() -> None:
    """`arms` went from required to optional and `Condition` gained a validator.
    A study that declares arms must be untouched by both."""
    paths = sorted((REPO / "recipes").glob("*.yaml"))
    assert len(paths) > 20, "recipes directory looks wrong"
    for path in paths:
        rec = recipe.load(path)
        assert rec.condition.arms, f"{path.name} loaded with no arms"
