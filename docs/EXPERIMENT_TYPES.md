# Experiment types: what the builder must support

Draft, 26 Oct 2026. Written for the experiment builder in melange: which designs
exist, what each one needs from the builder, and what images add. Examples are
recipe ids from our corpus (`docs/EXPERIMENTS.md`).

## The parts every experiment has

Every experiment, whatever its type, is made of the same four parts as a training
row:

| Part | What it is | Builder needs |
|---|---|---|
| **Condition** | what a respondent is shown (text, a table of attributes, an image) | one or more versions, plus an optional "no stimulus" control |
| **Outcome** | the question asked | one or more questions, each with its own answer format |
| **Response** | the answer | answer formats, see below |
| **Assignment** | who sees which condition | random split, fixed counts per condition, how many screens per person |

The type of experiment is mostly a question of **how conditions are made and how
many each person sees**.

## Picking the type in the dialogue

The types differ on five things. The agent can settle the type by finding out
these five, in this order, and should not ask for a type by name (users rarely
know it).

| # | Question for the agent to settle | Answer points to |
|---|---|---|
| 1 | Is anything being compared at all? | no → **9 single condition** |
| 2 | How are the versions made? | written out one by one → **1 A/B**; built from factors → **2 factorial**; slots in one story → **3 vignette**; two described options side by side → **4 conjoint**; drawn from a pool of items → **5 paired comparison** |
| 3 | How many versions does one person see? | one → between-subjects (1, 2, 3); several → **6 within-subject**, or the repeated rounds of 3, 4, 5 |
| 4 | Is the answer about one thing, or a choice between things shown together? | one thing → rating (1, 2, 3, 6); a choice → 4, 5 |
| 5 | Is the difference in what was shown, or in what came before / how the question was asked? | what came before → **7 order/priming**; a sensitive question asked indirectly → **8 list experiment** |

Images do not make a new type. For any type, the agent also asks: **is the thing
shown text, an image, or both?** If an image: the image files, where each came
from and its licence, and a written description of each (see **Images** below).

Words in the request that point to a type:

| The user says | Likely type | Check |
|---|---|---|
| "test these two / three messages", "which headline works" | 1 A/B | is each message rated alone (A/B) or are they compared side by side (5)? |
| "does X matter, and does Y, and together?" | 2 factorial | are X and Y independent factors with levels? |
| "a story about a person where we change their age / name / job" | 3 vignette | one template, slots varied |
| "which candidate / product / policy would people choose", "what drives choice" | 4 conjoint | two options described by the same attributes? |
| "which of these claims / arguments is most convincing", "rank these" | 5 paired comparison or MaxDiff | many items, compared against each other |
| "show each person all the concepts" | 6 within-subject | order matters: randomise it |
| "does asking X first change Y" | 7 order | the condition is a prior question |
| "people won't answer honestly" | 8 list experiment | only if the topic is sensitive |

## Types, simplest first

Each type below: what it is, **how it differs** from its nearest neighbours,
what the **agent must ask** in the dialogue, and examples from our corpus.

### 1. A/B (between-subjects split)

Each person sees **one** version, written out in full. Two or more conditions,
often with a control. Wording tests, framing, message tests, information
provision, anchors.

- **Differs from:** factorial (2): versions here are written one by one, not
  built from factors. Paired comparison (5): here a person never sees the other
  versions, so they rate one thing, not choose between things.
- **Agent asks:** the versions (full text of each); whether there is a control
  (nothing shown, or a neutral version); the outcome questions and their answer
  formats; anything everyone sees before or after.
- **Examples:** DEL climate news (4 arms, no control), information provision
  (3 and 5 arms), Innovation Panel wording and layout splits (2–10 versions).
- **Market-research names:** monadic concept test, message test, **RTB** test
  (which reason to believe is most convincing, each shown to a different group).

### 2. Factorial

Versions are built from **factors**, each with levels, crossed: 2×2, 2×2×2, often
plus a true control. Answers which factor matters and whether they interact.

