# Spec: synthetic quotes on training rows

Reviewed and built 30 Oct 2026 (code: `src/micromotives_datasets/quotes.py`, `scripts/quotes_*.py`, prompts in `prompts/quotes/`, router `scripts/quotes_router.py`, pod runbook `docs/RUNPOD_QUOTES.md`); the pilot has not run yet. Written 30 Oct 2026
from a design discussion between rich and the micromotives-training agent. Nothing here
is built yet. Facts marked *measured* were counted on export `v3/studies_10pct@v3-10pct`;
model facts were checked on the Hugging Face model pages on 30 Oct 2026.

## 1. Purpose

Each training row gets a short quote: what this respondent might say, in their own
words, about why they gave the response they gave. The trained model answers in ONE
assistant turn, response first and quote second (rich, 30 Oct 2026):

    Answer: 4
    Quote: Honestly, that advert frightened me. My dad went the same way.

so a run reports both a quantitative result (response distributions) and a qualitative
one (why people in each part of the distribution answered as they did, and where groups
diverge). One turn rather than two: no invented "why?" question a respondent was never
asked, simpler masking, and one request per prediction instead of two, which matters at
scale. A row without a quote ends after its `Answer:` line. For numeric evaluation,
generation stops at the end of that line, so quotes cost nothing when unread.

This is not Socrates' "reasoning before the answer", which aimed to improve the
prediction (they found it helped on seen studies and did little on unseen ones). Here
the answer comes first and the quote explains it, so the quote cannot change the
number.

Every quote is synthetic and flagged as such. It is a plausible explanation of a real
response, not what the respondent thought.

**Human, not average** (rich, 30 Oct 2026). The models simulate people, and people are
often not reasonable. A quote should sound like this one person, with the reasons real
people actually give: gut feeling, mood, habit, a story they half remember, a wrong
belief held with confidence, distrust, contrariness, self-interest, a reason that does
not quite follow, or "I don't really know, it just seemed right". A tidy, balanced,
sensible explanation that anyone might give is a failure, not a safe default. Nothing in
writing, checking or variety measurement may reward the average answer or the rational
one; each section below is written to that rule.

## 2. Scope

- **Training rows only.** Never eval rows: a quote is written from the real response,
  so on an eval row it would leak the answer.
- **Text studies only.** Image experiments are not supported at the start: rows whose
  condition showed a picture get no quote.
- **Order of work:** the pilot (section 10) on a small set of rows first; then quotes for
  every training row of the 10% export (`v3/studies_10pct`), released as a new export
  version (section 4).
- All sources, Innovation Panel included, processed on RunPod Secure Cloud. Innovation
  Panel personas, responses and quotes are never printed in an agent session; review
  uses TESS and Dataverse rows.

## 3. Ownership

A quote is part of the row, so this repo owns all of it: prompts, generation, checking,
diversity measures, writing `quote` and `synthetic_quote`, and the export. The models
run on a RunPod pod behind one router; the scripts that call them run in this repo, and
the quotes land in the dataset here (section 9, `docs/RUNPOD_QUOTES.md`).

micromotives-training only consumes exports that carry quotes: the one-turn format in
section 1 (its parser reads the `Answer:` line instead of a bare number), a config switch
to train with or without quotes, a masking check that the loss covers the whole
assistant turn, and evaluation of the quotes its model writes.

## 4. Where quotes go

The schema already has both fields (`schema.py`): `quote` (text) and `synthetic_quote`
(bool, default false). *Measured:* `quote` is empty on all 72,961 v3 training rows.

**Quotes are kept in their own table, not written into a sample.** The 10% export is
not random from run to run: `export.py` picks respondents with a fixed seed (3407) from
a sorted list of IDs, per study, so the same rows give the same 10%. *Measured:*
`(study, recipe, participant_id, condition_num, task_num)` is unique on every v3
training row. So:

1. A quote table, keyed by that row key, holding the quote and a hash of what it was
   written from (persona, condition, outcome, response).
2. The export joins quotes onto the rows it selects: the next version is the same 10%
   (same seed) plus quotes.
3. Quotes accumulate: a later export (25%, full) only needs quotes for rows not yet in
   the table. Nothing is written twice.
4. A quote whose input hash no longer matches its row (the row changed upstream, as
   `8ctbk`'s outcome did) is not joined, and is rewritten.

In the exported rows:

- `quote`: the accepted quote; `synthetic_quote`: true.
- Rows with no accepted quote after the repair rounds keep an empty `quote`, and are
  counted (section 7).
- **Provenance in the export manifest:** writer and checker model ids and revisions,
  prompt versions, sampling settings, seed, pass rate, rows left without a quote.
- The reason angle and voice drawn for each row (section 6) are kept as columns of the
  quote table, not exported with the rows, so a run can be repeated and analysed.

## 5. Writing

**Model: Qwen3.8-27B** (`Qwen/Qwen3.8-27B`; an FP8 copy is `Qwen/Qwen3.8-27B-FP8`).
Apache 2.0, 27.8B dense, released Aug 2026. Apache 2.0 matters: the quotes are used to
train a model, which frontier labs' terms restrict. Avoid `Qwen3.8-Flash-Next` (custom
Qwen community licence).

