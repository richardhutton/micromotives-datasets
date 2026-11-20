#!/usr/bin/env python3
"""Write recipes/researchbox482_s3.yaml: is this arrival time consistent with the estimate? (1 recipe).

Hu B, Gaertig C, Dietvorst BJ, "How Should Time Estimates be Structured to Increase Customer
Satisfaction?" (the manuscript title in the box's ReadMe; the deposit names no journal or
year). ResearchBox 482 ("Time Estimates and Customer Satisfaction",
https://researchbox.org/482), read from its Zenodo copy (record 15033033,
https://zenodo.org/records/15033033). CC BY 4.0 ("All content posted to ResearchBox is under
a CC By 4.0 License", the box page). US online samples (MTurk via CloudResearch, Prolific).
The paper was not read; the answer key is the authors' own Stata code (Code/Study S3.do),
transcribed and re-run on the deposit and on the built rows, and the numbers Online
Supplement 6 reports for it.

Every judgement is here, in code, so the recipe can be re-derived and reviewed.

THE BOX. Eleven studies (1-8, S1-S3), each with a .qsf, a survey doc of screenshots, an .xlsx
data file (one header row, codes), a codebook, a Stata do file and an AsPredicted
pre-registration; plus "Underlying Distributions.xlsx", the ReadMe, a note on Study 1's
condition names and the Online Supplement (.docx). The .qsf files are 2024 copies
(SurveyCreationDate 2024-07-24 for S3; S3 was pre-registered in Nov 2023), so none is
literally the fielded file; S3's wording agrees with its pre-registration (the eleven time
bins and both answer labels, word-for-word) and with the supplement's description.

WHAT IS BUILT. Study S3 (AsPredicted #150577, Supplement 6), 2 x 2 between people: a
navigation app (driving to a local shopping mall) or a food delivery app (ordering dinner),
whose estimate was a point ("43 minutes") or a range ("33-53 minutes"). On one page everyone
then said, for each of eleven time bins from "< 21 min" to "> 65 min", whether it was
consistent with the estimate ("Yes, consistent" / "No, inconsistent"). Each bin is one
outcome. Kind "mix" (two crossed manipulations).

NOT BUILT (NOT_BUILT), each with its reason. Studies 1, 2, 3, 5, 6, 7, 8 and S1 share one
paradigm: twenty pages, one per past order (or trip), each showing the app's estimate and how
long that order actually took, the twenty times drawn at random per person, then the outcomes
(satisfaction, perceived accuracy). The deposit records WHICH twenty times a person saw (the
"outcomes" column; Study 3's draw36-draw55) but not the order the pages came in: each
codebook says so in words ("the order represents the order in which the numbers were listed
in the loop & merge function, rather than the actual order presented to participant"), the
loop is a random subset (Randomization "Subset") and no display-order column exists
(asserted by check_sequences). Every outcome follows the whole sequence, so every row would
have to narrate twenty screens in an order that was not recorded (CONVENTIONS, "Repeated
measures within one block": an order randomised and not recorded cannot be narrated at all;
the choice-set ruling of 16 Nov 2026 explicitly does not reopen screen sequences). The pages
also print their own position ("Order ${lm://CurrentLoopNumber}:"). Study S1 shows the app's
estimate as pictures too; Study 4 adds a picture, JavaScript and a real countdown timer;
Study S2's response is a 20-ball distribution built in a JavaScript tool, not one value.

UK FIT. Ordering dinner from a delivery app, or driving to a local shopping mall with a
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

_SEQ = (
    "twenty pages, each the app's estimate and how long one past order actually took, the "
    "times drawn at random per person, come before every outcome, and the order of the pages "
    "is not recorded (the codebook says so; random-subset loop, no display-order column), so "
    "no row can narrate them (CONVENTIONS: an order randomised and not recorded cannot be "
    "narrated)"
)
NOT_BUILT = {
    "study1": f"Study 1 (point vs 10- or 20-minute range, food delivery): {_SEQ}.",
    "study2": f"Study 2 (point vs moderate vs extremely wide range): {_SEQ}.",
    "study3": "Study 3 (point vs range, a different estimate per order): "
    + _SEQ.replace("the times drawn", "each order's estimate and time drawn").replace(
        "random-subset loop", "twenty trial blocks in a random-subset block randomiser"
    )
    + ".",
    "study4": "Study 4 (choose Model Alpha or Beta, one giving a point and one a range): ten "
    "pages of the two models' estimates against randomly drawn pre-test completion times come "
    "before the choice, in an order the codebook says is not recorded; the instructions carry "
    "a picture (IM_bp9CGOYFmFW3tXg) and JavaScript, and the later slider task runs against a "
    "real countdown timer.",
    "study5": f"Study 5 (point vs range; satisfaction and perceived lateness): {_SEQ}.",
    "study6": f"Study 6 (optimistic, accurate or conservative point vs range): {_SEQ}.",
    "study7": f"Study 7 (accurate or conservative point or range): {_SEQ}.",
    "study8": f"Study 8 (short or long drive x accurate point, conservative point or range): "
    f"{_SEQ.replace('one past order', 'one past trip')}.",
    "s1": f"Study S1 (point, range, or both): {_SEQ}; the app's estimate is also shown as "
    "pictures (IM_4GDWg5juxdW4098, IM_b8fKvbEABNIgrLE, IM_e9Uhc0g4Wt4c5am).",
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
    s = re.sub(r"(?i)<br\s*/?>|</p>|</div>|<p[^>]*>|<div[^>]*>", "\n\n", raw or "")
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prep", action="store_true", help="code the data")
    ap.add_argument("--check", action="store_true", help="exit 1 if the recipe differs")
    args = ap.parse_args()
    if args.prep:
        check_pictures()
        check_codebook()
        check_sequences()
        path = RAW / data_file()
        prep().to_csv(path, index=False)
        print(f"wrote {path.relative_to(REPO)}")
        return 0
    e = experiment()
    path, text = recipe_path(e), render(e)
    if args.check:
        same = path.exists() and path.read_text() == text
        print(("matches " if same else "DIFFERS ") + path.name)
        return 0 if same else 1
    path.write_text(text)
    print(f"wrote {path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
