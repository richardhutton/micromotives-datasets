#!/usr/bin/env python3
"""Write recipes/researchbox124_*.yaml: X against a choice of Y or Z, in gambles (2 recipes).

Smith S & Spiller SA, "Undervaluation of Multi-Option Alternatives" (the box's title; the
authors are named on the Study 6d pre-registration, AsPredicted #41630; the deposit names no
publication). ResearchBox 124 (https://researchbox.org/124), read from its Zenodo copy
(record 21301841, https://zenodo.org/records/21301841). CC BY 4.0 ("All content posted to
ResearchBox is under a CC By 4.0 License", the box page). US samples (MTurk via CloudResearch,
2020, the pre-registrations); dollar stakes, kept as the source has them.

Every judgement is here, in code, so the recipes can be re-derived and reviewed.

THE BOX. Fifteen studies (1, 1b, 1c, 1d, 2, 2b, 3, 3b, 4, 5, 6, 6b, 6c, 6d, 6e), twelve .qsf
files (Studies 1 and 1b share one, as do 2 and 2b and 3 and 3b), the authors' cleaning and
analysis R code per study, each study's raw Qualtrics export (Other/*rawdata.csv: three
header rows, the third holding each column's ImportId) and their cleaned file (Data/), and an
AsPredicted pre-registration per study. The .qsf files are 2026 copies (SurveyCreationDate
2026-03-20) of surveys fielded in 2020; every trial column of the two raw exports built here
carries the ImportId of the .qsf question with the same export tag (asserted), so the copies
are the fielded questionnaires as far as the data can show.

WHAT IS BUILT. Studies 6d and 6e ("Undervaluation Study 1" and "Study 2" in their
pre-registrations, AsPredicted #41630 and #44164, May and July 2020). Every decision is a
choice between gambles described in words: a dollar amount and how to win it ("$5 / Flipping
heads on one coin"), where one option may itself be a choice ("$5 / A) Rolling a 1 / B)
Flipping tails on one coin": win $5 by whichever of A or B you pick). The question is whether
people undervalue that Y-or-Z option against Y alone. Ten sets of X, Y and Z; for each set a
per-person draw (type1-type10, 1-6, recorded) decides which versions of its six trials the
person meets, and the Qualtrics display logic on each question says which (read, never
inferred from the answers: `shown` evaluates it on the recorded draws, and every shown
question is answered and no other, asserted, all trials being ForceResponse ON).
- study6d: X vs Y-or-Z and X vs Y (control) trials (the pre-registration's "39 or 40
  choices"; built, without the three dominance checks, 34 or 35 per person), plus the Y vs Z
  choices of one randomly picked set at the end (1 or 2), so 35-37 rows per person (block QYZ; randpick, recorded). Which way
  round A) and B) are printed is a between-person draw (oddeven, recorded, routes to block
  Q1s or Q2s), and the words on screen carry it.
- study6e: sets 1-5 or 6-10 (set, recorded), and within each set X vs Y-or-Z (as Y-or-Z or
  Z-or-Y, order recorded), X vs Y vs Z, X vs Y, X vs Z and Y vs Z. Its end-of-study Y vs Z
  choices (blocks QYZ_1_5 / QYZ_6_10, one or two per person) are NOT built: they put again
  Y vs Z pairs the trials already ask, and 12 built people met the identical pair twice
  (QC: one condition and outcome answered twice), the second time after every trial; a row
  could only say which came first by narrating trials whose order is not recorded.
Kind "choice" (options described by stake and odds).

ONE ARM PER CHOICE SET. Each distinct list of options is one arm; every trial question is
one outcome naming its own arm column (Outcome.condition_var a_<tag>, set to the arm's code
where the question was shown, blank where not). A set of options asked by two questions (6d's
X vs Y control appears in both Q1s and Q2s) is one arm. The factors are the options
themselves (option_1, option_2 and, in 6e, option_3, "-" where a set has two), each level
the option's words joined with " / ", so every arm differs from its minimal pairs in the
words. Which comparison a question belongs to (X vs Y-or-Z, X vs Y, ...) is a property of the
question, not of the words alone (6e's X vs Z and Y vs Z trials can repeat another trial's
pair), so it is kept per outcome (`Question.version`), not as a factor.

THE ROW. The instruction screens every kept person read (6d: Instructions1, Instructions2,
Q186; 6e: Instructions1, Instructions2, Instructions3; 6e's Instructions3_Orig is shown only
when instructions = "original", and the flow sets "new" for everyone, asserted) are the
shared context, word-for-word, without their "INSTRUCTIONS" headings and the navigation line
"Click the arrow to continue reading the instructions." They hold the rules of the coins,
dice and cards, two example decisions and the lottery for real money (6d's first screen also
calls the decisions hypothetical; both statements are on its fielded screens, kept as they
are). Not narrated: the
comprehension questions and their retry page (identical for everyone, before the trials),
the three dominance attention checks among the trials (OD1-OD3, exclusions, not outcomes),
6e's risk-attitude (Holt-Laury) choices and questionnaires after the trials, and every other
trial: all trials sit in one block shown in a random order the deposit does not record, so
no row names another (CONVENTIONS: an order randomised and not recorded cannot be narrated).
Each trial screen shows its options and NO question text (QuestionText is a blank space,
asserted), and the order of the options on screen was randomised per question (Randomization
"All") and not recorded (no _DO column, asserted). So, under CONVENTIONS "Choice sets whose
on-screen order was randomised and not recorded", the row lists the options in the .qsf's
order, labelled "Option 1", "Option 2" (and "Option 3"), each option's lines as on screen,
and the answer is coded to that list. Added words (ours):
    '(the options were shown in a random order)'   after the instructions
    'Option 1:', 'Option 2:', 'Option 3:'           before each option
    '1 means "Option 1"; 2 means "Option 2".' (with '; 3 means "Option 3"' for three
      options) after the question.
The question itself, "Choose whichever option you prefer.", is transcribed from
Instructions1 ("In each decision, you should choose whichever option you prefer."); it is
not on the trial screens, which carry no question text.
Typography normalised (HTML, non-breaking spaces, curly quotes); the example decisions'
spacing collapsed. Some trials list two options with identical words: by design where a set's
Y is X itself (6d Q11a / 11aXY, 6e Q11a_X_Y, Q11a_X_Y_Z, Q21a_X_Y_Z), and in 6e's Q2c_X_Y_Z,
Q12c_X_Y_Z and Q12c_Y_Z, where Y and Z read the same although the set's X vs Y-or-Z trial
gives them different words, apparently a slip in the questionnaire. The fielded words are
the authority and are kept; none of these is in the answer key.

CODES. The .qsf's choices in ChoiceOrder are Option 1, 2, 3; the export holds each choice's
RecodeValues value where one is set (6e's three-option trials recode their third choice,
key 3, 6, 7, 8 or 11, to 3; its X vs Z trials export 1 and 3), and the coded file maps every
exported value back to its position (asserted injective, every data value covered). In every
X vs Y, X vs Y-or-Z and X vs Z-or-Y trial, X is choice 1 exported as 1, so the authors' "2 -
Choice" (1 when X was chosen) is "2 - response" on the rows.

EXCLUSIONS, the authors' cleaning code as written: Progress 100, then the three dominance
checks right in either of their copies (OD1 = 1, OD2 = 2, OD3 = 1; 6d's two copies are both
exported as OD1..OD3, read here by ImportId). 6d keeps 194 of 298 finished, 6e 176 of 298
(the pre-registrations' primary samples, the authors' N). 6e's flow sets instructions = "new",
which the display logic reads to show Instructions3 rather than Instructions3_Orig (one
sentence shorter); it is blank for the 27 people who started on 7 July 2020 between 11:19
and 14:50, and set for everyone from 15:17 that day on (62 of the day's 89 have it), so the
field and probably the new screen were added at a mid-day cutover. Which third screen those 12 kept
people read cannot be determined, so they are not built (`built_index`): 6e builds 164.
6d's flow sets timing = 12, which nothing in its .qsf reads (no logic, piped text or
JavaScript; asserted), so its 15 first-day people with timing blank are built.

PERSONA. Age (What is your age (in years)?, a text box; a whole number 18-100 kept, anything
else blank) and gender (the .qsf's labels: Male, Female, Non-binary; 6e recodes Non-binary
4 to 3, read through its RecodeValues).

ANSWER KEY. The pre-registered test in each study's analysis code (UVExp6d.Rmd,
UVExp6e.Rmd): per person, the share of X choices on X vs Y-or-Z trials minus the share on X vs
Y trials, its mean tested against 0. The authors' cleaning duplicates the controls that serve
both transparency levels and adds a copy of trial 21c's control as 21a's (with choice 1.5 in
6e, where 21a's control would pit X against an identical Y); those rules, applied as written
to the raw export AND, keyed by task_num, to the BUILT rows, reproduce the authors' own long
files (Data/UVExp6d.csv, 7,760 rows; UVExp6e.csv, 6,160) row for row, person by person. On
their files the test gives 6d 0.06365979 (t = 4.284, df 193) and 6e 0.05568182 (t = 3.375, df
175), the values their code records. The built 6d rows give 0.06365979; the built 6e rows (164
people) give 0.0582317, which is the authors' own file restricted to the same 164
(tests/test_gen_researchbox124.py).

NOT BUILT (NOT_BUILT), each with its reason below. JEV. scripts/recipe_prep.py reads
.sav/.dta/.por only; this deposit is .csv, so it does not apply. There is no assignment
column to find (the draws are named embedded fields that the display logic reads) and the
persona labels are the .qsf's own choices.

    uv run python scripts/gen_researchbox124.py --prep   # code the data
    uv run python scripts/gen_researchbox124.py          # write the recipes
    uv run python scripts/gen_researchbox124.py --check  # exit 1 if any recipe differs
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
STUDY_ID = "researchbox124"
RAW = REPO / "data" / "raw" / STUDY_ID
MATERIALS = RAW / "Materials"
OTHER = RAW / "Other"
DATA = RAW / "Data"
RECIPES = REPO / "recipes"
LICENCE = (
    'CC BY 4.0, stated on the box page https://researchbox.org/124 ("All content posted '
    'to ResearchBox is under a CC By 4.0 License"); read from its Zenodo copy, record '
    "21301841 (https://zenodo.org/records/21301841). Read 19 Nov 2026."
)
PAPER = (
    'Smith S & Spiller SA, "Undervaluation of Multi-Option Alternatives" (the box title; '
    "authors from AsPredicted #41630; no publication is named in the deposit). ResearchBox "
    "124 (https://researchbox.org/124)."
)

NOT_BUILT = {
    "study1": "Studies 1 and 1b (UV_S1_S1b.qsf; also the Study 1 heterogeneity files): films. "
    "Each person first rates 50 films on sliders; JavaScript then picks the trial films from "
    "the ones that person rated highly (goodset) and pipes them into every choice "
    "(${e://Field/t1.x} ...). The options are the person's own earlier answers fed back, and "
    "the row cannot carry the ratings that chose them. rich's piped-answer and JavaScript "
    "rules.",
    "study1c": "Study 1c (UV_S1c.qsf): the Study 1 film paradigm, trials built by JavaScript "
    "from the person's own ratings and piped in. Same reason as study1.",
    "study1d": "Study 1d (UV_S1d.qsf): the Study 1 film paradigm (trains to cinemas), trials "
    "built by JavaScript from the person's own ratings and piped in. Same reason as study1.",
    "study2": "Studies 2 and 2b (UV_S2_S2b.qsf): the film paradigm, trials built by "
    "JavaScript from the person's own ratings and piped in, plus re-rating sliders on piped "
    "options. Same reason as study1.",
    "study3": "Studies 3 and 3b (UV_S3_S3b.qsf): the film paradigm, trials built by "
    "JavaScript from the person's own ratings and piped in. Same reason as study1.",
    "study4": "Study 4 (UV_S4.qsf): a cruise's day in port. The person ranks six activity "
    "categories; JavaScript stores the ranks and every option is an activity from the "
    "categories that person ranked 1st, 2nd and 5th (${e://Field/1_1}, 2_1, 5_4). The options "
    "are chosen by the person's own earlier answer, which the row cannot carry. rich's "
    "piped-answer rule.",
    "study5": "Study 5 (UV_S5.qsf): TikTok videos, each option a picture (IMAGE_URL fields, "
    "19 <img> tags) and a video revealed on hover, chosen from the person's own category "
    "ranking. rich's picture and video rule.",
    "study6": "Study 6 (UV_S6.qsf): gambles shown by JavaScript one piece at a time in "
    "regions that appear and disappear (loop-and-merge fields, timeList / mainSequence); the "
    "between-person manipulation (condition_observe pro / anti undervaluation) is how long "
    "each piece stayed on screen. Condition text and timing are generated by JavaScript, "
    "not words in the .qsf. rich's JavaScript rule.",
    "study6b": "Study 6b (UV_S6b.qsf): the 6d/6e gambles behind mouse-tracking boxes. Each "
    "option is an empty box whose words JavaScript writes in only while the cursor is over "
    "it (onmouseenter / onmouseleave; the words are string literals in each question's "
    "QuestionJS), so what a person read depends on where they moved the mouse. rich's "
    "JavaScript rule; 6d and 6e field the same trials as plain text.",
    "study6c": "Study 6c (UV_S6c.qsf): every gamble is drawn at random per person by "
    "JavaScript (Math.random over amounts, coins, dice and cards in QuestionJS) and piped "
    "in (${e://Field/t1.1.x} ...). The raw export records each person's generated option "
    "text in its t*.*.* fields, so the options are not unreproducible: it may be buildable, "
    "the options as recorded attributes, if each person's trial membership and order can be "
    "proved from the export. Left for rich's ruling (JavaScript-generated condition text).",
}

# Pictures per .qsf: (<img> tags, distinct IM_ graphic ids). Only Study 5 has any.
PICTURES = {
    "UV_S1_S1b.qsf": (0, 0),
    "UV_S1c.qsf": (0, 0),
    "UV_S1d.qsf": (0, 0),
    "UV_S2_S2b.qsf": (0, 0),
    "UV_S3_S3b.qsf": (0, 0),
    "UV_S4.qsf": (0, 0),
    "UV_S5.qsf": (19, 53),
    "UV_S6.qsf": (0, 0),
    "UV_S6b.qsf": (0, 0),
    "UV_S6c.qsf": (0, 0),
    "UV_S6d.qsf": (0, 0),
    "UV_S6e.qsf": (0, 0),
}

# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

_TYPO = {"\xa0": " ", "\u200b": "", "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"'}


def plain(raw: str) -> str:
    """An HTML fragment to one line of plain text. Typography only."""
    s = re.sub(r"<[^>]+>", " ", raw or "")
    s = html.unescape(s)
    for a, b in _TYPO.items():
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def lines(raw: str) -> list[str]:
    """HTML to its non-empty lines: paragraphs and <br> breaks each start a line."""
    s = re.sub(r"(?i)<br\s*/?>|</p>|</div>|<p[^>]*>|<div[^>]*>", "\n", raw or "")
    return [x for x in (plain(p) for p in s.split("\n")) if x]


def graphics_in(raw: str) -> tuple[int, int]:
    """(<img> tags, distinct IM_ graphic ids) in a .qsf's text."""
    return raw.count("<img"), len(set(re.findall(r"IM_[A-Za-z0-9]{10,}", raw)))


