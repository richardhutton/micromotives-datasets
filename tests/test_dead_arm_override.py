"""An arm-level outcome override that can never apply is refused.

`scale_for` and `outcome_text_for` apply an arm's `outcome_question` and `scale`
only to an outcome with no `var` of its own (the evnyh guard). Where every
outcome names its `var`, the arm's wording is dead: 9.34's first draft put each
cell's filled question on its arm, and every row shipped the outcome's
placeholder question instead, with QC passing. The validator now refuses it.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyreadstat
import pytest

from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.pipeline.qc import check
from micromotives_datasets.recipe import Arm, Condition, ItemOverride, Outcome, Recipe, Scale
from micromotives_datasets.schema import Row
from micromotives_datasets.sources import spss

SCALE = Scale(min=1, max=3)


def _recipe(*, outcome_var: str | None, arm_question: bool, item_question: bool) -> Recipe:
    def arm(raw: int) -> Arm:
        return Arm(
            raw=raw,
            condition_num=raw - 1,
            text=f"Cell {raw}.",
            outcome_question=f"Question for cell {raw}?" if arm_question else None,
            outcome_var=None if outcome_var else f"Q{raw}",
            items=(
                {0: ItemOverride(outcome_question=f"Question for cell {raw}?")}
                if item_question
                else {}
            ),
        )

    return Recipe(
        study_id="dead01",
        source="dataverse",
        data_file="f.sav",
        licence="synthetic test fixture",
        condition=Condition(source_var="SPLIT", arms=[arm(1), arm(2)]),
        outcomes=[
            Outcome(var=outcome_var, task_num=0, question="[placeholder]", scale=SCALE),
        ],
        response_recode={1: 1, 2: 2, 3: 3},
    )


def test_arm_question_is_refused_when_the_outcome_names_its_var() -> None:
    with pytest.raises(ValueError, match="would never apply"):
        _recipe(outcome_var="Q", arm_question=True, item_question=False)


def test_arm_question_applies_when_the_arm_supplies_the_item() -> None:
    r = _recipe(outcome_var=None, arm_question=True, item_question=False)
    arm = r.condition.arms[1]
    assert r.outcome_text_for(r.outcomes[0], arm).startswith("Question for cell 2?")


def test_item_question_applies_when_the_outcome_names_its_var() -> None:
    r = _recipe(outcome_var="Q", arm_question=False, item_question=True)
    arm = r.condition.arms[0]
    assert r.outcome_text_for(r.outcomes[0], arm).startswith("Question for cell 1?")


def _built(tmp_path: Path, question: str) -> tuple[list[Row], Recipe]:
    rec = _recipe(outcome_var="Q", arm_question=False, item_question=False)
    rec = rec.model_copy(
        update={"outcomes": [rec.outcomes[0].model_copy(update={"question": question})]}
    )
    path = tmp_path / "f.sav"
    pyreadstat.write_sav(pd.DataFrame({"SPLIT": [1.0, 2.0], "Q": [1.0, 3.0]}), str(path))
    return list(build_rows(spss.read(path), rec)), rec


def test_a_placeholder_reaching_a_row_fails_qc(tmp_path: Path) -> None:
    rows, rec = _built(tmp_path, "[the question, in the cell's own wording]")
    assert any("bracketed placeholder" in f for f in check(rows, rec).failures)


def test_an_ordinary_question_passes_the_placeholder_rule(tmp_path: Path) -> None:
    rows, rec = _built(tmp_path, "Would you spend more, the same or less?")
    assert not any("bracketed placeholder" in f for f in check(rows, rec).failures)
