"""IP 9.14 — willingness to pay environmental taxes, ten question wordings, wave 7.

What could go wrong quietly, and the test for each:

1. **The wording.** The condition is the one part we write. Each of the ten
   versions differs by a clause, and each row must carry its own version's
   question, word-for-word, in the condition and the outcome. Pinned against
   questionnaire text written out below, never read from the recipe or the
   generator.

2. **The household join.** The version lives in `g_hhsamp_ip`. This file joins
   it again itself, independently of the generator, and requires every row's
   condition to equal that allocation AND the routing: the row's own version's
   variable holds the answer and every other version's is -8.

3. **The doubly-routed respondent** (ledger 143). One respondent holds a code in
   a version their household was not allocated. The recipe declares it; the
   melt must refuse a recipe that does not, and the derived file must blank only
   "not asked" (-8, -7), or the check would read routing that is not there.

4. **No answer lost**: every answered, singly-routed respondent is a row.

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
import re
import sys
from pathlib import Path

import pytest

from micromotives_datasets import recipe
from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.sources import spss

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_ip_envtax.py"
RECIPE = REPO / "recipes" / "ukds_6849_envtax_w7.yaml"
DERIVED = REPO / "data" / "raw" / "ukds_6849" / "envtax_w7-derived.sav"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"

# ---------------------------------------------------------------------------
# From `6849_ip_wave_7_questionnaires.pdf`, module Environmentaltax_ip7, pp.
# 538-541, items Envtax_a ... Envtax_j, field "Text". Deliberately NOT from the
# recipe or the generator. Keyed by condition_num (version code - 1).
# ---------------------------------------------------------------------------
STEM = "How willing would you be to pay higher taxes"
REDUCED = "reduced other taxes you pay by the same amount"
QUESTION = {
    0: f"{STEM} in order to protect the environment?",
    1: f"{STEM} in order to protect the environment, if the government {REDUCED}?",
    2: f"{STEM}, if the government spent the extra money on protecting the environment?",
    3: f"{STEM}, if the government spent the extra money on protecting the environment "
    f"and {REDUCED}?",
    4: f"{STEM}, if the government promised it would spend the extra money on protecting "
    "the environment?",
    # F says "reduce", not "reduced": the source's own word.
    5: f"{STEM}, if the government promised it would spend the extra money on protecting "
    "the environment and reduce other taxes you pay by the same amount?",
    6: f"{STEM} on things you buy that pollute the environment?",
    7: f"{STEM} on things you buy that pollute the environment, if the government {REDUCED}?",
    8: f"{STEM} on things you buy that pollute the environment, like petrol or electricity?",
    9: f"{STEM} on things you buy that pollute the environment, like petrol or electricity, "
    f"if the government {REDUCED}?",
}
# Options 1 "Very willing" ... 4 "Not at all willing"; the endpoints are what the
# answer instruction can carry (ledger 133).
INSTRUCTION = (
    'Only return an integer from 1 to 4 where 1 means "Very willing" and '
    '4 means "Not at all willing", nothing else.'
)
# Our own words (docs/CONVENTIONS.md, narration), pinned so a change is a decision.
NARRATION = "You were asked: "

VARS = [f"g_envtax_{v}" for v in "abcdefghij"]
# Answers 1-4 per condition, counted from the deposit on 10 Oct 2026.
COUNTS = {0: 234, 1: 221, 2: 197, 3: 222, 4: 214, 5: 219, 6: 238, 7: 218, 8: 235, 9: 237}


needs_deposit = pytest.mark.skipif(
    not (STATA / "g_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not DERIVED.exists(), reason="derived file not built — run scripts/gen_ip_envtax.py --write"
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_envtax", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_envtax"] = module
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
    ind = spss.read(STATA / "g_indresp_ip.dta").df
    hh = spss.read(STATA / "g_hhsamp_ip.dta").df
    alloc = {h: _code(a) for h, a in zip(hh["g_hidp"], hh["g_ff_envtaxqw7"], strict=True)}
    out: dict[str, dict[str, int | None]] = {}
    for _, r in ind.iterrows():
        pidp = int(r["pidp"])
        pid = "ukds_6849:ip_" + hashlib.sha256(f"ukds6849:{pidp}".encode()).hexdigest()[:12]
        rec: dict[str, int | None] = {"alloc": alloc.get(r["g_hidp"])}
        for v in VARS:
            rec[v] = _code(r[v])
        out[pid] = rec
    return out


# --- the generator ---------------------------------------------------------


@needs_deposit
def test_check_finds_allocation_routing_wording_and_recipe_consistent() -> None:
    assert _generator().check() == 0


@needs_deposit
def test_check_counts_a_scrambled_allocation() -> None:
    gen = _generator()
    merged, _ = gen._joined()
    broken = merged.copy()
    broken["g_ff_envtaxqw7"] = (
        broken["g_ff_envtaxqw7"].map({1: 2, 2: 1}).fillna(broken["g_ff_envtaxqw7"])
    )
    assert gen.check_routing(broken) > 0


@needs_deposit
def test_check_counts_a_second_doubly_routed_respondent() -> None:
    gen = _generator()
    merged, _ = gen._joined()
    broken = merged.copy()
    # One more version-A respondent with a code in version B's variable.
    target = broken.index[(broken["g_ff_envtaxqw7"] == 1) & (broken["g_envtax_a"] > 0)][0]
    broken.loc[target, "g_envtax_b"] = 2
    assert gen.check_routing(broken) > 0


@needs_deposit
def test_check_counts_a_respondent_not_routed_to_their_own_question() -> None:
    """The deposit has none, so only a broken copy exercises these two counts."""
    gen = _generator()
    merged, _ = gen._joined()
    answered_a = (merged["g_ff_envtaxqw7"] == 1) & (merged["g_envtax_a"] > 0)
    unrouted = merged.copy()
    unrouted.loc[unrouted.index[answered_a][0], "g_envtax_a"] = -8
    assert gen.check_routing(unrouted) > 0
    proxy_a = (merged["g_ff_envtaxqw7"] == 1) & (merged["g_indmode"] == -7)
    coded_proxy = merged.copy()
    coded_proxy.loc[coded_proxy.index[proxy_a][0], "g_envtax_a"] = 2
    assert gen.check_routing(coded_proxy) > 0
    # A blank in the respondent's OWN variable would be written blank and dropped.
    blank_own = merged.copy()
    blank_own["g_envtax_a"] = blank_own["g_envtax_a"].astype(float)
    blank_own.loc[blank_own.index[answered_a][0], "g_envtax_a"] = float("nan")
    assert gen.check_routing(blank_own) > 0


@needs_deposit
def test_check_counts_a_changed_word_in_the_questionnaire() -> None:
    gen = _generator()
    quex = gen._questionnaire()
    assert gen.check_wording(quex) == 0
    # F's "reduce" made "reduced"; the PDF wraps lines, so match any whitespace.
    broken, n = re.subn(r"and(\s+)reduce(\s+)other", r"and\1reduced\2other", quex, count=1)
    assert n == 1
    assert gen.check_wording(broken) > 0
    rerouted = quex.replace("If (ff_envtaxqw7=4)", "If (ff_envtaxqw7=5)", 1)
    assert (rerouted == quex) is False
    assert gen.check_wording(rerouted) > 0


@needs_deposit
def test_check_exits_non_zero_when_it_finds_anything(monkeypatch) -> None:
    gen = _generator()
    monkeypatch.setattr(gen, "check", lambda merged=None, quex=None: 1)
    monkeypatch.setattr(sys, "argv", ["gen_ip_envtax.py", "--check"])
    with pytest.raises(SystemExit) as exc:
        gen.main()
    assert exc.value.code not in (0, None)


def test_a_failed_join_never_quotes_its_keys() -> None:
    """Synthetic frames: pandas' own MergeError lists duplicated keys."""
    import pandas as pd

    gen = _generator()
    left = pd.DataFrame({"pidp": [918273645, 564738291]})
    right = pd.DataFrame({"pidp": [918273645, 918273645], "x": [1, 2]})
    with pytest.raises(gen.IdentifierSafeError) as exc:
        gen._merge(left, right, "pidp", "test join")
    assert "918273645" not in str(exc.value)
    assert exc.value.__cause__ is None and exc.value.__context__ is None


