#!/usr/bin/env python3
"""Write recipes/researchbox348_study1.yaml: should this person get overdraft coverage? (1 recipe).

Chin A, Zimmerman D, Johnson H, Shu SB (2022), "Decisions about overdraft coverage:
Disclosure design and personal finances", Journal of Experimental Psychology: Applied
28(4):746-774, doi:10.1037/xap0000460. ResearchBox 348 ("Decisions about Overdraft Coverage:
Disclosure", https://researchbox.org/348), read from its Zenodo copy. CC BY 4.0 ("All content
posted to ResearchBox is under a CC By 4.0 License", the box page). US samples (MTurk via
TurkPrime), Sept 2019 to 2021. The paper is paywalled and was not read; the answer key is the
authors' own R code (manuscript_cleaning.Rmd, manuscript_analysis.Rmd), transcribed and re-run
on the deposit and on the built rows.

Every judgement is here, in code, so the recipe can be re-derived and reviewed.

THE BOX. Three .qsf files (Studies 1, 2, 3) with their printouts, five data files (Studies 1,
2, 3 and the pilots of 1 and 3, .csv, one header row, choice text exported as labels), a
codebook per data file, the authors' R code (cleaning, analysis, and stimuli_generation.Rmd,
which wrote the Study 1 scenarios' HTML), the two design tables the scenarios come from
(Other/), and two AsPredicted pre-registrations (#28262, Studies 1-2; #66455, Study 3).

WHAT IS BUILT. Study 1 ("20190924 - Overdraft Disclosure Part A", wave 1 of AsPredicted
#28262), a rating-based conjoint about other people: everyone read ten descriptions of a
person opening a new checking account, varying six attributes two levels each (the fee per
overdraft, $25 or $35; the most fees in a day, 3 or 6; whether they have money left over at
the end of the month; whether they use the debit card for important purchases; whether they
have other ways to pay; a bank or a credit union), and said on a 0-100 slider whether this
person should get overdraft coverage. Nine profiles are the authors' Sawtooth fractional
design (Other/OD_characteristics_OD_Design_9.csv) and the tenth was added from the pilot's
design (stimuli_generation.Rmd); all ten are rated by everyone, so every row carries one
profile. Kind "story" (a vignette whose details vary).

NOT BUILT (NOT_BUILT), each with its reason:
- study2 and study3 (image list): the manipulation is the disclosure form itself, shown as a
  picture the person clicks on (Qualtrics HotSpot questions over graphics IM_...; the
  printouts show only the picture). The form carries the bank's name, the $34 fee and every
  word of the opt-in and opt-out choices. rich's picture rule (19 Nov 2026): skip. Study 2's
  one later scenario rating (a0_n1_s1_p0_l0_b1) follows the form, so it cannot be built
  without it either.
- study1_pilot and study3_pilot: the deposit holds no fielded questionnaire for either (the
  three .qsf files are Studies 1, 2 and 3), so their screens' wording cannot be read from the
  instrument; and both show a disclosure form as a picture too.

UK FIT (rich, 19 Nov 2026: judge whether a UK respondent can answer from the text shown).
Overdraft coverage as an opt-in with a fee per transaction is a US banking product
(Regulation E). The question asks for a judgement about a described person, and everything
it turns on is on the row: the survey's own definition of an overdraft (the screen that opens
the overdraft part of the survey, kept as shared context, see THE WORDING), the person's
circumstances and the program's fee and daily cap in dollars. "Checking account" and "credit
union" are US words with plain UK readings. Judged answerable, recorded as "Mostly" on the
ResearchBox list.

PICTURES (rich, 19 Nov 2026). Study 1's .qsf has no <img> and no graphic anywhere (asserted),
so no screen a Study 1 respondent could reach shows a picture. Studies 2 and 3 hold their
form graphics as HotSpot questions (3 and 5, asserted by GraphicID in PICTURES) and no <img>.

THE WORDING. From Study 1 (Conjoint).qsf, the blocks the survey flow reaches, word-for-word.
Each scenario is one slider question whose text has four parts, split by structure and
asserted identical where they should be: a lead ("Please read the description below
carefully. Then, please tell us whether you think this customer should get overdraft when
opening a new checking account.", the same in all ten), the "Personal background:" list (four
items), the "Overdraft program:" list (two items), and the question ("In your opinion, should
this person get overdraft coverage?", the same in all ten). The lists are the arm; each list
item becomes a line starting "- " (the screen's bullets) and the underlined headings keep
their words without the underline. The question is the outcome. Each row opens with the
lead, preceded by the definition screen every kept respondent read (QID18: "In this study, we
will ask you for your thoughts and opinions about overdraft on checking accounts. When we say
"overdraft," we mean: ..."), word-for-word. Not narrated: the analogy screener and consent;
the overdraft quiz (QID19), its retry page (QID68/QID69/QID67, shown only to those who got it
wrong) and the three knowledge questions that follow it (sub_od_knowl, obj_od_fee,
obj_od_chance), all asked before the scenarios and identical for every row; and the block's
fixed first screen (QID52, "In the next part of the study, we will show you information about
different people ... Please read the descriptions carefully, as some may be similar."), which
describes the sequence (CONVENTIONS, sequence signposting). Typography normalised.

FACTORS, READ FROM THE TEXT. Each scenario's export tag codes its profile (a fee amount, n
number of fees, s slack, p purchase purpose, l alternative payment, b bank), and the generator
parses every one of the six levels back out of the scenario's own words and asserts they
agree: a1 "$35" / a0 "$25"; n1 "6 each day" / n0 "3 each day"; s1 "able to save some money" /
s0 "don't have much money left over"; p1 "are responsible for making important purchases" /
p0 "are not responsible"; l1 "have other ways to pay" / l0 "don't have other ways to pay"; b1
"enters a bank" / b0 "enters a credit union"; and the daily cap is the product of fee and
number. The fielded number of fees is 3 or 6, as stimuli_generation.Rmd (num_v = c(3, 6)) and
the analysis's labels ("Max 6 Daily (vs 3)") have it; the Study 1 codebook's "n=number of fees
(1=4, 0=1)" is wrong (recorded, the .qsf wins).

THE OUTCOME. A horizontal slider, 0 to 100, whole numbers (CSSliderMin/Max, NumDecimals 0),
forced, with four labels over it ("Definitely no", "Probably no", "Probably yes", "Definitely
yes"; CenterLabels, so each sits over a quarter of the track, not at a point). So the scale
names no end labels, and one sentence of OURS after the question names all four:
    'The answer was a slider from 0 to 100; its labels, from 0 towards 100, were "Definitely
     no", "Probably no", "Probably yes" and "Definitely yes".'
(CONVENTIONS, layout exception: a clause of description, with the labels quoted.) The slider
started at 50 (not narrated).

ORDER. The ten scenarios each sit on their own page in a random order that is NOT recorded
(no _DO column in the deposit; the .qsf's advanced randomisation shuffles seven of them,
QID1-QID9, and three added later, QID63-QID65, sit outside its lists, asserted). So each row
carries its own scenario only and no position (CONVENTIONS: an unrecorded order is never
narrated), as researchbox3251 study3. Each scenario is its own outcome naming its own
profile's codes (Outcome.condition_vars, columns <dimension>_<k> for scenario k in block
order, constant: everyone saw all ten), as the DEL conjoints.

THE TEMPLATE. Ten profiles of a 2^6 design (a fraction: no two differ in one attribute only)
leave QC rule 5 no minimal pair to test, so the condition is declared as a sparse template
(ConditionTemplate, cells_drawn = the ten profiles) whose levels are the words each attribute
puts on screen, and QC renders the pairs instead. The day's maximum ("or $105") is fee x
number, which no single attribute's level can supply, so it is a seventh dimension,
daily_cap ($75, $105, $150, $210), derived and not randomised on its own; the generator
asserts that the template filled from each profile's codes reproduces that scenario's lists
exactly. The definition screen and the lead are the template's fixed opening, so the rows
keep their paragraph breaks.

EXCLUSIONS. The authors' cleaning code, applied as written: passed the three analogies (a
non-blank old_enough), 18 or older and consented, the overdraft definition right at the first
or second try, finished (a non-blank edu_lvl), and more than 180 seconds (timing_s1), the
pre-registered rules. 1,016 rows to 869 people, every one with all ten ratings (asserted).
These are the authors' wave-1 N.

PERSONA. Gender (the .qsf's own labels: Male, Female, Other/Prefer not to say; the last kept
as the source merges it) and year of birth (as answered, a drop-down of years; the deposit
exports the year). Age is not derived: the survey date and the year alone fix it only to
within a year, so year_of_birth goes in as itself, as gyrp9 does. Not used: education (US
categories with no crosswalk scheme for this source; adding one is shared catalogue work), and
the overdraft history, debit-card use and money questions asked after the scenarios (the same
domain as the outcome, and answered after it).

JEV. scripts/recipe_prep.py reads .sav/.dta/.por only; this box is .csv, and running it (19
Nov 2026, --source dataverse) exits "no .sav/.dta under data/raw/researchbox348/", so it does
not apply. There is no assignment column to find (everyone saw all ten profiles; the profile is
the export tag), and the persona labels are the .qsf's own choices.

ANSWER KEY. The paper's Table 3 (OLS of the rating on the six attributes with person fixed
effects, manuscript_analysis.Rmd) is paywalled and was not read, so the key is the authors'
model fitted twice: from the deposit through their own reshape (the export tag's digits
decoded as they decode them) and from the BUILT rows' factors. The six coefficients agree to
1e-9 (tests/test_gen_researchbox348.py), as do each profile's mean rating and the N (869
people, 8,690 ratings). On this deposit the authors' code gives fee $35 (vs $25) -2.265,
num_fees_high 1.603, no slack 3.950, critical purpose 7.375, other ways to pay -11.113,
credit union -0.588. Recorded, not resolved: the authors' indicator num_fees_high is 1 when
n = 0, which the fielded words make 3 fees a day, and their table labels it "Max 6 Daily (vs
3)"; amount_fee is 1 for $35 and is labelled "25 Fee (vs 35)". Whether the published Table 3
carries those labels cannot be determined from the deposit. The rows follow the fielded
words, which are the authority.

    uv run python scripts/gen_researchbox348.py --prep   # code the data
    uv run python scripts/gen_researchbox348.py          # write the recipe
    uv run python scripts/gen_researchbox348.py --check  # exit 1 if the recipe differs
"""

