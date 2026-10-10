"""IP 9.25 — consent to link HMRC records, wave 11 (wording x placement) and wave 15 (delivery).

What could go wrong quietly, and the test for each:

1. **The wording.** The condition is the one part we write. Each cell carries its
   own version's consent text, in its own mode's form, word-for-word. Pinned
   against questionnaire text written out below, never read from the recipe or
   the generator.

2. **The allocation.** Wave 11 allocates per person in `k_indresp_ip`, wave 15 per
   household in `o_hhsamp_ip`. This file reads both itself and requires every
   row's condition to equal that allocation AND the routing: the row's own
   version's consent variable holds the answer and no other version's is asked.

3. **The wave 11 script error** (Technical Report 5.3, Table 5.1). Face-to-face
   LATE respondents who may still have been on the laptop are excluded: 124
   standard and 103 easy rows, counted here from the deposit, and only late ones.

4. **The placement narration** (wave 11). "Earlier in the interview you were asked
   the questions that begin ..." must be true for every late row: each was asked
   the income and benefits questions.

5. **Who read it themselves** (wave 15, ledger 141). A self-completion row must
   be one whose self-completion was accepted as such (`scac`/`scac2` = 1); the
   CAPI cell is not filtered on the later `scac`.

6. **`--check` must be able to fail**, and must exit non-zero when it does.

UKDS rule: no assertion here compares or prints an identifier, a persona value
or a response value. Every comparison that touches respondents is reduced to a
COUNT first, so a failure message can only ever show a number.

These need the UKDS deposit, which is licensed and gitignored, so they skip when
it is absent rather than failing on a fresh clone.
"""

from __future__ import annotations

import collections
import copy
import functools
import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

from micromotives_datasets import recipe
from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.sources import spss

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_ip_hmrc.py"
# Recipe -> (wave, {condition_num: the wave's cell}). Wave 11's web cells are their
# own experiment; its face-to-face 2x2 is the other.
EXPERIMENTS = {
    "w11": (11, {0: 0, 1: 1, 2: 2, 3: 3}),
    "w11_web": (11, {0: 4, 1: 5}),
    "w15": (15, {n: n for n in range(5)}),
}
RECIPE = {k: REPO / "recipes" / f"ukds_6849_hmrc_consent_{k}.yaml" for k in EXPERIMENTS}
DERIVED = {w: REPO / "data" / "raw" / "ukds_6849" / f"hmrc_w{w}-derived.sav" for w in (11, 15)}
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"

# ---------------------------------------------------------------------------
# From `6849_ip_wave_11_questionnaires.pdf` (Hmrcconsentearly_ip11,
# Hmrcconsentlate_ip11, Benefits_w10) and `6849_ip_wave_15_questionnaire.pdf`
# (Hmrcconsent1/4_ip15, Casistart_ip15, Scahmrcconsent2/3_ip15), typed out here.
# Deliberately NOT from the recipe or the generator.
# ---------------------------------------------------------------------------
STANDARD = "We would like to add records held by HM Revenue and Customs, or HMRC, containing information on your employment and self-employment history, your income, National Insurance contributions and tax credits. All information will be used for research purposes only by academic or policy researchers under restricted access arrangements which make sure that the information is used responsibly and safely."  # noqa: E501
STANDARD_LEAFLET = "Please read this leaflet explaining how we would like to attach your HMRC records to the answers you have given in this study"  # noqa: E501
EASY = "We would like to add records held by HM Revenue and Customs, or HMRC, to the answers you have given in this study. If you agree: • We will send HMRC your name, address, sex and date of birth so that they can identify the records they have about you. The HMRC records contain information about your current and previous employment, your income, National Insurance contributions and tax credits. • We will not send HMRC the answers you have given in this study. • HMRC will send us your records. These will contain an anonymous identification number but not your name, address, sex or date of birth. • We will add the HMRC records to the answers you have given in this study. • We will make the combined anonymous data available for academic and policy research purposes only. • Access to the data will be restricted and controlled, to make sure that researchers use the information responsibly and safely. • This will not affect the way that you deal with HMRC in any way. Please read this leaflet for further information."  # noqa: E501
QUESTIONS = "Let me know if you have any questions."
QUESTION = "Do you give permission for us to pass your name, address, sex and date of birth to HMRC for this purpose?"  # noqa: E501
INTBENEFIT = "One of the most important parts of our research is how people are getting by financially these days. We have found that we need to ask about a number of different types of income, otherwise our results could be misleading. Please think about ALL of the extra sources of income you receive, as well as any benefits or tax credits."  # noqa: E501
SCAC = "I now have some questions for you to answer yourself on the computer."
SCAC2 = "I now have some questions for you to answer yourself on the computer. For the first one, I will read the question to you but do not tell me your answer. After reading the question, I will pass you the laptop so that you can enter your answer confidentially."  # noqa: E501
DIRECTOR = "Hello, I am Professor Michaela Benzeval, Director of Understanding Society. Linking your survey answers with administrative records while preserving the confidentiality of your data increases the value of the information you provide. Please read the following carefully."  # noqa: E501

