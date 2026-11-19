#!/usr/bin/env python3
"""Write recipes/researchbox231_*.yaml: payment frequency in a life simulator (9 recipes).

De La Rosa W & Tully SM (2022), "The Impact of Payment Frequency on Consumer Spending and
Subjective Wealth Perceptions", Journal of Consumer Research 48(6), doi:10.1093/jcr/ucab052.
ResearchBox 231 (https://researchbox.org/231), CC BY 4.0 ("All content posted to
ResearchBox is under a CC By 4.0 License", the box page). US online samples (Prolific and
MTurk, 2019-2021), US dollars and a US checking account; kept as the source has them.

Every judgement is here, in code, so the recipes can be re-derived and reviewed.

HOW THE SCREENS ARE GOT. Each study is a Qualtrics survey whose screens are filled from
embedded data: a balance is `$e{ e://Field/Money + e://Field/MoneyP }`, a screen is shown
only when `Condition = day`, a passive month is a loop-and-merge block. `Walk` replays the
survey flow for one arm: it takes the randomizer branch whose embedded data match the arm,
does the flow's own arithmetic, follows every branch and display condition that reads
embedded data, renders each block's text-only questions with their pipes filled, and stops
at the target question. It refuses (raises) on anything it does not model: a branch on a
respondent's answer that does anything but end the survey, an answerable question before
the target that is not on the declared skip list, a randomizer it cannot match. Branches on
an answer that only end the survey (consent refused, attention or bot check failed, a listed
Prolific id) are passed over, since every kept respondent got past them. Each test checks
that every balance shown equals the previous one plus the screen's income or expense.

WHAT IS BUILT, AND WHY ONLY THAT.
- Studies 3 and 4 (subjective wealth, prediction uncertainty): the simulation is passive
  (28 screens of the arm's fixed loop values, no choices), so every respondent in an arm
  saw the same screens. Built: 6 wealth and 4 uncertainty sliders, two recipes per study
  because the scale labels differ. The uncertainty rows add, after the simulation, the
  clause "You were then asked these questions, shown in a random order:" (ours) and the six
  wealth questions word-for-word (CONVENTIONS, "Narrating what the respondent did").
- Studies 2, 5, S1, S2, S3 (life simulator with spending choices): only the FIRST decision.
  Every later screen states a result and a balance that follow from the respondent's own
  earlier choices, so a later decision's condition is not shared by an arm; it would be
  one condition per path and would have to state each person's earlier answers as given.
  The end-of-study questions (subjective wealth etc.) sit after the whole path and fail
  for the same reason. The decision page showed a balance box beneath the question; it
  is placed after the clause "Beneath the question below, the same screen showed:" (ours).
  Options are listed in the .qsf's order (no choice randomisation); the answer is coded to
  that position from the deposit's dollar amount, through the .qsf's own recodes.

NOT BUILT.
- Study 6 (Instant Pay): in the access arm, an Instant Pay choice comes before the first
  spending decision and changes the balance it shows, so that arm has no shared
  condition; the no-access arm alone is not a contrast.
- Supplemental Study 4 (expense listing): every rating pipes the respondent's own free-text
  list onto the screen ("Please read over your response ... ${q://QID16/...}"), which no
  arm can carry; the listing itself is free text, coded by the authors.
- Pictures: the only <img> tags on live screens are S4's payday calendars (S4 not built)
  and Study 5's pictorial mood scales (Self-Assessment Manikin; the options are pictures),
  which come after the path and are not built. Studies 3 and 4's calendars are in the trash.

DROPPED FROM CONDITIONS. Consent, captcha, attention and bot checks (survey mechanics);
the TRUE/FALSE items restating the instructions and Studies 3-4's "how often / how much were
you paid" items (comprehension and recall checks, CONVENTIONS); Study 5's eligibility
notice; page timers.

AS THE SOURCE HAS IT. "You also spent $-76" and "$0 is deposited" (Studies 3-4, weekly
arm) are the screens' own renderings. In S3 the daily arm's Sunday screen says "You get
paid $1,400 every two weeks (Fridays)." exactly as the biweekly arm's does (QID22, shown
when Condition = day); kept and flagged (ledger 156). S2's income randomizer has only the
Low branch, so the $280 / $1400 wording was never assigned.

EXCLUSIONS reproduce each paper N (Studies 2-5) or the pre-registered rule (S1, S3; S2 by
the same rule): failed attention or recall checks, and those who said they had taken part
before. Age outside 18-100 is left blank in the persona; the person is kept.

JEV. scripts/recipe_prep.py reads .sav/.dta only and has no ResearchBox source, so it does
not apply to these CSVs; the assignment columns are named as such in the codebooks
("IV: CONDITION"), and persona labels are read from each .qsf's own choices.

    uv run python scripts/gen_researchbox231.py --prep   # (re)write the coded .csv files
    uv run python scripts/gen_researchbox231.py          # write the recipes
    uv run python scripts/gen_researchbox231.py --check  # exit 1 if any recipe differs
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
STUDY_ID = "researchbox231"
RAW = REPO / "data" / "raw" / STUDY_ID
MATERIALS = RAW / "Materials"
DATA_DIR = RAW / "Data"
RECIPES = REPO / "recipes"
LICENCE = (
    'CC BY 4.0, stated on the box page https://researchbox.org/231 ("All content posted '
    'to ResearchBox is under a CC By 4.0 License"). Read 19 Nov 2026.'
)
PAPER = (
    'De La Rosa W & Tully SM (2022), "The Impact of Payment Frequency on Consumer Spending '
    'and Subjective Wealth Perceptions", Journal of Consumer Research 48(6), '
    "doi:10.1093/jcr/ucab052. ResearchBox 231 (https://researchbox.org/231)."
)

QSF = {
    "2": "Study_2_-_Life_Simulator_Daily_v_Weekly_w_Overdraft.qsf",
    "3": "Study_3_-_Subjective_Wealth_Mediation_Study.qsf",
    "4": "Study_4_-_Subjective_Wealth_2_Pay_Frequency_x_2_Expense_Frequency.qsf",
    "5": "Study_5_-_Life_Simulator_Daily_v_Biweekly_28_Questions.qsf",
    "6": "Study_6_-_Life_Simulator_Daily_Access_vs_Weekly.qsf",
    "S1": "Supplemental_Study_1_-_Life_Simulator_Daily_vs_Weekly.qsf",
    "S2": "Supplemental_Study_2_-_Life_Simulator_Daily_vs_Weekly_w_no_constraints.qsf",
    "S3": "Supplemental_Study_3_-_Life_Simulator_Daily_vs_Biweekly.qsf",
    "S4": "Supplemental_Study_4_-_Expense_Elaboration.qsf",
}

_TYPO = {"\xa0": " ", "\u200b": "", "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"'}


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


def load_qsf(tag: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((MATERIALS / QSF[tag]).read_text())
    return data


class Survey:
    def __init__(self, tag: str) -> None:
        self.tag = tag
        q = load_qsf(tag)
        els = q["SurveyElements"]
        self.qs = {e["Payload"]["QuestionID"]: e["Payload"] for e in els if e["Element"] == "SQ"}
        self.blocks: dict[str, dict[str, Any]] = {}
        for e in els:
            if e["Element"] == "BL":
                p = e["Payload"]
                for b in p.values() if isinstance(p, dict) else p:
                    self.blocks[b["ID"]] = b
        self.flow = next(e for e in els if e["Element"] == "FL")["Payload"]


class StopWalkError(Exception):
    """Raised to unwind the walk once the target's page is complete."""


