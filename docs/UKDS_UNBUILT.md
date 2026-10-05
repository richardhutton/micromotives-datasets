# Innovation Panel experiments, screened

Generated — run `uv run python scripts/innovation_panel_table.py --write`.
Source: `data/catalog/innovation_panel_experiments.json`, whose titles and waves
are parsed from the Innovation Panel User Guide (UKDS **SN 6849**, waves 1–17,
2008–2024). Category and verdict are judgement and are recorded in that file.

**93 experiments.** 44 pass screening, 9 need a ruling, 40 are out.

The 44 that pass span **63 experiment-waves**, because 14 of them ran in two or more waves — which is the time axis the Harvard and TESS layers structurally cannot provide.

**Nothing here is claimed to be buildable.** These are desk judgements from the guide's own summaries. The condition text lives only in each wave's questionnaire PDF, and whether it is there word-for-word is unverified. That check will move experiments out of `build`, not into it.

**On the quoted descriptions.** The EUL defines the Data Collection to include its Documentation, which is why `jev.RESTRICTED` refuses `source="ukds"` and why the bundle is gitignored. The descriptions below are nonetheless quoted, because the User Guide is separately published on the open web — it says so itself: *"we recommend using the web-based version of the Innovation Panel User Guide as the documentation will develop over time, with the latest versions updated to these pages"*. Quoting an openly published guide is not redistributing a safeguarded collection. **No variable label, value label or row from the data files appears in this file or its catalogue**, and that is the line to hold.

## At a glance

| Verdict | Experiments | Experiment-waves |
|---|---|---|
| `build` | 44 | 63 |
| `marginal` | 9 | 22 |
| `drop` | 40 | 74 |

| Category | Build | Marginal | Drop |
|---|---|---|---|
| Attitudes and politics | 8 | 0 | 0 |
| Wellbeing and satisfaction | 2 | 2 | 0 |
| Health | 5 | 0 | 2 |
| Work, money and expectations | 6 | 2 | 0 |
| Family, care and the household | 6 | 1 | 0 |
| Technology and the future | 1 | 0 | 0 |
| Sensitive questions | 1 | 0 | 0 |
| Consent to data linkage | 8 | 0 | 0 |
| The form of the question rather than its content | 7 | 4 | 5 |
| Physical measurement and apps | 0 | 0 | 5 |
| Procedural — getting the respondent to take part | 0 | 0 | 28 |

**4 vignette studies** — `9.10`, `9.26`, `9.30`, `9.39`. These carry prose written by the researchers and shown to respondents word-for-word, which is the one thing the rest of the corpus is short of: every conjoint we hold gives attribute levels that we render into sentences ourselves.

## Experiments spanning two or more waves

The same condition, asked of different people in different years. Holding out a wave tests whether a model that predicts one year predicts another.

| ID | Waves | Title |
|---|---|---|
| `8.4` | 3, 4, 5, 7 | Dependent interviewing wording |
| `8.3` | 2, 3, 4 | Impact of question wording and context on measuring change |
| `8.5` | 3, 4, 5 | Branched vs. unbranched rating scales for measuring attitudes |
| `9.11` | 5, 8, 9 | Subjective expectations about the returns to higher education and decisions to attend university |
| `8.11` | 7, 8 | Impact of response scale direction on responses |
| `9.9` | 4, 5 | Context effects in fertility decisions |
| `9.10` | 5, 6 | Vignettes: measuring partner satisfaction with division of household labour |
| `9.12` | 6, 7 | Measuring change in self-assessed disability |
| `9.13` | 6, 7 | Associated Study: measuring time and risk preferences |
| `9.16` | 8, 9 | Social desirability bias in attitudes towards immigration |
| `9.17` | 8, 9 | Measuring sexual identity using direct and indirect questioning |
| `9.18` | 9, 17 | What do the general population regard as “successful ageing”? |
| `9.21` | 10, 11 | Improving consent to link to the electoral register |
| `9.25` | 11, 15 | HMRC data linkage consent experiment |

## Verdict: `build`

