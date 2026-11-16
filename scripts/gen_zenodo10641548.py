#!/usr/bin/env python3
"""Write recipes/zenodo10641548.yaml: trophy-hunting vignettes, UK respondents only.

Hare, Dickman, Johnson, Rono, Mutinhima, Sutherland, Kulunge, Sibanda, Mandoloma &
Kimaili, "Public perceptions of trophy hunting are pragmatic, not dogmatic", Proc. R.
Soc. B 291 (2024) 20231638, doi:10.1098/rspb.2023.1638 (open access, CC BY 4.0).
Zenodo record 10641548 ("Public perceptions of trophy hunting are pragmatic, not
dogmatic"), licence cc-zero, read from https://zenodo.org/api/records/10641548 on
16 Nov 2026: `README.md` and `final.data.csv` (1,192 x 16, one row per respondent,
answer TEXT rather than codes, "I don't know" answers already removed). The authors'
R script is the sibling record 10634895 (`Perceptions_of_hunting_script_Dryad.R`).

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* SCOPE. UK respondents only (rich, 16 Nov 2026): `country.1` == "UK", 388 people,
  the paper's own UK n (main text 2(c); ESM S2). USA (404) and South Africa (400)
  are not built. One row per person: each saw one vignette and answered one question.

* THE INSTRUMENT. The deposit has no questionnaire. The authors publish it in their
  electronic supplementary material (figshare doi:10.6084/m9.figshare.25062519,
  file rspb20231638_si_001.pdf): S3 "Full text of all 12 experimental vignettes"
  (ESM pp. 10-15) and S4 "Full instrument" (pp. 16-23; the vignette page is
  "SECTION 3: VIGNETTE", p. 20). An author-written appendix that reproduces the
  fielded wording is a primary source (docs/LEDGER.md 110); the paper's prose and
  Figure 1 paraphrase nothing that contradicts it, and Figure 1's three example
  vignettes match S3 word for word. Every vignette names "A person from the United
  States" as the hunter, for UK respondents too (main text 2(b): "a tourist from the
  USA"). `tests/test_gen_zenodo10641548.py` parses S3 out of the PDF's text and
  asserts all 12 arm texts below equal it.

* DESIGN. 2 x 2 x 3 between subjects, full factorial: animal (elephant, zebra) x
  meat (left for wildlife, provided to local people) x revenue (wildlife
  conservation, economic development, hunting-related companies). The assignment is
  `vignette`, e.g. "e.p.h" (Jev, conf 0.99, via scripts/recipe_prep.py's functions);
  the deposit also holds the three factors as `animal`, `meat`, `revenue`, and the
  two agree on every row (asserted). condition_num follows S3's order (elephant
  before zebra, wildlife before people, conservation, development, hunting), and
  the derived `vignette_code` is condition_num + 1. The UK cell counts reproduce
  ESM S8's UK column exactly (asserted).

* CONDITION. `shared_context` is the vignette page's first sentence ("On this page
  you will read a short passage ...") and the vignette's first paragraph, both
  identical in every arm. The arm is the rest of the vignette, word-for-word.
  Paragraph breaks become single spaces, as in every vignette recipe here, since
  `shared_context` joins the arm with a space. Typography only: curly apostrophes
  straightened. Of the page's three other preamble sentences, the first ("After you
  read the passage, please indicate ...") is the OUTCOME, below, not an omission.
  The other two are left out: "If you are indifferent, please select 'neither
  acceptable nor unacceptable'" is carried by the scale's labelled midpoint, and "If
  you do not know ..., please select 'I don't know'" offers an option no row
  carries, because the deposit has already removed every "I don't know" answer.

* OUTCOME. The page's own printed instruction, shown to every respondent above the
  randomised vignette (S4 p. 20), word-for-word: "After you read the passage, please
  indicate how acceptable or unacceptable you think it would be for the specific
  hunt described in the passage to take place." One text, true for all 388 rows.
  The answer item itself is NOT used. S4 prints the vignette page once, with the
  elephant/wildlife/conservation vignette as "[Randomly assigned vignette ... one
  included here as an example]", and the item under it reads "In your opinion, how
  acceptable would it be for this elephant hunt to take place?". The zebra arms'
  item is printed nowhere, so its wording could only be inferred, and the elephant
  wording would be false for them (ruled by the lead after the checker's review,
  16 Nov 2026). The instruction asks the same thing in words every respondent saw.
  Scale: seven points coded 1 "Very unacceptable" to 7 "Very acceptable", midpoint
  4 "Neither acceptable nor unacceptable" (S4's options, in the data's spelling).

* PERSONA. Age in years and gender ("Do you identify as..."; only Female and Male
  occur among the UK 388) come from the screener, asked before the vignette.
  Education and where the respondent grew up were asked after it (S4 section 4) and
  are mapped as stable demographics. Education labels are the data's ("Primary or
  elementary school", "Secondary or high school", "College or university degree",
  "Postgraduate degree"), which reword S4's English list ("Primary school",
  "Secondary school", ...) the same way in all three countries: the persona keeps
  what the source records. Crosswalk scheme uk_zenodo10641548. A residual
  ambiguity: in US usage "college degree" includes an associate degree, so the
  label could reach below bachelors (Jev: lowest rung bachelors 0.84, associate
  0.13); for UK respondents it is mapped by its headline to Bachelors to
  postgraduate (168 people). "Grew up" is the
  deposit's Rural/Urban merge of S4's four options (Very/Quite urban/rural); merged
  stays merged, as `grew_up_rural_or_urban` in `extra`. Not mapped: the four
  self-identity items (hunter, conservation, animal protection, human rights) and
  the two prioritisation items (people or wild animals; individual animals or
  groups). They were asked after the vignette and sit inside the outcome's own
  domain, so they would be the thing being judged, not who is judging it. Not in
  the deposit at all: ethnicity (a quota question), household income, current area.

* UK FIT. A hunt in sub-Saharan Africa by an American tourist, judged by adults
  living in urban UK, which is what was fielded. Nothing in it needs local knowledge.

    uv run python scripts/gen_zenodo10641548.py           # write derived CSV + recipe
    uv run python scripts/gen_zenodo10641548.py --check   # exit 1 if either differs
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "zenodo10641548"
CSV = RAW / "final.data.csv"
DERIVED = RAW / "zenodo10641548_uk_coded.csv"
RECIPE = REPO / "recipes" / "zenodo10641548.yaml"

# Factor levels in S3's order, keyed by the deposit's own level names.
ANIMALS = {"Elephant": "elephant", "Zebra": "zebra"}
MEATS = {"Wildlife": "wildlife", "People": "people"}
REVENUES = {"Conservation": "conservation", "Development": "development", "Hunting": "hunting"}

# The arms, in S3's order: condition_num = index, vignette_code = index + 1.
ARMS = [(a, m, r) for a in ANIMALS for m in MEATS for r in REVENUES]

# S4 p. 20, the vignette page's first sentence.
PAGE_INTRO = (
    "On this page you will read a short passage describing a situation in which a tourist "
    "plans to travel to Africa and hunt an animal."
)
# S3, identical opening paragraph of all twelve vignettes.
OPENING = (
    "In many African countries, wildlife tourism brings money into rural areas where wildlife "
    "is abundant. In many of these same areas, local people often experience poverty and food "
    "insecurity."
)
ARTICLE = {"Elephant": "an elephant", "Zebra": "a zebra"}
MEAT_TEXT = {
    "Wildlife": "leave the rest of the {animal} out in the open for wild animals to eat.",
    "People": "provide the {animal} meat to people who live nearby, where it is common to eat "
    "wild meat.",
}
REVENUE_TEXT = {
    "Conservation": "Revenue from this hunt would help support wildlife conservation in the "
    "area, for example through investments in wildlife monitoring, habitat protection, and "
    "wildlife crime prevention.",
    "Development": "Revenue from this hunt would help support economic development in the "
    "area, for example through investments in schools, healthcare, and roads.",
    "Hunting": "Revenue from this hunt would help support hunting-related companies in the "
    "area, for example hunting guides and taxidermists.",
}
# S4 p. 20, the page's instruction above the vignette: the outcome for every arm.
QUESTION = (
    "After you read the passage, please indicate how acceptable or unacceptable you think it "
    "would be for the specific hunt described in the passage to take place."
)
# S4 p. 20, the answer item, printed for the elephant example only. Not used (docstring).
ELEPHANT_ITEM = "In your opinion, how acceptable would it be for this elephant hunt to take place?"

RESPONSES = {
    "Very unacceptable": 1,
    "Unacceptable": 2,
    "Somewhat unacceptable": 3,
    "Neither acceptable nor unacceptable": 4,
    "Somewhat acceptable": 5,
    "Acceptable": 6,
    "Very acceptable": 7,
}

# ESM S8, UK column, in S3's arm order.
S8_UK = [35, 34, 30, 28, 29, 33, 29, 24, 42, 37, 38, 29]

PERSONA = {
    "age": "age",
    "gender": "gender",
    "education": "education",
    "grew_up_rural_or_urban": "rural.past.combined",
}


def arm_text(animal: str, meat: str, revenue: str) -> str:
    """The vignette after its opening paragraph, word-for-word from S3."""
    low = animal.lower()
    return (
        "A person from the United States plans to visit a rural area in Africa. During the "
        f"visit, this person would like to pay to hunt {ARTICLE[animal]}, in full compliance "
        "with all relevant local laws and regulations. They plan to have the "
        f"{low}'s head stuffed, take the head home as a memento of the experience, and "
        f"{MEAT_TEXT[meat].format(animal=low)} {REVENUE_TEXT[revenue]}"
    )


def load() -> pd.DataFrame:
    return pd.read_csv(CSV, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def derive(df: pd.DataFrame) -> pd.DataFrame:
    """The UK respondents, coded: one row per person."""
    assert df.shape == (1192, 16)
    assert Counter(df["country.1"]) == {"USA": 404, "UK": 388, "SA": 400}
    df = df.copy()
    # The deposit has no id column; its row order is the only stable handle.
    df["pid"] = range(1, len(df) + 1)
    uk = df[df["country.1"] == "UK"]
    code = {arm: i + 1 for i, arm in enumerate(ARMS)}
    rows = []
    for _, r in uk.iterrows():
        arm = (r["animal"], r["meat"], r["revenue"])
        letters = ".".join(x[0].lower() for x in arm)
        assert r["vignette"] == letters, (r["pid"], r["vignette"], arm)
        rows.append(
            {
                "pid": int(r["pid"]),
                "vignette_code": code[arm],
                "acceptability": RESPONSES[r["response.text"]],
                "age": int(r["age"]),
                "gender": r["gender"],
                "education": r["education"].strip(),
                "grew_up_rural_or_urban": r["rural.past.combined"],
            }
        )
    out = pd.DataFrame(rows)
    counts = out["vignette_code"].value_counts().sort_index().tolist()
    assert counts == S8_UK, counts
    assert set(out["gender"]) == {"Female", "Male"}
    return out


def build_arms() -> list[dict[str, Any]]:
    arms = []
    for i, (animal, meat, revenue) in enumerate(ARMS):
        arms.append(
            {
                "raw": i + 1,
                "condition_num": i,
                "factors": {
                    "animal": ANIMALS[animal],
                    "meat": MEATS[meat],
                    "revenue": REVENUES[revenue],
                },
                "text": arm_text(animal, meat, revenue),
            }
        )
    return arms


NOTES = """\
Hare et al., "Public perceptions of trophy hunting are pragmatic, not dogmatic", Proc. R.
Soc. B 291 (2024) 20231638, doi:10.1098/rspb.2023.1638. Zenodo record 10641548 (CC0):
final.data.csv, one row per respondent, "I don't know" answers already removed. Qualtrics
online panel, urban adults in the USA, UK and South Africa; ONLY THE 388 UK RESPONDENTS
are built (rich, 16 Nov 2026).

