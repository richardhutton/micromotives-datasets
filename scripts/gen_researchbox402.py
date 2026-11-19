#!/usr/bin/env python3
"""Write recipes/researchbox402_*.yaml: historical prices and purchase deferral (5 recipes).

Gunadi MP, Evangelidis I (2022), "The Impact of Historical Price Information on Purchase
Deferral", Journal of Marketing Research 59(3):623-640, doi:10.1177/00222437211060359.
ResearchBox 402 ("Historical Price Information & Purchase Deferral",
https://researchbox.org/402). CC BY 4.0 ("All content posted to ResearchBox is under a CC By
4.0 License", the box page). US dollars kept as the source has them.

Every judgement is here, in code, so the recipes can be re-derived and reviewed.

THE DESIGN. People shopping for a product see its past prices, which fell or rose, once or
several times, to the same current price, and say whether they would buy it now or later.
Studies 2-4 also ask what the price will be in a week, Study 2 whether it will keep moving
the same way. The box holds a data file and a codebook per study (1a, 1b, 2, 3, 4, 5), one
AsPredicted pre-registration per study and "Survey Materials.pdf" (62 pages, every study).
There is no .qsf and no analysis script.

THE INSTRUMENT. No .qsf. rich (19 Nov 2026): build a study only if the materials PDF gives
every condition's text and the outcome wording and each arm ties to the data's columns
unambiguously, and skip any study whose price history is a picture. The PDF holds 16
pictures, all on pages 44-59, all Study 5 (asserted from `pdfimages -list`); pages 1-43 are
text only. Its text layer is read with pdftotext, never typed in by hand.

THE WORDING IS THE FIELDED SCREEN'S. Each data file's variable labels are the Qualtrics
export of that column's question, i.e. the screen as fielded. CLAUDE.md makes the fielded
questionnaire the only authority on stimulus wording, so (main-session ruling, 19 Nov 2026)
every scenario and question that a label carries is built from the label, typos and all,
and the PDF supplies only what no label carries: Study 1b's instructions, the answer
options' order and the bounds of the price question, the page structure and orders, and
the one label the export cut short (Study 1b's DL3, whose words agree with the PDF's as far
as they go). Typography only is normalised: a line break the export lost becomes a space
("holidays.Only"), and Qualtrics' matrix joiner (": - ") is dropped. check_labels() asserts
that every built screen's words ARE its label's words, and LABEL_DIFFERENCES records, and
asserts both ways, where the PDF differs from them: "One weeks ago" on every fielded Study
1a screen (the PDF: "One week ago"); the prediction question fielded as "... will be? (in
$)." (Studies 2, 4) and "... the price of the speaker will be? (in $)." (Study 3), the PDF
having "... the price will be?"; and full stops missing after some amounts (Studies 3, 4).

THE TIE. The labels also tie each PDF arm to its data column: the dollar amounts and dates
in the label must equal the PDF screen's, in order, and exactly one PDF screen must match
each column (asserted; DL3 matches as a prefix, still uniquely; Study 1b's four day-1
screens are one text, so each ties within its own arm).

WHAT IS BUILT. Five recipes:
- study1a: flight tickets, 2 (decrease, increase) x 2 (one change, four changes) between
  people; buy the tickets now or later.
- study1b: a TV over four days, the same 2 x 2. Everyone saw January 16 at $1200 (one
  screen, the same for all four arms) and chose now or later; whoever chose later saw the
  next day's price, up to January 19. Each screen is its own condition (1 + 4 x 3 = 13) and
  its own outcome (task 0-3, "What would you do?" on day 1-4), each outcome naming its own
  assignment column (Outcome.condition_var). The routing is asserted: a day's answer exists
  exactly when the day before was answered "later".
- study2: a Bluetooth speaker, the same 2 x 2; buy now or later, then the price in a week
  and agreement that the price will keep moving the same way, those two in a random order.
- study3: the speaker, 2 x 3 (one change, four steady changes, or five changes with a
  reversal four days ago); buy now or later, then the price in a week.
- study4: a tablet, 2 x 3 (one change in the last week, one change three weeks ago, or five
  changes); buy now or later and the price in a week, in a random order.

NOT BUILT (NOT_BUILT): study5. Each product page is a picture of the store's web page, and
the picture alone carries the price history ("Was: EUR24 (4 days ago) ... CURRENT PRICE:
EUR15", materials PDF p. 44-59); the PDF's text gives only "What will you do?". rich's
picture rule: skip, and do not transcribe numbers from a picture.

THE ASSIGNMENT. No file has an assignment column: each arm's answers are in their own
columns, blank for anyone not shown that arm. In every file each person has exactly one
arm's choice column filled (asserted), and their other answers sit in that arm's columns
only (asserted). Jev (scripts/recipe_prep.py, 19 Nov 2026, run as `--source dataverse`, its
nearest open-archive class, since its choices list no researchbox) answered NONE_OF_THESE
for the assignment column on all five files (confidence 0.89, 0.84, 0.86, 0.82, 0.85 for
1a, 1b, 2, 3, 4), which agrees. The coded file gives each person an id from their row in
the deposit ("study2_17"), the only key the deposit has.

THE QUESTIONS. Each screen is a scenario followed by its question. The scenario's first
sentences (identical across arms) are shared_context; the price lines are the arm's text;
the question is the outcome, all word-for-word from the PDF. Buy now or later: 1 = "I would
buy the <product> now", 2 = "... later" (the .sav value labels and the PDF's options agree;
asserted). Price in a week: whole dollars, 0-150 (Studies 2, 3) or 0-500 (Study 4), the
PDF's "(in $; open-ended with minimum of $0 and maximum of $150)" being the bounds, not
screen text, so the scale states them. Study 2's agreement statement says "decrease" in the
decrease arms and "increase" in the increase arms, so it is set per arm (Arm.items), 1-7,
"strongly disagree", "neither agree nor disagree", "strongly agree" from the PDF.

ORDER, AND WHAT A ROW NARRATES. CONVENTIONS ("Repeated measures within one block"): a later
row may narrate an earlier screen, as asked, only where the order is fixed.
- Study 2: the choice is on page 1, fixed; the prediction and the agreement question are
  pages 2-3 "(in random order)", unrecorded. So each of those rows narrates the choice as
  asked, 'You were asked "What would you do?"' (words of OURS, recorded in notes), and never
  the other.
- Study 3: choice on page 1, prediction on page 2, fixed; the prediction row narrates the
  choice the same way.
- Study 4: the two are "pages 1-2 (in random order)", unrecorded; neither row narrates the
  other.
- Study 1b: each day's screen restates the earlier days' prices itself, and the instructions
  (shared_context) say that choosing to wait updates the page. No words are added; nothing
  narrates the earlier answers.
Every later screen repeats the full scenario, so each row's condition is true as it stands.

DROPPED. Nothing else was asked in Studies 1a-4 but age and gender.

EXCLUSIONS. None pre-registered ("We will not exclude any data", every study), and none
made: every row of every file is kept (802, 800, 802, 1,506, 1,506).

PERSONA. Age and gender. Gender labels from each file's own value labels (Female, Male,
Non-Binary; Study 1a offered only female/male). Jev mapped both at confidence 1.00 in every
file and found no non-answer label (10-39 labels per file, no disagreement with the regex).
Age as typed, except that ages outside 18-100 are left blank: no file validates it, and
Study 4 holds a 4 and a 17 (our judgement; the only two ages touched).

ANSWER KEY. No analysis script is deposited and the paper's tables were not read, so the
reference is the deposit itself, read column by column independently of `prep`. The tests
recompute each pre-registered analysis from the BUILT rows and from the deposit and require
them equal: the saturated logits of deferral (1a, 2, 3, 4), the count of deferrals per
person by cell (1b, an OLS on the 2 x 2), and the cell means of the price prediction and
the agreement item (2, 3, 4).

    uv run python scripts/gen_researchbox402.py --prep   # code the data
    uv run python scripts/gen_researchbox402.py          # write the recipes
    uv run python scripts/gen_researchbox402.py --check  # exit 1 if any recipe differs
"""

