#!/usr/bin/env python3
"""Write recipes/researchbox809_*.yaml: a corporate donation pledged as one sum or every month.

ResearchBox 809 ("Periodic Corporate Donations", https://researchbox.org/809), read from its
Zenodo copy (record 21934081, zip made 13 Feb 2026, 104 files). CC BY 4.0 ("All content
posted to ResearchBox is under a CC By 4.0 License", the box page). The paper is not named in
the box and was not read; the answer key is the authors' own R code (Code/*.rmd), transcribed
and re-run on the deposit and on the built rows. US online samples (Prolific and CloudResearch
Connect), 2022 to 2025, US dollars.

Every judgement is here, in code, so the recipes can be re-derived and reviewed.

THE BOX. Studies 1a and 1b (field studies), 2, 3, 4, 5a, 5b and web-appendix studies W1-W5.
Each lab study has one .qsf (Materials/), one .csv data file (Data/, one header row, the
.qsf's recodes, every randomised embedded-data field exported as its own column), a codebook
and the authors' .rmd. "DELETED AFTER BOX WAS PUBLIC/" holds one further study the authors
withdrew from view: "5b. Modest amounts" (AsPredicted #185918, fielded 8 Aug 2024, survey
name "_Web Appendix W4 - Small donations"), with its own .qsf, data and .rmd.

THE TWO "5b" QUESTIONNAIRES ARE TWO STUDIES, NOT TWO VERSIONS OF ONE. Each has its own data
file, and each data file can only have come from its own .qsf (`check_data_matches_qsf`,
run on every study): "5b new study. Modest amount.csv" has the columns filter, engage and
amount (low/modest/high) and the six prices of its .qsf ($100, $2,500, $500,000; $2, $50,
$10,000 every week, Alpha Manufacturing); "5b. Modest amounts.csv" has impact, commit, brand
and money (small/large) and the four prices of its .qsf (a named real retailer, $6 million or
$600 in total, $500,000 or $50 every month). Neither data file holds a value the other
.qsf could set. Only study5b (the one in the box, AsPredicted #252061, Oct 2025) is built.
The withdrawn one (study5b_2024) is NOT_BUILT (rich, 19 Nov 2026): the authors deleted it
from the box after it was public, and its stimulus names a real US clothing retailer.

WHICH QUESTIONNAIRE WAS FIELDED. Most .qsf files were exported after fielding (5a and W1 were
fielded Sept 2022 and exported 2024; W3 fielded Feb 2025, exported June 2025; Study 4's was
last modified 27 Feb 2025, after its 9-10 Feb fielding). The only proof available, and it is
asserted for every kept row, is that every randomised value the data file records (condition,
amount, price, price2, cause, company, brand, action, frequency, money, cond2) is exactly the
value the .qsf's flow sets for that row's assignment, and that every outcome column is a
question the flow reaches. Fixed wording cannot be proved against fielding by anything in
the deposit; the .qsf is the only instrument there is (recorded, as researchbox3299 did).

WHAT IS BUILT (one recipe each; see SPECS). All between-person; everyone read one scenario:
- study2 (stimulus sampling): a fashion retailer near you pledges a sum to one of six causes,
  as one total in 2024 or the same sum spread monthly, at six sizes; how likely are you to buy
  from it next time you need clothes (1-7). 72 arms. Kind "mix".
- study3 (serial mediation): $6 million in 2024 or $500,000 every month in 2024, to wildlife
  and environmental conservation; admire / view favourably / view positively (1-7), then
  genuine commitment (3 rows) and impact (3 rows) (1-7). "version".
- study4 (prosocial motivation moderator): a financial services company; total or monthly x
  whether it did this only after its main competitor announced a similar campaign. "mix".
- study5a (total donation size): a business owner donates to disaster relief, $100 or $520,000
  this year, or $2 or $10,000 every week; admire / favour / positive / morally praiseworthy.
- study5b: the same story at three sizes ($100 / $2,500 / $500,000, or $2 / $50 / $10,000 a
  week); admire / favour / positive, and how likely you would be to like a social media post
  about the donation. "mix".
- w1 (company evaluation, stimulus sampling): nine invented companies and causes, each with
  its own total and monthly amounts. 18 arms. "mix".
- w2 (inference control): total, monthly, or monthly with the total stated "(totaling $6
  million)"; purchase likelihood on 1-11. "version".
- w3 (donation size post-test): $100 this year or $2 every week; how reasonable is that
  amount (1-7). "version".
- w4 (addressing alternatives): $720,000 in 2024 or $60,000 every month; admire / favour /
  positive, then sacrifice (3), commitment (3 rows), future donation likelihood (0-100
  slider), skepticism (3 rows) and impact (3 rows). "version".
- w5 (another moderator): total or monthly x whether the company is also "widely known for
  their intentional overproduction, unethical sourcing of materials, and severe environmental
  damage". "mix".

NOT BUILT (NOT_BUILT): study5b_2024 (above), and study1a and study1b, the field studies.
Neither has person-level rows or a persona: 1a's data are ad-level aggregate counts (reach
and link clicks per campaign), and 1b's are website-link clicks, clickers only, with no row
for anyone who did not click. There is no .qsf for either.

LATER MEASURE BLOCKS. After the admire/favour/positive page, Studies 3, W4 and W5 show further
blocks (commitment, impact, sacrifice, skepticism, future donation likelihood) in a block
order the .qsf randomises and the deposit does not record (no _DO or FL_ column). Ruled by
rich (20 Nov 2026) for the A/B studies, 3 and W4: built, the way 5a's two pages are. Each row
carries the scenario, then that block's own reminder (the same words on every page,
asserted) and its own question only; nothing about the other blocks is narrated. Matrix
questions give one outcome per row, the row's label appended to the stem in double quotes
(layout, ours, as xk9ch); each data column <tag>_<k> is tied to the k-th row in ChoiceOrder
by the authors' codebook, which names that row's words and no other's (`check_codebook`).
W4's future-likelihood slider (0-100, whole numbers, no end labels) keeps its fielded range;
one sentence of OURS after the question names its only label:
    'The answer was a slider from 0 to 100, labelled "Percent (%) likelihood".'
W5's later blocks (commitment, impact, skepticism) are NOT built, pending rich's ruling (he
ruled for the A/B studies only). The recall check "How did the company make its donation?"
is an attention check (CONVENTIONS: not an outcome), used only for the authors' exclusion.

STUDY 5a's TWO MEASURE BLOCKS. Its admire/favour/positive page and its praiseworthy page are
the two blocks of one randomiser (SubSet 2), so each person saw both in a random order the
deposit does not record. Neither follows a fixed earlier question, so all four are built and
each row carries its own page only, with no position narrated, as researchbox348 study1 did
with its unrecorded scenario order. Both pages open with the same reminder (asserted).

THE CONDITION. Simulated from each .qsf's survey flow for the arm's assignment: embedded data
set by the randomisers and branches, display logic on embedded fields evaluated, piped fields
${e://Field/x} filled. The row is every text screen from the scenario's first screen up to and
including the reminder at the top of the measure page, word-for-word, one paragraph per
screen part; bullets become lines starting "- ". Dropped: consent, the participant-id box, the
"Welcome to the survey! On the following pages, you will read ..." screen (survey mechanics),
5b's pre-consent bot screener (a 600x62 picture of instructions plus a question on them; same
for everyone, before consent, and not part of the scenario), timing. In W5's low-reputation
arm the pledge screen is followed by a second screen restating it with the reputation
sentence; both are kept, as shown. Typography normalised (HTML, non-breaking spaces, curly
quotes); bold and underline dropped.

THE OUTCOME. The question word-for-word with its piped fields filled. Where it names the
arm's company or amount (W1, W3, 5b's engage), every arm carries its own wording
(items[t].outcome_question) and the Outcome-level question is the first arm's form,
overridden on every arm (as xk9ch). Scales are the .qsf's recoded values, labels from the
end choices with the number removed ("Not at all 1" -> "Not at all").

EXCLUSIONS. The authors' .rmd, applied as written: Status 0 and Finished 1; 5b also filter 1
(the screener); then the pre-registered recall check (aggregate must answer the one-time
option, periodic the monthly or weekly one; 5a's choices are in the other order, and its
.rmd codes it so). W2 and W3 have no recall check. Missing answers are dropped per outcome.

PERSONA. Age (years, as typed; outside 18-100 left blank: 5a has 0.31, W3 has 5, Study 2 has
17) and gender (the .qsf's labels Male, Female, Non-Binary; "Prefer not to say" left blank).

JEV. scripts/recipe_prep.py reads .sav only. Run on W5's SPSS file (19 Nov 2026, --source
dataverse) it named COND as the assignment (conf 0.92) and put COND2, the second factor, at
0.02. That file is the authors' recoded analysis set; the build reads the .csv, whose
assignment fields are named by the .qsf's randomisers, which are the authority.

ANSWER KEY. Each study's pre-registered model from its .rmd (positivity = mean of admire,
favor, positive; lm/aov with the authors' coding), fitted twice: on the deposit after the
authors' exclusions, and on the BUILT rows. They agree to 1e-9 (tests/test_gen_researchbox809.py,
which also records the values); for 3 and W4 that includes every later composite (commit,
impact; sacrifice, commitment, future_95, skepticism, impact). The authors' PROCESS outputs
(Other/*.pdf) give the analysed N for Studies 3 (556), W4 (429), W5 (1,643) and 5b_2024
(759), all reproduced, and for 3 and W4 each mediator's a-path (constant and condition
effect, SPSS, independent of the .rmd): all seven equal the built rows' to 4 decimals.

    uv run python scripts/gen_researchbox809.py --prep   # code the data
    uv run python scripts/gen_researchbox809.py          # write the recipes
    uv run python scripts/gen_researchbox809.py --check  # exit 1 if any recipe differs
"""

