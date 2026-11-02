#!/usr/bin/env python3
"""Write recipes/images/gybnm.yaml: political advert disclaimers (IMG44).

Gordon, Stafford & Dommett (Sheffield), "Cue to Trust? Investigating the Impact of
Political Advertising Transparency Disclaimers on Citizen Trust Evaluations",
Proceedings of the Annual Meeting of the Cognitive Science Society 46 (2024),
https://escholarship.org/uc/item/8fs0x868 (CC BY 4.0). OSF gybnm (CC0 1.0
Universal): the fielded questionnaire (full_survey.pdf), the Qualtrics export
(final_responses.csv), the authors' cleaning script (data_wrangle.Rmd) and all
eight advert pictures ("Experimental Materials/").

1,249 UK adults (Prolific) answered questions about UK politicians, then read a
short statement from the leader of a fictional party, The Reconnect Party, and were
shown four of its Facebook-style adverts, either plain (control) or each carrying
the words "Political ad." and a yellow disclaimer banner saying who paid for it,
that it was targeted on income, age and gender, the audience size and the amount
spent. They then rated the party and its adverts.

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* DESIGN. Between subjects, two arms. Each person saw all four adverts together
  and then answered questions about the party and "the adverts" as a whole: no
  question is about one advert, so no row needs to say which advert it rates and
  none cites a position in a sequence. The debrief text in the export says people
  were split into THREE groups (no imprint; who paid; who paid plus targeting),
  but the data's `Condition` holds two codes, the deposit has two sets of
  pictures, the questionnaire shows two columns ("Control Condition",
  "Experimental Condition") and the paper reports two conditions. Built as two.
* ARMS. `Condition` 0 = control, 1 = disclaimer: the authors' script labels them
  so ("control", "transparent"); each code has its own page-timing block (Q54 for
  0, Q56 for 1, never both); and the recall answers agree (who paid: 68 of 625
  "yes" in 0, 326 of 624 in 1). Pictures: `control_<k>.jpg` and
  `material<k>_transparent.jpg`, the same eight the questionnaire's table shows,
  advert k in row k of both columns.
* CONDITION. shared_context is the questionnaire's introduction to the adverts and
  the party leader's statement, word-for-word (full_survey.pdf, page 2), dropping
  "However, if you feel uncomfortable at any point, we remind you that you can
  exit the study at any time by closing the browser." and the paragraph about
  clicking next and the 40-second timer, as survey mechanics. The arm text quotes
  every word printed on each advert (the catalogue's text_in_image, " / " between
  separate blocks of text), each followed by the advert itself. Words that are
  OURS: "The four adverts were then shown:". The order the four were shown in is
  not recorded; the text lists them in the questionnaire's order and says nothing
  about order. In the disclaimer arm the paper quotes the banner as "...your age,
  income and gender..."; the pictures, which are what was shown, say "your
  income, age, and gender", and the text follows the pictures.
* OUTCOMES. Wording from the Qualtrics export's own question-text row (the
  second header line of final_responses.csv), which is what the survey platform
  displayed; whitespace between paragraphs is collapsed, curly quotes
  straightened, words kept (including "The Reconnect Parties' campaign"). It
  differs from full_survey.pdf in places ("The Reconnect Party adverts are
  credible." where the PDF has "Party's"; "above their personal interests" where
  the PDF has "own interests"; the integrity items' order), and the export wins.
  A grid item is its screen's stem followed by its statement in quotation marks.
  Dropped as survey mechanics: the social media trust screen's opening "Thank you
  for the time you've taken so far to answer the questions. The rest of the survey
  should take you no longer than 5 minutes to complete."
  Scale endpoint labels are the answer labels in the export. Answers are coded
  1..n in the order the questionnaire lists them, looked up by label (trailing
  spaces in labels such as "Mostly not targeted " are typography). Built: the 12
  trust items (competence, benevolence, integrity), credible, manipulative, the
  two transparency items, liking (1-5), agreement with the campaign's messages
  (1-5), felt targeted (1-5), the two social media trust items, confidence that
  online political adverts are regulated ("Don't know" coded 8 and not built, 7
  people) and acceptability of personalised political advertising.
* NOT BUILT. The two recall items ("did the adverts include information
  informing you who paid for them?" / "...if it had been targeted"): recall
  checks are not outcomes (docs/CONVENTIONS.md). The two attention checks.
  PERC_ID (where the respondent would place the party, left to right): the
  questionnaire lists eight positions plus "don't know" with garbled numbering,
  the export holds only seven of them, and 102 cells are blank with no "don't
  know" anywhere, so the offered scale and what a blank means cannot be
  determined. The eight "faith in reason" items (FIR_*): views about people in
  general, asked after the adverts, so neither a measure of the adverts nor a
  clean persona attribute.
* WHO. All 1,249 people in the export (all finished). The paper's 1,222 drops 26
  who took 270 seconds or less and one who gave their age as 4 (data_wrangle.Rmd:
  duration > 270, age > 17); the crosscheck applies that filter to the built rows
  and reproduces the paper's 611 per arm and its Table 1. The export has no
  respondent id, so `pid` is the 1-based row position in final_responses.csv.
* PERSONA. Asked BEFORE the adverts, so untouched by the manipulation: the ten
  items on politicians in the UK (ORIENT_1_*, ORIENT_2_*) and the five on MPs
  elected in 2019 (MISTRUST_EX_*, the attention check row left out), each on the
  seven-point agree scale, the answer label as the value. Asked at the END and
  mapped as stable facts: age, gender, education, party identification, left-right
  self-placement (`ideology`), interest in politics, use of social media for
  political information (two items) and six political activities in the last 12
  months. Age 4 (one person) is left absent. Gender "Prefer not to say" (3) is a
  non-answer. Left-right "I don't know" (71) is left absent, as QC requires of a
  label that carries no position. Education "Other, please specify" (6; free text
  not mapped) cannot be placed on the qualification ladder and is left absent;
  "A level, or equivelent" keeps its spelling. Education crosswalk scheme
  uk_gybnm_osf (data/catalog/persona_crosswalk_education.json), read from existing
  schemes' precedents, not asked of Jev.

    uv run python scripts/gen_gybnm.py --prep       # (re)write the coded .xlsx
    uv run python scripts/gen_gybnm.py --catalogue  # (re)write this study's images.json entries
    uv run python scripts/gen_gybnm.py            # write the recipe
    uv run python scripts/gen_gybnm.py --check    # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

RAW = REPO / "data" / "raw" / "gybnm"
RAW_CSV = RAW / "final_responses.csv"
DATA_FILE = "gybnm_coded.xlsx"
DATA = RAW / DATA_FILE
RECIPE = REPO / "recipes" / "images" / "gybnm.yaml"

CONDITION_VAR = "Condition"
ARM_CODES = {"none": 0, "paid for and targeting": 1}
ID_VAR = "pid"

# The four adverts: catalogue id stem, file stem in each arm, words printed on the
# control version. The disclaimer version adds "Political ad." under the party
# name and the banner below the picture.
ADS = [
    (
        "gybnm_ad1",
        1,
        [
            "We are listening.",
            "Our nation's political failures have come from an absence of new ideas, "
            "fresh perspectives, and insight into the lives of those across every sector "
            "of society",
        ],
        "5K-10K",
        "<£100",
    ),
    (
        "gybnm_ad2",
        2,
        [
            "UK politics has lost touch with what democracy really means. The Reconnect "
            "Party will address this.",
            "From health workers to farmers, builders to economists, pensioners to school goers",
            "The Reconnect Party was built by different people connected through the "
            "commitment to find effective political solutions, together",
        ],
        "1K-3K",
        "<£100",
    ),
    (
        "gybnm_ad3",
        3,
        [
            "Our candidates are ready to represent the diversity of our nation for the "
            "first time in the next general election.",
            "Most MPs have never had a job outside politics.",
            "All our candidates have worked in the real world and understand the "
            "demands, stresses and joys of the lives you lead.",
        ],
        "10K-30K",
        "£200-299",
    ),
    (
        "gybnm_ad4",
        4,
        [
            "We are a political party dedicated to democracy. Get in contact today to "
            "see how we can draw up new ideas together.",
            "RECONNECT PARTY",
            "together with you",
            "We don't expect you to just take our word for it.",
            "Click below to our website to read case by case examples of what we've "
            "already achieved to help citizens and local businesses.",
        ],
        "30K-60K",
        "£400-499",
    ),
]
NAME = "The Reconnect Party"
LOGO = ["RECONNECT PARTY", "together with you"]
FOOTER = [
    "WWW.RECONNECT.CO.UK/MANIFESTO",
    "Find out more about our plans on our website",
    "Learn more",
]


def banner(audience: str, spent: str) -> str:
    return (
        "Paid for by The Reconnect Party. The Reconnect Party shows you this ad on the "
        "basis of information about your income, age, and gender. Estimated audience "
        f"size: {audience}. Amount spent (GBP): {spent}."
    )


def ad_words(k: int, disclaimer: bool) -> str:
    """The catalogue's text_in_image for advert k: every block, top to bottom."""
    _, _, body, audience, spent = ADS[k]
    head = [NAME, "Political ad."] if disclaimer else [NAME]
    # Adverts 1-3 carry the logo box after their text; advert 4 above it, which
    # its own body list already places.
    middle = body if k == 3 else [*body, *LOGO]
    tail = [banner(audience, spent)] if disclaimer else []
    return " / ".join([*head, *middle, *tail, *FOOTER])