from __future__ import annotations

import argparse
import difflib
import re
import subprocess
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any

import pandas as pd
import pyreadstat
import yaml

REPO = Path(__file__).resolve().parents[1]
STUDY_ID = "researchbox402"
RAW = REPO / "data" / "raw" / STUDY_ID
MATERIALS = RAW / "Materials"
PDF = MATERIALS / "Survey Materials.pdf"
DATA = RAW / "Data"
CODEBOOK = RAW / "Codebook"
RECIPES = REPO / "recipes"
LICENCE = (
    'CC BY 4.0, stated on the box page https://researchbox.org/402 ("All content posted '
    'to ResearchBox is under a CC By 4.0 License"). Read 19 Nov 2026.'
)
PAPER = (
    'Gunadi MP, Evangelidis I (2022), "The Impact of Historical Price Information on '
    'Purchase Deferral", Journal of Marketing Research 59(3):623-640, '
    "doi:10.1177/00222437211060359. ResearchBox 402 (https://researchbox.org/402)."
)

TRUNCATED = "DL3"  # the one label the export cut short; its screen is read from the PDF

# tag -> the deposit's study label ("Study 1a - Data.sav")
LABEL = {"study1a": "1a", "study1b": "1b", "study2": "2", "study3": "3", "study4": "4"}

NOT_BUILT = {
    "study5": "ESADE store, four products (card holder, laptop bag, charger, water bottle): "
    "each product page is a picture of the web page, and the picture alone carries the price "
    "history ('Was: EUR24 (4 days ago) ... CURRENT PRICE: EUR15'); the PDF's text gives only "
    "'What will you do?' (materials PDF p. 44-59). rich's picture rule.",
}

# Every picture in the PDF, by page: Study 5's sixteen product pages and nothing else.
PICTURE_PAGES = list(range(44, 60))

# ---------------------------------------------------------------------------
# The PDF
# ---------------------------------------------------------------------------

_TYPO = {"\xa0": " ", "’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-", "\f": ""}


def norm(raw: str) -> str:
    """One line of plain text. Typography only."""
    s = raw
    for a, b in _TYPO.items():
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


@cache
def pdf_lines() -> tuple[str, ...]:
    """The PDF's text layer, one entry per line, page numbers and blank lines dropped."""
    out = subprocess.run(["pdftotext", str(PDF), "-"], capture_output=True, text=True, check=True)
    lines = [norm(x) for x in out.stdout.splitlines()]
    return tuple(x for x in lines if x and not re.fullmatch(r"\d+", x))


def check_pictures() -> None:
    out = subprocess.run(
        ["pdfimages", "-list", str(PDF)], capture_output=True, text=True, check=True
    ).stdout.splitlines()[2:]
    pages = [int(x.split()[0]) for x in out if x.strip()]
    assert pages == PICTURE_PAGES, pages


STUDY_HEADING = {"study1a": "Study 1a", "study1b": "Study 1b", "study2": "Study 2"}
STUDY_HEADING |= {"study3": "Study 3", "study4": "Study 4", "study5": "Study 5"}


def study_lines(tag: str) -> list[str]:
    lines = list(pdf_lines())
    heads = [lines.index(h) for h in STUDY_HEADING.values()]
    assert heads == sorted(heads)
    start = lines.index(STUDY_HEADING[tag])
    end = min([h for h in heads if h > start], default=len(lines))
    return lines[start + 1 : end]


