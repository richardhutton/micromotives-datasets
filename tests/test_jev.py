"""The Jev layer's own logic, tested offline with a stub client.

Only the parts that are OURS: paging, run-offs, confidence handling, review
flags. The model's judgement is measured by `scripts/jev_probe.py` and
`scripts/jev_calibration.py` against studies built by hand — a unit test cannot
and should not try.

Both bugs tested below were real and both were in code I wrote today. The second
is the more instructive: the fix for the first introduced it, and it was worse,
because an over-confident wrong answer survives review and an empty one does not.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from micromotives_datasets import jev


@dataclass
class _Response:
    answers: dict[str, _Answer]


@dataclass
class _Answer:
    choice: str
    confidence: float
    probabilities: dict[str, float]


class StubClient:
    """Answers from a fixed preference order, and records what it was asked.

    `oversized` reproduces the measured failure: a call offering more than
    `limit` options does not error, it quietly answers NONE_OF_THESE.
    """

    def __init__(self, prefer: list[str], *, limit: int | None = None) -> None:
        self.prefer = prefer
        self.limit = limit
        self.asked: list[list[str]] = []

    def system_one(self, state: str, questions: dict[str, Any]) -> Any:
        criteria = list(next(iter(questions.values())).criteria)
        offered = [c for c in criteria if c != jev.NONE_OF_THESE]
        self.asked.append(offered)
        if self.limit is not None and len(criteria) > self.limit:
            chosen, probs = jev.NONE_OF_THESE, {jev.NONE_OF_THESE: 1.0}
        else:
            ranked = [p for p in self.prefer if p in offered]
            if not ranked:
                chosen, probs = jev.NONE_OF_THESE, {jev.NONE_OF_THESE: 1.0}
            else:
                chosen = ranked[0]
                # Two near-equal rivals when both are present, so a close call
                # stays a close call.
                probs = (
                    {ranked[0]: 0.52, ranked[1]: 0.46}
                    if len(ranked) > 1
                    else {ranked[0]: 1.0, jev.NONE_OF_THESE: 0.0}
                )

        return _Response({next(iter(questions)): _Answer(chosen, max(probs.values()), probs)})


def _candidates(n: int, *, extra: list[str] | None = None) -> dict[str, str]:
    out = {f"VAR{i:03}": f"filler variable {i}" for i in range(n)}
    for name in extra or []:
        out[name] = f"the {name} variable"
    return out


def test_a_small_list_is_asked_in_one_call() -> None:
    cli = StubClient(["AGE"])
    v = jev.choose(cli, "s", "which is age?", _candidates(10, extra=["AGE"]), "none")
    assert v.value == "AGE"
    assert len(cli.asked) == 1


def test_a_large_list_is_paged_rather_than_truncated() -> None:
    """The bug: 57 candidates answered correctly, 150 returned NONE for everything.

    An oversized call does not error, it quietly answers "none of the above" —
    the worst failure for a prep tool, because an empty report reads exactly
    like a clean one.
    """
    cands = _candidates(145, extra=["AGE"])
    cli = StubClient(["AGE"], limit=jev.MAX_OPTIONS + 1)
    v = jev.choose(cli, "s", "which is age?", cands, "none")
    assert v.value == "AGE", "paging failed to find a candidate past the page limit"
    assert all(len(a) <= jev.MAX_OPTIONS for a in cli.asked), "a page exceeded the limit"
    assert len(cli.asked) > 1


def test_a_rival_that_is_only_runner_up_on_its_page_still_reaches_the_runoff() -> None:
    """The bug the first fix introduced, which was worse than the bug it fixed.

    Carrying only each page's WINNER forward drops a candidate that lost its own
    page to something else — so it is never compared against the eventual
    answer at all. Measured on `9xw67`: winner-only paging reported `REGION4` at
    confidence 1.00 where a single-page call put it at 0.52 against `REGION9`'s
    0.46. The close call is the true answer and the one a human must make.

    Two earlier versions of this test could not tell the bug from the fix. The
    first put both rivals in the same page, so they met whatever the paging did.
    The second put one rival per page, so each won its own page and both came
    forward anyway. The failure needs a rival that is beaten ON ITS PAGE.
    """
    cands: dict[str, str] = {}
    for i in range(jev.MAX_OPTIONS * 2):
        if i == 2:
            cands["REGION4"] = "census region, 4 categories"
        elif i == jev.MAX_OPTIONS + 3:
            cands["DECOY"] = "something more appealing on page two"
            cands["REGION9"] = "census division, 9 categories"
        cands[f"VAR{i:03}"] = f"filler variable {i}"

    pages = [list(cands)[i : i + jev.MAX_OPTIONS] for i in range(0, len(cands), jev.MAX_OPTIONS)]
    page_of = {n: i for i, pg in enumerate(pages) for n in pg}
    assert page_of["REGION4"] != page_of["REGION9"], "rivals must start on different pages"
    assert page_of["DECOY"] == page_of["REGION9"], "the decoy must beat REGION9 on its own page"

    # Preference order: REGION4 wins page one; DECOY beats REGION9 on page two,
    # so REGION9 survives only if runners-up are carried forward.
    cli = StubClient(["REGION4", "DECOY", "REGION9"], limit=jev.MAX_OPTIONS + 1)
    jev.choose(cli, "s", "which is region?", cands, "none")
    assert "REGION9" in set(cli.asked[-1]), (
        "REGION9 lost its own page and was never compared against the answer"
    )


def test_a_lone_survivor_is_never_asked_as_a_one_option_question() -> None:
    """A Choice with one option cannot answer anything else, and says 1.00.

    Narrow option lists inflating confidence is a failure this project has
    already paid for, so a sole survivor keeps the confidence it earned on its
    own page instead of being handed a fresh certainty.
    """
    cands = _candidates(100, extra=["AGE"])
    cli = StubClient(["AGE"], limit=jev.MAX_OPTIONS + 1)
    jev.choose(cli, "s", "which is age?", cands, "none")
    assert all(len(a) > 1 for a in cli.asked), f"asked a one-option question: {cli.asked}"


def test_nothing_anywhere_means_none_rather_than_a_guess() -> None:
    cli = StubClient([], limit=jev.MAX_OPTIONS + 1)
    v = jev.choose(cli, "s", "which is age?", _candidates(100), "none")
    assert v.value == jev.NONE_OF_THESE
    assert v.needs_review


def test_none_of_these_always_needs_review() -> None:
    assert jev.Verdict(value=jev.NONE_OF_THESE, confidence=1.0).needs_review


def test_describe_variable_sends_labels_and_never_data() -> None:
    """The wire rule, made structural: these take labels, not a dataframe."""
    line = jev.describe_variable("XTESS193", "Experimental condition", {1.0: "Vignette1 first"})
    assert "XTESS193" in line and "Vignette1 first" in line
    assert "values:" in line, "value labels are what disambiguate a mislabelled variable"


# --------------------------------------------------------------------------
# the condition screen
# --------------------------------------------------------------------------


class ScreenStub:
    """Answers `screen_condition` from a probability distribution it is handed.

    Records the `state` so a test can assert what crossed the wire, and what the
    frame told the model — the frame is not cosmetic here: a wrong one measurably
    inverted `sh4px`'s result (the corrected condition scored worse than the
    defective one), so it is worth a test of its own.
    """

    def __init__(self, probabilities: dict[str, float]) -> None:
        self.probabilities = probabilities
        self.states: list[str] = []

    def system_one(self, state: str, questions: dict[str, Any]) -> Any:
        self.states.append(state)
        chosen = max(self.probabilities, key=lambda k: self.probabilities[k])
        return _Response(
            {"defect": _Answer(chosen, self.probabilities[chosen], self.probabilities)}
        )


def _screen(probs: dict[str, float]) -> jev.ConditionFlag:
    return jev.screen_condition(
        ScreenStub(probs), "A company formed a team of six.", "How diverse is it?"
    )


def test_a_truthful_condition_is_not_flagged() -> None:
    f = _screen({"none": 0.9, "premature_treatment": 0.1})
    assert not f.needs_review
    assert f.defect_mass == pytest.approx(0.1)


def test_a_named_defect_class_is_flagged() -> None:
    f = _screen({"sequence_signposting": 0.7, "none": 0.3})
    assert f.needs_review
    assert "sequence_signposting" in f.render()


def test_defect_mass_is_summed_over_the_whole_distribution() -> None:
    """A defect split across several classes must not vanish from the signal.

    `Verdict.runners_up` keeps only the top three, so reading the mass off it
    would drop the fourth class — and a defect the model cannot settle on a name
    for is precisely when it is least certain and most worth a human. Here "none"
    wins the vote at 0.28 while 0.72 of the mass says something is wrong.
    """
    f = _screen(
        {
            "none": 0.28,
            "sequence_signposting": 0.18,
            "premature_treatment": 0.18,
            "reveals_the_experiment": 0.18,
            "truncated_text": 0.18,
        }
    )
    assert f.defect.value == "none", "the chosen label is still the plurality"
    assert f.defect_mass == pytest.approx(0.72)
    assert f.needs_review, "a split defect outvoted by 'none' must still be flagged"


def test_a_clean_label_below_the_threshold_passes() -> None:
    """The calibration, pinned: 0.35 was my guess and would have fired here.

    `relig_truncated_text`'s CORRECTED text measured 0.32. A threshold at 0.35
    sat 0.03 from flagging a correction; the measured gap put it at 0.45.
    """
    f = _screen({"none": 0.68, "truncated_text": 0.32})
    assert not f.needs_review
    assert f.defect_mass < jev.DEFECT_MASS_REVIEW


def test_the_frame_says_experiment_condition_and_reconstruction() -> None:
    """All three, because the first version of this frame said none of them.

    It claimed "a survey respondent was shown the following text". They were not
    shown it — it is second-person prose we compose afterwards from the
    questionnaire — and calling it a survey hid that one condition of a
    randomised experiment is what is being judged.
    """
    cli = ScreenStub({"none": 1.0})
    jev.screen_condition(cli, "THE CONDITION", "THE OUTCOME", study="s")
    state = cli.states[0].lower()
    assert "experiment" in state
    assert "condition" in state
    assert "reconstruction" in state
    assert "not a transcript" in state
    assert state.index("the condition") < state.index("the outcome")


def test_the_screen_sends_only_instrument_text() -> None:
    """Structural: the signature takes two strings, so no row can reach Jev."""
    cli = ScreenStub({"none": 1.0})
    jev.screen_condition(cli, "THE CONDITION", "THE OUTCOME")
    assert "THE CONDITION" in cli.states[0] and "THE OUTCOME" in cli.states[0]
