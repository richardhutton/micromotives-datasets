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


class LicenceRefusedError(RuntimeError):
    """Raised when a source's licence forbids its material reaching TypeSafe."""


RESTRICTED: dict[str, str] = {
    "ukds": (
        "UK Data Service safeguarded data, used under the End User Licence (CD137 "
        "v16.00). Clause 4: 'Not to give access to the Data Collection(s), in whole or "
        "in part, or to any Dataset(s) derived from the Data Collection(s)... except to "
        "Registered Users.' The EUL's own definitions put the instrument INSIDE the "
        "collection — 'Data Collection: The Dataset(s), Documentation, Metadata...', "
        "where Documentation is 'data-level documentation i.e. about individual "
        "databases or data files'. Variable labels and value labels ARE data-level "
        "documentation, so the exact thing this module sends is the exact thing clause 4 "
        "forbids sharing. There is no instrument-text-only carve-out of the kind "
        "CLAUDE.md permits for TESS deposits. Map UKDS allocation variables by hand."
    ),
}
"""Sources whose material must never reach TypeSafe. Absence is not permission.

This mirrors `embed.py`'s `CLEARED` gate deliberately, but inverts it. `embed`
names what MAY travel, because its corpus is small and every caller is in one
file. This module is reached from nine scripts, so an allow-list would have
failed closed on all of them the day it landed and been widened in a hurry,
which is how gates die.

The guarantee instead comes from `client()` taking a REQUIRED `source`: a caller
cannot reach the wire without naming what it is about to send. A missing name is
a type error at the call site rather than a silent default, and a wrong name is
something a person wrote down and can be held to.

It is a weaker guarantee than `embed.py`'s and that is worth saying plainly: this
stops the UKDS mistake, not every mistake.
"""


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


def client(source: str, http_client: Any = None) -> Any:
    """A TypeSafe client, or a clear explanation of why not.

    `source` says WHOSE material is about to cross the wire — `tess`, `dataverse`,
    `ukds`, `socsci210`. It is required and positional so that no caller can reach
    the wire without naming what it is sending; see `RESTRICTED` for why that is
    the guarantee rather than an allow-list. Anything named there raises.

    `TYPESAFE_API_KEY` lives in `~/.bash_profile`, which the Bash tool does not
    source — so the usual cause of failure here is a shell that was never told,
    not a missing key. Say so rather than letting the SDK raise something vaguer.

    `http_client` is for `scripts/jev_show_wire.py`, which hooks the transport to
    print exactly what leaves the machine. It takes one so that the thing being
    inspected is a REAL production call: the alternative is a script that builds
    its own payload and reports on that, which is how a stale copy of the
    transfer-screen prompt came to live there (ledger 85).
    """
    # A caller may legitimately be sending material from several sources in one
    # run — `persona_harmonise.py` reads every recipe — so a declaration may name
    # more than one, joined by "+". EVERY name is checked; naming two sources is
    # a wider promise than naming one, not a way to dilute it.
    if restricted := sorted(set(source.split("+")) & set(RESTRICTED)):
        source = restricted[0]
        raise LicenceRefusedError(
            f"{source!r} may not be sent to TypeSafe.\n\n{RESTRICTED[source]}\n\n"
            f"Nothing was sent. Do not widen this by passing a different source name — "
            f"the name is the declaration, and a false one is worse than no gate."
        )
    try:
        from typesafe_sdk import TypeSafeClient
    except ImportError as exc:  # pragma: no cover
        raise JevUnavailableError("typesafe-sdk is not installed: `uv add typesafe-sdk`") from exc
    if not os.environ.get("TYPESAFE_API_KEY"):
        raise JevUnavailableError(
            "TYPESAFE_API_KEY is not set. It lives in ~/.bash_profile, which is not "
            "sourced automatically — prefix the command with `source ~/.bash_profile &&`"
        )
    return TypeSafeClient() if http_client is None else TypeSafeClient(http_client=http_client)


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


# --------------------------------------------------------------------------
# the persona layer: which variable, and what its labels mean
# --------------------------------------------------------------------------
#
# These five prompts lived in four scripts until they were moved here. The
# module docstring above has said since it was written that asking them in
# separate scripts is how "a lesson learned in one did not reach the others",
# and the scripts went on owning them anyway — including `jev_show_wire.py`,
# which held a stale sixth copy of the transfer-screen wording, and
# `jev_calibration.py`, the harness that MEASURES Jev, which measured a prompt
# production does not send (ledger 86). `tests/test_architecture.py` now fails
# on a `system_one` call outside this module.

