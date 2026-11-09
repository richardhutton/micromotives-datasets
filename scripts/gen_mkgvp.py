#!/usr/bin/env python3
"""Write recipes/images/mkgvp.yaml: a burglary to report, and a police building seen twice.

Headley, Blount-Hill and St. John, TESS 1126 (fielded as NORC 8041.050, "TESS 050
Headley"), "Affective Architecture: Isolating the Influence of Physical Environment on
Perceptual and Behavioral Attitudes toward Police". OSF mkgvp, the TESS deposit
headley1126.zip: the data (8041.050_TESS 050 Headley.dta, and TESS0050_Headley_STATA.dta,
whose bytes differ in the header but whose 732 x 65 values are identical), its codebook,
the fielded questionnaire (8041.050_TESS 050 Headley_quex_v3clean.docx, "Q" below), NORC's
field report, the proposal (Headley1126.pdf) and the researchers' description document.

AmeriSpeak, US adults, web only (`SURV_MODE` 2 for all), English only (`SURV_LANG` 1),
fielded 13 to 28 November 2019. The proposal asked for equal White, Black and Latinx
thirds, and RACETHNICITY holds only codes 1, 2 and 4. 732 completed; all are built.

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* DESIGN. Twelve conditions between people: six buildings crossed with two question
  orders. The building is the preload `P_HEADLEY` (codebook and Q: 1-3 "Hostile
  defensive 1-3", 4-6 "Welcoming 1-3"; 126 / 121 / 120 / 127 / 117 / 121). The proposal's
  two factors are "type of building" (hostile/defensive or welcoming) and "external image"
  (three buildings of each type), so `design` and `building` here; both are carried by
  the pictures alone. The order is the script's `RND_01` (358 / 374), factor `order`: Q's
  directives read "IF RND_01=0 SHOW HEADLEY3, Q4, Q5 BEFORE HEADLEY1" and "IF RND_01=1
  SHOW HEADLEY3, Q4, Q5 AFTER Q3" (parsed and asserted). The data cannot confirm that
  direction (no timestamp covers Q4 or Q5), so it rests on the directive alone. RND_01 is
  independent of P_HEADLEY (every building has 50 to 70 people in each order).
  condition_num is 6 x RND_01 + P_HEADLEY - 1: 0-5 the six buildings with the police
  questions first, 6-11 the same buildings with them after. QC rules 1 and 5 compare words
  AND images (docs/CONVENTIONS.md, Image conditions).
* WHICH PICTURE IS WHICH ARM. Q's .txt export shows the [SHOW IF P_HEADLEY=n] lines with
  nothing under them, so the mapping is read from word/document.xml in document order:
  each "[SHOW IF P_HEADLEY=n]" paragraph is followed by exactly one embedded picture.
  Screen HEADLEY1A ("You now see the police department from a distance.") shows
  image3, image4, image5, image6, image7, image8 for n = 1..6; screen HEADLEY2 ("You are
  now closer...") shows image9..image14; and Q1, Q2 and Q3 each repeat HEADLEY2's
  picture above the question, the same media file for the same n (asserted). A second,
  independent witness: every picture's alt text is the path of the client's original
  file, "Image n hostile police building k.png" for the distant view and "... closeup"
  for the near one (n = 1-3 hostile k = n, n = 4-6 welcoming k = n - 3), and it agrees
  with the [SHOW IF] mapping for all 30 placements (asserted). Each distant photo and its
  close-up show the same building (read by eye). Word draws every picture uncropped
  (`<a:srcRect/>` on all of them, asserted), so the media file is what the page showed.
  The files are the copies NORC pasted into its questionnaire; the fielded files may
  differ in resolution or encoding.
* REDACTIONS. In four of the twelve photographs someone painted flat rectangles over
  lettering (P_HEADLEY 3, 4 and 6's close-ups and 6's distant view). The rectangles are
  part of what respondents saw, so the catalogue describes them and transcribes what
  remains readable; it never restores what they hide. The other photographs show their
  buildings' names or signs, sometimes legibly (catalogue `text_in_image`).
* CONDITION. No shared_context: the order narration comes first, so nothing every arm
  shares is a prefix. Every arm reads HEADLEY1 then HEADLEY1A's words, word-for-word from
  Q (the instruction to imagine the scenario, the burglary vignette, the walk to the
  police department and "You now see the police department from a distance."), then
  "<image> You are now closer to approaching the police department. <image>": the distant
  photo, HEADLEY2's one sentence word-for-word, and the close-up, in the order seen.
  Images and these words are identical across the two orders.
  For RND_01 = 0, the earlier block is narrated in front of that, as docs/CONVENTIONS.md
  ("Narrating what the respondent did") allows: what they were shown and asked, never
  what they answered. The quoted words are HEADLEY3, Q4's stem and nine statements, and
  Q5, all word-for-word from Q; the nine statements are listed in Q's order, and the row
  says they were shown in random order, which Q's [RANDOMIZE] makes true for everyone.
  The words that are OURS, added to join them, are exactly these four phrases, the
  second used twice: "You were first shown:" / "You were then asked:" / "for each of nine
  statements, shown in random order:" / "After that:".
  For RND_01 = 1 the block came after Q3, so no row names it (later screens are never
  named). The close-up appeared again above each question
  screen; the row places it once, directly before its question, which is the order the
  respondent met it. Typography only: curly quotes straightened, the ellipsis "..." made
  ASCII; "as honestly and realistic as you can" is the instrument's grammar and is kept.
* OUTCOMES. Twelve, each asked on a screen with the close-up above it:
  - Q1A-Q1I (task 0-8): the nine items of grid Q1, each "Indicate the likelihood that you
    would feel the following emotions and/or sentiments: I would feel..." then the item
    ("Safe as I am approaching this building"). The `<u>` tags round each emotion word are
    programming markup for underlining and are removed. The item in each variable is read
    from the codebook's bracketed label and asserted to be Q's listing order. Answers 1-5,
    1 "Clearly describes my feelings" .. 5 "Does not describe my feelings", midpoint
    "Moderately describes my feelings" (the data's labels, asserted equal to Q's).
  - Q2A, Q2B (task 9-10): "Please indicate your level of agreement with the following
    statement:" then each of the two statements; 1 "Strongly agree" .. 5 "Strongly
    disagree".
  - Q3 (task 11): "How likely are you to proceed in entering the police department?";
    1 "Very likely" .. 5 "Very unlikely".
  Item order within Q1 and Q2 was randomised and not recorded; no row says where its item
  sat. Each outcome drops 77 / 98 / 99 (DON'T KNOW / SKIPPED ON WEB / REFUSED, its own
  labels; only 98 occurs: 7 to 15 per Q1 item, 1 each on Q2A and Q2B, none on Q3).
* NOT BUILT. Q4 (nine police-legitimacy items: obligation to obey, normative alignment,
  satisfaction), Q5 (satisfaction at the last police stop), Q6 (ever been inside a police
  department) and Q7 (ever arrested). The proposal calls all of them "demographic and
  experiential items that might otherwise help to explain statistical relationships",
  i.e. controls, and asks for HEADLEY3/Q4/Q5 to be placed before the vignette for half the
  sample and after Q3 for the other half (`RND_01`, 358 / 374) "primarily to avoid priming
  stimuli responses". They are statements about the respondent and the police in general,
  not about the building shown, so they are not outcomes of this manipulation (the same
  call as yjvpn's moderator block and s6urt's profile items). Building Q4 for the
  RND_01 = 1 half only would make an outcome of a control measure for a self-selected
  half of its sample. Q6 and Q7 are facts about the respondent, but asked after the
  stimulus, so not admissible as persona; Q4/Q5 for the RND_01 = 0 half were asked
  before it, but sit in the outcomes' domain (police), so the domain rule keeps them out
  of the persona too. SocSci210 did not build them either. Excluded: Q4-Q7, twelve items,
  8,729 answers after skips (Q4 6,545, Q5 730, Q6 730, Q7 724).
* WHO. All 732 completes. `CaseId` is the participant id. Respondents answered each
  question or skipped it; each skip drops only that row. Rows: 12 outcomes x 732 people =
  8,784 possible, less 94 skips (92 on Q1, 2 on Q2, none on Q3) = 8,690.
* PERSONA. The standard AmeriSpeak preloads, as xtvu5 (the same NORC series): AGE,
  GENDER, EDUC (14 levels; Jev 0.99 over EDUC4), RACETHNICITY, INCOME (18 bands), MARITAL,
  EMPLOY, REGION4, HHSIZE, HOME_TYPE, HOUSING, METRO, INTERNET, PHONESERVICE, and the
  custom preloads P_PARTYID7, P_IDEO, P_RELIG, P_ATTEND (blank, not coded, where missing:
  5 / 0 / 8 / 7). GENDER 0 "Unknown" is left absent (no code 0 occurs; inert). P_IDEO 8
  "Haven't thought much about it" is KEPT as an answer, as xtvu5 keeps it; Jev called it
  non_answer at 0.72 (runner-up answer 0.19). `recipe_prep.py` preferred REGION9 at 0.40
  over REGION4 at 0.45 in the run-off; REGION4 is used, as every AmeriSpeak sibling does,
  because the persona crosswalk maps the four-region scheme. Two value labels are
  restored from Q's own preload table by `persona_label_rewrite`: P_RELIG 1, cut off at
  80 characters in the .dta ("... Presbyterian, Pent"), and P_IDEO 2, misspelt "Libreal"
  in the .dta where Q's table reads "Liberal" (no built row in the corpus carries
  "Libreal"). Not mapped: STATE, REGION9, AGE4 / AGE7 / EDUC4 (banded duplicates), the
  household age counts, Device, WEIGHT. No persona field names a building or a design.
* UK FIT. The photographs are recognisable US police buildings, several with US and state
  flags; rich accepted that for image builds on 9 Nov 2026. The words name no US place or
  institution ("police department" and the spelling "neighbor" are kept word-for-word).
  The sample is American.
* ANSWER KEY. SocSci210 holds this study: 8,690 rows, the same answers, but a different
  scope, so `comparable_to_socsci210` is false and the comparison lives in
  tests/test_gen_mkgvp.py. SocSci210 groups the twelve outcomes into three tasks (Q1, Q2,
  Q3), and its two conditions are RND_01, not the building: it describes condition 0 as a
  hostile/defensive building and 1 as a welcoming one, and its six condition-by-task
  response tables equal ours grouped by `order`, cell for cell, while they do not match
  ours grouped by `design`. So SocSci210's text names the wrong building type for about
  half the people in each of its conditions.
* JEV. `scripts/recipe_prep.py mkgvp --source tess` (instrument only): assignment
  P_HEADLEY at 0.94; persona as mapped above, with the two overrulings stated; no
  outcome label surprises. It found no questionnaire to scan, because Q is a .docx; the
  directives here are parsed from the .docx by this script.

    uv run python scripts/gen_mkgvp.py --prep       # copy the twelve photos out of the .docx
    uv run python scripts/gen_mkgvp.py --catalogue  # (re)write this study's images.json entries
    uv run python scripts/gen_mkgvp.py              # write the recipe
    uv run python scripts/gen_mkgvp.py --check      # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

STUDY = "mkgvp"
RAW = REPO / "data" / "raw" / STUDY
DATA_FILE = "8041.050_TESS 050 Headley.dta"
TWIN_FILE = "TESS0050_Headley_STATA.dta"
QUEX = RAW / "8041.050_TESS 050 Headley_quex_v3clean.docx"
CODEBOOK = RAW / "8041.050_TESS 050 Headley_Codebook.xlsx"
IMAGES = RAW / "images"
RECIPE = REPO / "recipes" / "images" / f"{STUDY}.yaml"
LICENCE = (
    "None stated: the TESS deposit on OSF (mkgvp, headley1126.zip) gives no reuse terms, "
    "and TESS has since suspended operations. The photographs are of real buildings, by "
    "photographers the deposit does not name. Used with rich's ruling of 9 Nov 2026 that an "
    "unstated licence does not block an image build."
)

ID_VAR = "CaseId"
COND_VAR = "P_HEADLEY"
ORDER_VAR = "RND_01"
# RND_01 -> the `order` factor level. 0 = HEADLEY3/Q4/Q5 before the vignette (narrated).
ORDER_LEVELS = {0: "police questions first", 1: "police questions after"}
# The only words of ours in any condition: they join the quoted RND_01 = 0 block.
FIRST_SHOWN = "You were first shown:"
THEN_ASKED = "You were then asked:"
FOR_EACH = "for each of nine statements, shown in random order:"
AFTER_THAT = "After that:"
P_HEADLEY_LABELS = {
    1: "Hostile defensive 1",
    2: "Hostile defensive 2",
    3: "Hostile defensive 3",
    4: "Welcoming 1",
    5: "Welcoming 2",
    6: "Welcoming 3",
}
# The two picture screens, and the question screens that repeat the second one's picture.
DISTANT_SCREEN = "HEADLEY1A"
CLOSE_SCREEN = "HEADLEY2"
REPEAT_SCREENS = ["Q1", "Q2", "Q3"]
VIEWS = {DISTANT_SCREEN: "distance", CLOSE_SCREEN: "closeup"}

Q1_VARS = [f"Q1{c}" for c in "ABCDEFGHI"]
Q2_VARS = ["Q2A", "Q2B"]
NON_ANSWERS = {77: "DON'T KNOW", 98: "SKIPPED ON WEB", 99: "REFUSED"}


def image_key(code: int, view: str) -> str:
    return f"p{code}_{view}"


def image_id(key: str) -> str:
    return f"{STUDY}_{key}"


# ---------------------------------------------------------------------------
# What is printed in each photograph, and what it shows. Read by eye from the files,
# zoomed; `text_in_image` is transcription (pieces separated by " / ", with notes in
# square brackets), `description` is ours: visible facts only, and never the
# researchers' "hostile" or "welcoming", which is what the respondents were judging.
# ---------------------------------------------------------------------------

TEXT_IN_IMAGE: dict[str, str] = {
    "p1_distance": (
        "[no legible words: the brown notice board at the lower left is printed with several "
        "paragraphs too small to read, and the narrow banner on the pole in front of the "
        "building carries no readable lettering]"
    ),
    "p1_closeup": (
        "7TH STREET / 100 N 200 / ANY TIME / PHILADELPHI LICE / HEADQUAR S / ENTRA E "
        "[partial: 7TH STREET and 100 N 200 are on the green street sign on the lamp post; a "
        "second street sign above it is turned edge-on and cannot be read. ANY TIME is on the "
        "tall red-and-white parking sign on the post at the left, whose other lines are too "
        "small to read. The last three lines are on the small blue sign on the wall below the "
        "pedestrian signal; the lamp post crosses it and hides the middle of each line, and "
        "its letters are small and blurred]"
    ),
    "p2_distance": (
        "POLICE / HEADQUARTERS / PNC / NO RIGHT TURN / ONE WAY "
        "[partial: POLICE HEADQUARTERS is in large letters high on the building's wall; PNC is "
        "the logo near the top of the dark tower behind; NO RIGHT TURN and ONE WAY are on the "
        "signs on the pole at the left. The green street sign on the building's corner, the "
        "small blue sign on its wall, the letters on the covered bridge's windows and the "
        "small white signs on the poles are too small or blurred to read]"
    ),
    "p2_closeup": (
        "POLICE / HEADQUARTERS / PNC / NO RIGHT TURN / ONE WAY "
        "[partial: POLICE HEADQUARTERS is in large letters on the pale stone corner; PNC is "
        "the logo on the dark tower behind; NO RIGHT TURN and ONE WAY are on the signs on the "
        "traffic-signal pole. The green street sign at the corner and the small sign on the "
        "post beside the parked cars cannot be read]"
    ),
    "p3_distance": (
        "OAKLAND POLICE / ADMINISTRATION BUILDING / 7th St / ONE WAY "
        "[partial: the first two lines are small and blurred, on the dark wall of the low "
        "building at the left; 7th St is the green street sign and ONE WAY the small sign "
        "by the street lamp. The badge on the shield-shaped sign carries no legible "
        "lettering]"
    ),
    "p3_closeup": (
        "AKLAND / OLICE "
        "[partial: on a dark panel above the entrance doors, in an arc; the first letter of "
        "each word is hidden by the door frame, and a line of smaller letters beneath is not "
        "legible. A flat grey rectangle is painted over the top of the shield-shaped sign above "
        "the entrance, and a flat black rectangle over part of the black wall at the left; "
        "what they cover cannot be read. The lettering on the building and on the yellow "
        "billboard at the far right is too small to read]"
    ),
    "p4_distance": (
        "[no legible words: the narrow banners on the lamp posts and the signs by the road are "
        "too small to read]"
    ),
    "p4_closeup": (
        "RY NEIGHBORHOOD STATION / AREA / B- "
        "[partial: RY NEIGHBORHOOD STATION is in large letters on the glass above the "
        "entrance; a flat blue-green rectangle is painted over the letters before it, and the "
        "R sits at the rectangle's edge. AREA "
        "and B- are on the stone wall to the left of the steps, behind the railing, which "
        "hides what follows B-]"
    ),
    "p5_distance": (
        "[no legible words: the low sign in front of the building is too small to read]"
    ),
    "p5_closeup": "[no legible words: no lettering or signs are visible]",
    "p6_distance": (
        "MMITME / QUARTERS "
        "[partial: MMITME is part of a line of large pale letters across the upper-floor "
        "windows; a large round letter in the window bay to its left cannot be read with "
        "certainty, and the rest of the line cannot be read. QUARTERS is in raised letters on the wall "
        "at ground level, its first letter partly behind a palm trunk; a flat grey rectangle is "
        "painted over the wall to its left. The round sign on the post at the far left is a "
        "symbol without words]"
    ),
    "p6_closeup": (
        "POLICE DEPARTMENT HEADQUARTERS "
        "[partial: in raised letters along the low concrete wall in front of the building; a "
        "flat grey rectangle is painted over the wall before POLICE, and another over a tall "
        "panel on the face of the tower at the left. A short number above the entrance doors "
        "is too small to read]"
    ),
}

DESCRIPTIONS: dict[str, str] = {
    "p1_distance": (
        "Colour photograph, landscape, taken from across a street. In the middle distance, a "
        "round building of four storeys in pale grey concrete, its curved front divided into a "
        "regular grid of small recessed windows, with a cylindrical structure rising from the "
        "middle of its roof. A high concrete wall runs along its base. In the foreground: a "
        "brick pavement, a street with a pedestrian crossing, a black metal railing at the "
        "right, a young tree, a fire hydrant and a brown notice board at the lower left; "
        "traffic lights on poles. Taller buildings and towers stand behind, under a pale blue "
        "sky with light cloud; the leaves of a tree fill the upper left corner."
    ),
    "p1_closeup": (
        "Colour photograph, landscape, taken from a street corner. A round building of pale "
        "grey concrete fills most of the frame: three rows of small recessed windows between "
        "vertical concrete fins, set back above a high, windowless concrete wall that runs "
        "along the pavement. In front: a white car parked at the kerb, a red fire hydrant, a "
        "small tree with yellowing leaves, and a lamp post carrying a green street sign, a "
        "pedestrian signal and a security camera, with a small blue sign on the wall behind "
        "it. Two people jog along the pavement at the right. Pale, overcast sky."
    ),
    "p2_distance": (
        "Colour photograph, landscape, taken from across a wide street. At the left, a "
        "three-storey building with upper floors faced in pale stone panels, with bands of "
        "windows and lettering high on the wall, and a ground floor of red-brown stone. A "
        "covered bridge with a row of windows runs from it to the right, over a gap at "
        "street level. Behind: a dark office tower with a logo near its top, a red-brick tower, "
        "a pale stone tower and a clock tower. A street lamp, a pole with street signs, "
        "traffic signals, a litter bin, a car on the road at the right and part of another at "
        "the lower right edge. Overcast sky."
    ),
    "p2_closeup": (
        "Colour photograph, portrait, taken from a street corner. A three-storey building: "
        "the corner faced in pale stone panels carrying the lettering, the side wall in grey "
        "concrete with long horizontal bands of windows, and a ground floor of red-brown stone. "
        "Two cars are parked at the kerb at the lower left; a pole carries traffic signals and "
        "road signs; a street lamp stands at the right and a security camera is fixed to the "
        "wall. A dark office tower with a logo stands behind at the upper right. Clear blue sky."
    ),
    "p3_distance": (
        "Colour photograph, portrait, looking up from street level. A tall, narrow building of "
        "about eleven storeys: the end wall a plain pale panelled surface without windows, the "
        "long side a dark grid of narrow windows, and a thin flat roof overhanging the top. "
        "Over the entrance on the dark ground floor, a large grey shield-shaped sign with a "
        "blue seven-pointed star badge. Bare trees at the left; a street lamp, a traffic "
        "signal on an arm and street signs; a low dark building at the left with lettering on "
        "its wall. Blue sky with streaks of white cloud."
    ),
    "p3_closeup": (
        "Colour photograph, landscape, looking up from the paved area in front of the "
        "entrance. A pale panelled tower rises behind a grey ground-floor block. Above the "
        "glass entrance doors, a large grey shield-shaped sign with a blue seven-pointed star "
        "badge; a flat grey rectangle covers the top of the shield. At the left, a low "
        "building clad in polished black panels, with a flat black rectangle on its wall. "
        "Three flagpoles: the United States flag, partly in frame at the top; a white flag "
        "with a red stripe, a red star and a bear (the California state flag); and a yellow "
        "flag with a green emblem. A low hedge, two people near the street, parked vehicles "
        "and other buildings at the right. Clear blue sky; leaves of a tree at the upper "
        "right."
    ),
    "p4_distance": (
        "Colour photograph, landscape, taken from a lawn across a road. A long three-storey "
        "building faced in honey-coloured stone with tall narrow windows, a glazed section at "
        "the left end, a band of windows along the top floor and a thin flat roof projecting "
        "over it. A tall flagpole at the right flies the United States flag; two smaller "
        "flags fly at the left, one of them blue. Young trees along the front, a few people on "
        "the pavement, a red car and a dark car on the road. Mature trees at both edges and a "
        "lower building behind at the left. Clear deep blue sky; green grass in the "
        "foreground."
    ),
    "p4_closeup": (
        "Colour photograph, landscape, from the pavement near the corner. A three-storey "
        "building with a fully glazed corner in blue-green glass, honey-coloured stone walls "
        "with tall narrow windows, and a wide flat roof projecting well beyond the corner. "
        "Lettering runs across the glass above the entrance, and a flat blue-green rectangle "
        "covers its start. A short flight of steps with railings leads to glass doors under a "
        "canopy; a man in dark clothes stands near the foot of the steps. Two flagpoles at "
        "the left fly the United States flag and a light blue flag. A street lamp and young "
        "trees at the right; cars parked along the street at the left. Clear blue sky."
    ),
    "p5_distance": (
        "Colour photograph, landscape, taken across a large paved area. A long, low building "
        "with a curving glass front and a white roof that sweeps out at the left into a large "
        "canopy on slanting white supports. Three flagpoles in front: the United States flag "
        "in the middle, a dark blue flag with a seal, and a green-and-blue flag. Rows of short "
        "posts, a low sign, a polished metal sphere, young and mature trees, and a street lamp "
        "at the right. Hills on the horizon at the left. Clear deep blue sky."
    ),
    "p5_closeup": (
        "Colour photograph, landscape, looking up from a courtyard. A building with a long "
        "curving front of glass under a thin white roof edge, the glass reflecting the blue "
        "sky, meets at the right a section clad in pale stone panels with horizontal strips "
        "of windows and a deep overhanging roof. At the lower left, slanting white supports "
        "carry a canopy; metal café tables and chairs stand around round raised planters with "
        "young trees. Branches of a large tree frame the top left. Clear blue sky."
    ),
    "p6_distance": (
        "Colour photograph, landscape, taken from across a wide road with a yellow centre "
        "line. A long three-storey building with grey panels and large windows, and a light "
        "metal sunshade running the length of the roof on slender posts. Palm trees stand in "
        "a planted strip in front. Lettering on a ground-floor wall at the right, with a flat "
        "grey rectangle covering the wall to its left; large pale letters across some upper "
        "windows. Utility poles and overhead wires, a traffic signal, and parked cars at the "
        "far left. Bright, hazy white sky."
    ),
    "p6_closeup": (
        "Colour photograph, portrait, looking up beside the building. A tall wall of blue "
        "glass panes reflecting clouds, under a slatted metal sunshade carried on slender "
        "posts; at the left, a grey panelled tower with a flat grey rectangle on its face. "
        "Steps with metal handrails lead up to glass entrance doors. In front, a low concrete "
        "wall with raised metal letters along it, and a bed of spiky plants and shrubs above "
        "it. Blue sky with white clouds."
    ),
}


# ---------------------------------------------------------------------------
# The questionnaire, read from the .docx in document order
# ---------------------------------------------------------------------------


def _clean(text: str) -> str:
    """Typography only: the <u> markup, curly quotes, the ellipsis, whitespace."""
    text = re.sub(r"</?u>", "", text)
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("…", "...")
    return re.sub(r"\s+", " ", text).strip()


def paragraphs() -> list[dict[str, Any]]:
    """Q's body, one entry per paragraph: its text, and each picture it embeds as
    (media member, alt text, has-no-crop)."""
    with zipfile.ZipFile(QUEX) as z:
        xml = z.read("word/document.xml").decode("utf-8")
        rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
    target = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="(media/[^"]+)"', rels))
    out: list[dict[str, Any]] = []
    text: list[str] = []
    pics: list[tuple[str, str, bool]] = []
    token = re.compile(
        r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>|(<w:drawing>.*?</w:drawing>)|(</w:p>)", re.S
    )
    for m in token.finditer(xml):
        if m.group(1) is not None:
            text.append(html.unescape(m.group(1)))
        elif m.group(2):
            d = m.group(2)
            rid = re.search(r'r:embed="(rId\d+)"', d)
            if not rid:
                raise SystemExit("a drawing with no embedded picture")
            descr = re.search(r'descr="([^"]*)"', d)
            uncropped = re.findall(r"<a:srcRect[^>]*/>", d) == ["<a:srcRect/>"]
            pics.append(
                (
                    "word/" + target[rid.group(1)],
                    html.unescape(descr.group(1)) if descr else "",
                    uncropped,
                )
            )
        else:
            out.append({"text": "".join(text), "pics": pics})
            text, pics = [], []
    return out


SCREEN = re.compile(r"\[?(HEADLEY\d+A?|Q\d+)\.\]?")


def screens() -> dict[str, list[dict[str, Any]]]:
    """Screen label ("HEADLEY1A", "Q1") -> its paragraphs, up to the next label."""
    out: dict[str, list[dict[str, Any]]] = {}
    current: str | None = None
    for p in paragraphs():
        m = SCREEN.fullmatch(p["text"].strip())
        if m:
            current = m.group(1)
            out[current] = []
            continue
        if current is not None:
            out[current].append(p)
    return out


def _words(paras: list[dict[str, Any]]) -> list[str]:
    """The screen's own words: directives in square brackets dropped, [SPACE] included."""
    out = []
    for p in paras:
        s = _clean(p["text"])
        if not s or re.fullmatch(r"\[[^\]]*\]", s):
            continue
        out.append(s)
    return out


