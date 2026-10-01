"""The pipeline must stay offline and deterministic.

`micromotives_datasets.jev` holds the semantic judgements, and they are made
when a recipe is AUTHORED — the answer is written into the YAML, reviewed by a
human, and argued with by a checker. They must not be made while a recipe is
EXECUTED: the same recipe has to build the same rows on every run, and a QC rule
that phoned an API would make `mmds build` unreproducible and dependent on a
network and a key.

That is easy to state and easy to erode — someone reaches for a better answer
inside a rule, and six months later nobody can reproduce a build. So it is a
test, because a boundary nobody checks is a boundary that moves.
"""

from __future__ import annotations

import ast
import itertools
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "micromotives_datasets"

# Anything that reaches the network, directly or through Jev.
FORBIDDEN = {"jev", "typesafe_sdk", "requests", "httpx", "urllib", "socket"}

# The modules a build actually runs. `sources.osf` is excluded: fetching a
# deposit is explicitly a network step and is not part of a build.
OFFLINE = [
    SRC / "pipeline",
    SRC / "persona",
    SRC / "recipe.py",
    SRC / "schema.py",
    SRC / "sources" / "spss.py",
    SRC / "sources" / "quex.py",
]


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            # `from ..jev import x` has module="jev"; `from . import jev` puts it
            # in names. Both have to be caught.
            if node.module:
                found.add(node.module.split(".")[-1])
                found.add(node.module.split(".")[0])
            found |= {a.name for a in node.names}
    return found


def _python_files() -> list[Path]:
    out: list[Path] = []
    for target in OFFLINE:
        out.extend(sorted(target.rglob("*.py")) if target.is_dir() else [target])
    return out


def test_the_pipeline_never_imports_jev_or_the_network() -> None:
    offenders: dict[str, set[str]] = {}
    for path in _python_files():
        bad = _imports(path) & FORBIDDEN
        if bad:
            offenders[str(path.relative_to(SRC))] = bad
    assert not offenders, (
        f"offline code imports something that reaches the network: {offenders}. "
        "Jev answers belong in the recipe, written at authoring time and reviewed "
        "there — not in a rule that runs on every build."
    )


def test_the_check_would_notice(tmp_path: Path) -> None:
    """The test above passes trivially if `_imports` returns nothing.

    This is the same discipline as mutation-testing a QC rule: a check that has
    never been shown to fire is not known to work.
    """
    sample = tmp_path / "offender.py"
    sample.write_text("from ..jev import client\nimport httpx\n")
    assert _imports(sample) & FORBIDDEN == {"jev", "httpx"}


def test_jev_itself_is_allowed_to_reach_the_network() -> None:
    """The rule is about where the call is made from, not that it never happens."""
    assert "typesafe_sdk" in (SRC / "jev.py").read_text()


# --------------------------------------------------------------------------
# a prompt lives in one place
# --------------------------------------------------------------------------

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"

# Harnesses whose JOB is to drive arbitrary payloads: they hold lists of
# (state, questions, expected) cases and measure the answers. A production
# function would be the wrong shape for them, so they may call `system_one`
# directly — but the list is exact, so a third file cannot quietly join it.
#
# `jev_calibration.py` is in here under protest. Ledger 86: it measures a
# question production does not ask — the first sentence of the assignment
# instruction only, over 10 candidates with the answer guaranteed present, so
# paging is never exercised although production pages at 45. Every calibration
# number this project has came from that. Pointing it at the production
# functions changes what the numbers MEAN, so it is a separate pass, and it is
# named here rather than left as a comment nobody reads.
MAY_CALL_JEV_DIRECTLY = {"jev_probe.py", "jev_calibration.py"}


def _calls_system_one(path: Path) -> bool:
    """A `.system_one(` call, ignoring the string that names it in prose."""
    tree = ast.parse(path.read_text())
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "system_one"
        for node in ast.walk(tree)
    )


def test_only_jev_owns_a_prompt() -> None:
    """Every production prompt lives in `jev.py`, and nowhere else.

    `jev.py`'s own docstring has said since it was written that asking these
    questions in separate scripts is how "a lesson learned in one did not reach
    the others" — and five scripts went on owning prompts anyway. Two of them
    mattered: `jev_show_wire.py` printed a stale copy of the transfer-screen
    wording as though it were what production sends, and `persona_harmonise.py`
    held the two prompts the persona crosswalk is built from.

    So it is a test, for the same reason the offline boundary is one.
    """
    offenders = sorted(
        p.name
        for p in SCRIPTS.glob("*.py")
        if p.name not in MAY_CALL_JEV_DIRECTLY and _calls_system_one(p)
    )
    assert not offenders, (
        f"these scripts build their own Jev payload: {offenders}. Move the prompt "
        "into src/micromotives_datasets/jev.py and call it — a prompt in two "
        "places is a prompt that will be fixed in one."
    )


