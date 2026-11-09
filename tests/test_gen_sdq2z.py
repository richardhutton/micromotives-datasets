"""`recipes/sdq2z.yaml` must stay exactly what its generator derives.

Same shape as `tests/test_gen_35M5CV_bbc.py`: the recipe is machine-generated
(one arm per distinct pair of buildings shown and answered), so the judgement
lives in `scripts/gen_sdq2z.py` and these tests stop the two drifting apart,
and pin the two judgements a numeric check cannot see: which data column is
Building 1, and that the table text says what the codes say.

The tests need the deposit, which is gitignored, so they skip when it is absent.
"""

from __future__ import annotations

import copy
import functools
import importlib.util
import random
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_sdq2z.py"
RECIPE = REPO / "recipes" / "sdq2z.yaml"
DATA = REPO / "data" / "raw" / "sdq2z" / "TESS209_Hankinson_Client.sav"

needs_data = pytest.mark.skipif(not DATA.exists(), reason="sdq2z deposit not fetched")


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_sdq2z", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_sdq2z"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _arms():
    return _generator().build_arms()


@functools.cache
def _dataset():
    return _generator().spss.read(DATA)


@needs_data
def test_the_recipe_is_exactly_what_the_generator_derives() -> None:
    gen = _generator()
    recipe = yaml.safe_load(RECIPE.read_text())
    assert recipe == gen.build_recipe(), (
        "the recipe and its generator have diverged; regenerate with "
        "`uv run python scripts/gen_sdq2z.py --write` and read the diff before accepting it"
    )


@needs_data
def test_one_arm_per_distinct_answered_pair() -> None:
    gen = _generator()
    arms = _arms()
    assert len(arms) == 14_620
    keys = [tuple(a["raw_values"][k] for k in gen.KEY_VARS) for a in arms]
    assert len(set(keys)) == len(keys)
    assert [a["condition_num"] for a in arms] == list(range(len(arms)))


@needs_data
def test_building_1_is_version1_read_from_the_data_s_own_labels() -> None:
    """Re-derive each sampled arm's table from the .sav's value and column
    labels, not from the generator's transcription, and check Building 1 holds
    the Version1 code and Building 2 the Version2 code, row by row, in Table 2's
    order. Swapping the sides, or the rows, fails this."""
    ds = _dataset()
    arms = _arms()
    for arm in random.Random(0).sample(arms, 300):
        paragraphs = arm["text"].split("\n\n")
        assert len(paragraphs) == 7
        for k, para in enumerate(paragraphs, start=1):
            col1 = f"Screen1_Attribute{k}_Version1"
            col2 = f"Screen1_Attribute{k}_Version2"
            heading = " ".join(ds.column_labels[col1].split())
            b1 = ds.value_labels[col1][float(arm["raw_values"][col1])]
            b2 = ds.value_labels[col2][float(arm["raw_values"][col2])]
            assert para == f"{heading}\n- Building 1: {b1}\n- Building 2: {b2}"


@needs_data
def test_every_answered_screen_finds_its_arm_and_no_refused_only_pair_is_declared() -> None:
    gen = _generator()
    ds = _dataset()
    declared = {tuple(a["raw_values"][k] for k in gen.KEY_VARS) for a in _arms()}
    answered: set[tuple[int, ...]] = set()
    for t in range(1, 6):
        cols = gen._condition_vars(t)
        for _, row in ds.df.iterrows():
            if row[f"Screen{t}"] in (1, 2):
                answered.add(tuple(int(row[c]) for c in cols))
    assert answered == declared


@needs_data
def test_the_transcription_check_catches_a_wrong_label() -> None:
    """`_check_against_data` must pass on the real transcription and fail when
    one level is altered, or it is not known to check anything."""
    gen = _generator()
    ds = _dataset()
    gen._check_against_data(ds)
    original = gen.TABLE2
    try:
        broken = copy.deepcopy(original)
        broken[4][2][2] = "Car park"
        gen.TABLE2 = broken
        with pytest.raises(ValueError, match="value labels"):
            gen._check_against_data(ds)
    finally:
        gen.TABLE2 = original
    gen._check_against_data(ds)


def test_the_place_fill_is_never_left_as_a_bracket_or_a_city() -> None:
    """The screen's city fill is the CONVENTIONS.md own-place clause in both the
    shared context and the question; no `[INSERT ...]` survives."""
    gen = _generator()
    for text in (gen.SHARED_CONTEXT, gen.QUESTION):
        assert "[" not in text and "INSERT" not in text
        assert gen.PLACE in text
    assert gen.SHARED_CONTEXT.count(gen.PLACE) == 4
