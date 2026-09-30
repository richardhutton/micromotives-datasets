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


NO_RESIDUAL = CatScheme(
    "strict",
    [
        cat("White", "white"),
        cat("Black", "black"),
        cat("Hispanic", "hispanic"),
        cat("2+", "two_or_more_races"),
        cat("Asian", "asian"),
    ],
)


def test_a_scheme_without_the_residual_can_still_be_harmonised() -> None:
    """The real `e45hu` case, and a correction to my first version of this rule.

    e45hu lists White/Black/Asian/Hispanic/2+ with no Other at all. Mapping its
    `asian` into a canonical `Other or Asian` is a valid coarsening — a
    canonical category may be the union of ONE source category as well as
    several. Demanding every scheme own every folded concept blocked a
    legitimate merge, and the first version of this module did exactly that.
    """
    # Paired against A, which has Other but NOT Asian — the real e45hu shape.
    # (Pairing it with B would be no test at all: both distinguish Asian, so it
    # correctly survives, which is what my first version of this test asserted
    # against.)
    target = canonical([NO_RESIDUAL, A])
    assert crosswalk(NO_RESIDUAL, target)["Asian"] == target["other"] == "Other or Asian"


def test_raises_only_when_no_scheme_anywhere_offers_a_residual() -> None:
    """Then there is genuinely nowhere honest to put the folded concept."""
    also_no_residual = CatScheme(
        "strict2",
        [cat("White", "white"), cat("Black", "black"), cat("Hispanic", "hispanic")],
    )
    with pytest.raises(ValueError, match="no scheme offers a residual"):
        canonical([NO_RESIDUAL, also_no_residual])


def test_refusals_do_not_become_a_category() -> None:
    """A refusal is an absence of an answer, so it gets no canonical category.

    It must also not drag a real concept into the residual by appearing to be a
    concept some schemes lack — the same reason `bands` keeps unparsed labels
    out of its edge arithmetic.
    """
    with_sentinels = CatScheme(
        "s", [*A.categories, cat("REFUSED", "declined"), cat("Not asked", "none_of_these")]
    )
    target = canonical([with_sentinels, A])
    assert "declined" not in target
    assert "none_of_these" not in target
    # ...and it is dropped from the crosswalk, leaving the field empty.
    assert "REFUSED" not in crosswalk(with_sentinels, target)


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
