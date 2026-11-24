"""8972k's words against its fielded questionnaire, and its built rows against an
independent reading of the deposit (TESS 136, Behrman).

There is no SocSci210 build of this study and no published table, so the answer
key is recomputed here from the .dta with pyreadstat, not through the pipeline,
and compared with the BUILT parquet: every (person, condition, task, response)
tuple, and each cell's count and mean. A third check reads the assignment's
direction from the screen timers, which the questionnaire cannot speak to: the
item a respondent met first (with the opening sentence, at the start of the
topic) takes longer.

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
RAW = REPO / "data" / "raw" / "8972k"
DTA = RAW / "TESS 136 Behrman_Final Data.dta"
STEM = "TESS 136 Behrman 141 Eareckson 142 Elliott_vFINAL"
PROG = RAW / f"{STEM}prog.docx"
SIMPLE = RAW / f"{STEM}simple.docx"
BUILT = REPO / "data" / "processed" / "8972k.parquet"
RECIPE = REPO / "recipes" / "8972k.yaml"

needs_raw = pytest.mark.skipif(not DTA.exists(), reason="8972k deposit not fetched")
needs_built = pytest.mark.skipif(not (BUILT.exists() and DTA.exists()), reason="8972k not built")

ITEMS = {0: "BEHRMAN_AA1", 1: "BEHRMAN_AB1"}

# Computed from the .dta when the recipe was written (2026-11-23), and stated in
# its notes: (RND_00, task) -> (answers, mean count).
CELLS = {
    (0, 0): (818, 2.502),
    (0, 1): (818, 2.191),
    (1, 0): (839, 2.544),
    (1, 1): (841, 2.303),
}


def docx_text(path: Path) -> str:
    """Paragraph text of a .docx, markup removed, typography normalised."""
    xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8")
    paras = [re.sub(r"<[^>]+>", "", p) for p in re.split(r"</w:p>", xml)]
    text = "\n".join(paras)
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"')):
        text = text.replace(a, b)
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    text = re.sub(r"</?u>", "", text)  # "<u>personally</u>" is typed into the prog text
    return re.sub(r"[ \t ]+", " ", text)


def quoted_strings(text: str) -> list[str]:
    return re.findall(r'"([^"]+)"', text)


@needs_raw
@pytest.mark.parametrize("doc", [PROG, SIMPLE], ids=["prog", "simple"])
def test_every_rendered_word_is_in_the_questionnaire(doc: Path) -> None:
    q = docx_text(doc)
    rec = load(RECIPE)
    opening = "We would like to ask you your opinions about family size."
    assert opening in q
    for o in rec.outcomes:
        assert o.question in q, o.question
        # the inserted sentence sits immediately before each question on its line
        assert re.search(re.escape(opening) + r"\]? " + re.escape(o.question), q)
    for arm in rec.condition.arms:
        for item in arm.items.values():
            assert item.condition_text is not None
            for s in quoted_strings(item.condition_text):
                s = " ".join(s.split())
                if s.startswith(opening):
                    rest = s[len(opening) :].strip()
                    assert rest in q, rest
                else:
                    assert re.search(r"(?m)^\s*\W?\s*" + re.escape(s) + r"\s*$", q), s


@needs_raw
def test_prog_questionnaire_puts_the_opening_on_the_first_item() -> None:
    q = docx_text(PROG)
    assert "[IF RND_00=0: show BEHRMAN_AA1 first and then BEHRMAN_AB1 second]" in q
    assert "[IF RND_00=1: show BEHRMAN_AB1 first and then BEHRMAN_AA1 second]" in q
    assert "[INSERT IF RND_00=0: We would like to ask you your opinions about family size.]" in q
    assert "[INSERT IF RND_00=1: We would like to ask you your opinions about family size.]" in q


def _deposit() -> pd.DataFrame:
    df, _ = pyreadstat.read_dta(str(DTA))
    return df


@needs_raw
def test_timers_agree_with_the_assignment_direction() -> None:
    df = _deposit()
    aa = df.groupby("RND_00")["BEHRMAN_AA1_TIMER_TOTALTIME"].median()
    ab = df.groupby("RND_00")["BEHRMAN_AB1_TIMER_TOTALTIME"].median()
    assert aa[0] > aa[1]  # AA1 first when RND_00 = 0
    assert ab[1] > ab[0]  # AB1 first when RND_00 = 1


def _expected() -> set[tuple[str, int, int, int]]:
    df = _deposit()
    out = set()
    # TESS ids are the row index (no participant_id_var), as every TESS build.
    for idx, r in df.iterrows():
        arm = int(r.RND_00)
        for task, var in ITEMS.items():
            code = r[var]
            if pd.isna(code) or code in (77, 98, 99):
                continue
            assert 1 <= code <= 8
            out.add((f"8972k:{idx}", arm, task, int(code) - 1))
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
    assert len(got) == len(b) == 3316
    # Compare sizes, not the sets themselves: a failure must not print rows.
    assert len(got - expected) == 0 and len(expected - got) == 0


@needs_built
def test_cell_counts_and_means() -> None:
    b = pd.read_parquet(BUILT)
    for (arm, task), (n, mean) in CELLS.items():
        g = b[(b.condition_num == arm) & (b.task_num == task)]
        assert len(g) == n, (arm, task)
        assert round(float(g.response_num.mean()), 3) == mean, (arm, task)


@needs_built
def test_one_condition_per_cell_and_household_size_rendered() -> None:
    b = pd.read_parquet(BUILT)
    assert int(b.groupby(["condition_num", "task_num"]).condition.nunique().max()) == 1
    # HHSIZE's word labels once dropped household size from every row.
    share = float(b.persona.str.contains(r'"household_size":\s?[1-5]\b', regex=True).mean())
    assert share > 0.8, share
