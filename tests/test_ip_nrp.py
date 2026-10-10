"""IP 9.23 — non-resident parents: Family Networks and Fertility History in either order, wave 10.

What could go wrong quietly, and the test for each:

1. **The wording.** The condition is the one part we write. Pinned against text
   written out below from `6849_ip_wave_10_questionnaires.pdf`, never read from
   the recipe or the generator, per condition and per mode.

2. **The order.** The deposit names variables by group, not by slot, and a label
   can be reversed (ledger 138). The order is read here off the Non-Resident
   Identifier module, which follows the FIRST module, independently of the
   generator; and every row's condition must follow from its household's code.

3. **Allocation = routing.** Nobody answers the other group's variables; every
   answer in the deposit is a row and no row appears from nowhere.

4. **The persona.** The Fertility History half must not carry children in the
   household (same domain); no condition may name the respondent's sex.

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
GEN = REPO / "scripts" / "gen_ip_nrp.py"
RECIPE = {
    "fh": REPO / "recipes" / "ukds_6849_nrp_w10_fh.yaml",
    "contact": REPO / "recipes" / "ukds_6849_nrp_w10_contact.yaml",
}
DERIVED = REPO / "data" / "raw" / "ukds_6849" / "nrp_w10-derived.sav"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"

# ---------------------------------------------------------------------------
# From the wave 10 questionnaire, modules Familynetworksa/b_ip10 (Lvreladp1/2,
# Masee .. Chcon) and Fertilityhistorya/b_ip10 (Fertintroadp, Ladopted, Lstep,
# Lprntadp). Typed out here; deliberately NOT imported from the generator.
# ---------------------------------------------------------------------------
FN_FIRST = "We now have a few questions about family members who are not living here with you."
FN_LATE_ADDS = (
    "We realise that we might be asking you to repeat some information that you gave us "
    "earlier in the survey. However, it's really important that we record all this information "
    "here, so please make sure you tell us about all your family members who don't live with "
    "you, even if you've mentioned them before."
)
RELATIVES_CAPI = (
    "Excluding relatives who are living in this household with you at the moment, can you tell "
    "me which of these types of relatives you have alive at the moment? Please tell me about all "
    "relatives, even those you aren't in contact with."
)
RELATIVES_WEB = (
    "Excluding relatives who are living in this household with you at the moment, please select "
    "the types of relatives you have alive at the moment? Please tell us about all relatives, "
    "even those you aren't in contact with."
)
RELATIVES_OPTIONS = (
    '"Mother" / "Father" / "Brothers/sisters" / "Grandchildren" / "Grandparents" / '
    '"Great Grandchildren" / "Great Grandparents" / "Step/adoptive mother" / '
    '"Step/adoptive father" / "Biological Son(s)/daughter(s)" / "Adopted Son(s)/daughter(s)" / '
    '"Step Son(s)/daughter(s)" / "None of these"'
)
FH_FIRST = (
    "The next questions are about any children you have or have ever had - including "
    "biological, adopted and step-children."
)
FH_INTRO = (
    f"{FH_FIRST} Because family life is changing and many more parents nowadays don't live "
    "with their children, it's really important to us that Understanding Society builds an "
    "accurate picture of what family life in the UK looks like. So, we're asking people about "
    "all of their children. So, as well as telling me about any children you currently live "
    "with, please make sure you tell me about any children you don't live with - including "
    "children you were never or are no longer in touch with, or any who may have died."
)
FH_LATE_ADDS = (
    "We realise that we might be asking you to repeat some information that you gave us "
    "earlier in the survey. However, it's really important that we record all this information "
    "here, so please make sure you tell us about all your children, even if you've mentioned "
    "them before."
)
ADOPTED = (
    "Have you ever adopted a child? Please include any adopted children, even if you are not "
    "living with them or are not in touch with them."
)
STEP = (
    "Have you ever lived with any step-children? Please include any step children you're "
    "currently living with and any that you've lived with in the past - even if you're no "
    "longer in touch with them."
)
BIO = (
    "Have you ever {verb} any biological children? Please include all children, including any "
    "you never lived or no longer live with, or are not in touch with."
)
SECTION = "The question that follows was part of a section introduced with:"

# (condition_num, interviewer-administered?) -> condition, as the respondent met it.
FH_CONDITION = {
    (0, True): (
        f'You had not been asked the questions that begin "{FN_FIRST}" earlier in the '
        f'interview. {SECTION} "{FH_INTRO}"'
    ),
    (1, True): (
        f'Earlier in the interview you were asked: "{FN_FIRST} {RELATIVES_CAPI}" '
        f'{RELATIVES_OPTIONS} {SECTION} "{FH_INTRO} {FH_LATE_ADDS}"'
    ),
    (1, False): (
        f'Earlier in the interview you were asked: "{FN_FIRST} {RELATIVES_WEB}" '
        f'{RELATIVES_OPTIONS} {SECTION} "{FH_INTRO} {FH_LATE_ADDS}"'
    ),
}
FH_CONDITION[(0, False)] = FH_CONDITION[(0, True)]

CONTACT_CONDITION = {
    (0, True): (
        f'You had not been asked the questions that begin "{FH_FIRST}" earlier in the '
        f'interview. {SECTION} "{FN_FIRST}"'
    ),
    (1, True): (
        f'Earlier in the interview you were asked the questions that begin: "{FH_INTRO}" '
        f'"{ADOPTED}" "Yes" / "No" "{STEP}" "Yes" / "No" {SECTION} "{FN_FIRST} {FN_LATE_ADDS}"'
    ),
    (1, False): (
        f'Earlier in the interview you were asked the questions that begin: "{FH_INTRO}" '
        f'"{ADOPTED}" "Yes" / "No" "{STEP}" "Yes" / "No" {SECTION} "{FN_FIRST}"'
    ),
}
CONTACT_CONDITION[(0, False)] = CONTACT_CONDITION[(0, True)]

FREQ = (
    '1 "Daily" 2 "At least once per week" 3 "At least once per month" '
    '4 "Several times per year" 5 "Less often" 6 "Never" Only return an integer from 1 to 6 '
    'where 1 means "Daily" and 6 means "Never", nothing else.'
)
YES_NO = '1 "Yes" 2 "No" Only return one of 1 or 2, nothing else.'
MOTHER = (
    "If you have both a biological and a step or adoptive mother, we are interested in knowing "
    "about the one with whom you have the most contact."
)
FATHER = (
    "If you have both a biological and a step or adoptive father, we are interested in knowing "
    "about the one with whom you have the most contact."
)
# task -> (question as read by an interviewer, sentence the web adds or "")
CONTACT_Q = {
    0: (
        "Thinking about your mother. Other than via Skype or webcam, how often do you see your "
        "mother?",
        MOTHER,
    ),
    1: (
        "And how often do you have contact by telephone, email, letter, Skype or webcam with "
        "your mother?",
        MOTHER,
    ),
    2: (
        "Thinking now about your father. Other than via Skype or webcam, how often do you see "
        "your father?",
        FATHER,
    ),
    3: (
        "And how often do you have contact by telephone, email, letter, Skype or webcam with "
        "your father?",
        FATHER,
    ),
    4: (
        "Thinking now about your children aged 18 or over. If you have more than one son or "
        "daughter aged 18 or over not living with you please think about the one with whom you "
        "have the most contact. Apart from via Skype or webcam, how often do you see your "
        "son/daughter?",
        "",
    ),
    5: (
        "And how often do you have contact by telephone, email, letter, Skype or webcam with "
        "your son/daughter (aged 18 or over)?",
        "If you have more than one son or daughter aged 18 or over not living with you, we are "
        "interested in knowing about the one with whom you have the most contact.",
    ),
}
FH_VARS = ("ladopted", "lstep", "lprntadp")
CONTACT_VARS = ("masee", "macon", "pasee", "pacon", "chsee", "chcon")

# Counted on the built rows 10 Oct 2026, aggregates only: (condition, task) -> rows.
FH_CELLS = {(0, 0): 1196, (0, 1): 1197, (0, 2): 1194, (1, 0): 1270, (1, 1): 1268, (1, 2): 1267}
CONTACT_CELLS = {
    (0, 0): 529,
    (0, 1): 528,
    (0, 2): 446,
    (0, 3): 446,
    (0, 4): 517,
    (0, 5): 518,
    (1, 0): 484,
    (1, 1): 485,
    (1, 2): 405,
    (1, 3): 405,
    (1, 4): 463,
    (1, 5): 464,
}


needs_deposit = pytest.mark.skipif(
    not (STATA / "j_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not DERIVED.exists(),
    reason="derived file not built — run scripts/gen_ip_nrp.py --write",
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_nrp", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_nrp"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows(kind: str) -> tuple:
    return tuple(build_rows(spss.read(DERIVED), recipe.load(RECIPE[kind])))


def _code(value: object) -> int | None:
    try:
        f = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return None if f != f else int(f)


@functools.cache
def _deposit() -> dict[str, dict[str, int | None]]:
    """participant id -> what the DEPOSIT says, joined here with dictionaries.

    No DataFrame merge, so no join can raise an error that quotes a key. Nothing
    from this mapping is ever printed.
    """
    ind = spss.read(STATA / "j_indresp_ip.dta").df
    hhs = spss.read(STATA / "j_hhsamp_ip.dta").df
    nonresid = spss.read(STATA / "j_nonresid_ip.dta").df
    alloc = {h: _code(a) for h, a in zip(hhs["j_hidp"], hhs["j_ff_nonresw10"], strict=True)}
    enumerated = collections.Counter(int(p) for p in nonresid["pidp"])
    wanted = [
        f"{v}{g}"
        for g in (1, 2)
        for v in (
            *FH_VARS,
            *CONTACT_VARS,
            "biou18num",
            "adopu18num",
            "stepu18num",
            "numbionrc",
            "numadoptnrc",
            "numstepnrc",
        )
    ]
    out: dict[str, dict[str, int | None]] = {}
    for _, r in ind.iterrows():
        pidp = int(r["pidp"])
        pid = "ukds_6849:ip_" + hashlib.sha256(f"ukds6849:{pidp}".encode()).hexdigest()[:12]
        d: dict[str, int | None] = {
            "alloc": alloc.get(r["j_hidp"]),
            "indmode": _code(r["j_indmode"]),
            "enumerated": enumerated.get(pidp, 0),
        }
        for v in wanted:
            d[v] = _code(r[f"j_{v}"])
        out[pid] = d
    return out


def _answered(v: int | None) -> bool:
    return v is not None and v not in (-9, -8, -7)


# --- the generator ---------------------------------------------------------


@needs_deposit
def test_check_finds_allocation_routing_labels_text_and_recipes_consistent() -> None:
    assert _generator().check() == 0


@needs_deposit
def test_check_counts_an_answer_in_the_other_groups_variable() -> None:
    gen = _generator()
    merged, labels = gen._joined()
    broken = merged.copy()
    group1 = broken.index[broken["j_ff_nonresw10"] == 1][:3]
    broken.loc[group1, "j_masee2"] = 1
    assert gen.check(broken, labels) > 0


@needs_deposit
def test_check_counts_a_blank_in_a_respondents_own_variable() -> None:
    gen = _generator()
    merged, labels = gen._joined()
    broken = merged.copy()
    # A blank where the routing said "inapplicable" and the universe agrees: no
    # other count can see it, so only the blank-in-own-variable count fails.
    routed_out = (broken["j_ff_nonresw10"] == 2) & (broken["j_chsee2"] == -8)
    broken.loc[broken.index[routed_out][:2], "j_chsee2"] = float("nan")
    assert gen.check(broken, labels) > 0


@needs_deposit
def test_check_counts_households_given_the_other_code() -> None:
    """A swapped allocation breaks both the routing and the order evidence."""
    gen = _generator()
    merged, labels = gen._joined()
    broken = merged.copy()
    asked = broken["j_ladopted1"].isin([1, 2])
    broken.loc[broken.index[asked][:4], "j_ff_nonresw10"] = 2
    assert gen.check(broken, labels) > 0


@needs_deposit
def test_check_counts_a_wrong_first_module() -> None:
    """The identifier module must match the FIRST module's count, for everyone."""
    gen = _generator()
    merged, labels = gen._joined()
    broken = merged.copy()
    has = broken["nonresid_n"] > 0
    broken.loc[broken.index[has][:2], "nonresid_n"] = 0
    assert gen.check(broken, labels) > 0


