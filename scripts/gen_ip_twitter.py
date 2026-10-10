#!/usr/bin/env python3
"""Derive the data file for IP 9.33 — Twitter consent, help links on the page or apart.

Wave 15 (2022). Households were split in two (`ff_twithelpw15`). Respondents
with a personal Twitter account were asked for consent to link it to their
survey answers. Version A showed eight help links on the consent page, between
the text and the question (`twitlinka`, Yes / No). Version B showed no links and
added a third option, "Not sure, I would like more information.", which led to a
separate page with the links and the question again (`twitlinkb`, then
`twitlinkinfo` for those who chose it).

The recipe (`recipes/ukds_6849_twitter_consent_w15.yaml`) holds the judgement.
This script does what a recipe cannot, because the pipeline reads one file and
the allocation is in another:

**Allocation is at household level**, in `o_hhsamp_ip`, joined on `o_hidp`.
`--check` verifies the join against the routing (ledger 138): a respondent's
consent answer must sit only in their own version's variable.

**The consent text has one respondent-level fill**: "As you have completed
surveys with us in the past, we {if ff_everint=1} / We {if ff_everint<>1}".
`ff_everint` is not in the person file; `o_indsamp_ip.o_everint` ("Interview
status: previous waves") is. `--check` confirms it against the instrument's own
routing: the Initial Conditions question `Ukborn` is asked only if
`ff_ivlolw <> 1 & ff_everint <> 1`, so anyone asked it had `ff_everint <> 1`.
`o_everint` = -8 (inapplicable) is resolved to the "<> 1" branch only when
`Ukborn` was asked, which is the script taking that branch.

**`pidp` is never written out.** `person` is the same hash as every other
Innovation Panel build.

    uv run python scripts/gen_ip_twitter.py --check
    uv run python scripts/gen_ip_twitter.py --write
"""

from __future__ import annotations

import argparse
import hashlib
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

from micromotives_datasets.sources import spss

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[1]
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"
OUT = REPO / "data" / "raw" / "ukds_6849"
W, WAVE, YEAR = "o", 15, 2022

ALLOC = "ff_twithelpw15"
OWN = {1: "twitlinka", 2: "twitlinkb"}
ANSWERS = ("twithave", "twitlinka", "twitlinkb", "twitlinkinfo")

PERSONA = (
    "dvage",
    "sex",
    "gor_dv",
    "jbstat",
    "hiqual_dv",
    "mastat_dv",
    "racel_dv",
    "nchild_dv",
)


def person_hash(pidp: int) -> str:
    """Same construction as `scripts/build_profiles.py`. Never the raw `pidp`."""
    return "ip_" + hashlib.sha256(f"ukds6849:{pidp}".encode()).hexdigest()[:12]


def derived_name() -> str:
    return f"twitter_w{WAVE}-derived.sav"


class IdentifierSafeError(RuntimeError):
    """An error whose message carries no respondent identifier or value."""


def _merge(left: pd.DataFrame, right: pd.DataFrame, key: str, what: str) -> pd.DataFrame:
    """A many-to-one left join that can never print a key.

    pandas' own `MergeError` lists the duplicated keys, which here are `pidp`s
    and household ids: licensed identifiers, and one such message already put
    `pidp`s into a conversation transcript. The duplicate is counted instead,
    and the original exception is suppressed rather than chained.
    """
    dupes = int(right[key].duplicated().sum())
    if dupes:
        raise IdentifierSafeError(f"{what}: {dupes} duplicated join key(s) on the right")
    try:
        return left.merge(right, on=key, how="left", validate="many_to_one")
    except Exception:
        raise IdentifierSafeError(f"{what}: merge failed (keys withheld)") from None


def _joined() -> tuple[pd.DataFrame, dict]:
    ind = spss.read(STATA / f"{W}_indresp_ip.dta")
    hh = spss.read(STATA / f"{W}_hhsamp_ip.dta")
    isamp = spss.read(STATA / f"{W}_indsamp_ip.dta")
    keep = [
        "pidp",
        f"{W}_hidp",
        f"{W}_indmode",
        f"{W}_ukborn",
        f"{W}_ff_ivlolw",
        *(f"{W}_{v}" for v in ANSWERS),
        *(f"{W}_{v}" for v in PERSONA),
    ]
    missing = [c for c in keep if c not in ind.df.columns]
    if missing:
        raise ValueError(f"indresp is missing {missing}")
    merged = _merge(
        ind.df[keep], hh.df[[f"{W}_hidp", f"{W}_{ALLOC}"]], f"{W}_hidp", "household allocation"
    )
    # A person can sit in two sampled households (6,938 rows, 6,796 people);
    # `o_everint` never differs between a person's rows, so one per person.
    status = isamp.df[["pidp", f"{W}_everint"]].drop_duplicates()
    if status["pidp"].duplicated().any():
        raise ValueError("o_everint differs between one person's indsamp rows")
    merged = _merge(merged, status, "pidp", "interview status")
    unmatched = int(merged[f"{W}_{ALLOC}"].isna().sum())
    if unmatched:
        raise ValueError(f"{unmatched} respondents have no household allocation row")
    return merged, ind.value_labels


