#!/usr/bin/env python3
"""Derive the data files for IP 9.25 — consent to link HMRC (tax) records, waves 11 and 15.

The two waves are DIFFERENT experiments under one User Guide number, so each has
its own recipe:

**Wave 11 (2018), two experiments:** `recipes/ukds_6849_hmrc_consent_w11.yaml`
(face-to-face, wording x placement) and `recipes/ukds_6849_hmrc_consent_w11_web.yaml`
(web, wording only). Allocated per
respondent, in `k_indresp_ip` (no household join). Wording, standard or easy:
`condiffcapi` (face-to-face) and `condiffcawi` (web). Face-to-face only, the
placement, early or late in the interview: `conlocstand` (standard wording) and
`conloceasy` (easy). Web respondents were always asked in the late module, and
their `conloc*` variable holds 2 ("late") accordingly. Four consent variables,
one per module: `consentq1` standard early, `consentq2` easy early, `consentq3`
standard late (face-to-face and web), `consentq4` easy late (both).

**Wave 15 (2022), `recipes/ukds_6849_hmrc_consent_w15.yaml`.** Easy wording for
everyone. Allocated per household in `o_hhsamp_ip`: face-to-face by
`ff_consentcasiw15` (1 interviewer asks it, 2 respondent reads and answers it on
the laptop, 3 interviewer reads a card and the respondent answers on the
laptop); web by `ff_consentwebw15` (1 text only, 2 with a photo of and message
from the study director). Consent in `hmrcconsentq1`..`q4`.

`--check` exits non-zero on any of: an answer outside the routing the
allocation implies (ledger 138); a change in the number of face-to-face late
rows excluded for the wave 11 script error (W11_SCRIPT_ERROR_ROWS); a late-placed respondent not asked the income
and benefits questions the condition says they had been asked; a quoted string
not found in the questionnaire PDF; a recipe arm whose text or question differs
from what this script composes. It prints COUNTS only.

**`pidp` and `hidp` are never written out.** `person` is the same hash as every
other Innovation Panel build.

    uv run python scripts/gen_ip_hmrc.py --check
    uv run python scripts/gen_ip_hmrc.py --write
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyreadstat
import yaml

from micromotives_datasets.sources import spss

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[1]
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"
PDF = REPO / "data" / "raw" / "ukds_6849" / "mrdoc" / "pdf"
OUT = REPO / "data" / "raw" / "ukds_6849"
QUEX = {
    11: PDF / "6849_ip_wave_11_questionnaires.pdf",
    15: PDF / "6849_ip_wave_15_questionnaire.pdf",
}
RECIPE = {
    "w11": REPO / "recipes" / "ukds_6849_hmrc_consent_w11.yaml",
    "w11_web": REPO / "recipes" / "ukds_6849_hmrc_consent_w11_web.yaml",
    "w15": REPO / "recipes" / "ukds_6849_hmrc_consent_w15.yaml",
}
PREFIX = {11: "k", 15: "o"}
YEAR = {11: 2018, 15: 2022}

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

# ---------------------------------------------------------------------------
# Instrument text, word-for-word from the questionnaire PDFs (typography only
# normalised). Every string here is asserted by `--check` to occur in the PDF.
# ---------------------------------------------------------------------------

# Wave 11, modules Hmrcconsentearly_ip11 / Hmrcconsentlate_ip11 (ConsentQ1-Q4).
STD_BODY = (
    "We would like to add records held by HM Revenue and Customs, or HMRC, containing "
    "information on your employment and self-employment history, your income, National "
    "Insurance contributions and tax credits. All information will be used for research "
    "purposes only by academic or policy researchers under restricted access arrangements "
    "which make sure that the information is used responsibly and safely."
)
STD_LEAFLET_CAPI = (
    "Please read this leaflet explaining how we would like to attach your HMRC records to the "
    "answers you have given in this study and let me know if you have any questions."
)
STD_LEAFLET_WEB = (
    "Please read this leaflet explaining how we would like to attach your HMRC records to the "
    "answers you have given in this study."
)
# The web alternative of ConsentQ3 reads "...responsibly and safely.>" before the
# leaflet sentence. The ">" is dropped as a stray markup character (recorded in
# the recipe); this is the PDF's own string, asserted to exist.
STD_WEB_STRAY = "responsibly and safely.> Please read this leaflet explaining how"

# The "easy" wording: wave 11 ConsentQ2/Q4, and every wave 15 version.
EASY_BODY = (
    "We would like to add records held by HM Revenue and Customs, or HMRC, to the answers you "
    "have given in this study. If you agree: "
    "• We will send HMRC your name, address, sex and date of birth so that they can identify "
    "the records they have about you. The HMRC records contain information about your current "
    "and previous employment, your income, National Insurance contributions and tax credits. "
    "• We will not send HMRC the answers you have given in this study. "
    "• HMRC will send us your records. These will contain an anonymous identification number "
    "but not your name, address, sex or date of birth. "
    "• We will add the HMRC records to the answers you have given in this study. "
    "• We will make the combined anonymous data available for academic and policy research "
    "purposes only. "
    "• Access to the data will be restricted and controlled, to make sure that researchers use "
    "the information responsibly and safely. "
    "• This will not affect the way that you deal with HMRC in any way."
)
EASY_LEAFLET = "Please read this leaflet for further information."
ANY_QUESTIONS = "Let me know if you have any questions."
LINK_LABEL = "How will my data be linked?"

QUESTION = (
    "Do you give permission for us to pass your name, address, sex and date of birth to HMRC "
    "for this purpose?"
)
OPTS_STD_CAPI = (
    "Respondent has read leaflet and is happy to give consent",
    "Respondent does not want to give consent",
)
OPTS_STD_WEB = (
    "I have read the leaflet and am happy to give consent",
    "I do not want to give consent",
)
OPTS_YES_NO = ("Yes", "No")

# Wave 11, module Benefits_w10, Intbenefit: the opening of the income and benefits
# questions, which sit between the early and late consent modules. Its first three
# sentences carry no mode fill.
INCOME_INTRO = (
    "One of the most important parts of our research is how people are getting by financially "
    "these days. We have found that we need to ask about a number of different types of "
    "income, otherwise our results could be misleading. Please think about ALL of the extra "
    "sources of income you receive, as well as any benefits or tax credits."
)

# Wave 15, Casistart_ip15: Scac (CASI version) and Scac2 (partial CASI version).
SCAC = "I now have some questions for you to answer yourself on the computer."
SCAC2 = (
    "I now have some questions for you to answer yourself on the computer. For the first one, "
    "I will read the question to you but do not tell me your answer. After reading the "
    "question, I will pass you the laptop so that you can enter your answer confidentially."
)
# Wave 15, Hmrcconsent4_ip15 scripting note: the message shown with the photo.
DIRECTOR = (
    "Hello, I am Professor Michaela Benzeval, Director of Understanding Society. Linking your "
    "survey answers with administrative records while preserving the confidentiality of your "
    "data increases the value of the information you provide. Please read the following "
    "carefully."
)

# ---------------------------------------------------------------------------
# Our own words (docs/CONVENTIONS.md, "Narrating what the respondent did" and
# the layout exception). Recorded word-for-word in each recipe's notes.
# ---------------------------------------------------------------------------
NOT_YET = (
    f'You had not been asked the questions that begin "{INCOME_INTRO}" earlier in the interview.'
)
ALREADY = f'Earlier in the interview you were asked the questions that begin "{INCOME_INTRO}"'
LINKS = f'The screen also gave a link to the leaflet and a link, "{LINK_LABEL}", to a flowchart.'


def q(text: str) -> str:
    return f'"{text}"'


def outcome(opts: tuple[str, str]) -> str:
    return f'{QUESTION} 1 "{opts[0]}" 2 "{opts[1]}"'


# The ROUTING cells per wave: condition_num -> (allocation codes, own outcome
# variable, condition text, options). `check_routing` reads these; the recipes'
# arms are built from them in RECIPES below.
ARMS: dict[int, dict[int, tuple[dict[str, int], str, str, tuple[str, str]]]] = {
    11: {
        0: (
            {"indmode": 1, "wording": 1, "placement": 1},
            "consentq1",
            f"{NOT_YET} The interviewer then read out this text: "
            + q(f"{STD_BODY} {STD_LEAFLET_CAPI}"),
            OPTS_STD_CAPI,
        ),
        1: (
            {"indmode": 1, "wording": 1, "placement": 2},
            "consentq3",
            f"{ALREADY} The interviewer then read out this text: "
            + q(f"{STD_BODY} {STD_LEAFLET_CAPI}"),
            OPTS_STD_CAPI,
        ),
        2: (
            {"indmode": 1, "wording": 2, "placement": 1},
            "consentq2",
            f"{NOT_YET} The interviewer then read out this text: "
            + q(f"{EASY_BODY} {EASY_LEAFLET} {ANY_QUESTIONS}"),
            OPTS_YES_NO,
        ),
        3: (
            {"indmode": 1, "wording": 2, "placement": 2},
            "consentq4",
            f"{ALREADY} The interviewer then read out this text: "
            + q(f"{EASY_BODY} {EASY_LEAFLET} {ANY_QUESTIONS}"),
            OPTS_YES_NO,
        ),
        4: (
            {"indmode": 3, "wording": 1, "placement": 2},
            "consentq3",
            "You were shown this text on the web: "
            + q(f"{STD_BODY} {STD_LEAFLET_WEB}")
            + f" {LINKS}",
            OPTS_STD_WEB,
        ),
        5: (
            {"indmode": 3, "wording": 2, "placement": 2},
            "consentq4",
            "You were shown this text on the web: "
            + q(f"{EASY_BODY} {EASY_LEAFLET}")
            + f" {LINKS}",
            OPTS_YES_NO,
        ),
    },
    15: {
        0: (
            {"indmode": 1, "casi": 1, "photo": -8, "selfcomp": -8},
            "hmrcconsentq1",
            "The interviewer read out this text: "
            + q(f"{EASY_BODY} {EASY_LEAFLET} {ANY_QUESTIONS}"),
            OPTS_YES_NO,
        ),
        1: (
            {"indmode": 1, "casi": 2, "photo": -8, "selfcomp": 1},
            "hmrcconsentq2",
            f"The interviewer said {q(SCAC)} You then read this text on the laptop and answered "
            f"the question that followed yourself: {q(f'{EASY_BODY} {EASY_LEAFLET}')} {LINKS}",
            OPTS_YES_NO,
        ),
        2: (
            {"indmode": 1, "casi": 3, "photo": -8, "selfcomp": 1},
            "hmrcconsentq3",
            f"The interviewer said {q(SCAC2)} The interviewer then read out this text from a card "
            f"and handed you the card: {q(f'{EASY_BODY} {EASY_LEAFLET} {ANY_QUESTIONS}')} The "
            "question that followed was on the laptop, and you entered your answer yourself.",
            OPTS_YES_NO,
        ),
        3: (
            {"indmode": 3, "casi": -8, "photo": 1, "selfcomp": -8},
            "hmrcconsentq2",
            f"You were shown this text on the web: {q(f'{EASY_BODY} {EASY_LEAFLET}')} {LINKS}",
            OPTS_YES_NO,
        ),
        4: (
            {"indmode": 3, "casi": -8, "photo": 2, "selfcomp": -8},
            "hmrcconsentq4",
            f"You were shown, on the web, a photo of the study director with this message: "
            f"{q(DIRECTOR)} Below it you were shown this text: "
            f"{q(f'{EASY_BODY} {EASY_LEAFLET}')} {LINKS}",
            OPTS_YES_NO,
        ),
    },
}

# Recipe -> (wave, {condition_num: (raw_values, own variable, text, options)}).
# Wave 11 is TWO experiments (coordinator's ruling after the independent check):
# the face-to-face 2x2 (wording x placement, both randomised and fully crossed)
# and the web wording contrast, which had no placement allocation of its own.
# The face-to-face arms also require `scripterr` = 0 (see W11_SCRIPT_ERROR_ROWS).
RECIPES: dict[str, tuple[int, dict[int, tuple[dict[str, int], str, str, tuple[str, str]]]]] = {
    "w11": (
        11,
        {
            n: ({**raw, "scripterr": 0}, own, text, opts)
            for n, (raw, own, text, opts) in ARMS[11].items()
            if raw["indmode"] == 1
        },
    ),
    "w11_web": (
        11,
        {
            n - 4: ({"indmode": 3, "wording": raw["wording"]}, own, text, opts)
            for n, (raw, own, text, opts) in ARMS[11].items()
            if raw["indmode"] == 3
        },
    ),
    "w15": (15, ARMS[15]),
}

CONSENT_VARS = {
    11: ("consentq1", "consentq2", "consentq3", "consentq4"),
    15: ("hmrcconsentq1", "hmrcconsentq2", "hmrcconsentq3", "hmrcconsentq4"),
}
# Wave 15: respondents whose consent answer contradicts the self-completion
# routing (CASI version, "Not able to do self-completion", yet answered the
# self-completion consent question). Counted, never assigned: the selfcomp gate
# excludes them. A change in either direction fails `--check`.
W15_ANSWERED_DESPITE_SCAC = 4

# Wave 11 variables that open, and sit inside, the income and benefits questions
# and the household finances questions; each must have been asked of every
# late-placed respondent.
W11_PRIOR = ("benbase1", "finnow")

# Wave 11 script error (Technical Report, section 5.3, Table 5.1, the script
# version active from 26 July): the "CASI early end" module did not appear for
# about 200 interviews, so some respondents were never told to hand the laptop
# back after the early self-completion section and "may have continued to
# self-complete" sections meant to be interviewer-administered. For a
# face-to-face LATE consent respondent who went through that section (`eq5dcond`
# 1 or 2) and has no self-completion interviewer number recorded for it
# (`casiintnoearly` = -9), "The interviewer then read out this text:" cannot be
# verified, so they are excluded (`scripterr` = 1). Answered rows lost, by
# wording (1 standard, 2 easy); a change in either direction fails `--check`.
W11_SCRIPT_ERROR_ROWS = {1: 124, 2: 103}


def person_hash(pidp: int) -> str:
    """Same construction as `scripts/build_profiles.py`. Never the raw `pidp`."""
    return "ip_" + hashlib.sha256(f"ukds6849:{pidp}".encode()).hexdigest()[:12]


def derived_name(wave: int) -> str:
    return f"hmrc_w{wave}-derived.sav"


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


def _joined(wave: int) -> tuple[pd.DataFrame, dict]:
    """The person file, with the allocation as the questionnaire routes on it.

    Columns are un-prefixed here so both waves read the same way.
    """
    w = PREFIX[wave]
    ind = spss.read(STATA / f"{w}_indresp_ip.dta")
    base = ["pidp", "indmode", *CONSENT_VARS[wave], *PERSONA]
    if wave == 11:
        base += [
            "condiffcapi",
            "condiffcawi",
            "conlocstand",
            "conloceasy",
            "eq5dcond",
            "casiintnoearly",
            *W11_PRIOR,
        ]
    else:
        base += ["hidp", "scac", "scac2"]
    cols = {f"{w}_{c}" if c != "pidp" else c: c for c in base}
    missing = [c for c in cols if c not in ind.df.columns]
    if missing:
        raise ValueError(f"indresp is missing {missing}")
    df = ind.df[list(cols)].rename(columns=cols)
    if wave == 15:
        hh = spss.read(STATA / f"{w}_hhsamp_ip.dta").df
        alloc = hh[[f"{w}_hidp", f"{w}_ff_consentcasiw15", f"{w}_ff_consentwebw15"]].rename(
            columns={
                f"{w}_hidp": "hidp",
                f"{w}_ff_consentcasiw15": "ff_casi",
                f"{w}_ff_consentwebw15": "ff_web",
            }
        )
        df = _merge(df, alloc, "hidp", "household allocation")
        unmatched = int(df["ff_casi"].isna().sum())
        if unmatched:
            raise ValueError(f"{unmatched} respondents have no household allocation row")
    labels = {
        c: dict(ind.value_labels[f"{w}_{c}"]) for c in PERSONA if ind.value_labels.get(f"{w}_{c}")
    }
    return df, labels


def _assignment(df: pd.DataFrame, wave: int) -> pd.DataFrame:
    """The recipe's `source_vars`, from the allocation and mode. -8 = not applicable."""
    out = pd.DataFrame(index=df.index)
    out["indmode"] = df["indmode"]
    if wave == 11:
        ftf, web = df["indmode"] == 1, df["indmode"] == 3
        out["wording"] = np.where(ftf, df["condiffcapi"], np.where(web, df["condiffcawi"], -8))
        out["placement"] = np.where(
            out["wording"] == 1,
            df["conlocstand"],
            np.where(out["wording"] == 2, df["conloceasy"], -8),
        )
        # The script error: 1 = excluded, 0 = not affected. `casiintnoearly` is an
        # interviewer number and is never written out; only this flag is.
        out["scripterr"] = (
            ftf
            & (out["placement"] == 2)
            & df["eq5dcond"].isin([1, 2])
            & (df["casiintnoearly"] == -9)
        ).astype(int)
    else:
        ftf, web = df["indmode"] == 1, df["indmode"] == 3
        out["casi"] = np.where(ftf, df["ff_casi"], -8)
        out["photo"] = np.where(web, df["ff_web"], -8)
        # The self-completion acceptance asked BEFORE the consent question: Scac in
        # the CASI version, Scac2 in the partial-CASI version. In the CAPI version
        # Scac comes after the consent question, so it is not part of the condition.
        out["selfcomp"] = np.where(
            ftf & (df["ff_casi"] == 2),
            df["scac"],
            np.where(ftf & (df["ff_casi"] == 3), df["scac2"], -8),
        )
    return out


