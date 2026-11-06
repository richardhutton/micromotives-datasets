"""The a4y7s Study 2 recipe (IMG69, AI labels on headline cards, UK sample) and its answer key.

The generator reads the instruction screens, the outcome wording and the card shown
by every question out of the fielded .qsf, reshapes the Qualtrics export to one row
per UK person per card, and quotes the words on each card; these tests stop a hand
edit drifting from it, and check the facts the rows rest on:

- each arm shows ONE card, quotes the catalogue's transcription of it, and carries the
  definition (and its reminder) only in the Weak, Medium and Strong arms;
- the Control and No Definition rows for the same unlabelled card are one condition,
  because their words and picture are identical;
- every person's twenty rows are ten different stories x two questions;
- the built rows reproduce the authors' own long file (data_clean.xlsx, their
  Script_clean.R) for the UK sample: the same 1,500 people, and every one of the
  30,000 ratings on the same card and question. That file is the only UK-specific
  reference: the paper (Altay & Gilardi 2024, PNAS Nexus pgae403) prints pooled US+UK
  model estimates and draws the UK ones only in figures (S8-S10). Its sample size is
  checked: 3,003 recruited, two excluded, 3,001 analysed.
- where the authors' file and ours disagree about a card, it is exactly the two survey
  slots whose export tag misdescribes the graphic shown, and nothing else.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_a4y7s_study2.py"
RECIPE = REPO / "recipes" / "images" / "a4y7s_study2.yaml"
RAW = REPO / "data" / "raw" / "a4y7s"
BUILT = REPO / "data" / "processed" / "images" / "a4y7s_study2.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_a4y7s_study2", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.DATA_XLSX.exists(), reason="a4y7s deposit not fetched")
needs_built = pytest.mark.skipif(
    not (BUILT.exists() and gen.DATA_XLSX.exists()), reason="a4y7s study 2 not built"
)

DEFINITION_WORDS = {
    "weak": "AI was used to improve the clarity of the text",
    "medium": "AI wrote a first draft of the article",
    "strong": "AI wrote the whole article",
}


@needs_raw
def test_recipe_is_what_the_generator_writes() -> None:
    assert RECIPE.read_text() == gen.render()


@needs_raw
def test_the_coded_spreadsheet_is_what_prep_derives() -> None:
    coded = pd.read_excel(gen.DATA)
    pd.testing.assert_frame_equal(gen.prep(), coded, check_dtype=False)


@needs_raw
def test_catalogue_entries_are_what_the_generator_derives() -> None:
    cat = images_mod.load()
    entries = gen.catalogue_entries()
    assert len(entries) == 30
    for image_id, entry in entries.items():
        assert cat[image_id].model_dump() == entry, image_id
        assert not images_mod.problems(image_id, cat), image_id


@needs_raw
@pytest.mark.skipif(shutil.which("sips") is None, reason="needs macOS sips")
def test_each_qualtrics_graphic_is_the_card_it_is_mapped_to() -> None:
    dist = gen.verify_graphics()
    assert len(dist) == 39 and max(dist.values()) < 1.0


@needs_raw
def test_the_two_mistagged_slots_show_the_ai_written_vaccine_card() -> None:
    """The finding the crosscheck's two disagreements rest on, read from the .qsf."""
    tenth = {b: gen.slots(b)[9] for b in ("Control_B", "Label_A")}
    assert tenth["Control_B"]["sha_tag"] == "1_t_AI_nol_sha"
    assert tenth["Label_A"]["sha_tag"] == "10_f_h_nol_sha"
    assert tenth["Control_B"]["graphic"] == tenth["Label_A"]["graphic"] == "IM_5cjysoBnzLwsJSe"
    assert gen.GRAPHIC_PICTURE["IM_5cjysoBnzLwsJSe"] == ("cdc_vaccine", "ai")


def test_each_arm_quotes_and_shows_its_own_card() -> None:
    rec = load(RECIPE)
    cat = images_mod.load()
    arms = rec.condition.arms
    assert sorted(a.condition_num for a in arms) == list(range(90))
    assert len({(a.text, tuple(a.images)) for a in arms}) == 90
    for arm in arms:
        f = arm.factors
        story, version = f["story"], f["version"]
        assert arm.images == [
            f"a4y7s_s2_{story}_"
            + {"human-written": "human", "AI-written": "ai"}[version]
            + ("_labelled" if f["label"] == "yes" else "")
        ]
        assert arm.text.count(images_mod.IMAGE_MARKER) == 1
        words = cat[arm.images[0]].text_in_image
        assert words and f'"{words}" <image>' in arm.text
        assert (gen.LABEL_WORDS in arm.text) == (f["label"] == "yes")
        for level, phrase in DEFINITION_WORDS.items():
            assert (phrase in arm.text) == (f["definition"] == level), arm.condition_num
        if f["definition"] == "none":
            assert arm.text.startswith("One of the headlines: ")
        else:
            assert arm.text.count(phrase := DEFINITION_WORDS[f["definition"]]) == 2, phrase
            assert "As a reminder, AI-generated headlines means that:" in arm.text
    assert rec.condition.shared_context == (
        "Some headlines may be human-generated while others may be generated by artificial "
        "intelligence (AI). If you see AI-generated headlines, they will be explicitly "
        "labeled as such."
    )


