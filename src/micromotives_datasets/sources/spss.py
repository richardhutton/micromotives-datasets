"""Read SPSS/Stata survey files into a dataframe plus label metadata.

Thin wrapper over pyreadstat. The only real work here is resolving numeric
codes to their value labels, which is what turns `PPGENDER == 2.0` into
"Female" for the persona text.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import pyreadstat


@dataclass
class Dataset:
    """A survey file: the rows, plus what the codes mean."""

    df: pd.DataFrame
    value_labels: dict[str, dict[float, str]]
    column_labels: dict[str, str]

    def label(self, var: str, value: Any) -> str:
        """Resolve a coded value to its label, falling back to the raw value."""
        try:
            fval = float(value)
        except (TypeError, ValueError):
            return str(value)
        labels = self.value_labels.get(var, {})
        if fval in labels:
            return labels[fval]
        # Integer-valued floats print as "42" not "42.0".
        return str(int(fval)) if fval == int(fval) else str(fval)


def read(path: str | Path) -> Dataset:
    """Read a .sav (SPSS) or .dta (Stata) file."""
    p = Path(path)
    suffix = p.suffix.lower()
    readers: dict[str, Any] = {
        ".sav": pyreadstat.read_sav,
        ".dta": pyreadstat.read_dta,
        ".por": pyreadstat.read_por,
    }
    reader = readers.get(suffix)
    if reader is None:
        raise ValueError(f"unsupported data file type: {p.name} (expected .sav/.dta/.por)")

    # Older SPSS files are frequently written in a Windows codepage rather than
    # UTF-8, and pyreadstat raises rather than substituting. Fall back through
    # the usual suspects instead of losing the study.
    last: Exception | None = None
    for encoding in (None, "latin1", "cp1252", "utf-8-sig", "iso-8859-15"):
        try:
            df, meta = reader(str(p)) if encoding is None else reader(str(p), encoding=encoding)
            break
        except (UnicodeDecodeError, pyreadstat.ReadstatError) as exc:
            last = exc
    else:
        # pandas' Stata reader recovers some files pyreadstat cannot decode at
        # any encoding. It gives variable labels but not value labels, which is
        # enough to inspect and screen a study; a recipe that needs value labels
        # will have to declare them itself.
        if suffix == ".dta":
            try:
                return _read_dta_with_pandas(p)
            except Exception as exc:
                last = exc
        raise ValueError(f"could not decode {p.name}: {last}") from last
    return Dataset(
        df=df,
        value_labels=dict(meta.variable_value_labels),
        # Some columns carry no label; drop those rather than widen the type.
        column_labels={k: v for k, v in meta.column_names_to_labels.items() if v is not None},
    )


def _read_dta_with_pandas(path: Path) -> Dataset:
    """Last-resort Stata reader for files pyreadstat cannot decode.

    Returns variable labels but no value labels — pandas does not expose them
    in a comparable form. Enough to inspect and screen a study; a recipe built
    on such a file must declare its own codings.
    """
    with pd.io.stata.StataReader(str(path)) as reader:
        df = reader.read()  # type: ignore[attr-defined]  # present at runtime
        labels = reader.variable_labels()
    return Dataset(
        df=df,
        value_labels={},
        column_labels={k: v for k, v in labels.items() if v},
    )
