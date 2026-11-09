"""The egmxd recipe (TESS 1443, Wolfson: a fast-food menu with QR codes, green
low-climate-impact labels or red high-climate-impact labels) and its answer key.

The generator reads the menu screen's words, the follow-up questions and which picture
each SHOW IF block embeds out of both fielded questionnaires (asserting they agree),
folds the fourteen 0/1 click variables into one `MENU_ITEM`, and carries the words on
each menu as a transcription. These tests stop a hand edit drifting from it, and check
the facts the rows rest on:

- each arm shows the picture its own SHOW IF block embeds, in both questionnaires, and
  that picture is the proposal's picture for the same arm;
- the three menus differ only in the key at the top and the label strips, and the
  transcription puts each label under exactly the items the picture labels;
- the hot-spot regions are the transcribed item names, in the same order;
- each follow-up's condition is the menu plus every question asked before it,
  narrated as asked and never as answered;
- the built rows reconcile exactly with SocSci210 (fetched 9 Nov 2026 by
  `mmds build --crosscheck` and transcribed here): their fourteen yes/no rows per
  person are our one menu answer, item by item and arm by arm; Q3, Q4, Q5 and Q6
  agree cell for cell (condition x response).

Tests needing the gitignored deposit, the derived .sav or the build skip on a fresh
clone.
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from micromotives_datasets import images as images_mod
from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_egmxd.py"
RECIPE = REPO / "recipes" / "images" / "egmxd.yaml"
RAW = REPO / "data" / "raw" / "egmxd"
DTA = RAW / "9089_TESS-Wolfson108_20220420.dta"
CODED = RAW / "egmxd_coded.sav"
BUILT = REPO / "data" / "processed" / "images" / "egmxd.parquet"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_egmxd", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not DTA.exists(), reason="egmxd deposit not fetched")
needs_coded = pytest.mark.skipif(not CODED.exists(), reason="egmxd --prep not run")
needs_built = pytest.mark.skipif(not (BUILT.exists() and CODED.exists()), reason="egmxd not built")
needs_sips = pytest.mark.skipif(not shutil.which("sips"), reason="needs macOS sips")

# SocSci210, study egmxd (mmds build --crosscheck, 9 Nov 2026). Their task 0 is one
# yes/no row per person per item; these are their "yes" rows by item and condition.
SOCSCI210_ROWS = 90_977
SOCSCI210_PEOPLE = 5_055
SOCSCI210_PER_TASK = {0: 70_770, 1: 5_053, 2: 5_052, 3: 5_051, 4: 5_051}
SOCSCI210_YES = {
    "Whopper": (261, 203, 120),
    "Impossible Whopper": (108, 100, 111),
    "Whopper Jr.": (140, 138, 131),
    "Double Whopper with Cheese": (113, 114, 187),
    "Bacon Double Cheeseburger": (229, 204, 68),
    "Cheeseburger": (113, 93, 194),
    "Crispy Chicken Sandwich": (117, 135, 150),
    "Spicy Crispy Chicken Sandwich": (154, 167, 174),
    "Original Chicken Sandwich": (87, 89, 110),
    "Chicken Jr.": (17, 33, 33),
    "10 Pc Nuggets": (44, 44, 57),
    "Big Fish": (96, 119, 137),
    "Chicken Garden Salad": (133, 185, 171),
    "Side Garden Salad": (55, 47, 74),
}
# Their tasks 1-4 (Q3, Q4, Q5, Q6) are our tasks 1-4: condition -> responses 1..n.
SOCSCI210_CELLS = {
    1: [[665, 256, 625, 93, 27], [541, 280, 562, 216, 71], [510, 248, 468, 328, 163]],
    2: [
        [245, 512, 418, 205, 145, 106, 35],
        [219, 455, 447, 192, 176, 130, 51],
        [241, 479, 439, 209, 148, 140, 60],
    ],
    3: [[202, 153, 299, 523, 489], [193, 170, 294, 539, 473], [178, 140, 298, 545, 555]],
    4: [[36, 102, 303, 805, 420], [45, 77, 303, 788, 456], [39, 92, 306, 780, 499]],
}


@needs_coded
def test_recipe_is_what_the_generator_writes() -> None:
    assert RECIPE.read_text() == gen.render()


@needs_raw
def test_catalogue_entries_are_what_the_generator_derives() -> None:
    cat = images_mod.load()
    for image_id, entry in gen.catalogue_entries().items():
        assert cat[image_id].model_dump() == entry, image_id
        assert not images_mod.problems(image_id, cat), image_id


@needs_raw
def test_each_menu_is_its_show_if_blocks_picture_in_both_questionnaires() -> None:
    q, pg = gen.instrument(gen.SIMPLE), gen.instrument(gen.PROG)
    expected = {
        "Q1A": (1, "word/media/image3.png", "word/media/image3.png", "9089.108_MenuA.png"),
        "Q1B": (2, "word/media/image4.png", "word/media/image4.png", "9089.108_MenuB.png"),
        "Q1C": (3, "word/media/image5.png", "word/media/image5.png", "9089.108_MenuC.png"),
    }
    with zipfile.ZipFile(gen.SIMPLE) as zs, zipfile.ZipFile(gen.PROG) as zp:
        for block, (cond, member_q, member_pg, name) in expected.items():
            assert q["menus"][block] == (cond, [member_q], [])
            assert pg["menus"][block] == (cond, [member_pg], [name])
            assert zs.read(member_q) == zp.read(member_pg)
            key = gen.MENUS[cond - 1][0]
            assert (RAW / "images" / f"menu_{key}.png").read_bytes() == zs.read(member_q)
    # three different pictures
    assert len({gen.menu_member(m[0]) for m in gen.MENUS}) == 3


@needs_raw
@needs_sips
def test_the_proposal_prints_the_same_menus_and_they_differ_only_in_their_labels() -> None:
    checks = gen.picture_checks()
    for key, dist in checks["proposal"].items():
        assert min(dist, key=dist.__getitem__) == key, (key, dist)
        assert dist[key] <= 12 and min(v for k, v in dist.items() if k != key) >= 100
    allowed = set(gen.KEY_ROWS).union(*map(set, gen.STRIP_ROWS))
    for key, rows in checks["differ"].items():
        assert rows and set(rows) <= allowed, key
        assert set(rows) & set(gen.KEY_ROWS), key  # the key at the top always differs


@needs_raw
def test_hot_spot_regions_are_the_transcribed_items_and_the_timers_name_the_arms() -> None:
    _, _, col_labels = gen.read_dta()
    names = gen.region_names(col_labels)
    assert names == {letter: [t[0] for t in gen.TILES] for letter in "ABC"}
    for _, _, label, letter, _, _ in gen.MENUS:
        assert col_labels[f"Q1{letter}_TIMER_Page_Submit"].startswith(f"[{label}]")


def test_labels_sit_under_exactly_the_items_the_design_names() -> None:
    names = [t[0] for t in gen.TILES]
    beef = {"Whopper", "Whopper Jr.", "Double Whopper with Cheese"}
    beef |= {"Bacon Double Cheeseburger", "Cheeseburger"}

    def labelled(key: str, label: str) -> set[str]:
        parts = gen.text_in_image(key).split(" / ")
        return {parts[i - 2] for i, p in enumerate(parts) if p == label and i >= 2}

    assert labelled("high_impact", "HIGH CLIMATE IMPACT") - {"CO2"} == beef
    assert labelled("low_impact", "LOW CLIMATE IMPACT") - {"CO2"} == set(names) - beef
    assert "CLIMATE" not in gen.text_in_image("control")
    for key, *_ in gen.MENUS:
        text = gen.text_in_image(key)
        # every item, its price and calories, in reading order, in every menu
        order = [text.index(f"/ {name} / {price}") for name, price in gen.TILES]
        assert order == sorted(order), key
        assert text.count("Cal.") == 14


def test_each_arm_quotes_its_menu_and_shows_its_picture() -> None:
    rec = load(RECIPE)
    assert rec.condition.shared_context == "This survey is about restaurant menus."
    assert sorted(a.raw or 0 for a in rec.condition.arms) == [1, 2, 3]
    for arm in rec.condition.arms:
        assert arm.raw is not None
        key = gen.MENUS[arm.raw - 1][0]
        assert arm.condition_num == arm.raw - 1
        assert arm.factors == {"label": key}
        assert arm.images == [f"egmxd_menu_{key}"]
        assert arm.text == f'{gen.LEAD} "{gen.text_in_image(key)}" <image>'
        assert arm.text.count(images_mod.IMAGE_MARKER) == 1
    texts = {a.raw: a.text for a in rec.condition.arms}
    assert "Scan the QR code" in texts[1] and "CLIMATE" not in texts[1]
    assert "LOW CLIMATE IMPACT" in texts[2] and "HIGH" not in texts[2]
    assert "HIGH CLIMATE IMPACT" in texts[3] and "LOW" not in texts[3]


def test_outcomes_are_the_menu_and_the_four_follow_ups() -> None:
    rec = load(RECIPE)
    assert [(o.var, o.task_num) for o in rec.outcomes] == [
        ("MENU_ITEM", 0),
        ("Q3", 1),
        ("Q4", 2),
        ("Q5", 3),
        ("Q6", 4),
    ]
    menu = rec.outcomes[0]
    assert menu.scale.nominal and (menu.scale.min, menu.scale.max) == (1, 14)
    assert menu.question.startswith("Imagine you are at a restaurant and about to order dinner.")
    for i, (name, _) in enumerate(gen.TILES, start=1):
        assert f'{i} means "{name}"' in menu.question
    for task in (1, 3, 4):  # coded 2-6 in the data
        assert rec.outcomes[task].response_recode == {2: 1, 3: 2, 4: 3, 5: 4, 6: 5}
    assert rec.outcomes[3].question.endswith("I am concerned about climate change.")
    # Q's words, not PG's "isimportant"
    assert rec.outcomes[4].question.endswith(
        "Making healthy food and beverage choices is important to me."
    )
    # the manipulation check is not built
    assert "notice any labels" not in " ".join(o.question for o in rec.outcomes)


def test_each_follow_up_states_only_what_was_shown_and_asked_before_it() -> None:
    rec = load(RECIPE)
    questions = {o.task_num: o.question for o in rec.outcomes}
    q2 = "Did you notice any labels (other than calories) next to or below the menu items?"
    for arm in rec.condition.arms:
        assert set(arm.items) == {1, 2, 3, 4}
        for task, item in arm.items.items():
            text = item.condition_text or ""
            assert text.startswith(arm.text + " You were asked: ")
            assert text.count(images_mod.IMAGE_MARKER) == 1
            quoted = re.findall(r'(?:You were asked|Then you were asked): "([^"]*)"', text)
            # the menu screen, Q2, then every built follow-up before this one, in order
            menu = questions[0].split(' 1 means "')[0]
            assert quoted == [menu, q2, *(questions[t] for t in range(1, task))]
            # asked, never answered: no answer option or item name follows the menu
            after = text[len(arm.text) :]
            ours = re.sub(r'"[^"]*"', '""', after)  # our words only, quotations removed
            assert ours.strip() == " ".join(
                ['You were asked: ""'] + ['Then you were asked: ""'] * (len(quoted) - 1)
            )
            assert not re.search(r"\b(you (chose|ordered|answered|said|selected|picked))\b", ours)
            for name, _ in gen.TILES:
                assert f'"{name}"' not in after


def test_the_answered_check_catches_and_passes() -> None:
    pattern = r"\b(you (chose|ordered|answered|said|selected|picked))\b"
    assert re.search(pattern, 'You were asked: "x" and you chose "Whopper".')
    assert not re.search(pattern, 'You were asked: "click on the ONE item you want to order"')


# Our descriptions are neutral and name no brand: words that would judge the food or
# name its maker.
FORBIDDEN = (
    r"\b(burger king|bk|mcdonald\w*|tasty|delicious|appeti[sz]ing|mouth-?watering|"
    r"healthy|unhealthy|greasy|junk|cheap|expensive|sustainable|bad|good|better|worse)\b"
)


def _offending(text: str) -> list[str]:
    return re.findall(FORBIDDEN, text.lower())


def test_the_forbidden_words_check_catches_and_passes() -> None:
    assert _offending("A Burger King menu of tasty, unhealthy food.") == [
        "burger king",
        "tasty",
        "unhealthy",
    ]
    assert _offending("Cheap and appetizing.") == ["cheap", "appetizing"]
    # what it must not catch: the menu's own capitals quoted, and words containing these
    assert _offending("LOW CLIMATE IMPACT labels; goodness; a badge; buns with lettuce") == []


def test_descriptions_are_neutral_and_quote_nothing_unprinted() -> None:
    for key, text in gen.DESCRIPTIONS.items():
        assert not _offending(text), (key, _offending(text))
        assert "Every word is quoted in text_in_image." in text
        # every capitalised phrase it quotes is on that menu
        for phrase in re.findall(r"\b[A-Z][A-Z&0-9 ]{2,}[A-Z0-9]\b", text):
            assert phrase in gen.text_in_image(key), (key, phrase)


@needs_coded
def test_menu_item_is_the_one_region_each_person_clicked() -> None:
    df, _, _ = gen.read_dta()
    coded = gen.read_any(CODED).df
    assert coded["CaseId"].tolist() == df["CaseId"].tolist()
    for _, cond, _, letter, _, _ in gen.MENUS:
        mine = df["P_COND"] == cond
        own = df.loc[mine, [f"Q1{letter}_{k}" for k in range(1, 15)]]
        assert (own.sum(axis=1) == 1).all()
        clicked = own.to_numpy().argmax(axis=1) + 1
        assert coded.loc[mine, "MENU_ITEM"].tolist() == clicked.astype(float).tolist()
    for var in ("P_COND", "Q3", "Q4", "RELIG", "AGE", "INCOME"):
        assert coded[var].equals(df[var].astype(float)), var


@needs_built
def test_rows_reconcile_exactly_with_socsci210() -> None:
    rows = pd.read_parquet(BUILT)
    assert rows["participant_id"].nunique() == SOCSCI210_PEOPLE
    menu = rows[rows["task_num"] == 0]
    assert len(menu) == SOCSCI210_PEOPLE  # one answer each
    # their fourteen yes/no rows per person are our one answer per person
    assert SOCSCI210_PER_TASK[0] == 14 * len(menu)
    names = [t[0] for t in gen.TILES]
    ours = menu.groupby(["response_num", "condition_num"]).size()
    for i, name in enumerate(names, start=1):
        assert tuple(int(ours.get((float(i), c), 0)) for c in range(3)) == SOCSCI210_YES[name]
    for task, cells in SOCSCI210_CELLS.items():
        t = rows[rows["task_num"] == task]
        ours_cells = pd.crosstab(t["condition_num"], t["response_num"].astype(int))
        assert ours_cells.values.tolist() == cells, task
        assert [int(c) for c in ours_cells.columns] == list(range(1, len(cells[0]) + 1))
        assert len(t) == SOCSCI210_PER_TASK[task]
    # the whole gap is their task-0 shape: fourteen rows per person where we have one
    assert SOCSCI210_ROWS - SOCSCI210_PER_TASK[0] + len(menu) == len(rows) == 25_262


@needs_built
def test_every_person_sees_one_menu() -> None:
    rows = pd.read_parquet(BUILT)
    per = rows.groupby("participant_id")["condition_num"].nunique()
    assert (per == 1).all()
    images = rows.groupby("condition_num")["condition_images"].first().map(list)
    assert images.to_dict() == {
        0: ["egmxd_menu_control"],
        1: ["egmxd_menu_low_impact"],
        2: ["egmxd_menu_high_impact"],
    }


@needs_built
def test_built_parquet_is_current(tmp_path: Path) -> None:
    """The answer-key tests read the parquet on disk, so a stale build would let a
    generator change (two menus swapped between arms, say) pass them unseen. Rebuild
    from the current recipe in memory and require the same rows."""
    from micromotives_datasets import cli

    rec, rows, _ = cli._load_and_build(RECIPE)
    fresh = pd.read_parquet(cli._write_parquet(rows, tmp_path, rec))
    on_disk = pd.read_parquet(BUILT)
    assert fresh.equals(on_disk), "egmxd.parquet is stale: rebuild with mmds build"
