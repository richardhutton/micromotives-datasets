"""The image catalogue: what an image id in a row refers to.

A row whose condition was a picture carries the picture's ID in
`Row.condition_images`, never the picture itself. The ID resolves here, in
`data/catalog/images.json` (tracked: it is metadata about stimuli), to the file
under `data/raw/` (not tracked: the files carry their sources' licences), the
file's sha256, where it came from, its licence, and two pieces of text:

- `text_in_image`: the words printed in the image, word-for-word. This is
  transcription, so it is checkable against the file.
- `description`: what the picture shows, in our words. This is written by us,
  so it gets the same checker treatment as a condition (CLAUDE.md, "The
  condition is the only part we write").

The training export resolves each ID through `resolve()`, which refuses a missing
file or a changed hash, so a model is never trained on a different picture from
the one the row's respondent saw.

The condition text marks where each image sat with `IMAGE_MARKER`, one per ID,
in order, so a vision model receives the picture at the right place.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, Field

from .config import DATA_DIR

CATALOG = DATA_DIR / "catalog" / "images.json"
IMAGE_MARKER = "<image>"


class Image(BaseModel):
    file: str = Field(description="Path relative to the repository's data/ directory.")
    sha256: str
    source: str = Field(description="Where the file came from, precisely enough to fetch again.")
    licence: str
    text_in_image: str | None = Field(
        default=None, description="Words printed in the image, word-for-word."
    )
    description: str = Field(description="What the picture shows. Written by us; checked.")


def load(path: Path = CATALOG) -> dict[str, Image]:
    raw = json.loads(path.read_text()) if path.exists() else {}
    return {k: Image(**v) for k, v in raw.items()}


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def problems(image_id: str, catalog: dict[str, Image], data_dir: Path = DATA_DIR) -> list[str]:
    """Why this ID cannot be trusted, or [] if it can."""
    img = catalog.get(image_id)
    if img is None:
        return [f"{image_id}: not in the image catalogue"]
    f = data_dir / img.file
    if not f.exists():
        return [f"{image_id}: file missing ({img.file})"]
    if sha256_of(f) != img.sha256:
        return [f"{image_id}: file changed since catalogued ({img.file})"]
    return []


def resolve(image_id: str, catalog: dict[str, Image], data_dir: Path = DATA_DIR) -> Path:
    """The file for an ID, refusing a missing or altered one."""
    found = problems(image_id, catalog, data_dir)
    if found:
        raise ValueError("; ".join(found))
    return data_dir / catalog[image_id].file
