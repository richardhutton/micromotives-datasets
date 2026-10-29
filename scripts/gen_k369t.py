#!/usr/bin/env python3
"""Write recipes/images/k369t.yaml: kcal and PACE labelling and portion choice (IMG27).

Marty, Franzon, Jones & Robinson (Liverpool), "Socioeconomic position, energy
labelling and portion size selection: an online study comparing calorie and
physical activity calorie equivalent (PACE) labelling in UK adults", OSF k369t;
published in Appetite 2021. Answer key: the deposit's pre-print (Table 2,
Figure 3). Instrument: the pre-registered protocol in the deposit, whose task
text the pre-print's Additional file section 1 repeats.

1,667 UK adults (Prolific, April-May 2020) were randomised between subjects to
one of four labelling groups, then served themselves 18 dishes in random order.
Each dish was a set of 50 photographs, 20 kcal apart (20 to 1000 kcal); the
first photograph shown was the smallest, the right arrow stepped to the next
larger one, the left arrow back, and the space bar confirmed. The deposit is
LONG: one row per person per dish, 30,006 rows, with `portion` naming the
photograph confirmed (e.g. "BB17" = beef in black bean sauce, photograph 17).

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* ARMS. `condition` (4 labelling groups, between subjects) x `food name` (18
  dishes, within subject): 72 arms, each data row one (person, dish) trial, both
  codes looked up BY LABEL. condition_num = group * 18 + dish. The person id is
  `subject`, so one person's 18 rows share one participant_id.
* IMAGES. The deposit does not hold the 900 task photographs. It holds, in the
  protocol's Appendix K (familiarity task), one small picture of each of the 18
  dishes; the protocol and the pre-print (section 2.4, Table S1) say those are
  the 600 kcal portion, the 30th photograph. The pre-print's Figure 1 shows the
  fielded tortellini screen at 600 kcal ("600 kcal", "120 min") and its plate
  matches the Appendix K tortellini picture. Each arm cites its dish's picture,
  and the text says it is photograph 30 of the 50; it does not stand in for the
  photograph the person confirmed, which the deposit does not hold. The pictures
  are 126-190 px, much smaller than on screen. Each dish's picture was matched
  to the data's dish by the caption printed on it.
  NOT cited: the example labels (protocol image1-3, 10, 12, 14) and the beef
  screenshots (image8, 9, 11, 13, 15) all show 500 kcal / 100 min, a value that
  belongs to one photograph of one dish; the label is described in words.
* CONDITION. The task instructions, word-for-word from protocol Appendix H, with
  each group's own label sentence where the protocol puts it (mid-paragraph, so
  the instructions are repeated per arm, not hoisted). Two sentences dropped as
  survey mechanics: "In this task, you will be shown pictures of 18 different
  dishes." and "Tap the spacebar to start." The on-screen line below the photo
  is quoted from the protocol's screenshots. The recommendation sentences are
  quoted word-for-word (protocol Appendix H, "During the task"; pre-print 2.3.2);
  where on screen they sat is not recorded, so the text says only that they were
  shown. Words that are OURS, all description of the documented display:
    "The dish was shown as one of 50 photographs of increasing portion size,
    captioned ...", "The first photograph showed the smallest portion; each tap
    of the right arrow showed the next larger one, up to the 50th.", "Photograph
    30 of the 50:", and per labelled group the label clause ("To the left of
    each photograph a label showed ..."). The label values are arithmetic from
    the protocol: 20 kcal per photograph, and 4 minutes of walking per 20 kcal
    (500 kcal = 100 min in the protocol, 600 kcal = 120 min in the pre-print);
    only "600 kcal" and "120 min" are quoted, because only those were seen
    beside photograph 30. The no-label group's text names no calories.
* OUTCOME. "How much would you like to eat?" is the screen's own question
  (protocol screenshots). The response is the number of the photograph
  confirmed, 1-50, read from `portion` through a per-arm recode built from that
  arm's own dish prefix. In every row kcal = 20 x that number (checked below), so
  it is a 1:1 of the paper's kcal outcome. Scale labels are ours: "Photograph 1,
  the smallest portion" / "Photograph 50, the largest portion". One row is
  dropped: a "Biryani" trial whose `portion` is "TO31", a tortellini photograph,
  so which dish was on screen cannot be told (the per-arm recode does not list
  it). 1,178 rows confirm photograph 1 although the instructions required one
  increase first; going up and back down satisfies that, so they are kept.
* PERSONA. Baseline questionnaire (protocol Appendix G), all asked BEFORE the
  task. Mapped: age, gender, ethnicity (five ONS groups, already in the
  crosswalk), employment and highest qualification (scheme uk_k369t_osf), years
  of study after leaving school at 16 (the question counts A levels, so not
  named "higher education"), subjective social status (MacArthur ladder 1-10),
  currently dieting, and hunger (0-100). Qualification is stored as codes 1-9;
  labels are the questionnaire's, and the code order is the protocol's 1-9
  coding, confirmed by the pre-print's Table 1 counts. The question asks students
  for the diploma being studied for, so for 52 students education is the
  qualification sought. NOT mapped: equivalised income (an OECD-equivalised
  float, not household income), BMI (unrounded floats, as in k7tw5), the
  derived education composite and binary, COVID-19 items (where they sat in the
  flow is not recorded), and everything measured after the task: executive
  function, food choice motives, IPAQ, familiarity, liking, aim guessing.

    uv run python scripts/gen_k369t.py            # write the recipe
    uv run python scripts/gen_k369t.py --check    # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

DATA_FILE = "kcal_pace_data_OSF_final.xlsx"
DATA = REPO / "data" / "raw" / "k369t" / DATA_FILE
RECIPE = REPO / "recipes" / "images" / "k369t.yaml"

GROUP_VAR = "condition"
DISH_VAR = "food name"
PORTION_VAR = "portion"
KCAL_VAR = "kcal"

# (data label, factor level, label sentence in the instructions, label clause, shown also)
GROUPS = [
    ("No labelling", "no label", "", "", []),
    (
        "Kcal labelling",
        "kcal",
        " For each portion, the label on the left will show you the calorie content.",
        "To the left of each photograph a label showed the calorie content of that portion: "
        "20 kcal for the first photograph, 20 kcal more for each one after it, and 1000 kcal for "
        'the 50th. Beside photograph 30 the label read "600 kcal".',
        ["kcal"],
    ),
    (
        "PACE labelling",
        "PACE",
        " For each portion, the label on the left will show you the physical activity calorie "
        "equivalent, as the number of minutes of walking needed to burn off the calories in the "
        "meal.",
        "To the left of each photograph a label with a walking figure showed the minutes of walking "
        "needed to burn off the calories in that portion: 4 minutes for the first photograph, 4 "
        "minutes more for each one after it, and 200 minutes for the 50th. Beside photograph 30 "
        'the label read "120 min".',
        ["pace"],
    ),
    (
        "Kcal & PACE labelling",
        "kcal and PACE",
        " For each portion, the label on the left will show you the calorie content and the "
        "physical activity calorie equivalent, as the number of minutes of walking needed to burn "
        "off the calories in the meal.",
        "To the left of each photograph two labels, one above the other, showed the calorie content "
        "of that portion and, with a walking figure, the minutes of walking needed to burn it off: "
        "20 kcal and 4 minutes for the first photograph, 20 kcal and 4 minutes more for each one "
        "after it, and 1000 kcal and 200 minutes for the 50th. Beside photograph 30 the labels "
        'read "600 kcal" and "120 min".',
        ["kcal", "pace"],
    ),
]
RECOMMENDATION = {
    "kcal": "On average women need 2,000 kcal per day and men need 2,500 kcal per day.",
    "pace": "According to physical activity recommendations, adults should aim to take part in at "
    "least 150 minutes of moderate intensity physical activity per week (brisk walk, swim, cycle).",
}

# (data label, photo-file prefix in `portion`, image id suffix, caption printed on the picture)
DISHES = [
    ("Beef with rice", "BB", "beef_black_bean_rice", "Beef in black bean sauce with rice"),
    ("Beef stew", "BS", "beef_stew_dumplings", "Beef stew with dumplings"),
    ("Chicken pasta", "CB", "chicken_bacon_pasta_bake", "Chicken and bacon pasta bake"),
    ("Coucous and salad", "CC", "couscous_salad", "Cous cous and salad"),
    ("Chicken, chips and beans", "CCB", "chicken_chips_beans", "Chicken, chips and baked beans"),
    ("Chicken korma", "CK", "chicken_korma_rice", "Chicken korma with rice"),
    ("Chicken salad", "CS", "chicken_salad", "Chicken salad"),
    ("Fish and chips", "FCP", "fish_chips_peas", "Fish, chips and peas"),
    (
        "Grilled fish",
        "GF",
        "grilled_fish_bean_salad",
        "Grilled white fish with tomato and bean salad",
    ),
    ("Carbonara", "HM", "ham_mushroom_carbonara", "Ham and mushroom carbonara"),
    ("Lasagne", "LAS", "lasagne_peas", "Lasagne and peas"),
    ("Mac cheese", "MC", "macaroni_cheese", "Macaroni cheese"),
    ("Risotto", "MR", "mushroom_risotto", "Mushroom risotto"),
    ("Pizza", "PP", "pepperoni_pizza", "Pepperoni pizza"),
    ("Bolognese", "SB", "spaghetti_bolognese", "Spaghetti bolognese"),
    ("Sausage", "SMP", "sausage_mash_peas", "Sausage, mashed potato and peas"),
    ("Tortellini", "TO", "tortellini", "Spinach & ricotta tortellini with tomato sauce"),
    ("Biryani", "VB", "vegetable_biryani", "Vegetable biryani"),
]

PHOTO = re.compile(r"^([A-Z]+)(\d{2})x?$")

INSTRUCTIONS = (
    "For each dish, you will be asked to decide how much you would like to eat as if you were "
    "eating it as main meal.{label}\nYou can change the quantity using the arrow keys on your "
    "keyboard:\n- tap on the right arrow to increase the quantity, on the left one to decrease "
    "the quantity\n- use the space bar to select the portion size you would like to eat.\nBefore "
    "you make your choice, take the time to explore the full range of portion sizes.\nYou need to "
    "increase the amount of food at least once to be able to select a portion and continue."
)
BELOW = (
    "Use the arrow keys to change the portion size. "
    "Use the spacebar to select the amount you would like to eat."
)

# Protocol Appendix G answer options, in the protocol's own 1-9 coding.
EDU_VAR = "highest qualification"
EDUCATION = {
    1: "No qualification",
    2: "1-3 GCSEs",
    3: "4+ GCSEs",
    4: "A level",
    5: "CertHE",
    6: "DipHE",
    7: "Higher education or Bachelor’s degree",
    8: "Post-Graduate degree",
    9: "Doctoral or professional degree",
}
SSS_VAR = "subjective social status"
HUNGER_VAR = "hunger"


def arm_text(group: tuple, caption: str) -> str:
    _, _, sentence, clause, shown = group
    parts = [f'The instructions read: "{INSTRUCTIONS.format(label=sentence)}"']
    parts.append(
        "The dish was shown as one of 50 photographs of increasing portion size, captioned "
        f'"{caption}". The first photograph showed the smallest portion; each tap of the right '
        "arrow showed the next larger one, up to the 50th."
    )
    if clause:
        parts.append(clause)
    if shown:
        quoted = " ".join(f'"{RECOMMENDATION[k]}"' for k in shown)
        parts.append(f"You were also shown: {quoted}")
    parts.append(f'Photograph 30 of the 50: <image> Below the photograph: "{BELOW}"')
    return "\n\n".join(parts)


def _photos(labels: dict) -> dict[str, dict[int, int]]:
    """Per dish prefix, {portion code: photograph number}. Every label must parse."""
    out: dict[str, dict[int, int]] = {}
    for code, label in labels.items():
        m = PHOTO.match(label)
        if m is None:
            raise SystemExit(f"portion label {label!r} does not parse")
        n = int(m.group(2))
        if not 1 <= n <= 50:
            raise SystemExit(f"portion label {label!r} outside 1-50")
        out.setdefault(m.group(1), {})[int(code)] = n
    return out


def _check_kcal(ds, photos: dict[str, dict[int, int]]) -> None:
    """kcal = 20 x photograph number on every row, and exactly one row's photo is another dish's."""
    df = ds.df
    num = {c: n for codes in photos.values() for c, n in codes.items()}
    prefix_of = {c: p for p, codes in photos.items() for c in codes}
    dish_prefix = {
        int(c): next(p for d, p, _, _ in DISHES if d == lab)
        for c, lab in ds.value_labels[DISH_VAR].items()
    }
    portion = df[PORTION_VAR].astype(int)
    if not (df[KCAL_VAR].astype(int) == portion.map(num) * 20).all():
        raise SystemExit("kcal is not 20 x photograph number on every row")
    foreign = (portion.map(prefix_of) != df[DISH_VAR].astype(int).map(dish_prefix)).sum()
    if foreign != 1:
        raise SystemExit(f"{foreign} rows show another dish's photograph; 1 expected")


def recipe() -> dict:
    ds = read_any(DATA)
    labels = ds.value_labels
    group_code = {v: int(k) for k, v in labels[GROUP_VAR].items()}
    dish_code = {v: int(k) for k, v in labels[DISH_VAR].items()}
    if sorted(group_code) != sorted(g[0] for g in GROUPS):
        raise SystemExit(f"group labels changed: {sorted(group_code)}")
    if sorted(dish_code) != sorted(d[0] for d in DISHES):
        raise SystemExit(f"dish labels changed: {sorted(dish_code)}")
    photos = _photos(labels[PORTION_VAR])
    if sorted(photos) != sorted(d[1] for d in DISHES):
        raise SystemExit(f"photo prefixes changed: {sorted(photos)}")
    _check_kcal(ds, photos)

    arms = []
    for g, group in enumerate(GROUPS):
        for d, (dish, prefix, key, caption) in enumerate(DISHES):
            arms.append(
                {
                    "raw_values": {GROUP_VAR: group_code[group[0]], DISH_VAR: dish_code[dish]},
                    "condition_num": g * len(DISHES) + d,
                    "factors": {"label": group[1], "dish": caption},
                    "text": arm_text(group, caption),
                    "images": [f"k369t_{key}"],
                    "response_recode": dict(sorted(photos[prefix].items())),
                }
            )

    return {
        "study_id": "k369t",
        "source": "osf",
        "title": "kcal and PACE (minutes of walking) labelling and self-served portion size: "
        "4 labelling groups x 18 dishes",
        "data_file": DATA_FILE,
        "licence": "none stated (OSF deposit k369t). Eric Robinson gave permission for research "
        "use of the OSF data, 26 Oct 2026 (data/catalog/image_contacts.json, robinson).",
        "comparable_to_socsci210": False,
        "participant_id_var": "subject",
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_vars": [GROUP_VAR, DISH_VAR],
            "factors": ["label", "dish"],
            "arms": arms,
        },
        "outcomes": [
            {
                "var": PORTION_VAR,
                "task_num": 0,
                "question": "How much would you like to eat?",
                "scale": {
                    "min": 1,
                    "max": 50,
                    "min_label": "Photograph 1, the smallest portion",
                    "max_label": "Photograph 50, the largest portion",
                },
            }
        ],
        "response_recode": {},
        "persona_map": {
            "age": "age",
            "gender": "gender",
            "ethnicity": "ethnicity",
            "employment": "employment status",
            "education": EDU_VAR,
            "years_of_study_after_leaving_school_at_16": "years of higher education",
            "subjective_social_status": SSS_VAR,
            "currently_dieting": "dieting status",
            "hunger": HUNGER_VAR,
        },
        "persona_label_rewrite": {
            EDU_VAR: EDUCATION,
            SSS_VAR: {
                k: f"{k} on a ladder of where people stand in society, from 1 (worst off) "
                "to 10 (best off)"
                for k in range(1, 11)
            },
            HUNGER_VAR: {
                k: f"{k} on a scale from 0 (Not at all hungry) to 100 (Extremely hungry)"
                for k in range(0, 101)
            },
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
