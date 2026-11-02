#!/usr/bin/env python3
"""Write recipes/images/del_sandbox_feb2023_help_pictures.yaml: who needs / deserves help (IMG07).

Hudson, Jennifer; Hudson, David; Morini, Paolo; Oh, Soomin; Torres-Raposo, Felipe,
2024, "DEL Sandbox 2023", https://doi.org/10.7910/DVN/XZ1XUZ, Harvard Dataverse, V1;
DEL_Sandbox_GreatBritain_Feb2023_Data.sav. Fielded online by YouGov, 20-28 February
2023, n = 2,007 adults in Great Britain (the deposit's Readme). The same file as
`del_sandbox_feb2023_wordfeminist` and the other five Feb 2023 text builds, whose
licence, person id and persona block carry over unchanged (read from that recipe by
this generator, so they cannot drift).

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* THE DESIGN. Four paired-photo screens, `images_1` .. `images_4`, every respondent.
  The script (DEL_Sandbox_GreatBritain_Feb2023_Survey.docx, the block after `femi`)
  lists ten photos, `img_name_arr` = M_EMP, M_WORK, W_WORK, W_PARENT, W_NEUT, W_EMP,
  W_CONT, M_PARENT, M_NEUT, M_CONT, and draws four pairs WITHOUT replacement across
  the whole block (`random_samples(..., 2)` then `sets.sdiff`), so each person sees
  eight different photos, none twice. The first of each pair is Picture A, the
  second Picture B. `img1_pair{k}_A` / `_B` record, per person, the `<img>` tag shown,
  with the file name in `alt` and the YouGov CloudFront URL in `src`; all 2,007
  people have all eight, every tag parses, each file name has exactly one URL, A and
  B always differ and the eight are always distinct (checked by `prep()`).
* WHAT VARIES. The ordered pair (A, B): 90 arms, condition_num = 9 * (code_A - 1) +
  rank of code_B among the other nine, codes 1-10 in the instrument's own array
  order. Declared on the condition as `source_vars` (screen 1's two columns) and on
  each later screen's outcome as `condition_vars`, so each screen resolves its own
  arm. Factors, structured metadata for each picture: person (man / woman, from the
  file name's M / W) and framing (the file name's own code: CONT, EMP, NEUT, PARENT,
  WORK). What the five codes stand for is NOT stated anywhere in the deposit
  (questionnaire, codebook, Readme), so they are kept as codes, not expanded.
* THE PREPPED FILE. The pipeline reads integer assignment codes, and the .sav holds
  the tags as strings, so `--prep` writes `DEL_Sandbox_GreatBritain_Feb2023_Data-
  derived.sav`: the deposit unchanged (a pyreadstat round trip, values, variable
  labels and value labels identical) plus eight integer columns `img_pair{k}_A_code`
  / `_B_code`, labelled with the file name. Nothing else changes.
* CONDITION. Ours: "Two pictures were shown side by side below the question." and the
  colon after each heading. The instrument's: "Picture A" and "Picture B", the
  table's two column headings, each over its picture (the questionnaire's table:
  one row of headings, one row of pictures, 50% width each). No pair number ("pair
  3") is rendered: a row cannot cite its position (docs/CONVENTIONS.md). The photos
  carry no caption on screen; the few words visible in them (a T-shirt, a tent) are
  in the catalogue's text_in_image, and are not quoted in the condition because
  they are incidental to the photograph, not a caption the respondent was given to
  read (k369t precedent: the image carries its own words).
* OUTCOMES. Word-for-word from the questionnaire (and the .sav's variable label):
  "Looking at the two images below, please tell us which pictures shows the person
  or people you think needs help the most." (`images_1`, `images_2`) and the same
  with "deserves help the most" (`images_3`, `images_4`). "pictures shows" is the
  instrument's grammar and is kept; the `**` bold markup is typography and goes.
  The answers are a nominal choice: 1 Picture A, 2 Both equally, 3 Picture B, 4
  Neither of these, enumerated in the question in the PZB01G form ("1 means ..."),
  ours. 5 "Don't know" is dropped as a non-answer; 8 "Skipped" and 9 "Not Asked" are
  labelled, never occur, and are declared so a re-fetched deposit drops them.
  Screens 1 and 2 share a wording, as do 3 and 4; their rows differ by the pictures
  (no person sees a photo twice), so no participant has two rows with the same
  condition and outcome (QC rule 24). The split tooling joins task numbers that
  share a wording into one hiding unit.
* WHAT CAME BEFORE, the same for everyone, none of it rendered. The block follows
  the feminism grid `femi` and a "Moving on..." page; earlier in the interview
  everyone answered the aid, gender-equality and feminism items built in the six
  Feb 2023 text recipes. The women-only `womenexp` block comes after.
* PHOTOS. Fetched from the ten URLs in the .sav into data/raw/del/feb2023_images/,
  byte-identical to an earlier independent download. Rights are not stated by the
  deposit. Several files carry embedded rights metadata (catalogue `licence`); it is
  recorded, not acted on.
* PERSONA and PERSON ID as in del_sandbox_feb2023_wordfeminist.yaml (`GUNQID`,
  study_id `del`, shared across all DEL files).
* REFERENCE. No published figures for this block were found; the crosscheck is
  internal (A/B balance, each photo's share chosen when shown).

    uv run python scripts/gen_del_feb2023_help_pictures.py --prep       # derived .sav
    uv run python scripts/gen_del_feb2023_help_pictures.py --catalogue  # images.json
    uv run python scripts/gen_del_feb2023_help_pictures.py              # the recipe
    uv run python scripts/gen_del_feb2023_help_pictures.py --check      # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

RAW = REPO / "data" / "raw" / "del"
SAV = RAW / "DEL_Sandbox_GreatBritain_Feb2023_Data.sav"
DATA_FILE = "DEL_Sandbox_GreatBritain_Feb2023_Data-derived.sav"
DERIVED = RAW / DATA_FILE
IMAGE_DIR = "raw/del/feb2023_images"  # relative to data/
RECIPE = REPO / "recipes" / "images" / "del_sandbox_feb2023_help_pictures.yaml"
PERSONA_FROM = REPO / "recipes" / "del_sandbox_feb2023_wordfeminist.yaml"

# The script's `img_name_arr`, in its own order; code = position + 1.
IMG_NAME_ARR = [
    "M_EMP.jpeg",
    "M_WORK.jpg",
    "W_WORK.jpg",
    "W_PARENT.jpg",
    "W_NEUT.jpg",
    "W_EMP.jpg",
    "W_CONT.jpg",
    "M_PARENT.jpg",
    "M_NEUT.jpg",
    "M_CONT.jpg",
]
CODE = {name: i + 1 for i, name in enumerate(IMG_NAME_ARR)}
SCREENS = [1, 2, 3, 4]
TAG = re.compile(
    r"<img src='(https://d25tjp0uwv51o3\.cloudfront\.net/public/[0-9a-f]{32}/"
    r"[0-9a-f]{24}\.jpe?g)' alt='([MW]_[A-Z]+\.jpe?g)'/>"
)


def tag_var(screen: int, side: str) -> str:
    return f"img1_pair{screen}_{side}"


def code_var(screen: int, side: str) -> str:
    return f"img_pair{screen}_{side}_code"


def image_id(name: str) -> str:
    return "del_feb2023_" + name.split(".")[0].lower()


def person(name: str) -> str:
    return {"M": "man", "W": "woman"}[name[0]]


def framing(name: str) -> str:
    return name.split(".")[0].split("_", 1)[1]


# --- the photos -------------------------------------------------------------------

# Words visible in each photo, word-for-word as far as legible; " / " between
# separate pieces of text. Most carry none. A transcription that is not complete
# says so in square brackets, which are ours.
TEXT_IN_IMAGE = {
    "M_EMP.jpeg": "AFRICA / WESTERN SAHARA / ALGERIA / LIBYA / MALI / NIGER / CHAD / "
    "SUDAN / TOGO / BENIN / [partial: the smaller country names on the map are not legible]",
    "M_PARENT.jpg": "UNHCR",
}

# Ours, and checked: what each photo shows, without guessing who, where or why. Only
# plainly visible facts (setting, clothing, what the person is doing, who is in the
# frame, where they look); no appraisals of build, mood or age, which could prime a
# question about who needs help. The same attribute wording in all ten.
DESCRIPTIONS = {
    "M_CONT.jpg": "Colour photograph, square. A Black man stands in dry, open bush, "
    "holding a long wooden stick across his body and looking off to one side; he wears "
    "a brown striped vest, a white bead necklace, a leather belt and dark trousers. "
    "Behind him is bare reddish ground with dark patches of burnt grass and scrubby "
    "trees under a hazy sky. No words.",
    "M_EMP.jpeg": "Colour photograph, square. A Black man stands with his hands on his "
    "hips, looking at the camera, in front of a fence of dry reeds or straw in bright "
    "sun. He wears a black T-shirt with purple trim printed with a map of Africa and "
    "the word AFRICA in large dotted letters; the larger country names on the map are "
    "quoted in text_in_image, the smaller ones are too small to read.",
    "M_NEUT.jpg": "Colour photograph, square, a head-and-shoulders portrait. A Black man "
    "with a shaved head looks at the camera; he wears a turquoise scrub-style top over "
    "a grey collared shirt. Behind him, out of focus, a single-storey building, a tree "
    "and a few people on sandy ground. No words.",
    "M_PARENT.jpg": "Colour photograph, square. A Black man with a short beard, in a "
    "blue shirt, sits holding a small child in a striped top on his lap; the man looks "
    "towards the camera, the child looks down and away. Behind them, white tents on "
    "bare ground among trees, with people standing nearby; one tent is printed with a "
    "blue logo and the word quoted in text_in_image, partly crossed by a guy rope, with "
    "smaller lines beneath too blurred to read. Printing on the child's top is not "
    "legible.",
    "M_WORK.jpg": "Colour photograph, square. A Black man with grey hair, in a "
    "short-sleeved light-coloured shirt, sits at a black manual sewing machine on a "
    "wooden table, his hands on the cloth, looking at the camera. Behind him, a window "
    "with wooden bars, a chair with a cloth over it, and plain walls. No legible words.",
    "W_CONT.jpg": "Colour photograph, square. A Black woman stands in front of a large "
    "heap of dry straw or thatch, looking at the camera, wearing a loose floral dress "
    "and a necklace of coloured beads. The ground is dry and dusty, with a hazy sky and "
    "bare trees to the left. No words.",
    "W_EMP.jpg": "Colour photograph, square. A Black woman stands with her hands on her "
    "hips, looking at the camera, on bare earth in front of round thatched huts and "
    "trees. She wears a mustard-yellow top and a long yellow-and-white patterned wrap "
    "skirt, with sandals. No words.",
    "W_NEUT.jpg": "Colour photograph, square, a head-and-shoulders portrait. A Black "
    "woman in a white head covering and a white collared uniform shirt, with a blue pen "
    "in the pocket, looks at the camera. Behind her, a building painted green below "
    "and yellow above, with a green door and barred windows. No words.",
    "W_PARENT.jpg": "Colour photograph, square. A Black woman holds a baby in a blue "
    "striped top, wrapped partly in a brightly patterned cloth; her eyes are lowered "
    "and the baby looks down. Behind them, out of focus, trees, dry ground and a "
    "building under a blue sky. Printing on the baby's top is not legible.",
    "W_WORK.jpg": "Colour photograph, square. A Black woman in a bright blue dress and a "
    "red head wrap kneels in a field of low green plants on dry, cracked soil, looking "
    "down and tending the plants with her hands. Flat land, scattered trees and "
    "distant figures stretch to the horizon under a pale blue sky. No words.",
}

# Rights metadata embedded in the files themselves (ImageDescription / Artist /
# Copyright / XMP dc:rights), recorded as found; files not listed carry none.
EMBEDDED_RIGHTS = {
    "M_EMP.jpeg": 'embedded copyright "Copyright (c) 2017 Anton_Ivanov/Shutterstock.  '
    'No use without permission."',
    "M_NEUT.jpg": 'embedded copyright "Crown Copyright: This image may be used for current '
    "news purposes only.  It may not be used, reproduced or transmitted for any other "
    "purpose without first obtaining a copyright license available from the MoD, Crown "
    'Copyright Unit."; artist "Corporal Paul Shaw ABIPP (Army)"',
    "M_WORK.jpg": 'embedded copyright "Department For International Development/Simon Davis"',
    "W_WORK.jpg": 'embedded copyright "© Valérie Batselaere 2012"; artist "Pablo '
    'Tosco/Intermon Oxfam, Valérie Batselaere"',
}
LICENCE = "Data CC0 (DEL); photos fetched from the survey's YouGov image URLs, rights not stated"


def urls() -> dict[str, str]:
    """File name -> the one URL the .sav shows it at."""
    import pyreadstat

    cols = [tag_var(k, s) for k in SCREENS for s in "AB"]
    df, _ = pyreadstat.read_sav(str(SAV), usecols=cols)
    out: dict[str, str] = {}
    for col in cols:
        for value in df[col].unique():
            m = TAG.fullmatch(value)
            if m is None:
                raise SystemExit(f"{col}: unparsed tag {value!r}")
            url, name = m.groups()
            if out.setdefault(name, url) != url:
                raise SystemExit(f"{name} shown at two URLs")
    if set(out) != set(IMG_NAME_ARR):
        raise SystemExit(f"photos in the data {sorted(out)} != img_name_arr")
    return out


def catalogue_entries() -> dict[str, dict[str, str]]:
    from micromotives_datasets.images import sha256_of

    where = urls()
    out: dict[str, dict[str, str]] = {}
    for name in IMG_NAME_ARR:
        f = f"{IMAGE_DIR}/{name}"
        licence = LICENCE
        if name in EMBEDDED_RIGHTS:
            licence += f"; the file carries {EMBEDDED_RIGHTS[name]}"
        out[image_id(name)] = {
            "file": f,
            "sha256": sha256_of(REPO / "data" / f),
            "source": f"{where[name]} (DEL Sandbox Feb 2023, doi:10.7910/DVN/XZ1XUZ: the "
            f"URL in img1_pair*_A/_B with alt='{name}'; the questionnaire's img_name_arr)",
            "licence": licence + ".",
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


# --- the prepped file ---------------------------------------------------------------


def coded(df: Any) -> Any:
    """Integer code columns for each screen's two pictures, checked on the way."""
    out = df.copy()
    for k in SCREENS:
        for side in "AB":
            names = df[tag_var(k, side)].map(lambda v: TAG.fullmatch(v).group(2))  # type: ignore[union-attr]
            out[code_var(k, side)] = names.map(CODE).astype(float)
    codes = out[[code_var(k, s) for k in SCREENS for s in "AB"]]
    if codes.isna().any().any():
        raise SystemExit("a picture tag did not resolve to a code")
    if not (codes.nunique(axis=1) == 8).all():
        raise SystemExit("a respondent saw the same photo twice")
    return out


