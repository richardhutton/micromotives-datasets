"""The Jev layer: the semantic judgements, in one place with one set of rules.

Jev (the `typesafe-sdk` package) answers the questions that need reading
comprehension. Before this module those questions were asked in eight separate
scripts, each with its own prompt, its own threshold and its own idea of what
goes on the wire — so a lesson learned in one did not reach the others. Three
times running, a mistake was fixed in one script and left standing in another.

**The division of labour**, settled by measurement and recorded in CLAUDE.md:
Jev answers *what is this variable* and *what does this label mean*; code
answers *do these bands tile*. Code can be unit-tested and a judgement cannot,
so anything decidable by arithmetic or parsing stays in code.

**The pipeline does not import this module, and must not.** `pipeline/` and
`sources/` have to be deterministic and offline: the same recipe must build the
same rows on every run, and a QC rule that phoned an API would make `mmds build`
unreproducible. Jev belongs to AUTHORING a recipe — its answer gets written into
the YAML, where a human reviews it and a checker can argue with it — never to
executing one. `tests/test_architecture.py` enforces this, because a boundary
nobody checks is a boundary that moves.

**What goes on the wire:** variable names, variable labels, value labels,
question wordings, study titles — the instrument. **Never respondent rows.**
Every function here takes labels and metadata, never a dataframe slice, which
makes the property structural rather than remembered. Licence-restricted
material (see CLAUDE.md, Data handling) must not reach Jev at all, instrument
included, until the licence has been read.

**Nothing here auto-accepts.** Every answer comes back with the confidence that
`Choice` and `Score` provide, and `Verdict.needs_review` is the caller's cue to
put a human in front of it. The one measured failure that matters: the transfer
screen agreed with hand reading on 12 of 16 studies and **two of its four errors
were in the dangerous direction**. Jev orders the queue; it never overrules an
eye.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

# Confidence below which a human must look. Not tuned to a dataset — chosen so
# that anything the model itself calls a close call is surfaced, because the
# cost of a wrong variable is a whole study built on the wrong column and the
# cost of a second look is a minute.
REVIEW_BELOW = 0.85

# Offered when none of the candidates is right. Present in every Choice here,
# because the alternative is a model forced to pick the least-bad wrong answer:
# measured, `a5v96`'s order-of-presentation variable was chosen at confidence
# 1.00 when the true manipulation had been filtered out of the list.
NONE_OF_THESE = "NONE_OF_THESE"


class JevUnavailableError(RuntimeError):
    """No API key, or the SDK is not installed."""


@dataclass
class Verdict:
    """One Jev answer, with everything needed to decide whether to trust it."""

    value: str
    confidence: float
    runners_up: list[tuple[str, float]] = field(default_factory=list)
    note: str = ""

    @property
    def needs_review(self) -> bool:
        return self.confidence < REVIEW_BELOW or self.value == NONE_OF_THESE

    @property
    def tiebreak_was_close(self) -> bool:
        """True when the second choice was nearly as likely as the first.

        A granularity tiebreak misfired three times by preferring a *different
        construct* that happened to be finer, each time on a margin this would
        have caught (ledger: the window had to come down from 0.10 to 0.03).
        """
        return bool(self.runners_up) and (self.confidence - self.runners_up[0][1]) < 0.10

    def render(self, label: str = "") -> str:
        flag = "REVIEW" if self.needs_review else "ok    "
        close = "  <- close call" if self.tiebreak_was_close else ""
        who = f"{label}: " if label else ""
        head = f"{flag} {who}{self.value}  (conf {self.confidence:.2f}){close}"
        if self.runners_up:
            head += f"\n         next: {[(k, round(v, 2)) for k, v in self.runners_up[:2]]}"
        if self.note:
            head += f"\n         {self.note}"
        return head


def client() -> Any:
    """A TypeSafe client, or a clear explanation of why not.

    `TYPESAFE_API_KEY` lives in `~/.bash_profile`, which the Bash tool does not
    source — so the usual cause of failure here is a shell that was never told,
    not a missing key. Say so rather than letting the SDK raise something vaguer.
    """
    try:
        from typesafe_sdk import TypeSafeClient
    except ImportError as exc:  # pragma: no cover
        raise JevUnavailableError("typesafe-sdk is not installed: `uv add typesafe-sdk`") from exc
    if not os.environ.get("TYPESAFE_API_KEY"):
        raise JevUnavailableError(
            "TYPESAFE_API_KEY is not set. It lives in ~/.bash_profile, which is not "
            "sourced automatically — prefix the command with `source ~/.bash_profile &&`"
        )
    return TypeSafeClient()


def _verdict(answer: Any, *, note: str = "") -> Verdict:
    probs: dict[str, float] = dict(getattr(answer, "probabilities", {}) or {})
    chosen = str(answer.choice)
    runners = sorted(((k, v) for k, v in probs.items() if k != chosen), key=lambda kv: -kv[1])
    return Verdict(
        value=chosen,
        confidence=float(getattr(answer, "confidence", 0.0)),
        runners_up=runners[:3],
        note=note,
    )


# --------------------------------------------------------------------------
# describing an instrument, without sending any of its data
# --------------------------------------------------------------------------


def describe_variable(
    name: str,
    column_label: str,
    value_labels: dict[float, str] | None,
    *,
    max_values: int = 8,
) -> str:
    """One variable as a line Jev can read: name, label, and what its codes mean.

    The VALUE labels are what disambiguate, and leaving them out has cost us a
    study: `a5v96`'s `XTESS193` is labelled "Experimental condition" but its
    values read "Vignette1 followed by Vignette2" — presentation order, not the
    manipulation, whose own variables are labelled merely "Data Only Variable".
    Sent without value labels, Jev picked the order variable at confidence 1.00
    and was reasonable to do so.

    Labels only. No respondent values pass through here.
    """
    line = f"- {name}: {(column_label or '').strip()[:120]}"
    vals = value_labels or {}
    if vals and len(vals) <= 14:
        shown = "; ".join(f"{_code(k)}={v}" for k, v in list(vals.items())[:max_values])
        line += f"  [values: {shown[:200]}]"
    elif vals:
        line += f"  [{len(vals)} distinct coded values]"
    return line


def _code(key: object) -> str:
    try:
        f = float(key)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return str(key)
    return str(int(f)) if f == int(f) else str(f)


# --------------------------------------------------------------------------
# the questions
# --------------------------------------------------------------------------


# Most candidates we may offer in one call. Measured, not guessed: a `Choice`
# over 57 variables answers correctly and confidently (`EMPLOY` at 1.00), the
# same question over 150 returns NONE_OF_THESE for every field — including the
# fields whose variables are plainly in the list. An oversized call does not
# error, it quietly answers "none of the above", which is the worst failure a
# tool like this can have: an empty report reads exactly like a clean one.
MAX_OPTIONS = 45


def choose(
    cli: Any,
    state: str,
    instructions: str,
    candidates: dict[str, str],
    none_means: str,
) -> Verdict:
    """Pick one candidate, paging through them when there are too many.

    Paging rather than pre-filtering. Narrowing the list by keyword is the
    caller quietly making the decision it is asking the model to make, and it
    has twice excluded the true answer here — a keyword filter dropped
    `CALARCO_VIGNETTE` because its label says "vignette", and an arm-count
    heuristic then filled the list with low-cardinality demographics. A
    tournament keeps every column in play: ask each page, then ask again among
    the page winners.

    The final round's confidence is the one reported, which is the honest one —
    it is the round where the real alternatives were actually side by side.
    """
    from typesafe_sdk import Choice

    def ask(options: dict[str, str]) -> Verdict:
        r = cli.system_one(
            state=state,
            questions={
                "pick": Choice(
                    instructions=instructions,
                    criteria={**options, NONE_OF_THESE: none_means},
                )
            },
        )
        return _verdict(r.answers["pick"])

    if len(candidates) <= MAX_OPTIONS:
        return ask(candidates)

    names = list(candidates)
    pages = [names[i : i + MAX_OPTIONS] for i in range(0, len(names), MAX_OPTIONS)]

    # Each page contributes its winner AND its runner-up. Carrying only the
    # winner forward splits genuine rivals across pages and then never compares
    # them: measured on `9xw67`, `REGION4` and `REGION9` land on different pages,
    # and winner-only paging reported `REGION4` at confidence 1.00 where the
    # same question over one page put it at 0.52 against `REGION9`'s 0.46. The
    # 0.52 is the true answer — that choice IS close, and a human should make it.
    through: dict[str, str] = {}
    for page in pages:
        v = ask({n: candidates[n] for n in page})
        for name in [v.value, *(k for k, _ in v.runners_up[:1])]:
            if name in candidates and name != NONE_OF_THESE:
                through[name] = candidates[name]
    if not through:
        return Verdict(value=NONE_OF_THESE, confidence=1.0, note=f"no page of {len(pages)} matched")

    # Never ask a one-option question: a `Choice` with a single candidate cannot
    # answer anything but that candidate, and reports high confidence for doing
    # so. Narrow option lists inflating confidence is a failure mode this project
    # has already paid for, so a lone survivor keeps the confidence it earned on
    # its own page rather than being handed a fresh 1.00.
    if len(through) == 1:
        only = next(iter(through))
        v = ask({n: candidates[n] for n in next(p for p in pages if only in p)})
        v.note = f"sole survivor of {len(pages)} pages; not compared against other pages"
        return v
    final = ask(through)
    final.note = f"run-off between {len(through)} of {len(candidates)} candidates"
    return final


def assignment_variable(cli: Any, listing: str, candidates: dict[str, str]) -> Verdict:
    """Which column records the randomised condition?

    `candidates` is a DENYLIST result, not an allowlist: offer every plausible
    variable and let the low probabilities reject them. Two earlier attempts to
    help by pre-selecting each excluded the true answer — a keyword filter
    dropped `CALARCO_VIGNETTE` because its label says "vignette", and an
    arm-count heuristic then filled the list with low-cardinality demographics.
    Narrowing the options is the caller quietly making the decision it is asking
    the model to make.
    """
    return choose(
        cli,
        state=f"A survey experiment data file. Variables and labels:\n\n{listing}",
        instructions=(
            "Which variable records which randomly assigned experimental condition "
            "each respondent was placed in? Judge the construct, not the variable's "
            "name: a variable labelled 'Experimental condition' whose values describe "
            "the ORDER two items were shown in is a counterbalancing variable, not the "
            "manipulation. If several are genuine assignments, choose the primary one."
        ),
        candidates=candidates,
        none_means="None of these is the experimental assignment variable",
    )


def label_is_a_non_answer(cli: Any, variable: str, labels: list[str]) -> dict[str, Verdict]:
    """For each value label: is it an ANSWER, or the absence of one?

    This is QC rule 12's judgement. In the pipeline it is made by a keyword
    regex (`refused|missing|not asked|skipped|don't know|please specify`), which
    has to stay there because QC runs offline on every build — but a keyword list
    decides this badly at the edges, and the edges are where it matters. Two real
    cases:

      "Other Christian religion, please specify"  IS an answer wearing an
          instruction. Dropped by keyword, it loses a real response — hence
          `Recipe.persona_label_rewrite`.
      "Not asked"  is not an answer, and must leave the field EMPTY rather than
          render as a person's religion.

    Asked at authoring time, written into the recipe as `persona_missing` or
    `persona_label_rewrite`, and reviewed there. The regex stays as a backstop.
    """
    from typesafe_sdk import Choice

    out: dict[str, Verdict] = {}
    for lab in labels:
        r = cli.system_one(
            state=(
                f'A survey variable "{variable}" offers the response option: "{lab}"\n\n'
                f"Its other options are: {', '.join(x for x in labels if x != lab)[:400]}"
            ),
            questions={
                "kind": Choice(
                    instructions=(
                        "Is this option a substantive ANSWER the respondent chose, or the "
                        "ABSENCE of an answer? An option that names a real category but "
                        "also carries scripting boilerplate — 'Other Christian religion, "
                        "please specify' — is still an answer. A refusal, a question never "
                        "asked, or a missing-data sentinel is not."
                    ),
                    criteria={
                        "answer": "a substantive response the respondent gave",
                        "answer_with_boilerplate": (
                            "a real response whose label carries a scripting instruction, "
                            "such as 'please specify'"
                        ),
                        "non_answer": (
                            "a refusal, 'don't know', 'not asked', or a missing-data code — "
                            "no answer was given"
                        ),
                    },
                )
            },
        )
        out[lab] = _verdict(r.answers["kind"])
    return out


def explain_condition(cli: Any, text: str) -> Verdict:
    """Triage a questionnaire condition that `sources.quex` refuses to parse.

    `quex` reads 89.7% of the 1,853 conditional directives in the corpus and
    REFUSES the rest rather than guessing — prose like "RESPONDENT IS
    AVAILABLE", a variable compared to another variable, an elided conjunction,
    a label where a code belongs. Those refusals were going to a human one build
    at a time.

    Most are not machine-evaluable by anything, and the useful question is not
    "what does this evaluate to" but "is this about the stimulus at all". A
    directive that only controls survey administration can be ignored; one that
    gates stimulus text cannot, and must be resolved by hand. Jev can tell those
    apart; a regex cannot.
    """
    from typesafe_sdk import Choice

    r = cli.system_one(
        state=f"A directive from a survey questionnaire's programming:\n\n    {text}",
        questions={
            "kind": Choice(
                instructions=(
                    "What does this directive control? Judge only what it would change "
                    "for a respondent."
                ),
                criteria={
                    "stimulus_text": (
                        "which words the respondent reads — resolving it wrongly would "
                        "change the stimulus"
                    ),
                    "survey_administration": (
                        "interview mechanics: whether the respondent is available, "
                        "screened out, re-prompted, terminated, or paid. Changes no "
                        "stimulus wording"
                    ),
                    "routing_only": (
                        "which later question is asked next, without changing any "
                        "question's wording"
                    ),
                    "unclear": "cannot be determined from the directive alone",
                },
            )
        },
    )
    return _verdict(r.answers["kind"], note=text[:160])


# --------------------------------------------------------------------------
# screening a BUILT row's condition — the one question no test can answer
# --------------------------------------------------------------------------

# Every serious defect this project has shipped was a condition asserting
# something untrue about what the respondent had experienced when they answered:
#
#   b87sm   "Scenario #1"              13,513 rows rating scenarios 2-8
#   es4xw   "in this version"          32,228 rows told the photo had versions
#   sh4px   the self-affirmation task  asked before the task happened
#   a2nbf   "{you/your partner}"        3,117 rows with an unresolved directive
#   a42yg   "both are equally"          500 rows with a word the source lacks
#
# All five live in the corpus's 308 distinct hand-written condition strings, and
# all five answer to one question: *could the respondent have known everything
# this text asserts, at the moment they were asked this outcome?* There is no
# unit test for that — it is irreducibly semantic — and it is the single place
# where this project's defects have actually lived. Variable selection, which is
# what Jev had been used for, has never produced a shipped defect.
#
# Each of the five was found by a human reading one row. At 308 strings the
# screen costs almost nothing and reads all of them.
CONDITION_DEFECTS = {
    "none": (
        "every statement is true of a participant in this condition at the moment "
        "the outcome question was asked"
    ),
    "reveals_the_experiment": (
        "refers to the experiment's own structure — other conditions, arms, versions, "
        "randomisation, or that other participants saw something different. A "
        "participant was in one condition and knew nothing of the others"
    ),
    "sequence_signposting": (
        "claims a position in a sequence — 'Scenario #1', 'the first vignette', 'the "
        "next one' — which need not be the position this condition actually gave them"
    ),
    "premature_treatment": (
        "describes a part of the treatment that had not yet been administered when "
        "this outcome was measured, so it asserts a history the participant did not "
        "yet have at that point in the experiment"
    ),
    "unresolved_directive": (
        "contains leftover questionnaire programming that was meant to be resolved "
        "before the condition was rendered: {a/b} alternatives, [SHOW IF ...], "
        "[INSERT ...], piping placeholders"
    ),
    "truncated_text": (
        "a sentence, label or list is cut off mid-word or mid-clause, usually an "
        "unbalanced bracket or a word ending abruptly"
    ),
    "addresses_the_wrong_person": (
        "attributes to the participant a relationship, attribute or circumstance they "
        "need not have had — a partner, a child, a job — where the text should have "
        "been resolved to what this participant actually reported"
    ),
}


# The two labels that mean "nothing wrong here".
_CLEAN = frozenset({"none", NONE_OF_THESE})

# Probability mass on NAMED defects above which a human looks. Measured by
# `scripts/condition_probe.py` against the defects this project actually shipped
# and their corrections, not chosen by taste. The measured gap:
#
#   shipped defect   0.63  0.64  0.96  0.97
#   its correction   0.04  0.05  0.32  (0.71, see below)
#
# 0.45 sits in that gap with room on both sides. 0.35, which was my guess before
# measuring, would have been 0.03 away from firing on a correction.
#
# The 0.71 is the interesting one. It is the screen flagging the CONTROL text in
# the probe — "Suppose that you were pregnant", which I wrote by hand as a42yg's
# corrected version. It is right: that sentence addresses the wrong person for
# half the sample, which is why the real fix for `a2nbf` was to resolve the
# pronoun from the respondent's own recorded sex rather than hardcode "you". The
# screen found a defect in my test fixture. Left in, and left failing, because a
# probe whose controls are quietly wrong measures nothing.
#
# Re-run the probe if the class list changes — adding a class moves every number.
DEFECT_MASS_REVIEW = 0.45


@dataclass
class ConditionFlag:
    """What the screen made of one (condition, outcome) pair.

    The signal is `defect_mass` — the total probability on named defect classes —
    not the chosen label's confidence. With eight options a correct "none" lands
    around 0.54-0.75, so `REVIEW_BELOW`, tuned for variable selection where one
    answer is usually obvious, flags every clean string. Measured: it flagged 8
    of 8 known-good conditions.

    The first version of this asked a second, redundant `Noul` as a cross-check.
    It returned 0.55-0.58 across every input — a spread of 0.03 — because the
    instruction was a three-clause conjunction, and a compound yes/no has no
    single answer to be probable about. That is ledger #72 exactly: a wrong
    primitive returns a number that looks perfectly usable. Removed rather than
    patched; the mass across the `Choice`'s own classes is the honest redundancy,
    and it is free.
    """

    defect: Verdict
    defect_mass: float
    study: str = ""
    outcome: str = ""
    excerpt: str = ""

    @property
    def needs_review(self) -> bool:
        return self.defect.value not in _CLEAN or self.defect_mass >= DEFECT_MASS_REVIEW

    def render(self) -> str:
        head = f"{self.study}  {self.defect.value}  "
        head += f"(conf {self.defect.confidence:.2f}, defect mass {self.defect_mass:.2f})"
        named = [(k, v) for k, v in self.defect.runners_up if k not in _CLEAN]
        if named:
            head += f"\n    nearest defect: {[(k, round(v, 2)) for k, v in named[:2]]}"
        if self.outcome:
            head += f"\n    asked: {self.outcome[:120]}"
        if self.excerpt:
            head += f"\n    text:  {self.excerpt[:220]}"
        return head


def screen_condition(cli: Any, condition: str, outcome: str, *, study: str = "") -> ConditionFlag:
    """Ask whether a built condition tells this respondent the truth.

    Takes two STRINGS — the rendered condition and the outcome question. Both are
    instrument text: the condition is what we composed from the questionnaire and
    the outcome is the question as asked. No persona, no response, no respondent
    row, which keeps the wire rule structural here as everywhere else in this
    module.
    """
    from typesafe_sdk import Choice

    # The frame has to say three things, and the first version said none of them:
    # that this is a randomised experiment, that the text is ONE CONDITION of it,
    # and that the text is a reconstruction rather than a transcript. Measured
    # cost of getting it wrong: told "a respondent was shown the following text",
    # the model scored `sh4px`'s CORRECTED condition worse than the defective one
    # (0.35 against 0.17), because under that frame any second-person narration of
    # past events reads as suspect and the shorter correction loses the context
    # that justified it. The frame was judging the genre, not the content.
    state = (
        "This is from a randomised social-science experiment. Each participant was "
        "assigned to exactly one experimental condition, then asked an outcome "
        "question. A participant knew only their own condition.\n\n"
        "The text below is a RECONSTRUCTION of one condition, written in the second "
        "person to describe what that condition's participants saw and did. It is "
        "not a transcript and participants never read these words — it was composed "
        "afterwards from the experiment's questionnaire.\n\n"
        f"THE CONDITION, AS RECONSTRUCTED:\n{condition}\n\n"
        f"THE OUTCOME QUESTION ASKED IN THIS CONDITION:\n{outcome}\n"
    )
    r = cli.system_one(
        state=state,
        questions={
            "defect": Choice(
                instructions=(
                    "Judge ONLY whether every statement in the reconstruction was TRUE "
                    "of a participant in this condition at the moment the outcome "
                    "question was asked. Do not judge the experiment's design or "
                    "ethics, do not judge whether the outcome is a good measure, and "
                    "do not penalise the reconstruction for being written in the "
                    "second person or for narrating earlier steps — that is the format, "
                    "and narrating what the participant had already done is correct. "
                    "The fault is a statement that was false, or not yet true, for a "
                    "participant in THIS condition at THAT moment. If more than one "
                    "applies, name the most serious."
                ),
                criteria={**CONDITION_DEFECTS, NONE_OF_THESE: "none of these fits"},
            ),
        },
    )
    answer = r.answers["defect"]
    probs: dict[str, float] = dict(getattr(answer, "probabilities", {}) or {})
    return ConditionFlag(
        defect=_verdict(answer),
        # Summed over the FULL distribution, not `runners_up` — that keeps only
        # the top three, so a defect split across four classes would vanish from
        # the signal exactly when it is least certain and most worth a look.
        defect_mass=sum(p for k, p in probs.items() if k not in _CLEAN),
        study=study,
        outcome=outcome[:200],
        excerpt=condition[:400],
    )
