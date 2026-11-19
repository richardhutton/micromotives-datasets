#!/usr/bin/env python3
"""Write recipes/researchbox2562_*.yaml: the skimpflation penalty (11 recipes).

Evangelidis I (2026), "Skimpflation Penalty: Decreases in Product Quality Trigger Stronger
Consumer Reactions than Decreases in Size or Increases in Price", Journal of Consumer
Research, doi:10.1093/jcr/ucag019 (the box page). ResearchBox 2562 ("Skimpflation Penalty",
https://researchbox.org/2562), archived as Zenodo doi:10.5281/zenodo.20808095. CC BY 4.0
("All content posted to ResearchBox is under a CC By 4.0 License", the box page). Prolific
samples (every pre-registration but Study 6's) and, for Study 6, a university behavioural
lab paid in euros (its two pre-registrations); US and European prices, kept as the source
has them. Study 7's detergent is "British" and priced in pounds.

Every judgement is here, in code, so the recipes can be re-derived and reviewed.

THE DESIGN. A firm facing higher costs raises the price, shrinks the product, or cuts its
quality (less cocoa, less olive oil, less orange juice, thinner toilet paper, a weaker
detergent). People say whether the change is fair or unfair, how likely they are to buy,
how big the change is, or which of the three they would take. One .qsf, one .sav, one R
script and one AsPredicted pre-registration per study (Study 6 has two); fourteen studies.

WHAT IS BUILT. Eleven of the fourteen (5a, 5b and 5c are NOT_BUILT; see PICTURES):
- study1: chocolate or a streaming platform x price, size or quality (2 x 3, between).
- study2a: olive spread, price, size or olive-oil share x the firm states the change on the
  packaging or not (3 x 2).
- study2b: orange juice, price, size or juice concentration x no communication, the
  manufacturer on the packaging, or the retailer on the shelf (3 x 3).
- study3: toilet paper, price, package size, paper quality or packaging quality (4 arms).
- study4: orange juice, each change by 10% x costs up 10%, 5% or 15% (3 x 3).
- study4_followup: orange juice, each change by 10%; how big is the change, 0-100 slider.
- NOT BUILT: study5a / study5b, chocolate (5%) / olive spread (15%), three changes, fair or
  unfair AND how likely to buy; study5c, olive spread (15%), how likely to buy only.
- study6: a lab sample choosing, for real, between a price rise, a smaller size and a
  lower-cocoa (then lower-juice) product; each choice followed by a quality rating.
- study7: a British detergent, price, size, or a weaker formula whose loss can or cannot be
  made up by using more; would you buy it, and (quality arms) how good is the new one.
- study2a_pilot, study2b_pilot, study5a_pilot: 50 people each, everyone shown the same
  quality cut (olive oil, orange juice, cocoa) and asked how it changes the product's
  quality, 1-9. Real Prolific samples on their own fielded, pre-registered .qsf (AsPredicted
  217313, 217885, 217546), so built, as single-condition experiments (kind baseline).

KINDS (against data/catalog/design_kinds.json). Studies 1, 2a, 2b, 4: mix (factorial).
Studies 3, 4 follow-up, 7: version. Pilots: baseline. Study 6: shelf, not
head_to_head and not priority. Nothing in it is randomised; everyone faces three fixed
options AT ONCE and picks one, for real (five winners get the product), which is shelf's
"what people pick when they face many options at once, as they would in a shop".
head_to_head is paired comparison ranking a long list, and priority (MaxDiff) a best/worst
over a long list; neither describes one pick from three.

THE ASSIGNMENT. No data file has an assignment column: each arm's question is its own
column, blank for people not shown it. Every fairness, purchase and buy question is
ForceResponse ON in the .qsf (asserted), so a blank means "not shown"; `prep` derives the
arm from which column is filled and asserts exactly one is. The R scripts derive their
dummies the same way. The 4 follow-up sliders are ForceResponse OFF and one of its 301
people moved none of them, so their arm cannot be known and they are dropped (declared,
asserted: 300 kept; the R script gives that person no condition either). Each coded file
gives each person an id from their row in the deposit ("study1_17"). Jev
(scripts/recipe_prep.py, 19 Nov 2026, run as `--source dataverse`, its nearest open-archive
class, since its choices list no researchbox) answered NONE_OF_THESE for the assignment
column on all fourteen .sav files (confidence 0.52-0.92), which agrees.

THE QUESTIONS. Each fairness screen is the scenario followed by "This is" and fair /
unfair (1032's format); the purchase screen repeats the scenario and asks "How likely are
you to buy the new product offering?" (1 Not at all likely to 7 Very likely, middle
unlabelled); the 4 follow-up slider asks "In your opinion, how big is the change in ..."
(0 Very small to 100 Very big; the slider's row label "Magnitude of change" is not
carried), its wording differing by arm (an item override per arm); Study 7 asks "Would
you buy this detergent after this change?" (1 No, 2 Yes, as the .qsf codes it). The
scenario is the condition, the closing question the outcome, both word-for-word, split at
the question (asserted). The 1-9 quality scales keep the source's three labels (ends and
midpoint, `mid_label`).

PICTURES. Studies 5a, 5b and 5c show one product photograph above the scenario, the SAME
graphic id in every arm of a study (asserted): a chocolate bar (5a), an olive-spread tub
(5b, 5c) whose printed words include a supermarket's name and "500g". Every word that
varies between arms is in the text; the picture does not vary, so these are text
experiments and the rows do not carry it (ledger 158: a picture is never described). The
tub's "500g" and the supermarket's name are facts a respondent could see that a row would
lack, so under rich's standing rule (19 Nov 2026: never carry a study whose stimulus
picture holds information the text lacks) all three are NOT_BUILT, 5a with them since its
photograph is of the same kind. The builders below still describe them. Study 6's two choice screens name a graphic id in their .qsf payload, but
both are text/graphic "TB" questions, which Qualtrics does not render a graphic for, and the
materials PDF shows none (asserted: no image in that PDF).

ORDER (for the record: 5a and 5b are not built). 5a and 5b put the fairness and purchase questions on ONE screen, below the picture,
in a random order that the deposit records (Price_DO_PriceFair etc., positions 2 and 3).
Per rich's ruling (19 Nov 2026) and CONVENTIONS' repeated-measures rule, the order is a
factor (question_order) and each row renders that person's order: the question shown
first carries the scenario; the one shown second carries, as 3299 Study 3 did for its
recorded order, the scenario, the earlier question narrated as asked, and the scenario
again (both questions repeat it word-for-word). Added words (ours):
    'You were asked "How likely are you to buy the new product offering?" On the same
     screen you were then shown the text again:'
    'You were asked to complete "This is" with fair or unfair. On the same screen you were
     then shown the text again:'
Everything else is in a fixed order and narrated only where an outcome follows another
screen: Study 7's quality rating (its own page, after the buy question, quality arms only:
'You were asked "Would you buy this detergent after this change?"'), and Study 6, whose four
screens run chocolate choice, chocolate quality, orange choice, orange quality, each row
carrying everything shown up to it ('You were asked "Which option do you prefer?"', 'You
were asked "<the quality question>"', 'You were then shown:'). Study 6's options were in a
fixed order (no choice randomisation, asserted), so they are listed as shown.

STUDY 6's REDACTION. The orange-juice screen in the deposit reads "a cafeteria in [redacted
for review purposes]": the fielded screen named a place the deposit withholds. No row may
say "[redacted ...]", which nobody saw, nor guess the place; following CONVENTIONS'
fill-the-deposit-does-not-hold ruling, the row puts one clause of ours in its place,
"(here the screen named a place)", true for every row and claiming no more than the deposit
shows.

DROPPED. Consent, the intro and welcome screens, Study 6's debrief and timing items (survey
mechanics). Nothing else: every answered question is an outcome.

EXCLUSIONS. None pre-registered ("We will not exclude any data", every study). Every row of
every file is kept except the 4 follow-up person above.

PERSONA. Age (typed; every .qsf validates 15-100, asserted, so ages outside it would be
left blank and none is; Study 6's lab sample includes 23 seventeen-year-olds, as typed) and
gender, labels from the .qsf's own choices. Jev (recipe_prep, 19 Nov 2026) mapped Age and
Gender at confidence 1.00 on every file; it called "I prefer not to answer" a non-answer
(1.00 on every file offering it) and "None of the above" a non-answer too (0.48-0.66,
REVIEW, against the regex, its top answer on all seven files offering it). Both are left
blank: "None of the above" names no gender, and a persona line "Gender: None of the above"
tells a reader nothing about the person. The count per study is asserted (GENDER_BLANKED).

    uv run python scripts/gen_researchbox2562.py --prep   # code the data
    uv run python scripts/gen_researchbox2562.py          # write the recipes
    uv run python scripts/gen_researchbox2562.py --check  # exit 1 if any recipe differs
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
import pyreadstat
import yaml

REPO = Path(__file__).resolve().parents[1]
STUDY_ID = "researchbox2562"
RAW = REPO / "data" / "raw" / STUDY_ID
MATERIALS = RAW / "Materials"
DATA = RAW / "Data"
CODEBOOK = RAW / "Codebook"
RECIPES = REPO / "recipes"
LICENCE = (
    'CC BY 4.0, stated on the box page https://researchbox.org/2562 ("All content posted '
    'to ResearchBox is under a CC By 4.0 License"); archived as Zenodo '
    "doi:10.5281/zenodo.20808095. Read 19 Nov 2026."
)
PAPER = (
    'Evangelidis I (2026), "Skimpflation Penalty: Decreases in Product Quality Trigger '
    'Stronger Consumer Reactions than Decreases in Size or Increases in Price", Journal of '
    "Consumer Research, doi:10.1093/jcr/ucag019. ResearchBox 2562 "
    "(https://researchbox.org/2562)."
)

# tag -> the deposit's study label ("Study 2a (Pilot) - Materials.qsf")
LABEL = {
    "study1": "1",
    "study2a": "2a",
    "study2a_pilot": "2a (Pilot)",
    "study2b": "2b",
    "study2b_pilot": "2b (Pilot)",
    "study3": "3",
    "study4": "4",
    "study4_followup": "4 (Follow-up)",
    "study5a": "5a",
    "study5a_pilot": "5a (Pilot)",
    "study5b": "5b",
    "study5c": "5c",
    "study6": "6",
    "study7": "7",
}
PREREG = {
    "study1": "AsPredicted #202768",
    "study2a": "AsPredicted #178850",
    "study2a_pilot": "AsPredicted #217313",
    "study2b": "AsPredicted #199523",
    "study2b_pilot": "AsPredicted #217885",
    "study3": "AsPredicted #202544",
    "study4": "AsPredicted #197343",
    "study4_followup": "AsPredicted #218825",
    "study5a": "AsPredicted #195682",
    "study5a_pilot": "AsPredicted #217546",
    "study5b": "AsPredicted #194977",
    "study5c": "AsPredicted #294618",
    "study6": "AsPredicted #249601 and #247301",
    "study7": "AsPredicted #294997",
}

# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

_TYPO = {"\xa0": " ", "​": "", "’": "'", "‘": "'", "“": '"', "”": '"'}


def _clean(s: str) -> str:
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    for a, b in _TYPO.items():
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def norm(raw: str) -> str:
    """HTML to one line of plain text. Typography only."""
    return _clean(re.sub(r"<br\s*/?>|</p>|</div>|</li>", " ", raw or ""))


def paragraphs(raw: str) -> str:
    """HTML to paragraphs (blank-line separated); an <ol> becomes "1. ..." lines."""
    out: list[str] = []
    for part in re.split(r"(<ol>.*?</ol>)", raw, flags=re.S):
        if part.startswith("<ol>"):
            items = re.findall(r"<li>(.*?)</li>", part, flags=re.S)
            out.append("\n".join(f"{i}. {_clean(x)}" for i, x in enumerate(items, 1)))
        else:
            for p in re.split(r"</div>|<br\s*/?>", part):
                if _clean(p):
                    out.append(_clean(p))
    return "\n\n".join(out)


# ---------------------------------------------------------------------------
# The questionnaires
# ---------------------------------------------------------------------------


def pdf_images(path: Path) -> list[str]:
    """The images in a PDF, one line each, as `pdfimages -list` reports them."""
    out = subprocess.run(["pdfimages", "-list", str(path)], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return out.stdout.splitlines()[2:]


def qsf_path(tag: str) -> Path:
    return MATERIALS / f"Study {LABEL[tag]} - Materials.qsf"


def pdf_path(tag: str) -> Path:
    return MATERIALS / f"Study {LABEL[tag]} - Materials.pdf"


class Survey:
    def __init__(self, tag: str) -> None:
        raw = qsf_path(tag).read_text()
        assert "<img" not in raw, f"{tag}: an inline picture in the .qsf"
        els = json.loads(raw)["SurveyElements"]
        self.qs: dict[str, dict[str, Any]] = {
            e["Payload"]["DataExportTag"]: e["Payload"] for e in els if e["Element"] == "SQ"
        }
        self.by_qid = {q["QuestionID"]: t for t, q in self.qs.items()}
        self.blocks: dict[str, dict[str, Any]] = {}
        for e in els:
            if e["Element"] == "BL":
                p = e["Payload"]
                for b in p.values() if isinstance(p, dict) else p:
                    self.blocks[b["ID"]] = b
        self.flow: dict[str, Any] = next(e for e in els if e["Element"] == "FL")["Payload"]

    def text(self, tag: str) -> str:
        return norm(self.qs[tag]["QuestionText"])

    def randomizers(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []

        def walk(n: dict[str, Any]) -> None:
            if n.get("Type") == "BlockRandomizer":
                out.append(n)
            for c in n.get("Flow", []):
                walk(c)

        walk(self.flow)
        return out

    def block_tags(self, block_id: str) -> list[str]:
        return [
            self.by_qid[x["QuestionID"]]
            for x in self.blocks[block_id]["BlockElements"]
            if x["Type"] == "Question"
        ]

    def graphics(self) -> dict[str, str]:
        """Export tag -> graphic id, for the graphic (GRB) questions only."""
        return {
            t: q["Graphics"]
            for t, q in self.qs.items()
            if q["QuestionType"] == "DB" and q["Selector"] == "GRB"
        }


def arm_blocks(sv: Survey) -> list[list[str]]:
    """The one BlockRandomizer's blocks (SubSet 1: each person sees one), as export tags."""
    (rand,) = sv.randomizers()
    assert int(rand["SubSet"]) == 1, rand["SubSet"]
    return [sv.block_tags(b["ID"]) for b in rand["Flow"]]


