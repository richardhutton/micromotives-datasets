"""`_branch` in `scripts/derive_LOGVPZ_risk.py` must mean what the authors' do-file means.

LOGVPZ's risk-tolerance outcome is the only outcome in the corpus that we COMPUTE
rather than read. Every other `response` is a column the respondent's own answer
landed in; this one is a 0-3 code derived from a branching pair of questions, and
the derivation is ours. That makes a swapped branch the single most damaging error
available in this study: the code would still be 0-3, every count would still be
8,075, QC would still pass, `verify_LOGVPZ.py` would still reproduce the control
mean (2.332 is a mean over a SYMMETRIC-ish distribution — swapping 1 and 2 moves
it by hundredths), and the only trace would be that the most risk-tolerant
respondents were labelled the least.

So the branch gets pinned here, as a table, transcribed one line at a time from
`data/raw/LOGVPZ/1-master.do` lines 409-417 — which is the authors' own code, not
our reading of their prose:

    gen     risk = 0 if expRiskIncomeW19 == 2 & expRiskIncomeaW19 == 2
    replace risk = 1 if expRiskIncomeW19 == 2 & expRiskIncomeaW19 == 1
    replace risk = 2 if expRiskIncomeW19 == 1 & expRiskIncomebW19 == 2
    replace risk = 3 if expRiskIncomeW19 == 1 & expRiskIncomebW19 == 1

The direction matters and is easy to get backwards, so it is stated once here in
words: in this instrument **1 = No and 2 = Yes**, and the SCALE runs from 0 = most
willing to take risks (accepted both gambles) to 3 = least willing (declined
both). Base Yes therefore routes to the `a` follow-up and the low codes; base No
routes to `b` and the high codes.

Unlike the generator tests in this directory, nothing here reads the deposit, so
none of it skips on a fresh clone. The whole point is that the branch semantics
stay checked on a machine that has no access to the data at all.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
DERIVE = REPO / "scripts" / "derive_LOGVPZ_risk.py"


def _module():
    spec = importlib.util.spec_from_file_location("derive_LOGVPZ_risk", DERIVE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["derive_LOGVPZ_risk"] = module
    spec.loader.exec_module(module)
    return module


# (base, a, b) -> expected code. `None` marks the follow-up that was NOT asked
# on that branch, which the deposit records as missing; the test passes NaN for
# it, so a `_branch` that read the wrong follow-up would see NaN and fall
# through to the no-resolution case rather than quietly returning a number.
AUTHORS_TABLE = [
    (2, 2, None, 0.0),
    (2, 1, None, 1.0),
    (1, None, 2, 2.0),
    (1, None, 1, 3.0),
]


@pytest.mark.parametrize(("base", "a", "b", "expected"), AUTHORS_TABLE)
def test_the_branch_is_the_authors_branch(
    base: int, a: int | None, b: int | None, expected: float
) -> None:
    """Each of the four do-file lines, one test case each."""
    branch = _module()._branch
    got = branch(
        float(base),
        math.nan if a is None else float(a),
        math.nan if b is None else float(b),
    )
    assert got == expected, (
        f"base={base} a={a} b={b} should be {expected} per 1-master.do:409-417, got {got}"
    )


def test_the_scale_runs_from_most_to_least_risk_tolerant() -> None:
    """The DIRECTION, stated independently of the table above.

    Both assertions below are implied by `AUTHORS_TABLE`, deliberately. A
    swap of two rows in that table is a one-character edit that still looks
    like a table; it would have to also survive this, which is written in the
    vocabulary of the thing being measured rather than of the source columns.
    And the recipe's `min_label`/`max_label` make exactly this claim to every
    consumer of the data, so if it is wrong, it is wrong in prose we ship.
    """
    branch = _module()._branch
    accepted_everything = branch(2.0, 2.0, math.nan)
    declined_everything = branch(1.0, math.nan, 1.0)
    assert accepted_everything == 0.0, "accepting both gambles is the MOST risk-tolerant end (0)"
    assert declined_everything == 3.0, "declining both gambles is the LEAST risk-tolerant end (3)"
    assert accepted_everything < declined_everything


def test_an_unresolved_branch_is_missing_rather_than_a_number() -> None:
    """No partial answer may become a risk code.

    A respondent who answered the base question and then dropped out has no
    position on this scale. Returning 0 (falsy, plausible, in range) for them
    would silently pile every dropout onto the most-risk-tolerant end. `_verify`
    in the script catches this in aggregate on the real file; this catches it
    per respondent, and on a machine with no file.
    """
    branch = _module()._branch
    unresolved = [
        (2.0, math.nan, math.nan),  # said Yes, never answered the `a` follow-up
        (1.0, math.nan, math.nan),  # said No, never answered the `b` follow-up
        (math.nan, 2.0, math.nan),  # follow-up without a base answer
        (math.nan, math.nan, math.nan),  # answered nothing
        (2.0, 9.0, math.nan),  # `a` holds the don't-know code, not an answer
        (1.0, math.nan, 9.0),  # `b` holds the don't-know code
        (2.0, math.nan, 2.0),  # said Yes but only `b` is populated — cannot happen
        (1.0, 2.0, math.nan),  # said No but only `a` is populated — cannot happen
    ]
    for base, a, b in unresolved:
        got = branch(base, a, b)
        assert math.isnan(got), f"base={base} a={a} b={b} must not resolve, got {got}"


def test_the_branch_reads_only_the_follow_up_its_base_answer_routed_to() -> None:
    """The `a` and `b` columns are not interchangeable.

    If `_branch` ever consulted both follow-ups, a respondent whose two columns
    disagreed would get a code anyway. The deposit has no such respondent today,
    so only this test would notice — and the next wave of a BES panel is exactly
    where one would appear.
    """
    branch = _module()._branch
    # Base Yes: `b` is irrelevant and must not change the answer, whatever it holds.
    assert branch(2.0, 2.0, 1.0) == branch(2.0, 2.0, 2.0) == branch(2.0, 2.0, math.nan) == 0.0
    # Base No: `a` is irrelevant in the same way.
    assert branch(1.0, 1.0, 2.0) == branch(1.0, 2.0, 2.0) == branch(1.0, math.nan, 2.0) == 2.0


def test_every_resolvable_input_is_covered_by_the_authors_table() -> None:
    """Exhaust the instrument's own code space: nothing outside the table resolves.

    The three columns each take 1, 2, a don't-know 9, or missing. That is 64
    combinations, small enough to enumerate rather than argue about — so this is
    the whole truth table, not a sample of it. Any future edit that makes a
    fifth input resolve to a code has to come here and say so.
    """
    branch = _module()._branch
    codes = [1.0, 2.0, 9.0, math.nan]
    expected = {
        (2.0, 2.0): 0.0,
        (2.0, 1.0): 1.0,
        (1.0, 2.0): 2.0,
        (1.0, 1.0): 3.0,
    }
    resolved = 0
    for base in codes:
        for a in codes:
            for b in codes:
                got = branch(base, a, b)
                follow_up = a if base == 2.0 else b
                want = expected.get((base, follow_up))
                if want is None:
                    assert math.isnan(got), f"({base}, {a}, {b}) resolved to {got}"
                else:
                    assert got == want, f"({base}, {a}, {b}) gave {got}, want {want}"
                    resolved += 1
    # 4 resolving (base, follow-up) pairs x 4 values of the unread column.
    assert resolved == 16, f"expected 16 of 64 inputs to resolve, {resolved} did"
