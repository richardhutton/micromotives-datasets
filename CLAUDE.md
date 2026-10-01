# CLAUDE.md

This project turns raw research data (experiments, surveys, panels) into
model-ready datasets for predicting human behaviour. This file holds the rules
that apply to **any** dataset built here. Dataset-specific detail lives in
`docs/`, not in this file.

**This is a living file.** Agents update it as they learn — see the last section.

---

## Before starting

- Read this file, then the relevant design doc in `docs/`. Design docs are the
  primary artefact: if the code and the doc disagree, flag it rather than
  silently picking one.
- Check what already exists (schema, sources, recipes, tests) before writing
  anything new. Extend; never build a parallel version.

Where to look, in order: `docs/LEDGER.md` (numbered findings — the most valuable
document here, read it before building anything), `docs/CONVENTIONS.md` (the
rulings those findings produced), `docs/SocSci-UK_MASTER.md` (schema, sources,
pipeline, status).

## The row contract

Every training row is a **(persona, condition, outcome, response)** tuple:

- **Persona** — who is responding: their attributes, as recorded in the source.
- **Condition** — what they were shown, rendered as the actual text/stimulus.
  If there was no stimulus, say so explicitly with a consistent sentinel.
- **Outcome** — the question they were asked.
- **Response** — what they answered, as a single, in-range value.

Keep the identifiers that make held-out splits possible (study, condition,
outcome, participant). Keep anything that varies *within* a condition (e.g.
conjoint profile attributes) as structured metadata, not only in prompt text.
The thing being judged is never part of the persona.

Four distinct parts. Never collapse outcome into condition.

**The condition is the only part we write.** Persona, outcome and response are
all read out of the source; the condition is assembled by us. So an error there
is the one error nothing downstream can detect — it produces a row that teaches
the model the wrong question while every count still reconciles.

## Never fabricate

The dataset's value is that every row is something a real person actually did.

- Never invent a stimulus, a response, a persona attribute, or a quote.
- Never attach a stimulus to a row that had none.
- Never translate or "harmonise" a value into something the source doesn't
  support. Absent stays absent; merged categories stay merged.
- Never impute missing responses. Drop missing/don't-know codes.
- If the source doesn't contain what's needed, the study fails — log it and move
  on. A skipped study is fine; a fabricated one poisons the set.

"Cannot determine from source" is a finding, not a failure.

## Using Jev (the LLM judge)

**Jev** (the `typesafe-sdk` package) is this project's structured-judgement API:
`TypeSafeClient.system_one(state, questions)`. Use it for the questions that
need **reading comprehension**, and only those.

