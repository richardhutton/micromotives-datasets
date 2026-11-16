#!/usr/bin/env python3
"""Write recipes/zenodo6572717.yaml: parents choose between two health services (CUPID DCE).

Nicholson, McDonnell, Conlon, De Brún, Doherty & McAuliffe, "Parent's preferences for
unscheduled paediatric healthcare: A discrete choice experiment", Health Expectations
26(5) (2023) 1931-1940, doi:10.1111/hex.13802 (open access, PMC10485340). Zenodo record
6572717, "CUPID: Parental preferences for unscheduled paediatric healthcare: A Discrete
Choice Experiment" (Nicholson, McDonnell, McAuliffe; CC BY 4.0, published 23 May 2022):
the survey (Parent_Decision_Making_DCE_Survey.docx), the Qualtrics export (Data from
Survey 23 Feb 2021.xlsx), the authors' analysis file (Stata Data Formatted for DCE.dta),
and two Ngene files (Syntax Final Feb 2021.ngs, Final Parent DCE design.ngd).

458 parents of a child under 16 living in IRELAND (Qualtrics research panels, February
2021) each chose between two health services, Service A and Service B, twelve times.
Each service is described by five attributes: how long to wait, the appointment system,
advice before attending, who you will see, and cost in euro. An Irish sample, not a UK
one: the euro amounts and the GP/practice-nurse framing are the source's and are kept.

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* 24 TASKS, 12 PER PERSON, NOT 6. The docx's survey-flow header says "DCE Block 1 (6
  Questions)" and prints six choice tables per block (Q6.1-Q6.6, Q7.1-Q7.6). That is
  the export, not the survey: its own intro says "There will be 12 different scenarios",
  the paper says 24 choice sets in two blocks of 12 (and "12 choice sets for each
  respondent"), the Zenodo description says the same, and the .xlsx export has
  "Source A/B Q6.1" ... "Q6.12" and "Q7.1" ... "Q7.12". In the .dta, `block` (1 or 2,
  the Qualtrics BlockRandomizer) decides the twelve: block 1 answered `choicetask_01`
  .. `_12`, block 2 `choicetask_13` .. `_24`, everyone exactly twelve (asserted). The
  .dta is long, 48 rows a person (24 tasks x 2 services, `task` "_01a" .. "_24b"), with
  `choice` missing on the twelve tasks of the other block.
* WHICH SERVICES EACH TASK SHOWED. Read from the .dta's attribute dummies
  (timely_*, appoint_*, guidance_*, continuity_*, cost), constant within each task row
  across all 458 people (asserted). The docx's choice tables DISAGREE with them: not
  one of its twelve tables matches any task in the data on all ten cells, and its Q7.1
  and Q7.2 are identical while their answers differ (73% vs 51% chose A). The docx
  carries the authors' own comment explaining why: "Please note the scenarios are
  presented differently in Qualtrics, but the formatting changes when exported to Word.
  I have added our copy of the scenarios below". So the docx tables are a working copy,
  not the fielded screens. Three things settle that the dummies are what was shown:
  - the paper's Figure 1, "Example of a choice set" (a screenshot of a fielded screen,
    with the Service A / Service B radio buttons), is task 1 in the data exactly
    (FIGURE_1 below; asserted), and matches no docx table;
  - the dummies reproduce the paper's Table 3 conditional logit to three decimals
    (tests/test_gen_zenodo6572717.py);
  - the Ngene .ngd is a third design again (a two-level appointment attribute, the
    pilot's per the paper: "the design was updated to adjust the wording of the levels
    of one attribute (appointment type)"), so it is not used.
* LEVEL WORDING. Figure 1 shows ten of the fifteen level texts word-for-word, and the
  docx copy's tables word them identically. The other five ("Next day", "Given
  appointment for evening/weekend", "Your own GP", "€0", "€45") are from the docx copy
  only: its combinations are not the fielded ones, but its wording agrees with the
  fielded screen wherever the two can be compared. Asserted present in the docx.
  Line breaks inside table cells become spaces; "9am- 5pm" in two docx cells is
  "9am-5pm" on Figure 1 and in the other docx cells.
* ATTRIBUTE ORDER. Figure 1, all twelve docx tables and the intro's numbered list give
  the five attributes in one order (wait, appointment system, advice, who, cost); the
  data has no order variable and the Ngene design has none either. So the order is
  taken as fixed, and the row headings are Figure 1's own left column. Not proved for
  every screen: a shuffled order would have left no trace, but nothing suggests one.
* CONDITION. One cell per task (24 of 216 x 216, a sparse template whose ten dimensions
  are the five attributes for each service; QC rule 5 then tests every attribute on
  real minimal pairs, which 24 written-out arms could not offer). The intro screen (Q5.1, shown once before the
  tasks; word-for-word, and the same as the paper's quoted vignette) then the two
  services. Kept: "For each scenario, please imagine ... in a health service" and "When
  responding to these scenarios, we would like you to think of a time before the
  COVID-19 pandemic ...". The full stop after "in a health service" is OURS: in the
  source the sentence runs on into "There will be 12 different scenarios ...", which
  is dropped as survey mechanics and sequence (docs/CONVENTIONS.md, "Sequence
  signposting"), as are "The next section will ask you ...", the five attribute
  definitions with their level lists (the design described, not a scenario), and the
  worked example ("Below is an example ...", "[EXAMPLE GRAPHIC]", "In this example the
  respondent chose Service A ..."). "We ask you to consider all of the characteristics
  and choose the service that you would prefer to attend." is the outcome (below).
  The table becomes two lists, "Service A" then "Service B", each line "<row heading>:
  <cell>", left column then right as on screen; the dashes and colons are layout, ours.
  The intro is written into every arm rather than `shared_context`, because the
  pipeline joins `shared_context` to the arm with a space and the list must start on
  its own line.
* OUTCOME. The choice screen has no question stem, only the table and two radio
  buttons "Service A" / "Service B". The question is therefore the intro's instruction,
  word-for-word, then the options enumerated (our words, the PZB01G convention for a
  nominal scale): 1 = Service A, 2 = Service B. A forced choice; no missing answers
  among the twelve tasks each person was shown. Read from the raw `choicetask_<k>`
  text, and asserted to agree with the authors' `choice` on both rows of the task and
  with the .xlsx export by Response ID.
* WHO. 450 of 458. The paper: "Data from eight participants were removed ahead of the
  analysis due to incorrect data (e.g., age of child greater than 18 years or the
  number of healthcare visits reporting as an unlikely amount [i.e., 2677])". In the
  .dta those eight are exactly the people whose cleaned `ChildAge` or `HealthcareUse`
  the authors set missing (four with a youngest child "aged" 20 to 1,115, four with
  2,013 to 2,677 visits; asserted). Keeping those eight is what moves the Table 3
  estimates off the published values, so the authors' exclusion is followed.
* PERSONA, from the survey's own answer text (the .dta's string columns, which agree
  one-to-one with its coded copies; checked): age; gender (no one chose "Other/ Prefer
  not to say"); education, ethnicity and employment through the crosswalks (Irish
  scheme `ie_zenodo6572717`, MERGE-only; Jev's readings in the crosswalk notes);
  family status, number of children and the youngest child's age as extras, the
  youngest child being the one every scenario asks about; and the screening question
  "Are you a parent/guardian of a child aged under 16 living in Ireland?" (all "Yes";
  failing it ended the survey), which is the only place a row can say Ireland.
  Family status is not mapped to marital_status: "Divorced/Separated" spans two
  canonical values and "Single" does not say never married. Not mapped, though asked:
  medical card, GP visit card and private health insurance, which decide what a
  respondent pays for exactly the care the outcome prices (the persona/outcome domain
  rule, EFXNLX); healthcare-professional status; the child's health and conditions.
* NOT CARRIED. `IPAddress`, `LocationLatitude`, `LocationLongitude` and the recipient
  name/email columns exist in the .dta and are empty for everyone; they are never read
  into the derived file. `ResponseID` is replaced by the authors' `newid` (1-458).
* JEV (recipe_prep, 16 Nov 2026): assignment `block` (0.40, REVIEW; correct: it is the
  block randomiser, and the task within block is fixed by the design); persona age and
  gender 0.99; education/ethnicity/employment/marital each pointed at the coded copy
  with the string column runner-up (the two agree; the string is used); no value labels
  to judge on the string columns; no questionnaire directives.

    uv run python scripts/gen_zenodo6572717.py --prep    # (re)write the coded long .csv
    uv run python scripts/gen_zenodo6572717.py           # write the recipe
    uv run python scripts/gen_zenodo6572717.py --check   # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
STUDY = "zenodo6572717"
RAW = REPO / "data" / "raw" / STUDY
DTA = RAW / "Stata Data Formatted for DCE.dta"
XLSX = RAW / "Data from Survey 23 Feb 2021.xlsx"
DOCX = RAW / "Parent_Decision_Making_DCE_Survey.docx"
DATA_FILE = f"{STUDY}_coded.csv"
DATA = RAW / DATA_FILE
RECIPE = REPO / "recipes" / f"{STUDY}.yaml"
LICENCE = (
    "CC BY 4.0 (cc-by-4.0), stated on Zenodo record 6572717 and read from "
    "https://zenodo.org/api/records/6572717 on 16 Nov 2026."
)

N_PEOPLE = 458
N_KEPT = 450
N_TASKS = 24
PER_BLOCK = 12

# ---------------------------------------------------------------------------
# The instrument
# ---------------------------------------------------------------------------

SCENARIO = (
    "For each scenario, please imagine that your youngest (or only) child has not been "
    "well (not been themselves) for a period of time. You have managed the illness to the "
    "best of your ability; however, you have now decided that you need further support "
    "from a health professional in a health service"
)
COVID = (
    "When responding to these scenarios, we would like you to think of a time before the "
    "COVID-19 pandemic and to not consider how the pandemic may impact your choice."
)
INSTRUCTION = (
    "We ask you to consider all of the characteristics and choose the service that you "
    "would prefer to attend."
)
OPTIONS = ("Service A", "Service B")
QUESTION = f'{INSTRUCTION} 1 means "{OPTIONS[0]}"; 2 means "{OPTIONS[1]}".'

# attribute -> (row heading on screen, {level slug: cell text}), in screen order.
ATTRIBUTES: dict[str, tuple[str, dict[str, str]]] = {
    "wait": (
        "How long to wait for appointment",
        {"same_day": "Same day", "next_day": "Next day", "two_days": "In two days' time"},
    ),
    "appointment": (
        "Appointment system",
        {
            "nine_to_five": "Given appointment between 9am-5pm",
            "evening_weekend": "Given appointment for evening/weekend",
            "walk_in": "Walk in with no appointment (unknown wait)",
        },
    ),
    "advice": (
        "Advice before attending",
        {
            "telephone_advice": "Telephone advice from healthcare professional about what to do",
            "no_advice": "No advice",
        },
    ),
    "who": (
        "Who you will see",
        {
            "own_gp": "Your own GP",
            "any_doctor_or_nurse": "Any doctor or nurse",
            "practice_nurse": "The practice nurse",
        },
    ),
    "cost": (
        "Cost",
        {"eur_0": "€0", "eur_15": "€15", "eur_30": "€30", "eur_45": "€45"},
    ),
}

# The .dta's dummy for each level (cost is its own numeric column).
DUMMIES: dict[str, dict[str, str]] = {
    "wait": {
        "same_day": "timely_sameday",
        "next_day": "timely_nextday",
        "two_days": "timely_2days",
    },
    "appointment": {
        "nine_to_five": "appoint_9to5",
        "evening_weekend": "appoint_eveweekend",
        "walk_in": "appoint_walkin",
    },
    "advice": {"telephone_advice": "guidance_teleadvice", "no_advice": "guidance_noadvice"},
    "who": {
        "own_gp": "continuity_ownGP",
        "any_doctor_or_nurse": "continuity_anyGPnurse",
        "practice_nurse": "continuity_practicenurse",
    },
}
COSTS = {0: "eur_0", 15: "eur_15", 30: "eur_30", 45: "eur_45"}
# Level code in the derived file: 1-based, in ATTRIBUTES order (ours; the .dta has dummies).
CODE = {
    attr: {slug: i for i, slug in enumerate(cells, 1)} for attr, (_, cells) in ATTRIBUTES.items()
}

# The paper's Figure 1, "Example of a choice set", transcribed from the image:
# (Service A, Service B), each in ATTRIBUTES order.
FIGURE_1 = (
    ("In two days' time", "Given appointment between 9am-5pm",
     "Telephone advice from healthcare professional about what to do",
     "The practice nurse", "€15"),
    ("Same day", "Walk in with no appointment (unknown wait)", "No advice",
     "Any doctor or nurse", "€30"),
)  # fmt: skip

# Persona: derived-file column -> .dta column (the survey's answer text).
PERSONA = {
    "age": "Whatageareyou",
    "gender": "Whatisyourgender",
    "education": "Whatisyourhighestlevelofed",
    "ethnicity": "Whatisyourethnicorcultural",
    "employment": "Whatisyouremploymentstatus",
    "family_status": "Whatisyourfamilystatus",
    "number_of_children": "Howmanychildrendoyouhave",
    "age_of_youngest_child": "Whatageisyouryoungestchild",
    "parent_of_a_child_under_16_living_in_Ireland": "Areyouaparentguardianofac",
}
# The coded copies the authors made of four of them; must agree one-to-one.
CODED_COPY = {
    "Whatisyourhighestlevelofed": "Education",
    "Whatisyourethnicorcultural": "Ethnic",
    "Whatisyouremploymentstatus": "workstatus",
    "Whatisyourfamilystatus": "FamilyStatus",
}

DESIGN_COLS = [c for d in DUMMIES.values() for c in d.values()] + ["cost"]
READ_COLS = [
    "ResponseID",
    "newid",
    "task",
    "block",
    "choice",
    "ChildAge",
    "HealthcareUse",
    "Approximatelyhowmanytimeshav",
    *DESIGN_COLS,
    *(f"choicetask_{k:02d}" for k in range(1, N_TASKS + 1)),
    *PERSONA.values(),
    *CODED_COPY.values(),
]


def _norm(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"').replace(" ", " ")
    return re.sub(r"\s+", " ", text).strip()


def docx_text() -> str:
    """The survey document's words, paragraphs and table cells run together."""
    with zipfile.ZipFile(DOCX) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    xml = re.sub(r"</w:p>|<w:br/>|<w:tab/>|</w:tc>", " ", xml)
    return _norm(re.sub(r"<[^>]+>", "", xml))


