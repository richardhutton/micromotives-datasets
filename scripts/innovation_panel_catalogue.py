"""Build `data/catalog/innovation_panel_experiments.json` from the UKDS User Guide.

The Innovation Panel's own User Guide catalogues all 93 of its experiments, with
each one's waves, a prose description, and frequently the allocation variable
name outright. So `title`, `waves`, `description` and `allocation_vars` are all
PARSED from it rather than transcribed — a 93-row table typed by hand would be
wrong somewhere and nothing would catch it.

What is NOT parsed is `category`, `verdict`, `reason` and `vignette`. Those are
judgement, they live in this file as literals, and that is deliberate: the value
of the catalogue is that somebody decided, in writing, and can be held to it.
`scripts/innovation_panel_table.py` renders the result to `docs/UKDS_UNBUILT.md`.

**Needs the local UKDS bundle**, which is licensed and gitignored, so this runs
only on a machine that has downloaded SN 6849. It shells out to `pdftotext`
(poppler) and caches the extracted text beside the bundle. Nothing leaves the
machine: see `jev.RESTRICTED`, which refuses `source="ukds"` outright.

    uv run python scripts/innovation_panel_catalogue.py
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "data" / "raw" / "ukds_6849"
GUIDE = BUNDLE / "mrdoc" / "pdf" / "6849_innovation_panel_user_guide.pdf"
UG = BUNDLE / "user_guide.txt"
OUT = REPO / "data" / "catalog" / "innovation_panel_experiments.json"


def guide_text() -> list[str]:
    """The User Guide as layout-preserving text, extracted once and cached.

    `-layout` is load-bearing rather than cosmetic: the overview table puts an
    experiment's title, summary and wave columns on one physical line, and the
    wave can only be recovered as the last whitespace-separated field of it.
    """
    if not UG.exists():
        if not GUIDE.exists():
            raise SystemExit(
                f"{GUIDE.relative_to(REPO)} is missing. This needs the local UKDS "
                "SN 6849 bundle, which is licensed and not in the repository."
            )
        subprocess.run(["pdftotext", "-layout", str(GUIDE), str(UG)], check=True)
    return UG.read_text().splitlines()

# Waves the table parse could not reach, read from each experiment's own section.
WAVES_BY_HAND = {
    "9.3": "5",
    "9.42": "16",
    "9.43": "16",
    "9.44": "16",
    "9.45": "16",
    "9.46": "17",
    "9.47": "17",
    "9.48": "17",
    "9.49": "17",
    "9.50": "17",
}

BUILD, MARGINAL, DROP = "build", "marginal", "drop"

# Experiments whose stimulus is researcher-written prose shown to respondents
# word-for-word. This is a FIELD rather than a note inside `reason`, because it
# is the single most important property for our purposes and a flag buried in
# prose gets lost — it did: pruning redundant reasons silently removed the
# "VIGNETTE" marker from three of the four, because those reasons restated
# titles that already contained the word "Vignettes".
VIGNETTES = {"9.10", "9.26", "9.30", "9.39"}

# (category, verdict, reason) per experiment. Sections 8 and 9 are assessed one by
# one; section 7 is ruled out as a class and says so once.
JUDGEMENT: dict[str, tuple[str, str, str]] = {
    # -- section 8: the form of the question rather than its content -----------
    "8.1": ("question-form", MARGINAL, "random subsets get different content, so there is no shared outcome to compare"),
    "8.2": ("question-form", DROP, "showcards are a visual stimulus, not text"),
    "8.3": ("question-form", BUILD, "question wording and context, varied in words"),
    "8.4": ("question-form", BUILD, "dependent interviewing wording"),
    "8.5": ("question-form", BUILD, "branched vs unbranched rating scales"),
    "8.6": ("question-form", DROP, "smiley faces are a visual stimulus, not text"),
    "8.7": ("question-form", DROP, "the condition is the interview mode, not words"),
    "8.8": ("question-form", BUILD, "prompts to reduce item non-response, varied in words"),
    "8.9": ("question-form", MARGINAL, "MTMM repeated-measures design; the condition is a measurement model, not a wording"),
    "8.10": ("question-form", BUILD, "classic response-order effects"),
    "8.11": ("question-form", BUILD, "answer scale direction reversed"),
    "8.12": ("question-form", MARGINAL, "tailored question selection; needs checking that a shared outcome exists"),
    "8.13": ("question-form", DROP, "mobile grid layout is a visual stimulus, not text"),
    "8.14": ("question-form", BUILD, "presentation of don't know / prefer not to answer"),
    "8.15": ("question-form", DROP, "outcome is whether a phone number was given, not a survey answer"),
    # -- section 9: substantive topics ----------------------------------------
    "9.1": ("work-money", MARGINAL, "one condition uses a showcard to trigger recall, so part of the stimulus is visual"),
    "9.2": ("wellbeing", MARGINAL, "mixes scale points and labelling (buildable) with showcards and mode (not)"),
    "9.3": ("wellbeing", MARGINAL, "X08IVC: the condition asks the respondent to compare themselves to others of their own gender or education, naming their own persona category"),
    "9.4": ("attitudes", BUILD, "asked about your profession vs your occupation; pure wording"),
    "9.5": ("work-money", BUILD, "wealth asked aggregate vs itemised, 2x2 with who reports"),
    "9.6": ("consent", BUILD, "consent asked in context vs at the end, 2x2"),
    "9.7": ("question-form", MARGINAL, "the outcome is a preference about survey mode, not a substantive answer"),
    "9.8": ("physical", DROP, "meter readings; no text stimulus"),
    "9.9": ("family-care", BUILD, "context effects in fertility decisions"),
    "9.10": ("family-care", BUILD, "respondents rate a described couple, not themselves"),
    "9.11": ("work-money", BUILD, "subjective expectations about the returns to higher education"),
    "9.12": ("health", BUILD, "measuring change in self-assessed disability"),
    "9.13": ("work-money", BUILD, "time and risk preference choices"),
    "9.14": ("attitudes", BUILD, "how people think about environmental taxes"),
    "9.15": ("health", DROP, "the outcome is the interviewer's rating, not the respondent's answer"),
    "9.16": ("attitudes", BUILD, "social desirability bias in attitudes towards immigration"),
    "9.17": ("sensitive", BUILD, "sexual identity asked directly vs indirectly"),
    "9.18": ("wellbeing", BUILD, "a substantive attitude, asked eight years apart"),
    "9.19": ("work-money", MARGINAL, "a module redesign; needs checking that conditions share an outcome"),
    "9.20": ("wellbeing", BUILD, "presentation of response options in satisfaction questions"),
    "9.21": ("consent", BUILD, "consent to link to the electoral register"),
    "9.22": ("work-money", BUILD, "financial management within couples"),
    "9.23": ("family-care", BUILD, "two versions of questions on non-resident parents and separation"),
    "9.24": ("health", BUILD, "EQ-5D-3L and EQ-5D-5L variants, three groups"),
    "9.25": ("consent", BUILD, "HMRC linkage consent, easy vs difficult wording"),
    "9.26": ("attitudes", BUILD, "two sets of questions: a conjoint and a set of vignettes"),
    "9.27": ("health", DROP, "the condition is interviewer-asked vs self-completion, which is mode"),
    "9.28": ("physical", DROP, "blood, blood spot and hair samples"),
    "9.29": ("consent", BUILD, "LinkedIn consent, placement crossed with a motivational statement"),
    "9.30": ("technology", BUILD, "automation threat severity x timeframe, 2x2"),
    "9.31": ("health", BUILD, "ReQoL-10 against other scales, randomised order"),
    "9.32": ("family-care", MARGINAL, "proxy nomination; needs checking that a respondent answer is the outcome"),
    "9.33": ("consent", BUILD, "Twitter consent"),
    "9.34": ("work-money", BUILD, "marginal propensity to consume"),
    "9.35": ("family-care", BUILD, "informal care"),
    "9.36": ("health", BUILD, "alcohol consumption"),
    "9.37": ("physical", DROP, "body measurement app"),
    "9.38": ("attitudes", BUILD, "national identity"),
    "9.39": ("family-care", BUILD, "homeworking and gender inequality in the labour market"),
    "9.40": ("attitudes", BUILD, "cognitive reflection and politically motivated reasoning"),
    "9.41": ("attitudes", BUILD, "robustness of climate change worry measurement"),
    "9.42": ("attitudes", BUILD, "understanding of the long-term future"),
    "9.43": ("health", BUILD, "versions of the mental health questions"),
    "9.44": ("physical", DROP, "outcome is whether photographs were supplied"),
    "9.45": ("physical", DROP, "mobile app game"),
    "9.46": ("consent", BUILD, "DWP consent decision process"),
    "9.47": ("family-care", BUILD, "standard vs activity-based identification of informal caregiving"),
    "9.48": ("work-money", BUILD, "labour market expectations"),
    "9.49": ("consent", BUILD, "consent to place in-home sensors"),
    "9.50": ("consent", BUILD, "consent to link smart meter data"),
}

SECTION_7_REASON = (
    "procedural: the condition is how the respondent was contacted, paid or "
    "interviewed, and the outcome is whether they took part at all rather than "
    "an answer they gave. Nothing here fits (persona, condition, outcome, response)."
)


def parse_bodies(lines: list[str]) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Each experiment's own description, and any allocation variable it names.

    The guide gives every experiment a prose section of its own, which is a far
    better description than the overview table's telegraphic summary — and it
    frequently names the allocation variable outright, e.g. 9.3's "The variable
    e_ff_lifesatw5 on the record e_hhsamp_ip controls allocation to versions of
    this question". Capturing that here means the build does not have to go
    hunting for it later.
    """
    # The body sections begin after the overview table, which ends with section
    # 10's rows around line 3500. Table rows are wide (title and summary and wave
    # on one line) and body headings are narrow, so width separates them; some
    # body headings carry a single leading space, so one is allowed.
    heads: list[tuple[int, str]] = []
    for i, ln in enumerate(lines):
        if i < 3510 or ln.startswith("  ") or len(ln) > 110:
            continue
        if m := re.match(r"^ ?(\d+\.\d+)\s+\S.*$", ln):
            heads.append((i, m.group(1)))

    alloc = re.compile(r"\b([a-q]_ff_[a-z0-9_]+|[a-q]_[a-z][a-z0-9_]*w\d+)\b")
    descriptions: dict[str, str] = {}
    variables: dict[str, list[str]] = {}
    for k, (i, num) in enumerate(heads):
        if num in descriptions:
            continue  # first occurrence is the section; later ones are cross-references
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        body = re.sub(r"\s+", " ", " ".join(x.strip() for x in lines[i + 1 : end])).strip()
        descriptions[num] = _first_sentences(body)
        if found := sorted(set(alloc.findall(body))):
            variables[num] = found
    return descriptions, variables


