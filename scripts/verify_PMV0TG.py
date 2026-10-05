"""Check the built PMV0TG (UK) rows against the authors' own published LPM.

PMV0TG is the UK subset of the CANDOUR 13-country COVID-19 vaccine-allocation
conjoint (Duch et al., PNAS 2021). The deposit ships two per-country OLS
tables as plain `.tex` (no CSV/R answer-key script, unlike `EFXNLX`):
`conjoint_combined_results_ols.tex` (WEIGHTED by the deposit's own `weights`
column, per its caption) and `conjoint_combined_results_UNWEIGHTED_ols.tex`.
Both report, per country, a linear probability model regressing the
forced-choice/`select` indicator on dummies for the five conjoint attributes,
coefficients to 2 decimal places with significance stars.

**This script uses the UNWEIGHTED table.** `weights` has no field in
`schema.Row`/`schema.Persona` — CLAUDE.md's row contract is
(persona, condition, outcome, response), not a sampling weight, and `EFXNLX`'s
own answer key needed no weight column either — so the BUILT PARQUET does not
carry `weights` and a weighted comparison from the parquet alone is not
possible without adding a schema field for one study's verification. The
recipe's own notes record a SEPARATE, non-parquet check confirming the
weighted table also reproduces from the raw deposit with its `weights`
column; that supports the choice but is not what this script does, which is
read the BUILT parquet only, per project convention.

Method:
  1. Read the BUILT PARQUET (never the deposit). Keep all 9,320 rows (every
     row here is already the forced-choice item — there is no separate
     profile-level outcome in this deposit's 21 columns, unlike EFXNLX's
     QB2grid acceptability items).
  2. Reshape each round-level row back to the two PROFILES it compared, using
     the row's own `factors` (attribute text, melt OUTPUT) and `response_num`
     (1.0 = Person A chosen, 2.0 = Person B chosen): one profile record per
     side, `chosen` = 1 for the side that matches `response_num`. This
     recovers exactly the original deposit's 18,640-row profile-level
     structure (9,320 rounds x 2 sides).
  3. Fit an unweighted OLS, `chosen ~ ATTRIBUTES`, with each attribute coded
     as dummies against the SAME reference level codebook.pdf asterisks
     (`*Average risk of COVID-19 death`, `*...transmitting...`, `*Lowest 20%
     income level`, `*Not working`, `*25 years old`) — the reference levels
     are declared independently here, not imported from
     `scripts/gen_PMV0TG.py`, so a wrong baseline in the generator cannot
     hide behind an identical wrong baseline in the check.
  4. Compare the 17 coefficients (1 intercept + 2+2+2+7+3 dummies) against the
     UK column of `conjoint_combined_results_UNWEIGHTED_ols.tex`, transcribed
     as data below, to the paper's own printed precision (2dp) plus a little
     slack for rounding at the boundary.

Besides the point-estimate match, four more invariants are checked:
  (A) exact row counts: 9,320 round-level built rows, every one of 1,165
      respondents has exactly 8;
  (B) the reshape produces exactly 18,640 profile rows (9,320 x 2), the
      deposit's own documented row count;
  (C) `condition` and `factors` agree on every row (every factor value
      appears verbatim in the rendered text) — the same cross-check
      `verify_EFXNLX.py` uses to trust `factors` as a stand-in for a text
      parse;
  (D) the reshaped `chosen` indicator splits exactly 9,320/9,320 (every round
      has exactly one chosen side), matching the deposit's own documented
      `select` split.

Run:  uv run python scripts/verify_PMV0TG.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
PARQUET = REPO / "data" / "processed" / "PMV0TG.parquet"

EXPECTED_ROUND_ROWS = 9_320
EXPECTED_RESPONDENTS = 1_165
EXPECTED_PROFILE_ROWS = 18_640
EXPECTED_ROWS_PER_RESPONDENT = 8
COEF_TOLERANCE = 0.006  # the published table rounds to 2dp

# Reference levels per codebook.pdf's own asterisks — declared independently
# of scripts/gen_PMV0TG.py's ATTR_LEVELS, deliberately, so a wrong baseline in
# the generator cannot hide behind an identical wrong baseline here.
REF_VULNERABILITY = "Average risk of COVID-19 death"
REF_TRANSMISSION = "Average risk of catching and transmitting the COVID-19 virus"
REF_INCOME = "Lowest 20% income level"
REF_OCCUPATION = "Not working"
REF_AGE = "25 years old"

ATTRS = ["vulnerability", "transmission", "income", "occupation", "age_category"]
REF_OF = {
    "vulnerability": REF_VULNERABILITY,
    "transmission": REF_TRANSMISSION,
    "income": REF_INCOME,
    "occupation": REF_OCCUPATION,
    "age_category": REF_AGE,
}

# UK column transcribed from conjoint_combined_results_UNWEIGHTED_ols.tex
# (column 6 of 13: Canada, Colombia, Spain, US, Australia, UK, ...). Row label
# -> (full attribute-level text as it appears in `factors`, coefficient).
UK_UNWEIGHTED: dict[str, float] = {
    "Intercept": 0.04,
    "vulnerability[T.Moderate (Twice the average risk of COVID-19 death)]": 0.10,
    "vulnerability[T.High (Five times the average risk of COVID-19 death)]": 0.27,
    "transmission[T.Moderate risk (Twice the average risk of catching and transmitting the "
    "COVID-19 virus)]": 0.07,
    "transmission[T.High risk (Five times the average risk of catching and transmitting the "
    "COVID-19 virus)]": 0.22,
    "income[T.Average income level]": -0.01,
    "income[T.Highest 20% income level]": -0.03,
    "occupation[T.Non-Key worker: Can work at home]": 0.01,
    "occupation[T.Non-Key worker: Cannot work at home]": 0.11,
    "occupation[T.Key worker: Education and childcare]": 0.27,
    "occupation[T.Key worker: Factory worker]": 0.19,
    "occupation[T.Key worker: Water and electricity service]": 0.22,
    "occupation[T.Key worker: Police and fire-fighting]": 0.27,
    "occupation[T.Key worker: Health and social care]": 0.32,
    "age_category[T.40 years old]": 0.06,
    "age_category[T.65 years old]": 0.13,
    "age_category[T.79 years old]": 0.16,
}


def load_built() -> pd.DataFrame:
    if not PARQUET.exists():
        raise SystemExit(f"{PARQUET} not found — run `uv run mmds build recipes/PMV0TG.yaml` first")
    return pd.read_parquet(PARQUET)


def check_row_counts(df: pd.DataFrame) -> list[str]:
    bad = []
    if len(df) != EXPECTED_ROUND_ROWS:
        bad.append(f"(A) round-level rows: got {len(df)}, expected {EXPECTED_ROUND_ROWS}")
    if df["participant_id"].nunique() != EXPECTED_RESPONDENTS:
        bad.append(
            f"(A) respondents: got {df['participant_id'].nunique()}, expected {EXPECTED_RESPONDENTS}"
        )
    counts = df.groupby("participant_id").size()
    bad_resp = counts[counts != EXPECTED_ROWS_PER_RESPONDENT]
    if len(bad_resp):
        bad.append(
            f"(A) {len(bad_resp)} respondents do not have exactly "
            f"{EXPECTED_ROWS_PER_RESPONDENT} rows"
        )
    if sorted(df["task_num"].unique()) != list(range(8)):
        bad.append(f"(A) task_num values are not exactly 0..7: {sorted(df['task_num'].unique())}")
    return bad


def check_condition_matches_factors(df: pd.DataFrame) -> list[str]:
    bad = []
    mismatches = 0
    for _, row in df.iterrows():
        cond = row["condition"]
        for key, value in row["factors"].items():
            if str(value) not in cond:
                mismatches += 1
                if mismatches <= 5:
                    bad.append(
                        f"(C) condition_num={row['condition_num']}: factor {key}={value!r} "
                        "not found verbatim in rendered condition text"
                    )
    if mismatches > 5:
        bad.append(f"(C) ... and {mismatches - 5} more such mismatches")
    return bad


def reshape_to_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Mirror the deposit's own A/B profile-row structure: one row per
    (respondent, round, side), `chosen` = 1 for the side `response_num` names.
    """
    records = []
    for _, row in df.iterrows():
        factors = row["factors"]
        resp = row["response_num"]
        for side, chosen_value in (("A", 1.0), ("B", 2.0)):
            rec = {
                "participant_id": row["participant_id"],
                "round": row["condition_num"],
                "chosen": int(resp == chosen_value),
            }
            for attr in ATTRS:
                rec[attr] = factors[f"{attr}_{side}"]
            records.append(rec)
    return pd.DataFrame.from_records(records)


