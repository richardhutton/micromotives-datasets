"""IP 9.4 — "occupation" or "profession" in an identity battery, wave 2.

One word varies, so the two things that can go wrong are which word a row
carries and whose household allocation it came from. A swapped word or a
scrambled join would still build and pass QC.

These need the UKDS deposit, which is licensed and gitignored, so they skip when
it is absent rather than failing on a fresh clone.
"""

from __future__ import annotations

import functools
import importlib.util
import sys
from pathlib import Path

import pytest

from micromotives_datasets import recipe
from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.sources import spss

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_ip_identity.py"
RECIPE = REPO / "recipes" / "ukds_6849_identity_w2.yaml"
DERIVED = REPO / "data" / "raw" / "ukds_6849" / "identity_w2-derived.sav"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"

# From the questionnaire, deliberately not from the recipe.
STEM = (
    "We’d like to know how important various things are to your sense of who you are. "
    "Please think about each thing I mention, and tell me whether you think it is important, "
    "not very important or not at all important to your sense of who you are?"
)
WORD = {"occupation": "Your occupation?", "profession": "Your profession?"}

needs_deposit = pytest.mark.skipif(
    not (STATA / "b_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not DERIVED.exists(), reason="derived file not built — run scripts/gen_ip_identity.py --write"
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_identity", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_identity"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows() -> tuple:
    return tuple(build_rows(spss.read(DERIVED), recipe.load(RECIPE)))


@needs_deposit
def test_the_joined_allocation_agrees_with_indresps_own_copy() -> None:
    assert _generator().check() == 0


@needs_deposit
def test_pidp_is_never_written_to_the_derived_file() -> None:
    frame, _ = _generator().derive()
    assert "pidp" not in frame.columns
    assert frame["person"].str.startswith("ip_").all()


@functools.cache
def _raw_version() -> dict[str, str]:
    """participant id -> the word indresp's OWN copy of the allocation says they got.

    Independent of the recipe and of the generator's household join, so a row that
    agreed with itself but not with the respondent's allocation fails here.
    """
    gen = _generator()
    df = spss.read(STATA / "b_indresp_ip.dta").df
    word = {1: "occupation", 2: "profession"}
    return {
        f"ukds_6849:{gen.person_hash(int(p))}": word[int(v)]
        for p, v in zip(df["pidp"], df["b_ff_identityw2"], strict=True)
        if v in word
    }


@needs_derived
def test_every_row_carries_its_own_versions_word_in_condition_and_question() -> None:
    raw = _raw_version()
    for row in _rows():
        assert raw[row.participant_id] == row.factors["word"]
        item = WORD[raw[row.participant_id]]
        assert row.condition == f'You were asked: "{STEM}" "{item}"'
        assert row.outcome.startswith(f"{STEM} {item} Only return an integer from 1 to 3")
        other = WORD["profession" if raw[row.participant_id] == "occupation" else "occupation"]
        assert other not in row.condition + row.outcome


@needs_derived
def test_the_row_count_and_range() -> None:
    rows = _rows()
    assert len(rows) == 1746
    assert {int(r.response) for r in rows} <= {1, 2, 3}
    assert all((r.participant_id or "").startswith("ukds_6849:ip_") for r in rows)
