#!/usr/bin/env python3
"""Write recipes/researchbox2057_*.yaml: forced choice versus a no-choice option (9 recipes).

"A Reexamination of the Effect of Forced Choice" (ResearchBox 2057,
https://researchbox.org/2057), read from its Zenodo copy (https://zenodo.org/records/21935325).
CC BY 4.0 ("All content posted to ResearchBox is under a CC By 4.0 License", the box page).
The box is anonymous (every AsPredicted pre-registration "is currently anonymous to enable
blind peer-review", one author) and names no paper; nothing here names an author. Nine
pre-registered replications of Dhar and Simonson (2003) on whether being made to choose, or
being free to walk away, changes WHICH option people pick. Fielded 2022-2025 (StartDate in
the timestamped files, never printed per person). Prices in US dollars, distances in miles,
kept as the source has them.

Every judgement is here, in code, so the recipes can be re-derived and reviewed.

THE BOX. Per study (1a, 1b, 2a, 2b, 3a, 3b, 4a, 4b, S1): a fielded Qualtrics .qsf and its PDF
printout, the data (.csv, and .sav except 1a, whose .sav the authors withdrew after the box
went public), a codebook, the authors' R code and an AsPredicted pre-registration.
Other/Additional Files.zip, added after acceptance, holds the same data with Qualtrics
timestamps, two R files that reproduce the paper's Tables 3-4 with the printed shares in
comments, and a Readme. `check_timestamped` asserts each timestamped file's answer, age and
gender columns equal the main .csv cell for cell, in the same row order, every response
Finished; so the main .csv is the complete, unfiltered sample. Every pre-registration says
"I will not exclude any data", and the R code excludes nothing: N is the whole file.

THE DESIGN, one shape throughout. Everyone read several choice problems (a product, a
restaurant, an apartment or a university applicant) on their own pages, each a short lead
and a table of two or three options, and answered "What would you do?". The survey flow
assigns each person to ONE between-person group (a BlockRandomizer showing 1 of its
branches), and each group's branch is a BlockRandomizer showing ALL its problem blocks in a
random order (SubSet = number of blocks, asserted). The groups:
- 1a, 1b: forced (pick A or B) or with a no-choice option (A, B or look elsewhere); one
  option is all-average, the other mixed. 1a (students, a university lab) prefixes the
  no-choice question with "As in normal purchase situations, you have the option of not
  choosing either of the two alternatives and look for other options."; 1b does not.
- 2a: 2 (forced, no-choice option) x 2 (two options, or a third: a compromise option in
  three problems, an asymmetrically dominated decoy in the other three).
- 2b, S1: 2 (forced, no-choice option) x 3 (two options, a dominated decoy, a compromise).
  In 2b the no-choice option is listed FIRST and the lead adds "You may also reject these
  options and go to another store." (or the rental-agency wording); in S1 it is last and
  the lead is unchanged.
- 3a, 3b: everyone has the no-choice option; one attribute is given as a single expert
  value or as a range (3a "82 to 86" written with a minus sign, 3b "Expert 1: 82; Expert 2:
  86").
- 4a, 4b: single stage (A, B [, C] or go to another store) or two stage (a forced choice,
  then, on the next page, "Next, think about the ... you just saw and the one you chose. If,
  instead of buying ..., you had the option of going to another store ... would you").

WHAT IS BUILT. Every study, every choice problem, one row per person per problem. Each ARM
is one problem as one group saw it (its block), so arm text is that page's own words, and
each outcome (one per problem) names its own assignment column `cell_<problem>` (the
within-person pattern, Outcome.condition_var): a person's arm for a problem is the block of
their group. The problem order was randomised and is not recorded, so no row says anything
about any other problem.

NOT BUILT (NOT_BUILT_OUTCOMES; no whole study fails):
- 4a, 4b, the two-stage group's second question. It asks about "the one you chose", the
  person's own answer on the page before, which no row can carry; and its row would have to
  narrate that answer. Not built. The authors' focal 4a/4b test (deferral, single vs
  two stage) uses it, so the answer key there is partial (see ANSWER KEY).
- 4a, 4b, the filler problems (backpacks, mouthwash, frying pans; data Q29-Q39), shown
  after each focal problem: identical in both groups, not a manipulation.
- 2b's three conflict ratings after each choice ("To what extent did... the decision feel
  like a dilemma / a "tough choice" / the options feel similar in attractiveness", 1-7).
  The pre-registration lists them with no prediction. They rate the person's own decision
  just made, so the same row-cannot-carry-the-answer problem; not built.

WHERE THE MANIPULATION LIVES. In 1a, 1b, 2a, S1, 4a and 4b the forced and no-choice pages of a
problem show the SAME lead and table; the manipulation is in the answer options (and, in
1a, in the question's own first sentence). So it is in the OUTCOME: each arm carries its own
question with its options enumerated (Arm.outcome_question, a nominal scale, its own
recode), and the factor `choice` is recorded on every arm but declared in
`condition.factors` only where the page text expresses it (2b), since QC rule 5 tests the
condition text and nothing else. Where two arms of one problem show identical page text, both
declare it (`items.<task>.condition_text`), as QC rule 1 requires of a deliberate collision.
`choice_in_text` derives this mechanically.

THE WORDING. Every lead, table, question and option is the .qsf's, word-for-word, from the
blocks the flow reaches. A table becomes one line per row, its non-empty cells joined by
" | " (the researchbox755 layout; no words added); the header row's empty corner cell is
dropped. Typography only is normalised (HTML, non-breaking spaces, curly quotes); the
minus sign (U+2212) in 3a's ranges is kept as the source has it. Dropped: the intro screen
("Thank you for your willingness to participate ...", survey mechanics, the same for all).
The question and its options become one outcome, options enumerated in the instrument's
fixed order (no choice randomisation in any built question, asserted):
  'What would you do? 1 means "I would buy Brand A"; 2 means "I would buy Brand B".'
The "N means" join is ours (the researchbox3299 form). A two-paragraph question (1a's
no-choice one) is joined with a space.

CODES. Each option's code in the data is read from the .sav's value labels (every study
but 1a, whose .sav was withdrawn): each option's words must label exactly one code, and
where the .qsf has RecodeValues they must agree (asserted, 1b-4b and S1). Two exceptions,
both asserted: 1a has no .sav and uses its .qsf's RecodeValues; 3a's .qsf has NO
RecodeValues (keys 1, 2, 4) while its .sav and the authors' R code put the way out at 3, so
the .sav wins (QSF_RECODE_MISSING). S1 has no RecodeValues and its data hold the raw keys
1, 2, 4, 6, which its .sav labels confirm. Each arm's recode maps the data code to the
option's position on screen (1..n), so the answer always counts down the listed options.
2b's no-choice problems put "Not buy ..." first, so code 1 there is walking away (the .sav
labels, the authors' R code and their Table 4 comments agree: no-choice 20.6% of the
two-option rows).

THE ASSIGNMENT. No column records it: each group's answers sit in its own columns, blank
for everyone else, every built question being forced-response (asserted). Each person's
filled choice columns are exactly one group's (asserted), which is how the authors' R
code codes condition (NonForced_dummy, Three_dummy, Range, TwoStage). Jev
(scripts/recipe_prep.py --only assignment --source dataverse, run on each .sav, 19 Nov
2026) answered NONE_OF_THESE for the assignment column on all eight (confidence
0.88-0.97), which agrees. Persons are ids from their row in the file ("study2b_17"), the
only key the main files have (the timestamped ResponseId is not used).

PERSONA. Age (years, text entry; all 18-86) and gender, labels from the .qsf's own
choices (Female, Male, Non-Binary, Other). The country of the samples is not stated
anywhere in the box (1a: "the University's behavioral lab"; 1b asks for an MTurk ID, 3a,
4a, 4b and S1 a Prolific ID, 2a, 2b and 3b record Prolific fields), so none is claimed.

PICTURES, JAVASCRIPT, PIPED TEXT. None in any .qsf (asserted: no graphic id, no <img>, no
QuestionJS, no ${...} on any built question).

ANSWER KEY. The authors' R code, transcribed (tests/test_gen_researchbox2057.py) and run on
the deposit and on the BUILT rows: their pooled logit on the relative choice of the target
option (1a, 1b, 2a, 2b, S1) or on choosing no option (3a, 3b), with problem dummies, gives the
same coefficients from both to 1e-9; their per-problem logits likewise; and the Table 3-4
shares printed in Additional Files' R comments (2a, 2b) are reproduced from the built rows
(2a exactly to the printed decimal; 2b's are printed with "≈" and one is off its own rounding:
compromise, forced, option B printed 35.2, where deposit and rows give 284/808 = 35.15).
4a and 4b: the authors' deferral model needs the unbuilt second stage, so only its inputs
that the rows carry are checked: the single-stage deferral share per problem and the
two-stage first-choice shares (their CamTwoStAvgChosen etc.).

    uv run python scripts/gen_researchbox2057.py --prep   # (re)write the coded .csv files
    uv run python scripts/gen_researchbox2057.py          # write the recipes
    uv run python scripts/gen_researchbox2057.py --check  # exit 1 if any recipe differs
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
STUDY_ID = "researchbox2057"
RAW = REPO / "data" / "raw" / STUDY_ID
MATERIALS = RAW / "Materials"
DATA = RAW / "Data"
RECIPES = REPO / "recipes"
LICENCE = (
    'CC BY 4.0, stated on the box page https://researchbox.org/2057 ("All content posted to '
    'ResearchBox is under a CC By 4.0 License"); read from its Zenodo copy '
    "https://zenodo.org/records/21935325. Read 19 Nov 2026."
)
SOURCE = (
    '"A Reexamination of the Effect of Forced Choice", ResearchBox 2057 '
    "(https://researchbox.org/2057), anonymous author, no paper named in the box."
)
STUDIES = ("1a", "1b", "2a", "2b", "3a", "3b", "4a", "4b", "S1")
AGE_RANGE = (18, 100)

# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

_TYPO = {"\xa0": " ", "​": "", "’": "'", "‘": "'", "“": '"', "”": '"'}


def clean(raw: str) -> str:
    """HTML fragment to one line. Typography only; words untouched."""
    s = re.sub(r"<br\s*/?>", " ", raw or "")
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    for a, b in _TYPO.items():
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def to_text(raw: str) -> str:
    """HTML to paragraphs (blank-line separated). A table is one line per row, its
    non-empty cells joined by " | " (the researchbox755 layout)."""

    def row(m: re.Match[str]) -> str:
        cells = [clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", m.group(0), re.S)]
        return "\x01" + " | ".join(c for c in cells if c) + "\x02"

    raw = re.sub(r"<tr[^>]*>.*?</tr>", row, raw or "", flags=re.S)
    parts = re.split(r"<br\s*/?>|</?p[^>]*>|</?div[^>]*>|</?table[^>]*>|</?tbody>", raw)
    out: list[str] = []
    for p in parts:
        if "\x01" in p:
            rest = clean(re.sub("\x01.*?\x02", " ", p, flags=re.S))
            if rest:
                out.append(rest)
            rows = [r for r in re.findall("\x01(.*?)\x02", p, re.S) if r.strip()]
            if rows:
                out.append("\n".join(rows))
        elif c := clean(p):
            out.append(c)
    return "\n\n".join(out)


def opt_question(question: str, options: list[str]) -> str:
    listed = "; ".join(f'{i} means "{o}"' for i, o in enumerate(options, 1))
    return f"{question} {listed}."


# ---------------------------------------------------------------------------
# The questionnaire
# ---------------------------------------------------------------------------


def qsf_path(study: str) -> Path:
    return MATERIALS / f"Study {study} - Materials.qsf"


def load_qsf(study: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(qsf_path(study).read_text(encoding="utf-8"))
    return data


def graphics_in(text: str) -> tuple[int, set[str]]:
    """(number of <img> tags, Qualtrics graphic ids) anywhere in a .qsf's text."""
    return len(re.findall(r"<img", text, re.I)), set(re.findall(r"IM_[A-Za-z0-9]{8,}", text))