def check_wording() -> None:
    """Every word the rows quote is in the survey document."""
    text = docx_text()
    for piece in (SCENARIO, COVID, INSTRUCTION, *OPTIONS):
        assert _norm(piece) in text, piece
    for heading, levels in ATTRIBUTES.values():
        assert heading in text, heading
        for cell in levels.values():
            assert cell in text, cell
    # The paper's vignette, as quoted in its Methods, is the same intro.
    assert "There will be 12 different scenarios" in text


def read_dta() -> pd.DataFrame:
    reader = pd.io.stata.StataReader(DTA)
    df = reader.read(convert_categoricals=False, columns=READ_COLS)
    assert df.shape[0] == N_PEOPLE * N_TASKS * 2
    return df


def level_of(row: Any) -> dict[str, str]:
    out = {}
    for attr, dummies in DUMMIES.items():
        on = [slug for slug, col in dummies.items() if row[col] == 1]
        assert len(on) == 1 and all(row[c] in (0, 1) for c in dummies.values())
        out[attr] = on[0]
    out["cost"] = COSTS[int(row["cost"])]
    return out


def design(df: pd.DataFrame | None = None) -> dict[int, tuple[dict[str, str], dict[str, str]]]:
    """Task 1-24 -> (Service A levels, Service B levels), from the authors' dummies."""
    df = read_dta() if df is None else df
    assert (df.groupby("task")[DESIGN_COLS].nunique() == 1).all().all(), "design varies"
    first = df.groupby("task")[DESIGN_COLS].first()
    out = {}
    for k in range(1, N_TASKS + 1):
        a, b = level_of(first.loc[f"_{k:02d}a"]), level_of(first.loc[f"_{k:02d}b"])
        assert a != b
        out[k] = (a, b)
    shown = tuple(tuple(ATTRIBUTES[attr][1][side[attr]] for attr in ATTRIBUTES) for side in out[1])
    assert shown == FIGURE_1, "task 1 is not the paper's Figure 1"
    return out


