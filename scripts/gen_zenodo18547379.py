#!/usr/bin/env python3
"""Write recipes/zenodo18547379_maxdiff.yaml: meat-reduction policies, best-worst (MaxDiff).

McBey, Martinez Sanchez, Horgan, Macdiarmid & McCormick, "Perceived effectiveness
of 25 interventions and policies designed to reduce meat consumption", Food
Quality and Preference 135 (2026) 105693, https://doi.org/10.1016/j.foodqual.2025.105693
(open access, CC BY; repository copy https://hdl.handle.net/2164/26170). Zenodo
record 18547379 v1.1, "Scottish meat consumption survey (Feb-Jul 2023)", licence
cc-by-4.0, read from https://zenodo.org/api/records/18547379 on 16 Nov 2026. The
deposit: `Scottish meat survey open access - cleaned.csv` (1,590 x 150, a Qualtrics
export with its two header rows removed), `Scottish_meat_survey_codebook_public.json`
(and the same as .tsv) and `README_open_access_Scottish_meat_survey_v3.txt`.

The first MaxDiff (best-worst scaling) in the corpus. Every judgement is here, in
code, so the recipe can be re-derived and reviewed:

* THE DESIGN. 25 policies and interventions; each respondent saw ten screens of
  four, picking the one "Most Likely" and the one "Least Likely" to make them eat
  less meat (the paper: "ten random subsets of four ... A balanced incomplete
  block design"). `vers_MAXDIFF` is the design version (260 of them, 3-7 people
  each); `{t}.{k}_MAXDIFF` holds the TEXT of the item in slot k of screen t, and
  one version always holds the same 40 texts (checked). 81 of 1,590 respondents
  have no version and no MaxDiff data at all (every item, pick and follow-up cell
  blank, checked); they are left out, leaving 1,509. Every one of the 15,090
  screens has four distinct items, exactly one "Most Likely" and exactly one
  "Least Likely" (checked, no exceptions). Non-meat-eaters are kept: only 5 of the
  1,509 (all pescatarian) are not omnivore or flexitarian, and the paper's own
  exclusion of non-meat-eaters is an analysis choice, not a routing one (they
  answered the same screens).

* THE INSTRUMENT. The deposit holds no questionnaire. The fielded wording is
  Qualtrics' own question-text header row, which the README says the codebook's
  `question` field reproduces. Screen t's picks are `Q{33+2t}_k`, whose codebook
  text is "(t/10) From the options below, choose the one that you think most
  likely, and the one that you think least likely to cause you to eat less meat
  and more vegetarian foods. - [Field-t.k_MAXDIFF]". The paper's Appendix 2
  words the 25 items differently ("A TV programme ...", "Plant-based options
  were cheaper ..."); those are descriptions for the paper, not what was shown,
  so the item texts come from the data, which is what Qualtrics piped onto the
  screen. Its Appendix 3 uses the data's own wording, which supports this.

* PICK k IS ITEM SLOT k. Qualtrics names each pick column after the embedded
  field it displayed: `Q35_k` is the row showing `${e://Field/1.k_MAXDIFF}`. That
  is the export's own statement of the alignment. Checked against the paper too:
  best-minus-worst per appearance, ranked, matches the paper's Appendix 3
  overall ranking of all 25 with Spearman 0.996 (Kendall 0.973; the only
  differences are adjacent swaps of items whose scores differ by 0.004 or less).
  Every other of the 23 ways of pairing pick columns with slots scores lower
  (the next best 0.964, which keeps two of the four slots right; every
  derangement is between 0.34 and -0.95).

* SLOT k IS SCREEN POSITION k. Not stated anywhere in the deposit, so this is
  inferred. If Qualtrics had shuffled the four rows on display, nothing on screen
  would follow k. It does: allowing for each item's own pull, the item in slot 1
  is picked "Most Likely" 14% more often than expected (4,305 against 3,765) and
  slots 1 and 4 are picked "Least Likely" more often (1.035, 1.047) than slots 2
  and 3 (0.943, 0.974), the primacy and end effects a fixed top-to-bottom list
  produces. Every item sat in every slot 565-642 times, so this is not the
  design putting strong items first. The rows render the items in slot order and
  the answer is the slot, 1-4. The riskiest judgement in this recipe.

* CONDITION. The stem (the codebook text above, "(t/10) " and " - [Field-...]"
  removed) followed by the four item texts, one per line, in slot order. "(t/10)"
  is dropped: a row cannot say where it sat in a sequence (docs/CONVENTIONS.md,
  "Sequence signposting"). The stem is the same in every arm but is written into
  each arm rather than into `shared_context`, because the pipeline joins
  `shared_context` to the arm with a space and the list has to start on its own
  line. Item typography: runs of spaces collapsed ("Receiving  a flyer" has two in
  the data; a web page shows one). No other character is changed. One arm per
  distinct ordered set of four actually shown: 2,583 of them over 2,600
  (version, screen) pairs. 203 sets of four were shown in more than one order;
  each order is its own arm, because the order is part of what was seen.
  The 25 items are coded 1-25 in alphabetical order of the data's text; the code
  exists only in the derived file and as `item_k` factors (slugs below), which
  hold the four item ids per row for splits by item.

* OUTCOMES. Three per screen, task_num 3(t-1) + 0/1/2:
  - "Most Likely" and "Least Likely" are two answer columns of ONE question on
    one screen, so each is its own outcome (docs/CONVENTIONS.md, "One stem,
    several labelled answer fields"). The question is the stem, plus one added
    sentence naming the column by its own on-screen label: 'Report only the
    option you chose as "Most Likely".' (or "Least Likely"), then the options
    enumerated, '1 means "<slot 1 text>"; 2 means ...' (our words, the PZB01G /
    DEL conjoint convention for a nominal choice). The answer is the slot, 1-4,
    nominal. Neither row names the other pick: both were made at once.
  - The follow-up "Considering only the options above..." (`Q{34+2t}`), answered
    by all 1,509 on all ten screens, IS built: it is asked about the same four
    items, every respondent got it, it is an answer about their own behaviour
    rather than a check on what they read, and the item texts it refers to sit
    in the condition, above it. Coded 1 "None of these would impact how much
    meat I eat", 2 "Some of these ...", 3 "All of these ..." (the codebook's
    labels word-for-word; an ordered scale, so endpoint and midpoint labels).
    Whether it shared the screen with the picks or followed on the next one is
    not in the deposit; either way the condition is the same four items.
  Fallback outcome wording for the two pick outcomes is a bracketed placeholder:
  every arm carries its own enumerated question for exactly the screens it was
  shown on (checked below), and QC rule 21 fails the build if a bracket ever
  reaches a row.

* PERSONA, from the derived file: gender (Q9), age band (Q10, into `age_band`;
  the persona's `age` holds whole years), education (Q11), ethnicity (Q8),
  household income (Q12, "What was your total household income before taxes in
  the last 12 months?"), employment (Q13), area (Q7, "Where do you live?").
  "Prefer not to say" is a non-answer (Jev, conf 1.00, via
  scripts/recipe_prep.py's functions on 16 Nov 2026) and is blanked here because a
  delimited export has no codes for `persona_missing` to name. Not mapped: Q14
  household status (Jev offered it as marital status at 0.26; it is a living
  arrangement, not a marital status), Q15-Q17 children, and everything about
  diet and meat (Q19-Q34), which is the outcome's own domain. Q8 is a
  tick-all-that-apply: two respondents ticked White and one other group, mapped
  to "Mixed or Multiple ethnic groups" by the crosswalk (scheme
  uk_zenodo18547379, added by merge with the other new labels: Jev read each one
  as the concept it is mapped to).

    uv run python scripts/gen_zenodo18547379.py           # write derived CSV + recipe
    uv run python scripts/gen_zenodo18547379.py --check   # exit 1 if either differs
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "zenodo18547379"
CSV = RAW / "Scottish meat survey open access - cleaned.csv"
CODEBOOK = RAW / "Scottish_meat_survey_codebook_public.json"
DERIVED = RAW / "maxdiff_coded.csv"
RECIPE = REPO / "recipes" / "zenodo18547379_maxdiff.yaml"

N_TASKS = 10
N_SLOTS = 4
MOST, LEAST = "Most Likely", "Least Likely"

# The codebook's question text for every pick column is this, between "(t/10) "
# and " - [Field-t.k_MAXDIFF]". Asserted against the codebook in `stem()`.
STEM = (
    "From the options below, choose the one that you think most likely, and the one "
    "that you think least likely to cause you to eat less meat and more vegetarian foods."
)
FOLLOW_UP = "Considering only the options above..."
IMPACT = {
    "None of these would impact how much meat I eat": 1,
    "Some of these would impact how much meat I eat": 2,
    "All of these would impact how much meat I eat": 3,
}

# Slug per item, for `factors`. Keyed by the data's text exactly as stored.
SLUGS = {
    "A 15% tax on the price of meat": "meat_tax_15pc",
    "A television programme on the health and environmental impact of eating too much meat": (
        "tv_programme"
    ),
    "Access to a website that explained the environmental, health, and animal welfare "
    "impact of meat": "website",
    "An app that showed me vegetarian meals": "app",
    "Celebrity endorsement of vegetarian foods": "celebrity",
    "Choosing to nominate certain days of the week as 'meat-free'": "meat_free_days",
    "Free cooking classes for vegetarian or reduced meat meals": "cooking_classes",
    "Free samples of vegetarian dishes to eat in a supermarket": "free_samples",
    "Greater variety of vegetarian dishes (e.g., in a supermarket or restaurant)": (
        "greater_variety"
    ),
    "Labelling of meat as 'factory farmed'": "label_factory_farmed",
    "Labels on meat showing it is bad for the environment (e.g., the traffic light system)": (
        "label_environment"
    ),
    "Labels on meat showing it is unhealthy (e.g., the traffic light system)": "label_unhealthy",
    "Learning more about the life of livestock": "livestock_life",
    "Lower price of vegetarian foods": "lower_price",
    "No meat available in workplace/school canteen": "no_meat_canteen",
    "Pre-made shopping lists and recipes for plant-based foods (e.g., when shopping online "
    "for food)": "shopping_lists",
    "Ready meals that contained less meat, and more vegetables or pulses": "ready_meals",
    "Receiving  a flyer on the benefits of vegetarian diets": "flyer",
    "There were more vegetarian than meat options in the supermarket": "more_veg_options",
    "Vegetarian dishes recommended to me in a restaurant by staff": "staff_recommend",
    "Vegetarian options were cheaper than they are now": "cheaper_than_now",
    "Vegetarian options were cheaper than those containing meat": "cheaper_than_meat",
    "Vegetarian options were more appealing or tasty": "more_appealing",
    "Vegetarian options were next to meats in the supermarket": "next_to_meat",
    "Weekly text messages reminding me of healthy and environmentally friendly vegetarian "
    "meals": "text_messages",
}
CODES = {text: i + 1 for i, text in enumerate(sorted(SLUGS))}

# Persona: derived column -> source column. Non-answers blanked (see docstring).
PERSONA = {
    "gender": "Q9",
    "age_band": "Q10",
    "education": "Q11",
    "ethnicity": "Q8",
    "income": "Q12",
    "employment": "Q13",
    "urban_rural": "Q7",
}
NON_ANSWERS = {"Prefer not to say"}

PICK_Q = {t: f"Q{33 + 2 * t}" for t in range(1, N_TASKS + 1)}
FOLLOW_Q = {t: f"Q{34 + 2 * t}" for t in range(1, N_TASKS + 1)}


def shown(text: str) -> str:
    """The item as a page displays it: runs of spaces collapsed, nothing else."""
    return re.sub(r" {2,}", " ", text)


def item_var(t: int, k: int) -> str:
    return f"item_{t}_{k}"


def task_nums(t: int) -> tuple[int, int, int]:
    """(most, least, follow-up) task_num for screen t."""
    base = 3 * (t - 1)
    return base, base + 1, base + 2


def load() -> pd.DataFrame:
    return pd.read_csv(CSV, dtype=str, keep_default_na=False)


def stem() -> str:
    """The stem, read from the codebook and checked against every pick column."""
    import json

    cb = {r["variable"]: r["question"] for r in json.loads(CODEBOOK.read_text())}
    for t in range(1, N_TASKS + 1):
        for k in range(1, N_SLOTS + 1):
            assert cb[f"{PICK_Q[t]}_{k}"] == f"({t}/10) {STEM} - [Field-{t}.{k}_MAXDIFF]"
        assert cb[FOLLOW_Q[t]] == FOLLOW_UP
    return STEM


def derive(df: pd.DataFrame) -> pd.DataFrame:
    """One row per respondent with a design version: codes, picks and persona."""
    assert df.shape == (1590, 150)
    md_cols = [
        c
        for t in range(1, N_TASKS + 1)
        for c in (
            *(f"{t}.{k}_MAXDIFF" for k in range(1, N_SLOTS + 1)),
            *(f"{PICK_Q[t]}_{k}" for k in range(1, N_SLOTS + 1)),
            FOLLOW_Q[t],
        )
    ]
    none = df[df["vers_MAXDIFF"] == ""]
    assert len(none) == 81 and (none[md_cols] == "").all().all()
    df = df[df["vers_MAXDIFF"] != ""]
    assert len(df) == 1509

    out: dict[str, list[Any]] = defaultdict(list)
    layout: dict[str, tuple[str, ...]] = {}
    for _, r in df.iterrows():
        out["participant_id"].append(int(r["participant_id"]))
        out["vers_MAXDIFF"].append(int(r["vers_MAXDIFF"]))
        texts = tuple(r[f"{t}.{k}_MAXDIFF"] for t in range(1, 11) for k in range(1, 5))
        assert layout.setdefault(r["vers_MAXDIFF"], texts) == texts, "version != layout"
        for t in range(1, N_TASKS + 1):
            items = [r[f"{t}.{k}_MAXDIFF"] for k in range(1, N_SLOTS + 1)]
            assert len(set(items)) == N_SLOTS and set(items) <= set(SLUGS)
            picks = [r[f"{PICK_Q[t]}_{k}"] for k in range(1, N_SLOTS + 1)]
            assert sorted(picks) == sorted([MOST, LEAST, "", ""]), (r["participant_id"], t)
            for k, text in enumerate(items, 1):
                out[item_var(t, k)].append(CODES[text])
            out[f"most_{t}"].append(picks.index(MOST) + 1)
            out[f"least_{t}"].append(picks.index(LEAST) + 1)
            out[f"impact_{t}"].append(IMPACT[r[FOLLOW_Q[t]]])
        for field, src in PERSONA.items():
            value = r[src]
            out[field].append("" if value in NON_ANSWERS else value)
    return pd.DataFrame(out)


def arm_question(which: str, items: list[str]) -> str:
    options = "; ".join(f'{k} means "{text}"' for k, text in enumerate(items, 1))
    return f'{STEM} Report only the option you chose as "{which}". {options}.'


def build_arms(wide: pd.DataFrame) -> list[dict[str, Any]]:
    """One arm per distinct ordered four actually shown, with its screens' questions."""
    by_text = {code: shown(text) for text, code in CODES.items()}
    slug = {code: SLUGS[text] for text, code in CODES.items()}
    screens: dict[tuple[int, ...], set[int]] = defaultdict(set)
    for t in range(1, N_TASKS + 1):
        cols = [item_var(t, k) for k in range(1, N_SLOTS + 1)]
        for tup in wide[cols].itertuples(index=False):
            screens[tuple(int(c) for c in tup)].add(t)
    arms = []
    for num, tup in enumerate(sorted(screens)):
        items = [by_text[c] for c in tup]
        overrides: dict[int, dict[str, str]] = {}
        for t in sorted(screens[tup]):
            most, least, _ = task_nums(t)
            overrides[most] = {"outcome_question": arm_question(MOST, items)}
            overrides[least] = {"outcome_question": arm_question(LEAST, items)}
        arms.append(
            {
                "raw_values": {item_var(1, k): c for k, c in enumerate(tup, 1)},
                "condition_num": num,
                "factors": {f"item_{k}": slug[c] for k, c in enumerate(tup, 1)},
                "text": STEM + "\n" + "\n".join(items),
                "items": overrides,
            }
        )
    return arms


