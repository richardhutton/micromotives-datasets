"""Synthetic quotes on training rows: keys, draws, prompts, verdicts, joining, variety.

Design: docs/QUOTES_SPEC.md. Everything here is pure (no model calls, no network) so it
can be unit-tested on the Mac; `scripts/quotes_run.py` does the calling on the pod.

A quote is written from a row's persona, condition, outcome and real response, so it is
for TRAINING rows only: on an eval row it would leak the answer. Quotes live in their own
table keyed by `ROW_KEY`, with a hash of what each was written from; the export joins the
table onto whatever rows it selects, and a quote whose hash no longer matches its row
(the row changed upstream) is not joined.

Every quote is synthetic (CLAUDE.md, Data handling): the export sets `synthetic_quote`.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import math
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROMPTS = ROOT / "prompts" / "quotes"

# Unique on every v3 training row (QUOTES_SPEC section 4, measured).
ROW_KEY = ["study", "recipe", "participant_id", "condition_num", "task_num"]
# What a quote is written from. A change in any of these makes the quote stale.
HASHED = ["persona", "condition", "outcome", "response"]

TABLE_COLUMNS = [
    *ROW_KEY,
    "input_hash",
    "quote",
    "passed",
    "rounds",
    "angle",
    "voice",
    "setting",
    "failed_checks",
    "notes",  # the checker's notes, which a rewrite (and a resumed run) needs
    "blind_prediction",
    "blind_agrees",
    "run",
]

# Reason angles, drawn per quote. The two families are the same length and a draw picks
# the family first, so the unreasoned reasons people actually give are drawn exactly as
# often as the reasoned ones (QUOTES_SPEC section 1, "human, not average").
REASONED_ANGLES = [
    "cost or money",
    "fairness",
    "family or the people close to them",
    "something that happened to them or someone they know",
    "their values or principles",
    "practical consequences",
    "safety or risk",
]
UNREASONED_ANGLES = [
    "gut feeling, no real reason",
    "their mood at the time",
    "habit, it's what they always do",
    "a story they half remember",
    "a belief they hold confidently that may well be wrong",
    "distrust of whoever is behind it",
    "contrariness or not liking being told",
]
ANGLES = REASONED_ANGLES + UNREASONED_ANGLES

# Voice, drawn once per respondent (one value per dimension), so one person sounds like
# one person across a study's outcomes.
VOICE_DIMENSIONS = [
    # length and manner as one dimension, so no voice is "says very little" and "rambling"
    [
        "says very little (ten words at most), blunt",
        "says very little (ten words at most), gentle",
        "chatty",
        "rambling",
    ],
    ["sure of themselves", "unsure, hedging"],
    ["plain-spoken", "articulate"],
]

CHECKS = [
    "fits_response",
    "tone_fits",
    "within_persona",
    "aligned_with_persona",
    "about_condition",
    "no_giveaways",
]


def _digest(*parts: object) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()


def input_hash(row: pd.Series | dict[str, Any]) -> str:
    """Hash of what a quote is written from: persona, condition, outcome, response."""
    return _digest(*(str(row[c]) for c in HASHED))


def row_key(row: pd.Series | dict[str, Any]) -> tuple[Any, ...]:
    return tuple(row[c] for c in ROW_KEY)


def _pick(seed: int, *key: object) -> int:
    """A stable non-negative integer from a seed and a key, independent of row order."""
    return int(_digest(seed, *key)[:15], 16)


def draw_angle(seed: int, key: Sequence[object]) -> str:
    """The reason angle for one row: family first (half and half), then an angle in it."""
    n = _pick(seed, "angle", *key)
    family = REASONED_ANGLES if n % 2 == 0 else UNREASONED_ANGLES
    return family[(n // 2) % len(family)]


def draw_voice(seed: int, study: str, participant_id: str) -> str:
    """The voice for one respondent in one study: one value from each dimension."""
    n = _pick(seed, "voice", study, participant_id)
    picks = []
    for options in VOICE_DIMENSIONS:
        picks.append(options[n % len(options)])
        n //= len(options)
    return ", ".join(picks)


def persona_lines(persona_json: str) -> str:
    """Every recorded persona field, one per line; absent fields stay absent."""
    persona = json.loads(persona_json)
    lines = []
    for field, value in persona.items():
        if value is None or value == "" or (isinstance(value, float) and math.isnan(value)):
            continue
        lines.append(f"{field.replace('_', ' ')}: {value}")
    return "\n".join(lines)


def is_text_row(row: pd.Series | dict[str, Any]) -> bool:
    """Image rows get no quote at the start (QUOTES_SPEC section 2)."""
    images = row.get("condition_images") if hasattr(row, "get") else None
    return images is None or len(images) == 0


def load_prompt(name: str) -> tuple[str, str]:
    """A prompt file's text and its sha256, for the run's provenance."""
    text = (PROMPTS / name).read_text()
    return text, hashlib.sha256(text.encode()).hexdigest()


# --- writing ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Item:
    """One row to write a quote for, with what was drawn for it."""

    key: tuple[Any, ...]
    participant_id: str
    persona: str  # rendered persona lines, or persona_text for the persona-light setting
    condition: str
    outcome: str
    response: str
    scale_min: int
    scale_max: int
    angle: str | None
    voice: str | None
    examples: tuple[str, ...] = ()  # real people's answers to OTHER questions, for voice (v6)


def item_block(item: Item, number: int, with_persona: bool, show_answer: bool = True) -> str:
    parts = [f"[{number}]"]
    if with_persona:
        parts.append(f"About this person:\n{item.persona}")
        if item.voice:
            parts.append(f"How they talk: {item.voice}")
    parts += [
        f"What the study put to them:\n{item.condition}",
        f"The question:\n{item.outcome}",
    ]
    if show_answer:
        parts.append(f"Their answer: {item.response} (scale {item.scale_min} to {item.scale_max})")
        if strength := answer_strength(item):
            parts.append(f"How strongly: {strength}")
    if item.angle and show_answer:
        parts.append(f"Lean on this kind of reason: {item.angle}")
    return "\n\n".join(parts)


def answer_strength(item: Item) -> str | None:
    """How far along its scale an answer sits, in words the writer can act on (v4).
    None when the answer is not a number on an ordered scale of more than two points."""
    try:
        value = float(item.response)
    except ValueError:
        return None
    width = item.scale_max - item.scale_min
    if width < 2:
        return None
    pos = (value - item.scale_min) / width
    if pos <= 0.1 or pos >= 0.9:
        return "at the far end of the scale: they feel strongly"
    if 0.4 <= pos <= 0.6:
        return "near the middle: lukewarm or torn"
    return "leaning one way, firmly but not fiercely"


def examples_block(examples: Sequence[str]) -> str:
    lines = "\n".join(f'- "{e}"' for e in examples)
    return (
        "STYLE EXAMPLES (for voice only). Below are real answers that other people, British "
        "voters, gave to different survey questions. They are NOT about this study and NOT "
        "about this person. Use them only to hear how real people talk: how short, blunt and "
        "plain they are, and how little they explain. Do not use their topics, words or "
        "opinions. Keep the English this person would use (American for someone in the US).\n"
        f"{lines}\n"
        "END OF STYLE EXAMPLES."
    )


def writer_messages(system: str, items: Sequence[Item]) -> list[dict[str, str]]:
    """One call: either one respondent's rows (persona once) or k respondents' (each own)."""
    one_person = len({i.participant_id for i in items}) == 1
    blocks = []
    if items and items[0].examples:
        blocks.append(examples_block(items[0].examples))
    if one_person:
        first = items[0]
        head = f"About this person:\n{first.persona}"
        if first.voice:
            head += f"\n\nHow they talk: {first.voice}"
        blocks.append(head)
        blocks.append(f"They answered {len(items)} question(s) in this study.")
    else:
        blocks.append(
            f"These are {len(items)} different people who answered the same question. "
            "Each has their own details; their quotes must sound like different people."
        )
    blocks += [item_block(it, n, not one_person) for n, it in enumerate(items, 1)]
    blocks.append(
        f'Reply with JSON only: {{"quotes": [...]}}, exactly {len(items)} strings, '
        "in the order above."
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": "\n\n".join(blocks)}]


def writer_schema(n: int) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "quotes": {"type": "array", "items": {"type": "string"}, "minItems": n, "maxItems": n}
        },
        "required": ["quotes"],
    }


def parse_quotes(text: str, n: int) -> list[str] | None:
    """The n quotes from a writer reply, or None when the reply is not usable."""
    try:
        quotes = json.loads(text)["quotes"]
    except (ValueError, KeyError, TypeError):
        return None
    if not isinstance(quotes, list) or len(quotes) != n:
        return None
    if not all(isinstance(q, str) and q.strip() for q in quotes):
        return None
    return [q.strip() for q in quotes]


def repair_messages(system: str, item: Item, quote: str, notes: str) -> list[dict[str, str]]:
    user = "\n\n".join(
        [
            *([examples_block(item.examples)] if item.examples else []),
            item_block(item, 1, True),
            f"A first attempt at their quote:\n{quote}",
            f"What a reviewer said was wrong with it:\n{notes}",
            "Write a new quote that fixes only what the reviewer named. Do not make the "
            "reason more sensible, balanced or polite than this person would be. "
            'Reply with JSON only: {"quotes": ["..."]}',
        ]
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


# --- the voice pool (v6) -----------------------------------------------------------------

POOL = ROOT / "data" / "processed" / "quotes" / "voice_pool.parquet"
DEGREE = re.compile(r"bachelor|degree|graduate|postgrad|master|doctor|phd|university", re.I)
NO_DEGREE = re.compile(
    r"no degree|below degree|less than (a )?degree|without a degree|non-degree|no formal", re.I
)


def persona_bands(persona_json: str) -> tuple[str | None, str | None]:
    """(age band, education band) from a persona, in the pool's bands; None when unknown."""
    p = json.loads(persona_json)
    age = p.get("age")
    band = None
    if (
        isinstance(age, int | float)
        and not (isinstance(age, float) and math.isnan(age))
        and age >= 16
    ):
        band = "18-34" if age < 35 else "35-54" if age < 55 else "55+"
    edu = p.get("education")
    edu_band = None
    if isinstance(edu, str) and edu.strip():
        edu_band = "no degree" if NO_DEGREE.search(edu) or not DEGREE.search(edu) else "degree"
    return band, edu_band


