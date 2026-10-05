"""Check the built 35M5CV_sky rows against Table 2 of Hobolt, Leeper & Tilley (2021).

UK studies are not in SocSci210 (`comparable_to_socsci210: false`), so there is no
numeric answer key from `mmds crosscheck`. The published paper is the answer key
instead, same pattern as `scripts/verify_QQM5MC.py`: this reads the BUILT PARQUET,
not the deposit, because reproducing Table 2 from the raw `.sav` would only prove
the paper is reproducible, while reproducing it from the melted rows proves the
condition mapping (which arm = which identity), the outcome mapping (which item is
which), the response recode, and the exclusion of "Neither"/"None" respondents all
survived the melt intact. Any one of those four could be wrong while the deposit
and the paper still visibly agreed with each other.

TABLE 2 (p. 14), "Brexit identity scale (1-5 scale of 5-question battery)":

    Sky - Oct/Nov 2017      Conservative 2.9   Labour 3.0   Leaver 3.4   Remainer 3.4

The sps analysis script (`sky-analysis.sps`) computes this scale as the mean of the
battery's 5 items, `WEIGHT BY Weights` before the `MEANS TABLES` command that
produces it -- so the comparison here is WEIGHTED, joining the original `Weights`
column from `data/raw/35M5CV/sky-data.sav` back onto the built rows by
`participant_id` (`f"{study_id}:{idx}"`, where `idx` is the row's 0-based position
in `sky-data.sav`, preserved unchanged through `scripts/gen_35M5CV_sky.py`'s
derivation). An UNWEIGHTED recomputation is also printed for transparency: three of
the four unweighted cells still round to the published figure, but Labour does not
(3.06 rounds to 3.1), which is itself evidence the published figure is weighted and
not an argument for widening the tolerance to swallow it.

A SECOND, INDEPENDENT CHECK IS BUILT INTO THIS SCRIPT: Table 2 restricts to
respondents with a CLEAN primary identity (Remainer/Leaver/Conservative/Labour).
Recomputing the SAME weighted means over the WIDER population that also includes
"Neither"/"None" respondents who were routed into a battery via the `refid1`/`pid1`
follow-up (see the recipe's notes) breaks three of the four matches (Remainer 3.29,
Leaver 3.29, Conservative 2.83 vs the published 3.4/3.4/2.9). This script checks
BOTH populations and asserts the clean-identifier one is what matches -- which is
independent confirmation that excluding the lean-routed respondents from this
recipe is not merely cautious, it is what the authors themselves did.

THE TABLE 2 FOOTNOTE N -- VERIFIED AGAINST THE DATA, NOT COPIED FROM THE NOTE

Table 2's own note reads: "The Sky data have a total unweighted N of 1,692 for
party identity and 1,702 for Brexit identity." Read directly from `sky-data.sav`,
`pid` (party identity, Split 2) has 1,702 valid (non-missing) responses -- all of
Split 2, zero missing -- and `refid` (Brexit identity, Split 1) has 1,692 valid
responses (1,779 minus 87 who did not answer `refid` at all). That is the OPPOSITE
pairing from what the footnote prints. This script asserts the Ns it finds against
the DATA (1,702 party / 1,692 Brexit), not against the footnote's wording, and
reports the divergence explicitly rather than bending the assertion to match a
probable transcription error in the two labels.

Run:  uv run python scripts/verify_35M5CV_sky.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pyreadstat

REPO = Path(__file__).resolve().parents[1]
PARQUET = REPO / "data" / "processed" / "35M5CV_sky.parquet"
RAW_SAV = REPO / "data" / "raw" / "35M5CV" / "sky-data.sav"

# condition_num -> (label, published Table 2 Brexit-identity-scale value, 1dp)
TABLE_2 = {
    0: ("Remainer", 3.4),
    1: ("Leaver", 3.4),
    2: ("Conservative", 2.9),
    3: ("Labour", 3.0),
}


def load_built() -> pd.DataFrame:
    if not PARQUET.exists():
        raise SystemExit(
            f"{PARQUET} not found — run `uv run mmds build recipes/35M5CV_sky.yaml` first"
        )
    df = pd.read_parquet(PARQUET)
    # idx is this row's 0-based position in sky-data.sav, preserved unchanged
    # through the derived file (scripts/gen_35M5CV_sky.py never reorders or
    # filters rows, only columns).
    df["idx"] = df["participant_id"].map(lambda s: int(s.split(":")[1]))
    return df


def participant_scale(df: pd.DataFrame) -> pd.DataFrame:
    """One row per participant: condition_num, idx, and their 5-item battery mean."""
    g = df.groupby("idx").agg(
        condition_num=("condition_num", "first"), scale=("response_num", "mean")
    )
    return g.reset_index()


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    return float((values * weights).sum() / weights.sum())


def check_table2(df: pd.DataFrame, weights: pd.Series) -> list[str]:
    """Clean-identifier population (the recipe's own rows) vs Table 2, weighted."""
    bad: list[str] = []
    per_participant = participant_scale(df)
    per_participant["weight"] = per_participant["idx"].map(weights)

    print("\nTable 2 (p.14) 'Brexit identity scale' — built rows, clean identifiers only:")
    for cond, (label, published) in TABLE_2.items():
        cell = per_participant[per_participant["condition_num"] == cond]
        n = len(cell)
        unweighted = cell["scale"].mean()
        weighted = weighted_mean(cell["scale"], cell["weight"])
        match = "OK" if round(weighted, 1) == published else "MISMATCH"
        print(
            f"  {label:<13} n={n:4d}  unweighted={unweighted:.3f}  "
            f"weighted={weighted:.3f} (rounds {round(weighted, 1)})  "
            f"published={published}  [{match}]"
        )
        if round(weighted, 1) != published:
            bad.append(
                f"{label}: weighted mean {weighted:.3f} rounds to {round(weighted, 1)}, "
                f"Table 2 prints {published}"
            )
    return bad


def check_wider_population_breaks(weights: pd.Series) -> None:
    """The deliberately-excluded lean-routed population, weighted the same way —
    shown to NOT match Table 2, as independent confirmation of the exclusion."""
    df, _meta = pyreadstat.read_sav(str(RAW_SAV))

    def battery_mean(cols: list[str]) -> pd.Series:
        return df[cols].mean(axis=1)

    df["EArefRscale_mine"] = battery_mean(["EArefR1", "EArefR2", "EArefR3", "EArefR4", "EArefR5"])
    df["EArefLscale_mine"] = battery_mean(["EArefL1", "EArefL2", "EArefL3", "EArefL4", "EArefL5"])
    df["EApidCscale_mine"] = battery_mean(["EApidC1", "EApidC2", "EApidC3", "EApidC4", "EApidC5"])
    df["EApidLascale_mine"] = battery_mean(
        ["EApidLa1", "EApidLa2", "EApidLa3", "EApidLa4", "EApidLa5"]
    )

    print("\nSame weighted computation over the WIDER population (clean identifiers PLUS")
    print("'Neither'/'None' respondents routed via the refid1/pid1 lean follow-up) —")
    print("expected to NOT match Table 2, confirming the recipe's exclusion is correct:")
    wider = {
        "Remainer-routed (EArefR)": ("EArefRscale_mine", 3.4),
        "Leaver-routed (EArefL)": ("EArefLscale_mine", 3.4),
        "Conservative-routed (EApidC)": ("EApidCscale_mine", 2.9),
        "Labour-routed (EApidLa)": ("EApidLascale_mine", 3.0),
    }
    for label, (col, published) in wider.items():
        has = df[col].notna()
        sub = df.loc[has, [col]].copy()
        sub["weight"] = sub.index.map(weights)
        w = weighted_mean(sub[col], sub["weight"])
        flag = "matches anyway" if round(w, 1) == published else "breaks, as expected"
        print(
            f"  {label:<30} n={int(has.sum()):4d}  weighted={w:.3f} (rounds {round(w, 1)})  [{flag}]"
        )


def check_footnote_n() -> list[str]:
    """The data's own Ns against Table 2's printed footnote, which this script
    asserts are swapped relative to the data."""
    df, _meta = pyreadstat.read_sav(str(RAW_SAV))
    split1 = df[df["Split"] == "Split 1"]
    split2 = df[df["Split"] == "Split 2"]
    brexit_n = int(split1["refid"].notna().sum())
    party_n = int(split2["pid"].notna().sum())

    print("\nTable 2 / Table 3 footnote check:")
    print(
        '  Footnote prints: "unweighted N of 1,692 for party identity and 1,702 for Brexit identity"'
    )
    print(f"  Data shows:      party identity (pid) valid N = {party_n}")
    print(f"                   Brexit identity (refid) valid N = {brexit_n}")
    if party_n == 1702 and brexit_n == 1692:
        print("  CONCLUSION: the footnote's two labels are swapped relative to the data.")
        print(
            "  This script asserts the DATA's pairing (1,702 party / 1,692 Brexit), not the footnote's."
        )
        return []
    return [
        f"footnote-N check failed: expected party=1702/brexit=1692 from the data, "
        f"got party={party_n}/brexit={brexit_n}"
    ]


def main() -> int:
    df = load_built()
    weights_df, _meta = pyreadstat.read_sav(str(RAW_SAV))
    weights = weights_df["Weights"]

    print("35M5CV_sky — built rows against Hobolt, Leeper & Tilley (2021) Table 2")
    print(f"\nbuilt: {len(df)} rows, {df['idx'].nunique()} participants")

    failures = check_table2(df, weights)
    check_wider_population_breaks(weights)
    failures += check_footnote_n()

    if failures:
        print("\nFAILED:")
        for line in failures:
            print(f"  {line}")
        return 1
    print(
        "\nVERIFIED — all 4 Table 2 cells match at 1dp (weighted), and the footnote-N divergence is confirmed."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
