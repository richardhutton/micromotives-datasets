"""The DEL panel wave 4 aid-project conjoint recipes and their checks.

- both recipes are byte-identical to what `scripts/gen_del_w4_aid_conjoint.py` derives
  from the fielded questionnaire, so neither can be hand-edited out of step;
- every level text and heading is in the questionnaire, and a mutated one is caught;
- the internal reference (no DEL publication of this conjoint was found): every level of
  every attribute is drawn in near-equal shares on both sides, no screen shows two
  identical projects, and Project A / B are chosen near 50/50;
- every built row is re-derived from the deposit by code that shares nothing with the
  generator but the variable names, and no row lays out a table or cites a position.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import functools
import importlib.util
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_del_w4_aid_conjoint.py"
RAW = REPO / "data" / "raw" / "del"
SAV = RAW / "DEL_Panel_GreatBritain_Wave_4_2022_Data.sav"
DOCX = RAW / "DEL_Panel_GreatBritain_Wave_4_2022_Survey.docx"
PROCESSED = REPO / "data" / "processed"

needs_docx = pytest.mark.skipif(not DOCX.exists(), reason="DEL deposit not fetched")
needs_sav = pytest.mark.skipif(not SAV.exists(), reason="DEL deposit not fetched")


@functools.cache
def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_del_w4_aid_conjoint", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_del_w4_aid_conjoint"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _sav() -> pd.DataFrame:
    import pyreadstat

    df, _ = pyreadstat.read_sav(str(SAV))
    return df


@needs_docx
@pytest.mark.parametrize("arm", ["8attr", "6attr"])
def test_recipe_is_exactly_what_the_generator_derives(arm: str) -> None:
    gen = _gen()
    assert gen.RECIPES[arm].read_text(encoding="utf-8") == gen.render(arm), (
        "regenerate with `uv run python scripts/gen_del_w4_aid_conjoint.py --write` "
        "and read the diff"
    )


@needs_docx
def test_every_instrument_string_is_in_the_questionnaire() -> None:
    gen = _gen()
    text = "\n".join(gen.questionnaire_lines())
    ins = gen.instrument()
    for k, levels in ins["levels"].items():
        for t in levels.values():
            assert t in text, (k, t)
    # Headings carry the resolved "Britain" fill, so check them around it.
    for h in ins["headings"].values():
        assert h.replace("Britain", '" + qcountry.response_text + "') in text or h in text
    assert ins["question"] in text
    # The check fails on a mutated string (the direction a passing check never shows).
    assert "To support education provisions" not in text


@needs_docx
def test_no_row_text_lays_out_a_table_or_cites_a_position() -> None:
    gen = _gen()
    for arm in ("8attr", "6attr"):
        t = gen.build(arm)["condition"]["template"]["text"]
        for bad in ("Attribute", "first", "second", "row", "Screen", "PAIR", "next few"):
            assert bad not in t, (arm, bad)
        n = len(gen.ARMS[arm]["attrs"])
        assert t.count('"{') == 2 * n


@needs_sav
@pytest.mark.parametrize("arm", ["8attr", "6attr"])
def test_levels_are_balanced_and_profiles_distinct(arm: str) -> None:
    gen = _gen()
    spec = gen.ARMS[arm]
    df = _sav()
    df = df[df.split_sample == spec["split"]]
    for s in (1, 2, 3):
        for p in ("A", "B"):
            for i, k in enumerate(spec["attrs"], start=1):
                col = df[spec["var"](s, k, i, p)]
                assert col.notna().all()
                shares = col.value_counts(normalize=True)
                n_levels = len(gen.ATTRS[k][1])
                assert set(shares.index) == set(range(1, n_levels + 1))
                assert (abs(shares - 1 / n_levels) < 0.03).all(), (s, p, k, shares)
    # The script redraws until the six profiles a person sees are all different.
    profiles = [
        df[[spec["var"](s, k, i, p) for i, k in enumerate(spec["attrs"], start=1)]]
        .astype(int)
        .astype(str)
        .agg("-".join, axis=1)
        for s in (1, 2, 3)
        for p in ("A", "B")
    ]
    together = pd.concat(profiles, axis=1)
    assert (together.nunique(axis=1) == 6).all()
    for s in (1, 2, 3):
        share_a = (df[spec["outcome"].format(s=s)] == 1).mean()
        assert 0.45 < share_a < 0.56, (s, share_a)


@needs_sav
@pytest.mark.parametrize("arm", ["8attr", "6attr"])
def test_built_rows_rederive_from_the_deposit(arm: str) -> None:
    path = PROCESSED / f"del_panel_w4_aid_conjoint_{arm}.parquet"
    if not path.exists():
        pytest.skip("not built")
    gen = _gen()
    spec = gen.ARMS[arm]
    ins = gen.instrument()
    rows = pd.read_parquet(path)
    df = _sav()
    df = df[df.split_sample == spec["split"]]
    assert len(rows) == 3 * len(df)
    by_id = df.set_index(df.GUNQID.astype("int64").astype(str))
    checked = 0
    for r in rows.itertuples():
        pid = str(r.participant_id).split(":", 1)[1]
        person = by_id.loc[pid]
        s = int(r.task_num) + 1
        assert int(person[spec["outcome"].format(s=s)]) == int(r.response_num)
        for p in ("A", "B"):
            # This project's own segment of the text holds exactly its drawn levels.
            seg = r.condition.split("Project A: ")[1]
            seg = seg.split(" Project B: ")[0 if p == "A" else 1]
            for i, k in enumerate(spec["attrs"], start=1):
                code = int(person[spec["var"](s, k, i, p)])
                assert f'{ins["headings"][k]}, "{ins["levels"][k][code]}"' in seg
        checked += 1
    assert checked == len(rows)
