#!/usr/bin/env python3
"""Write recipes/images/pr8zu_study1.yaml: alcohol health warning labels (IMG01).

Clarke, Pechey, Hollands et al., Cambridge: "The impact of health warning labels
on alcohol selection: two online experimental studies", OSF pr8zu, Study 1. Results
in Pechey et al. 2020, BMC Public Health 20:376 (PMC7114781), Table 3. The
sibling of IMG02 (k7tw5, snacks): same lab, same design, same paper.

UK adults who drink beer or wine at least weekly were asked which they prefer;
each then saw "an image of beer or wine (depending on preference) accompanied by
one of 21 different pictorial HWLs" (protocol v1.7, Study 1 procedure) and rated
it. The deposit holds 5,537 people; the paper reports 5,528.

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* ARMS. Two columns jointly define what a person saw. `Label Condition` (text,
  "Bowel cancer 2"; coded like a .sav by `sources.excel`) is the randomised label:
  7 harms x 3 photographs. `Which alcohol do you prefer?` (Beer/Wine) is NOT
  randomised, but the protocol says it decided which drink the label was shown on,
  so it is part of the condition and a factor: 21 x 2 = 42 arms, every code looked
  up BY LABEL. The images were matched to captions by document order in
  "Additional File Alcohol HWLs.docx" (each caption sits below its image), and
  every caption was read against the words printed on its image. The per-label
  means reproduce the paper's Table 3 under the same names (Bowel Cancer 1 highest
  arousal, 4.76 vs 4.77; Breast Cancer 3 lowest, 3.65 vs 3.65; Bowel Cancer 1 least
  supported, 3.50 vs 3.51), which ties the data's label names to the paper's.
  Which photograph is which within a harm rests on the caption order alone.
  Because the drink follows preference, the `drink` factor equals the persona's
  alcohol preference for every participant: it is not a randomised contrast.
* CONDITION. The protocol calls the drink "an image of an alcoholic beverage
  (either beer or wine)"; the deposit does not hold that picture, nor the brand,
  so the text says which drink it was and the image is the label alone. The words
  on the label are quoted word-for-word. "The drink is beer." / "The drink is
  wine." are our words, true for every row in their arm.
* OUTCOMES. Wording and endpoint labels from the protocol's Appendix 1, Study 1.
  The arousal items say "the label on this bottle" for beer and wine alike; that
  is the protocol's wording and is kept. Support is listed a (Strongly support) ..
  g (Strongly oppose) but the deposit holds it "scored 1-7"; the paper classes
  ratings above 4 as acceptable and reports the bowel-cancer labels least
  acceptable, and in the deposit people answering 7 have the highest arousal
  (mean 5.09 against 3.73 at 1) and the lowest AUDIT score, so 7 = Strongly
  support. A judgement: flagged for the checker. One `uncomfortable` cell holds
  only spaces; `sources.excel` reads it as blank and the row is dropped.
* DESIRE TO DRINK IS NOT BUILT. "How much do you want to drink this wine/beer
  right now?" is stored as codes 1, 2, 3, 4, 5, 8, 9: seven answers, no 6 or 7.
  The paper's means (e.g. Breast Cancer 3, 3.73) are the means of those raw codes,
  so the paper averaged an 8 and a 9 on a 7-point scale and cannot say which code
  is which point. The deposit cannot either: drinking measures rise with code from
  1 to 4, then run 9 < 8 ~ 5 (AUDIT Q2 1.25, 1.40, 1.68, 1.76; median units 14,
  18, 29, 28), which suggests the order 1,2,3,4,9,8,5 rather than 1..5,8,9. No
  mapping is supported by the source, so none is written (Never fabricate).
  Recoverable if the authors confirm their Qualtrics coding.
* PERSONA. The income key is a table image in the protocol
  (data/raw/pr8zu/protocol_media/image4.jpeg), identical to k7tw5's; transcribed
  below per year. Education's Bachelor label is mis-encoded in the deposit
  ("Bachelorâ€™s"); restored to the protocol's own curly apostrophe. Education is
  blank for 235 people; the protocol offered "None" and "Prefer not to say" and
  the data has neither as a label, so a blank MAY mean no qualifications. Left
  absent rather than guessed. The three AUDIT-C answers and the drink preference
  are mapped as recorded. NOT mapped: BMI (unrounded floats, as in k7tw5), weekly
  units consumed and purchased (unrounded floats to 4 dp), the AUDIT scores and
  `Ethnicity Code` (derived from mapped answers), `Date`, and `Health condition
  group` (an Excel fill-down artefact: "Bowel cancer" ... then "7 types of
  cancer", "8 types of cancer", ... "800 types of cancer").
* PHOTO is a factor (1-3 within each harm), expressed only by the picture: the
  three photographs of a harm share their words. QC rules 1 and 5 compare words
  AND images. Split on condition_num or the image id, never the condition string.

    uv run python scripts/gen_pr8zu_study1.py            # write the recipe
    uv run python scripts/gen_pr8zu_study1.py --check    # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

DATA_FILE = "Full dataset alcohol labelling study 1.xlsx"
DATA = REPO / "data" / "raw" / "pr8zu" / "Study 1" / DATA_FILE
RECIPE = REPO / "recipes" / "images" / "pr8zu_study1.yaml"

LABEL_VAR = "Label Condition"
DRINK_VAR = "Which alcohol do you prefer?"
EDU_VAR = (
    "What is\nthe highest grade or level of school that you have completed, or the highest\n"
    "degree you have received?"
)
INCOME_VAR = (
    "Please select the letter for the row in which\nyou would place your total household "
    "income per year, from all sources, before\ntax and other deductions"
)

# (data label stem, harm factor level, catalogue harm key) in the document's order.
HARMS = [
    ("Bowel cancer", "bowel cancer", "bowel_cancer"),
    ("Breast cancer", "breast cancer", "breast_cancer"),
    ("Liver cirrhosis", "liver cirrhosis", "liver_cirrhosis"),
    ("Heart disease", "heart disease", "heart_disease"),
    ("Liver cancer", "liver cancer", "liver_cancer"),
    ("Liver disease", "liver disease", "liver_disease"),
    ("7 types of cancer", "7 types of cancer", "7_types_of_cancer"),
]
WORDS = {
    "bowel_cancer": "Alcohol causes bowel cancer",
    "breast_cancer": "Alcohol causes breast cancer",
    "liver_cirrhosis": "Alcohol causes liver cirrhosis",
    "heart_disease": "Alcohol causes heart disease",
    "liver_cancer": "Alcohol causes liver cancer",
    "liver_disease": "Alcohol causes liver disease",
    "7_types_of_cancer": "Alcohol causes 7 types of cancer",
}
DRINKS = [("Beer", "beer"), ("Wine", "wine")]
SHARED = "You are shown a picture of an alcoholic drink accompanied by a health warning label."

# Protocol income table (per year), letter -> band, word-for-word except "-" -> "to".
INCOME = {
    "A": "up to £4,499 per year",
    "B": "£4,500 to £6,499 per year",
    "C": "£6,500 to £7,499 per year",
    "D": "£7,500 to £9,499 per year",
    "E": "£9,500 to £11,499 per year",
    "F": "£11,500 to £13,499 per year",
    "G": "£13,500 to £15,499 per year",
    "H": "£15,500 to £17,499 per year",
    "I": "£17,500 to £24,999 per year",
    "J": "£25,000 to £29,999 per year",
    "K": "£30,000 to £39,999 per year",
    "L": "£40,000 to £49,999 per year",
    "M": "£50,000 to £74,999 per year",
    "N": "£75,000 to £99,999 per year",
    "O": "£100,000 or more per year",
}
MOJIBAKE = "â€™"
AUDIT = {
    "how_often_has_a_drink_containing_alcohol": (
        "AUDIT Q1: How often do you have a drink containing alcohol?"
    ),
    "units_of_alcohol_on_a_typical_day_when_drinking": (
        "AUDIT Q2: How many units of alcohol do you drink on a typical day when you are drinking?"
    ),
    "how_often_6_or_more_units_if_female_or_8_or_more_if_male_on_a_single_occasion_in_the_last_year": (
        "AUDIT Q3: How often have you drunk 6 or more units (if female) or 8 or more units "
        "(if male), on a single occasion in the last year?"
    ),
}


def _scale(lo: str, hi: str, mid: str | None = None) -> dict:
    s: dict = {"min": 1, "max": 7, "min_label": lo, "max_label": hi}
    if mid:
        s["mid_label"] = mid
    return s


def recipe() -> dict:
    labels = read_any(DATA).value_labels
    code = {v: int(k) for k, v in labels[LABEL_VAR].items()}
    drink_code = {v: int(k) for k, v in labels[DRINK_VAR].items()}
    if sorted(drink_code) != [d for d, _ in DRINKS]:
        raise SystemExit(f"drink labels changed: {sorted(drink_code)}")
    arms = []
    for h, (data_name, level, key) in enumerate(HARMS):
        for photo in (1, 2, 3):
            for d, (drink_label, drink) in enumerate(DRINKS):
                arms.append(
                    {
                        "raw_values": {
                            LABEL_VAR: code[f"{data_name} {photo}"],
                            DRINK_VAR: drink_code[drink_label],
                        },
                        "condition_num": (h * 3 + photo - 1) * 2 + d,
                        "factors": {"harm": level, "photo": str(photo), "drink": drink},
                        "text": f'The drink is {drink}. The label reads: "{WORDS[key]}". <image>',
                        "images": [f"pr8zu_s1_{key}_{photo}"],
                    }
                )
    if len(arms) != 2 * len(code):
        raise SystemExit(f"{len(code)} labels in the data, {len(arms) // 2} declared")

    feelings = ["afraid", "worried", "uncomfortable", "disgusted"]
    outcomes = [
        {
            "var": f"N.E.A '{f}' (1-7)",
            "task_num": i,
            "question": f"How {f} does the label on this bottle make you feel?",
            "scale": _scale(f"Not at all {f}", f"Very {f}"),
        }
        for i, f in enumerate(feelings)
    ]
    outcomes.append(
        {
            "var": "Acceptability (scored 1-7)",
            "task_num": 4,
            "question": "Do you support or oppose putting this label on alcohol?",
            "scale": _scale("Strongly oppose", "Strongly support", "Neither oppose nor support"),
        }
    )

    income_code = {v: int(k) for k, v in labels[INCOME_VAR].items()}
    edu = {int(k): v.replace(MOJIBAKE, "’") for k, v in labels[EDU_VAR].items() if MOJIBAKE in v}
    if len(edu) != 1:
        raise SystemExit(f"expected one mis-encoded education label, found {len(edu)}")
    return {
        "study_id": "pr8zu",
        "source": "osf",
        "experiment": "study1",
        "title": "Pictorial health warning labels on beer or wine: 21 labels "
        "(7 harms x 3 photographs)",
        "data_file": DATA_FILE,
        "licence": "none stated (OSF deposit pr8zu). Permission granted by the authors for "
        "research use (data/catalog/image_contacts.json, hollands).",
        "comparable_to_socsci210": False,
        "participant_id_var": "Participant ID",
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_vars": [LABEL_VAR, DRINK_VAR],
            "factors": ["harm", "photo", "drink"],
            "shared_context": SHARED,
            "arms": arms,
        },
        "outcomes": outcomes,
        "response_recode": {i: i for i in range(1, 8)},
        "missing_codes": [-888, -999],
        "persona_map": {
            "age": "How old are you?",
            "gender": "Gender",
            "ethnicity": "Ethnicity",
            "education": EDU_VAR,
            "income": INCOME_VAR,
            "alcohol_preference": DRINK_VAR,
            **AUDIT,
        },
        "persona_missing": {v: [-888, -999] for v in ("Gender", "Ethnicity", EDU_VAR, INCOME_VAR)},
        "persona_label_rewrite": {
            INCOME_VAR: {income_code[letter]: band for letter, band in INCOME.items()},
            EDU_VAR: edu,
        },
    }


def render() -> str:
    return yaml.safe_dump(recipe(), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    text = render()
    if ap.parse_args().check:
        same = RECIPE.exists() and RECIPE.read_text() == text
        print("recipe matches generator" if same else "recipe DIFFERS from generator")
        return 0 if same else 1
    RECIPE.write_text(text)
    print(f"wrote {RECIPE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
