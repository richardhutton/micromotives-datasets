#!/usr/bin/env python3
"""Jev first pass over freshly fetched studies: which variable is the assignment?

Run before writing a recipe. Answers at or above the confidence threshold are
taken as a starting point; anything below is flagged for a human to settle.

This is the honest test of Jev, because unlike the calibration harness these
studies have NOT been built by hand yet — there is no answer to leak.

    uv run python scripts/jev_firstpass.py 7jt2f bf8p2 ...
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from micromotives_datasets.sources import spss

try:
    from typesafe_sdk import Choice, TypeSafeClient
except ImportError:  # pragma: no cover
    sys.exit("uv add typesafe-sdk first")

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw"
THRESHOLD = 0.85

NONE = "NONE_OF_THESE"

# A DENYLIST, deliberately — not an allowlist. An allowlist of keyword hints
# silently drops the right answer when it is named something unexpected (we lost
# CALARCO_VIGNETTE that way, and Jev then picked a question-order variable at
# 0.99 because it was the least-bad of the two options it was given). Excluding
# obvious non-candidates errs towards keeping the true answer in the list.
EXCLUDE_EXACT = {"caseid", "case_id", "id", "weight", "w8", "ns", "total", "respdate"}
EXCLUDE_SUBSTR = (
    "_time",
    "tm_start",
    "tm_finish",
    "starttime",
    "endtime",
    "duration",
    "weight",
    "svy_",
    "ppage",
    "ppeduc",
    "ppethm",
    "ppgender",
    "pphouse",
    "ppincome",
    "ppincimp",
    "ppmarit",
    "ppmsacat",
    "ppnet",
    "ppreg",
    "pprent",
    "ppstaten",
    "ppt0",
    "ppt1",
    "ppt2",
    "ppt6",
    "ppwork",
    "pphhhead",
    "pphhsize",
    "ppagecat",
    "ppagect",
    "ppdualin",
    "ppeducat",
)


def _is_plausible(name: str) -> bool:
    low = name.lower()
    if low in EXCLUDE_EXACT:
        return False
    return all(s not in low for s in EXCLUDE_SUBSTR)


def _fmt(key: object) -> str:
    """Value-label keys are usually floats but can be strings."""
    return f"{key:g}" if isinstance(key, (int, float)) else str(key)


def data_file_for(study_id: str) -> Path | None:
    """The biggest .sav/.dta in the study's raw folder."""
    folder = RAW / study_id
    if not folder.is_dir():
        return None
    files = [
        p
        for p in folder.rglob("*")
        if p.is_file()
        and p.suffix.lower() in {".sav", ".dta", ".por"}
        and not p.name.startswith("._")
    ]
    return max(files, key=lambda p: p.stat().st_size) if files else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("studies", nargs="+")
    ap.add_argument("--threshold", type=float, default=THRESHOLD)
    args = ap.parse_args()

    client = TypeSafeClient()
    auto = review = 0

    for study_id in args.studies:
        path = data_file_for(study_id)
        if path is None:
            print(f"SKIP   {study_id}: no .sav/.dta found under data/raw/{study_id}")
            continue

        ds = spss.read(path)
        cols = list(ds.df.columns)

        def describe(col: str, ds: spss.Dataset = ds) -> str:
            """Variable label PLUS its value labels.

            The value labels are what disambiguate. a5v96's XTESS193 is LABELLED
            "Experimental condition" but its values are "Vignette1 followed by
            Vignette2" — presentation order, not the manipulation, whose own
            variables are labelled merely "Data Only Variable". Sending variable
            labels alone made Jev pick the order variable at confidence 1.00.
            """
            label = (ds.column_labels.get(col) or "")[:110]
            values = ds.value_labels.get(col) or {}
            if values and len(values) <= 14:
                shown = "; ".join(f"{_fmt(k)}={v}" for k, v in list(values.items())[:6])
                return f"- {col}: {label}  [values: {shown[:170]}]"
            return f"- {col}: {label}"

        listing = "\n".join(describe(c) for c in cols[:70])
        # Offer EVERY plausible variable. Two earlier attempts to "help" by
        # pre-selecting (keyword hints, then fewest-distinct-values) each
        # excluded the true answer: the keyword filter dropped CALARCO_VIGNETTE
        # because its label says "vignette", and the arm-count ordering then
        # filled the list with low-cardinality demographics instead. Narrowing
        # the options is the caller quietly making the decision it is asking
        # the model to make.
        candidates = [c for c in cols if _is_plausible(c)][:60]

        response = client.system_one(
            state=f"A survey experiment data file. Variables and labels:\n\n{listing}",
            questions={
                "assignment_var": Choice(
                    instructions=(
                        "Which variable records which randomly assigned experimental "
                        "condition each respondent was placed in? If several variables "
                        "look like assignments, choose the primary one."
                    ),
                    criteria={
                        **{c: (ds.column_labels.get(c) or "")[:90] for c in candidates},
                        NONE: "None of these is the experimental assignment variable",
                    },
                )
            },
        )
        ans = response.answers["assignment_var"]
        flagged = ans.confidence >= args.threshold and ans.choice != NONE
        auto += flagged
        review += not flagged

        counts = (
            ds.df[ans.choice].value_counts().sort_index() if ans.choice in ds.df.columns else None
        )
        runners = sorted(ans.probabilities.items(), key=lambda kv: -kv[1])[1:3]

        print(
            f"{'AUTO  ' if flagged else 'REVIEW'} {study_id}  -> {ans.choice:24} "
            f"conf {ans.confidence:.2f}   ({ds.df.shape[0]:,} rows)"
        )
        print(f"         label:  {(ds.column_labels.get(ans.choice) or '')[:74]}")
        if counts is not None:
            print(f"         arms:   {dict(list(counts.items())[:12])}")
        print(f"         next:   {[(k, round(v, 2)) for k, v in runners]}")
        print()

    print(f"{auto} auto-accepted at >={args.threshold}, {review} flagged for review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
