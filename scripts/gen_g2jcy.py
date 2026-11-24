#!/usr/bin/env python3
"""Write recipes/g2jcy.yaml: Michael or Michelle, a clerk or a lawyer, asks to work from home.

TESS 142 (Marta Elliott and James M. Ragsdale, University of Nevada, Reno), "Public
Support for Remote Work Arrangements: An Experimental Study of the Effects of
Occupational Status, Mental Health Status, and Gender". NORC AmeriSpeak, web only,
general population 18+, fielded 16 January to 5 February 2024 (methods report). N =
1,668, one row per CaseId; NORC had already removed 57 cases for speeding, high refusal
or straight-lining both ELLIOTT_Q1 and ELLIOTT_Q2 (methods report, "Data Processing").

THE DEPOSIT

OSF g2jcy, component e5uqg "Data and Materials", one file ElliottM40.zip. The zip holds
ONE questionnaire for THREE TESS studies fielded together (Behrman 136, Eareckson 141,
Elliott 142), in a programming copy (..._vFINALprog.docx, "PG") and a simple copy
(..._vFINALsimple.docx, "Q"), plus Elliott's own data (TESS 142 Elliott_Final
Data.dta/.csv), codebook (.xlsx), the description document (M40-Elliott
description.docx, "PR") and NORC's methods report. Only "Block 3: TESS 142 Elliott" is
read here; the data file holds only Elliott's variables. Both .docx files embed two
images, word/media/image1.jpeg and image2.png, both on the cover page before any
question (the NORC and AmeriSpeak logos); no Elliott block is empty, every arm carries
its own words. This is a text study.

UK CHECK

A data entry clerk or a lawyer in a law firm asks their supervisor for a hybrid
schedule, two days in the office and three at home, because a quieter place helps them
work, and in half the arms says they have bipolar disorder. Respondents then judge the
motive, the likely effect on the work, and whether the request is reasonable and should
be approved. Law firms, clerks, lawyers, supervisors, salaries and hybrid working are
all ordinary in Britain, and no American law, institution, place or money appears in any
condition or outcome (the request is not framed as a legal accommodation). "Law office"
is American usage, kept word-for-word. The persona is the usual AmeriSpeak profile.

THE DESIGN

2 x 2 x 2 between subjects, one preload P_EXP_ELLIOTT (PG's preload table; in the .dta
as P_EXP_ELLIOTT, "PRELOAD: P_EXP_ELLIOTT"), codes 1-8 labelled in both PG and the .dta:
character (Michael 1-4, Michelle 5-8) x occupation (data entry clerk 1, 2, 5, 6; lawyer
3, 4, 7, 8) x disclosure (bipolar disorder on odd codes; nothing about mental health on
even codes). raw -> condition_num is raw - 1, no permutation. The direction is fixed
three ways that agree, and the generator asserts all three: the value labels ("Man,
Lower status, & Bipolar" ...), each [SHOW IF P_EXP_ELLIOTT=n] block's own words in PG
and Q, and the fills in every outcome ([IF P_EXP_ELLIOTT=1,2,3,4: Michael, IF
P_EXP_ELLIOTT=5,6,7,8: Michelle]). Every respondent has a code (197/214/213/201/235/224/
195/189). recipe_prep.py (Jev, 23 Nov 2026, full run) chose P_EXP_ELLIOTT at conf 0.96
after a run-off over 51 candidates (runner-up NONE_OF_THESE 0.02, RND_02 0.01).
Accepted; the questionnaire settles it on its own.

PR calls the higher-status job "an attorney"; every fielded vignette says "a lawyer". Q
and PG are used (docs/CONVENTIONS.md, Source authority). PR's template also omits the
fielded "Bipolar disorder" capital and reads "perform better at his job" for both
characters; neither reaches the rows.

CONDITION TEXT

Each arm is its ELLIOTT_VIGNETTE_n paragraph, word-for-word, from Q, after asserting PG
prints the same words. The paragraph opens with the character's name, so no prefix is
shared and there is no shared_context. Minimal pairs differ in text on every factor.

Two display screens before the vignette are left out. DISPLAY3 ("Now we'd like to get
your thoughts on a different topic.") was shown only when the block did not come first
and is a link between studies. DISPLAY_VIGNETTE ("You will see a paragraph in the next
screen. Please read it carefully before continuing because there will be follow-up
questions about it.") describes the instrument's screens, which the row does not
reproduce (CONVENTIONS, Sequence signposting). Neither says anything about the
character or the request. No words are added: every word of every condition is the
instrument's.

The three studies' blocks were shown in a random order (RND_02, values 0-5, "Used to
record order of Block1, Block2, Block3"; PG: "RANDOMIZE USING RND_02"). So some
respondents read this vignette after Behrman's block or Eareckson's (Eareckson's is
about male- and female-dominated occupations). No document maps RND_02's six codes to
orders, the other blocks are other studies with their own deposits, and a row cannot
say what came before it; RND_02 is declared in considered_and_rejected.

OUTCOMES: 10, ALL ASKED OF EVERY RESPONDENT AFTER THE VIGNETTE

  task 0-3  ELLIOTT_Q1A-D  attributions grid, 1 Strongly disagree .. 6 Strongly agree
  task 4-7  ELLIOTT_Q2A-D  competency grid, 1 Very unlikely .. 6 Very likely
  task 8    ELLIOTT_Q3     how reasonable, 1 Very unreasonable .. 6 Very reasonable
  task 9    ELLIOTT_Q4     should the supervisor approve, 1 Definitely yes .. 6
                           Definitely not (the scale runs from yes to no, as fielded;
                           codes are kept, and the instruction names both ends)

Every outcome names the character, so each arm carries its own wording of all ten
(Arm.items), with the fills resolved the way that arm's screen resolved them: Michael's,
his, he for codes 1-4 and Michelle's, her, she for 5-8. Outcome.question holds the
Michael wording only because the field is required; no row reads it, because every arm
overrides every task. Grid outcomes are the stem, a space, then the item, word-for-word.
The competency stem ends "it is that…" and each of its items begins "…Michael", the
screen's way of showing that the item completes the stem; once joined into one sentence
the item's leading ellipsis is dropped (typography: the stem's is kept, normalised to
"..."). The grid items are labelled to their columns by the codebook, which prints each
item in brackets before the stem; the generator asserts each matches Q's item. No
randomisation of grid items or of options is programmed ([GRID; SP], no RND_xx), and no
row cites a position.

The data's value labels equal Q's options for every outcome (asserted). Only 98
"SKIPPED ON WEB" occurs among the non-answers (77 and 99 are labelled, never used);
recipe_prep called DON'T KNOW / SKIPPED ON WEB / REFUSED non-answers on all ten at conf
>= 0.98 and agreed with the regex. missing_codes [77, 98, 99]; no outcome's range reaches
them.

ROW ARITHMETIC: 1,668 x 10 = 16,680 cells minus 131 skips (Q1A-D 11+12+16+11, Q2A-D
12+20+17+19, Q3 4, Q4 9) = 16,549 rows.

PERSONA

The AmeriSpeak set, mapped as the sibling deposits fielded in the same AmeriSpeak format
(yjvpn, 8ctbk, s6urt): AGE, GENDER, EDUC5, RACETHNICITY, INCOME, MARITAL, EMPLOY,
REGION4, HHSIZE, HOME_TYPE, HOUSING, METRO, INTERNET, PHONESERVICE, PartyID7, RELIG,
ATTEND. This file has no IDEO; ideology is IDEO20, "DATA-ONLY: Computed 5-level political
ideology", as in b87sm. recipe_prep: every field at conf >= 0.89 except region, a REVIEW
between REGION4 (0.36) and REGION9 (0.48); REGION4 is used, as in every other AmeriSpeak
recipe and the crosswalk built for it (ledger 149). Columns past recipe_prep's labels cap
(METRO, INTERNET, HOUSING, HOME_TYPE, PHONESERVICE, HHSIZE) were read by hand: plain
answers, no non-answer codes.

persona_missing: PartyID7 and IDEO20 -1 "Unknown" (2 and 26 respondents; Jev non_answer
0.94, 0.98); RELIG and ATTEND 77/98/99 (98 occurs 2 and 1 times). recipe_prep flagged
ATTEND's "SKIPPED ON WEB" as REVIEW (answer 0.37 against non_answer 0.40, disagreeing
with the regex). OVERRULED: it is the panel's web-skip code, the same label Jev called a
non-answer at conf 1.00 on RELIG and on every outcome. GENDER 0 "Unknown" (Jev 0.83,
0 occurrences, declared as in the siblings). RELIG code 1 is cut at 80 characters in the
.dta ("... Presbyterian, Pent"); restored from Q's own demographic profile, apostrophe
straightened.

Not mapped: Q2 (own mental or emotional health), Q3NEW_8 (ever told of an emotional,
nervous or psychiatric problem) and Q52 (seen a mental health professional in the past
12 months). PR asked for them as moderators; the persona schema has no field for them.
They are recorded here as the study's own moderators that the rows do not carry.
recipe_prep section 4's REVIEW items (BLOCK n DOES NOT APPEAR FIRST; P_HL002,
P_HL003NEWH, P_HL052 = missing) were read by eye: block-transition routing and profile
re-asks, none gating stimulus text.

VERIFICATION

Not in SocSci210 (comparable_to_socsci210: false), and no paper with this study's
numbers is in the deposit. tests/test_gen_g2jcy.py holds the answer keys: the built
rows reproduce every (arm, outcome) count and mean computed independently from the
deposit's CSV export (not the .dta the build reads), and the persona of the 1,668
people reproduces the unweighted percentages in NORC's methods report (Benchmark
Comparisons: age bands, race and ethnicity, education, sex) to the 0.1 printed.
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from html import unescape
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

STUDY = "g2jcy"
RAW = REPO / "data" / "raw" / STUDY
DATA_FILE = "TESS 142 Elliott_Final Data.dta"
CSV_FILE = "TESS 142 Elliott_Final Data.csv"
_STEM = "TESS 136 Behrman 141 Eareckson 142 Elliott"
SIMPLE = RAW / f"{_STEM}_vFINALsimple.docx"
PROG = RAW / f"{_STEM}_vFINALprog.docx"
CODEBOOK = RAW / "TESS 142 Elliott_Codebook.xlsx"
RECIPE = REPO / "recipes" / f"{STUDY}.yaml"
LICENCE = (
    "None stated: the TESS deposit on OSF (g2jcy, and its components 9d37u Proposal and "
    "e5uqg Data and Materials, checked via the OSF API 23 Nov 2026) has node_license null, "
    "and TESS has since suspended operations. No explicit grant of redistribution rights "
    "should be assumed."
)

ID_VAR = "CaseId"
COND_VAR = "P_EXP_ELLIOTT"

# code -> (character, occupation, disclosure), as the value labels name them.
P_EXP_LABELS = {
    1: "Man, Lower status, & Bipolar",
    2: "Man, Lower status, & No mental health",
    3: "Man, Higher status, & Bipolar",
    4: "Man, Higher status, & No mental health",
    5: "Woman, Lower status, & Bipolar",
    6: "Woman, Lower status, & No mental health",
    7: "Woman, Higher status, & Bipolar",
    8: "Woman, Higher status, & No mental health",
}
CODES = list(P_EXP_LABELS)


def factors_of(code: int) -> dict[str, str]:
    label = P_EXP_LABELS[code]
    return {
        "character": "michael" if label.startswith("Man") else "michelle",
        "occupation": "data_entry_clerk" if "Lower status" in label else "lawyer",
        "disclosure": "bipolar" if label.endswith("Bipolar") else "none",
    }


OUTCOME_VARS = [
    *(f"ELLIOTT_Q1{c}" for c in "ABCD"),
    *(f"ELLIOTT_Q2{c}" for c in "ABCD"),
    "ELLIOTT_Q3",
    "ELLIOTT_Q4",
]


# ---------------------------------------------------------------------------
# The questionnaire (.docx, read as Word stores it)
# ---------------------------------------------------------------------------


def _clean(text: str) -> str:
    """Typography only: curly quotes, the ellipsis character, non-breaking spaces."""
    text = unescape(text)
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("…", "...").replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def paragraphs(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    return [
        _clean("".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p)))
        for p in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S)
    ]


def elliott_block(path: Path) -> list[str]:
    """Block 3's paragraphs, blanks kept (they end option lists)."""
    paras = paragraphs(path)
    start = paras.index("Block 3: TESS 142 Elliott")
    end = next(
        i
        for i in range(start, len(paras))
        if paras[i].startswith(("Block 4", "Demographic Profile"))  # PG, Q
    )
    return paras[start + 1 : end]


