#!/usr/bin/env python3
"""Write recipes/images/wsqyn.yaml: the Restrain Food Database validation study (IMG34).

Randle, Duarte, Maizey, Tzavella, Adams & Chambers (Cardiff), "The Restrain Food
Database: validation of an open-source database of foods that should be eaten more
or less as part of a healthy diet", Royal Society Open Science 9:220923 (2022).
OSF 7gcsk (project, CC BY 4.0); this study's materials and data are its component
wsqyn (CC BY 4.0). Answer key: the paper's Tables 1, 3, 4 and 5 (PMC9682305).

2,150 UK adults (Prolific, March 2022; the authors' pre-registered sample after
excluding 19 incomplete and 148 too-fast participants) were each allocated to 1 of
52 sets of 10 food photographs. Every photograph was rated on three pages: page A
(taste, craving, healthiness), page B (eat more or less, frequency, five nutrient
ratings) and page C (recognition, image quality, positivity). A and B came in
random order, all 10 foods per page type before the next; C was always last.

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* INSTRUMENT. The Qualtrics export in the deposit (VSM_Validation_Study.qsf) is the
  authority for every word. The paper paraphrases the instructions and gives the
  taste anchor as "Extremely"; the fielded question says "Very much".
* WHAT WAS ON SCREEN. Each page showed one photograph with the food's name as a
  heading above it (paper section 3.1.5 and figure 4: "the image is presented in
  the middle of the screen with a description presented above"), then the page's
  questions. The heading is the page's own descriptive-text question, quoted
  word-for-word after removing HTML and non-breaking spaces. It differs between the
  three pages of the same food in 215 of 520 foods, mostly in capitals ("Apple Pie"
  on A, "Apple pie" on C) but sometimes in words ("Macaroni" on A and B, "Macaroni
  & cheese" on C; "Spinache" on A and B), so each page keeps its own.
* PHOTOGRAPHS. The deposit's .qsf names each page's picture by its Qualtrics
  library id; the pictures were fetched from the survey's own library
  (cardiffunipsych.eu.qualtrics.com/ControlPanel/Graphic.php?IM=<id>), so each
  row cites the exact file its page served, not the database's full-size copy.
  744 distinct files. In 514 foods the three pages show the same photograph,
  sometimes as separately uploaded copies whose bytes differ (re-encoded; the
  catalogue says so per image). In 6 foods the C page shows a DIFFERENT photograph
  from A and B (e.g. "Vegetable thai red curry" C shows the prawn curry photograph
  that "Prawn thai red curry" uses; "Hamburger" C shows a hamburger meal). Rows
  cite what each page showed; nothing is corrected.
* ARMS. One arm per distinct (heading, image file): 853 arms. An arm is shared
  wherever heading and file are identical: across the pages of one food, and in
  two places across foods ("Hamburger" in sets 46 and 47 is the same photograph
  under the same heading). Factors: `photo` (the image id, expressed only by the
  picture) and `heading`. Hold out by condition_num or image id, never by
  condition string; re-encoded copies of one photograph have different ids, and
  the catalogue names the copy each one repeats. Because one food spans several
  arms (294 of 520 foods), data/catalog/wsqyn_food_groups.json (written here)
  maps every condition_num to its set_item and database FoodID: a held-out image
  split must group by those.
* PAIRING PAGES TO FOODS. In each set's flow branch the A, B and C randomisers list
  10 blocks each; the k-th block of each is food k (the block descriptions are
  unreliable: "A455" occurs twice, "B417 " has a trailing space). This pairing was
  checked against the authors' own column header (vsm-header.rds) for all 1,560
  pages, and every answer written here is checked below against the authors'
  primary-analysis file, cell by cell.
* DATA. Derived file data/raw/wsqyn/wsqyn_long.csv, written by this script from the
  raw Qualtrics export: one row per (person, food), 21,500 rows, holding the arm
  code of each page, every answer as the instrument's own choice code (looked up
  by label), and the persona codes. Answers are read by each column's ImportId,
  never by the authors' renamed headers. Sample = the ProlificIDs in
  Final_data_primary_analyses.csv (the paper's analysed sample). 41 of them also
  left an abandoned second attempt in the export; as the authors do, the attempt
  that reached the attention check is used. The participant id is the Qualtrics
  ResponseId, so no Prolific id enters the corpus.
* OUTCOMES. 13 per food, wording word-for-word from the .qsf; slider endpoint
  labels are the sliders' own. "Drag the slider to respond" (the slider's handle
  label) is mechanics and dropped. Page B's grid asks one question with five rows
  (Calories, Fat, Saturated fat, Sugar, Salt); per docs/CONVENTIONS.md "One stem,
  several labelled answer fields" each row is an outcome, and the question gets
  ONE added sentence, ours: 'Report only the rating for "<row label>".' The
  frequency question's five options and the two nominal questions' options are
  enumerated as "Options: 1 = ..." (the codes are the instrument's). Image
  quality is coded as offered, 1 Good, 2 Okay, 3 Bad. The grid's fifth row reads
  "Salt" on 519 pages and "Vitamins & minerals" on one (B257, "Vegetable Thai Red
  Curry", set 26); that arm's fifth row quotes its own label (41 rows). The
  authors' header calls the column "RateVM" and their paper reports it as salt.
* CONDITION. shared_context quotes the task instructions word-for-word, dropping
  only "Click the arrow at the bottom right of the screen to begin the study." as
  survey mechanics. Words that are OURS: 'The food was shown in the centre of the
  screen, under the heading "<heading>":' (the paper's figure 4 description).
* PERSONA. All asked before the ratings (Demographics, then Hunger). Mapped: age,
  sex (Prefer not to say = missing), ethnicity (18 options, scheme uk_wsqyn_osf),
  dietary status (the four options word-for-word), diagnosed eating disorder now
  or in the past (Yes/No), hunger (0-100 in steps of 10), and BMI computed by the
  authors' own formula from the self-reported weight and height (kg, or stones x
  6.350293 + pounds / 2.2046; cm, or feet x 30.48 + inches x 2.54), rounded to one
  decimal, and left absent where the authors' analysis script drops it (<= 10 or
  >= 90). NOT mapped: dietary requirements (in this sample only "Diabetic", 51
  people; others were excluded by the authors), UK residence (a screener).
* NOT BUILT. Page timings; the attention check (after the task, and a check).
* CROSSCHECK (29 Oct 2026, on the built rows). Every answer, age, hunger and BMI
  equals the authors' primary-analysis file (checked in this script). Against the
  paper: craving, healthiness and taste by Eat More / Eat Less (Table 4) agree to
  0.01 (e.g. healthiness 86.43 vs 86.43 and 20.02 vs 20.03); all 30 subcategory
  means (Table 5) within 0.02, the same differences the authors' own file shows,
  so the paper's tables come from a marginally different extract. Age 42.09
  (13.91), sex 58.60 / 40.93 / 0.47 %, dietary status 1025 / 962 / 110 / 53, all as
  Tables 1 and 3. BMI is 26.89 (s.d. 6.08) on 2,144 people against the paper's
  26.90 (6.98): the s.d. is not reproduced by any cut of the deposited BMI. Two
  kept values (10.2, 10.5) pass the authors' rule but are implausible.

    uv run python scripts/gen_wsqyn.py            # write the derived file and recipe
    uv run python scripts/gen_wsqyn.py --check    # exit 1 if either differs
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import re
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "wsqyn"
QSF = RAW / "Qualtrics survey" / "VSM_Validation_Study.qsf"
EXPORT = RAW / "Raw Data" / "VSM Validation Study Final Raw.csv"
PRIMARY = RAW / "Summary data" / "Final_data_primary_analyses.csv"
GRAPHICS = RAW / "qualtrics_graphics"
LONG_NAME = "wsqyn_long.csv"
LONG = RAW / LONG_NAME
RECIPE = REPO / "recipes" / "images" / "wsqyn.yaml"
IMAGES = REPO / "data" / "catalog" / "images.json"
STIM = RAW / "Raw Data" / "VSM stim order.csv"
GROUPS = REPO / "data" / "catalog" / "wsqyn_food_groups.json"

INSTRUCTIONS = (
    "In the following section, you will be asked to rate a series of food images. "
    "Each image, along with a brief description of the food item (e.g. ‘apple pie’), will be "
    "presented with rating questions underneath the image. It is important that you think "
    "about each question carefully, but do not take too long to provide an answer."
)
SHARED = f'The instructions read: "{INSTRUCTIONS}"'
ARM_TEXT = 'The food was shown in the centre of the screen, under the heading "{heading}": <image>'
GRID_SENTENCE = 'Report only the rating for "{row}".'

# Each outcome: (column, page, question key in the page, row of the grid or None).
# Question keys are matched against the .qsf question text, never assumed.
PAGE_QUESTIONS = {
    "A": {
        "taste": "How strongly do you like the taste of this food?",
        "craving": "How strongly have you craved this food over the past 7 days?",
        "healthy": "How healthy do you think this food is?",
    },
    "B": {
        "diet": "What is a better choice for a healthier diet?",
        "freq": "How often have you eaten this food over the past 7 days?",
        "grid": "Please rate the food according to each scale presented below",
    },
    "C": {
        "recognise": "Do you recognise this food?",
        "quality": "How do you rate the quality of the image",
        "positive": "How positive do you rate the image?",
    },
}
GRID_ROWS = ["Calories", "Fat", "Saturated fat", "Sugar", "Salt"]
# (data column, page, question key, grid row)
OUTCOMES: list[tuple[str, str, str, str | None]] = [
    ("taste", "A", "taste", None),
    ("craving", "A", "craving", None),
    ("healthy", "A", "healthy", None),
    ("diet", "B", "diet", None),
    ("freq", "B", "freq", None),
    *[(f"grid_{i + 1}", "B", "grid", row) for i, row in enumerate(GRID_ROWS)],
    ("recognise", "C", "recognise", None),
    ("quality", "C", "quality", None),
    ("positive", "C", "positive", None),
]
SLIDERS = {"taste", "craving", "healthy", "positive"}

# Persona questions (data column, .qsf export tag). Codes are the .qsf choice codes.
PERSONA_TAGS = {
    "sex": "Q2.2",
    "ethnicity": "Q2.3",
    "eating_disorder": "Q2.11",
    "dietary_status": "Q2.12",
}
HUNGER_TAG = "Q3.1"
AGE_TAG = "Q2.1"
WEIGHT_TAGS = ("Q2.6", "Q2.7")  # kg; stones and pounds
HEIGHT_TAGS = ("Q2.9", "Q2.10")  # cm; feet and inches
BMI_DROP = (10.0, 90.0)  # the authors' analysis script: BMI <= 10 or >= 90 -> NA


def clean(text: str) -> str:
    """Rendered words of a .qsf HTML string: tags removed, entities and nbsp resolved."""
    t = re.sub(r"<br\s*/?>", " ", text)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t).replace("\xa0", " ")
    return re.sub(r"\s+", " ", t).strip()


def load_qsf() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(QSF.read_text(encoding="utf-8"))
    return data


def survey(qsf: dict[str, Any]) -> dict[str, Any]:
    """Questions, blocks and the per-set page structure from the .qsf."""
    els = qsf["SurveyElements"]
    qs = {e["PrimaryAttribute"]: e["Payload"] for e in els if e["Element"] == "SQ"}
    bl = next(e for e in els if e["Element"] == "BL")["Payload"]
    blocks = list(bl.values()) if isinstance(bl, dict) else bl
    by_id = {b["ID"]: b for b in blocks}

    pages: dict[str, dict[str, Any]] = {}
    for b in blocks:
        qids = [e["QuestionID"] for e in b.get("BlockElements", []) if e["Type"] == "Question"]
        graphic = [q for q in qids if qs[q]["QuestionType"] == "DB" and qs[q].get("Graphics")]
        if len(graphic) != 1:
            continue
        found: dict[str, str] = {}
        for page, wanted in PAGE_QUESTIONS.items():
            for key, words in wanted.items():
                hits = [q for q in qids if clean(qs[q]["QuestionText"]).startswith(words)]
                if len(hits) == 1:
                    found[f"{page}:{key}"] = hits[0]
        if not found:  # the attention check's picture of fruit: not a rating page
            continue
        kinds = {k.split(":")[0] for k in found}
        if len(kinds) != 1 or len(found) != len(PAGE_QUESTIONS[next(iter(kinds))]):
            raise SystemExit(f"block {b['Description']!r}: questions not recognised {found}")
        page = kinds.pop()
        pages[b["ID"]] = {
            "page": page,
            "heading": clean(qs[graphic[0]]["QuestionText"]),
            "graphic": qs[graphic[0]]["Graphics"],
            "questions": {k.split(":")[1]: q for k, q in found.items()},
        }

    flow = next(e for e in els if e["Element"] == "FL")["Payload"]["Flow"]
    sets: dict[int, dict[str, list[str]]] = {}
    for node in flow:
        if node["Type"] != "Branch":
            continue
        logic = node["BranchLogic"]["0"]["0"]
        if logic.get("LeftOperand") != "Set":
            continue
        s = int(str(logic["RightOperand"]).strip())
        lists: list[list[str]] = []

        def walk(n: dict[str, Any], out: list[list[str]] = lists) -> None:
            kids = n.get("Flow", [])
            if n["Type"] == "BlockRandomizer" and kids and all("ID" in k for k in kids):
                out.append([k["ID"] for k in kids])
                return
            for k in kids:
                walk(k)

        walk(node)
        for ids in lists:
            kinds = {pages[i]["page"] for i in ids}
            if len(kinds) != 1 or len(ids) != 10:
                raise SystemExit(f"set {s}: a randomiser is not 10 blocks of one page type")
            sets.setdefault(s, {})[kinds.pop()] = ids
    if sorted(sets) != list(range(1, 53)) or any(
        sorted(v) != ["A", "B", "C"] for v in sets.values()
    ):
        raise SystemExit("flow does not give 52 sets of A, B and C pages")
    return {"qs": qs, "pages": pages, "sets": sets, "blocks": by_id}


def image_ids() -> dict[str, str]:
    """sha256 -> catalogue id, for this study's images."""
    cat = json.loads(IMAGES.read_text(encoding="utf-8"))
    return {v["sha256"]: k for k, v in cat.items() if k.startswith("wsqyn_")}


