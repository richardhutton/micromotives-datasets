"""`recipes/35M5CV_lodger.yaml` must stay exactly what its generator derives.

Same shape as `tests/test_gen_EFXNLX.py`: the recipe is machine-generated
(8,345 arms, one per distinct (respondent, pair) actually drawn), so the
judgement lives in `scripts/gen_35M5CV_lodger.py` and this test is what stops
the recipe and the generator drifting apart silently.

The test needs the deposit, which is gitignored, so it skips when the data is
absent rather than failing on a fresh clone.
"""

from __future__ import annotations

import ast
import functools
import importlib.util
import random
import re
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_35M5CV_lodger.py"
RECIPE = REPO / "recipes" / "35M5CV_lodger.yaml"
DATA = REPO / "data" / "raw" / "35M5CV" / "lodger-data-raw.sav"


# The expensive calls below are memoised for the session. `build_arms()` reads
# the deposit and re-derives every condition; the recipe is up to 57MB of YAML.
# Each test file called them 4-7 times, nothing cached, and the suite reached
# 3m37s with 79% of it in five copies of one test — slow enough that agents
# stopped running it between changes, which is how a stale recipe survived an
# afternoon. Memoising is safe: same inputs, same output, and the tests that
# matter still compare generator output against the committed recipe.
@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_35M5CV_lodger", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_35M5CV_lodger"] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.skipif(not DATA.exists(), reason="35M5CV deposit not fetched (data/raw is gitignored)")
def test_the_recipe_is_exactly_what_the_generator_derives() -> None:
    gen = _generator()
    generated_arms = gen.build_arms()
    generated_outcomes = gen.build_outcomes()
    recipe = yaml.safe_load(RECIPE.read_text())
    assert generated_arms == recipe["condition"]["arms"], (
        "the recipe's arms and its generator have diverged — regenerate with "
        "`uv run python scripts/gen_35M5CV_lodger.py --write`, and read the diff before "
        "accepting it"
    )
    assert generated_outcomes == recipe["outcomes"], (
        "the recipe's outcomes and its generator have diverged — regenerate with "
        "`uv run python scripts/gen_35M5CV_lodger.py --write`"
    )


@pytest.mark.skipif(not DATA.exists(), reason="35M5CV deposit not fetched")
def test_every_pair_instance_is_distinct() -> None:
    """Pins the exact arm count (8,345 = 1,669 respondents x 5 pairs) and
    confirms there are zero collisions in the 14-attribute tuple, which is
    what makes the per-arm `response_recode` (see next test) and the
    position-dependent preamble safe without an item-level override.
    """
    gen = _generator()
    arms = gen.build_arms()
    assert len(arms) == 8_345

    raw_tuples = [tuple(a["raw_values"][k] for k in gen.KEY_VARS) for a in arms]
    assert len(set(raw_tuples)) == len(raw_tuples), (
        "two distinct arms share an identical 14-attribute tuple — the per-arm "
        "response_recode and the shared preamble are no longer safe without an "
        "item-level override"
    )


@pytest.mark.skipif(not DATA.exists(), reason="35M5CV deposit not fetched")
def test_outcome_counts_match_the_deposit_s_own_assertions() -> None:
    """5 pairs x 1 outcome each (QPAIRt) — unlike EFXNLX, there is no second,
    per-profile outcome variable here (see the generator's module docstring).
    """
    outcomes = _generator().build_outcomes()
    assert len(outcomes) == 5


@pytest.mark.skipif(not DATA.exists(), reason="35M5CV deposit not fetched")
def test_response_recode_names_the_two_profiles_shown() -> None:
    """Every arm's `response_recode` must map EXACTLY the two name codes this
    arm actually drew (name_seen1_tN -> 1, name_seen2_tN -> 2), independently
    re-derived from `raw_values` here rather than trusting the generator's own
    bookkeeping. This is the mechanism that resolves ledger-brief trap #1:
    `QPAIRt` stores WHICH NAME was picked, not which screen position.
    """
    gen = _generator()
    arms = gen.build_arms()
    rng = random.Random(0)
    for arm in rng.sample(arms, 200):
        name1 = arm["raw_values"]["name_seen1_t1"]
        name2 = arm["raw_values"]["name_seen2_t1"]
        assert name1 != name2
        assert arm["response_recode"] == {name1: 1, name2: 2}


