#!/usr/bin/env python3
"""Write recipes/images/3krjz.yaml: colour in flood risk matrices (IMG48).

Proto, Recchia, Dryhurst & Freeman (Winton Centre, Cambridge), "Do colored cells
in risk matrices affect decision-making and risk perception? Insights from
randomized controlled studies", Risk Analysis 43 (2023) 2114-2128,
doi:10.1111/risa.14091 (open access, UCL Discovery 10164990). OSF project 3krjz
("Risk Matrix Comprehension (Study 4)", CC-By Attribution 4.0 International);
data, R code and every stimulus picture are in its component 9nvk3
(`project.zip`), the fielded Qualtrics questionnaire is `survey.docx` there.
The paper is the answer key, executed in tests/test_gen_3krjz.py on the BUILT
rows: the paper's exclusions give its 2,249; Levene F = 0.674 as printed; all
nine Table 1 simple slopes (colour format on the risk comparison score at low,
mean and high numeracy) reproduce to the third decimal (e.g. banding vs no colour
at mean numeracy -0.399); the Experiment 2 missing counts are the printed 67, 45
and 36; and the crossing groups pay more in both colour formats, as Table 3 has
it. Table 3's multilevel coefficients are not recomputed (lme4 model, no
equivalent here); the within-person level means differ by 5.47 / 18.20 / 12.73
against the paper's multilevel 5.534 / 18.357 / 12.823.

5,791 UK adults (Respondi, quotas on age and gender) opened the survey; 4,864
were randomised. One survey held two experiments. Experiment 1: six "which risk
would you reduce?" choices, each shown as two risk matrices side by side.
Experiment 2: five "how much would you pay?" sliders, each one matrix. The
matrix's colour format was randomised between subjects (`colour_cond`: 0 no
colour, 1 cell shading, 2 colour banding) and, independently, whether the
Experiment 2 risk reductions crossed a colour boundary (`cross_cond`: 1 crosses).
`cross_cond` is drawn for the no-colour group too but changes nothing there: the
deposit has one no-colour picture per slider, and the authors' own cleaning
script (0_cleaning.R) blanks it for that group. So the paper's "3 x 2" is five
groups for Experiment 2 and three for Experiment 1, whose pictures do not depend
on `cross_cond` at all. Code meanings are from 0_cleaning.R and confirmed by the
paper's results (crosscheck): colour banding scores lowest on Experiment 1, the
crossing groups pay more on Experiment 2.

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* DATA. The deposit's `data/data_raw.csv` is a Qualtrics export: two header rows
  under the column names (question text, import ids) and every answer as text.
  `--prep` writes `3krjz_coded.xlsx` beside it: the header rows dropped, only the
  4,864 randomised people, only the columns used here (no IP address or
  location columns), plus one `stim_<item>` column per outcome. The six
  Experiment 1 answers are coded there in the questionnaire's option order (1
  Risk A, 2 Risk B, 3 Impossible to choose; any other text stops the run); the
  `.xlsx` reader codes the remaining text columns as it codes any spreadsheet's.
* ARMS. Within subject: one ARM per distinct picture-and-format a question was
  shown with, and each outcome's `condition_var` is its `stim_<item>` column,
  holding that person's arm for that item (the `b87sm` pattern). The six
  Experiment 1 items x 3 formats = 18 arms (cn 0-17); the five Experiment 2 items
  x 5 groups (no colour; cell shading without / with crossing; colour banding
  without / with crossing) = 25 arms (cn 18-42). `stim_<item>` is arithmetic on
  `colour_cond` and `cross_cond`, nothing else. The Experiment 1 arms are shared
  by both `cross_cond` groups of a format, because their pictures are the same;
  so on those rows the `boundary` factor reads "same picture for both boundary
  groups". Held-out splits must key on condition_num or the image ids.
* WHICH PICTURE. The questionnaire names each block's folder and file stem
  (x_comp1_no-col/cells/bands ... x_wtp_low/med/high_..._cross/no-cross(_imp1));
  the item variables are the block names (comp1, wtp_low_imp2 ...), so file and
  item pair by name: `_imp1` files belong to the `*_imp1` items, the files without
  it to `*_imp2`. Checked against the paper, both ways: (a) for every
  Experiment 1 picture, the option the authors' cleaning script scores as the
  greater absolute reduction (comp1 A, comp3 A, comp4 B, comp5 A, dist1 A, dist2
  A) is the one whose marked move, read off the picture as likelihood x impact,
  is the larger (POSITIONS below; asserted in code); (b) the three `_imp2`
  sliders reduce likelihood 0.6%->0.2%, 1.8%->0.6%, 16.2%->5.4%, exactly the
  paper's low, medium and high levels. The positions were read by eye from all
  49 pictures and are the same in every colour version of a picture.
  Consequence (checker, 29 Oct 2026): in Experiment 1 the keyed answer can be
  worked out from these stated positions alone, so for those items the picture
  adds only the colour; in Experiment 2 the colour boundary is carried by the
  picture only.
* NOT BUILT. `comp2`: "THIS SET OF STIMULI WERE NOT DISPLAYED CORRECTLY TO
  PARTICIPANTS" (questionnaire; the paper drops it too). What was on screen is
  unknown, so its 3,930 answers are not built. The attention check ("please
  select 80"), an instruction check, not an outcome (CONVENTIONS). `rm_use_exp`
  ("Have you encountered or used a risk matrix before?"): asked after the format
  was explained, so neither a clean persona attribute nor an outcome of the
  manipulation. The numeracy items and the free-text questions.
* CONDITION. Every row carries the whole explanation of the format the person was
  given, word-for-word from survey.docx, with that format's two explanation
  pictures (`x_intro1_*`, `x_intro2_*`), then Q269 (the task description), then
  the item's own picture. The questionnaire's block order puts Q269 before both
  experiments. NOT narrated: the other items. The paper says the item order
  within Experiment 1 and the order of the two experiments were both randomised,
  and the deposit records neither, so a row cannot say what came before it
  (CONVENTIONS, sequence signposting). Dropped as survey mechanics: "A set of 7
  questions will now begin. Would you like to see the instructions ... again?"
  (the count includes the broken comp2), and Q131, "You will be able to revisit
  your previous answers in this section ...".
  Words that are OURS, all description of the pictures: "The screen read:",
  "Below that was this grid:", the sentence naming the axis labels (each label
  quoted as printed), "The grid marks "A" in the cell at likelihood 3 and impact
  9." and the like for each marked cell (positions are the grid's own printed
  numbers), "Below the grid:", "The next screen showed:", "Below it:", "Then the
  screen read:", "For this question the screen showed two grids side by side,
  labelled as the first was:" / "a grid labelled as the first was:". The colours
  are NOT described in the text: they are the manipulation and the picture
  carries them (QC rules 1 and 5 compare words and images).
* OUTCOMES. Wording word-for-word from survey.docx. Experiment 1: "Risk A" /
  "Risk B" / "Impossible to choose", an unordered choice, enumerated in the
  question as 1/2/3 (nominal). These items have a correct answer by the authors'
  scoring; the response is the option chosen, recorded as asked. Experiment 2: a
  0-100 slider, "1 unit = £1k", kept as given (all values are whole numbers); an
  untouched slider is blank in the export and builds no row.
* WHO. Everyone randomised who answered the item: 4,107 people. That includes the
  473 who answered some items but did not finish (their answers are real; most
  have no end-of-survey demographics), the 1,326 the authors count as failing
  the attention check, and the colour-blind in coloured groups (persona
  `colour_blindness`). The paper's analytic sample (2,249) excludes all three;
  the crosscheck applies the paper's exclusions to these rows to reproduce it.
  Numeric age, ethnicity, income, education and ideology are absent for 434
  people (2,741 rows), nearly all non-finishers; their quota age band exists
  but is not mapped.
* PERSONA. Pre-treatment, asked before the format was explained: gender and age
  band (quota questions; the band is not mapped because numeric age is), colour
  blindness, perceived flood risk where you live (1-7), personal experience of
  flooding, and the four risk-perception items (1-7, each with its own endpoint
  labels, rewritten into the label as k369t does). Asked at the END of the
  survey, mapped as stable facts no flood-matrix question could change: numeric
  age, ethnicity, household income, highest qualification, and left-right
  self-placement (`ideology`). Crosswalk schemes uk_3krjz_osf (education, Jev
  ordinal_span; ethnicity, Jev category_concept, ONS five groups; income,
  arithmetic). Gender's third option, "Other / Prefer not to say", is an answer
  and a refusal in one code and cannot be split, so it is left absent (19
  people). NOT mapped: nationality and native language (free text), the
  numeracy items (a test, taken after the tasks).

    uv run python scripts/gen_3krjz.py --prep     # (re)write the coded .xlsx
    uv run python scripts/gen_3krjz.py            # write the recipe
    uv run python scripts/gen_3krjz.py --check    # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

RAW_DIR = REPO / "data" / "raw" / "3krjz"
RAW_CSV = RAW_DIR / "9nvk3" / "x" / "project" / "data" / "data_raw.csv"
DATA_FILE = "3krjz_coded.xlsx"
DATA = RAW_DIR / DATA_FILE
RECIPE = REPO / "recipes" / "images" / "3krjz.yaml"

# (format key, colour_cond code, factor level, file stem)
FORMATS = [
    ("no_colour", 0, "no colour", "no-col"),
    ("cells", 1, "cell shading", "cells"),
    ("bands", 2, "colour banding", "bands"),
]
SAME_BOTH = "same picture for both boundary groups"
# Experiment 2 groups: (key suffix, colour_cond, cross_cond or None, format level, boundary level)
WTP_GROUPS = [
    ("no_colour", 0, None, "no colour", "no colour boundaries"),
    ("cells_no_cross", 1, 0, "cell shading", "does not cross a colour boundary"),
    ("cells_cross", 1, 1, "cell shading", "crosses a colour boundary"),
    ("bands_no_cross", 2, 0, "colour banding", "does not cross a colour boundary"),
    ("bands_cross", 2, 1, "colour banding", "crosses a colour boundary"),
]

# Cell positions as (likelihood, impact), read from the pictures. Experiment 1:
# (A1, A2, B1, B2) and the option the authors score as the greater reduction.
COMP_ITEMS = [
    ("comp1", (81, 27), (27, 27), (27, 27), (1, 27), "Risk A"),
    ("comp3", (9, 27), (9, 9), (9, 9), (9, 3), "Risk A"),
    ("comp4", (9, 3), (3, 3), (27, 3), (9, 3), "Risk B"),
    ("comp5", (81, 3), (27, 3), (27, 3), (1, 3), "Risk A"),
    ("dist1", (81, 9), (27, 9), (27, 9), (9, 9), "Risk A"),
    ("dist2", (9, 27), (9, 3), (9, 9), (9, 3), "Risk A"),
]
COMP_DIR = {"comp": "comp", "dist": "comp/distractors"}
# Experiment 2: (item variable, level, impact suffix, A1, A2)
WTP_ITEMS = [
    ("wtp_low_imp2_1", "low", "", (3, 3), (1, 3)),
    ("wtp_med_imp2_1", "med", "", (9, 3), (3, 3)),
    ("wtp_high_imp2_1", "high", "", (81, 3), (27, 3)),
    ("wtp_low_imp1_1", "low", "_imp1", (3, 1), (1, 1)),
    ("wtp_med_imp1_1", "med", "_imp1", (9, 1), (3, 1)),
]
PERCENT = {1: 0.2, 3: 0.6, 9: 1.8, 27: 5.4, 81: 16.2}
IMPACT_WORD = {1: "Minor", 3: "Limited", 9: "Moderate", 27: "Significant", 81: "Catastrophic"}


def wtp_file(level: str, imp: str, fmt_stem: str, cross: int | None) -> str:
    """The deposit's file name for one slider picture (its no-colour names are irregular)."""
    if cross is None:
        stem = "x_wtp_medium_no-col" if (level, imp) == ("med", "") else f"x_wtp_{level}_no-col"
        return f"{stem}{imp}.jpg"
    return f"x_wtp_{level}_{fmt_stem}_{'cross' if cross else 'no-cross'}{imp}.jpg"


