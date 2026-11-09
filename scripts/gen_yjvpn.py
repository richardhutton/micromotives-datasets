#!/usr/bin/env python3
"""Write recipes/images/yjvpn.yaml: a photo of "Alex", labelled transgender or cisgender.

Kubicki, TESS 1576 (fielded as NORC 9089.138), "The De-gendering and Dehumanization
of Transgender People". OSF yjvpn, the TESS deposit kubicki1576.zip: the data
(9089.138_TESS-Kubicki_20231109.dta), its codebook, the fielded questionnaire in a
simple and a programming version (9089.138_TESS-Kubicki_vfinal.simple.txt / .prog.txt,
"Q" and "PG" below), NORC's methods and transparency report, the proposal
(Kubicki1576.pdf) and the researcher's description document (Kubicki-1576.R2
description.docx, a Qualtrics export of the design).

AmeriSpeak, US adults screened to be cisgender (report: "Cisgender general Population
Age 18+"), web only (`SURV_MODE` 2 for all), English only, fielded 23 October to
1 November 2023. 914 completed; all 914 are in the file and all are built.

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* DESIGN. 3 x 2 between people, held in the preload `P_COND` (codebook: 1
  TransMasculine, 2 TransAndrogynous, 3 TransFem, 4 CisMasc, 5 CisAndro, 6 CisFem;
  147 / 165 / 143 / 156 / 145 / 158). One of three photographs of a person, each
  captioned with the name Alex and a gender identity. condition_num is P_COND - 1.
  The photo factor (`appearance`, the researcher's own masculine / androgynous /
  feminine) is carried by the picture alone; the label factor by the caption's words.
  QC rules 1 and 5 compare words AND images (docs/CONVENTIONS.md, Image conditions).
* WHICH PICTURE IS WHICH CONDITION. Q (and PG, identically) shows above every
  stimulus question: "IF P_COND=1 OR 4 SHOW 9089.0138_MASQUALITY.PNG / IF P_COND=2
  OR 5 SHOW 9089.0138_ANDROQUALITY.PNG / IF P_COND=3 OR 6 SHOW
  9089.013_FEMQUALITY.PNG" (the last file name's missing "8" is the
  questionnaire's). Parsed here, and the four copies (Q1, Q2, Q4, Q3) asserted
  identical in both files.
* PICTURES, AND THE CAVEAT. The fielded PNGs are NOT in the deposit. The only
  full-size copies are the three photographs embedded in the researcher's
  description document, word/media/image2.png, image6.png and image7.png (512 x 512
  RGBA PNGs, background cut away to transparency). Which is which is read from that
  document's own block structure: image2 sits under "Start of Block: TransMasculine"
  and "CisMasc", image6 under "TransAndrogynous" and "CisAndro", image7 under
  "TransFem" and "CisFem" (checked in --catalogue, from the .docx XML). A second,
  independent witness: the proposal (Kubicki1576.pdf, pp. 12-13) prints three
  photographs under "ANDROGYNOUS PHOTO", "FEMININE PHOTO" and "MASCULINE PHOTO";
  reduced to 64 x 64 grey, each is nearest the description document's picture of
  the same name, by a wide margin (checked in --catalogue: within 4.7 / 11.2 / 4.7
  grey levels of its own and at least 30.5 from either other). So the faces are the
  study's faces. What cannot be shown is that these are the exact files NORC
  displayed: the description document is the researcher's Qualtrics draft, NORC
  renamed the files (MASQUALITY etc.), and the fielded copies may differ in
  resolution, cropping or encoding. Recorded in each catalogue entry's source. The
  proposal says the photographs were "generated from artificial intelligence"; it
  does not name the tool. No words are printed on any of them.
* CONDITION. shared_context is the instruction screen INSTRUC, word-for-word from Q
  (PG's copy is the same words, asserted, once its <em> tags and [SPACE] markers are
  removed). It is the screen every respondent read before the photo, and it holds the
  study's own definitions of cisgender and transgender. The welcome screen WINTRO_1
  (thanks, AmeriPoints, the Continue button) is survey mechanics and is dropped.
  Each arm is then the photo and its caption, "Alex, Transgender" or "Alex,
  Cisgender", word-for-word from Q, which Q says is centred under the image. The
  connecting words are OURS: 'A photo: <image> Centred beneath the photo: "Alex,
  Transgender"'. They say only what the directive says was on screen.
* OUTCOMES. Twenty, each asked on a screen with the same photo and caption above it:
  - Q1A-Q1Q (task 0-16): the 17 traits of grid Q1, each the grid's stem then the
    trait, joined with a space ("...typical of the individual in the photo?
    Ambitious"). The trait in each variable is read from the codebook's bracketed
    label and asserted to be Q's listing order. Answers 1-7, Extremely
    uncharacteristic .. Extremely characteristic, midpoint "Neither uncharacteristic
    nor characteristic". Trait order was randomised and recorded (Q1_ORDER*); no row
    says where its trait sat.
  - Q2 (task 17): the 0-100 feeling thermometer, a slider, word-for-word. The data's
    value labels on 0, 15, 30 .. 100 ("Very cold or unfavorable feeling" etc.) are
    the panel's stock thermometer labels and are NOT on the fielded screen (Q says
    only "[SLIDER [RANGE 0 TO 100]]"), so the scale carries no endpoint labels; the
    question's own words explain it. Its non-answers are 777 / 998 / 999 (this
    variable's own labels), so 77, 98 and 99 are SLIDER POSITIONS: 6, 4 and 14
    people, in a smooth distribution (76: 7, 78: 5, 97: 4, 100: 50). They are kept.
    The study's missing codes 77 / 98 / 99 are therefore NOT declared globally
    (`missing_codes` is empty); each outcome's own recode lists its valid codes and
    drops the rest.
  - Q3 (task 18): difficulty of determining Alex's gender, 1-5, Not at all difficult
    .. Extremely difficult, midpoint Slightly difficult.
  - Q4 (task 19): "If you saw Alex in passing, you would immediately think of them as
    a:", NOMINAL, options enumerated in the question as the instrument lists them
    (Man / Woman / Uncertain / "Other, please describe:"). Code 4 is kept as a real
    answer (10 people); the words they typed (`Q4_OE`) are free text and not built.
  Q1 and Q2 were shown in random order (ORDER1/ORDER2), then Q4, then Q3: the fielded
  order puts Q4 BEFORE Q3, so task numbers follow the variable names, not the screens.
  Every one of these screens repeated the photo and caption, so every row's
  condition is literally what was above its question. The order variables (ORDER1/2,
  Q1_ORDER*, and those of the unbuilt checks and moderator block) record
  presentation order, not manipulations, and are listed in `considered_and_rejected`.
* NOT BUILT. Q5 (the name of the person) and Q6 (their gender identity) are the
  attention / manipulation checks: their answers are stated in the condition, so
  they are not outcomes (docs/CONVENTIONS.md). Q7 (nine items of a genderism and
  transphobia scale) and Q8 / Q9 (how often the respondent has encountered
  transgender people, and stories about them in the media) are the proposal's
  moderator block ("Transphobia;Familiarity"), asked of everyone after the checks.
  They are statements about the respondent, not about the photo or Alex, so they
  are not outcomes of this manipulation (zaqkm's contact item and s6urt's profile
  items, the same call); and being asked after the stimulus, they are not
  admissible as persona either, which for Q7 the domain rule would forbid anyway.
  SocSci210 did not build them. Cost: up to 9 x 914 + 2 x 914 = 10,054 answers.
* WHO. All 914 completes. `CaseId` is the participant id. Respondents answered each
  question or skipped it (98 "SKIPPED ON WEB" on Q1/Q3/Q4: 4 to 11 per item; 998 on
  Q2: 61; 777 / 999 never occur); each skip drops only that row.
* PERSONA. The standard AmeriSpeak preloads, the same field set and variables as
  8ctbk: AGE, GENDER, EDUC5 (the file has no EDUC), RACETHNICITY, INCOME (18 bands),
  MARITAL, EMPLOY, REGION4, HHSIZE, HOME_TYPE, HOUSING, METRO, INTERNET,
  PHONESERVICE, PartyID7, IDEO, RELIG, ATTEND. Left absent: PartyID7 and IDEO -1
  "Unknown", RELIG / ATTEND 77 / 98 / 99, GENDER 0 "Unknown" (as 8ctbk; codes that
  do not occur here are inert). Not mapped: STATE, REGION9 (finer than every other
  TESS build's region), the banded duplicates AGE4 / AGE7 / INCOME4 / INCOME9, the
  household age counts, PartyID5. RELIG code 1's label is cut off at 80 characters
  in the .dta ("... Presbyterian, Pent"); `persona_label_rewrite` restores the whole
  answer from Q's demographic profile, as 9xw67 does. Every respondent was screened
  cisgender, so no persona field records gender identity; the caption names a
  category no persona field holds, so nothing in a row can be matched by
  substitution.
* UK FIT. The photo, the name, the definitions and the questions name no US place,
  law, party or institution; the rescan screen called it a full transfer. US
  spellings ("favorable") are kept word-for-word. The sample is American.
* ANSWER KEY. SocSci210 holds this study: 18,069 rows over six conditions. Our build
  has the same rows per condition and the same response distribution (crosscheck).
  SocSci210 groups the 20 outcomes into 5 tasks (12 traits, 5 traits, Q2, Q3, Q4)
  and words its conditions from the proposal ("How difficult would it be ..."), not
  from the fielded instrument; task counts are reported, not failed.
* NOT ASKED OF JEV. The assignment is the preload the questionnaire's own directives
  name, the persona is 8ctbk's, and each outcome's non-answer codes are its own value
  labels; no paid call.

    uv run python scripts/gen_yjvpn.py --prep       # extract the three photos from the .docx
    uv run python scripts/gen_yjvpn.py --catalogue  # (re)write this study's images.json entries
    uv run python scripts/gen_yjvpn.py              # write the recipe
    uv run python scripts/gen_yjvpn.py --check      # exit 1 if it differs
"""

