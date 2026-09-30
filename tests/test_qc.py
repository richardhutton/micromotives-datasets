"""QC rules. Each test corresponds to a real failure found in SocSci210."""

from __future__ import annotations

import pytest

from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.pipeline.qc import check
from micromotives_datasets.sources import spss


def test_clean_study_passes(fixture_sav, fixture_recipe) -> None:
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rep = check(rows, fixture_recipe)
    assert rep.passed, rep.failures
    assert rep.n_rows == 7
    assert rep.rows_per_condition == {0: 3, 1: 4}


def test_identical_condition_text_is_a_failure(fixture_sav, fixture_recipe) -> None:
    """The `sd7cf` failure: distinct conditions collapsing to one description.

    SocSci210 gave 12 conditions only 3 distinct stimulus strings, silently
    discarding a whole experimental factor. This must fail the build.
    """
    fixture_recipe.condition.arms[1].text = fixture_recipe.condition.arms[0].text
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rep = check(rows, fixture_recipe)
    assert not rep.passed
    assert any("identical text" in f for f in rep.failures)


def test_empty_rows_fail(fixture_recipe) -> None:
    rep = check([], fixture_recipe)
    assert not rep.passed
    assert any("no rows" in f for f in rep.failures)


def test_factor_that_never_changes_the_text_fails(fixture_sav, fixture_recipe) -> None:
    """A declared factor must actually be expressed in the arm text."""
    fixture_recipe.condition.arms[1].text = fixture_recipe.condition.arms[0].text
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rep = check(rows, fixture_recipe)
    assert any("does not change the arm text" in f or "identical text" in f for f in rep.failures)


def _two_factor_recipe(with_phantom: bool = False):
    """A crossed recipe whose text expresses every factor except `phantom`.

    Needed because the shared fixture has one factor and two arms, which cannot
    distinguish a real rule-5 check from a vacuous one. With `with_phantom` the
    grid becomes 2x2x2 so that `phantom` has genuine minimal pairs — arms alike
    in temperature and distance but differing in phantom — whose text is
    necessarily identical, since the text never mentions it.
    """
    import itertools as it

    from micromotives_datasets.recipe import Arm, Condition, Outcome, Recipe, Scale

    factors = ["temperature", "distance"] + (["phantom"] * with_phantom)
    levels = [("warm", "cold"), ("near", "far")] + ([("blond", "brown")] * with_phantom)
    arms = []
    for i, combo in enumerate(it.product(*levels)):
        f = dict(zip(factors, combo, strict=True))
        arms.append(
            Arm(
                raw=i + 1,
                condition_num=i,
                factors=f,
                text=f"The room was {f['temperature']} and {f['distance']}.",
            )
        )
    return Recipe(
        study_id="test02",
        source="tess",
        data_file="fixture.sav",
        condition=Condition(source_var="COND", factors=factors, arms=arms),
        outcomes=[
            Outcome(
                var="A1",
                task_num=0,
                question="How good?",
                scale=Scale(min=-3, max=3, min_label="Bad", max_label="Good"),
            )
        ],
        response_recode={5: 0},
        persona_map={"age": "AGE"},
    )


def _rows_for(recipe):
    """One row per arm — enough for the recipe-level rules."""
    from micromotives_datasets.schema import Persona, Row

    return [
        Row(
            persona=Persona(age=40),
            condition=recipe.condition.render(a),
            outcome="How good?",
            response="0",
            condition_num=a.condition_num,
            task_num=0,
            response_num=0.0,
            participant_id=str(a.raw),
            study_id=recipe.study_id,
            source="tess",
        )
        for a in recipe.condition.arms
    ]


def test_declared_factor_absent_from_all_arm_text_fails() -> None:
    """Rule 5 must not be vacuous.

    The original rule failed only when EVERY arm rendered identically — which
    rule 1 already catches — so a factor that appeared in no arm text at all
    passed. `phantom` varies across arms and is expressed nowhere.
    """
    recipe = _two_factor_recipe(with_phantom=True)
    rep = check(_rows_for(recipe), recipe)
    assert not rep.passed, "a factor absent from every arm text must fail"
    assert any("'phantom'" in f and "does not change the arm text" in f for f in rep.failures)


def test_crossed_factors_both_expressed_passes() -> None:
    """The same 2x2 without the phantom factor is clean."""
    recipe = _two_factor_recipe()
    rep = check(_rows_for(recipe), recipe)
    assert rep.passed, rep.failures


