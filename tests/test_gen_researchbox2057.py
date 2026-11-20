"""The researchbox2057 recipes (forced choice versus a no-choice option) and their answer key.

The generator reads every page from the .qsf through its survey flow, each answer's codes
from the .sav's value labels, and each person's group from which columns they answered.
These tests stop a hand edit drifting from it, and check the facts the rows rest on:

- each recipe and coded file is what the generator writes; no picture in any .qsf, and a
  planted one is seen; the timestamped files hold the same answers;
- the option-picking pattern accepts every pick and rejects every way out, both ways;
- each group's size, the 3a .qsf's missing recode, 2b's no-choice-first order;
- the answer key: the authors' R code, transcribed column by column and run on the deposit,
  and the same model run on the BUILT rows (options read back from each row's own arm) give
  the same coefficients to 1e-9: their pooled logit and every per-problem logit (1a, 1b,
  2a, 2b, S1 on the relative choice of the target option; 3a, 3b on choosing no option);
  the Table 3-4 shares printed in Additional Files' R comments (2a, 2b) come out of the
  built rows; 4a and 4b, whose second stage is not built, match the deposit on the shares
  the rows carry. A swapped answer code breaks the 1b model.

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
GEN = REPO / "scripts" / "gen_researchbox2057.py"
PROCESSED = REPO / "data" / "processed"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_researchbox2057", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_researchbox2057"] = mod  # dataclasses look their module up here
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.RAW.exists(), reason="researchbox2057 deposit not fetched")
STUDIES = list(gen.STUDIES)


def built(study: str) -> pd.DataFrame:
    path = PROCESSED / f"researchbox2057_{gen.name_of(study)}.parquet"
    if not path.exists():
        pytest.skip(f"researchbox2057 {study} not built")
    return pd.read_parquet(path)


# ---------------------------------------------------------------------------
# The generator's outputs and the facts they rest on
# ---------------------------------------------------------------------------


@needs_raw
@pytest.mark.parametrize("study", STUDIES)
def test_recipe_and_coded_file_are_what_the_generator_writes(study: str) -> None:
    e = gen.experiment(study)
    assert gen.recipe_path(e).read_text() == gen.render(e)
    load(gen.recipe_path(e))
    assert (gen.RAW / gen.data_file(study)).read_text() == gen.prep(study).to_csv(index=False)


def test_every_study_has_one_recipe_and_none_fails() -> None:
    have = sorted(p.stem for p in (REPO / "recipes").glob("researchbox2057_*.yaml"))
    assert have == sorted(f"researchbox2057_{gen.name_of(s)}" for s in STUDIES)
    assert gen.NOT_BUILT == ()
    assert set(gen.NOT_BUILT_OUTCOMES) == {"2b", "4a", "4b"}


@needs_raw
@pytest.mark.parametrize("study", STUDIES)
def test_no_pictures_and_the_timestamped_copy_agrees(study: str) -> None:
    gen.check_pictures(study)
    gen.check_timestamped(study)


def test_a_planted_picture_is_seen() -> None:
    assert gen.graphics_in('{"QuestionText":"<p>x</p>"}') == (0, set())
    assert gen.graphics_in('{"QuestionText":"<IMG src=x>"}')[0] == 1
    assert gen.graphics_in('{"GraphicID":"IM_abc123XYZ"}')[1] == {"IM_abc123XYZ"}


def test_pick_accepts_picks_and_rejects_ways_out() -> None:
    picks = [
        "I would buy Brand A",
        "I would go to Restaurant B",
        "Rent Apartment C",
        "Buy Brand B",
        "I would admit Applicant A",
        "I would buy Wine B",
        "I would buy Option C",
    ]
    ways_out = [
        "I would look for other options",
        "I would go to another store",
        "I would go to another restaurant",
        "Not buy any of these hard drives and go to another store",
        "I would not buy either of these cameras",
        "I would not go to either of these restaurants",
        "I would look for other applicants",
        "Not rent any of these apartments and visit another rental agency",
    ]
    assert all(gen.PICK.match(o) for o in picks)
    assert not any(gen.PICK.match(o) for o in ways_out)


def test_a_table_is_one_line_per_row() -> None:
    html = (
        "<span>Imagine X. You have:</span><div>&nbsp;<table><tbody>"
        "<tr><td>&nbsp;</td><td>Zoom</td><td>Price</td></tr>"
        "<tr><td>Brand A</td><td>Superior</td><td>High</td></tr></tbody></table></div>"
    )
    assert gen.to_text(html) == "Imagine X. You have:\n\nZoom | Price\nBrand A | Superior | High"


@needs_raw
def test_group_sizes_and_codes() -> None:
    sizes = {
        "1a": [101, 103],
        "1b": [153, 154],
        "2a": [201, 200, 199, 201],
        "2b": [199, 202, 202, 200, 201, 198],
        "3a": [150, 151],
        "3b": [201, 203],
        "4a": [150, 151],
        "4b": [249, 251],
        "S1": [201, 200, 201, 201, 201, 200],
    }
    for study, want in sizes.items():
        e = gen.experiment(study)
        coded = gen.prep(study)
        first = coded[f"cell_{e.problems[0]}"]
        got = [int((first == a.raw).sum()) for a in e.arms if a.factors["problem"] == e.problems[0]]
        assert got == want, study
    # 3a's .qsf keys the way out 4; its .sav and data say 3
    (p,) = [a.page for a in gen.experiment("3a").arms if a.page.tag == "CamNorange"]
    assert p.codes == [1, 2, 3]
    # 2b lists walking away first, and codes it 1
    (p,) = [a.page for a in gen.experiment("2b").arms if a.page.tag == "HDCoNonf"]
    assert not gen.PICK.match(p.options[0]) and p.codes == [1, 2, 3]


@needs_raw
def test_choice_is_a_text_factor_only_in_2b() -> None:
    for study in ("1a", "1b", "2a", "2b", "4a", "4b", "S1"):
        assert ("choice" in gen.experiment(study).text_factors) == (study == "2b"), study


# ---------------------------------------------------------------------------
# The answer key
# ---------------------------------------------------------------------------


def glm_logit(y: np.ndarray, xs: np.ndarray) -> np.ndarray:
    """R's glm(family = binomial) as glm.fit computes it (tests/test_gen_researchbox2562.py)."""
    xs = np.column_stack([np.ones(len(y)), xs])
    mu = (y + 0.5) / 2
    eta = np.log(mu / (1 - mu))

    def deviance(m: np.ndarray) -> float:
        with np.errstate(divide="ignore", invalid="ignore"):
            t = np.where(y == 1, -np.log(m), -np.log(1 - m))
        return float(2 * t.sum())

    dev_old = deviance(mu)
    b = np.zeros(xs.shape[1])
    for _ in range(25):
        w = mu * (1 - mu)
        z = eta + (y - mu) / w
        b = np.linalg.solve(xs.T @ (xs * w[:, None]), xs.T @ (w * z))
        eta = xs @ b
        mu = 1 / (1 + np.exp(-eta))
        dev = deviance(mu)
        if abs(dev - dev_old) / (abs(dev) + 0.1) < 1e-8:
            break
        dev_old = dev
    return b


