"""4zscf's words against its fielded questionnaire, and its built rows against an
independent reading of the deposit (TESS3 192, Mize: categorising sexual
orientation after a casual encounter that departs from a sexual history).

The questionnaire is an omnibus of three TESS studies; only the "TESS192 SURVEY
(MIZE)" block is read. Every word the recipe renders, other than the one added
"Report only the percentage for ..." sentence that docs/CONVENTIONS.md permits for
a screen of several labelled boxes, must sit in that block, under the right
display or question.

The numeric answer key is SocSci210 (`mmds build --crosscheck`, which passed on
all six fields). This file adds what the crosscheck cannot see: every (person,
condition, task, response) tuple, recomputed here from the .sav with pyreadstat
rather than through the pipeline, and the twelve cell counts and means, which
were read from SocSci210's parquet and from the .sav before the recipe existed
and agree to three decimals.

Tests needing the gitignored deposit or build skip on a fresh clone. No test
prints a row: failures compare sizes and aggregates only.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

import pandas as pd
import pyreadstat
import pytest

from micromotives_datasets.recipe import Recipe, load

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "4zscf"
SAV = RAW / "Tess192_Mize_Client.sav"
DOCX = RAW / "TESS185Johnston_TESS189Giner-Sorolla_TESS192Mize_v2clean.docx"
BUILT = REPO / "data" / "processed" / "4zscf.parquet"
RECIPE = REPO / "recipes" / "4zscf.yaml"

needs_raw = pytest.mark.skipif(not (SAV.exists() and DOCX.exists()), reason="4zscf not fetched")
needs_built = pytest.mark.skipif(not (BUILT.exists() and SAV.exists()), reason="4zscf not built")

ADDED = re.compile(r'^Report only the percentage for "([^"]+)"\.$')
DISPLAY = {1: "A", 2: "B", 3: "C", 4: "D"}
QUESTION_OF_RAW = {1: "Q1", 2: "Q1", 3: "Q2", 4: "Q2"}
BOX = {0: "A", 1: "B", 2: "C"}

# (condition_num, task) -> (answers, mean), read from SocSci210's parquet and,
# independently, from the .sav, before the recipe was written (2026-11-24).
CELLS = {
    (0, 0): (521, 31.455),
    (0, 1): (521, 24.217),
    (0, 2): (532, 50.555),
    (1, 0): (463, 8.641),
    (1, 1): (464, 47.121),
    (1, 2): (472, 49.900),
    (2, 0): (474, 51.129),
    (2, 1): (471, 15.176),
    (2, 2): (474, 41.086),
    (3, 0): (513, 11.747),
    (3, 1): (517, 40.959),
    (3, 2): (524, 53.567),
}


def _norm(s: str) -> str:
    """Collapse whitespace (non-breaking spaces and U+2028 included)."""
    return " ".join(s.replace("\xa0", " ").replace(" ", " ").split())


def mize_block() -> str:
    """Mize's block of the .docx, one paragraph per line, tabs and breaks kept."""
    xml = zipfile.ZipFile(DOCX).read("word/document.xml").decode("utf-8")
    xml = xml.replace("<w:tab/>", "\t").replace("<w:br/>", "\n")
    text = "\n".join(re.sub(r"<[^>]+>", "", p) for p in re.split(r"</w:p>", xml))
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"')):
        text = text.replace(a, b)
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    start = text.index("TESS192 SURVEY (MIZE)")
    end = text.index("PARTY7", start)
    return text[start:end]


def question_segment(block: str, q: str) -> str:
    """From "Q1." / "Q2." to the next question or the end of the block."""
    start = block.index(f"{q}. ")
    nxt = block.find("Q2. ", start + 4) if q == "Q1" else -1
    return block[start : nxt if nxt > 0 else len(block)]


@pytest.fixture(scope="module")
def rec() -> Recipe:
    return load(RECIPE)


@needs_raw
def test_shared_context_and_each_story_sit_under_their_own_display(rec: Recipe) -> None:
    block = mize_block()
    assert rec.condition.shared_context is not None
    intro = block.split("[DISPAA]", 1)[1].split("DOV_TESS192 =1", 1)[0]
    assert _norm(rec.condition.shared_context) == _norm(intro)
    for arm in rec.condition.arms:
        assert arm.raw is not None
        letter = DISPLAY[arm.raw]
        head = f"DOV_TESS192 ={arm.raw}\n[DISPLAY{letter}]\n"
        story = block.split(head, 1)[1].split("\n\n", 1)[0]
        assert _norm(arm.text) == _norm(story), arm.raw


def _questions(rec: Recipe, raw: int) -> dict[int, tuple[str, str]]:
    """task -> (variable, question) for one arm, after its item overrides."""
    arm = next(a for a in rec.condition.arms if a.raw == raw)
    out = {}
    for o in rec.outcomes:
        item = arm.items.get(o.task_num)
        var = (item.outcome_var if item and item.outcome_var else None) or o.var
        question = (item.outcome_question if item and item.outcome_question else None) or o.question
        assert var is not None
        out[o.task_num] = (var, question)
    return out


