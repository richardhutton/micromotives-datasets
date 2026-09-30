"""Harmonise banded persona attributes across surveys that chopped them up differently.

The 73 fetched studies carry EIGHT distinct income band schemes, phrased
inconsistently — `$10,000 to $12,499`, `$10,000 to $14,999`, `$10,000 to under
$20,000`, `Less than $30,000` — with `Not asked` and `REFUSED` mixed into the
same columns. Merged as-is, the same person is described several incompatible
ways depending on which study their row came from, which is the whole problem
this module exists to remove.

**The canonical boundaries are the INTERSECTION of every scheme's boundaries.**
That is the only choice that needs no guessing, and it is worth being precise
about why. A canonical edge at $7,500 can be produced from a scheme that has
that edge, by keeping it; but from a scheme whose nearest edges are $5,000 and
$10,000 it could only be produced by SPLITTING a band, i.e. by inventing a
distinction the survey never measured. So an edge survives only if every scheme
has it. Each source band then sits entirely inside exactly one canonical band,
and harmonising is a merge — lossy in one direction, never fabricated.

Parsing and tiling are arithmetic and are asserted here. Deciding which COLUMN
holds the respondent's income in the first place is a judgment and is not done
here — see `scripts/persona_classify.py`, where a regex proposed six vignette
variables about a fictional character as "income" and a model had to throw them
out.
"""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass

# Labels that are not a band at all. Kept explicit rather than pattern-matched,
# because a sentinel silently parsed as a band would land respondents in the
# wrong part of the distribution.
SENTINELS = {
    "not asked",
    "refused",
    "missing",
    "don't know",
    "dont know",
    "skipped on web",
    "no answer",
}

_MONEY = r"\$?\s*([\d,]+(?:\.\d+)?)"
# "$10,000 to $12,499", "$10,000 to under $20,000", "$30,000-$39,999".
# The class also accepts en/em dashes, which some deposits use as the separator.
# Hyphen, en dash and em dash: deposits use all three as the range separator.
# Spelled by codepoint because the glyphs are visually indistinguishable here,
# which is exactly the confusion that would make a missing one hard to spot.
_DASH = "[{}]".format("".join(chr(c) for c in (0x2D, 0x2013, 0x2014)))
_RANGE = re.compile(rf"{_MONEY}\s*(?:to(?:\s+under)?|{_DASH}|through)\s*{_MONEY}", re.I)
# "Less than $5,000", "Under $10,000"
_BELOW = re.compile(rf"(?:less\s+than|under|below|up\s+to)\s*{_MONEY}", re.I)
# "$175,000 or more", "$200,000+", "$100,000 and over"
_ABOVE = re.compile(
    rf"{_MONEY}\s*(?:or\s+(?:more|over|above|greater)|\+|and\s+over|and\s+above)", re.I
)

INF = float("inf")


@dataclass(frozen=True)
class Band:
    """A half-open interval [lo, hi) in the attribute's own units."""

    lo: float
    hi: float
    label: str

    def inside(self, other: Band) -> bool:
        return other.lo <= self.lo and self.hi <= other.hi


def _num(text: str) -> float:
    return float(text.replace(",", ""))


def parse(label: str) -> Band | None:
    """One band label to an interval, or None when it is not a band.

    Order matters: `_ABOVE` is tried before `_RANGE` would see a stray number,
    and the sentinel check comes first so `REFUSED` never becomes an interval.
    """
    clean = label.strip()
    if clean.lower().strip(" .") in SENTINELS:
        return None
    # RANGE must be tried FIRST. "$10,000 to under $20,000" contains the
    # substring "under $20,000", so a less-than test run earlier matches it and
    # returns [0, 20000) — silently moving everyone in that band to the bottom
    # of the distribution. Caught by a test, not by reading the code.
    if m := _RANGE.search(clean):
        lo, hi = _num(m.group(1)), _num(m.group(2))
        # "$10,000 to $12,499" is inclusive of 12,499, so the half-open upper
        # edge is the next whole unit. "to under $20,000" is already exclusive.
        exclusive = re.search(r"to\s+under", clean, re.I) is not None
        return Band(lo, hi if exclusive else hi + 1.0, clean)
    if m := _ABOVE.search(clean):
        return Band(_num(m.group(1)), INF, clean)
    if m := _BELOW.search(clean):
        return Band(0.0, _num(m.group(1)), clean)
    return None


@dataclass
class Scheme:
    """One survey's banding of an attribute."""

    name: str
    bands: list[Band]
    unparsed: list[str]

    @property
    def edges(self) -> set[float]:
        """Interior boundaries — 0 and infinity are shared by construction."""
        return {b.lo for b in self.bands if b.lo > 0} | {b.hi for b in self.bands if b.hi < INF}

    def tiles(self) -> list[str]:
        """Complaints if the bands do not cover the line exactly once."""
        problems = []
        ordered = sorted(self.bands, key=lambda b: b.lo)
        if not ordered:
            return [f"{self.name}: no parseable bands"]
        if ordered[0].lo != 0:
            problems.append(f"{self.name}: starts at {ordered[0].lo:,.0f}, not 0")
        if ordered[-1].hi != INF:
            problems.append(f"{self.name}: top band is bounded at {ordered[-1].hi:,.0f}")
        for a, b in itertools.pairwise(ordered):
            if a.hi < b.lo:
                problems.append(f"{self.name}: gap {a.hi:,.0f}-{b.lo:,.0f}")
            elif a.hi > b.lo:
                problems.append(f"{self.name}: overlap at {b.lo:,.0f}")
        return problems


def read_scheme(name: str, labels: list[str]) -> Scheme:
    parsed, unparsed = [], []
    for label in labels:
        band = parse(label)
        if band is None:
            unparsed.append(label)
        else:
            parsed.append(band)
    return Scheme(name=name, bands=sorted(parsed, key=lambda b: b.lo), unparsed=unparsed)


def canonical(schemes: list[Scheme]) -> list[Band]:
    """The coarsest banding every scheme can merge INTO without splitting.

    Its interior edges are the intersection of the schemes' interior edges: an
    edge only survives if every scheme already has it, because producing one
    that a scheme lacks would mean splitting that scheme's band.
    """
    live = [s for s in schemes if s.bands]
    if not live:
        return []
    shared = set.intersection(*(s.edges for s in live))
    cuts = [0.0, *sorted(shared), INF]
    return [Band(lo, hi, _name_band(lo, hi)) for lo, hi in itertools.pairwise(cuts)]


def _name_band(lo: float, hi: float) -> str:
    if lo == 0:
        return f"Under ${hi:,.0f}"
    if hi == INF:
        return f"${lo:,.0f} or more"
    # Back to the inclusive phrasing the surveys themselves use.
    return f"${lo:,.0f} to ${hi - 1:,.0f}"


def crosswalk(scheme: Scheme, target: list[Band]) -> dict[str, str]:
    """Each of this scheme's labels to its canonical band.

    Raises when a source band does not sit inside exactly one target band —
    which would mean the target was built wrongly, since by construction it
    cannot happen.
    """
    out: dict[str, str] = {}
    for band in scheme.bands:
        holders = [t for t in target if band.inside(t)]
        if len(holders) != 1:
            raise ValueError(
                f"{scheme.name}: {band.label!r} spans {len(holders)} canonical bands — "
                "the canonical scheme is not a coarsening of this one"
            )
        out[band.label] = holders[0].label
    return out
