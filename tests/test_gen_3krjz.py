"""The 3krjz recipe (IMG48, colour in flood risk matrices) and its answer key.

The generator derives every arm from the deposit's file names and from cell
positions read off the pictures; these tests stop a hand edit drifting from it,
and check the facts the arms rest on:

- each item's picture is the deposit file its block names, in the person's own
  colour format and (Experiment 2) boundary group, and each person's arm for an
  item is arithmetic on `colour_cond` and `cross_cond` alone;
- the cell positions the condition text states agree with the words the
  catalogue transcribes from that picture, and with the authors' scoring;
- the instrument text is word-for-word from the fielded questionnaire;
- the built rows reproduce the paper (Proto et al. 2023, Risk Analysis): the
  analytic sample of 2,249, Table 1's simple slopes, Levene's test, and the
  Experiment 2 missing counts.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import re
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_3krjz.py"
RECIPE = REPO / "recipes" / "images" / "3krjz.yaml"
RAW = REPO / "data" / "raw" / "3krjz"
CSV = RAW / "9nvk3" / "x" / "project" / "data" / "data_raw.csv"
DOCX = RAW / "9nvk3" / "survey.docx"
BUILT = REPO / "data" / "processed" / "images" / "3krjz.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_3krjz", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()


@pytest.mark.skipif(not (RAW / gen.DATA_FILE).exists(), reason="3krjz deposit not fetched")
def test_recipe_is_what_the_generator_writes() -> None:
    assert RECIPE.read_text() == gen.render()


@pytest.mark.skipif(not CSV.exists(), reason="3krjz deposit not fetched")
def test_the_coded_spreadsheet_is_what_prep_derives() -> None:
    derived = gen.prep()
    coded = pd.read_excel(RAW / gen.DATA_FILE)
    pd.testing.assert_frame_equal(derived, coded, check_dtype=False)


def test_every_arm_shows_its_own_format_and_items_picture() -> None:
    rec = load(RECIPE)
    cat = images_mod.load()
    arms = {a["condition_num"]: a for a in gen.all_arms()}
    assert len(rec.condition.arms) == len(arms) == 43
    keys = {lvl: key for key, _, lvl, _ in gen.FORMATS}
    for arm in rec.condition.arms:
        spec = arms[arm.condition_num]
        key = keys[arm.factors["format"]]
        task = arm.factors["task"]
        assert arm.images[:2] == [f"3krjz_intro1_{key}", f"3krjz_intro2_{key}"]
        assert arm.images[2].startswith(f"3krjz_{task}_{key}")
        assert arm.text.count(images_mod.IMAGE_MARKER) == 3
        # The catalogued file is the deposit file the generator names for this cell.
        assert cat[arm.images[2]].source.endswith(f"stimuli/{spec['_file']})")
        for img in arm.images:
            assert images_mod.problems(img, cat) == [], img


def test_each_persons_arm_is_arithmetic_on_the_two_assignment_codes() -> None:
    for spec in gen.all_arms():
        task = spec["factors"]["task"]
        colour, cross = spec["_code"]
        crosses = [0.0, 1.0] if cross is None else [float(cross)]
        for x in crosses:
            assert gen.stim_code(task, float(colour), x) == spec["condition_num"], (task, x)
        level = next(lvl for _, c, lvl, _ in gen.FORMATS if c == colour)
        assert spec["factors"]["format"] == level
        if task.startswith("wtp") and cross is not None:
            assert ("does not" in spec["factors"]["boundary"]) == (cross == 0)
            assert ("no-cross" in spec["_file"]) == (cross == 0)
            assert ("_imp1" in spec["_file"]) == task.endswith("imp1")


_MARK = re.compile(r'"([AB][12]?)" in the cell at likelihood (\d+) and impact (\d+)')


def _marks(words: str) -> dict[str, tuple[int, list[str]]]:
    """Impact row -> marks printed in it, from a catalogue transcription of one grid."""
    out: dict[str, tuple[int, list[str]]] = {}
    for line in words.split("\n"):
        parts = line.split()
        if len(parts) >= 2 and parts[1].isdigit():
            for m in parts[2:]:
                out[m] = (int(parts[1]), parts[2:])
    return out


def test_positions_in_the_text_agree_with_the_words_on_the_picture() -> None:
    rec = load(RECIPE)
    cat = images_mod.load()
    for arm in rec.condition.arms:
        item_part = arm.text.split("For this question")[1]
        stated = {m: (int(lk), int(im)) for m, lk, im in _MARK.findall(item_part)}
        grids = cat[arm.images[2]].text_in_image.split("\nLikelihood\n")
        printed: dict[str, tuple[int, list[str]]] = {}
        for g in grids:
            printed.update(_marks(g))
        assert set(stated) == set(printed), arm.condition_num
        for mark, (lik, imp) in stated.items():
            # The catalogue's description (checked against the picture) names the same cell.
            cell = f'"{mark}" in the cell at likelihood {lik}, impact {imp}'
            assert cell in cat[arm.images[2]].description, (arm.condition_num, mark)
            row_imp, row = printed[mark]
            assert row_imp == imp, (arm.condition_num, mark)
            # Marks in one row are printed left to right, so by likelihood.
            same_row = [m for m in row if m[0] == mark[0]]
            assert same_row == sorted(same_row, key=lambda m: stated[m][0]), arm.condition_num


def test_the_scoring_key_is_the_larger_marked_reduction() -> None:
    gen.check_scoring()
    item, a1, a2, b1, b2, key = gen.COMP_ITEMS[0]
    wrong = "Risk B" if key == "Risk A" else "Risk A"
    gen.COMP_ITEMS[0] = (item, a1, a2, b1, b2, wrong)
    try:
        with pytest.raises(SystemExit):
            gen.check_scoring()
    finally:
        gen.COMP_ITEMS[0] = (item, a1, a2, b1, b2, key)


def _docx_text() -> str:
    xml = zipfile.ZipFile(DOCX).read("word/document.xml").decode()
    paragraphs = re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S)
    words = " ".join("".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p)) for p in paragraphs)
    return " ".join(words.replace("&amp;", "&").split())


@pytest.mark.skipif(not DOCX.exists(), reason="3krjz deposit not fetched")
def test_the_instrument_text_is_word_for_word_from_the_questionnaire() -> None:
    fielded = _docx_text()
    for text in (gen.Q235, gen.Q242, gen.Q249, gen.Q269, gen.COMP_Q, gen.WTP_Q):
        assert " ".join(text.split()) in fielded
    for option in gen.COMP_OPTIONS:
        assert option in fielded


# ---- answer key: Proto et al. 2023 -------------------------------------------------


def _analytic(raw: pd.DataFrame) -> pd.DataFrame:
    """The paper's exclusions, as 0_cleaning.R applies them."""
    d = raw[(raw.Progress == 100) & raw.Q_TerminateFlag.isna()]
    d = d[~d["att.check"].astype(str).isin(["0", "0.0"])]
    blind = d.col_bl_binary.map({"Yes": 1, "No": 0})
    return d[~(d.colour_cond.isin([1, 2]) & (blind.eq(1) | blind.isna()))].set_index("tic")


