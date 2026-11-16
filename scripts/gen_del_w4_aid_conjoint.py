#!/usr/bin/env python3
"""Write the two DEL panel wave 4 aid-project conjoint recipes (tracker row W4_split_sample).

    recipes/del_panel_w4_aid_conjoint_8attr.yaml   split_sample == 1, all eight attributes
    recipes/del_panel_w4_aid_conjoint_6attr.yaml   split_sample == 2, six (no need, no
                                                   effectiveness)

Every instrument string is parsed out of the fielded questionnaire,
DEL_Panel_GreatBritain_Wave_4_2022_Survey.docx, and the two recipes are written whole from
this file, so `tests/test_gen_del_w4_aid_conjoint.py` can hold them byte-identical to what
is derived here. The persona block, licence and person id are read from
`recipes/del_panel_w4_extreme_weather.yaml` (same .sav), so they cannot drift apart.

    uv run python scripts/gen_del_w4_aid_conjoint.py           # compare, exit 1 on a diff
    uv run python scripts/gen_del_w4_aid_conjoint.py --write   # rewrite both recipes

Why two recipes and not one: a template declares one set of dimensions, and the arms differ
in which attributes exist and in which variables hold them (`scr_*_attrK_list_*` against
`scr_*_attrK_M_*`), so one template cannot carry both. The wave 3 donate/petition split is
the precedent.
"""

from __future__ import annotations

import argparse
import functools
import html
import re
import zipfile
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "del"
DOCX = RAW / "DEL_Panel_GreatBritain_Wave_4_2022_Survey.docx"
PERSONA_FROM = REPO / "recipes" / "del_panel_w4_extreme_weather.yaml"
RECIPES = {
    "8attr": REPO / "recipes" / "del_panel_w4_aid_conjoint_8attr.yaml",
    "6attr": REPO / "recipes" / "del_panel_w4_aid_conjoint_6attr.yaml",
}

# The questionnaire's attribute numbers (attrK_text / attrK_list), our dimension name for
# each, and our short level names. The names are ours and appear only in factors; the
# words a respondent read are parsed from the docx below.
ATTRS: dict[int, tuple[str, list[str]]] = {
    1: (
        "purpose",
        [
            "education",
            "health",
            "growth_jobs",
            "wash",
            "social_protection",
            "infrastructure",
            "food_security",
            "peace_security",
            "environment_climate",
            "gender_equality",
        ],
    ),
    2: ("region", ["east_asia_pacific", "latam_caribbean", "mena", "south_asia", "ssa"]),
    3: ("poverty", ["pct5", "pct10", "pct20", "pct40", "pct80"]),
    4: ("ties", ["historical_cultural", "diplomatic_strategic", "economic", "none"]),
    5: ("effectiveness", ["very", "effective", "moderately", "not_very"]),
    6: ("channel", ["uk_aid_agency", "international_orgs", "ngos", "private_sector"]),
    7: ("institutions", ["strong", "moderate", "weak"]),
    8: ("conditions", ["social_policy", "economic_policy", "democracy_rights", "none"]),
}

# Which attributes each arm showed, in the order its `format(...)` call fills the table,
# and the variable holding each one's level for screen s, project p. From the script's
# `[scr_1_attr1_list_A:attr1_list]` (arm 1) and `[scr_1_attr3_4_A:attr4_list]` (arm 2:
# the arm's 3rd row, the questionnaire's attribute 4).
ARMS: dict[str, dict[str, Any]] = {
    "8attr": {
        "split": 1,
        "attrs": [1, 2, 3, 4, 5, 6, 7, 8],
        "var": lambda s, k, i, p: f"scr_{s}_attr{k}_list_{p}",
        "outcome": "Q1_{s}",
        "label": "Shown All attributes",
    },
    "6attr": {
        "split": 2,
        "attrs": [1, 2, 4, 6, 7, 8],
        "var": lambda s, k, i, p: f"scr_{s}_attr{i}_{k}_{p}",
        "outcome": "Q1_conj2_{s}",
        "label": "Shown All attributes MINUS need & effective",
    },
}


def questionnaire_lines() -> list[str]:
    """The docx's paragraphs, as plain text (one questionnaire line each)."""
    xml = zipfile.ZipFile(DOCX).read("word/document.xml").decode("utf-8")
    return [html.unescape(re.sub(r"<[^>]+>", "", p)) for p in xml.split("</w:p>")]


def _one(lines: list[str], pattern: str) -> re.Match[str]:
    hits = [m for m in (re.search(pattern, ln) for ln in lines) if m]
    if len(hits) != 1:
        raise SystemExit(f"expected one line matching {pattern!r}, found {len(hits)}")
    return hits[0]


