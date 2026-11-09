"""The mkgvp recipe (TESS 1126, Headley: a burglary to report, then a police building seen
from a distance and close up) and its answer key.

The generator reads the vignette, the picture directives and every outcome's words out of
the fielded questionnaire (.docx, in document order), and copies the twelve photographs
out of the same file; these tests stop a hand edit drifting from it, and check the facts
the rows rest on:

- each arm shows the questionnaire's [SHOW IF P_HEADLEY=n] picture on each of the two
  screens, byte for byte, and each picture's alt text names the client's file for the
  same arm and view; the question screens repeat the close-up;
- the six buildings read the same words within each order, so the design is carried by
  the pictures alone, and neither the text nor our descriptions say "hostile" or
  "welcoming";
- for RND_01 = 0 (the police questions first) the condition narrates that block, quoting
  only its wording and never an answer option, and is otherwise the RND_01 = 1 text;
- every painted-over rectangle is recorded in both the transcription and the description;
- the built rows reproduce SocSci210 (fetched 9 Nov 2026 by `mmds build --crosscheck`
  and transcribed here): 8,690 rows, 732 people, and the same response counts in every
  cell of THEIR two conditions by three tasks once our rows are grouped by our `order`
  factor (RND_01), which is the variable SocSci210 used as the condition. Grouped by the
  real assignment's hostile / welcoming halves, the cells do not match: SocSci210
  attached the building type to the wrong half of the sample.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import json
import re
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load
from micromotives_datasets.sources import read_any

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_mkgvp.py"
RECIPE = REPO / "recipes" / "images" / "mkgvp.yaml"
RAW = REPO / "data" / "raw" / "mkgvp"
DTA = RAW / "8041.050_TESS 050 Headley.dta"
BUILT = REPO / "data" / "processed" / "images" / "mkgvp.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_mkgvp", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not DTA.exists(), reason="mkgvp deposit not fetched")
needs_built = pytest.mark.skipif(not (BUILT.exists() and DTA.exists()), reason="mkgvp not built")

# Read by hand from word/document.xml: the media file under each [SHOW IF P_HEADLEY=n].
MEDIA = {
    1: ("word/media/image3.png", "word/media/image9.jpeg"),
    2: ("word/media/image4.png", "word/media/image10.png"),
    3: ("word/media/image5.jpeg", "word/media/image11.png"),
    4: ("word/media/image6.png", "word/media/image12.png"),
    5: ("word/media/image7.jpeg", "word/media/image13.jpeg"),
    6: ("word/media/image8.jpeg", "word/media/image14.png"),
}
ARM_COUNTS = {1: 126, 2: 121, 3: 120, 4: 127, 5: 117, 6: 121}
ORDER_COUNTS = {0: 358, 1: 374}
CLOSER = "You are now closer to approaching the police department."

# SocSci210, study mkgvp (9 Nov 2026): response counts per (their condition_num, their
# task_num). Their tasks are Q1 (nine items), Q2 (two) and Q3; their condition 0 is
# described as a hostile/defensive building and 1 as a welcoming one.
SOCSCI210_ROWS = 8_690
SOCSCI210_PEOPLE = 732
SOCSCI210_CELLS = {
    (0, 0): {1: 628, 2: 596, 3: 644, 4: 539, 5: 780},
    (0, 1): {1: 230, 2: 273, 3: 144, 4: 45, 5: 23},
    (0, 2): {1: 221, 2: 79, 3: 33, 4: 12, 5: 13},
    (1, 0): {1: 592, 2: 647, 3: 663, 4: 523, 5: 884},
    (1, 1): {1: 257, 2: 272, 3: 148, 4: 53, 5: 17},
    (1, 2): {1: 230, 2: 77, 3: 39, 4: 14, 5: 14},
}
REDACTED = {"p3_closeup", "p4_closeup", "p6_distance", "p6_closeup"}


@needs_raw
def test_recipe_is_what_the_generator_writes() -> None:
    assert RECIPE.read_text() == gen.render()


@needs_raw
def test_catalogue_entries_are_what_the_generator_derives() -> None:
    cat = images_mod.load()
    entries = gen.catalogue_entries()
    assert len(entries) == 12
    for image_id, entry in entries.items():
        assert cat[image_id].model_dump() == entry, image_id
        assert not images_mod.problems(image_id, cat), image_id


@needs_raw
def test_each_arm_gets_its_show_if_picture_on_both_screens() -> None:
    pics = gen.instrument()["pictures"]
    assert {c: (pics["HEADLEY1A"][c], pics["HEADLEY2"][c]) for c in range(1, 7)} == MEDIA
    with zipfile.ZipFile(gen.QUEX) as z:
        for code, members in MEDIA.items():
            for view, member in zip(("distance", "closeup"), members, strict=True):
                key = gen.image_key(code, view)
                assert (REPO / "data" / gen.image_file(key, member)).read_bytes() == z.read(
                    member
                ), key


@needs_raw
def test_question_screens_repeat_the_closeup() -> None:
    sc = gen.screens()
    close = gen.picture_map(sc["HEADLEY2"])
    for q in ("Q1", "Q2", "Q3"):
        assert gen.picture_map(sc[q]) == close, q
    # the attitude block shows no picture
    for q in ("HEADLEY3", "Q4", "Q5", "Q6", "Q7"):
        assert not any(p["pics"] for p in sc[q]), q


@needs_raw
def test_alt_text_names_the_same_arm_and_view() -> None:
    sc = gen.screens()
    for screen, view in (("HEADLEY1A", "distance"), ("HEADLEY2", "closeup")):
        for code, (_, alt) in gen.picture_map(sc[screen]).items():
            assert gen._alt_file(alt).rsplit(".", 1)[0] == gen.expected_alt(code, view)
    assert gen.expected_alt(2, "closeup") == "Image 2 hostile police building 2 closeup"
    assert gen.expected_alt(5, "distance") == "Image 5 welcoming police building 2"


VIGNETTE_START = "Please imagine being in the following hypothetical scenario"
TAIL = f"You now see the police department from a distance. <image> {CLOSER} <image>"
ORDER = {0: "police questions first", 1: "police questions after"}


def test_each_arm_shows_its_two_photos_around_the_same_words() -> None:
    rec = load(RECIPE)
    assert rec.condition.source_vars == ["P_HEADLEY", "RND_01"]
    assert not rec.condition.shared_context
    seen = set()
    for arm in rec.condition.arms:
        assert arm.raw_values is not None
        code, rnd = arm.raw_values["P_HEADLEY"], arm.raw_values["RND_01"]
        seen.add((code, rnd))
        assert arm.condition_num == 6 * rnd + code - 1
        assert arm.images == [f"mkgvp_p{code}_distance", f"mkgvp_p{code}_closeup"]
        assert arm.text.count(images_mod.IMAGE_MARKER) == len(arm.images)
        assert arm.text.endswith(TAIL)
        design = "hostile defensive" if code <= 3 else "welcoming"
        assert arm.factors == {
            "design": design,
            "building": str((code - 1) % 3 + 1),
            "order": ORDER[rnd],
        }
    assert seen == {(c, r) for c in range(1, 7) for r in (0, 1)}
    texts = {
        r: {a.text for a in rec.condition.arms if a.factors["order"] == ORDER[r]} for r in (0, 1)
    }
    assert all(len(t) == 1 for t in texts.values())  # one wording per order
    (later,), (first,) = texts[1], texts[0]
    assert later.startswith(VIGNETTE_START)
    assert first.endswith(" " + later) and first.startswith("You were first shown:")


# What the RND_01 = 0 narration may contain beyond the instrument's quoted words.
OURS = (
    "You were first shown:",
    "You were then asked:",
    "for each of nine statements, shown in random order:",
    "After that:",
)
ANSWERS = (
    "Strongly agree",
    "Somewhat agree",
    "Neither agree nor disagree",
    "Somewhat disagree",
    "Strongly disagree",
    "Very satisfied",
    "Somewhat satisfied",
    "Neither satisfied nor dissatisfied",
    "Somewhat dissatisfied",
    "Very dissatisfied",
    "Not applicable",
)


def _unquoted(text: str) -> str:
    """The narration's own words: the quoted instrument wording removed."""
    return re.sub(r'"[^"]*"', "", text)