# ---- the instrument, word-for-word from survey.docx ---------------------------------
Q235 = (
    "Please read the information provided here carefully, even if you have seen risks "
    "displayed like this before. You will need it to complete the rest of the study.\n"
    "Take as long as you need to read this information before moving onto the next page.\n"
    "Thank you for your patience!"
)
Q242 = (
    "Information about risks can be communicated in many different ways. One risk "
    "communication format is shown above.\n"
    'Along the bottom of the grid is the likelihood of a risk - "How likely is this risk to '
    'happen?". This is shown on a 1 to 81 scale, where each increase of a level on the scale '
    'means the likelihood is three times greater (e.g., "3" is three times more likely than '
    '"1"). The chances of an event happening, for each level of the scale, are shown below the '
    "grid. They are shown both as a percentage and as a frequency.\n"
    'Up the left side of the grid is the potential impact of a risk - "If this risk happens, '
    'how bad will it be?". This is shown on a 1 to 81 scale, where each increase of a level on '
    'the scale means the potential impact is three times worse (e.g., "9" is a potential impact '
    'three times worse than "3").\n'
    "By putting a risk in a particular place on the grid (here, shown by the A, to stand for "
    "e.g., the risk of a flood in town A), we can communicate both the likelihood and impact of "
    "that risk at the same time."
)
Q249 = (
    "This risk presentation format can also be used to show a change in risk, as shown above. "
    "Risk A (e.g., the risk of a flood in Town A) has increased from its initial level (A1) to "
    "a new level (A2) after something has changed about the situation (e.g., the risk of a "
    "flood in Town A after flood barriers have been compromised). The initial risk level (A1) "
    "is presented in a darker colour than the new risk level (A2)."
)
Q269 = (
    "You will now be asked to use the format you have just seen to make some decisions about "
    "different flood risks.\n"
    "Please don't worry if you find the questions hard, or think you have answered some "
    "questions wrong - some of them are designed to be challenging, and not all of the "
    "questions have one right answer.\n"
    "Remember that your answers are very important as they will help us explore how useful "
    "this risk presentation format is in helping people understand and make decisions about "
    "risk.\n"
    "All of the flood risk scenarios you are about to see are hypothetical, and have been "
    "invented specifically for this study. They do not reflect any actual flood risks anywhere "
    "in the UK or abroad."
)
COMP_Q = (
    "There are two different flood risks in two different parts of the country, risk A and "
    "risk B. You only have the resources to reduce one of these risks (either A from A1 to A2 "
    "or B from B1 to B2), as shown above. Reducing either risk costs the same amount of "
    "resources. Which risk would you reduce?"
)
COMP_OPTIONS = ["Risk A", "Risk B", "Impossible to choose"]
WTP_Q = (
    "You are an emergency planner for the local government and you have some money you can use "
    "to decrease the likelihood of risk A (from A1 to A2), as shown above. The total budget "
    "available is £100k. However, spending to further reduce this risk means this money is not "
    "available for other important governmental projects.\n"
    "How much would you be willing to pay to move risk A from A1 to A2? Indicate the amount "
    "below:\n1 unit = £1k"
)

