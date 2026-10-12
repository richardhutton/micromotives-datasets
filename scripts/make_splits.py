"""Make the held-out splits, in SocSci210's metadata formats.

participant_mapping.json: which studies are held out from training entirely.
condition_mapping.json: within each experiment, which rows are held out because their
condition is (see "Hidden conditions" below).
task_mapping.json: the same, for outcomes (questions) instead of conditions.

    uv run python scripts/make_splits.py          # write data/catalog/splits/
    uv run python scripts/make_splits.py --check  # fail if the files would change

Copies SocSci210's `metadata/participant_mapping.json` ({"seen": [...], "unseen":
[...]}, 170 / 40 of 210 studies, ~19% unseen). The paper does not say how its 40
were chosen. Ours, ruled 12 Oct 2026 (docs/CONVENTIONS.md, "Unseen studies"):

- The unit held out is a STUDY: every experiment in it goes to the same side. For
  TESS and Harvard Dataverse that is the study id, as in SocSci210. Two sources
  file many experiments under one id, so they get a finer unit:
  - DEL: the survey file (one Dataverse deposit per wave), e.g. "del:panel_w4".
  - Innovation Panel: the IP experiment number in the recipe title, e.g.
    "ukds_6849:9.10", so the same experiment fielded in two waves stays together.
- TESS studies that are also in SocSci210 keep SocSci210's side, so Socrates and our
  model are compared on studies neither trained on.
- Everything else: UNSEEN_SHARE of each source's studies, drawn at random from a
  fixed seed, so every source is represented in the test set.
- EXCLUDED studies are on neither side (excluded.json says why). They are removed
  after the draw, so excluding one never moves another study between sides.

Hidden conditions (condition_mapping.json, SocSci210's file of that name; rich, 12 Oct
2026). A separate test from the study split, as in SocSci210, where 26 of the 129 studies
in its condition mapping are unseen in its participant mapping:

1. Every experiment (recipe) with at least MIN_GROUPS conditions, except EXCLUDED
   studies. Keyed by experiment, not study: conditions belong to one experiment, and a
   DEL survey holds several with different conditions.
2. Its rows are numbered 0, 1, 2, ... in ROW_ORDER (person, condition, outcome; never
   repeated), so a number always means the same answer, whatever order a parquet is in.
3. HIDDEN_SHARE of its conditions, rounded half up and at least one, drawn at random from
   a seed made of SEED and the experiment's name, so adding or changing one experiment
   never changes another's draw.
4. A row whose condition was drawn goes to "eval"; every other row to "train".

A condition number is not always a distinct text (a sequence of messages can show one
text under several numbers), so numbers that share any text are hidden together as one
unit, and "conditions" above means these units. The rule this guarantees, and the test
checks: no text in eval appears in train.

Hidden outcomes (task_mapping.json): the same four steps with the outcome (`task_num`)
in place of the condition (a question asked about five profiles in turn has five task
numbers and one wording: one unit, so it cannot be hidden from itself), and "task" added to each experiment's seed so its draw is
independent of the condition draw.

The study split reads only recipe headers; the condition mapping reads the built rows.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RECIPES = ROOT / "recipes"
OUT = ROOT / "data" / "catalog" / "splits"

UNSEEN_SHARE = 0.20
MIN_GROUPS = 4  # conditions (or outcomes) an experiment needs to take part
HIDDEN_SHARE = 0.25
ROW_ORDER = ["participant_id", "condition_num", "task_num"]
TEXTS = ["condition", "outcome"]
PROCESSED = ROOT / "data" / "processed"
SEED = 20261012

# SocSci210 metadata/participant_mapping.json (huggingface.co/datasets/socratesft/
# SocSci210), read 12 Oct 2026. Only the ids matter here, not their rows.
SOCSCI210_UNSEEN = frozenset(
    [
        "326nv",
        "5vm8g",
        "w72cz",
        "5hqan",
        "rj3aw",
        "py9kw",
        "5an26",
        "jmtyn",
        "kwfs3",
        "y9nb7",
        "c5r2f",
        "3muqx",
        "s43kb",
        "xym9d",
        "vnm9y",
        "ux8qt",
        "wn3y9",
        "qkhdg",
        "jkspw",
        "tcg8p",
        "rpw4u",
        "b3ve6",
        "ervm8",
        "a7uk3",
        "c38xe",
        "8ctbk",
        "nhgxf",
        "53kjy",
        "3rvgz",
        "zsekp",
        "7jt2f",
        "3pcdm",
        "9nphm",
        "yjvpn",
        "yp736",
        "xtvu5",
        "a5v96",
        "ak35q",
        "a693y",
        "ztwqy",
    ]
)
SOCSCI210_SEEN = frozenset(
    [
        "w7mnc",
        "z358z",
        "xy8jw",
        "7py98",
        "pxb6n",
        "bsd7j",
        "zx5b8",
        "n8azj",
        "t8xq7",
        "cmxkt",
        "3bzxg",
        "sd7cf",
        "c956y",
        "yv2ta",
        "v6kqy",
        "mwj3k",
        "vhycz",
        "5g882",
        "mebng",
        "my275",
        "9263n",
        "v5u8r",
        "b87sm",
        "e2pyb",
        "4rqy5",
        "bwgjp",
        "e45hu",
        "dh3nj",
        "pq5wm",
        "egmxd",
        "yg958",
        "k9bwj",
        "4w9pz",
        "jtgyq",
        "rdmus",
        "es4xw",
        "mzm26",
        "gzdnf",
        "3jwnf",
        "gx6hp",
        "r5hwx",
        "yn4gf",
        "q9w6s",
        "xc4yq",
        "yuazs",
        "prf7d",
        "v6nhw",
        "9n7hj",
        "py9q3",
        "5vyzq",
        "kryns",
        "ams2u",
        "nprqu",
        "84vy3",
        "8jv6a",
        "wmsah",
        "hz5rt",
        "3ydty",
        "nj5dx",
        "98muc",
        "fxcn4",
        "x2ztf",
        "qprms",
        "b5a4z",
        "pb2rr",
        "mebw9",
        "9xw67",
        "jf46x",
        "xweq8",
        "j6xgs",
        "6khjm",
        "gdrbk",
        "tuyjc",
        "bvkfc",
        "t936a",
        "sdq2z",
        "ndhyr",
        "a42yg",
        "7rt4q",
        "9fehm",
        "4zscf",
        "yc2qb",
        "z6gts",
        "qzd3f",
        "de5hx",
        "xvgh5",
        "r9v2d",
        "zaqkm",
        "48p7y",
        "8be6n",
        "dehmv",
        "ye2ej",
        "sjrpn",
        "dkhgv",
        "ac9jm",
        "ncs7k",
        "bf8p2",
        "vz5r4",
        "5mt6r",
        "52ymc",
        "6s2q5",
        "d3zvr",
        "4zwv2",
        "xfmrn",
        "cug34",
        "ejms3",
        "4gczb",
        "zv3wc",
        "zrwjp",
        "9fsem",
        "3xy9j",
        "xykr7",
        "cdgp2",
        "qmfy4",
        "8ypcc",
        "s2rd5",
        "hu45w",
        "8khwt",
        "sh4px",
        "bqm6j",
        "evnyh",
        "kv3sd",
        "yn7mx",
        "usywt",
        "6esdw",
        "k9ahx",
        "345ms",
        "4kjtn",
        "ef6my",
        "q8ra3",
        "fct42",
        "mkgvp",
        "savkp",
        "3hjyt",
        "5b6tf",
        "2fuqc",
        "nk9jd",
        "6wbd7",
        "rs65g",
        "m7vhz",
        "vemrp",
        "ftwqy",
        "hjn6m",
        "a2nbf",
        "v3bfk",
        "nst3w",
        "j38gd",
        "nb4xg",
        "6n5cz",
        "8tcj2",
        "4fsg5",
        "j986z",
        "yh2ef",
        "4nyuc",
        "h6zk9",
        "pjneh",
        "n96d8",
        "zb5nv",
        "mp3dr",
        "4n986",
        "hgmu6",
        "9tv2b",
        "zmtbw",
        "d3agv",
        "g59sr",
        "sffyb",
        "m52pd",
        "waq4m",
        "h84nt",
        "ar9e3",
    ]
)

# On neither side for now (rich, 12 Oct 2026). Removed after the draw: see split().
EXCLUDED = {
    "ukds_6849:9.13": "time and risk: 91 items per person, 109,770 rows, one condition "
    "(no experimental contrast); the largest study by far",
    "ukds_6849:9.31": "ReQoL and GHQ: 28 items per person, so one study outweighs most others",
}

_HEADER = re.compile(r"^(study_id|source|experiment|title):\s*(.*)$")
_IP_NUMBER = re.compile(r"\bexperiment (\d+\.\d+)\b")


def recipe_header(path: Path) -> dict[str, str]:
    """The top-level study_id, source, experiment and title of one recipe."""
    found: dict[str, str] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            if match := _HEADER.match(line):
                found.setdefault(match.group(1), match.group(2).strip().strip("'\""))
    return found


def study_of(header: dict[str, str]) -> str:
    """The unit held out together: see the module docstring."""
    source, study_id = header["source"], header["study_id"]
    if study_id == "del":
        wave = "_".join(header["experiment"].split("_")[:2])  # panel_w4, sandbox_feb2023
        return f"del:{wave}"
    if source == "innovation_panel":
        match = _IP_NUMBER.search(header.get("title", ""))
        if not match:
            raise ValueError(f"{header}: Innovation Panel recipe title names no experiment")
        return f"{study_id}:{match.group(1)}"
    return study_id


def experiments_by_study() -> dict[str, dict[str, object]]:
    """study -> its source and the recipes (experiments) in it."""
    studies: dict[str, dict[str, object]] = {}
    for path in sorted(RECIPES.glob("*.yaml")):
        header = recipe_header(path)
        study = study_of(header)
        entry = studies.setdefault(study, {"source": header["source"], "recipes": []})
        if entry["source"] != header["source"]:
            raise ValueError(f"{study} mixes sources")
        entry["recipes"].append(path.stem)  # type: ignore[attr-defined]
    return studies


def split(studies: dict[str, dict[str, object]]) -> dict[str, list[str]]:
    rng = random.Random(SEED)
    by_source: dict[str, list[str]] = defaultdict(list)
    for study, entry in studies.items():
        by_source[str(entry["source"])].append(study)

    unseen: set[str] = set()
    for source in sorted(by_source):
        ids = sorted(by_source[source])
        target = round(UNSEEN_SHARE * len(ids))
        forced_unseen = [s for s in ids if s in SOCSCI210_UNSEEN]
        forced_seen = {s for s in ids if s in SOCSCI210_SEEN}
        unseen.update(forced_unseen)
        free = [s for s in ids if s not in forced_seen and s not in SOCSCI210_UNSEEN]
        extra = max(0, target - len(forced_unseen))
        unseen.update(rng.sample(free, min(extra, len(free))))

    # Draw over every study, then drop the excluded ones, so the draw is the same
    # with or without them.
    all_ids = sorted(s for s in studies if s not in EXCLUDED)
    return {
        "seen": [s for s in all_ids if s not in unseen],
        "unseen": [s for s in all_ids if s in unseen],
    }


def numbered_rows(df: pd.DataFrame) -> pd.DataFrame:
    """One experiment's rows in ROW_ORDER, numbered 0..n-1 by position. The export
    numbers rows with this same function, so the mapping and the files agree."""
    if df.duplicated(ROW_ORDER).any():
        raise ValueError("rows repeat a (person, condition, outcome): cannot number them")
    return df.sort_values(ROW_ORDER, kind="stable").reset_index(drop=True)


def rows_by_experiment() -> dict[str, pd.DataFrame]:
    """recipe -> its built rows (the columns the splits need)."""
    recipe_of = {}
    for path in RECIPES.glob("*.yaml"):
        h = recipe_header(path)
        recipe_of[(h["study_id"], h.get("experiment") or None)] = path.stem
    out: dict[str, pd.DataFrame] = {}
    for pq in sorted(PROCESSED.glob("*.parquet")):
        df = pd.read_parquet(pq, columns=["study_id", "experiment", *ROW_ORDER, *TEXTS])
        for (sid, exp), g in df.groupby(["study_id", "experiment"], dropna=False):
            exp = None if pd.isna(exp) or exp == "" else str(exp)
            out[recipe_of[(str(sid), exp)]] = g[[*ROW_ORDER, *TEXTS]]
    if missing := sorted(set(recipe_of.values()) - set(out)):
        raise ValueError(f"recipes with no built rows: {missing}")
    return out


# What each mapping hides, and the seed prefix of its draw. The condition prefix is
# empty so condition_mapping.json is unchanged from its first draw.
HIDE = {
    "condition_mapping.json": ("condition_num", "condition", ""),
    "task_mapping.json": ("task_num", "outcome", "task:"),
}


def units(df: pd.DataFrame, number: str, text: str) -> pd.Series:
    """Each row's hiding unit: its `number`, joined with every other number that shares
    any `text` with it, so hiding a unit hides its text completely. Named by the
    smallest number in it, so a number that shares no text is its own unit, unchanged.

    Needed because a number is not always a distinct text: a question asked about five
    profiles in turn has five task numbers and one wording; in a sequence of messages
    one text appears under several condition numbers (rich, 12 Oct 2026).
    """
    parent: dict[int, int] = {}

    def root(x: int) -> int:
        while parent.setdefault(x, x) != x:
            x = parent[x]
        return x

    for numbers in df.groupby(text)[number].unique():
        first = root(int(numbers[0]))
        for n in numbers[1:]:
            a, b = sorted((first, root(int(n))))
            parent[b] = a
            first = a
    return df[number].map(lambda n: root(int(n)))


def hidden_values(seed: str, values: list[int]) -> list[int]:
    """Step 3 of "Hidden conditions": HIDDEN_SHARE of them, at least one."""
    k = max(1, int(HIDDEN_SHARE * len(values) + 0.5))
    return sorted(random.Random(seed).sample(sorted(values), k))


def hidden_mapping(
    rows: dict[str, pd.DataFrame], study: dict[str, str], number: str, text: str, prefix: str
) -> dict:
    """Steps 1-4 of "Hidden conditions", hiding whole units of `number` (see units())."""
    mapping = {}
    for experiment in sorted(rows):
        if study[experiment] in EXCLUDED:
            continue
        df = numbered_rows(rows[experiment])
        unit = units(df, number, text)
        values = [int(v) for v in unit.unique()]
        if len(values) < MIN_GROUPS:
            continue
        hidden = unit.isin(hidden_values(f"{SEED}:{prefix}{experiment}", values))
        mapping[experiment] = {
            "train": df.index[~hidden].tolist(),
            "eval": df.index[hidden].tolist(),
        }
    return mapping


def _compact(mapping: dict) -> str:
    """One line per list: the row lists run to hundreds of thousands of numbers."""
    lines = ["{"]
    for i, (name, sides) in enumerate(mapping.items()):
        comma = "," if i < len(mapping) - 1 else ""
        lines.append(f'  "{name}": {{')
        lines.append(f'    "train": {json.dumps(sides["train"])},')
        lines.append(f'    "eval": {json.dumps(sides["eval"])}')
        lines.append(f"  }}{comma}")
    lines.append("}")
    return "\n".join(lines) + "\n"


def outputs() -> dict[str, str]:
    studies = experiments_by_study()
    mapping = split(studies)
    recipes = {r: s for s, e in studies.items() for r in e["recipes"]}  # type: ignore[attr-defined]
    files = {
        "participant_mapping.json": json.dumps(mapping, indent=2) + "\n",
        "excluded.json": json.dumps(dict(sorted(EXCLUDED.items())), indent=2) + "\n",
        "study_of_recipe.json": json.dumps(dict(sorted(recipes.items())), indent=2) + "\n",
    }
    rows = rows_by_experiment()
    for name, (number, text, prefix) in HIDE.items():
        files[name] = _compact(hidden_mapping(rows, recipes, number, text, prefix))
    return files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = outputs()
    if args.check:
        stale = [n for n, text in files.items() if (OUT / n).read_text() != text]
        if stale:
            sys.exit(f"stale: {stale}; run scripts/make_splits.py")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (OUT / name).write_text(text)
    mapping = json.loads(files["participant_mapping.json"])
    studies = experiments_by_study()
    for side in ("seen", "unseen"):
        per_source: dict[str, int] = defaultdict(int)
        for s in mapping[side]:
            per_source[str(studies[s]["source"])] += 1
        print(f"{side}: {len(mapping[side])} studies {dict(sorted(per_source.items()))}")
    print("unseen:", mapping["unseen"])
    for name in HIDE:
        cm = json.loads(files[name])
        n_eval = sum(len(v["eval"]) for v in cm.values())
        n_all = n_eval + sum(len(v["train"]) for v in cm.values())
        print(f"{name}: {len(cm)} experiments, {n_all:,} rows, {n_eval:,} eval")


if __name__ == "__main__":
    main()
