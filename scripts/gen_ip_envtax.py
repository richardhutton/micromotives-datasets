#!/usr/bin/env python3
"""Derive the data file for IP 9.14: willingness to pay environmental taxes, ten wordings.

Wave 7 (2014). Households within PSUs were allocated to one of ten question
versions, A to J (`ff_envtaxqw7` in `g_hhsamp_ip`, User Guide 9.14). Each
respondent was asked ONE question, in their version's wording, stored in its own
variable `envtax_a` ... `envtax_j` in `g_indresp_ip`, all on the same four-point
answer scale ("Very willing" ... "Not at all willing"). The ten versions are five
pairs: in each pair one wording does not mention other taxes being reduced and
the other adds "if the government reduced other taxes you pay by the same
amount" (or its variant).

The recipe (`recipes/ukds_6849_envtax_w7.yaml`) holds the judgement. This
script does what a recipe cannot, because the pipeline reads one file and the
allocation is in another: it joins the version to the person on `g_hidp`.

**"Not asked" is written as blank.** In the deposit a question nobody put to a
respondent is coded -8 (inapplicable), or -7 for a proxy interview. The derived
file writes both as blank, and every other code (an answer, -1 don't know, -2
refused, -9 missing) as it stands. That is what lets the recipe switch on
`routing_check` (ledger 143), which counts a code in ANOTHER version's variable
as a second condition and needs blank to mean "not asked".

`--check` verifies, and exits non-zero on any disagreement:

- **allocation = routing** (ledger 134, 138): every non-proxy respondent holds a
  code in their own version's variable and none is missing one; codes in another
  version's variable are counted, and the count must equal `DOUBLY_ROUTED`, the
  number the recipe declares as `ambiguous_routing`;
- **only "not asked" is blanked**: -8 and -7 appear only where the routing says
  the question was not put, and -7 only for proxy interviews;
- **the wording**: each version's question, transcribed below, occurs in
  `6849_ip_wave_7_questionnaires.pdf` inside its own item's Text block, whose
  Universe routes it on the matching `ff_envtaxqw7` code; and the recipe's
  condition and outcome for each arm carry exactly that question.

**`pidp` is never written out.** `person` is the same hash as every other
Innovation Panel build. Nothing here prints a respondent-level value or an
identifier; every line of output is a count.

    uv run python scripts/gen_ip_envtax.py --check
    uv run python scripts/gen_ip_envtax.py --write
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

from micromotives_datasets import recipe as recipe_mod
from micromotives_datasets.sources import spss

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[1]
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"
PDF = REPO / "data" / "raw" / "ukds_6849" / "mrdoc" / "pdf" / "6849_ip_wave_7_questionnaires.pdf"
OUT = REPO / "data" / "raw" / "ukds_6849"
RECIPE = REPO / "recipes" / "ukds_6849_envtax_w7.yaml"
W, WAVE, YEAR = "g", 7, 2014

ALLOC = "ff_envtaxqw7"
VERSIONS = "abcdefghij"
# version code (1..10) -> its own answer variable
OWN = {i + 1: f"envtax_{v}" for i, v in enumerate(VERSIONS)}

# Respondents holding a code in a version's variable other than their own. The
# recipe declares the same number as `ambiguous_routing`; the melt drops them.
DOUBLY_ROUTED = 1

# Module Environmentaltax_ip7, items Envtax_a ... Envtax_j, the "Text" field,
# word-for-word. Typography: the source has no curly characters here.
QUESTIONS = {
    1: "How willing would you be to pay higher taxes in order to protect the environment?",
    2: "How willing would you be to pay higher taxes in order to protect the environment, "
    "if the government reduced other taxes you pay by the same amount?",
    3: "How willing would you be to pay higher taxes, if the government spent the extra "
    "money on protecting the environment?",
    4: "How willing would you be to pay higher taxes, if the government spent the extra "
    "money on protecting the environment and reduced other taxes you pay by the same amount?",
    5: "How willing would you be to pay higher taxes, if the government promised it would "
    "spend the extra money on protecting the environment?",
    6: "How willing would you be to pay higher taxes, if the government promised it would "
    "spend the extra money on protecting the environment and reduce other taxes you pay "
    "by the same amount?",
    7: "How willing would you be to pay higher taxes on things you buy that pollute the "
    "environment?",
    8: "How willing would you be to pay higher taxes on things you buy that pollute the "
    "environment, if the government reduced other taxes you pay by the same amount?",
    9: "How willing would you be to pay higher taxes on things you buy that pollute the "
    "environment, like petrol or electricity?",
    10: "How willing would you be to pay higher taxes on things you buy that pollute the "
    "environment, like petrol or electricity, if the government reduced other taxes you "
    "pay by the same amount?",
}
OPTIONS = ("Very willing", "Fairly willing", "Not very willing", "Not at all willing")

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
    return f"envtax_w{WAVE}-derived.sav"


class IdentifierSafeError(RuntimeError):
    """An error whose message carries no respondent identifier or value."""


def _merge(left: pd.DataFrame, right: pd.DataFrame, key: str, what: str) -> pd.DataFrame:
    """A many-to-one left join that can never print a key (see gen_ip_twitter.py)."""
    dupes = int(right[key].duplicated().sum())
    if dupes:
        raise IdentifierSafeError(f"{what}: {dupes} duplicated join key(s) on the right")
    try:
        return left.merge(right, on=key, how="left", validate="many_to_one")
    except Exception:
        raise IdentifierSafeError(f"{what}: merge failed (keys withheld)") from None


def _joined() -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    ind = spss.read(STATA / f"{W}_indresp_ip.dta")
    hh = spss.read(STATA / f"{W}_hhsamp_ip.dta")
    keep = [
        "pidp",
        f"{W}_hidp",
        f"{W}_indmode",
        *(f"{W}_{v}" for v in OWN.values()),
        *(f"{W}_{v}" for v in PERSONA),
    ]
    missing = [c for c in keep if c not in ind.df.columns]
    if missing:
        raise ValueError(f"indresp is missing {missing}")
    if int(ind.df["pidp"].duplicated().sum()):
        raise IdentifierSafeError("indresp holds a person twice")
    merged = _merge(
        ind.df[keep], hh.df[[f"{W}_hidp", f"{W}_{ALLOC}"]], f"{W}_hidp", "household allocation"
    )
    unmatched = int(merged[f"{W}_{ALLOC}"].isna().sum())
    if unmatched:
        raise ValueError(f"{unmatched} respondents have no household allocation row")
    return merged, ind.value_labels


def _blank_not_asked(series: pd.Series) -> pd.Series:
    """-8 (inapplicable) and -7 (proxy) mean the question was not put: blank."""
    return series.where(~series.isin([-8, -7]), np.nan)


def derive() -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    """One row per respondent: their version, their answers, their persona."""
    merged, value_labels = _joined()
    out = pd.DataFrame({"person": [person_hash(int(p)) for p in merged["pidp"]]})
    out["version"] = merged[f"{W}_{ALLOC}"].to_numpy()
    out["indmode"] = merged[f"{W}_indmode"].to_numpy()
    for v in OWN.values():
        out[v] = _blank_not_asked(merged[f"{W}_{v}"]).to_numpy()
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


def check_routing(merged: pd.DataFrame) -> int:
    """Allocation against routing, counted. Prints counts only."""
    bad = 0
    alloc = merged[f"{W}_{ALLOC}"]
    proxy = merged[f"{W}_indmode"] == -7
    elsewhere = pd.Series(False, index=merged.index)
    for code, var in OWN.items():
        own = merged[f"{W}_{var}"]
        in_arm = alloc == code
        answered = in_arm & ~proxy & own.isin([1, 2, 3, 4])
        nonanswer = in_arm & ~proxy & own.isin([-1, -2, -9])
        # Every non-proxy in this version must have been put this question.
        # A blank (NaN) there would be written blank and silently dropped, so it
        # counts as not routed too.
        not_routed = int((in_arm & ~proxy & (own.isin([-8, -7]) | own.isna())).sum())
        # A proxy is never interviewed, so must hold -7 and nothing else.
        proxy_coded = int((in_arm & proxy & (own != -7)).sum())
        print(
            f"  version {code:>2} ({var}): {int(in_arm.sum()):,} respondents, "
            f"{int(answered.sum()):,} answers 1-4, {int(nonanswer.sum())} non-answers, "
            f"{int((in_arm & proxy).sum())} proxies; {not_routed} not routed to their own "
            f"question, {proxy_coded} proxies holding a code"
        )
        bad += not_routed + proxy_coded
        for other_code, other in OWN.items():
            if other_code == code:
                continue
            got = merged[f"{W}_{other}"]
            elsewhere |= in_arm & ~got.isin([-8, -7])
            # -7 outside a proxy, or anything but -8 / -7 for a proxy, means the
            # blanking would hide a code that is not "not asked".
            bad += int((in_arm & ~proxy & (got == -7)).sum())
    unallocated = ~alloc.isin(list(OWN))
    codes = merged[[f"{W}_{v}" for v in OWN.values()]]
    stray = int((unallocated & (~codes.isin([-8, -7]) & codes.notna()).any(axis=1)).sum())
    doubly = int(elsewhere.sum())
    print(
        f"  {int(unallocated.sum())} respondents without a version ({stray} holding a code); "
        f"{doubly} holding a code in another version's variable (declared {DOUBLY_ROUTED})"
    )
    bad += stray + abs(doubly - DOUBLY_ROUTED)
    return bad


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _questionnaire() -> str:
    got = subprocess.run(["pdftotext", str(PDF), "-"], capture_output=True, text=True, check=True)
    return got.stdout


def check_wording(quex: str | None = None) -> int:
    """Each question in its own item's Text block, routed on its own code."""
    if quex is None:
        quex = _questionnaire()
    bad = 0
    for code, var in OWN.items():
        item = var.capitalize()  # Envtax_a
        start = quex.find(f"{item}.")
        if start < 0:
            print(f"  {item}: not found in the questionnaire")
            bad += 1
            continue
        block = quex[start:]
        text = block[block.find("Text") + 4 : block.find("Interviewer Instruction")]
        universe = re.search(r"If \(ff_envtaxqw7=(\d+)\)", block)
        opts = block[block.find("Options") : block.find("Mixed Mode")]
        ok_text = _norm(text) == QUESTIONS[code]
        ok_route = universe is not None and int(universe.group(1)) == code
        ok_opts = all(f"{i} {o}" in _norm(opts) for i, o in enumerate(OPTIONS, start=1))
        if not (ok_text and ok_route and ok_opts):
            print(f"  {item}: text {ok_text}, routed on code {code} {ok_route}, options {ok_opts}")
            bad += 1
    print(f"  wording: {10 - bad} of 10 items match the questionnaire's Text, Universe and Options")
    return bad


