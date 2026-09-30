# Can the UK datasets be merged? — persona check

**The question this answers:** to train on several studies at once, a field has
to mean the same thing in every file. If one study codes `gender 1=Male` and
another codes `1=Female`, stacking them corrupts the data. So before merging, we
check the codings line up.

**The answer:** the four main studies share one coding for most fields. Two
fields need a fix first.

Checked: the four YouGov studies — Persuasion, Brexit conjoint, Divided by the
Vote, Pricing Immigration.

## Fields that already match — safe to merge as-is

- **Gender** — 1=Male, 2=Female in all four.
- **Education** — same qualification list in all four.
- **EU-referendum vote** — 1=Remain, 2=Leave, 3=Did not vote in all four.
- **Region** — same coding in three of the four.

## Fields that don't match — need a fix before merging

- **Social grade.** Same A–E scale, but grouped differently per study:
  - Persuasion, Divided: A, B, C1, C2, D, E (full)
  - Brexit: AB, C1, C2, D, E
  - Pricing: AB, C1, C2, DE

  Fix: map all to common bands. Where a study already merged A+B or D+E, you
  can't split them back — keep them as `AB` / `DE`.

- **Region in "Divided by the Vote."** It's there, but uses different numbers
  than the other three. Fix: remap Divided's region codes to the standard 12
  regions.

## Still open

- **British Election Study** — couldn't check; the local file was deleted.
  Re-download to confirm it uses the same coding.
- The thinner / non-UK studies (Cyber, i-voting, vaccine, anti-immigrant,
  psychology) — not checked yet.

## The merged persona — field order for every row

age · gender · ethnicity · region · education · social grade · income ·
work status · marital · party · EU vote

One line per field that exists. Missing fields left out. Original value kept
alongside.

---
Checked 2026-09-21 from the study files on Harvard Dataverse.
DOIs: Persuasion `10.7910/DVN/POMIFD` · Brexit `10.7910/DVN/EFXNLX` ·
Divided `10.7910/DVN/35M5CV` · Pricing `10.7910/DVN/6MRVOM`.
