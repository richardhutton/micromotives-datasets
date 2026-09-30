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

from micromotives_datasets.persona import bands as band_mod  # noqa: E402
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


# Must match persona_classify.TIE_DELTA. Narrow because granularity is only a
# valid tiebreak among candidates measuring the SAME construct, and a wider
# window let "Occupation (detailed)" beat "Current Employment Status".
TIE_DELTA = 0.03


# Fields whose categories sit on an ORDERED ladder. `categories.py` is the wrong
# tool for these: "Bachelor's degree or higher" is not a concept that some
# schemes lack, it is a MERGE OF ADJACENT RUNGS — exactly what `bands.py` does.
# Pointing the categorical algorithm at education made the field unreconcilable,
# which was my error and not a fact about the data.
# Fields whose categories are NUMERIC INTERVALS. `bands.py` handles these
# entirely — parsing and tiling are arithmetic and asserted, so Jev is not asked
# anything it cannot be checked on.
BANDED = {"income"}

ORDINAL = {
    "education": [
        "less_than_high_school",
        "high_school",
        "some_college",
        "associate",
        "bachelors",
        "postgraduate",
    ],
}


def assign_ordinal(client: TypeSafeClient, field: str, labels: tuple[str, ...]):
    """For each label, the lowest and highest rung it covers.

    Two questions rather than one, because a label like "Bachelor's degree or
    higher" genuinely spans several rungs and forcing it onto a single concept
    is what broke the categorical attempt.
    """
    ladder = ORDINAL[field]
    vocab = {k: VOCAB[field][k] for k in ladder}
    out = []
    for label in labels:
        state = (
            f"A survey recorded the respondent's {field} with these categories:\n\n"
            + "\n".join(f"  - {x}" for x in labels)
            + f"\n\nThe category in question is: {label!r}\n"
        )
        qs = {}
        for edge, word in (("lowest", "LOWEST"), ("highest", "HIGHEST")):
            qs[edge] = Choice(
                criteria={**vocab, "none_of_these": "not an educational level at all"},
                instructions=(
                    f"The {word} level of education a respondent in the category "
                    f"{label!r} could have. For a category covering one level only, "
                    "the lowest and the highest are the same."
                ),
            )
        r = client.system_one(state=state, questions=qs)
        lo = str(r.answers["lowest"].choice)
        hi = str(r.answers["highest"].choice)
        if lo == "none_of_these" or hi == "none_of_these":
            out.append((label, None))
            continue
        i, j = ladder.index(lo), ladder.index(hi)
        if i > j:
            i, j = j, i
        out.append((label, band_mod.Band(float(i), float(j + 1), label)))
    return out


def harmonise_banded(field: str, groups: dict) -> int:
    """Numeric-interval harmonisation. No model involved, and none needed.

    Parsing "$10,000 to $12,499" and proving that two bands merge without a gap
    is arithmetic, so it is asserted rather than asked. Jev's contribution to
    this field was upstream: deciding which COLUMN is the respondent's income,
    where a regex offered six vignette variables about a fictional character.
    """
    schemes = []
    for labels, studies in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        name = f"{studies[0]}+{len(studies) - 1}" if len(studies) > 1 else studies[0]
        scheme = band_mod.read_scheme(name, list(labels))
        schemes.append(scheme)
        print(f"--- {name}  ({len(studies)} studies, {len(scheme.bands)} bands) ---")
        problems = scheme.tiles()
        print(f"    {'TILES CLEANLY' if not problems else '; '.join(problems)}")
        if scheme.unparsed:
            print(f"    not bands (left out): {scheme.unparsed}")
        print()

    target = band_mod.canonical(schemes)
    print(f"CANONICAL {field.upper()} — {len(target)} bands")
    for b in target:
        print("   ", b.label)

    maps = {}
    for scheme in schemes:
        cw = band_mod.crosswalk(scheme, target)
        maps[scheme.name] = cw
        merged = sum(1 for dst in set(cw.values()) if list(cw.values()).count(dst) > 1)
        if merged:
            print(f"\n  {scheme.name}: {merged} canonical bands formed by merging")
    path = OUT / f"persona_crosswalk_{field}.json"
    path.write_text(
        json.dumps({"canonical": {b.label: b.label for b in target}, "schemes": maps}, indent=2)
    )
    print(f"\nwrote {path.relative_to(REPO)}")
    return 0


