"""Check the built X08IVC rows against Tilley & Hobolt's own Table 2.

X08IVC is not in SocSci210 (it is a UK Dataverse deposit), so
`pipeline/crosscheck.py` has nothing to compare it to and the recipe sets
`comparable_to_socsci210: false`. Table 2 (p.6 of the published, open-access
paper) is the answer key instead — an AUTHOR-COMPUTED reference, not a number
this project derived and then agreed with.

This reads the BUILT PARQUET, not the deposit. Reproducing Table 2 from the
`.sav` would only prove the paper is reproducible; reproducing it from the
melted rows proves the condition mapping (Treat -> Control/BID cue), the
outcome mapping (the split-ballot brexG1c/brexG2c resolution), the response
recode, and the persona (EUID -> brexit_identity) all survived the melt.

Tilley, J. and Hobolt, S. B. (2023), "Brexit as an Identity: Political
Identities and Policy Norms", PS: Political Science & Politics 56(4):546-552.
Table 2, p.6:

                    Leaver   Remainer
    Control          1.62      3.14     (N=451)
    BID cue          1.70      3.39     (N=431)

Both N's are the Leaver+Remainer subset (Neither/Don't-know respondents are
excluded from Table 2, and from this check, exactly as the paper does it) and
both reproduce EXACTLY from the built rows: 220+231=451 (Control) and
194+237=431 (BID cue) — see the recipe's own notes for the full breakdown and
for the paper's OWN prose elsewhere in Appendix 2 that does not sum to these
same N's (219+199+153=571, 200+221+143=564), which this script does not try
to reproduce because it disagrees with the paper's own printed table.

The paper reports no regression/coefficient table for this experiment — Table
2 is group means and N's only — so there is nothing beyond these six numbers
to check against an author-computed reference. That is stated here plainly
rather than padded out with a mechanical check dressed up as equivalent:
WHAT THIS DOES NOT COVER is anything about `shared_context` (the common
preamble sentence, present in both conditions and so invisible to a group-mean
comparison) or about respondents the paper's Table 2 itself excludes
(Neither/Don't-know, 131 Control + 111 BID cue = 242 of the built 1,124 rows).

Run:  uv run python scripts/verify_X08IVC.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
TOL = 0.005  # half the last printed digit, so a match to 2dp is required

TABLE_2 = {
    (0, "Leaver"): (1.62, 220),
    (0, "Remainer"): (3.14, 231),
    (1, "Leaver"): (1.70, 194),
    (1, "Remainer"): (3.39, 237),
}
CONDITION_NAME = {0: "Control", 1: "BID cue"}


def _identity(persona_json: str) -> str | None:
    return json.loads(persona_json).get("extra", {}).get("brexit_identity")


def main() -> int:
    df = pd.read_parquet(REPO / "data" / "processed" / "X08IVC.parquet")
    df["identity"] = df["persona"].map(_identity)

    ok = True

    # Full built N first, independent of Table 2's own exclusions.
    n_total = len(df)
    n_control = int((df["condition_num"] == 0).sum())
    n_cue = int((df["condition_num"] == 1).sum())
    print(f"Built rows: {n_total} total (Control {n_control}, BID cue {n_cue})")
    if n_total != 1124 or n_control != 582 or n_cue != 542:
        print(f"  FAIL expected 1124 = 582 + 542, got {n_total} = {n_control} + {n_cue}")
        ok = False
    else:
        print("  OK   matches 582 (splitnumber=1) + 542 (splitnumber=2) exactly")

    print()
    print("Table 2 (p.6) — Mean Support for Pro-Immigration Policy (1-5 Scale)")
    for (cond, identity), (expected_mean, expected_n) in TABLE_2.items():
        sub = df[(df["condition_num"] == cond) & (df["identity"] == identity)]
        n = len(sub)
        mean = sub["response_num"].mean()
        label = f"{CONDITION_NAME[cond]}/{identity}"
        if n != expected_n:
            print(f"  FAIL {label}: N built {n}, paper {expected_n}")
            ok = False
        else:
            print(f"  OK   {label}: N = {n} (paper {expected_n})")
        if abs(mean - expected_mean) > TOL:
            print(f"  FAIL {label}: mean built {mean:.4f}, paper {expected_mean}")
            ok = False
        else:
            print(f"  OK   {label}: mean = {mean:.4f} (paper {expected_mean:.2f})")

    print()
    diff_control = TABLE_2[(0, "Remainer")][0] - TABLE_2[(0, "Leaver")][0]
    built_diff_control = (
        df[(df["condition_num"] == 0) & (df["identity"] == "Remainer")]["response_num"].mean()
        - df[(df["condition_num"] == 0) & (df["identity"] == "Leaver")]["response_num"].mean()
    )
    print(
        f"Control Remainer-Leaver gap: built {built_diff_control:.3f}, "
        f"paper prose states 'substantial: 1.5 points' ({diff_control:.2f} in the table itself)"
    )

    print()
    print(f"OVERALL: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
