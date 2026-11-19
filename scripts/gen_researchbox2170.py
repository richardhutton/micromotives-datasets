#!/usr/bin/env python3
"""Write recipes/researchbox2170_*.yaml: buy now, pay later versus a lump sum (3 recipes).

Maesen S & Ang D, "Buy Now Pay Later: Impact of Installment Payments on Customer
Purchases" (the project title in the deposit's README; the deposit does not say where or
whether the paper is published). ResearchBox 2170 ("BNPL and Spending",
https://researchbox.org/2170). CC BY 4.0 ("All content posted to ResearchBox is under a CC
By 4.0 License", the box page). Online samples, autumn 2023 (the consent screen calls the
task a "HIT"); US dollars; kept as the source has them.

Every judgement is here, in code, so the recipes can be re-derived and reviewed.

THE DEPOSIT. Folder names begin with a space (" Data", " Materials", " Other" ...). The
main studies' data are inside jamovi .omv files in " Other": an .omv is a zip whose
data.bin holds the columns one after another (int32 per cell for Integer and Text columns,
float64 for Decimal), with text values in strings.bin (ID columns, by byte offset) or in
xdata.json's level labels (Nominal text columns). `read_omv` decodes that and asserts it
consumed data.bin exactly. `--prep` writes each decoded table, every column, to
data/raw/researchbox2170/omv/<name>.csv and then the coded file the recipes read. The
originals are never written to.

WHICH QUESTIONNAIRE. Every study ships a 2024 "Submission:" export, twice, under "X.qsf"
and "X_.qsf"; the pairs are byte-identical (asserted). The README says these are "the
correct files with the trash removed". Studies 3 and Supplementary Study 2 also ship the
export made when they were fielded (survey created 14 and 16 Oct 2023, the days their data
were collected): BNPL_T-shirt_Study_3.qsf and "Supplementary Study 2 [Web Appendix H].qsf".
`check_qsf_pair` asserts that, for every question in a block the flow shows, the fielded and
the submission exports agree on normalised text, choices, answers, their order, recodes,
display logic and randomisation, and that the two flows are identical. They differ only in
one HTML attribute (a browser extension's data-sider-select-id inside a <b> tag, Study 3)
and in export tags (Supplementary Study 2: the fielded Q21/Q22 became PC/BC). The recipes
read the fielded export.

WHAT IS BUILT. Only the two studies whose questionnaires contain no picture at all (no
<img> in either export; the ruling below):
- Study 3 (T-shirt, $24): pay $24 now, pay $24 in 30 days, or 3 instalments of $8.
  Recipe study3: the four financial-constraint statements, asked on the stimulus page.
  Recipe study3_followup: the five price-perception statements ("feelings of being
  misled"), the four perceived-benefit statements and the three price-attractiveness
  statements, asked after it in two blocks whose order was randomised and recorded
  (FL_33_DO), so that order is a factor.
- Supplementary Study 2 (4 coffee mugs, $27): pay $27 in 21 days, or 3 instalments of $9.
  Recipe ss2: financial constraint (stimulus page), then perceived costs, then budget
  control, on three pages in a fixed order.

NOT BUILT (rich, 19 Nov 2026: if the manipulation, the price or the product is carried by
a picture, skip the study rather than transcribe or describe it):
- Study 2 (Halloween decorations): every one of the 25 products is offered as a picture
  beside its name and price, and the opening screen of each arm ends in a different picture
  (IM_dcZhxw8u8reQjFs, IM_6swELnaSs3Ve9q6) placed under the worked payment example. The
  outcome is a multi-select basket, and every later screen pipes the person's own total
  (${gr://SC_9t2iHac0ss2eN5c/Score}).
- Study 4 (flights, $59.10): the purchase screen of each arm ends in a 582x451 picture
  (IM_dcDtH2eaEbpEysm, IM_3EIZkJIPiKFhy2a), and the hotspot items that follow ask people to
  click "Pay $9.85 today" or "Pay $59.10 later" on it: the picture carries payment wording
  the text does not.
- Supplementary Study 1a (duvet): the product, its price and the payment method are shown
  only as a picture ("you've found the following duvet set ..." then IM_6yAA9KiaEFgJyBM /
  IM_7TYDoHIO53swhGm / IM_4VkRnxmAc2ZHXFk).
- Supplementary Study 1b (duvet): each product pair is shown only as two pictures before
  "Will you purchase ...?"; in the submission export the financial-constraint arm's block is
  empty.
- Supplementary Study 3 (coffee pods): each of the four arms' screens ends "Using the
  following payment, you can pay ..." and then a picture of its own (IM_aViTjivrEx3Ym5E,
  IM_0TUq6MNdwHAMi58, IM_e9RBW2UK0rOE1bU, IM_2t8xOqq42MhLdJQ); the screen also pipes the
  person's own brand choice.
The 386 <img> tags across the 21 .qsf files all sit in these five studies' exports.

NARRATION (ours, CONVENTIONS "Narrating what the respondent did"). A row's condition is the
stimulus screen and then every question shown on an EARLIER page, each line quoted as
the screen had it, introduced by one of two clauses of ours:
  "You were then asked (the statements were shown in a random order):"  where the .qsf
      randomises a matrix's statements (financial constraint; SS2's perceived costs)
  "You were then asked:"  for pages in a fixed order
The stimulus page is never re-shown in these studies, so it is not repeated. In
study3_followup the price-perception page opens with "What is the price of the T-shirt?"
above the five statements; it is narrated for those rows too, as it precedes them.

OUTCOMES. A matrix statement is one outcome, its question the matrix's stem plus the
statement ("To what extent does this payment method... make you feel less financially
constrainted", typo the source's). Separate statements under one intro (Study 3's
price-perception and benefit items) take the intro as their stem. Columns FC1_1..FC1_4
(and PC1..4, BC1..4) are the statements in the .qsf's ChoiceOrder (choice ids 1, 4, 5,
6): the export numbered them by position, as the display-order columns show (FC1_DO and
Q22_DO hold permutations of 1-4, never 5 or 6), and the pre-registrations list the items in
that order. Codes are the .qsf's own: 1 = the first answer shown, 9 = the last (asserted
against AnswerOrder and RecodeValues). The authors reverse the financial-constraint items
and PB4R in jamovi; the rows keep the codes as answered. NOT BUILT: "What is the price of
the T-shirt?" (a recall check; 598 people) and the two manipulation checks "How would you
describe the payment method?" (Lump sum/Ongoing Instalments, Now/Deferred; Study 3 and
SS2), CONVENTIONS "Attention and recall checks are not outcomes".

EXCLUSIONS reproduce the authors' jamovi N. Study 3: the jamovi filter (IMC2 == 1, the
closing attention check) and an assignment, 598 (200 / 197 / 201). Supplementary Study 2:
everyone with an assignment, 597 (297 / 300); of the 21 others, 5 failed the opening
attention check, which ends the survey, and 16 have no answer to it and nothing after. Age outside 18-100 (Study 3 has a 4) is left blank in the
persona; the person is kept.

JEV. scripts/recipe_prep.py reads .sav/.dta/.por only; the built studies' data exist only
as .omv, so it does not apply (the two .sav files are the unbuilt Supplementary Study 1).
The assignment is the embedded field BNPL that each survey's randomiser sets, and the
deposit's own randomiser record (FL_6_DO) is asserted to agree with it person by person.

    uv run python scripts/gen_researchbox2170.py --prep   # decode the .omv files, code the data
    uv run python scripts/gen_researchbox2170.py          # write the recipes
    uv run python scripts/gen_researchbox2170.py --check  # exit 1 if any recipe differs
"""

