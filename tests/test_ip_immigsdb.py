"""IP 9.16 — social desirability bias in attitudes to immigration, by item count.

Waves 8 and 9. Four groups, each a list answered with a count. What could go
wrong quietly, and the test for each:

1. **Which list a row shows.** The group comes from the household file, and
   wave 9's household file carries BOTH the wave 8 group and the wave 9 one;
   half the households changed group between them. The wrong one renders a
   different list over a real count, with every total reconciling.
2. **Allocation = routing.** Read from the raw files here, not from the
   generator: every answer must sit in the list its group was routed to.
3. **The order.** Statements were shuffled per respondent; each row must show
   THIS respondent's order, decoded here from the raw code.
4. **The words.** Checked against statements written here from the
   questionnaire, not from the recipe.
5. **Ethnicity in the persona**, kept by rich's ruling of 10 Oct 2026 although
   one condition names "Caribbean countries".

Failures report COUNTS only: this is UKDS End User Licence data, and an
assertion that printed a response or a persona would put it in a log.

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
GEN = REPO / "scripts" / "gen_ip_immigsdb.py"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"
# wave -> (file prefix, the allocation variable fielded THAT wave)
WAVES = {8: ("h", "ff_ictimw8"), 9: ("i", "ff_ictimw9")}

# From the questionnaire (Scaitemcount_ip8 / _ip9), deliberately not from the recipe.
# Numbered as the specification numbers them for the order code.
COMMON = [
    "The UK should increase assistance to the poor",
    "The UK should decrease the tax on diesel and petrol",
    "The UK should allow large corporations to pollute the environment",
]
SENSITIVE = {
    2: "The UK should allow people from Muslim countries to come and live here",
    3: "The UK should allow people from Eastern European countries to come and live here",
    4: "The UK should allow people from Caribbean countries to come and live here",
}
ANSWER_VAR = {1: "ictimc1", 2: "ictimt1", 3: "ictimt2", 4: "ictimt3"}
STEM = (
    "Of the following {n} statements, how many of them do you agree with? "
    "We don't want to know which statements, just how many."
)
QUESTION = "With how many items do you agree?"

# Answered (0..n) per group, counted once from the raw files by a script that
# shares no code with the generator or the pipeline.
CELLS = {
    8: {1: 514, 2: 532, 3: 525, 4: 562},
    9: {1: 488, 2: 531, 3: 523, 4: 529},
}


def _recipe_path(wave: int) -> Path:
    return REPO / "recipes" / f"ukds_6849_immigsdb_w{wave}.yaml"


def _derived(wave: int) -> Path:
    return REPO / "data" / "raw" / "ukds_6849" / f"immigsdb_w{wave}-derived.sav"


needs_deposit = pytest.mark.skipif(
    not (STATA / "h_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not all(_derived(w).exists() for w in WAVES),
    reason="derived files not built — run scripts/gen_ip_immigsdb.py --write",
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_immigsdb", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_immigsdb"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows(wave: int) -> tuple:
    return tuple(build_rows(spss.read(_derived(wave)), recipe.load(_recipe_path(wave))))


@functools.cache
def _raw(wave: int) -> dict[str, tuple[int, dict[str, float], dict[str, float]]]:
    """participant id -> (group, answers by var, order codes by var), from the raw files."""
    w, alloc = WAVES[wave]
    gen = _generator()
    ind = spss.read(STATA / f"{w}_indresp_ip.dta").df
    hh = spss.read(STATA / f"{w}_hhsamp_ip.dta").df[[f"{w}_hidp", f"{w}_{alloc}"]]
    group = dict(zip(hh[f"{w}_hidp"], hh[f"{w}_{alloc}"], strict=True))
    out = {}
    for _, r in ind.iterrows():
        g = group.get(r[f"{w}_hidp"])
        answers = {v: float(r[f"{w}_{v}"]) for v in ANSWER_VAR.values()}
        orders = {v: float(r[f"{w}_{v}o"]) for v in ANSWER_VAR.values()}
        out[f"ukds_6849:{gen.person_hash(int(r['pidp']))}"] = (
            -9 if g is None or g != g else int(g),
            answers,
            orders,
        )
    return out


def _routing_disagreements(wave: int, alloc: str) -> tuple[int, int]:
    """(answers in the routed list, answers anywhere else) under allocation `alloc`."""
    w, _ = WAVES[wave]
    ind = spss.read(STATA / f"{w}_indresp_ip.dta").df
    hh = spss.read(STATA / f"{w}_hhsamp_ip.dta").df[[f"{w}_hidp", f"{w}_{alloc}"]]
    df = ind.merge(hh, on=f"{w}_hidp", how="left", validate="many_to_one")
    routed = elsewhere = 0
    for code, var in ANSWER_VAR.items():
        answered = df[f"{w}_{var}"] >= 0
        routed += int((answered & (df[f"{w}_{alloc}"] == code)).sum())
        elsewhere += int((answered & (df[f"{w}_{alloc}"] != code)).sum())
    return routed, elsewhere


@needs_deposit
def test_the_generator_check_passes() -> None:
    gen = _generator()
    assert sum(gen.check(w) for w in gen.WAVES) == 0


@needs_deposit
def test_the_generator_check_fails_on_the_wave_8_group_at_wave_9(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The check must be able to fail: wave 9 under the wave 8 allocation."""
    gen = _generator()
    monkeypatch.setitem(gen.WAVES, "i", (9, 2016, "ff_ictimw8"))
    assert gen.check("i") > 500