from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
STUDY_ID = "researchbox348"
RAW = REPO / "data" / "raw" / STUDY_ID
MATERIALS = RAW / "Materials"
DATA = RAW / "Data"
CODEBOOK = RAW / "Codebook"
RECIPES = REPO / "recipes"
LICENCE = (
    'CC BY 4.0, stated on the box page https://researchbox.org/348 ("All content posted '
    'to ResearchBox is under a CC By 4.0 License"); read from its Zenodo copy. Read 19 Nov 2026.'
)
PAPER = (
    'Chin A, Zimmerman D, Johnson H, Shu SB (2022), "Decisions about overdraft coverage: '
    'Disclosure design and personal finances", Journal of Experimental Psychology: Applied '
    "28(4):746-774, doi:10.1037/xap0000460. ResearchBox 348 (https://researchbox.org/348)."
)

QSF = "Study 1 (Conjoint).qsf"
DATA_FILE = "study_1.csv"

# Graphics in each .qsf: <img> tags and HotSpot GraphicIDs. Studies 2 and 3 are not built.
PICTURES = {
    "Study 1 (Conjoint).qsf": (0, set()),
    "Study 2 Form Comparison.qsf": (
        0,
        {"IM_0P4IBeM9uUOdhbv", "IM_a9kxae0Fzvn69RH", "IM_9zbWZbNjVCRWSqx"},
    ),
    "Study 3 (Additional Forms).qsf": (
        0,
        {
            "IM_0P4IBeM9uUOdhbv",
            "IM_a9kxae0Fzvn69RH",
            "IM_9zbWZbNjVCRWSqx",
            "IM_8rd4FBfmAVayz8q",
            "IM_bjsFffHik1KDaOW",
        },
    ),
}