@needs_deposit
def test_check_counts_order_evidence_that_cannot_discriminate() -> None:
    """If the late module's count matched the identifier module for everyone too,
    the data would no longer show which module came first."""
    gen = _generator()
    merged, labels = gen._joined()
    broken = merged.copy()
    for early, late in (
        ("biou18num1", "numbionrc1"),
        ("adopu18num1", "numadoptnrc1"),
        ("stepu18num1", "numstepnrc1"),
    ):
        broken[f"j_{late}"] = broken[f"j_{early}"]
    assert gen.check(broken, labels) > 0


def _quiet_respondents(merged, g: int):
    """Group g respondents asked both modules whose contact items were all routed out."""
    gen = _generator()
    mask = (merged["j_ff_nonresw10"] == g) & gen._fn_asked(merged, g) & gen._fh_asked(merged, g)
    for v in CONTACT_VARS:
        mask &= merged[f"j_{v}{g}"] == -8
    return merged.index[mask]


@needs_deposit
def test_check_counts_another_respondent_asked_neither_module() -> None:
    gen = _generator()
    merged, labels = gen._joined()
    broken = merged.copy()
    idx = _quiet_respondents(broken, 1)[:1]
    for c in [gen._lv(1, code) for code in gen.LV_CODES] + [f"j_{v}1" for v in FH_VARS]:
        broken.loc[idx, c] = -8
    assert gen.check(broken, labels) > 0


