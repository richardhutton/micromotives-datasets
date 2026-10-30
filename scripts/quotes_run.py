"""Write, check and repair synthetic quotes for training rows, calling the RunPod pod.

Runs here; the models run on the pod, ONE AT A TIME with the whole GPU, behind a router
that switches between them on request (scripts/quotes_router.py, docs/RUNPOD_QUOTES.md).
Design: docs/QUOTES_SPEC.md; the pure parts are in micromotives_datasets.quotes and
unit-tested.

    source ~/.bash_profile && uv run python scripts/quotes_run.py ROWS.parquet OUT_DIR \\
        --url https://<pod id>-4000.proxy.runpod.net --setting full_persona \\
        [--keys pilot_keys.parquet] [--existing RUN_DIR ...] [--limit N]
    ... quotes_run.py ROWS.parquet OUT_DIR --resume      # carry on a stopped run

ROWS is an export's train.parquet; rows from a study the split holds out are refused,
since a quote written from the real response would leak it. QUOTES_API_KEY comes from
the environment.

Phases, each starting with the router switching to the model it needs:

    written      writer   write every quote
    checked 0    checker  check every quote
    rewritten 1  writer   rewrite the ones that failed, with the checker's notes
    checked 1    checker  check the rewrites
    rewritten 2, checked 2, then done

OUT_DIR gets quotes.parquet (TABLE_COLUMNS) and run.json after EVERY phase. --resume
reads them back and carries on from the phase after the last one saved, on exactly the
rows that run started with. Progress is printed as calls complete; counts only.

Settings (QUOTES_SPEC section 10), each adding to the one before:
    sampling       persona_text only; no angle, no voice
    angle_voice    plus a drawn reason angle per row and voice per respondent
    full_persona   plus every recorded persona field instead of persona_text
    group          plus k respondents sharing (recipe, factors, outcome, response) per call
All but `group` write one respondent's rows in a study together (section 6).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

from micromotives_datasets import quotes as q

SETTINGS = ["sampling", "angle_voice", "full_persona", "group"]
# v2 (30 Oct 2026, rich): invented details allowed if they fit the person; a clash fails.
# v3 (30 Oct 2026, rich, from batch 1's rejects): unreasoned reasons react to the condition,
# never to filling in the survey; no answer talk in words either; figures from the
# condition are not giveaways; react to named features of a profile.
# v4 (30 Oct 2026, rich, after the independent read found 55% generic): react to one
# concrete thing in the condition (swap test), never name the angle, no tidy balance, a
# strength cue per answer, terse voices capped at ten words, invented details only about
# the person; the checker works out direction and strength from the scale labels first.
PROMPT_VERSION = "v4"


def prompt_version_of(manifest: dict[str, Any]) -> str:
    """The prompt version a saved run used, so a resumed run never mixes two."""
    if "prompt_version" in manifest:
        return str(manifest["prompt_version"])
    names = list(manifest.get("prompts", {}))
    return names[0].rsplit("_", 1)[1].removesuffix(".md") if names else PROMPT_VERSION


MAX_ITEMS = 6  # rows per writer call: keeps each reply well inside the proxy's timeout
PROMPT_BUDGET = 6000  # estimated prompt tokens per writer call; the servers allow 16,384
CHARS_PER_TOKEN = 3.5  # deliberately low, so the estimate errs towards smaller calls
TOKENS_PER_QUOTE = 150
GROUP_K = 5  # QUOTES_SPEC section 11
REPAIR_ROUNDS = 2  # QUOTES_SPEC section 11
SPLIT = q.ROOT / "data" / "catalog" / "splits" / "studies_mapping.json"

# Qwen3.8 non-thinking settings, from the model card (checked 30 Oct 2026).
WRITER_SAMPLING = {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "min_p": 0.0,
    "presence_penalty": 1.5,
    "chat_template_kwargs": {"enable_thinking": False},
}
# A judge should be repeatable. Gemma 4's thinking is on only with <|think|> in the
# system prompt, which the checker prompts never contain.
CHECKER_SAMPLING = {"temperature": 0.0}
BLIND_SCHEMA = {
    "type": "object",
    "properties": {"answer": {"type": "number"}},
    "required": ["answer"],
}


class Server:
    """One model behind the router. A request that still fails after retries returns ""
    (counted, and treated like an unusable reply) instead of stopping the run."""

    RETRIES = 4

    def __init__(self, url: str, model: str, sampling: dict[str, Any], http: httpx.Client) -> None:
        self.url = url.rstrip("/")
        self.model = model
        self.sampling = sampling
        self.http = http
        self.failures: Counter[str] = Counter()
        self.root = ""  # the Hugging Face id, filled in when the pod switches to it

    def chat(self, messages: list[dict[str, str]], schema: dict[str, Any], max_tokens: int) -> str:
        body = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "reply", "schema": schema},
            },
            **self.sampling,
        }
        for attempt in range(self.RETRIES):
            try:
                r = self.http.post(f"{self.url}/v1/chat/completions", json=body)
            except httpx.HTTPError as e:
                reason = type(e).__name__
            else:
                if r.status_code == 200:
                    return str(r.json()["choices"][0]["message"]["content"] or "")
                reason = f"http {r.status_code}"
                if 400 <= r.status_code < 500 and r.status_code not in (408, 429):
                    break  # the request itself is wrong (e.g. too long): retrying won't help
            time.sleep(2**attempt)
        self.failures[reason] += 1
        return ""


class Pod:
    """The router's switch: one model loaded at a time, the whole GPU to it."""

    POLL = 10.0
    TIMEOUT = 50 * 60

    def __init__(self, url: str, http: httpx.Client) -> None:
        self.url = url.rstrip("/")
        self.http = http

    def state(self) -> dict[str, Any]:
        r = self.http.get(f"{self.url}/admin/state")
        r.raise_for_status()
        return dict(r.json())

    def use(self, model: str) -> dict[str, Any]:
        """Switch to `model` and wait until it answers; stop the run if it fails to start."""
        state = self.state()
        if state["model"] == model and state["status"] == "ready":
            return state
        started = time.monotonic()
        self.http.post(f"{self.url}/admin/switch", json={"model": model}).raise_for_status()
        seen = None
        while time.monotonic() - started < self.TIMEOUT:
            state = self.state()
            if state["model"] == model and state["status"] != seen:
                seen = state["status"]
                print(f"  pod: {model} {seen} ({time.monotonic() - started:.0f}s)", flush=True)
            if state["model"] == model and state["status"] == "ready":
                return state
            if state["model"] == model and state["status"] == "failed":
                raise SystemExit(f"{model} failed to start on the pod: {state.get('error')}")
            time.sleep(self.POLL)
        raise SystemExit(f"{model} not ready after {self.TIMEOUT / 60:.0f} minutes")