# ---- words printed on every grid (axis labels), and our sentence naming them ---------
AXIS_TOP = ["Catastrophic 81", "Significant 27", "Moderate 9", "Limited 3", "Minor 1"]
AXIS_BOTTOM = [
    *["1", "3", "9", "27", "81"],
    *["0.2%", "0.6%", "1.8%", "5.4%", "16.2%"],
    *["1 in 500", "3 in 500", "9 in 500", "27 in 500", "81 in 500"],
]
AXES_SENTENCE = (
    'Up the left side the grid is labelled "Impact", with the rows "Minor 1", "Limited 3", '
    '"Moderate 9", "Significant 27" and "Catastrophic 81" from bottom to top; along the bottom '
    'it is labelled "Likelihood", with the columns "1", "3", "9", "27" and "81" from left to '
    'right, and below each column its chance as a percentage and as a frequency: "0.2%" and '
    '"1 in 500", "0.6%" and "3 in 500", "1.8%" and "9 in 500", "5.4%" and "27 in 500", '
    '"16.2%" and "81 in 500".'
)


def at(mark: str, pos: tuple[int, int]) -> str:
    return f'"{mark}" in the cell at likelihood {pos[0]} and impact {pos[1]}'


def grid_words(marks: list[tuple[str, tuple[int, int]]]) -> str:
    """text_in_image for one grid: the words printed on it, top to bottom, left to right."""
    rows = []
    for label in AXIS_TOP:
        impact = int(label.split()[-1])
        here = sorted((p[0], m) for m, p in marks if p[1] == impact)
        rows.append(" ".join([label] + [m for _, m in here]))
    return "\n".join(["Impact", *rows, *AXIS_BOTTOM, "Likelihood"])


