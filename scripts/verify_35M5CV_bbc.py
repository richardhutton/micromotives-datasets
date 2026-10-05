"""Check the built 35M5CV BBC rows against the authors' own cregg::cj() estimates.

Hobolt, Leeper & Tilley, "Divided by the Vote: Affective Polarization in the
Wake of the Brexit Referendum" — the BBC conjoint. The deposit reports
every result as a plot only (ledger 99's precedent: a drawn bar is not a
usable answer key), but ships `bbc-analysis-cleaning.R`/`bbc-analysis.Rmd`
as R Markdown SOURCE, which computes AMCE/MM tables with `cregg::cj()` before
handing them to ggplot. `scripts/answer_key_35M5CV.R` re-runs that cleaning and
that estimator over the RAW `.sav` and writes
`data/catalog/answer_key_35M5CV_bbc.csv` — the numeric answer key for this
study (`comparable_to_socsci210: false`).

Re-deriving AMCEs in Python would check our code against our code, so instead:

  1. Read the BUILT PARQUET (never the deposit). Every row here is already
     pair-level (there is no profile-level outcome in this study — see
     `gen_35M5CV_bbc.py`'s module docstring).
  2. Reshape each row back to the two profiles it compared, exactly as
     `bbc-analysis-cleaning.R` and `answer_key_35M5CV.R` do: one row per
     (respondent, pair, side), `chosen` = 1 for the side the respondent
     picked, 0 for the other, 7 attribute columns (note: our `politics`
     factor is renamed to `party` in this step, matching the answer key's own
     column name — `cregg`'s feature names come from the data frame's own
     column names, not from our recipe's vocabulary).
  3. Hand that to `scripts/verify_35M5CV_bbc_cj.R`, which runs the
     IDENTICAL `cregg::cj()` call, releveling each feature to the SAME
     reference level the answer key used (read from the answer key's own
     `reference` column, never guessed).
  4. Compare the resulting 37 AMCEs and 37 marginal means (one per level,
     including each feature's own baseline row, which `cregg` reports at
     exactly 0) against the answer key.

Besides the point estimates, several invariants are checked, the most
important being (H): for a sample of rows, the response this project recorded
is independently re-derived STRAIGHT FROM THE RAW .sav by matching `QPAIRt`
(a NAME code) against `name_seen1_t{t}`/`name_seen2_t{t}` — the one mechanism
the brief flagged as the highest-risk trap in this study, verified here
end-to-end against the BUILT rows rather than only at generation time.

Run:  uv run python scripts/verify_35M5CV_bbc.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pyreadstat

REPO = Path(__file__).resolve().parents[1]
PARQUET = REPO / "data" / "processed" / "35M5CV_bbc.parquet"
ANSWER_KEY = REPO / "data" / "catalog" / "answer_key_35M5CV_bbc.csv"
RAW_SAV = REPO / "data" / "raw" / "35M5CV" / "bbc-data-raw.sav"
R_HELPER = REPO / "scripts" / "verify_35M5CV_bbc_cj.R"

# factor key (as this recipe names it) -> feature name (as the answer key,
# and cregg's formula, name it). Only `politics` differs — see
# gen_35M5CV_bbc.py trap #4: the SPSS variable stem is `politics`, but
# `answer_key_35M5CV.R`'s formula names it `party`.
FACTOR_TO_FEATURE = {
    "name": "name",
    "age": "age",
    "experience": "experience",
    "degree": "degree",
    "politics": "party",
    "eu": "eu",
    "occupation": "occupation",
}
FEATURES = list(FACTOR_TO_FEATURE.values())

EXPECTED_ROWS = 8_175
EXPECTED_RESPONDENTS = 1_635
EXPECTED_ROWS_PER_RESPONDENT = 5
EXPECTED_DISTINCT_CONDITIONS = 8_175
AMCE_TOLERANCE = 1e-6
MM_TOLERANCE = 1e-6
MM_MEAN_TOLERANCE = 0.01


def load_built() -> pd.DataFrame:
    if not PARQUET.exists():
        raise SystemExit(
            f"{PARQUET} not found — run `uv run mmds build recipes/35M5CV_bbc.yaml` first"
        )
    return pd.read_parquet(PARQUET)


def check_row_counts(df: pd.DataFrame) -> list[str]:
    bad = []
    if len(df) != EXPECTED_ROWS:
        bad.append(f"(A) rows: got {len(df)}, expected {EXPECTED_ROWS}")
    if df["participant_id"].nunique() != EXPECTED_RESPONDENTS:
        bad.append(
            f"(A) respondents: got {df['participant_id'].nunique()}, expected "
            f"{EXPECTED_RESPONDENTS}"
        )
    counts = df.groupby("participant_id").size()
    bad_counts = counts[counts != EXPECTED_ROWS_PER_RESPONDENT]
    if len(bad_counts):
        bad.append(
            f"(B) {len(bad_counts)} respondents do not have exactly "
            f"{EXPECTED_ROWS_PER_RESPONDENT} rows"
        )
    return bad


def check_condition_distinctness(df: pd.DataFrame) -> list[str]:
    bad = []
    n_cond = df["condition"].nunique()
    if n_cond != EXPECTED_DISTINCT_CONDITIONS:
        bad.append(
            f"(D) distinct condition strings: got {n_cond}, expected {EXPECTED_DISTINCT_CONDITIONS}"
        )
    tuples = df["factors"].map(lambda d: tuple(sorted(d.items())))
    if tuples.nunique() != EXPECTED_DISTINCT_CONDITIONS:
        bad.append(
            f"(D) distinct attribute tuples: got {tuples.nunique()}, expected "
            f"{EXPECTED_DISTINCT_CONDITIONS}"
        )
    return bad


def check_condition_matches_factors(df: pd.DataFrame) -> list[str]:
    """(E) Every factor value must appear verbatim in the rendered condition text."""
    bad = []
    mismatches = 0
    for _, row in df.iterrows():
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


def check_response_matches_response_num(df: pd.DataFrame) -> list[str]:
    """(G) The shipped `response` agrees with the `response_num` we verify against."""
    bad = []
    seen = df[["response", "response_num"]].drop_duplicates()
    for text, num in zip(seen["response"], seen["response_num"], strict=True):
        if float(text) != float(num):
            bad.append(f"(G) response {text!r} disagrees with response_num {num}")
    return bad


def check_name_coded_outcome_against_raw(
    df: pd.DataFrame, raw: pd.DataFrame, n: int = 500
) -> list[str]:
    """(H) Independently re-derive the response from the RAW .sav's QPAIRt and
    name_seen1/2_t{t}, bypassing this project's own recode entirely, and
    compare to what was built. This is the direct end-to-end check on the
    single highest-risk mechanism in this study (gen_35M5CV_bbc.py trap #3):
    `QPAIRt` names a PERSON, not a screen position.
    """
    bad = []
    sample = df.sample(n=min(n, len(df)), random_state=0)
    checked = 0
    for _, row in sample.iterrows():
        idx = int(row["participant_id"].split(":")[1])
        t = int(row["task_num"]) + 1
        raw_row = raw.iloc[idx]
        qpair = raw_row[f"QPAIR{t}"]
        name1 = raw_row[f"name_seen1_t{t}"]
        name2 = raw_row[f"name_seen2_t{t}"]
        if qpair == name1:
            expected = 1.0
        elif qpair == name2:
            expected = 2.0
        else:
            bad.append(
                f"(H) participant idx={idx} pair={t}: QPAIR{t}={qpair} matches neither "
                f"name_seen1 ({name1}) nor name_seen2 ({name2})"
            )
            continue
        checked += 1
        if expected != row["response_num"]:
            bad.append(
                f"(H) participant idx={idx} pair={t}: built response_num="
                f"{row['response_num']} but raw QPAIR{t} names the profile shown at "
                f"name_seen{'1' if expected == 1.0 else '2'} (expected {expected})"
            )
    if checked < n * 0.9:
        bad.append(f"(H) only matched {checked}/{len(sample)} sampled rows — test too weak")
    return bad


def reshape_to_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Mirror answer_key_35M5CV.R's reshape: one row per (respondent, pair,
    side), `chosen` = 1 for the picked side, feature columns renamed to the
    answer key's own names (party, not politics)."""
    records = []
    for _, row in df.iterrows():
        factors = row["factors"]
        resp = row["response_num"]
        for side, chosen_value in (("A", 1.0), ("B", 2.0)):
            rec = {
                "ID": row["participant_id"],
                "pair": row["condition_num"],
                "chosen": int(resp == chosen_value),
            }
            for factor_key, feature in FACTOR_TO_FEATURE.items():
                rec[feature] = factors[f"{factor_key}_{side}"]
            records.append(rec)
    return pd.DataFrame.from_records(records)


def run_cj(profile: pd.DataFrame, reference_levels: dict[str, str], tmpdir: Path) -> pd.DataFrame:
    in_csv = tmpdir / "profile.csv"
    ref_tsv = tmpdir / "reference_levels.tsv"
    out_csv = tmpdir / "cj_out.csv"
    profile.to_csv(in_csv, index=False)
    ref_tsv.write_text("".join(f"{k}\t{v}\n" for k, v in reference_levels.items()))

    result = subprocess.run(
        ["Rscript", str(R_HELPER), str(in_csv), str(ref_tsv), str(out_csv)],
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
    bad = []
    merged = ours.merge(
        key,
        on=["quantity", "feature", "level"],
        how="outer",
        suffixes=("_built", "_key"),
        indicator=True,
    )
    unmatched = merged[merged["_merge"] != "both"]
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
                f"key={row['estimate_key']:.6f} diff={row['abs_diff']:.6f}"
            )
    for _, row in mm_rows.iterrows():
        if row["abs_diff"] > MM_TOLERANCE:
            bad.append(
                f"MM {row['feature']} / {row['level']!r}: built={row['estimate_built']:.6f} "
                f"key={row['estimate_key']:.6f} diff={row['abs_diff']:.6f}"
            )
    return bad, max_amce, max_mm


def main() -> int:
    df = load_built()
    print("35M5CV (bbc) — built rows against the authors' own cregg::cj() estimator")
    print(f"\nbuilt parquet: {len(df)} rows")

    failures: list[str] = []
    failures += check_row_counts(df)
    failures += check_condition_distinctness(df)
    failures += check_condition_matches_factors(df)
    failures += check_response_matches_response_num(df)

    raw, _meta = pyreadstat.read_sav(str(RAW_SAV))
    failures += check_name_coded_outcome_against_raw(df, raw)

    print("\nreshaping to profile level (chosen indicator)...")
    profile = reshape_to_profile(df)
    expected_profile_n = 2 * len(df)
    if len(profile) != expected_profile_n:
        failures.append(f"reshape produced {len(profile)} rows, expected {expected_profile_n}")
    print(f"reshaped to {len(profile)} profile rows")

    key = pd.read_csv(ANSWER_KEY)
    reference_levels = {
        feature: key[key["feature"] == feature]["reference"].iloc[0] for feature in FEATURES
    }

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        print(f"\nrunning cregg::cj() via {R_HELPER.name}...")
        ours = run_cj(profile, reference_levels, tmpdir)

    cmp_failures, max_amce_diff, max_mm_diff = compare_estimates(ours, key)
    failures += cmp_failures

    print(f"\nlargest absolute AMCE disagreement:           {max_amce_diff:.8f}")
    print(f"largest absolute marginal-mean disagreement:  {max_mm_diff:.8f}")

    key_mm_mean = key[key["quantity"] == "mm"]["estimate"].mean()
    ours_mm_mean = ours[ours["quantity"] == "mm"]["estimate"].mean()
    print(f"\nmean of marginal means — answer key: {key_mm_mean:.6f}")
    print(f"mean of marginal means — built:      {ours_mm_mean:.6f}")
    if abs(ours_mm_mean - 0.5) > MM_MEAN_TOLERANCE:
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
        f"{(ours['quantity'] == 'mm').sum()} marginal means) agree with "
        f"answer_key_35M5CV_bbc.csv to within {AMCE_TOLERANCE}; all invariants (A)-(H) hold."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
