#!/usr/bin/env python3
"""Write recipes/ysqex.yaml: feelings about political candidates who are atheist,
not sure there is a God, or do not identify with a religion.

TESS 146 (Ewa Golebiowska), "Membership in a stigmatized religious minority and political
support". NORC AmeriSpeak, web (CAWI), general population 18+, fielded 29 March to 18
April 2024; "In total, NORC collected 1,274 final interviews", after NORC removed 18
cases (1 speeder, 13 high refusal, 4 not answering all conjoint items) (Project Methods
and Transparency Report). The .sav has exactly 1,274 rows, one per CaseId (unique).

THE DEPOSIT

OSF ysqex, Golebiowska1700.zip, extracted beside it byte-for-byte: the fielded
questionnaire in a programming copy ("9089.146 TESS 146 Golebiowska_vFINALprog.docx",
"PG") and a simple copy ("..._vFINALsimple.docx", "Q"), the data (.sav and .dta), the
codebook and NORC's frequency tables (.xlsx), the methods report, the proposal
("Golebiowska-1700.R1 description.docx", "PR") and the IRB form. The build reads the
.sav; the answer key (tests/test_gen_ysqex.py) reads the .dta and NORC's frequency
tables, which the build never reads.

SCOPE: Q1-Q6 ONLY (ruled by rich, 23 Nov 2026, for the UK dataset)

The instrument has two parts. A split-ballot block, Q1-Q8, fielded on AmeriSpeak, and
then a Sawtooth-hosted candidate conjoint, Q9-Q16 (PG "BEGINNING OF CONJOINT PROGRAMMED
BY SAWTOOTH"). Only the split-ballot outcomes are built.

NOT BUILT, the conjoint (Q9-Q16, 8 choices per respondent, at most 10,192 rows): every
profile carries "Party affiliation" Democrat / Republican and US race/ethnicity levels,
and four of the eight choices are "to be United States President", the other four "the
mayor of your town or city". A US two-party label is an attribute a UK respondent has no
equivalent for, so the conjoint is dropped as needing US politics, per the ruling. Its
religious-identity attribute is the same three groups as the split ballot plus "Attends
religious services weekly" and "Christian".

NOT BUILT, Q7 and Q8 (1,274 + 4 x 1,274 cells), and NOT persona either. Q7 ("On a
different subject, which of the following statements comes closest to expressing what you
believe about God?", six statements from "I don't believe in God." to "I know God really
exists and I have no doubts about it.") and Q8 (four statements on reason, science and
tradition, 1 Strongly agree .. 7 Strongly disagree) are about the RESPONDENT, not the
candidates: PG opens them "On a different subject" and "Switching gears once again", and
PR lists them as the respondent's own religiosity and rationalism. They are not outcomes
of the manipulation, which is the group named in the questions about candidates, so a row
pairing them with an arm would teach that the arm moved them. Nor are they mapped to the
persona: they were asked AFTER the manipulation (post-treatment, so not a clean
background attribute), the persona schema has no field for belief in God or rationalism,
and the respondent's religion is already carried by the AmeriSpeak profile variables
RELIG and ATTEND, which were collected before this survey (PG preloads P_RELIG,
P_ATTEND). Recorded here as the study's own moderators that the rows do not carry.

THE DESIGN

One factor, `target_group`, three arms, assigned by RND_01 (PG's table of RND_xx
variables: "RND_01 (randomly assign 1,2,3 only. Do not assign a value of 0)", associated
with "Q1, Q2, Q3, Q4, Q5, Q6"). Every one of Q1-Q6 names the group through the same fill:
  [IF RND_01=1:political candidates who are atheist,
   IF RND_01=2:political candidates who are not sure there is a God,
   IF RND_01=3:political candidates who do not currently identify with a religion]
RND_01 = 451 / 423 / 400, no blanks. raw -> condition_num is raw - 1.

RND_01's label in the data and the codebook is "RANDOMIZATION VARIABLE: Used to record
order of response options at Q1, Q2, Q3, Q4, Q5, Q6", which is wrong: no question in
the block randomises its options, and the only RND_01 directive anywhere in PG or Q is
the group fill above. That label is NORC's template text. recipe_prep.py (Jev, 23 Nov
2026) answered NONE_OF_THESE (conf 0.62, REVIEW) with MayorPresidentRandom_1 (the
conjoint block order) 0.29 behind it, misled by the same label. OVERRULED: the
questionnaire settles it. The data cannot tell arm 1 from arm 2 independently (their
thermometer means differ by under 1 point), so the direction rests on the fill, which
PG and Q print identically.

PR's split ballot is the same three groups, in capitals ("CANDIDATES WHO ARE ATHEISTS"
...) and with several wordings that were not fielded ("Now, I'd like to get your
feelings", "Thinking more about ..."); PG and Q are used (docs/CONVENTIONS.md, Source
authority).

CONDITION TEXT

The manipulation has no screen of its own: it is the group the questions name. So, as
a2nbf does for its baby/fetus wording, each arm's text is one sentence saying which
group the questions were about, with the group's words in double quotes, word-for-word
from the fill, and each outcome carries that arm's own question wording (Arm.items).
ADDED WORDS, stated per CONVENTIONS: "This set of survey questions was about" and the
closing full stop. They are true for every row: all eleven outcomes name the group.

  arm 0 (RND_01 = 1): This set of survey questions was about "political candidates who
                      are atheist".
  arm 1 (RND_01 = 2): ... "political candidates who are not sure there is a God".
  arm 2 (RND_01 = 3): ... "political candidates who do not currently identify with a
                      religion".

Not rendered: the welcome screen WINTRO_1 ("Thank you for agreeing to participate ...",
"This survey is about political concepts.", the incentive), which is survey mechanics.
No shared_context.

OUTCOMES: 11, ALL ASKED OF EVERY RESPONDENT, IN A FIXED ORDER

  task 0      Q1   feeling thermometer, slider 0-100 (PG "#[SLIDER [RANGE 0 TO 100]]")
  task 1-4    Q2A-D  four statements, 1 Strongly agree .. 7 Strongly disagree
  task 5-7    Q3A-C  Moral disgust, Anxiety, Anger, 0 Not at all .. 10 Very frequently
  task 8      Q4A  support for religion in the public sphere, 0-10
  task 9      Q5   liberal-conservative placement, 1 Extremely liberal .. 7 Extremely
                   conservative (4 Moderate)
  task 10     Q6A  trustworthiness, 0-10

Each wording is Q's, with the fill resolved for that arm, after asserting PG resolves to
the same words for every arm. Q1's two paragraphs are joined with a space. Grid outcomes
are the stem, a space, then the item. The Q2 stem ends with a full stop, as fielded. PG
underlines the group in most places ("<u>...</u>", typed into the text); the words are
kept and the underline dropped, as j6xgs does. Typography normalised per CONVENTIONS
(curly quotes straightened, en dashes in option labels made hyphens, the double space in
Q5 made single). "GRID ITEMS, RANDOMIZE" is the order of a grid's rows on screen; no row
cites a position. The codebook labels each grid column with its item in brackets; the
generator asserts each is Q's item for that column.

Scales: endpoint labels are the screen's own (option text without its number, or Q4A's
and Q6A's labels under the 0 and 10 buttons). Q1 is a slider with no labelled ends, so
its instruction names the range only; the question itself says what 0, 50 and 100 mean.
Q5 names its midpoint, "Moderate", which is code 4 of 7.

RESPONSES AND MISSING

Identity recodes over each scale (0-100, 1-7, 0-10). Q1's non-answer codes are 777 /
998 / 999 (DON'T KNOW / SKIPPED ON WEB / REFUSED); every other item's are 77 / 98 / 99,
which on Q1 are real thermometer ratings (77, 98 and 99 degrees: 27 respondents).
So missing_codes is [777, 998, 999] only, and on Q2-Q6 the 77/98/99 codes are dropped
because they lie outside each outcome's declared recode (the build drops any value not in
the recode). Jev (recipe_prep) called every one of those labels a non-answer at conf >=
0.98, agreeing with the regex. Only the web skip code occurs: Q1 998 331, Q2A-D 15 / 10 /
10 / 16, Q3A-C 22 / 20 / 26, Q4A 11, Q5 16, Q6A 7. No blank cells.

Q1's skip rate (26.0%) is far above every other item's (at most 2.0%). It is the
thermometer slider: a respondent who never moved it was recorded as skipped. Those rows
are dropped, not imputed (there is no answer to keep).

ROW ARITHMETIC: 1,274 x 11 = 14,014 cells minus 484 skips = 13,530 rows.

PERSONA

The AmeriSpeak set (ledger 149), as the sibling 2024 deposits: AGE, GENDER, EDUC5,
RACETHNICITY, INCOME, MARITAL, EMPLOY, REGION4, HHSIZE, HOME_TYPE, HOUSING, METRO,
INTERNET, PHONESERVICE, PartyID7, RELIG, ATTEND, and ideology from IDEO ("DATA-ONLY:
Computed 5-level political ideology"; this file has no IDEO20). recipe_prep agreed on
every field it judged at conf >= 0.89 except region, REVIEW between REGION4 (0.60) and
REGION9 (0.34); REGION4 is used, as in every AmeriSpeak recipe and the crosswalk built
for it. recipe_prep's labels pass was capped at 40 of 196 columns and the persona columns
fell past the cap, so their labels were read by hand: plain answers apart from those
declared below.

persona_missing (each exercised): PartyID7 -1 "Unknown" (2 respondents), IDEO -1
"Unknown" (15), RELIG 98 "SKIPPED ON WEB" (2). GENDER 0 "Unknown" and the 77/99 codes on
RELIG, and all three on ATTEND, have no occurrences and are not declared.

RELIG code 1's label in this file is "Protestant (Baptist, Methodist, etc.)", a shorter
form of the label this deposit's own PG prints for the same preload code (P_RELIG 1,
"Protestant (Baptist, Methodist, Non-denominational, Lutheran, Presbyterian,
Pentecostal, Episcopalian, Reformed, Church of Christ, Jehovah's Witness, etc.)"),
which is the label the AmeriSpeak crosswalk maps. Rewritten to PG's words. HHSIZE's
labels are words ("Two persons"), which the integer field cannot hold (8972k found this
dropped household size from every row silently); codes 1-5 are rewritten to their own
numbers, and code 6 "Six or more persons" is left unrendered (133 respondents), because
"6" would claim exactly six.

Kept although they sit near the topic: RELIG and ATTEND. The condition names a group a
persona value can also name (RELIG 9 "Atheist (do not believe in God)", 10 "Agnostic (not
sure if there is a God)"), but it states nothing about what any group thinks, so nothing
follows by substitution (CONVENTIONS, the condition must not name the respondent's own
persona category: "naming ... is not enough", rich, 10 Oct 2026). The respondent's
religion is an ordinary predictor of how they feel about irreligious candidates, as age
is.

Not mapped: PartyID5, AGE4, AGE7, INCOME4, INCOME9, REGION9, STATE (coarser or finer
duplicates), RELIG_OE (free text), HH01-HH18OV, Device, the conjoint's attribute and
order columns, MayorPresidentRandom_1.

UK CHECK

The block asks how the respondent feels about political candidates who are atheist, not
sure there is a God, or of no religion: warmth, whether they threaten "people like me",
disgust, anxiety and anger, how supportive they are of religion in public life, where they
sit politically and how trustworthy they are. Nothing in Q1-Q6 names an American party,
office, institution or place, and candidates' religion is a question a UK respondent can
answer. "favorable" is American spelling, kept word-for-word.

Q5's "extremely liberal" to "extremely conservative" scale is the American ideology
scale. Judged ANSWERABLE by a UK respondent and kept: both words are in ordinary British
political use, the scale is fully labelled, and the question asks where a group of
candidates sits rather than about any US party. The caveat, for a reader of the UK rows:
in Britain "liberal" more often means the economic or civil-liberties sense than the
American "left", and "conservative" carries the name of a party, so a UK answer to Q5 may
not mean what the same code meant to this sample. No word was changed.

VERIFICATION

Not in SocSci210 (fielded 2024; comparable_to_socsci210: false), and no paper with this
study's numbers is in the deposit. tests/test_gen_ysqex.py holds the answer keys: the
built rows reproduce every (arm, outcome) count and mean computed independently from the
.dta (not the .sav the build reads), and every outcome's whole-sample distribution in
NORC's unweighted frequency tables, code by code.
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

STUDY = "ysqex"
RAW = REPO / "data" / "raw" / STUDY
DATA_FILE = "TESS 146 Golebiowska_Final Data24Apr30.sav"
_STEM = "9089.146 TESS 146 Golebiowska_vFINAL"
SIMPLE = RAW / f"{_STEM}simple.docx"
PROG = RAW / f"{_STEM}prog.docx"
CODEBOOK = RAW / "9089.146 TESS 146 Golebiowska_Codebook.xlsx"
RECIPE = REPO / "recipes" / f"{STUDY}.yaml"
LICENCE = (
    "None stated: the TESS deposit on OSF (ysqex) states no licence, and TESS has since "
    "suspended operations. No explicit grant of redistribution rights should be assumed."
)

ID_VAR = "CaseId"
COND_VAR = "RND_01"
CODES = [1, 2, 3]
# The fill's three groups, as factor levels.
LEVELS = {1: "atheist", 2: "not_sure_god", 3: "no_religion"}
FRAME = "This set of survey questions was about"  # ADDED words, see notes

# Question label in the questionnaire -> the data columns it fills, in order.
QUESTIONS = {
    "Q1": ["Q1"],
    "Q2": ["Q2A", "Q2B", "Q2C", "Q2D"],
    "Q3": ["Q3A", "Q3B", "Q3C"],
    "Q4A": ["Q4A"],
    "Q5": ["Q5"],
    "Q6A": ["Q6A"],
}
OUTCOME_VARS = [v for vs in QUESTIONS.values() for v in vs]


# ---------------------------------------------------------------------------
# The questionnaire (.docx, read as Word stores it)
# ---------------------------------------------------------------------------


def _clean(text: str) -> str:
    """Typography only: curly quotes, dashes, non-breaking spaces, PG's typed underline."""
    text = unescape(text)
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-").replace("\xa0", " ")
    text = text.replace("<u>", "").replace("</u>", "")
    return re.sub(r"\s+", " ", text).strip()


