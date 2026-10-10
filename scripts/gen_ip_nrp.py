#!/usr/bin/env python3
"""Derive the data file and the recipes for IP 9.23: non-resident parents, wave 10.

Wave 10 (2017). Two adapted modules, Family Networks (relatives living elsewhere,
how often you see them) and Fertility History (every child you have ever had),
were asked of everyone, one early in the interview and the other late. The
household allocation `j_ff_nonresw10` on `j_hhsamp_ip` decided which came first
(User Guide 9.23: 1 = "Ask adapted Family Networks (Version A) module first",
2 = "Ask adapted Fertility History (Version A) module first", 50/50). The
versions differ in ORDER, not in their questions: each item is asked in the
same words whichever slot it sits in. The late module's introduction adds two
sentences acknowledging the repetition ("We realise that we might be asking you
to repeat some information ..."), and Family Networks' late version adds them
only for interviewer-administered respondents (its web text omits them).

So the design is the 9.24 / 9.42 one, built on what was asked before (rich's
ruling for 9.24), as two experiments with one answer type each (ledger 147):

  `nrp_w10_fh`      the three Fertility History questions asked of EVERYONE
                    (ever adopted, ever lived with step-children, ever had
                    biological children; Yes / No), conditioned on whether the
                    Family Networks questions had been asked earlier.
  `nrp_w10_contact` the six Family Networks contact-frequency questions (see
                    and contact mother, father, child aged 18+; Daily .. Never),
                    conditioned on whether the Fertility History questions had
                    been asked earlier.

This script does what a recipe cannot:

**The allocation lives in another file**, joined from `j_hhsamp_ip` on `j_hidp`.

**The variables are named by GROUP, not by position.** Group 1's items carry
suffix 1 (`masee1`, `ladopted1`) and group 2's suffix 2, whichever slot the
module sat in; the questionnaire places Familynetworksa (suffix 1) and
Fertilityhistorya (suffix 2) in the early slot. `--check` tests the data rather
than the label (ledger 138): the Non-Resident Identifier module enumerates exactly
the children the "A" modules counted, Family Networks' for every group 1
respondent and Fertility History's for every group 2 respondent. That proves the
loop followed the "A" modules; that "A" ran FIRST rests on the questionnaire's
module order, supported by the two group 1 web break-offs (Family Networks
answered, the late Fertility History coded -9).

**The routing.** Allocation equals routing: no respondent holds an answer in
the other group's variables, and none has a blank in their own group's. Within
Family Networks, each contact item's universe is computed from the respondent's
own answers (`lvreladp`, `biou18`/`adopu18`/`stepu18`) and must equal the
routing exactly. The three Fertility History questions must be routed alike.

**`pidp` is never written out.** `person` is the same hash as every Innovation
Panel build. No message printed here carries a respondent value.

    uv run python scripts/gen_ip_nrp.py --check
    uv run python scripts/gen_ip_nrp.py --write
    uv run python scripts/gen_ip_nrp.py --recipes
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
OUT = REPO / "data" / "raw" / "ukds_6849"
QUEX = REPO / "data" / "raw" / "ukds_6849" / "mrdoc" / "pdf" / "6849_ip_wave_10_questionnaires.pdf"
W, WAVE, YEAR = "j", 10, 2017
ALLOC = "ff_nonresw10"
NOT_ASKED = (-9, -8, -7)  # missing, inapplicable (routed out), proxy
GROUPS = (1, 2)

FH_ITEMS = ("ladopted", "lstep", "lprntadp")
CONTACT_ITEMS = ("masee", "macon", "pasee", "pacon", "chsee", "chcon")

# `lvreladp{g}{code}`: one 0/1 column per option of the code-all-that-apply
# relatives question. Codes 1/9 mother, 2/10 father, 11/12/13 sons/daughters.
LV_CODES = (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 96)

# Respondents interviewed in their own right (not proxy) who were asked
# NEITHER module: face-to-face, full interviews, answered later modules. The
# questionnaire has no route that skips both, so this is the deposit's fact, not
# ours; they hold no answer here and so produce no row. Counted 10 Oct 2026.
NEITHER_MODULE = {1: 4, 2: 3}
# Group 1 web respondents asked Family Networks (early) whose Fertility History
# (late) is coded -9 "missing": the interview stopped between the two. They are
# in the contact experiment (nothing was asked before) and not in the other.
FN_WITHOUT_LATE_FH = 2

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
# Instrument text, word-for-word from `6849_ip_wave_10_questionnaires.pdf`
# (typography only normalised). `check_text` asserts each string occurs there.
# ---------------------------------------------------------------------------
FN_OPEN = "We now have a few questions about family members who are not living here with you."
FN_REPEAT = (
    "We realise that we might be asking you to repeat some information that you gave us "
    "earlier in the survey. However, it's really important that we record all this "
    "information here, so please make sure you tell us about all your family members who "
    "don't live with you, even if you've mentioned them before."
)
LV_Q_CAPI = (
    "Excluding relatives who are living in this household with you at the moment, can you "
    "tell me which of these types of relatives you have alive at the moment? Please tell me "
    "about all relatives, even those you aren't in contact with."
)
LV_Q_WEB = (
    "Excluding relatives who are living in this household with you at the moment, please "
    "select the types of relatives you have alive at the moment? Please tell us about all "
    "relatives, even those you aren't in contact with."
)
# In the order of the Options list (codes 1, 2, 4-13, 96). A scripting note asks
# for a different display order; whether it was honoured is not recorded.
LV_OPTIONS = (
    "Mother",
    "Father",
    "Brothers/sisters",
    "Grandchildren",
    "Grandparents",
    "Great Grandchildren",
    "Great Grandparents",
    "Step/adoptive mother",
    "Step/adoptive father",
    "Biological Son(s)/daughter(s)",
    "Adopted Son(s)/daughter(s)",
    "Step Son(s)/daughter(s)",
    "None of these",
)
FH_INTRO = (
    "The next questions are about any children you have or have ever had - including "
    "biological, adopted and step-children. Because family life is changing and many more "
    "parents nowadays don't live with their children, it's really important to us that "
    "Understanding Society builds an accurate picture of what family life in the UK looks "
    "like. So, we're asking people about all of their children. So, as well as telling me "
    "about any children you currently live with, please make sure you tell me about any "
    "children you don't live with - including children you were never or are no longer in "
    "touch with, or any who may have died."
)
FH_OPEN = (
    "The next questions are about any children you have or have ever had - including "
    "biological, adopted and step-children."
)
FH_REPEAT = (
    "We realise that we might be asking you to repeat some information that you gave us "
    "earlier in the survey. However, it's really important that we record all this "
    "information here, so please make sure you tell us about all your children, even if "
    "you've mentioned them before."
)
Q_ADOPTED = (
    "Have you ever adopted a child? Please include any adopted children, even if you are "
    "not living with them or are not in touch with them."
)
Q_STEP = (
    "Have you ever lived with any step-children? Please include any step children you're "
    "currently living with and any that you've lived with in the past - even if you're no "
    "longer in touch with them."
)
# The PDF prints the fill as "[fathered/had]"; resolved per respondent on `sex`.
Q_BIO_PDF = (
    "Have you ever [fathered/had] any biological children? Please include all children, "
    "including any you never lived or no longer live with, or are not in touch with."
)
Q_BIO = Q_BIO_PDF.replace("[fathered/had]", "[IF sex=1 INSERT: fathered; IF sex=2 INSERT: had]")
YES_NO = ("Yes", "No")

MOTHER_WEB = (
    "If you have both a biological and a step or adoptive mother, we are interested in "
    "knowing about the one with whom you have the most contact."
)
FATHER_WEB = (
    "If you have both a biological and a step or adoptive father, we are interested in "
    "knowing about the one with whom you have the most contact."
)
CHILD_WEB = (
    "If you have more than one son or daughter aged 18 or over not living with you, we are "
    "interested in knowing about the one with whom you have the most contact."
)
# (interviewer-administered text, sentence the web version adds or None)
CONTACT_Q = {
    "masee": (
        "Thinking about your mother. Other than via Skype or webcam, how often do you see "
        "your mother?",
        MOTHER_WEB,
    ),
    "macon": (
        "And how often do you have contact by telephone, email, letter, Skype or webcam with "
        "your mother?",
        MOTHER_WEB,
    ),
    "pasee": (
        "Thinking now about your father. Other than via Skype or webcam, how often do you see "
        "your father?",
        FATHER_WEB,
    ),
    "pacon": (
        "And how often do you have contact by telephone, email, letter, Skype or webcam with "
        "your father?",
        FATHER_WEB,
    ),
    "chsee": (
        "Thinking now about your children aged 18 or over. If you have more than one son or "
        "daughter aged 18 or over not living with you please think about the one with whom "
        "you have the most contact. Apart from via Skype or webcam, how often do you see your "
        "son/daughter?",
        None,
    ),
    "chcon": (
        "And how often do you have contact by telephone, email, letter, Skype or webcam with "
        "your son/daughter (aged 18 or over)?",
        CHILD_WEB,
    ),
}
FREQ = (
    "Daily",
    "At least once per week",
    "At least once per month",
    "Several times per year",
    "Less often",
    "Never",
)
ALLOC_LABELS = {
    1: "Ask adapted Family Networks (Version A) module first",
    2: "Ask adapted Fertility History (Version A) module first",
}

# ---------------------------------------------------------------------------
# The conditions. Every word inside double quotes is the questionnaire's; the
# framing outside them is ours (docs/CONVENTIONS.md, "Narrating what the
# respondent did") and is recorded in each recipe's notes.
# ---------------------------------------------------------------------------


def _quoted(options: tuple[str, ...]) -> str:
    return " / ".join(f'"{o}"' for o in options)


def _by_mode(capi: str, web: str) -> str:
    """One fill per mode: interviewer-administered (1 face-to-face, 2 telephone), web (3)."""
    return f"[IF indmode=1,2 INSERT: {capi}; IF indmode=3 INSERT: {web}]"


INTRO_FRAME = "The question that follows was part of a section introduced with:"

FH_ARMS = {
    # raw value of `fn_earlier` -> (condition_num, factor, text)
    1: (
        0,
        "no",
        f'You had not been asked the questions that begin "{FN_OPEN}" earlier in the '
        f'interview. {INTRO_FRAME} "{FH_INTRO}"',
    ),
    2: (
        1,
        "yes",
        "Earlier in the interview you were asked: "
        + _by_mode(f'"{FN_OPEN} {LV_Q_CAPI}"', f'"{FN_OPEN} {LV_Q_WEB}"')
        + f" {_quoted(LV_OPTIONS)} {INTRO_FRAME} "
        + f'"{FH_INTRO} {FH_REPEAT}"',
    ),
}
CONTACT_ARMS = {
    # raw value of `fh_earlier` -> (condition_num, factor, text)
    1: (
        0,
        "no",
        f'You had not been asked the questions that begin "{FH_OPEN}" earlier in the '
        f'interview. {INTRO_FRAME} "{FN_OPEN}"',
    ),
    2: (
        1,
        "yes",
        f'Earlier in the interview you were asked the questions that begin: "{FH_INTRO}" '
        f'"{Q_ADOPTED}" {_quoted(YES_NO)} "{Q_STEP}" {_quoted(YES_NO)} {INTRO_FRAME} '
        + _by_mode(f'"{FN_OPEN} {FN_REPEAT}"', f'"{FN_OPEN}"'),
    ),
}


def _numbered(options: tuple[str, ...]) -> str:
    return " ".join(f'{i} "{o}"' for i, o in enumerate(options, 1))


def fh_question(item: str) -> str:
    q = {"ladopted": Q_ADOPTED, "lstep": Q_STEP, "lprntadp": Q_BIO}[item]
    return f"{q} {_numbered(YES_NO)}"


def contact_question(item: str) -> str:
    capi, web = CONTACT_Q[item]
    stem = capi if web is None else _by_mode(capi, f"{capi} {web}")
    return f"{stem} {_numbered(FREQ)}"


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


def person_hash(pidp: int) -> str:
    """Same construction as `scripts/build_profiles.py`. Never the raw `pidp`."""
    return "ip_" + hashlib.sha256(f"ukds6849:{pidp}".encode()).hexdigest()[:12]


def derived_name() -> str:
    return f"nrp_w{WAVE}-derived.sav"


class IdentifierSafeError(RuntimeError):
    """An error whose message carries no respondent identifier or value."""


def _merge(left: pd.DataFrame, right: pd.DataFrame, key: str, what: str) -> pd.DataFrame:
    """A left join that can never print a key (see gen_ip_automation._merge)."""
    dupes = int(right[key].duplicated().sum())
    if dupes:
        raise IdentifierSafeError(f"{what}: {dupes} duplicated join key(s) on the right")
    try:
        return left.merge(right, on=key, how="left", validate="many_to_one")
    except Exception:
        raise IdentifierSafeError(f"{what}: merge failed (keys withheld)") from None


def _lv(g: int, code: int) -> str:
    return f"{W}_lvreladp{g}{code}"


def _item_vars() -> list[str]:
    out = []
    for g in GROUPS:
        out += [f"{W}_{v}{g}" for v in FH_ITEMS + CONTACT_ITEMS]
        out += [f"{W}_{v}{g}" for v in ("biou18", "adopu18", "stepu18")]
        out += [f"{W}_{v}{g}" for v in ("biou18num", "adopu18num", "stepu18num")]
        out += [f"{W}_{v}{g}" for v in ("numbionrc", "numadoptnrc", "numstepnrc")]
        out += [_lv(g, c) for c in LV_CODES]
    return out


def _joined() -> tuple[pd.DataFrame, dict]:
    ind = spss.read(STATA / f"{W}_indresp_ip.dta")
    hhs = spss.read(STATA / f"{W}_hhsamp_ip.dta")
    nonresid = spss.read(STATA / f"{W}_nonresid_ip.dta")
    keep = ["pidp", f"{W}_hidp", f"{W}_indmode", *_item_vars(), *(f"{W}_{v}" for v in PERSONA)]
    missing = [c for c in keep if c not in ind.df.columns]
    if missing:
        raise IdentifierSafeError(f"indresp is missing {missing}")
    if f"{W}_{ALLOC}" not in hhs.df.columns:
        raise IdentifierSafeError(f"hhsamp is missing {W}_{ALLOC}")
    merged = _merge(
        ind.df[keep],
        hhs.df[[f"{W}_hidp", f"{W}_{ALLOC}"]],
        f"{W}_hidp",
        "household allocation",
    )
    # Children enumerated by the Non-Resident Identifier module, per person.
    counts = nonresid.df.groupby("pidp").size().rename("nonresid_n").reset_index()
    merged = _merge(merged, counts, "pidp", "non-resident identifier count")
    merged["nonresid_n"] = merged["nonresid_n"].fillna(0)
    labels = dict(ind.value_labels)
    labels[f"{W}_{ALLOC}"] = dict(hhs.value_labels.get(f"{W}_{ALLOC}") or {})
    return merged, labels


def _asked(col: pd.Series) -> pd.Series:
    """Put to the respondent: any code but blank, -9, -8 or -7 (DK/refusal count)."""
    return col.notna() & ~col.isin(NOT_ASKED)


def _fn_asked(df: pd.DataFrame, g: int) -> pd.Series:
    cols = [_asked(df[_lv(g, c)]) for c in LV_CODES]
    return pd.concat(cols, axis=1).any(axis=1)


def _fh_asked(df: pd.DataFrame, g: int) -> pd.Series:
    return _asked(df[f"{W}_ladopted{g}"])


def _own(df: pd.DataFrame, item: str) -> pd.Series:
    """Each respondent's answer from their own group's variable; NaN outside 1-2."""
    alloc = df[f"{W}_{ALLOC}"]
    out = pd.Series(np.nan, index=df.index)
    for g in GROUPS:
        out = out.where(alloc != g, df[f"{W}_{item}{g}"])
    return out


def derive() -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    """One row per respondent: their exposure codes, nine answers, fills, persona."""
    merged, value_labels = _joined()
    alloc = merged[f"{W}_{ALLOC}"]
    proxy = merged[f"{W}_indmode"] == -7
    out = pd.DataFrame({"person": [person_hash(int(p)) for p in merged["pidp"]]})

    # Fertility History experiment: had Family Networks been asked earlier?
    # Group 2 took Fertility History first (1, no). Group 1 took it late (2, yes),
    # provided Family Networks was in fact put to them (else -8, excluded).
    fn_earlier = np.where(alloc == 2, 1, np.where(_fn_asked(merged, 1), 2, -8))
    # Contact experiment: had Fertility History been asked earlier?
    fh_earlier = np.where(alloc == 1, 1, np.where(_fh_asked(merged, 2), 2, -8))
    out["fn_earlier"] = np.where(proxy, -7, fn_earlier)
    out["fh_earlier"] = np.where(proxy, -7, fh_earlier)
    for item in FH_ITEMS + CONTACT_ITEMS:
        out[item] = _own(merged, item).to_numpy()
    out["indmode"] = merged[f"{W}_indmode"].to_numpy()
    for v in PERSONA:
        out[v] = merged[f"{W}_{v}"].to_numpy()
    out["wave"] = WAVE
    out["year"] = YEAR

    labels: dict[str, dict[float, str]] = {}
    for v in PERSONA:
        got = value_labels.get(f"{W}_{v}")
        if got:
            labels[v] = dict(got)
    return out, labels


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def _contact_universe(df: pd.DataFrame, g: int) -> dict[str, pd.Series]:
    lv = {c: df[_lv(g, c)] == 1 for c in LV_CODES}
    mother = lv[1] | lv[9]
    father = lv[2] | lv[10]
    adult_child = (lv[11] | lv[12] | lv[13]) & (
        (df[f"{W}_biou18{g}"] == 3) | (df[f"{W}_adopu18{g}"] == 3) | (df[f"{W}_stepu18{g}"] == 3)
    )
    return {
        "masee": mother,
        "macon": mother,
        "pasee": father,
        "pacon": father,
        "chsee": adult_child,
        "chcon": adult_child,
    }


def _nonneg(col: pd.Series) -> pd.Series:
    return col.where(col > 0, 0).fillna(0)


def check_routing(merged: pd.DataFrame) -> int:
    """Allocation, order and routing, counted. Must be zero. Prints counts only."""
    bad = 0
    alloc = merged[f"{W}_{ALLOC}"]
    interviewed = merged[f"{W}_indmode"].isin([1, 2, 3])

    # 1. Every interviewed respondent holds one of the two codes.
    unalloc = int((interviewed & ~alloc.isin(GROUPS)).sum())
    print(f"  interviewed: {int(interviewed.sum()):,}; without an allocation: {unalloc}")
    bad += unalloc

    # 2. Allocation = routing: answers only in one's own group's variables, and
    #    never a blank there (a blank is no evidence of anything).
    wrong_group = blank_own = 0
    for g in GROUPS:
        other = 2 if g == 1 else 1
        mine = alloc == g
        own_cols = [c for c in _item_vars() if _group_of(c) == g]
        other_cols = [c for c in _item_vars() if _group_of(c) == other]
        for c in other_cols:
            wrong_group += int((mine & _asked(merged[c])).sum())
        for c in own_cols:
            blank_own += int((mine & merged[c].isna()).sum())
    print(f"  answers in the other group's variables: {wrong_group}; blanks in own: {blank_own}")
    bad += wrong_group + blank_own

    # 3. Which module the Non-Resident Identifier loop followed: it enumerates the
    #    children the "A" module counted. (That "A" came first is the
    #    questionnaire's module order, not something this count can show.)
    first = {
        1: sum(_nonneg(merged[f"{W}_{v}1"]) for v in ("biou18num", "adopu18num", "stepu18num")),
        2: sum(_nonneg(merged[f"{W}_{v}2"]) for v in ("numbionrc", "numadoptnrc", "numstepnrc")),
    }
    second = {
        1: sum(_nonneg(merged[f"{W}_{v}1"]) for v in ("numbionrc", "numadoptnrc", "numstepnrc")),
        2: sum(_nonneg(merged[f"{W}_{v}2"]) for v in ("biou18num", "adopu18num", "stepu18num")),
    }
    for g in GROUPS:
        mine = alloc == g
        off_first = int((mine & (merged["nonresid_n"] != first[g])).sum())
        off_second = int((mine & (merged["nonresid_n"] != second[g])).sum())
        name = "Family Networks" if g == 1 else "Fertility History"
        print(
            f"    group {g}: identifier counts differing from {name} (first): {off_first}; "
            f"from the other module: {off_second}"
        )
        bad += off_first
        # The evidence must discriminate: if the late module agreed for everyone
        # too, nothing here would show the order.
        bad += int(off_second == 0)

    # 4. Who was asked each module; the Fertility History items routed alike.
    for g in GROUPS:
        mine = (alloc == g) & interviewed
        fn, fh = _fn_asked(merged, g), _fh_asked(merged, g)
        neither = int((mine & ~fn & ~fh).sum())
        fn_only = int((mine & fn & ~fh).sum())
        fh_only = int((mine & ~fn & fh).sum())
        print(
            f"    group {g}: asked both modules {int((mine & fn & fh).sum()):,}; "
            f"neither {neither}; Family Networks only {fn_only}; Fertility History only {fh_only}"
        )
        bad += abs(neither - NEITHER_MODULE[g])
        bad += abs(fn_only - (FN_WITHOUT_LATE_FH if g == 1 else 0))
        bad += fh_only
        uneven = 0
        for v in FH_ITEMS[1:]:
            uneven += int((mine & (_asked(merged[f"{W}_{v}{g}"]) != fh)).sum())
        print(f"      Fertility History items routed differently from ladopted: {uneven}")
        bad += uneven

        # 5. Contact items: routing equals the universe computed from the
        #    respondent's own answers, exactly.
        # Routed = any code but -8 (inapplicable) or -7 (proxy): -9 "missing" is
        # an item lost INSIDE the route (one group 2 respondent's adult-child
        # pair), which yields no row but is not a routing fault.
        universe = _contact_universe(merged, g)
        off = 0
        for v in CONTACT_ITEMS:
            col = merged[f"{W}_{v}{g}"]
            routed = col.notna() & ~col.isin([-8, -7])
            off += int((mine & fn & (routed != universe[v])).sum())
            off += int((mine & ~fn & routed).sum())
        print(f"      contact items routed differently from their universe: {off}")
        bad += off
    return bad


def _group_of(col: str) -> int:
    """1 or 2: the group a suffixed variable belongs to (lvreladp carries it first)."""
    name = col[len(W) + 1 :]
    if name.startswith("lvreladp"):
        return int(name[len("lvreladp")])
    return int(name[-1])


def check_labels(labels: dict) -> int:
    # The deposit spells the User Guide's labels in lower case and without
    # "Ask adapted"; compared on the words they share, casefolded.
    got_alloc = {
        int(k): str(v).strip().casefold()
        for k, v in labels.get(f"{W}_{ALLOC}", {}).items()
        if k > 0
    }
    want = {k: v.removeprefix("Ask adapted ").casefold() for k, v in ALLOC_LABELS.items()}
    bad = int(got_alloc != want)
    for g in GROUPS:
        for v in FH_ITEMS:
            got = {int(k): str(t) for k, t in labels.get(f"{W}_{v}{g}", {}).items() if k > 0}
            bad += int(got != dict(enumerate(YES_NO, 1)))
        for v in CONTACT_ITEMS:
            got = {int(k): str(t) for k, t in labels.get(f"{W}_{v}{g}", {}).items() if k > 0}
            bad += int(got != dict(enumerate(FREQ, 1)))
    print(f"  allocation and answer labels against the documents: {bad} mismatch(es)")
    return bad


def check_answers(merged: pd.DataFrame) -> int:
    """Every answer is a code the instrument offers, or a missing code."""
    bad = 0
    for g in GROUPS:
        for v in FH_ITEMS:
            col = merged[f"{W}_{v}{g}"]
            bad += int((col.notna() & ~col.isin([1, 2, -1, -2, *NOT_ASKED])).sum())
        for v in CONTACT_ITEMS:
            col = merged[f"{W}_{v}{g}"]
            bad += int((col.notna() & ~col.isin([1, 2, 3, 4, 5, 6, -1, -2, *NOT_ASKED])).sum())
    print(f"  answers outside the offered codes and the missing codes: {bad}")
    return bad


def check_fills(merged: pd.DataFrame) -> int:
    """Every row's fills resolve: sex for "[fathered/had]", mode for the web text."""
    interviewed = merged[f"{W}_indmode"].isin([1, 2, 3])
    no_sex = int((interviewed & ~merged[f"{W}_sex"].isin([1, 2])).sum())
    print(f"  interviewed respondents without a sex for the fill: {no_sex}")
    return no_sex


