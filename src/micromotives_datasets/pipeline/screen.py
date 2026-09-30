"""Rule 9 — is there a second randomisation the recipe didn't declare?

This exists because of ledger #33. `z358z` is a 2x2 randomised through TWO
variables — `XTESS175` (scenario) and `DOV_OPTION` (consent alternative) — with
no combined four-level code anywhere in the file. The recipe declared only the
first, so a whole factor was silently absent from the stimulus text, and nothing
in the pipeline could have noticed. An agent happened to spot it.

It lives here rather than in `qc.check(rows, recipe)` because it needs the
`Dataset`, and that signature has no data access.

The screen is anchored on the recipe's OWN declared assignment variable. That
anchoring is what makes it usable: a naive "find all randomisation-looking
variables" sweep over the corpus returns over a thousand hits, dominated by
item-order variables. Requiring full, balanced crossing against the declared key
cuts it to near-zero on a correct recipe.

It warns; it never fails a build. A recipe silences a variable either by
declaring it in `source_vars` or by recording a reason in
`condition.considered_and_rejected`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

from ..recipe import Recipe
from ..sources.spss import Dataset

# Assignment variables in TESS deposits are named by convention: `DOV_*` ("data
# only variable"), `XTESS*`, or an X-prefixed code. Labels are a second route in,
# for the deposits that do not follow the naming.
NAME_PAT = re.compile(r"^(DOV|XTESS|X[A-Z]{2,})", re.I)
LABEL_PAT = re.compile(r"random|experim|condition|assign|version|\barm\b", re.I)

MAX_LEVELS = 12
MIN_COVERAGE = 0.95
MIN_BALANCE = 0.70


@dataclass
class Suspect:
    var: str
    label: str
    n_levels: int
    balance: float

    def render(self) -> str:
        return (
            f"{self.var} ({self.n_levels} levels, balance {self.balance:.2f})"
            f"{f' [{self.label}]' if self.label else ''}"
        )


def _balance(counts: pd.Series) -> float:
    """Smallest cell as a fraction of the largest. 1.0 is perfectly uniform."""
    if counts.empty or counts.max() == 0:
        return 0.0
    return float(counts.min() / counts.max())


def find_undeclared_assignment(ds: Dataset, recipe: Recipe) -> list[Suspect]:
    """Columns that look like a second randomisation crossed with the declared one."""
    declared = {v.upper() for v in recipe.condition.variables}
    if not declared:
        return []
    rejected = {k.upper() for k in recipe.condition.considered_and_rejected}

    # The declared assignment, as one key per respondent.
    keys = [c for c in ds.df.columns if c.upper() in declared]
    if len(keys) != len(declared):
        return []
    anchor = ds.df[keys].astype("string").agg("|".join, axis=1)

    out: list[Suspect] = []
    n = len(ds.df)
    for col in ds.df.columns:
        up = col.upper()
        if up in declared or up in rejected:
            continue
        label = (ds.column_labels.get(col) or "").strip()
        if not (NAME_PAT.match(col) or LABEL_PAT.search(label)):
            continue

        series = ds.df[col]
        if series.notna().sum() < MIN_COVERAGE * n:
            continue
        counts = series.value_counts(dropna=True)
        if not 2 <= len(counts) <= MAX_LEVELS:
            continue
        if _balance(counts) < MIN_BALANCE:
            continue

        # The discriminating test: a genuine second factor is fully crossed with
        # the declared one and roughly balanced within every cell. An item-order
        # or attention-check variable usually is not, or has empty cells.
        table = pd.crosstab(anchor, series)
        if table.size == 0 or (table.to_numpy() == 0).any():
            continue
        cells = table.to_numpy().flatten()
        if _balance(pd.Series(cells)) < MIN_BALANCE:
            continue

        out.append(Suspect(var=col, label=label, n_levels=len(counts), balance=_balance(counts)))
    return out


def render(suspects: list[Suspect]) -> str:
    lines = [f"  warn  possible undeclared assignment: {s.render()}" for s in suspects]
    if lines:
        lines.append(
            "        fully crossed and balanced against the declared assignment. "
            "Declare it in `source_vars`, or give a reason in "
            "`condition.considered_and_rejected`."
        )
    return "\n".join(lines)