def paragraphs(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    return [
        _clean("".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p)))
        for p in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S)
    ]


FILL = re.compile(r"\[IF RND_01=1:([^,\[\]]+), IF RND_01=2:([^,\[\]]+), IF RND_01=3:([^,\[\]]+)\]")


def resolve(text: str, code: int) -> str:
    """The words the screen showed for this RND_01 code."""
    out = FILL.sub(lambda m: m.group(code).strip(), text)
    if "[" in out or "]" in out or "RND_" in out:
        raise SystemExit(f"unresolved fill: {out!r}")
    return out


def group_phrase(path: Path, code: int) -> str:
    """The group's words for this code, from the first fill in Q1."""
    q1 = block(path)["Q1"]["stem"][0]
    m = FILL.search(q1)
    if not m:
        raise SystemExit(f"{path.name}: no RND_01 fill in Q1")
    return m.group(code).strip()


def block(path: Path) -> dict[str, dict[str, list[str]]]:
    """Q1-Q6A: stem paragraphs, grid items and options (fills unresolved)."""
    paras = paragraphs(path)
    start, end = paras.index("Q1."), paras.index("Q7.")
    lines = [p for p in paras[start:end] if p]
    out: dict[str, dict[str, list[str]]] = {}
    cur: dict[str, list[str]] | None = None
    mode = "stem"
    for s in lines:
        m = re.fullmatch(r"(Q\d[A-Z]?)\.", s)
        if m:
            cur = {"stem": [], "items": [], "options": []}
            out[m.group(1)] = cur
            mode = "stem"
            continue
        if cur is None or s.startswith("#[") or s == "○":
            continue
        if s == "GRID ITEMS, RANDOMIZE:":
            mode = "items"
        elif s == "RESPONSE OPTIONS:":
            mode = "options"
        elif re.fullmatch(r"\d+", s) or (mode == "stem" and cur["options"]):
            # Q4A / Q6A: a bare 0..10 row of buttons, then the two end labels.
            mode = "options"
            cur["options"].append(s)
        else:
            cur[mode].append(s)
    if list(out) != list(QUESTIONS):
        raise SystemExit(f"{path.name}: questions {list(out)}")
    return out


