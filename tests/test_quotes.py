"""micromotives_datasets.quotes: the pure parts of synthetic quote writing (QUOTES_SPEC)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from micromotives_datasets import quotes as q


def _row(**over: object) -> dict[str, object]:
    row: dict[str, object] = {
        "study": "s1",
        "recipe": "r1",
        "participant_id": "tess:p1",
        "condition_num": 0,
        "task_num": 0,
        "persona": json.dumps({"age": 40, "gender": "Female", "income": None}),
        "persona_text": "Age: 40\nGender: Female",
        "condition": "You read a warning about cancer.",
        "outcome": "How likely are you to stop smoking?",
        "response": "6",
        "response_num": 6.0,
        "scale_min": 0,
        "scale_max": 10,
        "scale_nominal": False,
        "factors": "{}",
        "source": "tess",
        "quote": None,
        "synthetic_quote": False,
    }
    row.update(over)
    return row


def _item(**over: object) -> q.Item:
    base = {
        "key": ("s1", "r1", "tess:p1", 0, 0),
        "participant_id": "tess:p1",
        "persona": "age: 40\ngender: Female",
        "condition": "You read a warning about cancer.",
        "outcome": "How likely are you to stop smoking?",
        "response": "RESPONSE_MARKER_7",
        "scale_min": 0,
        "scale_max": 10,
        "angle": "ANGLE_MARKER",
        "voice": "blunt",
    }
    base.update(over)
    return q.Item(**base)  # type: ignore[arg-type]


# --- what a quote is written from ---------------------------------------------------


@pytest.mark.parametrize("field", q.HASHED)
def test_input_hash_changes_with_each_input(field: str) -> None:
    assert q.input_hash(_row()) != q.input_hash(_row(**{field: "changed"}))


def test_input_hash_ignores_what_a_quote_is_not_written_from() -> None:
    assert q.input_hash(_row()) == q.input_hash(_row(source="dataverse", factors='{"a": 1}'))


def test_persona_lines_keeps_recorded_fields_and_drops_absent_ones() -> None:
    lines = q.persona_lines(json.dumps({"age": 0, "party_id": "Labour", "income": None, "x": ""}))
    assert lines == "age: 0\nparty id: Labour"


# --- draws ------------------------------------------------------------------------------


def test_angle_draw_is_stable_and_order_free() -> None:
    keys = [("s", "r", f"p{i}", 0, i) for i in range(50)]
    first = [q.draw_angle(1, k) for k in keys]
    assert first == [q.draw_angle(1, k) for k in keys]
    assert list(reversed(first)) == [q.draw_angle(1, k) for k in reversed(keys)]
    assert first != [q.draw_angle(2, k) for k in keys]


def test_unreasoned_angles_are_drawn_as_often_as_reasoned_ones() -> None:
    draws = [q.draw_angle(3407, ("s", "r", f"p{i}", 0, 0)) for i in range(4000)]
    share = sum(a in q.UNREASONED_ANGLES for a in draws) / len(draws)
    assert 0.46 < share < 0.54
    assert set(draws) == set(q.ANGLES)


def test_angle_families_are_the_same_size() -> None:
    assert len(q.REASONED_ANGLES) == len(q.UNREASONED_ANGLES)


def test_voice_is_one_per_respondent_and_differs_between_them() -> None:
    assert q.draw_voice(1, "s", "p1") == q.draw_voice(1, "s", "p1")
    voices = {q.draw_voice(1, "s", f"p{i}") for i in range(200)}
    assert len(voices) == 4 * 2 * 2  # every combination is reachable


def test_no_voice_is_both_terse_and_rambling() -> None:
    for i in range(500):
        voice = q.draw_voice(1, "s", f"p{i}")
        assert not ("says very little" in voice and "rambling" in voice)


@pytest.mark.parametrize(
    ("response", "lo", "hi", "expect"),
    [
        ("10", 0, 10, "far end"),
        ("1", 1, 7, "far end"),
        ("5", 0, 10, "middle"),
        ("3", 0, 10, "leaning"),
        ("1", 0, 1, None),
        ("Labour", 1, 5, None),
    ],
)
def test_answer_strength(response: str, lo: int, hi: int, expect: str | None) -> None:
    got = q.answer_strength(_item(response=response, scale_min=lo, scale_max=hi))
    assert (got is None) if expect is None else (expect in got)


def test_the_blind_test_does_not_get_the_strength_either() -> None:
    text = json.dumps(q.blind_messages("SYSTEM", _item(response="10"), "q"))
    assert "How strongly" not in text and "far end" not in text


# --- prompts ----------------------------------------------------------------------------


def test_blind_test_never_sees_the_answer_or_the_angle() -> None:
    text = json.dumps(q.blind_messages("SYSTEM", _item(), "I was scared."))
    assert "RESPONSE_MARKER_7" not in text
    assert "ANGLE_MARKER" not in text
    assert "I was scared." in text


def test_checker_sees_answer_and_angle() -> None:
    text = json.dumps(q.checker_messages("SYSTEM", _item(), "I was scared."))
    assert "RESPONSE_MARKER_7" in text and "ANGLE_MARKER" in text


def test_one_respondent_call_states_the_persona_once() -> None:
    items = [_item(key=("s1", "r1", "tess:p1", 0, t)) for t in range(3)]
    user = q.writer_messages("SYSTEM", items)[1]["content"]
    assert user.count("About this person:") == 1
    assert "exactly 3 strings" in user


def test_group_call_gives_each_person_their_own_details() -> None:
    items = [_item(participant_id=f"tess:p{i}", persona=f"age: {30 + i}") for i in range(5)]
    user = q.writer_messages("SYSTEM", items)[1]["content"]
    assert user.count("About this person:") == 5
    assert all(f"age: {30 + i}" in user for i in range(5))


def test_prompt_files_exist_and_carry_the_rules() -> None:
    writer, _ = q.load_prompt("writer_v2.md")
    checker, _ = q.load_prompt("checker_v2.md")
    assert "gut feeling" in writer and "never judge whether the reason is sensible" in checker
    assert "divorced" in writer and "divorced" in checker  # details may be added, never clash
    w3, _ = q.load_prompt("writer_v3.md")
    c3, _ = q.load_prompt("checker_v3.md")
    assert "Never describe filling in the survey" in w3 and "Seventy billion" in c3
    w4, _ = q.load_prompt("writer_v4.md")
    c4, _ = q.load_prompt("checker_v4.md")
    assert "Swap test" in c4 and "Never name the kind of reason" in w4
    c5, _ = q.load_prompt("checker_v5.md")
    assert "answer_means" in c5
    assert next(iter(q.checker_schema()["properties"])) == "answer_means"


# --- parsing ----------------------------------------------------------------------------


def test_parse_quotes() -> None:
    assert q.parse_quotes('{"quotes": [" a ", "b"]}', 2) == ["a", "b"]
    assert q.parse_quotes('{"quotes": ["a"]}', 2) is None
    assert q.parse_quotes('{"quotes": ["a", "  "]}', 2) is None
    assert q.parse_quotes("not json", 1) is None
    assert q.parse_quotes('{"quotes": [1]}', 1) is None


def test_parse_verdict_needs_every_check_as_a_boolean() -> None:
    good = dict.fromkeys(q.CHECKS, True)
    assert q.parse_verdict(json.dumps(good)) == good | {"notes": ""}
    assert q.parse_verdict(json.dumps(good | {"tone_fits": "true"})) is None
    assert q.parse_verdict(json.dumps(dict.fromkeys(q.CHECKS[1:], True))) is None
    assert q.failed_checks(good | {"tone_fits": False}) == ["tone_fits"]


def test_parse_blind() -> None:
    assert q.parse_blind('{"answer": 7}') == 7.0
    assert q.parse_blind('{"answer": true}') is None
    assert q.parse_blind('{"answer": "7"}') is None


@pytest.mark.parametrize(
    ("predicted", "actual", "lo", "hi", "nominal", "agrees"),
    [
        (8, 10, 0, 10, False, True),  # same side
        (2, 9, 0, 10, False, False),  # opposite sides
        (4, 6, 0, 10, False, True),  # straddles the middle, within tolerance
        (5, 5, 0, 10, False, True),  # at the middle
        (5, 9, 0, 10, False, False),  # middle against a strong answer
        (1, 0, 0, 1, False, False),  # binary: no tolerance to hide in
        (2, 2, 1, 4, True, True),  # nominal: same category
        (3, 2, 1, 4, True, False),  # nominal: neighbouring category is still wrong
        (1, 2, 1, 4, True, False),  # nominal: same side of the middle is not the same answer
        (3.5, 6.5, 0, 10, False, False),  # straddles the middle, beyond tolerance
        (100, 7, 0, 10, False, True),  # off the scale: counted as its end
        (-50, 7, 0, 10, False, False),
        (5.4, 4, 1, 4, True, True),  # nominal, off the scale: its last category
    ],
)
def test_direction_agrees(
    predicted: float, actual: float, lo: int, hi: int, nominal: bool, agrees: bool
) -> None:
    assert q.direction_agrees(predicted, actual, lo, hi, nominal) is agrees


def test_direction_refuses_an_empty_scale() -> None:
    with pytest.raises(ValueError):
        q.direction_agrees(1, 1, 3, 3, False)


# --- the table --------------------------------------------------------------------------


def _table(*entries: tuple[dict[str, object], str, bool, str]) -> pd.DataFrame:
    recs = []
    for row, quote, passed, run in entries:
        rec = {c: row[c] for c in q.ROW_KEY}
        rec |= {"input_hash": q.input_hash(row), "quote": quote, "passed": passed, "run": run}
        recs.append(rec)
    return pd.DataFrame(recs)


def test_merge_prefers_a_passed_quote_then_the_later_run() -> None:
    row = _row()
    old_pass = _table((row, "old", True, "a"))
    new_fail = _table((row, "bad", False, "b"))
    new_pass = _table((row, "new", True, "c"))
    assert q.merge_tables([old_pass, new_fail])["quote"].tolist() == ["old"]
    assert q.merge_tables([old_pass, new_pass])["quote"].tolist() == ["new"]


def test_merge_keeps_quotes_for_different_inputs_apart() -> None:
    merged = q.merge_tables(
        [_table((_row(), "a", True, "x"), (_row(response="2"), "b", True, "x"))]
    )
    assert len(merged) == 2


def test_join_fills_current_quotes_and_flags_them_synthetic() -> None:
    rows = pd.DataFrame([_row(), _row(participant_id="tess:p2")], index=[10, 11])
    out, counts = q.join_quotes(rows, _table((_row(), "I was scared.", True, "x")))
    assert out.loc[10, "quote"] == "I was scared." and bool(out.loc[10, "synthetic_quote"])
    assert out.loc[11, "quote"] is None and not out.loc[11, "synthetic_quote"]
    assert list(out.index) == [10, 11]
    assert (counts.with_quote, counts.stale, counts.without_quote) == (1, 0, 1)


def test_join_drops_a_quote_whose_row_changed_upstream() -> None:
    table = _table((_row(), "I was scared.", True, "x"))
    changed = pd.DataFrame([_row(outcome="A reworded question. Rate only this one.")])
    out, counts = q.join_quotes(changed, table)
    assert out["quote"].isna().all()
    assert counts.stale == 1


def test_join_ignores_failed_quotes() -> None:
    out, counts = q.join_quotes(pd.DataFrame([_row()]), _table((_row(), "meh", False, "x")))
    assert out["quote"].isna().all() and counts.with_quote == 0
    assert counts.stale == 0  # failed is not stale: nothing upstream changed


# --- variety ----------------------------------------------------------------------------


def test_variety_measures_on_known_cases() -> None:
    same = np.ones((4, 3))
    distinct = np.eye(4)
    assert q.spread(same) == pytest.approx(0)
    assert q.spread(distinct) == pytest.approx(1)
    assert q.near_duplicate_share(same) == 1 and q.near_duplicate_share(distinct) == 0
    assert q.vendi(same) == pytest.approx(1)
    assert q.vendi(distinct) == pytest.approx(4)
    split = np.array([[1, 0], [1, 0.01], [0, 1], [0.01, 1]])
    assert q.separation(split, ["a", "a", "b", "b"]) > 0.9
    assert q.separation(split, ["a", "b", "a", "b"]) < 0


# --- the export -------------------------------------------------------------------------

_spec = importlib.util.spec_from_file_location(
    "export", Path(__file__).resolve().parents[1] / "scripts" / "export.py"
)
assert _spec and _spec.loader
export = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(export)


def test_export_joins_quotes_and_records_the_run(tmp_path: Path) -> None:
    run = tmp_path / "run1"
    run.mkdir()
    table = _table((_row(), "I was scared.", True, "run1"))
    for c in q.TABLE_COLUMNS:
        if c not in table:
            table[c] = None
    table.to_parquet(run / "quotes.parquet", index=False)
    (run / "run.json").write_text(json.dumps({"run": "run1", "writer": {"model": "w"}}))
    train = pd.DataFrame([_row(), _row(participant_id="tess:p2")])
    out, manifest = export.add_quotes(train, [run])
    assert out["synthetic_quote"].tolist() == [True, False]
    assert manifest["with_quote"] == 1 and manifest["without_quote"] == 1
    assert manifest["runs"][0]["writer"] == {"model": "w"}
    assert len(manifest["runs"][0]["quotes_sha256"]) == 64


def test_preference_pairs_put_each_failed_draft_against_the_accepted_rewrite() -> None:
    key = {"study": "s", "recipe": "r", "participant_id": "p", "condition_num": 0, "task_num": 0}
    d = pd.DataFrame(
        [
            key
            | {
                "input_hash": "h",
                "round": 0,
                "quote": "generic",
                "passed": False,
                "failed_checks": '["about_condition"]',
            },
            key
            | {
                "input_hash": "h",
                "round": 1,
                "quote": "still off",
                "passed": False,
                "failed_checks": '["fits_response"]',
            },
            key
            | {
                "input_hash": "h",
                "round": 2,
                "quote": "good one",
                "passed": True,
                "failed_checks": "[]",
            },
            key
            | {
                "participant_id": "q",
                "input_hash": "h",
                "round": 0,
                "quote": "fine first time",
                "passed": True,
                "failed_checks": "[]",
            },
            key
            | {
                "participant_id": "z",
                "input_hash": "h",
                "round": 0,
                "quote": "never fixed",
                "passed": False,
                "failed_checks": "[]",
            },
        ]
    )
    pairs = q.preference_pairs(d)
    assert sorted(pairs["rejected"]) == ["generic", "still off"]
    assert set(pairs["chosen"]) == {"good one"}
    assert q.preference_pairs(d.iloc[:0]).empty


# --- the voice pool (v6) ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("persona", "bands"),
    [
        ({"age": 27, "education": "Bachelors to postgraduate"}, ("18-34", "degree")),
        ({"age": 60, "education": "High school"}, ("55+", "no degree")),
        ({"age": 40, "education": "No degree"}, ("35-54", "no degree")),
        (
            {"age": 40, "education": "Below degree level (not further distinguished)"},
            ("35-54", "no degree"),
        ),
        ({"age": None, "education": None}, (None, None)),
        ({"age": 15}, (None, None)),
    ],
)
def test_persona_bands(persona: dict[str, object], bands: tuple[str | None, str | None]) -> None:
    assert q.persona_bands(json.dumps(persona)) == bands


def _pool() -> q.VoicePool:
    rows = [
        {"text": f"young grad {i}", "n": 1, "age_band": "18-34", "edu_band": "degree"}
        for i in range(10)
    ] + [
        {"text": f"older {i}", "n": 1, "age_band": "55+", "edu_band": "no degree"}
        for i in range(10)
    ]
    return q.VoicePool(pd.DataFrame(rows))


def test_pool_gives_three_matched_and_two_from_anyone_stably() -> None:
    pool = _pool()
    got = pool.pick(1, ("s", "r", "p", 0, 0), ("18-34", "degree"))
    assert len(got) == 5 and len(set(got)) == 5
    for i in range(50):  # every time, not by luck: the other group is half the pool
        picked = pool.pick(1, ("s", "r", "p", 0, i), ("18-34", "degree"))
        assert all(e.startswith("young grad") for e in picked[:3])
    assert got == pool.pick(1, ("s", "r", "p", 0, 0), ("18-34", "degree"))
    assert got != pool.pick(1, ("s", "r", "p", 0, 1), ("18-34", "degree"))


def test_pool_falls_back_to_anyone_when_the_band_is_unknown() -> None:
    got = _pool().pick(1, ("k",), (None, None))
    assert len(got) == 5 and len(set(got)) == 5


def test_copied_example() -> None:
    examples = ["He is completely out of touch with ordinary people", "Everything"]
    assert q.copied_example(
        "Honestly he's completely out of touch with ordinary people, that one", examples
    )
    assert not q.copied_example("Never met anyone like that. Posh boy.", examples)
    assert not q.copied_example(
        "Everything about it, really.", examples
    )  # short examples may recur


def test_examples_reach_the_writer_but_not_the_blind_test() -> None:
    item = _item(examples=("Gut feeling", "Out of touch"))
    assert "Gut feeling" in q.writer_messages("S", [item])[1]["content"]
    assert "Gut feeling" not in json.dumps(q.blind_messages("S", item, "a quote"))


@pytest.mark.parametrize(
    ("quote", "tells"),
    [
        ("It sits in your gut \u2014 we can't keep doing this.", ["dash"]),
        ("Well... I don't know.", ["ellipsis"]),
        ("It's not only the money, but the principle.", ["not_x_but_y"]),
        ("It's just wrong.", ["just"]),
        ("It's not about money, it's about respect.", ["not_x_but_y"]),
        ("Look, I've always voted that way.", ["staged_opener"]),
        ("I don't like them asking me that.", ["survey_talk"]),
        ("Total gaslighting from the lot of them.", ["buzzword"]),
        ("Fair play; she stuck to water.", ["semicolon"]),
    ],
)
def test_ai_tells_catch_the_humanizer_patterns(quote: str, tells: list[str]) -> None:
    assert q.ai_tells(quote) == tells


@pytest.mark.parametrize(
    "quote",
    [
        "Not great but it'll do.",
        "Honestly, it scared me.",
        "I'm not sure, but probably not.",
        "He left. That's on him.",
        "Out of the question, that.",
        "My aunt drank like a fish and lived to be eighty.",
    ],
)
def test_ai_tells_leave_ordinary_speech_alone(quote: str) -> None:
    assert q.ai_tells(quote) == []


def test_just_can_be_left_out_for_older_prompt_versions() -> None:
    assert q.ai_tells("It's just wrong.", skip=("just",)) == []
