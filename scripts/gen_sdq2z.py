#!/usr/bin/env python3
"""Derive sdq2z's conjoint arms from the data, rather than hand-typing them.

`recipes/sdq2z.yaml` declares one arm per distinct pair of buildings actually
shown, keyed on all 14 attribute codes (7 per building). Same shape as
`gen_35M5CV_bbc.py` and `gen_EFXNLX.py`, and for the same reason: the design
is 6,144 possible buildings per column, so 37.7 million possible pairs, and
`ConditionTemplate` enumerates its full product, so a sparse template cannot
hold it. The judgement lives here; the recipe is its output, and
`tests/test_gen_sdq2z.py` fails if the two drift apart.

Hankinson, TESS 209, "Do liberals and conservatives differ in attitudes
towards new housing? A conjoint". GfK KnowledgePanel, US adults, fielded
7 July - 17 July 2016. Data `TESS209_Hankinson_Client.sav` (3,019 rows);
fielded questionnaire `TESS2 209_Final.txt` (Q below = its line numbers).

THE DESIGN (Q 85-242). Five screens. Each shows two buildings side by side,
"Building 1" and "Building 2" (Table 1, Q 106-129), each described by the same
seven attributes (Table 2, Q 133-168), levels assigned per building per
screen by a design that is NOT independent: within each respondent the ten
design-row ids rise across screens and columns, so Own/Rent and residents'
view are confounded with screen and column (Building 1 on screen 1 is "Own"
for 95% of people, on screen 5 for 23%). Do not assume balance downstream. One question per screen, on the same page (Q 195-197):
"Which of these two buildings would you prefer to see built in [CITY]?"
(Q1-Q5, Q 201-242), answered Building 1 or Building 2.

`ScreenT_AttributeK_Version1/2` hold the level shown for attribute K in
Building 1 / Building 2 on screen T, every cell populated (0 missing over
3,019 x 5 x 14). The attribute index K is Table 2's order: each column's own
SPSS label is that attribute's name, checked below against the questionnaire.
`ScreenT_Version_1/2` are design-row numbers (1-6,144, ascending across
screens), not assignments with any text, and are not used.

VERSION1 IS BUILDING 1. Not stated in so many words anywhere; checked against
the responses. With Version1 read as Building 1 (response 1), a building whose
local residents "Oppose the building" is chosen 45.6% of the time against
53.4% for "Support the building"; one replacing a "Historically-designated
building" 41.7% against 51-54% for the other three land uses; and nearer is
less popular than farther (45.9% at 1/8 mile, 52.4% at 2 miles), which is the
direction the study reports. Swapping the columns would invert all three.

ATTRIBUTE ROW ORDER IS FIXED, IN TABLE 2'S ORDER. The fielded questionnaire
gives no instruction to randomise the rows: Table 1 lays out "Attribute 1
Name" .. "Attribute 7 Name" and Table 2 lists the seven in one order, and the
data carries no order variable (all 138 columns read; the only `order`
columns, `Q6_7order` and `Q8_11order`, record the order of later questions).
The PROPOSAL (Hankinson707.pdf, Proposed Instrument) did ask to "randomize
the order of the four attributes across respondents", but it describes a
different design (four of seven attributes, other levels, four pairs, a
rating question), so it is not evidence about what was fielded. This is the
EFXNLX risk (ledger 114) and the riskiest judgement in this build: if the
fielded script shuffled the rows without recording it, every condition states
an order some respondents did not see.

THE ROW HEADINGS ARE TABLE 2'S "Attribute Name" column, word-for-word (the
double space after "used?" normalised). The intro (Q 90) calls them "traits,
such as 'Height'", and no heading in Table 2 is "Height" (the nearest is "How
tall will the building be?"). The questionnaire contradicts itself here; we
follow the table, which is the part that specifies the screen, and say so.

RENDERING. Table 1 is rows of attributes with one cell per building, so each
attribute is rendered as its heading followed by the two cells, labelled with
the table's own column headings:

    How far is the building from your home?
    - Building 1: 1/8 mile (2 minute walk)
    - Building 2: 1 mile (20 minute walk)

The only characters that are ours are the list dashes and the colons.

Usage:
    uv run python scripts/gen_sdq2z.py --check
    uv run python scripts/gen_sdq2z.py --write
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from micromotives_datasets.sources import spss

REPO = Path(__file__).resolve().parents[1]
RECIPE = REPO / "recipes" / "sdq2z.yaml"
DATA = REPO / "data" / "raw" / "sdq2z" / "TESS209_Hankinson_Client.sav"

# Table 2 (Q 135-168), word-for-word: (factor name, heading, levels by code).
# The codes are the .sav's; `_check_against_data` asserts the data's own value
# labels and column labels say exactly this, so a transcription slip fails
# loudly instead of shipping.
TABLE2: list[tuple[str, str, dict[int, str]]] = [
    (
        "distance",
        "How far is the building from your home?",
        {
            1: "1/8 mile (2 minute walk)",
            2: "1/2 mile (10 minute walk)",
            3: "1 mile (20 minute walk)",
            4: "2 miles (40 minute walk)",
        },
    ),
    (
        "residents_view",
        "How do local residents feel about the building?",
        {1: "Support the building", 2: "Oppose the building", 3: "No opinion"},
    ),
    (
        "affordable_share",
        "What share of units will be affordable for low-income residents?",
        {
            1: "None of the units",
            2: "One-quarter of the units",
            3: "Half of the units",
            4: "All of the units",
        },
    ),
    (
        "height",
        "How tall will the building be?",
        {1: "2 stories", 2: "3 stories", 3: "6 stories", 4: "12 stories"},
    ),
    (
        "current_land_use",
        "How is the land currently used? This will be demolished.",
        {
            1: "Empty building",
            2: "Parking lot",
            3: "Historically-designated building",
            4: "Open field",
        },
    ),
    ("tenure", "Will residents own or rent?", {1: "Own", 2: "Rent"}),
    (
        "units",
        "How many units will the building have?",
        {1: "12 units", 2: "24 units", 3: "48 units", 4: "96 units"},
    ),
]
N_ATTRS = len(TABLE2)
SIDES = (1, 2)  # Building 1 = Version1, Building 2 = Version2 (see docstring)


def _condition_vars(t: int) -> list[str]:
    """Screen t's 14 allocation columns: Building 1's seven, then Building 2's."""
    return [f"Screen{t}_Attribute{k}_Version{s}" for s in SIDES for k in range(1, N_ATTRS + 1)]