def _pdf_text() -> str:
    raw = subprocess.run(
        ["pdftotext", str(QUEX), "-"], capture_output=True, text=True, check=True
    ).stdout
    raw = raw.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = " ".join(raw.split())
    # Page furniture breaks sentences that run across a page.
    return re.sub(
        r" ?\d+ of 995 \d\d/\d\d/\d{4}, \d\d:\d\d Ip10\. Understanding Society - "
        r"Innovation Panel Wave 10 http\S+",
        "",
        text,
    )


def text_expectations() -> dict[str, int]:
    """Each quoted string -> how many times it occurs in the questionnaire."""
    exp = {
        # Family Networks, early (A) and late (B): the opening screen.
        f"{FN_OPEN} {LV_Q_CAPI}": 1,  # A interviewer text; B inserts FN_REPEAT
        f"{FN_OPEN} {FN_REPEAT} {LV_Q_CAPI}": 1,  # B interviewer text
        f"{FN_OPEN} {LV_Q_WEB}": 2,  # A and B web: no repeat sentences on the web
        # Fertility History: the intro screen, early (A) and late (B, + repeat).
        FH_INTRO: 2,
        f"{FH_INTRO} {FH_REPEAT} Options 1 Continue": 1,
        f"{FH_INTRO} Options 1 Continue": 1,
        Q_ADOPTED: 2,
        Q_STEP: 2,
        Q_BIO_PDF: 2,
        # Contact items: "Text <question>" opens the interviewer block and, where the
        # web version restates it, the web block too, in A and in B. Masee1's web
        # block is overprinted by its options in the PDF (two text layers collide),
        # so the masee strings read clean three times, not four.
        **{f"Text {CONTACT_Q[v][0]}": 4 for v in ("macon", "pasee", "pacon", "chcon")},
        f"Text {CONTACT_Q['masee'][0]}": 3,
        f"Text {CONTACT_Q['chsee'][0]}": 2,  # its web block only deletes the showcard
        f"{CONTACT_Q['masee'][0]} {MOTHER_WEB}": 1,
        f"{CONTACT_Q['macon'][0]} {MOTHER_WEB}": 2,
        f"{CONTACT_Q['pasee'][0]} {FATHER_WEB}": 2,
        f"{CONTACT_Q['pacon'][0]} {FATHER_WEB}": 2,
        f"{CONTACT_Q['chcon'][0]} {CHILD_WEB}": 2,
        # Mother's age, travel time, seeing and contact, web, A and B.
        MOTHER_WEB: 8,
    }
    # Options lists print each label twice (code, text, label).
    exp[
        "Options " + " ".join(f"{c} {o} {o}" for c, o in zip(LV_CODES, LV_OPTIONS, strict=True))
    ] = 2
    # The frequency options extract out of order (two columns interleave), so
    # they are checked against the deposit's value labels instead (check_labels).
    return exp