# Our own words (docs/CONVENTIONS.md, narration and the layout exception), pinned
# so a change to them is a decision and not a drift.
EARLY = f'You had not been asked the questions that begin "{INTBENEFIT}" earlier in the interview.'
LATE = f'Earlier in the interview you were asked the questions that begin "{INTBENEFIT}"'
READ_OUT = "The interviewer then read out this text:"
ON_WEB = "You were shown this text on the web:"
LINKS = 'The screen also gave a link to the leaflet and a link, "How will my data be linked?", to a flowchart.'  # noqa: E501

STD_CAPI = f'"{STANDARD} {STANDARD_LEAFLET} and let me know if you have any questions."'
STD_WEB = f'"{STANDARD} {STANDARD_LEAFLET}."'
EASY_CAPI = f'"{EASY} {QUESTIONS}"'
EASY_SCREEN = f'"{EASY}"'

CONDITION = {
    11: {
        0: f"{EARLY} {READ_OUT} {STD_CAPI}",
        1: f"{LATE} {READ_OUT} {STD_CAPI}",
        2: f"{EARLY} {READ_OUT} {EASY_CAPI}",
        3: f"{LATE} {READ_OUT} {EASY_CAPI}",
        4: f"{ON_WEB} {STD_WEB} {LINKS}",
        5: f"{ON_WEB} {EASY_SCREEN} {LINKS}",
    },
    15: {
        0: f"The interviewer read out this text: {EASY_CAPI}",
        1: f'The interviewer said "{SCAC}" You then read this text on the laptop and answered '
        f"the question that followed yourself: {EASY_SCREEN} {LINKS}",
        2: f'The interviewer said "{SCAC2}" The interviewer then read out this text from a card '
        f"and handed you the card: {EASY_CAPI} The question that followed was on the laptop, "
        "and you entered your answer yourself.",
        3: f"You were shown this text on the web: {EASY_SCREEN} {LINKS}",
        4: "You were shown, on the web, a photo of the study director with this message: "
        f'"{DIRECTOR}" Below it you were shown this text: {EASY_SCREEN} {LINKS}',
    },
}
OPTIONS = {
    "capi_std": (
        "Respondent has read leaflet and is happy to give consent",
        "Respondent does not want to give consent",
    ),
    "web_std": (
        "I have read the leaflet and am happy to give consent",
        "I do not want to give consent",
    ),
    "yes_no": ("Yes", "No"),
}
ARM_OPTIONS = {
    11: {0: "capi_std", 1: "capi_std", 2: "yes_no", 3: "yes_no", 4: "web_std", 5: "yes_no"},
    15: dict.fromkeys(range(5), "yes_no"),
}
OWN_VAR = {
    11: {
        0: "consentq1",
        1: "consentq3",
        2: "consentq2",
        3: "consentq4",
        4: "consentq3",
        5: "consentq4",
    },
    15: {
        0: "hmrcconsentq1",
        1: "hmrcconsentq2",
        2: "hmrcconsentq3",
        3: "hmrcconsentq2",
        4: "hmrcconsentq4",
    },
}
CONSENT_VARS = {w: sorted(set(OWN_VAR[w].values())) for w in (11, 15)}
COUNTS = {
    "w11": {0: 426, 1: 251, 2: 383, 3: 266},
    "w11_web": {0: 649, 1: 632},
    "w15": {0: 252, 1: 217, 2: 208, 3: 949, 4: 927},
}
# Wave 11 script error (Technical Report 5.3, Table 5.1): answered face-to-face LATE
# rows excluded, by cell (1 standard late, 3 easy late).
SCRIPT_ERROR_ROWS = {1: 124, 3: 103}