def _cell(assign: pd.DataFrame, raw: dict[str, int]) -> pd.Series:
    mask = pd.Series(True, index=assign.index)
    for var, val in raw.items():
        mask &= assign[var] == val
    return mask


def derive(wave: int) -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    """One row per respondent: assignment, consent answers and persona."""
    df, labels = _joined(wave)
    assign = _assignment(df, wave)
    out = pd.DataFrame({"person": [person_hash(int(p)) for p in df["pidp"]]})
    for c in assign.columns:
        out[c] = assign[c].to_numpy()
    for v in CONSENT_VARS[wave]:
        out[v] = df[v].to_numpy()
    for v in PERSONA:
        out[v] = df[v].to_numpy()
    out["wave"] = wave
    out["year"] = YEAR[wave]
    return out, labels


def _asked(s: pd.Series) -> pd.Series:
    """Put to the respondent: any code but inapplicable or proxy."""
    return ~s.isin([-8, -7]) & s.notna()


def check_routing(df: pd.DataFrame, wave: int) -> int:
    """Answers outside the routing the allocation implies, counted. Prints counts only."""
    assign = _assignment(df, wave)
    bad = 0
    owned = set()
    for num, (raw, own, _, _) in ARMS[wave].items():
        cell = _cell(assign, raw)
        owned.add(own)
        others = [v for v in CONSENT_VARS[wave] if v != own]
        not_routed = int((~_asked(df.loc[cell, own])).sum())
        elsewhere = int(sum(_asked(df.loc[cell, v]).sum() for v in others))
        print(
            f"  w{wave} arm {num}: {int(cell.sum()):,} in cell, {not_routed} not asked "
            f"{own}, {elsewhere} answers in another version's variable"
        )
        bad += not_routed + elsewhere
    # The other direction: anyone asked a consent variable must sit in a cell that
    # owns it, or be one of the declared exceptions.
    in_any = pd.Series(False, index=df.index)
    for raw, *_ in ARMS[wave].values():
        in_any |= _cell(assign, raw)
    stray = 0
    for v in CONSENT_VARS[wave]:
        stray += int((_asked(df[v]) & ~in_any).sum())
    if wave == 11:
        # Web respondents had no placement allocation of their own; the late module
        # is the only one the web script routes to, and the data must say "late".
        web = df["indmode"] == 3
        web_not_late = int((web & (assign["placement"] != 2)).sum())
        print(f"  w11 web respondents not coded late: {web_not_late}")
        bad += web_not_late
        print(f"  w11 consent answers outside every cell: {stray}")
        bad += stray
        # The late condition says the income and benefits questions came first.
        late = assign["placement"] == 2
        unasked = int(sum((late & ~_asked(df[v])).sum() for v in W11_PRIOR))
        print(f"  w11 late-placed respondents not asked {'/'.join(W11_PRIOR)}: {unasked}")
        bad += unasked
        # The script error: answered rows excluded, per wording, against the declaration.
        err = assign["scripterr"] == 1
        lost = {}
        for wording, own in ((1, "consentq3"), (2, "consentq4")):
            lost[wording] = int((err & (assign["wording"] == wording) & df[own].isin([1, 2])).sum())
        print(
            f"  w11 face-to-face late rows excluded for the script error: {lost} "
            f"(declared {W11_SCRIPT_ERROR_ROWS})"
        )
        bad += sum(abs(lost[k] - W11_SCRIPT_ERROR_ROWS[k]) for k in W11_SCRIPT_ERROR_ROWS)
        # It can only ever touch face-to-face late respondents.
        outside = int((err & ~((assign["indmode"] == 1) & (assign["placement"] == 2))).sum())
        print(f"  w11 script-error flags outside face-to-face late: {outside}")
        bad += outside
    else:
        # Outside every cell: CASI or partial-CASI respondents whose self-completion
        # was not accepted as such (codes 2-5). Answering while declining is the
        # declared contradiction; the rest are excluded as not having read and
        # entered it themselves (ledger 141).
        ftf = df["indmode"] == 1
        casi = ftf & (df["ff_casi"] == 2)
        despite = int((casi & df["scac"].isin([4, 5]) & _asked(df["hmrcconsentq2"])).sum())
        print(
            f"  w15 CASI version answered despite declining or being unable to self-complete: "
            f"{despite} (declared {W15_ANSWERED_DESPITE_SCAC})"
        )
        bad += abs(despite - W15_ANSWERED_DESPITE_SCAC)
        helped = int(
            (
                (casi & df["scac"].isin([2, 3]) & _asked(df["hmrcconsentq2"]))
                | (
                    ftf
                    & (df["ff_casi"] == 3)
                    & df["scac2"].isin([2, 3])
                    & _asked(df["hmrcconsentq3"])
                )
            ).sum()
        )
        print(f"  w15 answered with the interviewer completing or helping (excluded): {helped}")
        explained = despite + helped
        print(
            f"  w15 consent answers outside every cell: {stray} ({explained} accounted for above)"
        )
        bad += abs(stray - explained)
    return bad