Descriptions are the User Guide's own prose. `allocation` is the variable the guide names as controlling the condition, where it names one — the rest have to be found in the data.

### Attitudes and politics (8)

**`9.4` Measuring identity**  
wave 2 · allocation `b_ff_identityw2`  
In Wave 2, the Innovation Panel tested a set of questions on identity based on items carried in the Citizenship Survey in 2007-2008. In total, respondents were given 13 categories with which they could identify (or not).

*Assessed:* asked about your profession vs your occupation; pure wording

**`9.14` Assessing how people think about environmental taxes**  
wave 7  
This experiment examines different wordings of questions on willingness to pay environmental taxes. Each respondent receives a single question concerning willingness to pay an environmental tax. There are 10 question variants. Households within PSUs are allocated to treatment.

**`9.16` Social desirability bias in attitudes towards immigration**  
waves 8, 9  
Intolerance to ethnic minority immigrants is often masked, which can lead to systematically under-reported opposition and over-reported tolerance. This experiment is a longitudinal application of a list experiment.

**`9.26` Does competition over public services decrease support for residency rights of immigrants? — VIGNETTE**  
wave 11  
This study contains two experimental sets of questions that explore respondents’ views towards residency rights of immigrants.

*Assessed:* two sets of questions: a conjoint and a set of vignettes

**`9.38` National identity**  
wave 15  
National identities inform behaviours and shape social relations, with evidence for changes both in majority and minority identities in recent years with respect to self-reported identity choice and the meaning people ascribe to it.