def check_text(pdf: str | None = None) -> int:
    t = pdf if pdf is not None else _pdf_text()
    bad = 0
    for s, n in text_expectations().items():
        bad += int(t.count(s) != n)
    print(f"  questionnaire strings not found the expected number of times: {bad}")
    return bad


def check_recipe() -> int:
    bad = 0
    for kind, path in RECIPES.items():
        got = path.read_text() if path.exists() else ""
        bad += int(got != render_recipe(kind))
    print(f"  recipes differing from what this script composes: {bad}")
    return bad


def check(merged: pd.DataFrame | None = None, labels: dict | None = None) -> int:
    """Everything, counted. `merged`/`labels` default to the deposit; tests break copies."""
    if merged is None or labels is None:
        dep_merged, dep_labels = _joined()
        merged = dep_merged if merged is None else merged
        labels = dep_labels if labels is None else labels
    bad = check_routing(merged)
    bad += check_labels(labels)
    bad += check_answers(merged)
    bad += check_fills(merged)
    bad += check_text()
    bad += check_recipe()
    print(f"  {'AGREE' if bad == 0 else 'DEFECT'}")
    return bad


# ---------------------------------------------------------------------------
# Recipes
# ---------------------------------------------------------------------------

RECIPES = {
    "fh": REPO / "recipes" / "ukds_6849_nrp_w10_fh.yaml",
    "contact": REPO / "recipes" / "ukds_6849_nrp_w10_contact.yaml",
}

