#!/usr/bin/env python3
"""Write recipes/images/v6kqy.yaml: three photographs of one vehicle, then questions.

Rode, TESS 1532 (fielded as NORC 9089.122, "TESS 122 Rode"), "The Tesla effect:
Increasing Republican support for electric vehicle adoption through engagement with
a value-aligned product". OSF v6kqy, the TESS deposit rode1532.zip, unpacked under
data/raw/v6kqy/TESS 122 Rode/: the data (s2861_client.dta), NORC's deliverables
(the same data as CSV, a codebook, and the fielded questionnaire in a simple and a
programming version, 9089.122_TESS_Rode_vFINALsimple.docx / vFINALprog.docx, "Q" and
"PG" below), NORC's methods report, and the researcher's description document (a
zero-byte file in the deposit). The proposal is data/raw/v6kqy/Rode1532.pdf, fetched
separately ("Manuscript ID TESS-1532.R1").

AmeriSpeak, US adult Republicans and Republican leaners (Q's own heading; PARTYID7 is
5, 6 or 7 for all), web only (`SURV_MODE` 2), English only, fielded 1 to 14 March
2023. 2,458 completed; all 2,458 are in the file and all are built.

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* DESIGN. Two preloads (Q's demographic profile and PG's preload table):
  `DOV_EXP_RODE` 1 LIGHTNING, 2 XLT, 3 TESLA, 4 KONA, 5 CONTROL (499 / 518 / 500 /
  488 / 453), and, for the 453 controls only, `DOV_CONTROL` 1-4, the vehicle the
  control group was shown (118 / 105 / 110 / 120). Q's block-order directive: arms
  1-4 saw STIMULI, REVIEW_1, ATTITUDES, INTEREST1, REVIEW_2, INTEREST2; the control
  saw ATTITUDES, INTEREST1, STIMULI, REVIEW_1, REVIEW_2, INTEREST2. So the
  manipulation is whether a person evaluated one of four vehicles BEFORE the
  environmental-policy questions, and which vehicle. The data's ORDERA..ORDERF
  record exactly those two block orders, one per group (asserted).
* WHAT EACH PERSON SAW. Everyone saw the same three-page stimulus block, for one
  vehicle: STIMULI1 (photo; name, kind and price), STIMULI2 (photo; range),
  STIMULI3 (photo; towing or acceleration). So every person saw THREE photographs,
  one per page, in that fixed order, each with its sentence. The control group saw
  the same block for its `DOV_CONTROL` vehicle, but only after ATTITUDES and
  INTEREST1. Each REVIEW screen repeated the STIMULI1 photo at the top (PG: "DISPLAY
  IMAGE SHOWN IN DISPLAY_STIMULI1 AT THE TOP OF EACH SCREEN THROUGHOUT THE REVIEW
  SECTION"); that repeat is not rendered a second time, because the photo is
  already in the condition and an arm's pictures cannot differ between its outcomes.
* WHICH PICTURE IS WHICH CONDITION. Q embeds the twelve photographs, each in a
  paragraph directly under its own directive ("IF DOV_EXP_RODE=3 OR DOV_CONTROL=3:"),
  word/media/image3..image14. That mapping is read here from Q's document.xml in
  document order (the directive paragraph, then the r:embed of the next paragraph,
  then the sentence), not assumed. Q's first directive reads "IF DOV_EXP_RODE=1 OR
  DOV_CONTROL:" with the "=1" missing; PG's copy has it, and the condition is read
  as 1 (asserted against PG). Two independent witnesses agree: PG names the fielded
  files in the same per-screen order (LIGHTNING1/XLT1/TESLA1/KONA1.jpg on STIMULI1,
  ...2 and ...3 after), and the proposal (Rode1532.pdf, Appendix B, pp. 12-14)
  prints the same twelve photographs under the vehicle headings, in the order XLT,
  Lightning, Tesla, Kona; reduced to 64 x 64 grey, each proposal photograph is
  nearest Q's photograph for the same vehicle and page (checked in --catalogue).
  The fielded files themselves are not in the deposit: PG names them as .jpg on
  NORC's drive, and Q's TESLA1 copy is a PNG, so these are Q's embedded copies and
  may differ from what was served in resolution or encoding.
* CONDITION. shared_context is WINTRO_1's one line shown to everyone ("[ALL] This
  survey is about your opinions of products currently on the market."); the thanks,
  the AmeriPoints and the Continue button are survey mechanics and are dropped.
  Each arm then gives the introduction screen DISPLAY_INTRODUCTION for its group
  (two wordings, word-for-word from Q, asserted in PG), and, where the vehicle had
  been shown, the three pages: each photo, then its sentence, word-for-word from Q
  (and asserted present in PG). The connecting words are OURS: "Then three pages,
  each a photo followed by text:", and the quotation marks. They say only what PG's
  layout (INSERT IMAGE, then the text) says was on screen.
  Nine arms, two factors (`vehicle`, `order`):
  - 0-3: arms 1-4, the vehicle first. Every outcome.
  - 4-7: the control, shown vehicle `DOV_CONTROL` after the policy questions. The
    REVIEW outcomes only: these rows had the vehicle; their introduction told them
    "you will answer a few background questions and then learn about a product".
  - 8: the control BEFORE any vehicle. ATTITUDES and INTEREST1 only: those were
    asked before the stimulus block, so the condition is the control's
    introduction and nothing else, and carries no picture. SocSci210 gives these
    rows the vehicle the person saw only AFTER answering them; that is the defect
    this arm exists to avoid.
  The assignment therefore differs by outcome, which the recipe expresses the way
  within-subject designs do: the study-level `source_var` is a DERIVED column,
  `V6KQY_ARM` (DOV_EXP_RODE 1-4; 5 + DOV_CONTROL for the control, so 6-9), and
  ATTITUDES1A-2B and INTEREST1 declare `condition_var: DOV_EXP_RODE` (1-4 and 5).
  One code space: 1-4 are the same arms through either column. QC's rule 10 skips
  itself for such designs and says so. The derived file is the deposit .dta plus
  that one column, written as data/raw/v6kqy/v6kqy-derived.sav by --prep and
  checked equal to the deposit on every original column (as gh396, egmxd).
* OUTCOMES. Twenty-four, word-for-word from Q, typography normalised. Task numbers
  follow Q's listing order:
  - REVIEW1, REVIEW4, REVIEW5, REVIEW6 (task 0, 3, 4, 5): 1-5, Q's options.
  - REVIEW2, REVIEW3 (task 1, 2): "Yes" / "No", nominal, options enumerated in the
    question. Q's third option "Unsure" is coded 77, the panel's own DON'T KNOW
    code (its value label is "Unsure"), so it is a non-answer and dropped (182 and
    425 people), as SocSci210 did.
  - REVIEW7A-F (task 6-11) and REVIEW9A-F (task 12-17): grids, stem then item,
    1-5, Strongly disagree .. Strongly agree. Item order was randomised and not
    recorded; no row says where its item sat.
  - ATTITUDES1A-C (task 18-20): "How much do you oppose or support the
    following?" then the item, 1-5. ATTITUDES2A-B (task 21-22): agreement, 1-5.
  - INTEREST1 (task 23): "Do you want to learn some surprising facts about electric
    vehicles ...?" Yes / No, nominal.
  Each item's codes are checked against the data's value labels.
* NOT BUILT.
  - REVIEW8, "Which of the following features make you like this product? Select
    all that apply." A select-all list stored as seven 0/1 columns (REVIEW8_1 ..
    REVIEW8_7). The respondent ticked boxes in one list; a row per box would ask a
    yes/no question nobody was asked, and no build here has yet ruled how a
    select-all list becomes rows. SocSci210 built it as seven Yes/No rows (17,206).
    Left for rich's ruling; the cost is 7 x 2,458 = 17,206 rows.
  - REVIEW10-12, the fuel, price and range of the vehicle "based on the information
    provided earlier in this survey": comprehension checks whose answers are stated
    in the condition (docs/CONVENTIONS.md, as yjvpn's Q5/Q6). SocSci210 did not
    build them.
  - INTEREST2 is a display of three links (its only code is "Continue") and its
    click counts are behaviour after every built outcome; PID1/PIDA/PIDB/PIDi are
    the panel's party screener, not in the file as answers.
* WHO. All 2,458 completes. `CaseId` is the participant id. Skips are 98 "SKIPPED ON
  WEB" (2 to 20 per item); 77 occurs only as REVIEW2/3's "Unsure"; 99 never occurs.
  `missing_codes` is 77 / 98 / 99, none of which is a valid answer to any built
  item (every scale tops out at 5).
* PERSONA. The standard AmeriSpeak preloads, as yjvpn and 8ctbk: AGE, GENDER, EDUC5
  (the file has no EDUC), RACETHNICITY, INCOME (18 bands), MARITAL, EMPLOY,
  REGION4, HHSIZE, HOME_TYPE, HOUSING, METRO, INTERNET, PHONESERVICE, PARTYID7, IDEO,
  RELIG, ATTEND. Party and ideology are persona, never condition; the sample is
  Republicans and leaners by design. Left absent: PARTYID7 and IDEO -1 "Unknown",
  RELIG / ATTEND 77 / 98 / 99, GENDER 0 "Unknown". Not mapped: STATE, REGION9, the
  banded duplicates AGE4 / AGE7 / INCOME4 / INCOME9, the household age counts,
  PARTYID5. RELIG code 1's label is cut off at 80 characters in the .dta ("...
  Presbyterian, Pent"); `persona_label_rewrite` restores the whole answer from Q's
  demographic profile, as yjvpn. Code 14's label is "Something else, please
  specify:", a real answer wearing a text-box instruction; rewritten to "Something
  else", as vemrp, xk9ch and s6urt.
* UK FIT. American vehicles, US dollar prices, miles, pounds and "the U.S."
  economy. Accepted for image experiments (rich, 9 Nov 2026). US spellings
  ("favorable") are kept word-for-word.
* ANSWER KEY. SocSci210 holds this study: 75,329 rows, 2,458 people, four
  conditions (the vehicle, treatment and control merged) and six tasks. Their
  condition text is written from the proposal (a "5.3 seconds" Model 3 and "mpg"),
  not the fielded instrument (5.8 seconds). Reconciled cell for cell in
  tests/test_gen_v6kqy.py.
* JEV (scripts/recipe_prep.py v6kqy --source tess, 9 Nov 2026, instrument only).
  Assignment: DOV_EXP_RODE, conf 0.96 (runner-up DOV_CONTROL 0.02), accepted; the
  control's own vehicle column is the runner-up and is folded in above. Persona: every
  field as mapped here at conf 0.93-1.00, except region, REGION4 at 0.52 against
  REGION9 at 0.36 (REVIEW): REGION4 kept, as in every other TESS build. Non-answers:
  REVIEW2 / REVIEW3 "Unsure" judged non_answer at 0.82 (REVIEW) and 0.86, disagreeing
  with the keyword regex; accepted, as above. Its directive scan found no
  questionnaire (it does not read .docx), so that section checked nothing; the
  directives this recipe depends on are parsed and asserted here instead.

    uv run python scripts/gen_v6kqy.py --prep       # photos out of Q; the derived .sav
    uv run python scripts/gen_v6kqy.py --catalogue  # (re)write this study's images.json entries
    uv run python scripts/gen_v6kqy.py              # write the recipe
    uv run python scripts/gen_v6kqy.py --check      # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

STUDY = "v6kqy"
RAW = REPO / "data" / "raw" / STUDY
DEPOSIT = RAW / "TESS 122 Rode"
DTA = DEPOSIT / "s2861_client.dta"
DERIVED = RAW / "v6kqy-derived.sav"
DATA_FILE = DERIVED.name
SIMPLE = DEPOSIT / "deliverables" / "9089.122_TESS_Rode_vFINALsimple.docx"
PROG = DEPOSIT / "deliverables" / "9089.122_TESS_Rode_vFINALprog.docx"
PROPOSAL = RAW / "Rode1532.pdf"
IMAGES = RAW / "images"
RECIPE = REPO / "recipes" / "images" / f"{STUDY}.yaml"
LICENCE = (
    "None stated: the TESS deposit on OSF (v6kqy, rode1532.zip) gives no reuse terms, "
    "and TESS has since suspended operations. Used with rich's ruling of 9 Nov 2026 that "
    "an unstated licence does not block an image build."
)

ID_VAR = "CaseId"
COND_VAR = "DOV_EXP_RODE"
CONTROL_VAR = "DOV_CONTROL"
ARM_VAR = "V6KQY_ARM"
CONTROL_CODE = 5

# (key, DOV_EXP_RODE / DOV_CONTROL code, PG's file stem, proposal heading)
VEHICLES: list[tuple[str, int, str, str]] = [
    ("lightning", 1, "LIGHTNING", "Ford F-150 Lightning"),
    ("xlt", 2, "XLT", "Gas-powered Ford F-150 XLT"),
    ("tesla", 3, "TESLA", "Tesla Model 3"),
    ("kona", 4, "KONA", "Hyundai Kona Electric"),
]
SCREENS = [1, 2, 3]
# The proposal's twelve photographs, in page order (pdfimages -f 12 -l 14).
PROPOSAL_ORDER = [(v, s) for v in ("xlt", "lightning", "tesla", "kona") for s in SCREENS]

# Words printed on each photograph, word-for-word, where they can be read at the
# file's own resolution. Badges whose lettering is a blur are described, not quoted.
TEXT_IN_IMAGE: dict[str, str] = {
    "lightning_1": "",
    "lightning_2": "",
    "lightning_3": "",
    "xlt_1": "4x4",
    "xlt_2": "",
    "xlt_3": "",
    "tesla_1": "",
    "tesla_2": "TESLA",
    "tesla_3": "",
    "kona_1": "",
    "kona_2": "",
    "kona_3": "",
}

# Visible facts only: no appraisal of the vehicle (the study measures how people
# rate it), and no brand named unless its word is printed and legible.
DESCRIPTIONS: dict[str, str] = {
    "lightning_1": (
        "Colour photograph: a dark blue four-door pickup truck driving towards the "
        "camera on a two-lane road, seen from the front and side, headlights on. Bare "
        "brown hills rise behind it under a pale sky. An oval badge on the black grille; "
        "its lettering is too small to read."
    ),
    "lightning_2": (
        "Colour photograph at night: a bronze-coloured four-door pickup truck parked "
        "front-out in a lit garage, its headlights and a light bar across the front on. "
        "A cable runs from a box mounted on the garage's back wall to the side of the "
        "truck. Red tool chests stand at the left; the wet driveway in front reflects "
        "the light. No legible words."
    ),
    "lightning_3": (
        "Colour photograph: a pale blue four-door pickup truck on a residential street, "
        "towing a flatbed trailer that carries a yellow compact loader. Large houses and "
        "trees behind, a lawn in the foreground, an evening sky. An oval badge on the "
        "grille; its lettering is too small to read."
    ),
    "xlt_1": (
        "Colour photograph: a silver-grey four-door pickup truck parked on a mossy, "
        "rocky outcrop, seen from the front and side, with chrome grille and wheels. "
        "Water, forested hills and low grey clouds behind. An oval badge on the grille, "
        'its lettering too small to read; a small "4x4" badge on the side of the '
        "truck bed, by the tail light."
    ),
    "xlt_2": (
        "Colour photograph: a silver four-door pickup truck with a dark grille and "
        "black wheels, parked on a cracked car park beside dry grass, seen from the "
        "front and side. Bare trees, a pylon and low industrial buildings behind. An "
        "oval badge on the grille and a plate on the front bumper carrying a smaller "
        "oval and red lettering, all too small to read."
    ),
    "xlt_3": (
        "Colour photograph: a red four-door pickup truck on a snowy construction site, "
        "its tailgate open. A crane lowers a large dark cylinder towards the truck "
        "bed, and two workers in hard hats and high-visibility vests stand beside it; "
        "a yellow wheeled machine at the left. A glass-fronted building under "
        "construction behind. No legible words."
    ),
    "tesla_1": (
        "Colour photograph: a red four-door saloon car driving on a road, seen from the "
        "front and side, with dark wheels. Pale mountains and a hazy sky behind. No "
        "legible words."
    ),
    "tesla_2": (
        "Colour photograph: a dark red four-door saloon car parked beside a white "
        'charging post marked "TESLA" in red, a cable running from the post to the '
        "car. A tree, a hedge and two distant figures behind, in hazy sunlight. A small "
        "red T-shaped emblem in the bottom right corner of the picture."
    ),
    "tesla_3": (
        "Colour photograph: a silver four-door saloon car driving on a road, seen from "
        "the front and side, with a blurred green and rocky hillside behind. A small "
        "emblem on the bonnet; no legible words."
    ),
    "kona_1": (
        "Colour photograph: a grey compact SUV parked on a road, seen side-on, facing "
        "left. A dry grassy hill and a clear blue sky behind. No legible words."
    ),
    "kona_2": (
        "Colour photograph: the front half of a bright blue compact SUV parked at the "
        "kerb, plugged into an orange and black charging post on the pavement at the "
        "left. A wooden wall and trees behind, in sunshine. The printing on the "
        "charging post is too small to read."
    ),
    "kona_3": (
        "Colour photograph: a grey compact SUV driving towards the camera on a curving "
        "road lined with trees and a grassy bank, its headlights on. An emblem on the "
        "front; no legible words."
    ),
}

# What QC and the tests check a description against: no appraisal of the vehicle.
APPRAISAL = (
    r"\b(sleek|rugged|powerful|stylish|luxur\w*|beautiful|attractive|modern|tough|sporty|"
    r"premium|elegant|impressive|eco\w*|stunning|cheap|expensive|fast|quick|efficient|"
    r"reliable|safe|clean|green energy|futuristic|innovative)\b"
)

INTRO_TREATED = "1,2,3,4"
INTRO_CONTROL = "5"
PAGES = "Then three pages, each a photo followed by text:"

GRIDS = {
    "REVIEW7": "ABCDEF",
    "REVIEW9": "ABCDEF",
    "ATTITUDES1": "ABC",
    "ATTITUDES2": "AB",
}
# Built in this order; task_num is the position.
OUTCOME_ORDER = [
    "REVIEW1",
    "REVIEW2",
    "REVIEW3",
    "REVIEW4",
    "REVIEW5",
    "REVIEW6",
    "REVIEW7",
    "REVIEW9",
    "ATTITUDES1",
    "ATTITUDES2",
    "INTEREST1",
]
BEFORE_STIMULUS = {"ATTITUDES1", "ATTITUDES2", "INTEREST1"}  # asked first by the control
YES_NO = {"REVIEW2", "REVIEW3", "INTEREST1"}


def image_key(vehicle: str, screen: int) -> str:
    return f"{vehicle}_{screen}"


def image_id(key: str) -> str:
    return f"{STUDY}_{key}"


def _ext(member: str) -> str:
    return Path(member).suffix.lower().replace(".jpeg", ".jpg")


def image_file(key: str, member: str) -> str:
    """Path under data/, as the catalogue records it."""
    return f"raw/{STUDY}/images/{key}{_ext(member)}"


# ---------------------------------------------------------------------------
# The questionnaire
# ---------------------------------------------------------------------------


def _clean(text: str) -> str:
    """Typography only: entities, markup, curly quotes, whitespace."""
    text = html.unescape(text)
    text = re.sub(r"</?(i|em|u|b)>", "", text)
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip()


def paragraphs(path: Path) -> list[tuple[str, list[str]]]:
    """(text, embedded media members) per paragraph, in document order."""
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
        rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
    target = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="(media/[^"]+)"', rels))
    out = []
    for para in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
        text = _clean("".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", para)))
        media = ["word/" + target[r] for r in re.findall(r'r:embed="(rId\d+)"', para)]
        if text or media:
            out.append((text, media))
    return out


def _texts(path: Path) -> list[str]:
    return [t for t, _ in paragraphs(path) if t]


DIRECTIVE = re.compile(r"IF DOV_EXP_RODE=(\d) OR DOV_CONTROL(?:=(\d))?:")


def stimuli() -> dict[tuple[str, int], tuple[str, str]]:
    """(vehicle, screen) -> (Q's media member, sentence), read in document order:
    the directive paragraph, then the picture, then the sentence."""
    paras = paragraphs(SIMPLE)
    by_code = {code: key for key, code, *_ in VEHICLES}
    out: dict[tuple[str, int], tuple[str, str]] = {}
    screen: int | None = None
    i = 0
    while i < len(paras):
        text, _ = paras[i]
        m = re.fullmatch(r"DISPLAY_STIMULI(\d)\.", text)
        if m:
            screen = int(m.group(1))
        elif text == "END OF STIMULI BLOCK":
            break
        elif screen is not None and (d := DIRECTIVE.fullmatch(text)):
            code = int(d.group(1))
            if d.group(2) is not None and int(d.group(2)) != code:
                raise SystemExit(f"directive names two codes: {text}")
            pic_text, media = paras[i + 1]
            sentence, after = paras[i + 2]
            if pic_text or len(media) != 1 or after:
                raise SystemExit(f"STIMULI{screen} code {code}: expected picture then text")
            out[(by_code[code], screen)] = (media[0], sentence)
            i += 3
            continue
        i += 1
    if sorted(out) != sorted((v, s) for v, *_ in VEHICLES for s in SCREENS):
        raise SystemExit(f"stimulus block changed: {sorted(out)}")
    return out


def q_directive_typos() -> list[str]:
    """Q's directives that omit DOV_CONTROL's code (read as the DOV_EXP_RODE code)."""
    return [t for t in _texts(SIMPLE) if DIRECTIVE.fullmatch(t) and t.endswith("DOV_CONTROL:")]


def prog_files() -> dict[int, list[str]]:
    """Screen -> PG's image file stems, in the order PG lists their directives."""
    lines = _texts(PROG)
    out: dict[int, list[str]] = {}
    screen = None
    for line in lines:
        m = re.fullmatch(r"DISPLAY_STIMULI(\d)\.", line)
        if m:
            screen = int(m.group(1))
            out[screen] = []
        elif line == "END OF STIMULI BLOCK":
            break
        elif screen is not None:
            for stem, n in re.findall(r"\\([A-Z]+)(\d)\.jpg", line):
                if int(n) != screen:
                    raise SystemExit(f"PG STIMULI{screen} names {stem}{n}.jpg")
                out[screen].append(stem)
    return out


def prog_directives() -> dict[int, list[tuple[int, int]]]:
    """Screen -> (DOV_EXP_RODE, DOV_CONTROL) pairs of PG's INSERT IMAGE directives."""
    text = "\n".join(_texts(PROG))
    block = text.split("BEGINNING OF STIMULI BLOCK", 1)[1].split("END OF STIMULI BLOCK", 1)[0]
    out: dict[int, list[tuple[int, int]]] = {}
    for part in re.split(r"DISPLAY_STIMULI(?=\d\.)", block)[1:]:
        screen = int(part[0])
        out[screen] = [
            (int(a), int(b))
            for a, b in re.findall(r"IF DOV_EXP_RODE=(\d) OR DOV_CONTROL=(\d), INSERT IMAGE", part)
        ]
    return out


def intro(which: str) -> str:
    """DISPLAY_INTRODUCTION for DOV_EXP_RODE in `which` ("1,2,3,4" or "5")."""
    prefix = f"[IF DOV_EXP_RODE={which}: "
    (line,) = [t for t in _texts(SIMPLE) if t.startswith(prefix)]
    if not line.endswith("]"):
        raise SystemExit(f"introduction not closed: {line}")
    return line[len(prefix) : -1]


def welcome() -> str:
    """WINTRO_1's line shown to everyone (PG marks it [ALL])."""
    (line,) = [t for t in _texts(PROG) if t.startswith("[ALL] ")]
    return line.removeprefix("[ALL] ")


def questions() -> dict[str, dict[str, Any]]:
    """Q's label -> {stem, items, options}, for the built questions."""
    lines = _texts(SIMPLE)
    out: dict[str, dict[str, Any]] = {}
    for label in OUTCOME_ORDER:
        start = lines.index(f"{label}.")
        stem: list[str] = []
        items: list[str] = []
        options: list[str] = []
        part = "stem"
        for line in lines[start + 1 :]:
            if (
                re.fullmatch(r"[A-Z_0-9]+\.", line)
                or line.startswith("DISPLAY IMAGE")
                or line.startswith("END OF")
                or line.startswith("[SHOW IF")
            ):
                break
            if line.startswith("GRID ITEMS"):
                part = "items"
            elif line.startswith("RESPONSE OPTIONS"):
                part = "options"
            elif part == "stem":
                stem.append(line)
            elif part == "items":
                items.append(line)
            else:
                options.append(line)
        out[label] = {"stem": " ".join(stem), "items": items, "options": options}
    return out


def check_prog_agrees() -> None:
    """PG must carry Q's words for everything the recipe quotes (Source authority)."""
    pg = _clean(" ".join(_texts(PROG)))
    quoted: list[str] = [intro(INTRO_TREATED), intro(INTRO_CONTROL)]
    quoted += [s for _, s in stimuli().values()]
    for q in questions().values():
        quoted += [q["stem"], *q["items"], *q["options"]]
    missing = [t for t in quoted if t not in pg]
    if missing:
        raise SystemExit(f"PG lacks Q's words: {missing}")
    files = prog_files()
    order = [stem for _, _, stem, _ in VEHICLES]
    if any(files[s] != order for s in SCREENS):
        raise SystemExit(f"PG's image order changed: {files}")
    dirs = prog_directives()
    codes = [code for _, code, *_ in VEHICLES]
    if any(dirs[s] != [(c, c) for c in codes] for s in SCREENS):
        raise SystemExit(f"PG's image directives changed: {dirs}")


def protestant_label() -> str:
    """RELIG code 1 in full; the .dta's label stops at 80 characters."""
    (line,) = [t for t in _texts(SIMPLE) if t.startswith("1 = Protestant (")]
    return line.split("=", 1)[1].strip()


def something_else() -> str:
    """RELIG code 14 without its text-box instruction. The .dta labels it "Something
    else, please specify:"; the answer is the words before the comma, as vemrp,
    xk9ch and s6urt rewrite the same AmeriSpeak code."""
    label = read_any(DTA).value_labels["RELIG"][14]
    if label != "Something else, please specify:":
        raise SystemExit(f"RELIG 14 label changed: {label!r}")
    return label.split(",", 1)[0]


# ---------------------------------------------------------------------------
# Pictures
# ---------------------------------------------------------------------------


def extract() -> None:
    """--prep: copy each photo out of Q, byte for byte."""
    IMAGES.mkdir(exist_ok=True)
    with zipfile.ZipFile(SIMPLE) as z:
        for (vehicle, screen), (member, _) in stimuli().items():
            key = image_key(vehicle, screen)
            (REPO / "data" / image_file(key, member)).write_bytes(z.read(member))


def _grey64(path: Path) -> np.ndarray:
    """The picture reduced to 64x64 grey by macOS sips (as gen_yjvpn)."""
    with tempfile.TemporaryDirectory() as tmp:
        bmp = Path(tmp) / "p.bmp"
        subprocess.run(
            ["sips", "-z", "64", "64", "-s", "format", "bmp", str(path), "--out", str(bmp)],
            check=True,
            capture_output=True,
        )
        b = bmp.read_bytes()
    offset = int.from_bytes(b[10:14], "little")
    width = int.from_bytes(b[18:22], "little", signed=True)
    bpp = int.from_bytes(b[28:30], "little")
    if width != 64 or bpp not in (24, 32):
        raise SystemExit(f"{path.name}: unexpected bitmap {width}x{bpp}")
    n = bpp // 8
    px = np.frombuffer(b[offset : offset + 64 * 64 * n], dtype=np.uint8).reshape(64, 64, n)
    grey: np.ndarray = px[:, :, :3].astype(float).mean(axis=2)
    return grey


def proposal_distances() -> dict[str, dict[str, float]]:
    """Proposal photograph (as vehicle_screen) -> {our key: mean grey-level distance}."""
    if not shutil.which("pdfimages") or not shutil.which("sips"):
        raise SystemExit("pdfimages (poppler) and sips (macOS) are needed for this check")
    ours = {
        image_key(v, s): _grey64(REPO / "data" / image_file(image_key(v, s), m))
        for (v, s), (m, _) in stimuli().items()
    }
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["pdfimages", "-j", "-f", "12", "-l", "14", str(PROPOSAL), f"{tmp}/p"],
            check=True,
            capture_output=True,
        )
        jpgs = sorted(Path(tmp).glob("p-*.jpg"))
        if len(jpgs) != len(PROPOSAL_ORDER):
            raise SystemExit(f"proposal pp. 12-14 hold {len(jpgs)} photographs, expected 12")
        return {
            image_key(v, s): {k: float(np.abs(_grey64(j) - a).mean()) for k, a in ours.items()}
            for (v, s), j in zip(PROPOSAL_ORDER, jpgs, strict=True)
        }


