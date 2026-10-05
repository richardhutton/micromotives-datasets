# Email — POMIFD courtesy notice to Jack Blumenau

**Status:** FINAL, for rich to send.

**Revised three times on 5 Oct 2026.** Draft 1 asked permission to redistribute — wrong,
rich is not redistributing. Draft 2 stripped it to a bare notice. Draft 3 put the project
back in. This version corrects the facts: the paper is AJPS **2022**, doi
10.1111/ajps.12703 (the Dataverse record still says "Forthcoming"), fielded by **YouGov in
June 2019**, 3,317 respondents × 4 comparisons = 13,268, and the 336 arguments are
14 rhetorical elements × 12 issues × 2 positions, drawn from Hansard. Getting those right
matters: an email that describes someone's own design back to them inaccurately is worse
than one that does not mention it.

**To:** `j.blumenau@ucl.ac.uk`
**Cc:** Benjamin Lauderdale, optional
**Subject:** Use of POMIFD replication data — predicting individual persuasion with language models

---

Dear Dr Blumenau,

Your Harvard Dataverse deposit for "The Variable Persuasiveness of Political Rhetoric"
(doi:10.7910/DVN/POMIFD) carries the note *"This dataset is made available with limited
information on how it can be used. You may wish to communicate with the Contact(s)
specified before use."* — so I am doing that, and since the work may be of some interest
to you, a little about it.

I am building a UK dataset for testing how accurately large language models predict human
survey responses. It follows SocSci210 (arXiv:2509.05830), which did this for 210 US
experiments. Each row is a tuple: a respondent's demographic profile, the exact stimulus
they were shown, the question they were asked, and the answer they actually gave. The
model sees the first three and is scored on the fourth.

It currently covers eleven experiments and about 124,000 responses, all from CC0 Harvard
Dataverse deposits — Hobolt, Leeper and Tilley on the Brexit negotiations and on affective
polarisation, Sorace and Hobolt on motivated reasoning, Green and Pahontu on wealth and
Brexit support, Hix, Kaufmann and Leeper on immigration costs, Duch et al. on vaccine
allocation. Each study is verified by reproducing a figure its own authors published, and
recomputed from the built rows rather than from the raw file, so an error in the reshaping
cannot hide behind a correct-looking number.

Yours is the study I would most like to include, for a reason specific to your design.
Nearly everything I have is forced-choice conjoint, where the natural quantity is an
average marginal effect across respondents, and where the "stimulus" is really a table of
attribute levels that I have to render into prose. Your experiment is neither of those
things. The treatments are actual political arguments — drawn from Commons debates, not
constructed from factor levels — and the question you put to respondents is which of two
they personally found more persuasive. That is an individual-level prediction problem with
real political writing as the input, which is both much closer to what these models face
in practice and much harder to evaluate well.

Your own finding makes the point sharper. If the persuasiveness of a rhetorical element
varies as much across implementations as you report, then any claim that a model has
learned "what persuades people" has to survive exactly that variation — 14 elements across
12 issues — rather than one well-chosen vignette. I do not know of a better-suited dataset
in UK politics.

**I am not redistributing anything.** Nothing derived from your data would be published,
shared, or made available to anyone else; this is for my own research use. The article and
the deposit would be cited in any write-up.

If you would rather I did not use it, or there are parts you would want left out, please
just say and I will respect that. And if anything that comes out of it would be useful to
you — how well current models reproduce your estimates, for instance, or where they fail —
I would be glad to share it.

With thanks,

rich hutton
rich.hutton@googlemail.com

---

## Notes for rich, not for sending

**The second-to-last substantive paragraph is the one that earns a reply.** It is not
flattery — it restates his actual contribution (variation across implementations, not the
average effect) and says why that specific finding makes his data the right test. An
academic can tell the difference between someone who read the paper and someone who read
the abstract.

**Facts checked before sending**, so nothing in it is wrong about his own work: AJPS 2022
not forthcoming; YouGov June 2019; 3,317 respondents, four comparisons each, 13,268
observations; 14 × 12 × 2 = 336; arguments sourced from Hansard. All from the open author
manuscript at discovery.ucl.ac.uk/id/eprint/10145870.

**The closing offer costs nothing** and reads collegial rather than extractive. Cut it if
you would rather not be on the hook for a follow-up.

**It still asks for nothing**, so there is nothing to refuse. If he does not reply, that is
not a refusal — the terms say "you may wish to communicate", and you have.

**What we gain:** 3,317 respondents, 13,268 pairwise comparisons, 336 verbatim argument
texts across twelve UK policy issues — Heathrow's third runway, Boxing Day trading, Right
to Buy, surveillance powers, fracking, rail nationalisation, boardroom quotas, cannabis,
tuition fees, Trident, the 0.7% aid commitment and the sugar tax. The richest persona
block of any UK deposit, and the single biggest reduction available to the corpus's Brexit
concentration.
