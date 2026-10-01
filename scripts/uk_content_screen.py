#!/usr/bin/env python3
"""Screen studies for US-specific CONTENT, using their actual question wordings.

The existing `uk_applicable` judgement in the catalog was made from titles, which
cannot see inside a study. `sd7cf` — "Framing in Noisy Informational
Environments" — scored confidence 1.0 and no note; its outcome is *support for
the Patriot Act*, which a UK respondent cannot hold a view on.

This screens on the data file's variable labels, which carry the real question
wordings, so the thing that gives a study away is actually in front of the model.

Two questions, deliberately separate, because they cost different amounts:
  * stimulus_is_us_specific — the scenario mentions US institutions. Often
    survivable: swap the scenario, keep the design.
  * outcome_needs_us_knowledge — answering requires knowing US law/politics.
    Worse: a UK respondent has no view to predict.

Validate before trusting: `--validate` scores the screen against the studies we
have hand-classified by reading their questionnaires.

    uv run python scripts/uk_content_screen.py --validate
    uv run python scripts/uk_content_screen.py --all
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from micromotives_datasets.sources import spss

try:
    from typesafe_sdk import Noul, TypeSafeClient
except ImportError:  # pragma: no cover
    sys.exit("uv add typesafe-sdk first")

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw"
CATALOG = REPO / "data" / "catalog" / "tess_uk_foundation_sources.csv"

# Kept separate from the catalog's `uk_content` column ON PURPOSE. That column
# holds verdicts reached by reading the questionnaire; this file holds the
# screen's guesses. Writing the screen into the same column would overwrite
# read-with-my-own-eyes judgements with model output and leave no way to tell
# them apart — and the screen's whole justification is that it is a cheap
# pre-filter, not an authority.
OUT = REPO / "data" / "catalog" / "uk_transfer_screen.json"

SKIP_PREFIX = ("pp", "tm_", "ds_", "ts_")
SKIP_SUBSTR = ("_time", "weight", "caseid", "duration", "starttime", "endtime", "respdate")


@dataclass
class Screen:
    study_id: str
    title: str
    stimulus_us: float
    outcome_us: float

    @property
    def verdict(self) -> str:
        """Outcome-specificity is the expensive kind, so it dominates."""
        if self.outcome_us >= 0.5:
            return "us-specific"
        if self.stimulus_us >= 0.5:
            return "mechanism-only"
        return "full"

    @property
    def confidence(self) -> float:
        driver = self.outcome_us if self.outcome_us >= 0.5 else self.stimulus_us
        return driver if driver >= 0.5 else 1 - max(self.outcome_us, self.stimulus_us)


def data_file_for(study_id: str) -> Path | None:
    folder = RAW / study_id
    if not folder.is_dir():
        return None
    files = [
        p
        for p in folder.rglob("*")
        if p.is_file()
        and p.suffix.lower() in {".sav", ".dta", ".por"}
        and not p.name.startswith("._")
    ]
    return max(files, key=lambda p: p.stat().st_size) if files else None


def question_text(path: Path, limit: int = 45) -> str:
    """The study's real question wordings, from the variable labels."""
    ds = spss.read(path)
    out = []
    for name in ds.df.columns:
        low = name.lower()
        if low.startswith(SKIP_PREFIX) or any(s in low for s in SKIP_SUBSTR):
            continue
        label = (ds.column_labels.get(name) or "").strip()
        if len(label) > 15:  # a real question, not a code name
            out.append(f"- {label[:220]}")
        if len(out) >= limit:
            break
    return "\n".join(out)


def screen(client: TypeSafeClient, study_id: str, title: str, path: Path) -> Screen:
    state = (
        f'Survey experiment: "{title}"\n\n'
        f"The questions asked of respondents:\n\n{question_text(path)}"
    )
    r = client.system_one(
        state=state,
        questions={
            "stimulus_is_us_specific": Noul(
                instructions=(
                    "The scenarios or materials shown to respondents refer to institutions, "
                    "laws, political parties, public figures or cultural references that are "
                    "specific to the United States."
                )
            ),
            "outcome_needs_us_knowledge": Noul(
                instructions=(
                    "Answering the main outcome question requires knowledge of United States "
                    "law, politics or institutions that a respondent in another country would "
                    "not reliably have. Judge the OUTCOME question, not the topic in general — "
                    "a universal psychological question set in a US scene does not count."
                )
            ),
        },
    )
    return Screen(
        study_id=study_id,
        title=title,
        stimulus_us=float(r.answers["stimulus_is_us_specific"].noul),
        outcome_us=float(r.answers["outcome_needs_us_knowledge"].noul),
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", action="store_true", help="score against hand-classified studies")
    ap.add_argument("--all", action="store_true", help="screen every fetched study")
    ap.add_argument("studies", nargs="*")
    args = ap.parse_args()

    with open(CATALOG) as fh:
        rows = {r["osf_code"]: r for r in csv.DictReader(fh)}

    if args.validate:
        targets = [c for c, r in rows.items() if r.get("uk_content")]
    elif args.all:
        targets = [c for c in rows if (RAW / c).is_dir()]
    else:
        targets = args.studies

    client = TypeSafeClient()
    results: list[Screen] = []
    for code in targets:
        path = data_file_for(code)
        if path is None:
            print(f"SKIP  {code}: not fetched")
            continue
        try:
            results.append(screen(client, code, rows[code]["title"], path))
        except Exception as exc:
            print(f"ERR   {code}: {type(exc).__name__}: {str(exc)[:110]}")

    if results and not args.validate:
        # Merge rather than replace, so screening another ten studies next week
        # does not discard this week's. Keyed by study, newest run wins.
        saved = json.loads(OUT.read_text()) if OUT.exists() else {}
        for s in results:
            saved[s.study_id] = {
                **asdict(s),
                "verdict": s.verdict,
                "confidence": round(s.confidence, 3),
            }
        OUT.write_text(json.dumps(saved, indent=2, sort_keys=True))
        print(f"\nwrote {len(results)} verdicts to {OUT.relative_to(REPO)} ({len(saved)} total)")

    print(f"\n{'study':7} {'verdict':15} {'stim':>5} {'outc':>5}  title")
    for s in sorted(results, key=lambda s: -s.outcome_us):
        print(
            f"{s.study_id:7} {s.verdict:15} {s.stimulus_us:>5.2f} {s.outcome_us:>5.2f}  {s.title[:46]}"
        )

    if args.validate:
        print("\nVALIDATION against hand-classified studies")
        print(f"  {'study':7} {'ours':15} {'screen':15} agree")
        agree = 0
        for s in results:
            hand = rows[s.study_id]["uk_content"]
            # Our hand labels use full / mechanism-only; the screen can also say
            # us-specific, which is a stricter form of mechanism-only.
            same = hand == s.verdict or (hand == "mechanism-only" and s.verdict == "us-specific")
            agree += same
            print(f"  {s.study_id:7} {hand:15} {s.verdict:15} {'Y' if same else 'N'}")
        print(f"\n  agreement {agree}/{len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