def write_derived() -> None:
    import pyreadstat

    df, meta = pyreadstat.read_sav(str(SAV))
    out = coded(df)
    labels = dict(zip(meta.column_names, meta.column_labels, strict=True))
    value_labels = dict(meta.variable_value_labels)
    for k in SCREENS:
        for side in "AB":
            labels[code_var(k, side)] = f"{tag_var(k, side)}, coded by img_name_arr position"
            value_labels[code_var(k, side)] = {float(c): n for n, c in CODE.items()}
    pyreadstat.write_sav(
        out, str(DERIVED), column_labels=labels, variable_value_labels=value_labels
    )
    print(f"wrote {DERIVED.relative_to(REPO)}")


# --- the recipe -------------------------------------------------------------------

QUESTION = (
    "Looking at the two images below, please tell us which pictures shows the person or "
    "people you think {what} the most."
)
NEEDS = "needs help"
DESERVES = "deserves help"
OPTIONS = (
    ' 1 means "Picture A"; 2 means "Both equally"; 3 means "Picture B"; 4 means "Neither of these".'
)
WHAT = {1: NEEDS, 2: NEEDS, 3: DESERVES, 4: DESERVES}
DONT_KNOW, SKIPPED, NOT_ASKED = 5, 8, 9
CONDITION_TEXT = (
    "Two pictures were shown side by side below the question. Picture A: <image> Picture B: <image>"
)


