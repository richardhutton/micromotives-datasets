"""Source adapters. Each module exposes an iterator that yields `Row` objects
for one data source, so the pipeline can treat every source uniformly.

Planned adapters (see docs/SocSci-UK_MASTER.md sections 3-5):

- socsci210       PULL — melt studies already reconstructed in SocSci210.
- tess            BUILD — reconstruct UK-appropriate TESS studies from OSF.
- dataverse       BUILD — UK CC0 Harvard Dataverse experiments.
- innovation_panel BUILD — Understanding Society Innovation Panel (UKDS SN 6849).

Each adapter is responsible for its own licensing constraints; safeguarded
UKDS data never leaves the machine.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from ..schema import Row
from . import delimited, excel, spss

SourceIterator = Iterator[Row]

__all__ = ["SourceIterator", "read_any"]

_BINARY = {".sav", ".dta", ".por"}


def read_any(path: str | Path) -> spss.Dataset:
    """Read a survey file, choosing the reader by extension.

    Deposits are not uniform about this and the pipeline should not care:
    `QQM5MC` and `EFXNLX` ship SPSS, `TLT65Z` ships Stata, and `PMV0TG` ships
    248,576 rows of tab-delimited text with no statistical file at all. Both
    readers return the same `Dataset`, so everything downstream is identical —
    the only real difference is that a delimited export has already resolved its
    codes to text, so it carries no value labels, and `Dataset.label()` passes
    text straight through.

    One dispatcher rather than a branch at the call site, for the reason
    `jev.py` and `embed.py` are each one door: a second place that decides how
    to open a data file is a second place to get it wrong.
    """
    suffix = Path(path).suffix.lower()
    if suffix in _BINARY:
        return spss.read(path)
    if suffix in delimited.SEPARATORS:
        return delimited.read(path)
    if suffix in excel.SUFFIXES:
        return excel.read(path)
    raise ValueError(
        f"no reader for {Path(path).name} — expected one of "
        f"{sorted(_BINARY | set(delimited.SEPARATORS) | excel.SUFFIXES)}"
    )
