#!/usr/bin/env python3
"""Derive `recipes/gh396.yaml`: TESS 41 (Knowles, 2005), belonging among the socially isolated.

A 2 (subjective social connection) x 2 (item order) between-subjects design,
one assignment column (`D_VERS`, A-D). The connection factor is a pie chart
whose category boundaries make the respondent's own friend count look either
few (A, C: "Socially Isolated (0-5 close friends)") or many (B, D: "Socially
Embedded (3+ close friends)"). The order factor decides whether the
attachment-enhancing blocks (favourite TV character, groups, a past group task)
come before or after the subjective-isolation blocks (loneliness, friendships,
life satisfaction).

Because the order factor changes WHAT HAD BEEN ASKED before each outcome, every
(arm, outcome block) cell carries its own `condition_text`: the shared opening,
the arm's chart and self-categorisation item, then a narration of each block the
respondent had already been through, in that arm's order. Later blocks are never
named. Writing those 4 x 7 cells by hand invites a copying error nothing
downstream can see, so they are generated here from one list of fragments, and
`--check` confirms that every quoted fragment occurs word-for-word in the
fielded questionnaire.

The pie chart's numbers are not in the questionnaire's text layer. They are in
the four embedded MSGraph objects (`ObjectPool/*/Workbook`, the chart data:
5, 15, 55, 35) and in each object's cached rendering (`EPRINT`, an EMF whose
text records read "49%", "14%", "5%", "32%" and the four category labels).
`--check` re-reads both from the .doc (needs `olefile`, run through
`uvx --with olefile`), so the percentages in the recipe are derived rather
than copied.

    uv run python scripts/gen_gh396.py --write
    uvx --with olefile --with pyyaml python scripts/gen_gh396.py --check
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
QUEX_DOC = ROOT / "data/raw/gh396/quex/tess41_knowles_final.doc"
QUEX_TXT = ROOT / "data/raw/gh396/quex/tess41_knowles_final.txt"
RECIPE = ROOT / "recipes/gh396.yaml"
SAV = ROOT / "data/raw/gh396/tess41_knowles_CLIENT.sav"
OE = ROOT / "data/raw/gh396/quex/tess41_knowles_OE_CLIENT.xls"
DERIVED = ROOT / "data/raw/gh396/gh396-derived.sav"

# --- who is NOT asked about a TV character ------------------------------------
# Q6-Q19 presuppose the character the respondent typed at Q5. These respondents
# typed nothing (the open-ends file's "_na_") or typed that they have none, so
# every item is about a character they said they do not have; 35% of them
# straight-lined the midpoint against 4.6% of everyone else (independent
# checker). Their Q6-Q19 answers are blanked in the derived data file; their
# Q20-Q31 rows stay. HAND-REVIEWED, 2026-10-10: every one of the 412 Q5 answers
# was read. Rule: KEEP anyone whose answer identifies at least one specific
# character, person, cast or programme, however hedged ("Don't really have one.
# The one I liked best was Lenny on Law & Order", "the cast of sex in the city
# reruns", "The cast of 'Lost', but no particular character", a show title, a
# channel, an unrecognised but name-like string). DROP the rest, by reason:
NO_CHARACTER: dict[str, list[int]] = {
    # Q5 left blank: "_na_" in the open-ends file. They saw the ALTERNATE stem.
    "blank": [9, 61, 64, 73, 81, 85, 254, 271, 275, 361, 385],
    # Says they have no favourite / none / do not watch TV.
    "none": [
        1, 5, 6, 7, 18, 22, 27, 28, 31, 34, 36, 38, 39, 40, 45, 49, 50, 63, 67,
        94, 99, 100, 105, 111, 114, 115, 121, 125, 126, 128, 132, 133, 134, 135,
        137, 146, 154, 155, 160, 165, 170, 174, 178, 180, 182, 186, 195, 200,
        201, 203, 208, 215, 219, 222, 225, 243, 245, 246, 248, 251, 265, 267,
        272, 273, 281, 282, 289, 292, 294, 295, 307, 314, 315, 322, 324, 329,
        333, 336, 339, 341, 342, 345, 353, 358, 359, 360, 364, 373, 378, 380,
        381, 391, 394, 403, 406, 407, 408,
    ],
    # Says they don't know / can't say, or a non-answer ("?", "0", "donotno").
    "dont_know": [56, 78, 83, 235, 236, 252, 285, 320],
    # Answers without identifying anyone: "i have many", "everyone who can make
    # laugh or feel ggod", news casters in general, a list of genres, "mexican".
    "names_nobody": [122, 124, 127, 204, 383],
}  # fmt: skip
NO_CHARACTER_IDS = sorted(c for ids in NO_CHARACTER.values() for c in ids)
TV_VARS = [f"Q{i}" for i in range(6, 20)]

# --- word-for-word fragments of the fielded questionnaire --------------------
INTRO = (
    "In the following survey, we are interested in people’s social environment, "
    "their attitudes and preferences, and personality traits."
)
Q1 = "Do you live alone or with others?"
Q2 = "On average, how many waking hours each day do you spend alone?"
Q3 = (
    "Close friends are people with whom you feel a sense of loyalty, understanding, "
    "and camaraderie. You can confide in close friends and call on them when you need "
    "help. How many close friends do you have currently?"
)
JOHNSON = (
    "In a recent survey, Johnson (1999) asked 1,250 randomly selected Americans to "
    "count their close friendships. He then grouped the survey respondents based on "
    "their answers. See the pie chart below for a summary of his findings."
)
CHART_TITLE = "A Sample of 1,250 Respondents (Johnson, 1999)"
Q4 = (
    "Based on your earlier response, which of the following categories shown in the "
    "pie chart applies to you? Are you…"
)
CATEGORIES = {
    "isolated": [
        "Socially Isolated (0-5 close friends)",
        "Weakly Connected (6-10 close friends)",
        "Moderately Connected (11-15 close friends)",
        "Socially Embedded (16+ close friends)",
    ],
    "embedded": [
        "Socially Isolated (0 close friends)",
        "Weakly Connected (1 close friend)",
        "Moderately Connected (2 close friends)",
        "Socially Embedded (3+ close friends)",
    ],
}
# The chart's data labels, in category order (see module docstring and --check).
PERCENTS = ["5%", "14%", "49%", "32%"]

TV_DISPLAY = (
    "In order to get a better idea of who you are, we would like you to answer some "
    "questions about your attitudes and preferences. Specifically, we would like to "
    "know about your television-viewing preferences."
)
Q5 = "Who is your favorite television character?"
TV_STEM = (
    "For the next few items, you will need to report the extent to which you agree or "
    "disagree with statements about your favorite TV character that you listed in the "
    "previous item."
)
TV_ITEMS = {
    "Q6": "I think my favorite TV character is like an old friend.",
    "Q7": "I am not satisfied when other characters replace or overshadow my favorite TV character.",
    "Q8": "My favorite TV character makes me feel comfortable, as if I am with friends.",
    "Q9": "I would like to meet my favorite TV character in person.",
    "Q10": "My favorite TV character seems to understand the things I know.",
    "Q11": "I like hearing my favorite TV character’s voice in my home.",
    "Q12": "When my favorite TV character shows me how he or she feels about some issue, "
    "it helps me to make up my own mind about the issue.",
    "Q13": "I look forward to watching my favorite TV character’s show.",
    "Q14": "I like to compare my ideas with what my favorite TV character says.",
    "Q15": "My favorite TV character keeps me company when his or her program is on television.",
    "Q16": "I see my favorite TV character as a natural, down-to-earth person.",
    "Q17": "When I’m watching the program my favorite TV character is on, I feel as if I "
    "am part of the group.",
    "Q18": "If there were a story about my favorite TV character in a newspaper or "
    "magazine, I would read it.",
    "Q19": "I miss seeing my favorite TV character when his or her program is not on.",
}
GROUP_STEM = (
    "People often perceive collections of individuals differently. For example, some "
    "people may see their fellow coworkers as a meaningful group (the group “employees "
    "of the Alpha Company”) whereas other people may see their fellow coworkers as "
    "distinct, separate individuals (individuals who work for the Alpha Company). For "
    "the next question, you are going to be presented with two collections of "
    "individuals, and we would like to know the extent to which you feel like they "
    "form groups."
)
GROUP_ITEMS = {
    "Q20": "To what extent do you think internet users form a group (rather than just a "
    "bunch of individuals)?",
    "Q21": "To what extent do you think residents of your state form a group (rather "
    "than just a bunch of individuals)?",
}
TASK_DISPLAY = (
    "For the next couple of questions, we would like for you to think about a time "
    "that you worked on a project or some type of task in a group. Perhaps you had to "
    "complete a task within a group in your workplace, a sports team to which you "
    "belong, or a club in which you are a member. Now think about how the project or "
    "the final task turned out."
)
Q22 = "To what extent was the group outcome a success or a failure?"
Q23 = "Was the outcome due to your own individual efforts or due to teamwork?"
LONELY_STEM = (
    "The next questions are about how you feel about different aspects of your life. "
    "For each one, report how often you feel that way."
)
LONELY_ITEMS = {
    "Q24": "How often do you feel that you lack companionship?",
    "Q25": "How often do you feel left out?",
    "Q26": "How often do you feel isolated from others?",
}
FRIEND_DISPLAY = (
    "The next items have to do with your friendships. For each item, please tell us "
    "how much you agree or disagree."
)
Q27 = "To what extent are you satisfied with your friendships?"
Q28 = "To what extent do you think your friendships are strong?"
Q29 = "All things considered, how satisfied are you with your life as a whole these days?"
SELF_STEM = "For the next items, please report the extent to which the following statements are true of you."
SELF_ITEMS = {"Q30": "I have high self-esteem.", "Q31": "I have a strong need to belong."}

WORD_FOR_WORD = [
    INTRO, Q1, Q2, Q3, JOHNSON, CHART_TITLE, Q4, TV_DISPLAY, Q5, TV_STEM,
    *TV_ITEMS.values(), GROUP_STEM, *GROUP_ITEMS.values(), TASK_DISPLAY, Q22, Q23,
    LONELY_STEM, *LONELY_ITEMS.values(), FRIEND_DISPLAY, Q27, Q28, Q29, SELF_STEM,
    *SELF_ITEMS.values(), *CATEGORIES["isolated"], *CATEGORIES["embedded"],
]  # fmt: skip

# --- the narration: the ONLY words in a condition that we wrote ---------------
SHARED = (
    f'You were shown: "{INTRO}" You were then asked: "{Q1}", "{Q2}" and "{Q3}" '
    f'You were then shown: "{JOHNSON}"'
)


def chart(level: str) -> str:
    cats = CATEGORIES[level]
    shown = "; ".join(f"{c}: {p}" for c, p in zip(cats, PERCENTS, strict=True))
    return (
        f'Shown with the pie chart was the text "{CHART_TITLE}". The pie chart showed: '
        f'{shown}. You were then asked: "{Q4}" The options were the four categories '
        "shown in the pie chart."
    )


# What a block contributes to a LATER block's condition, once it is finished.
DONE = {
    "tv": (
        f'You were then shown: "{TV_DISPLAY}" and asked: "{Q5}" You were then asked to '
        "report the extent to which you agree or disagree with statements about your "
        "favorite TV character."
    ),
    "groups": (
        "You were then asked to what extent you think internet users, and residents of "
        "your state, form a group (rather than just a bunch of individuals)."
    ),
    "task": (
        "You were then asked to think about a time that you worked on a project or some "
        "type of task in a group, to what extent the group outcome was a success or a "
        "failure, and whether the outcome was due to your own individual efforts or due "
        "to teamwork."
    ),
    "lonely": (
        "You were then asked how often you feel that you lack companionship, how often "
        "you feel left out, and how often you feel isolated from others."
    ),
    "friends": (
        "You were then asked to what extent you are satisfied with your friendships and "
        "to what extent you think your friendships are strong."
    ),
    "life": "You were then asked how satisfied you are with your life as a whole these days.",
}
# What a block shows BEFORE its own scored items (its lead-in), where that lead-in
# is a separate screen rather than a grid stem (grid stems go in the question).
LEAD_IN = {
    "tv": f'You were then shown: "{TV_DISPLAY}" and asked: "{Q5}"',
    "task": f'You were then shown: "{TASK_DISPLAY}"',
}

ORDER = {
    # Questionnaire lines 36-39 (A-D) and the routing at 41-190 / 191-338.
    "attachment_first": ["tv", "groups", "task", "lonely", "friends", "life", "self"],
    "isolation_first": ["lonely", "friends", "life", "tv", "groups", "task", "self"],
}
ARMS = [  # D_VERS raw, condition_num, connection, order
    (1, 0, "isolated", "attachment_first"),
    (2, 1, "embedded", "attachment_first"),
    (3, 2, "isolated", "isolation_first"),
    (4, 3, "embedded", "isolation_first"),
]


def cell_text(level: str, order: str, block: str) -> str:
    seq = ORDER[order]
    parts = [chart(level)]
    parts += [DONE[b] for b in seq[: seq.index(block)]]
    if block in LEAD_IN:
        parts.append(LEAD_IN[block])
    return " ".join(parts)


def lit(lo: int, hi: int, lo_l: str, hi_l: str, mid: str | None = None) -> dict:
    s: dict = {"min": lo, "max": hi, "min_label": lo_l, "max_label": hi_l}
    if mid:
        s["mid_label"] = mid
    return s


AGREE5 = lit(1, 5, "Strongly disagree", "Strongly agree")  # mid omitted: see notes
GROUP7 = lit(1, 7, "Not at all a group", "Definitely a group")
SUCCESS7 = lit(
    1, 7, "Definitely a failure", "Definitely a success", "Neither a failure nor a success"
)
TEAM7 = lit(
    1, 7, "All due to your own individual efforts", "All due to teamwork",
    "Equally due to your own individual efforts and teamwork",
)  # fmt: skip
OFTEN3 = lit(1, 3, "Hardly ever", "Often", "Some of the time")
SATF5 = lit(1, 5, "Not at all satisfied", "Extremely satisfied", "Moderately satisfied")
STRONG5 = lit(1, 5, "Not at all strong", "Extremely strong", "Moderately strong")
LIFE_CD = lit(0, 10, "Totally dissatisfied", "Totally satisfied", "Moderately satisfied")
LIFE_AB = lit(1, 10, "Totally dissatisfied", "Totally satisfied")
TRUE5 = lit(1, 5, "Not at all true of me", "Extremely true of me", "Moderately true of me")


def outcomes() -> list[tuple[str, str, str, dict]]:
    """(var, block, question, scale) in task_num order."""
    out = [(v, "tv", f"{TV_STEM} {t}", AGREE5) for v, t in TV_ITEMS.items()]
    out += [(v, "groups", f"{GROUP_STEM} {t}", GROUP7) for v, t in GROUP_ITEMS.items()]
    out += [("Q22", "task", Q22, SUCCESS7), ("Q23", "task", Q23, TEAM7)]
    out += [(v, "lonely", f"{LONELY_STEM} {t}", OFTEN3) for v, t in LONELY_ITEMS.items()]
    out += [("Q27", "friends", f"{FRIEND_DISPLAY} {Q27}", SATF5)]
    out += [("Q28", "friends", f"{FRIEND_DISPLAY} {Q28}", STRONG5)]
    out += [("Q29", "life", Q29, LIFE_CD)]
    out += [(v, "self", f"{SELF_STEM} {t}", TRUE5) for v, t in SELF_ITEMS.items()]
    return out


Q29_RECODE_CD = {k: k - 1 for k in range(1, 12)}  # code 1 = "0 - Totally dissatisfied"
Q29_RECODE_AB = {k: k - 1 for k in range(2, 12)}  # 1-10 shown; code 1 (0) never used


def build() -> dict:
    outs = outcomes()
    q29_task = [v for v, *_ in outs].index("Q29")
    arms = []
    for raw, num, level, order in ARMS:
        items: dict[int, dict] = {}
        for task, (_v, block, _q, _s) in enumerate(outs):
            cell: dict = {"condition_text": cell_text(level, order, block)}
            if task == q29_task and order == "attachment_first":
                cell["scale"] = LIFE_AB
                cell["response_recode"] = Q29_RECODE_AB
            items[task] = cell
        arms.append(
            {
                "raw": raw,
                "condition_num": num,
                "factors": {"connection": level, "item_order": order},
                # Never rendered: every outcome's cell overrides it. It is the
                # last block's cell, the arm's whole history, so QC rule 5 can
                # see both factors in it (see notes, "ARM TEXT").
                "text": cell_text(level, order, "self"),
                "items": items,
            }
        )
    out_list = []
    for task, (v, _block, q, s) in enumerate(outs):
        o: dict = {"var": v, "task_num": task, "question": q, "scale": s}
        if v == "Q29":
            o["response_recode"] = Q29_RECODE_CD
        out_list.append(o)
    return {
        "study_id": "gh396",
        "source": "tess",
        "title": "Maintaining a Sense of Belonging among the Socially Isolated",
        "data_file": DERIVED.name,
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "notes": NOTES,
        "condition": {
            "source_var": "D_VERS",
            "factors": ["connection", "item_order"],
            "shared_context": SHARED,
            "arms": arms,
        },
        "outcomes": out_list,
        "response_recode": {k: k for k in range(1, 8)},
        "missing_codes": [-1, -2],
        "persona_map": {
            "age": "PPAGE",
            "gender": "PPGENDER",
            "education": "PPEDUCAT",
            "ethnicity": "PPETHM",
            "income": "PPINCIMP",
            "region": "PPREG4",
            "household_size": "PPHHSIZE",
            "housing_type": "PPHOUSE",
            "urban_rural": "PPMSACAT",
            "internet_access": "PPNET",
        },
    }


LICENCE = (
    "none stated on the OSF deposit (checked via the OSF API, 2026-10-02 and again "
    '2026-10-10: registration gh396 and its child components m29w4 "Data" and 8jrv6 '
    '"Materials and Methods" carry no licence). TESS has since suspended operations '
    "and its site states no reuse terms, so there is no explicit grant of "
    "redistribution rights for this deposit, and none should be assumed."
)

NOTES = """\
TESS 41 (Megan L. Knowles, Northwestern; Knowledge Networks, project K0835),
fielded 26 May - 1 Jun 2005 (SVY_DATE), N=412, about 100 per version as
requested (D_VERS 1-4: 103/103/103/103).