def picture_map(paras: list[dict[str, Any]]) -> dict[int, tuple[str, str]]:
    """P_HEADLEY code -> (media member, alt text) for the [SHOW IF] blocks on one screen.

    Each "[SHOW IF P_HEADLEY=n]" must be followed by exactly one picture before the next
    directive or text."""
    out: dict[int, tuple[str, str]] = {}
    code: int | None = None
    for p in paras:
        m = re.fullmatch(r"\[SHOW IF P_HEADLEY=(\d)\]", p["text"].strip())
        if m:
            code = int(m.group(1))
            if code in out:
                raise SystemExit(f"P_HEADLEY={code} shown twice on one screen")
            continue
        if p["pics"]:
            if code is None or len(p["pics"]) != 1 or code in out:
                raise SystemExit(f"a picture outside a single [SHOW IF] block: {p['pics']}")
            member, alt, uncropped = p["pics"][0]
            if not uncropped:
                raise SystemExit(f"{member} is cropped on the page")
            out[code] = (member, alt)
            code = None
        elif p["text"].strip() and code is not None:
            raise SystemExit(f"[SHOW IF P_HEADLEY={code}] has no picture")
    return out


def _alt_file(alt: str) -> str:
    return alt.replace("\\", "/").rsplit("/", 1)[-1]


