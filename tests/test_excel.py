"""An Excel export is read like a `.sav`: text becomes codes plus the labels that restore it.

`k7tw5` ships only a spreadsheet, and its randomised arm is a text column. What
must hold, and what must NOT happen:

* text round-trips: code -> label gives the source's own words back;
* the same text with a stray trailing space is one value, not two arms;
* a sentinel number living in a text column (-888) keeps its own value, so the
  recipe's missing codes still find it and nothing relabels it;
* a purely numeric column is left exactly as it was;
* a real number that would collide with an assigned code is refused.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from micromotives_datasets.sources import excel, read_any


def _xlsx(tmp_path: Path, frame: dict) -> Path:
    p = tmp_path / "s.xlsx"
    pd.DataFrame(frame).to_excel(p, index=False)
    return p


def test_text_round_trips_through_codes(tmp_path: Path) -> None:
    p = _xlsx(tmp_path, {"Label": ["Obesity 2", "Bowel cancer 1", "Obesity 2"]})
    ds = read_any(p)
    codes = ds.df["Label"].tolist()
    assert codes == [2.0, 1.0, 2.0], "sorted order: Bowel cancer 1 = 1, Obesity 2 = 2"
    assert [ds.label("Label", c) for c in codes] == ["Obesity 2", "Bowel cancer 1", "Obesity 2"]


def test_a_trailing_space_is_not_a_new_arm(tmp_path: Path) -> None:
    p = _xlsx(tmp_path, {"Label": ["Obesity 2", "Obesity 2 ", "Obesity 3"]})
    ds = excel.read(p)
    assert ds.value_labels["Label"] == {1.0: "Obesity 2", 2.0: "Obesity 3"}
    assert ds.df["Label"].tolist() == [1.0, 1.0, 2.0]


def test_a_sentinel_in_a_text_column_keeps_its_value(tmp_path: Path) -> None:
    p = _xlsx(tmp_path, {"Gender": ["Female", -888, "Male"]})
    ds = excel.read(p)
    assert ds.df["Gender"].tolist() == [1.0, -888.0, 2.0]
    assert -888.0 not in ds.value_labels["Gender"], "a sentinel must not acquire a label"


def test_a_numeric_column_is_untouched(tmp_path: Path) -> None:
    p = _xlsx(tmp_path, {"Age": [18, 89, 47], "Score": [1, 7, 4]})
    ds = excel.read(p)
    assert ds.value_labels == {}
    assert ds.df["Age"].tolist() == [18, 89, 47]


def test_a_number_colliding_with_a_code_is_refused(tmp_path: Path) -> None:
    """Text gets codes 1..n; a genuine 1 in the same column would merge two answers."""
    p = _xlsx(tmp_path, {"Mixed": ["Yes", 1, "No"]})
    with pytest.raises(ValueError, match="collide"):
        excel.read(p)


def test_a_cell_of_spaces_is_blank_and_the_column_stays_numeric(tmp_path: Path) -> None:
    """pr8zu: one cell of spaces in a 1..7 column made it 'text' and its 1 collide."""
    p = _xlsx(tmp_path, {"Score": [4, "     ", 1, 7]})
    ds = excel.read(p)
    assert "Score" not in ds.value_labels, "no label may be invented for an empty cell"
    assert ds.df["Score"].dtype == "float64"
    s = ds.df["Score"].tolist()
    assert s[0] == 4.0 and s[2] == 1.0 and s[3] == 7.0 and pd.isna(s[1])


def test_a_cell_of_spaces_in_a_text_column_gets_no_code(tmp_path: Path) -> None:
    """The blank must not become an arm, and real text beside it still codes."""
    p = _xlsx(tmp_path, {"Label": ["Obesity 2", "  ", "Obesity 3"]})
    ds = excel.read(p)
    assert ds.value_labels["Label"] == {1.0: "Obesity 2", 2.0: "Obesity 3"}
    assert pd.isna(ds.df["Label"].tolist()[1])
