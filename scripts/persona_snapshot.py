"""Pin every persona value in the corpus, so a crosswalk change cannot corrupt it quietly.

The persona layer is the one part of a row with **no answer key at all**. A
condition can be checked against the questionnaire, a response against the
codebook, a whole study against a published table — `QQM5MC` reproduces Sorace &
Hobolt's Table 1 to three decimals. Nothing checks a persona. The crosswalk was
built once, reviewed once, and from then on the only thing standing between it
and a silent corruption was that nobody touched it.

That is about to stop being true: the UK layer adds a second vocabulary to files
the US rows are harmonised through. So this records what the corpus says TODAY,
and reports every change.

**It is a diff, not a verdict.** It cannot tell you a mapping is right — nothing
can, which is why the bridge file is small enough to read. What it can tell you
is that a change you did not intend has happened, which is the failure this
project actually keeps having: `a42yg`'s religion label was fixed in one recipe
and left standing in seven others for ~27,900 rows, and the reason that survived
review is that no artefact anywhere said what the corpus's religion labels were.

Writing the first snapshot immediately found two:

  * `religion_attendance` (`ye2ej`, 12,971 rows) and `religious_attendance`
    (five recipes) are the same question with identical value sets under two
    key spellings. A consumer filtering the merged corpus on either one loses
    the other silently.
  * `sexual_orientation` (`yv2ta`) and `sexual_orientation_self` (`ye2ej`),
    likewise.

Neither is visible in a single study. Both are obvious in one sorted list.

    uv run python scripts/persona_snapshot.py            # compare, exit 1 on drift
    uv run python scripts/persona_snapshot.py --write    # accept the current state
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
PROCESSED = REPO / "data" / "processed"
SNAPSHOT = REPO / "data" / "catalog" / "persona_snapshot.json"

# Values are compared as sets; a count would make the snapshot churn on every
# rebuild for reasons that are not about vocabulary.


def read_corpus() -> dict[str, dict[str, list[str]]]:
    """{field: {value: [studies that emit it]}}, over every built parquet.

    Reads only the `persona` column, and only its DISTINCT values — the corpus
    is 290,280 rows and perhaps 300 persona values.
    """
    out: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for path in sorted(PROCESSED.glob("*.parquet")):
        study = path.stem
        frame = pd.read_parquet(path, columns=["persona"])
        for blob in frame["persona"].unique():
            person = json.loads(blob)
            for key, value in person.items():
                if key == "extra":
                    for extra_key, extra_value in value.items():
                        if extra_value:
                            out[f"extra.{extra_key}"][str(extra_value)].add(study)
                elif isinstance(value, str) and value:
                    out[key][value].add(study)
    return {f: {v: sorted(s) for v, s in sorted(vals.items())} for f, vals in sorted(out.items())}


def diff(old: dict, new: dict) -> list[str]:
    """Every difference, as lines. Empty means the vocabulary is unchanged."""
    lines: list[str] = []
    for field in sorted(set(old) | set(new)):
        before, after = old.get(field, {}), new.get(field, {})
        if field not in old:
            lines.append(f"+ FIELD {field}  ({len(after)} values, new)")
            continue
        if field not in new:
            lines.append(f"- FIELD {field}  ({len(before)} values, gone)")
            continue
        for value in sorted(set(before) | set(after)):
            if value not in before:
                lines.append(f"+ {field}: {value!r}  <- {', '.join(after[value])}")
            elif value not in after:
                lines.append(f"- {field}: {value!r}  (was in {', '.join(before[value])})")
            elif before[value] != after[value]:
                gained = sorted(set(after[value]) - set(before[value]))
                lost = sorted(set(before[value]) - set(after[value]))
                lines.append(f"~ {field}: {value!r}  +{gained} -{lost}")
    return lines


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--write", action="store_true", help="accept the current corpus as the baseline"
    )
    args = ap.parse_args()

    if not list(PROCESSED.glob("*.parquet")):
        sys.exit(f"no builds in {PROCESSED} — run `mmds build` for the recipes first")

    current = read_corpus()
    total = sum(len(v) for v in current.values())

    if args.write:
        SNAPSHOT.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
        print(f"wrote {SNAPSHOT.relative_to(REPO)}: {len(current)} fields, {total} values")
        return 0

    if not SNAPSHOT.exists():
        sys.exit(f"{SNAPSHOT.relative_to(REPO)} does not exist — run with --write to create it")

    changes = diff(json.loads(SNAPSHOT.read_text()), current)
    print(f"persona vocabulary: {len(current)} fields, {total} values")
    if not changes:
        print("unchanged.")
        return 0
    print(f"\n{len(changes)} CHANGES — read every line before accepting:\n")
    for line in changes:
        print(f"  {line}")
    print(
        "\nNothing here says a change is wrong. It says a change happened, which is "
        "\nwhat no artefact in this repo could say before. Accept with --write."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