class Walk:
    """Replays a survey flow for one arm, collecting the screens shown, up to `stop`."""

    def __init__(self, sv: Survey, arm: dict[str, str], stop: str, skip: set[str]) -> None:
        self.sv, self.arm, self.stop, self.skip = sv, arm, stop, skip
        self.ed: dict[str, str] = {}
        self.screens: list[str] = []
        self.target: dict[str, Any] | None = None
        self.after: list[str] = []  # text on the target's own page, beneath it
        self.also: list[str] = []  # other questions on the target's own page

    def pipe(self, text: str, lm: dict[str, str] | None = None) -> str:
        def ef(m: re.Match[str]) -> str:
            return self.ed[m.group(1)]

        text = re.sub(r"\$\{e://Field/([A-Za-z0-9_]+)\}", ef, text)
        if lm is not None:
            text = re.sub(r"\$\{lm://Field/(\d+)\}", lambda m: lm[m.group(1)], text)
        assert "${" not in text, text
        return text

    def value(self, v: str) -> str:
        m = re.fullmatch(r"\$e\{(.*)\}", v.strip())
        if not m:
            return self.pipe(v)
        # Every expression in these flows is a sum of fields: "e://Field/A + e://Field/B".
        terms = re.fullmatch(r"\s*e://Field/(\w+)((?:\s*[+-]\s*e://Field/\w+)*)\s*", m.group(1))
        assert terms, v
        r = float(self.ed[terms.group(1)])
        for sign, name in re.findall(r"([+-])\s*e://Field/(\w+)", terms.group(2)):
            r += float(self.ed[name]) * (1 if sign == "+" else -1)
        return str(int(r)) if r == int(r) else str(r)

    def cond(self, c: dict[str, Any]) -> bool:
        if c["LogicType"] != "EmbeddedField":
            raise ValueError(f"{self.sv.tag}: unsupported logic {c['LogicType']}")
        left = self.ed.get(c["LeftOperand"], "")
        right = c.get("RightOperand", "")
        op = c["Operator"]
        if op == "EqualTo":
            return left == right
        if op == "NotEqualTo":
            return left != right
        lv, rv = float(left), float(right)
        return {
            "LessThan": lv < rv,
            "GreaterThan": lv > rv,
            "GreaterThanOrEqual": lv >= rv,
            "LessThanOrEqual": lv <= rv,
        }[op]

    def logic(self, bl: dict[str, Any]) -> bool:
        result: bool | None = None
        for k in sorted((k for k in bl if k.isdigit()), key=int):
            group = bl[k]
            gres: bool | None = None
            for kk in sorted((x for x in group if x.isdigit()), key=int):
                c = group[kk]
                v = self.cond(c)
                conj = c.get("Conjuction", "And")
                gres = v if gres is None else (gres and v if conj == "And" else gres or v)
            conj = group.get("Conjuction", "Or")
            assert gres is not None
            result = (
                gres if result is None else (result and gres if conj == "And" else result or gres)
            )
        assert result is not None
        return result

    def run(self) -> None:
        try:
            self.node(self.sv.flow)
        except StopWalkError:
            return
        raise ValueError(f"{self.sv.tag}: never reached {self.stop}")

    def node(self, f: dict[str, Any]) -> None:
        t = f["Type"]
        if t == "Root":
            for c in f["Flow"]:
                self.node(c)
        elif t == "EmbeddedData":
            for e in f["EmbeddedData"]:
                # A field set with no value is empty on screen (Study 6's Wording0).
                v = e.get("Value")
                self.ed[e["Field"]] = "" if v is None else self.value(str(v))
        elif t in ("BlockRandomizer", "Randomizer"):
            hits = [c for c in f["Flow"] if c["Type"] == "EmbeddedData" and self.matches(c)]
            assert len(hits) == 1, (self.sv.tag, "randomizer", len(hits))
            self.node(hits[0])
        elif t == "Branch":
            conds = [
                c
                for g in f["BranchLogic"].values()
                if isinstance(g, dict)
                for c in g.values()
                if isinstance(c, dict)
            ]
            if any(c["LogicType"] != "EmbeddedField" for c in conds):
                # consent refused, attention or bot check failed, or a listed
                # Prolific id: every such branch only ends the survey.
                assert all(c["Type"] == "EndSurvey" for c in f["Flow"]), f
                return
            if any(c["LeftOperand"] in ("exclude",) for c in conds):
                assert all(c["Type"] == "EndSurvey" for c in f["Flow"]), f
                return
            if self.logic(f["BranchLogic"]):
                for c in f["Flow"]:
                    self.node(c)
        elif t in ("Standard", "Block"):
            self.block(self.sv.blocks[f["ID"]])
        elif t == "EndSurvey":
            raise ValueError(f"{self.sv.tag}: reached EndSurvey before {self.stop}")
        else:
            raise ValueError(f"{self.sv.tag}: unsupported flow element {t}")

    def matches(self, c: dict[str, Any]) -> bool:
        vals = {e["Field"]: str(e.get("Value")) for e in c["EmbeddedData"]}
        return all(vals.get(k) == v for k, v in self.arm.items() if k in vals) and any(
            k in vals for k in self.arm
        )

    def block(self, b: dict[str, Any]) -> None:
        opts = b.get("Options", {})
        loop = opts.get("Looping") not in (None, "None")
        iters: list[dict[str, str] | None] = [None]
        if loop:
            st = opts["LoopingOptions"]["Static"]
            iters = [st[k] for k in sorted(st, key=int)]
        for lm in iters:
            page: list[str] = []
            for be in b.get("BlockElements", []):
                if be["Type"] == "Page Break":
                    if self.target is not None:
                        raise StopWalkError
                    if page:
                        self.screens.append("\n".join(page))
                    page = []
                    continue
                qid = be["QuestionID"]
                q = self.sv.qs[qid]
                dl = q.get("DisplayLogic")
                if dl and not self.logic(dl):
                    continue
                if self.target is not None:  # the rest of the target's page
                    if qid in self.skip or q["QuestionType"] == "Timing":
                        continue
                    if q["QuestionType"] == "DB":
                        self.after.append(lines(self.pipe(q["QuestionText"], lm)))
                    else:
                        self.also.append(qid)
                    continue
                if qid == self.stop:
                    if page:
                        self.screens.append("\n".join(page))
                    page = []
                    self.target = q
                    continue
                if qid in self.skip or q["QuestionType"] == "Timing":
                    continue
                if q["QuestionType"] != "DB":
                    raise ValueError(f"{self.sv.tag}: answerable {qid} before {self.stop}")
                page.append(lines(self.pipe(q["QuestionText"], lm)))
            if self.target is not None:
                raise StopWalkError
            if page:
                self.screens.append("\n".join(page))