# What each persona field means, as a phrase that completes "This variable
# records ___ — as a fact about the person answering the survey."
PERSONA_WANTED = {
    "income": "the respondent's own total household income",
    "income_personal": "the respondent's own gross personal (individual, not household) income",
    "education": "the respondent's own highest level of education completed",
    "ethnicity": "the respondent's own race or ethnicity",
    "employment": "the respondent's own current employment status",
    "region": "where the respondent themselves lives",
}

# What a variable can turn out to be. `other` is deliberately present so the
# model can decline rather than be forced into a wrong box — the narrow-option
# mistake from the earlier Jev work, and the reason `a5v96`'s order variable was
# picked at confidence 1.00 once the true manipulation had been filtered out.
PERSONA_VARIABLE_KINDS = {
    "respondent_attribute": (
        "a fact about the person answering, from the panel profile or a "
        "demographic question they answered about themselves"
    ),
    "vignette_or_scenario_attribute": (
        "an attribute of a fictional person or situation described in material "
        "shown TO the respondent"
    ),
    "derived_or_computed": (
        "a helper column computed from other columns, e.g. a recode, a bracket "
        "flag or a 'data only variable'"
    ),
    "opinion_or_attitude_item": (
        "a question asking what the respondent thinks, rather than recording what they are"
    ),
    "weight_or_admin": ("a survey weight, case id, timestamp, mode or other administrative field"),
    "other": "none of the above fits",
}

# The canonical concepts a source label can denote, per field. US-anchored, and
# knowingly so: every scheme harmonised so far is a US survey. The UK layer adds
# a second vocabulary here rather than stretching this one — a trade
# apprenticeship has no rung on this ladder, and forcing it onto one would
# assert something false that nothing downstream could detect.
PERSONA_VOCAB: dict[str, dict[str, str]] = {
    "ethnicity": {
        "white": "White, Caucasian or European",
        "black": "Black, African-American or African",
        "hispanic": "Hispanic, Latino or Spanish origin",
        "asian": "Asian or Asian-American",
        "native_american": "American Indian, Native American or Alaska Native",
        "pacific_islander": "Native Hawaiian or other Pacific Islander",
        "middle_eastern": "Middle Eastern or North African",
        "two_or_more_races": "two or more races, mixed or multiracial",
        "other_residual": "a catch-all for anything not listed",
        "declined": "refused, prefer not to say, or missing",
    },
    "employment": {
        "employed_full_time": "working full time",
        "employed_part_time": "working part time",
        "self_employed": "self-employed",
        "employed_unspecified": "working, without full/part time distinguished",
        "unemployed_looking": "not working and looking for work",
        "unemployed_not_looking": "not working and not looking for work",
        "retired": "retired",
        "student": "in school or a student",
        "homemaker": "keeping house, homemaker or caring for family",
        "disabled": "disabled or unable to work",
        "other_residual": "a catch-all for anything not listed",
        "declined": "refused, prefer not to say, or missing",
    },
    "education": {
        "less_than_high_school": "did not complete secondary school",
        "high_school": "completed secondary school or equivalent",
        "some_college": "some post-secondary study, no degree",
        "associate": "a two-year or associate degree",
        "bachelors": "a bachelor's degree",
        "postgraduate": "a master's, doctorate or professional degree",
        "bachelors_or_higher": "a bachelor's degree or above, not distinguished further",
        "other_residual": "a catch-all for anything not listed",
        "declined": "refused, prefer not to say, or missing",
    },
}

# Fields whose concepts sit on a LINE, lowest to highest, so a label can span
# several of them. Order is load-bearing.
PERSONA_LADDER = {
    "education": [
        "less_than_high_school",
        "high_school",
        "some_college",
        "associate",
        "bachelors",
        "postgraduate",
    ],
}


@dataclass
class PersonaVariable:
    """What Jev made of one candidate column."""

    is_attribute: float
    kind: Verdict

    @property
    def needs_review(self) -> bool:
        return self.kind.needs_review


