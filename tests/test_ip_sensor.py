"""IP 9.49 — consent to an in-home sensor, wave 17 (information x duration x feedback).

What could go wrong quietly, and the test for each:

1. **The wording.** The condition is the one part we write. Each of the 20 cells
   per mode carries its own version's consent text, its own duration fill and,
   only where promised, the feedback paragraph. Pinned against questionnaire text
   typed out below, never read from the recipe or the generator.

2. **The allocation.** Per household in `q_hhsamp_ip`; the answer is in the
   household file `q_hhresp_ip`. This file reads both itself and requires every
   row's condition to equal that allocation AND the routing: the row's own
   version's consent variable holds the answer and the other version's is not
   asked (ledger 138).

3. **Who answered.** The persona is the household-questions respondent
   (`q_ivh*`), from their own individual interview. A row must be that person.

4. **The exclusions.** CATI (the User Guide's documented script error), the one
   unallocated household and the households with no persona are counted here
   from the deposit.

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
GEN = REPO / "scripts" / "gen_ip_sensor.py"
MODES = {"ftf": 1, "web": 3}
RECIPE = {m: REPO / "recipes" / f"ukds_6849_sensor_consent_w17_{m}.yaml" for m in MODES}
DERIVED = REPO / "data" / "raw" / "ukds_6849" / "sensor_w17-derived.sav"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"

# ---------------------------------------------------------------------------
# From `6849_innovation_panel_wave_17_questionnaire.pdf`, household_ip17,
# ENVSENSINTRO / ENVSENSCONS1 / ENVSENSCONS2 (pp. 190-194), typed out here.
# Deliberately NOT from the recipe or the generator.
# ---------------------------------------------------------------------------
INTRO = "We know the conditions in our homes can be different according to where we live, even in different homes in the same street. The air can contain different levels of certain gases (such as carbon dioxide) and microscopic particles. These variations in air quality, as well as things like air temperature, humidity, noise levels and light levels, may affect our physical health, and how we feel – and might affect different people in different ways."  # noqa: E501
P1 = "To understand how conditions inside people's homes vary, we would like to invite some households to place a sensor in their home for a period of time. The sensor will record things about indoor conditions such as air temperature, humidity, noise levels (but not actual sounds), light levels, and the presence of certain gases and microscopic particles in the air. Information collected by these sensors would be linked to the answers you have given in this study."  # noqa: E501
P2 = "The sensor will be in your home for {d}, and the team will contact you to arrange its return when it is time to do so."  # noqa: E501
REPORT = "A personalised report giving a summary comparing the conditions in your home to the average home will be sent to you once we have analysed the data."  # noqa: E501
GBP20 = "Once you have returned the sensor, you will receive £20 as a thank you."
FULL = "If you agree: - We will send your name, address, telephone number, and – if you have provided it – email address to researchers at the University of Glasgow, who are partnering with Understanding Society to collect these data using sensors. - The University of Glasgow researchers will send you a sensor with simple instructions on how to use it. - The sensor will just need to be plugged in and left in a room until it is time to return it. You will not need to do anything with it until it is time to send it back. - When it is time to return the sensor, the University of Glasgow will contact you to arrange returning it via a courier service that they will pay for. - You will be asked to complete a short questionnaire about where the sensor was located while it was in your home and your experiences with this task. - Data from the sensor will be passed back to Understanding Society and connected to the answers you have given in this study. - We will make the combined anonymous data available for academic and policy research purposes only. - Access to the data will be restricted and controlled, to make sure that researchers use the information responsibly and safely."  # noqa: E501
BRIEF = "If you agree, we will send your name, address, telephone number, and – if you have provided it – email address to researchers at the University of Glasgow, who are partnering with Understanding Society to collect this data using sensors."  # noqa: E501
LIMITED = "The number of sensors available for this study is limited, so not everyone who agrees to have a sensor will be sent one. It may also be that those who are happy to help with this part of the research may have to wait until later in the year for a sensor to be available."  # noqa: E501
LEAFLET = {
    "ftf": 'Please read this leaflet on "In-Home Sensors" for further information.',
    "web": "Please read this leaflet for further information.",
}
ASK = {
    1: "Do you give permission for us to pass your name, address, telephone number, and email address to the University of Glasgow so they can send you a sensor to place in your home for {d}?",  # noqa: E501
    2: "Do you give permission for us to pass your name, address telephone number, and email address to the University of Glasgow so they can send you a sensor to place in your home for {d}?",  # noqa: E501
}
DUR = {
    1: "up to 6 months",
    2: "up to 12 months",
    3: "up to a year",
    4: "up to 24 months",
    5: "up to 2 years",
}

# Our own words, pinned so a change to them is a decision and not a drift.
LINKS = (
    'The screen also gave a link to the leaflet and a link headed "How will my data be linked?".'
)
HELP = "The screen also offered more information as help text, shown only if you clicked on it."


def _cell_of(n: int) -> tuple[int, int, int]:
    """condition_num -> (information version, duration code, feedback code)."""
    return n // 10 + 1, (n % 10) // 2 + 1, n % 2 + 1


def _expected_condition(mode: str, n: int) -> str:
    info, dur, fb = _cell_of(n)
    parts = [P1, P2.format(d=DUR[dur])]
    if fb == 1:
        parts.append(REPORT)
    parts += [GBP20, FULL if info == 1 else BRIEF, LIMITED, LEAFLET[mode]]
    body = " ".join(parts)
    if mode == "ftf":
        return (
            f'The interviewer read out this text: "{INTRO}" '
            f'The interviewer then read out this text: "{body}"'
        )
    text = f'You were shown this text on the web: "{INTRO}" You were then shown this text: "{body}" {LINKS}'  # noqa: E501
    return f"{text} {HELP}" if info == 2 else text


def _expected_outcome(n: int) -> str:
    info, dur, _ = _cell_of(n)
    return f'{ASK[info].format(d=DUR[dur])} 1 "Yes" 2 "No" Only return one of 1 or 2, nothing else.'


COUNTS = {
    "ftf": {0: 27, 1: 29, 2: 13, 3: 14, 4: 12, 5: 11, 6: 12, 7: 12, 8: 15, 9: 13,
            10: 29, 11: 27, 12: 16, 13: 8, 14: 15, 15: 20, 16: 19, 17: 13, 18: 15, 19: 19},
    "web": {0: 74, 1: 82, 2: 46, 3: 42, 4: 52, 5: 36, 6: 40, 7: 45, 8: 38, 9: 41,
            10: 78, 11: 80, 12: 34, 13: 40, 14: 44, 15: 36, 16: 31, 17: 34, 18: 38, 19: 35},
}  # fmt: skip
# Answered (Yes/No) households not built, by reason, computed from the deposit below.
NO_PERSONA = {"ftf": 7, "web": 36}
CATI_ANSWERED = 31
UNALLOCATED_ASKED = 1

needs_deposit = pytest.mark.skipif(
    not (STATA / "q_hhresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not DERIVED.exists(),
    reason="derived file not built — run scripts/gen_ip_sensor.py --write",
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_sensor", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_sensor"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows(mode: str) -> tuple:
    return tuple(build_rows(spss.read(DERIVED), recipe.load(RECIPE[mode])))


def _code(value: object) -> int | None:
    try:
        f = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return None if f != f else int(f)


def _pid(pidp: int) -> str:
    return "ukds_6849:ip_" + hashlib.sha256(f"ukds6849:{pidp}".encode()).hexdigest()[:12]


@functools.cache
def _deposit() -> list[dict[str, object]]:
    """One dict per household interview, read here, not by the generator.

    Dictionaries rather than DataFrame merges, so no join can raise an error that
    quotes a key. Nothing from this list is ever printed.
    """
    samp = spss.read(STATA / "q_hhsamp_ip.dta").df
    alloc = {
        h: (_code(i), _code(d), _code(f))
        for h, i, d, f in zip(
            samp["q_hidp"],
            samp["q_ff_esensinfow17"],
            samp["q_ff_esensdurw17"],
            samp["q_ff_esensfbw17"],
            strict=True,
        )
    }
    ind = spss.read(STATA / "q_indresp_ip.dta").df
    who = {
        (h, _code(p)): _pid(int(pidp))
        for h, p, pidp in zip(ind["q_hidp"], ind["q_pno"], ind["pidp"], strict=True)
    }
    hh = spss.read(STATA / "q_hhresp_ip.dta").df
    out = []
    for _, r in hh.iterrows():
        marked = [p for p in range(17) if _code(r[f"q_ivh{p}"]) == 1]
        info, dur, fb = alloc.get(r["q_hidp"], (None, None, None))
        out.append(
            {
                "mode": _code(r["q_modetype"]),
                "info": info,
                "dur": dur,
                "fb": fb,
                "c1": _code(r["q_envsenscons1"]),
                "c2": _code(r["q_envsenscons2"]),
                "n_marked": len(marked),
                "person": who.get((r["q_hidp"], marked[0])) if len(marked) == 1 else None,
            }
        )
    return out


def _arm(d: dict[str, object]) -> int | None:
    """The condition_num the allocation puts this household in, by the guide's codes."""
    if d["info"] not in (1, 2) or d["dur"] not in DUR or d["fb"] not in (1, 2):
        return None
    return (d["info"] - 1) * 10 + (d["dur"] - 1) * 2 + (d["fb"] - 1)  # type: ignore[operator]


