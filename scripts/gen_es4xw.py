#!/usr/bin/env python3
"""Write recipes/images/es4xw.yaml: one of four photographs of a six-person management team.

Bauman, TESS2 040 (University of Chicago), "Perceptions of Diversity Across Groups".
OSF es4xw. Fielded June 2010 by Knowledge Networks (KnowledgePanel), N = 2,512, sampled
to equal African American / Asian / Hispanic / White quotas (the questionnaire's
"Sample Criteria"; the .sav keeps no screener). Files used: the data
(TESS2_040_Bauman_Client.sav), the fielded questionnaire as Word
(Tess2_040_Bauman_final.docx, "Q" below) and as text (Tess2_040_Bauman_final.txt, the
same words without the pictures). The proposal (Bauman024.pdf) was read only to see
whether it describes the fielded design; it does not (below), and no word of it is used.

This replaces the text build (recipes/es4xw.yaml). rich ruled on 9 Nov 2026 that the
text build was wrong in kind: respondents saw a photograph of the team and the text rows
stated its racial make-up in words, a sentence nobody read. Here the row carries the
photograph and the words that were actually on screen. Every row and response is the
text build's; only the condition text differs (tests/test_gen_es4xw.py).

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* DESIGN. One randomised variable with four levels. Q's sample-variable block reads
  "XTESS042 1=Picture1 2=Picture2 3=Picture3 4=Picture4"; the .sav's column is XTESS040
  ("Picture Selected", 1-4 "Picture 1" .. "Picture 4"; 636 / 644 / 625 / 607 = 2,512).
  Treated as one variable under a typo in Q: the labels match in words and order, it is
  the file's only four-level column whose counts sum to N, and recipe_prep.py (Jev)
  named XTESS040 the assignment at confidence 0.96 from its labels alone.
  condition_num is XTESS040 - 1.
* WHICH PICTURE IS WHICH ARM. Q shows "[SHOW BELOW PICTURE IF XTESS042=n]" four times,
  each followed directly by one embedded picture: word/media/image1.png .. image4.png,
  in that order (parsed from Q's XML in --prep and --check, not assumed from the file
  names). They are copied byte for byte to data/raw/es4xw/images/picture1..4.png.
  Each is a 446 x 405 PNG: six head-and-shoulders photographs in two rows of three,
  separated by white gutters.
* WHAT VARIES. Compared panel by panel here (mean absolute RGB difference; under 5 is
  the same photograph, over 30 a different one): the top-left, top-right,
  bottom-middle and bottom-right photographs are the same in all four pictures; the
  top-middle and bottom-left change. Picture 3 reuses picture 2's top-middle and
  picture 1's bottom-left; picture 4's two are in no other picture. So the four
  pictures differ in exactly two of six faces.
* THE ARMS' COMPOSITIONS ARE DESIGN FACTS, NOT CONDITION TEXT. TESS's study record
  (tessexperiments.org/study/bauman024, re-read 9 Nov 2026) gives the manipulation as
  "Racial composition of 6-person groups via pictures" with "Four conditions: 6 White,
  4 White + 2 African American, 4 White + 2 Asian, 4 White + 1 African American +
  1 Asian". It does not say which picture number is which. The text build fixed that
  from the data, and --check re-derives it from aggregates computed locally: on the mean
  of Q1, Q2 and (8 - Q3) by PPETHM, XTESS040 = 3 is the highest-rated picture for every
  respondent group (the paper's headline: Bauman, Trawalter & Unzueta 2014, PSPB 40,
  1354-1372, the mixed team is seen as most diverse by all), XTESS040 = 4 the lowest
  (the all-White team), and Black respondents rate picture 1 well above picture 2
  (4.51 vs 3.38) while White respondents barely separate them (4.85 vs 4.70), which
  places the two Black team members in picture 1 and the two Asian team members in
  picture 2. Picture 3 then combines one of each, as the panel comparison shows. These
  facts are kept only as the arms' factors, `black_member_present` x
  `asian_member_present` (present / absent), unchanged from the text build so that the
  rows compare exactly. They never appear in a row's condition, and our image
  descriptions do not state anyone's apparent race, ethnicity, gender or age.
* CONDITION. Q says to show the picture with a caption beneath it, "[SHOW BELOW TEXT
  FOR ALL RESPONDENTS UNDER IMAGE]", on the same page as the first three grids. Each
  arm is the picture marker followed by that caption, word-for-word from Q (curly
  apostrophe straightened): "<image> A large company recently formed a management team
  to lead a new project. You don't know any of them personally, but the company included
  pictures of the management team when it sent out an announcement about the project
  (see above)." The text build dropped "(see above)" because nothing preceded it; here
  the picture does, so the words are kept as fielded. No connecting words of ours.
  The four arms have the same words and differ only in their picture, which QC rules 1
  and 5 compare (docs/CONVENTIONS.md, Image conditions). There is no shared_context:
  the caption is the only shared text and it follows the picture.
* IMAGE IDS are es4xw_picture1 .. es4xw_picture4, Q's own neutral names for the four
  levels ("Picture1" .. "Picture4"). They say nothing about who is pictured. As in every
  image build here the ID is resolved to its file by the export and never written into
  a prompt, but a neutral name means a slip in that would leak nothing either.
* OUTCOMES. Q1-Q13, four grids each on a 1-7 scale, Strongly Disagree .. Strongly
  Agree with "Neither" in the middle (Q's grid header; the same as each item's .sav
  labels). Q1-Q3 perceived ethnic diversity of the team (Q3 reverse-worded), Q4-Q6
  expected fairness, Q7-Q9 wanting to join the team, Q10-Q13 colour-blind attitudes.
  Each statement is word-for-word from Q, read out of the text file and checked. The
  lead "Please rate the following statement:" is NOT on Q's screen (the grid shows
  only its agree / disagree header); it is the text build's, kept unchanged so that
  every outcome string compares exactly, and flagged here rather than silently
  inherited. All 13 are asked of everyone, with no branching. The first three grids
  are marked "[GRID - SP - PLACE IMAGE ABOVE QUESTIONS]"; the fourth (Q10-Q13) only
  "[GRID - SP]", so the picture was not on that page, but every respondent had just
  seen it on the three before. Those rows carry the same condition, as in the text
  build. -1 "Refused" is the only non-answer code.
* PERSONA. Unchanged from the text build: the KnowledgePanel PP* fields, xparty7,
  xideo and xrel1 (case-insensitive lookups). education is PPEDUCAT and region PPREG4,
  matching the other KnowledgePanel recipes rather than Jev's finer picks (ledger
  #64-66). xrel1 code 12 "Other non-Christian, please specify:" is rewritten to "Other
  non-Christian" (ledger #60). Sentinel codes on xparty7 / xideo / xrel1 / xrel2 are
  declared as in the text build.
* PROPOSAL VS FIELDED. Bauman024.pdf describes composite pictures of EIGHT head shots,
  3 or 5 minority members and four outcome items; the fielded study shows six, two
  minority members, a mixed condition and thirteen items. Nothing from it is used.
* SOCSCI210 holds es4xw (9,891 rows, four conditions, three outcomes), reconstructed
  from the proposal's description of an earlier eight-headshot pilot, not from the
  fielded instrument: its four pure-group conditions are not this study's, so no
  numeric reconciliation is possible (comparable_to_socsci210: false, as the text
  build found).
* CAVEAT. The pictures are photographs of what appear to be real people, in a
  stock-portrait style, with no statement of who they are or of their consent, and
  the deposit states no licence. rich accepted both on 9 Nov 2026. Recorded in each
  catalogue entry.
* NOT ASKED OF JEV. The assignment, persona and codes are the text build's, already
  screened; no paid call.

    uv run python scripts/gen_es4xw.py --prep       # extract the four pictures from Q
    uv run python scripts/gen_es4xw.py --catalogue  # (re)write this study's images.json entries
    uv run python scripts/gen_es4xw.py              # write the recipe
    uv run python scripts/gen_es4xw.py --check      # exit 1 if it differs
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
from typing import Any, cast

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

STUDY = "es4xw"
RAW = REPO / "data" / "raw" / STUDY
DATA_FILE = "TESS2_040_Bauman_Client.sav"
DOCX = RAW / "Tess2_040_Bauman_final.docx"
TXT = RAW / "Tess2_040_Bauman_final.txt"
IMAGES = RAW / "images"
RECIPE = REPO / "recipes" / "images" / f"{STUDY}.yaml"
LICENCE = (
    "None stated: the OSF deposit es4xw has no licence (node_license null, checked "
    "2026-10-01), TESS archived it without reuse terms, and TESS has since suspended "
    "operations. The pictures are photographs of apparently real people with no "
    "statement of who they are or of their consent. Used with rich's ruling of "
    "9 Nov 2026 accepting both."
)

COND_VAR = "XTESS040"
ARMS = [1, 2, 3, 4]
# The design facts (module docstring, "THE ARMS' COMPOSITIONS"): factors only, never text.
FACTORS: dict[int, dict[str, str]] = {
    1: {"black_member_present": "present", "asian_member_present": "absent"},
    2: {"black_member_present": "absent", "asian_member_present": "present"},
    3: {"black_member_present": "present", "asian_member_present": "present"},
    4: {"black_member_present": "absent", "asian_member_present": "absent"},
}
OUTCOME_LEAD = "Please rate the following statement:"  # the text build's words, not Q's
OUTCOME_VARS = [f"Q{i}" for i in range(1, 14)]

# Panel boxes (rows, columns) of the 2 x 3 grid, inside the white gutters; checked.
ROWS = [(0, 200), (205, 405)]
COLS = [(0, 145), (150, 296), (301, 446)]
SLOTS = {
    "top-left": (0, 0),
    "top-middle": (0, 1),
    "top-right": (0, 2),
    "bottom-left": (1, 0),
    "bottom-middle": (1, 1),
    "bottom-right": (1, 2),
}
SAME, DIFFERENT = 5.0, 30.0
# Which photograph fills each varying slot, by picture: same letter, same photograph.
VARYING = {
    "top-middle": {1: "a", 2: "b", 3: "b", 4: "c"},
    "bottom-left": {1: "d", 2: "e", 3: "d", 4: "f"},
}

# Visible facts only: layout, backdrop, clothing. No race, ethnicity, gender, age,
# hair, expression or appraisal: the study measures how people read the team's make-up.
_COMMON = (
    "Six colour head-and-shoulders photographs of six different people, in a grid of two "
    "rows of three separated by thin white lines. Each person faces the camera in front "
    "of the same plain blue-grey studio backdrop, and each wears a dark jacket."
)
_SLOT_TEXT = {
    "top-left": "a white open-collared shirt and a beaded necklace",
    "top-right": "a white shirt and a dark striped tie",
    "bottom-middle": "a white shirt and a dark red patterned tie",
    "bottom-right": "a white open-collared top",
}
_VARYING_TEXT = {
    ("top-middle", "a"): "a white shirt and a dark tie with small white dots",
    ("top-middle", "b"): "a light blue shirt and a grey checked tie",
    ("top-middle", "c"): "a white shirt and a light blue tie",
    ("bottom-left", "d"): "a white shirt and a light blue tie",
    ("bottom-left", "e"): "a light blue shirt and a grey and blue striped tie",
    ("bottom-left", "f"): "a light blue shirt and a tan patterned tie",
}


def description(n: int) -> str:
    parts = []
    for slot in SLOTS:
        what = _VARYING_TEXT[(slot, VARYING[slot][n])] if slot in VARYING else _SLOT_TEXT[slot]
        row, col = slot.split("-")
        parts.append(f"{row.capitalize()} row, {col}: {what}.")
    return f"{_COMMON} {' '.join(parts)} No words."


DESCRIPTIONS = {n: description(n) for n in ARMS}


def image_id(n: int) -> str:
    return f"{STUDY}_picture{n}"


def image_file(n: int) -> str:
    """Path under data/, as the catalogue records it."""
    return f"raw/{STUDY}/images/picture{n}.png"


def _clean(text: str) -> str:
    """Typography only: curly quotes and apostrophes, dashes in directives, whitespace."""
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# The questionnaire
# ---------------------------------------------------------------------------


def _docx_paragraphs() -> list[tuple[str, list[str]]]:
    """(text, embedded media members) for every paragraph of Q, in order."""
    with zipfile.ZipFile(DOCX) as z:
        xml = z.read("word/document.xml").decode("utf-8")
        rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
    target = {
        rid: f"word/{t}" for rid, t in re.findall(r'Id="(rId\d+)"[^>]*Target="(media/[^"]+)"', rels)
    }
    out = []
    for p in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
        text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p))
        media = [target[r] for r in re.findall(r'r:(?:embed|id)="(rId\d+)"', p) if r in target]
        out.append((text, media))
    return out


def docx_pictures() -> dict[int, str]:
    """XTESS042 value -> the media member Q embeds directly under its directive.

    The next paragraph with any text or picture after "[SHOW BELOW PICTURE IF
    XTESS042=n]" must be a single picture, and the four must be distinct."""
    paras = _docx_paragraphs()
    out: dict[int, str] = {}
    for i, (text, _) in enumerate(paras):
        m = re.fullmatch(r"\[SHOW BELOW PICTURE IF XTESS042=(\d)\]", text.strip())
        if not m:
            continue
        nxt = next(p for p in paras[i + 1 :] if p[0].strip() or p[1])
        if nxt[0].strip() or len(nxt[1]) != 1:
            raise SystemExit(f"directive {m.group(0)} is not followed by exactly one picture")
        out[int(m.group(1))] = nxt[1][0]
    if sorted(out) != ARMS or len(set(out.values())) != 4:
        raise SystemExit(f"picture directives changed: {out}")
    return out


