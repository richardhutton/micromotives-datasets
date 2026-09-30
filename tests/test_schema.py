"""Smoke tests for the (P, c, o, r) row schema and persona rendering."""

from micromotives_datasets.persona import render
from micromotives_datasets.schema import Persona, Row


def test_persona_render_skips_empty_fields() -> None:
    p = Persona(age=42, sex="Female", region="Scotland")
    text = render(p)
    assert "Age: 42" in text
    assert "Sex: Female" in text
    assert "Region: Scotland" in text
    assert "Income" not in text  # unset → skipped


def test_persona_render_includes_extra() -> None:
    p = Persona(extra={"Newspaper readership": "broadsheet"})
    assert "Newspaper readership: broadsheet" in render(p)


def test_row_has_four_distinct_parts() -> None:
    row = Row(
        persona=Persona(age=30),
        condition="You read that immigration rose last year.",
        outcome="How concerned are you about immigration? (1-7)",
        response="6",
        condition_num=2,
        response_num=6.0,
        source="tess",
        study_id="ab12c",
    )
    # The tuple's four parts are distinct fields.
    assert row.condition != row.outcome
    # (source, study_id, experiment, participant_id) — `experiment` is part of
    # the key because a deposit's sub-experiments share their respondents.
    assert row.anchor() == ("tess", "ab12c", None, None)


def test_synthetic_quote_defaults_false() -> None:
    row = Row(
        persona=Persona(),
        condition="c",
        outcome="o",
        response="r",
        source="socsci210",
        study_id="xyz99",
    )
    assert row.synthetic_quote is False
    assert row.quote is None


def test_participant_id_is_namespaced_by_study(fixture_sav, fixture_recipe) -> None:
    """Identity must be unique ACROSS studies, not just within one.

    These rows get merged into a single corpus. With a bare row index, 23,464
    respondents collapsed into 4,010 ids and "person 0" existed in all 14
    studies as 14 different people.
    """
    from micromotives_datasets.pipeline.build import build_rows
    from micromotives_datasets.sources import spss

    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    assert all(r.participant_id.startswith("test01:") for r in rows)


def test_anchor_separates_sub_experiments(fixture_sav, fixture_recipe) -> None:
    """One deposit's sub-experiments are answered by the SAME people.

    `a5v96`'s two vignettes were both shown to all 1,211 respondents, so without
    `experiment` in the key a respondent's rows from the two are
    indistinguishable.
    """
    from micromotives_datasets.pipeline.build import build_rows
    from micromotives_datasets.sources import spss

    ds = spss.read(fixture_sav)
    fixture_recipe.experiment = "one"
    a = list(build_rows(ds, fixture_recipe))[0]
    fixture_recipe.experiment = "two"
    b = list(build_rows(ds, fixture_recipe))[0]
    assert a.participant_id == b.participant_id, "same respondent, same id"
    assert a.anchor() != b.anchor(), "but different rows of the corpus"
