#!/usr/bin/env python3
"""Write recipes/researchbox482_*.yaml: time estimates and customer satisfaction (15 recipes).

Hu B, Gaertig C, Dietvorst BJ, "How Should Time Estimates be Structured to Increase Customer
Satisfaction?" (the manuscript title in the box's ReadMe; the deposit names no journal or
year). ResearchBox 482 ("Time Estimates and Customer Satisfaction",
https://researchbox.org/482), read from its Zenodo copy (record 15033033,
https://zenodo.org/records/15033033). CC BY 4.0 ("All content posted to ResearchBox is under
a CC By 4.0 License", the box page). US online samples (MTurk via CloudResearch, Prolific).
The paper was not read; the answer key is the authors' own Stata code (Code/Study N.do),
transcribed and re-run on the deposit and on the built rows, with the Ns and the S3 numbers
the Online Supplement reports.

Every judgement is here, in code, so the recipes can be re-derived and reviewed.

THE BOX. Eleven studies (1-8, S1-S3), each with a .qsf, a survey doc of screenshots, an .xlsx
data file (one header row, codes), a codebook, a Stata do file and an AsPredicted
pre-registration; plus "Underlying Distributions.xlsx", the ReadMe, a note on Study 1's
condition names and the Online Supplement (.docx). The .qsf files are 2024 copies
(SurveyCreationDate 2024-07-24 for S3; S3 was pre-registered in Nov 2023), so none is
literally the fielded file; S3's wording agrees with its pre-registration (the eleven time
bins and both answer labels, word-for-word) and with the supplement's description.

WHAT IS BUILT.
- s3: Study S3 (AsPredicted #150577, Supplement 6), 2 x 2 between people: a navigation app
  (driving to a local shopping mall) or a food delivery app (ordering dinner), whose estimate
  was a point ("43 minutes") or a range ("33-53 minutes"). On one page everyone then said, for
  each of eleven time bins from "< 21 min" to "> 65 min", whether it was consistent with the
  estimate. Each bin is one outcome. Kind "mix". (The rest of this docstring's S3 sections
  follow the sequence studies' below.)
- studyN_satisfaction and studyN_accuracy (Studies 1, 2, 3, 6, 7, 8) and study5_satisfaction
  and study5_lateness: THE SEQUENCE STUDIES, below.

THE SEQUENCE STUDIES (rich, 20 Nov 2026). Studies 1, 2, 3, 5, 6, 7 and 8 share one paradigm:
instructions; twenty pages, one per past order (Study 8: trip), each showing the app's
estimate and how long that order actually took, the twenty times drawn at random per person;
two attention checks; then two question blocks. Between people the estimate varies (SEQ_STUDIES
holds each study's arms, asserted against the ConditionName the flow's randomiser sets):
Study 1 45 / 40-50 / 35-55 minutes; Study 2 45 / 35-55 / 15-75; Study 3 a point (36 to 55, the
mean of each order's distribution) or the 20-minute range around it, a different estimate
per order; Study 5 45 / 35-55; Study 6 35 / 45 / 55 / 35-55; Study 7 a point or a range,
accurate (45, 35-55) or conservative (55, 45-65), two factors; Study 8 a short (~45 minutes)
or long (~2 hours 15) drive x an accurate point, a conservative point or a range. Kind
"version" for one factor, "mix" for Studies 7 and 8.

  The pages. The deposit records WHICH twenty times a person saw (the "outcomes" column,
  listed in loop & merge order; Study 3's draw36-draw55) but not the order the pages came in:
  each codebook says so ("the order represents the order in which the numbers were listed in
  the loop & merge function, rather than the actual order presented to participant"), the
  loop is a random subset and no display-order column exists (check_sequences). rich's ruling
  of 20 Nov 2026 (CONVENTIONS, beside the 16 Nov choice-set ruling) extends the choice-set
  clause to these feedback sequences: each row lists the twenty pages word-for-word in the
  data file's order, as lines starting "- ", after this clause of ours:
      "(shown one per page, in a random order; the order was not recorded)"
  and carries the twenty times as metadata (factors time_01-time_20, not declared factors:
  each person's draw is their own, so they have no minimal pair for QC rule 5; the tests
  check every row's times against the deposit and against its own text). Each listing is
  asserted to be a subsequence of the loop's fifty values in loop order (subsequence), so the
  data file's order is the loop's. Each page keeps its words except its position ("Order
  ${lm://CurrentLoopNumber}:", Study 3 "Order ${e://Field/trialOrder}:"; a row cannot cite
  its own position) and its click instruction ("Please click >> to view the next order.").
  Study 8's loop holds the times as words ("48 minutes", "2 hours and 12 minutes"), rendered
  as the loop has them and matched to the deposit's minutes. Study 3's JavaScript on each page
  only records the draw (setEmbeddedData; asserted it never touches the page).

  The rest of the condition. The instructions screens open each row word-for-word (estimate
  piped in), including their mechanics (">> button will appear after 2 seconds": a fixed
  two-second button delay, the same for everyone; it is not the manipulation). The attention
  checks after the pages ("How many orders ... did you see?", "What was the estimated delivery
  time ...?") are not narrated (CONVENTIONS, attention checks; 348 precedent). Then the intro
  of whichever question block came first ("You will now be asked to evaluate the food
  delivery app. Please answer the questions below.", display logic on dv_subfirst).

  The question blocks. Satisfaction: five 1-7 questions on one page in a random order not
  recorded (end labels from the .qsf, the number stripped). Accuracy: three drop-downs on one
  page, fixed order: the percentage of estimates very ACCURATE and very INACCURATE (0%-100% in
  tens; the deposit holds the percentage, coded 0-10 here, per outcome), and how many minutes
  the app is off (0 minute ... 20 minutes, the deposit's minutes). Study 5 has instead one
  lateness question (1 "Almost never", 4 "Sometimes", 7 "Almost Always"). The two blocks came
  in a random order, recorded (dv_subfirst; declared factor dv_order); Study 3 always asked
  satisfaction first. One recipe per block, so each row's condition is what preceded its own
  page: rows from the block shown second narrate the first block's questions as asked, with
  the words of ours "You were asked:" (fixed order) or "You were asked (the questions were
  shown in a random order):" (the satisfaction page), each question quoted.

  Exclusions. Each do file's: duplicate IP addresses, then duplicate ids (Study 8 recorded no
  ids, as its do file explains). N 698, 599, 479, 468, 801, 998, 888: the Ns the do files and
  Supplement 1 state. The attention checks are a robustness exclusion only (Supplement 3), not
  applied, as in the paper.

  Answer key. Each do file's main models (2.2): the satisfaction index (rowmean of the five)
  on its arm dummies or contrasts (Study 3 and 5 the range contrast; Study 7 point, accurate
  and their product, +-0.5; Study 8 Length and the estimate dummies), and the same model for
  each accuracy item and for lateness. Fitted on the deposit and on the BUILT rows (the
  percentages multiplied back by ten), every coefficient agrees to 1e-9, and moving one arm's
  rows to another breaks it (tests/test_gen_researchbox482.py).

  UK fit. Food delivery apps and a navigation app on a drive, in minutes: Yes.

NOT BUILT (NOT_BUILT), each with its reason. Study S1 shows the app's estimate on every page
as a picture, one per arm. Study 4's instructions point to a picture ("like the ones shown
below") and its time-limit questions pipe the person's own model choice back; its slider task
also runs against a real countdown timer. Study S2's response is a 20-ball distribution built
in a JavaScript tool, not one value.

UK FIT (S3). Ordering dinner from a delivery app, or driving to a local shopping mall with a
navigation app, estimated in minutes: everything the question turns on is on the row.
"Shopping mall" is a US word with a plain UK reading. Yes.

PICTURES (rich, 19 Nov 2026). S3's .qsf has no <img> and no graphic id (asserted), so no
screen an S3 respondent could reach shows a picture; PICTURES pins every .qsf's count.

THE WORDING. From Study S3.qsf, the blocks the survey flow reaches, word-for-word. The arm is
three screens, each chosen by display logic on the embedded field appName (gps or food) with
the estimate piped in (${e://Field/estimate}, the value the flow's randomiser set): the
instructions page ("Instructions:" and two paragraphs), the scenario page (one paragraph),
and the response page, which repeats the scenario in grey (asserted identical to the scenario
page, so it is written once) and then gives the task's own instructions (three paragraphs).
Not narrated: consent and the location attention check that ends the survey for anyone who
fails it (asked before assignment, identical for everyone). Typography normalised (HTML,
non-breaking spaces, curly quotes); bold, underline and grey dropped. A quotation mark in the
task instructions closes after the full stop ('of "43 minutes."'), and the matrix question has
its question mark inside the quotes ('"43 minutes?"'); both are the source's and are kept.

THE OUTCOMES. One Likert matrix (QID113, export tag binary), ForceResponse, eleven statements
in a fixed order (no randomisation), two answers: 1 "Yes, consistent", 2 "No, inconsistent"
(no RecodeValues, AnswerOrder 1, 2; the codebook agrees). Columns binary_1..binary_11 are the
statements in ChoiceOrder (choice ids 1-11 in order), as the codebook (var10-var20) and the
pre-registration list them; the share answering "Yes" peaks at "41-45 min", the bin holding
43 (asserted), which a shifted mapping could not do. Each outcome's question is the matrix's
stem, with the arm's estimate piped in, followed by its statement, so the question is set per
arm (Arm.items) for every outcome. Scale 1-2, labels from the answers.

EXCLUSIONS. The do file's, in order: duplicate IP addresses (ExcludeDuplicateIP), then
duplicate Prolific ids (ExcludeDuplicateID); 198 to 188, the N the do file and the supplement
state. Everyone in the deposit passed the opening check (pass_screen = 1). One kept person has
a blank consent cell; the authors keep them (they finished, and the check that follows consent
was answered), and so do we.

PERSONA. Age (a text box; 19-80 in the kept sample, an age outside 18-100 would be left blank)
and gender (the .qsf's labels Female, Male, Other, with Other's RecodeValue 3 as the codebook
says). The free text typed beside "Other" is never read.

JEV. scripts/recipe_prep.py reads .sav/.dta/.por only; this box is .xlsx, and running it (19
Nov 2026, --source dataverse) exits "no .sav/.dta under data/raw/researchbox482/", so it does
not apply. The assignment is the two embedded fields the flow's randomisers set (app,
Condition), exported as columns, asserted against their labels (appName, estimate).

ANSWER KEY. The do file's pre-registered DV is the number of bins answered "Yes, consistent";
its model is OLS of that count on the app (fixed effect) and the range contrast (+-0.5).
Recomputed from the deposit with the authors' exclusions and from the BUILT rows, the two
agree to 1e-9 (tests/test_gen_researchbox482.py) and give point M = 3.39 (SD 1.58, n = 92),
range M = 5.11 (SD 1.53, n = 96), b = 1.88 (SE 0.22): Supplement 6 reports exactly these.

    uv run python scripts/gen_researchbox482.py --prep   # code the data
    uv run python scripts/gen_researchbox482.py          # write the recipe
    uv run python scripts/gen_researchbox482.py --check  # exit 1 if the recipe differs
"""

