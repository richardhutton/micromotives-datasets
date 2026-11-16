"""The zenodo18547379 recipe (meat-reduction MaxDiff) and its answer key.

The generator reads every item text, pick and follow-up from the deposit's CSV;
these tests stop a hand edit drifting from it, and check the facts the rows rest
on:

- the recipe and the derived data file are what the generator writes;
- the stem and follow-up wording are the codebook's (Qualtrics' own header row);
- every arm's two pick questions enumerate exactly that arm's four items, in its
  slot order, and no row reaches the bracketed fallback;
- the built rows reproduce the paper's overall ranking of the 25 items (McBey et
  al., Food Quality and Preference 135, 2026, 105693, Appendix 3) from
  best-minus-worst scores, and pairing the picks with the slots any other way
  does markedly worse. That is the test of the riskiest mechanical step: pick
  column k belongs to item slot k.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import itertools
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_zenodo18547379.py"
RECIPE = REPO / "recipes" / "zenodo18547379_maxdiff.yaml"
RAW = REPO / "data" / "raw" / "zenodo18547379"
BUILT = REPO / "data" / "processed" / "zenodo18547379_maxdiff.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_zenodo18547379", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.CSV.exists(), reason="zenodo18547379 deposit not fetched")
needs_built = pytest.mark.skipif(
    not (BUILT.exists() and gen.CSV.exists()), reason="zenodo18547379 not built"
)

# Appendix 3, "Overall Rank" column, top to bottom, in the data's own wording
# (the paper prints "15 %", "curly quotes round factory farmed" and a single space in "Receiving a
# flyer"; typography only).
PAPER_RANK = [
    "lower_price",
    "more_appealing",
    "greater_variety",
    "cheaper_than_meat",
    "cheaper_than_now",
    "free_samples",
    "more_veg_options",
    "meat_tax_15pc",
    "ready_meals",
    "meat_free_days",
    "label_unhealthy",
    "cooking_classes",
    "shopping_lists",
    "staff_recommend",
    "label_factory_farmed",
    "next_to_meat",
    "app",
    "livestock_life",
    "label_environment",
    "no_meat_canteen",
    "tv_programme",
    "website",
    "flyer",
    "text_messages",
    "celebrity",
]


@needs_raw
def test_recipe_and_derived_file_are_what_the_generator_writes() -> None:
    wide = gen.derive(gen.load())
    assert RECIPE.read_text() == gen.render(wide)
    on_disk = pd.read_csv(gen.DERIVED)
    assert on_disk.equals(pd.read_csv(pd.io.common.StringIO(wide.to_csv(index=False))))


@needs_raw
def test_wording_is_the_codebooks() -> None:
    # `stem()` asserts the stem against all 40 pick columns and the follow-up
    # against all ten follow-up columns.
    assert gen.stem() == gen.STEM
    rec = load(RECIPE)
    follow = [o for o in rec.outcomes if o.task_num % 3 == 2]
    assert len(follow) == 10 and all(o.question == gen.FOLLOW_UP for o in follow)


def test_slugs_cover_25_distinct_items() -> None:
    assert len(gen.SLUGS) == 25 and len(set(gen.SLUGS.values())) == 25
    assert set(PAPER_RANK) == set(gen.SLUGS.values())


def test_each_arm_enumerates_its_own_items_in_slot_order() -> None:
    rec = load(RECIPE)
    by_slug = {slug: gen.shown(text) for text, slug in gen.SLUGS.items()}
    for arm in rec.condition.arms:
        items = [by_slug[arm.factors[f"item_{k}"]] for k in range(1, 5)]
        assert arm.text == gen.STEM + "\n" + "\n".join(items)
        assert arm.items, arm.condition_num
        for task, ov in arm.items.items():
            which = gen.MOST if task % 3 == 0 else gen.LEAST
            assert task % 3 in (0, 1)
            assert ov.outcome_question == gen.arm_question(which, items)
        # Neither question names the other column's pick: both columns are named
        # only as labels, never with an answer.
        assert "(t/10)" not in arm.text and "/10)" not in arm.text


@needs_built
def test_no_row_carries_the_fallback_question() -> None:
    rows = pd.read_parquet(BUILT, columns=["outcome", "condition"])
    assert len(rows) == 45_270
    assert not rows["outcome"].str.contains(r"\[").any()
    assert not rows["condition"].str.contains(r"\[").any()


def _scores(rows: pd.DataFrame, perm: tuple[int, ...]) -> dict[str, float]:
    """Best-minus-worst per appearance, reading response r as slot perm[r-1]."""
    shown: Counter[str] = Counter()
    net: Counter[str] = Counter()
    for factors, task, response in zip(
        rows["factors"], rows["task_num"], rows["response_num"], strict=True
    ):
        if task % 3 == 2:
            continue
        slugs = [factors[f"item_{k}"] for k in range(1, 5)]
        if task % 3 == 0:
            for s in slugs:
                shown[s] += 1
        picked = slugs[perm[int(response) - 1] - 1]
        net[picked] += 1 if task % 3 == 0 else -1
    return {s: net[s] / shown[s] for s in shown}


def _spearman(scores: dict[str, float]) -> float:
    ours = pd.Series({s: -scores[s] for s in PAPER_RANK}).rank()
    paper = pd.Series({s: i for i, s in enumerate(PAPER_RANK)}).rank()
    return float(ours.corr(paper))


@needs_built
def test_built_rows_reproduce_the_papers_ranking_and_no_other_alignment_does() -> None:
    rows = pd.read_parquet(BUILT, columns=["factors", "task_num", "response_num"])
    identity = _spearman(_scores(rows, (1, 2, 3, 4)))
    # 0.996 measured: three adjacent swaps between items whose scores differ by
    # 0.004 or less; the paper ranks by conditional logit, we by counts.
    assert identity > 0.99, identity
    others = [
        _spearman(_scores(rows, perm))
        for perm in itertools.permutations((1, 2, 3, 4))
        if perm != (1, 2, 3, 4)
    ]
    # The nearest rival (0.964) keeps two of the four slots right.
    assert max(others) < identity - 0.02, max(others)
    # A pairing that gets every slot wrong is far off.
    derangements = [
        _spearman(_scores(rows, p))
        for p in itertools.permutations((1, 2, 3, 4))
        if all(p[i] != i + 1 for i in range(4))
    ]
    assert max(derangements) < 0.5, derangements
