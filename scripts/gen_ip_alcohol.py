#!/usr/bin/env python3
"""Derive the data file for IP 9.36 — alcohol asked in units or in drinks.

Wave 15 (2022). Households were split in two. Version A (the NHS wording) asked
how many UNITS of alcohol the respondent drinks on a typical drinking day and how
often they have 6 (women) or 8 (men) or more units on one occasion; version B
asked the same two questions in ALCOHOLIC DRINKS. Only those who had drunk in the
past 12 months were asked either.

The recipe (`recipes/ukds_6849_alcohol_w15.yaml`) holds the judgement. This
script does what a recipe cannot, because the pipeline reads one file and the
allocation is in another:

**Allocation is at household level**, in `o_hhsamp_ip`, joined to the person on
`o_hidp`. `--check` verifies the join the only way the data allows: a person's
answers must sit only in their own version's variables (`auditc4a/5a` for A,
`auditc4b/5b` for B), so any answer in the other version's variables would mean
the join put them in the wrong household.

**`pidp` is never written out.** `person` is the same hash as every other
Innovation Panel build.

    uv run python scripts/gen_ip_alcohol.py --check
    uv run python scripts/gen_ip_alcohol.py --write
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

ALLOC = "ff_alcoholw15"
ITEMS = {1: ("auditc4a", "auditc5a"), 2: ("auditc4b", "auditc5b")}

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
    return f"alcohol_w{WAVE}-derived.sav"


def _joined() -> tuple[pd.DataFrame, dict]:
    ind = spss.read(STATA / f"{W}_indresp_ip.dta")
    hh = spss.read(STATA / f"{W}_hhsamp_ip.dta")
    answers = [f"{W}_{v}" for pair in ITEMS.values() for v in pair]
    keep = ["pidp", f"{W}_hidp", *answers, *(f"{W}_{v}" for v in PERSONA)]
    missing = [c for c in keep if c not in ind.df.columns]
    if missing:
        raise ValueError(f"indresp is missing {missing}")
    merged = ind.df[keep].merge(
        hh.df[[f"{W}_hidp", f"{W}_{ALLOC}"]], on=f"{W}_hidp", how="left", validate="many_to_one"
    )
    unmatched = int(merged[f"{W}_{ALLOC}"].isna().sum())
    if unmatched:
        raise ValueError(f"{unmatched} respondents have no household allocation row")
    return merged, ind.value_labels


def derive() -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    """One row per respondent: their version, their answers, their persona."""
    merged, value_labels = _joined()
    out = pd.DataFrame({"person": [person_hash(int(p)) for p in merged["pidp"]]})
    out["version"] = merged[f"{W}_{ALLOC}"].to_numpy()
    for pair in ITEMS.values():
        for v in pair:
            out[v] = merged[f"{W}_{v}"].to_numpy()
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


def check() -> int:
    """Answers outside the respondent's own version's variables. Must be zero."""
    derived, _ = derive()
    bad = answered = 0
    for version, own in ITEMS.items():
        other = ITEMS[3 - version]
        in_arm = derived["version"] == version
        answered += int((derived.loc[in_arm, list(own)] > 0).sum().sum())
        bad += int((derived.loc[in_arm, list(other)] > 0).sum().sum())
    print(
        f"  {answered:,} answers in the respondent's own version's variables, "
        f"{bad} in the other version's — {'AGREE' if bad == 0 else 'JOIN DEFECT'}"
    )
    return bad


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify the household join")
    ap.add_argument("--write", action="store_true", help="write the derived .sav file")
    args = ap.parse_args()

    if args.check and check():
        raise SystemExit("answers found in the other version's variables")

    df, labels = derive()
    answered = int(sum((df[v] > 0).sum() for pair in ITEMS.values() for v in pair))
    print(f"wave {WAVE}: {len(df):,} respondents, {answered:,} answers to the two items")
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