@dataclass
class Page:
    """One problem block as one group saw it: lead + table, then the choice question."""

    block: str  # the block's description, e.g. "Camera - Control - Forced"
    stem_qid: str
    choice_qid: str
    text: str  # the stem, rendered
    question: str  # the choice question's own words
    options: list[str]  # in on-screen order
    codes: list[int]  # the data code of each option, same order
    tag: str  # the choice question's export tag = its data column
    after: list[str] = field(default_factory=list)  # export tags on the block's later pages


class Survey:
    def __init__(self, study: str) -> None:
        self.study = study
        d = load_qsf(study)
        els = d["SurveyElements"]
        self.sq = {e["Payload"]["QuestionID"]: e["Payload"] for e in els if e["Element"] == "SQ"}
        bl = next(e for e in els if e["Element"] == "BL")["Payload"]
        self.blocks = {b["ID"]: b for b in (bl.values() if isinstance(bl, dict) else bl)}
        self.flow = next(e for e in els if e["Element"] == "FL")["Payload"]

    def groups(self) -> list[list[Page]]:
        """The between-person groups, each its problem pages in the .qsf's block order."""
        top = self.flow["Flow"]
        kinds = [n["Type"] for n in top]
        rands = [n for n in top if n["Type"] == "BlockRandomizer"]
        assert len(rands) == 1, (self.study, kinds)
        outer = rands[0]
        assert str(outer["SubSet"]) == "1" and outer["EvenPresentation"], self.study
        intro = [self.blocks[n["ID"]]["Description"] for n in top if n["Type"] == "Standard"]
        assert intro == ["Intro", "Demographics"], (self.study, intro)
        out = []
        for g in outer["Flow"]:
            assert g["Type"] == "BlockRandomizer", (self.study, g["Type"])
            kids = g["Flow"]
            assert all(k["Type"] == "Standard" for k in kids)
            # every block shown, in a random order
            assert int(g["SubSet"]) == len(kids) and g["EvenPresentation"], self.study
            out.append([self.page(k["ID"]) for k in kids])
        return out

    def page(self, block_id: str) -> Page:
        b = self.blocks[block_id]
        els = b["BlockElements"]
        breaks = [i for i, e in enumerate(els) if e["Type"] == "Page Break"]
        first = els[: breaks[0]] if breaks else els
        assert [e["Type"] for e in first] == ["Question", "Question"], (self.study, b)
        stem, choice = (self.sq[e["QuestionID"]] for e in first)
        assert stem["QuestionType"] == "DB" and choice["QuestionType"] == "MC", b["Description"]
        later = [self.sq[e["QuestionID"]] for e in els[len(first) :] if e["Type"] == "Question"]
        for q in (stem, choice):
            assert not q.get("QuestionJS") and not q.get("DisplayLogic"), q["QuestionID"]
            assert "${" not in json.dumps(q), q["QuestionID"]
        assert choice["Selector"] == "SAVR" and not choice.get("Randomization"), choice
        assert choice["Validation"]["Settings"]["ForceResponse"] == "ON", choice["QuestionID"]
        order = [str(k) for k in choice.get("ChoiceOrder") or sorted(choice["Choices"], key=int)]
        assert sorted(order, key=int) == sorted(choice["Choices"], key=int)
        recode = choice.get("RecodeValues") or {k: k for k in order}
        return Page(
            block=b["Description"],
            stem_qid=stem["QuestionID"],
            choice_qid=choice["QuestionID"],
            text=to_text(stem["QuestionText"]),
            question=" ".join(to_text(choice["QuestionText"]).split("\n\n")),
            options=[clean(choice["Choices"][k]["Display"]) for k in order],
            codes=[int(recode[k]) for k in order],
            tag=choice["DataExportTag"],
            after=[q["DataExportTag"] for q in later],
        )

    def gender_labels(self) -> dict[int, str]:
        (q,) = [p for p in self.sq.values() if p.get("DataExportTag") == "Gender"]
        recode = q.get("RecodeValues") or {k: k for k in q["Choices"]}
        return {int(recode[k]): clean(v["Display"]) for k, v in q["Choices"].items()}


