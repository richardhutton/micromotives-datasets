#!/usr/bin/env python3
"""Write recipes/images/rhfd6.yaml: safer gambling adverts and stigma (IMG55).

Palmer, Weiss-Cohen, Torrance & Newall (Bristol), "When 'help' might hurt: Do safer
gambling advertisements reduce or contribute to gambling stigma?", OSF Preprints
h8vxz v1 (10 March 2025), https://osf.io/preprints/osf/h8vxz_v1. OSF project rhfd6
("Gambling advertising & stigma"): the Qualtrics survey (Materials/Materials.qsf),
a Word copy of it and the debrief, the data (Data/stigma_data.csv), the authors'
analysis (Analyses and Results/Stigma.Rmd, knitted to Stigma.html on 24 September
2025) and the five advert pictures (Adverts/). Preregistration: OSF pjb98 (5 Feb
2025). The project states no licence; the registration lists GPL 3.0.

500 UK adults who gamble (Prolific, February 2025; screened to have reported at least
one non-lottery, non-bingo gambling format) each rated five real safer-gambling
adverts, shown one per page in random order, on three statements about people who
gamble heavily (1-7 agreement). In a separate block, before or after the adverts
(counterbalanced), they answered the nine-item Problem Gambling Severity Index.

Every judgement is here, in code, so the recipe can be re-derived and reviewed:

* DESIGN. Within person: everyone saw all five adverts, so one row per person per
  advert per statement, and the coded file is LONG (`pid`, `advert`). Five arms, one
  per advert; condition_num follows the .qsf flow's order: Sky Bet's deposit-limit
  advert 0, GambleAware's stigma-reduction advert 1, GambleAware's Bet Regret
  advert 2, the Odds Are: They Win advert 3, Racing TV's bet-responsibly advert 4.
  A person's five rows of one statement are five different conditions (QC rule 24).
* WHICH COLUMNS ARE WHICH ADVERT. The .qsf names its blocks "sky bet", "Stigma
  reduction", "Bet regret", "Odds are..." and "Gambling operator"; the data name the
  same answers DepositLimit_*, StigmaCampaign_*, ChasingLosses_*, OddsAre_* and
  BetResponsibly_*, and the authors' script and the preprint's Table 1 tie each name
  to its advert's words. The pictures settle it independently: each block's
  Qualtrics graphic, fetched from the survey's own graphic URL, is byte-identical
  (sha256) to the OSF file of that name (checked in --catalogue).
* PICTURES. The five OSF files, unaltered. They are the graphics each block's rating
  grid displayed as its question text. Each page showed its advert a second time
  below the grid, above the comment box (a display item; the block's fixed order is
  grid, picture, comment): for four adverts the same graphic, for Racing TV a larger
  copy of the same advert (Qualtrics IM_bDYh50Trh3fCbhc, 634x354 against 399x222;
  same layout and words), which OSF does not hold and which is not catalogued. Two
  OSF files named .jpeg are PNGs (Deposit_limit, Stigma_reduction, Chasing_Losses);
  kept as published.
* WORDS IN THE PICTURES (text_in_image). Every word printed on the advert, in
  reading order; " / " separates blocks and line wraps inside a block are joined
  with a space; curly quotes and apostrophes are straightened. Left out and
  described instead: the words on the phone screen in the Racing TV photograph
  (part of a photograph and mostly too small to read) and the registered-trademark
  marks. Odds Are's chip carries "FIXED" in its centre and five words round its rim,
  listed clockwise from the upper left.
* CONDITION. shared_context is the page before the adverts (block "Message intro"),
  word-for-word: "You will now be presented with various safer gambling adverts.
  Please rate each message using the scales provided." Each arm is then the advert:
  words that are OURS, "One of the adverts:", then its words in quotation marks (the
  stigma-reduction advert's words are already a quotation, so none are added) and
  the <image> marker. The order each person saw the adverts in IS recorded
  (`Block_Order`) but no row says where its advert sat, and nothing is said of the
  other four (docs/CONVENTIONS.md, sequence signposting); the authors found no order
  effect. Nor does a row say whether the person answered the PGSI before the adverts
  (`counterbalance` 0, 250 of the 498 built) or after them (1, 248).
* OUTCOMES. Three per advert, the rating grid's three statements word-for-word from
  the .qsf (HTML stripped; the five blocks' copies are identical, checked), in the
  .qsf's listing order: fault, will-power, worse. The grid has no stem (its question
  text is the advert), so the statement is the whole question. Statement order was
  randomised per person (the `*_Order` columns record it); each statement is its own
  row. Answers 1..7: Strongly disagree, Disagree, Somewhat disagree, Neither agree
  nor disagree, Somewhat agree, Agree, Strongly agree (.qsf answer ids, the data's
  codes; forced response, no missing answers).
* NOT BUILT. The optional comment box under each advert (free text), the closing
  feedback box, the Prolific ID, the carelessness check (a check, not an outcome),
  and the PGSI (asked once, before or after all five adverts, so it has no single
  advert for a condition; mapped as persona instead, below).
* WHO. 498 of the 500 people: the two who answered the carelessness check "No, I
  was not paying attention, discard my data" (`Honesty` 1) asked for their data to
  be discarded, and the authors' preregistered exclusion does the same; --prep
  asserts there are exactly two. `pid` is the 1-based row in stigma_data.csv.
* PERSONA. Prolific's own records, stable facts collected before the study: age,
  sex, ethnicity (`Ethnicity simplified`, crosswalk scheme uk_ons_five_group_short),
  employment (scheme uk_prolific_rhfd6, added to data/catalog/
  persona_crosswalk_employment.json), student status, country of birth,
  nationality, and the online gambling games the person reported playing (Prolific
  screener, comma-separated as exported). Then the nine PGSI items with their
  answers word-for-word (Never / Sometimes / Most of the time / Almost always; .qsf
  recode 0-3, the data's codes): they report the person's own gambling over the
  previous 12 months, a behavioural history rather than a reaction, and they are the
  authors' preregistered moderator. Half answered them after the adverts; the
  authors tested whether that order moved PGSI totals and found it did not (their
  negative-binomial model; our crosscheck repeats the comparison of means). The
  PGSI total is not mapped: no respondent gave it, it is our sum. Left absent: sex
  and ethnicity "Prefer not to say" (1 each), employment "DATA_EXPIRED" (49) and
  student status "DATA_EXPIRED" (43). Prolific's "Not in paid work (e.g.
  homemaker', 'retired or disabled)" has two stray quote marks from the export; they
  are typography and removed. Not mapped: country of residence (UK for everyone),
  `Language` (the export does not say whether it is first or fluent language).
* UK FIT. A UK sample rating UK adverts (Sky Bet, Racing TV, GambleAware, Greater
  Manchester's Odds Are campaign); British spelling throughout.
* NOT ASKED OF JEV. Assignment, persona and non-answer codes are settled by the .qsf
  flow, Prolific's export labels and existing crosswalk precedents; no paid call.

    uv run python scripts/gen_rhfd6.py --prep       # (re)write the coded long .xlsx
    uv run python scripts/gen_rhfd6.py --catalogue  # (re)write this study's images.json entries
    uv run python scripts/gen_rhfd6.py              # write the recipe
    uv run python scripts/gen_rhfd6.py --check      # exit 1 if it differs
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from micromotives_datasets.sources import read_any  # noqa: E402

STUDY = "rhfd6"
RAW = REPO / "data" / "raw" / STUDY
RAW_CSV = RAW / "Data" / "stigma_data.csv"
QSF = RAW / "Materials" / "Materials.qsf"
GRAPHICS = RAW / "qualtrics_graphics"
DATA_FILE = "rhfd6_coded.xlsx"
DATA = RAW / DATA_FILE
RECIPE = REPO / "recipes" / "images" / f"{STUDY}.yaml"
LICENCE = (
    "No licence stated on OSF project rhfd6; its registration pjb98 lists GNU GPL 3.0. "
    "Used with rich's ruling of 2 Nov 2026."
)

ID_VAR = "pid"
ADVERT_VAR = "advert"
HONESTY_DISCARD = 1
EXPECTED_DISCARDED = 2

# The five adverts in the .qsf flow's order:
# (key, data prefix, .qsf block, Qualtrics graphic of the grid, OSF file, factor level)
ADVERTS: list[tuple[str, str, str, str, str, str]] = [
    (
        "deposit_limit",
        "DepositLimit",
        "sky bet",
        "IM_06cbPcW6WftphDo",
        "Deposit_limit.jpeg",
        "Sky Bet: deposit limit",
    ),
    (
        "stigma_reduction",
        "StigmaCampaign",
        "Stigma reduction",
        "IM_7TIeugHzfAN9YZU",
        "Stigma_reduction.jpeg",
        "GambleAware: stigma reduction",
    ),
    (
        "bet_regret",
        "ChasingLosses",
        "Bet regret",
        "IM_bdBtrxyekHbiJVQ",
        "Chasing_Losses.jpeg",
        "GambleAware: Bet Regret",
    ),
    (
        "odds_are",
        "OddsAre",
        "Odds are...",
        "IM_0ldhwgg6ndS8nAy",
        "Odds_are.jpeg",
        "Odds Are: They Win",
    ),
    (
        "bet_responsibly",
        "BetResponsibly",
        "Gambling operator",
        "IM_bqJ7VVUx19Zba50",
        "Bet_responsibly.jpeg",
        "Racing TV: bet responsibly",
    ),
]
RACING_TV_LARGE_COPY = "IM_bDYh50Trh3fCbhc"

WORDS: dict[str, list[str]] = {
    "deposit_limit": ["JOIN THE HALF MILLION CUSTOMERS WHO HAVE SET A DEPOSIT LIMIT."],
    "stigma_reduction": [
        "\"It started to feel like I couldn't escape gambling ads",
        'so I got help"',
    ],
    "bet_regret": [
        "DID YOU ACTUALLY BELIEVE YOU WOULD WIN YOUR MONEY BACK BY CHASING YOUR LOSSES?",
        "THINK TWICE OR YOU'LL BET REGRET IT",
        "BeGambleAware.org",
    ],
    "odds_are": [
        "FIXED",
        "DICE",
        "POKER",
        "BLACKJACK",
        "SLOTS",
        "ROULETTE",
        "THE MAIN PURPOSE OF GAMBLING COMPANIES IS TO MAXIMISE PROFIT, GENERATED THROUGH "
        "CUSTOMER LOSSES.",
        "GAMBLING COMPANIES",
        "ODDS ARE THEY WIN",
        "#ODDSARETHEYWIN",
    ],
    "bet_responsibly": [
        "PLEASE BET RESPONSIBLY",
        "- Take time to think",
        "- Use safer gambling tools to stay in control",
        "Racing TV",
        "TAKE TIME TO THINK",
        "taketimetothink.co.uk",
        "BeGambleAware.org",
        "18+",
    ],
}

# Visible facts only: no inferred emotion, age, appraisal or ethnicity.
DESCRIPTIONS: dict[str, str] = {
    "deposit_limit": (
        "A wide banner, landscape, on a white background. A deep blue panel carries a faint "
        "repeated pattern of a small symbol, a cross above a curved line. In the centre a man "
        "with short grey hair, in a blue suit and an open-necked white shirt, stands with his "
        "arms folded, facing the viewer; his head rises above the top of the panel. Large white "
        "capital letters run across the panel and across him, the middle word much the "
        'largest; "MERS WHO" is drawn in outline only where it crosses his body, and the final '
        "full stop is red. No logo or other text is shown."
    ),
    "stigma_reduction": (
        "A tall portrait poster with an orange background shading to yellow at the foot, "
        "lightly speckled. Two stylised black eyes with white irises look down from the top "
        "edge and two look up from the bottom edge, cut off by the frame. Between them, in "
        "large black condensed letters, a quotation in quotation marks, its last line smaller "
        "and set apart. No logo or other text is shown."
    ),
    "bet_regret": (
        "A portrait poster on an orange background, set on a white margin. Large black "
        "capital letters ask a question; the last words, from MONEY on, tilt and tumble down "
        "the right side, the letters of LOSSES? falling one below another. Below sits a small "
        "square black-and-white photograph of a man with short dark hair, one hand raised to "
        "the side of his head, holding a mobile phone. At the foot a line of black capitals in which BET "
        "REGRET sits in a black box, BET in white on black and REGRET in white italic, and "
        "beneath it a small BeGambleAware.org logo. The picture is small, so its smallest "
        "text is soft."
    ),
    "odds_are": (
        "A square graphic on a black background patterned with faint diamonds and card-suit "
        "symbols. At the top a red-and-gold casino chip, its black centre showing FIXED in "
        "large gold capitals and five game names in white round its rim. Below, white capital "
        "letters state the main message. Under that two red labels with pointed ends sit side "
        "by side, each with white capitals, and at the foot a hashtag in white."
    ),
    "bet_responsibly": (
        "A small landscape banner. On the left, on a grey background, large white capitals "
        "with two lines in yellow below them, each starting with a dash, and the Racing TV "
        "logo in white. On the right a hand holds a smartphone showing a horse-racing app "
        "with race times, runners and small coloured logos, its words "
        "too small to read. Across the foot a yellow strip with a black pause-button symbol, "
        "TAKE TIME TO THINK and a small web address on the left, and the BeGambleAware.org "
        "logo with a black 18+ badge on the right."
    ),
}

INTRO_BLOCK = "Message intro"
LEAD = "One of the adverts:"


def advert_words(key: str) -> str:
    return " / ".join(WORDS[key])


def image_id(key: str) -> str:
    return f"rhfd6_{key}"


def image_file(osf_name: str) -> str:
    """Path under data/, as the catalogue records it."""
    return f"raw/{STUDY}/Adverts/{osf_name}"


# ---------------------------------------------------------------------------
# The .qsf
# ---------------------------------------------------------------------------


def _text(raw: str) -> str:
    """HTML to plain text. Typography only; words untouched."""
    raw = re.sub(r"<br\s*/?>|</p>|</div>", " ", raw)
    raw = re.sub(r"<[^>]+>", "", raw)
    raw = html.unescape(raw).replace("\xa0", " ")
    raw = raw.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", raw).strip()


def qsf() -> dict[str, Any]:
    out: dict[str, Any] = json.loads(QSF.read_text(encoding="utf-8-sig"))
    return out


def blocks(d: dict[str, Any] | None = None) -> dict[str, list[dict[str, Any]]]:
    """Live block description -> its questions' payloads, in block order. Trash skipped."""
    d = qsf() if d is None else d
    qs = {
        e["Payload"]["QuestionID"]: e["Payload"]
        for e in d["SurveyElements"]
        if e["Element"] == "SQ"
    }
    bl = next(e["Payload"] for e in d["SurveyElements"] if e["Element"] == "BL")
    bl = bl.values() if isinstance(bl, dict) else bl
    out: dict[str, list[dict[str, Any]]] = {}
    for b in bl:
        if b["Type"] == "Trash":
            continue
        out[b["Description"].strip()] = [
            qs[x["QuestionID"]] for x in b.get("BlockElements", []) if x["Type"] == "Question"
        ]
    return out


