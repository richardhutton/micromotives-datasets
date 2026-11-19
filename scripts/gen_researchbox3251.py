#!/usr/bin/env python3
"""Write recipes/researchbox3251_*.yaml: conditional promotions (5 recipes).

Cheng A, Stadler Blank A (2025), "The Conditional-Promotion Paradox: When and Why Conditional
Promotions Decrease Total Sales of the Promoted Product", Journal of Marketing Research
62(3):526-542, doi:10.1177/00222437241309324 (the author accepted manuscript, with its Web
Appendix, is on UDSpace: https://udspace.udel.edu/handle/19716/36002). ResearchBox 3251 ("JMR
Conditional Promotions", https://researchbox.org/3251), read from its Zenodo copy. CC BY 4.0
("All content posted to ResearchBox is under a CC By 4.0 License", the box page). US samples
(Prolific and a university lab), 2020-2024; US dollars, gallons and miles kept as the source
has them.

Every judgement is here, in code, so the recipes can be re-derived and reviewed.

THE DESIGN. A conditional promotion is a discount that needs something first: spend more,
belong to a group, be a loyalty member, drive to a store. The paper's claim is that one the
customer cannot or will not meet can LOWER sales of the promoted product at its regular price.
The box holds 9 .qsf, 13 data files (.xlsx, one header row, no value labels), a codebook per
data file, 10 .docx survey printouts, SAS code per study and 7 AsPredicted pre-registrations.
The folders' names start with a space (" Data/", " Materials/", ...), kept as found.

WHAT IS BUILT. Five of the eleven data sets:
- study2 (Study 2, pants): a 2 (precondition cost: spend over $100 or $500 at Saks) x 2
  (discount 5% or 30%) + no-promotion control, between people; which pair would you lean
  towards, Saks's or an identical $60 pair at Nordstrom (1-7).
- study3 (Study 3, printers): promotion (the first printer is $45 instore, $90 online) or
  none, between people, crossed with the distance to the store (0, 30, 60 or 90 miles) within
  person, the four distances in a random order the deposit does not record; which of five
  options would you choose (nominal). One recipe, eight conditions, four outcomes, each
  naming its own assignment column (Outcome.condition_var), as researchbox1032 study1.
- wa_b2 (Web Appendix B2, a phone): 2 (precondition: add a phone line, about $1200, or switch
  to 5G, about $120) x 2 (discount to $300 or to $900), between people; what Phone X is worth
  to you, and what the average consumer spends on it (open-ended dollars).
- wa_b3 (Web Appendix B3, gasoline): a cash-only discount you cannot use, or no promotion;
  purchase intention, how good a deal, gallons, three reactance items, fairness and regret.
- wa_b4 (Web Appendix B4, headphones): twelve conditional promotions, every person rating
  every one (line-up) in a random order the deposit does not record; how difficult it is for
  you to qualify, and how willing you are to do what it takes.

NOT BUILT (NOT_BUILT), each with its reason:
- pilot: scraped Poshmark listings (5,040 sold bags, days to sale); no respondents.
- study1: a bakery's daily sales counts; no respondents.
- wa_a3 (Study 1 post-test, macarons): the fielded scenario shows a picture, IM_0okkvNz4oqWRPEi
  (the .docx embeds it as word/media/image1.png, 610 x 298), whose printed words ARE the
  promotion: "Tuesday's Special" and "$1 Macarons". rich's ruling (19 Nov 2026): skip any study
  where a picture carries the product, its price or the promotion terms.
- study4 (Study 4, hotels; dropped by main-session ruling, 19 Nov 2026, rich's standing rule
  to remove the riskiest part): people first choose the preferred of two hotels, and every
  later screen pipes that answer in ("You find that Hotel A currently offers ...", the 1-7
  scale running from the chosen hotel to the other). Its arms are therefore defined by the
  respondent's own earlier answer, and a row could only be written by narrating that answer
  ("... and chose Hotel A."), which CONVENTIONS forbids: earlier answers are narrated as
  asked, never as given. A first build did exactly that and reproduced the paper; it is not
  kept.
- wa_b1_mturk and wa_b1_student (Web Appendix B1, lay theories): no manipulation (one scenario
  for everyone, no randomiser in the flow) and the data's two columns, renamed inc and dec,
  cannot be tied to a fielded question from the deposit: the survey asks two near-identical
  matrices (Q1 "will sell more/fewer units", Q2 "will increase/decrease the store's sales"),
  and the codebook's "conditional promotion will increase sales of the promoted product" fits
  either. Only the paper's prose suggests Q2. Not a fabrication risk we take for a study with
  no contrast.

PICTURES (rich, 19 Nov 2026: skip a study whose condition-relevant content is in a picture;
list every picture judged decorative). The nine .qsf hold 25 <img> tags (asserted,
check_pictures): Study 4's 10 (one graphic, IM_516c0e8xDYAjYVg, a theatre seating chart) and
WA-B4's 12 (IM_6FCV7VsjIATsRal, IM_1TgjXM3XLzML2XH, IM_0eWRjlYW9njb9at, IM_dm61Mrqh0aM27LT,
IM_b29AsYeonXoB2pn: scarves and a gift box) all sit in blocks of type Trash, which no flow
reaches, so no respondent of these surveys saw them; WA-A3's 3 (one graphic) sit once in the
fielded scenario and twice in Trash, and WA-A3 is not built. So no BUILT study shows any
picture, and none needed to be judged decorative. One more picture exists outside the .qsf:
the WA-B3 printout's word/media/image1.png, 200 x 32, is the printout's drawing of the gallons
slider (a bar and a handle, no words), part of the answer format and not a stimulus.

THE WORDING. Every condition and question is the .qsf's, word-for-word, from the blocks the
survey flow reaches (Survey.fielded; the unbuilt Study 4's .qsf repeats the export tags ch2
and tu in Trash, so tags are looked up only among fielded blocks and asserted unique there). HTML is
reduced to paragraphs; bold, underline and colour are dropped; typography is normalised. The
data files carry names only, no labels, so "the fielded export" here is the column set:
- Study 2's .qsf asks "Given this situation, how likely are you to buy this pair of pants at
  Saks?" (saks) on the scenario's page, before the Nordstrom question; neither the data nor
  the .docx printout has it. Whether it was shown cannot be told from the deposit, so no row
  narrates it.
- The codebooks agree with the .qsf's codes, except Study 3's gender ("1 = male, 2 =
  female"), whose data also hold 3, 4 and 5; their labels come from the .qsf's RecodeValues
  (Transgender, Non-binary/non-conforming, Identity not listed).
- Where a pre-registration words an outcome differently, the fielded .qsf is used.
No words of ours are added to any condition.

SURVEY MECHANICS DROPPED. Consent and IRB screens, Prolific ids, "click next" screens, and
two introductions that describe the sequence: Study 3's ("You will compare 2 printers at a
time. You will compare 4 product pairs ...") and WA-B4's ("You will now see 12 different
conditional promotions in sequential order", after a definition of conditional promotions
and a free-text paraphrase of it). A row cannot say where it sat in a sequence (CONVENTIONS),
and with the order unrecorded each row carries its own screen only.

ORDER. Study 3's four distance blocks (BlockRandomizer SubSet 4) and WA-B4's twelve
promotion blocks (SubSet 12) were shown in a random order, recorded nowhere in the deposit
(no _DO column); each row carries its own block only. Everything else is in a fixed order.
WA-B3's purchase, deal and gallons questions share a page
before its reactance/fairness/regret page, and the later page's rows do not narrate the
earlier (narration is allowed for a fixed order, not required; nothing is asserted that was
not shown). WA-B2's two price questions share a page with an unbuilt rating (eval, not in
the data).

ATTENTION AND OPEN TEXT. Not built: WA-B2's paraphrase of the promotion, every "final
thoughts" box; manipulation checks (Study 2, WA-B3) are in Trash and
were not fielded.

EXCLUSIONS. Each authors' script keeps Finished = 1 ("if finished ne 1 then delete"), and so
do we: the paper's N then matches the deposit exactly (Study 2 501 of 509, Study 3 347 of 347,
WA-B2 400 of 421, WA-B3 200 of 202, WA-B4 210 of 219). WA-B2's authors
also drop one person whose second answer is $10,000 (beyond 3 SD); a real answer, we keep it,
and the test asserts the paper's numbers both with that one removed and the difference.

THE ASSIGNMENT. Each file has the assignment as the randomiser's embedded field (Study 2 qp,
Study 3 cond, WA-B2 cond, WA-B3 cond), checked against the flow's values; Study 3's piped
prices (pipea .. pipeg) are asserted to agree with cond person by person. WA-B4 has no assignment: everyone saw all twelve, so each outcome names a constant
column. Jev: scripts/recipe_prep.py reads .sav/.dta/.por only and this box has .xlsx, so it
does not apply (as for researchbox108); the assignment columns are named as such in the
codebooks ("condition type", "condition in text form").

PERSONA. Age and gender. Age: Studies 2 and 3, WA-B2 and WA-B3 pick from a list 18 ... "100+"
(recoded 100, asserted absent); WA-B4's list is 18, 19, 20, 21 and "22 or older", so the 16
people answering "22 or older" have no age (a band is not an age in years). Gender labels are
the .qsf's own choices through its RecodeValues (WA-B4 asks "What is your sex?": Male,
Female); "Prefer not to respond" leaves gender blank, and "Identity not listed, write in:"
reads "Identity not listed" (the write-in instruction dropped; the text written was not
deposited).

ANSWER KEY. The paper's own tables and text, recomputed from the BUILT rows by
tests/test_gen_researchbox3251.py: Study 2's five cell means and SDs and its F tests; Study
3's Table 4, all 40 counts; WA-B2's
discount means; WA-B3's eight means and SDs; WA-B4's twelve Figure W1 means.

    uv run python scripts/gen_researchbox3251.py --prep   # code the data
    uv run python scripts/gen_researchbox3251.py          # write the recipes
    uv run python scripts/gen_researchbox3251.py --check  # exit 1 if any recipe differs
"""

