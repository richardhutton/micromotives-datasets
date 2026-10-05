# Innovation Panel — pull & reconstruct checklist

Practical guide to turning the **Understanding Society Innovation Panel** into
`(persona, condition, outcome, response)` rows for SocSci-UK. Follows Understanding
Society data conventions — **confirm exact variable names against each wave's data
dictionary**, since some shift over time. Access: UKDS, safeguarded (registration +
EUL; no redistribution). See master doc §5e.

## 1. Download (UKDS)

- **SN 6849** — *Understanding Society: Innovation Panel, Waves 1–17* (catalogue
  record `study/7083`). Get **Stata `.dta`** or **SPSS `.sav`**.
- **Docs bundle:** Innovation Panel **User Guide** (`6849_…user_guide.pdf`), the
  per-wave **"Results from methodological experiments"** working papers, and the
  **questionnaires / data dictionaries**. These name each experiment's **allocation
  variable** and the arm wordings — the map you build from.

## 2. File layout (UKHLS convention)

*Measured against the downloaded bundle on 5 Oct 2026, not inferred.*

- Wave-prefixed by letter: `a_` = IP1 (2008), `b_` = IP2, … `q_` = IP17 (2024).
  17 waves, 279 files, ~1 GB, in `data/raw/ukds_6849/` (gitignored).
- **Answers:** `{w}_indresp_ip` — one row per adult. Grows from **678 columns in
  2008 to 2,194 in 2024** as content accumulates.
- **Conditions:** `{w}_hhsamp_ip` — every sampled address, and the allocation
  variables, prefixed `{w}_ff_`. **This is not the file the answers are in**, so
  every build reads two files and joins them on `{w}_hidp`. That is new: all 13
  Harvard studies found the condition in the same file as the answer.
- Others: `{w}_hhresp_ip` (household answers), `{w}_indall_ip` / `{w}_indsamp_ip`
  (everyone enumerated, including non-respondents), `{w}_egoalt_ip` (one row per
  *pair* of people in a household — who is whose partner, parent, sibling),
  `{w}_income_ip` (one row per income source), `{w}_youth_ip` (ages 10–15).
- Every variable is wave-prefixed (`b_sex`, `b_jbstat`). **`_dv` = derived**
  (cleaned/harmonised — prefer these). **`_ff_` = fed forward** from an earlier
  wave, which is why wave 17's household file carries 172 allocation variables
  going back to wave 2 — a cumulative history, not 172 experiments in 2024.
- **`pidp` = cross-wave person ID.** 8,078 people, 41,086 person-wave rows, mean
  **5.09 waves per person**, 216 people in all 17. **Hash it, never store it
  raw** — it links to the whole of Understanding Society.
- Missing codes, consistent across all 279 files and **not** declared missing in
  Stata, so they arrive as ordinary numbers: `-1` don't know, `-2` refused,
  `-7` proxy, `-8` not applicable/routed, `-9` missing by error.
- **Do not use `pandas.read_stata`.** It silently falls back to latin-1 on these
  files (`UnicodeWarning: ... fallback encoding of latin-1 is being used`), which
  is the PZB01G mojibake bug by default. `sources/spss.read` reads them as clean
  UTF-8 with full value labels; verified on waves a, i and q.

## 3. Find the experiments (allocation variables)

**Already done once, at desk level:** `data/catalog/innovation_panel_experiments.json`
holds all **93** experiments the User Guide catalogues, rendered to
`docs/UKDS_UNBUILT.md` — 44 pass screening (63 experiment-waves), 9 need a
ruling, 40 are out. 37 of the 93 have their allocation variable named by the
guide itself and recorded in `allocation_vars`.

- **Primary:** the User Guide's §6.1 overview table and each experiment's own
  section, which usually names the variable outright — e.g. 9.3: *"The variable
  `e_ff_lifesatw5` on the record `e_hhsamp_ip` controls allocation to versions of
  this question"*, followed by its four codes and the outcome variables.
