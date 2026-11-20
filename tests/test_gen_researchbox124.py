"""The researchbox124 recipes (Smith and Spiller, undervaluation of Y-or-Z options) and their key.

The generator reads every trial of Studies 6d and 6e from the .qsf through its survey flow,
decides who was shown what by evaluating the .qsf's own display logic on the recorded draws,
and codes the raw export with the authors' exclusions. These tests stop a hand edit drifting
from it, and check the facts the rows rest on:

- the recipes and coded files are what the generator writes; only 6d and 6e have recipes;
- only Study 5's .qsf has pictures, and a planted one is seen;
- every trial column's ImportId is the .qsf question with its export tag, and no option
  order was recorded;
- the logic evaluator reads Or / And / AndIf as Qualtrics does and refuses what it does not
  know; for every kept person a trial is answered exactly when its logic says it was shown;
- the authors' exclusions, step by step, give their N (6d 194, 6e 176), and 6e's 12 first-day
  people, who started before the instructions marker existed, are the ones not built;
- the authors' long data (Data/UVExp6d.csv, UVExp6e.csv) is reproduced exactly, person by
  person, from the raw export AND from the BUILT rows through their own cleaning rules, and
  their pre-registered test gives the values their code records (6d 0.06365979, 6e
  0.05568182); a swapped answer code breaks the match;
- the rows carry only the words the notes declare as ours.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_researchbox124.py"
PROCESSED = REPO / "data" / "processed"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_researchbox124", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_researchbox124"] = mod  # dataclasses look their module up here
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.RAW.exists(), reason="researchbox124 deposit not fetched")
NAMES = ["study6d", "study6e"]


def built(name: str) -> pd.DataFrame:
    path = PROCESSED / f"researchbox124_{name}.parquet"
    if not path.exists():
        pytest.skip(f"researchbox124_{name} not built")
    return pd.read_parquet(path)


# ---------------------------------------------------------------------------
# The generator's own outputs
# ---------------------------------------------------------------------------


@needs_raw
@pytest.mark.parametrize("name", NAMES)
def test_recipe_and_coded_file_are_what_the_generator_writes(name: str) -> None:
    assert gen.recipe_path(name).read_text() == gen.render(name)
    assert (gen.RAW / gen.data_file(name)).read_text() == gen.prep(name).to_csv(index=False)
    r = load(gen.recipe_path(name))
    e = gen.experiment(name)
    assert len(r.condition.arms) == len(e.arms) and len(r.outcomes) == len(e.questions)


def test_only_6d_and_6e_have_recipes() -> None:
    assert sorted(p.stem for p in (REPO / "recipes").glob("researchbox124_*.yaml")) == [
        "researchbox124_study6d",
        "researchbox124_study6e",
    ]
    assert set(gen.NOT_BUILT) == {
        "study1",
        "study1c",
        "study1d",
        "study2",
        "study3",
        "study4",
        "study5",
        "study6",
        "study6b",
        "study6c",
    }


@needs_raw
def test_pictures_columns_and_flow() -> None:
    gen.check_pictures()
    for name in NAMES:
        gen.check_columns(name)
        gen.check_flow(name)


def test_a_planted_picture_is_seen() -> None:
    assert gen.graphics_in('{"QuestionText":"<p>x</p>"}') == (0, 0)
    assert gen.graphics_in('{"QuestionText":"<img src=x>"}')[0] == 1
    assert gen.graphics_in('{"Display":"IMAGE_URL:x IM_abcdefghij12"}')[1] == 1


# ---------------------------------------------------------------------------
# The logic evaluator
# ---------------------------------------------------------------------------


def _term(field: str, value: str, conj: str | None = None, op: str = "EqualTo") -> dict[str, Any]:
    t = {"LogicType": "EmbeddedField", "LeftOperand": field, "Operator": op}
    t["RightOperand"] = value
    return t | ({"Conjuction": conj} if conj else {})


def test_logic_reads_or_and_andif() -> None:
    logic = {
        "0": {"0": _term("type1", "1"), "1": _term("type1", "2", "Or"), "Type": "If"},
        "1": {"0": _term("order", "2"), "Type": "AndIf"},
        "Type": "BooleanExpression",
    }
    assert gen.holds(logic, {"type1": "2", "order": "2"})
    assert not gen.holds(logic, {"type1": "2", "order": "1"})  # the AndIf bites
    assert not gen.holds(logic, {"type1": "3", "order": "2"})
    assert gen.holds({}, {}) and gen.holds(None, {})
    neg = {"0": {"0": _term("set", "1", op="NotEqualTo"), "Type": "If"}}
    assert gen.holds(neg, {"set": "2"}) and not gen.holds(neg, {"set": "1"})


def test_logic_refuses_what_it_does_not_know() -> None:
    q = {"0": {"0": {"LogicType": "Question", "QuestionID": "QID1"}, "Type": "If"}}
    with pytest.raises(AssertionError):
        gen.holds(q, {})
    gt = {"0": {"0": _term("type1", "1", op="GreaterThan"), "Type": "If"}}
    with pytest.raises(AssertionError):
        gen.holds(gt, {"type1": "1"})
    mixed = {
        "0": {
            "0": _term("a", "1"),
            "1": _term("b", "1", "Or"),
            "2": _term("c", "1", "And"),
            "Type": "If",
        }
    }
    with pytest.raises(AssertionError):  # And with Or in one group: precedence unknown
        gen.holds(mixed, {"a": "1", "b": "1", "c": "1"})


# ---------------------------------------------------------------------------
# Exclusions
# ---------------------------------------------------------------------------


@needs_raw
def test_exclusions_step_by_step() -> None:
    for name, finished, kept, built_n in [("study6d", 298, 194, 194), ("study6e", 298, 176, 164)]:
        assert int((gen.named(name, "Progress") == "100").sum()) == finished
        assert len(gen.kept_index(name)) == kept
        assert len(gen.built_index(name)) == built_n
    # 6e's first-day people: started before the instructions marker existed
    k, b = set(gen.kept_index("study6e")), set(gen.built_index("study6e"))
    start = gen.named("study6e", "StartDate")
    marker = gen.named("study6e", "instructions")
    assert {start[i].split()[0] for i in k - b} == {"7/7/20"}
    assert {marker[i] for i in k - b} == {""} and {marker[i] for i in b} == {"new"}


@needs_raw
def test_shown_is_answered_for_every_kept_person() -> None:
    for name in NAMES:
        gen.answered_tags.cache_clear()
        assert gen.answered_tags(name)  # asserts shown == answered inside


@needs_raw
def test_versions_per_study() -> None:
    from collections import Counter

    v6d = Counter(q.version for q in gen.experiment("study6d").questions)
    v6e = Counter(q.version for q in gen.experiment("study6e").questions)
    assert v6d == {"X_YZ": 120, "X_Y": 88, "Y_Z": 57}
    assert v6e == {"X_YZ": 60, "X_ZY": 60, "X_Y_Z": 60, "X_Z": 60, "Y_Z": 60, "X_Y": 44}


# ---------------------------------------------------------------------------
# The answer key: the authors' long data and their pre-registered test
# ---------------------------------------------------------------------------


def _r_name(tag: str) -> str:
    """R's read.csv name for an export column: a leading digit gets an X."""
    return f"X{tag}" if tag[0].isdigit() else tag