from __future__ import annotations

import argparse
import html
import itertools
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
STUDY_ID = "researchbox809"
RAW = REPO / "data" / "raw" / STUDY_ID
DELETED = RAW / "DELETED AFTER BOX WAS PUBLIC"
RECIPES = REPO / "recipes"
LICENCE = (
    'CC BY 4.0, stated on the box page https://researchbox.org/809 ("All content posted '
    'to ResearchBox is under a CC By 4.0 License"); read from its Zenodo copy, record '
    "21934081 (https://zenodo.org/records/21934081). Read 19 Nov 2026."
)
SOURCE = (
    'ResearchBox 809, "Periodic Corporate Donations" (https://researchbox.org/809), Zenodo '
    "record 21934081. The paper is not named in the box and was not read."
)

NOT_BUILT = {
    "study5b_2024": 'Withdrawn 5b ("5b. Modest amounts", AsPredicted #185918): the '
    'authors deleted it from the box after it was public ("DELETED AFTER BOX WAS PUBLIC"), '
    "and its stimulus names a real retailer. Dropped (rich, 19 Nov 2026); its spec stays in "
    "ALL_SPECS for the record.",
    "study1a": "Field study 1a (Google ads): the data are ad-level aggregate counts (reach, "
    "link clicks per campaign), with no person-level rows and no persona; no .qsf.",
    "study1b": "Field study 1b (fundraising emails): the data are website-link clicks, "
    "clickers only (no row for anyone who did not click), with no persona; no .qsf.",
}

# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

_TYPO = {"\xa0": " ", "\u200b": "", "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"'}
_BREAK = re.compile(r"(?i)<br\s*/?>|</?p[^>]*>|</?div[^>]*>|</?ul[^>]*>|</li>")


def plain(raw: str) -> str:
    """An HTML fragment to one line of plain text. Typography only."""
    s = re.sub(r"<[^>]+>", " ", raw or "")
    s = html.unescape(s)
    for a, b in _TYPO.items():
        s = s.replace(a, b)
    s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r" ([.,?])", r"\1", s)  # a space the markup left before punctuation


def lines(raw: str) -> list[str]:
    """HTML to its visible lines: one per paragraph, '- ' for each list item."""
    s = re.sub(r"(?i)<li[^>]*>", "\n\x00", raw or "")
    s = _BREAK.sub("\n", s)
    out = []
    for part in s.split("\n"):
        bullet = part.startswith("\x00")
        t = plain(part.replace("\x00", ""))
        if t:
            out.append(f"- {t}" if bullet else t)
    return out


def screen_text(raw: str) -> str:
    """One screen's text: paragraphs blank-line separated, list items on their own lines."""
    out: list[str] = []
    for ln in lines(raw):
        if out and ln.startswith("- "):  # a list item stays under its lead line
            out[-1] += "\n" + ln
        else:
            out.append(ln)
    return "\n\n".join(out)