def expected_alt(code: int, view: str) -> str:
    """The client's original file name for this arm and view, as the alt text records it
    (the extension varies and is not checked)."""
    kind, k = ("hostile", code) if code <= 3 else ("welcoming", code - 3)
    tail = " closeup" if view == "closeup" else ""
    return f"Image {code} {kind} police building {k}{tail}"


def fielded() -> dict[str, Any]:
    """Everything the recipe quotes, and the picture mapping, from Q."""
    sc = screens()
    pictures = {name: picture_map(sc[name]) for name in [DISTANT_SCREEN, CLOSE_SCREEN]}
    for name, mapping in pictures.items():
        if sorted(mapping) != list(range(1, 7)):
            raise SystemExit(f"{name} shows pictures for {sorted(mapping)}")
        view = VIEWS[name]
        for code, (member, alt) in mapping.items():
            stem = _alt_file(alt).rsplit(".", 1)[0]
            if stem != expected_alt(code, view):
                raise SystemExit(f"{name} P_HEADLEY={code}: {member} alt text is {alt!r}")
    for name in REPEAT_SCREENS:
        if picture_map(sc[name]) != pictures[CLOSE_SCREEN]:
            raise SystemExit(f"{name} does not repeat {CLOSE_SCREEN}'s pictures")
    members = [m for mp in pictures.values() for m, _ in mp.values()]
    if len(set(members)) != 12:
        raise SystemExit("the twelve pictures are not twelve distinct files")

    texts = [_clean(p["text"]) for p in paragraphs()]
    order = [t for t in texts if t.startswith("IF RND_01=") and " SHOW HEADLEY3" in t]
    if order != [
        "IF RND_01=0 SHOW HEADLEY3, Q4, Q5 BEFORE HEADLEY1; Q6 AND Q7 ARE ALWAYS SHOWN LAST",
        "IF RND_01=1 SHOW HEADLEY3, Q4, Q5 AFTER Q3; Q6 AND Q7 ARE ALWAYS SHOWN LAST",
    ]:
        raise SystemExit(f"RND_01 directives changed: {order}")

    h1 = _words(sc["HEADLEY1"])
    h1a = _words(sc[DISTANT_SCREEN])
    h2 = _words(sc[CLOSE_SCREEN])
    q1, q2, q3 = (_words(sc[q]) for q in ("Q1", "Q2", "Q3"))
    return {
        "pictures": {name: {c: m for c, (m, _) in mp.items()} for name, mp in pictures.items()},
        "headley1": h1,
        "headley1a": h1a,
        "headley2": h2,
        "q1": q1,
        "q2": q2,
        "q3": q3,
        "headley3": _words(sc["HEADLEY3"]),
        "q4": _words(sc["Q4"]),
        "q5": _words(sc["Q5"]),
    }