def _which(name: str, q: Any) -> str | None:
    """The authors' name for a trial's rows (UVExp6dcleaning / UVExp6ecleaning)."""
    if name == "study6e":
        return str(q.tag)
    if q.block == "Q1s":
        return str(q.tag) if q.tag.endswith("XYZ") else f"{q.tag}XY"
    if q.block == "Q2s":
        t = _r_name(q.tag)
        return t if q.tag.endswith("XY") else f"{t}XYZ"
    return None  # 6d's closing Y vs Z block is not in their data


def _authors_rules(name: str, long: pd.DataFrame) -> pd.DataFrame:
    """Their cleaning on (SubjectNumber, Which, Choice): duplicate shared controls, add 21a."""
    long = long[long["Choice"].isin([1, 2, 3])].copy()
    long["HighT"] = long["Which"].str.contains("c")
    long["LowT"] = long["Which"].str.contains("a")
    both = long["HighT"] == long["LowT"]
    dup = long[both].assign(HighT=True, LowT=False)
    long.loc[both, "LowT"] = True
    long.loc[long["LowT"], "HighT"] = False
    long = pd.concat([long, dup])
    if name == "study6d":  # both blocks' copies of 21c's control ("X21cXY" is R's name)
        add = pd.concat(
            long[long["Which"] == f"{p}21cXY"].assign(Which=f"{p}21aXY", HighT=False, LowT=True)
            for p in ("Q", "X")
        )
    else:
        add = long[long["Which"] == "Q21c_X_Y"].assign(
            Which="Q21a_X_Y", HighT=False, LowT=True, Choice=1.5
        )
    return pd.concat([long, add]).reset_index(drop=True)


