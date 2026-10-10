"""IP 9.26 — right to remain for an immigrant where the respondent lives or in Glasgow, wave 11.

What could go wrong quietly, and the test for each:

1. **The wording.** The condition is the one part we write. Each arm must carry
   its own vignette, word-for-word, and the own-place arm its one clause of ours
   where the place's name was. Pinned against questionnaire text written out
   below, never read from the recipe.

2. **The allocation.** `cjitown` is person-level on `k_indresp_ip`. This file
   reads it again itself, independently of the generator, and requires every
   row's condition to equal it.

3. **The fill boundary and the symmetry.** The own-place clause is true only
   where the address was confirmed (`k_hhresp_ip.k_addrchck` = 1, joined here on
   `k_hidp`), and the Glasgow arm is restricted the same way so both arms come
   from one population. No row in EITHER arm may come from anyone else, and no
   buildable answer may be lost.

4. **The routing.** No telephone or interviewer-assisted respondent may appear.

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
GEN = REPO / "scripts" / "gen_ip_immig.py"
RECIPE = REPO / "recipes" / "ukds_6849_immig_vignette_w11.yaml"
DERIVED = REPO / "data" / "raw" / "ukds_6849" / "immig_w11-derived.sav"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"

# ---------------------------------------------------------------------------
# From `6849_ip_wave_11_questionnaires.pdf`, module Scaconjointimmigration_ip11,
# `Cjivig`, pp. 515-516. Deliberately NOT from the recipe.
# ---------------------------------------------------------------------------
BEFORE_TOWN = "A male born in Poland who lives in a private rental property in"
AFTER_TOWN = (
    "has put in an application for the right to remain in the United Kingdom "
    "indefinitely. He has a pre-existing health condition, is married and has three "
    "children in state school."
)
GLASGOW = "Glasgow"  # "GLASGOW {if cjitown = 2}", spelled as the allocation's label
QUESTION = (
    "On a scale from 1 to 10, where 1 indicates that the government should not grant "
    "the person the right to remain in the United Kingdom and 10 indicates that the "
    "applicant should be granted the right to remain in the United Kingdom, how would "
    "you rate the applicant?"
)
LOW = "Do not grant the applicant the right to remain"
HIGH = "Grant the applicant the right to remain"

# Our own words (docs/CONVENTIONS.md, narration and the layout exception), pinned
# here so a change to them is a decision and not a drift.
OPENING = (
    "After being asked to compare pairs of applicants for permanent residency in the "
    "United Kingdom, you were shown this text:"
)
# "place", not "town": the fill is ff_post_code, and what the screen printed is unseen.
OWN_PLACE = "(here the screen named the place where you live)"

CONDITION = {
    0: f'{OPENING} "{BEFORE_TOWN}" {OWN_PLACE} "{AFTER_TOWN}"',
    1: f'{OPENING} "{BEFORE_TOWN} {GLASGOW} {AFTER_TOWN}"',
}
OUTCOME = f'{QUESTION} Only return an integer from 1 to 10 where 1 means "{LOW}" and 10 means "{HIGH}", nothing else.'  # noqa: E501
COUNTS = {0: 968, 1: 949}


needs_deposit = pytest.mark.skipif(
    not (STATA / "k_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not DERIVED.exists(), reason="derived file not built — run scripts/gen_ip_immig.py --write"
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_immig", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_immig"] = module
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
    """participant id -> what the DEPOSIT says about them, joined here, not by the generator.

    Dictionaries rather than DataFrame merges, so no join can raise an error
    that quotes a key. Nothing from this mapping is ever printed.
    """
    ind = spss.read(STATA / "k_indresp_ip.dta").df
    hhr = spss.read(STATA / "k_hhresp_ip.dta").df
    addr = {h: _code(a) for h, a in zip(hhr["k_hidp"], hhr["k_addrchck"], strict=True)}
    out: dict[str, dict[str, int | None]] = {}
    for _, r in ind.iterrows():
        pidp = int(r["pidp"])
        pid = "ukds_6849:ip_" + hashlib.sha256(f"ukds6849:{pidp}".encode()).hexdigest()[:12]
        out[pid] = {
            "alloc": _code(r["k_cjitown"]),
            "answer": _code(r["k_cjivig"]),
            "addrchck": addr.get(r["k_hidp"]),
            "indmode": _code(r["k_indmode"]),
            "scac": _code(r["k_scac"]),
        }
    return out


# --- the generator ---------------------------------------------------------


@needs_deposit
def test_check_finds_allocation_routing_labels_and_fill_consistent() -> None:
    assert _generator().check() == 0


@needs_deposit
def test_check_counts_a_routing_change() -> None:
    gen = _generator()
    merged, labels = gen._joined()
    broken = merged.copy()
    # Every routed web respondent recoded to telephone: the universe excludes it.
    routed_web = (~broken["k_cjivig"].isin([-8, -7])) & (broken["k_indmode"] == 3)
    broken.loc[routed_web, "k_indmode"] = 2
    assert gen.check(broken, labels) > 0


@needs_deposit
def test_check_counts_swapped_allocation_labels() -> None:
    gen = _generator()
    merged, labels = gen._joined()
    broken = dict(labels)
    broken["k_cjitown"] = {1.0: "Glasgow", 2.0: "Town of residence from ff_postcode"}
    assert gen.check(merged, broken) > 0


@needs_deposit
def test_check_counts_a_missing_allocation() -> None:
    gen = _generator()
    merged, labels = gen._joined()
    broken = merged.copy()
    routed = ~broken["k_cjivig"].isin([-8, -7])
    broken.loc[routed[routed].index[:5], "k_cjitown"] = -9
    assert gen.check(broken, labels) > 0


@needs_deposit
def test_check_counts_a_fill_that_ignores_the_address(monkeypatch) -> None:
    gen = _generator()
    merged, labels = gen._joined()

    def every_own_town(m):  # the bug: arm 1 built whether or not the address held
        return m["k_cjitown"].where(m["k_cjitown"].isin([1, 2]))

    monkeypatch.setattr(gen, "town_shown", every_own_town)
    assert gen.check(merged, labels) > 0


@needs_deposit
def test_check_counts_a_glasgow_arm_left_unrestricted(monkeypatch) -> None:
    """The first build's asymmetry: own place restricted, Glasgow not."""
    gen = _generator()
    merged, labels = gen._joined()

    def glasgow_unrestricted(m):
        arm = m["k_cjitown"]
        out = arm.where((arm == 1) & (m["k_addrchck"] == 1))
        return out.mask(arm == 2, 2)

    monkeypatch.setattr(gen, "town_shown", glasgow_unrestricted)
    assert gen.check(merged, labels) > 0