QUESTION_START = ("What would you do?", "In a week from now", "Please indicate")


@dataclass
class Screen:
    header: str  # "[Single decrease - page 2 (displayed if ...)]"
    scenario: str
    question: str
    options: list[str]


def screens(tag: str) -> tuple[list[str], list[Screen]]:
    """(lines before the first condition, every screen in the order the PDF prints them)."""
    lines = study_lines(tag)
    i = lines.index("[Experimental condition]")
    intro, body = lines[:i], lines[i + 1 :]
    out: list[Screen] = []
    header = ""
    buf: list[str] = []
    opts: list[str] = []

    def flush() -> None:
        nonlocal buf, opts
        if buf:
            text = " ".join(buf)
            starts = [text.find(q) for q in QUESTION_START if q in text]
            assert len(starts) == 1, (tag, header, text)
            out.append(Screen(header, text[: starts[0]].strip(), text[starts[0] :], opts))
        buf, opts = [], []

    for line in body:
        if line.startswith("[Demographic"):
            break
        if line.startswith("["):
            flush()
            header = line
        elif re.fullmatch(r"\(Page \d or \d\)", line):
            flush()
        elif line.startswith("o "):
            opts.append(line[2:])
        else:
            buf.append(line)
    flush()
    return intro, out


# ---------------------------------------------------------------------------
# The .sav labels
# ---------------------------------------------------------------------------


@cache
def sav(tag: str) -> tuple[pd.DataFrame, Any]:
    return pyreadstat.read_sav(str(DATA / f"Study {LABEL[tag]} - Data.sav"))


def label(tag: str, col: str) -> str:
    return norm(sav(tag)[1].column_names_to_labels[col])


def prices(text: str) -> list[str]:
    """The dollar amounts and dates, in order ("now January 18" is not "January 18")."""
    return re.findall(r"\$\d+|(?:now )?January \d+", text)


def ties(tag: str, col: str, candidates: list[Screen]) -> Screen:
    """The one PDF screen whose dollar amounts are the column label's, in order."""
    got = prices(label(tag, col))
    full = [s for s in candidates if prices(s.scenario) == got]
    if label(tag, col).endswith(("?", "(in $).", "future")):  # the whole screen
        match = full
    else:  # the export cut the label short (Study 1b's DL3)
        match = [s for s in candidates if prices(s.scenario)[: len(got)] == got]
    assert len(match) == 1, (tag, col, got, [s.header for s in match])
    return match[0]


def _words(s: str) -> list[str]:
    # "holidays.Only", "$199Four": an export that lost a line break
    s = re.sub(r"(?<=[.\d])(?=[A-Z])", " ", s)
    s = s.replace(": - ", ": ")  # Qualtrics' matrix stem/statement joiner
    return s.split()


def differences(pdf_text: str, label_text: str) -> list[tuple[str, str]]:
    """Word-level differences, PDF side first."""
    a, b = _words(pdf_text), _words(label_text)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    return [
        (" ".join(a[i1:i2]), " ".join(b[j1:j2]))
        for op, i1, i2, j1, j2 in sm.get_opcodes()
        if op != "equal"
    ]


def fielded(tag: str, col: str, lead: str) -> tuple[str, str]:
    """(scenario body, question) as fielded: the column's label, the shared lead removed.

    Typography only: a line break the export lost ("holidays.Only") becomes a space, and
    Qualtrics' matrix joiner (": - ") is dropped. Words are the label's, typos and all.
    """
    words = " ".join(_words(label(tag, col)))
    assert words.startswith(lead + " "), (tag, col, words[:80])
    rest = words[len(lead) + 1 :]
    starts = [rest.find(q) for q in QUESTION_START if q in rest]
    assert len(starts) == 1, (tag, col, rest)
    return rest[: starts[0]].strip(), rest[starts[0] :]


# Every difference between the PDF screen and the fielded label, column by column. Read
# 19 Nov 2026; asserted both ways by check_labels(), so a new one fails the build.
_ONE_WEEKS = [("week", "weeks")]  # "One weeks ago" on every fielded screen
_IN_DOLLARS = ("", "(in $).")
_SPEAKER = ("", "of the speaker")
LABEL_DIFFERENCES: dict[str, dict[str, list[tuple[str, str]]]] = {
    "study1a": dict.fromkeys(("DecrLow", "DecrHigh", "IncrLow", "IncrHigh"), _ONE_WEEKS),
    # the export cut this label short; the words it has agree
    "study1b": {"DL3": [("Currently, the price of the TV is $900. What would you do?", "")]},
    "study2": {
        c: [_IN_DOLLARS] for c in ("PredDecLow", "PredDecHigh", "PredIncLow", "PredIncHigh")
    },
    "study3": {
        "PredDecLow": [_SPEAKER, _IN_DOLLARS],
        "PredDecHighMo": [_SPEAKER, _IN_DOLLARS],
        "DecHighNon": [("$80.", "$80")],
        "PredDecHighNon": [("$80.", "$80"), _SPEAKER, _IN_DOLLARS],
        "PredIncLow": [_SPEAKER, _IN_DOLLARS],
        "PredIncHigh": [_SPEAKER, _IN_DOLLARS],
        "IncHighNon": [("$40.", "$40")],
        "PredIncHighNon": [("$40.", "$40"), _SPEAKER, _IN_DOLLARS],
    },
    "study4": {
        "PredLowDeLa": [_IN_DOLLARS],
        "PredDeEa": [_IN_DOLLARS],
        "HighDe": [("$399.", "$399")],
        "PredHighDe": [("$399.", "$399"), _IN_DOLLARS],
        "PredLowInLa": [_IN_DOLLARS],
        "LowInEa": [("$199.", "$199")],
        "PredInEa": [("$199.", "$199"), _IN_DOLLARS],
        "HighIn": [("$199.", "$199")],
        "PredHighIn": [("$199.", "$199"), ("$299.", "$299"), _IN_DOLLARS],
    },
}

