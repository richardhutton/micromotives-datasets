#!/usr/bin/env python3
"""Derive the data files AND write the recipes for IP 9.9 — fertility after friends.

Waves 4 (2011) and 5 (2012), same allocation. Households were split: the
expected-fertility questions came either BEFORE (group 1, "Version A") or AFTER
(group 2, "Version B") a self-completion block about the respondent's close
friends, to test whether thinking about friends primes fertility intentions. Asked
of continuing respondents doing the self-completion, men 15-64 and women 15-45.

Built by rich's 9.24 ruling for order experiments: the condition is whether the
friends block had been asked earlier. The block is a LOOP over up to three
friends with answer-dependent fills, so it cannot be quoted whole. The "asked
earlier" condition quotes its opening question word-for-word (which everyone in
that arm met) and, for those who reported at least one close friend, the loop's own
opening instruction, introduced by an added narrating clause. Every quoted string
is asserted to occur in both waves' questionnaires.

Data decisions:
- the group comes from `{w}_hhsamp_ip` (`ff_fertw4`), joined on `hidp`;
- the A and B versions' answers merge into one variable per question;
- `prior` = 2 only where group 2 was routed into the friends block (`closenum`
  answered or don't-know), 1 for group 1, -8 otherwise (excluded); respondents
  answering with no household allocation are excluded (two, in wave 5).

    uv run python scripts/gen_ip_fertility.py --check --write --recipes
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

from micromotives_datasets.sources import spss

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[1]
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"
PDF = REPO / "data" / "raw" / "ukds_6849" / "mrdoc" / "pdf"
OUT = REPO / "data" / "raw" / "ukds_6849"
WAVES = {"d": (4, 2011), "e": (5, 2012)}

FRIENDS_OPEN = (
    "Here are a few questions about your friends. How many close friends would you say you "
    "have? Enter number"
)
LOOP_OPEN = (
    "Thinking of up to three of your closest friends, we would like to ask some questions "
    "about each of them in turn. None of the things we would like to know would allow us to "
    "identify your friend. Don't worry about the order which you tell us about them."
)
Q_ANY = "Do you think you will have any (more) children?"
# Wave 4 prints Version B as "... have and (more) children?" -- almost certainly a
# specification typo, but the questionnaire is the authority on wording, so those
# rows carry it as printed.
Q_ANY_W4_B = "Do you think you will have and (more) children?"
# On the web the friends question ends at "have?"; "Enter number" is a box label.
FRIENDS_OPEN_WEB = (
    "Here are a few questions about your friends. How many close friends would you say you have?"
)
Q_HOW_MANY = "How many (more) children do you think you will have? Enter number."
ANY_OPTIONS = ["Yes", "Self/partner currently pregnant", "No"]

PERSONA = (
    "dvage",
    "sex",
    "gor_dv",
    "jbstat",
    "hiqual_dv",
    "mastat_dv",
    "racel_dv",
    "nchild_dv",
)


def person_hash(pidp: int) -> str:
    """Same construction as `scripts/build_profiles.py`. Never the raw `pidp`."""
    return "ip_" + hashlib.sha256(f"ukds6849:{pidp}".encode()).hexdigest()[:12]


def derived_name(wave: int) -> str:
    return f"fertility_w{wave}-derived.sav"


def derive(w: str) -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    wave, year = WAVES[w]
    ind = spss.read(STATA / f"{w}_indresp_ip.dta")
    hh = spss.read(STATA / f"{w}_hhsamp_ip.dta").df
    hh = hh[[f"{w}_hidp", f"{w}_ff_fertw4"]].rename(columns={f"{w}_ff_fertw4": "grp"})
    df = ind.df.merge(hh, on=f"{w}_hidp", how="left", validate="many_to_one")
    grp = df["grp"].fillna(-9)
    out = pd.DataFrame({"person": [person_hash(int(p)) for p in df["pidp"]]})
    for q in ("lchmor", "lchmorn"):
        out[q] = np.where(
            grp == 1, df[f"{w}_{q}_a"], np.where(grp == 2, df[f"{w}_{q}_b"], -8.0)
        ).astype(float)
    closenum = df[f"{w}_closenum"]
    routed_friends = (closenum >= 0) | closenum.isin([-1, -2])
    out["prior"] = np.where(grp == 1, 1.0, np.where((grp == 2) & routed_friends, 2.0, -8.0))
    out["friends_loop"] = np.where(closenum > 0, 1.0, 0.0)
    out["indmode"] = df[f"{w}_indmode"].to_numpy()
    for v in PERSONA:
        out[v] = df[f"{w}_{v}"].to_numpy()
    out["wave"] = wave
    out["year"] = year
    labels: dict[str, dict[float, str]] = {}
    for v in PERSONA:
        got = ind.value_labels.get(f"{w}_{v}")
        if got:
            labels[v] = dict(got)
    return out, labels


def check(w: str) -> int:
    """Version A answers outside group 1, or B outside group 2. Must be 0."""
    ind = spss.read(STATA / f"{w}_indresp_ip.dta").df
    hh = spss.read(STATA / f"{w}_hhsamp_ip.dta").df[[f"{w}_hidp", f"{w}_ff_fertw4"]]
    df = ind.merge(hh.rename(columns={f"{w}_ff_fertw4": "grp"}), on=f"{w}_hidp", how="left")
    grp = df["grp"]
    bad = 0
    # indresp carries its own copy of the allocation: the join must agree with it.
    if f"{w}_ff_fertw4" in df:
        own = df[f"{w}_ff_fertw4"]
        both = (own > 0) & (grp > 0)
        disagree = int((own[both] != grp[both]).sum())
        print(
            f"  wave {WAVES[w][0]}: joined allocation vs indresp's copy, {int(both.sum())} "
            f"compared, {disagree} disagree"
        )
        bad += disagree
    for version, g in (("a", 1), ("b", 2)):
        answered = df[f"{w}_lchmor_{version}"] >= 0
        bad += int((answered & (grp > 0) & (grp != g)).sum())
    unallocated = int(
        ((df[f"{w}_lchmor_a"] >= 0) | (df[f"{w}_lchmor_b"] >= 0)).mul(~(grp > 0)).sum()
    )
    d, _ = derive(w)
    print(
        f"  wave {WAVES[w][0]}: {bad} answers in the other version; {unallocated} answering "
        f"with no allocation (excluded); prior {d['prior'].value_counts().sort_index().to_dict()}"
    )
    return bad


def _text(wave: int) -> str:
    raw = subprocess.run(
        ["pdftotext", str(PDF / f"6849_ip_wave_{wave}_questionnaires.pdf"), "-"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return " ".join(raw.split())


def write_recipes() -> None:
    for wave, _ in WAVES.values():
        t = _text(wave)
        for s in (FRIENDS_OPEN, FRIENDS_OPEN_WEB, LOOP_OPEN, Q_ANY, Q_HOW_MANY, *ANY_OPTIONS):
            assert s in t, (wave, s)
    assert Q_ANY_W4_B in _text(4)
    base = (REPO / "recipes" / "ukds_6849_identity_w2.yaml").read_text()
    lic = base.split("data_file:")[1].split("\n", 1)[1].split("comparable_to_socsci210")[0]
    persona = base.split("missing_codes:")[1]
    not_before = (
        'You had not been asked the questions that begin "Here are a few questions about your '
        'friends." earlier in the interview.'
    )
    loop = (
        "[IF friends_loop=1 INSERT: You were then asked about each of up to three of your "
        f'closest friends, introduced with: "{LOOP_OPEN}"]'
    )
    friends = f'[IF indmode=1 INSERT: "{FRIENDS_OPEN}"; IF indmode=3 INSERT: "{FRIENDS_OPEN_WEB}"]'
    before = f"Earlier in the interview you were asked: {friends} {loop}"
    opts = " ".join(f'{i} "{o}"' for i, o in enumerate(ANY_OPTIONS, 1))
    any_q = f"{Q_ANY} {opts}"
    for wave, _ in WAVES.values():
        items_b = ""
        if wave == 4:
            typo_q = json.dumps(f"{Q_ANY_W4_B} {opts}", ensure_ascii=False)
            items_b = f"""      items:
        0:
          outcome_question: {typo_q}