def test_nested_factor_warns_rather_than_failing() -> None:
    """A factor with no minimal pair cannot be tested — say so, don't guess.

    `a5v96` has `cds_recommendation: none` only on the arms with no decision
    aid: heed-vs-defy is undefined when there is no recommendation. That is a
    legitimate augmented factorial, so the rule must neither pass it silently
    nor fail it.
    """
    recipe = _two_factor_recipe()
    # Make `distance` perfectly confounded with `temperature`: no pair of arms
    # now differs in `distance` alone.
    for arm in recipe.condition.arms:
        arm.factors["distance"] = "near" if arm.factors["temperature"] == "warm" else "far"
    rep = check(_rows_for(recipe), recipe)
    assert rep.passed, rep.failures
    assert any("nested, not crossed" in w and "'distance'" in w for w in rep.warnings)


def test_response_outside_declared_scale_fails(fixture_sav, fixture_recipe) -> None:
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rows[0].response_num = 99.0
    rep = check(rows, fixture_recipe)
    assert not rep.passed
    assert any("outside declared scale" in f for f in rep.failures)


@pytest.mark.parametrize("field_", ["condition_num", "task_num"])
def test_duplicate_indices_rejected_by_recipe(fixture_recipe, field_) -> None:
    """Recipe validation catches duplicate canonical indices."""
    from micromotives_datasets.recipe import Recipe

    data = fixture_recipe.model_dump()
    if field_ == "condition_num":
        data["condition"]["arms"][1]["condition_num"] = 0
    else:
        data["outcomes"][1]["task_num"] = 0
    with pytest.raises(ValueError, match="duplicate"):
        Recipe.model_validate(data)


def test_non_monotonic_recode_fails(fixture_sav, fixture_recipe) -> None:
    """A higher band meaning a smaller quantity is a unit or parsing error."""
    fixture_recipe.outcomes[0].response_recode = {2: -3, 3: -2, 4: 99, 5: 0, 6: 1, 7: 2, 8: 3}
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rep = check(rows, fixture_recipe)
    assert not rep.passed
    assert any("changes direction" in f for f in rep.failures)


def test_colliding_bands_fail(fixture_sav, fixture_recipe) -> None:
    """The real SocSci210 defect: '1-4 minutes' and '1-3 hours' both -> 1."""
    fixture_recipe.outcomes[0].response_recode = {2: 1, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 8: 6}
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rep = check(rows, fixture_recipe)
    assert not rep.passed
    assert any("same value" in f for f in rep.failures)


def test_socsci210_zrwjp_time_recode_would_be_rejected() -> None:
    """Regression against the actual defect, using their real mapping.

    Their Q6 map took each band's lower bound at face value, ignoring that bands
    2-6 are minutes and 7-17 are hours. Our QC must reject it.
    """
    from micromotives_datasets.pipeline.qc import _all_recodes

    theirs = {
        1: 0,
        2: 1,
        3: 5,
        4: 10,
        5: 20,
        6: 40,
        7: 1,
        8: 4,
        9: 7,
        10: 10,
        11: 13,
        12: 16,
        13: 19,
        14: 22,
        15: 30,
        16: 40,
        17: 50,
    }
    values = [theirs[k] for k in sorted(theirs)]
    assert values != sorted(values), "should be non-monotonic"
    assert len(set(values)) < len(values), "should contain collisions"
    assert _all_recodes  # the helper is what QC walks


def test_reverse_coded_scale_is_allowed(fixture_sav, fixture_recipe) -> None:
    """A fully reverse-coded scale is legitimate and must not be flagged.

    Reverse-coded Likert items are common; only a MIXED direction (a unit
    switch) is a defect.
    """
    fixture_recipe.outcomes[0].response_recode = {2: 3, 3: 2, 4: 1, 5: 0, 6: -1, 7: -2, 8: -3}
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rep = check(rows, fixture_recipe)
    assert not any("changes direction" in f for f in rep.failures), rep.failures


# ---------------------------------------------------------------------------
# Mutation tests: do the rules FIRE when they should?
#
# Rule 5 was dead for eight studies and we found it by luck, not by testing.
# Every rule below therefore gets a MINIMAL mutation of an otherwise-clean
# study, and each assertion names that rule's own message — because asserting
# only `not rep.passed` is what let rule 5 hide: a crude mutation tripped
# rule 1 as well, so the suite went green while rule 5 checked nothing.
# ---------------------------------------------------------------------------


def _fails(rep, needle: str) -> bool:
    return any(needle in f for f in rep.failures)


def _warns(rep, needle: str) -> bool:
    return any(needle in w for w in rep.warnings)