SOURCES AND PROVENANCE

  Q  = tess41_knowles_final.doc, the FIELDED Knowledge Networks programming
       questionnaire (footer "FILENAME tess41_knowles_v4.doc", last saved
       5/26/2005 1:30 PM, the first day of fieldwork). OSF registration gh396,
       child component 8jrv6 "Materials and Methods"
       (https://osf.io/download/st4j7/, 255,488 bytes, sha256
       1c381a0993fbae717d552baed2400003e4c84ae878c7a763eac96477950533ab),
       fetched 2026-10-10 into data/raw/gh396/quex/ and converted with macOS
       textutil to tess41_knowles_final.txt. Line numbers below are 1-based
       into that .txt with blank lines removed (grep -v '^\\s*$').
  OE = tess41_knowles_OE_CLIENT.xls, the open ends (Q5, favourite TV
       character), component m29w4 "Data" (https://osf.io/download/a4bgm/,
       sha256 5748dc8d4aced3707a14211cad1023b533c40217aaffc034c683076ae31670ff).
       Used ONLY to decide who is eligible for Q6-Q19 (see "WHO IS ASKED
       ABOUT A TV CHARACTER"); no open-ended text goes into any row.
  Data = tess41_knowles_CLIENT.sav (412 x 62), component m29w4
       (https://osf.io/download/x9mdg/, sha256
       0eaa612059328e36178cc0cdfe0c86a3cab3783f8a9218b0a0d900f283be1cf3).
  Built from gh396-derived.sav, written by `scripts/gen_gh396.py --write`:
       the deposit's .sav with Q6-Q19 blanked for 121 respondents and nothing
       else changed (`--check` asserts this cell by cell).
  No proposal is in the deposit. The KN methodology PDF (sufm4) was not used.

  Q is the fielded version: its variable names and every option list match
  the .sav (Q4A/C and Q4B/D as the two category sets, Q6-Q31 items and
  scales), with three disagreements noted below (Q4D, Q20 stem, Q29).


THE DESIGN (Q 33-40)

  "THE STUDY IS A 2 (SUBJECTIVE SOCIAL CONNECTION) X 2 (ITEM ORDER)
  BETWEEN-SUBJECTS DESIGN". D_VERS ("DATA-ONLY: Version shown"):
    1 = A  isolated, attachment-enhancing questions first   -> condition 0
    2 = B  embedded, attachment-enhancing questions first   -> condition 1
    3 = C  isolated, subjective isolation questions first   -> condition 2
    4 = D  embedded, subjective isolation questions first   -> condition 3

  Everyone answers Q1-Q3 (live alone; waking hours alone; number of close
  friends), then sees a display citing "Johnson (1999)" and a pie chart of
  close-friend categories, then Q4 asks which category applies to them. The
  pie chart is the manipulation: its SHARES are identical in every version
  (5% / 14% / 49% / 32%), and only the friend-count boundaries of the four
  categories differ. A and C label "Socially Isolated (0-5 close friends)" ...
  "Socially Embedded (16+ close friends)"; B and D label "Socially Isolated (0
  close friends)" ... "Socially Embedded (3+ close friends)". So a respondent
  with the median 3 friends reads that they sit in the 5% "isolated" slice (A,
  C) or the 32% "embedded" slice (B, D). Q4's tabulation confirms it took:
  A/C 134 of 206 chose "Socially Isolated" (1) and 12 "Socially Embedded"
  (4); B/D 17 chose 1 and 113 chose 4.

  The order factor: A/B go TV character (Q5, Q6-19) -> groups (Q20-21) ->
  past group task (Q22-23) -> loneliness (Q24-26) -> friendships (Q27-28) ->
  life satisfaction (Q29) -> self (Q30-31) (Q 41-190). C/D go loneliness ->
  friendships -> life satisfaction -> TV -> groups -> task -> self (Q
  191-338). The order is fixed by the version, so it is RECORDED, not
  inferred. Routing confirmed in the data: every respondent in A/C holds Q4AC
  and no Q4BD, and the reverse for B/D (103/103 each).

  Q4D: Q 214 reads "SHOW THIS DISPLAY SCREEN AND Q4C FOR GROUP D", a typo:
  the item that follows is headed Q4D with the 0/1/2/3+ options, and all 103
  group D respondents answered Q4BD, none Q4AC. The data settles it.


