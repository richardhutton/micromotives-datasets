"""Independent re-derivation (run: uv run python scripts/verify_7tzpe.py) of every 7tzpe row
from the .sav. Reads the BUILT parquet; does not import the recipe.

The cell table below is written from the fielded questionnaire's design table
(Q lines 50-151), not from the recipe. The condition text is checked against
fragments of Q's vignette wording and the full disease-card text (CARD), not
against the recipe's strings.
"""

import json
import sys

import pandas as pd
import pyreadstat

ROOT = "/Users/richhuton/Workspace/products/micromotives-datasets"
df, meta = pyreadstat.read_sav(f"{ROOT}/data/raw/7tzpe/TESS3_156_Powroznik_Client.sav")
built = pd.read_parquet(f"{ROOT}/data/processed/7tzpe.parquet")

# group -> (disease, race, gender, weight), Q 56-151
CELLS = {}
for g in range(1, 17):
    disease = "diabetes" if g <= 8 else "lymphoma"
    k = (g - 1) % 8
    race = "white" if k in (0, 1, 4, 5) else "african_american"
    gender = "female" if k < 4 else "male"
    weight = "obese" if g % 2 == 1 else "normal"
    CELLS[g] = (disease, race, gender, weight)

# The disease cards. In the questionnaire they are IMAGES, not text:
# word/media/image2.png (diabetes) and word/media/image3.png (lymphoma) inside
# data/raw/7tzpe/quex/TESS3_156_Powroznik_Final_Questionnaire.docx
# (sha256 3558ab17eadaba45cfe7515b89a540f5aac55377dd3a72aff75aabc8b4bfbdc5).
# Transcribed from those PNGs, one line per card field, title first.
CARD = {
    "diabetes": "\n".join(
        [
            "Type II Diabetes",
            "Condition/Disease: Type II Diabetes Mellitus",
            "Diagnosis: Fasting plasma glucose level \u22657.0 mmol/l (126 mg/dl); "
            "Plasma \u2265 11.1 mmol/l (200 mg/dL) 2 hours after a glucose tolerance test",
            "Symptoms: Frequent urination; increased thirst and hunger; blurred vision",
            "Precondition: Impaired glucose tolerance or impaired fasting glucose",
            "Complications: Diabetes is a risk factor for stroke, cardiovascular disease, "
            "neuropathy, and kidney failure",
        ]
    ),
    "lymphoma": "\n".join(
        [
            "Non-Hodgkin Lymphoma",
            "Condition/Disease: Non-Hodgkin Lymphoma",
            "Classification of a variety of blood cancers",
            "Description: Overproduction of abnormal lymphocytes (white blood cells)",
            "Symptoms: Swollen lymph nodes; abdominal pain or swelling; fatigue; "
            "fever/night sweats; chest pains",
            "Diagnosis: Examination of lymph nodes; Imaging tests: x-ray, CT scan, MRI scan, "
            "or ultrasound; Biopsy of lymph node tissue or bone marrow",
        ]
    ),
}

# var -> valid range
OUTCOMES = {"Q10": (1, 2)}
for v in ["Q11_Environment", "Q11_Lifestyle", "Q11_Genetics", "Q11_BadLuck"]:
    OUTCOMES[v] = (0, 100)
for i in range(12, 22):
    OUTCOMES[f"Q{i}"] = (1, 5)
TASK = {v: i for i, v in enumerate(OUTCOMES)}

expected = {}
for idx, r in df.iterrows():
    g = int(r["XTESS156"])
    for v, (lo, hi) in OUTCOMES.items():
        x = r[v]
        if pd.isna(x) or x < 0:
            continue
        assert lo <= x <= hi and x == int(x), (idx, v, x)
        expected[(f"7tzpe:{idx}", TASK[v])] = (g - 1, int(x))