def split_question(sv: Survey, tag: str, question: str) -> str:
    """The scenario: the question text up to its closing `question`."""
    t = sv.text(tag)
    assert t.endswith(" " + question), (tag, t[-60:])
    return t[: -len(question) - 1]


def mc_scale(sv: Survey, tag: str, force: bool = True) -> dict[str, Any]:
    """A single-answer scale: codes from the .qsf's recodes, labels at the ends and middle."""
    q = sv.qs[tag]
    assert q["QuestionType"] == "MC" and q["Selector"] in ("SAVR", "SAHR"), tag
    assert (q["Validation"]["Settings"]["ForceResponse"] == "ON") is force, tag
    assert not q.get("Randomization"), tag  # options in a fixed order
    order = [str(k) for k in q["ChoiceOrder"]]
    recode = q.get("RecodeValues") or {}
    codes = [int(recode.get(k, k)) for k in order]
    assert codes == list(range(1, len(order) + 1)), (tag, codes)
    labels = [norm(q["Choices"][k]["Display"]) for k in order]
    sc: dict[str, Any] = {"min": 1, "max": len(order), "min_label": labels[0]}
    sc["max_label"] = labels[-1]
    inner = labels[1:-1]
    if len(order) > 2:
        mid = (len(order) - 1) // 2
        if inner[mid - 1]:
            sc["mid_label"] = inner[mid - 1]
            inner = inner[: mid - 1] + inner[mid:]
        assert all(lab == "" for lab in inner), (tag, labels)
    return sc


