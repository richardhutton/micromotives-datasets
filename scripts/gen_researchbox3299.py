#!/usr/bin/env python3
"""Write recipes/researchbox3299_*.yaml: sure versus uncertain price promotions (13 studies).

Gaertig C & Simmons JP (2025), "Why (and When) Are Uncertain Price Promotions More
Effective Than Equivalent Sure Discounts?", Journal of Consumer Research,
doi:10.1093/jcr/ucaf036. ResearchBox 3299 ("Probabilistic Price Promotions",
https://researchbox.org/3299), archived as Zenodo doi:10.5281/zenodo.15453383. CC BY 4.0
("All content posted to ResearchBox is under a CC By 4.0 License", the box page). US online
samples (MTurk 2018, Prolific 2023), US dollars and US places (Jersey Shore, Chicago,
Barcelona for the Spain study); kept as the source has them.

Every judgement is here, in code, so the recipes can be re-derived and reviewed.

WHICH QUESTIONNAIRE. Each study ships two .qsf files, "Qualtrics_Study_X" and
"Uncertain_Promotions_Paper_Study_X". Both are Qualtrics exports of copies made in 2025
(SurveyCreationDate 2025-01-31 or 2025-08-07; the studies were fielded in 2018 and 2023),
so neither is literally the fielded survey file. For ten studies the two files are
byte-identical. For Studies 4, S3 and S4 they differ ONLY in that the "Uncertain_Promotions"
copy still carries the IP-address exclusion lists in its survey flow, which the
"Qualtrics_Study" copy replaces with "[IP ADDRESSES DELETED FOR MATERIAL POSTING]" (and in
Qualtrics bookkeeping: element order, AnalyzeText flags, response-set ids). `check_qsf_pair`
asserts that every question's text, choices, recodes, display logic and every block are
identical across the pair, and that the flows agree once embedded-data values are
blanked. So the wording is the same in both; the recipes read "Qualtrics_Study_X" (the
redacted copy), and this script never reads or prints an embedded-data value from the
other one. The materials PDFs (the authors' screenshots) agree with the .qsf on every
stimulus screen; they differ on the intro screen ("On the next pages, we will ask you
read ...") and show age as a text box where the 2018/2023 .qsf copies of eight studies
have a drop-down; neither touches a row.

PICTURES. The hotel screens embed Qualtrics graphics (a hotels.com or kayak listing
screenshot) whose ids are in the .qsf. They were fetched from Qualtrics' own graphic
server (https://yul1.qualtrics.com/CP/Graphic.php?IM=<id>, 19 Nov 2026) into
Materials/graphics/, and match the authors' PDF screenshots. Each file is pinned by
sha256 below. Their PRINTED WORDS are transcribed (ledger 153: printed words in an image
are stimulus text, a picture is not), one line per field in reading order, wrapped lines
joined, bullets as "- ", check-mark glyphs dropped. Photographs, star icons and rating
circles are not rendered or described. Study 1 and 2's price ($48 for one night, $480
"Your 10 night total") exists ONLY inside the picture, so the transcription is what
carries the price factor. Study S5's slot-machine conditions show a 100x88 picture of
slot-machine reels beside the odds (IM_1EONH7n0qCst6Rv); it is not rendered: the words
beside it already say "you play an electronic slot machine".

ORDER OF THE OPTIONS. Where two options were shown and their order was randomised AND
recorded (SureDiscountFirst; CityFirst in S5), each row is rendered in that respondent's
order and the order is a declared factor. The answer codes are positional in the data
(the .qsf recodes the first choice to 1), so they stay as they are, coded to the order the
row shows; the do files reverse them by the same variable to get "chose the uncertain
promotion". The three-hotel choice sets (S1a, S1b, S1c, S2) were in a fixed order (no
choice randomisation in the .qsf; the PDFs show the same order in every condition).

WHAT IS DROPPED. Consent, the intro screens and "Click >> ..." (survey mechanics); "(click
on the hotel to make your selection)" (response mechanics); Study S4's "Click >> to see the
next scenario." (sequence signposting); timing items. Study 5's block randomisation lists
two further items (disappointment, likelihood of winning) that are not in the block, not
on the PDF's mediator screen and not in the data: not fielded, not built.

NARRATION (ours, CONVENTIONS "Narrating what the respondent did"). Where an outcome came
after an earlier question in the same study, its condition is everything shown up to its
own screen, and the earlier question is narrated as asked, with these added words:
  Study 3 (order of the two questions randomised and recorded, WQfirst):
    'You were asked "<earlier question>" You were then shown the scenario again:'
  Study 5 size and S4's second scenario (fixed order):
    'You were asked "Which price promotion would you like to receive?"'
  S4 adds, before the second scenario: 'You were then shown another scenario:'

EXCLUSIONS follow the authors' do files exactly (duplicate IP / ID responses, IPs from an
earlier study, S5's failed attention check, people who did not answer), so N matches the
N each do file states. Age outside 18-100 (332, 335 and 6, text entries) is left blank in
the persona; the person is kept, as the S1a do file keeps its 332.

    uv run python scripts/gen_researchbox3299.py --prep   # (re)write the coded .csv files
    uv run python scripts/gen_researchbox3299.py          # write the recipes
    uv run python scripts/gen_researchbox3299.py --check  # exit 1 if any recipe differs
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
STUDY_ID = "researchbox3299"
RAW = REPO / "data" / "raw" / STUDY_ID
MATERIALS = RAW / "Materials"
DATA_DIR = RAW / "Data"
GRAPHICS = MATERIALS / "graphics"
RECIPES = REPO / "recipes"
LICENCE = (
    'CC BY 4.0, stated on the box page https://researchbox.org/3299 ("All content posted '
    'to ResearchBox is under a CC By 4.0 License"); archived as Zenodo '
    "doi:10.5281/zenodo.15453383. Read 19 Nov 2026."
)
PAPER = (
    'Gaertig C & Simmons JP (2025), "Why (and When) Are Uncertain Price Promotions More '
    'Effective Than Equivalent Sure Discounts?", Journal of Consumer Research, '
    "doi:10.1093/jcr/ucaf036. ResearchBox 3299 (https://researchbox.org/3299)."
)

# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

_TYPO = {"\xa0": " ", "\u200b": "", "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"'}


def norm(raw: str) -> str:
    """HTML to one line of plain text. Typography only; words untouched."""
    s = re.sub(r"<br\s*/?>|</p>|</td>|</tr>|</div>", " ", raw or "")
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    for a, b in _TYPO.items():
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def qsf_path(tag: str, prefix: str = "Qualtrics_Study_") -> Path:
    return MATERIALS / f"{prefix}{tag}.qsf"


def load_qsf(tag: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(qsf_path(tag).read_text())
    return data


def questions(tag: str) -> dict[str, dict[str, Any]]:
    return {
        e["Payload"]["QuestionID"]: e["Payload"]
        for e in load_qsf(tag)["SurveyElements"]
        if e["Element"] == "SQ"
    }


def question_text(tag: str, qid: str) -> str:
    return norm(questions(tag)[qid]["QuestionText"])


def embedded(tag: str) -> set[tuple[str, str]]:
    """Every (field, value) the survey flow sets."""
    found: set[tuple[str, str]] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("Type") == "EmbeddedData":
                for e in node.get("EmbeddedData", []):
                    found.add((str(e.get("Field")), str(e.get("Value"))))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for e in load_qsf(tag)["SurveyElements"]:
        if e["Element"] == "FL":
            walk(e["Payload"])
    return found


def check_qsf_pair(tag: str) -> None:
    """The two exports agree on everything a respondent saw (see the docstring)."""
    a = json.loads(qsf_path(tag).read_text())
    b = json.loads(qsf_path(tag, "Uncertain_Promotions_Paper_Study_").read_text())
    fields = ["QuestionText", "Choices", "ChoiceOrder", "RecodeValues", "DisplayLogic", "Answers"]

    def sq(d: dict[str, Any]) -> dict[str, Any]:
        return {
            e["Payload"]["QuestionID"]: {f: e["Payload"].get(f) for f in fields}
            for e in d["SurveyElements"]
            if e["Element"] == "SQ"
        }

    def blocks(d: dict[str, Any]) -> list[str]:
        p = next(e for e in d["SurveyElements"] if e["Element"] == "BL")["Payload"]
        items = p.values() if isinstance(p, dict) else p
        return sorted(json.dumps(x, sort_keys=True) for x in items)

    def blank_values(node: Any) -> Any:
        if isinstance(node, dict):
            return {
                k: ("<value>" if k == "Value" else blank_values(v))
                for k, v in node.items()
                if k != "AnalyzeText" and not (k == "Autofill" and v == [])
            }
        if isinstance(node, list):
            return [blank_values(x) for x in node]
        return node

    def flow(d: dict[str, Any]) -> str:
        p = next(e for e in d["SurveyElements"] if e["Element"] == "FL")["Payload"]
        return json.dumps(blank_values(p), sort_keys=True)

    assert sq(a) == sq(b), f"{tag}: questions differ between the two .qsf exports"
    assert blocks(a) == blocks(b), f"{tag}: blocks differ between the two .qsf exports"
    assert flow(a) == flow(b), f"{tag}: survey flow differs between the two .qsf exports"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# The listings: printed words of each Qualtrics graphic, transcribed by eye
# ---------------------------------------------------------------------------

# graphic id -> (file, sha256 of the file as fetched)
GRAPHIC_FILES = {
    "IM_8iyszuEgAOQus0B": ("IM_8iyszuEgAOQus0B.png", "37b8852d"),
    "IM_8j0vY2hVDayx9ml": ("IM_8j0vY2hVDayx9ml.png", "37b8852d"),
    "IM_cCH0jwIJE1pCg6N": ("IM_cCH0jwIJE1pCg6N.png", "c2ba8824"),
    "IM_errYUqEW6awimzz": ("IM_errYUqEW6awimzz.png", "c2ba8824"),
    "IM_bIvX1rdCvoZeMYZ": ("IM_bIvX1rdCvoZeMYZ.png", "0b50ba62"),
    "IM_2cA1Ibb8yYSQRp3": ("IM_2cA1Ibb8yYSQRp3.png", "241a0dc0"),
    "IM_eKjrLdb7pXlOmln": ("IM_eKjrLdb7pXlOmln.png", "799f3e52"),
    "IM_0pHiZwfjvcCarid": ("IM_0pHiZwfjvcCarid.png", "d4edb30f"),
    "IM_bNGCSH7H1E2EXFH": ("IM_bNGCSH7H1E2EXFH.png", "5f7c2d9b"),
    "IM_295q2lhgFvjdfKt": ("IM_295q2lhgFvjdfKt.png", "763eec1c"),
    "IM_d4CQYjBUBYjy0br": ("IM_d4CQYjBUBYjy0br.png", "88065dd4"),
    "IM_2iCDSa27A63I18x": ("IM_2iCDSa27A63I18x.jpg", "91dfa36f"),
    "IM_2ayq4MH94GM1gpv": ("IM_2ayq4MH94GM1gpv.jpg", "81053d76"),
    "IM_4SpIIEjnCJ4PDoN": ("IM_4SpIIEjnCJ4PDoN.jpg", "027475f5"),
    # S1b uploads the same three listings once per condition's question.
    "IM_1Y0yZiVGTI5Lhu5": ("IM_1Y0yZiVGTI5Lhu5.jpg", "91dfa36f"),
    "IM_80rrfrXWS4OyY2F": ("IM_80rrfrXWS4OyY2F.jpg", "91dfa36f"),
    "IM_cvi56K2ivQk3Ti5": ("IM_cvi56K2ivQk3Ti5.jpg", "91dfa36f"),
    "IM_eSe8chmq0U0qgC1": ("IM_eSe8chmq0U0qgC1.jpg", "91dfa36f"),
    "IM_3V0Ojfp43TYBKuN": ("IM_3V0Ojfp43TYBKuN.jpg", "81053d76"),
    "IM_4Zz73XMh41Nd1LT": ("IM_4Zz73XMh41Nd1LT.jpg", "81053d76"),
    "IM_bklbrLAF7u1jn5r": ("IM_bklbrLAF7u1jn5r.jpg", "81053d76"),
    "IM_eKbOODZyZphQS9f": ("IM_eKbOODZyZphQS9f.jpg", "81053d76"),
    "IM_37zoLRsT98yScOF": ("IM_37zoLRsT98yScOF.jpg", "027475f5"),
    "IM_5AzTrFZvAoAlCoB": ("IM_5AzTrFZvAoAlCoB.jpg", "027475f5"),
    "IM_6Lr0Zcx3azdp8od": ("IM_6Lr0Zcx3azdp8od.jpg", "027475f5"),
    "IM_b7tbzYBSReGPGPr": ("IM_b7tbzYBSReGPGPr.jpg", "027475f5"),
}

_ECONO = [
    "Econo Lodge Somers Point (Last booked 10 hours ago)",
    "21 Macarthur Blvd, Somers Point, NJ, 08244 United States, 866-925-8676",
    "Somers Point",
    "- 2.7 miles to Ocean City",
    "- 9.7 miles to Atlantic City, NJ (ACY-Atlantic City Intl.)",
    "Collect nights",
    "Good 6.2",
    "120 Hotels.com guest reviews",
    "164 reviews",
]
_QUALITY = [
    "Quality Inn Pleasantville (Booked 1 hour ago)",
    "1012 Black Horse Pike, Pleasantville, NJ, 08232 United States, 866-539-9234",
    "Pleasantville",
    "- 8.3 miles to Ocean City",
    "- 4.2 miles to Atlantic City, NJ (ACY Atlantic City Intl.)",
    "Collect nights",
    "Good 6.8",
    "218 Hotels.com guest reviews",
    "89 reviews",
]
_RAMADA_WEST = [
    "Ramada West Atlantic City (Last booked 7 hours ago)",
    "8037 Black Horse Pike, Pleasantville, NJ, 08232 United States, 866-538-1314",
    "Pleasantville",
    "- 8.3 miles to Ocean City",
    "- 6.7 miles to Atlantic City, NJ (ACY-Atlantic City Intl.)",
    "Collect nights",
    "5.6",
    "659 Hotels.com guest reviews",
    "644 reviews",
]
_LOW = ["Choose Room"]
_TEN = "Your 10 night total"

LISTING: dict[str, list[str]] = {
    "37b8852d": [*_ECONO, "$48", *_LOW],
    "c2ba8824": [*_ECONO, "$480", _TEN, *_LOW],
    "0b50ba62": [*_QUALITY, "$44", *_LOW],
    "241a0dc0": [*_QUALITY, "$440", _TEN, *_LOW],
    "799f3e52": [*_RAMADA_WEST, "$42", *_LOW],
    "d4edb30f": [*_RAMADA_WEST, "$420", _TEN, *_LOW],
    "5f7c2d9b": [
        "$210",
        "Select",
        "$242 total",
        "The Buckingham Athletic Club",
        "0.6 mi",
        "map 440 S La Salle St (South Loop)",
        "4.4/5 user rating 9 reviews",
        "Like",
        "Be the first of your friends to like this.",
        "2 sites",
        "details save track price share",
    ],
    "763eec1c": [
        "$209",
        "Select",
        "$238 total",
        "The James Hotel Chicago",
        "0.6 mi",
        "map 55 East Ontario (Gold Coast, Old Town)",
        "4.5/5 user rating 50 reviews",
        "Like",
        "Be the first of your friends to like this.",
        "6 sites",
        "details save track price share",
    ],
    "88065dd4": [
        "$200",
        "Select",
        "$231 total",
        "Residence Inn Chicago Downtown/River North",
        "0.4 mi",
        "map 410 North Dearborn Street",
        "no reviews - write one",
        "Like",
        "Be the first of your friends to like this.",
        "1 site",
        "details save track price share",
    ],
    "91dfa36f": [
        "Ramada Plaza Chicago North Shore (Last booked 7 hours ago)",
        "1090 South Milwaukee Avenue, Wheeling, IL, 60090 United States, 866-925-8676",
        "3-star",
        "Wheeling",
        "- 21 miles to City center",
        "- 21 miles to Downtown Chicago",
        "Collect nights",
        "Good 7.8",
        "206 Hotels.com guest reviews",
        "108 reviews",
        "$90",
        "free cancellation",
        "pay now or at hotel",
        "Choose Room",
    ],
    "81053d76": [
        "Edward Hotel Chicago (Last booked 1 hour ago)",
        "6600 N. Mannheim Rd, Rosemont, IL, 60018 United States, 866-925-8676",
        "3-star",
        "Rosemont",
        "- 16 miles to City center",
        "- 16 miles to Downtown Chicago",
        "Collect nights",
        "Very Good 8.0",
        "948 Hotels.com guest reviews",
        "602 reviews",
        "$89",
        "free cancellation",
        "pay now or at hotel",
        "Choose Room",
    ],
    "027475f5": [
        "Best Western Plus Chicago Hillside (Booked 1 hour ago)",
        "4400 Frontage Road, Hillside, IL, 60162 United States, 866-925-4159",
        "3-star",
        "Hillside",
        "- 14 miles to City center",
        "- 14 miles to Downtown Chicago",
        "Collect nights",
        "Good 7.4",
        "349 Hotels.com guest reviews",
        "447 reviews",
        "$84",
        "free cancellation",
        "pay now or at hotel",
        "Choose Room",
    ],
}
# The hotel's name as printed, for the outcome's option list.
HOTEL_NAME = {
    "5f7c2d9b": "The Buckingham Athletic Club",
    "763eec1c": "The James Hotel Chicago",
    "88065dd4": "Residence Inn Chicago Downtown/River North",
    "91dfa36f": "Ramada Plaza Chicago North Shore",
    "81053d76": "Edward Hotel Chicago",
    "027475f5": "Best Western Plus Chicago Hillside",
    "37b8852d": "Econo Lodge Somers Point",
    "c2ba8824": "Econo Lodge Somers Point",
    "0b50ba62": "Quality Inn Pleasantville",
    "241a0dc0": "Quality Inn Pleasantville",
    "799f3e52": "Ramada West Atlantic City",
    "d4edb30f": "Ramada West Atlantic City",
}


def graphic_key(image_id: str) -> str:
    """The pinned hash prefix of a graphic, checked against the file when present."""
    name, short = GRAPHIC_FILES[image_id]
    path = GRAPHICS / name
    if path.exists():
        assert sha256(path).startswith(short), f"{name}: not the file transcribed"
    return short


def listing(image_id: str) -> str:
    return "\n".join(LISTING[graphic_key(image_id)])


def image_ids(html_text: str) -> list[str]:
    return re.findall(r"IM=(IM_[A-Za-z0-9]+)", html_text)


def choice_images(tag: str, qid: str) -> list[str]:
    q = questions(tag)[qid]
    assert not q.get("Randomization"), f"{tag} {qid}: choices randomised"
    order = [str(c) for c in (q.get("ChoiceOrder") or q["Choices"])]
    assert order == ["1", "2", "3"], (tag, qid, order)
    assert q.get("RecodeValues", {"1": "1", "2": "2", "3": "3"}) == {"1": "1", "2": "2", "3": "3"}
    return [q["Choices"][c]["Image"]["ImageLocation"] for c in order]


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

DATA_FILES = {
    "1": "Study 1 - Posted Data File.xls",
    "2": "Study 2 - Posted Data.xlsx",
    "3": "Study 3 - Posted Data File.xls",
    "4": "Study 4 - Posted Data File.xls",
    "4_Pretest": "Study 4 Pretest - Posted Data File.xls",
    "5": "Study 5 - Posted Data File.xls",
    "S1A": "Study S1a - Posted Data File.xls",
    "S1B": "Study S1b - Posted Data File.xls",
    "S1C": "Study S1c - Posted Data File.xls",
    "S2": "Study S2 - Posted Data File.xls",
    "S3": "Study S3 - Posted Data File.xls",
    "S4": "Study S4 - Posted Data File.xls",
    "S5": "Study S5 - Posted Data File.xls",
}
# Rows dropped by each do file, in its own words, and the N it then states.
EXCLUDE = {
    "1": (["ExcludeDuplicateIP", "ExcludePreviousIP"], 852),
    "2": (["ExcludeDuplicateIP"], 2338),
    "3": (["ExcludeDuplicateIP1", "ExcludeDuplicateID"], 2221),
    "4": (["ExcludeDuplicateIP", "ExcludeDuplicateID"], 2371),
    "4_Pretest": (["ExcludeDuplicateIP", "ExcludePreviousIP"], 867),
    "5": (["ExcludeDuplicateIP1", "ExcludeDuplicateID"], 1187),
    "S1A": ([], 1502),
    "S1B": (["ExcludeDuplicateIP", "ExcludePreviousIP"], 2039),
    "S1C": (["ExcludeDuplicateIP1", "ExcludeDuplicateID"], 2049),
    "S2": (["ExcludeDuplicateIP", "ExcludePreviousIP"], 2302),
    "S3": (["ExcludeDuplicateIP", "ExcludeDuplicateID"], 1188),
    "S4": (["ExcludeDuplicateIP", "ExcludeDuplicateID"], 984),
    "S5": (["FailedCheck"], 1986),
}
# The do file's DV for "did not answer", dropped after the flags (3, 5, S1c).
ANSWERED = {"3": "Rating", "5": "Rating", "S1C": "Choice"}
AGE_RANGE = (18, 100)


def read_study(tag: str) -> pd.DataFrame:
    df = pd.read_excel(DATA_DIR / DATA_FILES[tag])
    flags, n = EXCLUDE[tag]
    for f in flags:
        df = df[df[f] != 1]
    if tag in ANSWERED:
        df = df[df[ANSWERED[tag]].notna()]
    assert len(df) == n, f"{tag}: {len(df)} rows after exclusions, do file says {n}"
    return df.reset_index(drop=True)


def gender_labels(tag: str) -> dict[int, str]:
    q = next(
        p for p in questions(tag).values() if norm(p["QuestionText"]) == "What is your gender?"
    )
    recode = q.get("RecodeValues") or {k: k for k in q["Choices"]}
    return {int(recode[k]): norm(v["Display"]) for k, v in q["Choices"].items()}


def persona_cols(tag: str, df: pd.DataFrame) -> pd.DataFrame:
    labels = gender_labels(tag)
    age = pd.to_numeric(df["Age"], errors="coerce")
    ok = age.between(*AGE_RANGE)
    out = pd.DataFrame(
        {
            "age": age.where(ok).astype("Int64"),
            "gender": df["Gender"].map(lambda g: labels[int(g)] if pd.notna(g) else None),
        }
    )
    return out


# ---------------------------------------------------------------------------
# The experiments
# ---------------------------------------------------------------------------


@dataclass
class Arm:
    raw: dict[str, int]
    factors: dict[str, str]
    text: str
    options: list[str] | None = None  # nominal options in on-screen order
    question: str | None = None  # per-arm outcome wording
    item_text: dict[int, str] = field(default_factory=dict)  # per-outcome condition text


@dataclass
class Outcome:
    var: str
    question: str
    scale: dict[str, Any]


@dataclass
class Experiment:
    name: str
    tag: str
    title: str
    design: str
    source_vars: list[str]
    factors: list[str]
    arms: list[Arm]
    outcomes: list[Outcome]
    notes: str
    data_cols: dict[str, str]  # coded column -> deposit column
    rejected: dict[str, str] = field(default_factory=dict)


RATING_SCALE = {
    "min": 1,
    "max": 6,
    "min_label": "Definitely Promotion A",
    "max_label": "Definitely Promotion B",
}
SIZE_SCALE = {"min": 1, "max": 7, "min_label": "Very small", "max_label": "Very large"}
ORDER = {1: "sure_first", 0: "uncertain_first"}


def opt_question(question: str, options: list[str]) -> str:
    listed = "; ".join(f'{i} means "{o}"' for i, o in enumerate(options, 1))
    return f"{question} {listed}."


def table(first: str, second: str) -> str:
    return f"Promotion A: {first}\nPromotion B: {second}"


def require(text: str, source: str, where: str) -> None:
    assert flat(text) in source, f"{where}: {flat(text)!r} not in the questionnaire"


def require_ed(tag: str, pairs: dict[str, str]) -> None:
    ed = embedded(tag)
    for k, v in pairs.items():
        assert (k, v) in ed, f"{tag}: flow never sets {k} = {v!r}"


# --- Studies 1 and 2: hotel booking, choose one of two promotions -----------

HOTEL_INTRO = [
    "Imagine you selected the hotel below for an upcoming trip to the Jersey Shore.",
    "You learn that your booking comes with one of two types of price promotions, and that "
    "you can choose which type of price promotion you would like to receive.",
]
HOTEL_CHOICE = (
    "You can choose between receiving {first} or {second}. The price promotion that you "
    "choose will be applied to the price of the hotel room that is stated below."
)
WHICH_PROMOTION = "Which price promotion would you like to receive?"


def hotel_two_options(tag: str) -> list[Arm]:
    qs = questions(tag)
    low, high = qs["QID56"], qs["QID60"]
    assert "Low" in json.dumps(low["DisplayLogic"]) or "PriceLow" in json.dumps(low["DisplayLogic"])
    images = {"low": image_ids(low["QuestionText"]), "high": image_ids(high["QuestionText"])}
    assert len(images["low"]) == len(images["high"]) == 1
    for q in (low, high):
        src = norm(q["QuestionText"])
        for p in [
            *HOTEL_INTRO,
            HOTEL_CHOICE.format(first="${e://Field/First}", second="${e://Field/Second}"),
            WHICH_PROMOTION,
        ]:
            require(p, src, f"{tag} {q['QuestionID']}")
        assert q["RecodeValues"] == {"6": "1", "7": "2"}
    sure = "{p} off of the price of the hotel room"
    arms: list[Arm] = []
    if tag == "1":
        cells = {1: ("low", "1%"), 2: ("low", "10%"), 3: ("high", "1%"), 4: ("high", "10%")}
        for c, (price, pct) in cells.items():
            require_ed(tag, {"Condition": str(c), "Price": price.title(), "Probability": pct})
        require_ed(
            tag,
            {
                "First": "${e://Field/Probability} off of the price of the hotel room",
                "Second": "a ${e://Field/Probability} chance to get the hotel room for free",
            },
        )
        for c, (price, pct) in cells.items():
            s = sure.format(p=pct)
            u = f"a {pct} chance to get the hotel room for free"
            for sdf in (1, 0):
                first, second = (s, u) if sdf else (u, s)
                arms.append(
                    _hotel_arm(
                        c, sdf, {"price": price, "percent": pct}, first, second, images[price][0]
                    )
                )
    else:
        cells2 = {
            1: ("low", "free"),
            2: ("low", "half_price"),
            3: ("high", "free"),
            4: ("high", "half_price"),
        }
        for c, (price, kind) in cells2.items():
            require_ed(
                tag,
                {
                    "Condition": str(c),
                    "PriceLow": "1" if price == "low" else "0",
                    "Free": "1" if kind == "free" else "0",
                },
            )
        uncertain = {
            "free": "a 10% chance to get the hotel room for free",
            "half_price": "a 20% chance to get the hotel room for half price",
        }
        s = sure.format(p="10%")
        for u in uncertain.values():
            require_ed(tag, {"First": s, "Second": u})
            require_ed(tag, {"First": u, "Second": s})
        for c, (price, kind) in cells2.items():
            u = uncertain[kind]
            for sdf in (1, 0):
                first, second = (s, u) if sdf else (u, s)
                arms.append(
                    _hotel_arm(
                        c, sdf, {"price": price, "uncertain": kind}, first, second, images[price][0]
                    )
                )
    return arms


def _hotel_arm(
    c: int, sdf: int, factors: dict[str, str], first: str, second: str, image: str
) -> Arm:
    text = "\n\n".join(
        [*HOTEL_INTRO, HOTEL_CHOICE.format(first=first, second=second), listing(image)]
    )
    return Arm(
        raw={"Condition": c, "SureDiscountFirst": sdf},
        factors={**factors, "order": ORDER[sdf]},
        text=text,
        options=[first, second],
    )


# --- Product promotions on a 1-6 scale (Studies 4, 5, S4) -------------------

PRODUCT_INTRO = "Imagine you are about to buy a product."
PRODUCT_PRICE = "The original price of the product is {price}."
PRODUCT_LEARN = (
    "You learn that the product comes with one of two types of price promotions, and that you "
    "can choose which type of price promotion you would like to receive."
)
PRODUCT_CHOOSE = "You can choose between two promotions:"
PRODUCT_APPLIED = (
    "The promotion that you choose will be applied to the original price of the product ({price})."
)
UNCERTAIN_PRODUCT = "A 10% chance to get the product for free"


def product_screen(price: str, first: str, second: str) -> str:
    return "\n\n".join(
        [
            PRODUCT_INTRO,
            PRODUCT_PRICE.format(price=price),
            PRODUCT_LEARN,
            PRODUCT_CHOOSE,
            table(first, second),
            PRODUCT_APPLIED.format(price=price),
        ]
    )


def product_source(price: str, f1: str, f2: str) -> str:
    return flat(
        " ".join(
            [
                PRODUCT_INTRO,
                PRODUCT_PRICE.format(price=price),
                PRODUCT_LEARN,
                PRODUCT_CHOOSE,
                f"Promotion A: Promotion B: ${{e://Field/{f1}}} ${{e://Field/{f2}}}",
                PRODUCT_APPLIED.format(price=price),
            ]
        )
    )


def check_rating_q(q: dict[str, Any], tag: str) -> None:
    assert q["RecodeValues"] == {"6": "1", "7": "2", "8": "3", "9": "4", "10": "5", "11": "6"}, tag
    labels = [norm(q["Choices"][str(k)]["Display"]) for k in range(6, 12)]
    assert labels == ["Definitely Promotion A", "", "", "", "", "Definitely Promotion B"], (
        tag,
        labels,
    )


# ---------------------------------------------------------------------------


def study1() -> Experiment:
    return Experiment(
        name="study1",
        tag="1",
        title="Hotel booking: a sure discount or a same-sized chance the room is free (Study 1)",
        design="2 (price $48 for one night / $480 for ten nights) x 2 (1% / 10%) x 2 (option order, recorded) between subjects; choice of two promotions",
        source_vars=["Condition", "SureDiscountFirst"],
        factors=["price", "percent", "order"],
        arms=hotel_two_options("1"),
        outcomes=[Outcome("choice", WHICH_PROMOTION, {"min": 1, "max": 2, "nominal": True})],
        notes=(
            "Study 1, MTurk, March 2018. Imagine a Jersey Shore hotel; choose between X% off the "
            "room or an X% chance the room is free, X = 1 or 10; the price shown is $48 (one "
            'night) or $480 ("Your 10 night total"). The listing is a picture (IM_8iyszuEgAOQus0B '
            "low, IM_cCH0jwIJE1pCg6N high); its printed words are transcribed and carry the price. "
            "Options in each respondent's recorded order (SureDiscountFirst); Choice 1 = first "
            "option shown. 852 of 899 kept (do file: 11 duplicate IPs, 36 IPs from earlier studies)."
        ),
        data_cols={"choice": "Choice"},
    )


def study2() -> Experiment:
    return Experiment(
        name="study2",
        tag="2",
        title="Hotel booking: a sure 10% off, or a chance the room is free or half price (Study 2)",
        design="2 (price $48 / $480) x 2 (10% chance free / 20% chance half price) x 2 (option order, recorded) between subjects; choice of two promotions",
        source_vars=["Condition", "SureDiscountFirst"],
        factors=["price", "uncertain", "order"],
        arms=hotel_two_options("2"),
        outcomes=[Outcome("choice", WHICH_PROMOTION, {"min": 1, "max": 2, "nominal": True})],
        notes=(
            "Study 2, MTurk, October 2018. Same hotel screen and pictures as Study 1. Choose 10% "
            "off, or a 10% chance the room is free / a 20% chance it is half price. Options in "
            "each respondent's recorded order (SureDiscountFirst); Choice 1 = first option "
            "shown. 2,338 of 2,412 kept (do file: 74 duplicate IPs)."
        ),
        data_cols={"choice": "Choice"},
    )


GYM = {
    "low": (
        "Imagine that you have just decided to buy a 1-year membership to a gym close to your "
        "home, as well as a week's worth of personal training sessions. The membership usually "
        "costs $40/month, and a week's worth of personal training sessions costs $50.",
        "At the time of your purchase, you learn that the membership is being offered at a "
        "discount of $4 off of the monthly membership price. You also learn that the personal "
        "training sessions come with one of two types of price promotions, and that you can "
        "choose which type of price promotion you would like to receive.",
        "$4 off of the monthly gym membership",
    ),
    "high": (
        "Imagine that you have just decided to buy a 1-year membership to a gym close to your "
        "home, as well as a week's worth of personal training sessions. The membership usually "
        "costs $480/year, and a week's worth of personal training sessions costs $50.",
        "At the time of your purchase, you learn that the membership is being offered at a "
        "discount of $48 off of the yearly membership price. You also learn that the personal "
        "training sessions come with one of two types of price promotions, and that you can "
        "choose which type of price promotion you would like to receive.",
        "$48 off of the yearly gym membership",
    ),
}
GYM_SPECIFIC = (
    "Specifically, when purchasing the gym membership and the personal training sessions, you "
    "can choose between receiving one of the following two price promotions:"
)
GYM_SURE = "$5 off of the personal training sessions"
GYM_UNCERTAIN = "a 10% chance to get the personal training sessions for free"
GYM_WHICH = "Which promotion would you like to receive?"
WEALTH_Q = "In this scenario, how wealthy would you feel?"
CONSIDER = "Please consider this scenario:"


def gym_screen(context: str, sdf: int, prefix: bool) -> str:
    p1, p2, ctx = GYM[context]
    first, second = (GYM_SURE, GYM_UNCERTAIN) if sdf else (GYM_UNCERTAIN, GYM_SURE)
    parts = ([CONSIDER] if prefix else []) + [
        p1,
        p2,
        GYM_SPECIFIC,
        table(f"{ctx} & {first}", f"{ctx} & {second}"),
    ]
    return "\n\n".join(parts)


def check_gym(tag: str, scenario_qids: dict[str, str], table_qids: list[str], prefix: bool) -> None:
    for context, qid in scenario_qids.items():
        p1, p2, _ = GYM[context]
        require(
            " ".join(([CONSIDER] if prefix else []) + [p1, p2]),
            question_text(tag, qid),
            f"{tag} {qid}",
        )
    for qid in table_qids:
        require(
            GYM_SPECIFIC
            + " Promotion A: Promotion B: ${e://Field/Context} & ${e://Field/Target_First} "
            "${e://Field/Context} & ${e://Field/Target_Second}",
            question_text(tag, qid),
            f"{tag} {qid}",
        )
    require_ed(tag, {"Target_First": GYM_SURE, "Target_Second": GYM_UNCERTAIN})
    require_ed(tag, {"Target_First": GYM_UNCERTAIN, "Target_Second": GYM_SURE})
    require_ed(
        tag,
        {"Context": "${e://Field/ContextDiscount} off of the ${e://Field/Period} gym membership"},
    )
    require_ed(tag, {"ContextDiscount": "$4", "Period": "monthly"})
    require_ed(tag, {"ContextDiscount": "$48", "Period": "yearly"})


def study3(which: str) -> Experiment:
    tag = "3"
    check_gym(tag, {"low": "QID60", "high": "QID80"}, ["QID79"], True)
    check_gym(tag, {"low": "QID84", "high": "QID85"}, ["QID86"], True)
    require(GYM_WHICH, question_text(tag, "QID83"), "3 QID83")
    check_rating_q(questions(tag)["QID83"], tag)
    require(WEALTH_Q, question_text(tag, "QID89"), "3 QID89")
    wq = questions(tag)["QID89"]
    assert norm(wq["Choices"]["1"]["Display"]) == "Not at all wealthy"
    assert norm(wq["Choices"]["7"]["Display"]) == "Extremely wealthy"
    arms: list[Arm] = []
    for c, context in ((1, "low"), (2, "high")):
        for sdf in (1, 0):
            for wqf in (1, 0):
                screen = gym_screen(context, sdf, True)
                other = GYM_WHICH if which == "wealth" else WEALTH_Q
                second = (wqf == 1) == (which == "rating")
                text = (
                    screen
                    if not second
                    else "\n\n".join(
                        [
                            screen,
                            f'You were asked "{other}" You were then shown the scenario again:',
                            screen,
                        ]
                    )
                )
                arms.append(
                    Arm(
                        raw={"Condition": c, "SureDiscountFirst": sdf, "WQfirst": wqf},
                        factors={
                            "context_price": context,
                            "order": ORDER[sdf],
                            "question_order": "wealth_first" if wqf else "promotion_first",
                        },
                        text=text,
                    )
                )
    common = (
        "Study 3, Prolific, March 2023. A gym membership costing $40/month (with $4 off) or "
        "$480/year (with $48 off), plus $50 of personal training with a choice of $5 off or a 10% "
        "chance it is free. The wealth question and the promotion choice were asked on separate "
        "pages, in a randomised and recorded order (WQfirst); the second-asked one's condition "
        "repeats the scenario as the second page did, after the narration "
        "'You were asked \"<earlier question>\" You were then shown the scenario again:' (ours). "
        "2,221 of 2,925 kept (do file: 274 duplicate IPs, 55 duplicate Prolific IDs, then those "
        "who did not answer the rating)."
    )
    if which == "rating":
        return Experiment(
            name="study3",
            tag=tag,
            title="Gym membership: a sure $5 off training or a 10% chance it is free, after a small or large membership discount (Study 3)",
            design="2 (context: $40/month with $4 off / $480/year with $48 off) x 2 (option order) x 2 (question order), all recorded; 6-point preference between the two promotions",
            source_vars=["Condition", "SureDiscountFirst", "WQfirst"],
            factors=["context_price", "order", "question_order"],
            arms=arms,
            outcomes=[Outcome("rating", GYM_WHICH, RATING_SCALE)],
            notes=common
            + " Rating: 1 = Definitely Promotion A (shown first) to 6 = Definitely Promotion B.",
            data_cols={"rating": "Rating"},
        )
    return Experiment(
        name="study3_wealth",
        tag=tag,
        title="Gym membership: how wealthy would you feel, after a small or large membership discount (Study 3)",
        design="2 (context: $40/month with $4 off / $480/year with $48 off) x 2 (option order) x 2 (question order), all recorded; 7-point felt wealth",
        source_vars=["Condition", "SureDiscountFirst", "WQfirst"],
        factors=["context_price", "order", "question_order"],
        arms=arms,
        outcomes=[
            Outcome(
                "wealthy",
                WEALTH_Q,
                {
                    "min": 1,
                    "max": 7,
                    "min_label": "Not at all wealthy",
                    "max_label": "Extremely wealthy",
                },
            )
        ],
        notes=common
        + " Built separately from the rating because the answer type differs (ledger 147).",
        data_cols={"wealthy": "Wealthy"},
    )


def study4() -> Experiment:
    tag = "4"
    qs = questions(tag)
    sd = {
        1: ("low", "percent", "10%"),
        2: ("low", "dollar", "$1.10"),
        3: ("high", "percent", "10%"),
        4: ("high", "dollar", "$31.10"),
    }
    for c, (price, framing, d) in sd.items():
        require_ed(
            tag,
            {
                "Condition": str(c),
                "Price": price.title(),
                "Framing": "Percent" if framing == "percent" else "USD",
                "SureDiscount": d,
            },
        )
    require_ed(
        tag,
        {
            "First": "${e://Field/SureDiscount} off of the price of the product",
            "Second": UNCERTAIN_PRODUCT,
        },
    )
    require_ed(
        tag,
        {
            "First": UNCERTAIN_PRODUCT,
            "Second": "${e://Field/SureDiscount} off of the price of the product",
        },
    )
    for qid, price in (("QID60", "$11"), ("QID66", "$311")):
        require(
            product_source(price, "First", "Second") + " " + WHICH_PROMOTION,
            question_text(tag, qid),
            f"4 {qid}",
        )
        check_rating_q(qs[qid], tag)
    arms = []
    for c, (price, framing, d) in sd.items():
        for sdf in (1, 0):
            s = f"{d} off of the price of the product"
            first, second = (s, UNCERTAIN_PRODUCT) if sdf else (UNCERTAIN_PRODUCT, s)
            arms.append(
                Arm(
                    raw={"Condition": c, "SureDiscountFirst": sdf},
                    factors={"price": price, "framing": framing, "order": ORDER[sdf]},
                    text=product_screen("$11" if price == "low" else "$311", first, second),
                )
            )
    return Experiment(
        name="study4",
        tag=tag,
        title="A product at $11 or $311: 10% off (as % or $) or a 10% chance it is free (Study 4)",
        design="2 (price $11 / $311) x 2 (sure discount framed in % / $) x 2 (option order, recorded); 6-point preference between the two promotions",
        source_vars=["Condition", "SureDiscountFirst"],
        factors=["price", "framing", "order"],
        arms=arms,
        outcomes=[Outcome("rating", WHICH_PROMOTION, RATING_SCALE)],
        notes=(
            "Study 4, MTurk, April 2018. Promotion A is the option shown first (SureDiscountFirst). "
            "2,371 of 2,399 kept (do file: 28 duplicate IPs)."
        ),
        data_cols={"rating": "Rating"},
    )


PRETEST = [
    "Imagine you are about to buy a product.",
    "The original price of the product is {price}.",
    "You learn that the product comes with the following price discount:",
    "You will get {d} off of the price of the product.",
    "The price discount will be applied to the original price of the product ({price}).",
]
SIZE_Q = "How small or large does this discount feel to you?"


def study4_pretest() -> Experiment:
    tag = "4_Pretest"
    cells = {
        1: ("QID60", "low", "percent", "$11", "10%"),
        2: ("QID75", "low", "dollar", "$11", "$1.10"),
        3: ("QID76", "high", "percent", "$311", "10%"),
        4: ("QID77", "high", "dollar", "$311", "$31.10"),
    }
    arms = []
    for c, (qid, price, framing, p, d) in cells.items():
        paras = [x.format(price=p, d=d) for x in PRETEST]
        require(" ".join(paras), question_text(tag, qid), f"pretest {qid}")
        assert f'"RightOperand": "{c}"' in json.dumps(questions(tag)[qid]["DisplayLogic"])
        arms.append(
            Arm(
                raw={"Condition": c},
                factors={"price": price, "framing": framing},
                text="\n\n".join(paras),
            )
        )
    q = questions(tag)["QID74"]
    require(SIZE_Q, norm(q["QuestionText"]), "pretest QID74")
    assert (
        norm(q["Choices"]["13"]["Display"]) == "Very small"
        and norm(q["Choices"]["19"]["Display"]) == "Very large"
    )
    return Experiment(
        name="study4_pretest",
        tag=tag,
        title="How large does 10% off feel, as % or $, on a $11 or $311 product (Study 4 pretest)",
        design="2 (price $11 / $311) x 2 (discount framed in % / $) between subjects; 7-point perceived size of the discount",
        source_vars=["Condition"],
        factors=["price", "framing"],
        arms=arms,
        outcomes=[Outcome("size", SIZE_Q, SIZE_SCALE)],
        notes=(
            "Pretest for Study 4, MTurk, April 2018. One sure discount, no choice. 867 of 905 kept "
            "(do file: 20 duplicate IPs, 18 IPs from an earlier study)."
        ),
        data_cols={"size": "Rating"},
    )


def study5(which: str) -> Experiment:
    tag = "5"
    qs = questions(tag)
    sd = {1: ("percent", "10%"), 2: ("dollar", "$1.10")}
    for c, (framing, d) in sd.items():
        require_ed(
            tag,
            {
                "Condition": str(c),
                "SureFraming": "Percent" if framing == "percent" else "USD",
                "SureDiscountLow": d,
            },
        )
    require_ed(
        tag,
        {
            "LowFirst": "${e://Field/SureDiscountLow} off of the price of the product",
            "LowSecond": UNCERTAIN_PRODUCT,
        },
    )
    require_ed(
        tag,
        {
            "LowFirst": UNCERTAIN_PRODUCT,
            "LowSecond": "${e://Field/SureDiscountLow} off of the price of the product",
        },
    )
    require(
        product_source("$11", "LowFirst", "LowSecond") + " " + WHICH_PROMOTION,
        question_text(tag, "QID74"),
        "5 QID74",
    )
    check_rating_q(qs["QID74"], tag)
    reminder_head = (
        "Please consider the promotions that you just saw again and answer the questions below:"
    )
    require(
        " ".join(
            [
                reminder_head,
                PRODUCT_PRICE.format(price="$11"),
                PRODUCT_CHOOSE,
                "Promotion A: Promotion B: ${e://Field/LowFirst} ${e://Field/LowSecond}",
                PRODUCT_APPLIED.format(price="$11"),
            ]
        ),
        question_text(tag, "QID60"),
        "5 QID60",
    )
    size_src = (
        "Consider the sure discount of ${e://Field/SureDiscountLow} off of the price of the product. "
        + SIZE_Q
    )
    require(size_src, question_text(tag, "QID75"), "5 QID75")
    arms = []
    for c, (framing, d) in sd.items():
        for sdf in (1, 0):
            s = f"{d} off of the price of the product"
            first, second = (s, UNCERTAIN_PRODUCT) if sdf else (UNCERTAIN_PRODUCT, s)
            screen = product_screen("$11", first, second)
            if which == "size":
                reminder = "\n\n".join(
                    [
                        reminder_head,
                        PRODUCT_PRICE.format(price="$11"),
                        PRODUCT_CHOOSE,
                        table(first, second),
                        PRODUCT_APPLIED.format(price="$11"),
                    ]
                )
                text = "\n\n".join([screen, f'You were asked "{WHICH_PROMOTION}"', reminder])
            else:
                text = screen
            arms.append(
                Arm(
                    raw={"Condition": c, "SureDiscountFirst": sdf},
                    factors={"framing": framing, "order": ORDER[sdf]},
                    text=text,
                    question=(
                        size_src.replace("${e://Field/SureDiscountLow}", d)
                        if which == "size"
                        else None
                    ),
                )
            )
    common = (
        'Study 5, Prolific, April 2023. An $11 product; 10% off framed as "10%" or "$1.10", '
        "against a 10% chance it is free; option order randomised and recorded "
        "(SureDiscountFirst). 1,187 of 1,227 kept (do file: 18 duplicate IPs, 2 duplicate "
        "Prolific IDs, 20 who did not answer)."
    )
    if which == "rating":
        return Experiment(
            name="study5",
            tag=tag,
            title="An $11 product: 10% off framed as % or $, or a 10% chance it is free (Study 5)",
            design="2 (sure discount framed as 10% / $1.10) x 2 (option order, recorded); 6-point preference between the two promotions",
            source_vars=["Condition", "SureDiscountFirst"],
            factors=["framing", "order"],
            arms=arms,
            outcomes=[Outcome("rating", WHICH_PROMOTION, RATING_SCALE)],
            notes=common,
            data_cols={"rating": "Rating"},
        )
    return Experiment(
        name="study5_size",
        tag=tag,
        title="An $11 product: how large does 10% off feel, framed as % or $, after the choice (Study 5)",
        design="2 (sure discount framed as 10% / $1.10) x 2 (option order, recorded); 7-point perceived size of the sure discount, asked after the choice",
        source_vars=["Condition", "SureDiscountFirst"],
        factors=["framing", "order"],
        arms=arms,
        outcomes=[
            Outcome("size", "How small or large does this discount feel to you?", SIZE_SCALE)
        ],
        notes=common
        + (
            " The size question came on the next page, after the choice; its condition is "
            "the choice screen, then 'You were asked \"Which price promotion would you "
            "like to receive?\"' (ours), then that page's reminder word-for-word. Its "
            "wording pipes in the discount (10% or $1.10), so the question is set per arm."
        ),
        data_cols={"size": "Size"},
    )


def s1_family(tag: str) -> Experiment:
    qs = questions(tag)
    if tag == "S1A":
        stem = (
            "Imagine you had to select one of the following three rooms for an upcoming trip to "
            "Chicago, which would you choose?"
        )
        sure = "Note: The Buckingham is offering a {p} discount to reservations made in the next hour and that discount is not reflected in the price below."
        unc = "Note: The Buckingham is offering a promotion where all rooms booked in the next hour have a {p} chance of being entirely free."
        cells = {
            1: ("QID43", "none", "none"),
            2: ("QID47", "sure", "1%"),
            3: ("QID48", "sure", "10%"),
            4: ("QID49", "uncertain", "1%"),
            5: ("QID50", "uncertain", "10%"),
        }
    else:
        stem = (
            "Imagine you had to select one of the following three hotel rooms for an upcoming trip "
            "to Chicago. Which hotel room would you choose?"
        )
        sure = "Note: The Ramada Plaza is offering a promotion. All rooms booked in the next hour will get a {p} discount and that discount is not reflected in the price below."
        unc = "Note: The Ramada Plaza is offering a promotion. All rooms booked in the next hour will have a {p} chance of being entirely free."
        cells = {
            1: ("QID43", "none", "none"),
            2: ("QID47", "sure", "1%"),
            3: ("QID48", "sure", "5%"),
            4: ("QID49", "sure", "10%"),
            5: ("QID50", "uncertain", "1%"),
            6: ("QID53", "uncertain", "5%"),
            7: ("QID54", "uncertain", "10%"),
        }
    arms = []
    for c, (qid, kind, p) in cells.items():
        src = question_text(tag, qid)
        require(stem, src, f"{tag} {qid}")
        assert f'"RightOperand": "{c}"' in json.dumps(qs[qid]["DisplayLogic"]), (tag, qid)
        note = None if kind == "none" else (sure if kind == "sure" else unc).format(p=p)
        if note:
            require(note, src, f"{tag} {qid}")
        imgs = choice_images(tag, qid)
        keys = [graphic_key(i) for i in imgs]
        body = "\n\n".join(listing(i) for i in imgs)
        arms.append(
            Arm(
                raw={"Condition": c},
                factors={"promotion": kind, "size": p},
                text=(note + "\n\n" + body) if note else body,
                options=[HOTEL_NAME[k] for k in keys],
            )
        )
    assert len({tuple(a.options or []) for a in arms}) == 1
    return arms_to_s1(tag, stem, arms)


def arms_to_s1(tag: str, stem: str, arms: list[Arm]) -> Experiment:
    if tag == "S1A":
        return Experiment(
            name="s1a",
            tag=tag,
            title="Three Chicago hotels: the first offers nothing, 1% or 10% off, or a 1% or 10% chance the room is free (Study S1a)",
            design="5 conditions between subjects (no promotion; sure 1% / 10%; chance-for-free 1% / 10%) on the first of three hotels; choice of hotel",
            source_vars=["Condition"],
            factors=["promotion", "size"],
            arms=arms,
            outcomes=[Outcome("choice", stem, {"min": 1, "max": 3, "nominal": True})],
            notes=(
                "Study S1a, MTurk, January 2018. Three hotel listings (pictures; printed words "
                "transcribed, price column first as it sits on the left), fixed order; the promoted "
                "hotel is The Buckingham, listed first. All 1,502 kept (the do file excludes no one; "
                "it sets aside age 332 for the age summary only, left blank here)."
            ),
            data_cols={"choice": "Choice"},
        )
    return Experiment(
        name="s1b",
        tag=tag,
        title="Three Chicago hotels: the first offers nothing, 1%, 5% or 10% off, or the same chance the room is free (Study S1b)",
        design="7 conditions between subjects (no promotion; sure 1% / 5% / 10%; chance-for-free 1% / 5% / 10%) on the first of three hotels; choice of hotel",
        source_vars=["Condition"],
        factors=["promotion", "size"],
        arms=arms,
        outcomes=[Outcome("choice", stem, {"min": 1, "max": 3, "nominal": True})],
        notes=(
            "Study S1b, MTurk, January-February 2018. Three hotel listings (pictures; printed words "
            "transcribed), fixed order; the promoted hotel is the Ramada Plaza, listed first. 2,039 "
            "of 2,102 kept (do file: 32 duplicate IPs, 31 IPs from an earlier study)."
        ),
        data_cols={"choice": "Choice"},
    )


def s1c() -> Experiment:
    tag = "S1C"
    stem = (
        "Imagine you had to select one of the following three hotel rooms for an upcoming trip to "
        "Chicago. Which hotel room would you choose?"
    )
    require(
        stem + " (Please click on the hotel to make your selection.) ${e://Field/Note}",
        question_text(tag, "QID43"),
        "S1C QID43",
    )
    imgs = choice_images(tag, "QID43")
    names = {1: "The Ramada Plaza", 2: "The Edward Hotel", 3: "The Best Western Plus"}
    body = "\n\n".join(listing(i) for i in imgs)
    arms = []
    c = 0
    for hotel in (1, 2, 3):
        for kind in ("sure", "uncertain"):
            for p in ("1%", "10%"):
                c += 1
                note = (
                    f"Note: {names[hotel]} is offering a promotion. All rooms booked in the next hour will "
                    + (
                        f"get a {p} discount and that discount is not reflected in the price below."
                        if kind == "sure"
                        else f"have a {p} chance of being entirely free."
                    )
                )
                require_ed(
                    tag,
                    {
                        "Condition": str(c),
                        "Note": note,
                        "Hotel": str(hotel),
                        "Sure": "1" if kind == "sure" else "0",
                        "Small": "1" if p == "1%" else "0",
                    },
                )
                arms.append(
                    Arm(
                        raw={"Condition": c},
                        factors={
                            "promoted_hotel": HOTEL_NAME[graphic_key(imgs[hotel - 1])],
                            "promotion": kind,
                            "size": p,
                        },
                        text=note + "\n\n" + body,
                        options=[HOTEL_NAME[graphic_key(i)] for i in imgs],
                    )
                )
    return Experiment(
        name="s1c",
        tag=tag,
        title="Three Chicago hotels, one of them offering 1% or 10% off or the same chance the room is free (Study S1c)",
        design="3 (promoted hotel) x 2 (sure discount / chance for free) x 2 (1% / 10%) between subjects; choice of hotel",
        source_vars=["Condition"],
        factors=["promoted_hotel", "promotion", "size"],
        arms=arms,
        outcomes=[Outcome("choice", stem, {"min": 1, "max": 3, "nominal": True})],
        notes=(
            "Study S1c, Prolific, February 2023. Same three listings as S1b, fixed order; which hotel "
            "carries the promotion is randomised. Note text read from the flow and checked against "
            "the deposit's Note column. 2,049 of 2,136 kept (do file: 60 duplicate IPs, 2 duplicate "
            "Prolific IDs, 25 who did not choose)."
        ),
        data_cols={"choice": "Choice"},
    )


def s2() -> Experiment:
    tag = "S2"
    stem = (
        "Imagine you had to select one of the following three hotel rooms for an upcoming trip to "
        "the Jersey Shore. Which hotel room would you choose?"
    )
    notes = {
        "sure": "Note: The Econo Lodge is offering a promotion. All rooms booked in the next hour will get a 10% discount and that discount is not reflected in the price below.",
        "uncertain": "Note: The Econo Lodge is offering a promotion. All rooms booked in the next hour will have a 10% chance of being entirely free.",
    }
    qid_of = {"low": "QID43", "high": "QID47"}
    cells = {
        1: ("low", "sure"),
        2: ("low", "uncertain"),
        3: ("high", "sure"),
        4: ("high", "uncertain"),
    }
    arms = []
    for c, (price, kind) in cells.items():
        require_ed(
            tag,
            {
                "Condition": str(c),
                "Price": price.title(),
                "Discount": "Sure" if kind == "sure" else "Probabilistic",
                "DiscountText": notes[kind],
            },
        )
        qid = qid_of[price]
        require(
            stem + " (Please click on the hotel to make your selection.) ${e://Field/DiscountText}",
            question_text(tag, qid),
            f"S2 {qid}",
        )
        assert price.title() in json.dumps(questions(tag)[qid]["DisplayLogic"])
        imgs = choice_images(tag, qid)
        arms.append(
            Arm(
                raw={"Condition": c},
                factors={"price": price, "promotion": kind},
                text=notes[kind] + "\n\n" + "\n\n".join(listing(i) for i in imgs),
                options=[HOTEL_NAME[graphic_key(i)] for i in imgs],
            )
        )
    return Experiment(
        name="s2",
        tag=tag,
        title="Three Jersey Shore hotels at one-night or ten-night prices, the first offering 10% off or a 10% chance the room is free (Study S2)",
        design="2 (price for one night / ten nights) x 2 (sure 10% / 10% chance for free) between subjects; choice of hotel",
        source_vars=["Condition"],
        factors=["price", "promotion"],
        arms=arms,
        outcomes=[Outcome("choice", stem, {"min": 1, "max": 3, "nominal": True})],
        notes=(
            "Study S2, MTurk, March 2018. Three hotel listings (pictures; printed words transcribed), "
            "fixed order; the promoted hotel is the Econo Lodge, listed first; prices $48/$44/$42 for "
            'one night or $480/$440/$420 as "Your 10 night total". 2,302 of 2,417 kept (do file: 46 '
            "duplicate IPs, 69 IPs from an earlier study)."
        ),
        data_cols={"choice": "Choice"},
    )


def s3() -> Experiment:
    tag = "S3"
    check_gym(tag, {"low": "QID60", "high": "QID80"}, ["QID79"], False)
    require(GYM_WHICH, question_text(tag, "QID79"), "S3 QID79")
    check_rating_q(questions(tag)["QID79"], tag)
    arms = []
    for c, context in ((1, "low"), (2, "high")):
        for sdf in (1, 0):
            arms.append(
                Arm(
                    raw={"Condition": c, "SureDiscountFirst": sdf},
                    factors={"context_price": context, "order": ORDER[sdf]},
                    text=gym_screen(context, sdf, False),
                )
            )
    return Experiment(
        name="s3",
        tag=tag,
        title="Gym membership: a sure $5 off training or a 10% chance it is free, after a small or large membership discount (Study S3)",
        design="2 (context: $40/month with $4 off / $480/year with $48 off) x 2 (option order, recorded); 6-point preference between the two promotions",
        source_vars=["Condition", "SureDiscountFirst"],
        factors=["context_price", "order"],
        arms=arms,
        outcomes=[Outcome("rating", GYM_WHICH, RATING_SCALE)],
        notes=(
            "Study S3, MTurk, May 2018: Study 3's gym scenario without the wealth question. 1,188 of "
            "1,203 kept (do file: 15 duplicate IPs)."
        ),
        data_cols={"rating": "Rating"},
    )


def s4() -> Experiment:
    tag = "S4"
    qs = questions(tag)
    require_ed(tag, {"Condition": "1", "ContextPrice": "Low", "ContextDiscount": "$1.50"})
    require_ed(tag, {"Condition": "2", "ContextPrice": "High", "ContextDiscount": "$31.50"})
    sure_t, sure_c = (
        "$1.10 off of the price of the product",
        "${e://Field/ContextDiscount} off of the price of the product",
    )
    require_ed(
        tag,
        {
            "Target_First": sure_t,
            "Context_First": sure_c,
            "Target_Second": UNCERTAIN_PRODUCT,
            "Context_Second": UNCERTAIN_PRODUCT,
        },
    )
    require_ed(
        tag,
        {
            "Target_First": UNCERTAIN_PRODUCT,
            "Context_First": UNCERTAIN_PRODUCT,
            "Target_Second": sure_t,
            "Context_Second": sure_c,
        },
    )
    for qid, price, f in (
        ("QID75", "$15", "Context"),
        ("QID76", "$315", "Context"),
        ("QID60", "$11", "Target"),
    ):
        require(
            product_source(price, f"{f}_First", f"{f}_Second") + " " + WHICH_PROMOTION,
            question_text(tag, qid),
            f"S4 {qid}",
        )
        check_rating_q(qs[qid], tag)
    arms = []
    for c, (context, price, d) in {
        1: ("low", "$15", "$1.50"),
        2: ("high", "$315", "$31.50"),
    }.items():
        for sdf in (1, 0):
            cs, ts = f"{d} off of the price of the product", sure_t
            cf, csec = (cs, UNCERTAIN_PRODUCT) if sdf else (UNCERTAIN_PRODUCT, cs)
            tf, tsec = (ts, UNCERTAIN_PRODUCT) if sdf else (UNCERTAIN_PRODUCT, ts)
            first_screen = product_screen(price, cf, csec)
            target = "\n\n".join(
                [
                    first_screen,
                    f'You were asked "{WHICH_PROMOTION}" You were then shown another scenario:',
                    product_screen("$11", tf, tsec),
                ]
            )
            arms.append(
                Arm(
                    raw={"Condition": c, "SureDiscountFirst": sdf},
                    factors={"context_price": context, "order": ORDER[sdf]},
                    text=first_screen,
                    item_text={1: target},
                )
            )
    return Experiment(
        name="s4",
        tag=tag,
        title="A $15 or $315 product, then an $11 one: a sure discount or a 10% chance it is free (Study S4)",
        design="2 (first scenario: $15 with $1.50 off / $315 with $31.50 off) x 2 (option order, recorded); 6-point preference in each of two scenarios, the $11 one always second",
        source_vars=["Condition", "SureDiscountFirst"],
        factors=["context_price", "order"],
        arms=arms,
        outcomes=[
            Outcome("context_rating", WHICH_PROMOTION, RATING_SCALE),
            Outcome("rating", WHICH_PROMOTION, RATING_SCALE),
        ],
        notes=(
            "Study S4, MTurk, May 2018. Two scenarios in fixed order: the context product ($15 or $315), "
            "then the $11 target. Task 0 is the first (ContextRating); task 1 the second (Rating), whose "
            "condition is the first screen, then 'You were asked \"Which price promotion would you like "
            "to receive?\" You were then shown another scenario:' (ours), then the target screen. "
            '"Click >> to see the next scenario." is dropped. The same option order applied to both '
            "scenarios. 984 of 996 kept (do file: 12 duplicate IPs)."
        ),
        data_cols={"context_rating": "ContextRating", "rating": "Rating"},
    )


S5_INTRO = [
    "Imagine you are going on a 7-days vacation to Spain and are debating between a culture vacation in "
    "the city of Barcelona and a beach vacation in a coastal resort approximately 100 miles south of Barcelona.",
    "You are going on Kayak.com to compare hotel prices and have found one hotel in Barcelona and one in the "
    "beach resort that you would consider staying at. They both have 4 stars.",
    "Below are their prices/night.",
]
BEACH = ["Beach Vacation in a Coastal Resort", "Beach Resort Hotel", "$200"]
CITY = {
    "none": ["$200"],
    "sure": [
        "****Special Promotion (instantly taken at check-out):",
        "$180 (10% off regular price $200)",
    ],
    "chance_free": [
        "****Special Promotion (instantly taken at check-out; you play an electronic slot machine to find out if you win):",
        "10% chance to pay $0 (free)",
        "90% chance to pay $200 (regular price)",
    ],
    "chance_free_wheel": [
        "****Special Promotion (instantly taken at check-out; you spin a wheel to find out if you win):",
        "10% chance to pay $0 (free)",
        "90% chance to pay $200 (regular price)",
    ],
    "chance_half": [
        "****Special Promotion (instantly taken at check-out; you play an electronic slot machine to find out if you win):",
        "20% chance to pay $100",
        "80% chance to pay $200 (regular price)",
    ],
}
S5_QIDS = {  # condition -> (city first, beach first)
    1: ("QID8", "QID40"),
    2: ("QID25", "QID39"),
    3: ("QID23", "QID37"),
    4: ("QID35", "QID36"),
    5: ("QID34", "QID38"),
}


def s5() -> Experiment:
    tag = "S5"
    qs = questions(tag)
    require(" ".join(S5_INTRO), question_text(tag, "QID1"), "S5 QID1")
    kinds = {1: "none", 2: "sure", 3: "chance_free", 4: "chance_free_wheel", 5: "chance_half"}
    arms = []
    for c, kind in kinds.items():
        city = ["Culture Vacation in the City of Barcelona", "Barcelona City Hotel", *CITY[kind]]
        for city_first, qid in zip((1, 0), S5_QIDS[c], strict=True):
            q = qs[qid]
            require("Which vacation do you choose?", norm(q["QuestionText"]), f"S5 {qid}")
            dl = json.dumps(q["DisplayLogic"])
            assert f'"RightOperand": "{c}"' in dl and f'"RightOperand": "{city_first}"' in dl, (
                qid,
                c,
            )
            blocks = [city, BEACH] if city_first else [BEACH, city]
            for k, block in zip(("1", "2"), blocks, strict=True):
                assert norm(q["Choices"][k]["Display"]) == " ".join(block), (qid, k)
            arms.append(
                Arm(
                    raw={"Condition": c, "CityFirst": city_first},
                    factors={
                        "promotion": kind,
                        "order": "city_first" if city_first else "beach_first",
                    },
                    text="\n\n".join([*S5_INTRO, "\n".join(blocks[0]), "\n".join(blocks[1])]),
                    options=[blocks[0][0], blocks[1][0]],
                )
            )
    return Experiment(
        name="s5",
        tag=tag,
        title="Barcelona city hotel or a beach resort, the city one at full price, 10% off, or a chance to pay nothing or half (Study S5)",
        design="5 promotion conditions on the city hotel (none; sure 10% off; 10% chance free by slot machine; by wheel; 20% chance to pay half) x 2 (option order, recorded); choice of hotel",
        source_vars=["Condition", "CityFirst"],
        factors=["promotion", "order"],
        arms=arms,
        outcomes=[
            Outcome(
                "choice", "Which vacation do you choose?", {"min": 1, "max": 2, "nominal": True}
            )
        ],
        notes=(
            "Study S5, MTurk, January 2018. Two hotels, Barcelona city or a beach resort, $200 a night; the "
            "city one carries the promotion. Options in each respondent's recorded order (CityFirst); "
            "Choice 1 = first option shown. The slot-machine picture beside the odds in conditions 3 and 5 "
            "is not rendered. The 'Why did you choose the Barcelona City Hotel?' check-all item (city "
            "choosers only) and the two general vacation-liking items are not built. 1,986 of 2,011 kept "
            "(do file: 25 failed the attention check, a pre-registered exclusion)."
        ),
        data_cols={"choice": "Choice"},
        rejected={},
    )


# Not built (rich, 19 Nov 2026): Studies 1, 2, S1a, S1b, S1c and S2 carry their price, or
# the hotels people chose between, only inside booking-site screenshots, so their condition
# text would rest on words transcribed by hand from pictures. Their builders (study1,
# study2, s1_family, s1c, s2) and LISTING stay below for the record; nothing calls them.
# S5 also not built: its slot-machine arms show a picture of reels spelling "WIN" that the
# wheel arm does not, so the picture is part of the manipulation (checker, 19 Nov 2026).
NOT_BUILT = ("study1", "study2", "s1a", "s1b", "s1c", "s2", "s5")


def experiments() -> list[Experiment]:
    return [
        study3("rating"),
        study3("wealth"),
        study4(),
        study4_pretest(),
        study5("rating"),
        study5("size"),
        s3(),
        s4(),
    ]


# ---------------------------------------------------------------------------
# Coded data
# ---------------------------------------------------------------------------

CODED = {  # tag -> coded file stem; built studies only (see NOT_BUILT)
    "3": "study3",
    "4": "study4",
    "4_Pretest": "study4_pretest",
    "5": "study5",
    "S3": "s3",
    "S4": "s4",
}


def data_file(tag: str) -> str:
    return f"{STUDY_ID}_{CODED[tag]}.csv"


def prep(tag: str) -> pd.DataFrame:
    """One coded row per kept respondent: assignment, answers, age, gender."""
    check_qsf_pair(tag)
    df = read_study(tag)
    idcol = "Id" if "Id" in df.columns else "No"
    out = pd.DataFrame({"pid": [f"{CODED[tag]}_{int(i)}" for i in df[idcol]]})
    exps = [e for e in experiments() if e.tag == tag]
    for v in exps[0].source_vars:
        assert df[v].notna().all(), (tag, v)
        out[v] = df[v].astype(int)
    for e in exps:
        for coded, src in e.data_cols.items():
            out[coded] = pd.to_numeric(df[src], errors="coerce").astype("Int64")
    if tag == "3":  # the deposit's own piped wording agrees with the arm
        for _, r in df.iterrows():
            first = GYM_SURE if r["SureDiscountFirst"] == 1 else GYM_UNCERTAIN
            assert (
                r["Target_First"] == first
                and r["Context"] == GYM[{1: "low", 2: "high"}[int(r["Condition"])]][2]
            )
    if tag == "5":
        for _, r in df.iterrows():
            d = "10%" if r["Condition"] == 1 else "$1.10"
            s = f"{d} off of the price of the product"
            assert r["First"] == (s if r["SureDiscountFirst"] == 1 else UNCERTAIN_PRODUCT)
    if tag == "S1C":
        by_c = {a.raw["Condition"]: a.text.split("\n\n")[0] for a in exps[0].arms}
        for _, r in df.iterrows():
            assert r["Note"] == by_c[int(r["Condition"])]
    out = pd.concat([out, persona_cols(tag, df)], axis=1)
    return out.sort_values("pid").reset_index(drop=True)


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
        items: dict[int, Any] = {}
        for t, o in enumerate(e.outcomes):
            cell: dict[str, Any] = {}
            if a.options:
                cell["outcome_question"] = opt_question(o.question, a.options)
            elif a.question:
                cell["outcome_question"] = a.question
            if t in a.item_text:
                cell["condition_text"] = a.item_text[t]
            if cell:
                items[t] = cell
        if items:
            arm["items"] = items
        arms.append(arm)
    notes = (
        f"{PAPER}\n\nGENERATED by scripts/gen_researchbox3299.py; every judgement is in its "
        f"docstring. {e.notes}\n\nWording from the .qsf (Qualtrics_Study_{e.tag}.qsf; its twin "
        "export has the same questions, see the docstring). Typography normalised (curly quotes, "
        "non-breaking and zero-width spaces). Persona: age (years; outside 18-100 left blank) and "
        "gender, labels from the .qsf's own choices."
    )
    cond: dict[str, Any] = {"source_vars": e.source_vars, "factors": e.factors, "arms": arms}
    if e.rejected:
        cond["considered_and_rejected"] = e.rejected
    return {
        "study_id": STUDY_ID,
        "source": "researchbox",
        "experiment": e.name,
        "title": e.title,
        "data_file": data_file(e.tag),
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": "pid",
        "notes": notes,
        "condition": cond,
        "outcomes": [
            {"var": o.var, "task_num": t, "question": o.question, "scale": o.scale}
            for t, o in enumerate(e.outcomes)
        ],
        "response_recode": {
            k: k for k in range(e.outcomes[0].scale["min"], e.outcomes[0].scale["max"] + 1)
        },
        "missing_codes": [],
        "persona_map": {"age": "age", "gender": "gender"},
    }


def recipe_path(e: Experiment) -> Path:
    return RECIPES / f"{STUDY_ID}_{e.name}.yaml"


def render(e: Experiment) -> str:
    return yaml.safe_dump(recipe(e), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prep", action="store_true", help="(re)write the coded .csv files")
    ap.add_argument("--check", action="store_true", help="exit 1 if any recipe differs")
    args = ap.parse_args()
    if args.prep:
        for tag in CODED:
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
