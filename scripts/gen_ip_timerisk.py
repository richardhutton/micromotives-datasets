#!/usr/bin/env python3
"""Derive the data files AND write the recipes for IP 9.13 — time and risk choices.

Waves 6 (2013) and 7 (2014). An Associated Study: one adult per selected
household answered 72 choices between sums of money at different times, then 19
choices between lotteries, told beforehand that one in ten would be paid for real
on one randomly drawn answer (up to £250). Everyone saw the same preamble and the
same 91 choices; the only randomisation, who was paid, came after the answers.
So this is ONE condition, not an experiment — built on rich's ruling, 9 Oct 2026,
because the choices are real incentivised behaviour.

Unlike the other Innovation Panel builds, the recipes are GENERATED here, from the
questionnaire PDFs, so they can be regenerated rather than retyped: 91 items and two
mode-dependent preambles are too many strings to transcribe by hand. Every string
written is asserted to occur in the extracted questionnaire text.

Decisions the recipe notes record:
- "Choice 01" ... "Choice 91" and choice 91's "In this last choice, " are dropped
  (docs/CONVENTIONS.md, "Sequence signposting").
- The preambles' face-to-face and web sentences are resolved per row on `indmode`.
  The lottery preamble's `{if WEB}` follows two sentences; both are treated as
  web-only (an interpretation: face-to-face decliners got the separate Riskpreb
  screen, which repeats the second).
- Riskpreb — a second appeal shown only to face-to-face respondents who declined the
  lotteries — is in the condition of those who saw it and continued (`riskpreb` = 1),
  resolved per row.

    uv run python scripts/gen_ip_timerisk.py --write --recipes
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

from micromotives_datasets.sources import spss

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[1]
STATA = REPO / "data" / "raw" / "ukds_6849" / "stata" / "stata13_se"
PDF = REPO / "data" / "raw" / "ukds_6849" / "mrdoc" / "pdf"
OUT = REPO / "data" / "raw" / "ukds_6849"
WAVES = {"f": (6, 2013), "g": (7, 2014)}
CHOICES = range(1, 92)
TIME = range(1, 73)

PERSONA = (
    "dvage",
    "sex",
    "gor_dv",
    "jbstat",
    "hiqual_dv",
    "mastat_dv",
    "racel_dv",
    "nchild_dv",
)


def person_hash(pidp: int) -> str:
    """Same construction as `scripts/build_profiles.py`. Never the raw `pidp`."""
    return "ip_" + hashlib.sha256(f"ukds6849:{pidp}".encode()).hexdigest()[:12]


def derived_name(wave: int) -> str:
    return f"timerisk_w{wave}-derived.sav"


# --- data ------------------------------------------------------------------


def derive(w: str) -> tuple[pd.DataFrame, dict[str, dict[float, str]]]:
    wave, year = WAVES[w]
    r = spss.read(STATA / f"{w}_indresp_ip.dta")
    df = r.df
    out = pd.DataFrame({"person": [person_hash(int(p)) for p in df["pidp"]]})
    # One condition: everyone who chose to begin the questions.
    out["took_part"] = np.where(df[f"{w}_trpre"] == 1, 1.0, -8.0)
    out["indmode"] = df[f"{w}_indmode"].to_numpy()
    out["riskpreb"] = df[f"{w}_riskpreb"].to_numpy()
    for i in CHOICES:
        out[f"choice{i:02d}"] = df[f"{w}_choice{i:02d}"].to_numpy()
    for v in PERSONA:
        out[v] = df[f"{w}_{v}"].to_numpy()
    out["wave"] = wave
    out["year"] = year
    labels: dict[str, dict[float, str]] = {}
    for v in PERSONA:
        got = r.value_labels.get(f"{w}_{v}")
        if got:
            labels[v] = dict(got)
    return out, labels


def check(w: str) -> int:
    """Answers from someone who did not begin the questions. Must be 0."""
    d, _ = derive(w)
    answered = (d[[f"choice{i:02d}" for i in CHOICES]] > 0).any(axis=1)
    stray = int((answered & (d["took_part"] != 1)).sum())
    print(f"  wave {WAVES[w][0]}: {int(answered.sum())} answering, {stray} without TRPre = 1")
    return stray


# --- questionnaire text ----------------------------------------------------


def _text(wave: int) -> str:
    raw = subprocess.run(
        ["pdftotext", str(PDF / f"6849_ip_wave_{wave}_questionnaires.pdf"), "-"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return re.sub(r"\n[^\n]*(?:of 6\d\d|Ip0\d\.|http|\d\d/\d\d/\d{4})[^\n]*", "\n", raw)


def _items(t: str) -> dict:
    out: dict = {}
    for m in re.finditer(r"\nChoice(\d\d)\.\n(.*?)\nUse\n", t, re.S):
        body = m.group(2)
        txt = re.search(r"\nText\n(.*?)\nOptions\n", body, re.S)
        opts = re.search(r"\nOptions\n(.*?)(?:\nMixed Mode|\Z)", body, re.S)
        assert txt and opts, m.group(1)
        lines = [ln.strip() for ln in txt.group(1).split("\n") if ln.strip()]
        olines = [ln.strip() for ln in opts.group(1).split("\n") if ln.strip()]
        assert lines[0] == f"Choice {m.group(1)}", lines[0]
        question = " ".join(lines[1:])
        # Option lines are a code, then its label, which may wrap over several lines.
        labels: list[str] = []
        for ln in olines:
            if ln == str(len(labels) + 1):
                labels.append("")
            else:
                assert labels, f"option text before any code in choice {m.group(1)}"
                labels[-1] = f"{labels[-1]} {ln}".strip()
        assert len(labels) in (2, 6) and all(labels), (m.group(1), labels)
        out[int(m.group(1))] = {"question": question, "options": labels}
    for name in ("Trpre", "Riskpre", "Riskpreb"):
        m = re.search(rf"\n{name}\.\n.*?\nText\n(.*?)\nOptions\n", t, re.S)
        assert m, name
        out[name] = " ".join(m.group(1).split())
    return out


def _split_modes(text: str, capi: list[str], web: list[str]) -> tuple[str, str]:
    """Remove the fill markers and return (face-to-face text, web text).

    `capi` and `web` are the sentences that carry a mode marker; each must occur in
    the source, and the rest of the text is common to both modes.
    """
    plain = re.sub(r"\s*\{if (?:CAPI|WEB)\}\s*(?:/\s*)?", " ", text).strip()
    for s in capi + web:
        assert s in plain, s
    capi_text, web_text = plain, plain
    for s in web:
        capi_text = capi_text.replace(s, "")
    for s in capi:
        web_text = web_text.replace(s, "")
    return " ".join(capi_text.split()), " ".join(web_text.split())


def _by_mode(capi: str, web: str) -> str:
    if capi == web:
        return capi
    for bad in "[];":
        assert bad not in capi + web, bad
    return f"[IF indmode=1 INSERT: {capi}; IF indmode=3 INSERT: {web}]"


def write_recipes() -> None:
    texts = {w: _text(wave) for w, (wave, _) in WAVES.items()}
    items = {w: _items(t) for w, t in texts.items()}
    assert all(items["f"][i] == items["g"][i] for i in CHOICES), "choices differ by wave"
    base = (REPO / "recipes" / "ukds_6849_identity_w2.yaml").read_text()
    lic = base.split("data_file:")[1].split("\n", 1)[1].split("comparable_to_socsci210")[0]
    persona = base.split("missing_codes:")[1]
    for w, (wave, _) in WAVES.items():
        it = items[w]
        trpre = _by_mode(
            *_split_modes(
                it["Trpre"],
                capi=[
                    "To do this, we have a set of very brief questions for you to complete "
                    "yourself on the laptop.",
                    "If you have any questions, you can ask me now.",
                ],
                web=["To do this, we will ask you a set of very brief questions."],
            )
        )
        riskpre = _by_mode(
            *_split_modes(
                it["Riskpre"],
                capi=["If you have any questions, you can ask your interviewer now."],
                web=[
                    "You must complete all 91 items in order to have a chance to win. "
                    "Unfortunately if you do not continue then you will not have a chance "
                    "to receive any money."
                ],
            )
        )
        # The appeal's last sentence is an interface instruction ("... enter 1 or else
        # just return the laptop ..."; wave 7: press "continue"), and 1 is also an
        # answer code in the rows that carry it: dropped as survey mechanics.
        appeal = re.sub(r"\s*If you (?:do )?now want to continue.*$", "", it["Riskpreb"])
        assert appeal != it["Riskpreb"] and appeal in it["Riskpreb"]
        riskpreb = f"[IF riskpreb=1 INSERT: {appeal}]"
        assert ";" not in appeal and "[" not in appeal

        def question(i: int, it: dict = it) -> str:
            q = it[i]["question"].replace("In this last choice, you will", "You will")
            opts = " ".join(f'{k} "{o}"' for k, o in enumerate(it[i]["options"], 1))
            return f"{q} {opts}"

        notes = f"""University of Essex, Institute for Social and Economic Research, "Understanding