class VoicePool:
    """Real answers to pick voice examples from: K_MATCHED from people of the same age and
    education band (style, never opinion: no party, no region), K_RANDOM from anyone, so
    the voice shifts without turning into a caricature of a group. Draws are seeded by
    the row, so a resumed run shows the writer the same examples."""

    K_MATCHED = 3
    K_RANDOM = 2

    def __init__(self, pool: pd.DataFrame) -> None:
        self.pool = pool.reset_index(drop=True)
        # sqrt of how many people gave an answer: short common answers come up often, not always
        self.weight = np.sqrt(self.pool["n"].to_numpy(dtype=float))
        self.groups = {
            k: g.index.to_numpy()
            for k, g in self.pool.groupby(["age_band", "edu_band"], dropna=True)
        }

    @classmethod
    def load(cls, path: Path = POOL) -> VoicePool | None:
        return cls(pd.read_parquet(path)) if path.exists() else None

    def _draw(self, rng: np.random.Generator, idx: np.ndarray, k: int) -> list[str]:
        if len(idx) == 0 or k == 0:
            return []
        w = self.weight[idx] / self.weight[idx].sum()
        chosen = rng.choice(idx, size=min(k, len(idx)), replace=False, p=w)
        return [str(self.pool.at[i, "text"]) for i in chosen]

    def pick(
        self, seed: int, key: Sequence[object], bands: tuple[str | None, str | None]
    ) -> tuple[str, ...]:
        rng = np.random.default_rng(_pick(seed, "voice-examples", *key))
        matched = (
            self.groups.get(bands, np.array([], dtype=int))
            if None not in bands
            else np.array([], dtype=int)
        )
        k_matched = self.K_MATCHED if len(matched) else 0
        picked = self._draw(rng, matched, k_matched)
        rest = np.setdiff1d(np.arange(len(self.pool)), np.array([], dtype=int))
        while len(picked) < self.K_MATCHED + self.K_RANDOM:
            extra = self._draw(rng, rest, self.K_MATCHED + self.K_RANDOM - len(picked))
            picked += [e for e in extra if e not in picked]
        return tuple(picked)


