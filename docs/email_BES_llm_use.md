# Draft email — BES, hosted model use

**Status:** draft, not sent. For rich to send, edit or discard.

**To:** `BES@Manchester.ac.uk`
**Subject:** Does the Licensed Use cover sending panel responses to a hosted model?

---

Dear BES team,

I am a registered user of the Internet Panel and want to check one thing before
I do it.

Your wave 30 documentation (p.30) records that "Open text responses in wave 26
onwards were coded using large language models – GPT-4o from OpenAI – and not by
BES research associates."

I would like to do something similar and narrower. I am measuring how accurately
language models predict individual survey responses — the UK equivalent of Park
et al., "LLM Agents Grounded in Self-Reports Enable General-Purpose Simulation
of Individuals" (https://arxiv.org/abs/2411.10109). For each respondent I would send
one request to a hosted model (Anthropic's API) containing their own coded
answers with all identifiers removed and replaced by a one-way hash, and ask it
to predict one answer of theirs that I have withheld. The reply is a single
digit. No free text, no identifiers, one respondent per request, nothing in bulk,
and nothing published or shared.

My question is whether the Licensed Use already covers this, or whether you would
like me to ask separately. I am asking because of the Personal Data condition —
"Do not share or give access to the data to any third party who has not agreed to
these conditions" — which I read as possibly covering an API provider even where
the Licensed Use permits transfer for research purposes.

Happy to send the exact text of a single request if that is easier to judge than
my description of it.

With thanks,

rich hutton
rich.hutton@googlemail.com

---

## Notes for rich, not for sending

**Why this is a confirmation, not a request.** They already send respondents'
own free text to a third-party hosted API, and documented it. Free text is MORE
identifying than coded answers, so the thing being asked about is narrower than
their established practice. Someone on that team knows the answer already.

**Why ask at all, given that.** Their precedent is BES acting as the data
controller on their own data. A user doing it is a different position, and the
Personal Data condition is written broadly enough to catch it. The cost of
asking is one email; the cost of being wrong is the licence, which terminates
automatically on breach and obliges destroying every copy within seven days.

**Quote verified** against `Bes_wave30Documentationv30.0.pdf`, fetched from their
site and read directly — not from a search result. That matters here: the
previous licence question in this project (ledger 106) went wrong precisely
because a claim about terms had been written down once and never checked.

**What does NOT wait on this reply:** downloading, extracting, reshaping,
building rows, running local models, and fine-tuning locally. All of that is
inside the Licensed Use on its plain wording ("use, reproduce, extract,
download, copy", "you may alter or adapt the Datasets", "include ... in other
products for research purposes"). Only the hosted-model step waits.

**If they say no**, the fallback is the same as everywhere else: local models and
fine-tuning, which is where the project was heading anyway, plus the open and CC0
layers for anything a hosted model is needed for.

**The separate thing worth remembering.** BES also GRANTS distribution —
"reproduce, extract, download, copy, distribute, display or include ... in other
products for research purposes", with attribution, subject to recipients
agreeing to the same conditions. SocSci-UK currently has no publishable UK panel
data at all. That is share-alike rather than open, but it is far more than the
UKDS EUL allows, and it should shape what the UK layer is for.
