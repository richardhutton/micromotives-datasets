#!/usr/bin/env python3
"""Write recipes/d4zua.yaml: an e-mailed job reference for Amy or Jason Morgan, who
worked standard hours or 50 to 60 hours a week, and performed in the top 1% to 60%.

TESS 076 (Christin L. Munsch, University of Connecticut, and Lindsey T. O'Connor, CSU
Channel Islands), "Gender and the Disparate Payoffs of Overwork" (TESS S68). NORC
AmeriSpeak, web only (SURV_MODE 2 for all), English only (SURV_LANG 1), general
population 18+, fielded 16 February to 2 March 2021 (the questionnaire's cover; the
.sav's STARTDT). N = 2,116, one row per CaseId (unique).

THE DEPOSIT

OSF d4zua, one zip MunschS68.zip, unpacked in data/raw/d4zua/: the data
(TESS076_Munsch_client.sav, read here; the same data as TESS076_Munsch_STATA.dta, which
the answer-key test reads instead), the codebook (.xlsx), the proposal ("S68
description.docx", "PR"), the IRB letter, NORC's project report, and ONE questionnaire
for FOUR TESS studies fielded together (Jardina 067, Schaad 072, Munsch 076, Saha 077),
in a final copy (..._vFINAL.docx, "Q") and a programming copy (..._v6clean.docx, "PG").
Only Q's "MUNSCH 076 experiment's BLOCK" is read; the data file holds only Munsch's
variables plus the profile. The other three studies are not part of this source. No
picture is shown on any Munsch screen: this is a text study.

THE DESIGN

2 x 2 x 8 between subjects, 32 cells (PR: "a 2 x 2 x 8 ... 32 different possible
conditions"), held in three preloads, each with its own value labels in the .sav and the
codebook:
  P_MUNSCHEXP1 hours: 1 "40 hours/week salaried worker" (1,089), 2 "50+ hours/week
    salaried overworker" (1,027);
  P_MUNSCHEXP2 gender: 1 "woman applicant" (1,044), 2 "man applicant" (1,072);
  P_MUNSCHEXP3 performance: 1-8 = "1%", "5%", "10%", "20%", "30%", "40%", "50%", "60%"
    (244-298 each).
Every cell is filled (52-81 people). condition_num is the template's odometer, hours
slowest and performance fastest: (hours-1)*16 + (gender-1)*8 + (performance-1). Q's
[SHOW] directives name these three variables and these codes; the direction of each is
fixed by the value labels, by PR's operationalisation table, and by the words the
directives show (Amy/Ms./her for EXP2 = 1; "standard business hours" for EXP1 = 1). The
P_MUNSCHEXP3 fill prints the value label itself ("top [P_MUNSCHEXP3] of employees").

recipe_prep (Jev, 23 Nov 2026, full run): assignment REVIEW, NONE_OF_THESE 0.37 against
P_MUNSCHEXP1 0.42. The question is single-answer and cannot return a design held in three
variables; the three preloads are declared from Q and the labels. Section 4 found no
instrument (the .docx is not in its converted folder); every directive in the Munsch
block is instead parsed by `resolve` below, which stops on any clause it does not
understand, so none can gate text unread.

CONDITION

Two screens, both word-for-word. MUNSCH_DISPLAY1, the cover story, which every cell
shares ("Professional reference inquires (or "reference checks") ... answer the
questions that follow."; "inquires" is the source's own word), then MUNSCH_DISPLAY2, the
e-mail exchange, which PG says was displayed to "look like a screenshot of an email
exchange. Use same font types and sizes, indentations, and symbols". So its lines are
kept as Q lays them out: the reply, signed "Taylor", then the header "On Wed, Nov 25,
2020 at 10:33 AM Turner, Adam <aj.turner@diversified.com> wrote:", then A.J. Turner's
quoted inquiry with its ">" marks, including the hard break after "a professional".
Blank lines are collapsed to one and spaces within a line to one; nothing else is
changed. The two screens are joined by a blank line, no words added. "Dear Mr. Welch"
answered by "Taylor" is the source's own inconsistency, kept.

The template's fixed words are Q's; the placeholders carry the directives:
{gender} = "Amy"/"Jason" (once, in the inquiry), {gender.title} = "Ms."/"Mr.",
{gender.possessive} = "her"/"his", {gender.subject} = "she"/"he"; the hours run of six
directives becomes "{hours.conj} {gender.title} {hours}", where conj is "and"/"although"
and {hours} is the directive's own sentence, "Morgan worked standard business hours
(M-F, 9am-5pm)." or "Morgan often came in early and stayed late, putting in 50 or 60
hours/week."; {performance} is the label ("1%" .. "60%"). This generator checks all 32
rendered cells, condition and four questions, against an independent evaluation of every
[SHOW ... IF ...] clause in Q, and checks that PG shows the same words in every cell (PG
differs from Q only in bracketed programming notes). Every factor changes the text in
every minimal pair.

OUTCOMES. Q1-Q4, each on its own horizontal 1-7 grid, asked of everyone after the
e-mail: commitment ("how committed do you think Ms. Morgan is to her work?"),
competence, likeability, reliability. Wording per cell from the same directives, so each
question names that cell's Ms./Mr. and her/his. Scale ends are the screen's own labels
without the leading "1- " / "7- ", checked against the .sav's ("1 - not at all
committed" .. "7 - extremely committed"). 98 "SKIPPED ON WEB" is the only non-answer that
occurs (16 / 14 / 11 / 15); 77 and 99 are declared too (recipe_prep: all non_answer,
conf >= 0.98). PG says Q1-Q4 were shown in a randomised order, recorded; the deposit holds
no order variable, and no row says where its question sat.

NOT BUILT: Q5_MUNSCH, the hiring decision, "Suppose you are the hiring manager ... what
salary (between $90,000 and $140,000/year) to offer", options "I would not hire" and
"I would hire ... and offer $90,000 .. $140,000 as a starting salary" in $5,000 steps.
DROPPED (US dollar salary): ruled by rich, 23 Nov 2026, because this source goes to the
UK dataset. Cost: 2,103 rows.

ROW ARITHMETIC: 2,116 x 4 = 8,464 cells, minus 56 skips = 8,408 rows; 2,114 people (two
skipped all four).

PERSONA

The AmeriSpeak set the siblings map (g2jcy, 9xw67, xk9ch): AGE, GENDER, EDUC5,
RACETHNICITY, INCOME, MARITAL, EMPLOY, REGION4, HHSIZE, HOME_TYPE, HOUSING, METRO,
INTERNET, PHONESERVICE, PartyID7, IDEO, and the preloads P_RELIG and P_ATTEND (this
deposit has no RELIG/ATTEND; xtvu5 maps the same preloads). recipe_prep: every field at
conf >= 0.88 except region, REVIEW between REGION4 (0.45) and REGION9 (0.41); REGION4
kept, as every AmeriSpeak recipe and the crosswalk (scripts/persona_amerispeak.py). Its
labels pass skipped HOME_TYPE, PHONESERVICE and HHSIZE (cap); read by hand, none has a
non-answer label. persona_missing: GENDER 0 "Unknown", PartyID7 and IDEO -1 "Unknown"
(2 and 11 occur), P_RELIG and P_ATTEND 77/98/99 (none occurs; their missing are blank,
57 and 50, and leave the field empty). recipe_prep called P_ATTEND's "SKIPPED ON WEB" a
close call (non_answer 0.37, answer 0.41); it names a skip and is declared missing.
P_RELIG code 1 is severed by SPSS at "...Reformed, Church" in this .sav and codebook, and
this deposit's questionnaire does not print the preload; restored from the same
AmeriSpeak preload printed in full in xtvu5's questionnaire (Q 233) and g2jcy's
(cross-deposit restoration, as zx5b8; ledger 111). Not mapped: AGE4/AGE7, INCOME4/9,
STATE, REGION9 (coarser or finer than the shared scheme), the HH* age counts, the weight,
the timings, SURV_MODE/SURV_LANG (constant).

No persona field sits in the outcomes' domain (judging a stranger's commitment and
competence from a reference). The condition names the applicant's gender, and the persona
carries the respondent's; the condition states nothing any persona group thinks or does,
so nothing follows by substitution (CONVENTIONS, "The condition must not name the
respondent's own persona category").

UK CHECK

A reference e-mail between two managers about a project manager at a fictional firm,
"Highland Strategies", asked by "Diversified Project Management". No American place, law,
institution or money remains once Q5 is dropped. Three American conventions remain, kept
word-for-word and reported rather than edited: the Gmail-style header "On Wed, Nov 25,
2020 at 10:33 AM" (month-first date, AM), "(M-F, 9am-5pm)" for office hours, and "40
hour/week" as the standard full-time week (a little above the usual British 37.5). The
sample is American.

ANSWER KEY

Not in SocSci210, and NORC's project report prints no study results (only fieldwork).
The proposal's pilot is a different sample. So the key is the deposit itself, read
independently: tests/test_gen_d4zua.py recomputes the count and mean of every (cell,
outcome) pair, 128 of them, from the STATA copy (.dta, which the build never reads), and
per-factor means, and requires the built rows to match exactly.
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from html import unescape
from itertools import product
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

STUDY = "d4zua"
RAW = REPO / "data" / "raw" / STUDY
DATA_FILE = "TESS076_Munsch_client.sav"
_STEM = "8041.067_072_076_077_TESS067 072 076 077"
FINAL = RAW / f"{_STEM}_vFINAL.docx"
CLEAN = RAW / f"{_STEM}_v6clean.docx"
RECIPE = REPO / "recipes" / f"{STUDY}.yaml"
LICENCE = (
    "None stated: the TESS deposit on OSF (d4zua, and its components pvfgn Proposal and "
    "j547w Data and Materials, checked via the OSF API 23 Nov 2026) has node_license null "
    "and no license relationship, and TESS has since suspended operations. No explicit "
    "grant of redistribution rights should be assumed."
)

ID_VAR = "CaseId"
HOURS, GENDER, PERF = "P_MUNSCHEXP1", "P_MUNSCHEXP2", "P_MUNSCHEXP3"
DESIGN_VARS = [HOURS, GENDER, PERF]

# The deposit's own value labels for the three preloads (.sav and codebook).
HOURS_LABELS = {1: "40 hours/week salaried worker", 2: "50+ hours/week salaried overworker"}
GENDER_LABELS = {1: "woman applicant", 2: "man applicant"}
PERF_LABELS = {i + 1: f"{p}%" for i, p in enumerate([1, 5, 10, 20, 30, 40, 50, 60])}

OUTCOME_VARS = ["Q1_MUNSCH", "Q2_MUNSCH", "Q3_MUNSCH", "Q4_MUNSCH"]
NOT_BUILT = "Q5_MUNSCH"

# P_RELIG code 1 is severed by SPSS at "...Reformed, Church" in this .sav and in this
# deposit's codebook, and this deposit's questionnaire does not print the preload. The
# same AmeriSpeak preload P_RELIG, same 14 codes in the same order and the same severed
# prefix, is printed in full in the fielded questionnaire of TESS xtvu5 (its Q 233,
# restored there the same way); g2jcy's questionnaire prints the identical wording.
PROTESTANT = (
    "Protestant (Baptist, Methodist, Non-denominational, Lutheran, Presbyterian, "
    "Pentecostal, Episcopalian, Reformed, Church of Christ, Jehovah's Witness, etc.)"
)

# ---------------------------------------------------------------------------
# The template. Every word outside the placeholders is checked, cell by cell, against
# an independent resolution of the questionnaire's [SHOW] directives (`resolved`).
# ---------------------------------------------------------------------------

DIMENSIONS: dict[str, dict[str, Any]] = {
    "hours": {
        "var": HOURS,
        "levels": {
            1: {
                "level": "standard_hours",
                "text": "Morgan worked standard business hours (M-F, 9am-5pm).",
                "parts": {"conj": "and"},
            },
            2: {
                "level": "overwork",
                "text": "Morgan often came in early and stayed late, putting in 50 or 60 "
                "hours/week.",
                "parts": {"conj": "although"},
            },
        },
    },
    "gender": {
        "var": GENDER,
        "levels": {
            1: {
                "level": "woman",
                "text": "Amy",
                "parts": {"title": "Ms.", "possessive": "her", "subject": "she"},
            },
            2: {
                "level": "man",
                "text": "Jason",
                "parts": {"title": "Mr.", "possessive": "his", "subject": "he"},
            },
        },
    },
    "performance": {
        "var": PERF,
        "levels": {
            code: {"level": f"top_{label[:-1]}pct", "text": label}
            for code, label in PERF_LABELS.items()
        },
    },
}

# [SHOW] directive (curly-quoted, as Word stores it) -> placeholder. The six-directive
# run that carries the hours manipulation is replaced whole (HOURS_RUN).
SINGLE = {
    "[SHOW “Ms.” IF P_MUNSCHEXP2=1; SHOW “Mr.” if P_MUNSCHEXP2=2]": "{gender.title}",
    "[SHOW “her” IF P_MUNSCHEXP2=1; SHOW “his” if P_MUNSCHEXP2=2]": "{gender.possessive}",
    "[SHOW “she” IF P_MUNSCHEXP2=1; SHOW “he” if P_MUNSCHEXP2=2]": "{gender.subject}",
    "[SHOW “Amy” IF P_MUNSCHEXP2=1; SHOW “Jason” if P_MUNSCHEXP2=2]": "{gender}",
    "[P_MUNSCHEXP3]": "{performance}",
}
HOURS_RUN = re.compile(r"\[SHOW “and” if P_MUNSCHEXP1=1\].*?hours/week\.” if P_MUNSCHEXP1=2\]")


# ---------------------------------------------------------------------------
# The questionnaire (.docx, read as Word stores it)
# ---------------------------------------------------------------------------


def paragraphs(path: Path) -> list[str]:
    """Body paragraphs in order, a <w:br/> read as a newline; entities unescaped,
    non-breaking spaces made plain. Curly quotes are left for the directive parser."""
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    out = []
    for p in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
        bits = re.findall(r"<w:t[^>]*>([^<]*)</w:t>|(<w:br[^>]*/>)", p)
        out.append(unescape("".join(t if t else "\n" for t, _ in bits)).replace("\xa0", " "))
    return out


def munsch_block(path: Path) -> list[str]:
    """MUNSCH 076's paragraphs, up to the next study's block. Blank ones kept: they are
    the spacing of the e-mail. The four block headers at the top of the file (the
    randomised block list) are passed over: the block starts at the SECOND header."""
    paras = paragraphs(path)
    starts = [i for i, p in enumerate(paras) if p.strip() == "MUNSCH 076 experiment’s BLOCK"]
    if len(starts) != 2:
        raise SystemExit(f"{path.name}: {len(starts)} MUNSCH block headers")
    start = starts[1]
    end = next(i for i in range(start, len(paras)) if paras[i].startswith("SAHA 077"))
    return paras[start + 1 : end]


def _typo(text: str) -> str:
    """Typography only (docs/CONVENTIONS.md): curly quotes and apostrophes."""
    return text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')


def _layout(lines: list[str]) -> str:
    """Join the e-mail's lines: spaces collapsed within a line, blank lines collapsed to
    one, nothing else changed."""
    out: list[str] = []
    for raw in "\n".join(lines).split("\n"):
        line = re.sub(r" +", " ", raw).strip()
        if line or (out and out[-1]):
            out.append(line)
    while out and not out[-1]:
        out.pop()
    return "\n".join(out)


def screens(path: Path) -> dict[str, Any]:
    """The two display screens and the five question stems, raw (directives in place)."""
    block = [p for p in munsch_block(path) if not re.fullmatch(r"\s*\[[A-Z ;_0-9’.,]+\]\s*", p)]
    # Programming notes the simple copy lacks ([DISPLAY], [SP], the box note, the
    # randomise-Q1-Q4 note, timestamps) are bracketed upper-case lines: dropped above.
    block = [p for p in block if not p.strip().startswith(("[The below box", "[RANDOMIZE"))]
    i1, i2 = block.index("MUNSCH_DISPLAY1."), block.index("MUNSCH_DISPLAY2.")
    q_at = {m.group(1): i for i, p in enumerate(block) if (m := re.fullmatch(r"(Q\d)_MUNSCH\.", p))}
    if sorted(q_at) != ["Q1", "Q2", "Q3", "Q4", "Q5"]:
        raise SystemExit(f"{path.name}: questions {sorted(q_at)}")
    intro = [p for p in block[i1 + 1 : i2] if p.strip()]
    if len(intro) != 1:
        raise SystemExit(f"{path.name}: the cover-story screen is not one paragraph")
    email = block[i2 + 1 : q_at["Q1"]]
    stems: dict[str, str] = {}
    options: dict[str, list[str]] = {}
    order = sorted(q_at, key=q_at.get)  # type: ignore[arg-type]
    for k, q in enumerate(order):
        stop = q_at[order[k + 1]] if k + 1 < len(order) else len(block)
        body = [p.strip() for p in block[q_at[q] + 1 : stop] if p.strip()]
        stems[q] = body[0]
        options[q] = [x for x in body[1:] if not x.startswith(("HORIZONTAL GRID", "[HORIZONTAL"))]
    return {"intro": intro[0], "email": email, "stems": stems, "options": options}


# --- an independent resolver of the [SHOW] directives ------------------------

DIRECTIVE = re.compile(r"\[(SHOW [^\[\]]*|P_MUNSCHEXP3)\]")
CLAUSE = re.compile(r"SHOW “([^”]*)” (?:IF|if) (.+)")
COND = re.compile(r"(P_MUNSCHEXP\d)=(\d)")


def resolve(text: str, cell: dict[str, int]) -> str:
    """The words this cell's screen showed: each directive's clauses evaluated against
    the cell's three codes (a clause with an unknown shape stops the build)."""

    def one(m: re.Match[str]) -> str:
        body = m.group(1)
        if body == "P_MUNSCHEXP3":
            return PERF_LABELS[cell[PERF]]
        shown = []
        for clause in body.split(";"):
            c = CLAUSE.fullmatch(clause.strip())
            if not c:
                raise SystemExit(f"directive clause not understood: {clause!r}")
            conds = c.group(2).split(" and ")
            parsed = [COND.fullmatch(x.strip()) for x in conds]
            if not all(parsed):
                raise SystemExit(f"condition not understood: {c.group(2)!r}")
            if all(cell[p.group(1)] == int(p.group(2)) for p in parsed if p):
                shown.append(c.group(1))
        if len(shown) > 1:
            raise SystemExit(f"two clauses of one directive fire: {body!r}")
        return shown[0] if shown else ""

    out = DIRECTIVE.sub(one, text)
    if "[" in out or "]" in out:
        raise SystemExit(f"unresolved directive: {out!r}")
    return out


