# The answer key for 35M5CV's two buildable experiments (lodger, bbc).
#
# Hobolt, Leeper & Tilley, "Divided by the Vote: Affective polarization in the
# Wake of the Brexit Referendum" (BJPS 51(4):1476-1493). Both conjoints report
# every result as a plot only -- the main text, the supplementary .docx, and
# the deposit's own knitted lodger-analysis.pdf/bbc-analysis.pdf (whose
# "Results Holding Conjoint Features Constant" section is literally stubbed
# "Coming Soon!"). This project has already ruled a figure out as an answer
# key (ledger 99): a drawn bar resolves to about 0.1, which is looser than any
# useful tolerance.
#
# But both deposits ship the R Markdown SOURCE that computes the AMCE/MM
# tables with cregg::cj() before handing them to ggplot -- cj() returns a
# tidy data frame; the plot is what happens to it afterwards. So the numbers
# are already ours and merely unrendered. This script runs THEIR cleaning
# (lodger-analysis-cleaning.R / bbc-analysis-cleaning.R) and THEIR estimator,
# translated from rio::import to haven::read_sav (see note below), and
# deliberately does not reimplement AMCE estimation in Python: checking our
# melt against our own reimplementation would not be verification of
# anything. This is the answer_key_EFXNLX.R / verify_QQM5MC.py pattern.
#
# Usage:  Rscript scripts/answer_key_35M5CV.R

suppressPackageStartupMessages({
  library(haven)
  library(cregg)
})

RAW <- "data/raw/35M5CV"
stopifnot(dir.exists(RAW))

# `haven::read_sav`, not `rio::import`. rio returns the attribute columns as
# bare numerics, so every level arrives as "1"/"2"/"3" -- identical across
# every attribute -- which cregg then rejects for duplicated level names.
# The quiet version of that mistake is an answer key labelled by code number.
# (Confirmed necessary here too: the depositors' OWN cleaning scripts use
# rio::import + rio::factorize, which works for them because factorize reads
# the "labels" attribute directly off the imported column; read_sav +
# as_factor is the equivalent move for haven's labelled vectors.)

# Both experiments are 7-attribute forced-choice conjoints: QPAIRn (n=1..5)
# records *which of 11 candidate names* was chosen -- never which profile
# position -- so the choice has to be recovered by matching the chosen name
# against name_seen1_t{n} / name_seen2_t{n} per row. Building off QPAIRn as a
# raw 0/1/2 indicator would silently answer a different question.

# ---------------------------------------------------------------------------
# One reshape routine, parameterised per study. Mirrors the depositors' own
# two-stage reshape (wide -> pair-level -> profile-level) and repeats their
# row-count assertions: a different count here means we are describing a
# different dataset than the paper does.
# ---------------------------------------------------------------------------

