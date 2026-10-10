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


# --------------------------------------------------------------------------
# the persona and queue prompts, moved here from four scripts
# --------------------------------------------------------------------------


class PromptStub:
    """Answers every question with a fixed value, and records the whole call.

    These tests are mostly about the SHAPE of the call rather than the answer:
    that both questions are asked, that a label is shown its siblings, and that
    no respondent data goes with it. The prompts spent months living in scripts
    where nothing checked any of that.
    """

    def __init__(self, answers: dict[str, Any]) -> None:
        self.answers = answers
        self.states: list[str] = []
        self.questions: list[dict[str, Any]] = []

    def system_one(self, state: str, questions: dict[str, Any]) -> Any:
        self.states.append(state)
        self.questions.append(questions)
        return _Response({k: self.answers[k] for k in questions})


def _noul(value: float) -> Any:
    return type("N", (), {"noul": value})()


def _score(value: float, confidence: float) -> Any:
    return type("S", (), {"score": value, "confidence": confidence})()


def test_classifying_a_variable_asks_both_questions() -> None:
    """The Noul says how sure, the Choice says what it is instead.

    Both are needed: a regex proposed six vignette variables about a fictional
    character as 'income', and only the Choice had somewhere to put them.
    """
    stub = PromptStub(
        {
            "is_respondent_attribute": _noul(0.03),
            "kind": _Answer("vignette_or_scenario_attribute", 0.97, {}),
        }
    )
    reading = jev.classify_persona_variable(
        stub, "income", "A study", "- variable `V1`\n  label: her family depends on her income"
    )
    assert reading.is_attribute == 0.03
    assert reading.kind.value == "vignette_or_scenario_attribute"
    assert set(stub.questions[0]) == {"is_respondent_attribute", "kind"}
    # The option to decline must survive the move out of the script.
    assert "other" in stub.questions[0]["kind"].criteria


def test_a_category_is_judged_against_its_siblings() -> None:
    """Whether 'Other' is the catch-all depends entirely on what else was offered.

    So the full list goes in the state. A label judged alone cannot answer the
    question `categories.canonical` actually needs answered.
    """
    labels = ("White", "Black", "Other")
    stub = PromptStub({"concept": _Answer("other_residual", 0.9, {}), "is_residual": _noul(0.95)})
    reading = jev.category_concept(stub, "ethnicity", "Other", labels)
    assert reading.concept.value == "other_residual"
    assert reading.residual
    for sibling in labels:
        assert sibling in stub.states[0]


def test_a_category_below_the_residual_cut_is_not_the_catch_all() -> None:
    stub = PromptStub({"concept": _Answer("white", 0.99, {}), "is_residual": _noul(0.2)})
    assert not jev.category_concept(stub, "ethnicity", "White", ("White", "Other")).residual


def test_an_ordinal_label_is_asked_for_both_ends() -> None:
    """ "Bachelor's degree or higher" genuinely spans several rungs.

    Forcing it onto a single concept is what broke the categorical attempt, so
    the span is two questions and the answer is an interval.
    """
    stub = PromptStub(
        {"lowest": _Answer("bachelors", 0.9, {}), "highest": _Answer("postgraduate", 0.9, {})}
    )
    lo, hi = jev.ordinal_span(
        stub,
        "education",
        "Bachelor's degree or higher",
        ("High school", "Bachelor's degree or higher"),
    )
    assert (lo.value, hi.value) == ("bachelors", "postgraduate")
    # Only the ladder's rungs are offered — the residual and declined concepts
    # are not levels of education and must not be choosable as one.
    offered = set(stub.questions[0]["lowest"].criteria)
    assert offered == set(jev.PERSONA_LADDER["education"]) | {"none_of_these"}


def test_the_transfer_screen_returns_both_probabilities() -> None:
    stub = PromptStub(
        {"stimulus_is_us_specific": _noul(0.91), "outcome_needs_us_knowledge": _noul(0.12)}
    )
    assert jev.screen_uk_transfer(stub, "A study", "- Do you support the Patriot Act?") == (
        0.91,
        0.12,
    )


