# Draft email — UKDS permission request under EUL clause 5.5

**Status:** draft, not sent. For rich to send, edit or discard.

**Rewritten 7 Oct 2026, and the ask has changed.** The 5 Oct draft asked only for
permission to use a LOCAL AI coding assistant while writing extraction code, and
said explicitly that nothing would be sent to a hosted service. That was the
version most likely to get a yes, and it is no longer the version that helps:
measurements taken today show the research question cannot be answered on local
hardware at all. So this asks for the thing actually needed — sending a
pseudonymised subset of respondent data to a hosted model for inference — and
puts the evidence in the email, because without it the request reads as
convenience rather than feasibility.

The narrow ask is kept as a second, smaller question in the same email. Same
clause, same reviewer, and it is still unanswered.

**To:** UK Data Service user support (`support@ukdataservice.ac.uk`, or the contact form)
**Subject:** Request for written permission under EUL clause 5.5 — SN 6849

---

Dear UK Data Service,

I am a registered user. Clause 5.5 of the End User Licence Agreement (CD137,
v16.00) asks me to abstain from using Online Data Tools in connection with a
Data Collection unless I have explicit written permission, so I am writing to
request that permission for one specific use.

**The data:** SN 6849, *Understanding Society: Innovation Panel, Waves 1–17*,
downloaded under my EUL registration.

**The request, in one sentence:** permission to send one respondent's own
answers at a time, with their identifiers removed, to a hosted language model,
in order to measure how accurately it predicts an answer of theirs that I have
withheld from it.

The rest of this email is what that means in practice, why a model running on my
own machine will not do, and what I can and cannot promise about it.

## What I am trying to work out

One question: **if you know what a person has told a survey about themselves
over many years, can a language model predict how they will answer a question
they have not been asked yet?**

That is it. I am not modelling the population, not producing estimates about any
group, and not trying to identify anybody. The unit is one person predicting one
of their own answers, and the output is a percentage — how often the prediction
was right. This replicates and extends, on UK data, Park et al., *"LLM Agents
Grounded in Self-Reports Enable General-Purpose Simulation of Individuals"*,
which did the equivalent on the US General Social Survey.

The Innovation Panel suits it uniquely well because it follows the same people
for up to seventeen years, so each person has a long record of their own
answers, and because it keeps the randomisation variables most UK panel releases
drop.

## What I build from your data, and what I throw away

For each respondent I assemble one plain-text record from their own answers:
their demographics, then their answers to attitude, wellbeing, politics, trust
and health questions, each with the year attached. Nothing is added, nothing is
imputed, and no two respondents are combined. **It is one person's own answers,
reorganised and nothing else.**

I then delete one question from that record, and ask the model to predict the
answer I deleted. The deleted answer is the thing being measured, so it is
never sent.

Thrown away before anything else happens: `pidp` and every household
identifier, which are replaced by a one-way hash; the fed-forward (`ff_`)
columns, because they repeat the previous wave's answer; and unticked boxes from
condition checklists, which are the absence of an answer rather than one.

## Exactly what would be transmitted

One request per respondent per question. Below is the complete shape — this
example uses an invented person, so that this email contains no material from
your Data Collection. **I will gladly send you a real one before I make any
request, so you can see the actual text rather than my description of it.**

```
You are this person, answering a survey in 2024. Answer as they
would, not as you think they should.

ABOUT YOU
Age: 54        Sex: Female        Region: [one of the 12 GOR values]
Employment: [one value]           Education: [one value]
Marital status: [one value]

WHAT YOU HAVE TOLD THIS SURVEY OVER THE YEARS
- [question wording] [answer] [2011, 2013, 2015]
- [question wording] [answer] [2012] / [a different answer] [2018]
  ... typically 200-400 lines, all of them this person's own answers

THE QUESTION, ASKED IN 2024
[the wording of one question, taken from your questionnaire PDF]

OPTIONS
  1. [option] 2. [option] 3. [option]

Answer with the number of the option only.
```

The reply is a single digit. I record whether it matched the answer the person
actually gave, and nothing else.

So what crosses the boundary is: **one person's demographics, that person's own
survey answers, and the wording of the questions.** Roughly 6,500 characters. No
file, no table, no bulk transfer, no weights, and no part of the Data Collection
that this person did not themselves provide.

