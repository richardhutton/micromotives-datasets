"""The v6kqy recipe (TESS 1532, Rode: three photographs of one of four vehicles, before
or after the policy questions) and its answer key.

The generator reads the introductions, the twelve photographs and their sentences, and
every outcome's words out of the fielded questionnaire (asserting the programming
version carries the same words, the same image order and the same directives); these
tests stop a hand edit drifting from it, and check the facts the rows rest on:

- each photograph is the picture under its own "IF DOV_EXP_RODE=k OR DOV_CONTROL=k"
  directive in Q's document order, byte for byte, and the proposal prints the same
  photograph for the same vehicle and page;
- the control group's ATTITUDES and INTEREST1 rows carry no vehicle and no picture
  (they were asked before the stimulus block), and its REVIEW rows carry the
  DOV_CONTROL vehicle;
- our descriptions appraise no vehicle;
- the built rows reproduce SocSci210 (fetched 9 Nov 2026 from its parquet shards and
  transcribed here) cell for cell once our conditions are mapped to their vehicle and
  our 24 outcomes to their six tasks: 58,123 rows, which is their 75,329 less the
  17,206 rows of REVIEW8 (select-all, not built).

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load
from micromotives_datasets.sources import read_any

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_v6kqy.py"
RECIPE = REPO / "recipes" / "images" / "v6kqy.yaml"
RAW = REPO / "data" / "raw" / "v6kqy"
DTA = RAW / "TESS 122 Rode" / "s2861_client.dta"
BUILT = REPO / "data" / "processed" / "images" / "v6kqy.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_v6kqy", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not DTA.exists(), reason="v6kqy deposit not fetched")
needs_built = pytest.mark.skipif(not (BUILT.exists() and DTA.exists()), reason="v6kqy not built")
needs_tools = pytest.mark.skipif(
    not (shutil.which("pdfimages") and shutil.which("sips")), reason="needs pdfimages and sips"
)

# SocSci210, study v6kqy: 75,329 rows, 2,458 people. Their condition_num is the vehicle
# (1 Lightning, 2 XLT, 3 Tesla, 4 Kona: DOV_EXP_RODE, or DOV_CONTROL for the control);
# their task 0 = REVIEW1-7, 1 = REVIEW8, 2 = REVIEW9, 3 = ATTITUDES1, 4 = ATTITUDES2,
# 5 = INTEREST1. Rows per (vehicle, task), task 1 omitted.
SOCSCI210_ROWS = 75_329
SOCSCI210_REVIEW8_ROWS = 17_206
SOCSCI210_PEOPLE = 2458
SOCSCI210_CELLS = {
    (1, 0): 7252, (1, 2): 3685, (1, 3): 1847, (1, 4): 1230, (1, 5): 615,
    (2, 0): 7216, (2, 2): 3718, (2, 3): 1865, (2, 4): 1242, (2, 5): 621,
    (3, 0): 7163, (3, 2): 3643, (3, 3): 1816, (3, 4): 1210, (3, 5): 607,
    (4, 0): 7122, (4, 2): 3635, (4, 3): 1818, (4, 4): 1211, (4, 5): 607,
}  # fmt: skip
# Their response distribution per task, all vehicles together (task 1 omitted).
SOCSCI210_RESPONSES = {
    0: {1: 5870, 2: 6030, 3: 6493, 4: 7090, 5: 3270},
    2: {1: 3376, 2: 2471, 3: 4876, 4: 3063, 5: 895},
    3: {1: 1880, 2: 1616, 3: 1756, 4: 1515, 5: 579},
    4: {1: 1661, 2: 879, 3: 1091, 4: 963, 5: 299},
    5: {1: 1232, 2: 1218},
}


def _their_task(task: int) -> int:
    return 0 if task < 12 else 2 if task < 18 else 3 if task < 21 else 4 if task < 23 else 5


@needs_raw
def test_recipe_is_what_the_generator_writes() -> None:
    assert RECIPE.read_text() == gen.render()


@needs_raw
def test_catalogue_entries_are_what_the_generator_derives() -> None:
    cat = images_mod.load()
    for image_id, entry in gen.catalogue_entries().items():
        assert cat[image_id].model_dump() == entry, image_id
        assert not images_mod.problems(image_id, cat), image_id


@needs_raw
def test_derived_file_is_the_deposit_plus_the_arm_column() -> None:
    assert gen.check_derived()
    df = read_any(gen.DERIVED).df
    treated = df["DOV_EXP_RODE"] != 5
    assert (df.loc[treated, "V6KQY_ARM"] == df.loc[treated, "DOV_EXP_RODE"]).all()
    assert (df.loc[~treated, "V6KQY_ARM"] == 5 + df.loc[~treated, "DOV_CONTROL"]).all()
    assert df.loc[treated, "DOV_CONTROL"].isna().all()


@needs_raw
def test_each_photo_is_the_picture_under_its_own_directive() -> None:
    st = gen.stimuli()
    members = [m for m, _ in st.values()]
    assert sorted(members) == sorted(f"word/media/image{i}.{'png' if i == 5 else 'jpeg'}"
                                     for i in range(3, 15))  # fmt: skip
    # Q's document order: screen by screen, vehicle 1-4 within each screen.
    order = [st[(v, s)][0] for s in gen.SCREENS for v, *_ in gen.VEHICLES]
    assert order == sorted(order, key=lambda m: int(re.findall(r"\d+", m)[0]))
    with zipfile.ZipFile(gen.SIMPLE) as z:
        for (v, s), (member, _) in st.items():
            key = gen.image_key(v, s)
            assert (REPO / "data" / gen.image_file(key, member)).read_bytes() == z.read(member)
    assert st[("tesla", 3)][1].endswith("about 5.8 seconds.")  # fielded, not the proposal's 5.3
    assert st[("xlt", 2)][1] == "The F-150 XLT can drive about 500 miles on one tank of gas."


@needs_raw
def test_programming_version_agrees() -> None:
    gen.check_prog_agrees()
    assert gen.prog_files() == {s: ["LIGHTNING", "XLT", "TESLA", "KONA"] for s in gen.SCREENS}
    assert gen.prog_directives() == {s: [(1, 1), (2, 2), (3, 3), (4, 4)] for s in gen.SCREENS}
    # Q's one directive without DOV_CONTROL's code, read as the PG's "=1"
    assert gen.q_directive_typos() == ["IF DOV_EXP_RODE=1 OR DOV_CONTROL:"]


@needs_raw
@needs_tools
def test_the_proposal_prints_the_same_photographs() -> None:
    for theirs, dist in gen.proposal_distances().items():
        assert min(dist, key=dist.__getitem__) == theirs, (theirs, dist)
        assert dist[theirs] < 15.0
        assert min(v for k, v in dist.items() if k != theirs) > 30.0


def test_each_arm_shows_its_vehicle() -> None:
    rec = load(RECIPE)
    assert rec.condition.source_var == "V6KQY_ARM"
    by_num = {a.condition_num: a for a in rec.condition.arms}
    assert sorted(by_num) == list(range(9))
    names = {"lightning": "Ford F-150 Lightning", "xlt": "Ford F-150 XLT",
             "tesla": "Tesla Model 3", "kona": "Hyundai Kona Electric"}  # fmt: skip
    for n, (key, raw) in enumerate([("lightning", 1), ("xlt", 2), ("tesla", 3), ("kona", 4)]):
        pairs = ((by_num[n], "vehicle_first", raw), (by_num[n + 4], "questions_first", raw + 5))
        for arm, order, first in pairs:
            assert arm.raw == first
            assert arm.factors == {"vehicle": key, "order": order}
            assert arm.images == [f"v6kqy_{key}_{s}" for s in (1, 2, 3)]
            assert arm.text.count(images_mod.IMAGE_MARKER) == 3
            assert f'"This is the {names[key]},' in arm.text
            other = [v for k, v in names.items() if k != key]
            assert not any(o in arm.text for o in other)
            assert ("background questions" in arm.text) == (order == "questions_first")
    pre = by_num[8]
    assert pre.raw == 5 and pre.images == [] and pre.factors["vehicle"] == "none"
    assert images_mod.IMAGE_MARKER not in pre.text
    assert "background questions and then learn about a product" in pre.text
    assert not re.search(r"Ford|Tesla|Hyundai|F-150|Model 3|Kona", pre.text)
    assert rec.condition.shared_context == (
        "This survey is about your opinions of products currently on the market."
    )


def test_policy_questions_take_the_assignment_before_the_vehicle() -> None:
    rec = load(RECIPE)
    first = {o.var or "": o.condition_var for o in rec.outcomes}
    for var, cv in first.items():
        before = var.startswith("ATTITUDES") or var == "INTEREST1"
        assert cv == ("DOV_EXP_RODE" if before else None), var
    assert len(rec.outcomes) == 24
    assert not any(o.var and o.var.startswith(("REVIEW8", "REVIEW10", "REVIEW11", "REVIEW12"))
                   for o in rec.outcomes)  # fmt: skip


def _appraising(text: str) -> list[str]:
    return re.findall(gen.APPRAISAL, text.lower())


def test_the_appraisal_check_catches_and_passes() -> None:
    assert _appraising("A sleek, powerful truck.") == ["sleek", "powerful"]
    assert _appraising("An eco-friendly car") == ["eco"]
    # what it must not catch: colours, places, plain nouns
    assert _appraising("A dark blue pickup truck on a road; a bonnet; a green hillside.") == []


def test_descriptions_appraise_nothing_and_quote_what_is_printed() -> None:
    assert set(gen.DESCRIPTIONS) == set(gen.TEXT_IN_IMAGE)
    for key, text in gen.DESCRIPTIONS.items():
        assert not _appraising(text), (key, _appraising(text))
        words = gen.TEXT_IN_IMAGE[key]
        if words:
            assert f'"{words}"' in text, key
        else:
            assert "legible" in text or "too small to read" in text, key


@needs_built
def test_control_rows_see_no_vehicle_until_they_had_seen_one() -> None:
    rows = pd.read_parquet(BUILT)
    raw = read_any(gen.DERIVED).df
    triples = zip(raw["CaseId"], raw["DOV_EXP_RODE"], raw["DOV_CONTROL"].fillna(0), strict=True)
    ctrl = {f"v6kqy:{int(c)}": int(k) for c, e, k in triples if e == 5}
    mine = rows[rows["participant_id"].isin(ctrl)]
    assert mine["participant_id"].nunique() == len(ctrl) == 453
    before = mine["task_num"] >= 18
    assert (mine.loc[before, "condition_num"] == 8).all()
    assert mine.loc[before, "condition_images"].map(len).eq(0).all()
    after = mine[~before]
    assert (after["condition_num"] == after["participant_id"].map(ctrl) + 3).all()
    assert after["condition_images"].map(len).eq(3).all()
    treated = rows[~rows["participant_id"].isin(ctrl)]
    assert treated["condition_num"].between(0, 3).all()
    assert treated.groupby("participant_id")["condition_num"].nunique().eq(1).all()


@needs_built
def test_unsure_is_dropped_and_scales_hold() -> None:
    rows = pd.read_parquet(BUILT)
    df = read_any(gen.DERIVED).df
    for task, var in ((1, "REVIEW2"), (2, "REVIEW3")):
        got = rows[rows["task_num"] == task]["response_num"]
        assert set(got) == {1.0, 2.0}
        assert len(got) == int(df[var].isin([1, 2]).sum())
    assert rows["response_num"].between(1, 5).all()


@needs_built
def test_rows_reproduce_socsci210() -> None:
    rows = pd.read_parquet(BUILT)
    assert len(rows) == SOCSCI210_ROWS - SOCSCI210_REVIEW8_ROWS
    assert rows["participant_id"].nunique() == SOCSCI210_PEOPLE
    raw = read_any(gen.DERIVED).df
    vehicle = {
        f"v6kqy:{int(c)}": int(e) if e != 5 else int(k)
        for c, e, k in zip(
            raw["CaseId"], raw["DOV_EXP_RODE"], raw["DOV_CONTROL"].fillna(0), strict=True
        )
    }
    theirs_cond = rows["participant_id"].map(vehicle)
    theirs_task = rows["task_num"].map(_their_task)
    cells = pd.DataFrame({"c": theirs_cond, "t": theirs_task}).value_counts().to_dict()
    assert cells == SOCSCI210_CELLS
    for task, dist in SOCSCI210_RESPONSES.items():
        got = rows[theirs_task == task]["response_num"].astype(int).value_counts().to_dict()
        assert got == dist, task


@needs_built
def test_persona_has_no_truncated_or_instructed_religion() -> None:
    rows = pd.read_parquet(BUILT)
    religions = {json.loads(p).get("religion") for p in rows["persona"].unique()}
    assert not any(r and r.endswith("Pent") for r in religions)
    assert "Something else" in religions
    assert not any(r and "specify" in r for r in religions)


@needs_built
def test_built_parquet_is_current(tmp_path: Path) -> None:
    """The answer-key tests read the parquet on disk, so a stale build would let a
    generator change (e.g. two vehicles' photos swapped) pass them unseen. Rebuild
    from the current recipe in memory and require the same rows."""
    from micromotives_datasets import cli

    rec, rows, _ = cli._load_and_build(RECIPE)
    fresh = pd.read_parquet(cli._write_parquet(rows, tmp_path, rec))
    on_disk = pd.read_parquet(BUILT)
    assert fresh.equals(on_disk), "v6kqy.parquet is stale: rebuild with mmds build"