"""
        notes = f"""University of Essex, Institute for Social and Economic Research, "Understanding
Society: Innovation Panel, Waves 1-17, 2008-2024", UK Data Service SN 6849.
Experiment 9.9 in the Innovation Panel User Guide ("Context effects in fertility
decisions"); wave {wave}, the wave 4 allocation repeated at wave 5. GENERATED by
`scripts/gen_ip_fertility.py --recipes`; every quoted string is asserted to occur in
both waves' questionnaires. Do not edit by hand. The User Guide cites no publication.

A PRIMING ORDER EXPERIMENT, BUILT ON WHAT WAS ASKED BEFORE (rich's 9.24 ruling). The
expected-fertility questions came before (group 1) or after (group 2) a self-completion
block about the respondent's close friends. Asked of continuing respondents doing the
self-completion, men 15-64 and women 15-45: a small study.

THE CONDITION IS NARRATED. Group 1: "You had not been asked the questions that begin
"..." earlier in the interview." Group 2: "Earlier in the interview you were asked:"
with the friends block's opening question quoted. The block then loops over up to
three friends with answer-dependent fills ("[first/second/third]", "[him/her]"), so it
cannot be quoted whole; for respondents who reported at least one close friend the
condition adds "You were then asked about each of up to three of your closest friends,
introduced with:" and the loop's own opening instruction, word-for-word. Those framing
clauses are ADDED (docs/CONVENTIONS.md, "Narrating what the respondent did"), resolved per
row on `friends_loop`. Group 2 respondents not routed into the friends block are
excluded, as are respondents who answered with no household allocation.

OUTCOMES: "Do you think you will have any (more) children?" (nominal: yes / self or
partner currently pregnant / no) and, for those answering yes, "How many (more)
children do you think you will have?" (a count, 1-15: the range is ours, the
instrument gives only a two-digit box). Versions A and B use the same wording, except
that the wave 4 specification prints Version B as "Do you think you will have and
(more) children?" -- almost certainly a typo, but the questionnaire is the authority,
so wave 4 Version B rows carry it as printed (independent checker). The friends
question's "Enter number" is a box label on the web, where the quoted question ends at
"have?"; resolved per row on `indmode`.
In this study no group-2 respondent who skipped the friends block answered the
fertility questions, so the exclusion removes no rows and is not exercised here.

`person` is a hash of `pidp`, the same construction as every Innovation Panel build;
most respondents answered both waves, under one id. Allocated by household."""
        s = f"""study_id: ukds_6849
source: innovation_panel
title: "Understanding Society Innovation Panel, experiment 9.9: expected fertility asked before or
  after questions about friends (wave {wave})"
data_file: {derived_name(wave)}
{lic}comparable_to_socsci210: false
experiment: fertility_w{wave}
participant_id_var: person

notes: {json.dumps(notes, ensure_ascii=False)}

condition:
  source_var: prior
  factors: [friends_asked_earlier]
  arms:
    - raw: 1
      condition_num: 0
      factors: {{friends_asked_earlier: "no"}}
      text: {json.dumps(not_before, ensure_ascii=False)}
    - raw: 2
      condition_num: 1
      factors: {{friends_asked_earlier: "yes"}}
      text: {json.dumps(before, ensure_ascii=False)}
{items_b}
outcomes:
  - var: lchmor
    task_num: 0
    question: {json.dumps(any_q, ensure_ascii=False)}
    scale: {{min: 1, max: 3, nominal: true}}
  - var: lchmorn
    task_num: 1
    question: {json.dumps(Q_HOW_MANY, ensure_ascii=False)}
    scale: {{min: 1, max: 15}}

response_recode: {{{", ".join(f"{i}: {i}" for i in range(1, 16))}}}

respondent_vars: [friends_loop, indmode]

missing_codes:{persona}"""
        (REPO / "recipes" / f"ukds_6849_fertility_w{wave}.yaml").write_text(s)
        print(f"  wrote recipes/ukds_6849_fertility_w{wave}.yaml")
    assert re.search(r"\[", not_before) is None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify version routing")
    ap.add_argument("--write", action="store_true", help="write the derived .sav files")
    ap.add_argument("--recipes", action="store_true", help="regenerate the two recipes")
    args = ap.parse_args()
    if args.check and sum(check(w) for w in WAVES):
        raise SystemExit("answers in the other version")
    for w, (wave, _) in WAVES.items():
        df, labels = derive(w)
        usable = df["prior"] > 0
        n = int((df.loc[usable, ["lchmor", "lchmorn"]] > 0).sum().sum())
        print(f"wave {wave}: {n:,} answers from respondents with a known exposure")
        if args.write:
            narrow = df.copy()
            pyreadstat.write_sav(
                narrow, str(OUT / derived_name(wave)), variable_value_labels=labels
            )
    if args.recipes:
        write_recipes()


if __name__ == "__main__":
    main()
