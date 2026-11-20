#!/usr/bin/env python3
"""Write recipes/researchbox547_*.yaml: a parent orders lunch for their child, then for themselves.

ResearchBox 547 ("Sharing Food Can Backfire", Wight et al., https://researchbox.org/547), read
from its Zenodo copy (record 21931233, https://zenodo.org/records/21931233). CC BY 4.0 ("All
content posted to ResearchBox is under a CC By 4.0 License", the box page). The paper was not
read; the answer key is the authors' own SPSS syntax (Code/*.sps), transcribed and re-run on
the deposit and on the built rows. US-run Prolific samples of parents who live with their
child, 2021-2022 (the screener asks about the respondent's "biological child").

Every judgement is here, in code, so the recipes can be re-derived and reviewed.

THE BOX. Studies 1-5, each with a .qsf and its printout (Materials/), one .sav (Data/, the
authors' analysis file: the Qualtrics export plus their dummy codes and filters), a codebook
made from it, the authors' SPSS syntax (Code/) and an AsPredicted pre-registration. Plus two
interview guides for a qualitative study (no data). Files are tied to a study by the
AsPredicted number in their names (#80516 Study 2, #102770 Study 3, #73198 Study 4, #78575
Study 5), which is also the "AsPredicted" field each .qsf's flow sets and each .sav records
(asserted). The box's Table of Contents swaps the "Data" and "Codebook" section labels of
Studies 2 and 3 (it files "Study 3 #102770 ... .sav" under "Study 2"); the file names, the
syntax and the pre-registrations all agree with each other, so the file names are followed.
The .qsf files are blinded copies made after fielding (survey names "Blind_ECFO_StudyN_
AsPredNNNNN", created Dec 2021 / Jan 2023, after each study's fielding dates; the survey-name
numbers are the authors' working numbers, not the box's). Proof they are the fielded
instrument, asserted for every kept person: every randomised value the .sav records (share,
shareText, menuOrder/DVorder, CFO, temporalCondition, ...) is one the .qsf's randomiser sets
for that person's arm, and the .sav's own variable labels (written by Qualtrics at export)
quote each built question word-for-word with its pipes, and its value labels are the
question's options in the .qsf's recode order (`check_sav_labels`).

WHAT IS BUILT (one recipe each, all between people; the answer is the parent's own meal):
- study2 (#80516, Nov-Dec 2021): an invented meal-planning service will send the parent and
  child two trial meals to eat together. After choosing the child's meal from the kids' menu,
  the parent is told they CAN or CANNOT share their grown-up's meal with the child, and picks
  one of eight grown-up's meals (four healthy, four not). Menu order (healthy or unhealthy
  first) counterbalanced. 4 arms. Kind "version" (share is the manipulation; menu order a
  counterbalance, crossed).
- study3 (#102770, Jul-Aug 2022, mothers only: the screener ends the survey for anyone not
  answering "Female"): first told to make choices that best meet the child's needs in the
  moment, or that best prepare the child for success as an adult; then, at an invented cafe,
  orders for the child (two healthy options), then orders an entree for herself knowing she
  WILL or will NOT share it. 2 x 2 x menu order = 8 arms. Kind "mix".
- study4 (#73198, Aug 2021): the same cafe; the two kids' options that "stand out" are both
  healthy or both indulgent (the CFO factor), crossed with sharing and menu order. 8 arms.
  Kind "mix".

NOT BUILT (NOT_BUILT):
- study1: a field study at a nursery school (rich, 20 Nov 2026: flagged by the UK screen).
- study5: the manipulation is the person's own earlier answer shown back. Parents first sort
  eight lunches into the two their child would like most and least (a drag-and-drop); the
  child's lunch options at the event are then carried forward from that sort (QID87/QID88,
  DynamicChoices on QID81/QID82, "SelectedChoicesInGroup" of QID76), the "like" arm showing
  the two the parent had said the child likes most and the "dislike" arm the two least. A
  row would have to name those meals, which are the person's own answers.

WHAT EACH ROW IS. Persona: the parent. Condition: every screen from the child's-name
question to the self-choice page, simulated from the .qsf's flow for the arm (display logic
on embedded fields evaluated, piped fields filled), word-for-word, one paragraph per screen
part. Outcome: the self-choice question with its eight options enumerated in their on-screen
order ('1 means "..."; 2 means "..."', the 2057 layout, ours), the answer coded to its
option's position on screen (so the two menu orders code the same meal differently; each
arm's response_recode maps the .qsf's recode value, which names the meal, to its position).
Dropped as survey mechanics: consent, Prolific id, captcha, the "switch off your phone"
screen, the screener (every kept person gave the answer that lets the survey continue;
Study 3's gender question is also its screener), and timing.

THE CHILD'S NAME (the fill the deposit must not give). The survey asks for "the first name
or first initial of your child" and pipes what was typed into later screens and into the
outcome question itself ("... share your grown-up's meal with ${e://Field/name}?"). The
deposit does hold it, but a child's name has no place in a row, and a row may not invent
one. CONVENTIONS ("A per-respondent fill the deposit does not hold", the rule applied to
withheld fills) is followed: the row keeps the instrument's words either side and puts one
clause of ours in the fill's place, CHILD below. It is true only for someone who typed
something; the question was not forced, so people who left it empty (the screen then showed
nothing there) are excluded, a declared count per study (Spec.empty_name, asserted). The
name question itself is narrated as asked. Its answer is not a stimulus a respondent chose
in the sense of the brief's "own earlier answer" rule: it names the child, no opinion or
choice of theirs; the riskiest judgement of this build, so it is stated in the notes.

EARLIER QUESTIONS are narrated as asked, never as given (CONVENTIONS): 'You were asked
"...", with the options "..." and "...".' That covers the child's-meal question (the
parent's own choice for the child, not shown back afterwards on any screen a row carries),
and Study 3's "describe in your own words" check of the focus instruction.

PICTURES (ledger 158: a picture is never described, a screenshot never transcribed). Every
displayed picture is dropped with no clause in its place, because none carries anything the
text lacks: the website or tablet front page (a logo and menu buttons), a "Kids' Menu" title
card, and menu boards whose printed list is the options of the question on the same screen,
in the same order (seen in the printouts, Materials/*PDF.pdf). PICTURES lists each graphic
with that reason; `check_pictures` asserts it is every displayed graphic. Images in
QuestionText_Unsafe (stale copies of an earlier draft) were never displayed and are ignored.

STUDY 4's HIDDEN SENTENCE. In the fielded flow the indulgent arm's "The menu has many
options, but two in particular stand out ... Hamburger w/ fries and Chicken nuggets w/
tater tots." (QID53) is gated on CFO = "indulgent", a value the randomiser never sets (it
sets "healthy" or "unhealthy"). So the healthy arm saw its "stand out" sentence and the
unhealthy arm did not; the unhealthy arm went from the kids' menu screen straight to "Which
would you order for ...?" with the two indulgent options. The rows follow the .qsf.

EXCLUSIONS. The authors' main-analysis filter, FullSampleFilter = 1 (SCREENED = "IN"), then
a self-choice answer present (the logistic regression drops the rest), then the declared
empty-name exclusion. Their robustness filters (child age, Study 3's pre-registered
attention filter) are not applied.

PERSONA. The parent's age (years as typed; outside 18-100 left blank) and gender (the .qsf's
labels Male, Female, Non-binary; "Prefer to self describe" and "Prefer not to say" left
blank). The child's age and gender are about the child and are not used.

ANSWER KEY. Each study's main logistic regression from its .sps (CFS unhealthy 1 / healthy 0
on the authors' dummies and their product), fitted by IRLS on the deposit's own coded
columns and on the BUILT rows (unhealthy read from the factors and the coded position); the
coefficients agree to 1e-9, and every arm's count of unhealthy choices agrees exactly
(tests/test_gen_researchbox547.py, which also records the values).

JEV. scripts/recipe_prep.py --only assignment (--source dataverse, 20 Nov 2026) on each .sav:
see ASSIGNMENT_JEV. It names one column, and these designs cross two or three factors: for
Study 3 it split between the two manipulated factors (shareCondition 0.43, temporalCondition
0.35), and for Study 4 it put CFO, the second manipulated factor, at 0.02. Overruled in that
sense: the assignment fields the build reads are every field the .qsf's one randomiser sets
that varies between its cells, which is the authority.

    uv run python scripts/gen_researchbox547.py --prep   # code the data
    uv run python scripts/gen_researchbox547.py          # write the recipes
    uv run python scripts/gen_researchbox547.py --check  # exit 1 if any recipe differs
"""

