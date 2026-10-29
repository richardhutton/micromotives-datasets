#!/usr/bin/env python3
"""First look at the BES combined Internet Panel, before any build is designed.

The panel is ~127,000 respondents x ~13,000 variables in one wide file, one row
per person with each measure repeated per wave (`partyIdW1` ... `partyIdW31`).
Nothing about the profile build can be decided without knowing what is actually
in it, and four things in particular have already cost this project time
elsewhere:

1. **Truncated labels.** Six deposits here have shipped value or variable labels
   severed mid-word at a format ceiling, and in IP 9.10 the archived labels were
   not merely truncated but WRONG -- two opposite housework splits sharing one
   string. BES variable labels are expected to carry the question wording, which
   is the most valuable thing in the file, so this counts how many sit suspiciously
   close to 80 / 120 / 256 characters and prints the worst offenders to look at.

2. **Encoding.** `pandas.read_stata` silently falls back to latin-1, which is how
   mojibake enters a dataset unnoticed. The project reader fails loudly instead;
   this reports which encoding it landed on.

3. **How much panel there actually is.** The master doc records heavy attrition --
   median 5 waves of 31, about 31% doing ten or more. The profile work needs
   people with long histories, so the usable N is the count of deep respondents,
   not 127,000.

4. **Whether the repeated-measure ceiling can be computed.** The whole reason
   today's numbers are interpretable is `scripts/ceiling.py`: a question asked in
   two waves tells you how often a person reproduces their own answer. This checks
   how many variables repeat across waves at all, because that is what decides
   whether a BES ceiling is measurable.

**THE WHOLE FILE IS NEVER LOADED, AND THAT IS NOT AN OPTIMISATION.** 126,709 rows
x ~13,000 columns is about 1.6 billion cells; as float64 that is roughly 13 GB,
on a 16 GB machine that was already at 0.1 GB free and 11.5 GB of swap. The first
version of this script did load it, and had to be killed. Labels, wave structure
and the encoding check need no rows at all -- `metadataonly` answers them in
seconds -- and the depth check needs one measure's worth of columns, not all of
them. Any future work on this file should assume the same: read what you need,
never the frame.

    uv run python scripts/bes_inspect_panel.py
    uv run python scripts/bes_inspect_panel.py --file <path>
"""

from __future__ import annotations

import argparse
import re
import statistics
import warnings
from collections import Counter
from pathlib import Path

import pyreadstat

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[1]
BES = REPO / "data" / "raw" / "bes_panel"

# `partyIdW31` -> ("partyId", 31). The wave suffix is how a wide panel stores a
# repeated measure, so stripping it is what turns 13,000 columns into the much
# smaller number of actual questions.
WAVE_SUFFIX = re.compile(r"^(?P<stem>.+?)W(?P<wave>\d{1,2})$")

# Format ceilings labels get severed at. 80 is Stata's variable-label limit and
# where five of this project's six truncation findings sat; 120 and 256 are SPSS
# value- and variable-label limits.
CEILINGS = (80, 120, 256)


def read_metadata(path: Path):
    """Metadata only -- no rows. Encoding fallbacks in the order spss.py uses.

    `micromotives_datasets.sources.spss.read` is the project reader and the right
    thing everywhere else, but it loads the frame. Its encoding chain is reused
    here deliberately: cp1252 before latin1, because latin1 maps all 256 byte
    values and so never raises, which would hide a wrong decode rather than
    surface it.
    """
    last: Exception | None = None
    for encoding in (None, "cp1252", "latin1", "utf-8-sig", "iso-8859-15"):
        try:
            _, meta = (
                pyreadstat.read_sav(str(path), metadataonly=True)
                if encoding is None
                else pyreadstat.read_sav(str(path), metadataonly=True, encoding=encoding)
            )
            if encoding:
                print(f"  (read with encoding {encoding})")
            return meta
        except Exception as exc:  # trying the next encoding is the point
            last = exc
    raise SystemExit(f"could not read metadata from {path.name}: {last}")


