"""The melt, asserted exactly against a hand-computable fixture."""

from __future__ import annotations

from pathlib import Path

import pytest

from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.recipe import Recipe
from micromotives_datasets.sources import spss


def _rows(fixture_sav: Path, fixture_recipe: Recipe):
    return list(build_rows(spss.read(fixture_sav), fixture_recipe))


def test_row_count_drops_only_the_refused_item(fixture_sav, fixture_recipe) -> None:
    # 4 respondents x 2 items = 8, minus 1 refused = 7.
    # The refusal drops ONE item, not the whole respondent.
    rows = _rows(fixture_sav, fixture_recipe)
    assert len(rows) == 7
    assert len({r.participant_id for r in rows}) == 4


def test_responses_are_recoded_exactly(fixture_sav, fixture_recipe) -> None:
    rows = _rows(fixture_sav, fixture_recipe)
    by_task = {}
    for r in rows:
        by_task.setdefault(r.task_num, []).append(r.response_num)
    assert sorted(by_task[0]) == [-3.0, 0.0, 0.0, 3.0]  # A1: 5,8,2,5
    assert sorted(by_task[1]) == [-1.0, 1.0, 2.0]  # A2: 6,(refused),4,7


def test_condition_mapping_is_taken_from_the_recipe(fixture_sav, fixture_recipe) -> None:
    rows = _rows(fixture_sav, fixture_recipe)
    counts: dict[int, int] = {}
    for r in rows:
        counts[r.condition_num] = counts.get(r.condition_num, 0) + 1
    assert counts == {0: 3, 1: 4}  # respondent 2 refused one item


def test_condition_text_is_shared_context_plus_arm(fixture_sav, fixture_recipe) -> None:
    rows = _rows(fixture_sav, fixture_recipe)
    arm0 = next(r for r in rows if r.condition_num == 0)
    arm1 = next(r for r in rows if r.condition_num == 1)
    assert arm0.condition == 'You read a short profile. It said "good".'
    assert arm1.condition == 'You read a short profile. It said "bad".'
    assert arm0.condition != arm1.condition


def test_outcome_carries_question_and_scale_instruction(fixture_sav, fixture_recipe) -> None:
    rows = _rows(fixture_sav, fixture_recipe)
    r = next(r for r in rows if r.task_num == 0)
    assert r.outcome.startswith("How good?")
    assert 'from -3 to 3 where -3 means "Bad" and 3 means "Good"' in r.outcome


def test_persona_resolves_value_labels(fixture_sav, fixture_recipe) -> None:
    rows = _rows(fixture_sav, fixture_recipe)
    r = min(rows, key=lambda r: int(r.participant_id.split(":")[1]))
    assert r.persona.age == 30
    assert r.persona.sex == "Male"  # 1.0 -> label, not "1"


def test_values_outside_the_declared_scale_are_dropped(
    fixture_sav, fixture_recipe, tmp_path
) -> None:
    """An undeclared code must be dropped, never guessed at."""
    import pandas as pd
    import pyreadstat

    df = pd.DataFrame({"COND": [1.0], "A1": [99.0], "A2": [5.0], "AGE": [30.0], "SEX": [1.0]})
    p = tmp_path / "odd.sav"
    pyreadstat.write_sav(df, str(p))
    rows = list(build_rows(spss.read(p), fixture_recipe))
    assert [r.task_num for r in rows] == [1]  # A1=99 dropped, A2=5 kept


def test_undeclared_arm_is_skipped(fixture_sav, fixture_recipe, tmp_path) -> None:
    import pandas as pd
    import pyreadstat

    df = pd.DataFrame({"COND": [9.0], "A1": [5.0], "A2": [5.0], "AGE": [30.0], "SEX": [1.0]})
    p = tmp_path / "arm9.sav"
    pyreadstat.write_sav(df, str(p))
    assert list(build_rows(spss.read(p), fixture_recipe)) == []


