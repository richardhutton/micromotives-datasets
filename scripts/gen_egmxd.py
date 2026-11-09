#!/usr/bin/env python3
"""Write recipes/images/egmxd.yaml: a fast-food menu with QR codes, green or red labels.

Wolfson, TESS 1443 (fielded as NORC 9089.108), "Do Sustainability Labels Lead to More
Sustainable and Healthier Food Choices?". OSF egmxd, the TESS deposit wolfson1443.zip:
the data (9089_TESS-Wolfson108_20220420.dta), its codebook, the fielded questionnaire in
a simple and a programming version (9089.108_TESS-Wolfson_vFINALsimple.docx and
_v5clean.docx, "Q" and "PG" below), NORC's methods report, and the proposal
(Wolfson1443.pdf) with its description document (TESS-1443.R2 description.docx).

AmeriSpeak, US adults, web only (`SURV_MODE` 2 for all), English only, fielded
30 March to 13 April 2022. 5,055 completed; all 5,055 are in the file and all are built.
The menu task ran in Qualtrics (NORC's "trusted partner website"), the rest at NORC.

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* DESIGN. Three arms between people, the preload `P_COND` (codebook and PG's preload
  table: 1 Control, 2 Low impact, 3 High impact; 1,667 / 1,671 / 1,717).
  condition_num is P_COND - 1. Each arm saw one picture of a restaurant menu: the
  same fourteen items, prices and calories, differing only in their labels.
  Control: a QR code under every item and "Scan the QR code for more menu
  information." at the top. Low impact: a green "LOW CLIMATE IMPACT" label under
  the nine items without beef, and a green key at the top. High impact: a red "HIGH
  CLIMATE IMPACT" label under the five beef burgers, and a red key at the top. The
  three pictures are pixel-identical outside the top key and those label strips
  (checked in --catalogue). The factor `label` (control / low_impact / high_impact)
  is carried by the words as well as the picture, because the condition quotes
  every word printed on the menu (docs/CONVENTIONS.md, Image conditions).
* WHICH PICTURE IS WHICH CONDITION. Q's word/document.xml, read in order, has
  "[SHOW IF P_COND=1]" then "Q1A." then the picture r:embed rId10 (media/image3.png),
  P_COND=2 / Q1B. / rId11 (image4.png), P_COND=3 / Q1C. / rId12 (image5.png). PG
  embeds the same three files, byte for byte, as rId15 / rId16 / rId17 under the same
  three blocks, and names them in the line above each: "[9089.108_MenuA.png]",
  "[9089.108_MenuB.png]", "[9089.108_MenuC.png]". Both parsed here and asserted to
  agree. Two independent witnesses: the data's own timer labels name the arm of each
  block ("[Control] Timing", "[Low impact] Timing", "[High impact] Timing" on Q1A,
  Q1B, Q1C), and the proposal's description document prints the same three pictures
  under "MENU A: Control condition",
  "MENU B: Green positive sustainability label" and "MENU C: Red negative
  sustainability label": same size, every pixel within 8 of 255 levels of its own menu
  (another PNG encoding) and differing from the other two by up to 255 (checked in
  --catalogue). What cannot be shown is that these
  are the exact files Qualtrics displayed: NORC's MenuA/B/C.png are not in the
  deposit, so the pictures are Word's copies and may differ in resolution or
  encoding. Recorded in each catalogue entry's source.
* WORDS ON THE PICTURE. text_in_image transcribes every word legible in the file,
  from the top down and left to right, " / " between blocks; an item name that
  wraps onto two lines is joined with a space. Prices, calories and their "|" are
  kept as printed. The footprint icon on the key at the top carries the letters
  "CO2", legible there and transcribed; the same icon on the small labels under the
  items is a few pixels high and its letters cannot be read, so it is described, not
  transcribed. QR codes are pictures, not words. No brand name or logo is printed
  anywhere on the menu; the item names are the chain's own and are kept word-for-word.
* CONDITION. shared_context is the one line of the welcome screen that is not survey
  mechanics, "This survey is about restaurant menus." (Q and PG agree). Each arm is
  then OURS: 'The restaurant menu read, from top to bottom: "..." <image>', where the
  quotation is that arm's text_in_image word-for-word. Only the words "The restaurant
  menu read, from top to bottom:" are ours. That is the whole condition of task 0, the
  menu screen itself. Tasks 1-4 were asked on later screens, so each of their
  conditions (`items[task].condition_text`) is the menu followed by every question put
  to the respondent between the menu and that one, word-for-word and in the fielded
  order, narrated as asked and never as answered: 'You were asked: "Imagine you are
  ... before you choose." Then you were asked: "Did you notice any labels ...?"' and so
  on (docs/CONVENTIONS.md, Narrating what the respondent did; as
  del_sandbox_jul2020_global_goals). Only "You were asked:" and "Then you were
  asked:" are ours. The questions are quoted without their answer options, and nothing
  says what anyone chose. Q2's question is included because it was asked, although
  Q2 is not built. The order is fixed: no screen after the menu was randomised. The
  redirect screen DISPLAY1, the "No more than 1 choice may be selected" error and the
  soft prompt are mechanics and dropped.
* OUTCOMES. Five:
  - Task 0, the menu choice. The question is Q1A's words, word-for-word (Q1A, Q1B and
    Q1C are asserted identical, PG's copy too once its <u> tags and [SPACE] markers
    are removed), then the fourteen items enumerated, as a nominal scale requires:
    '1 means "Whopper"; ... 14 means "Side Garden Salad".' The menu was one clickable
    picture (Qualtrics "hot spot"), and the deposit records the click as fourteen 0/1
    variables per arm (Q1A_1 .. Q1A_14 for P_COND 1, Q1B_* for 2, Q1C_* for 3), each
    named in the codebook by its region, "[Whopper]" .. "[Side Garden Salad]". Every
    one of the 5,055 respondents has exactly one 1 among their own arm's fourteen and
    nothing in the other arms' (asserted). So --prep folds the fourteen into ONE
    variable, `MENU_ITEM` = the region clicked, 1-14 in the menu's reading order: an
    injective recode of what the respondent did, asked as one question. The region
    names are asserted equal to the item names transcribed from the picture.
    SocSci210 instead built fourteen yes/no rows per person ("Did you choose the
    Whopper?"); see ANSWER KEY.
  - Task 1, Q3: "How much do you agree or disagree with the following statement?"
    then the statement, joined with a space; 1-5, Strongly disagree .. Strongly agree,
    midpoint Neither agree nor disagree. The data codes it 2-6 (codebook and data
    agree), so the recode is 2->1 .. 6->5, by the questionnaire's own numbering.
  - Task 2, Q4: "How unhealthy or healthy do you think the meal you ordered is?";
    1-7, Very unhealthy .. Very healthy, midpoint Neither unhealthy nor healthy. "The
    meal you ordered" is the respondent's own task-0 choice, which no row states; the
    menu is in the condition, as it was in the respondent's memory.
  - Task 3, Q5: "How much do you agree or disagree with the following statement? I am
    concerned about climate change."; task 4, Q6: the same stem and "Making healthy
    food and beverage choices is important to me."; both 1-5 as Q3, coded 2-6 and
    recoded the same way. They are attitudes asked AFTER the labelled menu, so they
    can move with the label, and are built as outcomes (ruled 9 Nov 2026 by the
    coordinator, as vemrp's post-treatment environmental concern and 3xy9j's attitude
    items): the moderator precedent (yjvpn's Q7-Q9, zaqkm's contact item) covers facts
    about the respondent, not attitudes measured after treatment. The proposal's plan
    also names climate concern as a possible effect modifier; a reader using it that
    way must remember it was measured post-treatment. PG prints Q6 as
    "is<u>important</u>", which loses the space once the tags go; Q's "is important"
    is followed.
  Each was asked on its own screen after the menu, which was not shown again.
* NOT BUILT. Q2, "Did you notice any labels (other than calories) next to or below
  the menu items?", is the manipulation check: its answer is stated in the condition
  (docs/CONVENTIONS.md, attention and recall checks), 5,052 rows. SocSci210 did not
  build it either.
* WHO. All 5,055 completes; `CaseId` is the participant id. 98 "SKIPPED ON WEB" drops
  only that row (Q3: 2, Q4: 3, Q5: 4, Q6: 4; the menu: none).
* DATA FILE. pyreadstat cannot read this .dta at any encoding (Stata 117, latin-1
  strings with a cp1252 byte 0x92 in free text), and the pandas fallback in
  `sources.spss` returns labels in place of codes, which the melt cannot use. So
  --prep reads the .dta with pandas keeping the CODES, and writes egmxd_coded.sav
  with every column's codes, value labels and variable labels unchanged, plus
  `MENU_ITEM`; RELIGO (free text, not built) is left out. The round trip is asserted:
  every coded value in the .sav maps, through its value labels, to the label pandas
  decodes from the .dta.
* PERSONA. The standard AmeriSpeak preloads, b87sm's field set (also TESS on
  AmeriSpeak, 2021): AGE, GENDER, EDUC5, RACETHNICITY, INCOME (18 bands), MARITAL,
  EMPLOY, REGION4, HHSIZE, HOME_TYPE, HOUSING, METRO, INTERNET, PHONESERVICE,
  PartyID7, IDEO20, RELIG, ATTEND. Left absent: PartyID7 and IDEO20 -1 "Unknown"
  (17 and 62), RELIG and ATTEND 98 "SKIPPED ON WEB" (46 and 59), GENDER 0 "Unknown"
  (none here). Only codes this file labels are declared. Not mapped: STATE, REGION9,
  the banded duplicates AGE4 / AGE7 / INCOME4 / INCOME9, the household age counts,
  PartyID5. RELIG code 1's label is cut off at 80 characters in the .dta ("...
  Presbyterian, Pent"); `persona_label_rewrite` restores the whole answer from Q's
  demographic profile, with its own curly apostrophe (the religion crosswalk's
  spelling). RELIG 14 "Something else, please specify:" is a real answer wearing the
  text-box instruction; it is rewritten "Something else", as s6urt and 9xw67 carry it.
* UK FIT. rich approved this as an image build on 9 Nov 2026, accepting that the menu
  is a US fast-food chain's, priced in dollars. The questions name no US place, law or
  institution. US spellings are kept word-for-word. The sample is American.
* ANSWER KEY. SocSci210 holds this study (fetched 9 Nov 2026): 90,977 rows, 5,055
  people, three conditions, five tasks {0: 70,770, 1: 5,053, 2: 5,052, 3: 5,051,
  4: 5,051}. Their task 0 is our task 0 as fourteen yes/no rows per person (14 x
  5,055 = 70,770); their 5,055 "yes" rows, item by item and arm by arm, are exactly
  our task-0 answers. Their tasks 1 and 2 are our Q3 and Q4, the same rows and
  responses (their 1,666 / 1,670 / 1,717 per arm on Q3, ours too), and their tasks 3
  and 4 are our Q5 and Q6, cell for cell (1,666 / 1,669 / 1,716 per arm each). So
  90,977 - 70,770 + 5,055 = 25,262 = ours, every response agreeing; hence `comparable_to_socsci210: false`, with the
  reconciliation asserted in tests/test_gen_egmxd.py. Their conditions describe the
  menus in their own words ("You were shown a fast-food menu with a Quick Response
  code label next to every menu item"), not the menu's.
* NOT ASKED OF JEV. The assignment is the preload the questionnaire's own SHOW IF
  blocks name, the persona is b87sm's, and each outcome's non-answer is its own value
  label; no paid call.

    uv run python scripts/gen_egmxd.py --prep       # extract the menus, write the .sav
    uv run python scripts/gen_egmxd.py --catalogue  # (re)write this study's images.json entries
    uv run python scripts/gen_egmxd.py              # write the recipe
    uv run python scripts/gen_egmxd.py --check      # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import warnings
import zipfile
from html import unescape
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

STUDY = "egmxd"
RAW = REPO / "data" / "raw" / STUDY
DTA = RAW / "9089_TESS-Wolfson108_20220420.dta"
DATA_FILE = "egmxd_coded.sav"
CODED = RAW / DATA_FILE
SIMPLE = RAW / "9089.108_TESS-Wolfson_vFINALsimple.docx"
PROG = RAW / "9089.108_TESS-Wolfson_v5clean.docx"
DESCRIPTION = RAW / "TESS-1443.R2 description.docx"
IMAGES = RAW / "images"
RECIPE = REPO / "recipes" / "images" / f"{STUDY}.yaml"
LICENCE = (
    "None stated: the TESS deposit on OSF (egmxd, wolfson1443.zip) gives no reuse terms "
    "(OSF API, 2 Oct 2026: node_license null), and TESS has since suspended operations. "
    "Used with rich's ruling of 9 Nov 2026 that an unstated licence does not block an "
    "image build."
)

ID_VAR = "CaseId"
COND_VAR = "P_COND"
ITEM_VAR = "MENU_ITEM"

# The three menus: (key, P_COND, codebook label, block letter, PG's file name,
# description-document heading).
MENUS: list[tuple[str, int, str, str, str, str]] = [
    (
        "control",
        1,
        "Control",
        "A",
        "9089.108_MenuA.png",
        "MENU A: Control condition",
    ),
    (
        "low_impact",
        2,
        "Low impact",
        "B",
        "9089.108_MenuB.png",
        "MENU B: Green positive sustainability label",
    ),
    (
        "high_impact",
        3,
        "High impact",
        "C",
        "9089.108_MenuC.png",
        "MENU C: Red negative sustainability label",
    ),
]

# ---------------------------------------------------------------------------
# The words on the menu, transcribed from the pictures (docstring, WORDS ON THE
# PICTURE). The tiles, prices and calories are pixel-identical in all three files.
# ---------------------------------------------------------------------------

CALORIE_LINE = "2,000 calories a day is used for general nutrition advice, but calorie needs vary."
# (item name, price and calories as printed), in reading order. The names are also the
# hot-spot regions' names in the codebook, in the same order (asserted).
TILES: list[tuple[str, str]] = [
    ("Whopper", "$5.79 | 657 Cal."),
    ("Impossible Whopper", "$6.79 | 628 Cal."),
    ("Whopper Jr.", "$2.19 | 314 Cal."),
    ("Double Whopper with Cheese", "$6.69 | 939 Cal."),
    ("Bacon Double Cheeseburger", "$2.79 | 404 Cal."),
    ("Cheeseburger", "$1.29 | 283 Cal."),
    ("Crispy Chicken Sandwich", "$4.99 | 800 Cal."),
    ("Spicy Crispy Chicken Sandwich", "$4.99 | 950 Cal."),
    ("Original Chicken Sandwich", "$4.89 | 662 Cal."),
    ("Chicken Jr.", "$1.00 | 451 Cal."),
    ("10 Pc Nuggets", "$1.49 | 482 Cal."),
    ("Big Fish", "$4.99 | 513 Cal."),
    ("Chicken Garden Salad", "$5.89 | 870 Cal."),
    ("Side Garden Salad", "$1.69 | 322 Cal."),
]
# Section bar -> the tiles under it (0-based indices into TILES).
SECTIONS: list[tuple[str, range]] = [
    ("FLAME GRILLED BURGERS", range(0, 6)),
    ("CHICKEN & FISH", range(6, 12)),
    ("SALADS", range(12, 14)),
]
BEEF = {0, 2, 3, 4, 5}  # the five burgers labelled HIGH CLIMATE IMPACT in menu C
# Per menu: the key at the top (before the calorie line), and the label under the
# labelled tiles' prices, with which tiles carry it.
KEYS: dict[str, list[str]] = {
    "control": ["Scan the QR code for more menu information."],
    "low_impact": [
        "CO2",
        "LOW CLIMATE IMPACT",
        "This item is environmentally sustainable. It has low greenhouse gas emissions "
        "and a low contribution to climate change.",
    ],
    "high_impact": [
        "CO2",
        "HIGH CLIMATE IMPACT",
        "This item is not environmentally sustainable. It has high greenhouse gas "
        "emissions and a high contribution to climate change.",
    ],
}
LABELS: dict[str, tuple[str, set[int]]] = {
    "control": ("", set()),
    "low_impact": ("LOW CLIMATE IMPACT", set(range(14)) - BEEF),
    "high_impact": ("HIGH CLIMATE IMPACT", BEEF),
}


def text_in_image(key: str) -> str:
    """Every legible word on the menu, top to bottom, left to right."""
    label, labelled = LABELS[key]
    parts = [*KEYS[key], CALORIE_LINE]
    for bar, tiles in SECTIONS:
        parts.append(bar)
        for i in tiles:
            name, price = TILES[i]
            parts += [name, price]
            if i in labelled:
                parts.append(label)
    return " / ".join(parts)


_COMMON = (
    "A tall restaurant menu on a cream background, one picture. At the top, a line of "
    "bold text and a line of plain text, then three sections, each under a full-width "
    "coloured bar with its name in white capitals: FLAME GRILLED BURGERS (dark brown), "
    "CHICKEN & FISH (orange) and SALADS (green). The items sit up to three to a row in pale "
    "beige boxes, each a colour photograph of the food above its name in black, its "
    "price in dark brown and its calories in orange-brown. The burgers are in round "
    "buns, most with lettuce, tomato, onion, pickles or melted cheese, one with bacon; "
    "the chicken and fish section shows five sandwiches with breaded fillets and a pile "
    "of nuggets; the salads are a chicken salad and a side salad on white plates. No "
    "brand name or logo is printed. Every word is quoted in text_in_image. "
)
DESCRIPTIONS: dict[str, str] = {
    "control": _COMMON
    + (
        "In this version a small black-and-white QR code sits at the start of the top "
        "line and under the price of every one of the fourteen items. There are no "
        "climate labels."
    ),
    "low_impact": _COMMON
    + (
        "In this version the top line begins with a green label: a white footprint "
        "bearing the letters CO2, and the words LOW CLIMATE IMPACT in white. A smaller "
        "copy of the same green label sits under the price of nine items: Impossible "
        "Whopper, every item under CHICKEN & FISH and both salads; on the small labels "
        "the footprint's letters are too small to read. The other five burgers carry no "
        "label. There are no QR codes."
    ),
    "high_impact": _COMMON
    + (
        "In this version the top line begins with a red label: a white footprint "
        "bearing the letters CO2, and the words HIGH CLIMATE IMPACT in white. A smaller "
        "copy of the same red label sits under the price of five burgers: Whopper, "
        "Whopper Jr., Double Whopper with Cheese, Bacon Double Cheeseburger and "
        "Cheeseburger; on the small labels the footprint's letters are too small to "
        "read. Impossible Whopper and every chicken, fish and salad item carry no "
        "label. There are no QR codes."
    ),
}

LEAD = "The restaurant menu read, from top to bottom:"


def image_id(key: str) -> str:
    return f"egmxd_menu_{key}"


def image_file(key: str) -> str:
    """Path under data/, as the catalogue records it."""
    return f"raw/{STUDY}/images/menu_{key}.png"


def arm_text(key: str) -> str:
    return f'{LEAD} "{text_in_image(key)}" <image>'


# ---------------------------------------------------------------------------
# The questionnaire (.docx, read as Word stores it)
# ---------------------------------------------------------------------------


def _clean(text: str) -> str:
    """Typography only: PG's markup, curly quotes, non-breaking spaces, whitespace."""
    text = unescape(text)
    text = re.sub(r"</?u>", "", text)
    text = text.replace("[SPACE]", " ")
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def paragraphs(path: Path) -> list[tuple[str, list[str]]]:
    """(text, [docx media members embedded in it]) for every paragraph, in order."""
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
        rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
    target = {
        m.group(1): "word/" + m.group(2)
        for m in re.finditer(r'Id="(rId\d+)"[^>]*?Target="(media/[^"]+)"', rels)
    }
    out = []
    for para in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
        text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", para))
        media = [target[r] for r in re.findall(r'r:embed="(rId\d+)"', para)]
        out.append((text, media))
    return out


