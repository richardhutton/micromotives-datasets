#!/usr/bin/env python3
"""Sweep Harvard Dataverse for UK survey experiments we have not yet looked at.

The earlier harvest searched by author and then declared the pool "~tapped"
without saying what had been searched or at what grain (SocSci-UK_MASTER §5e,
corrected 2026-10-05). This script exists so the next claim of that kind can be
checked: every query and its hit count is written to the output next to the
results, and the grain is the DATASET, never the author.

Two stages, run separately because only the second costs money:

    uv run python scripts/dataverse_sweep.py harvest
    source ~/.bash_profile && uv run python scripts/dataverse_sweep.py screen

`harvest` runs QUERIES against the public search API, drops deposits already in
the catalogue, and fetches each remaining deposit's metadata: title, description,
keywords, geographic coverage, licence, publication and file list. No key needed.

`screen` splits the work the way CLAUDE.md does:
  * code judges mechanics — is there a data file, is there a file whose NAME says
    questionnaire/codebook/appendix, what licence does the API report;
  * Jev judges meaning — was the sample in the UK, and is this a randomised
    experiment. Both are read from the deposit's own description, which is
    instrument-level metadata, never respondent rows.

Nothing is auto-accepted. The output ranks a queue for a person to read, flags
every low-confidence verdict REVIEW, and lists every deposit where Jev and the
plain keyword heuristic DISAGREE about UK-ness, because that disagreement is the
only reason to pay for a judgement.

Output: data/catalog/dataverse_sweep.json (study metadata only; tracked).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "catalog" / "dataverse_sweep.json"
CANDIDATES = REPO / "data" / "catalog" / "uk_dataverse_candidates.csv"
PROVENANCE = REPO / "data" / "catalog" / "uk_dataverse_provenance.json"
BASE = "https://dataverse.harvard.edu"
# jev.REVIEW_BELOW, restated so `report` runs without the SDK installed.
REVIEW_BELOW = 0.85
HEADERS = {"User-Agent": "micromotives-datasets/0.1 (research data fetch)"}

UK_TERMS = '(Britain OR British OR "United Kingdom" OR UK OR England OR Scotland OR Wales)'
DESIGN_TERMS = [
    '"survey experiment"',
    "conjoint",
    "vignette",
    '"list experiment"',
    '"split ballot"',
    '"framing experiment"',
    '"randomized experiment"',
    '"randomised experiment"',
    '"factorial survey"',
    "YouGov",
    "Prolific",
]
QUERIES = [f"{d} AND {UK_TERMS}" for d in DESIGN_TERMS]

# DEL was harvested separately on 2026-10-10 (data/raw/del/); its collection
# aliases are excluded here so the sweep reports only what is new.
SKIP_COLLECTIONS = {"sandboxDEL", "panelsDEL", "trackersDEL", "devengagement"}

DATA_EXT = re.compile(r"\.(dta|sav|por|csv|tab|rds|rdata|xlsx?|parquet|feather)$", re.I)
INSTRUMENT_NAME = re.compile(
    r"questionnaire|survey|codebook|instrument|appendix|supplement|wording|qualtrics|\.qsf$|vignette",
    re.I,
)
# The heuristic Jev is checked against. Words, never punctuation (CLAUDE.md).
UK_WORDS = re.compile(
    r"\b(UK|U\.K\.|United Kingdom|Britain|British|England|English|Scotland|Scottish|Wales|Welsh|"
    r"Brexit|Westminster|NHS)\b"
)


class BlockedError(RuntimeError):
    """Harvard refused us outright. Stop: retrying a refusal is what earns one."""


# Seconds between requests. The first sweep (2026-10-10) ran eight at once and
# retried every failure; Harvard answered with a blanket 403 for this machine.
PAUSE = 1.5


def _get(url: str) -> Any:
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(3):
        time.sleep(PAUSE)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as exc:
            # A 4xx is an answer, not a hiccup. Never retry it.
            raise exc
        except Exception:  # network trouble only: retried, then re-raised
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))
    raise AssertionError("unreachable")


def _known_dois() -> set[str]:
    known: set[str] = set()
    with CANDIDATES.open() as f:
        for row in csv.DictReader(f):
            known.add(row["doi_or_id"].strip().lower().removeprefix("doi:"))
    for key, entry in json.loads(PROVENANCE.read_text()).items():
        known.add(str(entry.get("doi") or f"10.7910/DVN/{key}").lower())
    return known


def _search(query: str) -> tuple[int, list[dict[str, Any]]]:
    items: list[dict[str, Any]] = []
    start, total = 0, None
    while total is None or start < total:
        q = urllib.parse.quote(query)
        data = _get(f"{BASE}/api/search?q={q}&type=dataset&per_page=100&start={start}")["data"]
        total = int(data["total_count"])
        items.extend(data["items"])
        start += 100
        if not data["items"]:
            break
    return total, items


def _field(version: dict[str, Any], name: str) -> Any:
    for block in version.get("metadataBlocks", {}).values():
        for f in block.get("fields", []):
            if f["typeName"] == name:
                return f["value"]
    return None


def _strip(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def _metadata(global_id: str) -> dict[str, Any]:
    pid = urllib.parse.quote(global_id)
    v = _get(f"{BASE}/api/datasets/:persistentId/?persistentId={pid}")["data"]["latestVersion"]
    desc = _field(v, "dsDescription") or []
    kw = _field(v, "keyword") or []
    geo = _field(v, "geographicCoverage") or []
    pub = _field(v, "publication") or []
    files = [f["dataFile"]["filename"] for f in v.get("files", [])]
    return {
        "title": _field(v, "title"),
        "description": _strip(
            " ".join(d.get("dsDescriptionValue", {}).get("value", "") for d in desc)
        ),
        "keywords": [k.get("keywordValue", {}).get("value") for k in kw if k.get("keywordValue")],
        "geography": [
            ", ".join(str(x.get("value")) for x in g.values() if isinstance(x, dict)) for g in geo
        ],
        "licence": (v.get("license") or {}).get("name"),
        "terms_of_use": _strip(v.get("termsOfUse") or "")[:300] or None,
        "publication": _strip(pub[0].get("publicationCitation", {}).get("value", ""))
        if pub
        else None,
        "files": files,
    }


def harvest() -> None:
    known = _known_dois()
    queries: dict[str, int] = {}
    found: dict[str, dict[str, Any]] = {}
    for query in QUERIES:
        total, items = _search(query)
        queries[query] = total
        print(f"{total:5}  {query}")
        for it in items:
            gid = it["global_id"]
            if it.get("identifier_of_dataverse") in SKIP_COLLECTIONS:
                continue
            # The search result already carries title, description and keywords.
            # Kept, because Harvard's search also lists deposits HARVESTED from
            # other archives (heiDATA, Odum, Borealis ...) whose full record can
            # only be read at home — fetching them here returns 401/403.
            entry = found.setdefault(
                gid,
                {
                    "doi": gid,
                    "collection": it.get("identifier_of_dataverse"),
                    "hosted_at_harvard": gid.startswith("doi:10.7910/"),
                    "url": it.get("url"),
                    "title": it.get("name"),
                    "description": _strip(it.get("description") or ""),
                    "keywords": it.get("keywords") or [],
                    "published": (it.get("published_at") or "")[:10],
                    "matched": [],
                },
            )
            entry["matched"].append(query.split(" AND ")[0])
    new = {g: e for g, e in found.items() if g.lower().removeprefix("doi:") not in known}
    print(
        f"\n{len(found)} distinct deposits, {len(found) - len(new)} already catalogued, {len(new)} new"
    )
    # Full records (licence, files, geography) only for Harvard-hosted deposits,
    # one at a time, resuming from a previous run's file so a block costs nothing.
    done: dict[str, Any] = {}
    if OUT.exists():
        done = {g: d for g, d in json.loads(OUT.read_text())["deposits"].items() if "files" in d}
    todo = [g for g in sorted(new) if new[g]["hosted_at_harvard"]]
    for i, gid in enumerate(todo, 1):
        if gid in done:
            new[gid].update({k: done[gid][k] for k in done[gid] if k not in ("matched",)})
            continue
        try:
            new[gid].update(_metadata(gid))
        except urllib.error.HTTPError as exc:
            new[gid]["error"] = f"HTTP {exc.code}"
            if exc.code == 403 and sum(new[g].get("error") == "HTTP 403" for g in todo[:i]) >= 3:
                raise BlockedError(
                    "three 403s from Harvard-hosted deposits: blocked, stop and wait"
                ) from exc
        if i % 25 == 0:
            print(f"  metadata {i}/{len(todo)}")
    for entry in new.values():
        files = entry.get("files", [])
        entry["has_data"] = any(DATA_EXT.search(f) for f in files)
        # Replication packages often ship everything in one zip; its contents
        # are unknown until opened, so flag it rather than call it "no data".
        entry["has_zip"] = any(f.lower().endswith(".zip") for f in files)
        entry["instrument_files"] = [f for f in files if INSTRUMENT_NAME.search(f)]
        text = " ".join(
            [entry.get("title") or "", entry.get("description") or "", *entry.get("keywords", [])]
        )
        entry["uk_words"] = sorted(set(UK_WORDS.findall(text)))
    OUT.write_text(
        json.dumps(
            {
                "_about": __doc__.strip().splitlines()[0],
                "swept": time.strftime("%Y-%m-%d"),
                "grain": "dataset (Harvard Dataverse search API, type=dataset)",
                "queries": queries,
                "distinct_hits": len(found),
                "already_catalogued": len(found) - len(new),
                "deposits": dict(sorted(new.items())),
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    print(f"wrote {OUT.relative_to(REPO)}")


def screen() -> None:
    # The question itself lives in jev.screen_deposit (tests/test_architecture.py
    # holds every prompt to one file).
    from micromotives_datasets import jev

    sweep = json.loads(OUT.read_text())
    cli = jev.client("dataverse")
    deposits = sweep["deposits"]
    for i, d in enumerate(deposits.values(), 1):
        # Harvested deposits have no full record, but the search gave title and
        # description, which is what the screen reads.
        if "screen" in d or not d.get("title"):
            continue
        reading = jev.screen_deposit(
            cli,
            title=d["title"],
            description=d.get("description") or "",
            keywords=", ".join(k for k in d.get("keywords", []) if k),
            geography="; ".join(d.get("geography", [])),
            publication=d.get("publication") or "",
            files=", ".join(d.get("files", [])[:40]),
        )
        d["screen"] = {
            k: {
                "value": v.value,
                "confidence": round(v.confidence, 3),
                "runners_up": [[a, round(b, 3)] for a, b in v.runners_up],
            }
            for k, v in (("uk_sample", reading.uk_sample), ("design", reading.design))
        }
        if i % 20 == 0:
            print(f"  screened {i}/{len(deposits)}")
            OUT.write_text(json.dumps(sweep, indent=2, ensure_ascii=False) + "\n")
    OUT.write_text(json.dumps(sweep, indent=2, ensure_ascii=False) + "\n")
    report(sweep)


def report(sweep: dict[str, Any]) -> None:
    deps = sweep["deposits"]
    exp = {"survey_experiment", "conjoint", "list_experiment"}
    queue, disagree, review = [], [], []
    for gid, d in deps.items():
        s = d.get("screen")
        if not s:
            continue
        uk, design = s["uk_sample"], s["design"]
        is_uk = uk["value"] in ("uk_only", "uk_among_others")
        if is_uk != bool(d.get("uk_words")):
            disagree.append((gid, d, uk["value"], d.get("uk_words")))
        if min(uk["confidence"], design["confidence"]) < REVIEW_BELOW:
            review.append(gid)
        if is_uk and design["value"] in exp:
            queue.append((gid, d))
    print(f"\nqueue (UK sample + survey/conjoint/list experiment): {len(queue)}")

    # Conjoints first: most signal per UK respondent and the axis SocSci210 transfers
    # on best (SocSci-UK_MASTER §5d, "Why the UK layer leans conjoint").
    def rank(item: tuple[str, dict[str, Any]]) -> tuple[bool, bool, bool]:
        d = item[1]
        return (
            d["screen"]["design"]["value"] != "conjoint",
            not d["has_data"],
            not d["instrument_files"],
        )

    for gid, d in sorted(queue, key=rank):
        s = d["screen"]
        flag = "REVIEW" if gid in review else "ok    "
        print(
            f"  {flag} {gid:32} {s['uk_sample']['value']:16} {s['design']['value']:18} "
            f"data={'y' if d['has_data'] else ('zip' if d.get('has_zip') else 'n')} instr={len(d['instrument_files'])} "
            f"lic={d.get('licence')} | {(d.get('title') or '')[:70]}"
        )
    print(f"\nJev and the UK keyword heuristic disagree on {len(disagree)}:")
    for gid, d, v, w in disagree:
        print(f"  {gid:32} jev={v:16} words={w} | {(d.get('title') or '')[:70]}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("stage", choices=["harvest", "screen", "report"])
    a = ap.parse_args()
    if a.stage == "harvest":
        harvest()
    elif a.stage == "screen":
        screen()
    else:
        report(json.loads(OUT.read_text()))


if __name__ == "__main__":
    main()
