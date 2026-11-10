#!/usr/bin/env python3
"""Write recipes/images/4hjcf.yaml: social corrections under false and true news posts (IMG57).

Stoeckel, Stöckli, Ceka, Ricchi, Lyons and Reifler, "Social corrections act as a
double-edged sword by reducing the perceived accuracy of false and real news in the UK,
Germany, and Italy", Communications Psychology 2 (2024) 10, doi:10.1038/s44271-024-00057-w,
the UK experiment ("Experiment 1"). OSF 4hjcf, "Social correction - an online experiment
in the UK": the Qualtrics export (analyses/data.csv, semicolon-separated, cp1252), the
authors' six rendered R Markdown analyses (analyses/*.html), the pre-registration and its
update (methods/pre-reg.pdf, "pre-reg update .pdf") and the stimuli
(methods/posts/stimuli_osf.zip: 13 folders, four PNGs each). Pre-registered as OSF fpm2e
(12 July 2022). Dynata UK online panel, fielded 11-26 July 2022. No questionnaire is
deposited (the pre-registration's "uploaded questionnaire" is not on OSF either; the
registration holds no files).

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* DESIGN. Within person. Each respondent saw nine posts: true post 1, three false posts
  (Qualtrics flow randomiser FL_7, 3 of 10), true post 2, three false posts (FL_51, 3 of
  10), true post 3 (the paper's "Social media post assessment task"). Each post block
  showed ONE of four PNGs, chosen by an in-block randomiser whose display-order columns
  are `<post>_DO_<post>_control / _sc / _sca / _scp`: exactly one of the four is set for
  every respondent who reached the post (checked: never two, and never an answer
  without one). After the picture, three questions in a fixed order (their DO columns
  are the constants 2, 3, 4): accuracy, like, share.
* WHICH ARM IS WHICH PICTURE (proven, not guessed). The data's arm suffixes are decoded
  by the authors' own code, printed in analysis_truenews_osf.html and parsed here:
  `grepl("scp") ~ 3`, `grepl("sca") ~ 2`, `grepl("sc") ~ 1`, `grepl("control") ~ 0`,
  then revalued 0 "control", 1 "low ampl", 2 "high ampl", 3 "ampl+link". The stimulus
  files are named the same way in every folder: control.png, "low amp(lification)",
  "high amp(lification)" and "high amp(lification) + debunk(ing)" / "+ link". So sc = the
  low-amplification file, sca = high, scp = high + link. Independent witness: the
  per-arm effects in this deposit reproduce the paper's Table 1 under that decoding and
  under no other of the six permutations (`effects()`, crosscheck below).
* WHICH POST IS WHICH FOLDER (proven). The data's `post_k` (k = 1, 2, 3, 5, 6, 8, 10,
  11, 12, 13) and `realpost_k` (k = 1-3) are the folders "Stimulus FALSE NEWS k" and
  "Stimulus TRUE NEWS k": the same ten numbers, gaps included. Two witnesses: the
  authors' congeniality code ties each false post to the opinion it is congenial to
  (1 NHS; 2, 3, 8, 10 vaccines; 5 Brexit; 6, 11 climate; 12, 13 Russia), parsed here
  and asserted against each folder's topic; and their true-news labels (1 "effective
  covid booster", 2 "monkeypox cases rise", 3 "covid jab and blood clot") match the
  three true folders' pictures. The paper's Supplementary Table 36 lists the UK false
  headlines in the same order (1 Track & Trace ... 13 MFA Russia).
* THE TREATMENT IS IN THE PICTURE. Each of the 52 PNGs is a complete mock Facebook or
  Twitter screenshot (made with zeoob.com, names and faces generated, per the paper):
  the post, and in the treatment arms a corrective comment (a "miscorrection" under a
  true post) above a second, supporting comment, with like counts, and in the link arm
  a link card under the correction. Nothing was overlaid by the survey. So each arm is
  its picture; its words are transcribed in the catalogue (`text_in_image`) and quoted
  in the condition. Low and high amplification differ in the correction's like count,
  but not ONLY there: in several posts the supporting comment's count, a comment's age
  or one word also differs between files (post 1: 5 vs 6 likes; post 5: 10 vs 1 likes
  and 7h vs 4h; post 8: "Seema" vs "Seems"). The transcription records each file as it
  is; nothing is harmonised.
* WORDS IN THE PICTURES (text_in_image). Every word the platform or a person wrote:
  names, handles, the post's own text and the words of its graphic, time stamps, the
  reaction, comment, share, retweet and like counts (the like counts ARE the
  manipulation, so unlike be8a2 they are transcribed), comments, Facebook's
  "Like"/"Comment"/"Share"/"Like · Reply · 7h"/"View more N Comments"/"Write a
  comment...", and on a link card its source name and headline (and description line
  where it has one). " / " separates blocks; line wraps inside a block are joined with a
  space; curly quotes and apostrophes are straightened, "…" is written "...", and the
  middle dot is spaced " · " (typography, CONVENTIONS). Every word legible at the
  file's own resolution is transcribed (ledger 153), including words inside a
  photograph (the phone's "NHS Test and Trace", the vial's "Moderna COVID-19 Vaccine",
  the ship's "TOKATU NELSON", the generators' "YADX166" and "aggreko", the lectern's
  "Pfizer", the vials' "COVID-19 VACCINE"), a link card's kicker, byline and date, and
  a video's logo and caption. Two dates were read from blurred type and confirmed
  outside the picture: false 5's "10 NOVEMBER 2021" is the publication date of the
  Full Fact article the card shows (fullfact.org/online/Brexit-EU-fishing-fuel-
  subsidies, dated 10 Nov 2021 by the CIMPLE claim-review index); false 2's "21
  OCTOBER 2021" is read from the file alone. Left out, because they cannot be read or
  are too many to transcribe faithfully, and listed per picture in `UNQUOTED`: the
  small print on vial labels, false 6's cut-off orange letters, false 8's link-card
  date line (about 6 pixels high; a checker read "NOVEMBER 16, 2021 / 8:20 PM /
  UPDATED 9 MONTHS AGO", which this maker could not confirm digit by digit, so it is
  not quoted), post 12's map, post 13's photographed documents, and two tiny marks in
  link-card photographs. Icons and emoji are not words. Typos are the source's
  ("Twitter for Adroid", "@robertashcraft", "14:17 PM", "Seema Yeadon", "shi££").
* CONDITION. The task instructions are not in the deposit (the paper says only that
  respondents were "asked to imagine that these posts came up in their feed"), so
  nothing of them is quoted. Words that are OURS: 'You are shown a social media post:
  "..." <image>', and for a picture holding words not quoted (`UNQUOTED`) 'You are
  shown a social media post (not every word in it is quoted here): "..." <image>'. The
  clause says only that the quotation is partial; it never says what the missing words
  are (a condition does not describe a picture, ledger 158); the catalogue's
  `description` names them. No shared context.
* OUTCOMES. 13 posts x 3 questions = 39 outcomes, each with its post's own assignment
  column (`Outcome.condition_var`, the within-subject design). Wording from the
  pre-registration's table of dependent variables, the only deposited source; the paper
  prints the same words. Accuracy "To the best of your knowledge, how accurate is the
  claim in the above headline?" 1-4 (pre-registration: "not at all accurate/not very
  accurate/somewhat accurate/very accurate"); like and share 1-5, "1 = not at all
  likely, 5 = very likely". Direction: false posts' accuracy is lower than true posts'
  and every correction arm lowers it, as the paper reports (1 = not at all accurate).
* WHO, AND WHAT IS LEFT OUT. Every respondent who reached a post; non-finishers' answers
  to the posts they did see are kept (the melt drops a blank answer). 9 people took the
  survey twice under one panel id (`psid`); each attempt is its own response
  (`ResponseId`, the participant id) and is kept, as the authors did. EXCLUDED: any
  false post that BOTH flow randomisers drew for a person. FL_7 and FL_51 drew three
  posts each, independently, so the draws overlap for 1,429 of the 2,011 who finished
  (1,030 by one post, 383 by two, 16 by three); the data hold one answer and one arm for
  such a post. Over everyone, 1,888 person-post pairs, 1,464 people, 5,660 answers. Qualtrics shows a block reached a second time again, with the earlier
  answers pre-filled and editable, and keeps only the last answers (Qualtrics support,
  "Question Blocks" in Survey Flow). So the recorded answer may have been given on a
  second viewing, and whether the second showing drew the same arm is not recorded:
  the row's condition cannot be verified (ledger 143, 150). Counted in
  `double_drawn()`; the authors analysed these pairs as single exposures.
* PERSONA. Only what the source labels: `age_scr` (6 bands), `gender_scr`, `edu_scr`
  (3 groups), all asked before the posts. No value labels are deposited; the codes are
  read from the paper's Supplementary Table 11 (demographics of the UK experiment),
  whose counts reproduce the codes' order (age 235, 285, 344, 355, 310, 415 for codes
  1-6; education 771, 530, 643 for 1-3) and from the authors' code (`gender_scr == 1 ~
  "female"`, `== 2 ~ "male"`). Code 4 is the only other gender code; Table 11's third
  row is "Non-binary / third gender / other". Education's groups are Table 11's note,
  word-for-word. NOT mapped: `region_scr` (12 codes, no labels anywhere), `party`
  (11 codes; the authors' recode names only code 1 and its other branches are
  mis-keyed on `post`), `leftright` (0-10, endpoints unknown), and the attitude
  batteries (opinion_*, antiexpert_*, ssi_*, crt_*, russia_feeling_1, ukraine_war),
  whose code directions are not documented.
* UK FIT, per post. Fielded in the UK on a UK sample, most posts are UK stories (NHS
  Test and Trace, Brexit fishing fuel, COP26 in Glasgow, UK monkeypox, a UK inquest).
  Two are not: false post 2 is a US story (a Delta pilot) whose supporting comment
  names Biden, and false post 10 is set in a New York hospital; false posts 12 and 13
  are Russia-Ukraine war disinformation. Flagged for the lead, not removed: they were
  what UK respondents saw.
* LICENCE. None stated on OSF 4hjcf. The authors have been emailed; built under
  rich's standing ruling that an unstated licence does not block a build.

    uv run python -I scripts/gen_4hjcf.py --prep       # images + derived wide CSV
    uv run python -I scripts/gen_4hjcf.py --catalogue  # (re)write this study's images.json entries
    uv run python -I scripts/gen_4hjcf.py              # write the recipe
    uv run python -I scripts/gen_4hjcf.py --check      # exit 1 if recipe or wide CSV differ
"""

