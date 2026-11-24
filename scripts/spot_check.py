#!/usr/bin/env python3
"""Draw a random spot-check of built conditions for a person to verify against the source.

rich (24 Nov 2026): our claim that the corpus is built correctly needs evidence an outsider
can check, so a person reads a random sample of conditions against the original
instrument and we report the error rate. Numeric crosschecks cannot see condition text
(CLAUDE.md, "Numeric verification cannot see the condition"); only reading can.

Sampling: N studies drawn uniformly at random from the built text corpus
(data/processed/*.parquet, one file per recipe), then one (condition, outcome) pair drawn
uniformly from that study's distinct pairs. The seed and the draw are written to
data/catalog/spot_check.json so the sample is fixed before anyone looks at it.

Only the instrument is read: condition, outcome and scale columns. Persona and response
values are never loaded (CLAUDE.md, Data handling: UKDS rows never enter the conversation).

For each pair the script also LOCATES candidate source passages: the condition's longest
sentences are searched for in the .txt files under the study's raw folder. That is a
convenience for the reader, not a verdict: the reader checks that the passage is the right
one for this arm and this question, which the locator cannot know.

    uv run python scripts/spot_check.py --n 30 --seed 20261124   # draw, once
    uv run python scripts/spot_check.py --page                    # render the checking page
"""

from __future__ import annotations

import argparse
import html
import json
import random
import re
import subprocess
import zipfile
from pathlib import Path

import pyarrow.parquet as pq
import yaml

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
RECIPES = ROOT / "recipes"
OUT = ROOT / "data" / "catalog" / "spot_check.json"
HTML = ROOT / "docs" / "trackers" / "spot_check.html"
TEMPLATE = ROOT / "scripts" / "spot_check_template.html"
COLS = [
    "condition",
    "outcome",
    "factors",
    "condition_num",
    "task_num",
    "scale_min",
    "scale_max",
    "study_id",
]


def norm(s: str) -> str:
    """Typography and whitespace only; words never change (CLAUDE.md conventions)."""
    return norm_map(s)[0].strip()


def raw_dir(study_id: str) -> Path | None:
    """The raw folder whose name is the longest prefix of the study id (case-insensitive)."""
    best = None
    for d in RAW.iterdir():
        fits = d.is_dir() and study_id.lower().startswith(d.name.lower())
        if fits and (best is None or len(d.name) > len(best.name)):
            best = d
    return best


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", html.unescape(s))