def pipe(raw: str, ed: dict[str, str], known: set[str] | None = None) -> str:
    """Fill ${e://Field/x}. A field the flow sets for some arms but not this one shows
    nothing on screen (Qualtrics prints an unset field as empty): allowed only if `known`."""

    def sub(m: re.Match[str]) -> str:
        f = m.group(1)
        if f in ed:
            return ed[f]
        assert known is not None and f in known, f
        return ""

    out = re.sub(r"\$\{e://Field/(\w+)\}", sub, raw)
    assert "${" not in out, out[:200]
    return out


# ---------------------------------------------------------------------------
# The questionnaire, simulated through its flow
# ---------------------------------------------------------------------------

# Questions a branch may test, with the answer every kept respondent gave: consent
# (choice 1, "I consent ..."), and 5b's screener (choice 1, else the survey ends).
GATES = {"consent", "filter"}


class Survey:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.raw = path.read_text()
        d = json.loads(self.raw)
        self.entry = d["SurveyEntry"]
        els = d["SurveyElements"]
        self.by_id = {e["Payload"]["QuestionID"]: e["Payload"] for e in els if e["Element"] == "SQ"}
        self.blocks: dict[str, dict[str, Any]] = {}
        for e in els:
            if e["Element"] == "BL":
                p = e["Payload"]
                for b in p.values() if isinstance(p, dict) else p:
                    self.blocks[b["ID"]] = b
        self.flow = next(e for e in els if e["Element"] == "FL")["Payload"]
        self.fields = set(re.findall(r'"Field":\s*"(\w+)"', json.dumps(self.flow)))

    def qids(self, block_id: str) -> list[str]:
        return [
            x["QuestionID"]
            for x in self.blocks[block_id].get("BlockElements", [])
            if x["Type"] == "Question"
        ]

    def tag(self, qid: str) -> str:
        return str(self.by_id[qid]["DataExportTag"])

    def holds(self, logic: dict[str, Any], ed: dict[str, str]) -> bool:
        """A one-condition BooleanExpression on an embedded field or a gate question."""
        (expr,) = [v for k, v in logic.items() if k.isdigit()]
        (cond,) = [v for k, v in expr.items() if k.isdigit()]
        if cond["LogicType"] == "EmbeddedField":
            assert cond["Operator"] == "EqualTo", cond
            return bool(ed.get(cond["LeftOperand"]) == cond["RightOperand"])
        assert cond["LogicType"] == "Question", cond
        assert self.tag(cond["QuestionID"]) in GATES, cond
        assert cond["LeftOperand"].endswith("/SelectableChoice/1"), cond
        return {"Selected": True, "NotSelected": False}[cond["Operator"]]

    def walk(self, arm: dict[str, str]) -> tuple[dict[str, str], list[Any]]:
        """(embedded data, the blocks reached in order) for one assignment.

        A randomiser over embedded-data children is the assignment: it takes the child
        that sets one of the arm's fields to the arm's value. A randomiser over blocks
        is a measure group, returned as a list of its block ids."""
        ed: dict[str, str] = {}
        seq: list[Any] = []

        def go(n: dict[str, Any]) -> bool:  # False: the survey ended
            t = n.get("Type")
            if t == "EmbeddedData":
                for e in n["EmbeddedData"]:
                    if e.get("Value") is not None:
                        ed[e["Field"]] = e["Value"]
                return True
            if t == "BlockRandomizer":
                kids = n["Flow"]
                if all(k["Type"] == "EmbeddedData" for k in kids):
                    assert n["SubSet"] in (1, "1"), n["FlowID"]
                    hit = [
                        k
                        for k in kids
                        if any(
                            e["Field"] in arm and e.get("Value") == arm[e["Field"]]
                            for e in k["EmbeddedData"]
                        )
                    ]
                    assert len(hit) == 1, (n["FlowID"], arm)
                    return go(hit[0])
                assert all(k["Type"] in ("Block", "Standard") for k in kids), n["FlowID"]
                assert int(n["SubSet"]) == len(kids), n["FlowID"]  # every block shown
                seq.append([k["ID"] for k in kids])
                return True
            if t == "Branch":
                if self.holds(n["BranchLogic"], ed):
                    return all(go(c) for c in n.get("Flow", []))
                return True
            if t in ("Block", "Standard"):
                seq.append(n["ID"])
                return True
            if t == "EndSurvey":
                return False
            assert t == "Root", t
            for c in n.get("Flow", []):
                if not go(c):
                    break
            return True

        go(self.flow)
        return ed, seq

    def shown(self, qid: str, ed: dict[str, str]) -> bool:
        dl = self.by_id[qid].get("DisplayLogic")
        return True if not dl else self.holds(dl, ed)


def graphics_in(raw: str) -> tuple[set[str], set[str]]:
    """(questions holding an <img>, Qualtrics graphic ids) in a .qsf's text."""
    d = json.loads(raw)
    qs = {
        e["Payload"]["QuestionID"]
        for e in d["SurveyElements"]
        if e["Element"] == "SQ" and "<img" in json.dumps(e["Payload"])
    }
    return qs, set(re.findall(r"IM_\w+", raw))


# The one picture in any built .qsf: 5b's pre-consent screener (see the docstring).
PICTURES = {"study5b": ({"QID1184"}, {"IM_8kwY19HHmEvCh6e"})}


def check_pictures(spec: Spec) -> None:
    sv = Survey(spec.qsf)
    want = PICTURES.get(spec.name, (set(), set()))
    assert graphics_in(sv.raw) == want, (spec.name, graphics_in(sv.raw))
    for qid in want[0]:  # it is the screener, which no row carries
        assert SCREENER.match(plain(sv.by_id[qid]["QuestionText"])), qid
        assert spec.screener


def check_order_unrecorded(spec: Spec) -> None:
    """No display-order column anywhere in the data file."""
    cols = read_deposit(spec).columns
    assert not [c for c in cols if c.endswith("_DO") or c.startswith("FL_")], spec.name


# ---------------------------------------------------------------------------
# The studies
# ---------------------------------------------------------------------------

POSITIVITY = ["admire", "favor", "positive"]