def test_priority_is_scored_not_asked_as_a_yes_no() -> None:
    """Ledger 72: a Noul is a yes/no probability, not a magnitude.

    Asked as Nouls these returned a tight high cluster that discriminated
    nothing. The rubrics are what make the Score mean something, so they travel
    with the prompt rather than staying behind in the script.
    """
    stub = PromptStub(
        {
            "uk_relevance": _score(3.8, 0.84),
            "evergreen": _score(0.39, 0.71),
            "domain": _Answer("health_and_care", 0.9, {}),
        }
    )
    reading = jev.score_uk_priority(stub, "A study", "- Would you take the vaccine?")
    assert (reading.relevance, reading.evergreen) == (3.8, 0.39)
    assert reading.domain.value == "health_and_care"
    assert len(stub.questions[0]["uk_relevance"].criteria) == 5
    assert len(stub.questions[0]["evergreen"].criteria) == 5


def test_a_shaky_priority_asks_for_review() -> None:
    stub = PromptStub(
        {
            "uk_relevance": _score(2.0, 0.55),
            "evergreen": _score(2.0, 0.9),
            "domain": _Answer("other", 0.9, {}),
        }
    )
    assert jev.score_uk_priority(stub, "t", "q").needs_review


def test_no_prompt_here_can_be_handed_a_dataframe() -> None:
    """The never-respondent-rows property, asserted structurally.

    Every function takes strings and label tuples. That is what makes "the
    instrument goes on the wire, the data does not" a fact about the signatures
    rather than a habit — and it has to survive prompts moving between files.
    """
    import inspect

    for name in (
        "classify_persona_variable",
        "category_concept",
        "ordinal_span",
        "screen_uk_transfer",
        "score_uk_priority",
        "screen_deposit",
        "categorise_experiment",
    ):
        params = list(inspect.signature(getattr(jev, name)).parameters.values())
        for p in params[1:]:  # the client itself is exempt
            assert p.annotation in (str, "str", tuple, "tuple[str, ...]"), (
                f"jev.{name} takes {p.name}: {p.annotation} — every argument after the "
                "client must be text or labels, never a dataframe"
            )


# --------------------------------------------------------------------------
# the Dataverse sweep and corpus overview prompts (moved here 2026-10-10)
# --------------------------------------------------------------------------


def _deposit(uk: _Answer, design: _Answer) -> tuple[PromptStub, jev.DepositReading]:
    stub = PromptStub({"uk_sample": uk, "design": design})
    reading = jev.screen_deposit(
        stub,
        title="Pay to pollute",
        description="Survey experiments with Britons",
        keywords="survey experiment",
        geography="United Kingdom",
        publication="BJPolS 2017",
        files="data.tab, questionnaire.pdf",
    )
    return stub, reading


def test_a_deposit_is_asked_both_questions_from_its_own_metadata() -> None:
    stub, reading = _deposit(
        _Answer("uk_only", 0.95, {"uk_only": 0.95}),
        _Answer("survey_experiment", 0.9, {"survey_experiment": 0.9}),
    )
    assert set(stub.questions[0]) == {"uk_sample", "design"}
    assert set(stub.questions[0]["uk_sample"].criteria) == set(jev.DEPOSIT_UK_SAMPLE)
    assert set(stub.questions[0]["design"].criteria) == set(jev.DEPOSIT_DESIGN)
    assert "Pay to pollute" in stub.states[0] and "questionnaire.pdf" in stub.states[0]
    assert (reading.uk_sample.value, reading.design.value) == ("uk_only", "survey_experiment")
    assert not reading.needs_review


def test_an_unsure_reading_on_either_question_asks_for_review() -> None:
    """One confident answer must not cover for an unsure one."""
    _, reading = _deposit(
        _Answer("uk_only", 0.95, {"uk_only": 0.95}),
        _Answer("conjoint", 0.40, {"conjoint": 0.40, "survey_experiment": 0.35}),
    )
    assert reading.needs_review


def test_a_category_can_always_be_none_of_these() -> None:
    """DEL's aid studies had no slot in the vocabulary: saying so must be possible."""
    stub = PromptStub({"category": _Answer(jev.NONE_OF_THESE, 0.8, {})})
    v = jev.categorise_experiment(stub, "Aid budget", "UK aid", ("health",), ("health messaging",))
    criteria = stub.questions[0]["category"].criteria
    assert jev.NONE_OF_THESE in criteria and criteria["health"] == "health messaging"
    assert v.value == jev.NONE_OF_THESE and v.needs_review


def test_categories_and_meanings_must_pair_up() -> None:
    with pytest.raises(ValueError):
        jev.categorise_experiment(PromptStub({}), "t", "d", ("a", "b"), ("only one",))
