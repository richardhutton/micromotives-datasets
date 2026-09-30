# SocSci-UK — data overview & predict schema (from the actual files)

Built by opening the real respondent files (not from abstracts). Every field
below was seen in the data.

**Provenance.** Accessed 2026-09-21 via the Harvard Dataverse API
(`/api/datasets/:persistentId/`, `/api/access/datafile/{id}`) and per-file DDI
metadata (`/api/access/datafile/{id}/metadata/ddi`) for category labels; OSF via
`api.osf.io/v2`. Full DOIs/URLs and licences in §5 (References). Row-count and
column figures are read from the downloaded files; where a field is marked
"needs pull" the respondent file exceeded the download cap and was not opened.

## 1. The schema we predict from

One canonical row, same shape as SocSci210 (its real columns in brackets):

```
persona   : the demographic block (below), rendered as text. Missing fields omitted.   [demographic]
stimulus  : the text the respondent read = condition scenario + outcome question.       [stimuli]
condition : which randomised arm — an index, not text; its wording lives in `stimulus`. [condition_num]
question  : which outcome asked — an index, not text; its wording lives in `stimulus`.  [task_num]
response  : the answer as ONE integer = a single token (see build rules).               [response]
attributes: for conjoint rows, the level each attribute took (structured metadata).
source    : which dataset the row came from.                                            [study_id]
```

Note: in SocSci210 the condition and the outcome question are **not** separate
text fields — both are rendered into the single `stimuli` string, and each keeps
an integer index (`condition_num`, `task_num`) used only to build the
unseen-condition / unseen-outcome splits. Our `condition` and `question` columns
are those indices; the readable content is in `stimulus`.

### The parts we need (aligning with SocSci210)

Checked against the actual dataset (`socratesft/SocSci210`, HF dataset viewer,
2026-09-21). A row has **10 columns**, but only three carry content — the rest
are integer indices and bookkeeping:

| SocSci210 column | Type | Role |
|---|---|---|
| `demographic` | dict (~16 fields) | **Persona (P)** |
| `stimuli` | string | the rendered text the respondent read — **contains both the condition scenario and the outcome question** |
| `response` | int | **Response (r)** — one integer |
| `condition_num` | int | arm **index** (its text lives inside `stimuli`) |
| `task_num` | int | outcome-question **index** (its text lives inside `stimuli`) |
| `prompt` | string | `demographic` + `stimuli`, templated |
| `reasoning` | string | oracle trace (SFT+reasoning only) |
| `sample_id`, `participant`, `study_id` | — | bookkeeping |

So the paper's tuple `(P, c, o, r)` maps onto the columns like this — **the
condition and the outcome question are not separate content fields; both are
rendered into one `stimuli` string, and each carries a separate integer index**:

```
paper's  (P,           c,             o,          r)
column:   demographic  condition_num  task_num    response
                       └──── both rendered into ────┘
                                 stimuli (text)
```

**Four content parts we need per respondent** — persona, condition, outcome
question, response (the `(P, c, o, r)` tuple; Fig. 1 and Fig. 3 label all four
as distinct slots):

| Part | Have it? | Where it lives | SocSci210 column |
|---|---|---|---|
| **1. Persona (P)** — the demographic block | **Yes** | data file (see spine below) | `demographic` |
| **2. Condition (c)** — the treatment/scenario they read (the stimulus) | **Yes, but assembled per study** | conjoints: render from attribute columns · Persuasion: a companion file of argument texts · DEL: the questionnaire (`Survey.docx`) · video/image (Cyber): a description must be written | `stimuli` (text) + `condition_num` (index) |
| **3. Outcome question (o)** — what they were asked | **Yes** | questionnaire / codebook (often also in the prompt) | `stimuli` (text) + `task_num` (index) |
| **4. Response (r)** — the answer as one integer | **Yes** | data file (the outcome column) | `response` |

**Why the condition is the whole point — this is not just a survey.** Strip the
condition (Part 2) and all you have is a poll: *"people like this answer X."* Keep
it and you have something a decision-maker can act on: *"people like this answer X
when shown A, and Y when shown B."* That **gap between A and B, for the same
persona, is the treatment effect** — and it is the thing anyone deciding whether
to *act* actually wants to know. A poll tells you where opinion sits today; the
condition tells you how opinion *moves* when you change what people are shown.
That is why we carry the arm per respondent and never collapse it away: without
it the model can learn the response distribution but can never estimate how a
manipulation *shifts* it — which is the one question the engine exists to answer.
(This is also why Build Rule 2 keeps conjoint attributes as structured metadata:
you can only score how much each attribute moved the choice if you kept the arm.)

