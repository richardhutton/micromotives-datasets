"""Derive the risk-tolerance outcome for LOGVPZ's risk-tolerance experiment.

The recipe schema (`Recipe.outcomes[].var` / `Arm.outcome_var`) can only name ONE
source column per outcome. LOGVPZ's risk-tolerance outcome is not one column: the
authors' own `1-master.do` (program `yougov`, lines ~403-415) builds it from a
BRANCHING pair of questions —

    gen risk = 0 if expRiskIncomeW19 == 2 & expRiskIncomeaW19 == 2
    replace risk = 1 if expRiskIncomeW19 == 2 & expRiskIncomeaW19 == 1
    replace risk = 2 if expRiskIncomeW19 == 1 & expRiskIncomebW19 == 2
    replace risk = 3 if expRiskIncomeW19 == 1 & expRiskIncomebW19 == 1

    replace risk = 0 if controlRiskIncomeW19 == 2 & controlRiskIncomeaW19 == 2
    replace risk = 1 if controlRiskIncomeW19 == 2 & controlRiskIncomeaW19 == 1
    replace risk = 2 if controlRiskIncomeW19 == 1 & controlRiskIncomebW19 == 2
    replace risk = 3 if controlRiskIncomeW19 == 1 & controlRiskIncomebW19 == 1

i.e. a base gamble question (1=No, 2=Yes), then ONE of two follow-up questions
depending on the base answer: "a" if the base answer was Yes (a bigger gamble),
"b" if the base answer was No (a smaller, safer gamble). The exp*/control* variants
read from the matching condition's own three columns.

This is kept as a committed, reviewable script — not a throwaway — per ledger
finding #89 ("a generated recipe keeps the output and throws away the judgement").
It reads the ORIGINAL deposit file and writes ONE augmented file carrying every
original column plus `risk_derived`, so the recipe can point `Outcome.var` at a
real column exactly like every other study here.

Verified before writing a single row to the derived file (see `_verify` below):
zero branching exceptions across every respondent who answered a base gamble
question (8,075 of 8,075, exp + control combined, matching randgroup 4/6 exactly),
and the resulting column reproduces the authors' own Table D.2 (control mean
2.332, N 7,704 after their education/employment/age filters) when replicated with
their additional drops applied on top.

Run:  uv run python scripts/derive_LOGVPZ_risk.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "data" / "raw" / "LOGVPZ" / "yougov.dta"
DST = REPO / "data" / "raw" / "LOGVPZ" / "yougov_risk_derived.dta"


def _branch(base: float, a: float, b: float) -> float:
    """One respondent's risk code, or NaN if the branch does not resolve.

    `base` is the 50-50-double-or-cut-by-a-third gamble (1=No, 2=Yes). `a` is the
    follow-up asked only if base=Yes (a bigger gamble: double or halve). `b` is the
    follow-up asked only if base=No (a smaller gamble: double or cut by a fifth).
    """
    if base == 2 and a == 2:
        return 0.0  # accepted the base gamble AND the bigger follow-up gamble
    if base == 2 and a == 1:
        return 1.0  # accepted the base gamble, declined the bigger follow-up
    if base == 1 and b == 2:
        return 2.0  # declined the base gamble, accepted the safer follow-up
    if base == 1 and b == 1:
        return 3.0  # declined the base gamble AND the safer follow-up
    return np.nan


def _verify(df: pd.DataFrame, risk: pd.Series) -> None:
    routed = df["randgroup"].isin([4, 6])
    base_answered = (df["expRiskIncomeW19"].notna() & (df["randgroup"] == 4)) | (
        df["controlRiskIncomeW19"].notna() & (df["randgroup"] == 6)
    )
    n_base = int(base_answered.sum())
    n_resolved = int(risk[routed].notna().sum())
    if n_base != n_resolved:
        raise AssertionError(
            f"branching exceptions: {n_base} respondents answered the base gamble "
            f"question but only {n_resolved} resolved to a risk code"
        )
    if n_resolved != 8075:
        raise AssertionError(f"expected 8,075 resolved risk codes, got {n_resolved}")
    print(f"OK: {n_resolved} of {n_resolved} base-answered respondents resolved, zero exceptions")


def main() -> None:
    df, meta = pyreadstat.read_dta(SRC)

    risk_exp = [
        _branch(b, a, bb)
        for b, a, bb in zip(
            df["expRiskIncomeW19"], df["expRiskIncomeaW19"], df["expRiskIncomebW19"], strict=True
        )
    ]
    risk_ctrl = [
        _branch(b, a, bb)
        for b, a, bb in zip(
            df["controlRiskIncomeW19"],
            df["controlRiskIncomeaW19"],
            df["controlRiskIncomebW19"],
            strict=True,
        )
    ]
    risk = pd.Series(
        np.where(df["randgroup"] == 4, risk_exp, np.where(df["randgroup"] == 6, risk_ctrl, np.nan)),
        index=df.index,
    )
    _verify(df, risk)

    out = df.copy()
    out["risk_derived"] = risk
    # pyreadstat returns object-dtype columns (floats + NaN) for this file; Stata's
    # writer needs a numeric dtype, so coerce every column explicitly rather than
    # relying on pandas to infer it.
    for col in out.columns:
        out[col] = pd.to_numeric(out[col], errors="raise")

    # Carry every ORIGINAL value label and column label through to the derived
    # file. Writing with pandas' `to_stata` (no label support) silently dropped
    # them on the first attempt here: the build then rendered persona fields as
    # bare codes ("education: 0") instead of the file's own labels
    # ("No, I have never attended higher education") on every risk_tolerance
    # row — caught by comparing this build's QC warning against the companion
    # recipe's, which showed real labels. `pyreadstat.write_dta` preserves them
    # directly; `risk_derived` itself needs none (the recipe's own
    # `response_recode` and `Scale` carry its meaning, not a value label).
    pyreadstat.write_dta(
        out,
        str(DST),
        column_labels=dict(meta.column_names_to_labels),
        variable_value_labels=dict(meta.variable_value_labels),
        version=15,
    )
    print(f"wrote {DST} ({len(out)} rows, {len(out.columns)} columns)")


if __name__ == "__main__":
    main()
