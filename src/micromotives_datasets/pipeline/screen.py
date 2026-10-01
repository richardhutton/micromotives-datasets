"""Screens that need the DATA alongside the recipe, so cannot live in `qc.check`.

Both warn; neither ever fails a build. A recipe silences a variable either by
declaring it in `source_vars`, or by recording a reason in
`condition.considered_and_rejected` — which keeps the judgment on the record
instead of leaving it implicit.

**Rule 9 — an undeclared second randomisation.** Ledger #33: `z358z` is a 2x2
randomised through two variables, `XTESS175` (scenario) and `DOV_OPTION`
(consent alternative), with no combined four-level code anywhere in the file.
The recipe declared only the first, so a whole factor was silently absent from
the stimulus text and nothing in the pipeline could notice. An agent spotted it.

The screen is anchored on the recipe's OWN declared assignment. That anchoring
is what makes it usable: an unanchored sweep for randomisation-looking variables
across the corpus returns over a thousand hits.

**Rule 11 — a numbered sibling of the declared assignment.** `P_S1` alongside
`P_S2..P_S8` is what a within-subject repeated measure looks like in a wide file;
`Vignette1` alongside `Vignette2` is what a two-experiment deposit looks like.
Rule 9 is structurally blind to both, so this is deliberately a separate, much
cruder test.

Neither rule can tell a second ARM FACTOR from an item-order randomisation:
both are randomised, balanced, and independent of the first. The difference is
whether the level shows up in the stimulus text, which no statistic can see. So
these screens surface candidates for a decision — and order variables are
surfaced too, because ledger #2 is `sd7cf`'s *dropped distractor-position*
factor, i.e. a case where order WAS the manipulation.
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

# "preload" and "order" are both load-bearing. TESS labels randomisation
# preloads as `PRELOAD : P_ORDER` / `PRELOAD VARIABLE: P_S1`, matching no other
# keyword — that alone hid `zaqkm`'s second randomisation. And see the module
# docstring on why order variables must be surfaced rather than assumed benign.
LABEL_PAT = re.compile(r"random|experim|condition|assign|version|preload|\border\b|\barm\b", re.I)

MAX_LEVELS = 12
MIN_COVERAGE = 0.95
MIN_BALANCE = 0.70

# `P_S1` -> `P_S2`, `Vignette1` -> `Vignette2`. See `find_numbered_siblings`.
STEM_PAT = re.compile(r"^(.*?)(\d+)$")


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


def find_numbered_siblings(ds: Dataset, recipe: Recipe) -> list[str]:
    """Rule 11 — columns that are a numbered sibling of a declared variable.

    `b87sm` is within-subject: each respondent saw eight vignettes from a 72-cell
    universe, slot k assigned by `P_S{k}`. Declaring `P_S1` leaves seven further
    randomisations — 7/8 of the observations — unreachable, and rule 9 misses all
    seven for three independent reasons: the names do not match its pattern, the
    labels carry no keyword it knew, and 72 levels exceeds `MAX_LEVELS`; past all
    three, a 72-level anchor guarantees an empty crosstab cell.

    A numbered sibling needs none of that machinery. Measured across every recipe
    and draft: zero false positives, true positives on exactly the two studies
    with observations left on the table.
    """
    rejected = {k.upper() for k in recipe.condition.considered_and_rejected}
    return [c for c in _sibling_family(ds, recipe) if c.upper() not in rejected]


def _sibling_family(ds: Dataset, recipe: Recipe) -> list[str]:
    """Every numbered sibling of a declared variable, rejected or not.

    Rule 9 suppresses on this FAMILY rather than on what rule 11 still reports,
    and the distinction is load-bearing. Deriving the suppression list from
    `find_numbered_siblings` coupled the two rules backwards: recording
    `P_S2..P_S8` in `considered_and_rejected` — exactly what a recipe is supposed
    to do to silence rule 11 — emptied the list and un-silenced their 35
    decomposed component columns in rule 9. Measured on `b87sm`: doing the right
    thing took the build from 5 warnings to 40.

    The general form: **a suppression mechanism must not be derived from a
    reporting mechanism that the suppression itself feeds.**
    """
    # Per-item assignment variables count as declared here too: once a recipe
    # builds all eight of `b87sm`'s slots by naming `P_S{k}` on each outcome,
    # rule 11's whole message — "there are seven more slots you have not built" —
    # has been answered, and it must fall silent rather than report the answer.
    declared = recipe.assignment_variables
    stems = {m.group(1) for v in declared if (m := STEM_PAT.match(v)) and m.group(1)}
    if not stems:
        return []
    return [
        col
        for col in ds.df.columns
        if col.upper() not in declared
        and (m := STEM_PAT.match(col.upper()))
        and m.group(1) in stems
    ]


def find_undeclared_assignment(ds: Dataset, recipe: Recipe) -> list[Suspect]:
    """Rule 9 — columns that look like a second randomisation crossed with ours."""
    # Two different sets, and conflating them would break the rule in opposite
    # directions. `declared` is everything the recipe uses to assign an arm,
    # INCLUDING per-item assignment variables, because a declared variable must
    # never be reported as undeclared. The ANCHOR stays the study-level
    # condition: crossing slot 1's vignette against slot 2's is not a second
    # randomisation, it is the same randomisation drawn again, and anchoring on
    # all eight slots would make every column look nested.
    declared = recipe.assignment_variables
    if not declared:
        return []
    rejected = {k.upper() for k in recipe.condition.considered_and_rejected}

    study_level = {v.upper() for v in recipe.condition.variables}
    keys = [c for c in ds.df.columns if c.upper() in study_level]
    if len(keys) != len(study_level):
        return []

    # A column named `<declared assignment>_<something>` is a DECOMPOSITION of
    # a declared variable — `P_S2_Tech_Support` restates one factor of the
    # vignette `P_S2` already names — so it is not a second randomisation and
    # reporting it as one is noise.
    #
    # This fires only once the siblings are properly declared, and it is the
    # SAME bug as ledger #52 in a new dress. That one: recording `P_S2..P_S8`
    # in `considered_and_rejected` emptied the sibling list and un-silenced
    # their 35 component columns. This one: DECLARING `P_S2..P_S8` as per-item
    # assignment empties it the same way, for the same reason. The suppression
    # was derived from "siblings we have not dealt with yet", so every way of
    # dealing with them removed it. Deriving it from the declared variables
    # themselves has no such feedback.
    components = tuple(f"{v}_" for v in declared)
    anchor = ds.df[keys].astype("string").agg("|".join, axis=1)

    # Rule 11 owns the numbered-sibling family, so skip those and their component
    # columns. `b87sm` declares `P_S1`; the file also holds `P_S2..P_S8` and each
    # slot's five decomposed factor columns (`P_S2_Tech_Support`, ...). Rule 11
    # already reports the seven slots, and repeating all 40 components here would
    # bury the very signal it exists to give.
    sibling_prefixes = tuple(s.upper() for s in _sibling_family(ds, recipe))

    out: list[Suspect] = []
    n = len(ds.df)
    for col in ds.df.columns:
        up = col.upper()
        if up in declared or up in rejected:
            continue
        if sibling_prefixes and up.startswith(sibling_prefixes):
            continue
        if up.startswith(components):
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

        # Full crossing is the discriminating test: a second randomisation has
        # every combination populated, while a nested variable — a follow-up
        # asked of one arm only, or a component of the declared code itself —
        # leaves empty cells.
        #
        # We do NOT additionally require balance WITHIN cells. That gate was here
        # originally and it silently lost power as arm count grew: with `cug34`'s
        # 24 arms (~84 per cell) sampling noise alone puts min/max at 0.57-0.70,
        # so of six genuine second randomisations it reported exactly one — and
        # which one was essentially chance. `zaqkm` measured 0.39 at 40 arms.
        # Marginal balance (above) carries the same signal without the cell-size
        # dependence: those six score 0.91-1.00 on it.
        table = pd.crosstab(anchor, series)
        if table.size == 0 or (table.to_numpy() == 0).any():
            continue

        out.append(Suspect(var=col, label=label, n_levels=len(counts), balance=_balance(counts)))
    return out


def find_assignment_components(ds: Dataset, recipe: Recipe) -> list[str]:
    """Columns that decompose a declared assignment variable.

    Rule 9 does not report these one by one — there are 40 of them in `b87sm`
    and they would bury the signal the rule exists to give. But it must not
    hide them either: "40 columns suppressed as components of P_S1..P_S8" is a
    claim a reader can check, and a second manipulation that happened to be
    named after a declared variable would be visible in that list.
    """
    prefixes = tuple(f"{v}_" for v in recipe.assignment_variables)
    if not prefixes:
        return []
    return [c for c in ds.df.columns if c.upper().startswith(prefixes)]


def render(
    suspects: list[Suspect],
    siblings: list[str] | None = None,
    components: list[str] | None = None,
) -> str:
    lines = [f"  warn  possible undeclared assignment: {s.render()}" for s in suspects]
    if lines:
        lines.append(
            "        fully crossed with the declared assignment. Declare it in "
            "`source_vars`, or give a reason in `condition.considered_and_rejected`."
        )
    if siblings:
        lines.append(f"  warn  numbered siblings of the declared assignment: {', '.join(siblings)}")
        lines.append(
            "        the deposit probably holds further arms or a repeated measure. "
            "Declare them, or record the scope decision in "
            "`condition.considered_and_rejected`."
        )
    if components:
        shown = ", ".join(components[:6])
        more = f", and {len(components) - 6} more" if len(components) > 6 else ""
        lines.append(
            f"  note  {len(components)} column(s) suppressed as decompositions of the "
            f"declared assignment: {shown}{more}"
        )
    return "\n".join(lines)
