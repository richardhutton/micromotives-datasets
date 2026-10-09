"""IP 9.18 — what counts as "successful ageing", waves 9 and 17.

Four things here could go wrong quietly, and each has a test:

1. **The name in each slot.** The archive codes slot 1's name differently from
   slots 2 and 3 in wave 9, and wave 17 records only a sequence. A wrong map
   does not fail; it renders a real description with the wrong person in it,
   and every count still agrees. `--check` compares every derived name with the
   archive's own label and is run here as a test.

2. **Agreement.** The pronouns and the question both follow the name. Asserted
   on every built row against a name -> pronoun table written HERE from the
   questionnaire, not read back out of the recipe that produced the rows.

3. **The condition text.** The archived labels contradict themselves ("rarely
   sees family and friends regularly"), so the recipe transcribes the
   questionnaire, and the two waves differ by one comma.

4. **Wave 17's allocation.** It is not the balanced factorial the guide
   describes. The counts are pinned so the recipe notes cannot drift from them.

These need the UKDS deposit, which is licensed and gitignored, so they skip when
it is absent rather than failing on a fresh clone.
"""

from __future__ import annotations

import functools
import importlib.util
import re
import sys
from pathlib import Path

import pytest

from micromotives_datasets import recipe
from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.sources import spss

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_ip_vig_ageing.py"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"
RECIPES = {
    9: REPO / "recipes" / "ukds_6849_vig_ageing_w9.yaml",
    17: REPO / "recipes" / "ukds_6849_vig_ageing_w17.yaml",
}

# From the questionnaire's fills ("[He{ff_vigname = 1|2|3}]/[She{...}]"),
# deliberately not from the recipe.
PRONOUNS = {
    "George": ("He", "his"),
    "Harry": ("He", "his"),
    "Margaret": ("She", "her"),
    "Anne": ("She", "her"),
}

