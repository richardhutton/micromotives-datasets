"""Write a versioned train/eval export for the training project.

    uv run python scripts/export.py v2 studies
    uv run python scripts/export.py v2 studies                  # for the private HF repo / RunPod
    uv run python scripts/export.py v2 studies --fraction 0.1   # small test export

UKDS granted permission (Oct 2026, docs/ukds_permission_granted.md) for Innovation
Panel rows on rich's private Hugging Face repo and RunPod, so exports include them by
default. --without-ukds is only for a destination that permission does not cover.

Writes data/processed/exports/<version>/<split>/ (gitignored: respondent rows):

    train.parquet    rows of the seen studies
    eval.parquet     rows of the unseen studies
    manifest.json    what went in: counts, file hashes, the split file's hash, git commit

Only the unseen-studies split (data/catalog/splits/studies_mapping.json) for now; rich,
12 Oct 2026. Exports v1 were written before the rename (29 Oct 2026) and keep their
folder name, `participant`. Excluded studies are in neither file. A version is never
overwritten: a changed row or split makes a new version, so "trained on export vN"
always names the same rows.

`--fraction F` keeps a fraction F of each training study's respondents, with all of
their rows, drawn with a fixed seed, into its own folder (`..._10pct`). eval.parquet
is always complete. This follows SocSci210 (Kolluri et al., §5.5), which sampled 10% of
respondents in training only and scored held-out studies in full: sampling eval rows
leaves most (condition, outcome) pairs with one or two responses, too few to compare
distributions (micromotives-training LEDGER 5, 29 Oct 2026). Every study stays on the
side the split puts it, so the held-out property is unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_splits

ROOT = make_splits.ROOT
SPLITS = make_splits.OUT
# Under data/processed/: UKDS rows are written nowhere else (CLAUDE.md, Data handling).
EXPORTS = ROOT / "data" / "processed" / "exports"


def side_of(study: pd.Series, mapping: dict[str, list[str]]) -> pd.Series:
    """'train' for a seen study, 'eval' for an unseen one, None for neither (excluded)."""
    side = dict.fromkeys(mapping["seen"], "train") | dict.fromkeys(mapping["unseen"], "eval")
    return study.map(side)


def all_rows() -> pd.DataFrame:
    """Every built row, with the study the split uses, in a fixed order."""
    study_of = json.loads((SPLITS / "study_of_recipe.json").read_text())
    recipe_of = {}
    for path in make_splits.RECIPES.glob("*.yaml"):
        h = make_splits.recipe_header(path)
        recipe_of[(h["study_id"], h.get("experiment") or None)] = path.stem
    frames = []
    for pq in sorted(make_splits.PROCESSED.glob("*.parquet")):
        df = pd.read_parquet(pq)
        # factors is a per-experiment dict; as JSON text every file shares one schema.
        df["factors"] = df["factors"].map(lambda f: json.dumps(f, sort_keys=True))
        exp = df["experiment"].where(df["experiment"].notna() & (df["experiment"] != ""), None)
        df["recipe"] = [recipe_of[(s, e)] for s, e in zip(df["study_id"], exp, strict=True)]
        df["study"] = df["recipe"].map(study_of)
        frames.append(df)
    rows = pd.concat(frames, ignore_index=True)
    return rows.sort_values(["study", "recipe", *make_splits.ROW_ORDER], kind="stable")


SAMPLE_SEED = 3407


def sample_respondents(frame: pd.DataFrame, fraction: float) -> pd.DataFrame:
    """A fraction of each study's respondents with ALL their rows, fixed seed, original order.

    Per study, so every study keeps its share; at least one respondent per study, so a
    small study is not silently dropped. Whole respondents, so each one sampled still
    answers every outcome they answered.
    """
    if not 0 < fraction <= 1:
        raise ValueError(f"fraction must be in (0, 1], got {fraction}")
    keep = []
    for _, rows in frame.groupby("study", sort=True):
        people = pd.Series(sorted(rows["participant_id"].unique()))
        n = max(1, round(len(people) * fraction))
        chosen = set(people.sample(n=n, random_state=SAMPLE_SEED))
        keep.append(rows.index[rows["participant_id"].isin(chosen)])
    return frame.loc[frame.index.isin(pd.Index([]).append(keep))]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit() -> str:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "data/catalog", "recipes"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return head.stdout.strip() + ("-dirty" if dirty.stdout.strip() else "")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("version")
    parser.add_argument("split", choices=["studies"])
    parser.add_argument(
        "--without-ukds",
        action="store_true",
        help="leave out Innovation Panel rows, only for a destination the UKDS permission "
        "does not cover (it covers rich's private HF repo and RunPod)",
    )
    parser.add_argument(
        "--fraction",
        type=float,
        default=1.0,
        help="keep this fraction of each training study's respondents (e.g. 0.1), "
        "for a small test export; eval is always complete",
    )
    args = parser.parse_args()

    folder = args.split + ("_without_ukds" if args.without_ukds else "")
    if args.fraction != 1.0:
        folder += f"_{round(args.fraction * 100):g}pct"
    out = EXPORTS / args.version / folder
    if out.exists():
        sys.exit(f"{out} exists: a version is never overwritten; use a new version")

    mapping_file = SPLITS / "studies_mapping.json"
    mapping = json.loads(mapping_file.read_text())
    rows = all_rows()
    if args.without_ukds:
        rows = rows[rows["source"] != "innovation_panel"]
    rows["side"] = side_of(rows["study"], mapping)

    excluded = rows["side"].isna()
    if not set(rows.loc[excluded, "study"]) <= set(make_splits.EXCLUDED):
        sys.exit("rows on neither side are not exactly the excluded studies")
    train = rows[rows["side"] == "train"].drop(columns="side")
    held = rows[rows["side"] == "eval"].drop(columns="side")
    if args.fraction != 1.0:
        train = sample_respondents(train, args.fraction)
    if overlap := set(train["study"]) & set(held["study"]):
        sys.exit(f"studies on both sides: {sorted(overlap)}")
    # Panels (Innovation Panel, the DEL panel waves) put the same person in several
    # studies, so a person can be in train for one study and eval for another. That is
    # not a leak of the held-out study; it is counted so it is known, not hidden.
    shared_people = set(held["participant_id"]) & set(train["participant_id"])

    out.mkdir(parents=True)
    files = {"train.parquet": train, "eval.parquet": held}
    for name, frame in files.items():
        frame.to_parquet(out / name, index=False)

    def summary(frame: pd.DataFrame) -> dict:
        return {
            "rows": len(frame),
            "studies": frame["study"].nunique(),
            "experiments": frame["recipe"].nunique(),
            "participants": frame["participant_id"].nunique(),
            "rows_by_source": frame["source"].value_counts().sort_index().to_dict(),
        }

    manifest = {
        "version": args.version,
        "split": args.split,
        "fraction": args.fraction,
        "sample_seed": SAMPLE_SEED if args.fraction != 1.0 else None,
        "created": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_commit": _git_commit(),
        "split_file": {
            "path": str(mapping_file.relative_to(ROOT)),
            "sha256": _sha256(mapping_file),
        },
        "excluded_studies": sorted(make_splits.EXCLUDED),
        "excluded_rows": int(excluded.sum()),
        "participants_in_both": {
            "count": len(shared_people),
            "eval_rows": int(held["participant_id"].isin(shared_people).sum()),
            "by_source": held.loc[held["participant_id"].isin(shared_people), "source"]
            .value_counts()
            .sort_index()
            .to_dict(),
        },
        "includes_ukds": bool((rows.loc[~excluded, "source"] == "innovation_panel").any()),
        "train": summary(train) | {"sha256": _sha256(out / "train.parquet")},
        "eval": summary(held) | {"sha256": _sha256(out / "eval.parquet")},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    keys = ("train", "eval", "excluded_rows", "participants_in_both")
    print(json.dumps({k: manifest[k] for k in keys}, indent=2))


if __name__ == "__main__":
    main()
