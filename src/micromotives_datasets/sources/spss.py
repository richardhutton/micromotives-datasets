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


# Codepoints U+0080-U+009F. In Unicode these are unprintable C1 controls that no
# survey label legitimately contains; in Windows-1252 the same byte values are
# smart quotes, dashes, bullets and ellipses. So seeing one after a decode is
# near-proof that a cp1252 file was read as something else.
_C1 = frozenset(chr(c) for c in range(0x80, 0xA0))


def _control_characters(meta: Any) -> list[str]:
    """Labels containing C1 control characters, which means the decode is wrong."""
    bad: list[str] = []
    for labels in meta.variable_value_labels.values():
        bad.extend(str(v) for v in labels.values() if _C1 & set(str(v)))
    bad.extend(str(v) for v in meta.column_names_to_labels.values() if v and _C1 & set(str(v)))
    return bad


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
    #
    # ORDER IS LOAD-BEARING, and getting it wrong cost 5,279 of PZB01G's 5,333
    # rows (99%) before a checker read one rendered row and saw
    # "Own \x96 with a mortgage" where an en dash belonged.
    #
    # `latin1` maps every one of the 256 byte values to a codepoint, so it NEVER
    # raises — which made it not a fallback but a wall. Everything after it in
    # this tuple was unreachable, and a Windows-1252 file (the standard output of
    # every UK survey house here) decoded "successfully" with its smart quotes,
    # dashes and ellipses turned into raw C1 control characters. Those then
    # travelled all the way into the persona text a model would be shown.
    #
    # `cp1252` now comes first among the fallbacks because it is the STRICTER
    # test: it leaves five byte values undefined (0x81, 0x8D, 0x8F, 0x90, 0x9D)
    # and raises on them, so a file that is genuinely Latin-1 still falls through
    # to `latin1` below. A permissive codec must never be tried before a strict
    # one, or the strict one is decoration.
    last: Exception | None = None
    for encoding in (None, "cp1252", "latin1", "utf-8-sig", "iso-8859-15"):
        try:
            df, meta = reader(str(p)) if encoding is None else reader(str(p), encoding=encoding)
        except (UnicodeDecodeError, pyreadstat.ReadstatError) as exc:
            last = exc
            continue
        if control := _control_characters(meta):
            # A decode that "worked" and produced control characters did not
            # work. Ordering alone cannot be trusted to prevent this — the next
            # odd codepage will not be in the tuple at all — so the result is
            # checked rather than the method.
            last = ValueError(
                f"{encoding or 'utf-8'} decoded {p.name} but produced C1 control "
                f"characters in {len(control)} label(s), e.g. {control[0]!r}. That is "
                f"a mis-decode, not text."
            )
            continue
        break
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
