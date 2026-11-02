#!/usr/bin/env python3
"""Write recipes/images/zenodo10628634.yaml: mycelium as food, product x substrate (IMG77).

Fischer & Hilboesen (Wageningen), "Consumer acceptance of mycelium as protein
source", Food Quality and Preference 122 (2025) 105304,
https://doi.org/10.1016/j.foodqual.2024.105304 (open access, edepot.wur.nl/672569).
Zenodo record 10628634, "Consumer acceptance Mycelium" (CC BY 4.0): the survey
("full experimental design.docx", the same text and pictures as the .rtf copy),
the data (Mycelium.sav, with Mycelium.csv as an unlabelled copy), the authors' R
script and a readme.

449 UK adults (Prolific, 2021; the readme: "Sampled from Prolific age above 18,
residence in the UK"; the paper: "Participants were from the UK") were each shown
ONE of nine short texts about a new food made from mycelium, between subjects: the
product (a mould cake, a protein powder, a burger) crossed with what the mycelium
is grown on (composted horse manure with straw, hardwood logs, glucose with added
vitamins and minerals). Each text carries a picture of the product and a picture
of the substrate, each with a caption. They then rated the product.

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* INSTRUMENT. The docx is the only instrument in the deposit. The readme calls it
  "The survey as taken by participants - including all 9 conditions (only one
  shown for individual participants)", and it marks in red what participants did
  not see (scenario headings, question numbers, "Next page"). It carries Qualtrics
  traces ("I might consider consuming this product (5)", the duplicated
  "Q8. ... Q16 ..." heading), so it reads as a transcription of the fielded survey
  and is taken as the fielded wording. The paper's Text box 1 is a shorter
  paraphrase ("the roots of fungi", "Mycelium can be grown on either solid or
  liquid surfaces"), not what was shown, and is not used.
* ARMS. `Condition` 1-9 (value labels "mould cake x horse manure" ... "burger x
  glucose"); `Process` and `Source` agree with it in every row. Each code's text is
  the docx block under the red heading naming the same product and substrate
  (matched in code by keyword, not by position). The arm text is that block
  word-for-word, read from the docx at generation time, with typography normalised
  (curly quotes straightened, runs of spaces collapsed). The nine blocks are NOT
  word-identical apart from the product and substrate: the mould cake x manure
  block says "a new interesting food product" and "plant based"; the burger x
  manure block "a Mycelium burger"; and two burger blocks carry a sentence the
  others lack, burger x logs "The mycelium used for this product is grown using a
  substrate of straw." followed by a stray closing quotation mark, and burger x
  glucose "The mycelium used for this product is grown using a substrate of
  glucose with added vitamins and minerals." These are in black, the colour of
  what participants saw, in both the docx and the .rtf, so they are kept as
  shown, including the straw sentence that contradicts its own arm's logs.
  The evidence the other way is real: the paper's Text box 1 is one template with
  a single substrate statement per condition and no "substrate of straw"
  sentence, and "grown using a substrate of straw" under hardwood logs
  contradicts the design (as does its stray quotation mark), so that sentence may
  never have been shown. It is kept because the docx, the only fielded
  instrument in the deposit, has it in black; which is true cannot be settled
  from the deposit.
  Dropped as survey mechanics: "Please take your time to read the text and
  analyse the pictures carefully", identical in every arm. Words that are OURS:
  "Captioned:" before each picture's caption, which the survey printed under the
  picture. In the mould cake x manure block the docx floats the cake picture
  beside its caption; the other eight blocks place each picture above its
  caption, as the paper's Table 1 does, and so does the text here.
* PICTURES. Six, each shown in three arms: three products and three substrates.
  Extracted from the docx (word/media), five unaltered. The mould cake picture is
  displayed in the docx cropped (a:srcRect l=13.942%, r=21.314%, b=2.242%), which
  cuts off a second, dark lump on the right; the paper's Table 1 shows the same
  crop. The catalogued file is that crop, made with macOS sips (left 286, width
  1325, height 1340 of 2048x1371, rounded to whole pixels) and saved as PNG so no
  further compression is added. No picture carries words (text_in_image is empty).
* OUTCOMES. 16, every item before the background questions, in the survey's
  order: willingness to consider (Q1), the six value items (Q2: three of the
  authors' acceptance construct, three social value), four disgust items (Q3),
  health benefits, environmental benefits, health risks, environmental risks
  (Q4-Q7), and naturalness (Q8). Wording is the docx's: each screen's stem
  followed by its statement in quotation marks, question numbers (red) and the
  stray "Q16 ..." duplicate dropped. Scale endpoint and midpoint labels are the
  docx's column headings, without their "1." / "4." / "7." prefixes. The SPSS
  labels differ for Q1 ("4. I am indifferent about consuming this product", "7. I
  would definitly consider ..."); the docx wins as the survey shown. All answers
  are 1-7 as stored, none missing, risks NOT reverse-scored.
* NOT BUILT. Familiarity with eating mycelium and the twelve environmental concern
  items (Q9, Q10): asked after the scenario, about the person rather than the
  product, so neither an outcome of the manipulation nor a clean persona
  attribute (the paper uses both only as randomisation checks).
* WHO. All 449 rows (Table 2's cell sizes 50/51/50/50/50/49/50/50/49 equal the
  data's). Table 2's item means and SDs leave out the 4 people with no age (one
  each in mould cake x logs, mould cake x glucose, burger x manure, burger x logs),
  though it prints the full cell sizes; with those four left out the built rows
  reproduce all 144 of its means and all 144 of its SDs (the SDs rounded to three
  decimals and then two). Nothing else marks those four, so they are built. The
  data hold no respondent id, so participants are keyed by row position in
  Mycelium.sav.
* PERSONA. Asked at the end, stable facts: age (4 blank), gender ("Prefer not to
  say", 1 person, is a non-answer) and education. Education crosswalk scheme
  uk_zenodo10628634 (data/catalog/persona_crosswalk_education.json), read from
  existing schemes' precedents, not asked of Jev.

    uv run python scripts/gen_zenodo10628634.py --extract    # (re)write the six pictures
    uv run python scripts/gen_zenodo10628634.py --catalogue  # this study's images.json entries
    uv run python scripts/gen_zenodo10628634.py              # write the recipe
    uv run python scripts/gen_zenodo10628634.py --check      # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

STUDY = "zenodo10628634"
RAW = REPO / "data" / "raw" / STUDY
DOCX = RAW / "full experimental design.docx"
DATA_FILE = "Mycelium.sav"
DATA = RAW / DATA_FILE
PICTURES_DIR = "pictures"
RECIPE = REPO / "recipes" / "images" / f"{STUDY}.yaml"
RECORD = "https://zenodo.org/records/10628634"
LICENCE = (
    "CC BY 4.0 (Zenodo 10628634). The photographs are embedded in the deposit's survey "
    "document; their own sources and terms are not stated, and two carry embedded "
    "metadata from other publishers."
)

CONDITION_VAR = "Condition"
RED = "FF0000"

# Factor levels, each with the keywords that identify it in a docx heading and in
# the SPSS value label of `Condition`.
PRODUCTS = {
    "mould cake": ("cake",),
    "protein powder": ("powder",),
    "burger": ("burger",),
}
SUBSTRATES = {
    "horse manure": ("manure",),
    "hardwood logs": ("logs",),
    "glucose": ("glucose",),
}
# Picture id suffix and file name, keyed by the docx relationship's media name.
PICTURES = {
    "image1.jpg": ("product_mould_cake", "product_mould_cake.png"),
    "image5.jpg": ("product_protein_powder", "product_protein_powder.jpg"),
    "image6.jpg": ("product_burger", "product_burger.jpg"),
    "image2.jpg": ("substrate_horse_manure", "substrate_horse_manure.jpg"),
    "image3.jpg": ("substrate_hardwood_logs", "substrate_hardwood_logs.jpg"),
    "image4.png": ("substrate_glucose", "substrate_glucose.png"),
}
CROPPED = "image1.jpg"
DESCRIPTIONS = {
    "product_mould_cake": (
        "Photograph from above of a thick rectangular block of pale, straw-coloured fibrous "
        "material covered in white fluffy growth, resting on crumpled aluminium foil on a bed "
        "of white granules inside a grey container with small holes in its walls and two "
        "threaded metal rods across it; part of a white surface with a few brown crumbs at "
        "the right edge."
    ),
    "product_protein_powder": (
        "Photograph of a white plastic measuring scoop heaped with fine cream-coloured powder "
        "on a dark wooden surface, a small pile of the same powder in front of it and a green "
        "bowl of the powder behind it on the left."
    ),
    "product_burger": (
        "Photograph of two round, flat, brown patties with a criss-cross pattern pressed into "
        "their tops, one leaning against the other, on white paper."
    ),
    "substrate_horse_manure": (
        "Close-up photograph filling the frame with a dark brown, crumbly mass mixed with "
        "short broken pieces of yellow straw. A small, low-resolution picture."
    ),
    "substrate_hardwood_logs": (
        "Close-up photograph of a heap of split, pale wooden logs, some with dark bark on one "
        "side, filling the frame."
    ),
    "substrate_glucose": (
        "Photograph of a small clear glass vial with a white screw cap, about two-thirds full "
        "of clear yellow liquid, standing on a white surface against a plain white background, "
        "its reflection below it."
    ),
}

DROPPED = "Please take your time to read the text and analyse the pictures carefully"
CAPTION_LEAD = "Captioned:"


def _clean(text: str) -> str:
    """Typography only: straight quotes, single spaces. Words untouched."""
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace(" ", " ")
    return re.sub(r"\s+", " ", text).strip()


def _docx_parts() -> tuple[str, dict[str, str]]:
    with zipfile.ZipFile(DOCX) as z:
        xml = z.read("word/document.xml").decode("utf-8")
        rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
    media = {
        m.group(1): m.group(2).removeprefix("media/")
        for m in re.finditer(r'Id="([^"]+)"[^>]*Target="(media/[^"]+)"', rels)
    }
    return xml, media


def paragraphs() -> list[dict[str, Any]]:
    """Each body paragraph: its shown (non-red) text, its red text, its pictures.

    A picture is ("inline"|"anchor", media name, srcRect attributes)."""
    xml, media = _docx_parts()
    out: list[dict[str, Any]] = []
    for p in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
        shown, red = [], []
        for run in re.findall(r"<w:r[ >].*?</w:r>", p, flags=re.S):
            text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", run))
            colour = re.search(r'<w:color w:val="([^"]+)"', run)
            (red if colour and colour.group(1) == RED else shown).append(text)
        pictures = []
        for d in re.findall(r"<w:drawing>(.*?)</w:drawing>", p, flags=re.S):
            rid = re.search(r'r:embed="([^"]+)"', d)
            assert rid, "drawing without an embedded picture"
            crop = re.search(r"<a:srcRect([^/]*)/>", d)
            attrs = dict(re.findall(r'(\w+)="(\d+)"', crop.group(1))) if crop else {}
            kind = "anchor" if "<wp:anchor" in d else "inline"
            pictures.append((kind, media[rid.group(1)], attrs))
        out.append(
            {
                "shown": _clean("".join(shown)),
                "red": _clean("".join(red)),
                "pictures": pictures,
            }
        )
    return out


def _level(text: str, levels: dict[str, tuple[str, ...]]) -> str:
    hits = [lv for lv, keys in levels.items() if any(k in text.lower() for k in keys)]
    if len(hits) != 1:
        raise SystemExit(f"cannot place {text!r}: {hits}")
    return hits[0]


def scenarios() -> dict[tuple[str, str], list[tuple[str, str]]]:
    """(product, substrate) -> the block's items in order: ("text", s) or ("image", media)."""
    blocks: dict[tuple[str, str], list[tuple[str, str]]] = {}
    current: list[tuple[str, str]] | None = None
    for p in paragraphs():
        heading = p["red"] and not p["shown"] and " x " in p["red"]
        if heading:
            key = (_level(p["red"], PRODUCTS), _level(p["red"], SUBSTRATES))
            if key in blocks:
                raise SystemExit(f"two blocks for {key}")
            current = blocks[key] = []
            continue
        if current is None:
            continue
        if p["red"] == "Next page" and not p["shown"]:
            current = None
            continue
        if p["red"]:
            raise SystemExit(f"red text inside a scenario: {p['red']!r}")
        # A floating picture sits beside its caption in the docx's layout; every
        # inline one sits above it. Put pictures first.
        for _, name, _ in p["pictures"]:
            current.append(("image", name))
        if p["shown"]:
            current.append(("text", p["shown"]))
    if len(blocks) != 9:
        raise SystemExit(f"expected 9 scenario blocks, found {len(blocks)}")
    return blocks