def run_parallel[T](
    pool: ThreadPoolExecutor, fn: Callable[[int], T], todo: Sequence[int], label: str
) -> dict[int, T]:
    """fn over todo on the pool, printing progress as calls complete."""
    out: dict[int, T] = {}
    if not todo:
        return out
    every = max(200, len(todo) // 20)
    started = time.monotonic()
    futures = {pool.submit(fn, i): i for i in todo}
    for n, future in enumerate(as_completed(futures), 1):
        out[futures[future]] = future.result()
        if n % every == 0 or n == len(todo):
            rate = n / max(time.monotonic() - started, 1e-9)
            left = (len(todo) - n) / rate if rate else 0
            print(
                f"  {label}: {n} of {len(todo)}  ({rate:.1f}/s, ~{left / 60:.0f} min left)",
                flush=True,
            )
    return out


def est_tokens(text: str) -> int:
    return int(len(text) / CHARS_PER_TOKEN) + 1


def item_tokens(item: q.Item) -> int:
    return est_tokens(item.condition) + est_tokens(item.outcome) + 60


def build_items(rows: pd.DataFrame, setting: str, seed: int) -> list[q.Item]:
    items = []
    for _, row in rows.iterrows():
        key = q.row_key(row)
        drawn = setting != "sampling"
        persona = (
            q.persona_lines(row["persona"])
            if setting in ("full_persona", "group")
            else row["persona_text"]
        )
        items.append(
            q.Item(
                key=key,
                participant_id=row["participant_id"],
                persona=persona,
                condition=row["condition"],
                outcome=row["outcome"],
                response=str(row["response"]),
                scale_min=int(row["scale_min"]),
                scale_max=int(row["scale_max"]),
                angle=q.draw_angle(seed, key) if drawn else None,
                voice=q.draw_voice(seed, row["study"], row["participant_id"]) if drawn else None,
            )
        )
    return items


def plan_calls(rows: pd.DataFrame, items: list[q.Item], setting: str) -> list[list[int]]:
    """Positions of the items written together, one list per call. Every item is in
    exactly one call; a call holds at most MAX_ITEMS and stays within PROMPT_BUDGET
    (a single item over budget still gets a call of its own)."""
    calls: list[list[int]] = []
    left = list(range(len(rows)))
    if setting == "group":
        used: set[int] = set()
        for _, g in rows.groupby(["recipe", "factors", "outcome", "response"], sort=True):
            # one row per respondent in a group call, so k different people
            firsts = [rows.index.get_loc(i) for i in g.drop_duplicates("participant_id").index]
            for start in range(0, len(firsts) - len(firsts) % GROUP_K, GROUP_K):
                chunk = firsts[start : start + GROUP_K]
                persona_cost = sum(est_tokens(items[i].persona) for i in chunk)
                if persona_cost + sum(item_tokens(items[i]) for i in chunk) > PROMPT_BUDGET:
                    continue  # too long to write together; these go to their own calls
                calls.append(chunk)
                used.update(chunk)
        left = [i for i in left if i not in used]
    rest = rows.iloc[left]
    for _, person in rest.groupby(["study", "participant_id"], sort=True):
        ordered = [
            rows.index.get_loc(i) for i in person.sort_values(["condition_num", "task_num"]).index
        ]
        budget = PROMPT_BUDGET - est_tokens(items[ordered[0]].persona)
        call: list[int] = []
        used_tokens = 0
        for i in ordered:
            cost = item_tokens(items[i])
            if call and (len(call) == MAX_ITEMS or used_tokens + cost > budget):
                calls.append(call)
                call, used_tokens = [], 0
            call.append(i)
            used_tokens += cost
        calls.append(call)
    return calls


def write_call(writer: Server, system: str, items: Sequence[q.Item]) -> list[str | None]:
    messages = q.writer_messages(system, items)
    schema = q.writer_schema(len(items))
    for _ in range(2):  # one retry on an unusable reply
        got = q.parse_quotes(
            writer.chat(messages, schema, TOKENS_PER_QUOTE * len(items) + 50), len(items)
        )
        if got:
            return list(got)
    return [None] * len(items)


NOT_WRITTEN = {
    "failed": ["not_written"],
    "notes": "",
    "blind_prediction": None,
    "blind_agrees": False,
}


def check_one(
    checker: Server,
    prompts: dict[str, str],
    item: q.Item,
    quote: str,
    nominal: bool,
    actual: float,
    blind: bool = True,
) -> dict[str, Any]:
    verdict = q.parse_verdict(
        checker.chat(q.checker_messages(prompts["checker"], item, quote), q.checker_schema(), 400)
    )
    failed = q.failed_checks(verdict) if verdict else ["unreadable_verdict"]
    notes = (verdict or {}).get("notes", "")
    if not blind:  # rich, 30 Oct 2026: off for the full run; measured on a sample instead
        return {"failed": failed, "notes": notes, "blind_prediction": None, "blind_agrees": None}
    predicted = q.parse_blind(
        checker.chat(q.blind_messages(prompts["blind"], item, quote), BLIND_SCHEMA, 50)
    )
    agrees = predicted is not None and q.direction_agrees(
        predicted, actual, item.scale_min, item.scale_max, nominal
    )
    if not agrees:
        failed.append("blind_test")
        notes += " The quote suggests a different answer from the one they actually gave."
    return {
        "failed": failed,
        "notes": notes.strip(),
        "blind_prediction": predicted,
        "blind_agrees": agrees,
    }


def training_rows_only(rows: pd.DataFrame, split: Path = SPLIT) -> None:
    """Refuse rows from any study the split does not put in training."""
    seen = set(json.loads(split.read_text())["seen"])
    if bad := sorted(set(rows["study"]) - seen):
        sys.exit(f"rows from studies not in training: {bad[:5]}: a quote on them leaks the answer")


STEPS = [
    ("written", "writer", 0),
    ("checked 0", "checker", 0),
    ("rewritten 1", "writer", 1),
    ("checked 1", "checker", 1),
    ("rewritten 2", "writer", 2),
    ("checked 2", "checker", 2),
]
assert len(STEPS) == 2 * (REPAIR_ROUNDS + 1)


def next_step(phase: str | None) -> int:
    """Index in STEPS of the step after the saved phase (0 for a new run)."""
    if phase is None:
        return 0
    if phase == "done":
        return len(STEPS)
    names = [s[0] for s in STEPS]
    if phase not in names:
        raise SystemExit(f"cannot resume from phase {phase!r}")
    return names.index(phase) + 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rows", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--url", default=os.environ.get("QUOTES_URL"), help="the pod's router")
    ap.add_argument("--setting", choices=SETTINGS, default="full_persona")
    ap.add_argument(
        "--keys", type=Path, help="parquet of ROW_KEY columns to restrict to (the pilot)"
    )
    ap.add_argument("--existing", type=Path, nargs="+", default=[], help="earlier run folders")
    ap.add_argument("--limit", type=int, help="first N rows only, for a smoke test")
    ap.add_argument("--resume", action="store_true", help="carry on the run saved in OUT")
    ap.add_argument(
        "--no-blind", action="store_true", help="skip the blind test: one checker call per quote"
    )
    ap.add_argument("--seed", type=int, default=3407)
    ap.add_argument("--workers", type=int, default=64)
    args = ap.parse_args()

    key = os.environ.get("QUOTES_API_KEY", "")
    if not args.url or not key:
        sys.exit("set --url (or QUOTES_URL) and QUOTES_API_KEY")

    all_rows = pd.read_parquet(args.rows)
    training_rows_only(all_rows)
    saved: pd.DataFrame | None = None
    phase: str | None = None
    if args.resume:
        if not (args.out / "quotes.parquet").exists():
            sys.exit(f"nothing to resume in {args.out}")
        saved = pd.read_parquet(args.out / "quotes.parquet")
        manifest = json.loads((args.out / "run.json").read_text())
        phase, args.setting, args.seed = manifest["phase"], manifest["setting"], manifest["seed"]
        version = prompt_version_of(manifest)
        rows = saved[q.ROW_KEY].merge(all_rows, on=q.ROW_KEY, how="left", validate="one_to_one")
        if rows["persona"].isna().any():
            sys.exit("some saved rows are no longer in ROWS: resume against the same export")
    else:
        if args.out.exists() and any(args.out.iterdir()):
            sys.exit(f"{args.out} is not empty: a run is never overwritten (or use --resume)")
        rows = all_rows[all_rows.apply(q.is_text_row, axis=1)]
        if args.keys:
            keys = pd.read_parquet(args.keys)[q.ROW_KEY]
            rows = rows.reset_index(drop=True).merge(keys, on=q.ROW_KEY, validate="one_to_one")
        if args.existing:
            done = q.merge_tables(pd.read_parquet(run / "quotes.parquet") for run in args.existing)
            joined, _ = q.join_quotes(rows, done)
            rows = rows[~joined["synthetic_quote"].to_numpy()]
        if args.limit:
            rows = rows.head(args.limit)
    rows = rows.reset_index(drop=True)
    args.out.mkdir(parents=True, exist_ok=True)
    if not args.resume:
        version = PROMPT_VERSION

    prompts, prompt_hashes = {}, {}
    for name in ("writer", "checker", "blind"):
        prompts[name], prompt_hashes[name] = q.load_prompt(f"{name}_{version}.md")

    http = httpx.Client(timeout=300, headers={"Authorization": f"Bearer {key}"})
    pod = Pod(args.url, http)
    servers = {
        "writer": Server(args.url, "writer", WRITER_SAMPLING, http),
        "checker": Server(args.url, "checker", CHECKER_SAMPLING, http),
    }
    items = build_items(rows, args.setting, args.seed)
    n = len(items)

    quotes: list[str | None] = [None] * n
    results: list[dict[str, Any]] = [NOT_WRITTEN] * n
    rounds = [0] * n
    if saved is not None:
        drawn = [it.angle for it in items]
        if [a if isinstance(a, str) else None for a in saved["angle"]] != drawn:
            sys.exit("the saved angles differ from this run's draws: different setting or seed")
        notes = saved["notes"] if "notes" in saved else pd.Series([""] * n)
        quotes = [x if isinstance(x, str) else None for x in saved["quote"]]
        rounds = [int(x) for x in saved["rounds"]]
        if phase != "written":
            results = [
                {
                    "failed": json.loads(f),
                    "notes": nt if isinstance(nt, str) else "",
                    "blind_prediction": bp if pd.notna(bp) else None,
                    "blind_agrees": bool(ba),
                }
                for f, nt, bp, ba in zip(
                    saved["failed_checks"],
                    notes,
                    saved["blind_prediction"],
                    saved["blind_agrees"],
                    strict=True,
                )
            ]
    nominal = rows["scale_nominal"].astype(bool).tolist()
    actual = rows["response_num"].astype(float).tolist()
    print(f"rows: {n}  setting: {args.setting}  from: {phase or 'the start'}", flush=True)

    def save(phase_name: str) -> dict[str, Any]:
        table = rows[q.ROW_KEY].copy()
        table["input_hash"] = rows.apply(q.input_hash, axis=1)
        table["quote"] = pd.Series(quotes, dtype=object)
        table["passed"] = [not r["failed"] for r in results]
        table["rounds"] = rounds
        table["angle"] = [it.angle for it in items]
        table["voice"] = [it.voice for it in items]
        table["setting"] = args.setting
        table["failed_checks"] = [json.dumps(r["failed"]) for r in results]
        table["notes"] = [r["notes"] for r in results]
        table["blind_prediction"] = [r["blind_prediction"] for r in results]
        table["blind_agrees"] = [r["blind_agrees"] for r in results]
        table["run"] = args.out.name
        table = table[q.TABLE_COLUMNS]
        table.to_parquet(args.out / "quotes.parquet", index=False)
        report = summarise(rows, table)
        manifest = {
            "run": args.out.name,
            "phase": phase_name,
            "updated": datetime.now(UTC).isoformat(timespec="seconds"),
            "rows_file": str(args.rows),
            "setting": args.setting,
            "seed": args.seed,
            "serving": "one model at a time, switched by the router",
            "writer": {"model": servers["writer"].root, "sampling": WRITER_SAMPLING},
            "checker": {"model": servers["checker"].root, "sampling": CHECKER_SAMPLING},
            "prompt_version": version,
            "prompts": {f"{k}_{version}.md": h for k, h in prompt_hashes.items()},
            "repair_rounds": REPAIR_ROUNDS,
            "blind_test": not args.no_blind,
            "group_k": GROUP_K if args.setting == "group" else None,
            "request_failures": {k: dict(s.failures) for k, s in servers.items()},
            **report,
        }
        (args.out / "run.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n")
        return report

    writer, checker = servers["writer"], servers["checker"]

    def check(i: int) -> dict[str, Any]:
        quote = quotes[i]
        if quote is None:
            return NOT_WRITTEN
        return check_one(
            checker, prompts, items[i], quote, nominal[i], actual[i], blind=not args.no_blind
        )

    def rewrite(i: int) -> str | None:
        quote = quotes[i]
        if quote is None:
            return write_call(writer, prompts["writer"], [items[i]])[0]
        reply = writer.chat(
            q.repair_messages(prompts["writer"], items[i], quote, results[i]["notes"]),
            q.writer_schema(1),
            TOKENS_PER_QUOTE + 50,
        )
        got = q.parse_quotes(reply, 1)
        return got[0] if got else None

    with ThreadPoolExecutor(args.workers) as pool:
        for name, model, round_ in STEPS[next_step(phase) :]:
            if name.startswith("checked") or name.startswith("rewritten"):
                failing = [i for i in range(n) if results[i]["failed"]]
                if name.startswith("rewritten") and not failing:
                    break  # everything passed: nothing left to rewrite
            print(f"{name}: switching the pod to the {model}", flush=True)
            servers[model].root = pod.use(model)["hf"]
            if name == "written":
                calls = plan_calls(rows, items, args.setting)
                got = run_parallel(
                    pool,
                    lambda c, calls=calls: write_call(  # type: ignore[misc]
                        writer, prompts["writer"], [items[i] for i in calls[c]]
                    ),
                    range(len(calls)),
                    "write calls",
                )
                for c, quotes_c in got.items():
                    for i, quote in zip(calls[c], quotes_c, strict=True):
                        quotes[i] = quote
            elif name.startswith("rewritten"):
                for i, new in run_parallel(pool, rewrite, failing, "rewrites").items():
                    quotes[i], rounds[i] = new, round_
            else:
                todo = (
                    list(range(n)) if round_ == 0 else [i for i in range(n) if rounds[i] == round_]
                )
                for i, res in run_parallel(pool, check, todo, "checks").items():
                    results[i] = res
            report = save(name)
            print(f"{name}: saved; {report['passed']} of {n} pass so far", flush=True)

    report = save("done")
    print(json.dumps({k: report[k] for k in ("rows", "passed", "pass_rate")}, indent=2))
    failures = {k: dict(s.failures) for k, s in servers.items() if s.failures}
    if failures:
        print(f"request failures: {failures}")


