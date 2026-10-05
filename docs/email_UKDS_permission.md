# Draft email — UKDS permission request under EUL clause 5.5

**Status:** draft, not sent. For rich to send, edit or discard.

**To:** UK Data Service user support (`support@ukdataservice.ac.uk`, or the contact form)
**Subject:** Request for written permission under EUL clause 5.5 — Online Data Tools, SN 6849

---

Dear UK Data Service,

I am a registered user and I am writing to request explicit written permission under
clause 5.5 of the End User Licence Agreement (CD137, v16.00), which requires me to
abstain from using Online Data Tools in connection with my use of a Data Collection
unless such permission is granted.

**The data:** SN 6849, *Understanding Society: Innovation Panel, Waves 1–17*, downloaded
under my EUL registration.

**What I want to do.** I am building a research dataset for evaluating how accurately
large language models predict human survey responses. Each row pairs a respondent's
demographic profile with the exact stimulus they were shown and the answer they gave.
The Innovation Panel is uniquely suited to this because it retains the randomisation
variables, which most UK panel releases do not.

**Where an AI tool would be involved.** I want to be precise rather than ask for a
blanket permission:

1. **Locally, with no transmission.** Using an AI coding assistant to help write the
   extraction code — reading variable names and labels, mapping allocation variables to
   questionnaire wordings. The data stay on my machine; nothing from the Data Collection
   is sent anywhere. I read clause 5.5 as covering this on its plain wording even though
   nothing is transferred, which is why I am asking rather than assuming.

2. **Transmitting instrument text only, if permitted.** My pipeline can send *question
   wordings and variable labels* — never respondent records — to a third-party language
   model to help classify which variable records a randomised allocation. I am happy to
   disable this entirely for SN 6849 and do that step by hand. I mention it only so the
   request is complete.

3. **Model evaluation.** The built rows would be used to score model predictions. If that
   scoring were run against a hosted model, respondent rows would be transmitted. **I am
   not asking for permission for this**, and would run any such evaluation against locally
   hosted models unless you tell me otherwise.

**What I am not asking for.** No redistribution. I understand clause 5.4 covers derived
Datasets including synthetic ones, so nothing derived from SN 6849 would be published or
shared with anyone who is not a Registered User. I am also aware of clause 5.13 and would
expect to offer any derived Data Collection for deposit.

If the answer is that (1) alone is permissible and (2) and (3) are not, that would be
entirely workable and I would proceed on that basis. If it is simpler for you to say no,
that is a clear answer and I will not use the data.

I would also welcome a steer on whether this needs to go through a different route — an
amendment to my Project Information, or a request to the depositor (ISER) rather than to
the Service.

With thanks,

rich hutton
rich.hutton@googlemail.com
UKDS registered user

---

## Notes for rich, not for sending

**Why ask at all, rather than just not transmitting anything.** Because clause 5.5 does
not say "do not transmit". It says abstain from *using* such tools *in connection with*
your use of the Data Collection. The rationale sentence that follows mentions data
transfer, but it is explanatory, not limiting. Asking costs an email; being wrong costs
the registration and any work built on it.

**The three-part split is deliberate.** It makes it easy for them to grant the narrow
thing (local assistance, no transmission) without having to think about the hard thing
(sending respondent data to a hosted model). A single vague "can I use AI with your data"
invites a single vague no.

**Expect this to be a known question.** The clause is new — version 16.00 is dated
25 February 2026, and the AI language reads as a recent addition. UKDS will have a
position on it and may already have published guidance.

**If they say no:** the Innovation Panel is off the table and so is the BES Internet Panel
and the three discrete-choice sets, since all four are UKDS safeguarded under the same
EUL. That would leave the CC0 Harvard layer as the whole project, and make POMIFD's
licence and any further Dataverse search considerably more important. Worth knowing that
before investing more in the UKDS plan.