PG_FILL = re.compile(r"\[IF P_EXP_ELLIOTT=1,2,3,4: ([^,\]]+), IF P_EXP_ELLIOTT=5,6,7,8: ([^\]]+)\]")
Q_FILL = re.compile(r"\[([^\[\]/]+) / ([^\[\]/]+)\]")


def resolve(text: str, code: int, fill: re.Pattern[str]) -> str:
    """The words the screen showed for this code: first option for 1-4, second for 5-8."""
    out = fill.sub(lambda m: m.group(1 if code <= 4 else 2).strip(), text)
    if "[" in out or "]" in out:
        raise SystemExit(f"unresolved fill: {out!r}")
    return out


def instrument(path: Path) -> dict[str, Any]:
    """Vignettes, stems, grid items (templates, fills unresolved) and options."""
    lines = elliott_block(path)
    vignettes: dict[int, str] = {}
    questions: dict[str, dict[str, Any]] = {}
    i = 0
    while i < len(lines):
        s = lines[i]
        m = re.fullmatch(r"ELLIOTT_VIGNETTE_(\d)\.", s)
        if m:
            show = lines[i - 1] if lines[i - 1] != "[DISPLAY]" else lines[i - 2]
            if show.lstrip("#") != f"[SHOW IF P_EXP_ELLIOTT={m.group(1)}]":
                raise SystemExit(f"{path.name}: vignette {m.group(1)} under {show!r}")
            vignettes[int(m.group(1))] = lines[i + 1]
            i += 2
            continue
        m = re.fullmatch(r"(ELLIOTT_Q\d)\.", s)
        if m:
            q: dict[str, Any] = {"stem": lines[i + 1], "items": [], "options": []}
            j = i + 2
            mode = None
            while j < len(lines) and not re.fullmatch(r"(ELLIOTT_Q\d)\.", lines[j]):
                t = lines[j]
                if t == "GRID ITEMS:":
                    mode = "items"
                elif t == "RESPONSE OPTIONS:":
                    mode = "options"
                elif t and mode:
                    q[mode].append(t)
                elif not t and mode == "options" and q["options"]:
                    break
                j += 1
            questions[m.group(1)] = q
            i = j
            continue
        i += 1
    if sorted(vignettes) != CODES:
        raise SystemExit(f"{path.name}: vignettes {sorted(vignettes)}")
    return {"vignettes": vignettes, "questions": questions}


