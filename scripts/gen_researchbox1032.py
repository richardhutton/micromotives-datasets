#!/usr/bin/env python3
"""Write recipes/researchbox1032_*.yaml: shrinkflation aversion (7 recipes).

Evangelidis I (2024), "Frontiers: Shrinkflation Aversion: When and Why Product Size
Decreases Are Seen as More Unfair than Equivalent Price Increases", Marketing Science
43(2):280-288, doi:10.1287/mksc.2023.0269 (the box page). ResearchBox 1032 ("Shrinkflation
Aversion", https://researchbox.org/1032). CC BY 4.0 ("All content posted to ResearchBox is
under a CC By 4.0 License", the box page). Prolific samples, 2022-2023 (the pre-registrations
and the consent screen); US dollars, ounces and sheets, kept as the source has them.

Every judgement is here, in code, so the recipes can be re-derived and reviewed.

THE DESIGN. A manufacturer faces higher costs and either raises the price or shrinks the
product, the two changes giving the same price per unit. People say whether the change is
fair (Study 1: "acceptable") or unfair. One .qsf, one data file, one R script and one
AsPredicted pre-registration per study; no picture anywhere (asserted: no <img>, no IM_
graphic id in any .qsf).

WHAT IS BUILT. All seven studies:
- study1: chocolate ($4 to $5, or 10 oz to 8 oz) AND orange juice ($5 to $6, or 50 to 42 fl
  oz). Everyone judged both products; price or size was drawn separately for each product
  (two nested BlockRandomizers, SubSet 1), and the two products came in a random order
  (the outer BlockRandomizer, SubSet 2 of 2) that the deposit does not record. One recipe,
  four conditions (product x action), two outcomes per person, each outcome naming its own
  assignment column (Outcome.condition_var). Product is not randomised, action is.
- study2: potato chips ($3 to $4, or 12 oz to 9 oz), between people.
- study3: facial tissues ($6 to $7.5, or 160 to 128 sheets), between people; the fairness
  question and a three-statement agreement matrix (deceptive, forces buying more, too big),
  1-7.
- study4: detergent, 2 (price or net weight) x 2 (no further information, or the packaging
  states the change), between people.
- study5: potato chips, 2 (costs have increased, or have not) x 2 (price or size).
- s1: potato chips, price AND size judged by everyone (joint evaluation, the line-up). One
  condition per question, each person two rows.
- s2: potato chips, 2 (costs increased, or the quantity of raw materials supplied has
  decreased) x 2 (price or size).

THE ASSIGNMENT. No data file has an id or an assignment column: each arm's question is its
own column, blank for people who were not shown it. Every fairness question is
ForceResponse ON in the .qsf (asserted), so among the people in the file a blank means "not
shown", never "skipped"; `prep` derives the arm from which column is filled and asserts that
exactly one is, for each product in Study 1 and for the single scenario elsewhere. The R
scripts derive their dummies the same way (ifelse(x > 0, 1, 0), NA to 0). The coded file
gives each person an id from their row in the deposit ("study1_17"), the only key it has.
Jev (scripts/recipe_prep.py, 19 Nov 2026, run as `--source dataverse`, its nearest open-
archive class, since its choices list no researchbox) answered NONE_OF_THESE for the
assignment column on all six .sav files (confidence 0.59-0.88), which agrees: there is no
such column.

THE QUESTIONS. Each fairness screen is one sentence-completion question: the scenario, then
"This is" with the two answers beneath. The scenario is the condition (word-for-word, the
question text up to "This is", asserted to end there); the outcome is "This is", its scale
the .qsf's two choices (1 = fair or acceptable, 2 = unfair; codes asserted against the
RecodeValues where the .qsf has them, Studies 5 and S2 recoding choice 4 to 2). Study 3's
matrix repeats the scenario word-for-word (asserted) and then asks "To what extent do you
agree with the following statements:"; each statement is one outcome, the stem plus the
statement, 1 = Strongly disagree to 7 = Strongly agree (.qsf AnswerOrder; middle labels
blank). Its export columns _1, _2, _3 are the .qsf's choices 1, 2, 4 in ChoiceOrder, as the
codebook's labels confirm (asserted).

ORDER, AND WHY NO ROW NARRATES ANOTHER. CONVENTIONS ("Repeated measures within one block")
allows a later row to narrate an earlier screen only where the order is fixed or recorded;
"an order randomised and not recorded cannot be narrated at all". Here every within-person
order was randomised and none was recorded:
- Study 1, the two products (outer BlockRandomizer; no _DO column in the deposit);
- Study S1, the two questions (block option RandomizeQuestions RandomWithXPerPage, and the
  pre-registration: "The order of the two scenarios will be randomized");
- Study 3, the fairness question and the matrix (the same block option).
So each row carries its own scenario only, and the notes say what else the person was asked.
Every Study 3 question repeats the full scenario, so the condition is true whichever came
first.

DROPPED. Consent, the intro screen ("Thank you for your willingness to participate ...") and
the Prolific id (survey mechanics). Study 2's open-ended "Why do you think that this is
unfair?" (free text, asked only of those who said unfair) and its four coded columns
(Dishonest, BuyMore, TooMuch, Shrinkflation_dishonest): the authors' codes of that text, not
answers anyone gave.

EXCLUSIONS. None pre-registered ("We will not exclude any data", every study). Every row of
every file is kept, except one row of Study 3's file that is blank in every column (no
assignment, no answer, no age, no gender): 1,000 of 1,001. The R script keeps that row and,
through its NA-to-0 recode, counts it as a price-increase respondent who said fair; the test
asserts the difference this makes rather than hiding it.

PERSONA. Age (typed, the .qsf validates 18-100; outside that range would be left blank, none
is) and gender, labels from the .qsf's own choices (Female, Male, Non-Binary, Other). Jev
mapped both at confidence 1.00 on every .sav file and found no non-answer label (6 to 50
labels per file, no disagreement with the regex).

    uv run python scripts/gen_researchbox1032.py --prep   # code the data
    uv run python scripts/gen_researchbox1032.py          # write the recipes
    uv run python scripts/gen_researchbox1032.py --check  # exit 1 if any recipe differs
"""

