"""Does a person's own history predict their next answer, better than demographics?

Third attempt. The second measured something nobody asked: it hid the whole
TOPIC of the question being predicted, so predicting "do you have a long-standing
illness in 2024" removed seventeen years of general health, mobility, smoking and
drinking from the profile. The model was left guessing someone's health from
their views on nuclear power, and health duly scored WORSE with the profile than
without it (31.5% against 44.4%).

Park's rule is narrower: remove the question being predicted, keep the rest.
*"we exclude from the survey agents' input the questions that we evaluate on for
the GSS, and for the Big 5 all question-answer pairs from the same category as
the question being predicted"* — the whole-category exception exists because the
Big Five asks nine paraphrases per trait, so leaving eight in and predicting the
ninth is reading the answer off the page. Health questions are not paraphrases of
each other.

Two things in this archive make "remove the question" harder than it sounds, and
both leak the answer back in if missed:

- **One question is written several ways across waves.** 'GENERAL HEALTH',
  'General health' and 'general health' arrive as three separate questions.
- **One question lives in several variables.** General health is `sf1`, `scsf1`
  AND `ff_sf1` — the interviewer version, the self-completion version and the
  copy fed forward from last wave. That is why one person's 2015 showed both
  "excellent" and "fair".

So questions are grouped by a normalised label and the holdout removes the GROUP.

    uv run python holdout3.py --show     # print one complete prompt
    uv run python holdout3.py --limit 40 # the run
"""

from __future__ import annotations

import argparse
import json
import random
import re
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

PROFILES = Path(__file__).resolve().parents[1] / "data" / "profiles"
OUT_TEMPLATE = "holdout3_results_{mode}.json"
OLLAMA = "http://localhost:11434/api/generate"
MODEL = "qwen3:8b"

HELD_PER_PERSON = 10
MIN_REMAINING = 30

# Items that mean nothing without the stimulus the person was shown, plus the
# survey's own admin about itself — "Email sent with wellbeing app log-in
# information" is not something anyone told us about themselves.
NOT_SELF_REPORT = re.compile(
    r"list experiment|how many of these|applicant \d|candidate \d|profile \d"
    r"|organisations involved|vignette|scenario|the statement above|option [ab]\b"
    r"|decision heuristics|app (request|log-?in)|installing app|email sent"
    r"|outcome .*request|preamble|item count|panel conditioning"
    r"|environmental numeracy|perceived political influence"
    r"|environment and transport choice",
    re.I,
)
MEANINGLESS = re.compile(r"^(value \d+|v\d+|item \d+|code \d+|\d+)$", re.I)
ROUTING = re.compile(
    r"^(h?ousehold (not )?selected|not selected|selected|inapplicable|proxy"
    r"|skipped|not asked|routed)$",
    re.I,
)
NOISE = [
    (re.compile(r",?\s+or$", re.I), ""),
    (re.compile(r"\s*\((no )?showcard\)", re.I), ""),
    (re.compile(r",?\s*\bnsc\b", re.I), ""),
    (re.compile(r"\s*\(Exp [a-z]\)", re.I), ""),
    (re.compile(r"\bTF_SPONTANEOUS\b", re.I), ""),
    (re.compile(r"\s+late$", re.I), ""),
    (re.compile(r"\s*\(on a scale of (\d+) to \1\)"), ""),
    (re.compile(r"\s*\(branched\)", re.I), ""),
    (re.compile(r"\s+"), " "),
]

# The Big Five is the one battery here whose items are paraphrases of each
# other, so predicting one from the others is retrieval rather than prediction.
PARAPHRASE_BLOCK = re.compile(r"i see my self as a person who", re.I)


def tidy(text: str) -> str:
    for pattern, repl in NOISE:
        text = pattern.sub(repl, text)
    return text.strip(" ?,.")


SCALE_WORDS = {
    "does not apply to me at all": 1,
    "applies to me perfectly": 7,
}