def _texts(path: Path, fill: re.Pattern[str]) -> dict[str, Any]:
    """Per code: vignette and the ten outcome wordings, fills resolved."""
    ins = instrument(path)
    qs = ins["questions"]
    out: dict[str, Any] = {"vignettes": ins["vignettes"], "options": {}, "questions": {}}
    for code in CODES:
        words: list[str] = []
        for q in ("ELLIOTT_Q1", "ELLIOTT_Q2"):
            stem = resolve(qs[q]["stem"], code, fill)
            if len(qs[q]["items"]) != 4:
                raise SystemExit(f"{path.name} {q}: {len(qs[q]['items'])} items")
            for item in qs[q]["items"]:
                item = resolve(item, code, fill)
                if q == "ELLIOTT_Q2":
                    if not (stem.endswith("that...") and item.startswith("...")):
                        raise SystemExit(f"{path.name} {q}: continuation marks moved")
                    item = item.removeprefix("...")
                words.append(f"{stem} {item}")
        words += [resolve(qs[q]["stem"], code, fill) for q in ("ELLIOTT_Q3", "ELLIOTT_Q4")]
        out["questions"][code] = words
    for q in ("ELLIOTT_Q1", "ELLIOTT_Q2", "ELLIOTT_Q3", "ELLIOTT_Q4"):
        out["options"][q] = qs[q]["options"]
    out["templates"] = {q: qs[q] for q in ("ELLIOTT_Q1", "ELLIOTT_Q2")}
    return out


