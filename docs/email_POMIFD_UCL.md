# Draft email — POMIFD licence enquiry

**Status:** draft, not sent. For rich to send, edit or discard.

**To:** `j.blumenau@ucl.ac.uk` (Jack Blumenau, UCL — the deposit's named contact)
**Cc:** consider Benjamin Lauderdale, the co-author, also at UCL
**Subject:** Reuse permission — "The Variable Persuasiveness of Political Rhetoric" replication data (doi:10.7910/DVN/POMIFD)

---

Dear Dr Blumenau,

I am building an open benchmark dataset of UK survey experiments, for research on
how well language models predict human responses. It is modelled on SocSci210
(arXiv:2509.05830), which does the same for US studies, and each row pairs a
respondent's demographics with the exact stimulus they saw and the answer they
gave.

Your Harvard Dataverse deposit for "The Variable Persuasiveness of Political
Rhetoric" (doi:10.7910/DVN/POMIFD) is the single best-suited UK study I have
found. The 336 argument texts are deposited verbatim, every pairwise comparison a
respondent saw is recoverable, and the demographics are richer than in any other
UK deposit I have looked at. The other eight UK experiments I am working from are
all CC0, and I would very much like this one to sit alongside them.

The deposit's terms read: *"This dataset is made available with limited
information on how it can be used. You may wish to communicate with the
Contact(s) specified before use."* I am taking that invitation up rather than
assuming anything, because the Dataverse record states no licence and I would not
want to redistribute your material without your say-so.

Concretely, what I would like to ask is:

1. **May I redistribute derived rows?** The published dataset would contain, per
   row, one of your argument texts as the stimulus, the respondent's answer, and
   their demographics — so your argument wordings and respondent-level responses
   would be re-published, reformatted, as part of an openly licensed dataset.

2. **If yes, under what licence and what attribution?** CC0 or CC-BY would both
   work for me. I would cite the AJPS article and the deposit DOI on every row and
   in the dataset documentation either way.

3. **Is there anything you would want excluded?** If some variables or arguments
   should not be redistributed, I would rather know now and leave them out than
   guess.

If the answer is no, or not yet, that is genuinely fine — I will record the study
as unavailable and move on, and nothing of yours will appear anywhere.

Happy to share the row format, the code that produces it, or a sample built from
one of the CC0 studies, if that would help you judge the request.

With thanks for considering it,

rich hutton
rich.hutton@googlemail.com

---

## Notes for rich, not for sending

**What we gain if they say yes.** ~3,317 respondents and ~13,268 pairwise
comparisons, which would make it the second-largest UK study after `EFXNLX` and
the single richest on persona. The 336 arguments ship as 12 per-topic CSVs, all UK
policy questions — Heathrow's third runway, Boxing Day trading, Right to Buy,
surveillance powers, fracking, rail nationalisation, boardroom quotas, cannabis,
tuition fees, Trident, the 0.7% aid commitment, the sugar tax. That topic spread
alone would materially reduce the corpus's Brexit concentration.

**What the ask actually is.** Note question 1 is the real one, and it is a bigger
ask than it first looks: we would be re-publishing their argument texts AND
respondent-level answers. Worth being this explicit — a vague "may I use your
data" invites a vague yes that would not actually cover redistribution.

**The three things verified before writing this**, so nothing in the email
overstates:
- `licence` is literally `null` on the Dataverse API, re-confirmed 5 Oct 2026.
- `termsOfUse` is quoted exactly as the API returns it.
- Jack Blumenau is the deposit's own `datasetContact`, so he is the right
  recipient rather than a guess from the author list.

**If they say no**, the catalogue entry already carries the reason and the study
simply stays `blocked`. Nothing else in the project depends on it.