# The authors' R code, transcribed: for each problem, its columns (one per group) and, per
# column, the codes for target (TargetXChosen), competitor (CompXChosen) and no choice
# (XNochoice). Group dummies come from which column a person answered, as in the R code.
AUTHOR_NAME = {  # our problem key -> the authors' variable prefix
    "camcorder": "Cam",
    "camera": "Cam",
    "laptop": "Lap",
    "speaker": "Spe",
    "restaurant": "Rest",
    "cd_player": "CD",
    "barbecue": "BBQ",
    "microwave": "Mic",
    "cassette": "Cas",
    "binoculars": "Bin",
    "apartment": "Apa",
    "hard_drive": "HD",
    "admission": "Adm",
    "wine": "Wine",
}
DEPOSIT: dict[str, dict[str, Any]] = {
    "1a": {
        "problems": {
            "Cam": ["CamFor", "CamNon"],
            "Lap": ["LaptopFor", "LaptopNon"],
            "Spe": ["SpeakFor", "SpeakNon"],
            "Rest": ["RestaForc", "RestaNon"],
        },
        "target": 2,
        "comp": 1,
        "dummies": {"NonForced": lambda c: "Non" in c},
    },
    "2a": {
        "problems": {  # H2, the compromise problems
            "Cam": ["CamCoFor", "CamCompFor", "CamCoNon", "CamCompNon"],
            "CD": ["CDCoFor", "CDCompFor", "CDCoNon", "CDCompNon"],
            "BBQ": ["BBQCoFor", "BBQCompFor", "BBQCoNon", "BBQCompNon"],
        },
        "target": 2,
        "comp": 1,
        "dummies": {"Three": lambda c: "Comp" in c, "NonForced": lambda c: "Non" in c},
    },
    "2b": {
        "problems": {
            "Apa": ["ApaCoForc", "ApaDomForc", "ApComForc", "ApaCoNonf", "ApaDomNonf", "ApComNonf"],
            "Cam": [
                "CamCoFor",
                "CamDomForc",
                "CamComForc",
                "CamCoNonf",
                "CamDomNonf",
                "CamComNonf",
            ],
            "Spe": [
                "SpeCoForc",
                "SpeDomForc",
                "SpeaComForc",
                "SpeCoNonf",
                "SpeDomNonf",
                "SpeaComNonf",
            ],
            "HD": ["HDCoFor", "HDDomForc", "HDComForc", "HDCoNonf", "HDDomNonf", "HDComNonf"],
        },
        "target": lambda c: 3 if "Nonf" in c else 2,  # no choice is code 1 when offered
        "comp": lambda c: 2 if "Nonf" in c else 1,
        "dummies": {
            "Attr": lambda c: "Dom" in c,
            "Comp": lambda c: "Com" in c,
            "NonForced": lambda c: "Nonf" in c,
        },
    },
    "3a": {
        "problems": {
            "Cam": ["CamNorange", "CamRange"],
            "Lap": ["LaptNorange", "LaptRange"],
            "Adm": ["AdmNorange", "AdmRange"],
            "Wine": ["WineNorange", "WineRange"],
            "Rest": ["RestNorange", "RestRange"],
        },
        "nochoice": 3,
        "dummies": {"Range": lambda c: "Norange" not in c},
    },
}
DEPOSIT["1b"] = DEPOSIT["1a"]
DEPOSIT["3b"] = DEPOSIT["3a"]
DEPOSIT["S1"] = DEPOSIT["2b"] | {"target": 2, "comp": 1}