NOT_BUILT = {
    "study2": "Study 2 (form comparison): the manipulation is the overdraft disclosure form, "
    "shown as a picture the person clicks to choose (HotSpot questions over IM_0P4IBeM9uUOdhbv, "
    "IM_a9kxae0Fzvn69RH, IM_9zbWZbNjVCRWSqx); it carries Ficus Bank's name, the $34 fee and the "
    "opt-in and opt-out wording. rich's picture rule; image list. Its later scenario rating "
    "follows the form.",
    "study3": "Study 3 (additional forms): four disclosure forms, each a picture the person "
    "clicks (five HotSpot graphics), carrying the fee and the choice wording; every outcome "
    "follows the form. rich's picture rule; image list.",
    "study1_pilot": "Study 1 pilot: no fielded questionnaire in the deposit (the three .qsf "
    "files are Studies 1-3), so its screens' wording cannot be read from the instrument; it "
    "also shows a disclosure form as a picture.",
    "study3_pilot": "Study 3 pilot: no fielded questionnaire in the deposit, and its "
    "manipulation is a disclosure form shown as a picture.",
}

# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

_TYPO = {"\xa0": " ", "​": "", "’": "'", "‘": "'", "“": '"', "”": '"'}


def plain(raw: str) -> str:
    """An HTML fragment to one line of plain text. Typography only."""
    s = re.sub(r"<[^>]+>", " ", raw or "")
    s = html.unescape(s)
    for a, b in _TYPO.items():
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def paragraphs(raw: str) -> str:
    """HTML to paragraphs (blank-line separated), each one line of plain text."""
    s = re.sub(r"(?i)<br\s*/?>|</p>|</div>|<p[^>]*>|<div[^>]*>", "\n\n", raw or "")
    parts = [plain(p) for p in s.split("\n\n")]
    return "\n\n".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# The questionnaire