@pytest.mark.skipif(not DATA.exists(), reason="35M5CV deposit not fetched")
def test_attribute_rows_render_in_this_respondents_own_list_table_order() -> None:
    """Pins the fix against the SOURCE directly (re-deriving the expected
    order from `list_table` independently of `gen._attribute_order`), exactly
    as `test_gen_EFXNLX.py` does — the EFXNLX recipe once shipped 16,465
    conditions in a fixed canonical order no respondent had actually seen,
    and that defect's fingerprint (a `list_table`-shaped column, checked for
    and found) is the whole reason this generator resolves order per arm
    from the start.
    """
    gen = _generator()
    ds = gen.spss.read(DATA)
    value_labels = {a: dict(ds.value_labels[f"{a}_seen1_t1"]) for a in gen.SHUFFLED_ATTRS}
    arms = gen.build_arms()
    arms_by_raw = {tuple(sorted(a["raw_values"].items())): a for a in arms}

    rng = random.Random(0)
    sample = rng.sample(range(len(ds.df)), 30)

    checked = 0
    saw_noncanonical = 0
    for i in sample:
        row = ds.df.iloc[i]
        order = ast.literal_eval(row["list_table"])
        assert sorted(order) == list(range(1, 7))
        expected_attrs = [gen.SHUFFLED_ATTRS[slot - 1] for slot in order]

        for t in range(1, 6):
            cols = gen._condition_vars(t)
            raw_codes = [row[c] for c in cols]
            if any(c is None or c != c for c in raw_codes):  # NaN
                continue
            codes = [int(float(c)) for c in raw_codes]
            raw_values = dict(zip(gen.KEY_VARS, codes, strict=True))
            arm = arms_by_raw.get(tuple(sorted(raw_values.items())))
            if arm is None:
                continue
            checked += 1

            # The text is "...preamble paragraphs...\n\n<block A>\n\n<block B>" —
            # split on blank lines and take the last two paragraphs, which are
            # exactly the two profile blocks regardless of how many paragraphs
            # the (constant) preamble itself contains.
            paragraphs = arm["text"].split("\n\n")
            block_a_text, block_b_text = paragraphs[-2], paragraphs[-1]
            a_lines = [ln for ln in block_a_text.split("\n") if ln.startswith("- ")]
            b_lines = [ln for ln in block_b_text.split("\n") if ln.startswith("- ")]
            assert len(a_lines) == 6 and len(b_lines) == 6

            expected_values_a = [
                value_labels[a][raw_values[f"{a}_seen1_t1"]] for a in expected_attrs
            ]
            got_values_a = [ln[2:] for ln in a_lines]
            assert got_values_a == expected_values_a, (
                f"condition_num={arm['condition_num']}: attribute order does not match "
                f"this respondent's own list_table={row['list_table']!r}"
            )

            canonical_values_a = [
                value_labels[a][raw_values[f"{a}_seen1_t1"]] for a in gen.SHUFFLED_ATTRS
            ]
            if order == list(range(1, 7)):
                assert got_values_a == canonical_values_a
            else:
                saw_noncanonical += 1
                assert got_values_a != canonical_values_a

    assert checked >= 20, f"sample only matched {checked} arms — test is not exercising enough"
    assert saw_noncanonical >= 15, "sample drew suspiciously many canonical orders"


@pytest.mark.skipif(not DATA.exists(), reason="35M5CV deposit not fetched")
def test_no_attribute_label_is_rendered() -> None:
    """The fielded table's left-hand label column is wrapped in an HTML
    comment (`<!--th>$row1_1</th-->`) in every pair, in both studies — the
    respondent saw bare values, never a label like "Age:" or "Politics:".
    Guards against silently reintroducing a label prefix that would be
    stimulus text no respondent read.
    """
    gen = _generator()
    arms = gen.build_arms()
    label_prefix = re.compile(r"^- (Age|Occupation|Volunteering|Politics|EU|Hobby)\s*:", re.I)
    rng = random.Random(0)
    for arm in rng.sample(arms, 200):
        for line in arm["text"].split("\n"):
            if line.startswith("- "):
                assert not label_prefix.match(line), f"label leaked into rendered line: {line!r}"