# The PDF's response-format notes, which are not screen text.
_FORMAT_NOTE = re.compile(
    r" \(in \$; open-ended with minimum of \$0 and maximum of \$(\d+)\)\.$"
    r"| \(1 = strongly disagree, 4 = neither agree nor disagree, 7 = strongly agree\)\.$"
)


def strip_format_note(question: str) -> str:
    return _FORMAT_NOTE.sub("", question)


# ---------------------------------------------------------------------------
# The experiments
# ---------------------------------------------------------------------------


@dataclass
class Arm:
    code: int
    factors: dict[str, str]
    text: str
    columns: dict[str, str]  # outcome var -> deposit column
    items: dict[str, dict[str, str]] = field(default_factory=dict)  # var -> overrides


@dataclass
class Outcome:
    var: str
    question: str
    scale: dict[str, Any]
    condition_var: str | None = None
    recode: dict[int, int] | None = None


@dataclass
class Experiment:
    name: str
    title: str
    shared_context: str
    factors: list[str]
    arms: list[Arm]
    outcomes: list[Outcome]
    notes: str
    source_var: str = "arm"
    lead: str = ""  # the part of shared_context that the labels carry


def _choice_scale(scr: list[Screen]) -> dict[str, Any]:
    (opts,) = {tuple(s.options) for s in scr}
    assert len(opts) == 2 and opts[0].endswith(" now") and opts[1].endswith(" later"), opts
    return {"min": 1, "max": 2, "min_label": opts[0], "max_label": opts[1]}


def _split_shared(texts: list[str], prefix: str) -> list[str]:
    for t in texts:
        assert t.startswith(prefix + " "), (prefix, t[:80])
    return [t[len(prefix) + 1 :] for t in texts]


ASKED = 'You were asked "What would you do?"'  # words of OURS (CONVENTIONS, narrating)

# arm header in the PDF -> factors, for the 2 x 2 studies
TWO_BY_TWO = {
    "Single decrease": {"direction": "decrease", "frequency": "low"},
    "Multiple decreases": {"direction": "decrease", "frequency": "high"},
    "Single increase": {"direction": "increase", "frequency": "low"},
    "Multiple increases": {"direction": "increase", "frequency": "high"},
}


def _arm_name(header: str) -> str:
    return re.split(r" - |\]", header.strip("["))[0]


def study1a() -> Experiment:
    _, scr = screens("study1a")
    assert [s.header for s in scr] == [f"[{h}]" for h in TWO_BY_TWO]
    assert {s.question for s in scr} == {"What would you do?"}
    shared = (
        "Imagine that you are buying flight tickets for your upcoming holidays. Only one "
        "airline flies directly to that destination."
    )
    texts = _split_shared([s.scenario for s in scr], shared)
    cols = ["DecrLow", "DecrHigh", "IncrLow", "IncrHigh"]
    arms = []
    for i, (s, _t, c) in enumerate(zip(scr, texts, cols, strict=True)):
        assert ties("study1a", c, scr) is s
        body, q = fielded("study1a", c, shared)
        assert q == "What would you do?"
        arms.append(Arm(i + 1, TWO_BY_TWO[_arm_name(s.header)], body, {"choice": c}))
    return Experiment(
        name="study1a",
        title="Flight tickets whose price fell or rose, once or week by week, to $400 now: "
        "buy them now or later? (Study 1a)",
        shared_context=shared,
        lead=shared,
        factors=["direction", "frequency"],
        arms=arms,
        outcomes=[Outcome("choice", "What would you do?", _choice_scale(scr))],
        notes=(
            "Study 1a (pre-registered Sep 2019, AsPredicted #28377), 802 people, all kept "
            '("We will not exclude any data"). 2 x 2 between people: the tickets were $600 '
            "(decrease) or $200 (increase) four weeks ago and are $400 now, having changed "
            "once (in the last week) or every week. 1 = buy now, 2 = buy later, as answered."
        ),
    )