- **Differs from:** A/B (1): the user gives factors and levels, and the builder
  generates the versions. Vignette (3): factorial pieces are usually whole blocks
  of text added or swapped; a vignette slots short values into one sentence.
  Conjoint (4): one version per person and rated alone, not two options compared.
- **Agent asks:** the factors and their levels; the text for each level; how
  levels combine into one condition (order of blocks); whether all combinations
  are allowed; whether there is a control with none of them.
- **Examples:** EU referendum frames (cultural × economic × political, each
  pro/anti, plus control); Innovation Panel 2×2 (amount × period), 2×5×2 (info ×
  duration × feedback).

### 3. Vignette (fill-in-the-blanks)

One short story with slots (name, age, job, …) filled at random. Usually several
vignettes per person, each rated alone.

- **Differs from:** factorial (2): one template with short values slotted in,
  and often hundreds of combinations. Conjoint (4): one story rated alone, not
  two profiles compared; and a story, not a table.
- **Agent asks:** the template text with slots marked; the values for each slot;
  forbidden combinations (e.g. a name that implies a sex used with the other
  sex); vignettes per person; the rating questions.
- **Examples:** TESS `py9q3_vignette1-3`, `xk9ch_vignette1-2`, `9xw67_vignette`;
  one TESS design has 4 names × 2⁶ = 256 versions, another 480.

### 4. Conjoint (paired profiles)

Two options side by side (candidates, policies, NGOs, products), each described
by the same attributes drawn at random; the person picks one, sometimes also rates
each. Several rounds per person. Answers which attributes drive the choice.

- **Differs from:** vignette (3): two options compared, shown as attributes, not
  one story rated. Paired comparison (5): the options are made up from attributes
  for each screen, not taken whole from a fixed pool.
