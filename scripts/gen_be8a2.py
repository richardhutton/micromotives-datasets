#!/usr/bin/env python3
"""Write recipes/images/be8a2.yaml: digital imprints on campaigners' posts (IMG54).

Gordon and colleagues (Sheffield), with the Electoral Commission, "The impact of UK
transparency legislation on citizen informedness and trust (survey experiment)",
OSF be8a2 (CC0 1.0 Universal). The deposit holds the questionnaire
(survey_final.pdf, "Electoral Commission Digital Imprints Experiment: Survey Flow"),
a codebook (codebook.md), the Qualtrics data as read into R (Data wrangle/
main_data.csv), the authors' cleaning script (main_datawrangle.Rmd), their processed
files (Processed data/), the knitted analysis (knitted_analysis_script.pdf) and four
high-resolution pictures of the imprint versions (Experimental Materials/). No
paper is published yet that we could find; the knitted analysis is the answer key.

UK adults (Prolific, March 2024) were split between subjects into two groups, one
of which first read a short text about the new law requiring digital imprints, and
then each saw four Facebook posts from four fictional third-party campaigners. Two
of the four carried a digital imprint ("Promoted by: <name>, <address>") and two
did not; which two was randomised, so every post was seen in both versions by
different people. After EACH post they answered the same 13 questions about it.

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* DESIGN. A within-person design: one row per person per post, so a person's four
  posts are four conditions and the coded file is LONG (`pid`, `post`, `imprint`,
  `training`). 16 arms: the education text (shown or not, between subjects) x the
  post (4) x the imprint (absent or present). condition_num = training * 8 +
  (post - 1) * 2 + imprint. Each row names the post it rates and whether it carried
  the imprint, so a person's four ratings of one question are four different
  conditions (QC rule 24).
* ASSIGNMENT. `Training.condition` 0 = no education text, 1 = the text (codebook).
  `Advert.<k>` 0/1 = post k shown without/with its imprint (codebook: "version - 0
  = no imprint viewed, 1 = imprint viewed"). The data agree with the coding: for
  every person, post k's answers sit in exactly one set of columns, the plain set
  (`PK_<k>_1`...) when `Advert.<k>` is 0 and the imprint set (`PK_<k>imprint_1`...)
  when it is 1, never both (checked in --prep), and each person has exactly two
  imprints, one on post 1 or 2 and one on post 3 or 4 (four patterns, each crossed
  with both education groups, 159-180 people per cell). Post k is the questionnaire's "Advert k", which the authors' script
  names: Common Sense Collective 1, Breaking Barriers Alliance 2, Speak Freely Inc.
  3, Campaign for a better Britain 4; the pictures under each "Advert k" heading
  show that campaigner.
* PICTURES. The eight pictures are the questionnaire's own (survey_final.pdf pages
  2-4, "No imprint version" left, "Imprint version" right under each "Advert k"),
  extracted unaltered with poppler's pdfimages; positions read with pdftohtml. The
  deposit's "Experimental Materials" hold only the four imprint versions, as later
  re-captures: higher resolution, cropped differently, and in Breaking Barriers
  Alliance with the link address and photo credit NOT blurred where the
  questionnaire's picture blurs them. Using them for the imprint version and the
  questionnaire for the plain one would make each pair differ in more than the
  imprint, so all eight come from the questionnaire. Those re-captures were used
  only to read characters too small to read in the questionnaire's pictures (the
  Breaking Barriers Alliance comments and imprint), where the two show the same
  layout. The Breaking Barriers Alliance pictures are 781x489 and 765x479 pixels,
  so much of their small text is legible only through text_in_image.
* WORDS IN THE PICTURES (text_in_image). Every word the campaigner and the
  commenters wrote: page or account name, date, the post's text, the words of its
  graphic (headline, caption, masthead, link card), comments, a group's own About
  text, and in the imprint version the imprint. " / " separates blocks; line wraps
  inside a block are joined with a space; quotes and apostrophes are straightened.
  Left out, and described instead: words of the browser and of Facebook's own
  interface (navigation, Like/Comment/Share, "Most relevant", "Write a comment...",
  "View all 7 replies", "Join Group", comment ages), counts of reactions, comments,
  shares and members, words that are part of a photograph (protest banners,
  labels on props, vehicle markings, the cut-out newspaper headlines in the
  Common Sense Collective collage, which are partly covered and partly cut off),
  blurred names and link addresses, and a cut-off fragment at the foot of Speak
  Freely Inc.'s picture. Typos are the source's ("Common Sence", "does nor
  represent", "Primrose Kane").
* CONDITION. No shared context. Each arm's text is its group's text before the
  posts, word-for-word (questionnaire page 1; the codebook gives the same words),
  then the post. "Please view the post below and answer a few questions on the
  following page. Please pay attention as you won't be able to go back." is
  dropped as survey mechanics. Words that are OURS: "One of the four posts:". The
  order the four posts were shown in is not recorded and nothing is said about it,
  nor about which of the person's other posts carried imprints.
* OUTCOMES. 13 per post. The questionnaire PDF is the pre-fielding survey flow,
  and the authors note it differs from what was fielded ("ERROR IN PREREGISTERED
  SURVEY THAT INCLUDED THE WRONG VERSION OF 'INFORMED, ITEM 4' (in the final survey,
  this item was reworded to be positively phrased...)"); the data's answer labels
  also differ from it (political interest has "Slightly interested" and no "Don't
  know"). Wording therefore follows the codebook, which the authors wrote against
  the final survey: informed item 4 is "I can make an informed judgement about who
  is behind this material" (the PDF's negative "I do not feel able to make..." was
  not fielded), and persuasion item 2 is "This post promotes a particular
  viewpoint" where the PDF has "The post promotes" (a disclosed choice of source;
  no fielded export survives to settle it). Stems are the codebook's and the PDF's
  (they agree). The persuasion items' answer labels say "Slightly" and the others
  "Somewhat" (the data's own labels; the authors' script notes the difference).
  The four word pairs are asked as the stem followed by the pair in quotation marks. "I am not sure
  who is behind the material" is built as answered (agreement 1-7), NOT
  reverse-scored as the authors' informed scale does.
  Built: PK 1-4 (advert, viewpoint, is an advertisement, intended to influence),
  agreement with the post's message, informed 1-4 (political goal, enough
  information, not sure who, informed judgement), accurate, trustworthy,
  believable, factual.
* NOT BUILT. Post 2's attention check (informed_2_5 / informed_2imprint_5) and
  EPE_5. Everything after the four posts that is asked once (confidence in the
  regulation of online campaigning, how many imprints recalled, which campaigners
  recalled, who would find the information useful, knowledge of regulation,
  political information efficacy, the open question): their condition would be
  the whole sequence of four posts in an order the data do not record, and recall
  items are checks, not outcomes (docs/CONVENTIONS.md).
* WHO. Every person with answers: 1,357 of the export's 1,369 rows (9 gave no
  consent, 3 declined; all 12 have no data). The authors' 1,322 also drop 4 who
  failed both attention checks (their rows 420, 948, 1288 and 1315 after the 12
  blank rows are removed) and anyone faster than 360 seconds; the crosscheck
  applies that filter to the built rows and reproduces their processed file
  answer for answer and their descriptives table. `pid` is the 1-based row in
  main_data.csv, which is the authors' own `id` (row_number() before exclusions).
* PERSONA. All asked at the end (Stage 4) or recorded by Prolific, and mapped as
  stable facts: age (the data hold age; the questionnaire asked year of birth),
  gender, education, party identification, ethnicity (Prolific's
  `Ethnicity.simplified`, crosswalk scheme uk_ons_five_group_short), interest in
  politics, time spent online on news about politics, and how often the person
  uses Facebook. Gender "Prefer not to say" (7) and ethnicity blanks (6) are left
  absent; education "Other, please specify" (15; free text not mapped) cannot be
  placed on the ladder; time online "Not sure" (9) carries no amount. Party "Other,
  please specify___________" (23) is a real answer whose label carries the form's
  instruction, rewritten to "Other" (`persona_label_rewrite`), as gybnm's export
  labels it; the free text is not mapped. Trailing spaces, tabs and blank fill-in
  lines in labels are dropped as typography. NOT mapped: trust, mistrust and
  cynicism about politicians, satisfaction with democracy, and political efficacy,
  which are attitudes asked AFTER the manipulation; Prolific's employment and
  student status (199-262 "DATA_EXPIRED"), sex (the survey's gender is mapped),
  nationality and country. Education crosswalk scheme uk_be8a2_osf
  (data/catalog/persona_crosswalk_education.json), read from existing schemes'
  precedents, not asked of Jev.

    uv run python scripts/gen_be8a2.py --extract    # (re)write the eight pictures
    uv run python scripts/gen_be8a2.py --prep       # (re)write the coded long .xlsx
    uv run python scripts/gen_be8a2.py --catalogue  # (re)write this study's images.json entries
    uv run python scripts/gen_be8a2.py              # write the recipe
    uv run python scripts/gen_be8a2.py --check      # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

STUDY = "be8a2"
RAW = REPO / "data" / "raw" / STUDY
RAW_CSV = RAW / "Data wrangle" / "main_data.csv"
PDF = RAW / "survey_final.pdf"
PICTURES_DIR = "survey_images"
DATA_FILE = "be8a2_coded.xlsx"
DATA = RAW / DATA_FILE
RECIPE = REPO / "recipes" / "images" / f"{STUDY}.yaml"

ID_VAR = "pid"
TRAINING_VAR = "training"
POST_VAR = "post"
IMPRINT_VAR = "imprint"
TRAINING_LEVELS = {0: "not shown", 1: "shown"}
IMPRINT_LEVELS = {0: "absent", 1: "present"}

# ---------------------------------------------------------------------------
# The four posts. (key, campaigner, PDF page, pdfimages number of the no-imprint
# and imprint picture, blocks of words before the imprint's place, the imprint,
# blocks after it.) The imprint sits where it was printed: across the top of the
# picture (1), along the foot of the photograph (2), at the foot of the dark panel
# (3), under the post's date (4).
# ---------------------------------------------------------------------------

CSC_BEFORE = [
    "Common Sense Collective",
    "1 November",
    "The Conservative Party is turning towards the radical right.",
    "We do not say this lightly - there is a conscious strategy to adopt the language and "
    "policies of the radical right.",
    "Read 'Turning Right: The Dangerous Transformation of the Conservative Party'.",
]
CSC_AFTER = [
    "TURNING RIGHT",
    "THE DANGEROUS TRANSFORMATION OF THE CONSERVATIVE PARTY",
    "Common Sense Collective",
    "COMMONSENSECOLLECTIVE.ORG.UK",
    "Turning Right: The Dangerous Transformation of the Conservative Party",
    "Common Sence Collective has a proud history of opposing the far right for almost 20 years...",
]
BBA_AFTER = [
    "Breaking Barriers Alliance",
    "11 October",
    "If Labour is serious about overhauling the NHS, its TOP priority should be ending the "
    "wounding privatisation of the last 13 years. #reinstatethenhs #onlythenhs",
    "Labour is dead for crying out loud... it's been rigged by the right wing. Can't you "
    "understand that???",
    "And the failed PFI and creeping private involvement prior to that initiated by Labour",
    "How can they be serious about ending what they started! They are all the same no matter "
    "what banner they hide under.",
    "I'll not hold my breath. We all know his track record on future policy....",
    "This group is getting so partisan. Urgh! You're deliberately ignoring Labour's "
    "privatisation efforts and Blair's PFI!!!",
]
SFI_BEFORE = [
    "Speak Freely Inc.",
    "27 November at 18:41",
    "NHS delays are KILLING us.",
    "We can't wait this long for emergency care.",
    "We can't wait this long for operations.",
    "We can't wait this long for referrals.",
    "Last year saw a man die while waiting 18 minutes for an answer to his 999 call. It's "
    "horrific, and it's not on.",
    "NHS care delays in England harmed 8,000 people and caused 112 deaths last year",
    "The Guardian",
    "Newspaper of the year",
    "WE CAN'T WAIT",
    "Ambulances outside the Royal London hospital in London. The Patients Association "
    "described 'a disaster unfolding across the NHS'. Photograph: James Manning/PA",
]
CBB_BEFORE = [
    "Group by Campaign for a better Britain",
    "Campaign for a better Britain",
    "Campaign for a better Britain",
    "1 November 2023",
]
CBB_AFTER = [
    "From my own lived experience my current MP Lucy Fraser does nor represent me or any "
    "other person in her constituency that does not agree with Conservative party policy. "
    "It would be the same whatever the party if a different party to the one you support "
    "were elected. The majority of the time MP vote in line with party policy. MPs therefore "
    "represent party rather than constituent. Because of Parliament Protocol no other MP can "
    "represent me in parliament effectively leaving me with no representation. I believe it "
    "would be a mistake replacing Lords with elected representative. It would be nothing more "
    "than duplicating the House of Commons. It would just be another lot of MP following party "
    "politic (policies chosen by biggest donors to the party). At whatever level politics, "
    "policy is influenced by money whether it is lobbying or donations to political parties. "
    "I would prefer to see change in the way people are appointed to the Lords rather that "
    "directly elected politician. I would like to see businessmen and politicians and legal "
    "professions excluded from the Lords. I would also like to representation of other "
    "religions. Any election system chosen by government would be one that benefited the "
    "ruling party. Getting a fair system would be like getting turkeys to vote for Christmas",
    "Very well argued. One of the obvious changes would be to bring in PR. That would mean an "
    "end to wasted votes(more or less).",
    "Campaign for a better Britain is a community of activists and volunteers committed to "
    "introducing Proportional Representation to the House of Commons.",
    "United Kingdom",
]

POSTS: list[dict[str, Any]] = [
    {
        "key": "csc",
        "name": "Common Sense Collective",
        "page": 2,
        "pdfimages": (1, 3),
        "before": CSC_BEFORE,
        "imprint": "Promoted by: Common Sense Collective, 5 Birch Lane, Ancoats, Manchester, "
        "NYZ 497",
        "after": CSC_AFTER,
    },
    {
        "key": "bba",
        "name": "Breaking Barriers Alliance",
        "page": 3,
        "pdfimages": (5, 11),
        "before": [],
        "imprint": "Promoted by: Breaking Barriers Alliance, 2 Aberdere Lane, Wrexham, Wales, "
        "LL4 261",
        "after": BBA_AFTER,
    },
    {
        "key": "sfi",
        "name": "Speak Freely Inc.",
        "page": 3,
        "pdfimages": (7, 9),
        "before": SFI_BEFORE,
        "imprint": "Promoted by: Speak Freely Inc., 42 Primrose Kane, Camden Town, London, "
        "WC1b 734",
        "after": [],
    },
    {
        "key": "cbb",
        "name": "Campaign for a better Britain",
        "page": 4,
        "pdfimages": (12, 14),
        "before": CBB_BEFORE,
        "imprint": "Promoted by: Campaign for a better Britain, 47 St Lotts Road, Birmingham, "
        "B6U 2TU",
        "after": CBB_AFTER,
    },
]


def post_words(k: int, imprint: bool) -> str:
    """The catalogue's text_in_image for post k (0-based)."""
    p = POSTS[k]
    middle = [p["imprint"]] if imprint else []
    return " / ".join([*p["before"], *middle, *p["after"]])


