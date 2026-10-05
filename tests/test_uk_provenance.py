"""`data/catalog/uk_dataverse_provenance.json` is the UK layer's licence record.

It is the one file that says, per deposit, what permits us to ship the rows —
every UK recipe's `licence:` field is transcribed FROM here. It is also the only
catalogue in the project that is maintained by hand, which is why it drifted:
three of its nine deposits still said `"prepared"` after they had been built and
committed, found by a checker reading it rather than by anything that runs.

A hand-maintained status field will always drift. So the two fields that carry
consequences are pinned here against things that cannot be forgotten:

- **`status`** against the tracked recipes. A study is "built" exactly when a
  recipe exists for it. Deliberately NOT checked against `data/processed/`,
  which is gitignored — a test that passes only on a machine that happens to
  have built everything is not a test.
- **`licence`** against the literal string `CC0 1.0`. Every UK row we ship rests
  on that string being right for every deposit, and `embed.py`'s `CLEARED` gate
  keys on the exact spelling.

The checker that found the drift also found no data defect from it, which is the
point worth keeping: this file is read by people deciding what may be published,
not by the build, so its errors are invisible until someone acts on one.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROVENANCE = REPO / "data" / "catalog" / "uk_dataverse_provenance.json"
RECIPES = REPO / "recipes"

STATUSES = {"built", "prepared", "dropped"}


def _catalogue() -> dict[str, dict]:
    data: dict[str, dict] = json.loads(PROVENANCE.read_text())
    return data


def _recipes_for(deposit: str) -> list[str]:
    """Recipe filenames belonging to `deposit`.

    One deposit can hold several experiments (`35M5CV` ships a lodger conjoint
    and a BBC conjoint; `LOGVPZ` a satisfaction study and a risk study), so the
    match is on prefix and the relation is one-to-many.
    """
    return sorted(
        p.name
        for p in RECIPES.glob("*.yaml")
        if p.stem == deposit or p.stem.startswith(f"{deposit}_")
    )


def test_every_deposit_declares_a_known_status() -> None:
    for deposit, record in _catalogue().items():
        assert record.get("status") in STATUSES, (
            f"{deposit} has status {record.get('status')!r}, not one of {sorted(STATUSES)}"
        )


def test_status_built_means_a_recipe_exists_and_the_reverse() -> None:
    """The drift that actually happened, in both directions.

    Forwards catches a deposit marked built with nothing to show for it.
    Backwards catches the real failure: a deposit that got built while its
    record was left saying `prepared`, which is how `35M5CV`, `LOGVPZ` and
    `PMV0TG` spent several commits understating what the UK layer contained.
    """
    for deposit, record in _catalogue().items():
        recipes = _recipes_for(deposit)
        if record["status"] == "built":
            assert recipes, f"{deposit} is marked built but has no recipe in recipes/"
        else:
            assert not recipes, (
                f"{deposit} is marked {record['status']!r} but {recipes} exist(s) — "
                f"it is built, and the catalogue is the file people read to decide "
                f"what may be published"
            )


def test_anything_not_built_says_why() -> None:
    """A `prepared` or `dropped` row with no reason is an open question with no owner."""
    for deposit, record in _catalogue().items():
        if record["status"] != "built":
            reason = (record.get("status_reason") or "").strip()
            assert reason, f"{deposit} is {record['status']!r} with no status_reason"


def test_every_deposit_is_cc0() -> None:
    """The premise the whole UK layer rests on, spelled exactly as `embed.py` expects.

    If a tenth deposit is ever added under different terms, this test is where
    that has to be confronted — rather than in a recipe that quietly copies
    whatever the neighbouring recipe said.
    """
    for deposit, record in _catalogue().items():
        assert record.get("licence") == "CC0 1.0", (
            f"{deposit} records licence {record.get('licence')!r}; every UK deposit here is "
            f"CC0 1.0, and both the recipes and embed.py's CLEARED gate key on that spelling"
        )


def test_every_deposit_carries_a_doi_and_a_description() -> None:
    """Attribution, and enough text to know which study a deposit is without opening it."""
    for deposit, record in _catalogue().items():
        assert str(record.get("doi", "")).startswith("10.7910/DVN/"), (
            f"{deposit} has no Harvard Dataverse DOI"
        )
        assert (record.get("description") or "").strip(), f"{deposit} has no description"
        assert (record.get("authors") or "").strip(), f"{deposit} has no authors"
