#!/usr/bin/env python3
"""Write recipes/images/5an26.yaml: a headshot and a short profile of "Diane" or "David".

Paustian-Underdahl, TESS2 069 (University of North Carolina at Charlotte), "Gender and
Physical Attractiveness as Status Beliefs". OSF 5an26. Fielded 11 to 23 March 2011 by
Knowledge Networks (KnowledgePanel), US adults: 645 fielded, 435 completed (the response
rate report), all 435 in the file and all built. Files used: the data
(TESS2_069_Paustian-Underdahl_Client.sav), the fielded questionnaire as Word ("TESS2 069 -
Paustian-Underdahl_vfinal.doc", "Q" below) and as text (the .txt beside it, the same words
without the pictures). The proposal (PaustianUnderdahl098.pdf) is not used: it describes
a 2 x 2 with executive and secretary items that were not fielded as such.

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* DESIGN. 2 (gender) x 2 (attractiveness) x 4 (occupation) between people, 16 arms in
  XTESS069 (Q's table and the .sav's value labels, "A / Female / Attractive / Manager of
  Computer and Information Systems" .. "D / Male / Unattractive / Human Resources
  Specialist", asserted equal; 23-32 people per arm). recipe_prep.py (Jev) named XTESS069
  the assignment at confidence 0.94. condition_num is XTESS069 - 1. The factors are the
  study's own labels: `gender` (Female / Male), `attractiveness` (Attractive /
  Unattractive), `occupation` (the four job titles).
* WHAT CARRIES EACH FACTOR. Gender: the name and pronouns in the profile (Diane
  Williams, "professional woman" / David Williams, "professional man") and the photo.
  Attractiveness: the photo ALONE; Q's sixteen profiles are word-for-word the same
  within each gender (asserted). Occupation: only the hiring screens of Part III.
* WHICH PHOTO IS WHICH ARM. Q's table names a photo letter per arm: A for arms 1-4, B
  for 5-8, C for 9-12, D for 13-16, and Q prints the four photos in one paragraph under
  "Photos:", above a line of the four letters "A B C D". The pictures are inline Word 97
  pictures; this script reads Q's own structure (the OLE streams, the piece table and the
  character runs' sprmCPicLocation) and finds exactly four in that paragraph, left to
  right at character positions 1781, 1795, 1817 and 1834, each pointing to its own
  picture record in the Data stream. Each picture's bytes are taken from its own
  OfficeArt BLIP record, not by searching for image signatures (three JPEGs and one
  PNG, 187 x 201, 171 x 229, 192 x 193 and 159 x 223 pixels). Two independent checks,
  both computed locally:
  - Q29 is the attractiveness manipulation check ("how does Diane rate on physical
    attractiveness?", 1-9). Mean by photo: A 6.96, B 6.53, C 4.20, D 4.77 (n 104, 111,
    109, 109). A and B, which the table calls Attractive, are each rated above both C
    and D; `check_attractiveness` fails if that ordering is lost.
  - Seen by eye: the first and third pictures show the profile's woman, the second and
    fourth its man, as A/C Female and B/D Male require. (A check of judgement, recorded
    here, not computed.)
  The four are copied to data/raw/5an26/images/photo_a.jpg, photo_b.jpg, photo_c.jpg and
  photo_d.png. They are small (Q carries the note "WE WILL GET LARGER IMAGES FROM CLIENT,
  YES/NO?"), so the photos respondents saw may have been larger copies of the same
  pictures; the deposit holds no other copy. Recorded in each catalogue entry.
* IMAGE IDS are 5an26_photo_a .. 5an26_photo_d, Q's own neutral letters. They say
  nothing about attractiveness or gender. Our descriptions state only framing, backdrop
  and clothing: no judgement of looks, and no race, age or gender words.
* CONDITION, BY STAGE. Q's order: two instruction screens; Part I, the photo and
  profile on one page with the Q1-Q7 grid; Parts II and III in random order ("RANDOMIZE
  AND RECORD ORDER OF PART II AND PART III"); Part IV; then Q29. The data file has no
  column recording the Part II / Part III order (all 67 columns checked), so for a
  given respondent we cannot know which came first. Each row says only what EVERY
  respondent in its arm had certainly seen by its question:
  - shared_context: the two instruction screens, word-for-word ("We're studying how
    people quickly form first impressions ...", "Refer back to the description and
    picture ...").
  - Part I and Part II (tasks 0-20): the photo, then the profile. Part II's page showed
    only a link back to the photo and profile ("CLICK HERE TO REVIEW THE DESCRIPTION AND
    PICTURE"); everyone had seen both on the Part I page. About half the respondents
    had ALSO done Part III (the job and credentials) before Part II, but which half is
    not recorded, so Part II's condition cannot say so and does not. These rows differ
    only by gender and photo; the four occupation arms of each photo render identical
    text here, declared per cell with `condition_text` (QC rule 1's exemption).
  - Part III (tasks 21-25): the photo and profile, then the job screen ("Pretend you are
    looking to hire someone for the position of <job>" and the job's description), the
    credentials notice ("Please review Diane's credentials ... for a position in this
    job."), and the line Q shows under the photo and profile on the next page ("Diane
    attended Emory University and earned a bachelor's degree in 1993. Diane has
    completed a preliminary interview for this position, in which she scored well.").
    That page repeats the photo and profile above the new line; the repeat is not
    written out a second time (a row carries each picture once). This is each arm's
    `text`, the one QC rules 5 and 23 read.
  - Part IV (tasks 26-27): everything in Part III (both II and III precede IV), then
    the Part IV screen about SAT scores, word-for-word. It does not vary by arm.
  Screens are joined by blank lines. No connecting words of ours anywhere in a
  condition. The job title in "Pretend you are looking to hire someone for the
  position of Manager of Human Resources" has no full stop in Q and is given none.
* FILLS. Q's directives "[IF XTESS069=1-4, 9-12: Diane/IF XTESS069=5-8, 13-16: David]",
  the same with "she/he", and "[INSERT OCCUPATION NAME BASED ON ASSIGNED
  OCCUPATION=1-4]" are resolved per arm here, and nothing else bracketed may remain.
  Q's OCCUPATION = 1-4 table (XTESS069 1, 5, 9, 13 -> 1 and so on) is asserted to agree
  with the design table's job per arm. Every question wording is also checked against
  the .sav's own variable label once its "{Diane/David}" fill is put back.
* OUTCOMES. 28, in Q's order:
  - Q1-Q7 (tasks 0-6), Part I's grid, 1-9, "Below average" / "Average" / "Above
    average" (Q's header and the .sav's labels on 1, 5 and 9).
  - Q8-Q21 (tasks 7-20), Part II's competency grid, 1-5, the same three labels on 1, 3
    and 5. Each is the grid's stem then the competency as Q lists it, joined by a space
    ("How adequately do you think Diane exhibits the following competencies:
    Aggression"). The grid was randomised ("[RANDOMIZE]"), order not recorded; no row
    says where its item sat.
  - Q22-Q25 (tasks 21-24), Part III's grid, 1-5, the same labels; each question is
    the grid's stem "On a scale of 1 (LOW) to 5 (HIGH) please rate the applicant on the
    following items." then the item, word-for-word (Q24's "How well Diane would fit in
    on the job as a ...?" is Q's grammar).
  - Q26 (task 25), starting salary, six US dollar bands, 1-6 in Q's order. The bands
    are enumerated after the question as "Options: 1 = $20,000-$39,999, ..." (the words
    "Options:" and the "n =" codes are ours, as in 3muqx). Q's question ends with an
    unpaired closing quotation mark ("should earn?”"), absent from the .sav's label;
    dropped as typography.
  - Q27 and Q28 (tasks 26-27), Part IV: of twenty hires for work with numbers (Q27) or
    words (Q28), how many would be men and how many women. One screen, two boxes "Men"
    and "Women", and the screen would not continue until they summed to 20 (Q27_TOTAL
    and Q28_TOTAL are 20 for all 435). Built once each, from the "Men" box, with the
    added sentence 'Report only the number for "Men".' (docs/CONVENTIONS.md, One stem,
    several labelled answer fields). The "Women" box is 20 minus "Men" for every
    respondent, so building it would add a row and no information. 0-20.
    These are kept as outcomes although the screen does not vary by arm: they are
    judgements asked after the manipulation, about hiring men and women, which is what
    the study is about; they are not about the respondent (the yjvpn moderator ruling)
    and not a check on the stimulus.
  -1 "Refused" is the only non-answer code.
* NOT BUILT. Q29, the attractiveness manipulation check (docs/CONVENTIONS.md,
  Attention and recall checks): 433 answers. It is the evidence for the photo mapping
  above. The Women boxes Q27_Female / Q28_Female (870 answers, determined by the Men
  boxes) and the constant totals.
* WHO. All 435 completes; `CaseID` is the participant id. Each refusal drops only
  that row.
* PERSONA. The KnowledgePanel PP* fields, XPARTY7, XIDEO and XREL1, as es4xw:
  education PPEDUCAT and region PPREG4 (Jev preferred PPREG4 over ppreg9 at 0.45 to
  0.41, a close call; PPREG4 matches every other KnowledgePanel recipe). XREL1 code 12
  "Other non-Christian, please specify" is rewritten to "Other non-Christian".
  Sentinel codes on XPARTY7 / XIDEO / XREL1 declared as in es4xw. The persona has no
  field the profile names: nobody's own name, occupation or looks is recorded.
* UK FIT. rich accepted dollar amounts and US references in image experiments
  (9 Nov 2026). The US references here are Emory University, the SAT and the salary
  bands. The sample is American.
* SOCSCI210 holds 5an26 (11,689 rows, 435 people) as FOUR conditions (gender x
  attractiveness, the occupations merged) and 27 items worded from the proposal, not
  from Q. Matched column by column on response distributions, its 27 items are exactly
  the .sav's Q1-Q26 and Q29 in file order, from Q8 on under proposal wordings that do
  not belong to those columns (Q23 is called the attractiveness rating, Q29 "how many
  would be women", Q20's 1-5 answers are stored x1000 and Q26's salary bands x20). Our
  rows are its Q1-Q26 rows exactly (same people, same answers), minus Q29 (433) as a
  manipulation check, plus Q27 and Q28 Men (870): 11,689 - 433 + 870 = 12,126.
  Its four conditions are our sixteen merged by photo; per photo our Q1-Q26 rows plus
  the Q29 answers equal its counts (tests/test_gen_5an26.py). Because the arms are
  merged, `comparable_to_socsci210` is false and the comparison lives in the test.
* CAVEAT. The photos appear to be of real people, with no statement of who they are or
  of their consent, and the deposit states no licence. rich accepted both on 9 Nov 2026
  (as for es4xw). Recorded in each catalogue entry.

    uv run python scripts/gen_5an26.py --prep       # extract the four photos from Q
    uv run python scripts/gen_5an26.py --catalogue  # (re)write this study's images.json entries
    uv run python scripts/gen_5an26.py              # write the recipe
    uv run python scripts/gen_5an26.py --check      # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

STUDY = "5an26"
RAW = REPO / "data" / "raw" / STUDY
DATA_FILE = "TESS2_069_Paustian-Underdahl_Client.sav"
DOC = RAW / "TESS2 069 - Paustian-Underdahl_vfinal.doc"
TXT = RAW / "TESS2 069 - Paustian-Underdahl_vfinal.txt"
IMAGES = RAW / "images"
RECIPE = REPO / "recipes" / "images" / f"{STUDY}.yaml"
LICENCE = (
    "None stated: the OSF deposit 5an26 has no licence (node_license null, checked "
    "2026-10-02), TESS archived it without reuse terms, and TESS has since suspended "
    "operations. The photos appear to be of real people, with no statement of who they "
    "are or of their consent. Used with rich's ruling of 9 Nov 2026 accepting both."
)

ID_VAR = "CaseID"
COND_VAR = "XTESS069"
ARMS = list(range(1, 17))
LETTERS = "abcd"
N_ARM = {1: 24, 2: 28, 3: 29, 4: 23, 5: 27, 6: 26, 7: 26, 8: 32}
N_ARM |= {9: 29, 10: 27, 11: 27, 12: 27, 13: 27, 14: 28, 15: 28, 16: 27}

# Visible facts only: framing, backdrop, clothing. No gender, race, age, hair,
# expression or any appraisal of looks: the photo IS the attractiveness manipulation.
_FRAME = (
    "A small colour head-and-shoulders photograph of one person facing the camera, "
    "cropped at the chest"
)
DESCRIPTIONS = {
    "a": f"{_FRAME}, in front of an even pale grey backdrop. The person wears a dark red "
    "jacket and drop earrings. No words.",
    "b": f"{_FRAME}, in front of a dark brown-grey mottled backdrop. The person wears a "
    "dark pinstriped suit jacket, a white shirt and a pale blue-grey patterned tie. "
    "No words.",
    "c": f"{_FRAME}, in front of an even grey-beige backdrop. The person wears a black "
    "jacket over a red open-collared shirt, and a fine necklace. No words.",
    "d": f"{_FRAME}, in front of a dark grey backdrop that darkens towards the edges. "
    "The person wears a dark suit jacket, a white shirt and a gold and navy patterned "
    "tie. No words.",
}

NAME_FILL = "[IF XTESS069=1-4, 9-12: Diane/IF XTESS069=5-8, 13-16: David]"
PRONOUN_FILL = "[IF XTESS069=1-4, 9-12: she/IF XTESS069=5-8, 13-16: he]"
OCC_FILL = "[INSERT OCCUPATION NAME BASED ON ASSIGNED OCCUPATION=1-4]"

# Task numbers: Q1-Q26 -> 0-25, then the two Men boxes.
PART1 = [f"Q{i}" for i in range(1, 8)]
PART2 = [f"Q{i}" for i in range(8, 22)]
PART3 = [f"Q{i}" for i in range(22, 27)]
PART4 = ["Q27_Male", "Q28_Male"]
OUTCOME_VARS = PART1 + PART2 + PART3 + PART4
MEN_SENTENCE = 'Report only the number for "Men".'
OPTIONS_LEAD = "Options:"  # ours, as in 3muqx


def image_id(letter: str) -> str:
    return f"{STUDY}_photo_{letter}"


def image_file(letter: str) -> str:
    """Path under data/, as the catalogue records it."""
    ext = "png" if letter == "d" else "jpg"
    return f"raw/{STUDY}/images/photo_{letter}.{ext}"


def _clean(text: str) -> str:
    """Typography only: curly quotes and apostrophes, dashes, whitespace."""
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-").replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# The Word 97 questionnaire: where its pictures sit, and their bytes
# ---------------------------------------------------------------------------

_END = 0xFFFFFFFA


def ole_streams(path: Path) -> dict[str, bytes]:
    """The streams of an OLE compound file (enough of the format for one .doc)."""
    b = path.read_bytes()
    if b[:8] != bytes.fromhex("D0CF11E0A1B11AE1"):
        raise SystemExit(f"{path.name} is not an OLE compound file")
    ssz = 1 << struct.unpack("<H", b[30:32])[0]
    mssz = 1 << struct.unpack("<H", b[32:34])[0]
    nfat, dir_start = struct.unpack("<I", b[44:48])[0], struct.unpack("<I", b[48:52])[0]
    mini_cut, minifat_start = struct.unpack("<II", b[56:64])
    difat_start, ndifat = struct.unpack("<II", b[68:76])
    difat = list(struct.unpack("<109I", b[76:512]))
    s = difat_start
    while ndifat and s < _END:
        vals = struct.unpack(f"<{ssz // 4}I", b[512 + s * ssz : 512 + (s + 1) * ssz])
        difat += vals[:-1]
        s, ndifat = vals[-1], ndifat - 1
    fat: list[int] = []
    for sec in difat[:nfat]:
        fat += struct.unpack(f"<{ssz // 4}I", b[512 + sec * ssz : 512 + (sec + 1) * ssz])

    def read(start: int) -> bytes:
        out, s = b"", start
        while s < _END:
            out += b[512 + s * ssz : 512 + (s + 1) * ssz]
            s = fat[s]
        return out

    d = read(dir_start)
    entries = []
    for i in range(len(d) // 128):
        e = d[i * 128 : (i + 1) * 128]
        nl = struct.unpack("<H", e[64:66])[0]
        name = e[: max(nl - 2, 0)].decode("utf-16-le")
        start, size = struct.unpack("<I", e[116:120])[0], struct.unpack("<I", e[120:124])[0]
        entries.append((name, e[66], start, size))
    ministream = read(entries[0][2])[: entries[0][3]]
    minifat: list[int] = []
    s = minifat_start
    while s < _END:
        minifat += struct.unpack(f"<{ssz // 4}I", b[512 + s * ssz : 512 + (s + 1) * ssz])
        s = fat[s]
    out: dict[str, bytes] = {}
    for name, kind, start, size in entries:
        if kind != 2:
            continue
        if size < mini_cut:
            data, s = b"", start
            while s < _END:
                data += ministream[s * mssz : (s + 1) * mssz]
                s = minifat[s]
            out[name] = data[:size]
        else:
            out[name] = read(start)[:size]
    return out


def _sprms(grpprl: bytes) -> list[tuple[int, bytes]]:
    out, j = [], 0
    while j + 2 <= len(grpprl):
        sprm = struct.unpack("<H", grpprl[j : j + 2])[0]
        spra, j = sprm >> 13, j + 2
        size = grpprl[j] + 1 if spra == 6 else {0: 1, 1: 1, 2: 2, 3: 4, 4: 2, 5: 2, 7: 3}[spra]
        out.append((sprm, grpprl[j : j + size]))
        j += size
    return out


def doc_pictures() -> list[tuple[int, int, str, str, str]]:
    """(character position, Data-stream offset, its paragraph, the paragraph before,
    the next paragraph with any text) of every inline picture in Q with a picture
    location, in reading order."""
    st = ole_streams(DOC)
    wd = st["WordDocument"]
    tbl = st["1Table" if struct.unpack("<H", wd[10:12])[0] & 0x0200 else "0Table"]
    csw = struct.unpack("<H", wd[32:34])[0]
    p = 34 + csw * 2
    p += 2 + struct.unpack("<H", wd[p : p + 2])[0] * 4
    cb = struct.unpack("<H", wd[p : p + 2])[0]
    pairs = [struct.unpack("<II", wd[p + 2 + i * 8 : p + 10 + i * 8]) for i in range(cb)]
    (fc_bte, lcb_bte), (fc_clx, lcb_clx) = pairs[12], pairs[33]
    clx, i = tbl[fc_clx : fc_clx + lcb_clx], 0
    while clx[i] == 1:
        i += 3 + struct.unpack("<H", clx[i + 1 : i + 3])[0]
    lcb = struct.unpack("<I", clx[i + 1 : i + 5])[0]
    plc = clx[i + 5 : i + 5 + lcb]
    n = (lcb - 4) // 12
    cps = struct.unpack(f"<{n + 1}I", plc[: (n + 1) * 4])
    pieces = []
    for k in range(n):
        raw_fc = struct.unpack("<I", plc[(n + 1) * 4 + k * 8 + 2 : (n + 1) * 4 + k * 8 + 6])[0]
        comp = bool(raw_fc & 0x40000000)
        fc = (raw_fc & 0x3FFFFFFF) // (2 if comp else 1)
        pieces.append((cps[k], cps[k + 1], fc, comp))

    def cp_of(fc: int) -> int | None:
        for cp0, cp1, f0, comp in pieces:
            w = 1 if comp else 2
            if f0 <= fc < f0 + (cp1 - cp0) * w:
                return cp0 + (fc - f0) // w
        return None

    def text(lo: int, hi: int) -> str:
        out = ""
        for a, b_, f0, comp in pieces:
            s, e = max(a, lo), min(b_, hi)
            if s < e:
                out += (
                    wd[f0 + s - a : f0 + e - a].decode("cp1252")
                    if comp
                    else wd[f0 + 2 * (s - a) : f0 + 2 * (e - a)].decode("utf-16-le")
                )
        return out

    full = text(0, cps[-1])
    bte = tbl[fc_bte : fc_bte + lcb_bte]
    m = (lcb_bte - 4) // 8
    found = []
    for pn in struct.unpack(f"<{m}I", bte[(m + 1) * 4 :]):
        page = wd[(pn & 0x3FFFFF) * 512 : (pn & 0x3FFFFF) * 512 + 512]
        crun = page[511]
        rgfc = struct.unpack(f"<{crun + 1}I", page[: (crun + 1) * 4])
        for r in range(crun):
            off = page[(crun + 1) * 4 + r] * 2
            if not off:
                continue
            sprms = dict(_sprms(page[off + 1 : off + 1 + page[off]]))
            loc = sprms.get(0x6A03)
            cp = cp_of(rgfc[r])
            if loc is None or cp is None or full[cp] != "\x01":
                continue
            offset = struct.unpack("<I", loc)[0]
            if offset == 0:  # a field-code run carrying a default location, not a picture
                continue
            start = full.rfind("\r", 0, cp) + 1
            end = full.find("\r", cp)
            before = full[full.rfind("\r", 0, start - 1) + 1 : start - 1]
            after = next((x for x in full[end + 1 :].split("\r") if x.strip()), "")
            found.append((cp, offset, full[start:end], before, after))
    return sorted(found)


def photos_paragraph() -> tuple[list[int], list[int], str]:
    """Character positions and Data-stream offsets of the pictures in the paragraph
    directly after "Photos:", left to right, and the next paragraph's text (the
    letters under them). Read from the .doc alone."""
    para = [p for p in doc_pictures() if p[3].strip() == "Photos:"]
    if len(para) != 4 or len({p[2] for p in para}) != 1:
        raise SystemExit(f"expected one paragraph of exactly four pictures, found {para}")
    if para[0][2].replace("\x01", "").strip():
        raise SystemExit("the Photos paragraph now holds text as well as pictures")
    return [p[0] for p in para], [p[1] for p in para], para[0][4]


def _blip(data: bytes, start: int, end: int) -> bytes:
    """The one picture inside an OfficeArt record sequence, by its record header."""
    pos, found = start, []
    while pos + 8 <= end:
        ver_inst, kind, length = struct.unpack("<HHI", data[pos : pos + 8])
        ver, inst = ver_inst & 0xF, ver_inst >> 4
        body = pos + 8
        if ver == 0xF:  # container: descend
            found.append(_blip(data, body, body + length))
        elif kind == 0xF007:  # FBSE: a fixed 36-byte header and a name, then the blip
            name_len = data[body + 33]
            inner = body + 36 + name_len
            found.append(_blip(data, inner, body + length))
        elif kind in (0xF01D, 0xF01E, 0xF02A):  # JPEG, PNG, CMYK JPEG
            uids = 2 if inst in (0x46B, 0x6E3, 0x6E1, 0x6E5) else 1
            found.append(data[body + 16 * uids + 1 : body + length])
        pos = body + length
    found = [f for f in found if f]
    if len(found) > 1:
        raise SystemExit(f"more than one picture in one record at {start}")
    return found[0] if found else b""


def picture_bytes() -> dict[str, bytes]:
    """Letter -> the picture's bytes, left to right in the Photos paragraph."""
    data = ole_streams(DOC)["Data"]
    _, offsets, letters = photos_paragraph()
    if letters.split() != ["A", "B", "C", "D"]:
        raise SystemExit(f"the line under the photos changed: {letters!r}")
    out = {}
    for letter, off in zip(LETTERS, offsets, strict=True):
        lcb, cb_header = struct.unpack("<IH", data[off : off + 6])
        pic = _blip(data, off + cb_header, off + lcb)
        jpeg = pic[:3] == b"\xff\xd8\xff" and pic[-2:] == b"\xff\xd9"
        png = pic[:8] == b"\x89PNG\r\n\x1a\n" and pic[-8:-4] == b"IEND"
        if not (jpeg or png) or (png != (letter == "d")):
            raise SystemExit(f"photo {letter}: not the expected complete JPEG / PNG")
        if picture_size(pic) != SIZES[letter]:
            raise SystemExit(f"photo {letter}: size {picture_size(pic)} changed")
        out[letter] = pic
    return out


