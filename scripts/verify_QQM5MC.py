"""Check the built QQM5MC rows against the numbers Sorace & Hobolt published.

UK studies are not in SocSci210, so `pipeline/crosscheck.py` has nothing to compare
them to and the recipe sets `comparable_to_socsci210: false`. That leaves a 6,345-row
study with no numeric answer key at all — and the project's whole history is that a
build can agree with itself while being wrong about which question a row answers or
which condition a respondent met. The published table IS the answer key here, so this
script is what `mmds crosscheck` is for the TESS studies.

It reads the PARQUET, not the deposit. Reproducing the paper from the `.dta` proves
only that the paper is reproducible; reproducing it from the melted rows proves that
the condition mapping, the outcome mapping, the response recode and the persona all
survived the melt. All four are things a recipe can get wrong silently.

The key is TABLE 1, not Figures 4 and 5. Both regressions are saturated — four
conditions fully crossed with a two-level moderator — so the printed coefficients ARE
the eight cell means, and summing them recovers each to four significant figures. The
figures draw the same eight numbers as bars, readable to about 0.1; reading them by
eye put "16.9" against a constant the table prints as 16.83, which is a defect in the
reader and not in the build. Derive from the table.

Two deliberate differences from the published numbers, both expected and both
asserted rather than tolerated:

  * Our N is exactly 2 below the paper's on each item. ID 2158 was routed to both
    block B and block C; the authors' reshape keeps that person in both groups, so
    their N counts one respondent twice. We drop them (see the recipe's
    `ambiguous_routing`), so we lose both of the paper's copies.

  * Six of the eight rank cells land within 0.003 of the table. The two that do not
    are Prime only/Leave (0.018) and Info only/Leave (0.026) — which are exactly the
    two cells ID 2158 was counted in, and they move in the direction their low rank
    of 6 predicts. The tolerance is 0.05 so that agreement is still asserted, and
    the two outliers are named here so a future drift cannot hide behind them.

Run:  uv run python scripts/verify_QQM5MC.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
PARQUET = REPO / "data" / "processed" / "QQM5MC.parquet"

# condition_num is the do-file's `Group` coding, so these names are the paper's.
CONDITIONS = {0: "Control", 1: "Prime only", 2: "Prime & Info", 3: "Info only"}

# Table 1, transcribed. Model (1) is the rank item, model (2) the economy item;
# `task_num` is the key. The reference cell is Control/Remain, which is why the
# constant alone gives it. OLS, standard errors dropped — only the point estimates
# are needed to recover a cell mean from a saturated design.
TABLE_1: dict[int, dict[str, float]] = {
    0: {
        "constant": 16.83,
        "prime_only": 1.213,
        "prime_and_info": 1.495,
        "info_only": 1.660,
        "leave": -2.764,
        "prime_only_x_leave": -2.814,
        "prime_and_info_x_leave": -1.721,
        "info_only_x_leave": -0.305,
    },
    1: {
        "constant": 1.188,
        "prime_only": -0.0879,
        "prime_and_info": -0.120,
        "info_only": -0.0585,
        "leave": 0.656,
        "prime_only_x_leave": 0.279,
        "prime_and_info_x_leave": 0.220,
        "info_only_x_leave": -0.130,
    },
}
# condition_num -> the coefficient naming it, None for the reference condition.
CONDITION_TERM = {0: None, 1: "prime_only", 2: "prime_and_info", 3: "info_only"}
TOLERANCE = 0.05

# Table 1, "Observations". Ours are 2 lower for the reason in the docstring.
PUBLISHED_N = {0: 2762, 1: 2653}
OUR_N_DEFICIT = 2


def published_mean(task: int, condition: int, leaver: bool) -> float:
    """The cell mean Table 1 implies, by summing the terms that cell switches on."""
    coef = TABLE_1[task]
    total = coef["constant"]
    term = CONDITION_TERM[condition]
    if term is not None:
        total += coef[term]
    if leaver:
        total += coef["leave"]
        if term is not None:
            total += coef[f"{term}_x_leave"]
    return total


LEAVE = "I voted to Leave"
REMAIN = "I voted to Remain"


def load() -> pd.DataFrame:
    if not PARQUET.exists():
        raise SystemExit(f"{PARQUET} not found — run `uv run mmds build recipes/QQM5MC.yaml` first")
    df = pd.read_parquet(PARQUET)
    # The referendum vote is the paper's moderator and lives in the persona's
    # `extra`, which the parquet carries as JSON.
    df["vote"] = df["persona"].map(lambda s: json.loads(s)["extra"].get("eu_referendum_vote"))
    return df[df["vote"].isin([LEAVE, REMAIN])]


def check(df: pd.DataFrame) -> list[str]:
    """Every disagreement with the published numbers. Empty means verified."""
    bad: list[str] = []

    for task, expected_n in PUBLISHED_N.items():
        got = int((df["task_num"] == task).sum())
        want = expected_n - OUR_N_DEFICIT
        if got != want:
            bad.append(
                f"task {task}: N={got}, expected {want} "
                f"(the paper's {expected_n} less the duplicated respondent's two rows)"
            )

    for task in TABLE_1:
        rows = df[df["task_num"] == task]
        for cond in CONDITIONS:
            cell = rows[rows["condition_num"] == cond]
            for vote in (LEAVE, REMAIN):
                want = published_mean(task, cond, vote == LEAVE)
                got = cell[cell["vote"] == vote]["response_num"].mean()
                if pd.isna(got) or abs(got - want) > TOLERANCE:
                    bad.append(
                        f"task {task}, {CONDITIONS[cond]}, {vote}: mean={got:.3f}, "
                        f"Table 1 implies {want:.3f} (tolerance {TOLERANCE})"
                    )

    return bad


def main() -> int:
    df = load()
    failures = check(df)

    print("QQM5MC — built rows against Sorace & Hobolt (2021)")
    for task, label in ((0, "UK economy rank, 1-34"), (1, "economy getting better, 0-4")):
        rows = df[df["task_num"] == task]
        print(f"\n  task {task}  {label}   N={len(rows)}")
        table = rows.pivot_table(
            index="condition_num", columns="vote", values="response_num", aggfunc="mean"
        ).round(2)
        for cond in sorted(CONDITIONS):
            print(
                f"    {CONDITIONS[cond]:<14} "
                f"Leave {table.loc[cond, LEAVE]:>6.2f} "
                f"(table {published_mean(task, cond, True):.2f})   "
                f"Remain {table.loc[cond, REMAIN]:>6.2f} "
                f"(table {published_mean(task, cond, False):.2f})"
            )

    if failures:
        print("\nFAILED:")
        for line in failures:
            print(f"  {line}")
        return 1
    print("\nVERIFIED — 8 group means and 2 Ns agree with Table 1.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
