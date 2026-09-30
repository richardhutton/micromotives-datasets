#!/usr/bin/env python3
"""
inspect.py — a small CLI to explore Hugging Face datasets, built for the
`socratesft` org and its SocSci210 dataset, but usable on any public dataset.

It leans on the Hugging Face *datasets-server* REST API, so you can inspect the
schema, browse rows, and read column statistics WITHOUT downloading the full
9.4 GB dataset. Only the `mappings` command pulls small JSON files down.

Commands
--------
  org       List all datasets and models published by an org.
  info      Configs, splits, row counts, and the full column schema.
  sample    Pretty-print a few rows (truncated), to see what's inside.
  read      Dump the full text of one row's fields (great for prompt/reasoning).
  stats     Per-column statistics: value counts, histograms, null rates.
  mappings  Download & summarize the metadata/*.json split files (train logic).

Examples
--------
  python inspect.py org
  python inspect.py info
  python inspect.py sample -n 3
  python inspect.py read --row 0 --fields prompt,reasoning,stimuli,response
  python inspect.py stats
  python inspect.py mappings
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
import time

import requests

# ---------------------------------------------------------------------------
# Defaults — the thing we're here to look at.
# ---------------------------------------------------------------------------
DEFAULT_ORG = "socratesft"
DEFAULT_DATASET = "socratesft/SocSci210"
DEFAULT_CONFIG = "default"
DEFAULT_SPLIT = "train"

SERVER = "https://datasets-server.huggingface.co"
TIMEOUT = 30


# ---------------------------------------------------------------------------
# Tiny helpers
# ---------------------------------------------------------------------------
def _get(path: str, timeout: int = TIMEOUT, **params) -> dict:
    """GET a datasets-server endpoint and return parsed JSON.

    Retries with backoff on the two transient states the free public endpoint
    returns: 429 (rate limiting, from querying too fast) and a 500 whose body
    says the index "is loading" (the /filter and /search indexes warm up on
    first use). Raises with a clear message on genuine errors.
    """
    delay = 2.0
    for attempt in range(6):
        try:
            r = requests.get(f"{SERVER}/{path}", params=params, timeout=timeout)
        except requests.exceptions.ReadTimeout:
            if attempt < 5:
                print(f"  … request timed out, retrying [attempt {attempt + 1}/6]", file=sys.stderr)
                continue
            raise SystemExit(f"Repeated timeouts calling /{path}.")
        if r.status_code == 200:
            return r.json()
        loading = r.status_code == 500 and "loading" in r.text.lower()
        if r.status_code == 429 or loading:
            reason = "rate-limited (429)" if r.status_code == 429 else "index loading"
            if attempt < 5:
                print(
                    f"  … {reason}, backing off {delay:.0f}s [attempt {attempt + 1}/6]",
                    file=sys.stderr,
                )
                time.sleep(delay)
                delay = min(delay * 2, 30)
                continue
            raise SystemExit(
                f"Endpoint still unavailable ({reason}) after retries. This is "
                "temporary and NOT a permissions problem — wait a minute and retry."
            )
        raise SystemExit(
            f"HTTP {r.status_code} from /{path}\n{r.text[:300]}\n"
            "(A 404/403 here usually means the dataset is gated/private or the "
            "config/split name is wrong.)"
        )
    return {}  # unreachable


def _rule(title: str) -> None:
    print(f"\n\033[1m{title}\033[0m")
    print("─" * min(len(title), 70))


def _shorten(value, width: int = 100) -> str:
    text = " ".join(str(value).split())
    return textwrap.shorten(text, width=width, placeholder=" …")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_org(args) -> None:
    """List datasets and models under an org using the HF Hub client."""
    from huggingface_hub import HfApi

    api = HfApi()
    _rule(f"Organization: {args.org}")

    datasets = list(api.list_datasets(author=args.org))
    print(f"\nDatasets ({len(datasets)}):")
    for d in sorted(datasets, key=lambda x: -(x.downloads or 0)):
        print(f"  • {d.id}")
        print(
            f"      downloads={d.downloads or 0}  likes={d.likes or 0}  "
            f"updated={str(d.last_modified)[:10]}"
        )

    models = list(api.list_models(author=args.org))
    print(f"\nModels ({len(models)}):")
    for m in sorted(models, key=lambda x: -(x.downloads or 0)):
        print(f"  • {m.id}")
        print(
            f"      downloads={m.downloads or 0}  likes={m.likes or 0}  "
            f"updated={str(m.last_modified)[:10]}"
        )


def _print_feature(name: str, spec, indent: str = "  ") -> None:
    """Print one schema feature, recursing into nested structs and lists."""
    if isinstance(spec, dict) and "_type" not in spec and "dtype" not in spec:
        # nested struct: a dict of sub-features
        print(f"{indent}{name:<26} struct ({len(spec)} fields)")
        for sub, subspec in spec.items():
            _print_feature(sub, subspec, indent + "    ")
    elif isinstance(spec, list):  # Sequence feature
        print(f"{indent}{name:<26} list")
        for sub, subspec in (spec[0] or {}).items():
            _print_feature(sub, subspec, indent + "    ")
    else:
        dtype = spec.get("dtype", spec.get("_type", "?"))
        print(f"{indent}{name:<26} {dtype}")


def cmd_info(args) -> None:
    """Show configs, splits, row counts, and the column schema."""
    _rule(f"Dataset: {args.dataset}")

    info = _get("info", dataset=args.dataset)["dataset_info"]

    print("\nConfigs & splits:")
    for config_name, cfg in info.items():
        for split_name, sp in cfg.get("splits", {}).items():
            n = sp.get("num_examples")
            n = f"{n:,}" if isinstance(n, int) else "?"
            print(f"  • config={config_name:<12} split={split_name:<10} rows={n}")

    for config_name, cfg in info.items():
        features = cfg.get("features", {})
        _rule(f"Schema — config '{config_name}'  ({len(features)} top-level columns)")
        for name, spec in features.items():
            _print_feature(name, spec)

        size = cfg.get("dataset_size")
        dl = cfg.get("download_size")
        if size:
            extra = f"   download ≈ {dl / 1e9:.1f} GB" if dl else ""
            print(f"\n  uncompressed ≈ {size / 1e9:.1f} GB{extra}")


def cmd_sample(args) -> None:
    """Print a few rows with each field truncated to one line."""
    data = _get(
        "rows",
        dataset=args.dataset,
        config=args.config,
        split=args.split,
        offset=args.offset,
        length=args.n,
    )
    rows = data["rows"]
    _rule(
        f"{len(rows)} sample row(s) from {args.dataset} "
        f"[{args.config}/{args.split}] offset={args.offset}"
    )
    for entry in rows:
        idx = entry.get("row_idx")
        row = entry["row"]
        print(f"\n── row {idx} " + "─" * 50)
        for key, value in row.items():
            print(f"  {key:<24} {_shorten(value, args.width)}")


def cmd_read(args) -> None:
    """Dump the FULL text of selected fields for one row (no truncation)."""
    data = _get(
        "rows",
        dataset=args.dataset,
        config=args.config,
        split=args.split,
        offset=args.row,
        length=1,
    )
    if not data["rows"]:
        raise SystemExit(f"No row at offset {args.row}.")
    row = data["rows"][0]["row"]

    fields = [f.strip() for f in args.fields.split(",")] if args.fields else list(row)
    _rule(f"Full row {args.row} from {args.dataset}")
    for key in fields:
        if key not in row:
            print(f"\n[!] field '{key}' not found. Available: {', '.join(row)}")
            continue
        print(f"\n\033[1m{key}\033[0m")
        print("┈" * 60)
        print(row[key])


def cmd_stats(args) -> None:
    """Show per-column statistics computed by the datasets-server."""
    data = _get("statistics", dataset=args.dataset, config=args.config, split=args.split)
    _rule(f"Column statistics — {args.dataset} [{args.config}/{args.split}]")
    for col in data["statistics"]:
        name = col["column_name"]
        ctype = col["column_type"]
        s = col["column_statistics"]
        nulls = s.get("nan_count", 0)
        print(f"\n• {name}  ({ctype})   nulls={nulls}")
        if "min" in s:  # numeric
            print(
                f"    min={s.get('min')}  max={s.get('max')}  "
                f"mean={s.get('mean')}  median={s.get('median')}"
            )
        freqs = s.get("frequencies")
        if freqs:
            top = sorted(freqs.items(), key=lambda kv: -kv[1])[: args.top]
            for val, count in top:
                print(f"    {count:>10,}  {_shorten(val, 60)}")


def _persona(demo: dict) -> str:
    """One-line summary of a demographic struct."""
    keys = ["age", "gender", "party_id", "ideology", "education", "income"]
    bits = [f"{k}={demo[k]}" for k in keys if k in demo and demo[k] not in (None, "")]
    return ", ".join(bits)


def _scan_rows(args, n_rows: int) -> list:
    """Pull up to n_rows contiguous rows via the reliable /rows endpoint."""
    out = []
    offset = args.row
    while len(out) < n_rows:
        length = min(100, n_rows - len(out))
        res = _get(
            "rows",
            dataset=args.dataset,
            config=args.config,
            split=args.split,
            offset=offset,
            length=length,
        )
        batch = res["rows"]
        if not batch:
            break
        out.extend(e["row"] for e in batch)
        offset += len(batch)
    return out


def cmd_dpo(args) -> None:
    """Reconstruct a DPO preference pair {prompt, chosen, rejected}.

    The DPO pairs are NOT stored on Hugging Face — they are built from the
    SocSci210 rows (paper §4 / §5.5). For a focal persona p_pos who answered a
    question, the CHOSEN completion is their real response r_pos; the REJECTED
    completion is a DIFFERENT response r_neg given by another participant to the
    SAME question under the SAME condition. Only the number r_neg is borrowed —
    the prompt keeps p_pos's demographics.

    We find a valid pair by scanning a window of rows and grouping them into
    "cells" = (study_id, condition_num, task_num). A cell with two or more
    distinct responses gives us a chosen/rejected contrast.
    """
    rows = _scan_rows(args, args.scan)

    # Group into cells: same study + condition + outcome question.
    cells = {}
    for r in rows:
        key = (r["study_id"], r["condition_num"], r["task_num"])
        cells.setdefault(key, []).append(r)

    # Keep cells where personas disagreed (>=2 distinct responses).
    contested = {k: v for k, v in cells.items() if len({r["response"] for r in v}) >= 2}
    if not contested:
        raise SystemExit(
            f"No cell with differing responses in the {len(rows)} rows scanned "
            f"from offset {args.row}. Try a larger --scan or a different --row."
        )

    _rule(f"DPO preference pairs from {args.dataset}")
    print(
        f"scanned {len(rows)} rows from offset {args.row} → "
        f"{len(cells)} cells, {len(contested)} with a chosen/rejected contrast\n"
    )

    for key, cell in list(contested.items())[: args.pairs]:
        sid, cond, task = key
        focal = cell[0]  # p_pos
        r_pos = focal["response"]
        dist = {}
        for r in cell:
            dist[r["response"]] = dist.get(r["response"], 0) + 1

        print("═" * 66)
        print(
            f"cell: study_id={sid}  condition_num={cond}  task_num={task}  "
            f"({len(cell)} personas here)"
        )
        print("response distribution:", ", ".join(f"{v}×{c}" for v, c in sorted(dist.items())))

        print("\n\033[1mPROMPT (focal persona p_pos)\033[0m")
        print("┈" * 60)
        print(f"persona: {_persona(focal['demographic'])}")
        print(focal["prompt"] if args.full else _shorten(focal["prompt"], 350))

        print(f"\n  \033[1m✓ CHOSEN\033[0m   (r_pos, p_pos's real answer): {r_pos}")
        rejects = [r for r in cell if r["response"] != r_pos]
        print("  \033[1m✗ REJECTED\033[0m (r_neg, borrowed from another persona):")
        for r in rejects[:3]:
            print(
                f"      {r['response']}  ← participant {r['participant']} "
                f"({_persona(r['demographic'])})"
            )
        print()
    print(
        "Note: the prompt stays p_pos's; only the rejected *number* comes from "
        "another person. DPO trains F' to prefer the chosen over the rejected."
    )


def cmd_mappings(args) -> None:
    """Download the small metadata/*.json split files and summarize them."""
    from huggingface_hub import hf_hub_download

    files = [
        "metadata/participant_mapping.json",
        "metadata/task_mapping.json",
        "metadata/condition_mapping.json",
    ]
    _rule(f"Split-mapping files in {args.dataset}")
    for fname in files:
        try:
            path = hf_hub_download(repo_id=args.dataset, filename=fname, repo_type="dataset")
        except Exception as e:
            print(f"\n[!] could not fetch {fname}: {e}")
            continue
        with open(path) as fh:
            obj = json.load(fh)
        print(f"\n• {fname}")
        _summarize_json(obj, indent="    ")


def _summarize_json(obj, indent="") -> None:
    """Describe the shape of a decoded JSON object without dumping it all."""
    if isinstance(obj, dict):
        keys = list(obj.keys())
        print(f"{indent}dict with {len(keys)} keys, e.g. {keys[:5]}")
        for k in keys[:3]:
            v = obj[k]
            if isinstance(v, list):
                print(f"{indent}  '{k}': list of {len(v)} → sample {v[:3]}")
            elif isinstance(v, dict):
                print(f"{indent}  '{k}': dict of {len(v)} keys → {list(v)[:5]}")
            else:
                print(f"{indent}  '{k}': {_shorten(v, 60)}")
    elif isinstance(obj, list):
        print(f"{indent}list of {len(obj)} items → sample {obj[:3]}")
    else:
        print(f"{indent}{_shorten(obj)}")


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="command", required=True)

    def add_dataset_args(sp):
        sp.add_argument("--dataset", default=DEFAULT_DATASET)
        sp.add_argument("--config", default=DEFAULT_CONFIG)
        sp.add_argument("--split", default=DEFAULT_SPLIT)

    sp = sub.add_parser("org", help="list an org's datasets & models")
    sp.add_argument("--org", default=DEFAULT_ORG)
    sp.set_defaults(func=cmd_org)

    sp = sub.add_parser("info", help="schema, configs, splits, row counts")
    sp.add_argument("--dataset", default=DEFAULT_DATASET)
    sp.set_defaults(func=cmd_info)

    sp = sub.add_parser("sample", help="print a few truncated rows")
    add_dataset_args(sp)
    sp.add_argument("-n", type=int, default=3, help="rows to show (max 100)")
    sp.add_argument("--offset", type=int, default=0)
    sp.add_argument("--width", type=int, default=100, help="truncation width")
    sp.set_defaults(func=cmd_sample)

    sp = sub.add_parser("read", help="dump full field text for one row")
    add_dataset_args(sp)
    sp.add_argument("--row", type=int, default=0, help="row offset")
    sp.add_argument(
        "--fields",
        default="prompt,reasoning,stimuli,response",
        help="comma-separated field names (blank = all)",
    )
    sp.set_defaults(func=cmd_read)

    sp = sub.add_parser("stats", help="per-column statistics")
    add_dataset_args(sp)
    sp.add_argument("--top", type=int, default=10, help="top values per column")
    sp.set_defaults(func=cmd_stats)

    sp = sub.add_parser("dpo", help="reconstruct DPO preference pairs")
    add_dataset_args(sp)
    sp.add_argument("--row", type=int, default=0, help="row offset to scan from")
    sp.add_argument(
        "--scan", type=int, default=300, help="rows to scan for contrast cells (multiple of 100)"
    )
    sp.add_argument("--pairs", type=int, default=3, help="preference pairs to show")
    sp.add_argument("--full", action="store_true", help="show full prompt text")
    sp.set_defaults(func=cmd_dpo)

    sp = sub.add_parser("mappings", help="summarize the train/eval split files")
    sp.add_argument("--dataset", default=DEFAULT_DATASET)
    sp.set_defaults(func=cmd_mappings)

    return p


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
