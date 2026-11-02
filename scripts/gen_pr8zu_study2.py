#!/usr/bin/env python3
"""Write recipes/images/pr8zu_study2.yaml: the alcohol drink choice (IMG03, alcohol).

Clarke, Pechey, Mantzari, Hollands et al., Cambridge: "Impact of health warning
labels communicating the risk of cancer on alcohol selection: an online
experimental study", Addiction 116 (2021) 41-52, doi:10.1111/add.15072 (CC BY
4.0). OSF pr8zu, Study 2. The sibling of k7tw5 Study 2 (snacks).

6,024 UK adults who drink beer or wine at least weekly said which they prefer,
were randomised (Qualtrics) to one of four label groups, a 2 (image: present /
absent) x 2 (text: present / absent) design, saw twelve drinks one at a time and
then "all the 12 drinks simultaneously, in random order", and chose one (paper,
Primary outcome). Whether the drinks were beer or wine followed the stated
preference.

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* ARMS. The deposit has no codebook, and its `Condition` codes are NOT the
  protocol's group numbers (the protocol's control is group 4; in the deposit
  the control is the code whose people were all re-randomised for
  acceptability, `Acceptability condition` 2-4). The paper's Table 3 ties each
  code to its arm by count and by alcoholic selections, all exact: 1 control
  (1,510; 1,157), 2 text-only (1,511; 926), 3 image-only (1,502; 728), 4
  image-and-text (1,501; 837). Table 1's gender and weekly-units columns agree
  with the same mapping.
* DRINK is a factor, as in Study 1: the preference column decides which twelve
  drinks were shown, so 4 x 2 = 8 arms, and the `drink` factor equals the
  persona's preference for every participant (not a randomised contrast).
  !! WHICH CODE IS BEER IS A JUDGEMENT, OPEN: we are asking the authors. !!
  The paper's Table 1 literally labels code 1 "Wine" (its counts match code 1
  exactly). Everything else favours 1 = Beer, and that is what is built:
  gender, AUDIT, units, the protocol's option order and Study 1's labelled
  coding. If the authors say 1 = Wine, swap DRINKS and rebuild. The deposit holds
  1/2 with no labels. The protocol lists the options "Beer, Wine" (Qualtrics
  codes options in order, 1 = Beer). Code 1 is 77% male and drinks more per
  occasion; in Study 1, where the deposit labels them, beer drinkers are 77%
  male and wine drinkers 29%, the same split as codes 1 and 2 here (77% and
  29%). Against that, the paper's Table 1 prints "Wine" beside the code 1 counts
  (667 in image-and-text); but that table is not internally consistent (its
  image-and-text age bands, 451 / 572 / 482, are within one of the deposit's
  CONTROL group, 451 / 571 / 483), so 1 = Beer, 2 = Wine.
* WHICH LABELS. Bowel Cancer 1, Breast Cancer 1 and Liver Cancer 2 are starred
  "(Label 1-3)" in the authors' stimuli file (AlcoholLabellingOnlineStudyStimuli
  8.3.20.docx, the file the paper cites as https://osf.io/6dx2u/, sha256
  checked). Its label images are byte-identical to the Study 1 labels already
  catalogued, so the image-and-text arm cites pr8zu_s1_* ids. "Each health
  consequence was shown twice (i.e. on two drinks)" (paper); which drink carried
  which label cannot be determined from source, so no row claims a pairing.
  TEXT-ONLY: the same words, no picture (stimuli file examples). IMAGE-ONLY: the
  same photographs with no words; the deposit holds them only inset on an
  example wine bottle, not as label files, so the rows describe them in words,
  reusing the checked descriptions of the Study 1 catalogue entries.
* THE DRINKS are named from the packaging in the stimuli file's "Product
  selection" images (wine: word/media image22-23; beer: image24-25). The paper
  confirms the make-up: six alcoholic, "three different soft drinks and three
  different alcohol-free beers or wines". The alcohol-free ones carry an
  "Alcohol free" sticker in those images, which the rows say. The pictures are
  not attached: they show the drinks in two separate lines-up with no labels,
  a layout nobody saw and, for the alcoholic drinks, a state only the control
  arm saw.
* OUTCOME. The instruction is the protocol's: 'Imagine you are offered a drink.
  Please select the drink you would prefer to drink [today/now, or later
  today]'; the bracket is a draft placeholder and the fielded wording is NOT
  deposited. Rendered as "now or later today", which is what the paper
  supports ("either immediately or later on that day"). A judgement: flagged. The deposit
  records ONLY whether the drink chosen was alcoholic (`Primary outcome`, 1 /
  0), never which drink, so the response is that and the question says so.
* NOT BUILT. The secondary outcomes concern a single bottle "with or without a
  HWL" whose label the deposit does not record; acceptability re-randomised the
  control group. The time-pressure pairs are a second, sequential task. Desire
  to drink was not asked in Study 2.
* PERSONA. Labels: gender from the paper's Table 1 (1 Male: 779 in
  image-and-text; 4 is "Prefer not to say"); ethnicity in the order and wording
  of the k7tw5 Study 2 Legend (same lab, same questionnaire, matched by Table 1:
  White 1,401 ... prefer not to say 12 in image-and-text); education by the same
  Legend, the protocol's options in the same order (as in snacks, the paper's
  "Bachelor's degree or higher" counts codes 5, 6 and 7); income letters by the
  protocol table; AUDIT-C answers by the protocol's own 0-4 scoring, worded as
  the Study 1 deposit labels them; weekly units by Table 1's bands (exact
  counts). Age -999 (12 people) is a non-answer. Not mapped: unrounded BMI,
  units consumed, the AUDIT score (derived), `Date`.

    uv run python scripts/gen_pr8zu_study2.py            # write the recipe
    uv run python scripts/gen_pr8zu_study2.py --check    # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

DATA_FILE = "Alcohol study 2 full dataset.xlsx"
DATA = REPO / "data" / "raw" / "pr8zu" / "Study 2" / DATA_FILE
RECIPE = REPO / "recipes" / "images" / "pr8zu_study2.yaml"

CONDITION_VAR = "Condition"
DRINK_VAR = "Which alcohol do you prefer?"
CHOICE_VAR = "Primary outcome"
ACCEPT_VAR = "Acceptability condition"

# Deposit code -> label factor, tied by the paper's Table 3 counts.
GROUPS = {1: "none", 2: "text only", 3: "image only", 4: "image and text"}
CONTROL_CODE = 1
# Deposit code -> drink (judgement, see notes).
DRINKS = {1: "beer", 2: "wine"}

ALCOHOLIC = {
    "beer": "Fourpure American Pale, Cisk Export, Farsons Gold Label Pale Ale, Heineken, "
    "Pistonhead Full Amber and San Miguel Especial",
    "wine": "Jack & Gina Zinfandel Rosé, Tesco Merlot, Vicuña Sauvignon Blanc, Oyster Bay "
    "Merlot, The Straw Hat rosé and a Chilean Sauvignon Blanc",
}
NON_ALCOHOLIC = {
    "beer": 'three alcohol-free beers, each with an "Alcohol free" sticker (San Miguel 0,0, '
    "Heineken 0.0 and Pistonhead Flat Tire), and three soft drinks (J2O Orange & Passion "
    "Fruit, Appletiser and Coca-Cola)",
    "wine": 'three alcohol-free wines, each with an "Alcohol free" sticker (Eisberg Sauvignon '
    "Blanc, Morouj Merlot and Bon Voyage Pinot Noir Rosé), and three soft drinks (Cawston "
    "Press Apple & Mango, Coca-Cola and Bottlegreen Sparkling Elderflower Pressé)",
}
PLURAL = {"beer": "beers", "wine": "wines"}

# The three Study 2 HWLs (starred in the stimuli file), in the paper's order.
HWLS = [
    ("pr8zu_s1_bowel_cancer_1", "Alcohol causes bowel cancer"),
    ("pr8zu_s1_breast_cancer_1", "Alcohol causes breast cancer"),
    ("pr8zu_s1_liver_cancer_2", "Alcohol causes liver cancer"),
]
# The same three photographs, words removed (image-only arm). Worded from the
# checked descriptions of the catalogue entries above.
PHOTOS = [
    "a close-up of the inside of a bowel with large red growths around its wall",
    "a chest and underarm crossed by long healed surgical scars",
    "a cut surface of a liver with many pale round tumours, on black",
]

SHARED = (
    "You are shown pictures of twelve drinks, six alcoholic and six non-alcoholic, first one "
    "at a time and then all together in random order."
)
QUESTION = (
    "Imagine you are offered a drink. Please select the drink you would prefer to drink "
    "now or later today. Only whether the drink you choose is alcoholic is "
    "recorded: 1 means one of the six alcoholic drinks and 0 means one of the six "
    "non-alcoholic drinks."
)


def _labels(group: str, drink: str) -> str:
    on = f"Each of the six {PLURAL[drink]} carries"
    tail = "one of these three, each on two of the six"
    if group == "image and text":
        q = [f'"{w}" <image>' for _, w in HWLS]
        return f"{on} a health warning label with a picture, {tail}: {q[0]}, {q[1]} and {q[2]}."
    if group == "text only":
        q = [f'"{w}"' for _, w in HWLS]
        return f"{on} a health warning label in words only, {tail}: {q[0]}, {q[1]} and {q[2]}."
    if group == "image only":
        return (
            f"{on} a health warning label that is a photograph with no words, {tail}: "
            f"{PHOTOS[0]}; {PHOTOS[1]}; and {PHOTOS[2]}."
        )
    return "All twelve are in their original packaging, with no health warning labels."


def arm_text(group: str, drink: str) -> str:
    return (
        f"The drinks are {drink}. The six alcoholic {PLURAL[drink]} are {ALCOHOLIC[drink]}. "
        f"The six non-alcoholic drinks are {NON_ALCOHOLIC[drink]}. {_labels(group, drink)}"
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
# AUDIT-C, protocol scoring 0-4; wording as the Study 1 deposit labels it.
AUDIT = {
    "how_often_has_a_drink_containing_alcohol": (
        "How often do you have a drink containing alcohol?",
        [
            "Never",
            "Monthly or less",
            "2-4 times per month",
            "2-3 times per week",
            "4+ times per week",
        ],
    ),
    "units_of_alcohol_on_a_typical_day_when_drinking": (
        "How many units of alcohol do you drink on a typical day when you are drinking?",
        ["1-2 units", "3-4 units", "5-6 units", "7-9 units", "10+ units"],
    ),
    "how_often_6_or_more_units_if_female_or_8_or_more_if_male_on_a_single_occasion_in_the_last_year": (
        "How often have you drunk 6 or more units on a single occasion in the last year?",
        ["Never", "Less than monthly", "Monthly", "Weekly", "Daily or almost daily"],
    ),
}
WEEKLY_VAR = "Weekly consumption category"
WEEKLY = {1: "0-14 units", 2: "15-30 units", 3: "31-50 units", 4: "51-99 units", 5: "100+ units"}
NON_ANSWERS = [-888, -999]


def recipe() -> dict:
    ds = read_any(DATA)
    df = ds.df
    if set(df[CONDITION_VAR].dropna().astype(int)) != set(GROUPS):
        raise SystemExit("condition codes changed")
    if set(df[DRINK_VAR].dropna().astype(int)) != set(DRINKS):
        raise SystemExit("drink codes changed")
    # The control is the one group re-randomised for acceptability: its people
    # hold every acceptability code, every other group holds exactly one.
    spread = df.groupby(CONDITION_VAR)[ACCEPT_VAR].nunique()
    if int(spread.idxmax()) != CONTROL_CODE or sorted(spread) != [1, 1, 1, 3]:
        raise SystemExit(f"control group is not code {CONTROL_CODE}: {spread.to_dict()}")
    for col, _ in AUDIT.values():
        if col not in df.columns:
            raise SystemExit(f"{col!r} not in the deposit")

    arms = []
    for g, (raw, group) in enumerate(GROUPS.items()):
        for d, (drink_raw, drink) in enumerate(DRINKS.items()):
            arms.append(
                {
                    "raw_values": {CONDITION_VAR: raw, DRINK_VAR: drink_raw},
                    "condition_num": g * 2 + d,
                    "factors": {"label": group, "drink": drink},
                    "text": arm_text(group, drink),
                    "images": [i for i, _ in HWLS] if group == "image and text" else [],
                }
            )

    income_code = {v: int(k) for k, v in ds.value_labels["Income"].items()}
    persona_map = {
        "age": "Age",
        "gender": "Gender",
        "ethnicity": "Ethnicity",
        "education": "Education",
        "income": "Income",
        "alcohol_preference": DRINK_VAR,
        **{field: col for field, (col, _) in AUDIT.items()},
        "units_of_alcohol_drunk_per_week": WEEKLY_VAR,
    }
    return {
        "study_id": "pr8zu",
        "source": "osf",
        "experiment": "study2",
        "title": "Health warning labels (image, text, both or none) on six of twelve drinks: "
        "whether an alcoholic drink is chosen",
        "data_file": DATA_FILE,
        "licence": "No licence stated on OSF (pr8zu). Author permission: Gareth Hollands, "
        "2 Nov 2026, credit required.",
        "comparable_to_socsci210": False,
        "participant_id_var": "PID",
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_vars": [CONDITION_VAR, DRINK_VAR],
            "factors": ["label", "drink"],
            "shared_context": SHARED,
            "arms": arms,
        },
        "outcomes": [
            {
                "var": CHOICE_VAR,
                "task_num": 0,
                "question": QUESTION,
                "scale": {"min": 0, "max": 1, "nominal": True},
            }
        ],
        "response_recode": {0: 0, 1: 1},
        "missing_codes": NON_ANSWERS,
        "persona_map": persona_map,
        "persona_missing": {
            **{v: list(NON_ANSWERS) for v in persona_map.values()},
            "Gender": [*NON_ANSWERS, 4],
            "Ethnicity": [*NON_ANSWERS, 6],
        },
        "persona_label_rewrite": {
            "Gender": GENDER,
            "Ethnicity": ETHNICITY,
            "Education": EDUCATION,
            "Income": {income_code[letter]: band for letter, band in INCOME.items()},
            DRINK_VAR: {code: drink.capitalize() for code, drink in DRINKS.items()},
            **{col: dict(enumerate(labels)) for col, labels in AUDIT.values()},
            WEEKLY_VAR: WEEKLY,
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
