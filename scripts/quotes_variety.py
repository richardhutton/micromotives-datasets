"""Measure the variety of a quote run (docs/QUOTES_SPEC.md section 8).

    source ~/.bash_profile && uv run python scripts/quotes_variety.py ROWS.parquet RUN_DIR

Embeds every passed quote with Voyage (through embed.py; the quote sentence only), then
per group of rows sharing (recipe, factors, outcome, response) computes spread,
near-duplicate share and Vendi score, and per (recipe, factors, outcome) the separation
between quotes for different answers. Grouping and measuring happen here. Writes
RUN_DIR/variety.json; prints counts only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from micromotives_datasets import embed
from micromotives_datasets import quotes as q


def summary(values: list[float]) -> dict[str, Any]:
    clean = [v for v in values if not np.isnan(v)]
    if not clean:
        return {"groups": 0}
    return {
        "groups": len(clean),
        "median": round(float(np.median(clean)), 3),
        "mean": round(float(np.mean(clean)), 3),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rows", type=Path)
    ap.add_argument("run", type=Path)
    args = ap.parse_args()

    table = pd.read_parquet(args.run / "quotes.parquet")
    table = table[table["passed"].astype(bool)]
    cols = [*q.ROW_KEY, "factors", "outcome", "response"]
    rows = pd.read_parquet(args.rows, columns=cols)
    data = table.merge(rows, on=q.ROW_KEY, validate="one_to_one").reset_index(drop=True)
    texts = [embed.Text(str(i), quote, "synthetic-quote") for i, quote in enumerate(data["quote"])]
    got = embed.embed(texts)
    vectors = np.asarray([got[str(i)] for i in range(len(data))], dtype=float)

    spreads, dups, vendis, vendi_share, seps = [], [], [], [], []
    for _, g in data.groupby(["recipe", "factors", "outcome", "response"]):
        if len(g) < 2:
            continue
        e = vectors[g.index]
        spreads.append(q.spread(e))
        dups.append(q.near_duplicate_share(e))
        v = q.vendi(e)
        vendis.append(v)
        vendi_share.append(v / len(g))  # 1 = every quote distinct
    for _, g in data.groupby(["recipe", "factors", "outcome"]):
        if g["response"].nunique() >= 2 and len(g) >= 3:
            seps.append(q.separation(vectors[g.index], g["response"].tolist()))

    report = {
        "quotes": len(data),
        "embedding_model": embed.MODEL,
        "spread": summary(spreads),
        "near_duplicate_share": summary(dups),
        "vendi": summary(vendis),
        "vendi_per_quote": summary(vendi_share),
        "separation": summary(seps),
    }
    (args.run / "variety.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