@needs_deposit
def test_check_counts_a_late_module_without_the_early_one() -> None:
    gen = _generator()
    merged, labels = gen._joined()
    broken = merged.copy()
    idx = _quiet_respondents(broken, 1)[:1]
    for c in [gen._lv(1, code) for code in gen.LV_CODES]:
        broken.loc[idx, c] = -8
    assert gen.check(broken, labels) > 0


@needs_deposit
def test_check_counts_a_contact_item_routed_outside_its_universe() -> None:
    gen = _generator()
    merged, labels = gen._joined()
    broken = merged.copy()
    no_mother = (
        (broken["j_ff_nonresw10"] == 1)
        & (broken["j_lvreladp11"] == 0)
        & (broken["j_lvreladp19"] == 0)
        & (broken["j_masee1"] == -8)
    )
    broken.loc[broken.index[no_mother][:3], "j_masee1"] = 2
    assert gen.check(broken, labels) > 0


@needs_deposit
def test_check_counts_fertility_items_routed_apart() -> None:
    gen = _generator()
    merged, labels = gen._joined()
    broken = merged.copy()
    asked = broken["j_lstep1"].isin([1, 2])
    broken.loc[broken.index[asked][:2], "j_lstep1"] = -8
    assert gen.check(broken, labels) > 0