def fielded() -> dict[str, Any]:
    """Q, after asserting PG shows the same words for every code (CONVENTIONS, Source
    authority, ledger 52)."""
    q, pg = _texts(SIMPLE, Q_FILL), _texts(PROG, PG_FILL)
    for key in ("vignettes", "questions", "options"):
        if q[key] != pg[key]:
            raise SystemExit(f"PG and Q differ on {key}")
    return q


def protestant_label() -> str:
    """RELIG code 1 in full, from Q's demographic profile."""
    (line,) = [x for x in paragraphs(SIMPLE) if x.startswith("1 = Protestant (")]
    return line.split("=", 1)[1].strip()


def codebook_items() -> dict[str, str]:
    """Codebook: grid variable -> the bracketed item it prints before the stem."""
    import openpyxl

    wb = openpyxl.load_workbook(CODEBOOK, read_only=True)
    out: dict[str, str] = {}
    for row in wb.worksheets[0].iter_rows(values_only=True):
        if row and isinstance(row[0], str) and row[0] in OUTCOME_VARS[:8] and row[1]:
            m = re.match(r"\[(.*)\] (?:To what|If )", _clean(str(row[1])))
            if m:
                out.setdefault(row[0], m.group(1))
    return out


def _scale(options: list[str]) -> dict[str, Any]:
    return {"min": 1, "max": len(options), "min_label": options[0], "max_label": options[-1]}