GENERATED by scripts/gen_zenodo10641548.py, which also writes the derived data file
zenodo10641548_uk_coded.csv from the deposit's CSV. Every judgement is in that script's
docstring; in brief:

- Wording: the authors' electronic supplementary material (figshare
  doi:10.6084/m9.figshare.25062519), S3 "Full text of all 12 experimental vignettes"
  (pp. 10-15) and S4 "Full instrument" (vignette page p. 20). The deposit has no
  questionnaire.
- 2 x 2 x 3 between subjects: animal x use of meat x use of revenue; one vignette and one
  question per person. Arms in S3's order. UK cell counts equal ESM S8 exactly.
- Condition: the page's first sentence and the shared opening paragraph, then the arm's
  own text, word-for-word; paragraph breaks become spaces. Left out: two of the page's
  answer-instruction sentences (one explains the midpoint the scale already labels, one
  offers the "I don't know" option no row carries).
- Outcome, for all rows: the page's printed instruction, word-for-word, "After you read
  the passage, please indicate how acceptable or unacceptable you think it would be for
  the specific hunt described in the passage to take place." The answer item ("In your
  opinion, how acceptable would it be for this elephant hunt to take place?") is not
  used: S4 prints it only for the elephant example, and the zebra arms' wording is
  printed nowhere.
