"""h4k2t's words against its fielded questionnaire, and its built rows against an
independent reading of the deposit (TESS 125, Connors).

There is no SocSci210 build of this study and no published table, so the answer
key is recomputed here from the .dta with pyreadstat, not through the pipeline,
and compared with the BUILT parquet: every (person, condition, task, response)
tuple, and each (arm, task) cell's count and mean.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

import pandas as pd
import pyreadstat
import pytest

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "h4k2t"
DTA = RAW / "s3223_client_CONNORS.dta"
STEM = "TESS 124 Vora 125 Connors 133 Ollerenshaw Final"
PROG = RAW / f"{STEM} Programmed Questionnaire.docx"
SIMPLE = RAW / f"{STEM} Simple Questionnaire.docx"
BUILT = REPO / "data" / "processed" / "h4k2t.parquet"
RECIPE = REPO / "recipes" / "h4k2t.yaml"

needs_raw = pytest.mark.skipif(not DTA.exists(), reason="h4k2t deposit not fetched")
needs_built = pytest.mark.skipif(not (BUILT.exists() and DTA.exists()), reason="h4k2t not built")

ITEMS = {0: "CONNORS2", 1: "CONNORS3", 2: "CONNORS4", 3: "CONNORS5"}
OPTIONS = " (1) More likely; (2) Less likely; (3) The same."

# Computed from the .dta when the recipe was written (2026-11-23), and stated in
# its notes: (P_CONNORS, task) -> (answers, mean).
CELLS = {
    (1, 0): (207, 59.333),
    (1, 1): (206, 58.083),
    (1, 2): (211, 2.256),
    (1, 3): (211, 2.341),
    (2, 0): (223, 61.740),
    (2, 1): (226, 57.912),
    (2, 2): (229, 2.367),
    (2, 3): (229, 2.384),
    (3, 0): (204, 60.093),
    (3, 1): (205, 58.371),
    (3, 2): (205, 2.229),
    (3, 3): (203, 2.409),
    (4, 0): (200, 63.660),
    (4, 1): (202, 58.391),
    (4, 2): (205, 2.283),
    (4, 3): (204, 2.284),
    (5, 0): (207, 47.019),
    (5, 1): (202, 54.089),
    (5, 2): (209, 2.325),
    (5, 3): (209, 2.478),
    (6, 0): (215, 46.195),
    (6, 1): (214, 51.290),
    (6, 2): (223, 2.359),
    (6, 3): (219, 2.457),
    (7, 0): (193, 47.000),
    (7, 1): (193, 55.611),
    (7, 2): (195, 2.303),
    (7, 3): (195, 2.451),
    (8, 0): (200, 57.400),
    (8, 1): (198, 54.167),
    (8, 2): (201, 2.378),
    (8, 3): (199, 2.442),
}


def docx_text(path: Path) -> str:
    """Paragraph text of a .docx, markup removed, typography normalised."""
    xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8")
    paras = [re.sub(r"<[^>]+>", "", p) for p in re.split(r"</w:p>", xml)]
    text = "\n".join(paras)
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"')):
        text = text.replace(a, b)
    text = re.sub(r"</?(u|i|b|unbold)>", "", text)  # HTML typed into the prog text
    return re.sub(r"[ \t ]+", " ", text)


def block(q: str, raw: int) -> str:
    m = re.search(rf"SHOW IF P_CONNORS = {raw}: (.*)", q)
    assert m, raw
    return " ".join(re.sub(r"\]\s*$", "", m.group(1)).split())


@needs_raw
@pytest.mark.parametrize("doc", [SIMPLE, PROG], ids=["simple", "prog"])
def test_every_arm_is_its_questionnaire_block(doc: Path) -> None:
    q = docx_text(doc)
    rec = load(RECIPE)
    ctx = " ".join((rec.condition.shared_context or "").split())
    for arm in rec.condition.arms:
        assert arm.raw is not None
        mine = f"{ctx} {' '.join(arm.text.split())}"
        theirs = block(q, arm.raw)
        if doc == PROG and arm.raw == 1:
            # prog's "<i>frequently</i>talks" lost its space (Q 708); simple is followed.
            theirs = theirs.replace("frequentlytalks", "frequently talks")
        assert mine == theirs, arm.raw


@needs_raw
@pytest.mark.parametrize("doc", [SIMPLE, PROG], ids=["simple", "prog"])
def test_outcome_wording_is_the_questionnaire(doc: Path) -> None:
    q = " ".join(docx_text(doc).split())
    rec = load(RECIPE)
    for o in rec.outcomes:
        if o.task_num in (0, 1, 2):
            assert " ".join(o.question.split()) in q, o.var
    # CONNORS5: resolve the instrument's own fills for each arm and compare.
    m = re.search(r"If most feminists (.*?) would you be more or less likely to identify", q)
    assert m
    for arm in rec.condition.arms:
        r = arm.raw
        assert r is not None
        talks = "frequently" if r in (1, 2, 5, 6) else "rarely"
        conj = "and" if r in (1, 2, 7, 8) else "but"
        not_ = "not " if r >= 5 else ""
        want = (
            f"If most feminists {talks} talked about feminist issues {conj} were {not_}very "
            "active in working towards gender equality (like the individual described "
            "previously), would you be more or less likely to identify as a feminist?" + OPTIONS
        )
        got = arm.items[3].outcome_question
        assert got is not None and " ".join(got.split()) == want, r
    for label in ("1. More likely", "2. Less likely", "3. The same"):
        assert label in docx_text(PROG)


def _expected() -> set[tuple[str, int, int, int]]:
    df, _ = pyreadstat.read_dta(str(DTA))
    out = set()
    # TESS ids are the row index (no participant_id_var), as every TESS build.
    for idx, r in df.iterrows():
        arm = int(r.P_CONNORS) - 1
        for task, var in ITEMS.items():
            code = r[var]
            if pd.isna(code):
                continue
            code = int(code)
            top = 100 if task < 2 else 3
            lo = 0 if task < 2 else 1
            if not lo <= code <= top:
                assert code in (77, 98, 99, 777, 998, 999)
                continue
            out.add((f"h4k2t:{idx}", arm, task, code))
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
    assert len(got) == len(b) == 6642
    # Compare sizes, not the sets themselves: a failure must not print rows.
    assert len(got - expected) == 0 and len(expected - got) == 0


@needs_built
def test_cell_counts_and_means() -> None:
    b = pd.read_parquet(BUILT)
    for (raw, task), (n, mean) in CELLS.items():
        g = b[(b.condition_num == raw - 1) & (b.task_num == task)]
        assert len(g) == n, (raw, task)
        assert round(float(g.response_num.mean()), 3) == mean, (raw, task)


@needs_built
def test_one_condition_and_outcome_per_cell() -> None:
    b = pd.read_parquet(BUILT)
    cells = b.groupby(["condition_num", "task_num"])
    assert int(cells.condition.nunique().max()) == 1
    assert int(cells.outcome.nunique().max()) == 1
    # Task 3's wording differs by talks x activity: four distinct strings.
    assert b[b.task_num == 3].outcome.nunique() == 4
