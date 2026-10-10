#!/usr/bin/env python3
"""Derive the data file AND write the recipes for IP 9.49 — consent to an in-home sensor.

Wave 17 (2024), household questionnaire (`household_ip17`), answered ONCE per
household by the person the household file records as answering the household
questions (`q_ivh1`..`q_ivh16`, exactly one per household). Three factors,
randomised per HOUSEHOLD in `q_hhsamp_ip` (User Guide 9.49):

- `ff_esensinfow17`: 1 full information in the question text (ENVSENSCONS1),
  2 key information in the text and the rest in help text (ENVSENSCONS2);
- `ff_esensdurw17`: the stated maximum duration, filled into the text and the
  question: 1 "up to 6 months", 2 "up to 12 months", 3 "up to a year",
  4 "up to 24 months", 5 "up to 2 years";
- `ff_esensfbw17`: 1 a personalised feedback report promised (one paragraph),
  2 not mentioned.

Asked only face-to-face and on the web (GRIDVARIABLES.MODETYPE = 1|3). The User
Guide documents a script error: CATI households allocated to version 2 were asked
ENVSENSCONS2 anyway. They are not built (declared count, `--check` fails if it
changes). Two experiments, split by mode, because the information-location
factor is a different manipulation in each (what the interviewer read out, vs
what the screen showed with help text behind a click), and mode was not
randomised (ledger 151):

- `recipes/ukds_6849_sensor_consent_w17_ftf.yaml` (hh interview by CAPI)
- `recipes/ukds_6849_sensor_consent_w17_web.yaml` (hh interview by CAWI)

`--check` exits non-zero on any of: an answer outside the routing the
allocation implies (ledger 138), including a blank in a household's own-version
variable; a change in any declared exception count; a mode-cell of the 2x5x2
design with no row (ledger 151); a household with other than exactly one person
recorded as answering the household questions; a quoted string not found in the
questionnaire PDF; a recipe on disk that differs from what this script writes.
It prints COUNTS only.

**`pidp`, `hidp` and `pno` are never written out.** `person` is the same hash
as every other Innovation Panel build.

    uv run python scripts/gen_ip_sensor.py --check
    uv run python scripts/gen_ip_sensor.py --write --recipes
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import textwrap
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
DERIVED = f"sensor_w{WAVE}-derived.sav"
MODES = {"ftf": 1, "web": 3}
RECIPE = {k: REPO / "recipes" / f"ukds_6849_sensor_consent_w17_{k}.yaml" for k in MODES}

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
CONSENT = {1: "envsenscons1", 2: "envsenscons2"}

# ---------------------------------------------------------------------------
# Instrument text, word-for-word from the wave 17 questionnaire PDF, module
# household_ip17 (ENVSENSINTRO, ENVSENSCONS1, ENVSENSCONS2), typography only
# normalised (curly quotes straightened). Every string is asserted by `--check`
# to occur in the PDF, in the context it is used in.
# ---------------------------------------------------------------------------
INTRO = (
    "We know the conditions in our homes can be different according to where we live, even in "
    "different homes in the same street. The air can contain different levels of certain gases "
    "(such as carbon dioxide) and microscopic particles. These variations in air quality, as well "
    "as things like air temperature, humidity, noise levels and light levels, may affect our "
    "physical health, and how we feel – and might affect different people in different ways."
)
OPENING = (
    "To understand how conditions inside people's homes vary, we would like to invite some "
    "households to place a sensor in their home for a period of time. The sensor will record "
    "things about indoor conditions such as air temperature, humidity, noise levels (but not "
    "actual sounds), light levels, and the presence of certain gases and microscopic particles in "
    "the air. Information collected by these sensors would be linked to the answers you have given "
    "in this study. The sensor will be in your home for"
)
DURATION = {
    1: "up to 6 months",
    2: "up to 12 months",
    3: "up to a year",
    4: "up to 24 months",
    5: "up to 2 years",
}
# The fill exactly as the PDF prints it, asserted to occur after OPENING and in
# both questions, so a code mapped to the wrong words fails the check.
DURATION_FILL = " ".join(f"{t} {{if ff_esensdurw17 = {c}}}" for c, t in DURATION.items())
RETURN = ", and the team will contact you to arrange its return when it is time to do so."
FEEDBACK = (
    "A personalised report giving a summary comparing the conditions in your home to the average "
    "home will be sent to you once we have analysed the data."
)
THANKS = "Once you have returned the sensor, you will receive £20 as a thank you."
SEND_FULL = (
    "If you agree: - We will send your name, address, telephone number, and – if you have "
    "provided it – email address to researchers at the University of Glasgow, who are partnering "
    "with Understanding Society to collect these data using sensors."
)
# Version 1's remaining bullets; version 2 moved exactly these to its help text.
BULLETS = (
    "- The University of Glasgow researchers will send you a sensor with simple instructions on "
    "how to use it. - The sensor will just need to be plugged in and left in a room until it is "
    "time to return it. You will not need to do anything with it until it is time to send it back. "
    "- When it is time to return the sensor, the University of Glasgow will contact you to arrange "
    "returning it via a courier service that they will pay for. - You will be asked to complete a "
    "short questionnaire about where the sensor was located while it was in your home and your "
    "experiences with this task. - Data from the sensor will be passed back to Understanding "
    "Society and connected to the answers you have given in this study. - We will make the "
    "combined anonymous data available for academic and policy research purposes only. - Access "
    "to the data will be restricted and controlled, to make sure that researchers use the "
    "information responsibly and safely."
)
SEND_BRIEF = (
    "If you agree, we will send your name, address, telephone number, and – if you have provided "
    "it – email address to researchers at the University of Glasgow, who are partnering with "
    "Understanding Society to collect this data using sensors."
)
LIMITED = (
    "The number of sensors available for this study is limited, so not everyone who agrees to "
    "have a sensor will be sent one. It may also be that those who are happy to help with this "
    "part of the research may have to wait until later in the year for a sensor to be available."
)
LEAFLET_FTF = 'Please read this leaflet on "In-Home Sensors" for further information.'
LEAFLET_WEB = "Please read this leaflet for further information."
LINK_LABEL = "How will my data be linked?"
# The two questions differ by one comma ("address, telephone" / "address telephone").
QUESTION = {
    1: (
        "Do you give permission for us to pass your name, address, telephone number, and email "
        "address to the University of Glasgow so they can send you a sensor to place in your home "
        "for"
    ),
    2: (
        "Do you give permission for us to pass your name, address telephone number, and email "
        "address to the University of Glasgow so they can send you a sensor to place in your home "
        "for"
    ),
}
OPTIONS = ("Yes", "No")

# ---------------------------------------------------------------------------
# Our own words (docs/CONVENTIONS.md, "Narrating what the respondent did" and the
# layout exception). Recorded word-for-word in each recipe's notes.
# ---------------------------------------------------------------------------
FTF_FIRST = "The interviewer read out this text:"
FTF_THEN = "The interviewer then read out this text:"
WEB_FIRST = "You were shown this text on the web:"
WEB_THEN = "You were then shown this text:"
LINKS = f'The screen also gave a link to the leaflet and a link headed "{LINK_LABEL}".'
HELP = "The screen also offered more information as help text, shown only if you clicked on it."

# Declared exceptions, counted from the deposit; a change in either direction
# fails `--check`.
# User Guide 9.49 / "Consent question envsenscons2 asked in CATI mode": CATI
# households allocated to version 2 that were asked ENVSENSCONS2 (any code but
# -8), and of those, the ones answering Yes or No. Not built.
CATI_ASKED, CATI_ANSWERED = 34, 31
# Face-to-face or web households with no allocation on `q_hhsamp_ip` (all three
# variables -9) that were nevertheless asked a consent version. Not built: the
# fills they saw cannot be known.
UNALLOCATED_ASKED = 1
# Answered (Yes/No) households whose household-questions respondent has no
# individual interview, so no persona. Not built. By mode.
NO_PERSONA = {"ftf": 7, "web": 36}


def person_hash(pidp: int) -> str:
    """Same construction as `scripts/build_profiles.py`. Never the raw `pidp`."""
    return "ip_" + hashlib.sha256(f"ukds6849:{pidp}".encode()).hexdigest()[:12]


class IdentifierSafeError(RuntimeError):
    """An error whose message carries no respondent identifier or value."""


def _merge(left: pd.DataFrame, right: pd.DataFrame, key: str, what: str) -> pd.DataFrame:
    """A many-to-one left join that can never print a key (see gen_ip_twitter)."""
    dupes = int(right[key].duplicated().sum())
    if dupes:
        raise IdentifierSafeError(f"{what}: {dupes} duplicated join key(s) on the right")
    try:
        return left.merge(right, on=key, how="left", validate="many_to_one")
    except Exception:
        raise IdentifierSafeError(f"{what}: merge failed (keys withheld)") from None


def _joined() -> tuple[pd.DataFrame, dict]:
    """One row per household with a household interview: mode, allocation, consent
    answers, the household-questions respondent and their persona. Un-prefixed."""
    hh = spss.read(STATA / f"{W}_hhresp_ip.dta").df
    ivh = [f"{W}_ivh{i}" for i in range(17)]
    missing = [c for c in [f"{W}_hidp", f"{W}_modetype", *ivh] if c not in hh.columns]
    if missing:
        raise ValueError(f"hhresp is missing {missing}")
    df = pd.DataFrame(
        {
            "hidp": hh[f"{W}_hidp"].to_numpy(),
            "modetype": hh[f"{W}_modetype"].to_numpy(),
            "envsenscons1": hh[f"{W}_envsenscons1"].to_numpy(),
            "envsenscons2": hh[f"{W}_envsenscons2"].to_numpy(),
        }
    )
    marks = (hh[ivh] == 1).to_numpy()
    df["n_hhq_resp"] = marks.sum(axis=1)
    # 0 = "Non household member"; only meaningful where exactly one is marked.
    df["pno"] = np.where(df["n_hhq_resp"] == 1, marks.argmax(axis=1), -1)

    samp = spss.read(STATA / f"{W}_hhsamp_ip.dta").df
    alloc = pd.DataFrame(
        {
            "hidp": samp[f"{W}_hidp"].to_numpy(),
            "info": samp[f"{W}_ff_esensinfow17"].to_numpy(),
            "dur": samp[f"{W}_ff_esensdurw17"].to_numpy(),
            "fb": samp[f"{W}_ff_esensfbw17"].to_numpy(),
            "hhintmode": samp[f"{W}_hhintmode"].to_numpy(),
        }
    )
    df = _merge(df, alloc, "hidp", "household allocation")
    unmatched = int(df["info"].isna().sum())
    if unmatched:
        raise ValueError(f"{unmatched} households have no allocation row")

    ind = spss.read(STATA / f"{W}_indresp_ip.dta")
    cols = {"pidp": "pidp", f"{W}_hidp": "hidp", f"{W}_pno": "pno"}
    cols.update({f"{W}_{c}": c for c in PERSONA})
    miss = [c for c in cols if c not in ind.df.columns]
    if miss:
        raise ValueError(f"indresp is missing {miss}")
    people = ind.df[list(cols)].rename(columns=cols)
    # One combined join key, so the safe many-to-one merge applies.
    people["hp"] = (
        people["hidp"].astype("int64").astype(str) + ":" + people["pno"].astype("int64").astype(str)
    )
    df["hp"] = df["hidp"].astype("int64").astype(str) + ":" + df["pno"].astype(str)
    df = _merge(df, people.drop(columns=["hidp", "pno"]), "hp", "household respondent")
    df = df.drop(columns=["hp"])
    df["indresp"] = df["pidp"].notna().astype(int)
    labels = {
        c: dict(ind.value_labels[f"{W}_{c}"]) for c in PERSONA if ind.value_labels.get(f"{W}_{c}")
    }
    return df, labels


def _asked(s: pd.Series) -> pd.Series:
    """Put to the respondent: any code but inapplicable or proxy, and not blank."""
    return ~s.isin([-8, -7]) & s.notna()


def _answered(s: pd.Series) -> pd.Series:
    return s.isin([1, 2])


# ---------------------------------------------------------------------------
# The cells and their text.
# ---------------------------------------------------------------------------


def body(info: int, dur: int, fb: int, mode: str) -> str:
    parts = [f"{OPENING} {DURATION[dur]}{RETURN}"]
    if fb == 1:
        parts.append(FEEDBACK)
    parts.append(THANKS)
    parts.append(f"{SEND_FULL} {BULLETS}" if info == 1 else SEND_BRIEF)
    parts.append(LIMITED)
    parts.append(LEAFLET_FTF if mode == "ftf" else LEAFLET_WEB)
    return " ".join(parts)


def condition_text(info: int, dur: int, fb: int, mode: str) -> str:
    b = body(info, dur, fb, mode)
    if mode == "ftf":
        return f'{FTF_FIRST} "{INTRO}" {FTF_THEN} "{b}"'
    text = f'{WEB_FIRST} "{INTRO}" {WEB_THEN} "{b}" {LINKS}'
    return f"{text} {HELP}" if info == 2 else text


def question(info: int, dur: int) -> str:
    return f"{QUESTION[info]} {DURATION[dur]}?"


def outcome_text(info: int, dur: int) -> str:
    return f'{question(info, dur)} 1 "{OPTIONS[0]}" 2 "{OPTIONS[1]}"'


INFO_LEVEL = {1: "full_in_question", 2: "key_in_question_rest_in_help"}
DUR_LEVEL = {1: "6_months", 2: "12_months", 3: "a_year", 4: "24_months", 5: "2_years"}
FB_LEVEL = {1: "promised", 2: "not_mentioned"}


def cells() -> list[tuple[int, int, int, int]]:
    """(condition_num, info, dur, fb), info slowest."""
    out = []
    n = 0
    for info in (1, 2):
        for dur in DURATION:
            for fb in (1, 2):
                out.append((n, info, dur, fb))
                n += 1
    return out


def derive() -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    """One row per household: allocation, consent answers, respondent persona."""
    df, labels = _joined()
    out = pd.DataFrame(
        {"person": [person_hash(int(p)) if p == p else "ip_none" for p in df["pidp"].to_numpy()]}
    )
    for c in ("modetype", "info", "dur", "fb", "indresp", *CONSENT.values(), *PERSONA):
        out[c] = df[c].to_numpy()
    out[list(PERSONA)] = out[list(PERSONA)].fillna(-9)
    out["wave"] = WAVE
    out["year"] = YEAR
    return out, labels


# ---------------------------------------------------------------------------
# The checks.
# ---------------------------------------------------------------------------


def check_routing(df: pd.DataFrame) -> int:
    """Answers outside the routing the allocation implies, counted. Prints counts only."""
    bad = 0
    c1, c2 = df["envsenscons1"], df["envsenscons2"]
    mode_agree = int((df["modetype"] != df["hhintmode"]).sum())
    print(f"  household interview mode disagreeing between files: {mode_agree}")
    bad += mode_agree
    for mode, code in MODES.items():
        in_mode = df["modetype"] == code
        for info in (1, 2):
            own, other = (c1, c2) if info == 1 else (c2, c1)
            cell = in_mode & (df["info"] == info)
            not_routed = int((cell & ~_asked(own)).sum())
            elsewhere = int((cell & _asked(other)).sum())
            print(
                f"  {mode} version {info}: {int(cell.sum()):,} households, {not_routed} not "
                f"asked their own version (blank counts), {elsewhere} asked the other version"
            )
            bad += not_routed + elsewhere
        # The other two factors must hold a real code for every allocated household.
        allocated = in_mode & df["info"].isin([1, 2])
        bad_codes = int(
            (allocated & ~(df["dur"].isin(list(DURATION)) & df["fb"].isin([1, 2]))).sum()
        )
        print(
            f"  {mode} allocated households with a duration or feedback code out of range: "
            f"{bad_codes}"
        )
        bad += bad_codes
    # The documented CATI script error: version 2 asked, version 1 not.
    cati = df["modetype"] == 2
    cati_v1 = int((cati & (_asked(c1) | ((df["info"] == 1) & _asked(c2)))).sum())
    cati_asked = int((cati & (df["info"] == 2) & _asked(c2)).sum())
    cati_answered = int((cati & (df["info"] == 2) & _answered(c2)).sum())
    print(
        f"  CATI version 1 asked anything: {cati_v1}; CATI version 2 asked ENVSENSCONS2: "
        f"{cati_asked} (declared {CATI_ASKED}), answered {cati_answered} (declared "
        f"{CATI_ANSWERED})"
    )
    bad += cati_v1 + abs(cati_asked - CATI_ASKED) + abs(cati_answered - CATI_ANSWERED)
    unalloc = int((~df["info"].isin([1, 2]) & (_asked(c1) | _asked(c2))).sum())
    print(
        f"  unallocated households asked a consent version: {unalloc} "
        f"(declared {UNALLOCATED_ASKED})"
    )
    bad += abs(unalloc - UNALLOCATED_ASKED)
    # Who answered: exactly one household-questions respondent, a household member.
    not_one = int((df["n_hhq_resp"] != 1).sum())
    non_member = int((df["pno"] == 0).sum())
    print(
        f"  households without exactly one household-questions respondent: {not_one}; "
        f"answered by a non-member: {non_member}"
    )
    bad += not_one + non_member
    for mode, code in MODES.items():
        answered = (
            (df["modetype"] == code) & df["info"].isin([1, 2]) & (_answered(c1) | _answered(c2))
        )
        no_persona = int((answered & (df["indresp"] != 1)).sum())
        print(
            f"  {mode} answered households whose respondent has no individual interview: "
            f"{no_persona} (declared {NO_PERSONA[mode]})"
        )
        bad += abs(no_persona - NO_PERSONA[mode])
    bad += check_crossed(df)
    return bad


def built_counts(df: pd.DataFrame, mode: str) -> dict[int, int]:
    """Rows each cell would yield: allocated, own version answered, persona present."""
    counts = {}
    for n, info, dur, fb in cells():
        own = df[CONSENT[info]]
        keep = (
            (df["modetype"] == MODES[mode])
            & (df["info"] == info)
            & (df["dur"] == dur)
            & (df["fb"] == fb)
            & (df["indresp"] == 1)
            & _answered(own)
        )
        counts[n] = int(keep.sum())
    return counts


def check_crossed(df: pd.DataFrame) -> int:
    """Ledger 151: every declared cell must hold rows, in each mode."""
    bad = 0
    for mode in MODES:
        counts = built_counts(df, mode)
        empty = sum(v == 0 for v in counts.values())
        print(f"  {mode} cells of the 2x5x2 design with no row: {empty} of {len(counts)}")
        bad += empty
    return bad


def _pdf_text() -> str:
    raw = subprocess.run(
        ["pdftotext", str(QUEX), "-"], capture_output=True, text=True, check=True
    ).stdout
    raw = raw.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return " ".join(raw.split())


def text_strings() -> list[str]:
    """Each quoted string in the context the recipes use it in."""
    tail1 = f"{SEND_FULL} {BULLETS} {LIMITED}"
    return [
        f"Text: {INTRO} Options:",
        f"{OPENING} {DURATION_FILL}{RETURN} {FEEDBACK} {{if ff_esensfbw17 = 1}} {THANKS}",
        f"{THANKS} {tail1} {LEAFLET_FTF} {QUESTION[1]} {DURATION_FILL} ?",
        f"{THANKS} {tail1} {LEAFLET_WEB} https://",
        f"{THANKS} {SEND_BRIEF} {LIMITED} {LEAFLET_FTF} {QUESTION[2]} {DURATION_FILL}?",
        f"{THANKS} {SEND_BRIEF} {LIMITED} {LEAFLET_WEB} https://",
        f"/sensor {LINK_LABEL} https://",
        # The PDF lays the Help field out beside the options.
        f"Options: Help: 1 Yes Yes 2 No No If you agree: {BULLETS} Mixed Mode",
        "Options: 1 Yes Yes 2 No No",
    ]


def check_text(pdf: str | None = None) -> int:
    t = pdf if pdf is not None else _pdf_text()
    strings = text_strings()
    missing = sum(s not in t for s in strings)
    print(f"  questionnaire strings not found in the PDF: {missing} of {len(strings)}")
    return missing


# ---------------------------------------------------------------------------
# The recipes.
# ---------------------------------------------------------------------------

LICENCE = """\
  UK Data Service End User Licence (UKDS SN 6849). NOT redistributable. The EUL's
  definition of "Data Collection" includes the Documentation, so the variable and value
  labels are part of the collection as much as the microdata is. Nothing built from this
  recipe may leave the machine: `data/raw/` and `data/processed/*.parquet` are gitignored,
  and `src/micromotives_datasets/jev.py` refuses `source="ukds"` outright."""


def notes(mode: str, counts: dict[int, int]) -> str:
    other = "web" if mode == "ftf" else "ftf"
    per_cell = ", ".join(f"{n} {counts[n]}" for n in sorted(counts))
    by_info = {i: sum(counts[n] for n, inf, _, _ in cells() if inf == i) for i in (1, 2)}
    mode_words = (
        "FACE-TO-FACE: households whose household questionnaire was done in person "
        '(`q_modetype` = 1, "capi"; `q_hhintmode` agrees for every household).'
        if mode == "ftf"
        else "WEB: households whose household questionnaire was done online (`q_modetype` = 3, "
        '"cawi"; `q_hhintmode` agrees for every household).'
    )
    narration = (
        f'"{FTF_FIRST}" before the introduction and "{FTF_THEN}" before the consent text. '
        "Narration of reading out follows the face-to-face precedent of "
        "`ukds_6849_hmrc_consent_w15` (the questionnaire gives no showcard). The interviewer "
        'instruction "PLEASE HAND LEAFLET IN-HOME SENSORS TO RESPONDENT AND ALLOW RESPONDENT '
        'TIME TO READ IT AND ASK QUESTIONS." is not narrated (the same precedent): whether '
        "the leaflet was handed over is not recorded per household. In version 2 the help "
        "text was in the interviewer's script, not in front of the respondent; whether an "
        "interviewer read any of it out is not recorded, so nothing is said about it. The face-to-face "
        'leaflet sentence names the leaflet: \'Please read this leaflet on "In-Home Sensors" '
        "for further information.'"
        if mode == "ftf"
        else f'"{WEB_FIRST}" before the introduction; "{WEB_THEN}" before the consent text; '
        f"after it, '{LINKS}' (the PDF prints the leaflet URL and \"{LINK_LABEL}\" with a URL "
        "after the leaflet sentence; the URLs and what lay behind them are not rendered); "
        f"and in version 2 only, '{HELP}' That last sentence is DESCRIPTION of the layout, "
        "not transcription (the layout exception, docs/CONVENTIONS.md): the source has no "
        "words for it. Its basis is the questionnaire's scripting note on ENVSENSCONS2, "
        "\"For web respondents, record whether the respondent clicked on the 'help' text.\" "
        "The help text itself is NOT rendered (whether a respondent opened it is not in the "
        "deposit; the `ukds_6849_twitter_consent_w15` precedent for text behind a link). It "
        "is exactly version 1's last seven bullets, which `--check` asserts against the PDF's "
        "Help field."
    )
    return f"""\
