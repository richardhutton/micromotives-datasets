#!/usr/bin/env python3
"""Derive the data file for IP 9.30 — vignettes: intentions to prepare for automation.

Wave 14 (2021). The self-completion module `Scaworktech_ip14` opens with five
items asked before any vignette (`datawork`, `algorithmwork`, `robotwork`,
`losejob`, `losejoblong`), then three grid screens of nine agree/disagree
statements (`techreplace` .. `techchange`). The first statement's text opens
with a vignette whose wording is filled from the HOUSEHOLD allocation
`n_ff_techworkw14` on `n_hhsamp_ip` (User Guide 9.30: 1/5 of households to each
group): 1 = major severity, long-term; 2 = major, short-term; 3 = minor,
long-term; 4 = minor, short-term; 5 = control. Built by
`recipes/ukds_6849_automation_w14.yaml`, nine outcomes per respondent.

This script does what a recipe cannot:

**The allocation lives in another file.** `n_ff_techworkw14` is joined from
`n_hhsamp_ip` on `n_hidp`. The person file holds no copy of it, so there is no
second, person-level variable to disagree with (ledger 134).

**The routing.** The module's universe is ((face-to-face with `scac` 1-3) or
telephone or web) AND (`jbhas` = 1 or `jboff` = 1). Every variable in the
universe is in the deposit, so `--check` requires routing to equal the universe
EXACTLY, and every one of the fourteen module items to be routed identically.
All five arms answer the same variables, so the allocation cannot be read off
the routing (ledger 138); what `--check` can and does assert is that every
routed respondent holds exactly one of the five codes, and that the deposit's
labels for the allocation and the answers are the User Guide's and the
questionnaire's.

**`pidp` is never written out.** `person` is the same hash as every other
Innovation Panel build. No message printed here carries a respondent value.

    uv run python scripts/gen_ip_automation.py --check
    uv run python scripts/gen_ip_automation.py --write
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

ALLOC = "ff_techworkw14"
NOT_ASKED = (-8, -7)  # inapplicable (routed out), proxy

# The nine statements after the vignette, in questionnaire order.
OUTCOMES = (
    "techreplace",
    "techdoes",
    "techopp",
    "techimport",
    "techoutdate",
    "techskills",
    "techtrain",
    "techtime",
    "techchange",
)
# Asked in the same module but BEFORE the vignette: routed with it, not built.
PRE_VIGNETTE = ("datawork", "algorithmwork", "robotwork", "losejob", "losejoblong")

# User Guide 9.30 and the wave 14 technical report, section 3.2. The deposit's
# labels carry a leading space and lower case; compared stripped and casefolded.
ALLOC_LABELS = {
    1: "major severity; long-term",
    2: "major severity; short-term",
    3: "minor severity; long-term",
    4: "minor severity; short-term",
    5: "control group",
}
# Each statement's options in `Scaworktech_ip14` (all nine identical).
ANSWER_LABELS = {
    1: "Totally disagree",
    2: "Somewhat disagree",
    3: "Neither disagree nor agree",
    4: "Somewhat agree",
    5: "Totally agree",
}

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
    return f"automation_w{WAVE}-derived.sav"


class IdentifierSafeError(RuntimeError):
    """An error whose message carries no respondent identifier or value."""


def _merge(left: pd.DataFrame, right: pd.DataFrame, key: str, what: str) -> pd.DataFrame:
    """A many-to-one left join that can never print a key.

    pandas' own `MergeError` lists the duplicated keys, which here are household
    ids: licensed identifiers. The duplicate is counted instead, and the
    original exception is suppressed rather than chained.
    """
    dupes = int(right[key].duplicated().sum())
    if dupes:
        raise IdentifierSafeError(f"{what}: {dupes} duplicated join key(s) on the right")
    try:
        return left.merge(right, on=key, how="left", validate="many_to_one")
    except Exception:
        raise IdentifierSafeError(f"{what}: merge failed (keys withheld)") from None


def _joined() -> tuple[pd.DataFrame, dict]:
    ind = spss.read(STATA / f"{W}_indresp_ip.dta")
    hhs = spss.read(STATA / f"{W}_hhsamp_ip.dta")
    keep = [
        "pidp",
        f"{W}_hidp",
        f"{W}_indmode",
        f"{W}_scac",
        f"{W}_jbhas",
        f"{W}_jboff",
        *(f"{W}_{v}" for v in PRE_VIGNETTE + OUTCOMES),
        *(f"{W}_{v}" for v in PERSONA),
    ]
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
    labels = dict(ind.value_labels)
    labels[f"{W}_{ALLOC}"] = dict(hhs.value_labels.get(f"{W}_{ALLOC}") or {})
    return merged, labels


def _routed(merged: pd.DataFrame) -> pd.Series:
    return ~merged[f"{W}_{OUTCOMES[0]}"].isin(NOT_ASKED)


def _eligible(merged: pd.DataFrame) -> pd.Series:
    mode = merged[f"{W}_indmode"]
    face_sc = (mode == 1) & merged[f"{W}_scac"].between(1, 3)
    in_work = (merged[f"{W}_jbhas"] == 1) | (merged[f"{W}_jboff"] == 1)
    return (face_sc | mode.isin([2, 3])) & in_work


def derive() -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    """One row per respondent: their household's arm, nine answers, persona."""
    merged, value_labels = _joined()
    out = pd.DataFrame({"person": [person_hash(int(p)) for p in merged["pidp"]]})
    out["techworkw14"] = merged[f"{W}_{ALLOC}"].to_numpy()
    for v in OUTCOMES:
        out[v] = merged[f"{W}_{v}"].to_numpy()
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


