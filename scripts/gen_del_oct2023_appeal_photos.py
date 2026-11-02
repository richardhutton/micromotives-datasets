#!/usr/bin/env python3
"""Write recipes/images/del_sandbox_oct2023_appeal_photos.yaml: charity appeal photos (IMG06).

Hudson, Jennifer; Hudson, David; Morini, Paolo; Oh, Soomin; Torres-Raposo, Felipe,
2024, "DEL Sandbox 2023", https://doi.org/10.7910/DVN/XZ1XUZ, Harvard Dataverse, V1;
DEL_Sandbox_GreatBritain_Oct2023_Data.sav. Fielded online by YouGov, n = 3,639 adults
in Great Britain (the deposit's Readme, whose fieldwork line reads "9 October 2020 to
18 October 2023", a typo for 9-18 October 2023). The same Dataverse deposit as the
Feb 2023 builds, so licence, person id and persona block carry over from
`del_sandbox_feb2023_wordfeminist` (read from that recipe by this generator, and the
persona variables' value labels are checked identical between the two files).

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* THE DESIGN (DEL_Sandbox_GreatBritain_Oct2023_Survey.docx, MODULE B). `moduleB`
  (`panman.assign_treatment(2, ...)`) puts each respondent on one of two folders of
  photographs: 1 "photographer images" (1,815 people, `photo1`..`photo128`) or 2
  "partner images" (1,824, `IMG1`..`IMG127` plus `IMG102_ps`, which replaced the
  "IMG102 - Excluded" code; twelve partner codes are "No Image"). Five photos are
  then drawn from that folder by least-filled quotas (`Q_Chosen_*`, which agrees with
  the five slots for all 3,639 people). Slot k's photo is recorded per person as
  `image{k}_name` / `_number` / `_url`; every slot is filled, every name belongs to
  the respondent's own folder, every URL equals that photo's constant column, and no
  one sees a photo twice. 243 photos were shown (128 + 115; IMG102 never).
* TWO PAIRS OF PHOTOS ARE THE SAME FILE. photo107 = photo123 and photo112 = photo128,
  byte for byte. Each pair is one picture and one arm (`raws` holds both codes), so
  there are 241 arms, condition_num in folder then number order. Five people were
  shown both members of a pair (one photo107/123, four photo112/128): the second
  showing repeats the first prompt exactly, so the LATER slot's code is left blank in
  the prepped file and its 11 items are not built (`REPEATS`, checked by `prep()`).
* THE PREPPED FILE. The pipeline reads integer codes, so `--prep` writes
  `DEL_Sandbox_GreatBritain_Oct2023_Data-derived.sav`: the deposit unchanged (a
  pyreadstat round trip) plus five columns `image{k}_code` = 1000 x moduleB +
  image{k}_number, blank only for the five repeats. Nothing else changes.
* CONDITION. Ours, around the instrument's own phrase: You were told the images were
  ones that "international development charities/NGOs might use as part of their
  appeals to inspire action against global poverty." Then "This image was shown above
  each question:" and the photo. ADDED by us: "You were told the images were ones
  that", "This image was shown above each question:" and the quotation marks; the
  quoted words are the module's introduction page, word-for-word. That page itself
  ("In the following pages you will see a series of five images that ... Please answer
  the following questions about the images you have been shown.") is NOT rendered: it
  describes the instrument's sequence of five screens, which a row of one image cannot
  carry (docs/CONVENTIONS.md, sequence signposting). Only its appeal framing is kept,
  because nothing else tells the emotion, urgency and efficacy items what the pictures
  are. "Shown above each question" is true for every row: the script puts the slot's
  `<img>` above every item of the slot. DROPPED: the "Here is Image N" heading. The
  slot is recorded nowhere in the row, and earlier photos are not narrated (RISKIEST).
* WORDS IN THE PHOTOS. No captions or overlays. text_in_image holds whole words that
  can be read at the size shown, 600 pixels wide (T-shirt slogans, a sign, tanker
  lettering, the Cyrillic line in IMG119, the Latin-script handwriting on IMG65's
  blackboard); partly hidden words, writing in scripts not transcribed here (Bengali,
  Arabic, Pashto/Dari) and illegible marks are named in the description as not
  transcribed, never guessed. Numerals alone (the boy's "78" patch, "19 84" on IMG106's
  hoodie, the algebra on IMG65's board) are not words and are not recorded. The
  condition does not quote text_in_image (Feb 2023 / k369t precedent: the words are
  incidental to the photograph, not a caption the respondent was given to read). EXIF
  captions inside the files were never on screen and are not used.
* DESCRIPTIONS are ours and say only what is visible: clothing, pose, gaze, whether
  the person is smiling, setting and objects. No inferred emotion ("worried", "sad"),
  age band ("teenage", "older"), hardship ("shack", "camp", "worn") or appraisal of the
  place ("hospital", "plantation", "ruins"), any of which could lead the emotion,
  urgency and efficacy outcomes. Perceived skin colour is still stated; pending a
  ruling.
* OUTCOMES, per slot (suffix a..e = slot 1..5), word-for-word from the questionnaire
  with curly quotes straightened, `**` bold dropped and the urgency question's triple
  space collapsed: the four rows of the emotion grid (stem, then the row in quotation
  marks; rows were shown in random order, not recorded and not rendered), urgency,
  efficacy (all 1-5, endpoint labels as fielded, "1 - " prefixes dropped since the
  question itself names them), find out more (`getinfo`) and donate (yes/no, the two
  answers enumerated in the PZB01G form, "1 means ..."; ours), the amount (`donate_amt`,
  asked only of those who said yes, integer 1-9,999 as fielded, `open-intrange 1
  9999`; one answer of 9999, kept), and the follow-up on impact (0-10), which has two
  wordings: "You said you would donate ..." (`eff_follow_dy`) and "You said you would
  not donate ..." (`eff_follow_dn`; slot 5's are named `eff_follow_ey_e` /
  `eff_follow_en_e`). "You said you would (not) donate" is the instrument's own text,
  identical for everyone routed to the item. ADDED by us to the amount question: 'The
  answer box had "£" before it.' (the field's `left="£"` label; the question names no
  currency). 55 outcomes, task_num = 11 x slot + item.
* ANSWER ORDER. `moduleB2_order` (1 getinfo before donate, 2 donate first) varies
  only the order of the two appeal questions within each slot. It is recorded but not
  rendered, as no other build here renders question order, and it is declared under
  `considered_and_rejected`.
* NON-ANSWERS. 8 "Skipped" / 9 "Not Asked" on the 1-5 and yes/no items, 11 "Don't
  know" on the 0-10 items, and 99998 / 99999 on the amount, are dropped by each
  outcome's own recode (values not listed are dropped). Only 99998 / 99999 are
  study-wide `missing_codes`, because 8, 9 and 11 are real answers on the amount and
  the 0-10 items.
* NOT BUILT. MODULE C (half the sample, `Module_CD` = 1) re-shows two of the five
  photos with checks on what the main subject portrays (`manip_em*`, `manip_act*`,
  `manip_urg*`, `manip_ethn*`): manipulation checks, not outcomes
  (docs/CONVENTIONS.md). MODULE D (`modD_img_url`) is a different module.
* WHAT CAME BEFORE, the same for everyone: aid and development attitudes and actions,
  and "how much attention ... do you pay to images included in charity appeals?".
* PHOTOS. `--fetch` downloads the 243 shown files from the URLs in the .sav into
  data/raw/del/oct2023_images/ (bytes only, never opened as anything but an image).
  The catalogue cites one file per picture (photo107 and photo112 for the pairs).
* PERSONA and PERSON ID as in del_sandbox_feb2023_wordfeminist.yaml (`GUNQID`,
  study_id `del`, shared across all DEL files); age is real years (18-91).
* REFERENCE. No published per-photo or per-folder figures for this module were
  found; the crosscheck is internal (tests/test_gen_del_oct2023_appeal_photos.py).
* RISKIEST JUDGEMENT. Each row's condition is its own photo only. Slots 2-5 were
  answered after one to four other photos from the same folder, and those are not
  narrated. The allocation is by quota, not a randomised order of a fixed set, so the
  repeated-measures ruling (render the block so far) would put a different, mostly
  unique, history into almost every row; the carry-over is unmodelled instead.

    uv run python scripts/gen_del_oct2023_appeal_photos.py --fetch      # download photos
    uv run python scripts/gen_del_oct2023_appeal_photos.py --prep       # derived .sav
    uv run python scripts/gen_del_oct2023_appeal_photos.py --catalogue  # images.json
    uv run python scripts/gen_del_oct2023_appeal_photos.py              # the recipe
    uv run python scripts/gen_del_oct2023_appeal_photos.py --check      # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

RAW = REPO / "data" / "raw" / "del"
SAV = RAW / "DEL_Sandbox_GreatBritain_Oct2023_Data.sav"
FEB_SAV = RAW / "DEL_Sandbox_GreatBritain_Feb2023_Data.sav"
SURVEY = RAW / "DEL_Sandbox_GreatBritain_Oct2023_Survey.docx"
DATA_FILE = "DEL_Sandbox_GreatBritain_Oct2023_Data-derived.sav"
DERIVED = RAW / DATA_FILE
IMAGE_DIR = "raw/del/oct2023_images"  # relative to data/
RECIPE = REPO / "recipes" / "images" / "del_sandbox_oct2023_appeal_photos.yaml"
PERSONA_FROM = REPO / "recipes" / "del_sandbox_feb2023_wordfeminist.yaml"

SET_VAR = "moduleB"
SETS = {1: "photographer", 2: "partner"}
SLOTS = "abcde"  # the instrument's suffix for slot 1..5
# Byte-identical files: the later name is the same picture as the earlier.
SAME_FILE = {"photo123": "photo107", "photo128": "photo112"}
# (slot index 1-5 blanked, because that respondent had already seen the picture)
REPEATS = 5
LICENCE = (
    "Data CC0 (DEL). Photos fetched from the survey's YouGov image URLs; photo rights "
    "not stated (third-party charity and photographer images)."
)


def number_of(name: str) -> int:
    """The folder position a photo name stands for (IMG102_ps took code 128)."""
    return 128 if name == "IMG102_ps" else int(re.sub(r"\D", "", name))


def code_of(set_code: int, number: int) -> int:
    return 1000 * set_code + number


def code_var(k: int) -> str:
    return f"image{k}_code"


def image_id(name: str) -> str:
    return "del_oct2023_" + name.lower()


def _read_sav() -> Any:
    import pyreadstat

    df, _ = pyreadstat.read_sav(str(SAV))
    return df


def shown(df: Any) -> dict[str, tuple[int, str]]:
    """Photo name -> (folder code, URL), for every photo any slot showed. Checked."""
    out: dict[str, tuple[int, str]] = {}
    for k in range(1, 6):
        for s, name, number, url in zip(
            df[SET_VAR],
            df[f"image{k}_name"],
            df[f"image{k}_number"],
            df[f"image{k}_url"],
            strict=True,
        ):
            prefix = "photo" if s == 1 else "IMG"
            if not name.startswith(prefix):
                raise SystemExit(f"slot {k}: {name} shown to folder {s}")
            if number_of(name) != int(number):
                raise SystemExit(f"slot {k}: {name} recorded as number {number}")
            if url != df[name].iloc[0]:
                raise SystemExit(f"slot {k}: {name} shown at {url}, column says otherwise")
            if out.setdefault(name, (int(s), url)) != (int(s), url):
                raise SystemExit(f"{name} shown two ways")
    return out


def file_of(name: str, url: str) -> str:
    """Path under data/ of the downloaded file, keeping the URL's own extension."""
    return f"{IMAGE_DIR}/{name}.{url.rsplit('.', 1)[1]}"


