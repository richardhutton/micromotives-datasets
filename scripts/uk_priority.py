#!/usr/bin/env python3
"""Rank the unbuilt TESS studies by how much they are worth to SocSci-UK.

The existing `uk_content_screen.py` answers a different and narrower question:
CAN this study transfer (does answering it need US knowledge). This asks whether
it is WORTH transferring — does its outcome bear on something UK social research
and policy actually argues about.

Those come apart. A study can transfer perfectly and be of no interest (response
scale direction, vignette-order effects), or need its scenario re-set and still
be among the most valuable things in the catalog (attitudes to welfare
conditionality, who gets believed in a hospital).

Three things asked, kept separate because they trade off against each other:

  uk_relevance   does the outcome bear on a live UK question
  domain         so the final 40 can be spread rather than all one topic
  evergreen      an attitude that is still the same question in 2026, as against
                 one tied to a 2011 news cycle

Scores rank and flag; they do not decide. The output is a shortlist for me to
read, and `--balance` spreads the picks across domains rather than taking the
top N, because 40 studies all about healthcare is a worse dataset than 40 across
eight domains even if each one scores higher.

On the wire: titles and question wordings. Never respondent rows.

    uv run python scripts/uk_priority.py --all
    uv run python scripts/uk_priority.py --all --balance 26
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import warnings
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from micromotives_datasets.sources import spss  # noqa: E402

try:
    from typesafe_sdk import Choice, Score, TypeSafeClient
except ImportError:  # pragma: no cover
    sys.exit("uv add typesafe-sdk first")

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw"
CATALOG = REPO / "data" / "catalog" / "tess_uk_foundation_sources.csv"
OUT = REPO / "data" / "catalog" / "uk_priority.json"
SCREEN = REPO / "data" / "catalog" / "uk_transfer_screen.json"
SHORTLIST = REPO / "data" / "catalog" / "uk_shortlist.json"

BUILT = {
    "5hqan",
    "7jt2f",
    "8ctbk",
    "9263n",
    "a2nbf",
    "a42yg",
    "a5v96",
    "b87sm",
    "bf8p2",
    "c5r2f",
    "cug34",
    "dh3nj",
    "evnyh",
    "rpw4u",
    "sd7cf",
    "z358z",
    "zaqkm",
    "yv2ta",
    "zrwjp",
}

DOMAINS = {
    "health_and_care": "illness, medicine, doctors, mental health, disability, social care",
    "work_and_money": "jobs, pay, unemployment, pensions, debt, household finances",
    "family_and_relationships": "couples, parenting, childcare, housework, caring",
    "welfare_and_inequality": "benefits, poverty, redistribution, class, deservingness",
    "discrimination_and_identity": "race, gender, sexuality, religion, immigration, stigma",
    "crime_and_justice": "policing, courts, punishment, risk, safety",
    "environment_and_energy": "climate, pollution, energy use, sustainable consumption",
    "politics_and_institutions": "voting, parties, government, trust in institutions, media",
    "consumer_and_technology": "purchases, firms, apps, data and privacy, algorithms",
    "survey_methodology": "the study is ABOUT how surveys work — scales, wording, order effects",
}

SKIP_PREFIX = ("pp", "tm_", "ds_", "ts_", "dov_", "xtess")
SKIP_SUBSTR = ("_time", "weight", "caseid", "duration", "starttime", "endtime", "respdate")


# Relevance and evergreen are POSITIONS ON A SPECTRUM, so they are asked as
# `Score`, not `Noul`. The first version of this script asked both as `Noul`s
# and then ranked 59 studies by `relevance + 0.15 * evergreen` — arithmetic on
# two probabilities-of-yes. The primitive docs are explicit that this is not
# what a Noul measures: "A Noul value of 0.5 means the model gives yes and no
# equal probability. It does not mean the candidate has a medium skill level."
# The numbers looked perfectly usable, which is exactly the problem.
#
# A `Score` takes an ORDERED list of levels and returns the probability-weighted
# average of them, so the value is a position by construction and averaging two
# of them means something. Writing the levels out also forces the judgement to
# be stated rather than implied — the old `Noul` instructions described what a
# high score meant and left every other value to inference.
RELEVANCE_LEVELS = [
    "Of no interest to UK social research. The outcome bears on nothing a UK "
    "researcher, civil servant or journalist argues about.",
    "Marginal. Academic interest only, or a question settled long ago.",
    "Real but niche. A recognisable question within one specialism.",
    "Clearly relevant. A UK researcher in the field would call this a live "
    "question, though not a prominent one.",
    "Prominent. The outcome bears on something argued about in UK policy, the "
    "press or public debate right now.",
]

EVERGREEN_LEVELS = [
    "Tied to a specific past event, named politician, or a policy or technology "
    "since superseded. The question no longer exists in this form.",
    "Dated. Still intelligible, but the context has moved substantially.",
    "Partly dated. The underlying question survives; its framing has aged.",
    "Largely stable. Asked today it would mean much the same thing.",
    "Timeless. A question about human behaviour that does not depend on when it was asked.",
]


@dataclass
class Priority:
    study_id: str
    title: str
    relevance: float = 0.0
    evergreen: float = 0.0
    relevance_conf: float = 0.0
    evergreen_conf: float = 0.0
    domain: str = ""
    domain_conf: float = 0.0
    transfer: str = ""
    socsci_rows: int = 0

    @property
    def score(self) -> float:
        """Relevance dominates; evergreen is a modifier, not a veto.

        A dated-but-central question still beats a timeless irrelevant one, so
        evergreen is weighted lightly. `full` transfer earns a small bonus
        because re-anchoring a scenario is real work even when it is possible.

        Both terms are `Score` values on 0-4 rubrics, normalised to 0-1 here so
        the transfer bonus keeps the magnitude it was tuned at.
        """
        bonus = {"full": 0.10, "mechanism-only": 0.0, "us-specific": -0.30}.get(self.transfer, 0.0)
        return self.relevance / 4 + 0.15 * (self.evergreen / 4) + bonus

    @property
    def shaky(self) -> bool:
        """Any judgement the model itself was unsure of.

        `Score` and `Choice` both return a confidence whose documented purpose
        is deciding "when to act automatically and when to escalate to a
        person". We were reading `.choice` alone and throwing it away.
        """
        return min(self.relevance_conf, self.evergreen_conf, self.domain_conf) < 0.6


def questions_in(path: Path, limit: int = 30) -> str:
    ds = spss.read(path)
    out = []
    for name in ds.df.columns:
        low = name.lower()
        if low.startswith(SKIP_PREFIX) or any(s in low for s in SKIP_SUBSTR):
            continue
        label = (ds.column_labels.get(name) or "").strip()
        if len(label) > 20:
            out.append(f"- {label[:200]}")
        if len(out) >= limit:
            break
    return "\n".join(out)


def score(client: TypeSafeClient, p: Priority, path: Path) -> None:
    state = (
        f'Survey experiment: "{p.title}"\n\n'
        f"The questions asked of respondents:\n\n{questions_in(path)}\n"
    )
    r = client.system_one(
        state=state,
        questions={
            "uk_relevance": Score(
                criteria=RELEVANCE_LEVELS,
                instructions=(
                    "How much does the OUTCOME this study measures bear on a question "
                    "UK social research, public debate or policy argues about? Judge "
                    "the substance of what is being measured, not whether the scenario "
                    "happens to be set in America."
                ),
            ),
            "evergreen": Score(
                criteria=EVERGREEN_LEVELS,
                instructions=(
                    "Is the attitude or behaviour measured here still the same question "
                    "today as when it was asked?"
                ),
            ),
            "domain": Choice(
                criteria={**DOMAINS, "other": "none of these fits"},
                instructions="The single domain this study's OUTCOME sits in.",
            ),
        },
    )
    rel, ever, dom = (r.answers[k] for k in ("uk_relevance", "evergreen", "domain"))
    p.relevance, p.relevance_conf = float(rel.score), float(rel.confidence)
    p.evergreen, p.evergreen_conf = float(ever.score), float(ever.confidence)
    p.domain, p.domain_conf = str(dom.choice), float(dom.confidence)


def data_file_for(code: str) -> Path | None:
    folder = RAW / code
    if not folder.is_dir():
        return None
    files = [
        q
        for q in folder.rglob("*")
        if q.is_file()
        and q.suffix.lower() in {".sav", ".dta", ".por"}
        and not q.name.startswith("._")
    ]
    return max(files, key=lambda q: q.stat().st_size) if files else None


def buildable(code: str) -> bool:
    """Has both an instrument and a data file — otherwise it cannot be built."""
    folder = RAW / code
    if not folder.is_dir():
        return False
    has_q = any(
        q.suffix.lower() in {".txt", ".docx"} and "Response Rate" not in q.name
        for q in folder.rglob("*")
    )
    return has_q and data_file_for(code) is not None


def existing_transfer_verdicts() -> dict[str, str]:
    """Each study's transfer verdict, hand-read beating screened.

    Two sources, deliberately ranked. The catalog's `uk_content` column holds
    verdicts reached by reading the fielded questionnaire; `uk_transfer_screen.json`
    holds `uk_content_screen.py`'s guesses from variable labels. The screen
    agrees with hand reading on 12 of 16, and TWO of its four errors are in the
    dangerous direction — it called `b87sm` and `rpw4u` fully transferable where
    reading said mechanism-only. So the screen orders the queue; it never
    overrules an eye.
    """
    out: dict[str, str] = {}
    if SCREEN.exists():
        for code, rec in json.loads(SCREEN.read_text()).items():
            out[code] = rec["verdict"]
    with open(CATALOG) as fh:
        for row in csv.DictReader(fh):
            if row.get("uk_content"):
                out[row["osf_code"]] = row["uk_content"]
    return out


# `other` is what Jev says when none of the ten domains fit. It is a residual,
# not a domain, so giving it a turn in the round-robin spends slots on the
# studies that matched nothing — `vhycz` (collective memory, 0.58) was taking a
# place from better-scoring studies in real domains purely because `other` came
# up in rotation.
NOT_A_DOMAIN = frozenset({"other", ""})


def balance(items: list[Priority], want: int) -> list[Priority]:
    """Spread the picks across domains instead of taking the top N.

    Forty studies all about healthcare is a worse dataset than forty across
    eight domains, even if each healthcare study scores higher — the point of
    the corpus is coverage of human behaviour, not depth in one topic. So this
    takes the best remaining study from each domain in turn.
    """
    by_domain: dict[str, list[Priority]] = defaultdict(list)
    for p in sorted(items, key=lambda x: -x.score):
        if p.domain in NOT_A_DOMAIN:
            continue
        by_domain[p.domain].append(p)
    picked: list[Priority] = []
    while len(picked) < want and any(by_domain.values()):
        for dom in sorted(
            by_domain, key=lambda d: -max((x.score for x in by_domain[d]), default=0)
        ):
            if by_domain[dom] and len(picked) < want:
                picked.append(by_domain[dom].pop(0))
    return picked


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="score every buildable unbuilt study")
    ap.add_argument("--balance", type=int, default=0, help="also print a domain-spread shortlist")
    ap.add_argument(
        "--reuse",
        action="store_true",
        help="re-rank from saved scores without calling Jev (picks up new transfer verdicts)",
    )
    ap.add_argument("studies", nargs="*")
    args = ap.parse_args()

    with open(CATALOG) as fh:
        catalog = {r["osf_code"]: r for r in csv.DictReader(fh)}
    verdicts = existing_transfer_verdicts()

    if args.reuse:
        # The relevance and domain judgements do not change when a transfer
        # verdict arrives, so re-ranking must not re-pay for them.
        results = [Priority(**rec) for rec in json.loads(OUT.read_text())]
        for p in results:
            p.transfer = verdicts.get(p.study_id, p.transfer)
    else:
        targets = (
            [c for c in catalog if c not in BUILT and buildable(c)] if args.all else args.studies
        )
        client = TypeSafeClient()
        results = []
        for code in sorted(targets):
            path = data_file_for(code)
            if path is None:
                continue
            p = Priority(
                study_id=code,
                title=catalog[code]["title"],
                transfer=verdicts.get(code, ""),
                socsci_rows=int(catalog[code].get("socsci210_rows") or 0),
            )
            try:
                score(client, p, path)
                results.append(p)
                print(
                    f"{code}  rel={p.relevance:.2f} ever={p.evergreen:.2f} "
                    f"{p.domain:28} {p.title[:40]}"
                )
            except Exception as exc:
                print(f"ERR   {code}: {type(exc).__name__}: {str(exc)[:80]}")
        OUT.write_text(json.dumps([vars(r) for r in results], indent=2))

    print(f"\n{'study':7} {'score':>5} {'rel':>5} {'ever':>5} {'domain':28} title")
    for p in sorted(results, key=lambda x: -x.score):
        print(
            f"{p.study_id:7} {p.score:5.2f} {p.relevance:5.2f} {p.evergreen:5.2f} "
            f"{p.domain:28} {p.title[:40]}"
        )

    counts: dict[str, int] = defaultdict(int)
    for p in results:
        counts[p.domain] += 1
    print("\ndomain spread of the candidate pool:")
    for dom, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"   {dom:30} {n}")

    if args.balance:
        picked = balance(results, args.balance)
        print(f"\nSHORTLIST — {args.balance} studies, spread across domains")
        print(f"{'study':7} {'score':>5} {'transfer':15} {'domain':28} title")
        for p in picked:
            print(
                f"{p.study_id:7} {p.score:5.2f} {p.transfer or '-':15} {p.domain:28} {p.title[:40]}"
            )
        rows = sum(p.socsci_rows for p in picked)
        print(f"\n{len(picked)} studies, {rows:,} rows by SocSci210's count")
        # Saved so the build queue is a file both of us can read, rather than
        # something regenerated differently each time it is asked for.
        SHORTLIST.write_text(json.dumps([vars(p) for p in picked], indent=2))
        print(f"wrote {SHORTLIST.relative_to(REPO)}")
    if not args.reuse:
        print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