def graphic_file(graphic: str) -> Path:
    hits = sorted(GRAPHICS.glob(f"{graphic}.*"))
    if len(hits) != 1:
        raise SystemExit(f"graphic {graphic}: expected one file, found {hits}")
    return hits[0]


def choice_codes(payload: dict[str, Any], field: str = "Choices") -> dict[str, int]:
    return {clean(v["Display"]): int(k) for k, v in payload[field].items()}


def read_export() -> tuple[list[str], list[str], list[list[str]]]:
    with EXPORT.open(encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f)
        tags = next(r)
        next(r)
        imports = [json.loads(x)["ImportId"] for x in next(r)]
        rows = list(r)
    return tags, imports, rows


def bmi(row: dict[str, str]) -> float | None:
    """The authors' formula (convert.R), on the raw self-reports."""

    def num(x: str) -> float | None:
        try:
            return float(x)
        except ValueError:
            return None

    kg = num(row["kg"])
    if kg is None and num(row["stones"]) is not None and num(row["pounds"]) is not None:
        kg = round(num(row["stones"]) * 6.350293 + num(row["pounds"]) / 2.2046, 2)  # type: ignore[operator]
    cm = num(row["cm"])
    if cm is None and num(row["feet"]) is not None and num(row["inches"]) is not None:
        cm = round(num(row["feet"]) * 30.48 + num(row["inches"]) * 2.54, 2)  # type: ignore[operator]
    if kg is None or not cm:
        return None
    return round(kg / (cm / 100) ** 2, 2)


