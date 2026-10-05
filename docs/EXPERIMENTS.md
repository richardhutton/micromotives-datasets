# Experiments built

**This file is generated.** Run `uv run python scripts/experiments_table.py --write` after adding a recipe; `--check` fails if it is stale. Do not edit it by hand — see the module docstring for why.

**42 experiments.** 13 UK (CC0, redistributable), 1 UK licence-restricted (usable for research under each one's own recorded basis, **not** redistributable) and 28 US transfer layer (TESS, no licence stated — usable for research, **not** redistributable).

| Layer | Experiments | Rows | Redistributable |
|---|---|---|---|
| UK — Harvard Dataverse (CC0) | 13 | 130,596 | **yes, CC0 1.0** |
| UK — Harvard Dataverse (licence-restricted) | 1 | 13,268 | **no** — see each experiment's own licence note |
| US transfer — TESS | 28 | 283,935 | **no** — no licence stated |
| **Total** | **42** | **427,799** | |

---

## UK layer — Harvard Dataverse, CC0 1.0

The publishable corpus. Every one of these reproduces a number its own authors printed — a published table, or their own estimator run over the raw deposit — rather than a number we computed and then agreed with.

### `EFXNLX`

**Policy Preferences and Policy Legitimacy After Referendums: Evidence from the Brexit Negotiations**

Forced choice between two possible Brexit deals, each described by eight negotiated terms — immigration, EU citizens' rights, trade, legal jurisdiction, budget contributions, payments, the Irish border and the timeline — followed by a 1-4 acceptability rating of each deal separately.

- **Source** — Harvard Dataverse, `doi:10.7910/DVN/EFXNLX`
- **Type** — paired-profile conjoint, 8 attributes, 6 rounds per respondent, 3 outcomes per round (1 choice + 2 ratings)
- **Category** — political preferences/policy
- **Rows** — 49,395 from 3,293 respondents
- **Licence** — CC0 1.0 Universal
- **Verified against** — the authors' own `cregg::cj()`, 84 estimates agreeing to 1e-6; data/catalog/answer_key_EFXNLX.csv

### `35M5CV_sky`

**Divided by the Vote: Affective Polarization in the Wake of the Brexit Referendum (Sky emotional attachment battery)**

Five-item battery measuring strength of emotional attachment to one's own Brexit identity (Leaver/Remainer) or party identity (Conservative/Labour) — in-group language, personal offence at criticism, felt commonality, connectedness and pride in one's own side. The in-group-identification component of affective polarization, restricted to respondents with a clean primary identity (excludes 'Neither'/'None' respondents routed into a battery via an undocumented follow-up question).

- **Source** — Harvard Dataverse, `doi:10.7910/DVN/35M5CV`
- **Type** — randomised split ballot (Brexit identity vs party identity elicitation), 5 items per respondent, 2,411 respondents x 5 items
- **Category** — political identity/polarisation
- **Rows** — 12,055 from 2,411 respondents
- **Licence** — CC0 1.0 Universal
- **Verified against** — the paper's own Table 2 — all four identity-group scale means, weighted by the deposit's own `Weights` column, reproduced to the paper's printed 1dp precision; see scripts/verify_35M5CV_sky.py

### `PMV0TG`

**Citizens from 13 countries share similar preferences for COVID-19 vaccine allocation priorities**

Forced choice between two hypothetical people over who should receive a COVID-19 vaccine first, differing on risk of death, risk of transmitting, income, occupation and age. A rationing problem: who deserves a scarce life-saving good.

- **Source** — Harvard Dataverse, `doi:10.7910/DVN/PMV0TG`
- **Type** — paired-profile conjoint, 5 attributes, 8 rounds per respondent
- **Category** — moral/social/cognition
- **Rows** — 9,320 from 1,165 respondents
- **Licence** — CC0 1.0 Universal
- **Verified against** — the UK column of the authors' own deposited conjoint_combined_results_UNWEIGHTED_ols.tex — 17 coefficients to within 0.006

### `35M5CV_lodger`

**Divided by the Vote: Affective Polarization in the Wake of the Brexit Referendum (Lodger conjoint)**

Forced choice between two prospective lodgers described by name, age, occupation, volunteering, party politics, EU referendum vote and hobby. The classic social-distance measure: would you share your home with someone who voted the other way.

- **Source** — Harvard Dataverse, `doi:10.7910/DVN/35M5CV`
- **Type** — paired-profile conjoint, 7 attributes, 5 rounds per respondent
- **Category** — political identity/polarisation
- **Rows** — 8,345 from 1,669 respondents
- **Licence** — CC0 1.0 Universal
- **Verified against** — the authors' own `cregg::cj()` run over the raw deposit, transcribed to data/catalog/answer_key_35M5CV_lodger.csv

### `35M5CV_bbc`

**Divided by the Vote: Affective Polarization in the Wake of the Brexit Referendum (BBC conjoint)**

Forced choice between two applicants for Director General of the BBC, described by name, age, experience, degree, party politics, EU referendum vote and occupation. Tests whether Leave/Remain identity affects judgement of competence for a public role.

- **Source** — Harvard Dataverse, `doi:10.7910/DVN/35M5CV`
- **Type** — paired-profile conjoint, 7 attributes, 5 rounds per respondent
- **Category** — political identity/polarisation
- **Rows** — 8,175 from 1,635 respondents
- **Licence** — CC0 1.0 Universal
- **Verified against** — the authors' own `cregg::cj()` run over the raw deposit, transcribed to data/catalog/answer_key_35M5CV_bbc.csv

### `LOGVPZ_risk_tolerance`

**Mind the Gap: Why Wealthy Voters Support Brexit**

The same lottery-wealth treatment, with the outcome a 0-3 financial risk-tolerance code built from a branching pair of hypothetical job-gamble questions (would you swap a safe job for one with a 50-50 chance of doubling or cutting your income).

- **Source** — Harvard Dataverse, `doi:10.7910/DVN/LOGVPZ`
- **Type** — two-condition between-subject, one DERIVED outcome on a 0-3 scale
- **Category** — economics/behavioural
- **Rows** — 8,075 from 8,075 respondents
- **Licence** — CC0 1.0 Universal
- **Verified against** — the paper's own Table D.2 — N, control mean and both regression coefficients; the branch logic itself is pinned by tests/test_derive_LOGVPZ.py across all 64 inputs of the instrument's code space

### `LOGVPZ_brexit_satisfaction`

**Mind the Gap: Why Wealthy Voters Support Brexit**

Respondents are told to imagine they have won a substantial lottery prize, or told nothing, then asked how satisfied they are that the UK voted to leave the EU. Tests whether unearned wealth shifts Brexit support.

- **Source** — Harvard Dataverse, `doi:10.7910/DVN/LOGVPZ`
- **Type** — two-condition between-subject, one outcome on an 11-point scale
- **Category** — political preferences/policy
- **Rows** — 7,506 from 7,506 respondents
- **Licence** — CC0 1.0 Universal
- **Verified against** — the paper's own Table D.1 — N, control mean and both regression coefficients

### `6MRVOM_brexit_scenario`

**Pricing Immigration**

Respondents are told the government will, after Brexit, either keep immigration at roughly current levels or only cut it a little while shifting its source from Europe to beyond Europe. Two outcomes under whichever scenario they met: which party they would support in the next general election, and how satisfied they would feel about the Brexit decision. Tests whether the SOURCE of post-Brexit immigration, not just its level, moves party support and Brexit satisfaction.

- **Source** — Harvard Dataverse, `doi:10.7910/DVN/6MRVOM`
- **Type** — two-condition between-subject (post-Brexit immigration scenario), 2 outcomes per respondent (11-level nominal party choice, code 12 'Don't know' dropped per the 2026-10-05 ruling; 0-10 satisfaction)
- **Category** — political preferences/policy
- **Rows** — 6,526 from 3,636 respondents
- **Licence** — CC0 1.0
- **Verified against** — no author-computed or published reference exists for this block (checked analysis.R and the full 24-page accepted manuscript); scripts/verify_6MRVOM.py instead confirms the built distribution matches data.sav's own frequency tables exactly, cell for cell

### `QQM5MC`

**A Tale of Two Peoples: Motivated Reasoning in the Aftermath of the Brexit Vote**

A split ballot crossing a Leaver/Remainer identity prime with factual information about UK GDP growth. Outcomes are the respondent's estimate of the UK's growth rank among 34 OECD countries, and whether they think the economy is getting better or worse. Tests motivated reasoning about shared economic facts.

- **Source** — Harvard Dataverse, `doi:10.7910/DVN/QQM5MC`
- **Type** — 2x2 split ballot (prime x information) plus a true control, 2 outcomes
- **Category** — political identity/polarisation
- **Rows** — 6,345 from 3,266 respondents
- **Licence** — CC0 1.0
- **Verified against** — the paper's own Table 1 and Figures 4-5 — eight group means and two Ns

### `RJTVG8`

**Support for digitising the ballot box: a systematic review of i-voting pilots and a conjoint experiment**

Forced choice between two hypothetical UK internet-voting (i-voting) policies, differing on ten features — pre-registration, voting method, voting window, where trials succeeded, the pilot's effect on turnout and on fraud risk, who controls the platform, the cost to government, the proposing party and the endorsing body. The respondent judges a PROPOSED POLICY, not a person.

- **Source** — Harvard Dataverse, `doi:10.7910/DVN/RJTVG8`
- **Type** — paired-profile conjoint, 10 attributes (one — platform — a single 6-level draw, not a 2x3 cross), 5 tasks per respondent
- **Category** — political preferences/policy
- **Rows** — 6,000 from 1,200 respondents
- **Licence** — CC0 1.0
- **Verified against** — the authors' own cregg::mm() marginal means, Table A.4 of the author-accepted manuscript — 51 estimates to within 0.0015

### `PZB01G`

**For and Against Brexit: A Survey Experiment of the Impact of Campaign Effects on Public Attitudes toward EU Membership**

Respondents are shown a campaign vignette combining a pro- or anti-EU cultural frame, a pro- or anti-EU economic frame and a pro- or anti-EU political frame (eight combinations), or no vignette at all (a true control), then asked how they would vote in the EU membership referendum. Tests which real-world campaign arguments, alone and in combination, shift referendum vote intention.

- **Source** — Harvard Dataverse, `doi:10.7910/DVN/PZB01G`
- **Type** — 2x2x2 full factorial (cultural x economic x political frame, each pro/anti) plus a true control, one outcome on a 4-way nominal scale (Remain/Leave/Would not vote/Don't know)
- **Category** — political preferences/policy
- **Rows** — 5,333 from 5,333 respondents
- **Licence** — CC0 1.0
- **Verified against** — the paper's own Appendix Table A6 (nine group sizes, reproduced exactly) and its own text (p.8, the control group's published Wave 2 Remain/Leave/Don't-know-or-would-not-vote shares, reproduced to 0.1 percentage point); scripts/verify_PZB01G.py

### `6MRVOM_eu_share`

**Pricing Immigration**

Respondents are asked what percentage of all immigrants to the UK they would like to see coming from the EU (vs. elsewhere), on a 0-100 slider; half are additionally told the current EU share is 50%. Tests whether an explicit base-rate anchor shifts the preferred EU/non-EU immigration mix.

- **Source** — Harvard Dataverse, `doi:10.7910/DVN/6MRVOM`
- **Type** — two-condition between-subject (information anchor present/absent), one outcome on a 0-100 scale
- **Category** — political preferences/policy
- **Rows** — 2,397 from 2,397 respondents
- **Licence** — CC0 1.0
- **Verified against** — the deposit's own analysis.R — svymean(eushare), overall and by condition, reproduced from the built parquet to within rounding

### `X08IVC`

**Brexit as an Identity: Political Identities and Policy Norms**

Respondents are told there is debate about reducing immigration to Britain, then either given no further information or told that most Leavers support reducing immigration while most Remainers do not, before being asked whether immigration should be reduced. Tests whether a Brexit-identity policy-norm cue shifts Leavers' and Remainers' own immigration preferences toward their in-group's.

- **Source** — Harvard Dataverse, `doi:10.7910/DVN/X08IVC`
- **Type** — two-condition between-subject (control vs. a policy-norm cue), one outcome on a 5-point agreement scale
- **Category** — political preferences/policy
- **Rows** — 1,124 from 1,124 respondents
- **Licence** — CC0 1.0
- **Verified against** — the paper's own Table 2 — four group means and two group Ns, reproduced exactly

---

## UK layer — Harvard Dataverse, licence-restricted

**None of this is redistributable.** Each experiment here carries its own short licence note; the full basis it is used on is recorded in `data/catalog/uk_dataverse_provenance.json`'s `use_basis` for that study. Usable for research under that basis only — never published, shared, or sent to any external service.

### `POMIFD`

**Replication Data for: The Variable Persuasiveness of Political Rhetoric**

Respondents see two of 336 political arguments (14 rhetorical elements x 12 policy issues x 2 positions, for/against) shown together, verbatim as extracted from Hansard debate transcripts, and say which they find more persuasive or that the two are about the same. The respondent judges which ARGUMENT about a policy is persuasive, not a person — closer to the 'policy' pole than the 'identity' pole, since nothing about Leave/Remain regard for other people is measured. Unlike every other UK Dataverse study in this corpus (all conjoints, where the condition is a table of attribute levels this project renders into prose), the condition text here is the fielded instrument's own argument text, transcribed verbatim and not authored by this project.

- **Source** — Harvard Dataverse, `doi:10.7910/DVN/POMIFD`
- **Type** — within-subject paired-argument forced choice, 3-way nominal outcome (argument one more persuasive / about the same / argument two more persuasive), 4 comparisons per respondent drawn from 12 policy issues
- **Category** — political preferences/policy
- **Rows** — 13,268 from 3,317 respondents
- **Licence** — None stated (see `uk_dataverse_provenance.json`'s `use_basis` for the full basis)
- **Verified against** — the paper's own published descriptive statistic (AJPS 2022, p.9) — '28% of comparisons... about the same' — reproduced from the built parquet's response distribution; scripts/verify_POMIFD.py. Does NOT verify the headline Bayesian multilevel model (not refit) or any individual argument's text/pairing, which an aggregate proportion cannot see — see the script's own docstring

---

## US transfer layer — TESS, no licence stated

Fielded in the United States on topics judged universal enough to transfer. **None of this is redistributable**: all 202 deposits in the TESS catalogue were checked individually against the OSF API and 196 state no licence, 6 are unreachable. Usable for research here; not shippable, and not sent to any external service — `embed.py`'s licence gate refuses this text by name.

| Experiment | Title | Category | Rows | Respondents | Reference |
|---|---|---|---|---|---|
| `7jt2f` | When Others' Disbelief Engenders Prejudice: Characterizing Anti-Ath… | cross-national | 3,053 | 613 | osf.io/7jt2f |
| `c5r2f` | Do Policy Defaults Communicate Choice-Relevant Information? | economics/behavioural | 1,091 | 1,091 | osf.io/c5r2f |
| `a42yg` | Conflict between curative and palliative goals among health care pe… | health communication | 8,022 | 503 | osf.io/a42yg |
| `a5v96_vignette1` | What fosters patients' acceptance of Clinical Decision Support? (vi… | health communication | 3,621 | 1,211 | osf.io/a5v96 |
| `bf8p2` | Does Misery Love Company? Exploration of a Strategic Social Comparison | health communication | 1,998 | 1,998 | osf.io/bf8p2 |
| `dh3nj` | Public Perceptions of Prenatal Alcohol Consumption | health communication | 4,001 | 2,002 | osf.io/dh3nj |
| `sh4px` | Self-Affirmation and Affect: Effects on Implementation Intentions | health communication | 11,532 | 1,161 | osf.io/sh4px |
| `z358z` | Randomized Drug Trials without Consent? The Public's Perspective | health communication | 14,702 | 2,130 | osf.io/z358z |
| `zaqkm` | Causal Attributions, Treatability, and Mental Illness Stigma | health communication | 9,528 | 1,607 | osf.io/zaqkm |
| `9263n` | To Do, to Have, or to Share? Valuing Experiences and Material Posse… | moral/social/cognition | 6,328 | 814 | osf.io/9263n |
| `9xw67_conjoint` | Blame and Bias in Trust in Public Policy Algorithms | moral/social/cognition | 20,373 | 2,048 | osf.io/9xw67 |
| `9xw67_vignette` | Blame and Bias in Trust in Public Policy Algorithms | moral/social/cognition | 5,816 | 1,846 | osf.io/9xw67 |
| `b87sm` | How to Increase the Acceptance of Mobile App and Sensor Data Collec… | moral/social/cognition | 19,282 | 1,942 | osf.io/b87sm |
| `es4xw` | Perceptions of Diversity Across Groups | moral/social/cognition | 32,228 | 2,501 | osf.io/es4xw |
| `zrwjp` | The Barriers of Buying Happier Time | moral/social/cognition | 2,532 | 1,271 | osf.io/zrwjp |
| `5hqan` | Gender Identity and Diversity | survey methodology | 6,411 | 2,139 | osf.io/5hqan |
| `a2nbf` | An Experiment Testing Possible Question-Wording Effects on Key Gene… | survey methodology | 6,211 | 1,567 | osf.io/a2nbf |
| `evnyh_Q1a_and_validation` | Impact of Response Scale Direction on Survey Responses (Keusch, TES… | survey methodology | 33,932 | 1,724 | osf.io/evnyh |
| `rpw4u_RO1` | Cross-National Replication of Question Design Experiments (RO1: oil… | survey methodology | 1,023 | 1,023 | osf.io/rpw4u |
| `sd7cf` | Framing in Noisy Informational Environments | survey methodology | 4,124 | 2,069 | osf.io/sd7cf |
| `8ctbk` | Childbearing Preferences in the Face of Work, Family, and Financial… | work/family/gender | 17,464 | 1,794 | osf.io/8ctbk |
| `cug34_B01_B09` | Public Perceptions of Money in Families | work/family/gender | 15,091 | 4,004 | osf.io/cug34 |
| `py9q3_vignette1` | Attitudes toward the Employment of Mothers and Fathers | work/family/gender | 6,667 | 1,682 | osf.io/py9q3 |
| `py9q3_vignette2` | Attitudes toward the Employment of Mothers and Fathers | work/family/gender | 5,005 | 1,682 | osf.io/py9q3 |
| `py9q3_vignette3` | Attitudes toward the Employment of Mothers and Fathers | work/family/gender | 6,659 | 1,682 | osf.io/py9q3 |
| `ye2ej` | The Wages of Parenthood: At the Intersection of Sexual Orientation … | work/family/gender | 12,971 | 1,008 | osf.io/ye2ej |
| `yv2ta_flexible_scheduling` | Opting into Work-Family Policies: Comparing the Effects of Material… | work/family/gender | 12,131 | 2,036 | osf.io/yv2ta |
| `yv2ta_parental_leave` | Opting into Work-Family Policies: Comparing the Effects of Material… | work/family/gender | 12,139 | 2,036 | osf.io/yv2ta |

---

## By category

Categories are TESS's own six, reused verbatim so the two layers can be compared across one taxonomy, plus two political categories added for the UK layer — which needed them because TESS's vocabulary has no political category at all. That absence is itself a finding about how different the two corpora are. The definitions and the judgement behind the political split are in `data/catalog/experiment_manifest.json`.

| Category | UK | US (TESS) | Rows |
|---|---|---|---|
| cross-national | 0 | 1 | 3,053 |
| economics/behavioural | 1 | 1 | 9,166 |
| health communication | 0 | 7 | 53,404 |
| moral/social/cognition | 1 | 6 | 95,879 |
| political identity/polarisation | 4 | 0 | 34,920 |
| political preferences/policy | 8 | 0 | 91,549 |
| survey methodology | 0 | 5 | 51,701 |
| work/family/gender | 0 | 8 | 88,127 |