def fetch() -> None:
    import urllib.request

    df = _read_sav()
    for name, (_, url) in sorted(shown(df).items()):
        target = REPO / "data" / file_of(name, url)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with urllib.request.urlopen(url, timeout=60) as resp:
                target.write_bytes(resp.read())
    print(f"fetched into data/{IMAGE_DIR}/")


def pictures(df: Any) -> list[tuple[str, list[str]]]:
    """(catalogued name, every name showing that picture), photographer folder first."""
    names = shown(df)
    digest = {
        n: hashlib.sha256((REPO / "data" / file_of(n, u)).read_bytes()).hexdigest()
        for n, (_, u) in names.items()
    }
    groups: dict[str, list[str]] = {}
    for n in names:
        groups.setdefault(digest[n], []).append(n)
    found = {
        later: first
        for g in groups.values()
        if len(g) > 1
        for first, later in [sorted(g, key=number_of)]
    }
    if found != SAME_FILE or any(len(g) > 2 for g in groups.values()):
        raise SystemExit(f"duplicate files changed: {groups=}")
    out = [
        (n, sorted([n, *[k for k, v in SAME_FILE.items() if v == n]], key=number_of))
        for n in names
        if n not in SAME_FILE
    ]
    return sorted(out, key=lambda p: (names[p[0]][0], number_of(p[0])))


# --- the prepped file --------------------------------------------------------------


def coded(df: Any) -> Any:
    """Add image{k}_code; blank a slot whose picture the respondent already saw."""
    import numpy as np

    out = df.copy()
    same = {code_of(1, number_of(a)): code_of(1, number_of(b)) for a, b in SAME_FILE.items()}
    seen: list[set[int]] = [set() for _ in range(len(df))]
    blanked = 0
    for k in range(1, 6):
        codes = (df[SET_VAR] * 1000 + df[f"image{k}_number"]).to_numpy(dtype=float, copy=True)
        if np.isnan(codes).any():
            raise SystemExit(f"slot {k}: a respondent has no photo")
        for i, c in enumerate(codes):
            picture = same.get(int(c), int(c))
            if picture in seen[i]:
                codes[i] = np.nan
                blanked += 1
            seen[i].add(picture)
        out[code_var(k)] = codes
    if blanked != REPEATS:
        raise SystemExit(f"{blanked} repeated showings, expected {REPEATS}")
    return out


def write_derived() -> None:
    import pyreadstat

    df, meta = pyreadstat.read_sav(str(SAV))
    out = coded(df)
    labels = dict(zip(meta.column_names, meta.column_labels, strict=True))
    value_labels = dict(meta.variable_value_labels)
    for k in range(1, 6):
        labels[code_var(k)] = (
            f"1000 x moduleB + image{k}_number; blank where the picture was already shown"
        )
    pyreadstat.write_sav(
        out, str(DERIVED), column_labels=labels, variable_value_labels=value_labels
    )
    print(f"wrote {DERIVED.relative_to(REPO)}")


# --- the photos -------------------------------------------------------------------

# Whole words legible at the size shown, " / " between separate pieces of text.
GIRL_SHIRT = "FREEDOM"
TEXT_IN_IMAGE: dict[str, str] = {
    "IMG3": "FLOOR",
    "IMG7": "maisha!",
    "IMG13": "Snow Queen",
    "IMG28": "TRAVELLERS",
    "IMG29": "HoA",
    "IMG32": "MAKE HEALTH SERVICES YOUTH FRIENDLY",
    "IMG38": "FLAN-T90",
    "IMG64": "unicef",
    "IMG65": "Maktabada Nuur waxaa / oo / iyo Saynis ah. / ay / xisaabtu? / ah, in",
    "IMG105": "PDAM / UWE LINO / PDAM / Yayasan Sayangi Tunas Cilik / UWE LINO",
    "IMG106": "CASPARLIVO",
    "IMG119": "Мова - душа кожної національності, її / найцінніший скарб. / І. Огієнко",
    # The girl's T-shirt, where the word reads at the size shown (arms, bucket and
    # angle hide or blur it in the others).
    **{
        f"photo{n}": GIRL_SHIRT
        for n in (65, 66, 69, 70, 77, 78, 81, 82, 85, 86, 89, 90, 91, 93, 94, 95)
    },
}

