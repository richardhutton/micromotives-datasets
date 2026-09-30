"""The melt, asserted exactly against a hand-computable fixture."""

from __future__ import annotations

from pathlib import Path

from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.recipe import Recipe
from micromotives_datasets.sources import spss


def _rows(fixture_sav: Path, fixture_recipe: Recipe):
    return list(build_rows(spss.read(fixture_sav), fixture_recipe))


def test_row_count_drops_only_the_refused_item(fixture_sav, fixture_recipe) -> None:
    # 4 respondents x 2 items = 8, minus 1 refused = 7.
    # The refusal drops ONE item, not the whole respondent.
    rows = _rows(fixture_sav, fixture_recipe)
    assert len(rows) == 7
    assert len({r.participant_id for r in rows}) == 4


def test_responses_are_recoded_exactly(fixture_sav, fixture_recipe) -> None:
    rows = _rows(fixture_sav, fixture_recipe)
    by_task = {}
    for r in rows:
        by_task.setdefault(r.task_num, []).append(r.response_num)
    assert sorted(by_task[0]) == [-3.0, 0.0, 0.0, 3.0]  # A1: 5,8,2,5
    assert sorted(by_task[1]) == [-1.0, 1.0, 2.0]  # A2: 6,(refused),4,7


def test_condition_mapping_is_taken_from_the_recipe(fixture_sav, fixture_recipe) -> None:
    rows = _rows(fixture_sav, fixture_recipe)
    counts: dict[int, int] = {}
    for r in rows:
        counts[r.condition_num] = counts.get(r.condition_num, 0) + 1
    assert counts == {0: 3, 1: 4}  # respondent 2 refused one item


def test_condition_text_is_shared_context_plus_arm(fixture_sav, fixture_recipe) -> None:
    rows = _rows(fixture_sav, fixture_recipe)
    arm0 = next(r for r in rows if r.condition_num == 0)
    arm1 = next(r for r in rows if r.condition_num == 1)
    assert arm0.condition == 'You read a short profile. It said "good".'
    assert arm1.condition == 'You read a short profile. It said "bad".'
    assert arm0.condition != arm1.condition


def test_outcome_carries_question_and_scale_instruction(fixture_sav, fixture_recipe) -> None:
    rows = _rows(fixture_sav, fixture_recipe)
    r = next(r for r in rows if r.task_num == 0)
    assert r.outcome.startswith("How good?")
    assert 'from -3 to 3 where -3 means "Bad" and 3 means "Good"' in r.outcome


def test_persona_resolves_value_labels(fixture_sav, fixture_recipe) -> None:
    rows = _rows(fixture_sav, fixture_recipe)
    r = min(rows, key=lambda r: int(r.participant_id.split(":")[1]))
    assert r.persona.age == 30
    assert r.persona.sex == "Male"  # 1.0 -> label, not "1"


def test_values_outside_the_declared_scale_are_dropped(
    fixture_sav, fixture_recipe, tmp_path
) -> None:
    """An undeclared code must be dropped, never guessed at."""
    import pandas as pd
    import pyreadstat

    df = pd.DataFrame({"COND": [1.0], "A1": [99.0], "A2": [5.0], "AGE": [30.0], "SEX": [1.0]})
    p = tmp_path / "odd.sav"
    pyreadstat.write_sav(df, str(p))
    rows = list(build_rows(spss.read(p), fixture_recipe))
    assert [r.task_num for r in rows] == [1]  # A1=99 dropped, A2=5 kept


def test_undeclared_arm_is_skipped(fixture_sav, fixture_recipe, tmp_path) -> None:
    import pandas as pd
    import pyreadstat

    df = pd.DataFrame({"COND": [9.0], "A1": [5.0], "A2": [5.0], "AGE": [30.0], "SEX": [1.0]})
    p = tmp_path / "arm9.sav"
    pyreadstat.write_sav(df, str(p))
    assert list(build_rows(spss.read(p), fixture_recipe)) == []


def test_persona_variable_names_are_case_insensitive(fixture_sav, fixture_recipe) -> None:
    """Deposits and recipes disagree about capitalisation; that must not matter.

    A case-sensitive lookup silently dropped the ENTIRE persona of three studies
    — 33 mapped fields across 7,679 rows — because the recipes said `ppincimp`
    and the files said `PPINCIMP`. Persona is one of the four parts of the
    tuple, so those rows were near-useless, and nothing caught it: QC never
    inspected persona and crosscheck does not compare it.
    """
    fixture_recipe.persona_map = {"age": "age", "sex": "SeX"}  # file has AGE / SEX
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    assert rows[0].persona.age is not None
    assert rows[0].persona.sex is not None


def test_mapped_persona_variable_absent_from_data_is_an_error(fixture_sav, fixture_recipe) -> None:
    """Asking for a field and silently getting nothing is the failure mode."""
    import pytest

    fixture_recipe.persona_map = {"age": "AGE", "income": "NOT_A_COLUMN"}
    with pytest.raises(ValueError, match="persona variables not in data"):
        list(build_rows(spss.read(fixture_sav), fixture_recipe))
