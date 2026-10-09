#!/usr/bin/env python3
"""Derive the data file for IP 9.42 — compound growth framed as money or as sea level.

Wave 16 (2023). The same arithmetic (1% a year over 5, 30 and 100 years) was
asked as a savings account ("financial") or as an island below sea level
("environmental"). `ff_numquesw16` gave a household one set or both;
`ff_numeracyw16` decided which came in the early self-completion section and
which in the late one. Built as two experiments, the environmental answers and
the financial answers, each conditioned on whether the OTHER set had been asked
earlier (rich's ruling for 9.24, applied to the same kind of design).

**The archive's labels for `ff_numeracyw16` are reversed.** They, and the User
Guide, say 1 = "Environmental questions early/financial questions late". The
questionnaire routes the EARLY environmental questions on `ff_numeracyw16 = 2`,
and the data agree with the questionnaire: the environmental-only and
financial-only households answer early under 2 and 1 respectively. This script
follows the routing, never the label, and `--check` shows the cross-tabulation.

**Exposure is what happened.** `prior_env` and `prior_fin`: 1 = the other set
had not been asked before, 2 = it had been asked earlier, -8 = allocated to
have it earlier but not routed into the early section; excluded.

**`pidp` is never written out.**

    uv run python scripts/gen_ip_numeracy.py --check
    uv run python scripts/gen_ip_numeracy.py --write
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
NOT_ROUTED = -8
HORIZONS = ("5y", "30y", "100y")
# The questionnaire's routing: the early section holds this set under this code.
EARLY_SET = {1: "fin", 2: "env"}
# ff_numquesw16: which sets the household was asked.
ASKED = {1: ("fin",), 2: ("env",), 3: ("fin", "env")}

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
    return f"numeracy_w{WAVE}-derived.sav"


def _joined() -> tuple[pd.DataFrame, dict]:
    ind = spss.read(STATA / f"{W}_indresp_ip.dta")
    hh = spss.read(STATA / f"{W}_hhsamp_ip.dta").df
    hh = hh[[f"{W}_hidp", f"{W}_ff_numeracyw16", f"{W}_ff_numquesw16"]].rename(
        columns={f"{W}_ff_numeracyw16": "order", f"{W}_ff_numquesw16": "sets"}
    )
    df = ind.df.merge(hh, on=f"{W}_hidp", how="left", validate="many_to_one")
    if df["order"].isna().any():
        raise ValueError("respondents with no household allocation row")
    return df, ind.value_labels


def _asked(df: pd.DataFrame, block: str, when: str) -> pd.Series:
    """Routed into that section: any item answered, refused or don't-know."""
    cols = [f"{W}_{block}num{when}{h}" for h in HORIZONS]
    return (df[cols] > 0).any(axis=1) | df[cols].isin([-1, -2]).any(axis=1)


def derive() -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    df, value_labels = _joined()
    order, sets = df["order"], df["sets"]
    out = pd.DataFrame({"person": [person_hash(int(p)) for p in df["pidp"]]})
    for block in ("env", "fin"):
        other = "fin" if block == "env" else "env"
        has_block = sets.map(lambda s, b=block: b in ASKED.get(int(s), ()) if s > 0 else False)
        has_both = sets == 3
        early = order.map(lambda o, b=block: EARLY_SET.get(int(o)) == b if o > 0 else False)
        for h in HORIZONS:
            value = np.where(
                early, df[f"{W}_{block}numear{h}"], df[f"{W}_{block}numlat{h}"]
            ).astype(float)
            out[f"{block}{h}"] = np.where(has_block, value, float(NOT_ROUTED))
        other_first = has_block & has_both & ~early
        saw_other = _asked(df, other, "ear")
        prior = np.where(has_block, 1.0, float(NOT_ROUTED))
        prior = np.where(other_first, np.where(saw_other, 2.0, float(NOT_ROUTED)), prior)
        out[f"prior_{block}"] = prior
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
    """Answers in a section the routing says was not asked. Must be 0.

    Households with no allocation (-9) that answered anyway are counted and
    reported, not failed: their arm cannot be established, so `derive` leaves
    them out.
    """
    df, _ = _joined()
    bad = unallocated = 0
    for block in ("env", "fin"):
        for when in ("ear", "lat"):
            answered = (df[[f"{W}_{block}num{when}{h}" for h in HORIZONS]] > 0).any(axis=1)
            for (o, s), count in df[answered].groupby(["order", "sets"]).size().items():
                if o <= 0 or s <= 0:
                    unallocated += int(count)
                    continue
                routed = block in ASKED[int(s)] and (when == "ear") == (EARLY_SET[int(o)] == block)
                bad += 0 if routed else int(count)
    derived, _ = derive()
    for p in ("prior_env", "prior_fin"):
        print(f"  {p}: {derived[p].value_counts().sort_index().to_dict()}")
    print(
        f"  {bad} answers in a section the routing says was not asked; "
        f"{unallocated} answered sections from households with no allocation (excluded)"
    )
    return bad


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify routing against answers")
    ap.add_argument("--write", action="store_true", help="write the derived .sav file")
    args = ap.parse_args()
    if args.check and check():
        raise SystemExit("answers in a section the routing says was not asked")
    df, labels = derive()
    for block in ("env", "fin"):
        usable = df[f"prior_{block}"] > 0
        n = int(sum((df.loc[usable, f"{block}{h}"] > 0).sum() for h in HORIZONS))
        print(f"{block}: {n:,} answers from respondents with a known exposure")
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