needs_deposit = pytest.mark.skipif(
    not (STATA / "i_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not all(
        (REPO / "data" / "raw" / "ukds_6849" / f"vig_ageing_w{w}-derived.sav").exists()
        for w in RECIPES
    ),
    reason="derived files not built — run scripts/gen_ip_vig_ageing.py --write",
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_vig_ageing", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_vig_ageing"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows(wave: int) -> tuple:
    rec = recipe.load(RECIPES[wave])
    path = REPO / "data" / "raw" / "ukds_6849" / rec.data_file
    return tuple(build_rows(spss.read(path), rec))


# --- 1. the name in each slot ------------------------------------------------


@needs_deposit
def test_every_derived_name_agrees_with_the_archives_own_label() -> None:
    """6,030 names in wave 9 against each slot's own labels; 6,660 in wave 17
    against the sequence label, which spells the three names out."""
    for letter in ("i", "q"):
        assert _generator().check(letter) == 0


@needs_deposit
def test_wave_9_shows_exactly_the_guides_six_name_sequences() -> None:
    """The independent confirmation that decoding wave 17's sequence through the
    guide's table is right: wave 9 recorded the names themselves."""
    gen = _generator()
    frame, _ = gen.derive("i")
    allocated = frame[frame["vname1"] > 0]
    triples = {
        tuple(gen.NAMES[int(row[f"vname{i}"])] for i in (1, 2, 3))
        for _, row in allocated.iterrows()
    }
    assert triples == set(gen.SEQUENCES.values())


@needs_deposit
def test_pidp_is_never_written_to_the_derived_file() -> None:
    for letter in ("i", "q"):
        frame, _ = _generator().derive(letter)
        assert "pidp" not in frame.columns
        assert frame["person"].str.startswith("ip_").all()


# --- 2. agreement, on every row ----------------------------------------------

_OPENING = re.compile(r"answers! (\w+) is 75 years old")
_QUESTION = re.compile(r"^How successfully is (\w+) ageing\? ")


@needs_derived
def test_pronouns_and_question_follow_the_name_on_every_row() -> None:
    for wave in RECIPES:
        for row in _rows(wave):
            opening = _OPENING.search(row.condition)
            asked = _QUESTION.match(row.outcome)
            assert opening and asked, row.condition
            name = opening.group(1)
            assert asked.group(1) == name, f"described {name}, asked about {asked.group(1)}"
            assert row.factors["name"] == name
            subject, possessive = PRONOUNS[name]
            assert f". {subject} has " in row.condition
            assert f". {subject} sees {possessive} family" in row.condition


@needs_derived
def test_no_placeholder_or_generic_question_reaches_a_row() -> None:
    """`[name]` is the recipe's fallback question; the template must override it
    on every task."""
    for wave in RECIPES:
        for row in _rows(wave):
            assert "[name]" not in row.outcome
            assert not re.search(r"[{}\[\]]", row.condition)


@needs_derived
def test_the_condition_expresses_every_factor_the_row_claims() -> None:
    for wave in RECIPES:
        rec = recipe.load(RECIPES[wave])
        assert rec.condition.template is not None
        dims = rec.condition.template.dimensions
        for row in _rows(wave):
            for name, level in row.factors.items():
                wanted = next(v.text for v in dims[name].levels.values() if v.level == level)
                assert wanted in row.condition, f"{name}={level} not in the condition"


# --- 3. the condition text ---------------------------------------------------


def test_the_clauses_the_archived_labels_get_wrong() -> None:
    """Needs no data. The labels say "rarely sees family and friends regularly",
    "struggles to open food packaging easily" and "doesn't volunteers"."""
    for wave in RECIPES:
        template = recipe.load(RECIPES[wave]).condition.template
        assert template is not None
        levels = {n: d.levels for n, d in template.dimensions.items()}
        assert levels["interpersonal"][2].text == "rarely"
        assert levels["physical"][2].text == "struggles to open food packaging"
        assert levels["volunteering"][2].text == "doesn't volunteer"


def test_the_two_waves_differ_by_one_comma_and_nothing_else() -> None:
    nine, seventeen = (recipe.load(RECIPES[w]).condition.template for w in (9, 17))
    assert nine is not None and seventeen is not None
    assert seventeen.text == nine.text.replace(
        "{interpersonal} and {volunteering}", "{interpersonal}, and {volunteering}"
    )
    assert seventeen.text != nine.text
    rest = {"text"}
    assert nine.model_dump(exclude=rest) == seventeen.model_dump(exclude=rest)


# --- 4. the rows -------------------------------------------------------------


@needs_derived
def test_the_row_counts() -> None:
    """Reached twice: the generator counts answered descriptions, the pipeline
    builds rows, and they agree."""
    assert len(_rows(9)) == 5967
    assert len(_rows(17)) == 6600


@needs_derived
def test_responses_are_on_the_questionnaires_0_to_10() -> None:
    for wave in RECIPES:
        assert {int(r.response) for r in _rows(wave)} <= set(range(11))


@needs_derived
def test_all_256_cells_occur_in_both_waves() -> None:
    for wave in RECIPES:
        assert len({r.condition_num for r in _rows(wave)}) == 256


@needs_derived
def test_the_same_person_spans_both_waves() -> None:
    """The panel link: one id across waves eight years apart."""
    nine = {r.participant_id for r in _rows(9)}
    seventeen = {r.participant_id for r in _rows(17)}
    assert all((i or "").startswith("ukds_6849:ip_") for i in nine | seventeen)
    assert len(nine & seventeen) > 300, f"only {len(nine & seventeen)} span both waves"


@needs_derived
def test_the_persona_never_carries_a_sentinel_as_an_answer() -> None:
    for wave in RECIPES:
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


# --- 5. wave 17's allocation -------------------------------------------------


@needs_derived
def test_wave_17s_allocation_is_not_the_balanced_factorial_the_guide_describes() -> None:
    """Pinned because the recipe notes quote these numbers. Wave 9 is the
    control: the same design, implemented as documented."""
    gen = _generator()
    nine = gen.report_allocation("i", gen.derive("i")[0])
    seventeen = gen.report_allocation("q", gen.derive("q")[0])
    assert nine["distinct"] == nine["allocated"] == 2010
    assert nine["in_repeated"] == 0
    assert seventeen["allocated"] == 2220
    assert seventeen["largest_block"] == 354
    assert seventeen["in_repeated"] == 933
    assert seventeen["distinct"] == 1497


@needs_derived
def test_the_undocumented_slot_constraint() -> None:
    """Quoted in both recipes. Wave 9 never repeats description 1's six life
    codes in description 2 but does in 3, about as often as chance; wave 17
    never repeats them in any pair."""
    gen = _generator()

    def identical(letter: str, x: int, y: int) -> int:
        a = gen.derive(letter)[0]
        a = a[a["vdisease1"] > 0]
        return int((sum(a[f"{d}{x}"] == a[f"{d}{y}"] for d in gen.DIMS) == len(gen.DIMS)).sum())

    assert identical("i", 1, 2) == 0
    assert identical("i", 1, 3) == 38 and identical("i", 2, 3) == 35
    assert all(identical("q", x, y) == 0 for x, y in ((1, 2), (1, 3), (2, 3)))


@needs_derived
def test_wave_17s_persona_gap_is_the_size_the_notes_say() -> None:
    """681 rows with no age and no sex: shipped empty, never guessed."""
    rows = _rows(17)
    missing = [r for r in rows if r.persona.age is None and r.persona.sex is None]
    assert len(missing) == 681
    assert not [r for r in _rows(9) if r.persona.sex is None]
