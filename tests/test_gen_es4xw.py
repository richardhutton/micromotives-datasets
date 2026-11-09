"""The es4xw image recipe (TESS2 040, Bauman: one of four photographs of a six-person
management team) and its answer key.

The generator reads the caption, the outcome statements and the grid header out of the
fielded questionnaire, and the four pictures out of the same document; these tests stop
a hand edit drifting from it, and check the facts the rows rest on:

- each arm shows the picture Q embeds directly under its own "[SHOW BELOW PICTURE IF
  XTESS042=n]" directive, byte for byte;
- the four pictures share four of six photographs and differ in the top-middle and
  bottom-left, picture 3 combining picture 2's top-middle with picture 1's bottom-left;
- the condition is the fielded caption after the picture and says nothing about anyone's
  race; our descriptions name no race, ethnicity, gender or age;
- the arms' composition factors are where the data put them (picture 3 highest-rated
  as diverse by every respondent group, picture 4 lowest, and the in-group gap that
  places the Black team members in picture 1);
- every row, outcome, response, persona and factor equals the text build's
  (recipes/es4xw.yaml), only the condition differing.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_es4xw.py"
RECIPE = REPO / "recipes" / "images" / "es4xw.yaml"
RAW = REPO / "data" / "raw" / "es4xw"
SAV = RAW / "TESS2_040_Bauman_Client.sav"
BUILT = REPO / "data" / "processed" / "images" / "es4xw.parquet"
TEXT_BUILT = REPO / "data" / "processed" / "es4xw.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_es4xw", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not SAV.exists(), reason="es4xw deposit not fetched")
needs_built = pytest.mark.skipif(not (BUILT.exists() and SAV.exists()), reason="es4xw not built")
needs_text_build = pytest.mark.skipif(
    not (BUILT.exists() and TEXT_BUILT.exists()), reason="text build retired or not built"
)

CAPTION = (
    "A large company recently formed a management team to lead a new project. You don't "
    "know any of them personally, but the company included pictures of the management "
    "team when it sent out an announcement about the project (see above)."
)
FACTORS = {
    1: {"black_member_present": "present", "asian_member_present": "absent"},
    2: {"black_member_present": "absent", "asian_member_present": "present"},
    3: {"black_member_present": "present", "asian_member_present": "present"},
    4: {"black_member_present": "absent", "asian_member_present": "absent"},
}


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
def test_each_picture_is_the_one_under_its_directive() -> None:
    assert gen.docx_pictures() == {n: f"word/media/image{n}.png" for n in (1, 2, 3, 4)}
    for n, data in gen.picture_bytes().items():
        assert (RAW / "images" / f"picture{n}.png").read_bytes() == data, n


@needs_raw
def test_two_of_six_photographs_vary_and_picture_3_recombines() -> None:
    dist = gen.slot_distances()
    gen.check_slots(dist)  # raises on any departure
    tm, bl = dist["top-middle"], dist["bottom-left"]
    assert tm[1, 2] < gen.SAME and bl[0, 2] < gen.SAME  # 3 = 2's top-middle, 1's bottom-left
    for slot in ("top-left", "top-right", "bottom-middle", "bottom-right"):
        assert dist[slot].max() < gen.SAME, slot


@needs_raw
def test_the_slot_check_catches_a_swapped_picture() -> None:
    pics = gen.picture_bytes()
    swapped = {1: pics[3], 2: pics[2], 3: pics[1], 4: pics[4]}
    with pytest.raises(SystemExit):
        gen.check_slots(gen.slot_distances(swapped))


def test_png_decoder_reads_a_tiny_palette_image() -> None:
    import struct
    import zlib

    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + b"\0\0\0\0"

    ihdr = struct.pack(">IIBBBBB", 2, 2, 8, 3, 0, 0, 0)
    plte = bytes([0, 0, 0, 255, 0, 0])
    # filter 0 then filter 1 (sub): second row decodes to [1, 1]
    raw = bytes([0, 0, 1, 1, 1, 0])
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"PLTE", plte)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )
    img = gen.decode_png(png)
    assert img.shape == (2, 2, 3)
    assert img[0, 0].tolist() == [0, 0, 0] and img[0, 1].tolist() == [255, 0, 0]
    assert img[1].tolist() == [[255, 0, 0], [255, 0, 0]]


@needs_raw
def test_caption_is_word_for_word_in_both_copies_of_q() -> None:
    assert gen.caption() == CAPTION


def test_each_arm_is_its_picture_then_the_caption() -> None:
    rec = load(RECIPE)
    assert rec.condition.shared_context is None
    assert sorted(a.raw or 0 for a in rec.condition.arms) == [1, 2, 3, 4]
    for arm in rec.condition.arms:
        assert arm.raw is not None
        assert arm.condition_num == arm.raw - 1
        assert arm.images == [f"es4xw_picture{arm.raw}"]
        assert arm.factors == FACTORS[arm.raw]
        assert rec.condition.render(arm) == f"<image> {CAPTION}"
        assert arm.text.count(images_mod.IMAGE_MARKER) == 1


# Words neither the condition nor a description may use: the pictures ARE the
# manipulation of the team's racial make-up, so nothing we write may state it.
FORBIDDEN = (
    r"\b(black|white|asian|african|american|caucasian|hispanic|latino|latina|race|racial|"
    r"ethnic\w*|skin|dark-skinned|light-skinned|man|men|woman|women|male|female|he|she|"
    r"his|her|him|young|old|older|younger|aged?|middle-aged|smil\w*|happy|friendly|"
    r"attractive|bald|minority|diverse|diversity)\b"
)
# Colour words that ARE allowed in a description, because they name clothing or the
# backdrop and are followed by what they describe.
ALLOWED_COLOUR = re.compile(r"\bwhite (open-collared|shirt|lines|top|dots)\b|\bsmall white dots\b")


def _offending(text: str) -> list[str]:
    return re.findall(FORBIDDEN, ALLOWED_COLOUR.sub("", text.lower()))


def test_the_forbidden_words_check_catches_and_passes() -> None:
    assert _offending("Two Black men and four White people.") == ["black", "men", "white"]
    assert _offending("An Asian woman, smiling.") == ["asian", "woman", "smiling"]
    assert _offending("A white man in a white shirt.") == ["white", "man"]
    # what it must not catch: clothing colours, "the", "shoulders", "three"
    assert _offending("The head and shoulders; a white shirt and thin white lines; three") == []


def test_descriptions_name_no_race_gender_or_age() -> None:
    for n, text in gen.DESCRIPTIONS.items():
        assert not _offending(text), (n, _offending(text))
        assert text.endswith("No words.")


def test_condition_names_no_race() -> None:
    rec = load(RECIPE)
    for arm in rec.condition.arms:
        assert not _offending(rec.condition.render(arm)), arm.raw


def test_descriptions_differ_only_where_the_pictures_do() -> None:
    sentences = {n: d.split(". ") for n, d in gen.DESCRIPTIONS.items()}
    for i, parts in enumerate(zip(*sentences.values(), strict=True)):
        if len(set(parts)) > 1:
            assert parts[0].startswith(("Top row, middle", "Bottom row, left")), i
    assert gen.DESCRIPTIONS[1] != gen.DESCRIPTIONS[3] != gen.DESCRIPTIONS[2]


@needs_raw
def test_the_composition_factors_follow_the_data() -> None:
    means = gen.diversity_means()
    gen.check_composition(means)
    # and the check fails if pictures 1 and 2 were the other way round
    swapped = {e: {**m, 1: m[2], 2: m[1]} for e, m in means.items()}
    with pytest.raises(SystemExit):
        gen.check_composition(swapped)


@needs_raw
def test_outcome_statements_are_word_for_word() -> None:
    rec = load(RECIPE)
    stmts = gen.statements()
    assert [o.var for o in rec.outcomes] == [f"Q{i}" for i in range(1, 14)]
    for o in rec.outcomes:
        assert o.question == f'Please rate the following statement: "{stmts[o.var]}"'
    assert stmts["Q5"] == "This group would listen to everyone's views and opinions."
    assert gen.grid_directives()["Q10"] == "[GRID - SP]"


@needs_built
def test_every_person_sees_one_picture() -> None:
    rows = pd.read_parquet(BUILT)
    assert len(rows) == 32_228
    per = rows.groupby("participant_id")["condition_num"].nunique()
    assert len(per) == 2_501 and (per == 1).all()
    assert rows["condition_num"].value_counts().to_dict() == {0: 8131, 1: 8246, 2: 8049, 3: 7802}
    images = rows.groupby("condition_num")["condition_images"].first().map(list)
    assert images.to_dict() == {n - 1: [f"es4xw_picture{n}"] for n in (1, 2, 3, 4)}
    assert set(rows["condition"]) == {f"<image> {CAPTION}"}


@needs_text_build
def test_rows_equal_the_text_build_but_for_the_condition() -> None:
    img = pd.read_parquet(BUILT)
    txt = pd.read_parquet(TEXT_BUILT)
    assert len(img) == len(txt)
    for col in txt.columns:
        if col == "condition":
            continue
        a = img[col].map(lambda v: repr(v.tolist() if isinstance(v, np.ndarray) else v))
        b = txt[col].map(lambda v: repr(v.tolist() if isinstance(v, np.ndarray) else v))
        assert (a.values == b.values).all(), col
    assert not (img["condition"].values == txt["condition"].values).any()


@needs_built
def test_built_parquet_is_current(tmp_path: Path) -> None:
    """The answer-key tests read the parquet on disk, so a stale build would let a
    generator change (e.g. two pictures swapped between arms) pass them unseen.
    Rebuild from the current recipe in memory and require the same rows."""
    from micromotives_datasets import cli

    rec, rows, _ = cli._load_and_build(RECIPE)
    fresh = pd.read_parquet(cli._write_parquet(rows, tmp_path, rec))
    on_disk = pd.read_parquet(BUILT)
    assert fresh.equals(on_disk), "es4xw.parquet is stale: rebuild with mmds build"