@needs_deposit
@pytest.mark.parametrize("wave", [8, 9])
def test_allocation_equals_routing_in_the_raw_files(wave: int) -> None:
    routed, elsewhere = _routing_disagreements(wave, WAVES[wave][1])
    assert elsewhere == 0
    assert routed == sum(CELLS[wave].values())


@needs_deposit
def test_wave_9_routing_contradicts_the_carried_wave_8_group() -> None:
    """Why the wave 9 build must not read `i_ff_ictimw8`, which sits in the same file."""
    _, elsewhere = _routing_disagreements(9, "ff_ictimw8")
    assert elsewhere > 500


@needs_derived
@pytest.mark.parametrize("wave", [8, 9])
def test_each_row_shows_its_groups_list_and_carries_its_answer(wave: int) -> None:
    raw = _raw(wave)
    bad: dict[str, int] = dict.fromkeys(
        ("group", "stem", "statements", "response", "question", "factor"), 0
    )
    for row in _rows(wave):
        group, answers, _ = raw[row.participant_id]
        if group != row.condition_num + 1:
            bad["group"] += 1
            continue
        lines = row.condition.split("\n")
        n = 3 if group == 1 else 4
        bad["stem"] += lines[0] != STEM.format(n="three" if n == 3 else "four")
        expected = set(COMMON) | ({SENSITIVE[group]} if group in SENSITIVE else set())
        shown = [ln.removeprefix("• ") for ln in lines[1:]]
        bad["statements"] += len(shown) != n or set(shown) != expected
        bad["response"] += row.response_num != answers[ANSWER_VAR[group]]
        bad["question"] += not row.outcome.startswith(
            f"{QUESTION} Only return an integer from 0 to {n} "
        )
        want = (
            "none (control)" if group == 1 else SENSITIVE[group].split("from ")[1].split(" to")[0]
        )
        bad["factor"] += row.factors != {"sensitive_item": want}
    assert bad == dict.fromkeys(bad, 0)


@needs_derived
@pytest.mark.parametrize("wave", [8, 9])
def test_order_matches_the_raw_code_exactly(wave: int) -> None:
    """Decode the raw code against the questionnaire's numbering, line for line."""
    raw = _raw(wave)
    wrong = 0
    for row in _rows(wave):
        group, _, orders = raw[row.participant_id]
        numbered = COMMON + ([SENSITIVE[group]] if group in SENSITIVE else [])
        order = [int(ch) for ch in str(int(orders[ANSWER_VAR[group]]))]
        expected = [numbered[k - 1] for k in order]
        shown = [ln.removeprefix("• ") for ln in row.condition.split("\n")[1:]]
        wrong += shown != expected
    assert wrong == 0


@needs_derived
@pytest.mark.parametrize("wave", [8, 9])
def test_the_row_counts_per_cell(wave: int) -> None:
    per_cell: dict[int, int] = {}
    for row in _rows(wave):
        per_cell[row.condition_num + 1] = per_cell.get(row.condition_num + 1, 0) + 1
    assert per_cell == CELLS[wave]
    assert len({row.participant_id for row in _rows(wave)}) == len(_rows(wave))


@needs_derived
@pytest.mark.parametrize("wave", [8, 9])
def test_ethnicity_reaches_the_persona(wave: int) -> None:
    """Kept by rich's ruling of 10 Oct 2026, though one arm names "Caribbean countries"."""
    assert "racel_dv" in spss.read(_derived(wave)).df.columns
    assert recipe.load(_recipe_path(wave)).persona_map.get("ethnicity") == "racel_dv"
    missing = sum(1 for row in _rows(wave) if row.persona.ethnicity is None)
    assert missing < len(_rows(wave)) // 20


@needs_deposit
@pytest.mark.parametrize("defect", ["no group", "no order", "above the list length"])
def test_the_generator_check_counts_each_defect(
    monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    """Each term of `check` must be able to fire. None of them does on the real data."""
    gen = _generator()
    real = gen.derive

    def broken(w: str):
        d, labels = real(w)
        row = d.index[d["t1"] >= 0][0]
        if defect == "no group":
            d.loc[row, "group"] = -9.0
        elif defect == "no order":
            d.loc[row, "o_t1_1"] = float("nan")
        else:
            d.loc[row, "t1"] = 5.0
        return d, labels

    monkeypatch.setattr(gen, "derive", broken)
    assert gen.check("h") >= 1
