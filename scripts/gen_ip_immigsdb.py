#!/usr/bin/env python3
"""Derive the data files for IP 9.16 — social desirability bias in attitudes to immigration.

Waves 8 (2015) and 9 (2016). A list (item-count) experiment: respondents saw a
list of statements about UK policy and said only HOW MANY they agreed with.
The control group's list held three statements; each of three treatment groups
saw the same three plus one sensitive statement, "The UK should allow people
from {Muslim / Eastern European / Caribbean} countries to come and live here".
The group was drawn per household (`ff_ictimw8` in `h_hhsamp_ip` at wave 8,
`ff_ictimw9` in `i_hhsamp_ip` at wave 9, where half of each wave 8 group was
moved to one of the other three). The order of statements in the list was
shuffled per respondent and recorded as a permutation code.

The recipes (`recipes/ukds_6849_immigsdb_w{8,9}.yaml`) hold the lists
word-for-word. This script does what a recipe cannot:

**The group, joined from the household file.** Each list has its own answer
variable (`ictimc1`, `ictimt1`, `ictimt2`, `ictimt3`). `--check` confirms that
every answer sits in the variable its household's group was routed to and none
in any other, that no answering respondent lacks a group, and that every answer
has a recorded order (ledger 134 and 138: the allocation is whatever the routing
did, so it is cross-tabulated rather than believed).

**Each respondent's statement order.** `ictim<list>o` holds the order as a
permutation of statement numbers — 3124 means statement 3 was shown first, the
reading ledger 135 records as an assumption for 9.17, whose order codes come
from the same module and the same specification wording. The questionnaire
numbers statements in the same order as its bullets. For each list this writes
`o_<list>_<k>`, the 1-based screen position of statement k, which is what
`ItemOverride.line_order_vars` reads.

**Ethnicity is kept** (`racel_dv`), as in every Innovation Panel build. rich
ruled on 10 Oct 2026 that a policy statement naming a country group does not
state what a persona group thinks, so docs/CONVENTIONS.md's rule on conditions
naming the respondent's own category does not apply.

**`pidp` is never written out.** `person` is the same hash as every other
Innovation Panel build. Nothing here prints a respondent-level value.

    uv run python scripts/gen_ip_immigsdb.py --check
    uv run python scripts/gen_ip_immigsdb.py --write
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

# wave letter -> (wave number, year, the household allocation variable fielded that wave)
WAVES = {"h": (8, 2015, "ff_ictimw8"), "i": (9, 2016, "ff_ictimw9")}
# group code -> (answer variable suffix, number of statements in its list)
LISTS = {1: ("c1", 3), 2: ("t1", 4), 3: ("t2", 4), 4: ("t3", 4)}

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
    return f"immigsdb_w{wave}-derived.sav"


def positions(code: float, n: int) -> list[float]:
    """Screen position of statements 1..n, from a permutation code like 3124."""
    if code is None or np.isnan(code) or code < 1:
        return [np.nan] * n
    shown = [int(ch) for ch in str(int(code))]
    if sorted(shown) != list(range(1, n + 1)):
        raise ValueError(f"an order code is not a permutation of 1..{n}")
    pos = [0.0] * n
    for slot, statement in enumerate(shown, 1):
        pos[statement - 1] = float(slot)
    return pos


def derive(w: str) -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    wave, year, alloc = WAVES[w]
    ind = spss.read(STATA / f"{w}_indresp_ip.dta")
    hh = spss.read(STATA / f"{w}_hhsamp_ip.dta")
    grp = hh.df[[f"{w}_hidp", f"{w}_{alloc}"]].rename(columns={f"{w}_{alloc}": "group"})
    df = ind.df.merge(grp, on=f"{w}_hidp", how="left", validate="many_to_one")
    if len(df) != len(ind.df):
        raise ValueError("the household join changed the number of respondents")

    out = pd.DataFrame({"person": [person_hash(int(p)) for p in df["pidp"]]})
    g = df["group"].fillna(-9).to_numpy()
    out["group"] = np.where(np.isin(g, list(LISTS)), g, -9.0).astype(float)
    for suffix, n in LISTS.values():
        out[suffix] = df[f"{w}_ictim{suffix}"].to_numpy()
        pos = np.array([positions(float(c), n) for c in df[f"{w}_ictim{suffix}o"]])
        for k in range(n):
            out[f"o_{suffix}_{k + 1}"] = pos[:, k]
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


def tabulate(d: pd.DataFrame) -> dict[int, dict[str, int]]:
    """Answers per (group, answer variable). Aggregates only."""
    tab: dict[int, dict[str, int]] = {}
    for code in sorted(set(d["group"].astype(int))):
        rows = d["group"] == code
        tab[code] = {s: int((d.loc[rows, s] >= 0).sum()) for s, _ in LISTS.values()}
    return tab


def check(w: str) -> int:
    """Inconsistencies between allocation, routing and order. Must be 0."""
    wave = WAVES[w][0]
    d, _ = derive(w)
    tab = tabulate(d)
    routed = sum(tab.get(code, {}).get(s, 0) for code, (s, _) in LISTS.items())
    elsewhere = sum(
        n for code, row in tab.items() for s, n in row.items() if LISTS.get(code, ("",))[0] != s
    )
    unallocated = sum(tab.get(-9, {}).values())
    unordered = 0
    out_of_range = 0
    for s, n in LISTS.values():
        answered = d[s] >= 0
        unordered += int((answered & d[f"o_{s}_1"].isna()).sum())
        out_of_range += int((answered & (d[s] > n)).sum())
    print(
        f"  wave {wave}: {routed:,} answers in the list the group was routed to, "
        f"{elsewhere} in another list, {unallocated} answering with no group, "
        f"{unordered} answered with no recorded order, {out_of_range} above the list length"
    )
    for code, (s, _) in LISTS.items():
        print(f"    group {code} ({s}): {tab.get(code, {}).get(s, 0):,} answered")
    return elsewhere + unallocated + unordered + out_of_range + (0 if routed else 1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify allocation against routing")
    ap.add_argument("--write", action="store_true", help="write the derived .sav files")
    args = ap.parse_args()
    if args.check and sum(check(w) for w in WAVES):
        raise SystemExit("allocation and routing disagree")
    for w, (wave, _, _) in WAVES.items():
        df, labels = derive(w)
        answered = int((df[[s for s, _ in LISTS.values()]] >= 0).sum().sum())
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