def derive() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """The long file's rows, the arms, and the codes the recipe needs."""
    qsf = load_qsf()
    sv = survey(qsf)
    qs, pages, sets = sv["qs"], sv["pages"], sv["sets"]
    sha_to_id = image_ids()

    # Arms: one per distinct (heading, image), in order of first appearance.
    arm_of: dict[str, int] = {}
    arms: list[dict[str, Any]] = []
    image_of: dict[str, str] = {}
    for s in range(1, 53):
        for k in range(10):
            for page in "ABC":
                bid = sets[s][page][k]
                p = pages[bid]
                if p["graphic"] not in image_of:
                    digest = hashlib.sha256(graphic_file(p["graphic"]).read_bytes()).hexdigest()
                    if digest not in sha_to_id:
                        raise SystemExit(f"{p['graphic']} is not in the image catalogue")
                    image_of[p["graphic"]] = sha_to_id[digest]
                key = (p["heading"], image_of[p["graphic"]])
                code = next((a["condition_num"] for a in arms if a["_key"] == key), None)
                if code is None:
                    code = len(arms)
                    arms.append({"_key": key, "condition_num": code})
                arm_of[bid] = code
                arms[code].setdefault("_foods", set()).add((s, k + 1))

    # Answer codes, from the .qsf, by label.
    first = {page: pages[sets[1][page][0]]["questions"] for page in "ABC"}
    codes = {
        "diet": choice_codes(qs[first["B"]["diet"]]),
        "freq": choice_codes(qs[first["B"]["freq"]]),
        "grid": choice_codes(qs[first["B"]["grid"]], "Answers"),
        "grid_rows": choice_codes(qs[first["B"]["grid"]]),
        "recognise": choice_codes(qs[first["C"]["recognise"]]),
        "quality": choice_codes(qs[first["C"]["quality"]]),
    }
    if list(codes["grid_rows"]) != GRID_ROWS:
        raise SystemExit(f"grid rows changed: {list(codes['grid_rows'])}")
    for bid, p in pages.items():  # every page must offer the same options
        for key in ("diet", "freq", "recognise", "quality"):
            if key in p["questions"] and choice_codes(qs[p["questions"][key]]) != codes[key]:
                raise SystemExit(f"{bid}: {key} options differ")
        if "grid" in p["questions"]:
            g = qs[p["questions"]["grid"]]
            rows_here = choice_codes(g)
            if choice_codes(g, "Answers") != codes["grid"] or sorted(rows_here.values()) != [
                1,
                2,
                3,
                4,
                5,
            ]:
                raise SystemExit(f"{bid}: grid differs")
            if list(rows_here) != GRID_ROWS:
                # One page (B257, "Vegetable Thai Red Curry") asks "Vitamins & minerals"
                # where every other page asks "Salt"; its arm says so for that row.
                arm = arms[arm_of[bid]]
                labels = sorted(rows_here, key=lambda lab: rows_here[lab])
                if arm.setdefault("grid_rows", labels) != labels:
                    raise SystemExit(f"{bid}: arm shared by B pages with different grid rows")

    tags, imports, rows = read_export()
    col = {imp: i for i, imp in enumerate(imports)}
    tag_col = {t: i for i, t in enumerate(tags)}

    def qcol(qid: str, sub: str | int | None = None) -> int:
        return col[qid if sub is None else f"{qid}_{sub}"]

    by_tag = {p.get("DataExportTag"): q for q, p in qs.items()}
    persona_codes = {f: choice_codes(qs[by_tag[t]]) for f, t in PERSONA_TAGS.items()}

    sample = set()
    with PRIMARY.open(encoding="utf-8", newline="") as f:
        primary = list(csv.DictReader(f))
    for r in primary:
        sample.add(r["ProlificID"])
    pid_i, set_i = tag_col["ProlificID"], tag_col["Set"]
    # 41 analysed people also left an earlier or later abandoned attempt in the export.
    # The authors keep the attempt that reached the attention check (convert.R,
    # drop_na(AttentionCheck)); so does this.
    check_i = tag_col["Q6842"]
    chosen = [r for r in rows if r[pid_i] in sample and r[check_i]]
    if len(chosen) != len(sample) or len({r[pid_i] for r in chosen}) != len(sample):
        raise SystemExit("each analysed ProlificID must have exactly one export row")

    def persona(r: list[str]) -> dict[str, Any]:
        out: dict[str, Any] = {"age": int(r[qcol(by_tag[AGE_TAG], "TEXT")])}
        for field, tag in PERSONA_TAGS.items():
            v = r[qcol(by_tag[tag])]
            out[field] = persona_codes[field][v] if v else ""
        out["hunger"] = int(r[qcol(by_tag[HUNGER_TAG], 1)])
        raw = {
            "kg": r[qcol(by_tag[WEIGHT_TAGS[0]], "TEXT")],
            "stones": r[qcol(by_tag[WEIGHT_TAGS[1]], 1)],
            "pounds": r[qcol(by_tag[WEIGHT_TAGS[1]], 2)],
            "cm": r[qcol(by_tag[HEIGHT_TAGS[0]], "TEXT")],
            "feet": r[qcol(by_tag[HEIGHT_TAGS[1]], 1)],
            "inches": r[qcol(by_tag[HEIGHT_TAGS[1]], 2)],
        }
        b = bmi(raw)
        out["_bmi_authors"] = b
        out["bmi"] = "" if b is None or not BMI_DROP[0] < b < BMI_DROP[1] else f"{b:.1f}"
        return out

    long_rows: list[dict[str, Any]] = []
    for r in chosen:
        s = int(r[set_i])
        who = persona(r)
        for k in range(10):
            row: dict[str, Any] = {"response_id": r[tag_col["ResponseId"]], "set": s, "item": k + 1}
            for page in "ABC":
                row[f"arm_{page}"] = arm_of[sets[s][page][k]]
            qa = pages[sets[s]["A"][k]]["questions"]
            qb = pages[sets[s]["B"][k]]["questions"]
            qc = pages[sets[s]["C"][k]]["questions"]
            row["taste"] = r[qcol(qa["taste"], 1)]
            row["craving"] = r[qcol(qa["craving"], 1)]
            row["healthy"] = r[qcol(qa["healthy"], 1)]
            row["diet"] = codes["diet"].get(r[qcol(qb["diet"])], "")
            row["freq"] = codes["freq"].get(r[qcol(qb["freq"])], "")
            for i in range(5):
                row[f"grid_{i + 1}"] = codes["grid"].get(r[qcol(qb["grid"], i + 1)], "")
            row["recognise"] = codes["recognise"].get(r[qcol(qc["recognise"])], "")
            row["quality"] = codes["quality"].get(r[qcol(qc["quality"])], "")
            row["positive"] = r[qcol(qc["positive"], 1)]
            row.update(who)
            row["_prolific"] = r[pid_i]
            long_rows.append(row)

    _check_against_primary(long_rows, primary, codes)
    for row in long_rows:
        del row["_prolific"]
        del row["_bmi_authors"]

    meta = {"codes": codes, "persona_codes": persona_codes, "image_of": image_of}
    return long_rows, arms, meta


