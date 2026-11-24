"""t936a's words against its fielded questionnaire, and its built rows against the
deposit and against SocSci210 (TESS2 053, Schnettler: two parental-investment
vignettes, each its own 2 x 2 x 2, built as t936a_feeding and t936a_time).

Three independent authorities, none of them the pipeline:

- the questionnaire: each arm's condition is re-derived here from the fielded
  DISPLAY screen (Q 491, Q 574) and the insert tables (Q 286-483), and must equal
  the recipe word for word;
- the deposit: the .sav carries the inserts each respondent's screen was filled
  with (Insertv1b1 .. Insertv2s2_3). Every built row's condition must equal the
  screen filled from THAT respondent's own inserts, which tests the XVIGN -> arm
  mapping without trusting it; and every (person, condition, task, response) is
  recomputed with pyreadstat;
- SocSci210: its eight tasks are our eight outcomes, and each task's row count and
  full response distribution (transcribed below from its parquet shard 0003,
  queried 2026-11-24) must equal ours exactly.

Tests needing the gitignored deposit or build skip on a fresh clone. A failure
never prints respondent rows, only counts.
"""

from __future__ import annotations

import re
from collections import Counter
from itertools import combinations
from pathlib import Path

import pandas as pd
import pyreadstat
import pytest

from micromotives_datasets.recipe import Recipe, load

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "t936a"
SAV = RAW / "TESS2_053_Schnettler_Client.sav"
QUEX = RAW / "TESS2 053 Schnettler_FINAL.txt"
RECIPES = {
    "feeding": REPO / "recipes" / "t936a_feeding.yaml",
    "time": REPO / "recipes" / "t936a_time.yaml",
}
BUILT = {e: REPO / "data" / "processed" / f"t936a_{e}.parquet" for e in RECIPES}

needs_raw = pytest.mark.skipif(not (SAV.exists() and QUEX.exists()), reason="t936a not fetched")
needs_built = pytest.mark.skipif(
    not (SAV.exists() and all(p.exists() for p in BUILT.values())), reason="t936a not built"
)

# experiment -> (assignment, DISPLAY line, insert-table line span, outcome vars by task)
DESIGN = {
    "feeding": ("XVIGN1", 491, (286, 384), {0: "QV11", 1: "QV12", 2: "QV13", 3: "QV15"}),
    "time": ("XVIGN2", 574, (385, 483), {0: "QV21", 1: "QV22", 2: "QV23", 3: "QV25"}),
}
# Questionnaire line of each outcome's wording.
QUESTION_LINE = {"QV11": 495, "QV12": 512, "QV13": 529, "QV15": 554}
QUESTION_LINE |= {"QV21": 577, "QV22": 594, "QV23": 611, "QV25": 637}

# SocSci210 t936a: task -> {response: rows}. Their tasks 0-3 are V1 (their
# condition 0), 4-7 are V2 (condition 1). 15,891 rows, 2,006 participants.
SOCSCI210 = {
    0: dict(zip(range(-5, 6), [125, 71, 141, 130, 101, 475, 96, 150, 231, 163, 311], strict=True)),
    1: dict(zip(range(-5, 6), [117, 71, 123, 120, 119, 448, 119, 157, 209, 169, 333], strict=True)),
    2: dict(zip(range(-5, 6), [51, 51, 139, 175, 147, 747, 115, 167, 190, 90, 115], strict=True)),
    3: dict(zip(range(-5, 6), [845, 188, 175, 89, 46, 435, 25, 26, 40, 31, 91], strict=True)),
    4: dict(zip(range(-5, 6), [44, 13, 23, 21, 29, 261, 56, 74, 143, 244, 1081], strict=True)),
    5: dict(zip(range(-5, 6), [38, 15, 31, 37, 29, 265, 76, 97, 149, 237, 1002], strict=True)),
    6: dict(zip(range(-5, 6), [32, 14, 38, 66, 60, 592, 90, 169, 272, 185, 466], strict=True)),
    7: dict(zip(range(0, 11), [23, 2, 14, 22, 26, 181, 105, 198, 301, 227, 886], strict=True)),
}
THEIR_TASK = {("feeding", t): t for t in range(4)} | {("time", t): t + 4 for t in range(4)}


