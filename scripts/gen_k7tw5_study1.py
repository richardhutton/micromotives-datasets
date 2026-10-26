#!/usr/bin/env python3
"""Write recipes/images/k7tw5_study1.yaml: the first image experiment (IMG02).

Hollands, Clarke, Pechey et al., Cambridge: "The impact of health warning labels
on snack selection: two online experimental studies", OSF k7tw5, Study 1. Results
in Pechey et al. 2020, BMC Public Health 20:376 (PMC7114781).

4,618 UK adults who eat energy-dense snacks weekly and like chocolate were
randomised to "view an image of a chocolate bar accompanied by one of 18 different
pictorial HWLs" (protocol v1.8, Study 1 procedure) and rated it on six items.

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* ARMS. The data's `Label ` column holds text ("Bowel cancer 2"); `sources.excel`
  codes it like a .sav. Each arm's code is looked up BY LABEL, never typed. The 18
  labels are 6 harms x 3 photographs. Their images were matched to captions by
  document order in "Additional File Food HWLs.docx" (each caption sits below its
  image) and every caption was read against the words printed on the image; the
  per-label means then reproduce the paper's (Bowel cancer 1 and 2 both 4.59
  negative arousal, Obesity 1 lowest at 3.12, Type 2 diabetes 3 most supported at
  4.55), which ties data labels to captions.
* CONDITION. The words printed on the label are quoted word-for-word in the text,
  and the label itself is the image. The chocolate bar it sat beside is not in
  the deposit, so the text says it was there and the image is the label alone.
* OUTCOMES. Wording and endpoint labels from the protocol's Appendix 1. Support
  is asked a (Strongly support) .. g (Strongly oppose) but the deposit holds it
  "scored 1-7"; the paper classes ratings above 4 as acceptable and reports the
  bowel-cancer labels least acceptable, so 7 = Strongly support. A judgement:
  flagged for the checker.
* PERSONA. Income is stored as letters A-O; the key is a table image in the
  protocol (data/raw/k7tw5/protocol_media/image5.jpeg), transcribed below per
  year. Education's Bachelor label is mis-encoded in the deposit ("Bachelorâ€™s");
  restored to the protocol's own curly apostrophe. BMI is NOT mapped: the deposit
  stores it unrounded to 15 digits and the melt renders raw values (debt: 4,618
  people). "Consumption Frequency" (Daily/Weekly) is not mapped: the deposit does
  not say what it summarises. Education is blank for 262 people and -888 for 24;
  the protocol offered "None" and "Prefer not to say" and the data has neither, so
  a blank MAY mean no qualifications. Left absent rather than guessed.
* PHOTO is a factor (1-3 within each harm), expressed only by the picture: the
  three photographs of a harm share their words. QC rules 1 and 5 compare words
  AND images. Split on condition_num or the image id, never the condition string.

    uv run python scripts/gen_k7tw5_study1.py            # write the recipe
    uv run python scripts/gen_k7tw5_study1.py --check    # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

DATA = REPO / "data" / "raw" / "k7tw5" / "Study1" / "Food labelling study 1 final dataset.xlsx"
RECIPE = REPO / "recipes" / "images" / "k7tw5_study1.yaml"

# (data label, harm factor level, catalogue harm key) in the document's order.
HARMS = [
    ("Bowel cancer", "bowel cancer", "bowel_cancer"),
    ("Non-specified cancer", "cancer", "nonspecified_cancer"),
    ("13 types of cancer", "13 types of cancer", "13_types_of_cancer"),
    ("Type 2 diabetes", "type 2 diabetes", "type_2_diabetes"),
    ("Heart disease", "heart disease", "heart_disease"),
    ("Obesity", "obesity only", "obesity"),
]
WORDS = {
    "bowel_cancer": "Excess calories cause obesity which causes bowel cancer",
    "nonspecified_cancer": "Excess calories cause obesity which causes cancer",
    "13_types_of_cancer": "Excess calories cause obesity which causes 13 types of cancer",
    "type_2_diabetes": "Excess calories cause obesity which causes Type 2 diabetes",
    "heart_disease": "Excess calories cause obesity which causes heart disease",
    "obesity": "Excess calories cause obesity",
}
SHARED = "You are shown a picture of a chocolate bar accompanied by a health warning label."

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


def _scale(lo: str, hi: str, mid: str | None = None) -> dict:
    s: dict = {"min": 1, "max": 7, "min_label": lo, "max_label": hi}
    if mid:
        s["mid_label"] = mid
    return s


def recipe() -> dict:
    labels = read_any(DATA).value_labels
    code = {v: int(k) for k, v in labels["Label "].items()}
    arms = []
    for h, (data_name, level, key) in enumerate(HARMS):
        for photo in (1, 2, 3):
            arms.append(
                {
                    "raw": code[f"{data_name} {photo}"],
                    "condition_num": h * 3 + photo - 1,
                    "factors": {"harm": level, "photo": str(photo)},
                    "text": f'The label reads: "{WORDS[key]}". <image>',
                    "images": [f"k7tw5_s1_{key}_{photo}"],
                }
            )
    if len(arms) != len(code):
        raise SystemExit(f"{len(code)} labels in the data, {len(arms)} arms declared")

    feelings = ["afraid", "worried", "uncomfortable", "disgusted"]
    outcomes = [
        {
            "var": f"N.E.A '{f}' (1-7)",
            "task_num": i,
            "question": f"How {f} does the label on this snack make you feel?",
            "scale": _scale(f"Not at all {f}", f"Very {f}"),
        }
        for i, f in enumerate(feelings)
    ]
    outcomes.append(
        {
            "var": "Desirability (scored 1-7)",
            "task_num": 4,
            "question": "How much do you want to eat this snack right now?",
            "scale": _scale("Not at all", "Very much"),
        }
    )
    outcomes.append(
        {
            "var": "Acceptability (scored 1-7)",
            "task_num": 5,
            "question": "Do you support or oppose putting this label on high calorie snacks?",
            "scale": _scale("Strongly oppose", "Strongly support", "Neither oppose nor support"),
        }
    )

    income_code = {v: int(k) for k, v in labels["Income"].items()}
    edu = {
        int(k): v.replace(MOJIBAKE, "’") for k, v in labels["Education "].items() if MOJIBAKE in v
    }
    snacks = {
        "biscuits_and_cookies_as_a_snack": "Biscuits and cookies",
        "cakes,_muffins_and_pastries_as_a_snack": "Cakes, muffins and pastries",
        "chocolate_bars_as_a_snack": "Chocolate bars (or other chocolate-based snacks, e.g. pack of m&ms)",
        "sweets_as_a_snack": "Sweets (e.g. bag of skittles, packet of fruit pastilles)",
        "crisps_as_a_snack": "Packets of crisps",
    }
    return {
        "study_id": "k7tw5",
        "source": "osf",
        "experiment": "study1",
        "title": "Pictorial health warning labels on a chocolate bar: 18 labels (6 harms x 3 photographs)",
        "data_file": "Food labelling study 1 final dataset.xlsx",
        "licence": "none stated (OSF deposit k7tw5). Permission requested from the authors "
        "26 Oct 2026; not for any training export until granted.",
        "comparable_to_socsci210": False,
        "participant_id_var": "PID",
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_var": "Label ",
            "factors": ["harm", "photo"],
            "shared_context": SHARED,
            "arms": arms,
        },
        "outcomes": outcomes,
        "response_recode": {i: i for i in range(1, 8)},
        "missing_codes": [-888, -999],
        "persona_map": {
            "age": "Age",
            "gender": "Gender",
            "ethnicity": "Ethnicity",
            "education": "Education ",
            "income": "Income",
            **snacks,
        },
        "persona_missing": {
            v: [-888, -999] for v in ("Gender", "Ethnicity", "Education ", "Income")
        },
        "persona_label_rewrite": {
            "Income": {income_code[letter]: band for letter, band in INCOME.items()},
            "Education ": edu,
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