def graphics_in(payload: dict[str, Any]) -> list[str]:
    return re.findall(r"IM=(IM_\w+)", payload.get("QuestionText", ""))


def grid(block: str) -> dict[str, Any]:
    """The block's rating grid (the one Matrix question)."""
    (g,) = [p for p in blocks()[block] if p["QuestionType"] == "Matrix"]
    return g


def statements(block: str) -> list[str]:
    """The grid's statements, in the .qsf's listing order (ChoiceOrder)."""
    g = grid(block)
    return [_text(g["Choices"][str(c)]["Display"]) for c in g["ChoiceOrder"]]


def answers(block: str) -> list[str]:
    g = grid(block)
    return [_text(g["Answers"][str(a)]["Display"]) for a in g["AnswerOrder"]]


def shared_context() -> str:
    (intro,) = blocks()[INTRO_BLOCK]
    return _text(intro["QuestionText"])


def pgsi() -> tuple[list[str], list[str], dict[str, str]]:
    """(the nine items, the answer labels, recode answer id -> stored code)."""
    (p,) = blocks()["PGSI"]
    items = [_text(p["Choices"][str(c)]["Display"]) for c in p["ChoiceOrder"]]
    labels = [_text(p["Answers"][k]["Display"]) for k in sorted(p["Answers"], key=int)]
    return items, labels, p["RecodeValues"]


