"""The zenodo10641548 recipe (trophy-hunting vignettes, UK respondents) and its answer key.

The generator holds every word of the condition and outcome; these tests stop a hand
edit drifting from it, and check the words and numbers the rows rest on:

- the recipe and the derived data file are what the generator writes;
- all 12 arm texts equal the authors' ESM S3 (Hare et al., Proc. R. Soc. B 2024,
  rspb20231638_si_001.pdf), parsed out of the PDF here, and S4's vignette page holds
  the page sentence, the instruction used as the outcome, the example vignette and
  the seven scale labels;
- the built rows carry the arm's text and the same printed instruction as outcome;
- the paper's top-supported model (ESM S6) is reproduced with the UK half of its
  data taken from the built rows, and swapping the UK rows' meat factor breaks it.

Tests needing the gitignored deposit, the build, pdftotext or R skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
RECIPE = REPO / "recipes" / "zenodo10641548.yaml"
SI_PDF = REPO / "data" / "raw" / "zenodo10641548" / "si" / "rspb20231638_si_001.pdf"
BUILT = REPO / "data" / "processed" / "zenodo10641548.parquet"


def _module(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _module("gen_zenodo10641548")
needs_raw = pytest.mark.skipif(not gen.CSV.exists(), reason="zenodo10641548 deposit not fetched")
needs_si = pytest.mark.skipif(
    not SI_PDF.exists() or shutil.which("pdftotext") is None,
    reason="ESM PDF or pdftotext not available",
)
needs_built = pytest.mark.skipif(not BUILT.exists(), reason="zenodo10641548 not built")
needs_r = pytest.mark.skipif(
    not (BUILT.exists() and gen.CSV.exists() and shutil.which("Rscript")),
    reason="build, deposit or Rscript not available",
)


def _si(first: int, last: int) -> str:
    out = subprocess.run(
        ["pdftotext", "-raw", "-f", str(first), "-l", str(last), str(SI_PDF), "-"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return out.replace("’", "'")


def _s3_blocks() -> list[tuple[tuple[str, str, str], str]]:
    """ESM S3 (pp. 10-15): (animal, meat, revenue) and the vignette, lines joined."""
    head = re.compile(
        r"^(Elephant|Zebra) (Wildlife|People) (Conservation|Development|Hunting) (.*)$"
    )
    skip = re.compile(r"^(\d+|S3, continued|Animal Meat Revenue Vignette text)$")
    blocks: list[tuple[tuple[str, str, str], list[str]]] = []
    for line in _si(10, 15).splitlines():
        line = line.strip()
        if m := head.match(line):
            blocks.append(((m[1], m[2], m[3]), [m[4]]))
        elif blocks and line and not skip.match(line):
            blocks[-1][1].append(line)
    return [(arm, " ".join(lines)) for arm, lines in blocks]


@needs_raw
def test_recipe_and_derived_file_are_what_the_generator_writes() -> None:
    assert RECIPE.read_text() == gen.render()
    on_disk = pd.read_csv(gen.DERIVED)
    fresh = gen.derive(gen.load())
    assert on_disk.equals(pd.read_csv(pd.io.common.StringIO(fresh.to_csv(index=False))))


def test_arms_are_the_full_factorial_in_s3_order() -> None:
    rec = load(RECIPE)
    arms = rec.condition.arms
    assert [a.condition_num for a in arms] == list(range(12))
    assert [a.raw for a in arms] == list(range(1, 13))
    seen = {(a.factors["animal"], a.factors["meat"], a.factors["revenue"]) for a in arms}
    assert len(seen) == 12
    assert [a.factors["animal"] for a in arms] == ["elephant"] * 6 + ["zebra"] * 6


@needs_si
def test_every_arm_text_equals_esm_s3() -> None:
    blocks = _s3_blocks()
    assert [arm for arm, _ in blocks] == gen.ARMS
    for (animal, meat, revenue), text in blocks:
        assert text == f"{gen.OPENING} {gen.arm_text(animal, meat, revenue)}"


@needs_si
def test_s3_parser_rejects_a_changed_word() -> None:
    """The check above must fail on a one-word difference, not only on a missing arm."""
    (animal, meat, revenue), text = _s3_blocks()[7]
    wrong = gen.arm_text(animal, meat, revenue).replace("schools", "hospitals")
    assert text != f"{gen.OPENING} {wrong}"


@needs_si
def test_s4_vignette_page_holds_what_the_rows_use() -> None:
    page = " ".join(_si(20, 20).split())
    assert gen.PAGE_INTRO in page
    assert f"{gen.OPENING} {gen.arm_text(*gen.ARMS[0])}" in page
    assert gen.QUESTION in page
    assert gen.ELEPHANT_ITEM in page
    labels = " • ".join(gen.RESPONSES)
    assert f"• {labels} • I don't know" in page
    assert list(gen.RESPONSES.values()) == list(range(1, 8))


@needs_built
def test_built_rows_carry_their_arm_and_the_printed_instruction() -> None:
    rows = pd.read_parquet(BUILT)
    assert len(rows) == 388 and rows["participant_id"].is_unique
    for _, r in rows.iterrows():
        animal, meat, revenue = gen.ARMS[r["condition_num"]]
        expected = f"{gen.PAGE_INTRO} {gen.OPENING} {gen.arm_text(animal, meat, revenue)}"
        assert r["condition"] == expected
        assert r["factors"]["animal"] == animal.lower()
        question = gen.QUESTION
        assert r["outcome"].startswith(question + " Only return an integer from 1 to 7")
        assert "[" not in r["outcome"]
        assert "elephant hunt" not in r["outcome"] and "zebra hunt" not in r["outcome"]
    assert rows["condition_num"].value_counts().sort_index().tolist() == gen.S8_UK


@needs_r
def test_esm_s6_is_reproduced_from_the_built_rows() -> None:
    verify = _module("verify_zenodo10641548")
    est = verify.fit(verify.model_frame()).set_index("term")["estimate"]
    assert verify.compare(est, quiet=True) == []


@needs_r
def test_s6_check_catches_uk_rows_with_the_meat_factor_swapped() -> None:
    verify = _module("verify_zenodo10641548")
    frame = verify.model_frame()
    uk = frame["country"] == "UK"
    frame.loc[uk, "meat"] = frame.loc[uk, "meat"].map({"People": "Wildlife", "Wildlife": "People"})
    est = verify.fit(frame).set_index("term")["estimate"]
    assert "meatPeople" in verify.compare(est, quiet=True)