def cells() -> list[dict[str, int]]:
    return [
        {HOURS: h, GENDER: g, PERF: p}
        for h, g, p in product(HOURS_LABELS, GENDER_LABELS, PERF_LABELS)
    ]


def resolved(s: dict[str, Any], cell: dict[str, int]) -> dict[str, Any]:
    """One cell's condition and four questions, by the resolver alone."""
    intro = _typo(re.sub(r"\s+", " ", s["intro"]).strip())
    email = _typo(_layout([resolve(p, cell) for p in s["email"]]))
    qs = [_typo(re.sub(r"\s+", " ", resolve(s["stems"][q], cell)).strip()) for q in Q4]
    return {"text": f"{intro}\n\n{email}", "questions": qs}


Q4 = ["Q1", "Q2", "Q3", "Q4"]


# --- the template, from the same paragraphs ----------------------------------


def templated(text: str) -> str:
    text = HOURS_RUN.sub("{hours.conj} {gender.title} {hours}", text)
    for directive, placeholder in SINGLE.items():
        text = text.replace(directive, placeholder)
    if DIRECTIVE.search(text):
        raise SystemExit(f"a directive has no placeholder: {DIRECTIVE.search(text)}")
    return text


def render_cell(template: str, cell: dict[str, int]) -> str:
    """Fill the template the way recipe.ConditionTemplate.render does."""
    levels = {n: d["levels"][cell[d["var"]]] for n, d in DIMENSIONS.items()}
    for name, lv in levels.items():
        for part, frag in lv.get("parts", {}).items():
            template = template.replace(f"{{{name}.{part}}}", frag)
    for name, lv in levels.items():
        template = template.replace(f"{{{name}}}", lv["text"])
    return template