from __future__ import annotations

import argparse
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

STUDY = "yjvpn"
RAW = REPO / "data" / "raw" / STUDY
DATA_FILE = "9089.138_TESS-Kubicki_20231109.dta"
SIMPLE = RAW / "9089.138_TESS-Kubicki_vfinal.simple.txt"
PROG = RAW / "9089.138_TESS-Kubicki_vfinal.prog.txt"
CODEBOOK = RAW / "9089.138_TESS-Kubicki_Codebook_20231109.xlsx"
DESCRIPTION = RAW / "Kubicki-1576.R2 description.docx"
PROPOSAL = RAW / "Kubicki1576.pdf"
IMAGES = RAW / "images"
RECIPE = REPO / "recipes" / "images" / f"{STUDY}.yaml"
LICENCE = (
    "None stated: the TESS deposit on OSF (yjvpn, kubicki1576.zip) gives no reuse terms, "
    "and TESS has since suspended operations. Used with rich's ruling of 9 Nov 2026 that "
    "an unstated licence does not block an image build."
)

ID_VAR = "CaseId"
COND_VAR = "P_COND"

# The three photographs: (key, fielded file name in Q, P_CONDs, docx member,
# description-document blocks, proposal heading). Keys are the researcher's labels.
PHOTOS: list[tuple[str, str, tuple[int, int], str, tuple[str, str], str]] = [
    (
        "masculine",
        "9089.0138_MASQUALITY.PNG",
        (1, 4),
        "word/media/image2.png",
        ("TransMasculine", "CisMasc"),
        "MASCULINE PHOTO",
    ),
    (
        "androgynous",
        "9089.0138_ANDROQUALITY.PNG",
        (2, 5),
        "word/media/image6.png",
        ("TransAndrogynous", "CisAndro"),
        "ANDROGYNOUS PHOTO",
    ),
    (
        "feminine",
        "9089.013_FEMQUALITY.PNG",
        (3, 6),
        "word/media/image7.png",
        ("TransFem", "CisFem"),
        "FEMININE PHOTO",
    ),
]
# The proposal's photographs, in page order (pdfimages -f 12 -l 13), and their headings.
PROPOSAL_ORDER = ["ANDROGYNOUS PHOTO", "FEMININE PHOTO", "MASCULINE PHOTO"]

