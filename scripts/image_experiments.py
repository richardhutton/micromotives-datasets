#!/usr/bin/env python3
"""Render the image experiments tracker from its local data file.

The image counterpart of the text experiments list (rich, 26 Oct 2026): every image
experiment found, its build status, and whether we have permission to use it.

    data/catalog/image_experiment_list.json   one row per image experiment (IMG id)
    docs/trackers/image_experiments.html      generated page

Permission is copied from data/catalog/image_contacts.json, the email tracker's
data, so the two pages cannot disagree about who said yes.

    uv run python scripts/image_experiments.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "catalog" / "image_experiment_list.json"
CONTACTS = ROOT / "data" / "catalog" / "image_contacts.json"
HTML = ROOT / "docs" / "trackers" / "image_experiments.html"
TEMPLATE = ROOT / "scripts" / "image_experiments_template.html"

STATUSES = {"Built", "Buildable", "Waiting for images", "Needs checking", "Unlikely"}
PERMISSION = {
    "yes": "Yes",
    "sent": "Asked",
    "chased": "Asked",
    "ready": "Not asked yet",
    "todo": "Not asked yet",
    "no": "No",
    "notneeded": "Not needed",
}


def main() -> None:
    data = json.loads(DATA.read_text())
    contacts = json.loads(CONTACTS.read_text())
    who = {e["id"]: c for c in contacts for e in c["experiments"]}
    for r in data["rows"]:
        if r["status"] not in STATUSES:
            raise SystemExit(f"{r['id']}: unknown status {r['status']!r}")
        c = who.get(r["id"])
        r["permission"] = PERMISSION[c["status"]] if c else "Not asked yet"
        r["contact"] = c["name"] if c else ""
    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    HTML.write_text(TEMPLATE.read_text().replace("__DATA__", payload))
    print(f"wrote {HTML.relative_to(ROOT)}: {len(data['rows'])} image experiments")


if __name__ == "__main__":
    main()