def check(merged: pd.DataFrame | None = None, labels: dict | None = None) -> int:
    """Allocation, routing and labels, counted. Must be zero. Prints counts only.

    `merged` and `labels` default to the deposit; a test passes a deliberately
    broken copy to show each count can fail.
    """
    if merged is None or labels is None:
        dep_merged, dep_labels = _joined()
        merged = dep_merged if merged is None else merged
        labels = dep_labels if labels is None else labels
    bad = 0
    arm = merged[f"{W}_{ALLOC}"]
    routed = _routed(merged)

    # 1. Every routed respondent holds exactly one of the five codes.
    unallocated = int((routed & ~arm.isin([1, 2, 3, 4, 5])).sum())
    print(f"  routed to the module: {int(routed.sum()):,}; without an allocation: {unallocated}")
    bad += unallocated
    for code in (1, 2, 3, 4, 5):
        print(f"    arm {code}: {int((routed & (arm == code)).sum()):,} routed")

    # 2. Routing equals the universe exactly; every item routed alike.
    eligible = _eligible(merged)
    asked_outside = int((routed & ~eligible).sum())
    eligible_not_asked = int((~routed & eligible).sum())
    print(
        f"  routed outside the universe: {asked_outside}; in it, not routed: {eligible_not_asked}"
    )
    bad += asked_outside + eligible_not_asked
    uneven = 0
    for v in PRE_VIGNETTE + OUTCOMES[1:]:
        uneven += int(((~merged[f"{W}_{v}"].isin(NOT_ASKED)) != routed).sum())
    print(f"  module items routed differently from {OUTCOMES[0]}: {uneven}")
    bad += uneven

    # 3. The deposit's labels against the User Guide and the questionnaire.
    got_alloc = {
        int(k): str(v).strip().casefold()
        for k, v in labels.get(f"{W}_{ALLOC}", {}).items()
        if k > 0
    }
    label_bad = int(got_alloc != ALLOC_LABELS)
    for v in OUTCOMES:
        got = {int(k): str(t) for k, t in labels.get(f"{W}_{v}", {}).items() if k > 0}
        label_bad += int(got != ANSWER_LABELS)
    print(f"  allocation and answer labels against the documents: {label_bad} mismatch(es)")
    bad += label_bad

    # 4. Answers in range wherever routed (negative codes are dropped by the recipe).
    out_of_range = 0
    for v in OUTCOMES:
        col = merged[f"{W}_{v}"]
        out_of_range += int((routed & (col > 5)).sum() + (routed & (col == 0)).sum())
    print(f"  answers outside 1-5 or the missing codes: {out_of_range}")
    bad += out_of_range
    print(f"  {'AGREE' if bad == 0 else 'ROUTING DEFECT'}")
    return bad


def main() -> None:
    try:
        _main()
    except SystemExit:
        raise
    except IdentifierSafeError as exc:
        raise SystemExit(f"error: {exc}") from None
    except Exception as exc:
        # Any other message could quote a value from the deposit, so only the
        # exception's type leaves this process.
        raise SystemExit(f"error: {type(exc).__name__} (message withheld)") from None


def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify allocation, routing, labels")
    ap.add_argument("--write", action="store_true", help="write the derived .sav file")
    args = ap.parse_args()

    if args.check and check():
        raise SystemExit("routing check failed")

    df, labels = derive()
    print(f"wave {WAVE}: {len(df):,} respondents")
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
