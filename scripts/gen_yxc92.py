#!/usr/bin/env python3
"""Write recipes/images/yxc92.yaml: "Join This Group", WhatsApp inoculation (IMG75).

Maertens, Basol, Roozenbeek, Azevedo, Cook & van der Linden, "Inoculation Against
Misinformation on Closed Messaging Platforms: 'Join This Group' ...", OSF yxc92,
Study 1 (UK). Fielded on Prolific in January 2020 by the Cambridge Social
Decision-Making Lab; it is chapter 3 of Melisa Basol's PhD thesis ("Essays on
resistance against persuasion", Cambridge 2022, Apollo repository), which is the
earlier write-up and is cited below as "the thesis".

Design. Everyone rated 16 WhatsApp screenshots (three questions each, 1-7), was then
randomised to play the Join This Group game or Tetris, rated the same 16 screenshots
again, and about a week later rated them a third time in a separate follow-up
survey. Every row is one screenshot, one question, at one of those three moments.

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* DATA. `JTG - Study 1 (UK) - Raw Data.csv` (the authors' merged, anonymised T0+T10
  file, one row per person, a Qualtrics CHOICE-TEXT export: Gender reads "Female").
  `--prep` writes `yxc92_coded.xlsx`: one row per person with T0 data, a `pid`
  (1-based row number in the raw file; the deposit has no identifier, by design),
  the used columns, and one `stim_<moment>_<item>` column per screenshot and moment
  holding the arm that person met there, blank where no row may be built. The
  ratings are the displayed labels "1".."7": two matrices (Real1, Real3) have
  internal answer keys 1,5..10 and 1,4..9, which a numeric export would have shown;
  the data hold only 1..7, which is the text export reading the labels.
* ARM. The T0 survey flow (T0.qsf) runs a BlockRandomizer (SubSet 1,
  EvenPresentation) over two branches: a group that sets embedded data `Tetris` = 1
  and then shows the "Control - Tetris" block, and the "Inoculation - WhatsApp game"
  block. So `Tetris` is the randomiser's own record, not an inference; the tracker's
  "arm from timing columns" is corroboration only. Cross-tab (asserted in --prep):
  every `Tetris` = 1 has no Join This Group page timing, every blank has no Tetris
  timing, 504 of 505 `Tetris` = 1 carry Tetris page timing and all 473 blanks that
  reached the randomiser carry game page timing (505 vs 473: even presentation over
  978). One `Tetris` = 1 person has no Tetris page timing; the flow puts that block
  directly after the assignment, so they are kept as Tetris, as the authors keep
  them. Game arm restricted, as the authors restrict it (Script 2, step 5), to the
  people who typed the password shown at the end of the game (their list of 16
  accepted spellings): 417 of 473. The 56 others reached the game page but nothing
  shows they reached its end, so their post and follow-up rows are not built (their
  pre rows are: those came before the randomiser). This is a compliance selection,
  following the authors, not a random one: the 56 averaged 1,046 s on the game page
  against 824 s for the 417, and 38 of them typed nothing, so the game arm's post and
  follow-up rows hold those who entered a valid password while the Tetris arm holds everyone
  assigned to it. Proof against the paper: the
  authors' exclusions applied to these arms give exactly their 425 Tetris and 345
  game players (Results_Tables.xlsx, Demographics; tested on the built rows).
* MOMENTS. Pre (item set .1, before the randomiser: one condition for both arms),
  Post (.2, straight after the game) and Follow-up (.3, the T10 survey). The same
  16 Qualtrics graphics (IM ids) are used at all three (asserted from both .qsf).
  Follow-up rows only for people who finished T0 (the debrief, its last screen, is
  narrated) and have T10 data. The authors' 7-14 day window is not applied: the
  rows say only "a later, short follow-up survey", true for every interval seen
  (1.1 to 175 days).
* WHICH PICTURE. The data column for each screenshot is its Qualtrics export tag
  (FakeExpert1-1 -> FakeExpert1.1_1 ...). Each tag's question shows one graphic;
  that graphic is matched to the deposit's PNG three independent ways: (a) the
  printouts (T0 and T10 "Printout.pdf") print the pictures in block order, and each
  printed picture is pixel-identical (grey-level distance 0-8.5 of 255) to exactly
  one PNG, every other PNG at 20 or more; (b) each question's own <img> size equals
  its PNG's pixel size (Real2's is the same picture scaled to width 211); (c) the
  thesis's Appendix 4 prints the crafted items under the same badges and numbers,
  and its "Real" column in the same order as (a) and (b). This CONTRADICTS the
  deposit's own codebook and Script 2 comment, which call Real1 the Hyderabad
  hoax, Real2 the "Indians in UK" chain, Real3 the Adidas and Real4 the Aldi scam:
  the instrument says Real1 = Indians in UK, Real2 = Hyderabad, Real3 = Aldi,
  Real4 = Adidas. The authors' Natur_* scores average all four, so their results
  are unaffected; per-item rows here follow the instrument.
* BLACK BOXES. The PNGs and the printed survey cover sender names, the group name
  and some words (brands, politicians, places, parties, an ethnic group) with black
  boxes. Both surveys were last modified on 6 May 2024, a minute before their
  printouts, so the deposit alone cannot show the boxes were on screen in 2020. The
  thesis (2022) does: "source information was blacked out to avoid source
  confounds", it quotes an item with "(blanked out)", and its Appendix 4 shows the
  same boxed pictures. So the pictures are what respondents saw; nothing in the text
  describes them.
* CONDITION. Words from the instrument, quoted: the pretest and posttest explainer
  screens; each game page's instruction (Tetris: its first paragraph; its second,
  on not entering a name in the high-score table and what to do if the game froze,
  is operating instructions and left out; game: both paragraphs); the T0 debrief's
  first three paragraphs for follow-up rows (the withdrawal paragraph and contact
  lines left out). Each of those two partial quotes ends with " ..." inside its
  quote marks, saying only that the screen went on. The debrief came LAST in the
  first survey, after the post-test items, so post rows never quote it (an earlier
  draft attributed its description of the game to the researchers on post rows;
  the independent checker failed that: not on screen at that point, and it names
  the four techniques the outcomes are about). Post rows say only what the person
  was given and did; the game arm's game is therefore described only by its own
  page. At follow-up the debrief is narrated as read. Words that are OURS (all
  narration of what the respondent did, true for every row they appear in): "The
  screen read:", "The conversations followed, each with its own questions, and this
  was one of them:", "You were first shown a number of WhatsApp conversations, this
  one among them, and asked about each.", "You were then given this instruction:",
  "You entered the password the game gave you at the end.", "Then the screen read:", "The same conversations
  followed, ...", "You were then shown the same conversations again and asked about
  each.", "At the end of that survey the screen read:", "In a later, short
  follow-up survey the screen read:". The 16 screenshots were shown in a random
  order that the export does not record, so no row says what came before it among
  them. Not narrated: consent screens, the Prolific ID and WhatsApp-use questions,
  the T10 welcome screen.
* ON SCREEN, NOT OURS. Follow-up rows quote the debrief, which says "we randomly
  assigned participants to either the training condition ... or the control
  condition (a Tetris game)". QC rule 17 flags "randomly assigned"; here it was on
  screen, at the end of the first survey, for every person given follow-up rows, so
  it is declared in `condition.on_screen_construction` (QC notes it instead of
  warning). Dropping the sentence would leave Tetris players' rows without what
  they were told about their own game.
* OUTCOMES. 16 screenshots x 3 questions x 3 moments = 144. Wording is each live
  question's own row text (some read "judgment", some "judgement"); scale 1-7 with
  the column labels "Not at all" (1), "Neutral" (4), "Very" (7) from the qsf. Real1
  and Real2 key their third row 4, not 3, and the export names it _3: the row is
  matched by position, and every _3 is the forwarding question.
* NOT BUILT. The open question "what is the first that comes to mind when you hear
  'Join this Group'?" (free text, game arm only); the 11 left-right and
  libertarian-authoritarian agreement items (attitudes asked after the treatment).
* PERSONA. Gender, education, age band and party, asked at the end of T0; WhatsApp
  use in the last 12 months (asked before the pretest); news checking, social media
  use, interest in politics and left-right self-placement (end of T0, habits and
  identity a game is not expected to move). Rewritten labels: "Other, please
  specify:" -> "Other" (three people), "Other party, namely:" -> "Other party";
  "Refuse to say" (party) is a non-answer and left absent; "None" (no party, 147
  people) is an answer and kept as worded, so party goes to the .xlsx as the
  questionnaire's choice codes with their labels in the recipe (the .xlsx reader
  would read the text "None" as an empty cell). Sliders carry their own
  end labels ("4 on a scale from 1 (Very liberal) to 7 (Very conservative)").
  Party, left-right, news and social media habits and political interest were asked
  after the game: mapped as stable traits, a disclosed judgement. Education
  crosswalk scheme uk_yxc92_osf (data/catalog/persona_crosswalk_education.json):
  Jev ordinal_span read each of the five levels as one rung (0.89-1.0); GCSE-level,
  the lowest option offered (there is no "no qualifications" choice), goes to High
  school by its label, as uk_yougov_18 and uk_3krjz_osf map GCSE, a disclosed
  judgement (151 people).
* UK FIT. Twelve lab-made chats in British English (the pub, a last-minute goal,
  "neighbourhood") with a few imported details (an "attorney", a .co.za link), and
  four real messages: an Aldi £150 voucher scam, a free-shoes giveaway scam, a
  partisan chain message with its party and group names boxed, and an Indian
  child-kidnapping hoax with its place names boxed ("Cops", "10:24 PM"). All were
  fielded to and rated by a UK sample; none needs local knowledge to rate.

    uv run python scripts/gen_yxc92.py --prep       # copy the PNGs, write the coded .xlsx
    uv run python scripts/gen_yxc92.py --catalogue  # (re)write this study's images.json entries
    uv run python scripts/gen_yxc92.py              # write the recipe
    uv run python scripts/gen_yxc92.py --check      # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

RAW = REPO / "data" / "raw" / "yxc92"
UK = RAW / "Study 1 – UK"
RAW_CSV = UK / "Datasets and Cleaning Scripts" / "JTG – Study 1 (UK) – Raw Data.csv"
QUALTRICS = UK / "Survey Materials" / "Qualtrics"
T0_QSF = QUALTRICS / "JTG – Study 1 (UK) – T0.qsf"
T10_QSF = QUALTRICS / "JTG – Study 1 (UK) – T10.qsf"
T0_PRINTOUT = QUALTRICS / "JTG – Study 1 (UK) – T0 – Printout.pdf"
T10_PRINTOUT = QUALTRICS / "JTG – Study 1 (UK) – T10 – Printout.pdf"
STIMULI = UK / "Survey Materials" / "Stimuli" / "Manipulative"
IMAGES = RAW / "images"
DATA_FILE = "yxc92_coded.xlsx"
DATA = RAW / DATA_FILE
RECIPE = REPO / "recipes" / "images" / "yxc92.yaml"
LICENCE = (
    "none stated (OSF project yxc92 has no licence). Permission and the group column "
    "asked of the corresponding author 2 Nov 2026; built under rich's standing rule "
    "not to block on a missing licence."
)

# (export tag, deposit PNG) in the questionnaire's block order. Which PNG belongs to
# which tag is PROVEN in `check_pictures`, not taken from these names.
ITEMS = [
    ("FakeExpert1", "Fake_expert_1_climate_change_version_2_with_black_boxes.png"),
    ("FakeExpert2", "Fake_expert_2_smartphones_with_black_boxes.png"),
    ("FakeExpert3", "Fake_expert_3_health_with_black_boxes.png"),
    ("Emotion1", "Emotion_1_beating_with_black_boxes.png"),
    ("Emotion2", "Emotion_2_baby_formula_with_black_boxes.png"),
    ("Emotion3", "Emotion_3_elephant_with_black_boxes.png"),
    ("Polarization1", "Polarization_1_crime_with_black_boxes.png"),
    ("Polarization2", "Polarization_2_lying_version_2_with_black_boxes.png"),
    ("Polarization3", "Polarization_3_iq_version_2_with_black_boxes.png"),
    ("Escalation1", "Escalation_1_grooming_with_black_boxes.png"),
    ("Escalation2", "Escalation_2_terror_attack_with_black_boxes.png"),
    ("Escalation3", "Escalation_3_ethnicity_with_black_boxes.png"),
    ("Real1", "Real_wa_post_3_indians_in_uk_partial_black_boxes.png"),
    ("Real2", "Real_wa_post_2_hyderabad_with_black_boxes.png"),
    ("Real3", "Real_wa_post_8_aldi_supermarket_scam_cropped.png"),
    ("Real4", "Real_wa_post_6_free_adidas_shoes_with_black_boxes.png"),
]
TAGS = [t for t, _ in ITEMS]
# The deposit's codebook pairing, which the instrument contradicts (see notes).
CODEBOOK_REAL = {
    "Real1": "Real_wa_post_2_hyderabad_with_black_boxes.png",
    "Real2": "Real_wa_post_3_indians_in_uk_partial_black_boxes.png",
    "Real3": "Real_wa_post_6_free_adidas_shoes_with_black_boxes.png",
    "Real4": "Real_wa_post_8_aldi_supermarket_scam_cropped.png",
}

# moment index -> (item-set suffix, factor level, qsf, block description)
MOMENTS = [
    (1, "before the game", T0_QSF, "Pretest"),
    (2, "straight after the game", T0_QSF, "Posttest"),
    (3, "follow-up", T10_QSF, "Posttest 2"),
]
GAMES = [("Tetris", "Tetris"), ("JoinThisGroup", "Join This Group")]
MEASURES = 3

# The authors' accepted passwords (JTG_Study1_Script2_Cleaning_Scores.R, step 5).
VALID_PW = {
    "INOC155", "INOC156", "Inoc155", "inoc155", "INC155", "Inoc55", "IN655", "IN0C155",
    "INO155", "INOC155.", "INOV155", "IINOC155", "INOC115", "Inoc655", "INOCI55", "IN0CI55",
}  # fmt: skip

# ---- the instrument, word-for-word from the .qsf (checked in `check_instrument`) --
PRE_EXPLAINER = (
    "You will be shown a number of WhatsApp conversations. On a scale from 1 to 7, please "
    "indicate how reliable you find each of them to be, how confident you are in your "
    "judgment, and how likely you are to share the message with others."
)
POST_EXPLAINER = (
    "You will be shown a number of WhatsApp conversations. On a scale from 1 to 7, please "
    "indicate how reliable you judge each of them to be, how confident you are in your "
    "judgement, and how likely you are to share the message with others."
)
TETRIS = (
    "Your next objective is to play a game. In the frame underneath you can start. The "
    "proceed-button will only appear after a minimum of 9 minutes of attentive play. After "
    "+-12 minutes of active playing, you will automatically move to the next page. While the "
    "goal is to attain as high a level as possible, do not worry about bad performance, what "
    "counts is active playing. Double click on Tetris to start the game. The goal is to form "
    "solid horizontal lines with no gaps. You can use the arrow keys to move the blocks."
)
JTG = (
    "Your next objective is to complete a game. In the frame underneath you can start. The "
    "game takes approximately between 9 and 12 minutes to complete. At the end of the game, "
    "you will receive a secret password. You will have to enter this password in order for "
    "your participation to be approved and to continue to the next page! But please bear in "
    "mind that the password is not the same as your Prolific completion code. You will "
    "receive your completion code after completing the entire survey.\n"
    "In addition, the proceed-button will only appear after a minimum of 9 minutes of "
    "attentive play. It is important that you play this game attentively. If you rush "
    "through it without thinking about it properly, you will not be able to continue to the "
    "next page."
)
# A quote that stops before the screen's text did ends with " ..." inside the quote
# marks: Tetris's high-score paragraph, and the debrief's withdrawal and contact lines,
# followed on screen. Nothing says what they were.
PARTIAL = " ..."
GAME_TEXT = {"Tetris": TETRIS + PARTIAL, "JoinThisGroup": JTG}
DEBRIEF = (
    "Thank you for participating in this study! Below you will find more information about "
    "the study.\n"
    "The aim of this study is to learn more about how people perceive and engage with the "
    "techniques used in the production of misinformation on WhatsApp and other direct "
    "messaging apps. We are particularly interested in the best way to help teach people "
    "how to recognise misinformation on such platforms. In order to do this, we randomly "
    "assigned participants to either the training condition (an educational game about "
    "misinformation on WhatsApp) or the control condition (a Tetris game).\n"
    "The fake news game features four scenarios that are based on our current understanding "
    "of what techniques are common in the spread of misinformation on WhatsApp (the 'fake "
    "expert' technique, using emotional language, polarising messaging, and calling for "
    "(often violent) action). The theory behind the game relies on a principle known as "
    "inoculation: just as medical vaccines trigger antibodies in our immune system by "
    "injecting a severely weakened dose of a virus, the same can be achieved with "
    "information, cultivating “mental antibodies”. By demystifying the techniques that are "
    "used in the production of misinformation, we hope to help people resist and identify "
    "misinformation when they encounter it on direct messaging apps. The game serves as a "
    "simulation to help people familiarise themselves with these tactics, as familiarity is "
    "key to being able to identify unwanted persuasion attempts. Although inspired by real "
    "events, the content of both pre-and post survey questions as well as the game is "
    "entirely fictional and you have not actually spread any fake news."
)
# (qsf, question id, constant) for every quoted passage.
QUOTED = [
    (T0_QSF, "QID252", PRE_EXPLAINER),
    (T0_QSF, "QID253", POST_EXPLAINER),
    (T10_QSF, "QID252", PRE_EXPLAINER),
    (T0_QSF, "QID28", TETRIS),
    (T0_QSF, "QID25", JTG),
    (T0_QSF, "QID85", DEBRIEF),
]
SCALE = {
    "min": 1,
    "max": 7,
    "min_label": "Not at all",
    "max_label": "Very",
    "mid_label": "Neutral",
}

# ---- our words -------------------------------------------------------------------
FOLLOWED = "The conversations followed, each with its own questions, and this was one of them:"
FOLLOWED_AGAIN = (
    "The same conversations followed, each with its own questions, and this was one of them:"
)
FIRST = (
    "You were first shown a number of WhatsApp conversations, this one among them, and "
    "asked about each."
)
PASSWORD = "You entered the password the game gave you at the end."


def pre_text() -> str:
    return f'The screen read: "{PRE_EXPLAINER}" {FOLLOWED} <image>'


def game_lines(game: str) -> str:
    out = f'{FIRST} You were then given this instruction: "{GAME_TEXT[game]}"'
    if game == "JoinThisGroup":
        out += f" {PASSWORD}"
    return out


def post_text(game: str) -> str:
    return f'{game_lines(game)} Then the screen read: "{POST_EXPLAINER}" {FOLLOWED_AGAIN} <image>'


def followup_text(game: str) -> str:
    return (
        f"{game_lines(game)} You were then shown the same conversations again and asked "
        f'about each. At the end of that survey the screen read: "{DEBRIEF}{PARTIAL}" In a later, '
        f'short follow-up survey the screen read: "{PRE_EXPLAINER}" {FOLLOWED_AGAIN} <image>'
    )


# ---- what is printed in each picture, and what it shows (ours) --------------------
HEADER = "[the chat's name and picture and every sender's name are covered by black boxes]"
TEXT_IN_IMAGE = {
    "FakeExpert1": " / ".join([
        HEADER,
        '[cut off at the top: a black box followed by "!"] 10:56',
        "Oi! 10:57",
        "Seriously it was hot outside though, not normal for September 10:57",
        "Yeah incredible, climate change is getting serious isn't it! 10:58",
        "You think it's because of climate change or did we just get lucky? 10:58",
        "I don't know, there's a lot of different opinions! 11:01",
        "Dr. Abhi Singh, MD",
        "Well, I'm a doctor. I can tell you that what I see is that a lot of this 'climate "
        "change' can be explained by natural temperature fluctuations that occur in regular "
        "cycles. 11:03",
        "Hmm interesting! 11:03",
        "Type a message",
    ]),
    "FakeExpert2": " / ".join([
        HEADER,
        '[cut off at the top: "...rub it in guys..."] 12:04',
        "No seriously what happened? 12:05",
        "I don't know! 12:05",
        "Anyway don't worry, I'll just get a new one 12:07",
        "Fair enough 12:07",
        "I'm an attorney. Warning! [black box] smartphones, model [black box] are being "
        "withdrawn due to explosion risk. Two people have already been seriously injured. "
        "12:17",
        "Wow! 12:18",
        "What? 12:18",
        "Omg 12:18",
        "Type a message",
    ]),
    "FakeExpert3": " / ".join([
        HEADER,
        "[a photograph] 12:33",
        "Looks amazing! Recipe? 12:33",
        "Hahahha. My secret! But it's with cumin. 12:34",
        "Nice! 12:34",
        "Dr. Jim Current",
        "A new scientific study shows that some common vitamin supplements can cause "
        "cancer. Be careful, look at the ingredients list! 12:36",
        "Omg seriously? 12:37",
        "Knew it. Go organic! 12:37",
        "Type a message",
    ]),
    "Emotion1": " / ".join([
        HEADER,
        "[cut off at the top] 13:12",
        "Yeah it was crazy, last minute goal for [black box], what a joke. 13:13",
        "Yep, unbelievable. 13:13",
        "Anyone going to the pub tonight? 13:14",
        "Me! What time? 13:15",
        "About 8 ish? 13:15",
        "Guys! Check out this video. An old man was brutally beaten by hoodlums, he's "
        "begging for help at the hospital and they only give him treatment after HOURS of "
        "waiting!!!https://m.youtube.com/watch?v=dQw4w9WgXcQ 13:17",
        "Wow.. 13:19",
        "Type a message",
    ]),
    "Emotion2": " / ".join([
        HEADER,
        "Ok thanks! 13:25",
        "Nah it's Pamplars! Much softer on the skin, not even close. 13:26",
        "Ok either is good! Choose what you like :) 13:28",
        "Yeah I've found it doesn't matter all that much once, babies don't seem to care! "
        "13:29",
        "News alert! [black box] baby formula linked to horrific outbreak of new disease "
        "among infants age 1-2! See https://www.newstime.co.za/story/166374 13:31",
        "Wow no way! [two sad-but-relieved-face emoji] 13:33",
        "Omg really???? 13:33",
        "Type a message",
    ]),
    "Emotion3": " / ".join([
        HEADER,
        "[a photograph] look at this baby!! [heart-eyes emoji] [smiling emoji] 13:44",
        "Wow. Have you guys heard about the new pen size regulation for chickens btw? 13:45",
        "Nah that's not true! 13:46",
        "Isn't it? 13:46",
        "Guys, watch this!! Baby elephant gets horribly hurt after falling off a ledge and "
        "its mother cries for HOURS after!!! [sad-but-relieved-face emoji] "
        "Http://www.dailymotion.com/watch?/xHJu3aaZo3/ 13:47",
        "Type a message",
    ]),
    "Polarization1": " / ".join([
        HEADER,
        "[partly cut off at the top] Second that! Tell your friends and family! We need to "
        "get out the vote! 14:08",
        "Will do! Point of discussion: how do you guys feel about [black box]'s views on "
        "foreign policy? 14:09",
        "Much better than [black box]'s, that's for sure. What a lunatic. 14:11",
        "Yeah.. 14:11",
        "Oh for sure, that's beyond doubt by this point. But the important thing is that we "
        "vote, guys! Let's go! We can win this 14:13",
        'Check this! New interview FAIL. Crime is on the rise like crazy and [black box]\'s '
        'solution is to "listen" to what the criminals want! Insane!! '
        "www.csnnews.com/2019-09-16/ [black box] 14:16",
        "Type a message",
    ]),
    "Polarization2": " / ".join([
        HEADER,
        "[partly cut off at the top] ...I agree. It's going well, guys! I just heard that "
        "more people than ever are excited about voting! Good news [smiling emoji] 14:31",
        "Hahaha totally agreed [black box]! 14:33",
        "Not bad! Maybe politics isn't so bad after all eh? 14:36",
        "Either that or people have had enough of today's politics. 14:37",
        "Probably yeah!!! It's not hard to see [two tears-of-joy emoji] 14:39",
        "Well, about that. I just saw this new study. Turns out right-wingers and "
        "left-wingers don't lie at an equal rate. Guess who lies waaaaay more! 14:41",
        "I knew it [laughing emoji] 14:43",
        "Type a message",
    ]),
    "Polarization3": " / ".join([
        HEADER,
        "[partly cut off at the top] I think monitoring is super important. We all need to "
        "be on the lookout for anything weird or suspicious, and if you see anything in the "
        "area that strikes you as odd let us know here [smiling emoji] 14:51",
        "Let's do this! Thanks [black box] [two fist-bump emoji] 14:54",
        "Sign me up, where do we start! 14:56",
        "In! Love this :) :) 14:56",
        "Sure; I have a lot of work going on atm but I'll be on the lookout! Thanks "
        "[black box]! 14:58",
        'Hey! You all should see this video first! It totally debunks the idea of "equal '
        'IQ" between left-wing and right-wing people! I\'ve always known. '
        "www.vimeo.com/vid/2019/aJk6u886ga 15:00",
        "Type a message",
    ]),
    "Escalation1": " / ".join([
        HEADER,
        "If you say so [black box] You're probably right. 15:10",
        "It is what it is, people. Thanks for being on the lookout! 15:11",
        "[a photograph] 15:12",
        "These two men were found grooming young girls age 15-16 yesterday in [black box] "
        'They haven\'t been arrested because police say "no crime has been committed". We '
        "should act now! Forward if you agree! 15:15",
        "Type a message",
    ]),
    "Escalation2": " / ".join([
        HEADER,
        "[cut off at the top: \"...country is like this....\"] 15:21",
        "I know how you feel.... It's getting more and more difficult.... 15:23",
        "It's scary you're right! Didn't use to be like this I'm sure! [two sad-but-relieved-face "
        "emoji] 15:25",
        "Hello everyone! Thank you all for your comments :) I really like this chat! Thanks "
        "for the invite! 15:27",
        "I think it's soo important that we protect our children! This is an important "
        "group. 15:30",
        "www.csnnews.com/news/17635728 15:31",
        'WARNING! Potential terror attack happening on November 12. Police are barred from '
        'talking about it because of "secrecy". We deserve to be safe! Who\'s with me? 15:33',
        "Type a message",
    ]),
    "Escalation3": " / ".join([
        HEADER,
        "[cut off at the top: \"...happen.\"] 15:51",
        "Yea thanks, it's one of those days you know? Don't worry about it. 15:55",
        "There's a lot of tension in my neighbourhood! I can feel it. 15:56",
        "Yes me too.. 15:57",
        "[black box] have you seen the reports? Lots of unrest going on in [black box]. "
        "Police are advising to stay inside. Ethnic [black box] are the main target. Check "
        "out this video it's clear as day: www.youtube.com/watch?/ak736kshi 15:58",
        "Wow really? Thanks [black box]! Gee... 15:59",
        "Stay inside? Why not get out and find these gangsters ourselves!!!! 16:00",
        "Type a message",
    ]),
    "Real1": " / ".join([
        HEADER,
        "[cut off at the top] 11:01",
        "Pass this message on to every TRUE [black box] 11:01",
        "No self respecting [black box] should vote for the [black box] party. FULL STOP. "
        "11:02",
        "The [black box] party is now the mouthpiece of the [black box] government. 11:02",
        "[three angry-face emoji] 11:10",
        "Sent it! 11:10",
        "Thanks [black box]! 11:10",
        "There are now no excuses left for any [black box] to still be with the [black box] "
        "party. 11:11",
        "Thank you for forwarding! 11:12",
        "Sure [black box]! 11:12",
        "Type a message",
    ]),
    "Real2": " / ".join([
        "Guys please be on high alert 10:24 PM",
        "Three kids were kidnapped from my friend's area this morning.. There were 10 guys "
        "giving biscuits and people from that area have caught all 10 n 5 more based on "
        "their info... 10:24 PM",
        "Cops arrived at scene and informed that 400 people have landed in [black box] (or "
        "[black box] or [black box] or [black box] or [black box] or any other place) for "
        "child trafficking. Check my next video and repost. Parents pls be on high alert. "
        "10:25 PM",
    ]),
    "Real3": (
        "ALDI is giving away £150 Free Voucher to celebrate 27th anniversary, go here to get "
        "yours : http://www.alḍi.com/celebration . 08:42"
    ),
    "Real4": " / ".join([
        "[black box]",
        "[trainer emoji] [black box] is celebrating its 68th anniversary by giving free pair "
        "of shoes to 250 customers [trainer emoji]",
        "Grab Yours Now",
        "http://getyourshoes.co/[black box] 6:40 PM",
    ]),
}  # fmt: skip
CHAT = (
    "A phone screenshot of a WhatsApp group chat, partway through a conversation, with the "
    "green header bar at the top and the message box at the bottom. The chat's name and "
    "picture and the senders' names are covered by black boxes."
)
DESCRIPTION = {
    "FakeExpert1": CHAT + " One sender's name is shown in red.",
    "FakeExpert2": CHAT,
    "FakeExpert3": CHAT + " At the top is a photograph of a stew of meat and vegetables "
    "in a blue casserole dish; one sender's name is shown in red.",
    "Emotion1": CHAT,
    "Emotion2": CHAT,
    "Emotion3": CHAT + " At the top is a photograph of a piglet standing in grass.",
    "Polarization1": CHAT,
    "Polarization2": CHAT,
    "Polarization3": CHAT,
    "Escalation1": CHAT + " In the middle is a blurred photograph of two men seen from "
    "behind, in yellow light.",
    "Escalation2": CHAT,
    "Escalation3": CHAT,
    "Real1": CHAT,
    "Real2": "A screenshot of three WhatsApp messages on a plain beige background, with no "
    "header bar, no sender names and no message box.",
    "Real3": "A cropped screenshot of a single WhatsApp message on a patterned background.",
    "Real4": "A cropped screenshot of a single WhatsApp message whose sender's name is "
    "covered by a black box.",
}


def image_id(tag: str) -> str:
    return f"yxc92_{tag.lower()}"


def image_file(tag: str) -> str:
    return f"raw/yxc92/images/{tag}.png"


# ---------------------------------------------------------------------------
# The instrument
# ---------------------------------------------------------------------------


def _qsf(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text())
    return data


def _questions(path: Path) -> dict[str, dict[str, Any]]:
    return {
        e["PrimaryAttribute"]: e["Payload"]
        for e in _qsf(path)["SurveyElements"]
        if e["Element"] == "SQ"
    }


def _blocks(path: Path) -> dict[str, list[str]]:
    """Block description -> its question ids, in order."""
    out: dict[str, list[str]] = {}
    for e in _qsf(path)["SurveyElements"]:
        if e["Element"] != "BL":
            continue
        payload = e["Payload"]
        for b in payload.values() if isinstance(payload, dict) else payload:
            out[b.get("Description") or ""] = [
                x["QuestionID"] for x in b.get("BlockElements", []) if x.get("QuestionID")
            ]
    return out


def plain(markup: str) -> str:
    """Screen text: tags dropped (no space, so "<b>T</b>he" reads "The"), entities
    resolved, whitespace collapsed."""
    text = re.sub(r"<[^>]+>", "", markup.replace("<br", " <br").replace("</div>", " </div>"))
    text = html.unescape(text).replace("\xa0", " ")
    return " ".join(text.split())


def check_instrument() -> None:
    """Every quoted passage is in its question, word-for-word (whitespace aside)."""
    for qsf, qid, quote in QUOTED:
        screen = plain(_questions(qsf)[qid]["QuestionText"])
        if " ".join(quote.split()) not in screen:
            raise SystemExit(f"{qsf.name} {qid}: quoted passage not on screen: {quote[:60]}")


def check_flow() -> None:
    """The randomiser: one branch sets Tetris = 1 then shows the Tetris block, the other
    shows the game block; nothing else sets `Tetris`."""
    q = _qsf(T0_QSF)
    flow = next(e for e in q["SurveyElements"] if e["Element"] == "FL")["Payload"]["Flow"]
    rnd = [f for f in flow if f.get("Type") == "BlockRandomizer"]
    if len(rnd) != 1 or rnd[0]["SubSet"] != 1 or not rnd[0]["EvenPresentation"]:
        raise SystemExit("expected one even BlockRandomizer choosing one branch")
    names = {_block_id(q, desc): desc for desc in _blocks(T0_QSF)}
    branches = rnd[0]["Flow"]
    group, game = branches
    ed, tetris_block = group["Flow"]
    field = ed["EmbeddedData"][0]
    if (field["Field"], field["Value"]) != ("Tetris", "1"):
        raise SystemExit(f"unexpected embedded data {field}")
    if names[tetris_block["ID"]] != "Control - Tetris":
        raise SystemExit("the Tetris=1 branch does not show the Tetris block")
    if names[game["ID"]] != "Inoculation - WhatsApp game":
        raise SystemExit("the other branch is not the game block")
    if json.dumps(q).count('"Field": "Tetris"') + json.dumps(q).count('"Field":"Tetris"') != 1:
        raise SystemExit("`Tetris` is set somewhere else too")
    order = [names.get(f.get("ID", ""), f.get("Type")) for f in flow]
    want = ["Pretest-explainer", "Pretest", "BlockRandomizer", "Posttest-explainer", "Posttest"]
    if [o for o in order if o in want] != want:
        raise SystemExit(f"flow order changed: {order}")


def _block_id(q: dict[str, Any], desc: str) -> str:
    for e in q["SurveyElements"]:
        if e["Element"] != "BL":
            continue
        payload = e["Payload"]
        for b in payload.values() if isinstance(payload, dict) else payload:
            if (b.get("Description") or "") == desc:
                return str(b["ID"])
    raise KeyError(desc)


def live_items() -> dict[tuple[int, str], dict[str, Any]]:
    """(moment, tag) -> the live question: graphic id, display size, row wordings."""
    out: dict[tuple[int, str], dict[str, Any]] = {}
    for moment, _, qsf, block in MOMENTS:
        qs = _questions(qsf)
        qids = _blocks(qsf)[block]
        if len(qids) != len(ITEMS):
            raise SystemExit(f"{qsf.name} {block}: {len(qids)} questions, expected 16")
        for qid, tag in zip(qids, TAGS, strict=True):
            p = qs[qid]
            if p["DataExportTag"] != f"{tag}-{moment}":
                raise SystemExit(f"{qid} is {p['DataExportTag']}, expected {tag}-{moment}")
            ims = re.findall(r"IM=(IM_\w+)", p["QuestionText"])
            size = re.findall(r"width:\s*(\d+)px;\s*height:\s*(\d+)px", p["QuestionText"])
            rows = [plain(p["Choices"][str(c)]["Display"]) for c in p["ChoiceOrder"]]
            answers = [p["Answers"][str(a)]["Display"] for a in p["AnswerOrder"]]
            labels = [c["Display"] for c in p["ColumnLabels"]]
            if len(ims) != 1 or len(size) != 1 or len(rows) != MEASURES:
                raise SystemExit(f"{qid}: unexpected question shape")
            if answers != [str(i) for i in range(1, 8)]:
                raise SystemExit(f"{qid}: answers shown are {answers}")
            if labels != ["Not at all", "Neutral", "Very"]:
                raise SystemExit(f"{qid}: column labels {labels}")
            if not (
                rows[0].startswith("How reliable")
                and rows[1].startswith("How confident")
                and rows[2].startswith("How likely are you to forward")
            ):
                raise SystemExit(f"{qid}: rows {rows}")
            out[(moment, tag)] = {
                "im": ims[0],
                "size": (int(size[0][0]), int(size[0][1])),
                "rows": rows,
            }
    for tag in TAGS:
        if len({out[(m, tag)]["im"] for m, *_ in MOMENTS}) != 1:
            raise SystemExit(f"{tag}: different graphics at different moments")
    return out


# ---------------------------------------------------------------------------
# The pictures
# ---------------------------------------------------------------------------


def _png_size(path: Path) -> tuple[int, int]:
    head = path.read_bytes()[:24]
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"{path.name} is not a PNG")
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


def _grey(path: Path) -> np.ndarray:
    """The picture reduced to 48x96 grey by macOS sips (as gen_yjvpn's _grey64)."""
    with tempfile.TemporaryDirectory() as tmp:
        bmp = Path(tmp) / "p.bmp"
        subprocess.run(
            ["sips", "-z", "96", "48", "-s", "format", "bmp", str(path), "--out", str(bmp)],
            check=True,
            capture_output=True,
        )
        b = bmp.read_bytes()
    offset = int.from_bytes(b[10:14], "little")
    width = int.from_bytes(b[18:22], "little", signed=True)
    height = abs(int.from_bytes(b[22:26], "little", signed=True))
    n = int.from_bytes(b[28:30], "little") // 8
    stride = (width * n + 3) // 4 * 4
    px = np.frombuffer(b[offset : offset + stride * height], dtype=np.uint8)
    px = px.reshape(height, stride)[:, : width * n].reshape(height, width, n)
    grey: np.ndarray = px[:, :, :3].astype(float).mean(axis=2)
    return grey


def printout_distances() -> list[dict[str, float]]:
    """For every rating picture in both printouts, in print order: {PNG: distance}."""
    if not shutil.which("pdfimages") or not shutil.which("sips"):
        raise SystemExit("pdfimages (poppler) and sips (macOS) are needed for this check")
    ours = {f: _grey(STIMULI / f) for _, f in ITEMS}
    out = []
    with tempfile.TemporaryDirectory() as tmp:
        for pdf, tag in ((T0_PRINTOUT, "t0"), (T10_PRINTOUT, "t10")):
            subprocess.run(
                ["pdfimages", "-png", str(pdf), f"{tmp}/{tag}"], check=True, capture_output=True
            )
        for tag, want in (("t0", 2 * len(ITEMS)), ("t10", len(ITEMS))):
            pics = sorted(Path(tmp).glob(f"{tag}-*.png"))
            if len(pics) != want:
                raise SystemExit(f"{tag} printout holds {len(pics)} pictures, expected {want}")
            for p in pics:
                g = _grey(p)
                out.append({f: float(np.abs(g - a).mean()) for f, a in ours.items()})
    return out


def check_pictures() -> None:
    """Each tag's picture is its PNG: by print order, by pixels, and by display size."""
    dists = printout_distances()
    order = TAGS * 3  # T0 pretest, T0 posttest, T10: each block in tag order
    files = dict(ITEMS)
    for tag, dist in zip(order, dists, strict=True):
        mine = dist[files[tag]]
        others = [v for f, v in dist.items() if f != files[tag]]
        if mine > 10.0 or min(others) < 20.0:
            raise SystemExit(f"{tag}: printout picture distances {dist}")
    live = live_items()
    for tag, f in ITEMS:
        w, h = _png_size(STIMULI / f)
        dw, dh = live[(1, tag)]["size"]
        if abs(w / h - dw / dh) > 0.015 * (w / h):
            raise SystemExit(f"{tag}: shown at {dw}x{dh}, {f} is {w}x{h}")


def extract() -> None:
    """--prep, part 1: copy each PNG under its tag's name, byte for byte."""
    IMAGES.mkdir(exist_ok=True)
    for tag, f in ITEMS:
        (IMAGES / f"{tag}.png").write_bytes((STIMULI / f).read_bytes())


def catalogue_entries() -> dict[str, dict[str, str]]:
    from micromotives_datasets.images import sha256_of

    live = live_items()
    out: dict[str, dict[str, str]] = {}
    for tag, f in ITEMS:
        path = REPO / "data" / image_file(tag)
        if path.read_bytes() != (STIMULI / f).read_bytes():
            raise SystemExit(f"{path.name} is not {f}")
        im = live[(1, tag)]["im"]
        out[image_id(tag)] = {
            "file": image_file(tag),
            "sha256": sha256_of(path),
            "source": (
                f"OSF yxc92, Study 1 - UK/Survey Materials/Stimuli/Manipulative/{f}, copied "
                f"byte for byte. The fielded surveys (T0.qsf, T10.qsf) show Qualtrics graphic "
                f"{im} in the questions exported as {tag}-1, {tag}-2 and {tag}-3; the T0 and "
                "T10 printouts print that graphic pixel-identical to this file, and the "
                "question displays it at this file's proportions. The black boxes were on "
                "screen: Basol's thesis (Cambridge 2022, ch. 3) says source information was "
                "blacked out and shows the same pictures in its Appendix 4."
                + (
                    f" The deposit's codebook pairs {tag} with {CODEBOOK_REAL[tag]}; the "
                    "instrument does not."
                    if tag in CODEBOOK_REAL
                    else ""
                )
            ),
            "licence": "none stated (OSF project yxc92)",
            "text_in_image": TEXT_IN_IMAGE[tag],
            "description": DESCRIPTION[tag],
        }
    return out


def write_catalogue() -> None:
    """Add or refresh only this study's entries; re-read first, others are editing too."""
    check_pictures()
    entries = catalogue_entries()
    path = REPO / "data" / "catalog" / "images.json"
    current = json.loads(path.read_text())
    current.update(entries)
    path.write_text(json.dumps(current, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# The coded spreadsheet
# ---------------------------------------------------------------------------

PERSONA_MAP = {
    "gender": "Gender",
    "education": "Education",
    "age_band": "Age",
    "party_id": "PolParty",
    "ideology": "Left.right.simple_5",
    "whatsapp_use_in_the_last_12_months": "WAUse_1",
    "how_often_checks_the_news": "News.checking_1",
    "how_often_uses_social_media": "News.checking_2",
    "interest_in_politics": "Pol_interest_1",
}
SLIDER_LABELS = {
    "WAUse_1": ["Never", "Rarely", "About once a week", "Once a day", "More than once a day"],
    "News.checking_1": ["Never", "Rarely", "Sometimes", "Frequently", "All the time"],
    "News.checking_2": ["Never", "Rarely", "Sometimes", "Frequently", "All the time"],
}
SLIDER_ENDS = {
    "Pol_interest_1": (5, "Not at all interested", "Very interested"),
    "Left.right.simple_5": (7, "Very liberal", "Very conservative"),
}
# Labels rewritten to drop a scripting instruction; and one non-answer.
REWRITE = {"Gender": {"Other, please specify:": "Other"}, "PolParty": {
    "Other party, namely:": "Other party"}}  # fmt: skip
NON_ANSWER = {"PolParty": ["Refuse to say"]}
# Party is written to the .xlsx as the questionnaire's own choice codes, not text:
# 147 people answered "None", and the spreadsheet reader (pandas defaults) reads the
# string "None" as an empty cell, which silently made them party-less non-answers.
CODED = "PolParty"
# What pandas reads as missing by default; no text answer written to the .xlsx may
# be one of these (asserted in `prep`).
PANDAS_NA = {"", "#N/A", "#N/A N/A", "#NA", "-1.#IND", "-1.#QNAN", "-NaN", "-nan", "1.#IND",
    "1.#QNAN", "<NA>", "N/A", "NA", "NULL", "NaN", "None", "n/a", "nan", "null"}  # fmt: skip


def party_codes() -> dict[str, int]:
    """Party label (after REWRITE) -> its choice code in T0.qsf (QID251)."""
    p = _questions(T0_QSF)["QID251"]
    if p["DataExportTag"] != "PolParty":
        raise SystemExit("QID251 is not PolParty")
    out = {}
    for c in p["ChoiceOrder"]:
        label = plain(p["Choices"][str(c)]["Display"])
        out[REWRITE[CODED].get(label, label)] = int(c)
    return out


def rating_var(moment: int, tag: str, measure: int) -> str:
    return f"{tag}.{moment}_{measure + 1}"


def stim_column(moment: int, tag: str) -> str:
    return f"stim_{moment}_{tag}"


def condition_num(moment: int, game: int | None, t: int) -> int:
    if moment == 1:
        return t
    assert game is not None
    return len(ITEMS) * (1 + 2 * (moment - 2) + game) + t


def arms_of(raw: pd.DataFrame) -> pd.Series:
    """0 Tetris, 1 game (password typed), None otherwise. The randomiser's own record."""
    t0 = raw["StartDate.T0"].notna()
    tetris = raw["Tetris"] == "1"
    game_page = raw["Timing.Active_Page.Submit"].notna()
    tetris_page = raw["Timing.Tetris_Page.Submit"].notna()
    if (tetris & game_page).any() or (~tetris & tetris_page).any():
        raise SystemExit("a person has the other branch's page timing")
    if int((tetris & ~tetris_page).sum()) != 1:
        raise SystemExit("expected exactly one Tetris person without Tetris page timing")
    if int(tetris.sum()) != 505 or int((t0 & ~tetris & game_page).sum()) != 473:
        raise SystemExit("randomiser counts changed (505 Tetris, 473 game)")
    arm = pd.Series([None] * len(raw), index=raw.index, dtype=object)
    arm[t0 & tetris] = 0
    arm[t0 & ~tetris & game_page & raw["JoinThisGroup"].isin(VALID_PW)] = 1
    return arm


def read_raw() -> pd.DataFrame:
    raw = pd.read_csv(RAW_CSV, dtype=str, keep_default_na=False, na_values=["NA", ""])
    raw.insert(0, "pid", range(1, len(raw) + 1))
    return raw


def prep() -> pd.DataFrame:
    raw = read_raw()
    arm = arms_of(raw)
    raw = raw[raw["StartDate.T0"].notna()].copy()
    arm = arm[raw.index]
    finished_t0 = raw["Finished.T0"] == "True"
    has_t10 = raw["StartDate.T10"].notna()
    if (pd.to_datetime(raw["StartDate.T10"]) <= pd.to_datetime(raw["EndDate.T0"])).any():
        raise SystemExit("a follow-up started before its first part ended")
    ratings = [rating_var(m, t, k) for m, *_ in MOMENTS for t in TAGS for k in range(MEASURES)]
    out = raw[["pid", *PERSONA_MAP.values(), *ratings]].copy()
    for col in ratings + [v for v in PERSONA_MAP.values() if v.endswith(("_1", "_2", "_5"))]:
        out[col] = pd.to_numeric(out[col])
    for c in ratings:
        bad = set(out[c].dropna()) - set(range(1, 8))
        if bad:
            raise SystemExit(f"{c}: values {bad}")
    for col, rewrite in REWRITE.items():
        out[col] = out[col].replace(rewrite)
    codes = party_codes()
    unknown = set(out[CODED].dropna()) - set(codes)
    if unknown:
        raise SystemExit(f"{CODED}: labels not in the questionnaire {unknown}")
    out[CODED] = out[CODED].map(codes, na_action="ignore").astype("float64")
    for col in out.columns:
        if out[col].dtype == object and set(out[col].dropna()) & PANDAS_NA:
            raise SystemExit(f"{col}: a text answer the .xlsx reader would read as missing")
    stim: dict[str, list[float | None]] = {}
    for t, tag in enumerate(TAGS):
        stim[stim_column(1, tag)] = [float(condition_num(1, None, t))] * len(out)
        stim[stim_column(2, tag)] = [
            float(condition_num(2, int(a), t)) if a is not None else None for a in arm
        ]
        stim[stim_column(3, tag)] = [
            float(condition_num(3, int(a), t)) if a is not None and f and h else None
            for a, f, h in zip(arm, finished_t0, has_t10, strict=True)
        ]
    stims = pd.DataFrame(stim, index=out.index, dtype="float64")
    return pd.concat([out, stims], axis=1).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Recipe
# ---------------------------------------------------------------------------


def all_arms() -> list[dict[str, Any]]:
    arms = []
    for t, tag in enumerate(TAGS):
        cn = condition_num(1, None, t)
        arms.append(
            {
                "raw": cn,
                "condition_num": cn,
                "factors": {"moment": MOMENTS[0][1], "game": "not yet played", "message": tag},
                "text": pre_text(),
                "images": [image_id(tag)],
            }
        )
    for moment, level, *_ in MOMENTS[1:]:
        for g, (game, game_level) in enumerate(GAMES):
            for t, tag in enumerate(TAGS):
                cn = condition_num(moment, g, t)
                arms.append(
                    {
                        "raw": cn,
                        "condition_num": cn,
                        "factors": {"moment": level, "game": game_level, "message": tag},
                        "text": post_text(game) if moment == 2 else followup_text(game),
                        "images": [image_id(tag)],
                    }
                )
    return arms


def recipe() -> dict[str, Any]:
    check_instrument()
    check_flow()
    live = live_items()
    ds = read_any(DATA)

    outcomes = []
    for moment, *_ in MOMENTS:
        for tag in TAGS:
            rows = live[(moment, tag)]["rows"]
            for k in range(MEASURES):
                outcomes.append(
                    {
                        "var": rating_var(moment, tag, k),
                        "task_num": len(outcomes),
                        "question": rows[k],
                        "scale": dict(SCALE),
                        "condition_var": stim_column(moment, tag),
                    }
                )

    rewrite: dict[str, dict[int, str]] = {}
    for col, names in SLIDER_LABELS.items():
        rewrite[col] = dict(enumerate(names, start=1))
    for col, (top, lo, hi) in SLIDER_ENDS.items():
        rewrite[col] = {
            k: f"{k} on a scale from 1 ({lo}) to {top} ({hi})" for k in range(1, top + 1)
        }
    codes = party_codes()
    rewrite[CODED] = {c: label for label, c in codes.items()}
    missing = {CODED: [codes[t] for t in NON_ANSWER[CODED]]}
    if set(NON_ANSWER) != {CODED} or set(ds.df[CODED].dropna()) - set(codes.values()):
        raise SystemExit("party codes and the coded data disagree")

    return {
        "study_id": "yxc92",
        "source": "osf",
        "title": "Join This Group: WhatsApp misinformation game vs Tetris; reliability, "
        "confidence and forwarding of 16 WhatsApp screenshots before, after and at follow-up",
        "data_file": DATA_FILE,
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": "pid",
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_var": stim_column(1, TAGS[0]),
            "factors": ["moment", "game", "message"],
            "on_screen_construction": {
                "randomly assigned": "word-for-word from the T0 debrief (QID85), the last "
                "screen of the first survey, which every person given follow-up rows reached "
                "(Finished.T0); only follow-up rows quote it",
            },
            "arms": all_arms(),
        },
        "outcomes": outcomes,
        "response_recode": {i: i for i in range(1, 8)},
        "persona_map": PERSONA_MAP,
        "persona_missing": missing,
        "persona_label_rewrite": rewrite,
    }


def render() -> str:
    return yaml.safe_dump(recipe(), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--prep", action="store_true", help="copy the PNGs, write the coded .xlsx")
    ap.add_argument("--catalogue", action="store_true", help="add this study's images.json entries")
    args = ap.parse_args()
    if args.prep:
        check_flow()
        extract()
        prep().to_excel(DATA, index=False)
        print(f"wrote {IMAGES.relative_to(REPO)}/ and {DATA.relative_to(REPO)}")
        return 0
    if args.catalogue:
        write_catalogue()
        print("updated data/catalog/images.json (yxc92 entries only)")
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
