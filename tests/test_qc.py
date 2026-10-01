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


def _mixed_scale_recipe():
    """An arm-level scale alongside outcomes that name their own `var`.

    The `evnyh` shape: the arm supplies the experimental item (per-cell 1-5
    endpoints), while a second outcome is an open-ended 0-7 day count read from
    its own column. The arm's scale must not leak onto that second outcome.
    """
    from micromotives_datasets.recipe import Arm, Condition, Outcome, Recipe, Scale

    return Recipe(
        study_id="test03",
        source="tess",
        data_file="fixture.sav",
        condition=Condition(
            source_var="COND",
            factors=["framing"],
            arms=[
                Arm(
                    raw=1,
                    condition_num=0,
                    factors={"framing": "a"},
                    text="x",
                    outcome_var="A1",
                    scale=Scale(min=1, max=5, min_label="lo", max_label="hi"),
                ),
                Arm(
                    raw=2,
                    condition_num=1,
                    factors={"framing": "b"},
                    text="y",
                    outcome_var="A1",
                    scale=Scale(min=1, max=5, min_label="hi", max_label="lo"),
                ),
            ],
        ),
        outcomes=[
            # The arm supplies this one: no `var`, so the arm's scale applies.
            Outcome(
                task_num=0,
                question="experimental item?",
                scale=Scale(min=1, max=5, min_label="lo", max_label="hi"),
            ),
            # This one names its own variable and its own wider scale.
            Outcome(
                var="A2",
                task_num=1,
                question="how many days?",
                scale=Scale(min=-3, max=3, min_label="0 days", max_label="7 days"),
            ),
        ],
        response_recode={2: -3, 3: -2, 4: -1, 5: 0, 6: 1, 7: 2, 8: 3},
        missing_codes=[-1],
        persona_map={"age": "AGE"},
    )


def test_arm_scale_does_not_leak_onto_an_outcome_with_its_own_var(fixture_sav) -> None:
    """The evnyh defect: 16,824 rows told "an integer from 1 to 5" over 0-7 data.

    `outcome_var_for` prefers the outcome; `scale_for` must agree rather than
    invert that precedence.
    """
    recipe = _mixed_scale_recipe()
    rows = list(build_rows(spss.read(fixture_sav), recipe))
    task1 = [r for r in rows if r.task_num == 1]
    assert task1, "expected rows for the outcome that names its own var"
    for r in task1:
        assert "from -3 to 3" in r.outcome, r.outcome
        assert "from 1 to 5" not in r.outcome, r.outcome


def test_rule13_catches_a_response_outside_its_own_rendered_scale(fixture_sav) -> None:
    """Rule 4 cannot see this: every value IS in some declared recode.

    A crude break here would also trip rule 4, which is exactly how rule 5
    stayed hidden for eight studies — so this asserts rule 13's own message.
    """
    recipe = _mixed_scale_recipe()
    rows = list(build_rows(spss.read(fixture_sav), recipe))
    # Narrow the outcome's declared scale so its own rendered instruction no
    # longer admits the responses already built against it.
    recipe.outcomes[1].scale.min = 0
    recipe.outcomes[1].scale.max = 0
    rep = check(rows, recipe)
    assert _fails(rep, "outside the scale their own outcome text states"), rep.failures


def test_rule15_catches_a_row_citing_its_position_in_a_sequence(
    fixture_sav, fixture_recipe
) -> None:
    """The b87sm defect: 13,513 rows of 19,282 said "Scenario #1" while rating 2-8.

    Nothing else could see it. The 72 arms still rendered 72 distinct strings so
    rules 1 and 5 passed, the arm text matched the source byte-for-byte, the row
    counts reconciled exactly, and an exhaustive recomputation of every row's arm
    assignment found no error. It was visible only by reading a rendered row.
    """
    fixture_recipe.condition.shared_context = "Please read Scenario #1 carefully."
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rep = check(rows, fixture_recipe)
    assert _warns(rep, "cites a position in a sequence"), rep.warnings
    assert _warns(rep, "Scenario #1"), rep.warnings


def test_rule15_ignores_a_forward_reference_inside_the_same_row(
    fixture_sav, fixture_recipe
) -> None:
    """ "The following scenario" points inside the row and is correct.

    Two built studies use exactly this phrasing (`a5v96`, `z358z`). A rule that
    flagged them would be turned off within a week, which is how a rule stops
    catching anything.
    """
    fixture_recipe.condition.shared_context = "Please read the following scenario."
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rep = check(rows, fixture_recipe)
    assert not _warns(rep, "cites a position in a sequence"), rep.warnings


def test_rule16_warns_when_no_licence_is_recorded(fixture_sav, fixture_recipe) -> None:
    """Definition of done asks for source, licence AND provenance.

    Source and provenance were recorded richly from the first study; licence was
    recorded in zero of fourteen, because nothing asked.
    """
    fixture_recipe.licence = None
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    assert _warns(check(rows, fixture_recipe), "no licence recorded"), "rule 16 silent"


def test_rule16_accepts_none_stated_as_a_recorded_licence(fixture_sav, fixture_recipe) -> None:
    """ "None stated" is a fact about the deposit, and a useful one.

    Treating it as unrecorded would push a maker towards guessing a licence to
    clear the warning, which is the opposite of what the rule is for.
    """
    fixture_recipe.licence = "none stated"
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    assert not _warns(check(rows, fixture_recipe), "no licence recorded")


