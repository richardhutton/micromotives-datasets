"""Fetch a study's raw deposit from OSF.

TESS deposits are not uniform: files may sit at the node root, inside folders,
or in a child component (often named "Data and Materials"), and the payload is
sometimes a zip and sometimes the data file itself. This walks all of that and
pulls down whatever looks like data or documentation.

Questionnaires are usually legacy `.doc`, which no Python library reads well.
On macOS we shell out to `textutil`; elsewhere we try `antiword`/LibreOffice and
otherwise leave the binary in place for a human. The converted text is what the
recipe author reads to write the arm wordings.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

API = "https://api.osf.io/v2"
UA = {"User-Agent": "micromotives-datasets/0.1"}

DATA_SUFFIXES = {".sav", ".dta", ".por", ".csv", ".tab", ".zip", ".xlsx"}
DOC_SUFFIXES = {".doc", ".docx", ".pdf", ".txt", ".rtf"}


@dataclass
class OSFFile:
    name: str
    size: int
    download: str


@dataclass
class FetchResult:
    study_id: str
    dest: Path
    data_files: list[Path] = field(default_factory=list)
    doc_files: list[Path] = field(default_factory=list)
    converted: list[Path] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [f"FETCH — {self.study_id} -> {self.dest}"]
        for p in self.data_files:
            lines.append(f"  data  {p.name}  ({p.stat().st_size:,} bytes)")
        for p in self.doc_files:
            lines.append(f"  doc   {p.name}")
        for p in self.converted:
            lines.append(f"  text  {p.name}   <- readable questionnaire")
        for n in self.notes:
            lines.append(f"  note  {n}")
        return "\n".join(lines)


def _get(url: str, timeout: int = 40) -> dict[str, Any]:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data: dict[str, Any] = json.load(r)
        return data


def _walk(url: str, acc: list[OSFFile], budget: list[int], pause: float = 0.4) -> None:
    """Depth-first walk of an osfstorage listing, following folders."""
    if budget[0] <= 0:
        return
    budget[0] -= 1
    try:
        payload = _get(url)
    except Exception:  # a missing or non-public subtree is not fatal
        return
    for entry in payload.get("data", []):
        attrs = entry["attributes"]
        if attrs.get("kind") == "folder":
            time.sleep(pause)
            _walk(entry["relationships"]["files"]["links"]["related"]["href"], acc, budget, pause)
        else:
            acc.append(
                OSFFile(
                    name=attrs.get("name", ""),
                    size=int(attrs.get("size") or 0),
                    download=entry["links"].get("download", ""),
                )
            )


def list_files(osf_code: str, max_requests: int = 60) -> list[OSFFile]:
    """Every file on a node, including its child components."""
    guid = _get(f"{API}/guids/{osf_code}/")
    node_id = guid["data"]["id"]
    base = "registrations" if guid["data"]["type"] == "registrations" else "nodes"

    found: list[OSFFile] = []
    budget = [max_requests]
    _walk(f"{API}/{base}/{node_id}/files/osfstorage/", found, budget)
    try:
        children = _get(f"{API}/{base}/{node_id}/children/")
        for child in children.get("data", []):
            time.sleep(0.5)
            _walk(f"{API}/{base}/{child['id']}/files/osfstorage/", found, budget)
    except Exception:  # no child components is normal
        pass
    return found


def _download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=180) as r, dest.open("wb") as fh:
        shutil.copyfileobj(r, fh)


def doc_to_text(path: Path) -> Path | None:
    """Convert a Word document to plain text, if a converter is available."""
    out = path.with_suffix(".txt")
    if shutil.which("textutil"):  # macOS
        rc = subprocess.run(
            ["textutil", "-convert", "txt", "-output", str(out), str(path)],
            capture_output=True,
        )
        return out if rc.returncode == 0 and out.exists() else None
    if shutil.which("antiword") and path.suffix.lower() == ".doc":
        rc = subprocess.run(["antiword", str(path)], capture_output=True)
        if rc.returncode == 0:
            out.write_bytes(rc.stdout)
            return out
    return None


def fetch(osf_code: str, dest_root: Path, study_id: str | None = None) -> FetchResult:
    """Download a study's data + documentation and make the docs readable."""
    study_id = study_id or osf_code
    dest = dest_root / study_id
    dest.mkdir(parents=True, exist_ok=True)
    result = FetchResult(study_id=study_id, dest=dest)

    files = list_files(osf_code)
    if not files:
        result.notes.append("no files visible on OSF (private, or data held elsewhere)")
        return result

    for f in files:
        suffix = Path(f.name).suffix.lower()
        if suffix not in DATA_SUFFIXES | DOC_SUFFIXES or not f.download:
            continue
        target = dest / f.name
        if not target.exists():
            _download(f.download, target)
            time.sleep(0.3)

        if suffix == ".zip":
            try:
                with zipfile.ZipFile(target) as zf:
                    zf.extractall(dest)
                result.notes.append(f"unzipped {f.name}")
            except zipfile.BadZipFile:
                result.notes.append(f"{f.name} is not a readable zip")

    # Classify everything now on disk (including anything unzipped).
    for p in sorted(dest.rglob("*")):
        if not p.is_file():
            continue
        suffix = p.suffix.lower()
        if suffix in {".sav", ".dta", ".por"}:
            result.data_files.append(p)
        elif suffix in DOC_SUFFIXES and suffix != ".txt":
            result.doc_files.append(p)

    for doc in list(result.doc_files):
        if doc.suffix.lower() in {".doc", ".docx"}:
            converted = doc_to_text(doc)
            if converted:
                result.converted.append(converted)
            else:
                result.notes.append(f"could not convert {doc.name} — read it manually")

    if not result.data_files:
        result.notes.append("no .sav/.dta found — check the deposit layout")
    return result
