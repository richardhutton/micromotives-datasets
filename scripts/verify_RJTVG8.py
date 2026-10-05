"""Check the built RJTVG8 rows against the authors' own published marginal means.

RJTVG8 is the UK i-voting forced-choice conjoint (Turnbull-Dugarte & Devine,
Electoral Studies 86 (2023)). The deposit's own `replication_electoralstudies.R`
computes Figure 2/3 and Table A.4 ("Marginal means: proposal selected", the
author-accepted manuscript, p.xvii) with:

    mm1 <- mm(df, selected ~ prereg + method + vwindow + trials + pilot +
                fraud + cost + platform + private + party + endorse,
              id = ~IDvar, h0 = 0.5)

— `cregg::mm()`, on the SPLIT platform(3-level)/private(2-level)
representation the authors use for their own headline OLS too (not only for
plotting). Table A.4 prints 51 point estimates to 3dp (one per level of all
11 terms in that formula). This is the numeric answer key: re-derived here by
re-running the IDENTICAL formula over profile-level data reshaped from the
BUILT PARQUET, never the raw deposit, so agreement proves the melt rather than
merely proving the paper is reproducible (docs/CONVENTIONS.md, "Verifying a
study SocSci210 does not contain").

THE TRANSLATION STEP, AND WHY IT EXISTS
-----------------------------------------
This recipe renders `platform_num` as ONE 6-level attribute (the brief's
riskiest judgement — see recipes/RJTVG8.yaml's notes) and every attribute's
TEXT verbatim from the .dta's own value labels (including two genuine typos:
"smarphone", "...IT form"). Table A.4, and the `mm()` call that produced it,
both use the AUTHORS' OWN R `factor()` labels — the SPLIT platform/private
representation, correctly-spelled "smartphone", "USA" not "US", and in one
case their OWN typo ("particiaption" on two pilot levels) that is independent
of any typo in the data. None of this is a disagreement about the DESIGN —
`test_platform_num_is_a_bijection_of_platform_and_private`
(tests/test_gen_RJTVG8.py) already proves platform_num IS platform+private,
losslessly — it is simply two different vocabularies for the SAME 11
attributes. `_OUR_TEXT_TO_AUTHOR_LABEL` below is the declared, independent
translation (re-derived from `replication_electoralstudies.R`'s own
`factor(..., labels = ...)` calls and from the deposit's own
`platform`/`private` crosstab against `platform_num`, NOT imported from
`scripts/gen_RJTVG8.py`'s `ATTR_LEVELS` — so a wrong label in the generator
cannot hide behind an identical wrong label here, the same discipline
`verify_PMV0TG.py` uses for its reference levels).

Besides the 51 point estimates, four more invariants are checked:
  (A) exact row counts (6,000 pair-level, 12,000 profile-level, 1,200
      respondents, 5 rows each);
  (B) `condition` and `factors` agree on every row (every factor value
      appears verbatim in the rendered text);
  (C) the reshaped `chosen` indicator splits exactly 6,000/6,000;
  (D) the translation step is TOTAL — every value found in `factors` has an
      entry in `_OUR_TEXT_TO_AUTHOR_LABEL`, so a silently-unmapped level
      cannot fail to raise.

Run:  uv run python scripts/verify_RJTVG8.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
PARQUET = REPO / "data" / "processed" / "RJTVG8.parquet"
R_HELPER = REPO / "scripts" / "verify_RJTVG8_cj.R"

EXPECTED_PAIR_ROWS = 6_000
EXPECTED_PROFILE_ROWS = 12_000
EXPECTED_RESPONDENTS = 1_200
EXPECTED_ROWS_PER_RESPONDENT = 5
MM_TOLERANCE = 0.0015  # Table A.4 prints 3dp; mm() is also not perfectly
# deterministic in floating point across R/platform versions at the last digit

ATTRS_OURS = [
    "prereg",
    "method",
    "vwindow",
    "trials",
    "pilot",
    "fraud",
    "platform",
    "cost",
    "party",
    "endorse",
]
ATTRS_FOR_MM = [
    "prereg",
    "method",
    "vwindow",
    "trials",
    "pilot",
    "fraud",
    "cost",
    "platform",
    "private",
    "party",
    "endorse",
]

# Our verbatim text (as rendered, from the .dta's own value labels) ->
# the authors' own R `factor()` label (`replication_electoralstudies.R`,
# the `df$<attr> <- factor(..., labels = c(...))` calls). Declared
# independently of scripts/gen_RJTVG8.py.
_OUR_TEXT_TO_AUTHOR_LABEL: dict[str, dict[str, str]] = {
    "prereg": {
        "Automatically pre-registered": "Automatically pre-registered",
        "Must opt-in by post": "Must opt-in by post",
        "Must opt-in online": "Must opt-in online",
    },
    "method": {
        "Vote via website": "Vote via website",
        "Vote via SMS (text)": "Vote via SMS",
        "Vote via smarphone app": "Vote via smartphone app",  # data's own typo
        "Vote via telephone call": "Vote via telephone call",
    },
    "vwindow": {
        "available for two weeks up to (and including) polling day": (
            "Available for two weeks up to\n(and including) polling day"
        ),
        "available for up to two weeks before polling day": (
            "Available for up to two weeks\nbefore polling day"
        ),
        "available on polling day only": "Available on polling day only",
    },
    "trials": {
        "None": "No trials",
        "Estonia": "Estonia",
        "US": "USA",  # data's "US" == the paper's own "USA" factor label
        "Germany": "Germany",
        "Switzerland": "Switzerland",
        "Argentina": "Argentina",
        "Mozambique": "Mozambique",
    },
    "pilot": {
        "None": "No change",
        "Increases overall participation": "Increases overall participation",
        "Decreases overall participation": "Decreases overall participation",
        "Increases participation among young": "Increases particiaption among young",  # R's own typo
        "Decreases participation among young": "Decreases particiaption among young",  # R's own typo
        "Increases participation among elderly": "Increases participation among elderly",
        "Decreases participation among elderly": "Decreases participation among elderly",
        "Increases participation in socially deprived areas": (
            "Increases participation in socially deprived areas"
        ),
        "Decreases participation in socially deprived areas": (
            "Decreases participation in socially deprived areas"
        ),
    },
    "fraud": {
        "None": "None",
        "Reduces risk of electoral fraud": "Decreases risk of fraud",
        "Increases risk of electoral fraud": "Increase risk of fraud",
    },
    "cost": {
        "£0 (none)": "£0 (none)",
        "-£0.50 (50p less)": "-£0.50 (50p less)",
        "-£1 (one pound less)": "-£1 (one pound less)",
        "-£5 (five pounds less)": "-£5 (five pounds less)",
        "£0.50 (50p more)": "£0.50 (50p more)",
        "£1 (one pound more)": "£1 (one pound more)",
        "£5 (five pounds more)": "£5 (five pounds more)",
    },
    "party": {
        "Cross-party coalition": "Cross-party support",
        "Conservatives": "Conservatives",
        "Labour": "Labour",
        "Liberal Democrats": "Lib Dems",
        "the Greens": "Greens",
    },
    "endorse": {
        "None": "No endorsement",
        "UK Electoral Commission": "UK Electoral Commission",
        "United Nations Electoral Assistance Division (UN)": "United Nations (UN)",
        "UK Electoral Reform Society": "UK Electoral Reform Society",
        "European Union (EU)": "European Union",
    },
}

# `platform_num`'s six verbatim combined texts -> (3-level platform label,
# 2-level private label), independently re-derived from the deposit's own
# `platform`/`private` crosstab against `platform_num` (not imported from the
# generator). This is what makes the brief's riskiest judgement an EXERCISED
# claim, not merely an asserted one: if the bijection were wrong, this
# translation would misassign rows and the mm() comparison below would fail.
_PLATFORM_SPLIT: dict[str, tuple[str, str]] = {
    "Central government": ("Central government", "No private IT involvement"),
    "Central government & private sector IT form": (
        "Central government",
        "Private sector IT involvement",
    ),
    "Local council": ("Local council", "No private IT involvement"),
    "Local council & central government": (
        "Local council & central government",
        "No private IT involvement",
    ),
    "Local council & private sector IT firm": ("Local council", "Private sector IT involvement"),
    "Local council, central government & private sector IT firm": (
        "Local council & central government",
        "Private sector IT involvement",
    ),
}

# Table A.4 ("Marginal means: proposal selected", author-accepted manuscript
# p.xvii), transcribed as data, keyed by the AUTHORS' OWN R factor labels
# (matching exactly what mm()'s own "level" column will print, since the
# table was generated from this same call). feature -> {level: estimate}.
TABLE_A4: dict[str, dict[str, float]] = {
    "prereg": {
        "Automatically pre-registered": 0.536,
        "Must opt-in by post": 0.463,
        "Must opt-in online": 0.501,
    },
    "method": {
        "Vote via website": 0.555,
        "Vote via SMS": 0.506,
        "Vote via smartphone app": 0.519,
        "Vote via telephone call": 0.419,
    },
    "vwindow": {
        "Available for two weeks up to\n(and including) polling day": 0.515,
        "Available for up to two weeks\nbefore polling day": 0.507,
        "Available on polling day only": 0.478,
    },
    "trials": {
        "No trials": 0.464,
        "Argentina": 0.490,
        "Estonia": 0.501,
        "Germany": 0.545,
        "Mozambique": 0.442,
        "Switzerland": 0.542,
        "USA": 0.518,
    },
    "pilot": {
        "No change": 0.498,
        "Increases overall participation": 0.581,
        "Decreases overall participation": 0.452,
        "Increases particiaption among young": 0.550,
        "Decreases particiaption among young": 0.434,
        "Increases participation among elderly": 0.552,
        "Decreases participation among elderly": 0.465,
        "Increases participation in socially deprived areas": 0.588,
        "Decreases participation in socially deprived areas": 0.395,
    },
    "fraud": {
        "None": 0.521,
        "Decreases risk of fraud": 0.614,
        "Increase risk of fraud": 0.362,
    },
    "cost": {
        "£0 (none)": 0.556,
        "-£0.50 (50p less)": 0.543,
        "-£1 (one pound less)": 0.531,
        "-£5 (five pounds less)": 0.529,
        "£0.50 (50p more)": 0.488,
        "£1 (one pound more)": 0.475,
        "£5 (five pounds more)": 0.382,
    },
    "platform": {
        "Local council": 0.492,
        "Central government": 0.499,
        "Local council & central government": 0.509,
    },
    "private": {
        "No private IT involvement": 0.502,
        "Private sector IT involvement": 0.498,
    },
    "party": {
        "Cross-party support": 0.538,
        "Conservatives": 0.475,
        "Labour": 0.503,
        "Lib Dems": 0.503,
        "Greens": 0.482,
    },
    "endorse": {
        "No endorsement": 0.463,
        "European Union": 0.496,
        "UK Electoral Commission": 0.519,
        "UK Electoral Reform Society": 0.511,
        "United Nations (UN)": 0.512,
    },
}


def load_built() -> pd.DataFrame:
    if not PARQUET.exists():
        raise SystemExit(f"{PARQUET} not found — run `uv run mmds build recipes/RJTVG8.yaml` first")
    return pd.read_parquet(PARQUET)


def check_row_counts(df: pd.DataFrame) -> list[str]:
    bad = []
    if len(df) != EXPECTED_PAIR_ROWS:
        bad.append(f"(A) pair-level rows: got {len(df)}, expected {EXPECTED_PAIR_ROWS}")
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
    if sorted(df["task_num"].unique()) != list(range(5)):
        bad.append(f"(A) task_num values are not exactly 0..4: {sorted(df['task_num'].unique())}")
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
                        f"(B) condition_num={row['condition_num']}: factor {key}={value!r} "
                        "not found verbatim in rendered condition text"
                    )
    if mismatches > 5:
        bad.append(f"(B) ... and {mismatches - 5} more such mismatches")
    return bad


def _translate(attr: str, our_text: str) -> str:
    try:
        return _OUR_TEXT_TO_AUTHOR_LABEL[attr][our_text]
    except KeyError:
        raise ValueError(
            f"(D) no translation declared for {attr}={our_text!r} — "
            "_OUR_TEXT_TO_AUTHOR_LABEL is not total"
        ) from None


def reshape_to_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Mirror the deposit's own profile-row structure: one row per
    (respondent, task, side), `chosen` = 1 for the side `response_num` names.
    `platform_A`/`platform_B` (our single 6-level attribute) is split into
    the authors' own `platform`(3)/`private`(2) pair via `_PLATFORM_SPLIT` —
    the same bijection `test_platform_num_is_a_bijection_of_platform_and_private`
    verifies against the raw deposit.
    """
    records = []
    for _, row in df.iterrows():
        factors = row["factors"]
        resp = row["response_num"]
        for side, chosen_value in (("A", 1.0), ("B", 2.0)):
            rec = {
                "IDvar": row["participant_id"],
                "task": row["condition_num"],
                "chosen": int(resp == chosen_value),
            }
            for attr in ATTRS_OURS:
                our_text = factors[f"{attr}_{side}"]
                if attr == "platform":
                    platform_label, private_label = _PLATFORM_SPLIT[our_text]
                    rec["platform"] = platform_label
                    rec["private"] = private_label
                else:
                    rec[attr] = _translate(attr, our_text)
            records.append(rec)
    return pd.DataFrame.from_records(records)