def sav_labels(study: str) -> dict[str, dict[int, str]]:
    """The .sav's value labels (every study but 1a, whose .sav was withdrawn)."""
    import pyreadstat

    path = DATA / f"Study {study} - Data.sav"
    if not path.exists():
        return {}
    _, meta = pyreadstat.read_sav(str(path), metadataonly=True)
    return {
        v: {int(k): clean(str(t)) for k, t in labs.items()}
        for v, labs in meta.variable_value_labels.items()
    }


def data_codes(study: str, p: Page, labels: dict[str, dict[int, str]]) -> list[int]:
    """Each option's code in the data. The .sav's value labels are the authority where
    there is a .sav: each option's words must label exactly one code. Where the .qsf has
    RecodeValues they must agree. 3a's .qsf has none (its keys run 1, 2, 4) while its .sav
    and the authors' R code put the way out at 3: the .sav wins, and QSF_RECODE_MISSING
    records the one study where that happens."""
    if not labels:
        return p.codes  # 1a: the .qsf's RecodeValues, no .sav to read
    lab = labels[p.tag]
    codes = []
    for o in p.options:
        (c,) = [k for k, t in lab.items() if t == o]
        codes.append(c)
    assert sorted(lab) == sorted(codes), (study, p.tag, lab)
    if study in QSF_RECODE_MISSING:
        assert p.codes != codes, (study, p.tag)  # the .qsf's raw keys, not the data's
    else:
        assert p.codes == codes, (study, p.tag, p.codes, codes)
    return codes


