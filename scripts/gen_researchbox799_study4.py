#!/usr/bin/env python3
"""Write recipes/images/researchbox799_study4.yaml: wheelchair user in a restaurant ad (IMG73).

Cossu, Estes & Vosgerau, "Beyond Visibility: The Disability Inclusion Effect in
Advertising", Journal of Marketing (2026), doi:10.1177/00222429261447790; preprint
https://openaccess.city.ac.uk/id/eprint/37335/. ResearchBox 799 ("Disability
Inclusion", https://researchbox.org/799, mirrored as Zenodo record 21296065), CC BY
4.0. Study 4 ONLY: "Study 4 Ruling Out Warmth and Coolness" (.sav, .qsf, Qualtrics
PDF, codebook, SPSS syntax, AsPredicted #275889). The box's other studies are US
samples, or pre-tests and post-tests of other stimuli, and are not built here.

455 UK residents on Prolific (the paper: "We recruited 455 UK residents"; the data
hold no country variable, so UK rests on the paper) read a short news brief about a
fictional restaurant chain, Pastamasta Kitchen, and saw its ad, then rated the ad
and the brand (six 0-100 sliders) and the brand's inclusivity (three 1-7 items).

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* DESIGN. Between subjects, three arms. `Group` is an embedded field set by the
  survey flow's even-presentation randomiser (.qsf FL_5): 0 routes to the "Disability
  Forced" blocks, 1 to "Disability Voluntary", 2 to "Control". The .sav labels agree
  (0 " disability-conformity", 1 "disability-divergent", 2 " control"; the paper's
  disability-compliant, disability-divergent, control), and so does the data: each
  group answered only its own block's variables (`*_disability_F_*`, `*_disability_V_*`,
  `*_control_*`; checked in recipe()). The 4 people who chose "Very little" at the
  attention question were ended by the flow before randomisation and have no Group
  and no answers, so they make no rows; 451 people are built, the paper's analytic
  sample.
* WHAT EACH ARM SAW. Each group answered two blocks, attitudes and inclusivity, in
  random order (BlockRandomizer SubSet 2); the order is not recorded and nothing is
  said about it. Every block shows the news brief (a text item: bold headline, then
  the body) and under it the ad (a graphic item), then the questions. The two
  disability arms show the wheelchair picture (Qualtrics graphic IM_beaO66U4W2SbF2u),
  the control arm the same photograph with the wheelchair's wheels removed
  (IM_cwJ36LJe5e18RGS). The pictures are the Qualtrics PDF's own, extracted
  unaltered with poppler's pdfimages (page 3 for the wheelchair ad, page 12 for the
  control ad); the same two files appear on every page of their arms (sha256
  checked when written). The deposit holds no other copy.
* THE CONTROL ARM'S TWO HEADLINES. The control attitudes block's headline is
  "Pastamasta Kitchen Features Patron in Latest Campaign", but the control
  INCLUSIVITY block's headline, in both the .qsf and the Qualtrics PDF, is
  "Pastamasta Kitchen Features Wheelchair-Using Patron in Latest Campaign", above the
  control body ("...to feature a real customer in their campaign.") and the control
  picture. The paper's Figure 6 prints only the first. The fielded instrument is the
  authority, so the three inclusivity items of the control arm carry their own
  page's headline (an item-level `condition_text`); the six attitude items carry the
  attitudes page's. The disability arms show the same brief on both pages. Not
  expressible: about half the control group will have seen the inclusivity page
  first, so they had already read the wheelchair headline when they rated the ad;
  block order is not recorded, so no row says so and none asserts the other page.
* CONDITION. shared_context is the questionnaire's instructions, word-for-word, from
  "We are investigating" to "a couple of questions about it."; dropped as survey
  mechanics: the study length, "This is a serious study..." and "Please proceed when
  you're ready...". Each arm's text quotes its page's headline and body word-for-word
  from the .qsf (HTML stripped, entities resolved; the em dash and the missing comma
  after "Amsterdam" in the control body are the source's), then the ad with the only
  word printed in it, its logo's "pastamasta". Headline, body and ad each take a
  line, as on the page. Words that are OURS: "News brief:" and "The ad, shown
  below it:".
* OUTCOMES. Nine, in the questionnaire's listing order. The ad grid (0-100 sliders,
  "I like this ad.", "The ad is well made.", "My opinion regarding this ad is very
  positive.") is its stem then the statement in quotation marks; the three brand
  sliders are their stems ("...0 (Dislike) to 100 (Like)", Unfavorable/Favorable,
  Bad/Good), which carry no statement; the inclusivity grid (1-7) is its stem then
  the statement. Wording is the .qsf's (HTML stripped), and the generator checks the
  three arms' copies are identical. Scale labels are the .qsf's: the ad grid's
  "Strongly disagree" / "Neither agree nor disagree" / "Strongly agree" at 0 / 50 /
  100, the brand sliders' end labels, the Likert grid's seven answers (recoded
  1..7 by the .qsf's RecodeValues, which the .sav already holds). Slider answers
  are whole numbers (NumDecimals 0; checked). Statement order within each grid
  was randomised per person and is not recorded; each statement is its own row.
  The prereg calls item 1 "the brand promotes inclusivity" and the paper says it
  was rephrased from "sincerely promotes"; what was fielded is "The brand supports
  inclusivity." and that is what the row says.
* NOT BUILT. The attention question (a check, asked before randomisation), the
  Prolific ID (not in the deposit) and the closing comment box.
* WHO. All 451 randomised people. The export has no respondent id, so the id is
  the 0-based row position in the .sav.
* PERSONA. All asked at the end, after the ratings, and mapped as stable facts:
  age (typed in, 18-78), gender (the form offered only Male and Female), whether
  the person has a disability and, if yes, its type (Mental / Physical / Mental and
  physical, the labels word-for-word). No non-answer codes exist; the 57 "No"
  answers simply have no type.
* UK FIT. Fielded in the UK; a fictional chain, a Dutch dateline and a fictional EU
  standard, all presented as news, which a UK respondent reads as news from Europe.
  Nothing requires local knowledge the UK sample lacks.
* NOT ASKED OF JEV. The assignment, persona and non-answer questions recipe_prep.py
  asks are settled here by the .qsf flow, the .sav labels and the data (no paid
  call made).

    uv run python scripts/gen_researchbox799_study4.py --extract    # (re)extract the two ads
    uv run python scripts/gen_researchbox799_study4.py --catalogue  # (re)write its images.json entries
    uv run python scripts/gen_researchbox799_study4.py              # write the recipe
    uv run python scripts/gen_researchbox799_study4.py --check      # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

STUDY_ID = "researchbox799"
EXPERIMENT = "study4"
RAW = REPO / "data" / "raw" / STUDY_ID
DATA_FILE = "Study 4 Ruling Out Warmth and Coolness.sav"
DATA = RAW / "Data" / DATA_FILE
QSF = RAW / "Materials" / "Study 4 Ruling Out Warmth and Coolness.qsf"
PDF = RAW / "Materials" / "Study 4 Ruling Out Warmth and Coolness.pdf"
RECIPE = REPO / "recipes" / "images" / f"{STUDY_ID}_{EXPERIMENT}.yaml"
LICENCE = "CC BY 4.0 (ResearchBox 799, https://researchbox.org/799; Zenodo record 21296065)."

CONDITION_VAR = "Group"

# (canonical arm, Group code, factor level, block suffix in the variable names,
#  attitudes block, inclusivity block, image id)
ARMS = [
    (0, 2, "control", "control", "Control Attitudes", "Control Inclusivity", "control"),
    (
        1,
        1,
        "disability divergent",
        "disability_V",
        "Disability Voluntary Attitudes",
        "Disability Voluntary Inclusivity",
        "wheelchair",
    ),
    (
        2,
        0,
        "disability compliant",
        "disability_F",
        "Disability Forced Attitudes",
        "Disability Forced Inclusivity",
        "wheelchair",
    ),
]

# The ads: image key -> (Qualtrics graphic id, PDF page holding it, file under data/).
IMAGES = {
    "wheelchair": ("IM_beaO66U4W2SbF2u", 3, f"raw/{STUDY_ID}/images/ad_wheelchair.jpg"),
    "control": ("IM_cwJ36LJe5e18RGS", 12, f"raw/{STUDY_ID}/images/ad_control.jpg"),
}
# Every page each ad is on, to check the file extracted is the one shown throughout.
IMAGE_PAGES = {"wheelchair": [3, 6, 8, 10], "control": [12, 15]}
AD_WORDS = "pastamasta"

DESCRIPTIONS = {
    "wheelchair": (
        "Colour photograph, landscape, of people eating together at a long wooden table in "
        "a restaurant with exposed brick walls, shelves and lit candles behind them. The "
        "table holds plates of food, bowls, glasses of red wine, a lit white candle and "
        "napkins. In the foreground on the left a man with short fair hair, in a "
        "blue-and-white striped short-sleeved shirt, light blue shorts and a bracelet, sits "
        "in a manual wheelchair, holding a glass of red wine; the wheelchair's armrest, "
        "push handle and the lower part of one large wheel are in view. Beside him sits a "
        "woman with fair hair tied back, in a blue shirt with round orange earrings, and "
        "across the table a woman with long curly dark hair in a blue blouse holding a "
        "glass of red wine. At the right edge a hand holds a wine glass and a person in a "
        "green striped shirt, seen from behind, is cut off by the frame. In the top right "
        "corner a beige square logo: a spoon and a fork drawn as looping lines, with the "
        'word "pastamasta" in italics beneath. White margins run down the left and right '
        "sides of the picture."
    ),
    "control": (
        "Colour photograph, landscape, of people eating together at a long wooden table in "
        "a restaurant with exposed brick walls, shelves and lit candles behind them. The "
        "table holds plates of food, bowls, glasses of red wine, a lit white candle and "
        "napkins. In the foreground on the left a man with short fair hair, in a "
        "blue-and-white striped short-sleeved shirt, light blue shorts and a bracelet, sits "
        "in a dark chair with a black armrest and a dark panel below it, holding a glass of "
        "red wine. Beside him sits a woman with fair hair tied back, in a blue shirt with "
        "round orange earrings, and across the table a woman with long curly dark hair in a "
        "blue blouse holding a glass of red wine. At the right edge a hand holds a wine "
        "glass and a person in a green striped shirt, seen from behind, is cut off by the "
        "frame. In the top right corner a beige square logo: a spoon and a fork drawn as "
        'looping lines, with the word "pastamasta" in italics beneath. The photograph fills '
        "the frame."
    ),
}


def _text(raw: str) -> str:
    """HTML to plain text. Typography only; words untouched."""
    raw = re.sub(r"<br\s*/?>|</p>", " ", raw)
    raw = re.sub(r"<[^>]+>", "", raw)
    raw = html.unescape(raw).replace("\xa0", " ")
    raw = raw.replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", raw).strip()


def qsf() -> dict[str, Any]:
    out: dict[str, Any] = json.loads(QSF.read_text(encoding="utf-8-sig"))
    return out


def blocks(d: dict[str, Any] | None = None) -> dict[str, list[dict[str, Any]]]:
    """Live block description -> its questions' payloads, in block order. Trash is skipped."""
    d = qsf() if d is None else d
    qs = {
        e["Payload"]["QuestionID"]: e["Payload"]
        for e in d["SurveyElements"]
        if e["Element"] == "SQ"
    }
    bl = next(e["Payload"] for e in d["SurveyElements"] if e["Element"] == "BL")
    bl = bl.values() if isinstance(bl, dict) else bl
    out: dict[str, list[dict[str, Any]]] = {}
    for b in bl:
        if b["Type"] == "Trash":
            continue
        out[b["Description"].strip()] = [
            qs[x["QuestionID"]] for x in b.get("BlockElements", []) if x["Type"] == "Question"
        ]
    return out


