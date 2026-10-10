#!/usr/bin/env python3
"""Everything built and everything we could add, on one list and one map.

rich asked (2026-10-10) for one overview to plan the next batch: what we have,
what each candidate source could add, each with its title, description and
category, and a check that the additions bring DIVERSITY rather than more of the
same. This script assembles that list; the page that shows it is built from its
output.

Sources of rows, each read from the file that already owns it:

  built        scripts/experiments_table.collect() — the 63 built experiments
  DEL          data/catalog/del_experiments.json — 29 candidates, read 2026-10-10
  TESS         data/catalog/uk_priority.json for the 56 ready, unbuilt studies
               not in SocSci210 (tess64 below), with their priority scores
  Innovation   data/catalog/innovation_panel_experiments.json, unbuilt `build`
  Panel        and `marginal` verdicts
  Dataverse    data/catalog/dataverse_sweep.json, deposits Jev read as a UK
               sample AND a survey experiment, conjoint or list experiment

**Category.** Every row gets one of the manifest's eight categories, so the two
layers are counted in one taxonomy. Built rows keep the editorial category they
already have. Candidates from TESS, DEL and Dataverse are categorised by Jev
(`Choice`, with a NONE_OF_THESE option, confidence kept). Innovation Panel
candidates are mapped BY HAND below, because `jev.RESTRICTED` refuses anything
UKDS, titles included — the embedding gate admits UKDS public documentation, the
judge does not, and this script does not get to widen either.

**Diversity.** Every title is embedded (`embed.py`, voyage-3-large, titles only:
one register per map, per coverage_map.py's docstring). For each candidate,
`nearest_built` is its most similar built experiment and `novelty` is
1 - cosine similarity to it: near 0 means we already have something like it.
The 2D position reuses coverage_map's saved UMAP fit, so the built dots sit
where they have always sat.

Writes data/catalog/corpus_overview.json (titles, descriptions, categories,
scores — study metadata only).

    source ~/.bash_profile && uv run python scripts/corpus_overview.py
"""

from __future__ import annotations

import csv
import json
import pickle
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from micromotives_datasets import embed  # noqa: E402

CAT = ROOT / "data" / "catalog"
OUT = CAT / "corpus_overview.json"
FIT = CAT / "coverage_map_umap.pkl"
MANIFEST = CAT / "experiment_manifest.json"

# The 64 ready TESS studies of 2026-10-10: data and questionnaire on OSF, not in
# SocSci210, not built. 56 carry a priority score; the rest are listed unscored.
TESS_READY_FILTER = {"buildable": "yes", "has_questionnaire": "yes", "in_socsci210": "no"}

# Innovation Panel candidates, categorised by hand (Jev may not see UKDS text).
# Grouped by the catalogue's own category, with per-experiment exceptions where
# the group's default would misfile one.
IP_BY_CATEGORY = {
    "question-form": "survey methodology",
    "consent": "survey methodology",
    "sensitive": "survey methodology",
    "family-care": "work/family/gender",
    "work-money": "economics/behavioural",
    "health": "health communication",
    "wellbeing": "moral/social/cognition",
    "technology": "economics/behavioural",
    "attitudes": "political preferences/policy",
}
IP_EXCEPTIONS = {
    "9.16": "survey methodology",  # social desirability bias in immigration attitudes
    "9.38": "political identity/polarisation",  # national identity
    "9.40": "moral/social/cognition",  # cognitive reflection, motivated reasoning
    "9.41": "survey methodology",  # robustness of climate-worry MEASUREMENT
}


def _vocabulary() -> dict[str, str]:
    vocab = json.loads(MANIFEST.read_text())["_category_vocabulary"]
    return {k: v for k, v in vocab.items() if not k.startswith("_")}