def _check_against_primary(
    long_rows: list[dict[str, Any]], primary: list[dict[str, str]], codes: dict[str, Any]
) -> None:
    """Every answer must equal the authors' primary-analysis file, cell by cell.

    The authors mapped columns by a hand-built header; this script by ImportId and
    flow position. Agreement on every cell is the independent check on the pairing.
    """
    inv = {k: {v: lab for lab, v in m.items()} for k, m in codes.items() if k != "grid_rows"}
    theirs = {(r["ProlificID"], int(r["Set"]), int(r["Item"])): r for r in primary}
    pairs = [
        ("taste", "Taste", None),
        ("craving", "Cravings", None),
        ("healthy", "Healthiness", None),
        ("positive", "Positivity", None),
        ("diet", "HealthyDiet", "diet"),
        ("freq", "FreqofConsumption", "freq"),
        ("grid_1", "CalorieEstimate", "grid"),
        ("grid_2", "FatEstimate", "grid"),
        ("grid_3", "SaturatedFatEstimate", "grid"),
        ("grid_4", "SugarEstimate", "grid"),
        ("grid_5", "VitaminsMineralsEstimate", "grid"),
        ("recognise", "Recognisability", "recognise"),
        ("quality", "QualityofImage", "quality"),
    ]
    bad = 0
    for row in long_rows:
        t = theirs.get((row["_prolific"], row["set"], row["item"]))
        if t is None:
            raise SystemExit(f"no authors' row for set {row['set']} item {row['item']}")
        for mine, col, code in pairs:
            v = row[mine]
            mine_val = str(v) if code is None else inv[code].get(v, "")
            if mine_val != t[col]:
                bad += 1
        if str(row["age"]) != t["Age"] or str(row["hunger"]) != t["Hunger"]:
            bad += 1
        b = row["_bmi_authors"]
        if b is not None and abs(b - float(t["BMI"])) > 0.011:
            bad += 1
    if bad or len(long_rows) != len(primary):
        raise SystemExit(f"{bad} cells differ from the authors' primary-analysis file")