def canonical(text: str) -> str:
    """One spelling per answer.

    Also folds the Big Five's two label styles together: the same 1-7 item
    arrives as "5 (on a scale of 1 to 7)" in one wave and "applies to me
    perfectly" in another, so the scale looked like two different instruments.
    """
    t = tidy(text).lower()
    if t in SCALE_WORDS:
        return f"{SCALE_WORDS[t]} (on a scale of 1 to 7)"
    return t


def variable_root(variable: str) -> str:
    """One column, one question, however the archive dressed it up that wave.

    The archive renames a question when its MODE changes, not its meaning, and
    every one of these is the same question asked the same way:

        sf1 / scsf1                 `sc` = moved to self-completion
        sf3a / sf3a_b / scsf3a      `_b` = the no-showcard variant
        scghqa / scghqalat          `lat` = asked late in the questionnaire
        envhabit1 / _a / _b         two mode variants of one habit
        scenv_nowo / scenv_nowoexp  `exp` = the experimental re-ask

    Stripping only the wave letter left these as different questions, which
    split one answer into several segments — "general health: good [2008-2013];
    good [2014]" — and then labelled the result "(changed)" when nothing had.
    """
    v = variable.lower()
    v = re.sub(r"^[a-q]_", "", v)
    v = re.sub(r"^ff_", "", v)
    v = re.sub(r"^sc", "", v)
    v = re.sub(r"lat$", "", v)
    v = re.sub(r"exp$", "", v)
    v = re.sub(r"_[ab]$", "", v)
    return v


def is_fed_forward(variable: str) -> bool:
    """True for `w_ff_*`, whose value is LAST wave's answer, not this wave's.

    One person's 2016 showed `i_ff_health = no` and `i_health = yes`. Those do
    not contradict: the first is their 2015 answer, carried forward. Dating it
    2016 put a wrong answer in the profile for every fed-forward column, in
    every profile.
    """
    return bool(re.match(r"^[a-q]_ff_", variable.lower()))


def question_key(question: str) -> str:
    """One key per question, however the archive spelled it that wave.

    Beyond case, this folds the self-completion and fed-forward variants of a
    question onto the question itself: 'self-assessed general health status' and
    'GENERAL HEALTH' are the same question, and if the holdout removes one while
    leaving the other, the answer is handed straight back.
    """
    key = canonical(question)
    # "long standing illness" and "long-standing illness" are one question; the
    # archive hyphenates it differently between waves and the two lines then
    # contradicted each other in the same profile.
    key = key.replace("-", " ")
    key = re.sub(r"^(self.?assessed|sc)\s+", "", key)
    # The SF-12 renamed several items partway through the panel: "health limits
    # kind of work" became "Last 4 weeks: Physical health limits kind of work".
    # Treating them as different questions left the renamed version in the
    # profile while the holdout removed the original, handing back the answer.
    key = re.sub(r"^last \d+ weeks:\s*", "", key)
    key = re.sub(r"^physical\s+", "", key)
    key = re.sub(r"\s+status$", "", key)
    return key.strip(" -")


def group_key(answer: dict) -> str:
    """What makes two rows the same question. The variable root if we have it.

    Falling back to the label is for rows with no variable recorded; the label
    is the weaker signal, because the archive rewords a question far more
    readily than it renumbers a column.
    """
    root = variable_root(answer.get("variable", ""))
    return f"var:{root}" if root else question_key(answer["question"])


# Which answers the holdout removes. The three are different experiments and
# their numbers are not comparable, so the mode is named in the output.
#
#   inference  every year of the target question. "Could you work this out from
#              everything else you know about them?" Hardest, and the only one
#              that cannot be won by repeating last year.
#   block      the above, plus every other item in the same instrument block.
#              Park ran both: question-only scored 0.82, whole-block 0.77, and
#              the gap is how much a sibling item gives away.
#   panel      only the target YEAR. Their own earlier answers to the same
#              question stay, which is what you would really have in a panel —
#              and is why this one must be scored on predicting CHANGE. "Say
#              what they said last year" beats most models and learns nothing.
MODES = ("inference", "block", "panel")

