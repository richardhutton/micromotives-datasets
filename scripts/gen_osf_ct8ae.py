#!/usr/bin/env python3
"""Write recipes/osf_ct8ae_maxdiff.yaml: Schwartz life values, best-worst (MaxDiff).

Liang, Glover & Hawkins, "Time after time, the Best Worst Scaling method is more
reliable than ranking", PsyArXiv/OSF preprint r5dyu (posted 2 Oct 2025; the PDF's own
title reads "Simply, the Best-Worst Scaling method is more reliable than ranking").
This is its Experiment 1b. Published as Liang, Glover & Hawkins (2026), "Time after
time, the best-worst scaling method is more reliable than ranking", Behavior Research
Methods 58(10), doi:10.3758/s13428-026-03167-x (CC BY; read via Europe PMC
PMC13534160). Data: OSF node ct8ae. On 16 Nov 2026 it was private with no licence,
reached through the preprint's view-only link, and rich approved its use; Guy
Hawkins was emailed that day. On 17 Nov 2026 Garston Liang made the node public, and
it now carries CC BY 4.0 (OSF API: node license 563c1cf8..., "CC-By Attribution 4.0
International", read 17 Nov 2026). Downloaded
16 Nov 2026 to data/raw/osf_ct8ae/ (every file's md5 matched OSF's):
`data/raw_data/bws_retest/bws_retest_n100.csv` (a QuestionPro export, not
Qualtrics: 112 x 996 with two header rows; md5 0f280771...), the Prolific export
`data/demos/experiment1_bws_demos.csv` (there is no `bws_demos.csv`), the authors'
processed R objects and `analyses/data_preprocessing.R` (read, never run).
Fieldwork 24-25 Oct 2023, on Prolific, adults whose first language is English
(UK 55 of the 100, then Canada, Australia, South Africa and others).

The third MaxDiff in the corpus, built as `scripts/gen_zenodo18547379.py` and
`scripts/gen_figshare_32935409.py` build theirs. Every judgement is here:

* PRIVACY. The export carries `IP Address` and `Respondent Email` (and `Email
  List`, `Country Code` and `Region`, which QuestionPro derives from the IP). They
  are blanked in every row the moment the file is read (`read_export`), before
  anything else touches it, and never reach the derived file, the recipe or a row.
  The Prolific ID is used only to join the demographics and is not carried;
  `participant_id` is the 1-based data row of the export.

* THE DESIGN. Ten Schwartz values; eleven sets of 5 or 6 (five sets of 5, six of 6;
  each value six times, each pair three times: Lee et al. 2008's design, preprint
  p. 9). Each set is one screen: "Which is the MOST and LEAST important factor to
  you as a guiding principle in YOUR life?" with a "Most Important" and a "Least
  Important" button beside each value (Figure 1). Values were labelled as
  DIMENSIONS ("Benevolence") or as ITEMS ("Helpful, honest, forgiving"),
  randomised between people. Everyone did the eleven screens twice ("occasions");
  `condition` names the two label sets in occasion order: dimension-dimension 34,
  item-item 33, item-dimension 16, dimension-item 17. The export holds four
  branches of two occasions (8 x 11 questions); each person answered exactly the
  two segments their `condition` names (checked). Kept: the 100 with status
  Completed that are not `test_response` (the paper's N = 100); 5 Started, 2
  Terminated and 5 other test rows are left out. All 100 join the Prolific export.

* MOST OR LEAST. Each question is two blocks of one column per value, holding 1
  where that button was pressed. The second block's header is "Most Important
  Which is ..."; the first has no prefix and is "Least Important" (the authors'
  R script codes it "least"). Confirmed by the paper's own numbers (below): coded
  the other way round, Power would come top. Every screen has exactly one of each
  and they always differ (checked, 4,400 screens).

* ON-SCREEN ORDER, the riskiest judgement. Not recorded per person: the export
  has no display-order column. The published paper settles fixed versus shuffled:
  "The 11 subsets were presented in a randomized order, and the individual options
  within each set were not randomized." So each set had ONE fixed order, but which
  one is still not recorded: the export's column order is not a proven screen
  order, because Figure 1
  shows set 1 with item labels as Successful, Helpful, Clean, Devout, Protecting;
  the export holds Successful, Protecting, Helpful, Devout, Clean (the screenshot
  happens to be alphabetical by dimension name, so it may come from another build
  of the survey). Picks show no significant position effect under the export's
  order (conditional logit with item effects, LR test, most p = 0.62, least p =
  0.11). So the fixed order itself cannot be established from the deposit. By
  rich's ruling of 16 Nov 2026 on this study (docs/CONVENTIONS.md, "Choice sets
  whose on-screen order was randomised and not recorded", second paragraph) the
  row lists the values in the data file's order and adds one clause of ours,
  word-for-word: "(the options are listed in the data file's order; the order on
  screen was not recorded)". The answer is coded to that list, and each value's
  identity is kept as factors so training can re-order and remap: `label_type`
  (dimensions or items) and `options`, the values' slugs in listed order joined by
  "|" (answer k is the k-th). Not one factor per slot (`item_1` .. `item_6`) as the
  two precedents have: with 22 arms no two differ in one slot alone, so QC rule 5
  warns that it cannot test such a factor ("nested, not crossed"), and a build here
  must pass QC without warnings. `options` and `label_type` both have minimal pairs
  and are tested.

* FIRST OCCASION ONLY. The second occasion is not built. Its respondents had just
  answered the same eleven sets, minutes before (in the crossed conditions, under
  the other labels), and a row cannot say so without citing its place in a
  sequence, which it may not (docs/CONVENTIONS.md, "Sequence signposting"). Built
  beside the first, it would also give the same persona the same condition and
  outcome with a different answer as a target 1 time in 4 or so. The second
  occasion is used instead for the independent reference: the paper's test-retest
  agreement is reproduced from it (tests). The first occasion has dimension labels
  for 51 people (segments 1 and 7) and item labels for 49 (segments 3 and 5).

* CONDITION. In screen order of the survey: the welcome's two sentences about
  values (its "Welcome!" and "please click next ..." are navigation and dropped),
  the definitions page, one value per line (its "Please click next to proceed to
  the survey." dropped), the task instructions, the stem, the values of the set one
  per line, then the clause above. Typography only: non-breaking spaces as spaces,
  and the definitions page's run-together sentences ("self-indulgence.Stimulation:")
  split one per line. The definitions page reads "self-indulgence" and the item
  label "self-indulgent"; each is kept as shown. Sequence words dropped: "Step 1
  of 1" (Figure 1), the "second phase" page. One arm per (label type, ordered set):
  22 arms (11 sets x 2 label types; the two branches with the same label type
  list each set in the same order, checked).

* A SCRIPT ERROR ON SCREEN. Set 5 with ITEM labels asked "Which is the MOST and
  MOST important factor to you as a guiding principle in YOUR life?" (the export's
  question text, in all four item-label segments, so every person shown that set
  with item labels saw it; the dimension-label set 5 reads correctly). Kept and
  flagged per docs/CONVENTIONS.md, "A script error on screen": the words are
  rendered as shown, in the condition and in both outcome questions, followed by
  one clause of ours, '(this screen's question read "MOST and MOST" in the
  original survey)'. Its two buttons are taken to be "Most Important" and "Least
  Important" as on every other screen: the export's columns for it are named and
  coded exactly as theirs. That arm is not a clean contrast with its
  dimension-label counterpart (49 people, 98 rows).

* OUTCOMES. Two per set, task_num 2(t-1) + 0/1, as the precedents: the stem, then
  'Report only the option you chose as "Most Important".' (or "Least Important"),
  then '1 means "<value 1>"; 2 means ...' (our words). The answer is the value's
  place in the listed order, 1-5 or 1-6; each outcome's scale matches its set's
  size (set t has the same size for everyone). Slot 6 of a five-value set is coded
  0 in the derived file.

* PERSONA. Prolific's own records, as `scripts/gen_a4y7s_study2.py` and
  `scripts/gen_rhfd6.py` map them: age, sex, ethnicity (`Ethnicity simplified`,
  crosswalk scheme uk_ons_five_group_short), employment (scheme uk_prolific_rhfd6;
  the Student and Unemployed mappings are untouched), student status, country of
  birth, nationality, and country of residence (mapped here because the sample is
  NOT all British). Jev (scripts/recipe_prep.py's report functions, 16 Nov 2026,
  column names and category labels only, no rows) found Age (0.50, REVIEW against
  NONE_OF_THESE 0.45: accepted, the column is Prolific's age in years), Sex 0.99,
  Ethnicity simplified 1.00, Employment status 1.00; and called DATA_EXPIRED,
  CONSENT_REVOKED and "Prefer not to say" non-answers everywhere (0.88-1.00, the
  regex disagreeing on DATA_EXPIRED and CONSENT_REVOKED; Jev is right). One REVIEW,
  CONSENT_REVOKED on student status (0.42 vs answer 0.38), is moot: no kept person
  has CONSENT_REVOKED anywhere. Non-answers are blanked in the derived file. The
  export's "Not in paid work (e.g. homemaker', 'retired or disabled)" has two stray
  quote marks; typography, removed. `condition` (Jev 0.72, REVIEW) is the label
  assignment; accepted because every person answered exactly the segments it names.
  Not mapped: `Language` (English for everyone; a screener), submission metadata.

* INDEPENDENT REFERENCE. The paper's Exp. 1b numbers, from both occasions as it
  pools them: Benevolence 0.375 and Power -0.46 mean BWS score (reproduced 0.375,
  -0.461), its Table 1 top five in order (Benevolence, Self-direction, Achievement,
  Security, Universalism; reproduced), and mean test-retest Kendall's tau-b 0.82
  with the same labels and 0.41 with changed labels (reproduced 0.819, 0.405; the
  pooled 0.69 comes out 0.682). Pinned in tests/test_gen_osf_ct8ae.py. A score
  cannot see display order (ledger: EFXNLX); it checks the picks and their
  direction.

* AUTHORS' LABEL SWAP. `data_preprocessing.R` maps "devout, accepting my portion in
  life, humble" to conformity and "politeness, obedient, honouring parents and
  elders" to tradition, the reverse of the definitions page and the paper's Table 1.
  Their item-label scores for those two values are therefore swapped in their R
  objects. Not used here: values are coded from the definitions page.

* NOT BUILT. The second occasion (above). The ranking experiment (1a,
  `rank_retest.csv`) is a drag-to-order list: a ten-way ranking is not this
  recipe's row design and has no precedent here; its displayed order was
  randomised and not recorded. Experiment 2 has no raw export in the node, only the
  authors' processed R object.

    uv run python scripts/gen_osf_ct8ae.py           # write derived CSV + recipe
    uv run python scripts/gen_osf_ct8ae.py --check   # exit 1 if either differs
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
STUDY = "osf_ct8ae"
RAW = REPO / "data" / "raw" / STUDY
EXPORT = RAW / "data" / "raw_data" / "bws_retest" / "bws_retest_n100.csv"
DEMOS = RAW / "data" / "demos" / "experiment1_bws_demos.csv"
DERIVED = RAW / "maxdiff_coded.csv"
RECIPE = REPO / "recipes" / f"{STUDY}_maxdiff.yaml"

N_SETS = 11
N_SLOTS = 6
N_KEPT = 100
MOST, LEAST = "Most Important", "Least Important"
CLAUSE = "(the options are listed in the data file's order; the order on screen was not recorded)"

# Identifying columns, blanked on read. The last two QuestionPro derives from the IP.
DROP = ("IP Address", "Respondent Email", "Email List", "Country Code", "Region")
PROLIFIC_COL = 18  # "Please input your Prolific ID."; used to join, never carried

# Header text word-for-word (non-breaking spaces as spaces), checked in `instrument()`.
WELCOME = (
    "In this study, you will be asked to answer questions about values. Values are the "
    "things in life that matter most to you."
)
INSTRUCTIONS = (
    "In the following task, you will be asked to make some choices about the MOST and "
    "LEAST important values to you. You will make a number of these choices using "
    "different options."
)
STEM = "Which is the MOST and LEAST important factor to you as a guiding principle in YOUR life?"
# Set 5 with item labels (all four item-label segments, so everyone shown it) asked
# this instead: a script error on screen, kept and flagged (docs/CONVENTIONS.md).
STEM_ERROR = STEM.replace("MOST and LEAST", "MOST and MOST")
ERROR_AT = (2, 5)  # (label type, set)
ERROR_CLAUSE = '(this screen\'s question read "MOST and MOST" in the original survey)'

# code: (dimension label, item label, definitions-page line, slug). Codes follow the
# definitions page's order; labels are the export's second header row word-for-word.
VALUES: dict[int, tuple[str, str, str, str]] = {
    1: (
        "Power",
        "Social power, authority, wealth",
        "Power: Social power, authority, wealth.",
        "power",
    ),
    2: (
        "Achievement",
        "Successful, capable, ambitious",
        "Achievement: Successful, capable, ambitious.",
        "achievement",
    ),
    3: (
        "Hedonism",
        "Pleasure, enjoying life, self-indulgent",
        "Hedonism: Pleasure, enjoying life, self-indulgence.",
        "hedonism",
    ),
    4: (
        "Stimulation",
        "Daring, a varied life, an exciting life",
        "Stimulation: Daring, a varied life, an exciting life.",
        "stimulation",
    ),
    5: (
        "Self-Direction",
        "Creativity, curious, freedom",
        "Self-Direction: Creativity, curious, freedom.",
        "self_direction",
    ),
    6: (
        "Universalism",
        "Protecting the environment, a world of beauty, unity with nature",
        "Universalism: Protecting the environment, a world of beauty, unity with nature.",
        "universalism",
    ),
    7: (
        "Benevolence",
        "Helpful, honest, forgiving",
        "Benevolence: Helpful, honest, forgiving.",
        "benevolence",
    ),
    8: (
        "Tradition",
        "Devout, accepting my portion in life, humble",
        "Tradition: Devout, accepting my portion in life, humble.",
        "tradition",
    ),
    9: (
        "Conformity",
        "Politeness, obedient, honouring parents and elders",
        "Conformity: Politeness, obedient, honouring parents and elders.",
        "conformity",
    ),
    10: (
        "Security",
        "Clean, national security, social order",
        "Security: Clean, national security, social order.",
        "security",
    ),
}
LABEL_TYPES = {1: "dimensions", 2: "items"}
OPTION_SEP = "|"
# Segment (1-8, eleven questions each) -> label type shown, and condition -> its two
# segments in occasion order. Read from the export's own headers; checked in derive().
SEGMENT_LABEL = {1: 1, 2: 1, 3: 2, 4: 2, 5: 2, 6: 1, 7: 1, 8: 2}
SEGMENTS = {
    "dimension-dimension": (1, 2),
    "item-item": (3, 4),
    "item-dimension": (5, 6),
    "dimension-item": (7, 8),
}

PERSONA = {
    "age": "Age",
    "sex": "Sex",
    "ethnicity": "Ethnicity simplified",
    "employment": "Employment status",
    "student_status": "Student status",
    "country_of_birth": "Country of birth",
    "nationality": "Nationality",
    "country_of_residence": "Country of residence",
}
NON_ANSWERS = {"DATA_EXPIRED", "CONSENT_REVOKED", "Prefer not to say"}


def _flat(text: str) -> str:
    return " ".join(text.replace("\xa0", " ").split())


def read_export() -> tuple[list[str], list[str], list[list[str]]]:
    """(header, second header, data rows), identifying columns blanked on read."""
    with open(EXPORT, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    head, sub, data = rows[0], rows[1], rows[2:]
    drop = [head.index(name) for name in DROP]
    for row in data:
        for i in drop:
            row[i] = ""
    assert len(head) == 996 and len(data) == 112
    return head, sub, data


def code_of(label: str) -> tuple[int, int]:
    """(value code, label type) of an export label."""
    for code, (dim, item, _, _) in VALUES.items():
        if label == dim:
            return code, 1
        if label == item:
            return code, 2
    raise AssertionError(f"unknown value label {label!r}")


Question = tuple[list[int], list[int], list[int], str]


def questions(head: list[str], sub: list[str]) -> list[Question]:
    """The 88 questions: (least columns, most columns, value codes in column order, stem)."""
    blocks: list[tuple[int, int, str]] = []
    i = 22
    while i < len(head):
        if head[i] in (STEM, STEM_ERROR) or head[i] in (f"{MOST} {STEM}", f"{MOST} {STEM_ERROR}"):
            j = i + 1
            while j < len(head) and head[j] == "":
                j += 1
            blocks.append((i, j, "most" if head[i].startswith(MOST) else "least"))
            i = j
        else:
            i += 1
    assert len(blocks) == 176
    out = []
    for (a, b, kind_a), (c, d, kind_b) in zip(blocks[0::2], blocks[1::2], strict=True):
        assert (kind_a, kind_b) == ("least", "most") and sub[a:b] == sub[c:d]
        assert head[c] == f"{MOST} {head[a]}"
        codes = [code_of(x)[0] for x in sub[a:b]]
        out.append((list(range(a, b)), list(range(c, d)), codes, head[a]))
    for s in range(8):
        types = {code_of(sub[q[0][0]])[1] for q in out[s * 11 : (s + 1) * 11]}
        assert types == {SEGMENT_LABEL[s + 1]}, s
        for t, q in enumerate(out[s * 11 : (s + 1) * 11], 1):
            assert q[3] == (STEM_ERROR if (SEGMENT_LABEL[s + 1], t) == ERROR_AT else STEM), (s, t)
    return out


def instrument(head: list[str]) -> None:
    """The texts the condition uses, against the export's own headers."""
    assert _flat(head[19]) == (
        f"Welcome! {WELCOME} To help with some of the terms you may see throughout this "
        "survey, please click next to see a brief description of each value and the "
        "different ways they might be expressed."
    )
    defs = _flat(head[20])
    expected = (
        "".join(v[2] for v in VALUES.values()) + "Please click next to proceed to the survey."
    )
    assert defs.replace(" ", "") == expected.replace(" ", ""), defs
    for v in VALUES.values():
        assert v[2] in defs, v
    assert _flat(head[21]) == INSTRUCTIONS
    assert head[22] == STEM