def main() -> int:
    df = load_built()
    print("PMV0TG (UK) — built rows against the authors' own unweighted LPM")
    print(f"\nbuilt parquet: {len(df)} rows")

    failures: list[str] = []
    failures += check_row_counts(df)
    failures += check_condition_matches_factors(df)

    profile = reshape_to_profile(df)
    print(f"reshaped to {len(profile)} profile rows (2 per round)")
    if len(profile) != EXPECTED_PROFILE_ROWS:
        failures.append(
            f"(B) reshape produced {len(profile)} profile rows, expected {EXPECTED_PROFILE_ROWS}"
        )
    chosen_counts = profile["chosen"].value_counts().to_dict()
    if chosen_counts != {1: EXPECTED_ROUND_ROWS, 0: EXPECTED_ROUND_ROWS}:
        failures.append(f"(D) chosen split {chosen_counts}, expected 1:{9320} 0:{9320}")

    # Plain OLS by closed-form least squares (no statsmodels/patsy dependency
    # for one verify script): an intercept column plus, per attribute, a
    # dummy for every level EXCEPT the reference — the usual LPM dummy coding,
    # with the reference level chosen independently above.
    n = len(profile)
    design_cols: list[str] = ["Intercept"]
    design = [np.ones(n)]
    for attr in ATTRS:
        levels = sorted(v for v in profile[attr].unique() if v != REF_OF[attr])
        for level in levels:
            design_cols.append(f"{attr}[T.{level}]")
            design.append((profile[attr] == level).to_numpy(dtype=float))
    design_matrix = np.column_stack(design)
    y = profile["chosen"].to_numpy(dtype=float)
    coefs, _residuals, rank, _sv = np.linalg.lstsq(design_matrix, y, rcond=None)
    if rank < design_matrix.shape[1]:
        failures.append(
            f"design matrix is rank-deficient: rank={rank}, columns={design_matrix.shape[1]}"
        )
    fitted = design_matrix @ coefs
    ss_res = float(np.sum((y - fitted) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot

    print(f"\nN = {n}, R^2 = {r2:.4f}")

    ours = dict(zip(design_cols, coefs, strict=True))

    max_diff = 0.0
    for key, published in UK_UNWEIGHTED.items():
        got = ours.get(key)
        if got is None:
            failures.append(f"no fitted coefficient for {key!r}")
            continue
        diff = abs(got - published)
        max_diff = max(max_diff, diff)
        if diff > COEF_TOLERANCE:
            failures.append(
                f"{key}: built={got:.4f} published={published:.2f} diff={diff:.4f} "
                f"(tolerance {COEF_TOLERANCE})"
            )

    print(f"largest absolute coefficient disagreement: {max_diff:.5f}")

    if failures:
        print("\nFAILED:")
        for line in failures:
            print(f"  {line}")
        return 1

    print(
        f"\nVERIFIED — {len(UK_UNWEIGHTED)} coefficients agree with the UK column of "
        f"conjoint_combined_results_UNWEIGHTED_ols.tex to within {COEF_TOLERANCE}; "
        "invariants (A)-(D) hold."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
