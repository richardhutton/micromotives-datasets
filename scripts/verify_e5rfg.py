"""Independent re-derivation (run: uv run python scripts/verify_e5rfg.py)  of every e5rfg row from the .sav, plus Rabin &
Weizsaecker Table 4 check. Reads the BUILT parquets; does not import the recipe."""

import json
import sys

import pandas as pd
import pyreadstat

ROOT = "/Users/richhuton/Workspace/products/micromotives-datasets"
df, meta = pyreadstat.read_sav(f"{ROOT}/data/raw/e5rfg/TESS56_client.sav")

# Design as read from the questionnaire, written down here independently of the
# generator: module -> {var: (lo, hi)}; experiment -> modules.
CHOICE2 = (1, 2)
CHOICE4 = (1, 4)
DESIGN = {
    "tk": {1: {"M1D1": CHOICE2, "M1D2": CHOICE2}, 2: {"M2D1": CHOICE4}},
    "ce": {3: {"M3D1": (0, 1000), "M3D2": (0, 1000)}, 4: {"M4D1": (0, 1000)}},
    "pair": {5: {"M5D1": CHOICE2, "M5D2": CHOICE2}, 6: {"M6D1": CHOICE4}},
    "six": {
        7: {
            "M7D1": CHOICE2,
            "M7D2": CHOICE2,
            "M7D3": CHOICE4,
            "M7D4": (100, 1600),
            "M7D5": (850, 2350),
        },
        8: {
            "M8D1": CHOICE2,
            "M8D2": CHOICE2,
            "M8D3": (500, 1500),
            "M8D4": (500, 1500),
            "M8D6": CHOICE2,
        },
        9: {"M9D1": CHOICE2, "M9D2": CHOICE2, "M9D3": (850, 2350), "M9D6": (1000, 2000)},
        10: {
            "M10D1": CHOICE2,
            "M10D2": CHOICE4,
            "M10D3": (0, 1000),
            "M10D4": (0, 1000),
            "M10D5": (1500, 2500),
            "M10D6": CHOICE2,
        },
    },
}
FIRST_MODULE = {"tk": 1, "ce": 3, "pair": 5, "six": 7}

total_bad = 0
built_all = {}
for exp, mods in DESIGN.items():
    b = pd.read_parquet(f"{ROOT}/data/processed/e5rfg_{exp}.parquet")
    built_all[exp] = b
    # task_num -> var, from outcome order as declared in the design dict
    vars_in_order = [v for m in mods for v in mods[m]]
    expected = set()
    for idx, r in df.iterrows():
        m = int(r.MODULE)
        if m not in mods:
            continue
        for v, (lo, hi) in mods[m].items():
            x = r[v]
            if pd.isna(x) or x < 0:
                continue
            assert lo <= x <= hi and float(x).is_integer(), (v, x)
            expected.add((f"e5rfg:{idx}", vars_in_order.index(v), m - FIRST_MODULE[exp], int(x)))
    got = set(
        zip(b.participant_id, b.task_num, b.condition_num, b.response_num.astype(int), strict=True)
    )
    missing, extra = expected - got, got - expected
    # Persona spot-check: age and gender against the .sav for every row.
    pid = b.participant_id.str.split(":").str[1].astype(int)
    p = b.persona.map(json.loads)
    age_bad = int((p.map(lambda d: d["age"]).values != df.loc[pid, "PPAGE"].values).sum())
    gmap = {1.0: "Male", 2.0: "Female"}
    g_bad = int(
        (p.map(lambda d: d["gender"]).values != df.loc[pid, "PPGENDER"].map(gmap).values).sum()
    )
    # One condition string per (condition_num, task) and one outcome string per task.
    cpt = b.groupby(["condition_num", "task_num"]).condition.nunique().max()
    opt = b.groupby("task_num").outcome.nunique().max()
    # No bracketed programmer directive or blank line left in text.
    brk = int(
        b.condition.str.contains(r"\[|\]|_{3,}").sum()
        + b.outcome.str.contains(r"\[|\]|_{3,}").sum()
    )
    print(
        f"{exp}: rows {len(b)} expected {len(expected)} missing {len(missing)} extra {len(extra)} "
        f"age_bad {age_bad} gender_bad {g_bad} cond/cell {cpt} outcome/task {opt} brackets {brk} dup {len(b) - len(got)}"
    )
    total_bad += (
        len(missing)
        + len(extra)
        + age_bad
        + g_bad
        + brk
        + (len(b) - len(got))
        + (cpt != 1)
        + (opt != 1)
    )

# Table 4 is computed from the BUILT rows, not the deposit: rebuild a wide frame.
recs = {}
for exp, mods in DESIGN.items():
    vars_in_order = [v for m in mods for v in mods[m]]
    for r in built_all[exp].itertuples():
        d = recs.setdefault(r.participant_id, {})
        d["MODULE"] = r.condition_num + FIRST_MODULE[exp]
        d[vars_in_order[r.task_num]] = r.response_num
df = pd.DataFrame.from_dict(recs, orient="index")


# Table 4 of Rabin & Weizsaecker (combos A&C, A&D, B&C, B&D; N).
def combos(m, d1, d2):
    s = df[df["MODULE"].eq(m)][[d1, d2]].dropna()
    n = len(s)
    a = s[d1] == 1
    c = s[d2] == 1
    return n, [
        round(x / n, 2) for x in ((a & c).sum(), (a & ~c).sum(), (~a & c).sum(), (~a & ~c).sum())
    ]


