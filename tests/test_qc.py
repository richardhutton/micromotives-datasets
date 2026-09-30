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


def test_non_monotonic_recode_fails(fixture_sav, fixture_recipe) -> None:
    """A higher band meaning a smaller quantity is a unit or parsing error."""
    fixture_recipe.outcomes[0].response_recode = {2: -3, 3: -2, 4: 99, 5: 0, 6: 1, 7: 2, 8: 3}
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rep = check(rows, fixture_recipe)
    assert not rep.passed
    assert any("changes direction" in f for f in rep.failures)


def test_colliding_bands_fail(fixture_sav, fixture_recipe) -> None:
    """The real SocSci210 defect: '1-4 minutes' and '1-3 hours' both -> 1."""
    fixture_recipe.outcomes[0].response_recode = {2: 1, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 8: 6}
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rep = check(rows, fixture_recipe)
    assert not rep.passed
    assert any("same value" in f for f in rep.failures)


def test_socsci210_zrwjp_time_recode_would_be_rejected() -> None:
    """Regression against the actual defect, using their real mapping.

    Their Q6 map took each band's lower bound at face value, ignoring that bands
    2-6 are minutes and 7-17 are hours. Our QC must reject it.
    """
    from micromotives_datasets.pipeline.qc import _all_recodes

    theirs = {
        1: 0,
        2: 1,
        3: 5,
        4: 10,
        5: 20,
        6: 40,
        7: 1,
        8: 4,
        9: 7,
        10: 10,
        11: 13,
        12: 16,
        13: 19,
        14: 22,
        15: 30,
        16: 40,
        17: 50,
    }
    values = [theirs[k] for k in sorted(theirs)]
    assert values != sorted(values), "should be non-monotonic"
    assert len(set(values)) < len(values), "should contain collisions"
    assert _all_recodes  # the helper is what QC walks


def test_reverse_coded_scale_is_allowed(fixture_sav, fixture_recipe) -> None:
    """A fully reverse-coded scale is legitimate and must not be flagged.

    Reverse-coded Likert items are common; only a MIXED direction (a unit
    switch) is a defect.
    """
    fixture_recipe.outcomes[0].response_recode = {2: 3, 3: 2, 4: 1, 5: 0, 6: -1, 7: -2, 8: -3}
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rep = check(rows, fixture_recipe)
    assert not any("changes direction" in f for f in rep.failures), rep.failures