def prune_reason(reason: str, title: str, verdict: str) -> str:
    """Drop a `build` reason that only restates the title.

    Every experiment got a written reason during screening, which was right:
    deciding in writing is the point. But once the guide's own description is
    carried alongside, a reason reading "social desirability bias in attitudes
    towards immigration" under a title reading "Social desirability bias in
    attitudes towards immigration" is pure noise, and noise in a screening
    document is what stops people reading it.

    A `marginal` or `drop` reason is never pruned — that is the whole record of
    why something is not being built, and it has to survive.
    """
    if verdict != BUILD or not reason:
        return reason
    words = set(re.findall(r"[a-z]{4,}", reason.lower()))
    in_title = {w for w in words if w in title.lower()}
    if words and len(in_title) / len(words) >= 0.7:
        return ""
    return reason


def describe(description: str, title: str) -> str:
    """The guide's own description, or "" if what was captured is not one.

    Order matters: the wrapped-title tail comes off FIRST, because a body that
    begins "residency rights of immigrants? This study contains..." starts
    lowercase only because its own heading wrapped. Only after that does a
    lowercase start mean the capture genuinely landed mid-paragraph — which
    happens for 7.2, whose heading sits inside 7.1's prose rather than starting
    a section. A description reading "for the continuing sample is as follows:
    Groups 1-12, 13, 16..." is worse than none: it reads like a statement about
    the experiment and is not one.
    """
    stripped = strip_title_tail(description, title)
    return stripped if stripped[:1].isupper() else ""


