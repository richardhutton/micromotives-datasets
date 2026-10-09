#!/usr/bin/env python3
"""Does the questionnaire actually carry each experiment's question wording?

`ip_triage.py` checked that an allocation variable is named, exists in the data,
and has its arms documented. It did NOT check the thing that decides whether a
build produces real stimulus text or an invention: **is the wording in the wave
questionnaire, and can it be found by variable name?**

That gap is not theoretical. Building 9.10 took a session to discover its fifth
dimension lived in a different file from the one the guide implied, and the
archived value labels turned out to be not merely truncated but wrong — two
opposite housework splits sharing one label string. The questionnaire was the
only usable source, and the whole build rests on it.

So, per experiment: take every variable the User Guide names, look each one up in
the wave questionnaire, and report how many are found with a block of real prose
attached. A variable that appears only in a routing condition, or not at all, is
not wording.

**This reports what it found. It does not pass or fail anything.** `ip_triage.py`
produced six false negatives in a row from six different pattern defects, and
the lesson was that a verdict from a regex over a 900-page PDF is worth less than
the extract it is drawn from. So the default output is counts, and `--show`
prints the matched text for reading.

    uv run python scripts/ip_wording.py                 # the 16 selected
    uv run python scripts/ip_wording.py --id 9.18 --show
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CACHE = REPO / "data" / "raw" / "ukds_6849" / ".triage_text"
CATALOGUE = REPO / "data" / "catalog" / "innovation_panel_experiments.json"
WAVES = "abcdefghijklmnopq"

SELECTED = [
    "9.18", "9.39", "9.43", "9.36", "9.24", "9.4", "9.48", "9.17",
    "9.31", "9.12", "9.42", "9.20", "9.13", "9.11", "9.9", "9.47",
]

# A variable name as the guide writes it: bare, wave-prefixed, or in a list of
# "the variables affected by this experiment are a*, b*, c?". The trailing
# wildcards are the guide's own notation for a family and are stripped.
NAME = re.compile(r"\b([a-z][a-z0-9_]{3,})\b", re.I)

# Words that look like variables but are prose. Kept deliberately short: the
# real filter is whether the name turns up in the questionnaire at all.
STOP = {
    "this", "that", "with", "from", "were", "where", "which", "respondent",
    "respondents", "experiment", "question", "questions", "variable", "variables",
    "wave", "waves", "file", "record", "allocated", "allocation", "group", "groups",
    "version", "versions", "about", "their", "they", "there", "these", "those",
    "been", "have", "each", "both", "same", "also", "more", "most", "some", "such",
    "than", "then", "them", "when", "what", "will", "would", "could", "should",
    "study", "studies", "data", "survey", "answer", "answers", "asked", "household",
    "households", "individual", "individuals", "level", "sample", "random", "randomly",
    "treatment", "conditions", "condition", "between", "within", "first", "second",
    "third", "half", "whether", "included", "include", "using", "used",
}

# How the questionnaires mark the wording itself. Formats differ by wave -- the
# older ones print "Text" on its own line, the newer "Text:" inline -- so both.
WORDING = re.compile(r"^\s*Text\b", re.M)


def text_for(wave: int) -> str | None:
    for pattern in (
        f"6849_ip_wave_{wave}_questionnaire*.txt",
        f"6849_innovation_panel_wave_{wave}_questionnaire*.txt",
    ):
        found = sorted(CACHE.glob(pattern))
        if found:
            return found[0].read_text(errors="ignore")
    return None


def guide_sections() -> dict[str, str]:
    text = (CACHE / "6849_innovation_panel_user_guide.txt").read_text(errors="ignore")
    heads = list(re.finditer(r"^[ \t]*(\d+\.\d+)\s+(\S.*)$", text, re.M))
    best: dict[str, str] = {}
    for n, head in enumerate(heads):
        body = text[head.end() : heads[n + 1].start() if n + 1 < len(heads) else len(text)]
        if "." not in body[:600]:
            continue
        if len(body) > len(best.get(head.group(1), "")):
            best[head.group(1)] = body
    return best


def candidates(section: str) -> list[str]:
    """Variable-ish names the guide mentions, longest first."""
    seen: dict[str, None] = {}
    for m in NAME.finditer(section):
        name = m.group(1).lower()
        if name in STOP or (name.isalpha() and len(name) < 5):
            continue
        seen.setdefault(re.sub(r"^[a-q]_", "", name), None)
    return sorted(seen, key=len, reverse=True)


def look_up(name: str, questionnaire: str) -> str | None:
    """The question block this variable names, if the questionnaire has one.

    A match is only wording if a `Text` marker follows within the block. A
    variable cited in a routing condition ("if FSVIGNAME1 = 1") matches the name
    and carries no wording, and counting those would report a coverage this does
    not have.
    """
    for m in re.finditer(rf"\b{re.escape(name)}\b", questionnaire, re.I):
        block = questionnaire[m.start() : m.start() + 2500]
        if WORDING.search(block):
            return block
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--id", help="one experiment")
    ap.add_argument("--show", action="store_true", help="print the matched wording")
    args = ap.parse_args()

    raw = json.loads(CATALOGUE.read_text())
    exps = {x["id"]: x for x in (raw["experiments"] if isinstance(raw, dict) else raw)}
    sections = guide_sections()
    wanted = [args.id] if args.id else SELECTED

    print(f"{'id':<6}{'wave':<9}{'named':>6}{'found':>7}  title")
    summary = []
    for eid in wanted:
        exp = exps[eid]
        section = sections.get(eid, "")
        names = candidates(section)
        waves = [
            int(w) for w in str(exp["waves"]).replace(" ", "").split(",") if w.isdigit()
        ]
        hits: dict[str, str] = {}
        for wave in waves:
            q = text_for(wave)
            if q is None:
                continue
            for name in names:
                if name in hits:
                    continue
                block = look_up(name, q)
                if block:
                    hits[name] = block
        print(
            f"{eid:<6}{str(exp['waves'])[:8]:<9}{len(names):>6}{len(hits):>7}  "
            f"{exp['title'][:46]}"
        )
        summary.append((eid, len(names), len(hits)))
        if args.show and hits:
            name, block = next(iter(hits.items()))
            print(f"\n--- {eid}: wording found via {name!r} ---")
            print("\n".join(line for line in block[:1400].splitlines() if line.strip()))
            print("--- end ---\n")

    none_found = [e for e, _, h in summary if h == 0]
    print(f"\n{len(summary) - len(none_found)} of {len(summary)} have wording located")
    if none_found:
        print(f"  NOTHING FOUND for: {', '.join(none_found)} — read these by hand")


if __name__ == "__main__":
    main()
