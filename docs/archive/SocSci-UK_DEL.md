# Development Engagement Lab (DEL) — enumeration

What it is: a YouGov-fielded research programme (France, Germany, Great Britain,
US) on foreign aid, humanitarian, climate and related topics, 2020–2025. All
data is on Harvard Dataverse, **CC0** (public domain). **Great Britain is a
separate file** in every deposit, so no country filtering is needed. The persona
is the **same YouGov profile block** as our core studies (`age, gender,
region_GOR, socialgrade_cie, education_level, ethnicity_new`) — no new crosswalk.

Three deposit types:
- **Tracker** — repeated cross-sections. Observational (no experiments).
- **Panel** — same people over time. Longitudinal *and* holds experiments.
- **Sandbox** — the experiment programme (split-ballots, conjoints, list experiments).

## GB samples and experiments (from the data files)

| Deposit | GB respondents | Embedded experiments* | Type |
|---|---|---|---|
| Tracker 2020 (W1, W2) | 1,036 · 1,705 | 0 | observational |
| Tracker 2021 (W3, W4) | ~1,705 each | 0 | observational |
| Tracker 2022 (W5, W6) | ~1,690–1,882 | 0 | observational |
| Tracker 2023 (W7, W8) | 1,693 · 2,000 | 0 | observational |
| Tracker 2025 (W11, W12) | 2,229 · 2,241 | 0 | observational |
| Panel 2020 (W2) | 8,079 | 1 | **time + experiment** |
| Panel 2021 (W3) | 8,281 | **8** | **time + experiment** |
| Panel 2022 (W4) | 8,008 | 5 | **time + experiment** |
| Panel 2023 (W5) | 8,018 | 3 | **time + experiment** |
| Panel 2025 | — | — | GB file not found (different naming) |
| Sandbox 2020 (Apr, Jul) | 1,761 · 2,009 | 0 · 1 | experiments |
| Sandbox 2021 (Jun) | 3,023 | 0* | experiments |
| Sandbox 2022 (Jun) | 2,187 | 0* | experiments |
| Sandbox 2023 (Feb) | 2,007 | **9** | experiments |
| Sandbox 2023 (Oct) | 3,639 | 0* | experiments |

\* **Experiment count = split-ballot experiments only.** It does NOT count
conjoints or list experiments, which DEL Sandboxes also use under other column
names. So a "0" means "no split-ballot experiments found" — not "no
experiments." The 0-marked Sandboxes still need a conjoint/list-experiment check.

## What DEL adds

- **Non-party topics** — aid, humanitarian, climate, ODA, feminism — with
  money/donation outcomes (e.g. the Wave-3 NGO donation conjoint).
- **Panels give stimulus + time in one source** (~8,000 GB people per wave).
- **Persona already matches the core** — merges with no new mapping.
- Questionnaire (`Survey.docx`) and codebook (`Codebook.xlsx`) in every deposit,
  so exact stimulus wording per arm is available.

## Open next

1. Conjoint/list-experiment check on the 0-split Sandboxes and the Panels.
2. Locate the Panel 2025 GB file (naming differs).
3. Pull one experiment end-to-end as a worked example (persona + arm + outcome).

## Sources (all Harvard Dataverse, CC0)

Data paper: Nature Scientific Data `s41597-025-05135-0`.
Trackers: 2020 `10.7910/DVN/L9DUKN` · 2021 `PEH21C` · 2022 `L2STP0` · 2023 `XH4K0E` · 2025 `B3EG50`.
Panels: 2020 `KWTWCF` · 2021 `CCUZYI` · 2022 `WZPNNU` · 2023 `FTRXFO` · 2025 `UML4V5`.
Sandboxes: 2020 `LLM8VW` · 2021 `DUUPRY` · 2022 `ELT7M0` · 2023 `XZ1XUZ`.
(All prefixed `10.7910/DVN/`.)
