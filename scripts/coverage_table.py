"""What the corpus covers, and what it does not — counted, not asserted.

`docs/SocSci-UK_MASTER.md` §5a claims the UK layer has "genuine gaps" against
SocSci210's topics and names them in prose. Nothing stood behind that sentence.
This counts it instead.

Deliberately NOT an embedding. The TESS catalogue already carries a six-way
category on all 202 sources, so the gap question is answered exactly by a
crosstab — no model, no projection, no random seed, and the same input always
gives the same table. An embedding map earns its place where no category scheme
exists and the structure is finer than six buckets, which is a different job
(see `embed.py`).

`--json` writes `data/catalog/coverage.json`, which is TRACKED. That is the
point: the file diffs, so a build that moves the corpus shows up in review as a
changed line rather than as nothing at all. Same reasoning as
`persona_snapshot.py`.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
CATALOGUE = ROOT / "data" / "catalog" / "tess_uk_foundation_sources.csv"
UK_PROVENANCE = ROOT / "data" / "catalog" / "uk_dataverse_provenance.json"
RECIPES = ROOT / "recipes"
SNAPSHOT = ROOT / "data" / "catalog" / "coverage.json"

UNCATEGORISED = "(uncategorised)"


def built_study_ids() -> dict[str, list[str]]:
    """Study id -> the recipes that build it.

    Keyed on the recipe's own `study_id`, never on the filename. Three studies
    are built by more than one recipe — `9xw67` by two, `py9q3` by three,
    `yv2ta` by two — so 29 recipes are 25 studies, and counting files would
    over-count by four.
    """
    by_study: dict[str, list[str]] = defaultdict(list)
    for path in sorted(RECIPES.glob("*.yaml")):
        recipe = yaml.safe_load(path.read_text())
        by_study[str(recipe["study_id"])].append(path.name)
    return dict(by_study)


def _is_yes(value: str | None) -> bool:
    return (value or "").strip().lower() in {"yes", "true", "1"}


def catalogue_rows() -> list[dict[str, str]]:
    with CATALOGUE.open(newline="") as handle:
        return list(csv.DictReader(handle))


def uk_deposits() -> dict[str, dict[str, Any]]:
    if not UK_PROVENANCE.exists():
        return {}
    return json.loads(UK_PROVENANCE.read_text())


def collect() -> dict[str, Any]:
    built = built_study_ids()
    rows = catalogue_rows()
    uk = uk_deposits()

    # A catalogue row is identified by osf_code; that is the id the recipes use.
    by_category: dict[str, dict[str, Any]] = {}
    for row in rows:
        category = row.get("category") or UNCATEGORISED
        slot = by_category.setdefault(
            category,
            {
                "catalogued": 0,
                "built": 0,
                "in_socsci210": 0,
                "unbuilt_with_questionnaire": 0,
                "unscreened": 0,
            },
        )
        slot["catalogued"] += 1
        is_built = row.get("osf_code") in built
        if is_built:
            slot["built"] += 1
        if _is_yes(row.get("in_socsci210")):
            slot["in_socsci210"] += 1

        # `has_questionnaire` is a CATALOGUING-stage screen and is never
        # back-filled once a source is built — every built row is blank. So the
        # `yes` rows and the built rows are DISJOINT, and a ceiling of `yes`
        # alone divides by a population that cannot contain the numerator.
        # The ceiling is built + unbuilt-with-questionnaire. `skipped_report.py`
        # has always skipped built rows before reading this column; this script
        # did not, and reported 38% where the truth is 27%.
        if is_built:
            continue
        if _is_yes(row.get("has_questionnaire")):
            slot["unbuilt_with_questionnaire"] += 1
        elif not (row.get("has_questionnaire") or "").strip():
            slot["unscreened"] += 1

    catalogued_ids = {row.get("osf_code") for row in rows}
    outside = {sid: names for sid, names in built.items() if sid not in catalogued_ids}

    return {
        "categories": dict(sorted(by_category.items())),
        "built_studies": len(built),
        "built_recipes": sum(len(v) for v in built.values()),
        "catalogued_sources": len(rows),
        "built_outside_the_catalogue": dict(sorted(outside.items())),
        "uk_deposits": sorted(uk),
    }


def render(data: dict[str, Any]) -> str:
    lines: list[str] = []
    head = (
        f"{'category':<26}{'built':>6}{'ceiling':>9}{'of ceiling':>12}"
        f"{'left':>6}{'unscreened':>12}{'catalogued':>12}"
    )
    lines.append(head)
    lines.append("-" * len(head))
    totals = {"built": 0, "ceiling": 0, "left": 0, "unscreened": 0}
    for category, slot in data["categories"].items():
        built = slot["built"]
        left = slot["unbuilt_with_questionnaire"]
        ceiling = built + left
        share = f"{built / ceiling:.0%}" if ceiling else "-"
        lines.append(
            f"{category:<26}{built:>6}{ceiling:>9}{share:>12}{left:>6}"
            f"{slot['unscreened']:>12}{slot['catalogued']:>12}"
        )
        totals["built"] += built
        totals["ceiling"] += ceiling
        totals["left"] += left
        totals["unscreened"] += slot["unscreened"]
    lines.append("-" * len(head))
    lines.append(
        f"{'TOTAL':<26}{totals['built']:>6}{totals['ceiling']:>9}"
        f"{totals['built'] / totals['ceiling']:>11.0%}{totals['left']:>6}"
        f"{totals['unscreened']:>12}{data['catalogued_sources']:>12}"
    )
    lines.append("")
    lines.append(
        f"{data['built_studies']} studies from {data['built_recipes']} recipes. "
        "`ceiling` is built + unbuilt-with-a-questionnaire, because a source with no "
        "fielded questionnaire is not buildable at all under docs/CONVENTIONS.md. It "
        "is a FLOOR, not a true ceiling: `unscreened` rows have never been checked "
        "either way. Screening them moves the ceiling up, less any blocked for "
        "another reason — two currently are, needing US knowledge to answer."
    )
    outside = data["built_outside_the_catalogue"]
    if outside:
        lines.append("")
        lines.append(
            f"Built from OUTSIDE the catalogue ({len(outside)}): "
            + ", ".join(sorted(outside))
            + " — the UK layer, which is why the totals above do not reconcile "
            "with the corpus count."
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help=f"write {SNAPSHOT.relative_to(ROOT)} (tracked, so the diff is the report)",
    )
    args = parser.parse_args()

    data = collect()
    print(render(data))

    if args.json:
        SNAPSHOT.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        print(f"\nwrote {SNAPSHOT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
