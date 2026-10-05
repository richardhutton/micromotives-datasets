#!/usr/bin/env python3
"""Derive `sky-data-derived.sav` from the Sky sub-study's raw deposit file.

`recipes/35M5CV_sky.yaml` is hand-authored (4 arms x 5 items = 20 cells, small
enough to write directly, unlike `35M5CV_lodger`/`35M5CV_bbc`'s machine-written
hundreds of conjoint arms). What a hand-authored recipe CANNOT do is express
"the arm code lives in `refid` for these respondents and in `pid` for those" —
`recipe.Condition.source_var` names exactly one column, and `source_vars`
combines several with AND semantics (every one must be populated), not OR.
Here `refid` (Brexit identity) is populated only for Split 1 and `pid` (party
identity) only for Split 2 — never both for the same respondent — so neither
mechanism fits. This script does the one additional thing the recipe schema
cannot: it derives ONE merged arm-code column, `IdentityArm`, mechanically and
reproducibly, the same role `gen_PMV0TG.py`'s reshape plays for a shape the
melt cannot read directly.

ARM CODES (by the respondent's OWN primary identity answer only — see below):

    1  Remainer   Split 1, refid == 1  (574 respondents)
    2  Leaver     Split 1, refid == 3  (704 respondents)
    3  Conservative  Split 2, pid == 1 (580 respondents)
    4  Labour        Split 2, pid == 3 (553 respondents)

EXCLUDED FROM EVERY ARM, ON PURPOSE: refid == 2 ("Neither") and the 87
respondents who did not answer `refid` at all, and pid == 2 ("None") and pid
== 4 ("Other party"). All four groups contain respondents whose emotional-
attachment battery (`EArefR*`/`EArefL*`/`EApidC*`/`EApidLa*`) IS non-missing —
investigation (recorded in `recipes/35M5CV_sky.yaml`'s notes) found this is
fully explained by a deterministic follow-up "lean" question (`refid1`/`pid1`)
asked only of "Neither"/"None" respondents, NOT a mystery and NOT a second
randomisation. It is excluded anyway because (a) the deposit ships no
questionnaire for Sky, so there is no verbatim wording for the follow-up
question to build an honest condition from, and (b) writing a condition that
asserts "you think of yourself as a Remainer" for someone who told the primary
identity question "Neither" would be false regardless of what they said on a
follow-up we cannot quote. Weighted reproduction of the paper's own Table 2
(see the recipe notes) confirms this is also exactly the population the
AUTHORS used for that table, not merely the conservative choice.

SENTINEL CLEANING — "audit, do not copy" (CLAUDE.md)

This deposit ships several persona columns as plain strings with embedded
refusal/sentinel TEXT and no numeric code at all (`meta.variable_value_labels`
is empty for every one of them) — `recipe.persona_missing`'s mechanism can only
match a value that converts to a number (`_as_code`), so a bare-text sentinel
like "Prefer not to say" or "0" would otherwise pass straight through into the
rendered persona as if it were a genuine answer. This script blanks exactly the
sentinels below, nothing else, each with its own observed file-wide count
asserted so a re-fetched deposit that drifts fails loudly rather than silently
changing what gets dropped:

    Govt_region         "0"                                   18 respondents
    Ethnicity           "Prefer not to say"                    75 respondents
    Age                 <18 or >100 (no declared value labels  7 respondents
                        at all for this field -- these are     (0 x4, 5, 109,
                        plausibility outliers, not a coded      116)
                        sentinel, exactly the class of finding
                        ledger's 6MRVOM entry describes: a
                        missing-code declared nowhere, found
                        only by checking observed values)

Age == 99 (one respondent, file-wide) was investigated and deliberately NOT
treated as a sentinel: it sits within a plausible human age range (unlike 0,
5, 109, 116) and there is no declared code nor external evidence that 99 means
"refused" for THIS field specifically -- the deposit's "else=99" convention
belongs to the sps script's own RECODE statements on other variables (refid,
pid, the Likert items), not to Age, which is raw panel demographic data. That
respondent is not in any arm anyway (`refid`/`pid` both missing for them), so
the choice is moot for the build and recorded here only for the audit trail.
    Interest_in_politics "Don't know" (curly apostrophe,        21 respondents
                        the deposit's own glyph)
    English_vs_British  "Don't know" (ditto)                    24 respondents

"None of these" on `English_vs_British` is NOT touched -- it is a genuine
fourth answer (neither English nor British), not a refusal.

Usage:

    uv run python scripts/gen_35M5CV_sky.py            # derive + report
    uv run python scripts/gen_35M5CV_sky.py --write     # derive + write .sav
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "35M5CV" / "sky-data.sav"
OUT = REPO / "data" / "raw" / "35M5CV" / "sky-data-derived.sav"

DK = "Don’t know"  # the deposit's own curly apostrophe (typography, not a word)

ARM_COLS = {
    1: ["EArefR1", "EArefR2", "EArefR3", "EArefR4", "EArefR5"],
    2: ["EArefL1", "EArefL2", "EArefL3", "EArefL4", "EArefL5"],
    3: ["EApidC1", "EApidC2", "EApidC3", "EApidC4", "EApidC5"],
    4: ["EApidLa1", "EApidLa2", "EApidLa3", "EApidLa4", "EApidLa5"],
}
EXPECTED_ARM_N = {1: 574, 2: 704, 3: 580, 4: 553}

PERSONA_COLS = [
    "Age",
    "Gender",
    "Ethnicity",
    "Govt_region",
    "Mosaic_2014_groups",
    "Interest_in_politics",
    "English_vs_British",
]


def derive(df: pd.DataFrame) -> pd.DataFrame:
    """Add `IdentityArm` and blank the documented sentinels. Pure function of df."""
    out = df.copy()

    # --- arm code ------------------------------------------------------
    is_s1 = out["Split"] == "Split 1"
    is_s2 = out["Split"] == "Split 2"
    arm = pd.Series(np.nan, index=out.index, dtype="float64")
    arm[is_s1 & (out["refid"] == 1)] = 1
    arm[is_s1 & (out["refid"] == 3)] = 2
    arm[is_s2 & (out["pid"] == 1)] = 3
    arm[is_s2 & (out["pid"] == 3)] = 4
    out["IdentityArm"] = arm

    counts = arm.value_counts(dropna=True).astype(int).to_dict()
    for code, expected in EXPECTED_ARM_N.items():
        got = counts.get(float(code), 0)
        if got != expected:
            raise AssertionError(
                f"IdentityArm={code} has {got} respondents, expected {expected} -- "
                "the deposit has drifted from what this script and the recipe's "
                "notes were written against; re-derive the exclusion arithmetic "
                "before trusting the output"
            )
    # Every arm member answered every item of their own battery -- no partial
    # completion anywhere (checked exhaustively before this script was written).
    for code, cols in ARM_COLS.items():
        members = out.loc[arm == code, cols]
        n_any = members.notna().any(axis=1).sum()
        n_all = members.notna().all(axis=1).sum()
        if n_any != n_all or n_all != EXPECTED_ARM_N[code]:
            raise AssertionError(
                f"arm {code}: {n_any} respondents answered >=1 item but {n_all} "
                "answered all 5 -- partial battery completion has appeared where "
                "there was none before; the melt needs this understood, not just dropped"
            )

    # --- sentinel cleaning, each with an asserted file-wide count -------
    def _blank(col: str, mask: pd.Series, expected: int, label: str) -> None:
        got = int(mask.sum())
        if got != expected:
            raise AssertionError(
                f"{col}: {got} rows match the declared sentinel ({label}), expected "
                f"{expected} -- re-check before silently dropping a different count"
            )
        out.loc[mask, col] = np.nan

    _blank("Govt_region", out["Govt_region"] == "0", 18, '"0" (no such GB region)')
    _blank("Ethnicity", out["Ethnicity"] == "Prefer not to say", 75, '"Prefer not to say"')
    _blank("Interest_in_politics", out["Interest_in_politics"] == DK, 21, "Don't know")
    _blank("English_vs_British", out["English_vs_British"] == DK, 24, "Don't know")

    implausible_age = (out["Age"] < 18) | (out["Age"] > 100)
    _blank("Age", implausible_age, 7, "<18 or >100, no declared value label exists for Age")

    return out


def main() -> None:
    write = "--write" in sys.argv
    df, _meta = pyreadstat.read_sav(str(RAW))
    derived = derive(df)

    keep = ["IdentityArm", *PERSONA_COLS, *[c for cols in ARM_COLS.values() for c in cols]]
    narrow = derived[keep].copy()
    # pandas' Arrow-backed string dtype (pyreadstat's reader default) is not a
    # type pyreadstat.write_sav round-trips reliably; plain object + np.nan is.
    for col in narrow.columns:
        if narrow[col].dtype == "object" or str(narrow[col].dtype).startswith("string"):
            narrow[col] = narrow[col].astype(object).where(narrow[col].notna(), np.nan)

    print("IdentityArm counts:", narrow["IdentityArm"].value_counts(dropna=True).to_dict())
    print("rows:", len(narrow), "columns:", list(narrow.columns))

    if write:
        pyreadstat.write_sav(
            narrow,
            str(OUT),
            variable_value_labels={
                "IdentityArm": {
                    1: "Remainer identity (Brexit)",
                    2: "Leaver identity (Brexit)",
                    3: "Conservative identity (party)",
                    4: "Labour identity (party)",
                }
            },
        )
        print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