from __future__ import annotations

import argparse
import html
import json
import re
import warnings
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

warnings.filterwarnings("ignore", message="Workbook contains no default style")

REPO = Path(__file__).resolve().parents[1]
STUDY_ID = "researchbox3251"
RAW = REPO / "data" / "raw" / STUDY_ID
MATERIALS = RAW / " Materials"
DATA = RAW / " Data"
CODEBOOK = RAW / " Codebook"
RECIPES = REPO / "recipes"
LICENCE = (
    'CC BY 4.0, stated on the box page https://researchbox.org/3251 ("All content posted '
    'to ResearchBox is under a CC By 4.0 License"); read from its Zenodo copy. Read 19 Nov '
    "2026."
)
PAPER = (
    'Cheng A, Stadler Blank A (2025), "The Conditional-Promotion Paradox: When and Why '
    'Conditional Promotions Decrease Total Sales of the Promoted Product", Journal of '
    "Marketing Research 62(3):526-542, doi:10.1177/00222437241309324. ResearchBox 3251 "
    "(https://researchbox.org/3251)."
)

# tag -> (.qsf, data file, the paper's name for it, pre-registration)
SOURCES = {
    "study2": (
        "Study 2_Qualtrics survey.qsf",
        "Study 2_Qualtrics data_ResearchBox.xlsx",
        "Study 2",
        "AsPredicted #178590",
    ),
    "study3": (
        "Study 3_Qualtrics survey.qsf",
        "Study 3_Qualtrics data_ResearchBox.xlsx",
        "Study 3",
        "AsPredicted #106746",
    ),
    "wa_b2": (
        "WA-B2_Qualtrics survey.qsf",
        "WA-B2_Qualtrics data_ResearchBox.xlsx",
        "Web Appendix B2",
        "AsPredicted #148886",
    ),
    "wa_b3": (
        "WA-B3_Qualtrics survey.qsf",
        "WA-B3_Qualtrics data_ResearchBox.xlsx",
        "Web Appendix B3",
        "AsPredicted #182519",
    ),
    "wa_b4": (
        "WA-B4_Qualtrics survey.qsf",
        "WA-B4_Qualtrics data_Researchbox.xlsx",
        "Web Appendix B4",
        "not pre-registered",
    ),
}