def screens_to(
    tag: str,
    arm: dict[str, str],
    stop: str,
    skip: set[str] = frozenset(),  # type: ignore[assignment]
) -> Walk:
    w = Walk(Survey(tag), arm, stop, set(skip) | SKIP_ALWAYS[tag])
    w.run()
    return w


# Questions passed over on the way to a target, per study, with the reason.
# Consent, captcha, bot and attention checks are survey mechanics; the TRUE/FALSE
# items restate the instructions back to the respondent (comprehension checks,
# CONVENTIONS "Attention and recall checks are not outcomes"); Study 5's QID570
# is an eligibility screener ("If you believe you may have taken part ...").
SKIP_ALWAYS: dict[str, set[str]] = {
    "2": {"QID3", "QID234", "QID236", "QID235"},
    "3": {"QID15", "QID316", "QID317"},
    "4": {"QID15", "QID316", "QID317"},
    "5": {"QID427", "QID3", "QID421", "QID570", "QID234", "QID236", "QID419"},
    "S1": {"QID3"},
    "S2": {"QID571", "QID3", "QID234", "QID562", "QID236"},
    "S3": {"QID3", "QID234", "QID236"},
}


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

DATA_FILES = {
    "2": "Raw Data_Research Box.csv",
    "3": "Study 3 Raw Data_Research Box.csv",
    "4": "Study 4 Raw Data_Research Box.csv",
    "5": "Study 5 Raw Data_Research Box.csv",
    "S1": "Supplemental Study 1 Raw Data_Research Box.csv",
    "S2": "Supplemental Study 2 Raw Data_Research Box.csv",
    "S3": "Supplemental Study 3 - Raw Data_Research Box.csv",
}
# Exclusions, as the paper (Studies 2-5) and the pre-registrations (S1-S3) state
# them: (column prefix, value that EXCLUDES), and the N that results.
EXCLUDE: dict[str, tuple[list[tuple[str, int]], int]] = {
    "2": ([("Attention Check", 0)], 401),
    "3": ([("Have you previously", 1), ("Check 1", 0), ("Check 2", 0), ("Check 3", 0)], 112),
    "4": ([("Have you previously", 1), ("Check 1", 0), ("Check 2", 0), ("Check 3", 0)], 528),
    "5": ([("Attention Check", 0), ("Do you believe", 1)], 1120),
    "S1": ([("Attention Check", 0)], 146),
    "S2": ([("Attention Check", 0), ("Have you participated", 1)], 402),
    "S3": ([("Attention Check", 0), ("Have you previously", 1)], 404),
}
AGE_RANGE = (18, 100)


