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
    if suffix == ".sav":
        df, meta = pyreadstat.read_sav(str(p))
    elif suffix == ".dta":
        df, meta = pyreadstat.read_dta(str(p))
    elif suffix == ".por":
        df, meta = pyreadstat.read_por(str(p))
    else:
        raise ValueError(f"unsupported data file type: {p.name} (expected .sav/.dta/.por)")
    return Dataset(
        df=df,
        value_labels=dict(meta.variable_value_labels),
        # Some columns carry no label; drop those rather than widen the type.
        column_labels={k: v for k, v in meta.column_names_to_labels.items() if v is not None},
    )