def harmonise_ordinal(client: TypeSafeClient, field: str, groups: dict) -> int:
    """Ordered-ladder harmonisation.

    Same shape as `bands.canonical` — the canonical cut points are the
    INTERSECTION of every scheme's cut points, so a rung boundary survives only
    if all schemes have it — but it cannot reuse `bands.py` directly, because a
    band scheme PARTITIONS the line while several source categories here
    legitimately land on the SAME rung. `sh4px` lists eight separate
    pre-diploma grades ("9th grade", "10th grade", ...) and every one of them is
    `less_than_high_school`; read as intervals those look like eight overlapping
    bands, which is why the first attempt reported nine spurious overlaps.

    So labels are grouped by interval first, and only the distinct intervals are
    treated as the scheme's partition.
    """
    ladder = ORDINAL[field]
    top = len(ladder)
    per_scheme: list[tuple[str, dict[str, tuple[int, int]]]] = []
    declined: list[tuple[str, str]] = []

    for labels, studies in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        name = f"{studies[0]}+{len(studies) - 1}" if len(studies) > 1 else studies[0]
        spans: dict[str, tuple[int, int]] = {}
        print(f"--- {name}  ({len(studies)} studies) ---")
        for label, band in assign_ordinal(client, field, labels):
            if band is None:
                declined.append((name, label))
                print(f"    {label:48} not an educational level")
                continue
            lo, hi = int(band.lo), int(band.hi)
            spans[label] = (lo, hi)
            rungs = ladder[lo] if hi - lo == 1 else f"{ladder[lo]}..{ladder[hi - 1]}"
            print(f"    {label:48} {rungs}")
        per_scheme.append((name, spans))
        covered = sorted(set(spans.values()))
        holes = [(a[1], b[0]) for a, b in zip(covered, covered[1:], strict=False) if a[1] < b[0]]
        if holes:
            print(f"    note: rungs no category covers: {holes}")
        print()

    if declined:
        print("JEV DECLINED TO MAP (needs my eyes, not a guess):")
        for name, label in declined:
            print(f"    {name}: {label!r}")
        print()

    # An interior cut survives only if EVERY scheme cuts there.
    edge_sets = [
        {e for span in spans.values() for e in span if 0 < e < top}
        for _, spans in per_scheme
        if spans
    ]
    if not edge_sets:
        print("no scheme yielded any levels")
        return 1
    cuts = [0, *sorted(set.intersection(*edge_sets)), top]
    canon = [
        (lo, hi, ladder[lo] if hi - lo == 1 else f"{ladder[lo]} to {ladder[hi - 1]}")
        for lo, hi in zip(cuts, cuts[1:], strict=False)
    ]
    print(f"CANONICAL {field.upper()} — {len(canon)} levels")
    for _, _, label in canon:
        print("   ", _pretty(label))

    # A scheme that cannot be mapped is REPORTED and skipped, not fatal. `yc2qb`
    # offers both "BA or above" and "Post-graduate Degree" as separate options,
    # so its own categories overlap: read literally, "BA or above" spans two
    # canonical rungs. That is a real property of that questionnaire, and
    # letting one awkward scheme block the other 71 would be the wrong trade —
    # so it goes on a review list instead of being forced into a rung.
    maps: dict[str, dict[str, str]] = {}
    unmappable: list[tuple[str, str, int]] = []
    for name, spans in per_scheme:
        mapping, failed = {}, False
        for label, (lo, hi) in spans.items():
            holders = [c for c in canon if c[0] <= lo and hi <= c[1]]
            if len(holders) != 1:
                unmappable.append((name, label, len(holders)))
                failed = True
                continue
            mapping[label] = _pretty(holders[0][2])
        if not failed:
            maps[name] = mapping

    if unmappable:
        print("\nSCHEMES LEFT UNMAPPED (their own categories overlap — need my eyes):")
        for name, label, n in unmappable:
            print(f"    {name}: {label!r} spans {n} canonical levels")
        print(f"    -> {len(maps)} of {len(per_scheme)} schemes mapped")
    path = OUT / f"persona_crosswalk_{field}.json"
    path.write_text(
        json.dumps(
            {"canonical": {_pretty(c[2]): _pretty(c[2]) for c in canon}, "schemes": maps},
            indent=2,
        )
    )
    print(f"\nwrote {path.relative_to(REPO)}")
    return 0