**Pick the right primitive** — they are not interchangeable, and the wrong one
returns a number that looks usable and means something else
(https://docs.typesafe.ai/primitives):

| Primitive | For | `criteria` | Returns |
|---|---|---|---|
| `Noul` | a **yes/no** question where the probability itself is the answer | optional: what yes and no mean | `noul`, a probability 0–1 |
| `Choice` | pick one from a known **unordered** set | a MAP of option name to description; include `other` when coverage is uncertain | `choice`, `probabilities`, `confidence` |
| `Score` | a position on a **defined spectrum**, each level given a meaning | an ORDERED LIST of levels | `score` (may fall between levels), `legend`, `probabilities`, `confidence` |

The trap, in the docs' own words: *"A Noul value of 0.5 means the model gives
yes and no equal probability. It does not mean the candidate has a medium skill
level."* A `Noul` is **not** a magnitude. Do not rank, average or weight `Noul`
values as if they were positions on a scale — that is what `Score` is for, with
the levels written out.

`Noul` has no confidence field (the probability is the answer). `Choice` and
`Score` do, and the docs are explicit that it exists to decide *"when to act
automatically and when to escalate to a person"* — so read it rather than
taking `.choice` alone. Questions in one call are independent: removing one does
not change the others.

**One door: `scripts/recipe_prep.py <study_id>`.** Run it BEFORE writing a
recipe. It asks all four Jev-able questions about a study — which column is the
randomised assignment, which columns are the persona attributes, which value
labels are non-answers, and which questionnaire directives `quex` refuses and
whether any of them gate stimulus text. Everything it prints carries a
confidence and is flagged REVIEW when the model was unsure or the runner-up was
close. Wave 1 was authored without it, by five agents reading variable names by
eye, because it did not exist and its parts were scattered across eight scripts.
`src/micromotives_datasets/jev.py` is the shared layer underneath. (2026-10-01)

**Use Jev for meaning.** What construct does this variable measure? What does
this response label denote? Which of these columns holds the randomised
assignment? Does answering this question require local knowledge a respondent
elsewhere would not have? Which domain does this outcome belong to? These are
semantic judgements over question wordings and labels, and no amount of regex
will do them — a pattern-match offered six variables about a fictional
character as "household income" until the candidate list was widened.

**Use code for mechanics.** Do these bands tile without gaps or overlaps? Is
this recode injective? Does this variable exist in the file? Do these two
questionnaire versions agree? Anything decidable by arithmetic or parsing is
code's job, because code can be unit-tested and a judgement cannot.

**Never auto-accept.** Jev ranks and flags; a person or a second, independent
pass decides. Record the score next to the decision so a later reader can see
how close the call was. Do not write a threshold that silently commits.

**Calibrate before trusting a new question.** `scripts/jev_probe.py` and
`scripts/jev_calibration.py` pose questions whose answers are already known
from hand-built sources, so a new prompt can be scored before it is pointed at
sources with no reference. Do this: the transfer screen scored 12/16 against
hand-read studies, and **two of its four errors were in the dangerous
direction** — it called a source fully transferable where reading the
questionnaire said otherwise. That is why the screen orders the queue and never
overrules an eye.

**Known failure modes**, all observed here:
- **Using `Noul` where `Score` belongs.** `uk_priority.py` asked
  `uk_relevance` and `evergreen` as `Noul`s and ranked 59 studies by
  `relevance + 0.15 * evergreen` — arithmetic on two probabilities-of-yes. FIXED:
  both are now `Score` with five written-out levels, and the values discriminate
  where they had not (evergreen spreads 0.39–3.88 against a tight high cluster; a
  2002 smallpox-vaccine study correctly collapses to 0.39). The thresholds in
  `uk_content_screen.py` remain a legitimate `Noul` use — those really are yes/no
  questions. (2026-10-01)
- **An oversized call answers "none of the above" instead of failing.** See the
  option-list note below; this is the failure mode most likely to go unnoticed,
  because an empty report reads exactly like a clean one. (2026-10-01)
- A narrow option list inflates confidence. Keep candidate lists wide and let
  the low scores do the rejecting.
- A "prefer the more granular measure" tiebreak misfired three times by
  preferring a *different construct* that happened to be finer. Make tiebreaks
  narrow, and check whether one was load-bearing.
- Confidence is not calibrated across question types; compare scores within a
  question, not between questions.

**What may go on the wire.** Question wordings, variable labels, value labels
and study titles — the instrument. **Never respondent rows.** This property is
deliberate and worth preserving in any new script; `scripts/jev_show_wire.py`
prints the exact JSON a call sends so you can check. Licence-restricted data
(see **Data handling**) must never reach Jev at all, instrument included, until
the licence has been read.

**Ask one question at a time, and keep option lists under ~45.** Measured: a
`Choice` over 57 variables answers correctly and confidently; the same question
over 150 returns NONE_OF_THESE for every field, including fields whose variable
is plainly in the list. An oversized call does not error — it quietly answers
"none of the above", and an empty report reads exactly like a clean one.
`jev.choose` pages and runs off rather than truncating, because narrowing the
list by keyword is the caller making the decision it is asking the model to
make. **Carry each page's runner-up forward too**, or a candidate that loses its
own page is never compared against the answer at all. (2026-10-01)

**Practical notes.** `TYPESAFE_API_KEY` lives in `~/.bash_profile`, which the
Bash tool does not source — prefix `source ~/.bash_profile &&`. The primitive
reference above is the authority on `criteria`'s shape, which differs per
primitive and is the easiest thing to get wrong.

## Definition of done

A source is done only when **all** of these hold:

1. Built by one agent, **verified by a separate agent** that didn't build it.
2. QC passes with no warnings: rows well-formed, condition ↔ stimulus
   consistent, every response in range, persona fields mapped.
3. Checked against an independent reference where one exists (published
   numbers, another build of the same data). Where none exists, say so.
4. Tests added and passing. For a **source**, its recipe plus QC plus the
   independent crosscheck *are* its tests: all three are executable, all three
   re-run on every build, and the recipe is a reviewable text file. Unit tests
   belong to the **pipeline**, which is the part with branches. Adding a rule or
   changing shared code means adding a test for it, and mutation-testing that
   test. (Ruled 2026-10-01.)
5. Source, licence and provenance recorded.

"The code runs and produces rows" is **not** done.

## Data handling

- Raw and processed data never enter git.
- Respect each source's licence. Some forbid redistribution or sending data to
  external services — check before uploading, sharing or calling an API with it.
- Credentials live in environment variables, never in code or logs.
- Prefer original file formats over converted ones when conversion loses
  information (labels, codes).
- **UKDS safeguarded** data (Innovation Panel SN 6849, restricted BES) is End
  User Licence: never redistribute, never commit, never send to any external
  service including an LLM API, without checking the EUL first.
- Missing-value codes in survey microdata are negative (UKHLS `-1`, `-2`, `-7`,
  `-8`, `-9`) or `9999` (BES). Strip before making integer responses.
- Synthetic quotes are always labelled synthetic, never presented as real
  respondent words.

## Evaluation

- Measure against held-out data the model has never seen; never let held-out
  material leak into training.
- Report bounds alongside results (e.g. a random baseline and a
  resampling ceiling) so numbers mean something.
- Match the evaluation method of any reference work you compare against.

## Working rules

- One source at a time. Small, verifiable steps.
- When a source has a structure the pipeline can't handle, stop and report it.
  Don't force it into the wrong shape.
- Don't change shared code (schema, pipeline, core utilities) without stating
  what changes and why.
- Log every skipped or failed source with the reason.
- Lint, type-check and tests must pass before any commit.

---

## Keeping this file current

Agents **should** update this file when they learn something the next agent
would need. Rules for updating:

- Add only what is **general and durable** — true across sources, likely still
  true next month. Dataset-specific detail goes in `docs/`.
- Record **decisions**, not progress. No status updates, no "currently working
  on", no task lists.
- Keep it short. Edit or merge an existing line before adding a new one.
- Never weaken a rule in "Never fabricate" or "Definition of done" without the
  human's explicit approval.
- Note the date and a one-line reason with each addition.

### Project conventions
<!-- Agents: record tooling, layout and naming conventions here as established. -->
- Python project managed with **uv**. Add dependencies with `uv add`, run
  everything with `uv run` (scripts, tests, tools). Never use `pip install` or a
  bare `python`; commit `pyproject.toml` and `uv.lock` together.
- `src/` layout, Python 3.12+. Folder and repo hyphenated, package underscored.
  Gate before every commit:
  `uv run ruff check . && uv run ruff format . && uv run mypy src/ && uv run pytest -q`.
  (2026-10-01)
- One YAML per sub-experiment in `recipes/`, named `<study_id>[_<experiment>]`.
  The recipe holds every judgement; the melt stays pure and deterministic, so a
  build can be re-derived from the recipe alone and reviewed as a text file.
  (2026-10-01)
- `data/raw/` and `data/processed/*.parquet` are gitignored, per **Data
  handling**. `data/catalog/` IS tracked and should stay so: it holds metadata
  about studies — titles, rankings, screen verdicts, crosswalks — never
  respondent rows. (2026-10-01)
- Secrets live in `~/.bash_profile`, which the Bash tool does not source.
  Prefix `source ~/.bash_profile &&`. (2026-10-01)
- Typography may be normalised (curly quotes, en dashes, non-breaking spaces);
  **words never are**. A regex that matches source text keeps the source's own
  characters. (2026-10-01)
- Commit messages end with:
  `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`

### Lessons learned
<!-- Agents: record general pitfalls and how they were resolved. One line each, dated. -->
- **Build the artifact and inspect it.** Every serious defect in this project
  has been invisible per source and obvious once the corpus was merged and
  read: three sources with no persona at all, 23,464 participants collapsed to
  4,010 ids, 8,774 rows carrying an answer instruction their own response
  contradicted, 13,513 rows telling a respondent they were reading scenario 1
  while rating scenario 5. Every one passed QC. Per-source checks are necessary
  and nowhere near sufficient — merge and read rows. (2026-10-01)
- **Mutation-test every check.** QC rule 5 was vacuous across eight sources: it
  only failed when ALL arms were identical. A check never shown to fail is not
  known to work. Break it deliberately, watch it catch it, and keep a test for
  both directions — the thing it must catch AND the legitimate case it must
  ignore. (2026-10-01)
- **Measure the corpus before writing a heuristic.** A directive grammar that
  three worked examples suggested covered 733 of 1,522 real cases; eight income
  banding schemes existed where two were assumed; a regex offered six fictional
  vignette variables as household income. Count across all sources, then write.
  (2026-10-01)
- **A documented debt stops being visible the moment it is documented.** Four
  sources recorded the same schema gap in their own notes and it survived
  several rounds of work. What moved it was counting the 40,296 rows it cost.
  Put a number on a debt or it will not be paid. (2026-10-01)
- **Two resolvers answering "which value applies here" must agree.** One
  preferred the outcome's scale and the other the arm's; the disagreement sent
  47% of a source's rows out with an instruction contradicting their own
  response, silently. Route every such question through one function.
  (2026-10-01)
- **A suppression derived from "things not yet dealt with" is removed by every
  way of dealing with them.** The same bug landed twice from opposite
  directions: recording variables as rejected un-silenced their components, and
  later declaring them did the same. Derive suppression from what is DECLARED,
  which no act of declaring can empty. (2026-10-01)
- **A row cannot cite its own position in a sequence** ("Please read Scenario #5
  carefully", "on the previous page"). The row format has no way to express it,
  and in a within-subject design the number is wrong for most rows. Drop it.
  (2026-10-01)
- **Variable lookups must be case-insensitive; participant ids must be
  namespaced per source.** Both failures are silent, both have happened, both
  cost whole sources. (2026-10-01)
- **"Presumably" in a verification note is a guess wearing a finding's
  clothes.** Likewise a correct claim cited to the wrong artefact — state where
  a check's authority actually lives, or the next reader will look there, find
  nothing, and reasonably conclude it was assumed. (2026-10-01)
- **Write the test expecting to see it fail.** Several tests here were wrong
  before the code was: one asserted a universal label contains no "or" (it did),
  another compared two schemes that made the same distinction and so tested
  nothing. A test that passes first time deserves suspicion. (2026-10-01)
- **An LLM judge gets more confident as the option list narrows**, and a
  "prefer the finer measure" tiebreak will happily prefer a *different
  construct* that happens to be finer. Keep candidate lists wide and make
  tiebreaks narrow. (2026-10-01)

### Decisions
<!-- Agents: record design decisions agreed with the human. One line each, dated. -->
- **Build every source from the primary instrument; use any published
  reconstruction as a numeric answer key only.** The reference set we compare
  against has wrong stimulus text in most sources audited, while its arm
  assignment and row counts are nearly always right. (2026-10-01)
- **The fielded questionnaire is the only authority on stimulus wording** —
  never the proposal, even where the proposal reprints what looks like the
  stimulus. A proposal can also describe a smaller design than was fielded, so
  its condition *count* can be wrong too. A lookup spreadsheet the
  questionnaire references is part of the instrument. (2026-10-01)
- **Harmonising persona attributes may only MERGE, never split.** Canonical
  boundaries are the intersection of every scheme's boundaries, so an edge
  survives only if every scheme has it. This is what keeps the crosswalk inside
  "merged categories stay merged" under **Never fabricate**: producing a finer
  category than a source offered would invent a distinction nobody measured.
  (2026-10-01)
- **The LLM judges meaning; code judges mechanics** — settled by measurement
  across 785 candidate columns, of which 327 were rejected. See **Using Jev**
  above for the division of labour, the calibration requirement and the
  wire rule. (2026-10-01)
- **Maker/checker on every source**, the checker briefed to break the work
  rather than confirm it and told explicitly that a PASS is not evidence. A
  maker should name its own riskiest judgement before being asked — the two
  times that happened here, one of the flags exposed a real pipeline bug.
  (2026-10-01)
- **Verbatim for what varies, compressed for what is shared.** Context identical
  across arms is stated once; each arm carries only its varying remainder,
  verbatim. A declared factor that does not change the text between arms is a
  defect, not a cosmetic issue. (2026-10-01)