# Arms are keyed on screen 1's names; every screen's columns map onto these.
KEY_VARS = _condition_vars(1)
FACTORS = [f"{name}_{s}" for s in SIDES for name, _, _ in TABLE2]


def _check_against_data(ds: Any) -> None:
    """The transcription above must be what the data's own metadata says."""
    for t in range(1, 6):
        for s in SIDES:
            for k, (name, heading, levels) in enumerate(TABLE2, start=1):
                col = f"Screen{t}_Attribute{k}_Version{s}"
                label = " ".join(ds.column_labels[col].split())
                if label != heading:
                    raise ValueError(f"{col}: column label {label!r} is not {heading!r}")
                got = {int(c): v for c, v in ds.value_labels[col].items()}
                if got != levels:
                    raise ValueError(f"{col} ({name}): value labels {got} are not {levels}")


def _render(codes: list[int]) -> str:
    """The table, one attribute per paragraph, in Table 2's fixed order."""
    paragraphs = []
    for k, (_, heading, levels) in enumerate(TABLE2):
        b1, b2 = codes[k], codes[N_ATTRS + k]
        paragraphs.append(f"{heading}\n- Building 1: {levels[b1]}\n- Building 2: {levels[b2]}")
    return "\n\n".join(paragraphs)


def build_arms() -> list[dict[str, Any]]:
    """Every distinct 14-attribute pair shown AND answered, first-seen order.

    A screen whose choice was refused (-1) yields no row, so a pair seen only on
    refused screens would be an arm with no rows, which QC rule 2 rightly flags.
    Those pairs are left out; the refusals themselves are dropped by the
    recipe's `missing_codes` either way.
    """
    ds = spss.read(DATA)
    _check_against_data(ds)
    arms: list[dict[str, Any]] = []
    seen: set[tuple[int, ...]] = set()
    for t in range(1, 6):
        cols = _condition_vars(t)
        for _, row in ds.df.iterrows():
            values = [row[c] for c in cols]
            if any(v is None or v != v for v in values):  # NaN
                raise ValueError(f"screen {t}: a missing attribute code; none expected")
            answer = row[f"Screen{t}"]
            if answer not in (1, 2):
                if answer != -1:
                    raise ValueError(f"Screen{t}: unexpected response code {answer!r}")
                continue
            codes = [int(float(v)) for v in values]
            key = tuple(codes)
            if key in seen:
                continue
            seen.add(key)
            factors = {
                f: TABLE2[i % N_ATTRS][2][code]
                for i, (f, code) in enumerate(zip(FACTORS, codes, strict=True))
            }
            arms.append(
                {
                    "raw_values": dict(zip(KEY_VARS, codes, strict=True)),
                    "condition_num": len(arms),
                    "factors": factors,
                    "text": _render(codes),
                }
            )
    return arms


