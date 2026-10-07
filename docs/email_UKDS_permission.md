# Draft email — UKDS permission request under EUL clause 5.5

**Status:** draft, not sent. For rich to send, edit or discard.

**Cut down 7 Oct 2026** on rich's instruction: a person on a support desk has to
read this. The previous version ran to about 140 lines and explained itself
three times. This one is one screen. What survived the cut is the worked example
of a single request, because showing them the actual text is worth more than any
amount of describing it.

**To:** UK Data Service user support (`support@ukdataservice.ac.uk`, or the contact form)
**Subject:** Request for written permission under EUL clause 5.5 — SN 6849

---

Dear UK Data Service,

I am a registered user, and clause 5.5 of the End User Licence (CD137, v16.00)
asks me to abstain from using Online Data Tools in connection with a Data
Collection without explicit written permission. I am writing to request that
permission.

**The data:** SN 6849, *Understanding Society: Innovation Panel, Waves 1–17*,
downloaded under my registration.

**What I want to do.** Take one respondent's own answers, strip their
identifiers, delete one of their answers, and send the rest to a hosted language
model to see whether it can predict the answer I deleted. I am measuring how
accurately language models predict individual survey responses — the UK
equivalent of Park et al., *"LLM Agents Grounded in Self-Reports"*, done on the
US General Social Survey. The Innovation Panel suits it because it follows the
same people for up to seventeen years.

I am not modelling the population, producing estimates about any group, or
trying to identify anyone. The output is a single percentage: how often the
prediction was right.

**Exactly what would be sent.** One request per respondent, roughly 6,500
characters, in this shape. The example below uses an invented person so that this
email carries nothing from your Data Collection — **I will send you a real one
before I make any request, so you can approve the actual text.**

```
You are this person, answering a survey in 2024. Answer as they would.

ABOUT YOU
Age: 54   Sex: Female   Region: [one of 12]   Employment: [one value]
Education: [one value]  Marital status: [one value]

WHAT YOU HAVE TOLD THIS SURVEY OVER THE YEARS
- [question wording] [their answer] [2011, 2013, 2015]
  ... typically 200-400 lines, every one this person's own answer

THE QUESTION, ASKED IN 2024
[one question wording, from your questionnaire]

OPTIONS
  1. [option]  2. [option]  3. [option]

Answer with the number of the option only.
```

The reply is a single digit. Nothing else is sent and nothing else comes back.
No file, no table, no bulk transfer, and nothing about a respondent that they
did not themselves provide.

**Why a local model will not do.** I assumed one would and built it that way
first. On my own machine `qwen3:8b` scores 20.0% where random guessing scores
19.3% — it is at chance. A hosted model on identical input reaches 44% of the
maximum achievable. I measured that on synthetic data I generated myself, with
no material from your Data Collection in it, so that I could establish this
before asking you for anything. Without this permission the work is not slower;
it is not possible.

**What I commit to:**

- `pidp` and all household identifiers are replaced by a one-way hash and never
  transmitted.
- **The data would not be used to train any model.** My provider (Anthropic)
  does not train on API inputs unless the customer opts in, and I have not. I
  can forward their terms, and their retention period for abuse monitoring, if
  that would help you assess it.
- One respondent per request. Nothing in bulk, no files uploaded.
- Nothing published or shared. No derived data leaves my machine.

**What I cannot promise:** once a request reaches a third-party provider I no
longer control it beyond their contractual terms. I understand that may be the
whole answer.

**A second, smaller question.** Does clause 5.5 permit me to use an AI coding
assistant running locally while writing the extraction code — reading variable
names and labels — with nothing transmitted anywhere? I read the clause as
covering it even though no data moves, which is why I am asking.

If either answer is no, I will work within it. I would also welcome a steer if
this belongs on another route — a Project Information amendment, Secure Lab, or
a request to ISER rather than to the Service.

With thanks,

rich hutton
rich.hutton@googlemail.com
UKDS registered user

---

## Notes for rich, not for sending

**One thing to stand behind before you send:** "Nothing published or shared."
True today, and it is what makes the rest credible. If SocSci-UK's plan ever
changes on that, this email becomes a problem.

**Training vs retention — these are two different things, and the email now says
only the one that is true.** rich confirmed 7 Oct that Anthropic does not train
on API data without the customer opting in, and that he has not opted in. So
no-training is a fact and is stated as one.

An earlier draft also promised to "seek zero retention". That has been removed.
Zero data retention is a separate contractual arrangement, not the default, and
is generally not available on a standard account — so it was a safeguard that
might not have been deliverable, which is worse than one never claimed. Standard
API requests are retained for a limited period for abuse monitoring. The email
now offers to forward the provider's terms *including* that retention period,
which puts the actual number in front of the people whose job it is to judge it,
rather than having me characterise it.

**If they come back asking for zero retention specifically**, that is a
reasonable thing for them to want and worth pricing: it is an enterprise
arrangement. Better to have them ask for it than to have promised it.

**Why the ask got bigger.** The 5 Oct draft asked only to use a local coding
assistant and promised nothing would go to a hosted service. Narrow asks get
granted — but that one would have granted permission to do something that cannot
answer the question. Today's numbers (`scripts/synthetic_probe.py`, two runs of
40 held-out questions, 40 of 40 answered each) are what changed it.

**The evidence is the argument.** "This would be easier" gets declined. "I
tested the alternative on synthetic data specifically so I would not have to ask
you first, and it performs at chance" is a different proposition.

**Check their website first.** EUL v16.00 is dated 25 February 2026 and the AI
wording reads as a recent addition, so they likely have a published position.

**If they say no**, it covers the Innovation Panel, the BES Internet Panel and
the three discrete-choice sets together — same licence, same clause. What is left:
fine-tuning a local model on the dataset being built (different from prompting
one, and may clear a bar an 8B cannot clear by prompt); the open and CC0 layers,
where a hosted model can be used freely; and hardware, which buys one step up in
model size and on today's numbers will not close a 44-point gap.

**Until an answer arrives, nothing changes.** `jev.RESTRICTED` still refuses
`source="ukds"`, `data/raw`, `data/profiles` and `data/processed/*.parquet` stay
gitignored, and no UKDS-derived material has left this machine.
