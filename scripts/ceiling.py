#!/usr/bin/env python3
"""How reproducible is a person's own survey answer? The ceiling for holdout3.

`scripts/holdout3.py` scores a model on predicting a person's MOST RECENT answer
to a question held out of their profile. Its last reported numbers were profile
39.0%, demographics 36.2%, chance 30.3% — and nobody could say whether 39% was
good, because there was nothing to compare it against except chance.

This supplies the missing end of the scale, and needs no model. The Innovation
Panel asks the same questions wave after wave, so for most held-out targets the
same person answered the same question a year or two earlier. **How often their
latest answer matches their previous one is how much of the answer is
reproducible at all.**

It came out of building IP 9.10, where the design happens to show the same
person the identical made-up scenario a year apart: there, people gave the same
answer only 27.7% of the time on a 7-point scale, against 14.8% chance. The
entire winnable band was eight points wide. That is a fact about survey answers,
not about that one study, which is why it is worth knowing here before spending
an hour of model time.

**WHAT THIS NUMBER IS AND IS NOT.** It is a measure of reproducibility, not a
hard upper bound. Two reasons to be careful with it:

- A changed answer can be a REAL change — someone's health or politics genuinely
  moved — and a model holding the rest of their profile could in principle
  predict that better than assuming no change. So a model scoring above this
  line is not automatically broken.
- But a model scoring FAR above it is predicting something more stable than the
  person's own repeat answer, which deserves suspicion rather than celebration,
  and a model scoring near chance while this line sits near chance too has not
  failed at anything that was available.

So: read it as the top of the plausible range, printed next to chance, with the
model's score between them. `repeat_previous` is simultaneously the ceiling
estimate and the baseline holdout3 must beat — assuming no change is exactly
what a lazy predictor does.

    uv run python scripts/ceiling.py
    uv run python scripts/ceiling.py --json          # machine-readable
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
HOLDOUT = REPO / "scripts" / "holdout3.py"
PROFILES = REPO / "data" / "profiles"


def _holdout() -> Any:
    """Import holdout3 for its grouping rules, rather than restating them.

    The grouping is the load-bearing judgment here — `group_key`, `variable_root`
    and `usable` are what decide that `a_sf2a` and `c_scsf2a` are one question
    renamed mid-panel, and what keep fed-forward columns out. Restating any of it
    would let this script measure a ceiling for a question holdout3 does not ask.
    """
    spec = importlib.util.spec_from_file_location("holdout3", HOLDOUT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["holdout3"] = module
    spec.loader.exec_module(module)
    return module


def measure(limit: int | None = None) -> dict[str, Any]:
    h = _holdout()
    paths = sorted(PROFILES.glob("ip_*.json"))
    if limit:
        paths = paths[:limit]
    if not paths:
        raise SystemExit(f"no profiles in {PROFILES} — run scripts/build_profiles.py first")
    profiles = [json.loads(p.read_text()) for p in paths]

    # The option set per question, pooled across everyone, exactly as holdout3
    # builds it: chance depends on how many options the question offers, and that
    # is only knowable from the whole sample.
    pooled: dict[str, list[tuple[int | None, str]]] = defaultdict(list)
    for p in profiles:
        for a in p["answers"]:
            if h.usable(a):
                pooled[h.group_key(a)].append((a.get("code"), a["answer"]))

    # One row per (person, question) that the person answered in two or more
    # waves: their latest answer, their previous one, and the option set.
    rows: list[dict[str, Any]] = []
    for p in profiles:
        by_key: dict[str, list[dict]] = defaultdict(list)
        for a in p["answers"]:
            if h.usable(a):
                by_key[h.group_key(a)].append(a)
        for key, answers in by_key.items():
            options = h.option_list(pooled[key])
            if not options or len(options) < 2:
                continue
            years = sorted({a["year"] for a in answers})
            if len(years) < 2:
                continue
            latest = max(answers, key=lambda a: a["year"])
            # The most recent year STRICTLY before the target year. Several
            # answers can share a year when a question was asked in two modes;
            # any of them is that year's answer, so the first is taken.
            previous = max(
                (a for a in answers if a["year"] < latest["year"]), key=lambda a: a["year"]
            )
            now, before = h.canonical(latest["answer"]), h.canonical(previous["answer"])
            if now not in options or before not in options:
                continue
            rows.append(
                {
                    "topic": latest["topic"],
                    "gap_years": latest["year"] - previous["year"],
                    "same": now == before,
                    "options": len(options),
                    "index_now": options.index(now),
                    "index_before": options.index(before),
                }
            )

    def summarise(subset: list[dict[str, Any]]) -> dict[str, Any]:
        if not subset:
            return {}
        n = len(subset)
        # Chance per question is 1/k for its own k, averaged over the questions
        # actually asked — not 1/mean(k), which is a different and smaller number.
        chance = statistics.fmean(1 / r["options"] for r in subset)
        steps = [abs(r["index_now"] - r["index_before"]) for r in subset]
        return {
            "n": n,
            "repeat_previous": sum(r["same"] for r in subset) / n,
            "chance": chance,
            "within_one_option": statistics.fmean(s <= 1 for s in steps),
            "mean_options": statistics.fmean(r["options"] for r in subset),
            "mean_gap_years": statistics.fmean(r["gap_years"] for r in subset),
        }

    by_topic = {}
    for topic in sorted({r["topic"] for r in rows}):
        by_topic[topic] = summarise([r for r in rows if r["topic"] == topic])

    return {
        "people": len(profiles),
        "overall": summarise(rows),
        "by_topic": by_topic,
        "gap_distribution": dict(sorted(Counter(r["gap_years"] for r in rows).items())),
    }


def report(result: dict[str, Any]) -> None:
    o = result["overall"]
    print(
        f"{result['people']:,} people, {o['n']:,} (person, question) pairs answered in "
        f"two or more waves"
    )
    print(f"mean gap between the two answers: {o['mean_gap_years']:.1f} years")
    print()
    print(f"{'':<22}{'n':>8}{'chance':>9}{'CEILING':>9}{'±1 opt':>9}{'options':>9}")
    print(
        f"{'overall':<22}{o['n']:>8,}{o['chance']:>8.1%}{o['repeat_previous']:>9.1%}"
        f"{o['within_one_option']:>9.1%}{o['mean_options']:>9.1f}"
    )
    print()
    for topic, s in sorted(result["by_topic"].items(), key=lambda kv: -kv[1]["n"]):
        print(
            f"  {topic:<20}{s['n']:>8,}{s['chance']:>8.1%}{s['repeat_previous']:>9.1%}"
            f"{s['within_one_option']:>9.1%}{s['mean_options']:>9.1f}"
        )
    print()
    print("CEILING = how often a person's latest answer matches their own previous one.")
    print("Read the model's score between `chance` and `CEILING`, not against chance alone.")
    print("It is an estimate of reproducibility, not a hard bound — see the module docstring.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, help="use only the first N profiles")
    ap.add_argument("--json", action="store_true", help="print the numbers as JSON")
    args = ap.parse_args()
    result = measure(args.limit)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        report(result)


if __name__ == "__main__":
    main()
