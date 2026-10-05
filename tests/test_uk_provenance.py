"""`data/catalog/uk_dataverse_provenance.json` is the UK layer's licence record.

It is the one file that says, per deposit, what permits us to ship the rows —
every UK recipe's `licence:` field is transcribed FROM here. It is also the only
catalogue in the project that is maintained by hand, which is why it drifted:
three of its nine deposits still said `"prepared"` after they had been built and
committed, found by a checker reading it rather than by anything that runs.

A hand-maintained status field will always drift. So the three things that carry
consequences are pinned here against things that cannot be forgotten:

- **`status`** against the tracked recipes. A study is "built" exactly when a
  recipe exists for it. Deliberately NOT checked against `data/processed/`,
  which is gitignored — a test that passes only on a machine that happens to
  have built everything is not a test.
- **`licence`** against the literal string `CC0 1.0`, for anything we might
  actually use. Every UK row we ship rests on that string being right, and
  `embed.py`'s `CLEARED` gate keys on the exact spelling.
- **Completeness against `docs/SocSci-UK_MASTER.md` §5a**, which is the second
  failure and the worse one. The drift above was a wrong value; this is a missing
  row. `PZB01G`, `RJTVG8`, `SACJHE` and `POMIFD` were listed in §5a's table and
  absent from this file entirely — so they had no status, no reason, and nothing
  checked them, including the tests above, which can only inspect rows that
  exist. A test that iterates a catalogue cannot notice what is not in it, so the
  section that names the deposits is now the authority on which rows must be here.

The checker that found the drift also found no data defect from it, which is the
point worth keeping: this file is read by people deciding what may be published,
not by the build, so its errors are invisible until someone acts on one.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROVENANCE = REPO / "data" / "catalog" / "uk_dataverse_provenance.json"
MASTER = REPO / "docs" / "SocSci-UK_MASTER.md"
RECIPES = REPO / "recipes"

STATUSES = {
    "built": "a recipe exists and the rows are in the corpus",
    "prepared": "assessed, buildable or still under test, not yet built",
    "dropped": "will not be built, and `status_reason` says why",
    "blocked": "cannot be built for a reason outside our control — a licence, "
    "chiefly — rather than a judgement that it is not worth building",
}

# A Harvard Dataverse deposit code as §5a writes it: six uppercase alphanumerics.
DEPOSIT_CODE = re.compile(r"[A-Z0-9]{6}")


def _catalogue() -> dict[str, dict]:
    data: dict[str, dict] = json.loads(PROVENANCE.read_text())
    return data


def _recipes_for(deposit: str) -> list[str]:
    """Recipe filenames belonging to `deposit`.

    One deposit can hold several experiments (`35M5CV` ships a lodger conjoint
    and a BBC conjoint; `LOGVPZ` a satisfaction study and a risk study), so the
    match is on prefix and the relation is one-to-many.
    """
    return sorted(
        p.name
        for p in RECIPES.glob("*.yaml")
        if p.stem == deposit or p.stem.startswith(f"{deposit}_")
    )


def _section_5a() -> str:
    text = MASTER.read_text()
    match = re.search(r"^### 5a\..*?(?=^###? 5b\.)", text, re.M | re.S)
    assert match, "could not find section 5a in docs/SocSci-UK_MASTER.md"
    return match.group(0)


def _deposits_named_in_5a() -> set[str]:
    """Deposit codes appearing in any table cell of §5a.

    Scoped to table rows rather than the whole section so that prose mentioning
    a code in passing does not create a phantom obligation — it is the TABLES
    that enumerate the deposits, and a code in a table is a claim that the
    deposit is part of the UK universe.
    """
    codes: set[str] = set()
    for line in _section_5a().splitlines():
        if not line.startswith("|"):
            continue
        for cell in (c.strip().strip("`") for c in line.split("|")):
            if DEPOSIT_CODE.fullmatch(cell):
                codes.add(cell)
    assert len(codes) >= 9, f"only found {len(codes)} deposit codes in §5a; the parse has broken"
    return codes


def test_every_deposit_in_the_master_doc_has_a_catalogue_row() -> None:
    """The missing-row failure, which no other test in this file can see.

    Four deposits sat in §5a's table with no row here at all, and so had no
    status, no reason, and no test touching them — the rest of this file
    iterates the catalogue, and a catalogue cannot report what it omits. §5a is
    the authority on WHICH deposits exist; this file is the authority on what is
    true of each. Adding a deposit to the doc without a row here now fails.
    """
    missing = sorted(_deposits_named_in_5a() - set(_catalogue()))
    assert not missing, (
        f"{len(missing)} deposit(s) named in §5a of docs/SocSci-UK_MASTER.md have no row in "
        f"{PROVENANCE.name}: {missing}. A deposit with no row has no status and no reason, "
        f"so nothing decides anything about it and no test can see it."
    )


def test_every_deposit_declares_a_known_status() -> None:
    for deposit, record in _catalogue().items():
        assert record.get("status") in STATUSES, (
            f"{deposit} has status {record.get('status')!r}, not one of {sorted(STATUSES)}"
        )


def test_status_built_means_a_recipe_exists_and_the_reverse() -> None:
    """The drift that actually happened, in both directions.

    Forwards catches a deposit marked built with nothing to show for it.
    Backwards catches the real failure: a deposit that got built while its
    record was left saying `prepared`, which is how `35M5CV`, `LOGVPZ` and
    `PMV0TG` spent several commits understating what the UK layer contained.
    """
    for deposit, record in _catalogue().items():
        recipes = _recipes_for(deposit)
        if record["status"] == "built":
            assert recipes, f"{deposit} is marked built but has no recipe in recipes/"
        else:
            assert not recipes, (
                f"{deposit} is marked {record['status']!r} but {recipes} exist(s) — "
                f"it is built, and the catalogue is the file people read to decide "
                f"what may be published"
            )


def test_anything_not_built_says_why() -> None:
    """A `prepared` or `dropped` row with no reason is an open question with no owner."""
    for deposit, record in _catalogue().items():
        if record["status"] != "built":
            reason = (record.get("status_reason") or "").strip()
            assert reason, f"{deposit} is {record['status']!r} with no status_reason"


def test_anything_we_build_is_cc0_or_says_in_writing_why_not() -> None:
    """Nothing gets built until someone has written down what permits it.

    This test asserted plain `licence == "CC0 1.0"` until 5 October 2026, on the
    premise that the corpus would be PUBLISHED and CC0 was therefore the only
    thing shippable. rich then settled that he is not redistributing anything —
    the dataset is for his own research use — which moves the question from *may
    we publish this* to *may we use it*, and those have different answers.

    `POMIFD` is the case that forced it. Its licence is literally `null`, so it
    can never be republished; but its terms invite contact before use, rich made
    that contact, and he will delete the build if the depositor objects. That is
    a legitimate basis for use and an illegitimate basis for publication, and a
    field holding only a licence string cannot express the difference.

    So `use_basis` is required wherever the licence is not CC0. It is prose, not
    a flag, because the whole value is that a person had to write the reason down
    and can be held to it. What survives from the old test is the part that
    mattered: a deposit cannot reach a builder on a status alone.
    """
    for deposit, record in _catalogue().items():
        if record["status"] not in {"built", "prepared"}:
            continue
        if record.get("licence") == "CC0 1.0":
            continue
        basis = (record.get("use_basis") or "").strip()
        assert basis, (
            f"{deposit} is {record['status']!r} with licence {record.get('licence')!r} "
            f"and no `use_basis`. A deposit that is not CC0 may still be USED, but only "
            f"where someone has written down what permits it — the terms relied on, who "
            f"was contacted, and what happens if they object. Silence is not a basis."
        )


def test_only_cc0_is_ever_marked_redistributable() -> None:
    """Use and redistribution are different permissions and must not blur.

    §5a's heading said "(all CC0)" for three days after an audit found `POMIFD`
    was not — a licence claim in a heading, with the correction four lines below
    it. The modern version of that error would be a `use_basis` quietly growing
    into a redistribution claim, because the deposit is sitting in the corpus
    looking like every other built study.

    `redistributable` is therefore derived from the licence and nothing else. A
    `use_basis` can permit a build; it can never permit publication.
    """
    for deposit, record in _catalogue().items():
        redistributable = record.get("redistributable")
        if redistributable is None:
            continue
        expected = record.get("licence") == "CC0 1.0"
        assert redistributable is expected, (
            f"{deposit} records redistributable={redistributable!r} with licence "
            f"{record.get('licence')!r}. Only CC0 1.0 is redistributable; a use_basis "
            f"permits a build and never a publication"
        )


def test_every_deposit_carries_a_doi_and_a_description() -> None:
    """Attribution, and enough text to know which study a deposit is without opening it."""
    for deposit, record in _catalogue().items():
        assert str(record.get("doi", "")).startswith("10.7910/DVN/"), (
            f"{deposit} has no Harvard Dataverse DOI"
        )
        assert (record.get("description") or "").strip(), f"{deposit} has no description"
        assert (record.get("authors") or "").strip(), f"{deposit} has no authors"


def test_no_judgement_field_is_ever_blank_where_one_was_recorded() -> None:
    """A fetch must never overwrite a judgement with an API refresh.

    On 5 October 2026 `scripts/fetch_dataverse.py` did `prov[code] = {...}` — a
    wholesale replacement — and destroyed `PZB01G`'s `status` and
    `status_reason`: the record of why that study is buildable, established by a
    paper-access test and not regenerable from any API. `POMIFD` survived the
    same run only because its maker read the script first and avoided it.

    The script now merges. This is the second line of defence, and it is a
    different shape from the other tests here: those check that a value is
    RIGHT, this checks that a value a person wrote has not silently become
    absent. `status` is required of every row, so its disappearance is already
    caught — but `use_basis` and `redistributable` are optional by design, and
    an optional field is exactly the kind that vanishes without complaint.
    """
    catalogue = _catalogue()

    # `use_basis` exists only where the licence is not CC0; wherever that is
    # true, something must have been written, or the deposit should not be in a
    # buildable state at all.
    for deposit, record in catalogue.items():
        if record.get("licence") == "CC0 1.0":
            continue
        if record["status"] in {"dropped", "blocked"}:
            continue
        assert (record.get("use_basis") or "").strip(), (
            f"{deposit} is {record['status']!r} with a non-CC0 licence and an empty "
            f"use_basis. If a fetch has just run, check whether it overwrote the entry: "
            f"fetch_dataverse.py merges now, but the failure mode it caused was a "
            f"judgement silently replaced by an API refresh."
        )

    assert any(r.get("use_basis") for r in catalogue.values()), (
        "no deposit records a use_basis at all. POMIFD carries one; if it has gone, "
        "something has rewritten this file wholesale"
    )
