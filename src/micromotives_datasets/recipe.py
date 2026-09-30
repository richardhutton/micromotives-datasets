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

    raw: int = Field(description="Value of the source condition variable.")
    condition_num: int = Field(description="Canonical 0-based index. DECLARED, never inferred.")
    factors: dict[str, str] = Field(
        default_factory=dict,
        description="Factor levels for this arm, e.g. {label: Atheist, biography: present}. "
        "Used by QC to check every factor is actually expressed in the text.",
    )
    text: str = Field(description="What this arm saw. Verbatim for what varies.")


class Condition(BaseModel):
    """The experimental manipulation."""

    source_var: str = Field(description="Variable in the data holding the arm code.")
    shared_context: str | None = Field(
        default=None,
        description="Context identical across arms, stated ONCE rather than repeated "
        "per arm. Leave empty when arms differ wholesale.",
    )
    factors: list[str] = Field(
        default_factory=list, description="Names of the design factors, e.g. [label, biography]."
    )
    arms: list[Arm]

    def render(self, arm: Arm) -> str:
        """shared_context + arm text -> the condition string."""
        if self.shared_context:
            return f"{self.shared_context.strip()} {arm.text.strip()}"
        return arm.text.strip()

    def by_raw(self) -> dict[int, Arm]:
        return {a.raw: a for a in self.arms}


class Outcome(BaseModel):
    """One outcome question the respondent answered."""

    var: str = Field(description="Variable in the data holding the answer.")
    task_num: int = Field(description="Canonical 0-based item index.")
    question: str = Field(description="The question wording.")
    scale: Scale


class Recipe(BaseModel):
    """Everything needed to melt one study into (P, c, o, r) rows."""

    study_id: str
    source: str = Field(description="socsci210 | tess | dataverse | innovation_panel | bes")
    title: str | None = None
    data_file: str = Field(description="Filename of the data file inside data/raw/<study_id>/.")
    notes: str | None = None

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

    @model_validator(mode="after")
    def _check(self) -> Recipe:
        nums = [a.condition_num for a in self.condition.arms]
        if len(set(nums)) != len(nums):
            raise ValueError(f"duplicate condition_num in {self.study_id}: {nums}")
        raws = [a.raw for a in self.condition.arms]
        if len(set(raws)) != len(raws):
            raise ValueError(f"duplicate raw arm code in {self.study_id}: {raws}")
        tasks = [o.task_num for o in self.outcomes]
        if len(set(tasks)) != len(tasks):
            raise ValueError(f"duplicate task_num in {self.study_id}: {tasks}")
        # Every declared factor must be present on every arm.
        for arm in self.condition.arms:
            missing = set(self.condition.factors) - set(arm.factors)
            if missing:
                raise ValueError(f"arm raw={arm.raw} missing factor(s) {sorted(missing)}")
        return self


def load(path: str | Path) -> Recipe:
    """Load and validate a recipe YAML."""
    data: dict[str, Any] = yaml.safe_load(Path(path).read_text())
    return Recipe.model_validate(data)
