"""Recipe loading and validation, including the real 7jt2f recipe."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from micromotives_datasets import recipe as recipe_mod
from micromotives_datasets.recipe import Arm, Condition, Outcome, Recipe, Scale

REPO = Path(__file__).resolve().parents[1]


def test_scale_instruction() -> None:
    s = recipe_mod.Scale(min=-3, max=3, min_label="Bad", max_label="Good")
    assert s.instruction() == (
        'Only return an integer from -3 to 3 where -3 means "Bad" and 3 means "Good", nothing else.'
    )


def test_scale_without_labels() -> None:
    assert (
        recipe_mod.Scale(min=1, max=7).instruction()
        == "Only return an integer from 1 to 7, nothing else."
    )


def test_arm_missing_a_declared_factor_is_rejected(fixture_recipe) -> None:
    data = fixture_recipe.model_dump()
    data["condition"]["arms"][0]["factors"] = {}
    with pytest.raises(ValueError, match="missing factor"):
        recipe_mod.Recipe.model_validate(data)


def test_duplicate_raw_arm_rejected(fixture_recipe) -> None:
    data = fixture_recipe.model_dump()
    data["condition"]["arms"][1]["raw"] = 1
    with pytest.raises(ValueError, match="duplicate raw"):
        recipe_mod.Recipe.model_validate(data)


def test_real_7jt2f_recipe_loads_and_is_well_formed() -> None:
    rec = recipe_mod.load(REPO / "recipes" / "7jt2f.yaml")
    assert rec.study_id == "7jt2f"
    # 2 x 4 design: 8 arms, two declared factors.
    assert len(rec.condition.arms) == 8
    assert set(rec.condition.factors) == {"label", "self_introduction"}
    # Mapping is declared explicitly, and here happens to be raw-1.
    assert {a.raw: a.condition_num for a in rec.condition.arms} == {
        1: 0,
        2: 1,
        3: 2,
        4: 3,
        5: 4,
        6: 5,
        7: 6,
        8: 7,
    }
    # Five outcome items (Q7 deliberately excluded).
    assert [o.var for o in rec.outcomes] == ["Q2", "Q3", "Q4", "Q5", "Q6"]
    # The recode is the explicit map, not arithmetic.
    assert rec.response_recode == {2: -3, 3: -2, 4: -1, 5: 0, 6: 1, 7: 2, 8: 3}


def test_7jt2f_arms_have_distinct_text() -> None:
    """All eight arms must be distinguishable — the invariant SocSci210 broke."""
    rec = recipe_mod.load(REPO / "recipes" / "7jt2f.yaml")
    rendered = [rec.condition.render(a) for a in rec.condition.arms]
    assert len(set(rendered)) == 8


def test_7jt2f_self_introduction_factor_matches_the_questionnaire() -> None:
    """Arms 1-4 saw the self-introduction; arms 5-8 did not.

    This is the fact SocSci210 inverted, so it is pinned down here.
    """
    rec = recipe_mod.load(REPO / "recipes" / "7jt2f.yaml")
    by_raw = {a.raw: a for a in rec.condition.arms}
    for raw in (1, 2, 3, 4):
        assert by_raw[raw].factors["self_introduction"] == "present"
        assert "self-introduction" in by_raw[raw].text
    for raw in (5, 6, 7, 8):
        assert by_raw[raw].factors["self_introduction"] == "absent"
        assert "only by the label" in by_raw[raw].text


def test_recode_resolution_order_is_arm_then_outcome_then_study(fixture_recipe) -> None:
    """Arm beats outcome beats study (recipe.recode_for)."""
    arm = fixture_recipe.condition.arms[0]
    outcome = fixture_recipe.outcomes[0]
    assert fixture_recipe.recode_for(arm, outcome) == fixture_recipe.response_recode

    outcome.response_recode = {1: 100}
    assert fixture_recipe.recode_for(arm, outcome) == {1: 100}

    arm.response_recode = {1: 200}
    assert fixture_recipe.recode_for(arm, outcome) == {1: 200}


def test_real_zrwjp_recipe_uses_per_outcome_scales() -> None:
    rec = recipe_mod.load(REPO / "recipes" / "zrwjp.yaml")
    dollars, minutes = rec.outcomes[0], rec.outcomes[1]
    assert dollars.var == "Q5" and minutes.var == "Q6"
    # Dollars: band lower bounds, including the band SocSci210 mis-parsed as 1.
    assert dollars.response_recode is not None
    assert dollars.response_recode[16] == 1001
    # Time: everything in minutes, so sub-hour and hour bands cannot collide.
    assert minutes.response_recode is not None
    assert minutes.response_recode[2] == 1  # "1-4 minutes"
    assert minutes.response_recode[7] == 60  # "1-3 hours"
    assert minutes.response_recode[2] != minutes.response_recode[7]
    # Monotonic: a higher band must never mean less time.
    vals = [minutes.response_recode[b] for b in range(1, 18)]
    assert vals == sorted(vals)
    # We knowingly disagree with SocSci210 here.
    assert rec.comparable_to_socsci210 is False


def test_assignment_split_across_two_variables(fixture_recipe) -> None:
    """A 2x2 randomised through one variable per factor, not a combined code.

    z358z holds scenario in XTESS175 and consent alternative in DOV_OPTION;
    there is no single four-level assignment variable in the file.
    """
    data = fixture_recipe.model_dump()
    data["condition"]["source_var"] = None
    data["condition"]["source_vars"] = ["A", "B"]
    data["condition"]["factors"] = ["framing", "consent"]
    for i, (arm, a, b) in enumerate(zip(data["condition"]["arms"], (1, 1), (1, 2), strict=False)):
        arm["raw"] = None
        arm["raw_values"] = {"A": a, "B": b}
        arm["condition_num"] = i
        arm["factors"] = {"framing": "x", "consent": f"opt{b}"}
    rec = recipe_mod.Recipe.model_validate(data)
    assert rec.condition.variables == ["A", "B"]
    assert set(rec.condition.by_raw()) == {(1, 1), (1, 2)}


def test_duplicate_composite_key_rejected(fixture_recipe) -> None:
    data = fixture_recipe.model_dump()
    data["condition"]["source_var"] = None
    data["condition"]["source_vars"] = ["A", "B"]
    data["condition"]["factors"] = []
    for arm in data["condition"]["arms"]:
        arm["raw"] = None
        arm["raw_values"] = {"A": 1, "B": 1}  # identical -> must be rejected
        arm["factors"] = {}
    with pytest.raises(ValueError, match="duplicate"):
        recipe_mod.Recipe.model_validate(data)


def test_arm_missing_a_source_variable_rejected(fixture_recipe) -> None:
    data = fixture_recipe.model_dump()
    data["condition"]["source_var"] = None
    data["condition"]["source_vars"] = ["A", "B"]
    data["condition"]["factors"] = []
    for arm in data["condition"]["arms"]:
        arm["raw"] = None
        arm["raw_values"] = {"A": 1}  # B missing
        arm["factors"] = {}
    with pytest.raises(ValueError, match="missing raw_values"):
        recipe_mod.Recipe.model_validate(data)


def test_nominal_scale_renders_no_endpoints() -> None:
    """An unordered choice must not be given poles.

    `cug34`'s B09 codes are "they each pay half" / "Michelle pays all" /
    "Anthony pays all". Naming 1 and 3 as the endpoints implies Michelle-pays-all
    lies between them, when it is the opposite pole of the gender dimension the
    item measures.
    """
    from micromotives_datasets.recipe import Scale

    s = Scale(min=1, max=3, nominal=True)
    assert s.instruction() == "Only return one of 1, 2 or 3, nothing else."
    assert "from 1 to 3" not in s.instruction()


def test_nominal_scale_rejects_endpoint_labels() -> None:
    """The flag and the labels are contradictory, so the recipe must not load."""
    import pytest

    from micromotives_datasets.recipe import Scale

    with pytest.raises(ValueError, match="nominal scale must not carry"):
        Scale(min=1, max=3, nominal=True, min_label="a", max_label="b")


def test_ordinal_scale_keeps_its_endpoints() -> None:
    from micromotives_datasets.recipe import Scale

    s = Scale(min=-3, max=3, min_label="Bad", max_label="Good")
    assert 'from -3 to 3 where -3 means "Bad" and 3 means "Good"' in s.instruction()


# --------------------------------------------------------------------------
# Arm.raws — several source codes denoting one condition
# --------------------------------------------------------------------------


def _arm_recipe(arms: list[Arm]) -> dict[str, object]:
    return {
        "study_id": "t",
        "source": "tess",
        "data_file": "s.sav",
        "condition": Condition(source_var="X", arms=arms),
        "outcomes": [
            Outcome(
                var="Y",
                task_num=0,
                question="q",
                scale=Scale(min=1, max=2, min_label="lo", max_label="hi"),
            )
        ],
        "response_recode": {1: 1, 2: 2},
        "persona_map": {"age": "AGE"},
    }


def test_several_raw_codes_can_denote_one_condition() -> None:
    """`a2nbf` randomised question wording x a follow-up item, 2x2.

    The follow-up was administered after every scored outcome, so for the rows
    we build it had not happened — codes 1 and 2 are one condition and 3 and 4
    are another. Without this the recipe must either keep four arms whose text
    is identical in pairs (rule 1 fails, a manipulation looks lost) or describe
    a follow-up the participant had not yet reached.
    """
    r = Recipe.model_validate(
        _arm_recipe(
            [
                Arm(raws=[1, 2], condition_num=0, text="baby wording"),
                Arm(raws=[3, 4], condition_num=1, text="fetus wording"),
            ]
        )
    )
    by_raw = r.condition.by_raw()
    assert set(by_raw) == {(1,), (2,), (3,), (4,)}
    assert by_raw[(1,)] is by_raw[(2,)], "both codes must resolve to the same arm"
    assert by_raw[(3,)].condition_num == 1


def test_a_code_claimed_by_two_arms_is_still_caught() -> None:
    """The duplicate check must see every code, not one key per arm.

    Expanding `raws` into the key list is what keeps this an error; building one
    key per arm would let two arms both claim code 2 and never notice.
    """
    with pytest.raises(ValidationError, match="duplicate raw arm code"):
        Recipe.model_validate(
            _arm_recipe(
                [
                    Arm(raws=[1, 2], condition_num=0, text="a"),
                    Arm(raws=[2, 3], condition_num=1, text="b"),
                ]
            )
        )


def test_an_arm_may_not_declare_both_raw_and_raws() -> None:
    with pytest.raises(ValidationError, match="both `raw` and `raws`"):
        Recipe.model_validate(
            _arm_recipe(
                [
                    Arm(raw=1, raws=[1, 2], condition_num=0, text="a"),
                    Arm(raw=3, condition_num=1, text="b"),
                ]
            )
        )


def test_an_arm_with_neither_raw_nor_raws_is_rejected() -> None:
    with pytest.raises(ValidationError, match="needs `raw` or `raws`"):
        Recipe.model_validate(
            _arm_recipe(
                [
                    Arm(condition_num=0, text="a"),
                    Arm(raw=3, condition_num=1, text="b"),
                ]
            )
        )


# --------------------------------------------------------------------------
# line_order_vars — the instrument randomised which order its lines appeared in
# --------------------------------------------------------------------------


def test_lines_are_rendered_in_the_order_this_respondent_saw() -> None:
    """`8ctbk` randomised its six attribute rows per respondent.

    654 of the 720 possible orders occur across 1,794 respondents, and exactly
    ONE respondent saw the order the recipe used to render for everybody — so
    17,463 of 17,464 rows stated an order nobody had seen.
    """
    text = "1. first\n2. second\n3. third"
    # This respondent saw them third, first, second.
    assert Condition.reorder_lines(text, [3, 1, 2]) == "1. second\n2. third\n3. first"


def test_the_declared_order_renders_unchanged() -> None:
    text = "1. first\n2. second\n3. third"
    assert Condition.reorder_lines(text, [1, 2, 3]) == text


def test_an_order_that_is_not_a_permutation_is_refused() -> None:
    """Silently rendering a partial order would be worse than failing.

    A duplicate position means one line would overwrite another and one slot
    would stay empty, producing a profile the respondent never saw — the exact
    class of defect this field exists to remove.
    """
    with pytest.raises(ValueError, match="not a permutation"):
        Condition.reorder_lines("1. a\n2. b\n3. c", [1, 1, 3])


def test_a_mismatched_width_is_refused() -> None:
    with pytest.raises(ValueError, match="3 positions for 2 lines"):
        Condition.reorder_lines("1. a\n2. b", [1, 2, 3])


def test_existing_numbers_are_replaced_not_kept() -> None:
    """The number a line carries in the recipe is its DECLARED position.

    Keeping it would render "1. second" as "2. second" in slot 1 — a row whose
    own numbering contradicts its order.
    """
    out = Condition.reorder_lines("1. alpha\n2. beta", [2, 1])
    assert out == "1. beta\n2. alpha"
    assert "2. beta" not in out
