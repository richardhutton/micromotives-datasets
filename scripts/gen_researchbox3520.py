#!/usr/bin/env python3
"""Write the ResearchBox 3520 recipe (Edenbrandt & Häsler, UK beef mince choices, text arms).

    uv run python scripts/gen_researchbox3520.py --prep    # write the coded data file
    uv run python scripts/gen_researchbox3520.py           # write the recipe
    uv run python scripts/gen_researchbox3520.py --check   # exit 1 if the recipe differs

Edenbrandt AK & Häsler B, "Unravelling theory in choice analysis: do consumers fill in the
blanks?", European Review of Agricultural Economics, doi:10.1093/erae/jbaf009. ResearchBox
3520. A discrete choice experiment, UK adults who buy food: each person makes 8 choices
between two 500 g packs of beef mince, or neither. Ngene design, 24 choice sets in 3 blocks
of 8 (Data/Beef_Design_1Sept2023.xlsx). Four between-person arms: the four labels (RSPCA
Assured, Fair to Nature, Low Climate Impact, Premium Quality Angus) shown as logos (VC, VL)
or as text (TC, TL); "comprehensive" (C) states every label, present or "Not ...";
"affirmative" (L, the authors' A) shows only the labels a product has.

SCOPE (rich's ruling, 23 Nov 2026). Only the two TEXT arms are built, as one recipe whose
`label_display` factor is the TC/TL contrast. The logo arms are pictures and go to the image
list. The lamb choice experiment in the same survey is a different sample and not built.

SAMPLE: the authors' analysis file, Other/Beef_CE_Survey.txt (1,987 people x 8 tasks, the
file every Apollo model reads). It is checked here against the raw export
(Data/Beef_Lamb_23_replication.xls): the do-file's rules (Code/Beef Lamb Data structuring.do:
finished, consent, some responsibility for food purchases, attention check = "Often", age
18+, eats beef or lamb, at least 2.5 minutes, routed to a beef arm, did not ask to be
discarded) keep exactly 1,987, by arm 496/491/497/503, and every kept person's (arm,
duration, age, gender, raw answer to each choice variable) matches one person in the
analysis file and vice versa. So the analysis file's `choice` IS the raw Qualtrics code.

WORDING: the survey PDF (Materials/Survey beef mince.pdf), read with pdftotext; never typed
in except the intro's paragraph breaks, whose words are asserted equal to the PDF's. In the
text arms every product card is text in the PDF: 48 screens x 2 cards. Each card is
transcribed word-for-word, including the PDF's own typo "'RSPCA Assued'" (36 of the 96
cards, in both TC and TL, positive and "Not" forms alike; the rest read "'RSPCA Assured'").
The typo is per card, so card text is NOT a function of the attribute levels: every choice
set is its own arm, its words taken from its own screen.

TIE OF SCREEN TO DESIGN, proved not assumed. Each PDF screen's two cards are parsed into
attribute levels and matched to the one choice set in that block of the design with the
same two products; the match is unique for all 48 screens, every set is matched once per
arm, and the PDF's screens run in the design's order within each block (the do-file's
c<set>b<block> variables, in the same order). Which card the PDF prints first varies: the
design's alternative 2 on 15 of TC's 24 screens and 10 of TL's, and the same set is printed
in opposite orders in the two arms on 11 sets, which is what a print of a survey with
randomised choice order looks like. The export codes alternative 1 as 1 and 2 as 2 (the
do-file merges code k with design alternative k, and the analysis file's attributes equal
the design file's on every row). Checked against behaviour: people chose the cheaper product
on 67% of the text arms' non-opt-out choices under that mapping; and a pooled MNL fitted
under it fits better than the same set swapped on 22 of the 24 sets (log-likelihood
difference 2.0 to 704.7), the other two (13 and 22) being near-balanced sets where swapping
changes it by under 2 either way.

OPTION ORDER (the riskiest judgement). No .qsf is deposited and no per-person order is
recorded, so the cards' on-screen order cannot be established, and the printed order
disagrees with the export's from screen to screen. By rich's ruling on osf_ct8ae
(docs/CONVENTIONS.md, "Choice sets whose on-screen order was randomised and not recorded",
second paragraph) the row lists the options in the data file's order with the clause
"(the options are listed in the data file's order; the order on screen was not recorded)",
the answer coded to that list, and each option's attributes kept as factors so training can
re-order and remap. The opt-out is last on every printed screen and stays last.

TASK ORDER. Each row carries only its own screen. Whether the 8 screens of a block were
shown in a fixed or random order is not recorded either way; nothing narrates a position.
The intro's "You will make in total 8 purchase choices." is survey mechanics (CONVENTIONS,
"Sequence signposting") and is left out.

PERSONA: age (years; the analysis file has 18-87, none missing) and gender (the PDF's
labels: 1 Female, 2 Male; 3 "Prefer not to say" and 4 "Prefer to self-describe" left blank,
as in researchbox547; 3 does not occur, 4 is 4 people).
"""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
STUDY_ID = "researchbox3520"
EXPERIMENT = "text"
RAW = REPO / "data" / "raw" / STUDY_ID
BOX = RAW / "ResearchBox 3520"
PDF = BOX / " Materials" / "Survey beef mince.pdf"
CE = BOX / " Other" / "Beef_CE_Survey.txt"
DESIGN = BOX / " Data" / "Beef_Design_1Sept2023.xlsx"
RAW_EXPORT = BOX / " Data" / "Beef_Lamb_23_replication.xls"
DATA_FILE = f"{STUDY_ID}_{EXPERIMENT}.csv"
RECIPE = REPO / "recipes" / f"{STUDY_ID}_{EXPERIMENT}.yaml"

