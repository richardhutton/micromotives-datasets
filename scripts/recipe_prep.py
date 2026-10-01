#!/usr/bin/env python3
"""Everything Jev can tell you about a study, before you write its recipe.

**Run this first.** One command, four questions, all of them the kind that need
reading comprehension rather than arithmetic:

  1. Which column records the randomised assignment?
  2. Which columns are the persona attributes?
  3. Which value labels are non-answers, and which are answers wearing a
     scripting instruction?
  4. Which directives in the questionnaire does `sources.quex` refuse, and do
     any of them actually gate stimulus text?

Each of those was already answerable by some script in here, and that was the
problem: a maker had to know which of eight scripts to run, so in practice none
got run. Wave 1 was authored by five agents reading variable names by eye, with
a regex backstop, while a calibrated tool sat unused — not their fault, it was
not in the brief. This is the brief.

Nothing here decides anything. Every answer prints its confidence and is flagged
REVIEW when the model itself is unsure or when the runner-up was close. What you
do with it is write it into the recipe, where a human reads it and a checker
argues with it.

On the wire: variable names, labels, value labels, questionnaire directives.
Never respondent rows — `jev.describe_variable` takes labels, not data.

    source ~/.bash_profile && uv run python scripts/recipe_prep.py 9xw67
    ... --skip-labels        # the slowest section, one call per value label
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from micromotives_datasets import jev  # noqa: E402
from micromotives_datasets.sources import quex, spss  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw"

# Columns that cannot be an assignment or a persona attribute. A DENYLIST on
# purpose: an allowlist of keyword hints silently drops the right answer when it
# is named unexpectedly, which is how `CALARCO_VIGNETTE` was lost once.
SKIP_EXACT = {"caseid", "case_id", "id", "weight", "w8", "ns", "total", "respdate"}
SKIP_SUBSTR = ("_time", "starttime", "endtime", "duration", "weight", "tm_", "ds_", "ts_")

# Persona attributes worth asking about, as the canonical schema names them.
PERSONA_FIELDS = {
    "age": "the respondent's age in years",
    "gender": "the respondent's sex or gender",
    "income": "household income",
    "education": "highest level of education completed",
    "ethnicity": "race or ethnicity",
    "employment": "current employment status",
    "marital": "marital status",
    "region": "region or census division of residence",
    "religion": "religious affiliation",
    "household_size": "number of people in the household",
}


def data_files_for(study_id: str) -> list[Path]:
    """EVERY data file in the deposit, largest first — not just the biggest.

    `9xw67` ships two: `TESS 091A Ozer/` and `TESS 091B Ozer/`, which are two
    sub-experiments with different columns. Silently taking the larger one
    answers every question about a file the maker may not have meant, and says
    nothing about the other. A deposit with several data files is a scope
    decision, and the tool's job is to surface it, not to make it.
    """
    folder = RAW / study_id
    if not folder.is_dir():
        return []
    files = [
        p
        for p in folder.rglob("*")
        if p.is_file()
        and p.suffix.lower() in {".sav", ".dta", ".por"}
        and not p.name.startswith("._")
    ]
    return sorted(files, key=lambda p: -p.stat().st_size)


def questionnaires(study_id: str) -> list[Path]:
    folder = RAW / study_id
    return [
        p
        for p in sorted(folder.rglob("*.txt"))
        if not p.name.startswith("._") and "Response Rate" not in p.name
    ]


def plausible(name: str) -> bool:
    low = name.lower()
    return low not in SKIP_EXACT and not any(s in low for s in SKIP_SUBSTR)


def section(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def report_assignment(cli: object, ds: spss.Dataset) -> None:
    section("1. WHICH COLUMN IS THE RANDOMISED ASSIGNMENT?")
    cols = [c for c in ds.df.columns if plausible(str(c))]
    listing = "\n".join(
        jev.describe_variable(str(c), ds.column_labels.get(c, ""), ds.value_labels.get(c))
        for c in cols
    )
    candidates = {str(c): (ds.column_labels.get(c) or "")[:90] for c in cols}
    v = jev.assignment_variable(cli, listing, candidates)
    print(v.render())
    if v.value in ds.df.columns:
        counts = ds.df[v.value].value_counts().sort_index()
        print(f"         arms:  {dict(list(counts.items())[:14])}")
        print(f"         labels:{ds.value_labels.get(v.value) or '(none)'}")
    print(
        "\n  Remember: the recipe DECLARES raw -> condition_num per arm. There is no\n"
        "  universal rule — one study maps raw-1, another has the arms reversed."
    )


def report_persona(cli: object, ds: spss.Dataset) -> None:
    section("2. WHICH COLUMNS ARE THE PERSONA ATTRIBUTES?")
    cols = [c for c in ds.df.columns if plausible(str(c))]
    listing = "\n".join(
        jev.describe_variable(str(c), ds.column_labels.get(c, ""), ds.value_labels.get(c))
        for c in cols
    )
    # ONE question per call, deliberately. The first version asked all ten in a
    # single `system_one` — the docs say questions in a call are independent, and
    # they are, but ten questions each offering sixty variables is a large
    # payload and every single field came back NONE_OF_THESE. Measured on
    # `9xw67`, whose file plainly contains AGE, GENDER, RACETHNICITY and EDUC5:
    # batched, nothing; asked alone, AGE at confidence 1.00. A batched call that
    # silently answers "none of the above" to everything is the worst possible
    # failure for a tool like this, because an empty report reads like a clean
    # one — which is how wave 1 ended up authored by eye.
    missing: list[str] = []
    all_cols = {str(c): (ds.column_labels.get(c) or "")[:80] for c in cols}
    for field, desc in PERSONA_FIELDS.items():
        v = jev.choose(
            cli,
            state=f"A survey data file. Variables:\n\n{listing}",
            instructions=(
                f"Which variable records {desc}? Judge the construct, not the name. "
                "Choose NONE_OF_THESE if no variable measures it."
            ),
            candidates=all_cols,
            none_means=f"no variable in this file records {desc}",
        )
        if v.value == jev.NONE_OF_THESE:
            missing.append(field)
        else:
            print(v.render(field))
    if missing:
        print(f"\n  not found in this file: {', '.join(missing)}")
    print(
        "\n  `persona_map` is a DECLARATION: a name that resolves to nothing is a hard\n"
        "  error, not an empty field. Three studies lost their whole persona to a\n"
        "  case-sensitive lookup before that was true."
    )


def report_labels(cli: object, ds: spss.Dataset, mapped: list[str]) -> None:
    section("3. WHICH VALUE LABELS ARE NON-ANSWERS?")
    print(
        "  For `persona_missing` (leave the field empty) vs `persona_label_rewrite`\n"
        "  (a real answer wearing scripting boilerplate). QC rule 12 keeps a keyword\n"
        "  regex as a backstop; this is the judgement.\n"
    )
    asked = 0
    for var in mapped:
        labels = [str(v) for v in (ds.value_labels.get(var) or {}).values()]
        if not labels or len(labels) > 20:
            continue
        suspicious = [
            lab
            for lab in labels
            if any(
                w in lab.lower()
                for w in ("refus", "missing", "not asked", "skip", "know", "specify", "other")
            )
        ]
        if not suspicious:
            continue
        asked += 1
        print(f"  {var}:")
        for lab, v in jev.label_is_a_non_answer(cli, var, labels).items():
            if lab in suspicious:
                print(f"    {v.render(repr(lab))}")
    if not asked:
        print("  No label in the mapped persona variables looks like a non-answer.")


def report_refusals(cli: object, study_id: str) -> None:
    section("4. QUESTIONNAIRE DIRECTIVES `quex` WILL NOT PARSE")
    refused: dict[str, None] = {}
    for path in questionnaires(study_id):
        text = path.read_text(errors="replace")
        conds = [m.group(1) for m in quex._BLOCK_SHOW_IF.finditer(text)]
        for m in quex._INLINE.finditer(text):
            conds += [b.group("cond") for b in quex._BRANCH.finditer(m.group(1))]
        conds += [m.group("cond") for m in quex._IF_DISPLAY.finditer(text)]
        for c in conds:
            c = " ".join(c.split())
            try:
                quex.parse_condition(c)
            except quex.UnparsedConditionError:
                refused[c] = None
    if not refused:
        print("  None — every conditional directive in this deposit parses.")
        return
    print(
        f"  {len(refused)} distinct. Only the ones that gate STIMULUS TEXT need resolving\n"
        "  by hand; administration and routing can be ignored.\n"
    )
    for cond in list(refused)[:25]:
        print(f"    {jev.explain_condition(cli, cond).render()}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("study_id")
    ap.add_argument(
        "--skip-labels", action="store_true", help="skip section 3 (one call per label)"
    )
    ap.add_argument("--only", choices=["assignment", "persona", "labels", "refusals"])
    ap.add_argument("--file", default=None, help="which data file, when the deposit has several")
    args = ap.parse_args()

    files = data_files_for(args.study_id)
    if not files:
        sys.exit(f"no .sav/.dta under data/raw/{args.study_id}/ — fetch it first")

    if args.file:
        matches = [p for p in files if args.file in str(p)]
        if not matches:
            sys.exit(f"--file {args.file!r} matches none of: {[p.name for p in files]}")
        path = matches[0]
    else:
        path = files[0]

    try:
        cli = jev.client()
    except jev.JevUnavailableError as exc:
        sys.exit(str(exc))

    ds = spss.read(path)
    print(f"{args.study_id}: {path.name}  ({ds.df.shape[0]:,} rows x {ds.df.shape[1]} columns)")
    if len(files) > 1:
        print(
            f"\n  ** THIS DEPOSIT HAS {len(files)} DATA FILES. Reporting on the one above. **\n"
            + "\n".join(
                f"       {'->' if p == path else '  '} {p.relative_to(RAW / args.study_id)}"
                f"  ({p.stat().st_size / 1e6:.1f} MB)"
                for p in files
            )
            + "\n     Several files usually means several sub-experiments, which is a scope\n"
            "     decision for you: re-run with --file <part of the name> for the others."
        )
    print(f"\nquestionnaires: {[p.name for p in questionnaires(args.study_id)] or 'NONE FOUND'}")

    want = args.only
    if want in (None, "assignment"):
        report_assignment(cli, ds)
    if want in (None, "persona"):
        report_persona(cli, ds)
    if want == "labels" or (want is None and not args.skip_labels):
        cols = [c for c in ds.df.columns if plausible(str(c))]
        report_labels(cli, ds, cols[:40])
    if want in (None, "refusals"):
        report_refusals(cli, args.study_id)

    print(
        "\nNone of the above is a decision. Write what you accept into the recipe,\n"
        "with the confidence beside it, and say in `notes` what you overruled."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
