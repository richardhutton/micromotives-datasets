#!/usr/bin/env python3
"""Derive `recipes/vwn96.yaml`: TESS3 137 (Yeager, 2013), "What's the Best Way to Motivate Kids?".

Every respondent reads two vignettes about a high-school student who says "I'm
giving up", imagines being the student's teacher, and picks which of four
motivating statements they would be MOST likely to use. `XTESS137` randomises
which student comes FIRST: 1 = poor family / inner-city school first, 2 =
moderately wealthy family / suburban school first. The four statements are
shown in a per-respondent random order that the deposit RECORDS
(`Order_Q1_Q3_*` for arm 1, `Order_Q2_Q4_*` for arm 2), and the second student
is shown the statements in the same order as the first (programming notes).

Two things this script does that a hand-written recipe could not:

1. The cell texts are assembled from fragments of the fielded questionnaire
   held below by line number, and `--check` asserts each fragment occurs
   word-for-word (typography normalised) in the questionnaire text.
2. It writes `vwn96-derived.sav`: the deposit's corrected .sav plus ONE derived
   column and SEVEN blanked cells, nothing else (`--check` asserts this cell by
   cell):
     * `Order_Q1_Q3_1`: the deposit records the position of statements 2-4 for
       arm 1 but not statement 1 (the column is absent from BOTH .sav files on
       OSF). Positions are a permutation of 1-4 and the other three are
       distinct on all 1,049 arm-1 rows, so statement 1's position is the one
       left over: 10 - (sum of the other three). Arithmetic, not inference.
     * The second-student answer (Q3A arm 1, Q4A arm 2) is blanked for
       respondents who were NOT asked the full first-student sequence (they
       left Q1A/Q2A or Q1B/Q2B unanswered, so the routing skipped the later
       first-student screens). The second-student condition narrates that
       sequence as asked, and it was not asked of them. 7 answered cells.

    uv run python scripts/gen_vwn96.py --write
    uv run python scripts/gen_vwn96.py --check
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw/vwn96"
QUEX_TXT = RAW / "quex/TESS3 134 Johnston_TESS3 137 Yeager Survey.txt"
SAV = RAW / "Yeager-correcteddata.sav"
DERIVED = RAW / "vwn96-derived.sav"
RECIPE = ROOT / "recipes/vwn96.yaml"

QUEX_LINES = QUEX_TXT.read_text(encoding="utf-8").split("\n") if QUEX_TXT.exists() else []


def norm(s: str) -> str:
    """Typography only (docs/CONVENTIONS.md): quotes, dashes, runs of spaces."""
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace(" ", " ")
    return re.sub(r"[ \t]+", " ", s).strip()


def q(line: int) -> str:
    """Questionnaire line (1-based, blank lines kept), typography normalised.

    An option line ends with a tab and its code; the code is stripped.
    """
    return norm(re.sub(r"\t\s*\d+\s*$", "", QUEX_LINES[line - 1]))


# --- the instrument, by line of the textutil .txt ------------------------------
# Line numbers are pinned here and `--check` re-reads them, so a re-converted
# questionnaire whose lines moved fails rather than shifting text silently.
EXPECT = {
    101: "On the next screen, you'll read a brief story about a student. When reading it, "
    "imagine you were a teacher. Then say what you would be most likely to do in the situation.",
    107: "Q1a. Imagine a student from a poor family who attends a public high school located in "
    "the inner-city. You hear the student say \"I don't want to do this assignment any more. "
    "I don't see the point. I'm giving up.\"",
    109: "Imagine you were this student's teacher and wanted to motivate the student.",
    111: "Please read each statement below. Then select the statement that best describes what "
    "you would be MOST likely to do. There are no right or wrong answers - just provide your "
    "honest opinion.",
    139: "Q2a. Imagine a student from a moderately wealthy family who attends a public high school "
    "located in a suburban neighborhood. You hear the student say \"I don't want to do this "
    "assignment any more. I don't see the point. I'm giving up.\"",
    141: "Imagine you were this student's teacher and wanted to motivate the student.",
    143: "Please read each statement below. Then select the statement that best describes what "
    "you would be MOST likely to do. There are no right or wrong answers - just provide your "
    "honest opinion.",
    169: "Now please read a story about a second student. Again, imagine you were a teacher and "
    "say what you would be most likely to do.",
    175: "Q3a. Imagine a student from a moderately wealthy family who attends a public high school "
    "located in a suburban neighborhood. You hear the student say \"I don't want to do this "
    "assignment any more. I don't see the point. I'm giving up.\"",
    177: "Imagine you were this student's teacher and wanted to motivate the student.",
    179: "Please read each statement below. Then select the statement that best describes what "
    "you would be MOST LIKELY to do. There are no right or wrong answers - just provide your "
    "honest opinion.",
    207: "Q4a. Imagine a student from a poor family who attends a public high school located in "
    "the inner-city. You hear the student say \"I don't want to do this assignment any more. "
    "I don't see the point. I'm giving up.\"",
    209: "Imagine you were this student's teacher and wanted to motivate the student.",
    211: "Please read each statement below. Then select the statement that best describes what "
    "you would be MOST LIKELY to do. There are no right or wrong answers - just provide your "
    "honest opinion.",
}
# The four statements, codes 1-4, identical under all twelve items (Q 112-115,
# 121-124, 130-133, 144-147, 153-156, 162-165, 180-183, 189-192, 198-201,
# 212-215, 221-224, 230-233).
STATEMENT_LINES = [112, 113, 114, 115]
ALL_OPTION_BLOCKS = [112, 121, 130, 144, 153, 162, 180, 189, 198, 212, 221, 230]


def strip_qid(s: str) -> str:
    """'Q1a. Imagine ...' -> 'Imagine ...': the question id is not respondent-facing."""
    return re.sub(r"^Q\d[a-c]\. ", "", s)


DISPLAY = q(101) if QUEX_LINES else ""
SECOND = q(169) if QUEX_LINES else ""
IMAGINE = q(109) if QUEX_LINES else ""
VIGNETTE = {
    "poor": strip_qid(q(107)) if QUEX_LINES else "",
    "wealthy": strip_qid(q(139)) if QUEX_LINES else "",
}
STEM_FIRST = q(111) if QUEX_LINES else ""  # Q1a/Q2a: "MOST likely"
STEM_SECOND = q(179) if QUEX_LINES else ""  # Q3a/Q4a: "MOST LIKELY"
STATEMENTS = [q(n) for n in STATEMENT_LINES] if QUEX_LINES else []

# --- the words WE add (docs/CONVENTIONS.md, "Narrating what the respondent did")
LISTED = "The statements were listed in this order:"
ASKED_FIRST = (
    "You were asked to select, from the statements listed below, the statement that best "
    "describes what you would be MOST likely to do; then, of the remaining statements, the "
    "one you would be MOST LIKELY to do; then, of the last two statements, the one you "
    "would be MORE LIKELY to do."
)
ADDED = [LISTED, ASKED_FIRST]

# arm raw code -> (condition_num, first student, second student, order vars,
#                  first-student var, second-student var)
ARMS = {
    1: (0, "poor", "wealthy", [f"Order_Q1_Q3_{k}" for k in range(1, 5)], "Q1A", "Q3A"),
    2: (1, "wealthy", "poor", [f"Order_Q2_Q4_{k}" for k in range(1, 5)], "Q2A", "Q4A"),
}
LEVEL = {"poor": "poor_inner_city", "wealthy": "wealthy_suburban"}
# The first-student screens that must have been ASKED for the second-student
# narration to be true: a (always), b (shown if a answered), c (shown if a and b
# answered). Respondents missing a or b were not asked the full sequence.
SEQUENCE_GATE = {1: ("Q1A", "Q1B"), 2: ("Q2A", "Q2B")}


def bullets() -> str:
    return "\n".join(f"• {s}" for s in STATEMENTS)


def cell(first: str, second: str | None) -> str:
    """Condition text: the student screen(s) up to and including this outcome's own."""
    parts = [DISPLAY, VIGNETTE[first], IMAGINE]
    if second is not None:
        parts += [ASKED_FIRST, SECOND, VIGNETTE[second], IMAGINE]
    parts += [LISTED + "\n" + bullets()]
    return "\n\n".join(parts)


