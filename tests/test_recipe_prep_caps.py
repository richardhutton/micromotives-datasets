"""recipe_prep may cap what it asks Jev about, but never in silence.

On `k9ahx` (13 Nov 2026) a bare `cols[:40]` cut every persona variable out of
the labels pass and nothing said so — the failure CLAUDE.md names under "never
cap how much you ask about in silence".
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "recipe_prep.py"


@pytest.fixture(scope="module")
def recipe_prep():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("recipe_prep", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["recipe_prep"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_a_cap_names_every_item_it_leaves_out(recipe_prep, capsys) -> None:  # type: ignore[no-untyped-def]
    cols = [f"V{i}" for i in range(45)]
    kept = recipe_prep.capped(cols, 40, "columns")
    out = capsys.readouterr().out
    assert kept == cols[:40]
    assert "CAPPED" in out and "40 of 45" in out
    for left in cols[40:]:
        assert left in out


def test_no_cap_reached_prints_nothing(recipe_prep, capsys) -> None:  # type: ignore[no-untyped-def]
    cols = ["A", "B", "C"]
    assert recipe_prep.capped(cols, 40, "columns") == cols
    assert capsys.readouterr().out == ""


def test_no_bare_slice_caps_remain(recipe_prep) -> None:  # type: ignore[no-untyped-def]
    """The two former silent caps must go through `capped`."""
    src = SCRIPT.read_text()
    assert "cols[:40]" not in src
    assert "list(refused)[:25]" not in src