def screens(occasion: int | None = None) -> dict[int, dict[str, Any]]:
    """Per kept person: condition, Prolific id, and per occasion the label type and
    eleven (codes in column order, most position, least position), 1-based."""
    head, sub, data = read_export()
    instrument(head)
    qs = questions(head, sub)
    layout: dict[tuple[int, int], tuple[int, ...]] = {}
    out: dict[int, dict[str, Any]] = {}
    for n, row in enumerate(data, 1):
        if row[1] != "Completed" or row[7] == "test_response":
            continue
        cond = row[8]
        answered = tuple(
            s + 1
            for s in range(8)
            if any(row[c] for q in qs[s * 11 : (s + 1) * 11] for c in q[0] + q[1])
        )
        assert answered == SEGMENTS[cond], (n, cond)
        occasions = []
        for s in answered:
            label = SEGMENT_LABEL[s]
            sets = []
            for t, (least_cols, most_cols, codes, _) in enumerate(qs[(s - 1) * 11 : s * 11], 1):
                assert layout.setdefault((label, t), tuple(codes)) == tuple(codes), (s, t)
                lv = [row[c] for c in least_cols]
                mv = [row[c] for c in most_cols]
                assert sorted(lv)[-1] == "1" and lv.count("1") == 1 and set(lv) <= {"", "1"}
                assert sorted(mv)[-1] == "1" and mv.count("1") == 1 and set(mv) <= {"", "1"}
                most, least = mv.index("1") + 1, lv.index("1") + 1
                assert most != least, (n, s, t)
                sets.append((tuple(codes), most, least))
            occasions.append((label, sets))
        assert cond.split("-")[0][0] == LABEL_TYPES[occasions[0][0]][0]
        out[n] = {"condition": cond, "prolific": row[PROLIFIC_COL].strip(), "occasions": occasions}
    assert len(out) == N_KEPT
    # Both label types show the same eleven sets in the same sequence.
    for t in range(1, N_SETS + 1):
        assert sorted(layout[(1, t)]) == sorted(layout[(2, t)])
    return out