def legend(stem: str) -> str:
    keys = "; ".join(f'{k} means "{s}"' for k, s in enumerate(STATEMENTS, 1))
    return f"{stem}\n{keys}"


NOTES = """\
TESS3 137 (David Yeager), "What's the Best Way to Motivate Kids?", fielded by
GfK KnowledgePanel 2-14 May 2013 together with TESS3 134 (Johnston) in one
survey (SNO 17398): 3,316 fielded, 2,071 completed, 2,026 qualified completes
after dropping interviews under one minute (response rate report). The .sav
has 2,026 rows, CaseID unique. One experiment, one recipe.


SOURCES AND PROVENANCE

  Q    = "TESS3 134 Johnston_TESS3 137 Yeager Survey.docx", the FIELDED GfK
         programming questionnaire for the joint survey (SNO 17398, "April
         2013"). OSF registration vwn96, child component 7b64e "Materials and
         Methods" (https://osf.io/download/exgp7/, 2,009,114 bytes, sha256
         99ded46deccc05d63bb7866915ddef16d266fbcda354084fca97b7aa18db849e),
         fetched 2026-10-10 into data/raw/vwn96/quex/ and converted with macOS
         textutil. Line numbers below are 1-based into that .txt, blank lines
         kept. No tracked changes in the .docx. Its ten images (EMF) all sit in
         Johnston's section 1 (none after Johnston's Q3), so this study's
         stimulus is text only.
  RR   = "TESS3 137 Yeager - Response Rate Report.doc", component zwt5v "Data"
         (https://osf.io/download/p2fyb/, sha256
         353f690c6d9d830fe13d2c7f5849fd1ee7f8300198ee77f0189fcf9e96865719):
         field dates and N only.
  Data = Yeager-correcteddata.sav, component zwt5v
         (https://osf.io/download/c65jt/, 200,076 bytes, sha256
         ca13af4429cd76cdbd9117053f025cb2eb4297dac68b845898d06fc6b706c82d).
         The same component holds "TESS3 137_Yeager_Client.sav"
         (https://osf.io/download/ujec8/, sha256
         3eb72e07538d1f81ce7c9eaecca6fa17de799333d6b08b7733186dd8e686b415),
         fetched to data/raw/vwn96/orig/ for comparison only: the corrected
         file is the client file plus one column (PARTY7) and is identical to
         it on every shared column and CaseID (checked cell by cell).
  Built from vwn96-derived.sav, written by `scripts/gen_vwn96.py --write`:
         the corrected .sav plus the derived Order_Q1_Q3_1 and with 7
         second-student answers blanked (see below); `--check` asserts
         nothing else differs.
  No proposal is in the deposit; the GfK methodology PDF (rypf5) was not used.

  Q is the fielded version: its samvar block (Q 20-30) declares XTESS137
  (1-2) and XORDER (1,2), both in the .sav with those codes; the items Q1a-Q4c
  are the .sav's Q1A-Q4C with the same four options under codes 1-4 (value
  labels identical to Q's option text); the routing in Q (Q1a only if
  XTESS137 = 1, etc.) matches the data exactly (every arm-1 respondent holds
  Q1A/Q3A and no Q2A/Q4A, and the reverse); and Q's "RANDOMIZE AND RECORD
  ORDER" is the .sav's Order_* columns. One wording disagreement: the .sav's
  variable labels for Q3A and Q4A read "MOST likely", where Q (179, 211)
  prints "MOST LIKELY". Q is the authority and is followed.


THE DESIGN (Q 47, 101-233)

  XTESS137 randomises the ORDER of two student vignettes, between subjects:
    1 = poor family, inner-city school first (Q1a), then moderately wealthy,
        suburban (Q3a)                                      -> condition 0
    2 = moderately wealthy, suburban first (Q2a), then poor, inner-city
        (Q4a)                                               -> condition 1
  1,049 / 977. Each student screen asks, of four statements, which the
  respondent would be MOST likely to use as the student's teacher (a), then of
  the remaining three (b), then of the last two (c). The four statements are
  the same throughout; their on-screen order was randomised per respondent
  and RECORDED, once per arm (Q 105, 137), and the later screens "KEEP SAME
  ORDER AS PRESENTED IN Q1a/Q2a" (Q 118-205), so one order variable set
  covers both students. Within-subject, so both student types reach every
  respondent and the factor is which one came first.

  Assignment vs answers (first-choice code 1/2/3/4; -1 refused):
    arm 1 Q1A (poor, first):     149 / 115 / 386 / 389; 10 refused
    arm 1 Q3A (wealthy, second): 149 / 202 / 340 / 350;  8 refused
    arm 2 Q2A (wealthy, first):   89 /  79 / 418 / 388;  3 refused
    arm 2 Q4A (poor, second):    200 / 139 / 323 / 310;  5 refused
  Every Q?B differs from its Q?A and every Q?C from both, on every row
  (the "DO NOT SHOW RESPONSE SELECTED" routing held).

  XORDER (Q 47) randomises whether this survey's section came before or
  after Johnston's (TESS3 134) section, whose stimulus is one of ten news
  clipping IMAGES chosen by XTESS134, a variable not in this deposit. Not
  expressed: the earlier section cannot be rendered (images, assignment
  absent) and a row cannot say where it sat (CONVENTIONS, "Sequence
  signposting"). Declared in considered_and_rejected. It is crossed with
  XTESS137 (514/535/490/487).


OUTCOMES (2; one answer type, a nominal choice of four)

  task 0  first student, a-screen: Q1A (arm 1) / Q2A (arm 2). Stem Q 111 / 143.
  task 1  second student, a-screen: Q3A (arm 1) / Q4A (arm 2). Stem Q 179 / 211.
  The stems are word-for-word and differ only in "MOST likely" (first) vs
  "MOST LIKELY" (second), as Q prints them; each task's stem is identical
  across arms. The answer follows the corpus answer-key form for nominal items
  ('1 means "..."; 2 means "..."'), keyed by the .sav codes = Q's order: an
  answer key, not a claim of display order. The display order is in the
  condition.

  NOT BUILT: the b and c screens (Q1B-Q4C). Each shows only the statements the
  respondent had NOT already picked, so its option set is a function of the
  respondent's own earlier answer; a row could state it only by writing that
  answer into the condition, which puts a response into the part we write.
  Cost: 8,027 answered cells (Q1B 1,035, Q1C 1,032, Q3B 1,040, Q3C 1,036,
  Q2B 973, Q2C 971, Q4B 971, Q4C 969). The study's ranking is therefore
  represented by its first choice only.


THE CONDITION: WORD-FOR-WORD VS NARRATION

  Each cell is: the display (Q 101), then the student screen, then for the
  second student the narrated first-student questions, Q's transition display
  (Q 169) and the second student screen, then the statements in the
  respondent's recorded order. Paragraph breaks as newlines.

  Word-for-word from Q (typography normalised: curly quotes straightened, the
  en dash in "answers - just" made a hyphen, double spaces after full stops
  made single): Q 101, the vignettes Q 107 / 139 (question ids "Q1a." etc.
  dropped; Q3a = Q2a and Q4a = Q1a word-for-word, checked), Q 109 "Imagine you
  were this student's teacher ...", Q 169, the four statements (Q 112-115;
  identical in all twelve items, checked), and the stems Q 111 / 179 (in the
  outcome). "any more" and "inner-city" are Q's own.

  ADDED words (description, not transcription):
    "The statements were listed in this order:" before the bullet list. It is
      true: the order is each respondent's recorded order. One "• " per
      statement; the bullets carry no numbers or letters.
    For the second student only, the first-student questions, narrated as
      ASKED, never as given:
      "You were asked to select, from the statements listed below, the
      statement that best describes what you would be MOST likely to do;
      then, of the remaining statements, the one you would be MOST LIKELY to
      do; then, of the last two statements, the one you would be MORE LIKELY
      to do."
      Reuses Q's own phrases (Q 111, 120, 129); identical in both arms ("best"
      in Q2b's stem but not Q1b's is not carried, so the narration carries no
      arm signal of its own). "listed below" refers forward to the same four
      statements, which by design were in the same order for both students.

  STATEMENT ORDER. `items.<task>.line_order_vars` reorders the four bullets
  per respondent. Reading of the code: Order_Q1_Q3_k = the position (1-4) at
  which statement k was shown. Supported by (a) the variable labels, which
  name statement k's text and say "Order of Q1_Q3_k in Q1_Q3_1 to Q1_Q3_4
  sequence", and (b) the data: under this reading the first choice shows a
  primacy/recency U on all four items (position 1 chosen most or second-most
  often, position 2 least, every item), the classic list-order shape; under
  the inverse reading ("the statement shown at slot k") the pattern is flat
  or monotone and differs between items. The independent checker tested
  this: a likelihood-ratio test of primacy (first choice vs on-screen
  position) gives LR 35.9, p = 8e-8, under this reading and 0.59 under the
  inverse, and it holds in arm 2 alone, where no order column is derived.
  That is evidence, not proof (ledger 135). Which statements appear, and every response, are right under either
  reading; only the bullet order is at stake.
  Order_Q1_Q3_1 is derived (see the generator docstring); all 24 orders occur
  in both arms (29-58 respondents each).


DROPPED / EXCLUDED, WITH ROW COST

  * -1 Refused on the a-screens (missing_codes): task 0 13 (10 + 3), task 1
    13 (8 + 5).
  * Second-student rows of respondents not asked the full first-student
    sequence (Q1A/Q2A or Q1B/Q2B unanswered, so the narration "then, of the
    remaining ... then, of the last two" is false for them): 14 + 4
    respondents, of whom 7 answered the second-student screen (6 arm 1, 1
    arm 2). Blanked in the derived .sav; 7 rows. (11 more of those cells held
    -1 Refused and are blanked too; they produce no row either way.)
  * The b/c screens: 8,027 cells (above).
  * Teacher_flag (63 profiled teachers) and xpcm0160 (occupation, 1,112
    non-missing): not in the persona; the schema has no occupation field.
    A reviewer may want them as moderators (the respondent imagines being a
    teacher). Measured before the stimulus.


PERSONA

  GfK KnowledgePanel standard profile, as 7tzpe (TESS3 156): PPAGE, PPGENDER,
  PPEDUCAT, PPETHM, PPINCIMP, PPMARIT, PPWORK, PPREG4, PPHHSIZE, PPHOUSE,
  PPRENT, PPMSACAT, PPNET, plus the study's profile pulls PARTY7, IDEO, REL2
  (named without the X of Q's samvar block; the corrected file adds PARTY7,
  which the client file lacked). -1 Refused occurs on IDEO 7 and REL2 5 and is
  dropped from the persona. REL1 (religion) LEFT OUT: its labels
  ("Baptist-any denomination", ...) are not in the religion crosswalk's
  us_amerispeak scheme, so QC rule 14 warns (the same finding as 7tzpe).
  The thing judged is a hypothetical STUDENT (family income, school
  location); it is not part of the persona. PPINCIMP (household income) and
  PPMSACAT (metro / non-metro) sit near the manipulated student attributes
  but do not name them: the condition says "poor family" / "moderately
  wealthy family" and "inner-city" / "suburban", never an income band or
  "Metro", and the outcome (which motivator) is not derivable from either by
  substitution (CONVENTIONS, "The condition must not name the respondent's own
  persona category"). Respondent's own children (PPT01-PPT1317): not in the
  persona; the outcome is about a teacher and a student, not parenting, and
  the schema has no children field.


JEV (scripts/recipe_prep.py vwn96 --source tess --file Yeager)

  assignment: XTESS137, conf 0.93, ok (runner-up XORDER 0.03).
  persona: all ok at conf 1.00 except region PPREG4 REVIEW (0.71, runner-up
    ppreg9 0.22), accepted as every TESS recipe does. Jev picked PPEDUC; PPEDUCAT
    is used, as every KN/GfK recipe does, since the crosswalk harmonises it.
    Jev picked REL1 for religion; left out (rule 14, above).
  labels: 309 asked, 0 disagreements with the regex; -1 Refused / -2 Not asked
    are non-answers.
  directives: all 40 found parse (the run with `--file Yeager` so that the
    questionnaire is in scope; with `--file Yeager-correcteddata.sav` it
    scanned nothing).


RISKIEST JUDGEMENT

  The reading of the order code (above): if Order_*_k is instead "the
  statement shown at slot k", the bullet order on 2,274 of 4,019 rows
  (56.6%) is not the one the respondent saw (10 of the 24 orders read the
  same both ways). Second: dropping the b/c screens,
  which keeps only the first choice of a four-way ranking.


COUNTS

  2,026 respondents x 2 outcomes = 4,052 cells; 26 refused, 7 blanked (not
  asked the full sequence); 4,019 rows. task 0: arm 0 1,039, arm 1 974;
  task 1: arm 0 1,035, arm 1 971.


VERIFICATION

  Not in SocSci210 (catalogue: in_socsci210=no), so no answer key. No
  published table for this deposit was found (see the build report). Verified
  by re-deriving every row from the CORRECTED deposit .sav (not the derived
  file) with scripts/verify_vwn96.py, which holds its own copy of the
  questionnaire strings and asserts each row's condition and outcome text,
  response, order and persona."""

