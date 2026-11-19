#!/usr/bin/env python3
"""Write recipes/researchbox755_*.yaml: choice set size neglect (3 recipes).

Hu B, Moon A, VanEpps EM (2026), "Choice Set Size Neglect in Predicting Others' Preferences",
Psychological Science, doi:10.1177/09567976251400333 (published online 7 Jan 2026). ResearchBox
755 ("Choice Set Size Neglect", https://researchbox.org/755), read from its Zenodo copy. CC BY
4.0 ("All content posted to ResearchBox is under a CC By 4.0 License", the box page). US
samples on Prolific and Connect (CloudResearch); US dishes and the election kept as the source
has them.

Every judgement is here, in code, so the recipes can be re-derived and reviewed.

THE DESIGN. Someone chooses one option from a set of 2 or of 6; how much do they like what they
chose? The paper's claim is that people predicting ANOTHER person's liking neglect the set
size, which their own liking reflects, unless something draws attention to it (seeing both set
sizes at once, or a choice framed as a ranking). The box holds 6 .qsf, 7 data files (.xlsx,
one header row, no value labels), a codebook per data file, 6 .docx printouts, Stata code per
study, 7 AsPredicted pre-registrations and a ReadMe.

WHAT IS BUILT. Three recipes from two studies:
- study3 (Study 3, side dishes, Avery and Blake): separate evaluation (one person, who chose
  from 2 or from 6 side dishes) or joint evaluation (Avery chose from one set, Blake from the
  other, the 2-set shown first or second), crossed with a reason the sets differ (a different
  main course, lunch or dinner, weekday or weekend); how much do you think Avery (or Blake)
  likes the dish they chose (1-7).
- study4_food and study4_election (Study 4): Taylor chooses a side dish, Jordan votes for a
  District Attorney candidate, from 2 or 6 options, deciding by choosing or by first ranking
  them (2 x 2, between people); each person sees both scenarios, in a random order the deposit
  does not record, so each scenario is its own recipe and each row carries its own scenario
  only. How much do you think Taylor/Jordan likes the chosen option (1-7). The election is a
  US District Attorney primary, but the judgement turns only on the issue table shown (two
  issues per candidate) and is answerable without knowing US politics, so it is kept.

NOT BUILT (NOT_BUILT), each with its reason:
- study1, study2 and study5: every option is shown with a photograph of the dish (Study 1:
  six pictures, Study 2: eight, Study 5: six, 120/80/144 <img> tags, all in fielded blocks;
  check_pictures), so the product is in the picture. rich's ruling (19 Nov 2026): skip any
  study where a picture carries the product; these belong on the image list. Studies 1 and 2
  also have "self" arms whose liking question pipes in the respondent's own choice.
- study6_self (Study 6, the "self" half): the respondent chooses a charity and every later
  question names that answer ("How much of your 50-cent bonus would you like to donate to
  ${e://Field/choice_self}?", "How much do you like ${e://Field/choice_self}?"). A row would
  have to narrate the respondent's own answer, which CONVENTIONS forbids. The charity choice
  itself is not built either: its only stimulus is its own answer options, shown in a random
  order the deposit does not record, so nothing distinguishes the arms but the option list.
- study6_other (Study 6, the "other" half; dropped by main-session ruling, 19 Nov 2026,
  rich's UK-appropriate rule, removing the riskiest part): predict how much of a 50-cent bonus
  earlier participants donated to a named US charity (Feeding America, Americare, National
  Pediatric Cancer Foundation ...) they chose from 2 or 6, in US cents. The answer turns on
  familiarity with those US charities, which a UK respondent would not share. A first build
  (1,571 rows) reproduced the .do file and is not kept.
- study2_aggregate / study2_wave1: Study 2 (see above); two files of the same study.

PICTURES (rich, 19 Nov 2026). Every <img> tag in every .qsf is counted (check_pictures, PICTURES).
Studies 3 and 6 have none. Study 4 has 22, all one graphic, IM_3dww5dDjQ1HEMzI, fetched from
Qualtrics on 19 Nov 2026 (pdx1.qualtrics.com/CP/Graphic.php?IM=IM_3dww5dDjQ1HEMzI, a 512 x 512
PNG): a grey loading spinner, no words, no product, shown under "Taylor decides which side
dish to order." while the page waits. It carries no information and is dropped; the sentence
above it is kept. The .docx printout of Study 4 does not reproduce it.

THE WORDING. Every condition and question is the .qsf's, word-for-word, from the blocks the
survey flow reaches (Survey; questions addressed by QID, because export tags repeat). Pipes
(${e://Field/...}) are filled from the person's own recorded fields. HTML is reduced to
paragraphs; a table becomes one line per row with its non-empty cells joined by " | " and a
bulleted list one line per item starting "- " (layout, no words added); bold, underline,
colour and the yellow highlight on the chosen option are dropped (the sentence above each
list already names the choice); typography is normalised. Data quirks:
- The data's dish name "Saut√©ed brussels sprouts" is UTF-8 read as Mac Roman; it is decoded
  and asserted to be the .qsf's "Sautéed brussels sprouts" (the accent is a letter and kept).
- The Study 4 printout lower-cases the piped dish ("Taylor chooses fresh fruit cup."); the
  fielded fill is capitalised and is used (fielded export wins).

PAGES. A scenario unfolds over several pages in a fixed order. Study 3's last page restates
every earlier one, so it alone is the condition. Study 4's first page (the options) is not
restated, so the condition is the first page, then the "decides" page, then the last page
(which repeats the page before it, asserted), joined by blank lines and no words of ours. In
the 6-option ranking arm the "decides" sentence sat on five pages, each with a hidden
placeholder question that draws the next random rank (cand/dish2rank .. 6rank; jQuery hide);
it is rendered once.

ORDER. Study 3's joint arm records which set was shown first (twofirst), a factor. Study 4's
two scenarios came in a random order recorded nowhere (BlockRandomizer SubSet 2, no order
field); each row carries its own scenario only, and the "you will evaluate a separate
scenario" transition is dropped. Study 4's 6-option ranks are recorded per person
(dish2ranknum .. dish6ranknum, cand2ranknum .. cand6ranknum, asserted to be a permutation of 2-6)
and are part of the condition text. Everything else is fixed.

ATTENTION AND OPEN TEXT. Not built: attention checks ("Which of the following scenarios did
you see?") and comment boxes.

EXCLUSIONS. The authors' own (each .do file): drop people who left before or after
assignment, duplicate IP addresses and Prolific IDs (ExcludeDuplicateIP/ID = 1), and failed
attention checks. N as the .do files state: Study 3 587 of 602, Study 4 1,578 of 1,602.

THE ASSIGNMENT. Each file records the randomisers' embedded fields (Condition, reason,
twofirst, Choice, Frame, the dish fills, food_combo, candidate_combo_code,
the chosen option and the ranks), checked against the flow. Every arm is one combination of
what varied on screen, as drawn: arms are the cells that occur (a declared arm with no rows is a
QC warning), numbered in a deterministic order, and prep codes each person's cell. Jev:
scripts/recipe_prep.py reads .sav/.dta/.por only and this box has .xlsx, so it does not apply
(as for researchbox108 and researchbox3251); the assignment columns are named as such in the
codebooks.

PERSONA. Age (years, typed) and gender, labels from the .qsf's own choices (Male, Female, A
gender not listed); "Prefer not to disclose" is left blank.

ANSWER KEY. The paper's tables were not reachable (the journal page refused the request), so
the reference is the authors' own .do files run on the deposit: tests/test_gen_researchbox755.py
recomputes, from the BUILT rows, each study's cell means and Ns exactly as the .do file does
from the deposit (Study 3: dv by evaluation x choice set, and the OLS of dv on twoop, je,
their interaction and reason; Study 4: liking by scenario x condition, and the per-scenario
regression).

    uv run python scripts/gen_researchbox755.py --prep   # code the data
    uv run python scripts/gen_researchbox755.py          # write the recipes
    uv run python scripts/gen_researchbox755.py --check  # exit 1 if any recipe differs
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
STUDY_ID = "researchbox755"
RAW = REPO / "data" / "raw" / STUDY_ID
MATERIALS = RAW / "Materials"
DATA = RAW / "Data"
CODEBOOK = RAW / "Codebook"
RECIPES = REPO / "recipes"
LICENCE = (
    'CC BY 4.0, stated on the box page https://researchbox.org/755 ("All content posted '
    'to ResearchBox is under a CC By 4.0 License"); read from its Zenodo copy. Read 19 Nov '
    "2026."
)
PAPER = (
    "Hu B, Moon A, VanEpps EM (2026), \"Choice Set Size Neglect in Predicting Others' "
    'Preferences", Psychological Science, doi:10.1177/09567976251400333. ResearchBox 755 '
    "(https://researchbox.org/755)."
)

# recipe -> (.qsf, data file, the paper's name, pre-registration)
SOURCES = {
    "study3": ("Study 3.qsf", "Study 3.xlsx", "Study 3", "AsPredicted #225471"),
    "study4_food": (
        "Study 4.qsf",
        "Study 4.xlsx",
        "Study 4, side-dish scenario",
        "AsPredicted #108512",
    ),
    "study4_election": (
        "Study 4.qsf",
        "Study 4.xlsx",
        "Study 4, election scenario",
        "AsPredicted #108512",
    ),
}

NOT_BUILT = {
    "study1": "every dish is shown with its photograph (120 fielded <img> tags): an image study",
    "study2": "every dish is shown with its photograph (80 fielded <img> tags): an image study",
    "study5": "every dish is shown with its photograph (144 fielded <img> tags): an image study",
    "study6_self": (
        "the donation and liking questions pipe in the respondent's own charity choice, and the "
        "choice itself has no stimulus beyond its own randomly ordered options"
    ),
    "study6_other": (
        "predicting donations, in US cents, to named US charities (Feeding America, Americare, "
        "National Pediatric Cancer Foundation ...) needs US familiarity: not UK-appropriate"
    ),
}

# image list candidates: study -> distinct pictures in its .qsf
IMAGE_LIST = {"Study 1": 6, "Study 2": 8, "Study 5": 6}

# every <img> tag in every .qsf: file -> (fielded, not fielded)
PICTURES = {
    "Study 1.qsf": (120, 0),
    "Study 2.qsf": (80, 0),
    "Study 3.qsf": (0, 0),
    "Study 4.qsf": (22, 0),
    "Study 5.qsf": (144, 0),
    "Study 6.qsf": (0, 0),
}
SPINNER = "IM_3dww5dDjQ1HEMzI"  # Study 4's only picture: a loading spinner, no words

# people kept by the authors' exclusions (each .do file's "Final sample")
N = {"study3": 587, "study4_food": 1578, "study4_election": 1578}

# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

_TYPO = {"\xa0": " ", "\u200b": "", "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"'}


def _clean(s: str) -> str:
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    for a, b in _TYPO.items():
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def to_text(raw: str) -> str:
    """HTML to paragraphs (blank-line separated). A table is one line per row, its non-empty
    cells joined by " | "; a list item is one line starting "- ". Pictures are dropped."""
    raw = re.sub(r"<img[^>]*>", "", raw or "")

    def row(m: re.Match[str]) -> str:
        cells = [_clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", m.group(0), re.S)]
        return "\x01" + " | ".join(c for c in cells if c) + "\x02"

    raw = re.sub(r"<tr[^>]*>.*?</tr>", row, raw, flags=re.S)
    raw = re.sub(
        r"<li[^>]*>(.*?)</li>", lambda m: "\x01- " + _clean(m.group(1)) + "\x02", raw, flags=re.S
    )
    parts = re.split(r"<br\s*/?>|</?p[^>]*>|</?div[^>]*>|</?table[^>]*>|</?tbody>|</?ul>", raw)
    out: list[str] = []
    for p in parts:
        if "\x01" in p:
            rows = [r for r in re.findall("\x01(.*?)\x02", p, re.S) if r.strip()]
            rest = _clean(re.sub("\x01.*?\x02", " ", p, flags=re.S))
            if rest:
                out.append(rest)
            if rows:
                out.append("\n".join(rows))
        else:
            c = _clean(p)
            if c:
                out.append(c)
    return "\n\n".join(out)


def fill(text: str, pipe: dict[str, str]) -> str:
    """Replace each ${e://Field/x} with pipe[x]; fail on any left."""

    def sub(m: re.Match[str]) -> str:
        return pipe[m.group(1)]

    text = re.sub(r"\$\{e://Field/(\w+)\}", sub, text)
    assert "${" not in text, text
    return text


def scale_label(raw: str, code: int) -> str:
    """An answer label without its printed number ("Not at all<br>1")."""
    s = _clean(re.sub(r"<br\s*/?>", " ", raw))
    return s[: -len(str(code))].strip() if s.endswith(str(code)) else s


# ---------------------------------------------------------------------------
# The questionnaires
# ---------------------------------------------------------------------------


class Survey:
    def __init__(self, path: Path) -> None:
        els = json.loads(path.read_text())["SurveyElements"]
        self.q: dict[str, dict[str, Any]] = {
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
        self.embedded: list[dict[str, str]] = []

        def walk(n: dict[str, Any]) -> None:
            if n.get("Type") in ("Block", "Standard"):
                self.flow_blocks.append(n["ID"])
            if n.get("Type") == "EmbeddedData":
                self.embedded.append({x["Field"]: str(x.get("Value")) for x in n["EmbeddedData"]})
            for c in n.get("Flow", []):
                walk(c)

        walk(self.flow)
        assert all(self.blocks[b]["Type"] != "Trash" for b in self.flow_blocks)
        self.fielded = {
            x["QuestionID"]
            for b in self.flow_blocks
            for x in self.blocks[b].get("BlockElements", [])
            if x["Type"] == "Question"
        }

    def text(self, qid: str) -> str:
        assert qid in self.fielded, qid
        return to_text(self.q[qid]["QuestionText"])

    def block(self, name: str) -> str:
        (b,) = {b for b in self.flow_blocks if self.blocks[b]["Description"].strip() == name}
        return b

    def pages(self, name: str) -> list[list[str]]:
        """A block's pages: the QIDs of its text and question elements (timers dropped)."""
        out: list[list[str]] = [[]]
        for x in self.blocks[self.block(name)]["BlockElements"]:
            if x["Type"] == "Page Break":
                out.append([])
            elif self.q[x["QuestionID"]]["QuestionType"] != "Timing":
                out[-1].append(x["QuestionID"])
        return out

    def scale(self, qid: str) -> dict[str, Any]:
        q = self.q[qid]
        assert q["QuestionType"] == "MC" and q["Selector"] == "SAHR", qid
        order = [str(k) for k in q["ChoiceOrder"]]
        assert len(order) == 7, qid
        labs = [scale_label(q["Choices"][k]["Display"], i) for i, k in enumerate(order, 1)]
        assert labs[0] == "Not at all" and labs[-1] == "Very much", labs
        assert all(lab == "" for lab in labs[1:-1]), labs
        return {"min": 1, "max": 7, "min_label": labs[0], "max_label": labs[-1]}


@cache
def survey(qsf: str) -> Survey:
    return Survey(MATERIALS / qsf)


def check_pictures() -> None:
    """Every <img> tag in every .qsf, split by whether a fielded block holds it."""
    for name, (fielded, other) in PICTURES.items():
        sv = Survey(MATERIALS / name)
        got = [0, 0]
        for qid, q in sv.q.items():
            got[0 if qid in sv.fielded else 1] += len(re.findall(r"<img", json.dumps(q)))
        assert tuple(got) == (fielded, other), (name, got)
        raw = (MATERIALS / name).read_text()
        assert raw.count("<img") == fielded + other, name
        if name == "Study 4.qsf":
            assert set(re.findall(r"IM_\w+", raw)) == {SPINNER}
    for study, n in IMAGE_LIST.items():
        assert len(set(re.findall(r"IM_\w+", (MATERIALS / f"{study}.qsf").read_text()))) == n


def gender_labels(sv: Survey, qid: str) -> dict[int, str | None]:
    q = sv.q[qid]
    assert _clean(q["QuestionText"]) == "Please indicate your gender."
    out: dict[int, str | None] = {}
    for k in q["ChoiceOrder"]:
        s = _clean(q["Choices"][str(k)]["Display"])
        out[int(k)] = None if s.startswith("Prefer not to") else s
    assert out == {1: "Male", 2: "Female", 3: "A gender not listed", 4: None}, out
    return out


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


def demojibake(s: Any) -> Any:
    """The data's dish names are UTF-8 read as Mac Roman ("Saut√©ed")."""
    if isinstance(s, str) and "√" in s:
        return s.encode("mac_roman").decode("utf-8")
    return s


@cache
def deposit(name: str) -> pd.DataFrame:
    df = pd.read_excel(DATA / name)
    for c in df.columns:
        if df[c].dtype == object or str(df[c].dtype) in ("str", "string"):
            df[c] = df[c].map(demojibake)
    return df


def kept(tag: str) -> pd.DataFrame:
    """The authors' exclusions, as each .do file applies them."""
    df = deposit(SOURCES[tag][1]).copy()
    # leavers: Study 3 drops those with no attention-check answer, Study 4 those with no age
    df = df[df["attnchk"].notna()] if tag == "study3" else df[df["age"].notna()]
    df = df[(df["ExcludeDuplicateIP"] != 1) & (df["ExcludeDuplicateID"] != 1)]
    df = df[df["attnchk"] == 1]
    df = df.reset_index(drop=True)
    assert len(df) == N[tag], (tag, len(df))
    assert df["ResponseId"].is_unique and df["Finished"].eq(1).all()
    return df


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


# ---------------------------------------------------------------------------
# The experiments
# ---------------------------------------------------------------------------


@dataclass
class Arm:
    key: tuple[Any, ...]
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
    shared: str
    arms: list[Arm]
    outcomes: list[Outcome]
    notes: str
    keys: list[tuple[Any, ...]]  # each kept person's arm key, in kept() order


def _strip_shared(text: str, shared: str) -> str:
    assert text.startswith(shared + "\n\n"), text[:200]
    return text[len(shared) + 2 :]


def arms_from(keys: list[tuple[Any, ...]], make: Any) -> list[Arm]:
    """One arm per distinct key that occurs, in sorted key order."""
    return [make(k) for k in sorted(set(keys), key=lambda k: tuple(str(x) for x in k))]


# --- Study 3 ---------------------------------------------------------------

REASON = {1: "main_course", 2: "time_of_day", 3: "day_of_week"}
LIKE_SCALE_QID = {"like_SE": "QID606", "like_a": "QID7", "like_b": "QID588"}


def study3() -> Experiment:
    sv = survey("Study 3.qsf")
    se = sv.pages("Condition 1 & 2 - SE-2 and SE-6")
    je = sv.pages("Condition 3 - JE 2 AND 6")
    assert se[-1] == ["QID608", "QID609", "QID606"], se
    assert je[-1] == ["QID593", "QID596", "QID7", "QID588"], je
    # the display logic that picks each last-page variant
    for qid, field_, val in (
        ("QID608", "ConditionName", "SE-2"),
        ("QID609", "ConditionName", "SE-6"),
        ("QID593", "twofirst", "1"),
        ("QID596", "twofirst", "0"),
    ):
        dl = sv.q[qid]["DisplayLogic"]["0"]["0"]
        assert (dl["LeftOperand"], dl["RightOperand"].strip()) == (field_, val), qid
    dishes = {
        f"dish{i}_name": v
        for e in sv.embedded
        for i in range(1, 7)
        if (v := e.get(f"dish{i}_name")) and "$" not in v
    }
    assert list(dishes.values()) == [
        "Spring mix salad",
        "Fresh fruit cup",
        "Roasted snap peas",
        "Quinoa salad",
        "Sautéed brussels sprouts",
        "Roasted carrots and fennel",
    ]
    reasons = {int(e["reason"]): e for e in sv.embedded if "reason" in e}
    df = kept("study3")
    for c, v in dishes.items():
        assert (df[c] == v).all(), c
    for r, e in reasons.items():
        sub = df[df["reason"] == r]
        for f in ("dine", "choose_from_2", "choose_from_6"):
            assert (sub[f] == e[f]).all(), (r, f)
    assert df.groupby("Condition")["ConditionName"].agg(set).to_dict() == {
        1: {"SE-2"},
        2: {"SE-6"},
        3: {"JE"},
    }
    assert (df["twofirst"].notna() == (df["Condition"] == 3)).all()
    assert (df["other_choice1"] != df["two_unchosen"]).all()

    design = {1: "separate_2", 2: "separate_6"}
    keys: list[tuple[Any, ...]] = []
    for _, row in df.iterrows():
        cond = int(row["Condition"])
        des = design.get(cond) or ("joint_2_first" if row["twofirst"] == 1 else "joint_6_first")
        unchosen = None if cond == 2 else row["two_unchosen"]
        keys.append((des, int(row["reason"]), row["other_choice1"], unchosen))
    shared = "Consider the following scenario:"
    qtext = {v: _clean(sv.q[q]["QuestionText"]) for v, q in LIKE_SCALE_QID.items()}
    assert qtext == {
        "like_SE": "How much do you think Avery likes ${e://Field/other_choice1}?",
        "like_a": "How much do you think Avery likes ${e://Field/other_choice1}?",
        "like_b": "How much do you think Blake likes ${e://Field/other_choice1}?",
    }
    page = {
        "separate_2": "QID608",
        "separate_6": "QID609",
        "joint_2_first": "QID593",
        "joint_6_first": "QID596",
    }

    def make(k: tuple[Any, ...]) -> Arm:
        d, reason, chosen, unchosen = k
        pipe = dict(dishes) | {
            f: reasons[reason][f] for f in ("dine", "choose_from_2", "choose_from_6")
        }
        pipe |= {"other_choice1": chosen, "two_unchosen": unchosen or ""}
        text = _strip_shared(fill(sv.text(page[d]), pipe), shared)
        if d == "separate_6":
            assert "${e://Field/two_unchosen}" not in sv.q["QID609"]["QuestionText"]
        tasks = [0] if d.startswith("separate") else [1, 2]
        items = {
            t: {"outcome_question": fill(qtext[["like_SE", "like_a", "like_b"][t]], pipe)}
            for t in tasks
        }
        return Arm(
            k,
            {
                "design": d,
                "reason": REASON[reason],
                "chosen": slug(chosen),
                "unchosen": slug(unchosen) if unchosen else "not_shown",
            },
            text,
            items,
        )

    arms = arms_from(keys, make)
    sc = sv.scale("QID606")
    assert sv.scale("QID7") == sv.scale("QID588") == sc
    first = {
        t: next(a.items[t]["outcome_question"] for a in arms if t in a.items) for t in range(3)
    }
    return Experiment(
        name="study3",
        title="Avery (and Blake) chose a side dish from 2 or from 6, seen alone or side by side: "
        "how much do they like it? (Study 3)",
        kind="mix",
        factors=["design", "reason", "chosen", "unchosen"],
        shared=shared,
        arms=arms,
        outcomes=[
            Outcome("like_SE", first[0], sc),
            Outcome("like_a", first[1], sc),
            Outcome("like_b", first[2], sc),
        ],
        notes=(
            "Between people: separate evaluation (Avery, told of 2 side dishes or of 6, chooses "
            "one; ConditionName SE-2 / SE-6) or joint evaluation (Avery and Blake at the same "
            "restaurant, one choosing from 2 and the other from 6, the 2-set first or second as "
            "recorded in twofirst), crossed with why the sets differ (reason: a sandwich or a "
            "lunch plate; lunch or dinner; weekday or weekend). The chosen dish (one of six) and, "
            "in a 2-set, the other dish (one of the remaining five) were drawn per person and "
            "are piped in; the 6-set is always the same six. Arms are the cells drawn. The "
            "scenario unfolds over two or three pages, each restating the last; the condition "
            "is the last page, on which the question sits (1 Not at all, 7 Very much). Joint "
            "evaluation asks about Avery (like_a) then Blake (like_b) on that page; separate "
            "evaluation asks about Avery once (like_SE). In joint evaluation both choose the "
            'same dish ("Blake chooses ...") as the screen says.'
        ),
        keys=keys,
    )


# --- Study 4 ---------------------------------------------------------------

DESIGN4 = {(2, 1): "choose_2", (2, 2): "rank_2", (6, 1): "choose_6", (6, 2): "rank_6"}
CONDITION4 = {"choose_2": 1, "rank_2": 2, "choose_6": 3, "rank_6": 4}

# scenario -> design -> (first-page block, deciding block, block holding the last pages)
BLOCKS4 = {
    "food": {
        "choose_2": (
            "[FOOD] 2 options - first page",
            "[FOOD] 2 options - second page [Choose]",
            None,
        ),
        "rank_2": ("[FOOD] 2 options - first page", "[FOOD] 2 options - second page [Rank]", None),
        "choose_6": (
            "[FOOD] 6 options - first page",
            "[FOOD] 6 options - second page [Choose]",
            None,
        ),
        "rank_6": (
            "[FOOD] 6 options - first page",
            "[FOOD] 6 options - Rank randomization",
            "[FOOD] 6 options - second page info [Rank]",
        ),
    },
    "election": {
        "choose_2": (
            "[ELECTION] 2 options - first page",
            "[ELECTION] 2 options - second page [Choose]",
            None,
        ),
        "rank_2": (
            "[ELECTION] 2 options - first page",
            "[ELECTION] 2 options - second page [Rank]",
            None,
        ),
        "choose_6": (
            "[ELECTION] 6 options - first page",
            "[ELECTION] 6 options - second page [Choose]",
            None,
        ),
        "rank_6": (
            "[ELECTION] 6 options - first page",
            "[ELECTION] 6 options - Rank randomization",
            "[ELECTION] 6 options - second page [RANK]",
        ),
    },
}
LIKE4 = {"food": "like1", "election": "like2"}
WHO4 = {"food": "Taylor", "election": "Jordan"}
CANDS = "ABCDEF"


def study4_pages(
    sv: Survey, scenario: str, design: str
) -> tuple[str, str, list[str], list[str], str]:
    """(first-page QID, deciding QID, last-page QIDs (head + variants), the page before it, like QID)."""
    first, decide, last = BLOCKS4[scenario][design]
    (p1,) = sv.pages(first)
    assert len(p1) == 1, p1
    pages = sv.pages(decide)
    if last is None:
        assert len(pages) == 3, (decide, pages)
        p2, p3, p4 = pages
    else:
        assert len(pages) == 5 and all(len(p) == 2 for p in pages), pages
        texts = {sv.text(p[0]) for p in pages}
        assert len(texts) == 1, texts  # the same sentence on five pages
        for p in pages:  # each with a hidden, self-advancing placeholder
            js = sv.q[p[1]].get("QuestionJS") or ""
            assert ".hide()" in js and "clickNextButton" in js, p
        p2 = [pages[0][0]]
        p3, p4 = sv.pages(last)
    assert len(p2) == 1 and SPINNER in sv.q[p2[0]]["QuestionText"], p2
    like = p4[-1]
    assert sv.q[like]["DataExportTag"].startswith(LIKE4[scenario] + "_"), like
    return p1[0], p2[0], p4[:-1], p3, like


def study4(scenario: str) -> Experiment:
    tag = f"study4_{scenario}"
    sv = survey("Study 4.qsf")
    df = kept(tag)
    who = WHO4[scenario]
    fixed6 = {
        f"dish{i}_name": v
        for e in sv.embedded
        for i in range(1, 7)
        if len(e) >= 6 and (v := e.get(f"dish{i}_name"))
    }
    assert len(fixed6) == 6
    issues = {
        c: (e[f"issue1_cand{c}"], e[f"issue2_cand{c}"])
        for e in sv.embedded
        for c in CANDS
        if f"issue1_cand{c}" in e
    }
    assert len(issues) == 6
    sc = None
    keys: list[tuple[Any, ...]] = []
    likes: list[float] = []
    for _, r in df.iterrows():
        d = DESIGN4[(int(r["Choice"]), int(r["Frame"]))]
        ranks: tuple[int, ...] | None = None
        if scenario == "food":
            chosen = r["other_choice1"]
            if d.endswith("_2"):
                pair: tuple[str, ...] = (r["dish1_name"], r["dish2_name"])
                assert chosen in pair
            else:
                pair = tuple(fixed6.values())
                assert all(r[f"dish{i}_name"] == v for i, v in enumerate(pair, 1))
            prefix = "dish"
        else:
            chosen = r["other_choice3"]
            if d.endswith("_2"):
                code = r["candidate_combo_code"]
                pair = (code[0], code[1])
                shown = dict(zip("AB", pair, strict=True))
                assert chosen in ("Candidate A", "Candidate B")
                real = shown[chosen[-1]]
            else:
                pair = tuple(CANDS)
                real = chosen[-1]
            assert (r["issue1_chosen"], r["issue2_chosen"]) == issues[real], r["Id"]
            prefix = "cand"
        if d == "rank_6":
            ranks = tuple(int(r[f"{prefix}{k}ranknum"]) for k in range(2, 7))
            assert sorted(ranks) == [2, 3, 4, 5, 6], ranks
        else:
            assert all(pd.isna(r[f"{prefix}{k}ranknum"]) for k in range(2, 7))
        keys.append((d, pair, chosen, ranks))
        answered = [r[f"{LIKE4[scenario]}_{k}"] for k in range(1, 5)]
        assert [pd.notna(a) for a in answered] == [k == CONDITION4[d] for k in range(1, 5)], r["Id"]
        likes.append(answered[CONDITION4[d] - 1])

    def make(k: tuple[Any, ...]) -> Arm:
        nonlocal sc
        d, pair, chosen, ranks = k
        p1, p2, last, before, like = study4_pages(sv, scenario, d)
        if scenario == "food":
            names = list(pair)
            pipe = (
                dict(fixed6) if d.endswith("_6") else {"dish1_name": pair[0], "dish2_name": pair[1]}
            )
            pipe["other_choice1"] = chosen
            idx = names.index(chosen)
            prefix = "dish"
        else:
            if d.endswith("_2"):
                pipe = {
                    "issue1_A": issues[pair[0]][0],
                    "issue2_A": issues[pair[0]][1],
                    "issue1_B": issues[pair[1]][0],
                    "issue2_B": issues[pair[1]][1],
                }
                idx = "AB".index(chosen[-1])
            else:
                pipe = {}
                idx = CANDS.index(chosen[-1])
            pipe["other_choice3"] = chosen
            prefix = "cand"
        if ranks:
            pipe |= {f"{prefix}{j}ranknum": str(v) for j, v in enumerate(ranks, 2)}
        head, variants = last[0], last[1:]
        assert len(variants) == (2 if d.endswith("_2") else 6), variants
        variant = variants[idx]
        raw = sv.q[variant]["QuestionText"]
        if d.startswith("choose"):
            # the chosen option is the highlighted one
            after = raw[raw.index("background-color") :]
            if scenario == "food":
                m = re.search(r"\$\{e://Field/(\w+)\}", after)
                assert m and m.group(1) == f"dish{idx + 1}_name", (variant, idx)
            else:
                m = re.search(r"Candidate ([A-F])", after)
                assert m and m.group(1) == (CANDS if d.endswith("_6") else "AB")[idx], variant
        last_page = fill(sv.text(head), pipe) + "\n\n" + fill(sv.text(variant), pipe)
        if d.startswith("rank"):
            lines = fill(sv.text(variant), pipe).split("\n")
            label = names[idx] if scenario == "food" else chosen
            (one,) = [ln for ln in lines if ln.startswith("Ranked #1 |")]
            assert one.split(" | ")[1] == label, (one, label)
        # the page before the last is the same, without the question
        assert before[0] != head and fill(sv.text(before[0]), pipe) == fill(sv.text(head), pipe)
        assert fill(sv.text(before[1 + idx]), pipe) == fill(sv.text(variant), pipe)
        text = "\n\n".join([fill(sv.text(p1), pipe), sv.text(p2), last_page])
        s = sv.scale(like)
        assert sc is None or s == sc
        sc = s
        question = fill(_clean(sv.q[like]["QuestionText"]), pipe)
        assert question.startswith(f"How much do you think {who} likes ")
        factors = {
            "design": d,
            "options": "all_six" if d.endswith("_6") else "_".join(slug(p) for p in pair),
            "chosen": slug(chosen),
            "ranks": "-".join(map(str, ranks)) if ranks else "none",
        }
        return Arm(k, factors, text, {0: {"outcome_question": question}})

    arms = arms_from(keys, make)
    assert sc is not None
    title = {
        "food": "Taylor orders a side dish from 2 or 6, choosing or first ranking them: how "
        "much does Taylor like it? (Study 4)",
        "election": "Jordan votes for a District Attorney candidate from 2 or 6, choosing or "
        "first ranking them: how much does Jordan like the candidate? (Study 4)",
    }[scenario]
    what = {
        "food": "Taylor orders a side dish from 2 (one of the 15 pairs of six dishes, "
        "food_combo) or from all 6",
        "election": "Jordan votes in a District Attorney primary between 2 candidates (one of "
        "the 15 pairs of six, candidate_combo_code, shown as Candidate A and Candidate B with "
        "the pair's issues) or among all 6 (A-F), each with two issues in a table",
    }[scenario]
    exp = Experiment(
        name=tag,
        title=title,
        kind="mix",
        factors=["design", "options", "chosen", "ranks"],
        shared="",
        arms=arms,
        outcomes=[Outcome("like", arms[0].items[0]["outcome_question"], sc)],
        notes=(
            f"2 (2 or 6 options, Choice) x 2 (decide by choosing or by first ranking, Frame), "
            f"between people. {what}; the chosen option was drawn per person and piped in, and "
            "in the 6-option ranking arm the other five options' ranks (2-6) were drawn and "
            "recorded. Arms are the cells drawn. The condition is the first page (the options), "
            "the deciding page, and the last page (who chose or ranked what, with the options "
            "again), joined by blank lines; the page before the last is the same and is not "
            'repeated. Tables are one line per row, cells joined by " | ". The question is on '
            "the last page (1 Not at all, 7 Very much). Everyone also answered the other "
            "Study 4 scenario, in a random order the deposit does not record, so no row "
            "narrates it. The coded column `like` is the one of the four exported liking "
            f"columns ({LIKE4[scenario]}_1 .. _4, one per design cell) that the person answered, "
            "asserted to be the one for their cell."
        ),
        keys=keys,
    )
    exp_likes[tag] = likes
    return exp


exp_likes: dict[str, list[float]] = {}


def experiments() -> list[Experiment]:
    return [study3(), study4("food"), study4("election")]


def experiment(tag: str) -> Experiment:
    if tag == "study3":
        return study3()
    assert tag.startswith("study4"), tag
    return study4(tag.removeprefix("study4_"))


# ---------------------------------------------------------------------------
# Coded data
# ---------------------------------------------------------------------------


def data_file(tag: str) -> str:
    return f"{STUDY_ID}_{tag}.csv"


def answers(s: pd.Series, lo: int, hi: int) -> pd.Series:
    v = pd.to_numeric(s, errors="raise")
    assert (v.dropna() % 1 == 0).all()
    assert v.dropna().between(lo, hi).all()
    return v.astype("Int64")


def prep(tag: str) -> pd.DataFrame:
    """One coded row per kept person: the arm code, the answers, age, gender."""
    e = experiment(tag)
    df = kept(tag)
    qsf = SOURCES[tag][0]
    order = {a.key: i + 1 for i, a in enumerate(e.arms)}
    out = pd.DataFrame({"pid": [f"{tag}_{r}" for r in df["ResponseId"]]})
    out["arm"] = [order[k] for k in e.keys]
    if tag == "study3":
        for v in ("like_SE", "like_a", "like_b"):
            out[v] = answers(df[v], 1, 7).values
    else:
        out["like"] = answers(pd.Series(exp_likes[tag]), 1, 7).values
    sv = survey(qsf)
    glab = gender_labels(sv, "QID30")
    out["age"] = answers(df["age"], 18, 100).values
    out["gender"] = [glab[int(g)] if pd.notna(g) else None for g in df["gender"]]
    return out


def check_codebook(tag: str) -> None:
    """The codebook lists the data file's columns, in order."""
    name = SOURCES[tag][1]
    book = pd.read_csv(CODEBOOK / f"{name}___CODEBOOK.csv")
    assert list(book["varname"]) == list(deposit(name).columns), tag


# ---------------------------------------------------------------------------
# The recipes
# ---------------------------------------------------------------------------


def recipe(e: Experiment) -> dict[str, Any]:
    arms = []
    for i, a in enumerate(e.arms):
        arm: dict[str, Any] = {
            "raw_values": {"arm": i + 1},
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
    qsf, data, name, prereg = SOURCES[e.name]
    notes = (
        f"{PAPER}\n\nGENERATED by scripts/gen_researchbox755.py; every judgement is in its "
        f"docstring. {name} ({prereg}), {N[e.name]:,} people: the authors' exclusions as their "
        f".do file applies them (attrition, duplicate IP address or Prolific ID, failed "
        f"attention check). {e.notes}\n\nWording from {qsf} (the blocks the survey flow "
        "reaches), word-for-word, pipes filled from each person's recorded fields: the "
        "scenario is the condition, each question the outcome. Typography normalised (HTML, "
        "non-breaking spaces, curly quotes); emphasis and highlighting dropped; a loading "
        "spinner picture (Study 4) dropped. No words added. "
        f"Data: {data}. Persona: age (years, as typed) and gender (the .qsf's labels; "
        '"Prefer not to disclose" left blank).'
    )
    cond: dict[str, Any] = {"source_vars": ["arm"]}
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