OUTCOMES (26; Q1-Q4 and Q5 excluded)

  Q6-Q19  agreement with 14 statements about the favourite TV character,
          1 Strongly disagree - 5 Strongly agree (Q 82-111).
  Q20-21  do internet users / residents of your state form a group, 1-7.
  Q22     group task outcome, 1 Definitely a failure - 7 Definitely a success.
  Q23     own efforts vs teamwork, 1-7.
  Q24-26  how often lack companionship / left out / isolated, 1-3.
  Q27-28  satisfaction with / strength of friendships, 1-5.
  Q29     life satisfaction, 0-10 (C/D) or 1-10 (A/B), see below.
  Q30-31  "I have high self-esteem." / "I have a strong need to belong.",
          1-5.
  Grid stems are carried in each item's question, word-for-word from Q. The
  friendship display (Q 159) is a one-sentence lead-in printed immediately
  above Q27 and Q28, so it is carried in their question too.

  Excluded: Q1-Q3 are asked before the manipulation and are the input to it,
  not a response to it; they are also not used as persona, because the
  outcomes are about friendship and isolation (the domain rule). Q4 is the
  manipulation check: its answer is derivable from Q3 plus the condition
  text (CONVENTIONS, "Attention and recall checks are not outcomes"); cost
  412 rows. Q5 is open text.

  Q20 stem: the .sav label reads "For the next two questions"; Q (both
  versions, 113 and 292) reads "For the next question". Q is the authority
  and is used.

  Q6-Q19 midpoint: Q prints "Neither agree not disagree" (82-91, both
  versions); the .sav label reads "nor". Words are never normalised, and
  which spelling respondents saw is not determinable from the deposit, so no
  mid_label is given for these 14 items (endpoints only).

  Q29: Q prints the scale as "12345678910" for groups A/B (Q 176) and
  "012345678910" for C/D (Q 255), under the same three labels. The .sav has
  ONE variable with 11 codes, 1 = "0 - Totally dissatisfied" ... 11 = "10 -
  Totally satisfied". A/B use code 11 (25 respondents), so if they saw 1-10
  it was coded 2-11, and value = code - 1 holds either way; no A/B
  respondent used code 1 (C/D: 1). Built per Q: C/D carry 0-10 with mid 5
  "Moderately satisfied"; A/B carry 1-10 with endpoint labels only. The A/B
  table does print "Moderately satisfied" over its 5 column, but a 1-10
  scale has no middle code, and Scale.mid_label names only the midpoint of
  an odd-length scale (the validator refuses it on 1-10); writing it into
  the question instead is the free-text drift Scale.mid_label exists to
  prevent. So the A/B instruction omits the mid label, and this note
  records it. Then: recode code k -> k-1, code 1 not in the A/B map
  (it never occurs there). If the A/B screen actually showed 0-10 (the
  doc's A/B table losing a cell), the only falsehood is the A/B instruction's
  lower bound, and no A/B row has a response it contradicts.

  .sav vs .doc: the .sav labels differ from Q in three places (Q20 "For the
  next two questions" vs "next question"; "Neither agree nor disagree" vs
  Q's "not"; ONE 0-10 Q29 variable where Q prints 1-10 for A/B). So the
  programmed survey may have been edited after this .doc was saved
  (5/26/2005 1:30 PM, fieldwork day one). Q is still the only wording
  source in the deposit and is followed throughout; the three places are
  where it is least certain to match the screen.


WHO IS ASKED ABOUT A TV CHARACTER (Q6-Q19 eligibility)

  Q6-Q19 show the respondent's own Q5 answer on each screen ("[SHOW TEXT
  TYPED IN Q5 ON EACH SCREEN.]"), and every item presupposes that character.
  11 respondents left Q5 blank ("_na_" in the open ends, CASEIDs 9, 61, 64,
  73, 81, 85, 254, 271, 275, 361, 385) and so saw the ALTERNATE stem (Q
  85-86); about a hundred more typed that they have no favourite. Their
  answers read like non-answers: 34.7% straight-lined the midpoint (3) on
  all 14 items, against 3.1% of everyone else. Ruled (coordinator and
  checker, 2026-10-10): drop the Q6-Q19 rows of every respondent whose Q5 is
  blank or an explicit "none". Their Q20-Q31 rows stay.

  The list is HAND-REVIEWED, not a keyword match: every one of the 412 Q5
  answers was read. KEEP anyone whose answer identifies at least one
  specific character, person, cast or programme, however hedged ("Don't
  really have one. The one I liked best was Lenny on Law & Order"; "the
  cast of sex in the city reruns"; "The cast of 'Lost', but no particular
  character"; a show title or channel; an unrecognised name-like string).
  DROP 121 respondents, by reason (CASEIDs in NO_CHARACTER in the
  generator): blank 11; says none / no favourite / doesn't watch 97; don't
  know or a non-answer ("?", "0", "donotno") 8; answers without
  identifying anyone ("i have many", "everyone who can make laugh", news
  casters in general, a list of genres, "mexican") 5. Cost: 1,550 rows
  (Q6-Q19 answers held by those 121). The open ends decide eligibility
  only; none of their text reaches a row. With the 11 blanks dropped, every
  remaining Q6-Q19 row saw the main stem, which is the one rendered.


THE CONDITION: WORD-FOR-WORD VS NARRATION

  Each row's condition is: what everyone was shown or asked up to the
  manipulation (shared_context), the arm's chart and Q4, then each block the
  respondent had ALREADY completed in that arm's order, then the outcome
  block's own lead-in screen where it has one (the TV display and Q5; the
  group-task display). Later blocks are never named, and earlier answers are
  narrated as asked, never as given (CONVENTIONS, "Repeated measures within
  one block"; the order is fixed by D_VERS). Items earlier in the SAME block
  (e.g. Q22 before Q23) are not narrated: the block is the unit.

  Word-for-word from Q: the intro display (42), Q1, Q2, Q3 (45-52), the
  Johnson display (56), the text "A Sample of 1,250 Respondents
  (Johnson, 1999)" (343-346, one Word text box beside each chart), the four category
  labels per version (= Q4 options, 60-63 / 71-74), Q4's stem (59), the TV
  display and Q5 (77-79), the group-task display (127).

  The chart's percentages are not in Q's text layer. They come from the
  embedded MSGraph objects in the .doc: each one's data sheet holds 5, 15,
  55, 35 under the four category labels, and each one's cached rendering
  (the EMF the respondent-facing chart was drawn from) carries the data
  labels "49%", "14%", "5%", "32%" (Excel rounding 55/110 down to 49% so
  they sum to 100). Pairing by share: Isolated 5%, Weakly 14%, Moderately
  49%, Embedded 32%. `scripts/gen_gh396.py --check` re-derives all of this
  from the .doc and fails if any pairing changes.

  ADDED words (description, not transcription): "You were shown:", "You were
  then asked:", "You were then shown:", "and asked:", "Shown with the pie chart
  was the text "...". The pie chart showed:" (the title is a separate Word
  text box placed with each chart, not part of the chart object, so the
  row says only that it was shown with it), the "label: N%" layout of the chart, "The options were the
  four categories shown in the pie chart.", and one narration per completed
  block:
    TV:      'You were then shown: "<display>" and asked: "<Q5>" You were then
             asked to report the extent to which you agree or disagree with
             statements about your favorite TV character.'
    groups:  "You were then asked to what extent you think internet users,
             and residents of your state, form a group (rather than just a
             bunch of individuals)."
    task:    "You were then asked to think about a time that you worked on a
             project or some type of task in a group, to what extent the group
             outcome was a success or a failure, and whether the outcome was
             due to your own individual efforts or due to teamwork."
    lonely:  "You were then asked how often you feel that you lack
             companionship, how often you feel left out, and how often you
             feel isolated from others."
    friends: "You were then asked to what extent you are satisfied with your
             friendships and to what extent you think your friendships are
             strong."
    life:    "You were then asked how satisfied you are with your life as a
             whole these days."
  Each narration reuses the instrument's own phrases, reflowed into reported
  speech; each is true for everyone in the arm. The generator holds them in
  one place (DONE, LEAD_IN) so every cell uses the same words.

  ARM TEXT: every (arm, outcome) cell declares its own condition_text, so
  Arm.text is never rendered. It is set to the last block's cell (the arm's
  whole history) so that QC rule 5 can see both factors in it.