def check_pictures() -> None:
    assert sorted(p.name for p in MATERIALS.glob("*.qsf")) == sorted(PICTURES)
    for f, want in PICTURES.items():
        assert graphics_in((MATERIALS / f).read_text()) == want, f


# ---------------------------------------------------------------------------
# The questionnaire
# ---------------------------------------------------------------------------

Logic = dict[str, Any]


def holds(logic: Logic | None, ed: dict[str, str]) -> bool:
    """Evaluate Qualtrics display or branch logic over embedded-data values.

    Only what these surveys use is accepted: EmbeddedField EqualTo / NotEqualTo terms, one
    conjunction per group, groups joined by AndIf / OrIf. Anything else raises.
    """
    if not logic:
        return True
    result: bool | None = None
    for gk in sorted((k for k in logic if k.isdigit()), key=int):
        group = logic[gk]
        val: bool | None = None
        conjs = set()
        for tk in sorted((k for k in group if k.isdigit()), key=int):
            t = group[tk]
            assert t["LogicType"] == "EmbeddedField", t
            assert t["Operator"] in ("EqualTo", "NotEqualTo"), t
            v = ed[t["LeftOperand"]].strip() == str(t["RightOperand"]).strip()
            if t["Operator"] == "NotEqualTo":
                v = not v
            if val is None:
                assert "Conjuction" not in t, t
                val = v
            else:
                conjs.add(t["Conjuction"])
                val = (val or v) if t["Conjuction"] == "Or" else (val and v)
        assert val is not None and len(conjs) <= 1 and conjs <= {"Or", "And"}, group
        kind = group["Type"]
        if result is None:
            assert kind == "If", group
            result = val
        elif kind == "AndIf":
            result = result and val
        else:
            assert kind == "OrIf", group
            result = result or val
    assert result is not None
    return result