LICENCE = """licence: |-
  UK Data Service End User Licence (UKDS SN 6849). NOT redistributable. The EUL's
  definition of "Data Collection" includes the Documentation, so the variable and value
  labels are part of the collection as much as the microdata is. Nothing built from this
  recipe may leave the machine: `data/raw/` and `data/processed/*.parquet` are gitignored,
  and `src/micromotives_datasets/jev.py` refuses `source="ukds"` outright.
"""

COMMON_NOTES = """University of Essex, Institute for Social and Economic Research, "Understanding
Society: Innovation Panel, Waves 1-17, 2008-2024", UK Data Service SN 6849.
Experiment 9.23 in the Innovation Panel User Guide ("Non-resident parents and reasons
for separation"); wave 10 (2017). The User Guide cites no publication, and no published
table was found to verify against. GENERATED by `scripts/gen_ip_nrp.py --recipes`; do
not edit by hand. `ukds_6849_nrp_w10_fh.yaml` and `ukds_6849_nrp_w10_contact.yaml` are
the two halves.

THE DESIGN IS AN ORDER, NOT A WORDING. Two adapted modules, Family Networks (relatives
living elsewhere and how often you see them) and Fertility History (every child you have
ever had, biological, adopted or step), were both asked of everyone, one early in the
interview and the other late. The household allocation `j_ff_nonresw10` on
`j_hhsamp_ip` decided which came first (1 = Family Networks first, 2 = Fertility History
first; User Guide 9.23, 50/50). Each item is asked in the same words in either slot;
the late module's introduction adds two sentences acknowledging the repetition ("We
realise that we might be asking you to repeat some information ..."). In Family
Networks' late version those two sentences are in the interviewer text only; its web
text omits them, so the condition resolves them per row on `indmode`. Built, by rich's
ruling for 9.24 (the 9.42/9.47/9.9 pattern), on what was asked before; one answer type
per experiment (ledger 147), so two experiments.

THE ALLOCATION WAS NOT TRUSTED (ledger 138). The deposit names variables by GROUP
(suffix 1 for group 1, 2 for group 2), not by slot. `scripts/gen_ip_nrp.py --check`
finds no answer in the other group's variables and no blank in a respondent's own. The
Non-Resident Identifier module (`j_nonresid_ip`) enumerates exactly the children
Familynetworksa counted for every group 1 respondent and exactly those Fertilityhistorya
counted for every group 2 respondent (and differs from the other module's count for
some in each group). That PROVES the identifier loop followed the "A" modules, which the
specification also says. That the "A" modules ran FIRST is not proved by the data: it
rests on the questionnaire's module order (Familynetworksa and Fertilityhistorya sit
before Nonresid_ip10; the "B" modules much later), supported by the two group 1 web
break-offs who answered Family Networks and have the late Fertility History coded -9.
Routing
equals the questionnaire's universe for every contact item, computed from the
respondent's own relatives answers.

WHO WAS NOT ASKED. 89 proxy respondents (no interview of their own). Seven
face-to-face respondents with full interviews (4 in group 1, 3 in group 2) were asked
neither module, though they answered later modules; the questionnaire has no route that
does that, so this is recorded as the deposit's fact and they produce no rows. Two group
1 web respondents were asked Family Networks and then have Fertility History coded -9
(missing). Nobody was asked the late module without the early one, so the exclusion of
such respondents from the "asked earlier" arm is declared but removes no rows here.

WORD-FOR-WORD VS OURS. Wording from `6849_ip_wave_10_questionnaires.pdf`, modules
Familynetworksa/b_ip10 and Fertilityhistorya/b_ip10; `--check` asserts each quoted string
occurs there the expected number of times (page furniture removed). Inside double
quotes every word is the questionnaire's, typography normalised. ADDED BY US: "You had
not been asked the questions that begin", "earlier in the interview.", "Earlier in the
interview you were asked:" / "Earlier in the interview you were asked the questions that
begin:", "The question that follows was part of a section introduced with:", and the " / "
separators between quoted options. Interviewer instructions (e.g. "IF RESPONDENT HAS
BOTH BIOLOGICAL AND STEP/ADOPTIVE MOTHER ...", "IF NECESSARY: BY STEP-CHILDREN, I MEAN
...") and click-through Help text are not rendered: the respondent did not read them,
and the web versions carry the substance of the first as their own sentence, which IS
rendered on web rows. Telephone wording is the face-to-face wording ("READ OUT").

NOT BUILT. The relatives question itself (`lvreladp`, code all that apply: one question,
many answers; ledger 132) and the follow-ups whose answer type differs from the two built
here: ages of parents, numbers of relatives, whether parents live together or alone,
whether children under 18 live elsewhere and how many, children abroad, travel time to
mother/father, help given and received (code all that apply), the Fertility History
follow-ups (how many adopted / step / biological children, how many under 18, how many
living elsewhere), and every item about a specific non-resident child, including the
reasons for separation from the child's other parent (`j_nonresch2_ip`, one row per child,
code all that apply, asked only of the few with a non-resident child under 18). All of
these are comparable across the two orders and could each be its own experiment with its
own answer type; none is a single comparable outcome alongside these two.

`person` is a hash of `pidp`, the same construction as every Innovation Panel build.
Allocated by household, so a participant-level split puts one household's members, who
shared a condition, on both sides."""

