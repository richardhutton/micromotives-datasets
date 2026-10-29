"""export.sample_fraction: the small test export keeps every study, on its own side."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location(
    "export", Path(__file__).resolve().parents[1] / "scripts" / "export.py"
)
assert spec and spec.loader
export = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export)


def _rows() -> pd.DataFrame:
    sizes = {"a": 1000, "b": 200, "c": 3}
    return pd.DataFrame(
        {"study": [s for s, n in sizes.items() for _ in range(n)], "i": range(sum(sizes.values()))}
    )


def test_keeps_each_studys_share_and_every_study() -> None:
    out = export.sample_fraction(_rows(), 0.1)
    assert out["study"].value_counts().to_dict() == {"a": 100, "b": 20, "c": 1}


def test_same_rows_every_time_in_original_order() -> None:
    a = export.sample_fraction(_rows(), 0.1)
    b = export.sample_fraction(_rows(), 0.1)
    assert a.equals(b)
    assert a["i"].is_monotonic_increasing


def test_fraction_one_keeps_everything() -> None:
    rows = _rows()
    assert export.sample_fraction(rows, 1.0).equals(rows)


@pytest.mark.parametrize("bad", [0, -0.1, 1.5])
def test_refuses_a_fraction_outside_zero_to_one(bad: float) -> None:
    with pytest.raises(ValueError):
        export.sample_fraction(_rows(), bad)