LICENCE = (
    'CC BY 4.0, stated on the box page https://researchbox.org/3520 ("All content posted '
    'to ResearchBox is under a CC By 4.0 License"). Read 23 Nov 2026.'
)
PAPER = (
    'Edenbrandt AK & Häsler B, "Unravelling theory in choice analysis: do consumers fill in '
    'the blanks?", European Review of Agricultural Economics, doi:10.1093/erae/jbaf009. '
    "ResearchBox 3520 (https://researchbox.org/3520)."
)
TITLE = (
    "Which of two packs of beef mince would you buy, or neither? Welfare, nature, climate "
    "and quality labels shown as text, every label stated or only those present (UK)"
)

# Arm prefix in the export -> (treatment code in the analysis file, factor level, PDF tag,
# offset added to the choice set's number to make the arm code).
ARMS: dict[str, tuple[int, str, str, int]] = {
    "tc": (3, "comprehensive", "Beef_TC", 0),
    "tl": (4, "affirmative", "Beef_TL", 24),
}
GENDER = {1: "Female", 2: "Male"}  # 3 Prefer not to say, 4 Prefer to self-describe: blank

QUESTION = (
    "Which beef mince product would you purchase if it was a real purchase situation? "
    "Keep in mind how you normally think, and what you are prepared to pay when grocery "
    "shopping."
)
OPT_OUT = "If these products were the only to choose from I would not purchase any"
CLAUSE = "(the options are listed in the data file's order; the order on screen was not recorded)"
DROPPED = "You will make in total 8 purchase choices."

# The intro's paragraphs. Only the breaks are ours: `intro()` asserts the words, joined,
# are exactly the PDF's for both text arms.
INTRO_PARAGRAPHS = [
    "In this survey, we are interested in your preferences regarding specific food products.",
    "We would like you to imagine that you are about to purchase 500 grams of beef mince. "
    "This product is described using a number of characteristics.",
    "We have two options for you to choose from. We would like you to choose the one you are "
    "most likely to buy just as if you were in a real shopping situation. Imagine that the "
    "products that you are presented with are the only products available to choose from. "
    + DROPPED,
    "Please answer all choice tasks as if they were real shopping situations.",
    "Before we ask you to start, we will give you some information about the food "
    "characteristics of the beef mince products.",
    "RSPCA Assured\nProduct meets standards of higher animal welfare, from birth to slaughter "
    "including housing conditions, health and veterinary care, diet, handling and slaughter "
    "practices.",
    "Fair-to-Nature - certified\nProducer applies farming practices that enhance biodiversity "
    "and protect the natural environment.",
    "Low Climate Impact - certified\nThe lifecycle carbon footprint (CO2 equivalents) of a "
    "product with this label is significantly lower than for the typical beef product "
    "produced in the UK.",
    "Premium Quality Angus - certified\nHigh quality meat from Aberdeen Angus breed, "
    "specially selected for flavour, tenderness, and marbling.",
    "All beef mince products are produced in the United Kingdom with British beef.",
    "Just like in a real shopping situation, you can see the price and fat content of the "
    "beef mince products.",
    "Other than the indicated characteristics, the products are the same, i.e. they all have "
    "the same production date, and all products have the same packaging type as the one that "
    "you normally purchase.",
]