# ---------------------------------------------------------------------------


class Survey:
    """A .qsf, read through its flow: only questions a respondent could meet."""

    def __init__(self, filename: str) -> None:
        self.raw = (MATERIALS / filename).read_text()
        d = json.loads(self.raw)
        els = d["SurveyElements"]
        self.by_id = {e["Payload"]["QuestionID"]: e["Payload"] for e in els if e["Element"] == "SQ"}
        blocks: dict[str, dict[str, Any]] = {}
        for e in els:
            if e["Element"] == "BL":
                p = e["Payload"]
                for b in p.values() if isinstance(p, dict) else p:
                    blocks[b["ID"]] = b
        self.blocks = blocks
        flow = next(e for e in els if e["Element"] == "FL")["Payload"]
        self.flow_blocks: list[dict[str, Any]] = []

        def walk(n: dict[str, Any]) -> None:
            if n.get("Type") in ("Block", "Standard", "Default"):
                self.flow_blocks.append(blocks[n["ID"]])
            for c in n.get("Flow", []):
                walk(c)

        walk(flow)
        self.in_flow = [
            self.by_id[x["QuestionID"]]
            for b in self.flow_blocks
            for x in b.get("BlockElements", [])
            if x["Type"] == "Question"
        ]

    def block(self, description: str) -> dict[str, Any]:
        (b,) = [b for b in self.flow_blocks if b["Description"] == description]
        return b

    def q(self, tag: str) -> dict[str, Any]:
        """The ONE in-flow question with this export tag."""
        (p,) = [p for p in self.in_flow if p["DataExportTag"] == tag]
        return p


def graphics_in(raw: str) -> tuple[int, set[str]]:
    """(<img> tags, HotSpot graphic ids) in a .qsf's text."""
    return raw.count("<img"), set(re.findall(r'"GraphicID":"(IM_\w+)"', raw))


def graphics(filename: str) -> tuple[int, set[str]]:
    return graphics_in((MATERIALS / filename).read_text())


def check_pictures() -> None:
    """No picture anywhere in Study 1's .qsf; the form graphics are where expected."""
    assert sorted(p.name for p in MATERIALS.glob("*.qsf")) == sorted(PICTURES)
    for f, want in PICTURES.items():
        assert graphics(f) == want, f
    assert "Graphic" not in (MATERIALS / QSF).read_text()


# ---------------------------------------------------------------------------
# Study 1's scenarios
# ---------------------------------------------------------------------------

SCENARIO_BLOCK = "Overdraft Scenarios"
DEFINITION_QID = "QID18"
SEQUENCE_QID = "QID52"  # "In the next part of the study, ..." (dropped)
LEAD = (
    "Please read the description below carefully. Then, please tell us whether you think "
    "this customer should get overdraft when opening a new checking account."
)
QUESTION = "In your opinion, should this person get overdraft coverage?"
SLIDER_LABELS = ["Definitely no", "Probably no", "Probably yes", "Definitely yes"]
SLIDER_SENTENCE = (  # ours
    "The answer was a slider from 0 to 100; its labels, from 0 towards 100, were "
    '"Definitely no", "Probably no", "Probably yes" and "Definitely yes".'
)
TAG = re.compile(r"^a([01])_n([01])_s([01])_p([01])_l([01])_b([01])$")