def pairs() -> list[tuple[str, str]]:
    """Every ordered (A, B), A-major, in img_name_arr order: condition_num is the index."""
    return [(a, b) for a, b in itertools.permutations(IMG_NAME_ARR, 2)]


def arms() -> list[dict[str, Any]]:
    out = []
    for n, (a, b) in enumerate(pairs()):
        out.append(
            {
                "raw_values": {code_var(1, "A"): CODE[a], code_var(1, "B"): CODE[b]},
                "condition_num": n,
                "factors": {
                    "person_A": person(a),
                    "framing_A": framing(a),
                    "person_B": person(b),
                    "framing_B": framing(b),
                },
                "text": CONDITION_TEXT,
                "images": [image_id(a), image_id(b)],
            }
        )
    return out


def outcomes() -> list[dict[str, Any]]:
    out = []
    for k in SCREENS:
        o: dict[str, Any] = {
            "var": f"images_{k}",
            "task_num": k - 1,
            "question": QUESTION.format(what=WHAT[k]) + OPTIONS,
            "scale": {"min": 1, "max": 4, "nominal": True},
        }
        if k > 1:
            o["condition_vars"] = [code_var(k, "A"), code_var(k, "B")]
        out.append(o)
    return out


def persona() -> dict[str, Any]:
    src = yaml.safe_load(PERSONA_FROM.read_text())
    return {k: src[k] for k in ("persona_label_rewrite", "persona_map", "persona_missing")}