# Card line -> (design column, level). The label lines in the order the cards print them.
LABELS = [
    ("cl", "Low Climate Impact", re.compile(r"^(Not )?'Low Climate Impact' certified$")),
    ("ftn", "Fair to Nature", re.compile(r"^(Not )?'Fair to Nature' certified$")),
    ("q", "Premium Quality Angus", re.compile(r"^(Not )?'Premium Quality Angus' certified$")),
    ("rspca", "RSPCA Assured", re.compile(r"^(Not )?'RSPCA (Assured|Assued)'$")),
]
FAT = re.compile(r"^(\d+)% fat$")
PRICE = re.compile(r"^£(\d+\.\d\d)$")
ATTRS = ["rspca", "fat", "ftn", "q", "cl", "price"]
FACTOR_NAME = {
    "rspca": "rspca",
    "fat": "fat",
    "ftn": "fair_to_nature",
    "q": "premium_quality_angus",
    "cl": "low_climate_impact",
    "price": "price",
}


def norm(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"')
    return s.replace("”", '"').replace(" ", " ").strip()


@cache
def pdf_lines() -> tuple[str, ...]:
    out = subprocess.run(
        ["pdftotext", "-layout", str(PDF), "-"], capture_output=True, text=True, check=True
    )
    return tuple(norm(x) for x in out.stdout.splitlines())


def section(start: str, end: str) -> list[str]:
    lines = list(pdf_lines())
    assert lines.count(start) == 1 and lines.count(end) == 1, (start, end)
    return lines[lines.index(start) + 1 : lines.index(end)]


def intro(tag: str) -> str:
    """The arm's intro page, with our paragraph breaks and without DROPPED."""
    words = " ".join(section(f"Intro_{tag}", f"{tag}_B1")).split()
    assert words == " ".join(INTRO_PARAGRAPHS).split(), tag
    assert sum(p.count(DROPPED) for p in INTRO_PARAGRAPHS) == 1
    return "\n\n".join(INTRO_PARAGRAPHS).replace(" " + DROPPED, "")


@dataclass(frozen=True)
class Card:
    lines: tuple[str, ...]  # word-for-word, "Beef mince" first
    levels: tuple[float, ...]  # in ATTRS order

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


def parse_card(lines: list[str], comprehensive: bool) -> Card:
    assert lines[0] == "Beef mince", lines
    body = lines[1:]
    got: dict[str, float] = {}
    i = 0
    for col, _, rx in LABELS:
        m = rx.match(body[i]) if i < len(body) else None
        if m:
            assert comprehensive or not m.group(1), body  # affirmative never says "Not"
            got[col] = 0.0 if m.group(1) else 1.0
            i += 1
        else:
            assert not comprehensive, body  # comprehensive states every label
            got[col] = 0.0
    fat, price = FAT.match(body[i]), PRICE.match(body[i + 1])
    assert fat and price and len(body) == i + 2, body
    got["fat"], got["price"] = float(fat.group(1)), float(price.group(1))
    return Card(tuple(lines), tuple(got[a] for a in ATTRS))


def screens(tag: str, block: int, comprehensive: bool) -> list[tuple[Card, Card]]:
    end = (
        f"{tag}_B{block + 1}"
        if block < 3
        else ("Intro_Beef_TL" if tag == "Beef_TC" else "Intro CE Lamb")
    )
    body = [x for x in section(f"{tag}_B{block}", end) if x]
    q1 = "Which beef mince product would you purchase if it was a real purchase situation?"
    starts = [i for i, x in enumerate(body) if x == q1]
    assert len(starts) == 8 and starts[0] == 0, (tag, block)
    out = []
    for a, b in zip(starts, [*starts[1:], len(body)], strict=True):
        task = body[a:b]
        assert " ".join(task[:3]) == QUESTION, task[:3]
        assert " ".join(task[-2:]) == OPT_OUT, task[-2:]
        cards = task[3:-2]
        heads = [i for i, x in enumerate(cards) if x == "Beef mince"]
        assert heads[0] == 0 and len(heads) == 2, cards
        out.append(
            (
                parse_card(cards[: heads[1]], comprehensive),
                parse_card(cards[heads[1] :], comprehensive),
            )
        )
    return out


@cache
def design() -> pd.DataFrame:
    return pd.read_excel(DESIGN, sheet_name="Design").set_index("Choice situation")


def alt(s: int, k: int) -> tuple[float, ...]:
    row = design().loc[s]
    return tuple(float(row[f"alt{k}.{a}"]) for a in ATTRS)


@cache
def choice_sets(prefix: str) -> dict[int, tuple[Card, Card]]:
    """Choice set -> (card of design alternative 1, card of alternative 2), for one arm."""
    _, level, tag, _ = ARMS[prefix]
    out: dict[int, tuple[Card, Card]] = {}
    for block in (1, 2, 3):
        in_block = sorted(int(s) for s in design().index[design().Block == block])
        matched = []
        for first, second in screens(tag, block, level == "comprehensive"):
            hits = [s for s in in_block if {alt(s, 1), alt(s, 2)} == {first.levels, second.levels}]
            assert len(hits) == 1, (prefix, block, hits)
            s = hits[0]
            # The PDF prints either alternative first (see the docstring); file them by
            # the design's numbering, which is the export's.
            out[s] = (first, second) if first.levels == alt(s, 1) else (second, first)
            assert out[s][0].levels == alt(s, 1) and out[s][1].levels == alt(s, 2)
            matched.append(s)
        assert matched == in_block, (prefix, block, matched)  # once each, in design order
    assert sorted(out) == list(range(1, 25))
    return out


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


@cache
def analysis_file() -> pd.DataFrame:
    ce = pd.read_csv(CE, sep="\t")
    d = design()
    for _, r in ce.drop_duplicates("Choicesituation").iterrows():
        s = int(r.Choicesituation)
        assert int(d.loc[s].Block) == int(r.Block)
        for k in (1, 2):
            got = tuple(float(r[f"{a if a != 'q' else 'quality'}{k}"]) for a in ATTRS)
            assert got == alt(s, k), s
    return ce


def raw_signatures() -> dict[str, Any]:
    """The do-file's sample rules applied to the raw export, and each kept person's key."""
    d = pd.read_excel(RAW_EXPORT)
    d = d[d.finished == 1]
    d = d[d.consent == 1]
    d = d[d.responsible_purchase != 4]
    d = d[d.attention == 3]
    d = d[~(d.age < 18)]  # Stata: a missing age is not < 18
    d = d[~((d.food_habits_2 == 1) & (d.food_habits_3 == 1))]
    d = d[d.durationinseconds / 60 >= 2.5]
    prefixes = {1: "vc", 2: "vl", 3: "tc", 4: "tl"}
    treat = pd.Series(pd.NA, index=d.index, dtype="Int64")
    for t, p in prefixes.items():  # the do-file's order: a later arm overwrites
        hit = d[[f"{p}_c2b1", f"{p}_c5b2", f"{p}_c10b3"]].notna().any(axis=1)
        treat[hit] = t
    d = d.copy().assign(treatment=treat)
    d = d[d.treatment.notna()]
    d = d[d.respondent_quality != 0]
    sigs = []
    for _, r in d.iterrows():
        p = prefixes[int(r.treatment)]
        cols = [c for c in d.columns if c.startswith(f"{p}_c") and pd.notna(r[c])]
        sigs.append(
            (
                int(r.treatment),
                int(r.durationinseconds),
                int(r.age),
                int(r.gender),
                tuple(sorted((c, int(r[c])) for c in cols)),
            )
        )
    return {"n": len(d), "by_arm": d.treatment.value_counts().to_dict(), "sigs": sigs}


def analysis_signatures() -> list[tuple[Any, ...]]:
    prefixes = {1: "vc", 2: "vl", 3: "tc", 4: "tl"}
    out = []
    for _, g in analysis_file().groupby("id"):
        f = g.iloc[0]
        p = prefixes[int(f.treatment)]
        cols = tuple(
            sorted(
                (f"{p}_c{int(r.Choicesituation)}b{int(r.Block)}", int(r.choice))
                for _, r in g.iterrows()
            )
        )
        out.append((int(f.treatment), int(f.duration), int(f.age), int(f.gender), cols))
    return out


def check_sample() -> None:
    raw = raw_signatures()
    assert raw["n"] == 1987 and raw["by_arm"] == {1: 496, 2: 491, 3: 497, 4: 503}, raw["by_arm"]
    assert sorted(raw["sigs"]) == sorted(analysis_signatures())


def prep() -> pd.DataFrame:
    """One row per text-arm person: each set's arm code and answer (1/2/3), and the persona."""
    ce = analysis_file()
    rows = []
    for pid, g in ce.groupby("id"):
        t = int(g.treatment.iloc[0])
        prefix = next((p for p, a in ARMS.items() if a[0] == t), None)
        if prefix is None:
            continue
        assert len(g) == 8 and g.Choicesituation.nunique() == 8
        row: dict[str, Any] = {"pid": int(pid)}
        for _, r in g.iterrows():
            s = int(r.Choicesituation)
            row[f"a_c{s}"] = s + ARMS[prefix][3]
            row[f"r_c{s}"] = int(r.choice)  # 1 = design alt 1, 2 = alt 2, 3 = neither
        age = int(g.age.iloc[0])
        assert 18 <= age <= 120
        row["age"] = age
        row["gender"] = GENDER.get(int(g.gender.iloc[0]))
        rows.append(row)
    cols = ["pid"] + [f"{x}_c{s}" for s in range(1, 25) for x in ("a", "r")] + ["age", "gender"]
    out = pd.DataFrame(rows)[cols]
    for c in cols[1:-1]:
        out[c] = out[c].astype("Int64")
    assert len(out) == 1000 and out.pid.is_unique
    return out


# ---------------------------------------------------------------------------
# The recipe
# ---------------------------------------------------------------------------


def arm_text(s: int, prefix: str) -> str:
    c1, c2 = choice_sets(prefix)[s]
    return f"Option 1:\n{c1.text}\n\nOption 2:\n{c2.text}\n\nOption 3:\n{OPT_OUT}"


def level_text(attr: str, v: float) -> str:
    if attr == "price":
        return f"£{v:.2f}"
    if attr == "fat":
        return f"{int(v)}%"
    return "yes" if v == 1 else "no"


def arms() -> list[dict[str, Any]]:
    out = []
    for prefix, (_, level, _, offset) in ARMS.items():
        for s in range(1, 25):
            factors = {"label_display": level, "choice_set": f"c{s:02d}"}
            factors["design_block"] = str(int(design().loc[s].Block))
            for k in (1, 2):
                for a, v in zip(ATTRS, alt(s, k), strict=True):
                    factors[f"option_{k}_{FACTOR_NAME[a]}"] = level_text(a, v)
            out.append(
                {
                    "raw_values": {"a_c1": s + offset},
                    "condition_num": s + offset - 1,
                    "factors": factors,
                    "text": arm_text(s, prefix),
                }
            )
    return out


NOTES = """\
{paper}

GENERATED by scripts/gen_researchbox3520.py; every judgement is in its docstring. A discrete
choice experiment fielded to UK adults who buy food (TGM Research panel, autumn 2023): eight
choices between two 500 g packs of British beef mince described by four labels (RSPCA
Assured, Fair to Nature, Low Climate Impact, Premium Quality Angus), fat content and price,
or neither. Ngene design: 24 choice sets in 3 blocks of 8, each person one block. Built: the
two arms that showed the labels as TEXT (rich, 23 Nov 2026), 1,000 people, 8,000 rows:
label_display = comprehensive (the authors' T-C, 497 people: every label stated, as
certified or "Not ...") and affirmative (T-L in the export, T-A in the paper, 503: only the
labels a product has). Not built: the logo arms V-C and V-L (pictures, image list) and the
lamb experiment (other respondents). Sample: the authors' analysis file Beef_CE_Survey.txt,
1,987 people after their exclusions, which the generator re-derives from the raw export
person by person.

Each choice set is its own arm (48 = 2 x 24) and each set's answer its own outcome (r_c<set>,
arm column a_c<set>): the cards' words come from that set's own screen in the survey PDF,
word-for-word, including the PDF's typo "'RSPCA Assued'" on 36 of the 96 cards. Each screen
is tied to its design set by the two cards' attribute levels (unique for all 48). Shared
context: the arm's intro page (identical for both text arms), word-for-word, less "{dropped}"
(survey mechanics). Not narrated: the screener and attention questions before it, the
questions after the choices. Each row shows only its own screen; whether a block's screens
were in a fixed or random order is not recorded.

OPTION ORDER. The PDF prints either product first, differently from screen to screen and
between the two arms; the export codes the design's alternative 1 as 1. With no .qsf, the
on-screen order cannot be established, so (rich's osf_ct8ae ruling, docs/CONVENTIONS.md) the options are
listed in the data file's order after our clause "{clause}", and the answer is coded to that
list: 1 and 2 the two products, 3 neither. Each option's attributes are factors
(option_<k>_<attribute>) so training can re-order and remap. Added words (ours): the clause,
"Option 1:", "Option 2:", "Option 3:", and after the question '1 means "Option 1"; 2 means
"Option 2"; 3 means "Option 3".'. The question is the screen's own.

Persona: age (years) and gender (Female, Male; the 4 people who chose "Prefer to
self-describe" left blank). Reference: the authors' MNL in WTP space (Code/wMNL_TC.R,
wMNL_TA.R) re-estimated on the built rows equals the same model on Beef_CE_Survey.txt; see
tests/test_gen_researchbox3520.py."""


def recipe() -> dict[str, Any]:
    tc, tl = intro("Beef_TC"), intro("Beef_TL")
    assert tc == tl
    question = f'{QUESTION} 1 means "Option 1"; 2 means "Option 2"; 3 means "Option 3".'
    return {
        "study_id": STUDY_ID,
        "source": "researchbox",
        "experiment": EXPERIMENT,
        "title": TITLE,
        "data_file": DATA_FILE,
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": "pid",
        "notes": NOTES.format(paper=PAPER, dropped=DROPPED, clause=CLAUSE),
        "condition": {
            "source_vars": ["a_c1"],
            "shared_context": f"{tc}\n\n{CLAUSE}",
            "factors": ["label_display", "choice_set"],
            "arms": arms(),
        },
        "outcomes": [
            {
                "var": f"r_c{s}",
                "task_num": s - 1,
                "question": question,
                "scale": {"min": 1, "max": 3, "nominal": True},
                "condition_var": f"a_c{s}",
            }
            for s in range(1, 25)
        ],
        "response_recode": {1: 1, 2: 2, 3: 3},
        "missing_codes": [],
        "persona_map": {"age": "age", "gender": "gender"},
    }


def render() -> str:
    return yaml.safe_dump(recipe(), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prep", action="store_true", help="check the sample and code the data")
    ap.add_argument("--check", action="store_true", help="exit 1 if the recipe differs")
    args = ap.parse_args()
    if args.prep:
        check_sample()
        path = RAW / DATA_FILE
        prep().to_csv(path, index=False)
        print(f"wrote {path.relative_to(REPO)}")
        return 0
    text = render()
    if args.check:
        same = RECIPE.exists() and RECIPE.read_text() == text
        print(("matches " if same else "DIFFERS ") + RECIPE.name)
        return 0 if same else 1
    RECIPE.write_text(text)
    print(f"wrote {RECIPE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