def logic_fields(logic: Logic | None) -> set[str]:
    out: set[str] = set()
    for gk, group in (logic or {}).items():
        if gk.isdigit():
            out |= {t["LeftOperand"] for k, t in group.items() if k.isdigit()}
    return out


@dataclass
class FlowBlock:
    block: dict[str, Any]
    branches: list[Logic]  # every enclosing branch's logic, outermost first


class Survey:
    """A .qsf, read through its flow: only questions a respondent could meet."""

    def __init__(self, filename: str) -> None:
        self.raw = (MATERIALS / filename).read_text()
        d = json.loads(self.raw)
        els = d["SurveyElements"]
        self.by_id = {e["Payload"]["QuestionID"]: e["Payload"] for e in els if e["Element"] == "SQ"}
        blocks: dict[str, dict[str, Any]] = {}
        for e in els:
            if e["Element"] == "BL":
                p = e["Payload"]
                for b in p.values() if isinstance(p, dict) else p:
                    blocks[b["ID"]] = b
        flow = next(e for e in els if e["Element"] == "FL")["Payload"]
        self.flow: list[FlowBlock] = []

        def walk(n: dict[str, Any], branches: list[Logic], in_randomizer: bool) -> None:
            kind = n.get("Type")
            if kind in ("Block", "Standard", "Default"):
                assert not in_randomizer, n  # no block here is drawn by a randomizer
                self.flow.append(FlowBlock(blocks[n["ID"]], branches))
            here = [*branches, n["BranchLogic"]] if kind == "Branch" else branches
            for c in n.get("Flow", []):
                walk(c, here, in_randomizer or kind == "BlockRandomizer")

        walk(flow, [], False)

    def block(self, description: str) -> FlowBlock:
        (b,) = [b for b in self.flow if b.block["Description"] == description]
        return b

    def questions(self, description: str) -> list[dict[str, Any]]:
        b = self.block(description).block
        return [self.by_id[x["QuestionID"]] for x in b["BlockElements"] if x["Type"] == "Question"]


