"""`recipes/POMIFD.yaml` and its derived wide CSV must stay exactly what
`scripts/gen_POMIFD.py` derives.

Same shape as `tests/test_gen_PMV0TG.py`/`tests/test_gen_RJTVG8.py`: the
recipe's `condition.arms` and `outcomes` are machine-generated (5,579 arms,
one per distinct RENDERED argument pair actually drawn across 13,268
observations -- see `gen_POMIFD.py`'s `build_arms()` docstring for why this
is fewer than the 6,972 distinct (policy, pick) combinations drawn), so the
judgement lives in the generator and this test is what stops the recipe and
the generator drifting apart silently. It also pins the derived
`data/raw/POMIFD/experiment_one_wide.csv`, since that file carries judgement
too (the persona text-resolution, the combined policy/pick draw codes) and is
not itself reviewable the way the recipe YAML is.

The tests need the deposit, which is gitignored, so they skip when the data
is absent rather than failing on a fresh clone.
"""

from __future__ import annotations

import functools
import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_POMIFD.py"
RECIPE = REPO / "recipes" / "POMIFD.yaml"
RAW = REPO / "data" / "raw" / "POMIFD" / "experiment_one.sav"
WIDE = REPO / "data" / "raw" / "POMIFD" / "experiment_one_wide.csv"


# Memoised for the session -- see tests/test_gen_PMV0TG.py's identical comment:
# `load()`/`build_wide()`/`build_arms()` each re-read the deposit, and the
# recipe is multiple MB of YAML, so re-deriving per test makes the suite slow
# enough that it stops getting run.
@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_POMIFD", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_POMIFD"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _loaded():
    gen = _generator()
    return gen.load()


@pytest.mark.skipif(not RAW.exists(), reason="POMIFD deposit not fetched (data/raw is gitignored)")
def test_the_recipe_is_exactly_what_the_generator_derives() -> None:
    gen = _generator()
    _ds, df, prompts = _loaded()
    generated_arms = gen.build_arms(df, prompts)
    generated_outcomes = gen.build_outcomes()
    recipe = yaml.safe_load(RECIPE.read_text())
    assert generated_arms == recipe["condition"]["arms"], (
        "the recipe's arms and its generator have diverged — regenerate with "
        "`uv run python scripts/gen_POMIFD.py --write`, and read the diff before accepting it"
    )
    assert generated_outcomes == recipe["outcomes"], (
        "the recipe's outcomes and its generator have diverged — regenerate with "
        "`uv run python scripts/gen_POMIFD.py --write`"
    )


@pytest.mark.skipif(not RAW.exists(), reason="POMIFD deposit not fetched")
def test_the_wide_csv_is_exactly_what_the_generator_derives() -> None:
    gen = _generator()
    ds, df, _prompts = _loaded()
    wide = gen.build_wide(ds, df)
    assert WIDE.exists(), "data/raw/POMIFD/experiment_one_wide.csv missing — run --write"
    on_disk = gen.read_wide()
    import pandas as pd

    pd.testing.assert_frame_equal(on_disk, wide)


@pytest.mark.skipif(not RAW.exists(), reason="POMIFD deposit not fetched")
def test_structural_counts() -> None:
    """Pins the brief's own headline numbers, so a re-fetched deposit that
    drifts from them fails loudly rather than being assumed unchanged.
    `load()`/`build_wide()`/`build_arms()` already assert most of this
    internally; re-deriving the independent parts here means this test does
    not merely confirm the generator agrees with itself.
    """
    gen = _generator()
    ds, df, prompts = _loaded()

    assert df.shape == (3_317, 56)
    draws = gen._draws(df)
    assert len(draws) == 13_268
    assert draws.groupby("ID").size().eq(4).all()

    wide = gen.build_wide(ds, df)
    assert len(wide) == 3_317

    arms = gen.build_arms(df, prompts)
    assert len(arms) == 5_579

    outcomes = gen.build_outcomes()
    assert len(outcomes) == 12
    assert sorted(o["task_num"] for o in outcomes) == list(range(12))

    # 336 arguments = 14 rhetorical elements x 12 policy issues x 2 positions.
    import pandas as pd

    canon = pd.read_csv(REPO / "data" / "raw" / "POMIFD" / "canonical_sentences_v2.csv")
    assert canon.shape[0] == 336
    assert canon["Policy"].nunique() == 12
    assert canon["Element"].nunique() == 14
    assert canon.groupby(["Policy", "Element", "Pro.Con"]).ngroups == 336


@pytest.mark.skipif(not RAW.exists(), reason="POMIFD deposit not fetched")
def test_response_coding_matches_the_datas_own_value_labels_not_the_codebook() -> None:
    """Regression pin for the brief's central finding on this study:
    `Codebook.pdf` documents sc_X as 1=one/2=same/3=two, but the .sav's own
    embedded value-label dictionary says 1=one/2=TWO/3=same. This recipe
    follows the DATA. If a re-fetched deposit ever reverted to the codebook's
    order, this fails rather than silently flipping two-thirds of the scale.
    """
    ds, _, _ = _loaded()
    assert ds.value_labels["sc1"] == {
        1.0: "Argument **one** is more persuasive",
        2.0: "Argument **two** is more persuasive",
        3.0: "They are about the same",
        8.0: "Skipped",
        9.0: "Not Asked",
    }


@pytest.mark.skipif(not RAW.exists(), reason="POMIFD deposit not fetched")
def test_euvote_and_vote17_are_not_in_the_persona_map() -> None:
    """Regression pin for the domain ruling the task brief asked for by name:
    `pastvote_EURef`/`pastvote_2017` must never enter `persona_map`, because on
    several of the 12 issues a respondent's referendum/party vote sits close
    to a prediction of which side's argument they would find persuasive.
    """
    recipe = yaml.safe_load(RECIPE.read_text())
    mapped_source_vars = set(recipe["persona_map"].values())
    assert "pastvote_EURef" not in mapped_source_vars
    assert "pastvote_2017" not in mapped_source_vars
    # voted2017 (turnout) and politics_scale_profile_update (general ideology)
    # ARE kept — the ruling distinguishes them from vote CHOICE.
    gen = _generator()
    source_vars = {var for _, var, _ in gen.PERSONA_SPEC}
    assert "voted2017" in source_vars
    assert "politics_scale_profile_update" in source_vars
