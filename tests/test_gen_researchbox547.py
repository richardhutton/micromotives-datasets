"""The researchbox547 recipes (Wight et al., "Sharing Food Can Backfire") and their key.

The generator simulates each study's .qsf flow for every arm, puts one clause of ours where the
child's name was piped, and codes the authors' main-analysis sample. These tests stop a hand
edit drifting from it, and check the facts the rows rest on:

- the recipes and coded files are what the generator writes; only Studies 2-4 are built, and
  Study 5's child options really are carried forward from the person's own sort;
- the .sav's export labels quote each built question and its options (the column answers it);
  a changed option label is caught;
- the displayed pictures are exactly the ones listed as dropped, none is described; a
  planted one is seen;
- every kept row's randomised fields are what the flow sets for its arm; a tampered fill fails;
- Study 4's indulgent "stand out" sentence is gated on a value the randomiser never sets;
- the declared empty-name exclusions, and that no row carries anything per person;
- the answer key: each study's main logistic regression from its .sps, fitted on the deposit
  and on the BUILT rows (unhealthy read from the option's words in the row's own question),
  agrees to 1e-9, and each arm's count of unhealthy choices agrees exactly; reading the
  answers without the per-arm recode breaks it.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_researchbox547.py"
PROCESSED = REPO / "data" / "processed"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_researchbox547", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_researchbox547"] = mod  # dataclasses look their module up here
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.BOX.exists(), reason="researchbox547 deposit not fetched")
NAMES = ["study2", "study3", "study4"]


def built(name: str) -> pd.DataFrame:
    path = PROCESSED / f"researchbox547_{name}.parquet"
    if not path.exists():
        pytest.skip(f"researchbox547_{name} not built")
    return pd.read_parquet(path)


def test_only_studies_2_to_4_have_recipes() -> None:
    assert sorted(p.stem for p in (REPO / "recipes").glob("researchbox547_*.yaml")) == [
        f"researchbox547_{n}" for n in NAMES
    ]
    assert set(gen.NOT_BUILT) == {"study1", "study5"}
    assert [s.name for s in gen.SPECS] == NAMES


@needs_raw
@pytest.mark.parametrize("name", NAMES)
def test_recipe_and_coded_file_are_what_the_generator_writes(name: str) -> None:
    spec = gen.BY_NAME[name]
    assert gen.recipe_path(spec).read_text() == gen.render(spec)
    assert (gen.RAW / gen.data_file(spec)).read_text() == gen.prep(spec).to_csv(index=False)
    r = load(gen.recipe_path(spec))
    assert len(r.condition.arms) == {"study2": 4, "study3": 8, "study4": 8}[name]


@needs_raw
def test_study5_options_are_the_persons_own_sort() -> None:
    (qsf,) = (gen.BOX / "Materials").glob("Study 5 #78575 *.qsf")
    sv = gen.Survey(qsf)
    for tag, hidden in (("CFO_like", "2favorite"), ("CFO_dislike", "2notfavorite")):
        dyn = sv.q(tag)["DynamicChoices"]
        assert dyn["Locator"] == f"q://{sv.q(hidden)['QuestionID']}/ChoiceGroup/DisplayedChoices"
        src = sv.q(hidden)["DynamicChoices"]["Locator"]
        assert re.fullmatch(
            rf"q://{sv.q('sort')['QuestionID']}/ChoiceGroup/SelectedChoicesInGroup/[12]", src
        )


@needs_raw
@pytest.mark.parametrize("name", NAMES)
def test_files_labels_pictures(name: str) -> None:
    spec = gen.BY_NAME[name]
    gen.check_files(spec)
    gen.check_sav_labels(spec)
    gen.check_pictures(spec)
    gen.check_order_unrecorded(spec)


@needs_raw
def test_a_changed_option_label_is_caught(monkeypatch: pytest.MonkeyPatch) -> None:
    spec = gen.BY_NAME["study2"]
    real = gen.read_deposit

    def tampered(s: Any) -> tuple[pd.DataFrame, Any]:
        df, meta = real(s)
        vl = meta.variable_value_labels["CFS_1_4H_hfirst"]
        vl[5.0], vl[6.0] = vl[6.0], vl[5.0]
        return df, meta

    monkeypatch.setattr(gen, "read_deposit", tampered)
    with pytest.raises(AssertionError):
        gen.check_sav_labels(spec)


def test_a_planted_picture_is_seen() -> None:
    assert gen._IMG.findall('<p>x</p><img src="https://x/Graphic.php?IM=IM_abc" />') == ["IM_abc"]
    assert gen._IMG.findall("<p>no picture</p>") == []


@needs_raw
def test_no_row_describes_a_picture() -> None:
    for name in NAMES:
        for a in gen.arms(gen.BY_NAME[name]):
            assert "picture" not in a.text and "<img" not in a.text, (name, a.values)


@needs_raw
def test_a_tampered_fill_fails() -> None:
    spec = gen.BY_NAME["study3"]
    df = gen.kept(spec).copy()
    i = df.index[0]
    df.loc[i, "shareText"] = "will NOT" if df.loc[i, "shareText"] == "WILL" else "WILL"
    with pytest.raises(AssertionError):
        gen.check_data_matches_qsf(spec, df)


@needs_raw
def test_study4_indulgent_sentence_is_never_shown() -> None:
    spec = gen.BY_NAME["study4"]
    sv = gen.Survey(gen.qsf_path(spec))
    assert {c["CFO"] for c in sv.randomiser_cells()} == {"healthy", "unhealthy"}
    (p,) = [p for p in sv.by_id.values() if "Hamburger w/ fries and Chicken" in p["QuestionText"]]
    assert '"RightOperand": "indulgent"' in json.dumps(p["DisplayLogic"])
    for a in gen.arms(spec):
        stands = "two in particular stand out" in a.text
        assert stands == (a.values["CFO"] == "healthy"), a.values


@needs_raw
def test_empty_name_exclusions_and_counts() -> None:
    want = {"study2": (792, 1), "study3": (548, 1), "study4": (830, 0)}
    for name, (n, empty) in want.items():
        spec = gen.BY_NAME[name]
        df = gen.analysed(spec)
        assert len(df) == n and int(gen.name_empty(df).sum()) == empty
        assert len(gen.kept(spec)) == n - empty


@needs_raw
@pytest.mark.parametrize("name", NAMES)
def test_rows_carry_nothing_per_person(name: str) -> None:
    d = built(name)
    spec = gen.BY_NAME[name]
    assert len(d) == d["participant_id"].nunique() == spec.n_kept - spec.empty_name
    texts = {a.text for a in gen.arms(spec)}  # menu order shows only in the options
    assert len(texts) == {"study2": 2, "study3": 8, "study4": 4}[name]
    assert set(d["condition"]) == texts
    questions = {a.question for a in gen.arms(spec)}  # share x menu order: 4 wordings
    assert len(questions) == 4
    assert {o.split(" Only return")[0] for o in d["outcome"]} == questions
    assert d["condition"].str.contains(re.escape(gen.CHILD)).all()
    assert d["outcome"].str.contains(re.escape(gen.CHILD)).all()
    assert not d["condition"].str.contains(r"\$\{|@@|<img|\[Field", regex=True).any()


# ---------------------------------------------------------------------------
# The answer key: the authors' main logistic regression (Code/*.sps)
# ---------------------------------------------------------------------------


def logit(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Maximum-likelihood logistic regression by IRLS (what SPSS LOGISTIC REGRESSION fits)."""
    b = np.zeros(x.shape[1])
    for _ in range(100):
        p = 1 / (1 + np.exp(-x @ b))
        w = p * (1 - p)
        step = np.linalg.solve(x.T @ (x * w[:, None]), x.T @ (y - p))
        b += step
        if np.max(np.abs(step)) < 1e-13:
            break
    return np.asarray(b)


