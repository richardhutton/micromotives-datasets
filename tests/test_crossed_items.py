"""Designs where arms are CROSSED with items, rather than being items.

Two shapes, and between them they are what blocks roughly 60,000 rows in four
studies that are already built, checked and verified:

**Arm x item overrides.** `evnyh` holds its answers in 60 columns, one per
(item x arm). `Arm.outcome_var` can only name one variable for the whole arm, so
nine of its ten items were unreachable. `cug34` and `z358z` need two outcomes of
the same arm to carry different question text, and `Arm.outcome_question` applies
to all of them.

**Per-item assignment.** `b87sm` showed each respondent eight vignettes drawn
without replacement from a universe of 72, recording which appeared in slot k in
its own variable `P_S{k}`. One arm per respondent can only build one slot, and
seven eighths of the vignette observations sat outside the schema.

The tests that matter most here are the two about LEAKAGE, because that is the
failure this layer is most likely to cause: an override must reach the cell it
names and no other. An arm-level scale leaking onto an outcome with its own
variable cost `evnyh` 8,774 rows an answer instruction their own responses
contradicted, and QC was silent throughout.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pandas as pd
import pyreadstat
import pytest
from pydantic import ValidationError

from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.recipe import Arm, Condition, ItemOverride, Outcome, Recipe, Scale
from micromotives_datasets.sources import spss


def _scale(lo: int = 1, hi: int = 5) -> Scale:
    return Scale(min=lo, max=hi, min_label="Low", max_label="High")


# --------------------------------------------------------------------------
# arm x item overrides
# --------------------------------------------------------------------------


@pytest.fixture
def crossed_sav(tmp_path: Path) -> Path:
    """2 arms x 2 items, each cell in its OWN column — `evnyh`'s shape.

    Respondents 1-2 are in arm 1 and answered A1_1 / A1_2; respondents 3-4 are
    in arm 2 and answered A2_1 / A2_2. Every column is present for everyone, so
    a test that passes can only be reading the right one by resolution, not by
    luck.
    """
    df = pd.DataFrame(
        {
            "ASSIGN": [1.0, 1.0, 2.0, 2.0],
            "A1_1": [1.0, 2.0, 9.0, 9.0],
            "A1_2": [3.0, 4.0, 9.0, 9.0],
            "A2_1": [9.0, 9.0, 5.0, 4.0],
            "A2_2": [9.0, 9.0, 3.0, 2.0],
            "AGE": [30.0, 40.0, 50.0, 60.0],
        }
    )
    p = tmp_path / "crossed.sav"
    pyreadstat.write_sav(df, str(p))
    return p


def _crossed_recipe(**arm_kwargs: object) -> Recipe:
    return Recipe(
        study_id="cross01",
        source="tess",
        data_file="crossed.sav",
        condition=Condition(
            source_var="ASSIGN",
            factors=["framing"],
            arms=[
                Arm(
                    raw=1,
                    condition_num=0,
                    factors={"framing": "gain"},
                    text="Framed as a gain.",
                    items={
                        0: ItemOverride(outcome_var="A1_1"),
                        1: ItemOverride(outcome_var="A1_2"),
                    },
                ),
                Arm(
                    raw=2,
                    condition_num=1,
                    factors={"framing": "loss"},
                    text="Framed as a loss.",
                    items={
                        0: ItemOverride(outcome_var="A2_1"),
                        1: ItemOverride(outcome_var="A2_2"),
                    },
                    **arm_kwargs,  # type: ignore[arg-type]
                ),
            ],
        ),
        outcomes=[
            Outcome(task_num=0, question="How good?", scale=_scale()),
            Outcome(task_num=1, question="How warm?", scale=_scale()),
        ],
        response_recode={1: 1, 2: 2, 3: 3, 4: 4, 5: 5},
        missing_codes=[9],
        persona_map={"age": "AGE"},
    )


def test_each_arm_item_cell_reads_its_own_variable(crossed_sav: Path) -> None:
    """The whole point: 2 arms x 2 items = 4 live cells, not 2.

    Under the old schema only `Arm.outcome_var` existed, so an arm could name
    one variable and the second item of every arm was lost.
    """
    rows = list(build_rows(spss.read(crossed_sav), _crossed_recipe()))
    assert len(rows) == 8  # 4 respondents x 2 items
    assert Counter((r.condition_num, r.task_num) for r in rows) == {
        (0, 0): 2,
        (0, 1): 2,
        (1, 0): 2,
        (1, 1): 2,
    }
    # The values prove which column was read: arm 1 item 0 is A1_1 = 1,2 and
    # arm 1 item 1 is A1_2 = 3,4. Reading the wrong column would still yield
    # eight rows, so the count alone proves nothing.
    cells = {(r.condition_num, r.task_num) for r in rows}
    got = {
        key: sorted(r.response_num for r in rows if (r.condition_num, r.task_num) == key)
        for key in cells
    }
    assert got[(0, 0)] == [1.0, 2.0]
    assert got[(0, 1)] == [3.0, 4.0]
    assert got[(1, 0)] == [4.0, 5.0]
    assert got[(1, 1)] == [2.0, 3.0]


def test_item_override_beats_the_arm_wide_one(crossed_sav: Path) -> None:
    """An arm may carry both; the one naming the task wins.

    `arm.outcome_var="NOPE"` is a column that does not exist, so if the blanket
    value were ever preferred the build would raise rather than quietly differ —
    the assertion is that it does not raise AND reads the item's column.
    """
    rows = list(build_rows(spss.read(crossed_sav), _crossed_recipe(outcome_var="NOPE")))
    arm1 = [r for r in rows if r.condition_num == 1]
    assert sorted(r.response_num for r in arm1 if r.task_num == 0) == [4.0, 5.0]


def test_item_scale_reaches_an_outcome_that_names_its_own_variable(crossed_sav: Path) -> None:
    """The leak test, in the direction that must work.

    `scale_for` deliberately refuses an ARM-level scale when the outcome names
    its own `var`, because the arm is then not supplying the item. An ITEM-level
    scale has named the task, so that guard must not apply to it — otherwise the
    override is unusable in exactly the designs it exists for.
    """
    rec = _crossed_recipe()
    rec.outcomes[0].var = "A1_1"  # the outcome now names a variable itself
    rec.condition.arms[0].items[0] = ItemOverride(scale=Scale(min=0, max=10, nominal=False))
    text = rec.outcome_text_for(rec.outcomes[0], rec.condition.arms[0])
    assert "from 0 to 10" in text
    # ... and the other item of the same arm is untouched.
    other = rec.outcome_text_for(rec.outcomes[1], rec.condition.arms[0])
    assert "from 1 to 5" in other


def test_arm_scale_still_does_not_leak_onto_an_outcome_with_its_own_var(crossed_sav: Path) -> None:
    """The same leak test in the direction that must keep failing.

    This is ledger #44 — 8,774 rows of `evnyh`, 47.3% of the study, rendered
    "return an integer from 1 to 5" over responses that ran 0-7. Adding the item
    layer must not reopen it.
    """
    rec = _crossed_recipe()
    rec.outcomes[0].var = "A1_1"
    rec.condition.arms[0].scale = Scale(min=0, max=10)
    rec.condition.arms[0].items = {}
    assert "from 1 to 5" in rec.outcome_text_for(rec.outcomes[0], rec.condition.arms[0])


def test_item_question_and_recode_win(crossed_sav: Path) -> None:
    rec = _crossed_recipe()
    rec.condition.arms[0].outcome_question = "Arm-wide wording?"
    rec.condition.arms[0].response_recode = {1: 100, 2: 200, 3: 300, 4: 400, 5: 500}
    rec.condition.arms[0].items[0] = ItemOverride(
        outcome_var="A1_1",
        outcome_question="Item wording?",
        response_recode={1: 11, 2: 22, 3: 33, 4: 44, 5: 55},
    )
    arm = rec.condition.arms[0]
    assert rec.outcome_text_for(rec.outcomes[0], arm).startswith("Item wording?")
    assert rec.recode_for(arm, rec.outcomes[0]) == {1: 11, 2: 22, 3: 33, 4: 44, 5: 55}
    # Item 1 has no override of its own, so it falls back to the arm's.
    assert rec.outcome_text_for(rec.outcomes[1], arm).startswith("Arm-wide wording?")
    assert rec.recode_for(arm, rec.outcomes[1])[1] == 100


def test_item_override_for_an_undeclared_task_is_rejected() -> None:
    """A typo'd key must not read as a live override.

    Ignoring it silently would leave the blanket arm-level value in force while
    the recipe, in review, looks as though it had been overridden.
    """
    rec = _crossed_recipe().model_dump()
    rec["condition"]["arms"][0]["items"][7] = {"outcome_var": "A1_1"}
    with pytest.raises(ValidationError, match="task_num \\[7\\]"):
        Recipe.model_validate(rec)


# --------------------------------------------------------------------------
# per-item assignment (within-subject vignettes)
# --------------------------------------------------------------------------


@pytest.fixture
def slots_sav(tmp_path: Path) -> Path:
    """`b87sm`'s shape in miniature: 3 arms, 2 presentation slots.

    Respondent 3 has no slot-1 assignment, which is the case that decides
    whether a within-subject design may drop a whole respondent.
    """
    df = pd.DataFrame(
        {
            "P_S1": [1.0, 2.0, float("nan"), 3.0],
            "P_S2": [2.0, 3.0, 1.0, 1.0],
            "SCEN_1": [4.0, 5.0, 3.0, 2.0],
            "SCEN_2": [3.0, 2.0, 5.0, 4.0],
            "AGE": [30.0, 40.0, 50.0, 60.0],
        }
    )
    p = tmp_path / "slots.sav"
    pyreadstat.write_sav(df, str(p))
    return p


def _slots_recipe() -> Recipe:
    return Recipe(
        study_id="slot01",
        source="tess",
        data_file="slots.sav",
        condition=Condition(
            source_var="P_S1",
            factors=["vignette"],
            arms=[
                Arm(raw=1, condition_num=0, factors={"vignette": "a"}, text="Vignette A."),
                Arm(raw=2, condition_num=1, factors={"vignette": "b"}, text="Vignette B."),
                Arm(raw=3, condition_num=2, factors={"vignette": "c"}, text="Vignette C."),
            ],
        ),
        outcomes=[
            Outcome(
                var="SCEN_1",
                task_num=0,
                question="Slot 1 — how willing?",
                scale=_scale(),
                condition_var="P_S1",
            ),
            Outcome(
                var="SCEN_2",
                task_num=1,
                question="Slot 2 — how willing?",
                scale=_scale(),
                condition_var="P_S2",
            ),
        ],
        response_recode={1: 1, 2: 2, 3: 3, 4: 4, 5: 5},
        persona_map={"age": "AGE"},
    )


def test_each_item_takes_its_own_arm(slots_sav: Path) -> None:
    """The same respondent appears in different arms for different items.

    That is what a within-subject vignette design IS, and the old schema could
    not express it: `Condition.source_var` resolved one arm per respondent, so
    slot 2 was built with slot 1's vignette text or not at all.
    """
    rows = list(build_rows(spss.read(slots_sav), _slots_recipe()))
    by_participant: dict[str, dict[int, int]] = {}
    for r in rows:
        by_participant.setdefault(r.participant_id, {})[r.task_num] = r.condition_num
    # Respondent 0 saw vignette 1 in slot 1 and vignette 2 in slot 2.
    first = by_participant["slot01:0"]
    assert first == {0: 0, 1: 1}
    # And the condition TEXT follows the arm, not the respondent.
    slot2 = next(r for r in rows if r.participant_id == "slot01:0" and r.task_num == 1)
    assert slot2.condition == "Vignette B."


def test_a_respondent_missing_one_slot_still_contributes_the_others(slots_sav: Path) -> None:
    """Respondent 2 has no slot-1 vignette but did answer slot 2.

    A between-subjects build skips a respondent whose assignment is blank, which
    is right when there is one assignment. Here it would discard every item they
    DID answer — in `b87sm` that is up to seven vignettes per person.
    """
    rows = list(build_rows(spss.read(slots_sav), _slots_recipe()))
    theirs = [r for r in rows if r.participant_id == "slot01:2"]
    assert [r.task_num for r in theirs] == [1]
    assert theirs[0].condition == "Vignette A."  # P_S2 = 1


def test_declaring_both_condition_var_and_vars_is_rejected() -> None:
    rec = _slots_recipe().model_dump()
    rec["outcomes"][0]["condition_vars"] = ["P_S1"]
    with pytest.raises(ValidationError, match="declares both"):
        Recipe.model_validate(rec)


def test_a_per_item_assignment_of_the_wrong_width_is_rejected() -> None:
    """Arms are keyed by a tuple, so a width mismatch could never match.

    Failing loudly beats building zero rows for that item and leaving someone to
    work out why. A different ORDER of the same width is the worse case — it
    matches the WRONG arm — and cannot be caught here, which is why the field's
    description states the requirement.
    """
    rec = _slots_recipe().model_dump()
    rec["outcomes"][0]["condition_var"] = None
    rec["outcomes"][0]["condition_vars"] = ["P_S1", "P_S2"]
    with pytest.raises(ValidationError, match="would never match"):
        Recipe.model_validate(rec)


def test_a_study_with_no_per_item_assignment_is_unaffected(fixture_sav, fixture_recipe) -> None:
    """The ordinary case must not pay for this, in behaviour or in rows."""
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    assert len(rows) == 7  # 4 respondents x 2 items, less one refusal
