"""Expert reflections, with trends computed in code and a checker that breaks them.

The first version produced 35 confident notes for one person and four of the
eight checkable claims were false — *"health declined from excellent to fair"*,
*"didn't vote in the 2019 general election"*, *"interest in politics waned"*,
*"Labour to Liberal Democrat to neutral"*. Every false claim was a TREND, and
every true claim was a static fact. The model is reliable at describing a person
and unreliable at narrating how they changed, which is exactly the dimension
this dataset exists to provide.

So two changes, in that order of importance:

1. **Trends are computed, not inferred.** For any question asked in three or
   more years, the answer history is written out exactly and handed to the
   writer as fact. The model interprets change; it never detects it. Her party
   really is `Labour (2009, 2011, 2013, 2014, 2022), Liberal Democrat (2012)` —
   a one-year blip that four experts turned into a political journey.

2. **A checker that is told to break each note.** Writer proposes, checker
   verifies against her own answers, unsupported notes are dropped. The checker
   is briefed that a PASS is not evidence and that its job is to find the claim
   that is not in the data.

Still local: ollama only, because `jev.RESTRICTED` refuses `source="ukds"`.

    uv run python reflect2.py --one
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

PROFILES = Path(__file__).resolve().parents[1] / "data" / "profiles"
OLLAMA = "http://localhost:11434/api/generate"
MODEL = "qwen3:8b"
MIN_YEARS_FOR_TREND = 3

EXPERTS: dict[str, str] = {
    "psychologist": "their personality, temperament, outlook, and how they cope",
    "behavioural economist": "their attitude to risk, money, time, and trade-offs",
    "political scientist": "their political views, values, and civic engagement",
    "demographer": "their demographic traits, life course, and social position",
}


def tidy(label: str) -> str:
    s = re.sub(r"\s*\((no )?showcard\)", "", label)
    s = re.sub(r",?\s*\bnsc\b", "", s)
    s = re.sub(r"\s*\(Exp [a-z]\)", "", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip(" ?,")
    return s.capitalize() if s.isupper() else s


def histories(profile: dict) -> tuple[list[str], list[str]]:
    """Split answers into what changed and what did not, exactly.

    This is the whole fix. A question asked across several years becomes one
    line showing every answer and the years it was given, so "did this person
    change" is answered by the data rather than guessed from a wall of rows.
    """
    by_q: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for a in profile["answers"]:
        by_q[tidy(a["question"])][a["answer"].lower()].append(a["year"])

    changed: list[str] = []
    steady: list[str] = []
    for question, answers in sorted(by_q.items()):
        years = {y for ys in answers.values() for y in ys}
        if len(years) < MIN_YEARS_FOR_TREND:
            continue
        parts = [
            f"{ans} ({', '.join(str(y) for y in sorted(set(ys)))})"
            for ans, ys in sorted(answers.items(), key=lambda kv: min(kv[1]))
        ]
        line = f"  {question}: " + "; then ".join(parts)
        (changed if len(answers) > 1 else steady).append(line)
    return changed, steady


def render(profile: dict) -> str:
    changed, steady = histories(profile)
    lines = [f"{k.replace('_', ' ').capitalize()}: {v}" for k, v in profile["demographics"].items()]

    if steady:
        lines += ["", "ANSWERS THAT NEVER CHANGED (asked in 3+ years, same answer every time):"]
        lines += steady
    if changed:
        lines += ["", "ANSWERS THAT CHANGED (every answer and the years given, exactly):"]
        lines += changed

    lines += ["", "ALL ANSWERS BY YEAR:"]
    year = None
    seen: set[tuple[str, str]] = set()
    for a in sorted(profile["answers"], key=lambda a: (a["year"], a["topic"])):
        key = (tidy(a["question"]).lower(), a["answer"].lower())
        if key in seen:
            continue
        seen.add(key)
        if a["year"] != year:
            year = a["year"]
            lines.append(f"\n{year}:")
        lines.append(f"  {tidy(a['question'])}: {a['answer']}")
    return "\n".join(lines)


def ask(prompt: str, max_tokens: int, temperature: float = 0.3) -> str | None:
    body = json.dumps(
        {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
    ).encode()
    try:
        req = urllib.request.Request(
            OLLAMA, data=body, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=900) as r:
            return str(json.loads(r.read())["response"]).strip()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"      request failed: {exc}")
        return None


def write_notes(data: str, expert: str, subject: str) -> list[str]:
    out = ask(
        f"{data}\n\n=====\n\n"
        f"Imagine you are an expert {expert} (with a PhD) taking notes while reading "
        f"this person's survey answers. Write observations and reflections about "
        f"{subject}.\n\n"
        "RULES:\n"
        "- Between 5 and 15 observations, one per line, starting with '- '.\n"
        "- Infer what they did NOT say. Do not just repeat their answers back.\n"
        "- Any claim that something CHANGED over time must come from the section "
        "headed ANSWERS THAT CHANGED. Do not infer a trend from anything else.\n"
        "- Never state a year unless that exact year appears in the data.\n"
        "- If the evidence is thin, write fewer notes. Do not pad.",
        max_tokens=1200,
    )
    if not out:
        return []
    lines = [
        re.sub(r"^[-*\d.)\s]+", "", ln).strip()
        for ln in out.splitlines()
        if ln.strip().startswith(("-", "*")) or re.match(r"^\d+[.)]", ln.strip())
    ]
    return [ln for ln in lines if len(ln) > 30]


def check(data: str, note: str) -> tuple[bool, str]:
    """Verify one note against the person's answers. Briefed to break it.

    A checker told to "verify" agrees. This one is told the note is probably
    wrong and that finding nothing is a failure of the check, not a pass — the
    same framing the project uses on its study checkers.
    """
    out = ask(
        f"{data}\n\n=====\n\n"
        f'A researcher wrote this note about the person above:\n\n  "{note}"\n\n'
        "Your job is to BREAK it. Assume it is wrong until the data proves otherwise. "
        "Finding nothing wrong is a failure of your check, not a pass.\n\n"
        "Check in particular:\n"
        "- Does every year mentioned actually appear in the data?\n"
        "- If it claims something changed, increased or declined, does the data "
        "show that, or is it one odd reading among steady ones?\n"
        "- Is every fact it states actually present, or has it been assumed?\n\n"
        "Reply with exactly one line:\n"
        "SUPPORTED: <the specific answers that back it up>\n"
        "or\n"
        "UNSUPPORTED: <what it claims that the data does not show>",
        max_tokens=250,
        temperature=0.0,
    )
    if not out:
        return False, "checker did not respond"
    verdict = out.strip().splitlines()[0] if out.strip() else ""
    if re.match(r"\s*UNSUPPORTED", verdict, re.I):
        return False, verdict.split(":", 1)[-1].strip()
    if re.match(r"\s*SUPPORTED", verdict, re.I):
        return True, verdict.split(":", 1)[-1].strip()
    return False, f"checker was unclear: {verdict[:120]}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--one", action="store_true")
    args = ap.parse_args()

    files = sorted(PROFILES.glob("ip_*.json"))
    if args.one:
        files = files[:1]

    for path in files:
        profile = json.loads(path.read_text())
        data = render(profile)
        changed, steady = histories(profile)
        print(f"{path.name}  ({profile['n_answers']} answers)", flush=True)
        print(
            f"  computed: {len(changed)} questions changed, {len(steady)} never changed\n",
            flush=True,
        )

        kept: dict[str, list[dict]] = {}
        dropped: list[dict] = []
        for expert, subject in EXPERTS.items():
            started = time.time()
            notes = write_notes(data, expert, subject)
            verified = []
            print(f"  {expert:<22} wrote {len(notes)} notes, checking...", flush=True)
            for i, note in enumerate(notes, 1):
                ok, why = check(data, note)
                print(f"      {i}/{len(notes)} {'KEEP' if ok else 'DROP'}  {note[:72]}", flush=True)
                (verified if ok else dropped).append({"expert": expert, "note": note, "why": why})
            kept[expert] = list(verified)
            print(
                f"  {expert:<22} wrote {len(notes):>2}, kept {len(kept[expert]):>2}, "
                f"dropped {len(notes) - len(kept[expert]):>2}  ({time.time() - started:.0f}s)",
                flush=True,
            )

        profile["expert_reflections"] = {e: [v["note"] for v in v2] for e, v2 in kept.items()}
        profile["reflections_dropped"] = dropped
        profile["computed_histories"] = {"changed": changed, "unchanged": steady}
        path.write_text(json.dumps(profile, indent=2, ensure_ascii=False))

        if args.one:
            print("\n" + "=" * 70)
            print("KEPT")
            print("=" * 70)
            for expert, notes in profile["expert_reflections"].items():
                print(f"\n{expert.upper()}")
                for n in notes:
                    print(f"  - {n}")
            print("\n" + "=" * 70)
            print(f"DROPPED BY THE CHECKER ({len(dropped)})")
            print("=" * 70)
            for d in dropped:
                print(f"\n  [{d['expert']}] {d['note']}")
                print(f"      -> {d['why'][:200]}")


if __name__ == "__main__":
    main()