def _txt() -> str:
    return TXT.read_text(encoding="utf-8")


def caption() -> str:
    """The text Q shows under the picture to everyone, from the .txt and the .docx alike."""
    lines = _txt().splitlines()
    i = next(
        k for k, x in enumerate(lines) if "[SHOW BELOW TEXT FOR ALL RESPONDENTS UNDER IMAGE]" in x
    )
    from_txt = _clean(lines[i + 1])
    paras = [t for t, _ in _docx_paragraphs()]
    j = next(k for k, t in enumerate(paras) if "[SHOW BELOW TEXT FOR ALL RESPONDENTS" in t)
    from_docx = _clean(paras[j + 1])
    if from_txt != from_docx:
        raise SystemExit(f"caption differs between .txt and .docx: {from_txt!r} / {from_docx!r}")
    if not from_txt.startswith("A large company") or not from_txt.endswith("(see above)."):
        raise SystemExit(f"caption changed: {from_txt!r}")
    return from_txt


def statements() -> dict[str, str]:
    """Q1..Q13 -> the statement, word-for-word."""
    found = {f"Q{n}": _clean(s) for n, s in re.findall(r"^Q(\d+)\. (.+)$", _txt(), flags=re.M)}
    out = {v: found[v] for v in OUTCOME_VARS}
    return out