@dataclass
class Spec:
    name: str
    label: str  # the box's section name
    qsf: Path
    data: Path
    assign: dict[str, str]  # data/embedded field -> factor name, in flow order
    outcomes: list[str]  # export tags, all on the first measure page(s)
    attn: dict[str, int] | None  # condition -> the recall answer the .rmd keeps
    kind: str
    title: str
    n_kept: int  # the authors' N after their exclusions
    prereg: str
    sample: str
    not_built: str  # later outcomes, with the reason
    key: list[str]  # the authors' model: "<dv> ~ <terms>" (see `key_terms`)
    contrast: dict[str, str] = field(default_factory=dict)  # factor -> the +.5 level
    order: dict[str, list[str]] = field(default_factory=dict)  # the .rmd's factor() levels
    screener: bool = False


def _m(f: str) -> Path:
    return RAW / "Materials" / f


def _d(f: str) -> Path:
    return RAW / "Data" / f


LATER = (
    "Not built: the {blocks} blocks that follow the admire/favor/positive page, shown in a "
    "block order the .qsf randomises and the deposit does not record, so their rows would "
    "follow earlier questions that cannot be narrated in order; and the recall check "
    "(attention, used only for the exclusion)."
)
RECALL = "Not built: the recall check (attention, used only for the exclusion)."
SLIDER_SENTENCE = 'The answer was a slider from 0 to 100, labelled "{label}".'  # ours
LATER_BUILT = (
    "The {blocks} blocks after the admire/favor/positive page are built (rich, 20 Nov 2026), "
    "shown in a block order the .qsf randomises and the deposit does not record: each row "
    "carries the scenario, that block's own reminder and its own question only, with nothing "
    "narrated about the other blocks, as 5a's two pages are. Matrix rows are one outcome each, "
    "the row's label appended to the stem in double quotes (layout, ours), each column tied "
    "to its row by the authors' codebook."
    " A slider question is followed by one sentence of ours naming its only label, written "
    "word-for-word in these notes."
)
COMPOSITES_COLS = {
    "commit": ["commit_1", "commit_2", "commit_3"],
    "impact": ["impact_1", "impact_2", "impact_3"],
    "sacrifice": ["sac1", "sac2", "sac3"],
    "skepticism": ["skept_1", "skept_2", "skept_3"],
}