def nominal_choice(sv: Survey, tag: str) -> tuple[dict[str, Any], str]:
    """A pick among options: a nominal scale and the options enumerated for the question."""
    q = sv.qs[tag]
    assert q["QuestionType"] == "MC" and q["Selector"] == "SAVR", tag
    assert q["Validation"]["Settings"]["ForceResponse"] == "ON", tag
    assert not q.get("Randomization"), tag  # options in a fixed order
    order = [str(k) for k in q["ChoiceOrder"]]
    recode = q.get("RecodeValues") or {}
    codes = [int(recode.get(k, k)) for k in order]
    assert codes == list(range(1, len(order) + 1)), (tag, codes)
    opts = "; ".join(
        f'{c} means "{norm(q["Choices"][k]["Display"])}"' for c, k in zip(codes, order, strict=True)
    )
    return {"min": 1, "max": len(order), "nominal": True}, opts


def slider_scale(sv: Survey, tag: str) -> dict[str, Any]:
    q = sv.qs[tag]
    assert q["QuestionType"] == "Slider", tag
    c = q["Configuration"]
    assert (c["CSSliderMin"], c["CSSliderMax"], c["NumDecimals"]) == (0, 100, "0"), tag
    labels = [norm(q["Labels"][k]["Display"]) for k in ("1", "2")]
    assert list(q["Choices"]) == ["1"] and norm(q["Choices"]["1"]["Display"]) == (
        "Magnitude of change"
    )
    return {"min": 0, "max": 100, "min_label": labels[0], "max_label": labels[1]}


