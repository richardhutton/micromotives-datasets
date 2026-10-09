#!/usr/bin/env python3
"""Derive the data file AND write the recipes for IP 9.47 — two ways of asking about caring.

Wave 17 (2024). Every respondent was asked both the existing Understanding Society
questions on informal care and a new "activity-based" set (hours a week on six
kinds of caring), one set early in the interview and the other late, by household
(`ff_careexpw17` in `q_hhsamp_ip`: 1 = activity-based late, 2 = activity-based
early). Built by rich's 9.24 ruling as two experiments, each conditioned on whether
the OTHER set had been asked earlier:

- `caring_activity_w17`: the six activity-hours answers (the computed total is not
  a question and is not built);
- `caring_existing_w17`: the existing set's single-answer items — cares for someone
  in the household, cares for someone outside it, and weekly hours band.
  "Who do you look after?" (code all that apply, filled with household members'
  names) and the relationship items are not built: the 9.43 checklist ruling, and
  their fills carry other people's names.

The recipes are GENERATED here, every quoted string asserted to occur in the
questionnaire. Mode variants are resolved per row: the web wording adds "If none,
just enter zero." to the activity stem and "Please exclude any help that you
provide as part of your job." to the outside-household question; Help text, behind
a link on the web and an interviewer prompt otherwise, is never rendered.

    uv run python scripts/gen_ip_caring.py --check --write --recipes
"""

from __future__ import annotations

import argparse
import hashlib
import json
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
QUEX = (
    REPO
    / "data"
    / "raw"
    / "ukds_6849"
    / "mrdoc"
    / "pdf"
    / "6849_innovation_panel_wave_17_questionnaire.pdf"
)
OUT = REPO / "data" / "raw" / "ukds_6849"
W, WAVE, YEAR = "q", 17, 2024
DERIVED = f"caring_w{WAVE}-derived.sav"

ACTIVITY = {
    "abcarhh": "Household activities (such as cooking, cleaning, laundry)",
    "abcarper": "Personal care (such as dressing, washing, medication)",
    "abcarprac": "Providing practical support (help getting around, finances, appointments)",
    "abcarsup": "Providing social and emotional support",
    "abcartrav": "Travelling to and from their home",
    "abcaroth": "Any other caring tasks",
}
STEM = (
    "Now think about anyone - either living with you or not living with you - who is sick, "
    "disabled or elderly whom you look after or give special help to. Typically, how many hours "
    "do you spend on the following care activities for them each week?"
)
STEM_WEB_EXTRA = "If none, just enter zero."
STEM_FIRST = (
    "Now think about anyone - either living with you or not living with you - who is sick, "
    "disabled or elderly whom you look after or give special help to."
)
AIDHH = (
    "Is there anyone living with you who is sick, disabled or elderly whom you look after or "
    "give special help to (for example, a sick, disabled or elderly relative, husband, wife or "
    "friend etc)?"
)
AIDXHH = (
    "Do you provide some regular service or help for any sick, disabled or elderly person not "
    "living with you?"
)
AIDXHH_WEB_EXTRA = "Please exclude any help that you provide as part of your job."
NAIDXHH = "How many people do you care for?"
AIDHRS = (
    "Now thinking about everyone who you look after or provide help for, both those living with "
    "you and not living with you - in total, how many hours do you spend each week looking after "
    "or helping them?"
)
AIDHRS_OPTIONS = [
    "0 - 4 hours per week",
    "5 - 9 hours per week",
    "10 - 19 hours per week",
    "20 - 34 hours per week",
    "35 - 49 hours per week",
    "50 - 99 hours per week",
    "100 or more hours per week/continuous care",
    "Varies under 20 hours",
    "Varies 20 hours or more",
    "Other",
]
EXISTING = ("aidhh", "aidxhh", "aidhrs")
NOT_ROUTED = -8

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


def _asked(df: pd.DataFrame, col: str) -> pd.Series:
    return (df[col] >= 0) | df[col].isin([-1, -2])


