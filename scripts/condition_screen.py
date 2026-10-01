#!/usr/bin/env python3
"""Read every built condition and ask whether it tells the respondent the truth.

The defect that has cost this project the most is a condition asserting
something the respondent could not have known when they answered: `b87sm`'s
"Scenario #1" on 13,513 rows that were rating scenarios 2-8, `es4xw`'s "in this
version" on 32,228, `sh4px` narrating a writing task that had not happened yet,
`a2nbf`'s unresolved `{you/your partner}` on 3,117. Every one passed all sixteen
QC rules, reconciled to the row against the reference set, and was found by a
human reading a single row and asking whether it said something true.

There is no unit test for "could they have known this". It is the one question in
the build that is irreducibly semantic, and it is the question we had never put
to Jev — which was being spent instead on variable selection, where it has a
documented blind spot and where no shipped defect has ever originated.

The economics are what make this worth doing. 247,086 rows contain only
**308 distinct hand-written condition strings**; the two conjoints' 13,106 arms
are generated from attribute tables, so a sample covers their template. At that
size a mediocre hit rate is fine and false positives cost one glance each,
because every flag goes to a human. That is the opposite of the per-study prep
use, where a confident wrong answer gets written into a recipe and ships.

    source ~/.bash_profile && uv run python scripts/condition_screen.py
    source ~/.bash_profile && uv run python scripts/condition_screen.py --study b87sm
    uv run python scripts/condition_screen.py --reuse      # re-render, no calls

Answers are cached by content hash, so a re-run after fixing one study pays only
for what changed. On the wire: the rendered condition and the outcome question,
both instrument text. Never a persona, a response, or a respondent row.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd

from micromotives_datasets import jev

REPO = Path(__file__).resolve().parents[1]
BUILT = REPO / "data" / "processed"
CACHE = REPO / "data" / "catalog" / "condition_screen.json"
OUT = REPO / "docs" / "CONDITION_SCREEN.md"

# Above this many distinct conditions a study is sampled rather than read whole.
# Only the conjoints exceed it, and their arms are mechanically generated from an
# attribute table — the template repeats, so a sample tests the same prose. The
# sample is deterministic so a re-run screens the same strings and the cache hits.
SAMPLE_ABOVE = 60


def key_of(condition: str, outcome: str) -> str:
    return hashlib.sha256(f"{condition}\x00{outcome}".encode()).hexdigest()[:16]


def pairs_for(path: Path) -> tuple[list[tuple[str, str]], bool]:
    """Distinct (condition, outcome) pairs in one built file, and whether sampled."""
    d = pd.read_parquet(path, columns=["condition", "outcome"]).drop_duplicates()
    d = d.sort_values(["condition", "outcome"]).reset_index(drop=True)
    sampled = len(d) > SAMPLE_ABOVE
    if sampled:
        d = d.sample(n=SAMPLE_ABOVE, random_state=0).sort_index()
    return list(d.itertuples(index=False, name=None)), sampled


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", action="append", default=[], help="limit to these built files")
    ap.add_argument("--limit", type=int, default=0, help="stop after this many NEW calls")
    ap.add_argument("--reuse", action="store_true", help="re-render from cache, call nothing")
    args = ap.parse_args()

    cache: dict[str, dict[str, Any]] = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    files = sorted(BUILT.glob("*.parquet"))
    if args.study:
        files = [f for f in files if any(s in f.stem for s in args.study)]
    if not files:
        print("no built files matched — build something first")
        return 1

    cli = None if args.reuse else jev.client()
    flags: list[jev.ConditionFlag] = []
    calls = 0
    totals: dict[str, tuple[int, bool]] = {}

    for path in files:
        study = path.stem
        pairs, sampled = pairs_for(path)
        totals[study] = (len(pairs), sampled)
        for condition, outcome in pairs:
            k = key_of(condition, outcome)
            if k not in cache:
                if args.reuse:
                    continue
                if args.limit and calls >= args.limit:
                    continue
                flag = jev.screen_condition(cli, condition, outcome, study=study)
                # Verdict only. Storing the excerpt too took the cache to 944KB for
                # 1,002 entries, and the excerpt is already in the parquet — a cache
                # that duplicates its source grows without earning anything.
                cache[k] = {"defect": asdict(flag.defect), "defect_mass": flag.defect_mass}
                calls += 1
            rec = cache[k]
            flag = jev.ConditionFlag(
                defect=jev.Verdict(**rec["defect"]),
                defect_mass=rec["defect_mass"],
                study=study,
                outcome=outcome[:200],
                excerpt=condition[:400],
            )
            if flag.needs_review:
                flags.append(flag)
        print(f"{study:34} {len(pairs):5} pairs{'  (sampled)' if sampled else ''}")

    if not args.reuse:
        CACHE.write_text(json.dumps(cache, indent=1))

    screened = sum(n for n, _ in totals.values())
    lines = [
        "# Condition screen — does each built condition tell the respondent the truth?",
        "",
        "<!-- GENERATED by scripts/condition_screen.py — do not edit by hand. -->",
        "",
        f"{screened} distinct (condition, outcome) pairs screened across "
        f"{len(totals)} built experiments. **{len(flags)} need a human.**",
        "",
        "A flag is a question, not a finding. The screen cannot read the "
        "questionnaire, so it cannot know what the respondent actually saw — it can "
        "only notice that a text asserts something a respondent would be unlikely to "
        "know. Check each against the source before changing anything.",
        "",
    ]
    if flags:
        lines += ["| study | class | conf | defect mass | excerpt |", "|---|---|---|---|---|"]
        for f in sorted(flags, key=lambda x: (x.study, -x.defect_mass)):
            ex = f.excerpt[:90].replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| `{f.study}` | {f.defect.value} | {f.defect.confidence:.2f} "
                f"| {f.defect_mass:.2f} | {ex} |"
            )
        lines.append("")
    for study, (n, sampled) in sorted(totals.items()):
        if sampled:
            lines.append(
                f"- `{study}` has more than {SAMPLE_ABOVE} distinct conditions and was "
                f"**sampled** ({n} screened). Its arms are generated from an attribute "
                f"table, so the prose repeats — but this is a sample, not a clean bill."
            )
    OUT.write_text("\n".join(lines) + "\n")

    print(f"\n{calls} new calls, {screened} pairs screened, {len(flags)} flagged")
    print(f"wrote {OUT.relative_to(REPO)}")
    for f in sorted(flags, key=lambda x: -x.defect_mass)[:15]:
        print("\n" + f.render())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