def image_id(k: int, imprint: bool) -> str:
    return f"be8a2_{POSTS[k]['key']}_{'imprint' if imprint else 'no_imprint'}"


def image_file(k: int, imprint: bool) -> str:
    """Path under data/, as the catalogue records it."""
    return f"raw/{STUDY}/{PICTURES_DIR}/{image_id(k, imprint)}.png"


DESCRIPTIONS = [
    "A screenshot of a desktop web browser at facebook.com showing a Facebook post from "
    "Common Sense Collective, a page whose round logo shows a light bulb over an open book "
    "among teal leaves, with a blue verified tick. Below the post's text is a black-and-white collage of cut-out newspaper "
    "headlines about migrants, small boats, human rights law and Brexit, photographs of "
    "politicians, the Houses of Parliament and Big Ben, a protest placard and a "
    '"GBN" logo, with a white panel in the middle carrying the title and the page\'s logo. '
    "Under the picture is a grey link card. The post has 34 reactions (like, laughing, angry), "
    "18 comments and 5 shares, and no comments are shown.",
    "A screenshot of a desktop web browser at facebook.com showing a photograph opened from "
    "a Facebook post by Breaking Barriers Alliance, with the post's text and comments in a "
    "panel on the right. The photograph shows four people in business clothes standing on a paved "
    "square, wearing large printed face masks of politicians and holding cardboard knives "
    'labelled "Alliance Medical", "serco", "virgin" and "Greensill" over a blue box marked '
    '"NHS". Under the post\'s text are a link whose address is partly blurred out and a '
    '"Photo by" credit whose name is blurred; the post has 193 reactions, 27 comments and '
    "47 shares, and five comments are shown, the commenters' names blurred. The picture "
    "is small, so most of its text is hard to read.",
    "A screenshot of a desktop web browser at facebook.com showing a Facebook post from "
    "Speak Freely Inc., a page whose logo is a megaphone with a burst of colour from its "
    "mouth, with a blue verified tick, each of the middle three lines of text beginning with a red alarm-clock "
    "emoji. The post's picture, on a dark panel, is a screenshot of a Guardian news "
    'article: the headline with "8,000" circled and "112 deaths" underlined in orange, '
    "and a photograph of a paramedic wheeling a stretcher past a line of yellow London "
    'ambulances, overlaid with "WE CAN\'T WAIT" in white on an orange band, then the '
    "photograph's caption. The post has 70 reactions (like, angry, sad), 26 comments and "
    "21 shares; the top of one comment is cut off at the foot.",
    "A screenshot of a desktop web browser at facebook.com showing a public Facebook group, "
    "Campaign for a better Britain (7.1K members). Its cover photograph shows campaigners "
    'in front of a Gothic stone building holding purple banners reading "THE PEOPLE WANT '
    'PROPORTIONAL REPRESENTATION! PARLIAMENT IT\'S TIME TO MAKE VOTES MATTER!" and "MAKE '
    'VOTES MATTER". Below, a post by the group itself, with a ballot-box logo, carries a '
    "long text, 4 likes and 4 comments, one of which is shown with the commenter's name "
    "blurred. On the right, the group's About box, marked public and visible.",
]
IMPRINT_CLAUSE = [
    "In this version a black band across the top of the picture carries the imprint in white.",
    "In this version the imprint runs in white text with a black outline along the foot of the "
    "photograph.",
    "In this version the imprint is printed in grey on the dark panel below the article.",
    "In this version the imprint is printed in small grey text under the post's date.",
]
NO_IMPRINT_CLAUSE = "This version carries no imprint."


