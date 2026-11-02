"""Our quotes against a frontier model's, on the same rows and the same terms (rich, 2 Nov 2026).

    source ~/.bash_profile && uv run python scripts/quotes_frontier.py OUT_DIR [--dry-run]

The claim under test: our pipeline (writer, checker from another model family, rewrites)
writes better quotes than a frontier model given the same row. Fair means:

- Rows at random. N_CELLS experiments drawn at random from the TESS and Dataverse rows
  batch-v9-1 sent through our pipeline, one cell of PER_CELL people who gave the same
  answer to the same condition and outcome in each, whether or not our pipeline produced a
  quote. A row where it did not counts as a loss for ours.
- The same input and instructions. The frontier model gets exactly the messages our writer
  gets for that row: the v9 writer prompt (hard rules, "a sentence or two"), the persona with
  its country line, condition, outcome, answer and the same seeded BES style examples. One
  row per call, one attempt, no checker, no rewrite.
- The same blind judge for every pair: both quotes unlabelled, order random, each graded
  GOOD / WEAK / WRONG under rules that make stating the answer, mentioning the survey or
  reciting the person's details WRONG, and the better one picked.

Two comparisons per row: our FINAL quote (after checks and rewrites; v6) against the
frontier's, which tests the claim; and our FIRST draft (batch-v9-1 round 0, Friday's code)
against the frontier's, which compares the writers alone.

Stated, not fixed: the judge is a Claude model judging a Claude model's quotes, which
favours the frontier side; with 50 rows a share is good to about +/-14 points.

--dry-run replaces every model call with a canned reply and prints one full frontier
prompt, so the selection and the bookkeeping can be checked for nothing.
Writes OUT_DIR/rows.parquet and OUT_DIR/report.json; prints the report.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from micromotives_datasets import embed
from micromotives_datasets import quotes as q

WRITER = "claude-opus-5-5"
JUDGE = "claude-sonnet-5-5"
SEED = 11
RUN_SEED = 3407  # quotes_run.py's default, so the style examples are drawn the same way
N_CELLS = 10
PER_CELL = 5
EXPORT = q.ROOT / "data" / "processed" / "exports" / "v6" / "studies_10pct_quotes"
ROWS = q.ROOT / "data" / "processed" / "exports" / "v3" / "studies_10pct" / "train.parquet"
KEYS = q.ROOT / "data" / "processed" / "quotes" / "batch_v9_1_keys.parquet"
DRAFTS = q.ROOT / "data" / "processed" / "quotes" / "batch-v9-1" / "drafts.parquet"

GRADES = ("GOOD", "WEAK", "WRONG")
JUDGE_SYSTEM = """You judge synthetic quotes: what a real survey respondent might say, out loud, about why they gave their answer. You see the person, what they were shown, the question, their real answer, and two quotes, A and B, written by two different systems. Both were asked for a sentence or two.

Grade each quote:
- GOOD: sounds like this particular person talking, reacts to something specific in what they were shown, fits the direction and strength of their answer, and is the kind of reason a real person gives (gut feeling, habit or a half-wrong belief count as much as a sensible one).
- WEAK: nothing wrong, but bland, generic, tidy or balanced: an average reason anyone might give, or one that sounds written rather than said.
- WRONG: any of these: points the other way from the answer or at the wrong strength; gets the facts of what they were shown wrong; clashes with the person's details; states or describes their own answer ("I gave it a five", "I said no both times", "I'd go down the middle"); mentions the survey, the question or being asked; recites the person's recorded details back ("as a 25-year-old student").

Then pick the better quote: the one a careful reader would more readily believe a real person said. "tie" only when you truly cannot choose.

