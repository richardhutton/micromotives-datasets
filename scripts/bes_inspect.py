#!/usr/bin/env python3
"""
bes_inspect.py — inspect the British Election Study (BES) Internet Panel .dta,
the way explore.py inspects SocSci210. No prompts/reasoning here — the point is
to understand the RAW survey format: what variables exist, what topics are
covered, the demographics, and (crucially) which items are experiments.

The BES file is a WIDE panel: 1 row per respondent (~127k), ~13k columns, where
almost every measure repeats per wave with a `W<n>` suffix (e.g. partyIdW7).
Strip the suffix and you get the underlying "measure" / topic.

Metadata (names + labels + value labels) reads in <1s without loading the 3.6GB
of data, so most commands are instant. Only `values` and `sample` touch data,
and they read just the columns you ask for (optionally a row sample).

Commands
--------
  overview      dimensions, waves, measure count, label coverage
  catalog       dump ALL variables + labels + wave to a CSV
  measures      distinct measures (suffix stripped) + which waves they span
  search TERM   find variables whose name/label matches a keyword
  demographics  auto-detected demographic variables (the persona fields)
  experiments   auto-flagged experiment / randomisation variables
  values VAR    value labels + distribution for one variable
  sample        show a few respondents across chosen variables

Examples
--------
  python bes_inspect.py overview
  python bes_inspect.py search immigration
  python bes_inspect.py experiments
  python bes_inspect.py values partyIdW31
  python bes_inspect.py sample --vars ageW1,gender,partyIdW31 -n 5
"""

from __future__ import annotations

import argparse
import re
import sys

import pyreadstat

DEFAULT_DTA = "/Users/richhuton/bes-data/BES2024_W31_Panel_v31.05.dta"
WAVE_RE = re.compile(r"(W\d+)+$")  # strips one or more trailing W<n>
FIRST_WAVE_RE = re.compile(r"W(\d+)")

# High-precision keywords for likely experiment / randomisation items. Kept
# tight on purpose: loose words like "condition"/"version"/"prime" flood the
# results with medical conditions, scale versions and "Prime Minister".
EXPERIMENT_KW = [
    "experiment",
    "random",
    "manipulat",
    "vignette",
    "wording",
    "split ballot",
    "split-ballot",
    "control group",
    "treatment group",
    "primed with",
    "assigned at random",
    "was shown",
    "question wording",
]
# Core socio-demographic base measures (the persona fields). The BES `p_`
# profile block is caught by prefix; these are the non-p_ ones worth including.
CORE_DEMOG = {
    "age",
    "ageGroup",
    "gender",
    "country",
    "gor",
    "oslaua",
    "pcon",
    "new_pcon",
    "partyId",
    "partyIdStrength",
    "ethnicity",
    "religion",
    "housing",
    "gross_household",
    "gross_personal",
    "socgrade",
    "education",
    "disability",
    "workingStatus",
    "subjClass",
    "maritalStatus",
}


# ---------------------------------------------------------------------------
# Metadata loading (cached per process)
# ---------------------------------------------------------------------------
_META = None


def meta(path: str):
    """Read BES metadata only (fast, no data)."""
    global _META
    if _META is None:
        _, _META = pyreadstat.read_dta(path, metadataonly=True)
    return _META


def base_measure(name: str) -> str:
    """Strip the trailing W<n> wave suffix to get the underlying measure."""
    return WAVE_RE.sub("", name)


def wave_of(name: str):
    m = WAVE_RE.search(name)
    if not m:
        return None
    first = FIRST_WAVE_RE.search(m.group(0))
    return int(first.group(1)) if first else None


def label_of(m, name: str) -> str:
    return m.column_names_to_labels.get(name) or ""


def _rule(title: str) -> None:
    print(f"\n\033[1m{title}\033[0m")
    print("─" * min(len(title), 72))


