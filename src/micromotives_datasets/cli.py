"""`mmds` — build and verify study datasets.

mmds build recipes/7jt2f.yaml [--crosscheck] [--out data/processed]
mmds crosscheck 7jt2f
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import recipe as recipe_mod
from .config import PROCESSED_DIR, RAW_DIR
from .persona import render as render_persona
from .pipeline.build import build_rows
from .pipeline.qc import check
from .schema import Row
from .sources import spss


def _resolve_data_file(study_id: str, data_file: str) -> Path:
    """Find a study's data file under data/raw/<study_id>/.

    Zips extract into a subfolder named after the archive, so the file is often
    a level or two down rather than at the study root. The recipe names the file,
    not the path, and this finds it wherever it landed.
    """
    root = RAW_DIR / study_id
    direct = root / data_file
    if direct.exists():
        return direct
    matches = [p for p in root.rglob(data_file) if p.is_file() and not p.name.startswith("._")]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise SystemExit(
            f"{data_file!r} is ambiguous under {root} — found:\n"
            + "\n".join(f"  {m}" for m in matches)
        )
    raise SystemExit(
        f"data file not found: {data_file!r} anywhere under {root}\n"
        "Run `mmds fetch <osf_code>` first (raw data is gitignored by design)."
    )


def _load_and_build(recipe_path: Path) -> tuple[recipe_mod.Recipe, list[Row]]:
    rec = recipe_mod.load(recipe_path)
    data_path = _resolve_data_file(rec.study_id, rec.data_file)
    rows = list(build_rows(spss.read(data_path), rec))
    return rec, rows


def _write_parquet(rows: list[Row], out_dir: Path, study_id: str) -> Path:
    import pandas as pd

    out_dir.mkdir(parents=True, exist_ok=True)
    flat = []
    for r in rows:
        d = r.model_dump()
        d["persona_text"] = render_persona(r.persona)
        d["persona"] = r.persona.model_dump_json()
        flat.append(d)
    path = out_dir / f"{study_id}.parquet"
    pd.DataFrame(flat).to_parquet(path, index=False)
    return path


def cmd_build(args: argparse.Namespace) -> int:
    rec, rows = _load_and_build(Path(args.recipe))
    report = check(rows, rec)
    print(report.render())

    if args.crosscheck:
        print()
        if not rec.comparable_to_socsci210:
            print(
                f"CROSSCHECK — {rec.study_id}: SKIPPED (not comparable)\n"
                "  SocSci210 reconstructed a different scope for this study, so a numeric\n"
                "  comparison would be meaningless. See the recipe's notes."
            )
        else:
            from .pipeline.crosscheck import compare

            cc = compare(rows, rec.study_id)
            print(cc.render())
            if not cc.passed and not args.force:
                print("\ncrosscheck failed — not writing output (use --force to override)")
                return 1

    if not report.passed and not args.force:
        print("\nQC failed — not writing output (use --force to override)")
        return 1

    if not args.dry_run:
        path = _write_parquet(rows, Path(args.out), rec.study_id)
        print(f"\nwrote {len(rows):,} rows -> {path}")
    return 0


def cmd_crosscheck(args: argparse.Namespace) -> int:
    from .pipeline.crosscheck import compare

    recipe_path = Path(args.recipe) if args.recipe else Path("recipes") / f"{args.study_id}.yaml"
    rec, rows = _load_and_build(recipe_path)
    rep = compare(rows, rec.study_id)
    print(rep.render())
    return 0 if rep.passed else 1


def cmd_fetch(args: argparse.Namespace) -> int:
    from .sources.osf import fetch

    result = fetch(args.osf_code, RAW_DIR, study_id=args.study_id or args.osf_code)
    print(result.render())
    return 0 if result.data_files else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mmds", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    f = sub.add_parser("fetch", help="download a study's raw deposit from OSF")
    f.add_argument("osf_code", help="OSF 5-char code (== study_id for TESS studies)")
    f.add_argument("--study-id", default=None, help="override the local folder name")
    f.set_defaults(func=cmd_fetch)

    b = sub.add_parser("build", help="build a study into (P,c,o,r) rows")
    b.add_argument("recipe")
    b.add_argument("--out", default=str(PROCESSED_DIR))
    b.add_argument("--crosscheck", action="store_true", help="also verify against SocSci210")
    b.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    b.add_argument("--force", action="store_true", help="write even if checks fail")
    b.set_defaults(func=cmd_build)

    c = sub.add_parser("crosscheck", help="compare a build against SocSci210")
    c.add_argument("study_id")
    c.add_argument("--recipe", default=None)
    c.set_defaults(func=cmd_crosscheck)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:  # pragma: no cover
        return 130


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