def built_rows() -> list[dict[str, Any]]:
    from experiments_table import collect

    ip = {r["id"]: r for r in json.loads((CAT / "innovation_panel_experiments.json").read_text())}
    out = []
    for e in collect():
        title = e.title
        if e.source == "innovation_panel":
            # The recipe title is "Understanding Society Innovation Panel, experiment
            # 9.13: ...". Embedding that prefix would cluster every IP build on the
            # boilerplate, so the catalogue's own title stands in for it.
            m = re.search(r"experiment (\d+\.\d+)", title)
            if m and m.group(1) in ip:
                title = ip[m.group(1)]["title"]
        licence = {
            "innovation_panel": "ukds-public-documentation",
        }.get(e.source, "public-metadata")
        out.append(
            {
                "key": f"built:{e.recipe}",
                "id": e.recipe,
                "status": "built",
                "source": {
                    "tess": "TESS (US)",
                    "dataverse": "Harvard Dataverse (UK)",
                    "innovation_panel": "Innovation Panel (UK)",
                }.get(e.source, e.source),
                "title": title,
                "description": e.description or "",
                "category": e.category,
                "category_by": "editorial",
                "rows": e.rows,
                "licence": licence,
            }
        )
    return out


def del_rows() -> list[dict[str, Any]]:
    data = json.loads((CAT / "del_experiments.json").read_text())
    return [
        {
            "key": f"del:{x['id']}",
            "id": x["id"],
            "status": f"candidate ({x['status']})",
            "source": "DEL (UK)",
            "title": x["title"],
            "description": f"{x['versions']} versions. {x['what_varies']}. Answer: {x['answer']}.",
            "licence": "CC0 1.0",
        }
        for x in data["experiments"]
    ]


def tess_rows() -> list[dict[str, Any]]:
    built = {r["id"].split("_")[0] for r in built_rows()}
    cat = list(csv.DictReader((CAT / "tess_uk_foundation_sources.csv").open()))
    prio = {p["study_id"]: p for p in json.loads((CAT / "uk_priority.json").read_text())}
    out = []
    for r in cat:
        code = r["study_id"] or r["osf_code"]
        if code in built or any(r[k] != v for k, v in TESS_READY_FILTER.items()):
            continue
        p = prio.get(code)
        out.append(
            {
                "key": f"tess:{code}",
                "id": code,
                "status": "candidate" if p else "candidate (unscored)",
                "source": "TESS (US)",
                "title": r["title"],
                "description": f"TESS {r['year']}.",
                "category": r["category"],
                "category_by": "TESS catalogue",
                "priority": round(_priority(p), 3) if p else None,
                "transfer": (p or {}).get("transfer") or None,
                "licence": "public-metadata",
            }
        )
    return out


def _priority(p: dict[str, Any]) -> float:
    """uk_priority.Priority.score, restated so this script needs no Jev import."""
    bonus = {"full": 0.10, "mechanism-only": 0.0, "us-specific": -0.30}.get(
        p.get("transfer") or "", 0.0
    )
    return float(p["relevance"]) / 4 + 0.15 * (float(p["evergreen"]) / 4) + bonus


def ip_rows() -> list[dict[str, Any]]:
    built_ids = {
        "9.10",
        "9.18",
        "9.39",
        "9.36",
        "9.24",
        "9.4",
        "9.17",
        "9.31",
        "9.42",
        "9.20",
        "9.13",
        "9.9",
        "9.47",
    }
    out = []
    for r in json.loads((CAT / "innovation_panel_experiments.json").read_text()):
        if r["verdict"] not in ("build", "marginal") or r["id"] in built_ids:
            continue
        out.append(
            {
                "key": f"ip:{r['id']}",
                "id": f"IP {r['id']}",
                "status": "candidate" if r["verdict"] == "build" else "candidate (marginal)",
                "source": "Innovation Panel (UK)",
                "title": r["title"],
                "description": (r.get("description") or r.get("reason") or "").strip(),
                "category": IP_EXCEPTIONS.get(r["id"], IP_BY_CATEGORY[r["category"]]),
                "category_by": "hand map",
                "licence": "ukds-public-documentation",
            }
        )
    return out


