"""The 5an26 image recipe (TESS2 069, Paustian-Underdahl: a headshot and a short profile
of "Diane" or "David", then a job to hire for) and its answer key.

The generator reads every word out of the fielded questionnaire and the four photos out
of the same Word 97 document; these tests stop a hand edit drifting from it, and check
the facts the rows rest on:

- the four photos are the four inline pictures of Q's "Photos:" paragraph, left to right
  above the letters A B C D, byte for byte;
- the manipulation check Q29 rates the two photos Q's table calls Attractive above the
  two it calls Unattractive, and the check fails if a photo is swapped;
- each row's condition says only what everyone in its arm had seen by its question: no
  job before Part III, no SAT screen before Part IV;
- nothing we write names a judgement of looks, and our descriptions name no gender,
  race or age;
- the rows are SocSci210's Q1-Q26 rows, per photo, once its Q29 rows are added back.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_5an26.py"
RECIPE = REPO / "recipes" / "images" / "5an26.yaml"
RAW = REPO / "data" / "raw" / "5an26"
SAV = RAW / "TESS2_069_Paustian-Underdahl_Client.sav"
BUILT = REPO / "data" / "processed" / "images" / "5an26.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_5an26", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not SAV.exists(), reason="5an26 deposit not fetched")
needs_built = pytest.mark.skipif(not (BUILT.exists() and SAV.exists()), reason="5an26 not built")

PHOTO_OF_ARM = {n: "abcd"[(n - 1) // 4] for n in range(1, 17)}
DIANE = (
    "<image> Diane Williams is a 40-year-old professional woman. She's been working in her "
    "current position for six years. Her hobbies include swimming and tennis. She also likes "
    "to spend time with family, friends, and her two dogs."
)

# SocSci210's 5an26: four conditions (photo A-D, occupations merged), 27 items that are
# the .sav's Q1-Q26 and Q29 in file order (matched on response distributions).
SOCSCI210_ROWS = 11_689
SOCSCI210_PER_PHOTO = {0: 2792, 1: 2987, 2: 2956, 3: 2954}
Q29_ANSWERS_PER_PHOTO = {0: 104, 1: 111, 2: 109, 3: 109}


@needs_raw
def test_recipe_is_what_the_generator_writes() -> None:
    assert RECIPE.read_text() == gen.render()


@needs_raw
def test_catalogue_entries_are_what_the_generator_derives() -> None:
    cat = images_mod.load()
    for image_id, entry in gen.catalogue_entries().items():
        assert cat[image_id].model_dump() == entry, image_id
        assert not images_mod.problems(image_id, cat), image_id
    assert sorted(gen.catalogue_entries()) == [f"5an26_photo_{x}" for x in "abcd"]


@needs_raw
def test_the_photos_are_qs_four_pictures_left_to_right() -> None:
    cps, offsets, letters = gen.photos_paragraph()
    assert cps == [1781, 1795, 1817, 1834]
    assert offsets == sorted(offsets) and len(set(offsets)) == 4
    assert letters.split() == ["A", "B", "C", "D"]
    pics = gen.picture_bytes()
    for letter, data in pics.items():
        assert (REPO / "data" / gen.image_file(letter)).read_bytes() == data, letter
        assert gen.picture_size(data) == gen.SIZES[letter]
    # the only other picture in Q is in the footer (the fieldwork firm's logo)
    others = [p for p in gen.doc_pictures() if p[0] not in cps]
    assert len(others) == 1 and others[0][0] > 19_000


@needs_raw
def test_the_design_table_gives_each_arm_its_photo() -> None:
    table = gen.design_table()
    assert {n: row[0].lower() for n, row in table.items()} == PHOTO_OF_ARM
    assert {row[0]: row[1:3] for row in table.values()} == {
        "A": ("Female", "Attractive"),
        "B": ("Male", "Attractive"),
        "C": ("Female", "Unattractive"),
        "D": ("Male", "Unattractive"),
    }


@needs_raw
def test_q29_rates_the_attractive_photos_higher_and_catches_a_swap() -> None:
    means = gen.q29_means()
    table = gen.design_table()
    gen.check_attractiveness(means, table)  # raises on failure
    assert round(means["a"], 2) == 6.96 and round(means["c"], 2) == 4.20
    swapped = {**means, "a": means["c"], "c": means["a"]}
    with pytest.raises(SystemExit):
        gen.check_attractiveness(swapped, table)
    swapped = {**means, "b": means["d"], "d": means["b"]}
    with pytest.raises(SystemExit):
        gen.check_attractiveness(swapped, table)


@needs_raw
def test_the_profile_is_the_same_within_a_gender() -> None:
    profs = gen.profiles()
    assert {profs[n][1] for n in (1, 2, 3, 4, 9, 10, 11, 12)} == {DIANE.removeprefix("<image> ")}
    assert len({profs[n][1] for n in (5, 6, 7, 8, 13, 14, 15, 16)}) == 1


def test_each_arm_shows_its_photo_and_expresses_its_factors() -> None:
    rec = load(RECIPE)
    assert sorted(a.raw or 0 for a in rec.condition.arms) == list(range(1, 17))
    for arm in rec.condition.arms:
        assert arm.raw is not None and arm.condition_num == arm.raw - 1
        assert arm.images == [f"5an26_photo_{PHOTO_OF_ARM[arm.raw]}"]
        assert arm.text.count(images_mod.IMAGE_MARKER) == 1
        assert f"position of {arm.factors['occupation']}\n" in arm.text
        assert ("Diane" in arm.text) == (arm.factors["gender"] == "Female")
        assert ("David" in arm.text) == (arm.factors["gender"] == "Male")


def test_each_row_says_only_what_had_been_seen() -> None:
    rec = load(RECIPE)
    by_task = {o.task_num: o for o in rec.outcomes}
    for arm in rec.condition.arms:
        assert arm.raw is not None
        for task, outcome in by_task.items():
            text = rec.condition_text_for(outcome, arm)
            assert text.startswith(rec.condition.shared_context or "")
            assert text.count(images_mod.IMAGE_MARKER) == 1
            has_job = arm.factors["occupation"] in text
            has_sat = "SAT" in text
            if task <= 20:  # Parts I and II: the photo and profile only
                expected = DIANE if arm.factors["gender"] == "Female" else None
                assert not has_job and not has_sat and "Emory" not in text, (arm.raw, task)
                if expected:
                    assert text.endswith(expected)
            elif task <= 25:  # Part III
                assert has_job and not has_sat and text.endswith("scored well."), (arm.raw, task)
            else:  # Part IV
                assert has_job and has_sat and text.endswith("information on SAT scores.")


# Words neither a description nor anything we render may use about the person.
FORBIDDEN = (
    r"\b(attractive\w*|unattractive|beaut\w*|pretty|handsome|good-looking|plain|ugly|"
    r"black|white|asian|african|american|caucasian|hispanic|latino|latina|race|racial|"
    r"ethnic\w*|skin|man|men|woman|women|male|female|he|she|his|her|him|young|old|older|"
    r"younger|aged?|middle-aged|smil\w*|happy|friendly|bald\w*|hair\w*|curl\w*|blond\w*|"
    r"brunette|redhead\w*)\b"
)
ALLOWED_COLOUR = re.compile(r"\b(white shirt|black jacket)\b")


def _offending(text: str) -> list[str]:
    return re.findall(FORBIDDEN, ALLOWED_COLOUR.sub("", text.lower()))


def test_the_forbidden_words_check_catches_and_passes() -> None:
    assert _offending("An attractive woman, smiling, with curly hair.") == [
        "attractive",
        "woman",
        "smiling",
        "curly",
        "hair",
    ]
    assert _offending("A white man in a white shirt.") == ["white", "man"]
    # what it must not catch: clothing, "the", "shoulders", "chest", "there"
    assert _offending("The head and shoulders, cropped at the chest; a white shirt; there") == []


def test_descriptions_name_no_looks_gender_race_or_age() -> None:
    assert set(gen.DESCRIPTIONS) == set("abcd")
    for letter, text in gen.DESCRIPTIONS.items():
        assert not _offending(text), (letter, _offending(text))
        assert text.endswith("No words.")
    assert len(set(gen.DESCRIPTIONS.values())) == 4


def test_nothing_rendered_names_attractiveness() -> None:
    rec = load(RECIPE)
    for arm in rec.condition.arms:
        for outcome in rec.outcomes:
            text = rec.condition_text_for(outcome, arm) + rec.outcome_text_for(outcome, arm)
            assert not re.search(r"attractiv|beaut|looks", text, re.I), (arm.raw, outcome.var)


def test_outcomes_are_q1_to_q26_and_the_two_men_boxes() -> None:
    rec = load(RECIPE)
    assert [o.var for o in rec.outcomes] == [f"Q{i}" for i in range(1, 27)] + [
        "Q27_Male",
        "Q28_Male",
    ]
    assert [o.task_num for o in rec.outcomes] == list(range(28))
    assert "Q29" not in {o.var for o in rec.outcomes}
    arm16 = next(a for a in rec.condition.arms if a.raw == 16)
    q = {o.var: rec.outcome_text_for(o, arm16) for o in rec.outcomes}
    assert q["Q1"].startswith("How intelligent do you perceive David to be? Only return an ")
    assert q["Q21"].startswith(
        "How adequately do you think David exhibits the following competencies: Sympathy Only"
    )
    assert q["Q24"].startswith(
        "On a scale of 1 (LOW) to 5 (HIGH) please rate the applicant on the following items. "
        "How well David would fit in on the job as a Human Resources Specialist? Only"
    )
    assert q["Q26"].startswith(
        "Which of these starting salaries is closest to what you think David should earn? "
        "Options: 1 = $20,000-$39,999, "
    )
    assert q["Q28_Male"].startswith(
        "Suppose you had twenty positions to fill where the work required working with words. "
        "Of the twenty people you hired to work with words, how many do you think would be "
        'men and women? Report only the number for "Men". Only return an integer from 0 to 20'
    )


@needs_built
def test_every_person_sees_one_photo_and_one_arm() -> None:
    rows = pd.read_parquet(BUILT)
    assert len(rows) == 12_126
    per = rows.groupby("participant_id")["condition_num"].nunique()
    assert len(per) == 435 and (per == 1).all()
    images = rows.groupby("condition_num")["condition_images"].first().map(list)
    assert images.to_dict() == {n - 1: [f"5an26_photo_{PHOTO_OF_ARM[n]}"] for n in range(1, 17)}
    assert rows.groupby("task_num").size().to_dict()[26] == 435  # Q27 Men: no refusals
    q27 = rows[rows["task_num"] == 26]["response_num"]
    assert q27.between(0, 20).all() and q27.value_counts()[10.0] == 164


@needs_built
def test_rows_reconcile_with_socsci210() -> None:
    rows = pd.read_parquet(BUILT)
    q1_q26 = rows[rows["task_num"] <= 25]
    assert len(q1_q26) + sum(Q29_ANSWERS_PER_PHOTO.values()) == SOCSCI210_ROWS
    per_photo = q1_q26.groupby(q1_q26["condition_num"] // 4).size().to_dict()
    assert {k: v + Q29_ANSWERS_PER_PHOTO[k] for k, v in per_photo.items()} == SOCSCI210_PER_PHOTO
    df = gen.read_any(SAV).df
    ok = df["Q29"].between(1, 9)
    q29 = ((df.loc[ok, "XTESS069"] - 1) // 4).astype(int).value_counts().to_dict()
    assert q29 == Q29_ANSWERS_PER_PHOTO


@needs_built
def test_built_parquet_is_current(tmp_path: Path) -> None:
    """The answer-key tests read the parquet on disk, so a stale build would let a
    generator change (e.g. two photos swapped between arms) pass them unseen.
    Rebuild from the current recipe in memory and require the same rows."""
    from micromotives_datasets import cli

    rec, rows, _ = cli._load_and_build(RECIPE)
    fresh = pd.read_parquet(cli._write_parquet(rows, tmp_path, rec))
    on_disk = pd.read_parquet(BUILT)
    assert fresh.equals(on_disk), "5an26.parquet is stale: rebuild with mmds build"