from __future__ import annotations

import argparse
import html
import itertools
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import pyreadstat
import yaml

REPO = Path(__file__).resolve().parents[1]
STUDY_ID = "researchbox547"
RAW = REPO / "data" / "raw" / STUDY_ID
BOX = RAW / "ResearchBox 547"
RECIPES = REPO / "recipes"
LICENCE = (
    'CC BY 4.0, stated on the box page https://researchbox.org/547 ("All content posted '
    'to ResearchBox is under a CC By 4.0 License"); read from its Zenodo copy, record '
    "21931233 (https://zenodo.org/records/21931233). Read 20 Nov 2026."
)
SOURCE = (
    'ResearchBox 547, "Sharing Food Can Backfire" (Wight et al., https://researchbox.org/547), '
    "Zenodo record 21931233. The paper was not read."
)

NOT_BUILT = {
    "study1": "Field study at a nursery school (AsPredicted #115216); rich, 20 Nov 2026: "
    "flagged by the UK screen, not built.",
    "study5": "The child-preference manipulation is the person's own earlier answer shown "
    "back: parents sort eight lunches into the two their child would like most and least, "
    "and the child's options at the event are carried forward from that sort (QID87/QID88 "
    "DynamicChoices from QID81/QID82, SelectedChoicesInGroup of QID76). A row would have to "
    "name the meals the person chose.",
}

