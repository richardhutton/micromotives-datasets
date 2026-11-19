"""The researchbox2562 recipes (Evangelidis 2026, the skimpflation penalty) and their answer key.

The generator reads each scenario from the study's .qsf and derives each person's arm from
which of the deposit's per-arm columns is filled. These tests stop a hand edit drifting from
it, and check the facts the rows rest on:

- each recipe and coded file is what the generator writes, and the codebooks agree with the
  .qsf question by question;
- N, and N by arm, are the deposit's (no exclusions were pre-registered; the 4 follow-up
  loses the one person who moved no slider);
- the scale check fails on a reversed scale; the codebook check fails on a changed word;
- recomputed from the BUILT rows, the R scripts' models come out estimate for estimate and
  standard error for standard error, against the figures base R prints for the authors'
  own code run on the deposit (19 Nov 2026; tidyverse, epiDisplay, expss and car are only
  for printing and effect coding, so the summary() models were re-run in base R with haven,
  line for line): the logits of unfair on the change dummies in every fairness study
  (including the subsets by product, transparency, communication and cost level), the 4
  follow-up Welch t tests, the pilots' and
  Study 6's and 7's one-sample t tests against 5, Study 6's chi-squares and its logits of
  choosing option 3 on the quality rating, and Study 7's logits of buying. Every logit is
  refitted here by glm.fit's own procedure (`glm_logit`), every estimate, SE, t, df and
  chi-square agreeing to 1e-9 (the Welch df to 1e-7, R having printed 13 digits);
- swapping a factor (study 3's action, study 4's cost level) breaks the reproduction;
- 5a, 5b and 5c are NOT_BUILT (product photographs with printed words the rows lack), and
  no recipe of theirs exists.

Tests needing the gitignored deposit or build skip on a fresh clone.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from micromotives_datasets.recipe import load

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "gen_researchbox2562.py"
PROCESSED = REPO / "data" / "processed"


def _gen() -> Any:
    spec = importlib.util.spec_from_file_location("gen_researchbox2562", GEN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_researchbox2562"] = mod  # dataclasses look their module up here
    spec.loader.exec_module(mod)
    return mod


gen = _gen()
needs_raw = pytest.mark.skipif(not gen.RAW.exists(), reason="researchbox2562 deposit not fetched")
NAMES = [t for t in gen.LABEL if t not in gen.NOT_BUILT]


def built(name: str) -> pd.DataFrame:
    path = PROCESSED / f"researchbox2562_{name}.parquet"
    if not path.exists():
        pytest.skip(f"researchbox2562_{name} not built")
    df = pd.read_parquet(path)
    if df["factors"].notna().all():
        df = pd.concat([df.reset_index(drop=True), pd.json_normalize(df["factors"])], axis=1)
    return df


@needs_raw
@pytest.mark.parametrize("exp", gen.experiments(), ids=lambda e: e.name)
def test_recipe_is_what_the_generator_writes(exp: Any) -> None:
    assert gen.recipe_path(exp).read_text() == gen.render(exp)
    load(gen.recipe_path(exp))


def test_every_experiment_has_a_recipe() -> None:
    assert sorted(p.stem for p in (REPO / "recipes").glob("researchbox2562_*.yaml")) == sorted(
        f"researchbox2562_{n}" for n in NAMES
    )
    assert {e.name for e in gen.experiments()} == set(NAMES)


@needs_raw
@pytest.mark.parametrize("tag", NAMES)
def test_coded_file_is_what_the_generator_writes(tag: str) -> None:
    assert (gen.RAW / gen.data_file(tag)).read_text() == gen.prep(tag).to_csv(index=False)


@needs_raw
@pytest.mark.parametrize("tag", NAMES)
def test_codebook_matches_the_qsf(tag: str) -> None:
    gen.check_codebook(tag)


@needs_raw
def test_the_codebook_check_catches_a_changed_word(monkeypatch: pytest.MonkeyPatch) -> None:
    sv = gen.Survey("study7")
    sv.qs["Size"] = dict(sv.qs["Size"])
    sv.qs["Size"]["QuestionText"] = sv.qs["Size"]["QuestionText"].replace("909 ml", "900 ml")
    monkeypatch.setattr(gen, "Survey", lambda tag: sv)
    with pytest.raises(AssertionError):
        gen.check_codebook("study7")


@needs_raw
def test_n_and_arms_are_the_deposits() -> None:
    want = {
        "study1": {1: 269, 2: 239, 3: 236, 4: 259, 5: 255, 6: 244},
        "study3": {1: 396, 2: 395, 3: 384, 4: 426},
        "study4_followup": {1: 100, 2: 96, 3: 104},
        "study7": {1: 247, 2: 270, 3: 244, 4: 244},
        "study2a": {1: 457, 2: 498, 3: 531, 4: 490, 5: 534, 6: 496},
        "study2b": {1: 441, 2: 446, 3: 408, 4: 451, 5: 452, 6: 482, 7: 459, 8: 415, 9: 453},
        "study4": {1: 464, 2: 435, 3: 425, 4: 431, 5: 439, 6: 442, 7: 444, 8: 438, 9: 487},
    }
    for tag, arms in want.items():
        assert gen.prep(tag)["arm"].value_counts().to_dict() == arms, tag
    for tag in NAMES:
        assert (
            len(gen.prep(tag)) == gen.N[tag] == len(gen.read_deposit(tag)) - gen.DROPPED.get(tag, 0)
        )


@needs_raw
def test_the_scale_check_catches_a_reversed_scale() -> None:
    sv = gen.Survey("study4")
    assert gen.mc_scale(sv, "PriceEqual") == gen.FAIR_SCALE
    q = dict(sv.qs["PriceEqual"])
    q["ChoiceOrder"] = list(reversed(q["ChoiceOrder"]))
    sv.qs["PriceEqual"] = q
    with pytest.raises(AssertionError):
        gen.mc_scale(sv, "PriceEqual")


@needs_raw
def test_conditions_are_the_qsf_words_up_to_the_question() -> None:
    closing = {
        "study4_followup": None,
        "study7": gen.BUY_Q,
        "study2a_pilot": gen.QUAL_Q,
        "study2b_pilot": gen.QUAL_Q,
        "study5a_pilot": gen.QUAL_Q,
    }
    for e in gen.experiments():
        if e.name == "study6":
            continue
        sv = gen.Survey(e.name)
        first = e.outcomes[0].var
        for a, col in zip(e.arms, e.columns[first], strict=True):
            col = col.removesuffix("_1")
            scenario = a.text.split("\n\n")[0]  # 5a/5b's arm text narrates, then repeats it
            q = closing.get(e.name, gen.FAIR_Q)
            if q is None:
                q = a.items[0]["outcome_question"]
            assert sv.text(col) == f"{scenario} {q}", (e.name, a.code)
            assert "<" not in scenario and "&" not in scenario


# --------------------------------------------------------------------------------------
# The R scripts' models, from the built rows
# --------------------------------------------------------------------------------------

# summary(m)$coefficients[, 1:2], base R 4.x, the authors' code on the deposit.
R_LOGIT: dict[str, list[tuple[float, float]]] = {
    "study1": [
        (-0.89648810457628, 0.09593020071306),
        (0.86409660878504, 0.13153666215667),
        (1.66562119211361, 0.13722363207719),
    ],
    "study1_chocolate": [
        (-1.6593348835787, 0.1663748560154),
        (1.5000028450095, 0.2110057814122),
        (2.8036694215822, 0.2254129676847),
    ],
    "study1_streaming_platform": [
        (-0.3034659401530, 0.1257072729260),
        (0.3897940236415, 0.1775326357897),
        (0.7535353544980, 0.1817692032540),
    ],
    "study2a_low": [
        (-2.5532258937618, 0.1807247595913),
        (2.4287717192884, 0.2005582266503),
        (3.2548119429677, 0.2027616252934),
    ],
    "study2a_high": [
        (-2.7472709140485, 0.1883332381690),
        (1.0829563913885, 0.2252045867334),
        (1.4203999733994, 0.2182563025958),
    ],
    "study2b_none": [
        (-1.7552018734943, 0.1343286583594),
        (1.3553390209348, 0.1654572418912),
        (2.4593988902406, 0.1706299947099),
    ],
    "study2b_manufacturer": [
        (-2.3025849905233, 0.1637628887973),
        (0.9107504490280, 0.2017221339464),
        (1.2314469574105, 0.1942520568863),
    ],
    "study2b_retailer": [
        (-2.5910481104202, 0.1832806334709),
        (1.2346067124500, 0.2199699968590),
        (1.9078183665176, 0.2085497473269),
    ],
    "study3": [
        (-1.8458266904974, 0.1464324773382),
        (1.2901870509416, 0.1799193640276),
        (2.6956059417348, 0.1839988656524),
        (0.7782727988523, 0.1837697889099),
    ],
    "study4_up_10pct": [
        (-1.7447792603039, 0.1304775779184),
        (1.3393141521957, 0.1631040842375),
        (2.2393239984657, 0.1643881285428),
    ],
    "study4_up_15pct": [
        (-1.6588985426025, 0.1294815515411),
        (1.0668474789140, 0.1634681205885),
        (2.0541071505435, 0.1590721190036),
    ],
    "study4_up_5pct": [
        (1.0227033254799, 0.1092084442489),
        (-0.5155206929924, 0.1470942720801),
        (0.1685677936687, 0.1567962222505),
    ],
}


def glm_logit(y: np.ndarray, xs: np.ndarray) -> list[tuple[float, float]]:
    """R's glm(family = binomial) as glm.fit computes it: estimates and summary() SEs.

    Same start (mu = (y + 0.5) / 2), same IRLS step, same stopping rule (relative change in
    deviance under 1e-8) and the SEs from the last iteration's working weights, which is
    what summary.glm reports. Mimicking the procedure, not just the MLE, matters: where a
    cell's share is small glm stops a hair from the optimum and its SEs differ from the
    MLE's in the fifth decimal, so an exact-MLE answer key would need a loose tolerance.
    """
    xs = np.column_stack([np.ones(len(y)), xs])
    mu = (y + 0.5) / 2
    eta = np.log(mu / (1 - mu))

    def deviance(m: np.ndarray) -> float:
        with np.errstate(divide="ignore", invalid="ignore"):
            t = np.where(y == 1, -np.log(m), -np.log(1 - m))
        return float(2 * t.sum())

    dev_old = deviance(mu)
    for _ in range(25):  # glm.control(maxit = 25)
        w = mu * (1 - mu)
        z = eta + (y - mu) / w
        xtwx = xs.T @ (xs * w[:, None])
        b = np.linalg.solve(xtwx, xs.T @ (w * z))
        eta = xs @ b
        mu = 1 / (1 + np.exp(-eta))
        dev = deviance(mu)
        if abs(dev - dev_old) / (abs(dev) + 0.1) < 1e-8:
            break
        dev_old = dev
    se = np.sqrt(np.diag(np.linalg.inv(xtwx)))
    return [(float(b[i]), float(se[i])) for i in range(len(b))]


def saturated_logit(y: pd.Series, arm: pd.Series, levels: list[str]) -> list[tuple[float, float]]:
    """A logit of y on one dummy per arm in levels[1:], levels[0] the baseline, as R fits it."""
    assert set(arm) <= set(levels)
    xs = np.column_stack([(arm == lev).to_numpy(dtype=float) for lev in levels[1:]])
    return glm_logit(y.to_numpy(dtype=float), xs)


def _same(got: list[tuple[float, float]], want: list[tuple[float, float]]) -> bool:
    """Estimates and SEs to 1e-9 (R printed 13 significant digits)."""
    return all(
        abs(g[0] - w[0]) < 1e-9 and abs(g[1] - w[1]) < 1e-9 for g, w in zip(got, want, strict=True)
    )


ACTIONS = ["price_increase", "size_decrease", "quality_decrease"]


def _task(name: str, task: int) -> pd.DataFrame:
    df = built(name)
    df = df[df["task_num"] == task].copy()
    assert df["participant_id"].is_unique
    return df


def _unfair(df: pd.DataFrame) -> pd.Series:
    return (df["response_num"] == 2).astype(int)


def test_built_rows_reproduce_r_fairness_logits_study1() -> None:
    df = _task("study1", 0)
    assert len(df) == 1502
    assert _same(saturated_logit(_unfair(df), df["action"], ACTIONS), R_LOGIT["study1"])
    for product in ("chocolate", "streaming_platform"):
        sub = df[df["product"] == product]
        got = saturated_logit(_unfair(sub), sub["action"], ACTIONS)
        assert _same(got, R_LOGIT[f"study1_{product}"]), product


@pytest.mark.parametrize(
    "name,factor,levels",
    [
        ("study2a", "transparency", ["low", "high"]),
        ("study2b", "communication", ["none", "manufacturer", "retailer"]),
        ("study4", "costs", ["up_10pct", "up_15pct", "up_5pct"]),
    ],
)
def test_built_rows_reproduce_r_fairness_logits_by_subset(
    name: str, factor: str, levels: list[str]
) -> None:
    df = _task(name, 0)
    for lev in levels:
        sub = df[df[factor] == lev]
        got = saturated_logit(_unfair(sub), sub["action"], ACTIONS)
        assert _same(got, R_LOGIT[f"{name}_{lev}"]), lev


def test_built_rows_reproduce_r_fairness_logit_study3() -> None:
    df = _task("study3", 0)
    levels = [
        "price_increase",
        "size_decrease",
        "paper_quality_decrease",
        "packaging_quality_decrease",
    ]
    assert _same(saturated_logit(_unfair(df), df["action"], levels), R_LOGIT["study3"])


def _welch(a: pd.Series, b: pd.Series) -> tuple[float, float]:
    va, vb = a.var() / len(a), b.var() / len(b)
    t = (a.mean() - b.mean()) / math.sqrt(va + vb)
    df = (va + vb) ** 2 / (va**2 / (len(a) - 1) + vb**2 / (len(b) - 1))
    return t, df


def _one_sample(x: pd.Series, mu: float = 5) -> float:
    return (x.mean() - mu) / (x.std() / math.sqrt(len(x)))


def test_built_rows_reproduce_r_study4_followup_welch_tests() -> None:
    df = _task("study4_followup", 0)
    g = {a: df.loc[df["action"] == a, "response_num"].astype(float) for a in ACTIONS}
    want = {  # t.test(group_i, group_j): t and Welch df
        ("price_increase", "size_decrease"): (-0.3484628661178, 188.3079908305),
        ("price_increase", "quality_decrease"): (-3.82386590834, 200.9929613318),
        ("size_decrease", "quality_decrease"): (-3.208812006378, 195.8812442691),
    }
    for (a, b), (t, dof) in want.items():
        got = _welch(g[a], g[b])
        assert abs(got[0] - t) < 1e-9 and abs(got[1] - dof) < 1e-7, (a, b)


@pytest.mark.parametrize(
    "name,t",
    [
        ("study2a_pilot", -9.375145805592),
        ("study2b_pilot", -13.73521459243),
        ("study5a_pilot", -14.75733584003),
    ],
)
def test_built_rows_reproduce_r_pilot_t_tests(name: str, t: float) -> None:
    df = _task(name, 0)
    assert len(df) == 50 and abs(_one_sample(df["response_num"].astype(float)) - t) < 1e-9


def test_built_rows_reproduce_r_study6() -> None:
    df = built("study6")
    assert len(df) == 4 * 208
    assert (df.groupby("participant_id")["task_num"].nunique() == 4).all()
    wide = df.pivot(index="participant_id", columns="task_num", values="response_num")
    for task, chisq in ((0, 28.68269230769), (2, 7.451923076923)):
        obs = wide[task].value_counts().reindex([1, 2, 3]).to_numpy()
        exp = len(wide) / 3
        assert abs(((obs - exp) ** 2 / exp).sum() - chisq) < 1e-9
    for task, t in ((1, -12.77140879157), (3, -9.964857975178)):
        assert abs(_one_sample(wide[task].astype(float)) - t) < 1e-9
    # glm(Option3 ~ quality rating): the rows of one person must stay paired
    for (choice, rating), want in (
        ((0, 1), [(-2.68851781755037, 0.41521726103697), (0.31086561877853, 0.09255658547613)]),
        ((2, 3), [(-3.7192913523522, 0.6157612803231), (0.6088846676890, 0.1327409530162)]),
    ):
        y = (wide[choice] == 3).astype(float).to_numpy()
        got = glm_logit(y, wide[rating].to_numpy(dtype=float)[:, None])
        assert _same(got, want), choice


def test_built_rows_reproduce_r_study7() -> None:
    df = built("study7")
    buy = df[df["task_num"] == 0]
    levels = ["nonrecoverable_quality", "price_increase", "size_decrease", "recoverable_quality"]
    yes = (buy["response_num"] == 2).astype(int)
    got = saturated_logit(yes, buy["action"], levels)
    want = [
        (-0.7741883905625, 0.1377498624465),
        (1.3657557783045, 0.1913843426209),
        (1.2261735143055, 0.1859016939556),
        (0.4095452769746, 0.1895243228775),
    ]
    assert _same(got, want)
    rating = df[df["task_num"] == 1]
    assert set(rating["action"]) == {"recoverable_quality", "nonrecoverable_quality"}
    for arm, t in (
        ("recoverable_quality", -22.25530349931),
        ("nonrecoverable_quality", -18.74640347175),
    ):
        x = rating.loc[rating["action"] == arm, "response_num"].astype(float)
        assert len(x) == 244 and abs(_one_sample(x) - t) < 1e-9
    wide = df.pivot(index="participant_id", columns="task_num", values="response_num").dropna()
    got = glm_logit((wide[0] == 2).to_numpy(dtype=float), wide[1].to_numpy(dtype=float)[:, None])
    want = [(-3.7908802002113, 0.4296702372485), (0.9356933760861, 0.1189717530523)]
    assert _same(got, want)


def test_swapping_a_factor_breaks_the_reproduction() -> None:
    df = _task("study3", 0)
    levels = [
        "price_increase",
        "size_decrease",
        "paper_quality_decrease",
        "packaging_quality_decrease",
    ]
    swapped = df["action"].replace(
        {"price_increase": "size_decrease", "size_decrease": "price_increase"}
    )
    assert not _same(saturated_logit(_unfair(df), swapped, levels), R_LOGIT["study3"])
    # a mislabelled second factor: study 4's 5% and 15% cost levels exchanged
    df = _task("study4", 0)
    costs = df["costs"].replace({"up_5pct": "up_15pct", "up_15pct": "up_5pct"})
    sub = df[costs == "up_15pct"]
    got = saturated_logit(_unfair(sub), sub["action"], ACTIONS)
    assert not _same(got, R_LOGIT["study4_up_15pct"])