def excluded(df: pd.DataFrame) -> set[int]:
    """The paper's eight: cleaned child age or visit count set missing by the authors."""
    people = df.drop_duplicates("newid").set_index("newid")
    bad = people[people["ChildAge"].isna() | people["HealthcareUse"].isna()]
    raw_age = bad["Whatageisyouryoungestchild"]
    raw_visits = bad["Approximatelyhowmanytimeshav"]
    assert ((raw_age > 18) | (raw_visits > 1000)).all()
    assert ((raw_age > 18) ^ (raw_visits > 1000)).sum() == 8
    assert len(bad) == N_PEOPLE - N_KEPT
    return {int(i) for i in bad.index}


def xlsx_answers() -> dict[str, list[Any]]:
    """Response ID -> the 24 choicetask answers in the Qualtrics export."""
    import openpyxl

    wb = openpyxl.load_workbook(XLSX, read_only=True)
    rows = wb.worksheets[0].iter_rows(values_only=True)
    head = list(next(rows))
    rid = head.index("Response ID")
    cols = [head.index(f"choicetask_{k:02d}") for k in range(1, N_TASKS + 1)]
    out = {}
    for r in rows:
        if r[rid] is None:
            continue
        out[str(r[rid])] = [r[c] or "" for c in cols]
    assert len(out) == N_PEOPLE
    return out