def study1b() -> Experiment:
    intro, scr = screens("study1b")
    assert {s.question for s in scr} == {"What would you do?"}
    assert len(scr) == 16
    shared_intro = " ".join(intro)
    assert shared_intro.startswith("IMPORTANT INFORMATION: Prices of products change")
    lead = (
        "Imagine that you consider buying a new TV. You have been checking the price of a TV "
        "that you like during the past days."
    )
    texts = _split_shared([s.scenario for s in scr], lead)
    by_arm: dict[str, list[tuple[Screen, str]]] = {}
    for s, t in zip(scr, texts, strict=True):
        by_arm.setdefault(_arm_name(s.header), []).append((s, t))
    assert list(by_arm) == list(TWO_BY_TWO)
    prefix = {"Single decrease": "DL", "Multiple decreases": "DH"}
    prefix |= {"Single increase": "IL", "Multiple increases": "IH"}
    # Day 1 is the same screen in every arm: one condition for all.
    (day1,) = {t for pages in by_arm.values() for _, t in pages[:1]}
    assert day1 == "It is now January 16, 2021. Currently, the price of the TV is $1200."
    assert {fielded("study1b", f"{g}1", lead) for g in ("DL", "DH", "IL", "IH")} == {
        (day1, "What would you do?")
    }
    # No price change has been shown yet, so neither factor has a level on it.
    none = {"direction": "none_yet", "frequency": "none_yet", "date": "2021-01-16"}
    arms = [Arm(1, none, day1, {})]
    for a, (name, pages) in enumerate(by_arm.items()):
        assert pages[0][0].header == f"[{name} - page 1]"
        for k, (s, t) in enumerate(pages, 1):
            col = f"{prefix[name]}{k}"
            if k == 1:  # the four day-1 screens are one text: tie within the arm
                assert ties("study1b", col, [p[0] for p in pages]) is s
                continue
            assert ties("study1b", col, scr) is s
            assert s.header == (
                f"[{name} - page {k} (displayed if the participant deferred choice in the "
                "previous page)]"
            )
            date = f"2021-01-{15 + k}"
            if col != TRUNCATED:  # the fielded words, where the label carries them
                t, q = fielded("study1b", col, lead)
                assert q == "What would you do?"
            assert f"It is now January {15 + k}, 2021." in t
            arms.append(Arm(1 + a * 3 + (k - 1), TWO_BY_TWO[name] | {"date": date}, t, {}))
    outcomes = [
        Outcome(f"choice_day{k}", "What would you do?", _choice_scale(scr), f"cond_day{k}")
        for k in range(1, 5)
    ]
    return Experiment(
        name="study1b",
        title="A TV whose price falls or rises, once or day by day, from $1200: buy it now or "
        "wait a day, up to four days (Study 1b)",
        shared_context=f"{shared_intro} {lead}",
        lead=lead,
        factors=["direction", "frequency", "date"],
        arms=arms,
        outcomes=outcomes,
        notes=(
            "Study 1b (pre-registered Dec 2020, AsPredicted #54763), 800 people, all kept. "
            "2 x 2 between people (the price falls or rises; once, on January 17, or every "
            "day), shown day by day: everyone saw January 16 at $1200 (the same screen in "
            "every arm, one condition) and chose now or later; anyone who chose later saw "
            "the next day's screen, which restates the earlier prices, up to January 19. "
            "Each day is its own condition and its own outcome (task 0-3), each outcome "
            "naming its own assignment column (cond_day1..cond_day4); a person has one row "
            "per day they reached (asserted: a day is answered exactly when the day before "
            'was answered "later"). The instructions shown first, which say that choosing '
            "to wait updates the page, are in every row's shared context. No words added. "
            "1 = buy now, 2 = buy later, as answered. The pre-registered measure is the "
            "number of days a person chose later (0-4). A person who bought on day 1 has "
            "one row, whose condition cannot show their arm: none of it had been shown."
        ),
        source_var="cond_day1",
    )


def _price_scale(question: str) -> dict[str, Any]:
    m = _FORMAT_NOTE.search(question)
    assert m and m.group(1), question
    return {"min": 0, "max": int(m.group(1))}


def study2() -> Experiment:
    _, scr = screens("study2")
    lead = (
        "Imagine that you consider buying a Bluetooth speaker. You have been checking the "
        "price of a speaker that you like during the past weeks."
    )
    texts = _split_shared([s.scenario for s in scr], lead)
    # Per arm, three screens: page 1 (choice), then the two of pages 2-3.
    assert len(scr) == 12
    cols = {
        "Single decrease": ("DecLow", "PredDecLow", "TempDecLow_1"),
        "Multiple decreases": ("DecHigh", "PredDecHigh", "TempDecHigh_1"),
        "Single increase": ("IncLow", "PredIncLow", "TempIncLow_1"),
        "Multiple increases": ("IncHigh", "PredIncHigh", "TempIncHigh_1"),
    }
    arms, pred_qs, temp_qs, pred_fielded = [], set(), {}, set()
    for a, name in enumerate(TWO_BY_TWO):
        (c, p, t), (s1, s2, s3) = cols[name], scr[3 * a : 3 * a + 3]
        assert s1.header == f"[{name} - page 1]"
        assert s2.header == s3.header == f"[{name} - pages 2-3 (in random order)]"
        assert texts[3 * a] == texts[3 * a + 1] == texts[3 * a + 2]
        assert s1.question == "What would you do?"
        assert ties("study2", c, scr[0::3]) is s1
        assert ties("study2", p, scr[1::3]) is s2 and ties("study2", t, scr[2::3]) is s3
        assert s2.question.startswith("In a week") and s3.question.startswith("Please")
        pred_qs.add(s2.question)
        word = TWO_BY_TWO[name]["direction"]
        agree_note = " (1 = strongly disagree, 4 = neither agree nor disagree, 7 = strongly agree)."
        assert s3.question.endswith(agree_note)  # the scale below is this note's
        tq = strip_format_note(s3.question)
        assert tq.endswith(f"The price will continue to {word} in the future"), tq
        temp_qs[name] = tq
        body, q1 = fielded("study2", c, lead)
        pbody, q2 = fielded("study2", p, lead)
        tbody, q3 = fielded("study2", t, lead)
        assert q1 == "What would you do?" and q3.endswith(tq.split(": ", 1)[1])
        pred_fielded.add(q2)
        arms.append(
            Arm(
                a + 1,
                TWO_BY_TWO[name],
                body,
                {"choice": c, "pred": p, "agree": t},
                {
                    "pred": {"condition_text": f"{pbody} {ASKED}"},
                    "agree": {"condition_text": f"{tbody} {ASKED}", "outcome_question": q3},
                },
            )
        )
        temp_qs[name] = q3
    (pq,) = pred_qs
    (fq,) = pred_fielded
    agree_scale = {
        "min": 1,
        "max": 7,
        "min_label": "strongly disagree",
        "mid_label": "neither agree nor disagree",
        "max_label": "strongly agree",
    }
    return Experiment(
        name="study2",
        title="A Bluetooth speaker whose price fell or rose, once or week by week, to $60 now: "
        "buy now or later, what will it cost in a week, and will the price keep moving? "
        "(Study 2)",
        shared_context=lead,
        lead=lead,
        factors=["direction", "frequency"],
        arms=arms,
        outcomes=[
            Outcome("choice", "What would you do?", _choice_scale(scr[0::3])),
            Outcome("pred", fq, _price_scale(pq), recode=_identity(0, 150)),
            Outcome("agree", temp_qs["Single decrease"], agree_scale),
        ],
        notes=(
            "Study 2 (pre-registered Dec 2020, AsPredicted #54323), 802 people, all kept. "
            "2 x 2 between people: the speaker was $100 (decrease) or $20 (increase) four "
            "weeks ago and is $60 now, having changed once or every week. Page 1: buy now or "
            "later (1 now, 2 later). Pages 2-3, in a random order the deposit does not "
            "record, each repeating the scenario: the price in a week (whole dollars, the "
            "PDF's bounds $0-$150) and agreement, 1-7, that the price will continue to "
            "decrease (decrease arms) or increase (increase arms). The page-2 and page-3 "
            "rows narrate page 1 as asked, in words of OURS: 'You were asked \"What would "
            "you do?\"'; neither names the other, whose position is unrecorded."
        ),
    )


