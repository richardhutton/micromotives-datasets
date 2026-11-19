#!/usr/bin/env python3
"""Write recipes/researchbox108_*.yaml: top rated or best seller (3 recipes).

Barnes AJ, Shavitt S (2024), "Top Rated or Best Seller? Cultural Differences in Responses to
Attitudinal versus Behavioral Consensus Cues", Journal of Consumer Research 51(2):276-297,
doi:10.1093/jcr/ucad074. ResearchBox 108 ("Top Rated or Best Seller",
https://researchbox.org/108). CC BY 4.0 ("All content posted to ResearchBox is under a CC By
4.0 License", the box page). Prices kept as the source has them (US dollars, Indian rupees).

Every judgement is here, in code, so the recipes can be re-derived and reviewed.

THE DESIGN. An attitudinal consensus cue ("85% ... love the brand", "81% ... preferred
Neutron", "Top Rated") against a behavioural one ("buy the brand", "signed up with",
"Best Seller"), sometimes crossed with a self-construal prime or a measured culture scale.
The box holds nine .qsf files, eight data files (Studies 1-6, WA I, WA F), a materials PDF
(Studies 1-5), the table of item means and SDs (Studies 1-6, WA F, WA G) and one AsPredicted
pre-registration (Study 2, #53701).

WHAT IS BUILT. Three recipes:
- study1_us, study1_india: Study 1 ("Laplet"). A new tablet that doubles as a laptop; 85% of
  consumers who learn about it love it (attitudinal) or buy it (behavioural); how much would
  you pay? Two samples, each its own .qsf: the US one (U.S. market, a 0-1000 USD slider) and
  the India one (India market, a 0-50000 Rupee slider). The India .qsf is in English
  (SurveyLanguage EN, no translations; asserted), so it is built under rich's ruling. One
  data file holds both, INDIA 0/1 and AttCue 1 attitudinal / 0 behavioural.
- study4: Study 4 ("relative diagnosticity"). No manipulation: everyone read that some
  headphones are labelled "Top Rated" and some "Best Seller" and said which label is more
  important (impt) and, on the next page, more relevant (relv), 1 Definitely "Top Rated" to
  6 Definitely "Best Seller". A single-condition study (kind baseline), as 2562's pilots.

NOT BUILT (NOT_BUILT, with the reason each time):
- study2 (Neutron Mobile), study3 (Starbucks), study5 (ENZO headphones), wa_f (Starbucks
  again): the consensus cue screen in every arm shows a picture that carries the cue itself
  ("TOP RATED" / "BEST SELLING" / "BEST SELLER" / "BUYER'S CHOICE" banners, read from the
  materials PDF's own copies of the pictures) and the brand's name or logo; Study 5's product
  information screen is ONLY a picture (its attributes are printed words on the photograph).
  rich's picture rule (19 Nov 2026): skip.
- wa_i (Spontaneous inference): the only question is free text (FreeAssoc); the numeric
  columns are two research assistants' codes of that text, not answers anyone gave.
- study6 (Amazon): product listings (ratings, best-seller ranks, prices), no respondents.

PICTURES. The .qsf files hold 57 <img> tags (asserted per file in PICTURE_COUNT). Those in
the built studies' survey flows are all judged decorative, and every other in-flow picture
belongs to a study not built:
- Study 1 (both samples), Q16, IM_4JdL2Urh7IFjsXj: the community ladder beside the
  subjective-status question ("Think of this ladder ..."), 299 x 786, in the demographics
  block after the outcome. A drawn ladder; nothing about Laplet, its price or the cue, and
  the ses item it illustrates is not built.
- Study 4, Q194 (the consent screen), IM_7P9Qx7SaoRGp22V: 299 x 102, directly after
  "Sincerely," and before "Eligibility", i.e. the investigator's signature. Before any
  question, about no product. (The graphic itself is not retrievable: Qualtrics answers 308.)
The other 17 tags in Study 4's .qsf are in questions outside the survey flow (blocks of
other studies kept in the file, or the trash); asserted. Not-built studies' in-flow pictures
are listed in their NOT_BUILT reason.

THE ASSIGNMENT. Study 1: AttCue (the authors' code; the .qsf's BlockRandomizer shows
"love" or "buy", SubSet 1, evenly). Its two cells' texts differ only by "love" / "buy"
(asserted). Arm 1 attitudinal (love), arm 2 behavioural (buy). Study 4: one condition.

THE QUESTIONS. Study 1: the cue screen (a text/graphic question, no picture) is the
condition, word-for-word; the WTP slider ("How much would be willing to pay for a Laplet?",
the source's missing "you" kept) is the outcome, on its own block after it. The slider's
only row label names the currency ("USD" / "Rupee"), which the answer cannot be read
without, so one sentence of ours names it, quoting the label: 'Answer on the slider
labelled "USD".' (CONVENTIONS, one stem, several labelled answer fields: the field name is
the source's own, quoted, and notes record the added words.) Whole numbers, 0-1000 or
0-50000 (CSSliderMin/Max, NumDecimals 0; asserted), ForceResponse ON.
Study 4: impt's text is the scenario followed by "Which of these criteria do you think is
more important to consider?"; split there (asserted). The scenario is the condition. relv
follows on the next page in a fixed order, so its row carries the scenario and the earlier
question narrated as asked (CONVENTIONS, repeated measures): 'You were asked "Which of these
criteria do you think is more important to consider?"' (ours). Labels from the in-flow
questions' own choices: 1 'Definitely "Top Rated"', 6 'Definitely "Best Seller"' (impt) and
'Definitely that they are "Top Rated"' / '... "Best Seller"' (relv), middle unlabelled.
The .qsf also holds, OUTSIDE the flow, copies of impt and relv under the same export tags
with the ends reversed (1 "Best Seller"); questions are therefore always looked up through
the flow, never by export tag alone (asserted: the flow holds exactly one of each), and the
codebook's "higher values = behavioral consensus cues more diagnostic" agrees with the
in-flow coding.

ORDER. No order in either study was randomised: Study 1 shows one screen then the slider;
Study 4's culture scale (block "Advanced" randomisation) comes before both questions, which
are in a fixed order. Nothing to record as a factor.

DROPPED. Study 1: race and subjective status (not persona fields built here) and the
open-ended "what it means to be loyal to a brand". Study 4: the 16 Triandis and Gelfand
culture items (a measured moderator asked before the scenario; scale scores, not a response
to it) and race (a select-all question).

EXCLUSIONS. None pre-registered for these studies (only Study 2 has a pre-registration).
Study 1: all 200 rows kept (101 US, 99 India). Study 4: the deposit's 153 rows less 5 with no
answer to either question (blank in every column but the authors' mean-centred index): 148,
the N behind the answer key's 2.88 (1.75).

PERSONA. Age and gender. Study 1: age as typed (19-66; one blank), gender from `male`
(the .qsf recodes Male 1, Female 0; asserted). Study 4: age (the .qsf validates 16-100),
gender with the .qsf's labels (4 Male, 5 Female, 6 Non-binary/other). Ages outside the
.qsf's range would be left blank; none is.

JEV. scripts/recipe_prep.py reads .sav/.dta/.por only; this box has .csv and .xlsx, so it
does not apply. The assignment column is named as such in the codebook (AttCue), and the
persona labels are read from each .qsf's own choices.

ANSWER KEY. "Items means and sds for Studies 1-6.pdf", Table A1: Study 1 WTP 320.67 (162.45)
USD and 20106.39 (12252.44) INR; Study 4 relative cue diagnosticity 2.88 (1.75), the mean of
impt and relv. tests/test_gen_researchbox108.py recomputes all three from the BUILT rows.

    uv run python scripts/gen_researchbox108.py --prep   # code the data
    uv run python scripts/gen_researchbox108.py          # write the recipes
    uv run python scripts/gen_researchbox108.py --check  # exit 1 if any recipe differs
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
import yaml

REPO = Path(__file__).resolve().parents[1]
STUDY_ID = "researchbox108"
RAW = REPO / "data" / "raw" / STUDY_ID
MATERIALS = RAW / "Materials"
DATA = RAW / "Data"
CODEBOOK = RAW / "Codebook"
RECIPES = REPO / "recipes"
LICENCE = (
    'CC BY 4.0, stated on the box page https://researchbox.org/108 ("All content posted '
    'to ResearchBox is under a CC By 4.0 License"). Read 19 Nov 2026.'
)
PAPER = (
    'Barnes AJ, Shavitt S (2024), "Top Rated or Best Seller? Cultural Differences in '
    'Responses to Attitudinal versus Behavioral Consensus Cues", Journal of Consumer '
    "Research 51(2):276-297, doi:10.1093/jcr/ucad074. ResearchBox 108 "
    "(https://researchbox.org/108)."
)

QSF = {
    "study1_us": "Study 1 - US.qsf",
    "study1_india": "Study 1 - India.qsf",
    "study4": "Study 4 materials.qsf",
}

# Every <img> tag in every .qsf of the box: 57.
PICTURE_COUNT = {
    "Study 1 - India.qsf": 1,
    "Study 1 - US.qsf": 1,
    "Study 2.qsf": 3,
    "Study 3.qsf": 14,
    "Study 4 materials.qsf": 19,
    "Study 5 culture measure survey.qsf": 1,
    "Study 5 main survey.qsf": 4,
    "WA F Study.qsf": 14,
    "WA I Study.qsf": 0,
}

# In-flow pictures of the built studies, all judged decorative: (export tag, graphic id).
DECORATIVE = {
    "study1_us": {("Q16", "IM_4JdL2Urh7IFjsXj")},  # the community ladder (subjective status)
    "study1_india": {("Q16", "IM_4JdL2Urh7IFjsXj")},
    "study4": {("Q194", "IM_7P9Qx7SaoRGp22V")},  # the signature on the consent letter
}

NOT_BUILT = {
    "study2": "Neutron Mobile: each cue screen's picture (IM_9Su5Od74WcnWR0N, "
    "IM_7QFxJQMVxyug0jH) carries the cue itself, a 'TOP RATED' or 'BEST SELLING' banner, "
    "over the brand's logo (materials PDF p. 4-5). rich's picture rule.",
    "study3": "Starbucks: each cue screen's picture (IM_0pnNQyoeN0GvvYG, IM_ey4bZPWRxMpWSvY) "
    "is a Starbucks cup with a 'TOP RATED' or 'BEST SELLER' banner (materials PDF p. 8). "
    "rich's picture rule.",
    "study5": "ENZO headphones: every cue screen is a product photograph (the control one too), "
    "the cue arms with a 'BUYER'S CHOICE'-style banner, and the product information screen "
    "is only a picture whose attributes are printed words (materials PDF p. 11-13). rich's "
    "picture rule.",
    "wa_f": "Starbucks again: the same two cue pictures as Study 3 (acc, bcc). rich's "
    "picture rule.",
    "wa_i": "Spontaneous inference: the only question is free text; the numeric columns are "
    "research assistants' codes of it, not answers anyone gave.",
    "study6": "Amazon: product listings (ratings, best-seller ranks, prices), no respondents.",
}

# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

_TYPO = {"\xa0": " ", "​": "", "’": "'", "‘": "'", "“": '"', "”": '"'}


def norm(raw: str) -> str:
    """HTML to one line of plain text. Typography only."""
    s = re.sub(r"(?i)<br\s*/?>|</p>|</div>", " ", raw or "")
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    for a, b in _TYPO.items():
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------------------
# The questionnaires
# ---------------------------------------------------------------------------


class Survey:
    """A .qsf, read through its flow: only questions a respondent could meet."""

    def __init__(self, filename: str) -> None:
        self.raw = (MATERIALS / filename).read_text()
        d = json.loads(self.raw)
        self.entry: dict[str, Any] = d["SurveyEntry"]
        els = d["SurveyElements"]
        by_id = {e["Payload"]["QuestionID"]: e["Payload"] for e in els if e["Element"] == "SQ"}
        blocks: dict[str, dict[str, Any]] = {}
        for e in els:
            if e["Element"] == "BL":
                p = e["Payload"]
                for b in p.values() if isinstance(p, dict) else p:
                    blocks[b["ID"]] = b
        self.blocks = blocks
        self.flow: dict[str, Any] = next(e for e in els if e["Element"] == "FL")["Payload"]
        self.in_flow: list[dict[str, Any]] = []
        self.randomizers: list[dict[str, Any]] = []

        def walk(n: dict[str, Any]) -> None:
            if n.get("Type") == "BlockRandomizer":
                self.randomizers.append(n)
            if n.get("Type") in ("Block", "Standard", "Default"):
                for x in blocks[n["ID"]].get("BlockElements", []):
                    if x["Type"] == "Question":
                        self.in_flow.append(by_id[x["QuestionID"]])
            for c in n.get("Flow", []):
                walk(c)

        walk(self.flow)
        self.all = list(by_id.values())

    def q(self, tag: str) -> dict[str, Any]:
        """The ONE in-flow question with this export tag."""
        (p,) = [p for p in self.in_flow if p["DataExportTag"] == tag]
        return p

    def text(self, tag: str) -> str:
        return norm(self.q(tag)["QuestionText"])

    def pictures_in_flow(self) -> set[tuple[str, str]]:
        out = set()
        for p in self.in_flow:
            for im in re.findall(r"IM_\w+", json.dumps(p)):
                out.add((p["DataExportTag"], im))
        return out


def check_pictures() -> None:
    """57 tags in all; the built studies' in-flow pictures are exactly the decorative ones."""
    for f, n in PICTURE_COUNT.items():
        assert (MATERIALS / f).read_text().count("<img") == n, f
    assert sum(PICTURE_COUNT.values()) == 57
    assert sorted(p.name for p in MATERIALS.glob("*.qsf")) == sorted(PICTURE_COUNT)
    for tag, f in QSF.items():
        assert Survey(f).pictures_in_flow() == DECORATIVE[tag], tag