from __future__ import annotations

import argparse
import html
import io
import itertools
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

STUDY = "4hjcf"
RAW = REPO / "data" / "raw" / STUDY
DEPOSIT_CSV = RAW / "analyses" / "data.csv"
ZIP = RAW / "methods" / "posts" / "stimuli_osf.zip"
TRUE_HTML = RAW / "analyses" / "analysis_truenews_osf.html"
PREREG = RAW / "methods" / "pre-reg.pdf"
IMAGES = RAW / "images"
WIDE_NAME = "4hjcf_wide.csv"
WIDE = RAW / WIDE_NAME
RECIPE = REPO / "recipes" / "images" / f"{STUDY}.yaml"
LICENCE = (
    "None stated: OSF 4hjcf gives no reuse terms. The authors were emailed for "
    "permission; built under rich's ruling of 9 Nov 2026 that an unstated licence does "
    "not block an image build."
)
ID_VAR = "ResponseId"

# Data suffix -> (arm index, factor level, the file-name kind in every stimulus folder).
ARMS: list[tuple[str, int, str, str]] = [
    ("control", 0, "none", "control"),
    ("sc", 1, "few_likes", "low"),
    ("sca", 2, "many_likes", "high"),
    ("scp", 3, "many_likes_link", "link"),
]
# What the authors' code (analysis_truenews_osf.html) assigns each suffix.
AUTHORS_CODING = {"control": "control", "sc": "low ampl", "sca": "high ampl", "scp": "ampl+link"}

DVS = [
    (
        "acc",
        "To the best of your knowledge, how accurate is the claim in the above headline?",
        {"min": 1, "max": 4, "min_label": "not at all accurate", "max_label": "very accurate"},
    ),
    (
        "like",
        'How likely are you to "like" the article/post in the headline that you just read?',
        {"min": 1, "max": 5, "min_label": "not at all likely", "max_label": "very likely"},
    ),
    (
        "share",
        "How likely are you to share the article/post in the headline that you just read?",
        {"min": 1, "max": 5, "min_label": "not at all likely", "max_label": "very likely"},
    ),
]

# ---------------------------------------------------------------------------
# The thirteen posts, transcribed. Each picture's words are composed from blocks
# below; every block was read against its file (see the module docstring for the
# transcription rule). `counts[arm]` holds what differs between the three
# comment arms: (correction likes, support likes, and any per-file variants).
# ---------------------------------------------------------------------------

FB_TAIL = "Write a comment..."


POSTS: list[dict[str, Any]] = [
    {
        "var": "post_1",
        "folder": "Stimulus FALSE NEWS 1 (twitter) - NHS",
        "key": "false01",
        "veracity": "false",
        "platform": "Twitter",
        "topic": "nhs",
    },
    {
        "var": "post_2",
        "folder": "Stimulus FALSE NEWS 2 (twitter) - pilot",
        "key": "false02",
        "veracity": "false",
        "platform": "Twitter",
        "topic": "vaccine",
    },
    {
        "var": "post_3",
        "folder": "Stimulus FALSE NEWS 3 (facebook) - children vaccine death",
        "key": "false03",
        "veracity": "false",
        "platform": "Facebook",
        "topic": "vaccine",
    },
    {
        "var": "post_5",
        "folder": "Stimulus FALSE NEWS 5 (facebook) - boat",
        "key": "false05",
        "veracity": "false",
        "platform": "Facebook",
        "topic": "brexit",
    },
    {
        "var": "post_6",
        "folder": "Stimulus FALSE NEWS 6 (facebook) - COP26",
        "key": "false06",
        "veracity": "false",
        "platform": "Facebook",
        "topic": "climate",
    },
    {
        "var": "post_8",
        "folder": "Stimulus FALSE NEWS 8 (facebook) - pfizer president & killer vaccine",
        "key": "false08",
        "veracity": "false",
        "platform": "Facebook",
        "topic": "vaccine",
    },
    {
        "var": "post_10",
        "folder": "Stimulus FALSE NEWS 10 (facebook) - pfizer CEOs wife killed by vaccine",
        "key": "false10",
        "veracity": "false",
        "platform": "Facebook",
        "topic": "vaccine",
    },
    {
        "var": "post_11",
        "folder": "Stimulus FALSE NEWS 11 (twitter) - COP private jets",
        "key": "false11",
        "veracity": "false",
        "platform": "Twitter",
        "topic": "climate",
    },
    {
        "var": "post_12",
        "folder": "Stimulus FALSE NEWS 12 (facebook) - biolabs in Ukraine",
        "key": "false12",
        "veracity": "false",
        "platform": "Facebook",
        "topic": "russia",
    },
    {
        "var": "post_13",
        "folder": "Stimulus FALSE NEWS 13 (twitter) - Ukraine bombing civilians",
        "key": "false13",
        "veracity": "false",
        "platform": "Twitter",
        "topic": "russia",
    },
    {
        "var": "realpost_1",
        "folder": "Stimulus TRUE NEWS 1 (facebook) - covid",
        "key": "true01",
        "veracity": "true",
        "platform": "Facebook",
        "topic": "effective covid booster",
    },
    {
        "var": "realpost_2",
        "folder": "Stimulus TRUE NEWS 2 (facebook) - monkeypox",
        "key": "true02",
        "veracity": "true",
        "platform": "Facebook",
        "topic": "monkeypox cases rise",
    },
    {
        "var": "realpost_3",
        "folder": "Stimulus TRUE NEWS 3 (facebook) - covid",
        "key": "true03",
        "veracity": "true",
        "platform": "Facebook",
        "topic": "covid jab and blood clot",
    },
]
FALSE_VARS = [p["var"] for p in POSTS if p["veracity"] == "false"]
TRUE_VARS = [p["var"] for p in POSTS if p["veracity"] == "true"]
# The authors' congeniality code names the opinion each false post bears on.
OPINION_TOPIC = {
    "opinion_nhs": "nhs",
    "opinion_vaccine": "vaccine",
    "opinion_brexit": "brexit",
    "opinion_climate": "climate",
    "russia_feeling": "russia",
}


