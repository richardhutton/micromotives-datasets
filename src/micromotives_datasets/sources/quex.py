"""Resolve the scripting directives in a fielded questionnaire.

TESS questionnaires do not contain one written block per arm. They contain a
template plus programmer directives, and the arm a respondent actually saw is
what those directives evaluate to. `zaqkm`'s 40 arms are 5 first paragraphs x 8
second-paragraph blocks, each branching again on
`[SHOW IF DOV_MENTALHEALTH=2: alcohol use disorder ...]`.

Three of the last four studies built (`dh3nj`, `z358z`, `zaqkm`) assembled their
arm text from templated fragments, and each maker wrote its own throwaway parser
(ledger #51). This is the shared one. It matters more than a utility usually
would, because **the condition is the only part of a row we write**: persona,
outcome and response are all read from the data, so a mis-assembled arm teaches
a model the wrong question and nothing downstream can detect it.

WHAT THE DIRECTIVES ACTUALLY LOOK LIKE. Measured over all 127 questionnaire
files in `data/raw`, not inferred from the three studies that prompted this:
1,522 conditional directives, 630 distinct conditions. `[SHOW IF ...]` 809 uses
across 49 files, `[IF ... DISPLAY]` 578 across 52, `[INSERT IF ...]` 311 across
35. The operators are `=` (1,770), `<>` (49), `>=` (41), `<` (34), `>` (22),
`<=` (1); the connectives `AND` (265), `OR` (169), `NOT` (53), `IN` (16).

A grammar of just `VAR op NUMBER` joined by AND/OR fits 733 of the 1,522 — less
than half. The forms it misses are not exotic, they recur:

    PID1=3, 4, 77, 98, 99          a value LIST
    XTESS084 = 1-4                 a value RANGE
    XTESS069=1-4, 9-12             both at once
    MISSING P_ATTEND               a missingness test
    MISSING (S_PARTY7ID)           the same, parenthesised
    RESPONDENT IS AVAILABLE        prose — not evaluable by anything

So all of the first four are supported, and prose is REFUSED rather than guessed
at. `UnparsedConditionError` names the text it could not read. A resolver that
quietly treated `RESPONDENT IS AVAILABLE` as false would drop a block of arm
text and leave no trace, which is the exact failure mode this project keeps
finding and keeps paying for.

MEASURED COVERAGE, over the same 127 files: **1,662 of 1,853 conditions parse
(89.7%)**, and the 191 refusals fall into 116 forms, every one of which deserves
refusing:

    RESPONDENT IS AVAILABLE                 prose (16)
    R SKIPS PROMPT ONCE                     prose (8)
    (QSTATE = PPSTATEN)                     variable compared to VARIABLE (12)
    Q6 AND Q7 <> 98                         elided — means Q6<>98 AND Q7<>98 (6)
    Q7_SCREEN1 = "YES"                      a label where a code belongs (6)
    P_ AAM05 =1                             a space inside the variable name (6)

The first four cannot be evaluated without inventing something. The last two
could be normalised, and deliberately are not: guessing that `= "YES"` means
code 1 is exactly the kind of assumption that produces a plausible wrong answer.

WHAT THIS DOES NOT DO. `[SHOW IF ...]` has no closing marker, so the extent of
the block it governs is genuinely ambiguous in the source — it runs until
"the next thing", and what counts as the next thing varies by author.
`segment()` therefore returns the segmentation it inferred *for a human to read*
and never silently commits to it. Guessing block extents is how you get arm text
that is subtly wrong and passes every check we have.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

# A respondent's (or arm's) values for the variables a condition mentions.
# None means missing, which is distinct from absent: a variable not in the
# mapping at all is an error, while one present and None is a real "no answer"
# and the thing `MISSING VAR` is asking about.
Values = dict[str, int | None]


class UnparsedConditionError(ValueError):
    """A directive whose condition this module will not guess at.

    Carries the original text so a caller can list every refusal in one pass
    instead of discovering them one build at a time.
    """

    def __init__(self, text: str) -> None:
        super().__init__(f"cannot read condition {text!r} — resolve it by hand")
        self.text = text


class Cond(Protocol):
    def __call__(self, values: Values) -> bool: ...


# --------------------------------------------------------------------------
# conditions
# --------------------------------------------------------------------------

_VALUESET = re.compile(r"^-?\d+(?:\s*-\s*-?\d+)?(?:\s*,\s*-?\d+(?:\s*-\s*-?\d+)?)*$")
_MISSING = re.compile(r"^MISSING\s*\(?\s*([A-Za-z_]\w*)\s*\)?$", re.I)
_ATOM = re.compile(r"^([A-Za-z_]\w*)\s*(<>|!=|>=|<=|=|>|<)\s*(.+)$")
# Split on AND/OR at the top level. No parentheses appear in any measured
# condition, so there is no nesting to respect; if one ever does, it will not
# match the atom grammar and will be refused rather than mis-read.
_SPLIT = re.compile(r"\s+(AND|OR)\s+", re.I)
# Trailing scripting instruction glued onto a condition, e.g.
# `dov_direct=1 show response options 1-5` (62 uses). The condition ends where
# the instruction begins; keeping the instruction would make the value unreadable.
# The separator is sometimes a comma — `NUMBOX> 15, PROMPT`,
# `ATTENTION<>4, TERMINATE AND SET QUAL=2` — and TERMINATE/PROMPT/SET are verbs
# the first version of this list missed.
_TRAILING_INSTRUCTION = re.compile(
    r"[\s,]+(?:SHOW|DISPLAY|INSERT|SKIP|GOTO|GO\s+TO|RECORD|ASK|PROMPT|"
    r"TERMINATE|TERM|SET|MARK|CONTINUE)\b.*$",
    re.I,
)


def _numbers(spec: str) -> set[int]:
    """`1-4, 9-12` or `3, 4, 77` -> the set of values it denotes."""
    out: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        # A range, but mind that the values themselves may be negative: `-1`
        # is a refusal code in several deposits, so the split has to look for a
        # hyphen BETWEEN two numbers, not just any hyphen.
        m = re.fullmatch(r"(-?\d+)\s*-\s*(-?\d+)", part)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            out.update(range(min(lo, hi), max(lo, hi) + 1))
        else:
            out.add(int(part))
    return out


def _atom(text: str) -> Cond:
    text = text.strip().rstrip(".;")
    # NOT is stripped BEFORE the missingness test, so `NOT MISSING P_ATTEND`
    # parses. Testing MISSING first refused it, which would have been a silent
    # loss of exactly the 53 NOT directives this grammar exists to cover.
    negate = False
    if m := re.match(r"^NOT\s+(.+)$", text, re.I):
        negate, text = True, m.group(1).strip()

    if m := _MISSING.match(text):
        var = m.group(1).upper()

        def is_missing(values: Values, var: str = var) -> bool:
            return values.get(var) is None

        return _negated(is_missing) if negate else is_missing

    m = _ATOM.match(text)
    if not m:
        raise UnparsedConditionError(text)
    var, op, rhs = m.group(1).upper(), m.group(2), m.group(3).strip()
    rhs = _TRAILING_INSTRUCTION.sub("", rhs).strip().rstrip(".;:")
    if not _VALUESET.match(rhs):
        raise UnparsedConditionError(text)
    wanted = _numbers(rhs)

    if op in {"=", "<>", "!="} or len(wanted) > 1:
        if op not in {"=", "<>", "!="}:
            # `VAR >= 1,2,3` is not a thing anyone wrote and not a thing that
            # means anything. Refuse rather than pick an interpretation.
            raise UnparsedConditionError(text)
        equal = op == "="

        def member(values: Values, var: str = var, equal: bool = equal) -> bool:
            v = values.get(var)
            # Missing is not equal to anything, and is not unequal either: a
            # question that was never asked has no answer to compare. Treating
            # `VAR<>1` as true for a missing VAR would show a block to
            # respondents who were never in the branch at all.
            if v is None:
                return False
            return (v in wanted) is equal

        return _negated(member) if negate else member

    bound = next(iter(wanted))
    cmp: dict[str, Callable[[int], bool]] = {
        ">": lambda v: v > bound,
        "<": lambda v: v < bound,
        ">=": lambda v: v >= bound,
        "<=": lambda v: v <= bound,
    }
    test = cmp[op]

    def compare(values: Values, var: str = var) -> bool:
        v = values.get(var)
        return False if v is None else test(v)

    return _negated(compare) if negate else compare


def _negated(inner: Cond) -> Cond:
    def flipped(values: Values) -> bool:
        return not inner(values)

    return flipped


# `XTESS104=1 OR 2` and `REL1=1 OR 2 OR 3 OR ... OR 12` — a value list written
# with OR rather than commas. The operands after the first carry no variable, so
# splitting on OR first yields the orphan atom `2` and a refusal. Rewriting the
# run to `XTESS104=1,2` keeps one code path for what is one construct.
_OR_RUN = re.compile(r"(\w+\s*=\s*)(-?\d+(?:\s+OR\s+-?\d+)+)", re.I)
# `PANEL_TYPE=>20`, 2 uses — a transposed `>=`. Unambiguous: `=>` is not an
# operator in any notation these questionnaires use.
_TRANSPOSED = re.compile(r"=\s*>")


def _normalise(text: str) -> str:
    """Spelling variants that denote something the grammar already supports.

    Deliberately narrow. Each rewrite below was counted in the corpus and has
    exactly one possible reading; anything needing a judgement is left to be
    refused instead, because a normalisation that guesses is worse than a
    refusal that is visible.
    """

    def commas(m: re.Match[str]) -> str:
        return m.group(1) + re.sub(r"\s+OR\s+", ",", m.group(2), flags=re.I)

    return _OR_RUN.sub(commas, _TRANSPOSED.sub(">=", text))


def parse_condition(text: str) -> Cond:
    """A directive's condition as a predicate over a respondent's values.

    Raises `UnparsedConditionError` for anything outside the measured grammar,
    including the prose conditions (`RESPONDENT IS AVAILABLE`) that no parser
    can evaluate. That is the point: a refusal is visible and a wrong guess
    is not.
    """
    text = _normalise(text.strip())
    if not text:
        raise UnparsedConditionError(text)
    parts = _SPLIT.split(text)
    conds = [_atom(parts[0])]
    joiners = [parts[i].upper() for i in range(1, len(parts), 2)]
    conds += [_atom(parts[i]) for i in range(2, len(parts), 2)]
    if not joiners:
        return conds[0]
    # All measured conditions use a single connective throughout. A mixture
    # would need precedence rules the source does not state, so refuse it.
    if len(set(joiners)) > 1:
        raise UnparsedConditionError(text)

    if joiners[0] == "AND":

        def all_of(values: Values) -> bool:
            return all(c(values) for c in conds)

        return all_of

    def any_of(values: Values) -> bool:
        return any(c(values) for c in conds)

    return any_of


# --------------------------------------------------------------------------
# inline substitution
# --------------------------------------------------------------------------

# `[INSERT IF P_GENDER=1: he; INSERT IF P_GENDER=2: she]` and
# `[SHOW IF SMARTPHONE = 2: you would be loaned a device]`. Both are
# unambiguous: the bracket delimits the extent, so the text this governs is
# known rather than inferred.
#
# A third spelling uses a comma and a repeated verb in place of the colon:
# `[IF DOV_INS_EXPE_GENDER=1, INSERT him/ IF DOV_INS_EXPE_GENDER=2, INSERT her]`
# (19 uses across five studies), with branches divided by `/` rather than `;`.
# Same construct, different punctuation, so it is matched here rather than
# refused — the alternative was five studies each writing their own parser,
# which is the situation this module exists to end.
_INLINE = re.compile(
    r"\[((?:SHOW\s+IF|INSERT\s+IF|IF)\b[^\[\]]*?"
    r"(?::|,\s*(?:INSERT|DISPLAY|SHOW)\b)[^\[\]]*)\]",
    re.I,
)
# `[IF GENDER1=1 DISPLAY] Gay; [IF GENDER1<>1 DISPLAY] Lesbian or gay`
_IF_DISPLAY = re.compile(
    r"\[\s*IF\s+(?P<cond>[^\[\]]+?)\s+(?:DISPLAY|INSERT|SHOW)\s*\]\s*"
    r"(?P<text>[^\[\];]*)",
    re.I,
)
# One branch of an inline switch. The payload ends at the next branch, which
# may be introduced by `;` or by `/` — `INSERT him/ IF ...=2, INSERT her` — so
# the text runs to a lookahead rather than to a fixed delimiter class. Matching
# `[^;]*` instead swallowed the following branch whole and silently returned
# both payloads as one.
_BRANCH = re.compile(
    r"(?:SHOW\s+IF|INSERT\s+IF|IF)\s+(?P<cond>.+?)\s*"
    r"(?::|,\s*(?:INSERT|DISPLAY|SHOW)\b)\s*"
    r"(?P<text>.*?)"
    r"(?=\s*[;/]\s*(?:SHOW\s+IF|INSERT\s+IF|IF)\b|$)",
    re.I | re.S,
)

# Directives that are scripting or layout, never content: they say how to
# render a question, not what it said. Stripped rather than evaluated. Taken
# from the measured census, commonest first.
_NOISE = re.compile(
    r"\[\s*(?:SP|MP|SPACE|GRID|PROMPT|TEXT\s*BOX|TEXTBOX|MEDIUM\s+TEXTBOX|SINGLE\s+CHOICE|"
    r"HORIZONTAL(?:\s+SP)?|VERTICAL|NUMBER\s*BOX[^\]]*|NUMBOX[^\]]*|SLIDER[^\]]*|"
    r"RECORD[^\]]*|RANDOMIZE[^\]]*|PROGRAM[^\]]*|COMPUTE[^\]]*|CREATE[^\]]*|"
    r"NOTE[^\]]*|SCRIPTER[^\]]*|FORCE\s+RESPONSE[^\]]*|REMOVE\s+PREVIOUS\s+BUTTON|"
    r"CATI[^\]]*|CAWI[^\]]*|RED\s+TEXT[^\]]*|START\s+OF\s+SURVEY|END\s+OF\s+SURVEY|"
    # The en dash in the DISPLAY branch is deliberate: that is how the deposits
    # spell it, and this pattern matches SOURCE text rather than producing it.
    r"ALL|CUSTOM\s+PROMPT[^\]]*|DISPLAY\s*[-–][^\]]*)\s*\]",  # noqa: RUF001
    re.I,
)


def resolve_inline(text: str, values: Values) -> str:
    """Apply every INLINE conditional in `text` for one respondent's values.

    Only the forms whose extent the brackets delimit, so the result is derived
    rather than guessed. Block-level `[SHOW IF X=1]` with no payload inside the
    bracket is left untouched for `segment()` to report.
    """

    def one_inline(m: re.Match[str]) -> str:
        chosen = ""
        for branch in _BRANCH.finditer(m.group(1)):
            if parse_condition(branch.group("cond"))(values):
                chosen = branch.group("text").strip()
                break
        return chosen

    out = _INLINE.sub(one_inline, text)

    def one_if_display(m: re.Match[str]) -> str:
        keep = parse_condition(m.group("cond"))(values)
        return m.group("text").strip() if keep else ""

    return _IF_DISPLAY.sub(one_if_display, out)


def strip_scripting(text: str) -> str:
    """Remove layout and programmer directives, leaving what a respondent read.

    Conditionals are NOT removed here — losing one silently would change the
    arm text, so they have to be resolved, not stripped.
    """
    out = _NOISE.sub(" ", text)
    return re.sub(r"[ \t]{2,}", " ", out).strip()


# --------------------------------------------------------------------------
# block-level [SHOW IF ...], reported rather than trusted
# --------------------------------------------------------------------------


@dataclass
class Block:
    """One stretch of questionnaire text and the condition governing it."""

    condition: str
    text: str
    unparsed: bool = False

    def applies(self, values: Values) -> bool:
        if self.unparsed:
            raise UnparsedConditionError(self.condition)
        if not self.condition:
            return True
        return parse_condition(self.condition)(values)


@dataclass
class Segmentation:
    """What `segment()` inferred, for a human to check before relying on it.

    Deliberately a report and not a resolution. `[SHOW IF X=1]` carries no
    closing marker, so a block's extent runs until "the next thing" and what
    counts as the next thing is the author's habit, not a rule. Every serious
    defect this project has found was invisible per study and obvious once
    someone looked at the artifact; this is the looking.
    """

    blocks: list[Block] = field(default_factory=list)
    refusals: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = []
        for b in self.blocks:
            head = b.condition or "(unconditional)"
            flag = "  ** UNPARSED **" if b.unparsed else ""
            body = " ".join(b.text.split())
            lines.append(f"  [{head}]{flag}\n      {body[:300]}")
        if self.refusals:
            lines.append("\n  conditions this module refuses to guess at:")
            lines += [f"      {r}" for r in self.refusals]
        return "\n".join(lines)


_BLOCK_SHOW_IF = re.compile(r"\[\s*(?:SHOW\s+IF|IF)\s+([^\[\]:]+?)\s*\]", re.I)
# `[IF GENDER1=1 DISPLAY] Gay` is an INLINE switch that happens to match the
# block pattern too. It is `resolve_inline`'s business, and segmenting on it
# would cut the surrounding sentence into spurious blocks.
_INLINE_VERB = re.compile(r"\b(?:DISPLAY|INSERT|SHOW)\s*$", re.I)


def segment(text: str) -> Segmentation:
    """Split text into blocks at each `[SHOW IF ...]`, and say so plainly.

    A block runs from its directive to the next directive or the end of the
    text. That is an assumption, which is why this returns a report: read it
    against the questionnaire before building arm text from it.
    """
    seg = Segmentation()
    marks = [m for m in _BLOCK_SHOW_IF.finditer(text) if not _INLINE_VERB.search(m.group(1))]
    if not marks:
        seg.blocks.append(Block(condition="", text=text))
        return seg
    if marks[0].start() > 0:
        preamble = text[: marks[0].start()].strip()
        if preamble:
            seg.blocks.append(Block(condition="", text=preamble))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        cond = " ".join(m.group(1).split())
        bad = False
        try:
            parse_condition(cond)
        except UnparsedConditionError:
            bad = True
            seg.refusals.append(cond)
        seg.blocks.append(Block(condition=cond, text=text[m.end() : end].strip(), unparsed=bad))
    return seg
