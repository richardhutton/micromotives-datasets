#!/usr/bin/env python3
"""Derive the data files for IP 9.17 — sexual identity measured by item counts.

Waves 8 (2015) and 9 (2016). Respondents saw six lists of statements and said
only HOW MANY were true for them. Three lists in each wave carried an extra,
sensitive statement ("is the same sex as me"; "gay, lesbian or bisexual"); which
three depended on the household's group (`ff_ictsexw8`) and flipped between the
waves, so each respondent saw every list both with and without it across the two
waves. The order of statements within each list was shuffled per respondent and
recorded as a permutation code.

The recipes (`recipes/ukds_6849_itemcount_w{8,9}.yaml`) hold the lists
word-for-word. This script does what a recipe cannot:

**Which lists were sensitive, as one code.** `sensitive` is 1 when lists B, D
and F carried the sensitive statement and 2 when A, C and E did. Wave 8 group 1
and wave 9 group 2 are code 1; the rest code 2. `--check` confirms that every
answer sits in a variable its code says was asked, and none in the other.

**Each respondent's statement order.** `ictsex<list>o` holds the order as a
permutation of statement numbers — 3124 means statement 3 was shown first. The
questionnaire numbers statements in the same order as its bullets (checked for
all twelve lists). For each list this writes `o_<list>_<k>`, the 1-based screen
position of statement k, which is what `ItemOverride.line_order_vars` reads.

**`pidp` is never written out.** `person` is the same hash as every other
Innovation Panel build.

    uv run python scripts/gen_ip_itemcount.py --check
    uv run python scripts/gen_ip_itemcount.py --write
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

WAVES = {"h": (8, 2015), "i": (9, 2016)}
LETTERS = ("a", "b", "c", "d", "e", "f")
# Lists carrying the sensitive statement, per `sensitive` code.
SENSITIVE = {1: ("b", "d", "f"), 2: ("a", "c", "e")}
# Which `ff_ictsexw8` group got code 1 in each wave: the assignment flips.
CODE1_GROUP = {"h": 1, "i": 2}

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


def derived_name(wave: int) -> str:
    return f"itemcount_w{wave}-derived.sav"


def list_names() -> list[str]:
    """All twelve list variables: `a`, `as`, `b`, `bs`, ..."""
    return [f"{x}{s}" for x in LETTERS for s in ("", "s")]


def positions(code: float, n: int) -> list[float]:
    """Screen position of statements 1..n, from a permutation code like 3124."""
    if not code or code < 1 or np.isnan(code):
        return [np.nan] * n
    shown = [int(ch) for ch in str(int(code))]
    if sorted(shown) != list(range(1, n + 1)):
        raise ValueError(f"order code {int(code)} is not a permutation of 1..{n}")
    pos = [0.0] * n
    for slot, statement in enumerate(shown, 1):
        pos[statement - 1] = float(slot)
    return pos


def derive(w: str) -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    wave, year = WAVES[w]
    ind = spss.read(STATA / f"{w}_indresp_ip.dta")
    hh = spss.read(STATA / f"{w}_hhsamp_ip.dta")
    grp = hh.df[[f"{w}_hidp", f"{w}_ff_ictsexw8"]].rename(columns={f"{w}_ff_ictsexw8": "grp"})
    df = ind.df.merge(grp, on=f"{w}_hidp", how="left", validate="many_to_one")

    out = pd.DataFrame({"person": [person_hash(int(p)) for p in df["pidp"]]})
    g = df["grp"].fillna(-9)
    out["sensitive"] = np.where(
        g == CODE1_GROUP[w], 1.0, np.where(g == 3 - CODE1_GROUP[w], 2.0, -9.0)
    )
    for name in list_names():
        out[name] = df[f"{w}_ictsex{name}"].to_numpy()
        n = 5 if name.endswith("s") else 4
        pos = np.array([positions(c, n) for c in df[f"{w}_ictsex{name}o"]])
        for k in range(n):
            out[f"o_{name}_{k + 1}"] = pos[:, k]
    for v in PERSONA:
        out[v] = df[f"{w}_{v}"].to_numpy()
    out["wave"] = wave
    out["year"] = year
    labels: dict[str, dict[float, str]] = {}
    for v in PERSONA:
        got = ind.value_labels.get(f"{w}_{v}")
        if got:
            labels[v] = dict(got)
    return out, labels


def check(w: str) -> int:
    """Answers in a list the respondent's code says they were not shown. Must be 0."""
    wave = WAVES[w][0]
    d, _ = derive(w)
    bad = answered = 0
    for code, sens in SENSITIVE.items():
        rows = d["sensitive"] == code
        for x in LETTERS:
            shown, hidden = (f"{x}s", x) if x in sens else (x, f"{x}s")
            answered += int((d.loc[rows, shown] >= 0).sum())
            bad += int((d.loc[rows, hidden] >= 0).sum())
    unallocated = int(((d["sensitive"] < 0) & (d[list_names()] >= 0).any(axis=1)).sum())
    print(
        f"  wave {wave}: {answered:,} answers in lists the code says were shown, {bad} in "
        f"lists it says were not, {unallocated} answering respondents with no group"
    )
    return bad + unallocated


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify list assignment")
    ap.add_argument("--write", action="store_true", help="write the derived .sav files")
    args = ap.parse_args()
    if args.check and sum(check(w) for w in WAVES):
        raise SystemExit("answers in lists the respondent was not shown")
    for w, (wave, _) in WAVES.items():
        df, labels = derive(w)
        answered = int((df[list_names()] >= 0).sum().sum())
        print(f"wave {wave}: {len(df):,} respondents, {answered:,} list answers")
        if args.write:
            narrow = df.copy()
            for col in narrow.columns:
                if narrow[col].dtype == "object" or str(narrow[col].dtype).startswith("string"):
                    narrow[col] = narrow[col].astype(object).where(narrow[col].notna(), np.nan)
            path = OUT / derived_name(wave)
            pyreadstat.write_sav(narrow, str(path), variable_value_labels=labels)
            print(f"  wrote {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
