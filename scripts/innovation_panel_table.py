"""Generate `docs/UKDS_UNBUILT.md` — every Innovation Panel experiment, with a verdict.

The Innovation Panel (UKDS SN 6849) carries **93 experiments** across 17 waves, and
its own User Guide catalogues all of them with the allocation variables named. That is
unlike anything in the Harvard or TESS layers, where each deposit had to be assessed
from scratch. So the screening work here is a single pass over one list, and this file
is the record of it.

Everything except `category`, `verdict`, `reason` and `vignette` is PARSED from the
User Guide — titles from its table of contents, waves and descriptions from its body —
by `scripts/innovation_panel_catalogue.py`, so no title or wave number is transcribed
by hand. The judgement fields are written deliberately, because the point of the file
is that someone decided and can be held to it. The record shape lives in
`micromotives_datasets.innovation_panel`.

The verdicts apply the project's existing rules, nothing new:

- **procedural experiments are out as a class** (28 of them). The condition is how the
  respondent was contacted, paid or interviewed, and the outcome is whether they took
  part at all. There is no (persona, condition, outcome, response) row in that.
- **a visual or physical stimulus is not a stimulus** — the SACJHE ruling, applied to
  showcards, smiley faces, mobile grid layouts, blood samples and app games.
- **the condition must not name the respondent's own persona category** — the X08IVC
  ruling, which is what moved 9.3 out of the build list despite it looking ideal.

`marginal` means assessed and not decided: a reason is recorded and it needs a ruling
before it can move either way. It is deliberately not a third quality tier.

**This file does not claim any of these are buildable.** Every verdict here is a desk
judgement from the guide's own summary. The condition TEXT lives only in each wave's
questionnaire PDF, and whether it is there word-for-word, for a given experiment, is
unverified. That check is the next piece of work and it will move experiments out of
`build`, not into it.

    uv run python scripts/innovation_panel_table.py --write
    uv run python scripts/innovation_panel_table.py --check
"""

from __future__ import annotations

import argparse
import difflib
import sys
from collections.abc import Callable
from pathlib import Path

from micromotives_datasets.innovation_panel import Experiment, load

REPO = Path(__file__).resolve().parents[1]
CATALOGUE = REPO / "data" / "catalog" / "innovation_panel_experiments.json"
OUT = REPO / "docs" / "UKDS_UNBUILT.md"

# Printed headings, in the order they should appear, with what each one covers.
CATEGORIES: dict[str, str] = {
    "attitudes": "Attitudes and politics",
    "wellbeing": "Wellbeing and satisfaction",
    "health": "Health",
    "work-money": "Work, money and expectations",
    "family-care": "Family, care and the household",
    "technology": "Technology and the future",
    "sensitive": "Sensitive questions",
    "consent": "Consent to data linkage",
    "question-form": "The form of the question rather than its content",
    "physical": "Physical measurement and apps",
    "procedural": "Procedural — getting the respondent to take part",
}

VERDICTS = ("build", "marginal", "drop")


def catalogue() -> list[Experiment]:
    """The catalogue, refusing a category this script has no heading for."""
    records = load(CATALOGUE)
    unknown = sorted({r["category"] for r in records} - set(CATEGORIES))
    if unknown:
        raise SystemExit(f"catalogue uses categories with no heading: {unknown}")
    return records


def _wave_count(waves: str) -> int:
    """How many waves an experiment ran in, from the guide's own wave column.

    `All` means every wave, which the guide uses for the incentive experiment.
    Ranges like `1-5` count as the whole range; `2, 3, 4` as three.
    """
    if waves.strip() == "All":
        return 17
    total = 0
    for part in waves.split(","):
        part = part.strip().replace("–", "-")
        if not part:
            continue
        if "-" in part:
            lo, _, hi = part.partition("-")
            try:
                total += int(hi) - int(lo) + 1
            except ValueError:
                total += 1
        else:
            total += 1
    return total


