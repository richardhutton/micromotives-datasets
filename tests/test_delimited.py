"""A delimited export is a survey file whose codes are already resolved.

The thing worth testing is not the delimiter. It is that an EMPTY
`value_labels` is correct for this format and not a missing-metadata bug, and
that both spellings of "missing" in one file are read as missing — `PMV0TG`
uses a blank cell in one column and the literal string "NA" in another.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from micromotives_datasets.sources import delimited


def _write(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text(body)
    return p


def test_values_are_their_own_labels(tmp_path: Path) -> None:
    """A `.tab` stores "Female", not 2 plus a dictionary saying 2 is Female."""
    p = _write(tmp_path, "s.tab", "id\tgender\toccupation\n1\tFemale\tKey worker\n")
    ds = delimited.read(p)
    assert ds.value_labels == {}, "a resolved export has no code->label map to carry"
    assert ds.column_labels == {}, "a header row carries no question wording"
    # The point of the empty dict: label() passes text straight through.
    assert ds.label("gender", "Female") == "Female"
    assert ds.label("occupation", "Key worker") == "Key worker"


def test_a_numeric_column_still_prints_as_an_integer(tmp_path: Path) -> None:
    """`age` is 42, not 42.0 — the same rule the SPSS reader follows."""
    p = _write(tmp_path, "s.tab", "id\tage\n1\t42\n")
    ds = delimited.read(p)
    assert ds.label("age", ds.df["age"].iloc[0]) == "42"


def test_both_spellings_of_missing_are_missing(tmp_path: Path) -> None:
    """PMV0TG uses a blank cell AND the literal "NA", in one file.

    A stricter reader (`keep_default_na=False`) would admit "NA" as a real
    answer. That is ledger 109's shape: a value that is not a response being
    counted as one, in bulk, with nothing to notice it.
    """
    p = _write(tmp_path, "s.tab", "id\tideology\tincome\n1\t\tNA\n2\t5\tHigh\n")
    ds = delimited.read(p)
    assert ds.df["ideology"].isna().sum() == 1
    assert ds.df["income"].isna().sum() == 1
    assert ds.df["income"].iloc[1] == "High"


def test_an_unknown_extension_is_refused_rather_than_guessed(tmp_path: Path) -> None:
    p = _write(tmp_path, "s.weird", "a|b\n1|2\n")
    with pytest.raises(ValueError, match="unsupported delimited file type"):
        delimited.read(p)
    # ... but an explicit separator is honoured, because the caller knows.
    assert list(delimited.read(p, sep="|").df.columns) == ["a", "b"]


def test_a_non_utf8_file_is_recovered_rather_than_lost(tmp_path: Path) -> None:
    """Same reasoning as the SPSS reader's encoding fallback: do not lose a study."""
    p = tmp_path / "s.tab"
    p.write_bytes("id\tplace\n1\tM\xfcnchen\n".encode("latin1"))
    ds = delimited.read(p)
    assert ds.df["place"].iloc[0] == "München"
