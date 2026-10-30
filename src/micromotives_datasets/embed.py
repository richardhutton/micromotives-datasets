"""The only place that talks to Voyage.

`jev.py` exists because eight scripts each grew their own prompt and a lesson
learned in one never reached the others — and when the repo was finally grepped,
FIVE were still doing it, including the script whose entire job was to report what
production sends (ledger 100). Embeddings are the same class of thing: an
external service, reached over the wire, with a licence constraint attached. So
this is the one door, and `tests/test_architecture.py` fails the build if
anything else imports the client.

Two structural rules, both inherited from `jev.py`:

1. **Every function here takes strings. None takes a dataframe.** A respondent
   row cannot reach this module by accident, because there is no parameter it
   would fit through.
2. **Nothing crosses the wire until its licence has been read.** `cleared_text`
   is the gate, and an uncleared source raises rather than warns. A warning is
   something you read once; a raise is something that stops you.

Vectors are cached on disk keyed by (model, input_type, text), so the same text
is never paid for twice within a machine. The cache is GITIGNORED: it is about
24KB per text and grows without bound, and a vector is an expensive-to-recompute
INTERMEDIATE rather than a result. What gets tracked is the thing derived from it
— `data/catalog/coverage_map.json`, the 2D coordinates, which is what has to be
stable and diffable.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

MODEL = "voyage-3-large"
"""Voyage's strongest general-purpose text model at the time of writing.

Changing this invalidates nothing — the cache is keyed BY model, so an old
vector is never silently served for a new model. Re-embedding the corpus is a
few seconds and a few cents.
"""

InputType = Literal["document", "query"]

ROOT = Path(__file__).resolve().parent.parent.parent
CACHE = ROOT / "data" / "catalog" / "embeddings"

KEY_ENV = "VOYAGE_API_KEY"

CLEARED: dict[str, str] = {
    "CC0 1.0": "Public domain dedication. No restriction on any use.",
    "public-metadata": (
        "A study TITLE as published on a public listing page (tessexperiments.org, "
        "an OSF project page, a Dataverse record). Public-facing metadata about a "
        "study, not material FROM it."
    ),
    "ukds-public-documentation": (
        "A study title or description as UKDS THEMSELVES publish it, at "
        "doc.ukdataservice.ac.uk, downloadable without authentication. Public "
        "documentation about a collection, not microdata from it. Verified by "
        "fetching, not assumed — see the note below. Decided by rich, 9 Oct 2026."
    ),
    "synthetic-quote": (
        "A synthetic quote our writer model produced (docs/QUOTES_SPEC.md), sent alone "
        "for the variety measures: the sentence only, with no persona, condition, "
        "outcome, response or identifier. Decided by rich, 30 Oct 2026."
    ),
}
"""Licences whose text may cross the wire. Anything absent is refused.

Deliberately NOT in this list, and each for its own reason:

- **`TESS deposit, none stated`** — every TESS recipe records "no explicit grant
  of redistribution rights for this deposit, and none should be assumed", and
  **Voyage RETAINS API inputs and trains on them by default** (their FAQ, read
  2026-10-02: zero-day retention exists but must be opted into by an org admin
  with a payment method, and the opt-out is one-way). So sending this text under
  default terms would put material we have no redistribution rights to into a
  third party's training corpus. Not a close call while that is true.

  TESS study TITLES remain fine under `public-metadata` — they are published on
  tessexperiments.org. It is the condition and outcome TEXT that waits.

  To open this: opt the account out of retention FIRST, then add the key here
  with the date and who decided. Do not reason from "we already send instrument
  text to Jev" — see below, that premise is itself unverified.
- **Note on the wider gap, recorded here because this is where someone will look.**
  `recipe_prep.py` sends TESS value labels, variable labels and questionnaire
  directives to Jev (TypeSafe) on every run, which CLAUDE.md permits. TypeSafe's
  docs state nothing about retention, logging or training on customer input
  (checked 2026-10-02). CLAUDE.md's rule is precise about WHAT crosses the wire —
  instrument text only, never respondent rows, enforced structurally because
  every `jev.py` function takes strings rather than a dataframe — and silent
  about what the far end does with it. No respondent data has gone anywhere; the
  exposure is instrument text from deposits with no redistribution grant.

  **CLOSED by rich, 9 Oct 2026:** not a concern, because TESS material is freely
  distributed already — the deposits sit on tessexperiments.org and on OSF, and
  anyone can download them. "No licence stated" governs what WE may publish; it
  does not turn question wordings that are already public into something
  TypeSafe could leak. No enquiry is being sent. Recorded here so this is not
  reopened as an outstanding question.

- **UKDS safeguarded** — End User Licence. Never, under any circumstance, until
  the EUL has been read, instrument text included. `data/catalog/
  uk_dataverse_candidates.csv` carries three such rows WITH titles and authors,
  so a script that reads that file and forgets this gate would leak them.

  **This is still true of the MICRODATA and is not loosened by the entry above.**
  The respondents' answers, and the variable and value labels inside the `.dta`
  files, remain refused. What changed is narrower: UKDS publish the Innovation
  Panel's own documentation openly, so that documentation is not the thing the
  gate was built to hold.