# Visible facts only. No gender, age, ethnicity, emotion or appraisal: the study
# measures how people read this person's gender, so a description must not.
DESCRIPTIONS: dict[str, str] = {
    "masculine": (
        "Colour photograph, square: one person's head and the top of the shoulders, "
        "face-on, looking at the camera, mouth closed. Short dark brown hair, cut short at "
        "the sides and longer on top, brushed up and to one side. A dark grey collared top "
        "shows at the bottom edge. No jewellery is visible. The background is cut away "
        "(transparent in the file). No words."
    ),
    "androgynous": (
        "Colour photograph, square: one person's head and neck, face-on, looking at the "
        "camera, mouth closed. Short light brown hair, cut close at the sides and longer "
        "on top, brushed up and back. A grey crew-neck top shows at the bottom edge. No "
        "jewellery is visible. The background is cut away (transparent in the file). No "
        "words."
    ),
    "feminine": (
        "Colour photograph, square: one person's head and neck, face-on, looking at the "
        "camera, mouth closed. Brown hair parted in the middle, falling past the ears to "
        "about the shoulders. A small stud earring in the ear on the right of the picture. "
        "A pale pink-beige top shows at the bottom edge. The background is cut away "
        "(transparent in the file). No words."
    ),
}

# (factor level, caption P_CONDs in Q's directive)
LABELS: list[tuple[str, tuple[int, int, int]]] = [
    ("transgender", (1, 2, 3)),
    ("cisgender", (4, 5, 6)),
]
# The codebook's value labels for P_COND, which are also the description document's
# block names: each photo's two blocks (PHOTOS) must be two of these.
P_COND_LABELS = {
    1: "TransMasculine",
    2: "TransAndrogynous",
    3: "TransFem",
    4: "CisMasc",
    5: "CisAndro",
    6: "CisFem",
}
STIMULUS_QUESTIONS = ["Q1", "Q2", "Q4", "Q3"]  # the fielded order of the screens
LEAD = "A photo:"
BENEATH = "Centred beneath the photo:"