def image_id(k: int, disclaimer: bool) -> str:
    return f"{ADS[k][0]}_{'disclaimer' if disclaimer else 'control'}"


def image_file(k: int, disclaimer: bool) -> str:
    """Path under data/, as the catalogue records it."""
    n = ADS[k][1]
    name = f"material{n}_transparent.jpg" if disclaimer else f"control_{n}.jpg"
    return f"raw/gybnm/Experimental Materials/{name}"


FRAME = (
    "A Facebook-style sponsored post: the party's round grey shell-like logo and its name "
    "with a blue verified tick at the top{political}, the post's text below, then a "
    "picture, {banner}and a grey footer with the web address, a line of text and a "
    '"Learn more" button. Every word is quoted in text_in_image.'
)
PICTURES = [
    "The picture is a pale blue-grey panel with the slogan in black on the left and, on "
    "the right, a cut-away doll's house whose nine rooms each show people at work or at "
    "home (a meeting, a man at a whiteboard, an older man reading, a young man studying, "
    "two workers in high-visibility jackets, a farmer by a tractor, a mechanic, a woman "
    "at a laboratory bench, a father holding a small child); the party's logo box sits "
    "under the slogan.",
    "The picture shows, from above, four people working around a table covered with "
    "plans and a model of a city, with white text on a blue-grey panel over its left "
    "side and the party's logo box at the lower right.",
    "The picture is three panels inside a thin frame: a construction worker in a hard hat "
    "and high-visibility harness seen from behind, a train running through a misty forest, "
    "and a nurse seen from behind facing a whiteboard; white text runs across the middle "
    "with the party's logo box below it.",
    "The picture is split diagonally: on the left, the party's logo box and white text on "
    "black; on the right, a paintbrush with a burst of glossy grey paint on a light grey "
    "background.",
]