def _words(text: str) -> list[str]:
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).split()


def copied_example(quote: str, examples: Sequence[str]) -> bool:
    """A quote that reuses a real person's answer: an example of 4+ words found nearly
    word for word inside it. Real words must never pass as a synthetic quote."""
    words = _words(quote)
    for example in examples:
        ex = _words(example)
        if len(ex) < 4:
            continue
        for start in range(0, max(1, len(words) - len(ex) + 1)):
            window = words[start : start + len(ex)]
            if difflib.SequenceMatcher(None, window, ex).ratio() >= 0.75:
                return True
    return False


# --- AI tells (v7, from the humanizer skill) -------------------------------------------

AI_TELLS = {
    "dash": re.compile(r"[\u2014\u2013]| -- "),
    "semicolon": re.compile(r";"),
    "ellipsis": re.compile(r"\u2026|\.\.\."),
    "not_x_but_y": re.compile(
        r"\bnot (just|only|merely|because)\b[^.?!]{0,60}\bbut\b|\bit'?s not\b[^.?!]{1,40}, it'?s\b",
        re.I,
    ),
    "staged_opener": re.compile(
        r"^\s*(look,|honestly\?|here'?s the thing|the thing is|let'?s be honest|real talk)", re.I
    ),
    "survey_talk": re.compile(
        r"\b(survey|questionnaire|asking me|being asked|the passage|this study|who'?s counting)\b",
        re.I,
    ),
    "buzzword": re.compile(r"\b(gaslight\w*|red flag|toxic|delve|tapestry|testament)\b", re.I),
}