def strip_title_tail(description: str, title: str) -> str:
    """Drop the tail of a heading that wrapped onto the line below it.

    A long heading like "9.26 Does competition over public services decrease
    support for residency rights of immigrants?" is split across two lines, so
    the body text begins with "residency rights of immigrants?" — the remainder
    of its own title. Match the longest word-wise suffix of the title that the
    body starts with, and remove it.
    """
    words = title.split()
    for start in range(len(words)):
        tail = " ".join(words[start:])
        if tail and description.lower().startswith(tail.lower()):
            return description[len(tail) :].strip()
    return description


def _first_sentences(body: str, limit: int = 300) -> str:
    """Enough of the guide's prose to know what the experiment did, ending cleanly."""
    out = ""
    for sentence in re.split(r"(?<=[.!?]) ", body):
        if out and len(out) + len(sentence) + 1 > limit:
            break
        out = f"{out} {sentence}".strip()
    return out or body[:limit]


def parse_guide(lines: list[str]) -> tuple[dict[str, str], list[str], dict[str, str]]:
    """Titles from the table of contents, waves from the overview table.

    Titles come from the contents rather than the body headings because the
    contents gives each one complete on (at most) two lines, whereas a body
    heading can wrap mid-phrase in the middle of a page.
    """
    toc: dict[str, str] = {}
    order: list[str] = []
    last: str | None = None
    skip = re.compile(
        r"^(\d+\.|Allocations|Modules|Inclusion|Follow|Error|Template|Format|"
        r"Prenotification|Logo|Include|Explain|Collecting|.Early)"
    )
    for ln in lines[99:245]:
        s = ln.strip()
        if m := re.match(r"^(\d+\.\d+)\s+(.*)$", s):
            num, rest = m.groups()
            toc[num] = re.sub(r"[. ]*\d+$", "", rest).strip(" .")
            order.append(num)
            last = num
        elif s and last and not skip.match(s):
            cont = re.sub(r"[. ]*\d+$", "", s).strip(" .")
            if cont and len(cont) < 70:
                toc[last] = f"{toc[last]} {cont}".strip()

    waves: dict[str, str] = {}
    for ln in lines[2915:3465]:
        if not (m := re.match(r"^\s*(\d+\.\d+)\s+\S", ln)):
            continue
        tail = re.split(r"\s{2,}", ln.rstrip().strip())[-1]
        if re.fullmatch(r"(All|\d+(\s*[-–,.]\s*\d+)*)", tail):
            waves[m.group(1)] = tail.replace(".", ",")
    waves.update(WAVES_BY_HAND)
    return toc, order, waves


