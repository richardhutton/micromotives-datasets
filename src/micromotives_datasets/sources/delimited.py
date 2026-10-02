"""Read a delimited survey export (`.tab`, `.tsv`, `.csv`) into the same shape.

Some deposits ship no binary statistical file at all. `PMV0TG` is the first here:
248,576 rows in a tab-delimited text file, no `.sav`, no `.dta`. `recipe_prep.py`
refused it outright, and so would the pipeline.

**The important difference is not the delimiter, it is that the codes are already
resolved.** A `.sav` stores `2.0` plus a dictionary saying 2 means "Female"; a
`.tab` exported from the same study just stores "Female". So `value_labels` comes
back EMPTY, and that is correct rather than missing — `Dataset.label()` already
falls back to the raw value when it will not parse as a number, so a text cell
passes through untouched. Anyone later "fixing" the empty dictionary would be
inventing a mapping the file never had.

`column_labels` is empty too, and that one IS a real loss: a delimited file has
only a header row, so the question wording that a `.sav` carries per column
simply is not there. A recipe built on one of these has no variable labels to
quote and must take its wording from the instrument, which is where
`docs/CONVENTIONS.md` says it should come from anyway.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .spss import Dataset

SEPARATORS = {".tab": "\t", ".tsv": "\t", ".csv": ",", ".txt": "\t"}


def read(path: str | Path, *, sep: str | None = None) -> Dataset:
    """Read a delimited export. `sep` overrides the guess from the extension."""
    p = Path(path)
    if sep is None:
        sep = SEPARATORS.get(p.suffix.lower())
    if sep is None:
        raise ValueError(
            f"unsupported delimited file type: {p.name} "
            f"(expected one of {sorted(SEPARATORS)}, or pass sep=)"
        )

    # Default NA handling is deliberate and load-bearing. `PMV0TG` uses BOTH an
    # empty cell and the literal string "NA" for missing, in different columns of
    # the same file — pandas treats both as missing by default, and a stricter
    # reader (`keep_default_na=False`) would silently admit "NA" as a real
    # answer. That is the shape of ledger 109, where an unlabelled code was the
    # modal response of a study and nothing noticed.
    last: Exception | None = None
    for encoding in ("utf-8", "utf-8-sig", "latin1", "cp1252"):
        try:
            df = pd.read_csv(p, sep=sep, encoding=encoding, low_memory=False)
            break
        except UnicodeDecodeError as exc:
            last = exc
    else:
        raise ValueError(f"could not decode {p.name}: {last}") from last

    return Dataset(df=df, value_labels={}, column_labels={})
