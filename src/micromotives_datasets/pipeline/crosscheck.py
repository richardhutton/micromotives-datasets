"""Compare a build against SocSci210 — our answer key for the ~75 studies
that appear in both.

IMPORTANT: this asserts on NUMBERS ONLY. An audit of four studies found
SocSci210's numeric reconstruction correct in 4/4 but its stimulus TEXT wrong
in 3/4 (a factor inverted, a factor dropped, and all arms describing the wrong
scenario). So text is reported as an informational diff, never as a pass/fail.

SocSci210 is read straight from its parquet shards via DuckDB. The public
`/filter` API endpoint cannot serve this dataset (the index never loads).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from ..schema import Row

PARQUET_BASE = (
    "https://huggingface.co/datasets/socratesft/SocSci210/resolve/"
    "refs%2Fconvert%2Fparquet/default/train"
)
N_SHARDS = 17
SHARD_URLS = [f"{PARQUET_BASE}/{i:04d}.parquet" for i in range(N_SHARDS)]


@dataclass
class CrossCheckReport:
    study_id: str
    ours: dict[str, Any] = field(default_factory=dict)
    theirs: dict[str, Any] = field(default_factory=dict)
    mismatches: list[str] = field(default_factory=list)
    text_notes: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.mismatches

    def render(self) -> str:
        lines = [f"CROSSCHECK — {self.study_id}  (numbers only; text is informational)"]
        for key in ("n_rows", "n_conditions", "rows_per_condition", "response_distribution"):
            o, t = self.ours.get(key), self.theirs.get(key)
            flag = "ok " if o == t else "DIFF"
            lines.append(f"  [{flag}] {key}")
            if o != t:
                lines.append(f"         ours:   {o}")
                lines.append(f"         theirs: {t}")
        for m in self.mismatches:
            lines.append(f"  MISMATCH  {m}")
        for n in self.text_notes:
            lines.append(f"  note      {n}")
        lines.append(f"  => {'PASS' if self.passed else 'FAIL'}")
        return "\n".join(lines)


def _connect() -> Any:
    try:
        import duckdb
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("crosscheck needs duckdb: `uv add --dev duckdb`") from e
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    return con


def find_shards(study_id: str) -> list[str]:
    """Which parquet shards hold this study? Reads only the study_id column.

    A study can straddle a shard boundary (rows are not grouped by study), so
    this returns EVERY shard containing it. Reading only the largest one
    silently truncates the reference data.
    """
    con = _connect()
    rows = con.execute(
        f"SELECT filename, count(*) AS n FROM read_parquet({SHARD_URLS!r}, filename=true) "
        "WHERE study_id = ? GROUP BY 1 ORDER BY filename",
        [study_id],
    ).fetchall()
    return [r[0] for r in rows]


def find_shard(study_id: str) -> str | None:
    """Deprecated: the single largest shard. Use `find_shards`."""
    shards = find_shards(study_id)
    return shards[0] if shards else None


def fetch_socsci210(study_id: str, shards: list[str] | None = None) -> dict[str, Any]:
    """Pull the reference study's numeric profile (and its stimulus text)."""
    shards = shards or find_shards(study_id)
    if not shards:
        raise LookupError(f"{study_id} not found in SocSci210")
    con = _connect()
    con.execute(
        f"CREATE TABLE s AS SELECT * FROM read_parquet({shards!r}) WHERE study_id = ?", [study_id]
    )
    n_rows, n_participants = con.execute(
        "SELECT count(*), count(DISTINCT participant) FROM s"
    ).fetchone()
    per_cond = dict(con.execute("SELECT condition_num, count(*) FROM s GROUP BY 1").fetchall())
    dist = dict(con.execute("SELECT response, count(*) FROM s GROUP BY 1").fetchall())
    stimuli = dict(
        con.execute("SELECT condition_num, min(stimuli) FROM s GROUP BY 1 ORDER BY 1").fetchall()
    )
    return {
        "n_rows": int(n_rows),
        "n_participants": int(n_participants),
        "n_conditions": len(per_cond),
        "rows_per_condition": {int(k): int(v) for k, v in per_cond.items()},
        "response_distribution": {int(k): int(v) for k, v in dist.items()},
        "stimuli": {int(k): v for k, v in stimuli.items()},
    }


def profile(rows: list[Row]) -> dict[str, Any]:
    """The same numeric profile, computed from our own rows."""
    per_cond = Counter(r.condition_num for r in rows if r.condition_num is not None)
    dist = Counter(int(r.response_num) for r in rows if r.response_num is not None)
    return {
        "n_rows": len(rows),
        "n_participants": len({r.participant_id for r in rows}),
        "n_conditions": len(per_cond),
        "rows_per_condition": {int(k): int(v) for k, v in per_cond.items()},
        "response_distribution": {int(k): int(v) for k, v in dist.items()},
    }


def compare(rows: list[Row], study_id: str) -> CrossCheckReport:
    ours = profile(rows)
    theirs = fetch_socsci210(study_id)
    rep = CrossCheckReport(study_id=study_id, ours=ours, theirs=theirs)

    for key in ("n_rows", "n_conditions", "rows_per_condition", "response_distribution"):
        if ours.get(key) == theirs.get(key):
            continue
        # Per-condition counts that are a PERMUTATION of each other mean both
        # builds put the same respondents in the same cells and merely number
        # the cells differently. condition_num is an arbitrary index, and there
        # is no shared convention — one audited study used raw-1, another had
        # the arms reversed. That is a labelling difference, not a data
        # disagreement, so it is reported rather than failed.
        if key == "rows_per_condition":
            ours_counts = sorted((ours.get(key) or {}).values())
            their_counts = sorted((theirs.get(key) or {}).values())
            if ours_counts and ours_counts == their_counts:
                rep.text_notes.append(
                    "rows_per_condition is a permutation of SocSci210's — same cell sizes, "
                    "different condition_num ordering. Cells agree; only the index does not."
                )
                continue
        rep.mismatches.append(f"{key} differs")

    # Text is reported, never asserted — see module docstring.
    their_stimuli = theirs.get("stimuli", {})
    n_distinct = len(set(their_stimuli.values()))
    if n_distinct < len(their_stimuli):
        rep.text_notes.append(
            f"SocSci210 has {len(their_stimuli)} conditions but only {n_distinct} distinct "
            "stimulus strings — a manipulation is missing on their side"
        )
    return rep