FACTORS = ["fee_amount", "number_of_fees", "slack", "purchase_purpose", "alt_payment", "bank_type"]
LEVELS = {
    "fee_amount": ("$25", "$35"),
    "number_of_fees": ("3_per_day", "6_per_day"),
    "slack": ("month_to_month", "savings"),
    "purchase_purpose": ("discretionary", "critical"),
    "alt_payment": ("no", "yes"),
    "bank_type": ("credit_union", "bank"),
}
# The words each level puts on screen (asserted against all ten scenarios by rendering).
CLAUSES: dict[str, tuple[str, str]] = {
    "fee_amount": ("25", "35"),
    "number_of_fees": ("3", "6"),
    "slack": (
        "They make an average income and live in a high cost area, so they don't have much "
        "money left over at the end of the month.",
        "They make an average income and live in a low cost area, so they are able to save "
        "some money at the end of the month.",
    ),
    "purchase_purpose": (
        "They are not responsible for making important purchases (like car repairs and "
        "groceries) and leave that to others in the household. They use a debit card only for "
        "everyday purchases.",
        "They are responsible for making important purchases (like car repairs and groceries) "
        "and use the debit card for those purchases.",
    ),
    "alt_payment": (
        "They don't have other ways to pay if their debit card is declined.",
        "They have other ways to pay if their debit card is declined.",
    ),
    "bank_type": ("credit union", "bank"),
}
# The daily cap on screen is fee x number, so it is a seventh dimension of the TEMPLATE
# (derived, not randomised on its own): no single attribute's level can supply it.
CAP = "daily_cap"
CAPS = (75, 105, 150, 210)
DIMENSIONS = [*FACTORS, CAP]
TEMPLATE = (
    "Personal background:\n"
    "- This person enters a {bank_type}.\n"
    "- {slack}\n"
    "- {purchase_purpose}\n"
    "- {alt_payment}\n"
    "\n"
    "Overdraft program:\n"
    "- The {bank_type.word}'s overdraft fee is ${fee_amount} per transaction.\n"
    "- The maximum number of overdraft fees is {number_of_fees} each day, or ${daily_cap}."
)


def fill(cell: dict[str, int]) -> str:
    """The template filled from one cell: what that profile's lists say."""
    out = TEMPLATE.replace("{bank_type.word}", CLAUSES["bank_type"][cell["bank_type"]])
    for f in FACTORS:
        out = out.replace("{" + f + "}", CLAUSES[f][cell[f]])
    return out.replace("{" + CAP + "}", str(cell[CAP]))


@dataclass
class Scenario:
    tag: str  # the export tag: the profile's code
    qid: str
    code: int  # 1-10, block order
    bits: tuple[int, ...]  # a, n, s, p, l, b as the tag has them
    text: str  # the two lists, as the arm text

    @property
    def factors(self) -> dict[str, str]:
        return {f: LEVELS[f][b] for f, b in zip(FACTORS, self.bits, strict=True)}

    @property
    def cell(self) -> dict[str, int]:
        """Codes per template dimension: 0/1 per attribute, the cap in dollars."""
        c = dict(zip(FACTORS, self.bits, strict=True))
        c[CAP] = int(CLAUSES["fee_amount"][c["fee_amount"]]) * int(
            CLAUSES["number_of_fees"][c["number_of_fees"]]
        )
        assert c[CAP] in CAPS
        return c


def split_scenario(raw: str) -> tuple[str, list[str], list[str], str]:
    """(lead, background items, program items, question) from one scenario's HTML."""
    m = re.fullmatch(
        r"(?s)\s*(?:<div>)?(.*?)<u>Personal background:</u>(.*?)<ul>(.*?)</ul>(.*?)"
        r"<u>Overdraft program:</u>(.*?)<ul>(.*?)</ul>(.*?)(?:</div>)?\s*",
        raw,
    )
    assert m, raw[:200]
    lead, gap1, ul1, gap2, gap3, ul2, tail = m.groups()
    assert plain(gap1) == plain(gap3) == "" and plain(gap2) == "", (gap1, gap2, gap3)

    def items(ul: str) -> list[str]:
        assert plain(re.sub(r"(?s)<li>.*?</li>", "", ul)) == "", ul
        return [plain(x) for x in re.findall(r"(?s)<li>(.*?)</li>", ul)]

    return paragraphs(lead), items(ul1), items(ul2), paragraphs(tail)


