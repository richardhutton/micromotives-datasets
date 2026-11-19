#!/usr/bin/env python3
"""Render the ResearchBox experiments tracker from its local data file.

rich (19 Nov 2026): ResearchBox is a large new source of consumer and pricing
experiments, kept on its own tracker so it can be seen, and later exported, apart
from the text and image lists.

    data/catalog/researchbox_list.json          one row per public box with data
    docs/trackers/researchbox_experiments.html  generated page

    uv run python scripts/researchbox_list.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "catalog" / "researchbox_list.json"
KINDS = ROOT / "data" / "catalog" / "design_kinds.json"
HTML = ROOT / "docs" / "trackers" / "researchbox_experiments.html"
TEMPLATE = ROOT / "scripts" / "researchbox_list_template.html"

STATUSES = {"Built", "Buildable", "Download needed", "Needs checking", "Unlikely"}


def main() -> None:
    data = json.loads(DATA.read_text())
    kinds = {k["id"]: f"{k['type']} · {k['name']}" for k in json.loads(KINDS.read_text())["kinds"]}
    for r in data["rows"]:
        if r["status"] not in STATUSES:
            raise SystemExit(f"{r['id']}: unknown status {r['status']!r}")
        if r["kind"] and r["kind"] not in kinds:
            raise SystemExit(f"{r['id']}: kind {r['kind']!r} is not in design_kinds.json")
    payload = json.dumps({"rows": data["rows"], "kinds": kinds}, ensure_ascii=False).replace(
        "</", "<\\/"
    )
    HTML.write_text(TEMPLATE.read_text().replace("__DATA__", payload))
    print(f"wrote {HTML.relative_to(ROOT)}: {len(data['rows'])} ResearchBox boxes")


if __name__ == "__main__":
    main()
