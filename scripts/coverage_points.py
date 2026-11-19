#!/usr/bin/env python3
"""Check every experiment's category with Jev, and place every experiment on a map.

rich (13 Nov 2026), after the coverage page went up: the image categories were
assigned by eye, and the page had no map like the SocSci210 paper's Figure 2.
This adds both, for built experiments and candidates in the text and image sets.

1. **Category check (Jev).** One `Choice` per experiment over the manifest's eight
   categories plus NONE_OF_THESE (`jev.categorise_experiment`), from its title and
   our one-line description. Jev never overrules the list: the page shows where it
   DISAGREES with the recorded category, with its confidence, and a person decides.
   Innovation Panel experiments are not sent: `jev.client` refuses UKDS material
   outright (see `jev.RESTRICTED`). Image rows whose stimuli sit on UKDS ReShare
   are held back the same way.

2. **Kind (Jev).** One `Choice` per experiment over micromotives-service's eleven
   kinds of experiment (`data/catalog/design_kinds.json`, a snapshot of its
   `GET /v1/design/kinds`) plus NONE_OF_THESE (`jev.kind_of_experiment`), from the
   title, our description and the design notes. A keyword reading of the same text
   (`keyword_kind`) is set beside it, and the page shows where the two disagree.
   Innovation Panel experiments ARE sent for this question: their titles are UKDS's
   public documentation and the descriptions are ours, never labels or rows (rich,
   19 Nov 2026: "yes they can").

3. **Map (Voyage + t-SNE).** Titles only, one register, as `coverage_map.py`
   argues. Each title travels under the licence that clears it in `embed.CLEARED`:
   TESS and Dataverse titles are published metadata, DEL is CC0, Innovation Panel
   titles come from UKDS's own public user guide, and image-list titles are our
   own labels. t-SNE as in the paper, with a fixed seed; the picture is for
   reading clusters, and distances across the map mean little.

Results go to `data/catalog/coverage_points.json` (tracked: metadata only). Jev
answers are cached there by title and description, so a re-run pays only for new
or changed experiments; Voyage vectors are cached by `embed.py`.

    source ~/.bash_profile && uv run python scripts/coverage_points.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from micromotives_datasets import embed, jev  # noqa: E402

TEXT = ROOT / "data" / "catalog" / "experiment_list.json"
IMAGE = ROOT / "data" / "catalog" / "image_experiment_list.json"
MANIFEST = ROOT / "data" / "catalog" / "experiment_manifest.json"
KINDS = ROOT / "data" / "catalog" / "design_kinds.json"
OUT = ROOT / "data" / "catalog" / "coverage_points.json"

KEEP = {"Built", "Built (risky)", "Buildable", "Needs checking", "Waiting for images"}
TITLE_LICENCE = {
    "TESS": "public-metadata",
    "Harvard Dataverse": "public-metadata",
    "DEL": "CC0 1.0",
    "Innovation Panel": "ukds-public-documentation",
    "Zenodo": "public-metadata",
    "Other open archives": "public-metadata",
}
# Who the kind question's text belongs to. Innovation Panel titles are UKDS's public
# documentation (embed.CLEARED); image rows are described in our own words.
KIND_SOURCE = {"Innovation Panel": "ukds-public-documentation"}
JEV_SOURCE = {
    "TESS": "tess",
    "Harvard Dataverse": "dataverse",
    "DEL": "dataverse",
    "Zenodo": "zenodo",
    "Other open archives": "osf+figshare+eidc",
}


def items() -> list[dict]:
    design = {
        k: v.get("design") or "" for k, v in json.loads(MANIFEST.read_text())["experiments"].items()
    }
    out = []
    for r in json.loads(TEXT.read_text())["rows"]:
        if r["status"] in KEEP:
            out.append(
                {
                    "key": f"text:{r.get('recipe') or r['id']}",
                    "set": "Text",
                    "source": r["source"],
                    "title": r["title"],
                    "description": r.get("description") or "",
                    "category": r["category"],
                    "status": r["status"],
                    "licence": TITLE_LICENCE[r["source"]],
                    "jev_source": JEV_SOURCE.get(r["source"]),
                    "kind_source": KIND_SOURCE.get(r["source"], JEV_SOURCE.get(r["source"])),
                    "design": " ".join(
                        x
                        for x in (r.get("details") or "", design.get(r.get("recipe") or "", ""))
                        if x
                    ),
                }
            )
    for r in json.loads(IMAGE.read_text())["rows"]:
        if r["status"] in KEEP:
            ukds = "ukdataservice" in (r.get("link") or "")
            out.append(
                {
                    "key": f"image:{r['id']}",
                    "set": "Image",
                    "source": r.get("sample") or "",
                    "title": r["title"],
                    "description": r.get("description") or "",
                    "category": r["category"],
                    "status": r["status"],
                    "licence": "own-wording",
                    "jev_source": None if ukds else "osf+tess+dataverse",
                    "kind_source": "own-wording" if ukds else "osf+tess+dataverse",
                    "design": "",
                }
            )
    return out


def _digest(it: dict) -> str:
    return hashlib.sha256(f"{it['title']}\n{it['description']}".encode()).hexdigest()[:16]


def check_categories(rows: list[dict], previous: dict[str, dict]) -> None:
    vocab = {
        k: v
        for k, v in json.loads(MANIFEST.read_text())["_category_vocabulary"].items()
        if not k.startswith("_")
    }
    clients: dict[str, object] = {}
    asked = 0
    for it in rows:
        it["digest"] = _digest(it)
        old = previous.get(it["key"])
        if old and old.get("digest") == it["digest"] and "jev" in old:
            it["jev"] = old["jev"]
            continue
        if it["jev_source"] is None:
            it["jev"] = None
            continue
        cli = clients.setdefault(it["jev_source"], jev.client(it["jev_source"]))
        v = jev.categorise_experiment(
            cli, it["title"], it["description"], tuple(vocab), tuple(vocab.values())
        )
        it["jev"] = {
            "choice": v.value,
            "confidence": round(v.confidence, 3),
            "runner_up": v.runners_up[0][0] if v.runners_up else None,
            "runner_up_confidence": round(v.runners_up[0][1], 3) if v.runners_up else None,
        }
        asked += 1
        if asked % 25 == 0:
            print(f"  jev: {asked} asked", flush=True)
    print(f"jev: {asked} new calls, {sum(1 for i in rows if i.get('jev'))} answered")


# Words that name a design outright, most specific first. Only a cross-check on Jev:
# a description that names no method gets no keyword answer.
KEYWORDS = [
    ("priority", r"max ?diff|best[- ]worst"),
    ("head_to_head", r"head[- ]to[- ]head|paired comparison|pairwise"),
    ("sensitive_count", r"list experiment|item count"),
    ("choice", r"conjoint|discrete choice"),
    ("shelf", r"choice set|shelf|vending"),
    ("story", r"vignette"),
    ("context", r"question order|priming|primed|order of (the )?questions"),
    ("mix", r"\d+ ?[x×] ?\d+|factorial|crossed with"),
    ("lineup", r"within[- ]subject|each (person|respondent) (sees|rates) (all|every|\d+)"),
    ("baseline", r"\b(1|one|single) condition\b|no experiment"),
]


def keyword_kind(it: dict) -> str | None:
    text = f"{it['title']} {it['description']} {it['design']}".lower()
    for kind, pattern in KEYWORDS:
        if re.search(pattern, text):
            return kind
    return None


def check_kinds(rows: list[dict], previous: dict[str, dict]) -> None:
    kinds = json.loads(KINDS.read_text())["kinds"]
    names = tuple(k["id"] for k in kinds)
    meanings = tuple(f"{k['name']} ({k['also_called']}): answers {k['answers']}" for k in kinds)
    clients: dict[str, object] = {}
    asked = 0
    for it in rows:
        it["keyword_kind"] = keyword_kind(it)
        it["kind_digest"] = hashlib.sha256(
            f"{it['title']}\n{it['description']}\n{it['design']}".encode()
        ).hexdigest()[:16]
        old = previous.get(it["key"])
        if old and old.get("kind_digest") == it["kind_digest"] and old.get("jev_kind"):
            it["jev_kind"] = old["jev_kind"]
            continue
        cli = clients.setdefault(it["kind_source"], jev.client(it["kind_source"]))
        text = it["description"] + (f"\n\nDesign: {it['design']}" if it["design"] else "")
        v = jev.kind_of_experiment(cli, it["title"], text, names, meanings)
        it["jev_kind"] = {
            "choice": v.value,
            "confidence": round(v.confidence, 3),
            "runner_up": v.runners_up[0][0] if v.runners_up else None,
            "runner_up_confidence": round(v.runners_up[0][1], 3) if v.runners_up else None,
        }
        asked += 1
        if asked % 25 == 0:
            print(f"  jev kind: {asked} asked", flush=True)
    print(f"jev kind: {asked} new calls")


def place(rows: list[dict]) -> None:
    from sklearn.manifold import TSNE

    texts = [embed.Text(key=it["key"], text=it["title"], licence=it["licence"]) for it in rows]
    vecs = embed.embed(texts)
    m = np.array([vecs[it["key"]] for it in rows], dtype=np.float32)
    m /= np.linalg.norm(m, axis=1, keepdims=True)
    xy = TSNE(
        n_components=2, metric="cosine", init="pca", perplexity=30, random_state=3407
    ).fit_transform(m)
    for it, (x, y) in zip(rows, xy, strict=True):
        it["x"], it["y"] = round(float(x), 3), round(float(y), 3)


def main() -> None:
    previous = {}
    if OUT.exists():
        previous = {r["key"]: r for r in json.loads(OUT.read_text())["points"]}
    rows = items()
    check_categories(rows, previous)
    check_kinds(rows, previous)
    place(rows)
    keep = (
        "key",
        "set",
        "source",
        "title",
        "category",
        "status",
        "digest",
        "jev",
        "kind_digest",
        "jev_kind",
        "keyword_kind",
        "x",
        "y",
    )
    points = [{k: it.get(k) for k in keep} for it in rows]
    OUT.write_text(json.dumps({"points": points}, indent=1, ensure_ascii=False) + "\n")
    agree = [p for p in points if p["jev"] and p["jev"]["choice"] == p["category"]]
    differ = [p for p in points if p["jev"] and p["jev"]["choice"] != p["category"]]
    print(f"wrote {OUT.relative_to(ROOT)}: {len(points)} experiments")
    print(
        f"jev agrees on {len(agree)}, differs on {len(differ)}, not asked {sum(not p['jev'] for p in points)}"
    )


if __name__ == "__main__":
    main()
