"""IP 9.17 — sexual identity by item counts, waves 8 and 9.

Three things here could go wrong quietly, and each has a test:

1. **Which list a row shows.** Lists A, C, E or B, D, F carried the sensitive
   statement depending on group, and the assignment flips between waves. A
   wrong flip renders the other list over a real count.

2. **The order.** Statements were shuffled per respondent. The row must show
   THIS respondent's order, decoded here independently from the raw code.

3. **The words.** Checked against stems and sensitive statements written here
   from the questionnaire.

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
GEN = REPO / "scripts" / "gen_ip_itemcount.py"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"
WAVES = {8: "h", 9: "i"}

# From the questionnaire, deliberately not from the recipe.
STEMS = {
    "ab": "I have at least once been sexually attracted to someone who …",
    "cd": "I have at least once had an experience of a sexual kind – for example kissing, "
    "cuddling or sexual intercourse – with a person who …",
    "ef": "I would describe myself as being …",
}
SENSITIVE_STATEMENT = {
    "ab": "is the same sex as me",
    "cd": "is the same sex as me",
    "ef": "gay, lesbian or bisexual",
}
LETTERS = "abcdef"


def _recipe_path(wave: int) -> Path:
    return REPO / "recipes" / f"ukds_6849_itemcount_w{wave}.yaml"


def _derived(wave: int) -> Path:
    return REPO / "data" / "raw" / "ukds_6849" / f"itemcount_w{wave}-derived.sav"


needs_deposit = pytest.mark.skipif(
    not (STATA / "h_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not all(_derived(w).exists() for w in WAVES),
    reason="derived files not built — run scripts/gen_ip_itemcount.py --write",
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_itemcount", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_itemcount"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows(wave: int) -> tuple:
    return tuple(build_rows(spss.read(_derived(wave)), recipe.load(_recipe_path(wave))))


@functools.cache
def _raw(wave: int) -> dict[str, tuple[int, dict[str, float]]]:
    """participant id -> (household group, raw order codes by list)."""
    w = WAVES[wave]
    gen = _generator()
    ind = spss.read(STATA / f"{w}_indresp_ip.dta").df
    hh = spss.read(STATA / f"{w}_hhsamp_ip.dta").df[[f"{w}_hidp", f"{w}_ff_ictsexw8"]]
    group = dict(zip(hh[f"{w}_hidp"], hh[f"{w}_ff_ictsexw8"], strict=True))
    out = {}
    for _, r in ind.iterrows():
        codes = {f"{x}{s}": float(r[f"{w}_ictsex{x}{s}o"]) for x in LETTERS for s in ("", "s")}
        g = group.get(r[f"{w}_hidp"])
        out[f"ukds_6849:{gen.person_hash(int(r['pidp']))}"] = (
            -9 if g is None else int(g),
            codes,
        )
    return out


@needs_deposit
def test_every_answer_sits_in_a_list_the_respondent_was_shown() -> None:
    gen = _generator()
    assert sum(gen.check(w) for w in gen.WAVES) == 0


@needs_derived
@pytest.mark.parametrize("wave", [8, 9])
def test_each_row_shows_the_right_list_in_the_respondents_own_order(wave: int) -> None:
    raw = _raw(wave)
    # Group 1 saw the sensitive statement in B, D, F at wave 8, and in A, C, E at wave 9.
    sensitive_in = {(8, 1): "bdf", (8, 2): "ace", (9, 1): "ace", (9, 2): "bdf"}
    for row in _rows(wave):
        group, codes = raw[row.participant_id]
        letter = LETTERS[row.task_num]
        pair = next(p for p in STEMS if letter in p)
        sensitive = letter in sensitive_in[(wave, group)]
        name = letter + ("s" if sensitive else "")
        body = row.condition.split("relevant for you. ", 1)[1]
        lines = body.split("\n")
        assert lines[0] == STEMS[pair]
        shown = [ln.removeprefix("• ") for ln in lines[1:]]
        assert (SENSITIVE_STATEMENT[pair] in shown) == sensitive
        assert len(shown) == (5 if sensitive else 4)
        # The raw code lists statement numbers in screen order; statement 1 of a
        # sensitive list is the sensitive statement.
        order = [int(ch) for ch in str(int(codes[name]))]
        if sensitive:
            assert shown[order.index(1)] == SENSITIVE_STATEMENT[pair]
        assert sorted(order) == list(range(1, len(shown) + 1))


@needs_derived
@pytest.mark.parametrize("wave", [8, 9])
def test_order_matches_the_raw_code_exactly(wave: int) -> None:
    """Decode the raw code against the declared list and compare line for line."""
    raw = _raw(wave)
    rec = recipe.load(_recipe_path(wave))
    for row in _rows(wave):
        _, codes = raw[row.participant_id]
        arm = next(a for a in rec.condition.arms if a.factors == row.factors)
        item = arm.items[row.task_num]
        assert item.outcome_var is not None and item.condition_text is not None
        declared = [ln.removeprefix("• ") for ln in item.condition_text.split("\n")[1:]]
        order = [int(ch) for ch in str(int(codes[item.outcome_var]))]
        expected = [declared[k - 1] for k in order]
        shown = [ln.removeprefix("• ") for ln in row.condition.split("\n")[1:]]
        assert shown == expected


@needs_derived
def test_the_row_counts() -> None:
    assert len(_rows(8)) == 12672
    assert len(_rows(9)) == 12320