def _everint(merged: pd.DataFrame) -> pd.Series:
    """1 = ff_everint was 1; 2 = it was not, by the record or by the Ukborn routing."""
    rec = merged[f"{W}_everint"]
    asked_ukborn = merged[f"{W}_ukborn"] != -8
    out = pd.Series(np.nan, index=merged.index)
    out[rec == 1] = 1
    out[rec == 2] = 2
    out[(rec == -8) & asked_ukborn] = 2
    return out


def derive() -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    """One row per respondent: their version, mode, answers, fill and persona."""
    merged, value_labels = _joined()
    out = pd.DataFrame({"person": [person_hash(int(p)) for p in merged["pidp"]]})
    out["version"] = merged[f"{W}_{ALLOC}"].to_numpy()
    out["indmode"] = merged[f"{W}_indmode"].to_numpy()
    out["everint"] = _everint(merged).to_numpy()
    for v in ANSWERS:
        out[v] = merged[f"{W}_{v}"].to_numpy()
    for v in PERSONA:
        out[v] = merged[f"{W}_{v}"].to_numpy()
    out["wave"] = WAVE
    out["year"] = YEAR

    labels: dict[str, dict[float, str]] = {}
    for v in PERSONA:
        got = value_labels.get(f"{W}_{v}")
        if got:
            labels[v] = dict(got)
    return out, labels


def check(merged: pd.DataFrame | None = None) -> int:
    """Routing and fill disagreements, counted. Must be zero. Prints counts only.

    `merged` defaults to the deposit; a test passes a deliberately broken copy
    to show each count can fail.
    """
    if merged is None:
        merged, _ = _joined()
    bad = 0
    alloc = merged[f"{W}_{ALLOC}"]
    for version, own in OWN.items():
        other = OWN[3 - version]
        in_arm = alloc == version
        asked_own = int((~merged.loc[in_arm, f"{W}_{own}"].isin([-8, -7])).sum())
        asked_other = int((~merged.loc[in_arm, f"{W}_{other}"].isin([-8, -7])).sum())
        # A Twitter user in this version whose own question holds no code at all.
        users = in_arm & (merged[f"{W}_twithave"] == 1)
        missed = int((merged.loc[users, f"{W}_{own}"] == -8).sum())
        print(
            f"  version {version}: {asked_own:,} routed to {own}, {asked_other} to {other}, "
            f"{missed} Twitter users not routed to {own}"
        )
        bad += asked_other + missed
    info_bad = int(
        (
            (merged[f"{W}_twitlinkinfo"] != -8)
            & (merged[f"{W}_twitlinkinfo"] != -7)
            & (merged[f"{W}_twitlinkb"] != 3)
        ).sum()
    )
    print(f"  twitlinkinfo asked without twitlinkb = 3: {info_bad}")
    bad += info_bad

    # The fill: in the built population (web, Twitter account, allocated), the
    # record must agree with the Ukborn routing wherever both speak, and every
    # respondent must resolve.
    pop = (merged[f"{W}_indmode"] == 3) & (merged[f"{W}_twithave"] == 1) & alloc.isin([1, 2])
    rec = merged.loc[pop, f"{W}_everint"]
    asked = merged.loc[pop, f"{W}_ukborn"] != -8
    ivlolw1 = merged.loc[pop, f"{W}_ff_ivlolw"] == 1
    contradict = int(((rec == 1) & asked).sum() + ((rec == 2) & ~asked & ~ivlolw1).sum())
    unresolved = int(_everint(merged).loc[pop].isna().sum())
    print(
        f"  fill: {int((rec == 1).sum())} previously interviewed, "
        f"{int((rec == 2).sum())} not, {int((rec == -8).sum())} inapplicable "
        f"(resolved by Ukborn routing); {contradict} contradict the routing, "
        f"{unresolved} unresolved"
    )
    bad += contradict + unresolved
    print(f"  {'AGREE' if bad == 0 else 'ROUTING DEFECT'}")
    return bad


def main() -> None:
    try:
        _main()
    except SystemExit:
        raise
    except IdentifierSafeError as exc:
        raise SystemExit(f"error: {exc}") from None
    except Exception as exc:
        # Any other message could quote a value from the deposit, so only the
        # exception's type leaves this process.
        raise SystemExit(f"error: {type(exc).__name__} (message withheld)") from None


def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify the join and the fill")
    ap.add_argument("--write", action="store_true", help="write the derived .sav file")
    args = ap.parse_args()

    if args.check and check():
        raise SystemExit("routing check failed")

    df, labels = derive()
    print(f"wave {WAVE}: {len(df):,} respondents")
    if args.write:
        narrow = df.copy()
        for col in narrow.columns:
            if narrow[col].dtype == "object" or str(narrow[col].dtype).startswith("string"):
                narrow[col] = narrow[col].astype(object).where(narrow[col].notna(), np.nan)
        path = OUT / derived_name()
        pyreadstat.write_sav(narrow, str(path), variable_value_labels=labels)
        print(f"  wrote {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
