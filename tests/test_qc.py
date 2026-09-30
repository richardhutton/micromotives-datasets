"""QC rules. Each test corresponds to a real failure found in SocSci210."""

from __future__ import annotations

import pytest

from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.pipeline.qc import check
from micromotives_datasets.sources import spss


def test_clean_study_passes(fixture_sav, fixture_recipe) -> None:
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rep = check(rows, fixture_recipe)
    assert rep.passed, rep.failures
    assert rep.n_rows == 7
    assert rep.rows_per_condition == {0: 3, 1: 4}


def test_identical_condition_text_is_a_failure(fixture_sav, fixture_recipe) -> None:
    """The `sd7cf` failure: distinct conditions collapsing to one description.

    SocSci210 gave 12 conditions only 3 distinct stimulus strings, silently
    discarding a whole experimental factor. This must fail the build.
    """
    fixture_recipe.condition.arms[1].text = fixture_recipe.condition.arms[0].text
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rep = check(rows, fixture_recipe)
    assert not rep.passed
    assert any("identical text" in f for f in rep.failures)


def test_empty_rows_fail(fixture_recipe) -> None:
    rep = check([], fixture_recipe)
    assert not rep.passed
    assert any("no rows" in f for f in rep.failures)


def test_factor_that_never_changes_the_text_fails(fixture_sav, fixture_recipe) -> None:
    """A declared factor must actually be expressed in the arm text."""
    fixture_recipe.condition.arms[1].text = fixture_recipe.condition.arms[0].text
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rep = check(rows, fixture_recipe)
    assert any("never changes" in f or "identical text" in f for f in rep.failures)


def test_response_outside_declared_scale_fails(fixture_sav, fixture_recipe) -> None:
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rows[0].response_num = 99.0
    rep = check(rows, fixture_recipe)
    assert not rep.passed
    assert any("outside declared scale" in f for f in rep.failures)


@pytest.mark.parametrize("field_", ["condition_num", "task_num"])
def test_duplicate_indices_rejected_by_recipe(fixture_recipe, field_) -> None:
    """Recipe validation catches duplicate canonical indices."""
    from micromotives_datasets.recipe import Recipe

    data = fixture_recipe.model_dump()
    if field_ == "condition_num":
        data["condition"]["arms"][1]["condition_num"] = 0
    else:
        data["outcomes"][1]["task_num"] = 0
    with pytest.raises(ValueError, match="duplicate"):
        Recipe.model_validate(data)
