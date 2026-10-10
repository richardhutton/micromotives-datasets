"""Independent re-derivation (run: uv run python scripts/verify_gyrp9.py) of every
gyrp9 row, both experiments (gyrp9_send, gyrp9_return), from the .sav.

Reads the BUILT parquets; does not import the recipes. The design table and every
condition / outcome string below are written from the fielded CATI questionnaire
(data/raw/gyrp9/quex/TESS03_production_group_2q.txt, the Houser module, which is
identical in production groups 2-5), with curly apostrophes straightened. Each
paragraph constant is also asserted to occur in that questionnaire. The only words
here that are not the questionnaire's are the narration NARR, which the recipes
add between a respondent's first and second decision.

A second, separate answer key: the deposit's own frequency output
(data/raw/gyrp9/quex/TESS03_Houser_Module.txt, "TESS Production Data Output"). For
every decision variable, the count of each in-range amount it prints must equal the
number of built rows with that response in that cell.
"""

import json
import re
import sys
from collections import Counter

import pandas as pd
import pyreadstat

ROOT = "/Users/richhuton/Workspace/products/micromotives-datasets"
SAV = f"{ROOT}/data/raw/gyrp9/Houser.sav"
QUEX = f"{ROOT}/data/raw/gyrp9/quex/TESS03_production_group_2q.txt"
FREQ = f"{ROOT}/data/raw/gyrp9/quex/TESS03_Houser_Module.txt"

df, meta = pyreadstat.read_sav(SAV)
built = {e: pd.read_parquet(f"{ROOT}/data/processed/gyrp9_{e}.parquet") for e in ("send", "return")}

# ---------------------------------------------------------------- the words
INTRO = [
    "Next, I will ask you about how you might behave in a possible research study.",
    "Suppose you are participating in the study with another person who you do not know "
    "and you will never meet.",
    "Let me describe what will happen and ask your reaction.",
]
BOTH = "YOU BOTH KNOW THE FOLLOWING:"
GIVES50 = "A research organization gives both of you $50."
# trust game, first mover (houx1a / houx2a)
SEND_TASK = (
    "Your task is to decide how much money you will give to the other person. You can give "
    "any amount from $0 to $50 to the other person and keep the rest for yourself."
)
TRIPLED = (
    "At the same time, whatever amount you give will be tripled by the organization before "
    "the other person receives it. So, for example, if you give $20, the other person "
    "actually receives three times $20, or $60."
)
RETURN_RULES = [  # houx1b, and houx2c after its first line
    "The other person, after receiving the money, can send back any amount to you between "
    "$0 and TRIPLE THE AMOUNT YOU SENT.",
    "You can keep whatever amount you receive from the other person IN ADDITION TO ANY MONEY "
    "YOU ORIGINALLY CHOSE NOT TO SEND.",
    "The other person gets whatever they chose not to send you, PLUS THEIR ORIGINAL $50.",
]
KEEP_TRIPLED = "The other person can keep the tripled amount you send to her or him."
NOT_BACK = (
    "Next, let's consider another situation. Imagine the same study I just described except "
    "that THE OTHER PERSON ISN'T GIVEN AN OPPORTUNITY TO SEND MONEY BACK."
)
IS_BACK = (
    "Next, let's consider another situation. Imagine the same study I just described except "
    "that THE OTHER PERSON IS GIVEN AN OPPORTUNITY TO SEND MONEY BACK."
)
# trust game, second mover (houx3a/b ...)
OTHER_SENDS = [
    "The other person can choose to keep any amount from $0 to $50, and send the rest to you.",
    "Whatever amount is sent to you will be tripled by the organization before you receive "
    "it. So, for example, if the other person sends you $20, you actually receive three "
    "times $20, or $60.",
]
GIVE_BACK_TASK = (
    "Your task is to decide how much money you will give back to the other person. After "
    "receiving the money, you can send back any amount between $0 and the tripled amount you "
    "received."
)
AFTER_RECEIVING = (
    "After receiving the money, you can send back any amount between $0 and the tripled "
    "amount you received."
)
KEEP_50 = "You can keep whatever amount you chose not to send PLUS YOUR ORIGINAL $50."
NEXT_BOTH = "Next, let's consider another situation. YOU BOTH KNOW THE FOLLOWING:"
KEEP_SEND = "The other person can keep whatever amount you send to her or him."