def slider(sv: Survey, tag: str) -> tuple[int, int, str]:
    """(min, max, its one row label) for a whole-number forced slider."""
    q = sv.q(tag)
    assert (q["QuestionType"], q["Selector"]) == ("Slider", "HSLIDER"), tag
    c = q["Configuration"]
    assert c["NumDecimals"] == "0" and not c["SnapToGrid"], tag
    assert q["Validation"]["Settings"]["ForceResponse"] == "ON", tag
    assert list(q["Choices"]) == ["1"] and not q.get("Labels"), tag
    return int(c["CSSliderMin"]), int(c["CSSliderMax"]), norm(q["Choices"]["1"]["Display"])


def six_point(sv: Survey, tag: str) -> dict[str, Any]:
    """A 1-6 horizontal scale with labelled ends, codes as the .qsf has them."""
    q = sv.q(tag)
    assert (q["QuestionType"], q["Selector"]) == ("MC", "SAHR"), tag
    order = [str(k) for k in q["ChoiceOrder"]]
    assert order == [str(i) for i in range(1, 7)] and not q.get("RecodeValues"), tag
    labels = [norm(q["Choices"][k]["Display"]) for k in order]
    assert all(lab == "" for lab in labels[1:-1]), labels
    return {"min": 1, "max": 6, "min_label": labels[0], "max_label": labels[-1]}


