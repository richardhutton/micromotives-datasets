#!/usr/bin/env python3
"""Can a big model do the holdout task at all? Tested on invented people.

holdout3 scores `qwen3:8b` on predicting a person's held-out survey answer from
the rest of their profile. It is stuck around a third of the gettable range, and
three different things would explain that:

    the method is wrong        — past answers do not predict future ones
    the model is too small     — 8B cannot use a 6,600-character profile
    the prompt is wrong        — the signal is there and badly presented

Those need three different responses and holdout3 cannot tell them apart,
because it only ever runs one model. This runs a BIG model on the same task and
separates the first from the other two: if Claude scores well, the method is
sound and we are hardware-limited; if Claude also fails, the method is wrong and
no amount of hardware fixes it.

**NO UKDS DATA IS SENT, AND NONE IS USED TO BUILD THE PEOPLE.** The Innovation
Panel is licensed under the UKDS End User Licence, whose "Data Collection"
includes the Documentation — so the answers, the variable labels AND the question
wordings are all the collection, and none of them may leave this machine.
Perturbing a real profile does not change that, and would not even be useful: a
poor score on degraded data cannot distinguish a bad method from added noise.

So the people here are invented, and so are the questions. Each person is built
from a small set of latent traits, and their answers are generated from those
traits with noise. That makes the task HARDER in one respect and EASIER in
another, both worth stating:

  harder — a real person's answers are correlated through a lifetime of shared
  causes, so a real profile carries more redundant signal than this does.

  easier — here a consistent generating process genuinely exists. For a real
  person it may not, which is exactly what the 27.7% and 60.8% ceilings are
  measuring.

Therefore **a good score here does not predict a good score on real data**. What
it establishes is only the negative: if a big model cannot recover a held-out
answer from a profile that was generated to be recoverable, the whole approach
is unsound and nothing downstream is worth building. That is a cheap and
genuinely useful thing to know, and it is all this claims.

**THE COMPARISON THAT ACTUALLY SETTLES SOMETHING** is running the SAME invented
people past both models. Opus 5 and `qwen3:8b` then differ in exactly one
respect, against a ceiling computed from the generator itself, so:

    8B near Opus 5  -> the model is not the bottleneck, and the shortfall on
                       real data is about the data or the prompt
    8B far below    -> model size is the bottleneck, and no prompt work fixes it

    uv run python scripts/synthetic_probe.py --n 40                  # Opus 5
    uv run python scripts/synthetic_probe.py --n 40 --local          # qwen3:8b
    uv run python scripts/synthetic_probe.py --oracle                # the ceiling
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import statistics
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

import anthropic

MODEL = "claude-opus-5"
# Same endpoint, model and decoding settings holdout3 uses, so `--local` differs
# from the real-data run in the DATA only.
OLLAMA = "http://localhost:11434/api/generate"
LOCAL_MODEL = "qwen3:8b"

# Six latent traits on 0-1. Every answer is a noisy read of one or two of them,
# which is the structure Park's survey-only agents exploit: no single answer
# pins a trait, and thirty of them nearly do.
TRAITS = ("health", "optimism", "trust", "thrift", "tradition", "sociability")


@dataclass
class Item:
    """One invented question: its wording, its options, and what drives it."""

    key: str
    question: str
    options: list[str]
    drivers: tuple[str, ...]
    # True where a HIGH trait means a LATE option. Written per item rather than
    # inferred, because an inferred direction is the defect that put `excellent,
    # fair, good, poor, very good` into a prompt as if it were a scale.
    ascending: bool = True


# Written for this test. None of these is a UKHLS, SF-12, GHQ or BFI item; where
# a concept overlaps (nobody owns "how is your health"), the wording is ours and
# the option sets are deliberately not the panel's.
ITEMS: list[Item] = [
    Item(
        "stairs",
        "Climbing two flights of stairs leaves you out of breath.",
        ["never", "rarely", "sometimes", "often", "always"],
        ("health",),
        ascending=False,
    ),
    Item(
        "walk",
        "How far can you walk before you need to stop and rest?",
        ["a few steps", "to the end of the road", "half a mile", "two miles", "as far as I like"],
        ("health",),
    ),
    Item(
        "sleep",
        "In a usual week, how many nights do you sleep badly?",
        ["none", "one or two", "three or four", "five or six", "every night"],
        ("health", "optimism"),
        ascending=False,
    ),
    Item(
        "doctor",
        "How often have you seen a doctor about your own health this year?",
        ["not at all", "once", "two or three times", "four to six times", "more than six"],
        ("health",),
        ascending=False,
    ),
    Item(
        "nextyear",
        "Do you expect next year to be better or worse than this one?",
        ["much worse", "a little worse", "about the same", "a little better", "much better"],
        ("optimism",),
    ),
    Item(
        "worry",
        "How much of the day do you spend worrying about things?",
        ["none of it", "a little", "some of it", "most of it", "all of it"],
        ("optimism",),
        ascending=False,
    ),
    Item(
        "plans",
        "When something goes wrong, do you expect it to work out in the end?",
        ["never", "rarely", "sometimes", "usually", "always"],
        ("optimism", "trust"),
    ),
    Item(
        "strangers",
        "Most people would take advantage of you if they got the chance.",
        ["strongly agree", "agree", "neither", "disagree", "strongly disagree"],
        ("trust",),
    ),
    Item(
        "lend",
        "Would you lend fifty pounds to a neighbour you had met twice?",
        ["certainly not", "probably not", "not sure", "probably", "certainly"],
        ("trust", "sociability"),
    ),
    Item(
        "institutions",
        "How much do you trust large organisations to treat you fairly?",
        ["not at all", "a little", "somewhat", "a lot", "completely"],
        ("trust",),
    ),
    Item(
        "saving",
        "What do you do with money left over at the end of the month?",
        ["spend it", "mostly spend it", "half and half", "mostly save it", "save all of it"],
        ("thrift",),
    ),
    Item(
        "bargain",
        "How often do you compare prices before buying something ordinary?",
        ["never", "rarely", "sometimes", "usually", "every time"],
        ("thrift",),
    ),
    Item(
        "debt",
        "How comfortable are you borrowing money for something you want now?",
        ["very comfortable", "comfortable", "neither", "uncomfortable", "very uncomfortable"],
        ("thrift",),
    ),
    Item(
        "oldways",
        "The way things were done thirty years ago was generally better.",
        ["strongly disagree", "disagree", "neither", "agree", "strongly agree"],
        ("tradition",),
    ),
    Item(
        "change",
        "How do you feel when a familiar place in your town is redeveloped?",
        ["pleased", "mostly pleased", "indifferent", "mostly sorry", "sorry"],
        ("tradition",),
    ),
    Item(
        "duty",
        "People have a duty to keep up the customs they were raised with.",
        ["strongly disagree", "disagree", "neither", "agree", "strongly agree"],
        ("tradition", "trust"),
    ),
    Item(
        "evenings",
        "In a usual week, how many evenings do you spend with other people?",
        ["none", "one", "two or three", "four or five", "most evenings"],
        ("sociability",),
    ),
    Item(
        "party",
        "You are invited to a party where you will know almost nobody.",
        ["definitely not going", "probably not", "might go", "probably going", "definitely going"],
        ("sociability",),
    ),
    Item(
        "talk",
        "How easily do you start a conversation with someone you have just met?",
        ["not at all easily", "not very easily", "fairly easily", "easily", "very easily"],
        ("sociability", "trust"),
    ),
    Item(
        "alone",
        "How much do you enjoy a day entirely on your own?",
        ["enormously", "a lot", "somewhat", "a little", "not at all"],
        ("sociability",),
    ),
]

YEARS = tuple(range(2008, 2025))


@dataclass
class Person:
    """An invented person: latent traits, demographics, and dated answers."""

    traits: dict[str, float]
    age: int
    sex: str
    region: str
    answers: list[dict[str, Any]] = field(default_factory=list)


REGIONS = (
    "Scotland",
    "Wales",
    "North East",
    "North West",
    "London",
    "South West",
    "West Midlands",
    "Yorkshire and the Humber",
)


def make_person(rng: random.Random) -> Person:
    """Traits, then answers generated from them with noise and slow drift.

    `noise` is 0.18 of the 0-1 trait range. On a five-option item that puts a
    meaningful minority of answers one option away from the trait's own value,
    so the profile is informative without being a lookup table — if an item were
    deterministic in its trait, one sibling answer would give the target away and
    the test would measure nothing.
    """
    traits = {t: rng.random() for t in TRAITS}
    person = Person(
        traits=traits,
        age=rng.randint(25, 80),
        sex=rng.choice(("Male", "Female")),
        region=rng.choice(REGIONS),
    )
    # Traits drift slowly over the 17 years, so repeated answers are consistent
    # without being identical — the panel's own behaviour.
    drift = {t: rng.uniform(-0.15, 0.15) for t in TRAITS}
    for year in YEARS:
        span = (year - YEARS[0]) / (YEARS[-1] - YEARS[0])
        for item in ITEMS:
            if rng.random() > 0.45:  # not every item every year
                continue
            level = statistics.fmean(
                min(1.0, max(0.0, traits[d] + drift[d] * span)) for d in item.drivers
            )
            level += rng.gauss(0, 0.18)
            level = min(0.999, max(0.0, level))
            index = int(level * len(item.options))
            if not item.ascending:
                index = len(item.options) - 1 - index
            person.answers.append(
                {
                    "year": year,
                    "key": item.key,
                    "question": item.question,
                    "answer": item.options[index],
                }
            )
    return person


def build_prompt(person: Person, shown: list[dict[str, Any]], item: Item, year: int) -> str:
    """Same shape as holdout3's prompt, so the comparison is about the model."""
    lines = [
        "You are this person, answering a survey. Answer as they would, "
        "not as you think they should.",
        "",
        "ABOUT YOU",
        f"Age: {person.age - (2024 - year)}",
        f"Sex: {person.sex}",
        f"Region: {person.region}",
    ]
    if shown:
        lines += ["", "WHAT YOU HAVE TOLD THIS SURVEY OVER THE YEARS"]
        by_question: dict[str, list[tuple[int, str]]] = {}
        for a in shown:
            by_question.setdefault(a["question"], []).append((a["year"], a["answer"]))
        for question, pairs in by_question.items():
            runs = ", ".join(f"{ans} [{yr}]" for yr, ans in sorted(pairs))
            lines.append(f"- {question} {runs}")
    lines += ["", f"THE QUESTION, ASKED IN {year}", item.question, "", "OPTIONS"]
    lines += [f"  {i}. {opt}" for i, opt in enumerate(item.options, 1)]
    lines += ["", "Answer with the number of the option only."]
    return "\n".join(lines)


