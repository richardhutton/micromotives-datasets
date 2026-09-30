"""Apply the persona crosswalks at build time, so the corpus comes out harmonised.

`bands.py` and `categories.py` WORK OUT the mappings; `scripts/persona_*.py`
run them and save the result to `data/catalog/persona_crosswalk_<field>.json`.
This applies those files during the melt. Without it the mappings exist beside
the corpus and do nothing, which is exactly where they sat until this module.

Applied to the Persona itself rather than at render time, so the parquet carries
canonical values and every downstream consumer gets the same vocabulary without
having to know this layer exists. The raw label is always recoverable from the
source `.sav`, so nothing is lost by normalising here.

**A label with no mapping is left ALONE, not dropped.** The alternative —
blanking anything unrecognised — would silently thin the corpus as new studies
arrive with new schemes, and the whole point of this work was to stop that class
of silent loss. QC rule 14 reports unmapped values instead, so a sixth ethnicity
scheme announces itself rather than quietly degrading coverage.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from dataclasses import field as dc_field
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[3] / "data" / "catalog"


@dataclass
class Crosswalk:
    """Per persona field, a source label -> canonical label map."""

    maps: dict[str, dict[str, str]] = dc_field(default_factory=dict)
    vocab: dict[str, set[str]] = dc_field(default_factory=dict)

    @classmethod
    def load(cls, catalog: Path | None = None) -> Crosswalk:
        """Every `persona_crosswalk_<field>.json` in the catalog.

        The saved files are keyed by SCHEME, because that is how they are
        derived and reviewed. Here they are flattened to one label -> canonical
        map per field, which is what the melt can actually use: it sees a label,
        not a scheme. Flattening is safe only if no label means two different
        things across schemes, so that is asserted rather than assumed.
        """
        root = catalog or CATALOG
        maps: dict[str, dict[str, str]] = {}
        vocab: dict[str, set[str]] = {}
        for path in sorted(root.glob("persona_crosswalk_*.json")):
            field_name = path.stem.replace("persona_crosswalk_", "")
            data = json.loads(path.read_text())
            flat: dict[str, str] = {}
            for scheme, mapping in data["schemes"].items():
                for src, dst in mapping.items():
                    if src in flat and flat[src] != dst:
                        raise ValueError(
                            f"{field_name}: label {src!r} maps to both {flat[src]!r} and "
                            f"{dst!r} (scheme {scheme}) — cannot flatten"
                        )
                    flat[src] = dst
            maps[field_name] = flat
            vocab[field_name] = set(data["canonical"].values())
        return cls(maps=maps, vocab=vocab)

    def apply(self, field_name: str, label: str) -> str:
        """The canonical label, or the original when this field has no mapping."""
        return self.maps.get(field_name, {}).get(label, label)

    def unmapped(self, field_name: str, label: str) -> bool:
        """True when we have a vocabulary for this field and the label is outside it."""
        known = self.maps.get(field_name)
        if not known:
            return False
        return label not in known and label not in self.vocab.get(field_name, set())