got = {}
for r in built.itertuples():
    key = (r.participant_id, r.task_num)
    assert key not in got, key
    got[key] = (r.condition_num, int(r.response_num))
    assert r.response == str(int(r.response_num))

missing = set(expected) - set(got)
extra = set(got) - set(expected)
wrong = [k for k in set(expected) & set(got) if expected[k] != got[k]]
print(
    f"expected {len(expected)}  built {len(got)}  missing {len(missing)}  extra {len(extra)}  wrong {len(wrong)}"
)

# Condition text against the cell table, by fragments of Q's own wording.
bad_text = 0
for (cnum,), sub in built.groupby(["condition_num"]):
    texts = sub["condition"].unique()
    assert len(texts) == 1, cnum
    t = texts[0]
    disease, race, gender, weight = CELLS[cnum + 1]
    checks = [
        ("diagnosed with type II diabetes" in t) == (disease == "diabetes"),
        ("diagnosed with non-Hodgkin Lymphoma" in t) == (disease == "lymphoma"),
        ("34-year old African American" in t) == (race == "african_american"),
        ("34-year old white" in t) == (race == "white"),
        (" female." in t) == (gender == "female"),
        (" male." in t) == (gender == "male"),
        ("the patient is moderately obese" in t) == (weight == "obese"),
        ("the patient is of normal weight" in t) == (weight == "normal"),
        ("205lbs" in t or "240lbs" in t) == (weight == "obese"),
        ("5'5\"" in t) == (gender == "female"),
        t.startswith("Instructions: In this study"),
        # the whole card, as its own paragraph, for this arm's disease only
        f"\n\n{CARD[disease]}\n\n" in t,
        all(CARD[d] not in t for d in CARD if d != disease),
        "[" not in t and "]" not in t,
    ]
    if not all(checks):
        bad_text += 1
        print("BAD TEXT", cnum, checks)
print(f"condition strings checked: 16, bad {bad_text}")

# One outcome string per task.
per_task = built.groupby("task_num")["outcome"].nunique()
assert (per_task == 1).all(), per_task

# Persona age/gender match the .sav on every row.
idx = built["participant_id"].str.split(":").str[1].astype(int)
p = built["persona"].map(json.loads)
age_ok = (p.map(lambda d: d["age"]).values == df.loc[idx, "PPAGE"].values).all()
gmap = {1.0: "Male", 2.0: "Female"}
g_ok = (p.map(lambda d: d["gender"]).values == df.loc[idx, "PPGENDER"].map(gmap).values).all()
print(f"persona age match {age_ok}  gender match {g_ok}")

# Direction sanity check against the TESS abstract (NOT an answer key): obese
# patients blamed more (Q12, Q13), less sympathy (Q14), more support for
# penalties (Q20), more often 'under the patient's control' (Q10 code 1).
# Computed from the BUILT rows; part of pass/fail.
built["obese"] = built["condition_num"].map(lambda c: CELLS[c + 1][3] == "obese")
# Direction only (no magnitude): +1 = obese higher, -1 = obese lower.
DIRECTION = {"Q12": 1, "Q13": 1, "Q14": -1, "Q20": 1}
direction_ok = True
for v, sign in DIRECTION.items():
    s = built[built.task_num == TASK[v]].groupby("obese")["response_num"].mean()
    print(f"{v}: normal {s[False]:.3f}  obese {s[True]:.3f}")
    direction_ok = direction_ok and sign * (s[True] - s[False]) > 0
s = (
    built[built.task_num == TASK["Q10"]]
    .groupby("obese")["response_num"]
    .apply(lambda x: (x == 1).mean())
)
print(f"Q10 share 'under patient's control': normal {s[False]:.3f}  obese {s[True]:.3f}")
q10_dir = s[True] > s[False]
direction_ok = bool(direction_ok and q10_dir)
print(f"direction as in the abstract: {direction_ok}")

ok = not (missing or extra or wrong or bad_text) and age_ok and g_ok and direction_ok
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