def ask(client: anthropic.Anthropic, model: str, prompt: str, n_options: int) -> int | None:
    """One prediction. Returns the chosen option number, or None if unreadable.

    **Thinking is disabled deliberately, and it is not a detail.** On its default
    adaptive setting Opus 5 spent the whole of an 8-token budget on thinking
    tokens and returned no text block at all, so a third of the first run came
    back empty and those rows were quietly dropped from the denominator — a
    scoreboard computed over whichever questions happened to parse. It is also
    the fairer comparison: holdout3 calls the local model with `think: False`, so
    leaving it on here would credit the big model with reasoning the small one
    was never allowed.
    """
    try:
        msg = client.messages.create(
            model=model,
            max_tokens=8,
            thinking={"type": "disabled"},
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as exc:
        print(f"    api error: {exc}")
        return None
    text = "".join(b.text for b in msg.content if b.type == "text")
    found = re.search(r"\d+", text)
    if not found:
        print(f"    unparseable (stop_reason {msg.stop_reason}): {text!r}")
        return None
    value = int(found.group())
    if not 1 <= value <= n_options:
        print(f"    out of range: {value} not in 1..{n_options}")
        return None
    return value


def ask_local(prompt: str, n_options: int) -> int | None:
    """One prediction from ollama, with holdout3's exact decoding settings."""
    body = json.dumps(
        {
            "model": LOCAL_MODEL,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {"temperature": 0, "num_predict": 8},
        }
    ).encode()
    try:
        req = urllib.request.Request(
            OLLAMA, data=body, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=300) as r:
            text = str(json.loads(r.read())["response"])
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"    ollama error: {exc}")
        return None
    nums = re.findall(r"\b(\d+)\b", text)
    if not nums:
        print(f"    unparseable: {text!r}")
        return None
    value = int(nums[0])
    if not 1 <= value <= n_options:
        print(f"    out of range: {value} not in 1..{n_options}")
        return None
    return value