def set_sizes() -> list[int]:
    """Values per set, t = 1..11, from the export."""
    head, sub, _ = read_export()
    return [len(q[2]) for q in questions(head, sub)[:N_SETS]]


def _label(value: str) -> str:
    """Typography only: trim, and the export's stray quote marks. Words untouched."""
    return value.replace("homemaker', 'retired", "homemaker, retired").strip()


def derive() -> pd.DataFrame:
    """One row per kept person, first occasion only: label type, codes, picks, persona."""
    people = screens()
    with open(DEMOS, encoding="utf-8-sig", newline="") as fh:
        demos = {r["Participant id"]: r for r in csv.DictReader(fh)}
    out: dict[str, list[Any]] = defaultdict(list)
    for n in sorted(people):
        p = people[n]
        info = demos[p["prolific"]]
        assert info["Status"] == "APPROVED"
        assert "CONSENT_REVOKED" not in info.values()
        label, sets = p["occasions"][0]
        out["participant_id"].append(n)
        out["label_type"].append(label)
        for t, (codes, most, least) in enumerate(sets, 1):
            for k in range(1, N_SLOTS + 1):
                out[f"item_{t}_{k}"].append(codes[k - 1] if k <= len(codes) else 0)
            out[f"most_{t}"].append(most)
            out[f"least_{t}"].append(least)
        for col in PERSONA.values():
            value = _label(info[col])
            out[col].append("" if value in NON_ANSWERS else value)
    return pd.DataFrame(out)


