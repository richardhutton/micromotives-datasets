"""Check the built zenodo10641548 rows against the paper's published model (ESM S6).

Hare et al., "Public perceptions of trophy hunting are pragmatic, not dogmatic",
Proc. R. Soc. B 291 (2024) 20231638. The paper reports no UK-only estimates: its
top-supported model (ESM S6, ordinal logistic regression, 1,192 respondents) is
fitted on all three countries, with country as a main effect. So the check is that
model, refitted with the UK half of its data taken from the BUILT PARQUET, never the
deposit: each UK respondent's response and three experimental factors are read from
the row we wrote, and only the covariates we do not build (country, education,
hunter and animal-protection identity, people-or-animals priority) and the USA and
South African respondents come from the deposit. Agreement with S6's coefficients,
to their two printed decimals, says the UK responses and arm assignment survived the
melt. Country UK (-0.61 against South Africa) is the paper's headline UK result.

It says nothing about the condition TEXT, which tests/test_gen_zenodo10641548.py
checks against ESM S3 directly.

    uv run python scripts/verify_zenodo10641548.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DEPOSIT = REPO / "data" / "raw" / "zenodo10641548" / "final.data.csv"
BUILT = REPO / "data" / "processed" / "zenodo10641548.parquet"
R_HELPER = REPO / "scripts" / "verify_zenodo10641548_polr.R"

# Our factor slugs -> the deposit's labels. Typed here, not imported from the
# generator, so a wrong slug there cannot hide behind the same slug here.
ANIMAL = {"elephant": "Elephant", "zebra": "Zebra"}
MEAT = {"wildlife": "Wildlife", "people": "People"}
REVENUE = {"conservation": "Conservation", "development": "Development", "hunting": "Hunting"}

DK = "I don’t know"
# ESM S6 (pp. 27-28), polr's term names. Thresholds: zeta_k, "k|k+1".
S6 = {
    "countryUK": -0.61,
    "countryUSA": 0.22,
    "animalZebra": 0.23,
    "meatPeople": 0.49,
    "revenueDevelopment": -0.19,
    "revenueHunting": -0.43,
    "educationSecondary or high school": 0.58,
    "educationCollege or university degree": 0.65,
    "educationPostgraduate degree": 0.98,
    "hunterDisagree": 1.13,
    "hunterSomewhat disagree": 1.08,
    "hunterNeither agree nor disagree": 1.40,
    "hunterSomewhat agree": 2.03,
    "hunterAgree": 2.66,
    "hunterStrongly agree": 2.75,
    f"hunter{DK}": -0.58,
    "animal.protectionistDisagree": 2.53,
    "animal.protectionistSomewhat disagree": 1.36,
    "animal.protectionistNeither agree nor disagree": 1.07,
    "animal.protectionistSomewhat agree": 1.19,
    "animal.protectionistAgree": 0.83,
    "animal.protectionistStrongly agree": 0.64,
    f"animal.protectionist{DK}": -0.47,
    "people.animalsPrioritise wild animals": 0.66,
    "people.animalsPrioritise neither wild animals nor people": 0.43,
    "people.animalsPrioritise people": 0.72,
    "people.animalsStrongly prioritise people": 1.49,
    f"people.animals{DK}": 0.81,
    "1|2": 1.91,
    "2|3": 2.72,
    "3|4": 3.22,
    "4|5": 3.59,
    "5|6": 4.81,
    "6|7": 6.05,
}
RESPONSES = [
    "Very unacceptable",
    "Unacceptable",
    "Somewhat unacceptable",
    "Neither acceptable nor unacceptable",
    "Somewhat acceptable",
    "Acceptable",
    "Very acceptable",
]
TOL = 0.0051  # half a unit in S6's second decimal, plus float slack
# The thresholds and the education terms move together along a flat ridge: the
# reference level, primary schooling, holds 5 of 1,192 people (S6's threshold SEs
# are 1.02). polr and clm stop at slightly different points on it; 1|2 lands at
# 1.9153 against S6's 1.91 while every coefficient matches to two decimals. So the
# thresholds get a whole unit in the second decimal, and nothing else does.
TOL_THRESHOLD = 0.01


def model_frame() -> pd.DataFrame:
    dep = pd.read_csv(DEPOSIT, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    dep["pid"] = range(1, len(dep) + 1)
    dep["response"] = dep["response.text"].map({t: i + 1 for i, t in enumerate(RESPONSES)})
    assert dep["response"].notna().all()
    built = pd.read_parquet(BUILT)
    built["pid"] = built["participant_id"].str.removeprefix("zenodo10641548:").astype(int)
    assert built["pid"].is_unique
    uk = dep["country.1"] == "UK"
    assert set(built["pid"]) == set(dep.loc[uk, "pid"]), "built rows != deposit UK respondents"
    b = built.set_index("pid")
    ids = dep.loc[uk, "pid"]
    dep.loc[uk, "response"] = b.loc[ids, "response_num"].astype(int).to_numpy()
    for col, table in (("animal", ANIMAL), ("meat", MEAT), ("revenue", REVENUE)):
        dep.loc[uk, col] = [table[f[col]] for f in b.loc[ids, "factors"]]
    out = dep.rename(columns={"country.1": "country"})
    out["education"] = out["education"].str.strip()
    cols = ["response", "country", "animal", "meat", "revenue", "education", "hunter"]
    return out[[*cols, "animal.protectionist", "people.animals"]]


def fit(frame: pd.DataFrame) -> pd.DataFrame:
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp) / "in.csv", Path(tmp) / "out.csv"
        frame.to_csv(src, index=False, encoding="utf-8")
        subprocess.run(["Rscript", str(R_HELPER), str(src), str(dst)], check=True)
        return pd.read_csv(dst, encoding="utf-8")


def compare(est: pd.Series, quiet: bool = False) -> list[str]:
    """The S6 terms the fit does not reproduce, plus any term S6 does not have."""
    bad = []
    for term, want in S6.items():
        got = float(est[term])
        tol = TOL_THRESHOLD if "|" in term else TOL
        flag = "" if abs(got - want) <= tol else "   <-- MISMATCH"
        if flag:
            bad.append(term)
        if not quiet:
            print(f"  {term:58s} S6 {want:6.2f}  built {got:8.4f}{flag}")
    return bad + sorted(set(est.index) - set(S6))


def main() -> int:
    frame = model_frame()
    est = fit(frame).set_index("term")["estimate"]
    bad = compare(est)
    extra = sorted(set(est.index) - set(S6))
    print(
        f"\n{len(S6) - len(bad) + len(extra)}/{len(S6)} S6 estimates reproduced; terms not in S6: {extra}"
    )
    uk = frame[frame["country"] == "UK"]
    print("\nUK only, mean acceptability (1-7) by factor level, from the built rows:")
    for col in ("animal", "meat", "revenue"):
        print(f"  {col}: {uk.groupby(col)['response'].mean().round(2).to_dict()}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
