"""Check the built LOGVPZ rows against Green & Pahontu's own printed numbers.

LOGVPZ is not in SocSci210 (it is a UK Dataverse deposit), so
`pipeline/crosscheck.py` has nothing to compare it to and both recipes set
`comparable_to_socsci210: false`. Table D.1 and D.2 are the answer key instead,
transcribed below from the article's ONLINE SUPPLEMENTARY MATERIAL (fetched from
static.cambridge.org via the article's "Supplementary Material" DOI
https://doi.org/10.1017/S0007123423000728 — this is a separate PDF from the main
21-page article; the main text's Table 4/Figures 6-7 give the design and the
effect-size prose but not the regression table).

This reads the two BUILT PARQUETS, not the deposit — reproducing the paper from
the `.dta` would only prove the paper is reproducible; reproducing it from the
melted rows proves the condition mapping, the outcome mapping (including the
12->missing recode and, for risk tolerance, the branching derivation), the
response recode and the persona all survived the melt.

ONE DELIBERATE DIFFERENCE FROM THE PUBLISHED SAMPLE, on both experiments: both
recipes KEEP respondents the authors' own `1-master.do` drops — `anyUniW19==9999`
("Don't know") and `workingStatusW19==9` ("Other") — by blanking the affected
PERSONA FIELD rather than dropping the respondent (see each recipe's `notes`).
So the built row count is LARGER than the paper's regression N, and this script
does not expect it to match directly. Instead it applies the authors' own two
extra filters ON TOP of the built rows (persona.education present AND
persona.employment != 'Other') and asserts that reproduces their N, their
control mean and their coefficients exactly — which is the real test: it proves
our variable construction agrees with theirs, while our shipped corpus is
deliberately more complete.

Run:  uv run python scripts/verify_LOGVPZ.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
TOL = 0.001

# Table D.1 (p.10 of the supplementary PDF), transcribed in full.
TABLE_D1 = {
    "col1_coef": 0.245,
    "col2_coef": 0.191,
    "control_mean": 6.238,
    "n": 7225,
}
# Table D.2 (p.10 of the supplementary PDF), transcribed in full.
TABLE_D2 = {
    "col1_coef": -0.117,
    "col2_coef": -0.110,
    "control_mean": 2.332,
    "n": 7704,
}

# wkstat groups from `1-master.do` lines ~394-399, by the employment LABEL text
# that persona.employment carries (workingStatusW19's own value labels). Group 1
# ("working", levels 1/2/3) is the omitted reference category in Table D.1/D.2's
# column 2, matching the do-file's `i.wkstat` (Stata omits the lowest level).
WKSTAT_GROUP = {
    "Working full time (30 or more hours per week)": 1,
    "Working part time (8-29 hours a week)": 1,
    "Working part time (less than 8 hours a week)": 1,
    "Unemployed and looking for work": 2,
    "Full time university student": 3,
    "Other full time student": 3,
    "Retired": 4,
    "Not in paid work for any other reason": 5,
    # "Other" (workingStatusW19==9) deliberately has NO group here: the authors'
    # wkstat recode has no branch for it, so a row in this label is EXCLUDED by
    # authors_sample() below, same as the do-file's `drop if wkstat==.`.
}


def _persona_field(df: pd.DataFrame, field: str) -> pd.Series:
    return df["persona"].map(lambda p: json.loads(p).get(field))


def authors_sample(df: pd.DataFrame) -> pd.DataFrame:
    """Replicate the authors' two extra drops on top of our built rows.

    `anyUniW19==9999` -> our `education` field is blanked (None): exclude.
    `workingStatusW19==9` ("Other") -> kept as a real label in our persona,
    not blanked, but it has no `WKSTAT_GROUP` entry: exclude here, matching
    `drop if wkstat==.` in the do-file.
    """
    out = df.copy()
    out["education"] = _persona_field(out, "education")
    out["employment"] = _persona_field(out, "employment")
    out["wkstat"] = out["employment"].map(WKSTAT_GROUP)
    out["gender_p"] = _persona_field(out, "gender")
    out["age_p"] = _persona_field(out, "age")
    return out[out["education"].notna() & out["wkstat"].notna()].copy()


def ols_coef(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    x1 = np.column_stack([np.ones(len(x)), x])
    beta, *_ = np.linalg.lstsq(x1, y.astype(float), rcond=None)
    return np.asarray(beta)


def check_table(
    name: str, df: pd.DataFrame, treat_col: str, response_col: str, table: dict[str, float]
) -> bool:
    sample = authors_sample(df)
    ok = True

    n = len(sample)
    if n != table["n"]:
        print(f"  FAIL N: built {n}, paper {table['n']}")
        ok = False
    else:
        print(f"  OK   N = {n}")

    control = sample.loc[sample[treat_col] == 0, response_col]
    cmean = control.mean()
    if abs(cmean - table["control_mean"]) > TOL:
        print(f"  FAIL control mean: built {cmean:.4f}, paper {table['control_mean']}")
        ok = False
    else:
        print(f"  OK   control mean = {cmean:.4f} (paper {table['control_mean']})")

    beta1 = ols_coef(sample[response_col].to_numpy(), sample[treat_col].to_numpy())
    c1 = beta1[1]
    if abs(c1 - table["col1_coef"]) > TOL:
        print(f"  FAIL col1 coef: built {c1:.4f}, paper {table['col1_coef']}")
        ok = False
    else:
        print(f"  OK   col1 (bivariate) coef = {c1:.4f} (paper {table['col1_coef']})")

    female = (sample["gender_p"] == "Female").astype(float)
    age = sample["age_p"].astype(float)
    uni_dummies = pd.get_dummies(sample["education"], prefix="uni", drop_first=False).astype(float)
    # Drop the reference category (anyUniW19==0, "No, I have never attended
    # higher education") to match Table D.1/D.2's omitted base.
    ref_col = "uni_No, I have never attended higher education"
    uni_dummies = uni_dummies.drop(columns=[ref_col], errors="ignore")
    wk_dummies = pd.get_dummies(sample["wkstat"].astype(int), prefix="wk", drop_first=True).astype(
        float
    )

    x = pd.concat(
        [
            sample[[treat_col]].astype(float),
            female.rename("female"),
            age.rename("age"),
            uni_dummies,
            wk_dummies,
        ],
        axis=1,
    )
    beta2 = ols_coef(sample[response_col].to_numpy(), x.to_numpy())
    c2 = beta2[1]
    if abs(c2 - table["col2_coef"]) > TOL:
        print(f"  FAIL col2 (+controls) coef: built {c2:.4f}, paper {table['col2_coef']}")
        ok = False
    else:
        print(f"  OK   col2 (+controls) coef = {c2:.4f} (paper {table['col2_coef']})")

    print(f"  => {name}: {'PASS' if ok else 'FAIL'}")
    return ok


def main() -> int:
    d1 = pd.read_parquet(REPO / "data" / "processed" / "LOGVPZ_brexit_satisfaction.parquet")
    d2 = pd.read_parquet(REPO / "data" / "processed" / "LOGVPZ_risk_tolerance.parquet")

    print("Table D.1 — Wealth Increases Brexit Support (Survey Experiment)")
    ok1 = check_table("Table D.1", d1, "condition_num", "response_num", TABLE_D1)

    print()
    print("Table D.2 — Effect of Wealth Treatment on Risk Aversion")
    ok2 = check_table("Table D.2", d2, "condition_num", "response_num", TABLE_D2)

    print()
    overall = ok1 and ok2
    print(f"OVERALL: {'PASS' if overall else 'FAIL'}")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