from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
import pyreadstat
import yaml

REPO = Path(__file__).resolve().parents[1]
STUDY_ID = "researchbox1032"
RAW = REPO / "data" / "raw" / STUDY_ID
MATERIALS = RAW / "Materials"
DATA = RAW / "Data"
CODEBOOK = RAW / "Codebook"
RECIPES = REPO / "recipes"
LICENCE = (
    'CC BY 4.0, stated on the box page https://researchbox.org/1032 ("All content posted '
    'to ResearchBox is under a CC By 4.0 License"). Read 19 Nov 2026.'
)
PAPER = (
    'Evangelidis I (2024), "Frontiers: Shrinkflation Aversion: When and Why Product Size '
    'Decreases Are Seen as More Unfair than Equivalent Price Increases", Marketing Science '
    "43(2):280-288, doi:10.1287/mksc.2023.0269. ResearchBox 1032 (https://researchbox.org/1032)."
)

# tag -> the deposit's study label ("Study 1 - Materials.qsf", "Study 1 - Data.sav")
LABEL = {
    "study1": "1",
    "study2": "2",
    "study3": "3",
    "study4": "4",
    "study5": "5",
    "s1": "S1",
    "s2": "S2",
}

# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

_TYPO = {"\xa0": " ", "​": "", "’": "'", "‘": "'", "“": '"', "”": '"'}


def norm(raw: str) -> str:
    """HTML to one line of plain text. Typography only."""
    s = re.sub(r"<br\s*/?>|</p>|</div>", " ", raw or "")
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    for a, b in _TYPO.items():
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------------------
# The questionnaires
# ---------------------------------------------------------------------------