def _texts(path: Path) -> dict[str, Any]:
    """Per code: the eleven outcome wordings, fills resolved; plus the option lists."""
    qs = block(path)
    words: dict[int, list[str]] = {}
    for code in CODES:
        w: list[str] = []
        for q, cols in QUESTIONS.items():
            stem = resolve(" ".join(qs[q]["stem"]), code)
            items = qs[q]["items"]
            if len(items) != (len(cols) if len(cols) > 1 else 0):
                raise SystemExit(f"{path.name} {q}: {len(items)} items for {cols}")
            if items:
                w += [f"{stem} {resolve(item, code)}" for item in items]
            else:
                w.append(stem)
        words[code] = w
    return {
        "questions": words,
        "items": {q: qs[q]["items"] for q in QUESTIONS},
        "options": {q: qs[q]["options"] for q in QUESTIONS},
        "groups": {code: group_phrase(path, code) for code in CODES},
    }


def fielded() -> dict[str, Any]:
    """Q, after asserting PG shows the same words for every code (CONVENTIONS, Source
    authority, ledger 52)."""
    q, pg = _texts(SIMPLE), _texts(PROG)
    for key in ("questions", "items", "options", "groups"):
        if q[key] != pg[key]:
            raise SystemExit(f"PG and Q differ on {key}")
    return q


