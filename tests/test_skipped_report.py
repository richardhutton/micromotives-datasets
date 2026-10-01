"""`docs/SKIPPED.md` must add up, and must stay in step with the recipes.

CLAUDE.md requires every unbuilt source to be logged with a reason, and says a
reason there is a decision that can be revisited. That only works if the file is
current and its numbers are true — a generated report nobody reconciles is worse
than no report, because it reads authoritative.

Both failures here were real, and both arrived quietly:

  * It was SIX studies stale. The contract says "re-run it when the catalogue or
    a screen changes"; nothing enforced it, so nothing ran it.
  * Its headline disagreed with its own list the moment a UK study was built.
    `QQM5MC` comes from Harvard Dataverse, not the 202 TESS foundation sources,
    so counting every recipe in the numerator gave "25 of 202 built" above "178
    remaining" — 203 sources in a 202-source catalogue. The corpus is bigger
    than this catalogue now, and that is the first thing that noticed.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKIPPED = REPO / "docs" / "SKIPPED.md"
CATALOG = REPO / "data" / "catalog" / "tess_uk_foundation_sources.csv"
RECIPES = REPO / "recipes"


def _headline() -> tuple[int, int, int]:
    text = SKIPPED.read_text()
    built, total = (int(x) for x in re.search(r"(\d+) of (\d+) catalogued", text).groups())  # type: ignore[union-attr]
    remaining = int(re.search(r"remaining (\d+)", text).group(1))  # type: ignore[union-attr]
    return built, remaining, total


def test_the_headline_adds_up() -> None:
    """built + remaining == the catalogue, or one of the three is wrong."""
    built, remaining, total = _headline()
    assert built + remaining == total, (
        f"{built} built + {remaining} remaining = {built + remaining}, but the "
        f"catalogue holds {total}. Re-run `uv run python scripts/skipped_report.py`."
    )


def test_the_report_is_not_stale() -> None:
    """Every catalogued recipe is counted as built.

    Checked against `recipes/`, which is the only record of what has been built,
    rather than against a number written down somewhere and left behind.
    """
    with open(CATALOG) as fh:
        catalogued = {r["osf_code"] for r in csv.DictReader(fh)}
    recipes = {p.stem.split("_")[0] for p in RECIPES.glob("*.yaml")}
    built, _, _ = _headline()
    assert built == len(recipes & catalogued), (
        f"the report says {built} catalogued sources are built; `recipes/` holds "
        f"{len(recipes & catalogued)}. Re-run `uv run python scripts/skipped_report.py`."
    )


def test_sources_built_from_outside_the_catalogue_are_named() -> None:
    """A study the catalogue does not contain must still be visible somewhere.

    Otherwise the UK layer is invisible in the one document whose job is saying
    what is and is not built.
    """
    with open(CATALOG) as fh:
        catalogued = {r["osf_code"] for r in csv.DictReader(fh)}
    outside = {p.stem.split("_")[0] for p in RECIPES.glob("*.yaml")} - catalogued
    text = SKIPPED.read_text()
    missing = sorted(code for code in outside if code not in text)
    assert not missing, (
        f"built but named nowhere in SKIPPED.md: {missing}. Re-run "
        "`uv run python scripts/skipped_report.py`."
    )
