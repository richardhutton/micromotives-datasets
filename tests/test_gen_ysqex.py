"""The ysqex recipe (TESS 146, Golebiowska: political candidates who are atheist, not
sure there is a God, or of no religion) and its answer keys.

The generator reads every outcome wording out of the fielded questionnaire, in both its
simple and its programming copy, and resolves the RND_01 group fill the way each arm's
screen did. These tests stop a hand edit drifting from it, and check the facts the rows
rest on:

- three arms, raw code = condition_num + 1, each arm's text quoting its own group, and
  every outcome an arm carries naming that group and no other;
- Q1's 77/98/99 are real thermometer degrees, so they must survive while 777/998/999
  and the 98 skips on the other items are dropped;
- the built rows reproduce every (arm, outcome) count and mean computed from the .dta,
  a file the build never reads, and every (person, arm, task, response) tuple;
- every outcome's whole-sample distribution equals NORC's unweighted frequency table.

Tests needing the gitignored deposit or build skip on a fresh clone. No assertion
prints a row: failures report sizes and cell keys only.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_ysqex.py"
RECIPE = REPO / "recipes" / "ysqex.yaml"
RAW = REPO / "data" / "raw" / "ysqex"
DTA = RAW / "TESS 146 Golebiowska_Final Data24Apr30.dta"
FREQ = RAW / "9089.146 TESS 146 Golebiowska_Frequencies.xlsx"
BUILT = REPO / "data" / "processed" / "ysqex.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_ysqex", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not DTA.exists(), reason="ysqex deposit not fetched")
needs_built = pytest.mark.skipif(not (BUILT.exists() and DTA.exists()), reason="ysqex not built")

OUTCOMES = gen.OUTCOME_VARS
GROUPS = {
    0: "political candidates who are atheist",
    1: "political candidates who are not sure there is a God",
    2: "political candidates who do not currently identify with a religion",
}
TOP = {"Q1": 100, "Q2A": 7, "Q2B": 7, "Q2C": 7, "Q2D": 7, "Q5": 7}  # else 10

# Computed from the .dta when the recipe was written (2026-11-23):
# (condition_num, task_num) -> (answers, mean).
CELLS = {
    (0, 0): (342, 49.146),
    (0, 1): (447, 4.414),
    (0, 2): (449, 4.445),
    (0, 3): (450, 4.369),
    (0, 4): (448, 4.243),
    (0, 5): (446, 2.769),
    (0, 6): (445, 2.355),
    (0, 7): (445, 2.335),
    (0, 8): (448, 3.614),
    (0, 9): (446, 3.052),
    (0, 10): (449, 4.857),
    (1, 0): (312, 49.907),
    (1, 1): (416, 4.216),
    (1, 2): (416, 4.209),
    (1, 3): (416, 4.243),
    (1, 4): (414, 4.051),
    (1, 5): (413, 3.324),
    (1, 6): (415, 2.802),
    (1, 7): (413, 2.639),
    (1, 8): (418, 3.632),
    (1, 9): (417, 2.861),
    (1, 10): (421, 4.648),
    (2, 0): (289, 57.138),
    (2, 1): (396, 4.730),
    (2, 2): (399, 4.764),
    (2, 3): (398, 4.736),
    (2, 4): (396, 4.662),
    (2, 5): (393, 2.636),
    (2, 6): (394, 2.208),
    (2, 7): (390, 2.023),
    (2, 8): (397, 4.438),
    (2, 9): (395, 3.233),
    (2, 10): (397, 5.166),
}


@needs_raw
def test_recipe_is_what_the_generator_writes() -> None:
    assert RECIPE.read_text() == gen.render()


def test_fill_resolves_by_code() -> None:
    t = (
        "toward [IF RND_01=1:political candidates who are atheist, IF RND_01=2:political "
        "candidates who are not sure there is a God, IF RND_01=3:political candidates who do "
        "not currently identify with a religion]."
    )
    for code in (1, 2, 3):
        assert gen.resolve(t, code) == f"toward {GROUPS[code - 1]}."
    with pytest.raises(SystemExit):
        gen.resolve("toward [IF RND_01=1:atheists, IF RND_01=2:agnostics].", 1)


def test_arms_quote_their_own_group() -> None:
    rec = load(RECIPE)
    arms = sorted(rec.condition.arms, key=lambda a: a.condition_num)
    assert [(a.raw, a.condition_num) for a in arms] == [(1, 0), (2, 1), (3, 2)]
    assert rec.condition.source_var == "RND_01"
    assert rec.condition.shared_context is None
    for a in arms:
        assert a.text == f'This set of survey questions was about "{GROUPS[a.condition_num]}".'


def test_every_outcome_names_its_arms_group_only() -> None:
    rec = load(RECIPE)
    assert [o.var for o in rec.outcomes] == OUTCOMES
    for a in rec.condition.arms:
        assert sorted(a.items) == list(range(len(OUTCOMES)))
        for t, item in a.items.items():
            q = (item.outcome_question or "").lower()
            assert GROUPS[a.condition_num].lower() in q, (a.condition_num, t)
            for other, g in GROUPS.items():
                if other != a.condition_num:
                    assert g.lower() not in q, (a.condition_num, t, other)


def test_no_sequence_or_markup_leaks_into_wordings() -> None:
    rec = load(RECIPE)
    for a in rec.condition.arms:
        for item in a.items.values():
            q = item.outcome_question or ""
            assert not re.search(r"<u>|</u>|\[|\]|RND_|GRID|RANDOMIZE|  ", q), q


def test_q1_keeps_its_high_degrees_and_drops_its_own_non_answers() -> None:
    rec = load(RECIPE)
    q1 = next(o for o in rec.outcomes if o.var == "Q1")
    assert q1.response_recode == {i: i for i in range(101)}
    # 77, 98 and 99 are degrees on Q1; a study-level missing code would delete them.
    assert not {77, 98, 99} & set(rec.missing_codes)
    assert set(rec.missing_codes) == {777, 998, 999}
    # On the other items 77/98/99 are non-answers: dropped because outside the recode.
    for o in rec.outcomes:
        if o.var != "Q1":
            assert o.response_recode is not None
            assert not {77, 98, 99} & set(o.response_recode), o.var


@needs_raw
def test_generator_rejects_a_drifted_codebook_item(monkeypatch: pytest.MonkeyPatch) -> None:
    real = gen.codebook_items()
    drifted = dict(real, Q3B="Anger")
    monkeypatch.setattr(gen, "codebook_items", lambda: drifted)
    with pytest.raises(SystemExit):
        gen.recipe()


def _deposit() -> pd.DataFrame:
    import pyreadstat

    df, _ = pyreadstat.read_dta(str(DTA))
    return df


def _expected() -> set[tuple[str, int, int, int]]:
    df = _deposit()
    out = set()
    for _, r in df.iterrows():
        arm = int(r.RND_01) - 1
        for task, var in enumerate(OUTCOMES):
            code = r[var]
            if pd.isna(code) or code > TOP.get(var, 10):
                continue
            out.add((f"ysqex:{int(r.CaseId)}", arm, task, int(code)))
    return out


@needs_built
def test_built_rows_are_the_deposit_answers_exactly() -> None:
    b = pd.read_parquet(BUILT)
    got = set(
        zip(
            b.participant_id,
            b.condition_num.astype(int),
            b.task_num.astype(int),
            b.response_num.astype(int),
            strict=True,
        )
    )
    expected = _expected()
    assert len(got) == len(b) == 13530
    assert b.participant_id.nunique() == 1274
    # Compare sizes, not the sets themselves: a failure must not print rows.
    assert len(got - expected) == 0 and len(expected - got) == 0


@needs_built
def test_cell_counts_and_means() -> None:
    b = pd.read_parquet(BUILT)
    for (arm, task), (n, mean) in CELLS.items():
        g = b[(b.condition_num == arm) & (b.task_num == task)]
        assert len(g) == n, (arm, task)
        assert round(float(g.response_num.mean()), 3) == mean, (arm, task)


def _norc_frequencies() -> dict[str, dict[int, int]]:
    """NORC's unweighted frequency table: variable -> {code: count}, codes as printed."""
    import openpyxl

    ws = openpyxl.load_workbook(FREQ, read_only=True)["Unweighted_Frequency"]
    out: dict[str, dict[int, int]] = {}
    cur: str | None = None
    for row in ws.iter_rows(values_only=True):
        head = row[0]
        if isinstance(head, str) and head.split(" ", 1)[0] in OUTCOMES:
            cur = head.split(" ", 1)[0]
            out[cur] = {}
            continue
        if cur is None or not isinstance(row[1], str):
            continue
        if row[1] == "Total":
            cur = None
            continue
        m = re.match(r"(\d+)\b", row[1])
        if m:
            out[cur][int(m.group(1))] = int(row[2])
    return out


@needs_built
def test_built_distribution_matches_norcs_frequency_tables() -> None:
    freq = _norc_frequencies()
    assert sorted(freq) == sorted(OUTCOMES)
    b = pd.read_parquet(BUILT)
    for task, var in enumerate(OUTCOMES):
        norc = {k: n for k, n in freq[var].items() if k <= TOP.get(var, 10)}
        built = b[b.task_num == task].response_num.astype(int).value_counts().to_dict()
        assert built == norc, var
        assert sum(freq[var].values()) == 1274, var


@needs_built
def test_one_condition_per_arm_and_household_size_rendered() -> None:
    b = pd.read_parquet(BUILT)
    assert b.groupby("condition_num").condition.nunique().to_dict() == {0: 1, 1: 1, 2: 1}
    share = float(b.persona.str.contains(r'"household_size":\s?[1-5]\b', regex=True).mean())
    assert share > 0.85, share