TRAIT_VARS = [f"Q1{c}" for c in "ABCDEFGHIJKLMNOPQ"]


def image_id(key: str) -> str:
    return f"yjvpn_{key}"


def image_file(key: str) -> str:
    """Path under data/, as the catalogue records it."""
    return f"raw/{STUDY}/images/{key}.png"


# ---------------------------------------------------------------------------
# The questionnaire
# ---------------------------------------------------------------------------


def _clean(text: str) -> str:
    """Typography only: the programming copy's markup, curly quotes, whitespace."""
    text = re.sub(r"</?(em|u)>", "", text)
    text = text.replace("[SPACE]", " ").replace("[TEXTBOX]", "")
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip()


def _lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def sections(path: Path) -> dict[str, list[str]]:
    """Label line ("INSTRUC.", "Q1.") -> its lines, up to the next label or block header.

    Programming markup that sits between questions (timestamp instructions, [GRID],
    [SP], [SLIDER ...], [DISPLAY]) is skipped, so a section holds only screen text and
    the directives above it."""
    out: dict[str, list[str]] = {}
    current: str | None = None
    for line in _lines(path):
        s = line.strip()
        m = re.fullmatch(r"(WINTRO_1|INSTRUC|Q\d+|DEMO_INTRO)\.", s)
        if m:
            current = m.group(1)
            out[current] = []
            continue
        if s.isupper() and ("BLOCK" in s or s.startswith("ATTENTION")):
            current = None
            continue
        if s.startswith("#") or s.startswith("INSERT END TIMESTAMPS"):
            continue
        if re.match(r"\[(GRID|SP\]|SLIDER|SHOW ALL|DISPLAY)", s):
            continue
        if current is not None:
            out[current].append(line)
    return out


