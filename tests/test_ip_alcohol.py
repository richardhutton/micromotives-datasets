"""IP 9.36 — alcohol asked in units or in drinks, wave 15.

Three things here could go wrong quietly, and each has a test:

1. **The household join.** The version lives in `o_hhsamp_ip`. A wrong join
   would put a person under the other version's wording while their answer sits
   in their own version's variable, which is checkable: answers must never sit in
   the other version's variables.

2. **The wording.** The version IS the question. Each row's question must be its
   own version's, word-for-word, and the narrated condition must quote exactly
   the question the row then asks.

3. **The sex fill.** "6 or more" for women, "8 or more" for men, resolved per
   row. A swapped directive would still build and pass QC.

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
GEN = REPO / "scripts" / "gen_ip_alcohol.py"
RECIPE = REPO / "recipes" / "ukds_6849_alcohol_w15.yaml"
DERIVED = REPO / "data" / "raw" / "ukds_6849" / "alcohol_w15-derived.sav"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"

# From the questionnaire, deliberately not from the recipe. {n} is the threshold.
WORDING = {
    "units": (
        "How many units of alcohol do you drink on a typical day when you are drinking?",
        "How often have you had {n} or more units, on a single occasion in the last year?",
    ),
    "drinks": (
        "How many alcoholic drinks do you have on a typical day when you are drinking?",
        "How often have you had {n} or more alcoholic drinks, on a single occasion in the "
        "last year?",
    ),
}
THRESHOLD = {"Female": "6", "Male": "8"}

needs_deposit = pytest.mark.skipif(
    not (STATA / "o_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not DERIVED.exists(), reason="derived file not built — run scripts/gen_ip_alcohol.py --write"
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_alcohol", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_alcohol"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows() -> tuple:
    return tuple(build_rows(spss.read(DERIVED), recipe.load(RECIPE)))


@needs_deposit
def test_no_answer_sits_in_the_other_versions_variables() -> None:
    assert _generator().check() == 0


@needs_deposit
def test_pidp_is_never_written_to_the_derived_file() -> None:
    frame, _ = _generator().derive()
    assert "pidp" not in frame.columns
    assert frame["person"].str.startswith("ip_").all()


@needs_derived
def test_every_row_asks_its_own_versions_question_with_its_own_threshold() -> None:
    for row in _rows():
        template = WORDING[row.factors["measure"]][row.task_num]
        question = template.format(n=THRESHOLD[row.persona.sex])
        assert row.outcome.startswith(question + " "), (question, row.outcome[:90])
        assert row.condition == f'You were asked: "{question}"'


@needs_derived
def test_no_directive_or_fallback_reaches_a_row() -> None:
    for row in _rows():
        assert "[" not in row.condition + row.outcome
        assert "IF sex" not in row.condition + row.outcome


@needs_derived
def test_the_row_count_and_the_range() -> None:
    """4,208: the generator's count of answers, reached again by the pipeline."""
    rows = _rows()
    assert len(rows) == 4208
    assert {int(r.response) for r in rows} <= {1, 2, 3, 4, 5}
    assert {r.condition_num for r in rows} == {0, 1}


@needs_derived
def test_the_participant_id_is_the_persons_own_hash() -> None:
    assert all((r.participant_id or "").startswith("ukds_6849:ip_") for r in _rows())