def derive() -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    ind = spss.read(STATA / f"{W}_indresp_ip.dta")
    hh = spss.read(STATA / f"{W}_hhsamp_ip.dta").df
    hh = hh[[f"{W}_hidp", f"{W}_ff_careexpw17"]].rename(columns={f"{W}_ff_careexpw17": "grp"})
    df = ind.df.merge(hh, on=f"{W}_hidp", how="left", validate="many_to_one")
    grp = df["grp"].fillna(-9)
    out = pd.DataFrame({"person": [person_hash(int(p)) for p in df["pidp"]]})
    activity_early, existing_early = grp == 2, grp == 1
    for v in ACTIVITY:
        out[v] = np.where(
            activity_early, df[f"{W}_{v}ear"], np.where(existing_early, df[f"{W}_{v}lat"], -8.0)
        ).astype(float)
    for v in EXISTING:
        out[v] = np.where(
            existing_early, df[f"{W}_{v}ear"], np.where(activity_early, df[f"{W}_{v}lat"], -8.0)
        ).astype(float)
    out["aidhrs"] = out["aidhrs"].replace(97.0, 10.0)
    # Exposure: what was actually asked earlier, not what was allocated.
    saw_existing_early = _asked(df, f"{W}_aidxhhear")
    saw_activity_early = _asked(df, f"{W}_abcarhhear")
    out["prior_activity"] = np.where(
        activity_early, 1.0, np.where(existing_early & saw_existing_early, 2.0, -8.0)
    )
    out["prior_existing"] = np.where(
        existing_early, 1.0, np.where(activity_early & saw_activity_early, 2.0, -8.0)
    )
    # Was "Is there anyone living with you ..." asked in the early existing block?
    # "Is there anyone living with you ..." is asked only in households of more than
    # one; anything but -8 (inapplicable) in either module means it was in this
    # person's existing set -- including -9 missing (independent checker).
    in_universe = (df[f"{W}_aidhhear"] != -8) | (df[f"{W}_aidhhlat"] != -8)
    out["hhmulti"] = np.where(in_universe & (grp > 0), 1.0, 0.0)
    out["indmode"] = df[f"{W}_indmode"].to_numpy()
    for v in PERSONA:
        out[v] = df[f"{W}_{v}"].to_numpy()
    out["wave"] = WAVE
    out["year"] = YEAR
    labels: dict[str, dict[float, str]] = {}
    for v in PERSONA:
        got = ind.value_labels.get(f"{W}_{v}")
        if got:
            labels[v] = dict(got)
    return out, labels


def check() -> int:
    """Answers in a module the allocation says was not used. Must be 0."""
    ind = spss.read(STATA / f"{W}_indresp_ip.dta").df
    hh = spss.read(STATA / f"{W}_hhsamp_ip.dta").df[[f"{W}_hidp", f"{W}_ff_careexpw17"]]
    df = ind.merge(hh.rename(columns={f"{W}_ff_careexpw17": "grp"}), on=f"{W}_hidp", how="left")
    bad = 0
    for v, early_grp in [(a, 2) for a in ACTIVITY] + [(e, 1) for e in EXISTING]:
        allocated = df["grp"] > 0
        bad += int((allocated & (df["grp"] != early_grp) & (df[f"{W}_{v}ear"] >= 0)).sum())
        bad += int((allocated & (df["grp"] == early_grp) & (df[f"{W}_{v}lat"] >= 0)).sum())
    d, _ = derive()
    print(
        f"  {bad} answers in a module the allocation did not use; prior_activity "
        f"{d['prior_activity'].value_counts().sort_index().to_dict()}, prior_existing "
        f"{d['prior_existing'].value_counts().sort_index().to_dict()}"
    )
    return bad


def _by_mode(capi: str, web: str) -> str:
    if capi == web:
        return capi
    for bad in "[];":
        assert bad not in capi + web, bad
    return f"[IF indmode=1 INSERT: {capi}; IF indmode=2 INSERT: {capi}; IF indmode=3 INSERT: {web}]"