def _numeracy(d: pd.DataFrame) -> pd.Series:
    def num(c: str) -> pd.Series:
        return pd.to_numeric(d[c], errors="coerce")

    b2, b3, b4 = num("bnt_2"), num("bnt_3"), num("bnt_4")
    bnt = pd.Series(np.nan, index=d.index)
    c1 = b2.notna() & (b2 != 30)
    c2 = (b2 == 30) & ~c1
    c3 = ((b3 == 20) | (b4 == 50)) & ~c1 & ~c2
    c4 = (b3 != 20) & b3.notna() & (b4 != 50) & b4.notna() & ~c1 & ~c2 & ~c3
    bnt[c1], bnt[c2], bnt[c3], bnt[c4] = 1, 2, 4, 3

    def hit(c: str, v: float) -> pd.Series:
        x = num(c)
        return (x == v).astype(float).where(x.notna())

    schw = hit("sch_1", 500) + hit("sch_2", 10) + hit("sch_3", 0.1)
    risk = (d["1_in_x"] == "1 in 10").astype(float).where(d["1_in_x"].notna())
    return bnt + schw + risk


def _slopes(m: pd.DataFrame, ref: int, at: float) -> dict[int, float]:
    """lm(comparison ~ colour_cond * numeracy + rpi), colour effects at numeracy = at."""
    x = m.numeracy - at
    others = [c for c in (0, 1, 2) if c != ref]
    dummies = [(m.colour_cond == c).astype(float) for c in others]
    cols = [np.ones(len(m)), *dummies, x, *[dd * x for dd in dummies], m.rpi]
    b, *_ = np.linalg.lstsq(np.column_stack(cols), m.comparison.to_numpy(), rcond=None)
    return {c: round(float(b[1 + i]), 3) for i, c in enumerate(others)}


