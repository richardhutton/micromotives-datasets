"""IP 9.34 — marginal propensity to consume, wave 15, two recipes.

A 2 x 2 x 2 household split: question format (two-part / direct) x period (3 / 12
months) x amount (£500 / £2500). One recipe per format, both reading one derived
file, so that no outcome id carries a direction code in some rows and pounds in
others. What could go wrong quietly, and the test for each:

1. **The wording.** The period and amount exist only as fills inside the
   question, so a swapped fill builds and passes QC. Every cell's condition and
   outcome are pinned against questionnaire text written out here, never read
   from the recipe.
2. **The split.** Each recipe must hold only its own format's respondents, and
   every row's period and amount must be the household's allocation.
3. **The allocation itself.** Treatment and amount are visible in the routing
   (which variables hold answers); the generator's `--check` must find no answer
   outside it. Period is not visible in the routing and cannot be checked here.
4. **The fallback.** Each recipe's outcome has a placeholder question that every
   arm overrides; it reached all 1,259 two-part rows once with QC passing
   (ledger 146), so no row may carry a "[".

These need the UKDS deposit, which is licensed and gitignored, so they skip when
it is absent rather than failing on a fresh clone. Nothing here prints a
respondent's value, and no assertion is written so that its failure message
would: per-row checks count failures and assert the count.
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
GEN = REPO / "scripts" / "gen_ip_mpc.py"
RECIPES = {
    "two-part": REPO / "recipes" / "ukds_6849_mpc_twopart_w15.yaml",
    "direct": REPO / "recipes" / "ukds_6849_mpc_direct_w15.yaml",
}
TREATMENT = {"two-part": 1, "direct": 2}
DERIVED = REPO / "data" / "raw" / "ukds_6849" / "mpc_w15-derived.sav"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"

# From `6849_ip_wave_15_questionnaire.pdf`, module Scampc_ip15, deliberately not
# from the recipe. {a} is the amount fill, {d} the period fill.
TWO_PART = (
    "Now consider a hypothetical situation where you unexpectedly receive a one-time "
    "payment of {a} today. We would like to know whether this extra income would cause "
    "you to change your spending, borrowing and saving behaviour in any way over the next "
    "{d}. If you received the one-time {a} payment, over the next {d} would you..."
)
TWO_PART_OPTIONS = (
    "Spend more than if I hadn't received the {a}.",
    "Spend the same as if I hadn't received the {a}.",
    "Spend less than if I hadn't received the {a}.",
)
DIRECT = (
    "Imagine you unexpectedly received a one-time payment of {a} today. "
    "How much of it would you spend over the next {d}?"
)
BOX_LABEL = "Amount in £"

AMOUNT = {1: "£500", 2: "£2500"}
PERIOD = {1: "3 months", 2: "12 months"}
CAP = {"£500": 500, "£2500": 2500}

# condition_num -> (period code, amount code): the recipe's odometer, period slower.
CELLS = {0: (1, 1), 1: (1, 2), 2: (2, 1), 3: (2, 2)}
COUNTS = {
    "two-part": {0: 331, 1: 325, 2: 302, 3: 301},
    "direct": {0: 315, 1: 303, 2: 328, 3: 332},
}

needs_deposit = pytest.mark.skipif(
    not (STATA / "o_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not DERIVED.exists(), reason="derived file not built — run scripts/gen_ip_mpc.py --write"
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_mpc", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_mpc"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows(fmt: str) -> tuple:
    return tuple(build_rows(spss.read(DERIVED), recipe.load(RECIPES[fmt])))


@functools.cache
def _allocation() -> dict[str, tuple[int, int, int]]:
    """participant_id -> (treatment, period, amount), from the derived file."""
    df = spss.read(DERIVED).df
    return {
        f"ukds_6849:{p}": (int(t), int(d), int(a))
        for p, t, d, a in zip(
            df["person"], df["mpctreatment"], df["mpcduration"], df["mpcamount"], strict=True
        )
        if t > 0
    }


def _expected(fmt: str, condition_num: int) -> tuple[str, str]:
    """The cell's condition and the start of its outcome, from the text above."""
    d, a = CELLS[condition_num]
    fills = {"a": AMOUNT[a], "d": PERIOD[d]}
    if fmt == "two-part":
        question = TWO_PART.format(**fills)
        labels = [o.format(**fills) for o in TWO_PART_OPTIONS]
        instruction = (
            f'Only return an integer from 1 to 3 where 1 means "{labels[0]}", '
            f'2 means "{labels[1]}", and 3 means "{labels[2]}", nothing else.'
        )
        return f'You were asked: "{question}"', f"{question} {instruction}"
    question = DIRECT.format(**fills)
    instruction = f"Only return an integer from 0 to {CAP[AMOUNT[a]]}, nothing else."
    return f'You were asked: "{question}"', f"{question} {BOX_LABEL} {instruction}"