# ---------------------------------------------------------------------------
# The two studies
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Spec:
    name: str
    qsf: str
    raw: str
    cleaned: str  # the authors' cleaned file, Data/
    prereg: str
    instructions: tuple[str, ...]  # QIDs of the instruction screens, in order
    trial_blocks: tuple[str, ...]
    end_blocks: tuple[str, ...]  # the closing Y vs Z blocks
    checks: dict[str, str]  # attention-check export tag -> the right code
    markers: dict[str, str]  # flow-set fields that pick a screen -> the value the .qsf sets
    n_finished: int
    n_kept: int
    n_built: int
    key: float  # the authors' recorded mean difference
    title: str


SPECS = {
    "study6d": Spec(
        name="study6d",
        qsf="UV_S6d.qsf",
        raw="UVExp6drawdata.csv",
        cleaned="UVExp6d.csv",
        prereg="AsPredicted #41630",
        instructions=("QID2", "QID3", "QID186"),
        trial_blocks=("Q1s", "Q2s", "QYZ"),
        end_blocks=("QYZ",),
        checks={"OD1": "1", "OD2": "2", "OD3": "1"},
        markers={},
        n_finished=298,
        n_kept=194,
        n_built=194,
        key=0.06365979,
        title="Choices between gambles (coins, dice, cards): X against an option that lets you "
        "pick Y or Z, X against Y alone, and Y against Z; which do you prefer? (Study 6d)",
    ),
    "study6e": Spec(
        name="study6e",
        qsf="UV_S6e.qsf",
        raw="UVExp6erawdata.csv",
        cleaned="UVExp6e.csv",
        prereg="AsPredicted #44164",
        instructions=("QID2", "QID3", "QID795"),
        trial_blocks=("Rep1_1_5", "Rep1_6_10"),
        end_blocks=(),  # QYZ_1_5 / QYZ_6_10 not built: see the docstring
        checks={"OD1": "1", "OD2": "2", "OD3": "1", "OD1b": "1", "OD2b": "2", "OD3b": "1"},
        markers={"instructions": "new"},
        n_finished=298,
        n_kept=176,
        n_built=164,
        key=0.05568182,
        title="Choices between gambles (coins, dice, cards): X against an option that lets you "
        "pick Y or Z, against Y or Z alone, all three side by side, and Y against Z; which do "
        "you prefer? (Study 6e)",
    ),
}

