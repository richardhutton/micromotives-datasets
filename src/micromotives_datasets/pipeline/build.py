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
import re
from collections.abc import Iterator
from typing import Any

from ..persona.crosswalk import Crosswalk
from ..recipe import Arm, Recipe
from ..schema import Persona, Row
from ..sources import quex
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


def _persona(ds: Dataset, row: Any, recipe: Recipe, cw: Crosswalk | None = None) -> Persona:
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
        # Harmonise to the shared vocabulary, so rows from surveys that banded
        # or categorised this attribute differently describe the same person the
        # same way. An unmapped label passes through unchanged and is reported
        # by QC rule 14 rather than silently blanked.
        if cw is not None:
            label = cw.apply(field, label)

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
    # Loaded once per study: the crosswalk is small and identical for every row.
    cw = Crosswalk.load()
    arms = recipe.condition.by_raw()
    order_vars = recipe.condition.line_order_vars or []
    missing = set(recipe.missing_codes)
    cvars = recipe.condition.variables
    # An outcome may carry its own assignment variable, for a design where the
    # arm varies WITHIN respondent (the same person rated eight of 72 vignettes).
    # Where none does, every item shares the study-level assignment and this is
    # the same single lookup as before.
    per_item = {o.task_num: recipe.condition_vars_for(o) for o in recipe.outcomes}
    within_subject = any(v != cvars for v in per_item.values())

    witness_vars = recipe.condition.witness_vars
    for cvar in {v for vs in per_item.values() for v in vs} | set(cvars) | set(witness_vars):
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

    # Resolved once per study: the column names, upper-cased, for looking up a
    # respondent variable whatever case the recipe wrote it in.
    cols = {str(c).upper(): c for c in ds.df.columns}

    def _for_respondent(text: str, who: quex.Values) -> str:
        """Resolve any inline directive that depends on who is answering.

        A no-op for the usual study, which declares no `respondent_vars` and so
        cannot contain a directive this would resolve. Where one IS declared,
        `quex.resolve_inline` raises on a directive it cannot read, which is the
        behaviour we want: the alternative is shipping bracket notation into the
        corpus as stimulus text, which is what this exists to stop.
        """
        if not who:
            return text
        out = quex.resolve_inline(text, who)
        if out == text:
            return text
        # A branch resolving to nothing leaves a gap the survey engine would have
        # closed: "would you want [IF PPGENDER=1 INSERT: her] to have" reads
        # "would you want  to have" for a female respondent. Tidied ONLY where
        # resolution actually changed the string, so text that legitimately holds
        # a double space keeps it — typography normalises, words never do
        # (docs/CONVENTIONS.md).
        out = re.sub(r"[ \t]{2,}", " ", out)
        # A branch resolving to nothing at the END leaves a trailing space (IP 9.13's
        # second appeal, absent for most respondents).
        return re.sub(r"[ \t]+([,.;:?!])", r"\1", out).strip()

    def arm_for(row: Any, variables: list[str]) -> Arm | None:
        """The declared arm this respondent saw, by these assignment variables."""
        codes = [row[v] for v in variables]
        if any(_is_blank(c) for c in codes):
            return None
        # Not in the recipe's arms -> not part of this experiment. Silent by
        # design: deposits carry respondents from other blocks of the same field.
        return arms.get(tuple(int(float(c)) for c in codes))

    def witnessed_arms_for(row: Any) -> list[Arm]:
        """Every condition this respondent was asked, by the not-asked codes.

        None is ordinary — a deposit carries people from other blocks of the same
        omnibus. More than one is a defect in the instrument's routing, and the
        caller counts those rather than picking one.
        """
        codes: dict[str, int | None] = {}
        for var in witness_vars:
            value = row[var]
            codes[var] = None if _is_blank(value) else int(float(value))
        return recipe.condition.arms_asked(codes)

    # Each arm's OWN outcome variables: the ones only that condition was asked.
    # A variable shared by several arms proves nothing about routing, so it is
    # left out rather than read as a second condition.
    own_vars: dict[int, set[str]] = {}
    var_arms: dict[str, set[int]] = {}
    for owner in arms.values():
        declared = {owner.outcome_var} | {it.outcome_var for it in owner.items.values()}
        names = {cols.get(n.upper(), n) for n in declared if n}
        own_vars[id(owner)] = names
        for n in names:
            var_arms.setdefault(n, set()).add(id(owner))
    exclusive = {n for n, owners in var_arms.items() if len(owners) == 1}

    def answered_elsewhere(row: Any, arm: Arm) -> bool:
        """True when this respondent has ANY code in a variable only another arm was asked.

        Any code, "Don't know" included: a recorded non-answer still means the
        question was put to them. Only a blank means it was not.
        """
        for other in arms.values():
            if other is arm:
                continue
            for var in own_vars[id(other)] & exclusive:
                if var in row.index and not _is_blank(row[var]):
                    return True
        return False

    ambiguous = 0

    for idx, row in ds.df.iterrows():
        if witness_vars:
            asked = witnessed_arms_for(row)
            if len(asked) > 1:
                # Two conditions is no condition: the tuple this corpus is made of
                # has exactly one, and we cannot know which of the two they met.
                ambiguous += 1
            study_arm = asked[0] if len(asked) == 1 else None
        else:
            study_arm = arm_for(row, cvars)
            # The assignment column names one condition, but the respondent may
            # still have met another: a back-button in a web survey re-assigns,
            # and the answer to the abandoned condition stays in the file. DEL's
            # Feb 2023 sandbox has one such person, with page timings on both.
            # Their answer to the assigned condition may have been given after
            # seeing the other, so they have no single condition either.
            if (
                recipe.condition.routing_check
                and study_arm is not None
                and not within_subject
                and answered_elsewhere(row, study_arm)
            ):
                ambiguous += 1
                continue
        # A between-subjects design can skip the whole respondent on an
        # unassigned code. A within-subject one cannot: missing a vignette in
        # slot 1 says nothing about slots 2-8, and dropping the respondent would
        # throw away the seven items they did answer.
        if study_arm is None and not within_subject:
            continue

        # The positions this respondent saw each condition line in, when the
        # instrument randomised them. `8ctbk` records six, and 654 of the 720
        # possible orders occur, so one fixed rendering is right for about 1 row
        # in 720.
        line_order: list[int] | None = None
        if order_vars:
            codes = [row[v] for v in order_vars]
            line_order = (
                None if any(_is_blank(c) for c in codes) else [int(float(c)) for c in codes]
            )

        # The respondent's own identifier, where the recipe declares one. A panel
        # wave is its own file, so the row index would make the same person two
        # unrelated participants and lose the wave-on-wave link.
        who_id: str | None = None
        if recipe.participant_id_var is not None:
            key = cols.get(recipe.participant_id_var.upper())
            if key is None:
                raise ValueError(f"participant_id_var {recipe.participant_id_var!r} not in data")
            raw_id = row[key]
            if _is_blank(raw_id):
                raise ValueError(
                    f"{recipe.study_id}: row {idx} has no {recipe.participant_id_var!r} — "
                    "an unidentified respondent would silently fall back to the row index "
                    "and break the panel link for everyone after them"
                )
            # SPSS stores a numeric id as a float, so str() gives "120615074968.0".
            # Another file holding the same person as an integer would then give
            # them a second id and silently break the cross-file link (DEL's
            # GUNQID recurs across ten files). A whole number is written whole.
            if isinstance(raw_id, float) and raw_id.is_integer():
                raw_id = int(raw_id)
            who_id = str(raw_id).strip()

        persona = _persona(ds, row, recipe, cw)
        # Stimulus wording that varies by RESPONDENT, not by arm — a pronoun
        # chosen from the respondent's own recorded sex, say. Resolved per row
        # against the declared variables only, through the shared directive
        # parser, which refuses a condition it cannot read rather than guessing.
        who: quex.Values = {}
        for var in recipe.respondent_vars:
            key = cols.get(var.upper())
            who[var.upper()] = None if key is None else _as_code(row[key])

        for outcome in recipe.outcomes:
            arm = (
                study_arm
                if per_item[outcome.task_num] == cvars
                else arm_for(row, per_item[outcome.task_num])
            )
            if arm is None:
                continue
            # Per (condition, outcome), not per condition: an outcome can sit
            # where only part of the stimulus has happened yet. And where the
            # instrument randomised the order its attribute rows appeared in,
            # render THIS respondent's order rather than one fixed guess.
            # A list whose statements were shuffled per respondent, with its own
            # order variables per (arm, item) cell. Skipped when unrecorded: a
            # guessed order is the 8ctbk failure again.
            bullet_order: list[int] | None = None
            item = recipe.item_for(outcome, arm)
            if item is not None and item.line_order_vars:
                unrecorded_vars = [v for v in item.line_order_vars if v.upper() not in cols]
                if unrecorded_vars:
                    raise ValueError(f"line_order_vars {unrecorded_vars} not in data")
                codes = [row[cols[v.upper()]] for v in item.line_order_vars]
                if any(_is_blank(c) or float(c) < 1 for c in codes):
                    # No order recorded. A row nobody answered has nothing to
                    # lose; an ANSWERED one would vanish silently, so it stops
                    # the build instead (zero today in IP 9.17).
                    answer_var = recipe.outcome_var_for(outcome, arm)
                    answer = row[cols[answer_var.upper()]] if answer_var else None
                    if (
                        answer is not None
                        and not _is_blank(answer)
                        and (int(float(answer)) not in missing)
                    ):
                        raise ValueError(
                            f"{recipe.study_id}: row {idx} answered task {outcome.task_num} "
                            "but its statement order is not recorded"
                        )
                    continue
                bullet_order = [int(float(c)) for c in codes]
            condition_text = _for_respondent(
                recipe.condition_text_for(outcome, arm, line_order, bullet_order), who
            )
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
                outcome=_for_respondent(recipe.outcome_text_for(outcome, arm), who),
                response=str(response),
                response_num=float(response),
                condition_num=arm.condition_num,
                task_num=outcome.task_num,
                factors=dict(arm.factors),
                source=recipe.source,
                study_id=recipe.study_id,
                experiment=recipe.experiment,
                # Namespaced by study: these rows get merged into one corpus, and a
                # bare row index collapsed 23,464 respondents into 4,010 ids.
                participant_id=f"{recipe.study_id}:{who_id if who_id is not None else idx}",
            )

    # Checked once the melt has seen every respondent, so the number is the whole
    # file's and not a prefix of it. A mismatch either way is a failure: fewer
    # than declared means the deposit changed under a judgement made about the
    # old one, more means a discard nobody has looked at.
    if ambiguous != recipe.condition.ambiguous_routing:
        raise ValueError(
            f"{recipe.study_id}: {ambiguous} respondent(s) were routed to more than one "
            f"condition, but the recipe declares ambiguous_routing="
            f"{recipe.condition.ambiguous_routing}. Read the routing before changing the "
            f"number — a respondent with two conditions has none, and is dropped."
        )