SHAPE = ["text", "text", "image", "text", "text", "image", "text"]


def arm_parts(product: str, substrate: str) -> tuple[str, str, str, str, str, str]:
    """(intro, product picture, product caption, substrate text, substrate picture,
    substrate caption) for one block, after the dropped reading instruction."""
    items = scenarios()[(product, substrate)]
    if [k for k, _ in items] != SHAPE:
        raise SystemExit(f"{product} x {substrate}: unexpected shape {items}")
    values = [v for _, v in items]
    if values[0] != DROPPED:
        raise SystemExit(f"{product} x {substrate}: first line is {values[0]!r}")
    intro, pic1, cap1, sub, pic2, cap2 = values[1:]
    return intro, pic1, cap1, sub, pic2, cap2


def arm_text(product: str, substrate: str) -> tuple[str, list[str]]:
    intro, pic1, cap1, sub, pic2, cap2 = arm_parts(product, substrate)
    text = f'{intro} <image> {CAPTION_LEAD} "{cap1}" {sub} <image> {CAPTION_LEAD} "{cap2}"'
    return text, [image_id(pic1), image_id(pic2)]


def image_id(media_name: str) -> str:
    return f"{STUDY}_{PICTURES[media_name][0]}"


def image_file(media_name: str) -> str:
    """Path under data/, as the catalogue records it."""
    return f"raw/{STUDY}/{PICTURES_DIR}/{PICTURES[media_name][1]}"


