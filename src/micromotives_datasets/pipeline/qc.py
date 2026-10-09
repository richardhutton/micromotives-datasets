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
from typing import Any

from ..recipe import Recipe
from ..schema import Row

# Panel non-answer labels and scripting boilerplate, as they actually appear in
# value labels. See rule 12.
#
# The apostrophe is a CHARACTER CLASS, not a literal. `QQM5MC` spells "Don't
# know" and "Can't remember" with a curly apostrophe (U+2019), which `don'?t`
# silently failed to match — a corpus audit's first run reported both as suspect
# non-answers for exactly that reason. Measured against all 301 persona values in
# `data/catalog/persona_snapshot.json`, widening it this way changes NOTHING that
# is already built: it closes a blind spot rather than altering a verdict.
#
# Widened to "unknown", "dummy" and "prefer not" after a corpus-wide audit of
# every declared missing-code (`scripts/persona_missing_audit.py`). Those three
# are non-answers by any reading, and leaving them out had two costs: the audit
# reported four permanent false positives, which teaches a reader to skim it; and
# rule 12 stayed silent on 618 respondents across `b87sm`, `bf8p2` and `zaqkm`
# whose panel code -1 "Unknown" rendered into a persona as "Ideology: Unknown"
# and "Party identification: Unknown" — exactly what this rule exists to catch.
# Those three recipes now declare it, so the widening leaves no new warning.
#
# "not applicable" was added last, and it is the only term here found by the
# judge rather than by us: `scripts/recipe_prep.py` now prints every label where
# Jev and this regex disagree, and on its first run it reported exactly one —
# `work_responsibilty` = "Not applicable", which Jev called a non-answer at 0.79
# and this list missed. Nothing in the built corpus changes; it closes a hole.
#
# Not widened by guesswork beyond that. A term matching too much deletes real
# answers silently: "na" as a substring swallows "National", "Finance" and
# "Native American".
_NON_ANSWER = re.compile(
    r"please specify|refused|missing|not asked|skipped|don['\u2019]?t know"
    r"|no answer|unknown|dummy|prefer not|can['\u2019]?t remember|n/a|invalid|not applicable",
    re.I,
)