def classify_persona_variable(
    cli: Any, field: str, study_title: str, variable_block: str
) -> PersonaVariable:
    """Is this column the RESPONDENT's own attribute, or something else?

    Two questions rather than one, because they fail differently: the `Noul`
    says how confident it is that this is the person's own fact, the `Choice`
    says what it is instead when it is not. A regex proposed six vignette
    variables about a fictional character as "income"; the Choice is what threw
    them out, and it could only do that by having somewhere to put them.

    `variable_block` is the rendered candidate — name, label and value labels.
    Labels and metadata only: no respondent rows reach this call.
    """
    from typesafe_sdk import Choice, Noul

    state = (
        f'Survey study: "{study_title}"\n\nOne variable from its data file:\n\n{variable_block}\n'
    )
    r = cli.system_one(
        state=state,
        questions={
            "is_respondent_attribute": Noul(
                instructions=(
                    f"This variable records {PERSONA_WANTED[field]} — as a fact about the "
                    "person answering the survey. It is NOT a derived/computed "
                    "helper, NOT a weight, NOT an attribute of a fictional person "
                    "described in a vignette or scenario shown to the respondent, "
                    "and NOT a question asking the respondent's opinion about "
                    "someone else."
                )
            ),
            "kind": Choice(
                criteria=dict(PERSONA_VARIABLE_KINDS),
                instructions="What this variable actually is.",
            ),
        },
    )
    return PersonaVariable(
        is_attribute=float(r.answers["is_respondent_attribute"].noul),
        kind=_verdict(r.answers["kind"]),
    )


def _label_in_scheme(field: str, label: str, labels: tuple[str, ...]) -> str:
    """The state shared by both label-reading calls: the label, in its own list.

    A category is only readable against its siblings — whether 'Other' is the
    catch-all depends entirely on what else was offered.
    """
    return (
        f"A survey recorded the respondent's {field} with these categories:\n\n"
        + "\n".join(f"  - {x}" for x in labels)
        + f"\n\nThe category in question is: {label!r}\n"
    )


@dataclass
class CategoryReading:
    """What one source label denotes, and whether it is the scheme's catch-all."""

    concept: Verdict
    is_residual: float

    @property
    def residual(self) -> bool:
        return self.is_residual >= 0.5

    @property
    def needs_review(self) -> bool:
        return self.concept.needs_review


def category_concept(cli: Any, field: str, label: str, labels: tuple[str, ...]) -> CategoryReading:
    """Which canonical concept an UNORDERED source label denotes.

    `persona.categories` then does the bookkeeping: a canonical category must be
    a union of categories from EVERY scheme, so a concept one scheme separates
    and another folds into its residual ends up labelled `Other or Asian` rather
    than `Other`. Which label IS the residual is the judgement, and it is this
    call — a specific named group is not a catch-all, and neither is a refusal.
    """
    from typesafe_sdk import Choice, Noul

    r = cli.system_one(
        state=_label_in_scheme(field, label, labels),
        questions={
            "concept": Choice(
                criteria={**PERSONA_VOCAB[field], "none_of_these": "no listed concept fits"},
                instructions=(
                    f"Which concept the category {label!r} denotes. Judge the "
                    "category itself, in the context of the full list above. "
                    "Choose none_of_these rather than forcing a poor fit."
                ),
            ),
            "is_residual": Noul(
                instructions=(
                    f"The category {label!r} is a CATCH-ALL: it holds respondents "
                    "who do not fit any of the other listed categories. A specific "
                    "named group is not a catch-all, and neither is a refusal or "
                    "missing-data code."
                )
            ),
        },
    )
    return CategoryReading(
        concept=_verdict(r.answers["concept"]),
        is_residual=float(r.answers["is_residual"].noul),
    )


def ordinal_span(
    cli: Any, field: str, label: str, labels: tuple[str, ...]
) -> tuple[Verdict, Verdict]:
    """The lowest and highest rung an ORDERED source label covers.

    Two questions rather than one, because a label like "Bachelor's degree or
    higher" genuinely spans several rungs and forcing it onto a single concept
    is what broke the categorical attempt. The pair is what lets a label become
    an interval, which `persona.bands` can then tile.
    """
    from typesafe_sdk import Choice

    vocab = {k: PERSONA_VOCAB[field][k] for k in PERSONA_LADDER[field]}
    questions = {
        edge: Choice(
            criteria={**vocab, "none_of_these": "not an educational level at all"},
            instructions=(
                f"The {word} level of {field} a respondent in the category "
                f"{label!r} could have. For a category covering one level only, "
                "the lowest and the highest are the same."
            ),
        )
        for edge, word in (("lowest", "LOWEST"), ("highest", "HIGHEST"))
    }
    r = cli.system_one(state=_label_in_scheme(field, label, labels), questions=questions)
    return _verdict(r.answers["lowest"]), _verdict(r.answers["highest"])


# --------------------------------------------------------------------------
# choosing what to build: does a US study transfer, and is it worth it
# --------------------------------------------------------------------------

