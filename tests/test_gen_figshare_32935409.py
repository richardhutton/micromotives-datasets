"""The figshare_32935409 recipe (academic-integrity MaxDiff) and its checks.

The generator reads every item text and order from the questionnaire PDF and every
pick from the deposit's long file; these tests stop a hand edit drifting from it,
and check the facts the rows rest on:

- the recipe and the derived data file are what the generator writes;
- the stem, footnote, item texts and version 1's screen order are the PDF's, and
  the PDF check fails when any of them is changed;
- every arm's two questions enumerate exactly that arm's four items, in order;
- every built answer points at the item the deposit says was picked (the wide
  `serimost{t}` / `serileast{t}` columns, read independently of the melt);
- the "Least Serious" pick depends on stored position, the evidence that stored
  order is screen order, and that dependence vanishes when positions are shuffled;
- no published reference exists (the paper could not be found), so the ranking is
  checked only for face validity against the deposit's own "should result in
  disciplinary action" grid. A ranking cannot see display order (ledger: EFXNLX).

Tests needing the gitignored deposit, the build, or `pdftotext` skip without them.
"""

from __future__ import annotations

import importlib.util
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_figshare_32935409.py"
RECIPE = REPO / "recipes" / "figshare_32935409_maxdiff.yaml"
BUILT = REPO / "data" / "processed" / "figshare_32935409_maxdiff.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_figshare_32935409", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.CSV.exists(), reason="figshare_32935409 not fetched")
needs_pdf = pytest.mark.skipif(
    not (gen.PDF.exists() and shutil.which("pdftotext")), reason="questionnaire PDF or pdftotext"
)
needs_built = pytest.mark.skipif(
    not (BUILT.exists() and gen.CSV.exists()), reason="figshare_32935409 not built"
)


@needs_raw
def test_recipe_and_derived_file_are_what_the_generator_writes() -> None:
    wide = gen.derive(gen.load())
    assert RECIPE.read_text() == gen.render(wide)
    on_disk = pd.read_csv(gen.DERIVED)
    assert on_disk.equals(pd.read_csv(pd.io.common.StringIO(wide.to_csv(index=False))))


@needs_pdf
def test_wording_and_version_1_order_are_the_pdfs() -> None:
    gen.instrument()


@needs_pdf
@pytest.mark.parametrize("mutation", ["text", "order", "stem", "definition"])
def test_the_pdf_check_fails_when_the_instrument_is_changed(
    mutation: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    if mutation == "text":
        items = dict(gen.ITEMS)
        items[8] = ("Taking an exam for someone else", items[8][1])
        monkeypatch.setattr(gen, "ITEMS", items)
    elif mutation == "order":
        v1 = list(gen.PDF_VERSION_1)
        v1[0] = (10, 20, 19, 3)
        monkeypatch.setattr(gen, "PDF_VERSION_1", v1)
    elif mutation == "stem":
        monkeypatch.setattr(gen, "STEM", gen.STEM.replace("4 behaviours", "four behaviours"))
    else:
        monkeypatch.setattr(gen, "DEFINITION", gen.DEFINITION.replace("honesty, ", ""))
    with pytest.raises(AssertionError):
        gen.instrument()


def test_items_are_20_distinct_texts_and_slugs() -> None:
    assert sorted(gen.ITEMS) == list(range(1, 21))
    assert len({t for t, _ in gen.ITEMS.values()}) == 20
    assert len({s for _, s in gen.ITEMS.values()}) == 20
    # Version 1 shows every item exactly twice, as every version does.
    assert sorted(c for s in gen.PDF_VERSION_1 for c in s) == sorted(list(range(1, 21)) * 2)


def test_each_arm_enumerates_its_own_items_in_screen_order() -> None:
    rec = load(RECIPE)
    by_slug = {slug: text for text, slug in gen.ITEMS.values()}
    assert len(rec.condition.arms) == 500
    for arm in rec.condition.arms:
        items = [by_slug[arm.factors[f"item_{k}"]] for k in range(1, 5)]
        assert arm.text == gen.arm_text(items)
        assert arm.items, arm.condition_num
        for task, ov in arm.items.items():
            which = gen.MOST if task % 2 == 0 else gen.LEAST
            assert ov.outcome_question == gen.arm_question(which, items)
        assert "of 10)" not in arm.text


@needs_built
def test_every_built_answer_is_the_item_the_deposit_says_was_picked() -> None:
    rows = pd.read_parquet(
        BUILT, columns=["participant_id", "factors", "task_num", "response_num", "outcome"]
    )
    assert len(rows) == 9_340 and rows["participant_id"].nunique() == 467
    assert not rows["outcome"].str.contains(r"\[").any()
    raw = gen.load()
    people = raw[raw["n"] == "1"].set_index("id")
    slug = {code: s for code, (_, s) in gen.ITEMS.items()}
    checked = 0
    for pid, factors, task, resp in zip(
        rows["participant_id"], rows["factors"], rows["task_num"], rows["response_num"], strict=True
    ):
        t, which = task // 2 + 1, ("serimost" if task % 2 == 0 else "serileast")
        picked = int(people.loc[pid.removeprefix("figshare_32935409:"), f"{which}{t}"])
        assert factors[f"item_{int(resp)}"] == slug[picked], (pid, task)
        checked += 1
    assert checked == 9_340


def _least_chi2(wide: pd.DataFrame, shuffle: np.random.Generator | None = None) -> float:
    counts: Counter[int] = Counter()
    for t in range(1, gen.N_TASKS + 1):
        for pos in wide[f"least_{t}"]:
            counts[int(shuffle.integers(1, 5)) if shuffle is not None else int(pos)] += 1
    n = sum(counts.values())
    return float(sum((counts[k] - n / 4) ** 2 / (n / 4) for k in range(1, 5)))


@needs_raw
def test_least_serious_pick_depends_on_stored_position() -> None:
    # Every item sits in every position 214-254 times, so with display order
    # unrelated to stored order the picks would spread evenly over positions.
    # Measured 13.0 (1,224 / 1,150 / 1,074 / 1,222); chi-square, 3 df, 5% = 7.81.
    wide = pd.read_csv(gen.DERIVED)
    assert _least_chi2(wide) > 7.81
    # The same statistic with positions drawn at random does not reach it.
    assert _least_chi2(wide, np.random.default_rng(0)) < 7.81


@needs_built
def test_ranking_has_face_validity_against_the_should_be_disciplined_grid() -> None:
    rows = pd.read_parquet(BUILT, columns=["factors", "task_num", "response_num"])
    shown: Counter[str] = Counter()
    net: Counter[str] = Counter()
    for factors, task, resp in zip(
        rows["factors"], rows["task_num"], rows["response_num"], strict=True
    ):
        slugs = [factors[f"item_{k}"] for k in range(1, 5)]
        if task % 2 == 0:
            shown.update(slugs)
        net[slugs[int(resp) - 1]] += 1 if task % 2 == 0 else -1
    bw = pd.Series({s: net[s] / shown[s] for s in shown})
    raw = gen.load()
    people = raw[raw["n"] == "1"]
    should = pd.Series(
        {s: (people[f"threshshd_r{c}"] == "1").mean() for c, (_, s) in gen.ITEMS.items()}
    )
    # Measured 0.949. Not an alignment test (picks are stored as codes, so none is
    # inferred) and blind to display order; it catches a melt that scrambles picks.
    assert bw.corr(should, method="spearman") > 0.9
    assert bw.idxmax() == "exam_impersonation" and bw.idxmin() == "chatgpt_ideas"