INTRO1_MARKS = [("A", (3, 9))]
INTRO2_MARKS = [("A1", (1, 1)), ("A2", (1, 3))]


def intro_text() -> str:
    return "\n\n".join(
        [
            f'The screen read: "{Q235}" Below that was this grid: <image>',
            f"{AXES_SENTENCE} The grid marks {at(*INTRO1_MARKS[0])}.",
            f'Below the grid: "{Q242}"',
            f"The next screen showed: <image> It marks {at(*INTRO2_MARKS[0])} and "
            f'{at(*INTRO2_MARKS[1])}. Below it: "{Q249}"',
            f'Then the screen read: "{Q269}"',
        ]
    )


def comp_text(a1, a2, b1, b2) -> str:
    return (
        intro_text()
        + "\n\nFor this question the screen showed two grids side by side, labelled as the "
        f"first was: <image> The left grid marks {at('A1', a1)} and {at('A2', a2)}. The right "
        f"grid marks {at('B1', b1)} and {at('B2', b2)}."
    )


def wtp_text(a1, a2) -> str:
    return (
        intro_text()
        + "\n\nFor this question the screen showed a grid labelled as the first was: <image> "
        f"It marks {at('A1', a1)} and {at('A2', a2)}."
    )


def reduction(start: tuple[int, int], end: tuple[int, int]) -> float:
    """Absolute risk reduction, chance x impact, on the grid's printed values."""
    return PERCENT[start[0]] * start[1] - PERCENT[end[0]] * end[1]