def _list(lines: list[str], name: str) -> dict[int, str]:
    """A `[[name]]` option list: code -> text, trailing whitespace stripped."""
    start = lines.index(f"[[{name}]]")
    out: dict[int, str] = {}
    for ln in lines[start + 1 :]:
        m = re.match(r"\s*<(\d+)>\s*(.*?)\s*$", ln)
        if not m:
            break
        out[int(m.group(1))] = m.group(2)
    return out


def instrument() -> dict[str, Any]:
    """Every string the recipes use, read from the questionnaire, with the fills resolved."""
    lines = questionnaire_lines()
    # Country fills. `qcountry.set(2)`; the only codes are <2> Britain and, for
    # qcountryname, <2> British. GB was the only country in this wave's script.
    _one(lines, r"^qcountry\.set\(2\)\s*$")
    country = _one(lines, r"^\[qcountry if .*COUNTRY$")
    country_opts = lines[lines.index(country.string) + 1]
    assert country_opts.strip() == "<2> Britain", country_opts
    cname = _one(lines, r"^\[qcountryname\] .*COUNTRY Name$")
    cname_opts = lines[lines.index(cname.string) + 1]
    assert cname_opts.strip() == "<2> British", cname_opts

    intro = _one(lines, r"^<<b>(On the next few pages, .*)</b>>$").group(1)
    assert "$qcountryname" in intro
    intro = intro.replace("$qcountryname", "British")
    prefix = "On the next few pages, you"
    assert intro.startswith(prefix)
    intro = "You" + intro[len(prefix) :]

    headings: dict[int, str] = {}
    for k in ATTRS:
        m = _one(lines, rf"^attr{k}_text = (.*)$")
        expr = m.group(1).strip()
        expr = expr.replace('" + qcountry.response_text + "', "Britain")
        assert expr.startswith('"') and expr.endswith('"') and expr.count('"') == 2, expr
        headings[k] = expr[1:-1]

    question = _one(lines, r'^Q1_question_text= _\("(.*)"\)$').group(1)
    options = _list(lines, "options_list")
    assert options == {1: "Project A", 2: "Project B"}, options
    levels = {k: _list(lines, f"attr{k}_list") for k in ATTRS}
    for k, (_, names) in ATTRS.items():
        assert len(levels[k]) == len(names), (k, levels[k])

    # The arm-2 table really is attributes 1, 2, 4, 6, 7, 8 (its format() call).
    fmt = _one(lines, r"^screen1_table_conj2 = format\(table_template_conj2, (.*)\)$").group(1)
    shown = re.findall(r"attr(\d)_text", fmt)
    assert [int(x) for x in shown] == ARMS["6attr"]["attrs"], shown
    fmt1 = _one(lines, r"^screen1_table = format\(table_template, (.*)\)$").group(1)
    assert [int(x) for x in re.findall(r"attr(\d)_text", fmt1)] == ARMS["8attr"]["attrs"]
    # The attribute ROW ORDER is shuffled per respondent and kept in a page variable that
    # the deposit does not contain (see notes); the generator asserts the shuffle exists.
    _one(lines, r"^attr_order = random_shuffle\(\[1,2,3,4,5,6,7,8\]\)$")
    _one(lines, r"^attr_order_conj2 = random_shuffle\(\[1,2,3,4,5,6\]\)$")
    return {
        "intro": intro,
        "headings": headings,
        "question": question,
        "options": options,
        "levels": levels,
    }


def _project(arm: str, p: str, headings: dict[int, str]) -> str:
    parts = [f'{headings[k]}, "{{{ATTRS[k][0]}_{p}}}"' for k in ARMS[arm]["attrs"]]
    return f"Project {p}: " + "; ".join(parts) + "."