# ---------------------------------------------------------------------------
# Outcomes
# ---------------------------------------------------------------------------

# (coded column, data suffix); the order is the grid's listing order, checked in recipe().
OUTCOME_COLS = [("FAULT", "Fault"), ("WILLPOWER", "Willpower"), ("WORSE", "Worse")]
OUTCOME_KEYWORD = {"FAULT": "at fault", "WILLPOWER": "will-power", "WORSE": "worse than"}

# ---------------------------------------------------------------------------
# Persona
# ---------------------------------------------------------------------------

PERSONA_BASE = {
    "age": "Age",
    "sex": "Sex",
    "ethnicity": "Ethnicity simplified",
    "employment": "Employment status",
    "student_status": "Student status",
    "country_of_birth": "Country of birth",
    "nationality": "Nationality",
    "online_gambling_games_played": "Online gambling games",
}
PREFER_NOT = "Prefer not to say"
EXPIRED = "DATA_EXPIRED"
PGSI_STEM_KEY = "in_the_previous_12_months"


def _key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def pgsi_persona() -> dict[str, str]:
    items, _, _ = pgsi()
    return {f"{PGSI_STEM_KEY}_{_key(t)}": f"PGSI_{i}" for i, t in enumerate(items, start=1)}


def _label(v: Any) -> Any:
    """Typography only: trim, and the export's stray quote marks. Words untouched."""
    if not isinstance(v, str):
        return v
    return v.replace("homemaker', 'retired", "homemaker, retired").strip()