def description(k: int, disclaimer: bool) -> str:
    frame = FRAME.format(
        political=(', with "Political ad." and a small globe icon under the name')
        if disclaimer
        else "",
        banner="a bright yellow banner under the picture carrying the disclaimer, "
        if disclaimer
        else "",
    )
    return f"{frame} {PICTURES[k]}"


def catalogue_entries() -> dict[str, dict[str, str]]:
    """This study's entries in data/catalog/images.json."""
    from micromotives_datasets.images import sha256_of

    out: dict[str, dict[str, str]] = {}
    for disclaimer in (False, True):
        for k in range(len(ADS)):
            f = image_file(k, disclaimer)
            out[image_id(k, disclaimer)] = {
                "file": f,
                "sha256": sha256_of(REPO / "data" / f),
                "source": f"https://osf.io/gybnm/ (osfstorage, Experimental Materials/"
                f"{Path(f).name}; the questionnaire full_survey.pdf shows it in row {k + 1} "
                f"of its {'Experimental' if disclaimer else 'Control'} Condition column)",
                "licence": "CC0 1.0 Universal (OSF gybnm).",
                "text_in_image": ad_words(k, disclaimer),
                "description": description(k, disclaimer),
            }
    return out


def write_catalogue() -> None:
    """Add or refresh only this study's entries; re-read first, others are editing too."""
    import json

    path = REPO / "data" / "catalog" / "images.json"
    current = json.loads(path.read_text())
    current.update(catalogue_entries())
    path.write_text(json.dumps(current, indent=2, ensure_ascii=False))