# Ours, and checked: what each photo shows, without guessing who, where or why.
DESCRIPTIONS: dict[str, str] = {
    "IMG1": (
        "Colour photograph, landscape. A smiling boy in a baseball cap and jeans rides a "
        "large green scooter along a road; behind him stands a blackened, roofless two-"
        "storey brick building with empty window holes and heaps of rubble beside it, "
        "under a blue sky."
    ),
    "IMG2": (
        "Colour photograph, landscape. A Black man in a white shirt with a stethoscope "
        "round his neck stands with his arms folded, looking at the camera, not smiling, "
        "in a plain room with metal-framed beds behind him."
    ),
    "IMG3": (
        "Colour photograph, landscape. A Black woman with curly hair, glasses, a white "
        "coat and a pink stethoscope stands with her arms folded, smiling slightly, in a "
        "corridor beside a reception counter where another woman in a blue cap works at a"
        " computer."
    ),
    "IMG4": (
        "Colour photograph, portrait. A girl in a dusty white tracksuit crouches beside a"
        " muddy ditch of water against a rough stone wall, holding a plastic tub; "
        "children stand watching in the narrow alley behind her."
    ),
    "IMG5": (
        "Colour photograph, portrait. A man in a camouflage jacket and cap crouches in a "
        "field of green crops, pulling up a plant, with bare brown hills under a blue sky"
        " behind."
    ),
    "IMG6": (
        "Colour photograph, landscape. A smiling Black woman with long braids, in a red "
        "top decorated with white beads, stands on a sunny grass field with trees and low"
        " buildings out of focus behind her."
    ),
    "IMG7": (
        "Colour photograph, landscape. A Black man in a black knitted hat and black "
        "T-shirt stands with his arms folded, looking to the side, in front of a yellow "
        "corrugated wall covered in painted handprints."
    ),
    "IMG8": (
        "Colour photograph, landscape. Close portrait of a Black woman in profile, "
        "smiling slightly and looking into the distance, wearing a yellow-and-white "
        "striped scarf over her head and a pink top, against a blurred green background."
    ),
    "IMG9": (
        "Colour photograph, square. A Black woman in a sleeveless cream blouse sits "
        "against a mud wall holding a sleeping baby wrapped in a blue-and-white blanket, "
        "looking at the camera; a man in a white shirt sits behind her."
    ),
    "IMG13": (
        "Colour photograph, square. A small Black girl with her hair in knots rubs one "
        "eye with her hand while holding a teddy bear, in a printed T-shirt, with green "
        "trees out of focus behind her."
    ),
    "IMG14": (
        "Colour photograph, landscape. Close portrait of a girl in a green headscarf "
        "looking straight at the camera, unsmiling, in a classroom, with another girl in "
        "a purple headscarf out of focus behind her."
    ),
    "IMG15": (
        "Colour photograph, square. In a dim room, a woman in a pink headscarf and "
        "patterned clothes sits cross-legged on a bed and writes in a book, lit from the "
        "side, smiling slightly as she looks down."
    ),
    "IMG17": (
        "Colour photograph, square. A Black baby looks towards the camera, held against "
        "an adult's chest, while a gloved hand wraps a green and red measuring tape "
        "around the baby's upper arm."
    ),
    "IMG18": (
        "Colour photograph, landscape. A Black man in a white lab coat and gloves sits at"
        " a desk writing in a large ledger, in a laboratory with equipment, an air "
        "conditioner and two colleagues working behind him."
    ),
    "IMG19": (
        "Colour photograph, landscape. A woman in a headscarf with a large basket on her "
        "back picks leaves among rows of low green bushes, under tall trees in mist."
    ),
    "IMG20": (
        "Colour photograph, landscape. A Black woman in a purple top and green wrap skirt"
        " stands holding a stick beside a brick structure topped with a mound of earth, "
        "among banana plants and dry maize stalks under a blue sky."
    ),
    "IMG22": (
        "Colour photograph, landscape. A boy in a striped jacket leans over a low table, "
        "writing in a workbook with a blue pen and holding a sheet of paper, beside a "
        "maroon cushion, with a red cloth hanging behind him."
    ),
    "IMG23": (
        "Colour photograph, square. A woman in a long blue patterned dress and a white "
        "headscarf stands in the open wooden door of a fence made of rough poles, "
        "unsmiling, on dusty ground."
    ),
    "IMG24": (
        "Colour photograph, landscape. A smiling woman in a blue uniform and purple scarf"
        " stands to speak in a crowded classroom of pupils in blue uniforms, sitting at "
        "desks and looking up at her, beside barred windows in lime-green walls."
    ),
    "IMG25": (
        "Colour photograph, landscape. A Black woman in a black head wrap and a white lab"
        " coat sits at a desk with a large ledger, looking at a screen, in a laboratory "
        "where a man in a white coat works in the background."
    ),
    "IMG26": (
        "Colour photograph, landscape. A broadly smiling Black man in a yellow padded "
        "gilet over a green T-shirt stands with his hands in his pockets among banana "
        "plants, with sunlight shining through the leaves behind him."
    ),
    "IMG27": (
        "Colour photograph, landscape. A smiling Black man in a cap and green work coat "
        "stands with his arms folded in a food-processing room, where workers in blue "
        "coats, hairnets and face masks prepare vegetables at steel tables behind him."
    ),
    "IMG28": (
        "Colour photograph, landscape. A boy in a green knitted jumper and boots stands "
        "with his hands in his pockets on a heap of broken concrete and rubble in front "
        "of closed metal shop shutters, looking at the camera."
    ),
    "IMG29": (
        "Colour photograph, landscape. A smiling woman in a blue headscarf and a long "
        "checked dress stands in the open doorway of a metal-barred shopfront used as a "
        "home, with people sitting inside, shoes lined up on the pavement and red "
        "graffiti on the wall beside her."
    ),
    "IMG30": (
        "Colour photograph, portrait. A Black woman in a pink blouse, patterned skirt and"
        " white headscarf sits at a wooden table with a black sewing machine, holding "
        "fabric and looking out of a window, in a plain room with more sewing machines."
    ),
    "IMG31": (
        "Colour photograph, landscape. A Black woman in a white lace head wrap, a white "
        "shawl and a black-and-yellow dress laughs broadly, looking to the side, in front"
        " of an orange lattice brick wall."
    ),
    "IMG32": (
        "Colour photograph, landscape. A smiling Black woman in a green headscarf, "
        "printed white T-shirt and jeans holds illustrated booklets and hands them to "
        "people at the edge of the picture, on a red-earth yard in front of a brick "
        "building and trees."
    ),
    "IMG33": (
        "Colour photograph, landscape. A laughing Black woman in a striped top leans over"
        " a baby lying on a bed with a yellow cover, adjusting the baby's clothes, in a "
        "room with ochre walls."
    ),
    "IMG34": (
        "Colour photograph, portrait. A smiling Black man in a brown-and-white striped "
        "shirt stands in a storeroom stacked high with packs of bottled drinks and boxes "
        "of goods."
    ),
    "IMG35": (
        "Colour photograph, landscape. A Black man in a short-sleeved shirt and jeans "
        "sits in the doorway of an unfinished red-brick building, looking at the camera, "
        "with bare sandy ground and a pile of bricks in evening sun."
    ),
    "IMG36": (
        "Colour photograph, landscape. A smiling Black woman in a white gown with a blue-"
        "and-green patterned cloth over her lap sits on a metal-framed bed in a room with"
        " blue-and-cream walls, another person on a bed behind her."
    ),
    "IMG37": (
        "Colour photograph, landscape. A smiling Black man in a blue boiler suit with "
        "reflective stripes, a white hard hat and a yellow sun brim crouches handling "
        "orange-and-yellow safety netting; another worker on a phone stands behind him in"
        " an open site under a blue sky."
    ),
    "IMG38": (
        "Colour photograph, landscape. A barefoot, shirtless boy in jeans bends to fill a"
        " plastic bottle at a tap set in a concrete pillar beside green corrugated doors,"
        " in a street of brightly painted corrugated-iron houses; words are painted on "
        "the pillar."
    ),
    "IMG39": (
        "Colour photograph, portrait. A man in a T-shirt and a heavy black glove stirs a "
        "glowing pot of molten metal set in burning charcoal with a long metal rod, "
        "sparks flying, in a dark, cluttered workshop."
    ),
    "IMG40": (
        "Colour photograph, landscape. A Black man in a red T-shirt and black shorts "
        "stands resting his arm on a tall stack of shiny aluminium cooking pots, looking "
        "at the camera, in a yellow-walled storeroom full of more stacked pots."
    ),
    "IMG41": (
        "Colour photograph, portrait. A smiling Black man in a straw hat, black vest and "
        "jeans squats working a pair of leather bellows with two sticks, beside a heap of"
        " charcoal, under a shelter of tall reeds."
    ),
    "IMG42": (
        "Colour photograph, landscape. Schoolgirls in pale green uniforms with ties sit "
        "close together at a wooden desk writing in exercise books, one looking up "
        "towards the front, with younger children at a desk behind them against a bare "
        "wall."
    ),
    "IMG43": (
        "Colour photograph, landscape. A woman in a straw hat, blue top and patterned "
        "turquoise wrap skirt stands on a wide dirt road holding a small child in an "
        "orange dress on her hip, looking at the camera unsmiling."
    ),
    "IMG45": (
        "Colour photograph, square. A Black woman in a white tunic, a green patterned "
        "skirt and a matching head wrap stands unsmiling in a tiled room with metal beds "
        "under mosquito nets, a wheelchair and coloured bins along the wall."
    ),
    "IMG46": (
        "Colour photograph, landscape. A woman with braided hair, in a red vest top, "
        "carries a large yellow plastic water container on her shoulder, looking at the "
        "camera, on a dusty path among trees in low sun."
    ),
    "IMG47": (
        "Colour photograph, landscape. A laughing woman in a bright pink patterned dress "
        "sits against a green corrugated door between mud walls covered in climbing "
        "plants, drinking from a clear glass."
    ),
    "IMG48": (
        "Colour photograph, landscape. A smiling girl in a pink-and-green headscarf holds"
        " a large shiny metal water pot against her hip in front of a blue-tiled wall "
        "with taps and a small notice in a non-Latin script (not transcribed)."
    ),
    "IMG49": (
        "Colour photograph, landscape. A woman in a dark top and orange scarf carries a "
        "basin of earth on her head with both hands, walking along a path past a wooden "
        "fence, while a woman in a blue long draped garment stands behind her."
    ),
    "IMG50": (
        "Colour photograph, landscape. A Black woman in a black T-shirt fills a plastic "
        "drinks bottle at a tap on a tiled wall in bright sunshine, looking down at it; "
        "the bottle's red label and the lettering on her T-shirt and on the wall behind "
        "are partly hidden or cut off (not transcribed)."
    ),
    "IMG51": (
        "Colour photograph, landscape. A girl in a white headscarf and robe, with a "
        "patterned cloth on her head, carries a black plastic bucket on her head, "
        "steadying it with one hand, looking at the camera unsmiling, on a dry, dusty "
        "track with scrub behind."
    ),
    "IMG52": (
        "Colour photograph, portrait. A smiling woman in a blue shirt washes her soapy "
        "hands at a tap over a white concrete basin outside a yellow-painted building "
        "with a painted letter in a non-Latin script cut off at the edge."
    ),
    "IMG54": (
        "Colour photograph, landscape. A Black woman in a yellow T-shirt holds a baby "
        "wrapped in a green patterned cloth against her chest, looking at the camera "
        "unsmiling, in strong sunlight against a cream wall."
    ),
    "IMG56": (
        "Colour photograph, landscape. A smiling Black man in a brown jumper bends to "
        "fill a yellow plastic jerrycan at a tap inside a shelter of corrugated iron and "
        "wooden poles, with a blue drum beside him."
    ),
    "IMG57": (
        "Colour photograph, landscape. A woman in a long blue-and-white patterned dress "
        "stands on a wide expanse of dry, cracked earth with sparse scrub and trees "
        "behind, under a blue sky."
    ),
    "IMG58": (
        "Colour photograph, landscape. A smiling white woman in a pink headscarf and blue"
        " top holds up a small hand-woven rug with a red, green and black pattern, "
        "outside a house where another woman stands by a doorway beside a loom."
    ),
    "IMG59": (
        "Colour photograph, landscape. A smiling Black woman in a green head wrap and "
        "floral top sits behind a wooden table with a few round buns and banknotes on it,"
        " holding money, with long grass and trees behind her."
    ),
    "IMG60": (
        "Colour photograph, landscape. A Black woman in a headscarf, pink top and wrap "
        "skirt bends to dig with a long-handled hoe in a field of bean plants, with "
        "banana plants and trees behind under a cloudy sky."
    ),
    "IMG61": (
        "Colour photograph, landscape. A Black woman in a red head wrap and patterned "
        "dress sews blue fabric on a black treadle sewing machine, looking down at her "
        "work, in a workshop with more sewing machines."
    ),
    "IMG62": (
        "Colour photograph, landscape. A Black woman in an orange knitted hat and a grey "
        "sequinned top with a patterned shawl looks to one side, smiling slightly, in "
        "front of a breeze-block wall with leafy plants."
    ),
    "IMG63": (
        "Colour photograph, landscape. Two women in headscarves sit close together sewing"
        " and doing handwork; one, in a white headscarf, smiles as she embroiders white "
        "cloth, while the other works with yarn."
    ),
    "IMG64": (
        "Colour photograph, landscape. A smiling girl in a white headscarf and pale blue "
        "clothes sits cross-legged on a patterned mat with a notebook and pen, in a "
        "bright classroom where other children sit on the floor; a blue UNICEF sign with "
        "lines in a non-Latin script (not transcribed) and a hand-drawn poster hang on "
        "the wall behind."
    ),
    "IMG65": (
        "Colour photograph, landscape. A smiling girl in a yellow shirt stands at a "
        "blackboard, one hand raised with fingers spread and the other holding chalk to "
        "the board, which carries chalk algebra and handwritten lines of words in a "
        "language other than English, partly hidden by her; only the whole words that can"
        " be read are quoted in text_in_image."
    ),
    "IMG66": (
        "Colour photograph, landscape. A woman in an orange top and dark skirt waters "
        "rows of plants with a watering can, in a green field beneath a large tree, with "
        "hills behind."
    ),
    "IMG67": (
        "Colour photograph, landscape. A girl in a striped top and pink shorts stands "
        "thigh-deep in brown water, looking at the camera unsmiling, with thatched round "
        "huts, a boat and trees standing in the water behind her."
    ),
    "IMG68": (
        "Colour photograph, landscape. A Black woman with short hair looks up and away, "
        "unsmiling, in strong sunlight, in front of a stone building with blue-painted "
        "window frames."
    ),
    "IMG69": (
        "Colour photograph, portrait. A Black woman in a lilac head wrap and a bright "
        "blue-and-green patterned top leans over a blue-and-white checked table with "
        "trays of eggs and a cup, at a small roadside stall where another woman sits "
        "behind her."
    ),
    "IMG70": (
        "Colour photograph, portrait. A smiling Black woman in a yellow-and-blue "
        "patterned dress pounds food in a large wooden mortar with a tall pestle, at a "
        "busy market stall."
    ),
    "IMG71": (
        "Colour photograph, landscape. A shirtless man chops at a large dark log with a "
        "machete on a beach, with other men by painted wooden boats and buildings behind "
        "under a cloudy sky."
    ),
    "IMG72": (
        "Colour photograph, portrait. A smiling Black woman in a green uniform shirt and "
        "skirt with a red headband stands on a sandy path holding a tool over her "
        "shoulder and a shopping bag, in front of a low building among trees."
    ),
    "IMG73": (
        "Colour photograph, landscape. A smiling girl in a pink-and-blue floral outfit "
        "squats beside a red hand pump, filling a glass with water that runs from its "
        "spout, on a wet concrete floor against a stained yellow wall."
    ),
    "IMG74": (
        "Colour photograph, landscape. Close portrait of a woman in a black headscarf "
        "with red embroidered edging, looking straight at the camera unsmiling, in front "
        "of a shelter made of grey tarpaulin and wooden poles."
    ),
    "IMG75": (
        "Colour photograph, landscape. A woman in a red patterned outfit washes her soapy"
        " hands under a tap over a steel basin at a large metal hand-washing station with"
        " a yellow hand-washing sign, while women in long draped garments stand behind "
        "her."
    ),
    "IMG76": (
        "Colour photograph, landscape. A smiling Black woman in a striped headscarf and a"
        " blue work coat cuts long yellow bars of soap with a knife on a wooden bench, in"
        " a dim workshop with more bars stacked beside her."
    ),
    "IMG77": (
        "Colour photograph, landscape. A woman in a patterned headscarf and red top "
        "reaches up to a large hanging bag of mushroom-growing compost, among rows of "
        "such bags with mushrooms sprouting from them, in a dark room."
    ),
    "IMG78": (
        "Colour photograph, landscape. A broadly smiling boy in a green football shirt "
        "holds a red portable radio with an aerial against his ear, in front of a "
        "weathered blue wooden wall."
    ),
    "IMG80": (
        "Colour photograph, landscape. A girl with long fair hair, in a white T-shirt "
        "printed with pink flamingos and patterned shorts, stands unsmiling in a corridor"
        " with fallen ceiling panels, a toppled beam and rubble on the floor."
    ),
    "IMG81": (
        "Colour photograph, landscape. A smiling Black woman with long locs and glasses, "
        "in a striped top and black waistcoat, stands with her arms folded beside a "
        "dressmaker's dummy wearing a blue-and-white dress, in a bright room with net "
        "curtains."
    ),
    "IMG82": (
        "Colour photograph, portrait. A woman in a pink headscarf and patterned clothes "
        "waters a bed of green plants with a black watering can, in a garden in front of "
        "a single-storey house with a tin roof, under a blue sky."
    ),
    "IMG83": (
        "Colour photograph, portrait. A smiling woman in a purple headscarf, a dark "
        "spotted scarf and a dark tunic holds a tuft of white cotton in one hand, picking"
        " from cotton plants in a field."
    ),
    "IMG84": (
        "Colour photograph, portrait. A man in a white head cloth, a blue jacket and a "
        "dark jumper sits on a low wall in a sunny courtyard of whitewashed buildings, "
        "holding a cigarette, with washing hanging on lines above."
    ),
    "IMG85": (
        "Colour photograph, portrait. A smiling woman in a cream headscarf over a red cap"
        " and a pink overall writes in a large open book with a pen, against a plain grey"
        " wall."
    ),
    "IMG86": (
        "Colour photograph, landscape. A Black man sits on a donkey cart loaded with "
        "white plastic containers, holding one, as the donkey pulls it along a sandy "
        "track across dry, scrubby land with scattered trees."
    ),
    "IMG87": (
        "Colour photograph, landscape. A boy in a striped T-shirt holds a black umbrella "
        "and looks out over shelters with tarpaulin roofs on a hillside, with brown water"
        " spreading across the low ground and people wading in the distance."
    ),
    "IMG88": (
        "Colour photograph, landscape. A boy in a blue T-shirt and checked shorts stands "
        "ankle-deep in water in a street of corrugated-metal buildings, holding a paper "
        "and looking at the camera, with litter in the water and people walking behind."
    ),
    "IMG89": (
        "Colour photograph, landscape. A laughing boy in a blue school shirt leans out of"
        " a classroom window making a V sign with his fingers, with other children "
        "crowded behind him, in a yellow-and-blue painted wooden building."
    ),
    "IMG90": (
        "Colour photograph, landscape. A small fair-haired girl in a printed T-shirt and "
        "red leggings sits on the lower bunk of a bunk bed, looking at the camera "
        "unsmiling, against wallpaper printed with princesses."
    ),
    "IMG91": (
        "Colour photograph, landscape. A boy in a red shirt stands waist-deep in still "
        "water holding a yellow plastic container, looking at the camera unsmiling, "
        "beside half-submerged fences and belongings, with trees reflected in the water."
    ),
    "IMG92": (
        "Colour photograph, landscape. A woman in a grey knitted hat and black padded "
        "jacket, eyes nearly closed and mouth turned down, hugs a child in a pink hat "
        "close to her, by a road with an ambulance with flashing lights and people "
        "standing behind them."
    ),
    "IMG93": (
        "Colour photograph, landscape. A girl in a green patterned headscarf holds a "
        "small boy in a grey hooded top who hugs her, with her cheek against his head, in"
        " a room with red blankets."
    ),
    "IMG94": (
        "Colour photograph, landscape. A boy in a black hat and black jacket wheels a "
        "bicycle along a dirt road lined on both sides with heaps of broken building "
        "material."
    ),
    "IMG95": (
        "Colour photograph, landscape. A barefoot girl in an orange patterned dress "
        "carries a plastic jerrycan across red earth, behind her women in bright "
        "headscarves fill rows of yellow containers, with dome-shaped shelters of cloth "
        "and plastic behind."
    ),
    "IMG96": (
        "Colour photograph, landscape. A smiling boy in a red polo shirt stands under a "
        "white mosquito net, holding it up and spreading it out with both arms."
    ),
    "IMG97": (
        "Colour photograph, landscape. A boy in a dark fleece carries a stack of packets "
        "of nappies in his arms along a paved path, looking at the camera, with tents and"
        " people out of focus behind in evening light."
    ),
    "IMG98": (
        "Colour photograph, landscape. A girl in a red dress uses a long-handled shovel "
        "among blackened, smoking debris, with smoke filling the air and a crowd of "
        "people standing in the haze behind."
    ),
    "IMG99": (
        "Colour photograph, landscape. A smiling girl in a dark headscarf sits at a desk "
        "with an open book, in a classroom with a brightly painted landscape mural on the"
        " wall, with other girls in white headscarves beside her."
    ),
    "IMG100": (
        "Colour photograph, landscape. A smiling girl in a pink T-shirt and dark skirt "
        "fills a plastic water container from a hosepipe beside blue buckets and drums, "
        "in a shady yard under a large tree with people behind."
    ),
    "IMG101": (
        "Colour photograph, landscape. A man in a dark jacket over a patchwork jumper "
        "leans on a balcony rail, smiling slightly, above a large hall where families sit"
        " on mats and chairs among photographs on the walls."
    ),
    "IMG102_ps": (
        "Colour photograph, landscape. A smiling Black woman in a pink top stands in "
        "front of a blue-and-white painted building with a corrugated roof, in a sunny "
        "yard where a few people sit and stand in the shade."
    ),
    "IMG103": (
        "Colour photograph, landscape. A smiling girl with curly hair, in a leopard-print"
        " top, stands with her hands clasped in front of a row of large arched tents of "
        "blue and grey fabric on dusty ground."
    ),
    "IMG104": (
        "Colour photograph, landscape. A smiling woman with a brightly patterned shawl "
        "over her head stands beside a white signboard written in a non-Latin script (not"
        " transcribed), among trees."
    ),
    "IMG105": (
        "Colour photograph, landscape. Men fill large plastic water bottles from a green "
        "hose running from a tanker lorry; one man in a black jacket and cap holds the "
        "hose, another bends over a bottle, beside a grassy roadside; the tank is "
        "lettered, partly hidden by the man."
    ),
    "IMG106": (
        "Colour photograph, landscape. Close portrait of a boy in a light blue hooded top"
        " printed with a badge and lettering, looking at the camera unsmiling, in a "
        "narrow alley between concrete walls with painted writing in a non-Latin script "
        "(not transcribed)."
    ),
    "IMG107": (
        "Colour photograph, landscape. A boy in a black-and-red hooded top sits in a "
        "wheelchair in a narrow concrete alley, his leg in a white plaster cast resting "
        "on a board covered with a red cloth, with painted writing in a non-Latin script "
        "(not transcribed) on the wall."
    ),
    "IMG108": (
        "Colour photograph, landscape. A smiling boy in a checked shirt stands with his "
        "arms folded in a muddy lane between shelters of bamboo, brick and tarpaulin, "
        "under a grey sky."
    ),
    "IMG110": (
        "Colour photograph, landscape. A smiling boy with tousled dark hair, in a striped"
        " knitted jumper, stands close to the camera among white tents on bare, muddy "
        "ground under a white sky."
    ),
    "IMG111": (
        "Colour photograph, landscape. A smiling girl in a pale blue T-shirt looks back "
        "over her shoulder at the camera, sitting on metal waiting-room seats with "
        "another girl beside her."
    ),
    "IMG112": (
        "Colour photograph, landscape. A bearded man in a pink shirt sits on the edge of "
        "a bed with a red floral cover, looking at the camera unsmiling, in a bare room "
        "with grey concrete walls."
    ),
    "IMG113": (
        "Colour photograph, landscape. A boy in a blue football kit lies propped on a bed"
        " with floral covers, a bandage on his ankle and a dressing on his knee, looking "
        "at the camera unsmiling, against a stained concrete wall."
    ),
    "IMG114": (
        "Colour photograph, portrait. A smiling boy in a blue shirt writes with a pencil "
        "at a wooden desk with a textbook and papers, in a crowded classroom of children "
        "at desks, with colourful pictures on the walls."
    ),
    "IMG115": (
        "Colour photograph, landscape. A bearded man in a white cap and white clothes "
        "squats among heaps of mud bricks and broken timbers, his hand to his forehead, "
        "beside plastic buckets."
    ),
    "IMG116": (
        "Colour photograph, square. A girl in a red patterned dress and a pink-and-white "
        "shawl over her head stands unsmiling among heaps of mud bricks, timbers and "
        "pipes."
    ),
    "IMG118": (
        "Colour photograph, landscape. A laughing small girl with fair curly hair, in a "
        "patterned top and bead necklace, puts her fingers to her mouth, beside a hut "
        "with a thatched roof among green trees."
    ),
    "IMG119": (
        "Colour photograph, landscape. A girl with long fair hair and glasses, in a white"
        " blouse embroidered in blue, sits at a desk in an empty classroom with green "
        "blackboards and above them a painted line of writing in Cyrillic script, partly "
        "hidden by a small blue-and-yellow flag."
    ),
    "IMG120": (
        "Colour photograph, portrait. A woman with short dark hair in a black T-shirt "
        "printed with a cat stands with her hands behind her back, unsmiling, in front of"
        " a heap of broken concrete, with red-and-white tape stretched across behind her."
    ),
    "IMG121": (
        "Colour photograph, landscape. A smiling boy in a dark checked shirt stands "
        "beside a concrete water tank with bowls and a purple bucket on it, in a yard of "
        "corrugated-iron walls with clothes hanging up."
    ),
    "IMG122": (
        "Colour photograph, landscape. A small boy with pale paste on his cheeks, in a "
        "yellow T-shirt, sits holding a blue cup beside a large water dispenser bottle, "
        "with a smiling woman holding a baby sitting behind him, outdoors among houses."
    ),
    "IMG123": (
        "Colour photograph, landscape. A group of women in colourful headscarves and long"
        " draped garments and a man in a cap gather in front of a doorway, looking "
        "towards someone out of the picture, none smiling; a man's face is close in the "
        "foreground, out of focus."
    ),
    "IMG125": (
        "Colour photograph, portrait. A man in a grey turban and grey clothes crouches in"
        " a field of plants, scattering white granules by hand from a green sack, under a"
        " pale sky."
    ),
    "IMG126": (
        "Colour photograph, landscape. Two white women in dark coats sit close together "
        "at a table with paper cups and a flask under a large white marquee, one in a "
        "patterned headscarf looking at the camera, the other leaning towards her with "
        "eyes lowered."
    ),
    "IMG127": (
        "Colour photograph, landscape. A woman in a black headscarf and brown cardigan "
        "sits cross-legged on a blanket on the ground in front of a white canvas tent, "
        "with a walking stick beside her, looking at the camera."
    ),
    "photo1": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt stands facing the "
        "camera and smiles broadly, against a rough wall of brown stone blocks."
    ),
    "photo2": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt stands smiling and"
        " looking off to one side, against a rough wall of brown stone blocks."
    ),
    "photo3": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt and green-and-"
        "white shorts rides a bicycle past a rough wall of brown stone blocks, smiling at"
        " the camera."
    ),
    "photo4": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt and green-and-"
        "white shorts rides a bicycle past a rough wall of brown stone blocks, smiling "
        "and looking ahead, away from the camera."
    ),
    "photo5": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt stands with his "
        "arms folded, looking at the camera unsmiling, against a rough wall of brown "
        "stone blocks."
    ),
    "photo6": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt stands with his "
        "arms folded, unsmiling and looking off to one side, against a rough wall of "
        "brown stone blocks."
    ),
    "photo7": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt and green-and-"
        "white shorts sits on a bicycle, looking at the camera unsmiling, on a dirt yard "
        "where children play and people walk behind him."
    ),
    "photo8": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt and green-and-"
        "white shorts rides a bicycle past a rough wall of brown stone blocks, unsmiling "
        "and looking ahead, away from the camera."
    ),
    "photo9": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt stands facing the "
        "camera, unsmiling, against a rough wall of brown stone blocks."
    ),
    "photo10": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt stands unsmiling, "
        "looking off to one side, against a rough wall of brown stone blocks."
    ),
    "photo11": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt and green-and-"
        "white shorts rides a bicycle past a rough wall of brown stone blocks, looking at"
        " the camera unsmiling."
    ),
    "photo12": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt and green-and-"
        "white shorts rides a bicycle past a rough wall of brown stone blocks, unsmiling "
        "and looking ahead, away from the camera."
    ),
    "photo13": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt stands with his "
        "arms folded, looking at the camera unsmiling, on a dirt yard where children and "
        "adults walk past low buildings of corrugated metal and mud."
    ),
    "photo14": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt stands unsmiling, "
        "looking off to one side, on a dirt yard where children run and play in front of "
        "low buildings of corrugated metal and mud."
    ),
    "photo15": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt and green-and-"
        "white tracksuit trousers sits astride a bicycle on a bare earth slope, looking "
        "at the camera unsmiling."
    ),
    "photo16": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt and green-and-"
        "white shorts rides a bicycle past a rough wall of brown stone blocks, unsmiling "
        "and looking ahead, away from the camera."
    ),
    "photo17": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt stands facing the "
        "camera and smiles broadly, against a wall of rusty, patched corrugated iron."
    ),
    "photo18": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt stands smiling and"
        " looking off to one side, against a wall of rusty, patched corrugated iron."
    ),
    "photo19": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt and green "
        "tracksuit trousers sits astride a bicycle among rocks in front of a wall of "
        "rusty corrugated iron, smiling broadly at the camera."
    ),
    "photo20": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt and green "
        "tracksuit trousers sits astride a bicycle among rocks in front of a wall of "
        "rusty corrugated iron, smiling and looking off to one side."
    ),
    "photo21": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt stands with his "
        "arms folded, looking at the camera unsmiling, against a wall of rusty, patched "
        "corrugated iron."
    ),
    "photo22": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt stands with his "
        "arms folded, unsmiling and looking off to one side, against a wall of rusty, "
        "patched corrugated iron."
    ),
    "photo23": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt and green "
        "tracksuit trousers sits astride a bicycle on rough ground among rocks in front "
        "of a wall of rusty corrugated iron, looking at the camera unsmiling."
    ),
    "photo24": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt and green "
        "tracksuit trousers sits astride a bicycle among rocks in front of a wall of "
        "rusty corrugated iron, unsmiling and looking off to one side."
    ),
    "photo25": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt stands facing the "
        "camera, unsmiling, against a wall of rusty, patched corrugated iron."
    ),
    "photo26": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt stands unsmiling, "
        "looking off to one side, against a wall of rusty, patched corrugated iron."
    ),
    "photo27": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt and green "
        "tracksuit trousers sits astride a bicycle among rocks in front of a wall of "
        "rusty corrugated iron, looking at the camera unsmiling."
    ),
    "photo28": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt and green "
        "tracksuit trousers sits astride a bicycle among rocks in front of a wall of "
        "rusty corrugated iron, unsmiling and looking off to one side."
    ),
    "photo29": (
        "Colour photograph, landscape. Close portrait of a Black boy in a red sweatshirt "
        "facing the camera, unsmiling, against a wall of rusty, patched corrugated iron."
    ),
    "photo30": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt stands unsmiling, "
        "looking off to one side, against a wall of rusty, patched corrugated iron."
    ),
    "photo31": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt and green "
        "tracksuit trousers sits astride a bicycle among rocks in front of a wall of "
        "rusty corrugated iron, looking at the camera unsmiling."
    ),
    "photo32": (
        "Colour photograph, landscape. A Black boy in a red sweatshirt and green "
        "tracksuit trousers sits astride a bicycle among rocks in front of a wall of "
        "rusty corrugated iron, unsmiling and looking off to one side."
    ),
    "photo33": (
        "Colour photograph, landscape. A smiling Black man in a light blue shirt stands "
        "with his arms folded, looking at the camera, against a mud wall with its plaster"
        " broken away with the wooden sticks of its frame showing through and faint "
        "scratched writing."
    ),
    "photo34": (
        "Colour photograph, landscape. A smiling Black man in a light blue shirt stands "
        "with his arms folded, looking off to one side, against a wall of grey concrete "
        "blocks."
    ),
    "photo35": (
        "Colour photograph, landscape. A smiling Black man in a blue shirt rides a green "
        "bicycle along a busy, sunny street of small shops and stalls, looking back at "
        "the camera, with people walking behind."
    ),
    "photo36": (
        "Colour photograph, landscape. A smiling Black man in a blue shirt rides a green "
        "bicycle along a busy, sunny street of small shops and stalls, looking ahead, "
        "away from the camera."
    ),
    "photo37": (
        "Colour photograph, landscape. A Black man in a light blue shirt stands with his "
        "arms folded, looking at the camera unsmiling, against a mud wall with its "
        "plaster broken away with the wooden sticks of its frame showing through and "
        "faint scratched writing."
    ),
    "photo38": (
        "Colour photograph, landscape. A Black man in a light blue shirt stands "
        "unsmiling, looking off to one side, against a mud wall with its plaster broken "
        "away with the wooden sticks of its frame showing through and faint scratched "
        "writing."
    ),
    "photo39": (
        "Colour photograph, landscape. A Black man in a blue shirt stands holding a "
        "bicycle by its handlebar on a busy dirt street, looking back at the camera "
        "unsmiling, with people walking and a blue building behind."
    ),
    "photo40": (
        "Colour photograph, landscape. A Black man in a blue shirt stands holding a "
        "bicycle by its handlebar on a busy dirt street, unsmiling and looking off to one"
        " side, with people walking and a blue building behind."
    ),
    "photo41": (
        "Colour photograph, landscape. A Black man in a light blue shirt stands with his "
        "arms folded, looking at the camera unsmiling, against a mud wall with its "
        "plaster broken away with the wooden sticks of its frame showing through and "
        "faint scratched writing."
    ),
    "photo42": (
        "Colour photograph, landscape. A Black man in a light blue shirt stands "
        "unsmiling, looking off to one side, against a wall of rusty corrugated iron with"
        " chalk marks."
    ),
    "photo43": (
        "Colour photograph, landscape. A Black man in a blue shirt stands holding a "
        "bicycle by its handlebar on a dirt street, looking back at the camera unsmiling,"
        " with people walking and a blue building behind."
    ),
    "photo44": (
        "Colour photograph, landscape. A Black man in a blue shirt sits on a bicycle on a"
        " dirt yard, unsmiling and looking off to one side, with clothes hanging for sale"
        " at stalls behind him."
    ),
    "photo45": (
        "Colour photograph, landscape. A Black man in a light blue shirt stands with his "
        "arms folded, looking at the camera unsmiling, against a mud wall with its "
        "plaster broken away with the wooden sticks of its frame showing through and "
        "faint scratched writing."
    ),
    "photo46": (
        "Colour photograph, landscape. A Black man in a light blue shirt stands with his "
        "arms folded, unsmiling and looking off to one side, against a wall of rusty "
        "corrugated iron with chalk marks."
    ),
    "photo47": (
        "Colour photograph, landscape. A Black man in a blue shirt rides a green bicycle "
        "along a busy, sunny street of small shops and stalls, looking back at the camera"
        " unsmiling."
    ),
    "photo48": (
        "Colour photograph, landscape. A Black man in a blue shirt rides a green bicycle "
        "along a busy, sunny street of small shops and stalls, unsmiling and looking off "
        "to one side."
    ),
    "photo49": (
        "Colour photograph, landscape. A smiling Black man in a light blue shirt stands "
        "facing the camera with his hands clasped in front of him, against an old wooden "
        "door and rusty metal sheets."
    ),
    "photo50": (
        "Colour photograph, landscape. A smiling Black man in a light blue shirt stands "
        "looking off to one side, against an old wooden door and rusty metal sheets."
    ),
    "photo51": (
        "Colour photograph, landscape. A smiling Black man in a light blue shirt sits "
        "astride a bicycle on bare red earth, looking at the camera, with low buildings "
        "of corrugated metal, litter and electricity poles behind him under a grey sky."
    ),
    "photo52": (
        "Colour photograph, landscape. A smiling Black man in a light blue shirt sits "
        "astride a bicycle on bare red earth, looking off to one side, with low buildings"
        " of corrugated metal, litter and electricity poles behind him under a grey sky."
    ),
    "photo53": (
        "Colour photograph, landscape. A Black man in a light blue shirt stands facing "
        "the camera, unsmiling, against an old wooden door and rusty metal sheets."
    ),
    "photo54": (
        "Colour photograph, landscape. A Black man in a light blue shirt stands "
        "unsmiling, looking off to one side, against an old wooden door and rusty metal "
        "sheets."
    ),
    "photo55": (
        "Colour photograph, landscape. A Black man in a light blue shirt sits astride a "
        "bicycle on bare red earth, looking at the camera unsmiling, with low buildings "
        "of corrugated metal, litter and electricity poles behind him under a grey sky."
    ),
    "photo56": (
        "Colour photograph, landscape. A Black man in a light blue shirt sits astride a "
        "bicycle on bare red earth, unsmiling and looking off to one side, with low "
        "buildings of corrugated metal, litter and electricity poles behind him under a "
        "grey sky."
    ),
    "photo57": (
        "Colour photograph, landscape. A Black man in a light blue shirt stands facing "
        "the camera unsmiling, against an old wooden door and rusty metal sheets."
    ),
    "photo58": (
        "Colour photograph, landscape. A Black man in a light blue shirt stands with his "
        "hands clasped in front of him, head lowered and unsmiling, against an old wooden"
        " door and rusty metal sheets."
    ),
    "photo59": (
        "Colour photograph, landscape. A Black man in a light blue shirt sits astride a "
        "bicycle on bare red earth, looking at the camera, unsmiling, with litter and "
        "electricity poles behind him under a grey sky."
    ),
    "photo60": (
        "Colour photograph, landscape. A Black man in a light blue shirt sits astride a "
        "bicycle on bare red earth, unsmiling and looking off to one side, with litter "
        "and electricity poles behind him under a grey sky."
    ),
    "photo61": (
        "Colour photograph, landscape. A Black man in a light blue shirt stands with his "
        "hands clasped in front of him, looking at the camera, unsmiling, against an old "
        "wooden door and rusty metal sheets."
    ),
    "photo62": (
        "Colour photograph, landscape. A Black man in a light blue shirt stands "
        "unsmiling, looking off to one side, against an old wooden door and rusty metal "
        "sheets."
    ),
    "photo63": (
        "Colour photograph, landscape. A Black man in a light blue shirt sits astride a "
        "bicycle on bare red earth, looking at the camera, unsmiling, with litter and "
        "electricity poles behind him under a grey sky."
    ),
    "photo64": (
        "Colour photograph, landscape. A Black man in a light blue shirt sits astride a "
        "bicycle on bare red earth, unsmiling and looking off to one side, with litter "
        "and electricity poles behind him under a grey sky."
    ),
    "photo65": (
        "Colour photograph, landscape. A Black girl with short hair, in a grey printed "
        "T-shirt, stands facing the camera and smiles broadly, in front of a grassy, "
        "overgrown bank."
    ),
    "photo66": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt stands with"
        " her arms folded, smiling and looking off to one side, on a grassy slope with a "
        "concrete footbridge over a ditch behind her."
    ),
    "photo67": (
        "Colour photograph, landscape. A smiling Black girl in a grey printed T-shirt "
        "carries a pink bucket on her head with both hands, looking at the camera, in a "
        "yard with coloured plastic basins, a red chair and a building with mud walls and"
        " wooden poles."
    ),
    "photo68": (
        "Colour photograph, landscape. A smiling Black girl in a grey printed T-shirt "
        "carries a pink bucket on her head with both hands, looking off to one side, in a"
        " yard with coloured plastic basins, a red chair and a building with mud walls "
        "and wooden poles."
    ),
    "photo69": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt stands with"
        " her arms folded, smiling slightly at the camera, in front of a grassy, "
        "overgrown bank."
    ),
    "photo70": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt stands with"
        " her arms folded, smiling slightly and looking off to one side, in front of a "
        "grassy, overgrown bank."
    ),
    "photo71": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt carries a "
        "pink bucket on her head with both hands, looking at the camera with a slight "
        "smile, in a yard with coloured plastic basins, a red chair and a building with "
        "mud walls and wooden poles."
    ),
    "photo72": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt carries a "
        "pink bucket on her head with both hands, smiling slightly and looking off to one"
        " side, in a yard with coloured plastic basins, a red chair and a building with "
        "mud walls and wooden poles."
    ),
    "photo73": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt stands with"
        " her hands clasped in front of her, looking at the camera unsmiling, in front of"
        " a grassy, overgrown bank."
    ),
    "photo74": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt stands with"
        " her hands clasped in front of her, unsmiling and looking off to one side, in "
        "front of a grassy, overgrown bank."
    ),
    "photo75": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt carries a "
        "pink bucket on her head with both hands, looking at the camera unsmiling, in a "
        "yard with coloured plastic basins, a red chair and a building with mud walls and"
        " wooden poles, with people behind."
    ),
    "photo76": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt carries a "
        "pink bucket on her head with both hands, unsmiling and looking off to one side, "
        "in a yard with coloured plastic basins, a red chair and a building with mud "
        "walls and wooden poles."
    ),
    "photo77": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt stands with"
        " her arms folded, looking at the camera unsmiling, on a grassy slope with a "
        "concrete footbridge over a ditch behind her."
    ),
    "photo78": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt stands with"
        " her arms folded, unsmiling and looking off to one side, on a grassy slope with "
        "a concrete footbridge over a ditch behind her."
    ),
    "photo79": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt carries a "
        "pink bucket on her head with both hands, looking at the camera unsmiling, in a "
        "yard with coloured plastic basins, a red chair and a building with mud walls and"
        " wooden poles."
    ),
    "photo80": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt carries a "
        "pink bucket on her head with both hands, unsmiling and looking off to one side, "
        "in a yard with coloured plastic basins, a red chair and a building with mud "
        "walls and wooden poles, with people behind."
    ),
    "photo81": (
        "Colour photograph, landscape. A smiling Black girl in a grey printed T-shirt "
        "stands with her hands clasped in front of her, looking at the camera, between "
        "walls of mud, sticks and rusty corrugated iron."
    ),
    "photo82": (
        "Colour photograph, landscape. A smiling Black girl in a grey printed T-shirt "
        "stands with her hands clasped in front of her, looking off to one side, between "
        "walls of mud, sticks and rusty corrugated iron."
    ),
    "photo83": (
        "Colour photograph, landscape. A smiling Black girl in a grey printed T-shirt "
        "carries a pink bucket on her head with both hands, looking at the camera, "
        "between walls of mud, sticks and rusty corrugated iron."
    ),
    "photo84": (
        "Colour photograph, landscape. A smiling Black girl in a grey printed T-shirt "
        "carries a pink bucket on her head with both hands, looking off to one side, "
        "between walls of mud, sticks and rusty corrugated iron."
    ),
    "photo85": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt stands with"
        " her hands clasped in front of her, smiling slightly at the camera, between "
        "walls of mud, sticks and rusty corrugated iron."
    ),
    "photo86": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt stands with"
        " her arms folded, unsmiling and looking off to one side, between walls of mud, "
        "sticks and rusty corrugated iron."
    ),
    "photo87": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt carries a "
        "pink bucket on her head with both hands, looking at the camera unsmiling, "
        "between walls of mud, sticks and rusty corrugated iron."
    ),
    "photo88": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt carries a "
        "pink bucket on her head with both hands, unsmiling and looking off to one side, "
        "between walls of mud, sticks and rusty corrugated iron."
    ),
    "photo89": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt stands with"
        " her hands clasped in front of her, looking at the camera unsmiling, between "
        "walls of mud, sticks and rusty corrugated iron."
    ),
    "photo90": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt stands with"
        " her hands clasped in front of her, unsmiling and looking off to one side, "
        "between walls of mud, sticks and rusty corrugated iron."
    ),
    "photo91": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt carries a "
        "pink bucket on her head with both hands, looking at the camera unsmiling, "
        "between walls of mud, sticks and rusty corrugated iron."
    ),
    "photo92": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt carries a "
        "pink bucket on her head with both hands, unsmiling and looking off to one side, "
        "between walls of mud, sticks and rusty corrugated iron."
    ),
    "photo93": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt stands with"
        " her hands clasped in front of her, looking at the camera unsmiling, between "
        "walls of mud, sticks and rusty corrugated iron."
    ),
    "photo94": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt stands with"
        " her hands clasped in front of her, unsmiling and looking off to one side, "
        "between walls of mud, sticks and rusty corrugated iron."
    ),
    "photo95": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt carries a "
        "pink bucket on her head with both hands, looking at the camera unsmiling, "
        "between walls of mud, sticks and rusty corrugated iron."
    ),
    "photo96": (
        "Colour photograph, landscape. A Black girl in a grey printed T-shirt carries a "
        "pink bucket on her head with both hands, unsmiling and looking off to one side, "
        "between walls of mud, sticks and rusty corrugated iron."
    ),
    "photo97": (
        "Colour photograph, landscape. A smiling Black woman in a lilac polo-neck jumper "
        "stands with her hands clasped in front of her, looking at the camera, in front "
        "of a two-storey brick block of flats with balconies and washing."
    ),
    "photo98": (
        "Colour photograph, landscape. A smiling Black woman in a lilac polo-neck jumper "
        "stands with her hands clasped in front of her, looking off to one side, in front"
        " of a two-storey brick block of flats with balconies and washing."
    ),
    "photo99": (
        "Colour photograph, landscape. A smiling Black woman in a lilac polo-neck jumper "
        "carries a red bucket on her head, steadying it with one hand, looking at the "
        "camera, on a bare earth slope in front of a block of buildings and a tree."
    ),
    "photo100": (
        "Colour photograph, landscape. A smiling Black woman in a lilac polo-neck jumper "
        "carries a red bucket on her head, steadying it with one hand, looking down and "
        "to one side, on a bare earth slope in front of a block of buildings and a tree."
    ),
    "photo101": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper stands "
        "with her hands clasped in front of her, looking at the camera with a slight "
        "smile, in front of a two-storey brick block of flats with balconies."
    ),
    "photo102": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper stands "
        "with her hands clasped in front of her, unsmiling and looking off to one side, "
        "in front of a two-storey brick block of flats with balconies."
    ),
    "photo103": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper carries "
        "a red bucket on her head, steadying it with one hand, looking at the camera "
        "unsmiling, on a bare earth slope in front of a block of buildings and a tree."
    ),
    "photo104": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper carries "
        "a red bucket on her head, steadying it with one hand, unsmiling and looking off "
        "to one side, on a bare earth slope in front of a block of buildings."
    ),
    "photo105": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper stands "
        "with her hands clasped in front of her, looking at the camera unsmiling, against"
        " a wall of rough grey stones."
    ),
    "photo106": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper stands "
        "unsmiling, looking off to one side, against a cracked mud wall."
    ),
    "photo107": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper and dark"
        " skirt carries a red bucket on her head, steadying it with one hand, looking at "
        "the camera unsmiling, on a wide bare earth slope with buildings and a few people"
        " behind."
    ),
    "photo108": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper carries "
        "a red bucket on her head, steadying it with one hand, looking at the camera, "
        "unsmiling, on a bare earth slope in front of a block of buildings and a tree."
    ),
    "photo109": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper stands "
        "unsmiling, looking at the camera, in front of a two-storey brick block of flats "
        "with balconies."
    ),
    "photo110": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper stands "
        "unsmiling, looking off to one side, in front of a two-storey brick block of "
        "flats with balconies and washing."
    ),
    "photo111": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper carries "
        "a red bucket on her head, steadying it with one hand, looking at the camera, "
        "unsmiling, on a bare earth slope in front of buildings and a tree."
    ),
    "photo112": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper carries "
        "a red bucket on her head, steadying it with one hand, unsmiling, on a bare earth"
        " slope in front of a block of buildings and a tree."
    ),
    "photo113": (
        "Colour photograph, landscape. A smiling Black woman in a lilac polo-neck jumper "
        "stands with her hands clasped in front of her, looking at the camera, against a "
        "wall of rusty corrugated iron."
    ),
    "photo114": (
        "Colour photograph, landscape. A smiling Black woman in a lilac polo-neck jumper "
        "stands with her hands clasped in front of her, looking at the camera, against a "
        "wall of rusty corrugated iron."
    ),
    "photo115": (
        "Colour photograph, landscape. A broadly smiling Black woman in a lilac polo-neck"
        " jumper carries a red bucket on her head, steadying it with one hand, looking at"
        " the camera, on a bare earth slope in front of a block of buildings and a tree."
    ),
    "photo116": (
        "Colour photograph, landscape. A broadly smiling Black woman in a lilac polo-neck"
        " jumper carries a red bucket on her head, steadying it with one hand, looking "
        "down and to one side, on a bare earth slope in front of a block of buildings and"
        " a tree."
    ),
    "photo117": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper stands "
        "with her hands behind her back, looking at the camera with a slight smile, "
        "against a wall of rusty corrugated iron."
    ),
    "photo118": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper stands "
        "with her arms folded, unsmiling and looking off to one side, against a wall of "
        "rusty corrugated iron."
    ),
    "photo119": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper carries "
        "a red bucket on her head, steadying it with one hand, looking at the camera "
        "unsmiling, on a bare earth slope in front of a block of buildings and a tree."
    ),
    "photo120": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper carries "
        "a red bucket on her head, steadying it with one hand, unsmiling and looking off "
        "to one side, on a bare earth slope in front of a block of buildings."
    ),
    "photo121": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper stands "
        "with her hands clasped against her waist, looking at the camera, unsmiling, "
        "against a wall of rusty corrugated iron."
    ),
    "photo122": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper stands "
        "with her hands clasped against her waist, unsmiling and looking off to one side,"
        " against a wall of rusty corrugated iron."
    ),
    "photo124": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper carries "
        "a red bucket on her head, steadying it with one hand, unsmiling and looking off "
        "to one side, on a bare earth slope in front of a block of buildings and a tree."
    ),
    "photo125": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper and "
        "purple skirt stands with her arms by her sides, looking at the camera, "
        "unsmiling, against a wall of rusty corrugated iron."
    ),
    "photo126": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper and "
        "purple skirt stands unsmiling, looking off to one side, against a wall of rusty "
        "corrugated iron."
    ),
    "photo127": (
        "Colour photograph, landscape. A Black woman in a lilac polo-neck jumper carries "
        "a red bucket on her head, steadying it with one hand, looking at the camera, "
        "unsmiling, on a bare earth slope in front of a block of buildings and a tree."
    ),
}


