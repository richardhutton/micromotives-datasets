"""Band harmonisation. The arithmetic half of the persona crosswalk.

Judgment — which column is even the respondent's income — is not here; a regex
offered six vignette variables about a fictional character and a model threw
them out (`scripts/persona_classify.py`). What IS here must be provable, so
every rule below is asserted rather than trusted.
"""

from __future__ import annotations

import pytest

from micromotives_datasets.persona.bands import (
    INF,
    Band,
    canonical,
    crosswalk,
    parse,
    read_scheme,
)


@pytest.mark.parametrize(
    ("label", "lo", "hi"),
    [
        # Inclusive phrasing: "to $12,499" includes 12,499, so the half-open
        # upper edge is the next unit up.
        ("$10,000 to $12,499", 10_000, 12_500),
        ("$30,000-$39,999", 30_000, 40_000),
        # "to under" is already exclusive and must NOT be nudged.
        ("$10,000 to under $20,000", 10_000, 20_000),
        ("Less than $5,000", 0, 5_000),
        ("Under $10,000", 0, 10_000),
        ("$175,000 or more", 175_000, INF),
        ("$200,000+", 200_000, INF),
        ("$100,000 and over", 100_000, INF),
    ],
)
def test_parses_the_phrasings_the_surveys_actually_use(label, lo, hi) -> None:
    b = parse(label)
    assert b is not None, label
    assert (b.lo, b.hi) == (lo, hi)


@pytest.mark.parametrize("label", ["Not asked", "REFUSED", "Missing", "Skipped on web"])
def test_sentinels_are_not_bands(label) -> None:
    """A sentinel parsed as a band would put respondents in the wrong decile."""
    assert parse(label) is None


def test_inclusive_and_exclusive_phrasings_do_not_collide() -> None:
    """The distinction that makes tiling work.

    `$10,000 to $14,999` and `$10,000 to under $15,000` describe the SAME
    interval, and both must yield [10000, 15000) — otherwise adjacent bands
    would appear to overlap by one unit or leave a one-unit gap.
    """
    assert parse("$10,000 to $14,999") == Band(10_000, 15_000, "$10,000 to $14,999")
    assert parse("$10,000 to under $15,000").hi == 15_000


KP = [  # KnowledgePanel: splits the two lowest bands finer
    "Less than $5,000",
    "$5,000 to $7,499",
    "$7,500 to $9,999",
    "$10,000 to $12,499",
    "$12,500 to $14,999",
    "$15,000 to $19,999",
    "$20,000 or more",
]
AS = [  # AmeriSpeak: splits the top band instead
    "Less than $5,000",
    "$5,000 to $9,999",
    "$10,000 to $14,999",
    "$15,000 to $19,999",
    "$20,000 to $24,999",
    "$25,000 or more",
]


def test_real_schemes_tile_cleanly() -> None:
    for labels in (KP, AS):
        assert read_scheme("s", labels).tiles() == []


def test_a_gap_is_reported() -> None:
    s = read_scheme("gappy", ["Less than $5,000", "$10,000 or more"])
    assert any("gap" in p for p in s.tiles())


def test_an_overlap_is_reported() -> None:
    s = read_scheme("overlap", ["Less than $10,000", "$5,000 to $9,999", "$10,000 or more"])
    assert any("overlap" in p for p in s.tiles())


def test_canonical_edges_are_the_intersection() -> None:
    """The heart of it: an edge survives only if EVERY scheme has it.

    Keeping an edge one scheme lacks would mean splitting that scheme's band —
    inventing a distinction the survey never measured.
    """
    kp, am = read_scheme("kp", KP), read_scheme("as", AS)
    target = canonical([kp, am])
    edges = {b.lo for b in target if b.lo > 0}
    assert edges == kp.edges & am.edges
    # 7,500 and 12,500 are KP-only; 20,000 is in both; 25,000 is AS-only.
    assert 7_500 not in edges and 12_500 not in edges and 25_000 not in edges
    assert 20_000 in edges


def test_every_source_band_lands_in_exactly_one_canonical_band() -> None:
    kp, am = read_scheme("kp", KP), read_scheme("as", AS)
    target = canonical([kp, am])
    for s in (kp, am):
        cw = crosswalk(s, target)
        assert set(cw) == {b.label for b in s.bands}


def test_the_merges_are_the_expected_ones() -> None:
    kp, am = read_scheme("kp", KP), read_scheme("as", AS)
    cw = crosswalk(kp, canonical([kp, am]))
    assert cw["$5,000 to $7,499"] == cw["$7,500 to $9,999"]
    assert cw["$10,000 to $12,499"] == cw["$12,500 to $14,999"]
    # ...while a band both schemes share is not merged with anything.
    assert cw["$15,000 to $19,999"] == "$15,000 to $19,999"


def test_a_target_that_is_not_a_coarsening_is_rejected() -> None:
    """The assertion that makes the rest safe.

    If a caller supplies a target with an edge inside a source band, that band
    would have to be split. It must raise rather than pick a side.
    """
    kp = read_scheme("kp", KP)
    bogus = [Band(0, 6_000, "Under $6,000"), Band(6_000, INF, "$6,000 or more")]
    with pytest.raises(ValueError, match="not a coarsening"):
        crosswalk(kp, bogus)


def test_unparseable_labels_are_kept_separate_not_dropped() -> None:
    s = read_scheme("s", [*KP, "Not asked", "REFUSED"])
    assert len(s.bands) == len(KP)
    assert s.unparsed == ["Not asked", "REFUSED"]