# Items belonging to one instrument block, for MODE="block". The SF-12 physical
# functioning and role-physical items are one scale; the GHQ-12 is one scale.
BLOCKS = [
    re.compile(r"^sf\d"),
    re.compile(r"^ghq"),
    re.compile(r"^envhabit"),
]


# A branched item asks the stance first ("do you agree or disagree?") and the
# strength second ("strongly or somewhat?"), in two columns. The second column's
# answer is a bare intensifier — "strongly", "somewhat" — which says nothing on
# its own and reads as a same-year contradiction beside the stance. Rebuilding
# "somewhat disagree" from the pair needs to know which column is which half,
# per instrument, which we do not. So the fragment goes and the stance stays.
BARE_INTENSIFIER = re.compile(r"^(strongly|somewhat|a little|very much)$", re.I)

# The political-efficacy battery is branched across three columns per wave
# (`poleff2_c1` the stance, `_d1` the stance again in another mode, `_c3` the
# two combined) and the waves disagree about which column holds what. Rebuilt
# naively it becomes three lines under one label, or a same-year contradiction.
# Four lines out of eighty-nine, and reconstructing them correctly needs
# instrument documentation we do not have, so they go.
BRANCHED_MESS = re.compile(r"^poleff", re.I)


def usable(answer: dict) -> bool:
    q, a = answer["question"], answer["answer"]
    # A fed-forward value is last wave's answer wearing this wave's date, and
    # the real answer for this wave is almost always present in its own column,
    # so dropping it loses nothing and stops the profile contradicting itself.
    if is_fed_forward(answer.get("variable", "")):
        return False
    if NOT_SELF_REPORT.search(q) or NOT_SELF_REPORT.search(a):
        return False
    if ROUTING.match(a.strip()) or MEANINGLESS.match(a.strip()):
        return False
    if BARE_INTENSIFIER.match(tidy(a)):
        return False
    if BRANCHED_MESS.match(variable_root(answer.get("variable", ""))):
        return False
    return len(tidy(q)) >= 12


def age_at(profile: dict, year: int) -> int | None:
    try:
        now = int(str(profile["demographics"].get("age", "")).strip())
    except ValueError:
        return None
    return now - (profile["waves"][-1] - year)


def years_phrase(years: list[int]) -> str:
    out, start, prev = [], years[0], years[0]
    for y in [*years[1:], None]:
        if y is not None and y == prev + 1:
            prev = y
            continue
        out.append(str(start) if start == prev else f"{start}-{prev}")
        if y is not None:
            start = prev = y
    return ", ".join(out)


# A battery is a run of questions sharing a prefix before the colon: "GHQ:
# concentration", "GHQ: loss of sleep". Grouping them under one header drops the
# repeated prefix, keeps the battery together instead of scattered alphabetically,
# and — the actual reason — makes "show only the groups related to this question"
# a one-line change rather than a guess.
BATTERY_ALIASES = [
    (re.compile(r"^environmental habits?$", re.I), "Environmental habits"),
    (re.compile(r"^ghq$", re.I), "GHQ (general health questionnaire)"),
]
MIN_BATTERY = 3


BATTERY_SPLITS = [
    # The Big Five items separate on an ellipsis, and the political-discussion
    # battery on the word "with" — neither uses the colon the first version
    # assumed, so seven personality items and six discussion items sat as
    # thirteen unrelated lines.
    (
        re.compile(r"^(i see my self as a person who)\.\.\.\s*(.+)$", re.I),
        "Personality — I see myself as a person who...",
    ),
    (re.compile(r"^(talk about politics) with\s+(.+)$", re.I), "Talks about politics with"),
]


def battery_of(label: str) -> tuple[str, str] | None:
    """(header, item) if this label belongs to a battery, else None."""
    for pattern, header in BATTERY_SPLITS:
        if m := pattern.match(label.strip()):
            return header, m.group(2).strip()
    if ":" not in label:
        return None
    head, _, item = label.partition(":")
    head, item = head.strip(), item.strip()
    if not item or len(head) < 3:
        return None
    for pattern, canonical_head in BATTERY_ALIASES:
        if pattern.match(head):
            return canonical_head, item
    return head, item


