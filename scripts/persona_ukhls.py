#!/usr/bin/env python3
"""Map the Innovation Panel's persona labels into the corpus vocabulary.

Every UKDS build so far has ended with QC rule 14 reporting its persona values as
outside the canonical vocabulary — 6 education labels, 11 employment, 19
ethnicity, 10 marital status, 12 region, all unmapped. That is the designed
behaviour (`crosswalk.py`: "a label with no mapping is left ALONE"), and it means
the corpus currently describes the same person two ways depending on which study
they came from. Sixteen more Innovation Panel builds would repeat it sixteen
times, so it is cheaper to map once now than to rebuild later.

These are UKHLS derived variables: `hiqual_dv`, `jbstat`, `racel_dv`,
`mastat_dv`, `gor_dv`. One scheme per field, following the existing files'
structure, and written here rather than typed into the JSON so the judgement is
reviewable and re-runnable.

**Education follows precedent rather than inventing a ladder.** The four
canonical levels are a US high-school ladder inherited from the TESS layer, and
seven UK studies already share one YouGov 18-level scheme that maps into it —
"GCE A level or Higher Certificate" and "GCSE" both to High school, first and
higher degrees both to Bachelors to postgraduate, "Other technical, professional
or higher qualification" to Some college. UKHLS's six-level `hiqual_dv` is a
coarsening of exactly that ladder, so it maps the same way. Deciding otherwise
would make UKHLS rows incomparable with the seven UK studies already built.

**Ethnicity maps to the UK canonical values, which already exist.** The vocabulary
carries both US census categories (black, white, asian, hispanic) and UK ones
("Asian or Asian British", "Black, Black British, Caribbean or African", "Mixed or
Multiple ethnic groups", "Other ethnic group"), because an earlier UK study
needed them. UKHLS's `racel_dv` labels helpfully carry their census grouping in
brackets — "Bangladeshi (Asian or Asian British)" — so the mapping is read off
the label rather than guessed.

**Region needs one new canonical value.** The canonical list has the eleven
Great Britain regions and no Northern Ireland, because no study so far sampled
there. The Innovation Panel does. Adding it is the honest fix; mapping Northern
Ireland onto something else would be a falsehood about where someone lives.

**Two mappings that lose information, declared rather than hidden.** UKHLS
separates "A former civil partner" and "A surviving civil partner" from
"Separated from civil partner"; the canonical vocabulary has one Civil
Partnership value and no dissolution states. And "Looking after family or home"
is not unemployment in UKHLS's sense and is not any canonical employment state
either, so it goes to the residual `Other`. Both are coarsenings the raw `.sav`
still holds.

    uv run python scripts/persona_ukhls.py --check
    uv run python scripts/persona_ukhls.py --write
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

CATALOG = Path(__file__).resolve().parents[1] / "data" / "catalog"
SCHEME = "uk_ukhls_innovation_panel"

SCHEMES: dict[str, dict[str, str]] = {
    "education": {
        "No qualification": "Less than high school",
        "GCSE etc": "High school",
        "A-level etc": "High school",
        "Other qualification": "Some college to associate",
        "Degree": "Bachelors to postgraduate",
        "Other higher degree": "Bachelors to postgraduate",
    },
    "employment": {
        "In paid employment (full or part-time)": "Employed (hours not distinguished)",
        "Self employed": "Self employed",
        "Working in an apprenticeship": "Employed (hours not distinguished)",
        "On maternity leave": "Employed (hours not distinguished)",
        "Unpaid worker in family business": "Employed (hours not distinguished)",
        "On a government training scheme": "Full time student",
        "Full-time student": "Full time student",
        "Retired": "Retired",
        "Long term sick or disabled": "Disabled",
        "Looking after family or home": "Other",
        "Doing something else": "Other",
    },
    "ethnicity": {
        "British/English/Scottish/Welsh/Northern Irish/White British/White Scottish (White)": "White",
        "Irish (White)": "White",
        "Gypsy or Irish Traveller (White)": "White",
        "Roma": "White",
        "Any Other White Background (White)": "White",
        "Mixed: White and Black Caribbean": "Mixed or Multiple ethnic groups",
        "Mixed: White and Black African": "Mixed or Multiple ethnic groups",
        "Mixed: White and Asian": "Mixed or Multiple ethnic groups",
        "Mixed: Any Other Mixed Background": "Mixed or Multiple ethnic groups",
        "Indian (Asian or Asian British)": "Asian or Asian British",
        "Pakistani (Asian or Asian British)": "Asian or Asian British",
        "Bangladeshi (Asian or Asian British)": "Asian or Asian British",
        "Chinese (Asian or Asian British)": "Asian or Asian British",
        "Any Other Asian Background (Asian or Asian British)": "Asian or Asian British",
        "Caribbean (Black/Africa/Caribbean/Black British)": (
            "Black, Black British, Caribbean or African"
        ),
        "African (Black/African/Caribbean/Black British)": (
            "Black, Black British, Caribbean or African"
        ),
        "Any Other Black Background (Black/African/Caribbean/Black British)": (
            "Black, Black British, Caribbean or African"
        ),
        "Arab (Other Ethnic Group)": "Other ethnic group",
        "Any Other Ethnic Group (Other Ethnic Group)": "Other ethnic group",
    },
    "marital_status": {
        "Single and never married/in civil partnership": "Never married",
        "Married": "Married",
        "Living as couple": "Living as married",
        "In a registered same-sex civil partnership": "Civil Partnership",
        "Separated but legally married": "Separated (after being married)",
        "Divorced": "Divorced",
        "Widowed": "Widowed",
        "Separated from civil partner": "Civil Partnership",
        "A former civil partner": "Civil Partnership",
        "A surviving civil partner": "Civil Partnership",
    },
    # Eleven of the twelve are already the canonical spelling exactly. Written
    # out in full anyway: an identity mapping that is DECLARED survives a change
    # to either vocabulary, and one that is merely true by coincidence does not.
    "region": {
        "North East": "North East",
        "North West": "North West",
        "Yorkshire and the Humber": "Yorkshire and the Humber",
        "East Midlands": "East Midlands",
        "West Midlands": "West Midlands",
        "East of England": "East of England",
        "London": "London",
        "South East": "South East",
        "South West": "South West",
        "Wales": "Wales",
        "Scotland": "Scotland",
        "Northern Ireland": "Northern Ireland",
    },
}

# Canonical values this adds. Only one, and it is a place that exists.
NEW_CANONICAL: dict[str, list[str]] = {"region": ["Northern Ireland"]}


def load(field: str) -> dict[str, Any]:
    return json.loads((CATALOG / f"persona_crosswalk_{field}.json").read_text())


def apply_to(field: str, data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Add this scheme, and report anything it would contradict."""
    problems: list[str] = []
    canonical = dict(data["canonical"])
    for value in NEW_CANONICAL.get(field, []):
        canonical.setdefault(value, value)

    targets = set(canonical.values())
    for source, target in SCHEMES[field].items():
        if target not in targets:
            problems.append(f"{field}: {source!r} -> {target!r}, which is not canonical")

    # `Crosswalk.load` flattens every scheme into one map and asserts no label
    # means two different things. Checked here so the failure names the clash
    # rather than surfacing as an assertion three layers down.
    for scheme, mapping in data["schemes"].items():
        if scheme == SCHEME:
            continue
        for source, target in SCHEMES[field].items():
            if source in mapping and mapping[source] != target:
                problems.append(
                    f"{field}: {source!r} is {mapping[source]!r} in {scheme} "
                    f"but {target!r} here"
                )

    out = dict(data)
    out["canonical"] = canonical
    out["schemes"] = {**data["schemes"], SCHEME: SCHEMES[field]}
    return out, problems


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="save the crosswalk files")
    ap.add_argument("--check", action="store_true", help="report only (the default)")
    args = ap.parse_args()

    trouble = 0
    for field in SCHEMES:
        data = load(field)
        updated, problems = apply_to(field, data)
        added = [v for v in NEW_CANONICAL.get(field, []) if v not in data["canonical"]]
        note = f"  +canonical {added}" if added else ""
        print(f"{field:<16}{len(SCHEMES[field]):>3} labels mapped{note}")
        for p in problems:
            print(f"    PROBLEM {p}")
        trouble += len(problems)
        if not problems and args.write:
            path = CATALOG / f"persona_crosswalk_{field}.json"
            path.write_text(json.dumps(updated, indent=1, ensure_ascii=False) + "\n")
            print(f"    wrote {path.relative_to(CATALOG.parents[1])}")
    if trouble:
        raise SystemExit(f"{trouble} problem(s); nothing written for those fields")


if __name__ == "__main__":
    main()
