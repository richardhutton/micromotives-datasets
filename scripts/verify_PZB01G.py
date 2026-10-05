"""Check the built PZB01G rows against numbers Goodwin, Hix & Pickup (2020) published.

UK studies are not in SocSci210, so `pipeline/crosscheck.py` has nothing to compare
PZB01G to and the recipe sets `comparable_to_socsci210: false`. The published paper
and its official supplementary appendix are the answer key instead, and this script
is what `mmds crosscheck` is for the TESS studies.

It reads the built PARQUET, not the deposit. Reproducing the paper from
`Vignette data.dta` would prove only that the paper is reproducible; reproducing it
from the melted rows proves that the `split` assignment mapping, the `wave2q2`
outcome recode (including the decision to KEEP code 99 "Don't know" as a
substantive response rather than drop it — see the recipe's notes) and the row
count all survived the melt. All three are things a recipe can get wrong silently.

Two numbers, both the authors' own:

1. Appendix Table A6 ("III. Wave 2 Treatment Group Sizes") — nine group sizes,
   https://static.cambridge.org/content/id/urn:cambridge.org:id:article:S0007123417000667/resource/name/S0007123417000667sup001.pdf,
   page 4, transcribed below. Checked EXACTLY, not to a tolerance: the recipe's
   notes establish that no row is dropped at build time (every one of the 5,333
   vignette-wave respondents holds a non-missing `wave2q2` code), so the built
   `condition_num` counts should equal Table A6's nine numbers precisely.

2. The paper's own text (p.8): "In the second wave, among those in the control
   group (who were not exposed to any arguments), these results changed slightly
   to 37.1 per cent, 44.0 per cent and 18.8 per cent, respectively" — i.e. the
   Wave 2 Remain/Leave/(Don't know or would not vote) shares for the CONTROL
   condition only. The recipe keeps "Would not vote" (code 3) and "Don't know"
   (code 99, recoded to 4) as two separate response values rather than folding
   them together the way the authors' own `dk` dummy does (see notes: "merged
   categories stay merged" — nothing here invents a merge the source's own
   declared codes do not make); this script performs that same fold ONLY for
   the purpose of this comparison, on the built rows.

Run:  uv run python scripts/verify_PZB01G.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
PARQUET = REPO / "data" / "processed" / "PZB01G.parquet"

# condition_num = split - 1 (see recipe notes). Names match Table A6's own.
CONDITIONS = {
    0: "Control",
    1: "Pro Cultural, Pro Economic, Pro Political",
    2: "Anti Cultural, Pro Economic, Pro Political",
    3: "Pro Cultural, Anti Economic, Pro Political",
    4: "Anti Cultural, Anti Economic, Pro Political",
    5: "Pro Cultural, Pro Economic, Anti Political",
    6: "Anti Cultural, Pro Economic, Anti Political",
    7: "Pro Cultural, Anti Economic, Anti Political",
    8: "Anti Cultural, Anti Economic, Anti Political",
}

# Appendix Table A6, transcribed in full. Control's 563 is not a Table A6 row
# (the table lists only the eight treatment groups) but is given directly by
# the paper's own text (p.7, footnote 37: "Group sizes range from 551 to 652")
# and by the deposit's own `control` dummy (563 of 5,333) — included here so
# every one of the nine condition_num groups is checked.
TABLE_A6: dict[int, int] = {
    0: 563,
    1: 636,
    2: 551,
    3: 617,
    4: 553,
    5: 587,
    6: 610,
    7: 652,
    8: 564,
}

# p.8, the control group's own Wave 2 vote-intention shares. Percentages as
# printed, one decimal place.
CONTROL_PCT = {"remain": 37.1, "leave": 44.0, "dk_or_no_vote": 18.8}
PCT_TOLERANCE = 0.05  # the built counts should hit these exactly, not approximately


def load() -> pd.DataFrame:
    if not PARQUET.exists():
        raise SystemExit(f"{PARQUET} not found — run `uv run mmds build recipes/PZB01G.yaml` first")
    return pd.read_parquet(PARQUET)


def check_table_a6(df: pd.DataFrame) -> list[str]:
    bad: list[str] = []
    got_total = len(df)
    want_total = sum(TABLE_A6.values())
    if got_total != want_total:
        bad.append(f"total N: built {got_total}, Table A6 (+control) sums to {want_total}")
    for cond, want_n in TABLE_A6.items():
        got_n = int((df["condition_num"] == cond).sum())
        if got_n != want_n:
            bad.append(
                f"condition_num={cond} ({CONDITIONS[cond]}): built N={got_n}, "
                f"Table A6 says {want_n}"
            )
    return bad


def check_control_shares(df: pd.DataFrame) -> list[str]:
    bad: list[str] = []
    control = df[df["condition_num"] == 0]
    n = len(control)
    if n == 0:
        return ["no control-group rows built at all"]
    counts = control["response_num"].value_counts()
    remain = counts.get(1, 0)
    leave = counts.get(2, 0)
    # The fold this script performs ONLY for comparison: response 3 ("Would not
    # vote") and 4 (recoded from raw 99, "Don't know") combined, matching the
    # authors' own `dk` dummy (do-file lines 132-134), which the built parquet
    # deliberately does NOT do at the row level (see recipe notes).
    dk_or_no_vote = counts.get(3, 0) + counts.get(4, 0)

    got_pct = {
        "remain": 100 * remain / n,
        "leave": 100 * leave / n,
        "dk_or_no_vote": 100 * dk_or_no_vote / n,
    }
    for key, want in CONTROL_PCT.items():
        got = got_pct[key]
        if abs(got - want) > PCT_TOLERANCE:
            bad.append(
                f"control group {key}: built {got:.1f}% (n={n}), paper p.8 says {want}% "
                f"(tolerance {PCT_TOLERANCE}pp)"
            )
    return bad


def main() -> int:
    df = load()
    failures = check_table_a6(df) + check_control_shares(df)

    print("PZB01G — built rows against Goodwin, Hix & Pickup (2020)")
    print(f"\n  Table A6 group sizes (N={len(df)} total):")
    for cond in sorted(CONDITIONS):
        got = int((df["condition_num"] == cond).sum())
        print(f"    {CONDITIONS[cond]:<45} built {got:>4}   Table A6 {TABLE_A6[cond]:>4}")

    control = df[df["condition_num"] == 0]
    n = len(control)
    counts = control["response_num"].value_counts()
    remain, leave = counts.get(1, 0), counts.get(2, 0)
    dk_or_no_vote = counts.get(3, 0) + counts.get(4, 0)
    print(f"\n  Control group Wave 2 vote intention (N={n}):")
    print(f"    Remain          built {100 * remain / n:.1f}%   paper {CONTROL_PCT['remain']}%")
    print(f"    Leave           built {100 * leave / n:.1f}%   paper {CONTROL_PCT['leave']}%")
    print(
        f"    DK/would-not-vote built {100 * dk_or_no_vote / n:.1f}%   "
        f"paper {CONTROL_PCT['dk_or_no_vote']}%"
    )

    if failures:
        print("\nFAILED:")
        for line in failures:
            print(f"  {line}")
        return 1
    print(
        "\nVERIFIED — all 9 Table A6 group sizes and the control group's 3 published shares agree."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
