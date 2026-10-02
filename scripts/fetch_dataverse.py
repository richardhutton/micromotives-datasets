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
CC0 1.0 for all nine UK Dataverse deposits held so far -- so the licence is
written to data/catalog/uk_dataverse_provenance.json, from the API rather than
from anyone's assertion, which is what QC rule 16 asks a recipe to record. All
19 TESS deposits state none, which is what blocks publication, so this is the
first material in the corpus that could actually be redistributed.

This script's own `candidates()` only drives four of those nine (the rows
marked NEW-confirmed in uk_dataverse_candidates.csv) -- the other five
(EFXNLX, 6MRVOM, 35M5CV, PMV0TG, ZZYSIZ) were fetched and their provenance
entries rebuilt directly against the Dataverse API, not through this CSV.
Add them as NEW-confirmed rows before relying on `--only` to re-fetch them.

As of 2026-10-02, every provenance entry also carries `description`
(`dsDescription`, HTML stripped, `None` if the deposit has none) and
`publication` (`publicationCitation` plus the article DOI, `None` if the
deposit has neither) -- see `_description`/`_publication` below. Added after
the provenance file was found to hold zero descriptions for any of the nine
deposits on disk, and after `QQM5MC`'s own `publicationCitation` was found to
name the correct journal where another source had named the wrong one
(ledger 102).

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
import re
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


_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    """Drop markup Dataverse allows inside citation text (e.g. `<i>journal</i>`).

    This removes tags only -- never rewords or re-punctuates the underlying
    text, per the typography-normalisation rule in CLAUDE.md.
    """
    return _TAG_RE.sub("", text)


def _citation_field(version: dict[str, Any], type_name: str) -> dict[str, Any] | None:
    """Look up one field by name from the dataset's `citation` metadata block."""
    fields = version["metadataBlocks"]["citation"]["fields"]
    for f in fields:
        if f["typeName"] == type_name:
            return dict(f)
    return None


def _description(version: dict[str, Any]) -> str | None:
    """Plain-text `dsDescription`, HTML stripped. `None` if the deposit has none.

    rich noticed this project held nine UK deposits and recorded zero
    descriptions -- this (and `_publication` below) is why.
    """
    field = _citation_field(version, "dsDescription")
    if not field or not field.get("value"):
        return None
    first = field["value"][0]
    value = first.get("dsDescriptionValue", {}).get("value")
    return _strip_html(value) if value else None


def _publication(version: dict[str, Any]) -> dict[str, Any] | None:
    """The deposit's own `publicationCitation` plus the article DOI, if either exists.

    This field is what caught `QQM5MC` naming the wrong journal (ledger 102) --
    the deposit's own record had the right one the whole time.
    """
    field = _citation_field(version, "publication")
    if not field or not field.get("value"):
        return None
    first = field["value"][0]
    citation = first.get("publicationCitation", {}).get("value")
    doi = first.get("publicationIDNumber", {}).get("value")
    id_type = first.get("publicationIDType", {}).get("value")
    return {
        "citation": _strip_html(citation) if citation else None,
        "doi": doi if (doi and id_type == "doi") else None,
    }


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
            "description": _description(version),
            "publication": _publication(version),
            "files": files,
        }
        print(f"{code}: {row['title'][:60]}\n  licence: {licence}\n")

    PROVENANCE.write_text(json.dumps(prov, indent=1, sort_keys=True))
    print(f"wrote {PROVENANCE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
