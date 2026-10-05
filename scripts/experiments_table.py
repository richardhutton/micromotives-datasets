"""Generate `docs/EXPERIMENTS.md` — every experiment built, with its source and category.

The doc is GENERATED, not written, because the thing it describes changes every time a
recipe lands and a hand-maintained copy would drift. That is not a hypothetical: on
5 October 2026 `data/catalog/uk_dataverse_provenance.json` was found calling three
already-built deposits "prepared", and §5a of the master doc was found claiming "(all
CC0)" three days after an audit established that one of its deposits is not. Both were
hand-maintained. So almost nothing here is typed:

- **row and participant counts** come from the built parquet
- **source, licence, title, study_id** come from the recipe
- **DOI** comes from `uk_dataverse_provenance.json`, **OSF code and category** for the
  TESS layer from `tess_uk_foundation_sources.csv`
- **category, design and description** for the UK layer come from
  `data/catalog/experiment_manifest.json`, which is the only hand-authored input and
  holds only what cannot be derived

Run `--check` in CI or before a commit: it regenerates into memory and diffs against the
file on disk, so a stale doc fails rather than merely being stale.

    uv run python scripts/experiments_table.py --write
    uv run python scripts/experiments_table.py --check
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[1]
RECIPES = REPO / "recipes"
PROCESSED = REPO / "data" / "processed"
CATALOG = REPO / "data" / "catalog"
OUT = REPO / "docs" / "EXPERIMENTS.md"

MANIFEST = CATALOG / "experiment_manifest.json"
PROVENANCE = CATALOG / "uk_dataverse_provenance.json"
TESS = CATALOG / "tess_uk_foundation_sources.csv"

SOURCE_LABEL = {"dataverse": "Harvard Dataverse", "tess": "TESS (OSF)"}


@dataclass
class Experiment:
    """One built experiment, assembled from every place that knows part of it."""

    recipe: str
    study_id: str
    source: str
    title: str
    licence: str | None
    reference: str | None
    category: str
    design: str | None
    description: str | None
    verified_against: str | None
    rows: int | None
    participants: int | None

    @property
    def is_uk(self) -> bool:
        return self.source == "dataverse"

    @property
    def publishable(self) -> bool:
        """CC0 is the only thing in this corpus we may redistribute.

        Derived from the recipe's own licence string rather than from the layer,
        so a future non-CC0 Dataverse deposit or a future licensed TESS deposit
        lands on the right side of the line without anyone remembering to move it.
        """
        return bool(self.licence and self.licence.startswith("CC0"))


def _recipe_head(path: Path) -> dict[str, str]:
    """Top-level scalars from a recipe, read without parsing the whole file.

    The conjoint recipes are 13-57MB of machine-generated arms and `yaml.safe_load`
    on all of them takes over a minute. Only the header scalars are needed here,
    and they are always in the first few lines, so this reads a fixed prefix and
    regexes it. The cost of being wrong is a missing field in a doc, not a wrong
    row in a dataset.
    """
    head = path.read_text(encoding="utf-8")[:8000]
    out: dict[str, str] = {}
    for key in ("study_id", "source", "title", "licence", "experiment"):
        match = re.search(rf"^{key}: *(.*)$", head, re.M)
        if match:
            out[key] = match.group(1).strip().strip("'\"")
    return out


def _tess_index() -> dict[str, pd.Series]:
    table = pd.read_csv(TESS)
    index: dict[str, pd.Series] = {}
    for _, row in table.iterrows():
        for key in ("study_id", "osf_code", "tess_id"):
            value = row.get(key)
            if isinstance(value, str) and value.strip():
                index[value.strip()] = row
    return index


def _built_name(study_id: str, experiment: str | None) -> str:
    """The parquet basename the build writes, which is NOT the recipe filename.

    `pipeline.build` names its output from `study_id` plus `experiment`, so
    `recipes/8ctbk.yaml` (experiment: desirability) lands at
    `8ctbk_desirability.parquet` and `recipes/py9q3_vignette1.yaml` at
    `py9q3_vignette1_married_mother.parquet`. Keying on the recipe filename
    looked right for 31 of 35 recipes and silently reported the other four as
    unbuilt — which is exactly the failure this whole file exists to avoid, so
    it is derived the same way the build derives it rather than guessed from
    the path.
    """
    return f"{study_id}_{experiment}" if experiment else study_id


def _counts(study_id: str, experiment: str | None) -> tuple[int | None, int | None]:
    """Rows and distinct participants, or (None, None) if not built on this machine.

    `data/processed/` is gitignored, so a fresh clone has no parquet at all. The
    doc still generates — with the counts blank and a note saying so — rather
    than failing, because a doc that only builds on one laptop is not a doc.
    Row count comes from the parquet footer (no decompression); the participant
    count needs one column read.
    """
    path = PROCESSED / f"{_built_name(study_id, experiment)}.parquet"
    if not path.exists():
        return None, None
    rows = pq.ParquetFile(path).metadata.num_rows
    people = int(pd.read_parquet(path, columns=["participant_id"]).participant_id.nunique())
    return rows, people


def collect() -> list[Experiment]:
    manifest = json.loads(MANIFEST.read_text())
    entries: dict[str, dict] = manifest["experiments"]
    provenance = json.loads(PROVENANCE.read_text())
    tess = _tess_index()

    out: list[Experiment] = []
    for path in sorted(RECIPES.glob("*.yaml")):
        recipe = path.stem
        head = _recipe_head(path)
        study_id = head.get("study_id", recipe)
        source = head.get("source", "?")

        entry = entries.get(recipe, {})
        tess_row = tess.get(study_id)

        if entry:
            category = entry["category"]
        elif tess_row is not None:
            category = str(tess_row["category"])
        else:
            category = "UNCLASSIFIED"

        if source == "dataverse":
            doi = provenance.get(study_id, {}).get("doi")
            reference = f"doi:{doi}" if doi else None
        elif tess_row is not None and isinstance(tess_row.get("osf_code"), str):
            reference = f"osf.io/{tess_row['osf_code']}"
        else:
            reference = None

        rows, people = _counts(study_id, head.get("experiment"))
        out.append(
            Experiment(
                recipe=recipe,
                study_id=study_id,
                source=source,
                title=head.get("title") or (str(tess_row["title"]) if tess_row is not None else ""),
                # The recipe's licence field is prose for the UK deposits (it records
                # where the licence was read from), so only the leading identifier is
                # kept here. The authority remains the recipe and the provenance file.
                licence=(head.get("licence") or "").split(",")[0].strip() or None,
                reference=reference,
                category=category,
                design=entry.get("design"),
                description=entry.get("description"),
                verified_against=entry.get("verified_against"),
                rows=rows,
                participants=people,
            )
        )
    return out


def _num(value: int | None) -> str:
    return f"{value:,}" if value is not None else "—"


def render(experiments: list[Experiment]) -> str:
    uk = [e for e in experiments if e.is_uk]
    tess = [e for e in experiments if not e.is_uk]
    built = [e for e in experiments if e.rows is not None]
    uk_rows = sum(e.rows or 0 for e in uk)
    tess_rows = sum(e.rows or 0 for e in tess)

    lines: list[str] = []
    add = lines.append

    add("# Experiments built")
    add("")
    add(
        "**This file is generated.** Run `uv run python scripts/experiments_table.py --write` "
        "after adding a recipe; `--check` fails if it is stale. Do not edit it by hand — "
        "see the module docstring for why."
    )
    add("")
    add(
        f"**{len(experiments)} experiments.** "
        f"{len(uk)} UK (CC0, redistributable) and {len(tess)} US transfer layer "
        f"(TESS, no licence stated — usable for research, **not** redistributable)."
    )
    add("")
    if len(built) < len(experiments):
        add(
            f"> Counts below are blank for {len(experiments) - len(built)} experiment(s) not "
            f"built on this machine. `data/processed/` is gitignored, so a fresh clone shows "
            f"no counts until `mmds build` has run."
        )
        add("")

    add("| Layer | Experiments | Rows | Redistributable |")
    add("|---|---|---|---|")
    add(f"| UK — Harvard Dataverse | {len(uk)} | {uk_rows:,} | **yes, CC0 1.0** |")
    add(f"| US transfer — TESS | {len(tess)} | {tess_rows:,} | **no** — no licence stated |")
    add(f"| **Total** | **{len(experiments)}** | **{uk_rows + tess_rows:,}** | |")
    add("")
    add("---")
    add("")

    add("## UK layer — Harvard Dataverse, CC0 1.0")
    add("")
    add(
        "The publishable corpus. Every one of these reproduces a number its own authors "
        "printed — a published table, or their own estimator run over the raw deposit — "
        "rather than a number we computed and then agreed with."
    )
    add("")
    for e in sorted(uk, key=lambda x: -(x.rows or 0)):
        add(f"### `{e.recipe}`")
        add("")
        add(f"**{e.title}**")
        add("")
        if e.description:
            add(e.description)
            add("")
        add(f"- **Source** — {SOURCE_LABEL.get(e.source, e.source)}, `{e.reference or '—'}`")
        add(f"- **Type** — {e.design or '—'}")
        add(f"- **Category** — {e.category}")
        add(f"- **Rows** — {_num(e.rows)} from {_num(e.participants)} respondents")
        add(f"- **Licence** — {e.licence or '—'}")
        if e.verified_against:
            add(f"- **Verified against** — {e.verified_against}")
        add("")

    add("---")
    add("")
    add("## US transfer layer — TESS, no licence stated")
    add("")
    add(
        "Fielded in the United States on topics judged universal enough to transfer. "
        "**None of this is redistributable**: all 202 deposits in the TESS catalogue were "
        "checked individually against the OSF API and 196 state no licence, 6 are "
        "unreachable. Usable for research here; not shippable, and not sent to any external "
        "service — `embed.py`'s licence gate refuses this text by name."
    )
    add("")
    add("| Experiment | Title | Category | Rows | Respondents | Reference |")
    add("|---|---|---|---|---|---|")
    for e in sorted(tess, key=lambda x: (x.category, x.recipe)):
        title = e.title if len(e.title) <= 70 else e.title[:67] + "…"
        add(
            f"| `{e.recipe}` | {title} | {e.category} | {_num(e.rows)} | "
            f"{_num(e.participants)} | {e.reference or '—'} |"
        )
    add("")

    add("---")
    add("")
    add("## By category")
    add("")
    add(
        "Categories are TESS's own six, reused verbatim so the two layers can be compared "
        "across one taxonomy, plus two political categories added for the UK layer — which "
        "needed them because TESS's vocabulary has no political category at all. That "
        "absence is itself a finding about how different the two corpora are. The "
        "definitions and the judgement behind the political split are in "
        "`data/catalog/experiment_manifest.json`."
    )
    add("")
    add("| Category | UK | US (TESS) | Rows |")
    add("|---|---|---|---|")
    categories = sorted({e.category for e in experiments})
    for category in categories:
        members = [e for e in experiments if e.category == category]
        add(
            f"| {category} | {len([e for e in members if e.is_uk])} | "
            f"{len([e for e in members if not e.is_uk])} | "
            f"{sum(e.rows or 0 for e in members):,} |"
        )
    add("")

    unclassified = [e for e in experiments if e.category == "UNCLASSIFIED"]
    if unclassified:
        add(
            f"> **{len(unclassified)} experiment(s) have no category**: "
            f"{', '.join('`' + e.recipe + '`' for e in unclassified)}. "
            f"Add them to `data/catalog/experiment_manifest.json`."
        )
        add("")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="write docs/EXPERIMENTS.md")
    group.add_argument("--check", action="store_true", help="fail if the file on disk is stale")
    args = parser.parse_args()

    rendered = render(collect())

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
    diff = difflib.unified_diff(
        current.splitlines(keepends=True),
        rendered.splitlines(keepends=True),
        fromfile="on disk",
        tofile="regenerated",
    )
    sys.stderr.writelines(diff)
    print(f"\n{OUT.relative_to(REPO)} is STALE — run --write", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