def _own(d: dict[str, object]) -> object:
    return d["c1"] if d["info"] == 1 else d["c2"]


def _other(d: dict[str, object]) -> object:
    return d["c2"] if d["info"] == 1 else d["c1"]


# --- the generator ---------------------------------------------------------


@needs_deposit
def test_check_finds_routing_text_and_recipes_consistent() -> None:
    assert _generator().check() == 0


@needs_deposit
def test_check_counts_a_scrambled_allocation() -> None:
    gen = _generator()
    merged, _ = gen._joined()
    broken = merged.copy()
    broken["info"] = broken["info"].map({1: 2, 2: 1}).fillna(-9)
    assert gen.check_routing(broken) > 0


@needs_deposit
def test_check_counts_an_answer_in_the_other_versions_variable() -> None:
    gen = _generator()
    merged, _ = gen._joined()
    broken = merged.copy()
    who = broken.index[(broken["info"] == 1) & broken["envsenscons1"].isin([1, 2])][:1]
    broken.loc[who, "envsenscons2"] = 1
    assert gen.check_routing(broken) > 0


@needs_deposit
def test_check_counts_a_blank_in_the_own_version_variable() -> None:
    gen = _generator()
    merged, _ = gen._joined()
    broken = merged.copy()
    who = broken.index[(broken["info"] == 2) & (broken["modetype"] == 3)][:1]
    broken.loc[who, "envsenscons2"] = float("nan")
    assert gen.check_routing(broken) > 0


