"""The osf_ct8ae recipe (Schwartz values best-worst) and its checks.

- the recipe and the derived data file are what the generator writes;
- every pick is a member of the set shown, exactly one of each, and Most != Least;
- every arm lists its own values with the not-recorded clause, and each outcome's
  scale matches its set's size;
- every built answer points at the value the export's own button columns mark,
  read independently of the derived file;
- the item-label set 5 screen error is rendered and flagged, and nowhere else;
- the paper's numbers are reproduced (Benevolence 0.375, Power -0.46, Table 1's
  top five, test-retest tau 0.82 / 0.41), and coding Most and Least the other way
  round breaks them. A score cannot see display order (ledger: EFXNLX).

Tests needing the gitignored deposit or the build skip without them.
"""

from __future__ import annotations

import importlib.util
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest
from scipy.stats import kendalltau

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_osf_ct8ae.py"
RECIPE = REPO / "recipes" / "osf_ct8ae_maxdiff.yaml"
BUILT = REPO / "data" / "processed" / "osf_ct8ae_maxdiff.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_osf_ct8ae", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.EXPORT.exists(), reason="osf_ct8ae not fetched")
needs_built = pytest.mark.skipif(
    not (BUILT.exists() and gen.EXPORT.exists()), reason="osf_ct8ae not built"
)


@needs_raw
def test_recipe_and_derived_file_are_what_the_generator_writes() -> None:
    wide = gen.derive()
    assert RECIPE.read_text() == gen.render(wide)
    assert gen._same_csv(wide)


@needs_raw
def test_identifying_columns_are_blanked_on_read() -> None:
    head, _, data = gen.read_export()
    for name in gen.DROP:
        i = head.index(name)
        assert all(row[i] == "" for row in data), name
    wide = pd.read_csv(gen.DERIVED, dtype=str)
    assert not wide.apply(lambda c: c.str.contains("@", na=False)).any().any()


@needs_raw
def test_every_pick_is_one_of_the_set_and_most_is_not_least() -> None:
    people = gen.screens()
    assert len(people) == 100
    n = 0
    for p in people.values():
        assert len(p["occasions"]) == 2
        for _, sets in p["occasions"]:
            assert len(sets) == 11
            for codes, most, least in sets:
                assert len(codes) in (5, 6) and len(set(codes)) == len(codes)
                assert 1 <= most <= len(codes) and 1 <= least <= len(codes)
                assert most != least
                n += 1
    assert n == 2_200
    wide = pd.read_csv(gen.DERIVED)
    for t, size in enumerate(gen.set_sizes(), 1):
        assert wide[f"most_{t}"].between(1, size).all()
        assert wide[f"least_{t}"].between(1, size).all()
        assert (wide[f"most_{t}"] != wide[f"least_{t}"]).all()
        assert (wide[f"item_{t}_6"] == 0).all() == (size == 5)


def test_each_arm_lists_its_own_values_with_the_clause() -> None:
    rec = load(RECIPE)
    assert len(rec.condition.arms) == 22
    slugs = {v[3]: c for c, v in gen.VALUES.items()}
    for arm in rec.condition.arms:
        label = 1 if arm.factors["label_type"] == "dimensions" else 2
        codes = [slugs[s] for s in arm.factors["options"].split("|")]
        items = [gen.text_of(c, label) for c in codes]
        assert arm.text.endswith("\n".join(items) + "\n" + gen.CLAUSE)
        assert "Step 1 of 1" not in arm.text and "second phase" not in arm.text
        assert arm.items
        for task, ov in arm.items.items():
            t = task // 2 + 1
            which = gen.MOST if task % 2 == 0 else gen.LEAST
            assert ov.outcome_question == gen.arm_question(which, items, gen.stem_for(label, t))
    sizes = {o.task_num: o.scale.max for o in rec.outcomes}
    for arm in rec.condition.arms:
        for task in arm.items:
            assert sizes[task] == len(arm.factors["options"].split("|"))


