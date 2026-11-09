"""The 3xy9j recipe (TESS3 133, Chiong: a stroke or a cardiac arrest, its treatment's
outcomes for 100 people as an icon chart, asked as a choice or without consent) and
its answer key.

The generator reads every word of the condition and question out of the fielded
questionnaire (.docx, asserting its .txt copy has the same words) and the two charts
out of the same .docx; these tests stop a hand edit drifting from it, and check the
facts the rows rest on:

- each scenario screen embeds its scenario's chart (document.xml, in order), and the
  catalogued file is that picture byte for byte;
- the figures of each colour, counted from the file, equal the numbers the paragraph
  under the chart prints, and our description states the same counts and positions;
  the counter is shown to notice a recoloured figure, and not to be fooled by the
  other chart;
- the without-consent sentence is in the condition of exactly the two arms that saw
  it, and each arm asks its own question from its own variable;
- the seven statements of screen 3 (tasks 1-7) carry the arm's scenario and its
  question narrated as asked, never as answered, and nothing later;
- the built rows reproduce SocSci210's tasks 0-7, cell for cell (condition, task,
  response), fetched 9 Nov 2026 from its parquet shards and transcribed here. Its
  tasks 8-11 (Q9-Q12, health status and history) are not built.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import json
import re
import struct
import zipfile
import zlib
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_3xy9j.py"
RECIPE = REPO / "recipes" / "images" / "3xy9j.yaml"
RAW = REPO / "data" / "raw" / "3xy9j"
SAV = RAW / "TESS133 - Chiong - Final Deliverables" / "TESS3133_Chiong_Client_Final Data.sav"
BUILT = REPO / "data" / "processed" / "images" / "3xy9j.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_3xy9j", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not SAV.exists(), reason="3xy9j deposit not fetched")
needs_built = pytest.mark.skipif(not (BUILT.exists() and SAV.exists()), reason="3xy9j not built")

# SocSci210, study 3xy9j, tasks 0-7, as {(condition_num, task_num): {response: rows}}.
# Its condition_num is XTESS133 - 1 and its task_num our order, as ours. Its task 0 is
# the scenario question; 1-7 are Q2-Q8.
SOCSCI210_CELLS: dict[tuple[int, int], dict[int, int]] = {
    (0, 0): {1: 145, 2: 274, 3: 90, 4: 27},
    (1, 0): {1: 175, 2: 249, 3: 74, 4: 28},
    (2, 0): {1: 231, 2: 191, 3: 89, 4: 37},
    (3, 0): {1: 263, 2: 171, 3: 49, 4: 29},
    (0, 1): {1: 93, 2: 121, 3: 98, 4: 60, 5: 73, 6: 93},
    (0, 2): {1: 348, 2: 139, 3: 29, 4: 11, 5: 6, 6: 8},
    (0, 3): {1: 59, 2: 105, 3: 130, 4: 78, 5: 80, 6: 87},
    (0, 4): {1: 184, 2: 127, 3: 113, 4: 46, 5: 36, 6: 34},
    (0, 5): {1: 54, 2: 82, 3: 129, 4: 91, 5: 92, 6: 89},
    (0, 6): {1: 94, 2: 244, 3: 122, 4: 47, 5: 22, 6: 9},
    (0, 7): {1: 68, 2: 106, 3: 171, 4: 97, 5: 63, 6: 33},
    (1, 1): {1: 86, 2: 127, 3: 125, 4: 71, 5: 54, 6: 64},
    (1, 2): {1: 313, 2: 130, 3: 53, 4: 11, 5: 6, 6: 12},
    (1, 3): {1: 52, 2: 107, 3: 163, 4: 71, 5: 69, 6: 64},
    (1, 4): {1: 171, 2: 120, 3: 94, 4: 50, 5: 43, 6: 43},
    (1, 5): {1: 75, 2: 78, 3: 132, 4: 91, 5: 79, 6: 67},
    (1, 6): {1: 87, 2: 223, 3: 136, 4: 42, 5: 25, 6: 14},
    (1, 7): {1: 64, 2: 112, 3: 190, 4: 89, 5: 49, 6: 25},
    (2, 1): {1: 113, 2: 97, 3: 108, 4: 67, 5: 76, 6: 87},
    (2, 2): {1: 324, 2: 143, 3: 43, 4: 10, 5: 11, 6: 15},
    (2, 3): {1: 70, 2: 90, 3: 140, 4: 81, 5: 76, 6: 87},
    (2, 4): {1: 204, 2: 120, 3: 106, 4: 47, 5: 37, 6: 32},
    (2, 5): {1: 72, 2: 67, 3: 119, 4: 90, 5: 102, 6: 96},
    (2, 6): {1: 120, 2: 200, 3: 132, 4: 39, 5: 33, 6: 20},
    (2, 7): {1: 98, 2: 137, 3: 156, 4: 69, 5: 58, 6: 27},
    (3, 1): {1: 93, 2: 96, 3: 99, 4: 66, 5: 75, 6: 86},
    (3, 2): {1: 332, 2: 124, 3: 29, 4: 10, 5: 4, 6: 14},
    (3, 3): {1: 49, 2: 104, 3: 111, 4: 88, 5: 78, 6: 84},
    (3, 4): {1: 150, 2: 133, 3: 99, 4: 47, 5: 46, 6: 37},
    (3, 5): {1: 58, 2: 72, 3: 128, 4: 99, 5: 87, 6: 68},
    (3, 6): {1: 103, 2: 220, 3: 109, 4: 47, 5: 29, 6: 4},
    (3, 7): {1: 74, 2: 121, 3: 178, 4: 72, 5: 48, 6: 19},
}
SOCSCI210_PEOPLE_TASKS_0_7 = 2135
SOCSCI210_ROWS_ALL_TASKS = 25_482  # of which 8,503 are Q9-Q12, not built

# The two charts as our descriptions lay them out, row by row from the top:
# N normal or near normal (dark green), B better / disabled but independent (light
# green), W white (no change / dead), P pink, R dark red.
LAYOUT = {
    "stroke": [
        "NNNNNNNNNN",
        "BBBNNNBBBB",
        "BBBBBBBBBB",
        "WWWBBBWWWW",
        *["WWWWWWWWWW"] * 5,
        "WWWPRPWWWW",
    ],
    "cpr": [
        "NNNNNNNNNN",
        "NNBBBPRWWW",
        *["WWWWWWWWWW"] * 8,
    ],
}
LETTER = {
    "stroke": {
        "Normal or Near Normal": "N",
        "Better": "B",
        "No Change": "W",
        "Worse": "P",
        "Severely Disabled or Dead": "R",
    },
    "cpr": {
        "Normal or Near Normal": "N",
        "Disabled but Living Independently": "B",
        "Dead": "W",
        "Severely Disabled": "P",
        "Coma": "R",
    },
}


def _png(rows: list[bytes], w: int, h: int) -> bytes:
    """Encode RGBA rows as a PNG (filter 0), for the recolouring test."""

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    raw = b"".join(b"\x00" + r for r in rows)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


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
def test_each_screen_shows_its_scenarios_chart() -> None:
    # document.xml, in order: Q1a, Q1b show image2; Q1c, Q1d show image3; nothing else
    assert gen.body_pictures() == [
        "word/media/image2.png",
        "word/media/image2.png",
        "word/media/image3.png",
        "word/media/image3.png",
    ]
    q = gen.fielded()
    assert {c: s["chart"] for c, s in q.items()} == {
        1: "word/media/image2.png",
        2: "word/media/image2.png",
        3: "word/media/image3.png",
        4: "word/media/image3.png",
    }
    with zipfile.ZipFile(gen.DOCX) as z:
        assert (RAW / "images" / "stroke.png").read_bytes() == z.read("word/media/image2.png")
        assert (RAW / "images" / "cpr.png").read_bytes() == z.read("word/media/image3.png")


@needs_raw
def test_docx_and_txt_say_the_same_words() -> None:
    q = gen.instrument(gen.docx_paragraphs())
    qt = gen.instrument(gen.txt_paragraphs())
    for code in gen.GROUPS:
        assert {k: v for k, v in q[code].items() if k != "chart"} == {
            k: v for k, v in qt[code].items() if k != "chart"
        }
        assert qt[code]["chart"] is None


@needs_raw
@pytest.mark.parametrize("key", ["stroke", "cpr"])
def test_figures_match_the_printed_numbers_and_our_description(key: str) -> None:
    counts = gen.icon_counts(key)
    assert sum(counts.values()) == 100
    for label, (n, _) in gen.TEXT_COUNTS[key].items():
        assert counts[label] == n, label
    rest, n = gen.REMAINDER[key]
    assert counts[rest] == n
    # the layout, figure by figure
    grid = ["".join(LETTER[key][label] for label in row) for row in gen.icon_grid(key)]
    assert grid == LAYOUT[key]
    # and the description states every count against its legend label
    desc = gen.DESCRIPTIONS[key]
    for label, n in counts.items():
        assert re.search(rf'\b{n}\b[^.]*?\("{label}"\)|\("{label}", {n}\)', desc), label
    # the legend we transcribe is the legend we classify against
    assert gen.text_in_image(key).splitlines()[1:] == [lab for lab, _ in gen.LEGEND[key][1]]


@needs_raw
def test_the_counter_sees_a_recoloured_figure() -> None:
    """Paint the stroke chart's one dark red figure (bottom row, 5th) white: the count
    must move from "Severely Disabled or Dead" to "No Change"."""
    data = (RAW / "images" / "stroke.png").read_bytes()
    w, h, rows = gen.png_rgba(data)
    out = [bytearray(r) for r in rows]
    # the 5th column's run and the bottom band, generously
    for y in range(h - 55, h):
        for x in range(150, 186):
            p = out[y][4 * x : 4 * x + 4]
            if p[3] > 0 and p[0] < 150 and p[1] < 80:  # the dark red body
                out[y][4 * x : 4 * x + 4] = bytes([224, 224, 224, p[3]])
    counts = gen.icon_counts("stroke", _png([bytes(r) for r in out], w, h))
    assert counts["Severely Disabled or Dead"] == 0
    assert counts["No Change"] == 65
    # and the untouched file still reads as printed
    assert gen.icon_counts("stroke", data)["Severely Disabled or Dead"] == 1


@needs_raw
def test_the_counter_is_not_fooled_by_the_other_chart() -> None:
    cpr = (RAW / "images" / "cpr.png").read_bytes()
    # read with the stroke legend, the CPR chart cannot give the stroke numbers
    counts = gen.icon_counts("stroke", cpr)
    assert counts["Normal or Near Normal"] == 12
    assert counts["Better"] == 3
    assert counts != {
        "Normal or Near Normal": 13,
        "Better": 20,
        "No Change": 64,
        "Worse": 2,
        "Severely Disabled or Dead": 1,
    }


def test_each_arm_shows_its_scenario_chart_and_asks_its_own_question() -> None:
    rec = load(RECIPE)
    expected = {
        1: ("stroke", "hypothetical_choice", "Q1A", "3xy9j_stroke"),
        2: ("stroke", "without_consent", "Q1B", "3xy9j_stroke"),
        3: ("cardiac_arrest", "hypothetical_choice", "Q1C", "3xy9j_cpr"),
        4: ("cardiac_arrest", "without_consent", "Q1D", "3xy9j_cpr"),
    }
    assert sorted(a.raw or 0 for a in rec.condition.arms) == list(expected)
    for arm in rec.condition.arms:
        assert arm.raw is not None
        scenario, qtype, var, image = expected[arm.raw]
        assert arm.condition_num == arm.raw - 1
        assert arm.factors == {"scenario": scenario, "question_type": qtype}
        assert arm.outcome_var == var
        assert arm.images == [image]
        assert arm.text.count(images_mod.IMAGE_MARKER) == 1
        # the chart sits between the scenario and the paragraph that cites it
        before, after = arm.text.split(images_mod.IMAGE_MARKER)
        assert before.rstrip().endswith(("without the medicine.", "serious brain damage."))
        assert after.lstrip().startswith("This graphic shows")
        no_consent = "cannot communicate with you" in arm.text
        assert no_consent == (qtype == "without_consent"), arm.raw
        question = arm.outcome_question or ""
        if qtype == "without_consent":
            assert question.startswith("Even though the ")
            assert "not able to obtain your consent" in question
        else:
            assert question.startswith("Would you want treatment with ")
        assert ("CPR" in question) == (scenario == "cardiac_arrest")
        # the numbers the respondent read are the fielded ones, not the proposal's
        if scenario == "cardiac_arrest":
            assert "CPR would allow 12 people" in arm.text
            assert "5 people" not in arm.text
        else:
            assert "get better or worse on their own regardless" in arm.text
    context = rec.condition.shared_context or ""
    assert context.startswith("In medical emergencies, doctors and patients")
    assert not context.startswith("Q1")


def test_outcomes_are_the_scenario_question_and_the_seven_statements() -> None:
    rec = load(RECIPE)
    assert [o.task_num for o in rec.outcomes] == list(range(8))
    assert [o.var for o in rec.outcomes] == [None, "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"]
    assert rec.missing_codes == [-1]
    assert rec.response_recode == {1: 1, 2: 2, 3: 3, 4: 4}
    for o in rec.outcomes[1:]:
        assert (o.scale.min, o.scale.max) == (1, 6)
        assert (o.scale.min_label, o.scale.max_label) == ("Strongly agree", "Strongly disagree")
        assert o.response_recode == {i: i for i in range(1, 7)}
        assert o.question.startswith("We would also like to ask some questions about your")
        assert "1 (strongly agree) to 6 (strongly disagree)" in o.question
    assert rec.outcomes[1].question.endswith(
        "I prefer to rely upon my doctor's knowledge and not try to find out about my "
        "condition on my own."
    )
    assert rec.outcomes[7].question.endswith(
        "I do not believe in using statistics to make important life decisions."
    )
    # Q9-Q12 (health status and history) are facts, not outcomes
    assert not {"Q9", "Q10", "Q11", "Q12"} & {o.var for o in rec.outcomes}
    assert not rec.comparable_to_socsci210  # SocSci210 also built Q9-Q12; see notes


@needs_raw
def test_screen_3_is_read_the_same_from_docx_and_txt() -> None:
    grid = gen.attitude_grid(gen.docx_paragraphs())
    assert grid == gen.attitude_grid(gen.txt_paragraphs())
    assert [v for v, _ in grid["items"]] == ["Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"]


def test_statements_carry_the_scenario_and_its_question_asked_not_answered() -> None:
    rec = load(RECIPE)
    for arm in rec.condition.arms:
        task0 = rec.condition_text_for(rec.outcomes[0], arm)
        assert "You were asked" not in task0
        assert set(arm.items) == set(range(1, 8)), arm.raw
        for o in rec.outcomes[1:]:
            text = rec.condition_text_for(o, arm)
            # everything the scenario screen showed, then its question, and nothing else
            assert text == f'{task0} You were asked: "{arm.outcome_question}"', (arm.raw, o)
            assert text.count(images_mod.IMAGE_MARKER) == 1
            assert not re.search(r"\b(answer(ed)?|you said|you chose|replied)\b", text[-300:])
            # no later screen is named
            assert "We would also like" not in text


@needs_built
def test_every_person_sees_one_condition_and_its_chart() -> None:
    rows = pd.read_parquet(BUILT)
    per = rows.groupby("participant_id")["condition_num"].nunique()
    assert len(per) == SOCSCI210_PEOPLE_TASKS_0_7 and (per == 1).all()
    assert not rows.duplicated(["participant_id", "task_num"]).any()
    images = rows.groupby("condition_num")["condition_images"].first().map(list)
    assert images.to_dict() == {
        0: ["3xy9j_stroke"],
        1: ["3xy9j_stroke"],
        2: ["3xy9j_cpr"],
        3: ["3xy9j_cpr"],
    }


@needs_built
def test_rows_reproduce_socsci210_cell_for_cell() -> None:
    rows = pd.read_parquet(BUILT)
    assert len(rows) == sum(sum(d.values()) for d in SOCSCI210_CELLS.values()) == 16_979
    cells = zip(
        rows["condition_num"].astype(int),
        rows["task_num"].astype(int),
        rows["response_num"].astype(int),
        strict=True,
    )
    got: dict[tuple[int, int], dict[int, int]] = {}
    for c, t, k in cells:
        got.setdefault((c, t), {}).setdefault(k, 0)
        got[(c, t)][k] += 1
    assert got == SOCSCI210_CELLS


@needs_built
def test_persona_carries_no_refusal() -> None:
    rows = pd.read_parquet(BUILT)
    values = {
        v for p in rows["persona"].unique() for v in json.loads(p).values() if isinstance(v, str)
    }
    assert "Refused" not in values


@needs_built
def test_built_parquet_is_current(tmp_path: Path) -> None:
    """The answer-key tests read the parquet on disk, so a stale build would let a
    generator change (e.g. the two charts swapped between scenarios) pass them unseen.
    Rebuild from the current recipe in memory and require the same rows."""
    from micromotives_datasets import cli

    rec, rows, _ = cli._load_and_build(RECIPE)
    fresh = pd.read_parquet(cli._write_parquet(rows, tmp_path, rec))
    on_disk = pd.read_parquet(BUILT)
    assert fresh.equals(on_disk), "3xy9j.parquet is stale: rebuild with mmds build"