@needs_deposit
def test_check_exits_non_zero_when_it_finds_anything(monkeypatch) -> None:
    gen = _generator()
    monkeypatch.setattr(gen, "check", lambda merged=None, labels=None: 1)
    monkeypatch.setattr(sys, "argv", ["gen_ip_immig.py", "--check"])
    with pytest.raises(SystemExit) as exc:
        gen.main()
    assert exc.value.code not in (0, None)


def test_a_failed_join_never_quotes_its_keys() -> None:
    """Synthetic frames: the earlier slip was pandas listing duplicated keys."""
    import pandas as pd

    gen = _generator()
    left = pd.DataFrame({"k_hidp": [918273645, 564738291]})
    right = pd.DataFrame({"k_hidp": [918273645, 918273645], "x": [1, 2]})
    with pytest.raises(gen.IdentifierSafeError) as exc:
        gen._merge(left, right, "k_hidp", "test join")
    assert "918273645" not in str(exc.value)
    assert exc.value.__cause__ is None and exc.value.__context__ is None

    broken_left = pd.DataFrame({"other": [918273645]})
    ok_right = pd.DataFrame({"k_hidp": [564738291], "x": [1]})
    with pytest.raises(gen.IdentifierSafeError) as exc2:
        gen._merge(broken_left, ok_right, "k_hidp", "test join")
    assert "918273645" not in str(exc2.value)
    assert exc2.value.__cause__ is None and exc2.value.__suppress_context__


@needs_deposit
def test_pidp_is_never_written_to_the_derived_file() -> None:
    frame, _ = _generator().derive()
    assert "pidp" not in frame.columns
    assert "hidp" not in " ".join(frame.columns)
    assert frame["person"].str.startswith("ip_").all()


# --- the built rows ---------------------------------------------------------


@needs_derived
def test_each_condition_is_its_own_arms_vignette() -> None:
    wrong = sum(row.condition != CONDITION[row.condition_num] for row in _rows())
    assert wrong == 0


@needs_derived
def test_the_outcome_is_the_questionnaires_question() -> None:
    wrong = sum(row.outcome != OUTCOME for row in _rows())
    assert wrong == 0


@needs_derived
def test_rows_per_condition_and_answer_codes() -> None:
    rows = _rows()
    assert dict(collections.Counter(r.condition_num for r in rows)) == COUNTS
    out_of_range = sum(not 1 <= int(r.response) <= 10 for r in rows)
    assert out_of_range == 0
    assert {r.task_num for r in rows} == {0}


@needs_derived
def test_each_rows_condition_is_its_allocation_and_every_arm_needs_a_confirmed_address() -> None:
    dep = _deposit()
    off_allocation = 0
    unconfirmed: collections.Counter[int] = collections.Counter()
    for row in _rows():
        d = dep[row.participant_id]
        off_allocation += d["alloc"] != row.condition_num + 1
        unconfirmed[row.condition_num] += d["addrchck"] != 1
    assert off_allocation == 0
    # Both arms, separately: the symmetry is the point.
    assert unconfirmed[0] == 0
    assert unconfirmed[1] == 0


@needs_derived
def test_every_buildable_answer_is_a_row_and_nothing_else() -> None:
    """The other direction, computed from the deposit alone."""
    dep = _deposit()
    expected = collections.Counter()
    for d in dep.values():
        if d["answer"] is None or not 1 <= d["answer"] <= 10:
            continue
        if d["alloc"] in (1, 2) and d["addrchck"] == 1:
            expected[int(d["alloc"]) - 1] += 1  # type: ignore[arg-type]
    assert dict(expected) == COUNTS
    assert len({r.participant_id for r in _rows()}) == sum(COUNTS.values())


@needs_derived
def test_only_self_completion_respondents() -> None:
    dep = _deposit()
    rows = _rows()
    phone = sum(dep[r.participant_id]["indmode"] == 2 for r in rows)
    assisted = sum(
        dep[r.participant_id]["indmode"] == 1 and dep[r.participant_id]["scac"] != 1 for r in rows
    )
    assert phone == 0
    assert assisted == 0
