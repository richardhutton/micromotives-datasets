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

- Wave-prefixed by letter: `a_` = IP1, `b_` = IP2, … `q_` = IP17.
- Main file per wave: **`{w}_indresp_ip`** — one row per adult, all answers
  (personas, outcomes, **and allocation flags**). Support: `{w}_hhresp_ip`
  (household), `xwavedat_ip` (stable cross-wave vars).
- Every variable is wave-prefixed (`b_sex`, `b_jbstat`). **`_dv` = derived**
  (cleaned/harmonised — prefer these).
- **`pidp` = cross-wave person ID** → links a person across waves = the
  time/forecasting axis for free.

## 3. Find the experiments (allocation variables)

- **Primary:** User Guide experiment table + per-wave working papers list, per
  wave: experiment name → **allocation/randomisation variable** → outcome
  variable(s) → arm wordings.
- **Cross-check in data:** read `.dta` metadata with `pyreadstat`, grep variable
  **labels** for `experiment`, `random`, `alloc`, `treat`, `group`, `split`,
  `version`/`ver`, `assigned`, or the experiment short name. Allocation var is
  usually in `{w}_indresp_ip`.
- **Key advantage over BES:** the IP is built for experiments, so the allocation
  flag **is retained** — no "condition stripped" problem (confirm per experiment).

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