def check_recipe() -> int:
    """The recipe's condition and outcome for each arm carry its version's question."""
    rec = recipe_mod.load(RECIPE)
    bad = 0
    seen = set()
    for arm in rec.condition.arms:
        code = int(arm.raw)
        seen.add(code)
        item = arm.items[0]
        if arm.text != f'You were asked: "{QUESTIONS[code]}"':
            bad += 1
            print(f"  arm {arm.condition_num}: condition text is not version {code}'s question")
        if item.outcome_question != QUESTIONS[code] or item.outcome_var != OWN[code]:
            bad += 1
            print(f"  arm {arm.condition_num}: outcome is not version {code}'s question/variable")
    if seen != set(OWN):
        bad += 1
        print(f"  recipe arms cover versions {sorted(seen)}")
    if rec.condition.ambiguous_routing != DOUBLY_ROUTED:
        bad += 1
        print("  recipe ambiguous_routing differs from DOUBLY_ROUTED")
    print(f"  recipe: {len(rec.condition.arms)} arms, {bad} disagreements with the transcription")
    return bad


def check(merged: pd.DataFrame | None = None, quex: str | None = None) -> int:
    """All three checks. `merged` / `quex` let a test pass a deliberately broken copy."""
    if merged is None:
        merged, _ = _joined()
    bad = check_routing(merged) + check_wording(quex) + check_recipe()
    print(f"  {'AGREE' if bad == 0 else 'DISAGREE'}")
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
    ap.add_argument("--check", action="store_true", help="verify routing, wording and recipe")
    ap.add_argument("--write", action="store_true", help="write the derived .sav file")
    args = ap.parse_args()

    if args.check and check():
        raise SystemExit("check failed")

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