# One clause of ours in place of the piped child's name (see the docstring).
CHILD = "(here the screen showed what you had typed as your child's name)"

# The answer each kept person gave to a question the flow branches on.
GATES = {"consent": "1", "livingWchild": "1", "childScreener": "1", "gender": "2"}
DROPPED_BLOCKS = {"consent", "screener verification"}

# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

_TYPO = {"\xa0": " ", "\u200b": "", "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"'}
_BREAK = re.compile(r"(?i)<br\s*/?>|</?p[^>]*>|</?div[^>]*>|</?ul[^>]*>|</li>")
_IMG = re.compile(r"<img[^>]*?IM=(IM_\w+)[^>]*>")


def plain(raw: str) -> str:
    """An HTML fragment to one line of plain text. Typography only."""
    s = re.sub(r"<[^>]+>", " ", raw or "")
    s = html.unescape(s)
    for a, b in _TYPO.items():
        s = s.replace(a, b)
    s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r" ([.,?:])", r"\1", s)  # a space the markup left before punctuation


def screen_text(raw: str) -> str:
    """One screen part: paragraphs blank-line separated; pictures dropped (see PICTURES)."""
    s = _IMG.sub("", raw or "")
    s = _BREAK.sub("\n", s)
    return "\n\n".join(t for t in (plain(p) for p in s.split("\n")) if t)


def pipe(raw: str) -> str:
    """Fill the child's name with CHILD. Any other pipe is an error: none is displayed in
    the screens a row carries."""
    out = re.sub(r"\$\{e://Field/name\}|\$\{q://QID7/ChoiceTextEntryValue\}", CHILD, raw)
    assert "${" not in out, out[:300]
    return out


def fill(raw: str, ed: dict[str, str]) -> str:
    """Fill ${e://Field/x} from the arm's embedded data (shareText), then the name."""

    def sub(m: re.Match[str]) -> str:
        f = m.group(1)
        return m.group(0) if f == "name" else ed[f]

    return pipe(re.sub(r"\$\{e://Field/(\w+)\}", sub, raw))


# ---------------------------------------------------------------------------
# The questionnaire, simulated through its flow
# ---------------------------------------------------------------------------


class Survey:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.raw = path.read_text()
        d = json.loads(self.raw)
        self.entry = d["SurveyEntry"]
        els = d["SurveyElements"]
        self.by_id = {e["Payload"]["QuestionID"]: e["Payload"] for e in els if e["Element"] == "SQ"}
        self.blocks: dict[str, dict[str, Any]] = {}
        for e in els:
            if e["Element"] == "BL":
                p = e["Payload"]
                for b in p.values() if isinstance(p, dict) else p:
                    self.blocks[b["ID"]] = b
        self.flow = next(e for e in els if e["Element"] == "FL")["Payload"]

    def tag(self, qid: str) -> str:
        return str(self.by_id[qid]["DataExportTag"])

    def q(self, tag: str) -> dict[str, Any]:
        (p,) = [p for p in self.by_id.values() if p["DataExportTag"] == tag]
        return dict(p)

    def pages(self, block_id: str) -> list[list[str]]:
        """The block's questions, split at its page breaks."""
        out: list[list[str]] = [[]]
        for x in self.blocks[block_id].get("BlockElements", []):
            if x["Type"] == "Page Break":
                out.append([])
            else:
                assert x["Type"] == "Question", x
                out[-1].append(x["QuestionID"])
        return [p for p in out if p]

    def holds(self, logic: dict[str, Any], ed: dict[str, str]) -> bool:
        """A BooleanExpression of If/Or conditions on embedded fields or gate questions."""
        (expr,) = [v for k, v in logic.items() if k.isdigit()]
        conds = [v for k, v in sorted(expr.items()) if k.isdigit()]
        vals = []
        for i, c in enumerate(conds):
            assert i == 0 or c.get("Conjuction") == "Or", c
            if c["LogicType"] == "EmbeddedField":
                assert c["Operator"] == "EqualTo", c
                vals.append(ed.get(c["LeftOperand"]) == c["RightOperand"])
                continue
            assert c["LogicType"] == "Question", c
            m = re.fullmatch(r"q://(QID\d+)/SelectableChoice/(\d+)", c["LeftOperand"])
            assert m, c
            chosen = GATES[self.tag(m.group(1))] == m.group(2)
            vals.append({"Selected": chosen, "NotSelected": not chosen}[c["Operator"]])
        return any(vals)

    def walk(self, arm: dict[str, str]) -> tuple[dict[str, str], list[str]]:
        """(embedded data, the blocks reached in order) for one assignment. The one
        randomiser over embedded-data children is the assignment: it takes the child that
        sets every field of the arm to the arm's value."""
        ed: dict[str, str] = {}
        seq: list[str] = []

        def go(n: dict[str, Any]) -> bool:  # False: the survey ended
            t = n.get("Type")
            if t == "EmbeddedData":
                for e in n["EmbeddedData"]:
                    if e.get("Value") is not None:
                        ed[e["Field"]] = e["Value"]
                return True
            if t == "BlockRandomizer":
                kids = n["Flow"]
                assert all(k["Type"] == "EmbeddedData" for k in kids), n["FlowID"]
                assert n["SubSet"] in (1, "1") and n.get("EvenPresentation"), n["FlowID"]
                hit = [
                    k
                    for k in kids
                    if all(
                        any(e["Field"] == f and e.get("Value") == v for e in k["EmbeddedData"])
                        for f, v in arm.items()
                    )
                ]
                assert len(hit) == 1, (n["FlowID"], arm)
                return go(hit[0])
            if t == "Branch":
                if self.holds(n["BranchLogic"], ed):
                    return all(go(c) for c in n.get("Flow", []))
                return True
            if t in ("Block", "Standard"):
                seq.append(n["ID"])
                return True
            if t == "EndSurvey":
                return False
            assert t == "Root", t
            for c in n.get("Flow", []):
                if not go(c):
                    break
            return True

        go(self.flow)
        return ed, seq

    def shown(self, qid: str, ed: dict[str, str]) -> bool:
        dl = self.by_id[qid].get("DisplayLogic")
        return True if not dl else self.holds(dl, ed)

    def randomiser_cells(self) -> list[dict[str, str]]:
        """Each child of the assignment randomiser: the embedded fields it sets."""
        out: list[dict[str, str]] = []

        def go(n: dict[str, Any]) -> None:
            if n.get("Type") == "BlockRandomizer":
                for k in n["Flow"]:
                    out.append({e["Field"]: e["Value"] for e in k["EmbeddedData"]})
            for c in n.get("Flow", []):
                go(c)

        go(self.flow)
        return out