# 0-4 rubrics, written out. Asked as `Noul`s first, these returned a tight high
# cluster that discriminated nothing — a Noul is a yes/no probability, not a
# magnitude (ledger 72). As `Score`s with these levels, evergreen spreads
# 0.39-3.88 and a 2002 smallpox-vaccine study correctly collapses to 0.39.
UK_RELEVANCE_LEVELS = [
    "Of no interest to UK social research. The outcome bears on nothing a UK "
    "researcher, civil servant or journalist argues about.",
    "Marginal. Academic interest only, or a question settled long ago.",
    "Real but niche. A recognisable question within one specialism.",
    "Clearly relevant. A UK researcher in the field would call this a live "
    "question, though not a prominent one.",
    "Prominent. The outcome bears on something argued about in UK policy, the "
    "press or public debate right now.",
]

UK_EVERGREEN_LEVELS = [
    "Tied to a specific past event, named politician, or a policy or technology "
    "since superseded. The question no longer exists in this form.",
    "Dated. Still intelligible, but the context has moved substantially.",
    "Partly dated. The underlying question survives; its framing has aged.",
    "Largely stable. Asked today it would mean much the same thing.",
    "Timeless. A question about human behaviour that does not depend on when it was asked.",
]

UK_DOMAINS = {
    "health_and_care": "illness, medicine, doctors, mental health, disability, social care",
    "work_and_money": "jobs, pay, unemployment, pensions, debt, household finances",
    "family_and_relationships": "couples, parenting, childcare, housework, caring",
    "welfare_and_inequality": "benefits, poverty, redistribution, class, deservingness",
    "discrimination_and_identity": "race, gender, sexuality, religion, immigration, stigma",
    "crime_and_justice": "policing, courts, punishment, risk, safety",
    "environment_and_energy": "climate, pollution, energy use, sustainable consumption",
    "politics_and_institutions": "voting, parties, government, trust in institutions, media",
    "consumer_and_technology": "purchases, firms, apps, data and privacy, algorithms",
    "survey_methodology": "the study is ABOUT how surveys work — scales, wording, order effects",
}


def _study_state(title: str, questions: str) -> str:
    """A study described by its own question wordings. Instrument only."""
    return f'Survey experiment: "{title}"\n\nThe questions asked of respondents:\n\n{questions}'


def screen_uk_transfer(cli: Any, title: str, questions: str) -> tuple[float, float]:
    """Would this US study mean the same thing asked in the UK?

    Returns (stimulus_is_us_specific, outcome_needs_us_knowledge).

    **This orders a queue and never overrules an eye.** Measured against hand
    reading of the fielded questionnaires it agreed on 12 of 16 studies, and two
    of its four errors were in the dangerous direction — it called `b87sm` and
    `rpw4u` fully transferable where reading said mechanism-only.
    """
    from typesafe_sdk import Noul

    r = cli.system_one(
        state=_study_state(title, questions),
        questions={
            "stimulus_is_us_specific": Noul(
                instructions=(
                    "The scenarios or materials shown to respondents refer to institutions, "
                    "laws, political parties, public figures or cultural references that are "
                    "specific to the United States."
                )
            ),
            "outcome_needs_us_knowledge": Noul(
                instructions=(
                    "Answering the main outcome question requires knowledge of United States "
                    "law, politics or institutions that a respondent in another country would "
                    "not reliably have. Judge the OUTCOME question, not the topic in general — "
                    "a universal psychological question set in a US scene does not count."
                )
            ),
        },
    )
    return (
        float(r.answers["stimulus_is_us_specific"].noul),
        float(r.answers["outcome_needs_us_knowledge"].noul),
    )


@dataclass
class PriorityReading:
    """How much a study is worth building, and what it is about."""

    relevance: float
    relevance_conf: float
    evergreen: float
    evergreen_conf: float
    domain: Verdict

    @property
    def needs_review(self) -> bool:
        return min(self.relevance_conf, self.evergreen_conf, self.domain.confidence) < 0.6


