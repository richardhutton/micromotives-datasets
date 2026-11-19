#!/usr/bin/env python3
"""Write recipes/figshare_32935409_maxdiff.yaml: how serious is each breach of academic integrity (MaxDiff).

Rigby et al., "Student perceptions of 'the line' between acceptable and unacceptable
academic conduct in the age of Gen-AI: an Anchored Best-Worst Scaling study". The
paper could not be found on 16 Nov 2026 (searched by title, method and author); the
deposit's own description is the only account of it. University of Manchester
Figshare, doi:10.48420/32935409 (article 32935409 v1, posted 29 Jul 2026), licence
CC BY 4.0, read from https://api.figshare.com/v2/articles/32935409 on 16 Nov 2026.
The deposit: `ThresholdDatasetJournal.csv` (tab-separated despite the name; 56,040 x
196, long, one row per alternative per choice task; md5 70e5732b...) and
`ThresholdQuestionnaireWithVarNames.pdf` (55 pages, a Sawtooth print of the
fielded questionnaire with each answer's variable and code beside it).

The second MaxDiff in the corpus, built exactly as `scripts/gen_zenodo18547379.py`
builds the first. Every judgement is here, in code, so the recipe can be
re-derived and reviewed:

* THE DESIGN. 20 student behaviours; each respondent saw ten screens of four
  (PDF pp. 23-32, `serious_1` .. `serious_10`) and ticked the one "Most Serious"
  and the one "Least Serious" breach of academic integrity. 467 respondents, 120
  long rows each (checked): sets 1-10 are the ten screens, each written twice
  (`scale` 1 = the most-serious choice task, -1 = the least-serious one, four
  alternatives each, `seribest` marks the pick); sets 11-30 (`ancset` 1) are the
  anchoring "should / should not result in disciplinary action" grid, one set per
  behaviour (set 10+k is behaviour k, and its pick equals `threshshd_rk`), which is
  not a choice among the four and is not built (below). There are 50 design
  versions, and the version is a function of the respondent number alone:
  respondent n saw version ((n - 1) mod 50) + 1 (checked: every respondent with the
  same residue saw the same 40 items in the same order; `sys_RespNum` equals `id`).
  Every respondent saw each of the 20 behaviours exactly twice.

* THE PICKS. Two independent encodings in the deposit agree on all 4,670 screens:
  the wide `serimost{t}` / `serileast{t}` hold the item CODE picked, and the long
  rows' `seribest` flag the same items (0 mismatches). Every pick is one of the
  four items on its screen and most != least on every screen (checked). The PDF
  shows the codes are the item numbers (`serious_1_b=20` is the "Most Serious" box
  beside item 20's text). Because a pick is stored as an item code, not a
  position, no pick-to-slot alignment has to be inferred, unlike zenodo18547379.

* ON-SCREEN ORDER, the riskiest judgement. `item1..item4` (= `alt` 1-4) are taken
  as the top-to-bottom screen order. Evidence: (a) the PDF prints version 1 (the
  ten respondents with n = 51, 101, ..., 501), and for them the data's order equals
  the printed order on all ten screens, set order included; (b) the order is not a
  sort: 240 of 4,670 screens are ascending, near the 1-in-24 chance rate, so the
  "items stored in code order" worry does not hold; (c) every behaviour sits in
  every position 214-254 times, the positional balance a MaxDiff design is built
  with; (d) the "Least Serious" pick depends on stored position (1,224 / 1,150 /
  1,074 / 1,222 over positions 1-4; a permutation test that shuffles positions
  within each screen gives p = 0.0075), the end effect a fixed list produces and
  which a display shuffled independently of `alt` could not. The "Most Serious"
  pick shows no position effect (p = 0.85). Nothing in the deposit says whether
  the software shuffled the four rows on display; if it did, the
  docs/CONVENTIONS.md ruling of 16 Nov 2026 would keep these rows with the clause
  "(the options were shown in a random order)", so this judgement changes one
  clause, not whether the source is built.

* `rnd` IS NOT ABOUT THIS TASK. A number 0-100 per respondent; it varies within
  every design version (94 of the 99 values that occur span several versions), so
  it neither sets the design nor the order. It tracks `chatbws` / `chatreal`
  (rnd > 50 gets 1 for 439 of 467), which split an EARLIER block: chatreal 0 asked
  the essay-mill prevalence question (`ccprev`, `cccaught1`), 1 the ChatGPT one
  (`gptprev`, `gptcaught`), and only chatreal 1 has `aimost`. Every respondent saw
  the same MaxDiff task afterwards, so this is not a condition of these rows. The
  sibling deposit doi:10.48420/31292425 ("Generative AI, Contract Cheating and the
  Barriers to Academic Misconduct", same team, ~500 UK and Australian students) is
  a different BWS (what most and least deters you) in two Stata files split by
  that same AI / contract-cheating sample; not the same structure, not built.

* CONDITION. Word-for-word from the PDF screen: the stem "Which of these 4
  behaviours is the: Most Serious and which is the Least Serious breach of
  Academic Integrity." (a line break after "the:" rendered as a space), the four
  behaviours one per line in screen order, then the screen's footnote "By
  'academic integrity' we mean ...". "(t of 10)" is dropped (docs/CONVENTIONS.md,
  "Sequence signposting"). Typography only: PDF line wraps joined with a space. The
  generator re-reads every screen from the PDF (`instrument()`, via `pdftotext
  -layout`) and checks each text and its order. One arm per distinct ordered set
  of four actually shown: 500 (50 versions x 10 screens, none repeated). Each
  behaviour's code (the instrument's own, 1-20) sits in the derived file and its
  slug in the `item_k` factors, so training can re-order and remap.

* OUTCOMES. Two per screen, task_num 2(t-1) + 0/1. "Most Serious" and "Least
  Serious" are two answer columns of one question on one screen, so each is its
  own outcome (docs/CONVENTIONS.md, "One stem, several labelled answer fields"):
  the stem, then 'Report only the option you chose as "Most Serious".' (or "Least
  Serious"), then '1 means "<behaviour 1>"; 2 means ...' (our words, as
  zenodo18547379). The answer is the screen position, 1-4, nominal. Fallback
  outcome wording is a bracketed placeholder that QC rule 21 fails on; every arm
  carries its own question for the screens it was shown on.

* NOT BUILT. The anchoring grids `threshshd` ("should") and `threshwd` ("would")
  result in disciplinary action: 20 behaviours on one screen each, in an order the
  PDF prints differently from the MaxDiff and the data does not record; no choice
  among a set, and outside this MaxDiff recipe. The ease questions
  `seriousbwscomp` / `seriousbwsmake` are about the task, not an answer to it.
  `seritrain*` (four columns not in the PDF) are undocumented and left alone.

* PERSONA. A SPECIALIST SAMPLE: university students (current, or in 2023) in the
  UK and Australia. Fine for teaching the format; not a general population. The
  instrument asks no age. Jev (scripts/recipe_prep.py's report functions, 16 Nov
  2026, on question wordings and value labels only) found `gen` "What is your
  gender?" as the only standard persona field (conf 1.00) and no age, income,
  education, ethnicity, employment, marital status, region, religion or
  household size. Mapped: gender (gen); and as extras, in the PDF's own words,
  country of study (ctry: only Australia and UK occur), degree level (student),
  year of degree (year), full or part time (ftpt), domestic or international
  (dom) and main discipline (disc). "Prefer not to say" (gen) is a non-answer (Jev,
  conf 1.00) and is blanked; "Other (please tell us)" on student, year and disc is
  an answer wearing an instruction (Jev 0.91 / 0.88 / 0.83) and is written
  "Other". Not mapped: `eal` is stored 0/1 while the PDF codes it 1/2, so which
  value means which cannot be proved from the deposit; `fem`, `male`, `inter`,
  `sci` and the rest are derived dummies of mapped questions. Being a student is
  not written into `employment` or `education`: the Student mapping is pending a
  ruling, and an undergraduate's highest completed qualification is not stated.

    uv run python scripts/gen_figshare_32935409.py           # write derived CSV + recipe
    uv run python scripts/gen_figshare_32935409.py --check   # exit 1 if either differs
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
STUDY = "figshare_32935409"
RAW = REPO / "data" / "raw" / STUDY
CSV = RAW / "ThresholdDatasetJournal.csv"
PDF = RAW / "ThresholdQuestionnaireWithVarNames.pdf"
DERIVED = RAW / "maxdiff_coded.csv"
RECIPE = REPO / "recipes" / f"{STUDY}_maxdiff.yaml"

N_TASKS = 10
N_SLOTS = 4
N_VERSIONS = 50
MOST, LEAST = "Most Serious", "Least Serious"
FIRST_SCREEN_PAGE = 23  # serious_1 is PDF page 23, serious_10 page 32

STEM = (
    "Which of these 4 behaviours is the: Most Serious and which is the Least Serious "
    "breach of Academic Integrity."
)
DEFINITION = (
    "By 'academic integrity' we mean the expectation that students and all members of "
    "the academic community act with: honesty, trust, fairness, respect and responsibility."
)

# The instrument's own codes (the value of `serious_t_b` / `serious_t_w` beside each
# text in the PDF), text word-for-word, slug for `factors`.
ITEMS: dict[int, tuple[str, str]] = {
    1: ("Basing your assignment on that of a student from a previous year", "previous_year"),
    2: ("Collaborating on an assignment when it should be individual work", "collaborating"),
    3: (
        "Copying a few paragraphs into an assignment from a source without referencing it",
        "copy_few_paragraphs",
    ),
    4: ("Copying most of an assignment from a source without referencing it", "copy_most"),
    5: (
        "Adding sources you have not used to Reference section of an assignment",
        "unused_references",
    ),
    6: (
        "Inventing an illness or family crisis to get an extension on an assignment",
        "invented_illness",
    ),
    7: ("Not contributing to the group work in a group assignment", "group_freeriding"),
    8: ("Taking an exam for another person", "exam_impersonation"),
    9: ("Taking un-authorized notes into an on-campus exam", "unauthorised_notes"),
    10: ("Submitting an assignment written for you (for free) by a friend", "friend_wrote_it"),
    11: (
        "Writing an assignment (for free) for a friend who will submit it as their own work",
        "wrote_for_friend",
    ),
    12: (
        "Submitting an essay you downloaded for free from an internet essay bank",
        "essay_bank",
    ),
    13: ("Making up data or results for a project or lab report", "fabricated_data"),
    14: ("Submitting an assignment you paid a company to write for you.", "paid_company"),
    15: (
        "Using an assignment you purchased to help you write your own assignment.",
        "purchased_as_help",
    ),
    16: ("Submitting an assignment that was 100% generated by ChatGPT", "chatgpt_100pc"),
    17: (
        "Submitting an assignment that is your edit of content generated by ChatGPT",
        "chatgpt_edited",
    ),
    18: (
        "Using ChatGPT to rephrase work you have pasted from a website/paper.",
        "chatgpt_rephrase",
    ),
    19: (
        "Putting your assignment into ChatGPT to get an idea how to answer it (but writing "
        "it yourself)",
        "chatgpt_ideas",
    ),
    20: (
        "Recording yourself as present at a compulsory session when you were absent.",
        "false_attendance",
    ),
}

# Version 1 as the PDF prints it (screen t, top to bottom), read by `instrument()`.
PDF_VERSION_1 = [
    (20, 10, 19, 3),
    (16, 17, 8, 15),
    (9, 2, 6, 7),
    (11, 18, 1, 4),
    (5, 13, 14, 12),
    (17, 20, 2, 11),
    (6, 16, 12, 10),
    (8, 4, 14, 3),
    (18, 19, 5, 9),
    (1, 15, 7, 13),
]

# Persona: derived column -> (source column, {code: label as the PDF prints it}).
# None as a label blanks the field (a non-answer); see the docstring.
OTHER = "Other"
PERSONA: dict[str, tuple[str, dict[int, str | None]]] = {
    "gender": ("gen", {1: "Female", 2: "Male", 3: "Other", 4: None}),
    "country_of_study": ("ctry", {1: "Australia", 2: "UK"}),
    "degree_level": ("student", {1: "Undergraduate", 2: "Postgraduate", 3: OTHER}),
    "year_of_degree": (
        "year",
        {1: "Year 1", 2: "Year 2", 3: "Year 3", 4: "Year 4", 5: "Have finished it.", 6: OTHER},
    ),
    "full_or_part_time": ("ftpt", {1: "Full time", 2: "Part time"}),
    "domestic_or_international": ("dom", {1: "domestic / home", 2: "international student"}),
    "discipline": (
        "disc",
        {
            1: "Architecture and Buildings",
            2: "Arts/Humanities",
            3: "Business and Commerce",
            4: "Creative Arts/Performance",
            5: "Earth & Environmental Sciences",
            6: "Education",
            7: "Engineering",
            8: "Health Sciences",
            9: "Information Technology",
            10: "Law",
            11: "Mathematics",
            12: "Media/Communication Studies",
            13: "Science",
            14: "Psychology",
            15: OTHER,
        },
    ),
}


def item_var(t: int, k: int) -> str:
    return f"item_{t}_{k}"


def task_nums(t: int) -> tuple[int, int]:
    """(most, least) task_num for screen t."""
    return 2 * (t - 1), 2 * (t - 1) + 1


def version(respondent: int) -> int:
    return (respondent - 1) % N_VERSIONS + 1


def load() -> pd.DataFrame:
    return pd.read_csv(CSV, sep="\t", dtype=str, keep_default_na=False)


def _flat(text: str) -> str:
    return " ".join(text.split())


def instrument() -> None:
    """Check STEM, DEFINITION, every item text and version 1's order against the PDF.

    `pdftotext -layout` prints each screen's rows top to bottom with the answer
    boxes' variable names (`serious_t_w=<code>`) on the row they belong to, so the
    codes' order is the screen order, and with those names removed the page reads
    as the screen does.
    """
    for t, expected in enumerate(PDF_VERSION_1, 1):
        page = FIRST_SCREEN_PAGE + t - 1
        out = subprocess.run(
            ["pdftotext", "-layout", "-f", str(page), "-l", str(page), str(PDF), "-"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        codes = tuple(int(c) for c in re.findall(rf"serious_{t}_w=(\d+)", out))
        assert codes == expected, (t, codes)
        assert re.findall(rf"serious_{t}_b=(\d+)", out) == [str(c) for c in codes], t
        flat = _flat(re.sub(rf"serious_{t}_[bw]=\d+", " ", out))
        assert flat.startswith(f"serious_{t} {STEM} Most Least Serious Serious "), t
        assert flat.endswith(f"({t} of 10) {DEFINITION} Back Next 0% 100%"), t
        for c in codes:
            assert ITEMS[c][0] in flat, (t, c)
        at = [flat.index(ITEMS[c][0]) for c in codes]
        assert at == sorted(at), (t, at)


def derive(df: pd.DataFrame) -> pd.DataFrame:
    """One row per respondent: version, item codes in screen order, picks, persona."""
    assert df.shape == (56040, 196)
    people = df[df["n"] == "1"].set_index("id")
    assert len(people) == 467 and (people.index == people["sys_RespNum"]).all()
    assert (df.groupby("id").size() == 120).all()
    bws = df[df["ancset"] == "0"]
    assert set(bws["set"].astype(int)) == set(range(1, N_TASKS + 1))
    # Each screen's four items, from the scale = 1 rows in `alt` order; the scale =
    # -1 rows must list the same four in the same order.
    tasks: dict[tuple[str, int], dict[str, Any]] = {}
    for (pid, s, scale), g in bws.groupby(["id", "set", "scale"]):
        g = g.sort_values("alt", key=lambda c: c.astype(int))
        assert g["alt"].tolist() == ["1", "2", "3", "4"]
        items = tuple(int(i) for i in g["item"])
        assert items == tuple(int(g.iloc[0][f"item{k}"]) for k in range(1, 5))
        chosen = g[g["seribest"] == "1"]["item"].tolist()
        assert len(chosen) == 1, (pid, s, scale)
        rec = tasks.setdefault((str(pid), int(s)), {"items": items})
        assert rec["items"] == items
        rec["most" if scale == "1" else "least"] = int(chosen[0])

    out: dict[str, list[Any]] = defaultdict(list)
    layout: dict[int, tuple[tuple[int, ...], ...]] = {}
    for pid in sorted(people.index, key=int):
        r = people.loc[pid]
        v = version(int(pid))
        screens = tuple(tasks[(pid, t)]["items"] for t in range(1, N_TASKS + 1))
        assert layout.setdefault(v, screens) == screens, ("version != layout", pid)
        assert sorted(c for s in screens for c in s) == sorted(list(range(1, 21)) * 2)
        out["participant_id"].append(int(pid))
        out["version"].append(v)
        for t in range(1, N_TASKS + 1):
            task = tasks[(pid, t)]
            items = list(task["items"])
            most, least = int(r[f"serimost{t}"]), int(r[f"serileast{t}"])
            # The wide columns and the long rows' flags are independent encodings.
            assert (most, least) == (task["most"], task["least"]), (pid, t)
            assert most in items and least in items and most != least, (pid, t)
            for k, code in enumerate(items, 1):
                out[item_var(t, k)].append(code)
            out[f"most_{t}"].append(items.index(most) + 1)
            out[f"least_{t}"].append(items.index(least) + 1)
        for field, (src, labels) in PERSONA.items():
            raw = r[src]
            out[field].append("" if raw == "" else (labels[int(raw)] or ""))
    assert layout[1] == tuple(PDF_VERSION_1)
    assert len(layout) == N_VERSIONS
    return pd.DataFrame(out)


def arm_question(which: str, items: list[str]) -> str:
    options = "; ".join(f'{k} means "{text}"' for k, text in enumerate(items, 1))
    return f'{STEM} Report only the option you chose as "{which}". {options}.'


def arm_text(items: list[str]) -> str:
    return STEM + "\n" + "\n".join(items) + "\n" + DEFINITION


def build_arms(wide: pd.DataFrame) -> list[dict[str, Any]]:
    """One arm per distinct ordered four actually shown, with its screens' questions."""
    screens: dict[tuple[int, ...], set[int]] = defaultdict(set)
    for t in range(1, N_TASKS + 1):
        cols = [item_var(t, k) for k in range(1, N_SLOTS + 1)]
        for tup in wide[cols].itertuples(index=False):
            screens[tuple(int(c) for c in tup)].add(t)
    arms = []
    for num, tup in enumerate(sorted(screens)):
        items = [ITEMS[c][0] for c in tup]
        overrides: dict[int, dict[str, str]] = {}
        for t in sorted(screens[tup]):
            most, least = task_nums(t)
            overrides[most] = {"outcome_question": arm_question(MOST, items)}
            overrides[least] = {"outcome_question": arm_question(LEAST, items)}
        arms.append(
            {
                "raw_values": {item_var(1, k): c for k, c in enumerate(tup, 1)},
                "condition_num": num,
                "factors": {f"item_{k}": ITEMS[c][1] for k, c in enumerate(tup, 1)},
                "text": arm_text(items),
                "items": overrides,
            }
        )
    return arms