def displayed_graphics(sv: Survey) -> dict[str, list[str]]:
    """Graphic ids in each question's displayed QuestionText (not the stale _Unsafe copy)."""
    out = {}
    for qid, p in sv.by_id.items():
        ims = _IMG.findall(p.get("QuestionText", ""))
        if ims:
            out[qid] = ims
    return out


# ---------------------------------------------------------------------------
# The studies
# ---------------------------------------------------------------------------


@dataclass
class Spec:
    name: str
    asp: str  # AsPredicted number, the file key
    assign: dict[str, str]  # embedded field -> factor name
    label: str  # the .sav dummy the authors use for each factor: factor -> (column, level=1)
    outcome_tags: dict[str, str]  # menu order value -> the self-choice question's export tag
    order_field: str
    kind: str
    title: str
    sample: str
    n_kept: int  # after the authors' filter and a self-choice answer, before the name rule
    empty_name: int  # of those, left the child's-name box empty (excluded, declared)
    dv: str  # the authors' 0/1 unhealthy dummy
    key: list[tuple[str, str]]  # the .sps main model's dummies: (column, factor=level as 1)
    fills: list[str]  # .sav columns the randomiser sets, checked against the arm


SPECS = [
    Spec(
        name="study2",
        asp="80516",
        assign={"share": "share", "menuOrder": "menu_order"},
        label="Study 2 (AsPredicted #80516)",
        outcome_tags={"healthyFirst": "CFS_1-4H_hfirst", "unhealthyFirst": "CFS_5-8u_ufirst"},
        order_field="menuOrder",
        kind="version",
        title="A meal-planning service will send a parent and child trial meals to eat "
        "together: after choosing the child's meal, the parent is told they can or cannot "
        "share theirs, and picks one of eight grown-up's meals (Study 2)",
        sample="Prolific, 19 Nov to 2 Dec 2021",
        n_kept=792,
        empty_name=1,
        dv="CFS_1Unh0Hthy",
        key=[("share1_not0", "share=yes")],
        fills=["share", "shareText", "menuOrder", "shareText2"],
    ),
    Spec(
        name="study3",
        asp="102770",
        assign={"temporalCondition": "focus", "shareCondition": "share", "DVorder": "menu_order"},
        label="Study 3 (AsPredicted #102770)",
        outcome_tags={"healthyFirst": "CFS_1-4H_hfirst", "unhealthyFirst": "CFS_5-8u_ufirst"},
        order_field="DVorder",
        kind="mix",
        title="A mother told to choose what best meets her child's needs in the moment, or "
        "what best prepares the child for adult life, orders the child's lunch at a cafe and "
        "then her own entree, knowing she will or will not share it (Study 3)",
        sample="Prolific, 19 Jul to 3 Aug 2022, mothers only",
        n_kept=548,
        empty_name=1,
        dv="CFS_1unh_0hthy",
        key=[("present1future0", "focus=present"), ("share1not0", "share=yes")],
        fills=[
            "temporalCondition",
            "shareCondition",
            "DVorder",
            "shareText",
            "share1not0",
            "present1future0",
            "attCheck_correctText",
            "attCheck_wrongText",
        ],
    ),
    Spec(
        name="study4",
        asp="73198",
        assign={"CFO": "child_meal", "share": "share", "menuOrder": "menu_order"},
        label="Study 4 (AsPredicted #73198)",
        outcome_tags={"healthyFirst": "CFS_1-4H_hfirst", "unhealthyFirst": "CFS_5-8u_ufirst"},
        order_field="menuOrder",
        kind="mix",
        title="At a cafe, the two kids' meals that stand out for a parent's child are both "
        "healthy or both indulgent; the parent orders one, then an entree for themselves, "
        "knowing they will or will not share it (Study 4)",
        sample="Prolific, 23 Aug 2021",
        n_kept=830,
        empty_name=0,
        dv="CFS_1unh0hthy",
        key=[("CFO_1hthy0unh", "child_meal=healthy"), ("Share_1y0n", "share=yes")],
        fills=["CFO", "share", "shareText", "menuOrder"],
    ),
]
BY_NAME = {s.name: s for s in SPECS}

