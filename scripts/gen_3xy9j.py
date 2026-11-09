#!/usr/bin/env python3
"""Write recipes/images/3xy9j.yaml: a stroke or a cardiac arrest, its treatment's
outcomes for 100 people as an icon chart, asked as a choice or without consent, then
seven statements about medical decisions.

Chiong, TESS3 133 (GfK SNO 17158, February 2013), "An experiment on the presumption
of consent to emergency medical treatment". OSF 3xy9j: the proposal (Chiong300.pdf,
TESS-0300.R1) and the TESS deposit Chiong300.zip, unpacked to "TESS133 - Chiong -
Final Deliverables/": the data (TESS3133_Chiong_Client_Final Data.sav), the fielded
questionnaire as a Word file (TESS3 133 Chiong Survey_Final.docx, "Q" below) with a
plain-text copy (.txt, "QT"), the response rate report and GfK's methodology note.

KnowledgePanel, US adults aged 50 and over (PPAGE 50 to 94; the proposal: "older (50+)
American adults"), web. 2,154 in the file, all with an assignment.

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* DESIGN. 2 x 2 between people, held in the preload `XTESS133` (Q's study details:
  "1 =Group1a; 2 =Group 1b; 3 =Group 2a; 4 =Group 2b"; .sav: Group 1a .. Group 2b;
  545 / 534 / 555 / 520). The proposal names the factors: clinical scenario (a stroke
  treated with the clot-dissolving medicine t-PA, or a cardiac arrest treated with
  CPR) and question type (a hypothetical choice, or treatment "in the absence of
  consent or surrogate input"). Q's screens: [IF XTESS133=1] Q1a stroke / choice,
  =2 Q1b stroke / without consent, =3 Q1c cardiac arrest / choice, =4 Q1d cardiac
  arrest / without consent. condition_num is XTESS133 - 1. Each group answers its own
  variable, Q1A .. Q1D (every other group's copy is blank), declared per arm.
  The recipe_prep call agreed: XTESS133, confidence 1.00.
* WHY AN IMAGE EXPERIMENT. Each scenario screen shows a chart between the scenario and
  the sentence "This graphic shows ...". Read from Q's document.xml in order: the
  screens for XTESS133 = 1 and 2 embed relationship rId12 = word/media/image2.png and
  those for 3 and 4 embed rId13 = word/media/image3.png, one picture per screen and no
  other picture in the body (checked here). So the picture VARIES WITH THE SCENARIO
  factor and is identical within it. It repeats the text's numbers (checked: the
  figures of each colour are counted from the file and equal the numbers in the
  paragraph under it), but it is part of what every respondent saw, the paragraph
  under it cites it ("This graphic shows"), and it carries what the text does not:
  the layout of the 100 figures, the legend's own category names, and for the cardiac
  arrest the 83 "Dead" that the text leaves as "most of them ... would die". Built as
  an image experiment, so a text-only reader still has every number and a vision
  reader has the chart. The proposal says the stroke chart follows published
  guidance on figures for stroke thrombolysis (Gadhia et al. 2010).
* PICTURES. Copied byte for byte out of Q (the fielded questionnaire itself, not a
  draft), 550 x 529 RGBA PNGs: stroke.png (image2) and cpr.png (image3). Whether GfK
  displayed them at this size cannot be known from the deposit. Each is a 10 x 10
  grid of identical head-and-shoulders figures, coloured by outcome, with a legend on
  the right. The figure counts in each description are measured from the file
  (`icon_counts`, by the colour of each figure's body against the legend's
  swatches), not read by eye. The other pictures in Q's media folder are not shown on
  any screen of the body (logos in the headers).
* CONDITION. shared_context is the paragraph that opens every scenario screen ("In
  medical emergencies, ... their health care."), word-for-word and identical on all
  four (asserted), its "Q1a." label removed. Each arm is then the scenario's two
  paragraphs, `<image>` where the chart sits, and the paragraph under the chart, all
  word-for-word. For the two without-consent groups the screen's last paragraph is
  "Imagine that the doctors [paramedics] cannot communicate with you ... whether you
  would want this treatment. Even though the doctors [paramedics] are not able to
  obtain your consent, would you want them to treat you with this medicine [CPR]?":
  its first sentence states the situation and goes in the condition; its second is
  the question and is the outcome. No words of ours are added to task 0's condition
  (for tasks 1-7, see OUTCOMES). Response
  options and screen mechanics ([GRID SP ACROSS], the option codes) are not text.
  The consent screen before it (UCSF's research consent form) is survey mechanics and
  is dropped.
* OUTCOMES. Eight.
  - Task 0: the scenario screen's question, which differs by arm and is declared per
    arm (`outcome_question`): "Would you want treatment with this medicine for your
    condition?" (1a), "... with CPR for your condition?" (2a), and the "Even though
    ..." sentences above (1b, 2b). Answers 1-4: Definitely yes, Probably yes, Probably
    no, Definitely no (Q, and the .sav's labels). -1 "Refused" is the only non-answer
    (recipe_prep: non_answer, 1.00): 9 / 8 / 7 / 8 people, dropped.
  - Tasks 1-7: Q2-Q8, the grid on screen 3, asked of everyone straight after the
    scenario screen: seven statements about consent, involvement and treatment
    (relying on the doctor, being offered choices, leaving decisions to the doctor,
    fear of dependency, wanting a long life, confidence in care, distrust of
    statistics). They are attitudes asked after the randomised scenario, so they can
    move with it: built as post-treatment outcomes, the same call as vemrp's Q8
    (ruled by the coordinator, 9 Nov 2026). Each question is the grid's stem then
    the statement, joined with a space, word-for-word from Q (asserted the same in
    QT), the "Q2." labels removed. Answers 1-6, "Strongly agree" .. "Strongly
    disagree", the screen's own end labels (the .sav's read "Strongly agree <BR/>1"
    etc., GfK's markup; the codes are asserted to be those labels). -1 "Refused" is
    dropped. No order variable exists and the grid shows all seven at once, so no row
    says where its statement sat.
  - THE CONDITION AT TASKS 1-7 states only what that person had seen and been asked
    by then: the arm's scenario screen, the chart, and then the scenario question,
    narrated as asked, never as answered (32 people refused it and are still built
    here, docs/CONVENTIONS.md, Repeated measures within one block). Declared per arm
    as an item `condition_text`: the arm's text, then the words of ours 'You were
    asked:' and that arm's question in double quotes, word-for-word. "You were
    asked:" is the only addition, and it is true for every row it appears in.
* NOT BUILT. Q9-Q12 (general physical health, ever diagnosed with a heart attack,
  with a stroke, having an advance directive), asked of everyone after the grid:
  health status and history are facts about the respondent, not reactions to the
  scenario, so they are not outcomes of this manipulation (the proposal: "personal
  and health factors"; ruled by the coordinator, 9 Nov 2026). Asked after the
  stimulus, they are not admissible as persona either. SocSci210 built them (its
  tasks 8-11). Cost: 8,503 rows (SocSci210's count for those tasks).
* WHO. 2,154 respondents; 2,135 answered at least one built question and are built
  (2,122 answered the scenario question). Each item's refusal drops only that row.
  `CaseID` is the participant id (unique).
* PERSONA. The standard GfK KnowledgePanel profile, as a42yg (same variable names):
  PPAGE, PPGENDER, PPEDUCAT, PPETHM, PPINCIMP, PPMARIT, PPWORK, PPREG4, PPHHSIZE,
  PPHOUSE, PPRENT, PPMSACAT, PPNET, and the study's merged party, ideology and
  religion items PARTY7, IDEO, REL1, REL2 (Q: DOV_ = the preload, else the backfill
  question). Left absent: IDEO / REL1 / REL2 -1 "Refused" (PARTY7 has no non-answer
  code). recipe_prep offered PPEDUC (14 levels, confidence 0.99) for education;
  overruled for PPEDUCAT, which every other GfK TESS recipe maps and the crosswalk
  covers. It offered PPREG4 for region (0.61, runner-up ppreg9); PPREG4 accepted, as
  every other TESS build. Not mapped: PPEDUC, ppreg9, PPSTATEN, ppagecat / ppagect4,
  PPHHHEAD, the household age counts PPT*, the weight and timings. No persona field
  is in the outcome's domain (medical treatment), and the condition names no persona
  category.
* UK FIT. A stroke and a cardiac arrest, an ambulance, paramedics, a hospital, t-PA
  and CPR: nothing in the condition or question is American law, place or
  institution. US spelling ("paralyzed") is kept word-for-word. The sample is American
  and aged 50 or over.
* ANSWER KEY. SocSci210 holds this study: 25,482 rows, 2,142 people, 12 tasks. Its
  tasks 0-7 are ours, numbered the same: 16,979 rows, 2,135 people, and every
  (condition, task, response) cell equal to ours, value for value
  (tests/test_gen_3xy9j.py). Its other 8,503 rows are Q9-Q12, not built above, so
  `comparable_to_socsci210` is false (the whole-study crosscheck compares row totals
  and would fail on scope alone) and the cell-for-cell comparison is the test.
  SocSci210's text differs from what was fielded. Its conditions are worded from the
  PROPOSAL: the cardiac-arrest text gives CPR as saving "5 people" at normal
  function, 1 with some brain damage and 1 in a coma or too damaged to live
  independently, where the fielded screen and chart say 12, 3, 1 and 1; and it drops
  "on their own" from the stroke paragraph. At tasks 1-7 it gives the statement
  without the grid's stem, does not say the scenario question was asked, and its
  answer instruction reads "1 means Strongly disagree and 6 means Strongly agree",
  the reverse of the screen (1 = strongly agree) and of the .sav, while its stored
  responses are the raw codes, equal to ours: its prompts invert the meaning of
  every answer on those seven tasks. Our text is Q's.
* JEV. scripts/recipe_prep.py 3xy9j --source tess (9 Nov 2026): assignment XTESS133
  (1.00); persona as above; 301 value labels asked, the one disagreement with the
  regex is PPSTATEN's "ID" (Idaho, an answer; not mapped). Its questionnaire scan
  found no instrument because it does not read .docx; the directives were read here
  instead, and Q's only routing on the built screens is [IF XTESS133=k].

    uv run python scripts/gen_3xy9j.py --prep       # extract the two charts from Q
    uv run python scripts/gen_3xy9j.py --catalogue  # (re)write this study's images.json entries
    uv run python scripts/gen_3xy9j.py              # write the recipe
    uv run python scripts/gen_3xy9j.py --check      # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import zipfile
import zlib
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

STUDY = "3xy9j"
RAW = REPO / "data" / "raw" / STUDY
DELIVERABLES = RAW / "TESS133 - Chiong - Final Deliverables"
DATA_FILE = "TESS3133_Chiong_Client_Final Data.sav"
DOCX = DELIVERABLES / "TESS3 133 Chiong Survey_Final.docx"
TXT = DELIVERABLES / "TESS3 133 Chiong Survey_Final.txt"
IMAGES = RAW / "images"
RECIPE = REPO / "recipes" / "images" / f"{STUDY}.yaml"
LICENCE = (
    "None stated: the TESS deposit on OSF (3xy9j, Chiong300.zip) gives no reuse terms "
    "(OSF node_license null, checked 9 Nov 2026), and TESS has since suspended "
    "operations. Used with rich's ruling of 9 Nov 2026 that an unstated licence does "
    "not block a build."
)

ID_VAR = "CaseID"
COND_VAR = "XTESS133"
MARKER = "<image>"

# XTESS133 code -> (Q's label, scenario, question type, answer variable)
GROUPS: dict[int, tuple[str, str, str, str]] = {
    1: ("Q1a", "stroke", "hypothetical_choice", "Q1A"),
    2: ("Q1b", "stroke", "without_consent", "Q1B"),
    3: ("Q1c", "cardiac_arrest", "hypothetical_choice", "Q1C"),
    4: ("Q1d", "cardiac_arrest", "without_consent", "Q1D"),
}
XTESS133_LABELS = {1: "Group 1a", 2: "Group 1b", 3: "Group 2a", 4: "Group 2b"}
OPTIONS = ["Definitely yes", "Probably yes", "Probably no", "Definitely no"]
# Screen 3's statements, built as outcomes (tasks 1-7), and the words of ours that
# narrate the scenario question before them.
ATTITUDE_VARS = [f"Q{i}" for i in range(2, 9)]
ASKED = "You were asked:"

# scenario -> the docx member its screens show. Asserted against document.xml.
CHART_MEMBER = {"stroke": "word/media/image2.png", "cardiac_arrest": "word/media/image3.png"}
CHART_KEY = {"stroke": "stroke", "cardiac_arrest": "cpr"}

# The legend of each chart, top to bottom: (printed label, reference swatch RGB).
# The swatch colours are measured from the figures (each is the body colour of that
# legend entry's figures); a figure is assigned to the nearest.
LEGEND: dict[str, tuple[str, list[tuple[str, tuple[int, int, int]]]]] = {
    "stroke": (
        "Change in Final Outcome as a Result of Treatment",
        [
            ("Normal or Near Normal", (81, 157, 65)),
            ("Better", (158, 195, 133)),
            ("No Change", (220, 220, 220)),
            ("Worse", (216, 94, 118)),
            ("Severely Disabled or Dead", (93, 31, 32)),
        ],
    ),
    "cpr": (
        "Outcome after Treatment",
        [
            ("Normal or Near Normal", (81, 157, 65)),
            ("Disabled but Living Independently", (158, 195, 133)),
            ("Severely Disabled", (219, 146, 161)),
            ("Coma", (106, 53, 54)),
            ("Dead", (220, 220, 220)),
        ],
    ),
}

# The numbers the paragraph under each chart states, as the sentence that states
# them, word-for-word from Q. The count of each legend category must equal them.
TEXT_COUNTS: dict[str, dict[str, tuple[int, str]]] = {
    "stroke": {
        "Normal or Near Normal": (
            13,
            "The medicine would make 13 people normal or near normal again.",
        ),
        "Better": (
            20,
            "It would make another 20 people better but not all the way back to normal.",
        ),
        "Severely Disabled or Dead": (
            1,
            "1 person would either be killed or made severely disabled by the medicine,",
        ),
        "Worse": (2, "and another 2 people would be made worse by the medicine."),
    },
    "cpr": {
        "Normal or Near Normal": (
            12,
            "CPR would allow 12 people to survive at a normal or near normal level of function.",
        ),
        "Disabled but Living Independently": (
            3,
            "It would allow another 3 people to survive with some brain damage, but still "
            "able to live independently.",
        ),
        "Severely Disabled": (
            1,
            "1 person would survive with too much brain damage to live independently,",
        ),
        "Coma": (1, "and another 1 person would survive in a coma."),
    },
}
# What the text leaves to "most of them": the rest of the 100.
REMAINDER = {"stroke": ("No Change", 64), "cpr": ("Dead", 83)}

# Visible facts only. Counts and positions are measured (icon_counts / icon_grid);
# rows are counted from the top, figures from the left.
DESCRIPTIONS: dict[str, str] = {
    "stroke": (
        "An icon chart: 100 identical head-and-shoulders figures in a grid of 10 rows of "
        '10, each coloured by outcome, with a legend on the right headed "Change in Final '
        'Outcome as a Result of Treatment". 13 figures are dark green ("Normal or Near '
        'Normal"): the whole top row and the 4th to 6th of the second row. 20 are light '
        'green ("Better"): the rest of the second row, the whole third row and the 4th to '
        '6th of the fourth row. 64 are white ("No Change"). In the bottom row the 4th and '
        '6th figures are pink ("Worse", 2) and the 5th, between them, dark red ("Severely '
        'Disabled or Dead", 1). No other words or numbers.'
    ),
    "cpr": (
        "An icon chart: 100 identical head-and-shoulders figures in a grid of 10 rows of "
        '10, each coloured by outcome, with a legend on the right headed "Outcome after '
        'Treatment". 12 figures are dark green ("Normal or Near Normal"): the whole top '
        "row and the first two of the second row. In the second row, the 3rd to 5th are "
        'light green ("Disabled but Living Independently", 3), the 6th pink ("Severely '
        'Disabled", 1) and the 7th dark red ("Coma", 1). The other 83 figures, the rest '
        'of the second row and all of the eight rows below it, are white ("Dead"). No '
        "other words or numbers."
    ),
}


def image_id(key: str) -> str:
    return f"{STUDY}_{key}"


def image_file(key: str) -> str:
    """Path under data/, as the catalogue records it."""
    return f"raw/{STUDY}/images/{key}.png"


def text_in_image(key: str) -> str:
    title, entries = LEGEND[key]
    return "\n".join([title, *(label for label, _ in entries)])


# ---------------------------------------------------------------------------
# The questionnaire
# ---------------------------------------------------------------------------


def _clean(text: str) -> str:
    """Typography only (docs/CONVENTIONS.md): curly quotes, dashes, whitespace."""
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("—", "-").replace("–", "-").replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def docx_paragraphs() -> list[str]:
    """Q's body paragraphs in order; a paragraph that embeds a picture reads
    `<image:word/media/...>` for each picture, in place."""
    with zipfile.ZipFile(DOCX) as z:
        xml = z.read("word/document.xml").decode("utf-8")
        rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
    target = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="(media/[^"]+)"', rels))
    out = []
    for para in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
        pieces = re.findall(r'<w:t[^>]*>([^<]*)</w:t>|r:embed="(rId\d+)"', para)
        text = "".join(t if t else f"<image:word/{target[r]}>" for t, r in pieces)
        if text.strip():
            out.append(text)
    return out


def txt_paragraphs() -> list[str]:
    return [x for x in TXT.read_text(encoding="utf-8").splitlines() if x.strip()]


def screens(paras: list[str]) -> dict[int, list[str]]:
    """XTESS133 code -> the paragraphs of its scenario screen, after its [IF] line, up
    to the next [SCREEN] header. Mechanics ([GRID ...]) and options are left in."""
    out: dict[int, list[str]] = {}
    current: int | None = None
    for p in paras:
        s = p.strip()
        m = re.fullmatch(r"\[IF XTESS133=(\d)\]", s)
        if m:
            current = int(m.group(1))
            out[current] = []
            continue
        if s.startswith("[SCREEN"):
            current = None
            continue
        if current is not None:
            out[current].append(p)
    return out


def parse_screen(code: int, paras: list[str]) -> dict[str, Any]:
    """One scenario screen: its opening paragraph, scenario, chart, chart paragraph,
    last paragraph and options."""
    label = GROUPS[code][0]
    body = [p for p in paras if not re.fullmatch(r"\s*\[GRID SP ACROSS\]\s*", p)]
    # options: the four labels then their codes 1-4, at the end
    tail = [_clean(p) for p in body[-8:]]
    if tail != [*OPTIONS, "1", "2", "3", "4"]:
        raise SystemExit(f"{label}: options changed: {tail}")
    body = body[:-8]
    opening = _clean(body[0])
    if not opening.startswith(f"{label}. "):
        raise SystemExit(f"{label}: screen does not open with its label")
    images = [i for i, p in enumerate(body) if "<image:" in p]
    charts = [m for p in body for m in re.findall(r"<image:([^>]+)>", p)]
    if len(images) > 1 or len(charts) > 1:
        raise SystemExit(f"{label}: more than one picture")
    if images:
        i = images[0]
        if _clean(re.sub(r"<image:[^>]+>", "", body[i])):
            raise SystemExit(f"{label}: the picture's paragraph has words in it")
        scenario = [_clean(p) for p in body[1:i]]
        after = [_clean(p) for p in body[i + 1 :]]
    else:  # the plain-text copy: the chart is simply absent
        scenario = [_clean(p) for p in body[1:3]]
        after = [_clean(p) for p in body[3:]]
    if len(scenario) != 2 or len(after) != 2:
        raise SystemExit(f"{label}: expected 2 scenario and 2 closing paragraphs")
    return {
        "opening": opening.removeprefix(f"{label}. "),
        "scenario": scenario,
        "chart": charts[0] if charts else None,
        "graphic": after[0],
        "last": after[1],
    }


def instrument(paras: list[str]) -> dict[int, dict[str, Any]]:
    found = screens(paras)
    if sorted(found) != sorted(GROUPS):
        raise SystemExit(f"scenario screens found for {sorted(found)}")
    return {code: parse_screen(code, found[code]) for code in GROUPS}


def fielded() -> dict[int, dict[str, Any]]:
    """Q, after asserting QT holds the same words (QT has no pictures)."""
    q = instrument(docx_paragraphs())
    qt = instrument(txt_paragraphs())
    for code in GROUPS:
        a = {k: v for k, v in q[code].items() if k != "chart"}
        b = {k: v for k, v in qt[code].items() if k != "chart"}
        if a != b:
            raise SystemExit(f"{GROUPS[code][0]}: .docx and .txt disagree")
    openings = {s["opening"] for s in q.values()}
    if len(openings) != 1:
        raise SystemExit("the opening paragraph differs between screens")
    for code, (label, scenario, _, _) in GROUPS.items():
        if q[code]["chart"] != CHART_MEMBER[scenario]:
            raise SystemExit(f"{label} shows {q[code]['chart']}, not {CHART_MEMBER[scenario]}")
    # within a scenario, everything above the last paragraph is identical
    for g1, g2 in ((1, 2), (3, 4)):
        for k in ("scenario", "graphic"):
            if q[g1][k] != q[g2][k]:
                raise SystemExit(f"groups {g1} and {g2} differ in {k}")
    return q


def body_pictures() -> list[str]:
    """Every picture in Q's body, in order."""
    return [m for p in docx_paragraphs() for m in re.findall(r"<image:([^>]+)>", p)]


