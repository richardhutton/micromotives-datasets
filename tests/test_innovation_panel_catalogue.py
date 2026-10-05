"""`data/catalog/innovation_panel_experiments.json` is the UKDS screening record.

It says, for each of the Innovation Panel's 93 experiments, whether we intend to
build it and why not if not. `docs/UKDS_UNBUILT.md` is generated from it.

The failure this guards against is the one that has already happened twice in
this project, in two different files: a hand-maintained judgement drifting out of
step with what is true. `uk_dataverse_provenance.json` spent several commits
calling three already-built deposits "prepared"; §5a of the master doc claimed
"(all CC0)" for three days after an audit found that one deposit is not. Both
were found by a person reading them, not by anything that runs.

So three things are pinned here:

- **the generated doc is not stale**, which is the same `--check` discipline as
  `scripts/experiments_table.py` and is the only one of these a person would
  otherwise have to remember
- **every record is complete**, and in particular that a `marginal` or `drop`
  verdict carries a reason. A `build` reason is allowed to be empty, because the
  generator prunes reasons that only restate the title — but silence about why
  something is NOT being built is exactly the gap that leaves an open question
  with no owner
- **the vignette flag survives**, which is not hypothetical: it was originally a
  "VIGNETTE" marker inside the `reason` prose, and pruning redundant reasons
  silently deleted it from three of the four, because those reasons restated
  titles that already contained the word "Vignettes". A flag that matters
  belongs in a field, and a field that matters gets a test.

Deliberately NOT tested: whether any of these are actually buildable. That
depends on the condition wording being in the wave questionnaires, which is
unverified, and the catalogue says so in writing rather than pretending.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from micromotives_datasets.innovation_panel import Experiment

REPO = Path(__file__).resolve().parents[1]
CATALOGUE = REPO / "data" / "catalog" / "innovation_panel_experiments.json"
DOC = REPO / "docs" / "UKDS_UNBUILT.md"
GENERATOR = REPO / "scripts" / "innovation_panel_table.py"

VERDICTS = {"build", "marginal", "drop"}

# The four experiments whose stimulus is researcher-written prose shown to
# respondents word-for-word. Hard-coded because losing one silently is the
# failure this file exists to catch, and a test that derives the answer from the
# file it is checking cannot catch it.
VIGNETTES = {"9.10", "9.26", "9.30", "9.39"}


@pytest.fixture(scope="module")
def catalogue() -> list[Experiment]:
    records: list[Experiment] = json.loads(CATALOGUE.read_text())
    return records


def test_the_generated_doc_is_not_stale() -> None:
    """A doc regenerated from a changed catalogue, and never written, is a lie."""
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"{DOC.relative_to(REPO)} is stale — run "
        f"`uv run python scripts/innovation_panel_table.py --write`.\n{result.stderr[-2000:]}"
    )


def test_every_experiment_is_complete(catalogue: list[Experiment]) -> None:
    fields = {
        "id",
        "title",
        "category",
        "waves",
        "verdict",
        "reason",
        "description",
        "vignette",
        "allocation_vars",
    }
    for record in catalogue:
        missing = sorted(fields - set(record))
        assert not missing, f"{record.get('id')} is missing fields: {missing}"
        assert record["verdict"] in VERDICTS, (
            f"{record['id']} has verdict {record['verdict']!r}, not one of {sorted(VERDICTS)}"
        )
        assert record["title"].strip(), f"{record['id']} has no title"


def test_anything_not_being_built_says_why(catalogue: list[Experiment]) -> None:
    """`build` may have an empty reason; `marginal` and `drop` may not.

    A `build` reason is pruned when it only restates the title, so emptiness
    there carries no information. Not building something is a decision, and a
    decision with no recorded reason is an open question with no owner.
    """
    for record in catalogue:
        if record["verdict"] == "build":
            continue
        assert record["reason"].strip(), (
            f"{record['id']} is {record['verdict']!r} with no reason. "
            f"Screening something out is a decision and has to be written down."
        )


def test_the_vignette_studies_are_still_flagged(catalogue: list[Experiment]) -> None:
    """The four prose-stimulus experiments, which are the reason to care at all.

    Everything else we hold is a conjoint whose condition text WE write from
    attribute levels, which is the one part of a row nothing downstream can
    check. These four came out of the researchers' own hands and went to
    respondents as written.
    """
    flagged = {r["id"] for r in catalogue if r["vignette"]}
    assert flagged == VIGNETTES, (
        f"vignette flags are {sorted(flagged)}, expected {sorted(VIGNETTES)}. "
        f"This flag was lost once already, by living inside the `reason` prose "
        f"where a tidy-up deleted it."
    )
    for record in catalogue:
        if record["id"] in VIGNETTES:
            assert record["verdict"] == "build", (
                f"{record['id']} is a vignette study marked {record['verdict']!r}. "
                f"If that is deliberate, the reason has to say so explicitly."
            )


def test_nothing_from_the_data_files_leaks_into_the_tracked_catalogue() -> None:
    """The licence line, enforced rather than asserted in prose.

    The EUL defines the Data Collection to include its Documentation, which is
    why `jev.RESTRICTED` refuses `source="ukds"` and `data/raw/` is gitignored.
    Two things are quoted in the tracked catalogue anyway, deliberately: the
    User Guide's descriptions, because Understanding Society separately
    publishes that guide on the open web, and the allocation variable names the
    guide itself prints.

    What must never appear is anything read out of the `.dta` files — a variable
    label, a value label, a row. Those are the collection proper. So any
    wave-prefixed token that is NOT one of the allocation variables the guide
    names is treated as a leak, because the only way such a token gets here is
    by someone pasting from a dataframe.
    """
    catalogue_text = CATALOGUE.read_text()
    records = json.loads(catalogue_text)
    from_the_guide = {v for r in records for v in r["allocation_vars"]}
    # File and key names the guide prints in prose, which are structure, not data.
    structural = {"e_hhsamp_ip", "w_hhsamp_ip", "w_indresp_ip", "w_hidp"}
    wave_prefixed = re.compile(r"\b[a-q]_[a-z][a-z0-9_]{2,}\b")

    for name, text in (("the catalogue", catalogue_text), ("the doc", DOC.read_text())):
        leaked = sorted(set(wave_prefixed.findall(text)) - from_the_guide - structural)
        assert not leaked, (
            f"{name} contains wave-prefixed tokens that the User Guide does not name: "
            f"{leaked}. Those come out of the data files, whose labels ARE the licensed "
            f"collection. Remove them; the guide's own prose is quotable, the data is not."
        )


def test_the_hazard_rulings_are_applied(catalogue: list[Experiment]) -> None:
    """The two standing rulings that moved experiments out of the build list.

    `9.3` trips X08IVC: its condition asks the respondent to rate their
    satisfaction relative to others of their own gender or education, which names
    their own persona category. It is otherwise an ideal study — five conditions,
    a substantive outcome, the allocation variable named in the guide — which is
    exactly why it needs a test rather than a memory.

    The physical and procedural experiments are the SACJHE ruling applied at
    scale: a stimulus that is not text is not a stimulus for us.
    """
    by_id = {r["id"]: r for r in catalogue}

    assert by_id["9.3"]["verdict"] == "marginal", (
        "9.3 is back in the build list. Its condition names the respondent's own "
        "gender or education, which is the X08IVC hazard class; see CONVENTIONS.md "
        "for the three remedies before moving it."
    )
    assert "X08IVC" in by_id["9.3"]["reason"]

    for record in catalogue:
        if record["category"] in {"procedural", "physical"}:
            assert record["verdict"] == "drop", (
                f"{record['id']} is {record['category']} and marked "
                f"{record['verdict']!r}. Procedural experiments measure whether "
                f"someone took part, not what they answered; physical ones have no "
                f"text stimulus."
            )