def catalogue_entries() -> dict[str, dict[str, str]]:
    from micromotives_datasets.images import sha256_of

    df = _read_sav()
    where = shown(df)
    out: dict[str, dict[str, str]] = {}
    for name, names in pictures(df):
        s, url = where[name]
        f = file_of(name, url)
        cols = " and ".join(f"`{n}` ({where[n][1]})" for n in names)
        same = " (byte-identical files, one picture)" if len(names) > 1 else ""
        out[image_id(name)] = {
            "file": f,
            "sha256": sha256_of(REPO / "data" / f),
            "source": f"DEL Sandbox Oct 2023, doi:10.7910/DVN/XZ1XUZ, "
            f"DEL_Sandbox_GreatBritain_Oct2023_Data.sav: {SETS[s]} folder, column "
            f"{cols}{same}; shown in `image{{k}}_url` when `image{{k}}_name` is that name",
            "licence": LICENCE,
            "text_in_image": TEXT_IN_IMAGE.get(name, ""),
            "description": DESCRIPTIONS[name],
        }
    return out


def write_catalogue() -> None:
    """Add or refresh only this study's entries; re-read first, others are editing too."""
    path = REPO / "data" / "catalog" / "images.json"
    current = json.loads(path.read_text())
    current.update(catalogue_entries())
    path.write_text(json.dumps(current, indent=2, ensure_ascii=False))


