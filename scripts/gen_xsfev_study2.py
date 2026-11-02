#!/usr/bin/env python3
"""Write recipes/images/xsfev_study2.yaml: health warning vs irrelevant aversive labels (IMG40).

Ventsel, Pechey, Marteau, Hollands, Fletcher et al., Cambridge: "Effect of health
warning labels on motivation towards energy-dense snack foods: Two experimental
studies", Appetite 175 (2022), PMC9194909. OSF xsfev, Study 2 only: an online
Prolific study, 1,382 analysed. Study 1 (n=90, a lab conditioning study with a
joystick task and a real snack choice) is a different design and is not built.

People who like milk chocolate and eat it weekly were randomised (Qualtrics) to
see four chocolate bars (Dairy Milk, Mars, Snickers, Galaxy) carrying health
warning labels (HWL), irrelevant aversive labels (IAL: unpleasant animal pictures)
or no label, through a manikin task, two snack choices, a go/no-go task, two more
snack choices and a final liking/wanting rating of each bar (protocol v2.2,
Procedure; data dictionary).

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* ARMS. `Condition` 1 = Control, 2 = HWLs, 3 = IALs (data dictionary). The
  counts are the paper's (471 / 457 / 454) and the post-rating means reproduce
  its Table 2 exactly, which ties the codes to the arms.
* WHICH LABELS. The Supplementary Material (S8, S9) shows the labels fielded in
  Study 2, and they are what the arms cite. The protocol's Appendix 2 is NOT
  used for the IALs: its examples are the Study 1 / pre-pilot set ("A dog that
  has died and is decomposing", ...), and S9 says the pilot replaced two of
  them. Images: supplementary docx word/media image19-21 (HWLs), image26-28
  (IALs), each read against the words printed on it.
* WHICH LABEL ON WHICH BAR cannot be determined from source, so no row claims
  one. The manikin task used 12 chocolate stimuli (protocol 1.1: "the 12
  chocolate bars", i.e. four bars x three labels), and the deposit's own two
  pictures of the HWL bars disagree (S8 shows Mars with heart disease; the S13
  selection screenshot shows Mars with Type 2 diabetes). The condition
  therefore says each bar carried one of the three labels and shows the three
  labels, not the bars. The no-label arm shows no picture.
* OUTCOMES BUILT. The post-task liking and wanting of each bar (8 items, 0-100
  visual analogue scale, "not at all" (0) to "very" (100), wording from the
  protocol and the paper), and the FIRST snack choice pair: the unlabelled
  selection and the labelled selection, both taken after the manikin task. The
  choice options are those on the fielded Qualtrics screen (S13 screenshots):
  the four bars and four fruits (apple, banana, orange, grapes); the deposit
  records only which kind was chosen (1 chocolate bar, 2 healthier snack). The
  screen's own words open the question. Labelled-selection wording differs per
  arm (`items` override), because what the bars carried differs. In the no-label
  arm the labelled selection is the unlabelled screen again: its row would repeat
  the first choice's prompt word for word (471 people, 55 answering differently),
  so that one cell is dropped, as the repeated second pair is.
* NOT BUILT. Baseline liking and wanting: asked before randomisation took
  effect, of unlabelled bars, so they are not an outcome of any arm. The
  stationery ratings: control stimuli never labelled in any arm. The second
  snack choice pair (after the go/no-go task): the same question again, which a
  row cannot tell apart from the first without citing its position in the
  sequence. Manikin and go/no-go reaction times: not survey responses.
* PERSONA. Codes are bare integers in the deposit; labels are the data
  dictionary's own inline definitions (ethnicity, education), the supplement's
  footnotes (purchase and consumption frequency, eating behaviour), and the
  dictionary's income table (data/raw/xsfev/s2dict_media/image1.jpeg,
  byte-identical to k7tw5's, so the same transcription). Gender 4 and ethnicity 6 (prefer not
  to say) and the -888 / -999 codes are non-answers. Hunger (0 not hungry at all .. 100 the most hungry)
  and time since eating were asked before the tasks. Eating behaviour and
  purchase/consumption frequency were asked at the END, after exposure; they are
  mapped because the supplement's S15 shows them identical across arms (e.g.
  Dairy Milk purchasing 1.4 in all three) and they describe habits over the last
  month. A judgement: flagged for the checker. BMI is not mapped (unrounded
  floats, as in k7tw5).

    uv run python scripts/gen_xsfev_study2.py            # write the recipe
    uv run python scripts/gen_xsfev_study2.py --check    # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

DATA_FILE = "Study2_AvoidApproach_Data_20201019.xlsx"
DATA = REPO / "data" / "raw" / "xsfev" / "data" / DATA_FILE
RECIPE = REPO / "recipes" / "images" / "xsfev_study2.yaml"

CONDITION_VAR = "Condition"
# Data dictionary: "1 to 3 / Control / HWLs / IALs".
ARM_CODES = {"none": 1, "health warning": 2, "irrelevant aversive": 3}

HWLS = [
    ("xsfev_s2_hwl_heart_disease", "Excess calories cause obesity which causes heart disease"),
    ("xsfev_s2_hwl_bowel_cancer", "Excess calories cause obesity which causes bowel cancer"),
    ("xsfev_s2_hwl_type_2_diabetes", "Excess calories cause obesity which causes Type 2 diabetes"),
]
IALS = [
    ("xsfev_s2_ial_aggressive_dog", "A dog that is aggressive and is showing its teeth"),
    ("xsfev_s2_ial_dead_dog", "A dog that is dead and abandoned"),
    ("xsfev_s2_ial_dead_cat", "A cat that was hit by a car and killed"),
]

SHARED = "You are shown pictures of four chocolate bars: Dairy Milk, Mars, Snickers and Galaxy."
BARS = "four chocolate bars (Dairy Milk, Mars, Snickers and Galaxy)"
FRUIT = "four pieces of fruit (an apple, a banana, an orange and a bunch of grapes)"
SCREEN = "Imagine you are offered a snack. Click on the one you would most like to eat now."
CHOICE_CODES = "1 means you chose a chocolate bar and 2 means you chose a piece of fruit."
UNLABELLED = "shown in their original packaging without any label"
ON_BARS = {
    "health warning": "each carrying one of the health warning labels",
    "irrelevant aversive": "each carrying one of the labels with an unpleasant picture",
    "none": UNLABELLED,
}

# (column stem in the deposit, name in the question)
BAR_COLS = [
    (
        "Post-IM task (labelled per condition)-Dairy Milk_like",
        "Post-IM task (labelled per condition)-Dairy Milk-want",
        "Dairy Milk",
    ),
    (
        "Post-IM task (labelled per condition)-mars-like",
        "Post-IM task (labelled per condition)-mars-want",
        "Mars",
    ),
    (
        "Post-IM task (labelled per condition)-snickers-like",
        "Post-IM task (labelled per condition)-snickers-want",
        "Snickers",
    ),
    (
        "Post-IM task (labelled per condition)-galaxy-like",
        "Post-IM task (labelled per condition)-galaxy-want",
        "Galaxy",
    ),
]
SELECT_UNLABELLED = "1st Snack selection - Part 1(unlabelled, post-manikin task)"
SELECT_LABELLED = (
    "1st Snack selection - Part 2 (labelled depending on randomised condition, post manikin task)"
)

# Protocol income table (per year), letter -> band, word-for-word except "-" -> "to".
INCOME = [
    "up to £4,499 per year",
    "£4,500 to £6,499 per year",
    "£6,500 to £7,499 per year",
    "£7,500 to £9,499 per year",
    "£9,500 to £11,499 per year",
    "£11,500 to £13,499 per year",
    "£13,500 to £15,499 per year",
    "£15,500 to £17,499 per year",
    "£17,500 to £24,999 per year",
    "£25,000 to £29,999 per year",
    "£30,000 to £39,999 per year",
    "£40,000 to £49,999 per year",
    "£50,000 to £74,999 per year",
    "£75,000 to £99,999 per year",
    "£100,000 or more per year",
]
# Data dictionary, column X, inline definitions.
ETHNICITY = {
    1: "White British / White Irish / Other White background",
    2: "Mixed White and Black African / Mixed White and Asian / Mixed White and Black "
    "Caribbean / Other Mixed background",
    3: "Asian/Asian British (Indian/Pakistani/Bangladeshi/Chinese/Other Asian/Asian British "
    "background)",
    4: "Black/Black British (African/Caribbean/Other Black/Black British background)",
    5: "Other ethnic group",
}
# Data dictionary, column Y, inline definitions.
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
}
GENDER = {1: "Male", 2: "Female", 3: "Other"}
# Supplementary S15 footnotes 3-5.
FREQUENCY = {1: "Monthly or less often", 2: "At least once a week", 3: "Just about every day"}
TRUE_FALSE = {1: "Definitely false", 2: "Mostly false", 3: "Mostly true", 4: "Definitely true"}

TFEQ = {
    "how_true_i_deliberately_take_small_helpings_to_control_my_weight": (
        'How true is "I deliberately take small helpings to control my weight"'
    ),
    "how_true_i_dont_eat_some_foods_because_they_make_me_fat": (
        'How true is "I don\'t eat some foods because they make me fat."'
    ),
    "how_true_i_consciously_hold_back_on_how_much_i_eat_at_meals_to_keep_from_gaining_weight": (
        'How true is "I consciously hold back on how much I eat at meals to keep from gaining '
        'weight"'
    ),
}
HABITS = {
    f"times_{verb}_{key}_in_the_last_month": f"{stem} - {col}"
    for key, col in (
        ("dairy_milk", "DM"),
        ("mars", "Mars"),
        ("snickers", "Snickers"),
        ("galaxy", "Galaxy"),
    )
    for verb, stem in (("purchased", "Purchasing Frequency"), ("eaten", "Consumption frequency"))
}
NON_ANSWERS = [-888, -999]


def _labels(images: list[tuple[str, str]]) -> str:
    quoted = [f'"{words}" <image>' for _, words in images]
    return f"{quoted[0]}, {quoted[1]} and {quoted[2]}."


ARM_TEXT = {
    "health warning": "Each bar's packaging carries a health warning label, one of these "
    "three: " + _labels(HWLS),
    "irrelevant aversive": "Each bar's packaging carries a label with an unpleasant picture, "
    "one of these three: " + _labels(IALS),
    "none": "The bars are shown in their original packaging, with no label.",
}
ARM_IMAGES = {
    "health warning": [i for i, _ in HWLS],
    "irrelevant aversive": [i for i, _ in IALS],
    "none": [],
}


def _choice(bars: str) -> str:
    return f"{SCREEN} The eight snacks are {BARS}, {bars}, and {FRUIT}. {CHOICE_CODES}"


def _labelled_choice(level: str) -> dict:
    """The labelled snack choice (task 9) for one arm.

    In the no-label arm the "labelled" screen is the unlabelled one again, so its
    row would repeat task 8's prompt word for word; it is dropped with an EMPTY
    recode, under which no answer is in range and the cell yields no rows.
    """
    if level == "none":
        return {"response_recode": {}}
    return {"outcome_question": _choice(ON_BARS[level])}


def recipe() -> dict:
    ds = read_any(DATA)
    codes = set(ds.df[CONDITION_VAR].unique())
    if codes != set(ARM_CODES.values()):
        raise SystemExit(f"condition codes changed: {sorted(codes)}")
    for like, want, _ in BAR_COLS:
        for col in (like, want, SELECT_UNLABELLED, SELECT_LABELLED):
            if col not in ds.df.columns:
                raise SystemExit(f"{col!r} not in the deposit")

    vas = {"min": 0, "max": 100, "min_label": "not at all", "max_label": "very"}
    outcomes: list[dict] = []
    for i, (like, _, bar) in enumerate(BAR_COLS):
        outcomes.append(
            {
                "var": like,
                "task_num": i,
                "question": f"{bar}: How much do you like this chocolate bar generally?",
                "scale": dict(vas),
            }
        )
    for i, (_, want, bar) in enumerate(BAR_COLS):
        outcomes.append(
            {
                "var": want,
                "task_num": 4 + i,
                "question": f"{bar}: How much do you want one of these chocolate bars right now?",
                "scale": dict(vas),
            }
        )
    choice_scale = {"min": 1, "max": 2, "nominal": True}
    outcomes.append(
        {
            "var": SELECT_UNLABELLED,
            "task_num": 8,
            "question": _choice(UNLABELLED),
            "scale": dict(choice_scale),
            "response_recode": {1: 1, 2: 2},
        }
    )
    outcomes.append(
        {
            "var": SELECT_LABELLED,
            "task_num": 9,
            "question": _choice(UNLABELLED),
            "scale": dict(choice_scale),
            "response_recode": {1: 1, 2: 2},
        }
    )

    arms = []
    for n, (level, raw) in enumerate(ARM_CODES.items()):
        arms.append(
            {
                "raw": raw,
                "condition_num": n,
                "factors": {"label": level},
                "text": ARM_TEXT[level],
                "images": ARM_IMAGES[level],
                "items": {9: _labelled_choice(level)},
            }
        )

    persona_map = {
        "age": "Age",
        "gender": "Gender",
        "ethnicity": "Ethnicity",
        "education": "Education",
        "income": "Income",
        "how_hungry_from_0_not_hungry_at_all_to_100_the_most_hungry": "Hunger",
        "when_did_you_last_have_something_to_eat": "Time since ate",
        **TFEQ,
        **HABITS,
    }
    rewrite = {
        "Gender": GENDER,
        "Ethnicity": ETHNICITY,
        "Education": EDUCATION,
        "Income": {i + 1: band for i, band in enumerate(INCOME)},
        **dict.fromkeys(TFEQ.values(), TRUE_FALSE),
        **dict.fromkeys(HABITS.values(), FREQUENCY),
    }
    return {
        "study_id": "xsfev",
        "source": "osf",
        "experiment": "study2",
        "title": "Health warning labels vs irrelevant aversive labels vs no label on chocolate "
        "bars: liking, wanting and snack choice",
        "data_file": DATA_FILE,
        "licence": "No licence stated on OSF (xsfev). Author permission: Gareth Hollands, "
        "2 Nov 2026, for the group, credit required; Paul Fletcher (cc) did not reply "
        "separately.",
        "comparable_to_socsci210": False,
        "participant_id_var": "Subject ID",
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_var": CONDITION_VAR,
            "factors": ["label"],
            "shared_context": SHARED,
            "arms": arms,
        },
        "outcomes": outcomes,
        "response_recode": {i: i for i in range(0, 101)},
        "missing_codes": NON_ANSWERS,
        "persona_map": persona_map,
        "persona_missing": {
            **dict.fromkeys(persona_map.values(), NON_ANSWERS),
            "Gender": [*NON_ANSWERS, 4],
            "Ethnicity": [*NON_ANSWERS, 6],
        },
        "persona_label_rewrite": rewrite,
    }


class _NoAliases(yaml.SafeDumper):
    """Write shared label maps out in full: a recipe is read by people, not parsers."""

    def ignore_aliases(self, data: object) -> bool:
        return True


def render() -> str:
    return yaml.dump(recipe(), Dumper=_NoAliases, sort_keys=False, allow_unicode=True, width=100)


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