**`9.40` Cognitive reflection and politically motivated reasoning**  
wave 16  
This experiment uses a variation of a known cognitive reflection test (CRT) to test whether politically motivated reasoning is a manifestation of heuristic or deliberative thinking. The CRT is a four-question battery asking cognitive ability-like questions (e.g.

**`9.41` Robustness of climate change worries measurement**  
wave 16  
This experiment compares two versions of a single question on worry about climate change. Since the effects of climate change aggravate over time, it may mostly impact future generations.

**`9.42` Understanding of the long-term future**  
wave 16  
People’s perception of the long-term future plays an important role in the support for policies that address intergenerational challenges such as climate change, nuclear waste 207 storage and technological risks. Yet, many people find it difficult to think about the future beyond their own lifespan.

### Wellbeing and satisfaction (2)

**`9.18` What do the general population regard as “successful ageing”?**  
waves 9, 17  
Populations are ageing and there is substantial interest among researchers, policy makers and the general population as to what constitutes ‘successful ageing’. At Wave 9 and Wave 17, respondents were presented with a series of vignettes, each describing an older person.

*Assessed:* a substantive attitude, asked eight years apart

**`9.20` Presentation of response options in satisfaction questions**  
wave 9  
Recent findings suggest a significant drop in health satisfaction across waves of the Understanding Society survey. It is unclear if it is an actual change or artefact of the survey design.

### Health (5)

**`9.12` Measuring change in self-assessed disability**  
waves 6, 7  
This experimentation uses dependent interviewing to investigate the measurement of change in self-assessed measures of long-standing illness or disability.

**`9.24` Variations of the EQ-5D questions**  
wave 11  
This module aims to explore the differences in measurement of the widely used EQ-5D instrument using two developed variants. The EQ-5D is a 5-item instrument, designed by a consortium called EuroQol, to measure health-related quality of life.

*Assessed:* EQ-5D-3L and EQ-5D-5L variants, three groups

**`9.31` Comparison of ReQoL-10 to other scales**  
wave 14 · allocation `n_ff_req10cond`  
This experiment compared the 10-item Recovering Quality of Life questionnaire (ReQoL-10) to other health quality of life scales: the instrument (EQ-5D-3L) currently preferred by the National Institute for Health and Clinical Excellence (NICE) and the 12-item General Health Questionnaire (GHQ).

*Assessed:* ReQoL-10 against other scales, randomised order

**`9.36` Alcohol consumption**  
wave 15  
A review of Understanding Society questionnaires identified our usage of the Audit-C alcohol consumption questions differed somewhat from the questions the NHS uses for its measures.

**`9.43` Mental health questions comparisons**  
wave 16  
At IP16, a study was conducted to compare the mental health questions that had been deployed in Understanding Society over the years. The main survey questions about diagnoses of health conditions remained close to static for the first nine waves of the main survey.

### Work, money and expectations (6)

**`9.5` Measures of wealth**  
wave 3  
Wave 3 of the Innovation Panel was used to examine four different question designs for collecting the amount of money held in savings and investments: Table: Schematic design of Wave 3 measuring wealth experiment treatments Individual Reporting Financial Reporting Aggregate Amounts Group 1 Group 2 Itemized Amounts Group 3 Group 4 For all groups, an initial question asks respondents to report which specific types of savings or investments they hold.

*Assessed:* wealth asked aggregate vs itemised, 2x2 with who reports

**`9.11` Subjective expectations about the returns to higher education and decisions to attend university**  
waves 5, 8, 9 · allocation `e_ff_wageinfow5`  
This Wave 5 study tested ways of measuring perceptions about the economic returns to higher education, the costs involved, and experimentally tests the effects of information on actual decisions to attend university.

**`9.13` Associated Study: measuring time and risk preferences**  
waves 6, 7  
These data are from an Associated Study, which was approved and implemented as part of Wave 6 and Wave 7 data collection. Researchers using these data should acknowledge their source in any publications arising from analysis of the data.

**`9.22` Financial management within couples**  
wave 10  
This experiment compares two ways of asking couples about their financial management and perception of money ownership. The first condition asks only about how joint expenses are shared, with a response option included about shared money.

**`9.34` Marginal propensity to consume**  
wave 15  
A large and influential literature aims to measure consumers’ spending, saving and debt responses to income changes using questions of this kind. These studies aim to estimate how much consumers would spend out of each £1 change in income.

**`9.48` Labour market expectations**  
wave 17  
This experiment was intended to investigate respondents’ reporting of their labour market expectations.

### Family, care and the household (6)

**`9.9` Context effects in fertility decisions**  
waves 4, 5 · allocation `d_ff_fertw4`, `e_ff_fertw4`  
This Wave 4 experiment examines priming effects that impact on the respondent’s thoughts about expected total fertility. Fertility intentions can be highly dependent on wider context, such as partnership, age, actual childbearing, economic position and social pressures.

**`9.10` Vignettes: measuring partner satisfaction with division of household labour — VIGNETTE**  
waves 5, 6  
In Waves 5 and 6 respondents evaluated a set of vignettes related to the sharing of domestic work. The hypothetical arrangements varied along five dimensions: (1) paid work; (2) earnings; (3) presence of children; (4) housework allocations; and (5) use of paid help.

*Assessed:* respondents rate a described couple, not themselves

**`9.23` Non-resident parents and reasons for separation**  
wave 10  
Two question modules which have been used in the past in the Innovation Panel were adapted to capture information on non-resident parents.

*Assessed:* two versions of questions on non-resident parents and separation

**`9.35` Informal care**  
wave 15  
Measurement of informal care is problematic for a number of reasons. Caregiving is a complex concept and ontologically vague. Linguistically speaking, ‘care’ can refer to emotions and/or practices and, in common parlance, ‘caregiving’ tends to embody a nebulous set of activities.

**`9.39` Vignettes: measuring flexibility stigma - double whammy or femininity stigma — VIGNETTE**  
wave 16  
This experiment uses a vignette design to examine what the rise in homeworking practices mean with regards to gender inequality in the labour market.

*Assessed:* homeworking and gender inequality in the labour market

**`9.47` Identification of informal caregiving**  
wave 17  
The Understanding Society questionnaire includes questions designed to identify people who provide informal care and seeking to measure how much time they spend providing care. The existing questions adopt an approach of asking about informal care in general.

*Assessed:* standard vs activity-based identification of informal caregiving

### Technology and the future (1)

**`9.30` Vignettes: intentions to prepare for automation — VIGNETTE**  
wave 14 · allocation `n_ff_techworkw14`  
This experiment tested how what is communicated about the impact of automation affects the extent to which individuals are concerned about automation, are interested in re/upskilling to prepare for automation and intend to undertake actions accordingly.

*Assessed:* automation threat severity x timeframe, 2x2

### Sensitive questions (1)

**`9.17` Measuring sexual identity using direct and indirect questioning**  
waves 8, 9  
The identification of the best strategies to measure sexual orientation is needed to inform policy makers of experience of stigma and harassment suffered by the lesbian, gay and bisexual population.

*Assessed:* sexual identity asked directly vs indirectly

### Consent to data linkage (8)

**`9.6` Context of questions about consent to data linkage with administrative records**  
wave 4 · allocation `d_ff_conexpw4`  
Often the survey design decisions regarding how to obtain consent for administrative data linkage to social survey data are based on anecdotal accounts and common sense rather than empirical evidence.

*Assessed:* consent asked in context vs at the end, 2x2

**`9.21` Improving consent to link to the electoral register**  
waves 10, 11  
Two experimental conditions exist for this experiment. First is the medium of obtaining consent; the second involves the wording to the consent request. Respondents were first assigned to either an “opt-in” or “opt-out” consent condition.

**`9.25` HMRC data linkage consent experiment**  
waves 11, 15  
This experiment compares the impact of placement and wording of consent to data linkage to HMRC records. This consent question was originally carried in the mainstage of Understanding Society.

*Assessed:* HMRC linkage consent, easy vs difficult wording

**`9.29` LinkedIn consent**  
wave 14 · allocation `n_ff_lkincon`, `n_ff_lkinstat`  
This experiment tested different ways of asking respondents for consent to link data from their LinkedIn profiles to their Understanding Society survey data. LinkedIn is a platform that serves mainly as a professional networking site, including allowing individuals to search for jobs.

*Assessed:* LinkedIn consent, placement crossed with a motivational statement

**`9.33` Twitter consent**  
wave 15  
This module repeats the consent asked (non-experimentally) at IP10 (see 10.5 Consent to link Twitter data) and aims to look at the feasibilities and practicalities of linking social media (in particular Twitter) and survey data in a longitudinal context, and how they can be combined to improve the quality of both.

**`9.46` Consent decision process**  
wave 17  
This experiment aimed to test whether participants can be encouraged to think about a consent request more reflectively and whether this then affects the consent decision and related indicators of effort and understanding.

**`9.49` Indoor residential environment: consent for in-home sensor**  
wave 17  
Wave 17 included an overarching project to investigate people’s indoor residential environment and their energy use.

*Assessed:* consent to place in-home sensors

**`9.50` Domestic energy use: consent for smart meter data linkage**  
wave 17  
Wave 17 included an overarching project to investigate people’s indoor residential environment and their energy use.

### The form of the question rather than its content (7)

**`8.3` Impact of question wording and context on measuring change**  
waves 2, 3, 4 · allocation `b_ff_changew2`, `c_ff_changew2`, `d_ff_changew2`, `d_ff_changew4`  
Measuring how people’s social and economic circumstances change over time is a key purpose of household panel surveys. Levels of change are often overestimated in panel surveys.

*Assessed:* question wording and context, varied in words

**`8.4` Dependent interviewing wording**  
waves 3, 4, 5, 7 · allocation `c_ff_changew2`, `d_ff_changew2`  
At Wave 3, an experiment was included to examine the potential effects of different wording of dependent interview questions on responses. A split-ballot experiment contrasted two versions of phrasing.

**`8.5` Branched vs. unbranched rating scales for measuring attitudes**  
waves 3, 4, 5 · allocation `c_ff_branchingw3`  
The most common method for eliciting attitudes and beliefs in surveys is to employ rating scales where respondents are asked to choose the alternative that best describes their belief in, attitude towards or agreement with a statement.

**`8.8` Methods of reducing item non-response in web surveys**  
wave 6 · allocation `f_ff_itemnonw6`  
Elevated levels of item non-response in web surveys are a concern. To see whether the incidence of item non-response can be reduced, Wave 6 contained an experiment on 6 questions which showed relatively high levels of item non-response in past waves.

*Assessed:* prompts to reduce item non-response, varied in words

**`8.10` Replicating classic response order experiments across countries**  
wave 7  
This experiment contained a number of questions originally described and analyzed by Schuman and Presser (1981), as well as some new variants. The purpose of these questions was to examine whether the experiments can be replicated decades later and across countries.

**`8.11` Impact of response scale direction on responses**  
waves 7, 8  
In Wave 7, this set of experiments reflects two different, though related, research questions. The first, most general, research question is whether and how the direction of a response scale affects survey responses.

*Assessed:* answer scale direction reversed

**`8.14` Don’t know/prefer not to answer response presentation**  
wave 11  
This experiment explores the impact of the presentation of Don’t Know/Prefer Not to Answer response options in electronic self-completion questions.

## Verdict: `marginal`

Assessed and not decided. Each needs a ruling before it can move either way; `9.3` is the one to look at first, because it is otherwise ideal.

### Wellbeing and satisfaction (2)

**`9.2` Measuring satisfaction**  
waves 1-3, 5, 6 · allocation `b_ff_jobsatw2`, `b_ff_lifesatw2`, `c_ff_lifesatw3`, `f_ff_lifesatw3`  
The way you ask subjective evaluation questions (e.g., satisfaction) may have a big influence on the types of answers that you get. A series of experiments with question wording, format and placement have been run in Waves 1-3 and 5 of the IP.

*Assessed:* mixes scale points and labelling (buildable) with showcards and mode (not)

**`9.3` Reference groups in measuring satisfaction**  
wave 5 · allocation `e_ff_lifesatw5`  
At Wave 5, an experiment examined the comparison groups women have in mind when they answer questions about life satisfaction. Respondents were randomly allocated to one of four treatments groups.

*Assessed:* X08IVC: the condition asks the respondent to compare themselves to others of their own gender or education, naming their own persona category

### Work, money and expectations (2)

**`9.1` Measures of consumption and expenditure**  
waves 1, 6 · allocation `f_consexpw6`  
At Wave 1, an experiment was conducted to help develop efficient data collection instruments concerning household consumption. There is methodological concern about whether respondents consider all possible categories of expenditure to arrive at reports of household consumption.

*Assessed:* one condition uses a showcard to trigger recall, so part of the stimulus is visual

**`9.19` Benefits unit finances module**  
wave 9  
The first experiment presented respondents with an income summary screen, which displayed the person’s derived monthly net income based on their responses to previous answers in the survey. The second experiment was part of the Benefit Unit Finances module.

*Assessed:* a module redesign; needs checking that conditions share an outcome

### Family, care and the household (1)

**`9.32` Proxy nomination**  
wave 14 · allocation `n_ff_prxear`, `n_ff_prxver`  
This experiment tested different ways of asking respondents to nominate a proxy who could complete a short questionnaire on their behalf in future waves, if they themselves were unable to complete it or moved into an institution.

*Assessed:* proxy nomination; needs checking that a respondent answer is the outcome

### The form of the question rather than its content (4)

**`8.1` Subsetting the questionnaire content**  
waves 1-5  
In Wave 1, the Innovation Panel tested the feasibility of using random subsets of questionnaire content. The purpose was to explore the possibility of maximising survey content while minimising overall questionnaire burden for respondents.

*Assessed:* random subsets get different content, so there is no shared outcome to compare

**`8.9` Separating systematic measurement error components using MTMM in longitudinal studies**  
waves 7, 8, 9  
This experiment extended multi-trait multi-method (MTMM) designs beyond allowing for separation of random and common method variance. It identified three additional systematic variance components: acquiescence, social desirability, and extreme response.

*Assessed:* MTMM repeated-measures design; the condition is a measurement model, not a wording

**`8.12` Enhancing respondent engagement with the survey through tailored interesting questions**  
wave 7  
This experiment focuses on whether including extra questions that are of interest to the respondent improves their perception of the current survey and participation in the following wave.

*Assessed:* tailored question selection; needs checking that a shared outcome exists

**`9.7` Respondent preferences about mode of data collection**  
waves 4, 5, 6 · allocation `d_ff_group2`, `e_ff_group2`, `f_ff_group2`  
In Wave 4 a split-ballot experiment was used to collect information about the preferred mode of administration for the survey.

*Assessed:* the outcome is a preference about survey mode, not a substantive answer

## Verdict: `drop`

Listed compactly. The 28 procedural experiments share one reason and do not repeat it per row.

### Health (2)

| ID | Waves | Title | Why not |
|---|---|---|---|
| `9.15` | 8 | Validity of interviewer ratings of respondent health | the outcome is the interviewer's rating, not the respondent's answer |
| `9.27` | 12 | Reporting of height and weight | the condition is interviewer-asked vs self-completion, which is mode |

### The form of the question rather than its content (5)

| ID | Waves | Title | Why not |
|---|---|---|---|
| `8.2` | 1-3 | Showcards vs. no showcards | showcards are a visual stimulus, not text |
| `8.6` | 5, 6 | Smiley faces vs. text-based scales in child self-completion | smiley faces are a visual stimulus, not text |
| `8.7` | 6 | Quality of recall data with web vs. face-to-face | the condition is the interview mode, not words |
| `8.13` | 10 | Grid design in mobile surveys | mobile grid layout is a visual stimulus, not text |
| `8.15` | 12, 15 | Collecting mobile phone numbers | outcome is whether a phone number was given, not a survey answer |

### Physical measurement and apps (5)

| ID | Waves | Title | Why not |
|---|---|---|---|
| `9.8` | 5, 6 | Feasibility of directly measuring household energy use | meter readings; no text stimulus |
| `9.28` | 12 | Biomarker and sample collection | blood, blood spot and hair samples |
| `9.37` | 15 | Body Volume Index app and body measurements | body measurement app |
| `9.44` | 16 | Asking for child red book pictures | outcome is whether photographs were supplied |
| `9.45` | 16 | Spatial cognition mobile app game | mobile app game |

### Procedural — getting the respondent to take part (28)

> The condition is how the respondent was contacted, paid or interviewed, and the outcome is whether they took part at all rather than an answer they gave. There is no (persona, condition, outcome, response) row in that.

| ID | Waves | Title |
|---|---|---|
| `7.1` | All | Respondent incentives to encourage participation and web response |
| `7.2` | 7 | Conditional and unconditional incentives |
| `7.3` | 3 | Mixed mode experiments: telephone and face-to-face |
| `7.4` | 5-12, 15-17 | Mixed mode experiments: web and face-to-face |
| `7.5` | 4, 5, 6 | Paper vs CASI self-completion |
| `7.6` | 2 | Advance materials: letters vs. cards |
| `7.7` | 5 | Advance materials: content of advance letters |
| `7.8` | 6 | Targeted advance letters |
| `7.9` | 7 | Number of mailings between interviews |
| `7.10` | 4 | Different ways of asking respondents to register on participant website |
| `7.11` | 4 | Improving interviewer observations about characteristics of address |
| `7.12` | 4 | Effect of content of re-issue letter on refusal conversion |
| `7.13` | 4 | Early bird scheduling: encouraging respondents to call interviewer to schedule appointment |
| `7.14` | 9 | Targeted weekday invitation emails |
| `7.15` | 10 | Using prospect theory in wording of advance letters |
| `7.16` | 11 | Invitation letters for mixed mode survey |
| `7.17` | 11 | Spending Study 2 |
| `7.18` | 12 | Invitation to complete pre-interview blood pressure measure: information treatment vs pro-social appeal |
| `7.19` | 13 | Fieldwork compression experiment |
| `7.20` | 13 | Event triggered data collection |
| `7.21` | 13,15 | Consent to send survey questions by SMS |
| `7.22` | 13 | Wellbeing app study |
| `7.23` | 14 | Asking for Living Apart Together partner details |
| `7.24` | 14 | Contact protocols for IP14 refreshment sample |
| `7.25` | 16 | PERKs for unconditional incentives |
| `7.26` | 16 | Youth online survey |
| `7.27` | 16 | Test of Government logo on envelopes for continuing sample |
| `7.28` | 17 | Youth survey invite mailing |