RISKIEST JUDGEMENT

  Rendering a pie chart as text. The chart is the manipulation, and its
  numbers are not in the questionnaire's prose; they were recovered from the
  embedded chart objects (data sheet and cached rendering agree). That is
  the instrument's own content, not an inference, but it rests on the
  fielded screen having shown the chart as the .doc embeds it, data labels
  included. If the KN screen omitted the percentage labels, the "N%" figures
  would be words no respondent read. (Contrast IP 9.11, dropped because its
  graph's figures are in no part of the instrument.) Second: the Q29 A/B
  scale (above).


PERSONA

  Standard KN profile: age PPAGE, gender PPGENDER, education PPEDUCAT,
  ethnicity PPETHM, income PPINCIMP, region PPREG4, household_size PPHHSIZE,
  housing_type PPHOUSE, urban_rural PPMSACAT, internet_access PPNET.
  recipe_prep's Jev pass: assignment D_VERS REVIEW (conf 0.69, runner-up
  NONE_OF_THESE 0.20), accepted: Q 40 asks for exactly this data-only
  variable and it splits 103 x 4. region PPREG4 REVIEW (0.69, runner-up
  PPREG9 0.23), accepted: the four-region field is the one every other KN
  recipe here uses. Value labels: 281 asked, 0 disagreements with the regex;
  -1 REFUSED and -2 Not asked are dropped (none occur on an outcome; item
  non-response here is system-missing, 203 cells).
  LEFT OUT because their labels are not in the shared crosswalk (QC rule
  14): marital_status PPMARIT ("Single (never married)"), employment PPWORK
  ("I am a homemaker", "I am an owner/partner in small business, prof
  practice, farm", "I am disabled"), housing_ownership PPRENT ("Own",
  "Rent", "Do not pay for housing"). The fix is a crosswalk entry for the
  2005 KN spellings, not an edit here.


