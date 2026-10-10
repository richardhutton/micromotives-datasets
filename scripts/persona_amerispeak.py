#!/usr/bin/env python3
"""Add the AmeriSpeak (TESS/NORC) profile labels to four persona crosswalks.

WHY THEY WERE UNMAPPED. `housing_ownership`, `marital_status`, `region` and
`religion` were built from UK schemes only (YouGov, then the Innovation Panel).
No US scheme was ever added to any of the four, so every AmeriSpeak recipe that
maps HOUSING / MARITAL / REGION4 / RELIG has carried a rule 14 warning — not just
8ctbk and s6urt but zaqkm, b87sm and others. The labels that happened to match
a UK canonical by spelling ("Married", "Buddhist") passed; everything else did
not. Nothing chose a wrong scheme: there was no US scheme to choose. And the
warning printed three labels per field (ledger 127): the real count across the
two files is 25, including "West", which sorted fourth and was never shown.

The scheme added here is the full list each questionnaire OFFERS, read from the
value labels of the variables the recipes declare (ledger 64, 66), after the
recipes' own `persona_label_rewrite` (RELIG 1 restored from the questionnaire,
RELIG 14 with its text-box instruction removed). 8ctbk's MARITAL offers five of
s6urt's six options; the scheme is the union and the maps agree.

THE RULE APPLIED, field by field. A US label goes to an existing canonical only
where it denotes the same thing — the UK/US precedent set by ethnicity ("'White'
is the one label both layers map to") and income. Where the US category is a
merge of several UK categories, or a classification the UK list does not make,
it becomes its own canonical value in the source's own words: mapping it onto
one UK category would split a merged category or assert a meaning the source
does not support, and coarsening the UK side to meet it would destroy detail
nobody asked us to lose.

  marital_status
    "Living with partner" -> "Living as married". The Innovation Panel's "Living
      as couple" already lands there; this is the established cohabitation rule.
      It is NOT "Married" — the same list offers Married separately.
    "Separated" -> "Separated (after being married)". In a marital-status list
      that offers "Never married" and "Living with partner" separately, this is
      separation from a spouse, as UKHLS "Separated but legally married" is.
      The riskiest call here: the label does not say "from a spouse" itself.
    Married / Widowed / Divorced / Never married: already canonical, listed so
      the scheme is declared whole.
  region — US Census regions. No UK region is the same place, so all four are
    new canonical values, unchanged. "Northeast" is not "North East" (England).
  housing_ownership — the Census tenure question. "Owned or being bought" merges
    the UK's outright/mortgage/shared-ownership split; "Rented for cash" merges
    three landlord types and paying rent to family; "Occupied without payment of
    cash rent" is wider than living rent-free with family (it also covers, say,
    housing that comes with a job). None maps; all three are new, unchanged.
  religion
    "Roman Catholic (Catholic)" -> "Roman Catholic"; "Jewish (Judaism)" ->
    "Jewish"; "Muslim (Islam)" -> "Muslim"; "Orthodox (Greek, Russian, or some
    other orthodox church)" -> "Orthodox Christian". The parentheses are glosses
    of the same faith, and the crosswalk already names faiths by the adjective.
    Buddhist / Hindu: already canonical.
    New, unchanged: Protestant (merges Baptist, Methodist, Presbyterian,
    Pentecostal, Episcopalian ... which the UK list keeps apart), Mormon, Just
    Christian, Unitarian, and Atheist / Agnostic / Nothing in particular — three
    distinctions the UK list does not make, so none is folded into "No
    religion", which answers a different question (belonging, not belief).
    "Something else" stays its own value rather than "Other religion": it is the
    residual of a list that includes non-belief options, so it need not be a
    religion at all; residuals are not shared across UK/US (ethnicity precedent).

HOW THIS FOLLOWS THE "TWO VOCABULARIES" DECISION (SocSci-UK_MASTER.md, "The
persona crosswalk is US-anchored"). As in the ethnicity and income files, the US
values sit beside the UK ones in the same file, under their own named scheme, and
a value is shared only where the concept is genuinely the same. No UK scheme or
canonical value is changed, and `persona_harmonise.py` is NOT re-run: its
`canonical()` keeps only boundaries every scheme shares, so feeding it these
schemes would collapse the UK denominations and tenures (and raise on region).
The per-row vocabulary tag that decision also calls for is not built; that is a
schema change and out of scope here.

TYPOGRAPHY VARIANTS, two extra schemes mapping to the SAME targets (the
`uk_gor_capital_the` precedent; typography normalises, words never do):
  us_amerispeak_quoted — dh3nj's .sav wraps every RELIG label in a straight
    opening and curly closing quote ('"Buddhist”'). Same words.
  us_amerispeak_straight_apostrophe — the xk9ch recipes restore RELIG 1 from
    their questionnaire with "Jehovah's" (straight); 8ctbk/s6urt/dh3nj use U+2019.

Each file is rewritten in its own existing style (indent and escaping are
detected by a byte-for-byte round trip, and the script refuses if none
matches), with the new canonical values and the new scheme appended at the end.

    uv run python scripts/persona_amerispeak.py            # report
    uv run python scripts/persona_amerispeak.py --write    # save
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

CATALOG = Path(__file__).resolve().parents[1] / "data" / "catalog"

SCHEME = "us_amerispeak"

PROTESTANT = (
    "Protestant (Baptist, Methodist, Non-denominational, Lutheran, Presbyterian, "
    "Pentecostal, Episcopalian, Reformed, Church of Christ, Jehovah’s Witness, etc.)"
)

ADD: dict[str, dict[str, str]] = {
    "housing_ownership": {
        "Owned or being bought by you or someone in your household": (
            "Owned or being bought by you or someone in your household"
        ),
        "Rented for cash": "Rented for cash",
        "Occupied without payment of cash rent": "Occupied without payment of cash rent",
    },
    "marital_status": {
        "Married": "Married",
        "Widowed": "Widowed",
        "Divorced": "Divorced",
        "Separated": "Separated (after being married)",
        "Never married": "Never married",
        "Living with partner": "Living as married",
    },
    "region": {
        "Northeast": "Northeast",
        "Midwest": "Midwest",
        "South": "South",
        "West": "West",
    },
    "religion": {
        PROTESTANT: PROTESTANT,
        "Roman Catholic (Catholic)": "Roman Catholic",
        "Mormon (Church of Jesus Christ of Latter-day Saints/LDS)": (
            "Mormon (Church of Jesus Christ of Latter-day Saints/LDS)"
        ),
        "Orthodox (Greek, Russian, or some other orthodox church)": "Orthodox Christian",
        "Jewish (Judaism)": "Jewish",
        "Muslim (Islam)": "Muslim",
        "Buddhist": "Buddhist",
        "Hindu": "Hindu",
        "Atheist (do not believe in God)": "Atheist (do not believe in God)",
        "Agnostic (not sure if there is a God)": "Agnostic (not sure if there is a God)",
        "Nothing in particular": "Nothing in particular",
        "Just Christian": "Just Christian",
        "Unitarian (Universalist)": "Unitarian (Universalist)",
        "Something else": "Something else",
    },
}

# dh3nj's RELIG labels as its .sav spells them, minus the wrapping quotes. Only
# the codes the file labels (1-9); code 1 is restored by its recipe and so
# arrives unquoted.
DH3NJ_QUOTED: dict[str, str] = {
    k: v
    for k, v in ADD["religion"].items()
    if k
    in {
        "Roman Catholic (Catholic)",
        "Mormon (Church of Jesus Christ of Latter-day Saints/LDS)",
        "Orthodox (Greek, Russian, or some other orthodox church)",
        "Jewish (Judaism)",
        "Muslim (Islam)",
        "Buddhist",
        "Hindu",
        "Atheist (do not believe in God)",
    }
}

NEW_CANONICAL: dict[str, list[str]] = {
    "housing_ownership": [
        "Owned or being bought by you or someone in your household",
        "Rented for cash",
        "Occupied without payment of cash rent",
    ],
    "region": ["Northeast", "Midwest", "South", "West"],
    "religion": [
        PROTESTANT,
        "Mormon (Church of Jesus Christ of Latter-day Saints/LDS)",
        "Atheist (do not believe in God)",
        "Agnostic (not sure if there is a God)",
        "Nothing in particular",
        "Just Christian",
        "Unitarian (Universalist)",
        "Something else",
    ],
}


def schemes_for(field: str) -> dict[str, dict[str, str]]:
    """The scheme(s) this script adds to one field: the main one plus spellings."""
    out = {SCHEME: dict(ADD[field])}
    if field == "religion":
        # Built FROM the main map, so a variant cannot disagree with it.
        out[SCHEME + "_quoted"] = {f'"{k}\u201d': v for k, v in DH3NJ_QUOTED.items()}
        out[SCHEME + "_straight_apostrophe"] = {
            PROTESTANT.replace("\u2019", "'"): ADD[field][PROTESTANT]
        }
    return out


def apply_to(field: str, data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Extend the crosswalk, and report anything the addition would contradict.

    Re-running on an already-extended file is a no-op, not an error; a scheme
    already present with DIFFERENT content is a problem.
    """
    problems: list[str] = []
    first_time = SCHEME not in data["schemes"]
    canonical = dict(data["canonical"])
    for value in NEW_CANONICAL.get(field, []):
        if first_time and value in canonical.values():
            problems.append(f"{value!r} is declared new but is already canonical")
        canonical.setdefault(value, value)
    schemes = dict(data["schemes"])
    for name, mapping in schemes_for(field).items():
        if name in schemes and schemes[name] != mapping:
            problems.append(f"scheme {name!r} exists with different content")
        for source, target in mapping.items():
            if target not in canonical.values():
                problems.append(f"{source!r} -> {target!r}, which is not canonical")
            for scheme, existing in data["schemes"].items():
                if source in existing and existing[source] != target:
                    problems.append(f"{source!r} is {existing[source]!r} in {scheme}")
        schemes.setdefault(name, mapping)
    out = dict(data)
    out["canonical"] = canonical
    out["schemes"] = schemes
    return out, problems


