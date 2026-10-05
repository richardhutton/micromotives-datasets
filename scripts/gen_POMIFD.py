#!/usr/bin/env python3
"""Derive POMIFD's 336-argument paired-comparison conditions from the data.

POMIFD (Blumenau & Lauderdale, "The Variable Persuasiveness of Political
Rhetoric", AJPS 2022, doi:10.1111/ajps.12703) fielded Experiment 1 to YouGov's
UK online panel in June 2019: 3,317 respondents each saw 4 of 12 policy
issues; for each, two of that issue's 28 arguments (14 rhetorical elements x
2 positions, for/against) were shown together and the respondent said which
was more persuasive, or that the two were about the same. 3,317 x 4 = 13,268
observations, confirmed exactly from `experiment_one.sav` below. **Build
Experiment 1 only** -- see the "EXPERIMENT 2 IS OUT OF SCOPE" section.

THE LICENCE POSITION -- read before touching anything else
------------------------------------------------------------
This deposit's Dataverse `license` field is literally null. Nothing built
from this recipe may ever be published, shared, or sent to any external
service (no LLM API -- `embed.py`'s CLEARED gate does not list POMIFD and
must not). It is used for the project owner's private research only, on the
basis recorded in full under `uk_dataverse_provenance.json`'s
`POMIFD.use_basis`: the deposit's own terms invite contacting the depositor
before use, rich emailed Jack Blumenau (UCL, the deposit's datasetContact) on
5 Oct 2026 before anything was fetched, and the standing commitment is that
if the authors object, the build and the raw deposit are deleted. Read
`use_basis` in full before changing anything about this status. The recipe's
own `licence:` field restates this; never write "CC0" anywhere near this
study.

THE FETCH -- A TRAP THIS PROJECT HAS NOW HIT, AND A SECOND HAZARD FOUND HERE
-------------------------------------------------------------------------------
`experiment_one.tab` reports `originalFileFormat: application/x-spss-sav` --
Dataverse's own label-stripped derivative of an uploaded `.sav`, exactly the
`QQM5MC` mistake and the one `RJTVG8` caught. Fetched with `?format=original`
instead, giving `experiment_one.sav` (3,317 x 56, read via `sources.spss`).
`canonical_sentences_v2.tab` (original: plain CSV), `elements.tab` (original:
`.xlsx`) and `issue_prompts.tab` (original: `.xlsx`) were likewise fetched
with `?format=original` -- none of these three loses value labels the way a
`.sav`/`.dta` ingest does, but the SERVED `.tab` would still have reformatted
them through Dataverse's own tab-delimited ingest, which is a needless second
hop away from what the depositors actually uploaded.

**A second hazard, found and avoided, not inherited from precedent**:
`scripts/fetch_dataverse.py`'s `main()` was NOT used to fetch this deposit,
for two independent reasons, either one sufficient on its own:

1. It downloads every file the API lists for a candidate with no
   size/pattern filter. This deposit ships ten `posterior_*.Rdata` files
   (28MB-80MB each, ~480MB total) that the task brief explicitly forbids
   downloading, plus `argument_fixed_effect.Rdata` (3.4MB, also model
   output). A plain run would have pulled all of them.
2. `main()` does `prov[code] = {...}` -- a full REPLACEMENT of the
   provenance entry, not a merge. `data/catalog/uk_dataverse_provenance.json`
   already carries a hand-authored `POMIFD` entry with `status`,
   `status_reason`, `use_basis` and `redistributable` -- fields `main()`
   never writes. Running it would have silently deleted all four, including
   the standing commitment to delete the build on author objection. (It
   would also have been a no-op by itself: `uk_dataverse_candidates.csv`
   still marks POMIFD `blocked-licence`, which `main()`'s own
   `candidates()` filters out -- so the hazard would only bite a future
   maker who also flips that status to `NEW-confirmed` to make the fetch run
   at all, at which point it bites silently.)

This build instead used a one-off script (same Dataverse API calls,
same `?format=original` logic, an explicit skip-list for
`posterior_*`/`argument_fixed_effect.Rdata`/`liwc_dictionaries.Rdata`/
paper-writing artefacts (`.tex`, `.bib`, `.Rmd`)/`experiment_two.sav`) and
touched NEITHER `uk_dataverse_candidates.csv` NOR the provenance JSON at
fetch time. `uk_dataverse_provenance.json`'s `status` is updated to `built`
by hand after this build passes QC, with `licence`/`status_reason`/
`use_basis`/`redistributable` left exactly as recorded. A future maintainer
extending `fetch_dataverse.py` to a size/pattern skip-list and a merge-not-
replace provenance write would fix this for every study, not just this one.

WHAT THE 24 FETCHED CSVs ACTUALLY ARE -- THE BRIEF'S OWN HEDGE, RESOLVED
-----------------------------------------------------------------------------
The task brief hedged that the twelve large `N_<Issue>.csv` files "may be
posterior draws rather than data". They are not. `README.txt` names them
directly: "We implemented the survey instrument by providing pre-randomised
draws from our desired treatment distributions to the survey vendor... found
in policy_csvs/" -- and `01_experiment_1.R`'s own reshape confirms it
mechanically: `prompts[[selected_policies[x]]][selected_rows[x],]` looks up
row `maxdiff_version_pick_p` (1..756) of policy `p`'s CSV to recover the
respondent's actual pair. These are the COMPLETE, EXHAUSTIVE design matrix
for Experiment 1 -- 756 rows per policy = every unordered pair of that
policy's 28 arguments, in BOTH left/right orders (C(28,2) x 2 = 378 x 2 =
756, confirmed below) -- not a posterior sample of anything. This generator
reads these twelve files (`POLICY_FILES` below) and nothing else for
condition text.

The twelve SMALL `<Issue>.csv` files (~30KB, no numeric prefix) are a
DIFFERENT thing entirely: README.txt's own `strong_weak_argument_sets/`
directory, used ONLY by Experiment 2 (the validation study -- `Codebook.pdf`
documents `policy_X_pro`/`policy_X_con` as referencing exactly this
directory, "Missing = 99 or 999", a different missingness scheme from
Experiment 1's). Fetched for completeness; not read by this generator.

EXPERIMENT 2 IS OUT OF SCOPE
-------------------------------
`experiment_two.sav` (not fetched -- see the skip-list above) and
`02_experiment_2.R` (fetched, read) are a SEPARATE out-of-sample validation
study: 6,600 respondents, fielded Feb 2020, 13,200 responses. Its outcome is
different in kind -- "Are you for or against <policy issue>?" (For/Not
sure/Against, `prompt_2.png`), not argument persuasiveness -- and its
treatment is a COMBINED multi-sentence "strong"/"weak" argument built by
concatenating several of the same 336 elements' sentences (`prompt_2.png`'s
Heathrow "For" card visibly concatenates the Common-sense and Cost/benefit
sentences from Table A1 into one paragraph), not a single element's text. If
ever built, it would need its own recipe (`POMIFD_experiment_2`) keyed off
`policy_X_pro`/`policy_X_con` against `strong_weak_argument_sets/`, entirely
independent of everything below.

WHERE THE CONDITION TEXT COMES FROM, AND WHAT WAS STRIPPED
---------------------------------------------------------------
`policy_csvs/<N>_<policy>.csv` is the fielded instrument's own pre-randomised
draw file -- the thing YouGov actually rendered -- not a secondary
reconstruction. `text_one`/`text_two` are transcribed VERBATIM, never
retyped from the appendix (see the cross-check below). `<b>...</b>` tags
(policy_csvs' own `prompt` column) and markdown `**...**` (the `.sav`'s own
`sc1`..`sc12` value labels, and `issue_prompts.xlsx`'s `Prompt_*` columns)
are stripped: both are confirmed, against `for_against_screen.png`, to mark
on-screen BOLD STYLING, not literal characters any respondent read -- the
screenshot's "arguments for and against" and "Argument **one**" render as
plain bold text, no asterisks or angle brackets visible. The underlying
WORDS are identical whichever markup convention wrote them (confirmed: the
`.xlsx`'s `Prompt_pro_pro` and the CSV's own `prompt` column differ only in
`**`/`<b>`, word for word, for every one of 36 distinct prompts checked). One
genuine non-breaking space (`\xa0`, in the overseas-aid Pro argument, "our
moral duty") is normalised to a plain space per docs/CONVENTIONS.md's
typography rule. Nothing else is touched: a source typo is kept exactly as
written. `policy_id=12` (sugar tax), `pair_id` with `element=Appeal to
fairness`, `pro_con=Pro` reads "A sugar tax is important because it helps to
all children a fair chance of a healthy life." (missing "give") in
`policy_csvs`, `canonical_sentences_v2.csv` AND the published appendix
(Table A12) identically -- genuinely the source's own wording, confirmed
independently in all three places, not a transcription slip anywhere in this
pipeline.

APPENDIX CROSS-CHECK -- SPOT-CHECKED, NOT EXHAUSTIVE, ZERO DIVERGENCE FOUND
--------------------------------------------------------------------------------
`data/raw/POMIFD/paper/working_paper.txt` (the author's self-archived 72-page
working paper, `pdftotext -layout` extraction of
https://benjaminlauderdale.net/files/papers/2022BlumenauLauderdale.pdf --
fetched because the UCL Discovery copy the task brief names is the 16-page
Wiley-typeset journal article ONLY, with the appendix hosted as separate
Supporting Information this build could not retrieve; both PDFs are kept
under `data/raw/POMIFD/paper/`) contains Tables A1-A12, "Treatment texts",
one per policy, all 336 arguments, matching the brief's "pp. 20-34"
description. Spot-checked by eye: all 4 argument pairs appearing in
`for_against_screen.png` (Table A1, Heathrow -- Ad hominem and Appeal to
authority, both positions, 4 texts) and the complete 28-argument Table A12
(Sugar tax, including the "helps to all children" typo above) against
`policy_csvs/1_...csv` and `policy_csvs/12_...csv`. Zero wording divergence
found in this sample. The 14 element NAMES differ in SURFACE form only
between `elements.xlsx`'s long descriptive names and the data's own short
names used in `policy_csvs`/`canonical_sentences_v2.csv` (e.g. "Costs vs
benefits arguments" vs "Cost/benefit") -- declared in `ELEMENT_NAME_MAP` and
asserted in `load()`, the same kind of naming-only divergence RJTVG8
documented for its own appendix table. This is a SAMPLE, not an exhaustive
336-argument diff; a systematic parse of all 12 appendix tables was judged
not worth the PDF-table-parsing risk for a cross-check this brief asked to be
done "on a sample".

RESPONSE CODING -- THE DATA'S OWN VALUE LABELS DISAGREE WITH Codebook.pdf
--------------------------------------------------------------------------------
`Codebook.pdf` documents `sc_X` as 1=one-more-persuasive, 2=about-the-same,
3=two-more-persuasive. `experiment_one.sav`'s OWN embedded value-label
dictionary (`ds.value_labels["sc1"]`, identical on sc1..sc12) says something
different: 1=one-more-persuasive, 2=TWO-more-persuasive, 3=about-the-same.
Per docs/CONVENTIONS.md's source-authority ruling (the fielded data is the
authority over a secondary document), this generator follows the `.sav`'s
own labels, asserted in `load()` against exactly this dictionary so a
re-fetched deposit that silently reverted to the codebook's order would fail
loudly rather than flipping two-thirds of the scale. `for_against_screen.png`
confirms the on-screen BUTTON ORDER (one / same / two, left to right) but
carries no codes, so it cannot adjudicate which CODE means what -- only the
`.sav`'s own dictionary can, and that is what is used. Flagged here because
it is exactly the kind of divergence a maker who trusted only the PDF
codebook would get backwards silently.

MISSING-CODE AUDIT -- DECLARED SENTINELS ARE UNIVERSALLY UNUSED HERE
----------------------------------------------------------------------------
Every sentinel code this deposit declares anywhere (`8`, `9`, `98`, `99`,
`998`, `999`, `-8`, `-9` -- "Skipped"/"Not Asked"/"N/A") was checked against
the POOLED observed values of every variable this generator touches, in
BOTH directions. None occurs even once: genuine non-response/non-selection
is represented as a blank cell throughout this deposit, which `_is_blank()`
already handles with nothing to declare. This is the opposite of `6MRVOM`'s
997-as-slider-value finding, and worth recording precisely because the
pattern could easily have gone the other way.

What DOES occur, and is a real non-answer disguised as an in-range code, is
a genuine "Don't know"/"Prefer not to say"/"Refused" RESPONSE OPTION a
respondent can affirmatively select -- these are blanked in Python, in
`PERSONA_NON_ANSWER_CODES` below, BEFORE the wide CSV is written (the same
pattern `RJTVG8` uses for its `education` field), not via the recipe's
`persona_missing`, which is a no-op once persona values are pre-resolved to
text (see "WHY A DERIVED WIDE CSV" below -- `_as_code()` on a text label
returns `None`, so a numeric-code-keyed `persona_missing` declaration could
never match). Audited: `profile_education_level` 19/20 ("Don't know"/"Prefer
not to say") DO occur; `profile_gross_household` 16/17 DO occur;
`ethnicity_new` 19 DOES occur; `politics_scale_profile_update` 8 ("Don't
know") DOES occur; `voted2017` 99 ("Don't know") DOES occur.
`profile_socialgrade_cie`'s declared 7="Refused"/8="Unknown" do NOT occur
(only codes 1-6 are ever observed) -- declared defensively anyway, since a
declaration that currently cannot be exercised is exactly the state ledger
finding #101 warns is hardest to verify, and dropping it would be the
dangerous direction.

**The Ledger-101 echo, found here too**: `profile_GOR` declares code 12 =
"Northern Ireland" and code 13 = "Non UK & Invalid". Neither occurs ONCE
across all 3,317 respondents -- only codes 1-11 are ever observed. This is
the exact shape of ledger finding #101 (a declared region level with zero
rows), and it is kept in the declared code/label mapping regardless, not
deleted -- a genuine UK YouGov panel quota sample excluding Northern Ireland
is plausible (several UK panels quota on Great Britain only) and the
zero-occurrence fact is stated here explicitly so a later reader does not
mistake an absence of NI respondents for a bug in this generator.

`pastvote_2017`'s own value-label dictionary separately declares BOTH code 8
and code 9 as "N/A" (a duplicate label for two different codes, distinct
from the TRUE blank/NaN that 595 of 3,317 respondents carry for this
variable) -- noted for completeness; not consequential here because
`pastvote_2017` is excluded from persona entirely (see the domain ruling
below).

PERSONA -- THE DOMAIN RULING THE BRIEF ASKED FOR, STATED EXPLICITLY
-------------------------------------------------------------------------
The paper's own covariate analysis (the `posterior_covariate_correlation_*`
filenames) is by age, education, gender, attention, EU referendum vote and
2017 vote. All six are found in `experiment_one.sav`: `age`, `profile_
education_level`, `profile_gender`, `political_attention`, `pastvote_EURef`,
`pastvote_2017`.

**`pastvote_EURef` (euvote) and `pastvote_2017` (vote17) are EXCLUDED.** The
outcome here is which political ARGUMENT a respondent finds persuasive,
across 12 issues that include Renewing Trident, spending 0.7% of GDP on
overseas aid and fracking -- named explicitly in the task brief as issues
where a person's referendum/party vote sits close to a prediction of which
side's argument they would find persuasive. Predicting argument
persuasiveness from EU-referendum or party vote is retrieval of a correlated
political identity, not inference about rhetorical persuasion from who
someone IS -- the same reasoning `EFXNLX` applied to `eu_referendum_vote` and
`6MRVOM_brexit_scenario` applied to `pastvote_2015` (its outcome was party
choice). Both are left out of `PERSONA_SPEC` entirely.

**`voted2017` (did you vote in the 2017 general election -- Yes/No/Don't
know) is KEPT.** This is turnout, not vote CHOICE: it measures civic
participation, carries no information about WHICH side or party a
respondent favours on any of the 12 issues, and is not in the outcome's
domain the way `pastvote_2017` is. Mapped to `extra["voted_2017"]`.

**`politics_scale_profile_update` (general 7-point left-right
self-placement) is KEPT, mapped to `ideology`.** It is a general orientation
rather than a specific electoral choice tied to one of the 12 issues --
every other UK study in this corpus that excludes a specific vote-choice
variable keeps a general ideology scale where one exists, and this follows
the same line.

Six further demographics are kept as ordinary, non-outcome-adjacent
attributes: `profile_gender`, `profile_GOR` (region), `profile_
gross_household` (income band), `profile_marital_stat`, `profile_
socialgrade_cie` (social grade), `profile_work_stat` (employment),
`ethnicity_new`. `W8` (YouGov's own sampling weight), `starttime`/`endtime`
and `m_m_rand_all_rnd` (the randomisation spec string) are excluded as
non-persona, matching `PMV0TG`'s exclusion of its own `weights` column.

WHY A DERIVED WIDE CSV, AND WHY PERSONA IS PRE-RESOLVED TO TEXT IN IT
--------------------------------------------------------------------------
Each respondent answers up to 4 of 12 POSSIBLE policy slots, each slot's
condition keyed by TWO things at once -- which policy (1-12) and which of
that policy's 756 pre-randomised draws (`maxdiff_version_pick{p}`). The
pipeline's `Condition.by_raw()` looks arms up by a tuple of VALUES, not
variable names, so a per-outcome `condition_var` naming a DIFFERENT column
per policy slot still resolves correctly against one shared `condition.arms`
list -- provided the VALUE itself encodes which policy it belongs to (a
`pick` of 412 means something different for policy 3 than for policy 7).
`draw_p{p} = p * 1000 + pick` is exactly that encoding (`pick` never exceeds
756, so the thousands digit is never ambiguous), computed once per slot and
written as a single combined column -- the same reason `RJTVG8`/`PMV0TG`
each write their own derived wide file rather than reading the deposit
directly.

Persona is pre-resolved to its TEXT label (via `ds.label()`) before being
written to the wide CSV, exactly as `RJTVG8.build_wide()` does, and for the
same reason: the wide CSV is read back through `sources.delimited` (a plain
CSV has no value-label dictionary of its own), and `recipe.persona_missing`
can only match a NUMERIC code -- a text cell fails `_as_code()` and
resolves to `None`, so a `persona_missing` declaration keyed on it would
silently never fire. Non-answer codes are therefore blanked here, in
`PERSONA_NON_ANSWER_CODES`, before any text is written -- this recipe's own
`persona_missing:` is correspondingly empty, and that emptiness is
INTENTIONAL, not an oversight.

    uv run python scripts/gen_POMIFD.py --check   # agree with the recipe?
    uv run python scripts/gen_POMIFD.py --write   # regenerate wide CSV + arms/outcomes
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from micromotives_datasets.sources import spss

REPO = Path(__file__).resolve().parents[1]
RECIPE = REPO / "recipes" / "POMIFD.yaml"
RAW = REPO / "data" / "raw" / "POMIFD"
SAV = RAW / "experiment_one.sav"
CANON = RAW / "canonical_sentences_v2.csv"
ELEMENTS_XLSX = RAW / "elements.xlsx"
WIDE = RAW / "experiment_one_wide.csv"

N_RESPONDENTS = 3_317
N_OBS = 13_268
N_ISSUES = 12
N_ELEMENTS = 14
N_ARGUMENTS = 336
N_PAIRS_PER_ISSUE = 756  # C(28, 2) x 2 orders -- every unordered pair, both left/right
N_ARMS = 5_579  # distinct RENDERED pairs actually drawn, after the Arm.raws dedup below

POLICY_FILES: list[tuple[int, str]] = [
    (1, "1_Building_a_third_runway_at_Heathrow.csv"),
    (2, "2_Closing_large_retail_stores_on_Boxing_Day.csv"),
    (3, "3_Extending_the_Right_to_Buy.csv"),
    (4, "4_Extension_of_surveillance_powers_in_the_UK.csv"),
    (5, "5_Fracking_in_the_UK.csv"),
    (6, "6_Nationalisation_of_the_railways_in_the_UK.csv"),
    (7, "7_Quotas_for_women_on_corporate_boards.csv"),
    (8, "8_Reducing_the_legal_restrictions_on_cannabis_use.csv"),
    (9, "9_Reducing_university_tuition_fees.csv"),
    (10, "10_Renewing_Trident.csv"),
    (11, "11_Spending_0.7%_of_GDP_on_overseas_aid.csv"),
    (12, "12_Sugar_tax_in_the_UK.csv"),
]

# elements.xlsx's long descriptive names -> the short names natively used in
# canonical_sentences_v2.csv / policy_csvs' own element_one/element_two
# columns (what actually renders into `factors`). Asserted equal, as a SET
# under this mapping, in `load()` -- see the module docstring's appendix
# cross-check section.
ELEMENT_NAME_MAP: dict[str, str] = {
    "Costs vs benefits arguments": "Cost/benefit",
    "Appeals to expertise": "Appeal to authority/endorsement",
    "Metaphor/figure of speech": "Metaphor",
    "Side-effects": "Side Effects",
    "Public opinion": "Public Opinion",
}

# (persona field name, source .sav variable, non-answer codes to blank).
# Applied in Python before the wide CSV is written -- see the module
# docstring's "WHY A DERIVED WIDE CSV" section for why this cannot live in
# the recipe's `persona_missing` once persona is text-resolved.
# pastvote_EURef / pastvote_2017 are deliberately absent (domain ruling).
PERSONA_SPEC: list[tuple[str, str, set[int]]] = [
    ("age", "age", set()),
    ("gender", "profile_gender", set()),
    ("education", "profile_education_level", {19, 20}),
    ("region", "profile_GOR", set()),
    ("income", "profile_gross_household", {16, 17}),
    ("marital_status", "profile_marital_stat", set()),
    ("social_grade", "profile_socialgrade_cie", {7, 8}),
    ("employment", "profile_work_stat", set()),
    ("ethnicity", "ethnicity_new", {19}),
    ("ideology", "politics_scale_profile_update", {8}),
    ("political_attention", "political_attention", set()),
    ("voted_2017", "voted2017", {99}),
]

# Explicit dtypes for reading the wide CSV back. Needed because
# `political_attention` happens to have zero missing values and every value
# is a digit string ("0".."10") -- without this, `pd.read_csv`'s own type
# inference silently reads it back as int64 instead of the text column
# `build_wide()` writes, and an otherwise-identical round trip would report
# as DIFFERENT for a reason that has nothing to do with the data.
_TEXT_COLS = [f for f, _, _ in PERSONA_SPEC if f != "age"]
WIDE_DTYPES: dict[str, Any] = {"ID": "int64", "age": "int64", **dict.fromkeys(_TEXT_COLS, "string")}
for _p in range(1, N_ISSUES + 1):
    WIDE_DTYPES[f"draw_p{_p}"] = "float64"
    WIDE_DTYPES[f"sc_p{_p}"] = "float64"


def read_wide() -> pd.DataFrame:
    """Read the wide CSV back with the dtypes `build_wide()` actually produces."""
    return pd.read_csv(WIDE, dtype=WIDE_DTYPES)


_BOLD_TAG = re.compile(r"</?b>")
_MD_BOLD = re.compile(r"\*\*")


def _strip_markup(text: str) -> str:
    """Drop presentational bold markers; keep every word. See module docstring."""
    text = _BOLD_TAG.sub("", str(text))
    text = _MD_BOLD.sub("", text)
    text = text.replace("\xa0", " ")
    return text.strip()


def load() -> tuple[spss.Dataset, pd.DataFrame, dict[int, pd.DataFrame]]:
    ds = spss.read(SAV)
    df = ds.df
    if df.shape != (N_RESPONDENTS, 56):
        raise ValueError(f"deposit shape drifted: {df.shape}, expected ({N_RESPONDENTS}, 56)")

    sel_cols = [f"qselected_SKUs_{p}" for p in range(1, N_ISSUES + 1)]
    n_selected = df[sel_cols].notna().sum(axis=1)
    if not (n_selected == 4).all():
        raise ValueError("not every respondent has exactly 4 selected policy slots")

    sc_labels = ds.value_labels.get("sc1")
    expected_sc_labels = {
        1.0: "Argument **one** is more persuasive",
        2.0: "Argument **two** is more persuasive",
        3.0: "They are about the same",
        8.0: "Skipped",
        9.0: "Not Asked",
    }
    if sc_labels != expected_sc_labels:
        raise ValueError(
            f"sc1 value labels drifted from the data's own documented order: {sc_labels} "
            f"!= {expected_sc_labels} -- re-read the module docstring's 'RESPONSE CODING' "
            "section before trusting Codebook.pdf's different (1/2/3 = one/same/two) order"
        )

    prompts: dict[int, pd.DataFrame] = {}
    for policy_id, filename in POLICY_FILES:
        p = pd.read_csv(RAW / filename)
        if p.shape[0] != N_PAIRS_PER_ISSUE or not p["pair_id"].is_unique:
            raise ValueError(f"{filename}: expected {N_PAIRS_PER_ISSUE} unique pair_id rows")
        prompts[policy_id] = p

    # 336 arguments = 14 elements x 12 issues x 2 positions, confirmed against
    # the deposit's own flat argument list, not assumed.
    canon = pd.read_csv(CANON)
    if canon.shape[0] != N_ARGUMENTS:
        raise ValueError(f"canonical_sentences_v2.csv has {canon.shape[0]} rows, expected 336")
    if canon["Text"].duplicated().any():
        raise ValueError("canonical_sentences_v2.csv has duplicate argument texts")
    if canon.groupby(["Policy", "Element", "Pro.Con"]).ngroups != N_ARGUMENTS:
        raise ValueError("canonical_sentences_v2.csv is not a clean 14 x 12 x 2 decomposition")
    if canon["Policy"].nunique() != N_ISSUES or canon["Element"].nunique() != N_ELEMENTS:
        raise ValueError("canonical_sentences_v2.csv does not have 12 policies x 14 elements")

    # Every policy_csvs element name, reconciled through ELEMENT_NAME_MAP,
    # must equal elements.xlsx's declared 14 -- and canonical_sentences_v2's
    # own element set, which uses the SAME short names as policy_csvs.
    elx = pd.read_excel(ELEMENTS_XLSX)
    elx_names = set(elx["Element"].unique())
    data_names = set(canon["Element"].unique())
    reconciled = {ELEMENT_NAME_MAP.get(n, n) for n in elx_names}
    if reconciled != data_names:
        raise ValueError(
            f"element name sets disagree after ELEMENT_NAME_MAP: elements.xlsx "
            f"(reconciled) {reconciled} != data {data_names} -- read the divergence "
            "before adding it to ELEMENT_NAME_MAP"
        )
    for policy_id, p in prompts.items():
        in_data = set(p["element_one"].unique()) | set(p["element_two"].unique())
        if in_data != data_names:
            raise ValueError(f"policy {policy_id}: element set drifted from canonical_sentences_v2")
        # Every policy's 756-row design matrix collapses to exactly 560
        # distinct rendered pairs (364 singletons + 196 pairs sharing
        # byte-identical content at two different pair_ids) -- see
        # build_arms()'s docstring. Asserted identically for all 12 policies
        # so a re-fetched deposit that changed this stops the build rather
        # than silently widening `Arm.raws` groupings no one checked.
        combo = (
            p["text_one_title"]
            + "|"
            + p["text_one"]
            + "||"
            + p["text_two_title"]
            + "|"
            + p["text_two"]
        )
        sizes = combo.value_counts()
        if len(sizes) != 560 or dict(sizes.value_counts()) != {1: 364, 2: 196}:
            raise ValueError(
                f"policy {policy_id}: expected 560 distinct rendered pairs (364 singletons + "
                f"196 doubled), found {len(sizes)} groups with size distribution "
                f"{dict(sizes.value_counts())}"
            )

    return ds, df, prompts


def _draws(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (respondent, selected policy slot) -- 13,268 total."""
    records: list[tuple[int, int, int, int]] = []
    for _, row in df.iterrows():
        for p in range(1, N_ISSUES + 1):
            if pd.isna(row[f"qselected_SKUs_{p}"]):
                continue
            pick = int(row[f"maxdiff_version_pick{p}"])
            sc = int(row[f"sc{p}"])
            records.append((int(row["ID"]), p, pick, sc))
    out = pd.DataFrame(records, columns=["ID", "policy_id", "pick", "sc"])
    if len(out) != N_OBS:
        raise ValueError(f"{len(out)} (respondent, slot) draws, expected {N_OBS}")
    if not out["sc"].isin({1, 2, 3}).all():
        raise ValueError(f"sc values outside {{1,2,3}}: {sorted(set(out['sc']) - {1, 2, 3})}")
    return out