def _identity(lo: int, hi: int) -> dict[int, int]:
    return {k: k for k in range(lo, hi + 1)}


SIX = {
    "study3": [
        ("Single decrease", "DecLow", "PredDecLow", "decrease", "single"),
        ("Multiple monotonic decreases", "DecHighMo", "PredDecHighMo", "decrease", "monotonic"),
        ("Multiple nonmonotonic decreases", "DecHighNon", "PredDecHighNon", "decrease", "nonmono"),
        ("Single increase", "IncLow", "PredIncLow", "increase", "single"),
        ("Multiple monotonic increases", "IncHighMo", "PredIncHigh", "increase", "monotonic"),
        ("Multiple nonmonotonic increases", "IncHighNon", "PredIncHighNon", "increase", "nonmono"),
    ],
    "study4": [
        ("Single decrease late", "LowDeLa", "PredLowDeLa", "decrease", "single_late"),
        ("Single decrease early", "LowDeEa", "PredDeEa", "decrease", "single_early"),
        ("Multiple decreases", "HighDe", "PredHighDe", "decrease", "multiple"),
        ("Single increase late", "LowInLa", "PredLowInLa", "increase", "single_late"),
        ("Single increase early", "LowInEa", "PredInEa", "increase", "single_early"),
        ("Multiple increases", "HighIn", "PredHighIn", "increase", "multiple"),
    ],
}
_PATTERN = {"nonmono": "nonmonotonic"}


def two_by_three(tag: str) -> tuple[list[Screen], list[Arm], str, str]:
    _, scr = screens(tag)
    product = {"study3": "speaker", "study4": "tablet"}[tag]
    lead = (
        f"Imagine that you consider buying a {'Bluetooth speaker' if tag == 'study3' else 'tablet'}"
        f". You have been checking the price of a {product} that you like during the past weeks."
    )
    texts = _split_shared([s.scenario for s in scr], lead)
    assert len(scr) == 12
    arms = []
    pred_fielded = set()
    for a, (name, c, p, direction, pattern) in enumerate(SIX[tag]):
        s1, s2 = scr[2 * a : 2 * a + 2]
        if tag == "study3":
            assert s1.header == f"[{name} - page 1]" and s2.header == f"[{name} - page 2]"
        else:
            assert s1.header == s2.header == f"[{name} - pages 1-2 (in random order)]"
        assert texts[2 * a] == texts[2 * a + 1]
        assert s1.question == "What would you do?" and s2.question.startswith("In a week")
        assert ties(tag, c, scr[0::2]) is s1
        assert ties(tag, p, scr[1::2]) is s2
        body, q1 = fielded(tag, c, lead)
        pbody, q2 = fielded(tag, p, lead)
        assert q1 == "What would you do?"
        pred_fielded.add(q2)
        f = {"direction": direction, "pattern": _PATTERN.get(pattern, pattern)}
        items = {}
        if tag == "study3":  # fixed order: the prediction row narrates the choice
            items = {"pred": {"condition_text": f"{pbody} {ASKED}"}}
        elif pbody != body:  # the fielded prediction screen's own words
            items = {"pred": {"condition_text": pbody}}
        arms.append(Arm(a + 1, f, body, {"choice": c, "pred": p}, items))
    (fq,) = pred_fielded
    return scr, arms, lead, fq


def study3() -> Experiment:
    scr, arms, lead, fq = two_by_three("study3")
    (pq,) = {s.question for s in scr[1::2]}
    return Experiment(
        name="study3",
        title="A Bluetooth speaker whose price fell or rose to $60, once, week by week, or with "
        "a reversal four days ago: buy now or later, and what will it cost in a week? "
        "(Study 3)",
        shared_context=lead,
        lead=lead,
        factors=["direction", "pattern"],
        arms=arms,
        outcomes=[
            Outcome("choice", "What would you do?", _choice_scale(scr[0::2])),
            Outcome("pred", fq, _price_scale(pq), recode=_identity(0, 150)),
        ],
        notes=(
            "Study 3 (pre-registered Feb 2021, AsPredicted #59001), 1,506 people, all kept. "
            "2 x 3 between people: the speaker was $100 (decrease) or $20 (increase) four "
            "weeks ago and is $60 now, having changed once, every week (monotonic), or every "
            "week with a step back four days ago (nonmonotonic). Page 1: buy now or later "
            "(1 now, 2 later); page 2, repeating the scenario: the price in a week (whole "
            "dollars, the PDF's bounds $0-$150). The order is fixed, so the page-2 row "
            "narrates page 1 as asked, in words of OURS: 'You were asked \"What would you "
            "do?\"'."
        ),
    )


