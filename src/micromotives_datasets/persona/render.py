"""Render a Persona to the text that goes into the prompt.

Kept deliberately simple and deterministic: named fields in a fixed order,
then any `extra` fields. Sources map their raw demographics onto `Persona`
(see docs/innovation_panel_checklist.md §4 for the UKHLS mapping); this module
only turns a populated `Persona` into a sentence-ish block.
"""

from __future__ import annotations

from ..schema import Persona

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
    ("housing_type", "Housing type"),
    ("housing_ownership", "Housing ownership"),
    ("religion", "Religion"),
    ("urban_rural", "Area"),
    ("internet_access", "Internet access"),
    ("phone_service", "Phone service"),
    ("party_id", "Party identification"),
    ("ideology", "Ideology"),
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
            lines.append(f"{_label_for(key)}: {value}")
    return "\n".join(lines)


def _label_for(key: str) -> str:
    """`religious_attendance` -> `Religious attendance`.

    The named fields above all carry a written label; `extra` keys were rendered
    raw, so a persona read "Ideology: Slightly conservative" and then
    "religious_attendance: Once a week" — the same person described in two
    registers, in one block of text a model is asked to read. Found by a checker
    on `5hqan` and traced here; it affects every study that maps an attribute
    outside the named schema, which is five of twenty so far. Cosmetic, but this
    corpus is merged across studies and gratuitous inconsistency in the prompt
    is a signal about provenance rather than about the person.
    """
    words = key.replace("_", " ").strip()
    return words[:1].upper() + words[1:] if words else words
