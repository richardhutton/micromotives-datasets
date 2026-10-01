"""The questionnaire directive resolver.

Every condition string asserted on below was taken from the measured census of
`data/raw` — 1,522 conditional directives across 127 questionnaire files — not
invented. Inventing them is how a parser ends up handling the three forms its
author happened to think of: a grammar of `VAR op NUMBER` joined by AND/OR fits
only 733 of the 1,522, and the forms it misses (value lists, ranges, MISSING)
are not edge cases but recur in dozens of files.

The most important tests here are the REFUSALS. Arm text is the only part of a
row this project writes, so a condition silently evaluated the wrong way
produces a row that teaches a model the wrong question, passes every QC rule,
and matches SocSci210's row counts exactly.
"""

from __future__ import annotations

import pytest

from micromotives_datasets.sources.quex import (
    UnparsedConditionError,
    parse_condition,
    resolve_inline,
    segment,
    strip_scripting,
)

# --------------------------------------------------------------------------
# conditions
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("cond", "values", "expected"),
    [
        # the plain case, 1,770 uses of `=`
        ("P_GENDER=1", {"P_GENDER": 1}, True),
        ("P_GENDER=1", {"P_GENDER": 2}, False),
        # case-insensitive variable names: deposits are inconsistent, and a
        # case-sensitive lookup once cost three studies their entire persona
        ("p_gender=1", {"P_GENDER": 1}, True),
        ("P_GENDER=1", {"p_gender": 1}, False),  # values are the caller's to normalise
        # `<>`, 49 uses
        ("GENDER1<>1", {"GENDER1": 2}, True),
        ("GENDER1<>1", {"GENDER1": 1}, False),
        # comparisons
        ("PANEL_TYPE>=20", {"PANEL_TYPE": 20}, True),
        ("PANEL_TYPE>=20", {"PANEL_TYPE": 19}, False),
        # value LIST — `PID1=3, 4, 77, 98, 99`, 21 uses
        ("PID1=3, 4, 77, 98, 99", {"PID1": 77}, True),
        ("PID1=3, 4, 77, 98, 99", {"PID1": 5}, False),
        ("P_KIM=2,3,4", {"P_KIM": 4}, True),
        # value RANGE — `XTESS084 = 1-4`, 8 uses each for three studies
        ("XTESS084 = 1-4", {"XTESS084": 4}, True),
        ("XTESS084 = 1-4", {"XTESS084": 5}, False),
        # range and list together — `XTESS069=1-4, 9-12`, 18 uses
        ("XTESS069=1-4, 9-12", {"XTESS069": 11}, True),
        ("XTESS069=1-4, 9-12", {"XTESS069": 7}, False),
        ("VIGNOE=1-12", {"VIGNOE": 12}, True),
        # negative codes are values, not range separators: -1 is a refusal
        # code in several deposits
        ("Q1=-1", {"Q1": -1}, True),
        # AND, 265 uses
        ("P_GENDER=1 AND P_BEHAV=1", {"P_GENDER": 1, "P_BEHAV": 1}, True),
        ("P_GENDER=1 AND P_BEHAV=1", {"P_GENDER": 1, "P_BEHAV": 2}, False),
        # OR, 169 uses
        ("P_GENDER=1 OR P_BEHAV=1", {"P_GENDER": 2, "P_BEHAV": 1}, True),
        ("P_GENDER=1 OR P_BEHAV=1", {"P_GENDER": 2, "P_BEHAV": 2}, False),
        # MISSING, 11 + 8 uses in the two spellings
        ("MISSING P_ATTEND", {"P_ATTEND": None}, True),
        ("MISSING P_ATTEND", {"P_ATTEND": 3}, False),
        ("MISSING (S_PARTY7ID)", {"S_PARTY7ID": None}, True),
        # NOT, 53 uses
        ("NOT P_GENDER=1", {"P_GENDER": 2}, True),
        ("NOT P_GENDER=1", {"P_GENDER": 1}, False),
        ("NOT MISSING P_ATTEND", {"P_ATTEND": 3}, True),
        ("NOT MISSING P_ATTEND", {"P_ATTEND": None}, False),
        # a scripting instruction glued onto the condition —
        # `dov_direct=1 show response options 1-5`, 62 uses
        ("dov_direct=1 show response options 1-5", {"DOV_DIRECT": 1}, True),
        ("dov_direct=1 show response options 1-5", {"DOV_DIRECT": 2}, False),
    ],
)
def test_measured_conditions_evaluate(cond: str, values: dict, expected: bool) -> None:
    assert parse_condition(cond)(values) is expected


def test_missing_is_neither_equal_nor_unequal() -> None:
    """A question never asked has no answer to compare against.

    Reading `VAR<>1` as true when VAR is missing would show a block of arm text
    to respondents who were never in that branch at all — and the text would
    look perfectly plausible in review.
    """
    assert parse_condition("Q1=1")({"Q1": None}) is False
    assert parse_condition("Q1<>1")({"Q1": None}) is False
    assert parse_condition("Q1>=1")({"Q1": None}) is False


def test_a_variable_absent_from_values_is_false_not_an_error() -> None:
    """Resolving one arm's text need not supply every variable in the file."""
    assert parse_condition("Q1=1")({}) is False