@pytest.mark.skipif(not (CSV.exists() and BUILT.exists()), reason="3krjz not fetched or built")
def test_the_built_rows_reproduce_the_paper() -> None:
    from scipy import stats

    raw = pd.read_csv(CSV, skiprows=[1, 2], low_memory=False)
    rows = pd.read_parquet(BUILT)
    rows["tic"] = rows.participant_id.str.split(":").str[1].astype(int)
    d = _analytic(raw)
    assert len(d) == 2249  # "The final analytic sample consisted of 2249 individuals"

    # Risk comparison score: the authors' key on comp1/3/4/5, from OUR rows.
    key = {0: 1, 1: 1, 2: 2, 3: 1}
    r = rows[rows.task_num.isin(key)]
    ok = (r.response_num == r.task_num.map(key)).astype(int)
    d = d.assign(comparison=ok.groupby(r.tic).sum().reindex(d.index).fillna(0))
    d = d.assign(numeracy=_numeracy(d), rpi=d.rpi1_1 + d.rpi2_1 + d.rpi3_1 + d.rpi4_1)

    groups = [d.comparison[d.colour_cond == c] for c in (0, 1, 2)]
    assert round(float(stats.levene(*groups).statistic), 3) == 0.674  # F(2, 2246) = 0.674

    m = d.dropna(subset=["numeracy", "rpi"])
    mu, sd = d.numeracy.mean(), d.numeracy.std()
    # Table 1: (reference, numeracy) -> {other format: B}
    table1 = {
        (0, mu - sd): {1: 0.075, 2: -0.125},
        (0, mu): {1: -0.008, 2: -0.399},
        (0, mu + sd): {1: -0.091, 2: -0.672},
        (1, mu - sd): {2: -0.201},
        (1, mu): {2: -0.391},
        (1, mu + sd): {2: -0.582},
    }
    for (ref, at), want in table1.items():
        got = _slopes(m, ref, at)
        for c, b in want.items():
            assert got[c] == b, (ref, at, c)

    # Experiment 2: "missing observations ... 67 at low, 45 at medium, 36 at high".
    w = rows[rows.task_num.isin([6, 7, 8])].pivot_table(
        index="tic", columns="task_num", values="response_num"
    )
    w = w.reindex(d.index)
    assert [int(w[t].isna().sum()) for t in (6, 7, 8)] == [67, 45, 36]
    # Crossing groups pay more (Table 3, every format at mean numeracy): ties
    # cross_cond = 1 to "crosses", which decides which picture each arm cites.
    mean_wtp = w.mean(axis=1)
    for colour in (1, 2):
        by = mean_wtp.groupby(d.cross_cond[d.colour_cond == colour]).mean()
        assert by[1.0] > by[0.0], colour