@needs_deposit
def test_check_counts_a_changed_exception() -> None:
    gen = _generator()
    merged, _ = gen._joined()
    # One fewer CATI version-2 household answering in error (asked, but refused).
    cati = merged.copy()
    who = cati.index[
        (cati["modetype"] == 2) & (cati["info"] == 2) & cati["envsenscons2"].isin([1, 2])
    ][:1]
    assert len(who) == 1
    cati.loc[who, "envsenscons2"] = -2
    assert gen.check_routing(cati) > 0
    # One more answered household losing its persona.
    lost = merged.copy()
    who = lost.index[(lost["modetype"] == 3) & (lost["indresp"] == 1)][:1]
    lost.loc[who, "indresp"] = 0
    assert gen.check_routing(lost) > 0
    # Two people recorded as answering the household questions.
    two = merged.copy()
    two.loc[two.index[:1], "n_hhq_resp"] = 2
    assert gen.check_routing(two) > 0


@needs_deposit
def test_check_counts_an_empty_cell() -> None:
    """Ledger 151: a declared cell with no rows is not a fully crossed factor."""
    gen = _generator()
    merged, _ = gen._joined()
    broken = merged.copy()
    gone = (broken["modetype"] == 1) & (broken["info"] == 2) & (broken["dur"] == 5)
    broken.loc[gone & (broken["fb"] == 1), "fb"] = 2
    assert gen.check_crossed(broken) > 0


def test_check_counts_text_missing_from_the_questionnaire() -> None:
    gen = _generator()
    assert gen.check_text(pdf="nothing here") > 0
    # A duration code mapped to the wrong words is caught against the PDF's fill notation.
    t = gen._pdf_text() if gen.QUEX.exists() else None
    if t is None:
        pytest.skip("questionnaire PDF not present")
    assert gen.check_text(pdf=t) == 0
    swapped = {**gen.DURATION, 2: gen.DURATION[3], 3: gen.DURATION[2]}
    original = gen.DURATION
    try:
        gen.DURATION = swapped
        gen.DURATION_FILL = " ".join(f"{w} {{if ff_esensdurw17 = {c}}}" for c, w in swapped.items())
        assert gen.check_text(pdf=t) > 0
    finally:
        gen.DURATION = original
        gen.DURATION_FILL = " ".join(
            f"{w} {{if ff_esensdurw17 = {c}}}" for c, w in original.items()
        )


@needs_deposit
def test_check_counts_a_recipe_that_drifted(tmp_path, monkeypatch) -> None:
    gen = _generator()
    merged, _ = gen._joined()
    assert gen.check_recipes(merged) == 0
    for mode, path in RECIPE.items():
        copy = tmp_path / path.name
        copy.write_text(path.read_text().replace("up to a year", "up to one year", 1))
        monkeypatch.setitem(gen.RECIPE, mode, copy)
    assert gen.check_recipes(merged) > 0


@needs_deposit
def test_check_exits_non_zero_when_it_finds_anything(monkeypatch) -> None:
    gen = _generator()
    monkeypatch.setattr(gen, "check", lambda: 1)
    monkeypatch.setattr(sys, "argv", ["gen_ip_sensor.py", "--check"])
    with pytest.raises(SystemExit) as exc:
        gen.main()
    assert exc.value.code not in (0, None)


