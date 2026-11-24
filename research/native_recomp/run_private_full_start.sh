#!/usr/bin/env bash
# Bounded DOL-only launch of a private whole-image native executable.
set -euo pipefail
umask 077
if [[ $# -ne 3 && $# -ne 4 ]]; then
  echo 'Usage: run_private_full_start.sh PRIVATE_EXE OWNER_DOL FRESH_PRIVATE_RUN_DIR [startup|hardware|cache]' >&2
  exit 2
fi
exe="$(realpath "$1")";dol="$(realpath "$2")";work="$(realpath -m "$3")"
here="$(cd "$(dirname "$0")" && pwd)"
mode="${4:-startup}"
case "$mode" in
  startup) audit=audit_v419_full_start.py;;
  hardware) audit=audit_v425_full_hardware.py;;
  cache) audit=audit_v428_full_cache.py;;
  *) echo 'Invalid bounded startup mode' >&2; exit 2;;
esac
[[ -x "$exe" && -f "$exe" && -f "$dol" && ! -e "$work" && ! -L "$work" ]] || {
  echo 'V419_FULL_START_INPUT accepted=0'; exit 1;
}
if [[ "$(sha256sum "$dol" | cut -d ' ' -f1)" != 16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4 ]]; then
  echo 'V419_FULL_START_INPUT accepted=0'; exit 1
fi
mkdir -m 700 "$work"
printf '%s\n' '[system]' 'platform = "Wii"' '[input]' 'mode = 6' > "$work/config.toml"
echo 'V419_FULL_START_INPUT accepted=1 dol_only=1'
rc=0
(
  cd "$work"
  ulimit -c 0
  ulimit -f 8192
  timeout --signal=TERM --kill-after=3s 20s env -i PATH="$PATH" HOME="$work" \
    NWII_HEADLESS=1 NWII_TRACE_CALLS=1 UNDERCOVER_V419_START=1 \
    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy "$exe" "$dol" "$work/config.toml"
) > "$work/run-private.log" 2>&1 || rc=$?
python3 "$here/$audit" "$work/run-private.log" "$rc"