GENDER_BLANK = {"I prefer not to answer", "None of the above"}
AGE_RANGE = (15, 100)


def gender_labels(sv: Survey) -> dict[int, str]:
    q = sv.qs["Gender"]
    assert norm(q["QuestionText"]) == "What is your gender?"
    recode = q.get("RecodeValues") or {}
    return {int(recode.get(k, k)): norm(v["Display"]) for k, v in q["Choices"].items()}


def age_range(sv: Survey) -> tuple[int, int]:
    v = sv.qs["Age"]["Validation"]["Settings"]
    assert v["ContentType"] == "ValidNumber" and v["ForceResponse"] == "ON"
    return int(v["ValidNumber"]["Min"]), int(v["ValidNumber"]["Max"])


# ---------------------------------------------------------------------------
# The experiments
# ---------------------------------------------------------------------------


@dataclass
class Arm:
    code: int
    factors: dict[str, str]
    text: str
    items: dict[int, dict[str, Any]] = field(default_factory=dict)


@dataclass
class Outcome:
    var: str
    question: str
    scale: dict[str, Any]


@dataclass
class Experiment:
    name: str
    title: str
    kind: str
    factors: list[str]
    arms: list[Arm]
    outcomes: list[Outcome]
    notes: str
    # per outcome, the deposit columns (one per arm, in arm order; None = not asked there)
    columns: dict[str, list[str | None]] = field(default_factory=dict)


FAIR_Q = "This is"
PUR_Q = "How likely are you to buy the new product offering?"
BUY_Q = "Would you buy this detergent after this change?"
QUAL_Q = "In your opinion, the quality of the product..."


def fairness(name: str, cells: list[tuple[str, dict[str, str]]]) -> tuple[Survey, list[Arm]]:
    """Arms of a between-person fairness study, one column per arm, in the flow's order."""
    sv = Survey(name)
    assert arm_blocks(sv) == [[c] for c, _ in cells], name
    assert not sv.graphics(), name
    arms = [Arm(i + 1, f, split_question(sv, c, FAIR_Q)) for i, (c, f) in enumerate(cells)]
    (sc,) = {json.dumps(mc_scale(sv, c)) for c, _ in cells}
    assert json.loads(sc) == {"min": 1, "max": 2, "min_label": "fair", "max_label": "unfair"}
    return sv, arms


FAIR_SCALE = {"min": 1, "max": 2, "min_label": "fair", "max_label": "unfair"}
ACTIONS = ["price_increase", "size_decrease", "quality_decrease"]


def study1() -> Experiment:
    cells = [
        (f"{p}{a}", {"product": prod, "action": act})
        for p, prod in (("Cho", "chocolate"), ("Str", "streaming_platform"))
        for a, act in zip(("Price", "Size", "Qual"), ACTIONS, strict=True)
    ]
    _, arms = fairness("study1", cells)
    return Experiment(
        name="study1",
        title="A chocolate maker or a streaming platform, facing higher costs, raises the "
        "price, shrinks the product or cuts its quality: fair or unfair? (Study 1)",
        kind="mix",
        factors=["product", "action"],
        arms=arms,
        outcomes=[Outcome("fair", FAIR_Q, FAIR_SCALE)],
        notes="3 (price, size or quality) x 2 (a chocolate manufacturer or a streaming "
        "platform's movie library) between people.",
        columns={"fair": [c for c, _ in cells]},
    )


def study2a() -> Experiment:
    cells = [
        (f"{t}{a}", {"action": act, "transparency": lev})
        for a, act in zip(("Price", "Size", "Qual"), ACTIONS, strict=True)
        for t, lev in (("Lowtr", "low"), ("Hightr", "high"))
    ]
    _, arms = fairness("study2a", cells)
    return Experiment(
        name="study2a",
        title="An olive spread maker, facing higher costs, raises the price, shrinks the pack "
        "or cuts the olive oil, saying so on the packaging or not: fair or unfair? (Study 2a)",
        kind="mix",
        factors=["action", "transparency"],
        arms=arms,
        outcomes=[Outcome("fair", FAIR_Q, FAIR_SCALE)],
        notes="3 (price, package size or percentage of olive oil) x 2 (the firm explicitly "
        "communicates the change on the packaging, high transparency, or no more is said, "
        "low) between people.",
        columns={"fair": [c for c, _ in cells]},
    )


def study2b() -> Experiment:
    cells = [
        (f"{t}{a}", {"action": act, "communication": lev})
        for t, lev in (("No", "none"), ("Man", "manufacturer"), ("Ret", "retailer"))
        for a, act in zip(("Price", "Size", "Qual"), ACTIONS, strict=True)
    ]
    _, arms = fairness("study2b", cells)
    return Experiment(
        name="study2b",
        title="An orange juice maker, facing higher costs, raises the price, shrinks the pack "
        "or dilutes the juice, and the change is stated on the pack, on the shelf, or not at "
        "all: fair or unfair? (Study 2b)",
        kind="mix",
        factors=["action", "communication"],
        arms=arms,
        outcomes=[Outcome("fair", FAIR_Q, FAIR_SCALE)],
        notes="3 (price, package size or concentration of orange juice) x 3 (no "
        "communication, the manufacturer communicates the change on the packaging, or the "
        "retailer on the shelf) between people.",
        columns={"fair": [c for c, _ in cells]},
    )


def study3() -> Experiment:
    cells = [
        ("Price", {"action": "price_increase"}),
        ("Size", {"action": "size_decrease"}),
        ("QualPaper", {"action": "paper_quality_decrease"}),
        ("QualPack", {"action": "packaging_quality_decrease"}),
    ]
    _, arms = fairness("study3", cells)
    return Experiment(
        name="study3",
        title="A toilet paper maker, facing higher costs, raises the price, shrinks the pack, "
        "or cuts the paper's or the packaging's quality: fair or unfair? (Study 3)",
        kind="version",
        factors=["action"],
        arms=arms,
        outcomes=[Outcome("fair", FAIR_Q, FAIR_SCALE)],
        notes="Four arms between people: price, package size, toilet paper quality, or "
        "packaging quality.",
        columns={"fair": [c for c, _ in cells]},
    )