def col(df: pd.DataFrame, prefix: str) -> str:
    hits = [c for c in df.columns if c.strip().startswith(prefix)]
    assert len(hits) == 1, (prefix, hits)
    return hits[0]


def read_study(tag: str) -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / DATA_FILES[tag], encoding="utf-8-sig")
    rules, n = EXCLUDE[tag]
    for prefix, bad in rules:
        c = col(df, prefix)
        assert df[c].notna().all(), (tag, c)
        df = df[df[c] != bad]
    assert len(df) == n, f"{tag}: {len(df)} rows after exclusions, expected {n}"
    return df.reset_index(drop=True)


def live_questions(sv: Survey) -> dict[str, dict[str, Any]]:
    """Questions in blocks that are not the trash."""
    keep: set[str] = set()
    for b in sv.blocks.values():
        if b.get("Type") != "Trash":
            keep |= {e["QuestionID"] for e in b.get("BlockElements", []) if "QuestionID" in e}
    return {k: v for k, v in sv.qs.items() if k in keep}


def demographic(tag: str, kind: str) -> dict[str, Any] | None:
    pats = {
        "gender": r"What is your gender\?",
        "age": r"What is your age\?",
        "income": r"What's your household income\?",
        "education": r"What('s| is) (the |your )(highest level of education|education)",
    }
    hits = [
        q
        for q in live_questions(Survey(tag)).values()
        if re.match(pats[kind], norm(q["QuestionText"]))
    ]
    assert len(hits) <= 1, (tag, kind, len(hits))
    return hits[0] if hits else None


def choice_labels(q: dict[str, Any]) -> dict[int, str]:
    """Exported code -> the label on screen, through the .qsf's own recodes."""
    rec = q.get("RecodeValues") or {}
    return {int(rec.get(k, k)): norm(v["Display"]) for k, v in q["Choices"].items()}


DEMO_COLS = {
    "gender": ("What is your gender?", "Gender"),
    "age": ("What is your age?", "Age"),
    "income": ("What's your household income?", "Income"),
    "education": ("What", "Education"),
}


def demo_col(df: pd.DataFrame, kind: str) -> str:
    if kind == "education":
        hits = [c for c in df.columns if "education" in c.lower()]
        assert len(hits) == 1, hits
        return hits[0]
    a, b = DEMO_COLS[kind]
    for c in (a, b):
        if c in df.columns:
            return c
    raise KeyError((kind, list(df.columns)))


