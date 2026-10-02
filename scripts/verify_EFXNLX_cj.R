# R helper for scripts/verify_EFXNLX.py — runs the SAME estimator as
# scripts/answer_key_EFXNLX.R (cregg::cj, formula, clustering, reference-level
# convention), but over profile-level data reshaped from the BUILT PARQUET
# instead of over the raw .sav.
#
# This is deliberately dumb: no cleaning, no releveling, no missing-value
# logic. All of that already happened (a) in the melt, which produced the
# input CSV, and (b) is asserted separately by the Python orchestrator. This
# script's only job is to be the identical estimator over a different input,
# so that a disagreement with answer_key_EFXNLX.csv can only be explained by
# the melt, not by two estimators differing.
#
# Usage: Rscript scripts/verify_EFXNLX_cj.R <input_profile_csv> <output_csv>

suppressPackageStartupMessages({
  library(cregg)
})

args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 2)
IN  <- args[1]
OUT <- args[2]

ATTRS <- c("imigration", "rights", "trade", "laws", "budget", "payment",
           "border", "timeline")

prof <- read.csv(IN, stringsAsFactors = FALSE, colClasses = "character")
prof$chosen <- as.integer(prof$chosen)
for (a in ATTRS) prof[[a]] <- factor(prof[[a]])

cat("# profile-level rows fed to cj():", nrow(prof), "\n")
cat("# distinct respondents (ID):", length(unique(prof$ID)), "\n")

f <- as.formula(paste("chosen ~", paste(ATTRS, collapse = " + ")))

amce <- cj(prof, f, id = ~ID, estimate = "amce")
mm   <- cj(prof, f, id = ~ID, estimate = "mm")

COLS <- c("feature", "level", "estimate", "std.error")
key <- rbind(
  cbind(quantity = "amce", amce[, COLS]),
  cbind(quantity = "mm",   mm[, COLS])
)
key$reference <- vapply(as.character(key$feature),
                        function(a) levels(prof[[a]])[1], character(1))
write.csv(key, OUT, row.names = FALSE)

cat(sprintf("wrote %s — %d rows (%d AMCEs, %d marginal means)\n",
            OUT, nrow(key), nrow(amce), nrow(mm)))
cat(sprintf("# mean of marginal means: %.6f\n", mean(mm$estimate)))
