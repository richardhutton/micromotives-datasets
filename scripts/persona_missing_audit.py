"""Every declared missing-code, resolved to the label it actually drops.

`persona_missing` says "this code carries no answer, so leave the field empty
rather than rendering its label". Getting it wrong in one direction renders
"Religion: Refused" into a persona; getting it wrong in the other **silently
deletes a real answer**, and nothing downstream can tell. QC cannot check it —
the code is gone by the time a row exists — and a checker found one by reading
the .dta's own value labels, which is the only place the answer lives.

`QQM5MC` declared `Region_GOR: [12, 13, ...]` where 12 is "Northern Ireland", a
real region. It drops nothing today, because this deposit has no respondent from
Northern Ireland at all — which is exactly why it survived. **An inert wrong
declaration is the shape that outlives review**, and it would have deleted the
region of every NI respondent the moment a refetch or another UK deposit had one.

So this resolves all 120 declared codes across 21 recipes against their own data
file and prints what each one drops, with how many respondents hold it. Three
things to read for:

  SUSPECT   the label does not look like a non-answer. Read it.
  UNUSED    nothing in this file carries the code, so the declaration has never
            been exercised and could say anything.
  (ok)      the label reads as a refusal, a don't-know, or a not-asked.

The classifier is a keyword list and is deliberately crude — it exists to ORDER
the reading, not to replace it. 120 lines is a readable list; the point is that
somebody reads it.

    uv run python scripts/persona_missing_audit.py            # offline, the regex
    uv run python scripts/persona_missing_audit.py --jev      # ask the judge
    uv run python scripts/persona_missing_audit.py QQM5MC     # one study
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import yaml

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from micromotives_datasets import jev  # noqa: E402
from micromotives_datasets.pipeline.qc import reads_as_a_non_answer  # noqa: E402
from micromotives_datasets.sources import spss  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw"
RECIPES = REPO / "recipes"


def data_file_for(study: str) -> Path | None:
    folder = RAW / study
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


def audit(recipe_path: Path, cli: object | None = None) -> list[tuple[str, str, str, int, str]]:
    """(variable, code, label, n_respondents, verdict) for each declared code.

    With a Jev client, the judgement is Jev's and the regex is only a
    cross-check; without one it is the regex alone. Both paths exist on
    purpose. UKDS safeguarded data is End User Licence — never sent to an
    external service, instrument included — so the offline path is the only
    one those deposits will ever have, and it must stay good enough to run.
    """
    recipe = yaml.safe_load(recipe_path.read_text())
    declared = recipe.get("persona_missing") or {}
    if not declared:
        return []
    path = data_file_for(recipe["study_id"])
    if path is None:
        return []
    ds = spss.read(path)
    by_upper = {str(c).upper(): c for c in ds.df.columns}

    out = []
    for var, codes in sorted(declared.items()):
        col = by_upper.get(var.upper())
        if col is None:
            for code in codes:
                out.append((var, str(code), "<variable not in file>", 0, "SUSPECT"))
            continue
        labels = ds.value_labels.get(col, {})
        counts = ds.df[col].value_counts()
        # One Jev pass per variable, over ALL its labels — a label is only
        # readable against its siblings, and asking about the declared codes
        # alone would hide the question "is this one unlike the others".
        judged: dict[str, str] = {}
        if cli is not None:
            declared_labels = [labels.get(float(c), "") for c in codes]
            if any(declared_labels):
                every = [str(v) for v in labels.values()]
                judged = {
                    lab: v.value for lab, v in jev.label_is_a_non_answer(cli, var, every).items()
                }
        for code in codes:
            label = labels.get(float(code), "")
            n = int(counts.get(float(code), 0))
            if label and label in judged:
                # Jev decides; the regex becomes a second opinion worth printing
                # when it differs, because a disagreement is where either is wrong.
                by_jev = judged[label] != "answer"
                by_regex = reads_as_a_non_answer(label)
                verdict = "(ok)" if by_jev else "SUSPECT"
                if by_jev != by_regex:
                    verdict += " [regex differs]"
                if n == 0 and not verdict.startswith("SUSPECT"):
                    verdict = "UNUSED" + verdict[4:]
                out.append((var, str(code), label, n, verdict))
                continue
            if not label:
                # No label at all: a bare sentinel like -1 or 9999 that the file
                # never names. Legitimate and common, but say so.
                verdict = "(unlabelled)" if n == 0 else "(unlabelled, in use)"
            elif reads_as_a_non_answer(label):
                verdict = "(ok)"
            else:
                verdict = "SUSPECT"
            if n == 0 and verdict != "SUSPECT":
                verdict = "UNUSED"
            out.append((var, str(code), label, n, verdict))
    return out


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--jev"]
    use_jev = "--jev" in sys.argv[1:]
    cli = jev.client("tess") if use_jev else None
    if use_jev:
        print("Asking Jev per variable. The regex becomes a second opinion.\n")
    wanted = set(args)
    paths = sorted(RECIPES.glob("*.yaml"))
    if wanted:
        paths = [p for p in paths if p.stem.split("_")[0] in wanted or p.stem in wanted]

    suspects: list[str] = []
    unused = 0
    checked = 0
    for path in paths:
        rows = audit(path, cli)
        if not rows:
            continue
        print(f"\n### {path.stem}")
        for var, code, label, n, verdict in rows:
            checked += 1
            if verdict == "SUSPECT":
                suspects.append(f"{path.stem}  {var}={code}  {label!r}  ({n} respondents)")
            if verdict == "UNUSED":
                unused += 1
            mark = "  <<<" if verdict == "SUSPECT" else ""
            print(f"  {var:24s} {code:>6s}  n={n:<6d} {verdict:20s} {label[:60]!r}{mark}")

    print(f"\n{checked} declared codes checked.")
    print(f"{unused} are UNUSED — never exercised by this deposit, so never tested.")
    if suspects:
        print(f"\n{len(suspects)} SUSPECT — a label that does not read as a non-answer:\n")
        for line in suspects:
            print(f"  {line}")
        print("\nRead each one. A real answer in this list is deleted silently.")
        return 1
    print("No suspects.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