def prep() -> pd.DataFrame:
    """The coded long file: one row per kept person per task they answered."""
    check_wording()
    df = read_dta()
    tasks = design(df)
    assert (df.groupby("newid").size() == N_TASKS * 2).all()
    assert df["newid"].nunique() == N_PEOPLE == df["ResponseID"].nunique()
    for raw, coded in CODED_COPY.items():
        pairs = df.drop_duplicates("newid")[[raw, coded]].drop_duplicates()
        assert pairs[raw].is_unique and pairs[coded].is_unique, raw
    drop = excluded(df)
    export = xlsx_answers()

    out: list[dict[str, Any]] = []
    for pid, person in df.groupby("newid"):
        p = person.set_index("task")
        block = int(p["block"].iloc[0])
        assert (p["block"] == block).all() and block in (1, 2)
        mine = range(1, 13) if block == 1 else range(13, 25)
        answers = export[str(p["ResponseID"].iloc[0])]
        for k in range(1, N_TASKS + 1):
            text = str(p[f"choicetask_{k:02d}"].iloc[0])
            a, b = p.loc[f"_{k:02d}a", "choice"], p.loc[f"_{k:02d}b", "choice"]
            assert (answers[k - 1] or "") == text, (pid, k)
            if k not in mine:
                assert text == "" and pd.isna(a) and pd.isna(b), (pid, k)
                continue
            assert text in OPTIONS and a + b == 1, (pid, k)
            assert (a == 1) == (text == OPTIONS[0]), (pid, k)
            if int(pid) in drop:
                continue
            row: dict[str, Any] = {"pid": int(pid), "task": k}
            for side, levels in zip("AB", tasks[k], strict=True):
                for attr, slug in levels.items():
                    row[f"{attr}_{side}"] = CODE[attr][slug]
            row["choice"] = OPTIONS.index(text) + 1
            for col, src in PERSONA.items():
                row[col] = p[src].iloc[0]
            out.append(row)
    coded = pd.DataFrame(out)
    assert len(coded) == N_KEPT * PER_BLOCK and coded["pid"].nunique() == N_KEPT
    assert (coded["parent_of_a_child_under_16_living_in_Ireland"] == "Yes").all()
    return coded


