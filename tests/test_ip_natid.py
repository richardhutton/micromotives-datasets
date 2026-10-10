"""IP 9.38 — importance of being British, with or without the national identity
question asked first, wave 15.

An order experiment, so the text of the two conditions is fixed and the things
that can go wrong quietly are WHO gets which condition:

1. **Routing, not the label.** The condition must be the version the respondent
   was routed into, and that must match the household allocation. Checked here
   against the raw files with a join the test does itself.

2. **New entrants.** The main interview asks new entrants the same national
   identity question, so "had not been asked earlier" is false for them. They
   must carry no row; their household's other members must still carry theirs.

3. **The wording.** Both strings are written out below from the questionnaire
   (`6849_ip_wave_15_questionnaire.pdf`, module Scaidentityexp_ip15), never read
   from the recipe.

These need the UKDS deposit, which is licensed and gitignored, so they skip when
it is absent rather than failing on a fresh clone. Nothing respondent-level is
printed by any assertion message here: failures report counts only.
"""

from __future__ import annotations

import functools
import hashlib
import importlib.util
import sys
from collections import Counter
from pathlib import Path

import pytest

from micromotives_datasets import recipe
from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.sources import spss

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_ip_natid.py"
RECIPE = REPO / "recipes" / "ukds_6849_national_identity_w15.yaml"
DERIVED = REPO / "data" / "raw" / "ukds_6849" / "natid_w15-derived.sav"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"

# From the questionnaire, deliberately not from the recipe.
NATID = (
    "What do you consider your national identity to be? You may choose as many or as few as apply."
)
NATID_OPTIONS = ("English", "Welsh", "Scottish", "Northern Irish", "British", "Irish", "Other")
BRIT = (
    "Most people who live in the UK may think of themselves as being British in some way. "
    "On a scale of 0 to 10 where 0 means 'not at all important' and 10 means 'extremely "
    "important', how important is being British to you?"
)
CONDITION = {
    0: f'You had not been asked the question "{NATID}" earlier in the interview.',
    1: f'Earlier in the interview you were asked: "{NATID}" '
    + " / ".join(f'"{o}"' for o in NATID_OPTIONS),
}
# Version A (importance first) is routed on allocation 1, version B on 2.
ALLOC_FOR_CONDITION = {0: 1, 1: 2}
NOT_ASKED = (-8, -7)