# Jev's answer to "which column is the randomised assignment" on each .sav (recipe_prep).
ASSIGNMENT_JEV = {
    "study2": "share (conf 0.95; next share1_not0 0.04)",
    "study3": "shareCondition (conf 0.43, REVIEW; next temporalCondition 0.35, share1not0 0.12)",
    "study4": "share (conf 0.75, REVIEW; next Share_1y0n 0.21, CFO 0.02)",
}


def qsf_path(spec: Spec) -> Path:
    (p,) = (BOX / "Materials").glob(f"Study * #{spec.asp} Qualtrics Survey QSF.qsf")
    return p


def sav_path(spec: Spec) -> Path:
    (p,) = (BOX / "Data").glob(f"Study * #{spec.asp} data and codebook.sav")
    return p


def study_number(spec: Spec) -> str:
    return spec.name.removeprefix("study")


def check_files(spec: Spec) -> None:
    """Materials, data, code and pre-registration carry the same study number for the
    AsPredicted number, and the .qsf's flow sets that number."""
    n = study_number(spec)
    for sub, pat in [
        ("Materials", f"Study {n} #{spec.asp} Qualtrics Survey QSF.qsf"),
        ("Data", f"Study {n} #{spec.asp} data and codebook.sav"),
        ("Code", f"Study {n} #{spec.asp} syntax.sps"),
        ("Pre-Registration", f"Study {n} - AsPredicted #{spec.asp}.pdf"),
    ]:
        assert (BOX / sub / pat).exists(), (sub, pat)
    ed, _ = Survey(qsf_path(spec)).walk(levels_first(spec))
    assert ed["AsPredicted"] == spec.asp


# ---------------------------------------------------------------------------
# Pictures (read from the printouts; see the docstring)
# ---------------------------------------------------------------------------

# Every displayed graphic, with why dropping it loses nothing the text lacks (ledger 158:
# a picture is never described, a screenshot never transcribed). Seen in the printouts.
PICTURES: dict[str, dict[str, str]] = {
    "study2": {
        "IM_0Hwia6r7xk4qbSC": "the website's front page: logo and three menu buttons",
        "IM_bEsif0Tn2ihIx0y": "the kids' menu board: the four options of the question beneath",
        "IM_6tcJvWBoF1h6dg2": "the grown-up's menu board: the question's eight options, same order",
        "IM_6DPw8ix3Bvo0MF8": "the grown-up's menu board: the question's eight options, same order",
    },
    "study3": {
        "IM_5dpWrI0sGnVmSI6": "the tablet's front page: logo and six menu-section buttons",
        "IM_3E3bOk1j9zacbC6": 'a "Kids\' Menu" title card',
        "IM_3IDe5ctoYnYH0zk": "the entrees board: the question's eight options, same order",
        "IM_cHmIy5JcFYCxUO2": "the entrees board: the question's eight options, same order",
    },
}
PICTURES["study4"] = PICTURES["study3"]


def options(p: dict[str, Any]) -> list[str]:
    """A choice question's options, in their on-screen order."""
    assert not p.get("Randomization"), p["DataExportTag"]
    return [plain(p["Choices"][str(k)]["Display"]) for k in p["ChoiceOrder"]]


def check_pictures(spec: Spec) -> None:
    """The displayed pictures are exactly those PICTURES lists as dropped, and nothing else
    in the .qsf's displayed text is a picture."""
    sv = Survey(qsf_path(spec))
    shown = {im for ims in displayed_graphics(sv).values() for im in ims}
    assert shown == set(PICTURES[spec.name]), (spec.name, shown)


# ---------------------------------------------------------------------------
# Arms
# ---------------------------------------------------------------------------