# Questionnaire page 2, word-for-word (ASCII quotes), minus survey mechanics.
SHARED = (
    "As you've been informed, this survey is interested in understanding how you form "
    "judgments about political actors and organisations. In this next section, you will "
    "be shown a selection of 4 political advertisements created by a political party "
    "named The Reconnect Party. The adverts you see have been selected from their "
    "upcoming online ad campaign for the next general election. First, you will be shown "
    "the advertisements, then you will be asked about your perception of The Reconnect "
    "Party. It is important to remind you that the views and beliefs of The Reconnect "
    "Party do not represent those of the researchers of this study or of the University "
    "of Sheffield more widely. This study does not intend to promote a particular "
    "political viewpoint. The following provides a statement from the leader of The "
    'Reconnect Party to give you some background to their campaign: "Over the last '
    "decade, citizens from across the UK have come together through an organisation "
    "named Reconnect to discuss what they want for themselves and their communities. "
    "After years of preparation, we have formed a new political party - The Reconnect "
    "Party - offering citizens electoral candidates from a vast range of careers and "
    "backgrounds and a clear understanding of the nation's social and economic needs. "
    "Our growing party now has 30,000 members and 270 candidates across Scotland, "
    "England, Wales, and Northern Ireland ready to run for the first time in their local "
    "constituencies. We believe the UK deserves a politics every citizen can feel "
    'connected to."'
)
LEAD = "The four adverts were then shown:"


def arm_text(disclaimer: bool) -> str:
    quoted = [f'"{ad_words(k, disclaimer)}" <image>' for k in range(len(ADS))]
    return f"{LEAD} " + " ".join(quoted)


AGREE7 = [
    "Strongly disagree",
    "Disagree",
    "Somewhat disagree",
    "Neither agree nor disagree",
    "Somewhat agree",
    "Agree",
    "Strongly agree",
]
LIKE5 = [
    "Dislike a great deal",
    "Dislike somewhat",
    "Neither like nor dislike",
    "Like somewhat",
    "Like a great deal",
]
AGREE5 = [
    "Completely disagree",
    "Somewhat disagree",
    "Neither agree or disagree",
    "Somewhat agree",
    "Completely agree",
]
TARGET5 = [
    "Not at all targeted at me",
    "Mostly not targeted",
    "Somewhat targeted",
    "Mostly targeted",
    "Completely targeted at me",
]
ACCEPT7 = [
    "Not at all acceptable",
    "Mostly unacceptable",
    "Somewhat unacceptable",
    "Neither acceptable nor unacceptable",
    "Somewhat acceptable",
    "Mostly acceptable",
    "Completely acceptable",
]
DONT_KNOW = "Don't know"
DONT_KNOW_CODE = 8