def text_of(code: int, label: int) -> str:
    return VALUES[code][0] if label == 1 else VALUES[code][1]


def preamble() -> str:
    return "\n".join([WELCOME, *(v[2] for v in VALUES.values()), INSTRUCTIONS])


def stem_for(label: int, t: int) -> str:
    """The stem as the screen showed it, with our clause where it was in error."""
    return f"{STEM_ERROR} {ERROR_CLAUSE}" if (label, t) == ERROR_AT else STEM


def arm_text(items: list[str], stem: str = STEM) -> str:
    return preamble() + "\n" + stem + "\n" + "\n".join(items) + "\n" + CLAUSE


def arm_question(which: str, items: list[str], stem: str = STEM) -> str:
    options = "; ".join(f'{k} means "{text}"' for k, text in enumerate(items, 1))
    return f'{stem} Report only the option you chose as "{which}". {options}.'


def task_nums(t: int) -> tuple[int, int]:
    """(most, least) task_num for set t."""
    return 2 * (t - 1), 2 * (t - 1) + 1


def cvars(t: int) -> list[str]:
    return ["label_type", *(f"item_{t}_{k}" for k in range(1, N_SLOTS + 1))]


def build_arms(wide: pd.DataFrame) -> list[dict[str, Any]]:
    """One arm per (label type, ordered set) shown, with its set's two questions."""
    shown: dict[tuple[int, ...], set[int]] = defaultdict(set)
    for t in range(1, N_SETS + 1):
        for tup in wide[cvars(t)].itertuples(index=False):
            shown[tuple(int(c) for c in tup)].add(t)
    arms = []
    for num, key in enumerate(sorted(shown)):
        label, codes = key[0], [c for c in key[1:] if c]
        items = [text_of(c, label) for c in codes]
        overrides: dict[int, dict[str, str]] = {}
        stems = {stem_for(label, t) for t in shown[key]}
        assert len(stems) == 1, key
        stem = stems.pop()
        for t in sorted(shown[key]):
            most, least = task_nums(t)
            overrides[most] = {"outcome_question": arm_question(MOST, items, stem)}
            overrides[least] = {"outcome_question": arm_question(LEAST, items, stem)}
        factors = {
            "label_type": LABEL_TYPES[label],
            "options": OPTION_SEP.join(VALUES[c][3] for c in codes),
        }
        arms.append(
            {
                "raw_values": dict(zip(cvars(1), key, strict=True)),
                "condition_num": num,
                "factors": factors,
                "text": arm_text(items, stem),
                "items": overrides,
            }
        )
    return arms