LICENCE = (
    "none stated on the OSF deposit (checked via the OSF API, 2026-10-10: registration vwn96 "
    'and its child components zwt5v "Data" and 7b64e "Materials and Methods" all have '
    "node_license null; same finding recorded 2026-10-02 in "
    "data/catalog/tess_uk_foundation_sources.csv). TESS states no reuse terms for its archived "
    "studies and has since suspended operations. So there is no explicit grant of "
    "redistribution rights for this deposit, and none should be assumed."
)


def build() -> dict:
    arms = []
    for raw, (cnum, first, second, order, var0, var1) in ARMS.items():
        last = cell(first, second)
        arms.append(
            {
                "raw": raw,
                "condition_num": cnum,
                "factors": {"first_student": LEVEL[first]},
                # Arm.text is never rendered (every cell overrides it); set to the
                # arm's whole history so QC rule 5 can see the factor in it.
                "text": last,
                "items": {
                    0: {
                        "outcome_var": var0,
                        "condition_text": cell(first, None),
                        "line_order_vars": list(order),
                    },
                    1: {
                        "outcome_var": var1,
                        "condition_text": last,
                        "line_order_vars": list(order),
                    },
                },
            }
        )
    return {
        "study_id": "vwn96",
        "source": "tess",
        "title": "What's the Best Way to Motivate Kids?",
        "data_file": DERIVED.name,
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "notes": NOTES,
        "condition": {
            "source_var": "XTESS137",
            "factors": ["first_student"],
            "considered_and_rejected": {
                "XORDER": "Randomises whether this survey section came before or after "
                "Johnston's TESS3 134 section (Q 47), whose news-clipping images and "
                "assignment (XTESS134) are not in this deposit; a row cannot say where it "
                "sat. Crossed with XTESS137 (514/535/490/487).",
            },
            "arms": arms,
        },
        "outcomes": [
            {
                "task_num": 0,
                "question": legend(STEM_FIRST),
                "scale": {"min": 1, "max": 4, "nominal": True},
            },
            {
                "task_num": 1,
                "question": legend(STEM_SECOND),
                "scale": {"min": 1, "max": 4, "nominal": True},
            },
        ],
        "response_recode": {1: 1, 2: 2, 3: 3, 4: 4},
        "missing_codes": [-1, -2],
        "persona_missing": {"IDEO": [-1], "REL2": [-1]},
        "persona_map": {
            "age": "PPAGE",
            "gender": "PPGENDER",
            "education": "PPEDUCAT",
            "ethnicity": "PPETHM",
            "income": "PPINCIMP",
            "marital_status": "PPMARIT",
            "employment": "PPWORK",
            "region": "PPREG4",
            "household_size": "PPHHSIZE",
            "housing_type": "PPHOUSE",
            "housing_ownership": "PPRENT",
            "urban_rural": "PPMSACAT",
            "internet_access": "PPNET",
            "party_id": "PARTY7",
            "ideology": "IDEO",
            "religious_attendance": "REL2",
        },
    }


