"""Which persona values fall outside the canonical vocabulary.

Separate from `pipeline/qc.py` only to keep that module free of a dependency on
the catalog: QC is otherwise pure, taking rows and a recipe and reading nothing
from disk. This is the one check that needs to know what the agreed vocabulary
IS, so the disk access is isolated here.
"""

from __future__ import annotations

from collections import defaultdict

from .persona.crosswalk import Crosswalk
from .schema import Row


def unmapped_values(rows: list[Row]) -> dict[str, set[str]]:
    """Persona field -> values not in that field's canonical vocabulary.

    Silent when a field has no crosswalk yet, so adding one field at a time
    does not make every other field shout.
    """
    cw = Crosswalk.load()
    if not cw.maps:
        return {}
    stray: dict[str, set[str]] = defaultdict(set)
    # One pass over distinct (field, value) pairs rather than over every row:
    # a corpus has tens of thousands of rows and a handful of persona values.
    seen: set[tuple[str, str]] = set()
    for row in rows:
        for field_name, value in row.persona.model_dump().items():
            if field_name == "extra" or not isinstance(value, str) or not value:
                continue
            key = (field_name, value)
            if key in seen:
                continue
            seen.add(key)
            if cw.unmapped(field_name, value):
                stray[field_name].add(value)
    return dict(stray)