def _tw_reply(head: str, to: str, text: str) -> list[str]:
    return [head, f"Replying to {to}", text]


def words(key: str, arm: str) -> list[str]:
    """The blocks of words printed in one picture, top to bottom."""
    w = _WORDS[key]
    return list(w(arm))


def text_in_image(key: str, arm: str) -> str:
    return " / ".join(words(key, arm))


def _false01(arm: str) -> list[str]:
    head = [
        "Robert Ashcroft",
        "robertashcroft",
        "There are only TWO projects in history that have cost more than the Track & Trace "
        "app: the ISS (£72bn) and the entire US road network (£82bn). So there we have it: at "
        "£37 billion, the third most expensive thing we've ever spaffed money on is a broken "
        "version of Pokemon Go.",
        "NHS Test and Trace",
        "4:17 PM · Feb 2, 2021",
        "27 Retweets 188 Likes",
    ]
    if arm == "control":
        return head
    c1, c2 = {"low": ("6", "5"), "high": ("145", "6"), "link": ("145", "6")}[arm]
    link = (
        [
            "fullfact.org",
            "Flawed comparisons between test and trace systems go viral - Full Fact",
            "Claims suggesting the system in England costs vastly more than those in Wales "
            "and Ireland uses incomparable figures.",
        ]
        if arm == "link"
        else []
    )
    return [
        *head,
        *_tw_reply(
            "Anita Vara @anitavara · 5h",
            "@robertashcraft",
            "This is somewhat misleading: NHS Test and Trace is not an app but all "
            "coronavirus testing in the UK...",
        ),
        *link,
        c1,
        *_tw_reply("John Milton @johnmilton · 4h", "@robertashcraft", "This is absolutely insane!"),
        c2,
    ]


def _false02(arm: str) -> list[str]:
    head = [
        "Cliff Davie",
        "cliffdavie",
        "So, we're just not going to talk about the Delta pilot who died mid-flight in the "
        "cockpit just a few weeks after taking the COVID vaccine?",
        "Moderna COVID-19 Vaccine",
        "14:17 PM · Oct 7, 2021",
        "28 Retweets 184 Likes",
    ]
    if arm == "control":
        return head
    c1 = {"low": "7", "high": "156", "link": "156"}[arm]
    link = (
        ["HEALTH / CORONAVIRUS", "Vaccinated pilot did not die mid-flight", "21 OCTOBER 2021"]
        if arm == "link"
        else []
    )
    return [
        *head,
        *_tw_reply(
            "Lisa Langley @lisalangley · 9h",
            "@cliffdavie",
            "Someone else posted about this topic. Of course, nothing attached showing it's "
            "been documented. Stop spreading crap that isn't true or give us a reliable source.",
        ),
        *link,
        c1,
        *_tw_reply(
            "Terence Royston @terenceroyston · 4h",
            "@cliffdavie",
            "Holy shit, Biden was hiding these risks???? What the hell other risks are they "
            "hiding from travelers?",
        ),
        "6",
    ]


def _fb_head(name: str, when: str, post: list[str], reactions: str, counts: str) -> list[str]:
    return [name, when, *post, reactions, counts, "Like", "Share"]


def _false03(arm: str) -> list[str]:
    head = _fb_head(
        "Hannah Green",
        "Yesterday at 14:45pm",
        [
            "Deaths among male Children are 83% higher than the 5-year-average since they "
            "were given the Covid-19 Vaccine"
        ],
        "158",
        "25 Comments 5 Shares",
    )
    if arm == "control":
        return [*head, "View more 25 Comments", FB_TAIL]
    c1 = {"low": "10", "high": "100", "link": "100"}[arm]
    link = (
        [
            "No evidence linking deaths among children to vaccine rollout - Full Fact",
            "An article by The Exposé makes a misleading link betw",
        ]
        if arm == "link"
        else []
    )
    return [
        *head,
        "View more 23 Comments",
        "Julie Milton Stop spreading crap that isn't true",
        *link,
        *_fb_comment_tail(c1, "7h"),
        "David Walker There is something seriously wrong when the 'cure' kills more children "
        "than the 'problem'. Wake up people!",
        *_fb_comment_tail("9", "7h"),
        FB_TAIL,
    ]


def _fb_comment_tail(count: str, age: str) -> list[str]:
    return [count, f"Like · Reply · {age}"]


def _false05(arm: str) -> list[str]:
    head = _fb_head(
        "Hugo Sherlock",
        "Yesterday at 13:14am",
        [
            "Did you know, another interesting point. Fishing boats run on EU subsidised fuel "
            "running at around 30p a litre. After brexit ( 1st January) it will be £1.40 litre. "
            "That's on top of the tariffs they will have to pay to sell their fish to the EU!",
            "TOKATU NELSON",
        ],
        "106",
        "20 Comments 3 Shares",
    )
    if arm == "control":
        return [*head, "View more 20 Comments", FB_TAIL]
    c1, c2, age2, port = {
        "low": ("10", "10", "7h", "port!"),
        "high": ("153", "1", "4h", "port!"),
        "link": ("153", "10", "7h", 'port!"'),
    }[arm]
    link = (
        [
            "ONLINE",
            "Brexit hasn't quadrupled the cost of fuel for fishing boats",
            "10 NOVEMBER 2021",
        ]
        if arm == "link"
        else []
    )
    return [
        *head,
        "View more 18 Comments",
        "Diane Ryan This post is disingenuous if not a straight forward lie",
        *link,
        *_fb_comment_tail(c1, "4h"),
        "Helen Sanson Not forgetting the paperwork will take longer, fish less fresh, and "
        f"that's IF the French let them into {port}",
        *_fb_comment_tail(c2, age2),
        FB_TAIL,
    ]


