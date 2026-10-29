"""The Innovation Panel experiment catalogue: its record shape and how to read it.

UKDS **SN 6849** — Understanding Society: Innovation Panel, waves 1-17, 2008-2024.
Its User Guide catalogues 93 experiments, and `data/catalog/innovation_panel_experiments.json`
is our screening pass over all of them: what each one is, and whether we intend to
build it.

The shape lives here rather than in either script because two of them read the
file — `scripts/innovation_panel_catalogue.py` writes it, `scripts/innovation_panel_table.py`
renders it, and `tests/test_innovation_panel_catalogue.py` checks it — and a
record shape defined three times is a record shape that disagrees with itself.

Reading this file does NOT touch the licensed data. The catalogue holds only the
published User Guide's prose and the allocation variable names it prints; the
`.dta` files it describes stay in gitignored `data/raw/ukds_6849/`, and
`jev.RESTRICTED` refuses `source="ukds"` so none of it can reach a model.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

CATALOGUE = (
    Path(__file__).resolve().parents[2] / "data" / "catalog" / "innovation_panel_experiments.json"
)

#: What a verdict means. `marginal` is "assessed and not decided", deliberately
#: not a third quality tier — it needs a ruling before it moves either way.
VERDICTS: dict[str, str] = {
    "build": "passes screening; the condition is text and the outcome is a respondent's answer",
    "marginal": "assessed and undecided; `reason` says what the open question is",
    "drop": "will not be built, and `reason` says why",
}


class Experiment(TypedDict):
    """One Innovation Panel experiment as the catalogue records it.

    `id`, `title`, `waves`, `description` and `allocation_vars` are parsed from
    the User Guide. `category`, `verdict`, `reason` and `vignette` are judgement.

    Spelled out as a TypedDict rather than left a bare dict because the fields
    are not all strings — `vignette` is a bool and `allocation_vars` a list — so
    `dict[str, str]` would be a lie and `dict[str, object]` makes every read
    need a cast.
    """

    #: Section number in the User Guide, e.g. "9.30". The stable identifier.
    id: str
    title: str
    category: str
    #: The guide's own wave column, e.g. "5, 6" or "1-5" or "All".
    waves: str
    verdict: str
    #: Why, in prose. Empty is permitted ONLY for `build`, where it would merely
    #: restate the title; a `marginal` or `drop` with no reason is an open
    #: question with no owner.
    reason: str
    #: The User Guide's own description of the experiment.
    description: str
    #: True where the stimulus is researcher-written prose shown word-for-word.
    #: A field rather than a note in `reason`, because it was a note once and a
    #: tidy-up silently deleted it from three of the four.
    vignette: bool
    #: Allocation variables the guide names outright, e.g. ["e_ff_lifesatw5"].
    #: Empty means the guide did not name one, not that none exists.
    allocation_vars: list[str]


def load(path: Path | None = None) -> list[Experiment]:
    """The catalogue, in the User Guide's own order."""
    records: list[Experiment] = json.loads((path or CATALOGUE).read_text())
    return records


def by_verdict(verdict: str, path: Path | None = None) -> list[Experiment]:
    """Every experiment with the given verdict.

    Raises on an unknown verdict rather than returning nothing, because a typo
    that silently yields an empty list reads as "there are none of those".
    """
    if verdict not in VERDICTS:
        raise ValueError(f"unknown verdict {verdict!r}; expected one of {sorted(VERDICTS)}")
    return [r for r in load(path) if r["verdict"] == verdict]