def _between(lines: list[str], start: str, stop: str | None) -> list[str]:
    i = next(n for n, x in enumerate(lines) if x.startswith(start))
    out = []
    for x in lines[i + 1 :]:
        if stop is not None and x.startswith(stop):
            break
        out.append(x)
    return out


def instrument() -> dict[str, Any]:
    """The parsed wording, split into stems, items and options, asserted to shape."""
    q = fielded()
    if len(q["headley1"]) != 2 or len(q["headley1a"]) != 2 or len(q["headley2"]) != 1:
        raise SystemExit(f"vignette screens changed: {q['headley1']} {q['headley1a']}")
    q1, q2, q3 = q["q1"], q["q2"], q["q3"]
    q1_stem = q1[: q1.index("CAWI GRID ITEMS [RANDOMIZE]:")]
    q2_stem = q2[: q2.index("CAWI GRID ITEMS [RANDOMIZE]:")]
    q3_stem = q3[: q3.index("CAWI RESPONSE OPTIONS:")]
    q4, q5 = q["q4"], q["q5"]
    out = {
        "vignette": " ".join(q["headley1"] + q["headley1a"]),
        "headley3": q["headley3"],
        "q4_stem": " ".join(q4[: q4.index("CAWI GRID ITEMS [RANDOMIZE]")]),
        "q4_items": _between(q4, "CAWI GRID ITEMS", "CAWI RESPONSE OPTIONS"),
        "q5": " ".join(q5[: q5.index("CAWI RESPONSE OPTIONS:")]),
        "closer": q["headley2"][0],
        "pictures": q["pictures"],
        "q1_stem": " ".join(q1_stem),
        "q1_items": _between(q1, "CAWI GRID ITEMS", "CAWI RESPONSE OPTIONS"),
        "q1_options": _between(q1, "CAWI RESPONSE OPTIONS", None),
        "q2_stem": " ".join(q2_stem),
        "q2_items": _between(q2, "CAWI GRID ITEMS", "CAWI RESPONSE OPTIONS"),
        "q2_options": _between(q2, "CAWI RESPONSE OPTIONS", None),
        "q3": " ".join(q3_stem),
        "q3_options": _between(q3, "CAWI RESPONSE OPTIONS", None),
    }
    if len(out["headley3"]) != 1:
        raise SystemExit(f"HEADLEY3 changed: {out['headley3']}")
    shapes = {
        "q4_items": 9,
        "q1_items": 9,
        "q1_options": 5,
        "q2_items": 2,
        "q2_options": 5,
        "q3_options": 5,
    }
    for k, n in shapes.items():
        if len(out[k]) != n:
            raise SystemExit(f"{k} has {len(out[k])} entries, expected {n}: {out[k]}")
    return out