@needs_raw
def test_the_order_narration_quotes_the_block_and_adds_only_our_joins() -> None:
    q = gen.instrument()
    narration = gen.narration(q)
    quoted = re.findall(r'"([^"]*)"', narration)
    assert quoted == [*q["headley3"], q["q4_stem"], *q["q4_items"], q["q5"]]
    assert (
        quoted[0] == "We're going to ask you about your perceptions of the criminal justice system."
    )
    assert len(q["q4_items"]) == 9
    rest = _unquoted(narration)
    for phrase in OURS:
        rest = rest.replace(phrase, "")
    assert rest.strip() == ""
    assert not any(a.lower() in narration.lower() for a in ANSWERS)
    # every added phrase is recorded word-for-word in the recipe's notes
    notes = re.sub(r"\s+", " ", load(RECIPE).notes or "")
    assert all(f'"{phrase}"' in notes for phrase in OURS)


def test_the_unquoted_check_catches_and_passes() -> None:
    assert (
        _unquoted('You were shown: "a b" and "c". After that:')
        == "You were shown:  and . After that:"
    )
    assert _unquoted("no quotes here") == "no quotes here"


# Words neither the condition nor our descriptions may use: the study asks people how a
# building makes them feel, so our account of the picture must not answer for them.
JUDGING = (
    r"\b(hostile|defensive|welcoming|inviting|imposing|intimidating|threatening|friendly|"
    r"forbidding|fortress\w*|prison\w*|bunker\w*|brutalist|grim|bleak|stark|austere|"
    r"cold|warm|open|closed|safe|unsafe|attractive|ugly|beautiful|pleasant|modern|old|dated)\b"
)


def _judging(text: str) -> list[str]:
    return re.findall(JUDGING, text.lower())


