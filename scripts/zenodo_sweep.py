#!/usr/bin/env python3
"""Sweep Zenodo for survey experiments we have not yet looked at, and screen them with Jev.

rich (16 Nov 2026), after the first MaxDiff and paired-choice sources came from
Zenodo: run the new Zenodo finds through the Jev classifier to see what suits the
dataset, rather than picking by eye. This is `dataverse_sweep.py` for Zenodo, with
the same division of labour (CLAUDE.md):

  * code judges mechanics: licence id from the API, is there a data file, is there
    a file whose NAME says questionnaire/codebook/appendix, UK words in the text;
  * Jev judges meaning, from the record's own public metadata (title, description,
    keywords, file NAMES; never a file's contents): was the sample in the UK, is
    this a randomised experiment and of what kind (`jev.screen_deposit`), and which
    of our eight categories it belongs to (`jev.categorise_experiment`).

Nothing is auto-accepted. The report ranks a reading queue, flags low-confidence
verdicts REVIEW, and lists where Jev and the UK keyword heuristic disagree.

    uv run python scripts/zenodo_sweep.py harvest
    source ~/.bash_profile && uv run python scripts/zenodo_sweep.py screen

Output: data/catalog/zenodo_sweep.json (record metadata only; tracked).
"""

from __future__ import annotations

import argparse
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
OUT = REPO / "data" / "catalog" / "zenodo_sweep.json"
LIST = REPO / "data" / "catalog" / "experiment_list.json"
MANIFEST = REPO / "data" / "catalog" / "experiment_manifest.json"
API = "https://zenodo.org/api/records"
HEADERS = {"User-Agent": "micromotives-datasets/0.1 (research data fetch)"}
# jev.REVIEW_BELOW, restated so `report` runs without the SDK installed.
REVIEW_BELOW = 0.85
# Zenodo answers 429 to bursts; anonymous page size is capped at 25.
PAUSE = 2.0
PAGES = 3

QUERIES = [
    '"best-worst"',
    '"best worst"',
    'maxdiff OR "max-diff"',
    '"discrete choice experiment"',
    '"choice experiment"',
    "conjoint",
    '"paired comparison"',
    '"stated preference"',
    '"survey experiment"',
    '"vignette experiment" OR "factorial survey"',
    '"framing experiment"',
    '"list experiment"',
]

OPEN_LICENCES = ("cc-by-4", "cc-by-3", "cc-by-sa", "cc-zero", "cc0", "odc-by")
DATA_EXT = re.compile(r"\.(dta|sav|por|csv|tab|rds|rdata|xlsx?|parquet|feather|zip)$", re.I)
INSTRUMENT_NAME = re.compile(
    r"questionnaire|survey|codebook|instrument|appendix|supplement|wording|qualtrics|\.qsf$|vignette|design",
    re.I,
)
# The heuristic Jev is checked against. Words, never punctuation (CLAUDE.md).
UK_WORDS = re.compile(
    r"\b(UK|U\.K\.|United Kingdom|Britain|British|England|English|Scotland|Scottish|Wales|Welsh|"
    r"Brexit|Westminster|NHS)\b"
)


def _get(url: str) -> Any:
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as exc:
            if exc.code != 429:
                raise
            time.sleep(30 * (attempt + 1))
    raise RuntimeError(f"still rate-limited after 5 tries: {url}")