def instrument() -> dict[str, Any]:
    """Template text and question templates, after asserting that (a) every one of the
    32 cells renders exactly what the resolver says its screen showed, and (b) the
    v6clean copy shows the same words in every cell."""
    s = screens(FINAL)
    intro = _typo(re.sub(r"\s+", " ", s["intro"]).strip())
    text = f"{intro}\n\n" + _typo(_layout([templated(p) for p in s["email"]]))
    questions = [_typo(re.sub(r"\s+", " ", templated(s["stems"][q])).strip()) for q in Q4]
    other = screens(CLEAN)
    for cell in cells():
        want = resolved(s, cell)
        if render_cell(text, cell) != want["text"]:
            raise SystemExit(f"template and resolver disagree on {cell}")
        if [render_cell(q, cell) for q in questions] != want["questions"]:
            raise SystemExit(f"question templates and resolver disagree on {cell}")
        if resolved(other, cell) != want:
            raise SystemExit(f"v6clean and vFINAL differ on {cell}")
    return {"text": text, "questions": questions, "options": s["options"], "stems": s["stems"]}


def _scale_end(option: str) -> tuple[int, str]:
    m = re.fullmatch(r"0(\d) (\d)- (.+)", option.strip())
    if not m or m.group(1) != m.group(2):
        raise SystemExit(f"scale end not understood: {option!r}")
    return int(m.group(2)), m.group(3).strip()


