#!/usr/bin/env python3
"""Read a holdout3 run and score it between chance and the ceiling, per topic.

holdout3 prints accuracy against chance. That was enough to know 39.0% beat
30.3%, and not enough to know whether 39.0% was any good — and it isn't:
`scripts/ceiling.py` measured that people reproduce their own earlier answer to
the same question only 60.8% of the time, so the winnable band is about 25% to
61% and 39% used a third of it.

Worse, the per-topic lines were actively misleading without ceilings beside
them. Social attitudes offers 5.8 options and a 47.0% ceiling; health offers 3.5
and 74.0%. Reading 25.0% and 31.5% side by side as "both poor" gets the first
roughly right and the second badly wrong — health at 31.5% against a 74%
ceiling is a 42-point hole, which is what the broken whole-topic holdout
actually cost.

So this reports one column that can be compared across topics: **how much of the
range between chance and the ceiling the model captured.** Everything else is
context for it.

    uv run python scripts/scoreboard.py                     # the inference run
    uv run python scripts/scoreboard.py --mode panel

**Where there is no ceiling, this says so and scores nothing.** Personality has
0% coverage — the Big Five was asked once, so nobody has a second answer to
compare — and religion and risk are 1% and 5%. Those topics get a blank, not an
estimate. A quarter of the target pool sits there, which is also why the overall
line is reported twice: once over everything, and once over only the questions
whose ceiling is known.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
PROFILES = REPO / "data" / "profiles"
ARMS = ("demographics", "profile")

# A topic needs enough repeated-measure pairs for its ceiling to mean anything.
# `ceiling.py` reports trust on 42 pairs out of 145 targets (37% coverage); that
# is thin but real. Personality's 0 is not thin, it is absent.
MIN_PAIRS = 30


def accuracy(rows: list[dict[str, Any]], arm: str) -> tuple[int, float | None]:
    got = [r for r in rows if r.get(arm) is not None]
    if not got:
        return 0, None
    return len(got), sum(r[arm] == r["truth"] for r in got) / len(got)


def chance_of(rows: list[dict[str, Any]]) -> float:
    """Mean of 1/k over the questions asked — not 1/mean(k), a different number."""
    return sum(1 / r["n_options"] for r in rows) / len(rows)


def captured(score: float, chance: float, ceiling: float) -> float | None:
    """Share of the gettable range the model took. None where the range is empty.

    Can be negative, and health's -4% under the broken holdout design is the
    reason this is not clamped: a model below chance is telling you something,
    and hiding the sign would have made that look like a small shortfall.
    """
    span = ceiling - chance
    return None if span <= 0 else (score - chance) / span


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", default="inference", choices=("inference", "block", "panel"))
    ap.add_argument("--ceiling", type=Path, help="a ceiling.py --json file (default: recompute)")
    args = ap.parse_args()

    results_path = PROFILES / f"holdout3_results_{args.mode}.json"
    if not results_path.exists():
        raise SystemExit(
            f"no results at {results_path} — run "
            f"`uv run python scripts/holdout3.py --mode {args.mode}` first"
        )
    results: list[dict[str, Any]] = json.loads(results_path.read_text())

    if args.ceiling:
        ceil = json.loads(args.ceiling.read_text())
    else:
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location("ceiling", REPO / "scripts" / "ceiling.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules["ceiling"] = module
        spec.loader.exec_module(module)
        ceil = module.measure()

    ceilings = {
        topic: s["repeat_previous"]
        for topic, s in ceil["by_topic"].items()
        if s.get("n", 0) >= MIN_PAIRS
    }

    print(
        f"MODE {args.mode} — {len(results):,} questions, {len({r['id'] for r in results}):,} people"
    )
    print(
        f"ceiling from {ceil['people']:,} profiles, {ceil['overall']['n']:,} repeated pairs, "
        f"mean gap {ceil['overall']['mean_gap_years']:.1f} years"
    )
    print()
    head = f"{'topic':<20}{'n':>5}{'chance':>8}{'demo':>8}{'profile':>9}{'CEILING':>9}"
    print(head + f"{'demo':>8}{'prof':>7}   <- share of the gettable range")
    print("-" * (len(head) + 15))

    def line(name: str, rows: list[dict[str, Any]], ceiling: float | None) -> None:
        ch = chance_of(rows)
        out = f"{name:<20}{len(rows):>5}{ch:>8.1%}"
        scores = {}
        for arm in ARMS:
            _, acc = accuracy(rows, arm)
            scores[arm] = acc
            out += f"{acc:>8.1%}" if acc is not None else f"{'-':>8}"
        if ceiling is None:
            print(out + f"{'none':>9}{'':>8}{'':>7}   no second answer to compare")
            return
        out += f"{ceiling:>9.1%}"
        for arm in ARMS:
            share = None if scores[arm] is None else captured(scores[arm], ch, ceiling)
            out += f"{share:>8.0%}" if share is not None else f"{'-':>8}"
        print(out)

    topics = sorted(
        {r["topic"] for r in results}, key=lambda t: -len([r for r in results if r["topic"] == t])
    )
    for topic in topics:
        rows = [r for r in results if r["topic"] == topic]
        line(topic, rows, ceilings.get(topic))

    print("-" * (len(head) + 15))
    line("ALL", results, ceil["overall"]["repeat_previous"])
    known = [r for r in results if r["topic"] in ceilings]
    if len(known) != len(results):
        # The honest subtotal. The ALL line above mixes questions whose ceiling is
        # known with questions whose ceiling is not, and its share column is
        # therefore an average over a quantity that does not exist for part of it.
        line("ALL (ceiling known)", known, ceil["overall"]["repeat_previous"])
    print()
    print("CEILING = how often a person's own later answer matches their earlier one.")
    print("The last two columns are the only ones comparable ACROSS topics.")


if __name__ == "__main__":
    main()
