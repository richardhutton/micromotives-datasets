#!/usr/bin/env python3
"""Add the Development Engagement Lab's persona labels to the crosswalk.

DEL is fielded by YouGov and carries the same profile block as the UK Dataverse
studies, so almost every label is already mapped (the first DEL build's QC found
one field short). The exception is religion: DEL's YouGov list has a
"Pentecostal" option that `uk_yougov_religion` (built from PZB01G's older list)
does not.

The DEL label itself is cut off by SPSS in every DEL file and every codebook —
"Yes - Pentecostal (e.g. Assemblies of God, Elim Pentecostal Church, New
Testament Church of God, Redeemed Christian Chur" — so the full wording exists
nowhere in the deposit. The recipe keeps the label's complete head, "Yes -
Pentecostal" (the source's own words; only the example list is lost, by the
a42yg precedent of dropping a broken tail), and that head is what is mapped
here. The crosswalk's own rule applies: strip "Yes - ", keep every denomination
as its own category, collapse nothing.

    uv run python scripts/persona_del.py            # report
    uv run python scripts/persona_del.py --write    # save
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

CATALOG = Path(__file__).resolve().parents[1] / "data" / "catalog"

SCHEME = "uk_yougov_religion"
ADD: dict[str, dict[str, str]] = {"religion": {"Yes - Pentecostal": "Pentecostal"}}
NEW_CANONICAL: dict[str, list[str]] = {"religion": ["Pentecostal"]}


def apply_to(field: str, data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Extend the scheme, and report anything the addition would contradict."""
    problems: list[str] = []
    canonical = dict(data["canonical"])
    for value in NEW_CANONICAL.get(field, []):
        canonical.setdefault(value, value)
    for source, target in ADD[field].items():
        if target not in canonical.values():
            problems.append(f"{source!r} -> {target!r}, which is not canonical")
        for scheme, mapping in data["schemes"].items():
            if source in mapping and mapping[source] != target:
                problems.append(f"{source!r} is {mapping[source]!r} in {scheme}")
    out = dict(data)
    out["canonical"] = canonical
    out["schemes"] = {**data["schemes"], SCHEME: {**data["schemes"][SCHEME], **ADD[field]}}
    return out, problems


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    for field in ADD:
        path = CATALOG / f"persona_crosswalk_{field}.json"
        updated, problems = apply_to(field, json.loads(path.read_text()))
        print(f"{field}: +{list(ADD[field])}")
        for p in problems:
            print(f"    PROBLEM {p}")
        if problems:
            raise SystemExit("nothing written")
        if args.write:
            path.write_text(json.dumps(updated, indent=2) + "\n")
            print(f"    wrote {path.name}")


if __name__ == "__main__":
    main()