QSF_RECODE_MISSING = ("3a",)


def check_pictures(study: str) -> None:
    n, ids = graphics_in(qsf_path(study).read_text(encoding="utf-8"))
    assert n == 0 and not ids, (study, n, ids)


# ---------------------------------------------------------------------------
# What each block's name means (the authors' own block descriptions)
# ---------------------------------------------------------------------------

PROBLEM = {  # block's first part -> problem key (the same problem in every group)
    "Camcorder": "camcorder",
    "Camera": "camera",
    "Laptop": "laptop",
    "Speaker": "speaker",
    "Speakers": "speaker",
    "Restaurant": "restaurant",
    "CD Player": "cd_player",
    "Barbecue": "barbecue",
    "Microwave": "microwave",
    "Cassette": "cassette",
    "Binoculars": "binoculars",
    "Apartment": "apartment",
    "Hard Drive": "hard_drive",
    "HD": "hard_drive",
    "Admission": "admission",
    "Wine": "wine",
}
CHOICE = {
    "Forced": "forced",
    "Nonforced": "no_choice_option",
    "Single-Stage": "single_stage",
    "Two-Stage": "two_stage_first_choice",
}
SET = {
    "Control": "two_options",
    "Compromise": "compromise",
    "Attraction": "attraction",
    "Dominance": "attraction",  # a dominated decoy (pre-registrations 2b and S1)
}
RANGE = {"No-range": "point_values", "No-Range": "point_values", "Range": "ranges"}
# An option that picks one of the table's rows; any other option is the way out.
PICK = re.compile(
    r"^(I would )?(buy|go to|rent|admit) "
    r"(Brand|Option|Restaurant|Apartment|Camera|Laptop|Wine|Applicant) [A-C]$",
    re.I,
)