def _false06(arm: str) -> list[str]:
    head = _fb_head(
        "John Basham",
        "Yesterday at 17:09pm",
        [
            "REPORT: A Group Of Diesel Gas Generators Are Hidden From Public View Behind "
            "Screens At The #COP26 Climate Conference. Why Didn't They Use Wind & Solar To "
            "Power The Event?",
            "YADX166",
            "aggreko",
        ],
        "161",
        "20 Comments 6 Shares",
    )
    if arm == "control":
        return [*head, "View more 20 Comments", FB_TAIL]
    c1, age2 = {"low": ("10", "4h"), "high": ("184", "4h"), "link": ("184", "1h")}[arm]
    link = (
        ["Fact Check-COP26 did not use diesel generators to power event, organizers say"]
        if arm == "link"
        else []
    )
    return [
        *head,
        "View more 18 Comments",
        "Claude Hodgkinson There is something deeply deeply fishy about this",
        *link,
        *_fb_comment_tail(c1, "1h"),
        "Stephen Hughes They are failing on multiple fronts to keep the charade going much longer",
        *_fb_comment_tail("7", age2),
        FB_TAIL,
    ]


def _false08(arm: str) -> list[str]:
    head = _fb_head(
        "Brittany Dickson",
        "Yesterday at 11:54",
        [
            "Dr. Michael Yeadon, former Pfizer vice president, warns children are 50 times "
            "more likely to be killed by the covid vaccines than the virus itself"
        ],
        "178",
        "12 Comments 6 Shares",
    )
    if arm == "control":
        return [*head, FB_TAIL]
    c1, seems, age = {
        "low": ("3", "Seema", "8h"),
        "high": ("166", "Seems", "5h"),
        "link": ("166", "Seems", "5h"),
    }[arm]
    link = (
        [
            "Fact Check-No evidence to support claim by ex-Pfizer scientist on COVID-19 "
            "vaccine safety in children",
            "By Reuters Fact Check",
        ]
        if arm == "link"
        else []
    )
    return [
        *head,
        "View more 10 Comments",
        f"Anja Weimer There is not the slightest evidence. {seems} Yeadon has an axe to grind "
        "with his former employer.",
        *link,
        *_fb_comment_tail(c1, age),
        "Doug Stanton Pushing these DANGEROUS JABS on children = WILFUL CHILD ENDANGERMENT",
        *_fb_comment_tail("3", age),
        FB_TAIL,
    ]


def _false10(arm: str) -> list[str]:
    head = _fb_head(
        "Harry Abraham",
        "Yesterday at 13:56",
        [
            "Myriam Bourla – the wife of Pfizer CEO Albert Bourla – has died from "
            "complications from the COVID-19 vaccine early Wednesday, according to her "
            "doctor. She passed away in the emergency room at New York-Presbyterian Lawrence "
            "Hospital after being brought in by paramedics. The cause of death has been "
            "listed as complications from the Pfizer vaccine.",
            "Pfizer",
        ],
        "155",
        "21 Comments 10 Shares",
    )
    if arm == "control":
        return [*head, "View more 21 Comments", FB_TAIL]
    c1 = {"low": "10", "high": "109", "link": "109"}[arm]
    link = (
        [
            "REUTERS.COM",
            "Fact Check-False claim about Pfizer CEO's wife dying after complications from "
            "COVID-19 vaccine",
        ]
        if arm == "link"
        else []
    )
    return [
        *head,
        "View more 19 Comments",
        "Pauline Clay No. Just not. Never happened.",
        *link,
        *_fb_comment_tail(c1, "4h"),
        "Frederika Barclay Oops? Could that be Karma or just bad luck?",
        *_fb_comment_tail("5", "7h"),
        FB_TAIL,
    ]


def _false11(arm: str) -> list[str]:
    head = [
        "Linda White",
        "lindawhite",
        "There are 400 private jets ferrying delegations to the COP26 conference. It is "
        "estimated they will emit in 24 hours as much CO2 as Scotland emits in a year!",
        "16:30 AM · Nov 2, 2021",
        "29 Retweets 152 Likes",
    ]
    if arm == "control":
        return head
    c1 = {"low": "8", "high": "148", "link": "148"}[arm]
    # The handle is printed "@ lindawhite" (with a space) in the low and high files only.
    to = "@lindawhite" if arm == "link" else "@ lindawhite"
    link = (
        [
            "FULLFACT.ORG",
            "Emissions from COP26 private jets are far, far lower than Scotland's annual CO2 "
            "output - Full Fact",
        ]
        if arm == "link"
        else []
    )
    return [
        *head,
        *_tw_reply(
            "David Martin @davidmartin · 8h",
            to,
            "You know this isn't true. Or even remotely close to the truth.",
        ),
        *link,
        c1,
        *_tw_reply("Peter Turner @peterturner · 5h", to, "This is embarrassing"),
        "6",
    ]


def _false12(arm: str) -> list[str]:
    head = _fb_head(
        "Mary Barrett",
        "Yesterday at 4:42pm",
        [
            "US BIOLABS IN UKRAINE",
            "Exclusive US biolabs in Ukraine, and they are financed at the expense of the US "
            "Department of Defense.",
            "The laboratories are located in Odessa, Vinnytsia, Uzhgorod, Lviv (three), Kiev "
            "(three), Kherson, Ternopil, and near Crimea and Luhansk. 2 other possible "
            "locations Kharkiv and Mykolaiv",
        ],
        "128",
        "21 Comments 10 Shares",
    )
    if arm == "control":
        return [*head, "View more 21 Comments", FB_TAIL]
    c1 = {"low": "9", "high": "155", "link": "155"}[arm]
    link = (
        [
            "FACT CHECK",
            "Fact check: False claim of US biolabs in Ukraine tied to Russian disinformation "
            "campaign",
            "Ella Lee",
            "USA TODAY",
            "Published 6:39 p.m. ET Feb. 25, 2022 | Updated 2:59 p.m. ET Feb. 27, 2022",
        ]
        if arm == "link"
        else []
    )
    return [
        *head,
        "View more 19 Comments",
        "Tom Archer Baseless and unfounded. Crap!",
        *link,
        *_fb_comment_tail(c1, "5h"),
        "David Askew You are right",
        *_fb_comment_tail("7", "4h"),
        FB_TAIL,
    ]


def _false13(arm: str) -> list[str]:
    head = [
        "Garry Cave",
        "@garryknows",
        "MFA Russia",
        "@mfa_russia",
        "Russia government organization",
        "Classified documents (order by the Commander National Guard of Ukraine) acquired by "
        "@mod_russia confirm without a shadow of a doubt: the Kiev regime was covertly "
        "preparing an offensive operation against #Donbass, scheduled for March 2022.",
        "In detail: bit.ly/3pKBYMf",
        "4:17 PM · March 9, 2022 · Twitter for Adroid",
        "25 Retweets 175 Likes",
    ]
    if arm == "control":
        return head
    c1 = {"low": "6", "high": "155", "link": "155"}[arm]
    link = (
        [
            "MENU",
            "POLITIFACT",
            "The Poynter Institute",
            "By Samantha Putterman",
            "March 14, 2022",
            "No, this document doesn't show classified Ukrainian military orders to attack "
            "the Donbas region",
        ]
        if arm == "link"
        else []
    )
    return [
        *head,
        *_tw_reply("Rory Fraser @roryontwitter · 6h", "@garryknows", "What utter hogwash."),
        *link,
        f"0 0 {c1}",
        *_tw_reply(
            "Ann Ball @annball123 · 4h",
            "@garryknows",
            "Putin saved the Donbas people of another massacre.",
        ),
        "0 0 5",
    ]


