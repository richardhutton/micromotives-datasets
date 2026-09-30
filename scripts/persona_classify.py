#!/usr/bin/env python3
"""Ask Jev which column actually holds a persona attribute, per study.

This is the job BEFORE the crosswalk, and it is the one a pattern cannot do.
A name/label regex over the 73 fetched studies pulled in, as an "income
variable":

    'her family depends on her income'
    'her family does not depend on her income because she has other resources'

— a vignette variable describing a fictional character, matched on the word
"income". Feeding that into a band crosswalk would have silently corrupted the
persona of whatever study it came from.

So the pipeline is: a deliberately WIDE regex proposes candidates, Jev decides
which one is the respondent's own attribute, and arithmetic verifies the band
merges afterwards (see persona_crosswalk.py). Jev is asked a closed question
with a checkable answer, which is where it has measured well; it never decides
the mapping itself.

What goes on the wire: variable names, variable labels, and value labels — i.e.
the codebook. Never respondent rows. Keep that property deliberate.

    uv run python scripts/persona_classify.py --field income --validate
    uv run python scripts/persona_classify.py --field income --all
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import warnings
from dataclasses import dataclass
from dataclasses import field as dc_field
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from micromotives_datasets.sources import spss  # noqa: E402

try:
    from typesafe_sdk import Choice, Noul, TypeSafeClient
except ImportError:  # pragma: no cover
    sys.exit("uv add typesafe-sdk first")

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw"
OUT = REPO / "data" / "catalog" / "persona_candidates.json"

# Deliberately wide. Precision is Jev's job; this only has to avoid MISSING a
# variable, because a candidate never offered can never be chosen.
PATTERNS = {
    "income": r"incim|income|hhinc|faminc|earn|salary|wage",
    "education": r"educ|degree|school|qualif",
    "ethnicity": r"ethm|ethn|race|racethn|hisp",
    "employment": r"work|employ|labour|labor|job",
    "region": r"reg\d|region|state|msa|urban|metro",
}

# What we are actually looking for, in the words we would use to a person.
WANTED = {
    "income": "the respondent's own total household income",
    "education": "the respondent's own highest level of education completed",
    "ethnicity": "the respondent's own race or ethnicity",
    "employment": "the respondent's own current employment status",
    "region": "where the respondent themselves lives",
}

# Studies whose income variable we already know, from recipes that build and
# crosscheck. Used by --validate to measure Jev before trusting it.
KNOWN_INCOME = {
    "7jt2f": "PPINCIMP",
    "9263n": "PPINCIMP",
    "a5v96": "PPINCIMP",
    "c5r2f": "PPINCIMP",
    "cug34": "PPINCIMP",
    "evnyh": "PPINCIMP",
    "z358z": "PPINCIMP",
    "rpw4u": "PPINCIMP",
    "sd7cf": "PPINCIMP",
    "zrwjp": "PPINCIMP",
    "b87sm": "INCOME",
    "bf8p2": "INCOME",
    "dh3nj": "INCOME",
    "zaqkm": "INCOME",
}


@dataclass
class Candidate:
    var: str
    label: str
    n_levels: int
    values: list[str] = dc_field(default_factory=list)
    is_attribute: float = 0.0
    kind: str = ""

    def describe(self) -> str:
        vals = "; ".join(self.values[:6])
        more = f" (+{self.n_levels - 6} more)" if self.n_levels > 6 else ""
        return (
            f"- variable `{self.var}`\n"
            f"  label: {self.label or '(none)'}\n"
            f"  {self.n_levels} values: {vals}{more}"
        )


def candidates_for(ds: spss.Dataset, field: str) -> list[Candidate]:
    pat = re.compile(PATTERNS[field], re.I)
    out = []
    for col in ds.df.columns:
        label = (ds.column_labels.get(col) or "").strip()
        if not (pat.search(col) or pat.search(label)):
            continue
        labels = ds.value_labels.get(col, {})
        vals = [str(v) for _, v in sorted(labels.items())]
        out.append(
            Candidate(
                var=col, label=label, n_levels=len(vals) or int(ds.df[col].nunique()), values=vals
            )
        )
    return out


def classify(client: TypeSafeClient, field: str, title: str, cands: list[Candidate]) -> None:
    """Ask, per candidate, whether it is the respondent's own attribute."""
    for c in cands:
        state = f'Survey study: "{title}"\n\nOne variable from its data file:\n\n{c.describe()}\n'
        r = client.system_one(
            state=state,
            questions={
                "is_respondent_attribute": Noul(
                    instructions=(
                        f"This variable records {WANTED[field]} — as a fact about the "
                        "person answering the survey. It is NOT a derived/computed "
                        "helper, NOT a weight, NOT an attribute of a fictional person "
                        "described in a vignette or scenario shown to the respondent, "
                        "and NOT a question asking the respondent's opinion about "
                        "someone else."
                    )
                ),
                # `criteria` is the option set; `other` is deliberately present so
                # the model can decline rather than being forced into a wrong box —
                # the narrow-option-list mistake from the earlier Jev work.
                "kind": Choice(
                    criteria={
                        "respondent_attribute": (
                            "a fact about the person answering, from the panel profile "
                            "or a demographic question they answered about themselves"
                        ),
                        "vignette_or_scenario_attribute": (
                            "an attribute of a fictional person or situation described "
                            "in material shown TO the respondent"
                        ),
                        "derived_or_computed": (
                            "a helper column computed from other columns, e.g. a "
                            "recode, a bracket flag or a 'data only variable'"
                        ),
                        "opinion_or_attitude_item": (
                            "a question asking what the respondent thinks, rather than "
                            "recording what they are"
                        ),
                        "weight_or_admin": (
                            "a survey weight, case id, timestamp, mode or other "
                            "administrative field"
                        ),
                        "other": "none of the above fits",
                    },
                    instructions="What this variable actually is.",
                ),
            },
        )
        c.is_attribute = float(r.answers["is_respondent_attribute"].noul)
        c.kind = str(r.answers["kind"].choice)