def factors_of(study: str, p: Page) -> dict[str, str]:
    """Read the block description; check it against what the page shows."""
    parts = [s.strip() for s in p.block.split(" - ") if s.strip() not in ("Page 1",)]
    f: dict[str, str] = {"problem": PROBLEM[parts[0]]}
    for s in parts[1:]:
        if s in CHOICE:
            f["choice"] = CHOICE[s]
        elif s in SET:
            f["option_set"] = SET[s]
        elif s in RANGE:
            f["values"] = RANGE[s]
        else:
            raise KeyError((study, p.block, s))
    n_table = len(p.text.split("\n\n")[-1].split("\n")) - 1  # option rows under the header
    walk = [o for o in p.options if not PICK.match(o)]
    if study in ("3a", "3b"):
        f["choice"] = "no_choice_option"  # everyone had it
    # the page agrees with its name
    assert len(walk) == (0 if f["choice"] in ("forced", "two_stage_first_choice") else 1), (
        study,
        p.block,
        p.options,
    )
    assert len(p.options) == n_table + len(walk), (study, p.block)
    if "option_set" in f:
        assert n_table == (2 if f["option_set"] == "two_options" else 3), (study, p.block)
    if f["choice"] == "two_stage_first_choice":
        assert p.after and p.after[0].endswith("Two2"), (study, p.block, p.after)
    return f


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


def data_path(study: str) -> Path:
    return DATA / f"Study {study} - Data (csv).csv"


def read_data(study: str) -> pd.DataFrame:
    return pd.read_csv(data_path(study))


def timestamped(study: str) -> pd.DataFrame:
    """The same study from Other/Additional Files.zip (read in memory, never extracted)."""
    import io
    import zipfile

    with zipfile.ZipFile(RAW / "Other" / "Additional Files.zip") as z:
        return pd.read_csv(io.BytesIO(z.read(f"Study {study} - Data (csv).csv")))