@needs_raw
@pytest.mark.parametrize("raw", [1, 2, 3, 4])
def test_every_outcome_word_is_on_its_own_question_screen(rec: Recipe, raw: int) -> None:
    q = QUESTION_OF_RAW[raw]
    seg = question_segment(mize_block(), q)
    labels_on_screen = {
        m.group(1): m.group(2).strip()
        for m in re.finditer(r"(?m)^([ABC])=([^\t\n]+?)\s*\t*\[NUMBER BOX 0-100\]", seg)
    }
    assert set(labels_on_screen) == {"A", "B", "C"}
    stem_line = seg.split("\n", 1)[0][len(f"{q}. ") :]
    instruction = re.search(r"\(Please indicate[^\n]+\)\.", seg)
    assert instruction is not None
    for task, (var, question) in _questions(rec, raw).items():
        lines = question.split("\n")
        assert len(lines) == 6, (raw, task)
        stem, instr, a, b, c, added = lines
        assert stem == _norm(stem_line)
        assert instr == _norm(instruction.group(0))
        assert [a, b, c] == [labels_on_screen[k] for k in "ABC"]
        # the added sentence names THIS task's own box, quoted from the screen
        m = ADDED.match(added)
        assert m is not None, added
        assert m.group(1) == labels_on_screen[BOX[task]]
        # and the answer comes from that box's variable on that question
        assert var == f"{q}_{BOX[task]}"


@needs_raw
def test_middle_box_is_gay_for_michael_and_gay_lesbian_for_emily(rec: Recipe) -> None:
    assert _questions(rec, 1)[1][1].endswith('"Gay".')
    assert _questions(rec, 3)[1][1].endswith('"Gay/Lesbian".')
    block = mize_block()
    assert re.search(r"(?m)^B=Gay\s*\t", question_segment(block, "Q1"))
    assert re.search(r"(?m)^B=Gay/Lesbian\t", question_segment(block, "Q2"))


def _deposit() -> pd.DataFrame:
    df, _ = pyreadstat.read_sav(str(SAV))
    return df


@needs_raw
def test_routing_puts_q1_on_displays_a_b_and_q2_on_c_d() -> None:
    df = _deposit()
    assert df.DOV_TESS192.value_counts().sort_index().tolist() == [545, 477, 482, 531]
    for box in "ABC":
        q1 = df.groupby("DOV_TESS192")[f"Q1_{box}"].count().to_dict()
        q2 = df.groupby("DOV_TESS192")[f"Q2_{box}"].count().to_dict()
        assert q1 == {1.0: 545, 2.0: 477, 3.0: 0, 4.0: 0}
        assert q2 == {1.0: 0, 2.0: 0, 3.0: 482, 4.0: 531}


def _expected() -> set[tuple[str, int, int, int]]:
    df = _deposit()
    out = set()
    # TESS ids are the row index (no participant_id_var), as every TESS build.
    for idx, r in df.iterrows():
        raw = int(r.DOV_TESS192)
        q = QUESTION_OF_RAW[raw]
        for task, box in BOX.items():
            v = r[f"{q}_{box}"]
            if pd.isna(v) or v == -1:
                continue
            assert 0 <= v <= 100 and v == int(v)
            out.add((f"4zscf:{idx}", raw - 1, task, int(v)))
    return out


@needs_built
def test_built_rows_are_the_deposit_answers_exactly() -> None:
    b = pd.read_parquet(BUILT)
    got = set(
        zip(
            b.participant_id,
            b.condition_num.astype(int),
            b.task_num.astype(int),
            b.response_num.astype(int),
            strict=True,
        )
    )
    expected = _expected()
    assert len(got) == len(b) == 5946
    assert b.participant_id.nunique() == 2013
    # Compare sizes, not the sets themselves: a failure must not print rows.
    assert len(got - expected) == 0 and len(expected - got) == 0


@needs_built
def test_cell_counts_and_means() -> None:
    b = pd.read_parquet(BUILT)
    for (cond, task), (n, mean) in CELLS.items():
        g = b[(b.condition_num == cond) & (b.task_num == task)]
        assert len(g) == n, (cond, task)
        assert round(float(g.response_num.mean()), 3) == mean, (cond, task)


@needs_built
def test_each_cell_renders_one_condition_and_one_outcome_naming_its_own_target() -> None:
    b = pd.read_parquet(BUILT)
    per = b.groupby(["condition_num", "task_num"]).agg(
        c=("condition", "nunique"), o=("outcome", "nunique")
    )
    assert int(per.c.max()) == 1 and int(per.o.max()) == 1
    for cond, name in ((0, "Michael"), (1, "Michael"), (2, "Emily"), (3, "Emily")):
        g = b[b.condition_num == cond]
        assert g.outcome.str.startswith(f"How likely to do you think {name} is:").all()
        assert g.condition.str.contains(f"{name} is currently single").all()