def build_wide(ds: spss.Dataset, df: pd.DataFrame) -> pd.DataFrame:
    """One row per respondent: persona (text-resolved) + 12 slots' worth of columns."""
    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        rec: dict[str, Any] = {"ID": int(row["ID"])}
        for field, var, non_answer in PERSONA_SPEC:
            raw = row[var]
            if pd.isna(raw):
                rec[field] = None
                continue
            code = int(raw)
            if code in non_answer:
                rec[field] = None
                continue
            rec[field] = code if field == "age" else ds.label(var, raw)
        for p in range(1, N_ISSUES + 1):
            if pd.isna(row[f"qselected_SKUs_{p}"]):
                rec[f"draw_p{p}"] = None
                rec[f"sc_p{p}"] = None
            else:
                pick = int(row[f"maxdiff_version_pick{p}"])
                rec[f"draw_p{p}"] = p * 1000 + pick
                rec[f"sc_p{p}"] = int(row[f"sc{p}"])
        records.append(rec)
    wide = pd.DataFrame.from_records(records)
    if wide.shape[0] != N_RESPONDENTS:
        raise ValueError(f"wide CSV has {wide.shape[0]} respondent rows, expected {N_RESPONDENTS}")
    # Pandas' nullable "string" dtype explicitly, not the default object dtype
    # -- matches `read_wide()`'s own dtype= so a round trip through the CSV
    # compares equal regardless of whether a column's values happen to look
    # numeric (see `political_attention`'s own comment above `WIDE_DTYPES`).
    for col in _TEXT_COLS:
        wide[col] = wide[col].astype("string")
    return wide