DROP_LINES = {"INSTRUCTIONS", "Click the arrow to continue reading the instructions."}
RANDOM_ORDER = "(the options were shown in a random order)"  # ours


@dataclass
class Question:
    qid: str
    tag: str
    block: str
    version: str  # X_YZ, X_ZY (6e), X_Y_Z, X_Y, X_Z, Y_Z; 6d's Y-or-Z is "X_YZ"
    options: list[list[str]]  # each option's lines, .qsf ChoiceOrder
    export: list[str]  # the exported value of each option
    logic: list[Logic]  # enclosing branches, then the question's own display logic
    arm: int = 0  # filled in by `arms`

    @property
    def var(self) -> str:
        return f"r_{self.tag}"

    @property
    def arm_var(self) -> str:
        return f"a_{self.tag}"

    def shown(self, ed: dict[str, str]) -> bool:
        return all(holds(lg, ed) for lg in self.logic)


def option_lines(display: str) -> list[str]:
    """One option's lines as on screen, asserted to be a stake and one or two ways to win."""
    out = lines(display)
    assert re.fullmatch(r"\$\d+", out[0]), out
    rest = out[1:]
    assert len(rest) == 1 or (
        len(rest) == 2 and rest[0].startswith("A) ") and rest[1].startswith("B) ")
    ), out
    assert not any("${" in x for x in out), out
    return out


def version_of(spec: Spec, block: str, tag: str, options: list[list[str]]) -> str:
    """Which comparison a trial is, from its export tag; checked against its options."""
    bundle = [len(o) == 3 for o in options]
    if block in spec.end_blocks:
        v = "Y_Z"
    elif spec.name == "study6d":
        # Q1s: Q<k>XYZ are X vs Y-or-Z, the rest controls; Q2s: <k>XY are controls.
        is_xyz = tag.endswith("XYZ") if block == "Q1s" else not tag.endswith("XY")
        v = "X_YZ" if is_xyz else "X_Y"
    else:
        m = re.fullmatch(r"Q\d+(?:a|c|ac)_(X_YZ|X_ZY|X_Y_Z|X_Y|X_Z|Y_Z)", tag)
        assert m, tag
        v = m.group(1)
    want = {
        "X_YZ": [False, True],
        "X_ZY": [False, True],
        "X_Y_Z": [False, False, False],
    }.get(v, [False, False])
    assert bundle == want, (tag, v, options)
    return v


@cache
def questions(name: str) -> list[Question]:
    """Every trial question a respondent could meet, in flow order (checks excluded)."""
    spec = SPECS[name]
    sv = Survey(spec.qsf)
    out: list[Question] = []
    for bname in spec.trial_blocks:
        fb = sv.block(bname)
        assert fb.block["Options"]["RandomizeQuestions"] == "Advanced", bname
        for p in sv.questions(bname):
            assert (p["QuestionType"], p["Selector"]) == ("MC", "SAHR"), p["QuestionID"]
            assert plain(p["QuestionText"]) == "", p["QuestionID"]  # no question on screen
            assert p["Validation"]["Settings"]["ForceResponse"] == "ON", p["QuestionID"]
            assert p["Randomization"]["Type"] == "All", p["QuestionID"]  # option order
            assert not p.get("QuestionJS"), p["QuestionID"]
            if p["DataExportTag"] in spec.checks:
                assert not p.get("DisplayLogic"), p["QuestionID"]  # everyone met the checks
                continue
            order = [str(k) for k in p["ChoiceOrder"]]
            assert sorted(order) == sorted(p["Choices"]), p["QuestionID"]
            rec = p.get("RecodeValues") or {}
            export = [str(rec.get(k, k)) for k in order]
            assert len(set(export)) == len(export), p["QuestionID"]
            opts = [option_lines(p["Choices"][k]["Display"]) for k in order]
            tag = p["DataExportTag"]
            out.append(
                Question(
                    qid=p["QuestionID"],
                    tag=tag,
                    block=bname,
                    version=version_of(spec, bname, tag, opts),
                    options=opts,
                    export=export,
                    logic=[*fb.branches, p.get("DisplayLogic") or {}],
                )
            )
    assert len({q.tag for q in out}) == len(out)
    return out


