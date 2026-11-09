"""The yjvpn recipe (TESS 1576, Kubicki: a photo of Alex, captioned transgender or
cisgender) and its answer key.

The generator reads the instruction screen, the captions, the image directive and every
outcome's words out of the fielded questionnaire (asserting the simple and programming
versions agree), and the three photographs out of the researcher's description
document; these tests stop a hand edit drifting from it, and check the facts the rows
rest on:

- each arm shows the photograph the questionnaire's directive names for its P_COND,
  and that photograph is the description document's picture for the same blocks,
  byte for byte, and the proposal's picture under the same heading;
- the condition text names the label but never the appearance, which only the picture
  carries; our descriptions name no gender, age or ethnicity;
- the thermometer keeps the slider positions 77, 98 and 99 (its own non-answers are
  777 / 998 / 999);
- the built rows reproduce SocSci210 (fetched 9 Nov 2026 by `mmds build --crosscheck`
  and transcribed here): 18,069 rows, 914 people, the same rows per condition, and
  the same row count per SocSci210 task once our 20 outcomes are grouped as theirs
  (12 gendered traits, 5 humanising traits, Q2, Q3, Q4).

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_yjvpn.py"
RECIPE = REPO / "recipes" / "images" / "yjvpn.yaml"
RAW = REPO / "data" / "raw" / "yjvpn"
DTA = RAW / "9089.138_TESS-Kubicki_20231109.dta"
BUILT = REPO / "data" / "processed" / "images" / "yjvpn.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_yjvpn", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not DTA.exists(), reason="yjvpn deposit not fetched")
needs_built = pytest.mark.skipif(not (BUILT.exists() and DTA.exists()), reason="yjvpn not built")
needs_tools = pytest.mark.skipif(
    not (shutil.which("pdfimages") and shutil.which("sips")), reason="needs pdfimages and sips"
)

# SocSci210, study yjvpn (mmds build --crosscheck, 9 Nov 2026).
SOCSCI210_ROWS = 18_069
SOCSCI210_PEOPLE = 914
SOCSCI210_PER_CONDITION = {0: 2912, 1: 3241, 2: 2820, 3: 3072, 4: 2884, 5: 3140}
SOCSCI210_PER_TASK = {0: 10881, 1: 4521, 2: 853, 3: 906, 4: 908}
# The proposal's "Highly Desirable Humanizing Traits (Haslam & Bain, 2007)"; the other
# twelve are its "Stereotypical Gendered Traits (Diekman & Eagly, 2000)".
HUMANISING = {"Ambitious", "Analytic", "Imaginative", "Passionate", "Sympathetic"}


@needs_raw
def test_recipe_is_what_the_generator_writes() -> None:
    assert RECIPE.read_text() == gen.render()


@needs_raw
def test_catalogue_entries_are_what_the_generator_derives() -> None:
    cat = images_mod.load()
    for image_id, entry in gen.catalogue_entries().items():
        assert cat[image_id].model_dump() == entry, image_id
        assert not images_mod.problems(image_id, cat), image_id


@needs_raw
def test_each_photo_is_its_blocks_picture_in_the_description_document() -> None:
    blocks = gen.docx_blocks()
    with zipfile.ZipFile(gen.DESCRIPTION) as z:
        for key, _, conds, member, names, _ in gen.PHOTOS:
            assert names == tuple(gen.P_COND_LABELS[c] for c in conds)
            for b in names:
                assert member in blocks[b], (key, b)
            assert (RAW / "images" / f"{key}.png").read_bytes() == z.read(member), key
    # and no condition block shows two of the three
    members = {p[3] for p in gen.PHOTOS}
    for b, media in blocks.items():
        assert len(members & set(media)) <= 1, b


@needs_raw
@needs_tools
def test_the_proposal_prints_the_same_faces_under_the_same_headings() -> None:
    for heading, dist in gen.proposal_distances().items():
        key = next(p[0] for p in gen.PHOTOS if p[5] == heading)
        assert min(dist, key=dist.__getitem__) == key, (heading, dist)
        assert dist[key] < 15.0 and min(v for k, v in dist.items() if k != key) > 25.0


@needs_raw
def test_simple_and_prog_questionnaires_say_the_same_words() -> None:
    assert gen.instrument(gen.SIMPLE) == gen.instrument(gen.PROG)
    q = gen.fielded()
    assert q["photos"] == {
        (1, 4): "9089.0138_MASQUALITY.PNG",
        (2, 5): "9089.0138_ANDROQUALITY.PNG",
        (3, 6): "9089.013_FEMQUALITY.PNG",
    }
    assert q["captions"] == {(1, 2, 3): "Alex, Transgender", (4, 5, 6): "Alex, Cisgender"}


def test_each_arm_shows_its_photo_and_caption() -> None:
    rec = load(RECIPE)
    expected = {
        1: ("masculine", "Transgender"),
        2: ("androgynous", "Transgender"),
        3: ("feminine", "Transgender"),
        4: ("masculine", "Cisgender"),
        5: ("androgynous", "Cisgender"),
        6: ("feminine", "Cisgender"),
    }
    assert sorted(a.raw or 0 for a in rec.condition.arms) == list(expected)
    for arm in rec.condition.arms:
        assert arm.raw is not None
        photo, label = expected[arm.raw]
        assert arm.condition_num == arm.raw - 1
        assert arm.images == [f"yjvpn_{photo}"]
        assert arm.factors == {"appearance": photo, "label": label.lower()}
        assert arm.text == f'A photo: <image> Centred beneath the photo: "Alex, {label}"'
        assert arm.text.count(images_mod.IMAGE_MARKER) == 1
    context = rec.condition.shared_context or ""
    assert context.startswith("Thank you for taking our survey.")
    assert context.endswith(
        "a transgender woman was born biologically male and identifies as a woman."
    )


def test_the_appearance_is_carried_by_the_picture_alone() -> None:
    rec = load(RECIPE)
    for arm in rec.condition.arms:
        text = rec.condition.render(arm).lower()
        # "female" and "male" are in the instruction screen's definitions, for every arm
        assert not re.search(r"\b(masculin\w*|feminin\w*|androgyn\w*)", text), arm.raw


# Words a description must not use: the study measures how people read this person's
# gender, so our account of the picture names no gender, age or ethnicity.
FORBIDDEN = (
    r"\b(man|men|woman|women|male|female|boy|girl|he|she|his|her|him|masculine|feminine|"
    r"androgynous|young|old|older|younger|aged?|white|black|asian|caucasian|hispanic|"
    r"latino|latina|european|attractive|handsome|pretty|beautiful|smil\w*|happy|sad|"
    r"friendly|confident|trans|transgender|cis|cisgender)\b"
)


def _offending(text: str) -> list[str]:
    return re.findall(FORBIDDEN, text.lower())


def test_the_forbidden_words_check_catches_and_passes() -> None:
    assert _offending("A young man with short hair, smiling.") == ["young", "man", "smiling"]
    assert _offending("Her hair falls past the ears.") == ["her"]
    assert _offending("A transgender person.") == ["transgender"]
    # what it must not catch: hair, shoulders, "the" contain "he", and so on
    assert (
        _offending("The head and shoulders; short hair; a grey top; transparent background") == []
    )


def test_descriptions_name_no_gender_age_or_ethnicity() -> None:
    for key, text in gen.DESCRIPTIONS.items():
        assert not _offending(text), (key, _offending(text))
        assert "No words." in text


@needs_built
def test_every_person_sees_one_condition() -> None:
    rows = pd.read_parquet(BUILT)
    per = rows.groupby("participant_id")["condition_num"].nunique()
    assert len(per) == SOCSCI210_PEOPLE and (per == 1).all()
    images = rows.groupby("condition_num")["condition_images"].first().map(list)
    assert images.to_dict() == {
        0: ["yjvpn_masculine"],
        1: ["yjvpn_androgynous"],
        2: ["yjvpn_feminine"],
        3: ["yjvpn_masculine"],
        4: ["yjvpn_androgynous"],
        5: ["yjvpn_feminine"],
    }


@needs_built
def test_the_thermometer_keeps_slider_positions_77_98_and_99() -> None:
    rows = pd.read_parquet(BUILT)
    q2 = rows[rows["task_num"] == 17]["response_num"]
    assert len(q2) == 853  # 914 minus 61 at 998 "SKIPPED ON WEB"
    counts = q2.value_counts().to_dict()
    assert (counts[77.0], counts[98.0], counts[99.0]) == (6, 4, 14)
    assert q2.between(0, 100).all()
    # and the other outcomes drop their 98 "SKIPPED ON WEB"
    others = rows[rows["task_num"] != 17]["response_num"]
    assert others.between(1, 7).all()


@needs_built
def test_rows_reproduce_socsci210() -> None:
    rows = pd.read_parquet(BUILT)
    assert len(rows) == SOCSCI210_ROWS
    assert rows["participant_id"].nunique() == SOCSCI210_PEOPLE
    assert rows["condition_num"].value_counts().to_dict() == SOCSCI210_PER_CONDITION
    traits = dict(enumerate(gen.fielded()["traits"]))

    def theirs(task: int) -> int:
        if task < 17:
            return 1 if traits[task] in HUMANISING else 0
        return task - 15

    grouped = rows["task_num"].map(theirs).value_counts().to_dict()
    assert grouped == SOCSCI210_PER_TASK


@needs_built
def test_persona_has_no_truncated_religion() -> None:
    rows = pd.read_parquet(BUILT)
    religions = {json.loads(p).get("religion") for p in rows["persona"].unique()}
    assert not any(r and r.endswith("Pent") for r in religions)
    assert any(r and r.startswith("Protestant (") and r.endswith("etc.)") for r in religions)


@needs_built
def test_built_parquet_is_current(tmp_path: Path) -> None:
    """The answer-key tests read the parquet on disk, so a stale build would let a
    generator change (e.g. two photos swapped between conditions) pass them unseen.
    Rebuild from the current recipe in memory and require the same rows."""
    from micromotives_datasets import cli

    rec, rows, _ = cli._load_and_build(RECIPE)
    fresh = pd.read_parquet(cli._write_parquet(rows, tmp_path, rec))
    on_disk = pd.read_parquet(BUILT)
    assert fresh.equals(on_disk), "yjvpn.parquet is stale: rebuild with mmds build"