@needs_deposit
def test_check_counts_swapped_allocation_labels() -> None:
    gen = _generator()
    merged, labels = gen._joined()
    broken = dict(labels)
    swapped = dict(labels["j_ff_nonresw10"])
    swapped[1.0], swapped[2.0] = swapped[2.0], swapped[1.0]
    broken["j_ff_nonresw10"] = swapped
    assert gen.check(merged, broken) > 0


@needs_deposit
def test_check_counts_a_recipe_edited_by_hand(monkeypatch, tmp_path) -> None:
    gen = _generator()
    edited = tmp_path / "fh.yaml"
    edited.write_text(RECIPE["fh"].read_text().replace("earlier in the interview.", "before.", 1))
    monkeypatch.setitem(gen.RECIPES, "fh", edited)
    assert gen.check_recipe() == 1


@needs_deposit
def test_check_exits_non_zero_when_it_finds_anything(monkeypatch) -> None:
    gen = _generator()
    monkeypatch.setattr(gen, "check", lambda merged=None, labels=None: 1)
    monkeypatch.setattr(sys, "argv", ["gen_ip_nrp.py", "--check"])
    with pytest.raises(SystemExit) as exc:
        gen.main()
    assert exc.value.code not in (0, None)


def test_a_failed_join_never_quotes_its_keys() -> None:
    """Synthetic frames: pandas' own MergeError lists duplicated keys."""
    import pandas as pd

    gen = _generator()
    left = pd.DataFrame({"j_hidp": [918273645, 564738291]})
    right = pd.DataFrame({"j_hidp": [918273645, 918273645], "x": [1, 2]})
    with pytest.raises(gen.IdentifierSafeError) as exc:
        gen._merge(left, right, "j_hidp", "test join")
    assert "918273645" not in str(exc.value)
    assert exc.value.__cause__ is None and exc.value.__context__ is None