def parse_bits(bg: list[str], prog: list[str]) -> tuple[int, ...]:
    """The six levels read back out of the scenario's own words."""
    assert len(bg) == 4 and len(prog) == 2, (bg, prog)
    place = {"This person enters a bank.": 1, "This person enters a credit union.": 0}[bg[0]]
    slack = {
        "They make an average income and live in a low cost area, so they are able to save "
        "some money at the end of the month.": 1,
        "They make an average income and live in a high cost area, so they don't have much "
        "money left over at the end of the month.": 0,
    }[bg[1]]
    purpose = {
        "They are responsible for making important purchases (like car repairs and groceries) "
        "and use the debit card for those purchases.": 1,
        "They are not responsible for making important purchases (like car repairs and "
        "groceries) and leave that to others in the household. They use a debit card only for "
        "everyday purchases.": 0,
    }[bg[2]]
    alt = {
        "They have other ways to pay if their debit card is declined.": 1,
        "They don't have other ways to pay if their debit card is declined.": 0,
    }[bg[3]]
    word = "bank" if place else "credit union"
    fm = re.fullmatch(rf"The {word}'s overdraft fee is \$(25|35) per transaction\.", prog[0])
    nm = re.fullmatch(
        r"The maximum number of overdraft fees is (3|6) each day, or \$(\d+)\.", prog[1]
    )
    assert fm and nm, prog
    fee, num, cap = int(fm.group(1)), int(nm.group(1)), int(nm.group(2))
    assert cap == fee * num, prog  # the daily cap is fee x number
    return (int(fee == 35), int(num == 6), slack, purpose, alt, place)


def arm_text(bg: list[str], prog: list[str]) -> str:
    return (
        "Personal background:\n"
        + "\n".join(f"- {x}" for x in bg)
        + "\n\nOverdraft program:\n"
        + "\n".join(f"- {x}" for x in prog)
    )


def scenario_qids(sv: Survey) -> list[str]:
    b = sv.block(SCENARIO_BLOCK)
    qids = [x["QuestionID"] for x in b["BlockElements"] if x["Type"] == "Question"]
    assert qids[0] == SEQUENCE_QID
    return qids[1:]


def check_order(sv: Survey) -> None:
    """Random order, unrecorded: seven shuffled by the block, three outside its lists."""
    b = sv.block(SCENARIO_BLOCK)
    adv = b["Options"]["Randomization"]["Advanced"]
    assert b["Options"]["RandomizeQuestions"] == "Advanced"
    assert adv["FixedOrder"][0] == SEQUENCE_QID
    assert adv["FixedOrder"][1:] == ["{~Randomized~}"] * 7
    qids = scenario_qids(sv)
    assert sorted(adv["RandomizeAll"]) == sorted(qids[:7])
    assert set(qids[7:]) == {"QID63", "QID64", "QID65"}
    assert not adv["Undisplayed"] and not adv["RandomSubSet"]
    assert not any(c.endswith("_DO") for c in read_deposit().columns)


def scenarios() -> tuple[str, list[Scenario]]:
    """(the lead, the ten scenarios in block order), every part asserted."""
    sv = Survey(QSF)
    out, leads, questions = [], set(), set()
    for code, qid in enumerate(scenario_qids(sv), 1):
        q = sv.by_id[qid]
        assert (q["QuestionType"], q["Selector"]) == ("Slider", "HSLIDER"), qid
        c = q["Configuration"]
        assert (c["CSSliderMin"], c["CSSliderMax"], c["NumDecimals"]) == (0, 100, "0"), qid
        assert c["CenterLabels"] and not c["SnapToGrid"] and not c.get("NotApplicable"), qid
        assert q["Validation"]["Settings"]["ForceResponse"] == "ON", qid
        assert list(q["Choices"]) == ["1"] and plain(q["Choices"]["1"]["Display"]) == ""
        labels = [plain(q["Labels"][k]["Display"]) for k in sorted(q["Labels"], key=int)]
        assert labels == SLIDER_LABELS, labels
        assert not q.get("DisplayLogic"), qid
        lead, bg, prog, question = split_scenario(q["QuestionText"])
        leads.add(lead)
        questions.add(question)
        m = TAG.match(q["DataExportTag"])
        assert m, q["DataExportTag"]
        bits = tuple(int(g) for g in m.groups())
        assert parse_bits(bg, prog) == bits, (q["DataExportTag"], bg, prog)
        s = Scenario(q["DataExportTag"], qid, code, bits, arm_text(bg, prog))
        assert fill(s.cell) == s.text, (s.tag, fill(s.cell), s.text)  # the template is exact
        out.append(s)
    assert leads == {LEAD}, leads
    assert questions == {QUESTION}, questions
    assert len({s.bits for s in out}) == 10
    return LEAD, out


def definition() -> str:
    sv = Survey(QSF)
    q = sv.by_id[DEFINITION_QID]
    assert q["QuestionType"] == "DB" and not q.get("DisplayLogic")
    assert sv.block("Pre scenario questions")["BlockElements"][0]["QuestionID"] == DEFINITION_QID
    return paragraphs(q["QuestionText"])


# ---------------------------------------------------------------------------
# The experiment
# ---------------------------------------------------------------------------


