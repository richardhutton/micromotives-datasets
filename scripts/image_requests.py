#!/usr/bin/env python3
"""Render the image-data email tracker page from its local data file.

rich asked (2026-10-26) for the tracker to live locally, like the experiment list,
with no remote copy. One data file, one generated page:

    data/catalog/image_contacts.json   one row per person emailed (study metadata,
                                       public researcher addresses, our emails)
    docs/trackers/image_requests.html  generated page

Statuses: todo, ready, sent, chased, yes, no, notneeded.

    uv run python scripts/image_requests.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "catalog" / "image_contacts.json"
HTML = ROOT / "docs" / "trackers" / "image_requests.html"
TEMPLATE = ROOT / "scripts" / "image_requests_template.html"

STATUSES = {"todo", "ready", "sent", "chased", "yes", "no", "notneeded"}


def main() -> None:
    rows = json.loads(DATA.read_text())
    bad = [r["id"] for r in rows if r["status"] not in STATUSES]
    if bad:
        raise SystemExit(f"unknown status on: {', '.join(bad)}")
    rows.sort(key=lambda r: r["order"])
    payload = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    HTML.write_text(TEMPLATE.read_text().replace("__DATA__", payload))
    print(f"wrote {HTML.relative_to(ROOT)}: {len(rows)} contacts")
    # The image experiments page takes its Permission column from this same data,
    # so it is regenerated in the same step: the two pages cannot drift apart.
    import runpy

    runpy.run_path(str(ROOT / "scripts" / "image_experiments.py"), run_name="__main__")


if __name__ == "__main__":
    main()
