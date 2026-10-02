#!/usr/bin/env python3
"""Derive EFXNLX's conjoint arms from the data, rather than hand-typing them.

`recipes/EFXNLX.yaml` declares one arm per distinct (respondent, pair) PAIR
actually drawn — the condition is "the two profiles shown together" (see the
recipe's own notes and docs/CONVENTIONS.md's row-shape ruling), not a single
profile, so the key is all 8 attributes on BOTH sides at once (16 columns).

Verified before writing this file (see the maker's report, not repeated here):
  * all 16,465 (respondent, pair) attribute 16-tuples are DISTINCT — zero
    collisions across the whole deposit, so every arm belongs to exactly one
    pair POSITION (1, or 2-5) and the position-dependent preamble below can
    never be attached to the wrong instance.
  * no attribute column is missing for any respondent at any pair position.
  * every attribute's value-label set is byte-identical across t1..t5 (no
    questionnaire drift between pair slots).

The 8 attribute rows are rendered in THIS RESPONDENT's own on-screen order
(`list_table`), not a fixed canonical order — see `_attribute_order` below for
why that is resolved here rather than via `condition.line_order_vars`.

    uv run python scripts/gen_EFXNLX.py --check   # agree with the recipe?
    uv run python scripts/gen_EFXNLX.py --write   # regenerate the arms
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import Any

import yaml

from micromotives_datasets.sources import spss

REPO = Path(__file__).resolve().parents[1]
RECIPE = REPO / "recipes" / "EFXNLX.yaml"
DATA = REPO / "data" / "raw" / "EFXNLX" / "LSEResults_Brexit_170428_client.sav"

# The 8 attributes, in the on-screen table's own row order (questionnaire.docx
# `col_1`, lines 173 and 237-245). The row LABEL is the table's own left-column
# text, read from the .sav's variable label (`_seen1_t1`'s column label) rather
# than retyped — it is identical to the questionnaire's `col_1` array.
ATTRS = ["imigration", "rights", "trade", "laws", "budget", "payment", "border", "timeline"]

# The two position-dependent preambles (questionnaire.docx lines 394 and 597,
# the latter repeated verbatim at 801/1005/1208 for pairs 3/4/5 — grep-confirmed
# identical). `<<br/>>` is the survey engine's own line-break markup, not a word
# a respondent read; it renders as the paragraph break below.
PREAMBLE_FIRST = (
    "We are interested in your opinions about the negotiations between Britain "
    "and the European Union regarding Britain's exit from the EU and future "
    "relationship with the EU.\n\nPlease look carefully at these two possible "
    "outcomes:"
)
PREAMBLE_LATER = (
    "And now please look carefully at these two possible outcomes of the Brexit negotiations:"
)

# Canonical column names used as the generic keys in every arm's `raw_values`
# and as `condition.source_vars` — pair 1's own columns, exactly as 9xw67 used
# V1_A's. The melt matches by VALUE, positionally, never by these names, so an
# arm built from pair 3's columns is keyed under these same generic names.
KEY_VARS = [f"{a}_seen1_t1" for a in ATTRS] + [f"{a}_seen2_t1" for a in ATTRS]


def _condition_vars(t: int) -> list[str]:
    return [f"{a}_seen1_t{t}" for a in ATTRS] + [f"{a}_seen2_t{t}" for a in ATTRS]


def _attribute_order(raw: Any) -> list[int]:
    """This respondent's own on-screen attribute row order.

    `list_table` (questionnaire.docx line 168: `list_table =
    random_shuffle([1,2,3,4,5,6,7,8])`, drawn once before pair 1 and reused
    UNCHANGED for pairs 2-5, lines 203-233 vs. 537-559/741-763/945-967/1148-1170)
    is a string-encoded permutation of 1..8, e.g. `'[3, 2, 7, 6, 4, 8, 5, 1]'`.
    Position p (1-based) on screen shows `col_1[list_table[p-1]-1]` — i.e.
    `ATTRS[order[p-1] - 1]` here, since `ATTRS` is written in `col_1`'s own
    order (questionnaire.docx line 173).

    This is `column 166 of 422` in the .sav (non-null for all 3,293
    respondents, 3,137 distinct values, zero respondents drawing the canonical
    [1,2,3,4,5,6,7,8]) — the recipe's own notes used to assert no such column
    exists; it does, and this is what reads it. Resolved HERE, once per
    (respondent, pair) condition, rather than via `condition.line_order_vars`:
    that mechanism exists for a design where several respondents share one
    declared arm and the order is a per-ROW property looked up at melt time
    from several separate order columns (`8ctbk`'s six
    `Attribute<n>_Order_*`). Here every arm is already 1:1 with a single
    (respondent, pair) instance (zero collisions across all 16,465 attribute
    16-tuples — see the module docstring), so the order is a fixed property of
    the arm being generated, not something to re-derive per row, and the
    source encodes it as one compound string rather than one column per slot.
    Extending the shared `Condition`/build.py machinery to parse a list-coded
    string would serve only this one recipe and touch code `8ctbk` depends on;
    doing it here keeps `line_order_vars` doing the one job it was built for.
    """
    order = ast.literal_eval(raw)
    if sorted(order) != list(range(1, 9)):
        raise ValueError(f"list_table is not a permutation of 1..8: {raw!r}")
    return [int(x) for x in order]


def build_arms() -> list[dict[str, Any]]:
    """Every distinct (respondent, pair) 16-attribute PAIR actually shown.

    Scan order is pair-position-major (t=1..5), respondent-row-major within
    each position — declared, not left to prose, per the 9xw67 lesson that
    "scanning X across all respondents" reads equally well two ways.
    """
    ds = spss.read(DATA)
    value_labels = {a: dict(ds.value_labels.get(f"{a}_seen1_t1") or {}) for a in ATTRS}
    row_labels = {a: ds.column_labels[f"{a}_seen1_t1"] for a in ATTRS}

    arms: list[dict[str, Any]] = []
    seen: dict[tuple[int, ...], int] = {}

    for t in range(1, 6):
        cols = _condition_vars(t)
        preamble = PREAMBLE_FIRST if t == 1 else PREAMBLE_LATER
        for _, row in ds.df.iterrows():
            codes = []
            for col in cols:
                value = row[col]
                if value is None or value != value:  # NaN
                    codes = []
                    break
                codes.append(int(float(value)))
            if not codes:
                continue
            key = tuple(codes)
            if key in seen:
                continue
            seen[key] = len(arms)
            codes_a, codes_b = codes[:8], codes[8:]
            order = _attribute_order(row["list_table"])

            def block(label: str, side_codes: list[int], order: list[int] = order) -> str:
                lines = [label]
                # Screen position p shows ATTRS[order[p-1] - 1], per the
                # questionnaire's own `col_1[list_table[p-1]-1]`. Iterating
                # `ATTRS` directly here is what rendered 16,465 conditions in an
                # order no respondent saw.
                for slot in order:
                    a = ATTRS[slot - 1]
                    lines.append(f"- {row_labels[a]}: {value_labels[a][side_codes[slot - 1]]}")
                return "\n".join(lines)

            factors = {}
            for a, code in zip(ATTRS, codes_a, strict=True):
                factors[f"{a}_A"] = value_labels[a][code]
            for a, code in zip(ATTRS, codes_b, strict=True):
                factors[f"{a}_B"] = value_labels[a][code]

            text = f"{preamble}\n\n{block('Outcome A', codes_a)}\n\n{block('Outcome B', codes_b)}"
            arms.append(
                {
                    "raw_values": dict(zip(KEY_VARS, codes, strict=True)),
                    "condition_num": len(arms),
                    "factors": factors,
                    "text": text,
                }
            )
    return arms


_CHOICE_Q = 'Which of these two outcomes do you prefer? 1 means "Outcome A"; 2 means "Outcome B".'
_ACCEPT_Q = (
    "How acceptable or unacceptable are each of the outcomes to you personally? "
    'Report only your rating of "Outcome {side}".'
)


def build_outcomes() -> list[dict[str, Any]]:
    outcomes: list[dict[str, Any]] = []
    for t in range(1, 6):
        base = (t - 1) * 3
        cvars = _condition_vars(t)
        outcomes.append(
            {
                "var": f"QB1_PAIR{t}",
                "task_num": base,
                "question": _CHOICE_Q,
                "scale": {"min": 1, "max": 2, "nominal": True},
                "response_recode": {1: 1, 2: 2},
                "condition_vars": cvars,
            }
        )
        outcomes.append(
            {
                "var": f"QB2gridA_PAIR{t}",
                "task_num": base + 1,
                "question": _ACCEPT_Q.format(side="A"),
                "scale": {
                    "min": 1,
                    "max": 4,
                    "min_label": "Completely acceptable",
                    "max_label": "Completely unacceptable",
                },
                "response_recode": {1: 1, 2: 2, 3: 3, 4: 4},
                "condition_vars": cvars,
            }
        )
        outcomes.append(
            {
                "var": f"QB2gridB_PAIR{t}",
                "task_num": base + 2,
                "question": _ACCEPT_Q.format(side="B"),
                "scale": {
                    "min": 1,
                    "max": 4,
                    "min_label": "Completely acceptable",
                    "max_label": "Completely unacceptable",
                },
                "response_recode": {1: 1, 2: 2, 3: 3, 4: 4},
                "condition_vars": cvars,
            }
        )
    return outcomes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="compare against the recipe")
    ap.add_argument("--write", action="store_true", help="rewrite the recipe's arms/outcomes")
    args = ap.parse_args()

    generated_arms = build_arms()
    generated_outcomes = build_outcomes()
    recipe = yaml.safe_load(RECIPE.read_text())
    current_arms = recipe["condition"]["arms"]
    current_outcomes = recipe["outcomes"]
    print(
        f"generated {len(generated_arms):,} arms ({recipe.get('condition', {}).get('arms', []) and ''}); "
        f"recipe holds {len(current_arms):,}"
    )
    print(f"generated {len(generated_outcomes)} outcomes; recipe holds {len(current_outcomes)}")

    if args.write:
        recipe["condition"]["arms"] = generated_arms
        recipe["outcomes"] = generated_outcomes
        RECIPE.write_text(yaml.safe_dump(recipe, sort_keys=False, allow_unicode=True, width=100))
        print(f"wrote {RECIPE.relative_to(REPO)}")
        return 0

    ok = True
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
        print("IDENTICAL — the recipe is exactly what this file derives")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
