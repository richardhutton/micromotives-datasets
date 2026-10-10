"""A drawn factorial: most cells are empty by arithmetic, but every level must occur.

DEL's NGO conjoint declares 2x2x5x5 levels per profile and two profiles, 10,000 cells,
and 12,438 screens fill 7,052 of them. QC rule 2's "every declared arm must appear"
can never pass for such a design, so `ConditionTemplate.sparse` swaps it for the check
that still means something: every declared LEVEL of every dimension appears.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyreadstat

from micromotives_datasets.pipeline.build import build_rows
from micromotives_datasets.pipeline.qc import check
from micromotives_datasets.recipe import Recipe
from micromotives_datasets.sources import spss


def _recipe(sparse: bool) -> Recipe:
    return Recipe.model_validate(
        {
            "study_id": "spr01",
            "source": "dataverse",
            "data_file": "f.sav",
            "licence": "synthetic test fixture",
            "condition": {
                "template": {
                    "sparse": sparse,
                    "text": "An NGO that is {size} and works in {region}.",
                    "dimensions": {
                        "size": {
                            "var": "SIZE",
                            "levels": {
                                1: {"level": "large", "text": "large"},
                                2: {"level": "small", "text": "small"},
                            },
                        },
                        "region": {
                            "var": "REGION",
                            "levels": {
                                1: {"level": "africa", "text": "Africa"},
                                2: {"level": "asia", "text": "Asia"},
                                3: {"level": "latam", "text": "Latin America"},
                            },
                        },
                    },
                }
            },
            "outcomes": [
                {"var": "Q", "task_num": 0, "question": "Donate?", "scale": {"min": 1, "max": 2}}
            ],
            "response_recode": {1: 1, 2: 2},
        }
    )


def _rows(tmp_path: Path, size: list[int], region: list[int], sparse: bool):
    path = tmp_path / "f.sav"
    pyreadstat.write_sav(
        pd.DataFrame({"SIZE": size, "REGION": region, "Q": [1] * len(size)}).astype(float),
        str(path),
    )
    rec = _recipe(sparse)
    return list(build_rows(spss.read(path), rec)), rec


def test_a_sparse_design_with_every_level_present_raises_no_warning(tmp_path: Path) -> None:
    # 3 of 6 cells occur, but every level of both dimensions does.
    rows, rec = _rows(tmp_path, [1, 2, 1], [1, 2, 3], sparse=True)
    assert check(rows, rec).warnings == []


def test_a_level_that_never_occurs_is_still_flagged(tmp_path: Path) -> None:
    rows, rec = _rows(tmp_path, [1, 2, 1], [1, 2, 2], sparse=True)
    warnings = check(rows, rec).warnings
    assert any("region levels with no rows: ['latam']" in w for w in warnings), warnings


def test_without_sparse_every_empty_cell_is_still_flagged(tmp_path: Path) -> None:
    """A crossed design (9.10, 9.18) keeps the cell-level rule: an empty cell there IS news."""
    rows, rec = _rows(tmp_path, [1, 2, 1], [1, 2, 3], sparse=False)
    assert any("declared arms with no rows" in w for w in check(rows, rec).warnings)


# --- age is read through its value labels (DEL wave 3 stores 1 = "18") --------


def _age_rows(tmp_path: Path, codes: list[float], labels: dict[float, str] | None):
    path = tmp_path / "a.sav"
    df = pd.DataFrame(
        {
            "SIZE": [1.0] * len(codes),
            "REGION": [1.0] * len(codes),
            "Q": [1.0] * len(codes),
            "AGE": codes,
        }
    )
    pyreadstat.write_sav(df, str(path), variable_value_labels={"AGE": labels} if labels else None)
    rec = _recipe(sparse=True).model_copy(update={"persona_map": {"age": "AGE"}})
    return list(build_rows(spss.read(path), rec)), rec


def test_a_coded_age_is_read_through_its_label(tmp_path: Path) -> None:
    rows, _ = _age_rows(tmp_path, [1.0, 77.0], {1.0: "18", 77.0: "94"})
    assert [r.persona.age for r in rows] == [18, 94]


def test_a_real_age_without_labels_is_unchanged(tmp_path: Path) -> None:
    rows, _ = _age_rows(tmp_path, [64.0, 18.0], None)
    assert [r.persona.age for r in rows] == [64, 18]


def test_an_impossible_age_fails_qc(tmp_path: Path) -> None:
    rows, rec = _age_rows(tmp_path, [1.0, 40.0], None)  # the raw-code defect, unlabelled
    assert any("persona ages outside 16-120" in f for f in check(rows, rec).failures)
