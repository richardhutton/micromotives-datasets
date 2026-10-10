# Recipe conventions

Rulings that apply to every recipe, so they are decided once rather than per
study. `docs/LEDGER.md` records *what went wrong*; this records *what we decided*.

---

## Characters: typography normalises, words never do

**Normalise to ASCII:** curly apostrophes and quotes (`’ ‘ ” “` → `' "`), en and
em dashes (`– —` → `-`), the ellipsis character (`…` → `...`), and non-breaking
spaces.

**Never normalise:** words, spelling, grammar, capitalisation, or punctuation that
changes a sentence. Source typos are kept word-for-word — `a5v96`'s doubled "make sure
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

## Arm text: word-for-word for what varies, compressed for what is shared

The oldest rule in the project and the reason the recipes are trustworthy.

- Context identical across every arm goes in `shared_context`, **once**.
- Each arm carries only its own varying remainder, **word-for-word**.
- A declared factor that does not change the text between arms is a **defect**,
  not a cosmetic issue — QC rule 5 tests exactly this, via minimal pairs.

`shared_context` is a **prefix**. Shared material that sits mid-paragraph cannot
be hoisted, and is therefore repeated per arm (`cug34` repeats one sentence 24
times). That is correct: keeping the paragraph as the respondent read it beats
de-duplication.

## Sequence signposting: a row cannot say where it sat

**Drop any text that cites the row's own position in a sequence** — "Please read
Scenario #5 carefully", "the third of eight questions", "on the previous page".
Do not transcribe it and do not vary it per item.

A row is one `(persona, condition, outcome, response)` tuple. It has no way to
express "this is the fifth of eight screens you have seen", so a numbered
self-reference asserts a sequence the row does not contain. In a within-subject
design it is additionally *wrong* for most rows: `b87sm` hardcoded "Scenario #1"
into `shared_context`, and 13,513 of its 19,282 rows (70.1%) told the respondent
they were reading scenario 1 while rating scenario 2 through 8.

Note what did not catch that. The 72 arms still rendered 72 distinct strings, so
rules 1 and 5 were satisfied; the arm text matched the source byte-for-byte; the
row counts reconciled exactly; QC passed with zero warnings; an independent
exhaustive check of all 19,282 rows' arm assignment found no error. A checker
found it by reading one rendered row and asking what it said. **QC rule 15** now
tests it, on numbered references only — "the following scenario" points inside
the same row and is correct.