# Q1-Q5 (Q 201-242), identical stems. The city fill is replaced by the
# CONVENTIONS.md own-place clause; the options sentence is ours (PZB01G).
PLACE = "(here the screen named the place where you live)"
QUESTION = (
    f"Which of these two buildings would you prefer to see built in {PLACE}? "
    '1 means "Building 1"; 2 means "Building 2".'
)


def build_outcomes() -> list[dict[str, Any]]:
    return [
        {
            "var": f"Screen{t}",
            "task_num": t - 1,
            "question": QUESTION,
            "scale": {"min": 1, "max": 2, "nominal": True},
            "condition_vars": _condition_vars(t),
        }
        for t in range(1, 6)
    ]


# Q 86-97, word-for-word except the four city fills.
SHARED_CONTEXT = (
    f"From your ZIP code, you live in {PLACE}. Now, imagine that someone wants to build "
    f"a residential building in {PLACE}.\n\n"
    "Starting with the next page, you will see pairs of residential buildings. Each "
    "building will be described in a column of seven traits, such as 'Height'. For each "
    f"page, please select the building that you would prefer to see built in {PLACE}.\n\n"
    "Even if you would like more information or are opposed to both, please indicate "
    "which of the two buildings you would prefer.\n\n"
    "Note: These building proposals are not for where you would prefer to move or live. "
    f"Instead, they are for what kind of housing you would like to see built in {PLACE}."
)

LICENCE = (
    "none stated on the OSF deposit (checked via the OSF API, 2026-11-09: node_license "
    "null, no license relationship). TESS archived its post-2009 projects through the "
    "Roper Center and its own site states no reuse terms; TESS has since suspended "
    "operations. So there is no explicit grant of redistribution rights for this "
    "deposit, and none should be assumed."
)