from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
STUDY_ID = "researchbox482"
RAW = REPO / "data" / "raw" / STUDY_ID
BOX = RAW / "ResearchBox 482"
MATERIALS = BOX / " Materials"  # the Zenodo zip's folder names start with a space
DATA = BOX / " Data"
CODEBOOK = BOX / " Codebook"
RECIPES = REPO / "recipes"
LICENCE = (
    'CC BY 4.0, stated on the box page https://researchbox.org/482 ("All content posted '
    'to ResearchBox is under a CC By 4.0 License"); read from its Zenodo copy, record '
    "15033033 (https://zenodo.org/records/15033033). Read 19 Nov 2026."
)
PAPER = (
    'Hu B, Gaertig C, Dietvorst BJ, "How Should Time Estimates be Structured to Increase '
    "Customer Satisfaction?\" (manuscript title from the box's ReadMe). ResearchBox 482 "
    "(https://researchbox.org/482)."
)

QSF = "Study S3.qsf"
DATA_FILE = "Study S3.xlsx"

# <img> tags and graphic ids in each .qsf (S3 has none).
PICTURES: dict[str, tuple[int, set[str]]] = {
    "Study 1.qsf": (0, set()),
    "Study 2.qsf": (0, set()),
    "Study 3.qsf": (0, set()),
    "Study 4.qsf": (1, {"IM_bp9CGOYFmFW3tXg"}),
    "Study 5.qsf": (0, set()),
    "Study 6.qsf": (0, set()),
    "Study 7.qsf": (0, set()),
    "Study 8.qsf": (0, set()),
    "Study S1.qsf": (3, {"IM_4GDWg5juxdW4098", "IM_b8fKvbEABNIgrLE", "IM_e9Uhc0g4Wt4c5am"}),
    "Study S2.qsf": (
        5,
        {"IM_08wU44BZK8C5yHI", "IM_0qbF1x7ICLYMX2e", "IM_a9speyUrfJs9bBs", "IM_bjXEWHN7pgH4F5I"},
    ),
    "Study S3.qsf": (0, set()),
}

NOT_BUILT = {
    "study4": "Study 4 (choose Model Alpha or Beta, one giving a point and one a range): the "
    "instructions every row would open with show a picture (IM_bp9CGOYFmFW3tXg) that the text "
    "points to ('like the ones shown below'), and the time-limit questions pipe the person's "
    "own model choice back ('${q://QID93/ChoiceGroup/SelectedChoices}'s estimate'); the later "
    "slider task also runs against a real countdown timer.",
    "s1": "Study S1 (point, range, or both): on every one of the twenty order pages the app's "
    "estimate is a picture (IM_4GDWg5juxdW4098, IM_b8fKvbEABNIgrLE, IM_e9Uhc0g4Wt4c5am, one per "
    "arm), so the manipulation lives only in pictures.",
    "s2": "Study S2 (food or navigation app x point or range): the response is a distribution "
    "of 20 balls over nine time bins, built in a JavaScript tool shown with pictures "
    "(DistributionResult1), not a single value. Also, the food-app elicitation screen (QID105) "
    "hard-codes '33-53 minutes' for both estimate arms.",
}

# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

_TYPO = {"\xa0": " ", "\u200b": "", "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"'}


def plain(raw: str) -> str:
    """An HTML fragment to one line of plain text. Typography only; tags vanish."""
    s = re.sub(r"<[^>]+>", "", raw or "")
    s = html.unescape(s)
    for a, b in _TYPO.items():
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def paragraphs(raw: str) -> str:
    """HTML to paragraphs (blank-line separated), each one line of plain text."""
    s = re.sub(r"(?i)</?br\s*/?>|</p>|</div>|<p[^>]*>|<div[^>]*>", "\n\n", raw or "")
    parts = [plain(p) for p in s.split("\n\n")]
    return "\n\n".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# The questionnaires
# ---------------------------------------------------------------------------


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
        self.blocks = blocks
        self.flow = next(e for e in els if e["Element"] == "FL")["Payload"]
        self.flow_blocks: list[dict[str, Any]] = []
        self.randomisers: list[dict[str, Any]] = []

        def walk(n: dict[str, Any]) -> None:
            if n.get("Type") in ("Block", "Standard", "Default"):
                self.flow_blocks.append(blocks[n["ID"]])
            if n.get("Type") == "BlockRandomizer":
                self.randomisers.append(n)
            for c in n.get("Flow", []):
                walk(c)

        walk(self.flow)

    def block(self, description: str) -> dict[str, Any]:
        (b,) = [b for b in self.flow_blocks if b["Description"] == description]
        return b

    def qids(self, description: str) -> list[str]:
        return [
            x["QuestionID"]
            for x in self.block(description)["BlockElements"]
            if x["Type"] == "Question"
        ]

    def loops(self) -> list[dict[str, Any]]:
        return [
            b["Options"]["LoopingOptions"]
            for b in self.blocks.values()
            if b.get("Options", {}).get("Looping") not in (None, "None")
        ]


def graphics_in(raw: str) -> tuple[int, set[str]]:
    """(<img> tags, graphic ids) in a .qsf's text."""
    return raw.count("<img"), set(re.findall(r"\bIM_[A-Za-z0-9]+\b", raw))


def check_pictures() -> None:
    assert sorted(p.name for p in MATERIALS.glob("*.qsf")) == sorted(PICTURES)
    for f, want in PICTURES.items():
        assert graphics_in((MATERIALS / f).read_text()) == want, f


# Studies whose outcomes all follow a sequence of pages whose order is not recorded.
SEQUENCE_STUDIES = ["1", "2", "3", "4", "5", "6", "7", "8", "S1"]
UNRECORDED = "rather than the actual order presented to participant"


def read_xlsx(study: str) -> pd.DataFrame:
    return pd.read_excel(DATA / f"Study {study}.xlsx")


def check_sequences() -> None:
    """Every sequence study randomises its pages and records no order (see the docstring)."""
    for s in SEQUENCE_STUDIES:
        sv = Survey(f"Study {s}.qsf")
        loops = sv.loops()
        assert loops and all(lo["Randomization"] == "Subset" for lo in loops), s
        cols = list(read_xlsx(s).columns)
        assert not [c for c in cols if c.endswith("_DO") or "order" in c.lower()], s
        book = pd.read_csv(CODEBOOK / f"Study {s}.xlsx___CODEBOOK.csv")
        assert list(book["varname"]) == cols, s
        if s == "3":  # one loop per trial, the twenty trial blocks shuffled by a randomiser
            assert len(loops) == 20 and all(lo["TotalRandSubset"] == "1" for lo in loops)
            (r,) = [r for r in sv.randomisers if len(r["Flow"]) == 20]
            assert r["SubSet"] in (20, "20"), r["SubSet"]
            assert [f"draw{k}" for k in range(36, 56)] == [c for c in cols if c.startswith("draw")]
        else:
            desc = str(book.set_index("varname").loc["outcomes", "description"])
            assert UNRECORDED in desc.replace("participants", "participant"), (s, desc)
    # the pages print their own position
    trial = Survey("Study 1.qsf").by_id["QID2"]["QuestionText"]
    assert plain(trial).startswith("Order ${lm://CurrentLoopNumber}:"), trial


# ---------------------------------------------------------------------------
# The sequence studies (1, 2, 3, 5, 6, 7, 8)
# ---------------------------------------------------------------------------

UNORDERED = "(shown one per page, in a random order; the order was not recorded)"  # rich, ours
ASKED = "You were asked:"  # ours
ASKED_RANDOM = "You were asked (the questions were shown in a random order):"  # ours
_POSITION = re.compile(
    r"^(?:Order|Trip) \$\{(?:lm://CurrentLoopNumber|e://Field/trialOrder)\}: (.+)$"
)
_NEXT = re.compile(r"^(.+?) Please click >> to view the next (?:order|trip)\.$")
SB = ["sb_like", "sb_info", "sb_useful", "sb_accurate", "sb_trust"]
OB = ["ob_accurate", "ob_inaccurate", "ob_error"]
BLOCK_ITEMS = {"satisfaction": SB, "accuracy": OB, "lateness": ["late"]}
BLOCK_NAME = {
    "satisfaction": "DV (subjective)",
    "accuracy": "DV (objective)",
    "lateness": "Mediator",
}


@dataclass
class SeqStudy:
    key: str  # the deposit's study number
    kind: str
    factors: list[str]
    # (Length, Condition) -> (the deposit's ConditionName, factor levels); Length 0 if none
    cells: dict[tuple[int, int], tuple[str, dict[str, str]]]
    other: str  # the block besides satisfaction: accuracy or lateness
    counterbalanced: bool  # dv_subfirst randomised (Study 3: satisfaction first, fixed)
    n: int  # the do file's N after its exclusions
    title: str

    @property
    def name(self) -> str:
        return f"study{self.key}"

    @property
    def blocks(self) -> list[str]:
        return ["satisfaction", self.other]


def _one(levels: dict[int, tuple[str, str]], factor: str = "estimate") -> dict[Any, Any]:
    return {(0, c): (n, {factor: lv}) for c, (n, lv) in levels.items()}


SEQ_STUDIES = [
    SeqStudy(
        "1",
        "version",
        ["estimate"],
        _one(
            {
                1: ("Point estimate", "point_45"),
                2: ("Range 10", "range_40_50"),
                3: ("Range 20", "range_35_55"),
            }
        ),
        "accuracy",
        True,
        698,
        "Twenty past food deliveries, all estimated at 45 minutes, 40-50 minutes or 35-55 "
        "minutes, each with how long it actually took: how satisfied with the app, and how "
        "accurate is it? (Study 1)",
    ),
    SeqStudy(
        "2",
        "version",
        ["estimate"],
        _one(
            {
                1: ("Point estimate", "point_45"),
                2: ("Normal range", "range_35_55"),
                3: ("Extreme range", "range_15_75"),
            }
        ),
        "accuracy",
        True,
        599,
        "Twenty past food deliveries, all estimated at 45 minutes, 35-55 minutes or 15-75 "
        "minutes, each with how long it actually took: how satisfied with the app, and how "
        "accurate is it? (Study 2)",
    ),
    SeqStudy(
        "3",
        "version",
        ["estimate"],
        _one({1: ("Point estimate", "point"), 2: ("Range 20", "range")}),
        "accuracy",
        False,
        479,
        "Twenty past food deliveries, each estimated as a point (36 to 55 minutes) or a "
        "20-minute range around it, each with how long it actually took: how satisfied with "
        "the app, and how accurate is it? (Study 3)",
    ),
    SeqStudy(
        "5",
        "version",
        ["estimate"],
        _one({1: ("Point estimate", "point_45"), 2: ("Range estimate", "range_35_55")}),
        "lateness",
        True,
        468,
        "Twenty past food deliveries, all estimated at 45 minutes or 35-55 minutes, each with "
        "how long it actually took: how satisfied with the app, and how often is it "
        "unexpectedly late? (Study 5)",
    ),
    SeqStudy(
        "6",
        "version",
        ["estimate"],
        _one(
            {
                1: ("Optimistic point estimate", "point_35"),
                2: ("Accurate point estimate", "point_45"),
                3: ("Conservative point estimate", "point_55"),
                4: ("Range", "range_35_55"),
            }
        ),
        "accuracy",
        True,
        801,
        "Twenty past food deliveries, all estimated at 35, 45 or 55 minutes or 35-55 minutes, "
        "each with how long it actually took: how satisfied with the app, and how accurate is "
        "it? (Study 6)",
    ),
    SeqStudy(
        "7",
        "mix",
        ["format", "location"],
        {
            (0, 1): ("Accurate point estimate", {"format": "point", "location": "accurate"}),
            (0, 2): (
                "Conservative point estimate",
                {"format": "point", "location": "conservative"},
            ),
            (0, 3): ("Accurate range", {"format": "range", "location": "accurate"}),
            (0, 4): ("Conservative range", {"format": "range", "location": "conservative"}),
        },
        "accuracy",
        True,
        998,
        "Twenty past food deliveries, all estimated at 45 or 55 minutes or 35-55 or 45-65 "
        "minutes, each with how long it actually took: how satisfied with the app, and how "
        "accurate is it? (Study 7)",
    ),
    SeqStudy(
        "8",
        "mix",
        ["length", "estimate"],
        {
            (ln, c): (name, {"length": lname, "estimate": lv})
            for ln, lname in ((1, "short"), (2, "long"))
            for c, (name, lv) in {
                1: ("Accurate point estimate", "accurate_point"),
                2: ("Conservative point estimate", "conservative_point"),
                3: ("Range", "range"),
            }.items()
        },
        "accuracy",
        True,
        888,
        "Twenty past drives, short (about 45 minutes) or long (about 2 hours 15 minutes), all "
        "with the same accurate point, conservative point or range estimate, each with how "
        "long it actually took: how satisfied with the navigation app, and how accurate is "
        "it? (Study 8)",
    ),
]
SEQ = {s.key: s for s in SEQ_STUDIES}


def flat(raw: str) -> str:
    """HTML to one line: line breaks become spaces, then plain."""
    return plain(re.sub(r"(?i)</?br\s*/?>|</p>|</div>", " ", raw or ""))


def in_flow_blocks(sv: Survey, description: str) -> dict[str, Any]:
    """The block with this description; a block may be reached by several branches."""
    found = {b["ID"]: b for b in sv.flow_blocks if b["Description"] == description}
    (b,) = found.values()
    return b


def block_questions(sv: Survey, b: dict[str, Any]) -> list[dict[str, Any]]:
    """A block's questions in block order, page timers dropped."""
    qs = [sv.by_id[x["QuestionID"]] for x in b["BlockElements"] if x["Type"] == "Question"]
    return [q for q in qs if q["QuestionType"] != "Timing"]


def seq_assignments(sv: Survey) -> dict[tuple[int, int], dict[str, str]]:
    """(Length, Condition) -> the embedded fields its randomiser sets (Length 0 if none)."""
    out: dict[tuple[int, int], dict[str, str]] = {}

    def walk(n: dict[str, Any], length: int) -> None:
        if n.get("Type") == "Branch":
            logic = n["BranchLogic"]["0"]["0"]
            if logic.get("LeftOperand") == "Length":
                assert logic["Operator"] == "EqualTo"
                length = int(logic["RightOperand"])
        if n.get("Type") == "BlockRandomizer":
            for c in n["Flow"]:
                if c.get("Type") != "EmbeddedData":
                    continue
                f = {e["Field"]: e["Value"] for e in c["EmbeddedData"]}
                if "Condition" in f:
                    assert n["SubSet"] in (1, "1") and n.get("EvenPresentation"), n
                    key = (length, int(f["Condition"]))
                    assert key not in out, key
                    out[key] = f
        for c in n.get("Flow", []):
            walk(c, length)

    walk(sv.flow, 0)
    return out


@dataclass
class Loop:
    values: list[str]  # the static loop's field 1, in loop & merge order
    page: str  # the page, plain, position and click instruction dropped, pipes left in


def loops_of(sv: Survey) -> dict[str, Loop]:
    """Loop block description -> its values and its page wording."""
    out: dict[str, Loop] = {}
    for b in {b["ID"]: b for b in sv.flow_blocks}.values():
        opts = b.get("Options", {})
        if opts.get("Looping") in (None, "None"):
            continue
        lo = opts["LoopingOptions"]
        assert opts["Looping"] == "Static" and lo["Randomization"] == "Subset", b["Description"]
        static = lo["Static"]
        values = [static[k]["1"] for k in sorted(static, key=int)]
        qs = block_questions(sv, b)
        assert len(qs) == 2 and all(q["QuestionType"] == "DB" for q in qs), b["Description"]
        assert not any(q.get("DisplayLogic") for q in qs)
        assert [x["Type"] for x in b["BlockElements"]].count("Page Break") == 0
        first = _POSITION.match(flat(qs[0]["QuestionText"]))
        second = _NEXT.match(flat(qs[1]["QuestionText"]))
        assert first and second, (flat(qs[0]["QuestionText"]), flat(qs[1]["QuestionText"]))
        for q in qs:  # Study 3's JavaScript only records the draw; it never touches the page
            js = q.get("QuestionJS") or ""
            assert not re.search(r"innerHTML|jQuery|\$\(|getQuestion|style", js), js
            body = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
            calls = set(re.findall(r"Qualtrics\.SurveyEngine\.(\w+)", body))
            assert calls <= {"addOnload", "addOnReady", "addOnUnload", "setEmbeddedData"}, calls
        out[b["Description"]] = Loop(values, f"{first.group(1)} {second.group(1)}")
    return out


def minutes(value: str) -> int:
    """A loop value ('59', '48 minutes', '2 hours and 12 minutes') in minutes."""
    m = re.fullmatch(r"(?:(\d+) hours? and )?(\d+)(?: minutes)?", value)
    assert m, value
    return int(m.group(1) or 0) * 60 + int(m.group(2))


def subsequence(drawn: list[int], values: list[str]) -> list[str]:
    """The loop values the person saw, matched in loop order; fails if `drawn` is not one."""
    out, i = [], 0
    for want in drawn:
        while i < len(values) and minutes(values[i]) != want:
            i += 1
        assert i < len(values), (drawn, want)
        out.append(values[i])
        i += 1
    return out


def scale_of(q: dict[str, Any]) -> tuple[list[str], list[int]]:
    """(choice labels in order, recode values) of a single-answer question."""
    order = [str(k) for k in q.get("ChoiceOrder") or sorted(q["Choices"], key=int)]
    labels = [flat(q["Choices"][k]["Display"]) for k in order]
    rec = q.get("RecodeValues") or {}
    codes = [int(rec.get(k, k)) for k in order]
    return labels, codes


@dataclass
class SeqOutcome:
    var: str
    question: str
    scale: dict[str, Any]
    recode: dict[int, int]


def seq_outcome(q: dict[str, Any]) -> SeqOutcome:
    """One item's question and scale, from the .qsf, with the deposit's codes."""
    assert q["QuestionType"] == "MC" and not q.get("DisplayLogic"), q["QuestionID"]
    var, text = q["DataExportTag"], plain(q["QuestionText"])
    labels, codes = scale_of(q)
    if var.startswith("sb_") or var == "late":
        assert codes == list(range(1, 8)), (var, codes)
        lo, hi = (re.fullmatch(r"(.+) ([17])", labels[i]) for i in (0, 6))
        assert lo and hi and [lo.group(2), hi.group(2)] == ["1", "7"], labels
        mids = labels[1:6]
        sc: dict[str, Any] = {"min": 1, "max": 7, "min_label": lo.group(1)}
        sc["max_label"] = hi.group(1)
        if var == "late":
            assert mids[2] == "Sometimes 4" and mids[:2] + mids[3:] == ["2", "3", "5", "6"]
            sc["mid_label"] = "Sometimes"
        else:
            assert mids == ["2", "3", "4", "5", "6"], mids
        return SeqOutcome(var, text, sc, {k: k for k in range(1, 8)})
    if var in ("ob_accurate", "ob_inaccurate"):
        assert labels == [f"{10 * i}%" for i in range(11)], labels
        # the deposit holds the percentage (0, 10, ..., 100); coded 0-10 here
        return SeqOutcome(
            var,
            text,
            {"min": 0, "max": 10, "min_label": "0%", "max_label": "100%"},
            {10 * i: i for i in range(11)},
        )
    assert var == "ob_error", var
    assert labels[0] == "0 minute" and labels[-1] == "20 minutes" and len(labels) == 21
    return SeqOutcome(
        var,
        text,
        {"min": 0, "max": 20, "min_label": labels[0], "max_label": labels[-1]},
        {k: k for k in range(21)},
    )


@dataclass
class DVBlock:
    intro: str | None  # the intro on the block's page when it came first
    first_when: str | None  # the dv_subfirst value its intro is shown for
    items: list[SeqOutcome]
    randomised: bool


def dv_block(sv: Survey, block: str) -> DVBlock:
    b = in_flow_blocks(sv, BLOCK_NAME[block])
    assert "Page Break" not in [x["Type"] for x in b["BlockElements"]]  # one page
    qs = block_questions(sv, b)
    intro, when = None, None
    if qs[0]["QuestionType"] == "DB":
        q0 = qs.pop(0)
        intro = paragraphs(q0["QuestionText"])
        dl = q0.get("DisplayLogic")
        if dl:
            cond = dl["0"]["0"]
            assert (cond["LeftOperand"], cond["Operator"]) == ("dv_subfirst", "EqualTo"), cond
            when = str(cond["RightOperand"])
    items = [seq_outcome(q) for q in qs]
    assert [i.var for i in items] == BLOCK_ITEMS[block], [i.var for i in items]
    rnd = b["Options"].get("RandomizeQuestions") == "Advanced"
    if rnd:
        adv = b["Options"]["Randomization"]["Advanced"]
        assert sorted(adv["RandomizeAll"]) == sorted(q["QuestionID"] for q in qs)
    else:
        assert b["Options"].get("RandomizeQuestions") in (None, "false"), b["Options"]
    return DVBlock(intro, when, items, rnd)


@dataclass
class SeqDesign:
    study: SeqStudy
    sv: Survey
    assign: dict[tuple[int, int], dict[str, str]]
    loops: dict[str, Loop]
    instructions: dict[tuple[int, int], str]  # per cell, estimate piped in
    dvs: dict[str, DVBlock]


def seq_design(st: SeqStudy) -> SeqDesign:
    sv = Survey(f"Study {st.key}.qsf")
    assign = seq_assignments(sv)
    assert set(assign) == set(st.cells), (st.key, sorted(assign))
    for k, (name, _) in st.cells.items():
        assert assign[k]["ConditionName"] == name, (k, assign[k])
    ins = block_questions(sv, in_flow_blocks(sv, "Instructions"))
    assert all(q["QuestionType"] == "DB" and not q.get("DisplayLogic") for q in ins)
    instructions = {}
    for k, f in assign.items():
        text = "\n\n".join(paragraphs(q["QuestionText"]) for q in ins)
        if st.key != "3":
            assert text.count("${e://Field/PredictionText}") == 1, text
            text = text.replace("${e://Field/PredictionText}", f["PredictionText"])
        assert "${" not in text, text
        instructions[k] = text
    dvs = {b: dv_block(sv, b) for b in st.blocks}
    if st.counterbalanced:
        assert {d.first_when for d in dvs.values()} == {"1", "0"}
        assert dvs["satisfaction"].first_when == "1"
    else:  # Study 3: satisfaction, then accuracy, fixed
        assert dvs["satisfaction"].first_when is None and dvs[st.other].intro is None
    return SeqDesign(st, sv, assign, loops_of(sv), instructions, dvs)


def pages_of(d: SeqDesign, row: pd.Series) -> tuple[list[str], list[int]]:
    """(the pages this person saw, in the data file's order; their times in minutes)."""
    st, key = d.study, (int(row.get("Length", 0) or 0), int(row["Condition"]))
    if st.key == "3":
        pages, times = [], []
        for k in range(36, 56):
            loop = d.loops[f"Trial - {k} min"]
            t = int(row[f"draw{k}"])
            assert str(t) in loop.values, (k, t)
            est = d.assign[key][f"PredictionText{k}"]
            assert est == row[f"PredictionText{k}"], (k, est)
            page = loop.page.replace(f"${{e://Field/PredictionText{k}}}", est)
            pages.append(page.replace("${lm://Field/1}", str(t)))
            times.append(t)
        return pages, times
    if st.key == "8":
        loop = d.loops[{1: "short - 20 trials", 2: "long - 20 trials"}[key[0]]]
    else:
        (loop,) = d.loops.values()
    drawn = [int(x) for x in str(row["outcomes"]).split(",")]
    assert len(drawn) == 20, drawn
    shown = subsequence(drawn, loop.values)
    est = d.assign[key]["PredictionText"]
    assert est == row["PredictionText"], (est, row["PredictionText"])
    page = loop.page.replace("${e://Field/PredictionText}", est)
    return [page.replace("${lm://Field/1}", v) for v in shown], drawn


def narrate(block: DVBlock) -> str:
    head = ASKED_RANDOM if block.randomised else ASKED
    return "\n".join([head] + [f'"{i.question}"' for i in block.items])


def seq_text(
    d: SeqDesign, key: tuple[int, int], pages: list[str], block: str, sub_first: bool
) -> str:
    """One row's condition: instructions, the pages, the first DV page, any earlier block."""
    st = d.study
    first = "satisfaction" if sub_first else st.other
    intro = d.dvs[first].intro
    assert intro, (st.key, first)
    parts = [d.instructions[key], UNORDERED + "\n" + "\n".join(f"- {p}" for p in pages), intro]
    if block != first:
        parts.append(narrate(d.dvs[first]))
    return "\n\n".join(parts)


def seq_kept(st: SeqStudy) -> pd.DataFrame:
    """The do file's sample: duplicate IPs, then duplicate ids (Study 8 has none recorded)."""
    df = read_xlsx(st.key)
    assert df["Id"].is_unique
    df = df[df["ExcludeDuplicateIP"] != 1]
    if "ExcludeDuplicateID" in df:
        df = df[df["ExcludeDuplicateID"] != 1]
    else:
        assert st.key == "8"
    return df.reset_index(drop=True)


def seq_gender(sv: Survey) -> dict[int, str]:
    (q,) = [q for q in sv.by_id.values() if q["DataExportTag"] == "gender"]
    rec = q["RecodeValues"]
    labels = {int(rec[k]): plain(v["Display"]) for k, v in q["Choices"].items()}
    assert labels == {1: "Female", 2: "Male", 3: "Other"}, labels
    return labels


@dataclass
class SeqCell:
    code: int
    key: tuple[int, int]
    sub_first: bool
    pages: list[str]
    times: list[int]


def sub_first_of(st: SeqStudy, row: pd.Series) -> bool:
    return bool(int(row["dv_subfirst"])) if st.counterbalanced else True


def seq_cells(d: SeqDesign, df: pd.DataFrame) -> tuple[list[SeqCell], list[int]]:
    """The distinct (assignment, block order, pages) cells, and each person's cell code."""
    st = d.study
    keyed = []
    for _, row in df.iterrows():
        key = (int(row.get("Length", 0) or 0), int(row["Condition"]))
        pages, times = pages_of(d, row)
        keyed.append((key, sub_first_of(st, row), tuple(pages), tuple(times)))
    distinct = sorted(set(keyed))
    code = {k: i + 1 for i, k in enumerate(distinct)}
    cells = [SeqCell(code[k], k[0], k[1], list(k[2]), list(k[3])) for k in distinct]
    return cells, [code[k] for k in keyed]


def seq_data_file(st: SeqStudy) -> str:
    return f"{STUDY_ID}_{st.name}.csv"


def seq_prep(st: SeqStudy) -> pd.DataFrame:
    d = seq_design(st)
    df = seq_kept(st)
    assert len(df) == st.n, (st.key, len(df))
    _, codes = seq_cells(d, df)
    out = pd.DataFrame({"pid": [f"{st.name}_{i}" for i in df["Id"]], "cell": codes})
    for b in st.blocks:
        for it in d.dvs[b].items:
            v = df[it.var]
            assert v.notna().all() and v.isin(list(it.recode)).all(), (st.key, it.var)
            out[it.var] = v.astype(int).values
    age = pd.to_numeric(df["age"], errors="coerce")
    out["age"] = age.where(age.between(*AGE_RANGE)).astype("Int64").values
    labels = seq_gender(d.sv)
    assert set(df["gender"].dropna().astype(int)) <= set(labels)
    out["gender"] = df["gender"].map(lambda g: labels[int(g)] if pd.notna(g) else None).values
    assert out["pid"].is_unique
    return out


def seq_recipe(st: SeqStudy, block: str) -> dict[str, Any]:
    d = seq_design(st)
    df = seq_kept(st)
    cells, _ = seq_cells(d, df)
    order_factor = st.counterbalanced
    factors = [*st.factors, *(["dv_order"] if order_factor else [])]
    arms = []
    for i, c in enumerate(cells):
        f = dict(st.cells[c.key][1])
        if order_factor:
            f["dv_order"] = f"{'satisfaction' if c.sub_first else st.other}_first"
        for j, t in enumerate(c.times, 1):  # structured metadata, not declared factors
            f[f"time_{j:02d}"] = str(t)
        arms.append(
            {
                "raw": c.code,
                "condition_num": i,
                "factors": f,
                "text": seq_text(d, c.key, c.pages, block, c.sub_first),
            }
        )
    items = d.dvs[block].items
    outcomes = [
        {
            "var": it.var,
            "task_num": t,
            "question": it.question,
            "scale": it.scale,
            **({"response_recode": it.recode} if block == "accuracy" else {}),
        }
        for t, it in enumerate(items)
    ]
    # The study-level recode is the last item's (every accuracy item also carries its own;
    # merged, the percentages' 30 -> 3 would collide with ob_error's 3 -> 3).
    recode = items[-1].recode
    other = d.dvs["satisfaction" if block != "satisfaction" else st.other]
    notes = (
        f"{PAPER}\n\nGENERATED by scripts/gen_researchbox482.py; every judgement is in its "
        f"docstring. Study {st.key}, {st.n:,} people kept by the do file's exclusions (duplicate "
        "IP addresses, then duplicate ids). Between people: "
        + "; ".join(
            f"{n} ({', '.join(f'{k}={v}' for k, v in lv.items())})" for n, lv in st.cells.values()
        )
        + ". Everyone then saw twenty pages, one per past "
        + ("trip" if st.key == "8" else "order")
        + ", each the app's estimate and how long it actually took, drawn at random per "
        "person; the order of the pages was randomised and not recorded, so each row lists them "
        "in the data file's order (loop & merge order"
        + ("; Study 3's draw36-draw55" if st.key == "3" else "")
        + f") after this clause of ours: '{UNORDERED}' (rich, 20 Nov 2026). Each page is "
        "written word-for-word as a line starting '- ', without its position ('Order N:') or its "
        "click instruction. The twenty times are also carried as factors time_01-time_20 "
        "(metadata, not declared factors). The instructions screens open each row, "
        "word-for-word; the attention checks after the pages are not narrated. "
        + (
            "The two question blocks came in a random order, recorded (dv_subfirst, the "
            "factor dv_order); "
            if st.counterbalanced
            else "The satisfaction block always came first; "
        )
        + "rows from the block shown second narrate the first block's questions as asked, after "
        f"its intro, with these words of ours: '{ASKED if not other.randomised else ASKED_RANDOM}'. "
        + (
            "The five satisfaction questions shared one page in a random order not recorded. "
            if block == "satisfaction"
            else ""
        )
        + (
            "The percentages are coded 0-10 (the deposit's 0, 10, ..., 100 divided by ten). "
            if block == "accuracy"
            else ""
        )
        + "Persona: age (years, as typed; outside 18-100 left blank) and gender (the .qsf's "
        f"labels). Wording from Study {st.key}.qsf. US sample."
    )
    return {
        "study_id": STUDY_ID,
        "source": "researchbox",
        "experiment": f"{st.name}_{block}",
        "title": st.title,
        "data_file": seq_data_file(st),
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": "pid",
        "notes": notes,
        "condition": {"source_var": "cell", "factors": factors, "arms": arms},
        "outcomes": outcomes,
        "response_recode": recode,
        "missing_codes": [],
        "persona_map": {"age": "age", "gender": "gender"},
    }


def seq_recipe_path(st: SeqStudy, block: str) -> Path:
    return RECIPES / f"{STUDY_ID}_{st.name}_{block}.yaml"


def seq_render(st: SeqStudy, block: str) -> str:
    return yaml.safe_dump(seq_recipe(st, block), sort_keys=False, allow_unicode=True, width=100)


# ---------------------------------------------------------------------------
# Study S3
# ---------------------------------------------------------------------------

APPS = {"gps": 1, "food": 2}  # appName -> app (embedded data set together, asserted)
APP_LEVEL = {"gps": "navigation", "food": "food_delivery"}
ESTIMATE_LEVEL = {1: "point", 2: "range"}
ANSWERS = ("Yes, consistent", "No, inconsistent")
BINS = [
    "< 21 min",
    "21-25 min",
    "26-30 min",
    "31-35 min",
    "36-40 min",
    "41-45 min",
    "46-50 min",
    "51-55 min",
    "56-60 min",
    "61-65 min",
    "> 65 min",
]
PIPE = "${e://Field/estimate}"
MATRIX_QID = "QID113"


def assignments(sv: Survey) -> tuple[dict[str, int], dict[int, str]]:
    """(appName -> app, Condition -> estimate) as the flow's two randomisers set them."""
    sets = []
    for r in sv.randomisers:
        assert r["SubSet"] in (1, "1") and r.get("EvenPresentation"), r
        sets.append([{e["Field"]: e["Value"] for e in n["EmbeddedData"]} for n in r["Flow"]])
    assert len(sets) == 2, sets
    apps = {d["appName"]: int(d["app"]) for d in sets[0]}
    ests = {int(d["Condition"]): d["estimate"] for d in sets[1]}
    assert apps == APPS, apps
    assert {int(d["Condition"]): d["ConditionName"] for d in sets[1]} == {1: "point", 2: "range"}
    assert ests == {1: "43 minutes", 2: "33-53 minutes"}, ests
    return apps, ests


def shown_for(q: dict[str, Any]) -> str:
    """The appName a display-logic question is shown for (its only condition)."""
    dl = q["DisplayLogic"]
    assert set(dl) == {"0", "Type", "inPage"} and set(dl["0"]) == {"0", "Type"}, dl
    cond = dl["0"]["0"]
    assert (cond["LogicType"], cond["LeftOperand"], cond["Operator"]) == (
        "EmbeddedField",
        "appName",
        "EqualTo",
    ), cond
    return str(cond["RightOperand"])


def screens(sv: Survey) -> dict[str, list[str]]:
    """appName -> [instructions, scenario, response-page scenario, task instructions] (HTML)."""
    scen = sv.qids("Scenario")
    dv = sv.qids("DV")
    assert scen == ["QID94", "QID95", "QID96", "QID97"], scen
    assert dv == ["QID109", "QID110", "QID111", "QID112", MATRIX_QID, "QID114"], dv
    kinds = [x["Type"] for x in sv.block("Scenario")["BlockElements"]]
    assert kinds == ["Question", "Question", "Page Break", "Question", "Question"], kinds
    assert all(x["Type"] == "Question" for x in sv.block("DV")["BlockElements"])  # one page
    out: dict[str, list[str]] = {a: [] for a in APPS}
    for qid in [*scen, *dv[:4]]:
        q = sv.by_id[qid]
        assert (q["QuestionType"], q["Selector"]) == ("DB", "TB"), qid
        out[shown_for(q)].append(q["QuestionText"])
    assert sv.by_id[MATRIX_QID].get("DisplayLogic") is None
    assert sv.by_id["QID114"]["QuestionType"] == "Timing"
    assert all(len(v) == 4 for v in out.values()), out
    return out


def fill(raw: str, estimate: str) -> str:
    assert PIPE in raw or "${" not in raw, raw
    out = paragraphs(raw.replace(PIPE, estimate))
    assert "${" not in out, out
    return out


def arm_text(pages: list[str], estimate: str) -> str:
    instructions, scenario, again, task = (fill(p, estimate) for p in pages)
    assert again == scenario, (again, scenario)  # the response page repeats it in grey
    return f"{instructions}\n\n{scenario}\n\n{task}"


def matrix(sv: Survey) -> tuple[str, list[str]]:
    """(the stem, raw HTML; the statements in ChoiceOrder, plain)."""
    q = sv.by_id[MATRIX_QID]
    assert (q["QuestionType"], q["Selector"], q["SubSelector"]) == (
        "Matrix",
        "Likert",
        "SingleAnswer",
    )
    assert q["DataExportTag"] == "binary"
    assert q["Validation"]["Settings"]["ForceResponse"] == "ON"
    assert not q.get("Randomization") and not q.get("RecodeValues")
    assert not q.get("AnswerRandomization")
    assert q["ChoiceOrder"] == [str(k) for k in range(1, 12)]
    assert q["AnswerOrder"] == ["1", "2"]
    assert tuple(plain(q["Answers"][k]["Display"]) for k in ("1", "2")) == ANSWERS
    items = [plain(q["Choices"][k]["Display"]) for k in q["ChoiceOrder"]]
    assert items == BINS, items
    return q["QuestionText"], items


def stem(raw: str, estimate: str) -> str:
    return plain(raw.replace(PIPE, estimate))


@dataclass
class Arm:
    app: str  # appName
    condition: int  # Condition
    estimate: str
    text: str

    @property
    def factors(self) -> dict[str, str]:
        return {"app": APP_LEVEL[self.app], "estimate": ESTIMATE_LEVEL[self.condition]}


@dataclass
class Experiment:
    name: str
    title: str
    kind: str
    arms: list[Arm]
    stem_html: str
    bins: list[str]
    notes: str


def experiment() -> Experiment:
    sv = Survey(QSF)
    apps, ests = assignments(sv)
    pages = screens(sv)
    stem_html, bins = matrix(sv)
    arms = [
        Arm(app, cond, ests[cond], arm_text(pages[app], ests[cond]))
        for app in apps  # gps, food: the .qsf's order
        for cond in sorted(ests)
    ]
    return Experiment(
        name="s3",
        title="A navigation app or a food delivery app estimates 43 minutes or 33-53 minutes: "
        "which arrival times, from under 21 to over 65 minutes, are consistent with the "
        "estimate? (Study S3)",
        kind="mix",
        arms=arms,
        stem_html=stem_html,
        bins=bins,
        notes="Study S3 (AsPredicted #150577; Online Supplement 6), 188 people kept by the "
        "authors' exclusions (duplicate IP addresses, then duplicate Prolific ids). 2 x 2 "
        "between people: a navigation app or a food delivery app, a point estimate ('43 "
        "minutes') or a range ('33-53 minutes'). Each row is the instructions page, the "
        "scenario page and the response page's own instructions, word-for-word; the response "
        "page repeats the scenario in grey, identical to the scenario page, so it is written "
        "once. Consent and the opening location check (which ends the survey on a fail) are "
        "not narrated. Eleven outcomes, one per time bin of a fixed-order matrix on one page; "
        "each question is the matrix's stem with the arm's estimate piped in, then the bin. "
        "Answers as coded: 1 'Yes, consistent', 2 'No, inconsistent'. One kept person has a "
        "blank consent cell; the authors keep them.",
    )


# ---------------------------------------------------------------------------
# Coded data
# ---------------------------------------------------------------------------

N = 188
AGE_RANGE = (18, 100)


def data_file() -> str:
    return f"{STUDY_ID}_s3.csv"


def read_deposit() -> pd.DataFrame:
    return read_xlsx("S3")


def kept() -> pd.DataFrame:
    """The authors' sample (Study S3.do, in order)."""
    df = read_deposit()
    assert df["Id"].is_unique and (df["pass_screen"] == 1).all() and (df["Finished"] == 1).all()
    df = df[df["ExcludeDuplicateIP"] != 1]
    df = df[df["ExcludeDuplicateID"] != 1]
    return df.reset_index(drop=True)


def gender_labels() -> dict[int, str]:
    sv = Survey(QSF)
    (q,) = [q for q in sv.by_id.values() if q["DataExportTag"] == "gender"]
    rec = q["RecodeValues"]
    return {int(rec[k]): plain(v["Display"]) for k, v in q["Choices"].items()}


def prep() -> pd.DataFrame:
    """One coded row per kept person: the two assignment codes, eleven answers, persona."""
    df = kept()
    e = experiment()
    ests = {a.condition: a.estimate for a in e.arms}
    assert (df["appName"].map(APPS) == df["app"]).all()
    assert (df["Condition"].map(ests) == df["estimate"]).all()
    assert (df["Condition"].map(ESTIMATE_LEVEL) == df["ConditionName"]).all()
    out = pd.DataFrame({"pid": [f"s3_{i}" for i in df["Id"]]})
    out["app"] = df["app"].astype(int).values
    out["condition"] = df["Condition"].astype(int).values
    for k in range(1, len(BINS) + 1):
        v = df[f"binary_{k}"]
        assert v.isin([1, 2]).all(), k
        out[f"binary_{k}"] = v.astype(int).values
    age = pd.to_numeric(df["age"], errors="coerce")
    out["age"] = age.where(age.between(*AGE_RANGE)).astype("Int64").values
    labels = gender_labels()
    assert labels == {1: "Female", 2: "Male", 3: "Other"}, labels
    assert set(df["gender"].dropna().astype(int)) <= set(labels)
    out["gender"] = df["gender"].map(lambda g: labels[int(g)] if pd.notna(g) else None).values
    assert len(out) == N and out["pid"].is_unique, len(out)
    return out


def check_codebook() -> None:
    book = pd.read_csv(CODEBOOK / "Study S3.xlsx___CODEBOOK.csv")
    df = read_deposit()
    assert list(book["varname"]) == list(df.columns)
    d = book.set_index("varname")["description"]
    assert '1 = "Yes, consistent"; 2 = "No, inconsistent"' in d["binary_1"]
    assert d["binary_1"].startswith("var10-var20")
    assert list(df.columns[9:20]) == [f"binary_{k}" for k in range(1, 12)]
    assert "1 = GPS app, 2 = food delivery app" in d["app"]
    assert "1 = point estimate, 2 = range estimate" in d["Condition"]
    assert "3 = other" in d["gender"]


# ---------------------------------------------------------------------------
# The recipe
# ---------------------------------------------------------------------------


def scale() -> dict[str, Any]:
    return {"min": 1, "max": 2, "min_label": ANSWERS[0], "max_label": ANSWERS[1]}


def recipe(e: Experiment) -> dict[str, Any]:
    arms = []
    for i, a in enumerate(e.arms):
        q = stem(e.stem_html, a.estimate)
        arms.append(
            {
                "raw_values": {"app": APPS[a.app], "condition": a.condition},
                "condition_num": i,
                "factors": a.factors,
                "text": a.text,
                "items": {t: {"outcome_question": f"{q} {b}"} for t, b in enumerate(e.bins)},
            }
        )
    first = stem(e.stem_html, e.arms[0].estimate)
    outcomes = [
        {"var": f"binary_{t + 1}", "task_num": t, "question": f"{first} {b}", "scale": scale()}
        for t, b in enumerate(e.bins)
    ]
    notes = (
        f"{PAPER}\n\nGENERATED by scripts/gen_researchbox482.py; every judgement is in its "
        f"docstring. {e.notes}\n\nWording from {QSF} (the blocks the survey flow reaches), "
        "word-for-word; no picture anywhere in it. Typography normalised (HTML, non-breaking "
        "spaces, curly quotes); bold and grey dropped. Data: Study S3.xlsx. Persona: age "
        "(years, as typed; outside 18-100 left blank) and gender (the .qsf's labels). US "
        "sample (Prolific)."
    )
    return {
        "study_id": STUDY_ID,
        "source": "researchbox",
        "experiment": e.name,
        "title": e.title,
        "data_file": data_file(),
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": "pid",
        "notes": notes,
        "condition": {
            "source_vars": ["app", "condition"],
            "factors": ["app", "estimate"],
            "arms": arms,
        },
        "outcomes": outcomes,
        "response_recode": {1: 1, 2: 2},
        "missing_codes": [],
        "persona_map": {"age": "age", "gender": "gender"},
    }


def recipe_path(e: Experiment) -> Path:
    return RECIPES / f"{STUDY_ID}_{e.name}.yaml"


def render(e: Experiment) -> str:
    return yaml.safe_dump(recipe(e), sort_keys=False, allow_unicode=True, width=100)


def all_recipes() -> list[tuple[Path, str]]:
    """(path, text) of every recipe this box builds."""
    e = experiment()
    out = [(recipe_path(e), render(e))]
    for st in SEQ_STUDIES:
        out += [(seq_recipe_path(st, b), seq_render(st, b)) for b in st.blocks]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prep", action="store_true", help="code the data")
    ap.add_argument("--check", action="store_true", help="exit 1 if any recipe differs")
    args = ap.parse_args()
    if args.prep:
        check_pictures()
        check_codebook()
        check_sequences()
        coded = [(RAW / data_file(), prep())]
        coded += [(RAW / seq_data_file(st), seq_prep(st)) for st in SEQ_STUDIES]
        for path, df in coded:
            df.to_csv(path, index=False)
            print(f"wrote {path.relative_to(REPO)}")
        return 0
    bad = 0
    for path, text in all_recipes():
        if args.check:
            same = path.exists() and path.read_text() == text
            print(("matches " if same else "DIFFERS ") + path.name)
            bad += not same
        else:
            path.write_text(text)
            print(f"wrote {path.relative_to(REPO)}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