def _pdf_text(wave: int) -> str:
    raw = subprocess.run(
        ["pdftotext", str(QUEX[wave]), "-"], capture_output=True, text=True, check=True
    ).stdout
    raw = raw.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return " ".join(raw.split())


def check_text(wave: int, pdf: str | None = None) -> int:
    """Every quoted instrument string occurs in that wave's questionnaire PDF."""
    t = pdf if pdf is not None else _pdf_text(wave)
    if wave == 11:
        strings = [
            STD_BODY,
            STD_LEAFLET_CAPI,
            STD_LEAFLET_WEB,
            STD_WEB_STRAY,
            f"{EASY_BODY} {EASY_LEAFLET} {ANY_QUESTIONS} {QUESTION}",
            f"{EASY_BODY} {EASY_LEAFLET}",
            f"[{LINK_LABEL}]",
            INCOME_INTRO,
            QUESTION,
            *OPTS_STD_CAPI,
            *OPTS_STD_WEB,
        ]
    else:
        strings = [
            f"{EASY_BODY} {EASY_LEAFLET} {ANY_QUESTIONS} {QUESTION}",
            f"{EASY_BODY} {EASY_LEAFLET} [https://",
            f"{LINK_LABEL} [https://",
            SCAC,
            SCAC2,
            f'"{DIRECTOR}"',
            QUESTION,
        ]
    missing = sum(s not in t for s in strings)
    print(f"  w{wave} questionnaire strings not found in the PDF: {missing} of {len(strings)}")
    return missing