def study4() -> Experiment:
    cells = [
        (f"{a}{m}", {"action": act, "costs": lev})
        for m, lev in (("Equal", "up_10pct"), ("Higher", "up_5pct"), ("Lower", "up_15pct"))
        for a, act in zip(("Price", "Size", "Qual"), ACTIONS, strict=True)
    ]
    _, arms = fairness("study4", cells)
    return Experiment(
        name="study4",
        title="An orange juice maker whose costs rose 10%, 5% or 15% raises the price, shrinks "
        "the pack or dilutes the juice by 10%: fair or unfair? (Study 4)",
        kind="mix",
        factors=["action", "costs"],
        arms=arms,
        outcomes=[Outcome("fair", FAIR_Q, FAIR_SCALE)],
        notes="3 (price, package size or concentration, each changed by 10%) x 3 (costs "
        "increased by 10%, 5% or 15%: the R script's Equal, Higher and Lower, the change "
        "being equal to, higher or lower than the cost increase) between people.",
        columns={"fair": [c for c, _ in cells]},
    )


def study4_followup() -> Experiment:
    name = "study4_followup"
    sv = Survey(name)
    cols = ["Price", "Size", "Quality"]
    assert arm_blocks(sv) == [[c] for c in cols]
    assert not sv.graphics()
    arms, scales = [], set()
    for i, (c, act) in enumerate(zip(cols, ACTIONS, strict=True)):
        t = sv.text(c)
        cut = t.index(" In your opinion, how big is the change in ")
        q = sv.qs[c]
        assert q["Validation"]["Settings"]["ForceResponse"] == "OFF"
        arms.append(Arm(i + 1, {"action": act}, t[:cut], {0: {"outcome_question": t[cut + 1 :]}}))
        scales.add(json.dumps(slider_scale(sv, c)))
    (sc,) = scales
    return Experiment(
        name=name,
        title="An orange juice maker, facing higher costs, raises the price, shrinks the pack "
        "or dilutes the juice by 10%: how big is the change? (Study 4 follow-up)",
        kind="version",
        factors=["action"],
        arms=arms,
        outcomes=[Outcome("magnitude", arms[0].items[0]["outcome_question"], json.loads(sc))],
        notes="Three arms between people, each change by 10%. The question names the "
        "changed attribute, so its wording differs by arm (an item override on each arm). "
        "A slider from 0 (Very small) to 100 (Very big), whole numbers; its row label "
        '"Magnitude of change" is not carried. The slider was not forced: one of 301 '
        "people moved none, so their arm is unknown and they are dropped; 300 kept.",
        columns={"magnitude": [f"{c}_1" for c in cols]},
    )


NARRATE_PUR = f'You were asked "{PUR_Q}" On the same screen you were then shown the text again:'
NARRATE_FAIR = (
    'You were asked to complete "This is" with fair or unfair. On the same screen you were '
    "then shown the text again:"
)
ORDERS = [("fairness_first", "Fair"), ("purchase_first", "Pur")]


def study5(name: str) -> Experiment:
    """5a and 5b: fairness and purchase on one screen, in a recorded random order."""
    sv = Survey(name)
    blocks = arm_blocks(sv)
    graphics = sv.graphics()
    (graphic,) = set(graphics.values())  # one picture, the same in every arm
    arms: list[Arm] = []
    fair_cols, pur_cols = [], []
    for b, (p, act) in zip(
        blocks, zip(("Price", "Size", "Qual"), ACTIONS, strict=True), strict=True
    ):
        pic, *qs = b
        assert pic in graphics and sorted(qs) == sorted([f"{p}Fair", f"{p}Pur"]), b
        scenario = split_question(sv, f"{p}Fair", FAIR_Q)
        assert split_question(sv, f"{p}Pur", PUR_Q) == scenario
        assert mc_scale(sv, f"{p}Fair") == FAIR_SCALE
        for order, _first in ORDERS:
            code = len(arms) + 1
            # As 3299 Study 3: the arm's text is what its second-asked question's row
            # shows, and the first-asked question's row overrides it with the scenario
            # alone, so the two orders' arm texts differ (QC rule 5's minimal pair).
            if order == "fairness_first":
                text = f"{scenario}\n\n{NARRATE_FAIR}\n\n{scenario}"
                items = {0: {"condition_text": scenario}}
            else:
                text = f"{scenario}\n\n{NARRATE_PUR}\n\n{scenario}"
                items = {1: {"condition_text": scenario}}
            arms.append(Arm(code, {"action": act, "question_order": order}, text, items))
            fair_cols.append(f"{p}Fair")
            pur_cols.append(f"{p}Pur")
    pur = {json.dumps(mc_scale(sv, c)) for c in set(pur_cols)}
    (pur_scale,) = pur
    product = {"study5a": "chocolate", "study5b": "olive spread"}[name]
    pct = {"study5a": "5%", "study5b": "15%"}[name]
    picture = {
        "study5a": "a chocolate bar",
        "study5b": 'an olive spread tub whose printed words include a supermarket\'s name and "500g"',
    }[name]
    return Experiment(
        name=name,
        title=f"A {product} maker, facing {pct} higher costs, raises the price, shrinks the "
        f"pack or cuts the {'cocoa' if name == 'study5a' else 'olive oil'} by {pct}: fair or "
        f"unfair, and how likely are you to buy? (Study {LABEL[name]})",
        kind="mix",
        factors=["action", "question_order"],
        arms=arms,
        outcomes=[
            Outcome("fair", FAIR_Q, FAIR_SCALE),
            Outcome("purchase", PUR_Q, json.loads(pur_scale)),
        ],
        notes=f"Three arms between people (price, package size or amount of "
        f"{'cocoa' if name == 'study5a' else 'olive oil'}, each by {pct}), each person "
        "answering two questions on one screen: fair or unfair, and how likely to buy. "
        "Their order was random and is recorded (the block's display-order columns), so it "
        "is a factor (question_order) and each row renders that person's order: the second "
        "question's row narrates the first, as asked, then repeats the scenario, which both "
        f"questions printed word-for-word. Added words (ours): '{NARRATE_PUR}' and "
        f"'{NARRATE_FAIR}'. Above both questions the screen showed a photograph of "
        f"{picture} (graphic {graphic}), the same in every arm; it is not carried, and the "
        "text holds every word that varies between arms.",
        columns={"fair": fair_cols, "purchase": pur_cols},
    )


