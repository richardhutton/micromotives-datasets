# R helper for scripts/verify_RJTVG8.py — runs the SAME estimator as
# `replication_electoralstudies.R`'s own Figure-2/Table-A.4 call:
#
#   mm1 <- mm(df, selected ~ prereg + method + vwindow + trials + pilot +
#               fraud + cost + platform + private + party + endorse,
#             id = ~IDvar, h0 = 0.5)
#
# but over profile-level data reshaped from the BUILT PARQUET instead of the
# raw .dta. This is deliberately dumb: no cleaning, no releveling, no
# missing-value logic — all of that already happened (a) in the melt, which
# produced the input CSV, and (b) in the Python orchestrator, which also
# translates our rendered attribute TEXT back to the authors' own R factor
# labels before calling this. This script's only job is to be the IDENTICAL
# estimator over a different input, so a disagreement with the transcribed
# Table A.4 can only be explained by the melt (or the translation), not by
# two estimators differing. Same pattern as scripts/verify_EFXNLX_cj.R.
#
# Usage: Rscript scripts/verify_RJTVG8_cj.R <input_profile_csv> <output_csv>

suppressPackageStartupMessages({
  library(cregg)
})

args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 2)
IN  <- args[1]
OUT <- args[2]

ATTRS <- c("prereg", "method", "vwindow", "trials", "pilot", "fraud", "cost",
           "platform", "private", "party", "endorse")

prof <- read.csv(IN, stringsAsFactors = FALSE, colClasses = "character")
prof$chosen <- as.integer(prof$chosen)
for (a in ATTRS) prof[[a]] <- factor(prof[[a]])

cat("# profile-level rows fed to mm():", nrow(prof), "\n")
cat("# distinct respondents (IDvar):", length(unique(prof$IDvar)), "\n")

f <- as.formula(paste("chosen ~", paste(ATTRS, collapse = " + ")))

mm1 <- mm(prof, f, id = ~IDvar, h0 = 0.5)

COLS <- c("feature", "level", "estimate", "std.error")
write.csv(mm1[, COLS], OUT, row.names = FALSE)

cat(sprintf("wrote %s — %d marginal means\n", OUT, nrow(mm1)))