ALL_SPECS = [
    Spec(
        name="study2",
        label="2. Stimulus sampling",
        qsf=_m("2. Stimulus sampling.qsf"),
        data=_d("2. Stimulus sampling.csv"),
        assign={"amount": "amount", "scenario": "cause", "condition": "schedule"},
        outcomes=["purchase"],
        attn={"aggregate": 1, "periodic": 2},
        kind="mix",
        title="A fashion retailer with a store near you pledges to one of six causes, one sum "
        "in 2024 or the same sum every month, at six sizes: how likely are you to buy from it? "
        "(Study 2)",
        n_kept=1540,
        prereg="AsPredicted #165250",
        sample="CloudResearch Connect, March 2024",
        not_built=RECALL,
        key=["purchase ~ schedule + amount + cause"],
    ),
    Spec(
        name="study3",
        label="3. Serial mediation",
        qsf=_m("3. Serial mediation.qsf"),
        data=_d("3. Serial mediation.csv"),
        assign={"condition": "schedule"},
        outcomes=[*POSITIVITY, *COMPOSITES_COLS["commit"], *COMPOSITES_COLS["impact"]],
        attn={"aggregate": 1, "periodic": 2},
        kind="version",
        title="A fashion retailer pledges $6 million in 2024 or $500,000 every month in 2024 "
        "to wildlife and environmental conservation: how much would you admire it, and how "
        "committed and impactful is it? (Study 3)",
        n_kept=556,
        prereg="AsPredicted #188881",
        sample="Prolific, September 2024",
        not_built=LATER_BUILT.format(blocks="commitment and impact") + " " + RECALL,
        key=["positivity ~ schedule", "commit ~ schedule", "impact ~ schedule"],
    ),
    Spec(
        name="study4",
        label="4. Prosocial Motivation Moderator",
        qsf=_m("4. Prosocial Motivation Moderator.qsf"),
        data=_d("4. Prosocial Motivation Moderator.csv"),
        assign={"condition": "schedule", "cond2": "follower"},
        outcomes=POSITIVITY,
        attn={"aggregate": 1, "periodic": 2},
        kind="mix",
        title="A financial services company's donation campaign, $6 million once or $500,000 "
        "every month in 2025, started or not only after its main competitor announced one: "
        "how much would you admire it? (Study 4)",
        n_kept=1778,
        prereg="AsPredicted #211193",
        sample="Prolific, February 2025",
        not_built=RECALL,
        key=["positivity ~ schedule * follower"],
        contrast={"schedule": "periodic", "follower": "follower"},
    ),
    Spec(
        name="study5a",
        label="5a. Total donation size",
        qsf=_m("5a. Total donation size.qsf"),
        data=_d("5a. Total donation size.csv"),
        assign={"condition": "schedule", "money": "money"},
        outcomes=[*POSITIVITY, "praiseworthy"],
        attn={"aggregate": 2, "periodic": 1},
        kind="mix",
        title="A business owner donates to disaster relief, $100 or $520,000 this year, or $2 "
        "or $10,000 every week: how much do you admire the business, and how praiseworthy "
        "is it? (Study 5a)",
        n_kept=1181,
        prereg="AsPredicted #107475",
        sample="Prolific, September 2022",
        not_built=RECALL
        + " The admire/favor/positive page and the praiseworthy page are the two blocks of "
        "one randomiser, in an order the deposit does not record; each row carries its own "
        "page only.",
        key=["positivity ~ schedule * money", "praiseworthy ~ schedule * money"],
        contrast={"schedule": "periodic", "money": "high"},
    ),
    Spec(
        name="study5b",
        label="5b (new study). Modest amount",
        qsf=_m("5b new study. Modest amount.qsf"),
        data=_d("5b new study. Modest amount.csv"),
        assign={"condition": "schedule", "amount": "amount"},
        outcomes=[*POSITIVITY, "engage"],
        attn={"aggregate": 1, "periodic": 2},
        kind="mix",
        title="A business owner donates to disaster relief, $100, $2,500 or $500,000 this "
        "year, or $2, $50 or $10,000 every week: how much would you admire the business, and "
        "would you like a social media post about it? (Study 5b)",
        n_kept=2418,
        prereg="AsPredicted #252061",
        sample="Prolific, October 2025",
        not_built=RECALL,
        key=["positivity ~ schedule * amount", "engage ~ schedule * amount"],
        order={"amount": ["low", "modest", "high"]},
        screener=True,
    ),
    Spec(
        name="study5b_2024",
        label="5b. Modest amounts (deleted after the box was public)",
        qsf=DELETED / "Materials" / "5b. Modest amounts.qsf",
        data=DELETED / "Data" / "5b. Modest amounts.csv",
        assign={"condition": "schedule", "money": "money"},
        outcomes=POSITIVITY,
        attn={"aggregate": 1, "periodic": 2},
        kind="mix",
        title="A clothing retailer pledges to wildlife and environmental conservation, $6 "
        "million or $600 in total in 2024, or $500,000 or $50 every month: how much would you "
        "admire it? (withdrawn Study 5b, 2024)",
        n_kept=759,
        prereg="AsPredicted #185918",
        sample="Prolific, August 2024",
        not_built=LATER.format(blocks="impact and commitment"),
        key=["positivity ~ schedule * money"],
        contrast={"schedule": "periodic", "money": "large"},
    ),
    Spec(
        name="w1",
        label="W1. Company eval stimulus sampling",
        qsf=_m("W1. Company eval stimulus sampling.qsf"),
        data=_d("W1. Company eval stimulus sampling.csv"),
        assign={"condition": "schedule", "scenario": "company"},
        outcomes=POSITIVITY,
        attn={"aggregate": 1, "periodic": 2},
        kind="mix",
        title="Nine companies, each pledging to its own cause one sum in 2023 or a monthly sum "
        "through 2023: how much do you admire it? (Study W1)",
        n_kept=1665,
        prereg="AsPredicted #108254",
        sample="Prolific, September 2022",
        not_built=RECALL,
        key=["positivity ~ schedule + company"],
    ),
    Spec(
        name="w2",
        label="W2. Inference Control",
        qsf=_m("W2. Inference Control.qsf"),
        data=_d("W2. Inference Control.csv"),
        assign={"condition": "schedule"},
        outcomes=["purchase"],
        attn=None,
        kind="version",
        title="A fashion retailer pledges $6 million in 2024, $500,000 every month, or $500,000 "
        "every month with the $6 million total stated: how likely are you to buy from it? "
        "(Study W2)",
        n_kept=1203,
        prereg="AsPredicted #167438",
        sample="CloudResearch Connect, March 2024",
        not_built="No recall check in this study.",
        key=["purchase ~ schedule"],
    ),
    Spec(
        name="w3",
        label="W3. Donation size post-test",
        qsf=_m("W3. Donation size post-test.qsf"),
        data=_d("W3. Donation size post-test.csv"),
        assign={"condition": "schedule"},
        outcomes=["reasonable"],
        attn=None,
        kind="version",
        title="A business owner donates $100 this year or $2 every week to disaster relief: "
        "how reasonable is that amount? (Study W3)",
        n_kept=100,
        prereg="none in the box",
        sample="Prolific, February 2025",
        not_built="No recall check in this study.",
        key=["reasonable ~ schedule"],
    ),
    Spec(
        name="w4",
        label="W4. Addressing alternatives",
        qsf=_m("W4. Addressing alternatives.qsf"),
        data=_d("W4. Addressing alternatives.csv"),
        assign={"condition": "schedule"},
        outcomes=[
            *POSITIVITY,
            *COMPOSITES_COLS["sacrifice"],
            *COMPOSITES_COLS["commit"],
            "future_95",
            *COMPOSITES_COLS["skepticism"],
            *COMPOSITES_COLS["impact"],
        ],
        attn={"aggregate": 1, "periodic": 2},
        kind="version",
        title="A fashion retailer pledges $720,000 in 2024 or $60,000 every month to end world "
        "hunger: how much would you admire it, and how costly, committed, lasting, self-serving "
        "and impactful is it? (Study W4)",
        n_kept=429,
        prereg="AsPredicted #158321",
        sample="Prolific, January 2024",
        not_built=LATER_BUILT.format(
            blocks="sacrifice, commitment, future donation likelihood, skepticism and impact"
        )
        + " The future-likelihood slider keeps its fielded range (0-100, whole numbers, no end "
        "labels); added words (ours), after its question: '"
        + SLIDER_SENTENCE.format(label="Percent (%) likelihood")
        + "' "
        + RECALL,
        key=[
            "positivity ~ schedule",
            "sacrifice ~ schedule",
            "commitment ~ schedule",
            "future_95 ~ schedule",
            "skepticism ~ schedule",
            "impact ~ schedule",
        ],
    ),
    Spec(
        name="w5",
        label="W5. Another moderator",
        qsf=_m("W5. Another moderator.qsf"),
        data=_d("W5. Another moderator.csv"),
        assign={"condition": "schedule", "cond2": "reputation"},
        outcomes=POSITIVITY,
        attn={"aggregate": 1, "periodic": 2},
        kind="mix",
        title="A fashion retailer pledges $6 million in 2024 or $500,000 every month to "
        "conservation, and is or is not also known for severe environmental damage: how much "
        "would you admire it? (Study W5)",
        n_kept=1643,
        prereg="AsPredicted #186611",
        sample="Prolific, August 2024",
        not_built=LATER.format(blocks="commitment, impact and skepticism")
        + " Pending rich's ruling (20 Nov 2026: the later blocks are built for the A/B studies, "
        "3 and W4, only).",
        key=["positivity ~ schedule * reputation"],
        contrast={"schedule": "periodic", "reputation": "low"},
    ),
]
# The withdrawn study keeps its spec for the record (and for the two-5b proof); nothing
# writes or builds it.
SPECS = [s for s in ALL_SPECS if s.name not in NOT_BUILT]
BY_NAME = {s.name: s for s in ALL_SPECS}

# Screens dropped wherever they appear before the measures (see the docstring).
WELCOME = re.compile(r"^Welcome to the survey!")
SCREENER = re.compile(r"^Below are the instructions for this survey\.")


# ---------------------------------------------------------------------------
# Arms
# ---------------------------------------------------------------------------


@dataclass
class Arm:
    values: dict[str, str]  # assignment field -> value, as the data records it
    ed: dict[str, str]  # every embedded field the flow set
    text: str
    questions: dict[str, str]  # export tag -> its wording for this arm
    scales: dict[str, dict[str, Any]]