def build_arms(df: pd.DataFrame, prompts: dict[int, pd.DataFrame]) -> list[dict[str, Any]]:
    """Every distinct (policy, pair) actually drawn, policy-major then pair_id-major.

    Declared order, not left to prose (the RJTVG8/PMV0TG precedent).

    **Dedup is by RENDERED TEXT, not by (policy_id, pick)** -- found necessary,
    not assumed: each policy's 756-row design matrix is NOT 756 distinct
    pairs. Checked directly (every one of the 12 files, identically): 560 of
    756 rows are unique by (text_one_title, text_one, text_two_title,
    text_two); 196 content-groups contain exactly 2 rows apiece with BYTE-
    IDENTICAL rendered content at two different `pair_id`s (364 singletons +
    196 pairs x 2 = 756). This is a stable, deliberate feature of the
    design file itself (the same exhaustive-pair generator populated with a
    duplicate weighting, not a data-entry artefact), not noise: all twelve
    policies show the EXACT same 560/196 split. A first pass that deduplicated
    by (policy_id, pick) instead produced two different `condition_num`s that
    rendered identical text for the same outcome -- QC's "a manipulation has
    been lost" check, correctly refusing to build it (1,393 pairs failed, one
    per duplicate-content pair per policy). The fix is `Arm.raws`, built for
    exactly this ("several values of the single source condition variable
    that all denote the SAME condition"): every (policy_id, pick) combined
    code that renders this text is collected into one arm's `raws` list.
    """
    draws = _draws(df)
    distinct = draws[["policy_id", "pick"]].drop_duplicates().sort_values(["policy_id", "pick"])

    arms: list[dict[str, Any]] = []
    by_text: dict[tuple[int, str], int] = {}  # (policy_id, text) -> index into arms
    for policy_id, pick in distinct.itertuples(index=False):
        policy_id, pick = int(policy_id), int(pick)
        prow = prompts[policy_id].iloc[pick - 1]
        if int(prow["pair_id"]) != pick:
            raise ValueError(f"policy {policy_id} row {pick}: pair_id {prow['pair_id']} != {pick}")
        text_one = _strip_markup(prow["text_one"])
        text_two = _strip_markup(prow["text_two"])
        description = _strip_markup(prow["description"])
        prompt = _strip_markup(prow["prompt"])
        policy_name = _strip_markup(prow["policy"])
        text = (
            f"{policy_name}\n\n{description}\n\n{prompt}\n\n"
            f"{prow['text_one_title']}: {text_one}\n"
            f"{prow['text_two_title']}: {text_two}"
        )
        code = policy_id * 1000 + pick
        key = (policy_id, text)
        existing = by_text.get(key)
        if existing is not None:
            arms[existing]["raws"].append(code)
            continue
        factors = {
            "policy": policy_name,
            "element_one": prow["element_one"],
            "pro_con_one": prow["pro_con_one"],
            "element_two": prow["element_two"],
            "pro_con_two": prow["pro_con_two"],
        }
        by_text[key] = len(arms)
        arms.append(
            {
                "raws": [code],
                "condition_num": len(arms),
                "factors": factors,
                "text": text,
            }
        )
    if len(arms) != N_ARMS:
        raise ValueError(f"built {len(arms)} arms, expected {N_ARMS}")
    return arms