def verify_against_proposal() -> None:
    for theirs, dist in proposal_distances().items():
        nearest = min(dist, key=dist.__getitem__)
        others = [v for k, v in dist.items() if k != theirs]
        if nearest != theirs or dist[theirs] > 15.0 or min(others) < 30.0:
            raise SystemExit(f"proposal photo {theirs} is nearest {nearest}: {dist}")


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------


def catalogue_entries() -> dict[str, dict[str, str]]:
    """This study's entries in data/catalog/images.json, after checking each file is
    Q's picture for its directive, byte for byte."""
    from micromotives_datasets.images import sha256_of

    stems = {key: stem for key, _, stem, _ in VEHICLES}
    codes = {key: code for key, code, *_ in VEHICLES}
    out: dict[str, dict[str, str]] = {}
    with zipfile.ZipFile(SIMPLE) as z:
        for (vehicle, screen), (member, sentence) in stimuli().items():
            key = image_key(vehicle, screen)
            f = image_file(key, member)
            if (REPO / "data" / f).read_bytes() != z.read(member):
                raise SystemExit(f"{f} is not {member} of the fielded questionnaire")
            c = codes[vehicle]
            out[image_id(key)] = {
                "file": f,
                "sha256": sha256_of(REPO / "data" / f),
                "source": (
                    "OSF v6kqy, TESS deposit rode1532.zip: embedded in NORC's fielded "
                    f'questionnaire "9089.122_TESS_Rode_vFINALsimple.docx" as {member}, '
                    "copied byte for byte; it is the picture under that document's "
                    f'"IF DOV_EXP_RODE={c} OR DOV_CONTROL={c}" directive on '
                    f'DISPLAY_STIMULI{screen}, above the text "{sentence}" The '
                    f"programming version names the fielded file {stems[vehicle]}{screen}.jpg "
                    "on NORC's drive, which is not in the deposit, so this is the "
                    "questionnaire's copy and may differ from it in resolution or "
                    "encoding. The proposal (Rode1532.pdf, Appendix B) prints the same "
                    "photograph for the same vehicle and page."
                ),
                "licence": LICENCE,
                "text_in_image": TEXT_IN_IMAGE[key],
                "description": DESCRIPTIONS[key],
            }
    return out