# dictator-equivalent screens, by amount sent in the trust game (houx3d/5d/7d; 4a/6a/8a)
DICT_SECOND = {
    10: [
        "Next, let's consider another situation. Imagine the same study I just described "
        "except that THE OTHER PERSON IS INITIALLY GIVEN $40 AND YOU ARE INITIALLY GIVEN $50.",
        "You THEN RECEIVE AN ADDITIONAL $30. You can choose to keep any amount OF THIS MONEY "
        "from $0 to $30 and send the rest to the other person.",
        KEEP_SEND,
    ],
    30: [
        "Next, let's consider another situation. Imagine the same study I just described "
        "except that THE OTHER PERSON IS INITIALLY GIVEN $20 AND YOU ARE INITIALLY GIVEN $50.",
        "You THEN RECEIVE AN ADDITIONAL $90. You can choose to keep any amount from $0 to $90 "
        "and send the rest to the other person.",
        KEEP_SEND,
    ],
    50: [
        "Next, let's consider another situation. Imagine the same study I just described "
        "except that THE OTHER PERSON IS INITIALLY GIVEN NO MONEY AND YOU ARE INITIALLY GIVEN "
        "$50.",
        "You then receive an additional $150. You can choose to keep any amount of this money "
        "from $0 to $150 and send the rest to the other person.",
        KEEP_SEND,
    ],
}
DICT_FIRST = {
    10: [
        "A research organization initially gives the other person $40 and you $50.",
        "You then receive an additional $30 and must decide how much of this amount you will "
        "give to the other person. You can give any amount from $0 to $30 to the other person "
        "and keep the rest for yourself.",
        "So, for example, you could keep $18 and send $12.",
        "The other person can keep whatever amount you send to her or him PLUS THEIR ORIGINAL $40.",
    ],
    30: [
        "A research organization initially gives the other person $20 and you $50.",
        "You then receive an additional $90 and must decide how much of this amount you will "
        "give to the other person. You can give any amount from $0 to $90 to the other person "
        "and keep the rest for yourself.",
        "So, for example, you could keep $54 and send $36.",
        "The other person can keep whatever amount you send to her or him PLUS THEIR ORIGINAL $20.",
    ],
    50: [
        "A research organization initially gives the other person no money and you $50.",
        "You then receive an additional $150 and must decide how much of this amount you will "
        "give to the other person. You can give any amount from $0 to $150 to the other person "
        "and keep the rest for yourself.",
        "So, for example, you could keep $90 and send $60.",
        KEEP_SEND,
    ],
}


def ask(top: int) -> str:
    return f"What amount of money between $0 and ${top} would you send to the other person?"


def under(top: int) -> str:
    return f"Under those conditions, what amount of money between $0 and ${top} would you send to the other person?"


def suppose(sent: int) -> str:
    return f"Suppose the other person sends ${sent} so you receive ${3 * sent}."


NARR = 'You were asked: "{}"'  # ADDED by the recipes; the quoted question is Q's


def j(ps: list[str]) -> str:
    return "\n\n".join(ps)