def split_last(last: str) -> tuple[str | None, str]:
    """The screen's last paragraph -> (situation sentence or None, question)."""
    if last.endswith("for your condition?") and last.startswith("Would you want"):
        return None, last
    m = re.fullmatch(
        r"(Imagine that .*? whether you would want this treatment\.) (Even though .*\?)", last
    )
    if not m:
        raise SystemExit(f"unexpected last paragraph: {last}")
    return m.group(1), m.group(2)


# ---------------------------------------------------------------------------
# Pictures
# ---------------------------------------------------------------------------


def png_rgba(data: bytes) -> tuple[int, int, list[bytes]]:
    """Decode an 8-bit RGBA, non-interlaced PNG (all these charts are) into rows."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("not a PNG")
    i, idat = 8, b""
    w = h = 0
    while i < len(data):
        (n,) = struct.unpack(">I", data[i : i + 4])
        kind, chunk = data[i + 4 : i + 8], data[i + 8 : i + 8 + n]
        i += 12 + n
        if kind == b"IHDR":
            w, h, depth, colour, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
            if (depth, colour, interlace) != (8, 6, 0):
                raise SystemExit("expected an 8-bit RGBA non-interlaced PNG")
        elif kind == b"IDAT":
            idat += chunk
    raw = zlib.decompress(idat)
    stride, out, prev, p = w * 4, [], bytearray(w * 4), 0
    for _ in range(h):
        f, line = raw[p], bytearray(raw[p + 1 : p + 1 + stride])
        p += 1 + stride
        for x in range(stride):
            a = line[x - 4] if x >= 4 else 0
            up = prev[x]
            c = prev[x - 4] if x >= 4 else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + up) & 255
            elif f == 3:
                line[x] = (line[x] + (a + up) // 2) & 255
            elif f == 4:
                pa, pb, pc = abs(up - c), abs(a - c), abs(a + up - 2 * c)
                pr = a if pa <= pb and pa <= pc else (up if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        out.append(bytes(line))
        prev = line
    return w, h, out


def icon_grid(key: str, data: bytes | None = None) -> list[list[str]]:
    """The chart's 10 x 10 figures, each as the legend label of its body colour.

    Columns are found from the image (the first ten runs of inked columns); rows are
    the grid's height in ten equal bands. A figure's body is sampled in the lower part
    of its band and the middle of its column, and assigned to the nearest swatch."""
    if data is None:
        data = (REPO / "data" / image_file(key)).read_bytes()
    w, h, rows = png_rgba(data)

    def px(x: int, y: int) -> bytes:
        return rows[y][4 * x : 4 * x + 4]

    def inked(x: int, y: int) -> bool:
        p = px(x, y)
        return p[3] > 0 and min(p[:3]) < 235

    col_on = [sum(inked(x, y) for y in range(h)) > 40 for x in range(w)]
    cols: list[tuple[int, int]] = []
    start: int | None = None
    for x, on in enumerate([*col_on, False]):
        if on and start is None:
            start = x
        if not on and start is not None:
            cols.append((start, x))
            start = None
    cols = cols[:10]
    if len(cols) != 10 or any(not 28 <= b - a <= 38 for a, b in cols):
        raise SystemExit(f"{key}: grid columns not found: {cols}")
    x_end = cols[-1][1]
    ys = [y for y in range(h) if any(inked(x, y) for x in range(x_end))]
    top, bottom = ys[0], ys[-1] + 1
    pitch = (bottom - top) / 10
    swatches = LEGEND[key][1]
    grid: list[list[str]] = []
    for r in range(10):
        y0 = top + r * pitch
        band = range(int(y0 + 0.6 * pitch), int(y0 + 0.85 * pitch))
        line = []
        for a, b in cols:
            xs = range(a + (b - a) // 4, b - (b - a) // 4)
            ps = [px(x, y) for y in band for x in xs if px(x, y)[3] > 200]
            mean = [sum(p[i] for p in ps) / len(ps) for i in range(3)]
            label = min(
                swatches,
                key=lambda s: sum((mean[i] - s[1][i]) ** 2 for i in range(3)),
            )[0]
            line.append(label)
        grid.append(line)
    return grid


def icon_counts(key: str, data: bytes | None = None) -> dict[str, int]:
    counts = {label: 0 for label, _ in LEGEND[key][1]}
    for line in icon_grid(key, data):
        for label in line:
            counts[label] += 1
    return counts


def extract() -> None:
    """--prep: copy each chart out of Q, byte for byte."""
    IMAGES.mkdir(exist_ok=True)
    with zipfile.ZipFile(DOCX) as z:
        for scenario, member in CHART_MEMBER.items():
            (IMAGES / f"{CHART_KEY[scenario]}.png").write_bytes(z.read(member))


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------


def catalogue_entries() -> dict[str, dict[str, str]]:
    """This study's entries in data/catalog/images.json, after checking each file is
    Q's picture byte for byte and its figures match the numbers Q prints under it."""
    from micromotives_datasets.images import sha256_of

    q = fielded()
    out: dict[str, dict[str, str]] = {}
    with zipfile.ZipFile(DOCX) as z:
        for scenario, member in CHART_MEMBER.items():
            key = CHART_KEY[scenario]
            f = image_file(key)
            data = (REPO / "data" / f).read_bytes()
            if data != z.read(member):
                raise SystemExit(f"{f} is not {member} of the questionnaire")
            counts = icon_counts(key, data)
            graphic = next(s["graphic"] for c, s in q.items() if GROUPS[c][1] == scenario)
            for label, (n, sentence) in TEXT_COUNTS[key].items():
                if counts[label] != n or sentence not in graphic:
                    raise SystemExit(f"{key}: {label} is {counts[label]}, text says {n}")
            rest, n = REMAINDER[key]
            if counts[rest] != n:
                raise SystemExit(f"{key}: {rest} is {counts[rest]}, expected {n}")
            codes = [c for c, g in GROUPS.items() if g[1] == scenario]
            out[image_id(key)] = {
                "file": f,
                "sha256": sha256_of(REPO / "data" / f),
                "source": (
                    "OSF 3xy9j, TESS deposit Chiong300.zip: embedded in the fielded "
                    'questionnaire "TESS3 133 Chiong Survey_Final.docx" as '
                    f"{member}, copied byte for byte. The questionnaire shows it on the "
                    f"scenario screens for XTESS133 = {codes[0]} and {codes[1]} "
                    f"({GROUPS[codes[0]][0]}, {GROUPS[codes[1]][0]}), between the scenario "
                    'and the paragraph beginning "This graphic shows". The size GfK '
                    "displayed it at is not recorded."
                ),
                "licence": LICENCE,
                "text_in_image": text_in_image(key),
                "description": DESCRIPTIONS[key],
            }
    return out