def persona_cols(tag: str, df: pd.DataFrame) -> pd.DataFrame:
    age = pd.to_numeric(df[demo_col(df, "age")], errors="coerce")
    out = pd.DataFrame({"age": age.where(age.between(*AGE_RANGE)).astype("Int64")})
    for kind in ("gender", "income", "education"):
        q = demographic(tag, kind)
        if q is None:
            continue
        labels = choice_labels(q)
        raw = pd.to_numeric(df[demo_col(df, kind)], errors="coerce")
        assert set(raw.dropna().astype(int)) <= set(labels), (tag, kind)
        out[kind] = raw.map(lambda v, lab=labels: lab[int(v)] if pd.notna(v) else None)
    return out


# ---------------------------------------------------------------------------
# The experiments
# ---------------------------------------------------------------------------


@dataclass
class Arm:
    code: int
    factors: dict[str, str]
    walk: dict[str, str]  # the embedded data the survey's randomizer set for this arm
    text: str = ""


@dataclass
class Outcome:
    var: str
    qid: str
    question: str
    scale: dict[str, Any]


@dataclass
class Experiment:
    name: str
    tag: str
    title: str
    factor_vars: list[str]  # coded columns that hold the assignment
    factors: list[str]
    arms: list[Arm]
    outcomes: list[Outcome]
    notes: str
    rejected: dict[str, str] = field(default_factory=dict)


# Deposit assignment column -> {deposit value: coded value}, per study.
ASSIGN: dict[str, dict[str, tuple[str, dict[str, int]]]] = {
    "2": {"pay": ("Condition", {"day": 1, "week": 2})},
    "3": {"pay": ("Condition", {"Daily": 1, "Weekly": 2})},
    "4": {
        "pay": ("Pay Frequency", {"Daily": 1, "Weekly": 2}),
        "expense": ("Expense Frequency", {"Daily": 1, "Weekly": 2}),
    },
    "5": {"pay": ("Condition", {"Daily": 1, "Bi-Weekly": 2})},
    "S1": {"pay": ("Condition", {"day": 1, "week": 2})},
    "S2": {"pay": ("Condition", {"day": 1, "week": 2})},
    "S3": {"pay": ("Condition", {"day": 1, "bi-week": 2})},
}

DECISION_CLAUSE = "Beneath the question below, the same screen showed:"  # ours
EARLIER_CLAUSE = "You were then asked these questions, shown in a random order:"  # ours


def opt_question(question: str, options: list[str]) -> str:
    listed = "; ".join(f'{i} means "{o}"' for i, o in enumerate(options, 1))
    return f"{question}\n{listed}."


def decision_options(q: dict[str, Any]) -> list[tuple[str, int, str]]:
    """(choice key, dollar recode, label) in on-screen order; the order is fixed."""
    assert not q.get("Randomization") or q["Randomization"].get("Type") in (None, "None"), q
    return [
        (k, int(q["RecodeValues"][k]), norm(q["Choices"][k]["Display"]))
        for k in map(str, q["ChoiceOrder"])
    ]


def first_decision(
    tag: str, name: str, stop: str, arms: list[Arm], title: str, notes: str
) -> Experiment:
    question: str | None = None
    options: list[tuple[str, int, str]] | None = None
    for a in arms:
        w = screens_to(tag, a.walk, stop)
        assert w.target is not None and not w.also, (tag, w.also)
        assert len(w.after) == 1 and "Balance" in w.after[0], (tag, w.after)
        a.text = "\n\n".join(w.screens) + f"\n\n{DECISION_CLAUSE}\n" + w.after[0]
        q, o = lines(w.target["QuestionText"]), decision_options(w.target)
        assert question in (None, q) and options in (None, o), tag
        question, options = q, o
    assert question is not None and options is not None
    return Experiment(
        name=name,
        tag=tag,
        title=title,
        factor_vars=["pay"],
        factors=["pay_frequency"],
        arms=arms,
        outcomes=[
            Outcome(
                var="decision1",
                qid=stop,
                question=opt_question(question, [o[2] for o in options]),
                scale={"min": 1, "max": len(options), "nominal": True},
            )
        ],
        notes=notes,
    )


WEALTH = ["QID387", "QID407", "QID408", "QID409", "QID410", "QID412"]  # Subjective Wealth 1-6
EASE = ["QID416", "QID417", "QID418", "QID419"]  # Prediction Uncertainty 1-4


def slider(q: dict[str, Any]) -> dict[str, Any]:
    cfg = q["Configuration"]
    assert q["QuestionType"] == "Slider" and (cfg["CSSliderMin"], cfg["CSSliderMax"]) == (0, 100)
    assert cfg["NumDecimals"] == "0", q["QuestionID"]
    labels = [norm(v["Display"]) for _, v in sorted(q["Labels"].items(), key=lambda x: int(x[0]))]
    assert len(labels) == 2, labels
    return {"min": 0, "max": 100, "min_label": labels[0], "max_label": labels[1]}