def render(records: list[Experiment]) -> str:
    counts = {v: [r for r in records if r["verdict"] == v] for v in VERDICTS}
    build_waves = sum(_wave_count(r["waves"]) for r in counts["build"])
    multi = [r for r in counts["build"] if _wave_count(r["waves"]) >= 2]
    vignettes = [r for r in records if r["vignette"]]

    out: list[str] = []
    w = out.append

    w("# Innovation Panel experiments, screened\n")
    w(
        "Generated — run `uv run python scripts/innovation_panel_table.py --write`.\n"
        "Source: `data/catalog/innovation_panel_experiments.json`, whose titles and waves\n"
        "are parsed from the Innovation Panel User Guide (UKDS **SN 6849**, waves 1–17,\n"
        "2008–2024). Category and verdict are judgement and are recorded in that file.\n"
    )
    w(
        f"**{len(records)} experiments.** {len(counts['build'])} pass screening, "
        f"{len(counts['marginal'])} need a ruling, {len(counts['drop'])} are out.\n"
    )
    w(
        f"The {len(counts['build'])} that pass span **{build_waves} experiment-waves**, because "
        f"{len(multi)} of them ran in two or more waves — which is the time axis the Harvard "
        "and TESS layers structurally cannot provide.\n"
    )
    w(
        "**Nothing here is claimed to be buildable.** These are desk judgements from the "
        "guide's own summaries. The condition text lives only in each wave's questionnaire "
        "PDF, and whether it is there word-for-word is unverified. That check will move "
        "experiments out of `build`, not into it.\n"
    )
    w(
        "**On the quoted descriptions.** The EUL defines the Data Collection to include "
        'its Documentation, which is why `jev.RESTRICTED` refuses `source="ukds"` and why '
        "the bundle is gitignored. The descriptions below are nonetheless quoted, because "
        "the User Guide is separately published on the open web — it says so itself: "
        '*"we recommend using the web-based version of the Innovation Panel User Guide as '
        'the documentation will develop over time, with the latest versions updated to '
        'these pages"*. Quoting an openly published guide is not redistributing a '
        "safeguarded collection. **No variable label, value label or row from the data "
        "files appears in this file or its catalogue**, and that is the line to hold.\n"
    )

    w("## At a glance\n")
    w("| Verdict | Experiments | Experiment-waves |")
    w("|---|---|---|")
    for v in VERDICTS:
        waves = sum(_wave_count(r["waves"]) for r in counts[v])
        w(f"| `{v}` | {len(counts[v])} | {waves} |")
    w("")

    w("| Category | Build | Marginal | Drop |")
    w("|---|---|---|---|")
    for key, label in CATEGORIES.items():
        rows = [r for r in records if r["category"] == key]
        if not rows:
            continue
        cells = [str(sum(1 for r in rows if r["verdict"] == v)) for v in VERDICTS]
        w(f"| {label} | {' | '.join(cells)} |")
    w("")

    if vignettes:
        w(
            f"**{len(vignettes)} vignette studies** — "
            + ", ".join(f"`{r['id']}`" for r in vignettes)
            + ". These carry prose written by the researchers and shown to respondents "
            "word-for-word, which is the one thing the rest of the corpus is short of: "
            "every conjoint we hold gives attribute levels that we render into sentences "
            "ourselves.\n"
        )

    w("## Experiments spanning two or more waves\n")
    w(
        "The same condition, asked of different people in different years. Holding out a "
        "wave tests whether a model that predicts one year predicts another.\n"
    )
    w("| ID | Waves | Title |")
    w("|---|---|---|")
    for r in sorted(multi, key=lambda r: -_wave_count(r["waves"])):
        w(f"| `{r['id']}` | {r['waves']} | {r['title']} |")
    w("")

    w("## Verdict: `build`\n")
    w(
        "Descriptions are the User Guide's own prose. `allocation` is the variable the "
        "guide names as controlling the condition, where it names one — the rest have to "
        "be found in the data.\n"
    )
    _sections(w, records, "build")

    w("## Verdict: `marginal`\n")
    w(
        "Assessed and not decided. Each needs a ruling before it can move either way; "
        "`9.3` is the one to look at first, because it is otherwise ideal.\n"
    )
    _sections(w, records, "marginal")

    w("## Verdict: `drop`\n")
    w(
        "Listed compactly. The 28 procedural experiments share one reason and do not "
        "repeat it per row.\n"
    )
    for key, label in CATEGORIES.items():
        rows = [r for r in records if r["verdict"] == "drop" and r["category"] == key]
        if not rows:
            continue
        w(f"### {label} ({len(rows)})\n")
        if key == "procedural":
            w(f"> {SECTION_7_REASON}\n")
            w("| ID | Waves | Title |")
            w("|---|---|---|")
            for r in rows:
                w(f"| `{r['id']}` | {r['waves']} | {r['title']} |")
        else:
            w("| ID | Waves | Title | Why not |")
            w("|---|---|---|---|")
            for r in rows:
                w(f"| `{r['id']}` | {r['waves']} | {r['title']} | {r['reason']} |")
        w("")

    return "\n".join(out) + "\n"


SECTION_7_REASON = (
    "The condition is how the respondent was contacted, paid or interviewed, and the "
    "outcome is whether they took part at all rather than an answer they gave. There is "
    "no (persona, condition, outcome, response) row in that."
)


def _sections(w: Callable[[str], None], records: list[Experiment], verdict: str) -> None:
    """One entry per experiment, as prose rather than a table.

    A table cannot carry a description without becoming unreadable, and the
    description is the point of this file — the id and title alone do not tell
    anyone what the experiment did.
    """
    for key, label in CATEGORIES.items():
        rows = [r for r in records if r["verdict"] == verdict and r["category"] == key]
        if not rows:
            continue
        w(f"### {label} ({len(rows)})\n")
        for r in rows:
            flag = " — VIGNETTE" if r["vignette"] else ""
            w(f"**`{r['id']}` {r['title']}{flag}**  ")
            plural = "wave" if _wave_count(r["waves"]) == 1 else "waves"
            meta = [f"{plural} {r['waves']}" if r["waves"] else "waves unrecorded"]
            if r["allocation_vars"]:
                meta.append("allocation " + ", ".join(f"`{v}`" for v in r["allocation_vars"]))
            w(" · ".join(meta) + "  ")
            if r["description"]:
                w(r["description"])
            # A pruned reason means the title and description already said it.
            if r["reason"]:
                w(f"\n*Assessed:* {r['reason']}")
            w("")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="write docs/UKDS_UNBUILT.md")
    group.add_argument("--check", action="store_true", help="fail if the file on disk is stale")
    args = parser.parse_args()

    rendered = render(catalogue())

    if args.write:
        OUT.write_text(rendered)
        print(f"wrote {OUT.relative_to(REPO)} ({len(rendered.splitlines())} lines)")
        return 0

    if not OUT.exists():
        print(f"{OUT.relative_to(REPO)} does not exist; run --write", file=sys.stderr)
        return 1
    current = OUT.read_text()
    if current == rendered:
        print(f"{OUT.relative_to(REPO)} is up to date")
        return 0
    sys.stderr.writelines(
        difflib.unified_diff(
            current.splitlines(keepends=True),
            rendered.splitlines(keepends=True),
            fromfile="on disk",
            tofile="regenerated",
        )
    )
    print(f"\n{OUT.relative_to(REPO)} is STALE — run --write", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
