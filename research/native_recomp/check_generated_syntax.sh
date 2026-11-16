#!/usr/bin/env bash
set -euo pipefail
outdir="$1"
logdir="$outdir/syntax-validation"
mkdir -p "$logdir"
export outdir logdir
find "$outdir" -maxdepth 1 -name 'output_*.cpp' -print0 | xargs -0 -P 4 -I '{}' bash -c '
  f="$1"; base="$(basename "$f" .cpp)"
  if timeout 30s g++ -std=c++20 -fsyntax-only -fmax-errors=5 -I "$outdir/nWiiRuntime/include" -I "$outdir" "$f" > "$logdir/$base.log" 2>&1; then
    printf "PASS %s\n" "$base" > "$logdir/$base.status"
  else
    printf "FAIL %s\n" "$base" > "$logdir/$base.status"
  fi
' _ '{}'
if timeout 40s g++ -std=c++20 -fsyntax-only -fmax-errors=5 -I "$outdir/nWiiRuntime/include" -I "$outdir" "$outdir/main_output.cpp" > "$logdir/main_output.log" 2>&1; then
  echo 'PASS main_output' > "$logdir/main_output.status"
else
  echo 'FAIL main_output' > "$logdir/main_output.status"
fi
awk '{x[$1]++} END {for(k in x) print k, x[k]}' "$logdir"/*.status