def _true01(arm: str) -> list[str]:
    head = _fb_head(
        "Victoria Moon",
        "Yesterday at 5:45pm",
        [
            "Two Pfizer and BioNTech Covid-19 vaccine booster updated to target the Omicron "
            "variant show a substantially higher immune response than the current COVID-19 "
            "vaccine.",
            "COVID-19 VACCINE",
        ],
        "152",
        "24 Comments 6 Shares",
    )
    if arm == "control":
        return [*head, "View more 18 Comments", FB_TAIL]
    c1 = {"low": "9", "high": "112", "link": "112"}[arm]
    link = (
        [
            "INDEPENDENT.CO.UK",
            "Mum, 36, most likely died from Covid Pfizer vaccine days after dose, inquest told",
        ]
        if arm == "link"
        else []
    )
    return [
        *head,
        "View more 18 Comments",
        "Jonathan Manley More lies",
        *link,
        *_fb_comment_tail(c1, "8h"),
        "Laura McConnell Thank you all science",
        *_fb_comment_tail("8", "11h"),
        FB_TAIL,
    ]


def _fb_head3(name: str, when: str, post: list[str], reactions: str, counts: str) -> list[str]:
    return [name, when, *post, reactions, counts, "Like", "Comment", "Share"]


def _true02(arm: str) -> list[str]:
    head = _fb_head3(
        "Ian Levy",
        "Yesterday at 4:45pm",
        [
            "BREAKING: 219 new cases detected in UK",
            "Monkeypox cases continue to rise in UK: 99 per cent of all infections are among "
            "men, says UK Health Security Agency",
        ],
        "175",
        "21 Comments 10 Shares",
    )
    if arm == "control":
        return [*head, "View more 16 Comments", FB_TAIL]
    c1 = {"low": "6", "high": "176", "link": "176"}[arm]
    link = (
        [
            "Peter McCullough, MD MPH",
            "@P_McCulloughMD",
            "Follow",
            "Planning for Monkeypox campaign was in the planning for years "
            'WHO/WEF/CEPI/CDC/Jynneos. The CDC has a large "Monkeypox Response Team" and '
            "there were planning exercises in Munich in March 2021. I explain to Childrens "
            "Health Defense Dr Tony O'Donnell.@ChildrensHD",
            "CHD.TV",
            "Dr. Peter A. McCullough, MD, MPH",
        ]
        if arm == "link"
        else []
    )
    return [
        *head,
        "View more 19 Comments",
        "Sandra Hart Judging by the comments I am not the only one to call BS on this",
        *link,
        *_fb_comment_tail(c1, "1h"),
        "Karen Lees Every virus is coming to UK",
        *_fb_comment_tail("5", "2h"),
        FB_TAIL,
    ]


def _true03(arm: str) -> list[str]:
    head = _fb_head3(
        "Jonathan Lamb",
        "Yesterday at 2:45pm",
        ["Jack Last died of a blood clot days after Covid jab, inquest told"],
        "188",
        "24 Comments 11 Shares",
    )
    if arm == "control":
        return [*head, "View more 24 Comments", FB_TAIL]
    c1 = {"low": "8", "high": "125", "link": "125"}[arm]
    link = (
        [
            "Public Health Communications COLLABORATIVE",
            "Post baselessly links COVID-19 vaccines to blood clots, miscarriage, and Bell's palsy",
            "May 01, 2022",
        ]
        if arm == "link"
        else []
    )
    return [
        *head,
        "View more 22 Comments",
        "John Dines What a load of bull shi££",
        *link,
        *_fb_comment_tail(c1, "1h"),
        "Helen Bowie Women take birth control daily and that too can cause blood clots, but "
        "guess what, they still rather take the risk",
        *_fb_comment_tail("7", "1h"),
        FB_TAIL,
    ]


_WORDS = {
    "false01": _false01,
    "false02": _false02,
    "false03": _false03,
    "false05": _false05,
    "false06": _false06,
    "false08": _false08,
    "false10": _false10,
    "false11": _false11,
    "false12": _false12,
    "false13": _false13,
    "true01": _true01,
    "true02": _true02,
    "true03": _true03,
}

# ---------------------------------------------------------------------------
# Descriptions: what each picture shows, in our words. One for the post, one
# per arm for the comments. Visible facts only; the words are in text_in_image.
# ---------------------------------------------------------------------------

POST_DESCRIPTIONS: dict[str, str] = {
    "false01": (
        "A screenshot of a Twitter post, portrait. A round profile photograph of a smiling "
        "man, his name with a blue verified tick, and his handle. The post's picture: on the "
        "left a pale panel of dark blue condensed text; on the right a hand holding up a "
        'mobile phone whose blue screen shows the NHS logo and "Test and Trace". Below: '
        "the time and date, the retweet and like counts, and Twitter's reply, retweet, like "
        "and share icons."
    ),
    "false02": (
        "A screenshot of a Twitter post, portrait. A round profile photograph of a smiling "
        "young man and his name and handle. The post's picture is a grey-toned image of an "
        "airliner flying through a stormy sky with lightning above a runway, a vaccine vial "
        "labelled as Moderna's COVID-19 vaccine standing in the foreground; the post's words "
        "are printed across it in large red condensed capitals. Below: the time and date, "
        "the retweet and like counts, and Twitter's icons."
    ),
    "false03": (
        "A screenshot of a Facebook post. A round profile photograph of a woman with a "
        "green online dot, her name, and the time with a globe icon. The post's picture is "
        "an orange square fading to white in the centre, the claim in large black condensed "
        "type. Below it: reaction icons (like, wow, sad) with the reaction count, the "
        "comment and share counts, and Facebook's Like and Share buttons."
    ),
    "false05": (
        "A screenshot of a Facebook post. A round profile photograph of a man with a green "
        "online dot, his name, and the time with a globe icon. The post's picture: on the "
        "left a photograph of a large blue and white fishing vessel at sea, its name on the "
        "bow, cut out with a torn edge; on the right the claim in black type on white. "
        "Below it: reaction icons (like, love, wow) with the reaction count, the comment "
        "and share counts, and Facebook's Like and Share buttons."
    ),
    "false06": (
        "A screenshot of a Facebook post. A round profile photograph of a man with a green "
        "online dot, his name, and the time with a globe icon. The post's picture is a "
        "photograph of grey generator units behind a white perforated screen, branded "
        "Aggreko, with a black hexagon of white text over it and two smaller hexagonal "
        "photographs of generators behind screens. Below it: reaction icons (like, love, "
        "laugh) with the reaction count, the comment and share counts, and Facebook's Like "
        "and Share buttons."
    ),
    "false08": (
        "A screenshot of a Facebook post. A round profile photograph with a green online "
        "dot, the poster's name, and the time with a globe icon. The post's picture: on the "
        "left a photograph of a grey-haired man in glasses speaking; on the right, on "
        "black, a black-and-white photograph of a frightened child with hands at the mouth, "
        "a thin white line, and the claim in white type. Below it: three reaction icons "
        "with the reaction count, the comment and share counts, and Facebook's Like and "
        "Share buttons."
    ),
    "false10": (
        "A screenshot of a Facebook post. A round profile photograph of a man in "
        "sunglasses with a green online dot, his name, and the time with a globe icon. The "
        "post's picture: the claim in black type on white on the left; on the right a "
        "photograph of a grey-haired man in glasses, suit and blue tie speaking at a lectern "
        "bearing the Pfizer logo. Below it: reaction icons (like, love, angry) with the "
        "reaction count, the comment and share counts, and Facebook's Like and Share "
        "buttons."
    ),
    "false11": (
        "A screenshot of a Twitter post, portrait. A round profile photograph of a "
        "dark-haired woman and her name and handle. The post's picture is an aerial "
        "photograph of dozens of private jets parked in rows on an airfield, with a "
        "translucent white circle on the left holding the claim in dark type under a short "
        "rule. Below: the time and date, the retweet and like counts, and Twitter's icons."
    ),
    "false12": (
        "A screenshot of a Facebook post. A round profile photograph of a woman with a "
        "green online dot, her name, and the time with a globe icon. The post's picture: "
        '"US BIOLABS IN UKRAINE" in red capitals on a black band; below it a political '
        "map of Ukraine and its neighbours, with a partly cut-off Nations Online Project "
        "credit, its oblast names, "
        "cities, seas and a legend, marked with red and purple dots; and at the foot, on "
        "black, the claim in yellow type on the left and the list of locations in white "
        "type on the right. Below it: three reaction icons with the reaction count, the "
        "comment and share counts, and Facebook's Like and Share buttons."
    ),
    "false13": (
        "A screenshot of a Twitter post, portrait: a man's quote of another tweet. A round "
        "profile photograph of a man in a cap, his name and handle. The quoted tweet, in a "
        "bordered box, is from MFA Russia (round dark blue emblem, Russian flag, blue "
        "verified tick, government-organisation label) and opens with a red exclamation "
        "mark; @mod_russia, #Donbass and the bit.ly link are in blue. Under its text, "
        "three photographs of typed Ukrainian documents with handwritten notes, signatures "
        'and stamps. Below: the time, date and "Twitter for Adroid" in blue, the retweet '
        "and like counts, and Twitter's icons."
    ),
    "true01": (
        "A screenshot of a Facebook post. A round profile photograph of a woman with a "
        "green online dot, her name, and the time with a globe icon. The post's picture is "
        'a photograph of a row of vaccine vials with blue caps labelled "COVID-19 '
        'VACCINE", the claim in white type down the left side. Below it: reaction icons '
        "(like, wow, laugh) with the reaction count, the comment and share counts, and "
        "Facebook's Like and Share buttons."
    ),
    "true02": (
        "A screenshot of a Facebook post. A round profile photograph of a man with a "
        "green online dot, his name, and the time with a globe icon. The post's picture: "
        "close-up photographs of skin with raised spots (a shoulder above, a torso below), "
        "with a white band across the middle holding a bold headline and a subheading in "
        "black. Below it: reaction icons (like, sad, laugh) with the reaction count, the "
        "comment and share counts, and Facebook's Like, Comment and Share buttons."
    ),
    "true03": (
        "A screenshot of a Facebook post. A round profile photograph of a young man with a "
        "green online dot, his name, and the time with a globe icon. The post's picture: "
        "the headline in large black type on white on the left, and on the right a "
        "photograph of a smiling man with tousled brown hair outdoors. Below it: reaction "
        "icons (like, sad, angry) with the reaction count, the comment and share counts, "
        "and Facebook's Like, Comment and Share buttons."
    ),
}