def description(k: int, imprint: bool) -> str:
    return f"{DESCRIPTIONS[k]} {IMPRINT_CLAUSE[k] if imprint else NO_IMPRINT_CLAUSE}"


def extract() -> None:
    """Write the eight pictures, unaltered, from the questionnaire with pdfimages."""
    out = RAW / PICTURES_DIR
    out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdfimages", "-png", str(PDF), f"{tmp}/img"], check=True)
        for k, p in enumerate(POSTS):
            for imprint, num in zip((False, True), p["pdfimages"], strict=True):
                src = Path(tmp) / f"img-{num:03d}.png"
                shutil.copyfile(src, REPO / "data" / image_file(k, imprint))


def catalogue_entries() -> dict[str, dict[str, str]]:
    """This study's entries in data/catalog/images.json."""
    from micromotives_datasets.images import sha256_of

    out: dict[str, dict[str, str]] = {}
    for k, p in enumerate(POSTS):
        for imprint in (False, True):
            f = image_file(k, imprint)
            side = "Imprint version" if imprint else "No imprint version"
            out[image_id(k, imprint)] = {
                "file": f,
                "sha256": sha256_of(REPO / "data" / f),
                "source": f"https://osf.io/be8a2/ (osfstorage, survey_final.pdf page {p['page']}, "
                f'the "{side}" picture under "Advert {k + 1}"; extracted unaltered with '
                f"poppler pdfimages -png, image {p['pdfimages'][int(imprint)]})",
                "licence": "CC0 1.0 Universal (OSF be8a2). The mock-up embeds third-party "
                "photographs and graphics whose own terms the deposit does not state.",
                "text_in_image": post_words(k, imprint),
                "description": description(k, imprint),
            }
    return out


