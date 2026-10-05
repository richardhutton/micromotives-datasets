# R helper for scripts/verify_35M5CV_lodger.py — runs the SAME estimator as
# scripts/answer_key_35M5CV.R's `run_study("LODGER", ...)` (cregg::cj, formula,
# clustering, reference-level convention for party/eu), but over profile-level
# data reshaped from the BUILT PARQUET instead of over the raw .sav.
#
# Deliberately dumb: no cleaning, no releveling logic beyond fixing factor
# LEVEL ORDER to match the answer key's own baseline per feature (passed in as
# a side-channel JSON of reference levels, so this script does not need to
# re-derive party/eu's hand releveling independently — it only has to use the
# SAME one). Everything else already happened in the melt. A disagreement with
# answer_key_35M5CV_lodger.csv can then only be explained by the melt.
#
# Usage: Rscript scripts/verify_35M5CV_lodger_cj.R <input_profile_csv> <reference_levels_tsv> <output_csv>
#
# `reference_levels_tsv` is plain TAB-separated "feature<TAB>level" lines, one
# per attribute — not JSON, deliberately: `jsonlite` is not installed in this
# environment and this project's own convention
# (R_MAKEVARS_USER=tools/Makevars to build a missing package) is for packages
# this analysis genuinely needs, not a parsing convenience base R already has.

suppressPackageStartupMessages({
  library(cregg)
})

args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 3)
IN   <- args[1]
REFF <- args[2]
OUT  <- args[3]

ATTRS <- c("name", "age", "occupation", "volunteer", "party", "eu", "hobby")

prof <- read.csv(IN, stringsAsFactors = FALSE, colClasses = "character")
prof$chosen <- as.integer(prof$chosen)

ref_lines <- strsplit(readLines(REFF), "\t")
refs <- setNames(vapply(ref_lines, `[[`, character(1), 2),
                  vapply(ref_lines, `[[`, character(1), 1))

for (a in ATTRS) {
  lv <- unique(prof[[a]])
  # Reference level first, everything else in the order it first appears —
  # cregg only needs the BASELINE pinned; it does not care about the order of
  # the remaining levels (the AMCE for each is reported against the baseline
  # regardless of where it sits in `levels()`).
  ref <- refs[[a]]
  stopifnot(ref %in% lv)
  ordered <- c(ref, setdiff(lv, ref))
  prof[[a]] <- factor(prof[[a]], levels = ordered)
}

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
