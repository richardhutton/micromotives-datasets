"""The build pipeline: parse → reconstruct → QC → emit.

Turns raw source deposits into validated `(P,c,o,r)` rows and writes Parquet to
`data/processed/`. See docs/SocSci-UK_MASTER.md §8 for the full pipeline
(agent + judgment layer + human), including where a typed-decision judge (Jev)
slots in for is-experiment / variable-ID / category-map / row-QC calls.
"""

from __future__ import annotations
