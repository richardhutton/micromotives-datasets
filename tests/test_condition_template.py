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


# --- parts: fragments that agree with a level, for IP 9.18 -------------------

# A name with the pronoun and possessive that must follow it. The bare `{who}`
# stays once-only; the parts repeat.
AGREE: dict = {
    "text": "{who} is old. {who.subj} sees {who.poss} friends {often}.",
    "outcome_questions": {0: "How is {who} doing?", 1: "Is {who.subj} well?"},
    "dimensions": {
        "who": {
            "var": "ff_name",
            "levels": {
                1: {"level": "George", "text": "George", "parts": {"subj": "He", "poss": "his"}},
                2: {"level": "Anne", "text": "Anne", "parts": {"subj": "She", "poss": "her"}},
            },
        },
        "often": {
            "var": "ff_often",
            "levels": {1: {"level": "regularly", "text": "regularly"},
                       2: {"level": "rarely", "text": "rarely"}},
        },
    },
}


def _agree(**over: object) -> recipe.ConditionTemplate:
    return recipe.ConditionTemplate.model_validate(AGREE | over)


def test_parts_follow_their_level_and_may_repeat() -> None:
    arms = _agree().expand()
    assert arms[0].text == "George is old. He sees his friends regularly."
    assert arms[3].text == "Anne is old. She sees her friends rarely."


def test_each_question_is_rendered_from_the_same_cell_for_its_own_task() -> None:
    arms = _agree().expand()
    assert set(arms[3].items) == {0, 1}
    assert arms[3].items[0].outcome_question == "How is Anne doing?"
    assert arms[3].items[1].outcome_question == "Is She well?"
    assert arms[0].items[1].outcome_question == "Is He well?"


def test_a_part_placed_only_in_a_question_counts_as_placed() -> None:
    """9.39's object pronoun ("How do you see her ...") appears in no
    condition text, only in questions."""
    dims = {k: dict(v) for k, v in AGREE["dimensions"].items()}
    dims["who"] = {
        "var": "ff_name",
        "levels": {
            1: {
                "level": "G",
                "text": "George",
                "parts": {"subj": "He", "poss": "his", "obj": "him"},
            },
            2: {
                "level": "A",
                "text": "Anne",
                "parts": {"subj": "She", "poss": "her", "obj": "her"},
            },
        },
    }
    arms = _agree(dimensions=dims, outcome_questions={0: "Do you like {who.obj}?"}).expand()
    assert arms[3].items[0].outcome_question == "Do you like her?"


def test_a_template_without_a_question_adds_no_item_overrides() -> None:
    """The housework template must be untouched by this addition."""
    assert all(not a.items for a in _template().expand())


def test_parts_do_not_relax_the_once_only_rule_for_the_bare_clause() -> None:
    with pytest.raises(ValidationError, match="appears more than once"):
        _agree(text="{who} is old. {who.subj} sees {who.poss} friends {often}. {who}.")


def test_a_part_only_some_levels_declare_is_refused() -> None:
    """The cells lacking it would ship literal braces."""
    dims = {k: dict(v) for k, v in AGREE["dimensions"].items()}
    dims["who"] = {"var": "ff_name", "levels": {
        1: {"level": "George", "text": "George", "parts": {"subj": "He", "poss": "his"}},
        2: {"level": "Anne", "text": "Anne", "parts": {"subj": "She"}},
    }}
    with pytest.raises(ValidationError, match="levels declare different parts"):
        _agree(dimensions=dims)


def test_a_declared_part_never_placed_is_refused() -> None:
    with pytest.raises(ValidationError, match="declared but never placed"):
        _agree(text="{who} is old. {who.subj} sees friends {often}.")


def test_a_part_placeholder_naming_no_part_is_refused() -> None:
    with pytest.raises(ValidationError, match="names a part no level declares"):
        _agree(text="{who} is old. {who.subj} sees {who.poss} {who.obj} friends {often}.")


def test_a_part_placeholder_naming_no_dimension_is_refused() -> None:
    with pytest.raises(ValidationError, match="names no declared dimension"):
        _agree(text="{who} is old. {who.subj} sees {who.poss} friends {often} {x.y}.")


def test_a_question_placeholder_naming_no_dimension_is_refused() -> None:
    with pytest.raises(ValidationError, match="outcome_questions placeholders"):
        _agree(outcome_questions={0: "How is {whom} doing?"})


def test_no_placeholder_survives_into_text_or_question() -> None:
    for arm in _agree().expand():
        rendered = [arm.text] + [i.outcome_question or "" for i in arm.items.values()]
        assert not any("{" in r or "}" in r for r in rendered)


@pytest.mark.parametrize(
    "over",
    [
        {"text": "{who} is old. {who.subj} sees {who.poss} friends {often} {who.subj.x}."},
        {"outcome_questions": {0: "How is {who } doing?"}},
        {"outcome_questions": {0: "How is {who-x} doing?"}},
    ],
)
def test_no_placeholder_shape_survives_expansion(over: dict) -> None:
    """Shapes the placeholder regexes do not parse. Found by the 9.18 checker:
    each validated and shipped literal braces."""
    with pytest.raises((ValidationError, ValueError), match=r"placeholder left|braces"):
        _agree(**over).expand()


def test_a_clause_carrying_a_placeholder_is_refused() -> None:
    """Parts render before clauses, so `{who.subj}` inside a clause would be left
    standing, and `{often}` inside a part would be filled from another dimension."""
    dims = {k: dict(v) for k, v in AGREE["dimensions"].items()}
    dims["often"] = {
        "var": "ff_often",
        "levels": {
            1: {"level": "regularly", "text": "regularly {who.subj}"},
            2: {"level": "rarely", "text": "rarely"},
        },
    }
    with pytest.raises(ValidationError, match="braces in"):
        _agree(dimensions=dims)


def test_a_templated_recipe_must_question_every_outcome() -> None:
    """Found by the 9.39 checker: dropping one task from `outcome_questions`
    validated, built, and passed QC with bracketed fallback wording."""
    import yaml

    path = REPO / "recipes" / "ukds_6849_vig_ageing_w9.yaml"
    data = yaml.safe_load(path.read_text())
    recipe.Recipe.model_validate(data)
    del data["condition"]["template"]["outcome_questions"][2]
    with pytest.raises(ValidationError, match=r"covers no question for task_num \[2\]"):
        recipe.Recipe.model_validate(data)