class _Dumper(yaml.SafeDumper):
    pass


def _str(dumper: yaml.SafeDumper, s: str) -> yaml.ScalarNode:
    if "\n" in s:
        return dumper.represent_scalar("tag:yaml.org,2002:str", s, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", s)


_Dumper.add_representer(str, _str)

HEADER = (
    "# GENERATED by scripts/gen_vwn96.py from the fielded questionnaire\n"
    "# (data/raw/vwn96/quex/). Edit the generator, not this file.\n"
)


def render() -> str:
    body = yaml.dump(build(), Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=88)
    return HEADER + body


# --- the derived data file ----------------------------------------------------
EXPECTED_BLANKED = 7  # answered second-student cells of the not-fully-asked; computed, pinned


def _derive(df):  # type: ignore[no-untyped-def]
    import pandas as pd

    out = df.copy()
    arm1 = out["XTESS137"] == 1
    others = out.loc[arm1, ["Order_Q1_Q3_2", "Order_Q1_Q3_3", "Order_Q1_Q3_4"]]
    out["Order_Q1_Q3_1"] = float("nan")
    out.loc[arm1, "Order_Q1_Q3_1"] = 10 - others.sum(axis=1)
    blanked = pd.Series(False, index=out.index)
    for raw, (_, _, _, _, _, second_var) in ARMS.items():
        a, b = SEQUENCE_GATE[raw]
        in_arm = out["XTESS137"] == raw
        not_full = in_arm & ~(out[a].isin([1, 2, 3, 4]) & out[b].isin([1, 2, 3, 4]))
        blanked |= not_full & out[second_var].isin([1, 2, 3, 4])
        out.loc[not_full, second_var] = float("nan")
    return out, blanked


def write_derived() -> None:
    import pyreadstat

    df, meta = pyreadstat.read_sav(str(SAV))
    out, blanked = _derive(df)
    labels = dict(zip(meta.column_names, meta.column_labels, strict=True))
    labels["Order_Q1_Q3_1"] = (
        "[Mention that they need to do the work if they want to earn a lot of money in a "
        "good job one day.] DERIVED by scripts/gen_vwn96.py: 10 - sum(Order_Q1_Q3_2..4)"
    )
    pyreadstat.write_sav(
        out,
        str(DERIVED),
        column_labels=[labels[c] for c in out.columns],
        variable_value_labels=meta.variable_value_labels,
    )
    print(f"wrote {DERIVED} (Order_Q1_Q3_1 added; {int(blanked.sum())} cells blanked)")


def check_derived() -> int:
    import pyreadstat

    bad = 0
    a, _ = pyreadstat.read_sav(str(SAV))
    b, _ = pyreadstat.read_sav(str(DERIVED))
    if list(b.columns) != [*a.columns, "Order_Q1_Q3_1"]:
        print("derived columns are not the deposit's plus Order_Q1_Q3_1")
        return 1
    if not (a["CaseID"].values == b["CaseID"].values).all():
        print("derived CaseIDs differ")
        return 1
    arm1 = a["XTESS137"] == 1
    o = a.loc[arm1, ["Order_Q1_Q3_2", "Order_Q1_Q3_3", "Order_Q1_Q3_4"]]
    if o.isna().any().any() or not (o.nunique(axis=1) == 3).all():
        print("arm-1 recorded positions are not three distinct values on every row")
        bad += 1
    full = b.loc[arm1, [f"Order_Q1_Q3_{k}" for k in range(1, 5)]]
    if not full.apply(lambda r: sorted(r) == [1, 2, 3, 4], axis=1).all():
        print("derived arm-1 order is not a permutation of 1-4 on every row")
        bad += 1
    if b.loc[~arm1, "Order_Q1_Q3_1"].notna().any():
        print("Order_Q1_Q3_1 set outside arm 1")
        bad += 1
    expect, blanked = _derive(a)
    second = ["Q3A", "Q4A"]
    rest = [c for c in a.columns if c not in second]
    if not a[rest].equals(b[rest]):
        print("derived file differs from the deposit outside Q3A/Q4A")
        bad += 1
    for c in [*second, "Order_Q1_Q3_1"]:
        same = (expect[c] == b[c]) | (expect[c].isna() & b[c].isna())
        if not same.all():
            # Both directions: a blank not applied, or a cell changed that should not be.
            print(f"{c}: derived file differs from the derivation on {int((~same).sum())} rows")
            bad += 1
    # What the file actually blanked, read from the file rather than the derivation.
    n = int(sum((a[c].isin([1, 2, 3, 4]) & b[c].isna()).sum() for c in second))
    if n != int(blanked.sum()):
        print(f"file blanks {n} answered cells; derivation says {int(blanked.sum())}")
        bad += 1
    print(f"derived: Order_Q1_Q3_1 on {int(arm1.sum())} rows; {n} answered cells blanked")
    if n != EXPECTED_BLANKED:
        print(f"expected {EXPECTED_BLANKED} blanked cells")
        bad += 1
    return bad


def check() -> int:
    bad = check_derived()
    for line, text in EXPECT.items():
        if q(line) != text:
            print(f"Q {line}: {q(line)!r} != pinned {text!r}")
            bad += 1
    # Second-student vignettes are the first-student ones, word-for-word.
    if strip_qid(q(175)) != VIGNETTE["wealthy"] or strip_qid(q(207)) != VIGNETTE["poor"]:
        print("Q3a/Q4a vignette differs from Q2a/Q1a")
        bad += 1
    for start in ALL_OPTION_BLOCKS:
        if [q(start + i) for i in range(4)] != STATEMENTS:
            print(f"option block at Q {start} differs")
            bad += 1
    # Every arm-text paragraph that is not ours occurs in Q.
    quex = norm(" ".join(QUEX_LINES))
    for raw in ARMS:
        _, first, second, *_ = ARMS[raw]
        for para in cell(first, second).split("\n"):
            para = para.removeprefix("• ")
            if para and para not in ADDED and para not in quex:
                print(f"NOT IN QUESTIONNAIRE: {para[:70]!r}")
                bad += 1
    # Value labels = Q's option text.
    import pyreadstat

    _, meta = pyreadstat.read_sav(str(SAV), metadataonly=True)
    for v in ["Q1A", "Q2A", "Q3A", "Q4A"]:
        labs = [norm(meta.variable_value_labels[v][float(k)]) for k in range(1, 5)]
        if labs != STATEMENTS:
            print(f"{v} value labels differ from Q's statements: {labs}")
            bad += 1
    if RECIPE.read_text() != render():
        print("recipes/vwn96.yaml is not what the generator derives")
        bad += 1
    print("OK" if not bad else f"{bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.write:
        RECIPE.write_text(render())
        print(f"wrote {RECIPE}")
        write_derived()
    if args.check:
        sys.exit(check())
