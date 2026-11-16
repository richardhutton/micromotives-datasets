# R helper for scripts/verify_zenodo10641548.py: the paper's top-supported model
# (Hare et al., Proc. R. Soc. B 2024, ESM S6), fitted as a proportional-odds logit.
#
# The authors fit it with ordinal::clm (logit link), the deposit's own script
# `Perceptions_of_hunting_script_Dryad.R`. MASS::polr maximises the same
# likelihood with the same parameterisation (logit P(Y <= k) = zeta_k - eta), so
# the estimates agree; polr is used because MASS ships with R and ordinal is not
# installed here. The response and the three experimental factors for UK rows come
# from the BUILT parquet; everything else from the deposit, joined by the Python
# orchestrator. Reference levels are S6's (and R's alphabetical defaults).
#
# Usage: Rscript scripts/verify_zenodo10641548_polr.R <input_csv> <output_csv>

suppressPackageStartupMessages(library(MASS))

args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 2)
d <- read.csv(args[1], stringsAsFactors = TRUE, encoding = "UTF-8")
d$response <- factor(d$response, levels = 1:7, ordered = TRUE)
d$country <- relevel(d$country, ref = "SA")
d$meat <- relevel(d$meat, ref = "Wildlife")  # S6 reports "Meat, people"; R would pick People
d$hunter <- relevel(d$hunter, ref = "Strongly disagree")
d$animal.protectionist <- relevel(d$animal.protectionist, ref = "Strongly disagree")
d$people.animals <- relevel(d$people.animals, ref = "Strongly prioritise wild animals")
d$education <- relevel(d$education, ref = "Primary or elementary school")

m <- polr(response ~ country + animal + meat + revenue + education + hunter +
            animal.protectionist + people.animals, data = d, Hess = TRUE, method = "logistic")
co <- coef(summary(m))
write.csv(data.frame(term = rownames(co), estimate = co[, "Value"], se = co[, "Std. Error"]),
          args[2], row.names = FALSE)
