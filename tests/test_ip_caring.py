"""IP 9.47 — existing against activity-based caring questions, in order, wave 17.

The condition must say what was actually asked earlier, the answer must come from
the module the household's allocation used, and the wording must follow mode.
The recipes are generated from the questionnaire, so regenerating must change nothing.

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
GEN = REPO / "scripts" / "gen_ip_caring.py"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"
DERIVED = REPO / "data" / "raw" / "ukds_6849" / "caring_w17-derived.sav"
RECIPES = {k: REPO / "recipes" / f"ukds_6849_caring_{k}_w17.yaml" for k in ("activity", "existing")}
# From the questionnaire, deliberately not from the recipe.
WEB_ZERO = "If none, just enter zero."
AIDHH_OPEN = "Is there anyone living with you who is sick"
EXISTING_ROWS = 4847

needs_deposit = pytest.mark.skipif(
    not (STATA / "q_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not DERIVED.exists(), reason="derived file not built — run scripts/gen_ip_caring.py --write"
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_caring", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_caring"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows(key: str) -> tuple:
    return tuple(build_rows(spss.read(DERIVED), recipe.load(RECIPES[key])))


@functools.cache
def _raw() -> dict[str, dict]:
    gen = _generator()
    df = spss.read(STATA / "q_indresp_ip.dta").df
    out = {}
    for _, r in df.iterrows():
        out[f"ukds_6849:{gen.person_hash(int(r['pidp']))}"] = {
            "activity_early": r["q_abcarhhear"] >= 0 or r["q_abcarhhear"] in (-1, -2),
            "existing_early": r["q_aidxhhear"] >= 0 or r["q_aidxhhear"] in (-1, -2),
            "aidhh_in_universe": r["q_aidhhear"] != -8 or r["q_aidhhlat"] != -8,
            "mode": int(r["q_indmode"]),
            "answers": {
                c[2:]: float(r[c])
                for c in df.columns
                if c.startswith(("q_abcar", "q_aid", "q_naid"))
            },
        }
    return out


@needs_deposit
def test_regenerating_the_recipes_changes_nothing() -> None:
    before = {k: p.read_text() for k, p in RECIPES.items()}
    try:
        _generator().write_recipes()
        assert {k: p.read_text() for k, p in RECIPES.items()} == before
    finally:
        for k, text in before.items():
            RECIPES[k].write_text(text)


@needs_deposit
def test_no_answer_outside_the_allocated_module() -> None:
    assert _generator().check() == 0


@needs_derived
@pytest.mark.parametrize("key", ["activity", "existing"])
def test_condition_and_answer_follow_what_was_actually_asked(key: str) -> None:
    raw = _raw()
    other_early = "existing_early" if key == "activity" else "activity_early"
    own_early = "activity_early" if key == "activity" else "existing_early"
    rec = recipe.load(RECIPES[key])
    for row in _rows(key):
        p = raw[row.participant_id]
        assert row.condition.startswith("Earlier in the interview") == p[other_early]
        if key == "activity":
            assert (AIDHH_OPEN in row.condition) == p["aidhh_in_universe"]
        var = rec.outcomes[row.task_num].var
        when = "ear" if p[own_early] else "lat"
        raw_value = p["answers"][f"{var}{when}"]
        assert (10.0 if raw_value == 97 else raw_value) == float(row.response)


@needs_derived
def test_wording_follows_mode() -> None:
    raw = _raw()
    for row in _rows("activity"):
        assert (WEB_ZERO in row.outcome) == (raw[row.participant_id]["mode"] == 3)


@needs_derived
def test_the_row_counts() -> None:
    assert len(_rows("activity")) == 13875
    assert len(_rows("existing")) == EXISTING_ROWS