This is the same ruling as dropping survey mechanics ("on the following pages
you will see 8 different scenarios"), and for the same reason: both describe the
instrument's structure, which the row format does not reproduce.

## One stem, several labelled answer fields

Where one question screen collects **several numbers under their own field
labels** — `cug34`'s B02 asks how much goes in the shared account *and* the
individual account on one screen — build one outcome per field and append a
single sentence naming which field this row reports: *"Report only the amount
for the Shared Account."*

This is permitted because it disambiguates the **response format**, not the
stimulus: the respondent's decision is already made and fixed, and the sentence
only says which of their two numbers this row carries. It is the same job the
scale instruction does.

Two conditions, both required:
- the field name must be the **source's own label**, quoted, not a paraphrase;
- `notes` must record the added sentence word-for-word and say it was added.

It is narrower than the layout exception above. That one exists because the
source contains *no words at all* for the manipulation; this one is reusing
words the source does contain.

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

## The condition must not name the respondent's own persona category

Distinct from the domain rule, and stricter. The domain rule says a persona
attribute must not sit in the same domain as the outcome — it is about
CORRELATION, and it is why `EFXNLX` drops `eu_referendum_vote` and
`6MRVOM_eu_share` drops `pastvote_EURef`.

This is a different failure. If the condition text names the categories a persona
field distinguishes, the answer is not correlated with the persona, it is
DERIVABLE from the prompt by substitution, and the row stops measuring anything
about people.

The case that established it is `X08IVC` (dropped 2026-10-05). Its cued condition
read:

> "A recent survey has shown that most Leavers agree that immigration should be
> reduced, whereas most Remainers do not agree that immigration should be
> reduced."

and its persona carried `brexit_identity` ∈ {Leaver, Remainer, Neither}. Given
`{persona: Leaver}` and that sentence, a model reaches the expected answer with no
knowledge of British politics, of immigration, or of people. It only has to match
a string.

**What to do when you find one.** Three options, in order of preference:

1. **Remove the persona field.** Correct whenever the study has other persona
   fields, which is the normal case.
2. **Drop the study**, if removing the field leaves no persona at all. `X08IVC`
   had eleven columns and no demographics of any kind, so excluding
   `brexit_identity` left 1,124 rows describing nobody.
3. **Keep it and mark it** in `experiment_manifest.json` as trivially
   predictable. Only defensible for a study whose diagnostic value as a floor
   outweighs the risk, and only if no aggregate score can be reported without the
   mark travelling with it. `X08IVC` was judged not to clear that bar.

**What it does NOT cover** (ruled by rich, 10 Oct 2026, on IP 9.16). A condition
that merely MENTIONS a group the persona can belong to is not this failure. 9.16's
list item "The UK should allow people from Caribbean countries to come and live
here" sits beside a persona ethnicity of "Black, Black British, Caribbean or
African", but it states no attitude for anyone, so nothing can be matched across:
ethnicity there is an ordinary predictor, like age, and stays. The test is whether
the condition says what a persona group THINKS or DOES, so that the answer follows
by substitution. Naming a country, a nationality or an ethnicity is not enough.

**How to spot it.** Read one rendered condition against the persona fields beside
it, for one row. This is not detectable numerically — the study verified against
all four cells of its authors' published table, on both N and mean, while being
unusable for its intended purpose.

## Never invent stimulus text

If the source does not contain text for something, say so in `notes` and leave it
out. "Cannot determine from source" is a finding, not a failure. Omitting a
paragraph and documenting the omission always beats guessing at it — `z358z`'s
maker did this and was right to.

The one accepted exception is a **layout** manipulation with no words anywhere in
the source (`evnyh` varies whether a scale runs down the page or across it). The
option labels are transcribed word-for-word; the layout gets one clause of plain
description, and `notes` must say explicitly that the clause is description
rather than transcription.

## Scope

- One recipe melts one condition variable, so **one recipe per sub-experiment**,
  named with `experiment:`. Output is keyed `<study_id>_<experiment>`.
- Deliberate scope limits get recorded in `notes` **and**, where a screen would
  otherwise flag them, in `condition.considered_and_rejected` with a reason. A
  recorded reason must be *accurate*, not merely present — a wrong reason is
  worse than none, because it closes the question.

## Narrating what the respondent did

A manipulation delivered across several screens — a writing task, then a passage
to read — has to become ONE condition string, and the join has to be written by
us. That is permitted, under three conditions, all required:

- it narrates **what the respondent did**, never what they were shown;
- it is **true for everyone in that arm**, with no numbers and no sequence
  position (see **Sequence signposting**);
- `notes` records the added words word-for-word and says they were added.

`a42yg` is the worked example: *"You first completed a short writing task, and
then read a passage..."*, then the values list and the writing prompt both
word-for-word, joined by *"You then selected a value and were asked:"*. Every other
word is the instrument's.

This is narrower than it looks. The alternative was either to drop the
self-affirmation factor from the text — which QC rule 5 correctly fails as a
declared factor that does not express — or to present a two-screen task as one
undifferentiated block, which would be less true, not more.

**Repeated measures within one block** (ruled by rich, 10 Oct 2026). When a
respondent answers the same question several times as a block unfolds, and the
ORDER of the screens is what was randomised, each row's condition is everything
shown in that block up to and including its own screen, in that respondent's
order. Later screens are never named. `del_sandbox_jul2020_global_goals` is the
worked example (conditions of 26-370 words), and it is the only way both
randomised orders reach the text. Earlier answers are narrated as asked, never
as given: *"You were asked to rate..."*, not *"You rated..."*, because a
respondent who answered Don't know did not rate anything — the first draft's
"rated" was false for 1,593 rows. The order must be fixed by the assignment;
an order randomised and not recorded cannot be narrated at all.

## A per-respondent fill the deposit does not hold

Ruled by rich, 10 Oct 2026, on IP 9.26's own-place vignette. The screen named the
respondent's own town (a fill from their address, `ff_post_code`), and the deposit
does not contain it. The row keeps the instrument's words on either side and puts
one clause of ours in the fill's place: *"(here the screen named the place where you
live)"*. Three conditions, all required:

- the clause must be true for every row it appears in — 9.26 builds the arm only
  for respondents whose address on record was confirmed (`addrchck` = 1), and the
  comparison arm is restricted the same way so both come from one population;