def picture_size(pic: bytes) -> tuple[int, int]:
    """(width, height) from a PNG header or a JPEG's first SOF marker."""
    if pic[:4] == b"\x89PNG":
        w, h = struct.unpack(">II", pic[16:24])
        return w, h
    i = 2
    while i < len(pic):
        marker, length = pic[i + 1], struct.unpack(">H", pic[i + 2 : i + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h, w = struct.unpack(">HH", pic[i + 5 : i + 9])
            return w, h
        i += 2 + length
    raise SystemExit("no JPEG frame header")


SIZES = {"a": (187, 201), "b": (171, 229), "c": (192, 193), "d": (159, 223)}


def extract() -> None:
    """--prep: copy each picture out of Q, byte for byte."""
    IMAGES.mkdir(exist_ok=True)
    for letter, data in picture_bytes().items():
        (REPO / "data" / image_file(letter)).write_bytes(data)


# ---------------------------------------------------------------------------
# The questionnaire's words
# ---------------------------------------------------------------------------


def _lines() -> list[str]:
    return TXT.read_text(encoding="utf-8").splitlines()


def design_table() -> dict[int, tuple[str, str, str, str]]:
    """XTESS069 -> (photo letter, gender, attractiveness, occupation), from Q's table."""
    lines = [x.strip() for x in _lines()]
    i = lines.index("XTESS069")
    if lines[i + 1 : i + 5] != ["Photo", "Gender", "Attractiveness", "Occupation"]:
        raise SystemExit("design table header changed")
    out = {}
    for k in range(16):
        row = lines[i + 5 + k * 5 : i + 10 + k * 5]
        out[int(row[0])] = (row[1], row[2], row[3], row[4])
    if sorted(out) != ARMS:
        raise SystemExit(f"design table arms changed: {sorted(out)}")
    return out


def profiles() -> dict[int, tuple[str, str]]:
    """XTESS069 -> (photo letter, profile text) from "DESCRIPTIONS FOR XTESS069=1-16"."""
    text = "\n".join(_lines())
    out = {}
    for m in re.finditer(r"XTESS069= (\d+): \n\{Photo ([A-D])\}\n(.+)", text):
        out[int(m.group(1))] = (m.group(2), _clean(m.group(3)))
    if sorted(out) != ARMS:
        raise SystemExit(f"profiles changed: {sorted(out)}")
    return out


def occupations() -> dict[int, tuple[str, str]]:
    """OCCUPATION n -> (name, description)."""
    lines = [x.strip() for x in _lines()]
    out = {}
    for n in range(1, 5):
        i = lines.index(f"OCCUPATION {n}")
        out[n] = (_clean(lines[i + 1]), _clean(lines[i + 2]))
    return out


def occupation_of_arm() -> dict[int, int]:
    """Q's "IF XTESS069=1, 5, 9, OR 13 OCCUPATION=1" table."""
    out = {}
    for m in re.finditer(r"IF XTESS069=([\d, OR]+?)\s+OCCUPATION=(\d)", "\n".join(_lines())):
        for arm in re.findall(r"\d+", m.group(1)):
            out[int(arm)] = int(m.group(2))
    if sorted(out) != ARMS:
        raise SystemExit(f"occupation table changed: {out}")
    return out


def _after(marker: str, skip_blank: bool = True) -> str:
    lines = _lines()
    i = next(k for k, x in enumerate(lines) if x.strip() == marker)
    return next(x for x in lines[i + 1 :] if x.strip()) if skip_blank else lines[i + 1]


def intro() -> str:
    """The two instruction screens before the photo: three paragraphs, word-for-word."""
    lines = _lines()
    i = next(k for k, x in enumerate(lines) if x.strip() == "Part I.")
    block = [x for x in lines[i + 1 : i + 7] if x.strip() and x.strip() != "[DISPLAY]"]
    if len(block) != 3 or not block[0].startswith("We") or not block[2].startswith("Refer"):
        raise SystemExit(f"instruction screens changed: {block}")
    return "\n\n".join(_clean(x) for x in block)


def part3_screens() -> tuple[str, str, str]:
    """(job screen lead, credentials notice, line under the photo), with fills."""
    lines = _lines()
    lead = next(_clean(x) for x in lines if x.startswith("Pretend you are looking"))
    k = next(k for k, x in enumerate(lines) if x.startswith("Please review "))
    review = _clean(lines[k] + " " + lines[k + 1])
    under = next(_clean(x) for x in lines if "attended Emory University" in x)
    return lead, review, under


def part4_screen() -> str:
    lines = _lines()
    i = next(k for k, x in enumerate(lines) if x.strip() == "Part IV.")
    block = [x for x in lines[i + 1 : i + 6] if x.strip() and x.strip() != "[DISPLAY]"]
    if len(block) != 2 or not block[0].startswith("On average, high school girls"):
        raise SystemExit(f"Part IV screen changed: {block}")
    return "\n\n".join(_clean(x) for x in block)


def fill(text: str, arm: int, occupation: str | None = None) -> str:
    """Resolve Q's directives for one arm; nothing bracketed may survive."""
    female = arm in (1, 2, 3, 4, 9, 10, 11, 12)
    text = text.replace(NAME_FILL, "Diane" if female else "David")
    text = text.replace(PRONOUN_FILL, "she" if female else "he")
    if OCC_FILL in text:
        if occupation is None:
            raise SystemExit("an occupation fill with no occupation")
        text = text.replace(OCC_FILL, occupation)
    if "[" in text or "{" in text:
        raise SystemExit(f"unresolved directive: {text!r}")
    return text


def part1_questions() -> list[str]:
    """Q1-Q7 from Q's grid, one table row whose cells the .txt separates with BEL."""
    line = next(x for x in _lines() if "How intelligent do you perceive" in x)
    cells = [_clean(c) for c in line.split("\a") if c.strip()]
    header = ["Below average", "Average", "Above average", *map(str, range(1, 10))]
    if cells[:12] != header or len(cells) != 19:
        raise SystemExit(f"Part I grid changed: {cells}")
    return cells[12:]


def part2_stem_and_items() -> tuple[str, list[str]]:
    lines = [x.strip() for x in _lines()]
    stem = next(_clean(x) for x in lines if x.startswith("How adequately do you think"))
    i = lines.index("Part II.")
    j = lines.index("Part III.")
    k = next(n for n in range(i, j) if lines[n] == "5")
    items = [_clean(x) for x in lines[k + 1 : j] if x]
    if len(items) != 14:
        raise SystemExit(f"Part II items changed: {items}")
    return stem, items


def part3_stem_and_items() -> tuple[str, list[str]]:
    lines = [x.strip() for x in _lines()]
    stem = next(_clean(x) for x in lines if x.startswith("On a scale of 1 (LOW)"))
    starts = ("What do you think is", "How well do you think", "How well [", "What is the")
    items = [_clean(x) for x in lines if x.startswith(starts)]
    if len(items) != 4:
        raise SystemExit(f"Part III grid changed: {items}")
    return stem, items


def salary() -> tuple[str, list[str]]:
    lines = [x.strip() for x in _lines()]
    i = next(k for k, x in enumerate(lines) if x.startswith("Which of these starting salaries"))
    q = _clean(lines[i])
    if not q.endswith('earn?"'):
        raise SystemExit(f"salary question changed: {q!r}")
    q = q[:-1]  # the unpaired closing quotation mark (module docstring, Q26)
    bands = [x for x in lines[i + 1 : i + 9] if x]
    if len(bands) != 6:
        raise SystemExit(f"salary bands changed: {bands}")
    return q, bands


def twenty() -> dict[str, str]:
    """Q27 / Q28: the two sentences above the Men / Women boxes."""
    lines = [x.strip() for x in _lines()]
    out = {}
    for var, kind in (("Q27_Male", "numbers"), ("Q28_Male", "words")):
        i = lines.index(
            f"Suppose you had twenty positions to fill where the work required working with {kind}."
        )
        j = next(k for k in range(i + 1, len(lines)) if lines[k])
        if not lines[j].startswith(f"Of the twenty people you hired to work with {kind}"):
            raise SystemExit(f"{var} wording changed")
        out[var] = _clean(f"{lines[i]} {lines[j]}")
        nxt = [x for x in lines[j + 1 : j + 8] if x]
        if [x.split()[0] for x in nxt[:3]] != ["Men", "Women", "Total"]:
            raise SystemExit(f"{var}: answer boxes changed: {nxt[:3]}")
    return out


# ---------------------------------------------------------------------------
# Which photo is attractive: the manipulation check, computed locally
# ---------------------------------------------------------------------------


def q29_means() -> dict[str, float]:
    """Photo letter -> mean Q29 (attractiveness, 1-9, answers only)."""
    df = read_any(RAW / DATA_FILE).df
    ok = df["Q29"].between(1, 9)
    letter = ((df.loc[ok, COND_VAR] - 1) // 4).astype(int).map(dict(enumerate(LETTERS)))
    means = df.loc[ok, "Q29"].groupby(letter).mean()
    return {str(k): float(v) for k, v in means.items()}


def check_attractiveness(
    means: dict[str, float], table: dict[int, tuple[str, str, str, str]]
) -> None:
    """Every photo the table calls Attractive is rated above every one it calls
    Unattractive, by at least a point."""
    label = {row[0].lower(): row[2] for row in table.values()}
    hi = [means[x] for x in LETTERS if label[x] == "Attractive"]
    lo = [means[x] for x in LETTERS if label[x] == "Unattractive"]
    if len(hi) != 2 or len(lo) != 2 or min(hi) - max(lo) < 1.0:
        raise SystemExit(f"Q29 no longer separates the attractive photos: {means}")


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------


def catalogue_entries() -> dict[str, dict[str, str]]:
    """This study's entries in data/catalog/images.json, after checking each file is
    the picture at its position in Q's Photos paragraph, byte for byte."""
    from micromotives_datasets.images import sha256_of

    pics = picture_bytes()
    _, offsets, _ = photos_paragraph()
    out: dict[str, dict[str, str]] = {}
    for n, letter in enumerate(LETTERS):
        f = REPO / "data" / image_file(letter)
        if f.read_bytes() != pics[letter]:
            raise SystemExit(f"{image_file(letter)} is not photo {letter.upper()} of Q")
        w, h = picture_size(pics[letter])
        out[image_id(letter)] = {
            "file": image_file(letter),
            "sha256": sha256_of(f),
            "source": (
                "OSF 5an26, TESS2 069 (Paustian-Underdahl) deposit: inline picture "
                f'{n + 1} of 4, left to right, in the paragraph under "Photos:" of the '
                'fielded questionnaire "TESS2 069 - Paustian-Underdahl_vfinal.doc", above '
                f"the letter {letter.upper()} (Data stream offset {offsets[n]}), copied "
                f"byte for byte from its OfficeArt picture record ({w} x {h}). The "
                'questionnaire notes "WE WILL GET LARGER IMAGES FROM CLIENT", so the '
                "fielded copy may have been larger. A photograph of an apparently real "
                "person, with no statement of who they are or of their consent."
            ),
            "licence": LICENCE,
            "text_in_image": "",
            "description": DESCRIPTIONS[letter],
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


def _strip_code(label: str) -> str:
    return re.sub(r"^\d+ ", "", label)


def recipe() -> dict[str, Any]:
    ds = read_any(RAW / DATA_FILE)
    labels, var_labels, df = ds.value_labels, ds.column_labels, ds.df
    table = design_table()
    want = {n: " / ".join(row) for n, row in table.items()}
    if {int(k): v for k, v in labels[COND_VAR].items()} != want:
        raise SystemExit(f"{COND_VAR} value labels differ from Q's table: {labels[COND_VAR]}")
    counts = {int(k): int(v) for k, v in df[COND_VAR].value_counts().items()}
    if counts != N_ARM or len(df) != 435 or df[ID_VAR].nunique() != 435:
        raise SystemExit(f"{COND_VAR} counts changed: {counts}")
    if any(re.search(r"order|rand|part", c, re.I) for c in df.columns if c != "XPARTY7"):
        raise SystemExit("a column now looks like a recorded Part II / III order")
    check_attractiveness(q29_means(), table)

    profs, occs, occ_of = profiles(), occupations(), occupation_of_arm()
    for n, (photo, gender, _, job) in table.items():
        if profs[n][0] != photo or occs[occ_of[n]][0] != job:
            raise SystemExit(f"arm {n}: photo or job differs between Q's tables")
        if profs[n][1].startswith("Diane") != (gender == "Female"):
            raise SystemExit(f"arm {n}: the profile's name contradicts the table's gender")
    for group in ([1, 2, 3, 4, 9, 10, 11, 12], [5, 6, 7, 8, 13, 14, 15, 16]):
        if len({profs[n][1] for n in group}) != 1:
            raise SystemExit("the profile text varies within a gender")
    if not profs[1][1].startswith("Diane Williams is") or not profs[5][1].startswith("David"):
        raise SystemExit("profile names changed")

    # Question wordings, checked against the .sav's own variable labels.
    p1 = part1_questions()
    stem2, items2 = part2_stem_and_items()
    stem3, items3 = part3_stem_and_items()
    salary_q, bands = salary()
    boxes = twenty()

    def sav_form(q: str) -> str:
        return _clean(q.replace(NAME_FILL, "{Diane/David}").replace(OCC_FILL, "{OCCUPATION}"))

    for var, q in zip(PART1, p1, strict=True):
        if sav_form(q) != _clean(var_labels[var]):
            raise SystemExit(f"{var}: Q {q!r} vs .sav {var_labels[var]!r}")
    for var, item in zip(PART2, items2, strict=True):
        if _clean(var_labels[var]) != f"[{item}] {sav_form(stem2)}":
            raise SystemExit(f"{var}: Q {item!r} vs .sav {var_labels[var]!r}")
    for var, q in zip(PART3[:4], items3, strict=True):
        if sav_form(q) != _clean(var_labels[var]):
            raise SystemExit(f"{var}: Q {q!r} vs .sav {var_labels[var]!r}")
    if sav_form(salary_q) != _clean(var_labels["Q26"]):
        raise SystemExit(f"Q26: Q {salary_q!r} vs .sav {var_labels['Q26']!r}")
    if [labels["Q26"][float(k)] for k in range(1, 7)] != bands:
        raise SystemExit("Q26 bands differ between Q and the .sav")

    # Scales: the grid headers' three words against the .sav's labels.
    nine = {k: _strip_code(labels["Q1"][float(k)]) for k in (1, 5, 9)}
    five = {k: _strip_code(labels["Q8"][float(k)]) for k in (1, 3, 5)}
    if list(nine.values()) != ["Below average", "Average", "Above average"] or list(
        five.values()
    ) != list(nine.values()):
        raise SystemExit("grid labels changed")
    for var in PART1 + PART2 + PART3[:4]:
        ref = labels["Q1" if var in PART1 else "Q8"]
        if labels[var] != ref:
            raise SystemExit(f"{var}: value labels differ from its grid's")

    def scale(lo: int, hi: int) -> dict[str, Any]:
        return {
            "min": lo,
            "max": hi,
            "min_label": "Below average",
            "mid_label": "Average",
            "max_label": "Above average",
        }

    outcomes: list[dict[str, Any]] = []
    for t, var in enumerate(OUTCOME_VARS):
        o: dict[str, Any] = {"var": var, "task_num": t}
        if var in PART1:
            o |= {"question": sav_form(p1[t]), "scale": scale(1, 9)}
        elif var in PART2:
            o |= {"question": f"{sav_form(stem2)} {items2[t - 7]}", "scale": scale(1, 5)}
        elif var in PART3[:4]:
            o |= {"question": f"{stem3} {sav_form(items3[t - 21])}", "scale": scale(1, 5)}
        elif var == "Q26":
            o |= {
                "question": sav_form(salary_q),
                "scale": {"min": 1, "max": 6, "min_label": bands[0], "max_label": bands[-1]},
                "response_recode": {i: i for i in range(1, 7)},
            }
        else:
            o |= {
                "question": f"{boxes[var]} {MEN_SENTENCE}",
                "scale": {"min": 0, "max": 20},
                "response_recode": {i: i for i in range(21)},
            }
        outcomes.append(o)

    lead, review, under = part3_screens()
    sat = part4_screen()

    def question_for(var: str, arm: int, job: str) -> str:
        t = OUTCOME_VARS.index(var)
        if var in PART1:
            return fill(p1[t], arm)
        if var in PART2:
            return f"{fill(stem2, arm)} {items2[t - 7]}"
        if var in PART3[:4]:
            return f"{stem3} {fill(items3[t - 21], arm, job)}"
        if var == "Q26":
            opts = ", ".join(f"{i} = {b}" for i, b in enumerate(bands, 1))
            return f"{fill(salary_q, arm)} {OPTIONS_LEAD} {opts}."
        return f"{boxes[var]} {MEN_SENTENCE}"

    arms = []
    for n in ARMS:
        photo, gender, attract, job = table[n]
        occ_name, occ_desc = occs[occ_of[n]]
        seen_first = f"<image> {profs[n][1]}"
        part3 = "\n\n".join(
            [seen_first, fill(lead, n, occ_name), occ_desc, fill(review, n), fill(under, n)]
        )
        part4 = f"{part3}\n\n{sat}"
        items: dict[int, dict[str, str]] = {}
        for t, var in enumerate(OUTCOME_VARS):
            text = seen_first if var in PART1 + PART2 else part3 if var in PART3 else part4
            items[t] = {"outcome_question": question_for(var, n, job), "condition_text": text}
        arms.append(
            {
                "raw": n,
                "condition_num": n - 1,
                "factors": {"gender": gender, "attractiveness": attract, "occupation": job},
                "text": part3,
                "images": [image_id(photo.lower())],
                "items": items,
            }
        )

    return {
        "study_id": STUDY,
        "source": "tess",
        "title": "Gender and Physical Attractiveness as Status Beliefs",
        "data_file": DATA_FILE,
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": ID_VAR,
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_var": COND_VAR,
            "shared_context": intro(),
            "factors": ["gender", "attractiveness", "occupation"],
            "considered_and_rejected": {
                "Q29": "the attractiveness manipulation check (not an outcome); the "
                "evidence for which photo is which arm",
            },
            "arms": arms,
        },
        "outcomes": outcomes,
        "response_recode": {i: i for i in range(1, 10)},
        "missing_codes": [-1],
        "persona_missing": {
            "XPARTY7": [8, 9],
            "XIDEO": [-1, 8, 9],
            "XREL1": [14],
        },
        "persona_label_rewrite": {"XREL1": {12: "Other non-Christian"}},
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
            "party_id": "XPARTY7",
            "ideology": "XIDEO",
            "religion": "XREL1",
        },
    }


def render() -> str:
    return yaml.safe_dump(recipe(), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--prep", action="store_true", help="extract the photos from the .doc")
    ap.add_argument("--catalogue", action="store_true", help="add this study's images.json entries")
    args = ap.parse_args()
    if args.prep:
        extract()
        print(f"wrote {IMAGES.relative_to(REPO)}/photo_{{a,b,c}}.jpg, photo_d.png")
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