def main() -> None:
    lines = guide_text()
    toc, order, waves = parse_guide(lines)
    descriptions, variables = parse_bodies(lines)
    records = []
    for num in order:
        section = int(num.split(".")[0])
        if section not in (7, 8, 9):
            continue
        if section == 7:
            category, verdict, reason = "procedural", DROP, SECTION_7_REASON
        elif num not in JUDGEMENT:
            raise SystemExit(f"{num} has no judgement recorded: {toc.get(num)!r}")
        else:
            category, verdict, reason = JUDGEMENT[num]
        records.append(
            {
                "id": num,
                "title": toc[num],
                "category": category,
                "waves": waves.get(num, ""),
                "verdict": verdict,
                "reason": prune_reason(reason, toc[num], verdict),
                "description": describe(descriptions.get(num, ""), toc[num]),
                "vignette": num in VIGNETTES,
                "allocation_vars": variables.get(num, []),
            }
        )
    unknown = sorted(set(JUDGEMENT) - {r["id"] for r in records})
    if unknown:
        raise SystemExit(f"judgement recorded for ids not in the guide: {unknown}")
    OUT.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(records)} experiments to {OUT}")
    for v in (BUILD, MARGINAL, DROP):
        n = sum(1 for r in records if r["verdict"] == v)
        print(f"  {v:<9} {n}")


if __name__ == "__main__":
    main()
