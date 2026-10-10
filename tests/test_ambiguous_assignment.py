"""A coded assignment can still be ambiguous.

The assignment column names one condition, but a web survey's back button can
re-assign, and the answer to the abandoned condition stays in the file. DEL's
Feb 2023 sandbox has exactly one such respondent: assigned to condition 1, with
page timings and answers on both condition 1's question and condition 5's. Their
answer to condition 1 may have been given after seeing condition 5, so they have
no single condition, and the tuple this corpus is made of needs exactly one.

The melt detects this only through a variable just ONE arm was asked, counts it
against the recipe's declared `ambiguous_routing`, and drops the respondent.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyreadstat
import pytest

from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.recipe import Arm, Condition, Outcome, Recipe, Scale
from micromotives_datasets.sources import spss

DK = 6  # a non-answer code, declared in missing_codes


def _recipe(ambiguous: int = 0, *, check: bool = True) -> Recipe:
    return Recipe(
        study_id="amb01",
        source="dataverse",
        data_file="f.sav",
        licence="synthetic test fixture",
        condition=Condition(
            source_var="SPLIT",
            routing_check=check,
            ambiguous_routing=ambiguous,
            ambiguous_routing_reason="respondent 3 answered both conditions" if ambiguous else None,
            arms=[
                Arm(raw=1, condition_num=0, text="A development policy.", outcome_var="Q1"),
                Arm(
                    raw=2, condition_num=1, text="A feminist development policy.", outcome_var="Q2"
                ),
            ],
        ),
        outcomes=[Outcome(task_num=0, question="Support or oppose?", scale=Scale(min=1, max=5))],
        response_recode={k: k for k in range(1, 6)},
        missing_codes=[DK],
    )


def _data(tmp_path: Path, rows: list[tuple[float, float, float]]) -> spss.Dataset:
    path = tmp_path / "f.sav"
    pyreadstat.write_sav(pd.DataFrame(rows, columns=["SPLIT", "Q1", "Q2"]), str(path))
    return spss.read(path)


NAN = float("nan")


def test_an_answer_under_another_arms_own_question_drops_the_respondent(tmp_path: Path) -> None:
    ds = _data(tmp_path, [(1, 2, NAN), (2, NAN, 4), (1, 1, 3)])
    rows = list(build_rows(ds, _recipe(ambiguous=1)))
    assert len(rows) == 2, "the respondent with answers in both conditions is dropped"
    assert sorted(r.condition_num for r in rows) == [0, 1]


def test_an_undeclared_second_condition_stops_the_build(tmp_path: Path) -> None:
    """Silently keeping the assigned arm would ship a row whose condition is uncertain."""
    ds = _data(tmp_path, [(1, 2, NAN), (2, NAN, 4), (1, 1, 3)])
    with pytest.raises(ValueError, match="ambiguous_routing=0"):
        list(build_rows(ds, _recipe(ambiguous=0)))


def test_a_dont_know_under_another_arm_still_counts_as_being_asked(tmp_path: Path) -> None:
    """A recorded non-answer means the question was put to them. Only a blank means
    it was not, so "Don't know" in the other arm's variable is a second condition."""
    ds = _data(tmp_path, [(1, 2, NAN), (2, NAN, 4), (1, 1, DK)])
    with pytest.raises(ValueError, match="ambiguous_routing=0"):
        list(build_rows(ds, _recipe(ambiguous=0)))
    assert len(list(build_rows(ds, _recipe(ambiguous=1)))) == 2


def test_without_the_check_the_assigned_arm_is_kept(tmp_path: Path) -> None:
    """Off by default: the Innovation Panel codes 'not asked' as negative numbers, and
    reading those as answers would discard thousands of respondents."""
    ds = _data(tmp_path, [(1, 2, NAN), (2, NAN, 4), (1, 1, -8)])
    assert len(list(build_rows(ds, _recipe(ambiguous=0, check=False)))) == 3


def test_a_declared_count_without_the_check_is_refused() -> None:
    with pytest.raises(ValueError, match="routing_check: true"):
        _recipe(ambiguous=1, check=False)


def test_a_numeric_person_id_is_written_without_a_decimal(tmp_path: Path) -> None:
    """SPSS reads a numeric id as a float; "123.0" and "123" would be two people."""
    path = tmp_path / "f.sav"
    pyreadstat.write_sav(
        pd.DataFrame({"SPLIT": [1.0], "Q1": [2.0], "Q2": [NAN], "PID": [120615074968.0]}),
        str(path),
    )
    rec = _recipe().model_copy(update={"participant_id_var": "PID"})
    (row,) = build_rows(spss.read(path), rec)
    assert row.participant_id == "amb01:120615074968"
