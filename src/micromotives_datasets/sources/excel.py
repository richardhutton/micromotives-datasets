"""Read an Excel survey export (`.xlsx`) into the same shape as a `.sav`.

`k7tw5` (the Cambridge snack warning-label study, the first image experiment here)
ships its data only as a spreadsheet, and its randomised arm is a TEXT column:
"Bowel cancer 2", not a code. Every recipe declares its arms by integer code, so
the text has to become codes somewhere.

It happens here, and only here, by doing what a `.sav` already does: each text
column is stored as integer codes PLUS a value-label dictionary giving every code
its original string. Nothing is lost, `Dataset.label()` turns a code straight back
into the source's own words, and a recipe can be reviewed against those words.

The codes are assigned 1..n in sorted order of the (whitespace-stripped) text, so
the same file always yields the same codes. A recipe should still never TYPE one
of these codes by hand: the generator that writes it looks each code up by its
label, so a code that moved would fail loudly rather than point at the wrong arm.

Two details the k7tw5 file forced:

- Whitespace. Its label column holds both "Obesity 2" and "Obesity 2 " (two
  rows carry a trailing space). That is typography, not a different arm, so values
  are stripped before coding and the two become one code.
- Sentinels inside text columns. The same column holds the strings and the
  number -888 ("no answer"). A number in a text column keeps its own value as its
  code, unlabelled, so the recipe's `missing_codes` sees exactly the source's -888
  and nothing is relabelled.

Purely numeric columns pass through untouched.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .spss import Dataset

SUFFIXES = {".xlsx"}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _encode(column: pd.Series) -> tuple[pd.Series, dict[float, str]]:
    """Text -> codes 1..n (sorted, stripped); numbers keep their value; blanks stay blank."""
    texts = sorted({str(v).strip() for v in column.dropna() if not _is_number(v)})
    code_of = {t: float(i) for i, t in enumerate(texts, start=1)}
    clashes = {float(v) for v in column.dropna() if _is_number(v) and float(v) in code_of.values()}
    if clashes:
        # A real number that collides with an assigned code would make two
        # different answers one code. Never seen; refuse rather than guess.
        raise ValueError(
            f"column {column.name!r} mixes text with numbers {sorted(clashes)} that "
            "collide with the codes assigned to its text"
        )

    def code(v: Any) -> float | None:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        if _is_number(v):
            return float(v)
        return code_of[str(v).strip()]

    labels = {c: t for t, c in code_of.items()}
    return column.map(code).astype("float64"), labels


def read(path: str | Path, *, sheet: str | int = 0) -> Dataset:
    """Read one sheet of a spreadsheet, coding its text columns like a `.sav`."""
    df = pd.read_excel(Path(path), sheet_name=sheet)
    value_labels: dict[str, dict[float, str]] = {}
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]) and any(
            not _is_number(v) for v in df[col].dropna()
        ):
            df[col], labels = _encode(df[col])
            value_labels[str(col)] = labels
    return Dataset(df=df, value_labels=value_labels, column_labels={})
