#!/usr/bin/env python3
"""Measure the condition screen against the defects this project actually shipped.

`jev.DEFECT_MASS_REVIEW` is a threshold, and a threshold chosen by taste is a
guess with a number on it. This probe sets it by measurement: it screens the five
real defects — reconstructed verbatim from the record, with the exact text that
shipped — alongside the corrected version of each, and reports the separation.

Why this and not a unit test: a unit test with a stub proves our arithmetic, and
`tests/test_jev.py` does that. Nothing offline can tell us whether the model can
actually see the difference between "Scenario #1" on a row rating scenario 5 and
the same text with that sentence removed. Only the live call answers that, and
the answer is a number we should have on file rather than an impression.

It is also the project's first eval. CLAUDE.md has had an evaluation section
since it was written and nothing had ever exercised it.

    source ~/.bash_profile && uv run python scripts/condition_probe.py

Writes docs/CONDITION_PROBE.md. On the wire: stimulus and question text only.
"""

from __future__ import annotations

import json
from pathlib import Path

from micromotives_datasets import jev

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "CONDITION_PROBE.md"
CACHE = REPO / "data" / "catalog" / "condition_probe.json"

# A shared scenario body, so the only difference between a case and its control
# is the defect itself. Lifted from b87sm's real arm text.
_B87SM = (
    "A company is developing a smartphone app for a research study. The app would "
    "collect data from the sensors already built into your phone. The data would be "
    "stored on university servers and deleted after five years."
)

# The five defects, each with the text that SHIPPED and the text that replaced it.
# Where a defect is quoted, it is quoted from the ledger or the recipe diff, not
# paraphrased — a probe built on a paraphrase measures the paraphrase.
CASES: list[dict[str, str]] = [
    {
        "id": "b87sm_sequence_signposting",
        "expect": "sequence_signposting",
        "rows": "13,513",
        "outcome": "How willing would you be to install this app?",
        "bad": f"Scenario #1. {_B87SM}",
        "good": _B87SM,
    },
    {
        "id": "es4xw_reveals_the_experiment",
        "expect": "reveals_the_experiment",
        "rows": "32,228",
        "outcome": "This team includes a high degree of ethnic diversity.",
        "bad": (
            "The page showed a photograph of six individual headshots, arranged in two "
            "rows of three. Four of the six people pictured are the same in every "
            "version of this photograph: a White woman (top row, left), a White man "
            "(top row, right), a White man (bottom row, middle), and a White woman "
            "(bottom row, right). The remaining two people pictured (top row, middle; "
            "bottom row, left) are, in this version, both Black men, so the pictured "
            "team has two Black members and four White members."
        ),
        "good": (
            "A large company recently formed a management team to lead a new project. "
            "You don't know any of them personally, but the company included pictures "
            "of the management team when it sent out an announcement about the project. "
            "The team pictured had six people: two were Black and four were White."
        ),
    },
    {
        "id": "sh4px_premature_treatment",
        "expect": "premature_treatment",
        "rows": "4,600 excluded",
        "outcome": "How do you currently feel? Happy.",
        "bad": (
            "You were asked to recall a time you felt happy and to write about it. You "
            "then completed a values exercise in which you wrote about a value that "
            "matters to you and why. You then read an article about the link between "
            "alcohol consumption and breast cancer risk."
        ),
        "good": ("You were asked to recall a time you felt happy and to write about it."),
    },
    {
        "id": "a2nbf_unresolved_directive",
        "expect": "unresolved_directive",
        "rows": "3,117",
        "outcome": "Would you want this test?",
        "bad": (
            "Suppose that {you/your partner} were pregnant and a test were available "
            "early in the pregnancy that could detect a serious genetic condition."
        ),
        "good": (
            "Suppose that you were pregnant and a test were available early in the "
            "pregnancy that could detect a serious genetic condition."
        ),
    },
    {
        "id": "relig_truncated_text",
        "expect": "truncated_text",
        "rows": "27,900",
        "outcome": "How much do you agree with this statement?",
        "bad": (
            "You described your religion as Protestant (Baptist, Methodist, "
            "Non-denominational, Lutheran, Presbyterian, Pent"
        ),
        "good": (
            "You described your religion as Protestant (Baptist, Methodist, "
            "Non-denominational, Lutheran, Presbyterian, Pentecostal, Episcopalian, "
            "Reformed, Church of Christ, Jehovah's Witness, etc.)"
        ),
    },
]


def main() -> int:
    cli = jev.client("tess")
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    rows = []
    for case in CASES:
        for kind in ("bad", "good"):
            key = f"{case['id']}:{kind}"
            if key not in cache:
                f = jev.screen_condition(cli, case[kind], case["outcome"], study=case["id"])
                cache[key] = {
                    "chosen": f.defect.value,
                    "confidence": f.defect.confidence,
                    "mass": f.defect_mass,
                    "flagged": f.needs_review,
                }
            rows.append((case, kind, cache[key]))
    CACHE.write_text(json.dumps(cache, indent=1))

    bad = [r for c, k, r in rows if k == "bad"]
    good = [r for c, k, r in rows if k == "good"]
    caught = sum(1 for r in bad if r["flagged"])
    false_pos = sum(1 for r in good if r["flagged"])
    named = sum(1 for c, k, r in rows if k == "bad" and r["chosen"] == c["expect"])

    lines = [
        "# Condition screen — probe against the defects we shipped",
        "",
        "<!-- GENERATED by scripts/condition_probe.py — do not edit by hand. -->",
        "",
        f"**{caught}/{len(bad)} shipped defects flagged. "
        f"{named}/{len(bad)} named by the right class. "
        f"{false_pos}/{len(good)} false positives on the corrected text.**",
        "",
        f"`DEFECT_MASS_REVIEW` is {jev.DEFECT_MASS_REVIEW}. The margin below is what "
        "that threshold has to sit inside — a defect's mass against its own "
        "correction's, with everything else about the text held equal.",
        "",
        "| defect | rows it cost | shipped: class (mass) | corrected: class (mass) | caught |",
        "|---|---|---|---|---|",
    ]
    for case in CASES:
        b = cache[f"{case['id']}:bad"]
        g = cache[f"{case['id']}:good"]
        mark = "yes" if b["flagged"] else "**NO**"
        lines.append(
            f"| `{case['id']}` | {case['rows']} "
            f"| {b['chosen']} ({b['mass']:.2f}) "
            f"| {g['chosen']} ({g['mass']:.2f}) | {mark} |"
        )
    lines += [
        "",
        "A defect the screen misses is not a reason to loosen the threshold — it is a "
        "reason to add a class, or to accept that this particular fault needs a "
        'different check. `a42yg`\'s invented word "equally" is the clearest example: '
        "nothing about that text is unknowable to the respondent, it is simply not what "
        "the source said, so no amount of threshold tuning will find it. That one needs "
        "the source alongside the text, which this screen does not have.",
        "",
    ]
    OUT.write_text("\n".join(lines) + "\n")

    print(
        f"caught {caught}/{len(bad)}  named {named}/{len(bad)}  false pos {false_pos}/{len(good)}"
    )
    for case in CASES:
        b = cache[f"{case['id']}:bad"]
        g = cache[f"{case['id']}:good"]
        print(
            f"  {case['id']:34} bad={b['chosen']:24} {b['mass']:.2f}   "
            f"good={g['chosen']:6} {g['mass']:.2f}"
        )
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