def build(arm: str) -> dict[str, Any]:
    ins = instrument()
    spec = ARMS[arm]
    text = (
        f"{ins['intro']} You were then shown two projects. "
        f"{_project(arm, 'A', ins['headings'])} {_project(arm, 'B', ins['headings'])}"
    )
    dims: dict[str, Any] = {}
    for p in ("A", "B"):
        for i, k in enumerate(spec["attrs"], start=1):
            name, slugs = ATTRS[k]
            dims[f"{name}_{p}"] = {
                "var": spec["var"](1, k, i, p),
                "levels": {
                    code: {"level": slugs[code - 1], "text": txt}
                    for code, txt in ins["levels"][k].items()
                },
            }

    def screen_vars(s: int) -> list[str]:
        return [
            spec["var"](s, k, i, p)
            for p in ("A", "B")
            for i, k in enumerate(spec["attrs"], start=1)
        ]

    # The cells actually drawn (ConditionTemplate.cells_drawn): the full product is
    # 3.7e10 cells (arm 1) or 9.2e7 (arm 2), too large to expand, so the recipe lists
    # the drawn ones, read from the deposit. Codes only; the words stay in `levels`.
    df = _deposit()
    df = df[df.split_sample == spec["split"]]
    drawn = {
        tuple(int(c) for c in codes)
        for s in (1, 2, 3)
        for codes in df[screen_vars(s)].itertuples(index=False)
    }
    o = ins["options"]
    question = f'{ins["question"]} 1 means "{o[1]}"; 2 means "{o[2]}".'
    outcomes: list[dict[str, Any]] = []
    for s in (1, 2, 3):
        out: dict[str, Any] = {
            "var": spec["outcome"].format(s=s),
            "task_num": s - 1,
            "question": question,
            "scale": {"min": 1, "max": 2, "nominal": True},
        }
        if s > 1:
            out["condition_vars"] = screen_vars(s)
        outcomes.append(out)

    persona = yaml.safe_load(PERSONA_FROM.read_text())
    return {
        "study_id": "del",
        "source": "dataverse",
        "title": TITLES[arm],
        "data_file": "DEL_Panel_GreatBritain_Wave_4_2022_Data.sav",
        "licence": persona["licence"],
        "comparable_to_socsci210": False,
        "experiment": f"panel_w4_aid_conjoint_{arm}",
        "participant_id_var": persona["participant_id_var"],
        "notes": NOTES.format(
            arm=arm,
            other=("6attr" if arm == "8attr" else "8attr"),
            split=spec["split"],
            label=spec["label"],
            n=N[arm],
        ),
        "condition": {
            "considered_and_rejected": {
                "split_sample": "the assignment between the two recipes (1 = eight "
                "attributes, del_panel_w4_aid_conjoint_8attr; 2 = six, "
                "del_panel_w4_aid_conjoint_6attr); within a recipe it is constant, and "
                "the attribute set it decides is in the text itself",
            },
            "template": {
                "sparse": True,
                "text": text,
                "dimensions": dims,
                "cells_drawn": [_Flow(c) for c in sorted(drawn)],
            },
        },
        "outcomes": outcomes,
        "response_recode": {1: 1, 2: 2},
        "missing_codes": [8, 9],
        "persona_label_rewrite": persona["persona_label_rewrite"],
        "persona_map": persona["persona_map"],
        "persona_missing": persona["persona_missing"],
    }


TITLES = {
    "8attr": "Development Engagement Lab, Panel Great Britain wave 4 (2022): aid project "
    "conjoint, eight attributes",
    "6attr": "Development Engagement Lab, Panel Great Britain wave 4 (2022): aid project "
    "conjoint, six attributes (no need, no effectiveness)",
}
N = {"8attr": "3,994 people, 11,982 rows", "6attr": "4,014 people, 12,042 rows"}

