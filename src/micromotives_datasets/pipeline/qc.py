"""Structural checks on built rows. No oracle required.

These run on EVERY study, including the ~120 with no SocSci210 counterpart to
check against. Each rule exists because we saw the corresponding failure in a
real dataset — see docs/verification/.
"""

from __future__ import annotations

import itertools
import re
from collections import Counter
from dataclasses import dataclass, field

from ..recipe import Recipe
from ..schema import Row

# Panel non-answer labels and scripting boilerplate, as they actually appear in
# TESS value labels. See rule 12.
_NON_ANSWER = re.compile(
    r"please specify|refused|missing|not asked|skipped|don'?t know|no answer", re.I
)


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
    # A rule that declined to run, and why. Distinct from a warning: nothing is
    # wrong, but a check a reader would assume had run did not, and silently
    # skipping it would let a real defect hide behind an unexamined PASS.
    notes: list[str] = field(default_factory=list)

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
        for n in self.notes:
            lines.append(f"  note  {n}")
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
    #
    # The rule only has purchase on a BETWEEN-SUBJECTS design, where every
    # respondent in an arm is asked every item, so uneven coverage can only mean
    # a missing variable. Where an outcome carries its own `condition_var` the
    # arm varies within respondent, and coverage is then set by how often each
    # arm happened to be DRAWN — which the rule cannot distinguish from a defect.
    #
    # Measured on the first conjoint built here, `8ctbk`: 1,146 profiles crossed
    # with 10 task slots, so a profile drawn 4 times cannot span more than 4 of
    # the 10 and the rule fired on nearly every arm. The two obvious repairs both
    # fail — counting per (participant, arm) silences `8ctbk` but then fires on
    # `b87sm`, where slot 1 legitimately carries 3 items and slots 2-8 carry 1,
    # and loosening the 0.5 threshold gives up the `9263n` defect it exists for.
    # So it is skipped, and says so: a rule that cannot tell design from defect
    # on a class of design should decline, not guess.
    within_subject = any(
        recipe.condition_vars_for(o) != recipe.condition.variables for o in recipe.outcomes
    )
    if within_subject:
        rep.notes.append(
            "rule 10 (per-arm outcome coverage) skipped: this design assigns arms "
            "per item, so coverage reflects how often each arm was drawn rather "
            "than whether an outcome variable is missing"
        )
    else:
        tasks_per_arm: dict[int, set[int]] = {}
        for r in rows:
            if r.condition_num is not None and r.task_num is not None:
                tasks_per_arm.setdefault(r.condition_num, set()).add(r.task_num)
        if len(tasks_per_arm) > 1:
            widest = max(len(t) for t in tasks_per_arm.values())
            thin = {
                cond: len(t) for cond, t in sorted(tasks_per_arm.items()) if len(t) < 0.5 * widest
            }
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

    # --- Rule 13: the response must fit the scale the ROW'S OWN TEXT states --
    # Rule 4 checks the union of all declared recodes, which is structurally
    # blind to the rendered instruction. `evnyh` emitted "return an integer from
    # 1 to 5" on 16,824 rows whose responses ran 0-7 — direction inverted on top
    # — and QC passed with zero warnings, because every one of those values IS in
    # some declared recode.
    #
    # Resolved through `recipe.scale_for`, the same call the melt uses, so this
    # rule and the rendering can never drift apart.
    by_cond = {a.condition_num: a for a in recipe.condition.arms}
    by_task = {o.task_num: o for o in recipe.outcomes}
    outside: Counter[tuple[int, int]] = Counter()
    for r in rows:
        r_arm = by_cond.get(r.condition_num) if r.condition_num is not None else None
        r_out = by_task.get(r.task_num) if r.task_num is not None else None
        if r_arm is None or r_out is None or r.response_num is None:
            continue
        scale = recipe.scale_for(r_out, r_arm)
        if not scale.min <= r.response_num <= scale.max:
            outside[(r.condition_num, r.task_num)] += 1  # type: ignore[index]
    if outside:
        rep.failures.append(
            "responses outside the scale their own outcome text states, per "
            f"(condition, task): {dict(sorted(outside.items()))} — the rendered answer "
            "instruction contradicts the response it is attached to"
        )

    # --- Rule 14: persona values must be in the canonical vocabulary --------
    # The crosswalk passes an unmapped label through unchanged rather than
    # blanking it, because silently thinning the corpus as new schemes arrive is
    # the exact failure this whole layer exists to prevent. So the loudness has
    # to live here: a sixth ethnicity scheme, or a new income banding, shows up
    # as a warning naming the values rather than as quietly divergent personas.
    from .._persona_vocab import unmapped_values

    if stray := unmapped_values(rows):
        shown = "; ".join(f"{f}: {sorted(v)[:3]}" for f, v in sorted(stray.items()))
        rep.warnings.append(
            f"persona values outside the canonical vocabulary — {shown} "
            "— re-run scripts/persona_harmonise.py for those fields, or the corpus "
            "will describe the same person two ways"
        )

    # --- Rule 12: no persona field may render a non-answer label ------------
    # Found by sweeping built rows across the whole corpus: 5 of 14 recipes were
    # putting panel boilerplate into persona text, and `b87sm` shipped 93 rows of
    # `religion: "SKIPPED ON WEB"` with a 335-line notes block that never
    # mentioned persona. Nothing caught it because nothing looked.
    #
    # Two distinct causes, which is why there are two escape hatches. A sentinel
    # ("Refused", "SKIPPED ON WEB") carries no answer and belongs in
    # `persona_missing`. But `cug34`'s 685 rows read "Other Christian religion,
    # please specify" — a real answer wearing an interviewer instruction, which
    # dropping would discard; that belongs in `persona_label_rewrite`.
    dirty: Counter[str] = Counter()
    for r in rows:
        for pfield, value in r.persona.model_dump().items():
            if pfield == "extra" or not isinstance(value, str):
                continue
            if m := _NON_ANSWER.search(value):
                dirty[f"{pfield}={m.group(0)!r}"] += 1
    if dirty:
        worst = ", ".join(f"{k} x{v}" for k, v in dirty.most_common(4))
        rep.warnings.append(
            f"persona fields carrying a non-answer label: {worst} "
            "— use `persona_missing` for sentinels that carry no answer, or "
            "`persona_label_rewrite` where the code is a real answer with a dirty label"
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

    # --- Rule 15: no row may cite its own position in a sequence ------------
    # `b87sm` carried "Please read Scenario #1 carefully." in `shared_context`,
    # so 13,513 of its 19,282 rows (70.1%) told the respondent they were reading
    # scenario 1 while rating scenario 2 through 8. Nothing existing could see
    # it: the 72 arms still rendered 72 distinct strings (rules 1 and 5
    # satisfied), the arm text matched the source byte-for-byte, the row counts
    # reconciled exactly, and QC passed with no warnings. It was visible only by
    # reading a row and asking what it said.
    #
    # The general fault is not the wrong number, it is citing a position at all.
    # A row is one (persona, condition, outcome, response) tuple with no way to
    # express "this is the fifth of eight screens you have seen", so a numbered
    # self-reference asserts a sequence the row cannot represent — and in a
    # within-subject design it is additionally wrong for most rows.
    #
    # Numbered references only. Measured across all 14 built studies this
    # pattern has zero matches once `b87sm` is fixed, while a pattern that also
    # caught "the following scenario" would fire on two studies where the phrase
    # is a forward reference inside the same row and perfectly correct.
    signposts: Counter[str] = Counter()
    for r in rows:
        for text in (r.condition, r.outcome):
            for m in _SIGNPOST.finditer(str(text)):
                signposts[" ".join(m.group(0).split())] += 1
    if signposts:
        rep.warnings.append(
            f"row text cites a position in a sequence: {dict(signposts)} — a row cannot "
            "say which of several screens it was, and in a within-subject design the "
            "number is wrong for most rows. Drop the signpost, or record why it belongs"
        )

    # --- Rule 16: the deposit's licence must be recorded --------------------
    # CLAUDE.md's definition of done asks for "source, licence and provenance
    # recorded". Source and provenance were recorded richly from the first
    # study — adapter, study id, line citations into the instrument — and
    # licence was recorded in ZERO of fourteen, which nothing noticed because
    # nothing asked. An unrecorded licence is the one provenance gap that can
    # make a built row unpublishable, and it is cheapest to answer while the
    # deposit page is still open.
    if not (recipe.licence or "").strip():
        rep.warnings.append(
            "no licence recorded for this deposit — see `Recipe.licence`. Write what "
            "the deposit itself states, including 'none stated' where it states none"
        )

    return rep


# A numbered self-reference, e.g. "Scenario #1", "Question 3", "part 2". NOT
# "the following scenario", which points inside the same row and is correct.
_SIGNPOST = re.compile(
    r"\b(?:scenario|vignette|item|question|situation|statement|part|page|screen|section)"
    r"\s+(?:#\s*)?\d+\b",
    re.I,
)


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