def check_scoring() -> None:
    """Each Experiment 1 key names the larger marked move; each _imp2 slider is the paper's."""
    for item, a1, a2, b1, b2, key in COMP_ITEMS:
        bigger = "Risk A" if reduction(a1, a2) > reduction(b1, b2) else "Risk B"
        if bigger != key:
            raise SystemExit(f"{item}: picture says {bigger} is the bigger reduction, key {key}")
    paper = {"low": (0.6, 0.2), "med": (1.8, 0.6), "high": (16.2, 5.4)}
    for _, level, imp, a1, a2 in WTP_ITEMS:
        if not imp and (PERCENT[a1[0]], PERCENT[a2[0]]) != paper[level]:
            raise SystemExit(f"wtp {level}: picture does not match the paper's levels")


# ---- arms --------------------------------------------------------------------------
def comp_arms() -> list[dict]:
    arms = []
    for t, (item, a1, a2, b1, b2, _) in enumerate(COMP_ITEMS):
        folder = COMP_DIR[item[:4]]
        for f, (key, code, level, stem) in enumerate(FORMATS):
            arms.append(
                {
                    "raw": t * 3 + f,
                    "condition_num": t * 3 + f,
                    "factors": {"format": level, "boundary": SAME_BOTH, "task": item},
                    "text": comp_text(a1, a2, b1, b2),
                    "images": [
                        f"3krjz_intro1_{key}",
                        f"3krjz_intro2_{key}",
                        f"3krjz_{item}_{key}",
                    ],
                    "_file": f"{folder}/x_{item}_{stem}.jpg",
                    "_code": (code, None),
                }
            )
    return arms