def broad(m, v, order):
    s = df[df["MODULE"].eq(m)][v].dropna()
    n = len(s)
    return n, [round((s == k).sum() / n, 2) for k in order]


TABLE4 = {
    "T1 Ex1": ((88, [0.16, 0.66, 0.03, 0.15]), combos(1, "M1D1", "M1D2")),
    # broad options: code 1 = A&D, 2 = A&C, 3 = B&C, 4 = B&D
    "T2 Ex1 broad": ((86, [0.22, 0.06, 0.24, 0.48]), broad(2, "M2D1", [2, 1, 3, 4])),
    "T5 Ex2": ((107, [0.24, 0.53, 0.05, 0.19]), combos(5, "M5D1", "M5D2")),
    # M6D1: 1 = 50% -1000/0 (A&D), 2 = -500 (A&C), 3 = 50% -1000/+100 (B&C), 4 = 4-outcome (B&D)
    # REF's printed values. Ours have A&C and B&C transposed; see KNOWN below.
    "T6 Ex2 broad": ((108, [0.09, 0.38, 0.12, 0.41]), broad(6, "M6D1", [2, 1, 3, 4])),
    "T7 Ex2": ((None, [0.22, 0.53, 0.05, 0.20]), combos(7, "M7D1", "M7D2")),
    # M7D3: 1 = -700/+950 (A&D), 2 = +200 (A&C), 3 = -550/+950 (B&C), 4 = 4-outcome (B&D)
    "T7 Ex4 broad": ((None, [0.72, 0.04, 0.13, 0.12]), broad(7, "M7D3", [2, 1, 3, 4])),
    # Ex2 in T8: A = M8D6 code1, C = M8D1 code1 (losing $500)
    "T8 Ex2 separate": ((None, [0.26, 0.44, 0.07, 0.23]), combos(8, "M8D6", "M8D1")),
    # Ex3: A = M8D2 code1 (winning $1500), C = M8D1 code1
    "T8 Ex3": ((None, [0.23, 0.50, 0.10, 0.17]), combos(8, "M8D2", "M8D1")),
    "T9 Ex4": ((179, [0.35, 0.36, 0.16, 0.13]), combos(9, "M9D1", "M9D2")),
    # M10D2 same options as M6D1
    "T10 Ex2 broad": ((None, [0.15, 0.24, 0.24, 0.36]), broad(10, "M10D2", [2, 1, 3, 4])),
    "T10 Ex4 separate": ((None, [0.33, 0.43, 0.10, 0.14]), combos(10, "M10D1", "M10D6")),
}
# KNOWN differences, asserted explicitly rather than absorbed by a tolerance: the
# rows whose cells must match REF only after swapping the given positions. T6
# (M6D1): REF prints A&C 0.09 / B&C 0.12, ours are 0.12 / 0.09. M10D2 has the same
# four options and labels and matches REF under the same code mapping, so a
# transposition in REF is the likelier cause; a 2/3 code swap in the deposit
# cannot be ruled out from the source.
KNOWN = {"T6 Ex2 broad": (0, 2)}


def close(pv, v):
    return max(abs(a - b) for a, b in zip(pv, v, strict=True)) <= 0.011


t4_bad = 0
known_seen = 0
for k, ((pn, pv), (n, v)) in TABLE4.items():
    n_ok = pn is None or pn == n
    if k in KNOWN:
        i, j = KNOWN[k]
        swapped = list(pv)
        swapped[i], swapped[j] = swapped[j], swapped[i]
        # The known difference must still be there (direct comparison fails) and
        # must be exactly the declared transposition (swapped comparison passes).
        ok = n_ok and not close(pv, v) and close(swapped, v)
        known_seen += ok
        status = f"KNOWN DIFFERENCE (REF transposition, cells {i}/{j})" if ok else "MISMATCH"
    else:
        ok = n_ok and close(pv, v)
        status = "ok" if ok else "MISMATCH"
    t4_bad += not ok
    print(f"  {k:18s} paper N={pn} {pv}  ours N={n} {v}  {status}")
print(
    "TOTAL row defects:",
    total_bad,
    " Table 4 mismatches:",
    t4_bad,
    " known paper differences:",
    known_seen,
    "of",
    len(KNOWN),
)

# Appendix Tables 8.1/8.2 (IZA DP 3040): % at min, mean NCE, % at EV, % at max.
# Gains: NCE = CE - EV. Losses (stated amount L willing to lose): NCE = L - |EV|.
CE = [  # var, lo, hi, loss?, paper row (min, nce, rn, max) or rows to choose from
    ("M3D1", 0, 1000, False),
    ("M4D1", 0, 1000, False),
    ("M10D3", 0, 1000, False),
    ("M3D2", 0, 1000, True),
    ("M10D4", 0, 1000, True),
    ("M8D4", 500, 1500, True),
    ("M8D3", 500, 1500, False),
    ("M9D6", 1000, 2000, False),
    ("M10D5", 1500, 2500, False),
    ("M7D4", 100, 1600, False),
    ("M7D5", 850, 2350, False),
    ("M9D3", 850, 2350, False),
]
for v, lo, hi, loss in CE:
    s = df[v].dropna()
    ev = (lo + hi) / 2
    nce = (s - ev) if not loss else (ev - s)  # paper reports losses sign-flipped, min/max swapped
    print(
        f"  {v:6s} n={len(s)} %min={(s == lo).mean():.2f} meanNCE={nce.mean():.2f} %EV={(s == ev).mean():.2f} %max={(s == hi).mean():.2f}"
    )

sys.exit(1 if total_bad or t4_bad else 0)
