"""`recipes/EFXNLX.yaml` must stay exactly what its generator derives.

Same shape as `tests/test_gen_9xw67.py`: the recipe is machine-generated
(16,465 arms, one per distinct (respondent, pair) actually drawn), so the
judgement lives in `scripts/gen_EFXNLX.py` and this test is what stops the
recipe and the generator drifting apart silently.

The test needs the deposit, which is gitignored, so it skips when the data is
absent rather than failing on a fresh clone.
"""

from __future__ import annotations

import ast
import functools
import importlib.util
import random
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_EFXNLX.py"
RECIPE = REPO / "recipes" / "EFXNLX.yaml"
DATA = REPO / "data" / "raw" / "EFXNLX" / "LSEResults_Brexit_170428_client.sav"


# The expensive calls below are memoised for the session. `build_arms()` reads
# the deposit and re-derives every condition; the recipe is up to 57MB of YAML.
# Each test file called them 4-7 times, nothing cached, and the suite reached
# 3m37s with 79% of it in five copies of one test — slow enough that agents
# stopped running it between changes, which is how a stale recipe survived an
# afternoon. Memoising is safe: same inputs, same output, and the tests that
# matter still compare generator output against the committed recipe.
@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_EFXNLX", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_EFXNLX"] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.skipif(not DATA.exists(), reason="EFXNLX deposit not fetched (data/raw is gitignored)")
def test_the_recipe_is_exactly_what_the_generator_derives() -> None:
    gen = _generator()
    generated_arms = gen.build_arms()
    generated_outcomes = gen.build_outcomes()
    recipe = yaml.safe_load(RECIPE.read_text())
    assert generated_arms == recipe["condition"]["arms"], (
        "the recipe's arms and its generator have diverged — regenerate with "
        "`uv run python scripts/gen_EFXNLX.py --write`, and read the diff before accepting it"
    )
    assert generated_outcomes == recipe["outcomes"], (
        "the recipe's outcomes and its generator have diverged — regenerate with "
        "`uv run python scripts/gen_EFXNLX.py --write`"
    )


@pytest.mark.skipif(not DATA.exists(), reason="EFXNLX deposit not fetched")
def test_every_pair_instance_is_distinct() -> None:
    """The design that lets position (pair 1 vs 2-5) determine the preamble
    with no item-level override: verified once here, not just asserted in
    the recipe's notes. If a re-fetched deposit ever contained two different
    (respondent, pair) instances with the identical 16-attribute tuple drawn
    at DIFFERENT pair positions, the generator's single `arm.text` per tuple
    would render the wrong preamble for whichever position lost the race —
    silently, since nothing else would change. This pins the count so that
    stops being invisible.
    """
    arms = _generator().build_arms()
    assert len(arms) == 16_465

    raw_tuples = [tuple(a["raw_values"][k] for k in _generator().KEY_VARS) for a in arms]
    assert len(set(raw_tuples)) == len(raw_tuples), (
        "two distinct arms share an identical 16-attribute tuple — the "
        "position-dependent preamble is no longer safe without an item-level "
        "condition_text override; re-read the maker's report before changing "
        "this design"
    )


@pytest.mark.skipif(not DATA.exists(), reason="EFXNLX deposit not fetched")
def test_outcome_counts_match_the_deposit_s_own_assertions() -> None:
    """16,465 pair-level / 32,930 profile-level, hard-asserted by
    `analysis-conjoint-cleaning.R`'s own `stopifnot`.
    """
    outcomes = _generator().build_outcomes()
    assert len(outcomes) == 15  # 5 pairs x (choice, acceptability-A, acceptability-B)


@pytest.mark.skipif(not DATA.exists(), reason="EFXNLX deposit not fetched")
def test_attribute_rows_render_in_this_respondents_own_list_table_order() -> None:
    """Defect (SEVERE, found by a checker): the generator used to render every
    arm's 8 attribute rows in one fixed canonical order, regardless of
    `list_table` — this respondent's OWN on-screen shuffle, drawn once before
    pair 1 and reused unchanged for pairs 2-5 (questionnaire.docx line 168).
    `list_table` is non-null for all 3,293 respondents and ZERO of them drew
    the canonical [1,2,3,4,5,6,7,8] order, so every one of the 16,465
    conditions previously stated a sequence nobody saw.

    This pins the fix against the SOURCE directly (re-deriving the expected
    order from `list_table` independently of `_attribute_order`, so a bug
    shared between the test and the generator can't hide), not merely against
    `--check` agreeing with the recipe, which would pass whatever order both
    files happened to agree on.
    """
    gen = _generator()
    ds = gen.spss.read(DATA)
    arms = gen.build_arms()
    arms_by_raw = {tuple(sorted(a["raw_values"].items())): a for a in arms}

    row_label = {a: ds.column_labels[f"{a}_seen1_t1"] for a in gen.ATTRS}
    canonical_labels = [row_label[a] for a in gen.ATTRS]

    rng = random.Random(0)
    sample = rng.sample(range(len(ds.df)), 30)

    checked = 0
    saw_noncanonical = 0
    for i in sample:
        row = ds.df.iloc[i]
        # Independent re-derivation of the expected order, straight from
        # `list_table`'s own semantics (questionnaire.docx: `row{p}_1 =
        # col_1[list_table[p-1]-1]`) -- deliberately NOT calling
        # `gen._attribute_order` here, so this test cannot pass merely
        # because it shares a bug with the function it is checking.
        order = ast.literal_eval(row["list_table"])
        assert sorted(order) == list(range(1, 9))
        expected_labels = [row_label[gen.ATTRS[slot - 1]] for slot in order]

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

            lines = [ln for ln in arm["text"].split("\n") if ln.startswith("- ")]
            assert len(lines) == 16, "expected 8 lines for Outcome A + 8 for Outcome B"
            outcome_a_labels = [ln[2:].split(":", 1)[0] for ln in lines[:8]]
            outcome_b_labels = [ln[2:].split(":", 1)[0] for ln in lines[8:]]

            assert outcome_a_labels == expected_labels, (
                f"condition_num={arm['condition_num']}: Outcome A attribute order does not "
                f"match this respondent's own list_table={row['list_table']!r}"
            )
            assert outcome_b_labels == expected_labels, (
                f"condition_num={arm['condition_num']}: Outcome B attribute order does not "
                f"match this respondent's own list_table={row['list_table']!r}"
            )

            # The canonical order must appear for no respondent who did not
            # actually draw it -- the exact assertion that was false under the
            # old fixed-canonical-order rendering (0 of 3,293 respondents).
            if order == list(range(1, 9)):
                assert outcome_a_labels == canonical_labels
            else:
                saw_noncanonical += 1
                assert outcome_a_labels != canonical_labels

    assert checked >= 25, f"sample only matched {checked} arms -- test is not exercising enough"
    assert saw_noncanonical >= 20, "sample drew suspiciously many canonical orders"
