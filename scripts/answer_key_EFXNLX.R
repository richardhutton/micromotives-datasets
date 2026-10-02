# The answer key for EFXNLX, taken from the depositors' own estimator.
#
# The published paper reports every result as an AMCE coefficient PLOT — Figures
# 2 to 5, no numeric table in the main text beyond one inline value. This project
# has already ruled that a figure is not an acceptable answer key: I once failed
# two correct cells by reading 16.9 off a chart the table prints as 16.83
# (ledger 99).
#
# But the CC0 deposit ships the full Supplementary Information as R Markdown
# SOURCE, and that source computes the numbers with `cregg::cj()` before handing
# them to ggplot. `cj()` returns a tidy data frame; the plot is what happens to it
# afterwards. So the numbers are already ours and merely unrendered.
#
# This script runs THEIR cleaning and THEIR estimator and prints what it returns.
# It deliberately does not reimplement AMCE estimation in Python: checking our
# melt against our own reimplementation would not be verification of anything.
# The output is transcribed into a Python verify script as constants, which is
# the `verify_QQM5MC.py` pattern — one study, one answer key, read from the BUILT
# parquet so it tests the melt rather than the paper.
#
# Usage:  Rscript scripts/answer_key_EFXNLX.R > data/catalog/answer_key_EFXNLX.txt

suppressPackageStartupMessages({
  library(haven)
  library(cregg)
})

RAW <- "data/raw/EFXNLX"
stopifnot(dir.exists(RAW))

# `haven::read_sav`, not `rio::import`. rio returns the attribute columns as
# bare numerics, so every level came through as "1", "2", "3" — identical
# across all 8 attributes, which cregg then rejected for duplicated level names.
# That failure was loud. The quiet version of the same mistake would have been
# an answer key labelled by code number, which is exactly the shape of the
# defect found in 6MRVOM's Table 1: right numbers, wrong labels on them.
d <- haven::read_sav(file.path(RAW, "LSEResults_Brexit_170428_client.sav"))
cat("# respondents:", nrow(d), "\n")

# ---------------------------------------------------------------------------
# Reshape, following analysis-conjoint-cleaning.R exactly.
#
# Two reshapes: wide -> one row per (respondent, pair), then -> one row per
# (respondent, pair, profile). The depositors assert both counts with stopifnot;
# those assertions are repeated here, because a count that silently changed
# would mean we are describing a different dataset than the paper does.
# ---------------------------------------------------------------------------

ATTRS <- c("imigration", "rights", "trade", "laws", "budget", "payment",
           "border", "timeline")
PAIRS <- 1:5   # the 6th, fixed pair is excluded from the paper AND from the
               # depositors' own analysis, so it is excluded here too.

long <- do.call(rbind, lapply(PAIRS, function(t) {
  base <- data.frame(
    ID   = seq_len(nrow(d)),
    pair = t,
    Q1   = d[[paste0("QB1_PAIR", t)]],
    stringsAsFactors = FALSE
  )
  for (side in 1:2) {
    for (a in ATTRS) {
      v <- d[[sprintf("%s_seen%d_t%d", a, side, t)]]
      base[[sprintf("%s_%d", a, side)]] <- as.character(haven::as_factor(v))
    }
  }
  base
}))
stopifnot(nrow(long) == 5 * nrow(d))
cat("# pair-level rows:", nrow(long), "\n")

prof <- do.call(rbind, lapply(1:2, function(side) {
  out <- data.frame(
    ID      = long$ID,
    pair    = long$pair,
    profile = side,
    chosen  = as.integer(long$Q1 == side),
    stringsAsFactors = FALSE
  )
  for (a in ATTRS) out[[a]] <- long[[sprintf("%s_%d", a, side)]]
  out
}))
stopifnot(nrow(prof) == 2 * nrow(long))
cat("# profile-level rows:", nrow(prof), "\n")

prof <- prof[!is.na(prof$chosen), ]
for (a in ATTRS) prof[[a]] <- factor(prof[[a]])
cat("# profile-level rows, non-missing outcome:", nrow(prof), "\n\n")

# ---------------------------------------------------------------------------
# The estimator, and the numbers it returns.
#
# Baselines are NOT the raw code order — analysis-conjoint-cleaning.R relevels
# every attribute by hand, and the sign of every AMCE depends on it. Rather than
# transcribe their releveling (and risk a quiet transposition, which is exactly
# the defect found in 6MRVOM's Table 1), the reference level of each factor is
# PRINTED below so the Python verify script can assert against the same baseline
# it was computed from.
# ---------------------------------------------------------------------------

cat("## reference level per attribute\n")
for (a in ATTRS) cat(sprintf("%-12s %s\n", a, levels(prof[[a]])[1]))
cat("\n")

f <- as.formula(paste("chosen ~", paste(ATTRS, collapse = " + ")))

COLS <- c("feature", "level", "estimate", "std.error")
OUT <- "data/catalog/answer_key_EFXNLX.csv"

cat("## AMCEs (cregg::cj, estimate = \"amce\", clustered by respondent)\n")
amce <- cj(prof, f, id = ~ID, estimate = "amce")

cat("\n## marginal means (cregg::cj, estimate = \"mm\")\n")
mm <- cj(prof, f, id = ~ID, estimate = "mm")

# Written as a file, not just printed: a wide data frame wraps in the console
# into column blocks, and transcribing constants by eye out of wrapped output is
# the same class of mistake as reading a value off a chart. The CSV is what the
# Python verify script is built from.
key <- rbind(
  cbind(quantity = "amce", amce[, COLS]),
  cbind(quantity = "mm",   mm[, COLS])
)
key$reference <- vapply(as.character(key$feature),
                        function(a) levels(prof[[a]])[1], character(1))
write.csv(key, OUT, row.names = FALSE)
cat(sprintf("\nwrote %s — %d rows (%d AMCEs, %d marginal means)\n",
            OUT, nrow(key), nrow(amce), nrow(mm)))

cat("\n# a forced choice between two profiles means the marginal means over a\n")
cat("# fully randomised design average to 0.5; a build whose melt dropped or\n")
cat("# duplicated profiles would not reproduce that.\n")
cat(sprintf("# mean of marginal means: %.6f\n", mean(mm$estimate)))
