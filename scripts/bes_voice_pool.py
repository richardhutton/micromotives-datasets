"""Build the pool of real people's own words that the quote writer copies the VOICE of.

    uv run python scripts/bes_voice_pool.py

docs/QUOTES_SPEC.md (v6): the quotes all sounded like one model. Real open-text answers
from the British Election Study internet panel ("Strings" file, waves 1-30; rich has
BES's OK for this use) show how people actually explain themselves: mostly a few words,
sometimes a sentence, in their own spelling. Only questions that ask for a REASON or a
reaction are used (main reason for a vote or a non-vote, what they like or dislike about
a leader, what changed their view, why they expect a party to win, vaccine worries).

Each answer is tagged with the person's age band and education band from the panel
file, so the writer can be shown answers from people like the respondent; party and
region are deliberately NOT used, since they carry opinions and the examples are for
voice only. Writes data/processed/quotes/voice_pool.parquet (gitignored: respondent
text). Prints counts only.
"""

from __future__ import annotations

import re

import pandas as pd
import pyreadstat

from micromotives_datasets import quotes as q

RAW = q.ROOT / "data" / "raw" / "bes_panel"
STRINGS = RAW / "BES2024_W30Strings_v30.1.sav"
PANEL = RAW / "BES2024_W31_Panel_v31.05.sav"
OUT = q.ROOT / "data" / "processed" / "quotes" / "voice_pool.parquet"

REASON = re.compile(
    r"^(ReasonForvoteOth|changeViewDetail|euVoteReasons|euNonVoteReasons|conwinreasonopen2?|"
    r"gePostVoteReasons|geVoteIntentionReasons|geNonVoteIntentionReasons|vaccinefearsopen|"
    r"(starmer|sunak)(Like|Dislike)Open_text1)W\d+$"
)
PLACEHOLDERS = {
    "",
    "__NA__",
    "-1",
    "-99",
    "n/a",
    "na",
    "none",
    "nothing",
    "dont know",
    "don't know",
    "dk",
}
MAX_WORDS = 40


def age_band(age: float) -> str | None:
    if pd.isna(age) or age < 16:
        return None
    return "18-34" if age < 35 else "35-54" if age < 55 else "55+"


def edu_band(level: float) -> str | None:
    if pd.isna(level):
        return None
    return "degree" if level >= 4 else "no degree"


def latest(frame: pd.DataFrame, prefix: str) -> pd.Series:
    """Each person's most recent non-missing value of a per-wave variable."""
    cols = sorted(
        (c for c in frame.columns if c.startswith(prefix)), key=lambda c: int(c[len(prefix) :])
    )
    return frame[cols].ffill(axis=1).iloc[:, -1]


def main() -> None:
    _, meta = pyreadstat.read_sav(STRINGS, metadataonly=True)
    cols = [c for c in meta.column_names if REASON.match(c)]
    text, _ = pyreadstat.read_sav(STRINGS, usecols=["id", *cols], encoding="latin1")
    long = text.melt(id_vars="id", var_name="question", value_name="text").dropna()
    long["text"] = long["text"].astype(str).str.strip()
    long = long[~long["text"].str.lower().isin(PLACEHOLDERS) & (long["text"].str.len() > 1)]
    long = long[long["text"].str.split().str.len() <= MAX_WORDS]
    long["question"] = long["question"].str.replace(r"W\d+$", "", regex=True)

    _, pmeta = pyreadstat.read_sav(PANEL, metadataonly=True)
    want = ["id"] + [c for c in pmeta.column_names if re.match(r"^(ageW|p_edlevelW)\d+$", c)]
    panel, _ = pyreadstat.read_sav(PANEL, usecols=want)
    people = pd.DataFrame(
        {
            "id": panel["id"],
            "age_band": latest(panel, "ageW").map(age_band),
            "edu_band": latest(panel, "p_edlevelW").map(edu_band),
        }
    )
    pool = long.merge(people, on="id", how="left").drop(columns="id")
    # one row per distinct answer, with how many people gave it, so a common short answer
    # ("Everything") can be shown about as often as people really give it
    counts = pool.groupby("text").size().rename("n")
    pool = pool.drop_duplicates(["text"]).merge(counts, on="text").reset_index(drop=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pool.to_parquet(OUT, index=False)

    words = pool["text"].str.split().str.len()
    print(f"{len(pool)} distinct real answers from {pool['question'].nunique()} reason questions")
    print(f"words: median {int(words.median())}, 90th percentile {int(words.quantile(0.9))}")
    print(pool.groupby(["age_band", "edu_band"], dropna=False).size().to_string())


if __name__ == "__main__":
    main()