# ------------------------------------------------------- the design table
# HOU_COND -> (experiment, condition_num, {task: (var, condition, question)}, top, factors)
# task 0 = trust game decision, task 1 = dictator game decision.
DESIGN: dict[int, tuple] = {}
t1 = [*INTRO, BOTH, GIVES50, SEND_TASK, TRIPLED, *RETURN_RULES]
DESIGN[1] = (
    "send",
    0,
    {
        0: ("HOUX1C", j(t1), ask(50)),
        1: ("HOUX1D", j([*t1, NARR.format(ask(50)), NOT_BACK]), under(50)),
    },
    50,
    {"game_order": "trust game first"},
)
d2 = [*INTRO, BOTH, GIVES50, SEND_TASK, TRIPLED, KEEP_TRIPLED]
DESIGN[2] = (
    "send",
    1,
    {
        1: ("HOUX2B", j(d2), ask(50)),
        0: ("HOUX2D", j([*d2, NARR.format(ask(50)), IS_BACK, *RETURN_RULES]), under(50)),
    },
    50,
    {"game_order": "dictator game first"},
)
for cond, sent in ((3, 10), (5, 30), (7, 50)):  # trust (second mover) first
    top = 3 * sent
    # houx3b opens "Your task is to decide ... give back"; houx5b and houx7b open
    # "After receiving the money", as do the second-position screens houx4d/6d/8d.
    back = GIVE_BACK_TASK if cond == 3 else AFTER_RECEIVING
    first = [*INTRO, BOTH, GIVES50, *OTHER_SENDS, back, KEEP_50, suppose(sent)]
    DESIGN[cond] = (
        "return",
        cond - 3,
        {
            0: (f"HOUX{cond}C", j(first), ask(top)),
            1: (f"HOUX{cond}E", j(first + [NARR.format(ask(top))] + DICT_SECOND[sent]), under(top)),
        },
        top,
        {"amount_sent": f"${sent} sent, ${top} received", "game_order": "trust game first"},
    )
for cond, sent in ((4, 10), (6, 30), (8, 50)):  # dictator first
    top = 3 * sent
    first = INTRO + [BOTH] + DICT_FIRST[sent]
    second = [NEXT_BOTH, GIVES50, *OTHER_SENDS, AFTER_RECEIVING, KEEP_50, suppose(sent)]
    DESIGN[cond] = (
        "return",
        cond - 3,
        {
            1: (f"HOUX{cond}B", j(first), ask(top)),
            0: (f"HOUX{cond}E", j([*first, NARR.format(ask(top)), *second]), ask(top)),
        },
        top,
        {"amount_sent": f"${sent} sent, ${top} received", "game_order": "dictator game first"},
    )

fail: list[str] = []

# ---------------------------------- every constant is the questionnaire's
with open(QUEX, encoding="utf-8") as fh:
    quex = fh.read()
quex = quex.replace("’", "'").replace("‘", "'")
quex = re.sub(r"[ \t]+", " ", quex)
consts = [
    *INTRO,
    BOTH,
    GIVES50,
    SEND_TASK,
    TRIPLED,
    KEEP_TRIPLED,
    NOT_BACK,
    IS_BACK,
    GIVE_BACK_TASK,
    AFTER_RECEIVING,
    KEEP_50,
    NEXT_BOTH,
    KEEP_SEND,
    *RETURN_RULES,
    *OTHER_SENDS,
]
consts += [p for v in DICT_SECOND.values() for p in v] + [p for v in DICT_FIRST.values() for p in v]
consts += [f(t) for t in (30, 50, 90, 150) for f in (ask, under)] + [
    suppose(s) for s in (10, 30, 50)
]
missing = [c for c in consts if c not in quex]
if missing:
    fail.append(f"{len(missing)} constants not found in the questionnaire: {missing[:2]}")

# ------------------------------------------- design claims, executed
# Read again keeping user-missing codes, so DK/RF (998/999) are not mistaken for
# "never asked".
raw, _ = pyreadstat.read_sav(SAV, user_missing=True)

# (a) HOU_COND is cut from the 1-200 draw HOUX_RAN at Q's stated probabilities.
PROBS = [25, 25, 4.5, 4.5, 8, 8, 12.5, 12.5]  # Q: "Condition 1: 25%" ... "Condition 8: 12.5%"
upper, edges = 0.0, []
for pct in PROBS:
    upper += pct * 2  # percent of 200
    edges.append(upper)