def _pretty(slug: str) -> str:
    """`bachelors to postgraduate` -> `Bachelors to postgraduate`."""
    words = slug.replace("_", " ")
    return words[:1].upper() + words[1:]


def pick(cands: list[dict]) -> dict:
    live = [c for c in cands if c["is_attribute"] >= 0.5] or cands
    best = max(c["is_attribute"] for c in live)
    near = [c for c in live if best - c["is_attribute"] <= TIE_DELTA]
    return max(near, key=lambda c: (c["n_levels"], c["is_attribute"]))


def schemes_from_recipes(field: str) -> dict[tuple[str, ...], list[str]]:
    """Distinct label sets for this field, from the variable each RECIPE declares.

    The only correct source, arrived at after getting it wrong twice.

    Deriving from the variable Jev PICKED covers that variable's labels, but a
    recipe renders whatever variable IT declared, which may be a coarser
    sibling: the classifier prefers the fine-grained `PPEDUC` while the recipes
    map the 4-level `PPEDUCAT`, so the crosswalk covered labels the corpus never
    contains and missed every label it does. QC rule 14 caught that on the first
    rebuild.

    Deriving from the BUILT CORPUS then looks right and is worse — it is
    circular. Once the crosswalk is applied the corpus holds harmonised labels,
    so a second run reads its own output back as input.

    The recipes' own declared variables, read raw from the source file, are
    neither: they are exactly what gets rendered, and they never change under us.
    """
    from micromotives_datasets.cli import _resolve_data_file
    from micromotives_datasets.recipe import load as load_recipe

    found: dict[tuple[str, ...], list[str]] = {}
    for path in sorted((REPO / "recipes").glob("*.yaml")):
        rec = load_recipe(path)
        var = rec.persona_map.get(field)
        if not var:
            continue
        ds = spss.read(_resolve_data_file(rec.study_id, rec.data_file))
        col = next((c for c in ds.df.columns if c.upper() == var.upper()), None)
        if col is None:
            continue
        # EVERY declared value label, not only the ones this sample happens to
        # contain. A scheme's categories are what the questionnaire OFFERED.
        # Filtering to observed values made `zrwjp` look like a 2-category
        # scheme — its respondents are all in work — which then forced every
        # other study's retired/disabled/unemployed distinctions to collapse
        # into one bucket. Absence in a sample is not absence from the scheme.
        labels = tuple(str(v) for _, v in sorted(ds.value_labels.get(col, {}).items()))
        if labels:
            found.setdefault(labels, []).append(path.stem)
    return found


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
    ap.add_argument("--field", default="ethnicity", choices=sorted(set(VOCAB) | BANDED))
    ap.add_argument(
        "--from-candidates",
        action="store_true",
        help="derive schemes from the variables Jev picked across all 73 fetched "
        "studies, rather than from the variables the built recipes declare "
        "(the default). Use this to see what is coming when more studies land.",
    )
    args = ap.parse_args()

    groups = schemes_for(args.field) if args.from_candidates else schemes_from_recipes(args.field)
    print(f"{len(groups)} distinct {args.field} schemes across the fetched studies\n")

    if args.field in BANDED:
        return harmonise_banded(args.field, groups)

    client = TypeSafeClient()
    if args.field in ORDINAL:
        return harmonise_ordinal(client, args.field, groups)
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