def wtp_arms() -> list[dict]:
    arms = []
    base = 3 * len(COMP_ITEMS)
    for t, (var, level, imp, a1, a2) in enumerate(WTP_ITEMS):
        item = var.removesuffix("_1")
        for g, (suffix, colour, cross, fmt, boundary) in enumerate(WTP_GROUPS):
            key = FORMATS[colour][0]
            cn = base + t * len(WTP_GROUPS) + g
            arms.append(
                {
                    "raw": cn,
                    "condition_num": cn,
                    "factors": {"format": fmt, "boundary": boundary, "task": item},
                    "text": wtp_text(a1, a2),
                    "images": [
                        f"3krjz_intro1_{key}",
                        f"3krjz_intro2_{key}",
                        f"3krjz_{item}_{suffix}",
                    ],
                    "_file": "wtp/" + wtp_file(level, imp, FORMATS[colour][3], cross),
                    "_code": (colour, cross),
                }
            )
    return arms


def all_arms() -> list[dict]:
    return comp_arms() + wtp_arms()


def stim_column(item: str) -> str:
    return f"stim_{item}"


def stim_code(item: str, colour: float, cross: float) -> float | None:
    """This person's arm for this item: arithmetic on colour_cond and cross_cond only."""
    if pd.isna(colour):
        return None
    names = [c[0] for c in COMP_ITEMS]
    if item in names:
        return float(names.index(item) * 3 + int(colour))
    wtp = [w[0].removesuffix("_1") for w in WTP_ITEMS]
    t = wtp.index(item)
    if int(colour) == 0:
        g = 0
    else:
        if pd.isna(cross):
            return None
        g = {(1, 0): 1, (1, 1): 2, (2, 0): 3, (2, 1): 4}[(int(colour), int(cross))]
    return float(3 * len(COMP_ITEMS) + t * len(WTP_GROUPS) + g)


# ---- persona -----------------------------------------------------------------------
# One option holds an answer and a refusal together and cannot be split: absent.
GENDER_MIXED = "Other / Prefer not to say"
SCALES = {
    "flood_risk_1": ("No risk", "High risk"),
    "rpi1_1": ("Not concerned at all", "Very concerned"),
    "rpi2_1": ("Very unlikely", "Very likely"),
    "rpi3_1": ("Very unlikely", "Very likely"),
    "rpi4_1": ("Not serious at all", "Very serious"),
}
PERSONA_MAP = {
    "age": "age",
    "gender": "Q219",
    "ethnicity": "ethnicity",
    "income": "income",
    "education": "education",
    "ideology": "pol_views",
    "colour_blindness": "col_bl_binary",
    "perceived_flood_risk_where_you_live": "flood_risk_1",
    "personal_experience_of_flooding": "Q1462",
    "concern_about_flooding": "rpi1_1",
    "likelihood_of_serious_threat_to_own_health_or_wellbeing_from_flooding": "rpi2_1",
    "likelihood_of_harmful_long_term_impacts_of_flooding_on_society": "rpi3_1",
    "seriousness_of_national_flooding_impacts": "rpi4_1",
}

KEEP = [
    "tic",
    "colour_cond",
    "cross_cond",
    *[c[0] for c in COMP_ITEMS],
    *[w[0] for w in WTP_ITEMS],
    *PERSONA_MAP.values(),
]