Society: Innovation Panel, Waves 1-17, 2008-2024", UK Data Service SN 6849.
Experiment 9.13 in the Innovation Panel User Guide, an Associated Study (Linking
Experimental and Survey Data, ES/K001965/1, PI M. M. Galizzi), which asks that
publications acknowledge it. Wave {wave}; GENERATED by `scripts/gen_ip_timerisk.py
--recipes` from the questionnaire PDF, every string asserted to occur in it. Do not
edit by hand.

ONE CONDITION, NOT AN EXPERIMENT (rich's ruling, 9 Oct 2026). One adult per selected
household answered 72 choices between sums of money at different times and 19 between
lotteries, told beforehand that one in ten would be paid for real on one randomly drawn
answer, up to £250. Everyone saw the same preamble and the same choices; the only
randomisation, who was paid, came after the answers. Built because these are real,
incentivised choices. The choices are identical in waves 6 and 7; the preambles are not.

THE CONDITION is the module's own preamble (Trpre), word-for-word, and for the
lottery choices also the lottery preamble (Riskpre), plus, for the 4 face-to-face
respondents who first declined the lotteries and then continued, the second appeal they
saw (Riskpreb). Preamble sentences marked for one mode are resolved per row on
`indmode`. The lottery preamble's web marker follows two sentences ("You must complete
all 91 items ... any money."); both are treated as web-only, an interpretation:
face-to-face decliners got Riskpreb, which repeats the second.

EDITS, by the sequence rule (docs/CONVENTIONS.md): each item's label "Choice 01" ...
"Choice 91" is dropped, and choice 91's "In this last choice, you will" becomes "You
will". "91 questions in this section" in the preambles is kept: it states a count, not
the row's position. Answers are nominal (Option A or B; for choice 91 one of six
lotteries), listed in each question.