def _strip(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def _known() -> set[str]:
    """Zenodo record ids already on the experiment list or in a recipe name."""
    ids = {r["id"] for r in json.loads(LIST.read_text())["rows"] if r["source"] == "Zenodo"}
    ids |= {
        p.stem.removeprefix("zenodo").split("_")[0] for p in REPO.glob("recipes/**/zenodo*.yaml")
    }
    return ids


def harvest() -> None:
    known = _known()
    queries: dict[str, int] = {}
    found: dict[str, dict[str, Any]] = {}
    for q in QUERIES:
        total = 0
        for page in range(1, PAGES + 1):
            url = f"{API}?" + urllib.parse.urlencode(
                {"q": q, "type": "dataset", "size": 25, "page": page}
            )
            d = _get(url)
            total = d.get("hits", {}).get("total", total)
            for h in d.get("hits", {}).get("hits", []):
                m = h["metadata"]
                if m.get("resource_type", {}).get("type") != "dataset":
                    continue
                e = found.setdefault(
                    str(h["id"]),
                    {
                        "id": str(h["id"]),
                        "url": f"https://zenodo.org/records/{h['id']}",
                        "title": m.get("title") or "",
                        "description": _strip(m.get("description") or "")[:3000],
                        "keywords": m.get("keywords") or [],
                        "published": m.get("publication_date") or "",
                        "licence": (m.get("license") or {}).get("id") or "",
                        "files": [f["key"] for f in h.get("files", [])],
                        "related": [
                            r.get("identifier")
                            for r in m.get("related_identifiers", [])
                            if r.get("relation") in ("isSupplementTo", "isDescribedBy", "cites")
                        ][:5],
                        "matched": [],
                    },
                )
                e["matched"].append(q)
            time.sleep(PAUSE)
        queries[q] = total
        print(f"{total:6}  {q}")
    new = {k: e for k, e in found.items() if k not in known}
    for e in new.values():
        e["open_licence"] = e["licence"].startswith(OPEN_LICENCES)
        e["has_data"] = any(DATA_EXT.search(f) for f in e["files"])
        e["instrument_files"] = [f for f in e["files"] if INSTRUMENT_NAME.search(f)]
        text = " ".join([e["title"], e["description"], *e["keywords"]])
        e["uk_words"] = sorted(set(UK_WORDS.findall(text)))
    previous: dict[str, Any] = {}
    if OUT.exists():
        previous = json.loads(OUT.read_text())["records"]
    for k, e in new.items():
        for key in ("screen", "category"):
            if key in previous.get(k, {}) and previous[k].get("title") == e["title"]:
                e[key] = previous[k][key]
    OUT.write_text(
        json.dumps(
            {
                "_about": __doc__.strip().splitlines()[0],
                "swept": time.strftime("%Y-%m-%d"),
                "grain": f"record (Zenodo API, type=dataset, first {PAGES * 25} per query)",
                "queries": queries,
                "distinct_hits": len(found),
                "already_listed": len(found) - len(new),
                "records": dict(sorted(new.items())),
            },
            indent=1,
            ensure_ascii=False,
        )
        + "\n"
    )
    n_open = sum(e["open_licence"] for e in new.values())
    print(f"\n{len(found)} distinct records, {len(new)} new, {n_open} with an open licence")
    print(f"wrote {OUT.relative_to(REPO)}")


def screen() -> None:
    from micromotives_datasets import jev

    sweep = json.loads(OUT.read_text())
    vocab = {
        k: v
        for k, v in json.loads(MANIFEST.read_text())["_category_vocabulary"].items()
        if not k.startswith("_")
    }
    cli = jev.client("zenodo")
    todo = [
        r
        for r in sweep["records"].values()
        if r["open_licence"] and r["has_data"] and "screen" not in r
    ]
    print(f"screening {len(todo)} open-licence records with data")
    for i, r in enumerate(todo, 1):
        reading = jev.screen_deposit(
            cli,
            title=r["title"],
            description=r["description"],
            keywords=", ".join(k for k in r["keywords"] if k),
            geography="",
            publication="; ".join(x for x in r["related"] if x),
            files=", ".join(r["files"][:40]),
        )
        r["screen"] = {
            k: {
                "value": v.value,
                "confidence": round(v.confidence, 3),
                "runners_up": [[a, round(b, 3)] for a, b in v.runners_up],
            }
            for k, v in (("uk_sample", reading.uk_sample), ("design", reading.design))
        }
        c = jev.categorise_experiment(
            cli, r["title"], r["description"][:1500], tuple(vocab), tuple(vocab.values())
        )
        r["category"] = {
            "value": c.value,
            "confidence": round(c.confidence, 3),
            "runner_up": c.runners_up[0][0] if c.runners_up else None,
        }
        if i % 20 == 0:
            print(f"  screened {i}/{len(todo)}", flush=True)
            OUT.write_text(json.dumps(sweep, indent=1, ensure_ascii=False) + "\n")
    OUT.write_text(json.dumps(sweep, indent=1, ensure_ascii=False) + "\n")
    report(sweep)


def report(sweep: dict[str, Any]) -> None:
    recs = sweep["records"]
    exp = {"survey_experiment", "conjoint", "list_experiment"}
    shown = [r for r in recs.values() if r.get("screen")]
    print(f"\n{len(shown)} screened")
    groups: dict[str, list[dict[str, Any]]] = {"uk": [], "uk_among": [], "other": []}
    disagree = []
    for r in shown:
        s = r["screen"]
        is_uk = s["uk_sample"]["value"] in ("uk_only", "uk_among_others")
        if is_uk != bool(r["uk_words"]):
            disagree.append(r)
        if s["design"]["value"] not in exp:
            continue
        key = {"uk_only": "uk", "uk_among_others": "uk_among"}.get(s["uk_sample"]["value"], "other")
        groups[key].append(r)
    for key, title in (
        ("uk", "UK sample, randomised survey design"),
        ("uk_among", "multi-country including the UK, randomised survey design"),
        ("other", "not UK (or cannot tell), randomised survey design"),
    ):
        print(f"\n{title}: {len(groups[key])}")
        for r in sorted(groups[key], key=lambda r: r["screen"]["design"]["value"] != "conjoint"):
            s = r["screen"]
            low = min(s["uk_sample"]["confidence"], s["design"]["confidence"]) < REVIEW_BELOW
            print(
                f"  {'REVIEW' if low else 'ok    '} {r['id']:>9} {s['uk_sample']['value']:16} "
                f"{s['design']['value']:18} {r['category']['value'][:22]:22} "
                f"instr={len(r['instrument_files'])} | {r['title'][:70]}"
            )
    print(f"\nJev and the UK keyword heuristic disagree on {len(disagree)}:")
    for r in disagree:
        print(
            f"  {r['id']:>9} jev={r['screen']['uk_sample']['value']:16} words={r['uk_words']} | {r['title'][:70]}"
        )


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