def check_timestamped(study: str) -> None:
    a, d = timestamped(study), read_data(study)
    assert len(a) == len(d) and (a["Finished"] == 1).all(), study
    assert a[list(d.columns)].equals(d), study


def assign(study: str, df: pd.DataFrame, groups: list[list[Page]]) -> list[int]:
    """Each person's group: the one whose choice columns are exactly the filled ones."""
    tags = {p.tag for g in groups for p in g}
    assert tags <= set(df.columns), (study, tags - set(df.columns))
    want = [{p.tag for p in g} for g in groups]
    out = []
    for _, r in df.iterrows():
        filled = {t for t in tags if pd.notna(r[t])}
        (gi,) = [i for i, w in enumerate(want) if w == filled]
        out.append(gi)
    return out


# ---------------------------------------------------------------------------
# The experiments
# ---------------------------------------------------------------------------


@dataclass
class Arm:
    raw: int
    group: int
    page: Page
    factors: dict[str, str]


@dataclass
class Experiment:
    study: str
    name: str
    title: str
    notes: str
    problems: list[str]  # task order
    arms: list[Arm]
    text_factors: list[str]


TITLES = {
    "1a": "Camcorder, laptop, Bluetooth speaker, restaurant: an all-average or a mixed option, "
    "made to choose or free to look for other options (Study 1a, students)",
    "1b": "Camera, laptop, Bluetooth speaker, restaurant: an all-average or a mixed option, "
    "made to choose or free not to buy (Study 1b)",
    "2a": "Six products, two options or a third (a compromise or a decoy), made to choose or "
    "free to look for other options (Study 2a)",
    "2b": "Apartment, camera, speaker, hard drive: two options, a decoy or a compromise, made "
    "to choose or free to go elsewhere (Study 2b)",
    "3a": "Camera, laptop, applicant, wine, restaurant: quality as one expert value or as a "
    "range; choose one or look for other alternatives (Study 3a)",
    "3b": "Camera, laptop, applicant, wine, restaurant: two experts agreeing or giving a "
    "range; choose one or look for other alternatives (Study 3b)",
    "4a": "Camera, laptop, restaurant: an all-average or a mixed option, with a go-elsewhere "
    "option or made to choose first (Study 4a)",
    "4b": "Camera, speaker, hard drive: three options in a line, with a go-elsewhere option "
    "or made to choose first (Study 4b)",
    "S1": "Apartment, camera, speaker, hard drive: two options, a decoy or a compromise, made "
    "to choose or free not to buy (Study S1)",
}
DESIGN = {
    "1a": "Two groups between people: made to choose (A or B) or offered a no-choice option, "
    "four problems each.",
    "1b": "Two groups between people: made to choose (A or B) or offered a no-choice option, "
    "four problems each.",
    "2a": "2 x 2 between people: made to choose or offered a no-choice option; two options, or "
    "a third (a compromise option for camera, CD player and barbecue, a dominated decoy for "
    "microwave, cassette player and binoculars). Six problems each.",
    "2b": "2 x 3 between people: made to choose or offered a no-choice option (listed first, "
    "and named in the lead); two options, a dominated decoy, or a compromise. Four problems "
    "each.",
    "3a": "Two groups between people: one attribute given as a single value or as a range; "
    "everyone could look for other alternatives. Five problems each.",
    "3b": "Two groups between people: two experts' values the same or different; everyone "
    "could look for other alternatives. Five problems each.",
    "4a": "Two groups between people: single stage (A, B or go elsewhere) or two stage (A or "
    "B, then a second question not built). Three problems each.",
    "4b": "Two groups between people: single stage (A, B, C or go elsewhere) or two stage (A, "
    "B or C, then a second question not built). Three problems each.",
    "S1": "2 x 3 between people: made to choose or offered a no-choice option; two options, a "
    "dominated decoy, or a compromise. Four problems each.",
}
SAMPLE = {
    "1a": "students in a university behavioural lab (pre-registration)",
    "1b": "an online panel (the survey asks for an MTurk ID)",
    "2a": "Prolific (the survey records Prolific fields)",
    "2b": "Prolific (the survey records Prolific fields)",
    "3a": "an online panel (the survey asks for a Prolific ID)",
    "3b": "Prolific (the survey records Prolific fields)",
    "4a": "an online panel (the survey asks for a Prolific ID)",
    "4b": "an online panel (the survey asks for a Prolific ID)",
    "S1": "an online panel (the survey asks for a Prolific ID)",
}
PREREG = {
    "1a": "#147483",
    "1b": "#84536",
    "2a": "#168970",
    "2b": "#226927",
    "3a": "#85333",
    "3b": "#229731",
    "4a": "#85573",
    "4b": "#85699",
    "S1": "#84418",
}