# ---------------------------------------------------------------------------
# The recipe
# ---------------------------------------------------------------------------


def service_lines(name: str, fill: dict[str, str]) -> str:
    lines = [name]
    for attr, (heading, _) in ATTRIBUTES.items():
        lines.append(f"- {heading}: {fill[attr]}")
    return "\n".join(lines)


def arm_text(a: dict[str, str], b: dict[str, str]) -> str:
    """The rendered text for one task, from level slugs (used by the tests)."""
    cells = {attr: cells for attr, (_, cells) in ATTRIBUTES.items()}
    fa = {attr: cells[attr][a[attr]] for attr in ATTRIBUTES}
    fb = {attr: cells[attr][b[attr]] for attr in ATTRIBUTES}
    return _text(fa, fb)


def _text(fa: dict[str, str], fb: dict[str, str]) -> str:
    intro = f"{SCENARIO}. {COVID}"
    return "\n\n".join([intro, service_lines(OPTIONS[0], fa), service_lines(OPTIONS[1], fb)])


def template_text() -> str:
    return _text(
        {attr: f"{{{attr}_A}}" for attr in ATTRIBUTES},
        {attr: f"{{{attr}_B}}" for attr in ATTRIBUTES},
    )


def dimensions() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for side in "AB":
        for attr, (_, cells) in ATTRIBUTES.items():
            out[f"{attr}_{side}"] = {
                "var": f"{attr}_{side}",
                "levels": {
                    CODE[attr][slug]: {"level": slug, "text": text} for slug, text in cells.items()
                },
            }
    return out