def gender_labels(sv: Survey, tag: str) -> dict[int, str]:
    q = sv.q(tag)
    assert q["QuestionType"] == "MC", tag
    recode = q.get("RecodeValues") or {}
    return {int(recode.get(k, k)): norm(v["Display"]) for k, v in q["Choices"].items()}


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
    persona: str


WTP_Q = "How much would be willing to pay for a Laplet?"
CURRENCY = {"study1_us": ("U.S.", "USD"), "study1_india": ("India", "Rupee")}


def study1(name: str) -> Experiment:
    sv = Survey(QSF[name])
    assert sv.entry["SurveyLanguage"] == "EN"
    assert all(not p.get("Language") for p in sv.all), name  # no translation anywhere
    (rand,) = sv.randomizers
    assert rand["SubSet"] == 1 and rand["EvenPresentation"], name
    shown = [sv.blocks[b["ID"]]["Description"] for b in rand["Flow"]]
    assert shown == ["love", "buy"], shown
    love, buy = sv.text("love"), sv.text("buy")
    assert love.replace(", love the brand.", ", buy the brand.") == buy  # only the verb differs
    market, unit = CURRENCY[name]
    assert f"first few months in the {market} market" in love
    lo, hi, label = slider(sv, "Q5")
    assert sv.text("Q5") == WTP_Q and label == unit
    added = f'Answer on the slider labelled "{unit}".'
    sample = "US" if name == "study1_us" else "India"
    return Experiment(
        name=name,
        title=f"A new tablet that doubles as a laptop: 85% of consumers in the {market} market "
        f"who learn about it love it, or buy it; how much would you pay? (Study 1, {sample} "
        "sample)",
        kind="version",
        factors=["cue"],
        arms=[
            Arm(1, {"cue": "attitudinal"}, love),
            Arm(2, {"cue": "behavioural"}, buy),
        ],
        outcomes=[Outcome("wtp", f"{WTP_Q} {added}", {"min": lo, "max": hi})],
        notes=f"Study 1, the {sample} sample ({QSF[name]}; the .qsf is in English). Between "
        "people: 85% of consumers who learn about Laplet love it (attitudinal cue) or buy it "
        f"(behavioural cue); then a slider from {lo} to {hi}, whole numbers, forced. The "
        f"slider's one row label is \"{unit}\", the currency; the sentence '{added}' is OURS, "
        "added so the row says what the number is (CONVENTIONS: one stem, several labelled "
        "answer fields; the label is the source's, quoted). The question's missing 'you' is "
        "the source's. Not built: race, subjective status and an open-ended question on "
        "brand loyalty.",
        persona="age as typed and gender from the deposit's `male` (the .qsf recodes Male 1, "
        "Female 0)",
    )