def _expected_outcome(wave: int, arm: int) -> str:
    a, b = OPTIONS[ARM_OPTIONS[wave][arm]]
    return f'{QUESTION} 1 "{a}" 2 "{b}" Only return one of 1 or 2, nothing else.'


needs_deposit = pytest.mark.skipif(
    not (STATA / "k_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not all(p.exists() for p in DERIVED.values()),
    reason="derived files not built — run scripts/gen_ip_hmrc.py --write",
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_hmrc", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_hmrc"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows(key: str) -> tuple:
    wave = EXPERIMENTS[key][0]
    return tuple(build_rows(spss.read(DERIVED[wave]), recipe.load(RECIPE[key])))


def _cell(key: str, condition_num: int) -> int:
    return EXPERIMENTS[key][1][condition_num]


def _code(value: object) -> int | None:
    try:
        f = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return None if f != f else int(f)


def _pid(pidp: int) -> str:
    return "ukds_6849:ip_" + hashlib.sha256(f"ukds6849:{pidp}".encode()).hexdigest()[:12]


@functools.cache
def _deposit(wave: int) -> dict[str, dict[str, int | None]]:
    """participant id -> what the DEPOSIT says about them, read here, not by the generator.

    Dictionaries rather than DataFrame merges, so no join can raise an error
    that quotes a key. Nothing from this mapping is ever printed.
    """
    w = {11: "k", 15: "o"}[wave]
    ind = spss.read(STATA / f"{w}_indresp_ip.dta").df
    alloc: dict[object, tuple[int | None, int | None]] = {}
    if wave == 15:
        hh = spss.read(STATA / "o_hhsamp_ip.dta").df
        for h, c, web in zip(
            hh["o_hidp"], hh["o_ff_consentcasiw15"], hh["o_ff_consentwebw15"], strict=True
        ):
            alloc[h] = (_code(c), _code(web))
    out: dict[str, dict[str, int | None]] = {}
    for _, r in ind.iterrows():
        d: dict[str, int | None] = {"indmode": _code(r[f"{w}_indmode"])}
        for v in CONSENT_VARS[wave]:
            d[v] = _code(r[f"{w}_{v}"])
        if wave == 11:
            for v in (
                "condiffcapi",
                "condiffcawi",
                "conlocstand",
                "conloceasy",
                "benbase1",
                "finnow",
            ):
                d[v] = _code(r[f"{w}_{v}"])
            # Went through the early self-completion section (9.24 allocation 1 or 2)
            # with no self-completion interviewer number recorded for it. Kept as a
            # flag only: `casiintnoearly` is an interviewer number.
            d["casi_early_unreturned"] = int(
                _code(r["k_eq5dcond"]) in (1, 2) and _code(r["k_casiintnoearly"]) == -9
            )
        else:
            d["casi"], d["web"] = alloc.get(r["o_hidp"], (None, None))
            d["scac"], d["scac2"] = _code(r["o_scac"]), _code(r["o_scac2"])
        out[_pid(int(r["pidp"]))] = d
    return out


def _allocated_arm(wave: int, d: dict[str, int | None]) -> int | None:
    """The arm the allocation puts this person in, by the User Guide's codes."""
    if wave == 11:
        if d["indmode"] == 1:
            wording = d["condiffcapi"]
            place = d["conlocstand"] if wording == 1 else d["conloceasy"]
            return {(1, 1): 0, (1, 2): 1, (2, 1): 2, (2, 2): 3}.get((wording, place))  # type: ignore[arg-type]
        if d["indmode"] == 3:
            return {1: 4, 2: 5}.get(d["condiffcawi"])  # type: ignore[arg-type]
        return None
    if d["indmode"] == 1:
        return {1: 0, 2: 1, 3: 2}.get(d["casi"])  # type: ignore[arg-type]
    if d["indmode"] == 3:
        return {1: 3, 2: 4}.get(d["web"])  # type: ignore[arg-type]
    return None


def _self_completed(wave: int, arm: int, d: dict[str, int | None]) -> bool:
    if wave == 15 and arm == 1:
        return d["scac"] == 1
    if wave == 15 and arm == 2:
        return d["scac2"] == 1
    return True


def _script_error(wave: int, arm: int, d: dict[str, int | None]) -> bool:
    """Wave 11 face-to-face LATE, and possibly still on the laptop (Tech Report 5.3)."""
    return wave == 11 and arm in (1, 3) and d["casi_early_unreturned"] == 1


def _kept(wave: int, arm: int, d: dict[str, int | None]) -> bool:
    return _self_completed(wave, arm, d) and not _script_error(wave, arm, d)


# --- the generator ---------------------------------------------------------


@needs_deposit
def test_check_finds_routing_text_and_recipes_consistent() -> None:
    assert _generator().check() == 0


@needs_deposit
@pytest.mark.parametrize("wave", [11, 15])
def test_check_counts_a_scrambled_allocation(wave: int) -> None:
    gen = _generator()
    merged, _ = gen._joined(wave)
    broken = merged.copy()
    var = "condiffcapi" if wave == 11 else "ff_casi"
    broken[var] = broken[var].map({1: 2, 2: 1, 3: 3}).fillna(-9)
    assert gen.check_routing(broken, wave) > 0


@needs_deposit
@pytest.mark.parametrize("wave", [11, 15])
def test_check_counts_an_answer_in_another_versions_variable(wave: int) -> None:
    """Allocation intact, own question answered, but a second version's asked too."""
    gen = _generator()
    merged, _ = gen._joined(wave)
    broken = merged.copy()
    own, other = OWN_VAR[wave][0], OWN_VAR[wave][2]
    who = broken.index[broken[own].isin([1, 2])][:1]
    broken.loc[who, other] = 1
    assert gen.check_routing(broken, wave) > 0


@needs_deposit
def test_check_counts_a_swapped_placement() -> None:
    gen = _generator()
    merged, _ = gen._joined(11)
    broken = merged.copy()
    broken["conloceasy"] = broken["conloceasy"].map({1: 2, 2: 1}).fillna(-8)
    assert gen.check_routing(broken, 11) > 0


@needs_deposit
def test_check_counts_a_late_respondent_never_asked_about_income() -> None:
    gen = _generator()
    merged, _ = gen._joined(11)
    broken = merged.copy()
    broken.loc[broken["conlocstand"] == 2, "benbase1"] = -8
    assert gen.check_routing(broken, 11) > 0


@needs_deposit
def test_check_counts_a_changed_self_completion_exception() -> None:
    gen = _generator()
    merged, _ = gen._joined(15)
    broken = merged.copy()
    # One more CASI respondent "unable" to self-complete yet answering.
    who = broken.index[(broken["ff_casi"] == 2) & (broken["scac"] == 1) & (broken["indmode"] == 1)][
        :1
    ]
    broken.loc[who, "scac"] = 5
    assert gen.check_routing(broken, 15) > 0


@pytest.mark.parametrize("wave", [11, 15])
def test_check_counts_text_missing_from_the_questionnaire(wave: int) -> None:
    assert _generator().check_text(wave, pdf="nothing here") > 0


@needs_deposit
def test_check_counts_a_changed_script_error_exclusion() -> None:
    gen = _generator()
    merged, _ = gen._joined(11)
    broken = merged.copy()
    # One more answered late respondent from the early self-completion section
    # without a recorded self-completion interviewer.
    late = (
        (merged["indmode"] == 1) & (merged["conlocstand"] == 2) & merged["consentq3"].isin([1, 2])
    )
    who = broken.index[late & merged["eq5dcond"].isin([1, 2]) & (merged["casiintnoearly"] != -9)][
        :1
    ]
    assert len(who) == 1
    broken.loc[who, "casiintnoearly"] = -9
    assert gen.check_routing(broken, 11) > 0


@needs_deposit
def test_check_counts_a_script_error_flag_outside_face_to_face_late(monkeypatch) -> None:
    """The flag must never reach an early or web respondent, whose answers it would drop."""
    gen = _generator()
    merged, _ = gen._joined(11)
    original = gen._assignment

    def flag_one_early(df, wave):
        out = original(df, wave)
        early = out.index[(out["indmode"] == 1) & (out["placement"] == 1)][:1]
        out.loc[early, "scripterr"] = 1
        return out

    monkeypatch.setattr(gen, "_assignment", flag_one_early)
    assert gen.check_routing(merged, 11) > 0


@pytest.mark.parametrize("key", list(EXPERIMENTS))
def test_check_counts_a_recipe_that_drifted(key: str) -> None:
    gen = _generator()
    rec = yaml.safe_load(RECIPE[key].read_text())
    assert gen.check_recipe(key, rec) == 0
    drifted = copy.deepcopy(rec)
    drifted["condition"]["arms"][1]["text"] = drifted["condition"]["arms"][0]["text"]
    assert gen.check_recipe(key, drifted) > 0
    wrong_var = copy.deepcopy(rec)
    item = wrong_var["condition"]["arms"][0]["items"][0]
    item["outcome_var"] = next(
        v for v in CONSENT_VARS[EXPERIMENTS[key][0]] if v != item["outcome_var"]
    )
    assert gen.check_recipe(key, wrong_var) > 0
    gate = copy.deepcopy(rec)
    gate["condition"]["arms"][0]["raw_values"]["indmode"] = 2
    assert gen.check_recipe(key, gate) > 0


@needs_deposit
def test_check_exits_non_zero_when_it_finds_anything(monkeypatch) -> None:
    gen = _generator()
    monkeypatch.setattr(gen, "check", lambda wave=None: 1)
    monkeypatch.setattr(sys, "argv", ["gen_ip_hmrc.py", "--check"])
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
    assert exc.value.__cause__ is None and exc.value.__context__ is None

    broken_left = pd.DataFrame({"other": [918273645]})
    ok_right = pd.DataFrame({"hidp": [564738291], "x": [1]})
    with pytest.raises(gen.IdentifierSafeError) as exc2:
        gen._merge(broken_left, ok_right, "hidp", "test join")
    assert "918273645" not in str(exc2.value)
    assert exc2.value.__cause__ is None and exc2.value.__suppress_context__


@needs_deposit
@pytest.mark.parametrize("wave", [11, 15])
def test_no_identifier_is_written_to_the_derived_file(wave: int) -> None:
    frame, _ = _generator().derive(wave)
    assert "pidp" not in frame.columns
    assert "hidp" not in " ".join(frame.columns)
    assert frame["person"].str.startswith("ip_").all()


# --- the built rows ---------------------------------------------------------


@needs_derived
@pytest.mark.parametrize("key", list(EXPERIMENTS))
def test_each_condition_is_its_own_cells_text(key: str) -> None:
    wave = EXPERIMENTS[key][0]
    rows = _rows(key)
    wrong = sum(row.condition != CONDITION[wave][_cell(key, row.condition_num)] for row in rows)
    assert wrong == 0


@needs_derived
@pytest.mark.parametrize("key", list(EXPERIMENTS))
def test_each_outcome_is_its_own_cells_question_and_options(key: str) -> None:
    wave = EXPERIMENTS[key][0]
    rows = _rows(key)
    wrong = sum(
        row.outcome != _expected_outcome(wave, _cell(key, row.condition_num)) for row in rows
    )
    assert wrong == 0


@needs_derived
@pytest.mark.parametrize("key", list(EXPERIMENTS))
def test_rows_per_cell_and_answer_codes(key: str) -> None:
    rows = _rows(key)
    assert dict(collections.Counter(r.condition_num for r in rows)) == COUNTS[key]
    assert sum(int(r.response) not in (1, 2) for r in rows) == 0
    assert {r.task_num for r in rows} == {0}
    assert len({r.participant_id for r in rows}) == len(rows)


@needs_derived
@pytest.mark.parametrize("key", list(EXPERIMENTS))
def test_every_answer_in_the_deposit_is_a_row(key: str) -> None:
    """The other direction, computed from the deposit alone."""
    wave, cells = EXPERIMENTS[key]
    by_cell = {cell: num for num, cell in cells.items()}
    expected: collections.Counter = collections.Counter()
    for d in _deposit(wave).values():
        arm = _allocated_arm(wave, d)
        if arm not in by_cell or not _kept(wave, arm, d):  # type: ignore[arg-type]
            continue
        if d[OWN_VAR[wave][arm]] in (1, 2):  # type: ignore[index]
            expected[by_cell[arm]] += 1  # type: ignore[index]
    assert dict(expected) == COUNTS[key]


@needs_derived
@pytest.mark.parametrize("key", list(EXPERIMENTS))
def test_each_rows_condition_is_its_allocation_and_its_routing(key: str) -> None:
    wave = EXPERIMENTS[key][0]
    dep = _deposit(wave)
    off_allocation = off_routing = 0
    for row in _rows(key):
        d = dep[row.participant_id]
        arm = _cell(key, row.condition_num)
        own = OWN_VAR[wave][arm]
        off_allocation += _allocated_arm(wave, d) != arm
        off_routing += d[own] not in (1, 2)
        off_routing += sum(d[v] not in (-8, None) for v in CONSENT_VARS[wave] if v != own)
    assert off_allocation == 0
    assert off_routing == 0


@needs_derived
def test_wave11_script_error_rows_are_excluded_and_counted() -> None:
    """Technical Report 5.3: late respondents possibly still on the laptop."""
    dep = _deposit(11)
    lost: collections.Counter = collections.Counter()
    for d in dep.values():
        arm = _allocated_arm(11, d)
        if arm is not None and _script_error(11, arm, d) and d[OWN_VAR[11][arm]] in (1, 2):
            lost[arm] += 1
    assert dict(lost) == SCRIPT_ERROR_ROWS
    built = sum(
        dep[r.participant_id]["casi_early_unreturned"] == 1
        for r in _rows("w11")
        if r.condition_num in (1, 3)
    )
    assert built == 0
    # The exclusion is LATE only: early respondents with the same record are kept,
    # because their consent came before the early self-completion section.
    early_kept = sum(
        dep[r.participant_id]["casi_early_unreturned"] == 1
        for r in _rows("w11")
        if r.condition_num in (0, 2)
    )
    assert early_kept > 0


@needs_derived
def test_wave11_placement_narration_is_true() -> None:
    dep = _deposit(11)
    rows = _rows("w11")
    late = [r for r in rows if LATE in r.condition]
    early = [r for r in rows if EARLY in r.condition]
    assert len(late) + len(early) == len(rows)
    assert {r.condition_num for r in late} == {1, 3}
    assert {r.condition_num for r in early} == {0, 2}
    unasked = sum(
        dep[r.participant_id][v] in (-8, None) for r in late for v in ("benbase1", "finnow")
    )
    assert unasked == 0
    # The web experiment declares no placement and narrates none.
    web = _rows("w11_web")
    narrated = sum(INTBENEFIT in r.condition for r in web)
    assert narrated == 0
    assert all(dep[r.participant_id]["indmode"] == 3 for r in web)
    assert all(dep[r.participant_id]["indmode"] == 1 for r in rows)


@needs_derived
def test_wave15_self_completion_rows_read_and_answered_it_themselves() -> None:
    dep = _deposit(15)
    rows = _rows("w15")
    not_self = sum(not _self_completed(15, r.condition_num, dep[r.participant_id]) for r in rows)
    assert not_self == 0
    # The CAPI cell is NOT filtered on the later scac: some of its rows declined or
    # needed help with self-completion afterwards, and must still be there.
    capi_later_declined = sum(
        r.condition_num == 0 and dep[r.participant_id]["scac"] not in (1, None) for r in rows
    )
    assert capi_later_declined > 0
    # Telephone and proxy respondents are never in the experiment.
    assert sum(dep[r.participant_id]["indmode"] not in (1, 3) for r in rows) == 0