def _code(rule: Any, col: str) -> int:
    return int(rule(col) if callable(rule) else rule)


def deposit_long(study: str) -> pd.DataFrame:
    """One row per person x problem, the authors' variables, from the raw deposit."""
    spec = DEPOSIT[study]
    df = gen.read_data(study)
    rows = []
    for i, r in df.iterrows():
        for prob, cols in spec["problems"].items():
            (col,) = [c for c in cols if pd.notna(r[c])]
            v = int(r[col])
            row: dict[str, Any] = {"who": i, "problem": prob}
            if "nochoice" in spec:
                row["y"] = int(v == spec["nochoice"])
            else:
                row["y"] = (
                    1
                    if v == _code(spec["target"], col)
                    else 0
                    if v == _code(spec["comp"], col)
                    else np.nan
                )
            for d, f in spec["dummies"].items():
                # a person's dummies come from their FIRST problem's column, as in the R code
                first = next(c for c in next(iter(spec["problems"].values())) if pd.notna(r[c]))
                row[d] = int(f(first))
            rows.append(row)
    return pd.DataFrame(rows)


def _f(x: Any) -> dict[str, str]:
    return x if isinstance(x, dict) else json.loads(x)


def built_long(study: str, swap: bool = False) -> pd.DataFrame:
    """The same variables from the BUILT rows: each answer read back through its own arm's
    options (A, B, C or the way out), problems named the authors' way."""
    d = built(study)
    e = gen.experiment(study)
    letters = []
    for a in e.arms:
        letters.append(
            [
                (m.group(1) if (m := re.search(r" ([A-C])$", o)) and gen.PICK.match(o) else "-")
                for o in a.page.options
            ]
        )
    spec = DEPOSIT[study]
    f = d["factors"].map(_f)
    out = pd.DataFrame(
        {
            "who": d["participant_id"].values,
            "problem": f.map(lambda x: AUTHOR_NAME[x["problem"]]).values,
        }
    )
    resp = d["response_num"].astype(int).to_numpy()
    if swap:
        resp = np.where(resp == 1, 2, np.where(resp == 2, 1, resp))
    letter = [letters[c][r - 1] for c, r in zip(d["condition_num"], resp, strict=True)]
    if "nochoice" in spec:
        out["y"] = [int(x == "-") for x in letter]
    else:
        out["y"] = [1 if x == "B" else 0 if x == "A" else np.nan for x in letter]
    dummies = {
        "NonForced": lambda x: x["choice"] == "no_choice_option",
        "Three": lambda x: x.get("option_set") not in (None, "two_options"),
        "Attr": lambda x: x.get("option_set") == "attraction",
        "Comp": lambda x: x.get("option_set") == "compromise",
        "Range": lambda x: x.get("values") == "ranges",
    }
    for dname in spec["dummies"]:
        out[dname] = f.map(dummies[dname]).astype(int).values
    return out[out["problem"].isin(spec["problems"])].reset_index(drop=True)