def norm(s: str) -> str:
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("–", "-"), ("—", "-")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s.replace(" ", " ")).strip()


def quex_lines() -> list[str]:
    return QUEX.read_text(encoding="utf-8").split("\n")


def insert_table(start: int, end: int) -> dict[int, dict[str, str]]:
    """Code -> {insert name (lower case): value}, from the questionnaire's table."""
    out: dict[int, dict[str, str]] = {}
    code = None
    for line in quex_lines()[start - 1 : end]:
        line = line.strip()
        if re.fullmatch(r"[1-8]", line):
            code = int(line)
            out[code] = {}
        m = re.match(r"(Insertv\d\w+)=(.*)", line)
        if m:
            assert code is not None
            out[code][m.group(1).lower()] = norm(m.group(2))
    return out


def fill(screen: str, inserts: dict[str, str]) -> str:
    return norm(re.sub(r"\[(insertv\w+)\]", lambda m: inserts[m.group(1).lower()], screen))


def recipe(exp: str) -> Recipe:
    return load(RECIPES[exp])


@needs_raw
@pytest.mark.parametrize("exp", list(RECIPES))
def test_every_arm_is_the_fielded_screen_with_its_inserts(exp: str) -> None:
    var, line, span, _ = DESIGN[exp]
    screen = quex_lines()[line - 1]
    table = insert_table(*span)
    assert sorted(table) == list(range(1, 9))
    rec = recipe(exp)
    assert rec.condition.source_var == var
    arms = {a.raw: a for a in rec.condition.arms}
    assert sorted(arms) == list(range(1, 9))
    for code, arm in arms.items():
        assert arm.condition_num == code - 1
        assert norm(arm.text) == fill(screen, table[code]), code
        assert "[" not in arm.text


@needs_raw
def test_v2_follows_the_fielded_screen_not_the_specification() -> None:
    """Q 168 (the PI's specification) and Q 574 (the fielded DISPLAY) disagree."""
    q = quex_lines()
    spec, fielded = norm(q[167]), norm(q[573])
    assert "second recommendation" in spec and "first recommendation" in fielded
    assert "optimal way" in spec and "in the best way" in fielded
    assert "5.5 lb" not in spec and "(less than 5.5 lb)" in fielded
    for arm in recipe("time").condition.arms:
        text = norm(arm.text)
        assert "first recommendation" in text and "second recommendation" not in text
        assert "optimal" not in text and "developmental potential" not in text


@needs_raw
@pytest.mark.parametrize("exp", list(RECIPES))
def test_every_question_and_scale_end_is_in_the_questionnaire(exp: str) -> None:
    q = quex_lines()
    rec = recipe(exp)
    for o in rec.outcomes:
        assert o.var is not None
        line = norm(q[QUESTION_LINE[o.var] - 1])
        stem = re.sub(r"^QV\d\d\.\s*", "", line)
        if "[" in stem:  # the child's name, resolved per arm
            head, tail = stem.split("[")[0], stem.split("]")[1]
            for arm in rec.condition.arms:
                asked = arm.items[o.task_num].outcome_question
                assert asked is not None and asked.startswith(head) and asked.endswith(tail)
        else:
            assert o.question == stem, o.var
        block = "\n".join(norm(x) for x in q[QUESTION_LINE[o.var] : QUESTION_LINE[o.var] + 4])
        assert o.scale.min_label in block and o.scale.max_label in block, o.var


@needs_raw
def test_v1_question_names_the_formula_fed_child() -> None:
    table = insert_table(*DESIGN["feeding"][2])
    for arm in recipe("feeding").condition.arms:
        child = table[arm.raw]["insertv1s2_2"]
        assert child in {"Caroline", "Bob"}
        for task in (0, 1, 2):
            asked = arm.items[task].outcome_question
            assert asked is not None and asked.endswith(f"formula-feed {child}?")


@needs_raw
@pytest.mark.parametrize("exp", list(RECIPES))
def test_deposit_inserts_agree_with_the_questionnaire_table(exp: str) -> None:
    var, _, span, _ = DESIGN[exp]
    table = insert_table(*span)
    df, _ = pyreadstat.read_sav(str(SAV))
    cols = [c for c in df.columns if c.lower() in table[1]]
    assert len(cols) == 10
    for code, g in df.groupby(var):
        for c in cols:
            assert set(g[c].map(norm)) == {table[int(code)][c.lower()]}, (code, c)


