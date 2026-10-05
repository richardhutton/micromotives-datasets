# The UKDS End User Licence forbids AI tools, by name

**Read 5 October 2026** from the current EUL — `CD137-EndUserLicence`, version 16.00,
dated 25 February 2026, fetched from ukdataservice.ac.uk. This is the agreement rich
signed at registration; it is UKDS-wide, not per-study, which is why it is not in the
SN 6849 download.

## The two clauses that decide it

**Definition (§4).** Emphasis added:

> **Online Data Tools:** Any software, application, system or platform that operates via
> the internet or a cloud-based service and is used to process, analyse, manipulate or
> generate data and other types of content, **including but not limited to tools that
> employ 'artificial intelligence' (AI) technologies, including generative AI
> technologies**, that are designed to perform human-like cognitive functions such as
> learning, reasoning, problem-solving, understanding natural language, perception and
> generating new or original content.

**Obligation (§5.5).**

> To **abstain from using any Online Data Tools in connection with your use of the Data
> Collection(s)**, unless explicit written permission is granted by the Data Service
> Provider. The Registered User acknowledges that the use of such tools may compromise
> data security and enable data transfer to unauthorised parties in violation of clause 4.

There is no interpretation to do. Generative AI is named in the definition, and the
obligation is to abstain, not to be careful.

## Two more clauses that matter

**§5.4 — derived data is covered too.**

> Not to give access to the Data Collection(s), in whole or in part, **or to any
> Dataset(s) derived from the Data Collection(s) (including synthetic Dataset(s))**,
> except to Registered Users...

So built `(persona, condition, outcome, response)` rows from UKDS are themselves a
derived Dataset and can never be published. That was already the working assumption; it
is now the text.

**§4 — "Data Collection" includes the documentation.**

> **Data Collection:** The Dataset(s), **Documentation**, Metadata, occasionally code...

The questionnaires are Documentation, therefore part of the Data Collection. So the
instrument text is covered by §5.5 exactly as the respondent rows are. There is no
"instrument text only" carve-out of the kind CLAUDE.md permits for TESS.

**§5.13** also obliges us to OFFER FOR DEPOSIT any new Data Collection derived from the
materials, at the conclusion of the research. Worth knowing before building one.

## What this blocks

Everything UKDS, and more than the API calls:

- **Jev / TypeSafe** — `recipe_prep.py` sends question wordings and value labels on every
  run. Forbidden for any UKDS source.
- **Voyage** — already refused by `embed.py`'s `CLEARED` gate, which names UKDS. That gate
  turns out to have been right for a reason stronger than the one written in it.
- **Claude** — and this is the part not to be clever about. §5.5 forbids using Online Data
  Tools *"in connection with your use of the Data Collection(s)"*. It does not say "do not
  upload the data to them". An assistant helping to write a recipe against SN 6849 is a
  generative AI tool used in connection with the use of that Data Collection, on the plain
  words.

  The narrow reading is that the clause's stated rationale is data security and transfer
  to unauthorised parties, so work that transmits nothing is outside the mischief. That
  reading is available but it is not what the clause says: the rationale sentence is
  explanatory ("acknowledges that... may"), and the obligation above it is flat. I would
  not rely on it, and I am not going to pretend the convenient reading is the natural one.

## What it does not block

Nothing already built. The 124,885 CC0 rows are Harvard Dataverse, and the TESS layer is
OSF. Neither is a UKDS Data Collection and neither is touched by this.

## The route through

§5.5 grants the exception itself: *"unless explicit written permission is granted by the
Data Service Provider."* So the answer is to ask, not to guess — and the ask is narrow and
reasonable, because what this project does with the data is exactly what the Innovation
Panel's own methodological-experiments programme exists to support.

Draft at `docs/email_UKDS_permission.md`.

Until that permission is in hand, SN 6849 stays on disk, unread by any tool that reaches
the internet. **No UKDS recipe should be written, by me or by anyone, in the meantime.**
