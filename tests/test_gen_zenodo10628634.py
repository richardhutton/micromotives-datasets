"""The zenodo10628634 recipe (IMG77, mycelium as food) and its answer key.

The generator reads every arm's words from the survey document and every answer
from Mycelium.sav; these tests stop a hand edit drifting from it, and check the
facts the rows rest on:

- each of the nine arms is the docx block for its own product and substrate, shows
  that product's picture and that substrate's picture, and carries every black
  sentence of its block apart from the dropped reading instruction;
- every outcome's wording is in the docx's shown text;
- the built rows reproduce the paper (Fischer & Hilboesen, Food Quality and
  Preference 122, 2025, 105304): Table 2's cell sizes, the mean and SD of all 15
  rated items in all nine cells, and the randomisation-check rows for age, gender
  and education.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import tempfile
import zipfile
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_zenodo10628634.py"
RECIPE = REPO / "recipes" / "images" / "zenodo10628634.yaml"
RAW = REPO / "data" / "raw" / "zenodo10628634"
SAV = RAW / "Mycelium.sav"
BUILT = REPO / "data" / "processed" / "images" / "zenodo10628634.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_zenodo10628634", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not SAV.exists(), reason="zenodo10628634 deposit not fetched")
needs_built = pytest.mark.skipif(
    not (BUILT.exists() and SAV.exists()), reason="zenodo10628634 not built"
)

PRODUCT_PICTURE = {
    "mould cake": "zenodo10628634_product_mould_cake",
    "protein powder": "zenodo10628634_product_protein_powder",
    "burger": "zenodo10628634_product_burger",
}
SUBSTRATE_PICTURE = {
    "horse manure": "zenodo10628634_substrate_horse_manure",
    "hardwood logs": "zenodo10628634_substrate_hardwood_logs",
    "glucose": "zenodo10628634_substrate_glucose",
}
PRODUCT_WORDS = {
    "mould cake": "natural mould cake similar to tempeh",
    "protein powder": "mycelium protein powder, which can be used in smoothies",
    "burger": "burger and will have an appearance",
}
SUBSTRATE_WORDS = {
    "horse manure": "grown using a substrate of composted horse manure mixed with straw, which",
    "hardwood logs": "grown using hardwood logs as a growth substrate",
    "glucose": "The mycelium used for the novel product is grown using a substrate of glucose",
}


@needs_raw
def test_recipe_is_what_the_generator_writes() -> None:
    assert RECIPE.read_text() == gen.render()


@needs_raw
def test_catalogue_entries_are_what_the_generator_derives() -> None:
    cat = images_mod.load()
    for image_id, entry in gen.catalogue_entries().items():
        assert cat[image_id].model_dump() == entry, image_id


@needs_raw
def test_condition_codes_name_the_arms_factors() -> None:
    from micromotives_datasets.sources import read_any

    ds = read_any(SAV)
    rec = load(RECIPE)
    labels = ds.value_labels["Condition"]
    for arm in rec.condition.arms:
        label = str(labels[float(arm.raw)]) if float(arm.raw) in labels else labels[arm.raw]
        product, substrate = arm.factors["product"], arm.factors["substrate"]
        assert gen.PRODUCTS[product][0] in label and gen.SUBSTRATES[substrate][0] in label
    # Process and Source agree with Condition in every row.
    df = ds.df
    proc = {1: "mould cake", 2: "protein powder", 3: "burger"}
    src = {1: "horse manure", 2: "hardwood logs", 3: "glucose"}
    by_raw = {a.raw: a.factors for a in rec.condition.arms}
    for c, p, s in zip(df["Condition"], df["Process"], df["Source"], strict=True):
        assert by_raw[int(c)] == {"product": proc[int(p)], "substrate": src[int(s)]}


def test_each_arm_shows_and_names_its_own_product_and_substrate() -> None:
    rec = load(RECIPE)
    assert len(rec.condition.arms) == 9
    seen = set()
    for arm in rec.condition.arms:
        product, substrate = arm.factors["product"], arm.factors["substrate"]
        seen.add((product, substrate))
        assert arm.images == [PRODUCT_PICTURE[product], SUBSTRATE_PICTURE[substrate]]
        assert arm.text.count(images_mod.IMAGE_MARKER) == 2
        assert PRODUCT_WORDS[product] in arm.text
        assert SUBSTRATE_WORDS[substrate] in arm.text
        for other in set(PRODUCT_WORDS) - {product}:
            assert PRODUCT_WORDS[other] not in arm.text, (product, other)
        for other in set(SUBSTRATE_WORDS) - {substrate}:
            assert SUBSTRATE_WORDS[other] not in arm.text, (substrate, other)
        assert gen.DROPPED not in arm.text
    assert len(seen) == 9


@needs_raw
def test_arm_text_is_the_docx_block_word_for_word() -> None:
    shown = gen.docx_shown_text()
    rec = load(RECIPE)
    for arm in rec.condition.arms:
        parts = gen.arm_parts(arm.factors["product"], arm.factors["substrate"])
        intro, _, cap1, sub, _, cap2 = parts
        for sentence in (intro, cap1, sub, cap2):
            assert sentence in shown
            assert sentence in arm.text
        # Nothing but our caption lead is added.
        ours = arm.text
        for piece in (intro, sub, f'"{cap1}"', f'"{cap2}"'):
            ours = ours.replace(piece, "", 1)
        assert ours.split() == ["<image>", "Captioned:", "<image>", "Captioned:"]


@needs_raw
def test_the_mould_cake_picture_is_the_docx_crop() -> None:
    assert gen.crop_box() == (286, 0, 1325, 1340)
    cat = images_mod.load()
    for image_id in [*PRODUCT_PICTURE.values(), *SUBSTRATE_PICTURE.values()]:
        assert images_mod.problems(image_id, cat) == []
        assert cat[image_id].text_in_image == ""


@needs_raw
@pytest.mark.skipif(shutil.which("sips") is None, reason="needs macOS sips to re-crop")
def test_each_arms_pictures_are_the_files_its_docx_block_shows() -> None:
    """Semantic, not frozen: the picture each arm's FACTORS call for must be,
    byte for byte, the docx media its own block embeds (the mould cake re-cropped
    as the docx displays it). A product or substrate picture swapped on disk, in
    the catalogue or in the generator's picture table fails here even when the
    generator, catalogue and recipe agree with each other."""
    cat = images_mod.load()
    rec = load(RECIPE)
    with zipfile.ZipFile(gen.DOCX) as z, tempfile.TemporaryDirectory() as tmp:
        for arm in rec.condition.arms:
            product, substrate = arm.factors["product"], arm.factors["substrate"]
            block = gen.scenarios()[(product, substrate)]
            media = [v for k, v in block if k == "image"]
            expected = [PRODUCT_PICTURE[product], SUBSTRATE_PICTURE[substrate]]
            assert arm.images == expected
            for image_id, name in zip(expected, media, strict=True):
                raw = z.read(f"word/media/{name}")
                if image_id == PRODUCT_PICTURE["mould cake"]:
                    src = Path(tmp) / name
                    src.write_bytes(raw)
                    out = Path(tmp) / "crop.png"
                    left, top, w, h = gen.crop_box()
                    subprocess.run(
                        [
                            "sips",
                            "-s",
                            "format",
                            "png",
                            "-c",
                            str(h),
                            str(w),
                            "--cropOffset",
                            str(top),
                            str(left),
                            str(src),
                            "--out",
                            str(out),
                        ],
                        check=True,
                        capture_output=True,
                    )
                    raw = out.read_bytes()
                want = hashlib.sha256(raw).hexdigest()
                f = REPO / "data" / cat[image_id].file
                assert hashlib.sha256(f.read_bytes()).hexdigest() == want, (arm.raw, image_id)
                assert cat[image_id].sha256 == want, (arm.raw, image_id)


@needs_raw
def test_outcome_wording_is_the_docx_text() -> None:
    shown = gen.docx_shown_text()
    rec = load(RECIPE)
    assert [o.var for o in rec.outcomes] == [v for v, *_ in gen.OUTCOME_ITEMS]
    for (_, stem, statement, labels), outcome in zip(gen.OUTCOME_ITEMS, rec.outcomes, strict=True):
        assert stem in shown and statement in shown
        assert outcome.question == f'{stem} "{statement}"'
        for label in labels:
            assert label in shown, label
    built = {o.var for o in rec.outcomes}
    assert not built & {"Familiarity", "hearR", "envrR", "Env", *[f"Q17_{i}" for i in range(1, 13)]}


# Table 2: per cell (Condition 1..9 in the paper's column order), mean then SD.
TABLE_2 = {
    "ATT2": (
        [3.62, 3.56, 3.82, 3.78, 4.12, 4.37, 3.33, 4.22, 3.76],
        [1.94, 1.68, 1.73, 1.60, 1.39, 1.19, 1.57, 1.59, 1.44],
    ),
    "INT1": (
        [3.98, 3.60, 3.82, 4.10, 4.64, 4.43, 3.67, 4.35, 4.08],
        [2.25, 1.93, 2.02, 1.87, 1.56, 1.73, 1.99, 1.90, 1.89],
    ),
    "ATT1": (
        [3.30, 3.12, 3.35, 3.58, 3.96, 3.78, 3.39, 3.88, 3.59],
        [1.74, 1.42, 1.61, 1.44, 1.37, 1.23, 1.69, 1.39, 1.43],
    ),
    "INT2": (
        [3.16, 2.88, 2.92, 3.46, 4.04, 3.63, 3.00, 3.65, 3.37],
        [1.99, 1.48, 1.74, 1.56, 1.43, 1.59, 1.54, 1.54, 1.65],
    ),
    "SOC1": (
        [3.24, 3.00, 3.27, 3.32, 3.40, 3.16, 2.80, 3.08, 2.82],
        [1.83, 1.71, 1.59, 1.60, 1.50, 1.48, 1.59, 1.48, 1.60],
    ),
    "SOC2": (
        [2.80, 2.74, 3.04, 2.90, 3.22, 2.94, 2.49, 2.86, 2.57],
        [1.55, 1.51, 1.55, 1.50, 1.45, 1.51, 1.42, 1.35, 1.62],
    ),
    "SOC3": (
        [3.18, 2.98, 3.10, 3.12, 3.76, 3.35, 2.88, 3.14, 2.82],
        [1.64, 1.62, 1.48, 1.52, 1.57, 1.59, 1.64, 1.46, 1.69],
    ),
    "HeaB": (
        [4.34, 3.98, 4.51, 4.22, 4.60, 4.71, 3.82, 4.20, 4.20],
        [1.56, 1.29, 1.37, 1.38, 1.16, 1.46, 1.68, 1.26, 1.35],
    ),
    "HeaR": (
        [2.90, 2.76, 2.57, 3.12, 2.64, 2.63, 3.12, 2.82, 2.59],
        [1.53, 1.30, 1.29, 1.42, 1.06, 1.15, 1.41, 1.63, 1.08],
    ),
    "EnvB": (
        [5.22, 5.26, 5.29, 4.96, 5.18, 5.33, 4.94, 5.29, 5.08],
        [1.43, 1.28, 1.53, 1.38, 1.38, 1.27, 1.64, 1.37, 1.38],
    ),
    "EnvR": (
        [2.60, 2.44, 2.76, 2.42, 2.70, 2.47, 2.88, 2.65, 2.51],
        [1.31, 1.07, 1.23, 1.18, 1.37, 1.14, 1.44, 1.28, 1.14],
    ),
    "DISG2": (
        [3.82, 3.72, 4.16, 3.34, 2.84, 2.67, 3.92, 3.00, 3.29],
        [2.19, 2.27, 2.07, 2.04, 1.80, 1.88, 2.03, 1.95, 2.12],
    ),
    "DISG3": (
        [3.94, 3.52, 3.78, 3.30, 2.80, 2.69, 4.08, 3.08, 3.14],
        [2.15, 2.19, 1.96, 2.10, 1.98, 2.01, 2.09, 1.89, 2.00],
    ),
    "DISG4": (
        [3.78, 3.60, 3.76, 3.08, 2.52, 2.39, 3.71, 2.76, 3.02],
        [2.12, 2.30, 2.01, 2.08, 1.78, 1.80, 2.02, 1.88, 2.04],
    ),
    "DISG1": (
        [3.66, 3.82, 4.16, 3.08, 2.60, 2.41, 3.71, 2.98, 3.22],
        [2.18, 2.27, 2.12, 1.97, 1.71, 1.59, 1.97, 1.95, 2.05],
    ),
    "NATURAL": (
        [5.40, 5.38, 4.86, 5.06, 5.06, 4.69, 4.92, 4.96, 4.00],
        [1.49, 1.54, 1.68, 1.41, 1.42, 1.53, 1.66, 1.63, 1.76],
    ),
}
CELL_N = [50, 51, 50, 50, 50, 49, 50, 50, 49]
AGE = [43.48, 44.64, 46.22, 46.54, 43.16, 41.43, 45.39, 46.08, 45.67]
MALE = [29, 22, 25, 24, 27, 25, 23, 23, 21]
FEMALE = [21, 28, 25, 26, 23, 24, 27, 27, 28]
# Education: GCSE + A levels (both High school here) and Bachelor's + Master's +
# Doctorate (Bachelors to postgraduate), summed from Table 2's rows.
HIGH_SCHOOL = [9 + 11, 6 + 15, 8 + 14, 10 + 11, 8 + 14, 2 + 18, 9 + 15, 12 + 11, 7 + 15]
DEGREE = [
    15 + 12 + 3,
    25 + 3 + 2,
    21 + 6 + 1,
    16 + 10 + 3,
    19 + 7 + 1,
    21 + 7 + 1,
    13 + 13 + 0,
    16 + 7 + 4,
    22 + 4 + 1,
]


def _half_up(x: float, places: int) -> float:
    q = Decimal(1).scaleb(-places)
    return float(Decimal(repr(float(x))).quantize(q, rounding=ROUND_HALF_UP))


def _wide() -> pd.DataFrame:
    rows = pd.read_parquet(BUILT)
    var = {o.task_num: o.var for o in load(RECIPE).outcomes}
    wide = rows.pivot(index="participant_id", columns="task_num", values="response_num")
    wide = wide.rename(columns=var)
    first = rows.groupby("participant_id").first()
    wide["cell"] = first["condition_num"]
    persona = first["persona"].map(json.loads)
    for field in ("age", "gender", "education"):
        wide[field] = persona.map(lambda p, f=field: p[f])
    return wide


@needs_built
def test_paper_cell_sizes_and_table_2_items() -> None:
    w = _wide()
    assert len(w) == 449
    assert [int((w["cell"] == c).sum()) for c in range(9)] == CELL_N
    # Table 2 prints every cell's full size, but its item means and SDs leave out
    # the 4 people with no age (its footnote: "N for age was 445"), one each in
    # mould cake x logs, mould cake x glucose, burger x manure and burger x logs:
    # listwise deletion in SPSS. With all 449 those four cells differ by up to
    # 0.08 and the other five agree exactly; with the four left out all nine do.
    # Dropping any other single person in those cells does not reproduce them.
    w = w[w["age"].notna()]
    assert len(w) == 445
    for item, (means, sds) in TABLE_2.items():
        g = w.groupby("cell")[item]
        got_m = [_half_up(x, 2) for x in g.mean()]
        # SDs are printed rounded twice, to three decimals and then to two: 12 of
        # the 144 (e.g. ATT2 powder x manure, 1.5945 -> 1.595 -> "1.60") are off
        # by just over 0.005 under a single rounding and exact under the double.
        got_sd = [_half_up(_half_up(x, 3), 2) for x in g.std()]
        assert got_m == means, (item, got_m)
        assert got_sd == sds, (item, got_sd)


@needs_built
def test_paper_randomisation_rows() -> None:
    w = _wide()
    g = w.groupby("cell")
    assert [_half_up(x, 2) for x in g["age"].mean()] == AGE
    # Section 3.1: "51 % female, mean age 44.7 year (SD=15.6)".
    assert _half_up(100 * (w["gender"] == "Female").mean(), 0) == 51
    assert (_half_up(w["age"].mean(), 1), _half_up(w["age"].std(), 1)) == (44.7, 15.6)
    assert [int((grp["gender"] == "Male").sum()) for _, grp in g] == MALE
    assert [int((grp["gender"] == "Female").sum()) for _, grp in g] == FEMALE
    assert [int((grp["education"] == "High school").sum()) for _, grp in g] == HIGH_SCHOOL
    assert [int((grp["education"] == "Bachelors to postgraduate").sum()) for _, grp in g] == DEGREE
    assert int(w["age"].isna().sum()) == 4
    assert int(w["gender"].isna().sum()) == 1
