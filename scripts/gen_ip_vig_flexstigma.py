#!/usr/bin/env python3
"""Derive the data file for IP 9.39 — flexibility stigma in hiring.

Wave 16 (2023). Employed respondents aged 18-65, imagining themselves as an HR
manager, read three job candidates and rated each on four 0-10 questions:
whether they would recommend the candidate, and how they see the candidate's
work commitment, productivity and team-playing. Five dimensions vary per
candidate: gender (carried by the name), parenthood, the candidate's own home
working, how common home working is in the company, and company policy.
2 x 2 x 3 x 4 x 4 = 192 cells per slot.

The recipe (`recipes/ukds_6849_vig_flexstigma_w16.yaml`) holds the judgement.
This script does what a recipe cannot:

**One name coding across all three slots.** Each slot has its own pair of names
— `fsvigname1` is 1 = Charlotte Davies, 2 = Paul Taylor; `fsvigname2` is Anna
Wright / Adam Newton; `fsvigname3` Sarah Walker / James Harrison — all coded
1/2. `by_raw` keys arms on codes, so a shared code 1 would put Charlotte in
slot 2. The derived `name1-3` use one six-name coding (`NAMES`), resolved
through each slot's OWN value labels, and `--check` verifies every derived name
against those labels.

**The prefix is stripped and `pidp` is never written out.** `person` is the
same hash as the other Innovation Panel builds, so one person keeps one id
across experiments.

    uv run python scripts/gen_ip_vig_flexstigma.py --check
    uv run python scripts/gen_ip_vig_flexstigma.py --write
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
W, WAVE, YEAR = "p", 16, 2023

# The four non-name dimensions, archive names without prefix or slot.
DIMS = ("fsvigparent", "fsvighybrid", "fsvigorguse", "fsvigorgpol")
# The four ratings per candidate, in the order the questionnaire asks them.
ITEMS = ("fsvrecomm", "fsvcommit", "fsvproduct", "fsvteam")

# One coding for all six names. The recipe's levels are keyed on it.
NAMES = {
    1: "Charlotte Davies",
    2: "Paul Taylor",
    3: "Anna Wright",
    4: "Adam Newton",
    5: "Sarah Walker",
    6: "James Harrison",
}
CODE = {name: code for code, name in NAMES.items()}

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
    return f"vig_flexstigma_w{WAVE}-derived.sav"


def derive() -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    """One row per respondent: three candidates, twelve ratings, persona."""
    r = spss.read(STATA / f"{W}_indresp_ip.dta")
    df = r.df
    needed = ["pidp"]
    needed += [f"{W}_fsvigname{i}" for i in (1, 2, 3)]
    needed += [f"{W}_{d}{i}" for d in DIMS for i in (1, 2, 3)]
    needed += [f"{W}_{it}{i}" for it in ITEMS for i in (1, 2, 3)]
    needed += [f"{W}_{v}" for v in PERSONA]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"indresp is missing {missing}")

    out = pd.DataFrame({"person": [person_hash(int(p)) for p in df["pidp"]]})
    for i in (1, 2, 3):
        var = f"{W}_fsvigname{i}"
        lab = r.value_labels[var]
        raw = df[var]
        names = raw.map(lambda c, lab=lab: lab.get(c) if c > 0 else None)
        unknown = set(names.dropna()) - set(CODE)
        if unknown:
            raise ValueError(f"slot {i}: names outside the declared six: {sorted(unknown)}")
        # Unallocated slots keep the archive's own negative code.
        out[f"name{i}"] = np.where(
            names.notna(), names.map(CODE).fillna(-9).to_numpy(), raw.to_numpy()
        ).astype(float)
        for d in DIMS:
            out[f"{d}{i}"] = df[f"{W}_{d}{i}"].to_numpy()
        for it in ITEMS:
            out[f"{it}{i}"] = df[f"{W}_{it}{i}"].to_numpy()
    for v in PERSONA:
        out[v] = df[f"{W}_{v}"].to_numpy()
    out["wave"] = WAVE
    out["year"] = YEAR

    labels: dict[str, dict[float, str]] = {}
    for v in PERSONA:
        got = r.value_labels.get(f"{W}_{v}")
        if got:
            labels[v] = dict(got)
    for i in (1, 2, 3):
        labels[f"name{i}"] = {float(c): n for c, n in NAMES.items()}
    return out, labels


def check() -> int:
    """Every derived name against the archive's own label for that slot."""
    r = spss.read(STATA / f"{W}_indresp_ip.dta")
    derived, _ = derive()
    if len(derived) != len(r.df):
        raise ValueError(f"derived {len(derived)} rows from {len(r.df)}")
    bad = compared = 0
    for i in (1, 2, 3):
        var = f"{W}_fsvigname{i}"
        lab = r.value_labels[var]
        for mine, theirs in zip(derived[f"name{i}"], r.df[var], strict=True):
            if theirs > 0:
                compared += 1
                bad += NAMES.get(int(mine)) != lab[theirs]
    print(
        f"  {compared:,} derived names compared with each slot's own labels — "
        f"{'AGREE' if bad == 0 else f'{bad} DISAGREEMENTS'}"
    )
    report_allocation(derived)
    return bad


def report_allocation(derived: pd.DataFrame) -> dict[str, int]:
    """How random the allocation was. Reported, never a failure."""
    cols = [f"name{i}" for i in (1, 2, 3)] + [f"{d}{i}" for i in (1, 2, 3) for d in DIMS]
    a = derived[derived["name1"] > 0]
    counts = a[cols].astype(int).astype(str).agg("".join, axis=1).value_counts()
    out = {
        "allocated": len(a),
        "distinct": int(counts.size),
        "in_repeated": int(counts[counts > 1].sum()),
    }
    print(
        f"  {out['allocated']:,} allocated, {out['distinct']:,} distinct allocations, "
        f"{out['in_repeated']:,} sharing one"
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify the name harmonisation")
    ap.add_argument("--write", action="store_true", help="write the derived .sav file")
    args = ap.parse_args()

    if args.check and check():
        raise SystemExit("name disagreements")

    df, labels = derive()
    rated = int(sum((df[f"{it}{i}"] >= 0).sum() for it in ITEMS for i in (1, 2, 3)))
    print(f"wave {WAVE}: {len(df):,} respondents, {rated:,} ratings given")
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
