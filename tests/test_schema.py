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
    assert row.anchor() == ("tess", "ab12c", None)


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
