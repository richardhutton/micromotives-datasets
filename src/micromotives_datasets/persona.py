"""Render a Persona to the text that goes into the prompt.

Kept deliberately simple and deterministic: named fields in a fixed order,
then any `extra` fields. Sources map their raw demographics onto `Persona`
(see docs/innovation_panel_checklist.md §4 for the UKHLS mapping); this module
only turns a populated `Persona` into a sentence-ish block.
"""

from __future__ import annotations

from .schema import Persona

# (attribute, human label) in render order.
_FIELDS: list[tuple[str, str]] = [
    ("age", "Age"),
    ("sex", "Sex"),
    ("gender", "Gender"),
    ("ethnicity", "Ethnicity"),
    ("region", "Region"),
    ("education", "Education"),
    ("employment", "Employment"),
    ("social_grade", "Social grade"),
    ("income", "Income"),
    ("marital_status", "Marital status"),
    ("household_size", "Household size"),
    ("religion", "Religion"),
    ("urban_rural", "Area"),
    ("party_id", "Party identification"),
]


def render(persona: Persona) -> str:
    """Persona → newline-separated `Label: value` lines. Empty fields skipped."""
    lines: list[str] = []
    for attr, label in _FIELDS:
        value = getattr(persona, attr)
        if value is not None and value != "":
            lines.append(f"{label}: {value}")
    for key, value in persona.extra.items():
        if value != "":
            lines.append(f"{key}: {value}")
    return "\n".join(lines)