def prep() -> pd.DataFrame:
    """The coded long spreadsheet: one row per person per advert."""
    wide = pd.read_csv(RAW_CSV, low_memory=False)
    wide.insert(0, ID_VAR, range(1, len(wide) + 1))
    discarded = int((wide["Honesty"] == HONESTY_DISCARD).sum())
    if discarded != EXPECTED_DISCARDED:
        raise SystemExit(f"{discarded} asked to discard their data, expected {EXPECTED_DISCARDED}")
    wide = wide[wide["Honesty"] != HONESTY_DISCARD]
    _, pgsi_labels, recode = pgsi()
    pgsi_label = {int(code): pgsi_labels[int(aid) - 1] for aid, code in recode.items()}
    expected_order = {a[1] for a in ADVERTS}
    rows = []
    for _, r in wide.iterrows():
        if set(str(r["Block_Order"]).split(",")) != expected_order:
            raise SystemExit(f"pid {r[ID_VAR]}: did not see all five adverts")
        for k, (_, prefix, *_rest) in enumerate(ADVERTS):
            out: dict[str, Any] = {ID_VAR: r[ID_VAR], ADVERT_VAR: k + 1}
            for col, suffix in OUTCOME_COLS:
                value = r[f"{prefix}_{suffix}"]
                if pd.isna(value) or int(value) not in range(1, 8):
                    raise SystemExit(f"pid {r[ID_VAR]} {prefix}_{suffix}: {value!r}")
                out[col] = int(value)
            for var in PERSONA_BASE.values():
                out[var] = _label(r[var])
            for var in pgsi_persona().values():
                out[var] = pgsi_label[int(r[var])]
            rows.append(out)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------