def write_catalogue() -> None:
    """Add or refresh only this study's entries; re-read first, others are editing too."""
    path = REPO / "data" / "catalog" / "images.json"
    entries = catalogue_entries()
    current = json.loads(path.read_text())
    current.update(entries)
    path.write_text(json.dumps(current, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Recipe
# ---------------------------------------------------------------------------


def attitude_grid(paras: list[str]) -> dict[str, Any]:
    """Screen 3, the grid asked of everyone after the scenario screen: its stem, its
    scale's two end labels, and its statements Q2-Q8 in the order listed."""
    start = next(i for i, p in enumerate(paras) if p.strip().startswith("[SCREEN 3"))
    end = next(i for i, p in enumerate(paras) if i > start and p.strip() == "[Display]")
    body = [_clean(p) for p in paras[start + 1 : end]]
    if body[0].lower() != "[grid; sp across]":
        raise SystemExit(f"screen 3 opens with {body[0]!r}")
    scale = body[2:11]
    if scale != ["Strongly agree", "1", "2", "3", "4", "5", "Strongly", "disagree", "6"]:
        raise SystemExit(f"screen 3's scale changed: {scale}")
    items = []
    for p in body[11:]:
        m = re.fullmatch(r"(Q[2-8])\. (.+)", p)
        if not m:
            raise SystemExit(f"unexpected line in screen 3: {p!r}")
        items.append((m.group(1), m.group(2)))
    if [v for v, _ in items] != ATTITUDE_VARS:
        raise SystemExit(f"screen 3 lists {[v for v, _ in items]}")
    return {
        "stem": body[1],
        "min_label": "Strongly agree",
        "max_label": "Strongly disagree",
        "items": items,
    }


def fielded_grid() -> dict[str, Any]:
    q, qt = attitude_grid(docx_paragraphs()), attitude_grid(txt_paragraphs())
    if q != qt:
        raise SystemExit("screen 3: .docx and .txt disagree")
    return q


def arm_text(screen: dict[str, Any]) -> str:
    situation, _ = split_last(screen["last"])
    parts = [*screen["scenario"], MARKER, screen["graphic"]]
    if situation:
        parts.append(situation)
    return " ".join(parts)


def after_scenario_text(screen: dict[str, Any]) -> str:
    """The condition for an item on screen 3: the arm's scenario screen, then the
    question it asked, narrated as asked (never as answered: 32 people refused it)."""
    _, question = split_last(screen["last"])
    return f'{arm_text(screen)} {ASKED} "{question}"'


def recipe() -> dict[str, Any]:
    q = fielded()
    ds = read_any(DELIVERABLES / DATA_FILE)
    labels = ds.value_labels

    if {int(k): v for k, v in labels[COND_VAR].items()} != XTESS133_LABELS:
        raise SystemExit(f"{COND_VAR} labels changed: {labels[COND_VAR]}")
    if sorted(int(c) for c in ds.df[COND_VAR].dropna().unique()) != list(GROUPS):
        raise SystemExit(f"{COND_VAR} codes changed")
    if ds.df[COND_VAR].isna().any():
        raise SystemExit(f"someone has no {COND_VAR}")
    if not ds.df[ID_VAR].is_unique:
        raise SystemExit(f"{ID_VAR} is not unique")
    for code, (_label, _, _, var) in GROUPS.items():
        if {int(k): v for k, v in labels[var].items()} != {-1: "Refused"} | dict(
            enumerate(OPTIONS, start=1)
        ):
            raise SystemExit(f"{var}: value labels differ from the questionnaire")
        others = ds.df[ds.df[COND_VAR] != code][var]
        if others.notna().any():
            raise SystemExit(f"{var} is answered outside group {code}")
    grid = fielded_grid()
    # The .sav's labels are the screen's, with GfK's markup: "Strongly agree <BR/>1".
    expected = {-1: "Refused", 1: "Strongly agree <BR/>1", 6: "Strongly disagree <BR/>6"}
    expected |= {i: str(i) for i in range(2, 6)}
    for var in ATTITUDE_VARS:
        if {int(k): v for k, v in labels[var].items()} != expected:
            raise SystemExit(f"{var}: value labels differ from screen 3")

    arms: list[dict[str, Any]] = []
    for code, (_, scenario, qtype, var) in GROUPS.items():
        screen = q[code]
        _, question = split_last(screen["last"])
        later = after_scenario_text(screen)
        arms.append(
            {
                "raw": code,
                "condition_num": code - 1,
                "factors": {"scenario": scenario, "question_type": qtype},
                "text": arm_text(screen),
                "images": [image_id(CHART_KEY[scenario])],
                "outcome_var": var,
                "outcome_question": question,
                "items": {t: {"condition_text": later} for t in range(1, 8)},
            }
        )
    attitudes = [
        {
            "var": var,
            "task_num": t,
            "question": f"{grid['stem']} {statement}",
            "scale": {
                "min": 1,
                "max": 6,
                "min_label": grid["min_label"],
                "max_label": grid["max_label"],
            },
            "response_recode": {i: i for i in range(1, 7)},
        }
        for t, (var, statement) in enumerate(grid["items"], start=1)
    ]

    return {
        "study_id": STUDY,
        "source": "tess",
        "title": "An experiment on the presumption of consent to emergency medical treatment: "
        "a stroke treated with t-PA or a cardiac arrest treated with CPR, its outcomes for 100 "
        "people shown as an icon chart, asked as a choice or as treatment without consent",
        "data_file": DATA_FILE,
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": ID_VAR,
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_var": COND_VAR,
            "shared_context": q[1]["opening"],
            "factors": ["scenario", "question_type"],
            "arms": arms,
        },
        "outcomes": [
            {
                "task_num": 0,
                "question": "Would you want treatment with this medicine for your condition?",
                "scale": {
                    "min": 1,
                    "max": 4,
                    "min_label": OPTIONS[0],
                    "max_label": OPTIONS[-1],
                },
            },
            *attitudes,
        ],
        "response_recode": {i: i for i in range(1, 5)},
        "missing_codes": [-1],
        "persona_map": {
            "age": "PPAGE",
            "gender": "PPGENDER",
            "education": "PPEDUCAT",
            "ethnicity": "PPETHM",
            "income": "PPINCIMP",
            "marital_status": "PPMARIT",
            "employment": "PPWORK",
            "region": "PPREG4",
            "household_size": "PPHHSIZE",
            "housing_type": "PPHOUSE",
            "housing_ownership": "PPRENT",
            "urban_rural": "PPMSACAT",
            "internet_access": "PPNET",
            "party_id": "PARTY7",
            "ideology": "IDEO",
            "religion": "REL1",
            "religious_attendance": "REL2",
        },
        "persona_missing": {"IDEO": [-1], "REL1": [-1], "REL2": [-1]},
    }


def render() -> str:
    return yaml.safe_dump(recipe(), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--prep", action="store_true", help="extract the charts from the .docx")
    ap.add_argument("--catalogue", action="store_true", help="add this study's images.json entries")
    args = ap.parse_args()
    if args.prep:
        extract()
        print(f"wrote {IMAGES.relative_to(REPO)}/{{stroke,cpr}}.png")
        return 0
    if args.catalogue:
        write_catalogue()
        print("updated data/catalog/images.json (3xy9j entries only)")
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