def reads_as_a_non_answer(label: str) -> bool:
    """Does this value label carry an answer, or the absence of one?

    Rule 12's judgement, exposed so nothing has to keep a second copy of it.
    `scripts/persona_missing_audit.py` asks exactly this about a code a recipe
    proposes to DROP, where rule 12 asks it about a label that survived into a
    row — the same question from either side of the melt, and the sort of pair
    that drifts apart when each side owns its own list.

    A keyword list decides this badly at the edges, which is why
    `jev.label_is_a_non_answer` exists for authoring time and this stays a
    backstop. It must never be widened by guesswork: a term that matches too much
    deletes real answers silently, and "na" as a substring swallows "National",
    "Finance" and "Native American".
    """
    return bool(_NON_ANSWER.search(label))


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
    # Compared PER ITEM, because a manipulation is lost only when two arms show
    # the same thing in answer to the SAME question. Comparing across all of a
    # study's items conflates that with a legitimate case: an outcome measured
    # before the arms have diverged, where identical text is the truth.
    #
    # `sh4px` asks four mood items BETWEEN its two writing tasks, so at those
    # items nothing distinguishes an arm yet; its maker excluded all four rather
    # than narrate a treatment the respondent had not reached, costing 4 of 10
    # fielded items. `a2nbf` has the same shape at Q1/Q2.
    #
    # The exemption is not automatic. Both cells must DECLARE a
    # `condition_text` override for that item, so a maker states that the two
    # are deliberately identical there and a reader can argue with it. An
    # undeclared collision still fails — which is the `sd7cf` defect this rule
    # exists for, where 12 conditions collapsed into 3 distinct strings.
    declared_same = {
        (task, arm.condition_num)
        for arm in recipe.condition.arms
        for task, item in arm.items.items()
        if item.condition_text is not None
    }
    by_item: dict[int, dict[int, set[str]]] = {}
    for r in rows:
        if r.condition_num is None or r.task_num is None:
            continue
        by_item.setdefault(r.task_num, {}).setdefault(r.condition_num, set()).add(r.condition)
    for task, per_condition in sorted(by_item.items()):
        seen: dict[str, int] = {}
        for cond, texts in sorted(per_condition.items()):
            for t in texts:
                if t in seen and seen[t] != cond:
                    if (task, cond) in declared_same and (task, seen[t]) in declared_same:
                        continue
                    rep.failures.append(
                        f"conditions {seen[t]} and {cond} render identical text on task "
                        f"{task} — a manipulation has been lost. If they are genuinely "
                        "identical there (an item measured before the arms diverge), "
                        "declare `condition_text` on both"
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
        # A minimal pair is two conditions agreeing on every OTHER factor, which
        # is a GROUP BY rather than a search. Bucketing on the all-but-`factor`
        # key gives exactly the same pairs as comparing every combination, at
        # sum(m^2) over buckets instead of n^2 — and when conditions are nearly
        # all distinct, as in a conjoint, every bucket is a singleton and the
        # work vanishes. Measured identical to the quadratic form on all 30
        # recipes in the corpus (samples for the two large conjoints); EFXNLX at
        # 1,200 conditions went 3.975s to 0.034s, and its full QC pass had been
        # taking 562 of its 564 seconds in this rule alone. A nine-minute check
        # is a check people stop running.
        buckets: dict[tuple[Any, ...], list[Any]] = {}
        for arm in recipe.condition.arms:
            buckets.setdefault(tuple(arm.factors.get(o) for o in others), []).append(arm)
        pairs = [
            (a, b)
            for group in buckets.values()
            if len(group) > 1
            for a, b in itertools.combinations(group, 2)
            if a.factors.get(factor) != b.factors.get(factor)
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
        same = [(a.label, b.label) for a, b in pairs if a.text.split() == b.text.split()]
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

    # --- Rule 17: no row may mention the experiment's own construction ------
    # `es4xw` shipped 32,228 rows (100% of the study) whose condition said four
    # faces "are the same in every version of this photograph" and that the other
    # two are, "in this version", both Black men. A participant was assigned to
    # one condition and could not know versions existed.
    #
    # This is a SIBLING of rule 15, not a widening of it. Rule 15's own comment
    # records that it was deliberately held to numbered references because a
    # pattern also catching "the following scenario" fired falsely on two studies
    # where the phrase is a correct forward reference inside the same row. That
    # measurement still holds, so the narrow rule stays narrow and this one takes
    # the separable class: words about the study's variants and apparatus.
    #
    # Measured over all 27 built experiments: the only match is `5hqan`'s ", in the
    # same position regardless of condition", on all 6,411 rows.
    #
    # A draft also matched "this part of the survey", which I recorded as a second
    # genuine hit without reading the sentence. Read, it is fine: "This part of the
    # survey asked you about sex and gender" names a SECTION, not an arm, asserts
    # nothing a participant could not know, and reveals no variants. Counting a
    # match is not the same as finding a defect, and that branch is gone.
    #
    # Against `es4xw`'s shipped text it fires twice; against its fix, not at all;
    # against `b87sm`'s "Scenario #1", not at all, which is right — that one is
    # rule 15's.
    construction: Counter[str] = Counter()
    for r in rows:
        for text in (r.condition, r.outcome):
            for m in _CONSTRUCTION.finditer(str(text)):
                construction[" ".join(m.group(0).split()).lower()] += 1
    if construction:
        rep.warnings.append(
            f"row text refers to the experiment's own construction: {dict(construction)} "
            "— a participant saw one condition and knew nothing of the others, so this "
            "tells them something they could not have known. Drop it, or record why it "
            "was genuinely on screen"
        )

    # --- Rule 18: no row may render text that is cut off --------------------
    # Two shipped instances, both found by sweeping the corpus rather than by
    # anything in the pipeline:
    #
    #   * Seven studies rendered religion as "Protestant (Baptist, Methodist,
    #     Non-denominational, Lutheran, Presbyterian, Pent" — SPSS truncates a
    #     value label at 120 characters, and two deposits truncate at 80, so a
    #     length test alone would have missed two of the seven. ~27,900 rows.
    #     a42yg's REL1 had the identical fault, was fixed in that one recipe, and
    #     the corpus was never swept — the fifth time this project has fixed a
    #     defect locally and left its siblings standing.
    #
    #   * `8ctbk` rendered a conjoint attribute whose level is "BLANK" as a bare
    #     "4. -" on 5,682 of 17,464 rows (32.5%), telling participants they read a
    #     six-line profile whose fourth line was a hyphen.
    #
    # An unbalanced opening bracket is the precise signal for the first, because
    # a truncated label almost always severs a parenthetical. Measured: 5,714
    # distinct persona values across 7 studies, every one a real truncation, and
    # zero matches in any condition or outcome text.
    cut: Counter[str] = Counter()
    for r in rows:
        for where, text in (("condition", r.condition), ("outcome", r.outcome)):
            if text.count("(") > text.count(")"):
                cut[f"{where}: unclosed bracket, text looks truncated"] += 1
        # Persona is a structured object here, not rendered text, so check its
        # own string fields — the same traversal rule 12 uses. That is also the
        # more precise place to look: it names the field that is truncated
        # ("religion") instead of reporting that something in a long rendered
        # paragraph was.
        for pfield, value in r.persona.model_dump().items():
            if pfield == "extra" or not isinstance(value, str):
                continue
            if value.count("(") > value.count(")"):
                cut[f"persona.{pfield}: unclosed bracket, label looks truncated"] += 1
    if cut:
        rep.warnings.append(
            f"row text appears cut off — {dict(cut)} — recover the full wording from the "
            "questionnaire, or drop the line. A value label truncated by SPSS is still "
            "wrong when it reaches a built row"
        )

    # --- Rule 19: a panel source must identify its respondents ---------------
    # In a panel the same person answers in several waves, and each wave is its
    # own file. `Recipe.participant_id_var` exists so one person keeps one id
    # across all of them; without it the melt falls back to the ROW INDEX and the
    # same person in two waves becomes two unrelated participants.
    #
    # That link is most of why the Innovation Panel is worth its licence. Roughly
    # the same 2,500 people answer experiment after experiment from 2008 to 2024,
    # so this corpus can ask whether behaviour in one experiment predicts
    # behaviour in another — a question SocSci210 cannot pose at all, because its
    # 210 studies are 210 separate samples of different people.
    #
    # A FAILURE rather than a warning, because the loss is silent and total.
    # Nothing downstream looks wrong: row counts are right, conditions are right,
    # every other rule passes, and the link is simply gone. The id must also not
    # be the archive's own person identifier — SN 6849 stores a hash of `pidp`,
    # never `pidp` itself, which links to the whole of Understanding Society.
    if recipe.source == "innovation_panel" and recipe.participant_id_var is None:
        rep.failures.append(
            "a panel source must declare `participant_id_var`. Without it every "
            "respondent is keyed by row index, so the same person in two waves "
            "becomes two unrelated participants, and the wave-on-wave link is lost "
            "with nothing else looking wrong"
        )

    return rep


# Text about the experiment's own apparatus: its variants, its arms, its sections.
# Deliberately NOT a general "version" match. An early draft included
# `versions? of th(is|e)`, which fired on "the latest version of the
# questionnaire" — a legitimate stimulus — and was redundant anyway, since
# es4xw's "every version of this photograph" is caught by the quantifier branch
# below. Each alternative here names the study's own construction.
_CONSTRUCTION = re.compile(
    r"\b(?:in|for)\s+this\s+(?:version|condition|arm|variant|scenario\s+group)\b"
    r"|\b(?:every|each|another|the\s+other)\s+(?:version|condition|arm|variant)\b"
    r"|\bregardless\s+of\s+(?:condition|version|arm|which\s+version)\b"
    r"|\brandomly\s+assigned\b|\bexperimental\s+condition\b",
    re.I,
)


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
            out.append((f"arm {arm.label}", arm.response_recode))
    return out