def levels(sv: Survey, spec: Spec) -> dict[str, list[str]]:
    """Each assignment field's values, in the .qsf's order (first randomiser setting it)."""
    found: dict[str, list[str]] = {f: [] for f in spec.assign}

    def go(n: dict[str, Any]) -> None:
        if n.get("Type") == "BlockRandomizer" and all(
            k["Type"] == "EmbeddedData" for k in n["Flow"]
        ):
            for k in n["Flow"]:
                for e in k["EmbeddedData"]:
                    f, v = e["Field"], e.get("Value")
                    if f in found and v not in found[f]:
                        found[f].append(v)
        for c in n.get("Flow", []):
            go(c)

    go(sv.flow)
    assert all(found.values()), found
    return found


def outcome_scale(q: dict[str, Any]) -> dict[str, Any]:
    assert q["QuestionType"] == "MC" and q["Selector"] == "SAHR", q["DataExportTag"]
    rv = q["RecodeValues"]
    order = sorted(q["Choices"], key=lambda k: int(rv[k]))
    codes = [int(rv[k]) for k in order]
    assert codes == list(range(1, len(codes) + 1)), codes
    disp = [plain(q["Choices"][k]["Display"]) for k in order]
    for i, d in enumerate(disp[1:-1], 2):
        assert d == str(i), disp
    lo = re.fullmatch(r"(?:1 )?(.+?)(?: 1)?", disp[0])
    hi = re.fullmatch(rf"(?:{len(codes)} )?(.+?)(?: {len(codes)})?", disp[-1])
    assert lo and hi, disp
    return {
        "min": 1,
        "max": len(codes),
        "min_label": lo.group(1),
        "max_label": hi.group(1),
    }


@dataclass
class Item:
    """What one data column answers: a question, and for a matrix or slider its row."""

    qid: str
    tag: str
    row: str | None  # the matrix row / slider choice id, else None


def resolve(sv: Survey, col: str) -> Item:
    """The fielded question a data column answers. Single questions are their export tag;
    a matrix column <tag>_<k> is the k-th row in ChoiceOrder (as the codebook states, see
    `check_codebook`); a slider column <tag>_<choice id> is that choice."""
    by_tag = {p["DataExportTag"]: q for q, p in sv.by_id.items()}
    if col in by_tag:
        return Item(by_tag[col], col, None)
    m = re.fullmatch(r"(\w+?)_(\d+)", col)
    assert m and m.group(1) in by_tag, col
    qid = by_tag[m.group(1)]
    p = sv.by_id[qid]
    k = m.group(2)
    if p["QuestionType"] == "Matrix":
        assert p["Selector"] == "Likert" and p["SubSelector"] == "SingleAnswer", col
        assert p["ChoiceDataExportTags"] is False, col
        return Item(qid, m.group(1), str(p["ChoiceOrder"][int(k) - 1]))
    assert p["QuestionType"] == "Slider" and k in p["Choices"], col
    return Item(qid, m.group(1), k)


def item_scale(p: dict[str, Any]) -> dict[str, Any]:
    if p["QuestionType"] == "MC":
        return outcome_scale(p)
    if p["QuestionType"] == "Slider":
        c = p["Configuration"]
        assert p["Selector"] == "HSLIDER" and c["NumDecimals"] == "0" and not p.get("Labels")
        return {"min": int(c["CSSliderMin"]), "max": int(c["CSSliderMax"])}
    # a Likert matrix: the answers are the scale, recoded 1..k
    rv = p["RecodeValues"]
    order = [str(a) for a in p["AnswerOrder"]]
    assert [int(rv[a]) for a in order] == list(range(1, len(order) + 1)), rv
    disp = [plain(p["Answers"][a]["Display"]) for a in order]
    n = len(order)
    for i, d in enumerate(disp[1:-1], 2):
        assert d == str(i), disp
    lo, hi = re.fullmatch(r"(.+?) 1", disp[0]), re.fullmatch(rf"(.+?) {n}", disp[-1])
    assert lo and hi, disp
    return {"min": 1, "max": n, "min_label": lo.group(1), "max_label": hi.group(1)}


def item_question(p: dict[str, Any], it: Item, ed: dict[str, str], known: set[str]) -> str:
    """The question as fielded; a matrix row is appended in double quotes (layout, ours),
    a slider gets SLIDER_SENTENCE naming its own label."""
    stem = plain(pipe(p["QuestionText"], ed, known))
    if it.row is None:
        return stem
    label = plain(pipe(p["Choices"][it.row]["Display"], ed, known))
    if p["QuestionType"] == "Matrix":
        return f'{stem} "{label}"'
    return f"{stem} {SLIDER_SENTENCE.format(label=label)}"


def build_arm(sv: Survey, spec: Spec, values: dict[str, str]) -> Arm:
    ed, seq = sv.walk(values)
    for f, v in values.items():
        assert ed.get(f) == v, (f, ed.get(f), v)
    flat: list[tuple[str, str]] = []  # (block id, qid) in flow order
    group_of: dict[str, list[str]] = {}
    for item in seq:
        ids = item if isinstance(item, list) else [item]
        for b in ids:
            if isinstance(item, list):
                group_of[b] = item
            flat.extend((b, q) for q in sv.qids(b))
    block_of = {q: b for b, q in flat}
    items = {c: resolve(sv, c) for c in spec.outcomes}
    assert all(it.qid in block_of for it in items.values()), spec.name
    # The measure blocks: each outcome's own block, and every block of its randomiser.
    measure_blocks: set[str] = set()
    for it in items.values():
        b = block_of[it.qid]
        measure_blocks |= set(group_of.get(b, [b]))
    start = min(i for i, (b, _) in enumerate(flat) if b in measure_blocks)
    before: list[str] = []
    for _, q in flat[:start]:
        p = sv.by_id[q]
        if p["QuestionType"] == "Timing" or not sv.shown(q, ed):
            continue
        if p["QuestionType"] != "DB":
            # nothing is asked before the measures but consent, id and the screener
            assert p["DataExportTag"] in {*GATES, "prolific id", "ID"}, p["DataExportTag"]
            continue
        t = screen_text(pipe(p["QuestionText"], ed, sv.fields))
        if WELCOME.match(t) or (spec.screener and SCREENER.match(t)):
            continue
        before.append(t)
    reminders: dict[str, str] = {}
    questions: dict[str, str] = {}
    scales: dict[str, dict[str, Any]] = {}
    for col, it in items.items():
        b = block_of[it.qid]
        shown = []
        for q in sv.qids(b):
            p = sv.by_id[q]
            if p["QuestionType"] == "DB" and sv.shown(q, ed):
                shown.append(screen_text(pipe(p["QuestionText"], ed, sv.fields)))
        # one reminder, at the top of the outcome's own page: the only screen it adds
        (reminders[col],) = shown
        assert sv.by_id[sv.qids(b)[0]]["QuestionType"] == "DB", b
        assert "Page Break" not in json.dumps(sv.blocks[b]), b
        p = sv.by_id[it.qid]
        assert not p.get("DisplayLogic"), col
        questions[col] = item_question(p, it, ed, sv.fields)
        scales[col] = item_scale(p)
    assert len(set(reminders.values())) == 1, reminders  # every measure page's reminder
    text = "\n\n".join([*before, next(iter(reminders.values()))])
    return Arm(values, ed, text, questions, scales)