def preload_options(var: str) -> list[str]:
    """The bulleted options under a custom preload in Q's preload table."""
    texts = [_clean(p["text"]) for p in paragraphs()]
    i = texts.index(var)
    # var, "No", "No", "Numeric", then the options until the next preload name
    out = []
    for t in texts[i + 4 :]:
        if re.fullmatch(r"P_[A-Z]+", t) or not t:
            break
        out.append(t)
    return out


def codebook_items() -> dict[str, str]:
    """Q1A..Q2B -> the item in the codebook's bracketed label."""
    cb = pd.read_excel(CODEBOOK, sheet_name="Codebook", header=None)
    out = {}
    for _, r in cb.iterrows():
        var = str(r.iloc[0]).strip()
        if var in Q1_VARS + Q2_VARS and var not in out:
            m = re.match(r"\[([^\]]+)\]", str(r.iloc[1]))
            if not m:
                raise SystemExit(f"{var}: codebook label has no [item]")
            out[var] = _clean(m.group(1))
    return out


# ---------------------------------------------------------------------------
# Pictures and catalogue
# ---------------------------------------------------------------------------


def photos() -> dict[str, str]:
    """Image key -> docx media member, for all twelve."""
    pics = instrument()["pictures"]
    return {
        image_key(code, VIEWS[screen]): member
        for screen, mapping in pics.items()
        for code, member in sorted(mapping.items())
    }