def build_outcomes() -> list[dict[str, Any]]:
    outcomes = []
    for t in range(1, N_TASKS + 1):
        most, least, follow = task_nums(t)
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
        outcomes.append(
            {
                "var": f"impact_{t}",
                "task_num": follow,
                "question": FOLLOW_UP,
                "scale": {
                    "min": 1,
                    "max": 3,
                    "min_label": "None of these would impact how much meat I eat",
                    "mid_label": "Some of these would impact how much meat I eat",
                    "max_label": "All of these would impact how much meat I eat",
                },
                "response_recode": {1: 1, 2: 2, 3: 3},
                "condition_vars": cvars,
            }
        )
    return outcomes


NOTES = """\
McBey, Martinez Sanchez, Horgan, Macdiarmid & McCormick, "Perceived effectiveness of
25 interventions and policies designed to reduce meat consumption", Food Quality and
Preference 135 (2026) 105693, doi:10.1016/j.foodqual.2025.105693. Zenodo record
18547379 v1.1 (doi:10.5281/zenodo.18547379), Qualtrics online survey of adults in
Scotland, Feb-Jul 2023, approximately nationally representative by age, gender,
education and ethnicity.

GENERATED by scripts/gen_zenodo18547379.py, which also writes the derived data file
maxdiff_coded.csv from the deposit's CSV. Every judgement is in that script's
docstring; in brief:

- MaxDiff: ten screens of four of 25 policies; pick the one "Most Likely" and the one
  "Least Likely" to make you eat less meat, then say whether all, some or none of the
  four would. Three outcomes per screen; the answer to the two picks is the item's
  screen position, 1-4, and the options are enumerated in the question (our words).
- 81 of 1,590 respondents have no design version and no MaxDiff data; left out.
- The deposit has no questionnaire. Wording is Qualtrics' own question-text row as the
  codebook reproduces it; item texts are the piped embedded data. "(t/10)" is dropped
  (sequence signposting). Added words, ours: 'Report only the option you chose as
  "Most Likely".' (or "Least Likely") and the '1 means "..."; 2 means ...' enumeration.
- Pick column k is item slot k by Qualtrics' own column naming, and reproduces the
  paper's overall ranking of the 25 (Appendix 3) at Spearman 0.996; no other pairing
  comes close. That slot k was screen position k is INFERRED from primacy and end
  effects in the picks; the deposit does not say whether Qualtrics shuffled the
  display. The riskiest judgement here.
- Design version is not in the row schema; it is recoverable from participant_id via
  the deposit (`vers_MAXDIFF`).
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
    stem()
    if wide is None:
        wide = derive(load())
    recipe = {
        "study_id": "zenodo18547379",
        "source": "zenodo",
        "title": (
            "Scottish meat consumption survey (Feb-Jul 2023): which policies would most "
            "and least make you eat less meat (best-worst scaling)"
        ),
        "data_file": DERIVED.name,
        "licence": (
            "CC BY 4.0 (cc-by-4.0), stated on Zenodo record 18547379 and read from "
            "https://zenodo.org/api/records/18547379 on 16 Nov 2026."
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