def history_lines(answers: list[dict]) -> dict[str, tuple[str, str]]:
    """Per question group: (label, answers-with-years), kept apart.

    Returning the two separately matters: the first version returned a finished
    line and the caller split it on ": " to recover the label, which turned
    "GHQ: concentration: same as usual" into the label "GHQ" and silently
    disabled every battery.
    """
    grouped: dict[str, dict[object, list[int]]] = defaultdict(lambda: defaultdict(list))
    label: dict[str, str] = {}
    spelling: dict[str, dict[object, str]] = {}
    for a in answers:
        if not usable(a):
            continue
        key = group_key(a)
        label.setdefault(key, tidy(a["question"]))
        # The code identifies an answer, but ONLY within its own variable:
        # different variables reuse the same numbers for different meanings.
        # Keying on the bare code merged "strongly" (c_poleff2_d2, code 2, 2010)
        # with "neither agree/disagree" (d_poleff2_c1, code 2, 2011) and
        # invented a 2011 answer the person never gave. So the key is the
        # variable root plus the code, and the root drops the wave prefix
        # because the same variable is a_x in 2008 and q_x in 2024.
        variant = a["code"] if a.get("code") is not None else canonical(a["answer"])
        grouped[key][variant].append(a["year"])
        if variant not in spelling.get(key, {}):
            spelling.setdefault(key, {})[variant] = canonical(a["answer"])

    lines = {}
    for key, variants in grouped.items():
        parts = [
            f"{spelling[key][v]} [{years_phrase(sorted(set(ys)))}]"
            for v, ys in sorted(variants.items(), key=lambda kv: min(kv[1]))
        ]
        mark = "  (changed)" if len(parts) > 1 else ""
        lines[key] = (label[key], "; ".join(parts) + mark)
    return lines


def option_list(raw: list[tuple[int | None, str]]) -> list[str] | None:
    """Deduplicate by code, order by code; text cannot do either job."""
    by_code: dict[object, str] = {}
    for code, text in raw:
        text = tidy(text)
        if not text or ROUTING.match(text) or MEANINGLESS.match(text):
            continue
        by_code.setdefault(code if code is not None else text.lower(), canonical(text))
    if len(by_code) < 2:
        return None
    numbered = sorted((k, v) for k, v in by_code.items() if isinstance(k, int))
    unnumbered = sorted(v for k, v in by_code.items() if not isinstance(k, int))
    return [v for _, v in numbered] + unnumbered


def render_history(lines: dict[str, tuple[str, str]], order: list[str]) -> str:
    """Lay the history out, collapsing batteries under a single header."""
    members: dict[str, list[tuple[str, str]]] = defaultdict(list)
    singles: list[str] = []
    for key in order:
        label, rest = lines[key]
        if b := battery_of(label):
            members[b[0]].append((b[1], rest))
        else:
            singles.append(f"- {label}: {rest}")

    out: list[str] = []
    for header, items in members.items():
        if len(items) < MIN_BATTERY:
            # Too few to be worth a header; put them back as ordinary lines.
            singles.extend(f"- {header}: {item}: {rest}" for item, rest in items)
            continue
        out.append(f"{header}:")
        out.extend(f"  - {item}: {rest}" for item, rest in sorted(items))
    return "\n".join(sorted(singles) + ([""] if singles and out else []) + out)