def test_a_failed_join_never_quotes_its_keys() -> None:
    import pandas as pd

    gen = _generator()
    left = pd.DataFrame({"hidp": [918273645, 564738291]})
    right = pd.DataFrame({"hidp": [918273645, 918273645], "x": [1, 2]})
    with pytest.raises(gen.IdentifierSafeError) as exc:
        gen._merge(left, right, "hidp", "test join")
    assert "918273645" not in str(exc.value)
    broken_left = pd.DataFrame({"other": [918273645]})
    ok_right = pd.DataFrame({"hidp": [564738291], "x": [1]})
    with pytest.raises(gen.IdentifierSafeError) as exc2:
        gen._merge(broken_left, ok_right, "hidp", "test join")
    assert "918273645" not in str(exc2.value)
    assert exc2.value.__cause__ is None and exc2.value.__suppress_context__


@needs_deposit
def test_no_identifier_is_written_to_the_derived_file() -> None:
    frame, _ = _generator().derive()
    cols = " ".join(frame.columns)
    assert "pidp" not in cols and "hidp" not in cols and "pno" not in cols
    assert frame["person"].str.startswith("ip_").all()


# --- the built rows ---------------------------------------------------------


@needs_derived
@pytest.mark.parametrize("mode", list(MODES))
def test_each_condition_is_its_own_cells_text(mode: str) -> None:
    wrong = sum(r.condition != _expected_condition(mode, r.condition_num) for r in _rows(mode))
    assert wrong == 0


@needs_derived
@pytest.mark.parametrize("mode", list(MODES))
def test_each_outcome_is_its_own_cells_question(mode: str) -> None:
    wrong = sum(r.outcome != _expected_outcome(r.condition_num) for r in _rows(mode))
    assert wrong == 0


@needs_derived
@pytest.mark.parametrize("mode", list(MODES))
def test_rows_per_cell_and_answer_codes(mode: str) -> None:
    rows = _rows(mode)
    assert dict(collections.Counter(r.condition_num for r in rows)) == COUNTS[mode]
    assert sum(int(r.response) not in (1, 2) for r in rows) == 0
    assert {r.task_num for r in rows} == {0}
    assert len({r.participant_id for r in rows}) == len(rows)


@needs_derived
@pytest.mark.parametrize("mode", list(MODES))
def test_every_answer_in_the_deposit_is_a_row(mode: str) -> None:
    """The other direction, computed from the deposit alone."""
    expected: collections.Counter = collections.Counter()
    no_persona = 0
    for d in _deposit():
        if d["mode"] != MODES[mode] or _arm(d) is None or _own(d) not in (1, 2):
            continue
        if d["person"] is None:
            no_persona += 1
            continue
        expected[_arm(d)] += 1
    assert dict(expected) == COUNTS[mode]
    assert no_persona == NO_PERSONA[mode]


@needs_derived
@pytest.mark.parametrize("mode", list(MODES))
def test_each_rows_condition_is_its_allocation_and_its_routing(mode: str) -> None:
    by_person = {d["person"]: d for d in _deposit() if d["person"] is not None}
    off_allocation = off_routing = off_mode = 0
    for row in _rows(mode):
        d = by_person[row.participant_id]
        off_allocation += _arm(d) != row.condition_num
        off_mode += d["mode"] != MODES[mode]
        off_routing += _own(d) not in (1, 2)
        off_routing += _other(d) != -8
    assert off_allocation == 0
    assert off_mode == 0
    assert off_routing == 0


@needs_deposit
def test_allocation_matches_routing_in_every_household() -> None:
    """Ledger 138, from the deposit: version 1 asked ENVSENSCONS1 only, version 2
    ENVSENSCONS2 only, face-to-face and web; CATI version 1 never asked."""
    off = 0
    for d in _deposit():
        if d["mode"] in (1, 3) and d["info"] in (1, 2):
            off += _own(d) in (-8, None)
            off += _other(d) != -8
        if d["mode"] == 2:
            off += d["c1"] != -8
            off += d["info"] == 1 and d["c2"] != -8
    assert off == 0
    cati = sum(d["mode"] == 2 and d["c2"] in (1, 2) for d in _deposit())
    assert cati == CATI_ANSWERED
    unalloc = sum(
        d["info"] not in (1, 2) and (d["c1"] not in (-8, None) or d["c2"] not in (-8, None))
        for d in _deposit()
    )
    assert unalloc == UNALLOCATED_ASKED
    assert sum(d["n_marked"] != 1 for d in _deposit()) == 0


@needs_derived
def test_no_cati_or_unallocated_household_is_built() -> None:
    by_person = {d["person"]: d for d in _deposit() if d["person"] is not None}
    stray = sum(
        by_person[r.participant_id]["mode"] == 2 or _arm(by_person[r.participant_id]) is None
        for m in MODES
        for r in _rows(m)
    )
    assert stray == 0