def levels(spec: Spec) -> dict[str, list[str]]:
    """Each assignment field's values, in the randomiser's order."""
    cells = Survey(qsf_path(spec)).randomiser_cells()
    out: dict[str, list[str]] = {f: [] for f in spec.assign}
    for c in cells:
        for f in spec.assign:
            if c[f] not in out[f]:
                out[f].append(c[f])
    n = 1
    for v in out.values():
        n *= len(v)
    assert n == len(cells), (spec.name, out)  # a full crossing, each cell once
    return out


def levels_first(spec: Spec) -> dict[str, str]:
    return {f: v[0] for f, v in levels(spec).items()}


@dataclass
class Arm:
    values: dict[str, str]
    ed: dict[str, str]
    text: str
    question: str  # the self-choice question with its options enumerated
    recode: dict[int, int]  # the .qsf recode value (the meal) -> position on screen
    tag: str


def asked(p: dict[str, Any], ed: dict[str, str]) -> str:
    q = plain(fill(p["QuestionText"], ed))
    if p["QuestionType"] == "TE":
        return f'You were asked "{q}"'
    assert p["QuestionType"] == "MC", p["DataExportTag"]
    opts = options(p)
    listed = ", ".join(f'"{o}"' for o in opts[:-1]) + f' and "{opts[-1]}"'
    return f'You were asked "{q}", with the options {listed}.'


def build_arm(spec: Spec, values: dict[str, str]) -> Arm:
    sv = Survey(qsf_path(spec))
    ed, seq = sv.walk(values)
    for f, v in values.items():
        assert ed[f] == v
    target = spec.outcome_tags[ed[spec.order_field]]
    parts: list[str] = []
    outcome: dict[str, Any] | None = None
    for b in seq:
        if sv.blocks[b]["Description"] in DROPPED_BLOCKS:
            continue
        for page in sv.pages(b):
            for qid in page:
                p = sv.by_id[qid]
                if not sv.shown(qid, ed):
                    continue
                if p["DataExportTag"] == target:
                    outcome = p
                    break
                if p["QuestionType"] == "DB":
                    for im in _IMG.findall(p["QuestionText"]):
                        assert im in PICTURES[spec.name], im
                    t = screen_text(fill(p["QuestionText"], ed))
                    if t:
                        parts.append(t)
                else:
                    assert p["DataExportTag"] in {"name", "CFOhealthy", "CFOunhealthy", "emphasis"}
                    assert not _IMG.findall(p["QuestionText"])
                    parts.append(asked(p, ed))
            if outcome is not None:
                break
        if outcome is not None:
            break
    assert outcome is not None, (spec.name, values)
    stem = plain(fill(outcome["QuestionText"], ed))
    opts = options(outcome)
    enum = "; ".join(f'{i} means "{o}"' for i, o in enumerate(opts, 1))
    rv = outcome["RecodeValues"]
    recode = {int(rv[str(k)]): i for i, k in enumerate(outcome["ChoiceOrder"], 1)}
    assert sorted(recode) == list(range(1, 9)), recode
    return Arm(values, ed, "\n\n".join(parts), f"{stem} {enum}.", recode, target)


def arms(spec: Spec) -> list[Arm]:
    lv = levels(spec)
    return [build_arm(spec, dict(zip(lv, c, strict=True))) for c in itertools.product(*lv.values())]


# The meals the authors code unhealthy: recode values 5-8 (CFS_1_4H >= 5; asserted against
# their 0/1 dummy on every kept row). The .qsf's recode order lists the four healthy first.
UNHEALTHY = {5, 6, 7, 8}


def meal_names(spec: Spec) -> dict[int, str]:
    """Recode value -> meal, from the healthy-first question."""
    p = Survey(qsf_path(spec)).q(spec.outcome_tags["healthyFirst"])
    rv = p["RecodeValues"]
    return {int(rv[k]): plain(c["Display"]) for k, c in p["Choices"].items()}


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

AGE_RANGE = (18, 100)
GENDER_KEEP = {1: "Male", 2: "Female", 3: "Non-binary"}


def read_deposit(spec: Spec) -> tuple[pd.DataFrame, Any]:
    df, meta = pyreadstat.read_sav(str(sav_path(spec)))
    return df, meta


def analysed(spec: Spec) -> pd.DataFrame:
    """The authors' main-analysis sample: FullSampleFilter = 1 and a self-choice answer."""
    df, _ = read_deposit(spec)
    df = df[df["FullSampleFilter"] == 1]
    assert (df["SCREENED"] == "IN").all()
    df = df[df["CFS_1_4H"].notna()]
    assert len(df) == spec.n_kept, (spec.name, len(df))
    return df


def name_empty(df: pd.DataFrame) -> pd.Series:
    """Whether the child's-name box was left empty (the value itself is never read out)."""
    return df["name"].fillna("").str.strip() == ""


def kept(spec: Spec) -> pd.DataFrame:
    df = analysed(spec)
    empty = name_empty(df)
    assert int(empty.sum()) == spec.empty_name, (spec.name, int(empty.sum()))
    return df[~empty]


