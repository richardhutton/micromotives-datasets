"""Settings and canonical data paths.

Env vars are prefixed `MICROMOTIVES_` and can live in `.env.local`.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root = two parents up from this file (src/micromotives_datasets/config.py).
REPO_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = REPO_ROOT / "data"
CATALOG_DIR = DATA_DIR / "catalog"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DOCS_DIR = REPO_ROOT / "docs"

# Study-level catalogs (committed).
TESS_FOUNDATION_CSV = CATALOG_DIR / "tess_uk_foundation_sources.csv"
UK_DATAVERSE_CSV = CATALOG_DIR / "uk_dataverse_candidates.csv"

# SocSci210 on the Hugging Face Hub (org `socratesft`; see scripts/explore.py).
SOCSCI210_HF_REPO = "socratesft/SocSci210"


class Settings(BaseSettings):
    """Runtime settings. Override via env (MICROMOTIVES_*) or `.env.local`."""

    model_config = SettingsConfigDict(
        env_prefix="MICROMOTIVES_",
        env_file=".env.local",
        extra="ignore",
    )

    hf_token: str | None = None
    osf_token: str | None = None
    # Keep raw microdata off any external service unless a licence allows it.
    allow_external_egress: bool = False


settings = Settings()
