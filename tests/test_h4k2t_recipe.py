"""The h4k2t recipe (TESS 125, Connors: a feminist described as a man or a woman,
talking about feminist issues frequently or rarely, very active or not), checked
on the recipe alone.

The arm text and CONNORS5's arm-filled wording are both keyed to P_CONNORS, so
these tests pin that each arm's words say what its factors say, in both places,
and that the partisanship guess (CONNORS6) stays out by ruling. The words
themselves are checked against the questionnaire, and the rows against the
deposit, in `test_h4k2t_answer_key.py`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from micromotives_datasets.recipe import Recipe, load

RECIPE = Path(__file__).resolve().parents[1] / "recipes" / "h4k2t.yaml"

OPTIONS = " (1) More likely; (2) Less likely; (3) The same."

# P_CONNORS -> (person, talks, activity), as the questionnaire keys them.
DESIGN = {
    1: ("man", "frequently", "very active"),
    2: ("woman", "frequently", "very active"),
    3: ("man", "rarely", "very active"),
    4: ("woman", "rarely", "very active"),
    5: ("man", "frequently", "not very active"),
    6: ("woman", "frequently", "not very active"),
    7: ("man", "rarely", "not very active"),
    8: ("woman", "rarely", "not very active"),
}


def flat(s: str) -> str:
    return " ".join(s.split())


@pytest.fixture(scope="module")
def rec() -> Recipe:
    return load(RECIPE)


def test_assignment_and_factors(rec: Recipe) -> None:
    assert rec.condition.source_var == "P_CONNORS"
    assert sorted((a.raw, a.condition_num) for a in rec.condition.arms) == [
        (r, r - 1) for r in range(1, 9)
    ]
    for arm in rec.condition.arms:
        assert arm.raw is not None
        person, talks, activity = DESIGN[arm.raw]
        assert arm.factors == {"person": person, "talks": talks, "activity": activity}


@pytest.mark.parametrize("raw", range(1, 9))
def test_arm_text_says_what_its_factors_say(rec: Recipe, raw: int) -> None:
    arm = next(a for a in rec.condition.arms if a.raw == raw)
    person, talks, activity = DESIGN[raw]
    text = flat(arm.text)
    pron = "himself" if person == "man" else "herself"
    assert text.startswith(f"This person is a {person} who considers {pron} to be a feminist.")
    assert f"{talks} talks about feminist issues" in text
    if activity == "very active":
        assert "is very active" in text and "often working with groups" in text
        assert "not very active" not in text
    else:
        assert "is not very active" in text and "never working with groups" in text


@pytest.mark.parametrize("raw", range(1, 9))
def test_counterfactual_wording_is_filled_per_arm(rec: Recipe, raw: int) -> None:
    arm = next(a for a in rec.condition.arms if a.raw == raw)
    _, talks, activity = DESIGN[raw]
    # The questionnaire's fills: and/but agrees with whether the two clauses agree.
    conj = "and" if (talks == "frequently") == (activity == "very active") else "but"
    q = arm.items[3].outcome_question
    assert q is not None
    assert flat(q) == (
        f"If most feminists {talks} talked about feminist issues {conj} were "
        f"{activity} in working towards gender equality (like the individual "
        "described previously), would you be more or less likely to identify as a "
        "feminist?" + OPTIONS
    )


def test_template_question_is_never_rendered(rec: Recipe) -> None:
    task3 = next(o for o in rec.outcomes if o.task_num == 3)
    for arm in rec.condition.arms:
        rendered = rec.outcome_text_for(task3, arm)
        assert "[" not in rendered and "/" not in rendered.split("?")[0]


def test_outcomes_scales_and_codes(rec: Recipe) -> None:
    got = {o.task_num: o.var for o in rec.outcomes}
    assert got == {0: "CONNORS2", 1: "CONNORS3", 2: "CONNORS4", 3: "CONNORS5"}
    by = {o.task_num: o for o in rec.outcomes}
    for t in (0, 1):
        assert (by[t].scale.min, by[t].scale.max) == (0, 100)
        assert by[t].response_recode == {v: v for v in range(101)}
    assert by[2].scale.min_label == "Yes, definitely" and by[2].scale.max_label == "No"
    assert by[3].scale.nominal
    # 77/98/99 are real thermometer values and must never be a study-wide missing code.
    assert sorted(rec.missing_codes) == [777, 998, 999]
    for t in (2, 3):
        rc = by[t].response_recode
        assert rc is not None and set(rc) == {1, 2, 3}


def test_partisanship_guess_is_not_built(rec: Recipe) -> None:
    """rich, 23 Nov 2026: CONNORS6 (Democrat/Republican guess) is dropped for the UK set."""
    assert "CONNORS6" not in {o.var for o in rec.outcomes}
    assert "CONNORS6" not in {v.upper() for v in rec.persona_map.values()}
    for arm in rec.condition.arms:
        assert "Democrat" not in arm.text and "Republican" not in arm.text


def test_household_size_top_band_is_not_given_a_number(rec: Recipe) -> None:
    rewrite = rec.persona_label_rewrite["HHSIZE"]
    assert rewrite == {c: str(c) for c in range(1, 6)}