def design(cols: list[np.ndarray]) -> np.ndarray:
    """Intercept, the dummies, and (for two) their product, in the .sps order."""
    x = [np.ones(len(cols[0])), *cols]
    if len(cols) == 2:
        x.append(cols[0] * cols[1])
    return np.column_stack(x)


def deposit_fit(name: str, people: str = "kept") -> tuple[np.ndarray, pd.DataFrame]:
    spec = gen.BY_NAME[name]
    df = gen.kept(spec) if people == "kept" else gen.analysed(spec)
    cols = [df[c].to_numpy(float) for c, _ in spec.key]
    return logit(df[spec.dv].to_numpy(float), design(cols)), df


def built_frame(name: str, ignore_order: bool = False) -> pd.DataFrame:
    """Per row: the authors' dummies from the factors, and unhealthy read from the WORDS of
    the option the coded answer points to in the row's own question."""
    spec = gen.BY_NAME[name]
    d = built(name)
    unhealthy_meals = {m for k, m in gen.meal_names(spec).items() if k in gen.UNHEALTHY}
    f = d["factors"].map(lambda x: x if isinstance(x, dict) else json.loads(x))

    def meal(row: pd.Series) -> str:
        if ignore_order:  # the mutation: read the answer as the healthy-first position
            names = gen.meal_names(spec)
            return str(names[int(row["response_num"])])
        opts = re.findall(r'\d means "([^"]+)"', row["outcome"])
        return str(opts[int(row["response_num"]) - 1])

    out = pd.DataFrame({"unhealthy": d.apply(meal, axis=1).isin(unhealthy_meals).astype(int)})
    for col, cond in spec.key:
        fac, lev = cond.split("=")
        out[col] = f.map(lambda x, fac=fac, lev=lev: int(x[fac] == lev)).values
    out["arm"] = d["condition_num"].values
    return out


