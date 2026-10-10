#!/usr/bin/env python3
"""Derive the data file for IP 9.38 — national identity, which question first.

Wave 15 (2022). Self-completion module `Scaidentityexp_ip15`. Two questions,
in an order allocated by household (`o_ff_identityw15` in `o_hhsamp_ip`):

- group 1 (version A): importance of being British (0-10), then the national
  identity "choose as many or as few as apply" list;
- group 2 (version B): the national identity list, then importance of being
  British.

Only the importance-of-being-British answer is built. The national identity
list is a code-all-that-apply checklist, the shape the 9.43 ruling declines to
restructure into yes/no rows.

**The allocation is read from the routing, never the label** (ledger 138).
`--check` cross-tabulates the allocation against which version's variables hold
answers; it must find none in the other version's variables.

**New entrants are excluded.** The main interview's Ethnicity and National
Identity module asks the SAME national identity question (`NatID`) of every
new entrant never interviewed before. For them "had not been asked earlier in
the interview" is false in group 1, and in group 2 they met it twice. Excluded
from both arms, on routing into `NatID`, which is decided before allocation
matters and so keeps the randomised contrast.

**Exposure is what happened.** `natid_prior`: 1 = the national identity
question had not been asked earlier (version A routed); 2 = it had (version B
routed, its national identity question asked); -8 = neither, or a new entrant.

**`pidp` is never written out.** Nothing respondent-level is printed.

    uv run python scripts/gen_ip_natid.py --check
    uv run python scripts/gen_ip_natid.py --write
"""

from __future__ import annotations

import argparse
import hashlib
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
W, WAVE, YEAR = "o", 15, 2022
ALLOC = "ff_identityw15"
NOT_ROUTED = -8
#: Codes meaning "this person was never shown the variable": inapplicable, proxy.
NOT_ASKED = (-8, -7)
#: The version each allocation code routes into, per the questionnaire.
VERSION = {1: "a", 2: "b"}
NATID_ITEMS = ("1", "2", "3", "4", "5", "6", "97")

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


def derived_name() -> str:
    return f"natid_w{WAVE}-derived.sav"


def _joined() -> tuple[pd.DataFrame, dict]:
    ind = spss.read(STATA / f"{W}_indresp_ip.dta")
    hh = spss.read(STATA / f"{W}_hhsamp_ip.dta").df
    hh = hh[[f"{W}_hidp", f"{W}_{ALLOC}"]].rename(columns={f"{W}_{ALLOC}": "alloc"})
    df = ind.df.merge(hh, on=f"{W}_hidp", how="left", validate="many_to_one")
    if df["alloc"].isna().any():
        raise ValueError("respondents with no household allocation row")
    return df, ind.value_labels


def _routed(df: pd.DataFrame, var: str) -> pd.Series:
    """Shown the variable: anything but inapplicable or proxy (incl. DK/refused/missing)."""
    return ~df[f"{W}_{var}"].isin(NOT_ASKED)


def _new_entrant_natid(df: pd.DataFrame) -> pd.Series:
    """Routed into the main interview's own national identity question."""
    return _routed(df, "natid1")


def derive() -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    df, value_labels = _joined()
    out = pd.DataFrame({"person": [person_hash(int(p)) for p in df["pidp"]]})
    a_brit, b_brit = _routed(df, "scbritida"), _routed(df, "scbritidb")
    b_natid = _routed(df, "scnatidb1")
    excluded = _new_entrant_natid(df)
    prior = np.full(len(df), float(NOT_ROUTED))
    prior = np.where(a_brit & ~b_brit, 1.0, prior)
    prior = np.where(b_brit & b_natid & ~a_brit, 2.0, prior)
    prior = np.where(excluded, float(NOT_ROUTED), prior)
    out["natid_prior"] = prior
    out["brit"] = np.where(
        prior == 1.0,
        df[f"{W}_scbritida"],
        np.where(prior == 2.0, df[f"{W}_scbritidb"], float(NOT_ROUTED)),
    ).astype(float)
    for v in PERSONA:
        out[v] = df[f"{W}_{v}"].to_numpy()
    out["wave"] = WAVE
    out["year"] = YEAR
    labels: dict[str, dict[float, str]] = {}
    for v in PERSONA:
        got = value_labels.get(f"{W}_{v}")
        if got:
            labels[v] = dict(got)
    return out, labels