@dataclass
class Experiment:
    name: str
    title: str
    kind: str
    shared: str
    scenarios: list[Scenario]
    notes: str


def experiment() -> Experiment:
    lead, scen = scenarios()
    shared = f"{definition()}\n\n{lead}"
    return Experiment(
        name="study1",
        title="A person opening a checking account: the overdraft fee ($25 or $35), the most "
        "fees a day (3 or 6), money left over or not, the debit card for important purchases or "
        "not, other ways to pay or not, a bank or a credit union; should they get overdraft "
        "coverage? (Study 1)",
        kind="story",
        shared=shared,
        scenarios=scen,
        notes="Study 1 (AsPredicted #28262, wave 1), 869 people kept by the authors' "
        "pre-registered exclusions (analogies, age and consent, the overdraft definition right "
        "at the first or second try, finished, more than 180 seconds). Within person: everyone "
        "rated all ten profiles, each on its own page, in a random order the deposit does not "
        "record, so each row carries its own profile only, and each outcome names its own "
        "profile's codes (condition_vars <dimension>_<1-10>, constant columns). Six two-level "
        "attributes, read back from each profile's words and asserted against its export "
        "tag; the profiles are a fractional design (10 of 64), declared as a sparse template "
        "whose seventh dimension, daily_cap, is the day's maximum shown on screen (fee x "
        "number, not randomised on its own). Every row opens with the "
        "definition screen that opens the overdraft part of the survey (QID18), then the "
        "scenario page's lead, both word-for-word; between them the survey asked a quiz on "
        "that definition and three knowledge questions, not narrated, and the scenario "
        "block's first screen, which describes the sequence, is dropped. List items are "
        "written as lines starting '- '. Added words (ours), after the question: "
        f"'{SLIDER_SENTENCE}' (the slider's four labels sit over quarters of the track, so "
        "no end label is claimed for 0 or 100). The slider started at 50 (not narrated). "
        "The Study 1 codebook's 'number of fees (1=4, 0=1)' is wrong: the fielded .qsf, "
        "stimuli_generation.Rmd and the analysis all have 3 or 6.",
    )


# ---------------------------------------------------------------------------
# Coded data
# ---------------------------------------------------------------------------

N = 869
CORRECT_DEFINITION = "Overdraft is when your bank covers your transaction until you can pay it back"


MERGED_GENDER = "Other/Prefer not to say"  # an answer and a refusal in one: left blank


def dim_var(dim: str, code: int) -> str:
    """The coded column holding `dim`'s code for the scenario numbered `code` (1-10)."""
    return f"{dim}_{code}"


def data_file() -> str:
    return f"{STUDY_ID}_study1.csv"


def read_deposit() -> pd.DataFrame:
    return pd.read_csv(DATA / DATA_FILE, na_values=["NA"], keep_default_na=False)


def kept() -> pd.DataFrame:
    """The authors' wave-1 sample (manuscript_cleaning.Rmd, in order)."""
    df = read_deposit()
    assert df["ResponseId"].is_unique
    df = df[df["old_enough"].notna()]  # passed the analogies
    df = df[(df["old_enough"] == "Yes") & (df["agree_participate"] == "Yes")]
    df = df[(df["ob_od_cover"] == CORRECT_DEFINITION) | (df["ob_od_cover_2"] == CORRECT_DEFINITION)]
    df = df[df["edu_lvl"].notna()]  # finished
    df = df[df["timing_s1"] > 180]
    return df.reset_index(drop=True)


def gender_labels() -> list[str]:
    q = Survey(QSF).q("gender")
    assert q["QuestionType"] == "MC" and not q.get("RecodeValues")
    return [plain(q["Choices"][k]["Display"]) for k in sorted(q["Choices"], key=int)]


def birth_years() -> set[int]:
    q = Survey(QSF).q("birth_year")
    return {int(plain(v["Display"])) for v in q["Choices"].values()}


def prep() -> pd.DataFrame:
    """One coded row per kept person: ten constant arm columns, ten ratings, persona."""
    df = kept()
    e = experiment()
    out = pd.DataFrame({"pid": [f"study1_{r}" for r in df["ResponseId"]]})
    for s in e.scenarios:  # constant per scenario: everyone saw all ten
        for d in DIMENSIONS:
            out[dim_var(d, s.code)] = s.cell[d]
    for s in e.scenarios:
        v = pd.to_numeric(df[f"{s.tag}_1"], errors="raise")
        assert v.notna().all() and (v % 1 == 0).all() and v.between(0, 100).all(), s.tag
        out[f"r_{s.tag}"] = v.astype(int).values
    yob = pd.to_numeric(df["birth_year"], errors="raise")
    assert set(yob.astype(int)) <= birth_years()
    out["year_of_birth"] = yob.astype(int).values
    labels = gender_labels()
    assert labels == ["Male", "Female", MERGED_GENDER] and set(df["gender"]) <= set(labels)
    out["gender"] = df["gender"].where(df["gender"] != MERGED_GENDER).values
    assert len(out) == N and out["pid"].is_unique, len(out)
    return out


