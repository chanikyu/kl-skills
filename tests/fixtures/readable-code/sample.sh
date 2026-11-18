#!/bin/sh
# expect: vague-name:q vague-name:tmp no-docstring:sum_all

q=1
tmp="$q"
sum_all() {
  total=0
  for amount in "$@"; do
    total=$((total + amount))
  done
  echo "$total"
  echo "${#tmp}"
}

# 메시지를 찍는다. heredoc 안의 x=1 은 글이다.
print_note() {
  cat <<'EOF'
x=1
y=2
EOF
  label="z=3"
  echo "$label"
}
