#!/usr/bin/env python3
"""Write recipes/researchbox196_*.yaml: rating specific features (6 recipes).

Mehr KS, Simmons JP (2024), "How Does Rating Specific Features of an Experience Alter
Consumers' Overall Evaluations of That Experience?", Journal of Consumer Research
51(4):739-760, doi:10.1093/jcr/ucae005. ResearchBox 196 ("Rating Specific Features Alter
Overall Evaluations", https://researchbox.org/196), read from its Zenodo copy. CC BY 4.0
("All content posted to ResearchBox is under a CC By 4.0 License", the box page). US samples
(MTurk and Prolific), 2020-2022. The paper itself is paywalled and was not read; the answer
key is the authors' own R scripts, re-run on the deposit and on the built rows.

Every judgement is here, in code, so the recipes can be re-derived and reviewed.

THE DESIGN. People rate an experience overall, either alone or on a screen that also asks
them to rate its features (food, service, ...). The paper's claim is that rating the features
raises the overall rating of a subpar experience. The box holds 19 .qsf, 19 data files
(.csv, one header row, author-renamed columns), a codebook per data file, an R script per
study, AsPredicted pre-registrations and printouts (author-made PDFs with screenshots). The
folders' names start with a space (" Data/", " Materials/", ...), kept as found. Each .qsf
is matched to its data file by the box's Table of Contents (same "section"), and the match
is checked: every assignment value the data hold is one the .qsf's randomiser sets, and every
codebook attribute label is a row of the matching .qsf rating question (asserted).

WHAT IS BUILT. Six studies, every one a restaurant, flight, dentist, bookcase, sneakers,
food-delivery or call-centre experience rated in stars:
- study9 (Study 9): four domains (airplane, dentist, bookcase, sneakers), each with three or
  four scenarios; per domain the rating screen asked Overall only, Overall plus every
  attribute, Overall plus the scenario's positive attributes, or Overall plus its negative
  ones (randomised per domain). Only each person's FIRST domain is built (see ORDER), and
  not when that was the bookcase (main-session ruling, 19 Nov 2026, removing the riskiest
  part: the data's three bookcase columns tie to the .qsf's blocks bookcaseS1, S2 and S4 by
  position alone, and S2 and S4 share their rating rows, so the deposit cannot confirm which
  scenario text an answer belongs to; DROPPED_DOMAINS, count in the notes).
- study10 (Study 10): one of two subpar restaurant scenarios; Overall only, or Overall plus
  Food, Service, Ambiance and Value; then how likely to go again and to recommend (1-9).
- s3 (Study S3): your most recent food delivery; Overall alone or with five attributes.
- s4 (Study S4): your most recent call to a customer service centre; the same contrast.
- s5 (Study S5): one of two restaurant scenarios; Overall only, Overall with the attribute
  question below it, or the attribute question above it.
- s7 (Study S7): two of six restaurant scenarios each, in a recorded random order; Overall
  only, or Overall plus Food, Service, Ambiance and Value (between people).

NOT BUILT (NOT_BUILT), each with its reason:
- study3: people pick which of four experiences they have had (a restaurant with bad food and
  good service, ..., a ride share with a friendly but unsafe driver); that answer routes them
  to the restaurant or the ride-share questions and fixes the attribute rows they rate. The
  screens a person saw are therefore defined by their own answer, and a row would have to
  narrate it (rich, 19 Nov 2026: skip studies whose arms are defined by a person's own answer).
- study1, study2, study5, study6, study7, study8, s1 (image list): the fielded scenario
  ends "You know that OpenTable will ask you for one overall rating ..., like the one shown
  below:" over a screenshot of the rating question, so the picture shows the manipulation
  itself (one Overall row, or Overall plus attribute rows). rich's ruling (19 Nov 2026):
  a picture carrying the manipulation means skip; picture-heavy studies go to the image list.
- study4 and study4_pretest (image list): art galleries; the stimulus is the paintings
  (pictures), and Study 4 also shows a screenshot of the rating question.
- s2: the stimuli are animated films (videos, linked in a .docx, not in the deposit), and
  the instructions show a screenshot of the rating question.
- s6: a 2-minute animated movie (video), not in the deposit; the instructions show a
  screenshot of it.
- s7_pretest: a pretest of the S7 vignettes with no manipulation (attribute ratings only),
  no assignment column (which scenario a person saw is only which columns are filled), and
  its Airbnb scenario numbers tie to the .qsf's blocks by position alone.

PICTURES (rich, 19 Nov 2026). check_pictures counts every <img> in the QuestionText and
choices of every question the flow reaches (PICTURES), and separately every <img> anywhere
else in a payload. Studies 10, S7 and the S7 pretest carry <img> tags ONLY in
QuestionText_Unsafe, Qualtrics's stale copy of an earlier revision; the displayed
QuestionText has none, and Study 10's printout shows its scenario page with no picture. So
no BUILT study shows a respondent any picture. Studies 3, 9, S3, S4, S5 and S7 have no <img>
at all.

THE WORDING. Every scenario and question is the .qsf's, word-for-word, from blocks the survey
flow reaches; questions are found by QuestionID or within their block, because Study 10's
.qsf reuses the export tag Q5.3 (gender and "go again"). HTML is reduced to paragraphs;
emphasis dropped; typography normalised. Where the rating page repeated the scenario
(Studies 9, S5, S7, preceded in 9 and S5 by "Here is the scenario you read on the last/
previous page:", asserted word-for-word), the row states the scenario once. The printouts
for 9 and 10 say scenario and rating sat on one page; the fielded .qsf (which wins) puts a
page break in Study 9 and S7 and repeats the scenario, and in Study 10 shows both on one
page. Study 10's printout says the two follow-up questions were in a random order; the
fielded block has no randomisation (fixed: go again, then recommend). Neither is narrated.

THE MANIPULATION IN WORDS. The manipulation is which rows a star-rating question has, which
the instrument shows as a layout, not a sentence. Each arm therefore carries ONE sentence of
ours that names the rows, quoting each row's label word-for-word (the CONVENTIONS layout
exception, with the labels being the source's own):
    'Beneath the scenario was the rating question below, with one row of stars, labelled
     "Overall".'
    'Beneath the scenario was the rating question below, with a row of stars labelled
     "Overall" and, beneath it, rows labelled "Food", "Service", "Ambiance" and "Value".'
(S3 and S4 have no scenario: "The rating question below had ...".) Where the .qsf randomises
the attribute rows (Advanced randomisation, Overall fixed first, asserted), the sentence adds
"(these in a random order)"; the order is not recorded. S5's second question is quoted with
its own rows. S4's next page asks "Why were you calling ${q://QID117/ChoiceTextEntryValue}?",
piping the company the person typed. CONVENTIONS' per-respondent-fill clause ("here the
screen named the company you had given") would be false for the one kept person who typed
none (counted in the test), so that question is not narrated at all; S4's rows narrate only
the company question. Earlier screens are narrated as asked, never as given: "You were asked
"...", with ...". Every added sentence is in the recipe notes.

THE OUTCOME. The Overall row of the rating question: the question's own text, plus
'Report only the rating for "Overall".' (CONVENTIONS, one stem with several labelled fields:
the multiple arm's screen has several rows; the sentence names the source's own label).
Stars are discrete, 10 per row in 9, 10, S5 and S7 and 5 in S3 and S4 (StarCount asserted);
the answer is the number of stars. Study 10 adds its two 1-9 questions. The attribute ratings
(multiple arms only) are not built: the paper's dependent variable is Overall, and each
attribute is asked in one arm only.

ORDER. Study 9's four domains were shown in a random order that IS recorded (orderAirplane
.. orderSneakers, 1 = first). A row for a later domain would have to narrate every earlier
domain's scenario and rating screen (rich: recorded orders become factors and are rendered),
and with 60 domain screens that is close to one condition per person, so only position 1 is
built: 1 row per person, the first domain they saw, which nothing but the dropped intro
precedes. Not built: the rows for positions 2-4 (counted in the notes). S7's two scenarios
(two of six, random, recorded as orderS1 .. orderS6) are built at both positions: the second
row narrates the first scenario and its rating question as asked, then "You were then
shown:" and its own scenario (72 arms: 2 formats x (6 first + 30 ordered pairs)).

SURVEY MECHANICS DROPPED. Consent, IDs, instructions that describe the sequence ("In this
survey, you'll read and rate four scenarios"), the comprehension check that follows them
(authors' exclusion), page timers, demographics' lead-in. S3 and S4 keep their screening
screen's first sentence, which says what the survey is about; the eligibility question and
its answer (a date) are not narrated.

EXCLUSIONS. The authors' R scripts, applied as written (R's NA semantics: a NA in any test
excludes, since `which(deletes == 0)` drops NA): no Overall rating, duplicate IP, duplicate ID,
and where the script tests them a wrong comprehension answer (9 and 10: attnCheck != 1; S5:
!= 2) and an unapproved ID (9: unapprovedID == 1; 10 and S5: approvedID == 0; S3, S4:
unapprovedID == 1). S7 excludes per row (no rating, duplicate IP or ID).

THE ASSIGNMENT. From the randomiser's embedded fields, as exported (condition, scenario,
<domain>Condition), checked against the .qsf's values; the scenario a Study 9 person saw in
a domain is the one Overall column that is filled, asserted unique and consistent with the
domain's condition. Jev: scripts/recipe_prep.py reads .sav/.dta/.por only; this box is .csv,
and running it (19 Nov 2026, --source dataverse) exits "no .sav/.dta", so it does not apply.
The codebooks name the assignment columns.

PERSONA. Age (years, as exported; asserted 18-105) and gender (the .qsf's own labels: Man,
Woman, Other; S3: Male, Female, Other).

ANSWER KEY. tests/test_gen_researchbox196.py re-runs each R script's preregistered test on the
deposit (its exclusions, its variables) and on the BUILT rows, and asserts they agree: cell
means, N, and the pooled-variance t (10, S3, S4, S7 per scenario), S5's regressions as cell
means, Study 9's position-1 cell means against the deposit.

    uv run python scripts/gen_researchbox196.py --prep   # code the data
    uv run python scripts/gen_researchbox196.py          # write the recipes
    uv run python scripts/gen_researchbox196.py --check  # exit 1 if any recipe differs
"""