def build_outcomes() -> list[dict[str, Any]]:
    outcomes = []
    for t in range(1, N_TASKS + 1):
        most, least = task_nums(t)
        cvars = [item_var(t, k) for k in range(1, N_SLOTS + 1)]
        for num, var, which in ((most, f"most_{t}", MOST), (least, f"least_{t}", LEAST)):
            outcomes.append(
                {
                    "var": var,
                    "task_num": num,
                    "question": f"[the {which} question, enumerated per arm in `items`]",
                    "scale": {"min": 1, "max": 4, "nominal": True},
                    "condition_vars": cvars,
                }
            )
    return outcomes


NOTES = """\
Rigby et al., "Student perceptions of 'the line' between acceptable and unacceptable
academic conduct in the age of Gen-AI: an Anchored Best-Worst Scaling study" (not
found published on 16 Nov 2026). University of Manchester Figshare,
doi:10.48420/32935409 v1. Online survey (Sawtooth) of 467 university students in the
UK (232) and Australia (235), current or in 2023. A SPECIALIST SAMPLE: students, not
a general population; no age was asked.

GENERATED by scripts/gen_figshare_32935409.py, which also writes the derived data file
maxdiff_coded.csv from the deposit's long file. Every judgement is in that script's
docstring; in brief:

- MaxDiff: ten screens of four of 20 student behaviours; tick the one "Most Serious"
  and the one "Least Serious" breach of academic integrity. Two outcomes per screen;
  the answer is the behaviour's screen position, 1-4, and the options are enumerated
  in the question (our words). 50 design versions, set by respondent number.
- Wording word-for-word from the fielded questionnaire PDF (pp. 23-32), including the
  screen's footnote defining academic integrity. "(t of 10)" is dropped (sequence
  signposting). Added words, ours: 'Report only the option you chose as "Most
  Serious".' (or "Least Serious") and the '1 means "..."; 2 means ...' enumeration.
- Picks are stored as item codes in two independent encodings that agree on every
  screen, so no pick-to-position alignment is inferred.
- Screen order = the deposit's alt order. The PDF prints version 1 in exactly the
  data's order, and "Least Serious" picks show an end effect by stored position
  (permutation p = 0.0075). The deposit does not state whether the display was
  shuffled; the riskiest judgement here.
- Not built: the anchoring should/would-be-disciplined grids (threshshd, threshwd).
- No published reference to check against: the paper could not be found.
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
        wide = derive(load())
    recipe = {
        "study_id": STUDY,
        "source": "figshare",
        "title": (
            "Student perceptions of academic integrity in the age of Gen-AI: which of four "
            "behaviours is the most and least serious breach (best-worst scaling)"
        ),
        "data_file": DERIVED.name,
        "licence": (
            "CC BY 4.0, stated on University of Manchester Figshare article 32935409 "
            "(doi:10.48420/32935409) and read from "
            "https://api.figshare.com/v2/articles/32935409 on 16 Nov 2026."
        ),
        "comparable_to_socsci210": False,
        "experiment": "maxdiff",
        "participant_id_var": "participant_id",
        "notes": _Literal(NOTES),
        "condition": {
            "source_vars": [item_var(1, k) for k in range(1, N_SLOTS + 1)],
            "factors": [f"item_{k}" for k in range(1, N_SLOTS + 1)],
            "arms": build_arms(wide),
        },
        "outcomes": build_outcomes(),
        "response_recode": {1: 1, 2: 2, 3: 3, 4: 4},
        "persona_map": {field: field for field in PERSONA},
    }
    return yaml.dump(recipe, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    instrument()
    wide = derive(load())
    text = render(wide)
    if args.check:
        ok = RECIPE.read_text() == text
        on_disk = pd.read_csv(DERIVED)
        ok_csv = on_disk.equals(pd.read_csv(pd.io.common.StringIO(wide.to_csv(index=False))))
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