DIRECTIVE = re.compile(r"\s*(\[IF P_COND=.*?\]\s*\[CENTER UNDER IMAGE.*?\])", flags=re.S)


def _directive(lines: list[str]) -> str:
    """The [IF P_COND ...] image directive and the caption directive above a question."""
    m = DIRECTIVE.match("\n".join(lines))
    if not m:
        raise SystemExit("no image directive where one was expected")
    return m.group(1)


def _after_directive(lines: list[str]) -> list[str]:
    text = "\n".join(lines)
    m = DIRECTIVE.match(text)
    if not m:
        raise SystemExit("no image directive where one was expected")
    return text[m.end() :].splitlines()


def _bullets(lines: list[str], header: str) -> list[str]:
    """The bulleted (or numbered) options after a header line, up to the next blank run."""
    start = next(i for i, x in enumerate(lines) if x.strip().startswith(header))
    out: list[str] = []
    for x in lines[start + 1 :]:
        s = x.strip()
        if not s:
            if out:
                break
            continue
        if s.startswith("RESPONSE OPTIONS") or s.startswith("GRID ITEMS"):
            break
        out.append(_clean(re.sub(r"^(•|\d\d)\s*", "", s)))
    return out


def _stem(lines: list[str]) -> str:
    """The question's words: what follows the directive, up to its options."""
    body = []
    for x in _after_directive(lines):
        s = x.strip()
        if s.startswith("GRID ITEMS") or s.startswith("RESPONSE OPTIONS"):
            break
        body.append(s)
    return _clean(" ".join(body))


def instrument(path: Path) -> dict[str, Any]:
    """Everything the recipe quotes, parsed from one questionnaire file."""
    sec = sections(path)
    directives = [_directive(sec[q]) for q in STIMULUS_QUESTIONS]
    if any(_clean(d) != _clean(directives[0]) for d in directives):
        raise SystemExit(f"{path.name}: the four stimulus screens' directives differ")
    d = _clean(directives[0])
    photos = {
        (int(a), int(b)): f for a, b, f in re.findall(r"IF P_COND=(\d) OR (\d) SHOW (\S+\.PNG)", d)
    }
    captions = {
        tuple(int(x) for x in re.findall(r"\d", conds)): caption.strip()
        for conds, caption in re.findall(r"IF P_CONDITION=\s*([\d, OR]+?) SHOW (Alex, \w+)", d)
    }
    return {
        "instruc": _clean(" ".join(sec["INSTRUC"])),
        "photos": photos,
        "captions": captions,
        "q1_stem": _stem(sec["Q1"]),
        "traits": _bullets(sec["Q1"], "GRID ITEMS"),
        "q1_options": _bullets(sec["Q1"], "RESPONSE OPTIONS"),
        "q2": _stem(sec["Q2"]),
        "q3": _stem(sec["Q3"]),
        "q3_options": _bullets(sec["Q3"], "RESPONSE OPTIONS"),
        "q4": _stem(sec["Q4"]),
        "q4_options": _bullets(sec["Q4"], "RESPONSE OPTIONS"),
        "slider": "[SLIDER [RANGE 0 TO 100]]" in "\n".join(_lines(path)),
    }


def fielded() -> dict[str, Any]:
    """Q, after asserting PG says the same words (docs/CONVENTIONS.md, Source authority)."""
    q, pg = instrument(SIMPLE), instrument(PROG)
    if q != pg:
        diff = {k: (q[k], pg[k]) for k in q if q[k] != pg[k]}
        raise SystemExit(f"simple and prog questionnaires disagree: {diff}")
    expected_photos = {conds: name for _, name, conds, *_ in PHOTOS}
    if q["photos"] != expected_photos:
        raise SystemExit(f"image directive changed: {q['photos']}")
    expected_captions = {conds: f"Alex, {level.capitalize()}" for level, conds in LABELS}
    if q["captions"] != expected_captions:
        raise SystemExit(f"caption directive changed: {q['captions']}")
    return q