def test_clean_study_raises_no_warnings_either(fixture_sav, fixture_recipe) -> None:
    """A clean study must be silent, not merely passing.

    A rule that warns spuriously is nearly as bad as one that never fires: it
    trains us to ignore the warning column.
    """
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rep = check(rows, fixture_recipe)
    assert rep.passed, rep.failures
    assert rep.warnings == [], rep.warnings


def test_rule2_rows_in_an_undeclared_arm_fail(fixture_sav, fixture_recipe) -> None:
    """Rule 2: a condition_num the recipe never declared means the melt and the
    recipe disagree about the design."""
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rows[0].condition_num = 77
    rep = check(rows, fixture_recipe)
    assert _fails(rep, "rows in undeclared arms"), rep.failures


def test_rule2_declared_arm_with_no_rows_warns(fixture_sav, fixture_recipe) -> None:
    """Rule 2, other direction: an arm nobody was assigned to.

    A warning rather than a failure — small studies legitimately have empty
    cells — but it must be said out loud, because the usual cause is a wrong
    `raw` code silently matching nothing.
    """
    from micromotives_datasets.recipe import Arm

    fixture_recipe.condition.arms.append(
        Arm(raw=99, condition_num=2, factors={"framing": "neutral"}, text='It said "meh".')
    )
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rep = check(rows, fixture_recipe)
    assert _warns(rep, "declared arms with no rows"), rep.warnings
    assert "[2]" in " ".join(rep.warnings)


def test_rule3_declared_outcome_with_no_rows_warns(fixture_sav, fixture_recipe) -> None:
    """Rule 3: an outcome that produced nothing — usually a wrong variable name."""
    rows = [r for r in build_rows(spss.read(fixture_sav), fixture_recipe) if r.task_num != 1]
    rep = check(rows, fixture_recipe)
    assert _warns(rep, "declared outcomes with no rows"), rep.warnings


def test_rule6_empty_condition_text_fails(fixture_sav, fixture_recipe) -> None:
    """Rule 6: blank stimulus text. The row would train on nothing."""
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rows[0].condition = "   \n  "
    rep = check(rows, fixture_recipe)
    assert _fails(rep, "empty condition text"), rep.failures


def test_rule8_two_bands_collapsing_to_one_value_fails(fixture_sav, fixture_recipe) -> None:
    """Rule 8: the `zrwjp` defect — "1-4 minutes" and "1-3 hours" both to 1.

    A 60x error that made two bands indistinguishable. Distinct source bands
    must stay distinct.
    """
    fixture_recipe.outcomes[0].response_recode = {2: -3, 3: -2, 4: -1, 5: -1, 6: 1, 7: 2, 8: 3}
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rep = check(rows, fixture_recipe)
    assert _fails(rep, "maps distinct bands to the same value"), rep.failures
    assert "4" in " ".join(rep.failures) and "5" in " ".join(rep.failures)


def test_rule7_accepts_a_legitimately_reversed_scale(fixture_sav, fixture_recipe) -> None:
    """Rule 7 must NOT fire on a reverse-coded scale.

    Reverse coding is extremely common and legitimate; only a MIXED direction
    indicates a unit switch or parsing error. A rule that rejected reversal
    would push us to "fix" correct recipes.
    """
    fixture_recipe.outcomes[0].response_recode = {2: 3, 3: 2, 4: 1, 5: 0, 6: -1, 7: -2, 8: -3}
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rep = check(rows, fixture_recipe)
    assert not _fails(rep, "changes direction"), rep.failures


def test_rule5_catches_an_unexpressed_factor_in_an_arm_with_no_rows() -> None:
    """Where rule 5 is genuinely independent of rule 1.

    Rule 1 inspects the text of BUILT ROWS, so an arm nobody was assigned to is
    invisible to it. Rule 5 inspects the recipe's arms, so it still catches an
    unexpressed factor there. This is the case that justifies keeping both.
    """
    recipe = _two_factor_recipe(with_phantom=True)
    # The minimal pairs on `phantom` are condition_nums (0,1), (2,3), (4,5), (6,7).
    # Drop ONE arm from each pair, so no two surviving arms share text and rule 1
    # really is blind — while all eight arms remain in the recipe for rule 5.
    rows = [r for r in _rows_for(recipe) if r.condition_num % 2 == 0]
    rep = check(rows, recipe)
    assert not _fails(rep, "render identical text"), "rule 1 should be blind here"
    assert _fails(rep, "does not change the arm text"), rep.failures