def summarise(rows: pd.DataFrame, table: pd.DataFrame) -> dict[str, Any]:
    """Counts only. Pass rate by source, study, angle family and how unusual the answer is,
    so a checker that quietly filters irrational angles or unusual answers shows up."""
    passed = table["passed"].astype(bool)
    fails: Counter[str] = Counter()
    for f in table["failed_checks"]:
        fails.update(json.loads(f))
    width = (rows["scale_max"] - rows["scale_min"]).clip(lower=1)
    typical = rows.groupby(["recipe", "outcome"])["response_num"].transform("mean")
    unusual = pd.cut(
        ((rows["response_num"] - typical).abs() / width),
        [-0.01, 0.15, 0.35, 1.01],
        labels=["typical", "somewhat unusual", "unusual"],
    )
    family = table["angle"].map(
        lambda a: None if a is None else ("reasoned" if a in q.REASONED_ANGLES else "unreasoned")
    )

    def rate(by: pd.Series) -> dict[str, dict[str, float]]:
        g = passed.groupby(by.to_numpy(), observed=True)
        return {
            str(k): {"rows": int(n), "pass_rate": round(float(r), 3)}
            for k, n, r in zip(g.size().index, g.size(), g.mean(), strict=True)
        }

    return {
        "rows": len(table),
        "passed": int(passed.sum()),
        "pass_rate": round(float(passed.mean()), 3) if len(table) else None,
        "without_quote": int((~passed).sum()),
        "failed_checks": dict(fails.most_common()),
        "blind_agreement": (
            round(float(tested.astype(bool).mean()), 3)
            if len(tested := table["blind_agrees"].dropna())
            else None
        ),
        "by_source": rate(rows["source"]),
        "by_study": rate(rows["study"]),
        "by_angle_family": rate(family.fillna("none")),
        "by_unusualness": rate(unusual.astype(str)),
        "rounds_needed": {
            str(k): int(v)
            for k, v in table.loc[passed, "rounds"].value_counts().sort_index().items()
        },
    }


if __name__ == "__main__":
    main()
