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

MAPPING = json.loads((SPLITS / "studies_mapping.json").read_text())
STUDY_OF = json.loads((SPLITS / "study_of_recipe.json").read_text())


def test_committed_split_is_what_the_script_makes() -> None:
    for name, text in make_splits.outputs().items():
        assert (SPLITS / name).read_text() == text, f"{name} is stale: run scripts/make_splits.py"


def test_every_recipe_is_on_exactly_one_side() -> None:
    seen, unseen = set(MAPPING["seen"]), set(MAPPING["unseen"])
    excluded = set(make_splits.EXCLUDED)
    assert not seen & unseen
    assert not (seen | unseen) & excluded
    assert set(STUDY_OF.values()) == seen | unseen | excluded
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


def test_excluding_a_study_moves_no_other_study() -> None:
    studies = make_splits.experiments_by_study()
    with_all = make_splits.split(studies)
    saved = dict(make_splits.EXCLUDED)
    make_splits.EXCLUDED.clear()
    try:
        without = make_splits.split(studies)
    finally:
        make_splits.EXCLUDED.update(saved)
    for side in ("seen", "unseen"):
        assert set(with_all[side]) == set(without[side]) - set(saved), side


def test_hidden_text_never_reaches_train() -> None:
    rows = make_splits.rows_by_experiment()
    for name, (number, text, _) in make_splits.HIDE.items():
        mapping = json.loads((SPLITS / name).read_text())
        for experiment, sides in mapping.items():
            df = make_splits.numbered_rows(rows[experiment])
            train = set(df.loc[sides["train"], text])
            held = set(df.loc[sides["eval"], text])
            assert not train & held, (name, experiment)  # the rule itself, on the text
            assert sorted(sides["train"] + sides["eval"]) == list(range(len(df))), experiment
            unit = make_splits.units(df, number, text)
            n = unit.nunique()
            assert n >= make_splits.MIN_GROUPS, (name, experiment)
            hidden = unit[sides["eval"]].nunique()
            assert hidden == max(1, int(make_splits.HIDDEN_SHARE * n + 0.5)), experiment
        eligible = {
            e
            for e, df in rows.items()
            if make_splits.units(df, number, text).nunique() >= make_splits.MIN_GROUPS
            and STUDY_OF[e] not in make_splits.EXCLUDED
        }
        assert set(mapping) == eligible, name


def test_numbers_sharing_text_are_one_unit() -> None:
    import pandas as pd

    df = pd.DataFrame({"n": [0, 1, 2, 3, 4], "t": ["a", "a", "b", "c", "b"]})
    assert make_splits.units(df, "n", "t").tolist() == [0, 0, 2, 3, 2]


def test_export_puts_each_study_on_its_split_side() -> None:
    import sys

    import pandas as pd

    sys.path.insert(0, str(ROOT / "scripts"))
    import export

    mapping = {"seen": ["a", "b"], "unseen": ["c"]}
    sides = export.side_of(pd.Series(["a", "c", "b", "x"]), mapping).tolist()
    assert sides[:3] == ["train", "eval", "train"]
    assert pd.isna(sides[3])  # in neither list (excluded): in neither file