def dataverse_rows() -> list[dict[str, Any]]:
    path = CAT / "dataverse_sweep.json"
    if not path.exists():
        return []
    out = []
    for gid, d in json.loads(path.read_text())["deposits"].items():
        s = d.get("screen")
        if not s:
            continue
        if s["uk_sample"]["value"] not in ("uk_only", "uk_among_others"):
            continue
        if s["design"]["value"] not in ("survey_experiment", "conjoint", "list_experiment"):
            continue
        out.append(
            {
                "key": f"dv:{gid}",
                "id": gid.removeprefix("doi:10.7910/DVN/"),
                "status": "candidate (unscreened)",
                "source": "Harvard Dataverse sweep (UK)",
                "title": d.get("title") or gid,
                "description": (d.get("description") or "")[:400],
                "design": s["design"]["value"],
                "uk_sample": s["uk_sample"]["value"],
                "has_data": d.get("has_data"),
                "licence_name": d.get("licence"),
                "licence": "public-metadata",
            }
        )
    return out


def categorise(rows: list[dict[str, Any]], previous: dict[str, dict[str, Any]]) -> None:
    """Jev picks a category for each candidate that has none. Cached by key."""
    todo = [r for r in rows if "category" not in r]
    for r in todo:
        if r["key"] in previous and previous[r["key"]].get("category_by") == "jev":
            for k in ("category", "category_by", "category_conf"):
                r[k] = previous[r["key"]][k]
    todo = [r for r in rows if "category" not in r]
    if not todo:
        return
    from micromotives_datasets import jev

    vocab = _vocabulary()
    cli = jev.client("tess+dataverse")
    for r in todo:
        ans = jev.categorise_experiment(
            cli, r["title"], r["description"], tuple(vocab), tuple(vocab.values())
        )
        r["category"] = ans.value
        r["category_by"] = "jev"
        r["category_conf"] = round(ans.confidence, 3)


def diversity(rows: list[dict[str, Any]]) -> None:
    items = [embed.Text(key=r["key"], text=r["title"], licence=r["licence"]) for r in rows]
    vecs = embed.embed(items)
    m = np.array([vecs[r["key"]] for r in rows], dtype=np.float32)
    m /= np.linalg.norm(m, axis=1, keepdims=True)
    built = [i for i, r in enumerate(rows) if r["status"] == "built"]
    sims = m @ m[built].T
    for i, r in enumerate(rows):
        s = sims[i].copy()
        if r["status"] == "built":
            s[built.index(i)] = -1.0  # a built row's nearest OTHER built row
        j = int(np.argmax(s))
        r["nearest_built"] = rows[built[j]]["id"]
        r["nearest_built_title"] = rows[built[j]]["title"]
        r["novelty"] = round(1.0 - float(s[j]), 4)
    with FIT.open("rb") as handle:
        reducer = pickle.load(handle)
    for r, (x, y) in zip(rows, reducer.transform(m), strict=True):
        r["x"], r["y"] = round(float(x), 4), round(float(y), 4)


def main() -> None:
    previous = {}
    if OUT.exists():
        previous = {r["key"]: r for r in json.loads(OUT.read_text())["rows"]}
    rows = built_rows() + del_rows() + tess_rows() + ip_rows() + dataverse_rows()
    categorise(rows, previous)
    diversity(rows)
    for r in rows:
        r.pop("licence", None)
    OUT.write_text(
        json.dumps(
            {
                "_about": __doc__.strip().splitlines()[0],
                "categories": _vocabulary(),
                "rows": rows,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    from collections import Counter

    print(Counter((r["status"].split(" ")[0], r["source"]) for r in rows))
    print(f"wrote {OUT.relative_to(ROOT)}: {len(rows)} rows")


if __name__ == "__main__":
    main()