def protestant_label() -> str:
    """P_RELIG code 1 in full, from PG's preload table."""
    paras = paragraphs(PROG)
    i = paras.index("P_RELIG")
    # Word stores the code and the label in separate runs split by a tab: "1Protestant".
    (line,) = [x for x in paras[i : i + 20] if x.startswith("1Protestant (")]
    return line.removeprefix("1")


def codebook_items() -> dict[str, str]:
    """Codebook: grid variable -> the bracketed item it prints before the stem."""
    import openpyxl

    wb = openpyxl.load_workbook(CODEBOOK, read_only=True)
    out: dict[str, str] = {}
    for row in wb.worksheets[0].iter_rows(values_only=True):
        if row and isinstance(row[0], str) and row[0] in OUTCOME_VARS and row[1]:
            m = re.match(r"\[(.*?)\] (?:How|To what)", _clean(str(row[1])))
            if m:
                out[row[0]] = m.group(1)
    return out


def _strip_number(label: str) -> str:
    return re.sub(r"^\d+ - ", "", label)


def scales(options: dict[str, list[str]]) -> dict[str, dict[str, Any]]:
    """Each outcome's scale, from the screen's own option labels."""
    agree = options["Q2"]
    feel = options["Q3"]
    if agree[0] != "1 - Strongly agree" or agree[-1] != "7 - Strongly disagree" or len(agree) != 7:
        raise SystemExit(f"Q2 options {agree}")
    if feel[0] != "0 - Not at all" or feel[-1] != "10 - Very frequently" or len(feel) != 11:
        raise SystemExit(f"Q3 options {feel}")
    out: dict[str, dict[str, Any]] = {"Q1": {"min": 0, "max": 100}}
    for v in QUESTIONS["Q2"]:
        out[v] = {
            "min": 1,
            "max": 7,
            "min_label": _strip_number(agree[0]),
            "max_label": _strip_number(agree[-1]),
        }
    for v in QUESTIONS["Q3"]:
        out[v] = {
            "min": 0,
            "max": 10,
            "min_label": _strip_number(feel[0]),
            "max_label": _strip_number(feel[-1]),
        }
    for q in ("Q4A", "Q6A"):
        opts = options[q]
        if opts[:11] != [str(i) for i in range(11)] or len(opts) != 13:
            raise SystemExit(f"{q} options {opts}")
        out[q] = {"min": 0, "max": 10, "min_label": opts[11], "max_label": opts[12]}
    five = options["Q5"]
    if len(five) != 7:
        raise SystemExit(f"Q5 options {five}")
    out["Q5"] = {
        "min": 1,
        "max": 7,
        "min_label": five[0],
        "mid_label": five[3],
        "max_label": five[6],
    }
    return out