def _label(text: str) -> str | None:
    m = re.fullmatch(r"(Q\d[A-C]?)\.", text.strip())
    return m.group(1) if m else None


def instrument(path: Path) -> dict[str, Any]:
    """Everything the recipe quotes from one questionnaire file, and which picture each
    SHOW IF block embeds."""
    paras = paragraphs(path)
    blocks: dict[str, dict[str, Any]] = {}
    show: int | None = None
    current: str | None = None
    for text, media in paras:
        s = _clean(text)
        m = re.fullmatch(r"\[SHOW IF P_COND=(\d)\]", s)
        if m:
            show, current = int(m.group(1)), None
            continue
        if s.startswith("[SHOW IF") or s.startswith("IF R FINISHES CLIENT SURVEY"):
            # the next block, or (PG) the programming notes after the client survey
            show, current = None, None
            continue
        label = _label(s)
        if label:
            current = label
            blocks[label] = {"show": show, "lines": [], "media": [], "files": []}
            continue
        if current is None:
            continue
        b = blocks[current]
        b["media"] += media
        if re.fullmatch(r"\[[\w.]+\.png\]", s):
            b["files"].append(s.strip("[]"))
        elif s and not s.startswith("[") and s != "RESPONSE OPTIONS:":
            b["lines"].append(s)
    wintro = [_clean(t).removeprefix("[ALL] ") for t, _ in paras if "This survey is about" in t]

    def options(q: str) -> tuple[str, list[str]]:
        lines = blocks[q]["lines"]
        opts = [x for x in lines if re.match(r"\d+\. ", x)]
        stem = " ".join(x for x in lines if x not in opts)
        if [int(x.split(".")[0]) for x in opts] != list(range(1, len(opts) + 1)):
            raise SystemExit(f"{path.name} {q}: options not numbered 1..n")
        return stem, [x.split(". ", 1)[1] for x in opts]

    q2, q2_opts = options("Q2")
    q3, q3_opts = options("Q3")
    q4, q4_opts = options("Q4")
    q5, q5_opts = options("Q5")
    q6, q6_opts = options("Q6")
    return {
        "wintro": wintro,
        "menus": {
            q: (blocks[q]["show"], blocks[q]["media"], blocks[q]["files"])
            for q in ("Q1A", "Q1B", "Q1C")
        },
        "q1": {q: " ".join(blocks[q]["lines"]) for q in ("Q1A", "Q1B", "Q1C")},
        "q3": q3,
        "q3_options": q3_opts,
        "q4": q4,
        "q4_options": q4_opts,
        "q2": q2,
        "q2_options": q2_opts,
        "q5": q5,
        "q5_options": q5_opts,
        "q6": q6,
        "q6_options": q6_opts,
    }