def long_csv(long_rows: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(long_rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(long_rows)
    return buf.getvalue()


def recipe(arms: list[dict[str, Any]], meta: dict[str, Any]) -> dict[str, Any]:
    qsf = load_qsf()
    qs = survey(qsf)["qs"]
    codes = meta["codes"]

    def slider(column: str, text_qid: str) -> dict[str, Any]:
        p = qs[text_qid]
        cfg = p["Configuration"]
        return {
            "question": clean(p["QuestionText"]),
            "scale": {
                "min": int(cfg["CSSliderMin"]),
                "max": int(cfg["CSSliderMax"]),
                "min_label": clean(p["Labels"]["1"]["Display"]),
                "max_label": clean(p["Labels"]["2"]["Display"]),
            },
            "response_recode": {
                i: i for i in range(int(cfg["CSSliderMin"]), int(cfg["CSSliderMax"]) + 1)
            },
        }

    def options(m: dict[str, int]) -> str:
        return (
            "Options: "
            + ", ".join(f"{c} = {lab}" for lab, c in sorted(m.items(), key=lambda kv: kv[1]))
            + "."
        )

    # One page of each kind supplies the wording; derive() checked every page offers the same.
    sv = survey(qsf)
    first = {page: sv["pages"][sv["sets"][1][page][0]]["questions"] for page in "ABC"}
    outcomes = []
    for task, (column, page, key, row) in enumerate(OUTCOMES):
        qid = first[page][key]
        text = clean(qs[qid]["QuestionText"])
        if column in SLIDERS:
            o = slider(column, qid)
        elif key in ("diet", "recognise"):
            m = codes[key]
            o = {
                "question": f"{text} {options(m)}",
                "scale": {"min": min(m.values()), "max": max(m.values()), "nominal": True},
                "response_recode": {c: c for c in m.values()},
            }
        else:
            m = codes["grid" if key == "grid" else key]
            ordered = sorted(m.items(), key=lambda kv: kv[1])
            q = text
            if key == "grid":
                q = f"{text}. {GRID_SENTENCE.format(row=row)}"
            if key == "freq":
                q = f"{text} {options(m)}"
            scale: dict[str, Any] = {
                "min": ordered[0][1],
                "max": ordered[-1][1],
                "min_label": ordered[0][0],
                "max_label": ordered[-1][0],
            }
            if len(ordered) % 2:
                scale["mid_label"] = ordered[len(ordered) // 2][0]
            o = {"question": q, "scale": scale, "response_recode": {c: c for _, c in ordered}}
        outcomes.append(
            {
                "var": column,
                "task_num": task,
                "question": o["question"],
                "scale": o["scale"],
                "response_recode": o["response_recode"],
                "condition_var": f"arm_{page}",
            }
        )

    grid_text = clean(qs[first["B"]["grid"]]["QuestionText"])
    grid_tasks = {row: task for task, (_, _, _, row) in enumerate(OUTCOMES) if row}
    arm_specs = []
    for a in arms:
        spec: dict[str, Any] = {
            "raw": a["condition_num"],
            "condition_num": a["condition_num"],
            "factors": {"photo": a["_key"][1], "heading": a["_key"][0]},
            "text": ARM_TEXT.format(heading=a["_key"][0]),
            "images": [a["_key"][1]],
        }
        if "grid_rows" in a:
            spec["items"] = {
                grid_tasks[std]: {
                    "outcome_question": f"{grid_text}. {GRID_SENTENCE.format(row=here)}"
                }
                for std, here in zip(GRID_ROWS, a["grid_rows"], strict=True)
                if std != here
            }
        arm_specs.append(spec)

    pc = meta["persona_codes"]
    eating = {c: lab for lab, c in pc["eating_disorder"].items()}
    return {
        "study_id": "wsqyn",
        "source": "osf",
        "title": "Restrain Food Database validation: 520 food photographs, each rated on taste, "
        "craving, healthiness, diet choice, frequency, nutrients, recognition, quality and "
        "positivity",
        "data_file": LONG_NAME,
        "licence": "CC BY 4.0 (OSF 7gcsk and component wsqyn, as the deposit states). Each "
        "photograph also carries its own licence, recorded per image in data/catalog/images.json "
        "from the database's Attributions_Database.xlsx.",
        "comparable_to_socsci210": False,
        "participant_id_var": "response_id",
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_var": "arm_A",
            "shared_context": SHARED,
            "factors": ["photo", "heading"],
            "arms": arm_specs,
        },
        "outcomes": outcomes,
        "response_recode": {},
        "persona_map": {
            "age": "age",
            "sex": "sex",
            "ethnicity": "ethnicity",
            "dietary_status": "dietary_status",
            "diagnosed_eating_disorder_now_or_in_the_past": "eating_disorder",
            "hunger": "hunger",
            "bmi": "bmi",
        },
        "persona_missing": {"sex": [pc["sex"]["Prefer not to say"]]},
        "persona_label_rewrite": {
            "sex": {c: lab for lab, c in pc["sex"].items()},
            "ethnicity": {c: lab for lab, c in pc["ethnicity"].items()},
            "dietary_status": {c: lab for lab, c in pc["dietary_status"].items()},
            "eating_disorder": eating,
            "hunger": {
                k: f"{k} on a scale from 0 (Not at all) to 100 (Extremely)"
                for k in range(0, 101, 10)
            },
        },
    }


def food_groups(arms: list[dict[str, Any]]) -> str:
    """condition_num -> the food(s) it showed, for food-level held-out splits.

    Kept out of the arm text and factors on purpose: a factor must change the text
    (QC rule 5), and the food key is a grouping, not something anyone saw.
    """
    with STIM.open(encoding="utf-8-sig", newline="") as f:
        stim = {}
        for r in csv.DictReader(f):
            s, i = (int(x) for x in r["ItemCode"].split(" _ "))
            stim[(s, i)] = r
    out = {
        "_about": "IMG34 (wsqyn): each arm's food(s), as set_item (the study's 52 sets x 10 "
        "items) and the Restrain database's FoodID (VSM stim order.csv). An arm is one "
        "(heading, image file), so one food spans up to three arms (its A, B and C pages, "
        "headings and re-encoded copies differing) and one arm can serve two foods "
        "(Hamburger, sets 46 and 47). A held-out image split must group by food_id or "
        "set_item, never by condition_num alone. Written by scripts/gen_wsqyn.py.",
        "arms": {
            str(a["condition_num"]): [
                {
                    "set_item": f"{s}_{i}",
                    "food_id": stim[(s, i)]["FoodID"],
                    "food": stim[(s, i)]["Food"],
                }
                for s, i in sorted(a["_foods"])
            ]
            for a in arms
        },
    }
    return json.dumps(out, indent=1, ensure_ascii=False) + "\n"


def render(arms: list[dict[str, Any]], meta: dict[str, Any]) -> str:
    return yaml.safe_dump(recipe(arms, meta), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    long_rows, arms, meta = derive()
    data_text = long_csv(long_rows)
    text = render(arms, meta)
    groups = food_groups(arms)
    if args.check:
        same = (
            RECIPE.exists()
            and RECIPE.read_text(encoding="utf-8") == text
            and LONG.exists()
            and LONG.read_text(encoding="utf-8") == data_text
            and GROUPS.exists()
            and GROUPS.read_text(encoding="utf-8") == groups
        )
        print("recipe and data match generator" if same else "recipe or data DIFFERS")
        return 0 if same else 1
    LONG.write_text(data_text, encoding="utf-8")
    RECIPE.write_text(text, encoding="utf-8")
    GROUPS.write_text(groups, encoding="utf-8")
    print(f"wrote {LONG.relative_to(REPO)} ({len(long_rows)} rows) and {RECIPE.relative_to(REPO)}")
    print(f"arms {len(arms)}, images {len(set(meta['image_of'].values()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