def test_the_screen_error_is_flagged_on_its_arm_alone() -> None:
    rec = load(RECIPE)
    flagged = [a for a in rec.condition.arms if "MOST and MOST" in a.text]
    assert len(flagged) == 1
    arm = flagged[0]
    assert arm.factors["label_type"] == "items" and set(arm.items) == {8, 9}
    assert gen.ERROR_CLAUSE in arm.text
    assert all(gen.ERROR_CLAUSE in ov.outcome_question for ov in arm.items.values())


@needs_built
def test_every_built_answer_is_the_value_the_export_marks() -> None:
    rows = pd.read_parquet(BUILT, columns=["participant_id", "factors", "task_num", "response_num"])
    assert len(rows) == 2_200 and rows["participant_id"].nunique() == 100
    # Read straight from the export's button columns, not from the derived file.
    head, sub, data = gen.read_export()
    qs = gen.questions(head, sub)
    kept = {int(p.split(":")[1]) for p in rows["participant_id"]}
    seg = {n: gen.SEGMENTS[data[n - 1][8]][0] for n in kept}
    slug = {c: v[3] for c, v in gen.VALUES.items()}
    for pid, factors, task, resp in zip(
        rows["participant_id"], rows["factors"], rows["task_num"], rows["response_num"], strict=True
    ):
        n = int(pid.split(":")[1])
        t = task // 2 + 1
        least_cols, most_cols, codes, _ = qs[(seg[n] - 1) * 11 + t - 1]
        cols = most_cols if task % 2 == 0 else least_cols
        marked = [codes[i] for i, c in enumerate(cols) if data[n - 1][c] == "1"]
        assert len(marked) == 1
        assert factors["options"].split("|")[int(resp) - 1] == slug[marked[0]], (pid, task)


def _scores(swap: bool = False) -> tuple[dict[str, float], float, float]:
    """Mean BWS score per value over both occasions, and mean tau-b same / changed."""
    names = {c: v[0] for c, v in gen.VALUES.items()}
    per: list[dict[str, float]] = []
    same: list[float] = []
    changed: list[float] = []
    for p in gen.screens().values():
        occ = []
        for _, sets in p["occasions"]:
            net: Counter[str] = Counter()
            shown: Counter[str] = Counter()
            for codes, most, least in sets:
                if swap:
                    most, least = least, most
                shown.update(names[c] for c in codes)
                net[names[codes[most - 1]]] += 1
                net[names[codes[least - 1]]] -= 1
            occ.append({v: net[v] / shown[v] for v in shown})
        per += occ
        keys = sorted(occ[0])
        tau = kendalltau([occ[0][k] for k in keys], [occ[1][k] for k in keys]).statistic
        (same if p["condition"] in ("dimension-dimension", "item-item") else changed).append(tau)
    means = {v: float(np.mean([s[v] for s in per])) for v in per[0]}
    return means, float(np.mean(same)), float(np.mean(changed))


@needs_raw
def test_reproduces_the_papers_scores_and_reliability() -> None:
    means, same, changed = _scores()
    # Paper, Exp. 1b: Benevolence M = 0.375, Power M = -0.46 (Results, p. 11).
    assert round(means["Benevolence"], 3) == 0.375
    assert round(means["Power"], 2) == -0.46
    top = sorted(means, key=lambda v: -means[v])
    # Table 1's order: Benevolence, Self-direction, Achievement, Security, Universalism.
    assert top[:5] == ["Benevolence", "Self-Direction", "Achievement", "Security", "Universalism"]
    assert top[-1] == "Power"
    # Same labels 0.82, changed labels 0.41 (p. 14).
    assert round(same, 2) == 0.82 and round(changed, 2) == 0.41


@needs_raw
def test_most_and_least_the_other_way_round_breaks_the_reference() -> None:
    means, _, _ = _scores(swap=True)
    assert round(means["Benevolence"], 3) != 0.375
    assert max(means, key=lambda v: means[v]) == "Power"
