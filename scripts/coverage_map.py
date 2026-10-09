"""Where every source in the catalogue sits in topic space, and which parts we have built.

The companion to `coverage_table.py`. That one answers the gap question exactly,
using the catalogue's own six-way category — no model, no projection, no seed.
This one earns its place where the category runs out: six buckets cannot show
that two "moral/social/cognition" studies are about completely different things,
and the holes worth seeing are finer than a bucket.

**UMAP, not t-SNE, and the reason is the word "updating".** t-SNE cannot place a
new point into an existing layout — add a study next week and the whole embedding
re-runs, every dot moves, and this week's picture cannot be compared to last
week's. UMAP fits once and `transform()`s new points into the frozen space. So
the fit is SAVED, and a later study lands in the map the earlier ones defined
rather than rearranging them.

**Titles only, deliberately.** The built corpus holds far richer text — condition
wording, shared context, the outcome question — but the catalogue holds a bare
title, and embedding 900 characters of stimulus prose alongside a 70-character
academic title separates them on LENGTH and REGISTER before topic signal gets a
look in. That artefact looks exactly like real structure. One register per map.
A design-text map of the built corpus is a different map, and will be one.

Titles are public metadata — they sit on tessexperiments.org and on Dataverse
records — so this map is licence-safe for every source, which the design-text
version is not (see `CLEARED` in `embed.py`).
"""

from __future__ import annotations

import argparse
import csv
import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from micromotives_datasets import embed

ROOT = Path(__file__).resolve().parent.parent
CATALOGUE = ROOT / "data" / "catalog" / "tess_uk_foundation_sources.csv"
UK_PROVENANCE = ROOT / "data" / "catalog" / "uk_dataverse_provenance.json"
IP_CATALOGUE = ROOT / "data" / "catalog" / "innovation_panel_experiments.json"
RECIPES = ROOT / "recipes"
COORDS = ROOT / "data" / "catalog" / "coverage_map.json"
FIT = ROOT / "data" / "catalog" / "coverage_map_umap.pkl"

SEED = 20261002


def built_study_ids() -> set[str]:
    return {str(yaml.safe_load(p.read_text())["study_id"]) for p in RECIPES.glob("*.yaml")}


def sources() -> list[dict[str, Any]]:
    """Every source worth a dot, with the title that will be embedded."""
    built = built_study_ids()
    out: list[dict[str, Any]] = []

    with CATALOGUE.open(newline="") as handle:
        for row in csv.DictReader(handle):
            code = row["osf_code"]
            out.append(
                {
                    "code": code,
                    "title": row["title"],
                    "category": row.get("category") or "(uncategorised)",
                    "year": row.get("year") or "",
                    "origin": "US (TESS)",
                    "built": code in built,
                }
            )

    if UK_PROVENANCE.exists():
        for code, meta in json.loads(UK_PROVENANCE.read_text()).items():
            out.append(
                {
                    "code": code,
                    "title": meta["title"],
                    "category": "UK Dataverse",
                    "year": "",
                    "origin": "UK (Dataverse)",
                    "built": code in built,
                }
            )

    # The Innovation Panel's 93 experiments. Their titles come from the User
    # Guide, which UKDS publish themselves at doc.ukdataservice.ac.uk with no
    # authentication (verified 9 Oct 2026) -- see `ukds-public-documentation` in
    # embed.py for the check and who decided. The MICRODATA remains refused; this
    # is the guide's own description of what each experiment was.
    if IP_CATALOGUE.exists():
        catalogue = json.loads(IP_CATALOGUE.read_text())
        experiments = catalogue["experiments"] if isinstance(catalogue, dict) else catalogue
        for row in experiments:
            if row["verdict"] != "build":
                continue
            out.append(
                {
                    "code": f"IP{row['id']}",
                    "title": row["title"],
                    "category": f"IP {row['category']}",
                    "year": "",
                    "origin": "UK (Innovation Panel)",
                    # 9.10 is the only one built; its recipes carry study_id
                    # ukds_6849, which is shared, so the id has to be checked
                    # against the experiment rather than the study.
                    "built": row["id"] == "9.10",
                    "licence": "ukds-public-documentation",
                }
            )

    return out


def place(rows: list[dict[str, Any]], *, refit: bool) -> tuple[list[dict[str, Any]], str]:
    """Attach (x, y) to each row, fitting UMAP once and reusing it forever after.

    A refit moves every existing dot, so it is opt-in and loud. The normal path
    loads the saved fit and transforms, which is what keeps the map comparable
    across weeks.
    """
    import umap

    # Titles are public metadata: public listing pages carry them, so they are
    # cleared for the wire. Anything FROM a study — condition text, outcome
    # wording — is a different question and is not cleared.
    items = [
        embed.Text(key=r["code"], text=r["title"], licence=r.get("licence", "public-metadata"))
        for r in rows
    ]
    vectors = embed.embed(items)
    matrix = np.array([vectors[r["code"]] for r in rows], dtype=np.float32)

    if FIT.exists() and not refit:
        with FIT.open("rb") as handle:
            reducer = pickle.load(handle)
        coords = reducer.transform(matrix)
        how = "reused the saved fit — existing dots did not move"
    else:
        how = "FIT the map" if not FIT.exists() else "RE-FIT — every dot moved"
        reducer = umap.UMAP(
            n_components=2,
            n_neighbors=15,
            min_dist=0.1,
            metric="cosine",
            random_state=SEED,
        )
        coords = reducer.fit_transform(matrix)
        with FIT.open("wb") as handle:
            pickle.dump(reducer, handle)

    for row, (x, y) in zip(rows, coords, strict=True):
        row["x"], row["y"] = round(float(x), 4), round(float(y), 4)
    return rows, how


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refit",
        action="store_true",
        help="re-fit UMAP from scratch. MOVES EVERY EXISTING DOT, so the new map "
        "cannot be compared to the old one. Only when the corpus has changed "
        "enough that the old layout no longer describes it.",
    )
    args = parser.parse_args()

    rows, how = place(sources(), refit=args.refit)
    COORDS.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")

    built = sum(1 for r in rows if r["built"])
    uk = sum(1 for r in rows if r["origin"].startswith("UK"))
    print(f"{len(rows)} sources placed — {built} built, {uk} UK")
    print(f"wrote {COORDS.relative_to(ROOT)}")
    print(f"{how} ({FIT.relative_to(ROOT)})")


if __name__ == "__main__":
    main()