NOTES = """\
TESS 209 (Hankinson), "Do liberals and conservatives differ in attitudes towards
new housing? A conjoint". GfK KnowledgePanel, US adults. Response rate report
("TESS3 209 - Hankinson Response Rate Report.txt", line 6): fielded 7/07/2016 -
7/17/2016, 5,426 fielded, 3,344 completed, 3,010 qualified completes. The .sav
has 3,019 rows, nine more than that report's qualified count; no column marks
them and the report does not say how it counted, so all 3,019 are kept and the
gap is recorded rather than explained. Line numbers below (Q) are the fielded
questionnaire "TESS2 209_Final.txt".

GENERATED. The arms and outcomes are written by `scripts/gen_sdq2z.py`; its
module docstring carries the full design argument, and
`tests/test_gen_sdq2z.py` fails if this file and the generator disagree. Do
not edit the arms by hand.

THE DESIGN. Paired-profile conjoint, five screens per respondent, two
buildings per screen, seven attributes per building (Table 1 and Table 2,
Q 101-168). Levels were NOT drawn independently: the design-row ids rise
within each respondent across screens and columns, so Own/Rent and residents'
view are confounded with screen and column. Attribute ROW order on screen is
not recorded anywhere in the deposit (no order column; the docx holds only a
logo); Table 2's order is the only one the instrument evidences and is
assumed, unverified. One forced choice per screen,
Q1-Q5 (Q 201-242), stored in `Screen1`..`Screen5`: 1 = Building 1, 2 =
Building 2, -1 = Refused (dropped: 76 + 102 + 92 + 87 + 108 = 465). 3,019 x 5 =
15,095 screens, minus 465 = 14,630 rows, from 2,995 people (24 refused all
five). 15,085 distinct pairs among the 15,095 screens and 14,620 among the
14,630 answered ones (ten pairs drawn twice); arms are declared for answered
screens only, so 14,620 arms, every one with rows. No screen ever shows two
identical buildings.

STRUCTURED METADATA. Every arm's `factors` carries all 14 levels by name
(`distance_1` .. `units_1` for Building 1, `distance_2` .. `units_2` for
Building 2), so a consumer can select rows by attribute without parsing text.

ATTRIBUTE ROW ORDER: FIXED, Table 2's order. The fielded questionnaire says
nothing about shuffling the rows, and no order variable exists in the data
(the two `order` columns concern Q6-Q11). The proposal did ask for row order to
be randomised, but for a different, unfielded design. Riskiest judgement in
this build; see the generator's docstring.

ROW HEADINGS are Table 2's "Attribute Name" column. The intro's "seven traits,
such as 'Height'" (Q 90) does not match any of them (the height row reads "How
tall will the building be?"); the questionnaire contradicts itself and we follow
the table. Not resolvable from the deposit.

WORDS WE ADDED. (1) The respondent's city: the screen inserted it from their
ZIP code at five places (Q 86, 87, 91, 97 and each of Q1-Q5). Each is replaced
by the CONVENTIONS.md own-place clause, word-for-word: "(here the screen named
the place where you live)". It is true of every row: every respondent's city
was looked up from the ZIP code they entered, and anyone whose ZIP code was not
in the lookup table was terminated (Q 59). The deposit DOES hold the city
(`DOV_City`, 882 distinct US places, none blank), which goes beyond the
ruling's stated case (a fill the deposit does not hold). It is not inserted
because (a) the pipeline cannot place a respondent-level string in the
condition or the question, only arm-level text and coded directives, and (b)
these rows are built for a UK corpus, where 882 US place names in the
condition would carry the US into every row. That extension of the ruling
needs rich's sign-off. (2) Each question appends '1 means "Building 1"; 2
means "Building 2".' (the PZB01G nominal convention), naming the table's own
column headings. (3) The list dashes and colons in the table.

KEPT WORD-FOR-WORD THOUGH US IN FLAVOUR: "From your ZIP code", "stories",
"Parking lot", "Historically-designated building", distances in miles. None
needs US knowledge to answer; a UK adult could take part as written with their
own town in the fill. "Starting with the next page, you will see pairs ..." is
kept: it cites no position or count, and it carries the instruction to choose.

NOT IN THIS RECIPE. Q6A-Q13 (Q 244-393): expected price and rent changes, and
support for lowering development restrictions, with fills of the city's
housing-unit count and a "10% more" figure (`DOV_Units`, `DOV_TenPct`). Not a
randomised manipulation in themselves; `XTESS209` randomises only whether they
came before or after the conjoint (Q 75-77). SocSci210 built exactly those
items, with that order as the condition (see CROSSCHECK); they are a separate
sub-experiment and not built here.

CROSSCHECK (comparable_to_socsci210: false). SocSci210 has 23,843 rows for
sdq2z, 3,015 participants, three conditions and two tasks, responses 1-7: the
housing-price and support items, split by conjoint-first / conjoint-second.
None of the conjoint is in it, so there is no numeric answer key for this
recipe. Our independent check is the direction of the attribute effects (see
the generator's VERSION1 IS BUILDING 1).

ORDER COUNTERBALANCE. `XTESS209` (1 = conjoint first, 1,481; 2 = conjoint
second, 1,538) decides whether the respondent had already answered Q6A-Q13 when
they reached the conjoint. The conjoint's own screens are word-for-word the same
under both orders, and narrating eight earlier questions into every condition
would put the other sub-experiment's content into this one. Rejected as a factor
here, and recorded in `considered_and_rejected`.

PERSONA (KnowledgePanel profile, the TESS sibling set as in 5hqan.yaml):
gender PPGENDER, education PPEDUCAT, ethnicity PPETHM, income PPINCIMP,
marital_status PPMARIT, employment PPWORK, region PPREG4, household_size
PPHHSIZE, housing_type PPHOUSE, housing_ownership PPRENT, urban_rural PPMSACAT,
internet_access PPNET, party_id xParty7, ideology xIdeo, religion xRel1,
religious_attendance xRel2. No PPAGE in this file, only `ppagecat` (7 bands)
and `ppagect4`; the persona's `age` field holds whole years and would drop a
band, so the 7-band variable goes in as `age_band`. Its code 99 "Under 18"
never occurs and is not declared. Non-answers left empty: xParty7 8 "Refused"
(0 rows) and 9 "Missing" (119); xIdeo, xRel1, xRel2 -1 "Refused". xRel1 code 2's
value label is severed at 120 characters ("... Church of Ch"); restored from the
questionnaire's own option, Q 437. Not mapped: QZIP, xzip, DOV_City, PPSTATEN,
ppreg9 (finer location than the sibling recipes carry, and DOV_City is the
fill discussed above); xppracem (a second race scheme beside PPETHM); QOWN (a
screener asked in this survey, and PPRENT already carries tenure).

recipe_prep.py (2026-11-09), what was overruled: it offered `Screen1_Version_1`
(conf 0.32) and `XTESS209` (0.33) as the assignment; neither is, the 14
attribute columns per screen are. It called the attribute level "No opinion"
a non-answer (conf 0.74-0.88); it is stimulus text, a level of "How do local
residents feel about the building?", not anything a respondent said. It chose
PPEDUC for education (conf 0.98); PPEDUCAT is used, as in every sibling TESS
recipe.
"""


