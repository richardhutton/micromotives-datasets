"""Structural checks on built rows. No oracle required.

These run on EVERY study, including the ~120 with no SocSci210 counterpart to
check against. Each rule exists because we saw the corresponding failure in a
real dataset — see docs/verification/.
"""

from __future__ import annotations

import itertools
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

    # --- Rule 10: every arm must be measured about as thoroughly -------------
    # Found on `9263n`, where six of seven items are asked with a different
    # variable per branch (`Q3A` for the experiential arms, `Q3B` for the
    # material ones). Declaring only the A variants halved the corpus and left
    # arms 2 and 3 with one item out of seven — and QC passed, silently.
    #
    # Counting per OUTCOME would warn on every legitimately branched item (12 of
    # 14 here), which trains us to ignore the column. Counting per ARM is silent
    # when branching is symmetric and loud when it is not.
    tasks_per_arm: dict[int, set[int]] = {}
    for r in rows:
        if r.condition_num is not None and r.task_num is not None:
            tasks_per_arm.setdefault(r.condition_num, set()).add(r.task_num)
    if len(tasks_per_arm) > 1:
        widest = max(len(t) for t in tasks_per_arm.values())
        thin = {cond: len(t) for cond, t in sorted(tasks_per_arm.items()) if len(t) < 0.5 * widest}
        if thin:
            rep.warnings.append(
                f"arms measured on far fewer outcomes than their peers: {thin} "
                f"against {widest} — if the design is branched this is expected, "
                "otherwise an outcome variable for those arms is missing"
            )

    # --- Rule 4: responses inside the declared scale ------------------------
    # A recode can be declared at study, outcome or arm level, so the allowed
    # set is the union of all of them.
    allowed = set(recipe.response_recode.values())
    for outcome in recipe.outcomes:
        if outcome.response_recode:
            allowed |= set(outcome.response_recode.values())
    for arm in recipe.condition.arms:
        if arm.response_recode:
            allowed |= set(arm.response_recode.values())
    if bad := set(rep.response_distribution) - allowed:
        rep.failures.append(f"responses outside declared scale: {sorted(bad)}")

    # --- Rule 5: each factor must actually vary in the rendered text --------
    # Guards against a factor being declared but never expressed — the failure
    # mode behind SocSci210's inverted/dropped factors.
    #
    # Compare MINIMAL PAIRS: two arms differing in this factor and nothing else
    # must render different text. Anything looser is vacuous. The first version
    # of this rule failed only when *every* arm rendered identically, which
    # rule 1 already catches — so it passed a factor provably absent from all
    # arm text, and contributed nothing on the first eight studies.
    for factor in recipe.condition.factors:
        levels = {a.factors.get(factor) for a in recipe.condition.arms}
        if len(levels) < 2:
            rep.warnings.append(f"factor {factor!r} has fewer than 2 levels")
            continue
        others = [o for o in recipe.condition.factors if o != factor]
        pairs = [
            (a, b)
            for a, b in itertools.combinations(recipe.condition.arms, 2)
            if a.factors.get(factor) != b.factors.get(factor)
            and all(a.factors.get(o) == b.factors.get(o) for o in others)
        ]
        # No minimal pair means the factor is nested rather than crossed — e.g.
        # "did the doctor heed the computer?" is undefined in the arms with no
        # computer. That is a legitimate augmented factorial, not a defect, so
        # say the test could not run rather than passing it silently.
        if not pairs:
            rep.warnings.append(
                f"factor {factor!r} is nested, not crossed — no minimal pair exists, "
                "so its effect on the text could not be tested"
            )
            continue
        # split() so reflowing a YAML block does not read as a difference.
        same = [(a.raw, b.raw) for a, b in pairs if a.text.split() == b.text.split()]
        if same:
            rep.failures.append(
                f"factor {factor!r} does not change the arm text for {same} "
                "— declared but not expressed"
            )

    # --- Rule 6: no empty condition text ------------------------------------
    if any(not r.condition.strip() for r in rows):
        rep.failures.append("empty condition text on some rows")

    # --- Rules 7-8: banded recodes must behave like a quantity --------------
    # SocSci210 converted "1-4 minutes" and "1-3 hours" both to 1, under a
    # stimulus reading "hours saved" — a 60x error that made the two bands
    # indistinguishable. Both checks below catch that class without needing a
    # questionnaire, a model, or an oracle.
    for label, recode in _all_recodes(recipe):
        values = [recode[k] for k in sorted(recode)]

        # 7: monotonic in EITHER direction. Increasing is the normal case;
        # decreasing is a legitimately reverse-coded scale (very common). What
        # is never legitimate is a mixed direction — values climbing, dropping
        # back, then climbing again, which is what a unit switch looks like
        # (0,1,5,10,20,40 minutes then 1,4,7 hours).
        if values != sorted(values) and values != sorted(values, reverse=True):
            rep.failures.append(
                f"{label} recode changes direction: {values} — band order and value order "
                "only partly agree, which usually means a unit switch or a parsing error"
            )

        # 8: injective — two distinct bands must not collapse onto one value.
        dupes = {v for v in values if values.count(v) > 1}
        if dupes:
            collisions = {v: [k for k in sorted(recode) if recode[k] == v] for v in sorted(dupes)}
            rep.failures.append(
                f"{label} recode maps distinct bands to the same value: {collisions} "
                "— a distinction in the source has been lost"
            )

    return rep


def _all_recodes(recipe: Recipe) -> list[tuple[str, dict[int, int]]]:
    """Every declared recode, labelled by where it came from."""
    out: list[tuple[str, dict[int, int]]] = [("study", recipe.response_recode)]
    for outcome in recipe.outcomes:
        if outcome.response_recode:
            out.append((f"outcome task_num={outcome.task_num}", outcome.response_recode))
    for arm in recipe.condition.arms:
        if arm.response_recode:
            out.append((f"arm raw={arm.raw}", arm.response_recode))
    return out
