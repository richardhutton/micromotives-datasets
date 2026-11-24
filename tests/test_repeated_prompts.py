"""A prompt shown twice by chance: keep the first showing, drop the declared number of repeats.

QC rule 24 fails a person answering the same condition and outcome twice, because the row
format cannot say which answer came first. Conjoints that redraw every slot at random
(8ctbk, 9xw67_conjoint) do this by chance; the recipe declares `repeated_prompts` and the
melt keeps the first showing by task order. Tested both ways: what it drops, and that a
count other than the declared one stops the build.
"""

from __future__ import annotations

import pytest

from micromotives_datasets.pipeline import build
from micromotives_datasets.recipe import RepeatedPrompts
from micromotives_datasets.schema import Persona, Row


def _row(pid: str, task: int, cond: str, response: str) -> Row:
    return Row(
        persona=Persona(age=40),
        condition=cond,
        outcome="How much?",
        response=response,
        response_num=float(response),
        task_num=task,
        participant_id=pid,
        study_id="t",
        source="tess",
    )


ROWS = [
    _row("p1", 5, "profile A", "2"),  # the repeat, listed first on purpose
    _row("p1", 3, "profile A", "6"),  # the first showing (lower task number)
    _row("p1", 4, "profile B", "4"),
    _row("p2", 3, "profile A", "1"),  # a different person: not a repeat
]


class _Recipe:
    study_id = "t"

    def __init__(self, policy: RepeatedPrompts | None) -> None:
        self.repeated_prompts = policy


def _run(monkeypatch, policy):
    monkeypatch.setattr(build, "_melt", lambda ds, recipe: iter(ROWS))
    return list(build.build_rows(None, _Recipe(policy)))  # type: ignore[arg-type]


def test_keeps_the_first_showing_and_drops_the_later_one(monkeypatch) -> None:
    out = _run(monkeypatch, RepeatedPrompts(dropped=1, reason="chance redraw"))
    p1a = [r for r in out if r.participant_id == "p1" and r.condition == "profile A"]
    assert [(r.task_num, r.response) for r in p1a] == [(3, "6")]
    assert len(out) == 3


def test_a_count_other_than_the_declared_one_stops_the_build(monkeypatch) -> None:
    with pytest.raises(ValueError, match="repeated prompt"):
        _run(monkeypatch, RepeatedPrompts(dropped=2, reason="chance redraw"))


def test_without_a_declaration_nothing_is_dropped(monkeypatch) -> None:
    """The policy is opt-in; undeclared repeats are left for QC rule 24 to fail."""
    assert len(_run(monkeypatch, None)) == 4


def test_a_declaration_must_drop_something() -> None:
    with pytest.raises(ValueError):
        RepeatedPrompts(dropped=0, reason="x")