def source_texts(study_id: str, folder: Path | None) -> list[tuple[str, str]]:
    """(file, text) for every readable document in the study's raw folder and _converted."""
    paths: list[Path] = []
    if folder is not None:
        paths += [p for p in folder.rglob("*") if p.is_file()]
    conv = RAW / "_converted"
    if conv.is_dir():
        paths += [p for p in conv.iterdir() if p.name.lower().startswith(study_id.lower() + "__")]
    out: list[tuple[str, str]] = []
    for p in sorted(paths):
        ext = p.suffix.lower()
        try:
            if ext == ".doc":
                text = subprocess.run(
                    ["textutil", "-convert", "txt", "-stdout", str(p)],
                    capture_output=True,
                    text=True,
                    timeout=60,
                ).stdout
            elif ext in {".txt", ".rtf"}:
                text = p.read_text(errors="replace")
            elif ext == ".docx":
                with zipfile.ZipFile(p) as z:
                    xml = z.read("word/document.xml").decode("utf8", "replace")
                text = _strip_html(re.sub(r"</w:p>", "\n", xml))
            elif ext == ".qsf":
                text = _strip_html(p.read_text(errors="replace").replace("\\n", " "))
            elif ext == ".pdf":
                text = subprocess.run(
                    ["pdftotext", "-layout", str(p), "-"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                ).stdout
            else:
                continue
        except (OSError, zipfile.BadZipFile, KeyError, subprocess.SubprocessError):
            continue
        out.append((str(p.relative_to(ROOT)), text))
    return out


TYPO = {"\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-"}


def norm_map(text: str) -> tuple[str, list[int]]:
    """norm() plus, for each character of the result, its index in the original text."""
    out: list[str] = []
    idx: list[int] = []
    space = True
    for k, ch in enumerate(text):
        if ch.isspace() or ch == "\u00a0":
            if not space:
                out.append(" ")
                idx.append(k)
            space = True
            continue
        out.append(TYPO.get(ch, ch).lower()[:1] or ch)
        idx.append(k)
        space = False
    return "".join(out), idx


def excerpt(text: str, probe: str, before: int = 500, after: int = 1500) -> str:
    """The source's own words around a normalised probe, in their original case and layout."""
    flat, idx = norm_map(text)
    at = flat.find(probe)
    if at < 0:
        return ""
    s0, s1 = idx[at], idx[min(len(idx) - 1, at + len(probe) - 1)] + 1
    start = max(text.rfind("\n", 0, max(0, s0 - before)) + 1, s0 - before - 100)
    chunk = text[start : min(len(text), s1 + after)]
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", chunk)).strip()


def sentences_of(text: str) -> list[str]:
    parts = re.split(r"(?<=[.?!\"])\s+|\n+", text)
    return [s for s in parts if len(norm(s)) > 25]


def windows_of(sentence: str, others: list[str]) -> list[str]:
    """50-character windows of a varying sentence that no other version contains, so the
    passage is anchored on what sets this version apart ("and women's empowerment,
    compared to Poland") rather than on wording its siblings share. Several are kept,
    because a window that runs into a framing phrase we added will not be in the source."""
    n = norm(sentence).strip("\"' ")
    wins = [n[i : i + 50] for i in range(0, max(1, len(n) - 49), 5)]
    unique = [w for w in wins if all(w not in o for o in others)]
    mid = max(0, len(n) // 2 - 25)
    return [*unique, n[mid : mid + 50]]


def probe_of(sentence: str) -> str:
    n = norm(sentence).strip("\"' ")
    mid = max(0, len(n) // 2 - 25)
    return n[mid : mid + 50]


def study_tag(recipe: str, study_id: str) -> str:
    """The sub-study label in a recipe name, e.g. 'study6' from researchbox482_study6_satisfaction."""
    rest = recipe[len(study_id) :].strip("_").lower()
    m = re.match(r"(study|s|w|wa_b)(\d+[a-z]?)", rest)
    return (m.group(1).replace("_", "") + m.group(2)) if m else ""


def name_score(path: str, recipe: str, study_id: str) -> int:
    """Prefer files named for this sub-study; push down files named for a different one.

    +2 when the file names this sub-study's number (study6, W3, WA-B4), -2 when it names a
    different study number, and +1 for each other word of the recipe's suffix the file
    name carries as a whole word (us, india, food), -1 when it names a sibling's word.
    """
    tag = study_tag(recipe, study_id)
    words = set(re.findall(r"[a-z0-9]+", Path(path).name.lower()))
    fn = "".join(re.findall(r"[a-z0-9]+", Path(path).name.lower()))
    score = 0
    if tag:
        num = re.sub(r"^[a-z]+", "", tag)
        if tag in fn or f"study{num}" in fn:
            score += 2
        else:
            other = re.findall(r"study(\d+[a-z]?)", fn)
            if other and num not in other:
                score -= 2
    rest = recipe[len(study_id) :].strip("_").lower().split("_")
    extra = [w for w in rest if w and w != tag and not re.fullmatch(r"(study|s|w)\d+[a-z]?", w)]
    score += sum(1 for w in extra if w in words)
    return score


def locate(
    condition: str, others: list[str], outcome: str, study_id: str, recipe: str, folder: Path | None
) -> list[dict[str, object]]:
    """Find this version's own wording in the source documents.

    The probes come first from the sentences that are SPECIFIC to this version (absent from
    every other condition in the recipe), so the passage shown is the one that tells the
    versions apart rather than the shared opening every version repeats. Files named for
    this sub-study are preferred and files named for a different one pushed down.
    """
    if not condition.strip():
        return []
    other_flats = [norm(o) for o in others]
    sents = sorted(set(sentences_of(condition)), key=len, reverse=True)
    # A sentence VARIES if at least one other version lacks it: in a 2x2 every varying
    # sentence is shared with some other cell, so "absent from all others" finds nothing.
    own = [s for s in sents if any(norm(s).strip("\"' ") not in f for f in other_flats)]
    shared = [s for s in sents if s not in own]
    own_w = [windows_of(s, other_flats) for s in own[:4]]
    shared_p = [probe_of(s) for s in shared[:2]]
    out_p = [probe_of(s) for s in sorted(sentences_of(outcome), key=len, reverse=True)[:1]]
    hits: list[dict[str, object]] = []
    for name, text in source_texts(study_id, folder):
        flat = norm(text)
        o = [next(w for w in ws if w in flat) for ws in own_w if any(w in flat for w in ws)]
        sh = [pr for pr in shared_p if pr and pr in flat]
        if not (o or sh):
            continue
        key = o[0] if o else sh[0]
        hit: dict[str, object] = {
            "file": name,
            "matched": (
                f"{len(o)} of {len(own_w)} version-specific sentences, "
                f"{len(sh)} of {len(shared_p)} shared"
            ),
            "excerpt": excerpt(text, key),
            "_rank": (name_score(name, recipe, study_id), len(o), len(sh)),
        }
        if o and sh:
            ctx = excerpt(text, sh[0], 200, 600)
            if ctx and ctx[:200] not in str(hit["excerpt"]):
                hit["context"] = ctx
        q = [pr for pr in out_p if pr and pr in flat]
        if q:
            qx = excerpt(text, q[0], 200, 500)
            if qx and qx[:200] not in str(hit["excerpt"]):
                hit["question"] = qx
        hits.append(hit)
    hits.sort(key=lambda h: h["_rank"], reverse=True)  # type: ignore[arg-type,return-value]
    for h in hits:
        del h["_rank"]
    return hits[:3]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--page", action="store_true", help="render the page from the drawn sample")
    args = ap.parse_args()
    if args.page:
        payload = OUT.read_text().replace("</", "<\\/")
        HTML.write_text(TEMPLATE.read_text().replace("__DATA__", payload))
        print(f"wrote {HTML.relative_to(ROOT)}")
        return
    if args.seed is None:
        raise SystemExit("--seed is required to draw a sample")
    if OUT.exists():
        raise SystemExit(f"{OUT.relative_to(ROOT)} exists: the sample is fixed once drawn")

    recipes = {p.stem for p in RECIPES.glob("*.yaml")}
    files = sorted(p for p in PROCESSED.glob("*.parquet") if p.stem in recipes)
    rng = random.Random(args.seed)
    chosen = rng.sample(files, args.n)

    items = []
    for k, path in enumerate(chosen, 1):
        t = pq.read_table(path, columns=COLS).to_pylist()
        pairs = sorted({(r["condition_num"], r["task_num"]) for r in t})
        cnum, tnum = rng.choice(pairs)
        row = next(r for r in t if r["condition_num"] == cnum and r["task_num"] == tnum)
        others = sorted({r["condition"] for r in t if r["condition_num"] != cnum})
        recipe = yaml.safe_load((RECIPES / f"{path.stem}.yaml").read_text())
        folder = raw_dir(row["study_id"])
        items.append(
            {
                "n": k,
                "recipe": path.stem,
                "study_id": row["study_id"],
                "title": recipe.get("title", ""),
                "source": recipe.get("source", ""),
                "condition_num": cnum,
                "task_num": tnum,
                "factors": row["factors"],
                "condition": row["condition"],
                "outcome": row["outcome"],
                "scale": [row["scale_min"], row["scale_max"]],
                "raw_folder": str(folder.relative_to(ROOT)) if folder else None,
                "located": locate(
                    row["condition"], others, row["outcome"], row["study_id"], path.stem, folder
                ),
                "verdict": None,
                "note": "",
            }
        )
    about = (
        f"Random spot-check drawn 2026-11-24, seed {args.seed}: {args.n} of {len(files)} built "
        "text recipes chosen uniformly, one (condition, outcome) pair each. A person reads each "
        "against the original instrument. verdict: correct | wrong | cannot check."
    )
    OUT.write_text(
        json.dumps({"_about": about, "items": items}, indent=1, ensure_ascii=False) + "\n"
    )
    found = sum(1 for i in items if i["located"])
    print(f"wrote {OUT.relative_to(ROOT)}: {len(items)} items, source passage located for {found}")


if __name__ == "__main__":
    main()