def style_of(text: str) -> dict[str, Any]:
    """The json.dumps arguments that reproduce this file byte-for-byte."""
    data = json.loads(text)
    for indent in (1, 2, 4):
        for ensure_ascii in (False, True):
            if json.dumps(data, indent=indent, ensure_ascii=ensure_ascii) + "\n" == text:
                return {"indent": indent, "ensure_ascii": ensure_ascii}
    raise SystemExit("no json.dumps style reproduces the existing file; nothing written")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    # Every file is checked before any is written, so a problem in the last
    # field cannot leave the first three half-updated.
    pending: list[tuple[Path, str]] = []
    any_problem = False
    for field in ADD:
        path = CATALOG / f"persona_crosswalk_{field}.json"
        text = path.read_text()
        style = style_of(text)
        updated, problems = apply_to(field, json.loads(text))
        print(f"{field}  ({style})")
        for source, target in ((s_, t) for m in schemes_for(field).values() for s_, t in m.items()):
            mark = "NEW " if target in NEW_CANONICAL.get(field, []) else "    "
            print(f"  {mark}{source!r} -> {target!r}")
        for p in problems:
            print(f"    PROBLEM {p}")
        any_problem = any_problem or bool(problems)
        pending.append((path, json.dumps(updated, **style) + "\n"))
    if any_problem:
        raise SystemExit("nothing written")
    if args.write:
        for path, out in pending:
            path.write_text(out)
            print(f"wrote {path.name}")


if __name__ == "__main__":
    main()