@pytest.mark.parametrize(
    "cond",
    [
        "RESPONDENT IS AVAILABLE",  # 16 uses — prose, not evaluable
        "R SKIPS PROMPT ONCE",  # 8 uses
        "",
        "P_GENDER",  # a bare variable asserts nothing
        "P_GENDER = one",  # a word where a code belongs
        "A=1 AND B=2 OR C=3",  # mixed connectives need precedence the source omits
        "A>=1,2,3",  # a comparison against a set means nothing
    ],
)
def test_conditions_outside_the_measured_grammar_are_refused(cond: str) -> None:
    """The whole design rests on this.

    A resolver that treated `RESPONDENT IS AVAILABLE` as false would drop a
    block of arm text and leave no trace. `UnparsedConditionError` carries the text
    so every refusal can be listed in one pass.
    """
    with pytest.raises(UnparsedConditionError):
        parse_condition(cond)


def test_the_refusal_names_the_text_it_could_not_read() -> None:
    with pytest.raises(UnparsedConditionError) as exc:
        parse_condition("RESPONDENT IS AVAILABLE")
    assert exc.value.text == "RESPONDENT IS AVAILABLE"


# --------------------------------------------------------------------------
# inline substitution
# --------------------------------------------------------------------------


def test_insert_if_picks_the_branch_that_applies() -> None:
    """`[INSERT IF P_GENDER=1: he; INSERT IF P_GENDER=2: she]`, 311 uses."""
    t = "[INSERT IF P_GENDER=1: he; INSERT IF P_GENDER=2: she] is not that orientation."
    assert resolve_inline(t, {"P_GENDER": 1}) == "he is not that orientation."
    assert resolve_inline(t, {"P_GENDER": 2}) == "she is not that orientation."


def test_no_branch_applying_leaves_nothing_rather_than_a_directive() -> None:
    t = "[INSERT IF P_GENDER=1: he; INSERT IF P_GENDER=2: she] answered."
    assert resolve_inline(t, {"P_GENDER": 3}) == " answered."


def test_if_display_switch() -> None:
    """`[IF GENDER1=1 DISPLAY] Gay; [IF GENDER1<>1 DISPLAY] Lesbian or gay`, 578 uses."""
    t = "[IF GENDER1=1 DISPLAY] Gay; [IF GENDER1<>1 DISPLAY] Lesbian or gay"
    assert resolve_inline(t, {"GENDER1": 1}).strip() == "Gay;"
    assert resolve_inline(t, {"GENDER1": 2}).strip() == "; Lesbian or gay"


def test_show_if_with_a_payload_inside_the_bracket_is_inline() -> None:
    """`[SHOW IF SMARTPHONE = 2: ...]`, 16 uses.

    Unambiguous because the bracket delimits the text it governs — unlike the
    block form, where the extent has to be inferred.
    """
    t = "a. [SHOW IF SMARTPHONE = 2: You would be loaned a device for the study.] b."
    assert resolve_inline(t, {"SMARTPHONE": 2}) == (
        "a. You would be loaned a device for the study. b."
    )
    assert resolve_inline(t, {"SMARTPHONE": 1}) == "a.  b."


def test_an_unparsed_inline_condition_raises_rather_than_dropping_text() -> None:
    with pytest.raises(UnparsedConditionError):
        resolve_inline("[INSERT IF RESPONDENT IS AVAILABLE: hello]", {})


# --------------------------------------------------------------------------
# scripting noise
# --------------------------------------------------------------------------


def test_layout_directives_are_stripped() -> None:
    """`[SP]` alone is 1,276 uses across 66 files — pure rendering instruction."""
    t = "[SP] IDEO. In general, do you think of yourself as... [TEXT BOX]"
    assert strip_scripting(t) == "IDEO. In general, do you think of yourself as..."


def test_stripping_does_not_touch_conditionals() -> None:
    """Losing one silently would change the arm text, which is the one thing
    this project writes rather than reads."""
    t = "[SP] [SHOW IF X=1] the treatment paragraph"
    assert "[SHOW IF X=1]" in strip_scripting(t)


# --------------------------------------------------------------------------
# block segmentation — a report, never a silent resolution
# --------------------------------------------------------------------------


def test_segmentation_splits_at_each_block_directive() -> None:
    t = "Preamble. [SHOW IF X=1] first arm text. [SHOW IF X=2] second arm text."
    seg = segment(t)
    assert [b.condition for b in seg.blocks] == ["", "X=1", "X=2"]
    assert seg.blocks[1].text == "first arm text."
    assert seg.blocks[2].text == "second arm text."
    assert seg.blocks[0].applies({}) is True
    assert seg.blocks[1].applies({"X": 1}) is True
    assert seg.blocks[1].applies({"X": 2}) is False


def test_an_unparsed_block_condition_is_reported_and_refuses_to_apply() -> None:
    """Not silently dropped, and not silently kept either."""
    seg = segment("[SHOW IF RESPONDENT IS AVAILABLE] thanks for continuing")
    assert seg.refusals == ["RESPONDENT IS AVAILABLE"]
    assert seg.blocks[0].unparsed is True
    with pytest.raises(UnparsedConditionError):
        seg.blocks[0].applies({})
    assert "** UNPARSED **" in seg.render()


def test_the_inline_if_display_form_is_not_segmented_as_a_block() -> None:
    """It matches the block pattern too, and cutting on it would chop a sentence
    into blocks that do not exist in the questionnaire."""
    seg = segment("Pick one: [IF GENDER1=1 DISPLAY] Gay; [IF GENDER1<>1 DISPLAY] Lesbian")
    assert [b.condition for b in seg.blocks] == [""]


def test_text_with_no_directives_is_one_unconditional_block() -> None:
    seg = segment("Just a question.")
    assert len(seg.blocks) == 1
    assert seg.blocks[0].condition == ""
    assert seg.blocks[0].applies({}) is True