- it claims no more than the evidence shows — "place", not "town", because nothing
  proves the screen printed a town name rather than a postcode or district;
- `notes` records the clause word-for-word and says it was added.

A fill whose content matters to the outcome and cannot be stated truthfully this way
fails the study instead.

## Attention and recall checks are not outcomes

**Do not build post-stimulus recall or attention checks as outcomes.** "Thinking
back to the policy you were shown, how much of your pay was covered?" is a check
on whether the respondent read the screen, not a measure of how they behave.

They are genuine answers from real people, so excluding them is a judgement
about what this dataset is for, not about data quality. The reason: the answer is
recoverable from the condition text alone, so a model would score highly on them
while learning nothing about behaviour — and any evaluation that included them
would read better than it deserves. A dataset whose headline number is inflated
by comprehension items is worse than a smaller honest one.

Record the exclusion and its row cost in `notes`. `yv2ta` cost 8,092 rows across
its two recipes.

## A source with no stimulus

Some sources measure a response with no manipulation at all — a panel question
asked of everyone, with nothing randomised. CLAUDE.md requires that such a row
"say so explicitly with a consistent sentinel", and until a source needs one
every maker would invent a different spelling. So it is fixed here, before it
is needed:

    condition: "No stimulus was shown; the question was asked of everyone."

One arm, `condition_num: 0`, that exact string, and `factors: {}`. Not an empty
string and not a dash: a reader of the corpus must be able to tell "nothing was
shown" from "something was shown and we failed to record it", and an empty field
cannot carry that difference.

None of the 20 sources built so far needs this — every one has a manipulation.
It is written down because the first one that does will be written by an agent
that has not had this conversation.

## A study with no assignment column

Most instruments record which condition a respondent met in a column. Some do
not: they route people to separate blocks of variables and the only record is
that the blocks a person never saw carry a "not asked" code. `QQM5MC` is the
first here — four conditions as `Q1A/Q2A/Q3A` .. `Q2D/Q3D`, no `Exp_Group`
anywhere in the file, and the authors reconstruct it with a `reshape long`.

Declare `condition.not_asked_code` and a `witness_var` per arm. Three rules go
with it, and none of them is optional:

**Read the routing, never the response.** The witness is the code meaning "this
person was never shown this variable", which is the instrument's own account of
what it asked. It is not "they left it blank" and not "they answered". A file
that cannot tell those apart cannot use this mechanism — check first. `QQM5MC`
codes 9999 "Not Asked" and 9998 "Skipped" separately, which is what makes it
readable.

**A blank witness is a not-asked witness.** An absent cell is no evidence a
person saw a condition, and inventing one from a gap is the error the whole
mechanism exists to avoid.

**A respondent routed to two conditions has none.** Do not pick the first, and
do not pick by any rule — a row carries exactly one condition and we cannot know
which of the two they met, so drop the respondent. Declare how many
(`ambiguous_routing`) and why (`ambiguous_routing_reason`). The melt fails when
the number it finds differs in either direction, so the discard can never grow
quietly and a stale declaration cannot stand. `QQM5MC` has exactly one such
respondent in 3,267, and the published analysis counts them twice.

## Verifying a study SocSci210 does not contain

`mmds crosscheck` has nothing to compare a non-TESS study to, so
`comparable_to_socsci210: false` leaves it with no numeric answer key at all.
Use the published paper's own table instead — and prefer a table to a figure
whenever both carry the same numbers, because a drawn bar resolves to about 0.1
and that is looser than any useful tolerance.

A saturated regression is the best case: when every condition is crossed with
every level of a moderator, the printed coefficients ARE the cell means, and
summing the terms a cell switches on recovers each to the precision printed.
`scripts/verify_QQM5MC.py` is the pattern — one script per study, transcribing
the table as data, reading the BUILT parquet rather than the deposit. Reading
the deposit would prove only that the paper is reproducible; reading the melted
rows proves the condition mapping, the outcome mapping, the response recode and
the persona all survived the melt, which are four things a recipe can get wrong
silently.

Where our number legitimately differs from the published one, assert the
difference rather than widening the tolerance to swallow it. `QQM5MC`'s N is
exactly two below the paper's because we drop a doubly-routed respondent the
authors count twice, so the script checks for `published - 2` and says why.