def write_recipes() -> None:
    t = " ".join(
        subprocess.run(
            ["pdftotext", str(QUEX), "-"], capture_output=True, text=True, check=True
        ).stdout.split()
    )
    for s in (
        STEM,
        STEM_WEB_EXTRA,
        AIDHH,
        AIDXHH,
        AIDXHH_WEB_EXTRA,
        NAIDXHH,
        AIDHRS,
        *ACTIVITY.values(),
        *[o.split("/")[0] for o in AIDHRS_OPTIONS],
    ):
        assert s in t, s
    base = (REPO / "recipes" / "ukds_6849_identity_w2.yaml").read_text()
    lic = base.split("data_file:")[1].split("\n", 1)[1].split("comparable_to_socsci210")[0]
    persona = base.split("missing_codes:")[1]
    stem = _by_mode(STEM, f"{STEM} {STEM_WEB_EXTRA}")
    aidxhh = _by_mode(f'"{AIDXHH}"', f'"{AIDXHH} {AIDXHH_WEB_EXTRA}"')
    activity_list = " / ".join(f'"{x}"' for x in ACTIVITY.values())

    specs = {
        "activity": {
            "prior": "prior_activity",
            "sibling": "existing",
            "other": "existing_questions",
            "not_before": (
                "You had not been asked the questions that begin "
                f'[IF hhmulti=1 INSERT: "{AIDHH}"; IF hhmulti=0 INSERT: "{AIDXHH}"] '
                "earlier in the interview."
            ),
            "before": (
                f'Earlier in the interview you were asked: [IF hhmulti=1 INSERT: "{AIDHH}" and] '
                f"{aidxhh}"
            ),
            "what": "the six activity-hours answers",
        },
        "existing": {
            "prior": "prior_existing",
            "sibling": "activity",
            "other": "activity_questions",
            "not_before": f'You had not been asked the questions that begin "{STEM_FIRST}" earlier in the interview.',
            "before": f'Earlier in the interview you were asked: "{stem}" for each of: {activity_list}',
            "what": "the existing questions' single-answer items",
        },
    }
    for key, sp in specs.items():
        notes = f"""University of Essex, Institute for Social and Economic Research, "Understanding
Society: Innovation Panel, Waves 1-17, 2008-2024", UK Data Service SN 6849.
Experiment 9.47 in the Innovation Panel User Guide ("Identification of informal
caregiving"); wave 17 (2024). GENERATED by `scripts/gen_ip_caring.py --recipes`; every
quoted string asserted to occur in the questionnaire. Do not edit by hand. The User Guide
cites no publication. `ukds_6849_caring_{sp["sibling"]}_w17.yaml` is the other half.

AN ORDER EXPERIMENT, BUILT ON WHAT WAS ASKED BEFORE (rich's 9.24 ruling). Everyone was
asked both the existing caring questions and the new activity-based ones, one set early
and one late, by household. This recipe holds {sp["what"]}, conditioned on whether the
other set had been asked earlier — read from what the respondent was actually routed
into, not from the allocation. Respondents from households with no allocation are excluded.

THE CONDITION IS NARRATED: "Earlier in the interview you were asked:" with the other
set's opening questions quoted; or "You had not been asked the questions that begin "..."
earlier in the interview." The framing words, quotation marks and separators are ADDED
(docs/CONVENTIONS.md, "Narrating what the respondent did"). The existing set is a routed
cascade, so only its universal opening questions are quoted: "Is there anyone living with
you ..." for those whose household has more than one person (it was asked only of them),
and "Do you provide some regular service or help ...". The activity set's stem is shown
once above six items in a grid; it is repeated on every activity item here.

MODE. The web adds "If none, just enter zero." to the activity stem and "Please exclude
any help that you provide as part of your job." to the outside-household question;
resolved per row on `indmode`. Help text and interviewer instructions are not rendered.

NOT BUILT: the computed total of activity hours (not a question); "Who do you look
after?" (code all that apply, filled with household members' names) and the relationship
items (the 9.43 checklist ruling, and names of other people); and "How many people do you
care for?", which follows a yes to the outside-household question and counts only people
outside it, a context its row could not carry without adding words (independent checker).
"Other" (code 97) in the hours band is recoded to 10. Four web respondents from
households with no allocation answered (24 activity and 10 existing answers) and are
excluded, as in 9.42, though their path is visible. "Is there anyone living with you"
counts as asked for anyone in its universe, including two coded -9 (missing); the "not
asked" condition quotes whichever question opens the respondent's own existing set.

`person` is a hash of `pidp`, the same construction as every Innovation Panel build.
Allocated by household, so a participant-level split puts one household's members, who
shared a condition, on both sides."""
        s = f"""study_id: ukds_6849
source: innovation_panel
title: "Understanding Society Innovation Panel, experiment 9.47: informal caregiving, {key}
  questions, with or without the other set earlier (wave 17)"
data_file: {DERIVED}
{lic}comparable_to_socsci210: false
experiment: caring_{key}_w17
participant_id_var: person

notes: {json.dumps(notes, ensure_ascii=False)}

condition:
  source_var: {sp["prior"]}
  factors: [{sp["other"]}_asked_earlier]
  considered_and_rejected:
    prior_{sp["sibling"]}: "the exposure code for the sibling experiment; derived by the same generator, not a second randomisation"
  arms:
    - raw: 1
      condition_num: 0
      factors: {{{sp["other"]}_asked_earlier: "no"}}
      text: {json.dumps(sp["not_before"], ensure_ascii=False)}
    - raw: 2
      condition_num: 1
      factors: {{{sp["other"]}_asked_earlier: "yes"}}
      text: {json.dumps(sp["before"], ensure_ascii=False)}

outcomes:
"""
        if key == "activity":
            for t_, (v, label) in enumerate(ACTIVITY.items()):
                s += f"""  - var: {v}
    task_num: {t_}
    question: {json.dumps(f"{stem} {label}", ensure_ascii=False)}
    scale: {{min: 0, max: 168}}
"""
            recode = {i: i for i in range(0, 169)}
        else:
            yes_no = ' 1 "Yes" 2 "No"'
            items = [
                ("aidhh", AIDHH + yes_no, "{min: 1, max: 2, nominal: true}"),
                (
                    "aidxhh",
                    _by_mode(AIDXHH, f"{AIDXHH} {AIDXHH_WEB_EXTRA}") + yes_no,
                    "{min: 1, max: 2, nominal: true}",
                ),
                (
                    "aidhrs",
                    AIDHRS + " " + " ".join(f'{i} "{o}"' for i, o in enumerate(AIDHRS_OPTIONS, 1)),
                    "{min: 1, max: 10, nominal: true}",
                ),
            ]
            for t_, (v, q, scale) in enumerate(items):
                s += f"""  - var: {v}
    task_num: {t_}
    question: {json.dumps(q, ensure_ascii=False)}
    scale: {scale}
"""
            recode = {i: i for i in range(1, 11)}
        s += "\nresponse_recode: {" + ", ".join(f"{k}: {v}" for k, v in recode.items()) + "}\n\n"
        s += "respondent_vars: [indmode, hhmulti]\n\nmissing_codes:" + persona
        (REPO / "recipes" / f"ukds_6849_caring_{key}_w17.yaml").write_text(s)
        print(f"  wrote recipes/ukds_6849_caring_{key}_w17.yaml")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify routing against answers")
    ap.add_argument("--write", action="store_true", help="write the derived .sav file")
    ap.add_argument("--recipes", action="store_true", help="regenerate the two recipes")
    args = ap.parse_args()
    if args.check and check():
        raise SystemExit("answers in a module the allocation did not use")
    df, labels = derive()
    for key, cols in (("activity", list(ACTIVITY)), ("existing", list(EXISTING))):
        usable = df[f"prior_{key}"] > 0
        print(
            f"{key}: {int((df.loc[usable, cols] >= 0).sum().sum()):,} answers with a known exposure"
        )
    if args.write:
        pyreadstat.write_sav(df.copy(), str(OUT / DERIVED), variable_value_labels=labels)
    if args.recipes:
        write_recipes()


if __name__ == "__main__":
    main()
