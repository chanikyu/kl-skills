# expect: vague-name:q vague-name:tmp no-docstring:sum_all

sum_all <- function(values) {
  q <- 1
  tmp <- q
  for (amount in values) {
    tmp <- tmp + amount
  }
  tmp
}

#' 이름을 다듬는다. "x <- 1" 은 글이다.
tidy_name <- function(raw_name) {
  trimmed <- trimws(raw_name)
  lowered <- tolower(trimmed)
  note <- "y <- 2"
  message(note)
  lowered
}
