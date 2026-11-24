#!/usr/bin/env bash
# Private whole-image PowerPC translation, C++ syntax and optional native link probe.
# Never launch the generated executable or claim game boot or gameplay.
set -euo pipefail
if [[ $# -ne 5 ]]; then
  echo 'Usage: run_full_recomp_probe_ci.sh NWII_ROOT OWNER_DOL OWNER_ELF PRIVATE_WORK sample|all|link' >&2
  exit 2
fi
root="$(realpath "$1")"
dol="$(realpath "$2")"
elf="$(realpath "$3")"
work="$4"
mode="$5"
[[ "$mode" == sample || "$mode" == all || "$mode" == link ]] || { echo 'Invalid compile probe mode' >&2; exit 2; }
[[ ! -e "$work" ]] || { echo 'Private work destination must be fresh' >&2; exit 2; }
mkdir -p -m 700 "$work"
here="$(cd "$(dirname "$0")" && pwd)"
umask 077
python3 "$here/make_private_elf_symbol_map.py" "$elf" "$work/functions-private.csv"
python3 "$here/apply_psq_indexed_patch.py" "$root" > "$work/patch.log" 2>&1 || {
  echo 'Indexed paired-single patch failed' >&2; exit 1;
}
python3 "$here/apply_psq_estimate_and_gqr_v5.py" "$root" >> "$work/patch.log" 2>&1 || {
  echo 'Paired-single runtime patch failed' >&2; exit 1;
}
python3 "$here/apply_verified_elf_spans_v6.py" "$root" >> "$work/patch.log" 2>&1 || {
  echo 'Conservative ELF code-span patch failed' >&2; exit 1;
}
mkdir -p "$work/generated" "$work/bin"
g++ -std=c++20 -O2 -Wno-unused-variable -Wno-sign-compare \
  -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" \
  "$here/offline_recompiler_driver_v6.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" -o "$work/bin/translator" \
  > "$work/build.log" 2>&1 || {
    echo 'Whole-image offline translator failed to compile' >&2; exit 1;
  }
timeout 1200s "$work/bin/translator" "$dol" "$work/functions-private.csv" \
  "$work/generated" --strict-symbol-spans --generate "$root/nWiiRuntime" \
  > "$work/translation.log" 2>&1 || {
    echo 'Original whole-image translation failed; private diagnostics withheld' >&2; exit 1;
  }
count="$(find "$work/generated" -maxdepth 1 -type f -name 'output_*.cpp' | wc -l)"
(( count >= 20 )) || { echo 'Generated too few private C++ shards' >&2; exit 1; }
[[ -s "$work/generated/main_output.cpp" ]] || {
  echo 'Generated C++ dispatcher missing' >&2; exit 1;
}
if grep -lF 'UNIMPLEMENTED Opcode' "$work/generated"/output_*.cpp > "$work/opcode-failures.log"; then
  echo 'Explicit unsupported opcode markers remain in full-image translation' >&2
  exit 1
fi
if [[ "$mode" == sample ]]; then
  first="$(find "$work/generated" -maxdepth 1 -name 'output_*.cpp' | sort | head -1)"
  last="$(find "$work/generated" -maxdepth 1 -name 'output_*.cpp' | sort | tail -1)"
  set -- "$first" "$last" "$work/generated/main_output.cpp"
else
  set -- "$work/generated"/output_*.cpp "$work/generated/main_output.cpp"
fi
checks="$#"
for cpp in "$@"; do
  timeout 90s g++ -std=c++20 -fsyntax-only -fmax-errors=3 \
    -I"$work/generated/nWiiRuntime/include" -I"$work/generated" "$cpp" \
    > "$work/syntax.log" 2>&1 || {
      echo 'Private translated C++ syntax check failed; source withheld' >&2; exit 1;
    }
done
echo "PASS: whole Wii DOL translated into $count ephemeral C++ shards"
echo "PASS: translated syntax checks $checks/$checks mode=$mode"
if [[ "$mode" == link ]]; then
  bash "$here/run_private_full_link.sh" "$work/generated" "$work/native-build"
  echo 'INFO: native game launch, main, boot, frontend and gameplay NOT proven'
else
  echo 'INFO: original full-image linking, game main, boot, frontend and gameplay NOT proven'
fi
