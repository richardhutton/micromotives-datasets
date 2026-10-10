#!/usr/bin/env python3
"""Derive the data file for IP 9.34 — the marginal propensity to consume.

Wave 15 (2022). Three household-level allocations in `o_hhsamp_ip`, crossed and
each split half and half (User Guide 9.34):

- `ff_mpctreatment`: 1 = two-part question (spend more / the same / less, then
  how much), 2 = direct question (how much of it would you spend);
- `ff_mpcduration`: 1 = over the next 3 months, 2 = over the next 12 months;
- `ff_mpcamount`: 1 = a £500 one-time payment, 2 = £2500.

The recipes hold the judgement, one per question format, both reading this one
derived file: `recipes/ukds_6849_mpc_twopart_w15.yaml` and
`recipes/ukds_6849_mpc_direct_w15.yaml`. This script does what a recipe cannot, because the pipeline reads one file and the allocation
is in another: it joins the three allocations to the person on `o_hidp`.

`--check` cross-tabulates each allocation against the routing it should have
caused (ledger 134, 138), which is the only evidence the data holds that the
labels mean what they say:

- treatment: two-part respondents answer only `t1mpc*`, direct ones only `t2mpc*`;
- amount, direct arm: `t2mpc1500` is asked only under amount 1, `t2mpc12500`
  only under amount 2;
- amount, two-part arm: the follow-up `t1mpc3same*` is routed on whether the
  stated increase is below £500 (amount 1) or £2500 (amount 2), so the routing
  of every respondent who stated an increase must agree with their amount code;
- duration: changes only the wording, never the routing, so the data cannot
  confirm it. Recorded as such rather than claimed.

**`pidp` is never written out.** `person` is the same hash as every other
Innovation Panel build. Nothing here prints a respondent-level value; every line
of output is a count.

    uv run python scripts/gen_ip_mpc.py --check
    uv run python scripts/gen_ip_mpc.py --write
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

ALLOC = {
    "mpctreatment": "ff_mpctreatment",
    "mpcduration": "ff_mpcduration",
    "mpcamount": "ff_mpcamount",
}
T1 = ("t1mpc1", "t1mpc2inc", "t1mpc2red", "t1mpc3same1")
T2 = ("t2mpc1500", "t2mpc12500", "t2mpc21")
ANSWERS = ("t1mpc1", "t2mpc1500", "t2mpc12500")

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
    return f"mpc_w{WAVE}-derived.sav"


def _joined() -> tuple[pd.DataFrame, dict]:
    ind = spss.read(STATA / f"{W}_indresp_ip.dta")
    hh = spss.read(STATA / f"{W}_hhsamp_ip.dta")
    items = sorted({*T1, *T2, *ANSWERS})
    keep = ["pidp", f"{W}_hidp", *(f"{W}_{v}" for v in items), *(f"{W}_{v}" for v in PERSONA)]
    missing = [c for c in keep if c not in ind.df.columns]
    if missing:
        raise ValueError(f"indresp is missing {missing}")
    alloc = [f"{W}_{v}" for v in ALLOC.values()]
    merged = ind.df[keep].merge(
        hh.df[[f"{W}_hidp", *alloc]], on=f"{W}_hidp", how="left", validate="many_to_one"
    )
    unmatched = int(merged[alloc[0]].isna().sum())
    if unmatched:
        raise ValueError(f"{unmatched} respondents have no household allocation row")
    return merged, ind.value_labels


def derive() -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    """One row per respondent: their three allocations, their answers, their persona."""
    merged, value_labels = _joined()
    out = pd.DataFrame({"person": [person_hash(int(p)) for p in merged["pidp"]]})
    for name, var in ALLOC.items():
        out[name] = merged[f"{W}_{var}"].to_numpy()
    for v in ANSWERS:
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
    """Answers the allocation says could not have been asked. Must be zero."""
    merged, _ = _joined()
    treat = merged[f"{W}_ff_mpctreatment"]
    amount = merged[f"{W}_ff_mpcamount"]

    def answered(v: str) -> pd.Series:
        return merged[f"{W}_{v}"] >= 0

    bad = 0
    t1_any = pd.concat([answered(v) for v in T1], axis=1).any(axis=1)
    t2_any = pd.concat([answered(v) for v in T2], axis=1).any(axis=1)
    wrong_t1 = int((t1_any & (treat != 1)).sum())
    wrong_t2 = int((t2_any & (treat != 2)).sum())
    print(
        f"  treatment: {int((t1_any & (treat == 1)).sum()):,} two-part answerers under 1, "
        f"{wrong_t1} elsewhere; {int((t2_any & (treat == 2)).sum()):,} direct answerers "
        f"under 2, {wrong_t2} elsewhere"
    )
    bad += wrong_t1 + wrong_t2

    wrong_500 = int((answered("t2mpc1500") & (amount != 1)).sum())
    wrong_2500 = int((answered("t2mpc12500") & (amount != 2)).sum())
    print(
        f"  amount (direct): {int(answered('t2mpc1500').sum()):,} answers to the £500 item, "
        f"{wrong_500} outside amount 1; {int(answered('t2mpc12500').sum()):,} to the £2500 "
        f"item, {wrong_2500} outside amount 2"
    )
    bad += wrong_500 + wrong_2500

    # Two-part arm: T1MPC3SAME is asked after a stated increase only when that
    # increase is below the payment, so its routing reveals the amount code.
    inc = merged[f"{W}_t1mpc2inc"]
    stated = (treat == 1) & (merged[f"{W}_t1mpc1"] == 1) & (inc >= 0)
    limit = np.where(amount == 1, 500, np.where(amount == 2, 2500, np.nan))
    predicted = inc < limit
    asked = merged[f"{W}_t1mpc3same1"] != -8
    disagree = int((stated & (predicted != asked)).sum())
    print(
        f"  amount (two-part): {int(stated.sum()):,} stated increases, follow-up routing "
        f"disagrees with the amount code for {disagree}"
    )
    bad += disagree

    print("  duration: changes wording only, never routing; not checkable from the data")
    for name, var in ALLOC.items():
        got = merged[f"{W}_{var}"]
        ans = pd.concat([answered(v) for v in ANSWERS], axis=1).any(axis=1)
        counts = got[ans].value_counts().sort_index().to_dict()
        print(f"  {name}: answerers by code {counts}")
    print(f"  {'AGREE' if bad == 0 else 'ROUTING DISAGREES WITH ALLOCATION'}")
    return bad


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify allocation against routing")
    ap.add_argument("--write", action="store_true", help="write the derived .sav file")
    args = ap.parse_args()

    if args.check and check():
        raise SystemExit("answers found outside the allocated routing")

    df, labels = derive()
    answered = int(sum((df[v] >= 0).sum() for v in ANSWERS))
    print(f"wave {WAVE}: {len(df):,} respondents, {answered:,} answers to the three items")
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