from __future__ import annotations

import argparse
import html
import json
import re
import struct
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
STUDY_ID = "researchbox2170"
RAW = REPO / "data" / "raw" / STUDY_ID
MATERIALS = RAW / " Materials"
OTHER = RAW / " Other"
EXTRACTED = RAW / "omv"
RECIPES = REPO / "recipes"
LICENCE = (
    'CC BY 4.0, stated on the box page https://researchbox.org/2170 ("All content posted '
    'to ResearchBox is under a CC By 4.0 License"). Read 19 Nov 2026.'
)
PAPER = (
    'Maesen S & Ang D, "Buy Now Pay Later: Impact of Installment Payments on Customer '
    "Purchases\" (project title in the deposit's README; no publication is named). "
    "ResearchBox 2170 (https://researchbox.org/2170)."
)

# tag -> (fielded export, submission export, its byte-identical copy)
QSF = {
    "study3": (
        "BNPL_T-shirt_Study_3.qsf",
        "Study3_BNPL_T-shirt.qsf",
        "Study3_BNPL_T-shirt_.qsf",
    ),
    "ss2": (
        "Supplementary Study 2 [Web Appendix H].qsf",
        "SS2_BNPL_-Mugs.qsf",
        "SS2_BNPL_-Mugs_.qsf",
    ),
}
OMV = {
    "study3": "BNPL T-shirt (Study 3).omv",
    "ss2": "BNPL Mugs [Supplementary Study 2] - JAMOVI data.omv",
}

# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

_TYPO = {"\xa0": " ", "​": "", "’": "'", "‘": "'", "“": '"', "”": '"'}


def lines(raw: str) -> str:
    """HTML to plain text, keeping the screen's line breaks. Typography only."""
    s = re.sub(r"\s*\n\s*", " ", raw or "")
    s = re.sub(r"<br\s*/?>|</p>|</div>|<div[^>]*>|<p[^>]*>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    for a, b in _TYPO.items():
        s = s.replace(a, b)
    out = [re.sub(r"[ \t]+", " ", ln).strip() for ln in s.split("\n")]
    return "\n".join(ln for ln in out if ln)


def norm(raw: str) -> str:
    return re.sub(r"\s+", " ", lines(raw)).strip()


# ---------------------------------------------------------------------------
# The questionnaires
# ---------------------------------------------------------------------------


def load_qsf(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((MATERIALS / name).read_text())
    return data


class Survey:
    def __init__(self, name: str) -> None:
        els = load_qsf(name)["SurveyElements"]
        self.qs: dict[str, dict[str, Any]] = {
            e["Payload"]["QuestionID"]: e["Payload"] for e in els if e["Element"] == "SQ"
        }
        self.blocks: dict[str, dict[str, Any]] = {}
        for e in els:
            if e["Element"] == "BL":
                p = e["Payload"]
                for b in p.values() if isinstance(p, dict) else p:
                    self.blocks[b["ID"]] = b
        self.flow: dict[str, Any] = next(e for e in els if e["Element"] == "FL")["Payload"]

    def live(self) -> set[str]:
        """Questions in a non-trash block that the flow shows."""
        shown = json.dumps(self.flow)
        out: set[str] = set()
        for bid, b in self.blocks.items():
            if b.get("Type") != "Trash" and f'"{bid}"' in shown:
                out |= {
                    x["QuestionID"] for x in b.get("BlockElements", []) if x["Type"] == "Question"
                }
        return out

    def block_of(self, description: str) -> list[str]:
        b = next(b for b in self.blocks.values() if b.get("Description") == description)
        return [x["QuestionID"] for x in b["BlockElements"] if x["Type"] == "Question"]

    def assignments(self) -> dict[str, str]:
        """FlowID -> BNPL value, for the randomiser that sets BNPL."""
        out: dict[str, str] = {}

        def walk(n: dict[str, Any]) -> None:
            if n.get("Type") == "BlockRandomizer":
                for c in n.get("Flow", []):
                    if c.get("Type") == "EmbeddedData":
                        (e,) = c["EmbeddedData"]
                        if e["Field"] == "BNPL":
                            out[c["FlowID"]] = str(e["Value"])
            for c in n.get("Flow", []):
                walk(c)

        walk(self.flow)
        return out


def _shown_when(q: dict[str, Any]) -> str | None:
    """The BNPL value a question's display logic requires, or None if always shown."""
    dl = q.get("DisplayLogic")
    if not dl:
        return None
    (c,) = [v for k, v in dl["0"].items() if k.isdigit()]
    assert c["LeftOperand"] == "BNPL" and c["Operator"] == "EqualTo", c
    return str(c["RightOperand"])


def check_qsf_pair(tag: str) -> None:
    """The fielded and the submission exports agree on everything a respondent saw."""
    fielded, sub, copy = QSF[tag]
    assert (MATERIALS / sub).read_bytes() == (MATERIALS / copy).read_bytes(), (sub, copy)
    a, b = Survey(fielded), Survey(sub)
    assert a.live() == b.live(), tag

    def view(p: dict[str, Any]) -> dict[str, Any]:
        return {
            "text": norm(p.get("QuestionText", "")),
            "choices": {k: norm(v.get("Display", "")) for k, v in (p.get("Choices") or {}).items()},
            "answers": {k: norm(v.get("Display", "")) for k, v in (p.get("Answers") or {}).items()},
            "order": [p.get("ChoiceOrder"), p.get("AnswerOrder")],
            "recode": p.get("RecodeValues"),
            "logic": p.get("DisplayLogic"),
            "random": p.get("Randomization"),
            "type": [p["QuestionType"], p.get("Selector"), p.get("SubSelector")],
        }

    for qid in sorted(a.live()):
        assert view(a.qs[qid]) == view(b.qs[qid]), f"{tag} {qid} differs between exports"
    assert json.dumps(a.flow, sort_keys=True) == json.dumps(b.flow, sort_keys=True), tag
    for name in (fielded, sub):
        assert "<img" not in (MATERIALS / name).read_text(), f"{name} has a picture"


def scale_of(q: dict[str, Any]) -> tuple[int, int, str, str]:
    """(min, max, min_label, max_label) from the .qsf; codes asserted 1..n in screen order."""
    order = [str(x) for x in q["AnswerOrder"]]
    recode = q.get("RecodeValues") or {}
    codes = [int(recode.get(k, k)) for k in order]
    assert codes == list(range(1, len(order) + 1)), (q["QuestionID"], codes)
    if q["Selector"] == "Bipolar":
        (choice,) = q["Choices"].values()
        lo, hi = norm(choice["Display"]).split(":")
    else:
        lo, hi = (norm(q["Answers"][order[i]]["Display"]) for i in (0, -1))
        assert all(norm(q["Answers"][k]["Display"]) in ("", ".") for k in order[1:-1]), q[
            "QuestionID"
        ]
    return 1, len(order), lo.strip(), hi.strip()


def statements(q: dict[str, Any]) -> list[str]:
    """A matrix's statements in the .qsf's ChoiceOrder (the export's column order)."""
    return [norm(q["Choices"][str(k)]["Display"]) for k in q["ChoiceOrder"]]


# ---------------------------------------------------------------------------
# The data: jamovi .omv
# ---------------------------------------------------------------------------

_MISSING_INT = -2147483648


def read_omv(path: Path) -> tuple[pd.DataFrame, dict[str, dict[int, str]]]:
    """Decode an .omv: every column, and each Nominal column's {code: import value}."""
    z = zipfile.ZipFile(path)
    meta = json.loads(z.read("metadata.json"))["dataSet"]
    xdata = json.loads(z.read("xdata.json"))
    data, strings = z.read("data.bin"), z.read("strings.bin")
    n, off = meta["rowCount"], 0
    cols: dict[str, list[Any]] = {}
    levels: dict[str, dict[int, str]] = {}
    for f in meta["fields"]:
        name = f["name"]
        labs = xdata.get(name, {}).get("labels", [])
        levels[name] = {int(lv[0]): str(lv[2]) for lv in labs}
        if f["dataType"] == "Decimal":
            cols[name] = list(struct.unpack_from(f"<{n}d", data, off))
            off += 8 * n
            continue
        raw = struct.unpack_from(f"<{n}i", data, off)
        off += 4 * n
        if f["dataType"] == "Text" and f["measureType"] == "ID":
            cols[name] = [
                None if v == _MISSING_INT else strings[v : strings.index(b"\0", v)].decode()
                for v in raw
            ]
        elif f["dataType"] == "Text":
            text = {int(lv[0]): str(lv[1]) for lv in labs}
            cols[name] = [None if v == _MISSING_INT else text[v] for v in raw]
        else:
            cols[name] = [None if v == _MISSING_INT else v for v in raw]
    assert off == len(data), f"{path.name}: decoded {off} of {len(data)} bytes"
    df = pd.DataFrame(cols)
    for name, vals in cols.items():
        if vals and all(v is None or isinstance(v, int) for v in vals):
            df[name] = pd.array(vals, dtype="Int64")
    return df, levels


def gender_labels(sv: Survey) -> dict[int, str]:
    q = next(p for p in sv.qs.values() if norm(p["QuestionText"]) == "What is your gender?")
    return {int(q["RecodeValues"][k]): norm(v["Display"]) for k, v in q["Choices"].items()}


AGE_RANGE = (18, 100)


def persona_cols(sv: Survey, df: pd.DataFrame) -> pd.DataFrame:
    labels = gender_labels(sv)
    age = pd.to_numeric(df["Age"], errors="coerce")
    return pd.DataFrame(
        {
            "age": age.where(age.between(*AGE_RANGE)).astype("Int64"),
            "gender": [labels[int(g)] if pd.notna(g) else None for g in df["Gender"]],
        }
    )


# ---------------------------------------------------------------------------
# The experiments
# ---------------------------------------------------------------------------

RANDOM_CLAUSE = "You were then asked (the statements were shown in a random order):"  # ours
FIXED_CLAUSE = "You were then asked:"  # ours


def narrate(clause: str, shown: list[str]) -> str:
    return "\n".join([clause] + [f'"{s}"' for s in shown])


@dataclass
class Outcome:
    var: str
    question: str
    scale: tuple[int, int, str, str]
    earlier: list[tuple[str, list[str]]] = field(default_factory=list)  # narrated pages


@dataclass
class Arm:
    raw: dict[str, int]
    factors: dict[str, str]
    screen: str  # the stimulus screen
    earlier: list[tuple[str, list[str]]] = field(default_factory=list)  # arm-level pages
    item_pages: dict[int, list[tuple[str, list[str]]]] = field(default_factory=dict)


@dataclass
class Experiment:
    name: str
    tag: str
    title: str
    source_vars: list[str]
    factors: list[str]
    arms: list[Arm]
    outcomes: list[Outcome]
    notes: str


def condition(screen: str, pages: list[tuple[str, list[str]]]) -> str:
    return "\n\n".join([screen] + [narrate(c, s) for c, s in pages])


def stimulus_screens(sv: Survey, block: str) -> dict[str, str]:
    """BNPL value -> the stimulus text shown on the block's first page."""
    out: dict[str, str] = {}
    for qid in sv.block_of(block):
        q = sv.qs[qid]
        if q["QuestionType"] == "DB":
            when = _shown_when(q)
            assert when is not None and when not in out, qid
            out[when] = lines(q["QuestionText"])
    assert sorted(out) == sorted(sv.assignments().values()), (block, sorted(out))
    return out


def matrix(sv: Survey, qid: str, var: str) -> tuple[list[Outcome], list[str]]:
    """One outcome per statement of a Likert matrix, and its lines as narrated."""
    q = sv.qs[qid]
    stem = norm(q["QuestionText"])
    items = statements(q)
    sc = scale_of(q)
    outs = [Outcome(f"{var}{i}", f"{stem} {s}", sc) for i, s in enumerate(items, 1)]
    return outs, [stem, *items]


def separate(
    sv: Survey, intro: str, qids: list[str], vars_: list[str]
) -> tuple[list[Outcome], list[str]]:
    """Single-statement bipolar questions under one intro screen text."""
    outs, shown = [], [intro]
    for qid, var in zip(qids, vars_, strict=True):
        q = sv.qs[qid]
        st = norm(q["QuestionText"])
        outs.append(Outcome(var, f"{intro} {st}", scale_of(q)))
        shown.append(st)
    return outs, shown


def study3() -> tuple[Experiment, Experiment]:
    sv = Survey(QSF["study3"][0])
    assert sv.block_of("Financial Constraints") == ["QID192", "QID194", "QID195", "QID80"]
    screens = stimulus_screens(sv, "Financial Constraints")
    pay = {"0": "pay_now", "1": "pay_in_30_days", "2": "three_instalments"}
    assert sv.qs["QID80"]["Randomization"]["Type"] == "All"
    fc, fc_shown = matrix(sv, "QID80", "fc")
    fc_page = (RANDOM_CLAUSE, fc_shown)

    # Price-perception block: one page (no page break), the recall slider then M1-M5.
    price_block = sv.block_of("Price Attractiveness & Feeling of being misled")
    assert price_block == ["QID216", "QID154", "QID155", "QID156", "QID157", "QID158", "QID159"]
    amt = norm(sv.qs["QID216"]["QuestionText"])
    assert amt == "What is the price of the T-shirt?"
    misled, misled_shown = separate(
        sv, norm(sv.qs["QID154"]["QuestionText"]), price_block[2:], [f"m{i}" for i in range(1, 6)]
    )
    # Benefits block: page 1 intro + PB1-PB4R; page break; page 2 the Att matrix.
    b = next(b for b in sv.blocks.values() if b.get("Description") == "Perceived benefits\xa0")
    assert [x["Type"] for x in b["BlockElements"]] == ["Question"] * 5 + ["Page Break", "Question"]
    benefit_ids = sv.block_of("Perceived benefits\xa0")
    assert benefit_ids == ["QID174", "QID175", "QID176", "QID177", "QID178", "QID217"]
    benefits, benefits_shown = separate(
        sv, norm(sv.qs["QID174"]["QuestionText"]), benefit_ids[1:5], ["pb1", "pb2", "pb3", "pb4r"]
    )
    att, att_shown = matrix(sv, "QID217", "att")
    assert "Randomization" not in sv.qs["QID217"] or not sv.qs["QID217"]["Randomization"]

    first = Experiment(
        name="study3",
        tag="study3",
        title="T-shirt: pay $24 now, in 30 days or in 3 instalments of $8; feeling financially "
        "constrained (Study 3)",
        source_vars=["BNPL"],
        factors=["payment"],
        arms=[Arm({"BNPL": int(v)}, {"payment": pay[v]}, screens[v]) for v in sorted(screens)],
        outcomes=fc,
        notes=(
            "Study 3, 14 Oct 2023. A $24 T-shirt paid $24 now, $24 in 30 days, or in 3 "
            "instalments of $8, then four statements on financial constraint on the same page "
            "(order randomised and recorded, FC1_DO; the condition does not depend on it). "
            "598 of 632 kept, the authors' jamovi N: the filter IMC2 == 1 (closing attention "
            "check) and an assignment. 1 = Not at all, 9 = Very much, as answered; the authors "
            "reverse all four into a constraint score."
        ),
    )
    price_page = (FIXED_CLAUSE, [amt, *misled_shown])
    pb_page = (FIXED_CLAUSE, benefits_shown)
    later = [*misled, *benefits, *att]
    arms = []
    for v in sorted(screens):
        for order, flag in (("price_first", 1), ("benefits_first", 0)):
            before = [price_page] if flag else []
            pages: dict[int, list[tuple[str, list[str]]]] = {}
            for t, o in enumerate(later):
                if o in benefits:
                    pages[t] = [fc_page, *before]
                elif o in att:
                    pages[t] = [fc_page, *before, pb_page]
            arms.append(
                Arm(
                    {"BNPL": int(v), "price_first": flag},
                    {"payment": pay[v], "block_order": order},
                    screens[v],
                    # the arm text is the price-page rows' condition
                    [fc_page]
                    + ([] if flag else [pb_page, (FIXED_CLAUSE, att_shown)])
                    + [(FIXED_CLAUSE, [amt])],
                    pages,
                )
            )
    followup = Experiment(
        name="study3_followup",
        tag="study3",
        title="T-shirt: pay $24 now, in 30 days or in 3 instalments of $8; how clear and fair "
        "the price seems, and the benefit and price appeal of the purchase (Study 3)",
        source_vars=["BNPL", "price_first"],
        factors=["payment", "block_order"],
        arms=arms,
        outcomes=later,
        notes=(
            "Study 3, the questions after the financial-constraint page, in two blocks shown in "
            "a randomised and recorded order (FL_33_DO, coded price_first): the price page "
            '("What is the price of the T-shirt?", a recall check not built, then five '
            "statements on how clear and fair the price is) and the benefits block (four "
            "statements on one page, then the three-statement price-attractiveness matrix on "
            "the next). Each row's condition is the stimulus screen and then every earlier "
            "page, narrated (see the docstring): in the price-first order the benefit rows "
            "follow the price page, in the benefits-first order the price rows follow both "
            "benefit pages. 598 kept, as in study3. Every scale is 1 = Strongly disagree to "
            "9 = Strongly agree, as answered (PB4R is the authors' reverse-scored item)."
        ),
    )
    return first, followup


def ss2() -> Experiment:
    sv = Survey(QSF["ss2"][0])
    block = "Financial Constraints"
    b = next(b for b in sv.blocks.values() if b.get("Description") == block)
    kinds = [x["Type"] if x["Type"] != "Question" else x["QuestionID"] for x in b["BlockElements"]]
    assert kinds == ["QID194", "QID195", "QID80", "Page Break", "QID220", "Page Break", "QID221"]
    screens = stimulus_screens(sv, block)
    pay = {"1": "pay_in_21_days", "2": "three_instalments"}
    for qid in ("QID80", "QID220", "QID221"):
        assert sv.qs[qid]["Randomization"]["Type"] == "All", qid
    fc, fc_shown = matrix(sv, "QID80", "fc")
    pc, pc_shown = matrix(sv, "QID220", "pc")
    bc, _ = matrix(sv, "QID221", "bc")
    outcomes = list(fc)
    outcomes += [Outcome(o.var, o.question, o.scale, [(RANDOM_CLAUSE, fc_shown)]) for o in pc]
    outcomes += [
        Outcome(o.var, o.question, o.scale, [(RANDOM_CLAUSE, fc_shown), (RANDOM_CLAUSE, pc_shown)])
        for o in bc
    ]
    return Experiment(
        name="ss2",
        tag="ss2",
        title="Four coffee mugs: pay $27 in 21 days or in 3 instalments of $9; financial "
        "constraint, perceived cost and budget control (Supplementary Study 2)",
        source_vars=["BNPL"],
        factors=["payment"],
        arms=[Arm({"BNPL": int(v)}, {"payment": pay[v]}, screens[v]) for v in sorted(screens)],
        outcomes=outcomes,
        notes=(
            "Supplementary Study 2 (Web Appendix H), 16 Oct 2023. A $27 set of four mugs paid "
            "$27 in 21 days or in 3 instalments of $9 (at 7, 14 and 21 days), then three "
            "four-statement matrices on three pages in a fixed order: financial constraint (on "
            "the stimulus page), perceived costs, budget control. Each matrix's statements "
            "were randomised (.qsf; recorded in FC1_DO and Q22_DO; the perceived-cost column "
            "Q21_DO is empty in the deposit). A later page's condition is the stimulus screen "
            "and then the earlier pages, narrated (see the docstring). 597 of 618 kept, the "
            "authors' jamovi N: everyone assigned (of the other 21, 5 failed the opening "
            "attention check, which ends the survey, and 16 have no answer to it and nothing "
            "after). 1 = Not at all, 9 = Very much, as answered; the "
            "authors reverse the financial-constraint items."
        ),
    )


def experiments() -> list[Experiment]:
    a, b = study3()
    return [a, b, ss2()]


# ---------------------------------------------------------------------------
# Coded data
# ---------------------------------------------------------------------------

DATA_COLS = {  # tag -> {coded outcome var: deposit column}
    "study3": {
        **{f"fc{i}": f"FC1_{i}" for i in range(1, 5)},
        **{f"m{i}": f"M{i}_1" for i in range(1, 6)},
        "pb1": "PB1_1",
        "pb2": "PB2_1",
        "pb3": "PB3_1",
        "pb4r": "PB4R_1",
        **{f"att{i}": f"Att_{i}" for i in range(1, 4)},
    },
    "ss2": {
        **{f"fc{i}": f"FC1_{i}" for i in range(1, 5)},
        **{f"pc{i}": f"PC{i}" for i in range(1, 5)},
        **{f"bc{i}": f"BC{i}" for i in range(1, 5)},
    },
}
KEPT = {"study3": (598, {0: 200, 1: 197, 2: 201}), "ss2": (597, {1: 297, 2: 300})}
PRICE_FIRST = "PriceAttractiveness&Feelingofbeingmisled|Perceivedbenefits\xa0"
BENEFITS_FIRST = "Perceivedbenefits\xa0|PriceAttractiveness&Feelingofbeingmisled"


def data_file(tag: str) -> str:
    return f"{STUDY_ID}_{tag}.csv"


def deposit(tag: str) -> pd.DataFrame:
    """The decoded .omv after the authors' exclusions, with BNPL as the .qsf's value."""
    df, levels = read_omv(OTHER / OMV[tag])
    if tag == "study3":
        assert (df["Filter 1"] == (df["IMC2"] == 1).fillna(False).astype(int)).all()
        df = df[(df["IMC2"] == 1).fillna(False) & df["BNPL"].notna()].copy()
        df["BNPL"] = [int(levels["BNPL"][int(v)]) for v in df["BNPL"]]
    else:
        code = {lab: int(levels["BNPL"][k]) for k, lab in enumerate(["Defer LS", "BNPL (2)"])}
        assert levels["BNPL"] == {0: "1", 1: "2"}
        df = df[df["BNPL"].notna()].copy()
        df["BNPL"] = df["BNPL"].map(code)
        assert (df["IMC1"] == 1).all()
    n, by_arm = KEPT[tag]
    assert len(df) == n and df["BNPL"].value_counts().to_dict() == by_arm, tag
    # The deposit's record of the randomiser branch agrees with the assignment.
    flows = Survey(QSF[tag][0]).assignments()
    assert [flows[f] for f in df["FL_6_DO"]] == [str(v) for v in df["BNPL"]], tag
    return df.reset_index(drop=True)


def prep(tag: str) -> pd.DataFrame:
    """One coded row per kept respondent: assignment, answers, age, gender."""
    check_qsf_pair(tag)
    sv = Survey(QSF[tag][0])
    df = deposit(tag)
    out = pd.DataFrame({"pid": [f"{tag}_{r}" for r in df["ResponseId"]]})
    out["BNPL"] = df["BNPL"].astype(int)
    if tag == "study3":
        order = {PRICE_FIRST: 1, BENEFITS_FIRST: 0}
        assert set(df["FL_33_DO"]) == set(order)
        out["price_first"] = df["FL_33_DO"].map(order).astype(int)
    for coded, src in DATA_COLS[tag].items():
        col = pd.to_numeric(df[src], errors="coerce").astype("Int64")
        assert set(col.dropna()) <= set(range(1, 10)), (tag, src)
        out[coded] = col.values
    out = pd.concat([out, persona_cols(sv, df)], axis=1)
    return out.sort_values("pid").reset_index(drop=True)


def extract(tag: str) -> Path:
    """Write every decoded column of the .omv to omv/<name>.csv (the raw folder)."""
    EXTRACTED.mkdir(exist_ok=True)
    path = EXTRACTED / (Path(OMV[tag]).stem + ".csv")
    read_omv(OTHER / OMV[tag])[0].to_csv(path, index=False)
    return path


# ---------------------------------------------------------------------------
# The recipes
# ---------------------------------------------------------------------------


def _scale(sc: tuple[int, int, str, str]) -> dict[str, Any]:
    return {"min": sc[0], "max": sc[1], "min_label": sc[2], "max_label": sc[3]}


def recipe(e: Experiment) -> dict[str, Any]:
    arms = []
    for i, a in enumerate(e.arms):
        arm: dict[str, Any] = {
            "raw_values": a.raw,
            "condition_num": i,
            "factors": a.factors,
            "text": condition(a.screen, a.earlier),
        }
        items = {}
        for t, o in enumerate(e.outcomes):
            pages = a.item_pages.get(t, o.earlier)
            if pages:
                items[t] = {"condition_text": condition(a.screen, pages)}
        if items:
            arm["items"] = items
        arms.append(arm)
    notes = (
        f"{PAPER}\n\nGENERATED by scripts/gen_researchbox2170.py; every judgement is in its "
        f"docstring. {e.notes}\n\nWording from {QSF[e.tag][0]} (the fielded export; the "
        f"submission export {QSF[e.tag][1]} agrees on every question shown, see the "
        "docstring). Typography normalised (non-breaking spaces); line breaks kept as the "
        "screen had them. Added words (ours): 'You were then asked (the statements were shown "
        "in a random order):' and 'You were then asked:', each followed by the earlier "
        "page's lines in quotation marks. Persona: age (years; outside 18-100 left blank) and "
        "gender, labels from the .qsf's own choices."
    )
    return {
        "study_id": STUDY_ID,
        "source": "researchbox",
        "experiment": e.name,
        "title": e.title,
        "data_file": data_file(e.tag),
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": "pid",
        "notes": notes,
        "condition": {"source_vars": e.source_vars, "factors": e.factors, "arms": arms},
        "outcomes": [
            {"var": o.var, "task_num": t, "question": o.question, "scale": _scale(o.scale)}
            for t, o in enumerate(e.outcomes)
        ],
        "response_recode": {k: k for k in range(1, 10)},
        "missing_codes": [],
        "persona_map": {"age": "age", "gender": "gender"},
    }


def recipe_path(e: Experiment) -> Path:
    return RECIPES / f"{STUDY_ID}_{e.name}.yaml"


def render(e: Experiment) -> str:
    return yaml.safe_dump(recipe(e), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prep", action="store_true", help="decode the .omv files, code the data")
    ap.add_argument("--check", action="store_true", help="exit 1 if any recipe differs")
    args = ap.parse_args()
    if args.prep:
        for tag in QSF:
            print(f"wrote {extract(tag).relative_to(REPO)}")
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