def image_file(key: str, member: str) -> str:
    """Path under data/, as the catalogue records it; the docx's own extension."""
    return f"raw/{STUDY}/images/{key}{Path(member).suffix}"


def extract() -> None:
    """--prep: copy each photo out of the questionnaire, byte for byte."""
    IMAGES.mkdir(exist_ok=True)
    with zipfile.ZipFile(QUEX) as z:
        for key, member in photos().items():
            (REPO / "data" / image_file(key, member)).write_bytes(z.read(member))


def catalogue_entries() -> dict[str, dict[str, str]]:
    """This study's entries in data/catalog/images.json, after checking each file is its
    questionnaire picture, byte for byte."""
    from micromotives_datasets.images import sha256_of

    sc = screens()
    alts = {
        image_key(code, VIEWS[name]): _alt_file(alt)
        for name in VIEWS
        for code, (_, alt) in picture_map(sc[name]).items()
    }
    out: dict[str, dict[str, str]] = {}
    with zipfile.ZipFile(QUEX) as z:
        for key, member in photos().items():
            f = image_file(key, member)
            path = REPO / "data" / f
            if path.read_bytes() != z.read(member):
                raise SystemExit(f"{f} is not {member} of the questionnaire")
            code = int(key[1])
            screen = DISTANT_SCREEN if key.endswith("distance") else CLOSE_SCREEN
            shown = (
                f"screen {DISTANT_SCREEN}"
                if screen == DISTANT_SCREEN
                else f"screen {CLOSE_SCREEN} and again above questions Q1, Q2 and Q3"
            )
            out[image_id(key)] = {
                "file": f,
                "sha256": sha256_of(path),
                "source": (
                    "OSF mkgvp, TESS deposit headley1126.zip: embedded in the fielded "
                    f'questionnaire "{QUEX.name}" as {member}, copied byte for byte, under '
                    f'"[SHOW IF P_HEADLEY={code}]" on {shown}; its alt text names the '
                    f'client\'s original file "{alts[key]}". Shown uncropped on the page. '
                    "These are NORC's pasted copies; the fielded files may differ in "
                    "resolution or encoding."
                ),
                "licence": LICENCE,
                "text_in_image": TEXT_IN_IMAGE[key],
                "description": DESCRIPTIONS[key],
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
# Recipe
# ---------------------------------------------------------------------------


def narration(q: dict[str, Any]) -> str:
    """What an RND_01 = 0 respondent was shown and asked before the vignette: the
    instrument's words, quoted, joined by the four phrases declared above."""
    statements = " ".join(f'"{s}"' for s in q["q4_items"])
    return (
        f'{FIRST_SHOWN} "{q["headley3"][0]}" {THEN_ASKED} "{q["q4_stem"]}" {FOR_EACH} '
        f'{statements} {THEN_ASKED} "{q["q5"]}" {AFTER_THAT}'
    )


def arm_text(q: dict[str, Any], rnd: int) -> str:
    body = f"{q['vignette']} <image> {q['closer']} <image>"
    return f"{narration(q)} {body}" if rnd == 0 else body


def _scale(options: list[str]) -> dict[str, Any]:
    n = len(options)
    s: dict[str, Any] = {"min": 1, "max": n, "min_label": options[0], "max_label": options[-1]}
    if n % 2:
        s["mid_label"] = options[n // 2]
    return s


def _labels_match(labels: dict[Any, str], options: list[str]) -> bool:
    return [_clean(labels[k]) for k in range(1, len(options) + 1)] == options


def recipe() -> dict[str, Any]:
    q = instrument()
    ds = read_any(RAW / DATA_FILE)
    labels = ds.value_labels
    df = ds.df

    twin = read_any(RAW / TWIN_FILE).df
    if not df.equals(twin):
        raise SystemExit(f"{TWIN_FILE} differs from {DATA_FILE}")
    if sorted(int(c) for c in df[COND_VAR].dropna().unique()) != list(range(1, 7)):
        raise SystemExit(f"{COND_VAR} codes changed")
    if {int(k): v for k, v in labels[COND_VAR].items()} != P_HEADLEY_LABELS:
        raise SystemExit(f"{COND_VAR} value labels changed: {labels[COND_VAR]}")
    if not df[ID_VAR].is_unique:
        raise SystemExit(f"{ID_VAR} is not unique")

    items = codebook_items()
    if [items[v] for v in Q1_VARS] != q["q1_items"]:
        raise SystemExit("codebook Q1 item order differs from the questionnaire's listing")
    if [items[v] for v in Q2_VARS] != q["q2_items"]:
        raise SystemExit("codebook Q2 item order differs from the questionnaire's listing")
    for var, options in (
        [(v, q["q1_options"]) for v in Q1_VARS]
        + [(v, q["q2_options"]) for v in Q2_VARS]
        + [("Q3", q["q3_options"])]
    ):
        if not _labels_match(labels[var], options):
            raise SystemExit(f"{var}: value labels differ from the questionnaire")
        extra = {int(k): v for k, v in labels[var].items() if int(k) > len(options)}
        if extra != NON_ANSWERS:
            raise SystemExit(f"{var}: non-answer codes changed: {extra}")

    outcomes: list[dict[str, Any]] = []
    for t, (var, item) in enumerate(zip(Q1_VARS, q["q1_items"], strict=True)):
        outcomes.append(
            {
                "var": var,
                "task_num": t,
                "question": f"{q['q1_stem']} {item}",
                "scale": _scale(q["q1_options"]),
                "response_recode": {i: i for i in range(1, 6)},
            }
        )
    for t, (var, item) in enumerate(zip(Q2_VARS, q["q2_items"], strict=True), start=9):
        outcomes.append(
            {
                "var": var,
                "task_num": t,
                "question": f"{q['q2_stem']} {item}",
                "scale": _scale(q["q2_options"]),
                "response_recode": {i: i for i in range(1, 6)},
            }
        )
    outcomes.append(
        {
            "var": "Q3",
            "task_num": 11,
            "question": q["q3"],
            "scale": _scale(q["q3_options"]),
            "response_recode": {i: i for i in range(1, 6)},
        }
    )

    if sorted(int(c) for c in df[ORDER_VAR].dropna().unique()) != [0, 1]:
        raise SystemExit(f"{ORDER_VAR} codes changed")
    doc = re.sub(r"\s+", " ", __doc__ or "")
    for ours in (FIRST_SHOWN, THEN_ASKED, FOR_EACH, AFTER_THAT):
        if f'"{ours}"' not in doc:
            raise SystemExit(f"notes do not record our words {ours!r}")

    arms: list[dict[str, Any]] = []
    for rnd in (0, 1):
        for code in range(1, 7):
            design, building = P_HEADLEY_LABELS[code].rsplit(" ", 1)
            arms.append(
                {
                    "raw_values": {COND_VAR: code, ORDER_VAR: rnd},
                    "condition_num": 6 * rnd + code - 1,
                    "factors": {
                        "design": design.lower(),
                        "building": building,
                        "order": ORDER_LEVELS[rnd],
                    },
                    "text": arm_text(q, rnd),
                    "images": [
                        image_id(image_key(code, "distance")),
                        image_id(image_key(code, "closeup")),
                    ],
                }
            )

    relig = preload_options("P_RELIG")
    ideo = preload_options("P_IDEO")
    if not relig[0].startswith("Protestant (") or ideo[1] != "Liberal":
        raise SystemExit(f"preload table changed: {relig[0]!r} {ideo[1]!r}")
    if labels["P_IDEO"][2] != "Libreal" or not labels["P_RELIG"][1].endswith("Pent"):
        raise SystemExit("the .dta labels being restored have changed; re-read them")

    return {
        "study_id": STUDY,
        "source": "tess",
        "title": "Affective Architecture: a burglary to report in person, then one of six police "
        "buildings, seen from a distance and close up; feelings on approaching it, trust in the "
        "officers inside, and likelihood of going in",
        "data_file": DATA_FILE,
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": ID_VAR,
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_vars": [COND_VAR, ORDER_VAR],
            "factors": ["design", "building", "order"],
            "arms": arms,
        },
        "outcomes": outcomes,
        "response_recode": {},
        "missing_codes": [],
        "persona_map": {
            "age": "AGE",
            "gender": "GENDER",
            "education": "EDUC",
            "ethnicity": "RACETHNICITY",
            "income": "INCOME",
            "marital_status": "MARITAL",
            "employment": "EMPLOY",
            "region": "REGION4",
            "household_size": "HHSIZE",
            "housing_type": "HOME_TYPE",
            "housing_ownership": "HOUSING",
            "urban_rural": "METRO",
            "internet_access": "INTERNET",
            "phone_service": "PHONESERVICE",
            "party_id": "P_PARTYID7",
            "ideology": "P_IDEO",
            "religion": "P_RELIG",
            "religious_attendance": "P_ATTEND",
        },
        "persona_label_rewrite": {"P_RELIG": {1: relig[0]}, "P_IDEO": {2: ideo[1]}},
        "persona_missing": {"GENDER": [0]},
    }


def render() -> str:
    return yaml.safe_dump(recipe(), sort_keys=False, allow_unicode=True, width=100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--prep", action="store_true", help="copy the photos out of the .docx")
    ap.add_argument("--catalogue", action="store_true", help="add this study's images.json entries")
    args = ap.parse_args()
    if args.prep:
        extract()
        print(f"wrote {len(photos())} photos to {IMAGES.relative_to(REPO)}/")
        return 0
    if args.catalogue:
        write_catalogue()
        print("updated data/catalog/images.json (mkgvp entries only)")
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