@needs_deposit
def test_pidp_is_never_written_to_the_derived_file() -> None:
    frame, _ = _generator().derive()
    assert "pidp" not in frame.columns
    assert "hidp" not in " ".join(frame.columns)
    assert frame["person"].str.startswith("ip_").all()


@needs_derived
def test_derived_file_blanks_only_not_asked() -> None:
    """Blank exactly where the deposit says -8 or -7, the deposit's code everywhere else."""
    dep = _deposit()
    derived = spss.read(DERIVED).df
    by_person = {p: i for i, p in enumerate(derived["person"])}
    wrong = 0
    for pid, d in dep.items():
        i = by_person[pid.removeprefix("ukds_6849:")]
        for v in VARS:
            got = _code(derived.at[i, v.removeprefix("g_")])
            want = None if d[v] in (-8, -7) else d[v]
            wrong += got != want
    assert len(by_person) == len(dep)
    assert wrong == 0


# --- the built rows ---------------------------------------------------------


@needs_derived
def test_each_condition_and_outcome_is_its_own_versions_question() -> None:
    wrong_condition = wrong_outcome = 0
    for row in _rows():
        q = QUESTION[row.condition_num]
        wrong_condition += row.condition != f'{NARRATION}"{q}"'
        wrong_outcome += row.outcome != f"{q} {INSTRUCTION}"
    assert wrong_condition == 0
    assert wrong_outcome == 0