def protestant_label() -> str:
    """RELIG code 1 in full. The .dta's label stops at 80 characters ("... Presbyterian,
    Pent"); Q's demographic profile gives the whole answer (as 9xw67)."""
    (line,) = [x for x in _lines(SIMPLE) if x.strip().startswith("1 = Protestant (")]
    return _clean(line.split("=", 1)[1])


def codebook_traits() -> dict[str, str]:
    """Q1A..Q1Q -> the trait in the codebook's bracketed label."""
    cb = pd.read_excel(CODEBOOK, header=None)
    out = {}
    for _, r in cb.iterrows():
        var = str(r.iloc[0]).strip()
        if var in TRAIT_VARS:
            m = re.match(r"\[(\w+)\]", str(r.iloc[1]))
            if not m:
                raise SystemExit(f"{var}: codebook label has no [trait]")
            out[var] = m.group(1)
    return out


# ---------------------------------------------------------------------------
# Pictures
# ---------------------------------------------------------------------------


def docx_blocks() -> dict[str, list[str]]:
    """Description-document block name -> the docx media files it embeds, in order."""
    with zipfile.ZipFile(DESCRIPTION) as z:
        xml = z.read("word/document.xml").decode("utf-8")
        rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
    target = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="(media/[^"]+)"', rels))
    out: dict[str, list[str]] = {}
    block: str | None = None
    for para in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
        text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", para))
        if text.startswith("Start of Block: "):
            block = text.removeprefix("Start of Block: ").strip()
            out[block] = []
        elif text.startswith("End of Block: "):
            block = None
        elif block is not None:
            out[block] += [
                "word/" + target[r] for r in re.findall(r'r:embed="(rId\d+)"', para) if r in target
            ]
    return out


def photo_member(key: str) -> str:
    """The docx member that BOTH of the photo's blocks show as their large picture, and
    no other condition block shows."""
    (_, _, conds, member, blocks, _) = next(p for p in PHOTOS if p[0] == key)
    if tuple(P_COND_LABELS[c] for c in conds) != blocks:
        raise SystemExit(f"{key}: blocks {blocks} are not P_COND {conds}'s labels")
    by_block = docx_blocks()
    big = {
        b: {m for m in media if m.endswith(".png") and _png_size(m) == (512, 512)}
        for b, media in by_block.items()
    }
    for b in blocks:
        if big.get(b) != {member}:
            raise SystemExit(f"block {b} shows {big.get(b)}, expected {member}")
    others = {m for b, ms in big.items() if b not in blocks for m in ms}
    if member in others:
        raise SystemExit(f"{member} also appears outside {blocks}")
    return member


def _png_size(member: str) -> tuple[int, int]:
    with zipfile.ZipFile(DESCRIPTION) as z:
        head = z.read(member)[:24]
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return (0, 0)
    return (int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big"))


def extract() -> None:
    """--prep: copy each photo out of the description document, byte for byte."""
    IMAGES.mkdir(exist_ok=True)
    with zipfile.ZipFile(DESCRIPTION) as z:
        for key, *_ in PHOTOS:
            (IMAGES / f"{key}.png").write_bytes(z.read(photo_member(key)))


def _grey64(path: Path) -> np.ndarray:
    """The picture reduced to 64x64 grey by macOS sips (as gen_a4y7s_study2)."""
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
    """Proposal heading -> {photo key: mean grey-level distance}. Needs pdfimages and sips."""
    if not shutil.which("pdfimages") or not shutil.which("sips"):
        raise SystemExit("pdfimages (poppler) and sips (macOS) are needed for this check")
    ours = {key: _grey64(REPO / "data" / image_file(key)) for key, *_ in PHOTOS}
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["pdfimages", "-j", "-f", "12", "-l", "13", str(PROPOSAL), f"{tmp}/p"],
            check=True,
            capture_output=True,
        )
        jpgs = sorted(Path(tmp).glob("p-*.jpg"))
        if len(jpgs) != len(PROPOSAL_ORDER):
            raise SystemExit(f"proposal pp. 12-13 hold {len(jpgs)} photographs, expected 3")
        return {
            heading: {k: float(np.abs(_grey64(j) - a).mean()) for k, a in ours.items()}
            for heading, j in zip(PROPOSAL_ORDER, jpgs, strict=True)
        }


