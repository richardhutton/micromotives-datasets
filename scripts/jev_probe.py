#!/usr/bin/env python3
"""Measure Jev on decisions where we already know the right answer.

This is deliberately NOT a demo. Every question below comes from a study we
built by hand, so each has a ground-truth answer recorded in docs/LEDGER.md.
The point is to find out whether Jev is right, and — just as important —
whether its confidence is *honest*, before we let it near the ~120 studies
that have no reference to check against.

Usage:
    export TYPESAFE_API_KEY=...      # native key from typesafe.ai
    uv run python scripts/jev_probe.py

If you only have a Vercel AI Gateway key, `typesafe-ai/jev` is served there
too, but the gateway requires a card on file and its OpenAI-compatible chat
endpoint does not return the typed answer + confidence that make Jev worth
using. Prefer the native key.
"""

from __future__ import annotations

import os
import sys

try:
    import typesafe_sdk as ts
    from typesafe_sdk import Choice, Noul, TypeSafeClient
except ImportError:  # pragma: no cover
    sys.exit("pip/uv add typesafe-sdk first")


# --- Case 1: the defect Jev is meant to catch --------------------------------
# SocSci210 recorded Q10's answers under Q5's question wording. Our crosscheck
# only caught it by luck (their distribution was 78% zeros against our 10%).
# On a study with no reference, nothing would have caught it at all.
ZRWJP_STATE = """
Study: "The Barriers of Buying Happier Time" (TESS 180, Whillans).
Design: respondents report hours worked per week, weeks worked per year and annual
pay. One randomly assigned group is then SHOWN their computed hourly wage; the
control group is not. Both groups then name a task they dislike and would like to
outsource, and answer follow-up questions about it.

Variables in the data file:
- Q5:  "How much money per month do you think it would cost to outsource this task to others?"
- Q6:  "How much time per month would outsourcing this task to others save you?"
- Q9:  "In a typical month, do you spend any money in order to outsource tasks to others?"
- Q10: "In a typical month, how much money do you spend in order to outsource tasks to others?"
- Q3c: "How much do you earn per year before taxes and other deductions?"
- DOV_HRWAGE: "DATA ONLY: Calculated hourly wage"
"""

# --- Case 2: the inverted factor --------------------------------------------
# SocSci210 described arms 1-4 as "identified only by the label" when the
# questionnaire shows those arms DID include the self-introduction.
SWAN_STATE = """
Study: "When Others' Disbelief Engenders Prejudice" (TESS2 062, Swan).
From the questionnaire's routing blocks:
- XTESS062 = 1..4 : the screen shows Jordan's name, one descriptor line, AND a
  ~120-word friendly self-introduction Jordan wrote (about finishing a degree in
  architecture, wanting to move to California, running marathons). Block length
  ~1,690 characters.
- XTESS062 = 5..8 : the screen shows Jordan's name and the descriptor line ONLY,
  with no self-introduction. Block length ~960 characters.

A published reconstruction of this study describes the arms XTESS062 = 1..4 as
"Jordan is identified only by the label" and arms 5..8 as "identified by the label
with a short friendly biography".
"""

CASES: list[tuple[str, str, dict[str, object], dict[str, object]]] = [
    (
        "zrwjp: which variable is the dependent measure?",
        ZRWJP_STATE,
        {
            "dependent_measure": Choice(
                instructions=(
                    "Which single variable is this experiment's primary DEPENDENT MEASURE — "
                    "the outcome the randomised manipulation was designed to change? Exclude "
                    "measures of pre-existing behaviour and variables used only to build the "
                    "manipulation."
                ),
                criteria={
                    "Q5": "Estimated monthly cost of outsourcing the named task",
                    "Q6": "Estimated monthly time saved by outsourcing the named task",
                    "Q9": "Whether the respondent currently spends money outsourcing",
                    "Q10": "How much the respondent currently spends outsourcing per month",
                    "Q3c": "Annual earnings before tax",
                    "DOV_HRWAGE": "Calculated hourly wage",
                },
            ),
            "q10_is_baseline": Noul(
                instructions=(
                    "Q10 measures behaviour that already existed before the manipulation, "
                    "rather than a response to it."
                )
            ),
        },
        {"dependent_measure": "Q5", "q10_is_baseline": True},
    ),
    (
        "7jt2f: is the published description of the arms correct?",
        SWAN_STATE,
        {
            "description_is_correct": Noul(
                instructions=(
                    "The published reconstruction describes each arm correctly, given the "
                    "questionnaire routing blocks above."
                )
            ),
        },
        {"description_is_correct": False},
    ),
]


def main() -> int:
    if not os.environ.get(ts.constants.API_KEY_ENV):
        print(f"{ts.constants.API_KEY_ENV} is not set — nothing to measure.")
        print("Get a key from typesafe.ai; see this file's docstring.")
        return 1

    client = TypeSafeClient()
    for title, state, questions, expected in CASES:
        print("=" * 78)
        print(title)
        print("=" * 78)
        try:
            response = client.system_one(state=state, questions=questions)  # type: ignore[arg-type]
        except Exception as exc:
            print(f"  call failed: {type(exc).__name__}: {str(exc)[:200]}")
            continue
        print(f"  expected: {expected}")
        print(f"  response: {response}")
        print()
    print("Compare each answer AND its confidence against `expected` above.")
    print("A confident wrong answer is worse than an unconfident one — that is the")
    print("property being measured, not raw accuracy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