def _kind(name: str, which: pd.Series) -> tuple[pd.Series, pd.Series]:
    """(X vs Y-or-Z rows, X vs Y rows), by the authors' suffix tests."""
    if name == "study6d":
        return which.str.endswith("XYZ"), which.str.endswith("XY")
    return which.str.endswith("X_YZ") | which.str.endswith("X_ZY"), which.str.endswith("X_Y")


def _shares(name: str, long: pd.DataFrame) -> pd.DataFrame:
    """Per person: share of X choices on X vs Y-or-Z, and on X vs Y (2 - Choice)."""
    xyz, xy = _kind(name, long["Which"])
    x = 2 - long["Choice"]
    a = x[xyz].groupby(long.loc[xyz, "SubjectNumber"]).mean()
    b = x[xy].groupby(long.loc[xy, "SubjectNumber"]).mean()
    return pd.DataFrame({"xyz": a, "xy": b})


def _cleaned(name: str) -> pd.DataFrame:
    d = pd.read_csv(gen.DATA / gen.SPECS[name].cleaned)
    return d[["SubjectNumber", "Which", "Choice"]]


def _subject_numbers(name: str) -> dict[str, int]:
    """pid -> the authors' SubjectNumber (position among the kept, from 1)."""
    rid = gen.named(name, "ResponseId")
    pre = f"{gen.STUDY_ID}:{name}_"
    return {f"{pre}{rid[i]}": k for k, i in enumerate(gen.kept_index(name), 1)}


def _raw_long(name: str) -> pd.DataFrame:
    """Every kept person's trial answers from the raw export, as exported values."""
    out = []
    for q in gen.questions(name):
        which = _which(name, q)
        if which is None:
            continue
        col = gen.column(name, q.qid)
        for k, i in enumerate(gen.kept_index(name), 1):
            if col[i]:
                out.append((k, which, float(col[i])))
    return pd.DataFrame(out, columns=["SubjectNumber", "Which", "Choice"])


def _built_long(name: str, swap: bool = False) -> pd.DataFrame:
    """The BUILT rows back to the authors' long form: task_num names the question."""
    d = built(name)
    qs = gen.experiment(name).questions
    subj = _subject_numbers(name)
    out = []
    for pid, task, resp in zip(d["participant_id"], d["task_num"], d["response_num"], strict=True):
        q = qs[int(task)]
        which = _which(name, q)
        if which is None:
            continue
        pos = int(resp)
        if swap and len(q.options) == 2:
            pos = 3 - pos
        out.append((subj[pid], which, float(q.export[pos - 1])))
    return pd.DataFrame(out, columns=["SubjectNumber", "Which", "Choice"])


