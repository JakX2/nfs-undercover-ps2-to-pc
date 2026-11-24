#!/usr/bin/env bash
# Bounded, original DOL-only, headless startup through the DSP flush return.
set -euo pipefail
umask 077
[[ $# == 3 ]] || exit 2
exe="$(realpath "$1")";dol="$(realpath "$2")";work="$(realpath -m "$3")"
here="$(cd "$(dirname "$0")" && pwd)"
[[ -f "$exe" && -x "$exe" && -f "$dol" && ! -e "$work" && ! -L "$work" ]] || { echo 'V575_DSP_SC_INPUT accepted=0';exit 1; }
[[ "$(sha256sum "$dol" | cut -d ' ' -f1)" == 16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4 ]] || { echo 'V575_DSP_SC_INPUT accepted=0';exit 1; }
mkdir -m 700 "$work"
printf '%s\n' '[system]' 'platform = "Wii"' '[input]' 'mode = 6' > "$work/config.toml"
python3 "$here/write_sram_profile_v536.py" "$work/exi-test-profile.txt"
printf '%s\n' UNDERCOVER_SI_PROFILE_V1 latency=00000008 port0=absent port1=absent port2=absent port3=absent > "$work/si-test-profile.txt"
echo 'V575_DSP_SC_INPUT accepted=1 dol_only=1 profiles=synthetic'
rc=0
(
  cd "$work"
  ulimit -c 0
  ulimit -f 8192
  timeout --signal=TERM --kill-after=3s 20s env -i PATH="$PATH" HOME="$work" \
    NWII_HEADLESS=1 NWII_TRACE_CALLS=1 UNDERCOVER_V419_START=1 \
    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
    UNDERCOVER_V475_IRQ_MMIO=1 UNDERCOVER_V481_IRQ_BANKS=1 UNDERCOVER_V490_EXI_CONTROLLER=1 \
    "UNDERCOVER_V501_EXI_PROFILE=$work/exi-test-profile.txt" \
    UNDERCOVER_V512_SI=1 "UNDERCOVER_V518_SI_PROFILE=$work/si-test-profile.txt" \
    UNDERCOVER_V522_VICLK=0 UNDERCOVER_V537_ACR=1 UNDERCOVER_V574_SC=1 \
    "$exe" "$dol" "$work/config.toml"
) > "$work/run-private.log" 2>&1 || rc=$?
python3 "$here/audit_v575_dsp_sc_frontier.py" "$work/run-private.log" "$rc"
