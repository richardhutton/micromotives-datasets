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
import re
import subprocess
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from micromotives_datasets import jev  # noqa: E402
from micromotives_datasets.pipeline.qc import reads_as_a_non_answer  # noqa: E402
from micromotives_datasets.sources import quex, spss  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw"
# Converted instruments live beside the raw data, which is gitignored:
# they are derived from licensed deposits and must not enter git either.
CONVERTED = RAW / "_converted"

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


def questionnaires(study_id: str, only: str | None = None) -> list[Path]:
    """Every instrument in the deposit, as plain text.

    `only` scopes to one sub-study, the same substring `--file` applies to the
    data. `35M5CV` bundles SIX separately fielded surveys in one folder, and
    without this `--file lodger` reported on the BBC instrument too — harmless
    there because neither parses, but a deposit where one sub-study's
    directives resolve and another's do not would be collapsed into a single
    undifferentiated verdict, which is the kind of answer that reads as clean.

    TESS deposits ship `.txt`. Every Harvard Dataverse deposit so far ships
    `.docx`, and globbing only `.txt` did not FAIL on `EFXNLX` — it found
    nothing, and section 4 then printed "every conditional directive in this
    deposit parses", which is true of the empty set and means nothing. A clean
    verdict over zero files is the most dangerous output this script can
    produce, so `.doc`/`.docx` are converted here (`textutil`, as CLAUDE.md
    already prescribes) and section 4 refuses to report a pass over nothing.
    """
    folder = RAW / study_id
    found = [
        p
        for p in sorted(folder.rglob("*.txt"))
        if not p.name.startswith("._") and "Response Rate" not in p.name
    ]
    for doc in sorted(folder.rglob("*.doc*")):
        if doc.name.startswith("._") or doc.suffix.lower() not in {".doc", ".docx"}:
            continue
        plain = CONVERTED / f"{study_id}__{doc.stem}.txt"
        if not plain.exists():
            plain.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [
                    "/usr/bin/textutil",
                    "-convert",
                    "txt",
                    "-output",
                    str(plain),
                    str(doc),
                ],
                check=True,
            )
        found.append(plain)
    if only:
        found = [p for p in found if only in p.name]
    return found


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


# Above this many labels, the report says so rather than skipping in silence.
# `label_is_a_non_answer` is one call per label with a three-option Choice, so
# there is no option-list ceiling here — the cap is about cost, not correctness,
# and the old value of 20 sat just under a 22-level education ladder.
MAX_LABELS = 60


def report_labels(cli: object, ds: spss.Dataset, mapped: list[str]) -> None:
    section("3. WHICH VALUE LABELS ARE NON-ANSWERS?")
    print(
        "  For `persona_missing` (leave the field empty) vs `persona_label_rewrite`\n"
        "  (a real answer wearing scripting boilerplate). QC rule 12 keeps a keyword\n"
        "  regex as a backstop; this is the judgement.\n"
        "\n"
        "  Every label on every mapped variable is asked about. What prints is what is\n"
        "  ACTIONABLE or SURPRISING: anything Jev calls a non-answer, and anything where\n"
        "  Jev and the regex disagree. A plain answer the regex also thought was plain\n"
        "  tells you nothing, so it is counted rather than listed.\n"
    )
    asked = 0
    disagreements = 0
    for var in mapped:
        labels = [str(v) for v in (ds.value_labels.get(var) or {}).values()]
        if not labels:
            continue
        if len(labels) > MAX_LABELS:
            # Said out loud. The previous version skipped at 20 IN SILENCE, which
            # took out `QQM5MC`'s 22-level education ladder — the richest persona
            # variable in the study and the one the crosswalk turns on. A variable
            # with many labels is where a mistake is most likely to hide, so a cap
            # that hides it is the wrong way round.
            print(f"  {var}: SKIPPED — {len(labels)} labels, over the {MAX_LABELS} cap")
            continue

        verdicts = jev.label_is_a_non_answer(cli, var, labels)
        asked += len(labels)
        lines = []
        for lab, v in verdicts.items():
            by_jev_is_an_answer = v.value == "answer"
            by_regex_is_a_non_answer = reads_as_a_non_answer(lab)
            disagrees = by_jev_is_an_answer == by_regex_is_a_non_answer
            if disagrees:
                disagreements += 1
            # A plain answer that the regex also left alone is the boring majority.
            if by_jev_is_an_answer and not disagrees:
                continue
            flag = "  <- DISAGREES WITH THE REGEX" if disagrees else ""
            lines.append(f"    {v.render(repr(lab))}{flag}")
        if lines:
            print(f"  {var}:")
            print("\n".join(lines))

    print(f"\n  {asked} labels asked about; {disagreements} where Jev and the regex differ.")
    print(
        "  A disagreement is the reason to ask at all. The regex cannot see that\n"
        "  'Northern Ireland' is a real answer sitting in a drop list, or that\n"
        "  'Other Christian religion, please specify' is a real answer wearing an\n"
        "  instruction — and an earlier version of this report filtered Jev's verdicts\n"
        "  THROUGH that same regex, so the judgement could only ever confirm it."
    )