def write_catalogue() -> None:
    """Add or refresh only this study's entries; re-read first, others are editing too."""
    verify_against_proposal()
    entries = catalogue_entries()
    path = REPO / "data" / "catalog" / "images.json"
    current = json.loads(path.read_text())
    current.update(entries)
    path.write_text(json.dumps(current, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# The derived data file
# ---------------------------------------------------------------------------


def derived_arm(exp: Any, control: Any) -> float:
    """V6KQY_ARM: DOV_EXP_RODE 1-4 as is; the control 5 + DOV_CONTROL (6-9)."""
    if pd.isna(exp):
        return float("nan")
    e = int(exp)
    if e != CONTROL_CODE:
        if not pd.isna(control):
            raise SystemExit("a treated respondent has a DOV_CONTROL code")
        return float(e)
    if pd.isna(control):
        raise SystemExit("a control respondent has no DOV_CONTROL code")
    return float(CONTROL_CODE + int(control))


def write_derived() -> None:
    import pyreadstat

    df, meta = pyreadstat.read_dta(str(DTA))
    df[ARM_VAR] = [derived_arm(e, c) for e, c in zip(df[COND_VAR], df[CONTROL_VAR], strict=True)]
    labels = dict(meta.variable_value_labels)
    labels[ARM_VAR] = {
        **{float(code): key.upper() for key, code, *_ in VEHICLES},
        **{float(CONTROL_CODE + code): f"CONTROL_{k.upper()}" for k, code, *_ in VEHICLES},
    }
    col_labels = dict(meta.column_names_to_labels)
    col_labels[ARM_VAR] = (
        "Derived (gen_v6kqy.py): DOV_EXP_RODE 1-4, or 5 + DOV_CONTROL for the control"
    )
    for c in df.columns:
        if not (
            pd.api.types.is_numeric_dtype(df[c]) or pd.api.types.is_datetime64_any_dtype(df[c])
        ):
            df[c] = df[c].astype(object)
    pyreadstat.write_sav(
        df,
        str(DERIVED),
        column_labels=[col_labels.get(c) or "" for c in df.columns],
        variable_value_labels={v: {float(k): s for k, s in m.items()} for v, m in labels.items()},
    )
    if not check_derived():
        raise SystemExit("derived file does not match the deposit")


def check_derived() -> bool:
    """Derived = deposit on every original column, plus V6KQY_ARM as derived_arm says."""
    a = read_any(DTA).df
    b = read_any(DERIVED).df
    if list(b.columns) != [*a.columns, ARM_VAR]:
        return False
    numeric = [c for c in a.columns if pd.api.types.is_numeric_dtype(a[c])]
    for c in numeric:
        if not a[c].astype(float).equals(b[c].astype(float)):
            return False
    expected = pd.Series(
        [derived_arm(e, c) for e, c in zip(a[COND_VAR], a[CONTROL_VAR], strict=True)],
        name=ARM_VAR,
    )
    return bool(b[ARM_VAR].astype(float).reset_index(drop=True).equals(expected))


# ---------------------------------------------------------------------------
# Recipe
# ---------------------------------------------------------------------------


def pages_text(vehicle: str) -> str:
    st = stimuli()
    parts = [f'<image> "{st[(vehicle, s)][1]}"' for s in SCREENS]
    return f"{PAGES} " + " ".join(parts)


def _scale(options: list[str]) -> dict[str, Any]:
    n = len(options)
    s: dict[str, Any] = {"min": 1, "max": n, "min_label": options[0], "max_label": options[-1]}
    if n % 2:
        s["mid_label"] = options[n // 2]
    return s


def recipe() -> dict[str, Any]:
    q = questions()
    check_prog_agrees()
    ds = read_any(DERIVED)
    if not check_derived():
        raise SystemExit("derived file is stale: run --prep")
    df, labels = ds.df, ds.value_labels

    codes = sorted(int(c) for c in df[COND_VAR].dropna().unique())
    if codes != [1, 2, 3, 4, 5]:
        raise SystemExit(f"{COND_VAR} codes changed: {codes}")
    if not df[ID_VAR].is_unique:
        raise SystemExit(f"{ID_VAR} is not unique")
    # The block orders the directive gives, one per group, recorded in ORDERA..F.
    treated = df[COND_VAR] != CONTROL_CODE
    orders = df[[f"ORDER{x}" for x in "ABCDE"]].astype(int)
    if not (orders[treated] == [1, 2, 3, 4, 5]).all().all():
        raise SystemExit("treated block order is not STIMULI, REVIEW_1, ATTITUDES, ...")
    if not (orders[~treated] == [3, 4, 1, 2, 5]).all().all():
        raise SystemExit("control block order is not ATTITUDES, INTEREST1, STIMULI, ...")
    if q_directive_typos() != ["IF DOV_EXP_RODE=1 OR DOV_CONTROL:"]:
        raise SystemExit(f"Q's directive typos changed: {q_directive_typos()}")

    outcomes: list[dict[str, Any]] = []
    for label in OUTCOME_ORDER:
        spec = q[label]
        opts = spec["options"]
        if label in YES_NO:
            if label in ("REVIEW2", "REVIEW3"):
                if opts != ["Yes", "No", "Unsure"] or labels[label].get(77) != "Unsure":
                    raise SystemExit(f"{label}: options or the Unsure code changed")
                opts = opts[:2]
            elif opts != ["Yes", "No"]:
                raise SystemExit(f"{label}: options changed")
            listed = "; ".join(f'{i} means "{o}"' for i, o in enumerate(opts, start=1))
            scale: dict[str, Any] = {"min": 1, "max": 2, "nominal": True}
            texts = [(label, f"{spec['stem']} {listed}.")]
        else:
            if len(opts) != 5:
                raise SystemExit(f"{label}: expected five options, got {opts}")
            scale = _scale(opts)
            if label in GRIDS:
                letters = GRIDS[label]
                if len(spec["items"]) != len(letters):
                    raise SystemExit(f"{label}: item count changed")
                texts = [
                    (f"{label}{x}", f"{spec['stem']} {item}")
                    for x, item in zip(letters, spec["items"], strict=True)
                ]
            else:
                texts = [(label, spec["stem"])]
        for var, text in texts:
            # The data's own labels must agree with Q's options (typography aside).
            got = [_clean(labels[var][k]) for k in range(1, len(opts) + 1)]
            expect = opts
            if got != expect:
                raise SystemExit(f"{var}: value labels {got} differ from Q's {expect}")
            o: dict[str, Any] = {
                "var": var,
                "task_num": len(outcomes),
                "question": text,
                "scale": scale,
                "response_recode": {i: i for i in range(1, len(opts) + 1)},
            }
            if label in BEFORE_STIMULUS:
                o["condition_var"] = COND_VAR
            outcomes.append(o)

    treated_intro, control_intro = intro(INTRO_TREATED), intro(INTRO_CONTROL)
    arms: list[dict[str, Any]] = []
    for key, code, *_ in VEHICLES:
        arms.append(
            {
                "raw": code,
                "condition_num": code - 1,
                "factors": {"vehicle": key, "order": "vehicle_first"},
                "text": f"{treated_intro} {pages_text(key)}",
                "images": [image_id(image_key(key, s)) for s in SCREENS],
            }
        )
    for key, code, *_ in VEHICLES:
        arms.append(
            {
                "raw": CONTROL_CODE + code,
                "condition_num": 3 + code,
                "factors": {"vehicle": key, "order": "questions_first"},
                "text": f"{control_intro} {pages_text(key)}",
                "images": [image_id(image_key(key, s)) for s in SCREENS],
            }
        )
    arms.append(
        {
            "raw": CONTROL_CODE,
            "condition_num": 8,
            "factors": {"vehicle": "none", "order": "questions_first"},
            "text": control_intro,
        }
    )
    if {int(k): v for k, v in labels[COND_VAR].items()} != {
        1: "LIGHTNING",
        2: "XLT",
        3: "TESLA",
        4: "KONA",
        5: "CONTROL",
    }:
        raise SystemExit(f"{COND_VAR} value labels changed: {labels[COND_VAR]}")

    return {
        "study_id": STUDY,
        "source": "tess",
        "title": "The Tesla effect: three photographs of one of four vehicles, shown before or "
        "after questions on electric vehicles and climate policy, then rated as a product",
        "data_file": DATA_FILE,
        "licence": LICENCE,
        "comparable_to_socsci210": True,
        "participant_id_var": ID_VAR,
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_var": ARM_VAR,
            "shared_context": welcome(),
            "factors": ["vehicle", "order"],
            "arms": arms,
            "considered_and_rejected": {
                CONTROL_VAR: "The control group's vehicle; folded into V6KQY_ARM "
                "(5 + DOV_CONTROL), which is the declared assignment.",
                **{
                    f"ORDER{x}": "Block order, fixed by DOV_EXP_RODE (one order for arms "
                    "1-4, one for the control; asserted); the timing it records is the "
                    "`order` factor."
                    for x in "ABCDEF"
                },
            },
        },
        "outcomes": outcomes,
        "response_recode": {},
        "missing_codes": [77, 98, 99],
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
            "party_id": "PARTYID7",
            "ideology": "IDEO",
            "religion": "RELIG",
            "religious_attendance": "ATTEND",
        },
        "persona_label_rewrite": {"RELIG": {1: protestant_label(), 14: something_else()}},
        "persona_missing": {
            "PARTYID7": [-1],
            "IDEO": [-1],
            "RELIG": [77, 98, 99],
            "ATTEND": [77, 98, 99],
            "GENDER": [0],
        },
    }


def render() -> str:
    return yaml.safe_dump(recipe(), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--prep", action="store_true", help="photos out of Q; the derived .sav")
    ap.add_argument("--catalogue", action="store_true", help="add this study's images.json entries")
    args = ap.parse_args()
    if args.prep:
        extract()
        write_derived()
        print(f"wrote {IMAGES.relative_to(REPO)}/ (12 photos) and {DERIVED.relative_to(REPO)}")
        return 0
    if args.catalogue:
        write_catalogue()
        print(f"updated data/catalog/images.json ({STUDY} entries only)")
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