def catalogue_entries() -> dict[str, dict[str, str]]:
    """This study's entries in data/catalog/images.json, after checking each OSF file
    is the graphic its block displayed."""
    from micromotives_datasets.images import sha256_of

    out: dict[str, dict[str, str]] = {}
    for key, _, block, graphic, osf_name, _ in ADVERTS:
        if graphics_in(grid(block)) != [graphic]:
            raise SystemExit(f"{block}: grid shows {graphics_in(grid(block))}, expected {graphic}")
        f = image_file(osf_name)
        sha = sha256_of(REPO / "data" / f)
        if (GRAPHICS / graphic).exists() and sha256_of(GRAPHICS / graphic) != sha:
            raise SystemExit(f"{osf_name} is not Qualtrics graphic {graphic}")
        out[image_id(key)] = {
            "file": f,
            "sha256": sha,
            "source": f"https://osf.io/rhfd6/ (osfstorage, Adverts/{osf_name}); byte-identical "
            f'to Qualtrics graphic {graphic}, which the .qsf\'s "{block}" block shows as its '
            "rating grid's question text (Materials/Materials.qsf)",
            "licence": LICENCE + " The advert is a third-party campaign creative whose own "
            "terms the deposit does not state.",
            "text_in_image": advert_words(key),
            "description": DESCRIPTIONS[key],
        }
    return out