# --- the instrument ----------------------------------------------------------------


def _typography(text: str) -> str:
    """Straight quotes, no bold markup, single spaces. Words untouched."""
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("**", "")
    # Inline emphasis in the script's question text: <<b>...</b>>, <<strong>...</strong>>.
    text = re.sub(r"<<(?:b|strong)>(.*?)</(?:b|strong)>>", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def survey_text() -> str:
    """The questionnaire's paragraphs, typography normalised."""
    xml = zipfile.ZipFile(SURVEY).read("word/document.xml").decode()
    paras = [
        html.unescape("".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", p)))
        for p in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S)
    ]
    return "\n".join(_typography(p) for p in paras)


INTRO = (
    "In the following pages you will see a series of five images that international "
    "development charities/NGOs might use as part of their appeals to inspire action "
    "against global poverty. Please answer the following questions about the images you "
    "have been shown."
)
# The introduction's appeal framing, quoted inside our own sentence (see notes).
APPEAL = (
    "international development charities/NGOs might use as part of their appeals to "
    "inspire action against global poverty."
)
assert APPEAL in INTRO
SHARED = f'You were told the images were ones that "{APPEAL}"'
ARM_TEXT = "This image was shown above each question: <image>"

EMOTION_STEM = (
    "Looking at the image above, using the scale where 1 means 'Not at all' and 5 means "
    "'A great deal', please tell us the extent to which you feel the following emotions."
)
EMOTIONS = [
    "Happy, excited, alert, elated",
    "Calm, relaxed, serene, content",
    "Tired, bored, depressed, sad",
    "Upset, stressed, uncomfortable, anxious",
]
URGENCY = (
    "Thinking about the image above, using the scale below where 1 means 'Not at all "
    "urgent' and 5 means 'Very urgent' please tell us, in your opinion, how urgent is the "
    "situation shown in the image?"
)
EFFICACY = (
    "Thinking about the image above, where 1 means 'No difference at all' and 5 means 'A "
    "great deal of difference', how much of a difference do you think you can make to the "
    "lives of the people shown in the image?"
)
GETINFO = (
    "Imagine you saw the image above in an appeal from an international development "
    "charity/NGO. Based on this image, would you want to find out more about the appeal "
    "(e.g., by clicking a link to a website where you can find out more information about "
    "the appeal, or signing up to the organisation's mailing list)?"
)
GETINFO_OPTIONS = [
    "Yes, I want to find out more about the appeal",
    "No, I do not want to find out more about the appeal",
]
DONATE = (
    "Imagine you saw the image in an appeal from an international development "
    "charity/NGO. Based on the image, would you want to donate to the appeal?"
)
DONATE_OPTIONS = ["Yes, I want to donate to the appeal", "No, I don't want to donate to the appeal"]
AMOUNT = "You said you would donate to the appeal above. How much would you donate?"
AMOUNT_ADDED = ' The answer box had "£" before it.'
IMPACT_YES = (
    "You said you would donate to the appeal above. To what extent do you think your "
    "donation would impact the lives of the people you see in the image?"
)
IMPACT_NO = (
    "You said you would not donate to the appeal above. To what extent do you think a "
    "donation would impact the lives of the people you see in the image?"
)
IMPACT_MIN = "It wouldn't impact their lives at all"
IMPACT_MAX = "It would have a very positive impact on their lives"
AMOUNT_MAX = 9999
# One object each, so the YAML writes each map once and aliases the rest.
AMOUNT_RECODE = {v: v for v in range(1, AMOUNT_MAX + 1)}
IMPACT_RECODE = {v: v for v in range(11)}
YES_NO_RECODE = {1: 1, 2: 2}

# Every string above that claims to be the instrument's, as it must appear in it.
FROM_INSTRUMENT = [
    INTRO,
    EMOTION_STEM,
    *EMOTIONS,
    URGENCY,
    EFFICACY,
    GETINFO,
    *GETINFO_OPTIONS,
    DONATE,
    *DONATE_OPTIONS,
    AMOUNT,
    IMPACT_YES,
    IMPACT_NO,
    f"0 - {IMPACT_MIN}",
    f"10 - {IMPACT_MAX}",
    "<1> 1 - Not at all",
    "<5> 5 - A great deal",
    "<1> 1 - Not at all urgent",
    "<5> 5 - Very urgent",
    "<1> 1 - No difference at all",
    "<5> 5 - A great deal of difference",
    '{open-intrange 1 9999 left="£"}',
]


PER_SLOT = [
    EMOTION_STEM,
    *EMOTIONS,
    URGENCY,
    EFFICACY,
    GETINFO,
    DONATE,
    AMOUNT,
    IMPACT_YES,
    IMPACT_NO,
]


def check_wording(text: str | None = None) -> None:
    """Each instrument string is in the questionnaire; each per-slot one in all five slots."""
    text = (survey_text() if text is None else text).replace("–", "-")
    missing = [s for s in FROM_INSTRUMENT if s not in text]
    if missing:
        raise SystemExit(f"not in the questionnaire: {missing}")
    uneven = {s: text.count(s) for s in PER_SLOT if text.count(s) != len(SLOTS)}
    if uneven:
        raise SystemExit(f"not worded the same in all five slots: {uneven}")


def options(labels: list[str]) -> str:
    return " " + "; ".join(f'{i} means "{lab}"' for i, lab in enumerate(labels, start=1)) + "."


def _five(lo: str, hi: str) -> dict[str, Any]:
    return {"min": 1, "max": 5, "min_label": lo, "max_label": hi}


def slot_items(s: str) -> list[tuple[str, str, dict[str, Any], dict[int, int] | None]]:
    """(variable, question, scale, own recode) for one slot, in the instrument's order."""
    y, n = ("ey", "en") if s == "e" else ("dy", "dn")
    yes_no = YES_NO_RECODE
    return [
        *[
            (
                f"p_medemot_{s}{i}",
                f'{EMOTION_STEM} "{e}"',
                _five("Not at all", "A great deal"),
                None,
            )
            for i, e in enumerate(EMOTIONS, start=1)
        ],
        (f"p_medurgency_{s}", URGENCY, _five("Not at all urgent", "Very urgent"), None),
        (
            f"p_medefficacy_{s}",
            EFFICACY,
            _five("No difference at all", "A great deal of difference"),
            None,
        ),
        (
            f"getinfo_{s}",
            GETINFO + options(GETINFO_OPTIONS),
            {"min": 1, "max": 2, "nominal": True},
            yes_no,
        ),
        (
            f"donate_{s}",
            DONATE + options(DONATE_OPTIONS),
            {"min": 1, "max": 2, "nominal": True},
            yes_no,
        ),
        (
            f"donate_amt_{s}",
            AMOUNT + AMOUNT_ADDED,
            {"min": 1, "max": AMOUNT_MAX},
            AMOUNT_RECODE,
        ),
        *[
            (
                f"eff_follow_{v}_{s}",
                q,
                {"min": 0, "max": 10, "min_label": IMPACT_MIN, "max_label": IMPACT_MAX},
                IMPACT_RECODE,
            )
            for v, q in ((y, IMPACT_YES), (n, IMPACT_NO))
        ],
    ]


def outcomes() -> list[dict[str, Any]]:
    out = []
    for k, s in enumerate(SLOTS, start=1):
        for i, (var, question, scale, recode) in enumerate(slot_items(s)):
            o: dict[str, Any] = {
                "var": var,
                "task_num": 11 * (k - 1) + i,
                "question": question,
                "scale": scale,
            }
            if recode is not None:
                o["response_recode"] = recode
            if k > 1:
                o["condition_var"] = code_var(k)
            out.append(o)
    return out


def arms(df: Any) -> list[dict[str, Any]]:
    where = shown(df)
    out = []
    for n, (name, names) in enumerate(pictures(df)):
        s = where[name][0]
        codes = [code_of(s, number_of(x)) for x in names]
        arm: dict[str, Any] = {"raws": codes} if len(codes) > 1 else {"raw": codes[0]}
        arm |= {
            "condition_num": n,
            "factors": {"image_set": SETS[s], "photo": " = ".join(names)},
            "text": ARM_TEXT,
            "images": [image_id(name)],
        }
        out.append(arm)
    return out


def persona() -> dict[str, Any]:
    """The Feb 2023 persona block, after checking its variables mean the same here."""
    import pyreadstat

    src = yaml.safe_load(PERSONA_FROM.read_text())
    variables = list(src["persona_map"].values())
    _, oct_meta = pyreadstat.read_sav(str(SAV), usecols=variables, metadataonly=True)
    _, feb_meta = pyreadstat.read_sav(str(FEB_SAV), usecols=variables, metadataonly=True)
    for v in variables:
        if oct_meta.variable_value_labels.get(v) != feb_meta.variable_value_labels.get(v):
            raise SystemExit(f"{v}: value labels differ from Feb 2023")
    return {k: src[k] for k in ("persona_label_rewrite", "persona_map", "persona_missing")}


def recipe() -> dict[str, Any]:
    check_wording()
    df = _read_sav()
    src = yaml.safe_load(PERSONA_FROM.read_text())
    return {
        "study_id": "del",
        "source": "dataverse",
        "experiment": "sandbox_oct2023_appeal_photos",
        "title": "Development Engagement Lab, Sandbox Great Britain October 2023: "
        "photographs for international development charity appeals; emotions, urgency, "
        "efficacy, finding out more and donating",
        "data_file": DATA_FILE,
        "licence": src["licence"],
        "comparable_to_socsci210": False,
        "participant_id_var": src["participant_id_var"],
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_var": code_var(1),
            # `image_set` rides on each arm as metadata but is not declared: every photo
            # belongs to one folder, so it is nested in `photo` and has no minimal pair.
            "factors": ["photo"],
            "shared_context": SHARED,
            "considered_and_rejected": {
                "moduleB2_order": "Orders the two appeal questions within each slot "
                "(getinfo first, or donate first); question order is not rendered.",
            },
            "arms": arms(df),
        },
        "outcomes": outcomes(),
        "response_recode": {v: v for v in range(1, 6)},
        "missing_codes": [99998, 99999],
        **persona(),
    }


def render() -> str:
    return yaml.safe_dump(recipe(), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--fetch", action="store_true", help="download the shown photos")
    ap.add_argument("--prep", action="store_true", help="write the derived .sav")
    ap.add_argument("--catalogue", action="store_true", help="add this study's images.json entries")
    args = ap.parse_args()
    if args.fetch:
        fetch()
        return 0
    if args.catalogue:
        write_catalogue()
        print("updated data/catalog/images.json (del_oct2023_* entries only)")
        return 0
    if args.prep:
        write_derived()
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
