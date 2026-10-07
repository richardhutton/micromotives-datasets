#!/usr/bin/env python3
"""Derive the data file for IP 9.10 — satisfaction with the sharing of housework.

Waves 5 and 6. Each respondent read three made-up scenarios describing a couple's
work and housework arrangement — themselves and a partner — and rated how
satisfied they would be with how the housework was shared. Five dimensions were
randomised: paid work, relative earnings, children, the housework split, and
whether paid help was employed. 4 x 3 x 4 x 5 x 2 = 480 possible scenarios, all
480 of which occur.

The recipes (`recipes/ukds_6849_vig_housework_w{5,6}.yaml`) hold the judgment:
the condition template, the five dimensions and their word-for-word clauses, the
persona map. This script does the one thing a recipe cannot, because the pipeline
reads a single file and this study's assignment is spread over two:

**Allocation is at household level.** The fifth dimension, paid help, exists ONLY
in `{w}_hhsamp_ip`; four of the five are duplicated into `{w}_indresp_ip` but paid
help is not, and wave 6's indresp carries none of them. So all five are read from
`hhsamp` and joined to the person on `{w}_hidp`. Two people in the same household
therefore saw identical scenarios — the design, not a fault: same condition, two
different answers, which is exactly the variation a predictor has to earn.

Wave 5 duplicating four dimensions makes the join checkable, and `--check`
checks it: 23,880 comparisons between the household-level source and the
person-level copy, which must agree exactly or the join is scrambling who saw
what. Wave 6 has no such copy, so `--check` says so rather than reporting a
pass it did not earn.

Two further things this script does, both of which would otherwise be silent:

- **The wave prefix is stripped.** `e_vig1` and `f_vig1` both become `vig1`, so
  one recipe shape serves both waves and the dimension names in the template are
  wave-free. Only `data_file` and `experiment` differ between the two recipes.
- **`pidp` is never written out.** It is the Understanding Society person
  identifier and links to the whole study, so the derived file carries
  `person`, a hash of it, matching `scripts/build_profiles.py` so a row here
  resolves to a profile there. The same person keeps the same hash across waves,
  which is the panel link; `participant_id_var` in the recipe picks it up.

THE CEILING. The User Guide says "the exact allocation at Wave 5 was replicated
at Wave 6", and `--ceiling` tests that sentence rather than reading past it: it
holds (27,696 of 27,705 allocated cells identical for the 1,849 people in both
waves), so a returning respondent rated the SAME three arrangements a year
later. Across those 3,621 pairs the answer is identical only **27.7%** of the
time. That is the ceiling on exact-match accuracy for this outcome — nothing can
predict a person's answer better than the person reproduces it — and it also
means the two waves are not independent rows.

    uv run python scripts/gen_ip_vig_housework.py --ceiling
    uv run python scripts/gen_ip_vig_housework.py --check
    uv run python scripts/gen_ip_vig_housework.py --write
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

# Wave letter -> (wave number, fieldwork year). The Innovation Panel runs one
# wave a year from 2008; waves 5 and 6 are the only ones carrying this study.
WAVES = {"e": (5, 2012), "f": (6, 2013)}

# The five randomised dimensions, as the archive names them, without the wave
# prefix or the scenario suffix. Order is the recipe template's order, which is
# the order `condition_num` counts them in.
DIMS = ("paid_work", "earnings", "children", "housework", "paid_housework")

# Four of the five are duplicated into indresp in wave 5 and can be checked
# against the household-level source. Paid help is in neither wave's indresp.
CHECKABLE = ("paid_work", "earnings", "children", "housework")

# Persona variables, mapped by hand from the UKHLS derived variables. There is no
# `tenure_dv`, no `hhsize` and no net income variable in either wave's indresp,
# so housing, household size and income are simply unavailable for this study —
# UK personas are thinner than US ones and this is one of the places it shows.
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
    """Stable, deterministic, and NOT the Understanding Society identifier.

    Same construction as `scripts/build_profiles.py`, so a row built from this
    file resolves to that person's profile. The same person gets the same hash
    in waves 5 and 6, which is the panel link.
    """
    return "ip_" + hashlib.sha256(f"ukds6849:{pidp}".encode()).hexdigest()[:12]


def derived_name(wave: int) -> str:
    return f"vig_housework_w{wave}-derived.sav"


def derive(w: str) -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    """One row per respondent: their three scenarios, their answers, their persona."""
    wave, year = WAVES[w]
    ind = spss.read(STATA / f"{w}_indresp_ip.dta")
    hh = spss.read(STATA / f"{w}_hhsamp_ip.dta")

    alloc = [f"{w}_ff_{d}{i}" for d in DIMS for i in (1, 2, 3)]
    missing_alloc = [c for c in alloc if c not in hh.df.columns]
    if missing_alloc:
        raise ValueError(f"wave {wave}: hhsamp is missing {missing_alloc}")

    ind_keep = ["pidp", f"{w}_hidp"] + [f"{w}_vig{i}" for i in (1, 2, 3)]
    ind_keep += [f"{w}_{v}" for v in PERSONA]
    missing_ind = [c for c in ind_keep if c not in ind.df.columns]
    if missing_ind:
        raise ValueError(f"wave {wave}: indresp is missing {missing_ind}")

    merged = ind.df[ind_keep].merge(
        hh.df[[f"{w}_hidp", *alloc]], on=f"{w}_hidp", how="left", validate="many_to_one"
    )
    unmatched = merged[alloc[0]].isna().sum()
    if unmatched:
        raise ValueError(
            f"wave {wave}: {unmatched} respondents have no household allocation row. "
            "Their scenarios cannot be rendered and would have to be guessed."
        )

    # Wave-prefix stripped, so one recipe shape serves both waves.
    out = pd.DataFrame({"person": [person_hash(int(p)) for p in merged["pidp"]]})
    for i in (1, 2, 3):
        out[f"vig{i}"] = merged[f"{w}_vig{i}"].to_numpy()
        for d in DIMS:
            out[f"ff_{d}{i}"] = merged[f"{w}_ff_{d}{i}"].to_numpy()
    for v in PERSONA:
        out[v] = merged[f"{w}_{v}"].to_numpy()
    # Fieldwork wave and year, so a row carries its own place in panel time.
    out["wave"] = wave
    out["year"] = year

    labels: dict[str, dict[float, str]] = {}
    for v in PERSONA:
        got = ind.value_labels.get(f"{w}_{v}")
        if got:
            labels[v] = dict(got)
    for i in (1, 2, 3):
        got = ind.value_labels.get(f"{w}_vig{i}")
        if got:
            labels[f"vig{i}"] = dict(got)
    return out, labels


def check(w: str) -> int:
    """Verify THIS SCRIPT'S JOIN against wave 5's duplicate person-level copy.

    The point is to check the join as performed, not the two files it reads. An
    earlier version of this compared `indresp` against `hhsamp` directly, which
    passes whatever `derive` does to them — a join that matched the wrong
    household would have sailed straight through it. So the comparison is
    between the DERIVED frame and the person-level copy, row for row, and
    `derive` keeps `indresp`'s row order so "row for row" is the right
    alignment.

    Returns the number of disagreements. Wave 6's `indresp` carries no copy, so
    there is nothing to compare and this says so rather than reporting a pass it
    did not earn — the printed comparison count is what shows whether a check
    actually happened.
    """
    wave = WAVES[w][0]
    ind = spss.read(STATA / f"{w}_indresp_ip.dta").df
    cols = [
        (f"ff_{d}{i}", f"{w}_ff_{d}{i}")
        for d in CHECKABLE
        for i in (1, 2, 3)
        if f"{w}_ff_{d}{i}" in ind.columns
    ]
    if not cols:
        print(f"  wave {wave}: indresp carries no copy of the allocation — nothing to check")
        return 0
    derived, _ = derive(w)
    if len(derived) != len(ind):
        raise ValueError(
            f"wave {wave}: derived {len(derived)} rows from {len(ind)} respondents — the "
            "row-for-row comparison below assumes they correspond"
        )
    bad = 0
    compared = 0
    for mine, theirs in cols:
        a = derived[mine].to_numpy()
        b = ind[theirs].to_numpy()
        valid = (a > 0) & (b > 0)
        compared += int(valid.sum())
        bad += int((a[valid] != b[valid]).sum())
    verdict = "AGREE" if bad == 0 else f"{bad} DISAGREEMENTS"
    print(
        f"  wave {wave}: {compared:,} comparisons of the joined allocation against "
        f"indresp's own copy — {verdict}"
    )
    return bad


def ceiling() -> dict[str, float]:
    """How well a person agrees with THEMSELVES, a year apart, on one scenario.

    The User Guide says "the exact allocation at Wave 5 was replicated at Wave
    6". Testing that sentence instead of reading past it is where this came
    from: it holds, so a returning respondent rated the SAME three arrangements
    in 2012 and 2013, and those pairs measure the ceiling on exact-match
    accuracy for this outcome. Nothing can predict a person's answer better than
    the person reproduces it.

    Only pairs whose five allocated codes are identical in both waves count, so
    the handful of cells that did change are excluded rather than compared
    across different scenarios.
    """
    frames = {}
    for w in WAVES:
        ind = spss.read(STATA / f"{w}_indresp_ip.dta").df
        hh = spss.read(STATA / f"{w}_hhsamp_ip.dta").df
        alloc = [f"{w}_ff_{d}{i}" for d in DIMS for i in (1, 2, 3)]
        keep = ["pidp", f"{w}_hidp"] + [f"{w}_vig{i}" for i in (1, 2, 3)]
        frames[w] = ind[keep].merge(hh[[f"{w}_hidp", *alloc]], on=f"{w}_hidp")
    both = frames["e"].merge(frames["f"], on="pidp")

    pairs = []
    cells_same = cells_diff = cells_sentinel = 0
    for i in (1, 2, 3):
        usable = (both[f"e_vig{i}"] > 0) & (both[f"f_vig{i}"] > 0)
        for d in DIMS:
            a, b = both[f"e_ff_{d}{i}"], both[f"f_ff_{d}{i}"]
            agree = a == b
            # A cell is only evidence about the replication where BOTH waves
            # allocated one. Ten households carry -8 "inapplicable", and counting
            # those as disagreements understates the match: 39 mismatches on the
            # raw comparison, 9 once the sentinels are set aside.
            allocated = (a > 0) & (b > 0)
            cells_sentinel += int((~allocated).sum())
            cells_same += int((agree & allocated).sum())
            cells_diff += int((~agree & allocated).sum())
            usable &= agree
        pairs.append(
            pd.DataFrame({"a": both[f"e_vig{i}"][usable], "b": both[f"f_vig{i}"][usable]})
        )
    r = pd.concat(pairs)
    gap = (r["a"] - r["b"]).abs()
    out = {
        "people_in_both_waves": float(len(both)),
        "cells_identical": float(cells_same),
        "cells_changed": float(cells_diff),
        "cells_unallocated": float(cells_sentinel),
        "pairs": float(len(r)),
        "identical_answer": float((r["a"] == r["b"]).mean()),
        "within_one_point": float((gap <= 1).mean()),
        "mean_absolute_change": float(gap.mean()),
        "correlation": float(r["a"].corr(r["b"])),
    }
    print(
        f"  {out['people_in_both_waves']:,.0f} people in both waves; "
        f"{out['cells_identical']:,.0f} of "
        f"{out['cells_identical'] + out['cells_changed']:,.0f} allocated cells identical "
        f"({out['cells_unallocated']:,.0f} carried a sentinel in one wave and are set aside)"
    )
    print(
        f"  CEILING on exact match {out['identical_answer']:.1%} over "
        f"{out['pairs']:,.0f} same-person same-scenario pairs a year apart — "
        f"within one point {out['within_one_point']:.1%}, mean absolute change "
        f"{out['mean_absolute_change']:.2f} of 7, r = {out['correlation']:.3f}"
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify the household join")
    ap.add_argument(
        "--ceiling",
        action="store_true",
        help="report how well people agree with themselves a year apart",
    )
    ap.add_argument("--write", action="store_true", help="write the derived .sav files")
    args = ap.parse_args()

    if args.ceiling:
        ceiling()

    if args.check:
        bad = sum(check(w) for w in WAVES)
        if bad:
            raise SystemExit(f"{bad} disagreements between the two allocation copies")

    for w in WAVES:
        wave = WAVES[w][0]
        df, labels = derive(w)
        answered = int(sum((df[f"vig{i}"] > 0).sum() for i in (1, 2, 3)))
        print(
            f"wave {wave}: {len(df):,} respondents, {answered:,} scenarios answered, "
            f"{df['person'].nunique():,} people"
        )
        if args.write:
            narrow = df.copy()
            # pandas' Arrow-backed string dtype is not a type pyreadstat.write_sav
            # round-trips reliably; plain object + np.nan is.
            for col in narrow.columns:
                if narrow[col].dtype == "object" or str(narrow[col].dtype).startswith("string"):
                    narrow[col] = narrow[col].astype(object).where(narrow[col].notna(), np.nan)
            path = OUT / derived_name(wave)
            pyreadstat.write_sav(narrow, str(path), variable_value_labels=labels)
            print(f"  wrote {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