def build_prompt(
    profile: dict,
    shown: list[dict],
    question: dict,
    options: list[str],
    same_topic_last: bool = True,
) -> str:
    year = question["year"]
    who = dict(profile["demographics"])
    if (age := age_at(profile, year)) is not None:
        who["age"] = f"{age} (in {year})"
    header = "\n".join(f"{k.replace('_', ' ').capitalize()}: {v}" for k, v in who.items())

    lines = history_lines(shown)
    if same_topic_last:
        # Nearest the question is the strongest position in a long prompt, and
        # alphabetical order was putting climate-change opinions there for a
        # question about religion.
        topics = {group_key(a): a["topic"] for a in shown if usable(a)}
        related = [k for k in sorted(lines) if topics.get(k) == question["topic"]]
        other = [k for k in sorted(lines) if topics.get(k) != question["topic"]]
        body = render_history(lines, other)
        if related:
            body += "\n\n" + render_history(lines, related)
    else:
        body = render_history(lines, sorted(lines))

    choices = "\n".join(f"  {i + 1}. {o}" for i, o in enumerate(options))
    return (
        f"You are this person, answering a survey in {year}. "
        "Answer as they would, not as you think they should.\n\n"
        f"ABOUT YOU\n{header}\n\n"
        "WHAT YOU HAVE TOLD THIS SURVEY OVER THE YEARS\n"
        "Years in brackets. Where an answer changed, every version is shown.\n"
        f"{body}\n\n"
        f"THE QUESTION, ASKED IN {year}\n{tidy(question['question'])}\n\n"
        f"OPTIONS\n{choices}\n\n"
        "Answer with the number of the option only."
    )


def ask(prompt: str) -> int | None:
    body = json.dumps(
        {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {"temperature": 0, "num_predict": 8},
        }
    ).encode()
    try:
        req = urllib.request.Request(
            OLLAMA, data=body, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=300) as r:
            text = str(json.loads(r.read())["response"])
    except (urllib.error.URLError, TimeoutError, OSError):
        return None
    nums = re.findall(r"\b(\d+)\b", text)
    return int(nums[0]) if nums else None


def block_of(root: str) -> str | None:
    for pattern in BLOCKS:
        if pattern.match(root):
            return pattern.pattern
    return None