NOTES = """\
Hudson, Jennifer; Hudson, David; Morini, Paolo; Oh, Soomin, 2024, "DEL Panel 2022",
https://doi.org/10.7910/DVN/WZPNNU, Harvard Dataverse; DEL_Panel_GreatBritain_Wave_4_
2022_Data.sav. YouGov online panel, wave 4, fielded 30 September - 28 October 2022,
n = 8,008 adults in Great Britain (the deposit's Readme). GENERATED by
scripts/gen_del_w4_aid_conjoint.py; edit that, never this file.

THE DESIGN. A paired-profile conjoint about UK aid projects (tracker row W4_split_sample,
catalogued as "Climate aid conjoint"; it is not about climate aid: climate is one of ten
project purposes). `split_sample = panman.assign_treatment(2,[],"sample_alloc")`, not
stratified, sends 3,994 people to an eight-attribute version and 4,014 to a six-attribute
version that drops attribute 3 (extreme poverty, "need") and attribute 5 (typical
effectiveness): the script's labels are "Shown All attributes" / "Shown All attributes
MINUS need & effective". This recipe is arm {split}, "{label}" ({n}); the other arm is
del_panel_w4_aid_conjoint_{other}.yaml. Each person sees three screens. Each screen is a
table of two projects, A and B, one row per attribute, each level drawn uniformly and
independently per project and screen, redrawn until the six profiles a person sees are all
different. Every level of every attribute is recorded per person, screen and project
(`scr_<s>_attr<k>_list_<A|B>` for arm 1, `scr_<s>_attr<i>_<k>_<A|B>` for arm 2, where k is
the questionnaire's attribute number). Everyone answered all three screens; no one in one
arm has a value in the other arm's variables; no answer is Skipped.

WHAT IS TRANSCRIBED (DEL_Panel_GreatBritain_Wave_4_2022_Survey.docx, conjoint module).
Level texts: `attr1_list` .. `attr8_list`, word-for-word (trailing spaces dropped; the
.sav value labels agree but are truncated by SPSS at 120 characters). Row headings: the
script's `attr1_text` .. `attr8_text`, which fill the table's "Attribute" column, so unlike
wave 3 the headings were on screen and ARE rendered. Two fills resolved from the script's
own first lines (`qcountry.set(2)`, whose only codes are <2> "Britain" and, for
qcountryname, <2> "British"): attribute 4's heading reads "Nature of relationship between
Britain and recipient country", and the intro reads "the British government". Intro: the
`intro` page, word-for-word, less its opening "On the next few pages, " (survey mechanics
describing the screen sequence; docs/CONVENTIONS.md, "Sequence signposting"), so "you"
becomes "You". Question: `Q1_question_text`, "Which of the two aid projects do you support
more?", options <1> "Project A", <2> "Project B", in fixed order.

ATTRIBUTE ORDER: NOT RECORDED, AND NOT CLAIMED (the riskiest judgement here). The table
is built by `attr_order = random_shuffle([1,2,3,4,5,6,7,8])` (arm 2: `[1..6]`), drawn once
per person on `p_table` and used for all three screens. It is a script variable, not a
question, and is not in the deposit (all 403 columns read: no order, position or table
column). So the rows' order cannot be reproduced (ledger 114, EFXNLX). As with wave 3 and
ledger 155, nothing is laid out as a table and no position word is used: each project is
narrated as heading, "level" pairs in the questionnaire's attribute order, which is the
script's numbering and not a claim about what came first. ADDED by us (docs/CONVENTIONS.md,
"Narrating what the respondent did"): "You were then shown two projects.", "Project A:",
"Project B:", the commas, semicolons and quotation marks, and the closing full stops. The
"Attribute" / "Project A" / "Project B" column headings are not otherwise rendered.

The arm's attribute count is never stated; the six-attribute arm's text simply has six
headings per project, which is exactly what its screen showed. Screen numbers ("PAIR n")
do not exist in this script; nothing cites a screen's position.

CELLS. The template's full product is 192,000 x 192,000 cells (arm 1) or 9,600 x 9,600
(arm 2), far too many to expand, so `cells_drawn` lists the cells the deposit actually
holds, codes only, read by the generator from the three screens' variables (arm 1: 11,982
screens, all different; arm 2: 12,042 screens, 12,041 different). Each arm's
`condition_num` is still its odometer index in the full product. QC rule 5 has no drawn
minimal pair for most factors here, so it renders one from the template instead.

OUTCOME. One outcome per screen (task_num 0-2, `Q1_1`..`Q1_3` / `Q1_conj2_1`..`_3`), the
same question each time; 1 = "Project A", 2 = "Project B", a forced choice. The options
are enumerated in the question ("1 means ...; 2 means ...", our words, the PZB01G and
wave 3 convention) because a nominal scale may not carry end labels. 8 "Skipped" and 9
"Not Asked" are labelled and never occur (not asked is blank in this file); declared so a
re-fetched deposit drops them.

WHAT CAME BEFORE. Everyone: the opening trackers and the cost-of-living experiment
(`CoLSplit`; split_sample is not stratified on it, and its cells hold 962-1,043 each).
The intro page is shown to both arms alike. Immediately after: the climate block (`action`).

PERSONA, PERSON ID AND LICENCE are read by the generator from
del_panel_w4_extreme_weather.yaml (same .sav): `GUNQID`, wave 4's own non-answer codes,
age read through its value labels (ledger 145; in this file age is a real age, -9/-8
labelled and absent).

REFERENCE. None found: no DEL publication of this conjoint's AMCEs was located (Nov
2026). The internal check is in tests/test_gen_del_w4_aid_conjoint.py: every level of
every attribute occurs on both sides in near-equal shares, no screen shows two identical
projects, and Project A / B shares are near 50%."""


@functools.cache
def _deposit() -> Any:
    import pyreadstat

    df, _ = pyreadstat.read_sav(str(RAW / "DEL_Panel_GreatBritain_Wave_4_2022_Data.sav"))
    return df


class _Flow(list):  # type: ignore[type-arg]
    """A list dumped on one line."""


class _Dumper(yaml.SafeDumper):
    pass


def _flow(dumper: yaml.SafeDumper, data: _Flow) -> yaml.Node:
    return dumper.represent_sequence("tag:yaml.org,2002:seq", list(data), flow_style=True)


_Dumper.add_representer(_Flow, _flow)


def _str(dumper: yaml.SafeDumper, data: str) -> yaml.Node:
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_Dumper.add_representer(str, _str)


def render(arm: str) -> str:
    return yaml.dump(build(arm), Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="rewrite both recipes")
    args = ap.parse_args()
    ok = True
    for arm, path in RECIPES.items():
        text = render(arm)
        if args.write:
            path.write_text(text, encoding="utf-8")
            print(f"wrote {path.relative_to(REPO)}")
        elif not path.exists() or path.read_text(encoding="utf-8") != text:
            ok = False
            print(f"DIFFERS: {path.relative_to(REPO)}")
        else:
            print(f"identical: {path.relative_to(REPO)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