@needs_derived
def test_no_placeholder_reaches_a_row() -> None:
    assert sum("[" in r.condition or "[" in r.outcome for r in _rows()) == 0


@needs_derived
def test_rows_per_condition_and_answer_codes() -> None:
    rows = _rows()
    assert dict(collections.Counter(r.condition_num for r in rows)) == COUNTS
    assert sum(int(r.response) not in {1, 2, 3, 4} for r in rows) == 0
    assert {r.task_num for r in rows} == {0}
    assert len({r.participant_id for r in rows}) == len(rows)


@needs_derived
def test_each_rows_condition_is_its_households_allocation_and_its_routing() -> None:
    dep = _deposit()
    off_allocation = off_routing = 0
    for row in _rows():
        d = dep[row.participant_id]
        own = VARS[row.condition_num]
        off_allocation += d["alloc"] != row.condition_num + 1
        off_routing += d[own] not in {1, 2, 3, 4} or any(d[v] != -8 for v in VARS if v != own)
    assert off_allocation == 0
    assert off_routing == 0


@needs_derived
def test_every_singly_routed_answer_is_a_row_and_only_one_respondent_is_doubly_routed() -> None:
    dep = _deposit()
    expected: collections.Counter[int] = collections.Counter()
    doubly = 0
    for d in dep.values():
        if d["alloc"] not in range(1, 11):
            continue
        own = VARS[int(d["alloc"]) - 1]  # type: ignore[arg-type]
        if any(d[v] not in (-8, -7) for v in VARS if v != own):
            doubly += 1
            continue
        if d[own] in {1, 2, 3, 4}:
            expected[int(d["alloc"]) - 1] += 1  # type: ignore[arg-type]
    assert doubly == 1
    assert dict(expected) == COUNTS


@needs_derived
def test_the_melt_refuses_an_undeclared_doubly_routed_respondent() -> None:
    rec = recipe.load(RECIPE)
    undeclared = rec.model_copy(deep=True)
    undeclared.condition.ambiguous_routing = 0
    with pytest.raises(ValueError, match="routed to more than one condition"):
        list(build_rows(spss.read(DERIVED), undeclared))
