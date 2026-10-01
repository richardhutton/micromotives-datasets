#!/usr/bin/env python3
"""Fetch the UK Dataverse experiments, in their ORIGINAL format.

The original format is the whole point. Dataverse "ingests" an uploaded .dta or
.sav and serves a derived `.tab` by default -- and the ingest drops the value
labels. This project decodes personas, conditions and non-answers almost
entirely from value labels, so a `.tab` would mean reconstructing by hand what
the depositor already recorded, with every chance of getting it wrong.

`data/raw/QQM5MC` was fetched before this script existed and holds exactly that
mistake: `YouGovExp.tab`, where the API reports
`originalFileFormat: application/x-stata-14`. Re-running this replaces it.

Unlike every TESS deposit, these state a licence the API will tell you --
CC0 1.0 for all four -- so the licence is written to
data/catalog/uk_dataverse_provenance.json, from the API rather than from
anyone's assertion, which is what QC rule 16 asks a recipe to record. All 19 TESS deposits state none, which is what blocks publication,
so this is the first material in the corpus that could actually be redistributed.

    source ~/.bash_profile && uv run python scripts/fetch_dataverse.py
    source ~/.bash_profile && uv run python scripts/fetch_dataverse.py --only QQM5MC

Needs DATAVERSE_API_KEY (in ~/.bash_profile, which the shell here does not
source). The key is sent as a header and never written to disk or logged.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import urllib.request
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
CANDIDATES = REPO / "data" / "catalog" / "uk_dataverse_candidates.csv"
RAW = REPO / "data" / "raw"
PROVENANCE = REPO / "data" / "catalog" / "uk_dataverse_provenance.json"
BASE = "https://dataverse.harvard.edu"
# Harvard Dataverse returns 403 to the default `Python-urllib/3.x` agent while
# serving the identical request from curl. Not an auth problem -- a user-agent
# filter in front of the API.
HEADERS = {"User-Agent": "micromotives-datasets/0.1 (research data fetch)"}


def _key() -> str:
    key = os.environ.get("DATAVERSE_API_KEY")
    if not key:
        raise SystemExit(
            "DATAVERSE_API_KEY is not set. It lives in ~/.bash_profile, which is not "
            "sourced automatically — prefix the command with `source ~/.bash_profile &&`"
        )
    return key


def _get(url: str, key: str) -> Any:
    req = urllib.request.Request(url, headers={"X-Dataverse-key": key, **HEADERS})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def _download(file_id: int, dest: Path, key: str, *, original: bool) -> int:
    url = f"{BASE}/api/access/datafile/{file_id}"
    if original:
        url += "?format=original"
    req = urllib.request.Request(url, headers={"X-Dataverse-key": key, **HEADERS})
    with urllib.request.urlopen(req) as r:
        body = r.read()
    dest.write_bytes(body)
    return len(body)


def candidates(only: list[str]) -> list[dict[str, str]]:
    with open(CANDIDATES) as fh:
        rows = [r for r in csv.DictReader(fh) if r["status"] == "NEW-confirmed"]
    if only:
        rows = [r for r in rows if any(o in r["doi_or_id"] for o in only)]
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", action="append", default=[], help="Dataverse id, e.g. QQM5MC")
    args = ap.parse_args()

    key = _key()
    prov: dict[str, Any] = json.loads(PROVENANCE.read_text()) if PROVENANCE.exists() else {}

    for row in candidates(args.only):
        doi = row["doi_or_id"]
        code = doi.rsplit("/", 1)[-1]
        meta = _get(f"{BASE}/api/datasets/:persistentId/?persistentId=doi:{doi}", key)
        version = meta["data"]["latestVersion"]
        licence = (version.get("license") or {}).get("name") or version.get("termsOfUse")

        folder = RAW / code
        folder.mkdir(parents=True, exist_ok=True)
        files = []
        for f in version["files"]:
            df = f["dataFile"]
            # A file Dataverse ingested has an originalFileFormat; ask for that,
            # because the served .tab has had its value labels stripped.
            original = bool(df.get("originalFileFormat"))
            name = df.get("originalFileName") or df.get("filename") or str(df["id"])
            size = _download(df["id"], folder / name, key, original=original)
            files.append(
                {
                    "name": name,
                    "bytes": size,
                    "served_as": df.get("filename"),
                    "original_format": df.get("originalFileFormat"),
                }
            )
            flag = "  (ORIGINAL)" if original else ""
            print(f"  {name:38} {size:>10,} bytes{flag}")

        prov[code] = {
            "doi": doi,
            "title": row["title"],
            "authors": row["authors"],
            "licence": licence,
            "licence_source": "Dataverse API, latestVersion.license",
            "files": files,
        }
        print(f"{code}: {row['title'][:60]}\n  licence: {licence}\n")

    PROVENANCE.write_text(json.dumps(prov, indent=1, sort_keys=True))
    print(f"wrote {PROVENANCE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