def sav_tag(tag: str) -> str:
    return tag.replace("-", "_")


def check_sav_labels(spec: Spec) -> None:
    """The .sav's export labels quote each built question, and its value labels are the
    options in recode order: the columns answer those questions."""
    sv = Survey(qsf_path(spec))
    _, meta = read_deposit(spec)
    lab = meta.column_names_to_labels
    vl = meta.variable_value_labels

    def as_exported(raw: str) -> str:
        s = re.sub(r"\$\{e://Field/(\w+)\}", r"[Field-\1]", raw)
        s = re.sub(r"\$\{q://(QID\d+)/ChoiceTextEntryValue\}", r"[\1-ChoiceTextEntryValue]", s)
        return re.sub(r"\s+", " ", plain(s))

    tags = [*spec.outcome_tags.values()] + [
        t
        for t in ("CFOhealthy", "CFOunhealthy")
        if any(p["DataExportTag"] == t for p in sv.by_id.values())
    ]
    for t in tags:
        p = sv.q(t)
        assert re.sub(r"\s+", " ", lab[sav_tag(t)]) == as_exported(p["QuestionText"]), t
        rv = p.get("RecodeValues") or {k: k for k in p["Choices"]}
        want = {float(rv[k]): plain(c["Display"]) for k, c in p["Choices"].items()}
        got = {k: re.sub(r"\s+", " ", v).strip() for k, v in vl[sav_tag(t)].items()}
        assert got == want, (t, got, want)


def check_data_matches_qsf(spec: Spec, df: pd.DataFrame) -> None:
    """Every kept row's recorded fills are exactly what the .qsf's flow sets for its
    assignment, and its self-choice answer is in the column the arm's menu order shows (the
    other blank), coded unhealthy by the authors exactly when the meal is 5-8."""
    sv = Survey(qsf_path(spec))
    eds = {
        combo: sv.walk(dict(zip(spec.assign, combo, strict=True)))[0]
        for combo in itertools.product(*levels(spec).values())
    }
    for _, r in df.iterrows():
        ed = eds[tuple(r[f] for f in spec.assign)]
        for f in spec.fills:
            v = str(int(r[f])) if isinstance(r[f], float) else r[f]
            assert v == ed[f], (spec.name, f, v, ed[f])
        shown = sav_tag(spec.outcome_tags[r[spec.order_field]])
        (other,) = [sav_tag(t) for t in spec.outcome_tags.values() if sav_tag(t) != shown]
        assert r[shown] == r["CFS_1_4H"] and pd.isna(r[other]), spec.name
        assert int(r[spec.dv]) == int(r["CFS_1_4H"] in UNHEALTHY), spec.name


def check_order_unrecorded(spec: Spec) -> None:
    """Nothing to narrate: the build's screens are in a fixed order (no block randomiser
    besides the assignment; no _DO column)."""
    df, _ = read_deposit(spec)
    assert not [c for c in df.columns if c.endswith("_DO") or c.startswith("FL_")]


def codes(spec: Spec) -> dict[str, dict[str, int]]:
    return {f: {v: i for i, v in enumerate(vals, 1)} for f, vals in levels(spec).items()}


def data_file(spec: Spec) -> str:
    return f"{STUDY_ID}_{spec.name}.csv"


def prep(spec: Spec) -> pd.DataFrame:
    """One coded row per kept person: assignment codes, the meal (recode value), age, gender."""
    check_files(spec)
    check_sav_labels(spec)
    check_pictures(spec)
    check_order_unrecorded(spec)
    df = kept(spec)
    check_data_matches_qsf(spec, df)
    out = pd.DataFrame({"pid": [f"{spec.name}_{i}" for i in df.index]})
    for f, cmap in codes(spec).items():
        out[f] = df[f].map(cmap).astype(int).values
    out["cfs"] = df["CFS_1_4H"].astype(int).values
    agecol = "age" if "age" in df.columns else "parentAge"
    age = pd.to_numeric(df[agecol], errors="coerce")
    out["age"] = age.where(age.between(*AGE_RANGE)).round().astype("Int64").values
    gcol = "gender" if "gender" in df.columns else "parentGender"
    out["gender"] = df[gcol].map(lambda x: GENDER_KEEP.get(int(x)) if pd.notna(x) else None).values
    assert out["pid"].is_unique
    return out


# ---------------------------------------------------------------------------
# The recipes
# ---------------------------------------------------------------------------

NOT_BUILT_OUTCOMES = {
    "study2": "Not built: the mediator items (set an example, concern, sharing the kid's meal), "
    'anticipated enjoyment and the trial opt-in, which follow an "Order Summary" screen '
    "naming both meals the person chose.",
    "study3": "Not built: nothing else is asked after the self-choice except demographics and "
    "the end-of-survey recall check (attention, the authors' robustness filter).",
    "study4": "Not built: the sharing manipulation check, whose question names the entree "
    "the person chose.",
}