def study5c() -> Experiment:
    name = "study5c"
    sv = Survey(name)
    blocks = arm_blocks(sv)
    graphics = sv.graphics()
    (graphic,) = set(graphics.values())
    cols = ["Price", "Size", "Qual"]
    arms, scales = [], set()
    for i, (b, c, act) in enumerate(zip(blocks, cols, ACTIONS, strict=True)):
        assert b[0] in graphics and b[1:] == [c], b
        arms.append(Arm(i + 1, {"action": act}, split_question(sv, c, PUR_Q)))
        scales.add(json.dumps(mc_scale(sv, c)))
    (sc,) = scales
    return Experiment(
        name=name,
        title="An olive spread maker, facing 15% higher costs, raises the price, shrinks the "
        "pack or cuts the olive oil by 15%: how likely are you to buy? (Study 5c)",
        kind="version",
        factors=["action"],
        arms=arms,
        outcomes=[Outcome("purchase", PUR_Q, json.loads(sc))],
        notes="Three arms between people, each change by 15%; how likely to buy, 1 to 7. "
        "Above the question the screen showed a photograph of an olive spread tub whose "
        'printed words include a supermarket\'s name and "500g" (graphic '
        f"{graphic}), the same in every arm; it is not carried, and the text holds every "
        "word that varies between arms.",
        columns={"purchase": cols},
    )


def pilot(name: str) -> Experiment:
    sv = Survey(name)
    assert not sv.randomizers() and not sv.graphics()
    scenario = split_question(sv, "QualChange", QUAL_Q)
    sc = mc_scale(sv, "QualChange", force=False)
    product = {
        "study2a_pilot": ("an olive spread", "olive oil"),
        "study2b_pilot": ("an orange juice", "orange juice"),
        "study5a_pilot": ("a chocolate", "cocoa"),
    }[name]
    return Experiment(
        name=name,
        title=f"{product[0][0].upper()}{product[0][1:]} maker, facing higher costs, cuts the "
        f"{product[1]} in its product: what happens to its quality? (Study "
        f"{LABEL[name]})",
        kind="baseline",
        factors=[],
        arms=[Arm(1, {}, scenario)],
        outcomes=[Outcome("quality", QUAL_Q, sc)],
        notes="A pilot: 50 people on Prolific, its own pre-registered .qsf, no conditions "
        '("All participants will answer the same question"), so one condition. 1 to 9, '
        "the source labelling the ends and the midpoint (5). The question was not forced, "
        "and all 50 answered.",
        columns={"quality": ["QualChange"]},
    )


REDACTED = "[redacted for review purposes]"
PLACE = "(here the screen named a place)"


def study6() -> Experiment:
    name = "study6"
    sv = Survey(name)
    assert not sv.randomizers() and not sv.graphics()
    assert not pdf_images(pdf_path(name)), name  # the materials PDF shows no picture
    shared = paragraphs(sv.qs["Q47"]["QuestionText"])
    choc = paragraphs(sv.qs["Q16"]["QuestionText"])
    raw_ora = sv.qs["Q15"]["QuestionText"]
    assert raw_ora.count(REDACTED) == 1
    ora = paragraphs(raw_ora.replace(REDACTED, PLACE))
    for t in ("Q16", "Q15"):
        q = sv.qs[t]
        assert (q["QuestionType"], q["Selector"]) == ("DB", "TB"), t  # no graphic rendered
    choice_q = sv.text("ChoChoice")
    assert choice_q == sv.text("OraChoice") == "Which option do you prefer?"
    cho_sc, cho_opts = nominal_choice(sv, "ChoChoice")
    ora_sc, ora_opts = nominal_choice(sv, "OraChoice")
    cho_qual, ora_qual = sv.text("ChoQualChange"), sv.text("OraQualChange")
    cho_qsc = mc_scale(sv, "ChoQualChange", force=False)
    ora_qsc = mc_scale(sv, "OraQualChange", force=False)
    first = f"{shared}\n\n{choc}"
    asked_choice = f'You were asked "{choice_q}"'
    second = f"{first}\n\n{asked_choice}"
    third = f'{second} You were then asked "{cho_qual}" You were then shown:\n\n{ora}'
    fourth = f"{third}\n\n{asked_choice}"
    arm = Arm(1, {}, first, {1: {"condition_text": second}, 2: {"condition_text": third}})
    arm.items[3] = {"condition_text": fourth}
    return Experiment(
        name=name,
        title="Choosing for real between a price rise, a smaller size and less cocoa (then "
        "less orange juice), and rating what the quality cut does (Study 6)",
        kind="shelf",
        factors=[],
        arms=[arm],
        outcomes=[
            Outcome("cho_choice", f"{choice_q} {cho_opts}.", cho_sc),
            Outcome("cho_quality", cho_qual, cho_qsc),
            Outcome("ora_choice", f"{choice_q} {ora_opts}.", ora_sc),
            Outcome("ora_quality", ora_qual, ora_qsc),
        ],
        notes="A university behavioural lab (the pre-registrations), paid for real: five "
        "people drawn to receive the option they chose and EUR 5 less its price. No "
        "conditions: everyone saw the same four screens in a fixed order (chocolate choice, "
        "chocolate quality, orange juice choice, orange juice quality), so one condition "
        "with four outcomes, each row carrying everything shown up to its own question. "
        "The three options were listed in a fixed order (no choice randomisation in the "
        ".qsf) and are enumerated in the question as shown, codes as the .qsf recodes them "
        "(its third option is choice 5, recoded 3). The instructions screen is kept (the "
        "real stakes); its welcome page, the timing items and the debrief are dropped. "
        f"Added words (ours): '{asked_choice}', 'You were then asked \"...\"' (the quality "
        "question word-for-word), 'You were then shown:', and, where the deposit's "
        f"orange-juice screen reads \"a cafeteria in {REDACTED}\", the clause '{PLACE}' "
        "(the fielded screen named a place the deposit withholds). The two quality "
        "questions were not forced; all 208 answered both.",
        columns={
            "cho_choice": ["ChoChoice"],
            "cho_quality": ["ChoQualChange"],
            "ora_choice": ["OraChoice"],
            "ora_quality": ["OraQualChange"],
        },
    )