def ai_tells(quote: str) -> list[str]:
    """Humanizer tells that need no judgement to spot; any one fails the quote (v7)."""
    return [name for name, pattern in AI_TELLS.items() if pattern.search(quote)]


# --- checking --------------------------------------------------------------------------


def checker_messages(system: str, item: Item, quote: str) -> list[dict[str, str]]:
    user = "\n\n".join([item_block(item, 1, True), f"The quote:\n{quote}"])
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def checker_schema() -> dict[str, Any]:
    # answer_means comes FIRST, so the checker states the answer's direction and strength
    # before it judges fits_response (v5: direction errors were getting through)
    props: dict[str, Any] = {"answer_means": {"type": "string"}}
    props |= {c: {"type": "boolean"} for c in CHECKS}
    props["notes"] = {"type": "string"}
    return {"type": "object", "properties": props, "required": ["answer_means", *CHECKS, "notes"]}


def parse_verdict(text: str) -> dict[str, Any] | None:
    """A checker verdict with every check a real boolean, or None."""
    try:
        verdict = json.loads(text)
    except ValueError:
        return None
    if not isinstance(verdict, dict) or not all(isinstance(verdict.get(c), bool) for c in CHECKS):
        return None
    verdict.setdefault("notes", "")
    return verdict


def failed_checks(verdict: dict[str, Any]) -> list[str]:
    return [c for c in CHECKS if not verdict[c]]


