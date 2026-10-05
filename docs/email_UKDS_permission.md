# Draft email — UKDS permission request under EUL clause 5.5

**Status:** draft, not sent. For rich to send, edit or discard.

**Revised 5 Oct 2026.** The first draft spent paragraphs reassuring UKDS about
redistribution. rich is not redistributing anything, so clause 5.4 is satisfied
automatically and saying so at length only invites them to wonder why it came up. The
whole request is now about **one clause**: 5.5, the Online Data Tools prohibition. That is
the only thing standing between him and the data he has already downloaded.

**To:** UK Data Service user support (`support@ukdataservice.ac.uk`, or the contact form)
**Subject:** Request for written permission under EUL clause 5.5 — Online Data Tools, SN 6849

---

Dear UK Data Service,

I am a registered user, and clause 5.5 of the End User Licence Agreement (CD137, v16.00)
asks me to abstain from using Online Data Tools in connection with a Data Collection
unless I have explicit written permission. I am writing to request that permission.

**The data:** SN 6849, *Understanding Society: Innovation Panel, Waves 1–17*, downloaded
under my EUL registration.

**What I want to do.** I am building a dataset for my own research into how accurately
language models predict human survey responses, pairing a respondent's demographics with
the question they were asked and the answer they gave. The Innovation Panel suits this
because it retains the randomisation variables that most UK panel releases drop.

**What I am asking permission for, specifically:** to use an AI coding assistant locally
while writing the extraction code — reading variable names and labels, and mapping
allocation variables to the matching questionnaire wordings. **The data would stay on my
own machine and nothing from the Data Collection would be transmitted anywhere.**

I read clause 5.5 as covering this on its plain wording even though nothing is
transferred, which is why I am asking rather than assuming.

**What I am not asking for**, so that this is easy to answer:

- I am not asking to send any part of the Data Collection — including questionnaire text
  or variable labels — to any third-party or hosted service.
- I am not asking to redistribute anything. Nothing derived from the data would be
  published or shared with anyone.

If the answer is no, that is a clear answer and I will not use the data.

I would also welcome a steer on whether this should go through a different route — an
amendment to my Project Information, or a request to the depositor (ISER) rather than to
the Service.

With thanks,

rich hutton
rich.hutton@googlemail.com
UKDS registered user

---

## Notes for rich, not for sending

**This is now a single, narrow ask**, which is the version most likely to get a yes. The
earlier draft offered them three things to think about, including sending instrument text
to a third-party model. Cutting that is not just presentational — it is a commitment:
`recipe_prep.py` must not call Jev for any UKDS source, and I would build that lockout
before touching the data rather than relying on remembering.

**Why ask at all.** Clause 5.5 does not say "do not transmit". It says abstain from
*using* such tools *in connection with* your use of the Data Collection. The sentence
after it mentions data transfer, but that is explanatory, not limiting. Asking costs an
email; being wrong costs the registration.

**Expect this to be a known question.** Version 16.00 is dated 25 February 2026 and the AI
wording reads as a recent addition, so they will have a position and may already have
published guidance.

**If they say no:** the Innovation Panel, the BES Internet Panel and the three
discrete-choice sets all go together — same EUL, same clause. Worth knowing before
investing further in the UKDS plan.
