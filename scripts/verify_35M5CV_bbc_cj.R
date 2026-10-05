# R helper for scripts/verify_35M5CV_bbc.py — see verify_35M5CV_lodger_cj.R's
# header for the full rationale; this is the same mechanism for the BBC
# conjoint's own 7 attributes.
#
# Usage: Rscript scripts/verify_35M5CV_bbc_cj.R <input_profile_csv> <reference_levels_tsv> <output_csv>
#
# `reference_levels_tsv` is plain TAB-separated "feature<TAB>level" lines —
# see verify_35M5CV_lodger_cj.R's header for why this is not JSON.

suppressPackageStartupMessages({
  library(cregg)
})

args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 3)
IN   <- args[1]
REFF <- args[2]
OUT  <- args[3]

ATTRS <- c("name", "age", "experience", "degree", "party", "eu", "occupation")

prof <- read.csv(IN, stringsAsFactors = FALSE, colClasses = "character")
prof$chosen <- as.integer(prof$chosen)

ref_lines <- strsplit(readLines(REFF), "\t")
refs <- setNames(vapply(ref_lines, `[[`, character(1), 2),
                  vapply(ref_lines, `[[`, character(1), 1))

for (a in ATTRS) {
  lv <- unique(prof[[a]])
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
