"""IP 9.10 — the housework scenarios, waves 5 and 6.

Three things here could go wrong quietly, and each has a test:

1. **The household join.** The five randomised dimensions live in
   `{w}_hhsamp_ip` and are joined to the person on `{w}_hidp`. A wrong join does
   not fail -- it renders a real scenario that this person never read. Wave 5
   duplicates four of the five into `indresp`, so the join is checkable there,
   and `--check` is run as a test rather than left as a thing someone might run.

2. **The condition text.** The archived value labels are wrong in three places
   (`ff_children = 2` says "age 6" for six MONTHS; `ff_housework = 2` and `= 4`
   share one label across opposite arrangements; `ff_paid_housework = 2` reads
   "o paid work"). The recipe transcribes the questionnaire instead, so the test
   asserts the clauses the labels would have got wrong.

3. **The panel link.** The same person answers in both waves, in two separate
   files. The row index would make them two unrelated participants.

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
GEN = REPO / "scripts" / "gen_ip_vig_housework.py"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"
RECIPES = {
    5: REPO / "recipes" / "ukds_6849_vig_housework_w5.yaml",
    6: REPO / "recipes" / "ukds_6849_vig_housework_w6.yaml",
}

needs_deposit = pytest.mark.skipif(
    not (STATA / "e_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not (REPO / "data" / "raw" / "ukds_6849" / "vig_housework_w5-derived.sav").exists(),
    reason="derived file not built — run scripts/gen_ip_vig_housework.py --write",
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_vig_housework", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_vig_housework"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows(wave: int) -> tuple:
    rec = recipe.load(RECIPES[wave])
    path = REPO / "data" / "raw" / "ukds_6849" / rec.data_file
    return tuple(build_rows(spss.read(path), rec))


# --- 1. the household join --------------------------------------------------


@needs_deposit
def test_wave_5s_two_copies_of_the_allocation_agree() -> None:
    """The only direct evidence the `hidp` join is right. 23,880 comparisons."""
    assert _generator().check("e") == 0


@needs_deposit
def test_every_respondent_matches_a_household_allocation_row() -> None:
    """`derive` raises rather than leaving a scenario to be guessed."""
    for letter in ("e", "f"):
        frame, _ = _generator().derive(letter)
        for dim in _generator().DIMS:
            assert frame[f"ff_{dim}1"].notna().all()


@needs_deposit
def test_pidp_is_never_written_to_the_derived_file() -> None:
    """It is the Understanding Society person identifier and links to the whole
    study. The derived file carries a hash of it instead."""
    for letter in ("e", "f"):
        frame, _ = _generator().derive(letter)
        assert "pidp" not in frame.columns
        assert frame["person"].str.startswith("ip_").all()


# --- 2. the condition text --------------------------------------------------


@needs_deposit
def test_the_clauses_the_archived_labels_get_wrong() -> None:
    """Six months not six years, and the two housework splits kept apart."""
    cond = recipe.load(RECIPES[5]).condition
    assert cond.template is not None
    levels = {n: d.levels for n, d in cond.template.dimensions.items()}
    assert levels["children"][2].text == "one child aged 6 months,"
    assert levels["housework"][2].text == (
        "your partner does three quarters of the housework while you do one quarter of it,"
    )
    assert levels["housework"][4].text == (
        "your partner does one quarter of the housework while you do three quarters of it,"
    )
    assert levels["housework"][2].text != levels["housework"][4].text
    assert levels["paid_help"][2].text == (
        "and you do not employ anybody to help with the housework."
    )


@needs_deposit
def test_both_waves_declare_the_same_template() -> None:
    """The wave 6 questionnaire carries the text character for character, so a
    difference here means one of them was re-transcribed and drifted."""
    five, six = (recipe.load(RECIPES[w]).condition.template for w in (5, 6))
    assert five is not None and six is not None
    assert five.model_dump() == six.model_dump()


# --- 3. the rows ------------------------------------------------------------


@needs_derived
def test_the_row_counts_are_what_both_code_paths_found() -> None:
    """4,550 and 5,081 were reached independently by a standalone builder and by
    the recipe pipeline. A change to either should have to explain itself."""
    assert len(_rows(5)) == 4550
    assert len(_rows(6)) == 5081


@needs_derived
def test_all_480_cells_occur_and_nobody_draws_one_twice() -> None:
    for wave in (5, 6):
        rows = _rows(wave)
        assert len({r.condition_num for r in rows}) == 480
        by_person: dict[str, list[int]] = {}
        for row in rows:
            by_person.setdefault(row.participant_id or "", []).append(row.condition_num or -1)
        repeats = [p for p, cells in by_person.items() if len(cells) != len(set(cells))]
        assert not repeats, f"wave {wave}: {len(repeats)} people drew one cell twice"


@needs_derived
def test_the_participant_id_is_the_persons_own_hash_not_the_row_index() -> None:
    """The panel link, and the first version of this test did not test it.

    Asserting that the two waves' id sets OVERLAP passes under the row-index
    fallback too -- `ukds_6849:0` exists in both files and names two different
    people -- so that test survived the mutation that ignores
    `participant_id_var` entirely. These two assertions do not: the id has to be
    the `person` column, and it has to survive the rows being reordered, which a
    row index cannot.
    """
    rec = recipe.load(RECIPES[5])
    path = REPO / "data" / "raw" / "ukds_6849" / rec.data_file
    people = set(spss.read(path).df["person"])
    ids = {r.participant_id or "" for r in _rows(5)}
    assert {i.split(":", 1)[1] for i in ids} <= people
    assert all(i.startswith(f"{rec.study_id}:ip_") for i in ids)

    shuffled = spss.read(path)
    shuffled.df = shuffled.df.sample(frac=1.0, random_state=0)
    assert {r.participant_id for r in build_rows(shuffled, rec)} == ids


@needs_derived
def test_the_same_person_spans_both_waves() -> None:
    """What the panel link buys: most people answered in both 2012 and 2013, so
    the same person's ratings can be compared across a year."""
    both = {r.participant_id for r in _rows(5)} & {r.participant_id for r in _rows(6)}
    assert len(both) > 1000, f"only {len(both)} people span both waves"