def oracle_ceiling(trials: int = 4000, seed: int = 0) -> dict[str, float]:
    """The best score any predictor could get on these people.

    The generator adds gaussian noise to every answer, so even knowing a
    person's latent traits exactly does not reproduce their answer. Without this
    number a model's score is as uninterpretable as holdout3's 39% was before
    `scripts/ceiling.py` existed — which is the mistake this exists not to
    repeat.

    The oracle is given the undrifted trait, slightly less than the generator
    itself used, so this is a marginally conservative ceiling rather than an
    optimistic one.
    """
    rng = random.Random(seed)
    by_key = {i.key: i for i in ITEMS}
    exact = near = n = 0
    for _ in range(trials):
        person = make_person(rng)
        key = rng.choice(sorted({a["key"] for a in person.answers}))
        item = by_key[key]
        target = max((a for a in person.answers if a["key"] == key), key=lambda a: a["year"])
        truth = item.options.index(target["answer"]) + 1
        level = statistics.fmean(person.traits[d] for d in item.drivers)
        index = int(min(0.999, max(0.0, level)) * len(item.options))
        if not item.ascending:
            index = len(item.options) - 1 - index
        guess = index + 1
        n += 1
        exact += guess == truth
        near += abs(guess - truth) <= 1
    return {"n": n, "exact": exact / n, "within_one": near / n}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=40, help="how many held-out questions")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument(
        "--local", action="store_true", help=f"use {LOCAL_MODEL} via ollama instead of the API"
    )
    ap.add_argument("--oracle", action="store_true", help="print the ceiling and stop")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    if args.oracle:
        got = oracle_ceiling()
        print(
            f"oracle over {got['n']:,} held-out questions (knows the latent traits): "
            f"exact {got['exact']:.1%}, within one {got['within_one']:.1%}"
        )
        return

    client = None
    if not args.local:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise SystemExit("ANTHROPIC_API_KEY not set")
        client = anthropic.Anthropic()
    rng = random.Random(args.seed)
    by_key = {i.key: i for i in ITEMS}

    results = []
    for n in range(args.n):
        person = make_person(rng)
        # Hold out the person's most recent answer to one item, and every other
        # year of that same item -- holdout3's `inference` rule.
        keys = sorted({a["key"] for a in person.answers})
        key = rng.choice(keys)
        item = by_key[key]
        mine = [a for a in person.answers if a["key"] == key]
        target = max(mine, key=lambda a: a["year"])
        shown = [a for a in person.answers if a["key"] != key]
        truth = item.options.index(target["answer"]) + 1

        def predict(
            answers: list[dict[str, Any]],
            person: Person = person,
            item: Item = item,
            year: int = target["year"],
        ) -> int | None:
            # Loop variables bound as defaults: a closure over them would read
            # whichever person the loop had reached by call time.
            prompt = build_prompt(person, answers, item, year)
            if args.local:
                return ask_local(prompt, len(item.options))
            assert client is not None
            return ask(client, args.model, prompt, len(item.options))

        full = predict(shown)
        bare = predict([])
        results.append(
            {
                "key": key,
                "truth": truth,
                "profile": full,
                "demographics": bare,
                "n_options": len(item.options),
                "shown": len(shown),
            }
        )
        print(
            f"  {n + 1}/{args.n}  {key:<12} truth {truth}  profile {full}  demo {bare}", flush=True
        )

    def score(arm: str) -> tuple[int, float, float]:
        got = [r for r in results if r[arm] is not None]
        exact = sum(r[arm] == r["truth"] for r in got) / len(got)
        near = sum(abs(r[arm] - r["truth"]) <= 1 for r in got) / len(got)
        return len(got), exact, near

    chance = statistics.fmean(1 / r["n_options"] for r in results)
    ceiling = oracle_ceiling()
    name = LOCAL_MODEL if args.local else args.model
    print(
        f"\nmodel {name} — {len(results)} held-out questions, "
        f"mean {statistics.fmean(r['shown'] for r in results):.0f} answers shown"
    )
    print(f"\n{'arm':<16}{'answered':>10}{'exact':>9}{'within 1':>10}{'of range':>11}")
    print(f"{'chance':<16}{'-':>10}{chance:>8.1%}{'-':>10}{'-':>11}")
    for arm in ("demographics", "profile"):
        got, exact, near = score(arm)
        span = ceiling["exact"] - chance
        share = f"{(exact - chance) / span:>10.0%}" if span > 0 else f"{'-':>11}"
        print(f"{arm:<16}{got:>10}{exact:>8.1%}{near:>9.1%}{share}")
    print(
        f"{'ORACLE ceiling':<16}{ceiling['n']:>10,}{ceiling['exact']:>8.1%}"
        f"{ceiling['within_one']:>9.1%}{'100%':>11}"
    )
    # An arm that failed to answer some questions is scored on a different
    # subset, so the two columns stop being comparable. Said out loud rather
    # than left to be inferred from the `answered` column.
    for arm in ("demographics", "profile"):
        missed = sum(r[arm] is None for r in results)
        if missed:
            print(
                f"\n*** {arm}: {missed} of {len(results)} questions returned no usable "
                f"answer, so its score is over the other {len(results) - missed} ***"
            )
    print(
        "\nA good score here does NOT predict a good score on real data: these people "
        "were generated to be predictable.\nWhat a BAD score here would prove is that "
        "the approach cannot work at all. See the module docstring."
    )


if __name__ == "__main__":
    main()
