"""Split-ballot designs: per-arm outcome variables and per-arm answer coding.

In a question-wording experiment the question IS the treatment, so each arm is
asked a different variable — and in an option-order experiment the answer codes
are reversed between arms, meaning raw code 1 denotes opposite things. Applying
one global recode would silently invert half the answers.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pandas as pd
import pyreadstat
import pytest

from micromotives_datasets import recipe as recipe_mod
from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.sources import spss

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def ballot_sav(tmp_path: Path) -> Path:
    """4 respondents: two in arm 1 (normal codes), two in arm 2 (reversed)."""
    df = pd.DataFrame(
        {
            "ASSIGN": [1.0, 1.0, 2.0, 2.0],
            "Qa": [1.0, 2.0, float("nan"), float("nan")],
            "Qb": [float("nan"), float("nan"), 1.0, 2.0],
            "AGE": [30.0, 40.0, 50.0, 60.0],
        }
    )
    p = tmp_path / "ballot.sav"
    pyreadstat.write_sav(df, str(p))
    return p


@pytest.fixture
def ballot_recipe() -> recipe_mod.Recipe:
    return recipe_mod.Recipe(
        study_id="ballot",
        source="tess",
        data_file="ballot.sav",
        condition=recipe_mod.Condition(
            source_var="ASSIGN",
            factors=["order"],
            arms=[
                recipe_mod.Arm(
                    raw=1,
                    condition_num=0,
                    factors={"order": "A first"},
                    outcome_var="Qa",
                    response_recode={1: 1, 2: 2},
                    text="Asked with A listed first.",
                ),
                recipe_mod.Arm(
                    raw=2,
                    condition_num=1,
                    factors={"order": "B first"},
                    outcome_var="Qb",
                    response_recode={1: 2, 2: 1},  # reversed
                    text="Asked with B listed first.",
                ),
            ],
        ),
        outcomes=[
            recipe_mod.Outcome(
                task_num=0,
                question="Which is nearer right?",
                scale=recipe_mod.Scale(min=1, max=2, min_label="A", max_label="B"),
            )
        ],
        response_recode={1: 1, 2: 2},
        persona_map={"age": "AGE"},
    )


def test_each_arm_reads_its_own_variable(ballot_sav, ballot_recipe) -> None:
    rows = list(build_rows(spss.read(ballot_sav), ballot_recipe))
    assert len(rows) == 4  # everyone answered exactly one of Qa/Qb
    assert Counter(r.condition_num for r in rows) == {0: 2, 1: 2}


def test_reversed_arm_is_flipped_to_the_canonical_coding(ballot_sav, ballot_recipe) -> None:
    """The failure this guards: applying one recode would give {1: 2, 2: 2}."""
    rows = list(build_rows(spss.read(ballot_sav), ballot_recipe))
    # Arm 1 raw (1,2) -> (1,2). Arm 2 raw (1,2) -> (2,1). Canonical totals balance.
    assert Counter(int(r.response_num) for r in rows) == {1: 2, 2: 2}
    arm2 = sorted((r for r in rows if r.condition_num == 1), key=lambda r: int(r.participant_id))
    assert [int(r.response_num) for r in arm2] == [2, 1]  # flipped, not passed through


def test_outcome_without_var_requires_every_arm_to_supply_one(ballot_recipe) -> None:
    data = ballot_recipe.model_dump()
    data["condition"]["arms"][0]["outcome_var"] = None
    with pytest.raises(ValueError, match="no `var`"):
        recipe_mod.Recipe.model_validate(data)


def test_real_rpw4u_ro1_recipe() -> None:
    rec = recipe_mod.load(REPO / "recipes" / "rpw4u_RO1.yaml")
    assert rec.experiment == "RO1"
    # Scope differs from SocSci210's, so it must not be numerically crosschecked.
    assert rec.comparable_to_socsci210 is False
    # Arms b and d present their options in the opposite order.
    by_raw = {a.raw: a for a in rec.condition.arms}
    assert by_raw[1].response_recode == {1: 1, 2: 2}
    assert by_raw[2].response_recode == {1: 2, 2: 1}
    assert by_raw[4].response_recode == {1: 2, 2: 1}
    # Each arm is asked its own variable.
    assert [by_raw[i].outcome_var for i in (1, 2, 3, 4)] == ["RO1a", "RO1b", "RO1c", "RO1d"]
    # All four wordings are distinct — the signal SocSci210 collapsed.
    assert len({rec.condition.render(a) for a in rec.condition.arms}) == 4