def test_persona_variable_names_are_case_insensitive(fixture_sav, fixture_recipe) -> None:
    """Deposits and recipes disagree about capitalisation; that must not matter.

    A case-sensitive lookup silently dropped the ENTIRE persona of three studies
    — 33 mapped fields across 7,679 rows — because the recipes said `ppincimp`
    and the files said `PPINCIMP`. Persona is one of the four parts of the
    tuple, so those rows were near-useless, and nothing caught it: QC never
    inspected persona and crosscheck does not compare it.
    """
    fixture_recipe.persona_map = {"age": "age", "sex": "SeX"}  # file has AGE / SEX
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    assert rows[0].persona.age is not None
    assert rows[0].persona.sex is not None


def test_mapped_persona_variable_absent_from_data_is_an_error(fixture_sav, fixture_recipe) -> None:
    """Asking for a field and silently getting nothing is the failure mode."""
    import pytest

    fixture_recipe.persona_map = {"age": "AGE", "income": "NOT_A_COLUMN"}
    with pytest.raises(ValueError, match="persona variables not in data"):
        list(build_rows(spss.read(fixture_sav), fixture_recipe))


def test_the_melt_renders_each_respondent_s_own_line_order(tmp_path) -> None:
    """The melt must USE `line_order_vars`, not merely be able to.

    A unit test on `Condition.reorder_lines` proves the helper; it says nothing
    about whether the build calls it. `8ctbk` is why that distinction matters:
    its six attribute rows were randomised per respondent, 654 of the 720
    possible orders occur, and exactly ONE of 1,794 respondents saw the order
    the recipe rendered for everybody — so 17,463 of 17,464 rows asserted an
    order nobody had seen, and every count still reconciled.

    Two respondents, same condition, opposite orders.
    """
    import pandas as pd
    import pyreadstat

    from micromotives_datasets.recipe import Arm, Condition, Outcome, Recipe, Scale

    path = tmp_path / "o.sav"
    pyreadstat.write_sav(
        pd.DataFrame(
            {
                "X": [1.0, 1.0],
                "P1": [1.0, 2.0],
                "P2": [2.0, 1.0],
                "Y": [1.0, 2.0],
                "AGE": [40.0, 41.0],
            }
        ),
        str(path),
        column_labels={
            "X": "cond",
            "P1": "slot of line 1",
            "P2": "slot of line 2",
            "Y": "y",
            "AGE": "age",
        },
    )
    recipe = Recipe(
        study_id="t",
        source="tess",
        data_file="o.sav",
        licence="none stated",
        condition=Condition(
            source_var="X",
            line_order_vars=["P1", "P2"],
            arms=[Arm(raw=1, condition_num=0, text="1. apples\n2. pears")],
        ),
        outcomes=[
            Outcome(
                var="Y",
                task_num=0,
                question="q",
                scale=Scale(min=1, max=2, min_label="lo", max_label="hi"),
            )
        ],
        response_recode={1: 1, 2: 2},
        persona_map={"age": "AGE"},
    )
    rendered = sorted(r.condition for r in build_rows(spss.read(path), recipe))
    assert rendered == ["1. apples\n2. pears", "1. pears\n2. apples"], rendered


def _bullet_recipe(order_vars: list[str]):
    from micromotives_datasets.recipe import Arm, Condition, ItemOverride, Outcome, Recipe, Scale

    return Recipe(
        study_id="t",
        source="tess",
        data_file="o.sav",
        licence="none stated",
        condition=Condition(
            source_var="X",
            arms=[
                Arm(
                    raw=1,
                    condition_num=0,
                    text="list",
                    items={
                        0: ItemOverride(
                            outcome_var="Y",
                            condition_text="I have …\n• apples\n• pears\n• plums",
                            line_order_vars=order_vars,
                        )
                    },
                )
            ],
        ),
        outcomes=[
            Outcome(
                task_num=0,
                question="How many?",
                scale=Scale(min=0, max=3, min_label="none", max_label="all"),
            )
        ],
        response_recode={0: 0, 1: 1, 2: 2, 3: 3},
        persona_map={"age": "AGE"},
    )