Reply with JSON only: {"grade_a": "GOOD|WEAK|WRONG", "grade_b": "GOOD|WEAK|WRONG", "better": "A|B|tie", "reason": "one sentence"}"""


def _runner() -> Any:
    spec = importlib.util.spec_from_file_location(
        "quotes_run", q.ROOT / "scripts" / "quotes_run.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SETS = {"dev": 11, "heldout": 29}  # the held-out set is drawn from the experiments dev skips


def pick_rows(which: str) -> pd.DataFrame:
    """Random experiments, one random cell each, from every batch row: passed or not. The
    held-out set never shares an experiment with dev, and is only looked at to confirm a
    version that has already won on dev (rich, 2 Nov 2026)."""
    rows = pd.read_parquet(ROWS)
    rows = rows.merge(pd.read_parquet(KEYS)[q.ROW_KEY], on=q.ROW_KEY, validate="one_to_one")
    rows = rows[rows["source"].isin(["tess", "dataverse"])]
    cells = {
        recipe: [
            g
            for _, g in r.groupby(["factors", "outcome", "response"], sort=True)
            if len(g) >= PER_CELL
        ]
        for recipe, r in rows.groupby("recipe", sort=True)
    }
    cells = {k: v for k, v in cells.items() if v}

    def draw(seed: int, recipes: list[str]) -> pd.DataFrame:
        rng = random.Random(seed)
        picked = []
        for recipe in sorted(rng.sample(recipes, N_CELLS)):
            cell = cells[recipe][rng.randrange(len(cells[recipe]))]
            picked.append(cell.sample(PER_CELL, random_state=seed).assign(cell=recipe))
        return pd.concat(picked, ignore_index=True)

    dev = draw(SETS["dev"], sorted(cells))
    if which == "dev":
        return dev
    return draw(SETS["heldout"], sorted(set(cells) - set(dev["cell"])))


def attach_ours(rows: pd.DataFrame, run_dir: Path | None) -> pd.DataFrame:
    """Our final quote (passed only) and our first draft, from a run folder or, without one,
    from v6 and batch-v9-1. A row with no passing quote keeps none."""
    rows = rows.drop(columns=["quote"], errors="ignore")
    if run_dir is None:
        final = pd.read_parquet(EXPORT / "train.parquet", columns=[*q.ROW_KEY, "quote"])
        drafts = pd.read_parquet(DRAFTS)
    else:
        table = pd.read_parquet(run_dir / "quotes.parquet")
        final = table[table["passed"].astype(bool)][[*q.ROW_KEY, "quote"]]
        drafts = pd.read_parquet(run_dir / "drafts.parquet")
    rows = rows.merge(final, on=q.ROW_KEY, how="left", validate="one_to_one")
    first = drafts[drafts["round"] == 0][[*q.ROW_KEY, "quote"]].rename(
        columns={"quote": "first_draft"}
    )
    return rows.merge(first, on=q.ROW_KEY, how="left", validate="one_to_one")


def case_text(row: pd.Series) -> str:
    return (
        f"About this person:\n{q.with_country(row['persona_text'], row['source'])}\n\n"
        f"What the study put to them:\n{row['condition']}\n\n"
        f"The question:\n{row['outcome']}\n\n"
        f"Their answer: {row['response']}"
    )


SET_JUDGE_SYSTEM = """You judge two sets of synthetic quotes. Each set was written for the same group of different real people, who were all shown the same thing, asked the same question and gave the same answer. Real people who give the same answer still give different reasons, in different voices, and notice different things.

Pick the set that sounds more like that many different real people: distinct reasons, distinct voices, nobody echoing anyone else. Variety only counts when every quote is still a believable reason for that answer from that person; a set made odd for the sake of it does not win. "tie" only when you truly cannot choose.