def verify_against_proposal() -> None:
    for heading, dist in proposal_distances().items():
        key = next(p[0] for p in PHOTOS if p[5] == heading)
        others = [v for k, v in dist.items() if k != key]
        if dist[key] > 15.0 or min(others) < 25.0:
            raise SystemExit(f"{heading}: distances {dist}")


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------


def catalogue_entries() -> dict[str, dict[str, str]]:
    """This study's entries in data/catalog/images.json, after checking each file is the
    description document's picture for its blocks, byte for byte."""
    from micromotives_datasets.images import sha256_of

    out: dict[str, dict[str, str]] = {}
    with zipfile.ZipFile(DESCRIPTION) as z:
        for key, fielded_name, conds, _, blocks, heading in PHOTOS:
            member = photo_member(key)
            f = image_file(key)
            data = (REPO / "data" / f).read_bytes()
            if data != z.read(member):
                raise SystemExit(f"{f} is not {member} of the description document")
            out[image_id(key)] = {
                "file": f,
                "sha256": sha256_of(REPO / "data" / f),
                "source": (
                    f"OSF yjvpn, TESS deposit kubicki1576.zip: embedded in the researcher's "
                    f'"Kubicki-1576.R2 description.docx" as {member}, copied byte for byte; '
                    f"that document shows it in blocks {blocks[0]} and {blocks[1]}, and the "
                    f'proposal (Kubicki1576.pdf) prints the same face under "{heading}". '
                    f"The fielded questionnaire shows {fielded_name} for P_COND "
                    f"{conds[0]} and {conds[1]}; that file is not in the deposit, so this is "
                    "the researcher's copy and may differ from it in resolution, cropping "
                    "or encoding. The proposal says the photographs were generated with "
                    "artificial intelligence."
                ),
                "licence": LICENCE,
                "text_in_image": "",
                "description": DESCRIPTIONS[key],
            }
    return out