def arm_text(options: list[list[str]]) -> str:
    return "\n\n".join(f"Option {i}:\n" + "\n".join(o) for i, o in enumerate(options, 1))


QUESTION = "Choose whichever option you prefer."  # from Instructions1


def question_text(n: int) -> str:
    codes = "; ".join(f'{i} means "Option {i}"' for i in range(1, n + 1))  # ours
    return f"{QUESTION} {codes}."


@cache
def instructions(name: str) -> str:
    spec = SPECS[name]
    sv = Survey(spec.qsf)
    (fb,) = [b for b in sv.flow if b.block["Description"] == "Instructions"]
    shown = [
        x["QuestionID"]
        for x in fb.block["BlockElements"]
        if x["Type"] == "Question" and not sv.by_id[x["QuestionID"]].get("DisplayLogic")
    ]
    assert [q for q in shown if q in spec.instructions] == list(spec.instructions), shown
    paras = []
    for qid in spec.instructions:
        p = sv.by_id[qid]
        assert p["QuestionType"] == "DB" and not p.get("QuestionJS"), qid
        paras += [x for x in lines(p["QuestionText"]) if x not in DROP_LINES]
    text = "\n\n".join(paras)
    assert "${" not in text and "Click" not in text
    return text


@dataclass
class Experiment:
    name: str
    spec: Spec
    questions: list[Question]
    arms: list[list[list[str]]] = field(default_factory=list)  # each arm's options


def experiment(name: str) -> Experiment:
    """The questions that kept respondents answered, and the arms they share."""
    qs = [q for q in questions(name) if q.tag in answered_tags(name)]
    arms: list[list[list[str]]] = []
    for q in qs:
        if q.options not in arms:
            arms.append(q.options)
        q.arm = arms.index(q.options) + 1
    return Experiment(name, SPECS[name], qs, arms)


# ---------------------------------------------------------------------------
# The data
# ---------------------------------------------------------------------------


@cache
def read_raw(name: str) -> tuple[pd.DataFrame, list[str]]:
    """(the export's response rows as text, each column's ImportId QID)."""
    path = OTHER / SPECS[name].raw
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    header, imports = rows[0], rows[2]
    qids = [json.loads(x).get("ImportId", "") if x.startswith("{") else "" for x in imports]
    df = pd.DataFrame(rows[3:], columns=list(range(len(header))), dtype=str)
    df.attrs["names"] = header
    return df, qids


def column(name: str, qid: str) -> pd.Series:
    """The ONE column whose ImportId is this question."""
    df, qids = read_raw(name)
    (j,) = [j for j, q in enumerate(qids) if q == qid]
    return df[j]


def named(name: str, var: str) -> pd.Series:
    """The ONE column with this export name."""
    df, _ = read_raw(name)
    (j,) = [j for j, n in enumerate(df.attrs["names"]) if n == var]
    return df[j]


EMBEDDED: tuple[str, ...] = (*(f"type{k}" for k in range(1, 11)), "randpick")


def check_columns(name: str) -> None:
    """Every trial column's ImportId is the .qsf question with its export tag; no _DO."""
    df, qids = read_raw(name)
    names = df.attrs["names"]
    sv = Survey(SPECS[name].qsf)
    for q in questions(name):
        (j,) = [j for j, x in enumerate(qids) if x == q.qid]
        assert names[j] == q.tag == sv.by_id[q.qid]["DataExportTag"], (names[j], q.tag)
    assert not any("_DO" in n for n in names)


@cache
def kept_index(name: str) -> tuple[int, ...]:
    """The authors' sample: finished, and right on all three dominance checks."""
    spec = SPECS[name]
    df, _ = read_raw(name)
    fin = named(name, "Progress") == "100"
    assert int(fin.sum()) == spec.n_finished
    sv = Survey(spec.qsf)
    ok = fin.copy()
    for tag in ("OD1", "OD2", "OD3"):
        copies = [t for t in spec.checks if t.rstrip("b") == tag]
        qids = [
            p["QuestionID"]
            for fb in sv.flow
            for x in fb.block["BlockElements"]
            if x["Type"] == "Question"
            for p in [sv.by_id[x["QuestionID"]]]
            if p["DataExportTag"] in copies
        ]
        assert len(qids) == 2, (tag, qids)
        right = spec.checks[copies[0]]
        ok &= pd.concat([column(name, q) == right for q in qids], axis=1).any(axis=1)
    idx = tuple(int(i) for i in df.index[ok])
    assert len(idx) == spec.n_kept, len(idx)
    return idx


