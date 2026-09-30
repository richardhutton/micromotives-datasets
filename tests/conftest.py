"""A tiny synthetic study, so the melt can be tested exactly and offline.

Deliberately small enough to reason about by hand:

  4 respondents x 2 arms x 2 outcome items, with one refused answer.
  Codes 2..8 map to -3..+3 (same shape as the real TESS semantic differentials).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyreadstat
import pytest

from micromotives_datasets.recipe import Arm, Condition, Outcome, Recipe, Scale


@pytest.fixture
def fixture_sav(tmp_path: Path) -> Path:
    df = pd.DataFrame(
        {
            "COND": [1.0, 1.0, 2.0, 2.0],
            "A1": [5.0, 8.0, 2.0, 5.0],  # -> 0, 3, -3, 0
            "A2": [6.0, -1.0, 4.0, 7.0],  # -> 1, REFUSED(dropped), -1, 2
            "AGE": [30.0, 41.0, 52.0, 63.0],
            "SEX": [1.0, 2.0, 1.0, 2.0],
        }
    )
    path = tmp_path / "fixture.sav"
    pyreadstat.write_sav(
        df,
        str(path),
        variable_value_labels={
            "COND": {1.0: "Condition A", 2.0: "Condition B"},
            "A1": {-1.0: "Refused", 2.0: "-3", 5.0: "0", 8.0: "+3"},
            "A2": {-1.0: "Refused", 4.0: "-1", 6.0: "+1", 7.0: "+2"},
            "SEX": {1.0: "Male", 2.0: "Female"},
        },
    )
    return path


@pytest.fixture
def fixture_recipe() -> Recipe:
    return Recipe(
        study_id="test01",
        source="tess",
        data_file="fixture.sav",
        condition=Condition(
            source_var="COND",
            shared_context="You read a short profile.",
            factors=["framing"],
            arms=[
                Arm(
                    raw=1, condition_num=0, factors={"framing": "positive"}, text='It said "good".'
                ),
                Arm(raw=2, condition_num=1, factors={"framing": "negative"}, text='It said "bad".'),
            ],
        ),
        outcomes=[
            Outcome(
                var="A1",
                task_num=0,
                question="How good?",
                scale=Scale(min=-3, max=3, min_label="Bad", max_label="Good"),
            ),
            Outcome(
                var="A2",
                task_num=1,
                question="How warm?",
                scale=Scale(min=-3, max=3, min_label="Cold", max_label="Warm"),
            ),
        ],
        response_recode={2: -3, 3: -2, 4: -1, 5: 0, 6: 1, 7: 2, 8: 3},
        missing_codes=[-1],
        persona_map={"age": "AGE", "sex": "SEX"},
    )