def write_catalogue() -> None:
    """Add or refresh only this study's entries; re-read first, others are editing too."""
    path = REPO / "data" / "catalog" / "images.json"
    current = json.loads(path.read_text())
    current.update(catalogue_entries())
    path.write_text(json.dumps(current, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Recipe
# ---------------------------------------------------------------------------


def arm_text(key: str) -> str:
    """The advert's words in quotation marks, unless they carry their own (stigma reduction)."""
    words = advert_words(key)
    quoted = words if words.startswith('"') and words.endswith('"') else f'"{words}"'
    return f"{LEAD} {quoted} <image>"


def recipe() -> dict[str, Any]:
    ds = read_any(DATA)
    labels = ds.value_labels
    if set(ds.df[ADVERT_VAR].unique()) != set(range(1, len(ADVERTS) + 1)):
        raise SystemExit(f"advert codes changed: {sorted(ds.df[ADVERT_VAR].unique())}")

    wording = [statements(a[2]) for a in ADVERTS]
    scales = [answers(a[2]) for a in ADVERTS]
    if any(w != wording[0] for w in wording) or any(s != scales[0] for s in scales):
        raise SystemExit("the five grids' statements or answers differ")
    options = scales[0]
    if len(options) != 7:
        raise SystemExit(f"expected a 7-point grid, got {options}")
    outcomes = []
    for t, ((col, _), question) in enumerate(zip(OUTCOME_COLS, wording[0], strict=True)):
        if OUTCOME_KEYWORD[col] not in question:
            raise SystemExit(f"{col}: listing order changed ({question!r})")
        if col in labels:
            raise SystemExit(f"{col}: not coded by --prep")
        outcomes.append(
            {
                "var": col,
                "task_num": t,
                "question": question,
                "scale": {
                    "min": 1,
                    "max": 7,
                    "min_label": options[0],
                    "max_label": options[-1],
                    "mid_label": options[3],
                },
                "response_recode": {i: i for i in range(1, 8)},
            }
        )

    arms = [
        {
            "raw": k + 1,
            "condition_num": k,
            "factors": {"advert": level},
            "text": arm_text(key),
            "images": [image_id(key)],
        }
        for k, (key, _, _, _, _, level) in enumerate(ADVERTS)
    ]

    def code_of(var: str, label: str) -> int:
        return next(int(k) for k, v in labels[var].items() if v == label)

    return {
        "study_id": STUDY,
        "source": "osf",
        "title": "Safer gambling adverts and stigma: five real UK adverts, each rated by every "
        "person on three statements about people who gamble heavily",
        "data_file": DATA_FILE,
        "licence": LICENCE,
        "comparable_to_socsci210": False,
        "participant_id_var": ID_VAR,
        "notes": (__doc__ or "").strip(),
        "condition": {
            "source_var": ADVERT_VAR,
            "shared_context": shared_context(),
            "factors": ["advert"],
            "arms": arms,
        },
        "outcomes": outcomes,
        "response_recode": {},
        "missing_codes": [],
        "persona_map": {**PERSONA_BASE, **pgsi_persona()},
        "persona_missing": {
            "Sex": [code_of("Sex", PREFER_NOT)],
            "Ethnicity simplified": [code_of("Ethnicity simplified", PREFER_NOT)],
            "Employment status": [code_of("Employment status", EXPIRED)],
            "Student status": [code_of("Student status", EXPIRED)],
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
        print("updated data/catalog/images.json (rhfd6 entries only)")
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