- Education: "College or university degree" maps to Bachelors to postgraduate; in US
  usage it can include an associate degree, a residual ambiguity (168 UK people).
- Persona: age, gender, education (scheme uk_zenodo10641548), and where the respondent
  grew up (the deposit's Rural/Urban merge) as an extra. The identity and prioritisation
  items are post-vignette attitudes inside the outcome's domain and are not mapped.
- participant_id is the respondent's 1-based row number in the deposit's final.data.csv.
"""


class _Literal(str):
    pass


class _Dumper(yaml.SafeDumper):
    """Multi-line strings as `|` blocks, so the recipe reads as the row will."""


def _str(dumper: yaml.SafeDumper, data: str) -> yaml.ScalarNode:
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style=style)


_Dumper.add_representer(_Literal, _str)
_Dumper.add_representer(str, _str)


def render() -> str:
    recipe = {
        "study_id": "zenodo10641548",
        "source": "zenodo",
        "title": (
            "Public perceptions of trophy hunting are pragmatic, not dogmatic (UK respondents): "
            "how acceptable is a hunt in Africa, as the animal, the use of its meat and the use "
            "of the revenue vary"
        ),
        "data_file": DERIVED.name,
        "licence": (
            "CC0 1.0 (cc-zero), stated on Zenodo record 10641548 and read from "
            "https://zenodo.org/api/records/10641548 on 16 Nov 2026. Wording from the "
            "paper's electronic supplementary material, CC BY 4.0."
        ),
        "comparable_to_socsci210": False,
        "participant_id_var": "pid",
        "notes": _Literal(NOTES),
        "condition": {
            "source_var": "vignette_code",
            "shared_context": f"{PAGE_INTRO} {OPENING}",
            "factors": ["animal", "meat", "revenue"],
            "arms": build_arms(),
        },
        "outcomes": [
            {
                "var": "acceptability",
                "task_num": 0,
                "question": QUESTION,
                "scale": {
                    "min": 1,
                    "max": 7,
                    "min_label": "Very unacceptable",
                    "mid_label": "Neither acceptable nor unacceptable",
                    "max_label": "Very acceptable",
                },
            }
        ],
        "response_recode": {k: k for k in range(1, 8)},
        "persona_map": {field: field for field in PERSONA},
    }
    return yaml.dump(recipe, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    wide = derive(load())
    text = render()
    if args.check:
        ok = RECIPE.read_text() == text
        on_disk = pd.read_csv(DERIVED)
        ok_csv = on_disk.equals(pd.read_csv(pd.io.common.StringIO(wide.to_csv(index=False))))
        print(
            f"recipe {'matches' if ok else 'DIFFERS'}; derived CSV {'matches' if ok_csv else 'DIFFERS'}"
        )
        return 0 if ok and ok_csv else 1
    wide.to_csv(DERIVED, index=False)
    RECIPE.write_text(text)
    print(f"wrote {DERIVED.relative_to(REPO)} {wide.shape} and {RECIPE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