NARRATE_BUY = f'You were asked "{BUY_Q}"'


def study7() -> Experiment:
    name = "study7"
    sv = Survey(name)
    cols = ["Price", "Size", "RecQual", "NonQual"]
    acts = ["price_increase", "size_decrease", "recoverable_quality", "nonrecoverable_quality"]
    assert arm_blocks(sv) == [[c] for c in cols]
    assert not sv.graphics()
    rating_q = sv.text("QualChangeRating")
    rating_sc = mc_scale(sv, "QualChangeRating")
    # the rating is shown (its own block, after the arm) only to the two quality arms
    branch = json.dumps(sv.flow)
    for c in ("RecQual", "NonQual"):
        assert sv.qs[c]["QuestionID"] in branch
    for c in ("Price", "Size"):
        assert f'"QuestionID": "{sv.qs[c]["QuestionID"]}"' not in branch
    arms, scales = [], set()
    for i, (c, act) in enumerate(zip(cols, acts, strict=True)):
        scenario = split_question(sv, c, BUY_Q)
        items = {}
        if "Qual" in c:
            items = {1: {"condition_text": f"{scenario}\n\n{NARRATE_BUY}"}}
        arms.append(Arm(i + 1, {"action": act}, scenario, items))
        scales.add(json.dumps(mc_scale(sv, c)))
    (sc,) = scales
    assert json.loads(sc) == {"min": 1, "max": 2, "min_label": "No", "max_label": "Yes"}
    return Experiment(
        name=name,
        title="A British detergent maker, facing higher costs, raises the price, shrinks the "
        "bottle, or weakens the formula in a way more detergent can or cannot make up: would "
        "you buy it? (Study 7)",
        kind="version",
        factors=["action"],
        arms=arms,
        outcomes=[
            Outcome("buy", BUY_Q, json.loads(sc)),
            Outcome("quality", rating_q, rating_sc),
        ],
        notes="Four arms between people: price (GBP 6.00 to 6.60), bottle size (1,000 ml "
        "to 909 ml), or a weaker formula (30% to 27.3% active ingredients) whose loss "
        "using more detergent does or does not recover. Would you buy it: 1 = No, 2 = Yes, "
        "as the .qsf codes it. The two quality arms then rated the new detergent's quality "
        "on a page of its own (1 to 9, the source labelling the ends and the midpoint); "
        f"those rows add, after the scenario, '{NARRATE_BUY}' (ours, narrating the screen "
        "before as asked).",
        columns={"buy": cols, "quality": [None, None, "QualChangeRating", "QualChangeRating"]},
    )


# Not built (rich's standing rule, 19 Nov 2026: never carry a study whose stimulus picture
# holds information the text lacks). 5a, 5b and 5c show a product photograph above every
# scenario; 5b's and 5c's olive spread tub carries printed words (a supermarket's name,
# "500g") that no row could hold. Their builders stay above, for the record. The 5a pilot
# has no picture (asserted in `pilot`) and is built.
NOT_BUILT = ("study5a", "study5b", "study5c")


def experiments() -> list[Experiment]:
    return [
        study1(),
        study2a(),
        pilot("study2a_pilot"),
        study2b(),
        pilot("study2b_pilot"),
        study3(),
        study4(),
        study4_followup(),
        pilot("study5a_pilot"),
        study6(),
        study7(),
    ]


def experiment(tag: str) -> Experiment:
    (e,) = [x for x in experiments() if x.name == tag]
    return e


# ---------------------------------------------------------------------------
# Coded data
# ---------------------------------------------------------------------------

N = {
    "study1": 1502,
    "study2a": 3006,
    "study2a_pilot": 50,
    "study2b": 4007,
    "study2b_pilot": 50,
    "study3": 1601,
    "study4": 4005,
    "study4_followup": 300,
    "study5a_pilot": 50,
    "study6": 208,
    "study7": 1005,
}
DROPPED = {"study4_followup": 1}  # no slider moved, so no arm
GENDER_BLANKED = {"study1": 6, "study3": 2, "study4": 8}  # codes 5, 6


def data_file(tag: str) -> str:
    return f"{STUDY_ID}_{tag}.csv"


def read_deposit(tag: str) -> pd.DataFrame:
    """The deposit's file as it is, with each person's row number (1-based) as `row`."""
    df, _ = pyreadstat.read_sav(str(DATA / f"Study {LABEL[tag]} - Data.sav"))
    df.insert(0, "row", range(1, len(df) + 1))
    return df