FH_NOTES = """

THIS HALF: THE FERTILITY HISTORY QUESTIONS ASKED OF EVERYONE. "Have you ever adopted a
child?", "Have you ever lived with any step-children?" and "Have you ever [fathered/had]
any biological children?" (Yes / No; the fill is resolved per row on `sex`, 1 = Male
"fathered", 2 = Female "had", as the script does from the household grid). Each is put
to every interviewed respondent; the follow-ups are routed on the answers and are not
built. The condition is whether the Family Networks questions had been asked earlier.
"Not asked before" (group 2) quotes Family Networks' first sentence. "Asked earlier"
(group 1) quotes the Family Networks opening screen in the respondent's own mode
(interviewer "can you tell me which of these types of relatives..." / web "please select
the types of relatives...") with its thirteen options in the order of the Options list
(a scripting note asks for a different display order; whether it was honoured is not
recorded). Both then quote the Fertility History introduction screen that preceded the
three questions, with the late version's two added sentences in group 1.

PERSONA. The Innovation Panel spine WITHOUT `own_children_in_household` (`nchild_dv`):
having a child in the household nearly settles "have you ever had any biological
children", the same-domain rule that drops a persona field sitting in the outcome's
domain (CONVENTIONS, EFXNLX's `eu_referendum_vote`). Sex stays: it chooses the fill and
nothing more.

ROW COUNTS (aggregates). Don't know and refusal dropped."""

