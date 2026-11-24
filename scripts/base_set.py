#!/usr/bin/env python3
"""Render the base-set tracker: our own SocSci210-like dataset and where every study goes.

rich (23 Nov 2026): stage 1 trains a base model on our own version of SocSci210, rebuilt
from the original materials because SocSci210's condition text is wrong in most studies
audited (LEDGER, "Audit of SocSci210"); stage 2 tunes it on the UK set. Each study lives in
exactly one place: Base (stage 1), UK (stage 2), Eval (SocSci210's 40 held-out studies,
never trained on) or Review (UK fit not decided). New studies that are not UK-compatible
join Base; UK-compatible ones go to the UK set.

    data/catalog/base_set.json     one row per study
    docs/trackers/base_set.html    generated page

    uv run python scripts/base_set.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "catalog" / "base_set.json"
HTML = ROOT / "docs" / "trackers" / "base_set.html"
TEMPLATE = ROOT / "scripts" / "base_set_template.html"

SETS = {"Base", "UK", "Eval", "Review"}
STATUSES = {"Built", "To build", "To map", "Materials needed", "Unlikely"}


def main() -> None:
    rows = json.loads(DATA.read_text())["rows"]
    for r in rows:
        if r["set"] not in SETS:
            raise SystemExit(f"{r['id']}: unknown set {r['set']!r}")
        if r["status"] not in STATUSES:
            raise SystemExit(f"{r['id']}: unknown status {r['status']!r}")
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise SystemExit("a study is listed twice: each study lives in exactly one set")
    payload = json.dumps({"rows": rows}, ensure_ascii=False).replace("</", "<\\/")
    HTML.write_text(TEMPLATE.read_text().replace("__DATA__", payload))
    print(f"wrote {HTML.relative_to(ROOT)}: {len(rows)} studies")


if __name__ == "__main__":
    main()