- **Thinking off.** It is on by default; switch it off per request as the model card's
  "non-thinking mode" section shows (confirm the exact parameter there).
- **Sampling:** the card's settings for non-thinking mode: temperature 0.7, top_p 0.8,
  top_k 20, min_p 0, **presence_penalty 1.5** (discourages stock phrases).
- **Input:** the full persona (every field in `persona`, not only `persona_text`), the
  condition, the outcome, and the real response with its scale labels.
- **Ask:** one to three sentences, first person, plain everyday British English, about
  the condition and their answer; no numbers or scale references; no reciting the persona
  ("as a 45-year-old..."); only the quote.
- **Spoken, and felt** (rich, 30 Oct 2026). The quote is someone talking about the
  condition and their answer, and its tone carries their reaction. The condition is
  whatever the study put to them, in its own form: a message or warning they read, a
  scenario they were asked to imagine themselves in, a vignette about someone else to
  judge, a policy or product described, a profile to rate, or no stimulus at all (then
  the reaction is to the question itself). The quote responds to that form: "if that
  were me I'd be terrified" for an imagined diagnosis, "she's had a raw deal" for a
  vignette, "that's daylight robbery" for a price. A cancer warning that made them want
  to change is said with fear or worry in it; an unfair situation with irritation; a
  charity appeal with guilt or warmth; a dull description with boredom. The strength of
  the feeling follows the response: someone strongly moved sounds moved, someone barely
  moved sounds flat or dismissive, and someone who reacted against it can sound
  defensive, scornful or amused. Emotion is drawn from the condition and the response,
  never added for colour where neither supports it.

## 6. Variation

Temperature alone changes wording, not reasons. *Measured:* exact twins (same
persona, condition, outcome and response) are rare, 367 of 72,961 rows (0.5%), but up to
267 rows share a condition, outcome and response with different personas. The risk is
convergence: every one of them given the same obvious reason.

Base approach:

1. **Sampling settings** as above.
2. **A reason angle and a voice drawn per quote**, seeded and recorded. Angles such as
   cost, fairness, family, personal experience, distrust, values, gut feeling, mood,
   habit, a half-remembered story, a mistaken belief, contrariness, self-interest, not
   really knowing; voice such as short or chatty, sure or unsure, plain or articulate,
   rambling, blunt. The irrational angles are drawn as often as the reasoned ones. The
   checker rejects an angle only when it cannot fit the persona and response, never
   because it is unreasonable.
3. **The full persona**, which gives real grounds to differ without inventing any.
4. **For large groups** sharing a condition, outcome and response: write k quotes from k
   different respondents in one call, each with their own persona, so the model makes
   them differ.

Within one respondent, quotes should sound like one person across that study's
outcomes: draw the voice once per respondent, not per row, and **write all of one
respondent's quotes for a study in one call** (their persona once, then each condition,
outcome and response in turn), so their reasons do not contradict each other from one
outcome to the next unless a person plausibly would. Group writing (point 4) then
applies across respondents within the same study.

Optional later: rotating real open-text answers as style examples, where a study
collected them; several candidates per row with the most different kept.

## 7. Checking

**Model: Gemma 4 31B** (`google/gemma-4-31B-it`). Apache 2.0, 31.3B dense, released Mar
2026. A different family from the writer on purpose: a model grading its own family's
writing tends to pass it. Thinking off (it is switched on by a `<|think|>` token at the
start of the system prompt; leave it out).

Per quote, a structured (JSON) verdict:

- **Fits the response** in direction and strength.
- **Tone fits the condition and response**: the feeling in the quote is the reaction
  this condition could provoke, in its own form (a message read, a scenario imagined, a
  vignette judged, a profile rated), in someone who answered this way, at the right
  strength. A calm, neutral quote about a frightening scenario from someone it moved
  fails; so does alarm from someone it left cold; so does a quote that treats an
  imagined situation as a message read, or a vignette about someone else as their own.
- **Stays within the persona** (rich, 30 Oct 2026): small invented details that fit the
  person are allowed, the way people explain themselves ("my sister got it too"); anything
  that contradicts a recorded detail fails ("my wife" from someone divorced, grandchildren
  from a 19-year-old, "at work" from someone retired). Prompts v2. Such details come from
  the writer, so how OFTEN a reason or anecdote appears is not a finding about people.
- **Aligned with the persona** (rich, 30 Oct 2026): a reason THIS person could
  plausibly give, given their age, life stage, work, household, region, education and
  views as recorded, and a voice that fits them. A quote that would fit anyone equally
  well fails. Plausible, not typical: the check asks whether this person could say it,
  never whether it is what their group usually says, and it never requires the quote to
  mention a persona attribute (that would reward stereotypes and persona recital).