def score_uk_priority(cli: Any, title: str, questions: str) -> PriorityReading:
    """Rank a study for UK value: relevance, how well it has aged, its domain."""
    from typesafe_sdk import Choice, Score

    r = cli.system_one(
        state=_study_state(title, questions) + "\n",
        questions={
            "uk_relevance": Score(
                criteria=list(UK_RELEVANCE_LEVELS),
                instructions=(
                    "How much does the OUTCOME this study measures bear on a question "
                    "UK social research, public debate or policy argues about? Judge "
                    "the substance of what is being measured, not whether the scenario "
                    "happens to be set in America."
                ),
            ),
            "evergreen": Score(
                criteria=list(UK_EVERGREEN_LEVELS),
                instructions=(
                    "Is the attitude or behaviour measured here still the same question "
                    "today as when it was asked?"
                ),
            ),
            "domain": Choice(
                criteria={**UK_DOMAINS, "other": "none of these fits"},
                instructions="The single domain this study's OUTCOME sits in.",
            ),
        },
    )
    rel, ever = r.answers["uk_relevance"], r.answers["evergreen"]
    return PriorityReading(
        relevance=float(rel.score),
        relevance_conf=float(rel.confidence),
        evergreen=float(ever.score),
        evergreen_conf=float(ever.confidence),
        domain=_verdict(r.answers["domain"]),
    )


# --------------------------------------------------------------------------
# deposits and categories: the Dataverse sweep and corpus overview prompts
# --------------------------------------------------------------------------

DEPOSIT_UK_SAMPLE = {
    "uk_only": "respondents were sampled in the United Kingdom (or one of its nations) only",
    "uk_among_others": (
        "a multi-country study in which the UK, Britain or one of its nations is one of the samples"
    ),
    "not_uk": "respondents were sampled outside the United Kingdom",
    "cannot_tell": "the text does not say where respondents were sampled",
}
DEPOSIT_DESIGN = {
    "survey_experiment": (
        "a survey in which respondents were randomly assigned to different question wordings, "
        "frames, vignettes or information"
    ),
    "conjoint": "a conjoint or discrete-choice experiment with randomised profile attributes",
    "list_experiment": "a list experiment (item count technique) with randomised lists",
    "field_or_lab_experiment": (
        "a randomised experiment carried out in the field or a lab, not inside a survey"
    ),
    "observational": "a survey, panel, text corpus or other data with no randomised assignment",
    "other": "anything else, including software, simulations or aggregate data",
}


@dataclass
class DepositReading:
    """Where a data deposit's respondents were, and what kind of study made it."""

    uk_sample: Verdict
    design: Verdict

    @property
    def needs_review(self) -> bool:
        return self.uk_sample.needs_review or self.design.needs_review


def screen_deposit(
    cli: Any,
    title: str,
    description: str,
    keywords: str,
    geography: str,
    publication: str,
    files: str,
) -> DepositReading:
    """Read a Dataverse deposit's own metadata: UK sample? randomised design?

    Everything sent is the deposit's public record (title, description, keywords,
    coverage, citation, file NAMES). Never a data file's contents. A keyword
    heuristic is run beside this by `scripts/dataverse_sweep.py`, and the two
    are reported where they disagree; this ranks a reading queue, never decides.
    """
    from typesafe_sdk import Choice

    state = (
        f'Research data deposit: "{title}"\n\n'
        f"Description: {description or '(none)'}\n\n"
        f"Keywords: {keywords or '(none)'}\n"
        f"Geographic coverage: {geography or '(none)'}\n"
        f"Publication: {publication or '(none)'}\n"
        f"Files: {files or '(none)'}"
    )
    r = cli.system_one(
        state=state,
        questions={
            "uk_sample": Choice(
                criteria=DEPOSIT_UK_SAMPLE,
                instructions="Where were the respondents in this study sampled?",
            ),
            "design": Choice(
                criteria=DEPOSIT_DESIGN,
                instructions="What kind of study produced this data?",
            ),
        },
    )
    return DepositReading(
        uk_sample=_verdict(r.answers["uk_sample"]), design=_verdict(r.answers["design"])
    )


def categorise_experiment(
    cli: Any,
    title: str,
    description: str,
    categories: tuple[str, ...],
    meanings: tuple[str, ...],
) -> Verdict:
    """Pick one of the corpus's categories for an experiment, or NONE_OF_THESE.

    `categories` and `meanings` are the manifest's vocabulary, paired by
    position. NONE_OF_THESE is always offered, because a topic the vocabulary has
    no slot for (DEL's aid and climate studies, 2026-10-10) should say so rather
    than be forced into the least-bad wrong bucket.
    """
    from typesafe_sdk import Choice

    # strict=True is the check: a mismatched pair raises rather than silently
    # dropping categories off the end (tests/test_jev.py mutation-tests it).
    criteria = dict(zip(categories, meanings, strict=True))
    criteria[NONE_OF_THESE] = "none of these categories fits"
    r = cli.system_one(
        state=f'Survey experiment: "{title}"\n\n{description}',
        questions={
            "category": Choice(
                criteria=criteria,
                instructions="Which category best describes what this experiment studies?",
            )
        },
    )
    return _verdict(r.answers["category"])