def write_catalogue() -> None:
    """Add or refresh only this study's entries; re-read first, others are editing too."""
    import json

    path = REPO / "data" / "catalog" / "images.json"
    current = json.loads(path.read_text())
    current.update(catalogue_entries())
    path.write_text(json.dumps(current, indent=2, ensure_ascii=False))


# Questionnaire page 1 (and the codebook), word-for-word, ASCII apostrophes.
INTRO = {
    1: "Some of the posts you might see when browsing on social media are political campaign "
    "posts. A new transparency law for online political campaigning has just come into force. "
    "Now, most digital campaign material will require details of who paid for and produced "
    "it. This is designed to help voters know who is trying to reach them online and "
    "influence their vote. You are about to see four randomly selected social media posts. "
    "Please review each example and answer a short number of questions about what you've "
    "seen.",
    0: "You are about to see four social media posts. Please review each example and answer a "
    "short number of questions about what you've seen.",
}
LEAD = "One of the four posts:"


def arm_text(training: int, k: int, imprint: bool) -> str:
    return f'{INTRO[training]} {LEAD} "{post_words(k, imprint)}" <image>'


AGREE_SLIGHTLY = [
    "Strongly disagree",
    "Disagree",
    "Slightly disagree",
    "Neither agree nor disagree",
    "Slightly agree",
    "Agree",
    "Strongly agree",
]
AGREE_SOMEWHAT = [o.replace("Slightly", "Somewhat") for o in AGREE_SLIGHTLY]