def _straight(text: str) -> str:
    return text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')


def check_recipe(key: str, rec: dict[str, Any] | None = None) -> int:
    """The recipe's arms carry exactly the codes, text and question composed here."""
    if rec is None:
        rec = yaml.safe_load(RECIPE[key].read_text())
    _, composed = RECIPES[key]
    arms = {a["condition_num"]: a for a in rec["condition"]["arms"]}
    bad = int(set(arms) != set(composed))
    for num, (raw, own, text, opts) in composed.items():
        arm = arms.get(num)
        if arm is None:
            continue
        item = arm.get("items", {}).get(0, {})
        bad += arm.get("raw_values") != raw
        bad += " ".join(str(arm.get("text", "")).split()) != _straight(text)
        bad += item.get("outcome_var") != own
        bad += " ".join(str(item.get("outcome_question", "")).split()) != _straight(outcome(opts))
    print(f"  {key} recipe arms differing from the composed text: {bad}")
    return bad


def check(wave: int | None = None) -> int:
    bad = 0
    for wv in (11, 15) if wave is None else (wave,):
        df, _ = _joined(wv)
        bad += check_routing(df, wv)
        bad += check_text(wv)
        for key, (recipe_wave, _) in RECIPES.items():
            if recipe_wave == wv:
                bad += check_recipe(key)
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
    ap.add_argument("--write", action="store_true", help="write the derived .sav files")
    args = ap.parse_args()

    if args.check and check():
        raise SystemExit("check failed")

    for wave in (11, 15):
        df, labels = derive(wave)
        assign = df[
            [c for c in ("indmode", "wording", "placement", "casi", "photo", "selfcomp") if c in df]
        ]
        cells = {n: int(_cell(assign, raw).sum()) for n, (raw, *_) in ARMS[wave].items()}
        print(f"wave {wave}: {len(df):,} respondents; per arm {cells}")
        if args.write:
            path = OUT / derived_name(wave)
            pyreadstat.write_sav(df, str(path), variable_value_labels=labels)
            print(f"  wrote {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