def page(block: str) -> tuple[str, str, str]:
    """(headline, body, graphic id) of a block's news brief and ad."""
    items = blocks()[block]
    brief = next(p for p in items if p["QuestionType"] == "DB" and p["Selector"] == "TB")
    graphic = next(p for p in items if p["QuestionType"] == "DB" and p["Selector"] == "GRB")
    m = re.match(r"\s*<strong>(.*?)</strong>(.*)", brief["QuestionText"], re.S)
    if not m:
        raise SystemExit(f"{block}: brief has no bold headline")
    return _text(m.group(1)), _text(m.group(2)), graphic["Graphics"]


SHARED_FROM = "We are investigating"
SHARED_TO = "a couple of questions about it."


def shared_context() -> str:
    text = _text(blocks()["Instructions"][0]["QuestionText"])
    start = text.index(SHARED_FROM)
    end = text.index(SHARED_TO) + len(SHARED_TO)
    return text[start:end]


def arm_text(headline: str, body: str) -> str:
    return f'News brief:\n{headline}\n{body}\nThe ad, shown below it: "{AD_WORDS}" <image>'


# Outcome items: (task, variable stem as the .sav names it, qsf export tag stem,
#  choice key in that question or None). Variable for arm suffix s: stem.format(s).
OUTCOME_ITEMS = [
    (0, "Ad_{}_1", "Ad_{}", "1"),
    (1, "Ad_{}_2", "Ad_{}", "2"),
    (2, "Ad_{}_3", "Ad_{}", "3"),
    (3, "Brand1_{}_1", "Brand1_{}", None),
    (4, "Brand2_{}_1", "Brand2_{}", None),
    (5, "Brand3_{}_1", "Brand3_{}", None),
    (6, "{}_1", "{}", "1"),
    (7, "{}_2", "{}", "3"),
    (8, "{}_3", "{}", "4"),
]
INCLUSIVITY_TASKS = {6, 7, 8}


