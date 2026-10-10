#!/usr/bin/env python3
"""Derive the data file for IP 9.26 — residency rights for immigrants, the vignette.

Wave 11 (2018). Experiment 9.26 has two parts, both in the self-completion
module `Scaconjointimmigration_ip11`, asked only of respondents living in
England who completed it themselves (face-to-face with `scac` = 1, or web):

1. A paired-profile conjoint: three screens, each a table describing two
   applicants on eight randomised attributes (`cji<attr><pairing><a|b>`), a
   forced choice (`cjimmig1-3`) and a 1-10 rating of each applicant
   (`cji<pairing>app1/2`). **NOT BUILT** — see the recipe's notes: one screen
   is a cell of a 23,040 x 23,040 product, which `ConditionTemplate` expands in
   full, and its observed cells cannot be written into a tracked recipe
   because they are columns of the licensed deposit.
2. A vignette (`cjivig`, 1-10): one fixed applicant whose town of residence is
   randomised per person (`cjitown`, on `k_indresp_ip`): 1 = the respondent's
   own town, filled from their address, 2 = Glasgow. **Built** by
   `recipes/ukds_6849_immig_vignette_w11.yaml`.

This script does what a recipe cannot:

**The own-town fill depends on the address check, in another file.** The
questionnaire fills arm 1 with the town of `ff_post_code` when
`HHGRID.ADDRCHCK` = 1 (still resident at the address on record), and otherwise
with `HHGRID.TOWNADD` (a typed new town, asked on the web and telephone only)
or, failing that, `ff_post_code` again. `TOWNADD` is not in the deposit, so
for a household that moved the town shown is unknown: it may be the new town,
the old one, or (face-to-face, where `TOWNADD` is never asked) nothing.
`ADDRCHCK` is on `k_hhresp_ip`, joined on `k_hidp`. The derived `town_shown`
is the arm (1 own place, 2 Glasgow) only where the address was confirmed, and
missing otherwise. The own-place arm needs it because its text cannot be
written otherwise; the Glasgow arm is restricted the same way so both arms are
drawn from one population (the excluded group rates higher in both arms).

**The routing.** The module's universe is `HHGRID.REGION = 1` (England) and
(face-to-face with `scac` = 1, or web). `HHGRID.REGION` is not in the deposit;
`gor_dv` 1-9 stands in for it, and disagrees for a handful of people.
`--check` counts every disagreement and fails unless the counts are exactly
the ones declared below (`ROUTING_EXCEPTIONS`), so a new one stops the build
rather than passing quietly.

**`pidp` is never written out.** `person` is the same hash as every other
Innovation Panel build.

    uv run python scripts/gen_ip_immig.py --check
    uv run python scripts/gen_ip_immig.py --write
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

ALLOC = "cjitown"
ANSWER = "cjivig"
NOT_ASKED = (-8, -7)  # inapplicable (routed out), proxy

# The questionnaire's own option lists (module Experimentalvariables_ip11 and
# Scaconjointimmigration_ip11), which the deposit's value labels must match.
ALLOC_LABELS = {1: "Town of residence from ff_postcode", 2: "Glasgow"}
ANSWER_END_LABELS = {
    1: "Do not grant the applicant the right to remain",
    10: "Grant the applicant the right to remain",
}

# Routing disagreements with `gor_dv` standing in for HHGRID.REGION, counted on
# the deposit on 10 Oct 2026. Any other count fails `--check`.
#   asked_outside: routed to the module, but `gor_dv` is not England (1-9).
#   eligible_not_asked: `gor_dv` England and an eligible mode, but not routed.
ROUTING_EXCEPTIONS = {"asked_outside": 1, "eligible_not_asked": 3}

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
    return f"immig_w{WAVE}-derived.sav"


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
    hhr = spss.read(STATA / f"{W}_hhresp_ip.dta")
    keep = [
        "pidp",
        f"{W}_hidp",
        f"{W}_indmode",
        f"{W}_scac",
        f"{W}_{ALLOC}",
        f"{W}_{ANSWER}",
        *(f"{W}_{v}" for v in PERSONA),
    ]
    missing = [c for c in keep if c not in ind.df.columns]
    if missing:
        raise ValueError(f"indresp is missing {missing}")
    merged = _merge(
        ind.df[keep],
        hhr.df[[f"{W}_hidp", f"{W}_addrchck"]],
        f"{W}_hidp",
        "household address check",
    )
    labels = dict(ind.value_labels)
    return merged, labels


def town_shown(merged: pd.DataFrame) -> pd.Series:
    """The arm (1 own place, 2 Glasgow) where the address was confirmed; else NaN."""
    arm = merged[f"{W}_{ALLOC}"]
    confirmed = merged[f"{W}_addrchck"] == 1
    out = pd.Series(np.nan, index=merged.index)
    out[(arm == 1) & confirmed] = 1
    out[(arm == 2) & confirmed] = 2
    return out


def _routed(merged: pd.DataFrame) -> pd.Series:
    return ~merged[f"{W}_{ANSWER}"].isin(NOT_ASKED)


def _eligible(merged: pd.DataFrame) -> pd.Series:
    england = merged[f"{W}_gor_dv"].between(1, 9)
    mode = merged[f"{W}_indmode"]
    return england & (((mode == 1) & (merged[f"{W}_scac"] == 1)) | (mode == 3))


def derive() -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    """One row per respondent: their arm, the town actually shown, answer, persona."""
    merged, value_labels = _joined()
    out = pd.DataFrame({"person": [person_hash(int(p)) for p in merged["pidp"]]})
    out["cjitown"] = merged[f"{W}_{ALLOC}"].to_numpy()
    out["addrchck"] = merged[f"{W}_addrchck"].to_numpy()
    out["town_shown"] = town_shown(merged).to_numpy()
    out["cjivig"] = merged[f"{W}_{ANSWER}"].to_numpy()
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
    """Allocation, routing, labels and fill, counted. Must be zero. Prints counts only.

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

    # 1. Every routed respondent holds an allocation, and only codes 1 and 2.
    unallocated = int((routed & ~arm.isin([1, 2])).sum())
    print(f"  routed to the vignette: {int(routed.sum()):,}; without an allocation: {unallocated}")
    bad += unallocated
    for code in (1, 2):
        print(f"    arm {code}: {int((routed & (arm == code)).sum()):,} routed")

    # 2. Routing against the universe, exceptions declared.
    eligible = _eligible(merged)
    found = {
        "asked_outside": int((routed & ~eligible).sum()),
        "eligible_not_asked": int((~routed & eligible).sum()),
    }
    for k, n in found.items():
        want = ROUTING_EXCEPTIONS[k]
        print(f"  {k}: {n} (declared {want})")
        bad += abs(n - want)
    # No telephone or interviewer-assisted self-completion may be routed.
    assisted = int((routed & (merged[f"{W}_indmode"] == 1) & (merged[f"{W}_scac"] != 1)).sum())
    phone = int((routed & (merged[f"{W}_indmode"] == 2)).sum())
    print(f"  routed though assisted face-to-face: {assisted}; telephone: {phone}")
    bad += assisted + phone

    # 3. The deposit's labels against the questionnaire's option lists.
    got_alloc = {int(k): v for k, v in labels.get(f"{W}_{ALLOC}", {}).items() if k > 0}
    got_ends = {int(k): v for k, v in labels.get(f"{W}_{ANSWER}", {}).items() if k > 0}
    label_bad = int(got_alloc != ALLOC_LABELS) + int(got_ends != ANSWER_END_LABELS)
    print(f"  allocation and answer labels against the questionnaire: {label_bad} mismatch(es)")
    bad += label_bad

    # 4. The fill and the symmetric restriction: town_shown is the arm exactly
    # where the address was confirmed, in BOTH arms, and missing everywhere else.
    shown = town_shown(merged)
    confirmed = merged[f"{W}_addrchck"] == 1
    wrong_fill = int(
        (shown.notna() & ~confirmed).sum() + (confirmed & arm.isin([1, 2]) & (shown != arm)).sum()
    )
    excluded = {c: int((routed & (arm == c) & ~confirmed).sum()) for c in (1, 2)}
    no_hh = int((routed & merged[f"{W}_addrchck"].isna()).sum())
    print(
        f"  fill: {wrong_fill} inconsistent; routed but address not confirmed (not built): "
        f"own place {excluded[1]}, Glasgow {excluded[2]}; {no_hh} routed with no household record"
    )
    bad += wrong_fill
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
    ap.add_argument("--check", action="store_true", help="verify allocation, routing, fill")
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
