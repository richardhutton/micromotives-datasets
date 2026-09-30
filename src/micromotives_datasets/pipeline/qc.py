"""Structural checks on built rows. No oracle required.

These run on EVERY study, including the ~120 with no SocSci210 counterpart to
check against. Each rule exists because we saw the corresponding failure in a
real dataset — see docs/verification/.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from ..recipe import Recipe
from ..schema import Row


@dataclass
class QCReport:
    study_id: str
    n_rows: int = 0
    n_participants: int = 0
    rows_per_condition: dict[int, int] = field(default_factory=dict)
    rows_per_task: dict[int, int] = field(default_factory=dict)
    response_distribution: dict[int, int] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.failures

    def render(self) -> str:
        conds = dict(sorted(self.rows_per_condition.items()))
        tasks = dict(sorted(self.rows_per_task.items()))
        lines = [
            f"QC — {self.study_id}",
            f"  rows          {self.n_rows:,}",
            f"  participants  {self.n_participants:,}",
            f"  conditions    {len(conds)}  {conds}",
            f"  tasks         {len(tasks)}  {tasks}",
            f"  responses     {dict(sorted(self.response_distribution.items()))}",
        ]
        for f_ in self.failures:
            lines.append(f"  FAIL  {f_}")
        for w in self.warnings:
            lines.append(f"  warn  {w}")
        lines.append(f"  => {'PASS' if self.passed else 'FAIL'}")
        return "\n".join(lines)


def check(rows: list[Row], recipe: Recipe) -> QCReport:
    rep = QCReport(study_id=recipe.study_id)
    if not rows:
        rep.failures.append("no rows produced")
        return rep

    rep.n_rows = len(rows)
    rep.n_participants = len({r.participant_id for r in rows})
    rep.rows_per_condition = dict(
        Counter(r.condition_num for r in rows if r.condition_num is not None)
    )
    rep.rows_per_task = dict(Counter(r.task_num for r in rows if r.task_num is not None))
    rep.response_distribution = dict(
        Counter(int(r.response_num) for r in rows if r.response_num is not None)
    )

    # --- Rule 1: distinct conditions must produce distinct text -------------
    # Two conditions rendering the same string means a manipulation was lost.
    # This is the failure we found in SocSci210's `sd7cf`, where 12 conditions
    # collapsed into 3 distinct stimulus strings.
    text_by_cond: dict[int, set[str]] = {}
    for r in rows:
        if r.condition_num is not None:
            text_by_cond.setdefault(r.condition_num, set()).add(r.condition)
    seen: dict[str, int] = {}
    for cond, texts in sorted(text_by_cond.items()):
        for t in texts:
            if t in seen and seen[t] != cond:
                rep.failures.append(
                    f"conditions {seen[t]} and {cond} render identical text "
                    "— a manipulation has been lost"
                )
            seen[t] = cond

    # --- Rule 2: every declared arm must appear -----------------------------
    declared = {a.condition_num for a in recipe.condition.arms}
    produced = set(rep.rows_per_condition)
    if missing := declared - produced:
        rep.warnings.append(f"declared arms with no rows: {sorted(missing)}")
    if extra := produced - declared:
        rep.failures.append(f"rows in undeclared arms: {sorted(extra)}")

    # --- Rule 3: every declared outcome must appear -------------------------
    declared_tasks = {o.task_num for o in recipe.outcomes}
    if missing_t := declared_tasks - set(rep.rows_per_task):
        rep.warnings.append(f"declared outcomes with no rows: {sorted(missing_t)}")

    # --- Rule 4: responses inside the declared scale ------------------------
    allowed = set(recipe.response_recode.values())
    if bad := set(rep.response_distribution) - allowed:
        rep.failures.append(f"responses outside declared scale: {sorted(bad)}")

    # --- Rule 5: each factor must actually vary in the rendered text --------
    # Guards against a factor being declared but never expressed — the failure
    # mode behind SocSci210's inverted/dropped factors.
    for factor in recipe.condition.factors:
        levels = {a.factors.get(factor) for a in recipe.condition.arms}
        if len(levels) < 2:
            rep.warnings.append(f"factor {factor!r} has fewer than 2 levels")
            continue
        texts_by_level: dict[str | None, set[str]] = {}
        for a in recipe.condition.arms:
            texts_by_level.setdefault(a.factors.get(factor), set()).add(a.text)
        flat = [t for ts in texts_by_level.values() for t in ts]
        if len(set(flat)) == 1:
            rep.failures.append(f"factor {factor!r} varies but arm text never changes")

    # --- Rule 6: no empty condition text ------------------------------------
    if any(not r.condition.strip() for r in rows):
        rep.failures.append("empty condition text on some rows")

    return rep