University of Essex, Institute for Social and Economic Research, "Understanding
Society: Innovation Panel, Waves 1-17, 2008-2024", UK Data Service SN 6849.
Experiment 9.49 in the Innovation Panel User Guide ("Indoor residential environment:
consent for in-home sensor"); wave 17 (2024) only. The User Guide cites no publication.
GENERATED by `scripts/gen_ip_sensor.py --recipes`; every quoted string is asserted by
`--check` to occur in `6849_innovation_panel_wave_17_questionnaire.pdf`.
`ukds_6849_sensor_consent_w17_{other}.yaml` is the other mode.

THIS EXPERIMENT: {mode_words} Face-to-face and web are two experiments because mode was
not randomised and the information-location factor is a different manipulation in each:
face-to-face it changes what the interviewer read out; on the web it changes what was on
the screen and what sat behind a help click (ledger 151).

WHAT WAS RANDOMISED (User Guide 9.49, confirmed by the Technical Report: "All
randomisations were conducted at the household level"). Per HOUSEHOLD, on `q_hhsamp_ip`,
joined on `q_hidp`: `ff_esensinfow17` (1/2 each) 1 "Full information in question text"
(ENVSENSCONS1), 2 "Key information in question text, rest in help text" (ENVSENSCONS2);
`ff_esensdurw17` (1/3 to code 1, 1/6 to each other) the maximum duration filled into the
text and the question: 1 "up to 6 months", 2 "up to 12 months", 3 "up to a year", 4 "up to
24 months", 5 "up to 2 years" (12 months / a year and 24 months / 2 years state
the same length in different words); `ff_esensfbw17` (1/2 each) 1 "Feedback from sensor
promised" (the paragraph "{FEEDBACK}" is shown), 2 "not mentioned" (it is not). Fully
crossed: 2 x 5 x 2 = 20 cells, every one holding rows in this mode (`--check`).

THE LABELS WERE NOT TRUSTED (ledger 138). `--check` cross-tabulates the allocation
against the routing: in each mode every version-1 household was asked ENVSENSCONS1
(`envsenscons1`) and not ENVSENSCONS2, every version-2 household the reverse, with no
blank in a household's own-version variable. The duration and feedback fills are
asserted against the PDF's own fill notation code by code.

WHO ANSWERED. The consent was in the HOUSEHOLD questionnaire, answered once per
household. The persona is the person the household file records as answering the
household questions (`q_ivh1`..`q_ivh16`; exactly one per household, never a
non-member), read from their own individual interview (`q_indresp_ip`, joined on
household and person number). Households whose household-questions respondent gave no
individual interview have no persona and are NOT built: {NO_PERSONA[mode]} answered
households in this mode (declared; `--check` fails if it changes). One row per household,
so `person` is also the household.

THE CONDITION (module household_ip17, ENVSENSINTRO then ENVSENSCONS1 or ENVSENSCONS2,
pp. 190-194). Every household first saw the introduction ENVSENSINTRO ("{INTRO[:40]}
..."), then the consent text of its version with its duration and feedback fills
resolved. Version 1 carries the full "If you agree:" list of eight bullets; version 2
carries one sentence, "If you agree, we will send ...", with the other seven bullets in
help text. The two versions' wordings also differ where the questionnaire differs ("collect
these data" / "collect this data"; in the question "address, telephone number" /
"address telephone number"). Both transcribed as fielded.

WORD-FOR-WORD VS OURS. Inside the double quotes, every word is the questionnaire's,
typography normalised (curly quotes straightened; en dashes, the pound sign and the
source's "- " bullet markers kept). ADDED BY US (narration and the layout exception,
docs/CONVENTIONS.md): {narration}

ONE OUTCOME. The version's own question with its duration fill, word-for-word: "Do you
give permission for us to pass your name, address[,] telephone number, and email address
to the University of Glasgow so they can send you a sensor to place in your home for up
to ...?" 1 "Yes" 2 "No", read from the version's own variable. Don't know and refusal
dropped.

NOT BUILT. CATI (telephone) households: the module is face-to-face and web only; the User
Guide documents that CATI households allocated to version 2 were asked ENVSENSCONS2 in
error ({CATI_ASKED} asked, {CATI_ANSWERED} answered), while version-1 CATI households were
correctly not asked, so a CATI arm would exist for one version only, and the face-to-face
text (handing a leaflet) was not what a telephone respondent met. {UNALLOCATED_ASKED} web
household with no allocation on `q_hhsamp_ip` that was asked version 1 (its fills cannot
be known). The 156 households whose data were lost (User Guide, `q_ivfho` 17/39) are not
in `q_hhresp_ip` at all. The debrief questions (ESENSDEBRY / ESENSDEBRN): code-all-that-
apply lists whose universe and options follow the respondent's own consent answer (ledger
132, 142). The Technical Report records no other script error touching this module; its
two data issues (the CAWI-CAPI grid overwrite, the missing health-condition feed-forward)
do not.

