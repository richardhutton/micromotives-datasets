#!/usr/bin/env python3
"""Write recipes/images/k7tw5_study2.yaml: the snack vending-machine choice (IMG03, snacks).

Clarke, Pechey, Mantzari, Hollands et al., Cambridge: "Impact of health warning
labels on snack selection: an online experimental study", Appetite 154 (2020)
104744 (PMC7450271). OSF k7tw5, Study 2. The sibling of pr8zu Study 2 (alcohol).

4,134 UK adults who eat energy-dense snacks were randomised (Qualtrics) to one of
six label groups, a 3 (image-and-text HWL / text-only HWL / no HWL) x 2 (calorie
information / none) design, saw twelve snacks one at a time and then "all the 12
snacks presented in randomised order, similar to a vending machine layout", and
were told: "Imagine you are at a vending machine. Please select the snack you
would like to eat right now." (paper, 2.4.1, quoting the instruction). The
protocol's draft wording ("Click on the snack ...") is superseded by the paper's
quotation of what was shown.

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* ARMS. `Condition` 1-6 per the deposit's Legend sheet: 1 pictorial HWL with
  calories, 2 text-only HWL with calories, 3 calories only, 4 pictorial HWL,
  5 text-only HWL, 6 control (no label). The paper's Table 2 counts (692, 686,
  696, 688, 685, 687) and energy-dense selections (260, 299, 374, 255, 327, 405)
  are reproduced exactly by these codes, which ties each code to its arm.
* WHICH LABELS. The three HWLs used in Study 2 are starred in the authors'
  stimuli file (FoodLabellingStudyStimuli11.3.20.docx, the file the paper cites
  as https://osf.io/kf3r7/): Bowel Cancer 1, Type 2 Diabetes 1, Heart Disease 1.
  That file's embedded label images are byte-identical to the Study 1 labels
  already catalogued, so the arms cite the existing ids k7tw5_s1_*_1.
* WHICH LABEL ON WHICH SNACK cannot be determined from source. The paper says
  each energy-dense snack carried one of the three "so that all health
  consequences were shown equally across the selection": six snacks, three
  labels, so two each. The condition says exactly that and shows the three
  labels, never a snack-label pairing. CALORIES: "given per package and ...
  presented as black text on a white background" (paper). Only one product's
  number is in the deposit (Galaxy, 229, in an example image), so no row states
  a number. The original packs carry their own nutrition panels (the "Snack
  options" image shows e.g. "63 kcal" on the carrot crisps), so the no-calorie
  and control arms say only that no label was ADDED, never that no calories
  were visible.
* THE TWELVE SNACKS. Codes are the Legend's ("1 = doritios, 2 = apple crisps,
  3 = galaxy, 4 = Nims beetroot crisps, 5 = muller yoghurt, 6 = mccoys, 7 = apple
  and grapes fruit, 8 = millionaire shortbread, 9 = dairy milk, 10 = mango and
  pineapple fruit, 11 = GU dessert, 12 = KIND bar"). Names in the rows are read
  from the packaging in the stimuli file's "Snack options" image (word/media/
  image19.png), the selection the paper points to. Eleven of the twelve match a
  Legend name directly. Code 8's Legend name is generic: the product pictured is
  a Food Connections Caramel Shortcake Slice (millionaire's shortbread by another
  name). CODE 2 IS A JUDGEMENT, flagged for the checker: the Legend says "apple
  crisps" but the pictured selection has no apple crisps; its one product left
  unmatched is Morrisons Eat Smart carrot crisps, and the paper describes the
  less energy-dense set as "vegetable crisps, cereal bars, fruit and yoghurt",
  which fits carrot and beetroot crisps and not apple crisps. The Legend's names
  are demonstrably not the fielded products' (code 8; the protocol's candidate
  pool, data/raw/k7tw5/protocol_media, holds Nim's apple crisps and a Tesco
  millionaire shortbread, neither pictured in the final selection), so code 2 is
  named from the picture. Energy-dense (Primary outcome = 1) are codes 1, 3, 6,
  8, 9, 11, checked against the deposit below.
* THE PICTURE OF THE SELECTION IS NOT ATTACHED. It shows the twelve unlabelled,
  split by energy density with a dividing line: a layout no participant saw (the
  order was randomised) in a state only the control arm saw. The rows name the
  snacks instead and attach only the labels.
* OUTCOME. `Snack selected primary outcome`, 1-12, an unordered choice
  (nominal), the options enumerated in the question. Nine people hold 0 (no
  snack recorded); the paper counts them as not choosing an energy-dense snack,
  but 0 is not one of the twelve, so they are dropped (missing code 0). The
  paper's Table 2 numbers therefore reproduce on the 4,134 before that drop.
* NOT BUILT. The secondary outcomes (arousal, reactance, avoidance, disease
  risk, acceptability) were asked about "an image of a chocolate bar with or
  without a label", a different stimulus whose label the deposit does not
  record; acceptability also re-randomised the control group. The time-pressure
  pairs are a second, sequential task (six pairs) and are not built here.
* PERSONA. Codes are bare integers; labels are the Legend's own definitions.
  The paper's Table 1 ties the codes the Legend does not cover: gender 7 is
  "Prefer not to say" (0, 1, 0, 1, 1, 0 per group, matching the deposit), and
  ethnicity 7 is "Prefer not to say" (5, 3, 9, 7, 4, 2); both are non-answers.
  Education follows the Legend (1 no qualifications .. 7 other vocational); no
  one holds 1 or a non-answer, and the paper's "Bachelor's degree or higher"
  counts are codes 5, 6 AND 7 (e.g. 192 + 91 + 55 = 338), so the paper grouped
  "other vocational" with degrees. The Legend is followed; noted for the checker.
  Income letters A-O use the protocol's table (same transcription as Study 1).
  BMI category uses the Legend's bands; the unrounded BMI is not mapped.

    uv run python scripts/gen_k7tw5_study2.py            # write the recipe
    uv run python scripts/gen_k7tw5_study2.py --check    # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

DATA_FILE = "FoodLabellingOnline2Dataset.xlsx"
DATA = REPO / "data" / "raw" / "k7tw5" / "Study2" / DATA_FILE
RECIPE = REPO / "recipes" / "images" / "k7tw5_study2.yaml"

CONDITION_VAR = "Condition"
CHOICE_VAR = "Snack selected primary outcome"
ENERGY_DENSE_VAR = "Primary outcome"

# Legend, column C: Group n -> (hwl, calories).
GROUPS = {
    1: ("image and text", "shown"),
    2: ("text only", "shown"),
    3: ("none", "shown"),
    4: ("image and text", "not shown"),
    5: ("text only", "not shown"),
    6: ("none", "not shown"),
}

# Legend code -> name read from the packaging in the stimuli file's "Snack options".
SNACKS = {
    1: "Doritos Tangy Cheese",
    2: "Morrisons Eat Smart carrot crisps",
    3: "Galaxy Smooth Milk chocolate bar",
    4: "Nim's beetroot & parsnip vegetable crisps",
    5: "Müller Light Toffee yoghurt",
    6: "McCoy's Ridge Cut Salt & Malt Vinegar crisps",
    7: "Apple & Grape Snack Pack",
    8: "Food Connections Caramel Shortcake Slice",
    9: "Cadbury Dairy Milk chocolate bar",
    10: "Tesco Mango and Pineapple Fingers",
    11: "Gü Zillionaires' Cheesecake",
    12: "Pressed by KIND Dark Chocolate Banana bar",
}
ENERGY_DENSE = [1, 3, 6, 8, 9, 11]
SIX = "Doritos, McCoy's, Galaxy, Dairy Milk, the Gü cheesecake and the caramel shortcake slice"

# The three Study 2 HWLs (starred in the stimuli file), in the paper's order.
HWLS = [
    ("k7tw5_s1_bowel_cancer_1", "Excess calories cause obesity which causes bowel cancer"),
    ("k7tw5_s1_heart_disease_1", "Excess calories cause obesity which causes heart disease"),
    ("k7tw5_s1_type_2_diabetes_1", "Excess calories cause obesity which causes Type 2 diabetes"),
]

SHARED = (
    "You are shown pictures of twelve snacks, first one at a time and then all "
    "together in random order."
)
CALORIES = (
    "Every snack carries a calorie label giving its calories per pack, in black text on white."
)
NO_CALORIES = "No calorie label is added to the snacks."
NO_HWL = "No snack carries a health warning label."
CONTROL = "The snacks are in their original packaging, with no added labels."


def _hwl_text(kind: str) -> str:
    if kind == "image and text":
        quoted = [f'"{w}" <image>' for _, w in HWLS]
        what = "a health warning label with a picture"
    else:
        quoted = [f'"{w}"' for _, w in HWLS]
        what = "a health warning label in words only"
    return (
        f"{SIX} each carry {what}, one of these three, each on two of the six: "
        f"{quoted[0]}, {quoted[1]} and {quoted[2]}."
    )


def arm_text(hwl: str, calories: str) -> str:
    if hwl == "none" and calories == "not shown":
        return CONTROL
    parts = [NO_HWL if hwl == "none" else _hwl_text(hwl)]
    parts.append(CALORIES if calories == "shown" else NO_CALORIES)
    if hwl == "none":
        parts.reverse()
    return " ".join(parts)


QUESTION = (
    "Imagine you are at a vending machine. Please select the snack you would like to eat "
    "right now. The snacks are: "
    + "; ".join(f"{n} {name}" for n, name in SNACKS.items())
    + ". Answer with the number of the snack you choose."
)

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
# Legend, columns AD-AO, inline definitions.
GENDER = {1: "Male", 2: "Female", 3: "Other"}
ETHNICITY = {
    1: "White British / White Irish / Other White background",
    2: "Mixed White and Black African / Mixed White and Asian / Mixed White and Black "
    "Caribbean / Other Mixed background",
    3: "Asian/Asian British (Indian/Pakistani/Bangladeshi/Chinese/Other Asian/Asian British "
    "background)",
    4: "Black/Black British (African/Caribbean/Other Black/Black British background)",
    5: "Other ethnic group",
}
EDUCATION = {
    1: "No qualifications",
    2: "Up to 4 GCSE's (Including 1-4 O Levels/CSE/GCSEs (any grades), Foundation Diploma, "
    "NVQ level 1, Foundation GNVQ or equivalents) (or foreign equivalent)",
    3: "5 or more GCSE's or 1 A-level (Including 5+ GCSEs (Grades A*-C),1 A Level/ 2-3 AS "
    "Levels, NVQ level 2, Intermediate GNVQ, City and Guilds Craft, BTEC First/General "
    "Diploma, RSA Diploma, Apprenticeship or equivalents) (or foreign equivalent)",
    4: "2 or more A-levels (Including 2+ A Levels, 4+ AS Levels, NVQ Level 3, Advanced GNVQ, "
    "City and Guilds Advanced Craft, ONC, OND, BTEC National, RSA Advanced Diploma or "
    "equivalents) (or foreign equivalent)",
    5: "Bachelor's degree (Including BA, BSc, NVQ Level 4-5, HNC, HND, RSA Higher Diploma, "
    "BTEC Higher level or equivalents) (or foreign equivalent)",
    6: "Post-Graduate degree or qualification (Including Higher Degrees e.g. MA, PhD, PGCE, "
    "Professional qualifications e.g. teaching, nursing, accountancy or equivalents) (or "
    "foreign equivalent)",
    7: "Other vocational/work-related qualifications",
}
BMI_CATEGORY = {
    1: "Underweight (under 18.5)",
    2: "Healthy weight (18.5-24.9)",
    3: "Overweight (25-29.9)",
    4: "Obese (30-34.9)",
    5: "Severely obese (35-39.9)",
    6: "Morbidly obese (40+)",
}
SNACK_FREQUENCY = {1: "Daily", 2: "Weekly", 3: "Monthly", 4: "Never"}
# Legend scoring, worded as the protocol's screening options.
CATEGORY_FREQUENCY = {
    1: "Less than once a week",
    2: "Once a week",
    3: "2-3 times a week",
    4: "4-6 times a week",
    5: "Every day",
}
CATEGORIES = {
    "biscuits_and_cookies_as_a_snack": "Biscuits and cookies",
    "cakes,_muffins_and_pastries_as_a_snack": "Cakes, muffins and pastries",
    "chocolate_bars_as_a_snack": "Chocolate bars (or other chocolate-based snacks, e.g. pack of "
    "m&ms)",
    "sweets_as_a_snack": "Sweets (e.g. bag of skittles, packet of fruit pastilles)",
    "crisps_as_a_snack": "Packets of crisps",
}
NON_ANSWERS = [-888, -999]


def recipe() -> dict:
    ds = read_any(DATA)
    df = ds.df
    codes = set(df[CONDITION_VAR].dropna().astype(int))
    if codes != set(GROUPS):
        raise SystemExit(f"condition codes changed: {sorted(codes)}")
    chosen = set(df[CHOICE_VAR].dropna().astype(int)) - {0}
    if chosen != set(SNACKS):
        raise SystemExit(f"snack codes changed: {sorted(chosen)}")
    # The energy-dense six must be exactly the codes the deposit scores 1.
    picked = df[df[CHOICE_VAR] > 0]
    dense = set(picked.loc[picked[ENERGY_DENSE_VAR] == 1, CHOICE_VAR].astype(int))
    if dense != set(ENERGY_DENSE):
        raise SystemExit(f"energy-dense codes are {sorted(dense)}, not {ENERGY_DENSE}")

    arms = []
    for n, (raw, (hwl, calories)) in enumerate(GROUPS.items()):
        arms.append(
            {
                "raw": raw,
                "condition_num": n,
                "factors": {"hwl": hwl, "calories": calories},
                "text": arm_text(hwl, calories),
                "images": [i for i, _ in HWLS] if hwl == "image and text" else [],
            }
        )

    income_code = {v: int(k) for k, v in ds.value_labels["Income"].items()}
    persona_map = {
        "age": "Age",
        "gender": "Gender",
        "ethnicity": "Ethnicity",
        "education": "Education",
        "income": "Income",
        "bmi_category": "BMI category",
        "how_often_do_you_consume_a_snack": "Snack consumption frequency",
        **CATEGORIES,
    }
    return {
        "study_id": "k7tw5",
        "source": "osf",
        "experiment": "study2",
        "title": "Health warning labels and calorie labels on a vending machine of twelve "
        "snacks: which snack is chosen",
        "data_file": DATA_FILE,
        "licence": "No licence stated on OSF (k7tw5). Author permission: Gareth Hollands, "
        "2 Nov 2026, credit required.",
        "comparable_to_socsci210": False,
        "participant_id_var": "Participant number",
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_var": CONDITION_VAR,
            "factors": ["hwl", "calories"],
            "shared_context": SHARED,
            "arms": arms,
        },
        "outcomes": [
            {
                "var": CHOICE_VAR,
                "task_num": 0,
                "question": QUESTION,
                "scale": {"min": 1, "max": 12, "nominal": True},
            }
        ],
        "response_recode": {i: i for i in SNACKS},
        "missing_codes": [0, *NON_ANSWERS],
        "persona_map": persona_map,
        "persona_missing": {
            **{v: list(NON_ANSWERS) for v in persona_map.values()},
            "Gender": [*NON_ANSWERS, 4, 7],
            "Ethnicity": [*NON_ANSWERS, 6, 7],
        },
        "persona_label_rewrite": {
            "Gender": GENDER,
            "Ethnicity": ETHNICITY,
            "Education": EDUCATION,
            "Income": {income_code[letter]: band for letter, band in INCOME.items()},
            "BMI category": BMI_CATEGORY,
            "Snack consumption frequency": SNACK_FREQUENCY,
            **{v: dict(CATEGORY_FREQUENCY) for v in CATEGORIES.values()},
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