PK_STEM = (
    "Thinking about the image you've just seen, to what extent do you agree or disagree "
    "with the following statements."
)
INFORMED_STEM = (
    "To what extent do you agree or disagree with the following statements about the "
    "materials you have seen?"
)
PAIR_STEM = (
    "Please circle the number in between each pair of words which represents how you feel "
    "about the material you've just seen."
)

# (coded column, raw stem in main_data.csv with {k}{v} for post and version,
#  question, options or (min label, max label) for a 1-7 pair)
OUTCOMES: list[tuple[str, str, str, list[str] | tuple[str, str]]] = [
    ("PK1", "PK_{k}{v}_1", f'{PK_STEM} "The post feels like an advertisement"', AGREE_SLIGHTLY),
    (
        "PK2",
        "PK_{k}{v}_2",
        f'{PK_STEM} "This post promotes a particular viewpoint"',
        AGREE_SLIGHTLY,
    ),
    ("PK3", "PK_{k}{v}_3", f'{PK_STEM} "The post is an advertisement"', AGREE_SLIGHTLY),
    (
        "PK4",
        "PK_{k}{v}_4",
        f'{PK_STEM} "The post is intended to influence your opinion"',
        AGREE_SLIGHTLY,
    ),
    (
        "AGREE",
        "agree_{k}{v}",
        "To what extent do you agree or disagree with the message promoted by the post?",
        AGREE_SOMEWHAT,
    ),
    (
        "INF1",
        "informed_{k}{v}_1",
        f'{INFORMED_STEM} "The material had a political goal"',
        AGREE_SOMEWHAT,
    ),
    (
        "INF2",
        "informed_{k}{v}_2",
        f'{INFORMED_STEM} "The material contained enough information to know who placed the '
        'material"',
        AGREE_SOMEWHAT,
    ),
    (
        "INF3",
        "informed_{k}{v}_3",
        f'{INFORMED_STEM} "I am not sure who is behind the material"',
        AGREE_SOMEWHAT,
    ),
    (
        "INF4",
        "informed_{k}{v}_4",
        f'{INFORMED_STEM} "I can make an informed judgement about who is behind this material"',
        AGREE_SOMEWHAT,
    ),
    (
        "ACCURATE",
        "accurate_{k}{v}",
        f'{PAIR_STEM} "Inaccurate" - "accurate"',
        ("Inaccurate", "accurate"),
    ),
    (
        "TRUSTWORTHY",
        "trustworthy_{k}{v}",
        f'{PAIR_STEM} "Untrustworthy" - "trustworthy"',
        ("Untrustworthy", "trustworthy"),
    ),
    (
        "BELIEVABLE",
        "believable_{k}{v}",
        f'{PAIR_STEM} "Unbelievable" - "believable"',
        ("Unbelievable", "believable"),
    ),
    (
        "FACTUAL",
        "factual_{k}{v}",
        f'{PAIR_STEM} "Opinionated" - "factual"',
        ("Opinionated", "factual"),
    ),
]


