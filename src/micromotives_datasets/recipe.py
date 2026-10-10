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

import re
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
    mid_label: str | None = Field(
        default=None,
        description="Label the source gives the MIDPOINT, where it labels one. "
        "`a42yg`'s Q7 runs 1 'Curative care' to 7 'Palliative Care' and also "
        "labels 4 'Both are important'. With nowhere to put it, the maker wrote "
        "it into the question text as '(4 means both are equally important.)' — "
        "inventing the word 'equally', which asserts parity where the source "
        "says only that both matter, and then recording in `notes` that the "
        "clause was sourced rather than written. Neither the slip nor the false "
        "provenance was deliberate; the field was simply missing, so the "
        "information had to go somewhere, and free text is where things drift. "
        "Scale legends belong in the scale.",
    )
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
            base += f' where {self.min} means "{self.min_label}"'
            if self.mid_label:
                base += f', {self.midpoint} means "{self.mid_label}",'
            base += f' and {self.max} means "{self.max_label}"'
        return base + ", nothing else."

    @property
    def midpoint(self) -> int:
        """The integer code halfway along. Only meaningful on an odd-length scale."""
        return (self.min + self.max) // 2

    @model_validator(mode="after")
    def _check_nominal(self) -> Scale:
        if self.nominal and (self.min_label or self.max_label or self.mid_label):
            raise ValueError(
                "a nominal scale must not carry min_label/max_label/mid_label — they "
                "would assert an ordering it does not have; enumerate the options in "
                "the outcome `question` instead"
            )
        if self.mid_label:
            if not (self.min_label and self.max_label):
                raise ValueError(
                    "mid_label needs min_label and max_label: the instruction names the "
                    "midpoint only inside an endpoint-labelled scale, so a mid_label "
                    "alone would be silently dropped"
                )
            if (self.max - self.min) % 2:
                raise ValueError(
                    f"scale {self.min}-{self.max} has an even number of points, so it has "
                    "no middle code for mid_label to name — the source labelling one means "
                    "the scale has been read wrongly"
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
    condition_text: str | None = Field(
        default=None,
        description="CONDITION text for this (arm, item) cell, replacing `Arm.text`. "
        "An arm's text is one string shared by every outcome of that arm, but an "
        "outcome can sit at a point in the questionnaire where only PART of the arm's "
        "stimulus has happened. `sh4px` asks four mood items BETWEEN its two writing "
        "tasks, so the arm's text narrates a self-affirmation exercise the respondent "
        "has not yet done; its maker excluded all four items rather than assert a "
        "treatment history, costing 4 of 10 fielded items. `a2nbf`'s arm text says the "
        "questions referred to a defect found 'before a baby is born', which is true at "
        "Q3/Q4 and false at Q1/Q2, asked before any wording variant appears — 3,094 of "
        "its 6,211 rows. Set this to what WAS true at that item. The empty string is a "
        "legitimate value and means the shared context alone.",
    )
    line_order_vars: list[str] | None = Field(
        default=None,
        description="One variable per BULLET line ('• ...') of this cell's `condition_text`, "
        "giving the 1-based position that statement was shown in to this respondent. For "
        "an item-count list whose statements were shuffled per respondent and whose order "
        "variables differ per list: IP `9.17` records one per list, and a 5-statement list "
        "has 120 possible orders. Lines without a bullet (the list's stem) stay where they "
        "are, and bullets stay bullets — unlike `Condition.line_order_vars`, which "
        "renumbers. A row whose order is not recorded is skipped, not rendered in a "
        "guessed order.",
    )
    scale: Scale | None = Field(default=None, description="Response scale for this cell.")
    response_recode: dict[int, int] | None = Field(
        default=None, description="raw->canonical answer map for this cell."
    )


_LINE_NUMBER = re.compile(r"^\s*\d+\.\s*")


class Arm(BaseModel):
    """One randomised arm: its raw code, its canonical index, and what it showed."""

    raw: int | None = Field(
        default=None, description="Value of the single source condition variable."
    )
    raws: list[int] | None = Field(
        default=None,
        description="Several values of the single source condition variable that all "
        "denote THE SAME condition. `a2nbf` randomised a 2x2 of question wording x a "
        "follow-up item, but the follow-up was administered after every scored "
        "outcome, so for the rows we build it had not happened: raw codes 1 and 2 are "
        "one condition, 3 and 4 another. Use this rather than two arms sharing a "
        "condition_num, which would leave it ambiguous which arm's text and factors "
        "applied.",
    )
    raw_values: dict[str, int] | None = Field(
        default=None,
        description="Value of EACH source variable, when the assignment is split across "
        "several (a 2x2 held as two separate randomisation variables). Use with "
        "Condition.source_vars.",
    )
    witness_var: str | None = Field(
        default=None,
        description="Variable whose `Condition.not_asked_code` proves this respondent was "
        "NOT shown this condition. For an instrument that routes respondents to separate "
        "blocks of variables and records no assignment column at all: `QQM5MC` carries its "
        "four conditions as Q1A/Q2A/Q3A .. Q2D/Q3D, and the only record of who saw what is "
        "that the other blocks read 'Not Asked'. That code is the instrument's own account "
        "of what it asked, not an inference from the answer — item non-response has its own "
        "separate code. Use with `Condition.not_asked_code` and never together with "
        "`raw`/`raws`/`raw_values`.",
    )
    condition_num: int = Field(description="Canonical 0-based index. DECLARED, never inferred.")
    factors: dict[str, str] = Field(
        default_factory=dict,
        description="Factor levels for this arm, e.g. {label: Atheist, biography: present}. "
        "Used by QC to check every factor is actually expressed in the text.",
    )
    text: str = Field(description="What this arm saw. Verbatim for what varies.")

    @property
    def label(self) -> str:
        """How to name this arm in an error, whichever way it declares its codes."""
        if self.raws is not None:
            return f"raws={self.raws}"
        if self.raw_values is not None:
            return f"raw_values={self.raw_values}"
        if self.witness_var is not None:
            return f"witness_var={self.witness_var}"
        return f"raw={self.raw}"

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


class Level(BaseModel):
    """One level of one dimension of a templated factorial condition."""

    level: str = Field(description="Factor level name, for `Arm.factors`.")
    text: str = Field(description="The clause the respondent read. Verbatim.")
    parts: dict[str, str] = Field(
        default_factory=dict,
        description="Named fragments that must AGREE with this level elsewhere in the "
        "text, addressed as `{dimension.part}`. IP `9.18` randomises a name, and the "
        "pronoun and possessive later in the sentence follow it: 'George ... He ... his' "
        "against 'Margaret ... She ... her'. Every level of a dimension declares the "
        "same parts, so no cell can render a fragment another cell lacks.",
    )


class Dimension(BaseModel):
    """One randomised dimension of a templated factorial condition."""

    var: str = Field(description="Variable holding this dimension's allocated code.")
    levels: dict[int, Level] = Field(description="Allocated code -> what it said.")

    @model_validator(mode="after")
    def _non_empty(self) -> Dimension:
        if not self.levels:
            raise ValueError(f"dimension on {self.var!r} declares no levels")
        return self


class ConditionTemplate(BaseModel):
    """A factorial condition declared as a template plus its dimensions.

    For a design whose arms are the full product of several randomised
    dimensions. Enumerating that product in YAML does not work: IP `9.10`
    crosses 4 x 3 x 4 x 5 x 2 = 480 arms, and `9xw67` already showed where
    machine-written arms lead — 455,919 lines, 95% of all recipe text in this
    repo, which nobody reviewed and nobody could regenerate. The judgment in a
    factorial design is the dimension list and the clause wording, which is
    about forty lines; the product is arithmetic, and arithmetic belongs in
    code.

    `condition_num` is an odometer over `dimensions` in declared order, each
    dimension's levels in ascending code order, the LAST dimension moving
    fastest. Declared here rather than per arm, which is the one place rule 2
    ("the condition mapping is declared, never inferred") is satisfied by a rule
    instead of a table: the rule is reviewable in a way 480 numbers are not, and
    it means the same thing in every wave that reuses the template.
    """

    text: str = Field(
        description="The stimulus with one `{dimension}` placeholder per dimension, which "
        "is where that dimension's clause goes. `{dimension.part}` places one of that "
        "level's `parts`, and may repeat. Everything outside the placeholders is fixed "
        "wording and is verbatim."
    )
    dimensions: dict[str, Dimension] = Field(
        description="Dimension name -> its variable and levels, in the order "
        "`condition_num` counts them."
    )
    outcome_questions: dict[int, str] = Field(
        default_factory=dict,
        description="`task_num` -> the question for that item, when its wording varies "
        "with the cell. IP `9.18` asks 'How successfully is George ageing?', naming the "
        "person the condition described; IP `9.39` asks four questions per candidate, "
        "each with its own pronouns. Rendered from the same cell as `text`, with the "
        "same placeholders, and attached to each arm as an `ItemOverride` for exactly "
        "the tasks named, so a vignette's question never leaks onto another outcome.",
    )

    @model_validator(mode="after")
    def _placeholders_match(self) -> ConditionTemplate:
        bare = re.findall(r"\{(\w+)\}", self.text)
        found = set(bare)
        declared = set(self.dimensions)
        if found != declared:
            raise ValueError(
                f"template placeholders {sorted(found)} do not match declared dimensions "
                f"{sorted(declared)} — a dimension with no placeholder would be randomised "
                "but never shown, and a placeholder with no dimension would ship as "
                "literal braces into the corpus"
            )
        for name in declared:
            if bare.count(name) != 1:
                raise ValueError(f"dimension {name!r} appears more than once in the template")
        if len({d.var for d in self.dimensions.values()}) != len(self.dimensions):
            raise ValueError("two dimensions share one variable — their levels would collide")
        # A clause or fragment carrying a brace would be filled in, or left
        # standing, by the rendering of some OTHER placeholder.
        for name, dim in self.dimensions.items():
            for code, lv in dim.levels.items():
                for fragment in (lv.text, *lv.parts.values()):
                    if "{" in fragment or "}" in fragment:
                        raise ValueError(f"dimension {name!r} level {code}: braces in {fragment!r}")

        # Parts: every level of a dimension offers the same ones, and every one
        # offered is placed somewhere. A part only some levels carry would ship
        # as literal braces in the cells that lack it; a part nobody places is
        # agreement the template claims and never renders.
        question = " ".join(self.outcome_questions.values())
        used = set(re.findall(r"\{(\w+)\.(\w+)\}", self.text + question))
        for name, dim in self.dimensions.items():
            offered = {frozenset(lv.parts) for lv in dim.levels.values()}
            if len(offered) != 1:
                raise ValueError(
                    f"dimension {name!r}: levels declare different parts "
                    f"{sorted(sorted(o) for o in offered)} — every level must offer the same"
                )
            for part in next(iter(offered)):
                if (name, part) not in used:
                    raise ValueError(f"part {name}.{part} is declared but never placed")
        for name, part in used:
            if name not in declared:
                raise ValueError(f"placeholder {{{name}.{part}}} names no declared dimension")
            if part not in next(iter(self.dimensions[name].levels.values())).parts:
                raise ValueError(f"placeholder {{{name}.{part}}} names a part no level declares")

        stray = set(re.findall(r"\{(\w+)\}", question)) - declared
        if stray:
            raise ValueError(
                f"outcome_questions placeholders {sorted(stray)} name no declared dimension"
            )
        return self

    def render(self, template: str, levels: dict[str, Level]) -> str:
        """Fill `template` from one cell: parts first, then the bare clauses."""
        for name, level in levels.items():
            for part, fragment in level.parts.items():
                template = template.replace(f"{{{name}.{part}}}", fragment)
        for name, level in levels.items():
            template = template.replace(f"{{{name}}}", level.text)
        return template

    @property
    def names(self) -> list[str]:
        """Dimension names, in the order `condition_num` counts them."""
        return list(self.dimensions)

    @property
    def variables(self) -> list[str]:
        """The allocation variables, in dimension order."""
        return [d.var for d in self.dimensions.values()]

    def cells(self) -> list[dict[str, int]]:
        """Every cell of the product, as {dimension: code}, in odometer order."""
        out: list[dict[str, int]] = [{}]
        for name in self.names:
            codes = sorted(self.dimensions[name].levels)
            out = [cell | {name: code} for cell in out for code in codes]
        return out

    def expand(self) -> list[Arm]:
        """The product, as arms. One arm per cell, `condition_num` its index."""
        arms: list[Arm] = []
        for num, cell in enumerate(self.cells()):
            levels = {name: self.dimensions[name].levels[cell[name]] for name in self.names}
            text = self.render(self.text, levels)
            questions = {t: self.render(q, levels) for t, q in self.outcome_questions.items()}
            items = {t: ItemOverride(outcome_question=q) for t, q in questions.items()}
            # The backstop for every placeholder shape the checks above do not
            # parse (`{a.b.c}`, `{a-b}`, `{a }`): nothing with a brace ships.
            rendered = text + "".join(questions.values())
            if "{" in rendered or "}" in rendered:
                raise ValueError(f"cell {cell} rendered with a placeholder left in it")
            arms.append(
                Arm(
                    raw_values={self.dimensions[n].var: cell[n] for n in self.names},
                    condition_num=num,
                    factors={n: levels[n].level for n in self.names},
                    text=text,
                    items=items,
                )
            )
        return arms


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
    arms: list[Arm] = Field(
        default_factory=list,
        description="The arms, written out. Omit when `template` declares a factorial "
        "to expand instead; exactly one of the two is required.",
    )
    template: ConditionTemplate | None = Field(
        default=None,
        description="A factorial declared as a template plus its dimensions, expanded into "
        "`arms` on load. Use instead of `arms`, never alongside.",
    )

    not_asked_code: int | None = Field(
        default=None,
        description="The code meaning 'this respondent was never shown this variable', for "
        "a study whose assignment is recorded only by WHICH block of variables was put to "
        "each person. Switches arm resolution to `Arm.witness_var`. Declared rather than "
        "guessed because the same file also codes item non-response, and the two must not "
        "be confused: in `QQM5MC` 9999 is 'Not Asked' and 9998 is 'Skipped'.",
    )
    ambiguous_routing: int = Field(
        default=0,
        description="How many respondents the instrument routed to MORE THAN ONE condition. "
        "Such a respondent has no condition, so no (persona, condition, outcome, response) "
        "row can honestly be written for them and the melt drops them. The count is "
        "declared so the drop is never silent and never open-ended: the melt FAILS when the "
        "number it finds differs from this, so a second occurrence appearing in a re-fetched "
        "deposit stops the build instead of quietly growing the discard.",
    )
    routing_check: bool = Field(
        default=False,
        description="For a coded assignment: also read every arm's OWN outcome variables, "
        "and count a respondent with ANY code in another arm's variable as routed to two "
        "conditions (a back-button re-assigns, and the abandoned answer stays in the file; "
        "DEL's Feb 2023 sandbox has one). Off by default because deposits mark 'not asked' "
        "differently: blank in DEL, negative codes in the Innovation Panel, where switching "
        "it on would read thousands of not-asked codes as answers. Turn it on only where "
        "'not asked' is blank, and declare what it finds in `ambiguous_routing`.",
    )
    ambiguous_routing_reason: str | None = Field(
        default=None,
        description="Why those respondents are routed twice, and why dropping them is right. "
        "Required whenever `ambiguous_routing` is non-zero.",
    )

    line_order_vars: list[str] | None = Field(
        default=None,
        description="One variable per LINE of every arm's text, giving the position "
        "(1-based) that line was shown in to this respondent. For a conjoint whose "
        "attribute rows are randomised per respondent: `8ctbk` records six "
        "`Attribute<n>_Order_*` columns and 654 of the 720 possible orders occur, so a "
        "single fixed rendering is right for about 1 row in 720. Declaring these makes "
        "the melt render each respondent's own order and renumber accordingly. The "
        "numbering is the instrument's, not ours -- the deposit's screenshots show 1-6 "
        "down the left of the fielded table.",
    )

    @model_validator(mode="after")
    def _expand_template(self) -> Condition:
        """Turn a declared template into arms, and check nothing contradicts it."""
        if self.template is None:
            if not self.arms:
                raise ValueError("condition declares neither `arms` nor `template`")
            return self
        if self.arms:
            raise ValueError(
                "condition declares both `arms` and `template` — the expansion would "
                "silently replace the written arms, so say which one is meant"
            )
        declared = self.template.variables
        if self.source_var is not None:
            raise ValueError("a templated condition is factorial; use `source_vars`, not one var")
        if self.source_vars and self.source_vars != declared:
            raise ValueError(
                f"source_vars {self.source_vars} do not match the template's variables "
                f"{declared} in the same order — `by_raw` keys arms on that order, so a "
                "mismatch would look up the wrong cell rather than fail"
            )
        if self.factors and self.factors != self.template.names:
            raise ValueError(
                f"factors {self.factors} do not match the template's dimensions "
                f"{self.template.names} in the same order"
            )
        self.source_vars = declared
        self.factors = self.template.names
        self.arms = self.template.expand()
        return self

    @staticmethod
    def reorder_lines(text: str, positions: list[int]) -> str:
        """Put each line where this respondent saw it, and renumber.

        `positions[i]` is the 1-based slot that line i occupied on screen. Any
        existing "N. " prefix is stripped before renumbering, because the number
        a line carries in the recipe is its position in the DECLARED order, not
        in the one this respondent met.
        """
        lines = [ln.strip() for ln in text.strip().split("\n") if ln.strip()]
        if len(lines) != len(positions):
            raise ValueError(
                f"line_order_vars gives {len(positions)} positions for {len(lines)} lines"
            )
        if sorted(positions) != list(range(1, len(lines) + 1)):
            raise ValueError(f"line order is not a permutation of 1..{len(lines)}: {positions}")
        bare = [_LINE_NUMBER.sub("", ln) for ln in lines]
        ordered = [""] * len(lines)
        for line, slot in zip(bare, positions, strict=True):
            ordered[slot - 1] = line
        return "\n".join(f"{i}. {line}" for i, line in enumerate(ordered, 1))

    @staticmethod
    def reorder_bullets(text: str, positions: list[int]) -> str:
        """Put each bullet line where this respondent saw it; leave the rest alone.

        `positions[i]` is the 1-based slot the i-th bullet occupied among the
        bullets. Non-bullet lines keep their own places, so a stem above the list
        stays above it.
        """
        # Lines are kept exactly as written; only the bullet lines move.
        lines = text.strip().split("\n")
        slots = [k for k, ln in enumerate(lines) if ln.lstrip().startswith("•")]
        if len(slots) != len(positions):
            raise ValueError(f"{len(positions)} positions for {len(slots)} bullet lines")
        if sorted(positions) != list(range(1, len(slots) + 1)):
            raise ValueError(f"bullet order is not a permutation of 1..{len(slots)}: {positions}")
        bullets = [lines[k] for k in slots]
        ordered = [""] * len(slots)
        for bullet, slot in zip(bullets, positions, strict=True):
            ordered[slot - 1] = bullet
        for k, bullet in zip(slots, ordered, strict=True):
            lines[k] = bullet
        return "\n".join(lines)

    def render(self, arm: Arm) -> str:
        """shared_context + arm text -> the condition string."""
        if self.shared_context:
            return f"{self.shared_context.strip()} {arm.text.strip()}"
        return arm.text.strip()

    @property
    def variables(self) -> list[str]:
        """Every variable needed to determine an arm.

        Empty under the witness design, which has no assignment column at all;
        `witness_vars` carries those names instead. Keeping them apart matters:
        these are read as CODES and looked up in `by_raw`, and a witness value is
        a response, not a code.
        """
        return self.source_vars or ([self.source_var] if self.source_var else [])

    @property
    def witness_vars(self) -> list[str]:
        """The per-arm witness variables, in arm order. Empty unless witnessed."""
        return [a.witness_var for a in self.arms if a.witness_var is not None]

    @property
    def witnessed(self) -> bool:
        """True when arms are resolved by not-asked codes rather than an arm code."""
        return self.not_asked_code is not None

    def arms_asked(self, codes: dict[str, int | None]) -> list[Arm]:
        """Every arm this respondent was ASKED, by its witness.

        `codes` maps each witness variable to the respondent's value, or None
        where the cell is blank. A blank witness is treated exactly like the
        not-asked code: both mean the melt has no evidence this person saw the
        condition, and inventing one from an absent cell is the error this whole
        mechanism exists to avoid. Returns every match, not the first — the
        caller decides what more than one means, because a respondent with two
        conditions has none.
        """
        asked = []
        for arm in self.arms:
            assert arm.witness_var is not None
            value = codes.get(arm.witness_var)
            if value is not None and value != self.not_asked_code:
                asked.append(arm)
        return asked

    def key_for(self, values: dict[str, int]) -> tuple[int, ...]:
        """The lookup key for a respondent's assignment codes."""
        return tuple(values[v] for v in self.variables)

    def by_raw(self) -> dict[tuple[int, ...], Arm]:
        """Arms indexed by their assignment key (a 1-tuple in the usual case).

        Empty under the witness design, which has no codes to index by. The melt
        resolves those arms through `arms_asked` instead.
        """
        if self.witnessed:
            return {}
        out: dict[tuple[int, ...], Arm] = {}
        for arm in self.arms:
            if self.source_vars:
                assert arm.raw_values is not None
                out[tuple(arm.raw_values[v] for v in self.source_vars)] = arm
            elif arm.raws is not None:
                for code in arm.raws:
                    out[(code,)] = arm
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
    participant_id_var: str | None = Field(
        default=None,
        description="Column holding each respondent's identifier, used in place of the "
        "row index. For a PANEL, where the same person answers in several waves and each "
        "wave is its own file: the row index makes them two unrelated participants, and "
        "the wave-on-wave link is the whole reason a panel is worth building. Must NOT be "
        "the archive's own person identifier where that identifier links to further "
        "licensed data — IP 6849 stores a hash of `pidp`, never `pidp`.",
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
    respondent_vars: list[str] = Field(
        default_factory=list,
        description="Source variables whose value may resolve an inline directive in "
        "condition or outcome text, for stimulus wording that varies by RESPONDENT "
        "rather than by arm.\n\n"
        "`a2nbf` asks: 'If [IF PPGENDER=2 INSERT: you; IF PPGENDER=1 INSERT: your "
        "partner] were pregnant, would you want a test...'. That is not a "
        "manipulation — it is the same question phrased for who is being asked — so "
        "it cannot be an arm, and the maker rendered the unresolved template "
        "`{you/your partner}` on 3,117 rows: text no respondent read. The resolution "
        "was never unknowable; PPGENDER sits in this recipe's own `persona_map`.\n\n"
        "Declared rather than inferred, so nothing resolves silently: only variables "
        "named here are offered to the resolver, and the directives themselves are "
        "parsed by `sources.quex`, which REFUSES anything outside its measured "
        "grammar rather than guessing.",
    )
    persona_label_rewrite: dict[str, dict[int, str]] = Field(
        default_factory=dict,
        description="Source variable -> {code: replacement label}. Use this when the "
        "code IS a real answer but the panel's label carries scripting boilerplate — "
        "`REL1` code 11 is labelled 'Other Christian religion, please specify', which "
        "is a genuine response wearing an instruction. Dropping it would lose the "
        "answer; rewriting keeps it.",
    )

    def _check_assignment(self) -> None:
        """A recipe declares its assignment exactly one way, and declares it fully.

        The two ways are mutually exclusive by construction, not by convention: a
        witnessed arm has no code to look up and a coded arm has no witness to
        read, so a recipe holding both would have two answers to the only
        question that matters about a row.
        """
        cond = self.condition
        witnesses = [a.witness_var for a in cond.arms if a.witness_var is not None]
        if cond.witnessed:
            if cond.variables:
                raise ValueError(
                    f"{self.study_id}: condition declares both `not_asked_code` and "
                    f"source_var/source_vars — an arm cannot be resolved two ways"
                )
            if len(witnesses) != len(cond.arms):
                raise ValueError(
                    f"{self.study_id}: `not_asked_code` is set, so every arm needs a "
                    f"`witness_var` ({len(witnesses)} of {len(cond.arms)} have one)"
                )
            if len(set(witnesses)) != len(witnesses):
                # Two arms sharing a witness can never be told apart: the same
                # value would answer for both, so every respondent asked one
                # would read as having been asked the other too.
                raise ValueError(
                    f"{self.study_id}: arms share a witness_var and so cannot be "
                    f"distinguished: {witnesses}"
                )
            if any(a.raw is not None or a.raws or a.raw_values for a in cond.arms):
                raise ValueError(
                    f"{self.study_id}: a witnessed arm also declares raw/raws/raw_values"
                )
        else:
            if witnesses:
                raise ValueError(
                    f"{self.study_id}: arms declare `witness_var` but the condition has no "
                    f"`not_asked_code`, so the witnesses would never be read"
                )
            if not cond.variables:
                raise ValueError(
                    f"{self.study_id}: condition needs source_var, source_vars, or "
                    f"`not_asked_code` with a `witness_var` per arm"
                )
        if cond.ambiguous_routing and not cond.ambiguous_routing_reason:
            raise ValueError(
                f"{self.study_id}: ambiguous_routing={cond.ambiguous_routing} without a "
                f"reason — a discarded respondent must say why they were discarded"
            )
        if cond.ambiguous_routing and not cond.witnessed and not cond.routing_check:
            raise ValueError(
                f"{self.study_id}: ambiguous_routing on a coded assignment is only ever "
                f"counted with `routing_check: true`; without it the declaration is inert"
            )
        if cond.routing_check and not cond.witnessed:
            # A coded assignment names one arm, but a respondent can still have
            # met a second (a back-button re-assigns; DEL Feb 2023 has one). The
            # melt sees that only through a variable just ONE arm was asked, so
            # without such variables the check could never fire.
            owners: dict[str, int] = {}
            for arm in cond.arms:
                for v in {arm.outcome_var} | {it.outcome_var for it in arm.items.values()}:
                    if v:
                        owners[v.upper()] = owners.get(v.upper(), 0) + 1
            if not any(n == 1 for n in owners.values()):
                raise ValueError(
                    f"{self.study_id}: routing_check reads each arm's OWN outcome variable, "
                    f"and no arm has one here"
                )

    @model_validator(mode="after")
    def _check(self) -> Recipe:
        nums = [a.condition_num for a in self.condition.arms]
        if len(set(nums)) != len(nums):
            raise ValueError(f"duplicate condition_num in {self.study_id}: {nums}")
        self._check_assignment()
        # Arm codes, and their uniqueness. Skipped entirely under the witness
        # design, which declares no codes at all — `_check_assignment` has
        # already proved its witnesses are complete and distinct.
        if not self.condition.witnessed:
            if self.condition.source_vars:
                for arm in self.condition.arms:
                    missing = set(self.condition.source_vars) - set(arm.raw_values or {})
                    if missing:
                        raise ValueError(
                            f"{self.study_id}: an arm is missing raw_values for {sorted(missing)}"
                        )
            else:
                if any(a.raw is None and not a.raws for a in self.condition.arms):
                    raise ValueError(f"{self.study_id}: every arm needs `raw` or `raws`")
                if any(a.raw is not None and a.raws for a in self.condition.arms):
                    raise ValueError(f"{self.study_id}: an arm declares both `raw` and `raws`")
            # Build the key list from the arms directly — by_raw() is a dict, so
            # duplicates would silently collapse and never be caught.
            keys: list[tuple[int, ...]] = []
            for arm in self.condition.arms:
                if self.condition.source_vars:
                    keys.append(
                        tuple(arm.raw_values[v] for v in self.condition.source_vars)  # type: ignore[index]
                    )
                elif arm.raws is not None:
                    # Every code separately, so two arms both claiming code 2 is still
                    # caught — the whole point of this check.
                    keys.extend((c,) for c in arm.raws)
                else:
                    keys.append((arm.raw,))  # type: ignore[arg-type]
            if len(set(keys)) != len(keys):
                raise ValueError(f"duplicate raw arm code in {self.study_id}: {keys}")
        tasks = [o.task_num for o in self.outcomes]
        if len(set(tasks)) != len(tasks):
            raise ValueError(f"duplicate task_num in {self.study_id}: {tasks}")
        # Every declared factor must be present on every arm.
        for arm in self.condition.arms:
            missing = set(self.condition.factors) - set(arm.factors)
            if missing:
                raise ValueError(f"arm {arm.label} missing factor(s) {sorted(missing)}")
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
        # A template's questions are derived from the cell, so an outcome left
        # out of them ships its fallback wording silently — in 9.39 that was
        # "[her/him]" on 1,477 rows with QC reporting nothing. All or none.
        template = self.condition.template
        if template is not None and template.outcome_questions:
            uncovered = sorted(declared_tasks - set(template.outcome_questions))
            if uncovered:
                raise ValueError(
                    f"{self.study_id}: template.outcome_questions covers no question for "
                    f"task_num {uncovered}; those rows would carry the fallback wording"
                )
        for arm in self.condition.arms:
            for task, ov in arm.items.items():
                if ov.line_order_vars is None:
                    continue
                text = ov.condition_text or ""
                bullets = sum(1 for ln in text.split("\n") if ln.strip().startswith("•"))
                if bullets != len(ov.line_order_vars):
                    raise ValueError(
                        f"{self.study_id}: arm {arm.label} task {task} declares "
                        f"{len(ov.line_order_vars)} line_order_vars for {bullets} bullet lines"
                    )
            stray = sorted(set(arm.items) - declared_tasks)
            if stray:
                raise ValueError(
                    f"{self.study_id}: arm {arm.label} has item override(s) for "
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

    def condition_text_for(
        self,
        outcome: Outcome,
        arm: Arm,
        line_order: list[int] | None = None,
        bullet_order: list[int] | None = None,
    ) -> str:
        """The condition string for this (arm, item) cell.

        An item-level override wins, as everywhere else here, because it names
        the one cell it describes. `shared_context` is still prepended: it holds
        what was true for everyone throughout, and an item override replaces the
        ARM's contribution, not the study's.
        """
        item = self.item_for(outcome, arm)
        text = arm.text if item is None or item.condition_text is None else item.condition_text
        body = text.strip()
        # Only the arm's own lines are reordered. `shared_context` is not a list
        # of attributes and has no position to carry.
        if line_order and body:
            body = self.condition.reorder_lines(body, line_order)
        if bullet_order is not None:
            body = self.condition.reorder_bullets(body, bullet_order)
        ctx = (self.condition.shared_context or "").strip()
        if ctx and body:
            return f"{ctx} {body}"
        return ctx or body

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
