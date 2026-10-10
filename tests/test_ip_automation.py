"""IP 9.30 — intentions to prepare for automation, severity x timeframe vignette, wave 14.

What could go wrong quietly, and the test for each:

1. **The wording.** The condition is the one part we write. Each cell's
   vignette is assembled from the questionnaire's fills, and a fill attached to
   the wrong code would build, reconcile and pass QC. Pinned against text
   written out below from the questionnaire, never read from the recipe.

2. **The household join.** The allocation lives in `n_hhsamp_ip`. This file
   joins it again itself, with dictionaries rather than the generator's merge,
   and requires every row's condition to equal its household's code.

3. **The routing.** Every routed respondent holds an allocation; no answer is
   lost and none appears from outside the module's universe.

4. **The pre-vignette items** (`datawork` .. `losejoblong`) were asked before
   any condition and must never appear as outcomes.

5. **`--check` must be able to fail**, and must exit non-zero when it does.

UKDS rule: no assertion here compares or prints an identifier, a persona value
or a response value. Every comparison that touches respondents is reduced to a
COUNT first, so a failure message can only ever show a number.

These need the UKDS deposit, which is licensed and gitignored, so they skip when
it is absent rather than failing on a fresh clone.
"""

from __future__ import annotations

import collections
import functools
import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

from micromotives_datasets import recipe
from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.sources import spss

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_ip_automation.py"
RECIPE = REPO / "recipes" / "ukds_6849_automation_w14.yaml"
DERIVED = REPO / "data" / "raw" / "ukds_6849" / "automation_w14-derived.sav"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"

# ---------------------------------------------------------------------------
# From `6849_ip_wave_14_questionnaire.pdf`, module Scaworktech_ip14, `Techreplace`
# (p. 661 of 739), fills resolved by hand from the boxes on the rendered page.
# Deliberately NOT from the recipe.
# ---------------------------------------------------------------------------
TAIL = (
    "jobs now being done by humans could be done by new technology (e.g., robots, "
    "artificial intelligence, or algorithms)."
)
CONDITION = {
    0: f"Experts predict that in the next 20 years, 50% of all {TAIL}",  # code 1
    1: f"Experts predict that in the next 5 years, 50% of all {TAIL}",  # code 2
    2: f"Experts predict that in the next 20 years, 10% of all {TAIL}",  # code 3
    3: f"Experts predict that in the next 5 years, 10% of all {TAIL}",  # code 4
    4: (  # code 5, control
        f"Some experts think that in the future, {TAIL} Other experts think that new "
        "technology cannot replace work by humans, or only to limited extent."
    ),
}
STEM = (
    "When you think about your own work or organisation, to what extent do you agree "
    "or disagree with the following statements?"
)
ITEMS = {
    "techreplace": "My job could be replaced by new technology.",
    "techdoes": "I am worried that what I do in my job can be done by new technology.",
    "techopp": "New technology offers me new job opportunities.",
    "techimport": "It is important to keep up with new technological developments at work.",
    "techoutdate": "I am worried that new technology will make my skills outdated.",
    "techskills": "New technology offers me the opportunity to acquire new skills.",
    "techtrain": "I need further training to keep up with technological developments at work.",
    "techtime": "I am willing to spend extra time learning new technological skills for my work.",
    "techchange": (
        "I am considering training for a different job because new technology is replacing my work."
    ),
}
TASKS = list(ITEMS)
INSTRUCTION = (
    'Only return an integer from 1 to 5 where 1 means "Totally disagree" and 5 means '
    '"Totally agree", nothing else.'
)
PRE_VIGNETTE = ("datawork", "algorithmwork", "robotwork", "losejob", "losejoblong")

# Counted on the deposit 10 Oct 2026, aggregates only.
CELL_COUNTS = {0: 2777, 1: 3130, 2: 2950, 3: 3130, 4: 3033}
TASK_COUNTS = {0: 1669, 1: 1669, 2: 1665, 3: 1671, 4: 1671, 5: 1671, 6: 1668, 7: 1668, 8: 1668}
ROUTED = 1699


