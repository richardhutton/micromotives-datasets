"""The (P, c, o, r) row schema.

One row = one respondent answering one outcome under one randomised condition,
following SocSci210 (arXiv:2509.05830) Figure 1. The four parts are DISTINCT:

    persona    (P) — who the respondent is (demographics → text)
    condition  (c) — the randomised stimulus arm they saw (rendered text)
    outcome    (o) — the question they were asked
    response   (r) — what they answered

`condition` carries the rendered stimulus text; `condition_num` is the arm
index. SocSci210 keeps both — an index for grouping, the text for the prompt.
Do not collapse `outcome` into `condition`.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Persona(BaseModel):
    """Respondent demographics. Superset of the SocSci210 16-field struct;
    every field is optional because sources vary in what they collect. Render
    to text with `micromotives_datasets.persona.render`.
    """

    age: int | None = None
    sex: str | None = None
    gender: str | None = None
    education: str | None = None
    income: str | None = None
    ethnicity: str | None = None
    marital_status: str | None = None
    employment: str | None = None
    region: str | None = None
    social_grade: str | None = None
    party_id: str | None = None
    ideology: str | None = None
    religion: str | None = None
    household_size: int | None = None
    urban_rural: str | None = None
    housing_type: str | None = None
    housing_ownership: str | None = None
    internet_access: str | None = None
    phone_service: str | None = None
    # Free-form extras a source provides that don't map to a named field above.
    extra: dict[str, str] = Field(default_factory=dict)


class Row(BaseModel):
    """A single (P, c, o, r) training row plus provenance."""

    # --- the tuple ---------------------------------------------------------
    persona: Persona
    condition: str = Field(description="Rendered stimulus text of the arm shown.")
    outcome: str = Field(description="The outcome question wording.")
    response: str = Field(description="The respondent's answer (as text).")

    # --- structure / grouping ---------------------------------------------
    condition_num: int | None = Field(
        default=None, description="Randomised arm index within the experiment."
    )
    task_num: int | None = Field(
        default=None,
        description="Task/item index when a respondent answers several items "
        "(e.g. successive conjoint tasks) in one experiment.",
    )
    response_num: float | None = Field(
        default=None, description="Numeric response, when the answer is a scale/choice code."
    )

    # --- optional generative target ---------------------------------------
    quote: str | None = Field(
        default=None,
        description="Open-ended response text, when the source has one. Synthetic "
        "quotes MUST be flagged via `synthetic_quote`.",
    )
    synthetic_quote: bool = False

    # --- provenance --------------------------------------------------------
    source: str = Field(
        description="Source adapter: socsci210 | tess | dataverse | innovation_panel | bes"
    )
    study_id: str = Field(description="Stable study identifier (OSF 5-char code, TESS id, SN, …).")
    experiment: str | None = Field(
        default=None,
        description="Sub-experiment within the study, when one deposit yields several "
        "recipes. Part of the row's identity: one deposit's sub-experiments are "
        "answered by the SAME people, so without it a respondent's rows from two "
        "sub-experiments are indistinguishable.",
    )
    participant_id: str | None = Field(
        default=None,
        description="Respondent identifier, namespaced by study. It must be unique "
        "ACROSS studies, not only within one: these rows get merged into a single "
        "corpus, and a bare row index made 23,464 respondents collapse into 4,010 "
        "ids, with 'person 0' existing in all 14 studies as 14 different people.",
    )

    def anchor(self) -> tuple[str, str, str | None, str | None]:
        """(source, study_id, experiment, participant_id) — the row's origin key.

        `experiment` is in here because a deposit's sub-experiments share their
        respondents: `a5v96`'s two vignettes were both shown to all 1,211 people,
        so the key must separate them.
        """
        return (self.source, self.study_id, self.experiment, self.participant_id)