**Why a local model will not do.** I assumed it would, built the pipeline that
way, and tested it. Running `qwen3:8b` on my own machine, the model scores 20.0%
exact agreement on a task where random guessing scores 19.3% — it is at chance.
A hosted frontier model given the identical input scores 32.5%, which is 44% of
the way to the theoretical maximum of 48.1%. I measured this on synthetic data I
generated myself, containing no material from the Data Collection, precisely so
that I could establish this before asking you for anything. Locally runnable
models cannot perform the task, so without this permission the research is not
slower — it is not possible.

**The safeguards I can commit to:**

- `pidp` and every household identifier are never transmitted. Each record is
  keyed by a one-way hash, so a prediction can be scored locally but the request
  carries no identifier that links back to your study.
- I would use the provider's no-training setting, and would seek a
  zero-retention agreement. I can forward the provider's terms if that would
  help you assess it.
- One respondent per request. Nothing is sent in bulk, and no file from the
  Data Collection is uploaded anywhere.
- Nothing is published or shared. No derived dataset leaves my machine, and the
  directories holding the data and anything built from it are excluded from
  version control.
- I will send you the exact text of a single real request before I make any, so
  you are approving the actual content and not my summary of it.

**The safeguard I cannot offer**, stated plainly: once a request reaches a
third-party provider I no longer control it, beyond the provider's contractual
terms. I am not going to claim otherwise, and I understand that may be the whole
answer.

**A second, smaller question.** Separately from the above, I would like to
confirm whether clause 5.5 permits me to use an AI coding assistant running
locally on my own machine while writing the extraction code — reading variable
names and labels, and matching allocation variables to questionnaire wordings —
with nothing transmitted anywhere. I read the clause as covering this on its
plain wording even though no data is transferred, which is why I am asking
rather than assuming.

If the answer to either is no, that is a clear answer and I will work within it.

I would also welcome a steer on whether this belongs on a different route — an
amendment to my Project Information, a Secure Lab application, or a request to
the depositor (ISER) rather than to the Service.

With thanks,

rich hutton
rich.hutton@googlemail.com
UKDS registered user

---

## Notes for rich, not for sending

**Check these before sending.** Two things in the email are mine to draft and
yours to stand behind:

1. **The no-training and zero-retention claims.** Confirm what your provider
   actually offers on your plan before promising it. By default Anthropic does
   not train on API inputs; zero data retention is a separate arrangement and may
   not be available on a standard account. If it is not, cut that bullet rather
   than soften it — a safeguard you cannot deliver is worse than one you never
   claimed.
2. **"Nothing derived from the data would be redistributed."** True today, and it
   is the commitment that makes the rest credible. If the plan for SocSci-UK ever
   changes on that point, this email becomes a problem.

**Why the ask got bigger.** The 5 Oct version was deliberately narrow, on the
reasoning that a single small request is the most likely to be granted. That
reasoning was right and the request was still the wrong one: it asked for
permission to do something that would not have got the research done. Today's
measurement is what changed it — see `scripts/synthetic_probe.py`. The numbers
quoted in the email are from that script's two runs, 40 held-out questions each,
40 of 40 answered on both sides.

**The evidence is the argument.** Permission requests that say "this would be
easier" get declined. This one says "I tested the alternative and it does not
work, here are the numbers, and I did the test on synthetic data specifically so
I would not have to ask you first". That is a materially stronger position, and
it cost one afternoon to be able to say it.

**Expect this to be a known question.** Version 16.00 is dated 25 February 2026
and the AI wording reads as a recent addition, so they will have a position and
may already have published guidance. Worth a look at their website before
sending, in case the answer is already written down.

**If they say no.** It applies to the Innovation Panel, the BES Internet Panel
and the three discrete-choice sets together — same EUL, same clause. The
remaining routes are then:

- **fine-tune a local model** on the dataset being built, which is a different
  thing from prompting one and may clear the bar an 8B cannot clear by prompt;
- **the open and CC0 layers** (TESS, the four Harvard UK deposits), which carry no
  such restriction and where a hosted model can be used freely;
- **hardware**, which buys one step up in model size and, on today's numbers, is
  unlikely to close a 44-point gap.

**Until an answer arrives, nothing changes.** `jev.RESTRICTED` still refuses
`source="ukds"`, `data/raw`, `data/profiles` and `data/processed/*.parquet` stay
gitignored, and no UKDS-derived material has left this machine.
