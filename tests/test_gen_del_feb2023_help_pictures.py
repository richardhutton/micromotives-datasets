"""The DEL Feb 2023 paired-photo recipe (IMG07): who needs / deserves help the most.

The generator codes each screen's two pictures from the .sav's `<img>` tags into a
derived .sav and writes one arm per ordered (A, B) pair; these tests stop a hand edit
drifting from it and check the facts the rows rest on:

- the derived file is the deposit plus the eight code columns, nothing else changed;
- each arm shows its A picture first and its B picture second, and its factors are
  read off those two file names;
- the persona block is the Feb 2023 text builds' own;
- every built row re-derives from the deposit's own strings (alt file names and
  answers), with no code table in between, so a wrong code, a swapped A/B or a
  wrong screen-to-variable link fails here.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
import yaml

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_del_feb2023_help_pictures.py"
RECIPE = REPO / "recipes" / "images" / "del_sandbox_feb2023_help_pictures.yaml"
BUILT = REPO / "data" / "processed" / "images" / "del_sandbox_feb2023_help_pictures.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_del_feb2023_help_pictures", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.SAV.exists(), reason="DEL Feb 2023 deposit not fetched")
needs_built = pytest.mark.skipif(
    not (BUILT.exists() and gen.SAV.exists()), reason="IMG07 not built"
)


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
def test_derived_file_is_the_deposit_plus_the_code_columns() -> None:
    import pyreadstat

    a, ma = pyreadstat.read_sav(str(gen.SAV))
    b, mb = pyreadstat.read_sav(str(gen.DERIVED))
    added = [gen.code_var(k, s) for k in gen.SCREENS for s in "AB"]
    assert list(b.columns) == list(a.columns) + added
    pd.testing.assert_frame_equal(a, b[a.columns])
    pd.testing.assert_frame_equal(gen.coded(a)[added], b[added], check_dtype=False)
    for var, labels in ma.variable_value_labels.items():
        assert mb.variable_value_labels[var] == labels, var


def test_codes_follow_the_instruments_array() -> None:
    assert len(set(gen.IMG_NAME_ARR)) == 10
    assert [gen.CODE[n] for n in gen.IMG_NAME_ARR] == list(range(1, 11))


def test_each_arm_shows_a_then_b_and_its_factors_name_them() -> None:
    rec = load(RECIPE)
    arms = rec.condition.arms
    assert [a.condition_num for a in arms] == list(range(90))
    seen = set()
    by_code = {c: n for n, c in gen.CODE.items()}
    for arm in arms:
        assert arm.raw_values is not None
        a = by_code[arm.raw_values[gen.code_var(1, "A")]]
        b = by_code[arm.raw_values[gen.code_var(1, "B")]]
        assert a != b
        seen.add((a, b))
        assert arm.images == [gen.image_id(a), gen.image_id(b)]
        assert arm.text.index("Picture A:") < arm.text.index("Picture B:")
        assert arm.text.count(images_mod.IMAGE_MARKER) == 2
        assert arm.factors == {
            "person_A": {"M": "man", "W": "woman"}[a[0]],
            "framing_A": a.split(".")[0][2:],
            "person_B": {"M": "man", "W": "woman"}[b[0]],
            "framing_B": b.split(".")[0][2:],
        }
    assert len(seen) == 90


def test_each_screen_reads_its_own_pictures_and_answer() -> None:
    rec = load(RECIPE)
    assert [o.var for o in rec.outcomes] == ["images_1", "images_2", "images_3", "images_4"]
    for o in rec.outcomes:
        k = o.task_num + 1
        assert rec.condition_vars_for(o) == [gen.code_var(k, "A"), gen.code_var(k, "B")]
        what = "needs help" if k <= 2 else "deserves help"
        assert f"you think {what} the most." in o.question
        # A row never cites its place in the sequence.
        assert not re.search(r"\b(pair|screen|first|second|third|fourth)\b", o.question, re.I)
    assert rec.missing_codes == [5, 8, 9]
    assert 5 not in rec.response_recode


def test_persona_is_the_feb_2023_text_builds() -> None:
    rec = yaml.safe_load(RECIPE.read_text())
    src = yaml.safe_load(gen.PERSONA_FROM.read_text())
    for key in ("persona_map", "persona_missing", "persona_label_rewrite", "participant_id_var"):
        assert rec[key] == src[key], key
    assert rec["study_id"] == src["study_id"] == "del"


@needs_built
def test_every_row_rederives_from_the_deposits_own_strings() -> None:
    import pyreadstat

    raw, _ = pyreadstat.read_sav(str(gen.SAV))
    alt = re.compile(r"alt='([MW]_[A-Z]+)\.jpe?g'")
    expected = set()
    for _, r in raw.iterrows():
        pid = f"del:{int(r['GUNQID'])}"
        for k in gen.SCREENS:
            answer = r[f"images_{k}"]
            if answer in (1, 2, 3, 4):
                a = alt.search(r[gen.tag_var(k, "A")]).group(1).lower()  # type: ignore[union-attr]
                b = alt.search(r[gen.tag_var(k, "B")]).group(1).lower()  # type: ignore[union-attr]
                expected.add((pid, k - 1, f"del_feb2023_{a}", f"del_feb2023_{b}", int(answer)))
    rows = pd.read_parquet(BUILT)
    got = {
        (p, int(t), str(i[0]), str(i[1]), int(v))
        for p, t, i, v in zip(
            rows["participant_id"],
            rows["task_num"],
            rows["condition_images"],
            rows["response_num"],
            strict=True,
        )
    }
    assert len(rows) == len(got) == 6792
    assert got == expected
