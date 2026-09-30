"""Recipe loading and validation, including the real 7jt2f recipe."""

from __future__ import annotations

from pathlib import Path

import pytest

from micromotives_datasets import recipe as recipe_mod

REPO = Path(__file__).resolve().parents[1]


def test_scale_instruction() -> None:
    s = recipe_mod.Scale(min=-3, max=3, min_label="Bad", max_label="Good")
    assert s.instruction() == (
        'Only return an integer from -3 to 3 where -3 means "Bad" and 3 means "Good", nothing else.'
    )


def test_scale_without_labels() -> None:
    assert (
        recipe_mod.Scale(min=1, max=7).instruction()
        == "Only return an integer from 1 to 7, nothing else."
    )


def test_arm_missing_a_declared_factor_is_rejected(fixture_recipe) -> None:
    data = fixture_recipe.model_dump()
    data["condition"]["arms"][0]["factors"] = {}
    with pytest.raises(ValueError, match="missing factor"):
        recipe_mod.Recipe.model_validate(data)


def test_duplicate_raw_arm_rejected(fixture_recipe) -> None:
    data = fixture_recipe.model_dump()
    data["condition"]["arms"][1]["raw"] = 1
    with pytest.raises(ValueError, match="duplicate raw"):
        recipe_mod.Recipe.model_validate(data)


def test_real_7jt2f_recipe_loads_and_is_well_formed() -> None:
    rec = recipe_mod.load(REPO / "recipes" / "7jt2f.yaml")
    assert rec.study_id == "7jt2f"
    # 2 x 4 design: 8 arms, two declared factors.
    assert len(rec.condition.arms) == 8
    assert set(rec.condition.factors) == {"label", "self_introduction"}
    # Mapping is declared explicitly, and here happens to be raw-1.
    assert {a.raw: a.condition_num for a in rec.condition.arms} == {
        1: 0,
        2: 1,
        3: 2,
        4: 3,
        5: 4,
        6: 5,
        7: 6,
        8: 7,
    }
    # Five outcome items (Q7 deliberately excluded).
    assert [o.var for o in rec.outcomes] == ["Q2", "Q3", "Q4", "Q5", "Q6"]
    # The recode is the explicit map, not arithmetic.
    assert rec.response_recode == {2: -3, 3: -2, 4: -1, 5: 0, 6: 1, 7: 2, 8: 3}


def test_7jt2f_arms_have_distinct_text() -> None:
    """All eight arms must be distinguishable — the invariant SocSci210 broke."""
    rec = recipe_mod.load(REPO / "recipes" / "7jt2f.yaml")
    rendered = [rec.condition.render(a) for a in rec.condition.arms]
    assert len(set(rendered)) == 8


def test_7jt2f_self_introduction_factor_matches_the_questionnaire() -> None:
    """Arms 1-4 saw the self-introduction; arms 5-8 did not.

    This is the fact SocSci210 inverted, so it is pinned down here.
    """
    rec = recipe_mod.load(REPO / "recipes" / "7jt2f.yaml")
    by_raw = {a.raw: a for a in rec.condition.arms}
    for raw in (1, 2, 3, 4):
        assert by_raw[raw].factors["self_introduction"] == "present"
        assert "self-introduction" in by_raw[raw].text
    for raw in (5, 6, 7, 8):
        assert by_raw[raw].factors["self_introduction"] == "absent"
        assert "only by the label" in by_raw[raw].text