# Outcomes fielded and not built, with the reason (see the docstring).
NOT_BUILT_OUTCOMES = {
    "4a": {
        "CamTwo2, LapTwo2, ResTwo2": "the two-stage second question asks about 'the one you "
        "chose', the person's own earlier answer, which a row cannot carry",
        "Q33, Q31, Q36, Q29, Q31.0, Q39": "filler problems, the same in both groups",
    },
    "4b": {
        "CamTwo2, SpeTwo2, HDTwo2": "the two-stage second question asks about 'the one you "
        "chose', the person's own earlier answer, which a row cannot carry",
        "Q33, Q31, Q36, Q29, Q31.0, Q39": "filler problems, the same in both groups",
    },
    "2b": {
        "*Confl_1-3": "three 1-7 ratings of the decision the person had just made (dilemma, "
        "tough choice, options similar); the person's own choice is not in the row",
    },
}
NOT_BUILT: tuple[str, ...] = ()  # every study builds; see NOT_BUILT_OUTCOMES


def name_of(study: str) -> str:
    return f"study{study.lower()}"


def choice_in_text(arms: list[Arm]) -> bool:
    """Does the page TEXT differ between choice groups, problem by problem (other factors
    held equal)? Only then is `choice` a condition factor QC rule 5 can test."""
    seen: dict[tuple[Any, ...], dict[str, str]] = {}
    for a in arms:
        key = tuple(sorted((k, v) for k, v in a.factors.items() if k != "choice"))
        seen.setdefault(key, {})[a.factors["choice"]] = a.page.text
    pairs = [v for v in seen.values() if len(v) > 1]
    differ = [len(set(v.values())) > 1 for v in pairs]
    assert pairs and (all(differ) or not any(differ)), "choice changes some pages only"
    return all(differ)


def experiment(study: str) -> Experiment:
    s = Survey(study)
    check_pictures(study)
    groups = s.groups()
    labels = sav_labels(study)
    for g in groups:
        for p in g:
            p.codes = data_codes(study, p, labels)
    arms: list[Arm] = []
    problems: list[str] = []
    for gi, g in enumerate(groups):
        for p in g:
            f = factors_of(study, p)
            if f["problem"] not in problems:
                problems.append(f["problem"])
            arms.append(Arm(raw=len(arms) + 1, group=gi, page=p, factors=f))
    # every group shows every problem once
    for gi in range(len(groups)):
        assert sorted(a.factors["problem"] for a in arms if a.group == gi) == sorted(problems)
    text_factors = ["problem"] + [
        k for k in ("option_set", "values") if any(k in a.factors for a in arms)
    ]
    if study not in ("3a", "3b") and choice_in_text(arms):
        text_factors.insert(1, "choice")
    n = len(read_data(study))
    notes = (
        f"{DESIGN[study]} Problem order random and not recorded, so each row carries its own "
        f"problem only. {n:,} people, all kept (AsPredicted {PREREG[study]}: 'I will not "
        f"exclude any data'); sample: {SAMPLE[study]}, country not stated."
    )
    if "choice" not in text_factors and study not in ("3a", "3b"):
        notes += (
            " The forced and no-choice pages of a problem show the same lead and table; the "
            "manipulation is in the answer options, so it is in each arm's outcome question "
            "(factor `choice`, carried on every arm, is not a condition factor here because "
            "the condition text does not express it; both arms of a problem declare the "
            "shared text)."
        )
    if study in NOT_BUILT_OUTCOMES:
        notes += " Not built: " + "; ".join(
            f"{k} ({v})" for k, v in NOT_BUILT_OUTCOMES[study].items()
        )
        notes += "."
    return Experiment(
        study=study,
        name=name_of(study),
        title=TITLES[study],
        notes=notes,
        problems=problems,
        arms=arms,
        text_factors=text_factors,
    )


def experiments() -> list[Experiment]:
    return [experiment(s) for s in STUDIES if name_of(s) not in NOT_BUILT]


