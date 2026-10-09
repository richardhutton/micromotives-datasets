#!/usr/bin/env python3
"""Derive the data file for IP 9.20 — the same satisfaction questions in three layouts.

Wave 9 (2016). Households were split three ways (`ff_satisw9` in `i_hhsamp_ip`):
the four satisfaction questions in a grid on one screen, one per screen with the
answer options vertical, or one per screen with them horizontal. No word differs.

**Allocation is at household level**, joined to the person on `i_hidp`. indresp
carries no copy, so `--check` verifies the join the only way available: every
respondent must match a household row or be one of the 26 respondents the wave 9
deposit carries with no household allocation, none of whom answered.

**Respondents who heard the questions are excluded:** telephone respondents, and
face-to-face respondents whose interviewer read the self-completion out (`scac` = 2).
A screen layout was never shown to them, so their `layout` is -8. `--check`
reports how many answered (30 and 75).

**`pidp` is never written out.**

    uv run python scripts/gen_ip_satisfaction.py --check
    uv run python scripts/gen_ip_satisfaction.py --write
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
W, WAVE, YEAR = "i", 9, 2016
ITEMS = ("sclfsat1", "sclfsat2", "sclfsat7", "sclfsato")
TELEPHONE = 2
# scac = 2: "accepted self-completion but interviewer to complete due to
# reading/sight problems" -- the interviewer read the questions out.
READ_OUT = 2

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
    return f"satisfaction_w{WAVE}-derived.sav"


def _joined() -> tuple[pd.DataFrame, dict]:
    ind = spss.read(STATA / f"{W}_indresp_ip.dta")
    hh = spss.read(STATA / f"{W}_hhsamp_ip.dta").df
    hh = hh[[f"{W}_hidp", f"{W}_ff_satisw9"]].rename(columns={f"{W}_ff_satisw9": "alloc"})
    return ind.df.merge(hh, on=f"{W}_hidp", how="left", validate="many_to_one"), ind.value_labels


def derive() -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    df, value_labels = _joined()
    out = pd.DataFrame({"person": [person_hash(int(p)) for p in df["pidp"]]})
    layout = df["alloc"].fillna(-9).to_numpy(dtype=float)
    heard = (df[f"{W}_indmode"] == TELEPHONE) | (df[f"{W}_scac"] == READ_OUT)
    out["layout"] = np.where(heard, -8.0, layout)
    for v in ITEMS:
        out[v] = df[f"{W}_{v}"].to_numpy()
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
    """Answering respondents with no allocation (must be 0); telephone answerers excluded."""
    df, _ = _joined()
    answered = (df[[f"{W}_{v}" for v in ITEMS]] > 0).any(axis=1)
    unallocated = int((answered & df["alloc"].isna()).sum())
    phone = int((answered & (df[f"{W}_indmode"] == TELEPHONE)).sum())
    read_out = int((answered & (df[f"{W}_scac"] == READ_OUT)).sum())
    print(
        f"  {int(answered.sum()):,} answering respondents; {unallocated} with no household "
        f"allocation; {phone} by telephone and {read_out} read out by the interviewer "
        "(both excluded: they heard the questions)"
    )
    return unallocated


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify the household join")
    ap.add_argument("--write", action="store_true", help="write the derived .sav file")
    args = ap.parse_args()
    if args.check and check():
        raise SystemExit("answering respondents with no allocation")
    df, labels = derive()
    usable = df["layout"] > 0
    n = int(sum((df.loc[usable, v] > 0).sum() for v in ITEMS))
    print(f"wave {WAVE}: {n:,} answers from respondents shown a layout")
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
