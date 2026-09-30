"""The melt: recipe + survey data -> (P, c, o, r) rows.

Pure and deterministic. Everything requiring judgment lives in the recipe;
this module only mechanically applies it. That split is what makes the melt
testable against a fixture and verifiable against an external oracle.

One row per (respondent x outcome item) where the response is present and
not a missing code — matching how SocSci210 drops refused items individually
rather than excluding the whole respondent.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from typing import Any

from ..recipe import Recipe
from ..schema import Persona, Row
from ..sources.spss import Dataset


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    return isinstance(value, float) and math.isnan(value)


def _as_code(raw: Any) -> int | None:
    """The value as an integer code, or None if it is not one."""
    try:
        f = float(raw)
    except (TypeError, ValueError):
        return None
    return int(f) if f == int(f) else None


def _codes_for(mapping: dict[str, Any], var: str) -> Any:
    """Look a variable up in a recipe override map, ignoring case.

    Recipes and deposits disagree about capitalisation, so a case-sensitive
    lookup would silently ignore a declared override — the same class of bug as
    the one that dropped three studies' whole persona.
    """
    if var in mapping:
        return mapping[var]
    upper = var.upper()
    for k, v in mapping.items():
        if k.upper() == upper:
            return v
    return ()


def _persona(ds: Dataset, row: Any, recipe: Recipe) -> Persona:
    """Build a Persona by resolving each mapped source variable to its label."""
    fields: dict[str, Any] = {}
    extra: dict[str, str] = {}
    known = set(Persona.model_fields) - {"extra"}
    # SPSS/Stata variable names are case-insensitive in practice and deposits are
    # inconsistent about it, so resolve case-insensitively. A case-sensitive
    # lookup here silently dropped the ENTIRE persona of three studies — 33
    # mapped fields, 7,679 rows — because the recipes said `ppincimp` and the
    # files said `PPINCIMP`. Nothing caught it: QC never inspected persona and
    # crosscheck does not compare it.
    by_upper = {str(k).upper(): k for k in row.index}
    for field, var in recipe.persona_map.items():
        key = by_upper.get(var.upper())
        if key is None:
            continue
        raw = row[key]
        if _is_blank(raw):
            continue
        # A sentinel code carries no answer, so leave the field empty rather than
        # rendering its label — "Religion: Refused" is worse than no religion.
        code = _as_code(raw)
        if code is not None and code in _codes_for(recipe.persona_missing, var):
            continue
        # A code that IS an answer but whose panel label carries scripting
        # boilerplate ("Other Christian religion, please specify") gets rewritten,
        # because dropping it would throw away a real response.
        rewrite = _codes_for(recipe.persona_label_rewrite, var) or {}
        label = rewrite.get(code) if code is not None else None
        if label is None:
            label = ds.label(key, raw)
        if field in known:
            # age / household_size are ints on the model; everything else is text.
            if field in {"age", "household_size"}:
                try:
                    fields[field] = int(float(raw))
                except (TypeError, ValueError):
                    continue
            else:
                fields[field] = label
        else:
            extra[field] = label
    return Persona(**fields, extra=extra)


def build_rows(ds: Dataset, recipe: Recipe) -> Iterator[Row]:
    """Melt one study into canonical rows."""
    arms = recipe.condition.by_raw()
    missing = set(recipe.missing_codes)
    cvars = recipe.condition.variables

    for cvar in cvars:
        if cvar not in ds.df.columns:
            raise ValueError(f"condition variable {cvar!r} not in data")
    for outcome in recipe.outcomes:
        for declared_arm in recipe.condition.arms:
            var = recipe.outcome_var_for(outcome, declared_arm)
            if var is not None and var not in ds.df.columns:
                raise ValueError(f"outcome variable {var!r} not in data")

    # A mapped persona variable that is not in the file is a mistake, never an
    # intention: the recipe asked for a field and would silently get an empty
    # one. Three studies lost their whole persona this way. Fail loudly instead —
    # `persona_map` is a declaration, so a name that resolves to nothing is as
    # much an error as a missing outcome variable.
    present = {str(c).upper() for c in ds.df.columns}
    absent = {f: v for f, v in recipe.persona_map.items() if v.upper() not in present}
    if absent:
        raise ValueError(
            f"persona variables not in data: {absent} — a mapped field that "
            "resolves to nothing would render an empty persona silently"
        )

    for idx, row in ds.df.iterrows():
        codes = [row[v] for v in cvars]
        if any(_is_blank(c) for c in codes):
            continue
        arm = arms.get(tuple(int(float(c)) for c in codes))
        if arm is None:  # arm not declared in the recipe -> not part of the experiment
            continue

        persona = _persona(ds, row, recipe)
        condition_text = recipe.condition.render(arm)

        for outcome in recipe.outcomes:
            # Both the answer variable and its coding can vary: split-ballot
            # studies ask each arm a different question, option-order designs
            # reverse the codes per arm, and a study's items can sit on
            # different scales (e.g. banded dollars vs banded minutes).
            recode = recipe.recode_for(arm, outcome)
            var = recipe.outcome_var_for(outcome, arm)
            if var is None:
                continue
            raw = row[var]
            if _is_blank(raw):
                continue
            ivalue = int(float(raw))
            if ivalue in missing:
                continue
            if ivalue not in recode:
                continue  # value outside the declared scale -> drop, don't guess
            response = recode[ivalue]

            yield Row(
                persona=persona,
                condition=condition_text,
                outcome=recipe.outcome_text_for(outcome, arm),
                response=str(response),
                response_num=float(response),
                condition_num=arm.condition_num,
                task_num=outcome.task_num,
                source=recipe.source,
                study_id=recipe.study_id,
                experiment=recipe.experiment,
                # Namespaced by study: these rows get merged into one corpus, and a
                # bare row index collapsed 23,464 respondents into 4,010 ids.
                participant_id=f"{recipe.study_id}:{idx}",
            )