# (variable, option list) in task order. Grid items carry their statement.
OUTCOME_VARS: list[tuple[str, list[str]]] = [
    *[(f"COMP_{i}", AGREE7) for i in range(1, 5)],
    *[(f"BENEV_{i}", AGREE7) for i in range(1, 5)],
    *[(f"INTEG_{i}", AGREE7) for i in range(1, 5)],
    ("AD_TRUST_1", AGREE7),
    ("AD_TRUST_2", AGREE7),
    ("AD_TRUST_4", AGREE7),
    ("AD_TRUST_5", AGREE7),
    ("LIKE", LIKE5),
    ("AGREE", AGREE5),
    ("SELF_TAR", TARGET5),
    ("SM_TRUST_1", AGREE7),
    ("SM_TRUST_2", AGREE7),
    ("REG_TRUST_1", AGREE7),
    ("DATA_ACCEPT", ACCEPT7),
]

PRE_ITEMS = [
    *[f"ORIENT_1_{i}" for i in range(1, 6)],
    *[f"ORIENT_2_{i}" for i in range(1, 6)],
    *[f"MISTRUST_EX_{i}" for i in (1, 2, 3, 5, 6)],
]
END_ITEMS = {
    "interest_in_politics": "POL_INT",
    "uses_social_media_for_information_about_party_politics_and_elections": "SM_USE_1",
    "uses_social_media_for_information_about_political_issues_in_general": "SM_USE_2",
    "in_last_12_months_done_work_for_a_political_party_or_action_group": "ELECT_PAR_1",
    "in_last_12_months_given_money_to_a_political_party_organisation_or_cause": "ELECT_PAR_2",
    "in_last_12_months_displayed_an_election_poster": "ELECT_PAR_3",
    "in_last_12_months_listened_to_or_watched_a_party_election_broadcast": "ELECT_PAR_4",
    "in_last_12_months_read_a_campaign_leaflet_letter_text_or_email_from_a_party": "ELECT_PAR_5",
    "in_last_12_months_tried_to_persuade_somebody_which_party_to_vote_for": "ELECT_PAR_6",
}
OTHER_EDUCATION = "Other, please specify"
GENDER_REFUSED = "Prefer not to say"
IDEOLOGY_DONT_KNOW = "I don't know"
IMPOSSIBLE_AGE = [4]


def _clean(text: str) -> str:
    """Typography only: straight quotes, single spaces. Words untouched."""
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip()


def question_texts() -> dict[str, str]:
    """Column -> the question text row of the Qualtrics export."""
    header = pd.read_csv(RAW_CSV, nrows=1)
    return {c: str(header[c].iloc[0]) for c in header.columns}


def _split(text: str) -> tuple[str, str | None]:
    """A grid item's export text is '<stem> - <statement>'."""
    if " - " in text:
        stem, statement = text.rsplit(" - ", 1)
        return _clean(stem), _clean(statement)
    return _clean(text), None


# Survey mechanics opening the social media trust screen, dropped (see notes).
PROGRESS = (
    "Thank you for the time you've taken so far to answer the questions. The rest of the "
    "survey should take you no longer than 5 minutes to complete. "
)


def question(var: str, texts: dict[str, str]) -> str:
    stem, statement = _split(texts[var])
    stem = stem.removeprefix(PROGRESS)
    return f'{stem} "{statement}"' if statement else stem


def persona_key(var: str, texts: dict[str, str]) -> str:
    _, statement = _split(texts[var])
    assert statement, var
    return re.sub(r"[^a-z0-9]+", "_", statement.lower()).strip("_")


