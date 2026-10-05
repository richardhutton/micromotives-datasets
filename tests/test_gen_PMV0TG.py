"""`recipes/PMV0TG.yaml` and its derived wide CSV must stay exactly what
`scripts/gen_PMV0TG.py` derives.

Same shape as `tests/test_gen_EFXNLX.py`: the recipe's `condition.arms` and
`outcomes` are machine-generated (9,272 arms, one per distinct 10-attribute
profile pair actually drawn across 9,320 rounds), so the judgement lives in
the generator and this test is what stops the recipe and the generator
drifting apart silently. It also pins the derived
`data/raw/PMV0TG/nbh_clean_conjoint_UK_wide.csv`, since that file carries
judgement too (the reshape, the manufactured attribute codes) and is not
itself reviewable the way the recipe YAML is.

The tests need the deposit, which is gitignored, so they skip when the data
is absent rather than failing on a fresh clone.
"""

from __future__ import annotations

import functools
import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_PMV0TG.py"
RECIPE = REPO / "recipes" / "PMV0TG.yaml"
RAW = REPO / "data" / "raw" / "PMV0TG" / "nbh_clean_conjoint_global.tab"
WIDE = REPO / "data" / "raw" / "PMV0TG" / "nbh_clean_conjoint_UK_wide.csv"


# The expensive calls below are memoised for the session. `build_arms()` reads
# the deposit and re-derives every condition; the recipe is up to 57MB of YAML.
# Each test file called them 4-7 times, nothing cached, and the suite reached
# 3m37s with 79% of it in five copies of one test — slow enough that agents
# stopped running it between changes, which is how a stale recipe survived an
# afternoon. Memoising is safe: same inputs, same output, and the tests that
# matter still compare generator output against the committed recipe.
@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_PMV0TG", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_PMV0TG"] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.skipif(not RAW.exists(), reason="PMV0TG deposit not fetched (data/raw is gitignored)")
def test_the_recipe_is_exactly_what_the_generator_derives() -> None:
    gen = _generator()
    uk = gen.load_uk()
    wide = gen.build_wide(uk)
    generated_arms = gen.build_arms(wide)
    generated_outcomes = gen.build_outcomes()
    recipe = yaml.safe_load(RECIPE.read_text())
    assert generated_arms == recipe["condition"]["arms"], (
        "the recipe's arms and its generator have diverged — regenerate with "
        "`uv run python scripts/gen_PMV0TG.py --write`, and read the diff before accepting it"
    )
    assert generated_outcomes == recipe["outcomes"], (
        "the recipe's outcomes and its generator have diverged — regenerate with "
        "`uv run python scripts/gen_PMV0TG.py --write`"
    )


@pytest.mark.skipif(not RAW.exists(), reason="PMV0TG deposit not fetched")
def test_the_wide_csv_is_exactly_what_the_generator_derives() -> None:
    gen = _generator()
    uk = gen.load_uk()
    wide = gen.build_wide(uk)
    assert WIDE.exists(), "data/raw/PMV0TG/nbh_clean_conjoint_UK_wide.csv missing — run --write"
    on_disk = pd.read_csv(WIDE)
    pd.testing.assert_frame_equal(on_disk, wide)


@pytest.mark.skipif(not RAW.exists(), reason="PMV0TG deposit not fetched")
def test_uk_filter_and_structural_counts() -> None:
    """Pins the brief's own headline numbers, so a re-fetched deposit that
    drifts from them fails loudly rather than being assumed unchanged.
    `load_uk()` already asserts most of this internally; re-deriving the
    independent parts here (distinct arms, round count) means this test does
    not merely confirm the generator agrees with itself.
    """
    gen = _generator()
    uk = gen.load_uk()
    assert len(uk) == 18_640
    assert uk["id"].nunique() == 1_165
    assert (uk.groupby("id").size() == 16).all()

    wide = gen.build_wide(uk)
    assert len(wide) == 1_165

    arms = gen.build_arms(wide)
    assert len(arms) == 9_272  # 9,320 rounds, 48 coincidental repeats

    outcomes = gen.build_outcomes()
    assert len(outcomes) == 8


@pytest.mark.skipif(not RAW.exists(), reason="PMV0TG deposit not fetched")
def test_no_per_respondent_attribute_order_column_exists() -> None:
    """Regression pin for the brief's central warning: `EFXNLX`'s first recipe
    rendered a fixed canonical attribute order when the respondent's own
    on-screen order was randomised and recorded in a column
    (`list_table`) nobody checked for. This recipe's notes argue the opposite
    is true here — fixed order, no such column — ON THE EVIDENCE that the
    file's 21 columns are EXACTLY what `codebook.pdf` documents. Pin that
    evidence directly: if a re-fetched deposit ever gained a 22nd column, this
    fails and says so, rather than the claim quietly going stale the way
    `EFXNLX`'s did.
    """
    df = pd.read_csv(RAW, sep="\t", nrows=5)
    expected = {
        "id",
        "country",
        "age",
        "gender",
        "ideology",
        "ind_inc",
        "education",
        "hes_covid_2",
        "wtp_access",
        "wtp_private",
        "int_pol_implem_6",
        "weights",
        "person",
        "ans",
        "candidate",
        "vulnerability",
        "transmission",
        "income",
        "occupation",
        "age_category",
        "select",
    }
    assert set(df.columns) == expected, (
        f"column set changed: new={set(df.columns) - expected}, "
        f"missing={expected - set(df.columns)} — re-read the attribute-order "
        "evidence in recipes/PMV0TG.yaml's notes before assuming it still holds"
    )