def find_file(given: str | None) -> Path:
    if given:
        path = Path(given)
        if not path.exists():
            raise SystemExit(f"not found: {path}")
        return path
    candidates = sorted(
        [p for p in BES.glob("*") if p.suffix.lower() in {".sav", ".dta"}],
        key=lambda p: p.stat().st_size,
        reverse=True,
    )
    if not candidates:
        raise SystemExit(
            f"no .sav or .dta in {BES}\n"
            "Download the combined waves 1-31 Internet Panel (SPSS) and put it there."
        )
    return candidates[0]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--file", help="path to the panel file (default: largest in data/raw/bes_panel)"
    )
    ap.add_argument("--show", type=int, default=12, help="how many examples to print")
    args = ap.parse_args()

    path = find_file(args.file)
    size_gb = path.stat().st_size / 1024**3
    print(f"reading metadata from {path.name} ({size_gb:.2f} GB)\n")
    meta = read_metadata(path)

    rows, cols = meta.number_rows, len(meta.column_names)
    print(f"{rows:,} respondents x {cols:,} variables")

    # --- 1. labels -----------------------------------------------------------
    var_labels = [str(v) for v in meta.column_names_to_labels.values() if v]
    value_label_sets = meta.variable_value_labels
    val_labels = [str(t) for m in value_label_sets.values() for t in m.values() if t]
    print(f"\nVARIABLE LABELS  {len(var_labels):,} present of {cols:,} columns")
    if var_labels:
        lengths = [len(v) for v in var_labels]
        print(f"  length: median {statistics.median(lengths):.0f}, max {max(lengths)}")
        for limit in CEILINGS:
            at = [v for v in var_labels if limit - 2 <= len(v) <= limit]
            if at:
                print(f"  {len(at):,} sit within 2 characters of {limit} — possible truncation")
        # A label ending mid-word is the signature that survives any limit change.
        cut = [v for v in var_labels if len(v) >= 60 and not re.search(r"[.?!)\]\s]$", v)]
        print(f"  {len(cut):,} end without punctuation or space (may be severed):")
        for v in cut[: args.show]:
            print(f"      [{len(v):>3}] {v}")

    print(f"\nVALUE LABELS     {len(val_labels):,} across {len(value_label_sets):,} variables")
    if val_labels:
        lengths = [len(v) for v in val_labels]
        print(f"  length: median {statistics.median(lengths):.0f}, max {max(lengths)}")
        for limit in CEILINGS:
            at = [v for v in val_labels if limit - 2 <= len(v) <= limit]
            if at:
                print(f"  {len(at):,} sit within 2 characters of {limit} — possible truncation")

    # --- 2. the wave structure ----------------------------------------------
    stems: dict[str, set[int]] = {}
    unwaved = []
    for col in meta.column_names:
        found = WAVE_SUFFIX.match(str(col))
        if found:
            stems.setdefault(found.group("stem"), set()).add(int(found.group("wave")))
        else:
            unwaved.append(str(col))
    repeated = {s: w for s, w in stems.items() if len(w) > 1}
    print("\nWAVE STRUCTURE")
    print(f"  {len(stems):,} distinct measures carry a wave suffix")
    print(
        f"  {len(repeated):,} of them appear in MORE THAN ONE wave  <- the ceiling is "
        f"measurable on these"
    )
    print(f"  {len(unwaved):,} columns carry no wave suffix (persona, weights, ids)")
    if repeated:
        deepest = sorted(repeated.items(), key=lambda kv: -len(kv[1]))[: args.show]
        print("  measures present in the most waves:")
        for stem, waves in deepest:
            print(f"      {stem:<28} {len(waves):>2} waves")

    # --- 3. how much panel per person ---------------------------------------
    # A person's depth is how many waves they actually answered. `wt_` weights or
    # a `wave` indicator would be cheaper, but the honest measure is non-missing
    # answers on a measure asked in every wave.
    best = max(repeated.items(), key=lambda kv: len(kv[1]), default=(None, set()))
    if best[0]:
        stem, waves = best
        wanted = [f"{stem}W{w}" for w in sorted(waves)]
        wanted = [c for c in wanted if c in set(meta.column_names)]
        print(f"\nDEPTH, measured on '{stem}' ({len(wanted)} waves) — reading those columns only")
        frame, _ = pyreadstat.read_sav(str(path), usecols=wanted, disable_datetime_conversion=True)
        present = frame.notna().sum(axis=1)
        depth = Counter(int(d) for d in present)
        for threshold in (1, 5, 10, 15, 20):
            n = sum(c for d, c in depth.items() if d >= threshold)
            print(f"  answered {threshold:>2}+ waves: {n:>7,}  ({n / rows:.0%})")

    print("\nmetadata read without mojibake")


if __name__ == "__main__":
    main()