def prep() -> pd.DataFrame:
    """The coded spreadsheet: every respondent, used columns, outcomes coded 1..n."""
    df = pd.read_csv(RAW_CSV, skiprows=[1, 2], low_memory=False)
    df.insert(0, ID_VAR, range(1, len(df) + 1))
    keep = [
        ID_VAR,
        CONDITION_VAR,
        *[v for v, _ in OUTCOME_VARS],
        *PRE_ITEMS,
        "AGE",
        "GENDER",
        "EDUCATION",
        "PARTY_IDENT",
        "LEFT_RIGHT",
        *END_ITEMS.values(),
    ]
    df = df[keep].copy()
    for var, options in OUTCOME_VARS:
        codes = {o: float(i) for i, o in enumerate(options, start=1)}
        if var == "REG_TRUST_1":
            codes[DONT_KNOW] = float(DONT_KNOW_CODE)
        answers = df[var].map(lambda v: v.strip() if isinstance(v, str) else v)
        stray = set(answers.dropna()) - set(codes)
        if stray:
            raise SystemExit(f"{var}: unexpected answers {sorted(stray)}")
        df[var] = answers.map(codes)
    for var in PRE_ITEMS:
        stray = set(df[var].dropna()) - set(AGREE7)
        if stray:
            raise SystemExit(f"{var}: unexpected answers {sorted(stray)}")
    return df


def _scale(options: list[str]) -> dict[str, Any]:
    s: dict[str, Any] = {
        "min": 1,
        "max": len(options),
        "min_label": options[0],
        "max_label": options[-1],
    }
    if len(options) % 2:
        s["mid_label"] = options[len(options) // 2]
    return s


def recipe() -> dict[str, Any]:
    ds = read_any(DATA)
    labels = ds.value_labels
    if set(ds.df[CONDITION_VAR].unique()) != set(ARM_CODES.values()):
        raise SystemExit(f"condition codes changed: {sorted(ds.df[CONDITION_VAR].unique())}")
    texts = question_texts()

    outcomes = []
    for t, (var, options) in enumerate(OUTCOME_VARS):
        if var in labels:
            raise SystemExit(f"{var}: not coded by --prep")
        outcomes.append(
            {
                "var": var,
                "task_num": t,
                "question": question(var, texts),
                "scale": _scale(options),
                "response_recode": {i: i for i in range(1, len(options) + 1)},
            }
        )

    arms = [
        {
            "raw": raw,
            "condition_num": n,
            "factors": {"disclaimer": level},
            "text": arm_text(bool(raw)),
            "images": [image_id(k, bool(raw)) for k in range(len(ADS))],
        }
        for n, (level, raw) in enumerate(ARM_CODES.items())
    ]

    def code_of(var: str, label: str) -> int:
        return next(int(k) for k, v in labels[var].items() if v == label)

    persona_map = {
        "age": "AGE",
        "gender": "GENDER",
        "education": "EDUCATION",
        "party_id": "PARTY_IDENT",
        "ideology": "LEFT_RIGHT",
        **{persona_key(v, texts): v for v in PRE_ITEMS},
        **END_ITEMS,
    }
    return {
        "study_id": "gybnm",
        "source": "osf",
        "title": "Political advert disclaimers: four adverts from a fictional party, with or "
        "without a paid-for-by and targeting disclaimer; trust in the party and its adverts",
        "data_file": DATA_FILE,
        "licence": "CC0 1.0 Universal (OSF gybnm).",
        "comparable_to_socsci210": False,
        "participant_id_var": ID_VAR,
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_var": CONDITION_VAR,
            "factors": ["disclaimer"],
            "shared_context": SHARED,
            "arms": arms,
        },
        "outcomes": outcomes,
        "response_recode": {},
        "missing_codes": [DONT_KNOW_CODE],
        "persona_map": persona_map,
        "persona_missing": {
            "AGE": IMPOSSIBLE_AGE,
            "GENDER": [code_of("GENDER", GENDER_REFUSED)],
            "EDUCATION": [code_of("EDUCATION", OTHER_EDUCATION)],
            "LEFT_RIGHT": [code_of("LEFT_RIGHT", IDEOLOGY_DONT_KNOW)],
        },
    }


def render() -> str:
    return yaml.safe_dump(recipe(), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--prep", action="store_true", help="write the coded .xlsx from the deposit")
    ap.add_argument("--catalogue", action="store_true", help="add this study's images.json entries")
    args = ap.parse_args()
    if args.catalogue:
        write_catalogue()
        print("updated data/catalog/images.json (gybnm entries only)")
        return 0
    if args.prep:
        prep().to_excel(DATA, index=False)
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