def grid_directives() -> dict[str, str]:
    """The grid directive above each grid's first item (Q1, Q4, Q7, Q10)."""
    text = _clean(_txt().replace("–", "-"))
    out = {}
    for first in ("Q1", "Q4", "Q7", "Q10"):
        before = text[: text.index(f"{first}. ")]
        out[first] = re.findall(r"\[GRID[^\]]*\]", before)[-1]
    return out


def grid_scale() -> list[str]:
    """The seven column headings of the first grid, left to right, as Q prints them."""
    lines = [x.strip() for x in _txt().splitlines()]
    i = next(k for k, x in enumerate(lines) if x.startswith("[GRID"))
    words = [x for x in lines[i + 1 : lines.index("Q1. " + statements()["Q1"])] if x]
    degree, sides = words[:7], words[7:]
    if (
        degree
        != ["Strongly", "Moderately", "Slightly", "Neither", "Slightly", "Moderately", "Strongly"]
        or sides != ["DISAGREE"] * 3 + ["AGREE"] * 3
    ):
        raise SystemExit(f"grid header changed: {words}")
    return degree


# ---------------------------------------------------------------------------
# Pictures
# ---------------------------------------------------------------------------


def decode_png(data: bytes) -> np.ndarray:
    """An 8-bit palette or RGB PNG, non-interlaced, as an (h, w, 3) uint8 array."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    i, idat, plte = 8, b"", None
    w = h = depth = ctype = interlace = 0
    while i < len(data):
        (n,) = struct.unpack(">I", data[i : i + 4])
        kind, body = data[i + 4 : i + 8], data[i + 8 : i + 8 + n]
        i += 12 + n
        if kind == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
        elif kind == b"PLTE":
            plte = np.frombuffer(body, np.uint8).reshape(-1, 3)
        elif kind == b"IDAT":
            idat += body
    if depth != 8 or interlace or ctype not in (2, 3):
        raise ValueError(f"unsupported PNG: depth {depth}, type {ctype}, interlace {interlace}")
    bpp = 1 if ctype == 3 else 3
    stride = w * bpp
    raw = zlib.decompress(idat)
    out = np.zeros((h, stride), np.uint8)
    prev = np.zeros(stride, np.int64)
    for y in range(h):
        f = raw[y * (stride + 1)]
        start = y * (stride + 1) + 1
        line = np.frombuffer(raw[start : start + stride], np.uint8).astype(np.int64)
        cur = np.zeros(stride, np.int64)
        if f == 0:
            cur = line.copy()
        elif f == 2:
            cur = (line + prev) & 255
        else:
            for x in range(stride):
                a = cur[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                if f == 1:
                    pred = a
                elif f == 3:
                    pred = (a + b) // 2
                elif f == 4:
                    p = a + b - c
                    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                    pred = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                else:
                    raise ValueError(f"bad filter {f}")
                cur[x] = (line[x] + pred) & 255
        out[y] = cur
        prev = cur
    if ctype == 3:
        assert plte is not None
        return plte[out]
    return out.reshape(h, w, 3)


def picture_bytes() -> dict[int, bytes]:
    with zipfile.ZipFile(DOCX) as z:
        return {n: z.read(m) for n, m in docx_pictures().items()}


def _gutters(img: np.ndarray) -> tuple[list[int], list[int]]:
    white = img.astype(float).mean(axis=2) > 245
    cols = [int(x) for x in np.where(white.mean(axis=0) > 0.9)[0]]
    rows = [int(y) for y in np.where(white.mean(axis=1) > 0.9)[0]]
    return rows, cols


def slot_distances(pics: dict[int, bytes] | None = None) -> dict[str, np.ndarray]:
    """slot -> 4 x 4 matrix of mean absolute RGB difference between pictures."""
    pics = pics or picture_bytes()
    imgs = {n: decode_png(b).astype(float) for n, b in pics.items()}
    for n, img in imgs.items():
        rows, cols = _gutters(img)
        # The gutters must lie between the panel boxes (a panel's edge column may be
        # near-white too: picture 2's column 295).
        gutter_cols = {*range(145, 150), *range(296, 301)}
        if (
            img.shape[:2] != (405, 446)
            or rows != list(range(200, 205))
            or not gutter_cols <= set(cols)
            or not set(cols) <= {*range(144, 151), *range(295, 302)}
        ):
            raise SystemExit(f"picture {n}: grid layout changed {img.shape} {rows} {cols}")
    out = {}
    for slot, (r, c) in SLOTS.items():
        (r0, r1), (c0, c1) = ROWS[r], COLS[c]
        m = np.zeros((4, 4))
        for a in ARMS:
            for b in ARMS:
                m[a - 1, b - 1] = np.abs(imgs[a][r0:r1, c0:c1] - imgs[b][r0:r1, c0:c1]).mean()
        out[slot] = m
    return out


def check_slots(dist: dict[str, np.ndarray]) -> None:
    """Every slot is the same photograph across pictures exactly where VARYING says so."""
    for slot, m in dist.items():
        letters = VARYING.get(slot, dict.fromkeys(ARMS, "same"))
        for a in ARMS:
            for b in ARMS:
                if a == b:
                    continue
                same = letters[a] == letters[b]
                if (same and m[a - 1, b - 1] >= SAME) or (
                    not same and m[a - 1, b - 1] <= DIFFERENT
                ):
                    raise SystemExit(
                        f"{slot}: pictures {a} and {b} differ by {m[a - 1, b - 1]:.1f}"
                    )


def extract() -> None:
    """--prep: copy each picture out of Q, byte for byte."""
    IMAGES.mkdir(exist_ok=True)
    for n, data in picture_bytes().items():
        (IMAGES / f"picture{n}.png").write_bytes(data)


# ---------------------------------------------------------------------------
# Which arm is which composition (aggregates, computed locally)
# ---------------------------------------------------------------------------


def diversity_means() -> dict[int, dict[int, float]]:
    """PPETHM -> XTESS040 -> mean of (Q1 + Q2 + 8 - Q3) / 3, answers 1-7 only."""
    df = read_any(RAW / DATA_FILE).df
    cols = {c.lower(): c for c in df.columns}
    q = df[[cols["q1"], cols["q2"], cols["q3"]]].astype(float)
    ok = q.isin(range(1, 8)).all(axis=1)
    idx = (q.iloc[:, 0] + q.iloc[:, 1] + 8 - q.iloc[:, 2]) / 3
    frame = df.loc[ok, [cols["ppethm"], cols[COND_VAR.lower()]]].assign(idx=idx[ok])
    g = frame.groupby([cols["ppethm"], cols[COND_VAR.lower()]])["idx"].mean()
    out: dict[int, dict[int, float]] = {}
    for key, v in g.items():
        eth, arm = cast(tuple[int, int], key)
        out.setdefault(int(eth), {})[int(arm)] = float(v)
    return out


def check_composition(means: dict[int, dict[int, float]]) -> None:
    """The factor labels' evidence: 3 highest and 4 lowest for every group; Black
    respondents (PPETHM 2) separate 1 from 2 far more than White ones (PPETHM 1)."""
    for eth, m in means.items():
        if max(m, key=m.__getitem__) != 3 or min(m, key=m.__getitem__) != 4:
            raise SystemExit(f"PPETHM {eth}: picture ranking {m}")
    black, white = means[2][1] - means[2][2], means[1][1] - means[1][2]
    if not (black > 0.5 and black > 3 * abs(white)):
        raise SystemExit(
            f"in-group gap no longer places Black members in picture 1: {black, white}"
        )


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------


def catalogue_entries() -> dict[str, dict[str, str]]:
    """This study's entries in data/catalog/images.json, after checking each file is
    Q's picture for its directive, byte for byte."""
    from micromotives_datasets.images import sha256_of

    members = docx_pictures()
    pics = picture_bytes()
    out: dict[str, dict[str, str]] = {}
    for n in ARMS:
        f = REPO / "data" / image_file(n)
        if f.read_bytes() != pics[n]:
            raise SystemExit(f"{image_file(n)} is not {members[n]} of the questionnaire")
        out[image_id(n)] = {
            "file": image_file(n),
            "sha256": sha256_of(f),
            "source": (
                "OSF es4xw, TESS2 040 (Bauman) deposit: embedded in the fielded "
                f'questionnaire "Tess2_040_Bauman_final.docx" as {members[n]}, directly '
                f'under "[SHOW BELOW PICTURE IF XTESS042={n}]", copied byte for byte. '
                "Six photographs of apparently real people, with no statement of who "
                "they are or of their consent."
            ),
            "licence": LICENCE,
            "text_in_image": "",
            "description": DESCRIPTIONS[n],
        }
    return out