def report_refusals(cli: object, study_id: str, only: str | None = None) -> None:
    section("4. QUESTIONNAIRE DIRECTIVES `quex` WILL NOT PARSE")
    found = questionnaires(study_id, only)
    if not found:
        # A pass over zero files reads exactly like a pass over a clean deposit,
        # and that is how `EFXNLX` was reported clean having been scanned not at
        # all. Say what was checked, never report a verdict nothing earned.
        print(
            "  NOTHING SCANNED — no instrument found in this deposit.\n"
            "  This is NOT a pass. `quex` checked zero files, so it has said\n"
            "  nothing about whether a directive gates stimulus text. Either the\n"
            "  deposit ships no questionnaire — in which case docs/CONVENTIONS.md\n"
            "  makes it unbuildable, and that is the finding — or it ships one in\n"
            "  a form this script does not yet read. Find out which before writing\n"
            "  a recipe."
        )
        return
    refused: dict[str, None] = {}
    seen = 0
    looks_conditional = 0
    for path in found:
        text = path.read_text(errors="replace")
        # Anything that READS like routing, in whatever syntax. Counted apart
        # from what `quex` recognises, because the gap between the two numbers
        # is the thing worth knowing.
        looks_conditional += len(re.findall(r"[\[{][^\]}\n]{0,160}\bif\b", text, re.I))
        conds = [m.group(1) for m in quex._BLOCK_SHOW_IF.finditer(text)]
        for m in quex._INLINE.finditer(text):
            conds += [b.group("cond") for b in quex._BRANCH.finditer(m.group(1))]
        conds += [m.group("cond") for m in quex._IF_DISPLAY.finditer(text)]
        seen += len(conds)
        for c in conds:
            c = " ".join(c.split())
            try:
                quex.parse_condition(c)
            except quex.UnparsedConditionError:
                refused[c] = None
    if not seen:
        # "None refused" over zero directives is not "all parsed", it is "none
        # recognised". `EFXNLX` writes routing as `[QA2A if pdl.profile_GOR in
        # [...]]` and `{module conjoint1 if conjoint==1}` — a variable name
        # before the IF, and braces — so `quex`'s patterns match neither, and
        # the parser was never asked a single question.
        print(
            f"  NOTHING RECOGNISED — `quex` found 0 directives across "
            f"{len(found)} instrument(s), while a loose scan sees "
            f"{looks_conditional} that look like routing.\n"
            "  This is NOT a pass. If that second number is non-zero, this\n"
            "  deposit writes directives in a syntax `quex` does not read, and\n"
            "  nothing has been established about whether any of them gate\n"
            "  stimulus text. Read them by hand before writing the recipe."
        )
        return
    if not refused:
        print(f"  None — all {seen} directive(s) found in this deposit parse.")
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
    ap.add_argument(
        "--source",
        required=True,
        choices=["tess", "dataverse", "socsci210", "ukds"],
        help=(
            "whose material is about to be sent to TypeSafe. Required, with no default, "
            "because this script's whole job is to send variable labels, value labels and "
            "questionnaire routing text over the wire — and for a UKDS source that is "
            "exactly what the End User Licence forbids sharing. `ukds` is refused by "
            "jev.RESTRICTED; naming it wrongly to get past that is a lie, not a workaround."
        ),
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
        if len(matches) > 1:
            print(
                f"NOTE: --file {args.file!r} matches {len(matches)} files; using\n"
                f"      {matches[0].name}. The others were NOT inspected: "
                f"{[p.name for p in matches[1:]]}.\n"
                "      A deposit with several sub-experiments needs one run each.",
                file=sys.stderr,
            )
        path = matches[0]
    elif len(files) > 1:
        # Refuse rather than pick. Taking the LARGEST silently reported on
        # `nmg.dta` — a 277MB, 592-column panel wave — when the experiment lives
        # in `yougov.dta`, and every section of the report looked authoritative
        # about a file the maker had not chosen. Same family as the two fixes in
        # 3d92e08 and ad0002a: the tool must not produce a confident verdict
        # about something nobody selected.
        listing = "\n".join(
            f"      {p.name}  ({p.stat().st_size / 1_048_576:.1f} MB)" for p in files
        )
        sys.exit(
            f"{args.study_id} has {len(files)} data files and no --file given:\n"
            f"{listing}\n"
            "    Several files usually means several sub-experiments with different\n"
            "    columns. Choose one — this tool will not pick for you, because a\n"
            "    report about the wrong file reads exactly like a report about the\n"
            "    right one."
        )
    else:
        path = files[0]

    try:
        cli = jev.client(args.source)
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
    print(
        f"\nquestionnaires: "
        f"{[p.name for p in questionnaires(args.study_id, args.file)] or 'NONE FOUND'}"
    )

    want = args.only
    if want in (None, "assignment"):
        report_assignment(cli, ds)
    if want in (None, "persona"):
        report_persona(cli, ds)
    if want == "labels" or (want is None and not args.skip_labels):
        cols = [c for c in ds.df.columns if plausible(str(c))]
        report_labels(cli, ds, cols[:40])
    if want in (None, "refusals"):
        report_refusals(cli, args.study_id, args.file)

    print(
        "\nNone of the above is a decision. Write what you accept into the recipe,\n"
        "with the confidence beside it, and say in `notes` what you overruled."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
