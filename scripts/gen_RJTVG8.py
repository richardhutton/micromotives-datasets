#!/usr/bin/env python3
"""Derive RJTVG8's UK i-voting conjoint arms from the data, rather than hand-typing them.

RJTVG8 (Turnbull-Dugarte & Devine, "Support for digitising the ballot box",
Electoral Studies 86 (2023)) is a 10-attribute forced-choice conjoint, UK only,
1,200 respondents x 5 tasks x 2 profiles = 12,000 profile rows. Like `PMV0TG`
this reshapes a LONG profile-level deposit into one row per respondent, and
the pipeline's melt (`pipeline.build.build_rows`) needs one row per respondent
holding BOTH profiles of every task at once (`condition.source_vars` is looked
up by column name on a single `ds.df` row).

THE FETCH, AND THE FIRST FINDING
---------------------------------
The Dataverse API reports `evoting_replicationfile.tab`'s `originalFileFormat`
as `application/x-stata-14` — this deposit's `.tab` is Dataverse's own derived,
label-stripped export of an uploaded `.dta`, exactly the `QQM5MC` mistake
`scripts/fetch_dataverse.py`'s own docstring warns about ("Dataverse 'ingests'
an uploaded .dta or .sav and serves a derived .tab by default -- and the
ingest drops the value labels"). This is NOT the `PMV0TG` situation the task
brief's reading list primed us for: `PMV0TG` genuinely ships only a
tab-delimited export with no statistical file at all, so `sources.delimited`
returning empty `value_labels` is a correct absence there. Here an original
.dta exists and was fetched with `?format=original` (see
`data/raw/RJTVG8/evoting_replicationfile.dta`, 12,000 rows x 70 columns,
Stata 14 format) and read with `sources.spss`, which recovers 13 variables'
worth of real value labels the derived `.tab` would have discarded. Using the
`.tab` here would have meant reconstructing attribute wording by hand from a
secondary source when the primary one was one `?format=original` query away.

WHERE THE CONDITION TEXT COMES FROM
------------------------------------
This deposit ships NO fielded-instrument file at all — no `.qsf`, no
questionnaire export, no codebook separate from the data. Two secondary
sources exist: the published appendix's Table A.3 ("Attribute values &
pre-registered expectations", the task brief's suggested primary source) and
Figure 1 ("Example conjoint task", a screenshot of one rendered task). Neither
is the fielded instrument; both are compared against the DEPOSIT'S OWN value
labels (`ds.value_labels[f"{attr}_num"]`, recovered only because the original
.dta was fetched) before anything is numbered. Three discrepancies were found,
and they resolve the same way every time: Figure 1 (a literal screenshot)
agrees with the DATA, not with Table A.3 —

  1. `method` code for "website": data says "Vote via website" (baseline,
     matches). Data's code for the smartphone level reads "Vote via smarphone
     app" (sic); Table A.3 prints "Vote via smartphone app". Figure 1 does not
     show this level, so it cannot adjudicate — the DATA's own text is used
     verbatim (typos are source content, not noise — docs/CONVENTIONS.md).
  2. `trials`: data's level 7 reads "US"; Table A.3 prints "UK" for the
     equivalent row. Figure 1's own screenshot shows "US" for this exact
     attribute ("Successful trials completed in: ... US"), agreeing with the
     DATA against Table A.3. Table A.3's "UK" is treated as the appendix
     table's own transcription error, not corrected into the data, and not
     propagated into our text either — we follow the data+Figure 1 pair.
  3. `platform` level 2 ("Central government & private sector IT ..."): data
     says "...IT form" (sic); Table A.3 says "...IT firm" for all three
     private-sector levels. Figure 1 shows exactly this level and also reads
     "...IT form" — a second independent confirmation that the DATA's typo is
     the genuine on-screen text, not a data-entry slip. Levels 5 and 6 of the
     same attribute correctly say "firm" in the data; only level 2 has the typo.
     (A fourth, purely typographic difference on the six-way level — the data
     omits the Oxford comma in "Local council, central government & private
     sector IT firm" where Table A.3 has one — is also kept as the data's
     own text, not corrected.)
  4. `cost`'s three negative levels: data reads "-£0.50 (50p less)" etc. (no
     space after the minus sign); Table A.3 prints "- £0.50 (50p less)" (a
     space). Purely typographic, data's own spacing is kept.

So: **condition text is built from `ds.value_labels` verbatim, not retyped
from Table A.3.** `load()` asserts the data's level-text SET for every
attribute equals Table A.3's set, with exactly these three named exceptions —
anything else differing raises. Table A.3 remains useful for confirming
attribute identity/count and (via its italics) each attribute's baseline
level, used only by `scripts/verify_RJTVG8.py`, not by this generator.

ATTRIBUTE ROW ORDER — THE WEAKER FORM OF EVIDENCE, STATED AS SUCH
--------------------------------------------------------------------
No order-encoding column exists in the 70-column header (checked below,
`test_no_per_respondent_attribute_order_column_exists` pins it), and a grep of
both replication scripts (1,130 lines) for order|rand|shuffl|FL_|position|seq
finds zero matches outside ggplot's unrelated `legend.position`/
`strip.position` theme calls. That much replicates what a prior screen already
found. It is still only absence of a mechanism, not proof of a fixed layout —
the brief's own warning, after `EFXNLX` rendered 16,465 conditions in a fixed
order a randomisation column (undetected for a whole build) actually
contradicted.

What's new here: Figure 1 is a literal screenshot of one rendered task, and
its row order is -- Voting method, Voting window, Successful trials completed
in, Pilot outcome on participation, Pilot outcome on integrity, Online voting
platform controlled by, Change in government cost (per vote), Proposing
party, Endorsement, Pre-registration -- which is NOT Table A.3's order
(Table A.3 leads with Pre-registration; Figure 1 ends with it). That
divergence confirms Table A.3 is a thematically-grouped appendix list, not a
record of on-screen order, so Figure 1's order is used for rendering (and its
own row labels, which also differ slightly from Table A.3's attribute names,
e.g. "Voting method" vs "Method").

But Figure 1 is ONE example. Unlike `PMV0TG` (two independently-authored
sources -- a Qualtrics preview export AND a codebook.pdf -- agreeing with each
other and with the data's own column order), there is no second rendering to
cross-check order CONSISTENCY across respondents. A single screenshot cannot
distinguish "every respondent saw this order" from "this is the one
respondent whose screenshot got attached to the paper, in an otherwise
per-respondent-randomised design". `condition.line_order_vars` is NOT
declared (there is no per-respondent order column to declare it from, and
none would exist even if we wanted one) and every arm renders in Figure 1's
fixed order. This is the project's residual risk on this study, named
explicitly rather than resolved: **if attribute row order was in fact
randomised per respondent and simply not recorded, every condition here
states an order some unknown fraction of respondents did not see** -- the
exact shape of the EFXNLX defect, not ruled out, only not evidenced either.

    uv run python scripts/gen_RJTVG8.py --check   # agree with the recipe?
    uv run python scripts/gen_RJTVG8.py --write   # regenerate wide CSV + arms/outcomes
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from micromotives_datasets.sources import spss

REPO = Path(__file__).resolve().parents[1]
RECIPE = REPO / "recipes" / "RJTVG8.yaml"
RAW = REPO / "data" / "raw" / "RJTVG8" / "evoting_replicationfile.dta"
WIDE = REPO / "data" / "raw" / "RJTVG8" / "evoting_UK_wide.csv"

N_TASKS = 5
N_RESPONDENTS = 1_200
N_PROFILE_ROWS = 12_000

# The 10 attributes, in FIGURE 1's own on-screen row order (the paper's
# "Example conjoint task" screenshot, p.12 of the author-accepted manuscript),
# NOT Table A.3's thematically-grouped appendix order (which leads with
# Pre-registration; Figure 1 ends with it — see module docstring). ROW LABEL
# is Figure 1's own left-column text verbatim.
ATTRS: list[tuple[str, str]] = [
    ("method", "Voting method"),
    ("vwindow", "Voting window"),
    ("trials", "Successful trials completed in"),
    ("pilot", "Pilot outcome on participation"),
    ("fraud", "Pilot outcome on integrity"),
    ("platform", "Online voting platform controlled by"),
    ("cost", "Change in government cost (per vote)"),
    ("party", "Proposing party"),
    ("endorse", "Endorsement"),
    ("prereg", "Pre-registration"),
]
ATTR_NAMES = [a for a, _ in ATTRS]

# Table A.3's own level text (author-accepted manuscript, p.xiv), transcribed
# for the SET-equality check in `load()` only — never used to render text.
# Three cells are declared exceptions (see module docstring): the data (cross-
# confirmed by Figure 1 on two of the three) is what gets rendered.
TABLE_A3_LEVELS: dict[str, set[str]] = {
    "prereg": {"Automatically pre-registered", "Must opt-in by post", "Must opt-in online"},
    "method": {
        "Vote via website",
        "Vote via smartphone app",  # data: "Vote via smarphone app" (typo, kept verbatim)
        "Vote via telephone call",
        "Vote via SMS (text)",
    },
    "vwindow": {
        "available for two weeks up to (and including) polling day",
        "available for up to two weeks before polling day",
        "available on polling day only",
    },
    "trials": {
        "None",
        "Estonia",
        "UK",  # data + Figure 1: "US" — Table A.3's own transcription error
        "Germany",
        "Switzerland",
        "Argentina",
        "Mozambique",
    },
    "pilot": {
        "None",
        "Increases overall participation",
        "Decreases overall participation",
        "Increases participation among young",
        "Decreases participation among young",
        "Increases participation among elderly",
        "Decreases participation among elderly",
        "Increases participation in socially deprived areas",
        "Decreases participation in socially deprived areas",
    },
    "fraud": {"None", "Reduces risk of electoral fraud", "Increases risk of electoral fraud"},
    "platform": {
        "Local council",
        "Central government",
        "Local council & central government",
        "Local council & private sector IT firm",
        "Central government & private sector IT firm",  # data+Fig.1: "...IT form" (typo)
        "Local council, central government, & private sector IT firm",  # data has no 2nd comma
    },
    "cost": {
        "£0 (none)",
        "£0.50 (50p more)",
        "£1 (one pound more)",
        "£5 (five pounds more)",
        "- £0.50 (50p less)",  # data: "-£0.50 (50p less)" (no space after the minus)
        "- £1 (one pound less)",  # data: "-£1 (one pound less)"
        "- £5 (five pounds less)",  # data: "-£5 (five pounds less)"
    },
    "party": {"Cross-party coalition", "Conservatives", "Labour", "Liberal Democrats", "the Greens"},
    "endorse": {
        "None",
        "UK Electoral Commission",
        "United Nations Electoral Assistance Division (UN)",
        "UK Electoral Reform Society",
        "European Union (EU)",
    },
}

# The three documented data/Table-A.3 text divergences. Mapped
# data-text -> Table-A.3-equivalent-text so the SET check in `load()` can
# assert "everything else matches exactly" without hand-waving these three.
_KNOWN_TEXT_EXCEPTIONS: dict[str, dict[str, str]] = {
    "method": {"Vote via smarphone app": "Vote via smartphone app"},
    "trials": {"US": "UK"},
    "platform": {
        "Central government & private sector IT form": "Central government & private sector IT firm",
        "Local council, central government & private sector IT firm": (
            "Local council, central government, & private sector IT firm"
        ),
    },
    "cost": {
        "-£0.50 (50p less)": "- £0.50 (50p less)",
        "-£1 (one pound less)": "- £1 (one pound less)",
        "-£5 (five pounds less)": "- £5 (five pounds less)",
    },
}

PERSONA_COLS = ["sex", "noncis", "queer", "ethnic", "education", "ideo"]

# `sex`/`noncis`/`queer`/`ideo` carry NO value labels in the .dta at all — only
# `replication_electoralstudies.R`'s own `factor(..., labels = ...)` calls
# supply text (df$sex, df$noncis, df$queer, df$ideo, all read directly from
# that script and declared here). `ethnic`/`education` are NOT listed here:
# they resolve from the .dta's OWN value labels in `load()` instead, because
# those exist natively and retyping them would risk a silent drift from the
# source the way a hand-copied table always can.
PERSONA_LABELS: dict[str, dict[int, str]] = {
    "sex": {0: "Man", 1: "Woman"},
    "noncis": {0: "Cisgender", 1: "Not cisgender"},
    "queer": {0: "Hetero", 1: "LGB"},
    "ideo": {0: "Left", 1: "Centre", 2: "Right"},
}
# `education` code 1 is the literal value label "DATA EXPIRED" (a third-party
# panel-matching sentinel QC rule 12's non-answer regex does not catch —
# "expired" is not in its wordlist) and code 3 is "Don't know / not
# applicable" (which the regex WOULD catch, declared here anyway so the
# generator does not depend on that catching it later). Both resolve to a
# genuine blank in the wide CSV, not a rendered label.
PERSONA_NON_ANSWER_CODES: dict[str, set[int]] = {"education": {1, 3}}

KEY_VARS = [f"{a}_A_t1" for a in ATTR_NAMES] + [f"{a}_B_t1" for a in ATTR_NAMES]


def _task_cols(t: int) -> list[str]:
    return [f"{a}_A_t{t}" for a in ATTR_NAMES] + [f"{a}_B_t{t}" for a in ATTR_NAMES]


def load() -> tuple[pd.DataFrame, dict[str, dict[int, str]], dict[str, dict[int, str]]]:
    ds = spss.read(RAW)
    df = ds.df
    if df.shape != (N_PROFILE_ROWS, 70):
        raise ValueError(f"deposit shape drifted: {df.shape}, expected ({N_PROFILE_ROWS}, 70)")
    if df["IDvar"].nunique() != N_RESPONDENTS:
        raise ValueError(f"{df['IDvar'].nunique()} respondents, expected {N_RESPONDENTS}")
    counts = df.groupby("IDvar").size()
    if not (counts == 2 * N_TASKS).all():
        raise ValueError("not every respondent has exactly 10 rows (5 tasks x 2 profiles)")
    if sorted(df["task"].unique()) != list(range(1, N_TASKS + 1)):
        raise ValueError(f"task values are not exactly 1..{N_TASKS}: {sorted(df['task'].unique())}")
    if sorted(df["profile"].unique()) != [1, 2]:
        raise ValueError(f"profile values are not exactly [1, 2]: {sorted(df['profile'].unique())}")
    # The forced-choice key: `selected` (per-profile 0/1) must equal
    # `profile == choice` (the task-level winner) on every row — same
    # structural check as PMV0TG's `select == (candidate == ans)`.
    if not (df["selected"] == (df["profile"] == df["choice"]).astype(float)).all():
        raise ValueError("selected != (profile == choice) somewhere — the forced-choice key is off")
    if not (df.groupby(["IDvar", "task"])["choice"].nunique() == 1).all():
        raise ValueError("`choice` is not constant within (IDvar, task)")

    levels: dict[str, dict[int, str]] = {}
    for attr, _ in ATTRS:
        numcol = f"{attr}_num"
        vl = ds.value_labels.get(numcol)
        if not vl:
            raise ValueError(f"{numcol}: no value labels in the .dta (expected the original file)")
        levels[attr] = {int(k): v for k, v in vl.items()}
        data_set = set(levels[attr].values())
        exceptions = _KNOWN_TEXT_EXCEPTIONS.get(attr, {})
        reconciled = {exceptions.get(v, v) for v in data_set}
        expected = TABLE_A3_LEVELS[attr]
        if reconciled != expected:
            raise ValueError(
                f"{attr}: data levels (after declared exceptions) {reconciled} != "
                f"Table A.3 levels {expected} — an undeclared discrepancy exists, read it "
                "before adding it to _KNOWN_TEXT_EXCEPTIONS"
            )

    persona_levels: dict[str, dict[int, str]] = {k: dict(v) for k, v in PERSONA_LABELS.items()}
    for col in ("ethnic", "education"):
        vl = ds.value_labels.get(col)
        if not vl:
            raise ValueError(f"{col}: no value labels in the .dta (expected the original file)")
        persona_levels[col] = {int(k): v for k, v in vl.items()}
    return df, levels, persona_levels


def build_wide(df: pd.DataFrame, persona_levels: dict[str, dict[int, str]]) -> pd.DataFrame:
    """One row per respondent, 5 tasks' worth of columns each."""
    records: list[dict[str, Any]] = []
    for resp_id, grp in df.groupby("IDvar", sort=True):
        tasks = sorted(grp["task"].unique())
        if tasks != list(range(1, N_TASKS + 1)):
            raise ValueError(f"{resp_id}: tasks are not exactly 1..{N_TASKS}")
        persona_vals = grp[PERSONA_COLS].drop_duplicates(keep="first")
        # NaN != NaN, so a respondent whose persona field is genuinely missing
        # on every row still collapses to one row here (all ten copies equal,
        # including all-NaN) — drop_duplicates treats repeated NaN as one
        # value within a column, which is what "constant within respondent"
        # means for a field nobody answered.
        if len(persona_vals) != 1:
            raise ValueError(f"{resp_id}: persona fields are not constant across tasks")
        rec: dict[str, Any] = {"IDvar": resp_id}
        for col in PERSONA_COLS:
            raw = persona_vals.iloc[0][col]
            if pd.isna(raw):
                rec[col] = None
                continue
            code = int(raw)
            if code in PERSONA_NON_ANSWER_CODES.get(col, set()):
                rec[col] = None  # a sentinel code carries no answer — left blank, not labelled
                continue
            rec[col] = persona_levels[col][code]

        for t in range(1, N_TASKS + 1):
            task_rows = grp[grp["task"] == t]
            a_row = task_rows[task_rows["profile"] == 1]
            b_row = task_rows[task_rows["profile"] == 2]
            if len(a_row) != 1 or len(b_row) != 1:
                raise ValueError(f"{resp_id} task {t}: not exactly one profile-1 and one profile-2 row")
            a_row, b_row = a_row.iloc[0], b_row.iloc[0]
            for attr, _ in ATTRS:
                rec[f"{attr}_A_t{t}"] = int(a_row[f"{attr}_num"])
                rec[f"{attr}_B_t{t}"] = int(b_row[f"{attr}_num"])
            rec[f"choice_t{t}"] = int(a_row["choice"])
        records.append(rec)

    wide = pd.DataFrame.from_records(records)
    expected_cols = 1 + len(PERSONA_COLS) + N_TASKS * (2 * len(ATTRS) + 1)
    assert wide.shape == (N_RESPONDENTS, expected_cols), wide.shape
    return wide