def crop_box() -> tuple[int, int, int, int]:
    """(left, top, width, height) in pixels from the docx's own crop of the cake picture."""
    crops = {
        tuple(sorted(attrs.items()))
        for p in paragraphs()
        for _, name, attrs in p["pictures"]
        if name == CROPPED
    }
    if len(crops) != 1:
        raise SystemExit(f"the cake picture is cropped {len(crops)} different ways")
    attrs = {k: int(v) / 100000 for k, v in dict(next(iter(crops))).items()}
    width, height = 2048, 1371
    left = round(width * attrs.get("l", 0))
    right = round(width * attrs.get("r", 0))
    top = round(height * attrs.get("t", 0))
    bottom = round(height * attrs.get("b", 0))
    return left, top, width - left - right, height - top - bottom


def extract() -> None:
    """Write the six pictures from the docx; the cake one with the docx's crop."""
    out = RAW / PICTURES_DIR
    out.mkdir(exist_ok=True)
    with zipfile.ZipFile(DOCX) as z, tempfile.TemporaryDirectory() as tmp:
        for name in PICTURES:
            src = Path(tmp) / name
            src.write_bytes(z.read(f"word/media/{name}"))
            dst = REPO / "data" / image_file(name)
            if name != CROPPED:
                shutil.copyfile(src, dst)
                continue
            left, top, w, h = crop_box()
            subprocess.run(
                [
                    "sips",
                    "-s",
                    "format",
                    "png",
                    "-c",
                    str(h),
                    str(w),
                    "--cropOffset",
                    str(top),
                    str(left),
                    str(src),
                    "--out",
                    str(dst),
                ],
                check=True,
                capture_output=True,
            )


