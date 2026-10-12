"""The unseen-studies split (scripts/make_splits.py, data/catalog/splits/)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPLITS = ROOT / "data" / "catalog" / "splits"

_spec = importlib.util.spec_from_file_location("make_splits", ROOT / "scripts" / "make_splits.py")
assert _spec and _spec.loader
make_splits = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(make_splits)

MAPPING = json.loads((SPLITS / "participant_mapping.json").read_text())
STUDY_OF = json.loads((SPLITS / "study_of_recipe.json").read_text())


def test_committed_split_is_what_the_script_makes() -> None:
    for name, text in make_splits.outputs().items():
        assert (SPLITS / name).read_text() == text, f"{name} is stale: run scripts/make_splits.py"


def test_every_recipe_is_on_exactly_one_side() -> None:
    seen, unseen = set(MAPPING["seen"]), set(MAPPING["unseen"])
    assert not seen & unseen
    assert set(STUDY_OF.values()) == seen | unseen
    assert {p.stem for p in (ROOT / "recipes").glob("*.yaml")} == set(STUDY_OF)


def test_experiments_sharing_people_or_design_stay_together() -> None:
    together = [
        ("ukds_6849_vig_housework_w5", "ukds_6849_vig_housework_w6"),  # one IP expt, two waves
        ("ukds_6849_eq5d3l_w11", "ukds_6849_eq5d5l_w11"),  # one IP experiment, two arms
        ("del_panel_w4_cost_of_living", "del_panel_w4_east_africa_drought"),  # one DEL survey
        ("35M5CV_bbc", "35M5CV_lodger"),  # one deposit
    ]
    for a, b in together:
        assert STUDY_OF[a] == STUDY_OF[b], (a, b)
    assert STUDY_OF["del_panel_w4_cost_of_living"] != STUDY_OF["del_panel_w3_leadership"]


def test_socsci210_sides_are_kept_for_shared_tess_studies() -> None:
    ours = set(STUDY_OF.values())
    unseen = set(MAPPING["unseen"])
    shared_unseen = ours & make_splits.SOCSCI210_UNSEEN
    shared_seen = ours & make_splits.SOCSCI210_SEEN
    assert shared_unseen == {"5hqan", "7jt2f", "8ctbk", "a5v96", "c5r2f", "rpw4u"}
    assert shared_unseen <= unseen
    assert not shared_seen & unseen


def test_every_source_is_in_the_test_set_at_about_the_set_share() -> None:
    studies = make_splits.experiments_by_study()
    for source in {str(e["source"]) for e in studies.values()}:
        ids = [s for s, e in studies.items() if e["source"] == source]
        held = [s for s in ids if s in MAPPING["unseen"]]
        assert held, f"no {source} study is unseen"
        assert abs(len(held) / len(ids) - make_splits.UNSEEN_SHARE) < 0.1, source