def write_catalogue() -> None:
    """Add or refresh only this study's entries; re-read first, others are editing too."""
    verify_against_proposal()
    path = REPO / "data" / "catalog" / "images.json"
    current = json.loads(path.read_text())
    current.update(catalogue_entries())
    path.write_text(json.dumps(current, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Recipe
# ---------------------------------------------------------------------------


def arm_text(level: str) -> str:
    return f'{LEAD} <image> {BENEATH} "Alex, {level.capitalize()}"'


def _scale(options: list[str]) -> dict[str, Any]:
    n = len(options)
    s: dict[str, Any] = {"min": 1, "max": n, "min_label": options[0], "max_label": options[-1]}
    if n % 2:
        s["mid_label"] = options[n // 2]
    return s


def recipe() -> dict[str, Any]:
    q = fielded()
    ds = read_any(RAW / DATA_FILE)
    labels = ds.value_labels

    if sorted(int(c) for c in ds.df[COND_VAR].dropna().unique()) != list(range(1, 7)):
        raise SystemExit(f"{COND_VAR} codes changed")
    if not ds.df[ID_VAR].is_unique:
        raise SystemExit(f"{ID_VAR} is not unique")

    traits = codebook_traits()
    if [traits[v] for v in TRAIT_VARS] != q["traits"]:
        raise SystemExit("codebook trait order differs from the questionnaire's listing")
    if len(q["q1_options"]) != 7 or len(q["q3_options"]) != 5 or len(q["q4_options"]) != 4:
        raise SystemExit("an option list changed length")
    # The data's own labels must agree with the questionnaire's words (typography aside).
    for var, options in [("Q1A", q["q1_options"]), ("Q3", q["q3_options"])]:
        if [labels[var][k] for k in range(1, len(options) + 1)] != options:
            raise SystemExit(f"{var}: value labels differ from the questionnaire")
    if not q["slider"]:
        raise SystemExit("Q2 is no longer a 0-100 slider")
    for var in ("Q2",):
        if {777, 998, 999} - set(labels[var]):
            raise SystemExit("Q2's non-answer codes changed")

    outcomes: list[dict[str, Any]] = []
    for t, (var, trait) in enumerate(zip(TRAIT_VARS, q["traits"], strict=True)):
        outcomes.append(
            {
                "var": var,
                "task_num": t,
                "question": f"{q['q1_stem']} {trait}",
                "scale": _scale(q["q1_options"]),
                "response_recode": {i: i for i in range(1, 8)},
            }
        )
    outcomes.append(
        {
            "var": "Q2",
            "task_num": 17,
            "question": q["q2"],
            "scale": {"min": 0, "max": 100},
            "response_recode": {i: i for i in range(0, 101)},
        }
    )
    outcomes.append(
        {
            "var": "Q3",
            "task_num": 18,
            "question": q["q3"],
            "scale": _scale(q["q3_options"]),
            "response_recode": {i: i for i in range(1, 6)},
        }
    )
    listed = "; ".join(f'{i} means "{o}"' for i, o in enumerate(q["q4_options"], start=1))
    outcomes.append(
        {
            "var": "Q4",
            "task_num": 19,
            "question": f"{q['q4']} {listed}.",
            "scale": {"min": 1, "max": 4, "nominal": True},
            "response_recode": {i: i for i in range(1, 5)},
        }
    )

    arms: list[dict[str, Any]] = []
    for key, _, conds, *_ in PHOTOS:
        for level, label_conds in LABELS:
            (code,) = set(conds) & set(label_conds)
            arms.append(
                {
                    "raw": code,
                    "condition_num": code - 1,
                    "factors": {"appearance": key, "label": level},
                    "text": arm_text(level),
                    "images": [image_id(key)],
                }
            )
    arms.sort(key=lambda a: int(a["condition_num"]))
    if {int(k): v for k, v in labels[COND_VAR].items()} != P_COND_LABELS:
        raise SystemExit(f"{COND_VAR} value labels changed: {labels[COND_VAR]}")

    return {
        "study_id": STUDY,
        "source": "tess",
        "title": "The De-gendering and Dehumanization of Transgender People: one of three "
        "photographs of Alex, captioned transgender or cisgender, rated on 17 traits, warmth, "
        "how hard Alex's gender is to tell and what it is",
        "data_file": DATA_FILE,
        "licence": LICENCE,
        "comparable_to_socsci210": True,
        "participant_id_var": ID_VAR,
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_var": COND_VAR,
            "shared_context": q["instruc"],
            "factors": ["appearance", "label"],
            "arms": arms,
            "considered_and_rejected": {
                "RND_00": "Order of the two checks Q5/Q6, both not built; asked after "
                "every built outcome.",
                "ORDER1": "Records whether Q1 or Q2 came first; presentation order, "
                "not a manipulation, and no row says where it sat.",
                "ORDER2": "The other half of ORDER1.",
                **{
                    f"RAN{i}_Q{q}": f"Order of Q{q}'s response options; Q{q} is a "
                    "manipulation check, not built."
                    for q, n in ((5, 5), (6, 2))
                    for i in range(1, n + 1)
                },
                **{
                    f"ORDER{x}1": "Order of Q7, Q8 and Q9, the moderator block, not built; "
                    "asked after every built outcome."
                    for x in "ABC"
                },
                **{
                    f"Q7_ORDER{i}": "Order of Q7's grid items, not built; asked after "
                    "every built outcome."
                    for i in range(1, 10)
                },
            },
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
            "ideology": "IDEO",
            "religion": "RELIG",
            "religious_attendance": "ATTEND",
        },
        "persona_label_rewrite": {"RELIG": {1: protestant_label()}},
        "persona_missing": {
            "PartyID7": [-1],
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
    ap.add_argument("--prep", action="store_true", help="extract the photos from the .docx")
    ap.add_argument("--catalogue", action="store_true", help="add this study's images.json entries")
    args = ap.parse_args()
    if args.prep:
        extract()
        print(f"wrote {IMAGES.relative_to(REPO)}/{{masculine,androgynous,feminine}}.png")
        return 0
    if args.catalogue:
        write_catalogue()
        print("updated data/catalog/images.json (yjvpn entries only)")
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