@needs_derived
def test_an_answer_is_always_paired_with_the_scenario_it_answered() -> None:
    """The condition text must express the factor levels the row claims, for
    every row -- not just for the arm table QC rule 5 inspects."""
    rec = recipe.load(RECIPES[5])
    assert rec.condition.template is not None
    dims = rec.condition.template.dimensions
    for row in _rows(5):
        for name, level in row.factors.items():
            wanted = next(v.text for v in dims[name].levels.values() if v.level == level)
            assert wanted in row.condition, f"{name}={level} not expressed in the condition"


@needs_derived
def test_the_persona_never_carries_a_sentinel_as_an_answer() -> None:
    """ "Employment: refusal" is worse than no employment."""
    for wave in (5, 6):
        for row in _rows(wave):
            values = [v for v in row.persona.model_dump().values() if isinstance(v, str)]
            for value in values + list(row.persona.extra.values()):
                assert value.lower() not in {
                    "missing",
                    "inapplicable",
                    "proxy",
                    "refusal",
                    "don't know",
                    "-9",
                    "-8",
                    "-7",
                    "-2",
                    "-1",
                }


# --- 4. the ceiling ---------------------------------------------------------


@needs_deposit
def test_the_wave_5_allocation_really_was_replicated_at_wave_6() -> None:
    """The User Guide's claim, tested rather than read past. It is what makes
    the ceiling below measurable, so if it ever stops holding the ceiling number
    in the recipe notes and the master doc stops meaning anything."""
    got = _generator().ceiling()
    total = got["cells_identical"] + got["cells_changed"]
    assert got["cells_identical"] / total > 0.999, (
        f"only {got['cells_identical']:,.0f} of {total:,.0f} allocation cells match across "
        "waves — the same-person same-scenario pairs are no longer the same scenario"
    )


@needs_deposit
def test_the_exact_match_ceiling_is_the_number_the_docs_quote() -> None:
    """27.7%, pinned. Three documents now quote it -- both recipes' notes, the
    ledger and the master doc -- and a number quoted in prose and computed
    nowhere is how `9xw67`'s lost generator happened. The band is wide enough
    that only a real change to the pairing moves it out."""
    got = _generator().ceiling()
    assert got["pairs"] > 3000
    assert 0.26 < got["identical_answer"] < 0.29
    assert 0.55 < got["within_one_point"] < 0.60
    assert 0.30 < got["correlation"] < 0.36


# --- 5. the panel link is enforced, not just conventional -------------------


@needs_derived
def test_a_panel_recipe_without_participant_id_var_fails_qc() -> None:
    """QC rule 19. The convention was written into STATUS.md as load-bearing
    while nothing checked it, so one recipe omitting the field would have cost
    that experiment's respondents their link to every other, silently."""
    from micromotives_datasets.pipeline.qc import check

    rec = recipe.load(RECIPES[5])
    rows = list(_rows(5))[:200]
    assert not check(rows, rec).failures

    rec.participant_id_var = None
    failures = check(rows, rec).failures
    assert any("participant_id_var" in f for f in failures), failures


def test_every_innovation_panel_recipe_declares_it() -> None:
    """Needs no data: it is a property of the recipes. So it also runs on a
    fresh clone, where the deposit-dependent tests above all skip."""
    for path in sorted((REPO / "recipes").glob("*.yaml")):
        rec = recipe.load(path)
        if rec.source == "innovation_panel":
            assert rec.participant_id_var, f"{path.name} is a panel source with no id variable"