def recipe() -> dict[str, Any]:
    src = yaml.safe_load(PERSONA_FROM.read_text())
    return {
        "study_id": "del",
        "source": "dataverse",
        "experiment": "sandbox_feb2023_help_pictures",
        "title": "Development Engagement Lab, Sandbox Great Britain February 2023: paired "
        "photographs, which person needs / deserves help the most",
        "data_file": DATA_FILE,
        "licence": src["licence"],
        "comparable_to_socsci210": False,
        "participant_id_var": src["participant_id_var"],
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_vars": [code_var(1, "A"), code_var(1, "B")],
            "factors": ["person_A", "framing_A", "person_B", "framing_B"],
            "arms": arms(),
        },
        "outcomes": outcomes(),
        "response_recode": {1: 1, 2: 2, 3: 3, 4: 4},
        "missing_codes": [DONT_KNOW, SKIPPED, NOT_ASKED],
        **persona(),
    }


def render() -> str:
    return yaml.safe_dump(recipe(), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--prep", action="store_true", help="write the derived .sav")
    ap.add_argument("--catalogue", action="store_true", help="add this study's images.json entries")
    args = ap.parse_args()
    if args.catalogue:
        write_catalogue()
        print("updated data/catalog/images.json (del_feb2023_* entries only)")
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