def _canon(d: pd.DataFrame) -> pd.DataFrame:
    return d.sort_values(["SubjectNumber", "Which", "Choice"]).reset_index(drop=True)


@needs_raw
@pytest.mark.parametrize("name", NAMES)
def test_raw_export_reproduces_the_authors_long_data(name: str) -> None:
    ours = _authors_rules(name, _raw_long(name))[["SubjectNumber", "Which", "Choice"]]
    theirs = _cleaned(name)
    assert len(ours) == len(theirs) == {"study6d": 7760, "study6e": 6160}[name]
    pd.testing.assert_frame_equal(_canon(ours), _canon(theirs), check_dtype=False)


@needs_raw
@pytest.mark.parametrize(
    ("name", "key", "n"), [("study6d", 0.06365979, 194), ("study6e", 0.05568182, 176)]
)
def test_the_deposit_gives_the_authors_key(name: str, key: float, n: int) -> None:
    s = _shares(name, _cleaned(name))
    diff = s["xyz"] - s["xy"]
    assert len(diff) == n and diff.notna().all()
    assert abs(diff.mean() - key) < 5e-9
    assert gen.SPECS[name].key == key


@needs_raw
@pytest.mark.parametrize("name", NAMES)
def test_built_rows_reproduce_the_key(name: str) -> None:
    d = built(name)
    assert d["participant_id"].nunique() == gen.SPECS[name].n_built
    ours = _authors_rules(name, _built_long(name))
    theirs = _cleaned(name)
    keep = set(ours["SubjectNumber"])
    assert len(keep) == gen.SPECS[name].n_built
    theirs = theirs[theirs["SubjectNumber"].isin(keep)]
    pd.testing.assert_frame_equal(
        _canon(ours[["SubjectNumber", "Which", "Choice"]]), _canon(theirs), check_dtype=False
    )
    a, b = _shares(name, ours), _shares(name, theirs)
    assert np.allclose(a.to_numpy(), b.to_numpy(), atol=1e-12, rtol=0)
    est = (a["xyz"] - a["xy"]).mean()
    if name == "study6d":  # every kept person is built
        assert abs(est - gen.SPECS[name].key) < 5e-9
    else:  # the 164 built of the authors' 176, the same people in their own file
        assert abs(est - (b["xyz"] - b["xy"]).mean()) < 1e-12
        assert round(est, 6) == 0.058232
    # a swapped answer code moves every two-option person's shares
    bad = _shares(name, _authors_rules(name, _built_long(name, swap=True)))
    assert not np.allclose(bad.to_numpy(), a.to_numpy())


# ---------------------------------------------------------------------------
# The rows
# ---------------------------------------------------------------------------


@needs_raw
@pytest.mark.parametrize("name", NAMES)
def test_rows_carry_only_the_words_the_notes_declare_as_ours(name: str) -> None:
    d = built(name)
    notes = load(gen.recipe_path(name)).notes or ""
    for words in [gen.RANDOM_ORDER, "'Option 1:', 'Option 2:'", "transcribed from Instructions1"]:
        assert words in notes
    q = {o.split(" Only return")[0] for o in d["outcome"]}
    assert q <= {gen.question_text(2), gen.question_text(3)}
    assert all(x.startswith("Choose whichever option you prefer. 1 means") for x in q)
    assert "you should choose whichever option you prefer" in gen.instructions(name)
    cond = d["condition"]
    assert cond.str.startswith("In this study, you will be asked to make several decisions").all()
    assert not cond.str.contains("INSTRUCTIONS").any()
    assert not cond.str.contains("Click the arrow").any()
    assert not cond.str.contains("True or False").any()  # the comprehension questions
    assert cond.str.contains(gen.RANDOM_ORDER, regex=False).all()
    if name == "study6e":  # Instructions3, never Instructions3_Orig alone
        assert cond.str.contains("whether you try A or B is entirely up to you").all()
    # the dominance checks are not outcomes
    assert not any(q.tag.startswith("OD") for q in gen.experiment(name).questions)
