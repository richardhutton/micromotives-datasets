# Draft email — POMIFD courtesy notice

**Status:** draft, not sent. For rich to send, edit or discard.

**Revised twice on 5 Oct 2026.** Draft 1 asked permission to REDISTRIBUTE derived rows —
wrong, rich is not redistributing and does not want that liability. Draft 2 stripped it
back to a bare notice. This draft puts the substance back in, because rich's read is that
Blumenau may find the work genuinely interesting, and he is right: the paper is about
*variation in persuasiveness across people*, which is precisely the individual-level
prediction problem the dataset exists to measure. That is a real intellectual hook rather
than padding, and an academic is more likely to engage with it than with a bare notice.

Still asks for nothing.

**To:** `j.blumenau@ucl.ac.uk` (Jack Blumenau, UCL — the deposit's named contact)
**Cc:** Benjamin Lauderdale, if you want the co-author in the loop
**Subject:** Use of POMIFD replication data — predicting individual persuasion with language models

---

Dear Dr Blumenau,

Your Harvard Dataverse deposit for "The Variable Persuasiveness of Political Rhetoric"
(doi:10.7910/DVN/POMIFD) carries the note *"This dataset is made available with limited
information on how it can be used. You may wish to communicate with the Contact(s)
specified before use."* — so I am doing that, and since the work may be of some interest
to you, a little about it.

I am building a UK dataset for testing how accurately large language models predict
human survey responses. It follows SocSci210 (arXiv:2509.05830), which did this for 210
US experiments. Every row is a tuple: a respondent's demographic profile, the exact
stimulus they were shown, the question they were asked, and the answer they actually
gave. A model sees the first three and is scored on the fourth.

So far it covers eleven experiments and about 124,000 responses, all from CC0 Harvard
Dataverse deposits — Hobolt, Leeper and Tilley's Brexit negotiation and affective
polarisation conjoints, Sorace and Hobolt on motivated reasoning, Green and Pahontu on
wealth and Brexit support, Duch et al. on vaccine allocation, Hix, Kaufmann and Leeper
on immigration costs. Each one is verified by reproducing a number its own authors
published, from the built rows rather than from the raw file, so an error in the
reshaping cannot hide.

Your study is the one I most want in it, and the reason is specific. Most of what I have
is forced-choice conjoint, where the interesting quantity is an average marginal effect.
Yours asks something harder: *which* argument persuades *which* person. That is an
individual-level prediction problem, and it is exactly the thing these models are
claimed to be good at and rarely tested on properly. The 336 arguments ship verbatim,
every pairwise comparison a respondent saw is recoverable by a join, and the demographic
block is the richest of any UK deposit I have looked at. The twelve policy topics would
also pull the corpus away from the Brexit concentration it currently has.

**I am not redistributing anything.** Nothing derived from your data would be published,
shared or made available to anyone else — this is for my own research use. The study and
the AJPS article would be cited in any write-up.

If you would rather I did not use it, or there are parts you would want left out, please
just say and I will respect that. And if any of the above is useful to you — results on
how well current models reproduce your findings, for instance — I would be glad to share
what I find.

With thanks,

rich hutton
rich.hutton@googlemail.com

---

## Notes for rich, not for sending

**The hook is real, so it is worth leading with.** His paper's whole point is that
rhetorical elements persuade different people differently. An LLM benchmark that scores
individual-level prediction rather than aggregate effects is the natural computational
follow-on. If anyone replies to this, it will be because of that paragraph.

**The last line is an offer, not a promise.** Sharing results back costs nothing, reads
as collegial rather than extractive, and is the kind of thing that turns a one-line
acknowledgement into an actual correspondence. Drop it if you would rather not be on the
hook.

**Cc'ing Lauderdale** is optional. Blumenau is the named `datasetContact` so he is the
correct recipient; the co-author may simply want to know.

**Still asks for nothing**, so there is nothing to refuse. If they do not reply that is
not a refusal — the terms say "you may wish to communicate", and you have.

**What we gain:** ~3,317 respondents, ~13,268 pairwise comparisons, across Heathrow's
third runway, Boxing Day trading, Right to Buy, surveillance powers, fracking, rail
nationalisation, boardroom quotas, cannabis, tuition fees, Trident, the 0.7% aid
commitment and the sugar tax.