def run_mm(profile: pd.DataFrame, tmpdir: Path) -> pd.DataFrame:
    in_csv = tmpdir / "profile.csv"
    out_csv = tmpdir / "mm_out.csv"
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

    # `keep_default_na=False`: pandas' default NA-string list includes the
    # literal word "None", which is a genuine fraud-attribute level here
    # ("Pilot outcome on integrity: None"), not a missing marker — without
    # this, `fraud`'s baseline level silently became NaN on read-back.
    return pd.read_csv(out_csv, keep_default_na=False)


def compare_estimates(ours: pd.DataFrame) -> tuple[list[str], float]:
    bad: list[str] = []
    max_diff = 0.0
    seen: set[tuple[str, str]] = set()
    for _, row in ours.iterrows():
        feature, level, estimate = row["feature"], row["level"], row["estimate"]
        published = TABLE_A4.get(feature, {}).get(level)
        if published is None:
            bad.append(f"no Table A.4 entry for feature={feature!r} level={level!r}")
            continue
        seen.add((feature, level))
        diff = abs(float(estimate) - published)
        max_diff = max(max_diff, diff)
        if diff > MM_TOLERANCE:
            bad.append(
                f"{feature}/{level!r}: built={estimate:.4f} published={published:.3f} "
                f"diff={diff:.4f} (tolerance {MM_TOLERANCE})"
            )
    expected = {(f, lvl) for f, levels in TABLE_A4.items() for lvl in levels}
    missing = expected - seen
    if missing:
        bad.append(f"mm() output is missing {len(missing)} published level(s): {sorted(missing)[:5]}")
    return bad, max_diff