IMPT_Q = "Which of these criteria do you think is more important to consider?"


def study4() -> Experiment:
    sv = Survey(QSF["study4"])
    assert not sv.randomizers
    impt = sv.text("impt")
    assert impt.endswith(" " + IMPT_Q), impt
    scenario = impt[: -len(IMPT_Q) - 1]
    relv_q = sv.text("relv")
    asked = f'You were asked "{IMPT_Q}"'
    # impt and relv are on consecutive pages of one block, in that order
    (block,) = [
        b
        for b in sv.blocks.values()
        if any(x.get("QuestionID") == sv.q("impt")["QuestionID"] for x in b["BlockElements"])
    ]
    seq = [x.get("QuestionID") if x["Type"] == "Question" else "PB" for x in block["BlockElements"]]
    assert seq == [sv.q("impt")["QuestionID"], "PB", sv.q("relv")["QuestionID"]], seq
    return Experiment(
        name="study4",
        title='Shopping online for headphones, some labelled "Top Rated" and some "Best '
        'Seller": which label matters more? (Study 4)',
        kind="baseline",
        factors=[],
        arms=[Arm(1, {}, scenario, {1: {"condition_text": f"{scenario}\n\n{asked}"}})],
        outcomes=[
            Outcome("impt", IMPT_Q, six_point(sv, "impt")),
            Outcome("relv", relv_q, six_point(sv, "relv")),
        ],
        notes="Study 4 (its .qsf created Feb 2023), 148 people: the deposit's 153 rows less 5 that answered "
        "neither question (both were optional). No manipulation, so one condition: everyone "
        "read the same scenario and answered two questions on consecutive pages in a fixed "
        "order, which question is more important, then more relevant, 1 to 6 with the ends "
        "labelled. The second row narrates the first question as asked, in words of OURS: "
        f"'{asked}'. Not built: the 16 culture items asked before the scenario (a measured "
        "moderator) and race (select all that apply). The .qsf also holds, outside the "
        "survey flow, copies of both questions with the ends reversed; the in-flow ones are "
        "used, and the codebook's direction agrees.",
        persona="age (the .qsf validates 16-100) and gender, labels from the .qsf's own choices",
    )