@cache
def built_index(name: str) -> tuple[int, ...]:
    """The kept people who took the version of the survey the .qsf is.

    A field the flow sets to a constant and the display logic reads (6e's instructions =
    "new", which hides Instructions3_Orig and shows Instructions3) is blank for the people
    who started before it was added (6e: 7 July 2020, 11:19 to 14:50; it is set from 15:17
    that day): which instruction screen they read cannot be determined, so they are not built.
    """
    spec = SPECS[name]
    idx = tuple(
        i for i in kept_index(name) if all(named(name, f)[i] == v for f, v in spec.markers.items())
    )
    assert len(idx) == spec.n_built, len(idx)
    return idx


@cache
def embedded(name: str, i: int) -> dict[str, str]:
    """The recorded draws for one respondent."""
    keys = [*EMBEDDED, "oddeven"] if name == "study6d" else [*EMBEDDED, "set", "order"]
    return {k: named(name, k)[i] for k in keys} | (
        {"instructions": named(name, "instructions")[i]} if name == "study6e" else {}
    )


@cache
def answered_tags(name: str) -> frozenset[str]:
    """Trial questions with at least one kept answer; shown == answered for every person."""
    seen: set[str] = set()
    built = set(built_index(name))
    for q in questions(name):
        col = column(name, q.qid)
        for i in kept_index(name):
            ed = embedded(name, i)
            ans = col[i] != ""
            assert q.shown(ed) == ans, (q.tag, i)
            if ans:
                assert col[i] in q.export, (q.tag, col[i])
                if i in built:
                    seen.add(q.tag)
    return frozenset(seen)


def flow_constants(name: str) -> dict[str, str]:
    """Fields the survey flow sets to a fixed value (not a random draw, not blank)."""
    found: dict[str, str] = {}

    def walk(n: Any) -> None:
        if isinstance(n, dict) and n.get("Type") != "BlockRandomizer":  # those are draws
            if n.get("Type") == "EmbeddedData":
                for e in n.get("EmbeddedData", []):
                    v = e.get("Value")
                    if v and "${" not in str(v):
                        found[e["Field"]] = str(v)
            for c in n.get("Flow", []):
                walk(c)

    d = json.loads((MATERIALS / SPECS[name].qsf).read_text())
    walk(next(e for e in d["SurveyElements"] if e["Element"] == "FL")["Payload"])
    return found


def check_flow(name: str) -> None:
    """The draws the logic reads are recorded; the version markers are what the .qsf sets.

    6d and 6e both set `timing` (12, 20), which nothing in either .qsf reads (no logic, no
    piped text, no JavaScript); 6d's first-day respondents (26 May 2020) have it blank.
    6e's `instructions` IS read (it picks the third instruction screen), so it is a marker.
    """
    spec = SPECS[name]
    used: set[str] = set()
    for q in questions(name):
        for lg in q.logic:
            used |= logic_fields(lg)
    keys = set(embedded(name, kept_index(name)[0]))
    assert used <= keys, used - keys
    consts = flow_constants(name)
    raw = (MATERIALS / spec.qsf).read_text()
    for f, v in consts.items():
        read = f'"LeftOperand":"{f}"' in raw or f"Field\\/{f}" in raw or f"Field/{f}" in raw
        assert read == (f in spec.markers), (f, read)
        if f in spec.markers:
            assert spec.markers[f] == v
    assert set(spec.markers) <= set(consts)


def gender_labels(name: str) -> dict[str, str]:
    """Exported gender value -> the .qsf's label."""
    sv = Survey(SPECS[name].qsf)
    (p,) = [p for p in sv.by_id.values() if p["DataExportTag"] == "Q181"]
    assert plain(p["QuestionText"]) == "What is your gender?"
    rec = p.get("RecodeValues") or {}
    return {str(rec.get(k, k)): plain(c["Display"]) for k, c in p["Choices"].items()}


def age(text: str) -> int | None:
    t = text.strip()
    return int(t) if t.isdigit() and 18 <= int(t) <= 100 else None


def data_file(name: str) -> str:
    return f"{STUDY_ID}_{name}.csv"


def prep(name: str) -> pd.DataFrame:
    """One coded row per built person: each trial's arm code and answer, and the persona."""
    e = experiment(name)
    idx = list(built_index(name))
    rid = named(name, "ResponseId")
    out = pd.DataFrame({"pid": [f"{name}_{rid[i]}" for i in idx]})
    for q in e.questions:
        col = column(name, q.qid)
        pos = {v: k for k, v in enumerate(q.export, 1)}
        out[q.arm_var] = pd.array([q.arm if col[i] else pd.NA for i in idx], dtype="Int64")
        out[q.var] = pd.array([pos[col[i]] if col[i] else pd.NA for i in idx], dtype="Int64")
    out["age"] = pd.array([age(named(name, "Q180")[i]) for i in idx], dtype="Int64")
    labels = gender_labels(name)
    g = [named(name, "Q181")[i] for i in idx]
    assert set(g) <= set(labels) | {""}, set(g)
    out["gender"] = [labels.get(x) for x in g]
    assert out["pid"].is_unique and len(out) == SPECS[name].n_built
    return out


# ---------------------------------------------------------------------------
# The recipe
# ---------------------------------------------------------------------------


def factor_names(e: Experiment) -> list[str]:
    width = max(len(a) for a in e.arms)
    return [f"option_{k}" for k in range(1, width + 1)]


