"""The zenodo6572717 recipe (CUPID, parents choosing a health service) and its answer key.

The generator reads which services each task showed from the authors' attribute dummies,
every answer from the raw choice text, and the wording from the survey document; these
tests stop a hand edit drifting from it, and check the facts the rows rest on:

- the recipe and the derived long file are what the generator writes;
- task 1 is the paper's Figure 1 (a screenshot of a fielded screen), and every quoted
  word is in the survey document;
- every built row's condition is its own task's two services, A then B, and the built
  answers per task are the raw answers of the 450 kept parents;
- the built rows reproduce the paper's Table 3 conditional logit (Nicholson et al.,
  Health Expectations 26(5), 2023, 1931-1940): all nine coefficients, their odds
  ratios, the log likelihood and N. Swapping Service A and B, or the response codes,
  breaks it.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_zenodo6572717.py"
RECIPE = REPO / "recipes" / "zenodo6572717.yaml"
BUILT = REPO / "data" / "processed" / "zenodo6572717.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_zenodo6572717", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.DTA.exists(), reason="zenodo6572717 deposit not fetched")
needs_built = pytest.mark.skipif(
    not (BUILT.exists() and gen.DTA.exists()), reason="zenodo6572717 not built"
)

# Table 3, conditional logit: beta and odds ratio per term, as printed.
TABLE_3 = {
    "same_day": (0.935, 2.548),
    "next_day": (0.609, 1.839),
    "nine_to_five": (0.264, 1.301),
    "evening_weekend": (0.305, 1.357),
    "any_doctor_or_nurse": (0.152, 1.165),
    "own_gp": (0.502, 1.653),
    "telephone_advice": (0.237, 1.267),
    "cost": (-0.015, 0.985),
    "asc": (0.157, 1.170),
}
TABLE_3_LL = -3537
TABLE_3_N = 10_800  # alternatives: 450 parents x 12 tasks x 2

DUMMY_TERMS = {
    "wait": ("same_day", "next_day"),
    "appointment": ("nine_to_five", "evening_weekend"),
    "advice": ("telephone_advice",),
    "who": ("any_doctor_or_nurse", "own_gp"),
}


@needs_raw
def test_recipe_is_what_the_generator_writes() -> None:
    assert RECIPE.read_text() == gen.render()


@needs_raw
def test_derived_file_is_what_the_generator_writes() -> None:
    on_disk = pd.read_csv(gen.DATA)
    fresh = gen.prep()
    assert list(on_disk.columns) == list(fresh.columns)
    for col in fresh.columns:
        assert on_disk[col].astype(str).tolist() == fresh[col].astype(str).tolist(), col


@needs_raw
def test_task_1_is_the_papers_figure_1() -> None:
    a, b = gen.design()[1]
    for side, shown in zip((a, b), gen.FIGURE_1, strict=True):
        assert tuple(gen.ATTRIBUTES[k][1][side[k]] for k in gen.ATTRIBUTES) == shown


@needs_raw
def test_every_quoted_word_is_in_the_survey_document() -> None:
    gen.check_wording()


@needs_raw
def test_twelve_tasks_each_and_the_two_blocks_are_disjoint() -> None:
    coded = pd.read_csv(gen.DATA)
    per_person = coded.groupby("pid")["task"].apply(lambda s: tuple(sorted(s)))
    assert set(per_person) == {tuple(range(1, 13)), tuple(range(13, 25))}
    assert len(per_person) == gen.N_KEPT


def test_each_level_text_is_distinct_and_the_template_places_every_attribute() -> None:
    rec = load(RECIPE)
    tpl = rec.condition.template
    assert tpl is not None and tpl.sparse
    for dim in tpl.dimensions.values():
        texts = [lv.text for lv in dim.levels.values()]
        assert len(set(texts)) == len(texts)
    text = tpl.text
    assert text.index("Service A") < text.index("{wait_A}") < text.index("{cost_A}")
    assert text.index("{cost_A}") < text.index("Service B") < text.index("{wait_B}")


def _built() -> pd.DataFrame:
    return pd.read_parquet(BUILT)


def _task_of(design: dict[int, Any]) -> dict[tuple[tuple[str, str], ...], int]:
    out = {}
    for k, (a, b) in design.items():
        key = {f"{attr}_A": a[attr] for attr in gen.ATTRIBUTES}
        key |= {f"{attr}_B": b[attr] for attr in gen.ATTRIBUTES}
        out[tuple(sorted(key.items()))] = k
    return out


@needs_built
def test_each_row_shows_its_own_task_and_carries_its_raw_answer() -> None:
    design = gen.design()
    task_of = _task_of(design)
    built = _built()
    assert len(built) == gen.N_KEPT * gen.PER_BLOCK
    built["task"] = [task_of[tuple(sorted(f.items()))] for f in built["factors"]]
    for k, group in built.groupby("task"):
        a, b = design[k]
        assert set(group["condition"]) == {gen.arm_text(a, b)}
    # The answers per task are the raw choice text of the kept parents.
    df = gen.read_dta()
    keep = ~df["newid"].isin(gen.excluded(df))
    people = df[keep].drop_duplicates("newid")
    for k in range(1, gen.N_TASKS + 1):
        raw = Counter(people[f"choicetask_{k:02d}"])
        raw.pop("", None)
        got = Counter(built.loc[built["task"] == k, "response"])
        assert got == {"1": raw["Service A"], "2": raw["Service B"]}, k


def _fit(built: pd.DataFrame, swap: bool = False) -> tuple[dict[str, float], float]:
    """Binary logit of choosing A on (A - B) attributes plus an ASC: a two-alternative
    conditional logit, which is what Table 3 estimates."""
    cols = [t for terms in DUMMY_TERMS.values() for t in terms] + ["cost", "asc"]
    cost = {"eur_0": 0, "eur_15": 15, "eur_30": 30, "eur_45": 45}
    rows, y = [], []
    for f, resp in zip(built["factors"], built["response"], strict=True):
        diff = []
        for attr, terms in DUMMY_TERMS.items():
            for t in terms:
                diff.append(float(f[f"{attr}_A"] == t) - float(f[f"{attr}_B"] == t))
        diff.append(cost[f["cost_A"]] - cost[f["cost_B"]])
        diff.append(1.0)
        if swap:
            diff = [-d for d in diff[:-1]] + [1.0]
        rows.append(diff)
        y.append(1.0 if resp == "1" else 0.0)
    z, yy = np.array(rows), np.array(y)
    beta = np.zeros(z.shape[1])
    for _ in range(50):
        p = 1 / (1 + np.exp(-z @ beta))
        beta += np.linalg.solve((z * (p * (1 - p))[:, None]).T @ z, z.T @ (yy - p))
    p = 1 / (1 + np.exp(-z @ beta))
    ll = float(np.sum(yy * np.log(p) + (1 - yy) * np.log(1 - p)))
    return dict(zip(cols, beta.tolist(), strict=True)), ll


@needs_built
def test_built_rows_reproduce_table_3() -> None:
    built = _built()
    assert len(built) * 2 == TABLE_3_N
    beta, ll = _fit(built)
    for term, (b, odds) in TABLE_3.items():
        # Printed to three decimals; own GP's 0.502 is truncated (its OR 1.653 is e^0.5026).
        assert abs(beta[term] - b) <= 0.001, (term, beta[term])
        assert abs(math.exp(beta[term]) - odds) <= 0.0015, (term, math.exp(beta[term]))
    assert round(ll) == TABLE_3_LL


@needs_built
def test_swapping_the_services_or_the_answers_breaks_table_3() -> None:
    built = _built()
    swapped, _ = _fit(built, swap=True)
    assert abs(swapped["same_day"] - TABLE_3["same_day"][0]) > 0.5
    flipped = built.assign(response=built["response"].map({"1": "2", "2": "1"}))
    beta, _ = _fit(flipped)
    assert abs(beta["same_day"] - TABLE_3["same_day"][0]) > 0.5