# The .sps main model (intercept, dummies, product), rounded, for the record: on the kept
# people (the built rows' people) and on the authors' own N (before the empty-name rule).
RECORDED = {
    "study2": [-0.4643, 0.4439],
    "study3": [-0.6174, 0.0636, -0.0322, 0.8524],
    "study4": [0.1929, 0.0412, -0.1642, 0.5801],
}
AUTHORS_N = {
    "study2": [-0.4643, 0.4389],
    "study3": [-0.6174, 0.0636, -0.0322, 0.8653],
    "study4": [0.1929, 0.0412, -0.1642, 0.5801],
}


@needs_raw
@pytest.mark.parametrize("name", NAMES)
def test_the_authors_model_on_their_own_n(name: str) -> None:
    b, df = deposit_fit(name, "all")
    assert len(df) == gen.BY_NAME[name].n_kept
    assert np.round(b, 4).tolist() == AUTHORS_N[name]


@needs_raw
@pytest.mark.parametrize("name", NAMES)
def test_built_rows_reproduce_the_authors_model(name: str) -> None:
    spec = gen.BY_NAME[name]
    dep, _ = deposit_fit(name)
    b = built_frame(name)
    ours = logit(
        b["unhealthy"].to_numpy(float), design([b[c].to_numpy(float) for c, _ in spec.key])
    )
    assert np.allclose(dep, ours, atol=1e-9, rtol=0)
    assert np.round(dep, 4).tolist() == RECORDED[name]
    # reading the answer without the arm's menu order breaks it
    bad = built_frame(name, ignore_order=True)
    worse = logit(
        bad["unhealthy"].to_numpy(float), design([bad[c].to_numpy(float) for c, _ in spec.key])
    )
    assert not np.allclose(dep, worse, atol=1e-6, rtol=0)


@needs_raw
@pytest.mark.parametrize("name", NAMES)
def test_unhealthy_counts_per_arm_are_the_deposits(name: str) -> None:
    spec = gen.BY_NAME[name]
    df = gen.kept(spec)
    cmap = gen.codes(spec)
    arm_of = {
        tuple(cmap[f][v] for f, v in a.values.items()): i for i, a in enumerate(gen.arms(spec))
    }
    dep_arm = [arm_of[tuple(cmap[f][r[f]] for f in spec.assign)] for _, r in df.iterrows()]
    dep = df.assign(arm=dep_arm).groupby("arm")[spec.dv].agg(["sum", "count"])
    b = built_frame(name).groupby("arm")["unhealthy"].agg(["sum", "count"])
    assert (dep.astype(int).values == b.astype(int).values).all()
