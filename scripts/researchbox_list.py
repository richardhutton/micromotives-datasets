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

import kind_labels

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "catalog" / "researchbox_list.json"
KINDS = ROOT / "data" / "catalog" / "design_kinds.json"
RECORDED = ROOT / "data" / "catalog" / "experiment_kinds.json"
RECIPES = ROOT / "recipes"
PROCESSED = ROOT / "data" / "processed"
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
    # Each built box lists the experiments built from it (rich, 19 Nov 2026), read from the
    # recipes, the recorded kinds and the built rows, so the page cannot drift from them.
    recorded = json.loads(RECORDED.read_text())["kinds"]
    areas_file = ROOT / "data" / "catalog" / "experiment_areas.json"
    areas = json.loads(areas_file.read_text())["areas"] if areas_file.exists() else {}
    built: dict[int, list[dict[str, object]]] = {}
    for path in sorted(RECIPES.glob("researchbox*.yaml")):
        box = int(path.stem.removeprefix("researchbox").split("_")[0])
        title = next(
            (
                ln.split(":", 1)[1].strip().strip("'\"")
                for ln in path.read_text().splitlines()
                if ln.startswith("title:")
            ),
            path.stem,
        )
        rows_file = PROCESSED / f"{path.stem}.parquet"
        n = None
        if rows_file.exists():
            import pyarrow.parquet as pq

            n = pq.ParquetFile(rows_file).metadata.num_rows
        built.setdefault(box, []).append(
            {
                "name": path.stem,
                "title": title,
                "kind": recorded.get(f"text:{path.stem}", {}).get("kind", ""),
                "kind_label": kind_labels.label(f"text:{path.stem}"),
                "area": areas.get(f"text:{path.stem}", {}).get("area", ""),
                "rows": n,
            }
        )
    rows_out = [dict(r, experiments=built.get(r["box"], [])) for r in data["rows"]]
    payload = json.dumps({"rows": rows_out, "kinds": kinds}, ensure_ascii=False).replace(
        "</", "<\\/"
    )
    HTML.write_text(TEMPLATE.read_text().replace("__DATA__", payload))
    print(f"wrote {HTML.relative_to(ROOT)}: {len(data['rows'])} ResearchBox boxes")


if __name__ == "__main__":
    main()
