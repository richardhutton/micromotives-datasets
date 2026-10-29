"""export.sample_respondents: the small test export keeps every study and whole respondents."""

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
    """Three studies of 100, 20 and 3 respondents, each answering four outcomes."""
    people = {"a": 100, "b": 20, "c": 3}
    rows = [(s, f"{s}{p}", o) for s, n in people.items() for p in range(n) for o in range(4)]
    frame = pd.DataFrame(rows, columns=["study", "participant_id", "outcome"])
    frame["i"] = range(len(frame))
    return frame


def test_keeps_each_studys_share_of_respondents_and_every_study() -> None:
    out = export.sample_respondents(_rows(), 0.1)
    assert out.groupby("study")["participant_id"].nunique().to_dict() == {"a": 10, "b": 2, "c": 1}


def test_keeps_every_row_of_a_chosen_respondent() -> None:
    out = export.sample_respondents(_rows(), 0.1)
    assert (out.groupby("participant_id").size() == 4).all()
    assert len(out) == 4 * 13


def test_same_rows_every_time_in_original_order() -> None:
    a = export.sample_respondents(_rows(), 0.1)
    b = export.sample_respondents(_rows(), 0.1)
    assert a.equals(b)
    assert a["i"].is_monotonic_increasing


def test_fraction_one_keeps_everything() -> None:
    rows = _rows()
    assert export.sample_respondents(rows, 1.0).equals(rows)


@pytest.mark.parametrize("bad", [0, -0.1, 1.5])
def test_refuses_a_fraction_outside_zero_to_one(bad: float) -> None:
    with pytest.raises(ValueError):
        export.sample_respondents(_rows(), bad)