def _matches(m, name: str, keywords) -> bool:
    hay = f"{name} {label_of(m, name)}".lower()
    return any(k in hay for k in keywords)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_overview(args) -> None:
    m = meta(args.dta)
    cols = m.column_names
    waves = sorted({wave_of(c) for c in cols if wave_of(c)})
    measures = {base_measure(c) for c in cols}
    _rule("BES Internet Panel — overview")
    print(f"file:      {args.dta}")
    print(f"rows:      {m.number_rows:,} respondents")
    print(f"columns:   {m.number_columns:,} variables")
    print(f"waves:     {len(waves)} (W{min(waves)}–W{max(waves)})")
    print(f"measures:  {len(measures):,} distinct (after stripping W<n> suffix)")
    print(f"labelled:  {len(m.variable_value_labels):,} variables have value labels")
    non_wave = [c for c in cols if wave_of(c) is None]
    print(f"\n{len(non_wave)} non-wave (respondent-level) variables, e.g.:")
    for c in non_wave[:20]:
        print(f"  {c:<24} {label_of(m, c)[:60]}")


def cmd_catalog(args) -> None:
    import csv

    m = meta(args.dta)
    out = args.out
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["variable", "measure", "wave", "label", "n_value_labels"])
        for c in m.column_names:
            w.writerow(
                [
                    c,
                    base_measure(c),
                    wave_of(c) or "",
                    label_of(m, c),
                    len(m.variable_value_labels.get(c, {})),
                ]
            )
    print(f"wrote {m.number_columns:,} variables to {out}")
    print("open it in a spreadsheet / pandas to browse everything.")


def cmd_measures(args) -> None:
    m = meta(args.dta)
    groups = {}
    for c in m.column_names:
        b = base_measure(c)
        groups.setdefault(b, {"waves": set(), "label": label_of(m, c)})
        wv = wave_of(c)
        if wv:
            groups[b]["waves"].add(wv)
        if not groups[b]["label"]:
            groups[b]["label"] = label_of(m, c)
    # sort by how many waves a measure spans (persistent topics first)
    rows = sorted(groups.items(), key=lambda kv: -len(kv[1]["waves"]))
    if args.filter:
        rows = [r for r in rows if args.filter.lower() in f"{r[0]} {r[1]['label']}".lower()]
    _rule(
        f"{len(rows)} measures"
        + (f" matching '{args.filter}'" if args.filter else "")
        + " (most-persistent first)"
    )
    for base, info in rows[: args.limit]:
        nw = len(info["waves"])
        span = f"{nw}w" if nw else "1x"
        print(f"  {base:<26} [{span:>4}]  {info['label'][:58]}")
    if len(rows) > args.limit:
        print(f"  … {len(rows) - args.limit} more (raise --limit or use `search`)")


def cmd_search(args) -> None:
    m = meta(args.dta)
    term = args.term.lower()
    hits = [(c, label_of(m, c)) for c in m.column_names if term in f"{c} {label_of(m, c)}".lower()]
    _rule(f"{len(hits)} variables matching '{args.term}'")
    # collapse by measure so 31 waves of one item don't flood the output
    bymeasure = {}
    for c, lbl in hits:
        bymeasure.setdefault(base_measure(c), (lbl, []))[1].append(wave_of(c))
    for base, (lbl, waves) in list(bymeasure.items())[: args.limit]:
        waves = sorted(w for w in waves if w)
        wtxt = f"W{waves[0]}–W{waves[-1]}" if len(waves) > 1 else (f"W{waves[0]}" if waves else "—")
        print(f"  {base:<26} [{wtxt:>9}]  {lbl[:56]}")
    if len(bymeasure) > args.limit:
        print(f"  … {len(bymeasure) - args.limit} more measures; refine the term")


def _is_demographic(name: str) -> bool:
    base = base_measure(name)
    return name.startswith("p_") or base in CORE_DEMOG or base.startswith("p_")


def cmd_demographics(args) -> None:
    m = meta(args.dta)
    bymeasure = {}
    for c in m.column_names:
        if _is_demographic(c):
            bymeasure.setdefault(base_measure(c), label_of(m, c))
    _rule(f"{len(bymeasure)} DEMOGRAPHIC measures (persona fields)")
    for base, lbl in sorted(bymeasure.items())[: args.limit]:
        print(f"  {base:<26} {lbl[:60]}")
    print(
        "\n(The `p_*` block is the YouGov profile — the clean persona fields "
        "mapping to SocSci210's `demographic` struct. Verify against the "
        "questionnaire.)"
    )


