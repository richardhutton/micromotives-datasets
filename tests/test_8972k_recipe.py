"""The 8972k recipe (TESS 136, Behrman: ideal family size, general and personal,
asked in a randomised order), checked on the recipe alone.

Every respondent answered both questions; RND_00 set which came first, and the
opening sentence went on whichever did. So each (arm, task) cell carries its own
condition: the first-asked item sees only the opening sentence, the second-asked
item sees the first screen narrated as asked. These tests pin that structure, so a
hand edit cannot swap a cell, leak the later screen into an earlier one, or drop
the opening sentence. The words themselves are checked against the questionnaire,
and the rows against the deposit, in `test_8972k_answer_key.py`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from micromotives_datasets.recipe import Recipe, load

RECIPE = Path(__file__).resolve().parents[1] / "recipes" / "8972k.yaml"

OPENING = "We would like to ask you your opinions about family size."
GENERAL = "What do you think is the ideal number of children for a family to have?"
PERSONAL = "What would be the ideal number of children for you personally to have (or to have had)?"
OPTIONS = '"0" / "1" / "2" / "3" / "4" / "5" / "6" / "7 or more"'
QUESTION = {0: GENERAL, 1: PERSONAL}
# RND_00 = 0 shows AA1 (task 0, general) first; RND_00 = 1 shows AB1 (task 1) first.
FIRST_TASK = {0: 0, 1: 1}


def narrated(task: int) -> str:
    return f'Earlier in the survey you were asked: "{OPENING} {QUESTION[task]}" {OPTIONS}'


def cell_text(rec: Recipe, raw: int, task: int) -> str:
    arm = next(a for a in rec.condition.arms if a.raw == raw)
    text = arm.items[task].condition_text
    assert text is not None
    return " ".join(text.split())


@pytest.fixture(scope="module")
def rec() -> Recipe:
    return load(RECIPE)


def test_assignment_is_rnd00_with_two_arms(rec: Recipe) -> None:
    assert rec.condition.source_var == "RND_00"
    assert sorted((a.raw, a.condition_num) for a in rec.condition.arms) == [(0, 0), (1, 1)]
    assert "RND_02" in rec.condition.considered_and_rejected


@pytest.mark.parametrize("raw", [0, 1])
def test_first_asked_item_sees_only_the_opening_sentence(rec: Recipe, raw: int) -> None:
    assert cell_text(rec, raw, FIRST_TASK[raw]) == OPENING


@pytest.mark.parametrize("raw", [0, 1])
def test_second_asked_item_narrates_the_first_screen(rec: Recipe, raw: int) -> None:
    first = FIRST_TASK[raw]
    second = 1 - first
    text = cell_text(rec, raw, second)
    assert text == narrated(first)
    # The row's own question is never in its condition: it is the outcome.
    assert QUESTION[second] not in text


@pytest.mark.parametrize("raw", [0, 1])
def test_arm_text_is_the_last_cell(rec: Recipe, raw: int) -> None:
    arm = next(a for a in rec.condition.arms if a.raw == raw)
    assert " ".join(arm.text.split()) == cell_text(rec, raw, 1 - FIRST_TASK[raw])


def test_outcomes_and_scale(rec: Recipe) -> None:
    got = {o.task_num: (o.var, o.question) for o in rec.outcomes}
    assert got == {0: ("BEHRMAN_AA1", GENERAL), 1: ("BEHRMAN_AB1", PERSONAL)}
    for o in rec.outcomes:
        assert (o.scale.min, o.scale.max, o.scale.max_label) == (0, 7, "7 or more")
    # Stored 1..8 with labels "0".."7 or more": the count is the code minus one.
    assert rec.response_recode == {c: c - 1 for c in range(1, 9)}
    assert sorted(rec.missing_codes) == [77, 98, 99]


def test_household_size_top_band_is_not_given_a_number(rec: Recipe) -> None:
    """The top band, "Six or more persons", must never be given an exact count."""
    rewrite = rec.persona_label_rewrite["HHSIZE"]
    assert rewrite == {c: str(c) for c in range(1, 6)}
    assert 6 not in rewrite


def test_no_fertility_answer_in_the_persona(rec: Recipe) -> None:
    """Part B (own children, expected children) is the outcome's own domain."""
    mapped = {v.upper() for v in rec.persona_map.values()}
    assert not mapped & {"BEHRMAN_B1", "BEHRMAN_B2", "BEHRMAN_B3", "BEHRMAN_B4"}
    assert not mapped & {"HH01", "HH25", "HH612", "HH1317"}
