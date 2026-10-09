"""IP 9.9 — expected fertility asked before or after questions about friends, waves 4-5.

The condition says whether the friends block came first; it must be what happened.
The recipes are generated from the questionnaires, so regenerating them must change
nothing.

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
GEN = REPO / "scripts" / "gen_ip_fertility.py"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"
WAVES = {4: "d", 5: "e"}
# From the questionnaire, deliberately not from the recipe.
FRIENDS = "How many close friends would you say you have?"
LOOP = "Thinking of up to three of your closest friends"


def _recipe(wave: int) -> Path:
    return REPO / "recipes" / f"ukds_6849_fertility_w{wave}.yaml"


def _derived(wave: int) -> Path:
    return REPO / "data" / "raw" / "ukds_6849" / f"fertility_w{wave}-derived.sav"


needs_deposit = pytest.mark.skipif(
    not (STATA / "d_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not all(_derived(w).exists() for w in WAVES),
    reason="derived files not built — run scripts/gen_ip_fertility.py --write",
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_fertility", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_fertility"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows(wave: int) -> tuple:
    return tuple(build_rows(spss.read(_derived(wave)), recipe.load(_recipe(wave))))


@functools.cache
def _raw(wave: int) -> dict[str, tuple[bool, float]]:
    """participant id -> (answered version B, raw closenum), read independently."""
    w = WAVES[wave]
    gen = _generator()
    df = spss.read(STATA / f"{w}_indresp_ip.dta").df
    return {
        f"ukds_6849:{gen.person_hash(int(p))}": (b >= 0, float(c))
        for p, b, c in zip(df["pidp"], df[f"{w}_lchmor_b"], df[f"{w}_closenum"], strict=True)
    }


@needs_deposit
def test_regenerating_the_recipes_changes_nothing() -> None:
    before = {w: _recipe(w).read_text() for w in WAVES}
    try:
        _generator().write_recipes()
        assert {w: _recipe(w).read_text() for w in WAVES} == before
    finally:
        for w, text in before.items():
            _recipe(w).write_text(text)


@needs_deposit
def test_no_answer_sits_in_the_other_version_and_the_join_agrees() -> None:
    gen = _generator()
    assert sum(gen.check(w) for w in gen.WAVES) == 0


@needs_derived
@pytest.mark.parametrize("wave", [4, 5])
def test_the_condition_follows_which_version_was_answered(wave: int) -> None:
    raw = _raw(wave)
    for row in _rows(wave):
        version_b, closenum = raw[row.participant_id]
        asked_earlier = row.condition.startswith("Earlier in the interview you were asked: ")
        assert asked_earlier == version_b
        assert (FRIENDS in row.condition) == version_b
        assert (LOOP in row.condition) == (version_b and closenum > 0)
        assert "[" not in row.condition and not row.condition.endswith(" ")


@needs_derived
def test_the_row_counts() -> None:
    assert len(_rows(4)) == 532
    assert len(_rows(5)) == 407


@needs_derived
def test_wave_4_version_b_carries_the_wording_as_printed() -> None:
    """The wave 4 specification prints Version B as "have and (more) children?"."""
    for row in _rows(4):
        if row.task_num == 0:
            asked_earlier = row.condition.startswith("Earlier")
            assert ("will have and (more)" in row.outcome) == asked_earlier


@needs_derived
def test_web_respondents_were_not_told_to_enter_a_number() -> None:
    """On the web "Enter number" is a box label, not part of the question."""
    gen = _generator()
    df = spss.read(STATA / "e_indresp_ip.dta").df
    mode = {
        f"ukds_6849:{gen.person_hash(int(p))}": int(m)
        for p, m in zip(df["pidp"], df["e_indmode"], strict=True)
    }
    web_seen = 0
    for row in _rows(5):
        if row.condition.startswith("Earlier"):
            web = mode[row.participant_id] == 3
            web_seen += web
            assert ("Enter number" in row.condition) != web
    assert web_seen