ARM_DESCRIPTIONS: dict[str, str] = {
    "control": "No comments are shown.",
    "low": (
        "Below, two comments, each with its commenter's round profile photograph and its "
        "like count beside {icons}."
    ),
    "high": (
        "Below, two comments, each with its commenter's round profile photograph and its "
        "like count beside {icons}."
    ),
    "link": (
        "Below, two comments, each with its commenter's round profile photograph and its "
        "like count beside {icons}. The first carries a link card: {card}."
    ),
}
# How a comment's like count is shown, where it is not the platform's usual.
ICONS = {
    "Twitter": "a red heart",
    "Facebook": "small reaction icons",
    "false13": "a heart outline, after reply and retweet counts of 0",
}
LINK_CARDS: dict[str, str] = {
    "false01": "a photograph of a person in protective gear taking a throat swab from a woman, "
    "above the card's source, headline and summary",
    "false02": "a cropped article heading in bold black type, half underlined in turquoise, "
    "with a small grey section label above and a small grey date below",
    "false03": "a small photograph of a vaccine vial beside the headline and a line of grey "
    "text partly covered by the comment's reaction icons",
    "false05": "a cropped article heading in bold black type underlined in turquoise, with a "
    "small grey section label above and a small grey date below",
    "false06": "a white card with the headline in bold black type",
    "false08": "a line of small grey type, the headline in bold black type, and a small "
    "grey byline",
    "false10": "the source in small grey capitals above the headline in bold black type",
    "false11": "a photograph of a white private jet in flight against a grey sky, above the "
    "card's source and headline",
    "false12": 'a USA TODAY fact-check heading: a small blue "FACT CHECK" label, the '
    "headline in bold black type, the author's photograph and name, and a small grey "
    "publication line",
    "false13": 'a screenshot of a PolitiFact article heading: the PolitiFact logo with "The '
    "Poynter Institute\" and a menu bar, the author's photograph, name and date on the left, "
    "and the headline in bold black type",
    "true01": "a photograph of a smiling man and woman cheek to cheek, above the card's "
    "source and headline",
    "true02": "an embedded tweet by Peter McCullough with a Follow button, its text, and a "
    "video still of a grey-haired man in a suit and earphones, with a caption and a "
    "CHD.TV logo",
    "true03": "the Public Health Communications Collaborative logo and a menu icon above the "
    "headline in bold black serif type and a small date line",
}


# Words in a picture that are NOT in its text_in_image, per post and arm ("*" = every
# arm). Named in the catalogue description; the condition says only that the quotation
# is partial.
UNQUOTED: dict[str, dict[str, str]] = {
    "false02": {"*": "the small print on the vial's label, blurred and cut off"},
    "false03": {"link": "the label on the vial in the link card's photograph, too small to read"},
    "false06": {"*": "large orange letters cut off by the picture's left edge"},
    "false08": {"link": "a line of grey type above the link card's headline, too small to read"},
    "false11": {
        "link": "a registration mark on the jet in the link card's photograph, too small to read"
    },
    "false12": {"*": "the map's place names, legend and credit"},
    "false13": {
        "*": "the lettering of the MFA Russia emblem and the typed and handwritten words of the "
        "photographed documents"
    },
    "true01": {"*": "the small print on the vials' labels, too small to read"},
}


def unquoted(key: str, arm: str) -> str | None:
    u = UNQUOTED.get(key, {})
    return u.get(arm) or u.get("*")


def description(key: str, arm: str) -> str:
    post = POST_DESCRIPTIONS[key]
    if arm == "control":
        return _with_unquoted(f"{post} {ARM_DESCRIPTIONS['control']}", key, arm)
    platform = next(p["platform"] for p in POSTS if p["key"] == key)
    icons = ICONS.get(key, ICONS[platform])
    text = ARM_DESCRIPTIONS[arm].format(icons=icons, card=LINK_CARDS.get(key, ""))
    return _with_unquoted(f"{post} {text}", key, arm)


def _with_unquoted(desc: str, key: str, arm: str) -> str:
    missing = unquoted(key, arm)
    return f"{desc} Words not transcribed: {missing}." if missing else desc


# ---------------------------------------------------------------------------
# The deposit
# ---------------------------------------------------------------------------


def deposit() -> pd.DataFrame:
    """The Qualtrics export as deposited: semicolon-separated, Windows-1252."""
    return pd.read_csv(DEPOSIT_CSV, sep=";", encoding="cp1252", low_memory=False)


def arm_column(var: str, suffix: str) -> str:
    """The display-order column for one arm of one post. realpost_3's sc column is
    named with a 2 in the deposit; the authors' parse_number reads its first number."""
    if var == "realpost_3" and suffix == "sc":
        return "realpost_3_DO_realpost_2_sc"
    return f"{var}_DO_{var}_{suffix}"


