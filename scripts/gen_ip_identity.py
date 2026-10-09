#!/usr/bin/env python3
"""Derive the data file for IP 9.4 — "occupation" or "profession" in an identity battery.

Wave 2 (2009). Respondents rated how important thirteen things are to their
sense of who they are. The first was worded "Your occupation?" (group 1) or
"Your profession?" (group 2), allocated by household; the other twelve are the
same in both versions.

**Allocation is at household level**, in `b_hhsamp_ip`, joined to the person on
`b_hidp`. `b_indresp_ip` carries its own copy, so `--check` compares the joined
allocation with that copy row for row: they must agree exactly or the join is
scrambling who saw which word.

**`pidp` is never written out.** `person` is the same hash as every other
Innovation Panel build.

    uv run python scripts/gen_ip_identity.py --check
    uv run python scripts/gen_ip_identity.py --write
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
W, WAVE, YEAR = "b", 2, 2009
ALLOC = "ff_identityw2"
# Item (a) in each version. Items (b)-(m) are identical across versions.
ITEM_A = {1: "ethexp_aa", 2: "ethexp_ba"}

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
    return f"identity_w{WAVE}-derived.sav"


def _joined() -> tuple[pd.DataFrame, dict]:
    ind = spss.read(STATA / f"{W}_indresp_ip.dta")
    hh = spss.read(STATA / f"{W}_hhsamp_ip.dta")
    hh_alloc = hh.df[[f"{W}_hidp", f"{W}_{ALLOC}"]].rename(columns={f"{W}_{ALLOC}": "version"})
    merged = ind.df.merge(hh_alloc, on=f"{W}_hidp", how="left", validate="many_to_one")
    unmatched = int(merged["version"].isna().sum())
    if unmatched:
        raise ValueError(f"{unmatched} respondents have no household allocation row")
    return merged, ind.value_labels


def derive() -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    merged, value_labels = _joined()
    out = pd.DataFrame({"person": [person_hash(int(p)) for p in merged["pidp"]]})
    out["version"] = merged["version"].to_numpy()
    for var in ITEM_A.values():
        out[var] = merged[f"{W}_{var}"].to_numpy()
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
    """The DERIVED allocation against indresp's own copy, row for row."""
    ind = spss.read(STATA / f"{W}_indresp_ip.dta").df
    derived, _ = derive()
    if len(derived) != len(ind):
        raise ValueError(f"derived {len(derived)} rows from {len(ind)}")
    mine, theirs = derived["version"].to_numpy(), ind[f"{W}_{ALLOC}"].to_numpy()
    both = (mine > 0) & (theirs > 0)
    bad = int((mine[both] != theirs[both]).sum())
    stray = sum(
        int(((derived["version"] == v) & (derived[ITEM_A[3 - v]] > 0)).sum()) for v in (1, 2)
    )
    print(
        f"  {int(both.sum()):,} comparisons of the joined allocation against indresp's copy — "
        f"{'AGREE' if bad == 0 else f'{bad} DISAGREEMENTS'}; {stray} answers in the other "
        "version's variable"
    )
    return bad + stray


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify the household join")
    ap.add_argument("--write", action="store_true", help="write the derived .sav file")
    args = ap.parse_args()
    if args.check and check():
        raise SystemExit("allocation disagreements")
    df, labels = derive()
    answered = int(sum((df[v] > 0).sum() for v in ITEM_A.values()))
    print(f"wave {WAVE}: {len(df):,} respondents, {answered:,} answers to item (a)")
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
