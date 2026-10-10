"""Independent re-derivation (run: uv run python scripts/verify_vwn96.py) of every vwn96 row.

Reads the BUILT parquet and the deposit's CORRECTED .sav (not the derived file
the build reads, and not the recipe or its generator). The questionnaire
strings below are typed from the fielded questionnaire
(data/raw/vwn96/quex/TESS3 134 Johnston_TESS3 137 Yeager Survey.docx, sha256
99ded46deccc05d63bb7866915ddef16d266fbcda354084fca97b7aa18db849e; .txt lines
cited), with typography normalised (straight quotes, hyphen for the en dash,
single spaces). Every row's condition and outcome text is rebuilt from them and
compared whole.
"""

import json
import sys

import pandas as pd
import pyreadstat

ROOT = "/Users/richhuton/Workspace/products/micromotives-datasets"
df, meta = pyreadstat.read_sav(f"{ROOT}/data/raw/vwn96/Yeager-correcteddata.sav")
built = pd.read_parquet(f"{ROOT}/data/processed/vwn96.parquet")

# --- questionnaire strings (Q line numbers) -----------------------------------
INTRO = (  # Q 101
    "On the next screen, you'll read a brief story about a student. When reading it, imagine "
    "you were a teacher. Then say what you would be most likely to do in the situation."
)
POOR = (  # Q 107 (= Q 207)
    "Imagine a student from a poor family who attends a public high school located in the "
    "inner-city. You hear the student say \"I don't want to do this assignment any more. I "
    "don't see the point. I'm giving up.\""
)
WEALTHY = (  # Q 139 (= Q 175)
    "Imagine a student from a moderately wealthy family who attends a public high school located "
    "in a suburban neighborhood. You hear the student say \"I don't want to do this assignment "
    "any more. I don't see the point. I'm giving up.\""
)
TEACHER = "Imagine you were this student's teacher and wanted to motivate the student."  # Q 109
SECOND = (  # Q 169
    "Now please read a story about a second student. Again, imagine you were a teacher and say "
    "what you would be most likely to do."
)
STEM = {  # Q 111 (first student) and Q 179 (second student)
    0: "Please read each statement below. Then select the statement that best describes what "
    "you would be MOST likely to do. There are no right or wrong answers - just provide your "
    "honest opinion.",
    1: "Please read each statement below. Then select the statement that best describes what "
    "you would be MOST LIKELY to do. There are no right or wrong answers - just provide your "
    "honest opinion.",
}
STATEMENT = {  # Q 112-115, codes 1-4
    1: "Mention that they need to do the work if they want to earn a lot of money in a good job "
    "one day.",
    2: "Mention that their family is counting on them to do the work, graduate and go to college.",
    3: "Mention how the assignment could be related to their personal interests, like sports or "
    "music.",
    4: "Mention that if they really learn from the assignment, they may be able to help people by "
    "using that knowledge one day.",
}
# Words the recipe adds (its notes record them word-for-word).
LISTED = "The statements were listed in this order:"
ASKED = (
    "You were asked to select, from the statements listed below, the statement that best "
    "describes what you would be MOST likely to do; then, of the remaining statements, the one "
    "you would be MOST LIKELY to do; then, of the last two statements, the one you would be "
    "MORE LIKELY to do."
)

# --- design, from Q's routing (Q 104, 136, 172, 204) ---------------------------
# XTESS137 -> (condition_num, first vignette, second vignette, first var, second var,
#              order prefix, (a, b) vars that gate the second-student narration)
DESIGN = {
    1: (0, POOR, WEALTHY, "Q1A", "Q3A", "Order_Q1_Q3_", ("Q1A", "Q1B")),
    2: (1, WEALTHY, POOR, "Q2A", "Q4A", "Order_Q2_Q4_", ("Q2A", "Q2B")),
}
VALID = {1, 2, 3, 4}