def test_the_prompt_check_would_notice(tmp_path: Path) -> None:
    """The assertion above passes trivially if `_calls_system_one` never fires."""
    offender = tmp_path / "offender.py"
    offender.write_text("client.system_one(state='x', questions={})\n")
    assert _calls_system_one(offender)
    innocent = tmp_path / "innocent.py"
    innocent.write_text("x = 'we call system_one in jev.py'\n")
    assert not _calls_system_one(innocent)


def test_the_exception_list_names_only_files_that_exist() -> None:
    """An exemption for a deleted file is an exemption nobody will ever revisit."""
    missing = sorted(n for n in MAY_CALL_JEV_DIRECTLY if not (SCRIPTS / n).exists())
    assert not missing, f"exempted scripts that no longer exist: {missing}"


# --------------------------------------------------------------------------
# the persona vocabulary does not fork
# --------------------------------------------------------------------------

SNAPSHOT = Path(__file__).resolve().parents[1] / "data" / "catalog" / "persona_snapshot.json"


# Answers that could belong to almost any question, so sharing them is no
# evidence two fields are one. Every false positive the overlap heuristic
# produced on this corpus was a subset of these.
GENERIC_ANSWERS = frozenset(
    {"yes", "no", "other", "don't know", "refused", "prefer not to say", "none", "not sure"}
)


def _overlap(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if (a | b) else 0.0


def _generic(values: set[str]) -> bool:
    """True when the answers identify no particular question."""
    return {v.strip().lower() for v in values} <= GENERIC_ANSWERS


def test_no_two_persona_fields_are_the_same_field_twice() -> None:
    """Two spellings of one concept make a study invisible to anyone filtering.

    `ye2ej` emitted `religion_attendance` where five other recipes emit
    `religious_attendance`, with an IDENTICAL value set, and
    `sexual_orientation_self` where `yv2ta` emits `sexual_orientation`. Both
    survived maker, checker and every QC rule, because neither is visible inside
    one study — only in a sorted list of the whole corpus.

    Two heuristics, because the two cases differ. A name that contains another
    name is one field wearing a qualifier; a DISTINCTIVE value set that largely
    coincides with another is one question asked twice. Both are heuristics and
    both can be wrong — the point is that a fork has to be ARGUED with rather
    than arriving unannounced.

    "Distinctive" is load-bearing and was learned the hard way here. The first
    version of this check used overlap alone and reported three pairs, all
    false: `has_children`, `household_head` and `other_adults_help_childcare`
    are three different questions that happen to share the answers Yes / No /
    Other. A generic answer set says nothing about which question was asked, so
    it cannot be evidence that two questions are one. Measured on the corpus,
    every false positive was a subset of GENERIC and the one true positive
    (`religious_attendance`, six ordered frequencies) was not — so the rule is
    about the KIND of answer set, not a size threshold picked to fit.
    """
    import json

    fields = {
        k: set(v) for k, v in json.loads(SNAPSHOT.read_text()).items() if k.startswith("extra.")
    }
    forks: list[str] = []
    for a, b in itertools.combinations(sorted(fields), 2):
        short, long_ = sorted((a[6:], b[6:]), key=len)
        if short in long_:
            forks.append(f"{a} / {b} — one name contains the other")
        elif not _generic(fields[a]) and _overlap(fields[a], fields[b]) >= 0.5:
            forks.append(f"{a} / {b} — value sets overlap {_overlap(fields[a], fields[b]):.0%}")
    assert not forks, (
        f"the persona vocabulary has forked: {forks}. Pick one spelling across "
        "every recipe and re-run scripts/persona_snapshot.py — a consumer "
        "filtering the merged corpus on one of these silently loses the other."
    )


def test_the_fork_check_would_notice() -> None:
    """Both arms fire on the real cases, and the generic guard spares the rest."""
    # The religious_attendance fork: identical, distinctive, and NOT a substring
    # pair — "religion_attendance" is not inside "religious_attendance" — so the
    # overlap arm is the one that has to catch it.
    attendance = {"Never", "Once a week", "Once a year or less", "A few times a year"}
    assert _overlap(attendance, attendance) == 1.0
    assert not _generic(attendance)
    assert "religion_attendance" not in "religious_attendance"

    # The sexual_orientation fork: caught by the name arm, since the value sets
    # genuinely differ between the panel profile and the study's own question.
    assert "sexual_orientation" in "sexual_orientation_self"

    # And the three questions that merely share Yes / No / Other are spared.
    assert _generic({"Yes", "No", "Other"})
    assert _overlap({"a"}, {"b"}) == 0.0
