"""`recipes/RJTVG8.yaml` and its derived wide CSV must stay exactly what
`scripts/gen_RJTVG8.py` derives.

Same shape as `tests/test_gen_PMV0TG.py`: the recipe's `condition.arms` and
`outcomes` are machine-generated (6,000 arms, one per distinct 20-attribute
(Policy A, Policy B) pair actually drawn across 6,000 tasks — zero
collisions), so the judgement lives in the generator and this test is what
stops the recipe and the generator drifting apart silently. It also pins the
derived `data/raw/RJTVG8/evoting_UK_wide.csv`, since that file carries
judgement too (the reshape, the persona text resolution, the non-answer
sentinel handling) and is not itself reviewable the way the recipe YAML is.

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
GEN = REPO / "scripts" / "gen_RJTVG8.py"
RECIPE = REPO / "recipes" / "RJTVG8.yaml"
RAW = REPO / "data" / "raw" / "RJTVG8" / "evoting_replicationfile.dta"
WIDE = REPO / "data" / "raw" / "RJTVG8" / "evoting_UK_wide.csv"


# Memoised for the session — same reasoning as test_gen_PMV0TG.py /
# test_gen_EFXNLX.py: `build_arms()` re-derives all 6,000 conditions and the
# recipe is multi-megabyte YAML, so repeating this across several tests
# without caching made the earlier suites slow enough that a stale recipe
# survived an afternoon.
@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_RJTVG8", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_RJTVG8"] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.skipif(not RAW.exists(), reason="RJTVG8 deposit not fetched (data/raw is gitignored)")
def test_the_recipe_is_exactly_what_the_generator_derives() -> None:
    gen = _generator()
    df, levels, persona_levels = gen.load()
    wide = gen.build_wide(df, persona_levels)
    generated_arms = gen.build_arms(wide, levels)
    generated_outcomes = gen.build_outcomes()
    recipe = yaml.safe_load(RECIPE.read_text())
    assert generated_arms == recipe["condition"]["arms"], (
        "the recipe's arms and its generator have diverged — regenerate with "
        "`uv run python scripts/gen_RJTVG8.py --write`, and read the diff before accepting it"
    )
    assert generated_outcomes == recipe["outcomes"], (
        "the recipe's outcomes and its generator have diverged — regenerate with "
        "`uv run python scripts/gen_RJTVG8.py --write`"
    )


@pytest.mark.skipif(not RAW.exists(), reason="RJTVG8 deposit not fetched")
def test_the_wide_csv_is_exactly_what_the_generator_derives() -> None:
    gen = _generator()
    df, _levels, persona_levels = gen.load()
    wide = gen.build_wide(df, persona_levels)
    assert WIDE.exists(), "data/raw/RJTVG8/evoting_UK_wide.csv missing — run --write"
    on_disk = pd.read_csv(WIDE)
    pd.testing.assert_frame_equal(on_disk, wide, check_dtype=False)


@pytest.mark.skipif(not RAW.exists(), reason="RJTVG8 deposit not fetched")
def test_structural_counts() -> None:
    """Pins the brief's own headline numbers, so a re-fetched deposit that
    drifts from them fails loudly rather than being assumed unchanged.
    `load()` already asserts most of this internally; re-deriving the
    independent parts here (distinct arms, task count) means this test does
    not merely confirm the generator agrees with itself.
    """
    gen = _generator()
    df, levels, persona_levels = gen.load()
    assert len(df) == 12_000
    assert df["IDvar"].nunique() == 1_200
    assert (df.groupby("IDvar").size() == 10).all()
    assert sorted(df["task"].unique()) == [1, 2, 3, 4, 5]

    wide = gen.build_wide(df, persona_levels)
    assert len(wide) == 1_200

    arms = gen.build_arms(wide, levels)
    assert len(arms) == 6_000  # 6,000 task-instances, ZERO coincidental repeats

    outcomes = gen.build_outcomes()
    assert len(outcomes) == 5


@pytest.mark.skipif(not RAW.exists(), reason="RJTVG8 deposit not fetched")
def test_every_task_instance_is_distinct() -> None:
    """Unlike PMV0TG (48 coincidental repeats) and EFXNLX (where a repeat
    would have been a defect), RJTVG8 has zero: every one of the 6,000
    (respondent, task) instances draws a distinct 20-attribute tuple. Pinned
    directly so a re-fetched deposit that ever produces a collision is
    noticed — this design's dedup-by-tuple approach is documented as safe
    BECAUSE there is no position-dependent text (see the recipe's notes), but
    if that assumption needs revisiting a collision should say so loudly.
    """
    gen = _generator()
    df, levels, persona_levels = gen.load()
    wide = gen.build_wide(df, persona_levels)
    arms = gen.build_arms(wide, levels)
    raw_tuples = [tuple(a["raw_values"][k] for k in gen.KEY_VARS) for a in arms]
    assert len(raw_tuples) == 6_000
    assert len(set(raw_tuples)) == 6_000


@pytest.mark.skipif(not RAW.exists(), reason="RJTVG8 deposit not fetched")
def test_no_per_respondent_attribute_order_column_exists() -> None:
    """Regression pin for the brief's central warning: `EFXNLX`'s first recipe
    rendered a fixed canonical attribute order when the respondent's own
    on-screen order was randomised and recorded in a column nobody checked
    for. This recipe's notes state the WEAKER form of evidence applies here
    (no order column, one screenshot, no second cross-check) and deliberately
    does NOT declare `condition.line_order_vars`. Pin the absence directly:
    if a re-fetched deposit ever gained a 71st column, this fails and says
    so, rather than the claim quietly going stale.
    """
    import pyreadstat

    _df, meta = pyreadstat.read_dta(str(RAW))
    expected = {
        "IDvar",
        "task",
        "profile",
        "selected",
        "choice",
        "StartDate",
        "EndDate",
        "Durationinseconds",
        "consent",
        *[f"onlineactivity_{i}" for i in range(1, 11)],
        "perceive_fraud",
        "perceive_elecsat",
        "internetsat",
        "turnout",
        "votemethod",
        "education",
        "edmean",
        "degree",
        "child",
        "sex",
        "noncis",
        "queer",
        "ethnic",
        "nonwhite",
        "income",
        "incomemean",
        "income2",
        "voteleave",
        "vote2019",
        "votemain",
        "votetory",
        "ideo",
        "prereg_num",
        "prereg",
        "fraud_num",
        "fraud",
        "method_num",
        "method",
        "vwindow_num",
        "vwindow",
        "trials_num",
        "trials",
        "pilot_num",
        "pilot",
        "platform_num",
        "platform",
        "private",
        "cost_num",
        "cost",
        "party_num",
        "party",
        "endorse_num",
        "endorse",
        "probselected",
        "trustworthy",
        "trustbin",
        "satisfied_internet",
        "satisfied_elections",
        "viewsfraud",
        "trustnormal",
        "probnormal",
    }
    actual = set(meta.column_names)
    assert actual == expected, (
        f"column set changed: new={actual - expected}, missing={expected - actual} — "
        "re-read the attribute-order evidence in recipes/RJTVG8.yaml's notes before "
        "assuming it still holds"
    )
    assert len(expected) == 70


@pytest.mark.skipif(not RAW.exists(), reason="RJTVG8 deposit not fetched")
def test_platform_num_is_a_bijection_of_platform_and_private() -> None:
    """The brief's named riskiest judgement, pinned directly against the raw
    deposit rather than merely asserted in prose: `platform_num` (1-6) is
    rendered as ONE attribute in this recipe. This test independently
    verifies the claim that makes that safe — every `platform_num` code maps
    to exactly one (platform, private) pair and vice versa, i.e. the split
    representation the authors use for their marginal-means tables is a
    lossless re-encoding of the single randomised draw, not a separate
    manipulation.
    """
    gen = _generator()
    df, _levels, _persona_levels = gen.load()
    pairs = df.groupby("platform_num")[["platform", "private"]].agg(lambda s: tuple(sorted(set(s))))
    assert (pairs["platform"].map(len) == 1).all()
    assert (pairs["private"].map(len) == 1).all()
    combos = df[["platform", "private"]].drop_duplicates()
    assert len(combos) == 6
    assert df["platform_num"].nunique() == 6


@pytest.mark.skipif(not RAW.exists(), reason="RJTVG8 deposit not fetched")
def test_persona_resolves_to_text_not_raw_codes() -> None:
    """Regression pin for a defect this build caught by reading a built row,
    not by QC (which only WARNED): the wide CSV must carry resolved persona
    TEXT ("Man", "White", "Graduate degree ...") rather than the .dta's raw
    numeric codes ("1", "0", "4"). A first version of `build_wide` wrote the
    raw codes through unchanged, relying on `persona_label_rewrite` to
    resolve them at `mmds build` time — but `data_file` is the derived CSV,
    read via `sources.delimited`, which returns empty `value_labels` by
    construction, so the rewrite never had the original .dta's dictionary to
    draw from and every persona field silently rendered as a bare digit.
    """
    gen = _generator()
    df, _levels, persona_levels = gen.load()
    wide = gen.build_wide(df, persona_levels)
    for col in gen.PERSONA_COLS:
        non_null = wide[col].dropna()
        assert not non_null.empty, f"{col}: all-null, cannot check"
        assert non_null.map(lambda v: not str(v).strip("-").isdigit()).all(), (
            f"{col}: some values look like raw numeric codes, not resolved text: "
            f"{non_null[non_null.map(lambda v: str(v).strip('-').isdigit())].unique()[:5]}"
        )
    # And the two education non-answer codes are genuinely absent, not labelled.
    assert "DATA EXPIRED" not in wide["education"].dropna().unique()
    assert "Don't know / not applicable" not in wide["education"].dropna().unique()