CONTACT_NOTES = """

THIS HALF: HOW OFTEN YOU SEE AND CONTACT YOUR MOTHER, FATHER AND ADULT CHILD. Six
Family Networks items on one scale (1 "Daily" .. 6 "Never"): see mother, other contact
with mother, see father, other contact with father, see a son or daughter aged 18 or over
living elsewhere, other contact with them. Each is asked only where the respondent's
own answers make it apply (a living mother or step/adoptive mother; father likewise; a
son or daughter not living here with none under 18 in the relevant category), the same
rule in both orders. That universe is set by answers given inside the module, after the
condition, so the share of respondents reaching an item could itself differ by order;
the rows are those who reached it. Measured by the independent checker (aggregates):
among those asked the relatives list, the share reaching each item, Family Networks
first vs Fertility History first, is mother 41.6% vs 40.5% (p 0.58), father 35.1% vs
34.2% (p 0.66), adult child 40.9% vs 38.8% (p 0.30): no detectable difference. But the
gating relatives question itself moved with order on other codes ("Brothers/sisters"
-7.3 percentage points, "None of these" +4.2, both p<0.001), so a small order effect on
who reports an adult child living elsewhere cannot be ruled out. The web version adds a sentence on which parent, or
which child, to think about; resolved per row on `indmode`. The condition is whether the
Fertility History questions had been asked earlier. "Not asked before" (group 1) quotes
Fertility History's first sentence. "Asked earlier" (group 2) quotes its introduction
screen and its first two questions with their options ("begin:" because more followed:
the biological-children question carries a sex fill, which is left out of the condition
so that the condition never names the respondent's own sex). Both then quote the
opening sentence of the Family Networks screen the items followed, with the late
version's two added sentences for interviewer-administered respondents in group 2.

PERSONA. The same spine as every Innovation Panel build.

ROW COUNTS (aggregates). Don't know and refusal dropped."""