- **Agent asks:** what is being chosen (the thing both options are); the
  attributes and levels; rounds per person; the choice question ("which would you
  vote for") and any rating questions; attribute order fixed or shuffled;
  impossible combinations to forbid; whether "neither" is allowed.
- **Examples:** Brexit deals (8 attributes, 6 rounds), lodger and BBC conjoints
  (7 attributes, 5 rounds), vaccine priority (5 attributes, 8 rounds), i-voting
  (10 attributes), DEL NGO donate/petition (4 attributes, 3 screens).

### 5. Paired comparison and MaxDiff (pick from a pool)

Items from a fixed pool (claims, arguments, images) shown together; the person
picks the better one (pairs), or best and worst (MaxDiff, sets of 4–5). Several
screens per person. Answers how the items rank against each other.

- **Differs from:** conjoint (4): items are whole and fixed, not built from
  attributes. A/B (1): items are compared against each other, not rated alone.
- **Agent asks:** the item pool (full text or image of each); items per screen
  (2 = paired, 4–5 = MaxDiff); screens per person; the question ("which is more
  convincing"); whether "about the same" or "neither" is allowed.
- **Examples:** political arguments from Hansard (2 of 336), why Ukraine matters
  (2 of 14 statements, 5 screens). No MaxDiff in our corpus yet.
- **TURF** is an analysis run on MaxDiff or rating results (which set of items
  reaches the most different people), not a separate type. Nothing extra in the
  dialogue.

### 6. Within-subject (several versions per person)

The same person sees several versions in turn and rates each alone.

- **Differs from:** A/B (1): same versions, but everyone sees all (or several),
  so earlier ones can colour later ones; order must be randomised and recorded.
  Paired comparison (5): shown one after another and rated alone, not side by
  side.
- **Agent asks:** the versions; whether everyone sees all of them; random order
  or fixed; whether each is rated on the same questions.
- **Examples:** DEL goals (3 goals × 3 screens, 12 orders).
- **Market-research name:** sequential monadic.

### 7. Order / priming

The condition is **what was asked or shown before**: block A before the outcome,
or not at all. The outcome text is the same for everyone.

- **Differs from:** A/B (1): the outcome and its wording do not change; only what
  came earlier does. The model input must say what came earlier.
- **Agent asks:** the earlier block (questions or text); the outcome; whether the
  control sees the block later or never.
- **Examples:** Innovation Panel order experiments (EQ-5D, friends, housework
  hours).

### 8. List experiment (item count)

For sensitive questions. Control sees 3 statements, treatment the same 3 plus the
sensitive one; people say **how many** they agree with, never which.

- **Differs from:** every other type: the answer is a count, and the result is
  only readable for the group (difference in average count), never for one person.
- **Agent asks:** the sensitive statement; the 3–4 neutral statements; confirm the
  topic is sensitive enough to be worth it.
- **Examples:** Innovation Panel item-count experiments.

### 9. Single condition (no experiment)

Everyone sees the same thing; only the persona varies. A plain survey question.

- **Differs from:** everything above: nothing is randomised, so it measures how
  answers differ between people, not the effect of a change.
- **Agent asks:** the question and answer format; suggest a control or second
  version if the user is really asking "does X change minds".
- **Builder:** type 1 with one condition. Useful for baselines.

## Answer formats

| Format | Examples in corpus |
|---|---|
| Scale with labelled points (4, 5, 7 points) | agree–disagree, harm, increase/decrease |
| Numeric scale (0–10, 0–100 slider) | satisfaction, anchoring |
| Yes / no | consent, donate yes/no |
| Pick one, unordered (nominal) | party choice, 3-option with opt-out |
| Forced choice between two profiles or items | every conjoint, paired comparison |
| Number | hours per week, count in a list experiment |
| Amount, including split a total | £1,000 split three ways (sums to the total) |

Every format needs: the labels as shown, what counts as a non-answer
("Don't know", dropped), and the valid range.

## Images

None of our 110 experiments uses images yet. The candidates (`docs/IMAGE_CANDIDATES.md`,
requests sent per `docs/image_emails/`) come in four shapes, and all four are the
types above with an image as the condition:

| Shape | Same as type | Candidates |
|---|---|---|
| One image (or image + text) per person, rate it | 1. A/B | warning labels IMG01/02 (1 of 21 / 18), icon arrays IMG05, front-of-pack IMG14 |
| Several random images per person, rate each | 6. within-subject | food photos IMG04, charity photos IMG06, political ads IMG09 (4 per person) |
| Two images, pick one | 5. paired comparison / MaxDiff | needs/deserves help IMG07, climate images IMG16, architecture IMG17 |
| Pick one product from a shelf of images | 4/5, with more than two options | warning labels study 2 IMG03 |

What this means for the builder now:

1. **A condition is not only text.** Give each condition a list of parts: text,
   image, or table of attributes. Build that in now even if only text is used,
   so images are not a rebuild later.
2. **An image is stored as an asset** with an id, the file, where it came from and
   its licence, plus a **written description**. Factorial images (e.g. 2×2 shop
   displays IMG12) also keep their factor levels.
3. **Pools and draws.** Several image shapes draw k items from a pool per person;
   that is the same machinery as paired comparison and MaxDiff, so one "pool +
   draw" feature serves all three.
4. **Choice from more than two.** Allow a choice question over N conditions shown
   together, not only pairs.

### Open decision: how the model sees an image

The model we are about to train is text-only. For image experiments there are
two routes:

- **A vision model** that takes the image itself (needs a multimodal base model).
- **A text description** of the image in the condition. Simpler, but the
  description is written by us, which is exactly the part nothing downstream can
  check (CLAUDE.md, row contract), so it would need the same checker treatment as
  every condition.

Not decided. Either way the builder should store both the image and a description.

## Summary: what to support

| Priority | Feature |
|---|---|
| Now | A/B with control; multiple outcomes; all answer formats above |
| Now | Factors and levels → generated combinations (factorial, vignette) |
| Now | Conjoint: attributes, rounds per person, choice + rating questions |
| Now | Conditions as parts (text / image / attribute table), even if only text is used |
| Soon | Pools and draws (paired comparison, MaxDiff, image sets); screens per person; order recorded |
| Soon | Image assets with source, licence and description; choice over N |
| Later | Order/priming and list experiments (rare in commercial use) |