The second appeal's closing instruction ("If you do now want to continue enter 1 or
else just return the laptop to the interviewer."; in wave 7, press "continue") is
dropped as survey mechanics: it tells the respondent how to operate the screen, and "1"
is also an answer code in the rows that would carry it. One wave 6 respondent who was
not the household's selected person (TRFLAG = 0) nonetheless began and answered; the
answers are real and kept.

`person` is a hash of `pidp`, the same construction as every Innovation Panel build;
the same respondents were asked again in wave {7 if wave == 6 else 6}, under one id."""
        s = f"""study_id: ukds_6849
source: innovation_panel
title: "Understanding Society Innovation Panel, experiment 9.13: time and risk preference choices
  (wave {wave})"
data_file: {derived_name(wave)}
{lic}comparable_to_socsci210: false
experiment: timerisk_w{wave}
participant_id_var: person

notes: {json.dumps(notes, ensure_ascii=False)}

condition:
  source_var: took_part
  factors: []
  shared_context: {json.dumps(trpre, ensure_ascii=False)}
  arms:
    - raw: 1
      condition_num: 0
      factors: {{}}
      text: ""
      items:
"""
        for i in CHOICES:
            if i in TIME:
                continue
            s += f"""        {i - 1}:
          condition_text: {json.dumps(riskpre + " " + riskpreb, ensure_ascii=False)}
"""
        s += "\noutcomes:\n"
        for i in CHOICES:
            n = len(it[i]["options"])
            s += f"""  - var: choice{i:02d}
    task_num: {i - 1}
    question: {json.dumps(question(i), ensure_ascii=False)}
    scale: {{min: 1, max: {n}, nominal: true}}
"""
        s += "\nresponse_recode: {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6}\n\n"
        s += "respondent_vars: [indmode, riskpreb]\n\nmissing_codes:" + persona
        (REPO / "recipes" / f"ukds_6849_timerisk_w{wave}.yaml").write_text(s)
        print(f"  wrote recipes/ukds_6849_timerisk_w{wave}.yaml")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify participation routing")
    ap.add_argument("--write", action="store_true", help="write the derived .sav files")
    ap.add_argument("--recipes", action="store_true", help="regenerate the two recipes")
    args = ap.parse_args()
    if args.check and sum(check(w) for w in WAVES):
        raise SystemExit("answers from someone who did not begin the questions")
    for w, (wave, _) in WAVES.items():
        df, labels = derive(w)
        n = int((df.loc[df["took_part"] == 1, [f"choice{i:02d}" for i in CHOICES]] > 0).sum().sum())
        print(f"wave {wave}: {n:,} choices answered")
        if args.write:
            narrow = df.copy()
            for col in narrow.columns:
                if narrow[col].dtype == "object" or str(narrow[col].dtype).startswith("string"):
                    narrow[col] = narrow[col].astype(object).where(narrow[col].notna(), np.nan)
            pyreadstat.write_sav(
                narrow, str(OUT / derived_name(wave)), variable_value_labels=labels
            )
    if args.recipes:
        write_recipes()


if __name__ == "__main__":
    main()
