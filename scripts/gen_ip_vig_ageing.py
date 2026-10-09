#!/usr/bin/env python3
"""Derive the data files for IP 9.18 — what counts as "successful ageing".

Waves 9 (2016) and 17 (2024). Each respondent read three descriptions of an
imaginary 75-year-old and rated how successfully each was ageing, 0-10. Six
dimensions were randomised per description — chronic disease, disability,
cognition, physical functioning, seeing family and friends, volunteering — and
the name, which also sets the pronouns. 4 names x 2^6 = 256 possible arms.

The recipes (`recipes/ukds_6849_vig_ageing_w{9,17}.yaml`) hold the judgement:
the template, its clauses word-for-word from the questionnaire, the persona map.
This script does what a recipe cannot:

**One name coding across all three slots.** The archive codes each slot's name
differently. In wave 9, `i_vname1` is 1 = George, 2 = Margaret, but `i_vname2`
and `i_vname3` are 1 = Margaret, 2 = Harry, 3 = George, 4 = Anne. Wave 17 has
no per-slot name at all, only the sequence `q_vignameip17` (1-6), whose six
sequences the User Guide tabulates. `by_raw` keys arms on codes, so every slot
must use one coding, and this script writes `vname1-3` in the coding of `NAMES`
below. `--check` verifies the derived name against the archive's own label for
that slot (wave 9) and against the sequence label (wave 17), so a wrong map
fails rather than renders the wrong person.

**The prefix and suffix are stripped.** `i_vdisease1` and `q_vdisease1ip17`
both become `vdisease1`, so one recipe shape serves both waves.

**`pidp` is never written out.** The derived file carries `person`, the same
hash as `scripts/build_profiles.py` and `gen_ip_vig_housework.py`, so one person
keeps one id across this study, the housework study and their profile.

WAVE 17'S RANDOMISATION PARTLY FAILED. The guide says each dimension was
allocated half and half, each name sequence one sixth. In the data, 354
respondents — all web, mostly interviewed in November and December 2024 — share
one identical allocation (name sequence 5 and all eighteen life-dimension codes),
and a further 579 share theirs with at least one other respondent, in groups of
at most 8, 181 of 209 groups on a single start date. Wave 9, by contrast, gives
2,010 distinct allocations to 2,010 people. The
stored codes drive the displayed text, so each row's condition is still what
that person read; what is lost is the independence of the design. `--check`
reports these counts so they are computed, not quoted.

    uv run python scripts/gen_ip_vig_ageing.py --check
    uv run python scripts/gen_ip_vig_ageing.py --write
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

from micromotives_datasets.sources import spss

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[1]
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"
OUT = REPO / "data" / "raw" / "ukds_6849"

# Wave letter -> (wave number, fieldwork year, how a slot-i variable is named).
WAVES = {
    "i": (9, 2016, "i_{v}{i}"),
    "q": (17, 2024, "q_{v}{i}ip17"),
}

# The six randomised dimensions, archive names without prefix, slot or suffix.
DIMS = ("vdisease", "vdisability", "vcognit", "vphys", "vinterp", "vvolun")

# The one name coding every derived slot uses. The recipe's levels are keyed on it.
NAMES = {1: "George", 2: "Margaret", 3: "Harry", 4: "Anne"}
CODE = {name: code for code, name in NAMES.items()}

# The User Guide's six name sequences (section 9.18, both waves), which
# `q_vignameip17`'s own value labels repeat and wave 9's per-slot names confirm.
SEQUENCES = {
    1: ("George", "Margaret", "Harry"),
    2: ("George", "Margaret", "Anne"),
    3: ("George", "Harry", "Margaret"),
    4: ("Margaret", "George", "Harry"),
    5: ("Margaret", "George", "Anne"),
    6: ("Margaret", "Anne", "George"),
}

# Same persona variables as the housework build, for the same reasons: there is
# no tenure, household-size or net-income variable in `indresp`.
PERSONA = (
    "dvage",
    "sex",
    "gor_dv",
    "jbstat",
    "hiqual_dv",
    "mastat_dv",
    "racel_dv",
    "nchild_dv",
)


def person_hash(pidp: int) -> str:
    """Same construction as `scripts/build_profiles.py`. Never the raw `pidp`."""
    import hashlib

    return "ip_" + hashlib.sha256(f"ukds6849:{pidp}".encode()).hexdigest()[:12]


def derived_name(wave: int) -> str:
    return f"vig_ageing_w{wave}-derived.sav"


def _src(w: str, v: str, i: int | str = "") -> str:
    return WAVES[w][2].format(v=v, i=i)


def names_by_slot(w: str, df: pd.DataFrame, labels: dict) -> pd.DataFrame:
    """The name each respondent saw in each slot, as text. NaN where unallocated.

    Wave 9 reads the archive's per-slot name through that slot's OWN labels, so
    the differing codings are resolved by name rather than by a hand-written
    number map. Wave 17 decodes the sequence through the guide's table.
    """
    out = pd.DataFrame(index=df.index)
    if w == "i":
        for i in (1, 2, 3):
            var = _src(w, "vname", i)
            lab = labels[var]
            out[i] = df[var].map(lambda c, lab=lab: lab.get(c) if c > 0 else np.nan)
    else:
        seq = df[_src(w, "vigname")]
        for i in (1, 2, 3):
            out[i] = seq.map(lambda c, i=i: SEQUENCES[int(c)][i - 1] if c > 0 else np.nan)
    return out


def derive(w: str) -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    """One row per respondent: their three descriptions, answers and persona."""
    wave, year, _ = WAVES[w]
    r = spss.read(STATA / f"{w}_indresp_ip.dta")
    df = r.df

    needed = [_src(w, "vign", i) for i in (1, 2, 3)]
    needed += [_src(w, d, i) for d in DIMS for i in (1, 2, 3)]
    needed += [f"{w}_{v}" for v in PERSONA] + ["pidp"]
    needed += [_src(w, "vname", i) for i in (1, 2, 3)] if w == "i" else [_src(w, "vigname")]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"wave {wave}: indresp is missing {missing}")

    names = names_by_slot(w, df, r.value_labels)
    unknown = set(names.stack().dropna()) - set(CODE)
    if unknown:
        raise ValueError(f"wave {wave}: names outside the four declared: {sorted(unknown)}")

    out = pd.DataFrame({"person": [person_hash(int(p)) for p in df["pidp"]]})
    for i in (1, 2, 3):
        out[f"vign{i}"] = df[_src(w, "vign", i)].to_numpy()
        # Unallocated slots keep the archive's own negative code, so the melt's
        # missing handling sees exactly what the archive recorded.
        sentinel = df[_src(w, DIMS[0], i)].to_numpy()
        out[f"vname{i}"] = np.where(
            names[i].notna(), names[i].map(CODE).fillna(-9).to_numpy(), sentinel
        ).astype(float)
        for d in DIMS:
            out[f"{d}{i}"] = df[_src(w, d, i)].to_numpy()
    for v in PERSONA:
        out[v] = df[f"{w}_{v}"].to_numpy()
    out["wave"] = wave
    out["year"] = year

    labels: dict[str, dict[float, str]] = {}
    for v in PERSONA:
        got = r.value_labels.get(f"{w}_{v}")
        if got:
            labels[v] = dict(got)
    for i in (1, 2, 3):
        got = r.value_labels.get(_src(w, "vign", i))
        if got:
            labels[f"vign{i}"] = dict(got)
        labels[f"vname{i}"] = {float(c): n for c, n in NAMES.items()}
    return out, labels


def check(w: str) -> int:
    """Verify the DERIVED names against the archive's own record. Returns failures.

    Compares the frame `derive` returns, row for row with `indresp`, so a defect
    in the derivation — not merely in the source files — is what would fail.
    """
    wave = WAVES[w][0]
    r = spss.read(STATA / f"{w}_indresp_ip.dta")
    df = r.df
    derived, _ = derive(w)
    if len(derived) != len(df):
        raise ValueError(f"wave {wave}: derived {len(derived)} rows from {len(df)}")
    bad = 0
    compared = 0

    if w == "i":
        # Each derived code, decoded through NAMES, must equal the label the
        # archive gives that slot's own code.
        for i in (1, 2, 3):
            var = _src(w, "vname", i)
            lab = r.value_labels[var]
            for mine, theirs in zip(derived[f"vname{i}"], df[var], strict=True):
                if theirs > 0:
                    compared += 1
                    bad += NAMES.get(int(mine)) != lab[theirs]
        # And the triples seen must be exactly the guide's six sequences.
        allocated = df[_src(w, "vname", 1)] > 0
        triples = {
            tuple(NAMES[int(derived.loc[k, f"vname{i}"])] for i in (1, 2, 3))
            for k in derived.index[allocated]
        }
        extra = triples - set(SEQUENCES.values())
        print(
            f"  wave {wave}: {len(triples)} distinct name triples, "
            f"{'all' if not extra else 'NOT all'} among the guide's six"
        )
        bad += len(extra)
    else:
        # The sequence's own value label spells the three names out.
        var = _src(w, "vigname")
        lab = r.value_labels[var]
        for k in derived.index:
            code = df.loc[k, var]
            if code > 0:
                want = tuple(s.strip() for s in lab[code].split(","))
                got = tuple(NAMES.get(int(derived.loc[k, f"vname{i}"])) for i in (1, 2, 3))
                compared += 3
                bad += sum(a != b for a, b in zip(got, want, strict=True))

    print(
        f"  wave {wave}: {compared:,} derived names compared with the archive's labels — "
        f"{'AGREE' if bad == 0 else f'{bad} DISAGREEMENTS'}"
    )
    report_allocation(w, derived)
    return bad


def report_allocation(w: str, derived: pd.DataFrame) -> dict[str, int]:
    """How random the allocation actually was. Reported, never a failure.

    Under the design as documented, 2^18 x 6 profiles across ~2,000 people
    should almost never repeat. Wave 9 behaves so; wave 17 does not.

    The key is all three names plus all eighteen codes. An earlier version used
    only slot 1's name, which merges name sequences 1-3 (and 4-6) and reported
    1,395 / 1,060 for wave 17 where the truth is 1,497 / 933 — caught by the
    independent checker, not by its own test, which had pinned the wrong numbers.
    """
    wave = WAVES[w][0]
    cols = [f"vname{i}" for i in (1, 2, 3)] + [f"{d}{i}" for i in (1, 2, 3) for d in DIMS]
    a = derived[derived["vdisease1"] > 0]
    prof = a[cols].astype(int).astype(str).agg("".join, axis=1)
    counts = prof.value_counts()
    out = {
        "allocated": len(a),
        "distinct": int(counts.size),
        "largest_block": int(counts.iloc[0]),
        "in_repeated": int(counts[counts > 1].sum()),
    }
    print(
        f"  wave {wave}: {out['allocated']:,} allocated, {out['distinct']:,} distinct "
        f"allocations; largest identical block {out['largest_block']}, "
        f"{out['in_repeated']:,} respondents share an allocation with someone"
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify the name harmonisation")
    ap.add_argument("--write", action="store_true", help="write the derived .sav files")
    args = ap.parse_args()

    if args.check:
        bad = sum(check(w) for w in WAVES)
        if bad:
            raise SystemExit(f"{bad} name disagreements")

    for w in WAVES:
        wave = WAVES[w][0]
        df, labels = derive(w)
        answered = int(sum((df[f"vign{i}"] >= 0).sum() for i in (1, 2, 3)))
        print(f"wave {wave}: {len(df):,} respondents, {answered:,} descriptions rated")
        if args.write:
            narrow = df.copy()
            for col in narrow.columns:
                if narrow[col].dtype == "object" or str(narrow[col].dtype).startswith("string"):
                    narrow[col] = narrow[col].astype(object).where(narrow[col].notna(), np.nan)
            path = OUT / derived_name(wave)
            pyreadstat.write_sav(narrow, str(path), variable_value_labels=labels)
            print(f"  wrote {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