def incl_stem(suffix: str) -> str:
    return "Inclus_control" if suffix == "control" else f"Incl_{suffix}"


def var_for(task: int, suffix: str) -> str:
    _, var, _, _ = OUTCOME_ITEMS[task]
    return var.format(incl_stem(suffix)) if task in INCLUSIVITY_TASKS else var.format(suffix)


def tag_for(task: int, suffix: str) -> str:
    _, _, tag, _ = OUTCOME_ITEMS[task]
    return tag.format(incl_stem(suffix)) if task in INCLUSIVITY_TASKS else tag.format(suffix)


def _by_tag(d: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    """Export tag -> payload, LIVE blocks only.

    The .qsf's Trash block holds earlier copies under the same tags (QID142
    `Incl_disability_V`, QID151 `Inclus_control`); a lookup over every element would
    let file order decide which wording is read. A tag shared by two LIVE questions
    (the survey's own "Q50" is both a text item and the age question) is left out, so
    looking it up fails rather than picking one.
    """
    seen: dict[str, list[dict[str, Any]]] = {}
    for items in blocks(d).values():
        for p in items:
            seen.setdefault(p.get("DataExportTag"), []).append(p)
    return {tag: ps[0] for tag, ps in seen.items() if len(ps) == 1}


def _labels(p: dict[str, Any]) -> list[str]:
    return [_text(v["Display"]) for _, v in sorted(p["Labels"].items(), key=lambda kv: int(kv[0]))]


def question_and_scale(task: int, suffix: str) -> tuple[str, dict[str, Any]]:
    p = _by_tag()[tag_for(task, suffix)]
    stem = _text(p["QuestionText"])
    choice = OUTCOME_ITEMS[task][3]
    if choice is not None:
        q = f'{stem} "{_text(p["Choices"][choice]["Display"])}"'
    else:
        if [_text(c["Display"]) for c in p["Choices"].values()] != [""]:
            raise SystemExit(f"{tag_for(task, suffix)}: expected a single unlabelled slider")
        q = stem
    if p["QuestionType"] == "Slider":
        cfg = p["Configuration"]
        if (cfg["CSSliderMin"], cfg["CSSliderMax"], str(cfg["NumDecimals"])) != (0, 100, "0"):
            raise SystemExit(f"{tag_for(task, suffix)}: slider is not 0-100 whole numbers")
        shown = [x for x in _labels(p) if x]
        scale: dict[str, Any] = {"min": 0, "max": 100, "min_label": shown[0]}
        scale["max_label"] = shown[-1]
        if len(shown) == 3:
            scale["mid_label"] = shown[1]
        return q, scale
    answers = p["Answers"]
    recode = p["RecodeValues"]
    ordered = sorted(answers, key=lambda k: int(recode[k]))
    if [int(recode[k]) for k in ordered] != list(range(1, 8)):
        raise SystemExit(f"{tag_for(task, suffix)}: answers do not recode to 1..7")
    labels = [_text(answers[k]["Display"]) for k in ordered]
    return q, {
        "min": 1,
        "max": 7,
        "min_label": labels[0],
        "max_label": labels[-1],
        "mid_label": labels[3],
    }


def extract_images() -> None:
    """Pull the two ads out of the Qualtrics PDF and check every page shows the same file."""
    import hashlib

    out = RAW / "images"
    out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        digests: dict[str, set[str]] = {}
        for key, pages in IMAGE_PAGES.items():
            for pg in pages:
                prefix = f"{tmp}/{key}_{pg}"
                subprocess.run(
                    ["pdfimages", "-j", "-f", str(pg), "-l", str(pg), str(PDF), prefix], check=True
                )
                first = Path(f"{prefix}-000.jpg")
                digests.setdefault(key, set()).add(hashlib.sha256(first.read_bytes()).hexdigest())
                if pg == IMAGES[key][1]:
                    (REPO / "data" / IMAGES[key][2]).write_bytes(first.read_bytes())
        for key, ds in digests.items():
            if len(ds) != 1:
                raise SystemExit(f"{key}: pages {IMAGE_PAGES[key]} do not show the same file")


def image_id(key: str) -> str:
    return f"{STUDY_ID}_study4_ad_{key}"


def catalogue_entries() -> dict[str, dict[str, str]]:
    from micromotives_datasets.images import sha256_of

    out: dict[str, dict[str, str]] = {}
    for key, (graphic, pg, f) in IMAGES.items():
        out[image_id(key)] = {
            "file": f,
            "sha256": sha256_of(REPO / "data" / f),
            "source": "https://researchbox.org/799 (Zenodo record 21296065, ResearchBox_799.zip): "
            "Materials/Study 4 Ruling Out Warmth and Coolness.pdf, page "
            f"{pg}, first image, extracted unaltered with poppler pdfimages -j; Qualtrics "
            f"graphic {graphic} in the .qsf; shown on pages {IMAGE_PAGES[key]}",
            "licence": LICENCE,
            "text_in_image": AD_WORDS,
            "description": DESCRIPTIONS[key],
        }
    return out


def write_catalogue() -> None:
    """Add or refresh only this study's entries; re-read first, others are editing too."""
    path = REPO / "data" / "catalog" / "images.json"
    current = json.loads(path.read_text())
    current.update(catalogue_entries())
    path.write_text(json.dumps(current, indent=2, ensure_ascii=False))


def recipe() -> dict[str, Any]:
    ds = read_any(DATA)
    df = ds.df
    codes = {int(c) for c in df[CONDITION_VAR].dropna().unique()}
    if codes != {a[1] for a in ARMS}:
        raise SystemExit(f"Group codes changed: {sorted(codes)}")
    # Each group answered only its own block's variables.
    for _, raw, _, suffix, *_ in ARMS:
        for other in ARMS:
            for task in range(len(OUTCOME_ITEMS)):
                col = df[var_for(task, other[3])]
                filled = int(col[df[CONDITION_VAR] == raw].notna().sum())
                want = int((df[CONDITION_VAR] == raw).sum()) if other[3] == suffix else 0
                if filled != want:
                    raise SystemExit(f"Group {raw}: {var_for(task, other[3])} has {filled} answers")
                if task < 6:
                    vals = col.dropna()
                    if not ((vals % 1 == 0) & (vals >= 0) & (vals <= 100)).all():
                        raise SystemExit(f"{var_for(task, other[3])}: not whole numbers 0-100")

    outcomes = []
    for task in range(len(OUTCOME_ITEMS)):
        versions = {question_and_scale(task, a[3])[0] for a in ARMS}
        if len(versions) != 1:
            raise SystemExit(f"task {task}: arms word the question differently: {versions}")
        q, scale = question_and_scale(task, ARMS[0][3])
        outcomes.append(
            {
                "task_num": task,
                "question": q,
                "scale": scale,
                "response_recode": {i: i for i in range(scale["min"], scale["max"] + 1)},
            }
        )

    arms = []
    for num, raw, level, suffix, att_block, incl_block, img in ARMS:
        head, body, graphic = page(att_block)
        if graphic != IMAGES[img][0]:
            raise SystemExit(f"{att_block}: shows {graphic}, expected {IMAGES[img][0]}")
        ihead, ibody, igraphic = page(incl_block)
        if (ibody, igraphic) != (body, graphic):
            raise SystemExit(f"{incl_block}: body or picture differs from {att_block}")
        items: dict[int, dict[str, Any]] = {}
        for task in range(len(OUTCOME_ITEMS)):
            item: dict[str, Any] = {"outcome_var": var_for(task, suffix)}
            if ihead != head and task in INCLUSIVITY_TASKS:
                item["condition_text"] = arm_text(ihead, ibody)
            items[task] = item
        arms.append(
            {
                "raw": raw,
                "condition_num": num,
                "factors": {"inclusion": level},
                "text": arm_text(head, body),
                "images": [image_id(img)],
                "items": items,
            }
        )
    # Only the control arm's two pages disagree, and only in the headline.
    differing = [
        a["condition_num"] for a in arms if any("condition_text" in i for i in a["items"].values())
    ]
    if differing != [0]:
        raise SystemExit(f"expected only the control arm's headlines to differ, got {differing}")

    return {
        "study_id": STUDY_ID,
        "source": "researchbox",
        "experiment": EXPERIMENT,
        "title": "Wheelchair user in a restaurant ad: a news brief and ad for a fictional "
        "restaurant chain, with the diner's wheelchair edited out, shown, or shown to comply "
        "with an EU advertising standard; attitudes to the ad and brand, and the brand's "
        "inclusivity",
        "data_file": DATA_FILE,
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_var": CONDITION_VAR,
            "factors": ["inclusion"],
            "shared_context": shared_context(),
            "arms": arms,
        },
        "outcomes": outcomes,
        "response_recode": {},
        "persona_map": {
            "age": "Age",
            "gender": "Gender",
            "has_a_disability": "Disability_have",
            "type_of_disability": "Disability_type",
        },
    }


def render() -> str:
    return yaml.safe_dump(recipe(), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--extract", action="store_true", help="extract the two ads from the PDF")
    ap.add_argument("--catalogue", action="store_true", help="add this study's images.json entries")
    args = ap.parse_args()
    if args.extract:
        extract_images()
        print(f"wrote data/raw/{STUDY_ID}/images/ad_wheelchair.jpg and ad_control.jpg")
        return 0
    if args.catalogue:
        write_catalogue()
        print(f"updated data/catalog/images.json ({STUDY_ID} study 4 entries only)")
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