def order_of(r: pd.Series, prefix: str) -> list[int]:
    """Statement codes in on-screen order. Order_*_k = the slot statement k was shown in.

    Arm 1's deposit lacks Order_Q1_Q3_1; statement 1 takes the slot left over.
    """
    slot = {}
    for k in range(1, 5):
        col = f"{prefix}{k}"
        if col in r.index and not pd.isna(r[col]):
            slot[k] = int(r[col])
    missing = [k for k in range(1, 5) if k not in slot]
    assert len(missing) <= 1, (r["CaseID"], slot)
    if missing:
        (left,) = set(range(1, 5)) - set(slot.values())
        slot[missing[0]] = left
    assert sorted(slot.values()) == [1, 2, 3, 4], (r["CaseID"], slot)
    return [k for k, _ in sorted(slot.items(), key=lambda kv: kv[1])]


def condition(first: str, second: str | None, order: list[int]) -> str:
    paras = [INTRO, first, TEACHER]
    if second is not None:
        paras += [ASKED, SECOND, second, TEACHER]
    paras.append(LISTED + "\n" + "\n".join(f"• {STATEMENT[k]}" for k in order))
    return "\n\n".join(paras)


KEY = "; ".join(f'{k} means "{STATEMENT[k]}"' for k in range(1, 5))
INSTR = "Only return one of 1, 2, 3 or 4, nothing else."


def outcome(task: int) -> str:
    return f"{STEM[task]}\n{KEY} {INSTR}"


expected = {}
for idx, r in df.iterrows():
    raw = int(r["XTESS137"])
    cnum, first, second, v0, v1, prefix, (ga, gb) = DESIGN[raw]
    order = order_of(r, prefix)
    full_seq = r[ga] in VALID and r[gb] in VALID
    pid = f"vwn96:{idx}"
    if r[v0] in VALID:
        expected[(pid, 0)] = (cnum, int(r[v0]), condition(first, None, order), outcome(0))
    if r[v1] in VALID and full_seq:
        expected[(pid, 1)] = (cnum, int(r[v1]), condition(first, second, order), outcome(1))
    # The other arm's variables must be empty (routing).
    other = DESIGN[3 - raw]
    assert pd.isna(r[other[3]]) and pd.isna(r[other[4]]), (idx, "routed to both arms")

got = {}
for r in built.itertuples():
    key = (r.participant_id, r.task_num)
    assert key not in got, key
    got[key] = (r.condition_num, int(r.response_num), r.condition, r.outcome)
    assert r.response == str(int(r.response_num))

missing = set(expected) - set(got)
extra = set(got) - set(expected)
wrong_cr = [k for k in set(expected) & set(got) if expected[k][:2] != got[k][:2]]
wrong_cond = [k for k in set(expected) & set(got) if expected[k][2] != got[k][2]]
wrong_out = [k for k in set(expected) & set(got) if expected[k][3] != got[k][3]]
print(
    f"expected {len(expected)}  built {len(got)}  missing {len(missing)}  extra {len(extra)}  "
    f"wrong(cond/resp) {len(wrong_cr)}  wrong condition text {len(wrong_cond)}  "
    f"wrong outcome text {len(wrong_out)}"
)
for k in (wrong_cond + wrong_out)[:2]:
    print("EXPECTED:", expected[k][2:], "\nGOT:", got[k][2:])

# Per-(condition, task) counts and first-choice shares, from the BUILT rows.
tab = built.groupby(["condition_num", "task_num"])["response_num"]
print(tab.size().to_dict())
print(
    built.pivot_table(
        index=["condition_num", "task_num"],
        columns="response_num",
        values="participant_id",
        aggfunc="count",
    ).to_string()
)
no_brackets = not built["condition"].str.contains(r"[\[\]]").any()
print(f"no brackets in any condition: {no_brackets}")

# Persona against the .sav on every row.
idx = built["participant_id"].str.split(":").str[1].astype(int)
p = built["persona"].map(json.loads)
age_ok = (p.map(lambda d: d["age"]).values == df.loc[idx, "PPAGE"].values).all()
g_ok = (
    p.map(lambda d: d["gender"]).values
    == df.loc[idx, "PPGENDER"].map({1.0: "Male", 2.0: "Female"}).values
).all()
party_lab = meta.variable_value_labels["PARTY7"]
party_ok = (
    p.map(lambda d: d["party_id"]).values == df.loc[idx, "PARTY7"].map(party_lab).values
).all()
print(f"persona age {age_ok}  gender {g_ok}  party {party_ok}")

ok = (
    not (missing or extra or wrong_cr or wrong_cond or wrong_out)
    and no_brackets
    and age_ok
    and g_ok
    and party_ok
)
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