def test_arm_counts_per_definition() -> None:
    rec = load(RECIPE)
    per: dict[tuple[str, str], int] = {}
    for a in rec.condition.arms:
        k = (a.factors["definition"], a.factors["label"])
        per[k] = per.get(k, 0) + 1
    assert per == {
        ("none", "no"): 20,
        ("none", "yes"): 10,
        **{(d, "yes"): 10 for d in ("weak", "medium", "strong")},
        **{(d, "no"): 10 for d in ("weak", "medium", "strong")},
    }
    # In the labelled arms, the one unlabelled AI-written card is the vaccine card.
    unlabelled_ai = {
        (a.factors["definition"], a.factors["story"])
        for a in rec.condition.arms
        if a.factors["version"] == "AI-written"
        and a.factors["label"] == "no"
        and a.factors["definition"] != "none"
    }
    assert unlabelled_ai == {(d, "cdc_vaccine") for d in ("weak", "medium", "strong")}


def test_control_and_no_definition_share_only_identical_cards() -> None:
    """An arm listing two raw codes merges a Control card (1xx) with the same card in
    No Definition (2xx), never anything else."""
    rec = load(RECIPE)
    merged = [a for a in rec.condition.arms if a.raws]
    assert len(merged) == 10
    for a in merged:
        assert len(a.raws) == 2
        c, z = sorted(a.raws)
        assert c // 100 == 1 and z // 100 == 2 and c % 100 == z % 100
        assert a.factors["label"] == "no" and a.factors["definition"] == "none"


def test_no_row_says_where_its_card_sat() -> None:
    """Our words never place the card in the sequence ("the first headline", "10 news
    headlines"). The Medium definition's "first draft" is the source's and is not a
    position, so the check is on position words next to a sequence noun."""
    rec = load(RECIPE)
    ordinal = (
        r"(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|next|previous|last)"
    )
    noun = r"(headlines?|cards?|posts?|pages?|screens?)"
    pattern = re.compile(rf"\b{ordinal}\s+(news\s+)?{noun}\b|\b(10|ten)\s+(news\s+)?{noun}\b")
    for arm in rec.condition.arms:
        # Our words only: the card's own words are quoted, and one says "the Next Day".
        text = rec.condition.render(arm).split(gen.LEAD)[0].lower()
        assert not pattern.search(text), arm.text
    assert pattern.search("next, you will be presented with 10 news headlines")
    assert pattern.search("the second headline")
    assert not pattern.search("ai wrote a first draft of the article")


def test_the_outcomes_are_sharing_then_accuracy() -> None:
    rec = load(RECIPE)
    assert [o.question for o in rec.outcomes] == [
        "If you saw this post online, how likely would you be to share it?",
        "How accurate is the claim in the above headline?",
    ]
    assert [(o.scale.min, o.scale.max) for o in rec.outcomes] == [(1, 6), (1, 6)]
    assert [(o.scale.min_label, o.scale.max_label) for o in rec.outcomes] == [
        ("Extremely unlikely", "Extremely likely"),
        ("Certainly false", "Certainly true"),
    ]


@needs_built
def test_every_person_rates_ten_stories_twice() -> None:
    rows = pd.read_parquet(BUILT)
    assert len(rows) == 1500 * 10 * 2
    rows["story"] = rows["factors"].map(
        lambda f: json.loads(f)["story"] if isinstance(f, str) else f["story"]
    )
    per = rows.groupby("participant_id").agg(
        n=("condition_num", "size"),
        conds=("condition_num", "nunique"),
        stories=("story", "nunique"),
        tasks=("task_num", lambda t: tuple(sorted(t.value_counts().to_dict().items()))),
    )
    assert (per["n"] == 20).all() and (per["conds"] == 10).all() and (per["stories"] == 10).all()
    assert (per["tasks"] == ((0, 10), (1, 10))).all()