def raw_column(stem: str, k: int, imprint: bool) -> str:
    """main_data.csv's column for post k (1-based) in one version.

    The plain version is `PK_1_1` / `agree_1`; the imprint version inserts
    "imprint" after the post number: `PK_1imprint_1` / `agree_1imprint`.
    """
    return stem.format(k=k, v="imprint" if imprint else "")


PERSONA_RAW = {
    "age": "age",
    "gender": "gender",
    "education": "education",
    "party_id": "partyID",
    "ethnicity": "Ethnicity.simplified",
    "interest_in_politics": "political_interest",
    "time_spent_online_on_news_about_politics_and_current_affairs_on_an_average_day": "SM_use",
    "how_often_uses_facebook": "SM_frequency_1",
}
GENDER_REFUSED = "Prefer not to say"
OTHER_PARTY = "Other, please specify"
OTHER_EDUCATION = "Other, please specify"
TIME_NOT_SURE = "Not sure"


def _label(v: Any) -> Any:
    """Typography only: trim spaces, tabs and a fill-in blank line. Words untouched."""
    if not isinstance(v, str):
        return v
    return re.sub(r"_{3,}$", "", v.strip()).strip()


def prep() -> pd.DataFrame:
    """The coded long spreadsheet: one row per person per post, answers coded 1..7."""
    wide = pd.read_csv(RAW_CSV, low_memory=False)
    wide.insert(0, ID_VAR, range(1, len(wide) + 1))
    wide = wide[wide["Training.condition"].notna()]
    rows = []
    for _, r in wide.iterrows():
        imprints = [int(r[f"Advert.{k}"]) for k in range(1, 5)]
        if sum(imprints) != 2:
            raise SystemExit(f"pid {r[ID_VAR]}: {sum(imprints)} imprints")
        for k in range(1, 5):
            shown = bool(imprints[k - 1])
            out: dict[str, Any] = {
                ID_VAR: r[ID_VAR],
                TRAINING_VAR: int(r["Training.condition"]),
                POST_VAR: k,
                IMPRINT_VAR: int(shown),
            }
            for col, stem, _, options in OUTCOMES:
                other = r[raw_column(stem, k, not shown)]
                if pd.notna(other):
                    raise SystemExit(f"pid {r[ID_VAR]} post {k}: answer in the unshown version")
                value = r[raw_column(stem, k, shown)]
                if isinstance(options, list):
                    codes = {o: float(i) for i, o in enumerate(options, start=1)}
                    value = _label(value)
                    if pd.notna(value) and value not in codes:
                        raise SystemExit(f"{col}: unexpected answer {value!r}")
                    value = codes.get(value) if pd.notna(value) else None
                elif pd.notna(value) and value not in range(1, 8):
                    raise SystemExit(f"{col}: unexpected answer {value!r}")
                out[col] = value
            for var in PERSONA_RAW.values():
                out[var] = _label(r[var])
            rows.append(out)
    return pd.DataFrame(rows)