- **About the condition**: refers to what the condition actually was (message, scenario, vignette, profile or none), not something the study never put to them.
- **No giveaways**: no numbers, no scale talk, no persona recital.
- **Blind test**, a separate call: given persona, condition, outcome and the quote but
  not the response, predict the response. Scored on DIRECTION (same side of the scale,
  roughly), not the exact value: an exact-match test favours obvious reasons and filters
  out exactly the idiosyncratic ones this spec wants.
- **Never graded on reasonableness.** The checker is told explicitly that a weak,
  emotional, inconsistent or factually wrong reason is acceptable, often desirable, as
  long as it fits the response and this person. It must not reject or "repair" a quote
  for being irrational, and the repair prompt must not make quotes more sensible.
- The pilot reports pass rates split by how unusual the response is for the condition
  and by angle, so any checker that quietly filters unusual answers or irrational
  angles shows up as a lower pass rate there.

Failures are rewritten and checked again, up to a fixed number of rounds. Quotes that
never pass are left empty and counted per source and study.

## 8. Measuring variety

With Voyage embeddings of the quote text (through `embed.py`; the quote sentence only,
with no persona, condition, response or identifier), per group of rows sharing a
condition, outcome and response. Groups are formed here by `(recipe, factors, outcome,
response)`, not condition text, since conjoint and order-randomised conditions make
almost every condition text unique.

- **Spread:** mean pairwise cosine distance.
- **Near-duplicates:** share of pairs above about 0.9 similarity.
- **Effective number of distinct quotes:** Vendi score.
- **Separation:** quotes for different responses to the same condition and outcome
  should sit apart.

Aim: match human variety, not maximise it; maximised variety drifts into reasons no
real person gives. Where a study collected open-text "why" answers, their scores are the
target. Otherwise choose the setting with the most variety among those where at least
95% of quotes pass the checker.

## 9. Infrastructure

One RunPod pod (batch work; serverless suits the occasional requests of the trained
models later), serving **one model at a time with the whole GPU**: write all, switch,
check all, switch, rewrite the failures, switch, check them, and so on. This is the
design agreed at the start. From 30 Oct the pilot and the first 10,000-row batch ran both
models side by side instead, which was not agreed: each phase left the other model's
memory idle, and the checker, short of KV cache (98.6% full, 36 checks at once, about 2 a
second), would have taken hours for one batch. It was stopped and replaced.

- **The router** (`scripts/quotes_router.py`) owns the one vLLM server. `POST
  /admin/switch` stops the current model, waits for the port and GPU memory to free,
  starts the named one and reports `switching`, `loading`, `ready` or `failed` with the
  last error line of its log (`GET /admin/state`). Requests naming the other model get
  409. Models and their vLLM flags: `scripts/quotes_models.json` (0.90 of GPU memory).
- **The runner** (`scripts/quotes_run.py`, run here) switches the pod at the start of
  each phase, saves after each phase, prints progress as calls complete, and `--resume`
  carries on from the last saved phase on the same rows.
- **The card.** One model at a time needs room for Gemma 4 31B in FP8 (about 31 GB of
  weights) plus enough KV cache to run many checks at once: on a 48 GB L40S only about
  6 GB would be left, room for 2 or 3 checks, so the spec's original L40S does not suit
  this checker. An 80 GB or larger card does; the choice and its cost go to rich first.

Embeddings for the variety measures are Voyage, called from here (section 8).

## 10. Pilot

About 300 TESS and Dataverse training rows, spread across studies, text rows only,
chosen as whole respondents (so respondent-level writing is tested) and including rows
from the large shared groups (so group writing is tested).

Before the pilot, count the built studies that collected real open-text answers. About
ten recipes mention open-ended items (5hqan, 7tzpe, cug34, gh396, a2nbf and others);
their answers, read from the raw files, are the variety target in section 8 and the
optional style examples in section 6. Count first; whether they become rows of their own
is a separate decision.

1. Settings to compare: sampling only; plus angle and voice; plus full persona; plus
   group writing.
2. For each: checker pass rate per check, blind-test agreement, and the section 8
   measures.
3. Read the quotes: rich, a datasets agent and the training agent, per source and per
   response level.
4. Choose settings; record the choice and the numbers in this repo's ledger or
   conventions.

Done when the chosen setting reaches the pass rate, its variety is recorded, and a
separate agent (different model, briefed to break it) has read a sample.

## 11. Decisions (30 Oct 2026)

Proposed by the datasets agent, agreed by rich:

- **Length:** a short phrase up to three sentences. Real people are often brief.
- **Per-row angle and voice:** kept, as columns of the quote table (not exported with
  the rows), so a run can be repeated and analysed.
- **Blind test:** direction only (section 7). Exact tolerance set in the pilot.
- **Repair rounds:** two.
- **Group size k:** 5.
- **First export with quotes:** all sources at once.
- **Embeddings:** Voyage, the quote sentence only (section 8). Decided by rich.
- **Respondent-level writing:** one call per respondent per study (section 6).