def experiments() -> list[Experiment]:
    return [study1("study1_us"), study1("study1_india"), study4()]


# ---------------------------------------------------------------------------
# Coded data
# ---------------------------------------------------------------------------

N = {"study1_us": 101, "study1_india": 99, "study4": 148}


def data_file(tag: str) -> str:
    return f"{STUDY_ID}_{tag}.csv"


def read_deposit(tag: str) -> pd.DataFrame:
    """The deposit's file as it is, with each row's number (1-based) as `row`."""
    if tag.startswith("study1"):
        df = pd.read_excel(DATA / "Study 1 data.xlsx")
    else:
        df = pd.read_csv(DATA / "Study 4 data.csv")
    df.insert(0, "row", range(1, len(df) + 1))
    return df


def _age(s: pd.Series, lo: int, hi: int) -> pd.Series:
    age = pd.to_numeric(s, errors="coerce")
    return age.where(age.between(lo, hi)).round().astype("Int64")


def prep(tag: str) -> pd.DataFrame:
    """One coded row per kept person."""
    df = read_deposit(tag)
    if tag.startswith("study1"):
        assert len(df) == 200 and set(df["INDIA"]) == {0, 1} and set(df["AttCue"]) == {0, 1}
        df = df[df["INDIA"] == (1 if tag == "study1_india" else 0)].reset_index(drop=True)
        sv = Survey(QSF[tag])
        lo, hi, _ = slider(sv, "Q5")
        out = pd.DataFrame({"pid": [f"study1_{r}" for r in df["row"]]})
        out["arm"] = df["AttCue"].map({1: 1, 0: 2}).values
        wtp = df["WTP_raw"]
        assert (wtp == wtp.round()).all() and wtp.between(lo, hi).all(), tag
        out["wtp"] = wtp.astype(int).values
        out["age"] = _age(df["age"], 18, 100).values
        labels = gender_labels(sv, "Q10")
        assert labels == {1: "Male", 0: "Female"}, labels
        out["gender"] = [labels[int(g)] for g in df["male"]]
    else:
        sv = Survey(QSF["study4"])
        blank = df["impt"].isna() & df["relv"].isna()
        assert blank.sum() == 5
        others = df.drop(columns=["row", "tgmc"])
        assert others[blank].isna().all(axis=None)  # nothing answered at all
        df = df[~blank].reset_index(drop=True)
        assert df[["impt", "relv"]].notna().all(axis=None)
        out = pd.DataFrame({"pid": [f"study4_{r}" for r in df["row"]]})
        out["arm"] = 1
        for c in ("impt", "relv"):
            assert df[c].between(1, 6).all() and (df[c] == df[c].round()).all()
            out[c] = df[c].astype(int).values
        out["age"] = _age(df["age"], 16, 100).values
        labels = gender_labels(sv, "Q1020")
        assert labels == {4: "Male", 5: "Female", 6: "Non-binary/other"}, labels
        out["gender"] = [labels[int(g)] if pd.notna(g) else None for g in df["gender"]]
    assert len(out) == N[tag], (tag, len(out))
    return out