def fit(long: pd.DataFrame, study: str, problem: str | None = None) -> np.ndarray:
    spec = DEPOSIT[study]
    probs = list(spec["problems"])
    x = long.dropna(subset=["y"])
    if problem is not None:
        x = x[x["problem"] == problem]
    cols = [x[d].to_numpy(float) for d in spec["dummies"]]
    if problem is None:  # problem dummies, the first problem the reference, as in R
        cols += [(x["problem"] == p).to_numpy(float) for p in probs[1:]]
    return glm_logit(x["y"].to_numpy(float), np.column_stack(cols))


KEYED = ["1a", "1b", "2a", "2b", "3a", "3b", "S1"]


@needs_raw
@pytest.mark.parametrize("study", KEYED)
def test_built_rows_reproduce_the_authors_models(study: str) -> None:
    dep, ours = deposit_long(study), built_long(study)
    assert len(ours) == len(dep)
    assert np.allclose(fit(dep, study), fit(ours, study), atol=1e-9, rtol=0)
    for prob in DEPOSIT[study]["problems"]:
        assert np.allclose(fit(dep, study, prob), fit(ours, study, prob), atol=1e-9, rtol=0)


# each model1's group coefficients (pooled logit with problem dummies), 3 dp
POOLED: dict[str, list[float]] = {
    "1a": [-0.019],  # NonForced
    "1b": [-0.031],  # NonForced
    "2a": [0.422, -0.06],  # Three, NonForced (compromise problems)
    "2b": [0.862, 0.282, -0.017],  # Attr, Comp, NonForced
    "3a": [-0.087],  # Range
    "3b": [0.217],  # Range
    "S1": [1.099, 1.231, 0.118],  # Attr, Comp, NonForced
}


@needs_raw
def test_the_authors_pooled_estimates_for_the_record() -> None:
    """The group coefficients of each pooled model (model1 in each R file), to 3 dp."""
    for s in KEYED:
        got = np.round(fit(built_long(s), s), 3)[1 : 1 + len(DEPOSIT[s]["dummies"])]
        assert got.tolist() == POOLED[s], s


@needs_raw
def test_a_swapped_answer_breaks_the_model() -> None:
    dep = deposit_long("1b")
    assert not np.allclose(fit(dep, "1b"), fit(built_long("1b", swap=True), "1b"), atol=1e-6)


def _shares(d: pd.DataFrame, study: str, keep: Any) -> dict[str, float]:
    """Percent choosing each letter among built rows whose factors satisfy `keep`."""
    e = gen.experiment(study)
    f = d["factors"].map(_f)
    sel = d[f.map(keep).values]
    letters = {
        a.raw - 1: [
            (m.group(1) if (m := re.search(r" ([A-C])$", o)) and gen.PICK.match(o) else "none")
            for o in a.page.options
        ]
        for a in e.arms
    }
    picked = [
        letters[c][r - 1]
        for c, r in zip(sel["condition_num"], sel["response_num"].astype(int), strict=True)
    ]
    s = pd.Series(picked).value_counts(normalize=True) * 100
    return {str(k): float(v) for k, v in s.items()}