def cmd_experiments(args) -> None:
    m = meta(args.dta)
    hits = [c for c in m.column_names if _matches(m, c, EXPERIMENT_KW)]
    bymeasure = {}
    for c in hits:
        bymeasure.setdefault(base_measure(c), (label_of(m, c), set()))[1].add(wave_of(c))
    _rule(f"{len(bymeasure)} likely EXPERIMENT / RANDOMISATION measures")
    for base, (lbl, waves) in sorted(bymeasure.items())[: args.limit]:
        nw = len([w for w in waves if w])
        print(f"  {base:<26} [{nw or 1:>2}w]  {lbl[:56]}")
    print(
        "\n⭐ These are the SocSci210-equivalent gold: variables that record a "
        "randomised condition/treatment. Cross-check each against the "
        "questionnaire PDF to see the actual manipulation."
    )


def _resolve(m, name: str) -> str:
    """Resolve a possibly suffix-stripped measure to a real column name."""
    if name in m.column_names:
        return name
    cands = [c for c in m.column_names if base_measure(c) == name]
    if not cands:
        raise SystemExit(f"'{name}' not found. Try: python bes_inspect.py search {name}")
    if len(cands) == 1:
        print(f"(resolved '{name}' → '{cands[0]}')")
        return cands[0]
    # multiple waves: default to the latest, tell the user how to override
    latest = max(cands, key=lambda c: wave_of(c) or 0)
    print(
        f"(resolved '{name}' → '{latest}'; spans {len(cands)} waves, using "
        f"latest — pass a full name like {name}W1 for another)"
    )
    return latest


def cmd_values(args) -> None:
    m = meta(args.dta)
    var = _resolve(m, args.var)
    _rule(f"{var} — {label_of(m, var)}")
    labels = m.variable_value_labels.get(var, {})
    if labels:
        print("value labels:")
        for val, lbl in labels.items():
            print(f"  {val!r:>6} = {lbl}")
    # distribution from a row sample (fast); exact if you raise --rows
    df, _ = pyreadstat.read_dta(args.dta, usecols=[var], row_limit=args.rows)
    vc = df[var].value_counts(dropna=False).head(args.top)
    print(f"\ndistribution (first {args.rows:,} rows):")
    for val, cnt in vc.items():
        lbl = labels.get(val, "")
        print(f"  {cnt:>8,}  {str(val):>6}  {lbl}")


def cmd_sample(args) -> None:
    m = meta(args.dta)
    want = [_resolve(m, v.strip()) for v in args.vars.split(",")] if args.vars else []
    cols = (["id"] if "id" in m.column_names else []) + want
    df, _ = pyreadstat.read_dta(args.dta, usecols=cols, row_limit=args.n)
    _rule(f"{len(df)} sample respondents × {len(want)} variables")
    for _, row in df.iterrows():
        print("\n── respondent", row.get("id", "?"), "─" * 40)
        for v in want:
            raw = row[v]
            lbl = m.variable_value_labels.get(v, {}).get(raw, "")
            print(f"  {v:<24} {str(raw):>8}  {lbl}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--dta", default=DEFAULT_DTA, help="path to the BES .dta")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("overview").set_defaults(func=cmd_overview)

    sp = sub.add_parser("catalog", help="dump all variables to CSV")
    sp.add_argument("--out", default="bes_catalog.csv")
    sp.set_defaults(func=cmd_catalog)

    sp = sub.add_parser("measures", help="distinct measures / topics")
    sp.add_argument("--filter", help="only measures matching this text")
    sp.add_argument("--limit", type=int, default=60)
    sp.set_defaults(func=cmd_measures)

    sp = sub.add_parser("search", help="find variables by keyword")
    sp.add_argument("term")
    sp.add_argument("--limit", type=int, default=40)
    sp.set_defaults(func=cmd_search)

    sp = sub.add_parser("demographics", help="auto-detected persona fields")
    sp.add_argument("--limit", type=int, default=80)
    sp.set_defaults(func=cmd_demographics)

    sp = sub.add_parser("experiments", help="auto-flagged experiment variables")
    sp.add_argument("--limit", type=int, default=80)
    sp.set_defaults(func=cmd_experiments)

    sp = sub.add_parser("values", help="value labels + distribution for one var")
    sp.add_argument("var")
    sp.add_argument("--rows", type=int, default=20000, help="row sample size")
    sp.add_argument("--top", type=int, default=20)
    sp.set_defaults(func=cmd_values)

    sp = sub.add_parser("sample", help="show respondents across chosen vars")
    sp.add_argument("--vars", required=True, help="comma-separated variable names")
    sp.add_argument("-n", type=int, default=5)
    sp.set_defaults(func=cmd_sample)

    return p


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