from __future__ import annotations

import argparse
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
STUDY_ID = "researchbox196"
RAW = REPO / "data" / "raw" / STUDY_ID
MATERIALS = RAW / " Materials"
DATA = RAW / " Data"
CODEBOOK = RAW / " Codebook"
RECIPES = REPO / "recipes"
LICENCE = (
    'CC BY 4.0, stated on the box page https://researchbox.org/196 ("All content posted '
    'to ResearchBox is under a CC By 4.0 License"); read from its Zenodo copy. Read 19 Nov '
    "2026."
)
PAPER = (
    'Mehr KS, Simmons JP (2024), "How Does Rating Specific Features of an Experience Alter '
    "Consumers' Overall Evaluations of That Experience?\", Journal of Consumer Research "
    "51(4):739-760, doi:10.1093/jcr/ucae005. ResearchBox 196 (https://researchbox.org/196)."
)

# tag -> (.qsf, data file, the paper's name for it, pre-registration)
SOURCES = {
    "study9": ("Study 9.(file id 68).qsf", "Study 9.csv", "Study 9", "AsPredicted #63813"),
    "study10": (
        "Study 10.(file id 194).qsf",
        "Study 10.(file id 196).csv",
        "Study 10",
        "AsPredicted #85954",
    ),
    "s3": (
        "Study S3.(file id 73).qsf",
        "Study S3.(file id 96).csv",
        "Study S3",
        "AsPredicted #53649",
    ),
    "s4": ("Study S4.qsf", "Study S4.csv", "Study S4", "AsPredicted #54357"),
    "s5": ("Study S5.qsf", "Study S5.csv", "Study S5", "AsPredicted #107579"),
    "s7": (
        "Study S7.(file id 119).qsf",
        "Study S7.(file id 117).csv",
        "Study S7",
        "AsPredicted #76255",
    ),
}

IMAGE_LIST = (
    "study1",
    "study2",
    "study4",
    "study4_pretest",
    "study5",
    "study6",
    "study7",
    "study8",
    "s1",
)
SCREENSHOT = (
    "the fielded scenario ends with a screenshot of the rating question (one Overall row, or "
    "Overall plus attribute rows), so the picture shows the manipulation itself; image list"
)
NOT_BUILT = {
    "study1": SCREENSHOT,
    "study2": SCREENSHOT,
    "study3": (
        "the person's own answer (which of four past experiences they had) routes them to the "
        "restaurant or ride-share questions and fixes the rows they rate; a row would have to "
        "narrate that answer"
    ),
    "study4": "art galleries: the stimulus is paintings (pictures), plus a screenshot of the rating question; image list",
    "study4_pretest": "ratings of paintings shown as pictures; image list",
    "study5": SCREENSHOT,
    "study6": SCREENSHOT,
    "study7": SCREENSHOT,
    "study8": SCREENSHOT,
    "s1": SCREENSHOT,
    "s2": "the stimuli are animated films (videos), not in the deposit",
    "s6": "the stimulus is an animated movie (video), not in the deposit",
    "s7_pretest": (
        "a pretest of the S7 vignettes with no manipulation and no assignment column; its "
        "Airbnb scenario numbers tie to the .qsf's blocks by position alone"
    ),
}