def test_regenerating_the_recipes_changes_nothing() -> None:
    gen = _generator()
    for kind, path in RECIPE.items():
        assert path.read_text() == gen.render_recipe(kind)


@needs_deposit
def test_pidp_is_never_written_to_the_derived_file() -> None:
    frame, _ = _generator().derive()
    assert "pidp" not in frame.columns
    assert "hidp" not in " ".join(frame.columns)
    assert frame["person"].str.startswith("ip_").all()


# --- the deposit, read here alone ---------------------------------------------


@needs_deposit
def test_the_first_module_is_the_one_the_identifier_module_followed() -> None:
    """Group 1 met Family Networks first, group 2 Fertility History (ledger 138)."""
    first = {
        1: ("biou18num1", "adopu18num1", "stepu18num1"),
        2: ("numbionrc2", "numadoptnrc2", "numstepnrc2"),
    }
    late = {
        1: ("numbionrc1", "numadoptnrc1", "numstepnrc1"),
        2: ("biou18num2", "adopu18num2", "stepu18num2"),
    }
    off_first = collections.Counter()
    off_late = collections.Counter()
    for d in _deposit().values():
        g = d["alloc"]
        if g not in (1, 2):
            continue
        n_first = sum(max(d[v] or 0, 0) for v in first[g])
        n_late = sum(max(d[v] or 0, 0) for v in late[g])
        off_first[g] += d["enumerated"] != n_first
        off_late[g] += d["enumerated"] != n_late
    assert off_first == collections.Counter({1: 0, 2: 0})
    assert off_late[1] > 0 and off_late[2] > 0


@needs_deposit
def test_nobody_answers_the_other_groups_variables() -> None:
    wrong = 0
    for d in _deposit().values():
        g = d["alloc"]
        other = 2 if g == 1 else 1
        wrong += sum(_answered(d[f"{v}{other}"]) for v in FH_VARS + CONTACT_VARS)
    assert wrong == 0


# --- the built rows ---------------------------------------------------------


def _interviewer(pid: str) -> bool:
    return _deposit()[pid]["indmode"] in (1, 2)


@needs_derived
def test_each_fertility_condition_is_its_arms_text_in_the_respondents_mode() -> None:
    wrong = sum(
        r.condition != FH_CONDITION[(r.condition_num, _interviewer(r.participant_id))]
        for r in _rows("fh")
    )
    assert wrong == 0