def tasks_for(
    profile: dict, pooled: dict, rng: random.Random, mode: str = "inference"
) -> list[dict]:
    """Hold out whole QUESTIONS, not whole topics.

    The profile keeps the rest of the topic, which is the point: knowing someone
    rated their health excellent for sixteen years should help predict whether
    they report an illness, and the previous design deleted exactly that.
    """
    usable_answers = [a for a in profile["answers"] if usable(a)]
    by_key: dict[str, list[dict]] = defaultdict(list)
    for a in usable_answers:
        by_key[group_key(a)].append(a)

    # A question renamed mid-panel keeps its variable root: "health limits
    # typical activities" (a_sf2a, 2008-09) became "Health limits moderate
    # activities" (c_scsf2a, 2010+). Holding out only the later name left the
    # earlier answers to the SAME question sitting in the prompt. So the holdout
    # removes every key sharing a variable root with the target.
    roots_of: dict[str, set[str]] = defaultdict(set)
    for k, items in by_key.items():
        for a in items:
            roots_of[k].add(variable_root(a.get("variable", "")))

    out = []
    for key in rng.sample(sorted(by_key), k=min(len(by_key), HELD_PER_PERSON * 3)):
        answers = by_key[key]
        target = max(answers, key=lambda a: a["year"])  # their most recent answer
        options = option_list(pooled[key])
        if not options or canonical(target["answer"]) not in options:
            continue
        if PARAPHRASE_BLOCK.search(target["question"]):
            hide = {k for k in by_key if PARAPHRASE_BLOCK.search(by_key[k][0]["question"])}
        else:
            hide = {k for k in by_key if roots_of[k] & roots_of[key]}

        if mode == "block":
            blocks = {b for r in roots_of[key] if (b := block_of(r))}
            if blocks:
                hide |= {
                    k
                    for k, rs in roots_of.items()
                    if any(block_of(r) in blocks for r in rs if block_of(r))
                }
        if mode == "panel":
            # Keep their earlier answers to this very question; remove only the
            # year being predicted. Everything else stays as normal.
            shown = [
                a for a in usable_answers if group_key(a) not in hide or a["year"] < target["year"]
            ]
        else:
            shown = [a for a in usable_answers if group_key(a) not in hide]
        if len(shown) < MIN_REMAINING:
            continue
        out.append(
            {
                "p": profile,
                "shown": shown,
                "q": target,
                "options": options,
                "topic": target["topic"],
                "hidden": len(usable_answers) - len(shown),
            }
        )
        if len(out) >= HELD_PER_PERSON:
            break
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--show", action="store_true")
    ap.add_argument(
        "--mode",
        choices=MODES,
        default="inference",
        help="what the holdout removes; see MODES. The three are "
        "different experiments and their numbers do not compare.",
    )
    args = ap.parse_args()

    profiles = [json.loads(p.read_text()) for p in sorted(PROFILES.glob("ip_*.json"))]
    if args.limit:
        profiles = profiles[: args.limit]
    rng = random.Random(0)

    pooled: dict[str, list[tuple[int | None, str]]] = defaultdict(list)
    for p in profiles:
        for a in p["answers"]:
            if usable(a):
                pooled[group_key(a)].append((a.get("code"), a["answer"]))

    tasks = [t for p in profiles for t in tasks_for(p, pooled, rng, args.mode)]

    if args.show:
        t = next(x for x in tasks if x["topic"] == "health")
        prompt = build_prompt(t["p"], t["shown"], t["q"], t["options"])
        (PROFILES / "PROMPT_EXAMPLE.txt").write_text(prompt)
        print(prompt)
        print(
            f"\n[{len(prompt):,} chars | topic {t['topic']} | "
            f"{t['hidden']} answers hidden, {len(t['shown'])} shown]"
        )
        print(
            f"[TRUE ANSWER: {t['options'].index(canonical(t['q']['answer'])) + 1}. "
            f"{canonical(t['q']['answer'])}]"
        )
        return

    print(f"MODE: {args.mode}", flush=True)
    print(
        f"{len(profiles)} people, {len(tasks)} questions, {len(tasks) * 2} predictions", flush=True
    )
    out = PROFILES / OUT_TEMPLATE.format(mode=args.mode)
    results, started = [], time.time()
    for i, t in enumerate(tasks, 1):
        rec = {
            "id": t["p"]["id"],
            "topic": t["topic"],
            "year": t["q"]["year"],
            "question": tidy(t["q"]["question"]),
            "n_options": len(t["options"]),
            "truth": t["options"].index(canonical(t["q"]["answer"])) + 1,
        }
        rec["profile"] = ask(build_prompt(t["p"], t["shown"], t["q"], t["options"]))
        rec["demographics"] = ask(build_prompt(t["p"], [], t["q"], t["options"]))
        results.append(rec)
        out.write_text(json.dumps(results, indent=1))
        if i % 10 == 0 or i == len(tasks):
            rate = (time.time() - started) / i
            print(
                f"  {i}/{len(tasks)}  {rate:.1f}s/q  ~{rate * (len(tasks) - i) / 60:.0f} min left",
                flush=True,
            )

    chance = sum(1 / r["n_options"] for r in results) / len(results)
    print(f"\n{'arm':<22} {'answered':>9} {'correct':>9}")
    print(f"{'random guessing':<22} {'-':>9} {chance:>8.1%}")
    for arm in ("demographics", "profile"):
        got = [r for r in results if r[arm] is not None]
        acc = sum(r[arm] == r["truth"] for r in got) / len(got) if got else 0
        print(f"{arm:<22} {len(got):>9} {acc:>8.1%}")
    if args.mode == "panel":
        # The number that matters here is whether anything beats "say what they
        # said last year". Without it, a high score means nothing.
        repeats = [r for r in results if r.get("last_year") is not None]
        if repeats:
            acc = sum(r["last_year"] == r["truth"] for r in repeats) / len(repeats)
            print(
                f"{'repeat last year':<22} {len(repeats):>9} {acc:>8.1%}  <- beat this or it is noise"
            )
    print("\nby topic:")
    for topic in sorted({r["topic"] for r in results}):
        rows = [r for r in results if r["topic"] == topic]
        line = f"  {topic:<20}"
        for arm in ("demographics", "profile"):
            got = [r for r in rows if r[arm] is not None]
            line += (
                f"  {arm[:4]} {sum(r[arm] == r['truth'] for r in got) / len(got):>6.1%}"
                if got
                else "    -  "
            )
        print(line + f"  (n={len(rows)})")


if __name__ == "__main__":
    main()
