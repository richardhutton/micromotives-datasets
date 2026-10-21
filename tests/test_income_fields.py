"""Household and personal income are two fields, and each recipe maps the right one.

Until 21 Oct 2026 both went into `income` and rendered as "Income: £… per year".
Five UK studies (35M5CV_bbc, 35M5CV_lodger, QQM5MC, PZB01G, PMV0TG; 37,518 rows)
carried PERSONAL income that way beside household income from every other source,
so a model could not tell them apart. The variable labels were read from each
deposit to decide which is which:

- personal: `Income_GrossPersonal`, `gross_personal_income`,
  `profile_gross_personal` ("Income - gross personal").
- household: `gross_household`, `profile_gross_household`, DEL waves 4-5 `income`
  ("Income - gross household"); TESS `PPINCIMP` / `INCOME` ("Household Income").
- neither said: PMV0TG `ind_inc`, a High/Low split "relative to the median" that
  its codebook does not tie to the personal or the household question (the survey
  asks both). It goes to `income_level`, rendered "Income level", claiming neither.

The recipe check below works on variable NAMES, so a new name it does not know
fails rather than passing: read that variable's label, then add it here.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from micromotives_datasets.persona import render
from micromotives_datasets.persona.crosswalk import Crosswalk
from micromotives_datasets.schema import Persona

RECIPES = Path(__file__).resolve().parents[1] / "recipes"

PERSONAL = {"income_grosspersonal", "gross_personal_income", "profile_gross_personal"}
HOUSEHOLD = {"gross_household", "profile_gross_household", "income", "ppincimp"}
FIELD_FOR = {
    **dict.fromkeys(PERSONAL, "income_personal"),
    **dict.fromkeys(HOUSEHOLD, "income"),
    "ind_inc": "income_level",
}


def income_mappings(text: str) -> list[tuple[str, str]]:
    """(field, variable) for each income field in a recipe's top-level `persona_map`.

    Scans lines rather than parsing YAML: the largest recipes are tens of MB.
    `persona_missing` also has an `income:` key in DEL recipes, but it is keyed by
    VARIABLE and is outside `persona_map`, so it is not read.
    """
    found: list[tuple[str, str]] = []
    inside = False
    for line in text.splitlines():
        if line and not line[0].isspace():
            inside = line.rstrip() == "persona_map:"
            continue
        if inside:
            key, _, value = line.strip().partition(":")
            if key in {"income", "income_personal", "income_level", "household_income"}:
                found.append((key, value.strip()))
    return found


def check(mappings: list[tuple[str, str]]) -> list[str]:
    errors = []
    for field, var in mappings:
        want = FIELD_FOR.get(var.lower())
        if want is None:
            errors.append(f"{field}: {var} is not a known income variable — read its label")
        elif want != field:
            errors.append(f"{field}: {var} is {want}")
    return errors


def test_every_recipe_maps_income_to_the_field_its_source_measures() -> None:
    errors = []
    seen = 0
    for path in sorted(RECIPES.glob("*.yaml")):
        mappings = income_mappings(path.read_text())
        seen += len(mappings)
        errors += [f"{path.stem}: {e}" for e in check(mappings)]
    assert seen > 60, "found almost no income mappings — the scan is broken"
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize(
    ("mappings", "bad"),
    [
        ([("income", "Income_GrossPersonal")], True),  # personal in the household field
        ([("income_personal", "gross_household")], True),  # household in the personal field
        ([("income", "PPINCIMP")], False),
        ([("income_level", "ind_inc")], False),
        ([("income_personal", "ind_inc")], True),  # unstated: must not be called personal
        ([("income", "salary_band")], True),  # unknown: must be read, not assumed
    ],
)
def test_the_check_catches_a_swap_and_passes_a_correct_mapping(
    mappings: list[tuple[str, str]], bad: bool
) -> None:
    assert bool(check(mappings)) is bad


def test_the_scan_reads_persona_map_only() -> None:
    text = (
        "persona_map:\n  age: age\n  income: gross_household\n"
        "persona_missing:\n  income: [16, 17]\n"
    )
    assert income_mappings(text) == [("income", "gross_household")]


def test_both_incomes_render_with_their_own_label() -> None:
    text = render(Persona(income="£40,000 to £49,999 per year", income_personal="High"))
    assert "Household income: £40,000 to £49,999 per year" in text
    assert "Personal income: High" in text
    assert "\nIncome:" not in "\n" + text


def test_personal_income_uses_the_income_crosswalk() -> None:
    cw = Crosswalk(maps={"income": {"High": "Higher income"}}, vocab={"income": {"Higher income"}})
    assert cw.apply("income_personal", "High") == "Higher income"
    assert cw.unmapped("income_personal", "Weird band")
    assert not cw.unmapped("income_personal", "Higher income")
    assert cw.apply("income_level", "High") == "Higher income"


def test_an_unstated_income_renders_neutrally() -> None:
    text = render(Persona(extra={"income_level": "Higher income (band not specified)"}))
    assert text == "Income level: Higher income (band not specified)"
