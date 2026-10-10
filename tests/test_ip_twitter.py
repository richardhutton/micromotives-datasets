"""IP 9.33 — consent to link Twitter data, help links on the page or apart, wave 15.

What could go wrong quietly, and the test for each:

1. **The wording.** The condition is the one part we write. Each arm's consent
   text differs in a sentence as well as in where the links sat, and each row
   must carry its own arm's, word-for-word. Pinned against questionnaire text
   written out below, never read from the recipe.

2. **The household join.** The version lives in `o_hhsamp_ip`. This file joins
   it again itself, independently of the generator, and requires every row's
   condition to equal that allocation AND the routing: the row's own version's
   question holds an answer and the other version's does not.

3. **The web-only boundary** (ledger 141). The manipulation is a screen layout,
   so no face-to-face or telephone respondent may appear, and no web answerer may
   be lost.

4. **The "We" / "As you have completed surveys..." fill**, resolved per row from
   `everint`. A swapped directive would build and pass QC.

5. **`--check` must be able to fail**, and must exit non-zero when it does.

UKDS rule: no assertion here compares or prints an identifier, a persona value
or a response value. Every comparison that touches respondents is reduced to a
COUNT first, so a failure message can only ever show a number.

These need the UKDS deposit, which is licensed and gitignored, so they skip when
it is absent rather than failing on a fresh clone.
"""

from __future__ import annotations

import collections
import functools
import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

from micromotives_datasets import recipe
from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.sources import spss

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_ip_twitter.py"
RECIPE = REPO / "recipes" / "ukds_6849_twitter_consent_w15.yaml"
DERIVED = REPO / "data" / "raw" / "ukds_6849" / "twitter_w15-derived.sav"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"

# ---------------------------------------------------------------------------
# From `6849_ip_wave_15_questionnaire.pdf`, module Twitterconsent_ip15, pp.
# 203-206, in the source's own characters. Deliberately NOT from the recipe.
# ---------------------------------------------------------------------------
OPENING = "As social media plays an increasing role in society, who uses Twitter, how they use it, and what they say on it can provide useful information for social researchers trying to understand society."  # noqa: E501
FILL = {
    1: "As you have completed surveys with us in the past, we",  # {if ff_everint =1}
    2: "We",  # {if ff_everint <>1}
}
ADD = {
    0: "would like to add publicly available information from your Twitter account such as your profile information, tweets in the past and in future, and information about how you use your account to the information you have provided for this study.",  # noqa: E501
    1: "would like to add the information you have provided for this study to publicly available information from your Twitter account such as your profile information, tweets in the past and in future, and information about how you use your account.",  # noqa: E501
}
CLOSING = "By doing so, we will be able to get a more well-rounded understanding of people’s lives. For example, in a survey we can ask people’s views on a particular issue, but by adding their Twitter information we can get a deeper understanding by seeing what news accounts they follow, how they talk about the issue (if at all), and whether they are connected to people with similar or different views. Your Twitter information will be treated as confidential and given the same protections as the other information you give us in accordance with GDPR. Researchers who wish to see your detailed Twitter information will have to apply to do so and give reasons for that access."  # noqa: E501
HELP_LINKS = (
    "What information will you collect from my Twitter account?",
    "What will the information be used for?",
    "Why is my Twitter information useful for researchers?",
    "What if what I do on Twitter isn’t the ‘real’ me?",
    "Who will be able to access the information?",
    "What will you do to keep my information safe?",
    "How long will you collect and store my information for?",
    "What if I change my mind?",
)
QUESTION = "Are you willing to tell us the username for your personal Twitter account, and for your Twitter information to be collected and added to the information you have provided for this study"  # noqa: E501
NOT_SURE = "Not sure, I would like more information."

# Our own words (docs/CONVENTIONS.md, narration and the layout exception), pinned
# here so a change to them is a decision and not a drift.
SCREENER = (
    'You were asked "Do you have a personal Twitter account?" and answered "Yes". '
    "You were then shown this text:"
)
LAYOUT = {
    0: "Between this text and the question, the same page showed eight help links, "
    "each opening further information: " + " / ".join(f'"{h}"' for h in HELP_LINKS),
    # Cut from 'No help links ... They were on a separate page, reached by answering
    # "Not sure, ..."' on the checker's flag: the respondent could not know that.
    1: "No help links were shown with this text.",
}
OUTCOME = {
    0: f'{QUESTION}? 1 "Yes" 2 "No" Only return one of 1 or 2, nothing else.',
    1: f'{QUESTION}, or would you like more information? 3 "{NOT_SURE}" 1 "Yes" 2 "No" '
    "Only return one of 1, 2 or 3, nothing else.",
}
OWN_VAR = {0: "o_twitlinka", 1: "o_twitlinkb"}
ANSWER_CODES = {0: {1, 2}, 1: {1, 2, 3}}
COUNTS = {0: 267, 1: 260}