# PG prints Q6 as "is<u>important</u> to me": with its tags removed the space is gone.
# Q's "is important to me" is followed (docs/CONVENTIONS.md, Source authority).
PG_Q6_SLIP = ("choices is important to me.", "choices isimportant to me.")


def fielded() -> dict[str, Any]:
    """Q, after asserting PG says the same words and shows the same pictures for the
    same P_COND (docs/CONVENTIONS.md, Source authority)."""
    q, pg = instrument(SIMPLE), instrument(PROG)
    if pg["q6"] != q["q6"].replace(*PG_Q6_SLIP):
        raise SystemExit(f"Q6 differs other than by PG's missing space: {pg['q6']!r}")
    keys = ["wintro", "q1", "q2", "q2_options", "q3", "q3_options", "q4", "q4_options"]
    for key in (*keys, "q5", "q5_options", "q6_options"):
        if q[key] != pg[key]:
            raise SystemExit(f"simple and prog disagree on {key}: {q[key]!r} / {pg[key]!r}")
    if q["wintro"] != ["This survey is about restaurant menus."]:
        raise SystemExit(f"welcome line changed: {q['wintro']}")
    if len(set(q["q1"].values())) != 1:
        raise SystemExit(f"Q1A/Q1B/Q1C stems differ: {q['q1']}")
    with zipfile.ZipFile(SIMPLE) as zs, zipfile.ZipFile(PROG) as zp:
        for key, cond, _, letter, name, _ in MENUS:
            show_q, media_q, files_q = q["menus"][f"Q1{letter}"]
            show_p, media_p, files_p = pg["menus"][f"Q1{letter}"]
            if show_q != cond or show_p != cond:
                raise SystemExit(f"Q1{letter} is not under SHOW IF P_COND={cond}")
            if len(media_q) != 1 or len(media_p) != 1:
                raise SystemExit(f"Q1{letter}: expected one picture, got {media_q} / {media_p}")
            if zs.read(media_q[0]) != zp.read(media_p[0]):
                raise SystemExit(f"Q1{letter}: simple and prog embed different pictures")
            if files_q or files_p != [name]:
                raise SystemExit(f"Q1{letter}: file names {files_q} / {files_p}, expected {name}")
            if key != MENUS[cond - 1][0]:
                raise SystemExit("MENUS out of P_COND order")
    return q