def main() -> int:
    df = load_built()
    print("RJTVG8 — built rows against the authors' own cregg::mm() marginal means (Table A.4)")
    print(f"\nbuilt parquet: {len(df)} rows")

    failures: list[str] = []
    failures += check_row_counts(df)
    failures += check_condition_matches_factors(df)

    try:
        profile = reshape_to_profile(df)
    except ValueError as exc:
        print(f"\nFAILED during reshape: {exc}")
        return 1

    print(f"reshaped to {len(profile)} profile rows (2 per task)")
    if len(profile) != EXPECTED_PROFILE_ROWS:
        failures.append(
            f"(B) reshape produced {len(profile)} profile rows, expected {EXPECTED_PROFILE_ROWS}"
        )
    chosen_counts = profile["chosen"].value_counts().to_dict()
    expected_split = {1: EXPECTED_PAIR_ROWS, 0: EXPECTED_PAIR_ROWS}
    if chosen_counts != expected_split:
        failures.append(f"(C) chosen split {chosen_counts}, expected {expected_split}")

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        print(f"\nrunning cregg::mm() via {R_HELPER.name}...")
        ours = run_mm(profile, tmpdir)

    cmp_failures, max_diff = compare_estimates(ours)
    failures += cmp_failures
    print(f"\nlargest absolute marginal-mean disagreement: {max_diff:.5f}")

    if failures:
        print("\nFAILED:")
        for line in failures:
            print(f"  {line}")
        return 1

    n_published = sum(len(v) for v in TABLE_A4.values())
    print(
        f"\nVERIFIED — {n_published} marginal means agree with Table A.4 "
        f"(author-accepted manuscript, p.xvii) to within {MM_TOLERANCE}; invariants (A)-(D) hold."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