needs_deposit = pytest.mark.skipif(
    not (STATA / "o_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not DERIVED.exists(), reason="derived file not built — run scripts/gen_ip_natid.py --write"
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_natid", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_natid"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows() -> tuple:
    return tuple(build_rows(spss.read(DERIVED), recipe.load(RECIPE)))


def _built() -> tuple:
    """The rows, refusing an empty or shrunken set: a per-row check over no rows
    passes vacuously (two mutations here emptied the build and only the count
    test noticed)."""
    rows = _rows()
    assert len(rows) >= 2400, f"only {len(rows)} rows built"
    return rows


def _pid(pidp: int) -> str:
    """Written out here rather than imported, so a changed hash in the generator fails."""
    return "ukds_6849:ip_" + hashlib.sha256(f"ukds6849:{pidp}".encode()).hexdigest()[:12]


@functools.cache
def _raw() -> dict[str, dict]:
    """participant id -> what the RAW files say about them, joined by this test.

    Independent of the generator and of the recipe: allocation from `o_hhsamp_ip`,
    which version's question holds anything but not-asked, and whether the main
    interview routed them into its own national identity question.
    """
    ind = spss.read(STATA / "o_indresp_ip.dta").df
    hh = spss.read(STATA / "o_hhsamp_ip.dta").df
    alloc = dict(zip(hh["o_hidp"], hh["o_ff_identityw15"], strict=True))
    out: dict[str, dict] = {}
    for rec in ind[["pidp", "o_hidp", "o_scbritida", "o_scbritidb", "o_natid1"]].itertuples(
        index=False
    ):
        out[_pid(int(rec.pidp))] = {
            "hidp": int(rec.o_hidp),
            "alloc": int(alloc[rec.o_hidp]),
            "a": rec.o_scbritida not in NOT_ASKED,
            "b": rec.o_scbritidb not in NOT_ASKED,
            "a_ans": 0 <= rec.o_scbritida <= 10,
            "b_ans": 0 <= rec.o_scbritidb <= 10,
            "new_entrant": rec.o_natid1 not in NOT_ASKED,
        }
    return out


@needs_deposit
def test_check_finds_no_routing_inconsistency() -> None:
    assert _generator().check() == 0


@needs_deposit
def test_pidp_is_never_written_to_the_derived_file() -> None:
    frame, _ = _generator().derive()
    assert "pidp" not in frame.columns
    assert frame["person"].str.startswith("ip_").all()


@needs_derived
def test_every_row_carries_the_questionnaires_condition_and_outcome() -> None:
    for row in _built():
        assert row.condition == CONDITION[row.condition_num]
        assert row.outcome.startswith(BRIT + " Only return an integer from 0 to 10")
        assert row.factors["natid_asked_earlier"] == ("yes" if row.condition_num else "no")


@needs_derived
def test_condition_follows_routing_and_matches_the_household_allocation() -> None:
    raw = _raw()
    wrong_alloc = wrong_route = 0
    for row in _built():
        r = raw[row.participant_id]
        wrong_alloc += r["alloc"] != ALLOC_FOR_CONDITION[row.condition_num]
        routed_a, routed_b = (r["a"], r["b"]) if row.condition_num == 0 else (r["b"], r["a"])
        wrong_route += not routed_a or routed_b
    assert (wrong_alloc, wrong_route) == (0, 0)


@needs_derived
def test_responses_are_the_routed_versions_own_answer() -> None:
    ind = spss.read(STATA / "o_indresp_ip.dta").df
    value = {
        _pid(int(p)): (a, b)
        for p, a, b in zip(ind["pidp"], ind["o_scbritida"], ind["o_scbritidb"], strict=True)
    }
    bad = sum(
        float(row.response) != float(value[row.participant_id][row.condition_num])
        for row in _built()
    )
    assert bad == 0


@needs_derived
def test_the_per_condition_counts_and_range() -> None:
    rows = _rows()
    assert Counter(r.condition_num for r in rows) == {0: 1229, 1: 1243}
    assert {int(r.response) for r in rows} <= set(range(11))
    assert len({r.participant_id for r in rows}) == len(rows)


@needs_derived
def test_new_entrants_are_excluded() -> None:
    raw = _raw()
    # Not vacuous: 142 new entrants gave an in-scale answer in their own version.
    eligible = {
        pid
        for pid, r in raw.items()
        if r["new_entrant"]
        and ((r["alloc"] == 1 and r["a_ans"]) or (r["alloc"] == 2 and r["b_ans"]))
    }
    assert len(eligible) == 142
    assert sum(r.participant_id in eligible for r in _built()) == 0


@needs_deposit
def test_the_generator_gives_new_entrants_no_condition() -> None:
    gen = _generator()
    df, _ = gen._joined()
    frame, _ = gen.derive()
    entrants = (~df["o_natid1"].isin(NOT_ASKED)).to_numpy()
    assert entrants.sum() > 0
    assert int((frame["natid_prior"].to_numpy()[entrants] > 0).sum()) == 0


@needs_derived
def test_household_members_of_new_entrants_are_kept() -> None:
    """The exclusion is per person: only the new entrant met NatID earlier."""
    raw = _raw()
    entrant_households = {r["hidp"] for r in raw.values() if r["new_entrant"]}
    kept = sum(raw[row.participant_id]["hidp"] in entrant_households for row in _built())
    assert kept > 0


@needs_deposit
def test_condition_is_read_from_routing_not_the_allocation_label(monkeypatch) -> None:
    """On this deposit routing and allocation agree exactly, so a generator that
    read the label alone would build identical rows and pass every test above.
    A synthetic frame, no respondent data, where they disagree, decides it."""
    import pandas as pd

    gen = _generator()
    w = gen.W
    na = -8
    frame = pd.DataFrame(
        {
            # alloc says 1, routed into B -> asked earlier (2)
            # alloc says 2, routed into A -> not asked earlier (1)
            # alloc 1, routed nowhere -> no condition
            # alloc 1, routed into A, new entrant -> no condition
            "pidp": [1, 2, 3, 4],
            "alloc": [1, 2, 1, 1],
            f"{w}_scbritida": [na, 5, na, 5],
            f"{w}_scbritidb": [5, na, na, na],
            f"{w}_scnatidb1": [1, na, na, na],
            f"{w}_natid1": [na, na, na, 1],
            **{f"{w}_{v}": [0, 0, 0, 0] for v in gen.PERSONA},
        }
    )
    monkeypatch.setattr(gen, "_joined", lambda: (frame, {}))
    derived, _ = gen.derive()
    assert derived["natid_prior"].tolist() == [2.0, 1.0, -8.0, -8.0]
    assert derived["brit"].tolist() == [5.0, 5.0, -8.0, -8.0]