- **Also:** the per-wave **"Results from methodological experiments"** working
  papers, free from `understandingsociety.ac.uk`, one per wave from 2008 to 2023.
  These carry the **published numbers to verify a build against**, which is the
  project's whole QC method and the reason TLT65Z had to be dropped.
- **Cross-check in data:** read `.dta` metadata with `pyreadstat`, grep variable
  **labels** for `experiment`, `random`, `alloc`, `treat`, `group`, `split`,
  `version`/`ver`, `assigned`, or the experiment short name. Allocation var is
  usually in **`{w}_hhsamp_ip`**, not `{w}_indresp_ip` — household-level
  randomisation dominates, though ~293 person-level allocations exist across the
  17 waves and sit in the person file directly.
- **Randomisation is per household**, so everyone in a house saw the same
  version. 527 of 1,454 households in wave 6 hold two adults, up to seven. People
  in one household are **not independent rows**.
- Experiments within a wave are deliberately **orthogonal or independently
  randomised**, so several can be built from one wave without confounding.
- **The allocation flag is retained; the condition TEXT is not.** The data gives
  a group number. The wording lives only in that wave's questionnaire PDF
  (`6849_ip_wave_*_questionnaires.pdf`, 18 of them). **No questionnaire wording,
  no condition, nothing buildable** — and whether each of the 44 has usable
  wording there is the single largest unknown left.

## 4. Persona spine (`{w}_indresp_ip` + `xwavedat_ip`, prefer `_dv`)

| persona field | likely variable |
|---|---|
| age | `{w}_dvage` / `{w}_age_dv` |
| sex/gender | `{w}_sex` |
| education | `{w}_hiqual_dv` |
| income | `{w}_fimnnet_dv` (net monthly) or bands |
| ethnicity | `{w}_racel_dv` / `{w}_ethn_dv` |
| marital | `{w}_mastat_dv` |
| employment | `{w}_jbstat` |
| region | `{w}_gor_dv` (Govt Office Region) |
| social grade / class | `{w}_jbnssec_dv` (NS-SEC) |
| party ID | `{w}_vote*` (varies by wave) |

## 5. Reconstruct to (P, c, o, r)

For an experiment in wave `w`:
1. Keep respondents where the **allocation var A** is non-missing (in the experiment).
2. **persona** = demographic vars above → text.
3. **condition** = A's value → **join to the arm's stimulus wording** from the
   questionnaire/User Guide (wording is *not* in the data — the manual "part 2").
4. **outcome** = the outcome question wording (questionnaire).
5. **response** = the outcome variable value (integer).
6. Row key = `(pidp, wave, experiment)`. Because `pidp` links waves, attach
   **prior-wave answers** as history for the forecasting mode.

## 6. Gotchas

- **Missing-value codes are negative:** `-1` DK, `-2` refused, `-7` proxy, `-8`
  inapplicable, `-9`/`-10`/`-11`/`-20`/`-21` various missing. Strip before making
  integer responses (UKHLS equivalent of BES's `9999`).
- **Arm→text join is manual** — data gives the arm number; wording is in the
  questionnaire. Budget for it.
- **Weights** (`{w}_*_xw`) — use only for population-distribution matching, not raw
  training rows.
- **Modest N per experiment** (~1,500 households, often a subset) — fine given the
  ~10% saturation finding; not US-scale.
- **Licence:** safeguarded EUL — research use fine, no redistribution.

## 7. First target

Do **one substantive experiment end-to-end** as the template (User Guide's
substantive list — e.g. **immigration vs public-services**, or the **EQ-5D health**
variants), then generalise the melt across waves.

## 8. Next (turn generic → exact)

Once SN 6849 is pulled, share a wave's variable list (or the User Guide's
experiment table) → the generic recipe becomes an **exact variable-name mapping**
for a specific experiment.