def assigned_arm(df: pd.DataFrame, var: str) -> pd.Series:
    """0-3 for the arm each respondent saw for this post, NaN where not shown.

    Refuses a respondent with two arms recorded, and an answer with no arm."""
    shown = pd.DataFrame({s: df[arm_column(var, s)].notna() for s, *_ in ARMS})
    if (shown.sum(axis=1) > 1).any():
        raise SystemExit(f"{var}: a respondent has two arms recorded")
    out = pd.Series(np.nan, index=df.index)
    for s, idx, *_ in ARMS:
        out[shown[s]] = idx
    for dv, *_ in DVS:
        if (df[f"{var}_{dv}"].notna() & out.isna()).any():
            raise SystemExit(f"{var}_{dv}: an answer with no arm recorded")
    return out


def double_drawn(df: pd.DataFrame, var: str) -> pd.Series:
    """True where both flow randomisers (FL_7 and FL_51) drew this false post."""
    if var not in FALSE_VARS:
        return pd.Series(False, index=df.index)
    return df[f"FL_7_DO_{var}"].notna() & df[f"FL_51_DO_{var}"].notna()


def authors_html_text(path: Path = TRUE_HTML) -> str:
    t = path.read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", "", t))


def authors_treatment_coding() -> dict[str, str]:
    """Suffix -> the authors' treatment label, read from their own code."""
    t = authors_html_text()
    num = {s: int(n) for s, n in re.findall(r'grepl\("(\w+)", temp_treatment\) ~ (\d)', t)}
    names = {int(n): lab for n, lab in re.findall(r'"(\d)" = "([^"]+)"', t)}
    return {s: names[n] for s, n in num.items()}


def authors_congeniality() -> dict[str, str]:
    """False post var -> the opinion its congeniality is scored on (authors' code)."""
    t = authors_html_text()
    out = {}
    for n, var in re.findall(r"congeniality_(\d+) <- ifelse\(dat_wide\$(\w+)", t):
        out[f"post_{n}"] = OPINION_TOPIC[var]
    return out


def authors_true_names() -> dict[str, str]:
    t = authors_html_text()
    block = t.split("post_name=case_when(", 1)[1].split("))", 1)[0]
    return {f"realpost_{n}": name for n, name in re.findall(r'post==(\d) ~ "([^"]+)"', block)}


def verify_mapping() -> None:
    """The proofs in the docstring, as assertions."""
    coding = authors_treatment_coding()
    if coding != AUTHORS_CODING:
        raise SystemExit(f"authors' treatment coding changed: {coding}")
    if authors_congeniality() != {p["var"]: p["topic"] for p in POSTS if p["var"] in FALSE_VARS}:
        raise SystemExit(f"congeniality topics disagree: {authors_congeniality()}")
    if authors_true_names() != {p["var"]: p["topic"] for p in POSTS if p["var"] in TRUE_VARS}:
        raise SystemExit(f"true-post names disagree: {authors_true_names()}")
    for p in POSTS:
        n = int(p["var"].rsplit("_", 1)[1])
        kind = "FALSE" if p["veracity"] == "false" else "TRUE"
        if not p["folder"].startswith(f"Stimulus {kind} NEWS {n} ("):
            raise SystemExit(f"{p['var']} is not folder {p['folder']}")


# ---------------------------------------------------------------------------
# Pictures
# ---------------------------------------------------------------------------


def file_kind(name: str) -> str:
    """control / low / high / link, from a stimulus file's own name."""
    stem = name.lower()
    if stem == "control.png":
        return "control"
    if stem.startswith("low"):
        return "low"
    if stem.startswith("high") and ("debunk" in stem or "link" in stem):
        return "link"
    if stem.startswith("high"):
        return "high"
    raise SystemExit(f"unrecognised stimulus file {name!r}")


def members() -> dict[tuple[str, str], str]:
    """(post key, kind) -> zip member, refusing a folder without exactly one of each."""
    with zipfile.ZipFile(ZIP) as z:
        names = [n for n in z.namelist() if n.endswith(".png")]
    out: dict[tuple[str, str], str] = {}
    for p in POSTS:
        inside = [n for n in names if n.split("/")[1] == p["folder"]]
        kinds = {file_kind(n.rsplit("/", 1)[1]): n for n in inside}
        if len(inside) != 4 or set(kinds) != {"control", "low", "high", "link"}:
            raise SystemExit(f"{p['folder']}: {inside}")
        for k, n in kinds.items():
            out[(p["key"], k)] = n
    if len(names) != 52:
        raise SystemExit(f"{len(names)} stimulus files, expected 52")
    return out


def image_id(key: str, kind: str) -> str:
    return f"4hjcf_{key}_{kind}"


def image_file(key: str, kind: str) -> str:
    return f"raw/{STUDY}/images/{image_id(key, kind)}.png"


def extract_images() -> None:
    IMAGES.mkdir(exist_ok=True)
    with zipfile.ZipFile(ZIP) as z:
        for (key, kind), member in members().items():
            (IMAGES / f"{image_id(key, kind)}.png").write_bytes(z.read(member))


def catalogue_entries() -> dict[str, dict[str, str]]:
    from micromotives_datasets.images import sha256_of

    out: dict[str, dict[str, str]] = {}
    with zipfile.ZipFile(ZIP) as z:
        for (key, kind), member in sorted(members().items()):
            f = image_file(key, kind)
            if (REPO / "data" / f).read_bytes() != z.read(member):
                raise SystemExit(f"{f} is not {member}")
            out[image_id(key, kind)] = {
                "file": f,
                "sha256": sha256_of(REPO / "data" / f),
                "source": (
                    f"OSF 4hjcf, methods/posts/stimuli_osf.zip, member {member!r}, copied "
                    "byte for byte. A mock social media post made by the authors with "
                    "zeoob.com (names generated, profile photographs from the FFHQ dataset, "
                    "per the paper); shown as one picture."
                ),
                "licence": LICENCE,
                "text_in_image": text_in_image(key, kind),
                "description": description(key, kind),
            }
    return out