@needs_derived
def test_each_contact_condition_is_its_arms_text_in_the_respondents_mode() -> None:
    wrong = sum(
        r.condition != CONTACT_CONDITION[(r.condition_num, _interviewer(r.participant_id))]
        for r in _rows("contact")
    )
    assert wrong == 0


@needs_derived
def test_each_fertility_outcome_is_its_question_with_the_sex_fill() -> None:
    derived = spss.read(DERIVED).df
    sex = {
        f"ukds_6849:{p}": _code(s) for p, s in zip(derived["person"], derived["sex"], strict=True)
    }
    wrong = 0
    for r in _rows("fh"):
        if r.task_num == 2:
            verb = {1: "fathered", 2: "had"}[sex[r.participant_id]]  # type: ignore[index]
            q = BIO.format(verb=verb)
        else:
            q = (ADOPTED, STEP)[r.task_num]
        wrong += r.outcome != f"{q} {YES_NO}"
    assert wrong == 0


@needs_derived
def test_each_contact_outcome_is_its_question_in_the_respondents_mode() -> None:
    wrong = 0
    for r in _rows("contact"):
        capi, web = CONTACT_Q[r.task_num]
        q = capi if _interviewer(r.participant_id) or not web else f"{capi} {web}"
        wrong += r.outcome != f"{q} {FREQ}"
    assert wrong == 0


@needs_derived
def test_rows_per_cell_and_per_outcome() -> None:
    fh = collections.Counter((r.condition_num, r.task_num) for r in _rows("fh"))
    contact = collections.Counter((r.condition_num, r.task_num) for r in _rows("contact"))
    assert dict(fh) == FH_CELLS
    assert dict(contact) == CONTACT_CELLS
    assert sum(not 1 <= int(r.response) <= 2 for r in _rows("fh")) == 0
    assert sum(not 1 <= int(r.response) <= 6 for r in _rows("contact")) == 0


@needs_derived
def test_each_rows_condition_follows_from_its_households_allocation() -> None:
    dep = _deposit()
    # Fertility History: group 2 had it first (0); group 1 after Family Networks (1).
    off = sum(
        dep[r.participant_id]["alloc"] != (2 if r.condition_num == 0 else 1) for r in _rows("fh")
    )
    # Contact: group 1 had Family Networks first (0); group 2 after Fertility History (1).
    off += sum(
        dep[r.participant_id]["alloc"] != (1 if r.condition_num == 0 else 2)
        for r in _rows("contact")
    )
    assert off == 0


@needs_derived
def test_every_answer_is_a_row_and_nothing_else() -> None:
    """The other direction, computed from the deposit alone."""
    expected: collections.Counter = collections.Counter()
    for d in _deposit().values():
        g = d["alloc"]
        if g not in (1, 2):
            continue
        for t, v in enumerate(FH_VARS):
            if d[f"{v}{g}"] in (1, 2):
                expected[("fh", 0 if g == 2 else 1, t)] += 1
        for t, v in enumerate(CONTACT_VARS):
            if d[f"{v}{g}"] in (1, 2, 3, 4, 5, 6):
                expected[("contact", 0 if g == 1 else 1, t)] += 1
    got = collections.Counter(("fh", r.condition_num, r.task_num) for r in _rows("fh"))
    got += collections.Counter(("contact", r.condition_num, r.task_num) for r in _rows("contact"))
    assert sum((expected - got).values()) == 0
    assert sum((got - expected).values()) == 0


@needs_derived
def test_the_persona_never_meets_its_own_answer() -> None:
    """No children-in-household beside 'have you ever had children'; no sex in a condition."""
    fh = recipe.load(RECIPE["fh"])
    contact = recipe.load(RECIPE["contact"])
    assert "nchild_dv" not in fh.persona_map.values()
    assert "nchild_dv" in contact.persona_map.values()
    named = sum(
        any(w in r.condition for w in ("fathered", " had any biological"))
        for k in ("fh", "contact")
        for r in _rows(k)
    )
    assert named == 0