Reply with JSON only: {"better": "A|B|tie", "reason": "one sentence"}"""


def judge_set(
    ask: Callable[[str, str, str, int], str], cell: pd.DataFrame, ours_col: str, flip: bool
) -> dict[str, Any]:
    """One blind verdict on a whole cell: which set sounds like different people (rich,
    2 Nov 2026: a set of near-identical good quotes is wrong as a population). Fewer than
    two quotes of ours is a loss, unjudged."""
    ours = [
        (p, t)
        for p, t in zip(cell["persona_text"], cell[ours_col], strict=True)
        if isinstance(t, str)
    ]
    theirs = [
        (p, t)
        for p, t in zip(cell["persona_text"], cell["frontier"], strict=True)
        if isinstance(t, str)
    ]
    if len(ours) < 2:
        return {"better": "theirs", "reason": "fewer than two quotes of ours"}

    def block(quotes: list[tuple[str, str]]) -> str:
        return "\n".join(
            f"- ({p.splitlines()[0]}; {p.splitlines()[1] if len(p.splitlines()) > 1 else ''}) {t}"
            for p, t in quotes
        )

    first = cell.iloc[0]
    head = (
        f"What they were all shown:\n{first['condition']}\n\nThe question:\n{first['outcome']}\n\n"
        f"The answer they all gave: {first['response']}"
    )
    a, b = (theirs, ours) if flip else (ours, theirs)
    user = f"{head}\n\nSet A:\n{block(a)}\n\nSet B:\n{block(b)}"
    for attempt in range(3):
        text = ask(JUDGE, SET_JUDGE_SYSTEM, user, attempt)
        try:
            verdict = json.loads(text[text.index("{") : text.rindex("}") + 1])
        except ValueError:
            continue
        if verdict.get("better") in ("A", "B", "tie"):
            winner = {
                "A": "theirs" if flip else "ours",
                "B": "ours" if flip else "theirs",
                "tie": "tie",
            }
            return {"better": winner[verdict["better"]], "reason": verdict.get("reason", "")}
    return {"better": "unreadable", "reason": ""}


def judge_pair(
    ask: Callable[[str, str, str, int], str],
    row: pd.Series,
    ours: str | None,
    theirs: str,
    flip: bool,
) -> dict[str, Any]:
    """One blind verdict, mapped back to ours/theirs. No quote of ours is a loss, unjudged."""
    if not isinstance(ours, str) or not ours.strip():
        return {
            "grade_ours": "MISSING",
            "grade_theirs": None,
            "better": "theirs",
            "reason": "no quote of ours",
        }
    if not isinstance(theirs, str) or not theirs.strip():
        return {
            "grade_ours": None,
            "grade_theirs": "MISSING",
            "better": "ours",
            "reason": "no frontier quote",
        }
    a, b = (theirs, ours) if flip else (ours, theirs)
    user = f"{case_text(row)}\n\nQuote A:\n{a}\n\nQuote B:\n{b}"
    for attempt in range(3):  # a reply missing a field is asked again, never guessed
        text = ask(JUDGE, JUDGE_SYSTEM, user, attempt)
        try:
            verdict = json.loads(text[text.index("{") : text.rindex("}") + 1])
        except ValueError:
            continue
        if verdict.get("better") in ("A", "B", "tie") and all(
            verdict.get(k) in GRADES for k in ("grade_a", "grade_b")
        ):
            break
    else:
        return {"grade_ours": None, "grade_theirs": None, "better": "unreadable", "reason": ""}
    ours_key, theirs_key = ("b", "a") if flip else ("a", "b")
    winner = {"A": "theirs" if flip else "ours", "B": "ours" if flip else "theirs", "tie": "tie"}
    return {
        "grade_ours": verdict[f"grade_{ours_key}"],
        "grade_theirs": verdict[f"grade_{theirs_key}"],
        "better": winner[verdict["better"]],
        "reason": verdict.get("reason", ""),
    }


def variety(texts: list[str], cells: list[str], tag: str, dry: bool) -> dict[str, float]:
    frame = pd.DataFrame({"cell": cells, "text": texts}).dropna().reset_index(drop=True)
    if dry:
        vec = np.random.default_rng(0).normal(size=(len(frame), 8))
    else:
        items = [embed.Text(f"{tag}{i}", t, "synthetic-quote") for i, t in enumerate(frame["text"])]
        got = embed.embed(items)
        vec = np.asarray([got[f"{tag}{i}"] for i in range(len(frame))], dtype=float)
    spreads, dups, vendis = [], [], []
    for _, g in frame.groupby("cell"):
        if len(g) < 2:
            continue
        e = vec[g.index]
        spreads.append(q.spread(e))
        dups.append(q.near_duplicate_share(e))
        vendis.append(q.vendi(e) / len(g))
    return {
        "spread": round(float(np.mean(spreads)), 3),
        "near_duplicate_share": round(float(np.mean(dups)), 3),
        "vendi_per_quote": round(float(np.mean(vendis)), 3),
    }


def share(series: pd.Series) -> dict[str, float]:
    return {str(k): round(float(v), 2) for k, v in series.value_counts(normalize=True).items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    ap.add_argument("--set", choices=sorted(SETS), default="dev")
    ap.add_argument("--version", default="v9", help="writer prompt both sides get")
    ap.add_argument("--ours", type=Path, help="our quote run for these rows (default: v6)")
    ap.add_argument("--keys", type=Path, help="write the set's row keys here and stop")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = pick_rows(args.set)
    if args.keys:
        rows[q.ROW_KEY].to_parquet(args.keys, index=False)
        print(f"{len(rows)} {args.set} row keys -> {args.keys}")
        return
    rows = attach_ours(rows, args.ours)
    run = _runner()
    pool = q.VoicePool.load()
    items = run.build_items(rows, "full_persona", RUN_SEED, pool, angles=False)
    system, _ = q.load_prompt(f"writer_{args.version}.md")
    messages = [q.writer_messages(system, [it]) for it in items]

    if args.dry_run:
        print(messages[0][1]["content"], "\n")

        def ask(model: str, sys: str, user: str, attempt: int = 0) -> str:
            if model == WRITER:
                return '{"quotes": ["A dry-run quote."]}'
            if attempt == 0 and len(user) % 3 == 0:
                return '{"grade_a": "GOOD", "grade_b": "WEAK"}'  # the reply that crashed the run
            return '{"grade_a": "GOOD", "grade_b": "WEAK", "better": "A", "reason": "dry run"}'

        def write(m: list[dict[str, str]]) -> str | None:
            got = q.parse_quotes(ask(WRITER, m[0]["content"], m[1]["content"]), 1)
            return got[0] if got else None
    else:
        import anthropic

        client = anthropic.Anthropic()

        cache = args.out / "cache"
        cache.mkdir(parents=True, exist_ok=True)

        def ask(model: str, sys: str, user: str, attempt: int = 0) -> str:
            # every reply is kept on disk the moment it arrives, so a rerun after a crash
            # pays only for what it has not got yet
            key = hashlib.sha256(f"{model}\n{attempt}\n{sys}\n{user}".encode()).hexdigest()
            path = cache / f"{key}.txt"
            if path.exists():
                return path.read_text()
            reply = client.messages.create(
                model=model,
                max_tokens=2000,
                system=sys,
                messages=[{"role": "user", "content": user}],
                output_config={"effort": "low"},
            )
            text = "".join(b.text for b in reply.content if b.type == "text").strip()
            path.write_text(text)
            return text

        def write(m: list[dict[str, str]]) -> str | None:
            for attempt in range(3):  # our writer gets the same: one retry and then some
                text = ask(WRITER, m[0]["content"], m[1]["content"], attempt)
                got = q.parse_quotes(text[text.find("{") : text.rfind("}") + 1], 1)
                if got:
                    return got[0]
            return None

    with ThreadPoolExecutor(8) as ex:
        rows["frontier"] = list(ex.map(write, messages))
        flips = [random.Random(SEED + i).random() < 0.5 for i in range(len(rows))]
        final = list(
            ex.map(
                lambda i: judge_pair(
                    ask, rows.iloc[i], rows.iloc[i]["quote"], rows.iloc[i]["frontier"], flips[i]
                ),
                range(len(rows)),
            )
        )
        first = list(
            ex.map(
                lambda i: judge_pair(
                    ask,
                    rows.iloc[i],
                    rows.iloc[i]["first_draft"],
                    rows.iloc[i]["frontier"],
                    not flips[i],
                ),
                range(len(rows)),
            )
        )
        cells = [g for _, g in rows.groupby("cell", sort=True)]
        sets = list(
            ex.map(
                lambda k: (
                    {"cell": cells[k]["cell"].iloc[0]}
                    | judge_set(ask, cells[k], "quote", random.Random(SEED * 7 + k).random() < 0.5)
                ),
                range(len(cells)),
            )
        )
    rows = pd.concat(
        [rows, pd.DataFrame(final).add_prefix("final_"), pd.DataFrame(first).add_prefix("first_")],
        axis=1,
    )
    sets_frame = pd.DataFrame(sets)
    args.out.mkdir(parents=True, exist_ok=True)
    rows.to_parquet(args.out / "rows.parquet", index=False)
    sets_frame.to_parquet(args.out / "sets.parquet", index=False)

    def words(col: str) -> float:
        return float(rows[col].dropna().str.split().str.len().median())

    def tells(col: str) -> float:
        return round(float(rows[col].dropna().map(q.ai_tells).map(bool).mean()), 2)

    report = {
        "dry_run": args.dry_run,
        "set": args.set,
        "prompt_version": args.version,
        "ours": str(args.ours or "v6 export"),
        "rows": len(rows),
        "experiments": sorted(rows["cell"].unique()),
        "ours_missing": int(rows["quote"].isna().sum()),
        "judge_unreadable": int(
            (rows[["final_better", "first_better"]] == "unreadable").sum().sum()
        ),
        "frontier_unusable": int(rows["frontier"].isna().sum()),
        "writer": WRITER,
        "judge": JUDGE,
        "final_vs_frontier": {
            "better": share(rows["final_better"]),
            "grades_ours": share(rows["final_grade_ours"]),
            "grades_frontier": share(rows["final_grade_theirs"].dropna()),
        },
        "first_draft_vs_frontier": {
            "better": share(rows["first_better"]),
            "grades_ours": share(rows["first_grade_ours"]),
            "grades_frontier": share(rows["first_grade_theirs"].dropna()),
        },
        "median_words": {
            "final": words("quote"),
            "first_draft": words("first_draft"),
            "frontier": words("frontier"),
        },
        "diversity_set_judge": {
            "better": share(sets_frame["better"]),
            "by_cell": dict(zip(sets_frame["cell"], sets_frame["better"], strict=True)),
        },
        "code_tells": {
            "final": tells("quote"),
            "first_draft": tells("first_draft"),
            "frontier": tells("frontier"),
        },
        "variety": {
            "final": variety(rows["quote"].tolist(), rows["cell"].tolist(), "f", args.dry_run),
            "frontier": variety(
                rows["frontier"].tolist(), rows["cell"].tolist(), "t", args.dry_run
            ),
        },
        "caveats": "judge is Claude judging a Claude writer (favours the frontier); 50 rows: about +/-14 points",
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