def catalogue_entries() -> dict[str, dict[str, str]]:
    """This study's entries in data/catalog/images.json."""
    from micromotives_datasets.images import sha256_of

    out: dict[str, dict[str, str]] = {}
    for name, (suffix, _) in PICTURES.items():
        f = image_file(name)
        how = "extracted unaltered"
        if name == CROPPED:
            left, top, w, h = crop_box()
            how = (
                f"cropped as the docx displays it (a:srcRect; left {left}, top {top}, "
                f"{w}x{h} of 2048x1371) with macOS sips and saved as PNG"
            )
        out[image_id(name)] = {
            "file": f,
            "sha256": sha256_of(REPO / "data" / f),
            "source": f"{RECORD} (full experimental design.docx, word/media/{name}; {how})",
            "licence": LICENCE,
            "text_in_image": "",
            "description": DESCRIPTIONS[suffix],
        }
    return out


def write_catalogue() -> None:
    """Add or refresh only this study's entries; re-read first, others are editing too."""
    import json

    path = REPO / "data" / "catalog" / "images.json"
    current = json.loads(path.read_text())
    current.update(catalogue_entries())
    path.write_text(json.dumps(current, indent=2, ensure_ascii=False))


# The survey's question screens, word-for-word from the docx (black text).
Q1 = (
    "Imagine you walk through the grocery store and come across a novel product as "
    "described in the previous informational text. Please provide your response to the "
    "following statement regarding your willingness to consider this novel mycelium product."
)
Q2 = (
    "Please provide your response to the following statements regarding the value you "
    "perceive of the novel mycelium product"
)
Q3 = (
    "Please provide your response to the following statements regarding your feelings of "
    "disgust towards the novel mycelium product"
)
Q4 = (
    "Please provide your opinion on the following statement regarding the expected health "
    "benefits of consuming the novel mycelium product"
)
Q5 = (
    "Please provide your opinion on the following statement regarding the expected "
    "environmental sustainability benefits of producing the novel mycelium product"
)
Q6 = (
    "Please provide your opinion on the following statements regarding the expected health "
    "risks of consuming the novel mycelium product"
)
Q7 = (
    "Please provide your opinion on the following statements regarding the expected "
    "environmental sustainability risks of producing the novel mycelium product"
)
Q8 = "Please answer the following questions regarding the naturalness of the novel mycelium product"

