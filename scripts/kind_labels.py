"""The kind of each experiment, named the way the experiment builder names it.

One record: data/catalog/experiment_kinds.json (keys "text:<recipe>" and "image:<id>"),
named through data/catalog/design_kinds.json (refreshed from GET /v1/design/kinds), so
every tracker shows the same words and none keeps a second copy (rich, 24 Nov 2026).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECORDED = ROOT / "data" / "catalog" / "experiment_kinds.json"
DESIGN = ROOT / "data" / "catalog" / "design_kinds.json"
NOT_LABELLED = "Not labelled"


def builder_names() -> dict[str, str]:
    """Kind id -> 'Choice test (type 4, conjoint)'."""
    out = {}
    for k in json.loads(DESIGN.read_text())["kinds"]:
        also = (k.get("also_called") or "").split(",")[0].strip()
        out[k["id"]] = f"{k['name']} (type {k['type']}" + (f", {also})" if also else ")")
    return out


def label(key: str, recorded: dict | None = None, names: dict | None = None) -> str:
    """The builder's name for one experiment's kind, or 'Not labelled'."""
    recorded = recorded if recorded is not None else json.loads(RECORDED.read_text())["kinds"]
    names = names if names is not None else builder_names()
    kind = recorded.get(key, {}).get("kind")
    return names.get(kind, NOT_LABELLED) if kind else NOT_LABELLED


def labels_for(keys: list[str]) -> str:
    """Several experiments' kinds, distinct, joined; 'Not labelled' if none is recorded."""
    recorded = json.loads(RECORDED.read_text())["kinds"]
    names = builder_names()
    found = [label(k, recorded, names) for k in keys]
    known = [f for f in found if f != NOT_LABELLED]
    return " / ".join(dict.fromkeys(known)) if known else NOT_LABELLED
