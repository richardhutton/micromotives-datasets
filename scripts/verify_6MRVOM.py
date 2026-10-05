"""Check the built 6MRVOM rows against what the deposit's OWN code computed.

6MRVOM is not in SocSci210 (it is a UK Dataverse deposit), so
`pipeline/crosscheck.py` has nothing to compare it to and both recipes set
`comparable_to_socsci210: false`. Two different situations apply to the two
recipes built from this deposit, and this script treats them honestly rather
than papering over the difference:

  `6MRVOM_eu_share.yaml`        — the deposit's own `analysis.R` computes a
                                    weighted mean of exactly this outcome
                                    (`eushare`), printed as comments in the
                                    script. THAT is the answer key, and this
                                    script reproduces it from the BUILT
                                    PARQUET to high precision.

  `6MRVOM_brexit_scenario.yaml` — `analysis.R` never touches this block (grep
                                    confirms zero references to Q6_1/Q6_2/
                                    q71l/q72l/ExpSplitQ67), and the published
                                    paper (24-page accepted manuscript, read in
                                    full) never reports on it either — it was
                                    fielded but never analysed by the authors
                                    anywhere public. There is therefore no
                                    author-computed or published number to
                                    reproduce for this recipe, and this script
                                    says so rather than substituting a number
                                    this project computed itself (which would
                                    be worthless as a check — an answer key we
                                    computed and then agreed with proves
                                    nothing). What IS checked here is
                                    mechanical: that the built parquet's
                                    response distribution, split by condition
                                    and item, reproduces data.sav's own
                                    frequency tables EXACTLY, cell for cell —
                                    proving the melt is faithful to the file,
                                    which is a real (if weaker) check.

Both checks read the BUILT PARQUET, not the deposit, for the figures that can
be compared to an external number — reproducing analysis.R's `eushare` number
from the raw `.sav` would only prove analysis.R is reproducible; reproducing it
from the melted rows proves the condition mapping, the 997-is-missing recode,
and the persona join all survived the melt.

EU_SHARE WEIGHTING. `analysis.R` lines ~58-69 build `eushare <- ifelse(d$
ExpSplitQ5==1, d$Q5T, d$Q5)`, blank it at 997, and report:

    svymean(~ eushare, design = svy, na.rm = TRUE)                    46.87
    svyby(~ eushare, ~ tr_eushare, ..., FUN = svymean, na.rm=TRUE)
      Information (Q5T, ExpSplitQ5==1)                                46.98297
      Control     (Q5,  ExpSplitQ5==2)                                46.75926

`svy <- svydesign(data=d, ids=~0, weights=~W8)` declares NO clusters (`ids=~0`),
so `svymean` reduces to the plain weight-ratio estimator sum(w*x)/sum(w) — no
replicate weights, no finite-population correction. The built parquet does not
carry `W8` (it is a survey weight, not a persona/condition/outcome/response
field), so this script re-reads `data.sav` ONLY for `W8` and `ID`-equivalent row
position, and joins it back onto the built rows by `participant_id`
("6MRVOM:<row index>"), which `pipeline/build.py` derives from the SAME
`ds.df.iterrows()` order `pyreadstat.read_sav` always produces — confirmed by
checking the join recovers exactly 2,397 of 2,397 built rows with a weight,
zero unmatched.

Run:  uv run python scripts/verify_6MRVOM.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

REPO = Path(__file__).resolve().parents[1]
EU_SHARE_PARQUET = REPO / "data" / "processed" / "6MRVOM_eu_share.parquet"
SCENARIO_PARQUET = REPO / "data" / "processed" / "6MRVOM_brexit_scenario.parquet"
RAW_SAV = REPO / "data" / "raw" / "6MRVOM" / "data.sav"

# analysis.R's own printed output (lines ~58-69), transcribed verbatim.
PUBLISHED_OVERALL = 46.87
PUBLISHED_INFO = 46.98297  # tr_eushare == "Information" == ExpSplitQ5 == 1 (Q5T)
PUBLISHED_CONTROL = 46.75926  # tr_eushare == "Control" == ExpSplitQ5 == 2 (Q5)
# The printed figures are rounded to different precisions in analysis.R's own
# comments (the overall mean to 2 d.p., the by-group means to 5 d.p.), so the
# tolerance matches each one's own rounding rather than a single shared value.
TOLERANCE_OVERALL = 0.005
TOLERANCE_GROUP = 0.000005


def load_weights() -> pd.DataFrame:
    """ID (row position) -> W8, read the same way build.py reads the file."""
    df, _meta = pyreadstat.read_sav(str(RAW_SAV))
    out = df[["W8"]].copy()
    out["participant_id"] = [f"6MRVOM:{i}" for i in df.index]
    return out


def check_eu_share() -> list[str]:
    bad: list[str] = []
    if not EU_SHARE_PARQUET.exists():
        raise SystemExit(f"{EU_SHARE_PARQUET} not found — run `uv run mmds build recipes/6MRVOM_eu_share.yaml` first")
    rows = pd.read_parquet(EU_SHARE_PARQUET)
    weights = load_weights()
    merged = rows.merge(weights, on="participant_id", how="left", validate="one_to_one")
    unmatched = int(merged["W8"].isna().sum())
    if unmatched:
        bad.append(f"eu_share: {unmatched} of {len(merged)} built rows failed to join a weight")

    def wmean(mask: pd.Series) -> tuple[float, int]:
        sub = merged[mask]
        w = sub["W8"].to_numpy(dtype=float)
        x = sub["response_num"].to_numpy(dtype=float)
        return float(np.sum(w * x) / np.sum(w)), len(sub)

    overall, n_all = wmean(pd.Series(True, index=merged.index))
    info, n_info = wmean(merged["condition_num"] == 1)  # Q5T, present
    control, n_control = wmean(merged["condition_num"] == 0)  # Q5, absent

    print("6MRVOM_eu_share — built rows against analysis.R's own svymean() output")
    print(f"  N = {len(merged):,} (expected 2,397: 1,183 Q5T + 1,214 Q5)")
    print(f"  overall weighted mean  {overall:.5f}  (analysis.R: {PUBLISHED_OVERALL}, n={n_all})")
    print(f"  Information (Q5T)      {info:.5f}  (analysis.R: {PUBLISHED_INFO}, n={n_info})")
    print(f"  Control (Q5)           {control:.5f}  (analysis.R: {PUBLISHED_CONTROL}, n={n_control})")

    if len(merged) != 2397:
        bad.append(f"eu_share: N={len(merged)}, expected 2397 (1,183 Q5T + 1,214 Q5)")
    if n_info != 1183:
        bad.append(f"eu_share: Q5T (condition_num=1) N={n_info}, expected 1183")
    if n_control != 1214:
        bad.append(f"eu_share: Q5 (condition_num=0) N={n_control}, expected 1214")
    for label, got, want, tol in (
        ("overall", overall, PUBLISHED_OVERALL, TOLERANCE_OVERALL),
        ("Information (Q5T)", info, PUBLISHED_INFO, TOLERANCE_GROUP),
        ("Control (Q5)", control, PUBLISHED_CONTROL, TOLERANCE_GROUP),
    ):
        if abs(got - want) > tol:
            bad.append(f"eu_share: {label} mean={got:.5f}, analysis.R reports {want} (tolerance {tol})")
    return bad


# -- brexit_scenario: no author-computed reference exists; mechanical check only --

OUTCOME_VARS = {
    (1, 0): "Q6_1",
    (1, 1): "q71l",
    (2, 0): "Q6_2",
    (2, 1): "q72l",
}
ARM_TO_CONDITION_NUM = {1: 0, 2: 1}


def raw_distribution() -> dict[tuple[int, int, int], int]:
    """(condition_num, task_num, response) -> count, computed straight from data.sav."""
    df, _meta = pyreadstat.read_sav(str(RAW_SAV))
    out: dict[tuple[int, int, int], int] = {}
    for (arm, task), var in OUTCOME_VARS.items():
        cond_num = ARM_TO_CONDITION_NUM[arm]
        sub = df.loc[df["ExpSplitQ67"] == arm, var]
        sub = sub[~sub.isna()]
        for value, count in sub.value_counts().items():
            code = int(value)
            if code in (98, 99, 998, 999):
                continue
            out[(cond_num, task, code)] = out.get((cond_num, task, code), 0) + int(count)
    return out


def built_distribution(rows: pd.DataFrame) -> dict[tuple[int, int, int], int]:
    out: dict[tuple[int, int, int], int] = {}
    for (cond_num, task, resp), count in (
        rows.groupby(["condition_num", "task_num", "response_num"]).size().items()
    ):
        out[(int(cond_num), int(task), int(resp))] = int(count)
    return out


def check_brexit_scenario() -> list[str]:
    bad: list[str] = []
    if not SCENARIO_PARQUET.exists():
        raise SystemExit(
            f"{SCENARIO_PARQUET} not found — run `uv run mmds build recipes/6MRVOM_brexit_scenario.yaml` first"
        )
    rows = pd.read_parquet(SCENARIO_PARQUET)

    print("\n6MRVOM_brexit_scenario — NO author-computed or published reference exists")
    print("  analysis.R: zero references to Q6_1/Q6_2/q71l/q72l/ExpSplitQ67 (grepped).")
    print("  Published accepted manuscript (24 pp, read in full): never analyses this block.")
    print("  This is 'cannot determine from source' for an independent numeric answer key —")
    print("  stated as a finding, not substituted with a number this project computed itself.")
    print()
    print("  Mechanical check instead: built parquet's response distribution, by")
    print("  (condition_num, task_num, response), against data.sav's own frequency tables.")

    want = raw_distribution()
    got = built_distribution(rows)
    if want != got:
        only_want = {k: v for k, v in want.items() if got.get(k) != v}
        only_got = {k: v for k, v in got.items() if want.get(k) != v}
        bad.append(f"brexit_scenario: distribution mismatch — in data.sav not matched: {only_want}")
        if only_got:
            bad.append(f"brexit_scenario: in built parquet not matched: {only_got}")
    else:
        print(f"  MATCH — all {len(want)} (condition, task, response) cells agree exactly.")

    if len(rows) != 7272:
        bad.append(f"brexit_scenario: N={len(rows)}, expected 7272 (3,636 respondents x 2 outcomes)")
    else:
        print(f"  N = {len(rows):,} (expected 7,272: 3,636 respondents x 2 outcomes). Match.")

    party = rows[rows["task_num"] == 0]
    dk_rows = int((party["response_num"] == 12).sum())
    print(
        f"  party-choice N={len(party):,} includes {dk_rows:,} 'Don't know' (code 12) rows, "
        "kept as a genuine response — see recipe notes for the judgement."
    )
    if len(party) != 3636:
        bad.append(f"brexit_scenario: party-choice N={len(party)}, expected 3636 (12 kept as a response)")

    return bad


def main() -> int:
    failures = check_eu_share() + check_brexit_scenario()
    if failures:
        print("\nFAILED:")
        for line in failures:
            print(f"  {line}")
        return 1
    print("\nVERIFIED — eu_share matches analysis.R's svymean() output; brexit_scenario's")
    print("built distribution matches data.sav exactly (no author-computed reference exists).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