NOTES = """\
Nicholson, McDonnell, Conlon, De Brún, Doherty & McAuliffe, "Parent's preferences for
unscheduled paediatric healthcare: A discrete choice experiment", Health Expectations 26(5)
(2023) 1931-1940, doi:10.1111/hex.13802 (open access). Zenodo record 6572717
(doi:10.5281/zenodo.6572717), CUPID project, UCD. Qualtrics research panels, February 2021:
parents of a child under 16 living in IRELAND, not the UK. Euro amounts and the Irish GP /
practice-nurse framing are the source's and are kept.

GENERATED by scripts/gen_zenodo6572717.py, which also writes the derived long file
zenodo6572717_coded.csv from the deposit's .dta. Every judgement is in that script's
docstring; in brief:

- A paired-choice DCE: 24 fixed choice sets (Bayesian efficient design) in two blocks of
  12; each parent saw one block, so 12 rows per person. The docx shows only six tables per
  block, and they are the authors' working copy ("I have added our copy of the scenarios
  below"), not the fielded screens: none matches the data. The services shown are read from
  the authors' attribute dummies, which match the paper's Figure 1 (task 1) exactly and
  reproduce its Table 3 conditional logit.
- Condition: the intro screen word-for-word (the full stop after "in a health service" is
  ours, where the dropped "There will be 12 different scenarios ..." ran on), then Service A
  and Service B as two lists of "<row heading>: <cell>", headings and cells as on Figure 1,
  five cells from the docx copy only. Attribute order taken as fixed (Figure 1, every docx
  table and the intro's list agree; nothing in the data records an order). The riskiest
  judgement: five level texts and the order rest on the docx copy and one screenshot.
- Outcome: the intro's instruction, then '1 means "Service A"; 2 means "Service B".' (ours).
- 450 of 458 parents: the paper's eight exclusions (implausible child age or visit count).
- Persona: survey answer text; family status, number of children, youngest child's age and
  the Ireland screening question as extras. Medical card / GP visit card / insurance not
  mapped (they set what the respondent pays for the care being priced).
- IP address and location columns exist in the .dta, are empty, and are never read.
"""


def recipe() -> dict[str, Any]:
    design()  # the assertions: design constant per task, task 1 is Figure 1
    return {
        "study_id": STUDY,
        "source": "zenodo",
        "title": (
            "CUPID (Ireland, Feb 2021): parents choose between two health services for an "
            "unwell child (paired-choice DCE)"
        ),
        "data_file": DATA_FILE,
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": "pid",
        "notes": NOTES,
        "condition": {
            "considered_and_rejected": {
                "task": (
                    "The choice-set number, 1-24, of the fixed Ngene design (1-12 block 1, "
                    "13-24 block 2). Not a second randomisation: it determines all ten level "
                    "codes, which are the declared source_vars, one-to-one (24 tasks, 24 "
                    "distinct cells). Kept in the derived file so a row can be traced to its "
                    "task."
                ),
            },
            "template": {
                # 216 x 216 cells, 24 shown: a fixed design, not crossed.
                "sparse": True,
                "text": template_text(),
                "dimensions": dimensions(),
            },
        },
        "outcomes": [
            {
                "var": "choice",
                "task_num": 0,
                "question": QUESTION,
                "scale": {"min": 1, "max": 2, "nominal": True},
            }
        ],
        "response_recode": {1: 1, 2: 2},
        "missing_codes": [],
        "persona_map": {k: k for k in PERSONA},
    }


def render() -> str:
    return yaml.safe_dump(recipe(), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prep", action="store_true", help="(re)write the coded long .csv")
    ap.add_argument("--check", action="store_true", help="exit 1 if the recipe differs")
    args = ap.parse_args()
    if args.prep:
        prep().to_csv(DATA, index=False)
        print(f"wrote {DATA.relative_to(REPO)}")
        return 0
    text = render()
    if args.check:
        same = RECIPE.exists() and RECIPE.read_text() == text
        print("recipe matches generator" if same else "recipe DIFFERS from generator")
        return 0 if same else 1
    RECIPE.write_text(text)
    print(f"wrote {RECIPE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