def test_the_judging_words_check_catches_and_passes() -> None:
    assert _judging("An imposing, hostile concrete fortress.") == [
        "imposing",
        "hostile",
        "fortress",
    ]
    assert _judging("A warm and welcoming modern building.") == ["warm", "welcoming", "modern"]
    # what it must not catch: words that merely contain them
    assert _judging("Pale panels; a coldframe; oldest; opening; safety rail; openings") == []


def test_descriptions_and_conditions_do_not_judge_the_building() -> None:
    for key, text in gen.DESCRIPTIONS.items():
        assert not _judging(text), (key, _judging(text))
    rec = load(RECIPE)
    for arm in rec.condition.arms:
        assert not _judging(_unquoted(rec.condition.render(arm))), arm.condition_num


def test_every_painted_rectangle_is_recorded() -> None:
    assert (
        set(gen.TEXT_IN_IMAGE)
        == set(gen.DESCRIPTIONS)
        == {gen.image_key(c, v) for c in range(1, 7) for v in ("distance", "closeup")}
    )
    for key in gen.DESCRIPTIONS:
        said = "rectangle" in gen.DESCRIPTIONS[key]
        transcribed = "rectangle" in gen.TEXT_IN_IMAGE[key]
        assert said == transcribed == (key in REDACTED), key


@needs_built
def test_every_person_sees_one_condition() -> None:
    rows = pd.read_parquet(BUILT)
    per = rows.groupby("participant_id")["condition_num"].nunique()
    assert len(per) == SOCSCI210_PEOPLE and (per == 1).all()
    by_cond = rows.groupby("condition_num")["participant_id"].nunique()
    buildings = by_cond.groupby(by_cond.index % 6).sum().to_dict()
    assert {c + 1: n for c, n in buildings.items()} == ARM_COUNTS
    assert by_cond.groupby(by_cond.index // 6).sum().to_dict() == ORDER_COUNTS
    images = rows.groupby("condition_num")["condition_images"].first().map(list).to_dict()
    assert images == {
        6 * r + c - 1: [f"mkgvp_p{c}_distance", f"mkgvp_p{c}_closeup"]
        for c in MEDIA
        for r in (0, 1)
    }
    # each person's condition is their own P_HEADLEY and RND_01
    df = read_any(DTA).df
    ids = "mkgvp:" + df["CaseId"].astype(int).astype(str)
    want = dict(
        zip(ids, 6 * df["RND_01"].astype(int) + df["P_HEADLEY"].astype(int) - 1, strict=True)
    )
    got = rows.groupby("participant_id")["condition_num"].first()
    assert (got == got.index.map(want)).all()
    narrated = rows["condition"].str.startswith("You were first shown:")
    assert (narrated == (rows["condition_num"] < 6)).all()


def _cells(rows: pd.DataFrame, by: pd.Series) -> dict[tuple[int, int], dict[int, int]]:
    """Response counts per (grouping, SocSci210 task): Q1 items 0-8, Q2 9-10, Q3 11."""
    task = rows["task_num"].map(lambda t: 0 if t < 9 else 1 if t < 11 else 2)
    key = rows["participant_id"].map(by)
    out: dict[tuple[int, int], dict[int, int]] = {}
    for (k, t), g in rows.groupby([key, task]):
        counts = g["response_num"].astype(int).value_counts().sort_index()
        out[(int(k), int(t))] = {int(r): int(n) for r, n in counts.items()}
    return out


@needs_built
def test_rows_reproduce_socsci210_once_grouped_by_their_condition() -> None:
    rows = pd.read_parquet(BUILT)
    assert len(rows) == SOCSCI210_ROWS
    assert rows["participant_id"].nunique() == SOCSCI210_PEOPLE
    first = rows.groupby("participant_id")["condition_num"].first()
    order = pd.Series(first // 6)  # our `order` factor, RND_01
    design = pd.Series((first % 6 >= 3).astype(int))  # hostile 0, welcoming 1
    assert _cells(rows, order) == SOCSCI210_CELLS
    # and their condition is not the building type: the hostile / welcoming halves differ
    assert _cells(rows, design) != SOCSCI210_CELLS


@needs_built
def test_persona_labels_are_restored() -> None:
    rows = pd.read_parquet(BUILT)
    personas = [json.loads(p) for p in rows["persona"].unique()]
    ideologies = {p.get("ideology") for p in personas}
    assert "Liberal" in ideologies and "Libreal" not in ideologies
    religions = {p.get("religion") for p in personas}
    assert not any(r and r.endswith("Pent") for r in religions)


@needs_built
def test_built_parquet_is_current(tmp_path: Path) -> None:
    """The answer-key tests read the parquet on disk, so a stale build would let a
    generator change (e.g. two photos swapped between arms) pass them unseen.
    Rebuild from the current recipe in memory and require the same rows."""
    from micromotives_datasets import cli

    rec, rows, _ = cli._load_and_build(RECIPE)
    fresh = pd.read_parquet(cli._write_parquet(rows, tmp_path, rec))
    on_disk = pd.read_parquet(BUILT)
    assert fresh.equals(on_disk), "mkgvp.parquet is stale: rebuild with mmds build"