# every <img> in the displayed QuestionText or choices of a reachable question, and every
# <img> elsewhere in a reachable question's payload (QuestionText_Unsafe, a stale copy)
PICTURES = {
    "Study 1.qsf": (8, 5),
    "Study 2.qsf": (12, 9),
    "Study 3.qsf": (0, 0),
    "Study 4 - pretest.qsf": (50, 30),
    "Study 4.qsf": (7, 0),
    "Study 5.qsf": (18, 15),
    "Study 6.(file id 76).qsf": (18, 15),
    "Study 7.(file id 77).qsf": (18, 15),
    "Study 8.(file id 75).qsf": (8, 6),
    "Study 9.(file id 68).qsf": (0, 0),
    "Study 10.(file id 194).qsf": (0, 2),
    "Study S1.(file id 79).qsf": (18, 15),
    "Study S2.(file id 74).qsf": (2, 2),
    "Study S3.(file id 73).qsf": (0, 0),
    "Study S4.qsf": (0, 0),
    "Study S5.qsf": (0, 0),
    "Study S6.qsf": (1, 1),
    "Study S7 - qsf for pretest.qsf": (0, 2),
    "Study S7.(file id 119).qsf": (0, 0),
}

OVERALL_ONLY = 'Report only the rating for "Overall".'

# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