def check() -> int:
    """Every routing inconsistency, counted. Must be 0; `--check` exits non-zero otherwise.

    Counts: answers in the version the allocation does not route into; routed
    respondents from unallocated households; respondents routed into one of a
    version's two questions but not the other; new entrants carrying a derived
    condition; derived conditions that disagree with the household allocation.

    Prints aggregate counts only: the allocation against every experiment
    variable's routed status, and the exclusions.
    """
    df, _ = _joined()
    bad = 0
    for var in ("scbritid", "scnatid"):
        for code, version in VERSION.items():
            other = VERSION[3 - code]
            col = f"{var}{other}" if var == "scbritid" else f"{var}{other}1"
            stray = int(((df["alloc"] == code) & _routed(df, col)).sum())
            own = f"{var}{version}" if var == "scbritid" else f"{var}{version}1"
            mine = int(((df["alloc"] == code) & _routed(df, own)).sum())
            print(
                f"  alloc {code}: {mine:,} routed into {own}, {stray} into the other "
                f"version's {col}"
            )
            bad += stray
    unalloc = int(
        ((df["alloc"] <= 0) & (_routed(df, "scbritida") | _routed(df, "scbritidb"))).sum()
    )
    print(f"  {unalloc} routed respondents from households with no allocation")
    # Inside each version both questions share one universe; they must agree.
    for v in VERSION.values():
        disagree = int((_routed(df, f"scbritid{v}") != _routed(df, f"scnatid{v}1")).sum())
        print(f"  version {v}: {disagree} respondents routed into one question but not the other")
        bad += disagree
    derived, _ = derive()
    entrants = _new_entrant_natid(df)
    for code in VERSION:
        n = int((entrants & (df["alloc"] == code) & _routed(df, f"scbritid{VERSION[code]}")).sum())
        print(f"  alloc {code}: {n} new entrants asked NatID in the main interview (excluded)")
    # The DERIVED exposure, not the inputs (ledger 121): a new entrant must carry
    # none, and every exposure must be the one its household was allocated.
    prior = derived["natid_prior"].to_numpy()
    leaked = int((entrants.to_numpy() & (prior > 0)).sum())
    print(f"  {leaked} new entrants carrying a condition")
    expected = {1.0: 1, 2.0: 2}
    mismatched = sum(
        int(((prior == p) & (df["alloc"].to_numpy() != code)).sum()) for p, code in expected.items()
    )
    print(f"  {mismatched} derived conditions disagreeing with the household allocation")
    print(f"  natid_prior: {derived['natid_prior'].value_counts().sort_index().to_dict()}")
    return bad + unalloc + leaked + mismatched


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify routing against allocation")
    ap.add_argument("--write", action="store_true", help="write the derived .sav file")
    args = ap.parse_args()
    if args.check and check():
        raise SystemExit("routing disagrees with allocation")
    df, labels = derive()
    usable = df["natid_prior"] > 0
    in_scale = df["brit"].between(0, 10)
    for p in (1.0, 2.0):
        n = int((usable & in_scale & (df["natid_prior"] == p)).sum())
        print(f"natid_prior={int(p)}: {n:,} in-scale importance answers")
    print(f"  code 11 (not British, spontaneous): {int((usable & (df['brit'] == 11)).sum())}")
    if args.write:
        narrow = df.copy()
        for col in narrow.columns:
            if narrow[col].dtype == "object" or str(narrow[col].dtype).startswith("string"):
                narrow[col] = narrow[col].astype(object).where(narrow[col].notna(), np.nan)
        path = OUT / derived_name()
        pyreadstat.write_sav(narrow, str(path), variable_value_labels=labels)
        print(f"  wrote {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
