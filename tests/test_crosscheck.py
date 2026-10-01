"""The crosscheck's task dimension, which it ignored for the project's first 28 builds.

SocSci210 carries a `task_num` and we read only `condition_num`, `response` and
`stimuli`. So a study could agree on rows, conditions and the whole response
distribution while the two builds disagreed about WHICH QUESTION a row answers,
and nothing looked. That is not hypothetical: `sh4px`'s two SocSci210
"conditions" turned out to be our two outcome clusters, and `py9q3` had items
from a different sub-experiment filed under one condition. Both were found by a
maker querying the parquet by hand.

Task differences are REPORTED, never failed, for the same reason condition_num
ordering is not failed — there is no shared convention, and a branched design
has more than one defensible numbering. Measured on `9263n`: 14 tasks against
their 7, where each of theirs is exactly a pair of ours merged. Both schemes are
arguable, so failing the build would be wrong; staying silent was worse.

Offline: `compare` is handed a stub profile rather than reaching HuggingFace.
"""

from __future__ import annotations

from typing import Any

from micromotives_datasets.pipeline import crosscheck
from micromotives_datasets.schema import Persona, Row


def _rows(spec: list[tuple[int, int]]) -> list[Row]:
    """One row per (condition_num, task_num) pair given."""
    return [
        Row(
            persona=Persona(age=40),
            condition=f"arm {c}",
            outcome=f"question {t}",
            response="1",
            condition_num=c,
            task_num=t,
            response_num=1.0,
            participant_id=f"p{i}",
            study_id="t",
            source="tess",
        )
        for i, (c, t) in enumerate(spec)
    ]


def test_our_profile_now_reports_the_task_dimension() -> None:
    profile = crosscheck.profile(_rows([(0, 0), (0, 1), (1, 0), (1, 1), (1, 1)]))
    assert profile["n_tasks"] == 2
    assert profile["rows_per_task"] == {0: 2, 1: 3}
    assert profile["rows_per_condition"] == {0: 2, 1: 3}


def _compare_against(monkeypatch: Any, theirs: dict[str, Any], rows: list[Row]) -> Any:
    monkeypatch.setattr(crosscheck, "fetch_socsci210", lambda _study: theirs)
    return crosscheck.compare(rows, "t")


def test_a_merged_task_dimension_is_reported_and_does_not_fail(monkeypatch: Any) -> None:
    """The 9263n shape: their tasks are our tasks merged in pairs.

    Everything else agrees — same rows, same conditions, same responses — so the
    build must still pass, and the disagreement must still be visible.
    """
    rows = _rows([(0, 0), (0, 1), (1, 2), (1, 3)])
    report = _compare_against(
        monkeypatch,
        {
            "n_rows": 4,
            "n_conditions": 2,
            "n_tasks": 2,
            "rows_per_condition": {0: 2, 1: 2},
            "rows_per_task": {0: 2, 1: 2},
            "response_distribution": {1: 4},
            "stimuli": {0: "arm 0", 1: "arm 1"},
        },
        rows,
    )
    assert report.passed, report.mismatches
    joined = " ".join(report.text_notes)
    assert "n_tasks" in joined and "rows_per_task" in joined
    assert not any("task" in m for m in report.mismatches), report.mismatches


def test_a_real_numeric_disagreement_still_fails(monkeypatch: Any) -> None:
    """Demoting tasks to a note must not soften anything else."""
    rows = _rows([(0, 0), (0, 1), (1, 0), (1, 1)])
    report = _compare_against(
        monkeypatch,
        {
            "n_rows": 9,
            "n_conditions": 2,
            "n_tasks": 2,
            "rows_per_condition": {0: 5, 1: 4},
            "rows_per_task": {0: 5, 1: 4},
            "response_distribution": {1: 9},
            "stimuli": {0: "arm 0", 1: "arm 1"},
        },
        rows,
    )
    assert not report.passed
    assert any("n_rows" in m for m in report.mismatches), report.mismatches


def test_identical_task_counts_raise_no_note(monkeypatch: Any) -> None:
    rows = _rows([(0, 0), (0, 1), (1, 0), (1, 1)])
    report = _compare_against(
        monkeypatch,
        {
            "n_rows": 4,
            "n_conditions": 2,
            "n_tasks": 2,
            "rows_per_condition": {0: 2, 1: 2},
            "rows_per_task": {0: 2, 1: 2},
            "response_distribution": {1: 4},
            "stimuli": {0: "arm 0", 1: "arm 1"},
        },
        rows,
    )
    assert report.passed
    assert not any("task" in n for n in report.text_notes), report.text_notes