def prep(tag: str) -> pd.DataFrame:
    """One coded row per kept person: arm, answers, age, gender."""
    e = experiment(tag)
    sv = Survey(tag)
    df = read_deposit(tag)
    first_var = e.outcomes[0].var
    if len(e.arms) > 1:
        # the arm: which of the first outcome's per-arm columns is filled
        cols = list(dict.fromkeys(c for c in e.columns[first_var] if c))
        filled = df[cols].notna()
        n_filled = filled.sum(axis=1)
        assert set(n_filled) <= {0, 1}, tag
        assert int((n_filled == 0).sum()) == DROPPED.get(tag, 0), tag
        df = df[n_filled == 1].reset_index(drop=True)
        filled = filled[n_filled == 1].reset_index(drop=True)
        action_col = filled.idxmax(axis=1)
    out = pd.DataFrame({"pid": [f"{tag}_{r}" for r in df["row"]]})
    if len(e.arms) == 1:
        out["arm"] = 1
    elif tag in ("study5a", "study5b"):
        block = {"PriceFair": "Price", "SizeFair": "Size", "QualFair": "Quality"}
        codes = []
        for i, col in enumerate(action_col):
            pos = int(df.at[i, f"{block[col]}_DO_{col}"])
            other = int(df.at[i, f"{block[col]}_DO_{col.replace('Fair', 'Pur')}"])
            assert {pos, other} == {2, 3}  # position 1 is the picture
            order = "fairness_first" if pos == 2 else "purchase_first"
            (a,) = [
                a
                for a, c in zip(e.arms, e.columns["fair"], strict=True)
                if c == col and a.factors["question_order"] == order
            ]
            codes.append(a.code)
        out["arm"] = codes
    else:
        code = {c: a.code for a, c in zip(e.arms, e.columns[first_var], strict=True)}
        out["arm"] = action_col.map(code).values
    arm_of = {a.code: i for i, a in enumerate(e.arms)}
    for o in e.outcomes:
        vals = []
        for i, a in enumerate(out["arm"]):
            col = e.columns[o.var][arm_of[a]] if len(e.columns[o.var]) > 1 else e.columns[o.var][0]
            v = df.at[i, col] if col else float("nan")
            if col and o.var != "quality":
                assert pd.notna(v), (tag, o.var, i)  # forced, or (pilots, 6) all answered
            vals.append(v)
        s = pd.Series(vals, dtype="float64")
        if tag == "study7" and o.var == "quality":
            # answered exactly by the two quality arms
            assert (s.notna() == out["arm"].isin([3, 4])).all()
        if tag != "study7":
            assert s.notna().all(), (tag, o.var)
        assert (s.dropna() % 1 == 0).all()
        assert s.dropna().between(o.scale["min"], o.scale["max"]).all(), (tag, o.var)
        out[o.var] = s.astype("Int64").values
    lo, hi = age_range(sv)
    assert (lo, hi) == AGE_RANGE, tag
    age = pd.to_numeric(df["Age"], errors="coerce")
    out["age"] = age.where(age.between(lo, hi)).astype("Int64").values
    labels = gender_labels(sv)
    g = [labels[int(x)] if pd.notna(x) else None for x in df["Gender"]]
    blank = sum(x in GENDER_BLANK for x in g)
    assert blank == GENDER_BLANKED.get(tag, 0), (tag, blank)
    out["gender"] = [None if x in GENDER_BLANK else x for x in g]
    assert len(out) == N[tag], (tag, len(out))
    return out


def _nocurrency(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub("[\u00a3\u20ac]", "", s))


def check_codebook(tag: str) -> None:
    """Each column's label in the codebook is the question the .qsf asks under that tag.

    The codebooks lost the pound and euro signs in their export (Study 7's "increase the
    price to 6.60"), so those two characters are ignored on both sides.
    """
    sv = Survey(tag)
    book = pd.read_csv(next(CODEBOOK.glob(f"Study {LABEL[tag]} - Data.*___CODEBOOK.csv")))
    for var, desc in zip(book["varname"], book["description"], strict=True):
        base, _, item = var.partition("_")
        d = norm(str(desc).replace("<U+2019>", "'"))
        if var in sv.qs:
            assert _nocurrency(d) == _nocurrency(sv.text(var)), var
        elif base in sv.qs and item == "1" and sv.qs[base]["QuestionType"] == "Slider":
            want = f"{sv.text(base)} - {norm(sv.qs[base]['Choices']['1']['Display'])}"
            assert _nocurrency(d) == _nocurrency(want), var


# ---------------------------------------------------------------------------
# The recipes
# ---------------------------------------------------------------------------


def recipe(e: Experiment) -> dict[str, Any]:
    arms = []
    for i, a in enumerate(e.arms):
        arm: dict[str, Any] = {
            "raw_values": {"arm": a.code},
            "condition_num": i,
            "factors": a.factors,
            "text": a.text,
        }
        if a.items:
            arm["items"] = {k: a.items[k] for k in sorted(a.items)}
        arms.append(arm)
    outcomes = [
        {"var": o.var, "task_num": t, "question": o.question, "scale": o.scale}
        for t, o in enumerate(e.outcomes)
    ]
    lo = min(o.scale["min"] for o in e.outcomes)
    hi = max(o.scale["max"] for o in e.outcomes)
    notes = (
        f"{PAPER}\n\nGENERATED by scripts/gen_researchbox2562.py; every judgement is in its "
        f"docstring. Study {LABEL[e.name]} (pre-registered, {PREREG[e.name]}), "
        f"{N[e.name]:,} people. {e.notes} No exclusions were pre-registered.\n\nWording "
        f"from {qsf_path(e.name).name}. The scenario is the condition and the closing "
        "question the outcome, both word-for-word. Where there are arms, the assignment is "
        "derived from which arm's column is filled (each such question was ForceResponse, "
        "so a blank means not shown). Typography normalised (HTML entities, non-breaking "
        "spaces, curly quotes). Persona: age (years; the .qsf accepts 15-100) and gender, "
        'labels from the .qsf\'s own choices, "I prefer not to answer" and "None of the '
        'above" left blank (Jev: non-answer, 1.00 and 0.66).'
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
        "condition": {"source_vars": ["arm"], "factors": e.factors, "arms": arms},
        "outcomes": outcomes,
        "response_recode": {k: k for k in range(lo, hi + 1)},
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
        for tag in (t for t in LABEL if t not in NOT_BUILT):
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
