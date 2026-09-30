#!/usr/bin/env python3
"""Measure Jev on real pipeline decisions with known answers.

Unlike `jev_probe.py`, the inputs here are NOT curated summaries written after
the fact. Each state is built from RAW material — the actual variable list and
labels read out of the data file, or the verbatim questionnaire block — which is
what an agent would really be handed.

Ground truth comes from two real sources, neither invented for this test:
  * POSITIVE cases: our hand-built recipes, each verified against the
    questionnaire and (where comparable) against SocSci210's numbers.
  * NEGATIVE cases: SocSci210's own published stimulus text for studies where we
    established it is wrong (see docs/LEDGER.md).

Reports accuracy AND calibration. Calibration is the property that matters: if
we auto-accept everything above a confidence threshold, an over-confident model
silently ships wrong answers.

    uv run python scripts/jev_calibration.py [--limit N]
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from micromotives_datasets import recipe as recipe_mod
from micromotives_datasets.sources import spss

try:
    import typesafe_sdk as ts
    from typesafe_sdk import Choice, Noul, TypeSafeClient
except ImportError:  # pragma: no cover
    sys.exit("uv add typesafe-sdk first")

REPO = Path(__file__).resolve().parents[1]

# (recipe file, data subdir) for every study we have built and verified by hand.
STUDIES = [
    ("7jt2f.yaml", "7jt2f"),
    ("rpw4u_RO1.yaml", "rpw4u"),
    ("zrwjp.yaml", "zrwjp"),
    ("c5r2f.yaml", "c5r2f"),
]

# SocSci210's real, published stimulus text for arms we proved it describes
# wrongly. Quoted verbatim; see docs/LEDGER.md for the evidence.
SOCSCI210_WRONG = [
    (
        "7jt2f",
        0,
        'Jordan is identified only by the label "Atheist."',
        "arms 1-4 DID include a self-introduction; this says they did not",
    ),
    (
        "c5r2f",
        0,
        "You must get a new driver's license. In this state every person is considered "
        "not to be an organ donor unless they choose to be.",
        "arm 1 read the MEDICAL TESTING vignette, not organ donation",
    ),
]


@dataclass
class Case:
    case_id: str
    kind: str
    state: str
    questions: dict[str, object]
    expected: dict[str, object]
    note: str = ""


@dataclass
class Result:
    case_id: str
    kind: str
    key: str
    expected: object
    got: object
    confidence: float
    correct: bool
    note: str = ""


@dataclass
class Scoreboard:
    results: list[Result] = field(default_factory=list)

    def add(self, r: Result) -> None:
        self.results.append(r)

    def render(self) -> str:
        if not self.results:
            return "no results"
        lines = ["", "=" * 92, "RESULTS", "=" * 92]
        lines.append(f"{'case':34} {'decision':20} {'expected':12} {'got':12} {'conf':>5}  ok")
        for r in self.results:
            lines.append(
                f"{r.case_id[:33]:34} {r.key[:19]:20} {str(r.expected)[:11]:12} "
                f"{str(r.got)[:11]:12} {r.confidence:>5.2f}  {'Y' if r.correct else 'N'}"
            )
            if not r.correct and r.note:
                lines.append(f"{'':34} why: {r.note[:70]}")

        n = len(self.results)
        ok = sum(r.correct for r in self.results)
        lines += ["", "-" * 92, f"accuracy  {ok}/{n} = {ok / n:.0%}", "-" * 92]

        # Calibration: does stated confidence predict being right?
        lines.append("")
        lines.append("CALIBRATION — if confidence is honest, hit-rate should track the band")
        bands = [(0.0, 0.5), (0.5, 0.7), (0.7, 0.9), (0.9, 1.01)]
        lines.append(f"  {'confidence band':18} {'n':>3} {'hit rate':>9}   verdict")
        for lo, hi in bands:
            group = [r for r in self.results if lo <= r.confidence < hi]
            if not group:
                continue
            hit = sum(g.correct for g in group) / len(group)
            mid = (lo + min(hi, 1.0)) / 2
            verdict = (
                "ok"
                if abs(hit - mid) < 0.25
                else ("OVER-confident" if hit < mid else "under-confident")
            )
            lines.append(
                f"  {f'{lo:.1f}-{min(hi, 1.0):.1f}':18} {len(group):>3} {hit:>8.0%}   {verdict}"
            )

        wrong_confident = [r for r in self.results if not r.correct and r.confidence >= 0.8]
        lines.append("")
        if wrong_confident:
            lines.append(
                f"  !! {len(wrong_confident)} CONFIDENT WRONG answer(s) — these are the dangerous ones:"
            )
            for r in wrong_confident:
                lines.append(
                    f"     {r.case_id} / {r.key}: said {r.got!r} (conf {r.confidence:.2f}), truth {r.expected!r}"
                )
        else:
            lines.append("  no confident-wrong answers (nothing >=0.80 confidence was wrong)")
        return "\n".join(lines)


def _variable_listing(ds: spss.Dataset, limit: int = 60) -> str:
    """The raw variable list, as an agent would actually receive it."""
    out = []
    for name in list(ds.df.columns)[:limit]:
        label = (ds.column_labels.get(name) or "").strip()
        out.append(f"- {name}: {label[:120]}" if label else f"- {name}")
    return "\n".join(out)


def build_cases() -> list[Case]:
    cases: list[Case] = []

    for recipe_file, data_dir in STUDIES:
        rec = recipe_mod.load(REPO / "recipes" / recipe_file)
        data_path = REPO / "data" / "raw" / data_dir / rec.data_file
        if not data_path.exists():
            print(f"  (skipping {rec.study_id}: {data_path.name} not present)")
            continue
        ds = spss.read(data_path)
        listing = _variable_listing(ds)
        label = rec.experiment or rec.study_id

        # --- A: identify the randomised assignment variable ----------------
        # Ground truth: the recipe's condition.source_var, verified against the
        # questionnaire and (where comparable) SocSci210's cell counts.
        candidates = [c for c in ds.df.columns if c != rec.condition.source_var][:9]
        options = {rec.condition.source_var: "", **dict.fromkeys(candidates, "")}
        cases.append(
            Case(
                case_id=f"{label}/assignment-var",
                kind="A: which variable is the randomised assignment?",
                state=(f"A survey experiment data file. Its variables and labels:\n\n{listing}"),
                questions={
                    "assignment_var": Choice(
                        instructions=(
                            "Which variable records which randomly assigned experimental "
                            "condition each respondent was placed in?"
                        ),
                        criteria={k: (ds.column_labels.get(k) or "")[:90] for k in options},
                    )
                },
                expected={"assignment_var": rec.condition.source_var},
            )
        )

        # --- B: dependent measure vs covariate -----------------------------
        # Ground truth: variables the recipe uses as outcomes are DVs; the
        # persona variables are not.
        outcome_vars = [o.var for o in rec.outcomes if o.var] or [
            a.outcome_var for a in rec.condition.arms if a.outcome_var
        ]
        covariates = [v for v in rec.persona_map.values() if v in ds.df.columns][:2]
        for var, truth in [(v, True) for v in outcome_vars[:2]] + [(v, False) for v in covariates]:
            if var not in ds.df.columns:
                continue
            cases.append(
                Case(
                    case_id=f"{label}/{var}-is-dv",
                    kind="B: is this variable a dependent measure?",
                    state=(
                        f"A survey experiment data file. Its variables and labels:\n\n{listing}"
                    ),
                    questions={
                        "is_dependent_measure": Noul(
                            instructions=(
                                f"The variable {var} records a response the experiment was "
                                "designed to measure, rather than a background characteristic "
                                "of the respondent or an administrative field."
                            )
                        )
                    },
                    expected={"is_dependent_measure": truth},
                )
            )

    # --- C: does a description match the questionnaire block? --------------
    # Positive cases: our verified arm text. Negative cases: SocSci210's real,
    # published text for arms we proved it describes wrongly.
    q_path = REPO / "data" / "raw" / "7jt2f" / "questionnaire.txt"
    if q_path.exists():
        import re

        text = q_path.read_text(encoding="utf-8", errors="replace")
        parts = re.split(r"SHOW IF XTESS062 = (\d)\s*\(CONDITION ([A-H])\)\.", text)
        blocks = {}
        for i in range(1, len(parts) - 2, 3):
            blocks[int(parts[i])] = " ".join(parts[i + 2].split("SHOW IF")[0].split())[:1400]

        rec = recipe_mod.load(REPO / "recipes" / "7jt2f.yaml")
        ours = {a.raw: " ".join(a.text.split()) for a in rec.condition.arms}

        for raw, truth, desc, why in [
            (1, True, ours[1], "our recipe text, verified against this block"),
            (5, True, ours[5], "our recipe text, verified against this block"),
            (1, False, SOCSCI210_WRONG[0][2], SOCSCI210_WRONG[0][3]),
        ]:
            if raw not in blocks:
                continue
            cases.append(
                Case(
                    case_id=f"7jt2f/arm{raw}-desc-{'ok' if truth else 'bad'}",
                    kind="C: does the description match the questionnaire block?",
                    state=(
                        f"Questionnaire block actually shown to this group:\n\n{blocks[raw]}\n\n"
                        f"Proposed description of what this group saw:\n\n{desc}"
                    ),
                    questions={
                        "description_matches": Noul(
                            instructions=(
                                "The proposed description accurately describes what this group "
                                "was shown, without omitting or contradicting anything material."
                            )
                        )
                    },
                    expected={"description_matches": truth},
                    note=why,
                )
            )
    return cases


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="run only the first N cases")
    args = ap.parse_args()

    if not os.environ.get(ts.constants.API_KEY_ENV):
        return int(print(f"{ts.constants.API_KEY_ENV} not set") or 1)

    cases = build_cases()
    if args.limit:
        cases = cases[: args.limit]
    print(f"{len(cases)} cases with known answers\n")

    client = TypeSafeClient()
    board = Scoreboard()
    for case in cases:
        try:
            resp = client.system_one(state=case.state, questions=case.questions)  # type: ignore[arg-type]
        except Exception as exc:
            print(f"  {case.case_id}: call failed — {type(exc).__name__}: {str(exc)[:120]}")
            continue
        for key, expected in case.expected.items():
            ans = resp.answers[key]
            if hasattr(ans, "choice"):
                got, conf = ans.choice, float(getattr(ans, "confidence", 0.0))
                correct = got == expected
            else:
                raw = float(ans.noul)
                got, conf = raw >= 0.5, (raw if raw >= 0.5 else 1 - raw)
                correct = got == expected
            board.add(Result(case.case_id, case.kind, key, expected, got, conf, correct, case.note))

    print(board.render())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
