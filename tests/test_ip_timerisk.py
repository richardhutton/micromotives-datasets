"""IP 9.13 — time and risk preference choices, waves 6 and 7.

One condition, so the things that can go wrong are the words: the choices, the
preamble each respondent saw for their mode, and the second appeal only some saw.
The recipes are generated from the questionnaire PDFs, so the first test is that
regenerating them changes nothing.

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
GEN = REPO / "scripts" / "gen_ip_timerisk.py"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"
WAVES = {6: "f", 7: "g"}

# From the questionnaire, deliberately not from the recipe.
LAPTOP = "for you to complete yourself on the laptop."
WEB = "To do this, we will ask you a set of very brief questions."
APPEAL = "Thank you for answering some of the questions in this section."
CHOICE_01 = (
    'Between Option A and Option B, which option do you prefer? 1 "OPTION A: Receiving £100 '
    'in 1 month" 2 "OPTION B: Receiving £100.42 in 2 months"'
)


def _recipe(wave: int) -> Path:
    return REPO / "recipes" / f"ukds_6849_timerisk_w{wave}.yaml"


def _derived(wave: int) -> Path:
    return REPO / "data" / "raw" / "ukds_6849" / f"timerisk_w{wave}-derived.sav"


needs_deposit = pytest.mark.skipif(
    not (STATA / "f_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not all(_derived(w).exists() for w in WAVES),
    reason="derived files not built — run scripts/gen_ip_timerisk.py --write",
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_timerisk", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_timerisk"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows(wave: int) -> tuple:
    return tuple(build_rows(spss.read(_derived(wave)), recipe.load(_recipe(wave))))


@functools.cache
def _raw(wave: int) -> dict[str, tuple[int, int]]:
    w = WAVES[wave]
    gen = _generator()
    df = spss.read(STATA / f"{w}_indresp_ip.dta").df
    return {
        f"ukds_6849:{gen.person_hash(int(p))}": (int(m), int(b))
        for p, m, b in zip(df["pidp"], df[f"{w}_indmode"], df[f"{w}_riskpreb"], strict=True)
    }


@needs_deposit
def test_regenerating_the_recipes_changes_nothing(tmp_path) -> None:
    before = {w: _recipe(w).read_text() for w in WAVES}
    try:
        _generator().write_recipes()
        assert {w: _recipe(w).read_text() for w in WAVES} == before
    finally:
        for w, text in before.items():
            _recipe(w).write_text(text)


@needs_deposit
def test_nobody_answered_without_beginning_the_questions() -> None:
    gen = _generator()
    assert sum(gen.check(w) for w in gen.WAVES) == 0


@needs_derived
@pytest.mark.parametrize("wave", [6, 7])
def test_preamble_follows_mode_and_the_appeal_only_those_who_saw_it(wave: int) -> None:
    raw = _raw(wave)
    for row in _rows(wave):
        mode, appeal = raw[row.participant_id]
        assert (LAPTOP in row.condition) == (mode == 1)
        assert (WEB in row.condition) == (mode == 3)
        lottery = row.task_num >= 72
        assert (APPEAL in row.condition) == (lottery and appeal == 1)
        assert not row.condition.endswith(" ")


@needs_derived
@pytest.mark.parametrize("wave", [6, 7])
def test_no_sequence_label_and_the_first_choice_word_for_word(wave: int) -> None:
    for row in _rows(wave):
        assert "Choice " not in row.outcome and "In this last choice" not in row.outcome
        if row.task_num == 0:
            assert row.outcome.startswith(CHOICE_01)


@needs_derived
def test_the_row_counts() -> None:
    assert len(_rows(6)) == 63487
    assert len(_rows(7)) == 46283