def build_recipe() -> dict[str, Any]:
    return {
        "study_id": "sdq2z",
        "source": "tess",
        "title": "Do liberals and conservatives differ in attitudes towards new housing? "
        "A conjoint",
        "data_file": "TESS209_Hankinson_Client.sav",
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "notes": NOTES,
        "condition": {
            "source_vars": KEY_VARS,
            "factors": FACTORS,
            "considered_and_rejected": {
                "XTESS209": "Order counterbalance: 1 = the conjoint came before Q6A-Q13, "
                "2 = after. The conjoint's own screens are word-for-word the same under "
                "both, and Q6A-Q13 are a separate sub-experiment not built here, so "
                "this recipe does not narrate them into the condition.",
            },
            "shared_context": SHARED_CONTEXT,
            "arms": build_arms(),
        },
        "outcomes": build_outcomes(),
        "response_recode": {1: 1, 2: 2},
        "missing_codes": [-1],
        "persona_map": {
            "age_band": "ppagecat",
            "gender": "PPGENDER",
            "education": "PPEDUCAT",
            "ethnicity": "PPETHM",
            "income": "PPINCIMP",
            "marital_status": "PPMARIT",
            "employment": "PPWORK",
            "region": "PPREG4",
            "household_size": "PPHHSIZE",
            "housing_type": "PPHOUSE",
            "housing_ownership": "PPRENT",
            "urban_rural": "PPMSACAT",
            "internet_access": "PPNET",
            "party_id": "xParty7",
            "ideology": "xIdeo",
            "religion": "xRel1",
            "religious_attendance": "xRel2",
        },
        "persona_missing": {
            "xParty7": [8, 9],
            "xIdeo": [-1],
            "xRel1": [-1],
            "xRel2": [-1],
        },
        "persona_label_rewrite": {
            "xRel1": {
                2: "Evangelical or Protestant Christian (Baptist, Lutheran, Methodist, "
                "Presbyterian, Episcopalian, Pentecostal, Church of Christ, etc.)",
            },
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="compare against the recipe")
    ap.add_argument("--write", action="store_true", help="(re)write the whole recipe")
    args = ap.parse_args()

    generated = build_recipe()
    print(
        f"generated {len(generated['condition']['arms']):,} arms, "
        f"{len(generated['outcomes'])} outcomes"
    )
    if args.write:
        RECIPE.write_text(yaml.safe_dump(generated, sort_keys=False, allow_unicode=True, width=100))
        print(f"wrote {RECIPE.relative_to(REPO)}")
        return 0
    if not RECIPE.exists():
        print(f"{RECIPE} does not exist yet -- run with --write")
        return 1
    current = yaml.safe_load(RECIPE.read_text())
    if current == generated:
        print("IDENTICAL — the recipe is exactly what this file derives")
        return 0
    for key in generated:
        if current.get(key) != generated[key]:
            print(f"DIFFERS: {key}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