def recipe(e: Experiment) -> dict[str, Any]:
    spec = e.spec
    fnames = factor_names(e)
    first = e.questions[0].arm_var
    arms = [
        {
            "raw_values": {first: k},
            "condition_num": k - 1,
            "factors": {
                f: (" / ".join(opts[j]) if j < len(opts) else "-") for j, f in enumerate(fnames)
            },
            "text": arm_text(opts),
        }
        for k, opts in enumerate(e.arms, 1)
    ]
    outcomes = [
        {
            "var": q.var,
            "task_num": t,
            "question": question_text(len(q.options)),
            "scale": {"min": 1, "max": len(q.options), "nominal": True},
            "condition_var": q.arm_var,
        }
        for t, q in enumerate(e.questions)
    ]
    never = [q.tag for q in questions(e.name) if q.tag not in answered_tags(e.name)]
    notes = (
        f"{PAPER}\n\nGENERATED by scripts/gen_researchbox124.py; every judgement is in its "
        f"docstring. {e.name[5:].upper()} ({spec.prereg}, 2020), {spec.n_kept} of "
        f"{spec.n_finished} finished kept by the authors' rule (all three dominance checks "
        "right)"
        + (
            f"; {spec.n_kept - spec.n_built} of them, who started on the first day before the "
            "flow set instructions = 'new' (which picks the third instruction screen), are not "
            f"built, as which version of that screen they read cannot be determined: "
            f"{spec.n_built} built"
            if spec.n_built != spec.n_kept
            else ""
        )
        + ". Incentivised choices between gambles, each a dollar amount and a way to win "
        "it by coins, dice or cards; one option may let the person pick between two ways to "
        "win (A or B). Per-person draws, recorded, decide which version of each set's trials a "
        "person meets; every trial question is its own outcome naming its own arm column "
        f"(a_<tag>), {len(e.questions)} questions over {len(e.arms)} distinct choice sets. "
        "All trials were in one block in a random order the deposit does not record, so no "
        "row names another, and the order of the options on screen was randomised and not "
        "recorded, so they are listed in the .qsf's order. The trial screens carry no "
        "question text. Every row opens with the instruction screens word-for-word (without "
        "their INSTRUCTIONS headings and the line 'Click the arrow to continue reading the "
        "instructions.'); the comprehension questions, the three dominance checks and "
        "everything after the trials are not narrated. Added words (ours): "
        f"'{RANDOM_ORDER}' after the instructions; 'Option 1:', 'Option 2:'"
        + (", 'Option 3:'" if len(fnames) == 3 else "")
        + ' before each option; and, after the question, \'1 means "Option 1"; 2 means '
        '"Option 2".\''
        + (" (with '; 3 means \"Option 3\"' for three options)" if len(fnames) == 3 else "")
        + ". The question, 'Choose whichever option you prefer.', is transcribed from "
        "Instructions1 ('In each decision, you should choose whichever option you prefer.'); "
        "it is not on the trial screens. Codes are each option's position in that list, mapped from the export's values "
        "through the .qsf's RecodeValues."
        + (
            f" Fielded but answered by no kept person, not declared: {', '.join(never)}."
            if never
            else ""
        )
        + f"\n\nWording from {spec.qsf} (a 2026 copy of the fielded survey; every trial column "
        f"of {spec.raw} carries the ImportId of its .qsf question), word-for-word; no picture "
        "and no JavaScript in it. Typography normalised (HTML, non-breaking spaces, curly "
        "quotes). Data: the raw export (three header rows). Persona: age (a text box; 18-100 "
        "kept, else blank) and gender (the .qsf's labels). US sample (MTurk); dollar stakes."
    )
    return {
        "study_id": STUDY_ID,
        "source": "researchbox",
        "experiment": e.name,
        "title": spec.title,
        "data_file": data_file(e.name),
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": "pid",
        "notes": notes,
        "condition": {
            "source_vars": [first],
            "shared_context": f"{instructions(e.name)}\n\n{RANDOM_ORDER}",
            "factors": fnames,
            "arms": arms,
        },
        "outcomes": outcomes,
        "response_recode": {k: k for k in range(1, len(fnames) + 1)},
        "missing_codes": [],
        "persona_map": {"age": "age", "gender": "gender"},
    }


def recipe_path(name: str) -> Path:
    return RECIPES / f"{STUDY_ID}_{name}.yaml"


def render(name: str) -> str:
    return yaml.safe_dump(recipe(experiment(name)), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prep", action="store_true", help="code the data")
    ap.add_argument("--check", action="store_true", help="exit 1 if any recipe differs")
    args = ap.parse_args()
    if args.prep:
        check_pictures()
        for name in SPECS:
            check_columns(name)
            check_flow(name)
            path = RAW / data_file(name)
            prep(name).to_csv(path, index=False)
            print(f"wrote {path.relative_to(REPO)}")
        return 0
    status = 0
    for name in SPECS:
        path, text = recipe_path(name), render(name)
        if args.check:
            same = path.exists() and path.read_text() == text
            print(("matches " if same else "DIFFERS ") + path.name)
            status |= 0 if same else 1
        else:
            path.write_text(text)
            print(f"wrote {path.relative_to(REPO)}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
