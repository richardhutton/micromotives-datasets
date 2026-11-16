"""`recipes/3YCVOF.yaml` and its wide CSV must stay exactly what
`scripts/gen_3YCVOF.py` derives, and the profile template must reproduce the
fielded screen in the paper's Figure 1 word for word.

The template test needs no data, so it always runs. The others need the
deposit (gitignored) and R, so they skip without them.
"""

from __future__ import annotations

import functools
import importlib.util
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_3YCVOF.py"
RECIPE = REPO / "recipes" / "3YCVOF.yaml"
RDS = REPO / "data" / "raw" / "3YCVOF" / "study2data.rds"
WIDE = REPO / "data" / "raw" / "3YCVOF" / "study2_wide.csv"

needs_data = pytest.mark.skipif(
    not RDS.exists() or shutil.which("Rscript") is None,
    reason="3YCVOF deposit not fetched or R not installed",
)


@functools.cache
def _gen():
    spec = importlib.util.spec_from_file_location("gen_3YCVOF", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_3YCVOF"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _derived():
    gen = _gen()
    ds = gen.load()
    wide = gen.build_wide(ds)
    return ds, wide, gen.build_arms(wide, ds)


# Figure 1 (lower panel), author-accepted manuscript p.38, transcribed from the
# screenshot. Bold dropped, bullets as "- ".
FIGURE_1_MP1 = (
    "MP 1 has been a Conservative MP for 10 years\n"
    "- He spends on average 1 day of a 5-day week reviewing and working on national "
    "policies in Parliament, and\n"
    "- The remaining 4 days working on local constituency issues.\n"
    "- He rarely speaks out or votes against his party leadership."
)
FIGURE_1_MP2 = (
    "MP 2 has been a Labour MP for 21 years\n"
    "- She spends on average 4 days of a 5-day week reviewing and working on national "
    "policies in Parliament, and\n"
    "- The remaining 1 day working on local constituency issues.\n"
    "- She sometimes speaks out or votes against her party leadership."
)


def test_template_reproduces_figure_1() -> None:
    gen = _gen()
    mp1 = {"party": "Conservative", "tenure": "10", "sex": "male", "const": "4"}
    mp2 = {"party": "Labour", "tenure": "21", "sex": "female", "const": "1"}
    assert gen.render_profile(1, mp1 | {"rebellion": "rarely"}) == FIGURE_1_MP1
    assert gen.render_profile(2, mp2 | {"rebellion": "sometimes"}) == FIGURE_1_MP2


def test_template_rejects_a_swapped_day_count() -> None:
    """The constituency column is the CONSTITUENCY days; reading it as the
    national days would put 1 where Figure 1 shows 4. Must not match."""
    gen = _gen()
    swapped = {"party": "Conservative", "tenure": "10", "sex": "male", "const": "1"}
    assert gen.render_profile(1, swapped | {"rebellion": "rarely"}) != FIGURE_1_MP1


def test_shared_context_drops_sequence_and_mechanics() -> None:
    gen = _gen()
    assert "Comparison" not in gen.SHARED_CONTEXT
    assert "five" not in gen.SHARED_CONTEXT
    assert gen.SHARED_CONTEXT.startswith("People have different opinions")


def test_shared_context_says_the_listed_order_is_not_the_screen_order() -> None:
    """CONVENTIONS, choice sets randomised and not recorded (rich, 16 Nov 2026):
    the clause is the ruling's own words and closes the context, just before
    the two listed profiles."""
    gen = _gen()
    assert gen.SHARED_CONTEXT.endswith("\n\n(the options were shown in a random order)")


@needs_data
def test_recipe_is_exactly_what_the_generator_derives() -> None:
    gen = _gen()
    _ds, _wide, arms = _derived()
    recipe = yaml.safe_load(RECIPE.read_text())
    assert arms == recipe["condition"]["arms"], "regenerate: gen_3YCVOF.py --write"
    assert gen.build_outcomes() == recipe["outcomes"]
    assert recipe["condition"]["source_vars"] == gen.KEY_VARS
    assert recipe["condition"]["shared_context"] == gen.SHARED_CONTEXT


@needs_data
def test_wide_csv_is_exactly_what_the_generator_derives() -> None:
    _ds, wide, _arms = _derived()
    pd.testing.assert_frame_equal(pd.read_csv(WIDE), wide, check_dtype=False)


@needs_data
def test_structural_counts_and_reference_numbers() -> None:
    """1,899 respondents x 5 tasks; and the paper's headline AMCEs (p.21:
    rarely 13, sometimes 30, often 32 points over never) from the wide file."""
    _ds, wide, arms = _derived()
    assert len(wide) == 1_899
    assert len(arms) == 8_358
    chosen: dict[str, list[int]] = {}
    for t in range(1, 6):
        for side in (1, 2):
            for reb, ch in zip(wide[f"rebellion_{side}_t{t}"], wide[f"choice_t{t}"], strict=True):
                chosen.setdefault(str(reb), []).append(int(ch == side))
    ds = _derived()[0]
    rate = {ds.label("mp_rebellion", int(k)): sum(v) / len(v) for k, v in chosen.items()}
    amce = {k: round(100 * (rate[k] - rate["never"])) for k in ("rarely", "sometimes", "often")}
    assert amce == {"rarely": 13, "sometimes": 30, "often": 32}