# ---------------------------------------------------------------------------
# Coded data
# ---------------------------------------------------------------------------


def data_file(study: str) -> str:
    return f"{STUDY_ID}_{name_of(study)}.csv"


def prep(study: str) -> pd.DataFrame:
    """One coded row per person: each problem's arm, each choice column, age, gender."""
    check_timestamped(study)
    e = experiment(study)
    df = read_data(study)
    groups = sorted({a.group for a in e.arms})
    pages = [[a.page for a in e.arms if a.group == g] for g in groups]
    who = assign(study, df, pages)
    out = pd.DataFrame({"pid": [f"{e.name}_{i}" for i in range(len(df))]})
    for prob in e.problems:
        raw_of = {a.group: a.raw for a in e.arms if a.factors["problem"] == prob}
        out[f"cell_{prob}"] = [raw_of[g] for g in who]
    for a in e.arms:
        v = pd.to_numeric(df[a.page.tag], errors="raise")
        ok = v.dropna()
        assert (ok % 1 == 0).all() and set(ok.astype(int)) <= set(a.page.codes), a.page.tag
        out[a.page.tag] = v.astype("Int64")
    labels = Survey(study).gender_labels()
    age = pd.to_numeric(df["Age"], errors="coerce")
    out["age"] = age.where(age.between(*AGE_RANGE)).astype("Int64")
    assert df["Gender"].notna().all() and set(df["Gender"]) <= set(labels), study
    out["gender"] = df["Gender"].map(lambda g: labels[int(g)])
    return out


# ---------------------------------------------------------------------------
# The recipes
# ---------------------------------------------------------------------------


def recipe(e: Experiment) -> dict[str, Any]:
    task = {p: t for t, p in enumerate(e.problems)}
    # pages two arms of one problem share word for word (rule 1 wants both declared)
    by_text: dict[tuple[str, str], int] = {}
    for a in e.arms:
        k = (a.factors["problem"], a.page.text)
        by_text[k] = by_text.get(k, 0) + 1
    arms = []
    for i, a in enumerate(e.arms):
        n = len(a.page.options)
        arm: dict[str, Any] = {
            "raw": a.raw,
            "condition_num": i,
            "factors": a.factors,
            "text": a.page.text,
            "outcome_var": a.page.tag,
            "outcome_question": opt_question(a.page.question, a.page.options),
            "scale": {"min": 1, "max": n, "nominal": True},
            "response_recode": {c: j for j, c in enumerate(a.page.codes, 1)},
        }
        if by_text[(a.factors["problem"], a.page.text)] > 1:
            arm["items"] = {task[a.factors["problem"]]: {"condition_text": a.page.text}}
        arms.append(arm)
    widest = max(len(a.page.options) for a in e.arms)
    notes = (
        f"{SOURCE} Study {e.study}.\n\nGENERATED by scripts/gen_researchbox2057.py; every "
        f"judgement is in its docstring. {e.notes}\n\nWording from Study {e.study} - "
        "Materials.qsf (the blocks the survey flow reaches), word-for-word; no picture, script "
        'or piped text in it. Tables are one line per row, cells joined by " | ". Typography '
        "normalised. Added words (ours): the options' enumeration after each question, "
        '\'1 means "..."; 2 means "..."\'. Each answer is coded to its option\'s position '
        "on screen. Persona: age (years) and gender, labels from the .qsf's own choices."
    )
    return {
        "study_id": STUDY_ID,
        "source": "researchbox",
        "experiment": e.name,
        "title": e.title,
        "data_file": data_file(e.study),
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": "pid",
        "notes": notes,
        # source_var is the first problem's column; each outcome names its own
        "condition": {
            "source_var": f"cell_{e.problems[0]}",
            "factors": e.text_factors,
            "arms": arms,
        },
        "outcomes": [
            {
                "task_num": t,
                "question": "What would you do?",
                "scale": {"min": 1, "max": widest, "nominal": True},
                "condition_var": f"cell_{p}",
            }
            for t, p in enumerate(e.problems)
        ],
        "response_recode": {k: k for k in range(1, widest + 1)},
        "missing_codes": [],
        "persona_map": {"age": "age", "gender": "gender"},
    }


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
        for e in experiments():
            path = RAW / data_file(e.study)
            prep(e.study).to_csv(path, index=False)
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