def recipe() -> dict[str, Any]:
    q = fielded()
    ds = read_any(RAW / DATA_FILE)
    labels = ds.value_labels

    if sorted(int(c) for c in ds.df[COND_VAR].dropna().unique()) != CODES:
        raise SystemExit(f"{COND_VAR} codes changed")
    if ds.df[COND_VAR].isna().any() or not ds.df[ID_VAR].is_unique:
        raise SystemExit(f"{COND_VAR} has blanks or {ID_VAR} is not unique")

    groups = q["groups"]
    want_groups = {
        1: "political candidates who are atheist",
        2: "political candidates who are not sure there is a God",
        3: "political candidates who do not currently identify with a religion",
    }
    if groups != want_groups:
        raise SystemExit(f"fill groups changed: {groups}")
    # Every outcome wording names its own arm's group and no other.
    for code in CODES:
        for text in q["questions"][code]:
            low = text.lower()
            if want_groups[code].lower() not in low:
                raise SystemExit(f"arm {code}: an outcome does not name its group: {text!r}")
            for other in CODES:
                if other != code and want_groups[other].lower() in low:
                    raise SystemExit(f"arm {code}: an outcome names arm {other}'s group")

    # The codebook labels each grid column with its item; it must be Q's item, with the
    # three groups printed as one slash-separated fill.
    cb = codebook_items()
    for qn in ("Q2", "Q3"):
        for var, item in zip(QUESTIONS[qn], q["items"][qn], strict=True):
            want = FILL.sub(lambda m: f"[{m.group(1)}/{m.group(2)}/{m.group(3)}]", item)
            if cb.get(var) != want.rstrip("."):
                raise SystemExit(f"{var}: codebook item {cb.get(var)!r} is not Q's {want!r}")

    sc = scales(q["options"])
    # The data's value labels agree with the screen's options.
    for var in OUTCOME_VARS:
        s = sc[var]
        got = {int(k): _clean(v) for k, v in labels[var].items()}
        non = {777, 998, 999} if var == "Q1" else {77, 98, 99}
        if {k for k in got if k >= 77} != non:
            raise SystemExit(f"{var}: non-answer codes {sorted(got)}")
        if var == "Q1":
            continue
        if _strip_number(got[s["min"]]) != s["min_label"]:
            raise SystemExit(f"{var}: min label {got[s['min']]!r}")
        if _strip_number(got[s["max"]]) != s["max_label"]:
            raise SystemExit(f"{var}: max label {got[s['max']]!r}")
    if [labels["Q5"][float(k)] for k in range(1, 8)] != q["options"]["Q5"]:
        raise SystemExit("Q5 value labels differ from Q's options")

    outcomes = []
    for t, var in enumerate(OUTCOME_VARS):
        s = sc[var]
        outcomes.append(
            {
                "var": var,
                "task_num": t,
                "question": q["questions"][1][t],
                "scale": s,
                "response_recode": {i: i for i in range(s["min"], s["max"] + 1)},
            }
        )
    arms = [
        {
            "raw": code,
            "condition_num": code - 1,
            "factors": {"target_group": LEVELS[code]},
            "text": f'{FRAME} "{groups[code]}".',
            "items": {t: {"outcome_question": text} for t, text in enumerate(q["questions"][code])},
        }
        for code in CODES
    ]

    return {
        "study_id": STUDY,
        "source": "tess",
        "title": "Membership in a stigmatized religious minority and political support",
        "data_file": DATA_FILE,
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": ID_VAR,
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_var": COND_VAR,
            "factors": ["target_group"],
            "arms": arms,
            "considered_and_rejected": {
                "MayorPresidentRandom_1": "Order of the conjoint's mayor and president "
                "blocks (Q9-Q16), which are not built. Assigned after Q1-Q6 were answered.",
                **{
                    f"AttributeOrder_{k}": "Row order of the conjoint's eight candidate "
                    "attributes (fixed per respondent, PG), for Q9-Q16, which are not built. "
                    "Set after Q1-Q6 were answered and changes no word of them."
                    for k in range(1, 9)
                },
            },
        },
        "outcomes": outcomes,
        "response_recode": {i: i for i in range(1, 8)},
        "missing_codes": [777, 998, 999],
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
            "religion": "RELIG",
            "religious_attendance": "ATTEND",
        },
        "persona_label_rewrite": {
            "RELIG": {1: protestant_label()},
            "HHSIZE": {i: str(i) for i in range(1, 6)},
        },
        "persona_missing": {
            "PartyID7": [-1],
            "IDEO": [-1],
            "RELIG": [98],
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
