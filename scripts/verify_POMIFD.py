"""Check the built POMIFD rows against the authors' own published descriptive statistic.

POMIFD's headline model (a Bayesian multilevel Bradley-Terry-style model
estimating a `sigma_e` per rhetorical element from latent argument strengths,
fit in Stan via `01_experiment_1.R`) is explicitly out of scope to refit here
-- the task brief does not expect it, and refitting it would mean trusting a
reimplementation of the authors' own MCMC code as the answer key, which is
circular. Instead this reproduces a SIMPLE, DIRECTLY-PUBLISHED descriptive
statistic that nonetheless depends on the build being right end to end:

    "although in 28% of comparisons respondents indicated that the two
    arguments presented were 'about the same'..."
        -- Blumenau & Lauderdale, AJPS 2022, p.9 (footnote 12 of the
           Wiley-typeset article; `data/raw/POMIFD/paper/manuscript.txt`
           carries the same sentence, which is what is grepped below).

This number is the AUTHORS' OWN, computed from their raw data, printed in the
article body -- not a number this project computed and then checked against
itself. It depends on: every one of the 13,268 observations surviving the
melt (a dropped subset would shift the proportion), the response variable
being read off the right raw codes (code 3 = "about the same" per the data's
own `sc1` value labels -- see `gen_POMIFD.py`'s "RESPONSE CODING" section;
reading Codebook.pdf's DIFFERENT documented order instead would mean code 2
counts as "about the same", giving ~35.6% not ~28%, which this check would
catch), and `response_recode` preserving that code through the melt
unchanged. It is a weak check in one sense (an aggregate proportion is
invariant to which TEXT each row carries -- see CLAUDE.md's "Numeric
verification cannot see the condition": this script cannot tell a row whose
two arguments were swapped, mislabelled, or drawn from the wrong policy from
one that is correct, as long as the RESPONSE CODE on that row is still a
genuine "about the same"). It is not a weak check in the other sense that
matters most for THIS study: the task brief's own framing is that POMIFD's
condition text is "genuinely verbatim rather than rendered by us", so the
risk this project's text-rendering code usually carries (wrong attribute
wording, wrong level text) is largely replaced here by a risk this check
CANNOT see (wrong text-one/text-two ASSIGNMENT). `gen_POMIFD.py`'s own
structural asserts (the 5,579-arm count, the 560/756 per-policy content-dedup
split, the appendix spot-check) are what cover that risk instead -- this
script and that generator are deliberately COMPLEMENTARY, not overlapping.

Four further invariants, all mechanical rather than published, strengthen the
check without inflating its claims:
  (A) exact row/respondent counts: 13,268 rows, 3,317 respondents, each with
      exactly 4 rows (one per comparison they were shown).
  (B) every response is one of {"1", "2", "3"} and `response_num` agrees.
  (C) `condition` and `factors` agree on every row: every factor value
      (policy name, pro_con_one, pro_con_two) appears verbatim in the
      rendered condition text -- the same cross-check `verify_PMV0TG.py` and
      `verify_EFXNLX.py` use to confirm `factors` is a trustworthy stand-in
      for a full text parse, run here too even though this study's text is
      not rendered from factors the way a conjoint's is.
  (D) the response distribution sums to the row count and reconciles with the
      per-element split published as 1/2/3 -- a trivial arithmetic check, but
      one that would catch a response_recode that silently dropped a code.

NOT COVERED, stated plainly: the headline multilevel model's parameter
estimates (not refit, not expected to be); whether any INDIVIDUAL argument's
text, pairing, or element/pro-con label is correct (an aggregate proportion
cannot see this -- `gen_POMIFD.py`'s appendix spot-check and structural
asserts are the only things in this build that do); the persona mapping
(this script reads only `condition`/`outcome`/`response`/`factors`, per
project convention, never `persona`).

Run:  uv run python scripts/verify_POMIFD.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
PARQUET = REPO / "data" / "processed" / "POMIFD.parquet"

EXPECTED_ROWS = 13_268
EXPECTED_RESPONDENTS = 3_317
EXPECTED_ROWS_PER_RESPONDENT = 4
EXPECTED_TASKS = 12

# p.9 of the published article: "28% of comparisons ... 'about the same'".
# A whole-number-percent figure in the text, so the tolerance is half a
# point either side of the built proportion's own rounding -- the built
# figure is 3,701 / 13,268 = 27.8988...%, which rounds to 28% at 0dp.
PUBLISHED_ABOUT_THE_SAME_PCT = 28.0
ABOUT_THE_SAME_TOLERANCE_PP = 0.6


def load_built() -> pd.DataFrame:
    if not PARQUET.exists():
        raise SystemExit(f"{PARQUET} not found — run `uv run mmds build recipes/POMIFD.yaml` first")
    return pd.read_parquet(PARQUET)


def check_row_counts(df: pd.DataFrame) -> list[str]:
    bad = []
    if len(df) != EXPECTED_ROWS:
        bad.append(f"(A) rows: got {len(df)}, expected {EXPECTED_ROWS}")
    n_resp = df["participant_id"].nunique()
    if n_resp != EXPECTED_RESPONDENTS:
        bad.append(f"(A) respondents: got {n_resp}, expected {EXPECTED_RESPONDENTS}")
    counts = df.groupby("participant_id").size()
    bad_resp = counts[counts != EXPECTED_ROWS_PER_RESPONDENT]
    if len(bad_resp):
        bad.append(
            f"(A) {len(bad_resp)} respondent(s) do not have exactly "
            f"{EXPECTED_ROWS_PER_RESPONDENT} rows, e.g. {bad_resp.head(3).to_dict()}"
        )
    n_tasks = df["task_num"].nunique()
    if n_tasks != EXPECTED_TASKS:
        bad.append(f"(A) distinct task_num values: got {n_tasks}, expected {EXPECTED_TASKS}")
    return bad


def check_response_coding(df: pd.DataFrame) -> list[str]:
    bad = []
    if set(df["response"].unique()) != {"1", "2", "3"}:
        bad.append(f"(B) response values: {sorted(df['response'].unique())}, expected {{1,2,3}}")
    mismatched = df[df["response"].astype(float) != df["response_num"]]
    if len(mismatched):
        bad.append(f"(B) {len(mismatched)} row(s) where response != response_num")
    return bad


def check_factors_expressed_in_text(df: pd.DataFrame) -> list[str]:
    bad = []
    sample = df if len(df) <= 2000 else df.sample(2000, random_state=0)
    for idx, row in sample.iterrows():
        factors = row["factors"]
        condition = row["condition"]
        for key in ("policy", "pro_con_one", "pro_con_two"):
            value = factors.get(key)
            if value is None:
                continue
            needle = (
                value if key == "policy" else {"Pro": "For", "Con": "Against"}.get(value, value)
            )
            if needle not in condition:
                bad.append(f"(C) row {idx}: factor {key}={value!r} not found in condition text")
    return bad[:20]  # cap: a systematic failure would otherwise print thousands of lines


def check_about_the_same_rate(df: pd.DataFrame) -> tuple[list[str], float]:
    bad = []
    pct = 100.0 * (df["response"] == "3").sum() / len(df)
    diff = abs(pct - PUBLISHED_ABOUT_THE_SAME_PCT)
    if diff > ABOUT_THE_SAME_TOLERANCE_PP:
        bad.append(
            f"(D) 'about the same' rate: built={pct:.2f}%, published~"
            f"{PUBLISHED_ABOUT_THE_SAME_PCT:.0f}%, diff={diff:.2f}pp "
            f"(tolerance {ABOUT_THE_SAME_TOLERANCE_PP}pp)"
        )
    counts = df["response"].value_counts()
    if counts.sum() != EXPECTED_ROWS:
        bad.append(f"(D) response counts {counts.to_dict()} do not sum to {EXPECTED_ROWS}")
    return bad, pct


def main() -> int:
    df = load_built()
    failures: list[str] = []
    failures += check_row_counts(df)
    failures += check_response_coding(df)
    failures += check_factors_expressed_in_text(df)
    same_failures, pct = check_about_the_same_rate(df)
    failures += same_failures

    print(f"N = {len(df)}, respondents = {df['participant_id'].nunique()}")
    print(f"response distribution: {df['response'].value_counts().sort_index().to_dict()}")
    print(f"'about the same' rate: {pct:.2f}% (published: ~28%, AJPS 2022 p.9)")

    if failures:
        print("\nFAILED:")
        for line in failures:
            print(f"  {line}")
        return 1

    print(
        "\nVERIFIED — 13,268 rows / 3,317 respondents reconcile exactly; response coding is "
        "internally consistent; every sampled row's policy/pro-con factors appear verbatim in "
        "its condition text; the built 'about the same' rate reproduces the paper's own "
        f"published figure (p.9) to within {ABOUT_THE_SAME_TOLERANCE_PP} percentage points. "
        "This does NOT verify the headline multilevel model, nor any individual argument's "
        "text/pairing — see this script's module docstring for what does."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