PERSONA_FH = """persona_map:
  age: dvage
  sex: sex
  region: gor_dv
  employment: jbstat
  education: hiqual_dv
  marital_status: mastat_dv
  ethnicity: racel_dv
  wave: wave
  year: year

persona_missing:
  dvage: [-9, -8, -7, -2, -1]
  sex: [-9, -8, -7, -2, -1]
  gor_dv: [-9, -8, -7, -2, -1]
  jbstat: [-9, -8, -7, -2, -1]
  hiqual_dv: [-9, -8, -7, -2, -1]
  mastat_dv: [-9, -8, -7, -2, -1]
  racel_dv: [-9, -8, -7, -2, -1]
"""

PERSONA_CONTACT = """persona_map:
  age: dvage
  sex: sex
  region: gor_dv
  employment: jbstat
  education: hiqual_dv
  marital_status: mastat_dv
  ethnicity: racel_dv
  own_children_in_household: nchild_dv
  wave: wave
  year: year

persona_missing:
  dvage: [-9, -8, -7, -2, -1]
  sex: [-9, -8, -7, -2, -1]
  gor_dv: [-9, -8, -7, -2, -1]
  jbstat: [-9, -8, -7, -2, -1]
  hiqual_dv: [-9, -8, -7, -2, -1]
  mastat_dv: [-9, -8, -7, -2, -1]
  racel_dv: [-9, -8, -7, -2, -1]
  nchild_dv: [-9, -8, -7, -2, -1]
"""

