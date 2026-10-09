"""IP 9.31 — ReQoL-10 and EQ-5D-3L against the GHQ-12, in order, wave 14.

Three things here could go wrong quietly, and each has a test:

1. **The allocation.** The refreshment sample's arm is in the household file;
   its person-level variable holds a value that means nothing. Using it would
   put ~480 respondents under the wrong condition with every count agreeing.

2. **The answers.** Each block's answers come from the early or late module its
   arm used.

3. **Mode.** Telephone respondents heard different ReQoL and EQ-5D wording.

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
GEN = REPO / "scripts" / "gen_ip_reqol.py"
DERIVED = REPO / "data" / "raw" / "ukds_6849" / "reqol_w14-derived.sav"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"
RECIPES = {k: REPO / "recipes" / f"ukds_6849_{k}_w14.yaml" for k in ("reqol", "ghq")}

# From the questionnaire, deliberately not from the recipe.
REQOL1_WEB = "For each of the following statements, please tick ONE box that best describes"
REQOL1_TEL = "I will now read statements that relate to your quality of life"
GHQ_OPENING = "The next questions are about how you have been feeling over the last few weeks."

needs_deposit = pytest.mark.skipif(
    not (STATA / "n_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not DERIVED.exists(), reason="derived file not built — run scripts/gen_ip_reqol.py --write"
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_reqol", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_reqol"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows(key: str) -> tuple:
    return tuple(build_rows(spss.read(DERIVED), recipe.load(RECIPES[key])))


@functools.cache
def _raw() -> dict[str, dict]:
    """Per participant: true arm (from what was answered), mode, raw answers."""
    gen = _generator()
    df = spss.read(STATA / "n_indresp_ip.dta").df
    out = {}
    for _, r in df.iterrows():
        early_reqol = any(r[f"n_reqol{i}ear"] != -8 for i in range(1, 11))
        early_ghq = any(r[f"n_scghq{c}ear"] != -8 for c in "abcdefghijkl")
        arm = 1 if early_reqol else 2 if early_ghq else None
        answers = {
            c.removeprefix("n_"): float(r[c]) for c in df.columns if c.endswith(("ear", "lat"))
        }
        out[f"ukds_6849:{gen.person_hash(int(r['pidp']))}"] = {
            "arm": arm,
            "mode": int(r["n_indmode"]),
            "answers": answers,
        }
    return out


@needs_deposit
def test_no_answer_sits_in_a_module_the_arm_did_not_use() -> None:
    assert _generator().check() == 0


@needs_derived
@pytest.mark.parametrize("key", ["reqol", "ghq"])
def test_the_condition_follows_what_was_actually_answered_first(key: str) -> None:
    """The truth here is read off WHICH early module each person answered, not
    off either allocation variable, so a wrong allocation source fails."""
    raw = _raw()
    after_other = {"reqol": 2, "ghq": 1}[key]
    for row in _rows(key):
        truth = raw[row.participant_id]["arm"]
        asked_earlier = row.condition.startswith("Earlier in the interview you were asked: ")
        assert asked_earlier == (truth == after_other), row.participant_id


@needs_derived
@pytest.mark.parametrize("key", ["reqol", "ghq"])
def test_each_answer_comes_from_the_module_its_arm_used(key: str) -> None:
    raw = _raw()
    rec = recipe.load(RECIPES[key])
    early_in = {"reqol": 1, "ghq": 2}[key]
    for row in _rows(key):
        p = raw[row.participant_id]
        var = rec.outcomes[row.task_num].var
        when = "ear" if p["arm"] == early_in else "lat"
        assert p["answers"][f"{var}{when}"] == float(row.response)


@needs_derived
def test_reqol_wording_follows_the_respondents_mode() -> None:
    raw = _raw()
    for row in _rows("reqol"):
        if row.task_num != 0:
            continue
        tel = raw[row.participant_id]["mode"] == 2
        assert row.outcome.startswith(REQOL1_TEL if tel else REQOL1_WEB)
    for row in _rows("ghq"):
        if row.condition.startswith("Earlier"):
            tel = raw[row.participant_id]["mode"] == 2
            assert (REQOL1_TEL in row.condition) == tel
            assert (REQOL1_WEB in row.condition) != tel


@needs_derived
def test_no_sequence_word_or_directive_reaches_a_row() -> None:
    for key in RECIPES:
        for row in _rows(key):
            text = row.condition + row.outcome
            assert "IF indmode" not in text and "[" not in text
            assert not any(f"{w}, I would" in text for w in ("First", "Next", "Finally"))


@needs_derived
def test_the_row_counts() -> None:
    assert len(_rows("reqol")) == 48548
    assert len(_rows("ghq")) == 36447
    assert all(GHQ_OPENING in r.outcome for r in _rows("ghq") if r.task_num == 0)


@needs_derived
def test_telephone_eq5d_options_are_in_the_second_person() -> None:
    """The first build gave telephone respondents the self-completion options
    ("I have ..."); over the phone they heard "You have ...". Found by the
    independent checker. Task 11 is EQ-5D mobility."""
    raw = _raw()
    seen = {True: 0, False: 0}
    for row in _rows("reqol"):
        if row.task_num != 11:
            continue
        tel = raw[row.participant_id]["mode"] == 2
        seen[tel] += 1
        if tel:
            assert '1 "You have no problems in walking about."' in row.outcome
            assert "I have no problems" not in row.outcome
            assert '3 means "You are confined to bed."' in row.outcome
        else:
            assert '1 "I have no problems in walking about."' in row.outcome
    assert seen[True] and seen[False]
    for row in _rows("ghq"):
        if row.condition.startswith("Earlier") and raw[row.participant_id]["mode"] == 2:
            assert '"You have no problems in walking about."' in row.condition