def build_arms(wide: pd.DataFrame, levels: dict[str, dict[int, str]]) -> list[dict[str, Any]]:
    """Every distinct 20-attribute (Policy A, Policy B) pair actually drawn.

    Task-major, respondent-row-major within each task — declared, not left to
    prose (the PMV0TG/EFXNLX precedent: "scanning X across all respondents"
    reads equally well two ways). Dedup by tuple is safe here exactly as it
    was for PMV0TG, not EFXNLX: `shared_context` and the outcome wording are
    byte-identical across all 5 tasks (no position-dependent preamble), so a
    repeat of the same 20-attribute tuple at a different task position
    resolves to the SAME arm correctly, rather than risking the wrong
    position-dependent text the way a collision would for EFXNLX's 5-pair
    preambles.
    """
    arms: list[dict[str, Any]] = []
    seen: dict[tuple[int, ...], int] = {}

    for t in range(1, N_TASKS + 1):
        cols = _task_cols(t)
        for _, row in wide.iterrows():
            codes = [int(row[c]) for c in cols]
            key = tuple(codes)
            if key in seen:
                continue
            seen[key] = len(arms)
            codes_a, codes_b = codes[: len(ATTRS)], codes[len(ATTRS) :]

            def block(label: str, side_codes: list[int]) -> str:
                lines = [label]
                for (attr, row_label), code in zip(ATTRS, side_codes, strict=True):
                    lines.append(f"- {row_label}: {levels[attr][code]}")
                return "\n".join(lines)

            factors = {}
            for (attr, _), code in zip(ATTRS, codes_a, strict=True):
                factors[f"{attr}_A"] = levels[attr][code]
            for (attr, _), code in zip(ATTRS, codes_b, strict=True):
                factors[f"{attr}_B"] = levels[attr][code]

            text = f"{block('Policy A', codes_a)}\n\n{block('Policy B', codes_b)}"
            arms.append(
                {
                    "raw_values": dict(zip(KEY_VARS, codes, strict=True)),
                    "condition_num": len(arms),
                    "factors": factors,
                    "text": text,
                }
            )
    return arms