ROW COUNTS (aggregates). By condition_num ({", ".join(f"{n} = info {i}, duration {d}, feedback {f}" for n, i, d, f in cells()[:2])}, ...
info slowest, then duration, then feedback): {per_cell}. Version 1 {by_info[1]}, version 2
{by_info[2]}; {sum(counts.values())} rows, one per household.

PERSONA. The same spine as every Innovation Panel build, from the household-questions
respondent's own individual interview. `person` is a hash of `pidp`. A participant-level
split is a household-level split here."""


def _yaml_block(text: str, indent: int = 2) -> str:
    """Each paragraph re-wrapped to 88 columns, indented under the block scalar."""
    pad = " " * indent
    paras = [" ".join(p.split()) for p in text.split("\n\n")]
    return "\n\n".join(
        textwrap.fill(
            p, width=88, initial_indent=pad, subsequent_indent=pad, break_on_hyphens=False
        )
        for p in paras
    )


def recipe_text(mode: str, counts: dict[int, int]) -> str:
    title = (
        "Understanding Society Innovation Panel, experiment 9.49: consent to an in-home sensor, "
        "varying where the information sat, the stated duration and a promised feedback report, "
        + ("face-to-face" if mode == "ftf" else "web")
        + " (wave 17)"
    )
    arms = []
    for n, info, dur, fb in cells():
        arms.append(
            f"""    - raw_values: {{modetype: {MODES[mode]}, info: {info}, dur: {dur}, fb: {fb}, indresp: 1}}
      condition_num: {n}
      factors: {{information: {json.dumps(INFO_LEVEL[info])}, duration: {json.dumps(DUR_LEVEL[dur])}, feedback: {json.dumps(FB_LEVEL[fb])}}}
      text: {json.dumps(condition_text(info, dur, fb, mode), ensure_ascii=False)}
      items:
        0:
          outcome_var: {CONSENT[info]}
          outcome_question: {json.dumps(outcome_text(info, dur), ensure_ascii=False)}
          scale: {{min: 1, max: 2, nominal: true}}
          response_recode: {{1: 1, 2: 2}}"""
        )
    persona_map = "\n".join(
        f"  {k}: {v}"
        for k, v in (
            ("age", "dvage"),
            ("sex", "sex"),
            ("region", "gor_dv"),
            ("employment", "jbstat"),
            ("education", "hiqual_dv"),
            ("marital_status", "mastat_dv"),
            ("ethnicity", "racel_dv"),
            ("own_children_in_household", "nchild_dv"),
            ("wave", "wave"),
            ("year", "year"),
        )
    )
    persona_missing = "\n".join(f"  {v}: [-9, -8, -7, -2, -1]" for v in PERSONA)
    return f"""\
