"""The DEL Oct 2023 appeal-photo recipe (IMG06) and its checks.

- the recipe, the prepped .sav and the catalogue entries are what the generator
  derives, so none can be hand-edited out of step;
- every instrument string is in the questionnaire, in all five slots, and the check
  fails when one is not (both directions);
- a picture shown twice to one person is built once, from its first showing;
- every built row is re-derived from the DEPOSIT (not the prepped file) by code that
  shares nothing with the generator but the variable names: same people, same photo,
  same item, same answer, nothing missing and nothing extra;
- no row cites its slot ("Image 3") and no row quotes the words in its photo.

No published per-photo or per-folder figures exist to compare against (searched
Nov 2026); the re-derivation is the answer key. Tests needing the gitignored deposit,
photos or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_del_oct2023_appeal_photos.py"
RECIPE = REPO / "recipes" / "images" / "del_sandbox_oct2023_appeal_photos.yaml"
RAW = REPO / "data" / "raw" / "del"
SAV = RAW / "DEL_Sandbox_GreatBritain_Oct2023_Data.sav"
PHOTOS = RAW / "oct2023_images"
BUILT = REPO / "data" / "processed" / "images" / "del_sandbox_oct2023_appeal_photos.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_del_oct2023_appeal_photos", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(
    not (SAV.exists() and PHOTOS.exists()), reason="DEL Oct 2023 deposit or photos not fetched"
)
needs_built = pytest.mark.skipif(not (BUILT.exists() and SAV.exists()), reason="not built")


@needs_raw
def test_recipe_is_what_the_generator_writes() -> None:
    assert RECIPE.read_text() == gen.render()


@needs_raw
def test_catalogue_entries_are_what_the_generator_derives() -> None:
    cat = images_mod.load()
    entries = gen.catalogue_entries()
    assert len(entries) == 241
    for image_id, entry in entries.items():
        assert cat[image_id].model_dump() == entry, image_id
        assert not images_mod.problems(image_id, cat), image_id


@needs_raw
def test_prepped_file_adds_only_the_slot_codes() -> None:
    import pyreadstat

    raw, _ = pyreadstat.read_sav(str(SAV))
    derived, _ = pyreadstat.read_sav(str(RAW / gen.DATA_FILE))
    added = [gen.code_var(k) for k in range(1, 6)]
    assert list(derived.columns) == [*raw.columns, *added]
    pd.testing.assert_frame_equal(derived[added], gen.coded(raw)[added], check_dtype=False)
    assert int(derived[added].isna().sum().sum()) == gen.REPEATS


# --- the checks fail when they should --------------------------------------------


@needs_raw
def test_wording_check_passes_on_the_questionnaire() -> None:
    gen.check_wording()


@needs_raw
def test_wording_check_fails_on_a_changed_word_or_a_missing_slot() -> None:
    text = gen.survey_text()
    with pytest.raises(SystemExit, match="not in the questionnaire"):
        gen.check_wording(text.replace("Very urgent", "Most urgent"))
    # One slot's emotion stem reworded: still present elsewhere, but not five times.
    i = text.index(gen.EMOTION_STEM)
    one_off = text[:i] + text[i:].replace("the following emotions", "these emotions", 1)
    with pytest.raises(SystemExit, match="all five slots"):
        gen.check_wording(one_off)


def _slots(rows: list[list[int]], set_code: int = 1) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=[f"image{k}_number" for k in range(1, 6)], dtype=float)
    df.insert(0, gen.SET_VAR, float(set_code))
    return df


def test_a_repeated_picture_is_built_once_from_its_first_showing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gen, "REPEATS", 1)
    out = gen.coded(_slots([[1, 123, 2, 107, 3], [1, 2, 3, 4, 5]]))
    assert out.loc[0, "image2_code"] == 1123  # first showing kept
    assert np.isnan(out.loc[0, "image4_code"])  # photo107 is photo123: dropped
    assert not out.loc[1, [gen.code_var(k) for k in range(1, 6)]].isna().any()


def test_partner_photos_with_the_same_numbers_are_not_repeats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # IMG107 and IMG123 are different partner pictures; only the photographer pair is one.
    monkeypatch.setattr(gen, "REPEATS", 0)
    out = gen.coded(_slots([[1, 123, 2, 107, 3]], set_code=2))
    assert not out[[gen.code_var(k) for k in range(1, 6)]].isna().any().any()


def test_repeat_count_is_declared_both_ways(monkeypatch: pytest.MonkeyPatch) -> None:
    df = _slots([[1, 123, 2, 107, 3]])
    monkeypatch.setattr(gen, "REPEATS", 0)
    with pytest.raises(SystemExit, match="repeated showings"):
        gen.coded(df)
    monkeypatch.setattr(gen, "REPEATS", 2)
    with pytest.raises(SystemExit, match="repeated showings"):
        gen.coded(df)


# --- the recipe's text -----------------------------------------------------------


def test_every_arm_is_its_photo_under_the_shared_introduction() -> None:
    rec = load(RECIPE)
    assert len(rec.condition.arms) == 241
    assert rec.condition.shared_context == gen.SHARED
    for arm in rec.condition.arms:
        assert arm.text == gen.ARM_TEXT
        assert arm.images == [gen.image_id(arm.factors["photo"].split(" = ")[0])]
        codes = arm.raws or [arm.raw]
        set_code = 1 if arm.factors["image_set"] == "photographer" else 2
        names = arm.factors["photo"].split(" = ")
        assert codes == [gen.code_of(set_code, gen.number_of(n)) for n in names]
    merged = {a.factors["photo"] for a in rec.condition.arms if a.raws}
    assert merged == {"photo107 = photo123", "photo112 = photo128"}


def test_no_text_cites_a_slot_or_quotes_the_photo() -> None:
    rec = load(RECIPE)
    texts = [rec.condition.shared_context or "", gen.ARM_TEXT] + [o.question for o in rec.outcomes]
    for t in texts:
        assert not re.search(r"\bimage\s*\d", t, re.I), t
        assert "Here is" not in t
    cat = images_mod.load()
    for arm in rec.condition.arms:
        words = cat[arm.images[0]].text_in_image if arm.images[0] in cat else ""
        if words:
            assert words not in arm.text


def test_outcome_layout() -> None:
    rec = load(RECIPE)
    assert len(rec.outcomes) == 55
    for o in rec.outcomes:
        slot = o.task_num // 11
        assert o.var is not None and re.search(rf"_{gen.SLOTS[slot]}\d?$", o.var), o.var
        assert (o.condition_var is None) == (slot == 0)
    # 8, 9 and 11 are real answers on the amount and the 0-10 items.
    assert rec.missing_codes == [99998, 99999]


# --- the answer key: every row re-derived from the deposit -------------------------


def _expected() -> set[tuple[str, str, str, int]]:
    """(participant, photo, variable, answer) for every answer the build should hold."""
    import pyreadstat

    df, _ = pyreadstat.read_sav(str(SAV))
    same = {"photo123": "photo107", "photo128": "photo112"}
    valid = {
        "p_medemot": range(1, 6),
        "p_medurgency": range(1, 6),
        "p_medefficacy": range(1, 6),
        "getinfo": range(1, 3),
        "donate": range(1, 3),
        "donate_amt": range(1, 10000),
        "eff_follow": range(11),
    }
    out: set[tuple[str, str, str, int]] = set()
    for _, row in df.iterrows():
        pid = f"del:{int(row['GUNQID'])}"
        seen: set[str] = set()
        for k, s in enumerate("abcde", start=1):
            photo = same.get(row[f"image{k}_name"], row[f"image{k}_name"])
            if photo in seen:
                continue
            seen.add(photo)
            follow = ("ey", "en") if s == "e" else ("dy", "dn")
            items = [
                *[f"p_medemot_{s}{i}" for i in range(1, 5)],
                f"p_medurgency_{s}",
                f"p_medefficacy_{s}",
                f"getinfo_{s}",
                f"donate_{s}",
                f"donate_amt_{s}",
                *[f"eff_follow_{f}_{s}" for f in follow],
            ]
            for var in items:
                value = row[var]
                if pd.isna(value):
                    continue
                stem = max((p for p in valid if var.startswith(p)), key=len)
                if int(value) in valid[stem]:
                    out.add((pid, photo, var, int(value)))
    return out


@needs_built
def test_every_row_is_rederived_from_the_deposit() -> None:
    rec = load(RECIPE)
    var_of = {o.task_num: o.var for o in rec.outcomes}
    rows = pd.read_parquet(BUILT)
    got = {
        (pid, f["photo"].split(" = ")[0], var_of[t], int(r))
        for pid, f, t, r in zip(
            rows["participant_id"],
            rows["factors"],
            rows["task_num"],
            rows["response_num"],
            strict=True,
        )
    }
    assert len(got) == len(rows) == 164_209
    expected = _expected()
    assert got == expected, (len(got - expected), len(expected - got))