**Storage detail — c and o share one string, but stay distinct parts.**
SocSci210 concatenates the condition text and the outcome-question text into the
single `stimuli` string (and the assembled `prompt`), keeping `condition_num`
and `task_num` as integer indices — used to build the held-out
**unseen-condition** and **unseen-outcome** generalisation splits. They don't get
their own text columns, but they are two of the four parts, not one. In our files
the arm arrives as exactly such a code; the *wording* it maps to sits in the data
columns, a companion file, or the questionnaire depending on the study. **The
work is joining that arm code → its text, per study.**

**Not yet proven:** the arm→text join has not been done end-to-end on any single
dataset. Next step — build one complete row (`demographic` + `stimuli` +
`condition_num`/`task_num` + `response`) from one study.

**Persona = the common demographic spine** (richness varies by source):

| Canonical field | Coverage across UK sets |
|---|---|
| gender | **all** |
| education | **all** |
| income | **all** |
| age | most |
| social grade | most (politics) |
| party / past vote | most (politics) |
| EU-referendum vote | most (politics) |
| ethnicity | ~half |
| region (GOR) | some |
| marital, work, religion, newspaper | some (optional extras) |

So the **hard common core** is `gender · education · income`; the **strong UK-politics core** adds `age · social grade · party · EU vote`. That is the persona the model predicts from. Where a source lacks a field, the row just omits that line.

### How the persona compares to SocSci210

SocSci210's persona is a fixed 16-field block (with nulls where a study didn't
collect a field). Field-by-field against our UK spine:

| SocSci210 field | In our UK spine? |
|---|---|
| age, gender, education, income | ✅ |
| ethnicity, marital, employment (as work), party, location (as region) | ✅ where present |
| ideology | ~ (left–right in some studies, not in the spine) |
| household size | ❌ |
| housing type, housing ownership, metro status, internet access, phone service | ❌ (US-only filler) |

**We have, SocSci210 doesn't:** social grade (UK class), EU-referendum vote
(Brexit), newspaper readership (media diet), religion.

**SocSci210 has, we don't:** household size (a real gap), plus US-only filler
(internet/phone/metro/housing) that carries little predictive value.

**Verdict:** comparable, arguably stronger on signal — we cover every useful
SocSci210 demographic and add four UK political/class/media fields; the main
genuine gap is household size. Both are variable-length in practice (SocSci210
populates ~9–15 of its 16 fields per row), so our variable persona matches its
pattern rather than deviating. The real coverage-per-row only settles after the
merge.

### Two build rules

**1. The response is always one integer — a single token.**
- Forced choice → 1 or 2.
- Rating → its scale value (1–7, 0–100, etc.).
- Persuasion (two arguments, pick the more persuasive) → 1 or 2.

Why: in SFT the loss lands on a single answer token, so the model only learns
the response distribution if the target is one token. The stimulus text can be
as long as it likes; the target must stay one token.

**2. Conjoint rows keep their attributes as structured metadata — not just in the prompt.**
- The prompt writes out both profiles in full (as text).
- The row also records which level each attribute took that row.

Why: without the structured attributes you can't score, in a held-out study,
how much each attribute moved the choice. That score is the treatment-effect
result — the thing the engine is for. So capture the attributes when you build
the rows.

## 2. What's actually in each dataset (verified)

| # | Dataset | Rows (file) | Persona fields present | Stimulus form | Response form |
|---|---|---|---|---|---|
| 1 | Persuasion | 3,317 | age, gender, education, income, social grade, ethnicity, party, EU vote, marital | **336 text arguments** | MaxDiff — which argument most persuasive |
| 2 | Brexit conjoint | 3,293 | age, gender, education, region, income, social grade, party, EU vote, work, religion, newspaper | conjoint negotiation-outcome profiles | forced choice between packages |
| 3 | Divided by the Vote | 1,635 | age, gender, education, region, income, social grade, party, EU vote, work, newspaper | lodger / BBC vignettes | affective-polarisation ratings |
| 4 | For/Against Brexit | 19,986 obs | (needs latin-1 re-read) | pro/anti Brexit messages | attitude scale, 2 waves |
| 6 | Pricing Immigration | 3,636 | age, gender, education, income, social grade, ethnicity, party, EU vote, work | conjoint with **prices** attached | choice |
| 8 | i-voting | 1,200 (×tasks) | gender, education, income, ethnicity, party, EU vote | conjoint (voting-system attributes) | forced choice (`selected`/`choice`/`probselected`) |
| 9 | Cyber terrorism | 2,028 (US/UK/IL) | gender, education, income, marital, work, religion | **TV news report (video → needs text description)** | support-for-retaliation scale |
| 10 | Vaccine allocation (13-ctry) | — | respondent file >80MB — **targeted pull needed**; verify UK | conjoint | 8 forced choices each |
| 11 | Anti-immigrant (22-ctry) | 45,402 | age, gender, income, marital (**thin**) | conjoint | choice |
| 12–14 | Many Labs 1/2, PSA | — | **OSF zips — extraction pending** | various | various |