NOT_BUILT = {
    "pilot": "scraped Poshmark listings (days to sale); no respondents",
    "study1": "a bakery's daily sales counts; no respondents",
    "study4": (
        "its arms are defined by the respondent's own first answer (the preferred hotel), "
        "piped into every later screen; a row would have to narrate that answer as given"
    ),
    "wa_a3": (
        'the fielded scenario\'s picture prints the promotion ("Tuesday\'s Special", "$1 Macarons")'
    ),
    "wa_b1_mturk": (
        "no manipulation, and the exported inc/dec columns cannot be tied to one of the two "
        "near-identical fielded matrices"
    ),
    "wa_b1_student": (
        "no manipulation, and the exported inc/dec columns cannot be tied to one of the two "
        "near-identical fielded matrices"
    ),
}

# people kept (Finished = 1), as the paper reports them
N = {"study2": 501, "study3": 347, "wa_b2": 400, "wa_b3": 200, "wa_b4": 210}

# every <img> tag in every .qsf: file -> (fielded, in Trash)
PICTURES = {
    "Study 2_Qualtrics survey.qsf": (0, 0),
    "Study 3_Qualtrics survey.qsf": (0, 0),
    "Study 4_Qualtrics survey.qsf": (0, 10),
    "WA-A3_Qualtrics survey.qsf": (1, 2),
    "WA-B1 MTurk_Qualtrics survey.qsf": (0, 0),
    "WA-B1 Student_Qualtrics survey.qsf": (0, 0),
    "WA-B2_Qualtrics survey.qsf": (0, 0),
    "WA-B3_Qualtrics survey.qsf": (0, 0),
    "WA-B4_Qualtrics survey.qsf": (0, 12),
}

# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

