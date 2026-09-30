"""Harmonise UNORDERED persona attributes — ethnicity, employment, marital status.

Bands (`bands.py`) are intervals on a line, so merging them is arithmetic.
Categories are not, and the difference is not cosmetic. Measured on the built
corpus:

    scheme A (10 studies):  White  Black  Hispanic  2+ Races  Other
    scheme B (4 studies):   White  Black  Hispanic  2+        Other  Asian

Four of five differ only in wording, which is trivial. The real difference is
that **B separates Asian and A does not** — A's Asian respondents are inside
`Other`. And that is a one-way street: B can be folded into A by merging Asian
into Other, while A can never be expanded into B, because pulling Asian back
out of Other would mean inventing an answer nobody gave.

The rule that follows, and it is the same rule as `bands.py` in a different
dress: **a canonical category must be a union of categories from EVERY scheme.**
So when one scheme lacks a concept another has, the concept folds into the
residual ("Other"), and the canonical label says so — `Other or Asian`, not
`Other` — because a row must not claim a precision it does not have.

The semantic step (is `2+ Races, Non-Hispanic` the same concept as
`2+, non-Hispanic`? which category is the residual?) is a judgment and belongs
to Jev, via `scripts/persona_harmonise.py`. What is here is the bookkeeping,
which is checkable and therefore asserted.
"""

from __future__ import annotations

from dataclasses import dataclass

# A label meaning "none of the listed options". Identified by Jev per scheme;
# these are the spellings seen so far, kept as a fallback for offline use.
RESIDUAL_HINTS = ("other", "something else", "none of these", "not listed")


@dataclass(frozen=True)
class Category:
    """One source category, and the concept Jev says it denotes."""

    label: str
    concept: str
    is_residual: bool = False


@dataclass
class CatScheme:
    name: str
    categories: list[Category]

    @property
    def concepts(self) -> set[str]:
        return {c.concept for c in self.categories}

    @property
    def residual(self) -> Category | None:
        return next((c for c in self.categories if c.is_residual), None)


def canonical(schemes: list[CatScheme]) -> dict[str, str]:
    """Concept -> canonical label, given several schemes over the same population.

    A concept every scheme distinguishes keeps its own canonical category. A
    concept only SOME schemes distinguish cannot survive, because the schemes
    that lack it have already absorbed it into their residual — so it folds
    into the residual, whose label then names what it now contains.

    Raises when a concept is missing from a scheme that has no residual to
    absorb it: that scheme genuinely cannot be reconciled, and saying so is
    better than guessing which of its categories should swallow the difference.
    """
    live = [s for s in schemes if s.categories]
    if not live:
        return {}

    universal = set.intersection(*(s.concepts for s in live))
    everything = set.union(*(s.concepts for s in live))
    folded = sorted(everything - universal)

    if folded:
        for s in live:
            missing = folded and not s.concepts.issuperset(folded)
            if missing and s.residual is None:
                raise ValueError(
                    f"{s.name} distinguishes none of {folded} and has no residual "
                    "category to absorb them — cannot reconcile without guessing"
                )

    out: dict[str, str] = {}
    residual_concepts = {s.residual.concept for s in live if s.residual}
    for concept in sorted(universal):
        out[concept] = _title(concept)
    # Everything not universally distinguished lands in the residual, and the
    # residual's label admits what it has swallowed.
    if folded:
        absorbed = sorted(set(folded) - residual_concepts)
        for res in residual_concepts:
            out[res] = " or ".join([_title(res), *(_title(c) for c in absorbed)])
        for concept in folded:
            if concept not in residual_concepts:
                out[concept] = out[next(iter(residual_concepts))]
    return out


def _title(concept: str) -> str:
    """`two_or_more_races` -> `Two or more races`."""
    words = concept.replace("_", " ").strip()
    return words[:1].upper() + words[1:] if words else words


def crosswalk(scheme: CatScheme, target: dict[str, str]) -> dict[str, str]:
    """This scheme's own labels to canonical labels.

    Raises on a concept the target does not cover, which would mean `canonical`
    was built from a different set of schemes than the one being mapped — a
    caller error worth failing on rather than silently dropping a category.
    """
    out = {}
    for cat in scheme.categories:
        if cat.concept not in target:
            raise ValueError(
                f"{scheme.name}: concept {cat.concept!r} (label {cat.label!r}) is not "
                "in the canonical vocabulary"
            )
        out[cat.label] = target[cat.concept]
    return out


def guess_residual(label: str) -> bool:
    """Offline fallback for which category is the catch-all.

    Jev decides this in the real pipeline; this exists so `bands`-style tests
    and offline work do not need an API key.
    """
    low = label.lower()
    return any(h in low for h in RESIDUAL_HINTS)