def sim_arms(tag: str, arms: list[Arm]) -> None:
    """The simulation each arm watched, up to the first wealth question."""
    for a in arms:
        w = screens_to(tag, a.walk, WEALTH[0])
        assert sorted(w.also) == sorted(WEALTH[1:]) and not w.after, (tag, w.also)
        a.text = "\n\n".join(w.screens)
        # The ease page comes straight after the wealth page and nothing between.
        e = screens_to(tag, a.walk, EASE[0], set(WEALTH))
        assert "\n\n".join(e.screens) == a.text and sorted(e.also) == sorted(EASE[1:])


def wealth_study(tag: str, which: str, arms: list[Arm], title: str, notes: str) -> Experiment:
    sim_arms(tag, arms)
    qs = Survey(tag).qs
    if which == "wealth":
        outs = [
            Outcome(f"sw{i}", q, norm(qs[q]["QuestionText"]), slider(qs[q]))
            for i, q in enumerate(WEALTH, 1)
        ]
        name = f"study{tag}"
    else:
        earlier = "\n".join(f'"{norm(qs[q]["QuestionText"])}"' for q in WEALTH)
        for a in arms:
            a.text += f"\n\n{EARLIER_CLAUSE}\n{earlier}"
        outs = [
            Outcome(f"pu{i}", q, norm(qs[q]["QuestionText"]), slider(qs[q]))
            for i, q in enumerate(EASE, 1)
        ]
        name = f"study{tag}_ease"
    factors = ["pay_frequency"] + (["expense_frequency"] if tag == "4" else [])
    return Experiment(
        name=name,
        tag=tag,
        title=title,
        factor_vars=["pay"] + (["expense"] if tag == "4" else []),
        factors=factors,
        arms=arms,
        outcomes=outs,
        notes=notes,
    )


FIRST_ONLY = (
    "Only the FIRST spending decision is built. Every screen before it is the same for "
    "everyone in an arm, so its condition is fixed by the assignment. Every later screen "
    "shows a result and a balance that follow from the respondent's own earlier choices "
    '("You were late to work ...", "Alert: Your checking account balance is less than '
    '$0"), so no later decision, and no end-of-study question, has a condition shared by '
    "an arm: it would be one condition per path, stating each person's own earlier answers "
    "as given. Not built for that reason: {later}. The TRUE/FALSE items that restate the "
    "instructions are comprehension checks, dropped. Balances are those the survey flow's "
    "own embedded-data arithmetic produced for the arm (see the docstring). The decision "
    "screen showed a balance box beneath the question; it follows the added clause "
    f'"{DECISION_CLAUSE}" (ours). Options in the .qsf order, which was fixed.'
)


def pay_arms(tag: str, day: str, other: str, other_level: str, extra: dict[str, str]) -> list[Arm]:
    return [
        Arm(1, {"pay_frequency": "daily"}, {"Condition": day, **extra}),
        Arm(2, {"pay_frequency": other_level}, {"Condition": other, **extra}),
    ]


def study2() -> Experiment:
    return first_decision(
        "2",
        "study2",
        "QID8",
        pay_arms("2", "day", "week", "weekly", {}),
        "Life simulator: drinks with a friend after being paid daily or weekly (Study 2)",
        "Study 2, summer 2019. A five-week life simulator with a $35 overdraft fee: $850 "
        "to start, $650 rent, then a warehouse job paying $140 each weekday or $700 each "
        "Friday. "
        + FIRST_ONLY.format(later="14 further decisions and 4 subjective-wealth items")
        + " 401 of 405 kept (paper: 4 failed the attention check).",
    )


def study5() -> Experiment:
    return first_decision(
        "5",
        "study5",
        "QID231",
        pay_arms("5", "day", "week", "biweekly", {}),
        "Life simulator: rent with or without a cleaning fee, paid daily or every two weeks "
        "(Study 5)",
        "Study 5, winter 2020-21. A four-week life simulator, $875 to start, paid $140 "
        "each weekday or $1,400 every two weeks; a negative balance is deducted from the "
        "next paycheck. The first decision comes before any pay day in either arm, so "
        "the arms differ only in the stated pay schedule. "
        + FIRST_ONLY.format(
            later="27 further decisions, 6 subjective-wealth and 4 prediction-uncertainty "
            "items, planning, mood (pictorial scales), discounting and financial literacy"
        )
        + ' The first screen, an eligibility notice ("If you believe you may have taken '
        'part in a prior life simulation study ...") is survey mechanics, dropped. 1,120 '
        "of 1,200 kept (17 failed the attention check, 66 said they had taken the study "
        "before, 3 both; the paper's N).",
    )


def s1() -> Experiment:
    return first_decision(
        "S1",
        "s1",
        "QID8",
        pay_arms("S1", "day", "week", "weekly", {}),
        "Life simulator: drinks with a friend after being paid daily or weekly "
        "(Supplemental Study 1)",
        "Supplemental Study 1, 2019. As Study 2 but a negative balance is described as "
        "borrowing to be paid back, and the friend is Joe. "
        + FIRST_ONLY.format(later="13 further decisions")
        + " 146 of 149 kept (pre-registration: exclude failed attention checks).",
    )