def write_catalogue() -> None:
    """Add or refresh only this study's entries; re-read first, others are editing too."""
    check_slots(slot_distances())
    path = REPO / "data" / "catalog" / "images.json"
    current = json.loads(path.read_text())
    current.update(catalogue_entries())
    path.write_text(json.dumps(current, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Recipe
# ---------------------------------------------------------------------------


def arm_text() -> str:
    return f"<image> {caption()}"


def recipe() -> dict[str, Any]:
    ds = read_any(RAW / DATA_FILE)
    labels = ds.value_labels
    if {int(k): v for k, v in labels[COND_VAR].items()} != {n: f"Picture {n}" for n in ARMS}:
        raise SystemExit(f"{COND_VAR} value labels changed: {labels[COND_VAR]}")
    counts = ds.df[COND_VAR].value_counts().to_dict()
    if {int(cast(float, k)): int(v) for k, v in counts.items()} != {1: 636, 2: 644, 3: 625, 4: 607}:
        raise SystemExit(f"{COND_VAR} counts changed: {counts}")
    if "XTESS042\n1=Picture1\n2=Picture2\n3=Picture3\n4=Picture4" not in _txt():
        raise SystemExit("Q's sample-variable block changed")

    degree = grid_scale()
    low, mid, high = f"{degree[0]} Disagree", degree[3], f"{degree[-1]} Agree"
    for var in OUTCOME_VARS:
        want = {-1: "Refused", 1: low, 4: mid, 7: high}
        got = {k: labels[var][k] for k in want}
        if got != want:
            raise SystemExit(f"{var}: value labels {got} differ from Q's grid header")

    directives = grid_directives()
    if directives != {
        "Q1": "[GRID - SP - PLACE IMAGE ABOVE QUESTIONS]",
        "Q4": "[GRID - SP - PLACE IMAGE ABOVE QUESTIONS]",
        "Q7": "[GRID - SP - PLACE IMAGE ABOVE QUESTIONS]",
        "Q10": "[GRID - SP]",
    }:
        raise SystemExit(f"grid directives changed: {directives}")

    stmts = statements()
    outcomes = [
        {
            "var": var,
            "task_num": t,
            "question": f'{OUTCOME_LEAD} "{stmts[var]}"',
            "scale": {"min": 1, "max": 7, "min_label": low, "mid_label": mid, "max_label": high},
        }
        for t, var in enumerate(OUTCOME_VARS)
    ]
    arms = [
        {
            "raw": n,
            "condition_num": n - 1,
            "factors": FACTORS[n],
            "text": arm_text(),
            "images": [image_id(n)],
        }
        for n in ARMS
    ]
    return {
        "study_id": STUDY,
        "source": "tess",
        "title": "Perceptions of Diversity Across Groups",
        "data_file": DATA_FILE,
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_var": COND_VAR,
            "factors": ["black_member_present", "asian_member_present"],
            "arms": arms,
        },
        "outcomes": outcomes,
        "response_recode": {i: i for i in range(1, 8)},
        "missing_codes": [-1],
        "persona_missing": {
            "xparty7": [8, 9],
            "xideo": [-1, 8, 9],
            "xrel1": [14],
            "xrel2": [-1],
        },
        "persona_label_rewrite": {"xrel1": {12: "Other non-Christian"}},
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
            "party_id": "xparty7",
            "ideology": "xideo",
            "religion": "xrel1",
        },
    }


def render() -> str:
    return yaml.safe_dump(recipe(), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--prep", action="store_true", help="extract the pictures from the .docx")
    ap.add_argument("--catalogue", action="store_true", help="add this study's images.json entries")
    args = ap.parse_args()
    if args.prep:
        extract()
        print(f"wrote {IMAGES.relative_to(REPO)}/picture{{1,2,3,4}}.png")
        return 0
    if args.catalogue:
        write_catalogue()
        print("updated data/catalog/images.json (es4xw entries only)")
        return 0
    check_slots(slot_distances())
    check_composition(diversity_means())
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
