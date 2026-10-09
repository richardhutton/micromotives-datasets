#!/usr/bin/env python3
"""Can each Innovation Panel experiment actually be built? Checked, not assumed.

`SocSci-UK_MASTER.md` calls this "the largest unknown left, and resolving it can
only move the count down". The 44 build verdicts in
`data/catalog/innovation_panel_experiments.json` are DESK judgements made from
the User Guide's one-line summaries. Exactly one of them -- 9.10 -- has been
tested against the data and the questionnaire, and testing it found that the
summary was wrong about who stood in the scenario.

So this checks the four things a build needs, per experiment:

1. **The User Guide names an allocation variable.** Without one there is no
   condition, and the experiment cannot be a (persona, condition, outcome,
   response) row at all.
2. **That variable exists in the file the guide says it is in.** The guide is
   specific -- "in file p_hhsamp_ip" -- and specific claims can be checked.
   9.10's entry was right; the catalogue's own summary of it was not.
3. **The arms are documented with their meanings.** "1 = Wave 8 version, 2 =
   Wave 10 version" is a condition. A bare count of groups is not.
4. **The wave questionnaire carries the question wording.** This is the one that
   decides whether a build produces real stimulus text or an invention. The
   archived value labels cannot stand in: in 9.10 two opposite housework splits
   shared one label string.

A FAIL here is a real finding and the experiment drops out of the plan. A PASS
means worth starting, not finished -- 9.10 passed every check here and still took
a session to find that paid-help lived only in the household file.

    uv run python scripts/ip_triage.py                # the 16 selected
    uv run python scripts/ip_triage.py --all          # all 44 build-verdict
    uv run python scripts/ip_triage.py --id 9.43      # just one, with its text
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import warnings
from pathlib import Path

import pyreadstat

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "data" / "raw" / "ukds_6849" / "mrdoc" / "pdf"
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"
CATALOGUE = REPO / "data" / "catalog" / "innovation_panel_experiments.json"
CACHE = REPO / "data" / "raw" / "ukds_6849" / ".triage_text"

WAVES = "abcdefghijklmnopq"

# The selection in docs/STATUS.md section 3, in build order.
SELECTED = [
    "9.4", "9.43", "9.48", "9.17", "9.24", "9.18", "9.36",
    "9.20", "9.31", "9.12", "9.42", "9.39",
    "9.13", "9.11", "9.9", "9.47",
]

# A variable the guide names.
#
# The first version of this looked only for `ff_`-prefixed names, on the
# reasoning that fed-forward is the panel's convention for a household-level
# allocation. It is the convention for SOME of them, and that assumption
# produced five false FAILs -- including 9.39, whose allocation variables are
# `fsvigname1`, `fsvigparent1` and so on, named perfectly clearly in the guide
# with their arms written out underneath ("1 = Charlotte Davies"). A triage that
# drops good experiments because of a guessed prefix is worse than no triage.
#
# So two signals are used instead of a prefix, and both are the guide's own:
# a `ff_` name anywhere in the prose, and a line that is JUST an identifier,
# which is how the guide lays out an allocation variable before listing its
# arms. Everything found is then checked against the real columns, so a prose
# word that happens to look like an identifier does not survive.
# The optional `[a-q]_` wave prefix is load-bearing: `_` is a word character, so
# `\bff_` never matches inside `d_ff_fertw4`, and 9.9 was failed for having no
# allocation variable when the guide names one in plain sight.
ALLOC = re.compile(r"\b(?:[a-q]_)?ff_[a-z0-9_]+\b", re.I)
LONE_IDENT = re.compile(r"^[ \t]*([a-z][a-z0-9_]{3,})[ \t]*$", re.M | re.I)
# "eq5dcond on record k_indresp_ip:" -- the guide's other way of naming the
# controlling variable, and the fifth thing this script missed. 9.24 was failed
# for naming no allocation variable while naming it in the clearest sentence in
# its section.
ON_RECORD = re.compile(r"\b([a-z][a-z0-9_]{3,})\s+(?:on|in)\s+(?:record|file)\b", re.I)
# "in file p_hhsamp_ip" / "on record w_indresp_ip"
FILE_REF = re.compile(r"\b([a-q]|w)_(hhsamp|indresp|indall|hhresp)_ip\b", re.I)
# A documented arm meaning. Three layouts, because the guide uses all three and
# only the first was handled at first -- 9.9 writes "Group 1  Version A (before
# friendship questions)", which is as clear a condition as anything in the
# document and was being scored as undocumented.
ARM = re.compile(
    r"^[ \t]*(?:(\d)[ \t]*[=:][ \t]*\S"        # 1 = Wave 8 version
    r"|Group[ \t]+(\d)[ \t]+\S"                  # Group 1  Version A
    r"|(\d)[ \t]{2,}[A-Z]\S)",                    # 1    Version A
    re.M,
)


def pdftext(pdf: Path) -> str:
    """Cached `pdftotext -layout`. The questionnaires are 400-900 pages each."""
    CACHE.mkdir(exist_ok=True)
    out = CACHE / (pdf.stem + ".txt")
    if not out.exists():
        subprocess.run(["pdftotext", "-layout", str(pdf), str(out)], check=True)
    return out.read_text(errors="ignore")


def guide_sections() -> dict[str, str]:
    """The User Guide split into its numbered experiment sections.

    The guide carries each experiment twice: once as a row in a summary table and
    once as a full section. The full section is the one that names variables and
    files, so sections are taken as the LONGEST block under each heading.
    """
    text = pdftext(DOC / "6849_innovation_panel_user_guide.pdf")
    # `^[ \t]*` and not `^`: pdftotext keeps the page's left margin, so the real
    # section heading for 9.24 is " 9.24 Variations of the EQ-5D questions" with
    # a leading space. Anchoring hard at the line start matched only the
    # contents-table row, and 9.24 was failed for naming no allocation variable
    # while its real section names `eq5dcond` and all three of its arms.
    heads = list(re.finditer(r"^[ \t]*(\d+\.\d+)\s+(\S.*)$", text, re.M))
    best: dict[str, str] = {}
    for n, head in enumerate(heads):
        body = text[head.end() : heads[n + 1].start() if n + 1 < len(heads) else len(text)]
        key = head.group(1)
        # The guide prints each experiment twice: a row in a summary table and a
        # full section. Taking the longest block picked a TABLE fragment for
        # 9.24 -- three bullet points and no variables -- because the table row
        # ran further before the next heading than the real section did. A
        # section has to be prose, so one that never reaches a full stop is not
        # one.
        if "." not in body[:600]:
            continue
        if len(body) > len(best.get(key, "")):
            best[key] = body
    return best


def wave_letters(waves: str) -> list[str]:
    out = []
    for part in str(waves).replace(" ", "").split(","):
        if part.isdigit() and 1 <= int(part) <= 17:
            out.append(WAVES[int(part) - 1])
    return out


def columns_of(path: Path) -> set[str]:
    for enc in (None, "cp1252", "latin1"):
        try:
            _, meta = (
                pyreadstat.read_dta(str(path), metadataonly=True)
                if enc is None
                else pyreadstat.read_dta(str(path), metadataonly=True, encoding=enc)
            )
            return {c.lower() for c in meta.column_names}
        except Exception:  # try the next encoding
            continue
    return set()


def questionnaire_for(letter: str) -> Path | None:
    wave = WAVES.index(letter) + 1
    for pattern in (
        f"6849_ip_wave_{wave}_questionnaire*.pdf",
        f"6849_innovation_panel_wave_{wave}_questionnaire*.pdf",
    ):
        found = sorted(DOC.glob(pattern))
        if found:
            return found[0]
    return None


def triage(exp: dict, section: str) -> dict:
    """Four checks. Returns what was found, not a verdict dressed as a fact."""
    letters = wave_letters(exp["waves"])
    names = sorted(
        {m.group(0).lower() for m in ALLOC.finditer(section)}
        | {m.group(1).lower() for m in LONE_IDENT.finditer(section)}
        | {m.group(1).lower() for m in ON_RECORD.finditer(section)}
    )
    files = sorted({m.group(2).lower() for m in FILE_REF.finditer(section)})
    arms = len(set(ARM.findall(section)))

    # 2. does a named allocation variable exist in the data?
    found_in: dict[str, str] = {}
    for letter in letters:
        # Both files are always searched. The guide's "in file p_indresp_ip" is
        # usually right, and in 9.10 it was right about the four dimensions it
        # mentioned and silent about the fifth, which lived only in hhsamp.
        for stem in ("hhsamp", "indresp", "indall"):
            path = STATA / f"{letter}_{stem}_ip.dta"
            if not path.exists():
                continue
            cols = columns_of(path)
            for name in names:
                for candidate in (name, f"{letter}_{name}"):
                    if candidate.lower() in cols:
                        found_in.setdefault(name, f"{letter}_{stem}_ip")

    # 4. does the questionnaire mention the experiment's own variables?
    q_hits: dict[str, int] = {}
    for letter in letters:
        pdf = questionnaire_for(letter)
        if not pdf:
            q_hits[letter] = -1
            continue
        text = pdftext(pdf).lower()
        stems = {n.lower().replace("ff_", "").rstrip("0123456789") for n in names}
        stems = {s for s in stems if len(s) > 4}
        q_hits[letter] = sum(1 for s in stems if s in text)

    return {
        "id": exp["id"],
        "title": exp["title"],
        "category": exp["category"],
        "waves": exp["waves"],
        "alloc_named": names,
        "alloc_found": found_in,
        "files_named": files,
        "arms_documented": arms,
        "questionnaire": q_hits,
        "section_chars": len(section),
    }


def verdict(r: dict) -> tuple[str, str]:
    if not r["alloc_named"]:
        return "FAIL", "the guide names no allocation variable"
    if not r["alloc_found"]:
        return "FAIL", f"named {len(r['alloc_named'])} variable(s), none found in the data"
    if r["arms_documented"] < 2:
        return "CHECK", "fewer than 2 arm meanings written out in the guide"
    if all(v <= 0 for v in r["questionnaire"].values()):
        return "CHECK", "no questionnaire hit on the experiment's own variable names"
    return "PASS", f"{len(r['alloc_found'])} allocation variable(s) located"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--all", action="store_true", help="every build-verdict experiment")
    ap.add_argument("--id", help="one experiment, printing its User Guide section")
    args = ap.parse_args()

    raw = json.loads(CATALOGUE.read_text())
    exps = {x["id"]: x for x in (raw["experiments"] if isinstance(raw, dict) else raw)}
    sections = guide_sections()

    if args.id:
        exp = exps[args.id]
        section = sections.get(args.id, "")
        r = triage(exp, section)
        state, why = verdict(r)
        print(f"{state}  {r['id']}  {r['title']}\n  {why}\n")
        print(json.dumps({k: v for k, v in r.items() if k != "title"}, indent=2))
        print("\n--- User Guide section ---\n")
        print(section[:3000])
        return

    wanted = (
        [x for x in exps.values() if x["verdict"] == "build"]
        if args.all
        else [exps[i] for i in SELECTED]
    )
    results = []
    print(f"{'':6}{'id':<6}{'cat':<14}{'wv':<10}{'alloc':>6}{'arms':>6}  title")
    for exp in wanted:
        r = triage(exp, sections.get(exp["id"], ""))
        state, why = verdict(r)
        r["verdict"], r["why"] = state, why
        results.append(r)
        print(
            f"{state:<6}{r['id']:<6}{r['category'][:13]:<14}{str(r['waves'])[:9]:<10}"
            f"{len(r['alloc_found']):>6}{r['arms_documented']:>6}  {r['title'][:44]}"
        )
    out = REPO / "data" / "catalog" / "ip_triage.json"
    out.write_text(json.dumps(results, indent=2) + "\n")
    tally: dict[str, int] = {}
    for r in results:
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
    print(f"\n{tally}   -> {out.relative_to(REPO)}")
    for r in results:
        if r["verdict"] != "PASS":
            print(f"  {r['verdict']} {r['id']}: {r['why']}")


if __name__ == "__main__":
    main()