# Rows per (condition, outcome), counted on the built rows 10 Oct 2026 (aggregates)
# and pinned again, independently computed, in tests/test_ip_nrp.py.
ROW_COUNTS: dict[str, str] = {
    "fh": (
        " Fertility History not preceded by Family Networks (group 2): ladopted 1,196,"
        " lstep 1,197, lprntadp 1,194 (3,587 rows). Preceded by it (group 1): 1,270, 1,268,"
        " 1,267 (3,805 rows). 7,392 rows from 2,470 respondents; lprntadp rows read"
        ' "fathered" 1,118 times and "had" 1,343. Asked-earlier rows by mode:'
        " interviewer-administered 2,231, web 1,574. The independent checker passed this"
        " experiment with 0 mismatches."
    ),
    "contact": (
        " Family Networks not preceded by Fertility History (group 1): masee 529, macon 528,"
        " pasee 446, pacon 446, chsee 517, chcon 518 (2,984 rows). Preceded by it (group 2):"
        " 484, 485, 405, 405, 463, 464 (2,706 rows). 5,690 rows from 1,869 respondents."
        " Asked-earlier rows by mode: interviewer-administered 1,698, web 1,008. The"
        " independent checker passed this experiment with 0 mismatches."
    ),
}


def _j(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def render_recipe(kind: str) -> str:
    if kind == "fh":
        title = (
            "Understanding Society Innovation Panel, experiment 9.23: ever adopted, ever lived "
            "with step-children, ever had biological children, asked before or after the "
            "questions about relatives living elsewhere (wave 10)"
        )
        notes = COMMON_NOTES + FH_NOTES + ROW_COUNTS["fh"]
        source_var, factor, arms = "fn_earlier", "fn_asked_earlier", FH_ARMS
        considered = 'fh_earlier: "the exposure code for the sibling experiment ukds_6849_nrp_w10_contact; derived by the same generator, not a second randomisation"'
        outcomes = "\n".join(
            f"  - var: {v}\n    task_num: {i}\n    question: {_j(fh_question(v))}\n"
            "    scale: {min: 1, max: 2, nominal: true}"
            for i, v in enumerate(FH_ITEMS)
        )
        recode = "{1: 1, 2: 2}"
        respondent_vars = "[indmode, sex]"
        persona = PERSONA_FH
    else:
        title = (
            "Understanding Society Innovation Panel, experiment 9.23: how often you see and "
            "contact your mother, father and adult child, asked before or after the questions "
            "about all your children (wave 10)"
        )
        notes = COMMON_NOTES + CONTACT_NOTES + ROW_COUNTS["contact"]
        source_var, factor, arms = "fh_earlier", "fh_asked_earlier", CONTACT_ARMS
        considered = 'fn_earlier: "the exposure code for the sibling experiment ukds_6849_nrp_w10_fh; derived by the same generator, not a second randomisation"'
        outcomes = "\n".join(
            f"  - var: {v}\n    task_num: {i}\n    question: {_j(contact_question(v))}\n"
            f'    scale: {{min: 1, max: 6, min_label: "{FREQ[0]}", max_label: "{FREQ[-1]}"}}'
            for i, v in enumerate(CONTACT_ITEMS)
        )
        recode = "{1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6}"
        respondent_vars = "[indmode]"
        persona = PERSONA_CONTACT
    arm_text = "\n".join(
        f"    - raw: {raw}\n      condition_num: {num}\n"
        f'      factors: {{{factor}: "{level}"}}\n      text: {_j(text)}'
        for raw, (num, level, text) in arms.items()
    )
    return f"""study_id: ukds_6849
source: innovation_panel
title: {_j(title)}
data_file: {derived_name()}
{LICENCE}
comparable_to_socsci210: false
experiment: nrp_w10_{kind}
participant_id_var: person

notes: {_j(notes)}

condition:
  source_var: {source_var}
  factors: [{factor}]
  considered_and_rejected:
    {considered}
  arms:
{arm_text}

outcomes:
{outcomes}

response_recode: {recode}

respondent_vars: {respondent_vars}

missing_codes: [-9, -8, -7, -2, -1]

{persona}"""


def write_recipes() -> None:
    for kind, path in RECIPES.items():
        path.write_text(render_recipe(kind))
        print(f"  wrote {path.relative_to(REPO)}")


# ---------------------------------------------------------------------------


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
    ap.add_argument("--check", action="store_true", help="verify routing, labels, text, recipes")
    ap.add_argument("--write", action="store_true", help="write the derived .sav file")
    ap.add_argument("--recipes", action="store_true", help="write the two recipes")
    args = ap.parse_args()

    if args.recipes:
        write_recipes()
    if args.check and check():
        raise SystemExit("check failed")

    df, labels = derive()
    for col in ("fn_earlier", "fh_earlier"):
        print(f"  {col}: {dict(sorted(df[col].value_counts().astype(int).items()))}")
    print(f"wave {WAVE}: {len(df):,} respondents")
    if args.write:
        path = OUT / derived_name()
        pyreadstat.write_sav(df, str(path), variable_value_labels=labels)
        print(f"  wrote {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