def study4() -> Experiment:
    scr, arms, lead, fq = two_by_three("study4")
    (pq,) = {s.question for s in scr[1::2]}
    return Experiment(
        name="study4",
        title="A tablet whose price fell or rose by $100 to $299, in the last week, three weeks "
        "ago, or week by week: buy now or later, and what will it cost in a week? (Study 4)",
        shared_context=lead,
        lead=lead,
        factors=["direction", "pattern"],
        arms=arms,
        outcomes=[
            Outcome("choice", "What would you do?", _choice_scale(scr[0::2])),
            Outcome("pred", fq, _price_scale(pq), recode=_identity(0, 500)),
        ],
        notes=(
            "Study 4 (pre-registered Mar 2021, AsPredicted #60510), 1,506 people, all kept. "
            "2 x 3 between people: the tablet was $399 (decrease) or $199 (increase) five "
            "weeks ago and is $299 now, having changed once in the last week (single late), "
            "once three weeks ago (single early), or every week (multiple). Buy now or later "
            "(1 now, 2 later) and the price in a week (whole dollars, the PDF's bounds "
            "$0-$500), on two pages in a random order the deposit does not record, each "
            "repeating the scenario; neither row narrates the other."
        ),
    )


def experiments() -> list[Experiment]:
    return [study1a(), study1b(), study2(), study3(), study4()]


def pdf_pairs(e: Experiment) -> dict[str, str]:
    """Each built data column and the PDF text of its screen (scenario and question)."""
    _, scr = screens(e.name)
    out = {}
    for col in built_pairs(e):
        if e.name == "study1b":
            (s,) = [x for x in scr if x.header.startswith(f"[{_FULL[col[:2]]} - page {col[2]}")]
        else:
            kind = next(q for q in QUESTION_START if q in label(e.name, col))
            s = ties(e.name, col, [x for x in scr if x.question.startswith(kind)])
        out[col] = f"{s.scenario} {strip_format_note(s.question)}"
    return out


def built_pairs(e: Experiment) -> dict[str, str]:
    """Each built data column and the words its rows carry (lead, scenario, question)."""
    out = {}
    if e.name == "study1b":
        by_code = {a.code: a for a in e.arms}
        for gi, g in enumerate(("DL", "DH", "IL", "IH")):
            for k in range(1, 5):
                arm = by_code[1 if k == 1 else 1 + gi * 3 + (k - 1)]
                out[f"{g}{k}"] = f"{e.lead} {arm.text} {e.outcomes[k - 1].question}"
        return out
    for a in e.arms:
        for var, col in a.columns.items():
            (o,) = [x for x in e.outcomes if x.var == var]
            item = a.items.get(var, {})
            body = item.get("condition_text", a.text).removesuffix(f" {ASKED}")
            q = item.get("outcome_question", o.question)
            out[col] = f"{e.lead} {body} {q}"
    return out


def check_labels() -> None:
    """Every built screen is its fielded label's words; the PDF differs only as recorded."""
    for e in experiments():
        found = {}
        pdf = pdf_pairs(e)
        for col, words in built_pairs(e).items():
            fieldw = _words(label(e.name, col))
            if col == TRUNCATED and e.name == "study1b":
                assert words == pdf[col] and _words(words)[: len(fieldw)] == fieldw
            else:
                assert _words(words) == fieldw, (e.name, col)
            if d := differences(pdf[col], label(e.name, col)):
                found[col] = d
        assert found == LABEL_DIFFERENCES[e.name], (e.name, found)


_FULL = {"DL": "Single decrease", "DH": "Multiple decreases"}
_FULL |= {"IL": "Single increase", "IH": "Multiple increases"}


# ---------------------------------------------------------------------------
# Coded data
# ---------------------------------------------------------------------------

AGE_RANGE = (18, 100)
N = {"study1a": 802, "study1b": 800, "study2": 802, "study3": 1506, "study4": 1506}


def data_file(tag: str) -> str:
    return f"{STUDY_ID}_{tag}.csv"


def deposit(tag: str) -> pd.DataFrame:
    df = sav(tag)[0].copy()
    assert len(df) == N[tag], (tag, len(df))
    df.insert(0, "row", range(1, len(df) + 1))
    return df


def _int(s: pd.Series) -> pd.Series:
    assert (s.dropna() == s.dropna().round()).all()
    return s.astype("Int64")