All Dataverse sets above are **CC0** (public domain).

## 3. The honest reality

- **The persona is unifiable.** The common spine (`gender/education/income` everywhere; `age/social-grade/party/EU-vote` across the politics sets) means these merge into one persona schema. Names differ per source (`profile_gender` vs `sex`) — a per-source crosswalk fixes that.
- **The stimulus and response FORMATS differ per study** — text argument vs conjoint profile vs vignette vs news report; MaxDiff vs forced choice vs rating scale. These don't unify into one column; each renders to text in the prompt, and the response is the answer in that study's format.
- **Category coding still has to be harmonised** — income bands, education levels differ per study. Record raw categories, map to common bands. This is the remaining crosswalk work.

## 4. Gaps to close

1. Re-read #4 with latin-1 encoding.
2. Targeted pull of #10's respondent file (>80MB) and confirm UK inclusion.
3. Extract the OSF zips (#12–14); expect thinner, non-YouGov demographics.
4. Build the per-source crosswalk: column names + category codes → canonical persona.

## 5. Sources & references

Numbers match the dataset table in §2. All Harvard Dataverse deposits verified
CC0 1.0 (public domain) via the API on 2026-09-21.

| # | Dataset / authors | DOI / URL | Repository · licence |
|---|---|---|---|
| — | **SocSci210** (Kolluri, Wu, Park, Bernstein 2025) — reference format | https://huggingface.co/datasets/socratesft/SocSci210 · paper arXiv:2509.05830 | Hugging Face |
| 1 | The Variable Persuasiveness of Political Rhetoric (Blumenau & Lauderdale) | doi:10.7910/DVN/POMIFD · https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/POMIFD | Harvard Dataverse · CC0 |
| 2 | Policy preferences & legitimacy after referendums: Brexit conjoint (Hobolt, Leeper, Tilley) | doi:10.7910/DVN/EFXNLX | Harvard Dataverse · CC0 |
| 3 | Divided by the Vote (Hobolt, Leeper, Tilley) | doi:10.7910/DVN/35M5CV | Harvard Dataverse · CC0 |
| 4 | For and Against Brexit: campaign-effects experiment | doi:10.7910/DVN/PZB01G | Harvard Dataverse · CC0 |
| 6 | Pricing Immigration (Hix, Leeper, Kaufmann) | doi:10.7910/DVN/6MRVOM | Harvard Dataverse · CC0 |
| 8 | Support for digitising the ballot box: i-voting conjoint | doi:10.7910/DVN/RJTVG8 | Harvard Dataverse · CC0 |
| 9 | Cyber Terrorism and Public Support for Retaliation | doi:10.7910/DVN/SACJHE | Harvard Dataverse · CC0 · video stimuli |
| 10 | COVID-19 vaccine allocation, 13 countries (CANDOUR, Duch et al.) | doi:10.7910/DVN/PMV0TG | Harvard Dataverse · CC0 · verify UK |
| 11 | Geo-Political Rivalry & Anti-Immigrant Sentiment, 22 countries | doi:10.7910/DVN/ZZYSIZ | Harvard Dataverse · CC0 · verify UK |
| 12 | Many Labs 1 | https://osf.io/wx7ck/ | OSF · CC0 |
| 13 | Many Labs 2 | https://osf.io/8cd4r/ | OSF |
| 14 | Psychological Science Accelerator COVID-19 (data paper: Nature Sci Data, s41597-022-01811-7) | https://osf.io/gvw56/ · https://osf.io/s4hj2/ | OSF |

Not yet verified / pending (from the candidate list): #5 Attitudes Towards
Brexit 2017–2020 — https://reshare.ukdataservice.ac.uk/854869/ (UK Data Service
login required); #7 Measuring Subgroup Preferences (doi:10.7910/DVN/ARHZU4,
likely reuses #2). BES Internet Panel W1–31 — UK Data Service SN 8202,
doi:10.5255/UKDA-SN-8202-4 (local copy deleted; re-download to verify).