study_id: ukds_6849
source: innovation_panel
title: {json.dumps(title)}
data_file: {DERIVED}
licence: |-
{LICENCE}

comparable_to_socsci210: false
experiment: sensor_consent_w17_{mode}
participant_id_var: person

notes: |-
{_yaml_block(notes(mode, counts))}

condition:
  source_vars: [modetype, info, dur, fb, indresp]
  factors: [information, duration, feedback]
  arms:
{chr(10).join(arms)}

# No `var`: each arm names its own. The question here is a fallback every arm
# overrides; no built row may carry it.
outcomes:
  - task_num: 0
    question: "[consent to an in-home sensor, in the version's own wording]"
    scale: {{min: 1, max: 2, nominal: true}}

response_recode: {{1: 1, 2: 2}}

missing_codes: [-9, -8, -7, -2, -1]

persona_map:
{persona_map}

persona_missing:
{persona_missing}
"""


def check_recipes(df: pd.DataFrame) -> int:
    bad = 0
    for mode, path in RECIPE.items():
        want = recipe_text(mode, built_counts(df, mode))
        same = path.exists() and path.read_text() == want
        print(f"  {path.name} as this script writes it: {'yes' if same else 'NO'}")
        bad += not same
    return bad


def check() -> int:
    df, _ = _joined()
    bad = check_routing(df)
    bad += check_text()
    bad += check_recipes(df)
    print(f"  {'AGREE' if bad == 0 else 'DEFECT'}")
    return bad


def main() -> None:
    try:
        _main()
    except SystemExit:
        raise
    except IdentifierSafeError as exc:
        raise SystemExit(f"error: {exc}") from None
    except Exception as exc:
        # Any other message could quote a value from the deposit.
        raise SystemExit(f"error: {type(exc).__name__} (message withheld)") from None


def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify routing, text and recipes")
    ap.add_argument("--write", action="store_true", help="write the derived .sav file")
    ap.add_argument("--recipes", action="store_true", help="write the two recipes")
    args = ap.parse_args()

    if args.recipes:
        df, _ = _joined()
        for mode, path in RECIPE.items():
            path.write_text(recipe_text(mode, built_counts(df, mode)))
            print(f"  wrote {path.relative_to(REPO)}")

    if args.check and check():
        raise SystemExit("check failed")

    df, labels = derive()
    for mode in MODES:
        print(f"{mode}: rows per cell {built_counts(df, mode)}")
    if args.write:
        path = OUT / DERIVED
        pyreadstat.write_sav(df, str(path), variable_value_labels=labels)
        print(f"  wrote {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
