"""IP 9.39 — flexibility stigma in hiring, wave 16.

Three things here could go wrong quietly, and each has a test:

1. **The name in each slot.** Every slot codes its own two names 1/2, so a
   shared code would put Charlotte in slot 2. A wrong map renders a real
   candidate under the wrong name, with every count still agreeing.

2. **Agreement.** Pronouns in the description and in three of the four
   questions follow the name. Asserted on every row against a table written
   HERE from the questionnaire, not read back out of the recipe.

3. **Twelve outcomes, four kinds.** The right variable must reach the right
   task with the right question and scale. A swapped pair would still build.

These need the UKDS deposit, which is licensed and gitignored, so they skip when
it is absent rather than failing on a fresh clone.
"""

from __future__ import annotations

import functools
import importlib.util
import re
import sys
from pathlib import Path

import pytest

from micromotives_datasets import recipe
from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.sources import spss

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_ip_vig_flexstigma.py"
RECIPE = REPO / "recipes" / "ukds_6849_vig_flexstigma_w16.yaml"
DERIVED = REPO / "data" / "raw" / "ukds_6849" / "vig_flexstigma_w16-derived.sav"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"

# From the questionnaire, deliberately not from the recipe.
SLOT_NAMES = {
    1: {"Charlotte Davies": "f", "Paul Taylor": "m"},
    2: {"Anna Wright": "f", "Adam Newton": "m"},
    3: {"Sarah Walker": "f", "James Harrison": "m"},
}
PRONOUNS = {"f": ("She", "her", "her"), "m": ("He", "him", "his")}
QUESTIONS = (
    "How likely is it that would you recommend {name} for the job?",
    "How do you see {obj} in terms of {poss} work commitment?",
    "How do you see {obj} in terms of {poss} productivity?",
    "How do you see {obj} as a team player?",
)
ITEMS = ("fsvrecomm", "fsvcommit", "fsvproduct", "fsvteam")

needs_deposit = pytest.mark.skipif(
    not (STATA / "p_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not DERIVED.exists(),
    reason="derived file not built — run scripts/gen_ip_vig_flexstigma.py --write",
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_vig_flexstigma", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_vig_flexstigma"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows() -> tuple:
    return tuple(build_rows(spss.read(DERIVED), recipe.load(RECIPE)))


# --- 1. the name in each slot ------------------------------------------------


@needs_deposit
def test_every_derived_name_agrees_with_its_slots_own_label() -> None:
    assert _generator().check() == 0


@needs_deposit
def test_pidp_is_never_written_to_the_derived_file() -> None:
    frame, _ = _generator().derive()
    assert "pidp" not in frame.columns
    assert frame["person"].str.startswith("ip_").all()


@needs_derived
def test_each_slot_shows_only_its_own_two_names() -> None:
    for row in _rows():
        slot = row.task_num // 4 + 1
        assert row.factors["name"] in SLOT_NAMES[slot]


# --- 2. agreement, on every row ----------------------------------------------


@needs_derived
def test_description_and_question_follow_the_name_on_every_row() -> None:
    for row in _rows():
        slot = row.task_num // 4 + 1
        name = row.factors["name"]
        subject, obj, poss = PRONOUNS[SLOT_NAMES[slot][name]]
        body = row.condition.split("each\ncandidate. ", 1)[1]
        assert body.startswith(f"{name}, aged 35, ")
        assert f". {subject} works full-time and " in body
        expected = QUESTIONS[row.task_num % 4].format(name=name, obj=obj, poss=poss)
        assert row.outcome.startswith(expected + " "), (expected, row.outcome[:80])


@needs_derived
def test_no_position_label_bracket_or_brace_reaches_a_row() -> None:
    """ "Candidate 2:" would tell a respondent where they are in a sequence the
    row cannot express; brackets are the fallback questions' fill markers."""
    for row in _rows():
        assert "Candidate" not in row.condition
        assert not re.search(r"[\[\]{}]", row.condition + row.outcome)


@needs_derived
def test_the_condition_expresses_every_factor_the_row_claims() -> None:
    rec = recipe.load(RECIPE)
    assert rec.condition.template is not None
    dims = rec.condition.template.dimensions
    for row in _rows():
        for name, level in row.factors.items():
            wanted = next(v.text for v in dims[name].levels.values() if v.level == level)
            assert wanted in row.condition, f"{name}={level} not in the condition"


# --- 3. twelve outcomes ------------------------------------------------------


def test_each_task_reads_the_right_variable_and_scale() -> None:
    """Needs no data: the outcome wiring is a property of the recipe."""
    rec = recipe.load(RECIPE)
    assert len(rec.outcomes) == 12
    for o in rec.outcomes:
        slot, kind = o.task_num // 4 + 1, o.task_num % 4
        assert o.var == f"{ITEMS[kind]}{slot}"
        want = ("Not at all likely", "Most likely") if kind == 0 else ("Very poor", "Very good")
        assert (o.scale.min, o.scale.max, o.scale.min_label, o.scale.max_label) == (0, 10, *want)
        if slot > 1:
            assert o.condition_vars == [f"name{slot}"] + [
                f"{d}{slot}" for d in ("fsvigparent", "fsvighybrid", "fsvigorguse", "fsvigorgpol")
            ]


@needs_derived
def test_the_row_count_and_the_range() -> None:
    """17,656: the generator's count of ratings given, reached again by the pipeline."""
    rows = _rows()
    assert len(rows) == 17656
    assert {int(r.response) for r in rows} <= set(range(11))
    assert len({r.condition_num for r in rows}) == 576


@needs_derived
def test_the_participant_id_is_the_persons_own_hash() -> None:
    assert all((r.participant_id or "").startswith("ukds_6849:ip_") for r in _rows())


@needs_derived
def test_the_allocation_is_as_clean_as_the_recipe_says() -> None:
    gen = _generator()
    got = gen.report_allocation(gen.derive()[0])
    assert got["allocated"] == got["distinct"] == 1616
    assert got["in_repeated"] == 0
