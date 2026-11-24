"""Background: who ran the survey, where and when, kept apart from the condition.

Ruled 24 Nov 2026 (rich): a condition holds only what the respondent was shown; true
background is one fixed sentence in its own field, for every study or for none. QC rule
25 enforces the first half and scripts/export.py the second. Each check is tested in
both directions: what it must catch, and the legitimate case it must leave alone.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.pipeline.qc import _BACKGROUND_FORM, check
from micromotives_datasets.recipe import Background
from micromotives_datasets.sources import spss

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import export

BG = Background(run_by="YouGov", where="Great Britain", when="October 2017", sources=["x"])


def _rule25(rep) -> list[str]:
    return [f for f in rep.failures if f.startswith("rule 25")]


def test_render_is_the_fixed_form() -> None:
    assert BG.render() == "This survey was run by YouGov in Great Britain in October 2017."
    assert _BACKGROUND_FORM.fullmatch(BG.render())


def test_a_background_needs_a_source() -> None:
    with pytest.raises(ValueError):
        Background(run_by="YouGov", where="Great Britain", when="October 2017", sources=[])


def test_background_reaches_every_row_and_passes(fixture_sav, fixture_recipe) -> None:
    fixture_recipe.background = BG
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    assert {r.background for r in rows} == {BG.render()}
    assert _rule25(check(rows, fixture_recipe)) == []


def test_no_background_is_also_clean(fixture_sav, fixture_recipe) -> None:
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    assert {r.background for r in rows} == {""}
    assert _rule25(check(rows, fixture_recipe)) == []


def test_a_row_whose_background_differs_fails(fixture_sav, fixture_recipe) -> None:
    """Background must be identical across versions, or it becomes a manipulation."""
    fixture_recipe.background = BG
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    rows[0] = rows[0].model_copy(
        update={"background": "This survey was run by Ipsos in Wales in 2019."}
    )
    assert _rule25(check(rows, fixture_recipe))


@pytest.mark.parametrize(
    "sentence",
    [
        "You are taking part in an online survey run by YouGov UK on 30-31 October 2017.",
        "You are taking part in an online survey of adults in Great Britain, run by YouGov.",
        "You are taking part in the December 2019 post-election wave of the British Election "
        "Study internet panel, run by YouGov.",
        "You are taking part in the second part of an online survey about the EU.",
        "This survey was run by YouGov in Great Britain in October 2017.",
    ],
)
def test_background_inside_the_condition_fails(fixture_sav, fixture_recipe, sentence) -> None:
    """The ten Brexit recipes' own phrasings, and the rendered form itself."""
    arm = fixture_recipe.condition.arms[0]
    arm.text = f"{sentence} {arm.text}"
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    assert _rule25(check(rows, fixture_recipe))


@pytest.mark.parametrize(
    "sentence",
    [
        "Imagine you are taking part in a clinical trial of a new drug.",
        "A survey found that 40% of people agree.",
        "You are taking part in a game with another player.",
        "The survey was long, and you are taking part in the next stage.",
    ],
)
def test_stimuli_that_merely_mention_surveys_pass(fixture_sav, fixture_recipe, sentence) -> None:
    """What the rule must NOT catch: stimuli people were shown."""
    arm = fixture_recipe.condition.arms[0]
    arm.text = f"{sentence} {arm.text}"
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    assert _rule25(check(rows, fixture_recipe)) == []


def _frame(backgrounds: dict[str, str]) -> pd.DataFrame:
    return pd.DataFrame({"recipe": list(backgrounds), "background": list(backgrounds.values())})


def test_export_drops_a_partly_filled_background() -> None:
    rows, report = export.background_everywhere_or_nowhere(
        _frame({"a": BG.render(), "b": "", "c": BG.render()})
    )
    assert "background" not in rows
    assert report == {"included": False, "recipes_with": 2, "recipes": 3}


def test_export_keeps_a_background_every_row_has() -> None:
    rows, report = export.background_everywhere_or_nowhere(
        _frame({"a": BG.render(), "b": BG.render()})
    )
    assert "background" in rows
    assert report["included"] is True


def test_export_treats_a_missing_column_as_none() -> None:
    _rows, report = export.background_everywhere_or_nowhere(pd.DataFrame({"recipe": ["a"]}))
    assert report == {"included": False, "recipes_with": 0, "recipes": 1}


def test_a_recipe_carrying_its_own_background_is_refused(tmp_path) -> None:
    """Background lives in one place, the catalogue, so the two can never disagree."""
    from micromotives_datasets import recipe as recipe_mod

    src = Path(__file__).resolve().parents[1] / "recipes" / "QQM5MC.yaml"
    bad = tmp_path / "QQM5MC.yaml"
    bad.write_text(src.read_text() + "\nbackground:\n  run_by: YouGov\n")
    with pytest.raises(ValueError, match=r"backgrounds\.json"):
        recipe_mod.load(bad)


def test_load_attaches_the_catalogue_entry() -> None:
    from micromotives_datasets import recipe as recipe_mod

    rec = recipe_mod.load(Path(__file__).resolve().parents[1] / "recipes" / "QQM5MC.yaml")
    assert rec.background is not None
    assert rec.background.render() == "This survey was run by YouGov in Great Britain in July 2018."


def test_every_catalogue_entry_names_a_real_recipe_and_renders() -> None:
    import json

    root = Path(__file__).resolve().parents[1]
    entries = json.loads((root / "data" / "catalog" / "backgrounds.json").read_text())["recipes"]
    stems = {p.stem for p in (root / "recipes").rglob("*.yaml")}
    assert set(entries) <= stems, sorted(set(entries) - stems)
    for name, entry in entries.items():
        assert _BACKGROUND_FORM.fullmatch(Background.model_validate(entry).render()), name