_CHOICE_Q = (
    "Which of these arguments do you find more persuasive? Only return one of these three "
    'responses: 1 means "Argument one is more persuasive"; 2 means "Argument two is more '
    'persuasive"; 3 means "They are about the same".'
)


def build_outcomes() -> list[dict[str, Any]]:
    outcomes: list[dict[str, Any]] = []
    for policy_id, _ in POLICY_FILES:
        outcomes.append(
            {
                "var": f"sc_p{policy_id}",
                "task_num": policy_id - 1,
                "question": _CHOICE_Q,
                "scale": {"min": 1, "max": 3, "nominal": True},
                "condition_var": f"draw_p{policy_id}",
            }
        )
    return outcomes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="compare against the recipe + wide CSV")
    ap.add_argument("--write", action="store_true", help="regenerate the wide CSV and the recipe")
    args = ap.parse_args()

    ds, df, prompts = load()
    wide = build_wide(ds, df)
    generated_arms = build_arms(df, prompts)
    generated_outcomes = build_outcomes()

    recipe = yaml.safe_load(RECIPE.read_text()) if RECIPE.exists() else {}
    current_arms = recipe.get("condition", {}).get("arms", [])
    current_outcomes = recipe.get("outcomes", [])
    print(f"generated {len(generated_arms):,} arms; recipe holds {len(current_arms):,}")
    print(f"generated {len(generated_outcomes)} outcomes; recipe holds {len(current_outcomes)}")

    if args.write:
        WIDE.parent.mkdir(parents=True, exist_ok=True)
        wide.to_csv(WIDE, index=False)
        print(f"wrote {WIDE.relative_to(REPO)} ({wide.shape[0]} x {wide.shape[1]})")
        recipe.setdefault("condition", {})["arms"] = generated_arms
        recipe["outcomes"] = generated_outcomes
        RECIPE.write_text(yaml.safe_dump(recipe, sort_keys=False, allow_unicode=True, width=100))
        print(f"wrote {RECIPE.relative_to(REPO)}")
        return 0

    ok = True
    if not WIDE.exists():
        print("wide CSV missing -- run --write")
        ok = False
    else:
        on_disk = read_wide()
        if not on_disk.equals(wide):
            print("WIDE CSV DIFFERS from what this script derives")
            ok = False
    if generated_arms != current_arms:
        ok = False
        print("ARMS DIFFER")
        for i, (g, c) in enumerate(zip(generated_arms, current_arms, strict=False)):
            if g != c:
                print(f"  first difference at arm {i}:\n    generated {g}\n    recipe    {c}")
                break
    if generated_outcomes != current_outcomes:
        ok = False
        print("OUTCOMES DIFFER")
    if ok:
        print("IDENTICAL -- the recipe and wide CSV are exactly what this file derives")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