def _straight(text: str) -> str:
    """Typography normalises, words never do (docs/CONVENTIONS.md)."""
    return text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')


def expected_condition(arm: int, everint: int) -> str:
    consent = f"{OPENING} {FILL[everint]} {ADD[arm]} {CLOSING}"
    return _straight(f'{SCREENER} "{consent}" {LAYOUT[arm]}')


needs_deposit = pytest.mark.skipif(
    not (STATA / "o_indresp_ip.dta").exists(),
    reason="UKDS SN 6849 not present (licensed, data/raw is gitignored)",
)
needs_derived = pytest.mark.skipif(
    not DERIVED.exists(), reason="derived file not built — run scripts/gen_ip_twitter.py --write"
)


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("gen_ip_twitter", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_ip_twitter"] = module
    spec.loader.exec_module(module)
    return module


@functools.cache
def _rows() -> tuple:
    return tuple(build_rows(spss.read(DERIVED), recipe.load(RECIPE)))


def _code(value: object) -> int | None:
    try:
        f = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return None if f != f else int(f)


@functools.cache
def _deposit() -> dict[str, dict[str, int | None]]:
    """participant id -> what the DEPOSIT says about them, joined here, not by the generator.

    Dictionaries rather than DataFrame merges, so no join can raise an error
    that quotes a key. Nothing from this mapping is ever printed.
    """
    ind = spss.read(STATA / "o_indresp_ip.dta").df
    hh = spss.read(STATA / "o_hhsamp_ip.dta").df
    isamp = spss.read(STATA / "o_indsamp_ip.dta").df
    alloc = {h: _code(a) for h, a in zip(hh["o_hidp"], hh["o_ff_twithelpw15"], strict=True)}
    everint: dict[int, int | None] = {}
    for p, e in zip(isamp["pidp"], isamp["o_everint"], strict=True):
        everint.setdefault(int(p), _code(e))
    out: dict[str, dict[str, int | None]] = {}
    for _, r in ind.iterrows():
        pidp = int(r["pidp"])
        pid = "ukds_6849:ip_" + hashlib.sha256(f"ukds6849:{pidp}".encode()).hexdigest()[:12]
        out[pid] = {
            "alloc": alloc.get(r["o_hidp"]),
            "indmode": _code(r["o_indmode"]),
            "twithave": _code(r["o_twithave"]),
            "o_twitlinka": _code(r["o_twitlinka"]),
            "o_twitlinkb": _code(r["o_twitlinkb"]),
            "everint": everint.get(pidp),
            "ukborn_asked": int(_code(r["o_ukborn"]) != -8),
        }
    return out


# --- the generator ---------------------------------------------------------


@needs_deposit
def test_check_finds_allocation_routing_and_fill_consistent() -> None:
    assert _generator().check() == 0


@needs_deposit
def test_check_counts_a_scrambled_allocation() -> None:
    gen = _generator()
    merged, _ = gen._joined()
    broken = merged.copy()
    broken["o_ff_twithelpw15"] = broken["o_ff_twithelpw15"].map({1: 2, 2: 1}).fillna(-9)
    assert gen.check(broken) > 0


@needs_deposit
def test_check_counts_a_contradicted_fill() -> None:
    gen = _generator()
    merged, _ = gen._joined()
    broken = merged.copy()
    broken.loc[broken["o_everint"] == 2, "o_everint"] = 1
    assert gen.check(broken) > 0


@needs_deposit
def test_check_exits_non_zero_when_it_finds_anything(monkeypatch) -> None:
    gen = _generator()
    monkeypatch.setattr(gen, "check", lambda merged=None: 1)
    monkeypatch.setattr(sys, "argv", ["gen_ip_twitter.py", "--check"])
    with pytest.raises(SystemExit) as exc:
        gen.main()
    assert exc.value.code not in (0, None)


def test_a_failed_join_never_quotes_its_keys() -> None:
    """Synthetic frames: the earlier slip was pandas listing duplicated `pidp`s."""
    import pandas as pd

    gen = _generator()
    left = pd.DataFrame({"pidp": [918273645, 564738291]})
    right = pd.DataFrame({"pidp": [918273645, 918273645], "x": [1, 2]})
    with pytest.raises(gen.IdentifierSafeError) as exc:
        gen._merge(left, right, "pidp", "test join")
    assert "918273645" not in str(exc.value)
    # A traceback would print a chained pandas error, keys and all.
    assert exc.value.__cause__ is None and exc.value.__context__ is None

    # The other path: pandas itself raises, and its exception must not travel.
    broken_left = pd.DataFrame({"other": [918273645]})
    ok_right = pd.DataFrame({"pidp": [564738291], "x": [1]})
    with pytest.raises(gen.IdentifierSafeError) as exc2:
        gen._merge(broken_left, ok_right, "pidp", "test join")
    assert "918273645" not in str(exc2.value)
    assert exc2.value.__cause__ is None and exc2.value.__suppress_context__


@needs_deposit
def test_pidp_is_never_written_to_the_derived_file() -> None:
    frame, _ = _generator().derive()
    assert "pidp" not in frame.columns
    assert "hidp" not in " ".join(frame.columns)
    assert frame["person"].str.startswith("ip_").all()


# --- the built rows ---------------------------------------------------------


@needs_derived
def test_each_condition_is_its_own_arms_text_with_its_own_fill() -> None:
    dep = _deposit()
    wrong = 0
    for row in _rows():
        rec = dep[row.participant_id]["everint"]
        fill = 1 if rec == 1 else 2
        wrong += row.condition != expected_condition(row.condition_num, fill)
    assert wrong == 0


@needs_derived
def test_each_outcome_is_its_own_arms_question_and_options() -> None:
    wrong = sum(row.outcome != _straight(OUTCOME[row.condition_num]) for row in _rows())
    assert wrong == 0


@needs_derived
def test_rows_per_condition_and_answer_codes() -> None:
    rows = _rows()
    assert dict(collections.Counter(r.condition_num for r in rows)) == COUNTS
    out_of_range = sum(int(r.response) not in ANSWER_CODES[r.condition_num] for r in rows)
    assert out_of_range == 0
    assert {r.task_num for r in rows} == {0}


@needs_derived
def test_web_only_and_every_web_answer_kept() -> None:
    dep = _deposit()
    rows = _rows()
    not_web = sum(dep[r.participant_id]["indmode"] != 3 for r in rows)
    assert not_web == 0
    # The other direction: every web Twitter user with an answer in their own
    # version's question is a row, computed from the deposit alone.
    expected = collections.Counter()
    for d in dep.values():
        if d["indmode"] == 3 and d["twithave"] == 1 and d["alloc"] in (1, 2):
            arm = int(d["alloc"]) - 1  # type: ignore[arg-type]
            if d[OWN_VAR[arm]] in ANSWER_CODES[arm]:
                expected[arm] += 1
    assert dict(expected) == COUNTS


@needs_derived
def test_each_rows_condition_is_its_households_allocation_and_its_routing() -> None:
    dep = _deposit()
    off_allocation = off_routing = 0
    for row in _rows():
        d = dep[row.participant_id]
        arm = row.condition_num
        off_allocation += d["alloc"] != arm + 1
        off_routing += d[OWN_VAR[arm]] not in ANSWER_CODES[arm] or d[OWN_VAR[1 - arm]] != -8
    assert off_allocation == 0
    assert off_routing == 0


@needs_derived
def test_the_fill_follows_everint() -> None:
    dep = _deposit()
    previously = _straight(f"{FILL[1]} would like to add")
    fresh = f'"{OPENING} {FILL[2]} would like to add'
    wrong = 0
    tally = collections.Counter()
    for row in _rows():
        d = dep[row.participant_id]
        rec = d["everint"]
        if rec == 1:
            wrong += previously not in row.condition or fresh in row.condition
        elif rec == 2 or (rec == -8 and d["ukborn_asked"]):
            wrong += fresh not in row.condition or previously in row.condition
        else:
            wrong += 1  # unresolvable: must not have been built
        tally[rec] += 1
    assert wrong == 0
    # Both branches exercised, and the -8s (resolved by the Ukborn routing) present.
    assert tally[1] > 0 and tally[2] > 0 and tally[-8] > 0