def pick(cands: list[Candidate]) -> Candidate:
    """The one to use, given Jev's scores.

    A deposit often carries the SAME attribute at several granularities —
    `INCOME`, `INCOME4` and `INCOME9` are all the respondent's household
    income, and Jev rates all three highly because all three are correct. That
    is an ambiguity, not a disagreement, and resolving it is arithmetic rather
    than judgment: take the finest-grained version, because a coarser one can
    always be derived from it and never the reverse.

    So Jev decides WHICH KIND of variable each column is; this decides which of
    the survivors to keep. Keeping those two steps apart is what stops us
    asking a model a question that code can answer exactly.
    """
    live = [c for c in cands if c.is_attribute >= 0.5] or cands
    # Granularity only breaks a tie among candidates Jev rates EQUALLY. Ranking
    # on levels first picked `zrwjp`'s Q3c ("How much do you earn per year
    # before taxes", 0.55) over PPINCIMP, because Q3c has more levels — but Q3c
    # is PERSONAL EARNINGS, a different construct from HOUSEHOLD INCOME, which
    # is precisely why Jev scored it 0.55 and not 0.9. The confidence was
    # carrying real information and the tiebreak was throwing it away.
    best = max(c.is_attribute for c in live)
    contenders = [c for c in live if best - c.is_attribute <= 0.10]
    return max(contenders, key=lambda c: (c.n_levels, c.is_attribute))


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


def main() -> int:
    import csv

    ap = argparse.ArgumentParser()
    ap.add_argument("--field", default="income", choices=sorted(PATTERNS))
    ap.add_argument("--validate", action="store_true", help="score against known answers")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("studies", nargs="*")
    args = ap.parse_args()

    with open(REPO / "data" / "catalog" / "tess_uk_foundation_sources.csv") as fh:
        titles = {r["osf_code"]: r["title"] for r in csv.DictReader(fh)}

    if args.validate:
        targets = sorted(KNOWN_INCOME)
    elif args.all:
        targets = sorted(c for c in titles if (RAW / c).is_dir())
    else:
        targets = args.studies

    client = TypeSafeClient()
    results: dict[str, list[Candidate]] = {}
    for code in targets:
        path = data_file_for(code)
        if path is None:
            print(f"SKIP  {code}: not fetched")
            continue
        try:
            ds = spss.read(path)
            cands = candidates_for(ds, args.field)
            if not cands:
                print(f"NONE  {code}: no candidate columns")
                continue
            classify(client, args.field, titles.get(code, code), cands)
            results[code] = cands
            best = pick(cands)
            print(
                f"{code}  {len(cands)} candidates -> {best.var} "
                f"({best.is_attribute:.2f}, {best.kind})"
            )
        except Exception as exc:
            print(f"ERR   {code}: {type(exc).__name__}: {str(exc)[:90]}")

    OUT.write_text(json.dumps({c: [vars(x) for x in v] for c, v in results.items()}, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")

    if args.validate and args.field == "income":
        print("\nVALIDATION against the 14 studies whose income variable we know")
        print(f"  {'study':7} {'known':12} {'jev picked':12} {'conf':>5}  ok")
        hits = 0
        for code, cands in results.items():
            known = KNOWN_INCOME[code]
            best = pick(cands)
            ok = best.var.upper() == known.upper()
            hits += ok
            print(
                f"  {code:7} {known:12} {best.var:12} {best.is_attribute:5.2f}  "
                f"{'Y' if ok else 'N'}"
            )
        print(f"\n  top-1 accuracy {hits}/{len(results)}")
        # The dangerous error is calling a vignette variable a respondent one.
        fps = [
            (c, x)
            for c, v in results.items()
            for x in v
            if x.is_attribute >= 0.5 and x.var.upper() != KNOWN_INCOME[c].upper()
        ]
        print(f"  non-target candidates scored >= 0.50: {len(fps)}")
        for c, x in fps[:12]:
            print(f"     {c} {x.var} {x.is_attribute:.2f} [{x.kind}] {x.label[:46]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
