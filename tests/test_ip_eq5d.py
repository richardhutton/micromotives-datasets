"""IP 9.24 — the EQ-5D in its 3-level and 5-level forms, wave 11.

Three things here could go wrong quietly, and each has a test:

1. **Exposure.** The condition says whether the other form was asked earlier.
   It must be what happened, not what was allocated: a respondent who skipped
   the early module was never shown it. Checked against the raw file.

2. **The merged answers.** Each form's answers come from the early or the late
   module depending on the arm. A wrong pick would attach a real answer to the
   wrong position, and every count would still agree.

3. **The levels.** The middle options are what distinguishes the forms, so each
   question must carry its own form's options, word-for-word.

These need the UKDS deposit, which is licensed and gitignored, so they skip when
it is absent rather than failing on a fresh clone.
"""

from __future__ import annotations

import functools
import importlib.util
import sys
from pathlib import Path

import pytest

from micromotives_datasets import recipe
from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.sources import spss

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_ip_eq5d.py"
DERIVED = REPO / "data" / "raw" / "ukds_6849" / "eq5d_w11-derived.sav"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"
RECIPES = {
    "5l": REPO / "recipes" / "ukds_6849_eq5d5l_w11.yaml",
    "3l": REPO / "recipes" / "ukds_6849_eq5d3l_w11.yaml",
}
DIMS = ("mob", "care", "act", "pain", "anx")

# Mobility, from the questionnaire, deliberately not from the recipe.
MOBILITY = {
    "3l": (
        "I have no problems in walking about.",
        "I have some problems in walking about.",
        "I am confined to bed.",
    ),
    "5l": (
        "I have no problems in walking about.",
        "I have slight problems in walking about.",
        "I have moderate problems in walking about",
        "I have severe problems in walking about",
        "I am unable to walk about",
    ),
}
NOT_ASKED_BEFORE = "You had not been asked these health questions earlier in the interview."

needs_deposit = pytest.mark.skipif(
    not (STATA / "k_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not DERIVED.exists(), reason="derived file not built — run scripts/gen_ip_eq5d.py --write"
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_eq5d", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_eq5d"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows(form: str) -> tuple:
    return tuple(build_rows(spss.read(DERIVED), recipe.load(RECIPES[form])))


@functools.cache
def _raw() -> dict[str, tuple[int, bool, bool, dict[str, float]]]:
    """person -> (arm, saw 3L early, saw 5L early, answers by form+dim and time)."""
    gen = _generator()
    df = spss.read(STATA / "k_indresp_ip.dta").df
    out = {}
    for _, r in df.iterrows():
        early3 = any(r[f"k_eq3l{d}ear"] != -8 for d in DIMS)
        early5 = any(r[f"k_eq5l{d}ear"] != -8 for d in DIMS)
        answers = {
            f"{f}{d}{w}": float(r[f"k_eq{f}{d}{w}"])
            for f in ("3l", "5l")
            for d in DIMS
            for w in ("ear", "lat")
        }
        out[f"ukds_6849:{gen.person_hash(int(r['pidp']))}"] = (
            int(r["k_eq5dcond"]),
            early3,
            early5,
            answers,
        )
    return out


@needs_deposit
def test_no_answer_is_attributed_to_an_arm_that_never_asked_it() -> None:
    gen = _generator()
    frame, _ = gen.derive()
    assert not (frame.loc[frame["eq5dcond"] == 3, "eq3l_mob"] > 0).any()
    assert "pidp" not in frame.columns


@needs_derived
@pytest.mark.parametrize("form", ["5l", "3l"])
def test_the_condition_is_what_the_respondent_actually_saw(form: str) -> None:
    raw = _raw()
    after_other = {"5l": 2, "3l": 1}[form]
    for row in _rows(form):
        arm, early3, early5, _ = raw[row.participant_id]
        saw_other_early = early3 if form == "5l" else early5
        if row.condition == NOT_ASKED_BEFORE:
            assert arm != after_other
        else:
            assert arm == after_other and saw_other_early
            assert row.condition.startswith("Earlier in the interview you were asked: ")


@needs_derived
@pytest.mark.parametrize("form", ["5l", "3l"])
def test_each_answer_comes_from_the_module_its_arm_used(form: str) -> None:
    raw = _raw()
    when = {"5l": {1: "ear", 2: "lat", 3: "lat"}, "3l": {1: "lat", 2: "ear"}}[form]
    for row in _rows(form):
        arm, _, _, answers = raw[row.participant_id]
        dim = DIMS[row.task_num]
        assert answers[f"{form}{dim}{when[arm]}"] == float(row.response)


@needs_derived
@pytest.mark.parametrize("form", ["5l", "3l"])
def test_each_question_carries_its_own_forms_options(form: str) -> None:
    other = "3l" if form == "5l" else "5l"
    for row in _rows(form):
        if row.task_num != 0:
            continue
        for k, option in enumerate(MOBILITY[form], 1):
            assert f'{k} "{option}"' in row.outcome
        assert f'{len(MOBILITY[form]) + 1} "' not in row.outcome
        if row.condition != NOT_ASKED_BEFORE:
            assert f'"{MOBILITY[other][1]}"' in row.condition


@needs_derived
def test_the_row_counts() -> None:
    """The generator's answer counts, reached again by the pipeline."""
    assert len(_rows("5l")) == 13203
    assert len(_rows("3l")) == 8698
