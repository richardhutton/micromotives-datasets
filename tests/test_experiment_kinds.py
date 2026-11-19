"""Every tracked experiment has one recorded kind, from the service's eleven.

rich (19 Nov 2026): the kind breakdown changed every time it was asked about, because
nothing recorded a kind; each answer was worked out afresh from Jev's guesses. The
record is `data/catalog/experiment_kinds.json`, and the coverage page reads it. These
tests keep it complete and inside the vocabulary.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CATALOG = REPO / "data" / "catalog"
BUILT = {"Built", "Built (risky)"}
OPEN = {"Buildable", "Needs checking", "Waiting for images"}
BASES = {"named+jev", "read", "guess"}


def _recorded() -> dict[str, dict[str, str]]:
    data: dict[str, dict[str, str]] = json.loads((CATALOG / "experiment_kinds.json").read_text())[
        "kinds"
    ]
    return data


def _vocabulary() -> set[str]:
    return {k["id"] for k in json.loads((CATALOG / "design_kinds.json").read_text())["kinds"]}


def _tracked() -> list[tuple[str, str]]:
    """(key, status) for every built or open experiment on both lists."""
    out = []
    for r in json.loads((CATALOG / "experiment_list.json").read_text())["rows"]:
        out.append((f"text:{r.get('recipe') or r['id']}", r["status"]))
    for r in json.loads((CATALOG / "image_experiment_list.json").read_text())["rows"]:
        out.append((f"image:{r['id']}", r["status"]))
    return [(k, s) for k, s in out if s in BUILT | OPEN]


def test_every_tracked_experiment_has_a_kind() -> None:
    recorded = _recorded()
    missing = sorted(k for k, _ in _tracked() if k not in recorded)
    assert not missing, f"no kind recorded in experiment_kinds.json for: {missing}"


def test_every_kind_is_one_of_the_eleven() -> None:
    vocabulary = _vocabulary()
    assert len(vocabulary) == 11, vocabulary
    wrong = {k: v["kind"] for k, v in _recorded().items() if v["kind"] not in vocabulary}
    assert not wrong, f"kinds outside design_kinds.json: {wrong}"


def test_no_built_experiment_rests_on_a_guess() -> None:
    """A guess is allowed for a candidate described from its title; a built experiment
    has a recipe and design notes, so its kind must have been read."""
    recorded = _recorded()
    guessed = sorted(
        k for k, s in _tracked() if s in BUILT and recorded.get(k, {}).get("basis") == "guess"
    )
    assert not guessed, guessed
    assert {v["basis"] for v in recorded.values()} <= BASES