def arms(spec: Spec) -> list[Arm]:
    sv = Survey(spec.qsf)
    lv = levels(sv, spec)
    out = []
    for combo in itertools.product(*lv.values()):
        out.append(build_arm(sv, spec, dict(zip(lv, combo, strict=True))))
    return out


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

AGE_RANGE = (18, 100)
GENDER_REFUSAL = "Prefer not to say"
# Columns the flow sets from the assignment; checked against the arm for every kept row.
FILLS = ["amount", "scenario", "cause", "condition", "price", "price2", "frequency"]
FILLS += ["company", "brand", "money", "cond2", "action"]


def read_deposit(spec: Spec) -> pd.DataFrame:
    return pd.read_csv(spec.data, keep_default_na=True)


def kept(spec: Spec) -> pd.DataFrame:
    """The authors' analysed sample, by their .rmd, in order."""
    df = read_deposit(spec)
    df = df[(df["Status"] == 0) & (df["Finished"] == 1)]
    if spec.screener:
        df = df[df["filter"] == 1]
    if spec.attn:
        ok = pd.Series(False, index=df.index)
        for cond, a in spec.attn.items():
            ok |= (df["condition"] == cond) & (df["attn"] == a)
        df = df[ok]
    assert len(df) == spec.n_kept, (spec.name, len(df), spec.n_kept)
    return df


def _norm(v: Any) -> str | None:
    if pd.isna(v):
        return None
    return re.sub(r"\s+", " ", plain(str(v))).strip()


def check_data_matches_qsf(spec: Spec, df: pd.DataFrame | None = None) -> None:
    """Every kept row's recorded fills are exactly what the .qsf sets for its assignment."""
    df = kept(spec) if df is None else df
    by_values = {tuple(a.values[f] for f in spec.assign): a for a in arms(spec)}
    sv = Survey(spec.qsf)
    flow_tags = {sv.tag(q) for b in sv.blocks for q in sv.qids(b)}
    assert set(spec.outcomes) <= set(df.columns)
    assert {resolve(sv, c).tag for c in spec.outcomes} <= flow_tags
    for _, r in df.iterrows():
        a = by_values[tuple(r[f] for f in spec.assign)]
        for c in FILLS:
            if c in df.columns:
                assert _norm(r[c]) == _norm(a.ed.get(c)), (spec.name, c, r[c], a.ed.get(c))


def check_codebook(spec: Spec) -> None:
    """Each matrix column <tag>_<k> is the k-th row: the authors' codebook says so, naming
    the row's own words, and no other row's."""
    sv = Survey(spec.qsf)
    book = pd.read_csv(RAW / "Codebook" / f"{spec.data.name}___CODEBOOK.csv")
    desc = dict(zip(book["varname"], book["description"], strict=True))

    def norm(t: str) -> str:
        return re.sub(r"[^a-z]+", " ", t.lower()).strip()

    for col in spec.outcomes:
        it = resolve(sv, col)
        p = sv.by_id[it.qid]
        if p["QuestionType"] != "Matrix":
            continue
        rows = {k: norm(plain(p["Choices"][k]["Display"])) for k in p["ChoiceOrder"]}
        rows = {k: r.replace("yna corp s", "").strip() for k, r in rows.items()}
        hits = [k for k, r in rows.items() if r in norm(desc[col])]
        assert hits == [it.row], (spec.name, col, hits, it.row)


def gender_labels(sv: Survey) -> dict[int, str]:
    q = next(p for p in sv.by_id.values() if p["DataExportTag"] == "gender")
    rv = q["RecodeValues"]
    return {int(rv[k]): plain(v["Display"]) for k, v in q["Choices"].items()}


def data_file(spec: Spec) -> str:
    return f"{STUDY_ID}_{spec.name}.csv"


def codes(spec: Spec) -> dict[str, dict[str, int]]:
    """Assignment value -> code (1..k, the .qsf's order)."""
    lv = levels(Survey(spec.qsf), spec)
    return {f: {v: i for i, v in enumerate(vals, 1)} for f, vals in lv.items()}


def prep(spec: Spec) -> pd.DataFrame:
    """One coded row per kept person: assignment codes, answers, age, gender."""
    df = kept(spec)
    check_data_matches_qsf(spec, df)
    check_pictures(spec)
    check_order_unrecorded(spec)
    check_codebook(spec)
    sv = Survey(spec.qsf)
    out = pd.DataFrame({"pid": [f"{spec.name}_{i}" for i in df.index]})
    for f, cmap in codes(spec).items():
        out[f] = df[f].map(cmap).astype(int).values
    for t in spec.outcomes:
        v = pd.to_numeric(df[t], errors="raise")
        top = item_scale(sv.by_id[resolve(sv, t).qid])
        ok = v.dropna()
        assert (ok % 1 == 0).all() and ok.between(top["min"], top["max"]).all(), t
        out[t] = v.astype("Int64").values
    age = pd.to_numeric(df["age"], errors="coerce")
    out["age"] = age.where(age.between(*AGE_RANGE)).round().astype("Int64").values
    labels = gender_labels(sv)
    assert labels == {1: "Male", 2: "Female", 3: "Non-Binary", 4: GENDER_REFUSAL}, labels
    g = df["gender"].map(lambda x: labels[int(x)] if pd.notna(x) else None)
    out["gender"] = g.where(g != GENDER_REFUSAL).values
    assert out["pid"].is_unique
    return out


# ---------------------------------------------------------------------------
# The answer key: the authors' models (see the .rmd files)
# ---------------------------------------------------------------------------


# The .rmd composites: the mean of three items, NA if any is missing.
COMPOSITES = {"positivity": POSITIVITY, "commitment": COMPOSITES_COLS["commit"]}
COMPOSITES |= COMPOSITES_COLS