def build_outcomes(sizes: list[int]) -> list[dict[str, Any]]:
    outcomes = []
    for t, size in enumerate(sizes, 1):
        most, least = task_nums(t)
        for num, var, which in ((most, f"most_{t}", MOST), (least, f"least_{t}", LEAST)):
            outcomes.append(
                {
                    "var": var,
                    "task_num": num,
                    "question": f"[the {which} question, enumerated per arm in `items`]",
                    "scale": {"min": 1, "max": size, "nominal": True},
                    "condition_vars": cvars(t),
                }
            )
    return outcomes


LICENCE = (
    "CC BY 4.0, stated on OSF node ct8ae (https://osf.io/ct8ae/, read via the OSF API on "
    "17 Nov 2026) after the authors made it public that day at rich's request. Before that "
    "(16 Nov 2026) the node was private with no licence and its use was approved by rich. "
    "Paper: Behavior Research Methods 58(10), 2026, doi:10.3758/s13428-026-03167-x."
)

NOTES = """\
Liang, Glover & Hawkins, "Time after time, the Best Worst Scaling method is more
reliable than ranking", Behavior Research Methods 58(10), 2026
(doi:10.3758/s13428-026-03167-x; preprint OSF r5dyu), Experiment 1b. Data: OSF node
ct8ae, public under CC BY 4.0 since 17 Nov 2026 (private with no licence the day
before, when rich approved its use). QuestionPro survey on Prolific, 24-25
Oct 2023: 100 adults whose first language is English (55 living in the UK).

GENERATED by scripts/gen_osf_ct8ae.py, which also writes maxdiff_coded.csv from the
export. Every judgement is in that script's docstring; in brief:

- MaxDiff: eleven sets of 5 or 6 of Schwartz's ten values; pick the "Most Important"
  and the "Least Important" guiding principle in your life. Values labelled as
  dimensions ("Benevolence") or items ("Helpful, honest, forgiving"), between people.
  Two outcomes per set; the answer is the value's place in the listed order (1-5 or
  1-6), the options enumerated in the question (our words).
- Options within each set were not randomised (the published paper), but which fixed
  order was shown is not recorded (a Figure 1 screenshot disagrees with the export;
  no position effect). Per rich's ruling of 16 Nov 2026, values are
  listed in the data file's order with our clause "(the options are listed in the data
  file's order; the order on screen was not recorded)". Value identities are factors.
- First occasion only: the retest followed minutes later on the same sets, which a
  row cannot state. The retest serves the reference check instead.
- Wording word-for-word from the export's headers: the welcome's sentences on values,
  the definitions page, the instructions and the stem. Dropped: navigation, "Step 1 of
  1". Added words, ours: the clause, 'Report only the option you chose as "Most
  Important".' (or "Least Important") and the '1 means "..."' enumeration.
- Script error kept and flagged: item-label set 5's question read "MOST and MOST"; it
  is rendered as shown with our clause saying so. That arm is not a clean contrast.
- IP address and email columns blanked on read; never in the derived file or rows.
- Reproduces the paper: Benevolence 0.375, Power -0.46, Table 1's top five in order,
  test-retest tau 0.82 (same labels) and 0.41 (changed labels).
"""


