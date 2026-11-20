# Rich personas from the Innovation Panel: spec

Draft, 22 Oct 2026. Nothing built yet.

## Goal

Test whether knowing a person's life (their "why") improves predicting their
experiment answers (their "what"). The Innovation Panel (SN 6849) lets us do this
with data we already hold: the same people who took part in our 38 IP experiments
also answered the full annual Understanding Society questionnaire.

The question we answer: **on the same held-out people and experiments, does a rich
persona beat a thin one, and by how much?**

## What we have (measured 22 Oct 2026, labels and counts only)

- 17 annual waves (`a`–`q`_indresp_ip), 1,300–3,100 questions each.
- Every participant in all 38 IP experiments links to the annual files through
  `pidp` (via the same `person` hash the builds use): 65,759 person-experiments.
- Median 4 earlier waves per person-experiment. Fewest for the early experiments
  (identity w2, fertility w4/w5, housework w5).
- Rough topic split of a wave's questions: health and wellbeing, work, family and
  life events, money, education, housing; politics and attitudes rotate by wave.

## What a rich persona is

The thin persona stays exactly as it is now (age, sex, region, education,
employment, marital status, ethnicity, …). The rich persona adds a **history
block**: about 30 answers from the person's own earlier annual interviews.

Example shape (illustrative wording, not real data):

```text
Age: 47
Sex: Female
Region: North West
…
From earlier interviews:
- Life satisfaction (2021): Mostly satisfied
- General health (2021): Good
- Finances (2021): Just about getting by
- Hours worked per week (2020): 30
- Cares for someone outside the household (2021): Yes
- Interest in politics (2019): Not very interested
```

Each line carries the year it was asked, because answers age and modules rotate.

## Rules

1. **Earlier waves only.** A history item must come from a wave before the
   experiment wave. Never the same wave, never later.
2. **Most recent earlier answer**, per item, within **5 years** of the experiment.
   Older than that is left out. Not asked is left out. Never imputed.
3. **No near-duplicates of the outcome.** An item that measures the same thing as
   the experiment's outcome is excluded for that experiment (e.g. annual GHQ items
   for the GHQ experiment, annual alcohol questions for the alcohol experiment).
   The exclusion list is per experiment, written down, reviewed.
4. **Words, not codes.** Each answer is rendered through its value label, the same
   as every persona field. Missing codes (negative values) are dropped.
5. **Fixed item list across experiments**, so the model sees one consistent
   format. Only rule 3 removes items.
6. **Thin persona untouched.** The rich block is added; nothing in the current
   persona changes.

## Choosing the ~30 items

- I read the annual questionnaire labels (instrument text only) and propose a
  shortlist covering: wellbeing, health, money, work, family and caring, housing,
  politics and values, social life.
- Priority: items asked in most waves (so most people have a recent answer), and
  items that plausibly bear on the experiment topics.
- rich approves the list. Coverage per item (how many people have an answer within
  5 years) is computed locally as counts.
- No Jev: UKDS material does not go to Jev.

## Data and schema

- New persona field `history`: a list of `{item, year, answer}`, stored as
  structured metadata, rendered as the block above. Empty for every non-IP source.
- Built as **separate rich files** (`ukds_6849_<exp>_rich.parquet`) beside the
  existing ones. Same rows, same ids, same condition, outcome and response; only
  the persona differs. The current files are not touched.
- A build step joins the experiment rows to the annual files by `person`, applies
  rules 1–5, and records per experiment: people with a history, items per person
  (median), items excluded by rule 3.

## Checks

- Checker (different model) confirms: rows identical to the thin files apart from
  the history block; no item from the experiment wave or later; rule 3 exclusions
  applied; no codes or missing values rendered.
- Tests: wave-timing rule, 5-year cut-off, exclusion list, render format. Each
  mutation-tested.
- Licence handling as for all IP work: aggregates only in the chat; data stays on
  the laptop, the private HF repo and the RunPod pod.

## Evaluation

- Use the existing splits unchanged (same seen and unseen studies, same held-out
  people).
- Train once with IP training rows in **both** forms (thin and rich), so the model
  knows both formats.
- Score the IP eval rows twice, thin and rich, with the same model. Report the
  difference per experiment, with the random baseline and resampling ceiling as
  for every other result.
- Also report by history length (1–2 earlier waves vs 5+), to see whether more
  history helps more.

## Steps

1. Shortlist ~30 items with coverage counts → rich approves.
2. Write the rule-3 exclusion list per experiment → rich approves.
3. Build the join and the rich files; checker; tests.
4. Add rich rows to the export (IP training rows in both forms).
5. Train, score thin vs rich, write up.

## Out of scope for now

- Using history in the service: census-sampled respondents have no history. If the
  result is strong, a later step can explore adding history-like attributes to
  respondents conditionally (see app abstractions: Population → Respondent).
- Household-level context (`hhresp`), partner answers, and the youth files.
- SN 6614 (main Understanding Society); this spec uses SN 6849 only.

## Open questions

- 30 items, or a smaller and a larger set to see where the gain levels off?
- 5-year cut-off: right, or tighter for fast-changing items (job, health)?
- Free text answers (if any in the shortlist): leave out.
