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

    def instruction(self) -> str:
        """e.g. 'Only return an integer from -3 to 3 where -3 means "Very bad"...'"""
        base = f"Only return an integer from {self.min} to {self.max}"
        if self.min_label and self.max_label:
            base += (
                f' where {self.min} means "{self.min_label}"'
                f' and {self.max} means "{self.max_label}"'
            )
        return base + ", nothing else."


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


class Recipe(BaseModel):
    """Everything needed to melt one study into (P, c, o, r) rows."""

    study_id: str
    source: str = Field(description="socsci210 | tess | dataverse | innovation_panel | bes")
    title: str | None = None
    data_file: str = Field(description="Filename of the data file inside data/raw/<study_id>/.")
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
        # Every outcome must get its variable from somewhere: either the outcome
        # itself, or (split-ballot) every arm.
        arms_have_var = all(a.outcome_var for a in self.condition.arms)
        for outcome in self.outcomes:
            if not outcome.var and not arms_have_var:
                raise ValueError(
                    f"outcome task_num={outcome.task_num} has no `var`, and not every arm "
                    "declares `outcome_var`"
                )
        return self

    def recode_for(self, arm: Arm, outcome: Outcome | None = None) -> dict[int, int]:
        """The answer map to use, most specific first.

        Arm beats outcome beats study. An arm-level map exists because that arm
        *presented* the options differently (option-order experiments); an
        outcome-level map exists because that item is on a different scale
        (dollars vs minutes). Arm wins because it describes what was shown.
        """
        if arm.response_recode is not None:
            return arm.response_recode
        if outcome is not None and outcome.response_recode is not None:
            return outcome.response_recode
        return self.response_recode

    def outcome_var_for(self, outcome: Outcome, arm: Arm) -> str | None:
        """The variable holding this arm's answer to this outcome."""
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
        """
        if outcome.var is None and arm.scale is not None:
            return arm.scale
        return outcome.scale

    def outcome_text_for(self, outcome: Outcome, arm: Arm) -> str:
        """The rendered outcome: question + answer instruction.

        Arm-level overrides apply only where the arm supplies the item — see
        `scale_for`.
        """
        question = (arm.outcome_question if outcome.var is None else None) or outcome.question
        return f"{question} {self.scale_for(outcome, arm).instruction()}"


def load(path: str | Path) -> Recipe:
    """Load and validate a recipe YAML."""
    data: dict[str, Any] = yaml.safe_load(Path(path).read_text())
    return Recipe.model_validate(data)
