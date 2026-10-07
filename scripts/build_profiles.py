"""Build person profiles from the Innovation Panel's own survey answers.

A profile is what a person has told this survey about themselves over the years
they took part — attitudes, personality, trust, risk, wellbeing, politics,
religion — written out as facts with the year attached.

This is the shape Park et al. found works: their survey-only agents (177 GSS
items + the 44-item Big Five) scored 0.82 against a ceiling of 0.86, and their
"interview-summary" agents, which strip the person's way of speaking and keep
only the facts, scored 0.81 against 0.83 for full transcripts. The predictive
content is in the facts, not the voice.

**What is deliberately thrown away.** The first cut of this kept 2,135 answers
for its deepest person and 1,362 of them were health, nearly all unticked boxes
from long condition checklists — "Nervous breakdown: Not mentioned". Those are
not self-report, they are the absence of one, and they drowned the real content.
So: non-answers go, checklist non-selections go, and the health bucket is
capped, because a person who answers 80 condition-screening items has not told
us 80 things about themselves.

**IDs.** `pidp` is never stored. It is the Understanding Society person
identifier and links to the whole study, so each profile is keyed by a hash of
it. The hash is deterministic, so a profile resolves back to its rows locally,
and `_index.json` holds the mapping. Everything here is UKDS-derived and lives
under gitignored `data/profiles/`.

    uv run python build_profiles.py --one      # build one and print it
    uv run python build_profiles.py --n 300    # build 300, deepest first
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import warnings
from collections import defaultdict
from pathlib import Path

import pandas as pd

from micromotives_datasets.sources import spss

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[1]
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"
OUT = REPO / "data" / "profiles"
WAVES = "abcdefghijklmnopq"
YEAR = dict(zip(WAVES, range(2008, 2025), strict=True))

# Topics, most specific first — the first pattern to match a label names it.
# `personality` must precede `health`, or "Nervous breakdown" lands in it; the
# Big Five items in this panel are phrased "I see myself as someone who...".
TOPICS: dict[str, str] = {
    "personality": r"see myself as|i am someone who|personality|extravert|conscientious\b"
    r"|agreeableness|openness to|talkative|reserved\b|outgoing|thorough|does a thorough job"
    r"|gets nervous easily|has an active imagination|is original|trusting\b|lazy",
    "trust": r"\btrust\b|people can be trusted|take advantage of you|confidence in (parliament|police|government|the un)",
    "risk and patience": r"risk preference|willing to take risks|lottery|gamble|prefer to (wait|receive)"
    r"|impulsiv|time preference|patience",
    "politics": r"politic|which party|party identif|supports a particular|left.?right"
    r"|government should|interest in polit|voted? in|turnout",
    "social attitudes": r"attitude|immigra|gender role|woman.?s job|a woman and family|discriminat"
    r"|climate change|environment|inequal|benefit claimant|same.?sex|homosexual|redistribut",
    "religion": r"religio|belief in god|attendance at religious|which religion",
    "values": r"important in life|moral|right or wrong|what matters most|life goals",
    "wellbeing": r"ghq|life satisfaction|satisfied with (your )?life|how happy|happiness"
    r"|wellbeing|well-being|worthwhile|anxious yesterday|feel lonely|loneliness",
    "health": r"general health|long.?standing illness|self.?assessed health|health limits"
    r"|smok|alcohol|exercise|physical activity|how is your health",
}

ADMIN = re.compile(
    r"weight|^date|month|year of|interview date|proxy|^mode|^id$|hidp|pno|sample|issue"
    r"|number of|flag|indicator|derived.*(id|key)|whether|edited|imputed",
    re.I,
)

# A multi-code checklist leaves every unticked box as a row. Those are the
# absence of an answer, not an answer, and they were 64% of the first build.
#
# "no" is NOT in this list, and that is the point. The first version included it
# and deleted every "No" from every profile — 3,511 yeses and zero noes across
# 100 people. A profile then showed only what someone agreed with and never what
# they rejected: the non-voter, the non-believer and the person who does not
# trust others all looked like blanks. A bare "No" is an answer whenever the
# question was a question; it is only a non-answer on a checklist, and the test
# for THAT is the variable's own shape, not the word.
NON_ANSWER = re.compile(
    r"^(not mentioned|no(ne)? mentioned|not applicable|does not apply|inapplicable"
    r"|not selected|missing|not available|refused|don.?t know)$",
    re.I,
)
# Labels naming an item in a condition checklist rather than asking anything.
CHECKLIST = re.compile(
    r"health condition -|type of impairment|new health conditions|emotional, nervous or psychiatric"
    r"|which of these|mc |multi.?code",
    re.I,
)

# Timing screens, instruction screens, block markers: the instrument's own
# plumbing, not anything a person said.
PLUMBING = re.compile(
    r"time at (start|end)|^time |intro\b|introduction|press \d|screen|block\b"
    r"|showcard shown|^start of|^end of|continue|please turn|interviewer",
    re.I,
)
# A label ending in a bare letter or index is one item of a battery whose
# subject is in the showcard, not the label: "Trust in data holding
# organisations A" never says which organisation.
OPAQUE = re.compile(r"\b[a-h]$|\b(exp|var|item|q)\s*\d*[a-h]?$", re.I)
# Some value labels are themselves codes — the Big Five items answer "c6", not
# "applies perfectly". Dropping those cost this profile every personality item,
# which is the worst thing to lose: the Big Five is precisely what Park et al.
# used. So a code-shaped label is not discarded; the NUMBER is kept instead and
# the scale is named, because 6 is meaningless without knowing it runs to 7.
CODE_ANSWER = re.compile(r"^(c\d+|v\d+|\d+(\.\d+)?)$", re.I)
FILL_LEAK = re.compile(r"\{if\b|\}|\[if\b")

MIN_LABEL = 12
# No single topic may dominate a profile: answering 80 screening items is not
# telling us 80 things. Health is the offender; the cap applies to all.
TOPIC_CAP = 120


def topic_of(label: str) -> str | None:
    for topic, pattern in TOPICS.items():
        if re.search(pattern, label, re.I):
            return topic
    return None


def profile_id(pidp: int) -> str:
    """Stable, deterministic, and not the Understanding Society identifier."""
    return "ip_" + hashlib.sha256(f"ukds6849:{pidp}".encode()).hexdigest()[:12]


DEMO = {
    "age": "dvage", "sex": "sex", "region": "gor_dv", "employment": "jbstat",
    "education": "hiqual_dv", "marital_status": "mastat_dv", "housing": "tenure_dv",
    "children_in_household": "nchild_dv",
}


def collect() -> tuple[dict[int, list[dict]], dict[int, dict], dict[int, list[int]]]:
    answers: dict[int, list[dict]] = defaultdict(list)
    demographics: dict[int, dict] = {}
    years: dict[int, list[int]] = defaultdict(list)

    for w in WAVES:
        ds = spss.read(STATA / f"{w}_indresp_ip.dta")
        year = YEAR[w]
        wanted: list[tuple[str, str, str]] = []
        for col, label in ds.column_labels.items():
            if col == "pidp" or not label or len(label) < MIN_LABEL:
                continue
            if ADMIN.search(label) or CHECKLIST.search(label):
                continue
            if PLUMBING.search(label) or OPAQUE.search(label.strip()):
                continue
            if topic := topic_of(label):
                wanted.append((col, label, topic))
        demo_cols = {k: f"{w}_{v}" for k, v in DEMO.items() if f"{w}_{v}" in ds.df.columns}

        for _, row in ds.df.iterrows():
            pid = int(row["pidp"])
            years[pid].append(year)
            current = {}
            for k, c in demo_cols.items():
                val = row[c]
                if pd.isna(val):
                    continue
                num = pd.to_numeric(val, errors="coerce")
                if num is None or pd.isna(num) or num < 0:
                    continue
                current[k] = ds.label(c, val)
            if current:
                demographics[pid] = current  # keep the most recent wave's
            for col, label, topic in wanted:
                val = row[col]
                if pd.isna(val):
                    continue
                num = pd.to_numeric(val, errors="coerce")
                if num is not None and not pd.isna(num) and num < 0:
                    continue  # -1 don't know, -2 refused, -8 not applicable, -9 error
                text = str(ds.label(col, val)).strip().rstrip(",")
                if NON_ANSWER.match(text) or FILL_LEAK.search(text):
                    continue
                # A checklist variable has one real level — ticked. Its unticked
                # rows arrive as "no"/"none", and only there is "no" meaningless.
                levels = [v for k, v in ds.value_labels.get(col, {}).items() if k > 0]
                if len(levels) < 2 and re.fullmatch(r"no|none", text, re.I):
                    continue
                if CODE_ANSWER.match(text):
                    scale = [k for k in ds.value_labels.get(col, {}) if k > 0]
                    if not scale or num is None or pd.isna(num):
                        continue
                    text = f"{int(num)} (on a scale of {int(min(scale))} to {int(max(scale))})"
                code = None if num is None or pd.isna(num) else int(num)
                answers[pid].append(
                    {
                        "year": year,
                        "topic": topic,
                        "question": label.strip(),
                        "answer": text,
                        # The value label's own code. Two spellings of one
                        # answer share a code; an ordinal scale's codes run in
                        # scale order. Both facts are unrecoverable from the
                        # text, which is why the first run compared "no, not
                        # limited at all" against "no not limited at all" as if
                        # they were different answers, and listed general health
                        # as excellent, fair, good, poor, very good.
                        "code": code,
                        "variable": col,
                    }
                )
    return answers, demographics, years


def build(pid: int, answers: list[dict], demographics: dict, years: list[int]) -> dict:
    """One profile, with no topic allowed to swamp the rest."""
    unique: dict[tuple, dict] = {}
    for a in answers:
        unique.setdefault((a["year"], a["question"].lower(), a["answer"].lower()), a)
    answers = list(unique.values())

    kept: list[dict] = []
    seen: dict[str, int] = defaultdict(int)
    # Newest first within a topic, so a cap keeps the most recent evidence.
    for a in sorted(answers, key=lambda a: -a["year"]):
        if seen[a["topic"]] >= TOPIC_CAP:
            continue
        seen[a["topic"]] += 1
        kept.append(a)
    by_topic: dict[str, int] = defaultdict(int)
    for a in kept:
        by_topic[a["topic"]] += 1
    return {
        "id": profile_id(pid),
        "source": "ukds_6849",
        "waves": sorted(set(years)),
        "n_answers": len(kept),
        "n_before_capping": len(answers),
        "answers_by_topic": dict(sorted(by_topic.items(), key=lambda x: -x[1])),
        "demographics": demographics,
        "answers": sorted(kept, key=lambda a: (a["year"], a["topic"])),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--one", action="store_true", help="build one profile and print it")
    ap.add_argument("--n", type=int, help="build this many, deepest first")
    args = ap.parse_args()

    answers, demographics, years = collect()
    OUT.mkdir(parents=True, exist_ok=True)

    built = {p: build(p, answers[p], demographics.get(p, {}), years[p]) for p in answers}
    deepest = sorted(built, key=lambda p: -built[p]["n_answers"])
    sizes = pd.Series([built[p]["n_answers"] for p in deepest])
    print(f"people: {len(years):,}   with self-report: {len(answers):,}")
    print(f"answers per profile after cleaning: median {int(sizes.median())}, max {int(sizes.max())}")
    print(f"profiles with 221+ (the paper's size): {int((sizes >= 221).sum()):,}\n")

    if args.one:
        p = built[deepest[0]]
        path = OUT / f"{p['id']}.json"
        path.write_text(json.dumps(p, indent=2, ensure_ascii=False))
        print(f"wrote {path.relative_to(REPO)}")
        return

    n = args.n or 300
    index = {}
    for pid in deepest[:n]:
        p = built[pid]
        (OUT / f"{p['id']}.json").write_text(json.dumps(p, indent=2, ensure_ascii=False))
        index[p["id"]] = pid
    (OUT / "_index.json").write_text(json.dumps(index, indent=1))
    print(f"wrote {len(index)} profiles to {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