@needs_deposit
def test_no_answer_sits_outside_the_allocated_routing() -> None:
    """Treatment and amount, read from which variables hold answers. Must be zero."""
    assert _generator().check() == 0


@needs_deposit
def test_pidp_is_never_written_to_the_derived_file() -> None:
    frame, _ = _generator().derive()
    assert "pidp" not in frame.columns
    assert frame["person"].str.startswith("ip_").all()


@needs_derived
@pytest.mark.parametrize("fmt", list(RECIPES))
def test_every_cells_condition_and_outcome_are_the_questionnaires(fmt: str) -> None:
    seen = set()
    for row in _rows(fmt):
        condition, outcome = _expected(fmt, row.condition_num)
        assert row.condition == condition, (row.condition_num, row.condition[:120])
        assert row.outcome == outcome, (row.condition_num, row.outcome[-200:])
        seen.add(row.condition_num)
    assert seen == set(CELLS)


@needs_derived
@pytest.mark.parametrize("fmt", list(RECIPES))
def test_per_cell_counts(fmt: str) -> None:
    counts: dict[int, int] = {}
    for row in _rows(fmt):
        counts[row.condition_num] = counts.get(row.condition_num, 0) + 1
    assert counts == COUNTS[fmt]


@needs_derived
@pytest.mark.parametrize("fmt", list(RECIPES))
def test_no_row_carries_a_placeholder(fmt: str) -> None:
    for row in _rows(fmt):
        assert "[" not in row.condition + row.outcome, row.condition_num


@needs_derived
@pytest.mark.parametrize("fmt", list(RECIPES))
def test_each_recipe_holds_only_its_own_format(fmt: str) -> None:
    alloc = _allocation()
    treatments = {alloc[row.participant_id][0] for row in _rows(fmt)}
    assert treatments == {TREATMENT[fmt]}


@needs_derived
def test_no_respondent_is_in_both_recipes() -> None:
    two_part = {r.participant_id for r in _rows("two-part")}
    direct = {r.participant_id for r in _rows("direct")}
    assert not two_part & direct


@needs_derived
@pytest.mark.parametrize("fmt", list(RECIPES))
def test_every_rows_period_and_amount_are_its_households_allocation(fmt: str) -> None:
    alloc = _allocation()
    wrong = 0
    for row in _rows(fmt):
        _, d, a = alloc[row.participant_id]
        cell_ok = CELLS[row.condition_num] == (d, a)
        factors_ok = row.factors == {"duration": PERIOD[d], "amount": AMOUNT[a]}
        wrong += not (cell_ok and factors_ok)
    assert wrong == 0


@needs_derived
@pytest.mark.parametrize("fmt", list(RECIPES))
def test_every_response_is_inside_its_own_cells_range(fmt: str) -> None:
    outside = 0
    for row in _rows(fmt):
        value = int(row.response)
        low, high = (1, 3) if fmt == "two-part" else (0, CAP[row.factors["amount"]])
        outside += not low <= value <= high
    assert outside == 0


@needs_derived
@pytest.mark.parametrize("fmt", list(RECIPES))
def test_the_participant_id_is_the_persons_own_hash(fmt: str) -> None:
    assert all((r.participant_id or "").startswith("ukds_6849:ip_") for r in _rows(fmt))