@needs_raw
@pytest.mark.parametrize("exp", list(RECIPES))
def test_factors_decode_each_arm_and_every_minimal_pair_differs(exp: str) -> None:
    rec = recipe(exp)
    arms = rec.condition.arms
    for a in arms:
        assert set(a.factors) == set(rec.condition.factors)
    assert len({tuple(sorted(a.factors.items())) for a in arms}) == 8  # 2 x 2 x 2, no repeats
    for a, b in combinations(arms, 2):
        assert a.text != b.text
    for a in arms:  # each factor named in the text where it applies
        f = a.factors
        if exp == "feeding":
            assert f"her {f['nursed_child_birth_order']} child -" in a.text.replace("\n", " ")
            assert f"nursing for her {f['nursed_child']}'s development" in " ".join(a.text.split())
            assert f"- her {f['formula_fed_child']} " in " ".join(a.text.split())
        else:
            t = " ".join(a.text.split())
            lw, nw = f["low_weight_child"], f["normal_weight_child"]
            assert f"Their {f['low_weight_child_birth_order']} {lw} " in t
            assert re.search(rf"whereas their \S+ {nw} \w+ was born with normal", t)


def _deposit() -> pd.DataFrame:
    df, _ = pyreadstat.read_sav(str(SAV))
    return df


@needs_built
@pytest.mark.parametrize("exp", list(RECIPES))
def test_each_row_shows_the_screen_its_respondent_was_given(exp: str) -> None:
    """Fill the screen from the respondent's OWN insert columns, not from XVIGN."""
    _, line, span, _ = DESIGN[exp]
    screen = quex_lines()[line - 1]
    names = list(insert_table(*span)[1])
    df = _deposit()
    lookup = {c.lower(): c for c in df.columns}
    expected = {
        f"t936a:{idx}": fill(screen, {n: norm(str(r[lookup[n]])) for n in names})
        for idx, r in df.iterrows()
    }
    b = pd.read_parquet(BUILT[exp])
    wrong = sum(norm(c) != expected[p] for p, c in zip(b.participant_id, b.condition, strict=True))
    assert wrong == 0, wrong


@needs_built
@pytest.mark.parametrize("exp", list(RECIPES))
def test_built_rows_are_the_deposit_answers_exactly(exp: str) -> None:
    var, _, _, items = DESIGN[exp]
    df = _deposit()
    expected = set()
    for idx, r in df.iterrows():
        for task, v in items.items():
            code = r[v]
            if pd.isna(code) or code == -1:
                continue
            assert 1 <= code <= 11
            value = int(code) - 1 if v == "QV25" else int(code) - 6
            expected.add((f"t936a:{idx}", int(r[var]) - 1, task, value))
    b = pd.read_parquet(BUILT[exp])
    got = set(
        zip(
            b.participant_id,
            b.condition_num.astype(int),
            b.task_num.astype(int),
            b.response_num.astype(int),
            strict=True,
        )
    )
    assert len(got) == len(b)
    assert len(got - expected) == 0 and len(expected - got) == 0


@needs_built
def test_every_socsci210_task_matches_ours_exactly() -> None:
    rows = 0
    people: set[str] = set()
    for exp, path in BUILT.items():
        b = pd.read_parquet(path)
        rows += len(b)
        people |= set(b.participant_id)
        for task in range(4):
            ours = Counter(b[b.task_num == task].response_num.astype(int))
            assert dict(ours) == SOCSCI210[THEIR_TASK[(exp, task)]], (exp, task)
    assert rows == sum(sum(d.values()) for d in SOCSCI210.values()) == 15891
    assert len(people) == 2006


@needs_built
def test_no_recall_check_and_no_bracket_reaches_a_row() -> None:
    for path in BUILT.values():
        b = pd.read_parquet(path)
        assert not b.outcome.str.contains("Please mark everything").any()
        assert not b.outcome.str.contains(r"\[|\]", regex=True).any()
        assert not b.condition.str.contains(r"\[|\]|V1\.|V2\.", regex=True).any()