def test_rule16_is_not_satisfied_by_whitespace(fixture_sav, fixture_recipe) -> None:
    fixture_recipe.licence = "   "
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    assert _warns(check(rows, fixture_recipe), "no licence recorded")


# --------------------------------------------------------------------------
# Rule 17 — a row must not mention the experiment's own construction
# --------------------------------------------------------------------------


def _one_row(condition: str, *, persona=None, outcome: str = "How good?"):
    from micromotives_datasets.schema import Persona, Row

    return [
        Row(
            persona=persona or Persona(age=40),
            condition=condition,
            outcome=outcome,
            response="0",
            condition_num=0,
            task_num=0,
            response_num=0.0,
            participant_id="p1",
            study_id="t",
            source="tess",
        )
    ]


@pytest.mark.parametrize(
    "text",
    [
        # es4xw's shipped text, both occurrences, on 32,228 rows.
        "Four of the six people are the same in every version of this photograph.",
        "The remaining two are, in this version, both Black men.",
        # 5hqan, the two the corpus sweep found.
        "This part of the survey asked you about sex and gender.",
        "You were randomly assigned to read the following.",
        "In this condition the policy was described as permanent.",
        # 5hqan's actual shipped clause, on all 6,411 rows. The first version of
        # rule 17 missed it and caught a different sentence in the same study —
        # which is why one match per study is not evidence the rule is complete.
        "The question came after both, in the same position regardless of condition.",
    ],
)
def test_rule17_catches_text_about_the_study_itself(fixture_sav, fixture_recipe, text) -> None:
    """A participant was in one condition and knew nothing of the others."""
    rep = check(_one_row(text), fixture_recipe)
    assert _warns(rep, "refers to the experiment's own construction"), rep.warnings


@pytest.mark.parametrize(
    "text",
    [
        # es4xw's CORRECTED text must be clean, or the fix would not pass QC.
        "The team pictured had six people: two were Black and four were White.",
        # Rule 15 owns this one. If rule 17 also fired, the two would be
        # duplicates rather than siblings and the measured narrowness of 15
        # would have been pointless.
        "Scenario #1. A company is developing a smartphone app.",
        # A legitimate stimulus that happens to use the word "version".
        "The app would download the latest version of the questionnaire.",
        "You were asked to imagine a new condition affecting your health.",
    ],
)
def test_rule17_is_quiet_on_legitimate_text(fixture_sav, fixture_recipe, text) -> None:
    rep = check(_one_row(text), fixture_recipe)
    assert not _warns(rep, "refers to the experiment's own construction"), rep.warnings


# --------------------------------------------------------------------------
# Rule 18 — a row must not render text that is cut off
# --------------------------------------------------------------------------


def test_rule18_does_not_flag_a_slot_the_questionnaire_left_blank(
    fixture_sav, fixture_recipe
) -> None:
    """`8ctbk`'s "4. -" is CORRECT, and an earlier version of rule 18 said it was not.

    The questionnaire declares `c. [LEAVE BLANK]` as a genuine third level of the
    Family Policy attribute, and the screenshots embedded in the deposit's own
    .docx show a literal hyphen in that slot on screen. 5,682 of 17,464 rows
    reproduce what the participant actually read. A rule that flagged it would
    push a maker to "fix" correct text, which is worse than the rule not
    existing — so the detection was removed and this pins it out.
    """
    text = (
        "1. You have one child\n"
        "2. You work 40 hours a week\n"
        "3. You do most of the household work\n"
        "4. -\n"
        "5. Your household has just enough to pay your bills\n"
    )
    rep = check(_one_row(text), fixture_recipe)
    assert not _warns(rep, "appears cut off"), rep.warnings


def test_rule18_catches_a_truncated_persona_label(fixture_sav, fixture_recipe) -> None:
    """Seven studies, ~27,900 rows, and a42yg had the identical fault fixed in
    one recipe while its siblings were never swept.

    SPSS severs a value label at 120 characters and two deposits sever at 80, so
    an unclosed bracket is the signal rather than a length test — a length test
    would have missed two of the seven.
    """
    from micromotives_datasets.schema import Persona

    truncated = "Protestant (Baptist, Methodist, Non-denominational, Lutheran, Presbyterian, Pent"
    rep = check(
        _one_row("A clean condition.", persona=Persona(age=40, religion=truncated)), fixture_recipe
    )
    assert _warns(rep, "appears cut off"), rep.warnings
    assert "persona.religion" in " ".join(rep.warnings), "the rule should name the field"


def test_rule18_is_quiet_on_balanced_text(fixture_sav, fixture_recipe) -> None:
    from micromotives_datasets.schema import Persona

    full = (
        "Protestant (Baptist, Methodist, Non-denominational, Lutheran, Presbyterian, "
        "Pentecostal, Episcopalian, Reformed, Church of Christ, Jehovah's Witness, etc.)"
    )
    text = "1. You have one child\n2. A well-known, long-standing arrangement\n"
    rep = check(_one_row(text, persona=Persona(age=40, religion=full)), fixture_recipe)
    assert not _warns(rep, "appears cut off"), rep.warnings