def _scale(options: list[str] | tuple[str, str]) -> dict[str, Any]:
    if isinstance(options, tuple):
        return {"min": 1, "max": 7, "min_label": options[0], "max_label": options[1]}
    return {
        "min": 1,
        "max": len(options),
        "min_label": options[0],
        "max_label": options[-1],
        "mid_label": options[len(options) // 2],
    }


def condition_num(training: int, k: int, imprint: int) -> int:
    """k is 0-based."""
    return training * 8 + k * 2 + imprint


def recipe() -> dict[str, Any]:
    ds = read_any(DATA)
    labels = ds.value_labels
    for var, expect in (
        (TRAINING_VAR, {0, 1}),
        (POST_VAR, {1, 2, 3, 4}),
        (IMPRINT_VAR, {0, 1}),
    ):
        if set(ds.df[var].unique()) != expect:
            raise SystemExit(f"{var} codes changed: {sorted(ds.df[var].unique())}")

    outcomes = []
    for t, (col, _, question, options) in enumerate(OUTCOMES):
        if col in labels:
            raise SystemExit(f"{col}: not coded by --prep")
        outcomes.append(
            {
                "var": col,
                "task_num": t,
                "question": question,
                "scale": _scale(options),
                "response_recode": {i: i for i in range(1, 8)},
            }
        )

    arms = [
        {
            "raw_values": {TRAINING_VAR: training, POST_VAR: k + 1, IMPRINT_VAR: imprint},
            "condition_num": condition_num(training, k, imprint),
            "factors": {
                "education_text": TRAINING_LEVELS[training],
                "post": POSTS[k]["name"],
                "imprint": IMPRINT_LEVELS[imprint],
            },
            "text": arm_text(training, k, bool(imprint)),
            "images": [image_id(k, bool(imprint))],
        }
        for training in (0, 1)
        for k in range(len(POSTS))
        for imprint in (0, 1)
    ]

    def code_of(var: str, label: str) -> int:
        return next(int(k) for k, v in labels[var].items() if v == label)

    return {
        "study_id": STUDY,
        "source": "osf",
        "title": "Digital imprints: four Facebook posts from fictional campaigners, each seen "
        "with or without its imprint, after an education text or none; how each post was read",
        "data_file": DATA_FILE,
        "licence": "CC0 1.0 Universal (OSF be8a2).",
        "comparable_to_socsci210": False,
        "participant_id_var": ID_VAR,
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_vars": [TRAINING_VAR, POST_VAR, IMPRINT_VAR],
            "factors": ["education_text", "post", "imprint"],
            "arms": arms,
        },
        "outcomes": outcomes,
        "response_recode": {},
        "missing_codes": [],
        "persona_map": PERSONA_RAW,
        "persona_missing": {
            "gender": [code_of("gender", GENDER_REFUSED)],
            "education": [code_of("education", OTHER_EDUCATION)],
            "SM_use": [code_of("SM_use", TIME_NOT_SURE)],
        },
        "persona_label_rewrite": {"partyID": {code_of("partyID", OTHER_PARTY): "Other"}},
    }


def render() -> str:
    return yaml.safe_dump(recipe(), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--extract", action="store_true", help="write the eight pictures")
    ap.add_argument("--prep", action="store_true", help="write the coded .xlsx from the deposit")
    ap.add_argument("--catalogue", action="store_true", help="add this study's images.json entries")
    args = ap.parse_args()
    if args.extract:
        extract()
        print(f"wrote data/raw/{STUDY}/{PICTURES_DIR}/")
        return 0
    if args.catalogue:
        write_catalogue()
        print("updated data/catalog/images.json (be8a2 entries only)")
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