def test_an_item_renders_its_own_bullet_order_and_keeps_its_stem(tmp_path) -> None:
    """IP 9.17: each list has its own order variables and keeps its bullets.

    Three respondents: two orders, and one whose order was not recorded, who must
    be skipped rather than shown the declared order.
    """
    import pandas as pd
    import pyreadstat

    path = tmp_path / "o.sav"
    pyreadstat.write_sav(
        pd.DataFrame(
            {
                "X": [1.0, 1.0, 1.0],
                "P1": [1.0, 3.0, -8.0],
                "P2": [2.0, 1.0, -8.0],
                "P3": [3.0, 2.0, -8.0],
                "Y": [1.0, 2.0, 2.0],
                "AGE": [40.0, 41.0, 42.0],
            }
        ),
        str(path),
    )
    recipe = _bullet_recipe(["P1", "P2", "P3"])
    # The third respondent ANSWERED with no order recorded: that must stop the
    # build, not vanish (found by the 9.17 checker; zero such rows in that study).
    with pytest.raises(ValueError, match="statement order is not recorded"):
        list(build_rows(spss.read(path), recipe))
    # Unanswered with no order: nothing to render, nothing lost.
    df = spss.read(path).df
    df.loc[2, "Y"] = -8.0
    pyreadstat.write_sav(df, str(path))
    rows = list(build_rows(spss.read(path), recipe.model_copy(update={"missing_codes": [-8]})))
    assert [r.condition for r in rows] == [
        "I have …\n• apples\n• pears\n• plums",
        "I have …\n• pears\n• plums\n• apples",
    ]


def test_a_bullet_order_with_the_wrong_number_of_variables_is_refused() -> None:
    with pytest.raises(ValueError, match="2 line_order_vars for 3 bullet lines"):
        _bullet_recipe(["P1", "P2"])


def test_reorder_bullets_refuses_a_non_permutation() -> None:
    from micromotives_datasets.recipe import Condition

    with pytest.raises(ValueError, match="not a permutation"):
        Condition.reorder_bullets("s\n• a\n• b", [1, 1])


def test_a_study_with_no_factors_can_be_written(tmp_path) -> None:
    """IP 9.13 is one condition with `factors: {}` on every row, which Parquet
    cannot store as an empty struct. The writer must cope, and must leave a
    study WITH factors exactly as it was."""
    import pandas as pd

    from micromotives_datasets.cli import _write_parquet
    from micromotives_datasets.schema import Persona, Row

    def row(factors: dict) -> Row:
        return Row(
            persona=Persona(),
            condition="c",
            outcome="o",
            response="1",
            response_num=1.0,
            condition_num=0,
            task_num=0,
            factors=factors,
            source="tess",
            study_id="t",
        )

    rec = _bullet_recipe(["P1", "P2", "P3"])
    path = _write_parquet([row({}), row({})], tmp_path / "a", rec)
    assert pd.read_parquet(path)["factors"].isna().all()
    path = _write_parquet([row({"x": "1"}), row({"x": "2"})], tmp_path / "b", rec)
    assert list(pd.read_parquet(path)["factors"].map(lambda f: f["x"])) == ["1", "2"]


def test_a_fill_resolving_to_nothing_at_the_end_leaves_no_trailing_space(tmp_path) -> None:
    """IP 9.13's second appeal is absent for most respondents and sits at the end of
    the condition; resolving it to nothing used to leave a trailing space."""
    import pandas as pd
    import pyreadstat

    from micromotives_datasets.recipe import Arm, Condition, Outcome, Recipe, Scale

    path = tmp_path / "f.sav"
    pyreadstat.write_sav(
        pd.DataFrame({"X": [1.0, 1.0], "F": [1.0, 2.0], "Y": [1.0, 1.0], "AGE": [40.0, 41.0]}),
        str(path),
    )
    rec = Recipe(
        study_id="t",
        source="tess",
        data_file="f.sav",
        licence="none stated",
        condition=Condition(
            source_var="X",
            arms=[Arm(raw=1, condition_num=0, text="Intro. [IF F=1 INSERT: Appeal.]")],
        ),
        outcomes=[
            Outcome(var="Y", task_num=0, question="q", scale=Scale(min=1, max=2, nominal=True))
        ],
        response_recode={1: 1, 2: 2},
        respondent_vars=["F"],
        persona_map={"age": "AGE"},
    )
    rows = list(build_rows(spss.read(path), rec))
    assert [r.condition for r in rows] == ["Intro. Appeal.", "Intro."]
