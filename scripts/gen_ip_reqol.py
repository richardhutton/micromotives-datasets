#!/usr/bin/env python3
"""Derive the data file for IP 9.31 — ReQoL-10 and EQ-5D-3L against the GHQ-12, in order.

Wave 14 (2021). Half the respondents answered the ReQoL-10 (plus its physical
health item) and the EQ-5D-3L early in the interview and the GHQ-12 late (arm
1); the other half the reverse (arm 2). Built as two experiments, the ReQoL and
EQ-5D answers and the GHQ answers, each conditioned on whether the OTHER block
had been asked earlier — rich's ruling for 9.24, applied to the same design.

This script does what a recipe cannot:

**The allocation lives in two variables, and one of them is wrong for half the
sample.** For the continuing sample the arm was allocated in the script and is
`n_req10cond`. For the wave 14 refreshment sample (`hhorig` = 19) it was
allocated by household before fieldwork and is `n_ff_req10cond` in
`n_hhsamp_ip`. For refreshment respondents `n_req10cond` also holds a value,
and it bears no relation to what they were asked (253/226 and 252/233 across
the two blocks); `n_ff_req10cond` matches exactly. `arm` takes each from the
right place, and `--check` confirms that no answer sits in a module the arm did
not use.

**One variable per item per instrument**, merged from the early or late module
the arm used.

**Exposure is what happened.** `prior_reqol` (for the ReQoL/EQ-5D answers) and
`prior_ghq` (for the GHQ answers): 1 = the other block had not been asked
before, 2 = it had been asked earlier, -8 = the arm put it first but the
respondent was not routed into that early module, so "earlier you were asked"
would be false; excluded.

**`pidp` is never written out.**

    uv run python scripts/gen_ip_reqol.py --check
    uv run python scripts/gen_ip_reqol.py --write
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
W, WAVE, YEAR = "n", 14, 2021
REFRESHMENT = 19
NOT_ROUTED = -8

REQOL = [f"reqol{i}" for i in range(1, 11)] + ["reqphys"]
EQ5D = ["eq3lmob", "eq3lcare", "eq3lact", "eq3lpain", "eq3lanx"]
GHQ = [f"scghq{c}" for c in "abcdefghijkl"]
BLOCKS = {"reqol": REQOL + EQ5D, "ghq": GHQ}
# The arm in which each block came EARLY.
EARLY_IN = {"reqol": 1, "ghq": 2}

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
    return f"reqol_w{WAVE}-derived.sav"


def _arm(df: pd.DataFrame) -> pd.Series:
    """The arm actually allocated: household variable for the refreshment sample."""
    refresh = df[f"{W}_hhorig"] == REFRESHMENT
    return df[f"{W}_req10cond"].where(~refresh, df["hh_arm"]).fillna(-9)


def _routed(df: pd.DataFrame, items: list[str], when: str) -> pd.Series:
    return (df[[f"{W}_{v}{when}" for v in items]] != NOT_ROUTED).any(axis=1)


def derive() -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    ind = spss.read(STATA / f"{W}_indresp_ip.dta")
    hh = spss.read(STATA / f"{W}_hhsamp_ip.dta").df
    hh = hh[[f"{W}_hidp", f"{W}_ff_req10cond"]].rename(columns={f"{W}_ff_req10cond": "hh_arm"})
    df = ind.df.merge(hh, on=f"{W}_hidp", how="left", validate="many_to_one")
    arm = _arm(df)

    out = pd.DataFrame({"person": [person_hash(int(p)) for p in df["pidp"]]})
    out["arm"] = arm.to_numpy()
    out["indmode"] = df[f"{W}_indmode"].to_numpy()
    for block, items in BLOCKS.items():
        early = EARLY_IN[block]
        for v in items:
            value = pd.Series(float(NOT_ROUTED), index=df.index)
            value = value.where(arm != early, df[f"{W}_{v}ear"])
            value = value.where(arm != 3 - early, df[f"{W}_{v}lat"])
            out[v] = value.to_numpy()
        other = "ghq" if block == "reqol" else "reqol"
        saw_other_early = _routed(df, BLOCKS[other], "ear")
        prior = np.where(arm == early, 1.0, float(NOT_ROUTED))
        prior = np.where(arm == 3 - early, np.where(saw_other_early, 2.0, float(NOT_ROUTED)), prior)
        out[f"prior_{block}"] = prior
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
    """Answers in a module the respondent's arm did not use. Must be 0."""
    ind = spss.read(STATA / f"{W}_indresp_ip.dta").df
    derived, _ = derive()
    arm = derived["arm"].to_numpy()
    bad = 0
    for block, items in BLOCKS.items():
        early = EARLY_IN[block]
        for v in items:
            bad += int(((arm != early) & (ind[f"{W}_{v}ear"] > 0)).sum())
            bad += int(((arm != 3 - early) & (ind[f"{W}_{v}lat"] > 0)).sum())
    for p in ("prior_reqol", "prior_ghq"):
        counts = derived.groupby([p, "arm"]).size()
        print(
            f"  {p}: "
            + ", ".join(f"code {int(a)} arm {int(b)}: {n}" for (a, b), n in counts.items() if b > 0)
        )
    print(f"  {bad} answers in a module the arm did not use")
    return bad


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify allocation against answers")
    ap.add_argument("--write", action="store_true", help="write the derived .sav file")
    args = ap.parse_args()
    if args.check and check():
        raise SystemExit("answers in a module the arm did not use")
    df, labels = derive()
    for block, items in BLOCKS.items():
        usable = df[f"prior_{block}"] > 0
        n = int(sum((df.loc[usable, v] > 0).sum() for v in items))
        print(f"{block}: {n:,} answers from respondents with a known exposure")
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