def check_codebook() -> None:
    """The codebook's columns are the data file's; the scenario columns are the .qsf's tags."""
    book = pd.read_csv(CODEBOOK / f"{DATA_FILE}___CODEBOOK.csv")
    df = read_deposit()
    assert list(book["varname"]) == list(df.columns)
    tags = {s.tag for s in experiment().scenarios}
    assert {c[:-2] for c in df.columns if TAG.match(c[:-2])} == tags
    desc = book.set_index("varname").loc["a1_n0_s0_p0_l1_b1_1", "description"]
    assert "a=fee amount (1=35, 0=25)" in desc and "n=number of fees (1=4, 0=1)" in desc


# ---------------------------------------------------------------------------
# The recipe
# ---------------------------------------------------------------------------


def recipe(e: Experiment) -> dict[str, Any]:
    dims: dict[str, Any] = {}
    for d in DIMENSIONS:
        if d == CAP:
            levels = {c: {"level": f"${c}", "text": str(c)} for c in CAPS}
        else:
            levels = {
                b: {"level": LEVELS[d][b], "text": CLAUSES[d][b]}
                | ({"parts": {"word": CLAUSES[d][b]}} if d == "bank_type" else {})
                for b in (0, 1)
            }
        dims[d] = {"var": dim_var(d, 1), "levels": levels}
    template = {
        "sparse": True,
        "cells_drawn": [[s.cell[d] for d in DIMENSIONS] for s in e.scenarios],
        "text": f"{e.shared}\n\n{TEMPLATE}",
        "dimensions": dims,
    }
    outcomes = [
        {
            "var": f"r_{s.tag}",
            "task_num": t,
            "question": f"{QUESTION} {SLIDER_SENTENCE}",
            "scale": {"min": 0, "max": 100},
            "condition_vars": [dim_var(d, s.code) for d in DIMENSIONS],
        }
        for t, s in enumerate(e.scenarios)
    ]
    notes = (
        f"{PAPER}\n\nGENERATED by scripts/gen_researchbox348.py; every judgement is in its "
        f"docstring. {e.notes}\n\nWording from {QSF} (the blocks the survey flow reaches), "
        "word-for-word; no picture anywhere in it. Typography normalised (HTML, non-breaking "
        f"spaces, curly quotes); underline dropped. Data: {DATA_FILE}. Persona: gender (the "
        ".qsf's labels; 'Other/Prefer not to say' kept as the source merges it) and year of "
        "birth as answered (age not derived). US sample; the overdraft product is the US "
        "opt-in kind, defined on screen."
    )
    return {
        "study_id": STUDY_ID,
        "source": "researchbox",
        "experiment": e.name,
        "title": e.title,
        "data_file": data_file(),
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": "pid",
        "notes": notes,
        "condition": {
            "source_vars": [dim_var(d, 1) for d in DIMENSIONS],
            "factors": DIMENSIONS,
            "template": template,
        },
        "outcomes": outcomes,
        "response_recode": {k: k for k in range(0, 101)},
        "missing_codes": [],
        "persona_map": {"gender": "gender", "year_of_birth": "year_of_birth"},
    }


def recipe_path(e: Experiment) -> Path:
    return RECIPES / f"{STUDY_ID}_{e.name}.yaml"


def render(e: Experiment) -> str:
    return yaml.safe_dump(recipe(e), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prep", action="store_true", help="code the data")
    ap.add_argument("--check", action="store_true", help="exit 1 if the recipe differs")
    args = ap.parse_args()
    if args.prep:
        check_pictures()
        check_codebook()
        check_order(Survey(QSF))
        path = RAW / data_file()
        prep().to_csv(path, index=False)
        print(f"wrote {path.relative_to(REPO)}")
        return 0
    e = experiment()
    path, text = recipe_path(e), render(e)
    if args.check:
        same = path.exists() and path.read_text() == text
        print(("matches " if same else "DIFFERS ") + path.name)
        return 0 if same else 1
    path.write_text(text)
    print(f"wrote {path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