def qsf_path(tag: str) -> Path:
    return MATERIALS / f"Study {LABEL[tag]} - Materials.qsf"


class Survey:
    def __init__(self, tag: str) -> None:
        raw = qsf_path(tag).read_text()
        assert "<img" not in raw and "IM_" not in raw, f"{tag}: a picture in the .qsf"
        els = json.loads(raw)["SurveyElements"]
        self.qs: dict[str, dict[str, Any]] = {
            e["Payload"]["DataExportTag"]: e["Payload"] for e in els if e["Element"] == "SQ"
        }
        self.blocks: dict[str, dict[str, Any]] = {}
        for e in els:
            if e["Element"] == "BL":
                p = e["Payload"]
                for b in p.values() if isinstance(p, dict) else p:
                    self.blocks[b["ID"]] = b
        self.flow: dict[str, Any] = next(e for e in els if e["Element"] == "FL")["Payload"]

    def text(self, tag: str) -> str:
        return norm(self.qs[tag]["QuestionText"])

    def block_with(self, export_tag: str) -> dict[str, Any]:
        qid = self.qs[export_tag]["QuestionID"]
        (b,) = [
            b
            for b in self.blocks.values()
            if any(x.get("QuestionID") == qid for x in b.get("BlockElements", []))
        ]
        return b

    def randomizers(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []

        def walk(n: dict[str, Any]) -> None:
            if n.get("Type") == "BlockRandomizer":
                out.append(n)
            for c in n.get("Flow", []):
                walk(c)

        walk(self.flow)
        return out


SUFFIX = " This is"


def scenario(sv: Survey, export_tag: str) -> str:
    """The fairness question's scenario: its text up to the closing "This is"."""
    t = sv.text(export_tag)
    assert t.endswith(SUFFIX), (export_tag, t[-30:])
    return t[: -len(SUFFIX)]


def binary_scale(sv: Survey, export_tag: str) -> tuple[int, int, str, str]:
    """(1, 2, first answer, second answer), codes from the .qsf's own recodes."""
    q = sv.qs[export_tag]
    assert q["QuestionType"] == "MC" and q["Selector"] == "SAVR", export_tag
    assert q["Validation"]["Settings"]["ForceResponse"] == "ON", export_tag
    order = [str(k) for k in q["ChoiceOrder"]]
    recode = q.get("RecodeValues") or {}
    codes = [int(recode.get(k, k)) for k in order]
    assert codes == [1, 2], (export_tag, codes)
    lo, hi = (norm(q["Choices"][k]["Display"]) for k in order)
    return 1, 2, lo, hi


def likert(sv: Survey, export_tag: str) -> tuple[tuple[int, int, str, str], str, list[str]]:
    """A Likert matrix: its scale, its text and its statements in ChoiceOrder."""
    q = sv.qs[export_tag]
    assert q["QuestionType"] == "Matrix" and q["Selector"] == "Likert", export_tag
    order = [str(k) for k in q["AnswerOrder"]]
    recode = q.get("RecodeValues") or {}
    assert [int(recode.get(k, k)) for k in order] == list(range(1, len(order) + 1))
    labels = [norm(q["Answers"][k]["Display"]) for k in order]
    assert all(lab == "" for lab in labels[1:-1]), labels
    items = [norm(q["Choices"][str(k)]["Display"]) for k in q["ChoiceOrder"]]
    return (1, len(order), labels[0], labels[-1]), sv.text(export_tag), items


def gender_labels(sv: Survey) -> dict[int, str]:
    q = sv.qs["Gender"]
    assert norm(q["QuestionText"]) == "What is your gender?"
    recode = q.get("RecodeValues") or {}
    return {int(recode.get(k, k)): norm(v["Display"]) for k, v in q["Choices"].items()}


# ---------------------------------------------------------------------------
# The experiments
# ---------------------------------------------------------------------------


@dataclass
class Arm:
    code: int
    factors: dict[str, str]
    column: str  # the deposit column holding this arm's fairness answer
    text: str


@dataclass
class Outcome:
    var: str
    question: str
    scale: tuple[int, int, str, str]
    condition_var: str | None = None


@dataclass
class Experiment:
    name: str
    title: str
    factors: list[str]
    arms: list[Arm]
    outcomes: list[Outcome]
    notes: str
    source_var: str = "arm"
    groups: list[list[str]] = field(default_factory=list)  # columns of which one is filled


QUESTION = "This is"


def fairness_outcome(
    sv: Survey, columns: list[str], var: str, condition_var: str | None = None
) -> Outcome:
    scales = {binary_scale(sv, c) for c in columns}
    (sc,) = scales  # every arm offered the same two answers
    return Outcome(var, QUESTION, sc, condition_var)


def between(tag: str, cells: list[tuple[str, dict[str, str]]]) -> tuple[Survey, list[Arm]]:
    """Arms for a between-person study: one column per arm, in the flow's order."""
    sv = Survey(tag)
    (rand,) = sv.randomizers()
    assert rand["SubSet"] == 1, tag
    in_flow = []
    for b in rand["Flow"]:
        (qid,) = [
            x["QuestionID"]
            for x in sv.blocks[b["ID"]]["BlockElements"]
            if x["Type"] == "Question"
            and next(q for q in sv.qs.values() if q["QuestionID"] == x["QuestionID"])[
                "QuestionType"
            ]
            == "MC"
        ]
        in_flow.append(next(t for t, q in sv.qs.items() if q["QuestionID"] == qid))
    assert in_flow == [c for c, _ in cells], (tag, in_flow)
    return sv, [Arm(i + 1, f, c, scenario(sv, c)) for i, (c, f) in enumerate(cells)]


def study1() -> Experiment:
    sv = Survey("study1")
    outer, *inner = sv.randomizers()
    assert outer["SubSet"] == 2 and len(outer["Flow"]) == 2
    assert all(r["SubSet"] == 1 and len(r["Flow"]) == 2 for r in inner) and len(inner) == 2
    cells = [
        ("ChoPrice", {"product": "chocolate", "action": "price_increase"}),
        ("ChoSize", {"product": "chocolate", "action": "size_decrease"}),
        ("OraPrice", {"product": "orange_juice", "action": "price_increase"}),
        ("OraSize", {"product": "orange_juice", "action": "size_decrease"}),
    ]
    arms = [Arm(i + 1, f, c, scenario(sv, c)) for i, (c, f) in enumerate(cells)]
    return Experiment(
        name="study1",
        title="A chocolate maker and an orange juice maker, facing higher production costs, "
        "raise the price or shrink the product: acceptable or unfair? (Study 1)",
        factors=["product", "action"],
        arms=arms,
        outcomes=[
            fairness_outcome(sv, ["ChoPrice", "ChoSize"], "chocolate", "arm_chocolate"),
            fairness_outcome(sv, ["OraPrice", "OraSize"], "orange_juice", "arm_orange_juice"),
        ],
        notes=(
            "Study 1 (pre-registered Nov 2022, AsPredicted #113919), 501 people, all kept "
            "(no exclusions pre-registered). Everyone judged two scenarios, a chocolate "
            "manufacturer and an orange juice manufacturer; for each, whether the firm "
            "raised the price or shrank the product was drawn separately (two randomizers), "
            "so the arm varies within person and each outcome names its own assignment "
            "column (arm_chocolate: 1 price, 2 size; arm_orange_juice: 3 price, 4 size). "
            "The two products were shown in a random order that the deposit does not "
            "record, so neither row mentions the other product (CONVENTIONS: an order "
            "randomised and not recorded cannot be narrated); each person also judged the "
            "other product, before or after. 1 = acceptable, 2 = unfair, as answered."
        ),
        source_var="arm_chocolate",
        groups=[["ChoPrice", "ChoSize"], ["OraPrice", "OraSize"]],
    )


def study2() -> Experiment:
    sv, arms = between(
        "study2",
        [
            ("PriceIncFair", {"action": "price_increase"}),
            ("SizeDecFair", {"action": "size_decrease"}),
        ],
    )
    return Experiment(
        name="study2",
        title="A potato chips maker, facing higher production costs, raises the price or "
        "shrinks the pack: fair or unfair? (Study 2)",
        factors=["action"],
        arms=arms,
        outcomes=[fairness_outcome(sv, [a.column for a in arms], "fair")],
        notes=(
            "Study 2 (pre-registered May 2023, AsPredicted #133275), 301 people, all kept. "
            "Between people: price $3 to $4 or size 12 oz to 9 oz. 1 = fair, 2 = unfair, as "
            "answered. Not built: the open-ended explanation asked of those who said unfair "
            "(free text) and the authors' four codes of it."
        ),
        groups=[[a.column for a in arms]],
    )


def study3() -> Experiment:
    sv, arms = between(
        "study3",
        [
            ("PriceIncFair", {"action": "price_increase"}),
            ("SizeDecFair", {"action": "size_decrease"}),
        ],
    )
    stems = set()
    statements = []
    for arm, matrix in zip(arms, ["PriceIncProcess", "SizeDecProcess"], strict=True):
        sc, text, items = likert(sv, matrix)
        assert text.startswith(arm.text + " "), matrix  # the matrix repeats the scenario
        stems.add((sc, text[len(arm.text) + 1 :]))
        statements.append(items)
        block = sv.block_with(arm.column)
        assert block["Options"]["RandomizeQuestions"] == "RandomWithXPerPage", matrix
        assert sv.qs[matrix]["Randomization"]["Type"] == "All", matrix
    ((sc, stem),) = stems
    assert stem == "To what extent do you agree with the following statements:", stem
    assert statements[0] == statements[1]
    outcomes = [fairness_outcome(sv, [a.column for a in arms], "fair")]
    outcomes += [Outcome(f"process{i}", f"{stem} {s}", sc) for i, s in enumerate(statements[0], 1)]
    return Experiment(
        name="study3",
        title="A facial tissues maker, facing higher production costs, raises the price or cuts "
        "the sheets: fair or unfair, and is the change deceptive, too big, or forcing people "
        "to buy more? (Study 3)",
        factors=["action"],
        arms=arms,
        outcomes=outcomes,
        notes=(
            "Study 3 (pre-registered Sep 2023, AsPredicted #144533), 1,000 people: the "
            "deposit's 1,001 rows less one blank in every column. Between people: price $6 "
            "to $7.5 or 160 sheets to 128. In the arm's block, the fairness question and a "
            "three-statement agreement matrix that repeats the scenario word-for-word, the "
            "two in an order the deposit does not record (block option RandomWithXPerPage; "
            "the size arm's block fixes the matrix second), so no row narrates the other; the "
            "statements' order within the matrix was "
            "randomised too. 1 = fair, 2 = unfair; 1 = Strongly disagree to 7 = Strongly "
            "agree, as answered."
        ),
        groups=[[a.column for a in arms]],
    )


def study4() -> Experiment:
    sv, arms = between(
        "study4",
        [
            ("LowtrPrice", {"action": "price_increase", "transparency": "low"}),
            ("LowtrSize", {"action": "size_decrease", "transparency": "low"}),
            ("HightrPrice", {"action": "price_increase", "transparency": "high"}),
            ("HightrSize", {"action": "size_decrease", "transparency": "high"}),
        ],
    )
    return Experiment(
        name="study4",
        title="A detergent maker, facing higher production costs, raises the price or cuts the "
        "net weight, saying so on the pack or not: fair or unfair? (Study 4)",
        factors=["action", "transparency"],
        arms=arms,
        outcomes=[fairness_outcome(sv, [a.column for a in arms], "fair")],
        notes=(
            "Study 4 (pre-registered May 2023, AsPredicted #133756), 4,010 people, all kept. "
            "2 x 2 between people: price $16 to $19 or net weight 140 fl oz to 118, and "
            "whether the firm states the change on the packaging (high transparency) or no "
            "more is said (low). 1 = fair, 2 = unfair, as answered."
        ),
        groups=[[a.column for a in arms]],
    )


def study5() -> Experiment:
    sv, arms = between(
        "study5",
        [
            ("CostIncPrice", {"costs": "increased", "action": "price_increase"}),
            ("CostIncSize", {"costs": "increased", "action": "size_decrease"}),
            ("CostSamePrice", {"costs": "not_increased", "action": "price_increase"}),
            ("CostSameSize", {"costs": "not_increased", "action": "size_decrease"}),
        ],
    )
    return Experiment(
        name="study5",
        title="A potato chips maker whose costs have or have not increased raises the price or "
        "shrinks the pack: fair or unfair? (Study 5)",
        factors=["costs", "action"],
        arms=arms,
        outcomes=[fairness_outcome(sv, [a.column for a in arms], "fair")],
        notes=(
            "Study 5 (pre-registered May 2023, AsPredicted #132337), 1,202 people, all kept. "
            "2 x 2 between people: costs have increased or have not, and price $3 to $4 or "
            "size 12 oz to 9 oz. 1 = fair, 2 = unfair (the .qsf recodes its choice 4 to 2), "
            "as answered."
        ),
        groups=[[a.column for a in arms]],
    )


def s1() -> Experiment:
    sv = Survey("s1")
    (rand,) = sv.randomizers()
    assert rand["SubSet"] == 1 and len(rand["Flow"]) == 1  # one block, shown to everyone
    block = sv.block_with("PriceIncFair")
    assert block is sv.block_with("SizeDecFair")
    assert block["Options"]["RandomizeQuestions"] == "RandomWithXPerPage"
    cells = [
        ("PriceIncFair", {"action": "price_increase"}),
        ("SizeDecFair", {"action": "size_decrease"}),
    ]
    arms = [Arm(i + 1, f, c, scenario(sv, c)) for i, (c, f) in enumerate(cells)]
    return Experiment(
        name="s1",
        title="Joint evaluation: the same potato chips maker, facing higher production costs, "
        "raises the price, and shrinks the pack; is each fair or unfair? (Study S1)",
        factors=["action"],
        arms=arms,
        outcomes=[
            fairness_outcome(sv, ["PriceIncFair"], "price", "arm_price"),
            fairness_outcome(sv, ["SizeDecFair"], "size", "arm_size"),
        ],
        notes=(
            "Study S1 (pre-registered Sep 2023, AsPredicted #144974), 200 people, all kept. "
            "Within person: everyone judged both the price increase ($3 to $4) and the size "
            "decrease (12 oz to 9 oz), each person two rows. The two questions were in one "
            "block whose order the deposit does not record (block option RandomWithXPerPage "
            'with the size question listed as fixed; the pre-registration: "The order of the '
            'two scenarios will be randomized"), so neither row mentions the other '
            "(CONVENTIONS: an order not recorded cannot be narrated). The scenario wording is "
            "Study 2's. 1 = fair, "
            "2 = unfair, as answered."
        ),
        source_var="arm_price",
    )


def s2() -> Experiment:
    sv, arms = between(
        "s2",
        [
            ("CostIncPrice", {"reason": "costs_increased", "action": "price_increase"}),
            ("CostIncSize", {"reason": "costs_increased", "action": "size_decrease"}),
            ("MatDecPrice", {"reason": "materials_decreased", "action": "price_increase"}),
            ("MatDecSize", {"reason": "materials_decreased", "action": "size_decrease"}),
        ],
    )
    return Experiment(
        name="s2",
        title="A potato chips maker whose costs have increased, or whose raw-material supply "
        "has fallen, raises the price or shrinks the pack: fair or unfair? (Study S2)",
        factors=["reason", "action"],
        arms=arms,
        outcomes=[fairness_outcome(sv, [a.column for a in arms], "fair")],
        notes=(
            "Study S2 (pre-registered Sep 2023, AsPredicted #142420), 4,005 people, all kept. "
            "2 x 2 between people: costs have increased, or the quantity of raw materials "
            "supplied by vendors has decreased, and price $3 to $4 or size 12 oz to 9 oz. "
            "1 = fair, 2 = unfair (the .qsf recodes its choice 4 to 2), as answered."
        ),
        groups=[[a.column for a in arms]],
    )


def experiments() -> list[Experiment]:
    return [study1(), study2(), study3(), study4(), study5(), s1(), s2()]


# ---------------------------------------------------------------------------
# Coded data
# ---------------------------------------------------------------------------

AGE_RANGE = (18, 100)
N = {
    "study1": 501,
    "study2": 301,
    "study3": 1000,
    "study4": 4010,
    "study5": 1202,
    "s1": 200,
    "s2": 4005,
}
PROCESS_COLS = ["PriceIncProcess", "SizeDecProcess"]


def data_file(tag: str) -> str:
    return f"{STUDY_ID}_{tag}.csv"


def read_deposit(tag: str) -> pd.DataFrame:
    """The deposit's file as it is, with each person's row number (1-based) as `row`."""
    if tag == "study2":
        df = pd.read_csv(DATA / "Study 2 - Data.csv")
    else:
        df, _ = pyreadstat.read_sav(str(DATA / f"Study {LABEL[tag]} - Data.sav"))
    df.insert(0, "row", range(1, len(df) + 1))
    return df


def deposit(tag: str) -> pd.DataFrame:
    """The deposit's rows that are kept: all but Study 3's one row that is blank throughout."""
    df = read_deposit(tag)
    blank = df.drop(columns="row").isna().all(axis=1)
    assert blank.sum() == (1 if tag == "study3" else 0), (tag, int(blank.sum()))
    df = df[~blank].reset_index(drop=True)
    assert len(df) == N[tag], (tag, len(df))
    return df


def prep(tag: str) -> pd.DataFrame:
    """One coded row per kept person: arm column(s), answers, age, gender."""
    (e,) = [x for x in experiments() if x.name == tag]
    sv = Survey(tag)
    df = deposit(tag)
    out = pd.DataFrame({"pid": [f"{tag}_{r}" for r in df["row"]]})
    code = {a.column: a.code for a in e.arms}
    if tag == "s1":
        for c in ("PriceIncFair", "SizeDecFair"):
            assert df[c].notna().all(), c  # everyone answered both
        out["arm_price"], out["arm_size"] = code["PriceIncFair"], code["SizeDecFair"]
        out["price"] = df["PriceIncFair"].astype(int)
        out["size"] = df["SizeDecFair"].astype(int)
    else:
        for group, outcome in zip(e.groups, e.outcomes[: len(e.groups)], strict=True):
            filled = df[group].notna()
            assert (filled.sum(axis=1) == 1).all(), (tag, group)  # exactly one arm each
            arm = filled.idxmax(axis=1).map(code)
            out[outcome.condition_var or e.source_var] = arm.values
            out[outcome.var] = df[group].bfill(axis=1).iloc[:, 0].astype(int).values
        if tag == "study3":
            for i in (1, 2, 3):
                cols = [f"{m}_{i}" for m in PROCESS_COLS]
                filled = df[cols].notna()
                assert (filled.sum(axis=1) == 1).all()
                # a person's matrix is the one in their own arm's block
                assert (filled[cols[0]].values == (out["arm"] == 1).values).all()
                out[f"process{i}"] = df[cols].bfill(axis=1).iloc[:, 0].astype(int).values
    for o in e.outcomes:
        lo, hi = o.scale[0], o.scale[1]
        assert out[o.var].between(lo, hi).all(), (tag, o.var)
    labels = gender_labels(sv)
    age = pd.to_numeric(df["Age"], errors="coerce")
    out["age"] = age.where(age.between(*AGE_RANGE)).astype("Int64").values
    out["gender"] = [labels[int(g)] if pd.notna(g) else None for g in df["Gender"]]
    return out


def check_codebook(tag: str) -> None:
    """Each column's label in the codebook is the question the .qsf asks under that tag."""
    sv = Survey(tag)
    book = pd.read_csv(next(CODEBOOK.glob(f"Study {LABEL[tag]} - Data.*___CODEBOOK.csv")))
    if tag == "study2":
        return  # Study 2's codebook describes its columns in words, not question text
    for var, desc in zip(book["varname"], book["description"], strict=True):
        base, _, item = var.partition("_")
        if base in sv.qs and not item:
            assert norm(desc) == sv.text(base), var
        elif base in sv.qs:
            q = sv.qs[base]
            choice = str(q["ChoiceOrder"][int(item) - 1])
            want = f"{sv.text(base)} - {norm(q['Choices'][choice]['Display'])}"
            assert norm(desc) == want, var


# ---------------------------------------------------------------------------
# The recipes
# ---------------------------------------------------------------------------


def _scale(sc: tuple[int, int, str, str]) -> dict[str, Any]:
    return {"min": sc[0], "max": sc[1], "min_label": sc[2], "max_label": sc[3]}


def recipe(e: Experiment) -> dict[str, Any]:
    arms = [
        {
            "raw_values": {e.source_var: a.code},
            "condition_num": i,
            "factors": a.factors,
            "text": a.text,
        }
        for i, a in enumerate(e.arms)
    ]
    outcomes = []
    for t, o in enumerate(e.outcomes):
        out: dict[str, Any] = {"var": o.var, "task_num": t, "question": o.question}
        out["scale"] = _scale(o.scale)
        if o.condition_var:
            out["condition_var"] = o.condition_var
        outcomes.append(out)
    top = max(o.scale[1] for o in e.outcomes)
    notes = (
        f"{PAPER}\n\nGENERATED by scripts/gen_researchbox1032.py; every judgement is in its "
        f"docstring. {e.notes}\n\nWording from {qsf_path(e.name).name}. Each fairness screen "
        'was the scenario followed by "This is" and the two answers; the scenario is the '
        'condition and "This is" the question, both word-for-word. The assignment is '
        "derived from which arm's column is filled (every fairness question was "
        "ForceResponse, so a blank means not shown). Typography normalised (HTML entities, "
        "non-breaking spaces). No words added. Persona: age (years; outside 18-100 left "
        "blank) and gender, labels from the .qsf's own choices."
    )
    return {
        "study_id": STUDY_ID,
        "source": "researchbox",
        "experiment": e.name,
        "title": e.title,
        "data_file": data_file(e.name),
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": "pid",
        "notes": notes,
        "condition": {"source_vars": [e.source_var], "factors": e.factors, "arms": arms},
        "outcomes": outcomes,
        "response_recode": {k: k for k in range(1, top + 1)},
        "missing_codes": [],
        "persona_map": {"age": "age", "gender": "gender"},
    }


def recipe_path(e: Experiment) -> Path:
    return RECIPES / f"{STUDY_ID}_{e.name}.yaml"


def render(e: Experiment) -> str:
    return yaml.safe_dump(recipe(e), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prep", action="store_true", help="code the data")
    ap.add_argument("--check", action="store_true", help="exit 1 if any recipe differs")
    args = ap.parse_args()
    if args.prep:
        for tag in LABEL:
            check_codebook(tag)
            path = RAW / data_file(tag)
            prep(tag).to_csv(path, index=False)
            print(f"wrote {path.relative_to(REPO)}")
        return 0
    bad = 0
    for e in experiments():
        path, text = recipe_path(e), render(e)
        if args.check:
            same = path.exists() and path.read_text() == text
            bad += not same
            print(("matches " if same else "DIFFERS ") + path.name)
        else:
            path.write_text(text)
            print(f"wrote {path.relative_to(REPO)}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