assert edges[-1] == 200


def cut(draw: float) -> int:
    return next(c for c, hi in enumerate(edges, 1) if draw <= hi)


bad_cut = int((raw["HOUX_RAN"].map(cut) != raw["HOU_COND"]).sum())
if raw["HOUX_RAN"].isna().any() or bad_cut:
    fail.append(f"HOU_COND disagrees with the HOUX_RAN cut points on {bad_cut} respondents")
print(f"HOUX_RAN cut points: {len(raw) - bad_cut:,} of {len(raw):,} respondents agree")

# (b) Skip logic. Q: a comprehension prompt answered 2 ("no/R does not understand")
# or a decision answered 997 ends the module ("GOTO hou1_int"); DK/RF on a decision
# do not. Screens in Q's order per condition; no respondent answers a screen of
# another condition.
SCREENS = {
    1: ["HOUX1A", "HOUX1B", "HOUX1C", "HOUX1D"],
    2: ["HOUX2A", "HOUX2B", "HOUX2C", "HOUX2D"],
    3: ["HOUX3A", "HOUX3B", "HOUX3C", "HOUX3E"],
    4: ["HOUX4A", "HOUX4B", "HOUX4C", "HOUX4D", "HOUX4E"],
    5: ["HOUX5A", "HOUX5B", "HOUX5C", "HOUX5E"],
    6: ["HOUX6A", "HOUX6B", "HOUX6C", "HOUX6D", "HOUX6E"],
    7: ["HOUX7A", "HOUX7B", "HOUX7C", "HOUX7E"],
    8: ["HOUX8A", "HOUX8B", "HOUX8C", "HOUX8D", "HOUX8E"],
}
ALL = {v for vs in SCREENS.values() for v in vs}
DECISIONS = {var for d in DESIGN.values() for var, _, _ in d[2].values()}
assert len(DECISIONS) == 16
PROMPTS = ALL - DECISIONS  # "Do you understand so far?" / "Do you still follow me?"
skip_bad = Counter()
for _, r in raw.iterrows():
    seq = SCREENS[int(r["HOU_COND"])]
    if any(pd.notna(r[v]) for v in ALL - set(seq)):
        skip_bad["answered another condition's screen"] += 1
    ended = False
    for v in seq:
        val = r[v]
        if ended and pd.notna(val):
            skip_bad["answered after the module ended"] += 1
        if pd.isna(val):
            ended = True  # never reached: nothing after it may be answered either
        elif (v in PROMPTS and val == 2) or (v not in PROMPTS and val == 997):
            ended = True
    # first screen is asked of everyone assigned
    if pd.isna(r[seq[0]]):
        skip_bad["first screen not asked"] += 1
if skip_bad:
    fail.append(f"skip logic: {dict(skip_bad)}")
print(f"skip logic: {dict(skip_bad) or 'no violation'} over {len(raw):,} respondents")


# (c) Persona, from the .sav codes and Q's labels (with the recipes' rewrites
# written out here, not read from them).
GENDER = {1: "Male", 2: "Female"}
PARTY = {1: "a Republican", 2: "a Democrat", 3: "an Independent", 7: "no preference"}
IDEOL = {
    1: "a liberal",
    2: "a conservative",
    3: "a moderate",
    4: "Haven't thought much about it",
    7: "neither/none",
}


def persona_expected(idx: int) -> dict:
    r = raw.loc[idx]

    def look(table: dict, v: float) -> str | None:
        return None if pd.isna(v) else table.get(int(v))

    born = r["BORN"]
    return {
        "gender": look(GENDER, r["GENDER"]),
        "party_id": look(PARTY, r["PARTY_A"]),
        "ideology": look(IDEOL, r["IDEOL_A"]),
        "year_of_birth": None if pd.isna(born) or born >= 9998 else str(int(born)),
    }


