library(readxl)
path <- "PRS_Tracker.xlsx"

sheets <- list(
  list(name="Rental supply rightmove",        skip=8),
  list(name="Prevention duty by reason",      skip=7),
  list(name="Relief duty by reason",          skip=7),
  list(name="Prevention duty S21",            skip=7),
  list(name="Rightmove Rental Price Tracker", skip=7),
  list(name="RICS rental sentiment",          skip=8),
  list(name="Category 1 hazard",             skip=6),
  list(name="Landlord type",                 skip=6),
  list(name="Size of portfolio",             skip=6),
  list(name="Gaurantor EPLS",               skip=6),
  list(name="Households in PRS",            skip=8),
  list(name="Length of stay",               skip=8),
  list(name="Met Illegal eviction",         skip=6),
  list(name="Repossessions",                skip=14),
  list(name="Spareroom Demand Supply",      skip=7)
)

for (s in sheets) {
  tryCatch({
    df <- read_excel(path, sheet=s$name, col_names=FALSE, skip=s$skip)
    cat(sprintf("%-40s skip=%-3d cols=%-3d first_col='%s'\n",
      s$name, s$skip, ncol(df), as.character(df[1,1])))
  }, error = function(e) {
    cat(sprintf("%-40s ERROR: %s\n", s$name, e$message))
  })
}