def s2() -> Experiment:
    return first_decision(
        "S2",
        "s2",
        "QID332",
        pay_arms("S2", "day", "week", "weekly", {"Income": "Low"}),
        "Life simulator: a concert after being paid daily or weekly (Supplemental Study 2)",
        "Supplemental Study 2, 2020. $950 to start, $650 rent, paid $140 each weekday or "
        "$700 each Friday; no overdraft constraint is stated. The survey flow also has an "
        "income randomizer whose only branch is Low, so every respondent had the $140 / "
        "$700 wording (the $280 / $1400 wording is never assigned). "
        + FIRST_ONLY.format(later="14 further decisions")
        + " 402 of 431 kept (5 failed the attention check, 27 had taken a similar survey "
        "before, both by the rule the authors pre-registered for Studies 4-6 and S3; S2 "
        "has no pre-registration in the box).",
    )


def s3() -> Experiment:
    return first_decision(
        "S3",
        "s3",
        "QID8",
        pay_arms("S3", "day", "week", "biweekly", {}),
        "Life simulator: drinks with a friend after being paid daily or every two weeks "
        "(Supplemental Study 3)",
        "Supplemental Study 3, autumn 2019. $850 to start, $650 rent, paid $140 each "
        "weekday or $1,400 every two weeks. NOT A CLEAN CONTRAST: in the .qsf the daily-pay "
        "arm's Sunday screen (QID22, shown when Condition = day) says \"You get paid "
        "$1,400 every two weeks (Fridays).\" word-for-word as the biweekly arm's does, and "
        "then shows $140 deposits each weekday; no other screen states the daily schedule. "
        "Rendered as the .qsf has it (ledger 156: a screen error every respondent in an "
        "arm saw alike is kept and flagged; the evidence is the exported survey only). "
        + FIRST_ONLY.format(
            later="18 further decisions, 4 subjective-wealth items and the planning, "
            "self-control, mood and literacy scales"
        )
        + " 404 of 460 kept (pre-registration: 7 failed the attention check, 50 had "
        "taken a similar survey before, 1 both).",
    )


SIM_NOTE = (
    "A passive month-long simulation (no choices): one screen per day of February with "
    "that day's deposit, spending and balance, each screen word-for-word with the "
    'loop-and-merge values of the arm\'s block in the .qsf ("You also spent $-76" is '
    "the screen's own rendering). Six subjective-wealth sliders then four "
    "prediction-uncertainty sliders, 0-100, each set shown in a random order. Column "
    "Subjective Wealth k / Prediction Uncertainty k is the k-th question of its block in "
    "the .qsf: the deposit's columns follow the export's block order, and the codebook's "
    "polarity (items 4-6 and 1-2 reversed) matches it. The manipulation checks (how often "
    "/ how much were you paid, range of expenses) are recall checks, not built."
)


def study3(which: str) -> Experiment:
    arms = [
        Arm(1, {"pay_frequency": "daily"}, {"Frequency": "Daily"}),
        Arm(2, {"pay_frequency": "weekly"}, {"Frequency": "Weekly"}),
    ]
    label = "how wealthy it felt" if which == "wealth" else "how predictable it felt"
    return wealth_study(
        "3",
        which,
        arms,
        f"A simulated month paid $100 daily or $700 weekly: {label} (Study 3)",
        "Study 3, autumn 2020. Paid $100 every day (start $20) or $700 every week (start "
        "$500), with the same daily expenses. "
        + SIM_NOTE
        + " 112 of 152 kept (paper: 31 had taken part before, 9 failed the checks).",
    )


def study4(which: str) -> Experiment:
    arms = [
        Arm(c, {"pay_frequency": p, "expense_frequency": e}, {"Frequency": fp, "Exp": fe})
        for c, (p, e, fp, fe) in enumerate(
            [
                ("daily", "daily", "Daily", "day"),
                ("daily", "weekly", "Daily", "week"),
                ("weekly", "daily", "Weekly", "day"),
                ("weekly", "weekly", "Weekly", "week"),
            ]
        )
    ]
    label = "how wealthy it felt" if which == "wealth" else "how predictable it felt"
    return wealth_study(
        "4",
        which,
        arms,
        f"A simulated month, paid daily or weekly and spending daily or weekly: {label} (Study 4)",
        "Study 4, autumn 2020, 2 x 2: paid $100 every day or $700 every week, and paying "
        "expenses every day or every week (the same totals), $500 to start. "
        + SIM_NOTE
        + " 528 of 599 kept (paper: 37 had taken part before, 34 failed the checks).",
    )


