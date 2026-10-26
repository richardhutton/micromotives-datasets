"""Image conditions: rows cite pictures by ID; QC checks what was seen and that it is intact.

`k7tw5` (IMG02, the first image experiment) shows three different photographs under
the SAME words, so two things had to change, and each is tested in both directions:

* Rule 1 compares words AND images. Text alone would call three real arms one;
  but two arms showing the same words and the same picture are still one arm.
* Rule 23 is new: an image ID must be catalogued, its file present and unchanged,
  and the condition must carry one `<image>` marker per ID. Each way of failing
  silently trains on the wrong picture.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from micromotives_datasets import images as images_mod
from micromotives_datasets.pipeline import qc as qc_mod
from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.pipeline.qc import check
from micromotives_datasets.sources import spss


@pytest.fixture
def catalog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    """Two catalogued pictures on disk, with the QC pointed at them."""
    files = {}
    entries = {}
    for name in ("pic_a", "pic_b"):
        f = tmp_path / f"{name}.jpg"
        f.write_bytes(name.encode() * 50)
        files[name] = f
        entries[name] = images_mod.Image(
            file=str(f),  # absolute, so data_dir / file is the file itself
            sha256=images_mod.sha256_of(f),
            source="test",
            licence="test",
            description=f"a picture called {name}",
        )
    monkeypatch.setattr(qc_mod.images_mod, "load", lambda: entries)
    return files


def _rows_with_pictures(fixture_sav, fixture_recipe, same_text: bool, pics: list[str]):
    for arm, pic in zip(fixture_recipe.condition.arms, pics, strict=True):
        if same_text:
            arm.text = "The label: <image>"
        else:
            arm.text = f"{arm.text} <image>"
        arm.images = [pic]
    return list(build_rows(spss.read(fixture_sav), fixture_recipe))


def test_same_words_different_pictures_are_different_arms(
    fixture_sav, fixture_recipe, catalog
) -> None:
    """The k7tw5 case: Bowel cancer 1, 2 and 3 share their words, not their photo."""
    fixture_recipe.condition.factors = []
    for arm in fixture_recipe.condition.arms:
        arm.factors = {}
    rows = _rows_with_pictures(fixture_sav, fixture_recipe, True, ["pic_a", "pic_b"])
    rep = check(rows, fixture_recipe)
    assert not any("identical text" in f for f in rep.failures), rep.failures


def test_same_words_same_picture_is_still_a_lost_manipulation(
    fixture_sav, fixture_recipe, catalog
) -> None:
    rows = _rows_with_pictures(fixture_sav, fixture_recipe, True, ["pic_a", "pic_a"])
    rep = check(rows, fixture_recipe)
    assert any("identical text" in f for f in rep.failures)


def test_catalogued_intact_and_placed_pictures_pass(fixture_sav, fixture_recipe, catalog) -> None:
    rows = _rows_with_pictures(fixture_sav, fixture_recipe, False, ["pic_a", "pic_b"])
    rep = check(rows, fixture_recipe)
    assert rep.passed, rep.failures


def test_an_uncatalogued_picture_fails(fixture_sav, fixture_recipe, catalog) -> None:
    rows = _rows_with_pictures(fixture_sav, fixture_recipe, False, ["pic_a", "pic_missing"])
    rep = check(rows, fixture_recipe)
    assert any("pic_missing: not in the image catalogue" in f for f in rep.failures)


def test_a_changed_picture_fails(fixture_sav, fixture_recipe, catalog) -> None:
    """The file on disk is no longer the one the respondent saw."""
    catalog["pic_b"].write_bytes(b"something else entirely")
    rows = _rows_with_pictures(fixture_sav, fixture_recipe, False, ["pic_a", "pic_b"])
    rep = check(rows, fixture_recipe)
    assert any("pic_b: file changed" in f for f in rep.failures)


def test_a_missing_picture_file_fails(fixture_sav, fixture_recipe, catalog) -> None:
    catalog["pic_b"].unlink()
    rows = _rows_with_pictures(fixture_sav, fixture_recipe, False, ["pic_a", "pic_b"])
    rep = check(rows, fixture_recipe)
    assert any("pic_b: file missing" in f for f in rep.failures)


def test_a_picture_with_no_marker_fails(fixture_sav, fixture_recipe, catalog) -> None:
    """An ID the text never places: the model would get the picture nowhere."""
    rows = _rows_with_pictures(fixture_sav, fixture_recipe, False, ["pic_a", "pic_b"])
    rows[0].condition = rows[0].condition.replace("<image>", "")
    rep = check(rows, fixture_recipe)
    assert any("markers" in f for f in rep.failures)


def test_a_text_only_study_is_untouched(fixture_sav, fixture_recipe) -> None:
    """No images, no catalogue read, no new failures: every existing build stays as it was."""
    rows = list(build_rows(spss.read(fixture_sav), fixture_recipe))
    assert all(r.condition_images == [] for r in rows)
    assert check(rows, fixture_recipe).passed


def test_resolve_refuses_an_altered_file(tmp_path: Path) -> None:
    f = tmp_path / "x.jpg"
    f.write_bytes(b"original")
    cat = {
        "x": images_mod.Image(
            file=str(f), sha256=images_mod.sha256_of(f), source="t", licence="t", description="d"
        )
    }
    assert images_mod.resolve("x", cat) == f
    f.write_bytes(b"swapped")
    with pytest.raises(ValueError, match="file changed"):
        images_mod.resolve("x", cat)


def test_the_real_catalogue_is_well_formed() -> None:
    """Every entry parses; IDs are unique by construction of a JSON object."""
    raw = json.loads(images_mod.CATALOG.read_text())
    cat = images_mod.load()
    assert set(raw) == set(cat)
    for image_id, img in cat.items():
        assert len(img.sha256) == 64, image_id
        assert img.description, image_id
        assert not Path(img.file).is_absolute(), f"{image_id}: catalogue paths are relative"


def _harm_by_photo_recipe(photo_in_image: bool):
    """2 harms x 2 photos; the photo shows only in the picture, as in k7tw5."""
    from micromotives_datasets.recipe import Arm, Condition, Outcome, Recipe, Scale

    arms = []
    for i, (harm, photo) in enumerate(
        [("bowel", "1"), ("bowel", "2"), ("heart", "1"), ("heart", "2")]
    ):
        arms.append(
            Arm(
                raw=i + 1,
                condition_num=i,
                factors={"harm": harm, "photo": photo},
                text=f"Excess calories cause {harm} disease. <image>",
                images=[f"{harm}_{photo}" if photo_in_image else f"{harm}_1"],
            )
        )
    return Recipe(
        study_id="t",
        source="test",
        data_file="t.sav",
        condition=Condition(source_var="arm", factors=["harm", "photo"], arms=arms),
        outcomes=[Outcome(var="y", task_num=0, question="q?", scale=Scale(min=1, max=7))],
        response_recode={i: i for i in range(1, 8)},
    )


def _rule5_failures(recipe) -> list[str]:
    from micromotives_datasets.schema import Persona, Row

    rows = [
        Row(
            persona=Persona(),
            condition=a.text,
            condition_images=a.images,
            outcome="q?",
            response="1",
            response_num=1.0,
            condition_num=a.condition_num,
            task_num=0,
            factors=a.factors,
            source="test",
            study_id="t",
            participant_id=f"t:{a.condition_num}",
        )
        for a in recipe.condition.arms
    ]
    return [f for f in check(rows, recipe).failures if "does not change" in f]


def test_a_factor_expressed_only_by_the_picture_passes_rule_5() -> None:
    assert _rule5_failures(_harm_by_photo_recipe(photo_in_image=True)) == []


def test_a_photo_factor_whose_picture_never_changes_fails_rule_5() -> None:
    assert _rule5_failures(_harm_by_photo_recipe(photo_in_image=False))