def menu_member(key: str) -> str:
    """The docx member Q embeds under this menu's SHOW IF block."""
    _, cond, _, letter, _, _ = next(m for m in MENUS if m[0] == key)
    show, media, _ = fielded()["menus"][f"Q1{letter}"]
    assert show == cond
    return str(media[0])


# RELIG 14 "Something else, please specify:" is a real answer wearing its text-box
# instruction; the label minus the instruction, as s6urt and 9xw67 carry it.
SOMETHING_ELSE = "Something else"


def protestant_label() -> str:
    """RELIG code 1 in full: the .dta's label stops at 80 characters; Q's demographic
    profile gives the whole answer."""
    (line,) = [t for t, _ in paragraphs(SIMPLE) if _clean(t).startswith("1 = Protestant (")]
    # whitespace only: the source's own apostrophe is kept, as the religion crosswalk has it
    return re.sub(r"\s+", " ", unescape(line)).split("=", 1)[1].strip()


# ---------------------------------------------------------------------------
# The data: codes kept, the fourteen click variables folded into one
# ---------------------------------------------------------------------------


def read_dta() -> tuple[pd.DataFrame, dict[str, dict[int, str]], dict[str, str]]:
    """The .dta's codes, value labels and variable labels, via pandas (pyreadstat
    cannot decode this file)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with pd.io.stata.StataReader(str(DTA)) as r:
            df = r.read(convert_categoricals=False)  # type: ignore[attr-defined]
            vl = r.value_labels()
            ll = r.variable_labels()
        decoded = pd.read_stata(DTA)
    labels = {v: {int(k): str(s) for k, s in m.items()} for v, m in vl.items()}
    # Round trip: our codes + labels must say what pandas' own decoding says.
    for var, m in labels.items():
        if var not in df.columns:
            continue
        mapped = df[var].map(lambda x, m=m: m.get(int(x), x) if pd.notna(x) else x)
        theirs = decoded[var].astype(object)
        same = (mapped.astype(str) == theirs.astype(str)) | (mapped.isna() & theirs.isna())
        if not same.all():
            raise SystemExit(f"{var}: codes and labels do not reproduce pandas' decoding")
    return df, labels, {k: v for k, v in ll.items() if v}


def region_names(column_labels: dict[str, str]) -> dict[str, list[str]]:
    """Block letter -> the fourteen hot-spot region names, from the variable labels."""
    out: dict[str, list[str]] = {}
    for _, _, _, letter, _, _ in MENUS:
        names = []
        for k in range(1, 15):
            m = re.match(
                r"\[([^\]]+)\] Look at the restaurant menu", column_labels[f"Q1{letter}_{k}"]
            )
            if not m:
                raise SystemExit(f"Q1{letter}_{k}: no [region] in its label")
            names.append(m.group(1))
        out[letter] = names
    return out


def coded() -> tuple[pd.DataFrame, dict[str, dict[int, str]], dict[str, str]]:
    """The .sav's contents: every column's codes and labels, plus MENU_ITEM."""
    df, labels, col_labels = read_dta()
    if sorted(df[COND_VAR].unique().tolist()) != [1, 2, 3]:
        raise SystemExit(f"{COND_VAR} codes changed")
    if dict(labels[COND_VAR]) != {m[1]: m[2] for m in MENUS}:
        raise SystemExit(f"{COND_VAR} labels changed: {labels[COND_VAR]}")
    if not df[ID_VAR].is_unique or df[ID_VAR].isna().any():
        raise SystemExit(f"{ID_VAR} is not a unique id")
    names = region_names(col_labels)
    if any(n != [t[0] for t in TILES] for n in names.values()):
        raise SystemExit(f"hot-spot regions are not the transcribed item names: {names}")
    for _, _, label, letter, _, _ in MENUS:
        if not col_labels[f"Q1{letter}_TIMER_Page_Submit"].startswith(f"[{label}]"):
            raise SystemExit(f"Q1{letter}'s timer is not labelled {label}")
    item = pd.Series(np.nan, index=df.index)
    for _, cond, _, letter, _, _ in MENUS:
        mine = df[COND_VAR] == cond
        own = df.loc[mine, [f"Q1{letter}_{k}" for k in range(1, 15)]]
        if not own.isin([0, 1]).all().all():
            raise SystemExit(f"Q1{letter}: values other than 0/1 in its own arm")
        if not (own.sum(axis=1) == 1).all():
            raise SystemExit(f"Q1{letter}: someone clicked other than exactly one item")
        others = [f"Q1{m[3]}_{k}" for m in MENUS if m[3] != letter for k in range(1, 15)]
        if df.loc[mine, others].notna().any().any():
            raise SystemExit(f"P_COND={cond}: answers in another arm's menu")
        item[mine] = own.to_numpy().argmax(axis=1) + 1
    df = df.drop(columns=["RELIGO"])
    df[ITEM_VAR] = item.astype(float)
    labels[ITEM_VAR] = {i: name for i, (name, _) in enumerate(TILES, start=1)}
    col_labels[ITEM_VAR] = (
        "Derived (gen_egmxd.py): the menu region clicked, from the arm's Q1A/Q1B/Q1C_1..14"
    )
    return df, labels, col_labels


def write_coded() -> None:
    import pyreadstat

    df, labels, col_labels = coded()
    for c in df.columns:
        if not (
            pd.api.types.is_numeric_dtype(df[c]) or pd.api.types.is_datetime64_any_dtype(df[c])
        ):
            df[c] = df[c].astype(object)
    pyreadstat.write_sav(
        df,
        str(CODED),
        column_labels=[col_labels.get(c, "") for c in df.columns],
        variable_value_labels={
            v: {float(k): s for k, s in m.items()} for v, m in labels.items() if v in df.columns
        },
    )
    back = read_any(CODED)
    for var in (COND_VAR, ITEM_VAR, "Q3", "Q4", "RELIG"):
        if not back.df[var].equals(df[var].astype(float)):
            raise SystemExit(f"{var} did not survive the .sav round trip")


# ---------------------------------------------------------------------------
# Pictures
# ---------------------------------------------------------------------------


def extract() -> None:
    """--prep: copy each menu out of Q, byte for byte."""
    IMAGES.mkdir(exist_ok=True)
    with zipfile.ZipFile(SIMPLE) as z:
        for key, *_ in MENUS:
            (IMAGES / f"menu_{key}.png").write_bytes(z.read(menu_member(key)))


def _pixels(png: bytes) -> np.ndarray:
    """RGB pixels of a PNG, decoded by macOS sips (no imaging library in the project)."""
    if not shutil.which("sips"):
        raise SystemExit("sips (macOS) is needed for the picture checks")
    with tempfile.TemporaryDirectory() as tmp:
        src, bmp = Path(tmp) / "p.png", Path(tmp) / "p.bmp"
        src.write_bytes(png)
        subprocess.run(
            ["sips", "-s", "format", "bmp", str(src), "--out", str(bmp)],
            check=True,
            capture_output=True,
        )
        b = bmp.read_bytes()
    offset = int.from_bytes(b[10:14], "little")
    width = int.from_bytes(b[18:22], "little", signed=True)
    height = int.from_bytes(b[22:26], "little", signed=True)
    bpp = int.from_bytes(b[28:30], "little")
    if bpp not in (24, 32):
        raise SystemExit(f"unexpected bitmap depth {bpp}")
    stride = ((bpp * width + 31) // 32) * 4
    raw = np.frombuffer(b[offset : offset + stride * abs(height)], dtype=np.uint8)
    rows = raw.reshape(abs(height), stride)[:, : width * (bpp // 8)]
    px = rows.reshape(abs(height), width, bpp // 8)[:, :, 2::-1].astype(int)  # BGR -> RGB
    return px[::-1] if height > 0 else px


def description_menus() -> dict[str, str]:
    """Description-document heading -> the docx member printed under it."""
    out: dict[str, str] = {}
    heading: str | None = None
    for text, media in paragraphs(DESCRIPTION):
        s = _clean(text)
        if s.startswith("MENU "):
            heading = s
        elif media and heading:
            out[heading] = media[0]
            heading = None
    return out


def differing_rows(a: np.ndarray, b: np.ndarray) -> set[int]:
    """Pixel rows where two same-sized pictures differ visibly (summed RGB > 30)."""
    return set(np.where((np.abs(a - b).sum(axis=2) > 30).any(axis=1))[0].tolist())


def picture_checks() -> dict[str, Any]:
    """Each menu against the description document's picture of the same heading, and
    where the three menus differ from one another."""
    by_heading = description_menus()
    px = {key: _pixels((REPO / "data" / image_file(key)).read_bytes()) for key, *_ in MENUS}
    out: dict[str, Any] = {"proposal": {}, "differ": {}}
    with zipfile.ZipFile(DESCRIPTION) as z:
        for key, *_, heading in MENUS:
            theirs = _pixels(z.read(by_heading[heading]))
            out["proposal"][key] = {
                k: int(np.abs(theirs - p).max()) if theirs.shape == p.shape else 255
                for k, p in px.items()
            }
    for key in ("low_impact", "high_impact"):
        out["differ"][key] = sorted(differing_rows(px["control"], px[key]))
    return out


# The pixel rows where a labelled menu may differ from the control one: the key at
# the top and the label strip of each row of tiles (measured; see picture_checks).
KEY_ROWS = range(0, 100)
STRIP_ROWS = [range(440, 475), range(710, 775), range(1135, 1170), range(1395, 1435),
              range(1800, 1835)]  # fmt: skip


def verify_pictures() -> None:
    checks = picture_checks()
    for key, dist in checks["proposal"].items():
        others = [v for k, v in dist.items() if k != key]
        if dist[key] > 12 or min(others) < 100:
            raise SystemExit(f"{key}: description-document distances {dist}")
    allowed = set(KEY_ROWS).union(*map(set, STRIP_ROWS))
    for key, rows in checks["differ"].items():
        if not rows or not set(rows) <= allowed:
            raise SystemExit(f"{key} differs from control outside the key and label strips")


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------


def catalogue_entries() -> dict[str, dict[str, str]]:
    """This study's entries in data/catalog/images.json, after checking each file is
    Q's picture for its block, byte for byte."""
    from micromotives_datasets.images import sha256_of

    out: dict[str, dict[str, str]] = {}
    pg = instrument(PROG)
    with zipfile.ZipFile(SIMPLE) as z:
        for key, cond, label, letter, name, heading in MENUS:
            member = menu_member(key)
            f = image_file(key)
            if (REPO / "data" / f).read_bytes() != z.read(member):
                raise SystemExit(f"{f} is not {member} of {SIMPLE.name}")
            pg_member = pg["menus"][f"Q1{letter}"][1][0]
            out[image_id(key)] = {
                "file": f,
                "sha256": sha256_of(REPO / "data" / f),
                "source": (
                    "OSF egmxd, TESS deposit wolfson1443.zip: embedded in the fielded "
                    f"questionnaire {SIMPLE.name} as {member}, copied byte for byte, under "
                    f'"[SHOW IF P_COND={cond}]" and Q1{letter} (P_COND {cond} is "{label}"). '
                    f"The programming version {PROG.name} embeds the same bytes as "
                    f'{pg_member} in the same block and names the file "{name}"; the '
                    "proposal's description document prints the same picture, every pixel "
                    f'within 8 of 255 levels, under "{heading}". NORC\'s {name} is not in the deposit, so '
                    "this is Word's copy and may differ from it in resolution or encoding."
                ),
                "licence": LICENCE,
                "text_in_image": text_in_image(key),
                "description": DESCRIPTIONS[key],
            }
    return out