CONSIDER = (
    "I would never consider consuming this product",
    "I don't know if I would consider consuming this product",
    "I would definitely consider consuming this product",
)
AGREE = ("Totally disagree", "Neither agree nor disagree", "Totally agree")
EXTENT = ("None at all", "Moderately", "Extremely")
AMOUNT = ("Not at all", "Moderately", "A great deal")
NATURAL = ("Not at all natural", "Moderately natural", "Extremely natural")

# (variable, stem, statement, (min, mid, max) labels) in the survey's order.
OUTCOME_ITEMS: list[tuple[str, str, str, tuple[str, str, str]]] = [
    ("INT1", Q1, "I would consider consuming this product", CONSIDER),
    ("ATT1", Q2, "This product is one that I would enjoy", AGREE),
    ("INT2", Q2, "This product would make me want to consume it", AGREE),
    ("ATT2", Q2, "Consuming this product would make me feel good", AGREE),
    ("SOC1", Q2, "Consuming this product would help me feel acceptable", AGREE),
    ("SOC2", Q2, "Consuming this product would improve the way I am perceived", AGREE),
    ("SOC3", Q2, "Consuming this product would make a good impression on other people", AGREE),
    ("DISG1", Q3, "The thought of eating this food makes me nauseous", EXTENT),
    ("DISG2", Q3, "I dislike the idea of having this food in my stomach", EXTENT),
    (
        "DISG3",
        Q3,
        "I dislike the idea of this food because of what it is or where it comes from",
        EXTENT,
    ),
    ("DISG4", Q3, "The thought of eating this food is disgusting to me", EXTENT),
    ("HeaB", Q4, "Consuming this product will provide health benefits", AMOUNT),
    (
        "EnvB",
        Q5,
        "Producing this product will benefit the sustainability of the environment",
        AMOUNT,
    ),
    ("HeaR", Q6, "Consuming this product will result in health risks", AMOUNT),
    (
        "EnvR",
        Q7,
        "Producing this product will increase the risk of environmental sustainability losses",
        AMOUNT,
    ),
    ("NATURAL", Q8, "How natural do you perceive this product to be?", NATURAL),
]
GENDER_REFUSED = "Prefer not to say"


