"""Check the built EFXNLX rows against the authors' own cregg::cj() estimates.

EFXNLX is an 8-attribute forced-choice conjoint (Hobolt, Tilley & Leeper,
"Policy Preferences and Policy Legitimacy After Referendums"). The deposit's
own Supplementary Information (`analysis.Rmd`) computes every published
number with `cregg::cj()`, and `scripts/answer_key_EFXNLX.R` re-runs that
exact call over the RAW `.sav` to produce `data/catalog/answer_key_EFXNLX.csv`
— 42 AMCEs and 42 marginal means, the numeric answer key for this study
(`comparable_to_socsci210: false`, so there is no other one).

Re-deriving AMCEs in Python would check our code against our code, which the
answer-key script's own comments rule out. So this script instead:

  1. Reads the BUILT PARQUET (never the deposit) and keeps the 16,465
     pair-level forced-choice rows (task_num in {0, 3, 6, 9, 12}).
  2. Reshapes each one back to the two profiles it compared, exactly as
     `analysis-conjoint-cleaning.R` and `answer_key_EFXNLX.R` do over the raw
     data: one row per (respondent, pair, side), `chosen` = 1 for the side the
     respondent picked, 0 for the other, 8 attribute columns.
  3. Hands that to `scripts/verify_EFXNLX_cj.R`, which runs the IDENTICAL
     cregg::cj() call the answer-key script ran, over this input instead of
     the raw one.
  4. Compares the resulting 42 AMCEs and 42 marginal means against the answer
     key. Agreement proves the melt: the condition's 16 attribute values, the
     forced-choice response, and the respondent identifier all survived intact
     from raw .sav to parquet, because the only way the same estimator can
     return the same numbers over two different inputs is if those inputs
     encode the same design.

The attribute values used in step 2 come from the parquet's own `factors`
column, NOT from re-parsing the rendered `condition` prose. That column is
itself melt OUTPUT (written by the same build that wrote `condition`), so
reading it is still "reading the built artifact", and it is the sound choice
over a text parse: the condition text has free-form punctuation (en-dashes,
£ signs, curly quotes) that a regex could silently mis-extract, which would
test the regex, not the melt. Instead, invariant (E) below cross-checks the
two against each other directly, on every pair-level row — if `factors` and
`condition` ever disagreed, that check would fail on its own.

Besides the 84 point estimates, five more invariants are checked, each aimed
at a different failure mode a passing cj() comparison would not itself catch:

  (A) exact row counts (16,465 pair-level, 32,930 profile-level);
  (B) every respondent appears exactly 5 times at pair level, 10 at profile
      level;
  (C) the response distribution per outcome (all 15 of them) matches a direct
      tally from the raw .sav;
  (D) all 16,465 pair-level condition strings are distinct, and so are all
      16,465 attribute 16-tuples recovered from `factors`;
  (E) `condition` and `factors` agree on every pair-level row (every factor
      value appears verbatim in the rendered text);
  (F) the marginal means average to 0.5, both in the answer key and in our
      own cj() run over the melted data.

Run:  uv run python scripts/verify_EFXNLX.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pyreadstat

REPO = Path(__file__).resolve().parents[1]
PARQUET = REPO / "data" / "processed" / "EFXNLX.parquet"
ANSWER_KEY = REPO / "data" / "catalog" / "answer_key_EFXNLX.csv"
RAW_SAV = REPO / "data" / "raw" / "EFXNLX" / "LSEResults_Brexit_170428_client.sav"
R_HELPER = REPO / "scripts" / "verify_EFXNLX_cj.R"

ATTRS = ["imigration", "rights", "trade", "laws", "budget", "payment", "border", "timeline"]

# task_num -> position in the questionnaire. 0,3,6,9,12 are the forced-choice
# preference item for pairs 1..5 (QB1_PAIRn); the other ten are the two
# per-pair acceptability ratings (QB2gridA/B_PAIRn), not used by cj() here —
# see answer_key_EFXNLX.R, which reshapes only Q1 (the forced choice).
PAIR_TASK_NUMS = [0, 3, 6, 9, 12]

# --- expected values, named so a future melt break fails loudly -----------
EXPECTED_PAIR_ROWS = 16_465
EXPECTED_PROFILE_ROWS = 32_930
EXPECTED_RESPONDENTS = 3_293
EXPECTED_ROWS_PER_RESPONDENT_PAIR = 5
EXPECTED_ROWS_PER_RESPONDENT_PROFILE = 10
EXPECTED_DISTINCT_CONDITIONS = 16_465
RAW_DATA_MM_MEAN = 0.499845  # printed by answer_key_EFXNLX.R over the raw .sav
MM_MEAN_TOLERANCE = 1e-5
AMCE_TOLERANCE = 1e-6
MM_TOLERANCE = 1e-6


def rawvar(task_num: int) -> str:
    pair = task_num // 3 + 1
    sub = task_num % 3
    if sub == 0:
        return f"QB1_PAIR{pair}"
    if sub == 1:
        return f"QB2gridA_PAIR{pair}"
    return f"QB2gridB_PAIR{pair}"


def load_built() -> pd.DataFrame:
    if not PARQUET.exists():
        raise SystemExit(f"{PARQUET} not found — run `uv run mmds build recipes/EFXNLX.yaml` first")
    return pd.read_parquet(PARQUET)


def check_row_counts(df: pd.DataFrame) -> list[str]:
    bad = []
    pair = df[df["task_num"].isin(PAIR_TASK_NUMS)]
    profile = df[~df["task_num"].isin(PAIR_TASK_NUMS)]

    if len(pair) != EXPECTED_PAIR_ROWS:
        bad.append(f"(A) pair-level rows: got {len(pair)}, expected {EXPECTED_PAIR_ROWS}")
    if len(profile) != EXPECTED_PROFILE_ROWS:
        bad.append(f"(A) profile-level rows: got {len(profile)}, expected {EXPECTED_PROFILE_ROWS}")
    if df["participant_id"].nunique() != EXPECTED_RESPONDENTS:
        bad.append(
            f"(A) respondents: got {df['participant_id'].nunique()}, expected {EXPECTED_RESPONDENTS}"
        )

    pair_counts = pair.groupby("participant_id").size()
    bad_pair_resp = pair_counts[pair_counts != EXPECTED_ROWS_PER_RESPONDENT_PAIR]
    if len(bad_pair_resp):
        bad.append(
            f"(B) {len(bad_pair_resp)} respondents do not have exactly "
            f"{EXPECTED_ROWS_PER_RESPONDENT_PAIR} pair-level rows"
        )

    profile_counts = profile.groupby("participant_id").size()
    bad_profile_resp = profile_counts[profile_counts != EXPECTED_ROWS_PER_RESPONDENT_PROFILE]
    if len(bad_profile_resp):
        bad.append(
            f"(B) {len(bad_profile_resp)} respondents do not have exactly "
            f"{EXPECTED_ROWS_PER_RESPONDENT_PROFILE} profile-level rows"
        )

    return bad


def check_response_distribution(df: pd.DataFrame) -> list[str]:
    bad = []
    raw, _meta = pyreadstat.read_sav(str(RAW_SAV))
    for task_num in range(15):
        var = rawvar(task_num)
        built_counts = df[df["task_num"] == task_num]["response_num"].value_counts().to_dict()
        raw_series = raw[var].dropna().astype(float)
        raw_counts = raw_series.value_counts().to_dict()
        if built_counts != raw_counts:
            bad.append(
                f"(C) task {task_num} ({var}): built={built_counts} != raw .sav={raw_counts}"
            )
    return bad


def check_response_matches_response_num(df: pd.DataFrame) -> list[str]:
    """(G) The shipped `response` agrees with the `response_num` we verify against.

    Everything above tests `response_num`, because that is what the estimator
    needs. But `response` is the field a CONSUMER of this dataset reads — it is
    the fourth element of the row contract. They agree today; nothing asserted
    that they must, so a melt that wrote one correctly and the other wrongly
    would verify to machine precision and still ship wrong responses.

    Found by mutation-testing this script: corrupting `response` changed nothing,
    which is the right behaviour for the estimator and the wrong silence for the
    dataset.
    """
    bad = []
    for task_num in range(15):
        rows = df[df["task_num"] == task_num]
        if rows.empty:
            continue
        seen = rows[["response", "response_num"]].drop_duplicates()
        for text, num in zip(seen["response"], seen["response_num"], strict=True):
            try:
                as_num = float(str(text).strip())
            except ValueError:
                # A labelled response (e.g. "Completely acceptable") cannot be
                # compared numerically; distinctness is what matters there.
                continue
            if as_num != float(num):
                bad.append(
                    f"(G) task {task_num}: response {text!r} is paired with "
                    f"response_num {num} — they disagree"
                )
        # One text per number and one number per text, whatever the coding.
        for col, other in (("response", "response_num"), ("response_num", "response")):
            fanout = rows.groupby(col)[other].nunique()
            if (fanout > 1).any():
                offenders = fanout[fanout > 1].to_dict()
                bad.append(f"(G) task {task_num}: {col} maps to several {other}: {offenders}")
    return bad


def check_condition_distinctness(pair: pd.DataFrame) -> tuple[list[str], pd.Series]:
    bad = []
    n_cond = pair["condition"].nunique()
    if n_cond != EXPECTED_DISTINCT_CONDITIONS:
        bad.append(
            f"(D) distinct condition strings among pair-level rows: got {n_cond}, "
            f"expected {EXPECTED_DISTINCT_CONDITIONS}"
        )

    tuples = pair["factors"].map(lambda d: tuple(sorted(d.items())))
    n_tuples = tuples.nunique()
    if n_tuples != EXPECTED_DISTINCT_CONDITIONS:
        bad.append(
            f"(D) distinct attribute 16-tuples among pair-level rows: got {n_tuples}, "
            f"expected {EXPECTED_DISTINCT_CONDITIONS}"
        )
    return bad, tuples


def check_condition_matches_factors(pair: pd.DataFrame) -> list[str]:
    """(E) Every factor value must appear verbatim in the rendered condition text.

    This is the cross-check that lets us trust `factors` as a stand-in for a
    text parse: if the melt ever wrote a `factors` entry that did not match
    what it rendered, this would catch it independently of the cj() numbers.
    """
    bad = []
    mismatches = 0
    for _, row in pair.iterrows():
        cond = row["condition"]
        for key, value in row["factors"].items():
            if str(value) not in cond:
                mismatches += 1
                if mismatches <= 5:
                    bad.append(
                        f"(E) condition_num={row['condition_num']}: factor {key}={value!r} "
                        "not found verbatim in rendered condition text"
                    )
    if mismatches > 5:
        bad.append(f"(E) ... and {mismatches - 5} more such mismatches")
    return bad


def reshape_to_profile(pair: pd.DataFrame) -> pd.DataFrame:
    """Mirror analysis-conjoint-cleaning.R's reshape: one row per
    (respondent, pair, side), `chosen` = 1 for the picked side."""
    records = []
    for _, row in pair.iterrows():
        factors = row["factors"]
        resp = row["response_num"]
        for side, chosen_value in (("A", 1.0), ("B", 2.0)):
            rec = {
                "ID": row["participant_id"],
                "pair": row["condition_num"],
                "chosen": int(resp == chosen_value),
            }
            for a in ATTRS:
                rec[a] = factors[f"{a}_{side}"]
            records.append(rec)
    return pd.DataFrame.from_records(records)


def run_cj(profile: pd.DataFrame, tmpdir: Path) -> pd.DataFrame:
    in_csv = tmpdir / "profile.csv"
    out_csv = tmpdir / "cj_out.csv"
    profile.to_csv(in_csv, index=False)

    result = subprocess.run(
        ["Rscript", str(R_HELPER), str(in_csv), str(out_csv)],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise SystemExit(f"Rscript {R_HELPER} failed with exit code {result.returncode}")
    if result.stderr.strip():
        print("R stderr:\n" + result.stderr, file=sys.stderr)

    return pd.read_csv(out_csv)


def compare_estimates(ours: pd.DataFrame, key: pd.DataFrame) -> tuple[list[str], float, float]:
    """Join on (quantity, feature, level) and compare point estimates.

    Returns (failures, max_abs_diff_amce, max_abs_diff_mm).
    """
    bad = []
    merged = ours.merge(
        key,
        on=["quantity", "feature", "level"],
        how="outer",
        suffixes=("_built", "_key"),
        indicator=True,
    )

    unmatched = merged[merged["_merge"] != "both"]
    if len(unmatched):
        for _, row in unmatched.iterrows():
            bad.append(
                f"no match for quantity={row['quantity']} feature={row['feature']} "
                f"level={row['level']!r} (_merge={row['_merge']})"
            )

    matched = merged[merged["_merge"] == "both"].copy()
    matched["abs_diff"] = (matched["estimate_built"] - matched["estimate_key"]).abs()

    amce_rows = matched[matched["quantity"] == "amce"]
    mm_rows = matched[matched["quantity"] == "mm"]
    max_amce = amce_rows["abs_diff"].max() if len(amce_rows) else float("nan")
    max_mm = mm_rows["abs_diff"].max() if len(mm_rows) else float("nan")

    for _, row in amce_rows.iterrows():
        if row["abs_diff"] > AMCE_TOLERANCE:
            bad.append(
                f"AMCE {row['feature']} / {row['level']!r}: built={row['estimate_built']:.6f} "
                f"key={row['estimate_key']:.6f} diff={row['abs_diff']:.6f} "
                f"(tolerance {AMCE_TOLERANCE})"
            )
    for _, row in mm_rows.iterrows():
        if row["abs_diff"] > MM_TOLERANCE:
            bad.append(
                f"MM {row['feature']} / {row['level']!r}: built={row['estimate_built']:.6f} "
                f"key={row['estimate_key']:.6f} diff={row['abs_diff']:.6f} "
                f"(tolerance {MM_TOLERANCE})"
            )

    return bad, max_amce, max_mm


def main() -> int:
    df = load_built()
    pair = df[df["task_num"].isin(PAIR_TASK_NUMS)].reset_index(drop=True)

    print("EFXNLX — built rows against the authors' own cregg::cj() estimator")
    print(f"\nbuilt parquet: {len(df)} total rows ({len(pair)} pair-level)")

    failures: list[str] = []

    failures += check_row_counts(df)
    failures += check_response_distribution(df)

    cond_failures, _tuples = check_condition_distinctness(pair)
    failures += cond_failures
    failures += check_condition_matches_factors(pair)
    failures += check_response_matches_response_num(df)

    print("\nreshaping pair-level rows back to profile level (chosen indicator)...")
    profile = reshape_to_profile(pair)
    expected_profile_n = 2 * len(pair)
    if len(profile) != expected_profile_n:
        failures.append(
            f"reshape produced {len(profile)} profile rows, expected {expected_profile_n}"
        )
    print(f"reshaped to {len(profile)} profile rows (2 per pair-level row)")

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        print(f"\nrunning cregg::cj() via {R_HELPER.name}...")
        ours = run_cj(profile, tmpdir)

    key = pd.read_csv(ANSWER_KEY)

    cmp_failures, max_amce_diff, max_mm_diff = compare_estimates(ours, key)
    failures += cmp_failures

    print(f"\nlargest absolute AMCE disagreement:           {max_amce_diff:.8f}")
    print(f"largest absolute marginal-mean disagreement:  {max_mm_diff:.8f}")

    key_mm_mean = key[key["quantity"] == "mm"]["estimate"].mean()
    ours_mm_mean = ours[ours["quantity"] == "mm"]["estimate"].mean()
    print(f"\nmean of marginal means — answer key (raw .sav path): {key_mm_mean:.6f}")
    print(f"mean of marginal means — built parquet path:         {ours_mm_mean:.6f}")

    if abs(key_mm_mean - RAW_DATA_MM_MEAN) > MM_MEAN_TOLERANCE:
        failures.append(
            f"(F) answer key's own mean of marginal means {key_mm_mean:.6f} does not match "
            f"the documented raw-data value {RAW_DATA_MM_MEAN} within {MM_MEAN_TOLERANCE}"
        )
    if abs(ours_mm_mean - 0.5) > 0.01:
        failures.append(
            f"(F) built-path mean of marginal means {ours_mm_mean:.6f} is not close to the "
            "0.5 a fully-randomised forced choice implies"
        )

    if failures:
        print("\nFAILED:")
        for line in failures:
            print(f"  {line}")
        return 1

    print(
        f"\nVERIFIED — {len(ours)} point estimates ({(ours['quantity'] == 'amce').sum()} AMCEs, "
        f"{(ours['quantity'] == 'mm').sum()} marginal means) agree with answer_key_EFXNLX.csv "
        f"to within {AMCE_TOLERANCE}; all invariants (A)-(G) hold."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