def write_catalogue() -> None:
    """Add or refresh only this study's entries; re-read first, others are editing too."""
    verify_pictures()
    entries = catalogue_entries()
    path = REPO / "data" / "catalog" / "images.json"
    current = json.loads(path.read_text())
    current.update(entries)
    path.write_text(json.dumps(current, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Recipe
# ---------------------------------------------------------------------------


def _scale(options: list[str]) -> dict[str, Any]:
    n = len(options)
    s: dict[str, Any] = {"min": 1, "max": n, "min_label": options[0], "max_label": options[-1]}
    if n % 2:
        s["mid_label"] = options[n // 2]
    return s


# The screens after the menu, in the fielded order (no randomisation): Q2, the
# manipulation check (not built), then the four built follow-ups, task 1 to task 4.
SCREENS = ["q1", "q2", "q3", "q4", "q5", "q6"]
TASK_SCREEN = {1: "q3", 2: "q4", 3: "q5", 4: "q6"}


def asked_before(q: dict[str, Any]) -> dict[int, list[str]]:
    """Task -> the questions put to the respondent after the menu appeared and before
    this one, word-for-word, in order. Questions only: their answer options are not
    quoted, and nothing says what the respondent answered."""
    (stem,) = set(q["q1"].values())
    words = {"q1": stem, **{k: q[k] for k in SCREENS[1:]}}
    return {
        task: [words[k] for k in SCREENS[: SCREENS.index(screen)]]
        for task, screen in TASK_SCREEN.items()
    }


def narration(questions: list[str]) -> str:
    """OURS: 'You were asked: "..." Then you were asked: "..."', the earlier questions
    narrated as asked, never as answered (docs/CONVENTIONS.md, Narrating what the
    respondent did)."""
    first, *rest = questions
    return " ".join([f'You were asked: "{first}"', *(f'Then you were asked: "{x}"' for x in rest)])


def recipe() -> dict[str, Any]:
    q = fielded()
    ds = read_any(CODED)
    labels = ds.value_labels
    if sorted(int(c) for c in ds.df[COND_VAR].dropna().unique()) != [1, 2, 3]:
        raise SystemExit(f"{COND_VAR} codes changed")
    if not ds.df[ID_VAR].is_unique:
        raise SystemExit(f"{ID_VAR} is not unique")
    if [labels[ITEM_VAR][float(i)] for i in range(1, 15)] != [t[0] for t in TILES]:
        raise SystemExit(f"{ITEM_VAR} labels are not the menu's items")
    # The data's own labels must agree with the questionnaire's options; Q3 is coded 2-6.
    if [labels["Q3"][float(k)] for k in range(2, 7)] != q["q3_options"]:
        raise SystemExit("Q3: value labels differ from the questionnaire")
    if [labels["Q4"][float(k)] for k in range(1, 8)] != q["q4_options"]:
        raise SystemExit("Q4: value labels differ from the questionnaire")
    for var in ("Q5", "Q6"):  # coded 2-6, as Q3
        if [labels[var][float(k)] for k in range(2, 7)] != q[f"{var.lower()}_options"]:
            raise SystemExit(f"{var}: value labels differ from the questionnaire")
    for var, valid in (("Q3", 2), ("Q4", 1), ("Q5", 2), ("Q6", 2)):
        n = len(q[f"{var.lower()}_options"])
        if set(labels[var]) - set(map(float, range(valid, valid + n))) != {98.0}:
            raise SystemExit(f"{var} non-answer codes changed")

    (stem,) = set(q["q1"].values())
    listed = "; ".join(f'{i} means "{name}"' for i, (name, _) in enumerate(TILES, start=1))
    outcomes: list[dict[str, Any]] = [
        {
            "var": ITEM_VAR,
            "task_num": 0,
            "question": f"{stem} {listed}.",
            "scale": {"min": 1, "max": 14, "nominal": True},
            "response_recode": {i: i for i in range(1, 15)},
        },
        {
            "var": "Q3",
            "task_num": 1,
            "question": q["q3"],
            "scale": _scale(q["q3_options"]),
            "response_recode": {k: k - 1 for k in range(2, 7)},
        },
        {
            "var": "Q4",
            "task_num": 2,
            "question": q["q4"],
            "scale": _scale(q["q4_options"]),
            "response_recode": {i: i for i in range(1, 8)},
        },
        {
            "var": "Q5",
            "task_num": 3,
            "question": q["q5"],
            "scale": _scale(q["q5_options"]),
            "response_recode": {k: k - 1 for k in range(2, 7)},
        },
        {
            "var": "Q6",
            "task_num": 4,
            "question": q["q6"],
            "scale": _scale(q["q6_options"]),
            "response_recode": {k: k - 1 for k in range(2, 7)},
        },
    ]

    asked = asked_before(q)
    arms = [
        {
            "raw": cond,
            "condition_num": cond - 1,
            "factors": {"label": key},
            "text": arm_text(key),
            "images": [image_id(key)],
            "items": {
                task: {"condition_text": f"{arm_text(key)} {narration(asked[task])}"}
                for task in range(1, 5)
            },
        }
        for key, cond, *_ in MENUS
    ]

    return {
        "study_id": STUDY,
        "source": "tess",
        "title": "Do Sustainability Labels Lead to More Sustainable and Healthier Food "
        "Choices?: a fast-food menu with QR codes, green low-climate-impact labels or red "
        "high-climate-impact labels; the item ordered, whether the menu discouraged "
        "high-impact items, how healthy the meal was, climate concern and the importance "
        "of healthy choices",
        "data_file": DATA_FILE,
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": ID_VAR,
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_var": COND_VAR,
            "shared_context": q["wintro"][0],
            "factors": ["label"],
            "arms": arms,
        },
        "outcomes": outcomes,
        "response_recode": {},
        "missing_codes": [],
        "persona_map": {
            "age": "AGE",
            "gender": "GENDER",
            "education": "EDUC5",
            "ethnicity": "RACETHNICITY",
            "income": "INCOME",
            "marital_status": "MARITAL",
            "employment": "EMPLOY",
            "region": "REGION4",
            "household_size": "HHSIZE",
            "housing_type": "HOME_TYPE",
            "housing_ownership": "HOUSING",
            "urban_rural": "METRO",
            "internet_access": "INTERNET",
            "phone_service": "PHONESERVICE",
            "party_id": "PartyID7",
            "ideology": "IDEO20",
            "religion": "RELIG",
            "religious_attendance": "ATTEND",
        },
        "persona_label_rewrite": {"RELIG": {1: protestant_label(), 14: SOMETHING_ELSE}},
        "persona_missing": {
            "PartyID7": [-1],
            "IDEO20": [-1],
            "RELIG": [98],
            "ATTEND": [98],
            "GENDER": [0],
        },
    }


def render() -> str:
    return yaml.safe_dump(recipe(), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--prep", action="store_true", help="extract the menus, write the .sav")
    ap.add_argument("--catalogue", action="store_true", help="add this study's images.json entries")
    args = ap.parse_args()
    if args.prep:
        extract()
        write_coded()
        print(f"wrote {IMAGES.relative_to(REPO)}/menu_*.png and {CODED.relative_to(REPO)}")
        return 0
    if args.catalogue:
        write_catalogue()
        print("updated data/catalog/images.json (egmxd entries only)")
        return 0
    text = render()
    if args.check:
        same = RECIPE.exists() and RECIPE.read_text() == text
        print("recipe matches generator" if same else "recipe DIFFERS from generator")
        return 0 if same else 1
    RECIPE.write_text(text)
    print(f"wrote {RECIPE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
