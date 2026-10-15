#!/usr/bin/env python3
"""A t-SNE map of the corpus's STIMULI, the way Kolluri et al. draw SocSci210.

The paper (Figure 2, §3.1) embeds every stimulus — one (condition, outcome) pair —
and projects the set with t-SNE. That is a different map from `coverage_map.py`,
which places each study by its title. Here a point is one thing a respondent was
shown and asked, so the map shows how varied the CONDITIONS and OUTCOMES are,
which is what a train/eval split has to cover.

Choices, each deliberate:

- **One point per unique (condition, outcome).** The outcome's answer instruction
  ("Only return an integer ...") is cut off: it is the pipeline's wording, the
  same in every row, and would pull every point towards every other.
- **At most `CAP` per experiment, sampled with a fixed seed.** The conjoints hold
  thousands of unique stimuli each (EFXNLX alone 49,395); uncapped they would be
  most of the map and every other experiment a speck.
- **t-SNE, as the paper does, not UMAP.** This map is redrawn whole each time, so
  t-SNE's inability to place a new point into an old layout costs nothing here.
- **Only text cleared by `embed.CLEARED` is sent.** The licence comes from each
  recipe; anything not cleared is left off the map and listed in the output, never
  silently dropped. The Innovation Panel (UKDS End User Licence) is never sent.

    source ~/.bash_profile && uv run python scripts/stimulus_map.py
"""

from __future__ import annotations

import json
import random
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from micromotives_datasets import embed

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "data" / "catalog" / "stimulus_map.json"

CAP = 200
SEED = 20261010
SNIPPET = 160
SOURCE_LABEL = {
    "dataverse": "Dataverse / DEL",
    "tess": "TESS",
    "innovation_panel": "Innovation Panel",
}


def licence_key(recipe: dict) -> str:
    """The `embed.CLEARED` key this recipe's text travels under, if any."""
    first = str(recipe.get("licence") or "").strip()
    if recipe.get("source") == "innovation_panel":
        return "UKDS safeguarded"
    if first.startswith("CC0 1.0"):
        return "CC0 1.0"
    if recipe.get("source") == "tess":
        return "TESS deposit, none stated"
    return "not stated"


def question_only(outcome: str) -> str:
    return outcome.split(" Only return")[0].strip()


def committed_recipes() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "recipes/*.yaml"], cwd=ROOT, capture_output=True, text=True
    )
    return [ROOT / p for p in out.stdout.split()]


def parquet_for(recipe_path: Path, recipe: dict) -> Path | None:
    for name in (recipe_path.stem, f"{recipe['study_id']}_{recipe.get('experiment')}"):
        p = PROCESSED / f"{name}.parquet"
        if p.exists():
            return p
    hits = [
        p
        for p in PROCESSED.glob(f"{recipe['study_id']}*.parquet")
        if pd.read_parquet(p, columns=["experiment"]).experiment.iloc[0] == recipe.get("experiment")
    ]
    return hits[0] if len(hits) == 1 else None


def main() -> None:
    rng = random.Random(SEED)
    items: list[embed.Text] = []
    meta: dict[str, dict] = {}
    left_off: dict[str, str] = {}
    for rp in committed_recipes():
        recipe = yaml.safe_load(rp.read_text())
        lic = licence_key(recipe)
        if lic not in embed.CLEARED:
            left_off[rp.stem] = lic
            continue
        pq = parquet_for(rp, recipe)
        if pq is None:
            left_off[rp.stem] = "no built parquet found"
            continue
        df = pd.read_parquet(pq, columns=["condition", "outcome"])
        pairs = sorted(
            {(c, question_only(o)) for c, o in zip(df.condition, df.outcome, strict=True)}
        )
        n_unique = len(pairs)
        if len(pairs) > CAP:
            pairs = rng.sample(pairs, CAP)
        for i, (c, o) in enumerate(pairs):
            key = f"{rp.stem}#{i}"
            items.append(embed.Text(key=key, text=f"{c}\n\n{o}", licence=lic))
            meta[key] = {
                "exp": rp.stem,
                "source": SOURCE_LABEL.get(recipe.get("source", ""), recipe.get("source")),
                "c": c[:SNIPPET],
                "o": o[:SNIPPET],
            }
        meta.setdefault(f"__n__{rp.stem}", {"unique": n_unique})

    vectors = embed.embed(items)
    keys = [i.key for i in items]
    x = np.array([vectors[k] for k in keys])

    from sklearn.manifold import TSNE

    xy = TSNE(
        n_components=2, perplexity=30, metric="cosine", init="pca", random_state=SEED
    ).fit_transform(x)

    points = [
        {**meta[k], "x": round(float(a), 2), "y": round(float(b), 2)}
        for k, (a, b) in zip(keys, xy, strict=True)
    ]
    exps = sorted({p["exp"] for p in points})
    OUT.write_text(
        json.dumps(
            {
                "about": (
                    "t-SNE of stimulus embeddings: one point per unique (condition, "
                    f"outcome), at most {CAP} per experiment, {embed.MODEL}; "
                    "generated by scripts/stimulus_map.py."
                ),
                "model": embed.MODEL,
                "cap": CAP,
                "experiments": len(exps),
                "points": points,
                "left_off": left_off,
            },
            ensure_ascii=False,
        )
        + "\n"
    )
    print(f"{len(points)} stimuli from {len(exps)} experiments -> {OUT.relative_to(ROOT)}")
    print(f"left off ({len(left_off)}): {sorted(set(left_off.values()))}")


if __name__ == "__main__":
    main()
