#!/usr/bin/env python3
"""Ask Jev what each category label MEANS, so the harmoniser can merge them.

`persona/categories.py` does the bookkeeping: given that someone has said which
labels denote the same concept, it works out the canonical set and proves every
source category lands in exactly one. This supplies that "someone".

It is the semantic half, and it is not a string-matching job. Across the corpus
the same concept is spelled `2+ Races, Non-Hispanic`, `2+, non-Hispanic`,
`Two or more races`, `Multiracial`; the residual is `Other, Non-Hispanic`,
`Something else`, `Other or mixed`. And the difference that actually matters is
not spelling at all — one panel separates Asian while another folds it into
Other, which is a fact about what the category CONTAINS.

Two questions per label, deliberately separate because they fail differently:

  concept    which of a generous vocabulary this label denotes. `none_of_these`
             is always offered so Jev can decline rather than be squeezed into
             the nearest box — narrowing the options is the caller making the
             decision it claims to be asking about, which is how this project
             got burned before.
  is_residual whether the label is the catch-all. This one carries real weight:
             `categories.canonical` can only fold an unmatched concept into a
             residual, and raises when a scheme has none. Getting it wrong
             either invents a merge or blocks a legitimate one.

Everything Jev declines, and everything it is unsure about, is printed for
review rather than quietly resolved.

On the wire: value labels and variable labels only. Never respondent rows.

    uv run python scripts/persona_harmonise.py --field ethnicity
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from micromotives_datasets.persona.categories import (  # noqa: E402
    Category,
    CatScheme,
    canonical,
    crosswalk,
)
from micromotives_datasets.sources import spss  # noqa: E402

try:
    from typesafe_sdk import Choice, Noul, TypeSafeClient
except ImportError:  # pragma: no cover
    sys.exit("uv add typesafe-sdk first")

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw"
OUT = REPO / "data" / "catalog"

# Generous on purpose: a concept missing from the vocabulary forces a wrong
# answer, while a concept nobody uses costs nothing. `none_of_these` is the
# escape and every use of it gets surfaced.
VOCAB = {
    "ethnicity": {
        "white": "White, Caucasian or European",
        "black": "Black, African-American or African",
        "hispanic": "Hispanic, Latino or Spanish origin",
        "asian": "Asian or Asian-American",
        "native_american": "American Indian, Native American or Alaska Native",
        "pacific_islander": "Native Hawaiian or other Pacific Islander",
        "middle_eastern": "Middle Eastern or North African",
        "two_or_more_races": "two or more races, mixed or multiracial",
        "other_residual": "a catch-all for anything not listed",
        "declined": "refused, prefer not to say, or missing",
    },
    "employment": {
        "employed_full_time": "working full time",
        "employed_part_time": "working part time",
        "self_employed": "self-employed",
        "employed_unspecified": "working, without full/part time distinguished",
        "unemployed_looking": "not working and looking for work",
        "unemployed_not_looking": "not working and not looking for work",
        "retired": "retired",
        "student": "in school or a student",
        "homemaker": "keeping house, homemaker or caring for family",
        "disabled": "disabled or unable to work",
        "other_residual": "a catch-all for anything not listed",
        "declined": "refused, prefer not to say, or missing",
    },
    "education": {
        "less_than_high_school": "did not complete secondary school",
        "high_school": "completed secondary school or equivalent",
        "some_college": "some post-secondary study, no degree",
        "associate": "a two-year or associate degree",
        "bachelors": "a bachelor's degree",
        "postgraduate": "a master's, doctorate or professional degree",
        "bachelors_or_higher": "a bachelor's degree or above, not distinguished further",
        "other_residual": "a catch-all for anything not listed",
        "declined": "refused, prefer not to say, or missing",
    },
}


def pick(cands: list[dict]) -> dict:
    live = [c for c in cands if c["is_attribute"] >= 0.5] or cands
    best = max(c["is_attribute"] for c in live)
    near = [c for c in live if best - c["is_attribute"] <= 0.10]
    return max(near, key=lambda c: (c["n_levels"], c["is_attribute"]))


def schemes_for(field: str) -> dict[tuple[str, ...], list[str]]:
    """Distinct label sets for this field, mapped to the studies using them."""
    src = OUT / f"persona_candidates_{field}.json"
    if not src.exists():
        sys.exit(f"run persona_classify.py --field {field} --all first ({src} missing)")
    cands = json.loads(src.read_text())
    found: dict[tuple[str, ...], list[str]] = {}
    for code, cs in cands.items():
        chosen = pick(cs)
        files = [
            p
            for p in (RAW / code).rglob("*")
            if p.suffix.lower() in {".sav", ".dta"} and not p.name.startswith("._")
        ]
        if not files:
            continue
        ds = spss.read(max(files, key=lambda p: p.stat().st_size))
        col = next((c for c in ds.df.columns if c.upper() == chosen["var"].upper()), None)
        if col is None:
            continue
        labels = tuple(str(v) for _, v in sorted(ds.value_labels.get(col, {}).items()))
        if labels:
            found.setdefault(labels, []).append(code)
    return found


def assign(client: TypeSafeClient, field: str, labels: tuple[str, ...]) -> list[Category]:
    """One Jev call per label: which concept, and is it the catch-all."""
    vocab = VOCAB[field]
    out = []
    for label in labels:
        state = (
            f"A survey recorded the respondent's {field} with these categories:\n\n"
            + "\n".join(f"  - {x}" for x in labels)
            + f"\n\nThe category in question is: {label!r}\n"
        )
        r = client.system_one(
            state=state,
            questions={
                "concept": Choice(
                    criteria={**vocab, "none_of_these": "no listed concept fits"},
                    instructions=(
                        f"Which concept the category {label!r} denotes. Judge the "
                        "category itself, in the context of the full list above. "
                        "Choose none_of_these rather than forcing a poor fit."
                    ),
                ),
                "is_residual": Noul(
                    instructions=(
                        f"The category {label!r} is a CATCH-ALL: it holds respondents "
                        "who do not fit any of the other listed categories. A specific "
                        "named group is not a catch-all, and neither is a refusal or "
                        "missing-data code."
                    )
                ),
            },
        )
        concept = str(r.answers["concept"].choice)
        out.append(
            Category(
                label=label,
                concept=concept,
                is_residual=float(r.answers["is_residual"].noul) >= 0.5,
            )
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--field", default="ethnicity", choices=sorted(VOCAB))
    args = ap.parse_args()

    groups = schemes_for(args.field)
    print(f"{len(groups)} distinct {args.field} schemes across the fetched studies\n")

    client = TypeSafeClient()
    built: list[CatScheme] = []
    declined: list[tuple[str, str]] = []
    for labels, studies in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        name = f"{studies[0]}+{len(studies) - 1}" if len(studies) > 1 else studies[0]
        cats = assign(client, args.field, labels)
        built.append(CatScheme(name=name, categories=cats))
        res = [c.label for c in cats if c.is_residual]
        print(f"--- {name}  ({len(studies)} studies, {len(cats)} categories) ---")
        for c in cats:
            flag = "  <- RESIDUAL" if c.is_residual else ""
            print(f"    {c.label:44} {c.concept}{flag}")
            if c.concept == "none_of_these":
                declined.append((name, c.label))
        if len(res) != 1:
            print(f"    !! {len(res)} residual categories — canonical() needs exactly one")
        print()

    if declined:
        print("JEV DECLINED TO MAP (needs my eyes, not a guess):")
        for name, label in declined:
            print(f"    {name}: {label!r}")
        print()

    try:
        target = canonical(built)
    except ValueError as exc:
        print(f"CANNOT RECONCILE: {exc}")
        return 1

    print(f"CANONICAL {args.field.upper()} — {len(set(target.values()))} categories")
    for v in sorted(set(target.values())):
        print("   ", v)

    maps = {}
    for s in built:
        maps[s.name] = crosswalk(s, target)
    path = OUT / f"persona_crosswalk_{args.field}.json"
    path.write_text(json.dumps({"canonical": target, "schemes": maps}, indent=2))
    print(f"\nwrote {path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
