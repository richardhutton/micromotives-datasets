"""A decode that "succeeds" and produces control characters has not succeeded.

`sources/spss.py` tries a tuple of encodings in order. Until 5 October 2026 that
tuple began `(None, "latin1", "cp1252", ...)` — and `latin1` maps every one of
the 256 byte values to a codepoint, so it NEVER raises. It was not a fallback,
it was a wall: everything after it was unreachable, and a Windows-1252 file (the
standard output of every UK survey house in this corpus) decoded "successfully"
with its smart quotes, dashes and ellipses turned into raw C1 control
characters.

The cost was 5,279 of PZB01G's 5,333 rows — 99% — carrying strings like
`"Own \x96 with a mortgage"` in the persona text a model would be shown. QC
passed. Every count reconciled. The authors' nine published group sizes matched
exactly. It was found by a checker reading one rendered row, which is the same
way EFXNLX's wrong-on-every-row defect was found, and for the same reason: the
numbers cannot see the text.

Two guards, because the ordering fix alone is not enough — the next odd codepage
will not be in the tuple at all:

1. The order is pinned, strict before permissive.
2. The RESULT is checked. `_control_characters` rejects a decode that produced
   C1 codepoints, whatever encoding claimed to work.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import pytest

from micromotives_datasets.sources import spss

REPO = Path(__file__).resolve().parents[1]


def test_a_permissive_codec_never_precedes_a_strict_one() -> None:
    """`cp1252` must be tried before `latin1`, or it is decoration.

    `cp1252` leaves five byte values undefined (0x81, 0x8D, 0x8F, 0x90, 0x9D) and
    raises on them, so a genuinely Latin-1 file still falls through. `latin1`
    accepts everything and so can only ever be last among the single-byte codecs.
    """
    source = (REPO / "src" / "micromotives_datasets" / "sources" / "spss.py").read_text()
    order = [e for e in ("cp1252", "latin1") if f'"{e}"' in source]
    assert order == ["cp1252", "latin1"], (
        f"encoding order is {order}; latin1 accepts all 256 byte values and never "
        f"raises, so anything after it is unreachable"
    )


@pytest.mark.parametrize(
    ("label", "should_flag"),
    [
        ("Own \x96 with a mortgage", True),  # the real PZB01G string
        ("No don\x92t think of myself as any of these", True),  # the real party_id string
        ("Own – with a mortgage", False),  # correctly decoded en dash
        ("Married", False),
        ("£10,000 to £14,999 per year", False),  # non-ASCII but legitimate
    ],
)
def test_control_characters_are_detected_and_ordinary_text_is_not(
    label: str, should_flag: bool
) -> None:
    """The guard must catch the real corruption without rejecting real text.

    The second half matters as much as the first: a check that flagged every
    non-ASCII label would reject `£` and be turned off within a day.
    """

    class _Meta:
        variable_value_labels: ClassVar[dict[str, dict[float, str]]] = {"v": {1.0: label}}
        column_names_to_labels: ClassVar[dict[str, str]] = {}

    found = spss._control_characters(_Meta())
    assert bool(found) is should_flag, f"{label!r}: expected flag={should_flag}, got {found}"


@pytest.mark.skipif(
    not (REPO / "data" / "raw" / "PZB01G" / "Vignette data.dta").exists(),
    reason="deposit not fetched on this machine",
)
def test_the_file_that_broke_it_now_reads_correctly() -> None:
    """The regression itself, against the actual file.

    Deliberately pinned to the real deposit rather than a synthetic fixture: the
    bug was in how a REAL Windows-1252 Stata file interacts with pyreadstat's
    encoding argument, and a fixture written by the same person who wrote the fix
    would have encoded the same assumption.
    """
    dataset = spss.read(REPO / "data" / "raw" / "PZB01G" / "Vignette data.dta")
    tenure = dataset.value_labels.get("profile_house_tenure", {})
    values = [str(v) for v in tenure.values()]
    assert values, "profile_house_tenure has no value labels; the read has changed shape"
    assert any("Own – " in v for v in values), (
        f"expected a correctly decoded en dash in {values[:3]}"
    )
    assert not any(any(0x80 <= ord(c) <= 0x9F for c in v) for v in values), (
        f"C1 control characters survived the read: {values[:3]}"
    )
