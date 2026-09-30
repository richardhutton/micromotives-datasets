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

from ..schema import Row

SourceIterator = Iterator[Row]

__all__ = ["SourceIterator"]