needs_deposit = pytest.mark.skipif(
    not (STATA / "n_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not DERIVED.exists(),
    reason="derived file not built — run scripts/gen_ip_automation.py --write",
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_automation", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_automation"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows() -> tuple:
    return tuple(build_rows(spss.read(DERIVED), recipe.load(RECIPE)))


def _code(value: object) -> int | None:
    try:
        f = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return None if f != f else int(f)


@functools.cache
def _deposit() -> dict[str, dict[str, int | None]]:
    """participant id -> what the DEPOSIT says, joined here, not by the generator.

    Dictionaries rather than DataFrame merges, so no join can raise an error
    that quotes a key. Nothing from this mapping is ever printed.
    """
    ind = spss.read(STATA / "n_indresp_ip.dta").df
    hhs = spss.read(STATA / "n_hhsamp_ip.dta").df
    alloc = {h: _code(a) for h, a in zip(hhs["n_hidp"], hhs["n_ff_techworkw14"], strict=True)}
    out: dict[str, dict[str, int | None]] = {}
    for _, r in ind.iterrows():
        pidp = int(r["pidp"])
        pid = "ukds_6849:ip_" + hashlib.sha256(f"ukds6849:{pidp}".encode()).hexdigest()[:12]
        d: dict[str, int | None] = {
            "alloc": alloc.get(r["n_hidp"]),
            "indmode": _code(r["n_indmode"]),
            "scac": _code(r["n_scac"]),
            "jbhas": _code(r["n_jbhas"]),
            "jboff": _code(r["n_jboff"]),
        }
        for v in TASKS:
            d[v] = _code(r[f"n_{v}"])
        out[pid] = d
    return out


# --- the generator ---------------------------------------------------------


@needs_deposit
def test_check_finds_allocation_routing_and_labels_consistent() -> None:
    assert _generator().check() == 0


@needs_deposit
def test_check_counts_a_routing_change() -> None:
    gen = _generator()
    merged, labels = gen._joined()
    broken = merged.copy()
    # Routed respondents recoded as not in work: the universe excludes them.
    routed = ~broken["n_techreplace"].isin([-8, -7])
    idx = routed[routed].index[:5]
    broken.loc[idx, "n_jbhas"] = 2
    broken.loc[idx, "n_jboff"] = 2
    assert gen.check(broken, labels) > 0


@needs_deposit
def test_check_counts_one_item_routed_differently() -> None:
    gen = _generator()
    merged, labels = gen._joined()
    broken = merged.copy()
    routed = ~broken["n_techreplace"].isin([-8, -7])
    broken.loc[routed[routed].index[:3], "n_techchange"] = -8
    assert gen.check(broken, labels) > 0


@needs_deposit
def test_check_counts_swapped_allocation_labels() -> None:
    gen = _generator()
    merged, labels = gen._joined()
    broken = dict(labels)
    swapped = dict(labels["n_ff_techworkw14"])
    swapped[1.0], swapped[3.0] = swapped[3.0], swapped[1.0]
    broken["n_ff_techworkw14"] = swapped
    assert gen.check(merged, broken) > 0


@needs_deposit
def test_check_counts_a_missing_allocation() -> None:
    gen = _generator()
    merged, labels = gen._joined()
    broken = merged.copy()
    routed = ~broken["n_techreplace"].isin([-8, -7])
    broken.loc[routed[routed].index[:5], "n_ff_techworkw14"] = -9
    assert gen.check(broken, labels) > 0


@needs_deposit
def test_check_exits_non_zero_when_it_finds_anything(monkeypatch) -> None:
    gen = _generator()
    monkeypatch.setattr(gen, "check", lambda merged=None, labels=None: 1)
    monkeypatch.setattr(sys, "argv", ["gen_ip_automation.py", "--check"])
    with pytest.raises(SystemExit) as exc:
        gen.main()
    assert exc.value.code not in (0, None)


def test_a_failed_join_never_quotes_its_keys() -> None:
    """Synthetic frames: pandas' own MergeError lists duplicated keys."""
    import pandas as pd

    gen = _generator()
    left = pd.DataFrame({"n_hidp": [918273645, 564738291]})
    right = pd.DataFrame({"n_hidp": [918273645, 918273645], "x": [1, 2]})
    with pytest.raises(gen.IdentifierSafeError) as exc:
        gen._merge(left, right, "n_hidp", "test join")
    assert "918273645" not in str(exc.value)
    assert exc.value.__cause__ is None and exc.value.__context__ is None


@needs_deposit
def test_pidp_is_never_written_to_the_derived_file() -> None:
    frame, _ = _generator().derive()
    assert "pidp" not in frame.columns
    assert "hidp" not in " ".join(frame.columns)
    assert frame["person"].str.startswith("ip_").all()


# --- the built rows ---------------------------------------------------------


@needs_derived
def test_each_condition_is_its_cells_vignette() -> None:
    wrong = sum(row.condition != CONDITION[row.condition_num] for row in _rows())
    assert wrong == 0


@needs_derived
def test_each_outcome_is_the_stem_and_its_own_statement() -> None:
    wrong = sum(
        row.outcome != f"{STEM} {ITEMS[TASKS[row.task_num]]} {INSTRUCTION}" for row in _rows()
    )
    assert wrong == 0


@needs_derived
def test_no_pre_vignette_item_is_an_outcome() -> None:
    built = {o.var for o in recipe.load(RECIPE).outcomes}
    assert built == set(ITEMS)
    assert not built & set(PRE_VIGNETTE)


@needs_derived
def test_rows_per_cell_and_per_outcome() -> None:
    rows = _rows()
    assert dict(collections.Counter(r.condition_num for r in rows)) == CELL_COUNTS
    assert dict(collections.Counter(r.task_num for r in rows)) == TASK_COUNTS
    out_of_range = sum(not 1 <= int(r.response) <= 5 for r in rows)
    assert out_of_range == 0


@needs_derived
def test_each_rows_condition_is_its_households_allocation() -> None:
    dep = _deposit()
    off = sum(dep[r.participant_id]["alloc"] != r.condition_num + 1 for r in _rows())
    assert off == 0


@needs_derived
def test_every_answer_is_a_row_and_nothing_else() -> None:
    """The other direction, computed from the deposit alone."""
    dep = _deposit()
    expected: collections.Counter = collections.Counter()
    routed = 0
    for d in dep.values():
        if d["techreplace"] not in (-8, -7, None):
            routed += 1
        for t, v in enumerate(TASKS):
            ans = d[v]
            if ans is not None and 1 <= ans <= 5:
                expected[(int(d["alloc"]) - 1, t)] += 1  # type: ignore[arg-type]
    got = collections.Counter((r.condition_num, r.task_num) for r in _rows())
    assert routed == ROUTED
    assert sum((expected - got).values()) == 0
    assert sum((got - expected).values()) == 0


@needs_derived
def test_every_row_is_inside_the_modules_universe() -> None:
    dep = _deposit()
    outside = 0
    for r in _rows():
        d = dep[r.participant_id]
        mode_ok = (d["indmode"] == 1 and d["scac"] in (1, 2, 3)) or d["indmode"] in (2, 3)
        work_ok = d["jbhas"] == 1 or d["jboff"] == 1
        outside += not (mode_ok and work_ok)
    assert outside == 0
