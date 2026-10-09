"""IP 9.42 — compound growth framed as savings or as sea level, wave 16.

The archive's labels for which set came first are reversed, so the tests take
the truth from WHICH section each respondent answered, never from a label or
from the generator's reading of the allocation.

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
GEN = REPO / "scripts" / "gen_ip_numeracy.py"
DERIVED = REPO / "data" / "raw" / "ukds_6849" / "numeracy_w16-derived.sav"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"
RECIPES = {k: REPO / "recipes" / f"ukds_6849_numeracy_{k}_w16.yaml" for k in ("env", "fin")}
HORIZONS = ("5y", "30y", "100y")
# From the questionnaire, deliberately not from the recipe.
STEM = {
    "env": "Imagine a certain island that currently lies 100cm below sea level.",
    "fin": "Imagine a savings account with a current balance of £100.",
}

needs_deposit = pytest.mark.skipif(
    not (STATA / "p_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not DERIVED.exists(), reason="derived file not built — run scripts/gen_ip_numeracy.py --write"
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_numeracy", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_numeracy"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows(key: str) -> tuple:
    return tuple(build_rows(spss.read(DERIVED), recipe.load(RECIPES[key])))


@functools.cache
def _raw() -> dict[str, dict]:
    gen = _generator()
    df = spss.read(STATA / "p_indresp_ip.dta").df
    out = {}
    for _, r in df.iterrows():

        def asked(block: str, when: str, r=r) -> bool:
            return any(
                r[f"p_{block}num{when}{h}"] > 0 or r[f"p_{block}num{when}{h}"] in (-1, -2)
                for h in HORIZONS
            )

        out[f"ukds_6849:{gen.person_hash(int(r['pidp']))}"] = {
            "env_early": asked("env", "ear"),
            "fin_early": asked("fin", "ear"),
            "answers": {
                c.removeprefix("p_"): float(r[c])
                for c in df.columns
                if c.startswith(("p_envnum", "p_finnum"))
            },
        }
    return out


@needs_deposit
def test_no_answer_falls_outside_the_questionnaires_routing() -> None:
    assert _generator().check() == 0


@needs_derived
@pytest.mark.parametrize("key", ["env", "fin"])
def test_the_condition_is_whether_the_other_set_was_actually_answered_early(key: str) -> None:
    other = "fin" if key == "env" else "env"
    raw = _raw()
    for row in _rows(key):
        p = raw[row.participant_id]
        asked_earlier = row.condition.startswith("Earlier in the interview you were asked: ")
        assert asked_earlier == p[f"{other}_early"]
        assert STEM[other] in row.condition
        assert row.outcome.startswith(STEM[key])


@needs_derived
@pytest.mark.parametrize("key", ["env", "fin"])
def test_each_answer_comes_from_the_section_the_respondent_answered(key: str) -> None:
    raw = _raw()
    for row in _rows(key):
        p = raw[row.participant_id]
        when = "ear" if p[f"{key}_early"] else "lat"
        assert p["answers"][f"{key}num{when}{HORIZONS[row.task_num]}"] == float(row.response)


@needs_derived
def test_the_row_counts() -> None:
    assert len(_rows("env")) == 4638
    assert len(_rows("fin")) == 4602