class _Literal(str):
    pass


class _Dumper(yaml.SafeDumper):
    """Multi-line strings as `|` blocks, so the recipe reads as the row will."""


def _str(dumper: yaml.SafeDumper, data: str) -> yaml.ScalarNode:
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style=style)


_Dumper.add_representer(_Literal, _str)
_Dumper.add_representer(str, _str)


def render(wide: pd.DataFrame | None = None) -> str:
    if wide is None:
        wide = derive()
    recipe = {
        "study_id": STUDY,
        "source": "osf",
        "title": (
            "Schwartz life values: which of five or six is the most and least important "
            "guiding principle in your life (best-worst scaling)"
        ),
        "data_file": DERIVED.name,
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "experiment": "maxdiff",
        "participant_id_var": "participant_id",
        "notes": _Literal(NOTES),
        "condition": {
            "source_vars": cvars(1),
            "factors": ["label_type", "options"],
            "arms": build_arms(wide),
        },
        "outcomes": build_outcomes(set_sizes()),
        "response_recode": {k: k for k in range(1, N_SLOTS + 1)},
        "persona_map": dict(PERSONA),
    }
    return yaml.dump(recipe, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=100)


def _same_csv(wide: pd.DataFrame) -> bool:
    on_disk = pd.read_csv(DERIVED)
    return bool(on_disk.equals(pd.read_csv(pd.io.common.StringIO(wide.to_csv(index=False)))))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    wide = derive()
    text = render(wide)
    if args.check:
        ok, ok_csv = RECIPE.read_text() == text, _same_csv(wide)
        print(
            f"recipe {'matches' if ok else 'DIFFERS'}; derived CSV {'matches' if ok_csv else 'DIFFERS'}"
        )
        return 0 if ok and ok_csv else 1
    wide.to_csv(DERIVED, index=False)
    RECIPE.write_text(text)
    print(f"wrote {DERIVED.relative_to(REPO)} {wide.shape} and {RECIPE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
