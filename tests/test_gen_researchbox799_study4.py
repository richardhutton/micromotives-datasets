"""The researchbox799 Study 4 recipe (IMG73, wheelchair user in a restaurant ad) and its answer key.

The generator reads every word of the condition and the outcomes out of the fielded
.qsf; these tests stop a hand edit drifting from it, and check the facts the rows
rest on:

- each arm shows its own picture, as the .qsf's graphic ids and the PDF's pages say;
- the control arm's inclusivity items carry their own page's headline, which differs
  from its attitudes page ("Features Wheelchair-Using Patron" over the control ad);
- every outcome's wording is the .qsf's, the same in all three arms;
- the built rows reproduce the paper (Cossu, Estes & Vosgerau 2026, Study 4): the
  sample's demographics, Table 2's means and SDs, and the six t-tests and effect sizes.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_researchbox799_study4.py"
RECIPE = REPO / "recipes" / "images" / "researchbox799_study4.yaml"
BUILT = REPO / "data" / "processed" / "images" / "researchbox799_study4.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_researchbox799_study4", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.QSF.exists(), reason="researchbox799 not fetched")
needs_built = pytest.mark.skipif(
    not (BUILT.exists() and gen.QSF.exists()), reason="researchbox799 study 4 not built"
)

CONTROL, DIVERGENT, COMPLIANT = 0, 1, 2
WHEELCHAIR_HEADLINE = "Pastamasta Kitchen Features Wheelchair-Using Patron in Latest Campaign"
CONTROL_HEADLINE = "Pastamasta Kitchen Features Patron in Latest Campaign"


@needs_raw
def test_recipe_is_what_the_generator_writes() -> None:
    assert RECIPE.read_text() == gen.render()


@needs_raw
def test_catalogue_entries_are_what_the_generator_derives() -> None:
    cat = images_mod.load()
    for image_id, entry in gen.catalogue_entries().items():
        assert cat[image_id].model_dump() == entry, image_id
        assert not images_mod.problems(image_id, cat), image_id


def test_each_arm_shows_its_own_picture_and_brief() -> None:
    rec = load(RECIPE)
    arms = {a.condition_num: a for a in rec.condition.arms}
    assert {n: a.raw for n, a in arms.items()} == {CONTROL: 2, DIVERGENT: 1, COMPLIANT: 0}
    assert arms[CONTROL].images == ["researchbox799_study4_ad_control"]
    assert (
        arms[DIVERGENT].images == arms[COMPLIANT].images == ["researchbox799_study4_ad_wheelchair"]
    )
    for arm in arms.values():
        assert arm.text.count(images_mod.IMAGE_MARKER) == 1
        assert arm.text.endswith('"pastamasta" <image>')
    assert f"\n{CONTROL_HEADLINE}\n" in arms[CONTROL].text
    assert "manual wheelchair" not in arms[CONTROL].text
    assert f"\n{WHEELCHAIR_HEADLINE}\n" in arms[DIVERGENT].text
    assert "European Inclusive Advertising Standard" not in arms[DIVERGENT].text
    assert f"\n{WHEELCHAIR_HEADLINE}, Citing New EU Regulations\n" in arms[COMPLIANT].text
    assert "European Inclusive Advertising Standard (EIAS)" in arms[COMPLIANT].text


def test_only_the_control_inclusivity_page_has_another_headline() -> None:
    rec = load(RECIPE)
    for arm in rec.condition.arms:
        for task, item in arm.items.items():
            if arm.condition_num == CONTROL and task in gen.INCLUSIVITY_TASKS:
                assert item.condition_text is not None
                assert item.condition_text == arm.text.replace(
                    CONTROL_HEADLINE, WHEELCHAIR_HEADLINE
                )
                assert "manual wheelchair" not in item.condition_text
            else:
                assert item.condition_text is None, (arm.condition_num, task)


@needs_raw
def test_pages_as_fielded() -> None:
    """Read the .qsf directly: the headline mismatch is the instrument's, not ours."""
    for _, _, _, _, att, incl, img in gen.ARMS:
        a, i = gen.page(att), gen.page(incl)
        assert a[1:] == i[1:]
        assert a[2] == gen.IMAGES[img][0]
    assert gen.page("Control Attitudes")[0] == CONTROL_HEADLINE
    assert gen.page("Control Inclusivity")[0] == WHEELCHAIR_HEADLINE


@needs_raw
def test_outcome_wording_is_the_qsf_in_every_arm() -> None:
    rec = load(RECIPE)
    by_tag = gen._by_tag()
    for o in rec.outcomes:
        for arm in rec.condition.arms:
            suffix = next(a[3] for a in gen.ARMS if a[0] == arm.condition_num)
            p = by_tag[gen.tag_for(o.task_num, suffix)]
            assert o.question.startswith(gen._text(p["QuestionText"]))
            assert arm.items[o.task_num].outcome_var == gen.var_for(o.task_num, suffix)
    assert [o.scale.max for o in rec.outcomes] == [100] * 6 + [7] * 3
    assert rec.outcomes[6].question.endswith('"The brand supports inclusivity."')


def _wide() -> pd.DataFrame:
    rows = pd.read_parquet(BUILT)
    w = rows.pivot(index="participant_id", columns="task_num", values="response_num")
    w["arm"] = rows.groupby("participant_id")["condition_num"].first()
    w["attitudes"] = w[[0, 1, 2, 3, 4, 5]].mean(axis=1)
    w["inclusivity"] = w[[6, 7, 8]].mean(axis=1)
    return w


