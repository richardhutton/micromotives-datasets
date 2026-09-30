"""Harmonising unordered persona categories.

The case that drives the whole module, measured on the built corpus:

    scheme A (10 studies):  White  Black  Hispanic  2+ Races  Other
    scheme B (4 studies):   White  Black  Hispanic  2+        Other  Asian

B separates Asian; A hides it inside Other. B folds into A by merging; A can
never be expanded into B without inventing answers nobody gave.
"""

from __future__ import annotations

import pytest

from micromotives_datasets.persona.categories import (
    Category,
    CatScheme,
    canonical,
    crosswalk,
    guess_residual,
)


def cat(label: str, concept: str) -> Category:
    return Category(label=label, concept=concept, is_residual=guess_residual(label))


# The two real ethnicity schemes, with the concepts Jev would assign.
A = CatScheme(
    "knowledgepanel",
    [
        cat("White, Non-Hispanic", "white"),
        cat("Black, Non-Hispanic", "black"),
        cat("Hispanic", "hispanic"),
        cat("2+ Races, Non-Hispanic", "two_or_more_races"),
        cat("Other, Non-Hispanic", "other"),
    ],
)
B = CatScheme(
    "amerispeak",
    [
        cat("White, non-Hispanic", "white"),
        cat("Black, non-Hispanic", "black"),
        cat("Hispanic", "hispanic"),
        cat("2+, non-Hispanic", "two_or_more_races"),
        cat("Other, non-Hispanic", "other"),
        cat("Asian, non-Hispanic", "asian"),
    ],
)


def test_wording_differences_alone_are_harmonised() -> None:
    """`2+ Races, Non-Hispanic` and `2+, non-Hispanic` are one category."""
    target = canonical([A, B])
    assert (
        crosswalk(A, target)["2+ Races, Non-Hispanic"] == (crosswalk(B, target)["2+, non-Hispanic"])
    )


def test_a_category_only_one_scheme_distinguishes_folds_into_the_residual() -> None:
    """Asian cannot survive, because A has already absorbed it into Other."""
    target = canonical([A, B])
    b_map = crosswalk(B, target)
    assert b_map["Asian, non-Hispanic"] == b_map["Other, non-Hispanic"]


def test_the_folded_label_admits_what_it_contains() -> None:
    """A row must not claim a precision it does not have.

    Calling the merged category plain "Other" would hide that it now also
    holds every Asian respondent from four studies.
    """
    target = canonical([A, B])
    assert target["other"] == "Other or Asian"


def test_universally_distinguished_categories_are_untouched() -> None:
    """A concept every scheme distinguishes keeps its own category.

    Asserted as "no other concept shares its label" rather than by looking for
    the word "or" — "Two or more races" contains one legitimately, which the
    first version of this test tripped over.
    """
    target = canonical([A, B])
    for concept in ("white", "black", "hispanic", "two_or_more_races"):
        sharers = [c for c, label in target.items() if label == target[concept]]
        assert sharers == [concept], (concept, sharers)


def test_identical_schemes_need_no_folding() -> None:
    """With nothing to reconcile, every category keeps its own identity."""
    target = canonical([A, A])
    assert target["other"] == "Other"
    assert len(set(target.values())) == len(A.concepts)


def test_a_scheme_with_no_residual_cannot_absorb_and_must_raise() -> None:
    """Better to say "cannot reconcile" than to pick a victim.

    If a scheme lacks Asian AND has no catch-all, there is no honest place to
    put those respondents, and choosing one would be fabrication.
    """
    no_residual = CatScheme(
        "strict",
        [
            cat("White", "white"),
            cat("Black", "black"),
            cat("Hispanic", "hispanic"),
            cat("2+", "two_or_more_races"),
        ],
    )
    with pytest.raises(ValueError, match="no residual"):
        canonical([no_residual, B])


def test_crosswalk_rejects_a_concept_outside_the_vocabulary() -> None:
    """Guards a caller mixing a target built from different schemes."""
    target = canonical([A, A])  # no `asian` concept in this vocabulary
    with pytest.raises(ValueError, match="not in the canonical vocabulary"):
        crosswalk(B, target)


def test_every_source_label_maps_somewhere() -> None:
    target = canonical([A, B])
    for scheme in (A, B):
        assert set(crosswalk(scheme, target)) == {c.label for c in scheme.categories}


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("Other, Non-Hispanic", True),
        ("Something else", True),
        ("None of these", True),
        ("White, Non-Hispanic", False),
        ("Asian, non-Hispanic", False),
    ],
)
def test_residual_detection(label, expected) -> None:
    assert guess_residual(label) is expected