_CHOICE_Q = (
    "Which of these two i-voting policies do you prefer? "
    '1 means "Policy A"; 2 means "Policy B".'
)


def build_outcomes() -> list[dict[str, Any]]:
    outcomes: list[dict[str, Any]] = []
    for t in range(1, N_TASKS + 1):
        outcomes.append(
            {
                "var": f"choice_t{t}",
                "task_num": t - 1,
                "question": _CHOICE_Q,
                "scale": {"min": 1, "max": 2, "nominal": True},
                "response_recode": {1: 1, 2: 2},
                "condition_vars": _task_cols(t),
            }
        )
    return outcomes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="compare against the recipe + wide CSV")
    ap.add_argument("--write", action="store_true", help="regenerate the wide CSV and the recipe")
    args = ap.parse_args()

    df, levels, persona_levels = load()
    wide = build_wide(df, persona_levels)
    generated_arms = build_arms(wide, levels)
    generated_outcomes = build_outcomes()

    recipe = yaml.safe_load(RECIPE.read_text()) if RECIPE.exists() else {}
    current_arms = recipe.get("condition", {}).get("arms", [])
    current_outcomes = recipe.get("outcomes", [])
    print(f"generated {len(generated_arms):,} arms; recipe holds {len(current_arms):,}")
    print(f"generated {len(generated_outcomes)} outcomes; recipe holds {len(current_outcomes)}")

    if args.write:
        WIDE.parent.mkdir(parents=True, exist_ok=True)
        wide.to_csv(WIDE, index=False)
        print(f"wrote {WIDE.relative_to(REPO)} ({wide.shape[0]} x {wide.shape[1]})")
        recipe.setdefault("condition", {})["arms"] = generated_arms
        recipe["outcomes"] = generated_outcomes
        RECIPE.write_text(yaml.safe_dump(recipe, sort_keys=False, allow_unicode=True, width=100))
        print(f"wrote {RECIPE.relative_to(REPO)}")
        return 0

    ok = True
    if not WIDE.exists():
        print("wide CSV missing — run --write")
        ok = False
    else:
        on_disk = pd.read_csv(WIDE)
        if not on_disk.equals(wide):
            print("WIDE CSV DIFFERS from what this script derives")
            ok = False
    if generated_arms != current_arms:
        ok = False
        print("ARMS DIFFER")
        for i, (g, c) in enumerate(zip(generated_arms, current_arms, strict=False)):
            if g != c:
                print(f"  first difference at arm {i}:\n    generated {g}\n    recipe    {c}")
                break
    if generated_outcomes != current_outcomes:
        ok = False
        print("OUTCOMES DIFFER")
    if ok:
        print("IDENTICAL — the recipe and wide CSV are exactly what this file derives")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