def write_catalogue() -> None:
    """Add or refresh only this study's entries; re-read first, others are editing too."""
    path = REPO / "data" / "catalog" / "images.json"
    entries = catalogue_entries()
    current = json.loads(path.read_text())
    current.update(entries)
    path.write_text(json.dumps(current, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Persona and the derived wide file
# ---------------------------------------------------------------------------

# Supplementary Table 11 (the paper's ESM), in code order; see the docstring.
AGE = {1: "18-24", 2: "25-34", 3: "35-44", 4: "45-54", 5: "55-64", 6: "65+"}
GENDER = {1: "Female", 2: "Male", 4: "Non-binary / third gender / other"}
EDUCATION = {
    1: "Incomplete Secondary Education (Below GCSE / O Level), Secondary Education "
    "Completed (GCSE / O Level / CSE or equivalent), or Secondary Education Completed "
    "(A Level or equivalent)",
    2: "Some Vocational or Technical Qualifications or Vocational or Technical "
    "Qualifications Completed (e.g., HND, NVQ)",
    3: "University Education Completed (First Degree e.g., BA, BSc), Postgraduate "
    "Education Completed (e.g., Masters), Doctorate, or Post-doctorate or equivalent",
}
PERSONA_VARS = {"age_scr": AGE, "gender_scr": GENDER, "edu_scr": EDUCATION}


def cond_var(var: str) -> str:
    return f"{var}_cond"


def wide() -> pd.DataFrame:
    """One row per respondent who was shown any post: id, persona as text, and per
    post the arm code (condition_num + 1; blank where not shown or double-drawn) and
    the three answers as deposited."""
    df = deposit()
    if not df[ID_VAR].is_unique:
        raise SystemExit(f"{ID_VAR} is not unique")
    out = pd.DataFrame({ID_VAR: df[ID_VAR]})
    for var, labels in PERSONA_VARS.items():
        codes = df[var]
        bad = set(codes.dropna().astype(int)) - set(labels)
        if bad:
            raise SystemExit(f"{var}: unlabelled codes {bad}")
        out[var] = codes.map(lambda c, lab=labels: lab.get(int(c)) if pd.notna(c) else None)
    any_shown = pd.Series(False, index=df.index)
    for p_index, p in enumerate(POSTS):
        arm = assigned_arm(df, p["var"])
        arm[double_drawn(df, p["var"])] = np.nan
        any_shown |= arm.notna()
        out[cond_var(p["var"])] = (arm + p_index * 4 + 1).astype("Int64")
        for dv, *_ in DVS:
            out[f"{p['var']}_{dv}"] = df[f"{p['var']}_{dv}"].astype("Int64")
    return out[any_shown].reset_index(drop=True)


def wide_csv_text() -> str:
    buf = io.StringIO()
    wide().to_csv(buf, index=False)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Crosscheck against the paper (Table 1) and the authors' true-news analysis
# ---------------------------------------------------------------------------

# Fixed effects of each arm against control, from the authors' lmer models
# (analysis_fakenews_osf.html = the paper's Table 1; analysis_truenews_osf.html).
PUBLISHED = {
    ("false", "acc"): (-0.09691, -0.12621, -0.11438),
    ("false", "like"): (-0.05755, -0.07752, -0.03339),
    ("false", "share"): (-0.038779, -0.039583, -0.045208),
    ("true", "acc"): (-0.054140, -0.173702, -0.098025),
}


def authors_sample(df: pd.DataFrame) -> pd.DataFrame:
    """The authors' filter (analysis_truenews_osf.html): Progress 100, age, education
    and gender present, and at least one false post answered."""
    keep = (
        (df["Progress"] == 100)
        & df["age_scr"].notna()
        & df["edu_scr"].notna()
        & df["gender_scr"].notna()
        & df[[f"{v}_acc" for v in FALSE_VARS]].notna().any(axis=1)
    )
    return df[keep]


def effects(mapping: dict[str, int] | None = None) -> dict[tuple[str, str], tuple[float, ...]]:
    """Each arm's effect against control, person and post fixed effects, by
    alternating demeaning. `mapping` relabels the data's suffixes to arm indices
    (default: the decoding above), so other decodings can be scored."""
    df = authors_sample(deposit())
    m = mapping or {s: i for s, i, *_ in ARMS}
    out: dict[tuple[str, str], tuple[float, ...]] = {}
    for veracity, vars_ in (("false", FALSE_VARS), ("true", TRUE_VARS)):
        for dv, *_ in DVS:
            parts = []
            for var in vars_:
                raw = assigned_arm(df, var)
                arm = raw.map(lambda a: np.nan if pd.isna(a) else m[ARMS[int(a)][0]])
                parts.append(
                    pd.DataFrame(
                        {"pid": df[ID_VAR], "post": var, "arm": arm, "y": df[f"{var}_{dv}"]}
                    )
                )
            long = pd.concat(parts).dropna()
            x = pd.get_dummies(long["arm"].astype(int)).reindex(columns=[1, 2, 3]).astype(float)
            y = long["y"].astype(float)
            for _ in range(50):
                for k in ("pid", "post"):
                    y = y - y.groupby(long[k]).transform("mean")
                    x = x - x.groupby(long[k]).transform("mean")
            beta = np.linalg.lstsq(x.to_numpy(), y.to_numpy(), rcond=None)[0]
            out[(veracity, dv)] = tuple(float(b) for b in beta)
    return out


def decoding_errors() -> dict[tuple[str, ...], float]:
    """Summed squared distance from PUBLISHED for every assignment of sc/sca/scp to
    low/high/link. The decoding used must be the unique minimum."""
    out: dict[tuple[str, ...], float] = {}
    for perm in itertools.permutations([1, 2, 3]):
        m = {"control": 0, "sc": perm[0], "sca": perm[1], "scp": perm[2]}
        est = effects(m)
        out[tuple(ARMS[i][3] for i in perm)] = sum(
            (a - b) ** 2 for k, pub in PUBLISHED.items() for a, b in zip(est[k], pub, strict=True)
        )
    return out


# ---------------------------------------------------------------------------
# Recipe
# ---------------------------------------------------------------------------


PARTIAL = " (not every word in it is quoted here)"


def arm_text(key: str, kind: str) -> str:
    partial = PARTIAL if unquoted(key, kind) else ""
    return f'You are shown a social media post{partial}: "{text_in_image(key, kind)}" <image>'


def recipe() -> dict[str, Any]:
    verify_mapping()
    arms: list[dict[str, Any]] = []
    outcomes: list[dict[str, Any]] = []
    for p_index, p in enumerate(POSTS):
        for _, a_index, level, kind in ARMS:
            num = p_index * 4 + a_index
            arms.append(
                {
                    "raw": num + 1,
                    "condition_num": num,
                    "factors": {"post": p["key"], "comment": level},
                    "text": arm_text(p["key"], kind),
                    "images": [image_id(p["key"], kind)],
                }
            )
        for d_index, (dv, question, scale) in enumerate(DVS):
            outcomes.append(
                {
                    "var": f"{p['var']}_{dv}",
                    "task_num": p_index * 3 + d_index,
                    "question": question,
                    "scale": dict(scale),
                    "response_recode": {i: i for i in range(scale["min"], scale["max"] + 1)},
                    "condition_var": cond_var(p["var"]),
                }
            )
    return {
        "study_id": STUDY,
        "source": "osf",
        "title": "Social corrections under false and true news posts: no comment, a correction "
        "with few or many likes, or with a fact-check link (UK, 2022)",
        "data_file": WIDE_NAME,
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": ID_VAR,
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_var": cond_var(POSTS[0]["var"]),
            "factors": ["post", "comment"],
            "arms": arms,
            "considered_and_rejected": {
                "FL_7_DO_*": "Position (1-3) of each false post within the first flow "
                "randomiser; presentation order, and used only to find double draws.",
                "FL_51_DO_*": "The same for the second flow randomiser.",
                "*_DO_*_acc / _like / _share": "Display order of the three questions within "
                "each post block: the constants 2, 3, 4 (fixed order).",
                "att_check3_scr_*": "An attention-check post shown before the task to the "
                "main sample (added after the soft launch); not a manipulation.",
            },
        },
        "outcomes": outcomes,
        "response_recode": {},
        "missing_codes": [],
        "persona_map": {"age_band": "age_scr", "gender": "gender_scr", "education": "edu_scr"},
    }


def render() -> str:
    return yaml.safe_dump(recipe(), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--prep", action="store_true", help="images and the derived wide CSV")
    ap.add_argument("--catalogue", action="store_true", help="add this study's images.json entries")
    args = ap.parse_args()
    if args.prep:
        verify_mapping()
        extract_images()
        WIDE.write_text(wide_csv_text())
        print(f"wrote {IMAGES.relative_to(REPO)}/ (52) and {WIDE.relative_to(REPO)}")
        return 0
    if args.catalogue:
        write_catalogue()
        print("updated data/catalog/images.json (4hjcf entries only)")
        return 0
    text = render()
    if args.check:
        same = RECIPE.exists() and RECIPE.read_text() == text
        same_wide = WIDE.exists() and WIDE.read_text() == wide_csv_text()
        print("recipe matches generator" if same else "recipe DIFFERS from generator")
        print("wide CSV matches generator" if same_wide else "wide CSV DIFFERS from generator")
        return 0 if same and same_wide else 1
    RECIPE.write_text(text)
    print(f"wrote {RECIPE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