def recipe() -> dict[str, Any]:
    q = fielded()
    ds = read_any(RAW / DATA_FILE)
    labels = ds.value_labels

    if sorted(int(c) for c in ds.df[COND_VAR].dropna().unique()) != CODES:
        raise SystemExit(f"{COND_VAR} codes changed")
    if ds.df[COND_VAR].isna().any() or not ds.df[ID_VAR].is_unique:
        raise SystemExit(f"{COND_VAR} has blanks or {ID_VAR} is not unique")
    if {int(k): v for k, v in labels[COND_VAR].items()} != P_EXP_LABELS:
        raise SystemExit(f"{COND_VAR} value labels changed: {labels[COND_VAR]}")

    # Each vignette says what its label says.
    for code, text in q["vignettes"].items():
        f = factors_of(code)
        name = "Michael" if f["character"] == "michael" else "Michelle"
        job = "a data entry clerk" if f["occupation"] == "data_entry_clerk" else "a lawyer"
        if not text.startswith(f"{name} is {job} who works in-person in a law firm."):
            raise SystemExit(f"vignette {code} does not open as its label says")
        if ("disclosed that" in text and "Bipolar disorder" in text) != (
            f["disclosure"] == "bipolar"
        ):
            raise SystemExit(f"vignette {code}: disclosure disagrees with its label")

    # The codebook labels each grid column with its item; it must be Q's item.
    items = codebook_items()
    templates = [
        *q["templates"]["ELLIOTT_Q1"]["items"],
        *q["templates"]["ELLIOTT_Q2"]["items"],
    ]
    for var, template in zip(OUTCOME_VARS[:8], templates, strict=True):
        want = template.replace(" / ", "/").removeprefix("...").rstrip(".?").strip()
        if items.get(var) != want:
            raise SystemExit(f"{var}: codebook item {items.get(var)!r} is not Q's {want!r}")

    option_lists = [q["options"]["ELLIOTT_Q1"]] * 4 + [q["options"]["ELLIOTT_Q2"]] * 4
    option_lists += [q["options"]["ELLIOTT_Q3"], q["options"]["ELLIOTT_Q4"]]
    for var, options in zip(OUTCOME_VARS, option_lists, strict=True):
        if len(options) != 6:
            raise SystemExit(f"{var}: {len(options)} options")
        got = [_clean(labels[var][k]) for k in range(1, 7)]
        if got != options:
            raise SystemExit(f"{var}: value labels {got} differ from Q's {options}")
        if {77, 98, 99} - {int(k) for k in labels[var]}:
            raise SystemExit(f"{var}: non-answer codes changed")

    outcomes = [
        {
            "var": var,
            "task_num": t,
            "question": q["questions"][1][t],
            "scale": _scale(options),
        }
        for t, (var, options) in enumerate(zip(OUTCOME_VARS, option_lists, strict=True))
    ]
    arms = [
        {
            "raw": code,
            "condition_num": code - 1,
            "factors": factors_of(code),
            "text": q["vignettes"][code],
            "items": {t: {"outcome_question": text} for t, text in enumerate(q["questions"][code])},
        }
        for code in CODES
    ]

    return {
        "study_id": STUDY,
        "source": "tess",
        "title": "Public Support for Remote Work Arrangements: An Experimental Study of the "
        "Effects of Occupational Status, Mental Health Status, and Gender",
        "data_file": DATA_FILE,
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": ID_VAR,
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_var": COND_VAR,
            "factors": ["character", "occupation", "disclosure"],
            "arms": arms,
            "considered_and_rejected": {
                "RND_02": "Order of the three studies' blocks in this omnibus (Behrman 136, "
                "Eareckson 141, this one). Not part of this experiment's assignment: no "
                "document maps its six codes to orders, the other blocks are other studies, "
                "and a row cannot say what came before it.",
            },
        },
        "outcomes": outcomes,
        "response_recode": {i: i for i in range(1, 7)},
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
            "ideology": "IDEO20",
            "religion": "RELIG",
            "religious_attendance": "ATTEND",
        },
        "persona_label_rewrite": {"RELIG": {1: protestant_label()}},
        "persona_missing": {
            "PartyID7": [-1],
            "IDEO20": [-1],
            "RELIG": [77, 98, 99],
            "ATTEND": [77, 98, 99],
            "GENDER": [0],
        },
    }


def render() -> str:
    return yaml.safe_dump(recipe(), sort_keys=False, allow_unicode=True, width=100)


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