def blind_messages(system: str, item: Item, quote: str) -> list[dict[str, str]]:
    """Persona, condition, outcome and quote; never the response."""
    user = "\n\n".join(
        [
            item_block(item, 1, True, show_answer=False),
            f"What they said about it:\n{quote}",
            f'Predict their answer. Reply with JSON only: {{"answer": <number from '
            f"{item.scale_min} to {item.scale_max}>}}",
        ]
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def parse_blind(text: str) -> float | None:
    try:
        answer = json.loads(text)["answer"]
    except (ValueError, KeyError, TypeError):
        return None
    if isinstance(answer, bool) or not isinstance(answer, int | float):
        return None
    return float(answer)


def direction_agrees(
    predicted: float, actual: float, lo: float, hi: float, nominal: bool, tolerance: float = 0.2
) -> bool:
    """Does the blind prediction point the same way as the real answer?

    Nominal scales have no direction, so they need the same category. Otherwise a
    prediction agrees when it is on the same side of the midpoint, or within `tolerance`
    of the scale's width of the answer (which covers answers at or near the midpoint).
    Scored on direction, not exact value, so idiosyncratic reasons are not filtered out
    (QUOTES_SPEC section 7).
    """
    predicted = min(max(predicted, lo), hi)  # a prediction off the scale counts as its end
    if nominal:
        return round(predicted) == round(actual)
    if hi <= lo:
        raise ValueError(f"empty scale {lo}..{hi}")
    if abs(predicted - actual) <= tolerance * (hi - lo):
        return True
    mid = (lo + hi) / 2
    return (predicted - mid) * (actual - mid) > 0


# --- the quote table -------------------------------------------------------------------


def merge_tables(tables: Iterable[pd.DataFrame]) -> pd.DataFrame:
    """One table from several runs, oldest first: per key and input hash, a passed quote
    beats a failed one, and a later run beats an earlier one. Nothing is written twice."""
    frames = [t for t in tables if len(t)]
    if not frames:
        return pd.DataFrame(columns=TABLE_COLUMNS)
    both = pd.concat(frames, ignore_index=True)
    both["_order"] = range(len(both))
    both = both.sort_values(["passed", "_order"], kind="stable")
    return (
        both.drop_duplicates([*ROW_KEY, "input_hash"], keep="last")
        .sort_values("_order")
        .drop(columns="_order")
        .reset_index(drop=True)
    )


@dataclass
class JoinCounts:
    rows: int
    with_quote: int
    stale: int  # a passed quote exists for the key but was written from different inputs
    without_quote: int


def join_quotes(rows: pd.DataFrame, table: pd.DataFrame) -> tuple[pd.DataFrame, JoinCounts]:
    """`rows` with `quote` and `synthetic_quote` filled from passed, current quotes.

    A row that already holds a real quote from its source keeps it; a synthetic one is
    never put over it."""
    out = rows.copy()
    hashes = out.apply(input_hash, axis=1) if len(out) else pd.Series(dtype=str)
    out["_hash"] = hashes
    good = table[table["passed"].astype(bool)][[*ROW_KEY, "input_hash", "quote"]]
    good = good.rename(columns={"input_hash": "_hash", "quote": "_quote"})
    merged = out.merge(good, on=[*ROW_KEY, "_hash"], how="left", validate="many_to_one")
    real = merged["quote"].notna() if "quote" in merged else pd.Series(False, index=merged.index)
    have = merged["_quote"].notna() & ~real
    # object dtype, so a row with no quote holds None (as the schema has it), not NaN
    merged["quote"] = pd.Series(
        [
            s if h else (r if is_real else None)
            for s, h, r, is_real in zip(
                merged["_quote"], have, merged.get("quote", [None] * len(merged)), real, strict=True
            )
        ],
        index=merged.index,
        dtype=object,
    )
    merged["synthetic_quote"] = have
    # stale: a PASSED quote exists for the key, written from inputs the row no longer has
    keys_passed = good[ROW_KEY].drop_duplicates()
    known = merged[ROW_KEY].merge(keys_passed, how="left", indicator=True)["_merge"] == "both"
    stale = int((known.to_numpy() & ~have.to_numpy() & ~real.to_numpy()).sum())
    merged = merged.drop(columns=["_hash", "_quote"])
    merged.index = rows.index
    counts = JoinCounts(len(rows), int(have.sum()), stale, int((~have).sum()))
    return merged, counts


# --- drafts and preference pairs -------------------------------------------------------

DRAFT_COLUMNS = [
    *ROW_KEY,
    "input_hash",
    "round",
    "quote",
    "passed",
    "failed_checks",
    "notes",
    "prompt_version",
    "run",
]


def preference_pairs(drafts: pd.DataFrame) -> pd.DataFrame:
    """(rejected, chosen) pairs for preference training: for each row whose quote passed
    after a rewrite, every earlier failed draft of that row against the passing one.
    Same row and same inputs on both sides, so the only difference is the quote."""
    if drafts.empty:
        return pd.DataFrame(columns=[*ROW_KEY, "input_hash", "rejected", "chosen", "failed_checks"])
    keys = [*ROW_KEY, "input_hash"]
    chosen = drafts[drafts["passed"].astype(bool)].sort_values("round").drop_duplicates(keys)
    chosen = chosen[[*keys, "quote", "round"]].rename(columns={"quote": "chosen", "round": "_r"})
    failed = drafts[~drafts["passed"].astype(bool)][[*keys, "quote", "round", "failed_checks"]]
    pairs = failed.merge(chosen, on=keys)
    pairs = pairs[pairs["round"] < pairs["_r"]]
    return pairs.rename(columns={"quote": "rejected"})[
        [*keys, "rejected", "chosen", "failed_checks"]
    ].reset_index(drop=True)


# --- variety (QUOTES_SPEC section 8) ----------------------------------------------------


def _unit(emb: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    return emb / np.where(norms == 0, 1, norms)


def spread(emb: np.ndarray) -> float:
    """Mean pairwise cosine distance; 0 for fewer than two quotes."""
    n = len(emb)
    if n < 2:
        return 0.0
    sim = _unit(emb) @ _unit(emb).T
    return float((1 - sim[np.triu_indices(n, 1)]).mean())


def near_duplicate_share(emb: np.ndarray, threshold: float = 0.9) -> float:
    n = len(emb)
    if n < 2:
        return 0.0
    sim = _unit(emb) @ _unit(emb).T
    return float((sim[np.triu_indices(n, 1)] > threshold).mean())


def vendi(emb: np.ndarray) -> float:
    """Effective number of distinct quotes: exp of the entropy of the similarity
    kernel's eigenvalues (Friedman and Dieng). 1 when all are the same, n when all differ."""
    n = len(emb)
    if n == 0:
        return 0.0
    unit = _unit(emb)
    eig = np.linalg.eigvalsh((unit @ unit.T) / n)
    eig = eig[eig > 1e-12]
    return float(np.exp(-(eig * np.log(eig)).sum()))


def separation(emb: np.ndarray, responses: Sequence[object]) -> float:
    """Mean cosine distance between quotes for DIFFERENT responses minus that between
    quotes for the SAME response; positive when answers are told apart by their quotes."""
    unit = _unit(emb)
    sim = unit @ unit.T
    labels = np.asarray(responses)
    same = labels[:, None] == labels[None, :]
    upper = np.triu(np.ones_like(same, dtype=bool), 1)
    within, between = same & upper, ~same & upper
    if not within.any() or not between.any():
        return float("nan")
    return float((1 - sim[between]).mean() - (1 - sim[within]).mean())