@needs_built
def test_sample_matches_the_paper() -> None:
    import json

    rows = pd.read_parquet(BUILT)
    assert len(rows) == 451 * 9
    people = rows.groupby("participant_id")["persona"].first().map(json.loads)
    assert len(people) == 451  # 455 recruited, 4 failed the attention check
    ages = np.array([p["age"] for p in people])
    assert round(ages.mean(), 2) == 43.83 and round(ages.std(ddof=1), 2) == 14.44
    assert round(100 * np.mean([p["gender"] == "Female" for p in people])) == 57
    disabled = [
        p["extra"].get("type_of_disability")
        for p in people
        if p["extra"]["has_a_disability"] == "Yes"
    ]
    assert round(100 * len(disabled) / 451, 1) == 12.6  # printed "12.5 %"
    kinds = pd.Series(disabled).str.split(" [(]").str[0].value_counts().to_dict()
    # Printed: 5% mental, 4% physical, 3% both.
    shares = {k: round(100 * n / 451) for k, n in kinds.items()}
    assert shares == {"Mental": 5, "Physical": 4, "Mental and physical": 3}


@needs_built
def test_paper_table_2() -> None:
    w = _wide()
    assert w["arm"].value_counts().to_dict() == {DIVERGENT: 151, CONTROL: 150, COMPLIANT: 150}
    # Table 2: inclusivity (mean, SD), attitudes (mean, SD).
    table = {
        CONTROL: (4.94, 1.06, 65.01, 18.71),
        DIVERGENT: (5.66, 0.93, 75.05, 17.30),
        COMPLIANT: (5.72, 0.92, 71.46, 18.15),
    }
    for arm, printed in table.items():
        g = w[w["arm"] == arm]
        got = (
            g["inclusivity"].mean(),
            g["inclusivity"].std(),
            g["attitudes"].mean(),
            g["attitudes"].std(),
        )
        # One cell is truncated, not rounded: control inclusivity is 4.9467, printed
        # 4.94. Every other cell agrees to the printed two decimals.
        tol = 0.0067 if arm == CONTROL else 0.005
        assert np.allclose(got, printed, atol=tol), (arm, got)


@needs_built
def test_paper_t_tests() -> None:
    w = _wide()
    # (a, b, measure, |t| printed, d printed). Student's t, as SPSS T-TEST reports first.
    # Two t's sit off the printed value by more than rounding: divergent vs control on
    # attitudes is 4.835 here (printed 4.84) and divergent vs compliant on inclusivity
    # 0.647 (printed .67, with p = .518 printed, which 0.647 gives). Hence the 0.025.
    printed = (
        (DIVERGENT, CONTROL, "inclusivity", 6.18, 0.71),
        (COMPLIANT, CONTROL, "inclusivity", 6.80, 0.79),
        (DIVERGENT, COMPLIANT, "inclusivity", 0.67, 0.08),
        (DIVERGENT, CONTROL, "attitudes", 4.84, 0.56),
        (COMPLIANT, CONTROL, "attitudes", 3.03, 0.35),
        (DIVERGENT, COMPLIANT, "attitudes", 1.76, 0.20),
    )
    for a, b, m, t_printed, d_printed in printed:
        x = w.loc[w["arm"] == a, m]
        y = w.loc[w["arm"] == b, m]
        t = stats.ttest_ind(x, y)
        sp = np.sqrt(((len(x) - 1) * x.var() + (len(y) - 1) * y.var()) / (len(x) + len(y) - 2))
        assert abs(abs(t.statistic) - t_printed) < 0.025, (a, b, m, t.statistic)
        d = abs(x.mean() - y.mean()) / sp
        assert abs(d - d_printed) <= 0.0055, (a, b, m, d)
    p = stats.ttest_ind(
        w.loc[w["arm"] == DIVERGENT, "inclusivity"], w.loc[w["arm"] == COMPLIANT, "inclusivity"]
    ).pvalue
    assert round(p, 3) == 0.518


def _sq(qid: str, tag: str, text: str) -> dict[str, Any]:
    return {
        "Element": "SQ",
        "Payload": {"QuestionID": qid, "DataExportTag": tag, "QuestionText": text},
    }


def test_a_trashed_duplicate_tag_is_never_read() -> None:
    """The trashed copy comes LAST in file order, where a naive lookup would let it win."""
    fake = {
        "SurveyElements": [
            {
                "Element": "BL",
                "Payload": [
                    {
                        "Type": "Standard",
                        "Description": "Live",
                        "BlockElements": [{"Type": "Question", "QuestionID": "QID1"}],
                    },
                    {
                        "Type": "Trash",
                        "Description": "Trash",
                        "BlockElements": [{"Type": "Question", "QuestionID": "QID2"}],
                    },
                ],
            },
            _sq("QID1", "Inclus_control", "live wording"),
            _sq("QID2", "Inclus_control", "trashed wording"),
        ]
    }
    assert gen._by_tag(fake)["Inclus_control"]["QuestionText"] == "live wording"


@needs_raw
def test_the_qsf_duplicates_resolve_to_the_live_questions() -> None:
    d = gen.qsf()
    tags = [e["Payload"].get("DataExportTag") for e in d["SurveyElements"] if e["Element"] == "SQ"]
    assert tags.count("Incl_disability_V") == 2 and tags.count("Inclus_control") == 2
    by_tag = gen._by_tag()
    assert by_tag["Incl_disability_V"]["QuestionID"] == "QID152"
    assert by_tag["Inclus_control"]["QuestionID"] == "QID153"