run_study <- function(tag, file, expect_dim, attr_cols, out_csv) {
  cat("\n", strrep("=", 78), "\n", tag, "\n", strrep("=", 78), "\n", sep = "")

  d <- haven::read_sav(file.path(RAW, file))
  cat("# respondents:", nrow(d), " columns:", ncol(d), "\n")
  stopifnot(dim(d) == expect_dim)  # the depositors' own cleaning-script assertion

  PAIRS <- 1:5
  attrs <- names(attr_cols)  # e.g. name, age, occupation, hobby, volunteer, party, eu

  pair_level <- do.call(rbind, lapply(PAIRS, function(t) {
    base <- data.frame(ID = seq_len(nrow(d)), pair = t, stringsAsFactors = FALSE)
    qpair <- as.character(haven::as_factor(d[[sprintf("QPAIR%d", t)]]))
    base$chosen_name <- qpair
    for (side in 1:2) {
      for (a in attrs) {
        col <- sprintf("%s_seen%d_t%d", attr_cols[[a]], side, t)
        base[[sprintf("%s_%d", a, side)]] <-
          as.character(haven::as_factor(d[[col]]))
      }
    }
    base
  }))
  stopifnot(nrow(pair_level) == 5 * nrow(d))  # depositors' stopifnot(nrow(conj2) == 5*nrow(conj))
  cat("# pair-level rows:", nrow(pair_level), "\n")

  # recode outcome as a 0/1 indicator of whether THIS profile was chosen, by
  # matching the chosen NAME against the name shown in that profile position
  # -- exactly what *-analysis-cleaning.R does with
  #   outcomeA <- as.integer(outcome == nameA)
  prof <- do.call(rbind, lapply(1:2, function(side) {
    out <- data.frame(
      ID      = pair_level$ID,
      pair    = pair_level$pair,
      profile = side,
      chosen  = as.integer(pair_level$chosen_name == pair_level[[sprintf("name_%d", side)]]),
      stringsAsFactors = FALSE
    )
    for (a in attrs) out[[a]] <- pair_level[[sprintf("%s_%d", a, side)]]
    out
  }))
  stopifnot(nrow(prof) == 2 * nrow(pair_level))  # depositors' stopifnot(nrow(conj2) == 2*nrow(conj))
  cat("# profile-level rows:", nrow(prof), "\n")

  # Skipped/Not Asked -> NA, same as the depositors' na-ification of every
  # feature factor, before dropping rows with no resolved outcome.
  for (a in attrs) {
    prof[[a]][prof[[a]] %in% c("Skipped", "Not Asked")] <- NA_character_
  }
  prof <- prof[!is.na(prof$chosen), ]
  cat("# profile-level rows, non-missing outcome:", nrow(prof), "\n")

  # Factors: preserve the SPSS value-label order (ascending code), which is
  # what rio::factorize gives the depositors -- NOT R's default alphabetical
  # factor() ordering. party/eu are different: the depositors hand-relevel
  # them (see *-analysis-cleaning.R), baseline = code 3, "didn't vote/support
  # a side" -- reproduced here verbatim rather than risking a silent
  # transposition by guessing at an equivalent order.
  # Label text is pulled live from each dataset's own value-label attribute,
  # by CODE, never hardcoded -- the labels differ in wording between lodger
  # ("Voted Conservative at the 2017 election") and bbc ("Supported the
  # Conservative Party at the 2017 election"), and both use a curly
  # apostrophe ("Didn't"). Typography/word differences are exactly the trap
  # docs/CONVENTIONS.md warns about; reading them live avoids re-typing them.
  level_order <- function(colname) {
    labs <- attr(d[[colname]], "labels")
    labs <- labs[!names(labs) %in% c("Skipped", "Not Asked")]
    names(labs)[order(labs)]
  }
  relevel_by_code <- function(colname, codes_order) {
    labs <- attr(d[[colname]], "labels")
    vapply(codes_order, function(code) names(labs)[labs == code][1], character(1))
  }
  for (a in setdiff(attrs, c("party", "eu"))) {
    src_col <- sprintf("%s_seen1_t1", attr_cols[[a]])
    prof[[a]] <- factor(prof[[a]], levels = level_order(src_col))
  }
  # party/eu are NOT raw code order -- *-analysis-cleaning.R hand-relevels
  # both (factor(..., levels = c(3,2,1)) / c(3,1,2)) so baseline = code 3,
  # "didn't vote/support" -- reproduced verbatim rather than guessed at.
  if ("party" %in% attrs) {
    src <- sprintf("%s_seen1_t1", attr_cols[["party"]])
    prof$party <- factor(prof$party, levels = relevel_by_code(src, c(3, 2, 1)))
  }
  if ("eu" %in% attrs) {
    src <- sprintf("%s_seen1_t1", attr_cols[["eu"]])
    prof$eu <- factor(prof$eu, levels = relevel_by_code(src, c(3, 1, 2)))
  }

  cat("\n## reference level per attribute\n")
  for (a in attrs) cat(sprintf("%-12s %s\n", a, levels(prof[[a]])[1]))

  f <- as.formula(paste("chosen ~", paste(attrs, collapse = " + ")))

  COLS <- c("feature", "level", "estimate", "std.error")
  cat("\n## AMCEs (cregg::cj, estimate = \"amce\", clustered by respondent)\n")
  amce <- cregg::cj(prof, f, id = ~ID, estimate = "amce")

  cat("\n## marginal means (cregg::cj, estimate = \"mm\")\n")
  mm <- cregg::cj(prof, f, id = ~ID, estimate = "mm")

  key <- rbind(
    cbind(quantity = "amce", amce[, COLS]),
    cbind(quantity = "mm",   mm[, COLS])
  )
  key$reference <- vapply(as.character(key$feature),
                           function(a) levels(prof[[a]])[1], character(1))
  write.csv(key, out_csv, row.names = FALSE)
  cat(sprintf("\nwrote %s -- %d rows (%d AMCEs, %d marginal means)\n",
              out_csv, nrow(key), nrow(amce), nrow(mm)))

  # The invariant that would have caught a dropped or duplicated profile: a
  # forced choice between two fully randomised profiles means every
  # attribute's marginal means must average to 0.5.
  cat(sprintf("# mean of marginal means: %.6f  (forced-choice invariant: should be 0.5)\n",
              mean(mm$estimate)))

  invisible(list(prof = prof, amce = amce, mm = mm))
}

# ---------------------------------------------------------------------------
# lodger: name, age, occupation, hobby, volunteer, party, eu
# ---------------------------------------------------------------------------
lodger <- run_study(
  tag = "LODGER",
  file = "lodger-data-raw.sav",
  expect_dim = c(1669, 170),
  attr_cols = c(name = "name", age = "age", occupation = "occupation",
                hobby = "hobby", volunteer = "volunteer",
                party = "politics", eu = "eu"),
  out_csv = "data/catalog/answer_key_35M5CV_lodger.csv"
)

# ---------------------------------------------------------------------------
# bbc: name, age, experience, degree, occupation, party, eu
# ---------------------------------------------------------------------------
bbc <- run_study(
  tag = "BBC",
  file = "bbc-data-raw.sav",
  expect_dim = c(1635, 167),
  attr_cols = c(name = "name", age = "age", experience = "experience",
                degree = "degree", occupation = "occupation",
                party = "politics", eu = "eu"),
  out_csv = "data/catalog/answer_key_35M5CV_bbc.csv"
)

cat("\nDone.\n")