@needs_raw
def test_the_printed_table_3_and_4_shares() -> None:
    """Additional Files' R code prints these shares in comments; the built rows give them."""
    comp2a = {"camera", "cd_player", "barbecue"}
    attr2a = {"microwave", "cassette", "binoculars"}

    def cell(probs: set[str], opt: str, choice: str) -> Any:
        return lambda x: (
            x["problem"] in probs
            and (x.get("option_set") == "two_options") == (opt == "two")
            and x["choice"] == choice
        )

    printed_2a = [
        (comp2a, "two", "forced", {"A": 53.6, "B": 46.4}),
        (comp2a, "three", "forced", {"A": 30.7, "B": 40.2, "C": 29.2}),
        (comp2a, "two", "no_choice_option", {"A": 45.4, "B": 36.5, "none": 18.1}),
        (comp2a, "three", "no_choice_option", {"A": 28.2, "B": 34.8, "C": 27.0, "none": 10.0}),
        (attr2a, "two", "forced", {"A": 56.7, "B": 43.3}),
        (attr2a, "three", "forced", {"A": 30.2, "B": 64.3, "C": 5.5}),
        (attr2a, "two", "no_choice_option", {"A": 47.6, "B": 36.5, "none": 15.9}),
        (attr2a, "three", "no_choice_option", {"A": 31.7, "B": 56.7, "C": 5.0, "none": 6.6}),
    ]
    d = built("2a")
    for probs, opt, choice, want in printed_2a:
        got = _shares(d, "2a", cell(probs, opt, choice))
        assert {k: round(v, 1) for k, v in got.items()} == want, (opt, choice, got)

    def cell2b(setting: str, choice: str) -> Any:
        return lambda x: x.get("option_set") == setting and x["choice"] == choice

    printed_2b = [  # printed "≈", to the decimals printed
        ("two_options", "forced", {"A": 51.4, "B": 48.6}),
        ("compromise", "forced", {"A": 28, "B": 35.2, "C": 36.9}),
        ("attraction", "forced", {"A": 31.5, "B": 61.9, "C": 6.7}),
        ("two_options", "no_choice_option", {"none": 20.6, "A": 43.3, "B": 36.1}),
        ("compromise", "no_choice_option", {"none": 19.1, "A": 25.3, "B": 27.7, "C": 28}),
        ("attraction", "no_choice_option", {"none": 16.6, "A": 23.7, "B": 54.5, "C": 5.4}),
    ]
    d = built("2b")
    for setting, choice, want in printed_2b:
        got = _shares(d, "2b", cell2b(setting, choice))
        assert set(got) == set(want), (setting, choice)
        for k, v in want.items():
            # printed with "≈": one value is off its own rounding (compromise, forced, B
            # printed 35.2; deposit and rows both 284/808 = 35.15), so 0.1 on one decimal
            tol = 0.5 if float(v).is_integer() else 0.1
            assert abs(got[k] - v) <= tol, (setting, choice, k, got[k], v)


@needs_raw
@pytest.mark.parametrize(
    ("study", "single", "two"),
    [
        ("4a", ["CamSin", "LapSin", "ResSin"], ["CamTwo1", "LapTwo1", "ResTwo1"]),
        ("4b", ["CamSin", "SpeSin", "HDSin"], ["CamTwo1", "SpeTwo1", "HDTwo1"]),
    ],
)
def test_4a_4b_shares_the_rows_carry(study: str, single: list[str], two: list[str]) -> None:
    """The authors' Nochoice (single stage: code 3 in 4a, 4 in 4b) and TwoSt*Chosen (two
    stage, first choice = 2) per problem, deposit against built rows."""
    df = gen.read_data(study)
    d = built(study)
    e = gen.experiment(study)
    way_out = 3 if study == "4a" else 4
    for t, (s_col, t_col) in enumerate(zip(single, two, strict=True)):
        rows = d[d["task_num"] == t]
        f = rows["factors"].map(_f)
        sg = rows[f.map(lambda x: x["choice"] == "single_stage").values]
        tw = rows[f.map(lambda x: x["choice"] == "two_stage_first_choice").values]
        dep_s = df[s_col].dropna()
        assert len(sg) == len(dep_s) and len(tw) == df[t_col].notna().sum()
        (arm,) = [a for a in e.arms if a.page.tag == s_col]
        pos = arm.page.codes.index(way_out) + 1
        assert (sg["response_num"] == pos).mean() == pytest.approx(
            (dep_s == way_out).mean(), abs=1e-12
        )
        assert (tw["response_num"] == 2).mean() == pytest.approx(
            (df[t_col].dropna() == 2).mean(), abs=1e-12
        )