# ---------------------------------------------------------- expected rows
expected: dict[str, dict[tuple, tuple]] = {"send": {}, "return": {}}
for i, r in df.iterrows():
    exp, num, items, top, _ = DESIGN[int(r["HOU_COND"])]
    for task, (var, cond_text, q) in items.items():
        v = r[var]
        if pd.isna(v) or v != int(v) or not 0 <= v <= top:  # 997 / 999 / out of range
            continue
        expected[exp][(f"gyrp9:{i}", task)] = (
            num,
            int(v),
            cond_text,
            f"{q} Only return an integer from 0 to {top}, nothing else.",
        )

for exp, b in built.items():
    got = {(r.participant_id, int(r.task_num)): r for r in b.itertuples()}
    exp_keys, got_keys = set(expected[exp]), set(got)
    miss, extra = exp_keys - got_keys, got_keys - exp_keys
    wrong = Counter()
    for k in exp_keys & got_keys:
        num, resp, cond_text, outcome = expected[exp][k]
        r = got[k]
        if int(r.condition_num) != num:
            wrong["condition_num"] += 1
        if int(r.response_num) != resp or r.response != str(resp):
            wrong["response"] += 1
        if r.condition != cond_text:
            wrong["condition text"] += 1
        if r.outcome != outcome:
            wrong["outcome text"] += 1
        arm = DESIGN[next(c for c, d in DESIGN.items() if d[0] == exp and d[1] == num)]
        if dict(r.factors) != arm[4]:
            wrong["factors"] += 1
        idx = int(k[0].split(":")[1])
        p = json.loads(r.persona) if isinstance(r.persona, str) else r.persona
        for field, want in persona_expected(idx).items():
            got_v = p.get("extra", {}).get(field) if field == "year_of_birth" else p.get(field)
            if got_v != want:
                wrong[f"persona {field}"] += 1
    print(
        f"gyrp9_{exp}: expected {len(exp_keys):,}, built {len(got_keys):,}, missing {len(miss)}, "
        f"extra {len(extra)}, wrong {dict(wrong) or 0}"
    )
    if miss or extra or wrong or len(b) != len(got):
        fail.append(
            f"{exp}: missing {len(miss)} extra {len(extra)} wrong {dict(wrong)} dup {len(b) - len(got)}"
        )
    # one condition string per (arm, task), one outcome string per (arm, task)
    n = b.groupby(["condition_num", "task_num"]).agg({"condition": "nunique", "outcome": "nunique"})
    if (n.values != 1).any():
        fail.append(f"{exp}: a cell carries more than one condition/outcome string")

# ------------------------------------- answer key 2: the deposit's frequencies
with open(FREQ, encoding="utf-8") as fh:
    freq_txt = fh.read()
for exp, num, items, top, _ in DESIGN.values():
    for task, (var, _, _) in items.items():
        m = re.search(rf"\n{var.lower()}\s*\n(.*?)\n\s*-+\s*\n", freq_txt, re.S)
        if not m:
            fail.append(f"{var}: no frequency table")
            continue
        printed = {}
        for line in m.group(1).split("\n"):
            mm = re.match(r"^\s+(?:[\d.]+\s+)?(\d+)\s+(\d+)\s*$", line)
            if mm and 0 <= int(mm.group(2)) <= top:
                printed[int(mm.group(2))] = int(mm.group(1))
        printed = {k: v for k, v in printed.items() if v}
        b = built[exp]
        cell = b[(b.condition_num == num) & (b.task_num == task)]
        mine = Counter(int(x) for x in cell.response_num)
        if printed != dict(mine):
            fail.append(f"{var}: frequency output {printed} != built {dict(mine)}")
print("frequency output checked for", sum(len(d[2]) for d in DESIGN.values()), "decision variables")

if fail:
    print("FAIL")
    for f in fail:
        print("  ", f)
    sys.exit(1)
print("OK")
