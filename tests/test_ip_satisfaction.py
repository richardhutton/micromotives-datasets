"""IP 9.20 — the same satisfaction questions in three layouts, wave 9.

No word differs between arms, so the things that can go wrong are which layout
a row claims, and whether someone who never saw a screen is given one.

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
GEN = REPO / "scripts" / "gen_ip_satisfaction.py"
RECIPE = REPO / "recipes" / "ukds_6849_satisfaction_w9.yaml"
DERIVED = REPO / "data" / "raw" / "ukds_6849" / "satisfaction_w9-derived.sav"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"
# From the questionnaire's scripting note, deliberately not from the recipe.
LAYOUT_WORD = {1: "grid", 2: "vertically aligned", 3: "horizontally aligned"}

needs_deposit = pytest.mark.skipif(
    not (STATA / "i_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not DERIVED.exists(),
    reason="derived file not built — run scripts/gen_ip_satisfaction.py --write",
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_satisfaction", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_satisfaction"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows() -> tuple:
    return tuple(build_rows(spss.read(DERIVED), recipe.load(RECIPE)))


@functools.cache
def _raw() -> dict[str, tuple[int, int]]:
    """participant id -> (household layout, interview mode), read independently."""
    gen = _generator()
    ind = spss.read(STATA / "i_indresp_ip.dta").df
    hh = spss.read(STATA / "i_hhsamp_ip.dta").df
    layout = dict(zip(hh["i_hidp"], hh["i_ff_satisw9"].fillna(-9), strict=True))
    ind = ind.assign(i_indmode=ind["i_indmode"].fillna(-9))
    return {
        f"ukds_6849:{gen.person_hash(int(p))}": (int(layout.get(h, -9)), int(mode))
        for p, h, mode in zip(
            ind["pidp"], ind["i_hidp"], ind["i_indmode"].where(ind["i_scac"] != 2, 2), strict=True
        )
    }


@needs_deposit
def test_every_answering_respondent_has_an_allocation() -> None:
    assert _generator().check() == 0


@needs_derived
def test_each_row_describes_its_households_layout_and_nobody_heard_it() -> None:
    raw = _raw()
    for row in _rows():
        layout, mode = raw[row.participant_id]
        assert mode != 2, "someone who heard the questions was given a screen layout"
        assert LAYOUT_WORD[layout] in row.condition
        others = [w for k, w in LAYOUT_WORD.items() if k != layout]
        assert not any(w in row.condition for w in others)


@needs_derived
def test_the_row_count_and_range() -> None:
    rows = _rows()
    assert len(rows) == 8025
    assert {int(r.response) for r in rows} <= set(range(1, 8))
    assert all(r.outcome.startswith("Here are some questions about how you feel") for r in rows)