def check_codebook() -> None:
    """The codebook names the columns the coding reads, with the meanings it assumes."""
    b1 = pd.read_csv(CODEBOOK / "Study 1 data.xlsx___CODEBOOK.csv").set_index("varname")
    assert "0=US, 1=India" in b1.loc["INDIA", "description"]
    assert "1=attitudinal, 0=behavioral" in b1.loc["AttCue", "description"]
    assert "1=male, 0=female" in b1.loc["male", "description"]
    b4 = pd.read_csv(CODEBOOK / "Study 4 data.csv___CODEBOOK.csv").set_index("varname")
    assert (
        "higher values = behavioral consensus cues more diagnostic" in (b4.loc["dv", "description"])
    )
    assert b4.loc["gender", "description"] == "4=male, 5=female, 6=non-binary/other"


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
        f"{PAPER}\n\nGENERATED by scripts/gen_researchbox108.py; every judgement is in its "
        f"docstring. {e.notes} The deposit has no pre-registration for this study (only "
        "Study 2 has one), and every person with an answer is kept.\n\nWording from "
        f"{QSF[e.name]}, read through the survey flow. Every picture in the flow is "
        "decorative (listed in the generator) and none is on the condition's or the "
        "outcome's screen. Typography normalised (HTML entities, non-breaking spaces). "
        f"Persona: {e.persona}."
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
        check_pictures()
        check_codebook()
        for tag in QSF:
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
