"""Choose the quote pilot's rows (docs/QUOTES_SPEC.md section 10).

    uv run python scripts/quotes_pilot_rows.py data/processed/exports/v3/studies_10pct/train.parquet

TESS and Dataverse training rows only, text only, about 300-400 rows over every such
study. Per study:

- one WHOLE respondent (all their rows, at most MAX_ROWS of them), so writing one
  person's rows together is tested;
- five respondents from the study's largest group sharing (recipe, factors, outcome,
  response), one row each, so writing k different people together is tested. A study
  with no group of five gets a second whole respondent instead.

Seeded, so the same export gives the same pilot. Writes
data/processed/quotes/pilot_keys.parquet (ROW_KEY plus `part`), gitignored. Prints counts
only.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from micromotives_datasets import quotes as q

SEED = 3407
SOURCES = ["tess", "dataverse"]
MAX_ROWS = 10
K = 5
OUT = q.ROOT / "data" / "processed" / "quotes" / "pilot_keys.parquet"


def pick(rows: pd.DataFrame) -> pd.DataFrame:
    rows = rows[rows["source"].isin(SOURCES) & rows.apply(q.is_text_row, axis=1)]
    chosen = []
    for _, study in rows.groupby("study", sort=True):
        sizes = study.groupby("participant_id").size()
        taken: set[str] = set()
        groups = study.groupby(["recipe", "factors", "outcome", "response"], sort=True)
        people = groups["participant_id"].nunique()
        if people.max() >= K:
            biggest = groups.get_group(people.idxmax())
            firsts = biggest.drop_duplicates("participant_id")
            group_rows = firsts.sample(n=K, random_state=SEED)
            chosen.append(group_rows.assign(part="group"))
            taken |= set(group_rows["participant_id"])
            wholes = 1
        else:
            wholes = 2
        small = pd.Series(sorted(sizes[(sizes <= MAX_ROWS) & ~sizes.index.isin(taken)].index))
        if small.empty:
            small = pd.Series([sizes.drop(index=list(taken), errors="ignore").idxmin()])
        for person in small.sample(n=min(wholes, len(small)), random_state=SEED):
            chosen.append(study[study["participant_id"] == person].assign(part="respondent"))
    keys = pd.concat(chosen)[[*q.ROW_KEY, "part"]]
    # a row in both parts is kept once, as part of its respondent
    return (
        keys.sort_values("part", ascending=False).drop_duplicates(q.ROW_KEY).reset_index(drop=True)
    )


def main() -> None:
    rows = pd.read_parquet(Path(sys.argv[1]))
    keys = pick(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    keys.to_parquet(OUT, index=False)
    print(f"{len(keys)} rows from {keys['study'].nunique()} studies -> {OUT.relative_to(q.ROOT)}")
    print(keys["part"].value_counts().to_string())


if __name__ == "__main__":
    main()