def recipe() -> dict[str, Any]:
    ins = instrument()
    ds = read_any(RAW / DATA_FILE)
    df, labels = ds.df, ds.value_labels

    if not df[ID_VAR].is_unique:
        raise SystemExit(f"{ID_VAR} is not unique")
    for var, want in ((HOURS, HOURS_LABELS), (GENDER, GENDER_LABELS), (PERF, PERF_LABELS)):
        if df[var].isna().any():
            raise SystemExit(f"{var} has blanks")
        if {int(k): v for k, v in labels[var].items()} != want:
            raise SystemExit(f"{var} value labels changed: {labels[var]}")
        if sorted(int(x) for x in df[var].unique()) != sorted(want):
            raise SystemExit(f"{var} codes changed")
    # Each level's words say what its value label says.
    lv = DIMENSIONS["hours"]["levels"]
    if "standard business hours" not in lv[1]["text"] or "50 or 60" not in lv[2]["text"]:
        raise SystemExit("hours levels do not say what their labels say")

    scales = []
    for q, var in zip(Q4, OUTCOME_VARS, strict=True):
        opts = ins["options"][q]
        if len(opts) != 7:
            raise SystemExit(f"{q}: {len(opts)} options")
        lo, hi = _scale_end(opts[0]), _scale_end(opts[-1])
        if (lo[0], hi[0]) != (1, 7):
            raise SystemExit(f"{q}: scale runs {lo[0]}-{hi[0]}")
        got = {int(k): v for k, v in labels[var].items()}
        if got.get(1) != f"1 - {lo[1]}" or got.get(7) != f"7 - {hi[1]}":
            raise SystemExit(f"{var}: value labels {got} disagree with the questionnaire")
        if {77, 98, 99} - set(got):
            raise SystemExit(f"{var}: non-answer codes changed")
        scales.append({"min": 1, "max": 7, "min_label": lo[1], "max_label": hi[1]})

    if "$90,000" not in ins["stems"]["Q5"] or NOT_BUILT not in df.columns:
        raise SystemExit("Q5 is not the salary question this recipe says it drops")

    generic = [
        q.replace("{gender.title}", "Ms./Mr.").replace("{gender.possessive}", "her/his")
        for q in ins["questions"]
    ]
    outcomes = [
        {"var": var, "task_num": t, "question": generic[t], "scale": scales[t]}
        for t, var in enumerate(OUTCOME_VARS)
    ]

    return {
        "study_id": STUDY,
        "source": "tess",
        "title": "Gender and the Disparate Payoffs of Overwork",
        "data_file": DATA_FILE,
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": ID_VAR,
        "notes": (__doc__ or "").strip(),
        "condition": {
            "considered_and_rejected": {
                f"ORDER{i}": "Position of this study's block among the four TESS studies "
                "fielded in one omnibus (Jardina 067, Schaad 072, Munsch 076, Saha 077). "
                "Not part of this experiment's assignment: the other blocks are other "
                "studies, and a row cannot say what came before it."
                for i in range(1, 5)
            },
            "template": {
                "text": ins["text"],
                "outcome_questions": dict(enumerate(ins["questions"])),
                "dimensions": DIMENSIONS,
            },
        },
        "outcomes": outcomes,
        "response_recode": {i: i for i in range(1, 8)},
        "missing_codes": [77, 98, 99],
        "persona_map": {
            "age": "AGE",
            "gender": "GENDER",
            "education": "EDUC5",
            "ethnicity": "RACETHNICITY",
            "income": "INCOME",
            "marital_status": "MARITAL",
            "employment": "EMPLOY",
            "region": "REGION4",
            "household_size": "HHSIZE",
            "housing_type": "HOME_TYPE",
            "housing_ownership": "HOUSING",
            "urban_rural": "METRO",
            "internet_access": "INTERNET",
            "phone_service": "PHONESERVICE",
            "party_id": "PartyID7",
            "ideology": "IDEO",
            "religion": "P_RELIG",
            "religious_attendance": "P_ATTEND",
        },
        "persona_label_rewrite": {"P_RELIG": {1: PROTESTANT}},
        "persona_missing": {
            "GENDER": [0],
            "PartyID7": [-1],
            "IDEO": [-1],
            "P_RELIG": [77, 98, 99],
            "P_ATTEND": [77, 98, 99],
        },
    }


class _Dumper(yaml.SafeDumper):
    """Multi-line strings (the notes, the e-mail) as literal blocks, so the recipe reads
    the way the row will read."""


def _str(dumper: yaml.SafeDumper, value: str) -> yaml.ScalarNode:
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_Dumper.add_representer(str, _str)


def render() -> str:
    return yaml.dump(recipe(), Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    text = render()
    if args.check:
        same = RECIPE.exists() and RECIPE.read_text() == text
        print("recipe matches generator" if same else "recipe DIFFERS from generator")
        return 0 if same else 1
    RECIPE.write_text(text)
    print(f"wrote {RECIPE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