_TYPO = {"\xa0": " ", "\u200b": "", "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"'}


def _clean(s: str) -> str:
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    for a, b in _TYPO.items():
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def norm(raw: str) -> str:
    """HTML to one line of plain text. Typography only."""
    return _clean(re.sub(r"<br\s*/?>|</p>|</div>", " ", raw or ""))


def paragraphs(raw: str) -> str:
    """HTML to paragraphs, blank-line separated, empty ones dropped."""
    parts = re.split(r"<br\s*/?>|</p>|</div>|<div>|<p>", raw or "")
    return "\n\n".join(c for c in (_clean(p) for p in parts) if c)


def label(raw: str, code: int) -> str:
    """An answer label without the scale number printed beneath it ("very unwilling<br>1")."""
    s = norm(raw)
    if s == str(code):
        return ""
    return s[: -len(str(code))].strip() if s.endswith(f" {code}") else s


# ---------------------------------------------------------------------------
# The questionnaires
# ---------------------------------------------------------------------------


def qsf_path(tag: str) -> Path:
    return MATERIALS / SOURCES[tag][0]


class Survey:
    def __init__(self, path: Path) -> None:
        els = json.loads(path.read_text())["SurveyElements"]
        self.by_qid: dict[str, dict[str, Any]] = {
            e["Payload"]["QuestionID"]: e["Payload"] for e in els if e["Element"] == "SQ"
        }
        self.blocks: dict[str, dict[str, Any]] = {}
        for e in els:
            if e["Element"] == "BL":
                p = e["Payload"]
                for b in p.values() if isinstance(p, dict) else p:
                    self.blocks[b["ID"]] = b
        self.flow: dict[str, Any] = next(e for e in els if e["Element"] == "FL")["Payload"]
        self.flow_blocks: list[str] = []
        self.randomizers: list[dict[str, Any]] = []
        self.embedded: list[list[tuple[str, str]]] = []

        def walk(n: dict[str, Any]) -> None:
            if n.get("Type") in ("Block", "Standard"):
                self.flow_blocks.append(n["ID"])
            if n.get("Type") == "BlockRandomizer":
                self.randomizers.append(n)
            for c in n.get("Flow", []):
                walk(c)

        walk(self.flow)
        assert all(self.blocks[b]["Type"] != "Trash" for b in self.flow_blocks)
        self.qs: dict[str, dict[str, Any]] = {}
        for b in self.flow_blocks:
            for x in self.blocks[b].get("BlockElements", []):
                if x["Type"] == "Question":
                    q = self.by_qid[x["QuestionID"]]
                    if q["QuestionType"] in ("DB", "Timing") and q["DataExportTag"] in (
                        "time",
                        "next",
                    ):
                        continue  # page timers and "click next" screens, repeated by design
                    assert q["DataExportTag"] not in self.qs, q["DataExportTag"]
                    self.qs[q["DataExportTag"]] = q

    def text(self, tag: str) -> str:
        return paragraphs(self.qs[tag]["QuestionText"])

    def block_tags(self, block_id: str) -> list[str]:
        return [
            self.by_qid[x["QuestionID"]]["DataExportTag"] if x["Type"] == "Question" else x["Type"]
            for x in self.blocks[block_id]["BlockElements"]
        ]

    def block_named(self, name: str) -> str:
        (b,) = [b for b in self.flow_blocks if self.blocks[b]["Description"].strip() == name]
        return b

    def assignment(self) -> list[dict[str, str]]:
        """The one SubSet-1 randomiser's embedded-data settings, in flow order."""
        (r,) = [r for r in self.randomizers if int(r["SubSet"]) == 1]
        out = []
        for n in r["Flow"]:
            assert n["Type"] == "EmbeddedData"
            out.append({x["Field"]: str(x["Value"]) for x in n["EmbeddedData"]})
        return out


@cache
def survey(tag: str) -> Survey:
    return Survey(qsf_path(tag))


def codes(q: dict[str, Any]) -> list[tuple[int, str]]:
    """A single-answer question's (code, label) pairs in ChoiceOrder, codes recoded."""
    recode = q.get("RecodeValues") or {}
    order = [str(k) for k in q["ChoiceOrder"]]
    return [(int(recode.get(k, k)), q["Choices"][k]["Display"]) for k in order]


def mc_scale(q: dict[str, Any]) -> dict[str, Any]:
    """A 1..k single-answer scale: labels at the ends, and at the middle if it has one."""
    assert q["QuestionType"] == "MC" and q["Selector"] in ("SAVR", "SAHR")
    assert not q.get("Randomization")
    cs = codes(q)
    assert [c for c, _ in cs] == list(range(1, len(cs) + 1)), cs
    labs = [label(raw, c) for c, raw in cs]
    sc: dict[str, Any] = {"min": 1, "max": len(cs), "min_label": labs[0], "max_label": labs[-1]}
    mid = len(cs) // 2
    if len(cs) % 2 and labs[mid] and labs[mid] != str(mid + 1):
        sc["mid_label"] = labs[mid]
    return sc


def likert(q: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """A Likert matrix: its scale, and its statements by export column."""
    assert q["QuestionType"] == "Matrix" and q["Selector"] == "Likert"
    recode = q.get("RecodeValues") or {}
    order = [str(k) for k in q["AnswerOrder"]]
    vals = [int(recode.get(k, k)) for k in order]
    assert vals == list(range(1, len(order) + 1)), vals
    labs = [label(q["Answers"][k]["Display"], v) for k, v in zip(order, vals, strict=True)]
    assert all(x == "" for x in labs[1:-1]), labs
    sc = {"min": 1, "max": len(order), "min_label": labs[0], "max_label": labs[-1]}
    tags = q["ChoiceDataExportTags"]
    items = {tags[str(k)]: norm(q["Choices"][str(k)]["Display"]) for k in q["ChoiceOrder"]}
    return sc, items


def nominal(q: dict[str, Any], pipe: dict[str, str]) -> tuple[dict[str, Any], str]:
    """A pick among options: a nominal scale and the options enumerated, pipes filled."""
    assert q["QuestionType"] == "MC" and q["Selector"] == "SAVR" and not q.get("Randomization")
    cs = codes(q)
    assert [c for c, _ in cs] == list(range(1, len(cs) + 1)), cs
    opts = "; ".join(f'{c} means "{fill(norm(raw), pipe)}"' for c, raw in cs)
    return {"min": 1, "max": len(cs), "nominal": True}, opts


def fill(text: str, pipe: dict[str, str]) -> str:
    """Replace each Qualtrics pipe with its value; fail on any left."""
    for k, v in pipe.items():
        text = text.replace(k, v)
    assert "${" not in text, text
    return text


def gender_labels(q: dict[str, Any]) -> dict[int, str | None]:
    """Code -> label from the .qsf; a refusal is blank; the write-in prompt is dropped."""
    out: dict[int, str | None] = {}
    for c, raw in codes(q):
        s = norm(raw)
        if s.startswith("Prefer not to"):
            out[c] = None
        else:
            out[c] = re.sub(r",? \(?write in\)?:?$", "", s)
    return out


def age_codes(q: dict[str, Any]) -> dict[int, int | None]:
    """Recoded value -> age in years; a band ("22 or older", "100+") has none."""
    out: dict[int, int | None] = {}
    for c, raw in codes(q):
        s = norm(raw)
        out[c] = int(s) if s.isdigit() else None
    return out


def check_pictures() -> None:
    """Every <img> tag in every .qsf, split by whether a fielded block holds it."""
    for name, (fielded, trash) in PICTURES.items():
        sv = Survey(MATERIALS / name)
        reach = {
            x["QuestionID"]
            for b in sv.flow_blocks
            for x in sv.blocks[b].get("BlockElements", [])
            if x["Type"] == "Question"
        }
        got = [0, 0]
        for qid, q in sv.by_qid.items():
            n = len(re.findall(r"<img", json.dumps(q)))
            got[0 if qid in reach else 1] += n
        assert tuple(got) == (fielded, trash), (name, got)
        raw = (MATERIALS / name).read_text()
        assert raw.count("<img") == fielded + trash, name
    assert sum(f + t for f, t in PICTURES.values()) == 25


# ---------------------------------------------------------------------------
# The experiments
# ---------------------------------------------------------------------------


@dataclass
class Arm:
    raw: dict[str, int]
    factors: dict[str, str]
    text: str
    items: dict[int, dict[str, Any]] = field(default_factory=dict)


@dataclass
class Outcome:
    var: str
    question: str
    scale: dict[str, Any]
    condition_var: str | None = None


@dataclass
class Experiment:
    name: str
    title: str
    kind: str
    factors: list[str]
    source_vars: list[str]
    shared: str
    arms: list[Arm]
    outcomes: list[Outcome]
    notes: str


def study2() -> Experiment:
    sv = survey("study2")
    assign = sv.assignment()
    assert [a["qp"] for a in assign] == ["qlpl", "qlph", "qhpl", "qhph", "cg"]
    block = sv.block_named("Scenarios and DVs")
    assert sv.block_tags(block) == [
        "scen",
        "lowlow",
        "lowhigh",
        "highlow",
        "highhigh",
        "cg",
        "saks",
        "Page Break",
        "sub",
    ]
    cells = [
        ("lowlow", "low", "low"),
        ("lowhigh", "low", "high"),
        ("highlow", "high", "low"),
        ("highhigh", "high", "high"),
        ("cg", "none", "none"),
    ]
    arms = [
        Arm({"qp": i + 1}, {"precondition_cost": qty, "discount": pct}, sv.text(t))
        for i, (t, qty, pct) in enumerate(cells)
    ]
    q = sv.qs["sub"]
    sc = mc_scale(q)
    assert (sc["min_label"], sc["max_label"]) == ("The pair from Saks", "The pair from Nordstrom")
    return Experiment(
        name="study2",
        title="Pants at Saks for $60, with a spend-over-$100 or over-$500 promotion giving 5% "
        "or 30% off, or no promotion; Saks's pair or the same at Nordstrom? (Study 2)",
        kind="mix",
        factors=["precondition_cost", "discount"],
        source_vars=["qp"],
        shared=sv.text("scen"),
        arms=arms,
        outcomes=[Outcome("sub", sv.text("sub"), sc)],
        notes=(
            "2 (precondition cost: spend over $100, i.e. $40 more, or over $500) x 2 "
            "(discount 5% or 30% off the cart) + a no-promotion control, between people. "
            "The question (sub, its own page) names Nordstrom's $60 pair; 1 = The pair from "
            "Saks, 7 = The pair from Nordstrom, as answered (the paper reverse-codes it). The "
            ".qsf also places a Saks purchase-likelihood question (saks) on the scenario's "
            "page; neither the data nor the .docx printout has it, so no row narrates it. "
            'The highhigh arm\'s own wording is kept: "You need to spend $440 to qualify!" '
            '(the others: "$440 more" / "$40 more").'
        ),
    )


DISTANCES = (0, 30, 60, 90)
PRINTERS = {0: "a", 30: "c", 60: "e", 90: "g"}


def study3() -> Experiment:
    sv = survey("study3")
    assign = sv.assignment()
    assert assign == [
        {"cond": c, **{f"pipe{p}": v for p in "aceg"}} for c, v in (("cg", "90"), ("pr", "45"))
    ]
    (order,) = [r for r in sv.randomizers if int(r["SubSet"]) == 4]
    names = [sv.blocks[b["ID"]]["Description"] for b in order["Flow"]]
    assert names == [f"{d} miles" for d in DISTANCES], names
    shared = "Imagine that you are shopping for a new color printer."
    arms, outcomes = [], []
    for t, d in enumerate(DISTANCES):
        assert sv.block_tags(sv.block_named(f"{d} miles")) == [f"cg{d}", f"pr{d}", f"ch{d}"]
        q = sv.qs[f"ch{d}"]
        assert q["Validation"]["Settings"]["ForceResponse"] == "ON"
        sc = None
        for code, (cond, price, promo) in enumerate(
            (("cg", "90", "none"), ("pr", "45", "conditional")), 1
        ):
            text = sv.text(f"{cond}{d}")
            assert text.startswith(shared + "\n\n"), text
            sc, opts = nominal(q, {f"${{e://Field/pipe{PRINTERS[d]}}}": price})
            question = f"{norm(q['QuestionText'])} {opts}."
            arms.append(
                Arm(
                    {"arm_0": 2 * t + code},
                    {"promotion": promo, "distance": f"{d}_miles"},
                    text[len(shared) + 2 :],
                    {t: {"outcome_question": question}},
                )
            )
        assert sc is not None
        outcomes.append(Outcome(f"ch{d}", arms[-2].items[t]["outcome_question"], sc, f"arm_{d}"))
    return Experiment(
        name="study3",
        title="Two $90 printers, the first $45 instore under a conditional promotion or no "
        "promotion, the store 0, 30, 60 or 90 miles away: which option? (Study 3)",
        kind="mix",
        factors=["promotion", "distance"],
        source_vars=["arm_0"],
        shared=shared,
        arms=arms,
        outcomes=outcomes,
        notes=(
            "Promotion (the first printer $45 instore, $90 online) or none, between people "
            "(cond), crossed with the store's distance within person: everyone saw four "
            "blocks, 0, 30, 60 and 90 miles, each with its own pair of printers (A/B, C/D, "
            "E/F, G/H), in a random order the deposit does not record (BlockRandomizer, "
            "SubSet 4, no _DO column). So each row carries its own block only, and each "
            "outcome names its own assignment column (arm_0 .. arm_90: 1 no promotion, 2 "
            "promotion). The options are listed in the .qsf's fixed order with the piped "
            "instore price filled ($90 or $45, the embedded pipea .. pipeg, asserted to "
            "agree with cond); nominal, as answered. Not built: the introduction, which "
            'describes the sequence ("You will compare 4 product pairs").'
        ),
    )


def wa_b2() -> Experiment:
    sv = survey("wa_b2")
    assert [a["cond"] for a in sv.assignment()] == ["highhigh", "highlow", "lowhigh", "lowlow"]
    assert sv.block_tags(sv.block_named("Manipulations")) == [
        "time",
        "scen",
        "highhigh",
        "highlow",
        "lowhigh",
        "lowlow",
        "tho",
    ]
    assert sv.block_tags(sv.block_named("DVs")) == ["eval", "ref1", "ref2"]
    cells = [
        ("highhigh", "add_a_line", "70_percent"),
        ("highlow", "add_a_line", "10_percent"),
        ("lowhigh", "switch_to_5g", "70_percent"),
        ("lowlow", "switch_to_5g", "10_percent"),
    ]
    arms = [
        Arm({"cond": i + 1}, {"precondition": pre, "discount": dis}, sv.text(c))
        for i, (c, pre, dis) in enumerate(cells)
    ]
    for q in ("ref1", "ref2"):
        assert sv.qs[q]["QuestionType"] == "TE"
        assert not (sv.qs[q].get("Validation") or {}).get("Settings", {}).get("ContentType")
    sc = {"min": 0, "max": REF_MAX}
    return Experiment(
        name="wa_b2",
        title="Phone X, regular price $1000, for $300 or $900 if you add a phone line (about "
        "$1200 over two years) or switch to 5G (about $120): what is it worth? (Web "
        "Appendix B2)",
        kind="mix",
        factors=["precondition", "discount"],
        source_vars=["cond"],
        shared=sv.text("scen"),
        arms=arms,
        outcomes=[Outcome("ref1", sv.text("ref1"), sc), Outcome("ref2", sv.text("ref2"), sc)],
        notes=(
            "2 (precondition: add an additional phone line, about $1200 over two years, or "
            "switch to 5G, about $120) x 2 (Phone X for $300, 70% off, or $900, 10% off), "
            "between people. Two open-ended dollar answers on one page (also on it, an "
            "unbuilt rating not in the data): what Phone X is worth to you, and what the "
            "average consumer spends to buy it. The box takes any text (no validation), so "
            f"the scale states 0 to the largest answer given, {REF_MAX:,}; whole dollars as "
            "typed (every kept answer is a whole number, asserted). The authors drop one person "
            "beyond 3 SD (a second answer of $10,000); we keep them. Not built: a typed "
            "paraphrase of the promotion on the scenario page (an attention check)."
        ),
    )


REF_MAX = 10000


def wa_b3() -> Experiment:
    sv = survey("wa_b3")
    assert [a["cond"] for a in sv.assignment()] == ["cg", "pr"]
    assert sv.block_tags(sv.block_named("Manipulation")) == ["scen", "scenpr"]
    assert sv.block_tags(sv.block_named("DVs and mediation")) == [
        "dvs",
        "extent",
        "Page Break",
        "react",
    ]
    dv_sc, dv_items = likert(sv.qs["dvs"])
    re_sc, re_items = likert(sv.qs["react"])
    assert list(dv_items) == ["purch", "tu"]
    assert list(re_items) == ["react1", "react2", "react3", "fair", "regret"]
    ext = sv.qs["extent"]
    c = ext["Configuration"]
    assert (c["CSSliderMin"], c["CSSliderMax"], c["NumDecimals"]) == (0, 20, "0")
    assert norm(ext["Choices"]["1"]["Display"]) == "gallons"
    outcomes = [Outcome(v, f"{sv.text('dvs')} {s}", dv_sc) for v, s in dv_items.items()]
    outcomes.append(Outcome("extent", sv.text("extent"), {"min": 0, "max": 20}))
    outcomes += [Outcome(v, f"{sv.text('react')} {s}", re_sc) for v, s in re_items.items()]
    return Experiment(
        name="wa_b3",
        title="A gas station at $3.50/gallon, with a $2.50 cash price you cannot use or no "
        "promotion: fill up here, a good deal, how many gallons, fair, regret? (Web Appendix "
        "B3)",
        kind="version",
        factors=["promotion"],
        source_vars=["cond"],
        shared=sv.text("scen"),
        arms=[
            Arm({"cond": 1}, {"promotion": "none"}, ""),
            Arm({"cond": 2}, {"promotion": "cash_only"}, sv.text("scenpr")),
        ],
        outcomes=outcomes,
        notes=(
            "Two arms between people: no promotion (the scenario alone), or a promotion "
            "for customers paying in cash, $2.50/gallon, when you have no cash (the screen's "
            'own words, "Unfortunately, do not have any cash on you!", kept). Next page: '
            "agreement that you will likely fill up here and that $3.50/gallon is a good deal "
            "(1 not at all, 7 extremely) and how many gallons (a 0-20 slider, whole gallons; "
            'its one row is labelled "gallons", the unit the question names). Next page, fixed '
            "order: three reactance items, fairness and regret, the same scale; those rows do "
            "not narrate the earlier page."
        ),
    )


# WA-B4: block description -> (factor level, data prefix of the two outcome columns)
WA_B4 = {
    "loyalty": ("loyalty", "loyal"),
    "additional purchase": ("additional_purchase", "addl"),
    "referral": ("referral", "ref"),
    "minimum dollar": ("minimum_dollar", "dol"),
    "senior citizen": ("senior_citizen", "sr"),
    "student": ("student", "st"),
    "mother": ("mother", "mom"),
    "veteran": ("veteran", "vet"),
    "minimum quantity": ("minimum_quantity", "qty"),
    "happy hour": ("happy_hour", "hh"),
    "flash sale": ("flash_sale", "fl"),
    "geography": ("geography", "geo"),
}
DIFFICULTY = "How difficult or easy is it for you personally to qualify for this discount?"


def wa_b4() -> Experiment:
    sv = survey("wa_b4")
    (r,) = sv.randomizers
    assert int(r["SubSet"]) == 12
    names = [sv.blocks[b["ID"]]["Description"].strip() for b in r["Flow"]]
    assert names == list(WA_B4), names
    shared = "Imagine that you're interested in purchasing a pair of noise cancelling headphones from Firm A that cost $179.99."
    arms, outcomes = [], []
    for k, name in enumerate(WA_B4):
        lvl, pre = WA_B4[name]
        tags = sv.block_tags(sv.block_named(name))
        scen = tags[0]
        assert tags[1:3] == [f"{pre}1", f"{pre}2"], (name, tags)
        text = sv.text(scen)
        assert text.startswith(shared + "\n\n"), text
        arms.append(Arm({"arm_loyal": k + 1}, {"precondition": lvl}, text[len(shared) + 2 :]))
        d, w = sv.qs[f"{pre}1"], sv.qs[f"{pre}2"]
        assert norm(d["QuestionText"]) == DIFFICULTY, name
        assert norm(w["QuestionText"]).startswith(
            "How willing are you to do what it takes to qualify for this discount?"
        ), name
        for q in (d, w):
            assert q["Validation"]["Settings"]["ForceResponse"] == "ON", name
        outcomes.append(Outcome(f"{pre}1", norm(d["QuestionText"]), mc_scale(d), f"arm_{pre}"))
        outcomes.append(Outcome(f"{pre}2", norm(w["QuestionText"]), mc_scale(w), f"arm_{pre}"))
    return Experiment(
        name="wa_b4",
        title="Headphones at $179.99, 30% off if you meet one of twelve conditions (be a "
        "student, a veteran, a senior citizen, spend $200, refer two people ...): how hard is "
        "it for you, and how willing are you? (Web Appendix B4)",
        kind="lineup",
        factors=["precondition"],
        source_vars=["arm_loyal"],
        shared=shared,
        arms=arms,
        outcomes=outcomes,
        notes=(
            "Twelve conditional promotions on the same headphones, each a 30% discount with "
            "its own condition; every person saw all twelve, each on its own page, in a "
            "random order the deposit does not record (BlockRandomizer, SubSet 12, no _DO "
            "column), so each row carries its own promotion only and each outcome names a "
            "constant column (arm_loyal .. arm_geo). Per promotion: how difficult or easy it "
            "is for you personally to qualify (1 Extremely difficult, 4 Neither difficult nor "
            "easy, 7 Extremely easy; the other labels are not carried) and how willing you "
            "are to do what it takes, each with the block's own parenthesis (1 very "
            "unwilling, 7 very willing). Not built: four further questions per block (take "
            "advantage, deal, fairness, a Firm B alternative) that the data do not carry. A "
            'university lab sample; persona sex as asked; age is 18-21 or "22 or older", '
            "the latter left blank."
        ),
    )


def experiments() -> list[Experiment]:
    return [study2(), study3(), wa_b2(), wa_b3(), wa_b4()]


def experiment(tag: str) -> Experiment:
    (e,) = [x for x in experiments() if x.name == tag]
    return e


# ---------------------------------------------------------------------------
# Coded data
# ---------------------------------------------------------------------------


def data_file(tag: str) -> str:
    return f"{STUDY_ID}_{tag}.csv"


def read_deposit(tag: str) -> pd.DataFrame:
    return pd.read_excel(DATA / SOURCES[tag][1])


def kept(tag: str) -> pd.DataFrame:
    """The deposit's rows the authors analyse: Finished = 1."""
    df = read_deposit(tag)
    df = df[df["Finished"] == 1].reset_index(drop=True)
    assert len(df) == N[tag], (tag, len(df))
    assert df["ResponseId"].is_unique
    return df


# WA-B4 asks "What is your sex?" (Male, Female); every other study asks for gender.
SEX_OR_GENDER = {t: "sex" if t == "wa_b4" else "gender" for t in SOURCES}


def persona(tag: str, df: pd.DataFrame) -> tuple[list[Any], list[Any]]:
    sv = survey(tag)
    gq = sv.qs["sex" if "sex" in sv.qs else "gender"]
    assert norm(gq["QuestionText"]).startswith(
        "What is your sex?" if tag == "wa_b4" else ("Please indicate", "What is your gender")
    ), tag
    gcol = "sex" if "sex" in df.columns else "gender"
    glab = gender_labels(gq)
    gender = [glab[int(g)] if pd.notna(g) else None for g in df[gcol]]
    ages = age_codes(sv.qs["age"])
    if tag != "wa_b4":
        assert not (df["age"] == 100).any()  # "100+"
    age = [ages[int(a)] if pd.notna(a) else None for a in df["age"]]
    return age, gender


def answers(s: pd.Series, lo: int, hi: int) -> pd.Series:
    v = pd.to_numeric(s, errors="raise")
    assert (v.dropna() % 1 == 0).all()
    assert v.dropna().between(lo, hi).all()
    return v.astype("Int64")


def prep(tag: str) -> pd.DataFrame:
    """One coded row per kept person: assignment column(s), answers, age, gender."""
    e = experiment(tag)
    df = kept(tag)
    out = pd.DataFrame({"pid": [f"{tag}_{r}" for r in df["ResponseId"]]})
    if tag == "study2":
        order = ["qlpl", "qlph", "qhpl", "qhph", "cg"]
        want = [
            "cg" if (q, c) == ("cg", "cg") else f"q{q[0]}p{c[0]}"
            for q, c in zip(df["qty"], df["pct"], strict=True)
        ]
        assert list(df["qp"]) == want  # the merged field agrees with its two parts
        out["qp"] = df["qp"].map({k: i + 1 for i, k in enumerate(order)}).values
    elif tag == "study3":
        price = {"cg": 90, "pr": 45}
        for p in "aceg":
            assert (df[f"pipe{p}"] == df["cond"].map(price)).all()
        for d in DISTANCES:
            t = DISTANCES.index(d)
            out[f"arm_{d}"] = df["cond"].map({"cg": 2 * t + 1, "pr": 2 * t + 2}).values
    elif tag == "wa_b2":
        out["cond"] = (
            df["cond"].map({"highhigh": 1, "highlow": 2, "lowhigh": 3, "lowlow": 4}).values
        )
    elif tag == "wa_b3":
        out["cond"] = df["cond"].map({"cg": 1, "pr": 2}).values
    elif tag == "wa_b4":
        for k, (_, pre) in enumerate(WA_B4.values()):
            out[f"arm_{pre}"] = k + 1
    for v in e.source_vars + [o.condition_var for o in e.outcomes if o.condition_var]:
        assert out[v].notna().all(), (tag, v)
    for o in e.outcomes:
        out[o.var] = answers(df[o.var], o.scale["min"], o.scale["max"]).values
    age, gender = persona(tag, df)
    out["age"] = pd.Series(age, dtype="Int64").values
    out[SEX_OR_GENDER[tag]] = gender
    return out


def check_codebook(tag: str) -> None:
    """The codebook lists the data file's columns, in order."""
    book = pd.read_csv(CODEBOOK / f"{SOURCES[tag][1]}___CODEBOOK.csv")
    assert list(book["varname"]) == list(read_deposit(tag).columns), tag


# ---------------------------------------------------------------------------
# The recipes
# ---------------------------------------------------------------------------


def recipe(e: Experiment) -> dict[str, Any]:
    arms = []
    for i, a in enumerate(e.arms):
        arm: dict[str, Any] = {
            "raw_values": a.raw,
            "condition_num": i,
            "factors": a.factors,
            "text": a.text,
        }
        if a.items:
            arm["items"] = {k: a.items[k] for k in sorted(a.items)}
        arms.append(arm)
    outcomes = []
    for t, o in enumerate(e.outcomes):
        out: dict[str, Any] = {"var": o.var, "task_num": t, "question": o.question}
        out["scale"] = o.scale
        if o.condition_var:
            out["condition_var"] = o.condition_var
        outcomes.append(out)
    lo = min(o.scale["min"] for o in e.outcomes)
    hi = max(o.scale["max"] for o in e.outcomes)
    qsf, data, name, prereg = SOURCES[e.name]
    notes = (
        f"{PAPER}\n\nGENERATED by scripts/gen_researchbox3251.py; every judgement is in its "
        f"docstring. {name} ({prereg}), {N[e.name]:,} people: the data file's Finished = 1 "
        f"rows, as the authors' script keeps and the paper reports. {e.notes}\n\nWording "
        f"from {qsf} (the blocks the survey flow reaches), word-for-word: the scenario is "
        "the condition, each question the outcome. Typography normalised (HTML, non-breaking "
        "spaces, curly quotes); emphasis dropped. "
        + "No words added. "
        + f"Data: {data}. Persona: age (years, from the .qsf's list; a band such as \"22 "
        "or older\" left blank) and gender (WA-B4: sex, as it asks), labels from the .qsf's "
        'own choices, "Prefer not to respond" left blank and ", write in:" dropped from '
        '"Identity not listed".'
    )
    cond: dict[str, Any] = {"source_vars": e.source_vars}
    if e.shared:
        cond["shared_context"] = e.shared
    cond["factors"] = e.factors
    cond["arms"] = arms
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
        "condition": cond,
        "outcomes": outcomes,
        "response_recode": {k: k for k in range(lo, hi + 1)},
        "missing_codes": [],
        "persona_map": {"age": "age", SEX_OR_GENDER[e.name]: SEX_OR_GENDER[e.name]},
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
        check_pictures()
        for tag in SOURCES:
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