# Not built (rich's rule, 19 Nov 2026): Supplemental Study 3's daily arm is told "You get
# paid $1,400 every two weeks (Fridays)" (QID22, a copy of the biweekly arm's QID21) and then
# paid $140 each weekday, so its contrast is not clean. Its builder s3() stays for the record.
NOT_BUILT = ("s3",)


def experiments() -> list[Experiment]:
    return [
        study2(),
        study3("wealth"),
        study3("ease"),
        study4("wealth"),
        study4("ease"),
        study5(),
        s1(),
        s2(),
    ]


# ---------------------------------------------------------------------------
# Coded data
# ---------------------------------------------------------------------------

CODED = {
    "2": "study2",
    "3": "study3",
    "4": "study4",
    "5": "study5",
    "S1": "s1",
    "S2": "s2",
}


def data_file(tag: str) -> str:
    return f"{STUDY_ID}_{CODED[tag]}.csv"


def prep(tag: str) -> pd.DataFrame:
    """One coded row per kept respondent: assignment, answers, persona."""
    df = read_study(tag)
    idcol = "ResponseId" if "ResponseId" in df.columns else "Response ID"
    assert df[idcol].is_unique
    out = pd.DataFrame({"pid": [f"{CODED[tag]}_{i}" for i in df[idcol]]})
    for coded, (src, codes) in ASSIGN[tag].items():
        assert set(df[src]) == set(codes), (tag, src, set(df[src]))
        out[coded] = df[src].map(codes).astype(int)
    exps = [e for e in experiments() if e.tag == tag]
    for e in exps:
        for o in e.outcomes:
            if o.var == "decision1":
                target = Survey(tag).qs[o.qid]
                pos = {d: i for i, (_, d, _) in enumerate(decision_options(target), 1)}
                raw = df["Decision 1"].astype(int)
                assert set(raw) <= set(pos), (tag, set(raw))
                out[o.var] = raw.map(pos).astype(int)
            else:
                k = int(o.var[2:])
                src = "Subjective Wealth " if o.var.startswith("sw") else "Prediction Uncertainty "
                v = df[f"{src}{k}"]
                assert v.notna().all() and v.between(0, 100).all() and (v == v.round()).all()
                out[o.var] = v.astype(int)
    out = pd.concat([out, persona_cols(tag, df)], axis=1)
    return out.sort_values("pid").reset_index(drop=True)


# ---------------------------------------------------------------------------
# The recipes
# ---------------------------------------------------------------------------


def recipe(e: Experiment) -> dict[str, Any]:
    arms = [
        {
            "raw_values": dict(zip(e.factor_vars, _codes(e, a), strict=True)),
            "condition_num": i,
            "factors": a.factors,
            "text": a.text,
        }
        for i, a in enumerate(e.arms)
    ]
    persona = {"age": "age", "gender": "gender"}
    for kind in ("income", "education"):
        if demographic(e.tag, kind) is not None:
            persona[kind] = kind
    notes = (
        f"{PAPER}\n\nGENERATED by scripts/gen_researchbox231.py; every judgement is in its "
        f"docstring. {e.notes}\n\nWording from {QSF[e.tag]}. Typography normalised (curly "
        "quotes, non-breaking spaces); line breaks kept as the screen had them; one blank "
        "line between screens. Persona: age (years; outside 18-100 left blank), and "
        + ", ".join(k for k in persona if k != "age")
        + ", labels from the .qsf's own choices (income and education harmonised by the "
        "crosswalk scheme us_researchbox231_qualtrics). Ethnicity (multi-select) and own "
        "pay frequency not mapped."
    )
    cond: dict[str, Any] = {"source_vars": e.factor_vars, "factors": e.factors, "arms": arms}
    if e.rejected:
        cond["considered_and_rejected"] = e.rejected
    lo, hi = e.outcomes[0].scale["min"], e.outcomes[0].scale["max"]
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
        "condition": cond,
        "outcomes": [
            {"var": o.var, "task_num": t, "question": o.question, "scale": o.scale}
            for t, o in enumerate(e.outcomes)
        ],
        "response_recode": {k: k for k in range(lo, hi + 1)},
        "missing_codes": [],
        "persona_map": persona,
    }


def _codes(e: Experiment, a: Arm) -> list[int]:
    if len(e.factor_vars) == 1:
        return [a.code]
    p, x = a.factors["pay_frequency"], a.factors["expense_frequency"]
    return [{"daily": 1, "weekly": 2}[p], {"daily": 1, "weekly": 2}[x]]


def recipe_path(e: Experiment) -> Path:
    return RECIPES / f"{STUDY_ID}_{e.name}.yaml"


def render(e: Experiment) -> str:
    return yaml.safe_dump(recipe(e), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prep", action="store_true", help="(re)write the coded .csv files")
    ap.add_argument("--check", action="store_true", help="exit 1 if any recipe differs")
    args = ap.parse_args()
    if args.prep:
        for tag in CODED:
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