def prep() -> pd.DataFrame:
    """The coded spreadsheet: randomised people, used columns, one stim column per item."""
    df = pd.read_csv(RAW_CSV, skiprows=[1, 2], low_memory=False)
    df = df[df["colour_cond"].notna()][KEEP].reset_index(drop=True)
    for item, *_ in COMP_ITEMS:
        # Coded in the questionnaire's option order, so 1 = Risk A, 2 = Risk B,
        # 3 = Impossible to choose; anything else in the column stops the run.
        stray = set(df[item].dropna()) - set(COMP_OPTIONS)
        if stray:
            raise SystemExit(f"{item}: unexpected answers {sorted(stray)}")
        df[item] = df[item].map({o: float(i) for i, o in enumerate(COMP_OPTIONS, start=1)})
    items = [c[0] for c in COMP_ITEMS] + [w[0].removesuffix("_1") for w in WTP_ITEMS]
    for item in items:
        df[stim_column(item)] = [
            stim_code(item, c, x) for c, x in zip(df["colour_cond"], df["cross_cond"], strict=True)
        ]
    return df


def recipe() -> dict:
    check_scoring()
    ds = read_any(DATA)
    labels = ds.value_labels
    arms = all_arms()
    for arm in arms:
        del arm["_file"], arm["_code"]

    for item, *_ in COMP_ITEMS:
        codes = set(ds.df[item].dropna().astype(int))
        if item in labels or not codes <= {1, 2, 3}:
            raise SystemExit(f"{item}: not coded 1-3 by --prep")
    comp_recode = {i: i for i in range(1, len(COMP_OPTIONS) + 1)}
    gender_code = {v: int(k) for k, v in labels["Q219"].items()}
    enumerated = "; ".join(f'{i} means "{o}"' for i, o in enumerate(COMP_OPTIONS, start=1))

    outcomes = []
    for t, (item, *_) in enumerate(COMP_ITEMS):
        outcomes.append(
            {
                "var": item,
                "task_num": t,
                "question": f"{COMP_Q} {enumerated}.",
                "scale": {"min": 1, "max": 3, "nominal": True},
                "response_recode": dict(sorted(comp_recode.items())),
                "condition_var": stim_column(item),
            }
        )
    for t, (var, *_) in enumerate(WTP_ITEMS, start=len(COMP_ITEMS)):
        outcomes.append(
            {
                "var": var,
                "task_num": t,
                "question": WTP_Q,
                "scale": {"min": 0, "max": 100},
                "response_recode": {i: i for i in range(101)},
                "condition_var": stim_column(var.removesuffix("_1")),
            }
        )

    return {
        "study_id": "3krjz",
        "source": "osf",
        "title": "Colour in flood risk matrices: 3 colour formats x boundary crossing; which risk "
        "to reduce (6 items) and willingness to pay (5 items)",
        "data_file": DATA_FILE,
        "licence": "CC-By Attribution 4.0 International (OSF project 3krjz; data, code and "
        "stimuli in its component 9nvk3).",
        "comparable_to_socsci210": False,
        "participant_id_var": "tic",
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_var": stim_column(COMP_ITEMS[0][0]),
            "factors": ["format", "boundary", "task"],
            "arms": arms,
        },
        "outcomes": outcomes,
        "response_recode": {},
        "persona_map": PERSONA_MAP,
        "persona_missing": {"Q219": [gender_code[GENDER_MIXED]]},
        "persona_label_rewrite": {
            var: {k: f"{k} on a scale from 1 ({lo}) to 7 ({hi})" for k in range(1, 8)}
            for var, (lo, hi) in SCALES.items()
        },
    }


def render() -> str:
    return yaml.safe_dump(recipe(), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--prep", action="store_true", help="write the coded .xlsx from the deposit")
    args = ap.parse_args()
    if args.prep:
        prep().to_excel(DATA, index=False)
        print(f"wrote {DATA.relative_to(REPO)}")
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
