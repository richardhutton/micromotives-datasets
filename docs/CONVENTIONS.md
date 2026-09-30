# Recipe conventions

Rulings that apply to every recipe, so they are decided once rather than per
study. `docs/LEDGER.md` records *what went wrong*; this records *what we decided*.

---

## Characters: typography normalises, words never do

**Normalise to ASCII:** curly apostrophes and quotes (`’ ‘ ” “` → `' "`), en and
em dashes (`– —` → `-`), the ellipsis character (`…` → `...`), and non-breaking
spaces.

**Never normalise:** words, spelling, grammar, capitalisation, or punctuation that
changes a sentence. Source typos are kept verbatim — `a5v96`'s doubled "make sure
that that he is right", `zaqkm`'s "sticks with himself all day long", `cug34`'s
missing comma in one attribution arm. If in doubt, it stays.

### Why this line and not "preserve the source exactly"

Because **the sources are not internally consistent, so "preserve the source"
does not name a single answer.** Measured on `zaqkm`'s questionnaire: 43 curly
apostrophes, 7 straight, and one bare `David s` with none at all — for the same
word, in the same file. Preserving bytes would put the same possessive into the
corpus three different ways, none of which any respondent would have perceived as
different.

The deeper reason is what the two cases can and cannot carry:

- A **glyph** variant is an artefact of document conversion — which word
  processor wrote the `.doc`, how it was exported to `.txt`. It cannot be part of
  the manipulation, and no respondent could have read one as different from the
  other.
- A **word** variant can be. A typo or an odd phrase carries register and
  authenticity, and in a stimulus that is content. We have no way to know it is
  not load-bearing, so we keep it.

It also matters that this corpus gets **merged across studies**. Arm text that
differs only in apostrophe style would give a model a spurious signal about which
study a row came from.

### Practical note

13 of the first 14 recipes already do this, having straightened quotes without
anyone deciding to. `zaqkm` is the single outlier (114 curly in arm text), so the
sweep is one file — see the open items in `docs/LEDGER.md`.

Keep the normalisation in the recipe, not in `build.py`. The YAML should read the
way the row will read; a transformation hidden in the pipeline would make the
recipe stop being the audit trail.

---

## Arm text: verbatim for what varies, compressed for what is shared

The oldest rule in the project and the reason the recipes are trustworthy.

- Context identical across every arm goes in `shared_context`, **once**.
- Each arm carries only its own varying remainder, **verbatim**.
- A declared factor that does not change the text between arms is a **defect**,
  not a cosmetic issue — QC rule 5 tests exactly this, via minimal pairs.

`shared_context` is a **prefix**. Shared material that sits mid-paragraph cannot
be hoisted, and is therefore repeated per arm (`cug34` repeats one sentence 24
times). That is correct: keeping the paragraph as the respondent read it beats
de-duplication.

## Source authority

1. **The fielded questionnaire is the only authority on stimulus wording.** Never
   the proposal, never the paper appendix, even when the appendix reprints what
   looks like the stimulus. SocSci210 built at least three studies from the
   proposal using words no respondent saw (ledger #35, #44, and `zaqkm`).
2. **The proposal PDF is a legitimate authority on arm ORDER and factor names** —
   it resolved `a5v96`'s malformed block header decisively. But it can be stale
   even there: `cug34`'s proposal describes 12 cells where 24 were fielded.
3. **A lookup spreadsheet referenced by the questionnaire is part of the
   instrument.** `b87sm`'s questionnaire contains no arm text at all, only
   `[INSERT P_S1]` and "see excel table"; all 72 vignettes are in the `.xlsx`.
4. Where a deposit ships both *simple* and *prog* questionnaires, **derive from
   both and assert equality**. It is free and it catches parser bugs before they
   reach the YAML (ledger #52). Where they genuinely disagree, follow *simple*
   and record the disagreement in `notes`.

## Never invent stimulus text

If the source does not contain text for something, say so in `notes` and leave it
out. "Cannot determine from source" is a finding, not a failure. Omitting a
paragraph and documenting the omission always beats guessing at it — `z358z`'s
maker did this and was right to.

The one accepted exception is a **layout** manipulation with no words anywhere in
the source (`evnyh` varies whether a scale runs down the page or across it). The
option labels are transcribed verbatim; the layout gets one clause of plain
description, and `notes` must say explicitly that the clause is description
rather than transcription.

## Scope

- One recipe melts one condition variable, so **one recipe per sub-experiment**,
  named with `experiment:`. Output is keyed `<study_id>_<experiment>`.
- Deliberate scope limits get recorded in `notes` **and**, where a screen would
  otherwise flag them, in `condition.considered_and_rejected` with a reason. A
  recorded reason must be *accurate*, not merely present — a wrong reason is
  worse than none, because it closes the question.
