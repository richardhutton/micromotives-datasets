"""The witness design, and the first UK study built with it.

`QQM5MC` is the first study here with NO assignment column. Its four conditions are
four blocks of variables, and the only record of who saw what is that the blocks a
person was not routed to are coded 9999 "Not Asked". Every other recipe names a
`condition.source_var`; this one names a `witness_var` per arm instead.

Two properties carry the whole mechanism, and both are tested here rather than
assumed:

  * A respondent asked TWO blocks has no condition. The tuple this corpus is made of
    has exactly one, and we cannot know which of the two they met. A mechanism that
    took the first match would look identical on 3,266 of 3,267 respondents and be
    silently wrong on the remaining one — `ID 2158`, who was routed to both Prime
    only and Info only. The authors' own reshape keeps that person in both groups,
    so the published N of 2,762 counts them twice.

  * The number of such respondents is DECLARED. The melt fails when what it finds
    differs from the recipe, in either direction, so a re-fetched deposit cannot
    quietly grow the discard.

The deposit is gitignored, so the tests that need it skip on a fresh clone. The
mechanism tests do not need it and always run.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.pipeline.qc import reads_as_a_non_answer
from micromotives_datasets.recipe import Arm, Condition, Outcome, Recipe, Scale
from micromotives_datasets.recipe import load as load_recipe
from micromotives_datasets.sources import spss

REPO = Path(__file__).resolve().parents[1]
RECIPE = REPO / "recipes" / "QQM5MC.yaml"
DATA = REPO / "data" / "raw" / "QQM5MC" / "YouGovExp.dta"
VERIFY = REPO / "scripts" / "verify_QQM5MC.py"

NOT_ASKED = 9999

needs_deposit = pytest.mark.skipif(
    not DATA.exists(), reason="QQM5MC deposit not fetched (data/raw is gitignored)"
)


def _witnessed(ambiguous: int = 0, reason: str | None = None, **kwargs: Any) -> Condition:
    """Two conditions resolved by their own witness variables."""
    return Condition(
        not_asked_code=NOT_ASKED,
        ambiguous_routing=ambiguous,
        ambiguous_routing_reason=reason,
        factors=["prime"],
        arms=[
            Arm(
                witness_var="QA",
                condition_num=0,
                factors={"prime": "absent"},
                text="You went straight to the question.",
                items={0: {"outcome_var": "QA"}},
            ),
            Arm(
                witness_var="QB",
                condition_num=1,
                factors={"prime": "present"},
                text="You were asked about your identity first.",
                items={0: {"outcome_var": "QB"}},
            ),
        ],
        **kwargs,
    )


def _recipe(condition: Condition) -> Recipe:
    return Recipe(
        study_id="wit01",
        source="dataverse",
        data_file="fixture.sav",
        licence="not applicable — synthetic test fixture",
        condition=condition,
        outcomes=[
            Outcome(task_num=0, question="How is it?", scale=Scale(min=1, max=3)),
        ],
        response_recode={1: 1, 2: 2, 3: 3},
        missing_codes=[NOT_ASKED],
    )


# --- the mechanism, offline -------------------------------------------------


def test_exactly_one_arm_is_asked_when_the_other_block_says_not_asked() -> None:
    cond = _witnessed()
    assert [a.condition_num for a in cond.arms_asked({"QA": 2, "QB": NOT_ASKED})] == [0]
    assert [a.condition_num for a in cond.arms_asked({"QA": NOT_ASKED, "QB": 3})] == [1]


def test_a_blank_witness_is_read_as_not_asked() -> None:
    """A missing cell is no evidence the person saw the condition.

    Inventing one from an absent value is the whole error this mechanism exists to
    avoid, so None and the not-asked code must behave identically.
    """
    assert _witnessed().arms_asked({"QA": None, "QB": None}) == []


def test_being_asked_two_blocks_returns_both_rather_than_the_first() -> None:
    """The caller must be able to SEE the ambiguity; a picker would hide it."""
    asked = _witnessed().arms_asked({"QA": 2, "QB": 3})
    assert [a.condition_num for a in asked] == [0, 1]


def test_a_respondent_routed_twice_is_dropped_and_must_be_declared(tmp_path: Path) -> None:
    import pandas as pd
    import pyreadstat

    # Respondent 2 is asked both blocks; 0 saw A only, 1 saw B only.
    path = tmp_path / "fixture.sav"
    pyreadstat.write_sav(
        pd.DataFrame(
            {
                "QA": [2.0, float(NOT_ASKED), 2.0],
                "QB": [float(NOT_ASKED), 3.0, 3.0],
            }
        ),
        str(path),
    )
    ds = spss.read(path)

    # Undeclared: the melt refuses rather than discarding quietly.
    with pytest.raises(ValueError, match="routed to more than one condition"):
        list(build_rows(ds, _recipe(_witnessed())))

    # Declared: the ambiguous respondent is dropped, the other two build.
    rows = list(build_rows(ds, _recipe(_witnessed(1, "respondent 2 was routed to both"))))
    assert len(rows) == 2
    assert sorted(r.condition_num for r in rows) == [0, 1]


def test_declaring_more_ambiguity_than_exists_also_fails(tmp_path: Path) -> None:
    """Both directions fail. A stale declaration is as wrong as a missing one."""
    import pandas as pd
    import pyreadstat

    path = tmp_path / "clean.sav"
    pyreadstat.write_sav(
        pd.DataFrame({"QA": [2.0, float(NOT_ASKED)], "QB": [float(NOT_ASKED), 3.0]}),
        str(path),
    )
    with pytest.raises(ValueError, match="ambiguous_routing=1"):
        list(build_rows(spss.read(path), _recipe(_witnessed(1, "stale"))))


# --- what a recipe may and may not declare ----------------------------------


def test_a_witness_recipe_may_not_also_name_an_assignment_column() -> None:
    with pytest.raises(ValueError, match="cannot be resolved two ways"):
        _recipe(_witnessed(source_var="GROUP"))


def test_every_arm_needs_a_witness_once_not_asked_code_is_set() -> None:
    cond = _witnessed()
    cond.arms[1].witness_var = None
    with pytest.raises(ValueError, match="every arm needs a `witness_var`"):
        _recipe(cond)


def test_two_arms_may_not_share_a_witness() -> None:
    """Sharing one makes the conditions indistinguishable, not merely ambiguous."""
    cond = _witnessed()
    cond.arms[1].witness_var = "QA"
    with pytest.raises(ValueError, match="share a witness_var"):
        _recipe(cond)


def test_a_witness_without_a_not_asked_code_is_refused() -> None:
    """Otherwise the witness is inert and the recipe reads as though it were live."""
    with pytest.raises(ValueError, match="the witnesses would never be read"):
        Recipe(
            study_id="wit02",
            source="dataverse",
            data_file="f.sav",
            licence="synthetic",
            condition=Condition(
                source_var="GROUP",
                arms=[Arm(raw=1, witness_var="QA", condition_num=0, text="t")],
            ),
            outcomes=[Outcome(var="QA", task_num=0, question="q", scale=Scale(min=1, max=3))],
            response_recode={1: 1},
        )


def test_a_discarded_respondent_must_say_why() -> None:
    with pytest.raises(ValueError, match="without a reason"):
        _recipe(_witnessed(1))


def test_ambiguous_routing_is_meaningless_without_witnesses(fixture_recipe: Recipe) -> None:
    """A coded assignment yields one arm by construction, so the field cannot apply."""
    data = fixture_recipe.model_dump()
    data["condition"]["ambiguous_routing"] = 1
    data["condition"]["ambiguous_routing_reason"] = "n/a"
    with pytest.raises(ValueError, match="applies only to the witness design"):
        Recipe(**data)


# --- the real study ---------------------------------------------------------


@needs_deposit
def test_the_study_builds_to_the_shape_the_paper_describes() -> None:
    rows = list(build_rows(spss.read(DATA), load_recipe(RECIPE)))
    assert len(rows) == 6345
    # 3,267 respondents less ID 2158, who was routed to two conditions.
    assert len({r.participant_id for r in rows}) == 3266

    per_condition: dict[int, set[str]] = {}
    for r in rows:
        per_condition.setdefault(r.condition_num, set()).add(r.participant_id)  # type: ignore[arg-type]
    # Paper p. 23, four groups; block sizes A 859, B 820, C 798, D 791, with the
    # one ambiguous respondent removed from B and C. condition_num is the
    # do-file's Group coding: 0 Control, 1 Prime only, 2 Prime & Info, 3 Info only.
    assert {k: len(v) for k, v in sorted(per_condition.items())} == {
        0: 791,
        1: 819,
        2: 859,
        3: 797,
    }


@needs_deposit
def test_the_doubly_routed_respondent_is_absent() -> None:
    """`ID 2158` is row index 2157, so the participant id is QQM5MC:2157."""
    rows = list(build_rows(spss.read(DATA), load_recipe(RECIPE)))
    assert "QQM5MC:2157" not in {r.participant_id for r in rows}


@needs_deposit
def test_the_prime_appears_in_exactly_the_two_primed_conditions() -> None:
    """The prime IS the identity question, and the control saw neither it nor the
    information — paper p. 23: "The individuals in the control group (no referendum
    prime and no information) are only asked the economic performance questions."
    """
    rows = list(build_rows(spss.read(DATA), load_recipe(RECIPE)))
    prime_text = "do you think of yourself as a Leaver"
    primed = {r.condition_num for r in rows if prime_text in r.condition}
    informed = {r.condition_num for r in rows if "Gross Domestic Product" in r.condition}
    assert primed == {1, 2}
    assert informed == {2, 3}
    for r in rows:
        assert (r.factors["identity_prime"] == "present") == (r.condition_num in primed)
        assert (r.factors["economic_information"] == "present") == (r.condition_num in informed)


@needs_deposit
def test_no_condition_text_carries_a_truncated_label() -> None:
    """`work_type` is excluded because four of its labels are severed mid-word.

    At 120 characters, measured — this docstring said "Stata's 80-character
    ceiling" until a checker counted them. Ledger 85 had already recorded that
    this project's truncations run 80, 119 and 120, which is why the test matches
    the CUT rather than the length: a length threshold would miss two of the seven
    known cases, and the recipe's own 80 was recalled from 9xw67 rather than read.
    """
    from micromotives_datasets.persona.render import render

    labels = spss.read(DATA).value_labels
    severed_labels = [v for v in labels["work_type"].values() if len(v) == 120]
    assert len(severed_labels) == 4, f"expected four 120-char labels, got {len(severed_labels)}"

    rows = list(build_rows(spss.read(DATA), load_recipe(RECIPE)))
    severed = ("(e.g", "person", "secretar", "driver, b")
    offenders = {
        line for r in rows for line in render(r.persona).split("\n") if line.endswith(severed)
    }
    assert not offenders, offenders


@needs_deposit
def test_the_built_rows_reproduce_the_published_table() -> None:
    """UK studies have no SocSci210 row, so Table 1 is the answer key."""
    spec = importlib.util.spec_from_file_location("verify_QQM5MC", VERIFY)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["verify_QQM5MC"] = module
    spec.loader.exec_module(module)
    if not module.PARQUET.exists():
        pytest.skip("QQM5MC not built yet — run `mmds build recipes/QQM5MC.yaml`")
    assert module.check(module.load()) == []


@needs_deposit
def test_no_real_answer_is_declared_as_a_missing_code() -> None:
    """The one defect in this build that touched data, pinned.

    `Region_GOR: [12, ...]` declared "Northern Ireland" — a real region — as a
    sentinel. It dropped nothing, because this deposit has no respondent from
    Northern Ireland at all, and that is precisely why it survived a build, a QC
    pass and a read-through: an inert wrong declaration looks exactly like a
    correct one. It would have deleted the region of every NI respondent in a
    refetch, or in the next UK study that copied the pattern.

    Checked against the file's own value labels rather than a hand-written list,
    so this stays true if the deposit's coding ever changes.
    """
    recipe = load_recipe(RECIPE)
    labels = spss.read(DATA).value_labels
    by_upper = {k.upper(): k for k in labels}

    real_answers_dropped: list[str] = []
    for var, codes in recipe.persona_missing.items():
        key = by_upper.get(var.upper())
        if key is None:
            continue
        for code in codes:
            label = labels[key].get(float(code), "")
            if label and not reads_as_a_non_answer(label):
                real_answers_dropped.append(f"{var}={code} {label!r}")
    assert not real_answers_dropped, (
        f"persona_missing drops a label that reads as a real answer: "
        f"{real_answers_dropped}. Run scripts/persona_missing_audit.py."
    )