COUNTS

  412 respondents x 26 outcomes = 10,712 cells; 203 system-missing and
  1,550 no-character Q6-Q19 answers dropped; 8,959 rows. Per condition 0-3
  and per task: see the QC report.


VERIFICATION

  Not in SocSci210 (catalogue: no), so no answer key. No published table for
  this deposit was found: Knowles & Gardner (2008, PSPB, "Benefits of
  membership") and Gardner & Knowles (2008, Social Cognition) report a
  nationally representative sample but no cell table we could reach. So
  there is no independent numeric reference; verified instead by
  re-deriving every row from the .sav with a separate script (condition,
  task, response, persona) and by reading rows against Q."""


class _Dumper(yaml.SafeDumper):
    pass


def _str(dumper: yaml.SafeDumper, s: str) -> yaml.ScalarNode:
    if "\n" in s:
        return dumper.represent_scalar("tag:yaml.org,2002:str", s, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", s)


_Dumper.add_representer(str, _str)

HEADER = (
    "# GENERATED by scripts/gen_gh396.py from the fielded questionnaire\n"
    "# (data/raw/gh396/quex/tess41_knowles_final.doc). Edit the generator, not this file.\n"
)


def render() -> str:
    body = yaml.dump(build(), Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=88)
    return HEADER + body


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def write_derived() -> None:
    """The deposit's .sav with Q6-Q19 blanked for NO_CHARACTER_IDS, nothing else."""
    import pyreadstat

    df, meta = pyreadstat.read_sav(str(SAV))
    df.loc[df["CASEID"].isin(NO_CHARACTER_IDS), TV_VARS] = float("nan")
    pyreadstat.write_sav(
        df,
        str(DERIVED),
        column_labels=dict(zip(meta.column_names, meta.column_labels, strict=True)),
        variable_value_labels=meta.variable_value_labels,
    )
    print(f"wrote {DERIVED} ({len(NO_CHARACTER_IDS)} respondents' Q6-Q19 blanked)")


def check_derived() -> int:
    """Derived file = deposit except Q6-Q19 of exactly NO_CHARACTER_IDS; blanks = OE '_na_'."""
    import pyreadstat
    import xlrd  # type: ignore[import-untyped]

    bad = 0
    if len(set(NO_CHARACTER_IDS)) != len(NO_CHARACTER_IDS) or len(NO_CHARACTER_IDS) != 121:
        print(f"NO_CHARACTER: {len(NO_CHARACTER_IDS)} ids (expected 121, no duplicates)")
        bad += 1
    sheet = xlrd.open_workbook(str(OE)).sheet_by_index(0)
    oe = {int(sheet.cell_value(r, 0)): sheet.cell_value(r, 1) for r in range(1, sheet.nrows)}
    na = sorted(c for c, v in oe.items() if str(v).strip() == "_na_")
    if na != sorted(NO_CHARACTER["blank"]):
        print(f"blank Q5 in the open-ends file {na} != declared {NO_CHARACTER['blank']}")
        bad += 1
    if sorted(oe) != list(range(1, 413)):
        print("open-ends file does not hold CASEID 1-412 once each")
        bad += 1
    a, _ = pyreadstat.read_sav(str(SAV))
    b, _ = pyreadstat.read_sav(str(DERIVED))
    if list(a.columns) != list(b.columns) or not (a["CASEID"].values == b["CASEID"].values).all():
        print("derived file's columns or CASEIDs differ from the deposit")
        return bad + 1
    flagged = a["CASEID"].isin(NO_CHARACTER_IDS).values
    other = [c for c in a.columns if c not in TV_VARS]
    if not a[other].equals(b[other]) or not a.loc[~flagged, TV_VARS].equals(
        b.loc[~flagged, TV_VARS]
    ):
        print("derived file differs from the deposit outside the blanked cells")
        bad += 1
    if not b.loc[flagged, TV_VARS].isna().all().all():
        print("a flagged respondent still holds a Q6-Q19 answer")
        bad += 1
    blanked = int((a.loc[flagged, TV_VARS].notna()).sum().sum())
    print(f"derived: {int(flagged.sum())} respondents, {blanked} answered Q6-Q19 cells blanked")
    if int(flagged.sum()) != 121 or blanked != EXPECTED_BLANKED:
        print(f"expected 121 respondents and {EXPECTED_BLANKED} cells")
        bad += 1
    return bad


EXPECTED_BLANKED = 1550  # answered Q6-Q19 cells of the 121; computed, then pinned


def check() -> int:
    bad = check_derived()
    quex = _norm(QUEX_TXT.read_text())
    for frag in WORD_FOR_WORD:
        # Legend labels carry runs of spaces in the chart; whitespace is typography.
        if _norm(frag) not in quex and frag not in [c for cs in CATEGORIES.values() for c in cs]:
            print(f"NOT IN QUESTIONNAIRE: {frag[:70]!r}")
            bad += 1
    # Categories: Q4 options in the text layer.
    for cats in CATEGORIES.values():
        for c in cats:
            label, rng = c.split(" (")
            if not re.search(re.escape(label) + r"\s*\(" + re.escape(rng), quex):
                print(f"category not in questionnaire: {c}")
                bad += 1
    # Chart data and rendered labels from the embedded objects.
    import olefile  # type: ignore[import-not-found]

    o = olefile.OleFileIO(str(QUEX_DOC))
    objs = sorted({e[1] for e in o.listdir() if e[0] == "ObjectPool" and len(e) == 3})
    seen_levels = []
    for k in objs:
        wb = o.openstream(["ObjectPool", k, "Workbook"]).read()
        vals, labels, i = [], [], 0
        while i + 4 <= len(wb):
            rt, ln = struct.unpack("<HH", wb[i : i + 4])
            d = wb[i + 4 : i + 4 + ln]
            if rt == 0x0003:  # BIFF NUMBER (MSGraph)
                vals.append(struct.unpack("<d", d[7:15])[0])
            if rt == 0x0004:  # BIFF LABEL
                n = struct.unpack("<H", d[6:8])[0]
                labels.append(_norm(d[9 : 9 + n].decode("latin-1")))
            i += 4 + ln
        eprint = next(
            e for e in o.listdir() if len(e) == 3 and e[1] == k and e[2].endswith("EPRINT")
        )
        emf, texts, i = o.openstream(eprint).read(), [], 0
        while i + 8 <= len(emf):
            t, sz = struct.unpack("<II", emf[i : i + 8])
            if sz == 0:
                break
            if t == 84:  # EMR_EXTTEXTOUTW
                r = emf[i : i + sz]
                n, off = struct.unpack("<II", r[44:52])
                texts.append(r[off : off + 2 * n].decode("utf-16le"))
            i += sz
        level = next(lv for lv, cats in CATEGORIES.items() if _norm(cats[0]) == labels[0])
        seen_levels.append(level)
        if labels != [_norm(c) for c in CATEGORIES[level]]:
            print(f"{k}: chart labels {labels} differ from Q4 options")
            bad += 1
        total = sum(vals)
        derived = [f"{round(100 * v / total)}%" for v in vals]
        shown = [t for t in texts if t.endswith("%")]
        # Rendered labels are drawn slice by slice, not in category order, and Excel
        # rounds to sum to 100 (55/110 = 50.0 is drawn 49%): match each category to
        # the rendered label nearest its exact share, and require a bijection.
        exact = [100 * v / total for v in vals]
        pairing = [min(shown, key=lambda s, e=e: abs(float(s[:-1]) - e)) for e in exact]
        if sorted(pairing) != sorted(shown) or pairing != PERCENTS:
            print(f"{k}: data {vals} -> {derived}, rendered {shown}, paired {pairing}")
            bad += 1
        print(f"{k}: {level:9s} data={vals} rendered={shown} -> {pairing}")
    if sorted(seen_levels) != ["embedded", "embedded", "isolated", "isolated"]:
        print(f"expected two charts per level, got {seen_levels}")
        bad += 1
    if RECIPE.read_text() != render():
        print("recipes/gh396.yaml is not what the generator derives")
        bad += 1
    print("OK" if not bad else f"{bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write:
        RECIPE.write_text(render())
        print(f"wrote {RECIPE}")
        write_derived()
    if a.check:
        sys.exit(check())