def docx_shown_text() -> str:
    """Every black word of the survey, paragraphs joined by spaces (for tests)."""
    return " ".join(p["shown"] for p in paragraphs() if p["shown"])


def recipe() -> dict[str, Any]:
    ds = read_any(DATA)
    labels = ds.value_labels
    codes = {int(k): str(v) for k, v in labels[CONDITION_VAR].items()}
    if sorted(codes) != list(range(1, 10)):
        raise SystemExit(f"condition codes changed: {sorted(codes)}")
    if set(ds.df[CONDITION_VAR].dropna().astype(int)) != set(codes):
        raise SystemExit("condition codes in the data differ from the labels")

    arms = []
    for raw, label in sorted(codes.items()):
        product = _level(label, PRODUCTS)
        substrate = _level(label, SUBSTRATES)
        text, images = arm_text(product, substrate)
        arms.append(
            {
                "raw": raw,
                "condition_num": raw - 1,
                "factors": {"product": product, "substrate": substrate},
                "text": text,
                "images": images,
            }
        )

    outcomes = []
    for t, (var, stem, statement, (lo, mid, hi)) in enumerate(OUTCOME_ITEMS):
        stray = set(ds.df[var].dropna().astype(int)) - set(range(1, 8))
        if stray or ds.df[var].isna().any():
            raise SystemExit(f"{var}: unexpected answers {sorted(stray)}")
        outcomes.append(
            {
                "var": var,
                "task_num": t,
                "question": f'{stem} "{statement}"',
                "scale": {"min": 1, "max": 7, "min_label": lo, "max_label": hi, "mid_label": mid},
                "response_recode": {i: i for i in range(1, 8)},
            }
        )

    def code_of(var: str, label: str) -> int:
        return next(int(k) for k, v in labels[var].items() if v == label)

    return {
        "study_id": STUDY,
        "source": "zenodo",
        "title": "Mycelium as food: a mould cake, protein powder or burger grown on horse "
        "manure, hardwood logs or glucose, each shown in pictures; acceptance, value, "
        "disgust, benefits and risks, naturalness",
        "data_file": DATA_FILE,
        "licence": "CC BY 4.0 (Zenodo 10628634).",
        "comparable_to_socsci210": False,
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_var": CONDITION_VAR,
            "factors": ["product", "substrate"],
            "arms": arms,
        },
        "outcomes": outcomes,
        "response_recode": {},
        "persona_map": {"age": "Age", "gender": "Gender", "education": "Education"},
        "persona_missing": {"Gender": [code_of("Gender", GENDER_REFUSED)]},
    }


def render() -> str:
    return yaml.safe_dump(recipe(), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--extract", action="store_true", help="(re)write the six pictures")
    ap.add_argument("--catalogue", action="store_true", help="add this study's images.json entries")
    args = ap.parse_args()
    if args.extract:
        extract()
        print(f"wrote {(RAW / PICTURES_DIR).relative_to(REPO)}")
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
