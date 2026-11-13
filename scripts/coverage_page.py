#!/usr/bin/env python3
"""Render the category coverage tracker: text and image experiments on one page.

rich (13 Nov 2026), after reading the SocSci210 paper: one page that shows how the
built corpus spreads across categories, for both training sets, and where the
remaining candidates would add to it. It sits beside the two experiment trackers
rather than inside either, because its whole point is to set the two sets side by
side.

    data/catalog/experiment_list.json        text rows (category, status, rows)
    data/catalog/image_experiment_list.json  image rows (category, status, rows)
    docs/trackers/coverage.html              generated page

Both inputs already carry a category from the one vocabulary in
`experiment_manifest.json`; this script refuses to render if either uses a word
outside it, so a typo cannot open a ninth category on the page.

    uv run python scripts/coverage_page.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = ROOT / "data" / "catalog" / "experiment_list.json"
IMAGE = ROOT / "data" / "catalog" / "image_experiment_list.json"
MANIFEST = ROOT / "data" / "catalog" / "experiment_manifest.json"
HTML = ROOT / "docs" / "trackers" / "coverage.html"
TEMPLATE = ROOT / "scripts" / "coverage_template.html"

BUILT = {"Built", "Built (risky)"}
CANDIDATE = {"Buildable", "Needs checking", "Waiting for images"}


def _text_rows() -> list[dict]:
    """The text list with each Built row's count, as the text tracker computes it."""
    spec = importlib.util.spec_from_file_location(
        "experiment_list", ROOT / "scripts" / "experiment_list.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["experiment_list"] = mod
    spec.loader.exec_module(mod)
    data = json.loads(TEXT.read_text())
    mod.attach_row_counts(data)
    return data["rows"]


def main() -> None:
    vocab = [
        k for k in json.loads(MANIFEST.read_text())["_category_vocabulary"] if not k.startswith("_")
    ]
    items = []
    for r in _text_rows():
        items.append(
            {
                "set": "Text",
                "id": r.get("recipe") or r["id"],
                "title": r["title"],
                "source": r["source"],
                "category": r["category"],
                "status": r["status"],
                "rows": r.get("rows") if r["status"] in BUILT else None,
            }
        )
    for r in json.loads(IMAGE.read_text())["rows"]:
        items.append(
            {
                "set": "Image",
                "id": r["id"],
                "title": r["title"],
                "source": r.get("sample") or "",
                "category": r.get("category"),
                "status": r["status"],
                "rows": r.get("rows") if r["status"] in BUILT else None,
            }
        )
    # Jev's category check and the title map (scripts/coverage_points.py), joined by
    # key. An experiment added since the last run simply has neither yet.
    points_file = ROOT / "data" / "catalog" / "coverage_points.json"
    points = {}
    if points_file.exists():
        points = {p["key"]: p for p in json.loads(points_file.read_text())["points"]}
    for i in items:
        p = points.get(f"{i['set'].lower()}:{i['id']}")
        if p and p.get("title") == i["title"]:
            i["jev"], i["x"], i["y"] = p.get("jev"), p.get("x"), p.get("y")
            i["jev_held"] = p.get("jev") is None
    stray = sorted({str(i["category"]) for i in items} - set(vocab))
    if stray:
        raise SystemExit(f"categories outside the manifest vocabulary: {stray}")
    for i in items:
        i["kind"] = (
            "built" if i["status"] in BUILT else "candidate" if i["status"] in CANDIDATE else "out"
        )
        if i["kind"] == "built" and not i["rows"]:
            raise SystemExit(f"{i['set']} {i['id']}: built but no row count")
    payload = json.dumps({"categories": vocab, "items": items}, ensure_ascii=False).replace(
        "</", "<\\/"
    )
    HTML.write_text(TEMPLATE.read_text().replace("__DATA__", payload))
    built = [i for i in items if i["kind"] == "built"]
    print(
        f"wrote {HTML.relative_to(ROOT)}: {len(built)} built experiments, "
        f"{sum(i['rows'] for i in built):,} rows, {sum(i['kind'] == 'candidate' for i in items)} candidates"
    )


if __name__ == "__main__":
    main()
