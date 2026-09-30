"""Rule 9 — detect a second randomisation the recipe didn't declare.

Ledger #33: `z358z` is a 2x2 randomised through two separate variables with no
combined code in the file, so declaring only one silently dropped a whole factor
from the stimulus text. Nothing in the pipeline could notice; an agent happened
to. These tests pin the detector that makes it mechanical.

The screen must be both sensitive (catch a real second factor) and quiet (a
naive sweep for randomisation-looking variables returns over a thousand hits
across the corpus, dominated by item-order variables). Both properties are
tested, because a detector that cried wolf would be turned off.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyreadstat
import pytest

from micromotives_datasets.pipeline.screen import find_undeclared_assignment
from micromotives_datasets.recipe import Arm, Condition, Outcome, Recipe, Scale
from micromotives_datasets.sources import spss


def _write(tmp_path: Path, df: pd.DataFrame, labels: dict[str, str]) -> spss.Dataset:
    path = tmp_path / "s.sav"
    pyreadstat.write_sav(df, str(path), column_labels=labels)
    return spss.read(path)


def _recipe(source_vars: list[str], rejected: dict[str, str] | None = None) -> Recipe:
    return Recipe(
        study_id="t",
        source="tess",
        data_file="s.sav",
        condition=Condition(
            source_vars=source_vars,
            considered_and_rejected=rejected or {},
            arms=[
                Arm(raw_values=dict.fromkeys(source_vars, 1), condition_num=0, text="a"),
                Arm(raw_values=dict.fromkeys(source_vars, 2), condition_num=1, text="b"),
            ],
        ),
        outcomes=[
            Outcome(
                var="Y",
                task_num=0,
                question="q",
                scale=Scale(min=1, max=2, min_label="lo", max_label="hi"),
            )
        ],
        response_recode={1: 1, 2: 2},
        persona_map={"age": "AGE"},
    )


# A 2x2 fully crossed through two variables — the z358z shape. 40 respondents,
# 10 per cell, so every cell is populated and balanced.
CROSSED = pd.DataFrame(
    {
        "XTESS175": [1.0] * 20 + [2.0] * 20,
        "DOV_OPTION": ([1.0] * 10 + [2.0] * 10) * 2,
        "Y": [1.0, 2.0] * 20,
        "AGE": [30.0] * 40,
    }
)
LABELS = {
    "XTESS175": "Experimental scenario",
    "DOV_OPTION": "DOV: Experimental option",
    "Y": "outcome",
    "AGE": "age",
}


def test_catches_a_second_randomisation_that_is_fully_crossed(tmp_path) -> None:
    """The z358z regression: declare one variable, the other must be flagged."""
    ds = _write(tmp_path, CROSSED, LABELS)
    suspects = find_undeclared_assignment(ds, _recipe(["XTESS175"]))
    assert [s.var for s in suspects] == ["DOV_OPTION"], [s.render() for s in suspects]


def test_silent_once_both_variables_are_declared(tmp_path) -> None:
    ds = _write(tmp_path, CROSSED, LABELS)
    assert find_undeclared_assignment(ds, _recipe(["XTESS175", "DOV_OPTION"])) == []


def test_considered_and_rejected_silences_it(tmp_path) -> None:
    """The escape hatch records the judgment instead of leaving it implicit."""
    ds = _write(tmp_path, CROSSED, LABELS)
    rec = _recipe(["XTESS175"], rejected={"DOV_OPTION": "belongs to the other experiment"})
    assert find_undeclared_assignment(ds, rec) == []


def test_ignores_a_variable_that_is_not_fully_crossed(tmp_path) -> None:
    """Full crossing is the discriminating test.

    A variable nested inside one arm — a follow-up only asked of one scenario,
    say — is not a second factor of this design. Without this condition the
    screen would fire on most studies.
    """
    df = CROSSED.copy()
    df["DOV_OPTION"] = [1.0] * 20 + [2.0] * 20  # perfectly confounded with XTESS175
    ds = _write(tmp_path, df, LABELS)
    assert find_undeclared_assignment(ds, _recipe(["XTESS175"])) == []


def test_ignores_a_lopsided_variable(tmp_path) -> None:
    """Randomisation is balanced; an attention-check flag or a screener is not."""
    df = CROSSED.copy()
    df["DOV_OPTION"] = [1.0] * 38 + [2.0] * 2
    ds = _write(tmp_path, df, LABELS)
    assert find_undeclared_assignment(ds, _recipe(["XTESS175"])) == []


def test_ignores_variables_that_look_nothing_like_assignment(tmp_path) -> None:
    """Name/label pattern is the cheap first filter."""
    df = CROSSED.rename(columns={"DOV_OPTION": "PPGENDER"})
    labels = {**{k: v for k, v in LABELS.items() if k != "DOV_OPTION"}, "PPGENDER": "Gender"}
    ds = _write(tmp_path, df, labels)
    assert find_undeclared_assignment(ds, _recipe(["XTESS175"])) == []


@pytest.mark.parametrize("n_levels", [1, 13])
def test_ignores_implausible_level_counts(tmp_path, n_levels) -> None:
    """One level is not a manipulation; a great many is an item or a free response."""
    df = CROSSED.copy()
    df["DOV_OPTION"] = [float(i % n_levels) + 1 for i in range(40)]
    ds = _write(tmp_path, df, LABELS)
    assert find_undeclared_assignment(ds, _recipe(["XTESS175"])) == []


# ---------------------------------------------------------------------------
# Rule 11 — numbered siblings of the declared assignment variable.
#
# `b87sm` is within-subject: each respondent saw 8 vignettes from a 72-cell
# universe, slot k assigned by `P_S{k}`. Declaring `P_S1` leaves 7/8 of the
# observations unreachable, and rule 9 misses all seven — wrong name pattern,
# no keyword in the label ("PRELOAD VARIABLE: P_S2"), and 72 levels over
# MAX_LEVELS. This rule needs none of that machinery.
# ---------------------------------------------------------------------------

SLOTS = pd.DataFrame(
    {
        "P_S1": [float(i % 8) + 1 for i in range(40)],
        "P_S2": [float((i + 3) % 8) + 1 for i in range(40)],
        "Y": [1.0, 2.0] * 20,
        "AGE": [30.0] * 40,
    }
)
SLOT_LABELS = {
    "P_S1": "PRELOAD VARIABLE: P_S1",
    "P_S2": "PRELOAD VARIABLE: P_S2",
    "Y": "outcome",
    "AGE": "age",
}


def test_numbered_sibling_is_flagged(tmp_path) -> None:
    """The b87sm regression: P_S1 declared, P_S2 must be surfaced."""
    from micromotives_datasets.pipeline.screen import find_numbered_siblings

    ds = _write(tmp_path, SLOTS, SLOT_LABELS)
    assert find_numbered_siblings(ds, _recipe(["P_S1"])) == ["P_S2"]


def test_rule9_alone_is_blind_to_the_repeated_measure(tmp_path) -> None:
    """Why rule 11 has to exist separately.

    The sibling has no matching name pattern, no keyword in its label, and too
    many levels for rule 9's plausibility filter — so rule 9 says nothing. This
    test fails if someone later "simplifies" rule 11 away.
    """
    ds = _write(tmp_path, SLOTS, SLOT_LABELS)
    assert find_undeclared_assignment(ds, _recipe(["P_S1"])) == []


def test_numbered_siblings_silent_when_declared(tmp_path) -> None:
    from micromotives_datasets.pipeline.screen import find_numbered_siblings

    ds = _write(tmp_path, SLOTS, SLOT_LABELS)
    assert find_numbered_siblings(ds, _recipe(["P_S1", "P_S2"])) == []


def test_numbered_siblings_silenced_by_considered_and_rejected(tmp_path) -> None:
    from micromotives_datasets.pipeline.screen import find_numbered_siblings

    ds = _write(tmp_path, SLOTS, SLOT_LABELS)
    rec = _recipe(["P_S1"], rejected={"P_S2": "slot 2, owed as its own recipe"})
    assert find_numbered_siblings(ds, rec) == []


def test_no_stem_means_no_sibling_check(tmp_path) -> None:
    """A declared variable not ending in digits has no numbered siblings.

    Most assignment variables are like this (`SCENE`, `DOV_OPTION`), and the rule
    must stay silent rather than inventing a stem.
    """
    from micromotives_datasets.pipeline.screen import find_numbered_siblings

    df = SLOTS.rename(columns={"P_S1": "SCENE"})
    labels = {**{k: v for k, v in SLOT_LABELS.items() if k != "P_S1"}, "SCENE": "Scenario"}
    ds = _write(tmp_path, df, labels)
    assert find_numbered_siblings(ds, _recipe(["SCENE"])) == []


def test_recording_a_sibling_does_not_unsilence_its_components(tmp_path) -> None:
    """Rule 9 must suppress on the sibling FAMILY, not on what rule 11 reports.

    The bug this pins: rule 9 took its suppression list from
    `find_numbered_siblings`, which strips rejected variables — so recording
    `P_S2` in `considered_and_rejected` (the correct way to silence rule 11)
    un-silenced `P_S2`'s decomposed component columns in rule 9. Measured on the
    real `b87sm`, doing the right thing took the build from 5 warnings to 40.
    """
    from micromotives_datasets.pipeline.screen import find_numbered_siblings

    df = SLOTS.copy()
    # A component column of the sibling, of the shape b87sm really has.
    df["P_S2_Tech_Support"] = [1.0, 2.0] * 20
    labels = {**SLOT_LABELS, "P_S2_Tech_Support": "PRELOAD VARIABLE: P_S2 tech support"}
    ds = _write(tmp_path, df, labels)

    # Undeclared: rule 11 names the sibling, and rule 9 stays off its family.
    bare = _recipe(["P_S1"])
    assert find_numbered_siblings(ds, bare) == ["P_S2"]
    assert [s.var for s in find_undeclared_assignment(ds, bare)] == []

    # Recorded: rule 11 goes quiet and rule 9 must NOT pick up the component.
    rec = _recipe(["P_S1"], rejected={"P_S2": "slot 2, owed as its own recipe"})
    assert find_numbered_siblings(ds, rec) == []
    assert [s.var for s in find_undeclared_assignment(ds, rec)] == [], (
        "recording a sibling must not un-silence its component columns"
    )
