"""The per-study Recipe: the human-authored judgment that drives a build.

A recipe captures §8 stages 2-4 of the pipeline (identify condition/outcome,
map persona, assemble arm->text) as a reviewable YAML file. The melt
(`pipeline.build`) is then pure and deterministic.

Three design rules, each learned from auditing SocSci210's own reconstruction
(see docs/verification/):

1. **Factors are first-class.** An arm records its factor levels, not just a
   number. SocSci210 lost a whole factor in one study and inverted one in
   another because the design was flattened to a single label.
2. **The condition mapping is declared, never inferred.** `raw -> condition_num`
   is written out per arm. There is no universal rule: one audited study used
   `raw - 1`, another had the arms reversed.
3. **The response recode is an explicit value map**, not arithmetic, so it can
   be read and checked against the source codebook.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator


class Scale(BaseModel):
    """The response scale for an outcome, used to build the answer instruction."""

    min: int
    max: int
    min_label: str | None = None
    max_label: str | None = None
    nominal: bool = Field(
        default=False,
        description="True when the codes are an UNORDERED choice rather than a scale. "
        "Naming endpoints then asserts an ordering that does not exist: `cug34`'s "
        "B09 codes are 'each pay half' / 'Michelle pays all' / 'Anthony pays all', "
        "so calling 1 and 3 the endpoints implies Michelle-pays-all lies between "
        "them, when it is the opposite pole of the gender dimension being measured. "
        "The options must instead be enumerated in the question text.",
    )

    def instruction(self) -> str:
        """e.g. 'Only return an integer from -3 to 3 where -3 means "Very bad"...'"""
        if self.nominal:
            # No endpoints, and no "from x to y" either — that phrasing reads as a
            # range. The options belong in the question, where they carry no order.
            codes = ", ".join(str(c) for c in range(self.min, self.max))
            return f"Only return one of {codes} or {self.max}, nothing else."
        base = f"Only return an integer from {self.min} to {self.max}"
        if self.min_label and self.max_label:
            base += (
                f' where {self.min} means "{self.min_label}"'
                f' and {self.max} means "{self.max_label}"'
            )
        return base + ", nothing else."

    @model_validator(mode="after")
    def _check_nominal(self) -> Scale:
        if self.nominal and (self.min_label or self.max_label):
            raise ValueError(
                "a nominal scale must not carry min_label/max_label — they would "
                "assert an ordering it does not have; enumerate the options in the "
                "outcome `question` instead"
            )
        return self


class ItemOverride(BaseModel):
    """What one arm did to ONE outcome item, keyed by `task_num` on the arm.

    The four fields on `Arm` below (`outcome_var`, `response_recode`,
    `outcome_question`, `scale`) apply to every outcome of that arm, which is
    right for a split-ballot study where the arm IS the item. It is wrong
    whenever a study crosses arms with items, and that case is not rare — it
    currently blocks roughly 60,000 rows across four studies already built and
    verified:

      `evnyh`  holds its answers in 60 columns, one per (item x arm). Nine of
               its ten items are unreachable because the answer VARIABLE varies
               by both, and `Arm.outcome_var` can only name one.
      `cug34`  needs two outcomes of the same arm to carry different question
               text; `Arm.outcome_question` applies to all of them.
      `z358z`  the same, on Q1/Q2.

    An item-level override is also safer than the blanket kind, which is why it
    takes precedence unconditionally. `scale_for` has to guard the arm-level
    scale — an arm must not leak its scale onto an outcome that named its own
    variable, which cost 8,774 rows of `evnyh` an answer instruction that
    contradicted the response. An override that names its task cannot leak,
    because it has said exactly which cell it describes.
    """

    outcome_var: str | None = Field(
        default=None, description="Variable holding THIS arm's answer to THIS item."
    )
    outcome_question: str | None = Field(
        default=None, description="Question wording for this (arm, item) cell."
    )
    scale: Scale | None = Field(default=None, description="Response scale for this cell.")
    response_recode: dict[int, int] | None = Field(
        default=None, description="raw->canonical answer map for this cell."
    )


class Arm(BaseModel):
    """One randomised arm: its raw code, its canonical index, and what it showed."""

    raw: int | None = Field(
        default=None, description="Value of the single source condition variable."
    )
    raw_values: dict[str, int] | None = Field(
        default=None,
        description="Value of EACH source variable, when the assignment is split across "
        "several (a 2x2 held as two separate randomisation variables). Use with "
        "Condition.source_vars.",
    )
    condition_num: int = Field(description="Canonical 0-based index. DECLARED, never inferred.")
    factors: dict[str, str] = Field(
        default_factory=dict,
        description="Factor levels for this arm, e.g. {label: Atheist, biography: present}. "
        "Used by QC to check every factor is actually expressed in the text.",
    )
    text: str = Field(description="What this arm saw. Verbatim for what varies.")

    # --- question-wording designs ------------------------------------------
    # In a split-ballot study each arm is asked a DIFFERENT variable, and the
    # answer codes may be reversed between arms (option-order experiments).
    # Both are declared per arm so a reversal can never be applied silently.
    outcome_var: str | None = Field(
        default=None,
        description="Variable holding this arm's answer, when the outcome variable "
        "differs by arm (split-ballot). Overrides Outcome.var.",
    )
    response_recode: dict[int, int] | None = Field(
        default=None,
        description="Arm-specific raw->canonical answer map, for arms whose response "
        "options are presented in a different order. Overrides Recipe.response_recode.",
    )
    outcome_question: str | None = Field(
        default=None,
        description="Arm-specific question wording, when arms are asked different "
        "questions (e.g. how DISAPPOINTED under a loss framing vs how SATISFIED "
        "under a gain framing). Overrides Outcome.question.",
    )
    scale: Scale | None = Field(
        default=None,
        description="Arm-specific response scale, when the arm's question uses "
        "different endpoint labels. Overrides Outcome.scale.",
    )
    items: dict[int, ItemOverride] = Field(
        default_factory=dict,
        description="Overrides for individual outcome items, keyed by the outcome's "
        "`task_num`. Use when arms are CROSSED with items rather than being items. "
        "Beats every other override, because it names the exact cell.",
    )


class Condition(BaseModel):
    """The experimental manipulation."""

    source_var: str | None = Field(
        default=None, description="Variable in the data holding the arm code."
    )
    source_vars: list[str] = Field(
        default_factory=list,
        description="Several variables that JOINTLY define the arm, when a factorial "
        "design is randomised through one variable per factor rather than a single "
        "combined code. Each arm then declares `raw_values` for all of them.",
    )
    shared_context: str | None = Field(
        default=None,
        description="Context identical across arms, stated ONCE rather than repeated "
        "per arm. Leave empty when arms differ wholesale.",
    )
    factors: list[str] = Field(
        default_factory=list, description="Names of the design factors, e.g. [label, biography]."
    )
    considered_and_rejected: dict[str, str] = Field(
        default_factory=dict,
        description="Variables that LOOK like a second randomisation but are not part of "
        "this experiment's assignment, mapped to the reason why. Silences the "
        "undeclared-assignment screen for that variable, and records the judgment "
        "rather than leaving it implicit.",
    )
    arms: list[Arm]

    def render(self, arm: Arm) -> str:
        """shared_context + arm text -> the condition string."""
        if self.shared_context:
            return f"{self.shared_context.strip()} {arm.text.strip()}"
        return arm.text.strip()

    @property
    def variables(self) -> list[str]:
        """Every variable needed to determine an arm."""
        return self.source_vars or ([self.source_var] if self.source_var else [])

    def key_for(self, values: dict[str, int]) -> tuple[int, ...]:
        """The lookup key for a respondent's assignment codes."""
        return tuple(values[v] for v in self.variables)

    def by_raw(self) -> dict[tuple[int, ...], Arm]:
        """Arms indexed by their assignment key (a 1-tuple in the usual case)."""
        out: dict[tuple[int, ...], Arm] = {}
        for arm in self.arms:
            if self.source_vars:
                assert arm.raw_values is not None
                out[tuple(arm.raw_values[v] for v in self.source_vars)] = arm
            else:
                assert arm.raw is not None
                out[(arm.raw,)] = arm
        return out


