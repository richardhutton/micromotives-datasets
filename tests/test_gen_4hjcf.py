"""The 4hjcf recipe (IMG57, Stoeckel et al. 2024, UK experiment: social corrections under
false and true news posts) and the facts its rows rest on.

- the recipe, the derived wide CSV and this study's images.json entries are exactly
  what the generator derives, and each picture is its stimulus-zip member byte for byte;
- the data's arm suffixes are decoded by the authors' own code (sc = low, sca = high,
  scp = high + link), every stimulus folder names its four files the same way, and the
  per-arm effects in the deposit reproduce the authors' published coefficients under
  that decoding and under no other;
- each post's data number is its stimulus folder's number, as the authors' own
  congeniality and true-news labels confirm;
- a respondent with two arms recorded for one post, or an answer with no arm, is refused;
  a false post drawn by BOTH flow randomisers is left out (its condition cannot be
  verified), and nothing else is;
- every arm cites its own picture and quotes that picture's words, the control arm has
  no comment, and the link arm adds a link card to the high-amplification comment;
- the authors' analysis sample (1,944 people) reproduces Supplementary Table 11 under
  the persona labels used here, and the built rows are current.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import re
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_4hjcf.py"
RECIPE = REPO / "recipes" / "images" / "4hjcf.yaml"
RAW = REPO / "data" / "raw" / "4hjcf"
DEPOSIT = RAW / "analyses" / "data.csv"
BUILT = REPO / "data" / "processed" / "images" / "4hjcf.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_4hjcf", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not DEPOSIT.exists(), reason="4hjcf deposit not fetched")
needs_built = pytest.mark.skipif(
    not (BUILT.exists() and DEPOSIT.exists()), reason="4hjcf not built"
)

# Supplementary Table 11 (the paper's ESM, fetched 10 Nov 2026), UK experiment.
TABLE_11 = {
    "gender_scr": {
        "Female": 990,
        "Male": 946,
        "Non-binary / third gender / other": 8,
    },
    "age_scr": {"18-24": 235, "25-34": 285, "35-44": 344, "45-54": 355, "55-64": 310, "65+": 415},
    "edu_scr_codes": {1: 771, 2: 530, 3: 643},
}
# The authors' lmer models: Number of obs and psid groups. Their models drop the 8
# people whose gender is code 4 (NA in their recode), so ours carry 8 more people.
AUTHORS_OBS = {"false_acc": (9848, 1927), "true_acc": (5808, 1927)}


@needs_raw
def test_recipe_and_wide_csv_are_what_the_generator_writes() -> None:
    assert RECIPE.read_text() == gen.render()
    assert gen.WIDE.read_text() == gen.wide_csv_text()


@needs_raw
def test_catalogue_entries_are_what_the_generator_derives() -> None:
    cat = images_mod.load()
    entries = gen.catalogue_entries()  # raises if a file is not its zip member
    assert len(entries) == 52
    for image_id, entry in entries.items():
        assert cat[image_id].model_dump() == entry, image_id
        assert not images_mod.problems(image_id, cat), image_id


@needs_raw
def test_every_picture_is_its_zip_member_and_named_by_kind() -> None:
    m = gen.members()
    with zipfile.ZipFile(gen.ZIP) as z:
        for (key, kind), member in m.items():
            assert (gen.IMAGES / f"{gen.image_id(key, kind)}.png").read_bytes() == z.read(member)
            folder = member.split("/")[1]
            post = next(p for p in gen.POSTS if p["key"] == key)
            assert folder == post["folder"]
            assert gen.file_kind(member.rsplit("/", 1)[1]) == kind


def test_file_kind_reads_names() -> None:
    assert gen.file_kind("control.png") == "control"
    assert gen.file_kind("low amp.png") == "low"
    assert gen.file_kind("high amplification.png") == "high"
    assert gen.file_kind("high amp + debunk.png") == "link"
    assert gen.file_kind("high amp + link.png") == "link"
    with pytest.raises(SystemExit):
        gen.file_kind("medium.png")


@needs_raw
def test_authors_code_decodes_the_suffixes() -> None:
    assert gen.authors_treatment_coding() == {
        "control": "control",
        "sc": "low ampl",
        "sca": "high ampl",
        "scp": "ampl+link",
    }
    assert [(s, kind) for s, _, _, kind in gen.ARMS] == [
        ("control", "control"),
        ("sc", "low"),
        ("sca", "high"),
        ("scp", "link"),
    ]
    gen.verify_mapping()  # post numbers = folder numbers, congeniality, true-news labels


@needs_raw
def test_published_effects_pick_out_this_decoding_alone() -> None:
    errors = gen.decoding_errors()
    best = min(errors, key=errors.__getitem__)
    assert best == ("low", "high", "link")
    others = sorted(v for k, v in errors.items() if k != best)
    assert errors[best] * 5 < others[0]
    est = gen.effects()
    for key, pub in gen.PUBLISHED.items():
        for a, b in zip(est[key], pub, strict=True):
            assert abs(a - b) < 0.02, (key, est[key], pub)


@needs_raw
def test_sample_and_model_sizes_reproduce_the_authors() -> None:
    df = gen.authors_sample(gen.deposit())
    assert len(df) == 1944
    labelled = {
        v: df[v].map(lambda c, v=v: gen.PERSONA_VARS[v][int(c)]) for v in ("gender_scr", "age_scr")
    }
    assert labelled["gender_scr"].value_counts().to_dict() == TABLE_11["gender_scr"]
    assert labelled["age_scr"].value_counts().to_dict() == TABLE_11["age_scr"]
    assert df["edu_scr"].astype(int).value_counts().to_dict() == TABLE_11["edu_scr_codes"]
    in_models = df[df["gender_scr"] != 4]
    for name, vars_ in (("false_acc", gen.FALSE_VARS), ("true_acc", gen.TRUE_VARS)):
        n = sum(
            int((gen.assigned_arm(in_models, v).notna() & in_models[f"{v}_acc"].notna()).sum())
            for v in vars_
        )
        assert (n, in_models["psid"].nunique()) == AUTHORS_OBS[name]


def _synthetic(arms: dict[str, list[float | None]], answers: list[float | None]) -> pd.DataFrame:
    var = "post_1"
    cols: dict[str, Any] = {
        gen.arm_column(var, s): arms.get(s, [None] * len(answers)) for s, *_ in gen.ARMS
    }
    for dv, *_ in gen.DVS:
        cols[f"{var}_{dv}"] = answers
    return pd.DataFrame(cols)


def test_assigned_arm_reads_one_arm_and_refuses_two_or_none() -> None:
    ok = _synthetic({"control": [1, None], "scp": [None, 1]}, [2, 3])
    assert gen.assigned_arm(ok, "post_1").tolist() == [0, 3]
    with pytest.raises(SystemExit, match="two arms"):
        gen.assigned_arm(_synthetic({"sc": [1], "sca": [1]}, [2]), "post_1")
    with pytest.raises(SystemExit, match="no arm"):
        gen.assigned_arm(_synthetic({}, [2]), "post_1")


@needs_raw
def test_double_drawn_posts_and_only_those_are_left_out() -> None:
    df = gen.deposit()
    wide = gen.wide().set_index(gen.ID_VAR)
    pairs = 0
    for p in gen.POSTS:
        var = p["var"]
        arm = gen.assigned_arm(df, var)
        dd = gen.double_drawn(df, var)
        pairs += int(dd.sum())
        assert not (dd & arm.isna()).any(), var  # a double draw was always shown
        cond = wide[gen.cond_var(var)].reindex(df[gen.ID_VAR])
        cond.index = df.index
        assert cond[dd].isna().all(), var
        shown = arm.notna() & ~dd
        p_index = gen.POSTS.index(p)
        assert (cond[shown] == arm[shown] + p_index * 4 + 1).all(), var
    assert pairs == 1888
    # true posts are fixed blocks, never double drawn
    assert not any(gen.double_drawn(df, v).any() for v in gen.TRUE_VARS)


def test_each_arm_quotes_its_own_picture() -> None:
    rec = load(RECIPE)
    assert rec.condition.factors == ["post", "comment"]
    assert len(rec.condition.arms) == 52
    by_num = {a.condition_num: a for a in rec.condition.arms}
    for p_index, p in enumerate(gen.POSTS):
        texts = {}
        for _, a_index, level, kind in gen.ARMS:
            arm = by_num[p_index * 4 + a_index]
            assert arm.raw == p_index * 4 + a_index + 1
            assert arm.factors == {"post": p["key"], "comment": level}
            assert arm.images == [f"4hjcf_{p['key']}_{kind}"]
            assert arm.text.count(images_mod.IMAGE_MARKER) == 1
            words = gen.text_in_image(p["key"], kind)
            partial = (
                " (not every word in it is quoted here)" if gen.unquoted(p["key"], kind) else ""
            )
            assert arm.text == f'You are shown a social media post{partial}: "{words}" <image>'
            texts[kind] = words
        # the post itself is the same in every arm; the comments are added after it
        head = re.split(r" / (?:View more|Write a comment)", texts["control"])[0]
        for kind in ("low", "high", "link"):
            assert texts[kind].startswith(head), (p["key"], kind)
            assert len(texts[kind]) > len(texts["control"]), (p["key"], kind)
        assert len(set(texts.values())) == 4, p["key"]
        # the link arm is the high arm plus a link card
        assert len(texts["link"]) > len(texts["high"]), p["key"]


# Words legible at native resolution that an earlier transcription left out (checker,
# 10 Nov 2026); each must now be quoted in its picture's condition.
LEGIBLE = {
    ("false01", "*"): ["NHS Test and Trace"],
    ("false02", "*"): ["Moderna COVID-19 Vaccine"],
    ("false02", "link"): ["HEALTH / CORONAVIRUS", "21 OCTOBER 2021"],
    ("false05", "*"): ["TOKATU NELSON"],
    ("false05", "link"): ["ONLINE", "10 NOVEMBER 2021"],
    ("false06", "*"): ["YADX166", "aggreko"],
    ("false08", "link"): ["By Reuters Fact Check"],
    ("false10", "*"): ["Pfizer"],
    ("false12", "link"): [
        "FACT CHECK",
        "Ella Lee",
        "Published 6:39 p.m. ET Feb. 25, 2022 | Updated 2:59 p.m. ET Feb. 27, 2022",
    ],
    ("false13", "link"): ["The Poynter Institute", "By Samantha Putterman", "March 14, 2022"],
    ("true01", "*"): ["COVID-19 VACCINE"],
    ("true02", "link"): ["CHD.TV", "Dr. Peter A. McCullough, MD, MPH"],
    ("true03", "link"): ["May 01, 2022"],
}


def test_legible_words_are_quoted_and_omissions_declared() -> None:
    for (key, arm), blocks in LEGIBLE.items():
        for kind in ("control", "low", "high", "link") if arm == "*" else (arm,):
            got = gen.words(key, kind)
            for b in blocks:
                assert b in got, (key, kind, b)
    # every declared omission names a real post and arm, and reaches the description
    for key, arms in gen.UNQUOTED.items():
        assert key in {p["key"] for p in gen.POSTS}
        for arm in arms:
            assert arm in {"*", "control", "low", "high", "link"}
        for kind in ("control", "low", "high", "link"):
            missing = gen.unquoted(key, kind)
            if missing:
                assert gen.description(key, kind).endswith(f"Words not transcribed: {missing}.")
    assert gen.unquoted("false01", "link") is None
    assert gen.unquoted("false08", "low") is None
    assert gen.unquoted("false08", "link")


def test_outcomes_follow_each_posts_assignment() -> None:
    rec = load(RECIPE)
    assert len(rec.outcomes) == 39
    for o in rec.outcomes:
        var, dv = o.var.rsplit("_", 1)
        assert o.condition_var == f"{var}_cond"
        assert (o.scale.min, o.scale.max) == ((1, 4) if dv == "acc" else (1, 5))


@needs_built
def test_built_rows() -> None:
    d = pd.read_parquet(BUILT)
    assert len(d) == 44_428
    assert d["participant_id"].nunique() == 2_094
    assert d["condition_num"].nunique() == 52
    rec = load(RECIPE)
    by_num = {a.condition_num: a for a in rec.condition.arms}
    task_post = {o.task_num: o.var.rsplit("_", 1)[0] for o in rec.outcomes}
    for num, g in d.groupby("condition_num"):
        arm = by_num[int(num)]
        assert {tuple(x) for x in g["condition_images"]} == {tuple(arm.images)}
        post = next(p["var"] for p in gen.POSTS if p["key"] == arm.factors["post"])
        assert {task_post[int(t)] for t in g["task_num"]} == {post}
    assert d["response_num"].between(d["scale_min"], d["scale_max"]).all()


@needs_built
def test_built_parquet_is_current(tmp_path: Path) -> None:
    """The answer-key tests read the parquet on disk, so a stale build would let a
    generator change (e.g. two pictures swapped between arms) pass them unseen.
    Rebuild from the current recipe in memory and require the same rows."""
    from micromotives_datasets import cli

    rec, rows, _ = cli._load_and_build(RECIPE)
    fresh = pd.read_parquet(cli._write_parquet(rows, tmp_path, rec))
    on_disk = pd.read_parquet(BUILT)
    assert fresh.equals(on_disk), "4hjcf.parquet is stale: rebuild with mmds build"