def _authors_uk() -> pd.DataFrame:
    """The authors' long file, UK rows, keyed to our pid and condition_num."""
    clean = pd.read_excel(gen.AUTHORS_CLEAN)
    clean = clean[clean["Country"] == "UK"].copy()
    names, raw = gen.raw_export()
    col = {n: i for i, n in enumerate(names) if names.count(n) == 1}
    keep = gen.kept(names, raw)
    pid_of = {raw.loc[i, col["PROLIFIC_PID"]]: i + 1 for i in raw.index[keep]}
    arm_of = {
        "Control": 1,
        "Treatment_ZERO": 2,
        "Treatment_Weak": 3,
        "Treatment_Medium": 4,
        "Treatment_Strong": 5,
    }
    by_tag = {b: {s["sha_tag"]: s for s in gen.slots(b)} for b in gen.CARD_BLOCKS}
    rec = load(RECIPE)
    num_of = {code: a.condition_num for a in rec.condition.arms for code in (a.raws or [a.raw])}
    clean["pid"] = clean["PROLIFIC_PID"].map(pid_of)
    clean["block"] = (
        clean["Condition"].map(lambda c: "Control" if c == "Control" else "Label")
        + "_"
        + clean["Set"]
    )
    clean["sha_tag"] = clean["ITEM"].str.replace(r"_acc$", "_sha", regex=True)
    clean["picture"] = [
        by_tag[b][t]["picture"] for b, t in zip(clean["block"], clean["sha_tag"], strict=True)
    ]
    clean["condition_num"] = [
        num_of[arm_of[c] * 100 + gen.picture_index(*p)]
        for c, p in zip(clean["Condition"], clean["picture"], strict=True)
    ]
    clean["task_num"] = clean["DV"].map({"Sharing": 0, "Accuracy": 1})
    return clean


@needs_built
def test_every_rating_matches_the_authors_long_file() -> None:
    ours = pd.read_parquet(BUILT)
    ours["pid"] = ours["participant_id"].str.split(":").str[-1].astype(int)
    theirs = _authors_uk()
    assert theirs["pid"].notna().all() and theirs["pid"].nunique() == 1500
    assert len(theirs) == len(ours) == 30000
    key = ["pid", "condition_num", "task_num"]
    m = ours[[*key, "response_num"]].merge(
        theirs[[*key, "Ratings"]], on=key, how="outer", indicator=True, validate="one_to_one"
    )
    assert (m["_merge"] == "both").all()
    assert (m["response_num"] == m["Ratings"]).all()


@needs_raw
def test_the_authors_card_coding_differs_only_at_the_two_mistagged_slots() -> None:
    theirs = _authors_uk()
    veracity = {s: v for s, (v, _, _) in gen.STORIES.items()}
    ours_ver = theirs["picture"].map(lambda p: veracity[p[0]] == "true")
    ours_ai = theirs["picture"].map(lambda p: "Human" if p[1] == "human" else "AI")
    ours_label = theirs["picture"].map(lambda p: "Yes" if p[1] == "ai_labelled" else "No")
    differs = (
        (ours_ver != theirs["Veracity"].astype(bool))
        | (ours_ai != theirs["AI_Human"])
        | (ours_label != theirs["Label"])
    )
    slots = set(zip(theirs.loc[differs, "block"], theirs.loc[differs, "sha_tag"], strict=True))
    assert slots == {("Control_B", "1_t_AI_nol_sha"), ("Label_A", "10_f_h_nol_sha")}
    cb = differs & (theirs["block"] == "Control_B")
    la = differs & (theirs["block"] == "Label_A")
    # Control_B: authors say true, the card is the false vaccine claim (AI-written either way).
    assert theirs.loc[cb, "Veracity"].astype(bool).all() and not ours_ver[cb].any()
    assert (theirs.loc[cb, "AI_Human"] == ours_ai[cb]).all()
    # Label_A: authors say human-written, the card is the AI-written version, unlabelled.
    assert (theirs.loc[la, "AI_Human"] == "Human").all() and (ours_ai[la] == "AI").all()
    assert (theirs.loc[la, "Label"] == ours_label[la]).all()
    assert (int(cb.sum()), int(la.sum())) == (150 * 2, (154 + 150 + 146 + 149) * 2)


@needs_raw
def test_sample_size_matches_the_paper() -> None:
    """Paper, Study 2: 3,003 recruited, two excluded for the attention check."""
    names, raw = gen.raw_export()
    assert int(gen.kept(names, raw).sum()) == 3003 - 2
    clean = pd.read_excel(gen.AUTHORS_CLEAN)
    assert clean.groupby("Country")["PROLIFIC_PID"].nunique().to_dict() == {"UK": 1500, "US": 1500}


@needs_built
def test_built_parquet_is_current(tmp_path: Path) -> None:
    """The answer-key tests read the parquet on disk, so a stale build would let a
    generator change (e.g. the accuracy answers attached to the wrong card) pass them
    unseen. Rebuild from the current recipe in memory and require the same rows."""
    from micromotives_datasets import cli

    rec, rows, _ = cli._load_and_build(RECIPE)
    fresh = pd.read_parquet(cli._write_parquet(rows, tmp_path, rec))
    on_disk = pd.read_parquet(BUILT)
    assert fresh.equals(on_disk), "a4y7s_study2.parquet is stale: rebuild with mmds build"