_TYPO = {"\xa0": " ", "\u200b": "", "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"'}


def _clean(s: str) -> str:
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    for a, b in _TYPO.items():
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def norm(raw: str) -> str:
    """HTML to one line of plain text. Typography only."""
    return _clean(re.sub(r"<br\s*/?>|</p>|</div>", " ", raw or ""))


def paragraphs(raw: str) -> str:
    """HTML to paragraphs, blank-line separated, empty ones dropped."""
    parts = re.split(r"<br\s*/?>|</p>|</div>|<div>|<p>", raw or "")
    return "\n\n".join(c for c in (_clean(p) for p in parts) if c)


def quoted(labels: list[str]) -> str:
    q = [f'"{x}"' for x in labels]
    return q[0] if len(q) == 1 else ", ".join(q[:-1]) + " and " + q[-1]


# ---------------------------------------------------------------------------
# The questionnaires
# ---------------------------------------------------------------------------


class Survey:
    def __init__(self, path: Path) -> None:
        els = json.loads(path.read_text())["SurveyElements"]
        self.by_qid: dict[str, dict[str, Any]] = {
            e["Payload"]["QuestionID"]: e["Payload"] for e in els if e["Element"] == "SQ"
        }
        self.blocks: dict[str, dict[str, Any]] = {}
        for e in els:
            if e["Element"] == "BL":
                p = e["Payload"]
                for b in p.values() if isinstance(p, dict) else p:
                    self.blocks[b["ID"]] = b
        self.flow: dict[str, Any] = next(e for e in els if e["Element"] == "FL")["Payload"]
        self.flow_blocks: list[str] = []
        self.randomizers: list[dict[str, Any]] = []

        def walk(n: dict[str, Any]) -> None:
            if n.get("Type") in ("Block", "Standard"):
                self.flow_blocks.append(n["ID"])
            if n.get("Type") == "BlockRandomizer":
                self.randomizers.append(n)
            for c in n.get("Flow", []):
                walk(c)

        walk(self.flow)
        assert all(self.blocks[b]["Type"] != "Trash" for b in self.flow_blocks)

    def reachable(self) -> set[str]:
        return {
            x["QuestionID"]
            for b in self.flow_blocks
            for x in self.blocks[b].get("BlockElements", [])
            if x["Type"] == "Question"
        }

    def block_named(self, name: str) -> str:
        (b,) = [b for b in self.flow_blocks if self.blocks[b]["Description"].strip() == name]
        return b

    def block_qs(self, name: str) -> list[dict[str, Any]]:
        """A block's questions in order, page timers dropped."""
        out = []
        for x in self.blocks[self.block_named(name)]["BlockElements"]:
            if x["Type"] == "Question":
                q = self.by_qid[x["QuestionID"]]
                if q["QuestionType"] != "Timing":
                    out.append(q)
        return out

    def q(self, block: str, tag: str) -> dict[str, Any]:
        (q,) = [q for q in self.block_qs(block) if q["DataExportTag"] == tag]
        return q

    def embedded_values(self, field_name: str) -> list[str]:
        """Every value the flow assigns to an embedded field, in flow order."""
        out: list[str] = []

        def walk(n: dict[str, Any]) -> None:
            if n.get("Type") == "EmbeddedData":
                for x in n["EmbeddedData"]:
                    if x["Field"] == field_name:
                        out.append(str(x.get("Value")))
            for c in n.get("Flow", []):
                walk(c)

        walk(self.flow)
        return out


@cache
def survey(tag: str) -> Survey:
    return Survey(MATERIALS / SOURCES[tag][0])


def display_value(q: dict[str, Any]) -> tuple[str, str]:
    """(embedded field, value) of a question's one-condition display logic."""
    (d,) = [v for k, v in q["DisplayLogic"]["0"].items() if k != "Type"]
    assert d["LogicType"] == "EmbeddedField" and d["Operator"] == "EqualTo", d
    return d["LeftOperand"], str(d["RightOperand"]).strip()


@dataclass
class Rating:
    """A star-rating question: its text, row labels, stars, and whether rows 2.. are shuffled."""

    text: str
    rows: list[str]
    stars: int
    random_rest: bool


def rating(q: dict[str, Any]) -> Rating:
    assert q["QuestionType"] == "Slider" and q["Selector"] == "STAR", q["DataExportTag"]
    c = q["Configuration"]
    assert c["StarType"] == "discrete", c
    order = [str(k) for k in q["ChoiceOrder"]]
    rows = [norm(q["Choices"][k]["Display"]) for k in order]
    r = q.get("Randomization") or {}
    rand = False
    if r.get("Type") == "Advanced":
        adv = r["Advanced"]
        assert adv["FixedOrder"][0] == order[0], adv  # Overall stays first
        assert sorted(adv["RandomizeAll"]) == sorted(order[1:]), adv
        assert not adv["RandomSubSet"] and not adv.get("Undisplayed"), adv
        rand = len(order) > 2
    else:
        assert r.get("Type") in (None, "None"), r
    return Rating(norm(q["QuestionText"]), rows, int(c["StarCount"]), rand)


def rows_desc(r: Rating) -> str:
    """The rows of a rating question, in words of ours around the source's labels."""
    assert r.rows[0] == "Overall", r.rows
    if len(r.rows) == 1:
        return 'one row of stars, labelled "Overall"'
    rest = r.rows[1:]
    noun = "a row" if len(rest) == 1 else "rows"
    tail = " (these in a random order)" if r.random_rest else ""
    return (
        f'a row of stars labelled "Overall" and, beneath it, {noun} labelled {quoted(rest)}{tail}'
    )


def below_scenario(r: Rating) -> str:
    return f"Beneath the scenario was the rating question below, with {rows_desc(r)}."


def asked(r: Rating) -> str:
    return f'You were asked "{r.text}", with {rows_desc(r)}.'


def star_scale(r: Rating) -> dict[str, Any]:
    return {"min": 1, "max": r.stars}


def overall_question(r: Rating) -> str:
    return f"{r.text} {OVERALL_ONLY}"


def gender_labels(q: dict[str, Any]) -> dict[int, str]:
    assert not q.get("RecodeValues")
    return {int(k): norm(v["Display"]) for k, v in q["Choices"].items()}


def demographics(tag: str) -> dict[int, str]:
    sv = survey(tag)
    (g,) = [
        q for q in sv.block_qs("demographics") if norm(q["QuestionText"]) == "What is your gender?"
    ]
    return gender_labels(g)


def check_pictures() -> None:
    """Every <img> in every .qsf's reachable questions, displayed text vs stale copies."""
    for name, (shown, stale) in PICTURES.items():
        sv = Survey(MATERIALS / name)
        reach = sv.reachable()
        got = [0, 0]
        for qid, q in sv.by_qid.items():
            if qid not in reach:
                continue
            n_shown = len(
                re.findall(
                    "<img",
                    q.get("QuestionText", "")
                    + json.dumps(q.get("Choices", {}))
                    + json.dumps(q.get("Answers", {})),
                )
            )
            got[0] += n_shown
            got[1] += len(re.findall("<img", json.dumps(q))) - n_shown
        assert tuple(got) == (shown, stale), (name, got)
    built = {SOURCES[t][0] for t in SOURCES}
    assert all(PICTURES[f][0] == 0 for f in built)
    assert set(PICTURES) == {p.name for p in MATERIALS.glob("*.qsf")}


# ---------------------------------------------------------------------------
# The experiments
# ---------------------------------------------------------------------------


@dataclass
class Arm:
    raw: dict[str, int]
    factors: dict[str, str]
    text: str
    items: dict[int, dict[str, Any]] = field(default_factory=dict)


@dataclass
class Outcome:
    var: str
    question: str
    scale: dict[str, Any]
    condition_var: str | None = None


@dataclass
class Experiment:
    name: str
    title: str
    kind: str
    factors: list[str]
    source_vars: list[str]
    shared: str
    arms: list[Arm]
    outcomes: list[Outcome]
    notes: str
    added: list[str]


# Study 9 -------------------------------------------------------------------

DOMAINS = {  # data prefix -> (domain name, block prefix, data scenario -> block suffix)
    "air": ("airplane", "airplane", {1: 1, 2: 2, 3: 3, 4: 4}),
    "den": ("dentist", "dentist", {1: 1, 2: 2, 3: 3, 4: 4}),
    "boo": ("bookcase", "bookcase", {1: 1, 2: 2, 3: 4}),
    "sne": ("sneakers", "sneakers", {1: 1, 2: 2, 3: 3, 4: 4}),
}
FORMATS = {  # embedded value -> (data letter, factor level)
    "single": ("S", "overall_only"),
    "multiple": ("M", "all_attributes"),
    "positive": ("P", "positive_attributes"),
    "negative": ("N", "negative_attributes"),
}
LAST_PAGE = "Here is the scenario you read on the last page:"

# Dropped by main-session ruling (rich's standing rule: remove the riskiest part, 19 Nov
# 2026): every row whose first domain is the bookcase. The data's booS1..booS3 are tied to
# the .qsf's blocks bookcaseS1, S2, S4 by position alone, and S2 and S4 have the same rating
# rows, so the deposit cannot confirm which column is which block, i.e. which scenario text
# a row's answer belongs to. The codebook check still covers the bookcase cells.
DROPPED_DOMAINS = {"boo"}


def study9_cells(all_domains: bool = False) -> list[tuple[str, int, str, str, Rating]]:
    """(data prefix, data scenario, format, scenario text, rating) in a fixed order."""
    sv = survey("study9")
    out = []
    for pre, (dom, blk, scen) in DOMAINS.items():
        if pre in DROPPED_DOMAINS and not all_domains:
            continue
        assert sv.embedded_values(f"{dom}Condition") == list(FORMATS)
        # the scenario blocks, in the randomiser's order, are the data's S1, S2, ...
        (r,) = [
            r
            for r in sv.randomizers
            if int(r["SubSet"]) == 1
            and all(n["Type"] in ("Block", "Standard") for n in r["Flow"])
            and sv.blocks[r["Flow"][0]["ID"]]["Description"].startswith(blk)
        ]
        names = [sv.blocks[n["ID"]]["Description"].strip() for n in r["Flow"]]
        assert names == [f"{blk}S{b}" for b in scen.values()], names
        for s, b in scen.items():
            qs = sv.block_qs(f"{blk}S{b}")
            assert [q["QuestionType"] for q in qs] == ["DB", "DB"] + ["Slider"] * 4
            text = paragraphs(qs[0]["QuestionText"])
            assert norm(qs[1]["QuestionText"]) == f"{LAST_PAGE} {norm(qs[0]['QuestionText'])}"
            by_fmt = {}
            for q in qs[2:]:
                fld, val = display_value(q)
                assert fld == f"{dom}Condition", fld
                by_fmt[val] = rating(q)
            assert set(by_fmt) == set(FORMATS)
            for f in FORMATS:
                rt = by_fmt[f]
                assert rt.text == "What rating would you provide?" and rt.stars == 10
                assert (len(rt.rows) == 1) == (f == "single")
                out.append((pre, s, f, text, rt))
    return out


def study9_check_codebook() -> None:
    """The codebook's attribute labels are the .qsf rating question's rows, cell by cell."""
    book = pd.read_csv(CODEBOOK / f"{SOURCES['study9'][1]}___CODEBOOK.csv")
    desc = dict(zip(book["varname"], book["description"], strict=True))
    for pre, s, f, _, rt in study9_cells(all_domains=True):
        letter = FORMATS[f][0]
        got = []
        for k in range(1, 5):
            d = desc.get(f"{pre}S{s}{letter}At{k}")
            if d is not None:
                m = re.search(r"condition (.+) rating$", d)
                assert m, d
                got.append(m.group(1).strip().lower())
        assert got == [x.lower() for x in rt.rows[1:]], (pre, s, f, got, rt.rows)


def study9() -> Experiment:
    arms = []
    for code, (pre, s, f, text, rt) in enumerate(study9_cells(), 1):
        dom = DOMAINS[pre][0]
        arms.append(
            Arm(
                {"arm": code},
                {"scenario": f"{dom}_{s}", "rating_rows": FORMATS[f][1]},
                f"{text}\n\n{below_scenario(rt)}",
            )
        )
    q = "What rating would you provide?"
    return Experiment(
        name="study9",
        title="A flight, a dentist visit or sneakers gone partly wrong, rated "
        "Overall alone or beside all, the good or the bad features (Study 9)",
        kind="mix",
        factors=["scenario", "rating_rows"],
        source_vars=["arm"],
        shared="",
        arms=arms,
        outcomes=[Outcome("overall", f"{q} {OVERALL_ONLY}", {"min": 1, "max": 10})],
        notes=(
            "Four domains (airplane, dentist, bookcase, sneakers), each person rating one "
            "scenario per domain (randomised among the domain's 4, or 3 for bookcase), on a "
            "rating screen "
            "randomised per domain: Overall only, Overall plus every attribute, plus the "
            "scenario's positive attributes, or plus its negative ones (the .qsf's display "
            "logic; the codebook's attribute labels agree, asserted). The rating page "
            "repeated the scenario after 'Here is the scenario you read on the last page:'; "
            "the row states it once. The domains came in a random order that is recorded; "
            "only each person's FIRST domain is built, because a later domain's row would "
            f"have to narrate every earlier one. Not built: {study9_later():,} later-domain "
            "ratings of kept people. Also not built (main-session ruling, the riskiest part "
            f"removed): the {study9_bookcase_first():,} people whose first domain was the "
            "bookcase, because the data's three bookcase columns tie to the .qsf's blocks "
            "bookcaseS1, S2 and S4 by position alone and S2 and S4 have the same rating rows, "
            "so the deposit cannot confirm which scenario text an answer belongs to. Built: the "
            "airplane, dentist and sneakers domains. 10 stars, the answer the number chosen."
        ),
        added=[below_scenario(rt) for *_, rt in study9_cells()],
    )


# Study 10 ------------------------------------------------------------------


def study10() -> Experiment:
    sv = survey("study10")
    assert sv.embedded_values("condition") == ["single", "multiple"]
    assert sv.embedded_values("scenario") == ["1", "2", "1", "2"]
    one, many = sv.block_qs("3StarS1One"), sv.block_qs("3StarS1Multiple")
    assert [q["QuestionType"] for q in one] == ["DB", "DB", "Slider"]
    assert [q["QuestionType"] for q in many] == ["DB", "DB", "Slider"]
    scen = {}
    for k in (0, 1):
        assert display_value(one[k]) == ("scenario", str(k + 1))
        assert display_value(many[k]) == ("scenario", str(k + 1))
        assert norm(one[k]["QuestionText"]) == norm(many[k]["QuestionText"])
        scen[k + 1] = paragraphs(one[k]["QuestionText"])
    rts = {"single": rating(one[2]), "multiple": rating(many[2])}
    assert rts["single"].rows == ["Overall"]
    assert rts["multiple"].rows == ["Overall", "Food", "Service", "Ambiance", "Value"]
    assert not rts["multiple"].random_rest
    for r in rts.values():
        assert r.text == "How would you rate this restaurant?" and r.stars == 10
    pref = sv.block_qs("prefQs")
    assert [q["QuestionType"] for q in pref] == ["DB", "DB", "MC", "MC"]
    for k in (0, 1):
        assert norm(pref[k]["QuestionText"]) == (
            "On the previous page, you read the following scenario: " + norm(one[k]["QuestionText"])
        )
    go, rec = pref[2], pref[3]
    assert norm(go["QuestionText"]) == "How likely would you be to go to this restaurant again?"
    assert norm(rec["QuestionText"]).startswith("How likely would you be to recommend a friend")
    level = {"single": "overall_only", "multiple": "overall_and_attributes"}
    arms = []
    for code, (f, s) in enumerate([(f, s) for f in rts for s in (1, 2)], 1):
        rt = rts[f]
        narr = f"{scen[s]}\n\n{asked(rt)}"
        arms.append(
            Arm(
                {"arm": code},
                {"scenario": str(s), "rating_rows": level[f]},
                f"{scen[s]}\n\n{below_scenario(rt)}",
                {1: {"condition_text": narr}, 2: {"condition_text": narr}},
            )
        )
    outcomes = [
        Outcome("overall", overall_question(rts["single"]), star_scale(rts["single"])),
        Outcome("go_again", norm(go["QuestionText"]), nine_point(go)),
        Outcome("recommend", norm(rec["QuestionText"]), nine_point(rec)),
    ]
    return Experiment(
        name="study10",
        title="A subpar restaurant rated Overall alone or beside Food, Service, Ambiance and "
        "Value; then go again, recommend (Study 10)",
        kind="mix",
        factors=["scenario", "rating_rows"],
        source_vars=["arm"],
        shared="",
        arms=arms,
        outcomes=outcomes,
        notes=(
            "One of two subpar restaurant scenarios (undercooked food; cold food the waiter "
            "will not take back) x the rating question's rows (Overall only, or Overall, "
            "Food, Service, Ambiance and Value in that fixed order), between people; "
            "scenario and rating on one page. Next page: the scenario again ('On the previous "
            "page, you read the following scenario:', not repeated in the row) and how likely "
            "you would be to go again and to recommend a friend (1-9, end labels only). "
            "Those rows narrate the rating question as asked. 10 stars."
        ),
        added=[
            below_scenario(rts["single"]),
            below_scenario(rts["multiple"]),
            asked(rts["single"]),
            asked(rts["multiple"]),
        ],
    )


def nine_point(q: dict[str, Any]) -> dict[str, Any]:
    assert q["QuestionType"] == "MC" and q["Selector"] == "SAHR" and not q.get("Randomization")
    order = [str(k) for k in q["ChoiceOrder"]]
    assert [int(q["RecodeValues"].get(k, k)) for k in order] == list(range(1, 10))
    labs = [norm(q["Choices"][k]["Display"]) for k in order]
    assert labs[1:-1] == [str(i) for i in range(2, 9)], labs
    lo, hi = labs[0], labs[-1]
    assert lo.startswith("1 ") and hi.startswith("9 "), (lo, hi)
    return {"min": 1, "max": 9, "min_label": lo[2:], "max_label": hi[2:]}


# S3 and S4 -----------------------------------------------------------------


def recall(tag: str) -> Experiment:
    sv = survey(tag)
    assert sv.embedded_values("condition") == ["single", "multiple"]
    (screen,) = [q for q in sv.block_qs("screening") if q["QuestionType"] == "MC"]
    first = norm(screen["QuestionText"]).split(" In order to participate")[0]
    assert first.startswith("In this survey, you'll answer some questions about a "), first
    info = sv.block_qs("infoAboutDelivery" if tag == "s3" else "infoAboutExperience")
    dv = sv.block_qs("DV")
    assert [display_value(q) for q in dv] == [("condition", "single"), ("condition", "multiple")]
    rts = {"single": rating(dv[0]), "multiple": rating(dv[1])}
    for r in rts.values():
        assert r.stars == 5 and not r.random_rest
    assert rts["single"].rows == ["Overall"] and len(rts["multiple"].rows) > 2
    assert rts["single"].text == rts["multiple"].text
    if tag == "s3":
        qtexts = [norm(q["QuestionText"]) for q in info]
        assert len(qtexts) == 3
        lead = (
            "You were asked " + ", ".join(f'"{t}"' for t in qtexts[:-1]) + f' and "{qtexts[-1]}".'
        )
    else:
        a, b = (norm(q["QuestionText"]) for q in info)
        assert b == "Why were you calling ${q://QID117/ChoiceTextEntryValue}?", b
        assert info[0]["QuestionID"] == "QID117"
        lead = f'You were asked "{a}".'  # the piped "Why were you calling ..." is not narrated
    shared = f"{first}\n\n{lead}"
    level = {"single": "overall_only", "multiple": "overall_and_attributes"}

    def says(r: Rating) -> str:
        return f"The rating question below had {rows_desc(r)}."

    arms = [
        Arm({"condition": i + 1}, {"rating_rows": level[f]}, says(rts[f]))
        for i, f in enumerate(rts)
    ]
    what = "food delivery" if tag == "s3" else "call to a customer service centre"
    return Experiment(
        name=tag,
        title=f"Your most recent {what}, rated Overall alone or beside "
        f"{'five' if tag == 's3' else 'four'} of its features (Study {tag.upper()})",
        kind="version",
        factors=["rating_rows"],
        source_vars=["condition"],
        shared=shared,
        arms=arms,
        outcomes=[Outcome("overall", overall_question(rts["single"]), star_scale(rts["single"]))],
        notes=(
            "A real, recent experience of the respondent's own (eligibility screened; the "
            "screen's first sentence kept, its question and the date answered not narrated), "
            "a few questions about it (narrated as asked), then the rating question with "
            "Overall only or Overall plus the attribute rows, in the .qsf's fixed order, "
            "between people. 5 stars."
            + (
                " Not narrated: the next page's 'Why were you calling ${q://QID117/"
                "ChoiceTextEntryValue}?', which pipes the company the person typed (one kept "
                "person typed none, so no fill clause would be true of every row)."
                if tag == "s4"
                else ""
            )
        ),
        added=["You were asked", says(rts["single"]), says(rts["multiple"])],
    )


# S5 ------------------------------------------------------------------------

PREVIOUS_PAGE = "Here is the scenario you read on the previous page:"


def s5() -> Experiment:
    sv = survey("s5")
    assert sv.embedded_values("scenario") == ["1", "2"]
    assert sv.embedded_values("condition") == [
        "overallOnly",
        "overallAttributes",
        "attributesOverall",
    ]
    sc = sv.block_qs("scenarios")
    assert [display_value(q) for q in sc] == [("scenario", "1"), ("scenario", "2")]
    scen = {k + 1: paragraphs(sc[k]["QuestionText"]) for k in (0, 1)}
    layouts = {}
    for blk, cond in (
        ("overallOnly", "overall_only"),
        ("overallThenAttributes", "overall_then_attributes"),
        ("attributesThenOverall", "attributes_then_overall"),
    ):
        qs = sv.block_qs(blk)
        for k in (0, 1):
            assert display_value(qs[k]) == ("scenario", str(k + 1))
            assert norm(qs[k]["QuestionText"]) == f"{PREVIOUS_PAGE} {norm(sc[k]['QuestionText'])}"
        layouts[cond] = [rating(q) for q in qs[2:]]
    overall = layouts["overall_only"][0]
    assert overall.rows == ["Overall"] and overall.stars == 10
    assert overall.text == "How would you rate the overall experience at the restaurant?"
    o2, a2 = layouts["overall_then_attributes"]
    a3, o3 = layouts["attributes_then_overall"]
    assert o2 == overall == o3 and a2 == a3
    assert a2.rows == ["Food", "Service", "Ambiance", "Value"] and not a2.random_rest
    attr = f'"{a2.text}", with rows of stars labelled {quoted(a2.rows)}'
    clause = {
        "overall_only": "Beneath the scenario was the question below, alone, with one row of "
        'stars, labelled "Overall".',
        "overall_then_attributes": "Beneath the scenario was the question below, with one row "
        f'of stars, labelled "Overall", and beneath that a second question, {attr}.',
        "attributes_then_overall": f"Beneath the scenario was first a question, {attr}, and "
        'beneath that the question below, with one row of stars, labelled "Overall".',
    }
    arms = []
    for code, (c, s) in enumerate([(c, s) for c in clause for s in (1, 2)], 1):
        arms.append(
            Arm(
                {"arm": code}, {"scenario": str(s), "rating_layout": c}, f"{scen[s]}\n\n{clause[c]}"
            )
        )
    return Experiment(
        name="s5",
        title="A subpar restaurant rated Overall alone, Overall then its features on the same "
        "screen, or its features then Overall (Study S5)",
        kind="mix",
        factors=["scenario", "rating_layout"],
        source_vars=["arm"],
        shared="",
        arms=arms,
        outcomes=[Outcome("overall", overall_question(overall), star_scale(overall))],
        notes=(
            "One of two subpar restaurant scenarios x three layouts of the next page, "
            "between people: the Overall question alone; the Overall question with the "
            "attribute question (Food, Service, Ambiance, Value, fixed order) below it; or "
            "the attribute question above it. The page repeated the scenario after 'Here is "
            "the scenario you read on the previous page:'; the row states it once. 10 stars."
        ),
        added=list(clause.values()),
    )


# S7 ------------------------------------------------------------------------


def s7_parts() -> tuple[dict[int, str], dict[str, Rating]]:
    sv = survey("s7")
    assert sv.embedded_values("condition") == ["single", "multiple"]
    scen: dict[int, str] = {}
    rts: dict[str, Rating] = {}
    for f, suffix in (("single", "Single"), ("multiple", "Multiple")):
        for s in range(1, 7):
            blk = f"s{s}{suffix}" if not (s == 6 and f == "multiple") else "s6multiple"
            qs = sv.block_qs(blk)
            assert [q["QuestionType"] for q in qs] == ["DB", "DB", "Slider"], blk
            assert norm(qs[0]["QuestionText"]) == norm(qs[1]["QuestionText"])
            text = paragraphs(qs[0]["QuestionText"])
            assert scen.setdefault(s, text) == text
            rt = rating(qs[2])
            assert rts.setdefault(f, rt) == rt
    assert rts["single"].rows == ["Overall"]
    assert rts["multiple"].rows == ["Overall", "Food", "Service", "Ambiance", "Value"]
    assert not rts["multiple"].random_rest and rts["single"].stars == 10
    assert rts["single"].text == "What rating would you provide?"
    return scen, rts


S7_LEVEL = {"single": "overall_only", "multiple": "overall_and_attributes"}


def s7_code(f: str, first: int, second: int | None) -> int:
    """Arm code: 1-12 a first scenario; 13-72 a second scenario after a first."""
    fi = list(S7_LEVEL).index(f)
    if second is None:
        return fi * 6 + first
    pairs = [(a, b) for a in range(1, 7) for b in range(1, 7) if a != b]
    return 12 + fi * 30 + pairs.index((first, second)) + 1


def s7() -> Experiment:
    scen, rts = s7_parts()
    arms = []
    for f in S7_LEVEL:
        for s in range(1, 7):
            arms.append(
                Arm(
                    {"arm_1": s7_code(f, s, None)},
                    {"scenario": str(s), "rating_rows": S7_LEVEL[f], "earlier_scenario": "none"},
                    f"{scen[s]}\n\n{below_scenario(rts[f])}",
                )
            )
    for f in S7_LEVEL:
        for a in range(1, 7):
            for b in range(1, 7):
                if a == b:
                    continue
                text = (
                    f"{scen[a]}\n\n{asked(rts[f])}\n\nYou were then shown:\n\n{scen[b]}\n\n"
                    f"{below_scenario(rts[f])}"
                )
                arms.append(
                    Arm(
                        {"arm_1": s7_code(f, a, b)},
                        {
                            "scenario": str(b),
                            "rating_rows": S7_LEVEL[f],
                            "earlier_scenario": str(a),
                        },
                        text,
                    )
                )
    assert [a.raw["arm_1"] for a in arms] == list(range(1, 73))
    q = overall_question(rts["single"])
    return Experiment(
        name="s7",
        title="Two of six restaurant visits, each rated Overall alone or beside Food, "
        "Service, Ambiance and Value (Study S7)",
        kind="mix",
        factors=["scenario", "rating_rows", "earlier_scenario"],
        source_vars=["arm_1"],
        shared="",
        arms=arms,
        outcomes=[
            Outcome("rating_1", q, star_scale(rts["single"]), "arm_1"),
            Outcome("rating_2", q, star_scale(rts["single"]), "arm_2"),
        ],
        notes=(
            "Rating rows (Overall only, or Overall, Food, Service, Ambiance and Value in that "
            "fixed order) between people; two of six restaurant scenarios each, in a random "
            "order that IS recorded (orderS1 .. orderS6). Each scenario page was followed by "
            "a page repeating it word-for-word with the rating question; the row states it "
            "once. Task 0 is the scenario seen first (arm_1), task 1 the one seen second "
            "(arm_2), whose condition narrates the first scenario and its rating question as "
            "asked, then 'You were then shown:' (ours) and its own scenario. 10 stars."
        ),
        added=[
            below_scenario(rts["single"]),
            below_scenario(rts["multiple"]),
            asked(rts["single"]),
            asked(rts["multiple"]),
            "You were then shown:",
        ],
    )


def experiments() -> list[Experiment]:
    return [study9(), study10(), recall("s3"), recall("s4"), s5(), s7()]


def experiment(tag: str) -> Experiment:
    (e,) = [x for x in experiments() if x.name == tag]
    return e


# ---------------------------------------------------------------------------
# Coded data
# ---------------------------------------------------------------------------


def data_file(tag: str) -> str:
    return f"{STUDY_ID}_{tag}.csv"


def read_deposit(tag: str) -> pd.DataFrame:
    return pd.read_csv(DATA / SOURCES[tag][1])


def is1(s: pd.Series) -> pd.Series:
    """R's `x == 1` inside `which(deletes == 0)`: NA counts as failing the keep test."""
    return s.eq(1) & s.notna()


def is0(s: pd.Series) -> pd.Series:
    return s.eq(0) & s.notna()


def overall_of(df: pd.DataFrame, tag: str) -> pd.Series:
    if tag in ("study10",):
        return df["overallSingle"].fillna(df["overallMultiple"])
    if tag in ("s3", "s4"):
        return (
            df["condition"]
            .map({"single": 0, "multiple": 1})
            .pipe(lambda c: df["overallSingle"].where(c == 0, df["overallMultiple"].where(c == 1)))
        )
    if tag == "s5":
        cols = {
            "overallOnly": "overallOO",
            "overallAttributes": "overallOF",
            "attributesOverall": "overallOS",
        }
        out = pd.Series(float("nan"), index=df.index)
        for c, col in cols.items():
            out = out.where(df["condition"] != c, df[col])
        return out
    raise KeyError(tag)


def kept(tag: str) -> pd.DataFrame:
    """The deposit's people the authors' R script keeps (per person; S7 and 9 per row below)."""
    df = read_deposit(tag)
    assert df["id"].is_unique
    dup = is0(df["duplicateIP"]) & is0(df["duplicateID"])
    if tag == "study10":
        keep = (
            df.assign(o=overall_of(df, tag))["o"].notna()
            & dup
            & is1(df["attnCheck"])
            & is1(df["approvedID"])
        )
    elif tag in ("s3", "s4"):
        keep = overall_of(df, tag).notna() & dup & is0(df["unapprovedID"])
    elif tag == "s5":
        keep = overall_of(df, tag).notna() & dup & df["attnCheck"].eq(2) & is1(df["approvedID"])
    elif tag == "study9":
        keep = dup & is1(df["attnCheck"]) & is0(df["unapprovedID"])
    elif tag == "s7":
        keep = dup
    else:
        raise KeyError(tag)
    return df[keep].reset_index(drop=True)


def persona(tag: str, df: pd.DataFrame) -> pd.DataFrame:
    labels = demographics(tag)
    age = pd.to_numeric(df["age"])
    assert age.dropna().between(18, 105).all() and (age.dropna() % 1 == 0).all()
    assert set(df["gender"].dropna().astype(int)) <= set(labels)
    return pd.DataFrame(
        {
            "age": age.astype("Int64").values,
            "gender": [labels[int(g)] if pd.notna(g) else None for g in df["gender"]],
        }
    )


def stars(s: pd.Series, hi: int) -> pd.Series:
    v = pd.to_numeric(s, errors="raise")
    assert (v.dropna() % 1 == 0).all() and v.dropna().between(1, hi).all()
    return v.astype("Int64")


def study9_long(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (person, domain): order, scenario, format, overall rating."""
    rows = []
    for pre, (dom, _, scen) in DOMAINS.items():
        cond = df[f"{dom}Condition"]
        order = df[f"order{dom.capitalize()}"]
        for f, (letter, _) in FORMATS.items():
            for s in scen:
                col = df[f"{pre}S{s}{letter}Overall"]
                hit = col.notna()
                assert (cond[hit] == f).all(), (pre, s, f)
                for i in df.index[hit]:
                    rows.append((df.at[i, "id"], dom, pre, s, f, order[i], col[i]))
    long = pd.DataFrame(
        rows, columns=["id", "domain", "pre", "scenario", "format", "order", "rating"]
    )
    assert not long.duplicated(["id", "domain"]).any()  # one scenario per domain
    return long


def study9_codes() -> dict[tuple[str, int, str], int]:
    return {(pre, s, f): k for k, (pre, s, f, _, _) in enumerate(study9_cells(), 1)}


def prep(tag: str) -> pd.DataFrame:
    """One coded row per kept person: assignment column(s), answers, age, gender."""
    df = kept(tag)
    out = pd.DataFrame({"pid": [f"{tag}_{i}" for i in df["id"]]})
    if tag == "study9":
        long = study9_long(df)
        first = long[long["order"] == 1].set_index("id")
        assert first.index.is_unique
        gone = first.index[first["pre"].isin(DROPPED_DOMAINS)]
        df = df[~df["id"].isin(gone)].reset_index(drop=True)
        out = pd.DataFrame({"pid": [f"{tag}_{i}" for i in df["id"]]})
        first = first.drop(gone)
        codes = study9_codes()
        out["arm"] = [
            codes[(first.at[i, "pre"], int(first.at[i, "scenario"]), first.at[i, "format"])]
            if i in first.index
            else pd.NA
            for i in df["id"]
        ]
        out["overall"] = stars(
            pd.Series([first.at[i, "rating"] if i in first.index else None for i in df["id"]]), 10
        ).values
        has = out["overall"].notna()
        assert out.loc[has, "arm"].notna().all()
    elif tag == "study10":
        f = df["overallSingle"].notna().map({True: "single", False: "multiple"})
        assert (f == df["condition"]).all()
        assert not (df["overallSingle"].notna() & df["overallMultiple"].notna()).any()
        out["arm"] = (f.map({"single": 0, "multiple": 2}) + df["scenario"].astype(int)).values
        out["overall"] = stars(overall_of(df, tag), 10).values
        out["go_again"] = stars(df["prefQ1"], 9).values
        out["recommend"] = stars(df["prefQ2"], 9).values
    elif tag in ("s3", "s4"):
        out["condition"] = df["condition"].map({"single": 1, "multiple": 2}).values
        assert out["condition"].notna().all()
        other = df["overallMultiple"].where(df["condition"] == "single", df["overallSingle"])
        assert other.isna().all()  # nobody answered the other arm's question
        out["overall"] = stars(overall_of(df, tag), 5).values
    elif tag == "s5":
        layout = {"overallOnly": 0, "overallAttributes": 2, "attributesOverall": 4}
        out["arm"] = (df["condition"].map(layout) + df["scenario"].astype(int)).values
        out["overall"] = stars(overall_of(df, tag), 10).values
    elif tag == "s7":
        for slot in (1, 2):
            arms, ratings = [], []
            for _, r in df.iterrows():
                at = [s for s in range(1, 7) if r[f"orderS{s}"] == slot]
                if not at or pd.isna(r["condition"]):
                    arms.append(pd.NA)
                    ratings.append(None)
                    continue
                (s,) = at
                f = r["condition"]
                if slot == 1:
                    arms.append(s7_code(f, s, None))
                else:
                    (a,) = [x for x in range(1, 7) if r[f"orderS{x}"] == 1]
                    arms.append(s7_code(f, a, s))
                ratings.append(r[f"{f}S{s}"])
            out[f"arm_{slot}"] = pd.array(arms, dtype="Int64")
            out[f"rating_{slot}"] = stars(pd.Series(ratings, dtype="float"), 10).values
        for s in range(1, 7):  # nobody rated a scenario outside their two
            shown = df[f"orderS{s}"].notna()
            for f in S7_LEVEL:
                assert df.loc[~shown, f"{f}S{s}"].isna().all()
    p = persona(tag, df)
    out["age"] = p["age"].values
    out["gender"] = p["gender"].values
    return out


def study9_bookcase_first() -> int:
    """Kept people whose rated first domain was the bookcase: dropped by ruling."""
    long = study9_long(kept("study9"))
    first = long[(long["order"] == 1) & long["rating"].notna()]
    return int(first["pre"].isin(DROPPED_DOMAINS).sum())


def study9_later() -> int:
    """Kept people's ratings of domains 2-4: real answers this build leaves out."""
    long = study9_long(kept("study9"))
    return int((long["rating"].notna() & (long["order"] > 1)).sum())


def check_codebook(tag: str) -> None:
    """The codebook lists the data file's columns, in order."""
    book = pd.read_csv(CODEBOOK / f"{SOURCES[tag][1]}___CODEBOOK.csv")
    assert list(book["varname"]) == list(read_deposit(tag).columns), tag


ASSIGNMENT = {  # tag -> the data's assignment columns, each an embedded field the .qsf sets
    "study9": [f"{dom}Condition" for dom, _, _ in DOMAINS.values()],
    "study10": ["condition", "scenario"],
    "s3": ["condition"],
    "s4": ["condition"],
    "s5": ["condition", "scenario"],
    "s7": ["condition"],
}


def check_assignment(tag: str) -> None:
    """Every assignment value in the data file is one its .qsf's flow sets: the match."""
    df, sv = read_deposit(tag), survey(tag)
    for col in ASSIGNMENT[tag]:
        held = {str(v).removesuffix(".0") for v in df[col].dropna().unique()}
        sets = set(sv.embedded_values(col))
        assert held and held <= sets, (tag, col, held, sets)


# ---------------------------------------------------------------------------
# The recipes
# ---------------------------------------------------------------------------


def recipe(e: Experiment) -> dict[str, Any]:
    arms = []
    for i, a in enumerate(e.arms):
        arm: dict[str, Any] = {
            "raw_values": a.raw,
            "condition_num": i,
            "factors": a.factors,
            "text": a.text,
        }
        if a.items:
            arm["items"] = {k: a.items[k] for k in sorted(a.items)}
        arms.append(arm)
    outcomes = []
    for t, o in enumerate(e.outcomes):
        out: dict[str, Any] = {
            "var": o.var,
            "task_num": t,
            "question": o.question,
            "scale": o.scale,
        }
        if o.condition_var:
            out["condition_var"] = o.condition_var
        outcomes.append(out)
    hi = max(o.scale["max"] for o in e.outcomes)
    qsf, data, name, prereg = SOURCES[e.name]
    added = "; ".join(f"'{x}'" for x in dict.fromkeys(e.added))
    notes = (
        f"{PAPER}\n\nGENERATED by scripts/gen_researchbox196.py; every judgement is in its "
        f"docstring. {name} ({prereg}), {len(prep(e.name)):,} people kept by the authors' R "
        f"script's exclusions. {e.notes}\n\nWording from {qsf} (the blocks the survey flow "
        "reaches), word-for-word: the scenario is the condition, the rating question the "
        "outcome. Typography normalised (HTML, non-breaking spaces, curly quotes); emphasis "
        f"dropped. Added words (ours): {added}; and in each outcome, '{OVERALL_ONLY}' after "
        f"the question. Data: {data}. Persona: age (years, as exported) and gender, labels "
        "from the .qsf's own choices."
    )
    cond: dict[str, Any] = {"source_vars": e.source_vars}
    if e.shared:
        cond["shared_context"] = e.shared
    cond["factors"] = e.factors
    cond["arms"] = arms
    return {
        "study_id": STUDY_ID,
        "source": "researchbox",
        "experiment": e.name,
        "title": e.title,
        "data_file": data_file(e.name),
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": "pid",
        "notes": notes,
        "condition": cond,
        "outcomes": outcomes,
        "response_recode": {k: k for k in range(1, hi + 1)},
        "missing_codes": [],
        "persona_map": {"age": "age", "gender": "gender"},
    }


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
        study9_check_codebook()
        for tag in SOURCES:
            check_codebook(tag)
            check_assignment(tag)
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