class Outcome(BaseModel):
    """One outcome question the respondent answered."""

    var: str | None = Field(
        default=None,
        description="Variable holding the answer. Omit in split-ballot designs, where "
        "each Arm names its own `outcome_var` instead.",
    )
    task_num: int = Field(description="Canonical 0-based item index.")
    question: str = Field(description="The question wording.")
    scale: Scale
    response_recode: dict[int, int] | None = Field(
        default=None,
        description="Item-specific raw->canonical map, for studies whose outcomes are on "
        "different scales (e.g. one banded in dollars, another in minutes). Overridden "
        "by an Arm's own recode.",
    )

    # --- within-subject designs --------------------------------------------
    # `Condition.source_var` resolves ONE arm per respondent, which assumes the
    # assignment is between subjects. In a within-subject vignette design it is
    # not: `b87sm` showed each respondent eight vignettes drawn without
    # replacement from a universe of 72, and which of the 72 appeared in slot k
    # is held in its own variable `P_S{k}`. One arm per respondent can therefore
    # only ever build one slot — the recipe says so in its own notes, and seven
    # eighths of that study's vignette observations (about 40,900 rows) sit
    # outside it.
    #
    # Declaring the assignment variable on the OUTCOME says what is true: the 72
    # arms are shared, and each item records which one it showed.
    condition_var: str | None = Field(
        default=None,
        description="Variable holding the arm code FOR THIS ITEM, when assignment varies "
        "within respondent (a vignette shown in slot k). Overrides Condition.source_var.",
    )
    condition_vars: list[str] = Field(
        default_factory=list,
        description="Per-item equivalent of Condition.source_vars, for a within-subject "
        "factorial. Must list the same factors in the same order.",
    )