def composite(frame: pd.DataFrame, dv: str) -> pd.Series:
    if dv in COMPOSITES:
        return frame[COMPOSITES[dv]].sum(axis=1, min_count=3) / 3
    return frame[dv]


def key_terms(spec: Spec, formula: str, frame: pd.DataFrame) -> dict[str, float]:
    """OLS coefficients of the authors' model on a frame with factor columns (levels as the
    data names them) and the outcome columns. R's coding: treatment against the first level
    in sorted order, or the authors' +/-.5 contrast where they used one; '*' adds the
    interaction."""
    import numpy as np

    dv, rhs = (s.strip() for s in formula.split("~"))
    inter = "*" in rhs
    facs = [t.strip() for t in re.split(r"[+*]", rhs)]
    y = composite(frame, dv)
    keep = y.notna()
    for f in facs:
        keep &= frame[f].notna()
    d = frame[keep]
    cols: dict[str, Any] = {"(Intercept)": np.ones(len(d))}
    parts: dict[str, list[str]] = {}
    for f in facs:
        if f in spec.contrast:
            name = f"{f}C"
            cols[name] = np.where(d[f] == spec.contrast[f], 0.5, -0.5)
            parts[f] = [name]
        else:
            lv = spec.order.get(f) or sorted(d[f].unique())
            assert set(lv) == set(d[f].unique()), (f, lv)
            parts[f] = []
            for v in lv[1:]:
                name = f"{f}{v}"
                cols[name] = (d[f] == v).astype(float).to_numpy()
                parts[f].append(name)
    if inter:
        assert len(facs) == 2
        for a in parts[facs[0]]:
            for b in parts[facs[1]]:
                cols[f"{a}:{b}"] = cols[a] * cols[b]
    x = np.column_stack(list(cols.values()))
    b, *_ = np.linalg.lstsq(x, y[keep].to_numpy(float), rcond=None)
    out = dict(zip(cols, (float(v) for v in b), strict=True))
    out["n"] = float(len(d))
    return out


def deposit_frame(spec: Spec) -> pd.DataFrame:
    """The kept deposit with factor columns named as the recipe names them."""
    df = kept(spec)
    out = pd.DataFrame({fac: df[f].values for f, fac in spec.assign.items()})
    for t in spec.outcomes:
        out[t] = pd.to_numeric(df[t]).values
    return out


# ---------------------------------------------------------------------------
# The recipes
# ---------------------------------------------------------------------------


def recipe(spec: Spec) -> dict[str, Any]:
    arm_list = arms(spec)
    cmap = codes(spec)
    first = arm_list[0]
    per_arm = [t for t in spec.outcomes if len({a.questions[t] for a in arm_list}) > 1]
    out_arms = []
    for i, a in enumerate(arm_list):
        arm: dict[str, Any] = {
            "raw_values": {f: cmap[f][v] for f, v in a.values.items()},
            "condition_num": i,
            "factors": {spec.assign[f]: v for f, v in a.values.items()},
            "text": a.text,
        }
        if per_arm:
            arm["items"] = {
                spec.outcomes.index(t): {"outcome_question": a.questions[t]} for t in per_arm
            }
        out_arms.append(arm)
        assert a.scales == first.scales
    outcomes = [
        {"var": t, "task_num": i, "question": first.questions[t], "scale": first.scales[t]}
        for i, t in enumerate(spec.outcomes)
    ]
    lo = min(s["min"] for s in first.scales.values())
    hi = max(s["max"] for s in first.scales.values())
    per = (
        " The question names the arm's own "
        + ("company" if spec.name == "w1" else "amount")
        + f" ({', '.join(per_arm)}), so every arm carries its own wording; the Outcome-level "
        "question is the first arm's form, overridden on every arm."
        if per_arm
        else ""
    )
    notes = (
        f"{SOURCE}\n\nGENERATED by scripts/gen_researchbox809.py; every judgement is in its "
        f"docstring. {spec.label} ({spec.prereg}; {spec.sample}; US sample). "
        f"{spec.n_kept:,} people kept by the authors' .rmd (Status 0, Finished 1"
        + (", the screener answered right" if spec.screener else "")
        + (", the recall check answered right for the arm" if spec.attn else "")
        + "). Between-person: one scenario each, assigned by the .qsf's randomisers "
        f"({', '.join(spec.assign)}; every recorded fill checked against the .qsf for every "
        "kept row). The row is every text screen from the scenario's first screen to the "
        "reminder at the top of the measure page, word-for-word with its piped fields filled; "
        "the welcome screen, consent and id are dropped; bullets are written as lines "
        f"starting '- '.{per} {spec.not_built}\n\nWording from {spec.qsf.name} (the blocks "
        "the survey flow reaches). Typography normalised (HTML, non-breaking spaces, curly "
        f"quotes); bold and underline dropped. Data: {spec.data.name}. Persona: age (years; "
        "outside 18-100 left blank) and gender (the .qsf's labels; 'Prefer not to say' left "
        "blank). US sample, US dollars; invented companies"
        + (" except the withdrawn study's real retailer" if spec.name == "study5b_2024" else "")
        + "."
    )
    return {
        "study_id": STUDY_ID,
        "source": "researchbox",
        "experiment": spec.name,
        "title": spec.title,
        "data_file": data_file(spec),
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": "pid",
        "notes": notes,
        "condition": {
            "source_vars": list(spec.assign),
            "factors": list(spec.assign.values()),
            "arms": out_arms,
        },
        "outcomes": outcomes,
        "response_recode": {k: k for k in range(lo, hi + 1)},
        "missing_codes": [],
        "persona_map": {"age": "age", "gender": "gender"},
    }


def recipe_path(spec: Spec) -> Path:
    return RECIPES / f"{STUDY_ID}_{spec.name}.yaml"


def render(spec: Spec) -> str:
    return yaml.safe_dump(recipe(spec), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prep", action="store_true", help="code the data")
    ap.add_argument("--check", action="store_true", help="exit 1 if any recipe differs")
    args = ap.parse_args()
    if args.prep:
        for spec in SPECS:
            path = RAW / data_file(spec)
            prep(spec).to_csv(path, index=False)
            print(f"wrote {path.relative_to(REPO)}")
        return 0
    bad = 0
    for spec in SPECS:
        path, text = recipe_path(spec), render(spec)
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