def prep(tag: str) -> pd.DataFrame:
    """One coded row per person: assignment column(s), answers, age, gender."""
    (e,) = [x for x in experiments() if x.name == tag]
    df = deposit(tag)
    meta = sav(tag)[1]
    out = pd.DataFrame({"pid": [f"{tag}_{r}" for r in df["row"]]})
    if tag == "study1b":
        groups = ["DL", "DH", "IL", "IH"]  # the PDF's arm order
        firsts = [f"{g}1" for g in groups]
        filled = df[firsts].notna()
        assert (filled.sum(axis=1) == 1).all()
        between = filled.values.argmax(axis=1)  # 0..3
        for k in range(1, 5):
            cols = [f"{g}{k}" for g in groups]
            shown = df[cols].notna()
            assert (shown.sum(axis=1) <= 1).all()
            # a day is shown only in the person's own arm, and only after "later"
            for gi, g in enumerate(groups):
                assert not (shown[f"{g}{k}"] & (between != gi)).any()
                if k > 1:
                    assert (shown[f"{g}{k}"] == (df[f"{g}{k - 1}"] == 2)).all(), (g, k)
            ans = df[cols].bfill(axis=1).iloc[:, 0]
            code = 1 if k == 1 else 1 + between * 3 + (k - 1)
            out[f"cond_day{k}"] = pd.Series(code, index=df.index).where(ans.notna()).astype("Int64")
            out[f"choice_day{k}"] = _int(ans)
    else:
        choice_cols = [a.columns["choice"] for a in e.arms]
        filled = df[choice_cols].notna()
        assert (filled.sum(axis=1) == 1).all(), tag
        arm = filled.values.argmax(axis=1)
        out["arm"] = [e.arms[i].code for i in arm]
        for var in e.arms[0].columns:
            cols = [a.columns[var] for a in e.arms]
            shown = df[cols].notna()
            # every answer sits in the person's own arm's column, and nowhere else
            for i, c in enumerate(cols):
                assert (shown[c] == (arm == i)).all(), (tag, c)
            out[var] = _int(df[cols].bfill(axis=1).iloc[:, 0]).values
    for o in e.outcomes:
        lo, hi = o.scale["min"], o.scale["max"]
        v = out[o.var].dropna()
        assert v.between(lo, hi).all(), (tag, o.var)
        if o.scale.get("min_label") and hi == 2:
            vl = meta.variable_value_labels[e.arms[-1].columns.get(o.var, "DL1")]
            assert norm(vl[1.0]) == o.scale["min_label"], (tag, vl)
            assert norm(vl[2.0]) == o.scale["max_label"], (tag, vl)
    age = pd.to_numeric(df["Age"], errors="coerce")
    out["age"] = age.where(age.between(*AGE_RANGE)).astype("Int64").values
    labels = {int(k): norm(v) for k, v in meta.variable_value_labels["Gender"].items()}
    out["gender"] = [labels[int(g)] if pd.notna(g) else None for g in df["Gender"]]
    return out


def check_codebook(tag: str) -> None:
    """The codebook's descriptions are the .sav's labels (the same export)."""
    book = pd.read_csv(CODEBOOK / f"Study {LABEL[tag]} - Data.sav___CODEBOOK.csv")
    for var, desc in zip(book["varname"], book["description"], strict=True):
        assert _words(norm(desc)) == _words(label(tag, var)), (tag, var)


# ---------------------------------------------------------------------------
# The recipes
# ---------------------------------------------------------------------------


def _describe(pdf: str, fielded: str) -> str:
    if not pdf:
        return f'the fielded screen has "{fielded}", which the PDF lacks'
    if not fielded:
        return f'the label stops before "{pdf}" (cut short in the export; the PDF used there)'
    return f'fielded "{fielded}", the PDF "{pdf}"'


def recipe(e: Experiment) -> dict[str, Any]:
    tasks = {o.var: t for t, o in enumerate(e.outcomes)}
    arms = []
    for i, a in enumerate(sorted(e.arms, key=lambda x: x.code)):
        arm: dict[str, Any] = {
            "raw_values": {e.source_var: a.code},
            "condition_num": i,
            "factors": a.factors,
            "text": a.text,
        }
        if a.items:
            arm["items"] = {tasks[v]: dict(sorted(it.items())) for v, it in a.items.items()}
        arms.append(arm)
    outcomes = []
    for t, o in enumerate(e.outcomes):
        out: dict[str, Any] = {"var": o.var, "task_num": t, "question": o.question}
        out["scale"] = o.scale
        if o.recode:
            out["response_recode"] = o.recode
        if o.condition_var:
            out["condition_var"] = o.condition_var
        outcomes.append(out)
    diffs = LABEL_DIFFERENCES[e.name]
    seen = sorted({d for ds in diffs.values() for d in ds})
    diff_note = "; ".join(_describe(a, b) for a, b in seen) or "none"
    notes = (
        f"{PAPER}\n\nGENERATED by scripts/gen_researchbox402.py; every judgement is in its "
        f"docstring. {e.notes}\n\nWording: every scenario and question is the fielded "
        "screen's, from the data file's variable labels (Qualtrics' export of each question), "
        "typos kept; the materials PDF (no .qsf) supplies the page structure and order, the "
        "answer options, the price bounds and any text no label carries"
        f"{' (the instructions, and day 3 of the single-decrease arm, whose label is cut short)' if e.name == 'study1b' else ''}"
        ". No picture on any built study's pages. Each data column is tied to its PDF screen "
        "by the dollar amounts in its label, exactly one match each. Where the PDF's words "
        f"differ from the fielded ones: {diff_note}. Typography normalised. The assignment "
        "is derived from which arm's "
        "columns are filled. Persona: age (years; outside 18-100 left blank) and gender, "
        "labels from the .sav's value labels."
    )
    top = max(o.scale["max"] for o in e.outcomes if not o.recode)
    rec: dict[str, Any] = {
        "study_id": STUDY_ID,
        "source": "researchbox",
        "experiment": e.name,
        "title": e.title,
        "data_file": data_file(e.name),
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": "pid",
        "notes": notes,
        "condition": {
            "source_vars": [e.source_var],
            "shared_context": e.shared_context,
            "factors": e.factors,
            "arms": arms,
        },
        "outcomes": outcomes,
        "response_recode": _identity(1, top),
        "missing_codes": [],
        "persona_map": {"age": "age", "gender": "gender"},
    }
    return rec


def recipe_path(e: Experiment) -> Path:
    return RECIPES / f"{STUDY_ID}_{e.name}.yaml"


def render(e: Experiment) -> str:
    return yaml.safe_dump(recipe(e), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prep", action="store_true", help="code the data")
    ap.add_argument("--check", action="store_true", help="exit 1 if any recipe differs")
    args = ap.parse_args()
    if args.prep:
        check_pictures()
        check_labels()
        for tag in LABEL:
            check_codebook(tag)
            path = RAW / data_file(tag)
            prep(tag).to_csv(path, index=False)
            print(f"wrote {path.relative_to(REPO)}")
        return 0
    bad = 0
    for e in experiments():
        path, text = recipe_path(e), render(e)
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
