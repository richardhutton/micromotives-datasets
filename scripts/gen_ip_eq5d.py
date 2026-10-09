#!/usr/bin/env python3
"""Derive the data file for IP 9.24 — the EQ-5D asked in its 3-level and 5-level forms.

Wave 11 (2018). The EQ-5D's five health items (mobility, self-care, usual
activities, pain, anxiety/depression) were asked in the original 3-level form
(3L) and the newer 5-level form (5L), in an early or a late self-completion
module. `eq5dcond`, allocated per respondent:

    1  5L early, 3L late
    2  3L early, 5L late
    3  5L late only

Built as two experiments, the 5L answers and the 3L answers, each conditioned on
whether the OTHER form had been asked earlier in the interview (rich's ruling, 9
Oct 2026: build on prior exposure). This script does three things a recipe
cannot:

**One variable per item per form.** A form's answers sit in `...ear` or `...lat`
depending on the arm; `eq5l_<item>` and `eq3l_<item>` take whichever the arm
used, so arms that differ only in position can share one condition.

**Exposure is what happened, not what was allocated.** A respondent allocated to
see the other form early who skipped the early self-completion section (coded
-8 there) was never shown it, so "earlier you were asked ..." would be false for
them. `prior5` and `prior3` code what the respondent actually saw before the
form being answered:

    1  neither form had been asked before
    2  the other form had been asked earlier
   -8  allocated to see the other form first, but did not: excluded

`--check` reports how many respondents each code holds.

**`pidp` is never written out.** `person` is the same hash as every other
Innovation Panel build.

    uv run python scripts/gen_ip_eq5d.py --check
    uv run python scripts/gen_ip_eq5d.py --write
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
W, WAVE, YEAR = "k", 11, 2018

DIMS = ("mob", "care", "act", "pain", "anx")
# Which module each arm drew each form from. Arm 3 has no 3L.
SOURCE = {"5l": {1: "ear", 2: "lat", 3: "lat"}, "3l": {1: "lat", 2: "ear"}}
# The arm that saw the OTHER form early, before this one.
AFTER_OTHER = {"5l": 2, "3l": 1}
NOT_ROUTED = -8

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
    return f"eq5d_w{WAVE}-derived.sav"


def _was_asked(df: pd.DataFrame, form: str, when: str) -> pd.Series:
    """True where the respondent was routed into that module at all."""
    cols = [f"{W}_eq{form}{d}{when}" for d in DIMS]
    return (df[cols] != NOT_ROUTED).any(axis=1)


def derive() -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    r = spss.read(STATA / f"{W}_indresp_ip.dta")
    df = r.df
    needed = ["pidp", f"{W}_eq5dcond"]
    needed += [f"{W}_eq{f}{d}{w}" for f in ("3l", "5l") for d in DIMS for w in ("ear", "lat")]
    needed += [f"{W}_{v}" for v in PERSONA]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"indresp is missing {missing}")

    cond = df[f"{W}_eq5dcond"]
    out = pd.DataFrame({"person": [person_hash(int(p)) for p in df["pidp"]]})
    out["eq5dcond"] = cond.to_numpy()
    for form, by_arm in SOURCE.items():
        other = "3l" if form == "5l" else "5l"
        for d in DIMS:
            value = pd.Series(float(NOT_ROUTED), index=df.index)
            for arm, when in by_arm.items():
                value = value.where(cond != arm, df[f"{W}_eq{form}{d}{when}"])
            out[f"eq{form}_{d}"] = value.to_numpy()
        after = AFTER_OTHER[form]
        prior = np.where(cond.isin(list(by_arm)), 1.0, float(NOT_ROUTED))
        saw_other = _was_asked(df, other, "ear")
        prior = np.where(cond == after, np.where(saw_other, 2.0, float(NOT_ROUTED)), prior)
        out[f"prior{form[0]}"] = prior
    for v in PERSONA:
        out[v] = df[f"{W}_{v}"].to_numpy()
    out["wave"] = WAVE
    out["year"] = YEAR

    labels: dict[str, dict[float, str]] = {}
    for v in PERSONA:
        got = r.value_labels.get(f"{W}_{v}")
        if got:
            labels[v] = dict(got)
    for p in ("prior5", "prior3"):
        labels[p] = {1.0: "neither form asked before", 2.0: "other form asked earlier"}
    return out, labels


def check() -> dict[str, dict[int, int]]:
    """How many respondents each exposure code holds, per form, and per arm."""
    derived, _ = derive()
    report: dict[str, dict[int, int]] = {}
    for p in ("prior5", "prior3"):
        counts = derived.groupby([p, "eq5dcond"]).size()
        report[p] = {int(k[0]) * 10 + int(k[1]): int(n) for k, n in counts.items() if k[1] > 0}
        print(
            f"  {p}: "
            + ", ".join(f"code {k // 10} arm {k % 10}: {n}" for k, n in report[p].items())
        )
    # The merged answers must never come from a module the arm did not use.
    for form, by_arm in SOURCE.items():
        stray = 0
        for arm in (1, 2, 3):
            if arm not in by_arm:
                stray += int((derived.loc[derived["eq5dcond"] == arm, f"eq{form}_mob"] > 0).sum())
        print(f"  {form}: {stray} answers attributed to an arm that never asked it")
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report exposure codes")
    ap.add_argument("--write", action="store_true", help="write the derived .sav file")
    args = ap.parse_args()
    if args.check:
        check()
    df, labels = derive()
    for form in ("5l", "3l"):
        usable = df[f"prior{form[0]}"] > 0
        answered = int(sum((df.loc[usable, f"eq{form}_{d}"] > 0).sum() for d in DIMS))
        print(f"{form}: {answered:,} answers from respondents with a known exposure")
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