def recipe(spec: Spec) -> dict[str, Any]:
    arm_list = arms(spec)
    cmap = codes(spec)
    first = arm_list[0]
    out_arms = []
    for i, a in enumerate(arm_list):
        out_arms.append(
            {
                "raw_values": {f: cmap[f][v] for f, v in a.values.items()},
                "condition_num": i,
                "factors": {spec.assign[f]: v for f, v in a.values.items()},
                "text": a.text,
                "items": {
                    0: {
                        "outcome_question": a.question,
                        "response_recode": a.recode,
                        "condition_text": a.text,
                    }
                },
            }
        )
    meals = meal_names(spec)
    notes = (
        f"{SOURCE}\n\nGENERATED by scripts/gen_researchbox547.py; every judgement is in its "
        f"docstring. {spec.label}; {spec.sample}; US-run sample of parents living with their "
        f"child. {spec.n_kept - spec.empty_name:,} people: the authors' main-analysis filter "
        f"(FullSampleFilter = 1) with a self-choice answer ({spec.n_kept:,}), less "
        f"{spec.empty_name} who left the child's-name box empty. Between people: one arm each, "
        f"assigned by the .qsf's one randomiser ({', '.join(spec.assign)}; every recorded "
        "fill checked against it for every kept person). The row is every screen from the "
        "child's-name question to the self-choice page, word-for-word with its piped fields "
        "filled; consent, id, captcha, the phone screen and the screener are dropped. Earlier "
        "questions are narrated as asked ('You were asked \"...\", with the options ...'). "
        f"Added words (ours): '{CHILD}' wherever the screen piped the name typed for the "
        "child (CONVENTIONS, a per-respondent fill the deposit does not give); and the "
        "enumeration of the eight options after the question, 'N means \"...\"'. Pictures "
        "are dropped, not described (ledger 158): front pages, a title card, and menu boards "
        "whose words are the question's own options in the same order. The answer is coded to its option's position on screen; "
        "the meals by the .qsf's recode value (healthy 1-4, unhealthy 5-8) are "
        + "; ".join(f'{k} "{v}"' for k, v in sorted(meals.items()))
        + ". The menu order (healthy or unhealthy meals listed first) shows only in the "
        "order of the question's options, so `menu_order` is carried on every arm but is not "
        "a condition factor, and each pair of arms differing only in it declares its shared "
        "text (condition_text), as researchbox2057 does."
        + f" {NOT_BUILT_OUTCOMES[spec.name]}"
        + (
            " In the fielded flow the indulgent arm's 'stand out' sentence (QID53) is gated on "
            'CFO = "indulgent", which the randomiser never sets, so only the healthy arm saw '
            "its 'stand out' sentence; the rows follow the .qsf."
            if spec.name == "study4"
            else ""
        )
        + f"\n\nWording from {qsf_path(spec).name} (the blocks the survey flow reaches), a "
        "blinded copy whose randomised values and question labels match the .sav. Typography "
        "normalised (HTML, non-breaking spaces, curly quotes); bold and underline dropped. "
        f"Data: {sav_path(spec).name}. Persona: the parent's age (years; outside 18-100 left "
        "blank) and gender (the .qsf's labels; self-described and 'Prefer not to say' left "
        "blank)."
    )
    return {
        "study_id": STUDY_ID,
        "source": "researchbox",
        "experiment": spec.name,
        "title": spec.title,
        "data_file": data_file(spec),
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": "pid",
        "notes": notes,
        "condition": {
            "source_vars": list(spec.assign),
            "factors": [f for f in spec.assign.values() if f != "menu_order"],
            "arms": out_arms,
        },
        "outcomes": [
            {
                "var": "cfs",
                "task_num": 0,
                "question": first.question,
                "scale": {"min": 1, "max": 8, "nominal": True},
            }
        ],
        "response_recode": {k: k for k in range(1, 9)},
        "missing_codes": [],
        "persona_map": {"age": "age", "gender": "gender"},
    }


def recipe_path(spec: Spec) -> Path:
    return RECIPES / f"{STUDY_ID}_{spec.name}.yaml"


def render(spec: Spec) -> str:
    return yaml.safe_dump(recipe(spec), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prep", action="store_true", help="code the data")
    ap.add_argument("--check", action="store_true", help="exit 1 if any recipe differs")
    args = ap.parse_args()
    if args.prep:
        for spec in SPECS:
            path = RAW / data_file(spec)
            prep(spec).to_csv(path, index=False)
            print(f"wrote {path.relative_to(REPO)}")
        return 0
    bad = 0
    for spec in SPECS:
        path, text = recipe_path(spec), render(spec)
        if args.check:
            same = path.exists() and path.read_text() == text
            bad += not same
            print(("matches " if same else "DIFFERS ") + path.name)
        else:
            path.write_text(text)
            print(f"wrote {path.relative_to(REPO)}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