class Recipe(BaseModel):
    """Everything needed to melt one study into (P, c, o, r) rows."""

    study_id: str
    source: str = Field(description="socsci210 | tess | dataverse | innovation_panel | bes")
    title: str | None = None
    data_file: str = Field(description="Filename of the data file inside data/raw/<study_id>/.")
    licence: str | None = Field(
        default=None,
        description="The deposit's licence, as the deposit itself states it — e.g. "
        "'CC0 1.0 Universal (OSF deposit)', or 'none stated' where the archive "
        "gives none. CLAUDE.md's definition of done requires source, licence AND "
        "provenance; source and provenance were recorded richly from the start and "
        "licence was recorded in 0 of 14 studies, which nothing noticed because "
        "nothing asked. QC rule 16 asks. "
        "Record what the deposit says, not what seems likely: 'none stated' is a "
        "fact about the deposit and a useful one, a guessed licence is neither.",
    )
    notes: str | None = None
    experiment: str | None = Field(
        default=None,
        description="Names the sub-experiment when one deposit contains several "
        "independent experiments (one recipe file each), e.g. 'RO1'.",
    )
    comparable_to_socsci210: bool = Field(
        default=True,
        description="False when SocSci210 reconstructed a different scope for this study "
        "(a subset of arms, or arms merged), so a numeric crosscheck is meaningless.",
    )

    condition: Condition
    outcomes: list[Outcome]

    response_recode: dict[int, int] = Field(
        description="Explicit raw-value -> canonical-response map. Values not listed are dropped."
    )
    missing_codes: list[int] = Field(
        default_factory=list, description="Codes meaning refused/not-asked. Dropped per item."
    )
    persona_map: dict[str, str] = Field(
        default_factory=dict, description="Persona field -> source variable name."
    )
    persona_missing: dict[str, list[int]] = Field(
        default_factory=dict,
        description="Source variable -> codes that mean refused / not asked / missing. "
        "The field is left EMPTY for those respondents rather than rendering the "
        "sentinel's label. Use this when the code carries no answer.",
    )
    persona_label_rewrite: dict[str, dict[int, str]] = Field(
        default_factory=dict,
        description="Source variable -> {code: replacement label}. Use this when the "
        "code IS a real answer but the panel's label carries scripting boilerplate — "
        "`REL1` code 11 is labelled 'Other Christian religion, please specify', which "
        "is a genuine response wearing an instruction. Dropping it would lose the "
        "answer; rewriting keeps it.",
    )

    @model_validator(mode="after")
    def _check(self) -> Recipe:
        nums = [a.condition_num for a in self.condition.arms]
        if len(set(nums)) != len(nums):
            raise ValueError(f"duplicate condition_num in {self.study_id}: {nums}")
        if not self.condition.variables:
            raise ValueError(f"{self.study_id}: condition needs source_var or source_vars")
        if self.condition.source_vars:
            for arm in self.condition.arms:
                missing = set(self.condition.source_vars) - set(arm.raw_values or {})
                if missing:
                    raise ValueError(
                        f"{self.study_id}: an arm is missing raw_values for {sorted(missing)}"
                    )
        else:
            if any(a.raw is None for a in self.condition.arms):
                raise ValueError(f"{self.study_id}: every arm needs `raw`")
        # Build the key list from the arms directly — by_raw() is a dict, so
        # duplicates would silently collapse and never be caught.
        keys = [
            tuple(arm.raw_values[v] for v in self.condition.source_vars)  # type: ignore[index]
            if self.condition.source_vars
            else (arm.raw,)
            for arm in self.condition.arms
        ]
        if len(set(keys)) != len(keys):
            raise ValueError(f"duplicate raw arm code in {self.study_id}: {keys}")
        tasks = [o.task_num for o in self.outcomes]
        if len(set(tasks)) != len(tasks):
            raise ValueError(f"duplicate task_num in {self.study_id}: {tasks}")
        # Every declared factor must be present on every arm.
        for arm in self.condition.arms:
            missing = set(self.condition.factors) - set(arm.factors)
            if missing:
                raise ValueError(f"arm raw={arm.raw} missing factor(s) {sorted(missing)}")
        # Every outcome must get its variable from somewhere: the outcome itself,
        # (split-ballot) every arm, or an item-level override on every arm.
        arms_have_var = all(a.outcome_var for a in self.condition.arms)
        for outcome in self.outcomes:
            items_have_var = all(
                (ov := a.items.get(outcome.task_num)) is not None and ov.outcome_var
                for a in self.condition.arms
            )
            if not outcome.var and not arms_have_var and not items_have_var:
                raise ValueError(
                    f"outcome task_num={outcome.task_num} has no `var`, and neither every "
                    "arm's `outcome_var` nor every arm's item override supplies one"
                )
        # An item override keyed by a task_num no outcome has is dead text that
        # looks live. Silently ignoring it is how an answer variable goes
        # unapplied — a typo'd key would leave the blanket arm-level value in
        # force and read, in review, as though the override had taken effect.
        declared_tasks = {o.task_num for o in self.outcomes}
        for arm in self.condition.arms:
            stray = sorted(set(arm.items) - declared_tasks)
            if stray:
                raise ValueError(
                    f"{self.study_id}: arm raw={arm.raw} has item override(s) for "
                    f"task_num {stray}, which no outcome declares"
                )
        # A per-item assignment must describe the same factors in the same order
        # as the study-level one, because arms are keyed by that tuple. A
        # different length would miss every arm and build nothing; a different
        # ORDER would silently match the wrong arm, which is worse.
        width = len(self.condition.variables)
        for outcome in self.outcomes:
            if outcome.condition_var and outcome.condition_vars:
                raise ValueError(
                    f"outcome task_num={outcome.task_num} declares both `condition_var` "
                    "and `condition_vars` — use one"
                )
            own = self.condition_vars_for(outcome)
            if len(own) != width:
                raise ValueError(
                    f"outcome task_num={outcome.task_num} names {len(own)} condition "
                    f"variable(s) {own} but the arms are keyed by {width} "
                    f"({self.condition.variables}) — the key would never match"
                )
        return self

    @property
    def assignment_variables(self) -> set[str]:
        """Every variable this recipe uses to assign an arm, upper-cased.

        The study-level condition plus any per-item assignment. The screens need
        the full set and the melt needs them separately, so the distinction is
        kept rather than collapsed: a variable named here has been DECLARED, and
        must not then be reported as an undeclared second randomisation.

        This is the same coupling that cost `b87sm` 35 spurious warnings once —
        rule 11's suppression was derived from rule 9's reporting. A per-item
        assignment variable is declared in a new place, so anything asking "is
        this variable part of the design?" has to ask here, not at
        `condition.variables`.
        """
        out = {v.upper() for v in self.condition.variables}
        for outcome in self.outcomes:
            out |= {v.upper() for v in self.condition_vars_for(outcome)}
        return out

    def item_for(self, outcome: Outcome, arm: Arm) -> ItemOverride | None:
        """This arm's override for this specific item, if it declared one."""
        return arm.items.get(outcome.task_num)

    def condition_vars_for(self, outcome: Outcome) -> list[str]:
        """The variable(s) holding the arm code for this item.

        The outcome's own declaration wins, because an outcome only names one
        when the assignment genuinely varies within respondent; otherwise the
        study-level condition applies to every item, as before.
        """
        if outcome.condition_vars:
            return outcome.condition_vars
        if outcome.condition_var:
            return [outcome.condition_var]
        return self.condition.variables

    def recode_for(self, arm: Arm, outcome: Outcome | None = None) -> dict[int, int]:
        """The answer map to use, most specific first.

        Item beats arm beats outcome beats study. An arm-level map exists
        because that arm *presented* the options differently (option-order
        experiments); an outcome-level map exists because that item is on a
        different scale (dollars vs minutes). Arm beats outcome because it
        describes what was shown; an item-level map beats both because it names
        the one cell it is about.
        """
        if outcome is not None:
            item = self.item_for(outcome, arm)
            if item is not None and item.response_recode is not None:
                return item.response_recode
        if arm.response_recode is not None:
            return arm.response_recode
        if outcome is not None and outcome.response_recode is not None:
            return outcome.response_recode
        return self.response_recode

    def outcome_var_for(self, outcome: Outcome, arm: Arm) -> str | None:
        """The variable holding this arm's answer to this outcome."""
        item = self.item_for(outcome, arm)
        if item is not None and item.outcome_var is not None:
            return item.outcome_var
        return outcome.var or arm.outcome_var

    def scale_for(self, outcome: Outcome, arm: Arm) -> Scale:
        """The scale whose answer instruction this row carries.

        An arm-level override exists because in a split-ballot the ARM supplies
        the item: it names `outcome_var` and its own endpoint labels. When the
        OUTCOME names its own `var`, the arm is not supplying that item and its
        scale must not leak onto it.

        Getting this wrong was silent and severe. `evnyh` declares a per-cell 1-5
        scale on every arm (it must, for the experimental item) and a 0-7 scale on
        each of its ten open-ended validation outcomes. Under a bare
        `arm.scale or outcome.scale`, all ten rendered "return an integer from 1
        to 5" over responses that ran 0-7 — 8,774 rows, 47.3% of that study,
        carrying an answer instruction their own response contradicts, with the
        direction inverted on top. QC passed with zero warnings, because rule 4
        checks the union of declared RECODES and cannot see the rendered scale.

        `outcome_var_for` already prefers the outcome; this keeps the two
        resolutions consistent instead of opposite.

        An ITEM-level scale needs no such guard and so comes first: it has named
        the task it belongs to, and cannot be applied to an item it was not
        written for.
        """
        item = self.item_for(outcome, arm)
        if item is not None and item.scale is not None:
            return item.scale
        if outcome.var is None and arm.scale is not None:
            return arm.scale
        return outcome.scale

    def outcome_text_for(self, outcome: Outcome, arm: Arm) -> str:
        """The rendered outcome: question + answer instruction.

        Arm-level overrides apply only where the arm supplies the item — see
        `scale_for`. An item-level override always applies, for the same reason.
        """
        item = self.item_for(outcome, arm)
        question = (
            (item.outcome_question if item is not None else None)
            or (arm.outcome_question if outcome.var is None else None)
            or outcome.question
        )
        return f"{question} {self.scale_for(outcome, arm).instruction()}"


def load(path: str | Path) -> Recipe:
    """Load and validate a recipe YAML."""
    data: dict[str, Any] = yaml.safe_load(Path(path).read_text())
    return Recipe.model_validate(data)