- **Why `ukds-public-documentation` was added, 9 Oct 2026.** The question came up
  while trying to place the 44 Innovation Panel experiments on the coverage map.
  The gate refused them, correctly on the assumption that had been running all
  along — that the User Guide is Documentation, the EUL's "Data Collection"
  includes Documentation, so it cannot cross the wire. Checking rather than
  assuming found that UKDS serve it themselves, with no authentication:

      doc.ukdataservice.ac.uk/doc/6849/mrdoc/pdf/
        6849_innovation_panel_user_guide.pdf      200, 3,525,566 bytes
        6849_ip_wave_5_questionnaires.pdf         200, 7,229,251 bytes
        6849_ip_wave_16_questionnaire.pdf         200, 5,738,690 bytes

  Fetched 9 Oct 2026 with no credentials. So an experiment title taken from that
  guide is in the same position as a TESS title on tessexperiments.org: already
  published by the rights holder, on a public URL, by their own choice.

  Two things this does NOT license, stated because the next person will be
  tempted. It does not open the microdata, which is the point of the EUL. And it
  does not generalise to other UKDS collections without the same check — the
  test is a 200 with no credentials against `doc.ukdataservice.ac.uk`, run for
  that study, not an inference from this one.
"""


class LicenceRefusedError(RuntimeError):
    """Raised when text would cross the wire without its licence being cleared."""


@dataclass(frozen=True)
class Text:
    """One thing to embed, carrying the licence that lets it travel.

    The licence is not optional and has no default. Every caller has to say,
    per item, what permits this text to leave the machine — which means the
    question gets asked at the point where the answer is known, rather than
    inferred later by whoever reads the script.
    """

    key: str
    text: str
    licence: str


def cleared_text(items: list[Text]) -> list[Text]:
    """Return `items`, or raise naming every one that may not travel.

    Raises on the WHOLE batch rather than silently dropping the offenders: a
    caller that quietly embedded 24 of 25 studies would produce a map with a
    hole in it and no indication the hole was put there on purpose.
    """
    refused = sorted({i.licence for i in items if i.licence not in CLEARED})
    if refused:
        raise LicenceRefusedError(
            f"{len(refused)} licence(s) not cleared for the wire: {refused}. "
            f"Cleared: {sorted(CLEARED)}. Nothing was sent. "
            f"See CLEARED in {__name__} for why each is held, and do not widen it "
            f"without recording who decided and on what basis."
        )
    return items


def _digest(text: str, model: str, input_type: InputType) -> str:
    payload = f"{model}\x00{input_type}\x00{text}".encode()
    return hashlib.sha256(payload).hexdigest()


def _cache_path(digest: str) -> Path:
    return CACHE / digest[:2] / f"{digest}.json"


def _cached(digest: str) -> list[float] | None:
    path = _cache_path(digest)
    if not path.exists():
        return None
    vector: list[float] = json.loads(path.read_text())["vector"]
    return vector


def _store(digest: str, vector: list[float], model: str) -> None:
    path = _cache_path(digest)
    path.parent.mkdir(parents=True, exist_ok=True)
    # The TEXT is deliberately not stored. The source text is already in the
    # recipe or the catalogue, so a copy here would duplicate licensed material
    # into a second file for no gain — and the digest is enough to find a hit.
    path.write_text(json.dumps({"model": model, "vector": vector}) + "\n")


def client() -> Any:
    """The Voyage client, or a message saying exactly how to fix its absence."""
    key = os.environ.get(KEY_ENV)
    if not key:
        raise RuntimeError(
            f"{KEY_ENV} is not set. It belongs in the environment, never in code "
            f"or a config file. If it is in ~/.bash_profile, note that the shell "
            f"used here does not source that file automatically — prefix the "
            f"command with `source ~/.bash_profile &&`."
        )
    import voyageai

    return voyageai.Client(api_key=key)  # type: ignore[attr-defined]


def embed(
    items: list[Text],
    *,
    model: str = MODEL,
    input_type: InputType = "document",
    batch: int = 64,
) -> dict[str, list[float]]:
    """Embed `items`, returning `{key: vector}`. Cached items cost nothing.

    `input_type` is "document" for everything in a corpus map. Mixing "document"
    and "query" in one space distorts the distances, because Voyage prepends a
    different instruction to each — so the choice is a property of the MAP, not
    of the individual item, and lives here rather than at the call site.
    """
    cleared_text(items)

    out: dict[str, list[float]] = {}
    todo: list[Text] = []
    for item in items:
        hit = _cached(_digest(item.text, model, input_type))
        if hit is None:
            todo.append(item)
        else:
            out[item.key] = hit

    for start in range(0, len(todo), batch):
        chunk = todo[start : start + batch]
        result = client().embed([i.text for i in chunk], model=model, input_type=input_type)
        for item, vector in zip(chunk, result.embeddings, strict=True):
            out[item.key] = list(vector)
            _store(_digest(item.text, model, input_type), list(vector), model)

    return out
